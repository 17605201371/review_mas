#!/usr/bin/env python3
"""Case-level audit for recovery turns.

Aggregate ``recovery_effective_repair`` is not enough for the paper narrative:
a state mutation can be useful hygiene without being a recovery around a
reviewer-discovered negative flaw.  This audit classifies every recovery turn
into buckets such as verified review-negative repair, assessment-limitation
routing, state-hygiene repair, or false-positive/no-effect risk.
"""
from __future__ import annotations

import argparse
import copy
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agent_system.environments.env_package.review.state import (
    REVIEW_NEGATIVE_VERIFIED_LABEL,
    _has_trusted_existing_grounding,
    _is_grounded_paper_negative_evidence_record,
    _is_obligation_grounded_review_issue_evidence_record,
    _is_reviewer_absence_audit_evidence_record,
    _negative_evidence_type_for_record,
    _review_negative_label_for_record,
    build_decision_hygiene_view,
)


def _load_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _state_without_cached_hygiene(state: Dict[str, Any]) -> Dict[str, Any]:
    clean = copy.deepcopy(state or {})
    clean.pop("decision_hygiene", None)
    return clean


def _clip(value: Any, limit: int = 180) -> str:
    text = " ".join(str(value or "").split())
    return text if len(text) <= limit else text[: limit - 3] + "..."


def _as_list(value: Any) -> List[Any]:
    if isinstance(value, list):
        return value
    if value in (None, ""):
        return []
    return [value]


def _paper_id(row: Dict[str, Any]) -> str:
    return str(row.get("paper_id") or (row.get("review_state") or {}).get("paper_id") or "")


