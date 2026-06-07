from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence

from agent_system.environments.env_package.review.state import (
    MANAGER_ACTION_TYPES,
    _flaw_valid_negative_evidence_ids,
    _is_grounded_paper_negative_evidence_record,
    _is_paper_negative_evidence_record,
    _open_evidence_gaps,
    claim_coverage_summary,
    infer_final_decision,
)
from agent_system.environments.env_package.review.reward import _extract_decision

MIN_STATE_REQUIREMENTS = {
    "s1": {"claims": 0, "evidence_map": 0, "flaw_candidates": 0, "unresolved_questions": 0},
    "s2": {"claims": 1, "evidence_map": 0, "flaw_candidates": 0, "unresolved_questions": 1},
    "s3": {"claims": 1, "evidence_map": 1, "flaw_candidates": 0, "unresolved_questions": 1},
    "s4": {"claims": 1, "evidence_map": 1, "flaw_candidates": 1, "unresolved_questions": 1},
}

AUTO_FINALIZE_MIN_TURNS = {
    "s1": 1,
    "s2": 2,
    "s3": 2,
    "s4": 4,
}

RECOVERY_ACTION_TYPES = {"challenge_previous_hypothesis", "request_evidence_recheck"}
# Experimental controllers are disabled for the Mainline-Final-v1 runtime.
# Keep them as explicit constants for controlled ablations only.
ENABLE_STICKY_RECOVERY_BIAS = False
ENABLE_PROGRESSION_GATE = False
ENABLE_SUPPORT_FORMATION_PASS = False

# Mainline-Final-Integrated P0-2: ``hard_negative_discovery_override`` only
# fires after the manager's own pick (``manager_model``) or after one of the
# deterministic non-recovery progress overrides ran first.  Listing the
# eligible sources explicitly prevents the override from preempting any
# already-routed recovery turn (``s4_recovery_relevant_override``,
# ``negative_evidence_*_override`` etc.).
_HARD_NEGATIVE_DISCOVERY_ELIGIBLE_SOURCES = frozenset(
    {
        "manager_model",
        "claim_coverage_expansion_override",
        "s4_clarification_to_evidence_override",
        "s4_preclaim_clarification_override",
        "s4_claim_progress_override",
        "evidence_progress_override",
        "flaw_progress_override",
        "s4_evidence_to_flaw_override",
    }
)

ACTION_TO_WORKERS = {
    "extract_claims": ["Claim Agent"],
    "verify_evidence": ["Evidence Agent"],
    "analyze_flaws": ["Critique Agent"],
    "request_evidence_recheck": ["Evidence Agent"],
    "challenge_previous_hypothesis": ["Critique Agent", "Evidence Agent"],
    "summarize_progress": [],
    "ask_user_clarification": [],
    "finalize": [],
}


def get_agent_plan(mode: str) -> Dict[str, Any]:
    normalized = (mode or "s4").lower()
    if normalized == "s1":
        return {"mode": "s1", "manager": "Review Manager Agent", "workers": [], "max_turns_default": 1}
    if normalized == "s2":
        return {"mode": "s2", "manager": "Review Manager Agent", "workers": [], "max_turns_default": 3}
    if normalized == "s3":
        return {
            "mode": "s3",
            "manager": "Review Manager Agent",
            "workers": ["General Reviewer Agent 1", "General Reviewer Agent 2"],
            "max_turns_default": 3,
        }
    if normalized == "s4":
        return {
            "mode": "s4",
            "manager": "Review Manager Agent",
            "workers": ["Claim Agent", "Evidence Agent", "Critique Agent"],
            "max_turns_default": 5,
        }
    raise ValueError(f"Unsupported review mode: {mode}")


def synthesize_summary_update(state: Dict[str, Any], action_type: str) -> str:
    risk = state.get("risk_profile", {}) or {}
    revision_summary = state.get("revision_summary", [])[:2]
    conflict_summary = state.get("conflict_summary", [])[:2]
    dominant_risks = (risk.get("dominant_risks") or [])[:2]
    support_signals = (risk.get("support_signals") or [])[:2]

    parts = []
    if action_type == "summarize_progress":
        parts.append("The manager summarized the current review progress.")
    elif action_type == "ask_user_clarification":
        parts.append("The manager paused to request clarification before the next substantive review step.")
    if support_signals:
        parts.append("Support signals: " + " ".join(support_signals))
    if dominant_risks:
        parts.append("Dominant risks: " + " ".join(dominant_risks))
    if revision_summary:
        parts.append("Recent revisions: " + " ".join(revision_summary))
    if conflict_summary:
        parts.append("Recent conflicts: " + " ".join(conflict_summary))
    return " ".join(parts)[:1000]


def state_counts(state: Dict[str, Any]) -> Dict[str, int]:
    return {
        "claims": len(state.get("claims", [])),
        "evidence_map": len(state.get("evidence_map", [])),
        "flaw_candidates": len(state.get("flaw_candidates", [])),
        "unresolved_questions": len(state.get("unresolved_questions", [])),
    }


def payload_counts(payload: Dict[str, Any]) -> Dict[str, int]:
    return {
        "claims": len(payload.get("claims", [])),
        "evidence_map": len(payload.get("evidence_map", [])),
        "flaw_candidates": len(payload.get("flaw_candidates", [])),
        "unresolved_questions": len(payload.get("unresolved_questions", [])),
    }


def general_worker_fallback(worker_ids: Sequence[str], count: int) -> List[str]:
    return list(worker_ids[: max(1, count)]) if worker_ids else []


def pick_workers_for_action(action_type: str, worker_ids: Sequence[str], worker_limit: int) -> List[str]:
    preferred = ACTION_TO_WORKERS.get(action_type, [])
    selected = [agent for agent in preferred if agent in worker_ids]
    if selected:
        return selected[:worker_limit]
    if action_type in {"verify_evidence", "request_evidence_recheck", "challenge_previous_hypothesis", "extract_claims", "analyze_flaws"} and worker_ids:
        return general_worker_fallback(worker_ids, worker_limit)
    return []


def mode_allowed_actions(mode: str) -> set[str]:
    if mode == "s1":
        return {"extract_claims", "summarize_progress", "ask_user_clarification", "finalize"}
    if mode == "s2":
        return {"extract_claims", "verify_evidence", "summarize_progress", "ask_user_clarification", "finalize"}
    if mode == "s3":
        return {"extract_claims", "verify_evidence", "analyze_flaws", "request_evidence_recheck", "summarize_progress", "ask_user_clarification", "finalize"}
    return set(MANAGER_ACTION_TYPES)


def evidence_risk_signals(state: Dict[str, Any]) -> Dict[str, int]:
    evidence_items = state.get("evidence_map", []) or []
    weak_or_missing = 0
    contradictory = 0
    for item in evidence_items:
        strength = str(item.get("strength") or "").lower()
        stance = str(item.get("stance") or "").lower()
        if strength in {"weak", "missing"} or stance == "missing":
            weak_or_missing += 1
        if stance == "contradicts":
            contradictory += 1
    return {
        "weak_or_missing_evidence": weak_or_missing,
        "contradictory_evidence": contradictory,
    }


def _negative_evidence_is_binding_candidate(item: Dict[str, Any], state: Dict[str, Any]) -> bool:
    if not isinstance(item, dict):
        return False
    if not _is_grounded_paper_negative_evidence_record(item, state):
        return False
    if not str(item.get("evidence_id") or "").strip():
        return False
    stance = str(item.get("stance") or "").strip().lower()
    strength = str(item.get("strength") or "").strip().lower()
    if stance != "missing" and strength != "missing":
        return True
    negative_type = str(item.get("negative_evidence_type") or "").strip()
    actionability = str(item.get("negative_evidence_actionability") or "").strip()
    return negative_type in {"direct_contradiction", "negative_result", "missing_ablation", "missing_baseline", "insufficient_evaluation"} or actionability == "actionable_candidate"


def _unlinked_negative_evidence_candidates(state: Dict[str, Any]) -> List[Dict[str, Any]]:
    negative_evidence = [
        item for item in state.get("evidence_map", []) or []
        if _negative_evidence_is_binding_candidate(item, state)
    ]
    negative_ids = {str(item.get("evidence_id") or "").strip() for item in negative_evidence}
    linked_ids: set[str] = set()
    for flaw in state.get("flaw_candidates", []) or []:
        if not isinstance(flaw, dict):
            continue
        for evidence_id in _flaw_valid_negative_evidence_ids(flaw, state):
            if evidence_id in negative_ids:
                linked_ids.add(evidence_id)
    return [
        item for item in negative_evidence
        if str(item.get("evidence_id") or "").strip() not in linked_ids
    ]


def _recent_negative_binding_retry_evidence_ids(recent_turn_logs: Sequence[Dict[str, Any]]) -> set[str]:
    retried: set[str] = set()
    for turn in list(recent_turn_logs or [])[-3:]:
        action_type = str(turn.get("effective_action_type") or turn.get("action_type") or "")
        policy_source = str(turn.get("policy_source") or "")
        if action_type != "analyze_flaws" and policy_source != "negative_evidence_binding_retry_override":
            continue
        for evidence_id in turn.get("target_evidence_ids") or []:
            evidence_id = str(evidence_id).strip()
            if evidence_id:
                retried.add(evidence_id)
    return retried


def _verified_negative_flaw_review_targets(
    state: Dict[str, Any],
    recent_turn_logs: Sequence[Dict[str, Any]],
    *,
    limit: int = 2,
) -> Dict[str, List[str]]:
    retried_ids = _recent_negative_binding_retry_evidence_ids(recent_turn_logs)
    evidence_by_id = {
        str(item.get("evidence_id") or ""): item
        for item in state.get("evidence_map", []) or []
        if isinstance(item, dict) and str(item.get("evidence_id") or "").strip()
    }
    target_flaw_ids: List[str] = []
    target_evidence_ids: List[str] = []
    target_claim_ids: List[str] = []
    for flaw in state.get("flaw_candidates", []) or []:
        if not isinstance(flaw, dict):
            continue
        status = str(flaw.get("status") or "candidate").strip().lower()
        if status not in {"candidate", "potential_concern"}:
            continue
        candidate_evidence_ids = list(flaw.get("negative_evidence_ids") or []) + list(flaw.get("evidence_ids") or [])
        verified_ids: List[str] = []
        for raw in candidate_evidence_ids:
            evidence_id = str(raw or "").strip()
            if not evidence_id or evidence_id in retried_ids:
                continue
            item = evidence_by_id.get(evidence_id)
            if not item or not _is_grounded_paper_negative_evidence_record(item, state):
                continue
            negative_type = str(item.get("negative_evidence_type") or "").strip()
            if negative_type == "neutral_control_context":
                continue
            verified_ids.append(evidence_id)
            claim_id = str(item.get("claim_id") or "").strip()
            if claim_id and claim_id not in target_claim_ids:
                target_claim_ids.append(claim_id)
        if not verified_ids:
            continue
        flaw_id = str(flaw.get("flaw_id") or "").strip()
        if flaw_id and flaw_id not in target_flaw_ids:
            target_flaw_ids.append(flaw_id)
        for evidence_id in verified_ids:
            if evidence_id not in target_evidence_ids:
                target_evidence_ids.append(evidence_id)
        for claim_id in flaw.get("related_claim_ids") or []:
            claim_id = str(claim_id or "").strip()
            if claim_id and claim_id not in target_claim_ids:
                target_claim_ids.append(claim_id)
        if len(target_flaw_ids) >= limit:
            break
    return {
        "target_flaw_ids": target_flaw_ids[:limit],
        "target_evidence_ids": target_evidence_ids[:limit],
        "target_claim_ids": target_claim_ids[:limit],
    }


def _negative_evidence_binding_retry_targets(
    state: Dict[str, Any],
    recent_turn_logs: Sequence[Dict[str, Any]],
    *,
    limit: int = 2,
) -> Dict[str, List[str]]:
    retried_ids = _recent_negative_binding_retry_evidence_ids(recent_turn_logs)
    candidates = [
        item for item in _unlinked_negative_evidence_candidates(state)
        if str(item.get("evidence_id") or "").strip() not in retried_ids
    ]
    target_evidence_ids: List[str] = []
    target_claim_ids: List[str] = []
    for item in candidates:
        evidence_id = str(item.get("evidence_id") or "").strip()
        claim_id = str(item.get("claim_id") or "").strip()
        if evidence_id and evidence_id not in target_evidence_ids:
            target_evidence_ids.append(evidence_id)
        if claim_id and claim_id not in target_claim_ids:
            target_claim_ids.append(claim_id)
        if len(target_evidence_ids) >= limit:
            break
    return {
        "target_evidence_ids": target_evidence_ids,
        "target_claim_ids": target_claim_ids,
    }


