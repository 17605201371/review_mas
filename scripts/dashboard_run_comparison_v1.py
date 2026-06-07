#!/usr/bin/env python3
"""Run-comparison dashboard for mainline review_infer artifacts.

Aggregates a single .jsonl run (or compares two runs side-by-side) on the
fixed metric set agreed in the P26 optimization plan. Always evaluates the
"must-protect" lines and exits non-zero (when --fail-on-violation is set) if
any of them regress.

Field groups
------------

- Positive: real_strong, empirical, method, table_figure, result_or_experiment,
  abstract, independent_support_group, zero_real_papers, claims_with_real_strong,
  primary_claims_with_real_strong, primary_claims_with_empirical_support,
  primary_claims_with_deep_support.
- Negative: negative_evidence_candidate, verified_negative_flaw,
  verified_potential_concern, grounded_weakness, negative_evidence_unlinked.
- Contested: contested_support_total, contested_final_support_total,
  claims_with_contested_support, claims_with_contested_final_support,
  open_conflict_count.
- Recovery: recovery_attempted, recovery_patch_validated,
  recovery_patch_committed, recovery_layer_hygiene_delta_improved,
  recovery_success (SUCCESS failure_code count), failure_code histogram.
- Hygiene: final_nonreal_strong_support, low_score_promoted_strong,
  user_report_leakage, final_report_leakage, synthetic_marker_in_supporting,
  negative_evidence_unlinked_to_flaw.

Usage
-----

Single run:
    python scripts/dashboard_run_comparison_v1.py \
        --candidate path/to/run.jsonl \
        --output-md path/to/report.md

Compare two runs:
    python scripts/dashboard_run_comparison_v1.py \
        --baseline path/to/baseline.jsonl --label-baseline FROZEN \
        --candidate path/to/candidate.jsonl --label-candidate P0_1a \
        --output-md path/to/cmp.md --fail-on-violation
"""
from __future__ import annotations

import argparse
import copy
import json
import math
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agent_system.environments.env_package.review.state import (
    _build_support_survival_trace,
    _classify_negative_evidence_type,
    build_decision_hygiene_view,
)


# ---------- shared constants ---------------------------------------------

LEAK_TERMS = (
    "7. Audit Trace",
    "audit trace",
    "binary_decision",
    "recommendation_view",
    "Final Decision:",
    "internal ids",
    "internal id",
    "system did not see",
    "evidence was filtered",
    "Positive/support evidence was filtered",
    "negative evidence formation",
    "copied negative_or_gap",
    "hard-negative evidence",
    "system salvage",
    "system recovery",
    "recovery operation",
    "recovery patch",
    "evidence-recovery-missing",
)

# Evidence ids whose prefix indicates program-generated synthetic / placeholder
# evidence. These must never end up in turn_log.supporting_evidence_ids.
SYNTHETIC_EVIDENCE_PREFIXES = (
    "evidence-recovery-missing",
    "evidence-context-",
    "evidence-fallback-",
    "evidence-placeholder-",
    "evidence-synthetic-",
)

# Protection lines (must be true on every candidate run, see P26 plan).
FULL39_REFERENCE_PAPERS = 39

PROTECTION_LINES: List[Tuple[str, str, str]] = [
    # (key, op, threshold)
    ("final_nonreal_strong_support",          "==", "0"),
    ("low_score_promoted_strong",             "==", "0"),
    ("final_report_leakage_paper_count",      "==", "0"),
    ("synthetic_marker_in_supporting_count",  "==", "0"),
    ("negative_evidence_unlinked_to_flaw",    "==", "0"),
    # For smoke/dry-run protection, a weak-target block is a valid safe
    # recovery outcome.  Effective repair is still reported separately; the
    # defense net should not force unsafe commits just to raise commit count.
    ("recovery_safe_resolution_or_clean_state", ">=", "20"),
    ("hygiene_delta_or_safe_block_or_clean_state", ">=", "20"),
    ("real_strong_support_total",             ">=", "30"),
    ("independent_support_group_total",       ">=", "24"),
    ("empirical_real_strong_support_count",   ">=", "20"),
    ("claims_with_deep_support",              ">=", "8"),
    ("support_trace_missing_verified_quote_count", "==", "0"),
    ("support_trace_overridden_by_negative_burden_count", "==", "0"),
    ("evidence_formation_dead_loop_count",   "==", "0"),
    ("programmatic_specific_locator_count",   ">=", "18"),
]


# ---------- helpers ------------------------------------------------------

