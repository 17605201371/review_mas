#!/usr/bin/env python3
"""Build the P34-1 per-paper PaperIndex audit and score frozen human anchors."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from agent_system.environments.env_package.review.paper_index import PaperIndex, build_paper_index
from agent_system.inference.review_runner import _row_to_env_kwargs, load_review_rows


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_annotations(path: Optional[Path]) -> Dict[str, Any]:
    if path is None or not path.exists():
        return {}
    value = json.loads(path.read_text(encoding="utf-8"))
    cases = value.get("cases") if isinstance(value, dict) else None
    if not isinstance(cases, list):
        raise ValueError("annotation file must contain a cases list")
    return {str(item.get("paper_id") or ""): item for item in cases if isinstance(item, dict)}


def _paper_id(row: Dict[str, Any], mapped: Dict[str, Any], index: int) -> str:
    return str(row.get("id") or row.get("paper_id") or mapped.get("paper_id") or f"row-{index + 1:03d}")


def _boundary_match(index: PaperIndex, annotation: Dict[str, Any], tolerance: int) -> bool:
    expected_start = annotation.get("source_span_start")
    heading = str(annotation.get("heading") or "").strip().lower()
    section_type = str(annotation.get("section_type") or "").strip().lower()
    for section in index.sections:
        if expected_start is not None and abs(section.source_span_start - int(expected_start)) > tolerance:
            continue
        if heading and heading not in section.heading.lower():
            continue
        if section_type and section.section_type != section_type:
            continue
        return True
    return False


def _anchor_match(index: PaperIndex, annotation: Dict[str, Any]) -> bool:
    query = str(annotation.get("query") or annotation.get("text") or "").strip()
    expected_text = str(annotation.get("text") or "").strip()
    section_types = annotation.get("section_types") if isinstance(annotation.get("section_types"), list) else None
    if not query:
        return False
    for result in index.search(query, section_types=section_types, top_k=5):
        if not expected_text or expected_text.lower() in result.text.lower():
            return True
    return False


def _score_annotations(index: PaperIndex, annotation: Dict[str, Any], tolerance: int) -> Dict[str, Any]:
    boundaries = [item for item in annotation.get("expected_boundaries", []) if isinstance(item, dict)]
    anchors = [item for item in annotation.get("key_anchors", []) if isinstance(item, dict)]
    false_boundaries = [item for item in annotation.get("false_boundaries", []) if isinstance(item, dict)]
    boundary_hits = sum(_boundary_match(index, item, tolerance) for item in boundaries)
    anchor_hits = sum(_anchor_match(index, item) for item in anchors)
    false_boundary_hits = sum(_boundary_match(index, item, tolerance) for item in false_boundaries)
    return {
        "expected_boundary_count": len(boundaries),
        "expected_boundary_hit_count": boundary_hits,
        "key_anchor_count": len(anchors),
        "key_anchor_hit_count": anchor_hits,
        "labeled_false_boundary_count": len(false_boundaries),
        "labeled_false_boundary_hit_count": false_boundary_hits,
    }


def _case_report(paper_id: str, paper_text: str, annotation: Dict[str, Any], tolerance: int) -> Dict[str, Any]:
    index = build_paper_index(paper_text)
    audit = index.audit_summary()
    annotation_score = _score_annotations(index, annotation, tolerance)
    return {
        "paper_id": paper_id,
        "paper_text_sha256": hashlib.sha256(paper_text.encode("utf-8")).hexdigest(),
        **audit,
        "sections": [
            {
                "section_id": item.section_id,
                "section_type": item.section_type,
                "heading": item.heading,
                "source_span_start": item.source_span_start,
                "source_span_end": item.source_span_end,
                "parent_section_id": item.parent_section_id,
                "confidence": item.confidence,
                "parser_mode": item.parser_mode,
                "text_preview": item.text[:240],
            }
            for item in index.sections
        ],
        "artifacts": [
            {
                "artifact_id": item.artifact_id,
                "artifact_type": item.artifact_type,
                "locator": item.locator,
                "source_span_start": item.source_span_start,
                "source_span_end": item.source_span_end,
                "section_id": item.section_id,
                "confidence": item.confidence,
                "parser_mode": item.parser_mode,
                "text_preview": item.text[:240],
            }
            for item in index.artifacts
        ],
        "annotation_present": bool(annotation),
        "human_review_complete": bool(annotation.get("human_review_complete")),
        "annotation_score": annotation_score,
    }


def build_report(dataset: Path, annotations_path: Optional[Path], limit: Optional[int], tolerance: int) -> Dict[str, Any]:
    rows = load_review_rows(str(dataset), limit=limit)
    annotations = _load_annotations(annotations_path)
    cases: List[Dict[str, Any]] = []
    for row_index, row in enumerate(rows):
        mapped = _row_to_env_kwargs(row)
        paper_id = _paper_id(row, mapped, row_index)
        cases.append(_case_report(paper_id, str(mapped.get("paper_text") or ""), annotations.get(paper_id, {}), tolerance))

    boundary_total = sum(case["annotation_score"]["expected_boundary_count"] for case in cases)
    boundary_hits = sum(case["annotation_score"]["expected_boundary_hit_count"] for case in cases)
    anchor_total = sum(case["annotation_score"]["key_anchor_count"] for case in cases)
    anchor_hits = sum(case["annotation_score"]["key_anchor_hit_count"] for case in cases)
    false_total = sum(case["annotation_score"]["labeled_false_boundary_count"] for case in cases)
    false_hits = sum(case["annotation_score"]["labeled_false_boundary_hit_count"] for case in cases)
    boundary_recall = boundary_hits / boundary_total if boundary_total else None
    anchor_recall = anchor_hits / anchor_total if anchor_total else None
    parser_modes = Counter(mode for case in cases for mode in case["parser_modes"])
    completed_annotation_count = sum(case["human_review_complete"] for case in cases)
    all_papers_annotated = completed_annotation_count == len(cases)
    false_boundary_rate = false_hits / false_total if false_total else (0.0 if all_papers_annotated else None)
    annotation_ready = (
        all_papers_annotated
        and boundary_total > 0
        and anchor_total > 0
    )
    gates = {
        "expected_section_boundary_recall_gte_0_90": boundary_recall is not None and boundary_recall >= 0.9,
        "key_anchor_retrieval_recall_gte_0_90": anchor_recall is not None and anchor_recall >= 0.9,
        "false_section_boundary_rate_lte_0_10": false_boundary_rate is not None and false_boundary_rate <= 0.1,
        "all_spans_roundtrip": all(case["span_roundtrip_ok"] for case in cases),
        "all_papers_annotated": all_papers_annotated,
    }
    status = "PASS" if annotation_ready and all(gates.values()) else "FAIL" if annotation_ready else "NEEDS_MANUAL_ANCHORS"
    return {
        "status": status,
        "boundary": "P34-1 PaperIndex parser/retrieval audit; no ReviewState mutation",
        "dataset_path": str(dataset),
        "dataset_sha256": _sha256(dataset),
        "annotations_path": str(annotations_path) if annotations_path else "",
        "annotations_sha256": _sha256(annotations_path) if annotations_path and annotations_path.exists() else "",
        "paper_count": len(cases),
        "annotated_paper_count": sum(case["annotation_present"] for case in cases),
        "completed_annotation_count": completed_annotation_count,
        "parser_mode_counts": dict(sorted(parser_modes.items())),
        "fallback_paper_count": sum(case["fallback_used"] for case in cases),
        "span_roundtrip_paper_count": sum(case["span_roundtrip_ok"] for case in cases),
        "boundary_recall": boundary_recall,
        "anchor_retrieval_recall": anchor_recall,
        "false_boundary_rate": false_boundary_rate,
        "gates": gates,
        "cases": cases,
    }


def render_markdown(report: Dict[str, Any]) -> str:
    lines = [
        "# P34-1 PaperIndex Audit",
        "",
        f"- status: **{report['status']}**",
        f"- dataset: `{report['dataset_path']}`",
        f"- paper_count: `{report['paper_count']}`",
        f"- annotated_paper_count: `{report['annotated_paper_count']}`",
        f"- completed_annotation_count: `{report['completed_annotation_count']}`",
        f"- fallback_paper_count: `{report['fallback_paper_count']}`",
        f"- span_roundtrip_paper_count: `{report['span_roundtrip_paper_count']}`",
        f"- boundary_recall: `{report['boundary_recall']}`",
        f"- anchor_retrieval_recall: `{report['anchor_retrieval_recall']}`",
        f"- false_boundary_rate: `{report['false_boundary_rate']}`",
        f"- parser_mode_counts: `{report['parser_mode_counts']}`",
        "",
        "## Gates",
        "",
    ]
    lines.extend(f"- `{key}`: `{value}`" for key, value in report["gates"].items())
    lines.extend(["", "## Per Paper", ""])
    for case in report["cases"]:
        lines.append(
            f"- `{case['paper_id']}`: sections={case['section_count']}, artifacts={case['artifact_count']}, "
            f"modes={case['parser_modes']}, fallback={case['fallback_used']}, span_roundtrip={case['span_roundtrip_ok']}, "
            f"annotated={case['annotation_present']}"
        )
    if report["status"] == "NEEDS_MANUAL_ANCHORS":
        lines.extend(["", "Hard acceptance remains blocked until the frozen human anchor file covers all papers."])
    return "\n".join(lines) + "\n"


def write_annotation_template(report: Dict[str, Any], path: Path) -> None:
    cases = []
    for case in report["cases"]:
        boundary_suggestions = []
        seen_types = set()
        for section in case["sections"]:
            section_type = str(section.get("section_type") or "")
            if section_type in {"preamble", "other", "chunk"} or section_type in seen_types:
                continue
            boundary_suggestions.append({
                "heading": section.get("heading", ""),
                "section_type": section_type,
                "source_span_start": section.get("source_span_start"),
                "parser_mode": section.get("parser_mode", ""),
                "confidence": section.get("confidence", 0.0),
                "text_preview": section.get("text_preview", ""),
                "human_action": "accept|edit|reject",
            })
            seen_types.add(section_type)
            if len(boundary_suggestions) >= 8:
                break
        anchor_suggestions = []
        for artifact in case["artifacts"]:
            if artifact.get("artifact_type") not in {"table", "figure", "caption"}:
                continue
            preview = str(artifact.get("text_preview") or "")
            anchor_suggestions.append({
                "query": str(artifact.get("locator") or preview[:100]),
                "text": preview,
                "artifact_type": artifact.get("artifact_type", ""),
                "source_span_start": artifact.get("source_span_start"),
                "source_span_end": int(artifact.get("source_span_start") or 0) + len(preview),
                "human_action": "accept|edit|reject",
            })
            if len(anchor_suggestions) >= 6:
                break
        if len(anchor_suggestions) < 3:
            for section in case["sections"]:
                if section.get("section_type") not in {"method", "results", "analysis", "limitations"}:
                    continue
                preview = str(section.get("text_preview") or "")
                anchor_suggestions.append({
                    "query": f"{section.get('heading', '')} {preview[:100]}",
                    "text": preview,
                    "section_types": [section.get("section_type")],
                    "source_span_start": section.get("source_span_start"),
                    "source_span_end": min(int(section.get("source_span_end") or 0), int(section.get("source_span_start") or 0) + len(preview)),
                    "human_action": "accept|edit|reject",
                })
                if len(anchor_suggestions) >= 6:
                    break
        false_boundary_suggestions = [
            {
                "heading": section.get("heading", ""),
                "section_type": section.get("section_type", ""),
                "source_span_start": section.get("source_span_start"),
                "reason": "lower-confidence plain heading; confirm it is a real boundary",
                "human_action": "mark_real|mark_false",
            }
            for section in case["sections"]
            if section.get("parser_mode") == "plain_heading" or float(section.get("confidence") or 0.0) < 0.8
        ][:6]
        cases.append({
            "paper_id": case["paper_id"],
            "expected_boundaries": [],
            "key_anchors": [],
            "false_boundaries": [],
            "machine_boundary_suggestions": boundary_suggestions,
            "machine_anchor_suggestions": anchor_suggestions,
            "machine_false_boundary_suggestions": false_boundary_suggestions,
            "human_review_complete": False,
            "human_reviewer_id": "",
            "human_review_notes": "",
        })
    template = {
        "schema_version": "p34_paper_index_human_anchors_v1",
        "dataset_sha256": report["dataset_sha256"],
        "instructions": {
            "expected_boundaries": "Human-mark real section starts with heading/section_type/source_span_start.",
            "key_anchors": "Human-mark method/result/table/caption anchors using query + exact text.",
            "false_boundaries": "Human-mark lines that resemble headings but must not become sections.",
        },
        "machine_suggestions_are_not_labels": True,
        "cases": cases,
    }
    path.write_text(json.dumps(template, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--annotations")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--boundary-tolerance", type=int, default=8)
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--output-md", required=True)
    parser.add_argument("--write-annotation-template")
    args = parser.parse_args()

    report = build_report(Path(args.dataset), Path(args.annotations) if args.annotations else None, args.limit, args.boundary_tolerance)
    Path(args.output_json).write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    Path(args.output_md).write_text(render_markdown(report), encoding="utf-8")
    if args.write_annotation_template:
        write_annotation_template(report, Path(args.write_annotation_template))
    print(json.dumps({key: report[key] for key in ("status", "paper_count", "fallback_paper_count", "span_roundtrip_paper_count", "gates")}))
    return 0 if report["status"] in {"PASS", "NEEDS_MANUAL_ANCHORS"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