def _evidence_lookup(state: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    return {
        str(item.get("evidence_id") or ""): item
        for item in state.get("evidence_map", []) or []
        if isinstance(item, dict) and str(item.get("evidence_id") or "")
    }


def _target_text(state: Dict[str, Any], target_type: str, target_id: str) -> str:
    if target_type == "claim":
        for item in state.get("claims", []) or []:
            if isinstance(item, dict) and str(item.get("claim_id") or "") == target_id:
                return _clip(item.get("claim"), 220)
    if target_type == "flaw":
        for item in state.get("flaw_candidates", []) or []:
            if isinstance(item, dict) and str(item.get("flaw_id") or "") == target_id:
                return _clip(" ".join(str(item.get(k) or "") for k in ("title", "description")), 220)
    if target_type == "gap":
        for item in state.get("evidence_gaps", []) or []:
            if not isinstance(item, dict):
                continue
            if str(item.get("gap_id") or "") == target_id or str(item.get("claim_id") or "") == target_id:
                return _clip(item.get("description") or item.get("question") or item.get("text"), 220)
    return ""


def _evidence_bucket(state: Dict[str, Any], evidence: Dict[str, Any]) -> str:
    if not isinstance(evidence, dict) or not evidence:
        return "missing_evidence_id"
    source = str(evidence.get("source") or "").strip().lower()
    source_locator = str(evidence.get("source_locator") or "").strip().lower()
    if source in {"system recovery salvage", "fallback-extraction", "quote-bank-negative-grounding"}:
        return f"{source.replace(' ', '_')}_candidate"
    if source in {"model-output", "model output", "manager_model"} or source_locator in {"model-output", "model output", "manager_model"}:
        return "untrusted_model_output"
    if _is_obligation_grounded_review_issue_evidence_record(evidence, state):
        return "obligation_grounded_review_issue"
    if _is_reviewer_absence_audit_evidence_record(evidence, state):
        return "reviewer_absence_audit"
    if source == "reviewer_absence_audit" or evidence.get("absence_audit_verified"):
        return "stale_reviewer_absence_audit"
    if _is_grounded_paper_negative_evidence_record(evidence, state):
        return "verified_review_negative"
    semantic_label = str(evidence.get("semantic_grounding_label") or "").strip()
    if semantic_label == "semantic_negative_verified":
        review_label = _review_negative_label_for_record(evidence, state)
        return review_label or "semantic_negative_without_review_relation"
    stance = str(evidence.get("stance") or "").strip().lower()
    if stance in {"supports", "partially_supports", "partial_support", "partial-support"}:
        return "support_only"
    if _has_trusted_existing_grounding(evidence):
        return "trusted_non_negative_grounding"
    return "not_verified_or_unknown"


def _review_issue_bundle_display(evidence: Dict[str, Any]) -> Tuple[str, str]:
    bundle = evidence.get("review_issue_bundle") if isinstance(evidence, dict) else {}
    if not isinstance(bundle, dict):
        return "", ""
    missing = bundle.get("missing_or_mismatch")
    missing_items: List[str] = []
    if isinstance(missing, dict):
        missing_items = [str(item) for item in (missing.get("items") or [missing.get("entity")]) if str(item or "").strip()]
    inventory = [item for item in (bundle.get("observed_inventory") or []) if isinstance(item, dict)]
    inv0 = inventory[0] if inventory else {}
    locator = _clip(inv0.get("locator") or evidence.get("source_locator") or evidence.get("source"), 120)
    missing_text = "; ".join(_clip(item, 90) for item in missing_items)
    inventory_quote = _clip(inv0.get("quote"), 150)
    if missing_text and inventory_quote:
        return locator, f"missing/mismatch: {missing_text}; observed inventory: {inventory_quote}"
    if missing_text:
        return locator, f"missing/mismatch: {missing_text}"
    if inventory_quote:
        return locator, f"observed inventory: {inventory_quote}"
    return locator, ""


def _evidence_summary(state: Dict[str, Any], evidence_ids: List[str]) -> Tuple[List[Dict[str, Any]], Counter]:
    by_id = _evidence_lookup(state)
    summaries: List[Dict[str, Any]] = []
    counts: Counter = Counter()
    for evidence_id in evidence_ids:
        evidence = by_id.get(str(evidence_id) or "", {})
        bucket = _evidence_bucket(state, evidence)
        counts[bucket] += 1
        display_locator = _clip((evidence or {}).get("source_locator") or (evidence or {}).get("source"), 120)
        display_quote = _clip((evidence or {}).get("raw_quote") or (evidence or {}).get("evidence"), 220)
        if bucket == "obligation_grounded_review_issue":
            bundle_locator, bundle_quote = _review_issue_bundle_display(evidence)
            display_locator = bundle_locator or display_locator
            display_quote = bundle_quote or display_quote
        summaries.append(
            {
                "evidence_id": str(evidence_id),
                "bucket": bucket,
                "negative_type": _negative_evidence_type_for_record(evidence) if evidence else "",
                "review_negative_label": _review_negative_label_for_record(evidence, state) if evidence else "",
                "trusted_grounding": bool(evidence and _has_trusted_existing_grounding(evidence)),
                "locator": display_locator,
                "raw_quote": display_quote,
            }
        )
    return summaries, counts


def _narrative_bucket(turn: Dict[str, Any], evidence_counts: Counter) -> str:
    operation = str(turn.get("recovery_patch_operation") or "").strip()
    layer = str(turn.get("recovery_layer") or "").strip()
    effective = bool(turn.get("recovery_effective_repair"))
    committed = bool(turn.get("recovery_committed") or turn.get("recovery_patch_committed"))
    attempted = bool(turn.get("recovery_attempted") or turn.get("recovery_patch_mode_entered"))
    if not attempted:
        return "not_recovery_turn"
    if not committed:
        return "attempted_not_committed"
    if not effective:
        return "committed_not_effective"
    if operation in {"downgrade_claim_to_unsupported", "mark_contested"}:
        if evidence_counts.get("verified_review_negative", 0) > 0:
            return "verified_review_negative_repair"
        if evidence_counts.get("obligation_grounded_review_issue", 0) > 0:
            return "verified_review_issue_repair"
        if evidence_counts.get("reviewer_absence_audit", 0) > 0:
            return "reviewer_inferred_negative_repair"
        return "effective_repair_without_verified_negative"
    if operation == "route_to_assessment_limitation":
        return "assessment_limitation_routing"
    if operation in {"resolve_stale_gap", "rebind_evidence"}:
        return "state_hygiene_repair"
    if operation == "downgrade_final_to_candidate":
        if evidence_counts.get("verified_review_negative", 0) > 0:
            return "verified_negative_flaw_lifecycle_downgrade"
        if evidence_counts.get("obligation_grounded_review_issue", 0) > 0:
            return "verified_review_issue_lifecycle_downgrade"
        if evidence_counts.get("reviewer_absence_audit", 0) > 0:
            return "reviewer_inferred_flaw_lifecycle_downgrade"
        return "flaw_lifecycle_downgrade_needs_manual_review"
    return layer or "effective_repair_needs_manual_review"


def build_recovery_case_table(rows: Iterable[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Counter]:
    cases: List[Dict[str, Any]] = []
    summary: Counter = Counter()
    for row in rows:
        pid = _paper_id(row)
        raw_state = row.get("review_state") or {}
        if not isinstance(raw_state, dict):
            summary["invalid_state_rows"] += 1
            continue
        try:
            state = build_decision_hygiene_view(_state_without_cached_hygiene(raw_state))
        except Exception as exc:  # pragma: no cover - defensive for old artifacts
            summary["decision_hygiene_errors"] += 1
            cases.append(
                {
                    "paper_id": pid,
                    "turn_id": "",
                    "narrative_bucket": "decision_hygiene_error",
                    "reason": _clip(str(exc), 240),
                }
            )
            continue

        for turn in row.get("turn_logs", []) or []:
            if not isinstance(turn, dict):
                continue
            attempted = bool(turn.get("recovery_attempted") or turn.get("recovery_patch_mode_entered"))
            committed = bool(turn.get("recovery_committed") or turn.get("recovery_patch_committed"))
            effective = bool(turn.get("recovery_effective_repair"))
            if not (attempted or committed or effective):
                continue
            evidence_ids = [str(item) for item in _as_list(turn.get("supporting_evidence_ids")) if str(item)]
            evidence_rows, evidence_counts = _evidence_summary(state, evidence_ids)
            bucket = _narrative_bucket(turn, evidence_counts)
            summary[f"bucket::{bucket}"] += 1
            operation = str(turn.get("recovery_patch_operation") or "")
            if operation:
                summary[f"operation::{operation}"] += 1
            if effective:
                summary["effective_repair_turns"] += 1
                if bucket != "verified_review_negative_repair":
                    summary["effective_repair_not_verified_negative_repair"] += 1
            if evidence_counts.get("verified_review_negative", 0):
                summary["turns_with_verified_review_negative_evidence"] += 1
            if evidence_counts.get("obligation_grounded_review_issue", 0):
                summary["turns_with_verified_review_issue_bundle_evidence"] += 1
            if evidence_counts.get("reviewer_absence_audit", 0):
                summary["turns_with_reviewer_absence_audit_evidence"] += 1
            if evidence_counts:
                for key, value in evidence_counts.items():
                    summary[f"evidence_bucket::{key}"] += value
            cases.append(
                {
                    "paper_id": pid,
                    "turn_id": turn.get("turn_id") or turn.get("turn_index") or "",
                    "narrative_bucket": bucket,
                    "recovery_layer": turn.get("recovery_layer", ""),
                    "effective_repair": effective,
                    "committed": committed,
                    "operation": operation,
                    "target_type": turn.get("recovery_target_type", ""),
                    "target_id": turn.get("recovery_target_id", ""),
                    "target_text": _target_text(
                        state,
                        str(turn.get("recovery_target_type") or ""),
                        str(turn.get("recovery_target_id") or ""),
                    ),
                    "old_status": turn.get("old_status", ""),
                    "new_status": turn.get("new_status", ""),
                    "failure_code": turn.get("recovery_failure_code", ""),
                    "supporting_evidence_ids": evidence_ids,
                    "evidence_buckets": dict(evidence_counts),
                    "evidence": evidence_rows,
                }
            )
    summary["case_rows"] = len(cases)
    return cases, summary


def _md_table(headers: List[str], rows: List[List[Any]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        cells = [str(cell).replace("|", "\\|").replace("\n", " ") for cell in row]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def render_markdown(cases: List[Dict[str, Any]], summary: Counter) -> str:
    lines = [
        "# Recovery Case Audit v1",
        "",
        "## Summary",
        "",
        _md_table(["metric", "count"], [[key, value] for key, value in sorted(summary.items())]),
        "",
        "## Recovery Cases",
        "",
        _md_table(
            [
                "paper_id",
                "turn",
                "bucket",
                "operation",
                "layer",
                "target",
                "status",
                "evidence_buckets",
            ],
            [
                [
                    row.get("paper_id", ""),
                    row.get("turn_id", ""),
                    row.get("narrative_bucket", ""),
                    row.get("operation", ""),
                    row.get("recovery_layer", ""),
                    f"{row.get('target_type', '')}:{row.get('target_id', '')}",
                    f"{row.get('old_status', '')}->{row.get('new_status', '')}",
                    json.dumps(row.get("evidence_buckets", {}), ensure_ascii=False, sort_keys=True),
                ]
                for row in cases[:120]
            ],
        ),
        "",
        "## Evidence Details",
        "",
    ]
    detail_rows: List[List[Any]] = []
    for row in cases[:120]:
        for evidence in row.get("evidence", []) or []:
            detail_rows.append(
                [
                    row.get("paper_id", ""),
                    row.get("turn_id", ""),
                    row.get("narrative_bucket", ""),
                    evidence.get("evidence_id", ""),
                    evidence.get("bucket", ""),
                    evidence.get("negative_type", ""),
                    evidence.get("review_negative_label", ""),
                    evidence.get("locator", ""),
                    evidence.get("raw_quote", ""),
                ]
            )
    lines.append(
        _md_table(
            [
                "paper_id",
                "turn",
                "case_bucket",
                "evidence_id",
                "evidence_bucket",
                "negative_type",
                "review_label",
                "locator",
                "quote",
            ],
            detail_rows,
        )
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--output-md", required=True)
    args = parser.parse_args()
    rows = _load_jsonl(Path(args.input))
    cases, summary = build_recovery_case_table(rows)
    payload = {
        "input": args.input,
        "summary": dict(summary),
        "cases": cases,
    }
    Path(args.output_json).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    Path(args.output_md).write_text(render_markdown(cases, summary), encoding="utf-8")


if __name__ == "__main__":
    main()
