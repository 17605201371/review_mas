#!/usr/bin/env python3
"""Run a resumable dual-model AI pilot audit over all P34 hardneg20 packets."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Mapping, Sequence, Tuple

from agent_system.environments.env_package.review.paper_index import build_paper_index
from agent_system.inference.review_runner import ApiReviewGenerator
from scripts.p33_freeform_critique_probe import _extract_json_object, _load_dotenv


MODEL_CODES = {"M": "mimo-v2.5", "P": "mimo-v2.5-pro"}
ALLOWED = {
    "evidence_relation": {"supports", "partially_supports", "contradicts", "unrelated", "uncertain"},
    "claim_faithfulness": {"faithful", "overstated", "unsupported_extraction", "uncertain"},
    "review_issue": {"A", "B", "C", "D"},
}


def _load_json(path: Path) -> Dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain an object")
    return value


def _load_jsonl(path: Path) -> List[Dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _canonical_sha256(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _atomic_json(path: Path, value: Any) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(path)


def load_inputs(args: argparse.Namespace) -> Tuple[List[str], Dict[str, str], Dict[str, Dict[str, Any]], Dict[str, Any]]:
    runner_rows = _load_jsonl(Path(args.runner_jsonl))
    paper_ids = [str(row.get("paper_id") or "") for row in runner_rows if str(row.get("paper_id") or "")]
    paper_texts = {
        str(row.get("paper_id") or ""): str((row.get("review_state") or {}).get("paper_text") or "")
        for row in runner_rows
    }
    packets = {
        str(item.get("packet_id") or ""): item
        for path in (Path(args.packets), Path(args.issue_packets))
        for item in _load_jsonl(path)
        if str(item.get("packet_id") or "")
    }
    templates = {
        "evidence_relation": _load_json(Path(args.positive_template)),
        "claim_faithfulness": _load_json(Path(args.claim_template)),
        "review_issue": _load_json(Path(args.issue_template)),
        "paper_index": _load_json(Path(args.anchors)),
    }
    return paper_ids, paper_texts, packets, templates


def _source_text(source: Mapping[str, Any], limit: int = 1200) -> str:
    return str(source.get("quote") or source.get("text") or "")[:limit]


def _retrieval_rows(values: Sequence[Any], limit: int = 7) -> List[Dict[str, Any]]:
    rows = []
    for value in list(values or [])[:limit]:
        if not isinstance(value, Mapping):
            continue
        rows.append({
            "heading": str(value.get("heading") or value.get("source_locator") or ""),
            "section_type": str(value.get("section_type") or ""),
            "quote": _source_text(value, 1400),
            "matched_terms": list(value.get("matched_terms") or [])[:30],
        })
    return rows


def _merged_retrieval_rows(*groups: Sequence[Any], limit: int = 7) -> List[Dict[str, Any]]:
    merged = []
    seen = set()
    for group in groups:
        for row in _retrieval_rows(group, limit):
            key = " ".join(str(row.get("quote") or "").split())
            if not key or key in seen:
                continue
            seen.add(key)
            merged.append(row)
            if len(merged) >= limit:
                return merged
    return merged


def build_paper_payload(
    paper_id: str,
    paper_text: str,
    packets: Mapping[str, Mapping[str, Any]],
    templates: Mapping[str, Mapping[str, Any]],
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {"paper_id": paper_id, "paper_text": paper_text}
    for task in ("evidence_relation", "claim_faithfulness", "review_issue"):
        rows = []
        for label in templates[task].get("labels", []):
            if str(label.get("paper_id") or "") != paper_id:
                continue
            packet_id = str(label.get("packet_id") or "")
            packet = packets.get(packet_id, {})
            claim = packet.get("claim") if isinstance(packet.get("claim"), dict) else {}
            item: Dict[str, Any] = {
                "packet_id": packet_id,
                "claim": str(claim.get("claim_text") or claim.get("claim") or ""),
            }
            if task == "evidence_relation":
                evidence = packet.get("candidate_evidence") if isinstance(packet.get("candidate_evidence"), dict) else {}
                item.update({
                    "candidate_evidence": str(evidence.get("quote") or ""),
                    "source_locator": str(evidence.get("source_locator") or ""),
                    "counterevidence": _retrieval_rows(packet.get("counterevidence_candidates") or [], 4),
                })
            elif task == "claim_faithfulness":
                item["claim_sources"] = _retrieval_rows(packet.get("claim_source_spans") or [], 5)
            else:
                issue = packet.get("issue_hypothesis") if isinstance(packet.get("issue_hypothesis"), dict) else {}
                contract = packet.get("verification_contract") if isinstance(packet.get("verification_contract"), dict) else {}
                item.update({
                    "issue_type": str(issue.get("issue_type") or ""),
                    "hypothesis": str(issue.get("hypothesis") or contract.get("alleged_defect") or ""),
                    "expected_evidence": str(contract.get("required_resolution_evidence") or issue.get("expected_evidence") or ""),
                    "falsification_query": str(contract.get("falsification_query") or issue.get("counterevidence_query") or ""),
                    "paper_anchor": str(issue.get("paper_anchor") or ""),
                    "retrieval_bundle": _merged_retrieval_rows(
                        packet.get("counterevidence_candidates") or [],
                        packet.get("retrieved_evidence") or [],
                        limit=7,
                    ),
                    "unsearched_scope": str(packet.get("unsearched_scope") or ""),
                })
            rows.append(item)
        payload[task] = rows

    anchor_case = next(
        (item for item in templates["paper_index"].get("cases", []) if str(item.get("paper_id") or "") == paper_id),
        {},
    )
    index = build_paper_index(paper_text)
    payload["paper_index"] = {
        "explicit_sections": [
            {"section_id": item.section_id, "heading": item.heading, "section_type": item.section_type}
            for item in index.sections
            if item.heading != "preamble"
        ],
        "artifacts": [
            {
                "artifact_id": item.artifact_id,
                "artifact_type": item.artifact_type,
                "locator": item.locator,
                "text": item.text[:500],
            }
            for item in index.artifacts[:30]
        ],
        "machine_boundary_headings": [str(item.get("heading") or "") for item in anchor_case.get("machine_boundary_suggestions", [])],
        "machine_anchor_queries": [str(item.get("query") or "") for item in anchor_case.get("machine_anchor_suggestions", [])],
        "machine_false_boundary_headings": [str(item.get("heading") or "") for item in anchor_case.get("machine_false_boundary_suggestions", [])],
    }
    return payload


def audit_prompt(payload: Mapping[str, Any]) -> str:
    return (
        "You are independently auditing one research paper for a peer-review discovery study. "
        "Use only the supplied full paper and packets. Do not trust candidate wording. Search the full paper for counterevidence. "
        "Output Chinese reasons, each at most 120 Chinese characters.\n"
        "Evidence labels: supports, partially_supports, contradicts, unrelated, uncertain.\n"
        "Evidence relation is local: judge whether the supplied candidate_evidence quote itself supports the exact claim. "
        "Do not upgrade a narrow quote to supports merely because other parts of the paper support the claim.\n"
        "Claim labels: faithful, overstated, unsupported_extraction, uncertain.\n"
        "Claim faithfulness is textual fidelity to what the paper states and demonstrates. Do not mark a claim overstated only "
        "because more baselines or experiments could have been added; reserve overstated for scope or certainty beyond the paper.\n"
        "Review issue rubric: A=clear specific paper-facing issue ready for verification; "
        "B=defensible after careful wording or limited scope; C=interesting but weak/underspecified diagnosis only; "
        "D=false positive, contradicted, generic, external-knowledge dependent, or not review-worthy.\n"
        "A valid request for missing validation can be B when it is tightly tied to a central paper claim; do not reject it merely "
        "because it asks for an additional measurement, ablation, statistical report, or reproducibility detail. A is stricter than B. "
        "Use C when partial counterevidence leaves only a weak residual concern or when the diagnosis is materially underspecified.\n"
        "Mandatory negative check: before assigning A/B, inspect retrieval_bundle and search the full paper. "
        "If the paper directly contains the allegedly missing baseline, dataset, analysis, or protocol, assign D. "
        "Do not convert a false allegation into B merely because a narrower different concern could be invented; use D for the submitted candidate.\n"
        "For review issues, assign a short semantic cluster_key so synonymous candidates share the same key. "
        "For PaperIndex, select up to 12 key_artifact_ids from the provided artifacts and list missing_section_headings not covered by machine headings.\n"
        "Return exactly one JSON object with keys evidence_relation, claim_faithfulness, review_issue, paper_index, paper_summary_zh. "
        "Each task row must contain packet_id, label, reason_zh. Review rows also contain cluster_key and canonical_issue_zh. "
        "paper_index must contain key_artifact_ids, missing_section_headings, false_boundary_headings, reason_zh.\n"
        f"Input: {json.dumps(payload, ensure_ascii=False)}"
    )


def adjudication_prompt(payload: Mapping[str, Any], left: Mapping[str, Any], right: Mapping[str, Any]) -> str:
    slim = {key: payload[key] for key in ("paper_id", "paper_text", "evidence_relation", "claim_faithfulness", "review_issue", "paper_index")}
    disagreements = {}
    for task in ("evidence_relation", "claim_faithfulness", "review_issue"):
        left_rows = {str(item.get("packet_id") or ""): item for item in left.get(task, [])}
        right_rows = {str(item.get("packet_id") or ""): item for item in right.get(task, [])}
        disagreements[task] = [
            {
                "packet_id": packet_id,
                "audit_one_label": str(left_rows.get(packet_id, {}).get("label") or ""),
                "audit_two_label": str(right_rows.get(packet_id, {}).get("label") or ""),
            }
            for packet_id in sorted(set(left_rows) | set(right_rows))
            if str(left_rows.get(packet_id, {}).get("label") or "") != str(right_rows.get(packet_id, {}).get("label") or "")
        ]
    return (
        "Adjudicate two independent AI pilot audits of the same paper. Re-check every item against the supplied full paper; "
        "do not choose by majority or model identity. Use the same label rubrics. Merge synonymous review issues under identical "
        "cluster_key values. Output Chinese reasons <=140 characters. Return the same exact JSON schema as an independent audit, "
        "with one final row for every packet id and a final PaperIndex selection. For every listed disagreement, explicitly resolve "
        "the submitted candidate as written. A directly contradicted missing-X allegation must be D, not repaired into a different B concern.\n"
        f"Disagreement checklist: {json.dumps(disagreements, ensure_ascii=False)}\n"
        f"Paper and packets: {json.dumps(slim, ensure_ascii=False)}\n"
        f"Audit one: {json.dumps(left, ensure_ascii=False)}\n"
        f"Audit two: {json.dumps(right, ensure_ascii=False)}"
    )


def validate_output(value: Mapping[str, Any], payload: Mapping[str, Any]) -> Tuple[bool, List[str]]:
    errors: List[str] = []
    for task in ("evidence_relation", "claim_faithfulness", "review_issue"):
        expected = {str(item.get("packet_id") or "") for item in payload[task]}
        rows = value.get(task)
        if not isinstance(rows, list):
            errors.append(f"{task}:not_list")
            continue
        received_ids = [str(item.get("packet_id") or "") for item in rows if isinstance(item, dict)]
        received = set(received_ids)
        if received != expected:
            errors.append(f"{task}:id_mismatch")
        if len(received_ids) != len(received):
            errors.append(f"{task}:duplicate_id")
        for item in rows:
            if not isinstance(item, dict) or str(item.get("label") or "") not in ALLOWED[task]:
                errors.append(f"{task}:invalid_label")
                continue
            if not str(item.get("reason_zh") or "").strip():
                errors.append(f"{task}:missing_reason")
            if task == "review_issue" and not str(item.get("cluster_key") or "").strip():
                errors.append("review_issue:missing_cluster")
            if task == "review_issue" and not str(item.get("canonical_issue_zh") or "").strip():
                errors.append("review_issue:missing_canonical_issue")
    paper_index = value.get("paper_index")
    if not isinstance(paper_index, dict):
        errors.append("paper_index:not_object")
    else:
        allowed_artifacts = {str(item.get("artifact_id") or "") for item in payload["paper_index"]["artifacts"]}
        selected = set(str(item) for item in paper_index.get("key_artifact_ids", []) or [])
        if not selected.issubset(allowed_artifacts):
            errors.append("paper_index:unknown_artifact")
        if not str(paper_index.get("reason_zh") or "").strip():
            errors.append("paper_index:missing_reason")
    if not str(value.get("paper_summary_zh") or "").strip():
        errors.append("missing_summary")
    return not errors, errors


class Ledger:
    def __init__(self, path: Path):
        self.path = path
        self.rows = _load_jsonl(path) if path.exists() else []
        self.cache = {str(row.get("request_key") or ""): row for row in self.rows}

    def get(self, key: str) -> Dict[str, Any] | None:
        row = self.cache.get(key)
        return dict(row.get("parsed") or {}) if row and row.get("status") == "PASS" else None

    def put(self, row: Mapping[str, Any]) -> None:
        key = str(row.get("request_key") or "")
        self.cache[key] = dict(row)
        self.rows = [item for item in self.rows if str(item.get("request_key") or "") != key] + [dict(row)]
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary.write_text("".join(json.dumps(item, ensure_ascii=False) + "\n" for item in self.rows), encoding="utf-8")
        temporary.replace(self.path)


def run_phase(
    phase: str,
    model_code: str,
    requests: Sequence[Tuple[str, str, Mapping[str, Any]]],
    ledger: Ledger,
    args: argparse.Namespace,
) -> Dict[str, Dict[str, Any]]:
    results: Dict[str, Dict[str, Any]] = {}
    pending = []
    for paper_id, prompt, payload in requests:
        key = f"{phase}:{model_code}:{paper_id}:{hashlib.sha256(prompt.encode()).hexdigest()}"
        cached = ledger.get(key)
        if cached is not None:
            results[paper_id] = cached
        else:
            pending.append((paper_id, prompt, payload, key))
    generator = ApiReviewGenerator(
        model=MODEL_CODES[model_code], provider="mimo", temperature=0.0, top_p=1.0,
        max_tokens=args.max_tokens, max_workers=args.max_workers, timeout=args.timeout,
        max_retries=1, system_prompt="Return exactly one valid compact JSON object. No markdown or explanation.",
    )
    for round_index in range(3):
        if not pending:
            break
        raw_values = generator.generate_many([("P34 Full AI Pilot Audit", item[1]) for item in pending])
        retry = []
        for (paper_id, prompt, payload, key), raw in zip(pending, raw_values):
            parsed, parse_error = _extract_json_object(raw)
            valid, errors = validate_output(parsed if isinstance(parsed, dict) else {}, payload)
            if not parse_error and valid:
                results[paper_id] = dict(parsed)
                ledger.put({
                    "request_key": key, "phase": phase, "model_code": model_code, "paper_id": paper_id,
                    "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(), "raw_response": raw,
                    "parsed": parsed, "status": "PASS", "round": round_index + 1,
                })
            else:
                failure_errors = ([f"json_parse:{parse_error}"] if parse_error else []) + errors
                ledger.put({
                    "request_key": key, "phase": phase, "model_code": model_code, "paper_id": paper_id,
                    "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(), "raw_response": raw,
                    "parsed": parsed if isinstance(parsed, dict) else {}, "status": "FAIL",
                    "round": round_index + 1, "validation_errors": failure_errors,
                })
                correction = (
                    "\n\nVALIDATION CORRECTION: The previous answer failed these checks: "
                    + json.dumps(failure_errors, ensure_ascii=False)
                    + ". Return the complete JSON object again. Include every packet_id exactly once, use only allowed labels, "
                    "and include non-empty Chinese reason_zh for every row. Review rows also require cluster_key and canonical_issue_zh."
                )
                retry.append((paper_id, prompt + correction, payload, key))
        pending = retry
    if pending:
        raise RuntimeError(f"pilot audit retries exhausted: {[item[0] for item in pending]}")
    return results


def calibrate(final: Mapping[str, Any], pilot: Mapping[str, Any]) -> Dict[str, Any]:
    expected = pilot.get("tasks") or {}
    matched = total = 0
    disagreements = []
    for task in ("evidence_relation", "claim_faithfulness", "review_issue"):
        final_rows = {str(item.get("packet_id") or ""): item for item in final.get(task, [])}
        for packet_id, item in (expected.get(task) or {}).items():
            total += 1
            actual = str((final_rows.get(packet_id) or {}).get("label") or "")
            target = str(item.get("suggested_label") or "")
            if actual == target:
                matched += 1
            else:
                disagreements.append({"task": task, "packet_id": packet_id, "pilot": target, "full": actual})
    return {
        "matched": matched, "total": total, "agreement": matched / total if total else None,
        "disagreements": disagreements,
    }


def render_markdown(report: Mapping[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# P34 Hardneg20 Full AI Pilot Audit", "",
        "## Boundary", "",
        "AI-assisted pilot only; excluded from formal human gold, P34 gates, Judge targets, and ReviewState.", "",
        "## Summary", "",
        f"- papers: `{summary['paper_count']}`",
        f"- evidence labels: `{summary['evidence_label_counts']}`",
        f"- claim labels: `{summary['claim_label_counts']}`",
        f"- review labels: `{summary['review_label_counts']}`",
        f"- raw review issues: `{summary['raw_review_issue_count']}`",
        f"- distinct final clusters: `{summary['distinct_cluster_count']}`",
        f"- duplicate rate: `{summary['duplicate_rate']:.3f}`",
        f"- first-paper calibration: `{report['calibration']}`", "",
        "## Papers", "",
    ]
    for paper in report["papers"]:
        lines.extend([
            f"### {paper['paper_id']}", "",
            paper.get("paper_summary_zh") or "", "",
            f"- evidence: `{paper['label_counts']['evidence_relation']}`",
            f"- claims: `{paper['label_counts']['claim_faithfulness']}`",
            f"- review issues: `{paper['label_counts']['review_issue']}`",
            f"- raw issues / clusters: `{paper['raw_review_issue_count']} / {paper['distinct_cluster_count']}`",
            f"- PaperIndex: `{paper['paper_index_metrics']}`", "",
        ])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runner-jsonl", default="mimo_v25_negqty_recoverycap_guard3_targetneg_freeformrevneg_reviewissuebundle_p33admit_hardneg20_mt7_b4w2_api4_r5t600_tok2048_20260707_100900.jsonl")
    parser.add_argument("--packets", default="P34_2_JUDGE_DATASET_HARDNEG20_20260711_PACKETS.jsonl")
    parser.add_argument("--issue-packets", default="P34_2_SYMMETRIC_DISCOVERY_ACTIVE_20260711_PACKETS.jsonl")
    parser.add_argument("--positive-template", default="P34_2_JUDGE_DATASET_HARDNEG20_20260711_POSITIVE_HUMAN_AUDIT_TEMPLATE.json")
    parser.add_argument("--claim-template", default="P34_2_JUDGE_DATASET_HARDNEG20_20260711_CLAIM_HUMAN_AUDIT_TEMPLATE.json")
    parser.add_argument("--issue-template", default="P34_2_SYMMETRIC_DISCOVERY_ACTIVE_20260711_HUMAN_AUDIT_TEMPLATE.json")
    parser.add_argument("--anchors", default="P34_1_PAPER_INDEX_HUMAN_ANCHORS_HARDNEG20_TEMPLATE_20260711.json")
    parser.add_argument("--calibration", default="P34_CODEX_PILOT_AUDIT_YE3NRNRYOY_20260711.json")
    parser.add_argument("--env-file", default=".env")
    parser.add_argument("--ledger", default="P34_FULL_AI_PILOT_LEDGER_20260711.jsonl")
    parser.add_argument("--output-json", default="P34_FULL_AI_PILOT_AUDIT_HARDNEG20_20260711.json")
    parser.add_argument("--output-md", default="P34_FULL_AI_PILOT_AUDIT_HARDNEG20_20260711.md")
    parser.add_argument("--max-tokens", type=int, default=4096)
    parser.add_argument("--max-workers", type=int, default=6)
    parser.add_argument("--timeout", type=int, default=600)
    parser.add_argument("--limit", type=int, default=0, help="Audit only the first N selected papers; 0 means all")
    parser.add_argument("--paper-id", action="append", default=[], help="Audit only this paper id; repeatable")
    parser.add_argument("--independent-only", action="store_true", help="Export the two independent audits without adjudication")
    args = parser.parse_args()
    _load_dotenv(Path(args.env_file))

    paper_ids, paper_texts, packets, templates = load_inputs(args)
    paper_ids = list(dict.fromkeys(paper_ids))
    if args.paper_id:
        requested = set(args.paper_id)
        missing = sorted(requested - set(paper_ids))
        if missing:
            raise ValueError(f"unknown paper ids: {missing}")
        paper_ids = [paper_id for paper_id in paper_ids if paper_id in requested]
    if args.limit > 0:
        paper_ids = paper_ids[: args.limit]
    if not paper_ids:
        raise ValueError("no papers selected")
    payloads = {
        paper_id: build_paper_payload(paper_id, paper_texts[paper_id], packets, templates)
        for paper_id in paper_ids
    }
    ledger = Ledger(Path(args.ledger))
    independent_requests = [
        (paper_id, audit_prompt(payloads[paper_id]), payloads[paper_id]) for paper_id in paper_ids
    ]
    audits = {
        code: run_phase("independent", code, independent_requests, ledger, args)
        for code in ("M", "P")
    }
    if args.independent_only:
        report = {
            "schema_version": "p34_full_ai_pilot_independent_v1",
            "status": "INDEPENDENT_COMPLETE",
            "boundary": "AI-assisted pilot only; no formal human gold or ReviewState admission",
            "models": MODEL_CODES,
            "paper_ids": paper_ids,
            "input_hash": _canonical_sha256(payloads),
            "audits": audits,
            "calibration": {
                code: calibrate(values.get("ye3NrNrYOY", {}), _load_json(Path(args.calibration)))
                for code, values in audits.items()
            },
        }
        _atomic_json(Path(args.output_json), report)
        Path(args.output_md).write_text(
            "# P34 Hardneg20 Independent AI Pilot Audits\n\n"
            "AI-assisted pilot only; excluded from formal human gold and runtime admission.\n\n"
            f"- papers: `{len(paper_ids)}`\n"
            f"- calibration: `{report['calibration']}`\n",
            encoding="utf-8",
        )
        print(json.dumps({"status": report["status"], "paper_count": len(paper_ids), "calibration": report["calibration"]}, ensure_ascii=False))
        return 0
    adjudication_requests = [
        (
            paper_id,
            adjudication_prompt(payloads[paper_id], audits["M"][paper_id], audits["P"][paper_id]),
            payloads[paper_id],
        )
        for paper_id in paper_ids
    ]
    final = run_phase("adjudication", "P", adjudication_requests, ledger, args)

    paper_reports = []
    global_counts = {task: Counter() for task in ALLOWED}
    cluster_keys = set()
    raw_issue_count = 0
    for paper_id in paper_ids:
        item = final[paper_id]
        label_counts = {}
        for task in ALLOWED:
            counts = Counter(str(row.get("label") or "") for row in item[task])
            label_counts[task] = dict(counts)
            global_counts[task].update(counts)
        paper_clusters = {str(row.get("cluster_key") or "") for row in item["review_issue"]}
        cluster_keys.update(f"{paper_id}:{key}" for key in paper_clusters)
        raw_issue_count += len(item["review_issue"])
        explicit = {str(value.get("heading") or "") for value in payloads[paper_id]["paper_index"]["explicit_sections"]}
        machine = set(payloads[paper_id]["paper_index"]["machine_boundary_headings"])
        selected_artifacts = set(item["paper_index"].get("key_artifact_ids") or [])
        machine_queries = [value.lower() for value in payloads[paper_id]["paper_index"]["machine_anchor_queries"]]
        artifact_by_id = {value["artifact_id"]: value for value in payloads[paper_id]["paper_index"]["artifacts"]}
        machine_anchor_hits = sum(
            any(query and query in (artifact_by_id.get(artifact_id, {}).get("text") or "").lower() for query in machine_queries)
            for artifact_id in selected_artifacts
        )
        paper_reports.append({
            "paper_id": paper_id,
            "paper_summary_zh": item.get("paper_summary_zh"),
            "tasks": {task: item[task] for task in ALLOWED},
            "paper_index": item["paper_index"],
            "label_counts": label_counts,
            "raw_review_issue_count": len(item["review_issue"]),
            "distinct_cluster_count": len(paper_clusters),
            "paper_index_metrics": {
                "explicit_boundary_count": len(explicit),
                "machine_boundary_count": len(machine),
                "machine_boundary_heading_recall": len(explicit & machine) / len(explicit) if explicit else 1.0,
                "selected_key_artifact_count": len(selected_artifacts),
                "machine_anchor_hit_count": machine_anchor_hits,
                "machine_anchor_recall": machine_anchor_hits / len(selected_artifacts) if selected_artifacts else None,
            },
            "independent_model_outputs": {"M": audits["M"][paper_id], "P": audits["P"][paper_id]},
        })

    calibration = calibrate(final.get("ye3NrNrYOY", {}), _load_json(Path(args.calibration)))
    report = {
        "schema_version": "p34_full_ai_pilot_audit_v1",
        "status": "PASS" if calibration.get("agreement", 0.0) >= 0.80 else "FAIL_CALIBRATION",
        "boundary": "Dual-model AI pilot with Pro adjudication; excluded from formal human gold, gates, Judge targets, and ReviewState",
        "models": {"independent": MODEL_CODES, "adjudicator": MODEL_CODES["P"]},
        "input_hash": _canonical_sha256(payloads),
        "calibration": calibration,
        "summary": {
            "paper_count": len(paper_ids),
            "evidence_label_counts": dict(global_counts["evidence_relation"]),
            "claim_label_counts": dict(global_counts["claim_faithfulness"]),
            "review_label_counts": dict(global_counts["review_issue"]),
            "raw_review_issue_count": raw_issue_count,
            "distinct_cluster_count": len(cluster_keys),
            "duplicate_rate": 1.0 - (len(cluster_keys) / raw_issue_count if raw_issue_count else 1.0),
        },
        "papers": paper_reports,
    }
    _atomic_json(Path(args.output_json), report)
    Path(args.output_md).write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps({"status": report["status"], "summary": report["summary"], "calibration": calibration}, ensure_ascii=False))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
