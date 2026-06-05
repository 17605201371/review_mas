from __future__ import annotations

import argparse
import csv
import json
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
import sys
from typing import Any, Dict, Iterable, List

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agent_system.environments.env_package.review.state import (
    _flaw_has_negative_grounding,
    _is_fallback_or_meta_flaw,
    build_decision_hygiene_view,
    infer_final_recommendation_view,
)

SCHEMA_VERSION = "hygiene_metrics_v1_20260521_admission_shadow"

FIELDNAMES = [
    "schema_version",
    "paper_id",
    "final_decision",
    "decision_correct",
    "reward",
    "recommendation_view",
    "recommendation_binary_decision",
    "recommendation_reason",
    "accept_calibration_warning_count",
    "accept_calibration_warnings",
    "real_strong_support_total",
    "non_abstract_real_strong_support_count",
    "empirical_real_strong_support_count",
    "method_real_strong_support_count",
    "claims_with_real_strong_support",
    "claims_with_2plus_independent_support",
    "claims_with_empirical_real_strong_support",
    "primary_claim_total",
    "primary_claim_support_coverage",
    "primary_claim_empirical_coverage",
    "support_concentration_index",
    "quote_bank_claim_overlap_fallback_used_count",
    "quote_bank_claim_overlap_fallback_real_strong_count",
    "quote_bank_claim_overlap_fallback_semantic_mismatch_count",
    "quote_bank_claim_overlap_fallback_case_sample",
    "semantic_weak_promotion_used_count",
    "semantic_weak_promotion_real_strong_count",
    "semantic_weak_promotion_case_sample",
    "strength_promotion_from_medium_count",
    "strength_promotion_from_medium_real_strong_count",
    "support_admission_tier_counts",
    "support_admission_blocker_counts",
    "final_verified_moderate_support_total",
    "claims_with_verified_moderate_support",
    "verified_medium_support_blocked_count",
    "verified_abstract_support_blocked_count",
    "medium_deep_nonabstract_promotion_candidate_count",
    "medium_nonabstract_shadow_additional_support_count",
    "medium_nonabstract_shadow_real_strong_total",
    "medium_nonabstract_shadow_newly_supported_claim_count",
    "medium_or_abstract_shadow_additional_support_count",
    "medium_or_abstract_shadow_real_strong_total",
    "medium_or_abstract_shadow_newly_supported_claim_count",
    "negative_evidence_candidate_count",
    "negative_evidence_linked_to_flaw_count",
    "negative_evidence_unlinked_to_flaw_count",
    "negative_evidence_binding_retry_candidate_count",
    "negative_grounding_conflict_count",
    "invalid_negative_evidence_id_count",
    "stance_inferred_negative_grounding_count",
    "flaw_total",
    "active_flaw_count",
    "grounded_active_flaw_count",
    "grounded_major_or_critical_flaw_count",
    "support_only_flaw_filtered_count",
    "total_limitation_count",
    "actionable_limitation_count",
    "context_limitation_count",
    "unresolved_diagnostic_count",
    "stale_limitation_count",
    "actionable_limitation_ratio",
    "diagnostic_useful_limitation_ratio",
    "open_evidence_gap_count",
    "stale_evidence_gap_count",
    "open_conflict_count",
    "stale_conflict_count",
    "recovery_committed_turn_count",
]


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _json_counter(value: Any) -> Counter:
    if isinstance(value, str):
        if not value.strip():
            return Counter()
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            return Counter()
    if not isinstance(value, dict):
        return Counter()
    return Counter({str(key): _safe_int(count) for key, count in value.items()})


def _git_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        return ""