def _load_jsonl(path: Path) -> List[Dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _hygiene(row: Dict[str, Any]) -> Dict[str, Any]:
    state = row.get("review_state") or {}
    if isinstance(state, dict):
        try:
            state_for_view = copy.deepcopy(state)
            state_for_view.pop("decision_hygiene", None)
            view = build_decision_hygiene_view(state_for_view)
            hygiene = view.get("decision_hygiene") if isinstance(view, dict) else None
            if isinstance(hygiene, dict) and hygiene:
                return hygiene
        except Exception:
            pass
    return (((state or {}).get("state_audit") or {}).get("decision_hygiene") or {})


def _support_trace(row: Dict[str, Any]) -> List[Dict[str, Any]]:
    state = row.get("review_state") or {}
    if not isinstance(state, dict):
        return []
    try:
        state_for_view = copy.deepcopy(state)
        state_for_view.pop("decision_hygiene", None)
        return _build_support_survival_trace(build_decision_hygiene_view(state_for_view))
    except Exception:
        return []


def _sum(rows: Iterable[Dict[str, Any]], key: str) -> int:
    total = 0
    for r in rows:
        v = _hygiene(r).get(key, 0) or 0
        try:
            total += int(v)
        except (TypeError, ValueError):
            continue
    return total


def _paper_has_hygiene_positive(row: Dict[str, Any], key: str) -> bool:
    try:
        return int((_hygiene(row).get(key, 0) or 0)) > 0
    except (TypeError, ValueError):
        return False


def _paper_id(row: Dict[str, Any]) -> str:
    return str(row.get("paper_id") or row.get("id") or (row.get("review_state") or {}).get("paper_id") or "")


def _recovery_turn_delta(tl: Dict[str, Any]) -> Dict[str, Any]:
    delta = tl.get("recovery_state_delta") or {}
    return delta if isinstance(delta, dict) else {}


def _turn_has_no_effect_commit(tl: Dict[str, Any]) -> bool:
    if tl.get("recovery_no_effect_commit"):
        return True
    if not (tl.get("recovery_patch_committed") and tl.get("recovery_commit_applied")):
        return False
    delta = _recovery_turn_delta(tl)
    if not delta:
        return False
    return not bool(delta.get("consistency_improved")) and not bool(delta.get("negative_recovery_commit"))


def _turn_has_harmful_commit_risk(tl: Dict[str, Any]) -> bool:
    if tl.get("recovery_harmful_commit_risk") or tl.get("negative_recovery_commit"):
        return True
    return bool(_recovery_turn_delta(tl).get("negative_recovery_commit"))


def _row_has_clean_state(row: Dict[str, Any]) -> bool:
    hygiene = _hygiene(row)
    return int(hygiene.get("state_contamination_count") or 0) == 0 and int(hygiene.get("harmful_state_contamination_count") or 0) == 0


def _row_has_safe_block(row: Dict[str, Any]) -> bool:
    for tl in row.get("turn_logs") or []:
        if not isinstance(tl, dict):
            continue
        if (
            tl.get("recovery_failure_code") in {"BLOCKED_BY_POLICY", "INSUFFICIENT_EVIDENCE", "SEMANTIC_MISMATCH", "EVIDENCE_SEMANTIC_MISMATCH"}
            and tl.get("recovery_target_gate_label") == "weak_target"
            and tl.get("recovery_patch_operation") == "reject_patch"
        ):
            return True
    return False


def _row_has_recovery_success(row: Dict[str, Any]) -> bool:
    return any(
        isinstance(tl, dict) and (tl.get("recovery_failure_code") == "SUCCESS" or tl.get("recovery_success"))
        for tl in row.get("turn_logs") or []
    )


def _row_has_hygiene_delta(row: Dict[str, Any]) -> bool:
    return any(
        isinstance(tl, dict) and (tl.get("recovery_layer_hygiene_delta_improved") or tl.get("recovery_effective_repair"))
        for tl in row.get("turn_logs") or []
    )


def _gap_status_counts(rows: Iterable[Dict[str, Any]]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for row in rows:
        state = row.get("review_state") or {}
        for gap in state.get("evidence_gaps") or []:
            if not isinstance(gap, dict):
                continue
            status = str(gap.get("status") or "open").strip().lower() or "open"
            counts[status] += 1
    return counts



def _gap_text(item: Dict[str, Any]) -> str:
    return str(
        item.get("gap")
        or item.get("text")
        or item.get("description")
        or item.get("evidence_gap")
        or ""
    )


def _gap_lifecycle_class_counts(rows: Iterable[Dict[str, Any]]) -> Counter[str]:
    """Classify open evidence gaps by whether they are real targets or review uncertainty.

    The dashboard should not treat every open gap as paper-negative burden.
    Targetless/meta gaps are assessment limitations; claim/flaw/evidence-linked
    gaps are still actionable review-state items.
    """
    counts: Counter[str] = Counter()
    meta_terms = (
        "system",
        "parser",
        "parse",
        "json",
        "fallback",
        "excerpt",
        "snippet",
        "truncated",
        "full paper",
        "full text",
        "not visible",
        "not provided",
    )
    actionable_terms = (
        "baseline",
        "ablation",
        "metric",
        "benchmark",
        "experiment",
        "evaluation",
        "dataset",
        "table",
        "figure",
        "comparison",
        "reproducib",
        "implementation",
        "hyperparameter",
    )
    for row in rows:
        state = row.get("review_state") or {}
        for gap in state.get("evidence_gaps") or []:
            if not isinstance(gap, dict):
                gap = {"gap": str(gap or ""), "status": "open"}
            status = str(gap.get("status") or "open").strip().lower() or "open"
            if status != "open":
                continue
            text = _gap_text(gap).lower()
            has_target = bool(
                gap.get("claim_id")
                or gap.get("evidence_id")
                or gap.get("flaw_id")
                or gap.get("related_claim_ids")
                or gap.get("related_evidence_ids")
                or gap.get("related_flaw_ids")
            )
            if any(term in text for term in meta_terms):
                counts["meta_or_context_open_gap"] += 1
            elif not has_target:
                counts["targetless_open_gap"] += 1
            elif any(term in text for term in actionable_terms):
                counts["actionable_targeted_open_gap"] += 1
            else:
                counts["diagnostic_targeted_open_gap"] += 1
    return counts


def _unresolved_status_counts(rows: Iterable[Dict[str, Any]], *, final_view: bool = True) -> Counter[str]:
    counts: Counter[str] = Counter()
    for row in rows:
        state = row.get("review_state") or {}
        if final_view and isinstance(state, dict):
            try:
                state_for_view = copy.deepcopy(state)
                state_for_view.pop("decision_hygiene", None)
                state = build_decision_hygiene_view(state_for_view)
            except Exception:
                pass
        for item in state.get("unresolved_questions") or []:
            if isinstance(item, dict):
                status = str(item.get("status") or "open").strip().lower() or "open"
            else:
                status = "open"
            counts[status] += 1
    return counts


def _locator_specificity_counts(rows: Iterable[Dict[str, Any]]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for row in rows:
        for item in _support_trace(row):
            if not item.get("included_in_final_view"):
                continue
            locator_type = str(
                item.get("locator_type")
                or item.get("source_locator_type")
                or "generic"
            ).strip().lower() or "generic"
            try:
                locator_confidence = float(
                    item.get("locator_confidence")
                    if item.get("locator_confidence") is not None
                    else item.get("source_locator_confidence")
                    or 0.0
                )
            except (TypeError, ValueError):
                locator_confidence = 0.0
            counts[f"type_{locator_type}"] += 1
            if locator_confidence >= 0.75:
                counts["high_confidence"] += 1
            elif locator_confidence > 0:
                counts["low_confidence"] += 1
            if item.get("source_locator_specific"):
                counts["specific"] += 1
            else:
                counts["weak"] += 1
    return counts


def _derived_negative_type_counts(rows: Iterable[Dict[str, Any]]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for row in rows:
        state = row.get("review_state") or {}
        ev_by_id = {
            str(item.get("evidence_id") or ""): item
            for item in state.get("evidence_map", []) or []
            if isinstance(item, dict) and item.get("evidence_id")
        }
        for flaw in state.get("flaw_candidates", []) or []:
            if not isinstance(flaw, dict):
                continue
            ids = list(flaw.get("verified_negative_evidence_ids") or [])
            if not ids:
                ids = list(flaw.get("negative_evidence_ids") or []) + list(flaw.get("evidence_ids") or [])
            seen: set[str] = set()
            for raw in ids:
                evidence_id = str(raw or "").strip()
                if not evidence_id or evidence_id in seen:
                    continue
                seen.add(evidence_id)
                record = ev_by_id.get(evidence_id)
                if not isinstance(record, dict):
                    continue
                explicit = str(record.get("negative_evidence_type") or "").strip()
                if explicit:
                    counts[explicit] += 1
                else:
                    counts[_classify_negative_evidence_type(str(record.get("raw_quote") or record.get("evidence") or ""))] += 1
    return counts


def _record_has_verified_negative_grounding(record: Dict[str, Any]) -> bool:
    verified_label = str(record.get("verified_grounding_label") or "")
    semantic_label = str(record.get("semantic_grounding_label") or "")
    return verified_label.startswith("paper_grounded") and semantic_label == "semantic_negative_verified"


def _derived_negative_flaw_actionability_counts(rows: Iterable[Dict[str, Any]]) -> Tuple[int, int]:
    actionable_types = {
        "direct_contradiction",
        "negative_result",
        "missing_ablation",
        "missing_baseline",
        "insufficient_evaluation",
    }
    actionable_flaws = 0
    limitation_flaws = 0
    for row in rows:
        state = row.get("review_state") or {}
        ev_by_id = {
            str(item.get("evidence_id") or ""): item
            for item in state.get("evidence_map", []) or []
            if isinstance(item, dict) and item.get("evidence_id")
        }
        for flaw in state.get("flaw_candidates", []) or []:
            if not isinstance(flaw, dict):
                continue
            ids = list(flaw.get("verified_negative_evidence_ids") or [])
            if not ids:
                ids = list(flaw.get("negative_evidence_ids") or []) + list(flaw.get("evidence_ids") or [])
            types: set[str] = set()
            seen: set[str] = set()
            for raw in ids:
                evidence_id = str(raw or "").strip()
                if not evidence_id or evidence_id in seen:
                    continue
                seen.add(evidence_id)
                record = ev_by_id.get(evidence_id)
                if not isinstance(record, dict):
                    continue
                if not _record_has_verified_negative_grounding(record):
                    continue
                explicit = str(record.get("negative_evidence_type") or "").strip()
                if explicit:
                    types.add(explicit)
                else:
                    types.add(_classify_negative_evidence_type(str(record.get("raw_quote") or record.get("evidence") or "")))
            if not types:
                continue
            if types & actionable_types:
                actionable_flaws += 1
            else:
                limitation_flaws += 1
    return actionable_flaws, limitation_flaws


def _report_has_leak(text: str) -> bool:
    if not text:
        return False
    lowered = text.lower()
    return any(term.lower() in lowered for term in LEAK_TERMS)


def _aggregate(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    n_papers = len(rows)
    out: Dict[str, Any] = {"paper_count": n_papers}

    # --- positive support ----------------------------------------------
    out["real_strong_support_total"] = _sum(rows, "real_strong_support_total")
    out["independent_support_group_total"] = _sum(rows, "independent_support_group_total")
    out["empirical_real_strong_support_count"] = _sum(rows, "empirical_real_strong_support_count")
    out["method_real_strong_support_count"] = _sum(rows, "method_real_strong_support_count")
    out["table_or_figure_real_strong_support_count"] = _sum(rows, "table_or_figure_real_strong_support_count")
    out["result_or_experiment_real_strong_support_count"] = _sum(rows, "result_or_experiment_real_strong_support_count")
    out["abstract_real_strong_support_count"] = _sum(rows, "abstract_real_strong_support_count")
    out["ablation_real_strong_support_count"] = _sum(rows, "ablation_real_strong_support_count")
    out["verified_moderate_support_total"] = _sum(rows, "final_verified_moderate_support_total")
    out["diagnostic_independent_support_group_total"] = _sum(rows, "diagnostic_independent_support_group_total")
    out["claims_with_2plus_independent_or_diagnostic_support"] = _sum(rows, "claims_with_2plus_independent_or_diagnostic_support")
    out["diagnostic_support_signal_total"] = out["real_strong_support_total"] + out["verified_moderate_support_total"]
    out["contextual_support_total"] = _sum(rows, "contextual_support_total")
    out["claims_with_real_strong_support"] = _sum(rows, "claims_with_real_strong_support")
    out["claims_with_2plus_real_strong_support"] = _sum(rows, "claims_with_2plus_real_strong_support")
    out["claims_with_2plus_independent_support"] = _sum(rows, "claims_with_2plus_independent_support")
    out["claims_with_empirical_real_strong_support"] = _sum(rows, "claims_with_empirical_real_strong_support")
    out["claims_with_deep_support"] = _sum(rows, "claims_with_deep_support")
    out["claims_with_verified_moderate_support"] = _sum(rows, "claims_with_verified_moderate_support")
    out["papers_with_real_strong_support"] = sum(1 for r in rows if _paper_has_hygiene_positive(r, "real_strong_support_total"))
    out["papers_with_empirical_support"] = sum(1 for r in rows if _paper_has_hygiene_positive(r, "empirical_real_strong_support_count"))
    out["papers_with_deep_support"] = sum(1 for r in rows if _paper_has_hygiene_positive(r, "claims_with_deep_support"))
    out["positive_coverage_gap_papers"] = max(0, n_papers - out["papers_with_real_strong_support"])
    out["empirical_coverage_gap_papers"] = max(0, n_papers - out["papers_with_empirical_support"])
    out["deep_support_gap_papers"] = max(0, n_papers - out["papers_with_deep_support"])
    out["moderate_diagnostic_support_total"] = _sum(rows, "moderate_diagnostic_support_total")
    out["moderate_absorbed_into_final_strong_count"] = 0  # filled after support trace is built
    out["moderate_remaining_diagnostic_count"] = out["verified_moderate_support_total"]
    out["primary_claim_total"] = _sum(rows, "primary_claim_total")
    out["primary_claims_with_real_strong_support"] = _sum(rows, "primary_claims_with_real_strong_support")
    out["primary_claims_with_empirical_support"] = _sum(rows, "primary_claims_with_empirical_support")
    out["primary_claims_with_deep_support"] = _sum(rows, "primary_claims_with_deep_support")
    out["zero_real_papers"] = sum(1 for r in rows if (_hygiene(r).get("real_strong_support_total", 0) or 0) == 0)
    all_trace_items = [item for row in rows for item in _support_trace(row)]
    final_trace_items = [item for item in all_trace_items if item.get("included_in_final_view")]
    out["final_support_total"] = len(final_trace_items)
    out["final_support_direct_strong_count"] = sum(
        1
        for item in final_trace_items
        if str(item.get("initial_strength") or "") == "strong"
        and not item.get("strength_promotion_from_medium_used")
        and not item.get("semantic_weak_promotion_used")
    )
    out["final_support_promoted_from_medium_count"] = sum(
        1 for item in final_trace_items if item.get("strength_promotion_from_medium_used")
    )
    out["moderate_absorbed_into_final_strong_count"] = out["final_support_promoted_from_medium_count"]
    out["final_support_semantic_weak_promotion_count"] = sum(
        1 for item in final_trace_items if item.get("semantic_weak_promotion_used")
    )
    out["near_miss_deep_moderate_support_count"] = sum(
        1 for item in all_trace_items
        if item.get("verified_moderate_near_miss_promotion_path") == "near_miss_verified_deep_support"
    )
    out["near_miss_method_moderate_support_count"] = sum(
        1 for item in all_trace_items
        if item.get("verified_moderate_near_miss_promotion_path") == "near_miss_verified_method_support"
    )
    out["near_miss_specific_locator_moderate_count"] = sum(
        1 for item in all_trace_items
        if item.get("verified_moderate_near_miss_promotion_path") and item.get("source_locator_specific")
    )
    out["near_miss_promoted_to_final_count"] = sum(
        1 for item in final_trace_items if item.get("verified_moderate_near_miss_promotion_path")
    )
    out["support_trace_total"] = len(all_trace_items)
    out["support_trace_included_count"] = len(final_trace_items)
    out["support_trace_dropped_count"] = max(0, len(all_trace_items) - len(final_trace_items))
    drop_counts = Counter(str(item.get("final_drop_reason") or "included") for item in all_trace_items)
    for reason in (
        "hygiene_filtered",
        "overridden_by_negative_burden",
        "weak_support_depth",
        "semantic_mismatch",
        "duplicate_quote",
        "missing_verified_quote",
        "included",
    ):
        out[f"support_trace_{reason}_count"] = int(drop_counts.get(reason, 0))
    out["final_support_specific_locator_count"] = sum(
        1 for item in final_trace_items if item.get("source_locator_specific")
    )
    out["final_support_weak_locator_count"] = max(
        0,
        len(final_trace_items) - out["final_support_specific_locator_count"],
    )

    # --- negative & flaws ----------------------------------------------
    out["negative_evidence_candidate_count"] = _sum(rows, "negative_evidence_candidate_count")
    out["negative_evidence_linked_to_flaw_count"] = _sum(rows, "negative_evidence_linked_to_flaw_count")
    out["negative_evidence_unlinked_to_flaw"] = _sum(rows, "negative_evidence_unlinked_to_flaw_count")
    derived_actionable_flaws, derived_limitation_flaws = _derived_negative_flaw_actionability_counts(rows)
    verified_negative_sum = _sum(rows, "verified_negative_flaw_count")
    verified_actionable_sum = _sum(rows, "verified_actionable_negative_flaw_count")
    verified_limitation_sum = _sum(rows, "verified_limitation_negative_flaw_count")
    out["verified_negative_flaw_count"] = verified_negative_sum
    out["verified_actionable_negative_flaw_count"] = (
        verified_actionable_sum if verified_negative_sum else derived_actionable_flaws
    )
    out["verified_limitation_negative_flaw_count"] = (
        verified_limitation_sum if verified_negative_sum else derived_limitation_flaws
    )
    type_counts = Counter()
    for row in rows:
        type_counts.update((_hygiene(row).get("negative_evidence_type_counts") or {}))
    if not type_counts:
        type_counts = _derived_negative_type_counts(rows)
    for neg_type in (
        "direct_contradiction",
        "negative_result",
        "missing_ablation",
        "missing_baseline",
        "insufficient_evaluation",
        "reproducibility_gap",
        "scope_limitation",
        "neutral_control_context",
        "generic_gap",
    ):
        out[f"negative_type_{neg_type}"] = int(type_counts.get(neg_type, 0))
    out["verified_potential_concern_count"] = _sum(rows, "verified_potential_concern_count")
    out["grounded_weakness_count"] = _sum(rows, "grounded_weakness_count")
    out["assessment_limitation_flaw_count"] = _sum(rows, "assessment_limitation_flaw_count")
    out["negative_grounding_conflict_count"] = _sum(rows, "negative_grounding_conflict_count")
    out["invalid_negative_evidence_id_count_legacy"] = _sum(rows, "invalid_negative_evidence_id_count_legacy")
    out["negative_semantic_anchor_conflict_count"] = _sum(rows, "negative_semantic_anchor_conflict_count")
    out["generic_gap_semantic_rejected_count"] = _sum(rows, "generic_gap_semantic_rejected_count")
    out["negative_evidence_semantic_rejected_count"] = _sum(rows, "negative_evidence_semantic_rejected_count")
    out["downgraded_flaw_count"] = _sum(rows, "downgraded_flaw_count")
    out["potential_concern_count"] = _sum(rows, "potential_concern_count")

    # --- state contamination / target localization ---------------------
    contamination_type_counts: Counter = Counter()
    target_gate_counts: Counter = Counter()
    for row in rows:
        hygiene = _hygiene(row)
        contamination_type_counts.update(hygiene.get("state_contamination_type_counts") or {})
        target_gate_counts.update(hygiene.get("recovery_target_gate_counts") or {})
    out["state_contamination_count"] = _sum(rows, "state_contamination_count")
    out["state_contamination_count_legacy"] = _sum(rows, "state_contamination_count_legacy")
    out["harmful_state_contamination_count"] = _sum(rows, "harmful_state_contamination_count")
    out["repairable_state_warning_count"] = _sum(rows, "repairable_state_warning_count")
    out["conservative_state_warning_count"] = _sum(rows, "conservative_state_warning_count")
    out["state_hygiene_warning_count"] = _sum(rows, "state_hygiene_warning_count")
    out["weak_target_warning_count"] = _sum(rows, "weak_target_warning_count")
    out["repairable_contamination_target_count"] = _sum(rows, "repairable_contamination_target_count")
    out["conservative_contamination_target_count"] = _sum(rows, "conservative_contamination_target_count")
    out["blocked_fallback_contamination_target_count"] = _sum(rows, "blocked_fallback_contamination_target_count")
    out["blocked_empty_contamination_target_count"] = _sum(rows, "blocked_empty_contamination_target_count")
    for error_type in (
        "unsupported_with_strong_support",
        "zero_real_support",
        "stale_gap_persistence",
        "unsupported_flaw_escalation",
        "negative_evidence_overclaim",
        "evidence_misbinding",
        "meta_leakage",
        "stale_flaw_persistence",
        "harmful_recovery_risk",
    ):
        out[f"contamination_{error_type}"] = int(contamination_type_counts.get(error_type, 0))
    for gate_label in ("real_target", "weak_target", "fallback_target", "empty_target"):
        out[f"target_gate_{gate_label}"] = int(target_gate_counts.get(gate_label, 0))

    # --- contested -----------------------------------------------------
    out["contested_support_total"] = _sum(rows, "contested_support_total")
    out["contested_final_support_total"] = _sum(rows, "contested_final_support_total")
    out["claims_with_contested_support"] = _sum(rows, "claims_with_contested_support")
    out["claims_with_contested_final_support"] = _sum(rows, "claims_with_contested_final_support")
    out["open_conflict_count"] = _sum(rows, "open_conflict_count")

    # --- gaps / unresolved / locator ----------------------------------
    gap_counts = _gap_status_counts(rows)
    gap_lifecycle_counts = _gap_lifecycle_class_counts(rows)
    unresolved_counts = _unresolved_status_counts(rows, final_view=True)
    unresolved_raw_counts = _unresolved_status_counts(rows, final_view=False)
    locator_counts = _locator_specificity_counts(rows)
    out["evidence_gap_open_count"] = int(gap_counts.get("open", 0))
    out["evidence_gap_resolved_count"] = int(gap_counts.get("resolved", 0))
    out["evidence_gap_superseded_count"] = int(gap_counts.get("superseded", 0))
    out["evidence_gap_not_assessable_count"] = int(gap_counts.get("not_assessable", 0))
    out["state_hygiene_open_gap_count"] = _sum(rows, "open_evidence_gap_count")
    out["state_hygiene_stale_gap_count"] = _sum(rows, "stale_evidence_gap_count")
    out["targetless_open_gap_count"] = int(gap_lifecycle_counts.get("targetless_open_gap", 0))
    out["meta_or_context_open_gap_count"] = int(gap_lifecycle_counts.get("meta_or_context_open_gap", 0))
    out["actionable_targeted_open_gap_count"] = int(gap_lifecycle_counts.get("actionable_targeted_open_gap", 0))
    out["diagnostic_targeted_open_gap_count"] = int(gap_lifecycle_counts.get("diagnostic_targeted_open_gap", 0))
    out["targeted_open_gap_count"] = (
        out["actionable_targeted_open_gap_count"] + out["diagnostic_targeted_open_gap_count"]
    )
    out["assessment_limitation_open_gap_count"] = (
        out["targetless_open_gap_count"] + out["meta_or_context_open_gap_count"]
    )
    out["unresolved_open_count"] = int(unresolved_counts.get("open", 0))
    out["unresolved_open_raw_count"] = int(unresolved_raw_counts.get("open", 0))
    out["unresolved_resolved_count"] = int(unresolved_counts.get("resolved", 0))
    out["unresolved_deferred_count"] = _sum(rows, "deferred_unresolved_count")
    out["targetless_unresolved_deferred_count"] = _sum(rows, "targetless_unresolved_deferred_count")
    out["programmatic_specific_locator_count"] = int(locator_counts.get("specific", 0))
    out["programmatic_weak_locator_count"] = int(locator_counts.get("weak", 0))
    for locator_type in ("table", "figure", "section", "algorithm", "theorem", "generic"):
        out[f"programmatic_locator_type_{locator_type}_count"] = int(locator_counts.get(f"type_{locator_type}", 0))
    out["programmatic_high_confidence_locator_count"] = int(locator_counts.get("high_confidence", 0))
    out["programmatic_low_confidence_locator_count"] = int(locator_counts.get("low_confidence", 0))

    # --- evidence formation health (from turn_logs) -----------------------
    evidence_agent_worker_turns = 0
    quote_bank_nonzero_turns = 0
    payload_evidence_item_total = 0
    evidence_agent_nonempty_payload_turns = 0
    evidence_agent_question_only_turns = 0
    first_support_fallback_turns = 0
    model_adapter_quote_first_rewrite_count = 0
    model_adapter_strength_downgrade_count = 0
    small_model_quote_bank_augmentation_count = 0
    for r in rows:
        for tl in r.get("turn_logs") or []:
            if not isinstance(tl, dict):
                continue
            selected = tl.get("selected_agents") or []
            worker_payloads = tl.get("worker_payloads") or []
            evidence_payloads = [
                item.get("payload") or {}
                for item in worker_payloads
                if isinstance(item, dict) and item.get("agent_id") == "Evidence Agent"
            ]
            if "Evidence Agent" not in selected and not evidence_payloads:
                continue
            evidence_agent_worker_turns += 1
            if int(tl.get("evidence_quote_bank_count") or 0) > 0:
                quote_bank_nonzero_turns += 1
            turn_evidence_count = int(tl.get("evidence_payload_evidence_count") or 0)
            if not turn_evidence_count:
                for payload in evidence_payloads:
                    ev = payload.get("evidence_map") or []
                    if isinstance(ev, list):
                        turn_evidence_count += len([item for item in ev if isinstance(item, dict)])
            payload_evidence_item_total += turn_evidence_count
            turn_unresolved_count = 0
            for payload in evidence_payloads:
                for ev in payload.get("evidence_map") or []:
                    if not isinstance(ev, dict):
                        continue
                    if (
                        str(ev.get("evidence_id") or "").startswith("evidence-first-support-")
                        or "Fallback first-support item" in str(ev.get("binding_rationale") or "")
                    ):
                        first_support_fallback_turns += 1
                        break
                unresolved = payload.get("unresolved_questions") or []
                if isinstance(unresolved, list):
                    turn_unresolved_count += len(unresolved)
            if tl.get("first_support_fallback_from_quote_bank"):
                first_support_fallback_turns += 1
            payload_adapter_rewrites = 0
            payload_adapter_downgrades = 0
            payload_quote_bank_augmentations = 0
            for payload in evidence_payloads:
                payload_adapter_rewrites += int(payload.get("model_adapter_quote_first_rewrite_count") or 0)
                payload_adapter_downgrades += int(payload.get("model_adapter_strength_downgrade_count") or 0)
                payload_quote_bank_augmentations += int(payload.get("small_model_quote_bank_augmentation_count") or 0)
                for ev in payload.get("evidence_map") or []:
                    if not isinstance(ev, dict):
                        continue
                    evidence_id = str(ev.get("evidence_id") or "")
                    if ev.get("small_model_quote_bank_augmentation") or evidence_id.startswith("evidence-small-model-quote-bank-"):
                        payload_quote_bank_augmentations += 1
            model_adapter_quote_first_rewrite_count += payload_adapter_rewrites or int(tl.get("model_adapter_quote_first_rewrite_count") or 0)
            model_adapter_strength_downgrade_count += payload_adapter_downgrades or int(tl.get("model_adapter_strength_downgrade_count") or 0)
            small_model_quote_bank_augmentation_count += payload_quote_bank_augmentations or int(tl.get("small_model_quote_bank_augmentation_count") or 0)
            if turn_evidence_count > 0 or turn_unresolved_count > 0:
                evidence_agent_nonempty_payload_turns += 1
            if turn_evidence_count == 0 and turn_unresolved_count > 0:
                evidence_agent_question_only_turns += 1
    out["evidence_agent_worker_turns"] = evidence_agent_worker_turns
    out["quote_bank_nonzero_turns"] = quote_bank_nonzero_turns
    out["payload_evidence_item_total"] = payload_evidence_item_total
    out["evidence_agent_nonempty_payload_turns"] = evidence_agent_nonempty_payload_turns
    out["evidence_agent_question_only_turns"] = evidence_agent_question_only_turns
    out["first_support_fallback_turns"] = first_support_fallback_turns
    out["model_adapter_quote_first_rewrite_count"] = model_adapter_quote_first_rewrite_count
    out["model_adapter_strength_downgrade_count"] = model_adapter_strength_downgrade_count
    out["small_model_quote_bank_augmentation_count"] = small_model_quote_bank_augmentation_count
    out["evidence_formation_dead_loop_count"] = 1 if quote_bank_nonzero_turns > 0 and payload_evidence_item_total == 0 else 0

    # --- recovery (from turn_logs) -------------------------------------
    rec = Counter()
    failure_codes: Counter = Counter()
    synthetic_in_supporting = 0
    for r in rows:
        for tl in r.get("turn_logs") or []:
            if not isinstance(tl, dict):
                continue
            if tl.get("recovery_attempted"):
                rec["recovery_attempted"] += 1
            if tl.get("recovery_patch_validated"):
                rec["recovery_patch_validated"] += 1
            if tl.get("recovery_patch_committed"):
                rec["recovery_patch_committed"] += 1
            if tl.get("recovery_layer_hygiene_delta_improved"):
                rec["hygiene_delta_improved"] += 1
            if tl.get("recovery_effective_repair"):
                rec["recovery_effective_repair"] += 1
            if _turn_has_no_effect_commit(tl):
                rec["recovery_no_effect_commit"] += 1
            if _turn_has_harmful_commit_risk(tl):
                rec["recovery_harmful_commit_risk"] += 1
            if tl.get("recovery_committed"):
                rec["recovery_committed"] += 1
            gate_label = str(tl.get("recovery_target_gate_label") or "")
            if gate_label:
                rec[f"recovery_target_gate_{gate_label}_turns"] += 1
            operation = str(tl.get("recovery_patch_operation") or "")
            if operation:
                rec[f"recovery_patch_operation_{operation}_turns"] += 1
            code = str(tl.get("recovery_failure_code") or "")
            if code:
                failure_codes[code] += 1
                if code == "SUCCESS":
                    rec["recovery_success"] += 1
                elif (
                    code in {"BLOCKED_BY_POLICY", "INSUFFICIENT_EVIDENCE", "SEMANTIC_MISMATCH", "EVIDENCE_SEMANTIC_MISMATCH"}
                    and gate_label == "weak_target"
                    and operation == "reject_patch"
                ):
                    rec["recovery_safe_blocked_weak_target"] += 1
            # synthetic marker pollution check on patch supporting_evidence_ids
            sup_ids = tl.get("supporting_evidence_ids") or []
            for sid in sup_ids:
                s = str(sid)
                if any(s.startswith(p) for p in SYNTHETIC_EVIDENCE_PREFIXES):
                    synthetic_in_supporting += 1
    out["recovery_attempted"] = rec["recovery_attempted"]
    out["recovery_patch_validated"] = rec["recovery_patch_validated"]
    out["recovery_patch_committed"] = rec["recovery_patch_committed"]
    out["recovery_committed"] = rec["recovery_committed"]
    out["recovery_success"] = rec["recovery_success"]
    out["hygiene_delta_improved"] = rec["hygiene_delta_improved"]
    out["recovery_effective_repair"] = rec["recovery_effective_repair"]
    out["recovery_no_effect_commit"] = rec["recovery_no_effect_commit"]
    out["recovery_harmful_commit_risk"] = rec["recovery_harmful_commit_risk"]
    out["recovery_safe_blocked_weak_target"] = rec["recovery_safe_blocked_weak_target"]
    out["recovery_safe_resolution"] = rec["recovery_success"] + rec["recovery_safe_blocked_weak_target"]
    out["hygiene_delta_or_safe_block"] = rec["hygiene_delta_improved"] + rec["recovery_safe_blocked_weak_target"]
    # Protection thresholds are paper-scaled, so clean/safe/hygiene credit must
    # be case-level rather than turn-level.  The old aggregate only granted
    # clean-state credit when the entire run had zero contamination, which made
    # one contaminated paper erase clean-state credit for all other papers.
    out["recovery_safe_resolution_or_clean_state"] = sum(
        1 for row in rows
        if _row_has_clean_state(row) or _row_has_recovery_success(row) or _row_has_safe_block(row)
    )
    out["hygiene_delta_or_safe_block_or_clean_state"] = sum(
        1 for row in rows
        if _row_has_clean_state(row) or _row_has_hygiene_delta(row) or _row_has_safe_block(row)
    )
    for gate_label in ("real_target", "weak_target", "fallback_target", "empty_target"):
        out[f"recovery_target_gate_{gate_label}_turns"] = rec[f"recovery_target_gate_{gate_label}_turns"]
    for operation in (
        "reject_patch",
        "downgrade_final_to_candidate",
        "route_to_assessment_limitation",
        "rebind_evidence",
        "split_overbroad_claim",
        "convert_negative_to_gap",
        "mark_contested",
        "resolve_stale_gap",
    ):
        out[f"recovery_patch_operation_{operation}_turns"] = rec[f"recovery_patch_operation_{operation}_turns"]
    out["failure_codes"] = dict(failure_codes)
    out["synthetic_marker_in_supporting_count"] = synthetic_in_supporting

    # --- hygiene -------------------------------------------------------
    out["final_nonreal_strong_support"] = _sum(rows, "final_nonreal_strong_support_count")
    # final-strong-guard tracks low-score promotion downgrades; if any
    # low-score promotion ended up still strong, the guard would log it
    # under final_strong_guard_low_score_downgrade_count (which means the
    # guard *prevented* it). low_score_promoted_strong = remaining strong
    # entries whose semantic_alignment_score < 0.6 and which were promoted
    # via medium / weak paths. We approximate with an evidence_map scan.
    out["low_score_promoted_strong"] = _count_low_score_promoted_strong(rows)
    out["final_report_leakage_paper_count"] = sum(1 for r in rows if _report_has_leak(str(r.get("final_report") or "")))
    out["user_report_leakage_paper_count"] = sum(1 for r in rows if _report_has_leak(str((r.get("review_state") or {}).get("user_report") or "")))
    # final_decision
    decisions = Counter()
    for r in rows:
        d = str((r.get("review_state") or {}).get("final_decision") or r.get("final_decision") or "?")
        decisions[d] += 1
    out["final_decision_distribution"] = dict(decisions)
    return out


def _count_low_score_promoted_strong(rows: List[Dict[str, Any]]) -> int:
    """Return the number of evidence items that ended up final_strength=strong
    via a medium/weak promotion path with semantic_alignment_score<0.6.

    This is the "did a promoted-to-strong item slip past the low-score guard"
    counter that must stay at 0.
    """
    count = 0
    for r in rows:
        rs = r.get("review_state") or {}
        for ev in rs.get("evidence_map") or []:
            if not isinstance(ev, dict):
                continue
            if ev.get("final_strength") != "strong":
                continue
            score = ev.get("semantic_alignment_score")
            if not isinstance(score, (int, float)) or score >= 0.6:
                continue
            promoted = bool(ev.get("strength_promotion_from_medium_used")) or bool(ev.get("semantic_weak_promotion_used"))
            if promoted:
                count += 1
    return count


def _case_audit(rows: List[Dict[str, Any]], metrics: Dict[str, Any], issues: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Return per-paper attribution for recovery and hygiene protection lines."""
    cases: List[Dict[str, Any]] = []
    lists: Dict[str, List[str]] = {
        "hygiene_fail_case_list": [],
        "evidence_misbinding_case_list": [],
        "no_effect_patch_case_list": [],
        "harmful_commit_risk_case_list": [],
        "not_assessable_gap_case_list": [],
        "negative_semantic_rejected_case_list": [],
        "recovery_committed_but_ineffective_case_list": [],
        "validator_blocked_without_final_safe_state_case_list": [],
    }
    reason_counts: Counter[str] = Counter()

    for row in rows:
        pid = _paper_id(row)
        hygiene = _hygiene(row)
        turns = [tl for tl in (row.get("turn_logs") or []) if isinstance(tl, dict)]
        contamination_counts = hygiene.get("state_contamination_type_counts") or {}
        if not isinstance(contamination_counts, dict):
            contamination_counts = {}

        state_contamination_count = int(hygiene.get("state_contamination_count") or 0)
        harmful_state_contamination_count = int(hygiene.get("harmful_state_contamination_count") or 0)
        clean_state = state_contamination_count == 0 and harmful_state_contamination_count == 0

        safe_block_turns = [
            tl for tl in turns
            if tl.get("recovery_failure_code") in {"BLOCKED_BY_POLICY", "INSUFFICIENT_EVIDENCE", "SEMANTIC_MISMATCH", "EVIDENCE_SEMANTIC_MISMATCH"}
            and tl.get("recovery_target_gate_label") == "weak_target"
            and tl.get("recovery_patch_operation") == "reject_patch"
        ]
        improved_turns = [
            tl for tl in turns
            if tl.get("recovery_layer_hygiene_delta_improved") or tl.get("recovery_effective_repair")
        ]
        committed_turns = [tl for tl in turns if tl.get("recovery_patch_committed")]
        no_effect_turns = [tl for tl in turns if _turn_has_no_effect_commit(tl)]
        harmful_turns = [tl for tl in turns if _turn_has_harmful_commit_risk(tl)]
        blocked_turns = [tl for tl in turns if tl.get("recovery_attempted") and not tl.get("recovery_patch_committed")]

        gap_status_counts = Counter(
            str(g.get("status") or "open")
            for g in ((row.get("review_state") or {}).get("evidence_gaps") or [])
            if isinstance(g, dict)
        )
        unresolved_reason_counts = Counter(
            str(q.get("defer_reason") or q.get("reason") or q.get("status_reason") or "missing_reason")
            for q in ((row.get("review_state") or {}).get("unresolved_questions") or [])
            if isinstance(q, dict) and str(q.get("status") or "open") in {"deferred", "open"}
        )

        counted_for_hygiene_line = bool(clean_state or improved_turns or safe_block_turns)
        reasons: List[str] = []
        if clean_state:
            reasons.append("clean_state_recognized")
        if improved_turns:
            reasons.append("hygiene_delta_improved")
        if safe_block_turns:
            reasons.append("safe_block_counted")
        if not counted_for_hygiene_line:
            if not contamination_counts and state_contamination_count == 0:
                reasons.append("no_contamination_detected_but_clean_state_not_recognized")
            if committed_turns and not improved_turns:
                reasons.append("patch_committed_but_no_hygiene_delta")
            if no_effect_turns:
                reasons.append("no_effect_patch")
            if gap_status_counts.get("not_assessable", 0):
                reasons.append("gap_routed_to_not_assessable_but_not_counted")
            if int(contamination_counts.get("evidence_misbinding", 0) or 0):
                reasons.append("evidence_misbinding_present")
            if blocked_turns and not clean_state and not safe_block_turns:
                reasons.append("validator_blocked_without_final_safe_state")
            if not reasons:
                reasons.append("unattributed_hygiene_line_miss")
        if harmful_turns:
            reasons.append("harmful_commit_risk")
        if int(hygiene.get("negative_evidence_semantic_rejected_count") or 0) or int(hygiene.get("generic_gap_semantic_rejected_count") or 0):
            reasons.append("negative_semantic_rejected")

        for reason in reasons:
            reason_counts[reason] += 1

        if not counted_for_hygiene_line:
            lists["hygiene_fail_case_list"].append(pid)
        if int(contamination_counts.get("evidence_misbinding", 0) or 0):
            lists["evidence_misbinding_case_list"].append(pid)
        if no_effect_turns:
            lists["no_effect_patch_case_list"].append(pid)
        if harmful_turns:
            lists["harmful_commit_risk_case_list"].append(pid)
        if gap_status_counts.get("not_assessable", 0):
            lists["not_assessable_gap_case_list"].append(pid)
        if "negative_semantic_rejected" in reasons:
            lists["negative_semantic_rejected_case_list"].append(pid)
        if committed_turns and not improved_turns:
            lists["recovery_committed_but_ineffective_case_list"].append(pid)
        if "validator_blocked_without_final_safe_state" in reasons:
            lists["validator_blocked_without_final_safe_state_case_list"].append(pid)

        cases.append({
            "paper_id": pid,
            "final_decision": str((row.get("review_state") or {}).get("final_decision") or row.get("final_decision") or ""),
            "reward": row.get("reward"),
            "counted_for_hygiene_delta_or_safe_block_or_clean_state": counted_for_hygiene_line,
            "hygiene_case_reasons": reasons,
            "state_contamination_count": state_contamination_count,
            "harmful_state_contamination_count": harmful_state_contamination_count,
            "contamination_type_counts": contamination_counts,
            "gap_status_counts": dict(gap_status_counts),
            "unresolved_reason_counts": dict(unresolved_reason_counts),
            "recovery_attempted_turns": sum(1 for tl in turns if tl.get("recovery_attempted")),
            "recovery_committed_turns": len(committed_turns),
            "recovery_effective_repair_turns": len(improved_turns),
            "safe_block_turns": len(safe_block_turns),
            "no_effect_commit_turns": len(no_effect_turns),
            "harmful_commit_risk_turns": len(harmful_turns),
            "recovery_turns": [
                {
                    "turn_id": tl.get("turn_id"),
                    "operation": tl.get("recovery_patch_operation", ""),
                    "target_type": tl.get("recovery_target_type", ""),
                    "target_id": tl.get("recovery_target_id", ""),
                    "gate": tl.get("recovery_target_gate_label", ""),
                    "failure_code": tl.get("recovery_failure_code", ""),
                    "committed": bool(tl.get("recovery_patch_committed")),
                    "effective_repair": bool(tl.get("recovery_effective_repair")),
                    "no_effect_commit": bool(_turn_has_no_effect_commit(tl)),
                    "harmful_commit_risk": bool(_turn_has_harmful_commit_risk(tl)),
                    "state_delta": _recovery_turn_delta(tl),
                }
                for tl in turns
                if tl.get("recovery_attempted") or tl.get("recovery_patch_committed")
            ],
        })

    return {
        "summary": {
            "paper_count": len(rows),
            "metrics_subset": {
                key: metrics.get(key)
                for key in (
                    "hygiene_delta_or_safe_block_or_clean_state",
                    "recovery_safe_resolution_or_clean_state",
                    "recovery_patch_committed",
                    "recovery_effective_repair",
                    "hygiene_delta_improved",
                    "contamination_evidence_misbinding",
                    "evidence_gap_resolved_count",
                    "evidence_gap_superseded_count",
                    "evidence_gap_not_assessable_count",
                    "recovery_no_effect_commit",
                    "recovery_harmful_commit_risk",
                )
            },
            "protection_failures": [it for it in issues if not it.get("passed")],
            "hygiene_case_reason_counts": dict(sorted(reason_counts.items())),
        },
        "lists": lists,
        "cases": cases,
    }


# ---------- protection-line eval ----------------------------------------

def _resolve_dashboard_mode(metrics: Dict[str, Any], requested: str) -> str:
    requested = str(requested or "auto").strip().lower()
    if requested in {"smoke", "full39"}:
        return requested
    paper_count = int(metrics.get("paper_count") or 0)
    return "full39" if paper_count >= FULL39_REFERENCE_PAPERS else "smoke"


def _scaled_threshold(base_threshold: int, paper_count: int, mode: str) -> Tuple[int, str]:
    if mode != "smoke" or base_threshold <= 0:
        return base_threshold, ""
    scaled = max(1, math.ceil(base_threshold * max(paper_count, 1) / FULL39_REFERENCE_PAPERS))
    return scaled, f"smoke scaled from {base_threshold}/39"


def _check_protection(metrics: Dict[str, Any], mode: str) -> Tuple[List[Dict[str, Any]], bool]:
    issues: List[Dict[str, Any]] = []
    ok = True
    paper_count = int(metrics.get("paper_count") or 0)
    for key, op, thr_raw in PROTECTION_LINES:
        v = metrics.get(key, 0)
        try:
            base_thr = int(thr_raw)
            thr, note = _scaled_threshold(base_thr, paper_count, mode) if op == ">=" else (base_thr, "")
            vi = int(v)
        except (TypeError, ValueError):
            issues.append({"key": key, "value": v, "op": op, "threshold": thr_raw, "threshold_note": "", "passed": False})
            ok = False
            continue
        passed = ((op == "==" and vi == thr) or (op == ">=" and vi >= thr) or
                  (op == "<=" and vi <= thr))
        if not passed:
            ok = False
        issues.append({"key": key, "value": vi, "op": op, "threshold": thr, "threshold_note": note, "passed": passed})
    return issues, ok


# ---------- markdown rendering ------------------------------------------

GROUP_DEFS: List[Tuple[str, List[str]]] = [
    ("Evidence formation health", [
        "evidence_agent_worker_turns",
        "quote_bank_nonzero_turns",
        "payload_evidence_item_total",
        "evidence_agent_nonempty_payload_turns",
        "evidence_agent_question_only_turns",
        "first_support_fallback_turns",
        "model_adapter_quote_first_rewrite_count",
        "model_adapter_strength_downgrade_count",
        "small_model_quote_bank_augmentation_count",
        "evidence_formation_dead_loop_count",
    ]),
    ("Positive support", [
        "real_strong_support_total",
        "independent_support_group_total",
        "diagnostic_independent_support_group_total",
        "claims_with_2plus_independent_or_diagnostic_support",
        "empirical_real_strong_support_count",
        "method_real_strong_support_count",
        "table_or_figure_real_strong_support_count",
        "result_or_experiment_real_strong_support_count",
        "ablation_real_strong_support_count",
        "abstract_real_strong_support_count",
        "verified_moderate_support_total",
        "moderate_diagnostic_support_total",
        "moderate_absorbed_into_final_strong_count",
        "moderate_remaining_diagnostic_count",
        "diagnostic_support_signal_total",
        "papers_with_real_strong_support",
        "papers_with_empirical_support",
        "papers_with_deep_support",
        "positive_coverage_gap_papers",
        "empirical_coverage_gap_papers",
        "deep_support_gap_papers",
        "claims_with_real_strong_support",
        "claims_with_empirical_real_strong_support",
        "claims_with_deep_support",
        "claims_with_2plus_independent_support",
        "primary_claim_total",
        "primary_claims_with_real_strong_support",
        "primary_claims_with_empirical_support",
        "primary_claims_with_deep_support",
        "zero_real_papers",
        "final_support_total",
        "final_support_direct_strong_count",
        "final_support_promoted_from_medium_count",
        "final_support_semantic_weak_promotion_count",
        "near_miss_deep_moderate_support_count",
        "near_miss_method_moderate_support_count",
        "near_miss_specific_locator_moderate_count",
        "near_miss_promoted_to_final_count",
        "support_trace_total",
        "support_trace_included_count",
        "support_trace_dropped_count",
        "support_trace_hygiene_filtered_count",
        "support_trace_overridden_by_negative_burden_count",
        "support_trace_weak_support_depth_count",
        "support_trace_semantic_mismatch_count",
        "support_trace_duplicate_quote_count",
        "support_trace_missing_verified_quote_count",
        "final_support_specific_locator_count",
        "final_support_weak_locator_count",
    ]),
    ("Negative & flaws", [
        "negative_evidence_candidate_count",
        "negative_evidence_linked_to_flaw_count",
        "negative_evidence_unlinked_to_flaw",
        "verified_negative_flaw_count",
        "verified_actionable_negative_flaw_count",
        "verified_limitation_negative_flaw_count",
        "negative_type_direct_contradiction",
        "negative_type_negative_result",
        "negative_type_missing_ablation",
        "negative_type_missing_baseline",
        "negative_type_insufficient_evaluation",
        "negative_type_reproducibility_gap",
        "negative_type_scope_limitation",
        "negative_type_neutral_control_context",
        "negative_type_generic_gap",
        "verified_potential_concern_count",
        "grounded_weakness_count",
        "assessment_limitation_flaw_count",
        "negative_grounding_conflict_count",
        "invalid_negative_evidence_id_count_legacy",
        "negative_semantic_anchor_conflict_count",
        "generic_gap_semantic_rejected_count",
        "negative_evidence_semantic_rejected_count",
        "downgraded_flaw_count",
        "potential_concern_count",
    ]),
    ("State contamination", [
        "state_contamination_count",
        "state_contamination_count_legacy",
        "harmful_state_contamination_count",
        "repairable_state_warning_count",
        "conservative_state_warning_count",
        "state_hygiene_warning_count",
        "weak_target_warning_count",
        "repairable_contamination_target_count",
        "conservative_contamination_target_count",
        "blocked_fallback_contamination_target_count",
        "blocked_empty_contamination_target_count",
        "contamination_unsupported_with_strong_support",
        "contamination_zero_real_support",
        "contamination_stale_gap_persistence",
        "contamination_unsupported_flaw_escalation",
        "contamination_negative_evidence_overclaim",
        "contamination_evidence_misbinding",
        "contamination_meta_leakage",
        "contamination_stale_flaw_persistence",
        "contamination_harmful_recovery_risk",
        "target_gate_real_target",
        "target_gate_weak_target",
        "target_gate_fallback_target",
        "target_gate_empty_target",
    ]),
    ("Contested support", [
        "contested_support_total",
        "contested_final_support_total",
        "claims_with_contested_support",
        "claims_with_contested_final_support",
        "open_conflict_count",
    ]),
    ("Gap cleanup & locator", [
        "evidence_gap_open_count",
        "evidence_gap_resolved_count",
        "evidence_gap_superseded_count",
        "evidence_gap_not_assessable_count",
        "state_hygiene_open_gap_count",
        "state_hygiene_stale_gap_count",
        "targetless_open_gap_count",
        "meta_or_context_open_gap_count",
        "actionable_targeted_open_gap_count",
        "diagnostic_targeted_open_gap_count",
        "targeted_open_gap_count",
        "assessment_limitation_open_gap_count",
        "unresolved_open_count",
        "unresolved_open_raw_count",
        "unresolved_resolved_count",
        "unresolved_deferred_count",
        "targetless_unresolved_deferred_count",
        "programmatic_specific_locator_count",
        "programmatic_weak_locator_count",
        "programmatic_locator_type_table_count",
        "programmatic_locator_type_figure_count",
        "programmatic_locator_type_section_count",
        "programmatic_locator_type_algorithm_count",
        "programmatic_locator_type_theorem_count",
        "programmatic_locator_type_generic_count",
        "programmatic_high_confidence_locator_count",
        "programmatic_low_confidence_locator_count",
    ]),
    ("Recovery", [
        "recovery_attempted",
        "recovery_patch_validated",
        "recovery_patch_committed",
        "recovery_committed",
        "recovery_success",
        "hygiene_delta_improved",
        "recovery_effective_repair",
        "recovery_no_effect_commit",
        "recovery_harmful_commit_risk",
        "recovery_safe_resolution",
        "recovery_safe_resolution_or_clean_state",
        "hygiene_delta_or_safe_block",
        "hygiene_delta_or_safe_block_or_clean_state",
        "recovery_safe_blocked_weak_target",
        "recovery_target_gate_real_target_turns",
        "recovery_target_gate_weak_target_turns",
        "recovery_target_gate_fallback_target_turns",
        "recovery_target_gate_empty_target_turns",
        "recovery_patch_operation_reject_patch_turns",
        "recovery_patch_operation_downgrade_final_to_candidate_turns",
        "recovery_patch_operation_route_to_assessment_limitation_turns",
        "recovery_patch_operation_mark_contested_turns",
        "recovery_patch_operation_resolve_stale_gap_turns",
    ]),
    ("Hygiene", [
        "final_nonreal_strong_support",
        "low_score_promoted_strong",
        "final_report_leakage_paper_count",
        "user_report_leakage_paper_count",
        "synthetic_marker_in_supporting_count",
        "negative_evidence_unlinked_to_flaw",
    ]),
]


def _fmt_delta(b: Any, c: Any) -> str:
    try:
        d = int(c) - int(b)
    except (TypeError, ValueError):
        return ""
    if d > 0:
        return f"+{d}"
    return str(d)


def _render_metric_table(label_b: Optional[str], label_c: str, m_b: Optional[Dict[str, Any]], m_c: Dict[str, Any]) -> List[str]:
    lines: List[str] = []
    for group, keys in GROUP_DEFS:
        lines.append(f"## {group}")
        lines.append("")
        if m_b is not None:
            lines.append(f"| metric | {label_b} | {label_c} | delta |")
            lines.append("|---|---|---|---|")
            for k in keys:
                vb = m_b.get(k, 0)
                vc = m_c.get(k, 0)
                lines.append(f"| `{k}` | {vb} | {vc} | {_fmt_delta(vb, vc)} |")
        else:
            lines.append(f"| metric | {label_c} |")
            lines.append("|---|---|")
            for k in keys:
                lines.append(f"| `{k}` | {m_c.get(k, 0)} |")
        lines.append("")
    return lines


_FAILURE_CODE_INTERPRETATIONS: Dict[str, str] = {
    "SUCCESS": "recovery_patch_committed",
    "EVIDENCE_TARGET_MISMATCH": "safe_blocked_patch (missing or unverified IDs)",
    "BLOCKED_BY_POLICY": "safe_blocked_patch (policy restriction/abstention)",
    "INSUFFICIENT_EVIDENCE": "safe_blocked_patch (insufficient evidence criteria)",
    "SEMANTIC_MISMATCH": "safe_blocked_patch (semantic validation mismatch)",
    "EVIDENCE_SEMANTIC_MISMATCH": "safe_blocked_patch (semantic evidence validation mismatch)",
}


def _render_failure_table(label_b: Optional[str], label_c: str, m_b: Optional[Dict[str, Any]], m_c: Dict[str, Any]) -> List[str]:
    lines = ["## Recovery failure codes", ""]
    keys = set((m_c.get("failure_codes") or {}).keys())
    if m_b is not None:
        keys |= set((m_b.get("failure_codes") or {}).keys())
        lines.append(f"| code | {label_b} | {label_c} | delta | interpreted safety outcome |")
        lines.append("|---|---|---|---|---|")
        for k in sorted(keys):
            vb = (m_b.get("failure_codes") or {}).get(k, 0)
            vc = (m_c.get("failure_codes") or {}).get(k, 0)
            interpretation = _FAILURE_CODE_INTERPRETATIONS.get(k, "unclassified_failure_requires_review")
            lines.append(f"| `{k}` | {vb} | {vc} | {_fmt_delta(vb, vc)} | **{interpretation}** |")
    else:
        lines.append(f"| code | {label_c} | interpreted safety outcome |")
        lines.append("|---|---|---|")
        for k in sorted(keys):
            interpretation = _FAILURE_CODE_INTERPRETATIONS.get(k, "unclassified_failure_requires_review")
            lines.append(f"| `{k}` | {(m_c.get('failure_codes') or {}).get(k, 0)} | **{interpretation}** |")
    lines.append("")
    return lines


def _render_decision_table(label_b: Optional[str], label_c: str, m_b: Optional[Dict[str, Any]], m_c: Dict[str, Any]) -> List[str]:
    lines = ["## Final decision distribution", ""]
    keys = set((m_c.get("final_decision_distribution") or {}).keys())
    if m_b is not None:
        keys |= set((m_b.get("final_decision_distribution") or {}).keys())
        lines.append(f"| decision | {label_b} | {label_c} |")
        lines.append("|---|---|---|")
        for k in sorted(keys):
            vb = (m_b.get("final_decision_distribution") or {}).get(k, 0)
            vc = (m_c.get("final_decision_distribution") or {}).get(k, 0)
            lines.append(f"| `{k}` | {vb} | {vc} |")
    else:
        lines.append(f"| decision | {label_c} |")
        lines.append("|---|---|")
        for k in sorted(keys):
            lines.append(f"| `{k}` | {(m_c.get('final_decision_distribution') or {}).get(k, 0)} |")
    lines.append("")
    return lines


def _render_protection_table(issues: List[Dict[str, Any]], passed: bool) -> List[str]:
    lines = ["## Protection lines", ""]
    lines.append("| metric | op | threshold | note | actual | pass |")
    lines.append("|---|---|---|---|---|---|")
    for it in issues:
        mark = "PASS" if it["passed"] else "**FAIL**"
        note = it.get("threshold_note") or ""
        lines.append(f"| `{it['key']}` | `{it['op']}` | {it['threshold']} | {note} | {it['value']} | {mark} |")
    lines.append("")
    lines.append(f"**Overall protection: {'PASS' if passed else 'FAIL'}**")
    lines.append("")
    return lines


def render_report(label_b: Optional[str], label_c: str,
                  m_b: Optional[Dict[str, Any]], m_c: Dict[str, Any],
                  issues: List[Dict[str, Any]], passed: bool,
                  candidate_path: Path, baseline_path: Optional[Path],
                  dashboard_mode: str) -> str:
    head = ["# Run comparison dashboard v1", ""]
    head.append(f"- candidate: `{candidate_path}` (label: {label_c}, papers: {m_c['paper_count']})")
    if baseline_path is not None:
        head.append(f"- baseline:  `{baseline_path}` (label: {label_b}, papers: {(m_b or {}).get('paper_count', '?')})")
    head.append(f"- dashboard_mode: `{dashboard_mode}`")
    head.append("")
    body = (_render_protection_table(issues, passed)
            + _render_metric_table(label_b, label_c, m_b, m_c)
            + _render_failure_table(label_b, label_c, m_b, m_c)
            + _render_decision_table(label_b, label_c, m_b, m_c))
    return "\n".join(head + body)


# ---------- CLI entry ----------------------------------------------------

def main() -> int:
    p = argparse.ArgumentParser(description="Run-comparison dashboard for review_infer artifacts.")
    p.add_argument("--candidate", required=True, help="Path to the candidate .jsonl")
    p.add_argument("--baseline", default=None, help="Optional path to a baseline .jsonl for side-by-side comparison")
    p.add_argument("--label-candidate", default="candidate")
    p.add_argument("--label-baseline", default="baseline")
    p.add_argument("--output-md", required=True)
    p.add_argument("--output-json", default=None)
    p.add_argument("--output-audit-json", default=None,
                   help="Optional case-level audit JSON with hygiene/recovery attribution")
    p.add_argument("--mode", choices=["auto", "smoke", "full39"], default="auto",
                   help="Protection threshold mode. auto uses smoke for <39 papers and full39 otherwise.")
    p.add_argument("--fail-on-violation", action="store_true",
                   help="Exit with code 1 if any protection line fails on the candidate run")
    args = p.parse_args()

    candidate_path = Path(args.candidate)
    candidate_rows = _load_jsonl(candidate_path)
    m_c = _aggregate(candidate_rows)

    baseline_path = None
    m_b = None
    if args.baseline:
        baseline_path = Path(args.baseline)
        m_b = _aggregate(_load_jsonl(baseline_path))

    dashboard_mode = _resolve_dashboard_mode(m_c, args.mode)
    issues, passed = _check_protection(m_c, dashboard_mode)

    report = render_report(args.label_baseline if m_b is not None else None,
                           args.label_candidate, m_b, m_c, issues, passed,
                           candidate_path, baseline_path, dashboard_mode)
    Path(args.output_md).write_text(report + "\n", encoding="utf-8")
    if args.output_json:
        bundle = {
            "candidate": {"label": args.label_candidate, "path": str(candidate_path), "metrics": m_c},
            "baseline":  ({"label": args.label_baseline, "path": str(baseline_path), "metrics": m_b}
                          if m_b is not None else None),
            "dashboard_mode": dashboard_mode,
            "protection_issues": issues,
            "protection_passed": passed,
        }
        Path(args.output_json).write_text(json.dumps(bundle, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.output_audit_json:
        audit = _case_audit(candidate_rows, m_c, issues)
        Path(args.output_audit_json).write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")

    if args.fail_on_violation and not passed:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