def _recent_negative_evidence_formation_flaw_counts(recent_turn_logs: Sequence[Dict[str, Any]]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for turn in list(recent_turn_logs or [])[-5:]:
        if str(turn.get("policy_source") or "") not in {"negative_evidence_formation_override", "hard_negative_discovery_override"}:
            continue
        for flaw_id in turn.get("target_flaw_ids") or []:
            flaw_id = str(flaw_id).strip()
            if flaw_id:
                counts[flaw_id] = counts.get(flaw_id, 0) + 1
    return counts


def _has_recent_negative_evidence_formation_turn(recent_turn_logs: Sequence[Dict[str, Any]], *, window: int = 5) -> bool:
    for turn in list(recent_turn_logs or [])[-window:]:
        if turn.get("negative_evidence_formation_required"):
            return True
        if str(turn.get("policy_source") or "") in {"negative_evidence_formation_override", "hard_negative_discovery_override"}:
            return True
    return False


def _grounded_negative_evidence_count(state: Dict[str, Any]) -> int:
    return sum(
        1
        for item in state.get("evidence_map", []) or []
        if isinstance(item, dict) and _is_grounded_paper_negative_evidence_record(item, state)
    )


def _is_non_real_review_claim_id(claim_id: str) -> bool:
    value = str(claim_id or "").strip().lower()
    return (
        not value
        or _is_fallback_claim_id(value)
        or value.startswith("context")
        or value.startswith("claim-recovery")
        or value.startswith("claim-paper-context")
        or value.startswith("claim-paper-fallback")
        or value.startswith("recovery")
    )


def _claim_item_has_prompt_leakage(item: Dict[str, Any]) -> bool:
    claim_text = str((item or {}).get("claim") or "").strip().lower()
    if not claim_text:
        return False
    return any(marker in claim_text for marker in _PROMPT_LEAK_MARKERS)


def _claim_item_is_recovery_usable(item: Dict[str, Any], *, require_claim_text: bool = False) -> bool:
    claim_text = str((item or {}).get("claim") or "").strip()
    if require_claim_text and not claim_text:
        return False
    claim_id = str((item or {}).get("claim_id") or "").strip().lower()
    if not claim_id:
        return False
    if _claim_item_has_prompt_leakage(item):
        return False
    origin_kind = str((item or {}).get("claim_origin_kind") or "").strip().lower()
    claim_kind = str((item or {}).get("claim_kind") or "").strip().lower()
    origin = " ".join(
        str((item or {}).get(key) or "")
        for key in ("claim_origin", "claim_source", "source_stage", "provenance")
    ).lower()
    if claim_id.startswith(("claim-context", "claim-paper-context", "claim-recovery", "recovery")):
        return False
    if claim_id.startswith("claim-fallback"):
        return False
    if claim_id.startswith("claim-paper-fallback"):
        return (
            claim_kind == "paper_extracted"
            and origin_kind == "raw_salvaged_claim_agent_output"
            and "context_derived" not in origin
        )
    if origin_kind == "context_synthesized" or "context_derived" in origin:
        return False
    return not _is_non_real_review_claim_id(claim_id)


def _claim_is_recovery_usable(state: Dict[str, Any], claim_id: str) -> bool:
    claim_id = str(claim_id or "").strip()
    if not claim_id:
        return False
    for item in state.get("claims", []) or []:
        if isinstance(item, dict) and str(item.get("claim_id") or "").strip() == claim_id:
            return _claim_item_is_recovery_usable(item)
    return False


def _fallback_negative_evidence_claim_ids(state: Dict[str, Any], *, limit: int = 2) -> List[str]:
    selected: List[str] = []
    preferred_status = {"supported", "partially_supported", "uncertain"}
    claims = [item for item in state.get("claims", []) or [] if isinstance(item, dict)]
    for pass_preferred in (True, False):
        for item in claims:
            claim_id = str(item.get("claim_id") or "").strip()
            if not _claim_item_is_recovery_usable(item, require_claim_text=True):
                continue
            status = str(item.get("status") or "").strip().lower()
            if pass_preferred and status not in preferred_status:
                continue
            if claim_id not in selected:
                selected.append(claim_id)
            if len(selected) >= limit:
                return selected
    return selected


def _unverified_flaw_negative_evidence_targets(
    state: Dict[str, Any],
    recent_turn_logs: Sequence[Dict[str, Any]],
    *,
    limit: int = 2,
    max_retry_per_flaw: int = 1,
) -> Dict[str, List[str]]:
    retry_counts = _recent_negative_evidence_formation_flaw_counts(recent_turn_logs)
    evidence_lookup = {
        str(item.get("evidence_id") or "").strip(): item
        for item in state.get("evidence_map", []) or []
        if isinstance(item, dict) and str(item.get("evidence_id") or "").strip()
    }
    target_flaw_ids: List[str] = []
    target_claim_ids: List[str] = []
    target_evidence_ids: List[str] = []
    for flaw in state.get("flaw_candidates", []) or []:
        if not isinstance(flaw, dict):
            continue
        flaw_id = str(flaw.get("flaw_id") or "").strip()
        status = str(flaw.get("status") or "candidate").strip().lower()
        if not flaw_id or status not in _ACTIVE_FLAW_STATUSES:
            continue
        if retry_counts.get(flaw_id, 0) >= max_retry_per_flaw:
            continue
        if _flaw_valid_negative_evidence_ids(flaw, state):
            continue
        claim_ids = [str(item).strip() for item in flaw.get("related_claim_ids") or [] if str(item).strip()]
        evidence_ids = [str(item).strip() for item in flaw.get("negative_evidence_ids") or flaw.get("evidence_ids") or [] if str(item).strip()]
        for evidence_id in evidence_ids:
            item = evidence_lookup.get(evidence_id)
            claim_id = str((item or {}).get("claim_id") or "").strip()
            if claim_id and claim_id not in claim_ids:
                claim_ids.append(claim_id)
        if not claim_ids:
            claim_ids = _fallback_negative_evidence_claim_ids(state, limit=limit)
        if not claim_ids and not evidence_ids:
            continue
        target_flaw_ids.append(flaw_id)
        for claim_id in claim_ids:
            if claim_id not in target_claim_ids:
                target_claim_ids.append(claim_id)
        for evidence_id in evidence_ids:
            if evidence_id not in target_evidence_ids:
                target_evidence_ids.append(evidence_id)
        if len(target_flaw_ids) >= limit:
            break
    return {
        "target_flaw_ids": target_flaw_ids,
        "target_claim_ids": target_claim_ids[:limit],
        "target_evidence_ids": target_evidence_ids[: max(limit * 2, 2)],
    }


def _claim_extraction_turn_count(recent_turn_logs: Sequence[Dict[str, Any]]) -> int:
    count = 0
    for turn in recent_turn_logs or []:
        action_type = str(turn.get("effective_action_type") or turn.get("action_type") or "")
        if action_type == "extract_claims":
            count += 1
    return count


def _claim_coverage_expansion_plan(
    state: Dict[str, Any],
    recent_turn_logs: Sequence[Dict[str, Any]],
) -> Dict[str, Any]:
    coverage = claim_coverage_summary(state)
    counts = state_counts(state)
    extract_count = _claim_extraction_turn_count(recent_turn_logs)
    prior_expansion = any(
        turn.get("claim_coverage_expansion_required")
        or str(turn.get("policy_source") or "") == "claim_coverage_expansion_override"
        for turn in recent_turn_logs or []
    )
    required = (
        counts["claims"] > 0
        and counts["evidence_map"] == 0
        and counts["flaw_candidates"] == 0
        and extract_count >= 1
        and extract_count < 2
        and not prior_expansion
        and bool(coverage.get("claim_coverage_expansion_recommended"))
    )
    return {
        "required": required,
        "coverage": coverage,
        "missing_tags": list(coverage.get("missing_review_coverage_tags", [])),
        "target_claim_ids": [],
    }


def _turn_requested_recovery(turn: Dict[str, Any]) -> bool:
    action_type = str(turn.get("effective_action_type") or turn.get("action_type") or "")
    return action_type in RECOVERY_ACTION_TYPES or bool(turn.get("recovery_patch_mode_entered"))


def _state_is_recovery_relevant(state: Dict[str, Any], recent_turn_logs: Sequence[Dict[str, Any]]) -> bool:
    if bool(state.get("recovery_relevant")):
        return True
    if state.get("conflict_notes") or state.get("recovery_blocked_by"):
        return True
    latest_patch_log = state.get("_latest_patch_log", {}) or {}
    if str(latest_patch_log.get("recovery_failure_code") or "").strip():
        return True
    for turn in reversed(list(recent_turn_logs or [])[-3:]):
        if _turn_requested_recovery(turn):
            return True
        if str(turn.get("emission_failure_code") or "").strip():
            return True
        if str(turn.get("recovery_blocked_by") or "").strip():
            return True
    return False


def _sticky_recovery_bias(
    state: Dict[str, Any],
    recent_turn_logs: Sequence[Dict[str, Any]],
    action_type: str,
    allowed_actions: set[str],
) -> tuple[str, list[str]]:
    notes: list[str] = []
    if not _state_is_recovery_relevant(state, recent_turn_logs):
        return action_type, notes
    recent_turns = list(recent_turn_logs or [])
    previous_turn = recent_turns[-1] if recent_turns else {}
    previous_failed_patch_mode = bool(previous_turn.get("recovery_patch_mode_entered")) and not bool(previous_turn.get("recovery_emitted"))
    conflict_count = len(state.get("conflict_notes", []) or [])
    evidence_risks = evidence_risk_signals(state)
    unresolved = len([q for q in (state.get("unresolved_questions") or []) if q.get("status") != "resolved"])
    if action_type in RECOVERY_ACTION_TYPES:
        return action_type, notes
    if previous_failed_patch_mode and "challenge_previous_hypothesis" in allowed_actions:
        notes.append("Sticky recovery bias kept the manager in recovery after a failed recovery_patch turn.")
        return "challenge_previous_hypothesis", notes
    if conflict_count > 0 and "challenge_previous_hypothesis" in allowed_actions:
        notes.append("Sticky recovery bias promoted challenge_previous_hypothesis because unresolved conflicts remain.")
        return "challenge_previous_hypothesis", notes
    if (evidence_risks["weak_or_missing_evidence"] > 0 or unresolved > 0) and "request_evidence_recheck" in allowed_actions:
        notes.append("Sticky recovery bias promoted request_evidence_recheck because recovery-relevant evidence gaps remain open.")
        return "request_evidence_recheck", notes
    return action_type, notes



def _progression_gate_safe_action(
    state: Dict[str, Any],
    original_action: str,
    blocked_action: str,
    allowed_actions: set[str],
) -> str:
    counts = state_counts(state)
    normalized_original = str(original_action or "").strip()
    if normalized_original in {"verify_evidence", "analyze_flaws"} and normalized_original in allowed_actions:
        return normalized_original
    if counts["claims"] > 0 and "verify_evidence" in allowed_actions:
        return "verify_evidence"
    if counts["evidence_map"] > 0 and "analyze_flaws" in allowed_actions:
        return "analyze_flaws"
    if normalized_original and normalized_original in allowed_actions:
        return normalized_original
    if str(blocked_action or "") in allowed_actions:
        return str(blocked_action)
    return "verify_evidence" if "verify_evidence" in allowed_actions else str(blocked_action or normalized_original or "summarize_progress")


def _progression_gate_issues(
    state: Dict[str, Any],
    action_type: str,
    raw_target_claim_ids: Sequence[str],
) -> List[str]:
    if action_type not in RECOVERY_ACTION_TYPES:
        return []
    normalized_targets = _normalize_target_claim_ids(raw_target_claim_ids)
    real_targets = [claim_id for claim_id in normalized_targets if not _is_fallback_claim_id(claim_id)]
    issues: List[str] = []
    if any(_is_fallback_claim_id(claim_id) for claim_id in normalized_targets):
        issues.append("fallback_target")
    if len(real_targets) > 2 or (action_type == "challenge_previous_hypothesis" and len(real_targets) > 1):
        issues.append("broad_target")
    risk = state.get("risk_profile", {}) or {}
    conflict_count = int(risk.get("conflict_count", 0) or 0)
    contradictory = evidence_risk_signals(state)["contradictory_evidence"]
    hypotheses = state.get("current_hypotheses", []) or []
    if action_type == "challenge_previous_hypothesis" and conflict_count <= 0 and contradictory <= 0 and not hypotheses:
        issues.append("weak_conflict")
    if action_type == "request_evidence_recheck":
        weak_missing = evidence_risk_signals(state)["weak_or_missing_evidence"]
        if weak_missing <= 0 and conflict_count <= 0:
            issues.append("weak_conflict")
    return list(dict.fromkeys(issues))


def _progression_gate_reason(issues: Sequence[str]) -> str:
    normalized = [str(item) for item in issues if str(item)]
    if not normalized:
        return ""
    if len(set(normalized)) > 1:
        return "multiple_reasons"
    return normalized[0]

def _recovery_progression_issues(
    state: Dict[str, Any],
    action_type: str,
    target_claim_ids: Sequence[str],
    recent_turn_logs: Optional[Sequence[Dict[str, Any]]] = None,
) -> List[str]:
    del state, recent_turn_logs
    if action_type not in RECOVERY_ACTION_TYPES:
        return []
    normalized_targets = _normalize_target_claim_ids(target_claim_ids)
    issues: List[str] = []
    real_targets = [claim_id for claim_id in normalized_targets if not _is_fallback_claim_id(claim_id)]
    if action_type == "challenge_previous_hypothesis" and len(real_targets) > 2:
        issues.append("broad_target_set")
    fallback_targets = [claim_id for claim_id in normalized_targets if _is_fallback_claim_id(claim_id)]
    if fallback_targets:
        issues.append("fallback_anchored_target")
    return issues


def _choose_progression_throttle_action(
    state: Dict[str, Any],
    action_type: str,
    allowed_actions: set[str],
) -> str:
    counts = state_counts(state)
    normalized_action = str(action_type or "").strip()
    if normalized_action == "challenge_previous_hypothesis":
        if "request_evidence_recheck" in allowed_actions and counts["evidence_map"] > 0:
            return "request_evidence_recheck"
        if "verify_evidence" in allowed_actions and counts["claims"] > 0:
            return "verify_evidence"
    elif normalized_action == "request_evidence_recheck":
        if counts["evidence_map"] == 0 and "verify_evidence" in allowed_actions and counts["claims"] > 0:
            return "verify_evidence"
        return normalized_action
    if "analyze_flaws" in allowed_actions and counts["evidence_map"] > 0:
        return "analyze_flaws"
    if "summarize_progress" in allowed_actions:
        return "summarize_progress"
    return normalized_action or action_type


_RECOVERY_ELIGIBLE_CLAIM_STATUSES = {"supported", "partially_supported", "uncertain"}
_INACTIVE_CLAIM_STATUSES = {"unsupported", "superseded"}
_ACTIVE_FLAW_STATUSES = {"candidate", "confirmed"}


def _claim_ids_by_status(
    claims: Sequence[Dict[str, Any]],
    *,
    include: Optional[set[str]] = None,
    exclude: Optional[set[str]] = None,
    limit: int = 2,
    require_real: bool = False,
) -> List[str]:
    selected: List[str] = []
    for item in claims:
        claim_id = str(item.get("claim_id") or "").strip()
        status = str(item.get("status") or "").strip().lower()
        if not claim_id:
            continue
        if require_real and not _claim_item_is_recovery_usable(item):
            continue
        if include is not None and status not in include:
            continue
        if exclude is not None and status in exclude:
            continue
        if claim_id not in selected:
            selected.append(claim_id)
        if len(selected) >= limit:
            break
    return selected


def _claim_has_verified_negative_recovery_evidence(state: Dict[str, Any], claim_id: str) -> bool:
    claim_id = str(claim_id or "").strip()
    if not claim_id or not _claim_is_recovery_usable(state, claim_id):
        return False
    actionable_types = {
        "direct_contradiction",
        "negative_result",
        "missing_ablation",
        "missing_baseline",
        "insufficient_evaluation",
    }
    for item in state.get("evidence_map", []) or []:
        if not isinstance(item, dict):
            continue
        if str(item.get("claim_id") or "").strip() != claim_id:
            continue
        if not _is_grounded_paper_negative_evidence_record(item, state):
            continue
        stance = str(item.get("stance") or "").strip().lower()
        strength = str(item.get("strength") or "").strip().lower()
        negative_type = str(item.get("negative_evidence_type") or "").strip()
        actionability = str(item.get("negative_evidence_actionability") or "").strip()
        if stance in {"contradicts", "refutes", "weakens", "does_not_support", "unsupported"}:
            return True
        if strength in {"missing", "insufficient"} and (
            negative_type in actionable_types or actionability == "actionable_candidate"
        ):
            return True
    return False


def _recovery_ready_claim_ids(state: Dict[str, Any], claim_ids: Sequence[str], *, limit: int = 2) -> List[str]:
    claim_status = {
        str(item.get("claim_id") or "").strip(): str(item.get("status") or "uncertain").strip().lower()
        for item in state.get("claims", []) or []
        if isinstance(item, dict) and str(item.get("claim_id") or "").strip()
    }
    selected: List[str] = []
    for claim_id in _normalize_target_claim_ids(claim_ids):
        if not _claim_is_recovery_usable(state, claim_id):
            continue
        if claim_status.get(claim_id) not in _RECOVERY_ELIGIBLE_CLAIM_STATUSES:
            continue
        if not _claim_has_verified_negative_recovery_evidence(state, claim_id):
            continue
        if claim_id not in selected:
            selected.append(claim_id)
        if len(selected) >= limit:
            break
    return selected


def _verified_negative_recovery_claim_ids(state: Dict[str, Any], *, limit: int = 2) -> List[str]:
    claim_ids = [
        str(item.get("claim_id") or "").strip()
        for item in state.get("claims", []) or []
        if isinstance(item, dict) and str(item.get("claim_id") or "").strip()
    ]
    return _recovery_ready_claim_ids(state, claim_ids, limit=limit)


def _flaw_ids_by_status(
    flaws: Sequence[Dict[str, Any]],
    *,
    include: Optional[set[str]] = None,
    limit: int = 2,
) -> List[str]:
    selected: List[str] = []
    for item in flaws:
        flaw_id = str(item.get("flaw_id") or "").strip()
        status = str(item.get("status") or "").strip().lower()
        if not flaw_id:
            continue
        if include is not None and status not in include:
            continue
        if flaw_id not in selected:
            selected.append(flaw_id)
        if len(selected) >= limit:
            break
    return selected




def _active_unverified_flaw_ids(state: Dict[str, Any], *, limit: int = 2) -> List[str]:
    selected: List[str] = []
    for flaw in state.get("flaw_candidates", []) or []:
        if not isinstance(flaw, dict):
            continue
        flaw_id = str(flaw.get("flaw_id") or "").strip()
        status = str(flaw.get("status") or "candidate").strip().lower()
        if not flaw_id or status not in _ACTIVE_FLAW_STATUSES:
            continue
        if _flaw_valid_negative_evidence_ids(flaw, state):
            continue
        if flaw_id not in selected:
            selected.append(flaw_id)
        if len(selected) >= limit:
            break
    return selected

def _sanitize_targets_for_action(
    state: Dict[str, Any],
    action_type: str,
    payload: Dict[str, Any],
    inferred: Dict[str, Any],
) -> Dict[str, Any]:
    claims = state.get("claims", []) or []
    flaws = state.get("flaw_candidates", []) or []
    claim_lookup = {
        str(item.get("claim_id") or "").strip(): str(item.get("status") or "").strip().lower()
        for item in claims
        if str(item.get("claim_id") or "").strip()
    }
    flaw_lookup = {
        str(item.get("flaw_id") or "").strip(): str(item.get("status") or "").strip().lower()
        for item in flaws
        if str(item.get("flaw_id") or "").strip()
    }

    target_claim_ids = list(payload.get("target_claim_ids") or inferred.get("target_claim_ids") or [])
    target_flaw_ids = list(payload.get("target_flaw_ids") or inferred.get("target_flaw_ids") or [])

    if action_type == "challenge_previous_hypothesis":
        target_claim_ids = _recovery_ready_claim_ids(state, target_claim_ids, limit=2)
        if not target_claim_ids:
            target_claim_ids = _verified_negative_recovery_claim_ids(state, limit=2)

        target_flaw_ids = [
            fid for fid in target_flaw_ids
            if flaw_lookup.get(fid) in _ACTIVE_FLAW_STATUSES
        ]
        for fid in _active_unverified_flaw_ids(state, limit=2):
            if fid not in target_flaw_ids:
                target_flaw_ids.append(fid)
        if not target_claim_ids and not target_flaw_ids:
            target_flaw_ids = _flaw_ids_by_status(
                flaws,
                include=_ACTIVE_FLAW_STATUSES,
                limit=2,
            )
    elif action_type in {"verify_evidence", "request_evidence_recheck", "analyze_flaws"}:
        require_real_claim = action_type in {"request_evidence_recheck", "analyze_flaws"}
        target_claim_ids = [
            cid for cid in target_claim_ids
            if claim_lookup.get(cid) not in _INACTIVE_CLAIM_STATUSES
            and not (require_real_claim and not _claim_is_recovery_usable(state, cid))
        ]
        if not target_claim_ids:
            target_claim_ids = _claim_ids_by_status(
                claims,
                exclude=_INACTIVE_CLAIM_STATUSES,
                limit=3 if action_type != "request_evidence_recheck" else 2,
                require_real=require_real_claim,
            )

    payload["target_claim_ids"] = target_claim_ids
    payload["target_flaw_ids"] = target_flaw_ids
    return payload


_RECOVERY_ACTIONS = {"challenge_previous_hypothesis", "request_evidence_recheck"}


def _has_prior_recovery_action(recent_turn_logs: Sequence[Dict[str, Any]]) -> bool:
    # Check if any recent turn was a recovery action
    for tl in recent_turn_logs[-3:]:  # Check last few turns
        if (
            tl.get("recovery_attempted") or
            tl.get("action_type") in _RECOVERY_ACTIONS or
            tl.get("effective_action_type") in _RECOVERY_ACTIONS
        ):
            return True
    return False


def _has_recent_progression_throttle(recent_turn_logs: Sequence[Dict[str, Any]]) -> bool:
    for tl in recent_turn_logs[-2:]:
        if str(tl.get("policy_source") or "") == "progression_throttle_override":
            return True
    return False


def _real_strong_support_total(state: Dict[str, Any]) -> int:
    real_claim_ids = {
        str(item.get("claim_id") or "").strip()
        for item in state.get("claims", []) or []
        if item.get("claim_id") and not str(item.get("claim_id") or "").startswith("claim-fallback")
    }
    total = 0
    for evidence in state.get("evidence_map", []) or []:
        claim_id = str(evidence.get("claim_id") or "").strip()
        binding_status = str(evidence.get("binding_status") or "").strip()
        if (
            claim_id in real_claim_ids
            and str(evidence.get("strength") or "").lower() == "strong"
            and str(evidence.get("stance") or "").lower() in {"supports", "partially_supports"}
            and binding_status not in {"fallback_unverified", "invalid_claim_id", "unbound", "fallback_bound"}
        ):
            total += 1
    return total


def _verified_moderate_support_total(state: Dict[str, Any]) -> int:
    """Count verified moderate/medium positive support bound to non-fallback
    claims.  Used by the budget-aware ``hard_negative_discovery_override``
    gate to detect a paper whose support inventory is already non-empty
    even when no ``strong`` support exists yet."""
    real_claim_ids = {
        str(item.get("claim_id") or "").strip()
        for item in state.get("claims", []) or []
        if item.get("claim_id") and not str(item.get("claim_id") or "").startswith("claim-fallback")
    }
    total = 0
    for evidence in state.get("evidence_map", []) or []:
        claim_id = str(evidence.get("claim_id") or "").strip()
        binding_status = str(evidence.get("binding_status") or "").strip()
        strength = str(evidence.get("strength") or "").lower()
        stance = str(evidence.get("stance") or "").lower()
        if (
            claim_id in real_claim_ids
            and strength in {"medium", "moderate"}
            and stance in {"supports", "partially_supports"}
            and binding_status not in {"fallback_unverified", "invalid_claim_id", "unbound", "fallback_bound"}
        ):
            total += 1
    return total


def _positive_inventory_ready(state: Dict[str, Any]) -> bool:
    """Return ``True`` when the paper has enough positive support that
    spending one turn on a hard-negative discovery pass is acceptable.

    Mainline-Final-Integrated P0-2 budget-aware refinement: under
    ``max_turns=4`` the previous gate spent T3 on negative discovery and
    T4 on the recovery commit, leaving only T2 for support formation.
    Net result: ``real_strong_support_total`` collapsed (37 -> 14 on
    full39).  This helper is consulted by the gate to skip the override
    in tight-budget windows (last 1 free turn) when no positive support
    has formed yet, so the manager can keep grounding strong support
    instead of giving up the only remaining support-finding turn.
    """
    if _real_strong_support_total(state) >= 1:
        return True
    if _verified_moderate_support_total(state) >= 2:
        return True
    return False


def _recent_normal_evidence_verification_count(recent_turn_logs: Sequence[Dict[str, Any]], lookback: int = 4) -> int:
    total = 0
    for turn in list(recent_turn_logs or [])[-lookback:]:
        action = str(turn.get("effective_action_type") or turn.get("action_type") or "")
        turn_mode = str(turn.get("turn_mode") or "")
        if action == "verify_evidence" and turn_mode != "recovery_patch":
            total += 1
    return total


def _support_formation_pass_reason(
    state: Dict[str, Any],
    action_type: str,
    allowed_actions: set[str],
    recent_turn_logs: Sequence[Dict[str, Any]],
) -> str:
    # Disabled by default after mixed16/fulltest trials: extra evidence turns
    # improved some support counts but repeatedly hurt recovery/commit flow.
    # Keep the helper for controlled ablations, not for the mainline runtime.
    if not ENABLE_SUPPORT_FORMATION_PASS:
        return ""
    support_sensitive_actions = set(RECOVERY_ACTION_TYPES) | {"analyze_flaws", "summarize_progress", "finalize"}
    if action_type not in support_sensitive_actions:
        return ""
    if "verify_evidence" not in allowed_actions:
        return ""
    if not state.get("claims"):
        return ""
    if any(turn.get("support_formation_pass_triggered") for turn in recent_turn_logs or []):
        return ""
    if _has_prior_recovery_action(recent_turn_logs):
        return ""
    real_support = _real_strong_support_total(state)
    recent_verify = _recent_normal_evidence_verification_count(recent_turn_logs)
    if real_support < 2 and recent_verify < 2:
        return f"low_real_strong_support:{real_support};recent_verify_evidence:{recent_verify};from_action:{action_type}"
    return ""



def _choose_recovery_action(state: Dict[str, Any]) -> str:
    """Choose the best recovery action based on current state.

    Key insight: when flaws already exist, the issue is usually revising
    flaw judgments (challenge) not gathering more evidence (recheck).
    Prefer challenge_previous_hypothesis when flaw_candidates are present.
    """
    risks = evidence_risk_signals(state)
    has_flaws = len(state.get("flaw_candidates", [])) > 0
    if risks["contradictory_evidence"] > 0:
        return "challenge_previous_hypothesis"
    # When flaws exist, prefer challenge over recheck — the problem is the
    # flaw judgment, not the evidence gathering.
    if has_flaws:
        return "request_evidence_recheck" if _active_unverified_flaw_ids(state, limit=1) else "challenge_previous_hypothesis"
    if risks["weak_or_missing_evidence"] > 0:
        return "request_evidence_recheck"
    conflict_count = len(state.get("conflict_notes", []))
    if conflict_count > 0:
        return "challenge_previous_hypothesis"
    return "request_evidence_recheck"


def _choose_blocking_recovery_action(state: Dict[str, Any]) -> str:
    risks = evidence_risk_signals(state)
    risk = state.get("risk_profile", {}) or {}
    if risks["contradictory_evidence"] > 0 or state.get("conflict_notes"):
        return "challenge_previous_hypothesis"
    if _active_unverified_flaw_ids(state, limit=1):
        return "request_evidence_recheck"
    if _open_evidence_gaps(state) or str(risk.get("readiness") or "") == "needs_targeted_recheck":
        return "request_evidence_recheck"
    return _choose_recovery_action(state)


def _has_blocking_recovery_signal(state: Dict[str, Any], recent_turn_logs: Sequence[Dict[str, Any]]) -> bool:
    recent_turn_logs = list(recent_turn_logs or [])
    if len(recent_turn_logs) < 3:
        return False
    if not state.get("claims") or not state.get("evidence_map"):
        return False
    risk = state.get("risk_profile", {}) or {}
    flaws = state.get("flaw_candidates", []) or []
    has_active_flaw = any(str(item.get("status") or "candidate") not in {"downgraded", "retracted"} for item in flaws)
    if _active_unverified_flaw_ids(state, limit=1):
        return True
    open_evidence_gaps = _open_evidence_gaps(state)
    if open_evidence_gaps and has_active_flaw:
        return True
    if str(risk.get("readiness") or "") == "needs_targeted_recheck" and has_active_flaw:
        return True
    if int(risk.get("major_flaw_count", 0) or 0) > 0 and has_active_flaw:
        return True
    if int(risk.get("open_question_count", 0) or 0) >= 3 and (has_active_flaw or open_evidence_gaps):
        return True
    return False


def _normalize_recovery_phase(value: Any) -> str:
    phase = str(value or "").strip().lower()
    return phase if phase in {"normal_review", "recovery"} else ""


def _normalize_target_claim_ids(target_claim_ids: Sequence[str]) -> List[str]:
    return list(dict.fromkeys(str(item).strip() for item in (target_claim_ids or []) if str(item).strip()))


def _is_recovery_continuation_action(action_type: str) -> bool:
    return str(action_type or "").strip() in RECOVERY_ACTION_TYPES


def _apply_sticky_target_bias(
    target_claim_ids: Sequence[str],
    sticky_target_id: str,
) -> tuple[List[str], bool, bool]:
    normalized_targets = _normalize_target_claim_ids(target_claim_ids)
    if not sticky_target_id:
        return normalized_targets, False, False
    if len(normalized_targets) < 2:
        return normalized_targets, False, False
    if sticky_target_id in normalized_targets:
        blocked_switch = normalized_targets[0] != sticky_target_id
        if not blocked_switch:
            return normalized_targets, False, False
        reordered = [sticky_target_id] + [claim_id for claim_id in normalized_targets if claim_id != sticky_target_id]
        return reordered, True, True
    return normalized_targets, False, False


_FALLBACK_CLAIM_PREFIXES = (
    "claim-fallback-",
    "claim-context-",
    "claim-paper-fallback-",
    "claim-paper-context-",
)
_PROMPT_LEAK_MARKERS = (
    "do not output",
    "json block",
    "output exactly one strict json",
    "<json>",
    "<think>",
    "[truncated]",
)


def _is_fallback_claim_id(claim_id: str) -> bool:
    return str(claim_id or "").strip().lower().startswith(_FALLBACK_CLAIM_PREFIXES)


def _is_fallback_evidence_id(evidence_id: str) -> bool:
    value = str(evidence_id or "").strip()
    return value.startswith("evidence-fallback-") or value.startswith("evidence-general-")


def _target_is_broad(target_claim_ids: Sequence[str]) -> bool:
    # Observability only: three or more claim targets is broad for recovery debugging.
    return len(_normalize_target_claim_ids(target_claim_ids)) >= 3


def _fallback_claim_ids(target_claim_ids: Sequence[str]) -> List[str]:
    return [claim_id for claim_id in _normalize_target_claim_ids(target_claim_ids) if _is_fallback_claim_id(claim_id)]


def _target_quality(state: Dict[str, Any], target_claim_ids: Sequence[str], action_type: str = "") -> tuple[str, List[str]]:
    targets = _normalize_target_claim_ids(target_claim_ids)
    reasons: List[str] = []
    if not targets:
        return "empty_target", ["empty_target"]
    fallback_ids = _fallback_claim_ids(targets)
    if fallback_ids:
        reasons.append("fallback_target")
    if _target_is_broad(targets):
        reasons.append("broad_target")
    if str(action_type or "") in RECOVERY_ACTION_TYPES and not fallback_ids:
        strongest = max((_claim_contradiction_strength(state, claim_id) for claim_id in targets), default=0)
        if strongest <= 0:
            reasons.append("weak_target")
    if "fallback_target" in reasons:
        label = "fallback_target"
    elif "broad_target" in reasons:
        label = "broad_target"
    elif "weak_target" in reasons:
        label = "weak_target"
    else:
        label = "narrow_real_target"
        reasons.append("narrow_real_target")
    return label, reasons


# --- Target Quality Certificate (TQC) — observability-only -----------------
# Composes existing observability signals into 5 diagnostic dimensions plus a
# composite recovery_readiness_label. Used by analysis of Layer 3 runs to ask:
# "Is the current target actually ready for aggressive recovery?"
# No runtime behavior change; only writes fields into the payload / turn_log.

def _tqc_evidence_for_claims(state: Dict[str, Any], target_claim_ids: Sequence[str]) -> List[Dict[str, Any]]:
    targets = set(_normalize_target_claim_ids(target_claim_ids))
    if not targets:
        return []
    out: List[Dict[str, Any]] = []
    for ev in state.get("evidence_map") or []:
        claim_id = str(ev.get("claim_id") or "").strip()
        if claim_id in targets:
            out.append(ev)
    return out


def _tqc_target_source_label(target_claim_ids: Sequence[str]) -> str:
    targets = _normalize_target_claim_ids(target_claim_ids)
    if not targets:
        return "empty_or_unknown"
    fb = sum(1 for c in targets if _is_fallback_claim_id(c))
    if fb == len(targets):
        return "fallback_claim"
    if fb > 0:
        return "mixed_real_and_fallback"
    return "real_claim"


def _tqc_target_width_label(target_claim_ids: Sequence[str]) -> str:
    n = len(_normalize_target_claim_ids(target_claim_ids))
    if n == 0:
        return "empty"
    if n == 1:
        return "single_target"
    if n >= 3:
        return "broad_target_set"
    return "small_target_set"


def _tqc_evidence_grounding_label(state: Dict[str, Any], target_claim_ids: Sequence[str]) -> str:
    targets = _normalize_target_claim_ids(target_claim_ids)
    if not targets:
        return "no_aligned_evidence"
    aligned = _tqc_evidence_for_claims(state, targets)
    if not aligned:
        return "no_aligned_evidence"
    real_aligned = [
        ev for ev in aligned
        if not _is_fallback_evidence_id(str(ev.get("evidence_id") or ""))
    ]
    if not real_aligned:
        return "fallback_evidence_only"
    strong_present = any(
        str(ev.get("strength") or "").lower() == "strong"
        and str(ev.get("stance") or "").lower() in {"supports", "contradicts"}
        for ev in real_aligned
    )
    if strong_present:
        return "grounded_evidence"
    return "weak_evidence"


def _tqc_conflict_strength_label(state: Dict[str, Any], target_claim_ids: Sequence[str]) -> str:
    targets = _normalize_target_claim_ids(target_claim_ids)
    real_targets = [c for c in targets if not _is_fallback_claim_id(c)]
    risks = evidence_risk_signals(state)
    contradictory = int(risks.get("contradictory_evidence", 0) or 0)
    weak_missing = int(risks.get("weak_or_missing_evidence", 0) or 0)
    has_conflict_notes = bool(state.get("conflict_notes"))
    if not real_targets:
        if has_conflict_notes:
            return "unresolved_but_ungrounded"
        return "weak_conflict"
    strongest = max(
        (_claim_contradiction_strength(state, c) for c in real_targets),
        default=0,
    )
    if strongest >= 2 and contradictory > 0:
        return "strong_grounded_conflict"
    if strongest >= 1:
        return "weak_conflict"
    if weak_missing > 0:
        return "missing_evidence_only"
    if has_conflict_notes:
        return "unresolved_but_ungrounded"
    return "weak_conflict"


def _tqc_recovery_readiness(
    target_source: str,
    target_width: str,
    evidence_grounding: str,
    conflict_strength: str,
) -> tuple[str, List[str]]:
    reasons: List[str] = []
    if target_source == "empty_or_unknown":
        reasons.append("empty_or_unknown_target")
    elif target_source == "fallback_claim":
        reasons.append("fallback_only_target")
    elif target_source == "mixed_real_and_fallback":
        reasons.append("mixed_fallback_target")
    if target_width == "broad_target_set":
        reasons.append("broad_target")
    if evidence_grounding == "no_aligned_evidence":
        reasons.append("no_aligned_evidence")
    elif evidence_grounding == "fallback_evidence_only":
        reasons.append("fallback_evidence_only")
    elif evidence_grounding == "weak_evidence":
        reasons.append("weak_evidence")
    if conflict_strength == "missing_evidence_only":
        reasons.append("missing_evidence_only")
    elif conflict_strength == "weak_conflict":
        reasons.append("weak_conflict")
    elif conflict_strength == "unresolved_but_ungrounded":
        reasons.append("ungrounded_conflict")

    if target_source == "empty_or_unknown" or evidence_grounding == "no_aligned_evidence":
        label = "not_ready_for_recovery"
    elif target_source == "fallback_claim":
        label = "fallback_bridge_only"
    elif target_width == "broad_target_set":
        label = "needs_target_refinement"
    elif evidence_grounding in {"fallback_evidence_only", "weak_evidence"}:
        label = "needs_evidence_grounding"
    elif conflict_strength in {"weak_conflict", "missing_evidence_only", "unresolved_but_ungrounded"}:
        label = "needs_evidence_grounding"
    elif (
        target_source == "real_claim"
        and target_width in {"single_target", "small_target_set"}
        and evidence_grounding == "grounded_evidence"
        and conflict_strength == "strong_grounded_conflict"
    ):
        label = "ready_for_aggressive_recovery"
        reasons.append("ready")
    else:
        label = "needs_evidence_grounding"
    return label, reasons


def target_quality_certificate(
    state: Dict[str, Any],
    payload: Dict[str, Any],
    recent_turn_logs: Optional[Sequence[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Compute Target Quality Certificate over the final (post-sanitize) target.

    Observability-only: callers use the returned fields for diagnostic labeling
    of each turn, not for action selection.
    """
    targets = _normalize_target_claim_ids(
        payload.get("final_action_target_claim_ids")
        or payload.get("target_claim_ids")
        or []
    )
    target_source = _tqc_target_source_label(targets)
    target_width = _tqc_target_width_label(targets)
    evidence_grounding = _tqc_evidence_grounding_label(state, targets)
    conflict_strength = _tqc_conflict_strength_label(state, targets)
    readiness_label, readiness_reasons = _tqc_recovery_readiness(
        target_source, target_width, evidence_grounding, conflict_strength
    )
    return {
        "tqc_target_source": target_source,
        "tqc_target_width": target_width,
        "tqc_evidence_grounding": evidence_grounding,
        "tqc_conflict_strength": conflict_strength,
        "recovery_readiness_label": readiness_label,
        "recovery_readiness_reasons": readiness_reasons,
    }


def _recovery_push_reasons(state: Dict[str, Any], target_claim_ids: Sequence[str], action_type: str, policy_source: str) -> List[str]:
    reasons: List[str] = []
    _, quality_reasons = _target_quality(state, target_claim_ids, action_type)
    for reason in quality_reasons:
        if reason in {"broad_target", "fallback_target", "weak_target"} and reason not in reasons:
            reasons.append(reason)
    risk = state.get("risk_profile", {}) or {}
    evidence_risks = evidence_risk_signals(state)
    if int(risk.get("conflict_count", 0) or 0) > 0:
        reasons.append("unresolved_conflict")
    if evidence_risks.get("weak_or_missing_evidence", 0) > 0:
        reasons.append("missing_evidence")
    if evidence_risks.get("contradictory_evidence", 0) > 0:
        reasons.append("contradiction_present")
    if "fallback" in str(policy_source or ""):
        reasons.append("policy_fallback")
    return list(dict.fromkeys(reasons))


def _claim_has_prompt_leakage(state: Dict[str, Any], claim_id: str) -> bool:
    if not claim_id:
        return False
    for claim in state.get("claims", []) or []:
        if claim.get("claim_id") != claim_id:
            continue
        claim_text = str(claim.get("claim") or "").strip().lower()
        if not claim_text:
            return True
        return any(marker in claim_text for marker in _PROMPT_LEAK_MARKERS)
    return False


def _claim_contradiction_strength(
    state: Dict[str, Any],
    claim_id: str,
    recent_turn_logs: Optional[Sequence[Dict[str, Any]]] = None,
) -> int:
    if not claim_id:
        return 0
    score = 0
    claim_evidence_ids = set()
    for evidence in state.get("evidence_map", []) or []:
        if evidence.get("claim_id") != claim_id:
            continue
        evidence_id = str(evidence.get("evidence_id") or "").strip()
        if evidence_id:
            claim_evidence_ids.add(evidence_id)
        if evidence.get("stance") in {"contradicts", "missing"}:
            score += 2 if evidence.get("strength") == "strong" else 1
    for note in state.get("conflict_notes", []) or []:
        note_claim_id = str(note.get("claim_id") or "").strip()
        note_evidence_id = str(note.get("evidence_id") or "").strip()
        if note_claim_id == claim_id or (note_evidence_id and note_evidence_id in claim_evidence_ids):
            score += 1
    latest_turn = list(recent_turn_logs or [])[-1] if recent_turn_logs else {}
    if str(latest_turn.get("recovery_failure_code") or "") == "BLOCKED_BY_POLICY":
        target_ids = {
            str(item.get("target_id") or "").split(":")[-1]
            for item in (latest_turn.get("recovery_details") or [])
        }
        if claim_id in target_ids:
            score += 1
    return score


def _claim_is_sticky_eligible(state: Dict[str, Any], claim_id: str) -> bool:
    if not claim_id or _is_fallback_claim_id(claim_id) or _claim_has_prompt_leakage(state, claim_id):
        return False
    for claim in state.get("claims", []) or []:
        if claim.get("claim_id") == claim_id:
            return str(claim.get("status") or "").strip().lower() in _RECOVERY_ELIGIBLE_CLAIM_STATUSES
    return False


def _claim_was_recent_recovery_target(recent_turn_logs: Optional[Sequence[Dict[str, Any]]], claim_id: str) -> bool:
    if not claim_id or not recent_turn_logs:
        return False
    latest_turn = list(recent_turn_logs)[-1]
    action_type = str(latest_turn.get("effective_action_type") or latest_turn.get("action_type") or "")
    target_claim_ids = {str(item).strip() for item in (latest_turn.get("target_claim_ids") or []) if str(item).strip()}
    return action_type in RECOVERY_ACTION_TYPES and claim_id in target_claim_ids


def _claim_has_recent_blocked_recovery(recent_turn_logs: Optional[Sequence[Dict[str, Any]]], claim_id: str) -> bool:
    if not claim_id or not recent_turn_logs:
        return False
    latest_turn = list(recent_turn_logs)[-1]
    action_type = str(latest_turn.get("effective_action_type") or latest_turn.get("action_type") or "")
    target_claim_ids = {str(item).strip() for item in (latest_turn.get("target_claim_ids") or []) if str(item).strip()}
    return (
        action_type in RECOVERY_ACTION_TYPES
        and latest_turn.get("recovery_failure_code") == "BLOCKED_BY_POLICY"
        and claim_id in target_claim_ids
    )


def _select_sticky_creation_target(
    state: Dict[str, Any],
    target_claim_ids: Sequence[str],
    recent_turn_logs: Optional[Sequence[Dict[str, Any]]] = None,
    *,
    action_type: str = "",
) -> str:
    normalized_targets = _normalize_target_claim_ids(target_claim_ids)
    if action_type != "challenge_previous_hypothesis" or len(normalized_targets) < 2:
        return ""
    candidates = []
    for claim_id in normalized_targets:
        if not _claim_is_sticky_eligible(state, claim_id):
            continue
        contradiction_strength = _claim_contradiction_strength(state, claim_id, recent_turn_logs)
        if contradiction_strength < 2:
            continue
        if not (
            _claim_has_recent_blocked_recovery(recent_turn_logs, claim_id)
            or _claim_was_recent_recovery_target(recent_turn_logs, claim_id)
        ):
            continue
        candidates.append((claim_id, contradiction_strength))
    if not candidates:
        return ""
    strongest = max(score for _, score in candidates)
    strongest_ids = [claim_id for claim_id, score in candidates if score == strongest]
    if len(strongest_ids) != 1:
        return ""
    return strongest_ids[0]


def _should_create_sticky_target(
    state: Dict[str, Any],
    claim_id: str,
    target_claim_ids: Sequence[str],
    recent_turn_logs: Optional[Sequence[Dict[str, Any]]] = None,
    *,
    action_type: str = "",
) -> bool:
    if not claim_id:
        return False
    return claim_id == _select_sticky_creation_target(
        state,
        target_claim_ids,
        recent_turn_logs,
        action_type=action_type,
    )


def _apply_target_sticky_payload(
    state: Dict[str, Any],
    payload: Dict[str, Any],
    recent_turn_logs: Optional[Sequence[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    updated = dict(payload)
    updated["sticky_target_applied"] = False
    updated["sticky_target_reused"] = False
    updated["sticky_target_released"] = False
    updated["target_switch_blocked_by_sticky"] = False
    updated.setdefault("sticky_release_reason", "")

    phase = (
        _normalize_recovery_phase(updated.get("phase"))
        or _normalize_recovery_phase(state.get("phase"))
        or ("recovery" if str(updated.get("action_type") or "") in RECOVERY_ACTION_TYPES else "normal_review")
    )
    if phase != "recovery":
        if state.get("sticky_target_id"):
            updated["sticky_target_released"] = True
            updated["sticky_release_reason"] = updated.get("sticky_release_reason") or "phase_exit"
        updated["sticky_target_id"] = ""
        updated["sticky_target_type"] = ""
        updated["sticky_target_active"] = False
        updated["sticky_target_turns_remaining"] = 0
        return updated

    action_type = str(updated.get("action_type") or "")
    target_claim_ids = _normalize_target_claim_ids(updated.get("target_claim_ids", []))
    desired_target_id = target_claim_ids[0] if target_claim_ids else ""
    sticky_candidate_id = _select_sticky_creation_target(
        state,
        target_claim_ids,
        recent_turn_logs,
        action_type=action_type,
    )
    desired_strength = _claim_contradiction_strength(state, desired_target_id, recent_turn_logs) if desired_target_id else 0
    sticky_candidate_strength = _claim_contradiction_strength(state, sticky_candidate_id, recent_turn_logs) if sticky_candidate_id else 0

    sticky_target_id = str(state.get("sticky_target_id") or "")
    sticky_target_type = str(state.get("sticky_target_type") or "") or "claim"
    sticky_turns_remaining = max(0, int(state.get("sticky_target_turns_remaining", 0) or 0))
    sticky_active = bool(
        sticky_target_id
        and sticky_target_type == "claim"
        and sticky_turns_remaining > 0
        and _claim_is_sticky_eligible(state, sticky_target_id)
    )
    sticky_strength = _claim_contradiction_strength(state, sticky_target_id, recent_turn_logs) if sticky_active else 0

    if sticky_active:
        updated["sticky_target_id"] = sticky_target_id
        updated["sticky_target_type"] = sticky_target_type
        updated["sticky_target_active"] = True
        updated["sticky_target_turns_remaining"] = sticky_turns_remaining
        if not _is_recovery_continuation_action(action_type):
            return updated
        if sticky_candidate_id and sticky_candidate_id != sticky_target_id and sticky_candidate_strength > sticky_strength:
            updated["sticky_target_released"] = True
            updated["sticky_release_reason"] = "stronger_counterevidence"
            updated["sticky_target_id"] = sticky_candidate_id
            updated["sticky_target_type"] = "claim"
            updated["sticky_target_active"] = _claim_is_sticky_eligible(state, sticky_candidate_id)
            updated["sticky_target_turns_remaining"] = 1 if updated["sticky_target_active"] else 0
            biased_claim_ids, applied, blocked_switch = _apply_sticky_target_bias(
                target_claim_ids,
                sticky_candidate_id,
            )
            updated["target_claim_ids"] = biased_claim_ids
            updated["sticky_target_applied"] = applied and updated["sticky_target_active"]
            updated["sticky_target_reused"] = False
            updated["target_switch_blocked_by_sticky"] = blocked_switch
            return updated
        biased_claim_ids, applied, blocked_switch = _apply_sticky_target_bias(
            target_claim_ids,
            sticky_target_id,
        )
        updated["target_claim_ids"] = biased_claim_ids
        updated["sticky_target_applied"] = applied
        updated["sticky_target_reused"] = applied
        updated["target_switch_blocked_by_sticky"] = blocked_switch
        sticky_turns_remaining -= 1
        updated["sticky_target_turns_remaining"] = max(0, sticky_turns_remaining)
        if sticky_turns_remaining <= 0:
            updated["sticky_target_released"] = True
            updated["sticky_release_reason"] = updated.get("sticky_release_reason") or "forced_release"
            updated["sticky_target_active"] = False
        return updated

    if sticky_candidate_id:
        updated["sticky_target_id"] = sticky_candidate_id
        updated["sticky_target_type"] = "claim"
        updated["sticky_target_active"] = True
        updated["sticky_target_reused"] = False
        updated["sticky_target_released"] = False
        updated["sticky_release_reason"] = ""
        updated["sticky_target_turns_remaining"] = 1
        biased_claim_ids, applied, blocked_switch = _apply_sticky_target_bias(
            target_claim_ids,
            sticky_candidate_id,
        )
        updated["target_claim_ids"] = biased_claim_ids
        updated["sticky_target_applied"] = applied
        updated["target_switch_blocked_by_sticky"] = blocked_switch
        return updated

    updated["sticky_target_id"] = ""
    updated["sticky_target_type"] = ""
    updated["sticky_target_active"] = False
    updated["sticky_target_turns_remaining"] = 0
    return updated


def infer_action_from_state(mode: str, state: Dict[str, Any], recent_turn_logs: Optional[Sequence[Dict[str, Any]]] = None) -> Dict[str, Any]:
    counts = state_counts(state)
    risk = state.get("risk_profile", {}) or {}
    claims = state.get("claims", [])
    flaws = state.get("flaw_candidates", [])
    conflict_count = int(risk.get("conflict_count", 0) or 0)
    open_questions = int(risk.get("open_question_count", 0) or 0)
    readiness = str(risk.get("readiness") or "not_ready")
    evidence_gaps = _open_evidence_gaps(state)
    hypotheses = state.get("current_hypotheses", [])
    evidence_risks = evidence_risk_signals(state)
    weak_or_missing_evidence = evidence_risks["weak_or_missing_evidence"]
    contradictory_evidence = evidence_risks["contradictory_evidence"]
    recent_turn_logs = list(recent_turn_logs or [])
    recent_focuses = [item.get("focus", "") for item in recent_turn_logs[-2:] if item.get("focus")]
    recent_actions = [item.get("action_type", "") for item in recent_turn_logs[-2:] if item.get("action_type")]
    stalled_focus = len(recent_focuses) >= 2 and len(set(recent_focuses)) == 1
    repeated_action = len(recent_actions) >= 2 and len(set(recent_actions)) == 1

    if counts["claims"] == 0:
        return {"action_type": "extract_claims", "focus": "Identify the paper's core claims.", "rationale": "No structured claims exist yet.", "target_claim_ids": []}
    claim_expansion = _claim_coverage_expansion_plan(state, recent_turn_logs)
    if mode == "s4" and claim_expansion["required"] and "extract_claims" in mode_allowed_actions(mode):
        return {
            "action_type": "extract_claims",
            "focus": "Expand claim coverage with method, empirical, and limitation-sensitive claims before evidence binding.",
            "rationale": "The first claim pass is too narrow for robust evidence and critique binding.",
            "target_claim_ids": claim_expansion["target_claim_ids"],
            "claim_coverage_expansion_required": True,
            "claim_coverage_missing_tags": claim_expansion["missing_tags"],
        }
    if mode == "s4" and state.get("clarification_needed") and state.get("pending_user_question"):
        return {"action_type": "ask_user_clarification", "focus": state.get("pending_user_question", "Clarify the review target."), "rationale": "The state already indicates clarification is needed."}
    negative_retry_targets = _negative_evidence_binding_retry_targets(state, recent_turn_logs)
    if negative_retry_targets["target_evidence_ids"] and "analyze_flaws" in mode_allowed_actions(mode):
        return {
            "action_type": "analyze_flaws",
            "focus": "Bind unlinked negative evidence to a grounded flaw or explicitly downgrade it.",
            "rationale": "Paper-level negative evidence exists but is not yet linked to a valid flaw candidate.",
            "target_claim_ids": negative_retry_targets["target_claim_ids"],
            "target_evidence_ids": negative_retry_targets["target_evidence_ids"],
        }
    if conflict_count > 0 and hypotheses:
        return {"action_type": "challenge_previous_hypothesis", "focus": "Recheck earlier hypotheses against conflicting evidence.", "rationale": "Conflicts and active hypotheses indicate possible misjudgment.", "target_hypotheses": hypotheses[:3], "target_claim_ids": _claim_ids_by_status(claims, include=_RECOVERY_ELIGIBLE_CLAIM_STATUSES, limit=2)}
    if contradictory_evidence > 0 and counts["evidence_map"] > 0:
        return {"action_type": "challenge_previous_hypothesis", "focus": "Challenge the current conclusion against contradictory evidence.", "rationale": "Contradictory evidence should test whether earlier hypotheses or flaw judgments are too strong.", "target_claim_ids": _claim_ids_by_status(claims, include=_RECOVERY_ELIGIBLE_CLAIM_STATUSES, limit=2), "target_hypotheses": hypotheses[:3]}
    if counts["evidence_map"] == 0 or evidence_gaps:
        return {"action_type": "verify_evidence", "focus": "Ground the main claims in concrete evidence.", "rationale": "Claims exist but evidence grounding is incomplete.", "target_claim_ids": _claim_ids_by_status(claims, exclude=_INACTIVE_CLAIM_STATUSES, limit=2)}
    if weak_or_missing_evidence > 0 and open_questions >= 1:
        return {"action_type": "request_evidence_recheck", "focus": "Recheck the weakest or missing evidence supporting the current claims.", "rationale": "Weak or missing evidence remains in the state and should be revisited before trusting the current conclusion.", "target_claim_ids": _claim_ids_by_status(claims, exclude=_INACTIVE_CLAIM_STATUSES, limit=2)}
    active_flaws = [flaw for flaw in flaws if flaw.get("status") not in {"retracted", "downgraded"}]
    if not active_flaws:
        return {"action_type": "analyze_flaws", "focus": "Identify the strongest grounded weaknesses.", "rationale": "Evidence exists but grounded flaw analysis is still missing.", "target_claim_ids": _claim_ids_by_status(claims, exclude=_INACTIVE_CLAIM_STATUSES, limit=2)}
    unverified_flaw_ids = _active_unverified_flaw_ids(state, limit=2)
    if mode == "s4" and unverified_flaw_ids and not _has_prior_recovery_action(recent_turn_logs):
        return {
            "action_type": "challenge_previous_hypothesis",
            "focus": "Verify or downgrade active flaw candidates that lack verified negative evidence before final reporting.",
            "rationale": "Candidate flaws without verified negative evidence should not survive directly into final-view reporting.",
            "target_claim_ids": _claim_ids_by_status(claims, include=_RECOVERY_ELIGIBLE_CLAIM_STATUSES, limit=2),
            "target_flaw_ids": unverified_flaw_ids,
        }
    if open_questions >= 3:
        return {"action_type": "request_evidence_recheck", "focus": "Resolve the most blocking open questions with targeted evidence recheck.", "rationale": "Several unresolved questions remain after the initial pass.", "target_claim_ids": _claim_ids_by_status(claims, exclude=_INACTIVE_CLAIM_STATUSES, limit=2)}
    if stalled_focus or repeated_action:
        return {"action_type": "summarize_progress", "focus": "Summarize where the review is stalled before the next move.", "rationale": "Recent turns repeated the same focus or action without enough progress."}
    if readiness == "ready_to_finalize":
        return {"action_type": "finalize", "focus": "Convert the structured state into the final recommendation.", "rationale": "The risk profile indicates the state is coherent enough to finalize."}
    return {"action_type": "summarize_progress", "focus": "Summarize the current structured review progress before the next step.", "rationale": "The review state exists but needs consolidation before the next action."}


def infer_effective_action_type(manager_payload: Dict[str, Any], worker_payloads: List[Dict[str, Any]]) -> str:
    for worker in worker_payloads:
        payload = worker.get("payload", {}) or {}
        if payload.get("flaw_candidates"):
            return "analyze_flaws"
    for worker in worker_payloads:
        payload = worker.get("payload", {}) or {}
        if payload.get("evidence_map"):
            return "verify_evidence"
    for worker in worker_payloads:
        payload = worker.get("payload", {}) or {}
        if payload.get("claims"):
            return "extract_claims"
    return manager_payload.get("effective_action_type") or manager_payload.get("action_type") or "extract_claims"


def state_is_complete(mode: str, state: Dict[str, Any], manager_payload: Dict[str, Any], worker_payloads: List[Dict[str, Any]]) -> bool:
    requirements = MIN_STATE_REQUIREMENTS.get(mode, MIN_STATE_REQUIREMENTS["s4"])
    counts = state_counts(state)
    manager_counts = payload_counts(manager_payload)
    for worker in worker_payloads:
        worker_counts = payload_counts(worker["payload"])
        for key, value in worker_counts.items():
            counts[key] += value
    for key, min_value in requirements.items():
        counts[key] += manager_counts.get(key, 0)
        if counts.get(key, 0) < min_value:
            return False
    return True


def default_manager_payload(error: str = "") -> Dict[str, Any]:
    return {
        "decision": "continue",
        "action_type": "extract_claims",
        "selected_agents": [],
        "focus": "",
        "rationale": error[:600],
        "target_claim_ids": [],
        "target_flaw_ids": [],
        "target_evidence_ids": [],
        "target_hypotheses": [],
        "requires_clarification": False,
        "clarification_question": "",
        "summary_update": "",
        "dialogue_summary": "",
        "unresolved_questions": [],
        "claims": [],
        "evidence_map": [],
        "flaw_candidates": [],
        "recommendation": "undecided",
        "final_decision": "undecided",
        "final_report": "",
    }


def build_auto_finalize_payload(
    manager_payload: Dict[str, Any],
    selected_workers: List[str],
    mode: str,
    step: int,
    worker_payloads: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    finalized = dict(manager_payload)
    finalized["effective_action_type"] = infer_effective_action_type(finalized, worker_payloads or [])
    finalized["auto_finalized"] = True
    finalized["decision"] = "finalize"
    finalized["action_type"] = "finalize"
    finalized["selected_agents"] = []
    finalized["final_decision"] = finalized.get("final_decision") or finalized.get("recommendation") or "undecided"
    finalized["rationale"] = (
        ((finalized.get("rationale") or "").strip() + " ").strip()
        + f"Auto-finalized because the structured review state met the minimum completeness threshold for {mode} at turn {step}."
    )[:600]
    if not finalized.get("focus"):
        finalized["focus"] = "Summarize the structured review state into the final recommendation."
    return finalized


def resolve_result_final_decision(review_state: Dict[str, Any], final_report: str) -> str:
    has_structured_state = any(
        (review_state or {}).get(key)
        for key in ("claims", "evidence_map", "flaw_candidates", "unresolved_questions", "conflict_notes")
    )
    if has_structured_state:
        inferred = infer_final_decision(review_state or {}, {})
        if inferred in {"accept", "reject"}:
            return inferred

    # Fall back to textual or stored decisions only when there is no substantive
    # structured state. This prevents stale default rejects from overriding real
    # evidence accumulated in ReviewState while keeping empty-state reports sane.
    report_decision = _extract_decision(final_report or "")
    if report_decision in {"accept", "reject", "neutral"}:
        return "undecided" if report_decision == "neutral" else report_decision

    state_decision = str((review_state or {}).get("final_decision") or "").strip().lower()
    if state_decision in {"accept", "reject", "undecided"}:
        return state_decision
    return "undecided"


def apply_finalize_policy(
    manager_payload: Dict[str, Any],
    state: Dict[str, Any],
    mode: str,
    step: int,
    turn_cap: int,
    worker_ids: Sequence[str],
    worker_limit: int,
    selected_workers: List[str],
    worker_payloads: List[Dict[str, Any]],
    recent_turn_logs: Optional[Sequence[Dict[str, Any]]] = None,
) -> tuple[Dict[str, Any], List[str]]:
    payload = dict(manager_payload)
    explicit_finalize_output = bool(
        payload.get("final_report")
        and payload.get("final_decision") in {"accept", "reject", "undecided"}
        and (
            mode == "s1"
            or any(payload_counts(payload).values())
            or any(state_counts(state).values())
            or payload.get("requires_clarification")
            or payload.get("pending_user_question")
        )
    )
    if payload.get("decision") == "finalize" and not explicit_finalize_output and not state_is_complete(mode, state, payload, worker_payloads):
        payload["decision"] = "continue"
        payload["action_type"] = payload.get("action_type") if payload.get("action_type") != "finalize" else infer_action_from_state(mode, state, recent_turn_logs=recent_turn_logs).get("action_type", "verify_evidence")
        payload["final_decision"] = "undecided"
        payload["final_report"] = ""
        payload["policy_source"] = "finalize_guard_override"
        payload["policy_notes"] = list(dict.fromkeys(payload.get("policy_notes", []) + ["Finalize was overridden because the structured review state was incomplete."]))[:8]
        if not worker_ids:
            payload["unresolved_questions"] = list(
                dict.fromkeys(
                    payload.get("unresolved_questions", [])
                    + ["The structured review state is still incomplete; continue gathering claims, evidence, or flaws."]
                )
            )[:10]
        else:
            payload["selected_agents"] = pick_workers_for_action(payload["action_type"], worker_ids, worker_limit) or list(worker_ids[:worker_limit])
        payload["rationale"] = (
            (payload.get("rationale", "") + " ").strip()
            + "Finalize was overridden because the structured review state is incomplete."
        )[:600]
        if not payload.get("focus"):
            payload["focus"] = "Fill the missing structured review slots before finalizing."
        return payload, list(payload.get("selected_agents", []))

    if payload.get("decision") != "finalize":
        if payload.get("support_formation_pass_triggered"):
            payload["decision"] = "continue"
            payload["action_type"] = "verify_evidence"
            payload["effective_action_type"] = "verify_evidence"
            payload["turn_mode"] = "normal_evidence"
            payload["phase"] = "normal_review"
            payload["final_decision"] = "undecided"
            payload["final_report"] = ""
            payload["selected_agents"] = pick_workers_for_action("verify_evidence", worker_ids, worker_limit) or list(worker_ids[:worker_limit])
            policy_notes = list(payload.get("policy_notes", []))
            policy_notes.append("Auto-finalize/conflict-block was bypassed because support_formation_pass_triggered requires one normal evidence verification turn.")
            payload["policy_notes"] = list(dict.fromkeys(policy_notes))[:8]
            payload["policy_source"] = "support_formation_override"
            return payload, list(payload.get("selected_agents", []))

        auto_finalize_turn = AUTO_FINALIZE_MIN_TURNS.get(mode, max(1, turn_cap - 1))
        recent_logs = list(recent_turn_logs or [])
        if mode == "s4" and any(turn.get("support_formation_pass_triggered") for turn in recent_logs):
            # Support formation consumes an extra evidence turn. Without this
            # budget compensation, S4 often follows claim -> evidence -> support
            # evidence -> flaw and then auto-finalizes at turn 4 before recovery
            # or consolidation can run. Delay auto-finalize by one turn only.
            auto_finalize_turn = min(turn_cap, auto_finalize_turn + 1)
        auto_finalize_blocked_actions = {"ask_user_clarification", "request_evidence_recheck", "challenge_previous_hypothesis"}
        has_flaw_progress = any((worker.get("payload", {}) or {}).get("flaw_candidates") for worker in worker_payloads)
        unverified_flaw_ids = _active_unverified_flaw_ids(state, limit=2)

        # --- Component B: conflict-block ---
        # In S4, block auto-finalize when unresolved conflicts exist and no
        # recovery action has been taken yet, as long as there is at least one
        # remaining turn to attempt recovery.
        conflict_count = len(state.get("conflict_notes", []))
        recent_logs = list(recent_turn_logs or [])
        has_recovery = _has_prior_recovery_action(recent_logs)
        conflict_block = (
            mode == "s4"
            and conflict_count > 0
            and not has_recovery
            and step < turn_cap
        )
        flaw_lifecycle_block = (
            mode == "s4"
            and bool(unverified_flaw_ids)
            and not has_recovery
            and step < turn_cap
        )

        if (
            payload.get("action_type") not in auto_finalize_blocked_actions
            and (state_is_complete(mode, state, payload, worker_payloads) or (mode == "s4" and has_flaw_progress))
            and (step >= auto_finalize_turn or step >= turn_cap)
        ):
            if conflict_block:
                negative_targets = _unverified_flaw_negative_evidence_targets(state, recent_logs)
                if negative_targets["target_flaw_ids"]:
                    recovery_action = "request_evidence_recheck"
                    payload["decision"] = "continue"
                    payload["action_type"] = recovery_action
                    payload["effective_action_type"] = recovery_action
                    payload["target_flaw_ids"] = negative_targets["target_flaw_ids"]
                    payload["target_claim_ids"] = negative_targets["target_claim_ids"] or payload.get("target_claim_ids") or _fallback_negative_evidence_claim_ids(state, limit=2)
                    payload["target_evidence_ids"] = negative_targets["target_evidence_ids"]
                    payload["negative_evidence_formation_required"] = True
                    payload["final_decision"] = "undecided"
                    payload["final_report"] = ""
                    payload["policy_source"] = "negative_evidence_formation_override"
                    policy_notes = list(payload.get("policy_notes", []))
                    policy_notes.append(
                        f"Auto-finalize was blocked because {conflict_count} unresolved conflict(s) exist and active flaws lack verified negative evidence."
                    )
                    policy_notes.append("S4 requests verified negative evidence before challenge/recovery patch mode.")
                    payload["policy_notes"] = list(dict.fromkeys(policy_notes))[:8]
                    payload["rationale"] = (
                        (payload.get("rationale", "") + " ").strip()
                        + "Finalize was blocked to ground the active flaw in paper negative evidence before recovery."
                    )[:600]
                    payload["focus"] = "Find paper-grounded negative evidence for active flaw candidates before recovery."
                    payload["selected_agents"] = pick_workers_for_action(recovery_action, worker_ids, worker_limit) or list(worker_ids[:worker_limit])
                    return payload, list(payload.get("selected_agents", []))

                # Redirect to a recovery action instead of auto-finalizing.
                recovery_action = _choose_recovery_action(state)
                payload["decision"] = "continue"
                payload["action_type"] = recovery_action
                payload["effective_action_type"] = recovery_action
                payload["final_decision"] = "undecided"
                payload["final_report"] = ""
                payload["policy_source"] = "conflict_block_override"
                policy_notes = list(payload.get("policy_notes", []))
                policy_notes.append(
                    f"Auto-finalize was blocked because {conflict_count} unresolved conflict(s) exist and no recovery action has been taken yet."
                )
                payload["policy_notes"] = list(dict.fromkeys(policy_notes))[:8]
                payload["rationale"] = (
                    (payload.get("rationale", "") + " ").strip()
                    + f"Finalize was blocked to allow a recovery action for {conflict_count} unresolved conflict(s)."
                )[:600]
                if not payload.get("focus"):
                    payload["focus"] = "Address unresolved conflicts before finalizing the review."
                payload["selected_agents"] = pick_workers_for_action(recovery_action, worker_ids, worker_limit) or list(worker_ids[:worker_limit])
                return payload, list(payload.get("selected_agents", []))

            if flaw_lifecycle_block:
                negative_targets = _unverified_flaw_negative_evidence_targets(state, recent_logs)
                fallback_target_claim_ids = payload.get("target_claim_ids") or _fallback_negative_evidence_claim_ids(state, limit=2)
                can_form_negative_evidence = bool(negative_targets["target_flaw_ids"] or fallback_target_claim_ids)
                recovery_action = "request_evidence_recheck" if can_form_negative_evidence else "challenge_previous_hypothesis"
                payload["decision"] = "continue"
                payload["action_type"] = recovery_action
                payload["effective_action_type"] = recovery_action
                payload["target_flaw_ids"] = negative_targets["target_flaw_ids"] or unverified_flaw_ids
                payload["target_claim_ids"] = negative_targets["target_claim_ids"] or fallback_target_claim_ids
                payload["target_evidence_ids"] = negative_targets["target_evidence_ids"]
                if can_form_negative_evidence:
                    payload["negative_evidence_formation_required"] = True
                payload["final_decision"] = "undecided"
                payload["final_report"] = ""
                payload["policy_source"] = "negative_evidence_formation_override" if can_form_negative_evidence else "flaw_lifecycle_block_override"
                policy_notes = list(payload.get("policy_notes", []))
                policy_notes.append(
                    "Auto-finalize was blocked because active flaw candidates lack verified negative evidence."
                )
                if negative_targets["target_flaw_ids"]:
                    policy_notes.append(
                        "S4 requests verified negative evidence for the active flaw before challenge/recovery patch mode."
                    )
                payload["policy_notes"] = list(dict.fromkeys(policy_notes))[:8]
                payload["rationale"] = (
                    (payload.get("rationale", "") + " ").strip()
                    + "Finalize was blocked to verify or downgrade ungrounded flaw candidates."
                )[:600]
                payload["focus"] = "Find paper-grounded negative evidence for active flaw candidates before final reporting."
                payload["selected_agents"] = pick_workers_for_action(recovery_action, worker_ids, worker_limit) or list(worker_ids[:worker_limit])
                return payload, list(payload.get("selected_agents", []))

            payload = build_auto_finalize_payload(
                manager_payload=payload,
                selected_workers=selected_workers,
                mode=mode,
                step=step,
                worker_payloads=worker_payloads,
            )
            return payload, []

    return payload, list(selected_workers)


def apply_manager_policy_fallback(
    manager_payload: Dict[str, Any],
    state: Dict[str, Any],
    mode: str,
    worker_ids: Sequence[str],
    worker_limit: int,
    recent_turn_logs: Optional[Sequence[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    payload = dict(manager_payload)
    policy_notes = list(payload.get("policy_notes", []))
    policy_source = payload.get("policy_source") or "manager_model"
    inferred = infer_action_from_state(mode, state, recent_turn_logs=recent_turn_logs)
    raw_target_claim_ids = _normalize_target_claim_ids(inferred.get("target_claim_ids", []))
    payload["raw_target_claim_ids"] = list(raw_target_claim_ids)
    payload["raw_target_count"] = len(raw_target_claim_ids)
    payload["raw_target_is_broad"] = _target_is_broad(raw_target_claim_ids)
    allowed_actions = mode_allowed_actions(mode)
    original_action_type = payload.get("action_type")
    action_type = original_action_type
    if action_type not in MANAGER_ACTION_TYPES:
        policy_source = "fallback_inference"
        policy_notes.append("Manager action_type was invalid and was replaced by inferred policy.")
        action_type = inferred["action_type"]
    elif action_type not in allowed_actions:
        policy_source = "mode_constraint_override"
        policy_notes.append(f"Action {action_type} is not allowed in mode {mode}; replacing it with a mode-compatible action.")
        action_type = inferred["action_type"]
    if action_type not in allowed_actions:
        policy_source = "mode_constraint_override"
        if "summarize_progress" in allowed_actions:
            action_type = "summarize_progress"
        else:
            action_type = "finalize" if "finalize" in allowed_actions else sorted(allowed_actions)[0]
    recent_turn_logs = list(recent_turn_logs or [])
    counts = state_counts(state)
    previous_action = recent_turn_logs[-1].get("action_type", "") if recent_turn_logs else ""
    previous_focus = recent_turn_logs[-1].get("focus", "") if recent_turn_logs else ""
    inferred_action = inferred.get("action_type", action_type)
    current_focus = payload.get("focus") or inferred.get("focus", "")
    if mode == "s3" and action_type == "ask_user_clarification" and counts["claims"] == 0:
        policy_source = "s3_preclaim_clarification_override"
        policy_notes.append("S3 does not enter clarification mode before any structured claims exist.")
        action_type = "extract_claims"
    if (
        mode == "s3"
        and action_type == "ask_user_clarification"
        and counts["claims"] > 0
        and (counts["evidence_map"] == 0 or _open_evidence_gaps(state))
        and "verify_evidence" in allowed_actions
    ):
        policy_source = "s3_clarification_override"
        policy_notes.append("S3 keeps the turn budget on internal evidence progress instead of entering clarification mode.")
        action_type = "verify_evidence"
    if (
        mode == "s3"
        and action_type == "extract_claims"
        and counts["claims"] > 0
        and counts["evidence_map"] == 0
        and "verify_evidence" in allowed_actions
    ):
        policy_source = "s3_claim_progress_override"
        policy_notes.append("S3 moves from repeated claim extraction to evidence verification once claims exist.")
        action_type = "verify_evidence"
    if mode == "s4" and action_type == "ask_user_clarification" and counts["claims"] == 0:
        policy_source = "s4_preclaim_clarification_override"
        policy_notes.append("S4 does not enter clarification mode before any structured claims exist.")
        action_type = "extract_claims"
    claim_expansion = _claim_coverage_expansion_plan(state, recent_turn_logs)
    if (
        mode == "s4"
        and claim_expansion["required"]
        and "extract_claims" in allowed_actions
        and action_type in {"extract_claims", "verify_evidence", "ask_user_clarification", "summarize_progress", "finalize", "analyze_flaws"}
    ):
        policy_source = "claim_coverage_expansion_override"
        policy_notes.append("S4 runs one targeted claim expansion pass because existing claims lack method, empirical, or limitation-sensitive coverage.")
        payload["decision"] = "continue"
        payload["final_decision"] = "undecided"
        payload["final_report"] = ""
        payload["claim_coverage_expansion_required"] = True
        payload["claim_coverage_missing_tags"] = claim_expansion["missing_tags"]
        payload["claim_coverage"] = claim_expansion["coverage"]
        action_type = "extract_claims"
    if (
        mode == "s4"
        and action_type == "ask_user_clarification"
        and counts["claims"] > 0
        and (counts["evidence_map"] == 0 or _open_evidence_gaps(state))
        and "verify_evidence" in allowed_actions
        and policy_source == "manager_model"
    ):
        policy_source = "s4_clarification_to_evidence_override"
        policy_notes.append("S4 keeps the turn budget on evidence grounding before asking for clarification.")
        action_type = "verify_evidence"
    hard_negative_claim_ids = _fallback_negative_evidence_claim_ids(state, limit=2)
    if (
        mode == "s4"
        and policy_source == "manager_model"
        and action_type in {"ask_user_clarification", "verify_evidence", "summarize_progress"}
        and counts["evidence_map"] > 0
        and counts["flaw_candidates"] == 0
        and "analyze_flaws" in allowed_actions
    ):
        policy_source = "s4_evidence_to_flaw_override"
        policy_notes.append("S4 moves from grounded evidence to flaw analysis before spending turns on clarification or summary.")
        action_type = "analyze_flaws"
    negative_retry_targets = _negative_evidence_binding_retry_targets(state, recent_turn_logs)
    if (
        mode == "s4"
        and negative_retry_targets["target_evidence_ids"]
        and "analyze_flaws" in allowed_actions
        and action_type in {"ask_user_clarification", "verify_evidence", "request_evidence_recheck", "summarize_progress", "finalize", "analyze_flaws"}
    ):
        policy_source = "negative_evidence_binding_retry_override"
        policy_notes.append("S4 routes unlinked paper-level negative evidence to Critique Agent for flaw binding or explicit downgrade.")
        payload["decision"] = "continue"
        payload["final_decision"] = "undecided"
        payload["final_report"] = ""
        action_type = "analyze_flaws"
        payload["target_claim_ids"] = negative_retry_targets["target_claim_ids"]
        payload["target_evidence_ids"] = negative_retry_targets["target_evidence_ids"]
        payload["negative_evidence_binding_retry_required"] = True
    verified_negative_flaw_review_targets = _verified_negative_flaw_review_targets(state, recent_turn_logs)
    if (
        mode == "s4"
        and policy_source in _HARD_NEGATIVE_DISCOVERY_ELIGIBLE_SOURCES.union({"manager_model"})
        and action_type in {"challenge_previous_hypothesis", "verify_evidence", "request_evidence_recheck", "summarize_progress", "finalize"}
        and verified_negative_flaw_review_targets["target_flaw_ids"]
        and "analyze_flaws" in allowed_actions
    ):
        policy_source = "negative_evidence_binding_retry_override"
        policy_notes.append("S4 routes verified actionable negative evidence to Critique Agent before recovery patch mode.")
        payload["decision"] = "continue"
        payload["final_decision"] = "undecided"
        payload["final_report"] = ""
        action_type = "analyze_flaws"
        payload["target_flaw_ids"] = verified_negative_flaw_review_targets["target_flaw_ids"]
        payload["target_claim_ids"] = verified_negative_flaw_review_targets["target_claim_ids"]
        payload["target_evidence_ids"] = verified_negative_flaw_review_targets["target_evidence_ids"]
        payload["negative_evidence_binding_retry_required"] = True

    negative_formation_targets = _unverified_flaw_negative_evidence_targets(state, recent_turn_logs)
    if (
        mode == "s4"
        and negative_formation_targets["target_flaw_ids"]
        and "request_evidence_recheck" in allowed_actions
        and action_type in {"ask_user_clarification", "verify_evidence", "request_evidence_recheck", "challenge_previous_hypothesis", "analyze_flaws", "summarize_progress", "finalize"}
    ):
        policy_source = "negative_evidence_formation_override"
        policy_notes.append("S4 asks Evidence Agent to form verified negative evidence for active flaws before entering recovery patch mode.")
        payload["decision"] = "continue"
        payload["final_decision"] = "undecided"
        payload["final_report"] = ""
        action_type = "request_evidence_recheck"
        payload["target_flaw_ids"] = negative_formation_targets["target_flaw_ids"]
        payload["target_claim_ids"] = negative_formation_targets["target_claim_ids"]
        payload["target_evidence_ids"] = negative_formation_targets["target_evidence_ids"]
        payload["negative_evidence_formation_required"] = True
        payload["focus"] = "Find paper-grounded negative evidence for active flaw candidates before recovery or final reporting."
    if (
        mode == "s4"
        and action_type in {"summarize_progress", "finalize"}
        and counts["evidence_map"] > 0
        and evidence_risk_signals(state)["weak_or_missing_evidence"] > 0
        and "request_evidence_recheck" in allowed_actions
    ):
        policy_source = "s4_recheck_override"
        policy_notes.append("S4 revisits weak or missing evidence before summary or finalization.")
        action_type = "request_evidence_recheck"
    if (
        mode == "s4"
        and action_type in {"summarize_progress", "finalize", "ask_user_clarification"}
        and evidence_risk_signals(state)["contradictory_evidence"] > 0
        and "challenge_previous_hypothesis" in allowed_actions
    ):
        policy_source = "s4_challenge_override"
        policy_notes.append("S4 challenges earlier hypotheses when contradictory evidence is already present.")
        action_type = "challenge_previous_hypothesis"
    if (
        policy_source == "manager_model"
        and action_type == "extract_claims"
        and counts["claims"] > 0
        and inferred_action in {"verify_evidence", "request_evidence_recheck", "analyze_flaws", "challenge_previous_hypothesis"}
        and inferred_action in allowed_actions
    ):
        policy_source = "evidence_progress_override"
        policy_notes.append("Claims already exist, so the policy moved beyond claim extraction to advance evidence or flaw analysis.")
        action_type = inferred_action
    _flaw_eligible_sources = {"manager_model", "evidence_progress_override", "s4_clarification_to_evidence_override"}
    if (
        policy_source in _flaw_eligible_sources
        and action_type == "verify_evidence"
        and counts["evidence_map"] > 0
        and counts["flaw_candidates"] == 0
        and previous_action == "verify_evidence"
        and "analyze_flaws" in allowed_actions
    ):
        policy_source = "flaw_progress_override"
        policy_notes.append("Evidence already exists and evidence verification repeated, so the policy moved to grounded flaw analysis.")
        action_type = "analyze_flaws"
    elif (
        policy_source in _flaw_eligible_sources
        and action_type == "verify_evidence"
        and counts["evidence_map"] > 0
        and counts["flaw_candidates"] == 0
        and inferred_action in {"analyze_flaws", "request_evidence_recheck", "challenge_previous_hypothesis"}
        and inferred_action in allowed_actions
    ):
        policy_source = "flaw_progress_override"
        policy_notes.append("Evidence already exists, so the policy moved beyond evidence verification to grounded flaw analysis or recheck.")
        action_type = inferred_action
    # Mainline-Final-Integrated P0-2: hard-negative discovery override.
    # Placed AFTER ``evidence_progress_override`` and ``flaw_progress_override``
    # so it can re-route turns where the manager would otherwise spend the
    # remaining budget on more verify/flaw work even though no grounded
    # negative evidence exists yet.  Placed BEFORE the conflict / recovery
    # overrides so an already-recovery-routed turn is not preempted.  The
    # eligible-source gate keeps it from preempting recovery itself.
    #
    # Mainline-Final-Integrated P0-2 budget-aware refinement: under
    # ``max_turns=4`` the previous (always-fire) gate took T3 for negative
    # discovery and T4 for the recovery commit, leaving only T2 for support
    # formation.  This collapsed ``real_strong_support_total`` from 37 to 14
    # on full39 with no decision improvement.  The refined gate consults
    # ``_phase_step`` / ``_phase_turn_cap`` (attached by the runner) to
    # detect tight-budget windows and skips the override when:
    #   - no follow-up turn remains for the recovery commit, or
    #   - the only remaining free turn would otherwise be the last chance
    #     to ground positive support and the paper has no positive support
    #     yet (``_positive_inventory_ready`` is False).
    # When ``_phase_step`` / ``_phase_turn_cap`` are not provided (older
    # callers / tests), the override falls back to the previous always-fire
    # behaviour to preserve compatibility.
    phase_step = int(payload.get("_phase_step") or 0)
    phase_turn_cap = int(payload.get("_phase_turn_cap") or 0)
    remaining_after_current = (phase_turn_cap - phase_step) if (phase_turn_cap and phase_step) else None
    budget_aware_skip = False
    if remaining_after_current is not None:
        if remaining_after_current < 1:
            budget_aware_skip = True
        elif remaining_after_current < 2 and not _positive_inventory_ready(state):
            budget_aware_skip = True
    if (
        mode == "s4"
        and policy_source in _HARD_NEGATIVE_DISCOVERY_ELIGIBLE_SOURCES
        and counts["claims"] > 0
        # Mainline-Final-Integrated P0-2: ``>=1`` matches the calibrated full39
        # turn budget (max_turns=4) where only the very last decide_manager
        # call ever sees ``evidence_map >= 2``; the gate stayed silent in the
        # calibrated rerun with the previous ``>=2`` threshold.  Requiring at
        # least one already-merged evidence item still prevents the override
        # from firing before any worker pass.
        and counts["evidence_map"] >= 1
        and _grounded_negative_evidence_count(state) == 0
        and hard_negative_claim_ids
        and not _has_recent_negative_evidence_formation_turn(recent_turn_logs)
        and "request_evidence_recheck" in allowed_actions
        and action_type in {"extract_claims", "verify_evidence", "request_evidence_recheck", "analyze_flaws", "summarize_progress", "finalize"}
        and not budget_aware_skip
    ):
        policy_source = "hard_negative_discovery_override"
        policy_notes.append("S4 runs one hard-negative discovery pass so reject evidence is not inferred only from unresolved/meta burden.")
        payload["decision"] = "continue"
        payload["final_decision"] = "undecided"
        payload["final_report"] = ""
        action_type = "request_evidence_recheck"
        payload["target_claim_ids"] = hard_negative_claim_ids
        payload["target_flaw_ids"] = []
        payload["target_evidence_ids"] = []
        payload["negative_evidence_formation_required"] = True
        payload["focus"] = "Search for copied paper quotes that weaken, limit, contradict, or show missing support for the strongest real claims; emit unresolved if no direct negative quote is visible."
    elif budget_aware_skip and not _has_recent_negative_evidence_formation_turn(recent_turn_logs):
        # Surface the skip reason for offline audit so the budget-aware
        # behaviour shows up in policy_notes / per-turn manager_payload.
        policy_notes.append(
            f"hard_negative_discovery_override skipped budget_aware_skip remaining_after_current={remaining_after_current} positive_inventory_ready={_positive_inventory_ready(state)}"
        )
    # --- Component C: conflict-driven recovery override ---
    # After flaw analysis has produced at least one flaw, if conflicts exist
    # and no recovery action has been taken, redirect to a recovery action
    # instead of proceeding to summary/finalize.
    conflict_count = int((state.get("risk_profile", {}) or {}).get("conflict_count", 0) or 0)
    if (
        mode == "s4"
        and action_type in {"analyze_flaws", "summarize_progress", "finalize"}
        and conflict_count > 0
        and counts["flaw_candidates"] > 0
        and not _has_prior_recovery_action(recent_turn_logs)
    ):
        recovery_action = _choose_recovery_action(state)
        if recovery_action in allowed_actions:
            policy_source = "s4_conflict_recovery_override"
            policy_notes.append(
                f"S4 redirects to {recovery_action} because {conflict_count} conflict(s) exist and no recovery action has been taken."
            )
            action_type = recovery_action
    if (
        mode == "s4"
        and action_type in {"analyze_flaws", "summarize_progress", "finalize"}
        and _has_blocking_recovery_signal(state, recent_turn_logs)
        and not _has_prior_recovery_action(recent_turn_logs)
    ):
        recovery_action = _choose_blocking_recovery_action(state)
        if recovery_action in allowed_actions:
            policy_source = "s4_recovery_relevant_override"
            policy_notes.append(
                f"S4 redirects to {recovery_action} because recovery-relevant evidence gaps or active repair signals remain."
            )
            action_type = recovery_action
    if mode == "s4" and ENABLE_STICKY_RECOVERY_BIAS:
        biased_action, sticky_notes = _sticky_recovery_bias(state, recent_turn_logs, action_type, allowed_actions)
        if biased_action != action_type:
            policy_source = "sticky_recovery_bias"
            policy_notes.extend(sticky_notes)
            action_type = biased_action
    payload["support_formation_pass_triggered"] = False
    payload["support_formation_pass_reason"] = ""
    payload["support_formation_pass_from_action"] = ""
    support_reason = _support_formation_pass_reason(state, action_type, allowed_actions, recent_turn_logs)
    if mode == "s4" and support_reason:
        previous_recovery_action = action_type
        policy_source = "support_formation_override"
        policy_notes.append(
            "Support formation pass delayed aggressive recovery because real-claim strong support is still underdeveloped; "
            "using verify_evidence once more before recovery patch mode."
        )
        payload["support_formation_pass_triggered"] = True
        payload["support_formation_pass_reason"] = support_reason
        payload["support_formation_pass_from_action"] = previous_recovery_action
        payload["decision"] = "continue"
        payload["action_type"] = "verify_evidence"
        payload["effective_action_type"] = "verify_evidence"
        payload["turn_mode"] = "normal_evidence"
        payload["phase"] = "normal_review"
        action_type = "verify_evidence"
    # NOTE: Recovery Entry Decision v1 (defer non-ready sticky push) was tested
    # and rolled back — mean reward -0.0105, hj323oR3rw -0.105, only 3 defers
    # with 2/3 swallowed by downstream finalize/conflict_block.
    # See RECOVERY_ENTRY_DECISION_V1_RESULT.md. TQC observability retained.
    # Defer fields below default to False/empty for log-schema stability.
    payload.setdefault("recovery_entry_deferred", False)
    payload.setdefault("recovery_entry_defer_reason", "")
    payload.setdefault("recovery_entry_deferred_from", "")
    current_phase = (
        _normalize_recovery_phase(payload.get("phase"))
        or _normalize_recovery_phase(state.get("phase"))
    )
    candidate_targets_payload = {
        "target_claim_ids": payload.get("target_claim_ids") or inferred.get("target_claim_ids", []),
        "target_flaw_ids": payload.get("target_flaw_ids") or inferred.get("target_flaw_ids", []),
        "target_evidence_ids": payload.get("target_evidence_ids") or inferred.get("target_evidence_ids", []),
        "target_hypotheses": payload.get("target_hypotheses") or inferred.get("target_hypotheses", []),
    }
    raw_progression_target_claim_ids = _normalize_target_claim_ids(candidate_targets_payload.get("target_claim_ids", []))
    progression_gate_issues = _progression_gate_issues(state, action_type, raw_progression_target_claim_ids)
    payload["progression_gate_triggered"] = False
    payload["progression_gate_reason"] = ""
    payload["progression_gate_raw_target_ids"] = list(raw_progression_target_claim_ids)
    payload["progression_gate_sanitized_target_ids"] = []
    payload["blocked_aggressive_recovery_action"] = ""
    payload["fallback_target_gate_blocked"] = False
    payload["broad_target_gate_blocked"] = False
    payload["weak_conflict_gate_blocked"] = False
    # Legacy throttle fields remain explicit false for downstream compatibility.
    payload["progression_throttle_candidate"] = False
    payload["progression_throttle_issues"] = []
    payload["progression_throttle_applied"] = False
    if mode == "s4" and ENABLE_PROGRESSION_GATE and current_phase != "recovery" and progression_gate_issues:
        gated_action = _progression_gate_safe_action(state, original_action_type or inferred_action, action_type, allowed_actions)
        if gated_action != action_type:
            policy_source = "progression_gate_override"
            reason = _progression_gate_reason(progression_gate_issues)
            policy_notes.append(
                "Progression gate blocked aggressive recovery action "
                f"{action_type} because raw target/conflict grounding is not ready ({', '.join(progression_gate_issues)}); "
                f"using {gated_action} to refine target grounding first."
            )
            payload["progression_gate_triggered"] = True
            payload["progression_gate_reason"] = reason
            payload["blocked_aggressive_recovery_action"] = action_type
            payload["fallback_target_gate_blocked"] = "fallback_target" in progression_gate_issues
            payload["broad_target_gate_blocked"] = "broad_target" in progression_gate_issues
            payload["weak_conflict_gate_blocked"] = "weak_conflict" in progression_gate_issues
            action_type = gated_action
    if (
        inferred_action == "summarize_progress"
        and "summarize_progress" in allowed_actions
        and previous_action == action_type
        and previous_focus
        and current_focus == previous_focus
    ):
        policy_source = "stalled_focus_override"
        policy_notes.append("Recent turns repeated the same focus/action, so the policy switched to summarize_progress.")
        action_type = "summarize_progress"
    payload["action_type"] = action_type
    payload["policy_source"] = policy_source
    if action_type != "finalize" and payload.get("decision") == "finalize":
        payload["decision"] = "continue"
        payload["final_decision"] = "undecided"
        payload["final_report"] = ""
        policy_notes.append("Finalize decision was cleared because policy redirected the turn to a non-final action.")
    if action_type == "finalize":
        payload["decision"] = "finalize"
        payload["action_type"] = "finalize"
        payload["selected_agents"] = []
    else:
        payload["decision"] = "continue"
        selected = pick_workers_for_action(action_type, worker_ids, worker_limit)
        if not selected and payload.get("selected_agents"):
            selected = [agent for agent in payload.get("selected_agents", []) if agent in worker_ids][:worker_limit]
        if not selected:
            selected = pick_workers_for_action(inferred_action, worker_ids, worker_limit)
        payload["selected_agents"] = selected
    if not payload.get("focus"):
        payload["focus"] = inferred.get("focus", "Advance the review state.")
        if policy_source != "manager_model":
            policy_notes.append("Focus was filled from inferred policy context.")
    if not payload.get("rationale"):
        payload["rationale"] = inferred.get("rationale", "Fallback manager policy selected the next review action.")
        if policy_source != "manager_model":
            policy_notes.append("Rationale was filled from inferred policy context.")
    payload["target_claim_ids"] = payload.get("target_claim_ids") or inferred.get("target_claim_ids", [])
    payload["target_flaw_ids"] = payload.get("target_flaw_ids") or inferred.get("target_flaw_ids", [])
    payload["target_evidence_ids"] = payload.get("target_evidence_ids") or inferred.get("target_evidence_ids", [])
    payload["target_hypotheses"] = payload.get("target_hypotheses") or inferred.get("target_hypotheses", [])
    post_fallback_target_claim_ids = _normalize_target_claim_ids(payload.get("target_claim_ids", []))
    payload["post_fallback_target_claim_ids"] = list(post_fallback_target_claim_ids)
    payload["post_fallback_target_count"] = len(post_fallback_target_claim_ids)
    payload["fallback_claim_ids_used"] = _fallback_claim_ids(post_fallback_target_claim_ids)
    payload["fallback_evidence_ids_used"] = [
        evidence_id for evidence_id in _normalize_target_claim_ids(payload.get("target_evidence_ids", []))
        if _is_fallback_evidence_id(evidence_id)
    ]
    payload["fallback_target_present"] = bool(payload["fallback_claim_ids_used"] or payload["fallback_evidence_ids_used"])
    payload.setdefault("fallback_contradiction_emitted", False)
    payload = _apply_target_sticky_payload(state, payload, recent_turn_logs)
    payload = _sanitize_targets_for_action(state, action_type, payload, inferred)
    post_sanitize_target_claim_ids = _normalize_target_claim_ids(payload.get("target_claim_ids", []))
    if (
        action_type == "challenge_previous_hypothesis"
        and not post_sanitize_target_claim_ids
        and not payload.get("target_flaw_ids")
    ):
        refinement_targets = _unverified_flaw_negative_evidence_targets(state, recent_turn_logs)
        if refinement_targets["target_flaw_ids"] and "request_evidence_recheck" in allowed_actions:
            action_type = "request_evidence_recheck"
            payload["action_type"] = action_type
            payload["effective_action_type"] = action_type
            payload["target_flaw_ids"] = refinement_targets["target_flaw_ids"]
            payload["target_claim_ids"] = refinement_targets["target_claim_ids"]
            payload["target_evidence_ids"] = refinement_targets["target_evidence_ids"]
            payload["negative_evidence_formation_required"] = True
            payload["selected_agents"] = pick_workers_for_action(action_type, worker_ids, worker_limit)
            policy_source = "recovery_target_refinement_override"
            payload["policy_source"] = policy_source
            policy_notes.append("Recovery challenge target was empty/fallback after sanitization, so policy routed to evidence recheck for real negative-evidence formation.")
            post_sanitize_target_claim_ids = _normalize_target_claim_ids(payload.get("target_claim_ids", []))
        elif not state.get("claims") and "request_evidence_recheck" in allowed_actions:
            bootstrap_claim_ids = [
                claim_id
                for claim_id in post_fallback_target_claim_ids
                if not _is_non_real_review_claim_id(claim_id)
            ][:2]
            if bootstrap_claim_ids:
                action_type = "request_evidence_recheck"
                payload["action_type"] = action_type
                payload["effective_action_type"] = action_type
                payload["target_claim_ids"] = bootstrap_claim_ids
                payload["target_flaw_ids"] = []
                payload["selected_agents"] = pick_workers_for_action(action_type, worker_ids, worker_limit)
                policy_source = "recovery_target_bootstrap_recheck_override"
                payload["policy_source"] = policy_source
                policy_notes.append("Recovery challenge target was not yet present in ReviewState, so policy routed to evidence recheck before patch mode.")
                post_sanitize_target_claim_ids = bootstrap_claim_ids
            else:
                action_type = "summarize_progress"
                payload["action_type"] = action_type
                payload["effective_action_type"] = action_type
                payload["selected_agents"] = []
                payload["target_hypotheses"] = []
                policy_source = "recovery_target_exhausted_override"
                payload["policy_source"] = policy_source
                policy_notes.append("Recovery challenge target was empty/fallback after sanitization, so policy summarized the blockage instead of issuing another weak patch.")
                payload["focus"] = "Summarize the blocked recovery state after exhausting corrective targets."
                payload["rationale"] = "No verified-negative real claim or active flaw target remains for corrective challenge."
                post_sanitize_target_claim_ids = []
        else:
            action_type = "summarize_progress"
            payload["action_type"] = action_type
            payload["effective_action_type"] = action_type
            payload["selected_agents"] = []
            payload["target_hypotheses"] = []
            policy_source = "recovery_target_exhausted_override"
            payload["policy_source"] = policy_source
            policy_notes.append("Recovery challenge target was empty/fallback after sanitization, so policy summarized the blockage instead of issuing another weak patch.")
            payload["focus"] = "Summarize the blocked recovery state after exhausting corrective targets."
            payload["rationale"] = "No verified-negative real claim or active flaw target remains for corrective challenge."
            post_sanitize_target_claim_ids = []
    raw_target_set = set(raw_target_claim_ids)
    post_fallback_set = set(post_fallback_target_claim_ids)
    payload["post_sanitize_target_claim_ids"] = list(post_sanitize_target_claim_ids)
    payload["post_sanitize_target_count"] = len(post_sanitize_target_claim_ids)
    payload["sanitize_bloat_delta"] = max(0, len(post_sanitize_target_claim_ids) - len(post_fallback_target_claim_ids))
    payload["sanitize_expanded_from_raw"] = bool(set(post_sanitize_target_claim_ids) - raw_target_set) if raw_target_set or post_sanitize_target_claim_ids else False
    payload["sanitize_expanded_from_fallback"] = bool(set(post_sanitize_target_claim_ids) - post_fallback_set) if post_fallback_set or post_sanitize_target_claim_ids else False
    payload["sanitize_bloat_detected"] = bool(
        payload["sanitize_bloat_delta"] > 0
        or payload["sanitize_expanded_from_raw"]
        or payload["sanitize_expanded_from_fallback"]
    )
    payload["progression_gate_sanitized_target_ids"] = list(payload.get("target_claim_ids") or [])
    if (
        action_type == "challenge_previous_hypothesis"
        and state.get("claims")
        and not payload.get("target_claim_ids")
        and not payload.get("target_flaw_ids")
    ):
        action_type = "summarize_progress"
        payload["action_type"] = action_type
        payload["effective_action_type"] = action_type
        payload["selected_agents"] = []
        payload["target_hypotheses"] = []
        policy_source = "recovery_target_exhausted_override"
        payload["policy_source"] = policy_source
        policy_notes.append("All recovery-eligible targets are already exhausted, so the manager summarized the blockage instead of issuing another empty challenge.")
        payload["focus"] = "Summarize the blocked recovery state after exhausting corrective targets."
        payload["rationale"] = "No recovery-eligible claim or flaw remains for corrective challenge, so another recovery turn would only repeat a no-effect patch."
    if action_type == "ask_user_clarification":
        payload["selected_agents"] = []
        payload["requires_clarification"] = True
        payload["clarification_question"] = payload.get("clarification_question") or state.get("pending_user_question") or "What review priority should be clarified before the next turn?"
        payload["pending_user_question"] = payload["clarification_question"]
        payload["simulated_user_reply"] = payload.get("simulated_user_reply") or "Prioritize the strongest evidence gap affecting the final recommendation."
    elif action_type == "summarize_progress" and not payload.get("summary_update"):
        payload["summary_update"] = "The manager summarized the current review progress before the next step."
    payload["effective_action_type"] = action_type
    final_action_target_claim_ids = _normalize_target_claim_ids(payload.get("target_claim_ids", []))
    payload["final_action_target_claim_ids"] = list(final_action_target_claim_ids)
    payload["final_action_target_count"] = len(final_action_target_claim_ids)
    payload["final_action_type"] = payload.get("action_type", action_type)
    payload["final_effective_action_type"] = payload.get("effective_action_type", action_type)
    payload["recovery_candidate_action"] = original_action_type if original_action_type in MANAGER_ACTION_TYPES else inferred_action
    payload["recovery_push_triggered"] = action_type in RECOVERY_ACTION_TYPES
    payload["recovery_push_source"] = policy_source if payload["recovery_push_triggered"] else "none"
    payload["recovery_push_reasons"] = _recovery_push_reasons(
        state,
        final_action_target_claim_ids,
        action_type,
        policy_source,
    ) if payload["recovery_push_triggered"] else []
    target_quality_label, target_quality_reasons = _target_quality(state, final_action_target_claim_ids, action_type)
    payload["target_quality_label"] = target_quality_label
    payload["target_quality_reasons"] = target_quality_reasons
    # Target Quality Certificate (observability-only, no behavior change)
    payload.update(target_quality_certificate(state, payload, recent_turn_logs))
    payload["policy_notes"] = policy_notes
    return payload