def _active_flaws(state: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [
        flaw
        for flaw in state.get("flaw_candidates", []) or []
        if isinstance(flaw, dict)
        and flaw.get("status") not in {"downgraded", "retracted"}
        and not _is_fallback_or_meta_flaw(flaw)
    ]


def row_for_record(record: Dict[str, Any]) -> Dict[str, Any]:
    state = record.get("review_state") or {}
    decision_state = build_decision_hygiene_view(state)
    hygiene = decision_state.get("decision_hygiene", {}) or {}
    recommendation = infer_final_recommendation_view(state, {})
    active_flaws = _active_flaws(decision_state)
    grounded_flaws = [flaw for flaw in active_flaws if _flaw_has_negative_grounding(flaw, decision_state)]
    grounded_major_or_critical = [
        flaw for flaw in grounded_flaws if flaw.get("severity") in {"major", "critical"}
    ]
    recovery_commits = 0
    for turn in record.get("turn_logs", []) or []:
        if isinstance(turn, dict) and turn.get("recovery_committed"):
            recovery_commits += 1
    row: Dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "paper_id": record.get("paper_id", ""),
        "final_decision": record.get("final_decision", ""),
        "decision_correct": _safe_float(record.get("decision_correct")),
        "reward": _safe_float(record.get("reward")),
        "recommendation_view": recommendation.get("recommendation_view", ""),
        "recommendation_binary_decision": recommendation.get("binary_decision", ""),
        "recommendation_reason": recommendation.get("reason", ""),
        "accept_calibration_warning_count": _safe_int(recommendation.get("accept_calibration_warning_count")),
        "accept_calibration_warnings": ";".join(recommendation.get("accept_calibration_warnings") or []),
        "flaw_total": len(decision_state.get("flaw_candidates", []) or []),
        "active_flaw_count": len(active_flaws),
        "grounded_active_flaw_count": len(grounded_flaws),
        "grounded_major_or_critical_flaw_count": len(grounded_major_or_critical),
        "recovery_committed_turn_count": recovery_commits,
    }
    for key in FIELDNAMES:
        if key in row:
            continue
        value = hygiene.get(key)
        if isinstance(value, (list, dict)):
            row[key] = json.dumps(value, ensure_ascii=False, sort_keys=True)
        elif value is None:
            row[key] = 0
        else:
            row[key] = value
    return row


def iter_jsonl(path: Path) -> Iterable[Dict[str, Any]]:
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                yield json.loads(line)


def collect_rows(path: Path) -> List[Dict[str, Any]]:
    return [row_for_record(record) for record in iter_jsonl(path)]


def aggregate_rows(rows: List[Dict[str, Any]], *, input_path: str = "") -> Dict[str, Any]:
    numeric_totals: Dict[str, float] = defaultdict(float)
    numeric_keys = [
        key
        for key in FIELDNAMES
        if key not in {
            "schema_version",
            "paper_id",
            "final_decision",
            "recommendation_view",
            "recommendation_binary_decision",
            "recommendation_reason",
            "accept_calibration_warnings",
            "quote_bank_claim_overlap_fallback_case_sample",
            "semantic_weak_promotion_case_sample",
            "support_admission_tier_counts",
            "support_admission_blocker_counts",
        }
    ]
    support_admission_tier_counts = Counter()
    support_admission_blocker_counts = Counter()
    for row in rows:
        for key in numeric_keys:
            numeric_totals[key] += _safe_float(row.get(key))
        support_admission_tier_counts.update(_json_counter(row.get("support_admission_tier_counts")))
        support_admission_blocker_counts.update(_json_counter(row.get("support_admission_blocker_counts")))
    row_count = len(rows)
    decision_correct_total = numeric_totals.get("decision_correct", 0.0)
    reward_total = numeric_totals.get("reward", 0.0)
    return {
        "schema_version": SCHEMA_VERSION,
        "input_path": input_path,
        "git_commit": _git_commit(),
        "row_count": row_count,
        "unique_paper_count": len({row.get("paper_id") for row in rows}),
        "decision_accuracy": (decision_correct_total / row_count) if row_count else 0.0,
        "reward_mean": (reward_total / row_count) if row_count else 0.0,
        "final_decision_counts": dict(Counter(row.get("final_decision", "") for row in rows)),
        "recommendation_view_counts": dict(Counter(row.get("recommendation_view", "") for row in rows)),
        "recommendation_binary_counts": dict(Counter(row.get("recommendation_binary_decision", "") for row in rows)),
        "support_admission_tier_counts": dict(support_admission_tier_counts),
        "support_admission_blocker_counts": dict(support_admission_blocker_counts),
        "numeric_totals": dict(numeric_totals),
        "numeric_means": {
            key: (value / row_count if row_count else 0.0)
            for key, value in numeric_totals.items()
        },
    }


def write_csv(rows: List[Dict[str, Any]], path: Path) -> None:
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDNAMES)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in FIELDNAMES})


def main() -> int:
    parser = argparse.ArgumentParser(description="Export deterministic Hygiene metrics for review JSONL artifacts.")
    parser.add_argument("--jsonl", required=True)
    parser.add_argument("--output-csv", required=True)
    parser.add_argument("--output-json", required=True)
    args = parser.parse_args()

    input_path = Path(args.jsonl)
    rows = collect_rows(input_path)
    aggregate = aggregate_rows(rows, input_path=str(input_path))
    write_csv(rows, Path(args.output_csv))
    Path(args.output_json).write_text(json.dumps(aggregate, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"row_count": aggregate["row_count"], "schema_version": SCHEMA_VERSION}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
