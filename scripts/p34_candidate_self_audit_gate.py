#!/usr/bin/env python3
"""P34 candidate-level self-audit gate v2 (abstention mechanics).

v1 (2026-07-11 morning) was a diagnostic sidecar only: it produced flags in a
report but no pipeline-connectable output, so quota-filling was diagnosed but
not solved. The strict regex-drop mode was validated AGAINST the 377-label
diagnostic set and rejected (killed 56% of B while catching only 34% of D):
regex co-occurrence can retrieve candidate windows but cannot judge whether a
window resolves a concern. That division of labor is now explicit:

  * mechanical layer (this script): structural field checks + exact-span
    counterevidence RETRIEVAL, emitting auditable evidence windows;
  * judgment layer (LLM Judge with quote backfill): decides refuted / valid /
    uncertain using the attached windows. Never this script.

v2 outputs real pipeline artifacts:
  * --mode enrich  (default): every packet is re-emitted with a `self_audit`
    block and exact-span `counterevidence_windows` (round-trip verified against
    the raw paper text). Nothing is deleted.
  * --mode strict  : emits only passing packets to --out-packets-jsonl and a
    dropped-manifest sidecar. Kept for ablation ONLY — validated to over-block;
    must not gate admission.
  * --require-self-audit-fields : forward contract for NEW discovery runs —
    candidates missing searched_sections / absence_check_terms / confidence are
    structurally invalid (field presence is mechanically decidable; field
    truthfulness is not, and is NOT claimed here — real retrieval traces must
    be recorded by the harness, not self-reported).

Every window carries source_span_start/end into the RAW paper text plus the
raw quote slice, the paper text sha256, the query terms, and (best effort) the
PaperIndex section id, so a downstream Judge can quote-backfill mechanically.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
for entry in (str(REPO_ROOT / "scripts"), str(REPO_ROOT)):
    if entry not in sys.path:
        sys.path.insert(0, entry)

from p33_semantic_verifier_dryrun import _anchor_found  # noqa: E402  (read-only reuse)

ABSENCE_ISSUE_TYPES = {
    "missing_ablation",
    "missing_baseline",
    "insufficient_evaluation",
    "statistical_or_reporting_gap",
    "reproducibility_gap",
    "missing_robustness_or_generalization",
    "efficiency_cost_gap",
}

RESOLVING_MARKERS: Dict[str, str] = {
    "missing_ablation": r"ablat\w*|w/o\b|without\b|variant\w*|remov\w*|component-?wise|isolat\w*",
    "missing_baseline": r"baseline\w*|compar\w*|versus|vs\.?\s|outperform\w*|Table\s*\d",
    "insufficient_evaluation": r"evaluat\w*|benchmark\w*|dataset\w*|experiment\w*|Table\s*\d",
    "statistical_or_reporting_gap": r"standard deviation|std\b|confidence interval|±|p-value|p\s*<|seeds?\b|variance|error bar",
    "reproducibility_gap": r"hyperparameter\w*|learning rate|weight decay|epochs?\b|seeds?\b|code\b|implementation detail\w*|optimizer",
    "missing_robustness_or_generalization": r"robust\w*|generaliz\w*|cross-?(?:domain|dataset)|transfer\b|out-of-distribution|OOD\b",
    "efficiency_cost_gap": r"FLOPs?\b|runtime|latency|memory|GPU\s*(?:hours?|days?)|paramet\w*|inference time|training time|computational cost",
}

CONFIDENCE_FLOOR = 0.5
ENTITY_MIN_LEN = 4
WINDOW = 420
TOP_K_WINDOWS = 3
SELF_AUDIT_REQUIRED_FIELDS = ("searched_sections", "absence_check_terms", "confidence")


# ------------------------------------------------------------------------- io
def _load_json(path: Path) -> Dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def _load_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            row = json.loads(line)
            if isinstance(row, dict):
                rows.append(row)
    return rows


def _write_jsonl(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )


def _norm(value: Any) -> str:
    return str(value or "").strip()


def paper_text_by_lower_id(rows: Sequence[Mapping[str, Any]]) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for row in rows:
        state = row.get("review_state") or {}
        if not isinstance(state, dict):
            state = {}
        paper_id = _norm(row.get("paper_id") or state.get("paper_id"))
        if paper_id:
            # Lowercase join key (2026-07-07 case-mismatch lesson).
            out[paper_id.lower()] = str(state.get("paper_text") or "")
    return out


def _paper_sections(paper_text: str) -> List[Dict[str, Any]]:
    """Best-effort PaperIndex sections for offset->section_id mapping."""
    try:
        from agent_system.environments.env_package.review.paper_index import build_paper_index

        index = build_paper_index(paper_text)
        sections = getattr(index, "sections", None) or []
        out = []
        for section in sections:
            data = section if isinstance(section, dict) else getattr(section, "__dict__", {})
            out.append({
                "section_id": _norm(data.get("section_id")),
                "start": int(data.get("source_span_start") or 0),
                "end": int(data.get("source_span_end") or 0),
            })
        return out
    except Exception:
        return []


def _section_for_offset(sections: Sequence[Mapping[str, Any]], offset: int) -> str:
    for section in sections:
        if section["start"] <= offset < section["end"]:
            return section["section_id"]
    return ""


# ------------------------------------------------------------------- checks
def _entities(packet: Mapping[str, Any]) -> List[str]:
    hyp = packet.get("issue_hypothesis") or {}
    raw = hyp.get("named_entities_or_metrics") or []
    if isinstance(raw, str):
        raw = [raw]
    seen: List[str] = []
    for item in raw:
        text = _norm(item)
        if len(text) >= ENTITY_MIN_LEN and text.lower() not in {s.lower() for s in seen}:
            seen.append(text)
    return seen[:10]


def _hypothesis_fields(packet: Mapping[str, Any]) -> Dict[str, Any]:
    hyp = packet.get("issue_hypothesis") or {}
    contract = packet.get("verification_contract") or {}
    return {
        "issue_type": _norm(hyp.get("issue_type") or contract.get("issue_type")).lower(),
        "paper_anchor": _norm(hyp.get("paper_anchor")),
        "claim_anchor": _norm(hyp.get("claim_anchor")),
        "confidence": hyp.get("confidence"),
        "self_audit_missing": [
            field for field in SELF_AUDIT_REQUIRED_FIELDS
            if not _norm(hyp.get(field)) and hyp.get(field) not in (0, 0.0)
        ],
    }


def _counterevidence_windows(
    paper_text: str,
    issue_type: str,
    entities: Sequence[str],
    *,
    paper_sha: str,
    sections: Sequence[Mapping[str, Any]],
    packet_id: str = "",
    top_k: int = TOP_K_WINDOWS,
) -> List[Dict[str, Any]]:
    """Exact-span retrieval of candidate resolving windows. RETRIEVAL ONLY:
    a hit means "the Judge should look here", never "the candidate is wrong".

    Emitted in the existing evidence-id contract (evidence_id + section_id +
    source_span + quote + retrieval_query + full paper_text_sha256) so the Judge
    can legally cite them via ``counterevidence_candidates`` / section IDs.

    Windows are quality-ranked (not first-hit): a direct issue-type marker and a
    results/analysis/table section outrank a related-work or intro mention.
    """
    marker = RESOLVING_MARKERS.get(issue_type)
    if not marker or not paper_text or not entities:
        return []
    section_rank = {"results": 0, "analysis": 0, "experiment": 0, "ablation": 0,
                    "table": 0, "evaluation": 1, "method": 2, "approach": 2,
                    "introduction": 4, "related": 5, "background": 5}

    def _rank(section_id: str) -> int:
        low = section_id.lower()
        for key, value in section_rank.items():
            if key in low:
                return value
        return 3

    scored: List[tuple] = []
    taken: List[tuple] = []
    for entity in entities:
        for match in re.finditer(re.escape(entity), paper_text, flags=re.IGNORECASE):
            start = max(0, match.start() - WINDOW // 2)
            end = min(len(paper_text), match.end() + WINDOW)
            if any(min(end, e) - max(start, s) > WINDOW // 2 for s, e in taken):
                continue
            window_text = paper_text[start:end]
            marker_match = re.search(marker, window_text, flags=re.IGNORECASE)
            if not marker_match:
                continue
            taken.append((start, end))
            section_id = _section_for_offset(sections, match.start())
            # direct marker adjacency (marker within ~120 chars of entity) ranks higher
            adjacency = abs((start + marker_match.start()) - match.start())
            scored.append((
                _rank(section_id), adjacency,
                {
                    "evidence_id": f"ce-window-{packet_id}-{len(scored) + 1}" if packet_id
                    else f"ce-window-{len(scored) + 1}",
                    "source_id": f"ce-window-{packet_id}-{len(scored) + 1}" if packet_id
                    else f"ce-window-{len(scored) + 1}",
                    "evidence_kind": "mechanical_counterevidence_retrieval",
                    "entity": entity,
                    "matched_marker": marker_match.group(0),
                    "marker_regex": marker,
                    "source_span_start": start,
                    "source_span_end": end,
                    "quote": window_text,  # raw slice; round-trips by construction
                    "match_type": "exact_span_raw_slice",
                    "retrieval_query": entity,
                    "entity_offset": match.start(),
                    "section_id": section_id,
                    "paper_text_sha256": paper_sha,
                },
            ))
    scored.sort(key=lambda item: (item[0], item[1]))
    return [entry for _, _, entry in scored[:top_k]]


def audit_packet(
    packet: Mapping[str, Any],
    paper_text: str,
    *,
    strict: bool = False,
    require_self_audit_fields: bool = False,
    sections: Sequence[Mapping[str, Any]] = (),
    paper_sha: str = "",
) -> Dict[str, Any]:
    fields = _hypothesis_fields(packet)
    result: Dict[str, Any] = {
        "packet_id": _norm(packet.get("packet_id")),
        "paper_id": _norm(packet.get("paper_id")),
        "issue_type": fields["issue_type"],
        "checks": {},
    }

    anchor = fields["paper_anchor"] or fields["claim_anchor"]
    anchor_ok = bool(paper_text) and bool(anchor) and _anchor_found(paper_text, anchor)
    result["checks"]["anchor_located"] = anchor_ok

    confidence = fields["confidence"]
    confidence_missing = confidence is None
    if confidence_missing:
        confidence_ok = True  # legacy packets: flag, do not silently punish
    else:
        try:
            confidence_ok = float(confidence) >= CONFIDENCE_FLOOR
        except (TypeError, ValueError):
            confidence_ok = False
    result["checks"]["confidence_ok"] = confidence_ok
    result["checks"]["confidence_missing"] = confidence_missing

    missing_fields = fields["self_audit_missing"]
    result["checks"]["self_audit_fields_missing"] = missing_fields

    windows: List[Dict[str, Any]] = []
    if fields["issue_type"] in ABSENCE_ISSUE_TYPES:
        windows = _counterevidence_windows(
            paper_text, fields["issue_type"], _entities(packet),
            paper_sha=paper_sha, sections=sections,
            packet_id=_norm(packet.get("packet_id")),
        )
    result["checks"]["counterevidence_window_count"] = len(windows)
    if windows:
        result["counterevidence_windows"] = windows

    if require_self_audit_fields and missing_fields:
        result["gate"] = "invalid_missing_self_audit_fields"
    elif not anchor_ok:
        result["gate"] = "drop_anchor_unlocatable" if strict else "flag_anchor_unlocatable"
    elif not confidence_ok:
        result["gate"] = "drop_low_confidence" if strict else "flag_low_confidence"
    elif windows:
        result["gate"] = "drop_paper_counterevidence" if strict else "flag_counterevidence_window"
    else:
        result["gate"] = "pass"
    return result


# --------------------------------------------------------------- evaluation
def _labels_by_packet(audit_json: Mapping[str, Any]) -> Dict[str, str]:
    labels: Dict[str, str] = {}
    for paper in audit_json.get("papers", []):
        for _, items in (paper.get("tasks") or {}).items():
            for item in items:
                pid = _norm(item.get("packet_id"))
                if pid.startswith("discovery"):
                    labels[pid] = _norm(item.get("label")).upper()
    return labels


# --------------------------------------------------------------------- main
def build_report(args: argparse.Namespace) -> Dict[str, Any]:
    packets = _load_jsonl(Path(args.packets_jsonl))
    texts = paper_text_by_lower_id(_load_jsonl(Path(args.input_jsonl)))
    strict = args.mode == "strict"

    section_cache: Dict[str, List[Dict[str, Any]]] = {}
    sha_cache: Dict[str, str] = {}
    results: List[Dict[str, Any]] = []
    enriched: List[Dict[str, Any]] = []
    kept: List[Dict[str, Any]] = []
    dropped: List[Dict[str, Any]] = []
    invalid: List[Dict[str, Any]] = []

    for packet in packets:
        pid = _norm(packet.get("paper_id")).lower()
        paper_text = texts.get(pid, "")
        if pid not in sha_cache:
            sha_cache[pid] = hashlib.sha256(paper_text.encode("utf-8")).hexdigest()
            section_cache[pid] = _paper_sections(paper_text)
        result = audit_packet(
            packet, paper_text,
            strict=strict,
            require_self_audit_fields=args.require_self_audit_fields,
            sections=section_cache[pid],
            paper_sha=sha_cache[pid],
        )
        results.append(result)

        windows = result.get("counterevidence_windows") or []
        out_packet = dict(packet)
        out_packet["self_audit"] = {
            "gate": result["gate"],
            "checks": result["checks"],
            "rubric_note": "windows are retrieval hints for the Judge, not verdicts",
        }
        # Merge windows into the EXISTING Judge evidence-id contract so they are
        # legally citable: counterevidence_candidates carries evidence_id, and
        # every window section_id is added to searched_section_ids.
        if windows:
            merged = list(out_packet.get("counterevidence_candidates") or [])
            merged.extend(windows)
            out_packet["counterevidence_candidates"] = merged
            searched = list(out_packet.get("searched_section_ids") or [])
            for window in windows:
                sid = window.get("section_id")
                if sid and sid not in searched:
                    searched.append(sid)
            out_packet["searched_section_ids"] = searched
            out_packet["counterevidence_windows"] = windows  # mirror for humans

        # Two orthogonal dimensions (GPT cross-audit 2026-07-11):
        #  * contract_invalid  -> blocked in ALL modes, never reaches the Judge
        #  * counterevidence_hit -> enrich attaches evidence, never deletes
        #  * strict_regex_drop -> ablation only (validated to over-block)
        contract_invalid = result["gate"] == "invalid_missing_self_audit_fields"
        if contract_invalid:
            invalid.append({"packet_id": result["packet_id"],
                            "gate": result["gate"],
                            "self_audit_fields_missing": result["checks"]["self_audit_fields_missing"]})
            continue  # blocked in every mode; not emitted to Judge
        enriched.append(out_packet)
        if strict and result["gate"].startswith("drop_"):
            dropped.append({"packet_id": result["packet_id"], "gate": result["gate"]})
        else:
            kept.append(out_packet)

    gate_counts = Counter(r["gate"] for r in results)
    summary: Dict[str, Any] = {
        "mode": args.mode,
        "require_self_audit_fields": bool(args.require_self_audit_fields),
        "packet_count": len(results),
        "gate_counts": dict(gate_counts),
        "contract_invalid_count": len(invalid),
        "emitted_to_judge_count": len(enriched),
        "kept_count": len(kept),
        "dropped_count": len(dropped),
        "roundtrip_note": "every window quote is a raw paper_text slice at [source_span_start:source_span_end]",
    }

    if args.labels_json:
        labels = _labels_by_packet(_load_json(Path(args.labels_json)))
        matrix: Dict[str, Counter] = {}
        for r in results:
            label = labels.get(r["packet_id"], "")
            if label:
                matrix.setdefault(label, Counter())[r["gate"]] += 1
        summary["evaluation"] = {
            "note": "diagnostic labels, not gold; enrich-mode non-pass gates are flags (packet kept)",
            "label_gate_matrix": {k: dict(v) for k, v in sorted(matrix.items())},
            "label_join_missing": sum(1 for r in results if r["packet_id"] not in labels),
        }

    return {
        "label": args.label or "P34_CANDIDATE_SELF_AUDIT_GATE_V2",
        "packets_jsonl": str(args.packets_jsonl),
        "input_jsonl": str(args.input_jsonl),
        "confidence_floor": CONFIDENCE_FLOOR,
        "top_k_windows": TOP_K_WINDOWS,
        "summary": summary,
        "results": results,
        "_enriched": enriched,
        "_kept": kept,
        "_dropped": dropped,
        "_invalid": invalid,
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="P34 candidate self-audit gate v2 (sidecar)")
    parser.add_argument("--packets-jsonl", required=True)
    parser.add_argument("--input-jsonl", required=True)
    parser.add_argument("--labels-json", default="")
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-md", default="")
    parser.add_argument("--out-packets-jsonl", default="",
                        help="pipeline output: enrich mode writes ALL packets with self_audit + windows; strict mode writes only passing packets")
    parser.add_argument("--out-dropped-jsonl", default="",
                        help="strict mode: manifest of dropped packet ids + reasons")
    parser.add_argument("--label", default="")
    parser.add_argument("--mode", choices=["enrich", "strict"], default="enrich",
                        help="enrich (default): attach windows, drop nothing; strict: hard drops — validated to over-block on 2026-07-11 diagnostic labels, ablation use only")
    parser.add_argument("--require-self-audit-fields", action="store_true",
                        help="forward contract for new discovery runs: missing searched_sections/absence_check_terms/confidence => structurally invalid")
    args = parser.parse_args(argv)

    report = build_report(args)
    enriched = report.pop("_enriched")
    kept = report.pop("_kept")
    dropped = report.pop("_dropped")
    invalid = report.pop("_invalid")

    Path(args.out_json).write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    if args.out_packets_jsonl:
        # enrich: emit contract-VALID packets with attached evidence (never invalid).
        # strict: emit only passing packets. Invalid packets never reach the Judge.
        _write_jsonl(Path(args.out_packets_jsonl), enriched if args.mode == "enrich" else kept)
    if args.out_dropped_jsonl:
        _write_jsonl(Path(args.out_dropped_jsonl), dropped + invalid)
    if args.out_md:
        s = report["summary"]
        lines = [f"# {report['label']}", "",
                 f"- mode: `{s['mode']}` packets: `{s['packet_count']}` kept: `{s['kept_count']}` dropped: `{s['dropped_count']}`",
                 f"- gate counts: `{s['gate_counts']}`"]
        if s.get("evaluation"):
            lines += [f"- label × gate: `{s['evaluation']['label_gate_matrix']}`",
                      f"- label join missing: `{s['evaluation']['label_join_missing']}`"]
        Path(args.out_md).write_text("\n".join(lines), encoding="utf-8")

    s = report["summary"]
    print(f"[GATE-V2] mode={s['mode']} packets={s['packet_count']} "
          f"emitted_to_judge={s['emitted_to_judge_count']} contract_invalid={s['contract_invalid_count']} "
          f"kept={s['kept_count']} dropped={s['dropped_count']} gates={s['gate_counts']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
