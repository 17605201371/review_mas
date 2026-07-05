from __future__ import annotations

import argparse
import concurrent.futures
import copy
import json
import os
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple

from agent_system.review_prompts import (
    CLAIM_PROMPT,
    CRITIQUE_PROMPT,
    EVIDENCE_PROMPT,
    FREEFORM_REVIEWER_NEGATIVE_PROMPT,
    GENERAL_REVIEWER_PROMPT,
    MANAGER_PROMPT,
    RECOVERY_PATCH_PROMPT,
    REVIEW_ISSUE_DISCOVERY_PROMPT,
    TARGETED_NEGATIVE_EVIDENCE_PROMPT,
)
from agent_system import review_manager_policy as review_policy
from agent_system.environments.env_package.review.envs import ReviewEnv
from agent_system.environments.env_package.review.state import (
    MANAGER_ACTION_TYPES,
    REVIEW_NEGATIVE_VERIFIED_LABEL,
    _classify_negative_evidence_type,
    _hard_negative_diagnosis_targets,
    _missing_ablation_target_quality,
    _review_issue_candidate_menu_quality_failure,
    _review_issue_candidate_menu_id,
    _review_issue_candidate_selector_menu,
    _review_issue_component_ablation_seed_targets,
    _review_issue_disambiguate_candidate_menu_id,
    _review_issue_missing_items_are_concrete,
    _review_issue_normalized_cluster_target,
    _review_issue_slot_for_type,
    build_turn_action,
    build_decision_hygiene_view,
    infer_final_decision,
    normalize_manager_payload,
    normalize_review_update_payload,
    render_claim_observation,
    render_critique_observation,
    render_general_reviewer_observation,
    render_manager_observation,
    render_review_observation,
    render_evidence_observation,
)
from agent_system.environments.env_package.review.reward import _extract_decision
from agent_system.environments.env_package.review.support_quality import derive_sample_support_summary


PromptFn = Callable[[str, str], str]


def _freeform_reviewer_negative_enabled() -> bool:
    return os.environ.get("DRMAS_FREEFORM_REVIEWER_NEGATIVE", "").strip().lower() in {
        "1",
        "true",
        "on",
        "yes",
    }


def _critique_only_discovery_eval_enabled() -> bool:
    return os.environ.get("DRMAS_CRITIQUE_ONLY_DISCOVERY_EVAL", "").strip().lower() in {
        "1",
        "true",
        "on",
        "yes",
    }


GenerateFn = Callable[[str, str], str]


def _timestamp() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S")


def _generate_many(generate_fn: GenerateFn, requests: Sequence[tuple[str, str]]) -> List[str]:
    if not requests:
        return []
    batch_fn = getattr(generate_fn, "generate_many", None)
    if callable(batch_fn):
        return list(batch_fn(requests))
    return [generate_fn(agent_id, prompt) for agent_id, prompt in requests]


@dataclass(frozen=True)
class ReviewAgentSpec:
    agent_id: str
    prompt: str
    required_fields: tuple[str, ...] = ()
    is_manager: bool = False







AGENT_SPECS = {
    "Review Manager Agent": ReviewAgentSpec("Review Manager Agent", MANAGER_PROMPT, is_manager=True),
    "General Reviewer Agent": ReviewAgentSpec("General Reviewer Agent", GENERAL_REVIEWER_PROMPT),
    "General Reviewer Agent 1": ReviewAgentSpec("General Reviewer Agent 1", GENERAL_REVIEWER_PROMPT),
    "General Reviewer Agent 2": ReviewAgentSpec("General Reviewer Agent 2", GENERAL_REVIEWER_PROMPT),
    "General Reviewer Agent 3": ReviewAgentSpec("General Reviewer Agent 3", GENERAL_REVIEWER_PROMPT),
    "Reviewer Agent": ReviewAgentSpec("Reviewer Agent", GENERAL_REVIEWER_PROMPT),
    "Claim Agent": ReviewAgentSpec("Claim Agent", CLAIM_PROMPT, required_fields=("claims",)),
    "Evidence Agent": ReviewAgentSpec("Evidence Agent", EVIDENCE_PROMPT),
    "Critique Agent": ReviewAgentSpec("Critique Agent", CRITIQUE_PROMPT),
}





MAX_TEAM_CONTEXT_CHARS = 2400
MAX_TEAM_RESPONSE_CHARS = 700
MAX_MANAGER_OBSERVATION_CHARS = 5200
MAX_WORKER_OBSERVATION_CHARS = 4200
MAX_EVIDENCE_WORKER_OBSERVATION_CHARS = 3600
MAX_TARGETED_NEGATIVE_WORKER_OBSERVATION_CHARS = 5200

RECOVERY_TURN_MODES = {"normal_evidence", "recovery_patch"}
REVIEW_PHASES = {"normal_review", "recovery"}
RECOVERY_ACTION_TYPES = {"challenge_previous_hypothesis", "request_evidence_recheck"}
RECOVERY_PATCH_ACTION_TYPES = {"challenge_previous_hypothesis"}
_REVIEW_ISSUE_BUNDLE_ENABLED = os.environ.get("DRMAS_REVIEW_ISSUE_BUNDLE", "1").strip().lower() not in {
    "0",
    "false",
    "off",
    "no",
}
_DIAGPENDING_RECOVERY_ENABLED = (
    os.environ.get("DRMAS_DIAGPENDING_RECOVERY", "").strip().lower() in {
        "1",
        "true",
        "on",
        "yes",
    }
    or _REVIEW_ISSUE_BUNDLE_ENABLED
)


def _diagpending_recovery_enabled() -> bool:
    raw = os.environ.get("DRMAS_DIAGPENDING_RECOVERY")
    if raw is None or not str(raw).strip():
        return bool(_DIAGPENDING_RECOVERY_ENABLED)
    return str(raw).strip().lower() in {
        "1",
        "true",
        "on",
        "yes",
    }


def _clip_text(text: str, limit: int) -> str:
    value = str(text or "").strip()
    if len(value) <= limit:
        return value
    keep = max(0, limit - 25)
    return value[:keep].rstrip() + "\n...[truncated]"


def _clean_generation_snippet(text: str, limit: int = 260) -> str:
    value = str(text or "")
    value = value.replace("<think>", " ").replace("</think>", " ")
    value = value.replace("<json>", " ").replace("</json>", " ")
    value = " ".join(value.split())
    return _clip_text(value, limit)


def _candidate_text(value: Any, limit: int = 220) -> str:
    return _clip_text(" ".join(str(value or "").split()), limit)


def _candidate_slug(value: Any, fallback: str = "item") -> str:
    text = str(value or fallback).strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text[:80] or fallback


def _normalize_turn_mode(value: Any) -> str:
    mode = str(value or "").strip().lower()
    return mode if mode in RECOVERY_TURN_MODES else ""


def _normalize_phase(value: Any) -> str:
    phase = str(value or "").strip().lower()
    return phase if phase in REVIEW_PHASES else ""


def _is_recovery_triggered_turn(manager_payload: Optional[Dict[str, Any]]) -> bool:
    if not isinstance(manager_payload, dict):
        return False
    action_type = str(manager_payload.get("effective_action_type") or manager_payload.get("action_type") or "").strip()
    return (
        action_type in RECOVERY_PATCH_ACTION_TYPES
        or bool(manager_payload.get("recovery_patch_mode_entered"))
    )


def _apply_turn_mode(manager_payload: Dict[str, Any]) -> Dict[str, Any]:
    normalized = dict(manager_payload or {})
    phase = _normalize_phase(normalized.get("phase"))
    turn_mode = _normalize_turn_mode(normalized.get("turn_mode"))
    action_type = str(normalized.get("effective_action_type") or normalized.get("action_type") or "").strip()
    if phase == "recovery":
        turn_mode = "recovery_patch" if action_type in RECOVERY_PATCH_ACTION_TYPES else "normal_evidence"
    elif not turn_mode:
        turn_mode = "recovery_patch" if _is_recovery_triggered_turn(normalized) else "normal_evidence"
    if not phase:
        phase = "recovery" if action_type in RECOVERY_ACTION_TYPES or turn_mode == "recovery_patch" else "normal_review"
    normalized["phase"] = phase
    normalized["phase_before_action"] = _normalize_phase(normalized.get("phase_before_action")) or phase
    normalized["turn_mode"] = turn_mode
    normalized["recovery_patch_mode_entered"] = turn_mode == "recovery_patch"
    return normalized


def _latest_recovery_outcome(state: Dict[str, Any], recent_turn_logs: Sequence[Dict[str, Any]]) -> tuple[str, str]:
    latest_turn = list(recent_turn_logs or [])[-1] if recent_turn_logs else {}
    latest_patch_log = state.get("_latest_patch_log", {}) or {}
    latest_turn_is_recovery = bool(
        latest_turn and (
            str(latest_turn.get("phase_after_action") or latest_turn.get("phase") or "") == "recovery"
            or bool(latest_turn.get("recovery_patch_mode_entered"))
            or str(latest_turn.get("action_type") or "") in RECOVERY_ACTION_TYPES
            or str(latest_turn.get("effective_action_type") or "") in RECOVERY_ACTION_TYPES
        )
    )
    if latest_turn_is_recovery and bool(latest_turn.get("recovery_committed")):
        return "committed", "Previous recovery turn committed a patch."
    if bool(latest_patch_log.get("recovery_committed")):
        return "committed", "Previous recovery turn committed a patch."
    failure_code = str(latest_turn.get("recovery_failure_code") or latest_patch_log.get("recovery_failure_code") or "").strip()
    if latest_turn_is_recovery and failure_code == "BLOCKED_BY_POLICY":
        return "blocked_terminal", "Previous recovery turn ended in a blocked terminal result."
    return "open", ""


def _latest_turn_completed_normal_recheck(recent_turn_logs: Sequence[Dict[str, Any]]) -> bool:
    latest_turn = list(recent_turn_logs or [])[-1] if recent_turn_logs else {}
    action_type = str(latest_turn.get("effective_action_type") or latest_turn.get("action_type") or "").strip()
    turn_mode = _normalize_turn_mode(latest_turn.get("turn_mode"))
    return (
        action_type == "request_evidence_recheck"
        and turn_mode != "recovery_patch"
        and not str(latest_turn.get("recovery_failure_code") or "").strip()
    )


def _latest_turn_was_negative_evidence_formation(recent_turn_logs: Sequence[Dict[str, Any]]) -> bool:
    latest_turn = list(recent_turn_logs or [])[-1] if recent_turn_logs else {}
    policy_source = str(latest_turn.get("policy_source") or "")
    policy_requires_negative = policy_source in {"negative_evidence_formation_override", "compact_negative_pass_override"}
    targeted_requires_negative = (
        policy_source == "targeted_negative_search_override"
        and bool(latest_turn.get("targeted_negative_search_required"))
    )
    return bool(
        latest_turn.get("negative_evidence_formation_required")
        or policy_requires_negative
        or targeted_requires_negative
    )


def _state_has_verified_negative_binding_target(state: Optional[Dict[str, Any]]) -> bool:
    if not isinstance(state, dict):
        return False
    evidence_by_id = {
        str(item.get("evidence_id") or ""): item
        for item in state.get("evidence_map", []) or []
        if isinstance(item, dict) and str(item.get("evidence_id") or "")
    }
    for item in evidence_by_id.values():
        if _is_verified_negative_evidence_for_recovery(item) and _negative_evidence_record_is_actionable(item):
            return True
    for flaw in state.get("flaw_candidates", []) or []:
        if not isinstance(flaw, dict):
            continue
        ids = list(flaw.get("verified_negative_evidence_ids") or [])
        ids += list(flaw.get("negative_evidence_ids") or [])
        ids += list(flaw.get("evidence_ids") or [])
        for raw in ids:
            record = evidence_by_id.get(str(raw or ""))
            if record and _is_verified_negative_evidence_for_recovery(record) and _negative_evidence_record_is_actionable(record):
                return True
    return False


def _pending_reviewer_negative_candidate_claim_ids(state: Optional[Dict[str, Any]]) -> List[str]:
    if not isinstance(state, dict):
        return []
    claim_lookup = {
        str(item.get("claim_id") or "").strip(): item
        for item in state.get("claims", []) or []
        if isinstance(item, dict) and str(item.get("claim_id") or "").strip()
    }
    claim_ids: List[str] = []
    for item in state.get("reviewer_negative_candidates", []) or []:
        if not isinstance(item, dict):
            continue
        status = str(item.get("status") or "pending_quote_verification").strip().lower()
        if status not in {"pending_quote_verification", "open", "not_assessable"}:
            continue
        claim_id = str(item.get("claim_id") or "").strip()
        claim = claim_lookup.get(claim_id) or {}
        if not claim_id or claim_id.startswith(("claim-paper-context-", "claim-paper-fallback-", "claim-context-", "claim-fallback-")):
            continue
        claim_kind = str(claim.get("claim_kind") or "").strip().lower()
        if claim_kind and claim_kind not in {"paper_extracted", "raw_salvaged_claim_agent_output"}:
            continue
        claim_ids.append(claim_id)
    return list(dict.fromkeys(claim_ids))


def _route_pending_reviewer_negative_quote_verification(
    manager_payload: Dict[str, Any],
    state: Dict[str, Any],
    worker_ids: Sequence[str],
    worker_limit: int,
    recent_turn_logs: Sequence[Dict[str, Any]],
    step: int,
    turn_cap: int,
) -> Optional[Dict[str, Any]]:
    if not step or not turn_cap or step >= turn_cap:
        return None
    candidate_claim_ids = _pending_reviewer_negative_candidate_claim_ids(state)
    if not candidate_claim_ids:
        return None
    attempt_counter = getattr(review_policy, "_targeted_reviewer_negative_verification_attempt_count", None)
    attempt_count = int(attempt_counter(recent_turn_logs) if callable(attempt_counter) else 0)
    max_attempts = int(getattr(review_policy, "_TARGETED_REVIEWER_NEGATIVE_MAX_ATTEMPTS", 2) or 2)
    if attempt_count >= max_attempts:
        return None
    normalized = dict(manager_payload or {})
    normalized["decision"] = "continue"
    normalized["action_type"] = "verify_evidence"
    normalized["effective_action_type"] = "verify_evidence"
    normalized["phase"] = "normal_review"
    normalized["phase_enter_reason"] = ""
    normalized["phase_hold_reason"] = ""
    normalized["phase_exit_reason"] = normalized.get("phase_exit_reason") or "Recovery phase deferred because reviewer-negative candidates still need quote verification."
    normalized["turn_mode"] = "normal_evidence"
    normalized["recovery_patch_mode_entered"] = False
    normalized["final_decision"] = "undecided"
    normalized["final_report"] = ""
    normalized["selected_agents"] = [agent for agent in ["Evidence Agent"] if agent in worker_ids][:worker_limit] or list(worker_ids[:1])
    normalized["target_claim_ids"] = candidate_claim_ids[:2]
    normalized["target_flaw_ids"] = []
    normalized["target_evidence_ids"] = []
    normalized["target_hypotheses"] = []
    normalized["negative_evidence_formation_required"] = True
    normalized["targeted_negative_search_required"] = True
    normalized["freeform_reviewer_negative_discovery_required"] = False
    normalized["freeform_reviewer_negative_enabled"] = True
    normalized["freeform_reviewer_negative_stage"] = "quote_verification"
    normalized["policy_source"] = "targeted_negative_search_override"
    notes = list(normalized.get("policy_notes", []))
    notes.append(
        "Pending reviewer-negative candidates take priority over recovery; Evidence Agent must attempt quote verification before recovery patch routing."
    )
    normalized["policy_notes"] = list(dict.fromkeys(notes))[:8]
    normalized["focus"] = (
        "Verify pending reviewer-discovered negative candidates against copied paper text before recovery or final reporting."
    )
    normalized["rationale"] = (
        (str(normalized.get("rationale") or "").strip() + " ").strip()
        + "Reviewer-negative candidates exist but are still pending quote verification, so recovery is deferred until Evidence Agent checks them against paper text."
    )[:600]
    normalized["finalize_blocked_by_phase"] = False
    normalized["auto_finalized"] = False
    if not int(normalized.get("phase_turn_index") or 0):
        normalized["phase_turn_index"] = max(1, int(state.get("phase_turn_index", 0) or 0))
    return _apply_turn_mode(normalized)


def _preserve_negative_binding_retry_turn(
    manager_payload: Dict[str, Any],
    worker_ids: Sequence[str],
    worker_limit: int,
    recent_turn_logs: Sequence[Dict[str, Any]],
    state: Optional[Dict[str, Any]] = None,
) -> Optional[Dict[str, Any]]:
    policy_source = str((manager_payload or {}).get("policy_source") or "")
    action_type = str((manager_payload or {}).get("action_type") or "")
    explicit_retry = policy_source == "negative_evidence_binding_retry_override" and action_type == "analyze_flaws"
    post_negative_formation_review = (
        _latest_turn_was_negative_evidence_formation(recent_turn_logs)
        and action_type in {"challenge_previous_hypothesis", "analyze_flaws"}
        and _state_has_verified_negative_binding_target(state)
    )
    if not explicit_retry and not post_negative_formation_review:
        return None
    normalized = dict(manager_payload or {})
    normalized["phase"] = "normal_review"
    normalized["phase_before_action"] = "normal_review"
    normalized["phase_enter_reason"] = ""
    normalized["phase_hold_reason"] = ""
    normalized["phase_exit_reason"] = normalized.get("phase_exit_reason", "")
    normalized["decision"] = "continue"
    normalized["action_type"] = "analyze_flaws"
    normalized["effective_action_type"] = "analyze_flaws"
    if post_negative_formation_review and not explicit_retry:
        normalized["policy_source"] = "negative_evidence_binding_retry_override"
        normalized["negative_evidence_binding_retry_required"] = True
    normalized["turn_mode"] = "normal_evidence"
    normalized["recovery_patch_mode_entered"] = False
    normalized["finalize_blocked_by_phase"] = False
    normalized["selected_agents"] = [agent for agent in ["Critique Agent"] if agent in worker_ids][:worker_limit] or list(worker_ids[:1])
    if _latest_turn_was_negative_evidence_formation(recent_turn_logs):
        notes = list(normalized.get("policy_notes", []))
        notes.append("Recovery patch was deferred so Critique Agent can bind the verified negative evidence produced by the previous recheck.")
        normalized["policy_notes"] = list(dict.fromkeys(notes))[:8]
    return _apply_turn_mode(normalized)


def _recovery_candidate_claim_ids(state: Dict[str, Any], recovery_action: str) -> List[str]:
    claims = state.get("claims", []) or []
    evidence = state.get("evidence_map", []) or []
    allowed_statuses = {"supported", "partially_supported", "uncertain"} if recovery_action == "challenge_previous_hypothesis" else {"supported", "partially_supported", "uncertain", "new"}
    strong_claim_ids = {
        str(item.get("claim_id") or "").strip()
        for item in claims
        if isinstance(item, dict) and _is_recovery_claim_status_target(item)
    }
    claim_status = {
        str(item.get("claim_id") or ""): str(item.get("status") or "uncertain").strip().lower()
        for item in claims
        if item.get("claim_id") and str(item.get("claim_id") or "").strip() in strong_claim_ids
    }
    negative_claim_ids: List[str] = []
    for item in evidence:
        claim_id = str(item.get("claim_id") or "").strip()
        if not claim_id or claim_status.get(claim_id) not in allowed_statuses:
            continue
        if _allows_claim_status_downgrade_from_recovery(item):
            negative_claim_ids.append(claim_id)
    fallback_claim_ids = [
        str(item.get("claim_id") or "").strip()
        for item in claims
        if (
            item.get("claim_id")
            and str(item.get("claim_id") or "").strip() in strong_claim_ids
            and str(item.get("status") or "uncertain").strip().lower() in allowed_statuses
        )
    ]
    limit = 2 if recovery_action == "challenge_previous_hypothesis" else 3
    if recovery_action == "challenge_previous_hypothesis":
        return list(dict.fromkeys(negative_claim_ids + _recovery_lifecycle_claim_ids(state, limit=limit)))[:limit]
    return list(dict.fromkeys(negative_claim_ids + fallback_claim_ids))[:limit]


def _recovery_candidate_evidence_ids(state: Dict[str, Any], target_claim_ids: Sequence[str]) -> List[str]:
    target_claim_id_set = {str(item).strip() for item in target_claim_ids or [] if str(item).strip()}
    evidence_ids: List[str] = []
    for item in state.get("evidence_map", []) or []:
        claim_id = str(item.get("claim_id") or "").strip()
        evidence_id = str(item.get("evidence_id") or "").strip()
        if not evidence_id or claim_id not in target_claim_id_set:
            continue
        if _allows_claim_status_downgrade_from_recovery(item):
            evidence_ids.append(evidence_id)
    return list(dict.fromkeys(evidence_ids))[:4]


def _is_recovery_weak_claim_id(claim_id: str) -> bool:
    value = str(claim_id or "").strip().lower()
    return value.startswith(
        (
            "claim-context",
            "claim-fallback",
            "claim-recovery",
            "claim-paper-context",
        )
    )


def _recovery_claim_text_has_prompt_leakage(claim: Dict[str, Any]) -> bool:
    text = str((claim or {}).get("claim") or "").strip().lower()
    if not text:
        return False
    return any(
        marker in text
        for marker in (
            "do not output",
            "json block",
            "output exactly one strict json",
            "<json>",
            "<think>",
            "[truncated]",
        )
    )


def _negative_binding_claim_text_has_meta_shell(claim: Dict[str, Any]) -> bool:
    text = str((claim or {}).get("claim") or (claim or {}).get("text") or "").strip().lower()
    if not text:
        return True
    if any(
        marker in text
        for marker in (
            "claim-paper-context",
            "claim-context",
            "claim-paper-fallback",
            "claim-fallback",
            "claim-recovery",
            "context_synthesized",
            "context_derived",
            "raw_salvaged",
            "claim_type=",
            "coverage_tags=",
            "importance=",
        )
    ):
        return True
    if re.search(r"^\s*(?:what\s+(?:is|are|does|do)\b|how\s+(?:does|do|is|are)\b|why\s+(?:does|do|is|are)\b)", text):
        return True
    if re.search(r"\bfrom the (?:title|abstract|introduction)\b|\bthat could be (?:a|an)\b", text):
        return True
    return False


def _is_negative_binding_claim_target(claim: Dict[str, Any]) -> bool:
    """Allow real paper claims to host negative evidence without enabling status patches."""
    claim_id = str((claim or {}).get("claim_id") or "").strip()
    if not claim_id:
        return False
    lowered = claim_id.lower()
    if lowered.startswith(
        (
            "claim-context",
            "claim-recovery",
            "claim-paper-context",
            "claim-paper-recovery",
            "claim-paper-fallback",
            "claim-fallback",
        )
    ):
        return False
    if _recovery_claim_text_has_prompt_leakage(claim) or _negative_binding_claim_text_has_meta_shell(claim):
        return False
    origin_kind = str((claim or {}).get("claim_origin_kind") or "").strip().lower()
    canonicalized_raw_salvage = bool((claim or {}).get("paper_claim_canonicalized_from_raw_salvage"))
    if origin_kind in {
        "context_synthesized",
        "recovery_marker",
        "fallback_synthesized",
        "paper_context_synthesized",
    }:
        return False
    if origin_kind == "raw_salvaged_claim_agent_output" and not canonicalized_raw_salvage:
        return False
    return True


def _is_recovery_strong_claim_target(claim: Dict[str, Any]) -> bool:
    claim_id = str((claim or {}).get("claim_id") or "").strip()
    if not claim_id or _is_recovery_weak_claim_id(claim_id):
        return False
    if _recovery_claim_text_has_prompt_leakage(claim):
        return False
    origin_kind = str((claim or {}).get("claim_origin_kind") or "").strip().lower()
    claim_kind = str((claim or {}).get("claim_kind") or "").strip().lower()
    origin = " ".join(
        str((claim or {}).get(key) or "")
        for key in ("claim_origin", "claim_source", "source_stage", "provenance")
    ).lower()
    paper_salvaged_claim = (
        claim_id.lower().startswith("claim-paper-fallback")
        and claim_kind == "paper_extracted"
        and origin_kind == "raw_salvaged_claim_agent_output"
        and "context_derived" not in origin
    )
    if origin_kind == "context_synthesized":
        return False
    if origin_kind == "raw_salvaged_claim_agent_output":
        return paper_salvaged_claim
    if any(marker in origin for marker in ("context_derived", "raw_salvage", "malformed_claim_agent_output")):
        return False
    return True


def _is_recovery_contested_claim_target(claim: Dict[str, Any]) -> bool:
    """Return True when a claim can anchor a non-destructive contested relation.

    This is intentionally wider than ``_is_recovery_claim_status_target``:
    canonicalized raw-salvaged paper claims may host a contested relation, but
    still cannot be downgraded by claim-status recovery unless the stricter
    status target gate admits them.
    """
    claim_id = str((claim or {}).get("claim_id") or "").strip()
    if not claim_id or _is_recovery_weak_claim_id(claim_id):
        return False
    if _recovery_claim_text_has_prompt_leakage(claim) or _negative_binding_claim_text_has_meta_shell(claim):
        return False
    origin_kind = str((claim or {}).get("claim_origin_kind") or "").strip().lower()
    claim_kind = str((claim or {}).get("claim_kind") or "").strip().lower()
    origin = " ".join(
        str((claim or {}).get(key) or "")
        for key in ("claim_origin", "claim_source", "source_stage", "provenance")
    ).lower()
    if origin_kind in {
        "context_synthesized",
        "recovery_marker",
        "fallback_synthesized",
        "paper_context_synthesized",
    }:
        return False
    paper_salvaged_fallback = (
        claim_id.lower().startswith("claim-paper-fallback")
        and claim_kind == "paper_extracted"
        and origin_kind == "raw_salvaged_claim_agent_output"
        and "context_derived" not in origin
    )
    if origin_kind == "raw_salvaged_claim_agent_output":
        return bool((claim or {}).get("paper_claim_canonicalized_from_raw_salvage")) or paper_salvaged_fallback
    if any(marker in origin for marker in ("context_derived", "raw_salvage", "malformed_claim_agent_output")):
        return False
    return True


def _is_recovery_claim_status_target(claim: Dict[str, Any]) -> bool:
    """Return True for claims that can safely receive status-changing recovery."""
    claim_id = str((claim or {}).get("claim_id") or "").strip().lower()
    if claim_id.startswith("claim-paper-fallback"):
        return False
    return _is_recovery_strong_claim_target(claim)


def _flaw_has_real_recovery_claim_target(
    flaw: Dict[str, Any],
    claim_lookup: Dict[str, Dict[str, Any]],
    evidence_lookup: Dict[str, Dict[str, Any]],
) -> bool:
    """Return whether a flaw is connected to at least one real recovery claim.

    Quote-bank or scope-limitation flaws attached only to fallback/context
    claims should not produce recovery patches. They are assessment limitations,
    not real paper-side repairs.
    """
    candidate_claim_ids: List[str] = []
    for raw in (flaw or {}).get("related_claim_ids", []) or []:
        claim_id = str(raw or "").strip()
        if claim_id:
            candidate_claim_ids.append(claim_id)
    for raw_eid in (
        list((flaw or {}).get("evidence_ids") or [])
        + list((flaw or {}).get("negative_evidence_ids") or [])
        + list((flaw or {}).get("hard_negative_evidence_ids") or [])
        + list((flaw or {}).get("contradicting_evidence_ids") or [])
    ):
        record = evidence_lookup.get(str(raw_eid or "").strip())
        claim_id = str((record or {}).get("claim_id") or "").strip()
        if claim_id:
            candidate_claim_ids.append(claim_id)
    if not candidate_claim_ids:
        return True
    for claim_id in dict.fromkeys(candidate_claim_ids):
        if _is_recovery_claim_status_target(claim_lookup.get(claim_id, {})) or _is_recovery_contested_claim_target(claim_lookup.get(claim_id, {})):
            return True
    return False


def _blocked_non_real_flaw_target_payload(flaw_id: str) -> Dict[str, Any]:
    return normalize_review_update_payload(
        {
            "action": "blocked",
            "target_type": "flaw",
            "target_id": flaw_id,
            "blocked_reason": (
                "Target flaw is attached only to fallback/context claim targets; "
                "downgrading it would be a no-effect recovery patch rather than a real paper-side repair."
            ),
            "missing_requirements": ["real paper claim target with verified negative grounding"],
            "recovery_terminal": True,
            "recovery_terminal_reason": _ASSESSMENT_LIMITATION_NO_EFFECT_TERMINAL_REASON,
            "recovery_repeat_allowed": False,
        }
    )


_VERIFIED_RECOVERY_LABELS = {"paper_grounded_exact", "paper_grounded_normalized"}
_VERIFIED_RECOVERY_SEMANTIC_LABELS = {"semantic_support_verified", "semantic_negative_verified"}
_NEGATIVE_RECOVERY_STANCES = {
    "contradicts",
    "contradict",
    "refutes",
    "refute",
    "weakens",
    "weaken",
    "undermines",
    "undermine",
    "partially_contradicts",
    "partially_refutes",
    "missing",
    "unsupported",
    "does_not_support",
    "not_grounded",
    "negative",
}


_NEGATIVE_QUOTE_ANCHOR_RE = re.compile(
    r"\b(no\s+significant|not\s+significant|does\s+not|do\s+not|did\s+not|"
    r"lack|lacks|lacking|missing|without|insufficient|not\s+evaluated|"
    r"not\s+compare|no\s+ablation|component\s+analysis|single\s+dataset|"
    r"only\s+evaluated|unfair\s+(?:comparison|baseline)|weak\s+baseline|"
    r"robustness|generalization|generalisation|out-of-domain|ood|oracle|leakage|train[- ]test|"
    r"runtime|latency|memory|parameters?|flops|compute|computational\s+cost|"
    r"implementation\s+details?|hyperparameters?|reproducib(?:ility|le)|"
    r"mixed\s+results?|inconsistent\s+results?|marginal\s+improvements?|"
    r"fail|fails|failed|worse|underperform|limitation|limitations)\b",
    re.IGNORECASE,
)

_ACTIONABLE_NEGATIVE_EVIDENCE_TYPES = frozenset(
    {
        "direct_contradiction",
        "negative_result",
        "missing_ablation",
        "missing_baseline",
        "unfair_or_weak_baseline",
        "insufficient_evaluation",
        "missing_robustness_or_generalization",
        "evaluation_protocol_risk",
        "efficiency_cost_gap",
        "reproducibility_gap",
        "method_support_gap",
        "scope_overclaim",
        "result_claim_mismatch",
    }
)
_LIMITATION_NEGATIVE_EVIDENCE_TYPES = frozenset({"scope_limitation", "generic_gap"})
_TRUE_PAPER_NEGATIVE_EVIDENCE_TYPES = frozenset(
    {
        "direct_contradiction",
        "negative_result",
        "missing_ablation",
        "missing_baseline",
        "unfair_or_weak_baseline",
        "insufficient_evaluation",
        "missing_robustness_or_generalization",
        "evaluation_protocol_risk",
        "efficiency_cost_gap",
        "result_claim_mismatch",
        "reproducibility_gap",
        "method_support_gap",
    }
)
_SECONDARY_NEGATIVE_EVIDENCE_TYPES = frozenset({"scope_overclaim", "scope_limitation", "generic_gap"})
_PROTECTED_POTENTIAL_CONCERN_TERMINAL_REASON = "verified_actionable_negative_concern_preserved"
_ASSESSMENT_LIMITATION_NO_EFFECT_TERMINAL_REASON = "assessment_limitation_no_effect_preserved"
_PROTECTED_POTENTIAL_CONCERN_BLOCKED_REASON = (
    "Target flaw is already a candidate with verified actionable negative evidence; "
    "leave it as a final potential concern instead of routing it to an assessment limitation."
)


def _negative_quote_entry_type(entry: Dict[str, Any]) -> str:
    explicit = str(entry.get("negative_evidence_type") or "").strip()
    if explicit:
        return explicit
    return _classify_negative_evidence_type(str(entry.get("raw_quote") or ""))


def _negative_quote_entry_is_actionable(entry: Dict[str, Any]) -> bool:
    return _negative_quote_entry_type(entry) in _ACTIONABLE_NEGATIVE_EVIDENCE_TYPES


def _negative_evidence_record_type(item: Dict[str, Any]) -> str:
    explicit = str(item.get("negative_evidence_type") or "").strip()
    if explicit:
        return explicit
    return _classify_negative_evidence_type(str(item.get("raw_quote") or item.get("evidence") or ""))


def _negative_evidence_record_is_actionable(item: Dict[str, Any]) -> bool:
    return _negative_evidence_record_type(item) in _ACTIONABLE_NEGATIVE_EVIDENCE_TYPES


def _negative_evidence_type_priority(negative_type: str) -> int:
    value = str(negative_type or "").strip()
    if value in _TRUE_PAPER_NEGATIVE_EVIDENCE_TYPES:
        return 0
    if value == "scope_overclaim":
        return 1
    if value in _SECONDARY_NEGATIVE_EVIDENCE_TYPES:
        return 2
    return 3


_BROAD_CLAIM_RE = re.compile(
    r"\b(generaliz(?:e|es|ed|ation)|generalisation|zero-shot|unseen|robust|"
    r"across|various|diverse|all|any|foundation model|scal(?:e|es|able|ability)|"
    r"broad|universal|comprehensive|state-of-the-art|sota|"
    r"defy|defies|defying|overcome|mitigat(?:e|es|ed|ing|ion))\b",
    re.IGNORECASE,
)
_SCOPE_LIMIT_QUOTE_RE = re.compile(
    r"\b(future work|leave (?:their|our|this|its)? ?exploration|not yet (?:explored|evaluated|validated)|"
    r"limited to|only evaluated|out of scope|limitation|limitations|restrict(?:ed|ion|ions)?)\b",
    re.IGNORECASE,
)
_CONCRETE_SCOPE_LIMIT_QUOTE_RE = re.compile(
    r"\b(can be explored|could be explored|remain(?:s)? (?:for|as) future work|"
    r"leave (?:their|our|this|its)? ?exploration|not yet (?:explored|evaluated|validated)|"
    r"limited to|only evaluated|out of scope|more effective way|limitation|limitations|restrict(?:ed|ion|ions)?)\b",
    re.IGNORECASE,
)
_RESULT_SCOPE_CLAIM_RE = re.compile(
    r"\b(outperform|improv(?:e|es|ed|ement)|performance|accuracy|f1|auc|result|"
    r"state-of-the-art|sota|benchmark|achiev(?:e|es|ed))\b",
    re.IGNORECASE,
)
_RESULT_MISMATCH_SCOPE_QUOTE_RE = re.compile(
    r"\b(mixed results?|inconsistent(?: results?)?|not consistent(?:ly)?|"
    r"does not always improve|does not improve|failed? to improve|fails? to improve|"
    r"marginal(?: improvements?| gains?)?|small gains?|worse|underperform)\b",
    re.IGNORECASE,
)
_EVAL_SCOPE_CLAIM_RE = re.compile(
    r"\b(evaluat(?:e|es|ed|ion)|benchmark|dataset|comprehensive|robust|"
    r"generaliz(?:e|es|ed|ation)|across|diverse|unseen|external|out-of-domain)\b",
    re.IGNORECASE,
)
_INSUFFICIENT_EVAL_SCOPE_QUOTE_RE = re.compile(
    r"\b(only evaluated on|single dataset|limited (?:evaluation|experiments?|datasets?|benchmarks?)|"
    r"limited to (?:one|two|a single) (?:dataset|benchmark|task|domain)|"
    r"not (?:yet )?(?:evaluated|validated|tested)|small-scale evaluation|few datasets?|no evaluation)\b",
    re.IGNORECASE,
)
_ROBUSTNESS_SCOPE_CLAIM_RE = re.compile(
    r"\b(robust(?:ness)?|generaliz(?:e|es|ed|ation)|generalisation|unseen|"
    r"out-of-domain|ood|cross-domain|external|corrupt(?:ed|ion)|stress|"
    r"transfer(?:able|ability)|real-world)\b",
    re.IGNORECASE,
)
_ROBUSTNESS_GAP_QUOTE_RE = re.compile(
    r"\b(no (?:robustness|generalization|generalisation|out-of-domain|ood|cross-domain|stress) (?:test|evaluation|experiment)|"
    r"missing (?:robustness|generalization|generalisation|out-of-domain|ood|cross-domain|stress) (?:test|evaluation|experiment)|"
    r"not (?:tested|evaluated|validated) (?:on|under|against) (?:unseen|out-of-domain|ood|cross-domain|external|corrupted|noisy)|"
    r"only evaluated on (?:in-domain|seen|clean|single-domain)|"
    r"limited (?:robustness|generalization|generalisation|transferability) evaluation)\b",
    re.IGNORECASE,
)
_BASELINE_FAIRNESS_CLAIM_RE = re.compile(
    r"\b(baseline|baselines|comparison|compare|compared|state-of-the-art|sota|"
    r"outperform|surpass|competitive)\b",
    re.IGNORECASE,
)
_UNFAIR_BASELINE_QUOTE_RE = re.compile(
    r"\b(unfair (?:comparison|baseline|evaluation)|weak baselines?|"
    r"(?:baseline|baselines) (?:are|is|was|were)?\s*(?:weak|outdated|not tuned|untuned|unfair|inadequate)|"
    r"(?:weak|outdated|untuned|non[- ]competitive) baseline|"
    r"not (?:tuned|optimized) (?:for|on) (?:the )?(?:baseline|baselines)|"
    r"different (?:backbone|architecture|training budget|data split|protocol|setting) (?:for|between) (?:the )?(?:baseline|baselines|methods))\b",
    re.IGNORECASE,
)
_PROTOCOL_RISK_QUOTE_RE = re.compile(
    r"\b(train[- ]test leakage|data leakage|test[- ]set leakage|label leakage|"
    r"oracle (?:information|access|features?|labels?)|"
    r"(?:tune|tuned|select|selected) (?:hyperparameters?|models?|checkpoints?) on (?:the )?test set|"
    r"(?:validation|test) split (?:is|was)?\s*(?:not specified|unclear|missing)|"
    r"unfair evaluation protocol|protocol (?:bias|risk|leakage|mismatch)|"
    r"metric (?:mismatch|does not match|is inappropriate|not appropriate)|"
    r"best(?:-| )case (?:selection|reporting)|cherry[- ]pick(?:ed|ing))\b",
    re.IGNORECASE,
)
_EFFICIENCY_SCOPE_CLAIM_RE = re.compile(
    r"\b(efficient|efficiency|scal(?:e|es|able|ability)|runtime|latency|"
    r"memory|parameters?|flops|compute|computational cost|cost-effective|practical)\b",
    re.IGNORECASE,
)
_EFFICIENCY_COST_QUOTE_RE = re.compile(
    r"\b(no (?:runtime|latency|memory|parameter|parameters|flops|compute|computational cost|efficiency) (?:analysis|evaluation|report|measurement|comparison)|"
    r"missing (?:runtime|latency|memory|parameter|parameters|flops|compute|computational cost|efficiency) (?:analysis|evaluation|report|measurement|comparison)|"
    r"(?:runtime|latency|memory|parameters?|flops|compute|computational cost|efficiency)[^.!?]{0,120}(?:not (?:reported|measured|provided|evaluated|compared)|missing|omitted)|"
    r"high (?:runtime|latency|memory|computational cost|compute cost)|computationally expensive|"
    r"requires? substantial compute|requires? large memory)\b",
    re.IGNORECASE,
)
_REPRO_SCOPE_CLAIM_RE = re.compile(
    r"\b(reproduc(?:e|ible|ibility)|implementation|hyperparameter|training detail|"
    r"code|open-source|release(?:d)?|data split|compute setup|method detail)\b",
    re.IGNORECASE,
)
_REPRO_SCOPE_QUOTE_RE = re.compile(
    r"\b(reproducibility|cannot reproduce|hard to reproduce|difficult to reproduce|"
    r"not release(?:d)? code|code (?:is )?not (?:available|released)|"
    r"implementation details?|hyperparameters?|training details?|data splits?|compute setup)\b",
    re.IGNORECASE,
)


def _promote_scope_limitation_for_broad_claim(negative_type: str, claim_text: str, raw_quote: str) -> str:
    if negative_type != "scope_limitation":
        return negative_type
    claim = str(claim_text or "")
    quote = str(raw_quote or "")
    if _BASELINE_FAIRNESS_CLAIM_RE.search(claim) and _UNFAIR_BASELINE_QUOTE_RE.search(quote):
        return "unfair_or_weak_baseline"
    if _PROTOCOL_RISK_QUOTE_RE.search(quote):
        return "evaluation_protocol_risk"
    if _ROBUSTNESS_SCOPE_CLAIM_RE.search(claim) and _ROBUSTNESS_GAP_QUOTE_RE.search(quote):
        return "missing_robustness_or_generalization"
    if _EFFICIENCY_SCOPE_CLAIM_RE.search(claim) and _EFFICIENCY_COST_QUOTE_RE.search(quote):
        return "efficiency_cost_gap"
    if _RESULT_SCOPE_CLAIM_RE.search(claim) and _RESULT_MISMATCH_SCOPE_QUOTE_RE.search(quote):
        return "result_claim_mismatch"
    if _EVAL_SCOPE_CLAIM_RE.search(claim) and _INSUFFICIENT_EVAL_SCOPE_QUOTE_RE.search(quote):
        return "insufficient_evaluation"
    if _REPRO_SCOPE_CLAIM_RE.search(claim) and _REPRO_SCOPE_QUOTE_RE.search(quote):
        return "reproducibility_gap"
    if _BROAD_CLAIM_RE.search(claim) and _SCOPE_LIMIT_QUOTE_RE.search(quote):
        return "scope_overclaim"
    return negative_type


def _readable_negative_type_for_runner(negative_type: str) -> str:
    value = str(negative_type or "").strip()
    return value.replace("_", " ") if value else "negative evidence"


def _compact_runner_text(value: str, *, max_length: int) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    return text[:max_length]


def _runner_text_tokens(text: str) -> set[str]:
    tokens = set()
    for token in re.findall(r"[a-z][a-z0-9_\-]{2,}", str(text or "").lower()):
        if token in {"the", "and", "for", "with", "that", "this", "from", "paper", "claim", "method", "model", "result", "results", "evidence"}:
            continue
        tokens.add(token.strip("-_"))
    return {token for token in tokens if len(token) >= 3}


def _runner_overlap_score(left: str, right: str) -> float:
    left_tokens = _runner_text_tokens(left)
    right_tokens = _runner_text_tokens(right)
    if not left_tokens or not right_tokens:
        return 0.0
    return len(left_tokens & right_tokens) / max(1, min(len(left_tokens), len(right_tokens), 20))


def _real_claim_ids_from_state(state: Optional[Dict[str, Any]]) -> List[str]:
    ids: List[str] = []
    for claim in (state or {}).get("claims", []) or []:
        if not isinstance(claim, dict):
            continue
        claim_id = str(claim.get("claim_id") or "").strip()
        if not claim_id or not _is_negative_binding_claim_target(claim):
            continue
        ids.append(claim_id)
    return list(dict.fromkeys(ids))


def _claim_text_lookup(state: Optional[Dict[str, Any]]) -> Dict[str, str]:
    lookup: Dict[str, str] = {}
    for claim in (state or {}).get("claims", []) or []:
        if not isinstance(claim, dict):
            continue
        claim_id = str(claim.get("claim_id") or "").strip()
        if claim_id:
            lookup[claim_id] = str(claim.get("claim") or claim.get("text") or "")
    return lookup


def _target_flaw_text(manager_payload: Dict[str, Any], state: Optional[Dict[str, Any]]) -> str:
    target_ids = {str(item or "").strip() for item in (manager_payload or {}).get("target_flaw_ids", []) or [] if str(item or "").strip()}
    if not target_ids:
        return ""
    parts: List[str] = []
    for flaw in (state or {}).get("flaw_candidates", []) or []:
        if isinstance(flaw, dict) and str(flaw.get("flaw_id") or "").strip() in target_ids:
            parts.append(str(flaw.get("flaw") or flaw.get("description") or flaw.get("weakness") or ""))
    return " ".join(parts)


def _quote_bank_from_state_or_meta(state: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    meta = (state or {}).get("_latest_evidence_context_meta") or {}
    entries: List[Dict[str, Any]] = []
    for source in (
        meta.get("evidence_quote_bank", []) if isinstance(meta, dict) else [],
        meta.get("critique_negative_quote_bank", []) if isinstance(meta, dict) else [],
        (state or {}).get("evidence_quote_bank", []),
        (state or {}).get("critique_negative_quote_bank", []),
    ):
        entries.extend(item for item in source or [] if isinstance(item, dict))
    deduped: List[Dict[str, Any]] = []
    seen: set[str] = set()
    for item in entries:
        key = str(item.get("quote_id") or item.get("raw_quote") or "")
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped


def _runner_quote_bank_dedupe_key(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "").strip().lower())


def _negative_quote_bank_grounded_quote_ids(
    payload_items: Sequence[Dict[str, Any]],
    state: Optional[Dict[str, Any]],
) -> set[str]:
    negative_entries = []
    for item in _quote_bank_from_state_or_meta(state):
        if str(item.get("source_bucket") or "") != "negative_or_gap":
            continue
        neg_type = _negative_quote_entry_type(item)
        if neg_type in {"generic_gap", "neutral_control_context", "bibliographic_or_title_noise", "neutral_instruction_noise"}:
            continue
        negative_entries.append(item)
    negative_quote_ids = {
        str(item.get("quote_id") or "").strip()
        for item in negative_entries
        if str(item.get("quote_id") or "").strip()
    }
    negative_quote_raw_to_id = {
        _runner_quote_bank_dedupe_key(str(item.get("raw_quote") or "")): str(item.get("quote_id") or "").strip()
        for item in negative_entries
        if str(item.get("raw_quote") or "").strip() and str(item.get("quote_id") or "").strip()
    }
    grounded_ids: set[str] = set()
    for item in payload_items or []:
        if not isinstance(item, dict):
            continue
        quote_id = str(item.get("quote_id") or "").strip()
        if quote_id and quote_id in negative_quote_ids:
            grounded_ids.add(quote_id)
            continue
        source_bucket = str(item.get("support_source_bucket") or item.get("verified_source_bucket") or "").strip()
        raw_quote = str(item.get("raw_quote") or item.get("evidence") or "")
        raw_key = _runner_quote_bank_dedupe_key(raw_quote)
        if source_bucket in {"limitation_or_gap", "negative_or_gap"} and raw_key in negative_quote_raw_to_id:
            grounded_ids.add(negative_quote_raw_to_id[raw_key])
    return grounded_ids


def _select_negative_quote_bank_entries(
    state: Optional[Dict[str, Any]],
    manager_payload: Dict[str, Any],
    *,
    max_entries: int = 1,
    exclude_quote_ids: Optional[set[str]] = None,
) -> List[Dict[str, Any]]:
    quote_bank = _quote_bank_from_state_or_meta(state)
    target_text = " ".join([
        _target_flaw_text(manager_payload, state),
        " ".join(_claim_text_lookup(state).get(str(item or ""), "") for item in (manager_payload or {}).get("target_claim_ids", []) or []),
    ]).strip()
    excluded = {str(item or "").strip() for item in (exclude_quote_ids or set()) if str(item or "").strip()}
    candidates = []
    for item in quote_bank:
        quote_id = str(item.get("quote_id") or "").strip()
        if quote_id and quote_id in excluded:
            continue
        source_bucket = str(item.get("source_bucket") or "")
        raw_quote = str(item.get("raw_quote") or "").strip()
        if not raw_quote:
            continue
        neg_type = _negative_quote_entry_type(item)
        if neg_type in {"neutral_control_context", "bibliographic_or_title_noise", "neutral_instruction_noise"}:
            continue
        explicit_typed_negative = (
            source_bucket == "negative_or_gap"
            and neg_type in (_ACTIONABLE_NEGATIVE_EVIDENCE_TYPES | _LIMITATION_NEGATIVE_EVIDENCE_TYPES)
            and neg_type != "generic_gap"
        )
        if not explicit_typed_negative and not _NEGATIVE_QUOTE_ANCHOR_RE.search(raw_quote):
            continue
        if source_bucket == "abstract":
            continue
        explicit_negative_bucket = source_bucket == "negative_or_gap"
        if explicit_negative_bucket and neg_type == "generic_gap":
            continue
        if not explicit_negative_bucket and neg_type in {"generic_gap", "neutral_control_context"}:
            # Non-abstract quotes with negative terms are useful to ground an
            # assessment limitation, but not enough for claim-status downgrade.
            item = dict(item)
            item.setdefault("negative_evidence_type", "scope_limitation")
            item["negative_quote_bank_inferred_from_anchor"] = True
            neg_type = _negative_quote_entry_type(item)
        score = _runner_overlap_score(target_text, raw_quote) if target_text else 0.0
        scope_specificity = 1 if neg_type in _LIMITATION_NEGATIVE_EVIDENCE_TYPES and _CONCRETE_SCOPE_LIMIT_QUOTE_RE.search(raw_quote) else 0
        # Lower type rank is better: concrete paper flaws / claim-support
        # failures first, claim-aware scope-overclaim next, old limitation/gap
        # evidence only as fallback.  Within the same class, prefer target
        # overlap and concrete locators.
        type_rank = _negative_evidence_type_priority(neg_type)
        candidates.append((type_rank, -scope_specificity, -score, item))
    if not candidates:
        return []
    candidates.sort(key=lambda pair: (pair[0], pair[1], pair[2]))
    selected: List[Dict[str, Any]] = []
    seen_quote_ids: set[str] = set()
    seen_raw_keys: set[str] = set()
    ordered_items: List[Dict[str, Any]] = []
    used_types: set[str] = set()
    for _, _, _, item in candidates:
        neg_type = _negative_quote_entry_type(item)
        if neg_type in used_types:
            continue
        used_types.add(neg_type)
        ordered_items.append(item)
    ordered_items.extend(item for _, _, _, item in candidates if item not in ordered_items)
    for item in ordered_items:
        quote_id = str(item.get("quote_id") or "").strip()
        raw_key = _runner_quote_bank_dedupe_key(str(item.get("raw_quote") or ""))
        if quote_id and quote_id in seen_quote_ids:
            continue
        if raw_key and raw_key in seen_raw_keys:
            continue
        if quote_id:
            seen_quote_ids.add(quote_id)
        if raw_key:
            seen_raw_keys.add(raw_key)
        selected.append(item)
        if len(selected) >= max_entries:
            break
    return selected


def _select_negative_quote_bank_entry(state: Optional[Dict[str, Any]], manager_payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    entries = _select_negative_quote_bank_entries(state, manager_payload, max_entries=1)
    return entries[0] if entries else None


def _select_negative_quote_target_claim(state: Optional[Dict[str, Any]], manager_payload: Dict[str, Any], quote: str) -> str:
    real_ids = _real_claim_ids_from_state(state)
    target_ids: List[str] = []
    for field in ("target_claim_ids", "raw_target_claim_ids", "final_action_target_claim_ids", "post_sanitize_target_claim_ids"):
        target_ids.extend(str(item or "").strip() for item in (manager_payload or {}).get(field, []) or [] if str(item or "").strip())
    preferred = [claim_id for claim_id in dict.fromkeys(target_ids) if claim_id in real_ids]
    claim_texts = _claim_text_lookup(state)
    pool = preferred or real_ids
    if not pool:
        return ""
    return max(pool, key=lambda claim_id: _runner_overlap_score(claim_texts.get(claim_id, ""), quote))




def _payload_has_negative_quote_bank_grounding(payload_items: Sequence[Dict[str, Any]], state: Optional[Dict[str, Any]]) -> bool:
    return bool(_negative_quote_bank_grounded_quote_ids(payload_items, state))

def _negative_salvage_target_flaw_updates(
    manager_payload: Dict[str, Any],
    evidence_id: str,
    claim_id: str = "",
    quote_id: str = "",
    negative_evidence_type: str = "generic_gap",
    claim_text: str = "",
    raw_quote: str = "",
    source_locator: str = "",
) -> List[Dict[str, Any]]:
    updates: List[Dict[str, Any]] = []
    actionable = negative_evidence_type in _ACTIONABLE_NEGATIVE_EVIDENCE_TYPES
    severity = "major" if actionable else "minor"
    grounding_status = "review_negative_candidate" if actionable else "quote_candidate_needs_review_relation"
    readable_type = _readable_negative_type_for_runner(negative_evidence_type)
    compact_claim = _compact_runner_text(claim_text, max_length=140)
    compact_quote = _compact_runner_text(raw_quote, max_length=220)
    compact_locator = _compact_runner_text(source_locator, max_length=80)
    if "excerpt" in compact_locator.lower():
        compact_locator = ""
    if compact_claim and compact_quote:
        quote_prefix = f"{compact_locator} reports" if compact_locator else "paper quote reports"
        flaw_text = (
            f"Candidate {readable_type} quote for claim '{compact_claim}': "
            f"{quote_prefix} '{compact_quote}'. Keep only if review-semantic verification shows a current-paper weakness."
        )
    elif negative_evidence_type == "direct_contradiction":
        flaw_text = "Candidate paper quote may contradict or invalidate a target claim; keep only after review-semantic verification."
    elif negative_evidence_type == "negative_result":
        flaw_text = "Candidate paper quote reports a negative or weaker result; keep only if it weakens the target claim."
    elif negative_evidence_type == "missing_ablation":
        flaw_text = "Candidate paper quote may indicate a missing comparison, baseline, evaluation, or ablation relevant to the target claim."
    elif negative_evidence_type == "unfair_or_weak_baseline":
        flaw_text = "Candidate paper quote may indicate the baseline or comparison protocol is weak, unfair, untuned, or non-competitive for the target claim."
    elif negative_evidence_type == "missing_robustness_or_generalization":
        flaw_text = "Candidate paper quote may indicate missing or limited robustness, transfer, out-of-domain, or generalization evaluation for the target claim."
    elif negative_evidence_type == "evaluation_protocol_risk":
        flaw_text = "Candidate paper quote may indicate an evaluation protocol risk, such as leakage, oracle information, metric mismatch, or unfair selection."
    elif negative_evidence_type == "efficiency_cost_gap":
        flaw_text = "Candidate paper quote may indicate missing or adverse runtime, memory, latency, parameter, FLOP, or compute-cost evidence for the target claim."
    elif negative_evidence_type == "scope_overclaim":
        flaw_text = "Candidate paper quote may narrow the scope of a broad target claim; keep only if it directly weakens that claim."
    elif negative_evidence_type == "result_claim_mismatch":
        flaw_text = "Candidate paper quote may suggest the reported result is weaker than the target claim."
    else:
        flaw_text = "Target flaw has a negative-looking quote candidate; keep it candidate-only until review-semantic verification confirms a paper weakness."
    for raw in (manager_payload or {}).get("target_flaw_ids", []) or []:
        flaw_id = str(raw or "").strip()
        if not flaw_id:
            continue
        updates.append({
            "flaw_id": flaw_id,
            "flaw": flaw_text,
            "status": "candidate",
            "severity": severity,
            "related_claim_ids": [claim_id] if claim_id else [],
            "evidence_ids": [evidence_id],
            "negative_evidence_ids": [evidence_id],
            "grounding_status": grounding_status,
            "negative_evidence_type": negative_evidence_type,
            "source": "quote-bank-negative-grounding",
        })
    if not updates and evidence_id:
        safe_quote = re.sub(r"[^a-zA-Z0-9_-]+", "-", quote_id or evidence_id).strip("-") or "negative-quote"
        updates.append({
            "flaw_id": f"flaw-negative-quote-bank-{safe_quote}",
            "flaw": flaw_text,
            "status": "candidate",
            "severity": severity,
            "related_claim_ids": [claim_id] if claim_id else [],
            "evidence_ids": [evidence_id],
            "negative_evidence_ids": [evidence_id],
            "grounding_status": grounding_status,
            "negative_evidence_type": negative_evidence_type,
            "source": "quote-bank-negative-grounding",
        })
    return updates


def _negative_quote_bank_salvage_payload(
    state: Optional[Dict[str, Any]],
    manager_payload: Dict[str, Any],
    existing_count: int,
    entry_override: Optional[Dict[str, Any]] = None,
) -> Optional[Dict[str, Any]]:
    entry = entry_override if isinstance(entry_override, dict) else _select_negative_quote_bank_entry(state, manager_payload)
    if not entry:
        return None
    raw_quote = str(entry.get("raw_quote") or "").strip()
    claim_id = _select_negative_quote_target_claim(state, manager_payload, raw_quote)
    if not raw_quote or not claim_id:
        return None
    quote_id = str(entry.get("quote_id") or "negative-gap").strip()
    negative_evidence_type = _negative_quote_entry_type(entry)
    claim_text = _claim_text_lookup(state).get(claim_id, "")
    negative_evidence_type = _promote_scope_limitation_for_broad_claim(
        negative_evidence_type,
        claim_text,
        raw_quote,
    )
    source_bucket = str(entry.get("source_bucket") or "").strip()
    claim_status_downgrade_allowed = (
        source_bucket == "negative_or_gap"
        and negative_evidence_type in {"direct_contradiction", "negative_result"}
    )
    safe_quote_id = re.sub(r"[^a-zA-Z0-9_-]+", "-", quote_id).strip("-") or "negative-gap"
    evidence_id = f"evidence-negative-quote-bank-{safe_quote_id}-{existing_count + 1}"
    return {
        "evidence_id": evidence_id,
        "claim_id": claim_id,
        "evidence": (
            "Candidate paper quote for review-negative checking: "
            f"{raw_quote[:220]}"
        ),
        "source": "quote-bank-negative-grounding",
        "source_locator": str(entry.get("source_locator") or "Limitation / Gap quote"),
        "raw_quote": raw_quote,
        "quote_id": quote_id,
        "stance": "missing",
        "strength": "missing",
        "support_source_bucket": "limitation_or_gap",
        "verified_source_bucket": source_bucket,
        "negative_evidence_type": negative_evidence_type,
        "negative_evidence_actionability": "actionable_candidate" if negative_evidence_type in _ACTIONABLE_NEGATIVE_EVIDENCE_TYPES else "assessment_limitation",
        "claim_status_downgrade_allowed": claim_status_downgrade_allowed,
        "binding_status": "bound_real_claim",
        "binding_confidence": 0.72,
        "binding_rationale": "Deterministic candidate from program-extracted negative_or_gap quote bank; review-semantic verification is required before it counts as negative evidence.",
        "negative_quote_bank_salvage_status": "candidate_needs_review_relation",
        "grounded_judge_label": "paper_grounded",
        "grounded_judge_reason": "Quote was copied from the ReviewState evidence quote bank; semantic verification is applied during state merge.",
    }


def _is_verified_negative_evidence_for_recovery(item: Dict[str, Any]) -> bool:
    semantic_label = str(item.get("semantic_grounding_label") or "").strip()
    if not (
        isinstance(item, dict)
        and str(item.get("stance") or "").strip().lower() in _NEGATIVE_RECOVERY_STANCES
        and str(item.get("verified_grounding_label") or "") in _VERIFIED_RECOVERY_LABELS
        and semantic_label == "semantic_negative_verified"
    ):
        return False
    review_label = str(item.get("review_negative_label") or "").strip()
    if review_label:
        return review_label == REVIEW_NEGATIVE_VERIFIED_LABEL
    source = str(item.get("source") or "").strip().lower()
    has_quote_material = bool(str(item.get("raw_quote") or "").strip() or str(item.get("quote_id") or "").strip())
    if source == "quote-bank-negative-grounding" or has_quote_material or item.get("review_negative_checked"):
        return False
    return True


def _is_obligation_grounded_review_issue_for_recovery(item: Dict[str, Any]) -> bool:
    if not isinstance(item, dict):
        return False
    return (
        str(item.get("review_issue_source") or "").strip() == "obligation_grounded_review_issue"
        or str(item.get("review_issue_verification_status") or "").strip() == "verified_review_issue"
        or str(item.get("verified_grounding_label") or "").strip() == "paper_absence_audit_verified"
        or str(item.get("review_negative_label") or "").strip() == "review_negative_absence_audit_verified"
        or str(item.get("source") or "").strip() == "reviewer_absence_audit"
    )


def _allows_claim_status_downgrade_from_recovery(item: Dict[str, Any]) -> bool:
    """Only direct verified negative evidence can downgrade a claim.

    Program-salvaged quote-bank gap evidence is useful for grounded concerns,
    but it is too broad to prove that a paper claim itself is unsupported.
    Treat it as flaw/limitation grounding unless a future extractor marks it
    as direct claim-negative evidence.
    """
    if _is_obligation_grounded_review_issue_for_recovery(item):
        return False
    if not _is_verified_negative_evidence_for_recovery(item):
        return False
    source = str(item.get("source") or "").strip().lower()
    if source == "quote-bank-negative-grounding":
        return bool(item.get("claim_status_downgrade_allowed")) and _negative_evidence_record_is_actionable(item)
    stance = str(item.get("stance") or "").strip().lower()
    return stance in {"contradicts", "refutes", "missing", "unsupported"}


def _is_synthetic_recovery_evidence(item: Dict[str, Any]) -> bool:
    """Recognize program-emitted placeholder evidence (no real paper grounding).

    Synthetic markers are emitted by the recovery salvage path and the negative
    quote-bank fallback to keep ReviewState consistent. They share `stance == "missing"`
    AND `strength == "missing"` and a known synthetic source. Treat them as
    non-evidence for purposes of deciding whether Critique Agent should be
    asked to challenge a manager-sanitized claim.
    """
    if not isinstance(item, dict):
        return True
    stance = str(item.get("stance") or "").strip().lower()
    strength = str(item.get("strength") or "").strip().lower()
    if stance != "missing" or strength != "missing":
        return False
    source = str(item.get("source") or "").strip().lower()
    return source in {"system recovery salvage", "quote-bank-negative-grounding"}


def _claim_has_real_evidence_for_recovery(state: Dict[str, Any], claim_id: str) -> bool:
    """Return True if the claim has at least one non-synthetic evidence binding."""
    target = str(claim_id or "").strip()
    if not target:
        return False
    for item in state.get("evidence_map", []) or []:
        if not isinstance(item, dict):
            continue
        if str(item.get("claim_id") or "").strip() != target:
            continue
        if _is_synthetic_recovery_evidence(item):
            continue
        return True
    return False


def _flaw_has_verified_negative_evidence_for_recovery(flaw: Dict[str, Any], evidence_lookup: Dict[str, Dict[str, Any]]) -> bool:
    return bool(_flaw_verified_negative_evidence_ids_for_recovery(flaw, evidence_lookup))


def _flaw_verified_negative_evidence_ids_for_recovery(
    flaw: Dict[str, Any],
    evidence_lookup: Dict[str, Dict[str, Any]],
    *,
    quote_bank_only: bool = False,
) -> List[str]:
    evidence_ids: List[str] = []
    for raw in list(flaw.get("negative_evidence_ids") or []) + list(flaw.get("evidence_ids") or []):
        item = evidence_lookup.get(str(raw or ""))
        if not item or not _is_verified_negative_evidence_for_recovery(item):
            continue
        if quote_bank_only and str(item.get("source") or "").strip().lower() != "quote-bank-negative-grounding":
            continue
        evidence_id = str(item.get("evidence_id") or "").strip()
        if evidence_id and evidence_id not in evidence_ids:
            evidence_ids.append(evidence_id)
    return evidence_ids


def _claim_downgrade_patch_from_actionable_flaw(
    flaw: Dict[str, Any],
    claim_lookup: Dict[str, Dict[str, Any]],
    evidence_lookup: Dict[str, Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    if not isinstance(flaw, dict):
        return None
    actionable_ids = [
        evidence_id
        for evidence_id in _flaw_verified_negative_evidence_ids_for_recovery(flaw, evidence_lookup)
        if _allows_claim_status_downgrade_from_recovery(evidence_lookup.get(evidence_id, {}))
    ]
    if not actionable_ids:
        return None
    candidate_claim_ids: List[str] = []
    for evidence_id in actionable_ids:
        claim_id = str((evidence_lookup.get(evidence_id) or {}).get("claim_id") or "").strip()
        if claim_id:
            candidate_claim_ids.append(claim_id)
    candidate_claim_ids.extend(
        str(item or "").strip()
        for item in flaw.get("related_claim_ids") or []
        if str(item or "").strip()
    )
    for claim_id in dict.fromkeys(candidate_claim_ids):
        claim = claim_lookup.get(claim_id)
        if not _is_recovery_claim_status_target(claim or {}):
            continue
        old_status = str((claim or {}).get("status") or "uncertain").strip().lower()
        if old_status not in {"supported", "partially_supported", "uncertain"}:
            continue
        if _verified_positive_support_ids_for_claim(claim or {}, evidence_lookup):
            continue
        supporting_ids = [
            evidence_id
            for evidence_id in actionable_ids
            if str((evidence_lookup.get(evidence_id) or {}).get("claim_id") or "").strip() == claim_id
        ]
        if not supporting_ids:
            continue
        return normalize_review_update_payload(
            {
                "action": "apply_recovery_patch",
                "target_type": "claim",
                "target_id": claim_id,
                "old_status": old_status,
                "new_status": "unsupported",
                "supporting_evidence_ids": supporting_ids[:2],
                "reason_for_change": (
                    "Verified actionable negative evidence directly contests this real claim; "
                    "recovery marks it contested instead of routing the concern to an assessment limitation."
                ),
                "resolution_expectation": "partially_resolved",
                "confidence": 0.58,
            }
        )
    return None


def _verified_positive_support_ids_for_claim(
    claim: Dict[str, Any],
    evidence_lookup: Dict[str, Dict[str, Any]],
) -> List[str]:
    claim_id = str((claim or {}).get("claim_id") or "").strip()
    if not claim_id:
        return []
    candidate_ids: List[str] = [
        str(item or "").strip()
        for item in (claim or {}).get("supporting_evidence_ids", []) or []
        if str(item or "").strip()
    ]
    candidate_ids.extend(
        str(item.get("evidence_id") or "").strip()
        for item in evidence_lookup.values()
        if isinstance(item, dict) and str(item.get("claim_id") or "").strip() == claim_id
    )
    support_ids: List[str] = []
    for evidence_id in dict.fromkeys(candidate_ids):
        item = evidence_lookup.get(evidence_id)
        if not isinstance(item, dict):
            continue
        stance = str(item.get("stance") or "").strip().lower()
        grounding = str(item.get("verified_grounding_label") or "").strip()
        semantic = str(item.get("semantic_grounding_label") or "").strip()
        if (
            stance in {"supports", "partially_supports"}
            and grounding in _VERIFIED_RECOVERY_LABELS
            and semantic == "semantic_support_verified"
        ):
            support_ids.append(evidence_id)
    return support_ids


def _contested_relation_already_exists(
    state: Optional[Dict[str, Any]],
    claim_id: str,
    negative_evidence_ids: Sequence[str],
) -> bool:
    claim_id = str(claim_id or "").strip()
    negative_key = tuple(
        str(item or "").strip()
        for item in (negative_evidence_ids or [])
        if str(item or "").strip()
    )
    if not claim_id or not negative_key:
        return False
    for relation in (state or {}).get("contested_relations", []) or []:
        if not isinstance(relation, dict):
            continue
        if str(relation.get("claim_id") or "").strip() != claim_id:
            continue
        existing_key = tuple(
            str(item or "").strip()
            for item in relation.get("negative_evidence_ids", []) or []
            if str(item or "").strip()
        )
        if existing_key == negative_key:
            return True
    return False


def _mark_contested_patch_from_verified_negative_flaw(
    flaw: Dict[str, Any],
    claim_lookup: Dict[str, Dict[str, Any]],
    evidence_lookup: Dict[str, Dict[str, Any]],
    state: Optional[Dict[str, Any]] = None,
) -> Optional[Dict[str, Any]]:
    if not isinstance(flaw, dict):
        return None
    verified_negative_ids = _flaw_verified_negative_evidence_ids_for_recovery(flaw, evidence_lookup)
    if not verified_negative_ids:
        return None
    candidate_claim_ids: List[str] = []
    for evidence_id in verified_negative_ids:
        claim_id = str((evidence_lookup.get(evidence_id) or {}).get("claim_id") or "").strip()
        if claim_id:
            candidate_claim_ids.append(claim_id)
    candidate_claim_ids.extend(
        str(item or "").strip()
        for item in flaw.get("related_claim_ids") or []
        if str(item or "").strip()
    )
    for claim_id in dict.fromkeys(candidate_claim_ids):
        claim = claim_lookup.get(claim_id)
        if not _is_recovery_contested_claim_target(claim or {}):
            continue
        old_status = str((claim or {}).get("status") or "uncertain").strip().lower()
        if old_status not in {"supported", "partially_supported", "uncertain"}:
            continue
        aligned_negative_ids = [
            evidence_id
            for evidence_id in verified_negative_ids
            if str((evidence_lookup.get(evidence_id) or {}).get("claim_id") or "").strip() == claim_id
        ]
        if not aligned_negative_ids:
            continue
        if _contested_relation_already_exists(state, claim_id, aligned_negative_ids[:4]):
            continue
        support_ids = _verified_positive_support_ids_for_claim(claim or {}, evidence_lookup)
        if not support_ids:
            continue
        flaw_id = str(flaw.get("flaw_id") or "").strip()
        if not flaw_id:
            continue
        flaw_status = str(flaw.get("status") or "candidate").strip().lower() or "candidate"
        return normalize_review_update_payload(
            {
                "action": "apply_recovery_patch",
                "target_type": "flaw",
                "target_id": flaw_id,
                "old_status": flaw_status,
                "new_status": flaw_status,
                "supporting_evidence_ids": aligned_negative_ids[:2],
                "reason_for_change": (
                    "Verified paper-negative evidence contests a claim that also has verified positive support; "
                    "recovery records a contested relation from the flaw target without downgrading claim status."
                ),
                "resolution_expectation": "partially_resolved",
                "confidence": 0.6,
                "recovery_patch_operation": "mark_contested",
                "mark_contested": True,
                "contested_relation": {
                    "claim_id": claim_id,
                    "support_evidence_ids": support_ids[:4],
                    "negative_evidence_ids": aligned_negative_ids[:4],
                    "final_view": "potential_concern",
                },
            }
        )
    return None


def _flaw_contested_relation_already_exists(
    flaw: Dict[str, Any],
    state: Optional[Dict[str, Any]],
    evidence_lookup: Dict[str, Dict[str, Any]],
) -> bool:
    verified_negative_ids = _flaw_verified_negative_evidence_ids_for_recovery(flaw, evidence_lookup)
    if not verified_negative_ids:
        return False
    candidate_claim_ids: List[str] = []
    for evidence_id in verified_negative_ids:
        claim_id = str((evidence_lookup.get(evidence_id) or {}).get("claim_id") or "").strip()
        if claim_id:
            candidate_claim_ids.append(claim_id)
    candidate_claim_ids.extend(
        str(item or "").strip()
        for item in flaw.get("related_claim_ids") or []
        if str(item or "").strip()
    )
    for claim_id in dict.fromkeys(candidate_claim_ids):
        aligned_negative_ids = [
            evidence_id
            for evidence_id in verified_negative_ids
            if str((evidence_lookup.get(evidence_id) or {}).get("claim_id") or "").strip() == claim_id
        ]
        if aligned_negative_ids and _contested_relation_already_exists(state, claim_id, aligned_negative_ids[:4]):
            return True
    return False


def _protected_potential_concern_blocked_payload(flaw_id: str) -> Dict[str, Any]:
    payload = normalize_review_update_payload(
        {
            "action": "blocked",
            "target_type": "flaw",
            "target_id": flaw_id,
            "blocked_reason": _PROTECTED_POTENTIAL_CONCERN_BLOCKED_REASON,
            "missing_requirements": ["confirmed flaw status or claim-level downgrade evidence"],
            "recovery_terminal": True,
            "recovery_terminal_reason": _PROTECTED_POTENTIAL_CONCERN_TERMINAL_REASON,
            "recovery_repeat_allowed": False,
        }
    )
    payload["recovery_terminal"] = True
    payload["recovery_terminal_reason"] = _PROTECTED_POTENTIAL_CONCERN_TERMINAL_REASON
    payload["recovery_repeat_allowed"] = False
    return payload


def _recent_terminal_recovery_flaw_ids(recent_turn_logs: Optional[Sequence[Dict[str, Any]]], *, window: int = 8) -> set[str]:
    terminal_ids: set[str] = set()
    for turn in list(recent_turn_logs or [])[-window:]:
        target_type = str(turn.get("recovery_target_type") or "").strip().lower()
        target_id = str(turn.get("recovery_target_id") or "").strip()
        if target_type != "flaw" or not target_id:
            continue
        terminal_reason = str(turn.get("recovery_terminal_reason") or "").strip()
        failure_code = str(turn.get("recovery_failure_code") or "").strip()
        blocked_message = str(turn.get("recovery_failure_message") or turn.get("recovery_blocked_by") or "").lower()
        terminal = bool(turn.get("recovery_terminal"))
        if (
            terminal
            or terminal_reason == _PROTECTED_POTENTIAL_CONCERN_TERMINAL_REASON
            or terminal_reason == _ASSESSMENT_LIMITATION_NO_EFFECT_TERMINAL_REASON
            or failure_code == "ACTIONABLE_CONCERN_PRESERVED"
            or "final potential concern" in blocked_message
            or "already represented as an assessment limitation" in blocked_message
        ):
            terminal_ids.add(target_id)
    return terminal_ids


def _recovery_candidate_flaw_ids(
    state: Dict[str, Any],
    recent_turn_logs: Optional[Sequence[Dict[str, Any]]] = None,
    *,
    limit: int = 4,
) -> List[str]:
    terminal_flaw_ids = _recent_terminal_recovery_flaw_ids(recent_turn_logs)
    evidence_lookup = {
        str(item.get("evidence_id") or ""): item
        for item in state.get("evidence_map", []) or []
        if isinstance(item, dict) and item.get("evidence_id")
    }
    confirmed_actionable_candidates: List[str] = []
    actionable_candidates: List[str] = []
    unverified_candidates: List[str] = []
    verified_candidates: List[str] = []
    for flaw in state.get("flaw_candidates", []) or []:
        if not isinstance(flaw, dict):
            continue
        flaw_id = str(flaw.get("flaw_id") or "").strip()
        status = str(flaw.get("status") or "candidate").strip().lower()
        if not flaw_id or status not in {"candidate", "confirmed"}:
            continue
        if flaw_id in terminal_flaw_ids:
            continue
        verified_evidence_ids = _flaw_verified_negative_evidence_ids_for_recovery(flaw, evidence_lookup)
        if any(_allows_claim_status_downgrade_from_recovery(evidence_lookup.get(evidence_id, {})) for evidence_id in verified_evidence_ids):
            if status == "confirmed":
                confirmed_actionable_candidates.append(flaw_id)
                continue
            actionable_candidates.append(flaw_id)
        elif verified_evidence_ids:
            verified_candidates.append(flaw_id)
        else:
            unverified_candidates.append(flaw_id)
    candidates = confirmed_actionable_candidates + actionable_candidates + unverified_candidates + verified_candidates
    return list(dict.fromkeys(candidates))[:limit]


def _recovery_lifecycle_claim_ids(state: Dict[str, Any], *, limit: int = 2) -> List[str]:
    claim_lookup = {
        str(item.get("claim_id") or "").strip(): item
        for item in state.get("claims", []) or []
        if isinstance(item, dict) and str(item.get("claim_id") or "").strip()
    }
    evidence_lookup = {
        str(item.get("evidence_id") or ""): item
        for item in state.get("evidence_map", []) or []
        if isinstance(item, dict) and item.get("evidence_id")
    }
    selected: List[str] = []
    for flaw in state.get("flaw_candidates", []) or []:
        if not isinstance(flaw, dict):
            continue
        status = str(flaw.get("status") or "candidate").strip().lower()
        if status not in {"candidate", "confirmed"}:
            continue
        if not _flaw_verified_negative_evidence_ids_for_recovery(flaw, evidence_lookup):
            continue
        for raw in flaw.get("related_claim_ids") or []:
            claim_id = str(raw or "").strip()
            if not _is_recovery_claim_status_target(claim_lookup.get(claim_id, {})):
                continue
            if claim_id not in selected:
                selected.append(claim_id)
            if len(selected) >= limit:
                return selected
    return selected


def _recovery_candidate_flaw_evidence_ids(state: Dict[str, Any], target_flaw_ids: Sequence[str]) -> List[str]:
    target_set = {str(item).strip() for item in target_flaw_ids or [] if str(item).strip()}
    ids: List[str] = []
    for flaw in state.get("flaw_candidates", []) or []:
        if not isinstance(flaw, dict) or str(flaw.get("flaw_id") or "") not in target_set:
            continue
        for raw in flaw.get("evidence_ids") or []:
            if raw:
                ids.append(str(raw))
    return list(dict.fromkeys(ids))[:4]


def _ensure_recovery_targets(
    manager_payload: Dict[str, Any],
    state: Dict[str, Any],
    mode: str,
    recovery_action: str,
    recent_turn_logs: Sequence[Dict[str, Any]],
) -> Dict[str, Any]:
    normalized = manager_payload
    inferred_payload = _infer_action_from_state(mode, state, recent_turn_logs) or {}
    claim_lookup = {
        str(item.get("claim_id") or "").strip(): item
        for item in state.get("claims", []) or []
        if isinstance(item, dict) and str(item.get("claim_id") or "").strip()
    }
    if recovery_action == "request_evidence_recheck":
        current_claim_ids = [str(item).strip() for item in normalized.get("target_claim_ids", []) or [] if str(item).strip()]
        filtered_claim_ids = [
            claim_id
            for claim_id in current_claim_ids
            if _is_recovery_strong_claim_target(claim_lookup.get(claim_id, {}))
        ]
        normalized["target_claim_ids"] = filtered_claim_ids[:3]
    if recovery_action == "challenge_previous_hypothesis":
        viable_claim_ids = set(_recovery_candidate_claim_ids(state, recovery_action))
        current_claim_ids = [str(item).strip() for item in normalized.get("target_claim_ids", []) or [] if str(item).strip()]
        terminal_flaw_ids = _recent_terminal_recovery_flaw_ids(recent_turn_logs)
        if terminal_flaw_ids and normalized.get("target_flaw_ids"):
            normalized["target_flaw_ids"] = [
                str(item).strip()
                for item in normalized.get("target_flaw_ids", []) or []
                if str(item).strip() and str(item).strip() not in terminal_flaw_ids
            ]
        if current_claim_ids:
            filtered = [claim_id for claim_id in current_claim_ids if claim_id in viable_claim_ids]
            if filtered:
                normalized["target_claim_ids"] = filtered
            else:
                # The negative-evidence viability filter dropped every manager-sanitized
                # claim. Retain the subset that still has real (non-synthetic) evidence
                # in ReviewState. Upstream sanitize already validated these IDs as real
                # claims, and emptying them would force Critique Agent to block on
                # "missing target claim ID" even though upstream policy intentionally
                # chose them. Synthetic recovery-salvage missing markers are excluded so
                # claims whose only "evidence" is a placeholder cannot be challenged.
                with_real_evidence = [
                    claim_id
                    for claim_id in current_claim_ids
                    if _is_recovery_claim_status_target(claim_lookup.get(claim_id, {}))
                    if _claim_has_real_evidence_for_recovery(state, claim_id)
                ]
                normalized["target_claim_ids"] = with_real_evidence
    if not normalized.get("target_claim_ids"):
        target_claim_ids = list(inferred_payload.get("target_claim_ids", []) or [])
        if recovery_action == "request_evidence_recheck":
            target_claim_ids = [
                claim_id
                for claim_id in target_claim_ids
                if _is_recovery_strong_claim_target(claim_lookup.get(str(claim_id).strip(), {}))
            ]
        if recovery_action == "challenge_previous_hypothesis":
            viable_claim_ids = set(_recovery_candidate_claim_ids(state, recovery_action))
            target_claim_ids = [claim_id for claim_id in target_claim_ids if claim_id in viable_claim_ids]
        if not target_claim_ids:
            target_claim_ids = _recovery_candidate_claim_ids(state, recovery_action)
        if target_claim_ids:
            normalized["target_claim_ids"] = target_claim_ids
    if recovery_action == "challenge_previous_hypothesis" and not normalized.get("target_flaw_ids"):
        target_flaw_ids = _recovery_candidate_flaw_ids(state, recent_turn_logs)
        if target_flaw_ids:
            normalized["target_flaw_ids"] = target_flaw_ids
    if recovery_action == "challenge_previous_hypothesis" and not normalized.get("target_evidence_ids"):
        target_evidence_ids = _recovery_candidate_evidence_ids(state, normalized.get("target_claim_ids", []))
        if not target_evidence_ids:
            target_evidence_ids = _recovery_candidate_flaw_evidence_ids(state, normalized.get("target_flaw_ids", []))
        if target_evidence_ids:
            normalized["target_evidence_ids"] = target_evidence_ids
    return normalized


def _apply_recovery_phase_protocol(
    manager_payload: Dict[str, Any],
    state: Dict[str, Any],
    mode: str,
    worker_ids: Sequence[str],
    worker_limit: int,
    recent_turn_logs: Optional[Sequence[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    normalized = dict(manager_payload or {})
    recent_turn_logs = list(recent_turn_logs or [])
    previous_phase = _normalize_phase(state.get("phase")) or "normal_review"
    existing_phase = _normalize_phase(normalized.get("phase"))
    allowed_actions = _mode_allowed_actions(mode)
    action_type = str(normalized.get("effective_action_type") or normalized.get("action_type") or "").strip()
    requested_action = str(normalized.get("action_type") or "").strip()
    step = int(normalized.pop("_phase_step", 0) or 0)
    turn_cap = int(normalized.pop("_phase_turn_cap", 0) or 0)
    terminal_turn = bool(step and turn_cap and step >= turn_cap)
    normalized["phase_before_action"] = _normalize_phase(normalized.get("phase_before_action")) or previous_phase
    normalized.setdefault("phase_enter_reason", "")
    normalized.setdefault("phase_exit_reason", "")
    normalized.setdefault("phase_hold_reason", "")
    normalized["early_finalize_attempted"] = bool(
        normalized.get("early_finalize_attempted", False)
        or normalized.get("decision") == "finalize"
        or requested_action in {"summarize_progress", "finalize"}
    )
    normalized["finalize_blocked_by_phase"] = bool(normalized.get("finalize_blocked_by_phase", False))

    if normalized.get("review_issue_discovery_required"):
        normalized["decision"] = "continue"
        normalized["action_type"] = "analyze_flaws"
        normalized["effective_action_type"] = "analyze_flaws"
        normalized["phase"] = "normal_review"
        normalized["phase_before_action"] = "normal_review"
        normalized["phase_enter_reason"] = ""
        normalized["phase_exit_reason"] = normalized.get("phase_exit_reason", "") if previous_phase == "recovery" else ""
        normalized["phase_hold_reason"] = ""
        normalized["turn_mode"] = "normal_evidence"
        normalized["recovery_patch_mode_entered"] = False
        normalized["finalize_blocked_by_phase"] = False
        normalized["negative_evidence_binding_retry_required"] = False
        normalized["negative_evidence_formation_required"] = False
        normalized["targeted_negative_search_required"] = False
        normalized["compact_negative_pass_required"] = False
        normalized["hard_negative_diagnosis_required"] = False
        normalized["target_flaw_ids"] = []
        normalized["target_evidence_ids"] = []
        normalized["target_hypotheses"] = []
        normalized["selected_agents"] = [
            agent for agent in ["Critique Agent"] if agent in worker_ids
        ][:worker_limit] or list(worker_ids[:1])
        if not int(normalized.get("phase_turn_index") or 0):
            normalized["phase_turn_index"] = max(1, int(state.get("phase_turn_index", 0) or 0) + (1 if previous_phase == "normal_review" else 0))
        return _apply_turn_mode(normalized)

    preserved_binding_retry = _preserve_negative_binding_retry_turn(
        normalized,
        worker_ids,
        worker_limit,
        recent_turn_logs,
        state,
    )
    if preserved_binding_retry is not None:
        if not int(preserved_binding_retry.get("phase_turn_index") or 0):
            preserved_binding_retry["phase_turn_index"] = max(
                1,
                int(state.get("phase_turn_index", 0) or 0) + (1 if previous_phase == "normal_review" else 0),
            )
        return preserved_binding_retry

    if requested_action and requested_action not in allowed_actions:
        original_action = requested_action
        inferred_payload = _infer_action_from_state(mode, state, recent_turn_logs)
        inferred_action = str((inferred_payload or {}).get("action_type") or "").strip()
        fallback_action = inferred_action if inferred_action in allowed_actions else next(iter(allowed_actions), requested_action)
        normalized["action_type"] = fallback_action
        normalized["effective_action_type"] = fallback_action
        if fallback_action not in RECOVERY_ACTION_TYPES:
            normalized["phase"] = "normal_review"
            normalized["phase_before_action"] = "normal_review"
            normalized["turn_mode"] = "normal_evidence"
            normalized["recovery_patch_mode_entered"] = False
            existing_phase = "normal_review"
        requested_action = fallback_action
        action_type = fallback_action
        notes = list(normalized.get("policy_notes", []))
        notes.append(f"Action {original_action} is not allowed in mode {mode}; fallback action {fallback_action} was used before phase routing.")
        normalized["policy_notes"] = list(dict.fromkeys(notes))[:8]
        if normalized.get("policy_source") in {"", "manager_model"}:
            normalized["policy_source"] = "mode_action_guard"

    pending_reviewer_negative_verification = _route_pending_reviewer_negative_quote_verification(
        normalized,
        state,
        worker_ids,
        worker_limit,
        recent_turn_logs,
        step,
        turn_cap,
    )
    if pending_reviewer_negative_verification is not None:
        return pending_reviewer_negative_verification

    if str(normalized.get("policy_source") or "") == "recovery_target_exhausted_override":
        support_recheck_claim_ids: List[str] = []
        try:
            support_recheck_claim_ids = _claims_without_real_strong_support(state)[:2]
        except Exception:
            support_recheck_claim_ids = []
        if support_recheck_claim_ids and "request_evidence_recheck" in allowed_actions:
            normalized["phase"] = "normal_review"
            normalized["phase_enter_reason"] = ""
            normalized["phase_hold_reason"] = ""
            normalized["phase_exit_reason"] = normalized.get("phase_exit_reason") or "Recovery phase exited because no verified-negative real target remains."
            normalized["decision"] = "continue"
            normalized["action_type"] = "request_evidence_recheck"
            normalized["effective_action_type"] = "request_evidence_recheck"
            normalized["turn_mode"] = "normal_evidence"
            normalized["recovery_patch_mode_entered"] = False
            normalized["finalize_blocked_by_phase"] = False
            normalized["selected_agents"] = [agent for agent in ["Evidence Agent"] if agent in worker_ids][:worker_limit] or list(worker_ids[:1])
            normalized["target_claim_ids"] = support_recheck_claim_ids
            normalized["target_flaw_ids"] = []
            normalized["target_hypotheses"] = []
            normalized["policy_source"] = "recovery_target_exhausted_evidence_recheck_override"
            notes = list(normalized.get("policy_notes", []))
            notes.append("Recovery target was exhausted, so the remaining turn was routed to evidence recheck for claims without real-strong support instead of an empty summary.")
            normalized["policy_notes"] = list(dict.fromkeys(notes))[:8]
            if not normalized.get("focus"):
                normalized["focus"] = "Ground claims that still lack real-strong paper support after recovery target exhaustion."
            if not int(normalized.get("phase_turn_index") or 0):
                normalized["phase_turn_index"] = max(1, int(state.get("phase_turn_index", 0) or 0))
            return _apply_turn_mode(normalized)
        normalized["phase"] = "normal_review"
        normalized["phase_enter_reason"] = ""
        normalized["phase_hold_reason"] = ""
        normalized["phase_exit_reason"] = normalized.get("phase_exit_reason") or "Recovery phase exited because no verified-negative real target remains."
        normalized["decision"] = "continue"
        normalized["action_type"] = "summarize_progress"
        normalized["effective_action_type"] = "summarize_progress"
        normalized["turn_mode"] = "normal_evidence"
        normalized["recovery_patch_mode_entered"] = False
        normalized["finalize_blocked_by_phase"] = False
        normalized["selected_agents"] = []
        normalized["target_claim_ids"] = []
        normalized["target_flaw_ids"] = []
        normalized["target_hypotheses"] = []
        if not int(normalized.get("phase_turn_index") or 0):
            normalized["phase_turn_index"] = max(1, int(state.get("phase_turn_index", 0) or 0))
        return _apply_turn_mode(normalized)

    outcome, outcome_reason = _latest_recovery_outcome(state, recent_turn_logs)
    recovery_relevant_fn = getattr(review_policy, "_state_is_recovery_relevant", None)
    state_is_recovery_relevant = bool(recovery_relevant_fn(state, recent_turn_logs)) if callable(recovery_relevant_fn) else bool(state.get("conflict_notes"))

    support_reason_fn = getattr(review_policy, "_support_formation_pass_reason", None)
    support_reason = ""
    if callable(support_reason_fn):
        support_reason = str(support_reason_fn(state, action_type, allowed_actions, recent_turn_logs) or "")
    if support_reason and (requested_action in RECOVERY_ACTION_TYPES or action_type in RECOVERY_ACTION_TYPES):
        normalized["phase"] = "normal_review"
        normalized["phase_before_action"] = "normal_review"
        normalized["phase_enter_reason"] = ""
        normalized["phase_hold_reason"] = ""
        normalized["phase_exit_reason"] = normalized.get("phase_exit_reason", "") if previous_phase == "recovery" else ""
        normalized["decision"] = "continue"
        normalized["action_type"] = "verify_evidence"
        normalized["effective_action_type"] = "verify_evidence"
        normalized["turn_mode"] = "normal_evidence"
        normalized["recovery_patch_mode_entered"] = False
        normalized["selected_agents"] = [agent for agent in ["Evidence Agent"] if agent in worker_ids][:worker_limit] or list(worker_ids[:1])
        normalized["support_formation_pass_triggered"] = True
        normalized["support_formation_pass_reason"] = support_reason
        normalized["support_formation_pass_from_action"] = requested_action or action_type
        normalized["finalize_blocked_by_phase"] = False
        notes = list(normalized.get("policy_notes", []))
        notes.append("Support formation pass intercepted recovery entry and routed one normal evidence verification turn first.")
        normalized["policy_notes"] = list(dict.fromkeys(notes))[:8]
        normalized["policy_source"] = "support_formation_override"
        if not int(normalized.get("phase_turn_index") or 0):
            normalized["phase_turn_index"] = max(1, int(state.get("phase_turn_index", 0) or 0) + (1 if previous_phase == "normal_review" else 0))
        return _apply_turn_mode(normalized)

    gate_triggered = bool(normalized.get("progression_gate_triggered", False))
    support_pass_triggered = bool(normalized.get("support_formation_pass_triggered", False))
    if support_pass_triggered:
        normalized["phase"] = "normal_review"
        normalized["phase_enter_reason"] = ""
        normalized["phase_hold_reason"] = ""
        normalized["phase_exit_reason"] = normalized.get("phase_exit_reason", "") if previous_phase == "recovery" else ""
        normalized["decision"] = "continue"
        normalized["action_type"] = "verify_evidence"
        normalized["effective_action_type"] = "verify_evidence"
        normalized["turn_mode"] = "normal_evidence"
        normalized["recovery_patch_mode_entered"] = False
        normalized["finalize_blocked_by_phase"] = False
        normalized["selected_agents"] = [agent for agent in ["Evidence Agent"] if agent in worker_ids][:worker_limit] or list(worker_ids[:1])
        notes = list(normalized.get("policy_notes", []))
        notes.append("Recovery phase respected support_formation_pass_triggered and forced the turn to remain a normal evidence verification pass.")
        normalized["policy_notes"] = list(dict.fromkeys(notes))[:8]
        normalized["policy_source"] = "support_formation_override"
        if not int(normalized.get("phase_turn_index") or 0):
            normalized["phase_turn_index"] = max(1, int(state.get("phase_turn_index", 0) or 0) + (1 if previous_phase == "normal_review" else 0))
        return _apply_turn_mode(normalized)
    if (gate_triggered or support_pass_triggered) and requested_action not in RECOVERY_ACTION_TYPES and action_type not in RECOVERY_ACTION_TYPES:
        normalized["phase"] = "normal_review"
        normalized["phase_enter_reason"] = ""
        normalized["phase_hold_reason"] = ""
        normalized["phase_exit_reason"] = normalized.get("phase_exit_reason", "") if previous_phase == "recovery" else ""
        normalized["finalize_blocked_by_phase"] = False
        notes = list(normalized.get("policy_notes", []))
        if support_pass_triggered:
            notes.append("Recovery phase respected support_formation_pass_triggered and did not re-promote the evidence-support pass into recovery.")
        else:
            notes.append("Recovery phase respected progression_gate_triggered and did not re-promote the safe downgraded action into recovery.")
        normalized["policy_notes"] = list(dict.fromkeys(notes))[:8]
        if not int(normalized.get("phase_turn_index") or 0):
            normalized["phase_turn_index"] = max(1, int(state.get("phase_turn_index", 0) or 0) + (1 if previous_phase == "normal_review" else 0))
        return _apply_turn_mode(normalized)

    enter_recovery = False
    reason = ""
    if existing_phase == "recovery":
        enter_recovery = True
        reason = str(normalized.get("phase_hold_reason") or normalized.get("phase_enter_reason") or "Recovery phase already active for this turn.")

    terminal_finalize_requested = bool(
        terminal_turn and (normalized.get("decision") == "finalize" or requested_action in {"summarize_progress", "finalize"})
    )
    terminal_recovery_entry_blocked = bool(
        terminal_finalize_requested
        and previous_phase != "recovery"
        and existing_phase != "recovery"
        and action_type not in RECOVERY_ACTION_TYPES
        and requested_action not in RECOVERY_ACTION_TYPES
        and not state.get("conflict_notes")
        and not state_is_recovery_relevant
    )
    if terminal_recovery_entry_blocked:
        normalized["phase"] = "normal_review"
        normalized["phase_enter_reason"] = ""
        normalized["phase_hold_reason"] = ""
        normalized["finalize_blocked_by_phase"] = False
        if not int(normalized.get("phase_turn_index") or 0):
            normalized["phase_turn_index"] = max(1, int(state.get("phase_turn_index", 0) or 0))
        return _apply_turn_mode(normalized)
    if terminal_finalize_requested and previous_phase == "recovery":
        normalized["phase"] = "normal_review"
        normalized["phase_enter_reason"] = ""
        normalized["phase_hold_reason"] = ""
        normalized["phase_exit_reason"] = normalized.get("phase_exit_reason") or "Recovery phase exited because the current turn reached the terminal turn cap."
        normalized["finalize_blocked_by_phase"] = False
        if not int(normalized.get("phase_turn_index") or 0):
            normalized["phase_turn_index"] = max(1, int(state.get("phase_turn_index", 0) or 0))
        return _apply_turn_mode(normalized)
    elif previous_phase == "recovery":
        if outcome == "open":
            enter_recovery = True
            reason = "Recovery phase held because the previous recovery turn has not reached a terminal committed/blocked result."
        else:
            normalized["phase"] = "normal_review"
            normalized["phase_enter_reason"] = ""
            normalized["phase_hold_reason"] = ""
            normalized["phase_exit_reason"] = normalized.get("phase_exit_reason") or outcome_reason or "Recovery phase exited after a terminal recovery outcome."
            normalized["phase_turn_index"] = int(normalized.get("phase_turn_index") or 1)
            return _apply_turn_mode(normalized)
    elif action_type in RECOVERY_ACTION_TYPES or requested_action in RECOVERY_ACTION_TYPES:
        enter_recovery = True
        reason = f"Recovery phase entered because action {requested_action or action_type} is recovery-oriented."
    elif state.get("conflict_notes") and requested_action in {"verify_evidence", "summarize_progress", "finalize"}:
        enter_recovery = True
        reason = f"Recovery phase entered because {len(state.get('conflict_notes', []))} unresolved conflict(s) remain."
    elif state_is_recovery_relevant and requested_action in {"summarize_progress", "finalize"}:
        enter_recovery = True
        reason = "Recovery phase entered because recovery-relevant repair signals remain unresolved."

    if not enter_recovery:
        normalized["phase"] = "normal_review"
        normalized["phase_enter_reason"] = ""
        normalized["phase_exit_reason"] = normalized.get("phase_exit_reason", "") if previous_phase == "recovery" else ""
        normalized["phase_hold_reason"] = ""
        if not int(normalized.get("phase_turn_index") or 0):
            normalized["phase_turn_index"] = max(1, int(state.get("phase_turn_index", 0) or 0) + (1 if previous_phase == "normal_review" else 0))
        return _apply_turn_mode(normalized)

    normalized["phase"] = "recovery"
    if previous_phase != "recovery":
        if not normalized.get("phase_enter_reason"):
            normalized["phase_enter_reason"] = reason
        normalized["phase_hold_reason"] = ""
        normalized["phase_exit_reason"] = ""
        if not int(normalized.get("phase_turn_index") or 0):
            normalized["phase_turn_index"] = 1
    else:
        normalized["phase_enter_reason"] = ""
        if not normalized.get("phase_hold_reason"):
            normalized["phase_hold_reason"] = reason or "Recovery phase held for another turn."
        normalized["phase_exit_reason"] = ""
        if not int(normalized.get("phase_turn_index") or 0):
            normalized["phase_turn_index"] = max(1, int(state.get("phase_turn_index", 0) or 0) + 1)

    recovery_action = requested_action if requested_action in RECOVERY_ACTION_TYPES else action_type if action_type in RECOVERY_ACTION_TYPES else ""
    if not recovery_action:
        chooser = getattr(review_policy, "_choose_recovery_action", None)
        recovery_action = str(chooser(state) if callable(chooser) else "challenge_previous_hypothesis")
    if recovery_action not in RECOVERY_ACTION_TYPES:
        recovery_action = "challenge_previous_hypothesis"
    if recovery_action not in allowed_actions:
        recovery_action = "request_evidence_recheck" if "request_evidence_recheck" in allowed_actions else "challenge_previous_hypothesis"
    if (
        recovery_action == "request_evidence_recheck"
        and "challenge_previous_hypothesis" in allowed_actions
    ):
        candidate_claim_ids = _recovery_candidate_claim_ids(state, "challenge_previous_hypothesis")
        candidate_flaw_ids = _recovery_candidate_flaw_ids(state, recent_turn_logs)
        patch_ready = bool(candidate_claim_ids or candidate_flaw_ids)
        evidence_lookup = {
            str(item.get("evidence_id") or ""): item
            for item in state.get("evidence_map", []) or []
            if isinstance(item, dict) and item.get("evidence_id")
        }
        candidate_flaw_id_set = set(candidate_flaw_ids)
        verified_negative_flaw_ready = any(
            isinstance(flaw, dict)
            and str(flaw.get("flaw_id") or "").strip() in candidate_flaw_id_set
            and bool(_flaw_verified_negative_evidence_ids_for_recovery(flaw, evidence_lookup))
            for flaw in state.get("flaw_candidates", []) or []
        )
        completed_recheck = _latest_turn_completed_normal_recheck(recent_turn_logs)
        notes = list(normalized.get("policy_notes", []))
        if patch_ready and (completed_recheck or verified_negative_flaw_ready):
            recovery_action = "challenge_previous_hypothesis"
            if completed_recheck:
                notes.append("Recovery phase upgraded from evidence recheck to challenge patch after one normal recheck turn completed.")
            else:
                notes.append("Recovery phase upgraded from evidence recheck to challenge patch because a verified negative flaw target is already patch-ready.")
            normalized["policy_notes"] = list(dict.fromkeys(notes))[:8]
            if normalized.get("policy_source") in {"", "manager_model", "recovery_phase_override", "evidence_progress_override"}:
                normalized["policy_source"] = "recovery_recheck_to_patch_override"
        else:
            notes.append("Recovery phase did not upgrade recheck to patch because no verified-negative claim or downgradeable flaw target is available.")
            normalized["policy_notes"] = list(dict.fromkeys(notes))[:8]
            if completed_recheck and not verified_negative_flaw_ready:
                normalized["phase"] = "normal_review"
                normalized["phase_enter_reason"] = ""
                normalized["phase_hold_reason"] = ""
                normalized["phase_exit_reason"] = (
                    normalized.get("phase_exit_reason")
                    or "Recovery phase exited after one evidence recheck because no verifier-confirmed negative target was available."
                )
                normalized["decision"] = "continue"
                normalized["action_type"] = "analyze_flaws" if "analyze_flaws" in allowed_actions else "summarize_progress"
                normalized["effective_action_type"] = normalized["action_type"]
                normalized["turn_mode"] = "normal_evidence"
                normalized["recovery_patch_mode_entered"] = False
                normalized["finalize_blocked_by_phase"] = False
                normalized["selected_agents"] = [
                    agent for agent in ["Critique Agent"] if agent in worker_ids
                ][:worker_limit] if normalized["action_type"] == "analyze_flaws" else []
                normalized["target_flaw_ids"] = []
                normalized["target_evidence_ids"] = []
                notes.append(
                    "Recovery recheck did not produce a verifier-confirmed negative target; returning to normal flaw analysis instead of repeating recheck."
                )
                normalized["policy_notes"] = list(dict.fromkeys(notes))[:8]
                if normalized.get("policy_source") in {"", "manager_model", "recovery_phase_override", "evidence_progress_override", "s4_recovery_relevant_override"}:
                    normalized["policy_source"] = "recovery_recheck_exit_to_flaw_analysis"
                normalized.setdefault("policy_source", "recovery_recheck_exit_to_flaw_analysis")
                return _apply_turn_mode(normalized)

    if (
        normalized.get("decision") == "finalize"
        or requested_action in {"summarize_progress", "finalize"}
        or action_type not in RECOVERY_ACTION_TYPES
        or recovery_action != action_type
    ):
        normalized["finalize_blocked_by_phase"] = normalized["early_finalize_attempted"] or requested_action in {"summarize_progress", "finalize"}
        normalized["decision"] = "continue"
        normalized["action_type"] = recovery_action
        normalized["effective_action_type"] = recovery_action
        notes = list(normalized.get("policy_notes", []))
        notes.append("Recovery phase prevented summarize/finalize fallback before the current repair target reached a terminal outcome.")
        normalized["policy_notes"] = list(dict.fromkeys(notes))[:8]
        if normalized.get("policy_source") in {"", "manager_model"}:
            normalized["policy_source"] = "recovery_phase_override"
        normalized["rationale"] = (((normalized.get("rationale") or "").strip() + " ").strip() + "Recovery phase kept the turn on a repair-oriented action until the current recovery target reaches a terminal committed/blocked result.")[:600]
    normalized = _ensure_recovery_targets(normalized, state, mode, recovery_action, recent_turn_logs)
    if (
        recovery_action == "challenge_previous_hypothesis"
        and not normalized.get("target_claim_ids")
        and not normalized.get("target_flaw_ids")
    ):
        normalized["phase"] = "normal_review"
        normalized["phase_enter_reason"] = ""
        normalized["phase_hold_reason"] = ""
        normalized["phase_exit_reason"] = normalized.get("phase_exit_reason") or "Recovery phase exited because patch target selection found no real corrective target."
        normalized["decision"] = "continue"
        normalized["action_type"] = "summarize_progress"
        normalized["effective_action_type"] = "summarize_progress"
        normalized["turn_mode"] = "normal_evidence"
        normalized["recovery_patch_mode_entered"] = False
        normalized["finalize_blocked_by_phase"] = False
        normalized["selected_agents"] = []
        normalized["target_hypotheses"] = []
        notes = list(normalized.get("policy_notes", []))
        notes.append("Recovery patch routing was cancelled because no real claim or flaw target survived final target selection.")
        normalized["policy_notes"] = list(dict.fromkeys(notes))[:8]
        if normalized.get("policy_source") in {"", "manager_model", "recovery_phase_override", "evidence_progress_override"}:
            normalized["policy_source"] = "recovery_target_exhausted_override"
        return _apply_turn_mode(normalized)
    if str(normalized.get("policy_source") or "").strip() in {"negative_evidence_formation_override", "compact_negative_pass_override"}:
        normalized["negative_evidence_formation_required"] = True
    if worker_ids:
        normalized["selected_agents"] = _pick_workers_for_action(recovery_action, worker_ids, worker_limit) or list(worker_ids[:worker_limit])
    return _apply_turn_mode(normalized)

def append_team_context(team_context: str, agent_id: str, text_response: str) -> str:
    snippet = _clip_text(text_response, MAX_TEAM_RESPONSE_CHARS)
    if not snippet.strip():
        return team_context
    updated = team_context + f"\nThe output of \"{agent_id}\": {snippet}\n"
    if len(updated) <= MAX_TEAM_CONTEXT_CHARS:
        return updated
    return "...[older team context truncated]\n" + updated[-MAX_TEAM_CONTEXT_CHARS:]




def _escape_control_chars_in_json_strings(payload_text: str) -> str:
    escaped = []
    in_string = False
    is_escaped = False
    for ch in payload_text:
        if in_string:
            if is_escaped:
                escaped.append(ch)
                is_escaped = False
                continue
            if ch == "\\":
                escaped.append(ch)
                is_escaped = True
                continue
            if ch == '"':
                escaped.append(ch)
                in_string = False
                continue
            if ch == "\n":
                escaped.append("\\n")
                continue
            if ch == "\r":
                escaped.append("\\r")
                continue
            if ch == "\t":
                escaped.append("\\t")
                continue
            escaped.append(ch)
            continue
        escaped.append(ch)
        if ch == '"':
            in_string = True
    return "".join(escaped)


def _strip_json_wrappers(payload_text: str) -> str:
    value = str(payload_text or "").strip()
    if value.startswith("```json"):
        value = value[7:].strip()
        if value.endswith("```"):
            value = value[:-3].strip()
    elif value.startswith("```"):
        value = value[3:].strip()
        if value.endswith("```"):
            value = value[:-3].strip()
    return value


def _loads_json_object(payload_text: str) -> Dict[str, Any]:
    cleaned = _strip_json_wrappers(payload_text)
    try:
        payload = json.loads(cleaned)
    except json.JSONDecodeError:
        payload = json.loads(_escape_control_chars_in_json_strings(cleaned))
    if not isinstance(payload, dict):
        raise ValueError("JSON payload must be an object.")
    return payload


def _iter_balanced_json_object_strings(raw_text: str) -> List[str]:
    raw = str(raw_text or "")
    objects: List[str] = []
    in_string = False
    escaped = False
    depth = 0
    start = -1
    for pos, ch in enumerate(raw):
        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
            continue
        if ch == "{":
            if depth == 0:
                start = pos
            depth += 1
            continue
        if ch == "}" and depth > 0:
            depth -= 1
            if depth == 0 and start != -1:
                objects.append(raw[start : pos + 1])
                start = -1
    return objects


def _iter_tagged_json_payloads(raw_text: str) -> List[str]:
    raw = str(raw_text or "")
    payloads: List[str] = []
    pos = 0
    while True:
        start = raw.find("<json>", pos)
        if start == -1:
            break
        content_start = start + len("<json>")
        end = raw.find("</json>", content_start)
        if end == -1:
            tail = raw[content_start:]
            if "{" in tail:
                payloads.append(tail)
            break
        payload = raw[content_start:end]
        if "{" in payload:
            payloads.append(payload)
        pos = end + len("</json>")
    return payloads


def _iter_fenced_json_payloads(raw_text: str) -> List[str]:
    raw = str(raw_text or "")
    payloads: List[str] = []
    for match in re.finditer(r"```(?:json)?\s*(.*?)```", raw, flags=re.IGNORECASE | re.DOTALL):
        payload = match.group(1)
        if "{" in payload:
            payloads.append(payload)
    return payloads


def _json_payload_schema_score(payload: Dict[str, Any]) -> int:
    score = 0
    high_value_keys = {
        "evidence_map": 80,
        "review_issue_slots": 90,
        "review_issue_candidates": 85,
        "reviewer_negative_candidates": 80,
        "claims": 70,
        "flaw_candidates": 70,
        "selected_agents": 70,
        "decision": 50,
        "action_type": 45,
        "action": 55,
        "target_type": 30,
        "target_id": 30,
        "old_status": 20,
        "new_status": 20,
        "blocked_reason": 20,
        "conflict_notes": 15,
        "unresolved_questions": 15,
        "dialogue_summary": 10,
        "recommendation": 10,
    }
    for key, weight in high_value_keys.items():
        if key in payload:
            score += weight
    # Avoid selecting nested evidence/flaw item objects over the top-level agent payload.
    if any(key in payload for key in ("evidence_id", "flaw_id", "claim_id")) and score < 80:
        score -= 20
    return score


def _candidate_json_payloads(raw_text: str) -> List[str]:
    candidates: List[str] = []
    candidates.extend(_iter_tagged_json_payloads(raw_text))
    candidates.extend(_iter_fenced_json_payloads(raw_text))
    candidates.extend(_iter_balanced_json_object_strings(raw_text))
    seen = set()
    unique: List[str] = []
    for candidate in candidates:
        value = str(candidate or "").strip()
        if not value or value in seen:
            continue
        seen.add(value)
        unique.append(value)
    return unique


def _extract_best_json_object(raw_text: str) -> Dict[str, Any]:
    best_payload: Optional[Dict[str, Any]] = None
    best_score = -10**9
    errors: List[str] = []
    for candidate in _candidate_json_payloads(raw_text):
        try:
            payload = _loads_json_object(candidate)
        except Exception as exc:
            errors.append(str(exc))
            continue
        score = _json_payload_schema_score(payload)
        if score > best_score:
            best_payload = payload
            best_score = score
    if best_payload is not None:
        return best_payload
    if errors:
        raise ValueError(f"Invalid JSON payload: {errors[0]}")
    raise ValueError("Missing a valid JSON object.")


def _extract_complete_json_objects_from_array(payload_text: str, array_key: str) -> List[Dict[str, Any]]:
    raw = str(payload_text or "")
    key_match = re.search(r'"' + re.escape(array_key) + r'"\s*:', raw)
    if not key_match:
        return []
    array_start = raw.find("[", key_match.end())
    if array_start == -1:
        return []

    objects: List[Dict[str, Any]] = []
    in_string = False
    escaped = False
    depth = 0
    obj_start = -1
    for pos in range(array_start + 1, len(raw)):
        ch = raw[pos]
        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
            continue
        if ch == "{":
            if depth == 0:
                obj_start = pos
            depth += 1
            continue
        if ch == "}":
            if depth <= 0:
                continue
            depth -= 1
            if depth == 0 and obj_start != -1:
                candidate = raw[obj_start : pos + 1]
                try:
                    item = json.loads(candidate)
                except json.JSONDecodeError:
                    try:
                        item = json.loads(_escape_control_chars_in_json_strings(candidate))
                    except json.JSONDecodeError:
                        item = None
                if isinstance(item, dict):
                    objects.append(item)
                obj_start = -1
            continue
        if ch == "]" and depth == 0:
            break
    return objects


def _payload_text_has_empty_evidence_array(payload_text: str) -> bool:
    return bool(re.search(r'"evidence_map"\s*:\s*\[\s*\]', str(payload_text or "")))


def extract_evidence_partial_payload(text: str, *, allow_empty_not_assessable: bool = False) -> Dict[str, Any]:
    raw = str(text or "")
    json_start = raw.find("<json>")
    json_end = raw.find("</json>")
    if json_start != -1:
        payload_text = raw[json_start + len("<json>") : json_end if json_end > json_start else len(raw)]
    else:
        first_brace = raw.find("{")
        if first_brace == -1:
            raise ValueError("Missing evidence JSON payload.")
        payload_text = raw[first_brace:]
    payload_text = _strip_json_wrappers(payload_text)
    evidence_items = _extract_complete_json_objects_from_array(payload_text, "evidence_map")
    unresolved_items = _extract_complete_json_objects_from_array(payload_text, "unresolved_questions")
    if not evidence_items:
        if allow_empty_not_assessable and unresolved_items and _payload_text_has_empty_evidence_array(payload_text):
            safe_unresolved: List[Dict[str, Any]] = []
            for item in unresolved_items[:2]:
                if not isinstance(item, dict):
                    continue
                status = str(item.get("status") or "").strip().lower()
                if status and status != "not_assessable":
                    continue
                safe_unresolved.append({**item, "status": "not_assessable"})
            if safe_unresolved:
                return {
                    "evidence_map": [],
                    "conflict_notes": _extract_complete_json_objects_from_array(payload_text, "conflict_notes"),
                    "unresolved_questions": safe_unresolved,
                    "dialogue_summary": "Partially recovered targeted negative not-assessable result from malformed Evidence Agent JSON.",
                    "recommendation": "undecided",
                    "partial_json_recovery": True,
                }
        raise ValueError("No complete evidence_map items could be recovered.")
    return {
        "evidence_map": evidence_items,
        "conflict_notes": _extract_complete_json_objects_from_array(payload_text, "conflict_notes"),
        "unresolved_questions": unresolved_items if allow_empty_not_assessable else [],
        "dialogue_summary": "Partially recovered complete evidence items from malformed Evidence Agent JSON.",
        "recommendation": "undecided",
        "partial_json_recovery": True,
    }


def _extract_balanced_json_object_at(raw: str, start: int) -> Optional[Dict[str, Any]]:
    text = str(raw or "")
    if start < 0 or start >= len(text) or text[start] != "{":
        return None
    in_string = False
    escaped = False
    depth = 0
    for pos in range(start, len(text)):
        ch = text[pos]
        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
            continue
        if ch == "{":
            depth += 1
            continue
        if ch == "}":
            depth -= 1
            if depth == 0:
                candidate = text[start : pos + 1]
                try:
                    return _loads_json_object(candidate)
                except Exception:
                    return None
    return None


def _extract_review_issue_candidate_objects(raw_text: str) -> List[Dict[str, Any]]:
    raw = str(raw_text or "")
    objects: List[Dict[str, Any]] = []
    seen: set[str] = set()
    for array_key in ("review_issue_candidates", "reviewer_negative_candidates", "freeform_review_issue_candidates"):
        for item in _extract_complete_json_objects_from_array(raw, array_key):
            key = json.dumps(item, sort_keys=True, ensure_ascii=False)
            if key not in seen:
                seen.add(key)
                objects.append(item)
    for match in re.finditer(r'"candidate"\s*:\s*{', raw):
        brace_start = raw.find("{", match.start())
        item = _extract_balanced_json_object_at(raw, brace_start)
        if not isinstance(item, dict):
            continue
        if item.get("candidate") is None and item.get("no_candidate_reason") is not None:
            continue
        key = json.dumps(item, sort_keys=True, ensure_ascii=False)
        if key in seen:
            continue
        seen.add(key)
        objects.append(item)
    return objects[:12]


def _maybe_recover_review_issue_discovery_candidates(
    agent_id: str,
    raw_text: str,
    normalized_payload: Dict[str, Any],
    manager_payload: Optional[Dict[str, Any]],
) -> tuple[Dict[str, Any], bool]:
    if agent_id != "Critique Agent":
        return normalized_payload, False
    if not isinstance(manager_payload, dict) or not manager_payload.get("review_issue_discovery_required"):
        return normalized_payload, False
    if not isinstance(normalized_payload, dict):
        return normalized_payload, False
    if normalized_payload.get("reviewer_negative_candidates"):
        return normalized_payload, False
    raw_candidates = _extract_review_issue_candidate_objects(raw_text)
    if not raw_candidates:
        return normalized_payload, False
    recovered = normalize_review_update_payload({"reviewer_negative_candidates": raw_candidates})
    candidates = recovered.get("reviewer_negative_candidates", [])
    if not candidates:
        return normalized_payload, False
    updated = copy.deepcopy(normalized_payload)
    updated["reviewer_negative_candidates"] = candidates[:12]
    summary = _candidate_text(updated.get("dialogue_summary"), 800)
    updated["dialogue_summary"] = (
        (summary + " " if summary else "")
        + f"Recovered {len(candidates[:12])} review issue candidates from truncated review_issue_slots."
    )
    updated["_partial_json_recovery"] = True
    updated["review_issue_candidate_partial_recovery"] = True
    return updated, True


def extract_tagged_json(text: str) -> Dict[str, Any]:
    return _extract_best_json_object(text)


def normalize_agent_payload(
    agent_id: str,
    payload: Dict[str, Any],
    available_workers: Optional[Iterable[str]] = None,
) -> Dict[str, Any]:
    spec = AGENT_SPECS[agent_id]
    if spec.is_manager:
        return normalize_manager_payload(payload, available_agents=available_workers)
    return normalize_review_update_payload(payload, required_fields=spec.required_fields)


def _review_issue_inventory_type_matches_requirement(item: Dict[str, Any], requirement: str, issue_type: str) -> bool:
    reqs = {str(req or "").strip() for req in item.get("requirement_types", []) if str(req or "").strip()}
    inventory_type = str(item.get("inventory_type") or "").strip()
    requirement = str(requirement or "").strip()
    issue_type = str(issue_type or "").strip()
    if requirement and requirement in reqs:
        return True
    if issue_type in {"missing_baseline", "unfair_or_weak_baseline"}:
        return "baseline_or_comparison" in reqs or inventory_type == "baseline"
    if issue_type == "missing_ablation":
        return "ablation_or_component" in reqs or inventory_type == "ablation"
    if issue_type in {"insufficient_evaluation", "result_claim_mismatch"}:
        return bool(reqs & {"empirical_result", "baseline_or_comparison", "ablation_or_component"}) or inventory_type in {
            "metric",
            "baseline",
            "ablation",
        }
    if issue_type in {"missing_robustness_or_generalization", "scope_overclaim"}:
        return bool(reqs & {"robustness_or_generalization", "scope_coverage", "empirical_result"}) or inventory_type in {
            "dataset",
            "metric",
        }
    if issue_type == "evaluation_protocol_risk":
        return "evaluation_protocol" in reqs or inventory_type == "protocol"
    if issue_type == "efficiency_cost_gap":
        return "efficiency_cost" in reqs or inventory_type == "runtime"
    if issue_type in {"method_support_gap", "reproducibility_gap"}:
        return bool(reqs & {"method_detail", "reproducibility_detail"}) or inventory_type == "training_detail"
    return bool(reqs)


def _review_issue_slot_for_type(issue_type: str) -> str:
    issue_type = str(issue_type or "").strip()
    if issue_type in {"missing_baseline", "unfair_or_weak_baseline"}:
        return "missing_baseline"
    if issue_type == "missing_ablation":
        return "missing_ablation"
    if issue_type in {"missing_robustness_or_generalization", "scope_overclaim", "insufficient_evaluation"}:
        return "scope_or_robustness"
    if issue_type in {"evaluation_protocol_risk", "reproducibility_gap", "method_support_gap"}:
        return "protocol_or_reproducibility"
    if issue_type == "efficiency_cost_gap":
        return "efficiency_cost"
    if issue_type in {"result_claim_mismatch", "negative_result"}:
        return "result_claim_mismatch"
    return issue_type or "unknown"


def _select_review_issue_seed_inventory(
    target: Dict[str, Any],
    requirement: str,
    issue_type: str,
) -> List[Dict[str, Any]]:
    raw_items: List[Dict[str, Any]] = []
    for field in ("inventory_menu", "paper_evaluation_inventory", "verified_support_inventory"):
        value = target.get(field)
        if isinstance(value, list):
            raw_items.extend([item for item in value if isinstance(item, dict)])
    selected: List[Dict[str, Any]] = []
    seen: set[str] = set()
    for item in raw_items:
        quote = _candidate_text(item.get("quote"), 260)
        locator = _candidate_text(item.get("locator") or item.get("source_locator") or item.get("inventory_id"), 120)
        inventory_id = str(item.get("inventory_id") or item.get("evidence_id") or item.get("menu_id") or "").strip()
        if not quote or not locator:
            continue
        if not _review_issue_inventory_type_matches_requirement(item, requirement, issue_type):
            continue
        key = (inventory_id or quote).lower()
        if key in seen:
            continue
        seen.add(key)
        selected.append(
            {
                "inventory_id": inventory_id,
                "evidence_id": str(item.get("evidence_id") or ""),
                "quote": quote,
                "locator": locator,
                "inventory_type": str(item.get("inventory_type") or ""),
                "observed_items": [
                    _candidate_text(observed, 80)
                    for observed in (item.get("observed_items") or [])
                    if _candidate_text(observed, 80)
                ][:8],
            }
        )
        if len(selected) >= 2:
            break
    return selected


def _seed_items_from_review_issue_blueprint(target: Dict[str, Any], blueprint: Dict[str, Any]) -> List[str]:
    issue_type = str(blueprint.get("issue_type") or "")

    def usable_missing_ablation_item(text: str) -> bool:
        if issue_type != "missing_ablation":
            return True
        observed_inventory = []
        for field in ("inventory_menu", "paper_evaluation_inventory", "verified_support_inventory"):
            for item in target.get(field) or []:
                if isinstance(item, dict):
                    observed_inventory.append(item)
        quality = _missing_ablation_target_quality(
            {
                "missing_or_mismatch": {"entity": text, "items": [text]},
                "claim_anchor": {"quote": str(target.get("claim") or "")},
                "observed_inventory": observed_inventory[:3],
                "reviewer_negative_candidate": str(blueprint.get("prompt") or blueprint.get("description") or ""),
            }
        )
        return str(quality.get("quality") or "") in {"high", "medium"}

    if issue_type in {"missing_baseline", "unfair_or_weak_baseline"}:
        baseline_items: List[str] = []
        claim_text = str(target.get("claim") or "")
        claim_tokens = {token.lower() for token in re.findall(r"[A-Za-z][A-Za-z0-9_-]{2,}", claim_text)}
        for field in ("inventory_menu", "paper_evaluation_inventory", "verified_support_inventory"):
            for item in target.get(field) or []:
                if not isinstance(item, dict):
                    continue
                quote = str(item.get("quote") or "")
                reqs = {str(req or "") for req in item.get("requirement_types") or []}
                if "baseline_or_comparison" not in reqs and not re.search(
                    r"\b(?:baseline|baselines|prior\s+methods?|existing\s+methods?|state[- ]of[- ]the[- ]art|sota|compared)\b",
                    quote,
                    re.IGNORECASE,
                ):
                    continue
                observed_items = list(item.get("observed_items") or [])
                if not observed_items:
                    observed_items = re.findall(
                        r"\b(?:[A-Z]{2,}[A-Za-z0-9_-]*|[A-Z][A-Za-z0-9]+(?:[-_][A-Za-z0-9]+)+)\b",
                        quote,
                    )
                for raw_observed in observed_items:
                    observed = _candidate_text(raw_observed, 80)
                    if not observed:
                        continue
                    observed_l = observed.lower()
                    if len(observed_l) <= 2:
                        continue
                    if observed_l in claim_tokens:
                        continue
                    if observed_l in {
                        "table",
                        "figure",
                        "fine-tuning",
                        "fine tuning",
                        "state-of-the-art",
                        "state of the art",
                        "sota",
                        "compared",
                        "comparison",
                        "baseline",
                        "baselines",
                        "ours",
                        "method",
                        "methods",
                        "model",
                        "models",
                        "results",
                    }:
                        continue
                    if not re.search(r"\b[A-Z]{2,}[A-Za-z0-9_-]*\b|[-_]|[A-Z][a-z]+[A-Z]", observed):
                        continue
                    candidate = f"same-setting comparison against {observed}"
                    if candidate.lower() not in {item.lower() for item in baseline_items}:
                        baseline_items.append(candidate)
                    if len(baseline_items) >= 2:
                        return baseline_items
    examples = []
    for item in blueprint.get("candidate_missing_item_examples") or []:
        text = _candidate_text(item, 150)
        if not text:
            continue
        lower = text.lower()
        if issue_type in {"missing_baseline", "unfair_or_weak_baseline"} and re.search(
            r"\b(?:strongest|named|strong|standard|relevant|recent)\s+baseline\s+famil(?:y|ies)\b|"
            r"\bnamed\s+strong\s+baseline\b|"
            r"\bprior[- ]method\s+famil(?:y|ies)\b|"
            r"\bfairness\s+check\s+that\s+compares\b|"
            r"\bstate[- ]of[- ]the[- ]art\b|"
            r"\babsent\s+from\s+the\s+observed\s+comparison\s+table\b|"
            r"\bnamed\s+by\s+the\s+paper\s+task\b",
            lower,
        ):
            continue
        if issue_type == "missing_ablation" and not usable_missing_ablation_item(text):
            continue
        examples.append(text)
    if examples:
        return examples[:2]
    claim = str(target.get("claim") or "")
    surface = target.get("claim_surface_profile") if isinstance(target.get("claim_surface_profile"), dict) else {}
    entities = [
        _candidate_text(item, 80)
        for key in (
            "components_or_mechanisms",
            "comparison_targets",
            "datasets_or_benchmarks",
            "metrics_or_protocols",
            "resource_dimensions",
            "surface_entities",
        )
        for item in (surface.get(key) or [])
        if _candidate_text(item, 80)
    ]
    primary = entities[0] if entities else _candidate_text(claim, 80)
    if issue_type in {"missing_baseline", "unfair_or_weak_baseline"}:
        return []
    if issue_type == "missing_ablation":
        component_entities = [
            _candidate_text(item, 80)
            for item in (surface.get("components_or_mechanisms") or [])
            if _candidate_text(item, 80)
        ]
        for entity in component_entities + ([primary] if primary else []):
            candidate = f"component-isolation ablation for {entity}"
            if usable_missing_ablation_item(candidate):
                return [candidate]
        return []
    if issue_type in {"missing_robustness_or_generalization", "scope_overclaim"}:
        return []
    if issue_type == "evaluation_protocol_risk":
        return []
    if issue_type == "efficiency_cost_gap":
        return [f"runtime, memory, or compute-cost measurement for {primary}"] if primary else []
    if issue_type == "reproducibility_gap":
        return [f"training or implementation details for {primary}"] if primary else []
    if issue_type in {"insufficient_evaluation", "result_claim_mismatch"}:
        return []
    return [f"specific verification item for {primary}"] if primary else []


def _review_issue_candidate_semantic_cluster_key(candidate: Dict[str, Any]) -> Tuple[str, str, str]:
    if not isinstance(candidate, dict):
        return ("", "", "")
    claim_id = str(candidate.get("claim_id") or "").strip()
    issue_type = str(candidate.get("negative_type") or candidate.get("issue_type") or "").strip()
    missing_items = [
        _candidate_text(item, 160)
        for item in (candidate.get("missing_or_weak_items") or [])
        if _candidate_text(item, 160)
    ]
    if not claim_id or not issue_type or not missing_items:
        return ("", "", "")
    observed_inventory = candidate.get("observed_inventory")
    if not isinstance(observed_inventory, list):
        observed_inventory = []
    menu_item = candidate.get("review_issue_candidate_menu_item")
    if not observed_inventory and isinstance(menu_item, dict):
        snapshot_inventory = menu_item.get("observed_inventory")
        if isinstance(snapshot_inventory, list):
            observed_inventory = snapshot_inventory
        else:
            anchor = menu_item.get("inventory_anchor") if isinstance(menu_item.get("inventory_anchor"), dict) else {}
            if anchor:
                observed_inventory = [
                    {
                        "quote": _candidate_text(anchor.get("quote") or menu_item.get("inventory_quote"), 260),
                        "locator": _candidate_text(anchor.get("locator") or menu_item.get("inventory_locator"), 120),
                        "observed_items": list(anchor.get("observed_items") or []),
                        "inventory_type": str(anchor.get("inventory_type") or menu_item.get("inventory_type") or ""),
                    }
                ]
    bundle = {
        "missing_or_mismatch": {
            "entity": missing_items[0],
            "items": missing_items,
        },
        "observed_inventory": observed_inventory,
        "claim_anchor": {"quote": str(candidate.get("claim") or "")},
    }
    try:
        target = _review_issue_normalized_cluster_target(bundle, issue_type)
    except Exception:
        target = ""
    if not target or target == "unspecified_target":
        target = "|".join(item.lower() for item in missing_items)
    return (claim_id, issue_type, target)


def _seed_review_issue_missing_item_quality_failure(
    target: Dict[str, Any],
    *,
    issue_type: str,
    missing_item: str,
    observed_inventory: Sequence[Dict[str, Any]],
    source: str,
) -> str:
    missing = _candidate_text(missing_item, 160)
    if not missing:
        return "empty_missing_item"
    if not _review_issue_missing_items_are_concrete(issue_type, [missing]):
        return "missing_item_not_concrete"
    inventory_text = " ".join(
        [str(item.get("quote") or "") for item in observed_inventory or [] if isinstance(item, dict)]
        + [
            " ".join(
                _candidate_text(observed, 80)
                for observed in (item.get("observed_items") or [])
                if _candidate_text(observed, 80)
            )
            for item in observed_inventory or []
            if isinstance(item, dict)
        ]
    )
    return _review_issue_candidate_menu_quality_failure(
        neg_type=issue_type,
        expected_entity=missing,
        claim_text=str((target or {}).get("claim") or ""),
        inventory_text=inventory_text,
        source=source,
    )


def _seed_review_issue_candidates_from_targets(
    state: Dict[str, Any],
    *,
    max_candidates: int = 12,
) -> List[Dict[str, Any]]:
    try:
        targets = _hard_negative_diagnosis_targets(state or {}, claims=(state or {}).get("claims"), max_items=12)
    except Exception:
        targets = []
    candidates: List[Dict[str, Any]] = []
    seen: set[Tuple[str, str, str]] = set()
    type_counts: Dict[str, int] = {}
    seedable_types = {
        "missing_baseline",
        "unfair_or_weak_baseline",
        "missing_ablation",
        "insufficient_evaluation",
        "missing_robustness_or_generalization",
        "scope_overclaim",
        "evaluation_protocol_risk",
        "efficiency_cost_gap",
        "result_claim_mismatch",
    }

    def add_candidate(
        target: Dict[str, Any],
        *,
        issue_type: str,
        requirement: str,
        missing_item: str,
        obligation_id: str = "",
        source: str = "runner_seed_blueprint",
        observed_inventory: Optional[Sequence[Dict[str, Any]]] = None,
        entity_source: str = "",
    ) -> None:
        nonlocal candidates
        claim_id = str(target.get("claim_id") or "").strip()
        issue_type = str(issue_type or "").strip()
        requirement = str(requirement or "").strip()
        missing_item = _candidate_text(missing_item, 160)
        if not claim_id or not issue_type or not requirement or not missing_item:
            return
        claim_type = str(target.get("claim_type") or "").strip().lower()
        if claim_type == "limitation_or_boundary":
            return
        if issue_type not in seedable_types:
            return
        if type_counts.get(issue_type, 0) >= 2:
            return
        if observed_inventory is not None:
            inventory = [
                item for item in observed_inventory
                if isinstance(item, dict) and _candidate_text(item.get("quote"), 260)
            ][:3]
        else:
            inventory = _select_review_issue_seed_inventory(target, requirement, issue_type)
        if not inventory:
            return
        if _seed_review_issue_missing_item_quality_failure(
            target,
            issue_type=issue_type,
            missing_item=missing_item,
            observed_inventory=inventory,
            source=source,
        ):
            return
        key = (claim_id, issue_type, missing_item.lower())
        if key in seen:
            return
        seen.add(key)
        type_counts[issue_type] = type_counts.get(issue_type, 0) + 1
        candidate_id = "reviewer-seed-candidate-" + _candidate_slug(f"{claim_id}-{issue_type}-{missing_item}")
        weakness = (
            f"The claim may lack {missing_item}; verify this as a {issue_type.replace('_', ' ')} "
            "against the paper's observed inventory."
        )
        candidates.append(
            {
                "candidate_id": candidate_id,
                "claim_id": claim_id,
                "claim": _candidate_text(target.get("claim"), 240),
                "obligation_id": obligation_id,
                "weakness": weakness,
                "negative_type": issue_type,
                "required_evidence_type": requirement,
                "quote_grounding_mode": "absence_or_requirement_gap",
                "verification_question": (
                    f"Does the paper's observed inventory cover {missing_item} for claim {claim_id}?"
                ),
                "expected_quote_cues": ["Table", "Results", "Experiments", "Evaluation"],
                "missing_or_weak_items": [missing_item],
                "observed_inventory": inventory,
                "source_of_expectation": "reviewer_candidate",
                "source": source,
                "review_issue_slot": _review_issue_slot_for_type(issue_type),
                "discovery_origin": source,
                "entity_source": entity_source or str(target.get("entity_source") or ""),
                "status": "pending_absence_audit",
                "confidence": 0.62,
                "rationale": (
                    "Generated from visible entity-level claim obligations / issue blueprints because "
                    "the Critique discovery payload returned no candidates; still requires strict bundle verification."
                ),
            }
        )

    for target in targets:
        if not isinstance(target, dict):
            continue
        for obligation in target.get("entity_level_claim_obligations") or []:
            if not isinstance(obligation, dict):
                continue
            add_candidate(
                target,
                issue_type=str(obligation.get("issue_type") or ""),
                requirement=str(obligation.get("required_evidence_type") or ""),
                missing_item=str(obligation.get("expected_entity") or ""),
                obligation_id=str(obligation.get("obligation_id") or ""),
                source="runner_seed_entity_obligation",
            )
            if len(candidates) >= max_candidates:
                return candidates[:max_candidates]
        for blueprint in target.get("issue_candidate_blueprints") or []:
            if not isinstance(blueprint, dict):
                continue
            issue_type = str(blueprint.get("issue_type") or "")
            requirement = str(blueprint.get("required_evidence_type") or "")
            for missing_item in _seed_items_from_review_issue_blueprint(target, blueprint):
                add_candidate(
                    target,
                    issue_type=issue_type,
                    requirement=requirement,
                    missing_item=missing_item,
                    source="runner_seed_blueprint",
                )
                if len(candidates) >= max_candidates:
                    return candidates[:max_candidates]
    for claim in (state or {}).get("claims", []) or []:
        if not isinstance(claim, dict):
            continue
        claim_id = str(claim.get("claim_id") or "").strip()
        if not claim_id:
            continue
        claim_type = str(claim.get("claim_type") or "").strip().lower()
        if claim_type == "limitation_or_boundary":
            continue
        for target in _review_issue_component_ablation_seed_targets(state or {}, claim, max_items=2):
            if not isinstance(target, dict):
                continue
            add_candidate(
                {
                    "claim_id": claim_id,
                    "claim": claim.get("claim"),
                    "claim_type": claim.get("claim_type"),
                    "entity_source": "method_component",
                },
                issue_type="missing_ablation",
                requirement="ablation_or_component",
                missing_item=str(target.get("missing_item") or ""),
                source="runner_seed_component_ablation",
                observed_inventory=target.get("observed_inventory") or [],
                entity_source="method_component",
            )
            if len(candidates) >= max_candidates:
                return candidates[:max_candidates]
    return candidates[:max_candidates]


def _menu_item_from_seed_review_issue_candidate(candidate: Dict[str, Any], index: int) -> Dict[str, Any]:
    if not isinstance(candidate, dict):
        return {}
    claim_id = str(candidate.get("claim_id") or "").strip()
    issue_type = str(candidate.get("negative_type") or candidate.get("issue_type") or "").strip()
    required = str(candidate.get("required_evidence_type") or "").strip()
    missing_items = [
        _candidate_text(item, 160)
        for item in (candidate.get("missing_or_weak_items") or [])
        if _candidate_text(item, 160)
    ]
    observed_inventory = [
        item for item in (candidate.get("observed_inventory") or [])
        if isinstance(item, dict) and _candidate_text(item.get("quote"), 260)
    ]
    if not claim_id or not issue_type or not required or not missing_items or not observed_inventory:
        return {}
    expected = missing_items[0]
    if issue_type == "missing_ablation":
        quality_bundle = {
            "missing_or_mismatch": {"entity": expected, "items": missing_items},
            "observed_inventory": observed_inventory,
            "claim_anchor": {"quote": str(candidate.get("claim") or "")},
        }
        quality = _missing_ablation_target_quality(quality_bundle)
        if str(quality.get("quality") or "") in {"", "low", "reject"}:
            return {}
    else:
        quality = {}
    source = str(candidate.get("source") or candidate.get("discovery_origin") or "runner_seed_selector_menu")
    inventory0 = observed_inventory[0]
    return {
        "candidate_menu_id": _review_issue_candidate_menu_id(claim_id, issue_type, expected, index),
        "claim_id": claim_id,
        "claim": _candidate_text(candidate.get("claim"), 240),
        "obligation_id": str(candidate.get("obligation_id") or ""),
        "issue_type": issue_type,
        "required_evidence_type": required,
        "expected_entity": expected,
        "verifier_target_entity": expected,
        "entity_source": str(candidate.get("entity_source") or ""),
        "source": source if source.startswith("runner_seed") else f"runner_seed_selector_menu:{source}",
        "review_issue_slot": str(candidate.get("review_issue_slot") or _review_issue_slot_for_type(issue_type)),
        "inventory_id": str(inventory0.get("inventory_id") or ""),
        "inventory_quote": _candidate_text(inventory0.get("quote"), 260),
        "inventory_locator": _candidate_text(inventory0.get("locator"), 120),
        "inventory_type": _candidate_text(inventory0.get("inventory_type"), 80),
        "observed_inventory": observed_inventory[:2],
        "target_quality_hint": str(quality.get("quality") or ""),
        "target_quality_reason": str(quality.get("reason") or ""),
        "why_review_worthy": _candidate_text(
            candidate.get("weakness") or f"Runner seed found a verifier-ready review issue target: {expected}.",
            90,
        ),
        "counterevidence_search_terms": list(candidate.get("possible_counterevidence_terms") or missing_items)[:8],
        "counterevidence_aliases": list(candidate.get("possible_counterevidence_terms") or missing_items)[:8],
    }


def _seed_review_issue_candidate_menu_items_from_state(
    state: Dict[str, Any],
    *,
    max_items: int = 12,
) -> List[Dict[str, Any]]:
    seeded = _seed_review_issue_candidates_from_targets(state or {}, max_candidates=max_items)
    if not seeded:
        return []
    normalized = normalize_review_update_payload({"reviewer_negative_candidates": seeded})
    candidates = normalized.get("reviewer_negative_candidates", [])
    items: List[Dict[str, Any]] = []
    seen_clusters: set[Tuple[str, str, str]] = set()
    used_menu_ids: set[str] = set()
    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        cluster_key = _review_issue_candidate_semantic_cluster_key(candidate)
        if cluster_key[0] and cluster_key in seen_clusters:
            continue
        menu_item = _menu_item_from_seed_review_issue_candidate(candidate, len(items) + 1)
        if not menu_item:
            continue
        menu_item = dict(menu_item)
        menu_item["candidate_menu_id"] = _review_issue_disambiguate_candidate_menu_id(
            str(menu_item.get("candidate_menu_id") or ""),
            used_menu_ids,
            len(items) + 1,
        )
        if cluster_key[0]:
            seen_clusters.add(cluster_key)
        items.append(menu_item)
        if len(items) >= max_items:
            break
    return items


def _augmented_review_issue_selector_menu_from_state(
    state: Dict[str, Any],
    *,
    target_max_items: int = 12,
    selector_max_items: int = 12,
    selector_max_per_claim: int = 3,
    selector_max_per_type: int = 4,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    targets = _hard_negative_diagnosis_targets(
        state or {},
        claims=(state or {}).get("claims", []),
        max_items=target_max_items,
    )
    seed_menu_items = _seed_review_issue_candidate_menu_items_from_state(
        state or {},
        max_items=selector_max_items,
    )
    augmented_targets = list(targets or [])
    if seed_menu_items:
        augmented_targets.append(
            {
                "claim_id": "__runner_seed_selector_menu__",
                "review_issue_candidate_menu": seed_menu_items,
            }
        )
    visible_menu = _review_issue_candidate_selector_menu(
        augmented_targets,
        max_items=selector_max_items,
        max_per_claim=selector_max_per_claim,
        max_per_type=selector_max_per_type,
    )
    return augmented_targets, visible_menu


def _review_issue_bundle_enabled() -> bool:
    return os.environ.get("DRMAS_REVIEW_ISSUE_BUNDLE", "1").strip().lower() not in {
        "0",
        "false",
        "off",
        "no",
    }


def _targeted_negative_search_enabled() -> bool:
    if hasattr(review_policy, "_TARGETED_NEGATIVE_SEARCH_ENABLED"):
        return bool(getattr(review_policy, "_TARGETED_NEGATIVE_SEARCH_ENABLED"))
    return os.environ.get("DRMAS_TARGETED_NEGATIVE_SEARCH", "").strip().lower() in {
        "1",
        "true",
        "on",
        "yes",
    }


def _review_issue_discovery_recently_attempted(recent_turn_logs: Sequence[Dict[str, Any]]) -> bool:
    for turn in list(recent_turn_logs or [])[-5:]:
        if not isinstance(turn, dict):
            continue
        if turn.get("review_issue_discovery_required") or turn.get("freeform_reviewer_negative_discovery_required"):
            return True
        if str(turn.get("policy_source") or "") in {
            "review_issue_discovery_override",
            "freeform_reviewer_negative_discovery_override",
        }:
            return True
        if str(turn.get("freeform_reviewer_negative_stage") or "") == "candidate_discovery":
            return True
    helper = getattr(review_policy, "_has_recent_freeform_reviewer_negative_discovery", None)
    if callable(helper):
        try:
            return bool(helper(recent_turn_logs))
        except Exception:
            pass
    return False


def _review_issue_pending_candidate_exists(state: Dict[str, Any]) -> bool:
    helper = getattr(review_policy, "_has_pending_reviewer_negative_candidates", None)
    if callable(helper):
        try:
            return bool(helper(state or {}))
        except Exception:
            pass
    for item in (state or {}).get("reviewer_negative_candidates", []) or []:
        if not isinstance(item, dict):
            continue
        status = str(item.get("status") or "pending_quote_verification").strip().lower()
        if status in {
            "pending_quote_verification",
            "pending_absence_audit",
            "pending_issue_bundle_verification",
            "open",
            "not_assessable",
        }:
            return True
    return False


def _review_issue_positive_inventory_ready(state: Dict[str, Any]) -> bool:
    helper = getattr(review_policy, "_positive_inventory_ready", None)
    if callable(helper):
        try:
            return bool(helper(state or {}))
        except Exception:
            pass
    for item in (state or {}).get("evidence_map", []) or []:
        if not isinstance(item, dict):
            continue
        stance = str(item.get("stance") or "").strip().lower()
        strength = str(item.get("strength") or "").strip().lower()
        if stance == "supports" and strength == "strong":
            return True
    return False


def _review_issue_real_strong_support_count(state: Dict[str, Any]) -> int:
    count = 0
    for item in (state or {}).get("evidence_map", []) or []:
        if not isinstance(item, dict):
            continue
        stance = str(item.get("stance") or "").strip().lower()
        strength = str(item.get("strength") or "").strip().lower()
        if stance != "supports" or strength != "strong":
            continue
        binding = str(item.get("binding_status") or "").strip().lower()
        if binding and binding not in {"bound_real_claim", "bound", "verified"}:
            continue
        grounding = str(item.get("verified_grounding_label") or "").strip().lower()
        semantic = str(item.get("semantic_grounding_label") or "").strip().lower()
        if grounding and not grounding.startswith("paper_grounded"):
            continue
        if semantic and semantic not in {"semantic_support_verified", "semantic_verified", "support_verified"}:
            continue
        count += 1
    return count


def _maybe_upgrade_visible_review_issue_discovery_turn(
    manager_payload: Dict[str, Any],
    state: Dict[str, Any],
    *,
    mode: str,
    worker_ids: Sequence[str],
    worker_limit: int,
    recent_turn_logs: Sequence[Dict[str, Any]],
    step: int,
    turn_cap: int,
) -> Dict[str, Any]:
    if not isinstance(manager_payload, dict) or not isinstance(state, dict):
        return manager_payload
    if manager_payload.get("review_issue_discovery_required"):
        return manager_payload
    if mode != "s4":
        return manager_payload
    if not (
        _review_issue_bundle_enabled()
        and _targeted_negative_search_enabled()
        and (_freeform_reviewer_negative_enabled() or _review_issue_bundle_enabled())
    ):
        return manager_payload
    if "Critique Agent" not in worker_ids:
        return manager_payload
    if turn_cap > 0 and step >= turn_cap:
        return manager_payload
    phase = str(manager_payload.get("phase") or state.get("phase") or "").strip().lower()
    turn_mode = _normalize_turn_mode(manager_payload.get("turn_mode"))
    if phase == "recovery" or turn_mode == "recovery_patch" or manager_payload.get("recovery_patch_mode_entered"):
        return manager_payload
    action_type = str(manager_payload.get("effective_action_type") or manager_payload.get("action_type") or "").strip()
    if action_type not in {
        "verify_evidence",
        "request_evidence_recheck",
        "analyze_flaws",
        "summarize_progress",
        "finalize",
        "challenge_previous_hypothesis",
        "ask_user_clarification",
    }:
        return manager_payload
    if manager_payload.get("targeted_negative_search_no_task_blocked"):
        return manager_payload
    if _review_issue_pending_candidate_exists(state):
        return manager_payload
    if _review_issue_discovery_recently_attempted(recent_turn_logs):
        return manager_payload
    try:
        _targets, selector_menu = _augmented_review_issue_selector_menu_from_state(
            state or {},
            target_max_items=12,
            selector_max_items=12,
            selector_max_per_claim=3,
            selector_max_per_type=4,
        )
    except Exception:
        selector_menu = []
    if not selector_menu:
        return manager_payload

    updated = dict(manager_payload)
    updated["decision"] = "continue"
    updated["final_decision"] = "undecided"
    updated["final_report"] = ""
    updated["action_type"] = "analyze_flaws"
    updated["effective_action_type"] = "analyze_flaws"
    updated["phase"] = "normal_review"
    updated["turn_mode"] = "normal_evidence"
    updated["recovery_patch_mode_entered"] = False
    updated["finalize_blocked_by_phase"] = False
    updated["negative_evidence_formation_required"] = False
    updated["targeted_negative_search_required"] = False
    updated["negative_evidence_binding_retry_required"] = False
    updated["compact_negative_pass_required"] = False
    updated["hard_negative_diagnosis_required"] = False
    updated["review_issue_discovery_required"] = True
    updated["freeform_reviewer_negative_discovery_required"] = True
    updated["freeform_reviewer_negative_enabled"] = True
    updated["freeform_reviewer_negative_stage"] = "candidate_discovery"
    updated["policy_source"] = "review_issue_discovery_override"
    updated["selected_agents"] = [agent for agent in ["Critique Agent"] if agent in worker_ids][:worker_limit] or list(worker_ids[:1])
    updated["review_issue_candidate_selector_menu_snapshot"] = copy.deepcopy(selector_menu)
    updated["review_issue_candidate_selector_menu_snapshot_count"] = len(selector_menu)
    updated.pop("review_issue_discovery_empty_selector_menu", None)
    menu_claim_ids = [
        str(item.get("claim_id") or "").strip()
        for item in selector_menu
        if isinstance(item, dict) and str(item.get("claim_id") or "").strip()
    ]
    if menu_claim_ids:
        updated["target_claim_ids"] = list(dict.fromkeys(menu_claim_ids))[:2]
    else:
        updated["target_claim_ids"] = []
    updated["target_flaw_ids"] = []
    updated["target_evidence_ids"] = []
    updated["target_hypotheses"] = []
    updated["focus"] = (
        "Act like a peer reviewer and select likely paper review issues from the visible review_issue_candidate_selector_menu. "
        "Do not create verified negative evidence in this turn. Prefer selected_menu_items with copied candidate_menu_id values; "
        "write full review_issue_candidates only as a free-form fallback when no menu item fits."
    )
    notes = list(updated.get("policy_notes") or [])
    notes.append(
        "Runner upgraded this turn to Critique selector discovery because the visible augmented review_issue_candidate_selector_menu had verifier-ready items."
    )
    updated["policy_notes"] = list(dict.fromkeys(notes))[:8]
    return _apply_turn_mode(updated)


def _is_selector_style_review_issue_discovery_turn(manager_payload: Dict[str, Any]) -> bool:
    if not isinstance(manager_payload, dict):
        return False
    if manager_payload.get("review_issue_discovery_required"):
        return False
    if not manager_payload.get("freeform_reviewer_negative_discovery_required"):
        return False
    if str(manager_payload.get("freeform_reviewer_negative_stage") or "").strip() != "candidate_discovery":
        return False
    selected = {
        str(agent or "").strip()
        for agent in manager_payload.get("selected_agents", []) or []
        if str(agent or "").strip()
    }
    if "Critique Agent" not in selected:
        return False
    focus_text = " ".join(
        str(manager_payload.get(key) or "")
        for key in ("focus", "rationale", "active_focus")
    ).lower()
    return (
        "review_issue_candidate_selector_menu" in focus_text
        or "selected_menu_items" in focus_text
        or "candidate_menu_id" in focus_text
    )


def _standardize_selector_style_review_issue_discovery_turn(
    manager_payload: Dict[str, Any],
    state: Dict[str, Any],
    *,
    mode: str,
    worker_ids: Sequence[str],
    worker_limit: int,
    recent_turn_logs: Sequence[Dict[str, Any]],
    step: int,
    turn_cap: int,
) -> Dict[str, Any]:
    if not _is_selector_style_review_issue_discovery_turn(manager_payload):
        return manager_payload
    if mode != "s4" or "Critique Agent" not in worker_ids:
        return manager_payload
    if not (
        _review_issue_bundle_enabled()
        and _targeted_negative_search_enabled()
        and (_freeform_reviewer_negative_enabled() or _review_issue_bundle_enabled())
    ):
        return manager_payload
    if turn_cap > 0 and step >= turn_cap:
        return manager_payload
    phase = str(manager_payload.get("phase") or state.get("phase") or "").strip().lower()
    turn_mode = _normalize_turn_mode(manager_payload.get("turn_mode"))
    if phase == "recovery" or turn_mode == "recovery_patch" or manager_payload.get("recovery_patch_mode_entered"):
        return manager_payload
    if _review_issue_pending_candidate_exists(state):
        return manager_payload
    if _review_issue_discovery_recently_attempted(recent_turn_logs):
        return manager_payload
    try:
        _targets, selector_menu = _augmented_review_issue_selector_menu_from_state(
            state or {},
            target_max_items=12,
            selector_max_items=12,
            selector_max_per_claim=3,
            selector_max_per_type=4,
        )
    except Exception:
        selector_menu = []
    if not selector_menu:
        return manager_payload

    updated = dict(manager_payload)
    original_policy = str(updated.get("policy_source") or "")
    if original_policy:
        updated["review_issue_discovery_original_policy_source"] = original_policy
    updated["decision"] = "continue"
    updated["final_decision"] = "undecided"
    updated["final_report"] = ""
    updated["action_type"] = "analyze_flaws"
    updated["effective_action_type"] = "analyze_flaws"
    updated["phase"] = "normal_review"
    updated["turn_mode"] = "normal_evidence"
    updated["recovery_patch_mode_entered"] = False
    updated["finalize_blocked_by_phase"] = False
    updated["negative_evidence_formation_required"] = False
    updated["targeted_negative_search_required"] = False
    updated["negative_evidence_binding_retry_required"] = False
    updated["compact_negative_pass_required"] = False
    updated["hard_negative_diagnosis_required"] = False
    updated["review_issue_discovery_required"] = True
    updated["freeform_reviewer_negative_discovery_required"] = True
    updated["freeform_reviewer_negative_enabled"] = True
    updated["freeform_reviewer_negative_stage"] = "candidate_discovery"
    updated["policy_source"] = "review_issue_discovery_bridge_standardized"
    updated["selected_agents"] = [agent for agent in ["Critique Agent"] if agent in worker_ids][:worker_limit] or list(worker_ids[:1])
    updated["review_issue_candidate_selector_menu_snapshot"] = copy.deepcopy(selector_menu)
    updated["review_issue_candidate_selector_menu_snapshot_count"] = len(selector_menu)
    updated.pop("review_issue_discovery_empty_selector_menu", None)
    menu_claim_ids = [
        str(item.get("claim_id") or "").strip()
        for item in selector_menu
        if isinstance(item, dict) and str(item.get("claim_id") or "").strip()
    ]
    updated["target_claim_ids"] = list(dict.fromkeys(menu_claim_ids))[:3]
    updated["target_flaw_ids"] = []
    updated["target_evidence_ids"] = []
    updated["target_hypotheses"] = []
    updated["focus"] = (
        "Act like a peer reviewer and select likely paper review issues from the visible review_issue_candidate_selector_menu. "
        "Do not create verified negative evidence in this turn. Prefer selected_menu_items with copied candidate_menu_id values; "
        "write full review_issue_candidates only as a free-form fallback when no menu item fits."
    )
    notes = list(updated.get("policy_notes") or [])
    notes.append(
        "Standardized selector-style reviewer-negative discovery into the review_issue_discovery_required path with the augmented selector menu snapshot."
    )
    updated["policy_notes"] = list(dict.fromkeys(notes))[:8]
    return _apply_turn_mode(updated)


def _selector_menu_lookup_from_state(state: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    targets, visible_menu = _augmented_review_issue_selector_menu_from_state(
        state or {},
        target_max_items=12,
        selector_max_items=12,
        selector_max_per_claim=3,
        selector_max_per_type=4,
    )
    # The Critique prompt renders both the compact selector menu and each
    # target's short per-claim menu.  A selected id is safe to recover if it is
    # present in either rendered menu; arbitrary stale/hallucinated ids remain
    # ignored because they are not regenerated from the current state.
    full_by_id: Dict[str, Dict[str, Any]] = {}
    for target in targets or []:
        if not isinstance(target, dict):
            continue
        for item in target.get("review_issue_candidate_menu") or []:
            if not isinstance(item, dict):
                continue
            menu_id = str(item.get("candidate_menu_id") or "").strip()
            if menu_id:
                full_by_id[menu_id] = item
    for item in visible_menu or []:
        if not isinstance(item, dict):
            continue
        menu_id = str(item.get("candidate_menu_id") or "").strip()
        if menu_id and menu_id not in full_by_id:
            full_by_id[menu_id] = item
    return full_by_id


def _attach_review_issue_selector_snapshot(
    manager_payload: Dict[str, Any],
    state: Dict[str, Any],
) -> Dict[str, Any]:
    if not isinstance(manager_payload, dict) or not manager_payload.get("review_issue_discovery_required"):
        return manager_payload
    if manager_payload.get("review_issue_candidate_selector_menu_snapshot"):
        return manager_payload
    try:
        _targets, selector_menu = _augmented_review_issue_selector_menu_from_state(
            state or {},
            target_max_items=12,
            selector_max_items=12,
            selector_max_per_claim=3,
            selector_max_per_type=4,
        )
    except Exception:
        selector_menu = []
    if not selector_menu:
        manager_payload["review_issue_candidate_selector_menu_snapshot_count"] = 0
        manager_payload["review_issue_discovery_empty_selector_menu"] = True
        return manager_payload
    manager_payload["review_issue_candidate_selector_menu_snapshot"] = copy.deepcopy(selector_menu)
    manager_payload["review_issue_candidate_selector_menu_snapshot_count"] = len(selector_menu)
    manager_payload.pop("review_issue_discovery_empty_selector_menu", None)
    return manager_payload


def _downgrade_empty_review_issue_discovery_turn(manager_payload: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(manager_payload, dict):
        return manager_payload
    if not manager_payload.get("review_issue_discovery_required"):
        return manager_payload
    if manager_payload.get("review_issue_candidate_selector_menu_snapshot"):
        return manager_payload
    if not manager_payload.get("review_issue_discovery_empty_selector_menu"):
        return manager_payload
    updated = dict(manager_payload)
    updated["review_issue_discovery_required"] = False
    updated["freeform_reviewer_negative_discovery_required"] = False
    updated["review_issue_discovery_skipped_reason"] = "empty_selector_menu"
    updated["freeform_reviewer_negative_stage"] = "selector_discovery_skipped_no_menu"
    notes = list(updated.get("policy_notes") or [])
    notes.append("Critique selector discovery was downgraded because no visible selector menu item was available.")
    updated["policy_notes"] = list(dict.fromkeys(notes))[:8]
    focus = _candidate_text(updated.get("focus"), 260)
    if not focus or "review_issue_candidate_selector_menu" in focus:
        updated["focus"] = (
            "Analyze existing evidence, claims, and candidate flaws without selecting review_issue_candidate_selector_menu ids; "
            "no visible selector menu item is available in this turn."
        )
    return updated


def _candidate_from_selected_menu_item(
    menu_item: Dict[str, Any],
    selection: Dict[str, Any],
    index: int,
) -> Dict[str, Any]:
    menu_id = str(menu_item.get("candidate_menu_id") or selection.get("candidate_menu_id") or "").strip()
    expected = _candidate_text(
        menu_item.get("verifier_target_entity") or menu_item.get("expected_entity"),
        180,
    )
    observed_inventory = menu_item.get("observed_inventory")
    if not isinstance(observed_inventory, list) or not observed_inventory:
        anchor = menu_item.get("inventory_anchor") if isinstance(menu_item.get("inventory_anchor"), dict) else {}
        observed_inventory = [
            {
                "inventory_id": str(anchor.get("inventory_id") or menu_item.get("inventory_id") or ""),
                "quote": _candidate_text(anchor.get("quote") or menu_item.get("inventory_quote"), 260),
                "locator": _candidate_text(anchor.get("locator") or menu_item.get("inventory_locator"), 120),
                "observed_items": list(anchor.get("observed_items") or []),
                "inventory_type": str(anchor.get("inventory_type") or menu_item.get("inventory_type") or ""),
            }
        ]
    issue_type = str(menu_item.get("issue_type") or "")
    rationale = _candidate_text(menu_item.get("why_review_worthy") or selection.get("rationale"), 220)
    selection_rationale = _candidate_text(selection.get("rationale"), 220)
    rationale = re.sub(r"\s*\.\.\.\[truncated\]\s*", " ", rationale).strip()
    selection_rationale = re.sub(r"\s*\.\.\.\[truncated\]\s*", " ", selection_rationale).strip()
    return {
        "candidate_id": f"review-issue-candidate-selected-menu-{index}",
        "candidate_menu_id": menu_id,
        "review_issue_candidate_menu_item": copy.deepcopy(menu_item),
        "obligation_id": str(menu_item.get("obligation_id") or ""),
        "claim_id": str(menu_item.get("claim_id") or ""),
        "claim": _candidate_text(menu_item.get("claim") or menu_item.get("claim_text"), 240),
        "weakness": (
            f"Verify whether the paper leaves the review issue target uncovered: {expected}."
            if expected
            else "Verify the selected review issue menu target."
        ),
        "issue_type": issue_type,
        "negative_type": issue_type,
        "required_evidence_type": str(menu_item.get("required_evidence_type") or ""),
        "quote_grounding_mode": "absence_or_requirement_gap",
        "missing_or_weak_items": [expected] if expected else [],
        "observed_inventory": observed_inventory,
        "possible_counterevidence_terms": list(
            menu_item.get("counterevidence_search_terms")
            or menu_item.get("counterevidence_aliases")
            or []
        )[:8],
        "source_of_expectation": "reviewer_candidate",
        "source": "critique_selected_menu_item",
        "discovery_origin": "critique_payload_menu_selected",
        "review_issue_slot": str(menu_item.get("review_issue_slot") or menu_item.get("slot") or ""),
        "entity_source": str(menu_item.get("entity_source") or ""),
        "rationale": rationale,
        "selection_rationale": selection_rationale,
        "confidence": selection.get("confidence", 0.5),
        "status": "pending_absence_audit",
    }


def _resolve_selected_review_issue_menu_item(
    selected_menu_id: str,
    menu_by_id: Dict[str, Dict[str, Any]],
) -> Tuple[str, Dict[str, Any]]:
    menu_id = str(selected_menu_id or "").strip()
    if not menu_id:
        return "", {}
    exact = menu_by_id.get(menu_id)
    if exact:
        return menu_id, exact
    if not menu_id.startswith("rim-c") or len(menu_id) < 24:
        return "", {}
    matches = [
        (candidate_id, item)
        for candidate_id, item in menu_by_id.items()
        if isinstance(item, dict)
        and (
            candidate_id.startswith(menu_id)
            or menu_id.startswith(candidate_id)
        )
    ]
    if len(matches) != 1:
        return "", {}
    return matches[0]


def _maybe_recover_selected_review_issue_menu_items(
    worker_payload: Dict[str, Any],
    state: Dict[str, Any],
    manager_payload: Optional[Dict[str, Any]] = None,
    *,
    trace_worker: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    selections = worker_payload.get("selected_menu_items") if isinstance(worker_payload, dict) else []
    if not isinstance(selections, list) or not selections:
        return worker_payload
    menu_by_id: Dict[str, Dict[str, Any]] = {}
    if isinstance(manager_payload, dict):
        for item in manager_payload.get("review_issue_candidate_selector_menu_snapshot") or []:
            if not isinstance(item, dict):
                continue
            menu_id = str(item.get("candidate_menu_id") or "").strip()
            if menu_id:
                menu_by_id[menu_id] = item
    state_menu_by_id = _selector_menu_lookup_from_state(state or {})
    for menu_id, item in state_menu_by_id.items():
        menu_by_id.setdefault(menu_id, item)
    if not menu_by_id:
        return worker_payload
    existing_candidates = worker_payload.get("reviewer_negative_candidates")
    if not isinstance(existing_candidates, list):
        existing_candidates = []
    existing_menu_ids = {
        str(item.get("candidate_menu_id") or "").strip()
        for item in existing_candidates
        if isinstance(item, dict) and str(item.get("candidate_menu_id") or "").strip()
    }
    recovered: List[Dict[str, Any]] = []
    missing_menu_ids: List[str] = []
    for selection in selections:
        if not isinstance(selection, dict):
            continue
        decision = str(selection.get("decision") or "selected").strip().lower()
        if decision in {"reject", "rejected", "skip", "skipped", "no"}:
            continue
        menu_id = str(selection.get("candidate_menu_id") or "").strip()
        if not menu_id or menu_id in existing_menu_ids:
            continue
        resolved_menu_id, menu_item = _resolve_selected_review_issue_menu_item(menu_id, menu_by_id)
        if not menu_item:
            missing_menu_ids.append(menu_id)
            continue
        if resolved_menu_id in existing_menu_ids:
            continue
        resolved_selection = dict(selection)
        resolved_selection["candidate_menu_id"] = resolved_menu_id
        recovered.append(
            _candidate_from_selected_menu_item(
                menu_item,
                resolved_selection,
                len(existing_candidates) + len(recovered) + 1,
            )
        )
        existing_menu_ids.add(resolved_menu_id)
        if trace_worker is not None and resolved_menu_id != menu_id:
            trace_worker.setdefault("review_issue_selected_menu_prefix_resolutions", []).append(
                {"selected_menu_id": menu_id, "resolved_menu_id": resolved_menu_id}
            )
        if len(existing_candidates) + len(recovered) >= 12:
            break
    if not recovered:
        if trace_worker is not None and missing_menu_ids:
            trace_worker["review_issue_selected_menu_missing_ids"] = list(dict.fromkeys(missing_menu_ids))[:8]
            trace_worker["review_issue_selected_menu_recovery_used"] = False
        return worker_payload
    normalized = normalize_review_update_payload({"reviewer_negative_candidates": recovered})
    recovered_candidates = normalized.get("reviewer_negative_candidates", [])
    if not recovered_candidates:
        if trace_worker is not None:
            trace_worker["review_issue_selected_menu_recovery_normalization_failed"] = True
        return worker_payload
    updated = copy.deepcopy(worker_payload)
    updated["reviewer_negative_candidates"] = (list(existing_candidates) + recovered_candidates)[:12]
    summary = _candidate_text(updated.get("dialogue_summary"), 800)
    updated["dialogue_summary"] = (
        (summary + " " if summary else "")
        + f"Recovered {len(recovered_candidates)} selected review issue menu items into verifier-ready candidates."
    )
    if trace_worker is not None:
        trace_worker["review_issue_selected_menu_recovery_used"] = True
        trace_worker["review_issue_selected_menu_recovered_count"] = len(recovered_candidates)
        trace_worker["review_issue_selected_menu_ids"] = [
            str(item.get("candidate_menu_id") or "") for item in recovered_candidates
        ]
    return updated


def _maybe_seed_review_issue_discovery_payload(
    worker_id: str,
    worker_payload: Dict[str, Any],
    state: Dict[str, Any],
    manager_payload: Optional[Dict[str, Any]],
    *,
    trace_worker: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    if worker_id != "Critique Agent":
        return worker_payload
    if not isinstance(worker_payload, dict):
        return worker_payload
    formal_discovery_turn = bool(
        isinstance(manager_payload, dict)
        and manager_payload.get("review_issue_discovery_required")
    )
    selected_menu_items = worker_payload.get("selected_menu_items")
    has_selected_menu_items = isinstance(selected_menu_items, list) and any(
        isinstance(item, dict) and str(item.get("candidate_menu_id") or "").strip()
        for item in selected_menu_items
    )
    if has_selected_menu_items:
        worker_payload = _maybe_recover_selected_review_issue_menu_items(
            worker_payload,
            state or {},
            manager_payload if isinstance(manager_payload, dict) else None,
            trace_worker=trace_worker,
        )
    if not formal_discovery_turn:
        return worker_payload
    existing = worker_payload.get("reviewer_negative_candidates")
    existing_candidates = existing if isinstance(existing, list) else []
    if _critique_only_discovery_eval_enabled():
        updated = copy.deepcopy(worker_payload)
        updated["critique_only_discovery_eval"] = True
        if trace_worker is not None:
            trace_worker["critique_only_discovery_eval"] = True
            trace_worker["review_issue_seed_fallback_skipped_for_critique_only_eval"] = True
            trace_worker["seed_topup_after_critique_failure_count"] = 0
        return updated
    target_candidate_count = 12
    if len(existing_candidates) >= target_candidate_count:
        return worker_payload
    seeded = _seed_review_issue_candidates_from_targets(state or {}, max_candidates=target_candidate_count)
    if not seeded:
        return worker_payload
    normalized_seed = normalize_review_update_payload({"reviewer_negative_candidates": seeded})
    seed_candidates = normalized_seed.get("reviewer_negative_candidates", [])
    if not seed_candidates:
        return worker_payload
    seen: set[Tuple[str, str, str]] = set()
    seen_semantic_clusters: set[Tuple[str, str, str]] = set()
    for candidate in existing_candidates:
        if not isinstance(candidate, dict):
            continue
        seen.add(
            (
                str(candidate.get("claim_id") or ""),
                str(candidate.get("negative_type") or candidate.get("issue_type") or ""),
                "|".join(str(item or "").strip().lower() for item in candidate.get("missing_or_weak_items") or []),
            )
        )
        semantic_key = _review_issue_candidate_semantic_cluster_key(candidate)
        if semantic_key[0]:
            seen_semantic_clusters.add(semantic_key)
    top_up: List[Dict[str, Any]] = []
    shadowed_by_existing_count = 0
    for candidate in seed_candidates:
        key = (
            str(candidate.get("claim_id") or ""),
            str(candidate.get("negative_type") or candidate.get("issue_type") or ""),
            "|".join(str(item or "").strip().lower() for item in candidate.get("missing_or_weak_items") or []),
        )
        semantic_key = _review_issue_candidate_semantic_cluster_key(candidate)
        if key in seen:
            continue
        if semantic_key[0] and semantic_key in seen_semantic_clusters:
            shadowed_by_existing_count += 1
            continue
        seen.add(key)
        if semantic_key[0]:
            seen_semantic_clusters.add(semantic_key)
        top_up.append(candidate)
        if len(existing_candidates) + len(top_up) >= target_candidate_count:
            break
    if not top_up:
        if trace_worker is not None and shadowed_by_existing_count:
            trace_worker["review_issue_seed_topup_shadowed_by_existing_cluster_count"] = shadowed_by_existing_count
        return worker_payload
    updated = copy.deepcopy(worker_payload)
    updated["reviewer_negative_candidates"] = (list(existing_candidates) + top_up)[:target_candidate_count]
    summary = _candidate_text(updated.get("dialogue_summary"), 800)
    updated["dialogue_summary"] = (
        (summary + " " if summary else "")
        + f"Runner added {len(top_up)} review issue seed candidates from entity obligations and inventory for strict verification."
    )
    if trace_worker is not None:
        trace_worker["review_issue_seed_fallback_used"] = True
        trace_worker["review_issue_seed_candidate_count"] = len(top_up)
        if existing_candidates:
            trace_worker["seed_topup_after_critique_failure_count"] = len(top_up)
        if shadowed_by_existing_count:
            trace_worker["review_issue_seed_topup_shadowed_by_existing_cluster_count"] = shadowed_by_existing_count
        trace_worker["review_issue_seed_candidate_ids"] = [
            str(item.get("candidate_id") or "") for item in top_up
        ]
    return updated


def _worker_payload_trace_flags(trace_worker: Dict[str, Any]) -> Dict[str, Any]:
    """Copy lightweight recovery telemetry onto persisted turn worker rows."""
    if not isinstance(trace_worker, dict):
        return {}
    keys = (
        "review_issue_selected_menu_recovery_used",
        "review_issue_selected_menu_recovered_count",
        "review_issue_selected_menu_ids",
        "review_issue_selected_menu_missing_ids",
        "review_issue_selected_menu_recovery_normalization_failed",
        "review_issue_seed_fallback_used",
        "review_issue_seed_candidate_count",
        "review_issue_seed_candidate_ids",
        "review_issue_seed_topup_shadowed_by_existing_cluster_count",
        "review_issue_seed_fallback_skipped_for_critique_only_eval",
        "critique_only_discovery_eval",
        "seed_topup_after_critique_failure_count",
    )
    return {key: trace_worker[key] for key in keys if key in trace_worker}


def parse_agent_payload(
    agent_id: str,
    raw_text: str,
    available_workers: Optional[Iterable[str]] = None,
    manager_payload: Optional[Dict[str, Any]] = None,
) -> tuple[Dict[str, Any], bool]:
    recovery_patch_mode = _normalize_turn_mode((manager_payload or {}).get("turn_mode")) == "recovery_patch"
    targeted_negative_mode = bool((manager_payload or {}).get("targeted_negative_search_required"))
    raw_prefix = str(raw_text or "").lstrip().lower()
    if (
        agent_id == "Evidence Agent"
        and targeted_negative_mode
        and not raw_prefix.startswith(("<json>", "{"))
        and _looks_like_prompt_or_schema_echo(raw_text)
    ):
        try:
            partial_payload = extract_evidence_partial_payload(
                raw_text,
                allow_empty_not_assessable=True,
            )
            normalized = normalize_agent_payload(agent_id, partial_payload, available_workers=available_workers)
            normalized["_partial_json_recovery"] = True
            return normalized, True
        except Exception:
            pass
        raise ValueError("Targeted negative Evidence Agent output echoed prompt/schema text instead of direct JSON.")
    try:
        payload = extract_tagged_json(raw_text)
        normalized = normalize_agent_payload(agent_id, payload, available_workers=available_workers)
        recovered, partial = _maybe_recover_review_issue_discovery_candidates(
            agent_id,
            raw_text,
            normalized,
            manager_payload,
        )
        return recovered, partial
    except Exception as original_exc:
        if agent_id == "Critique Agent" and bool((manager_payload or {}).get("review_issue_discovery_required")):
            recovered_payload, partial = _maybe_recover_review_issue_discovery_candidates(
                agent_id,
                raw_text,
                normalize_review_update_payload({}),
                manager_payload,
            )
            if partial:
                return recovered_payload, True
        if agent_id == "Evidence Agent" and not recovery_patch_mode:
            try:
                partial_payload = extract_evidence_partial_payload(
                    raw_text,
                    allow_empty_not_assessable=bool((manager_payload or {}).get("targeted_negative_search_required")),
                )
                normalized = normalize_agent_payload(agent_id, partial_payload, available_workers=available_workers)
                normalized["_partial_json_recovery"] = True
                return normalized, True
            except Exception:
                pass
        raise original_exc


def _classify_evidence_json_failure(raw_text: str, parse_error: str = "") -> str:
    raw = str(raw_text or "")
    if not raw.strip():
        return "raw_empty"
    has_json_tag = "<json>" in raw
    has_json_end = "</json>" in raw
    if has_json_tag and not has_json_end:
        return "truncated_tagged_json"
    first_brace = raw.find("{")
    last_brace = raw.rfind("}")
    if first_brace == -1:
        return "no_json_object"
    if last_brace == -1 or last_brace < first_brace:
        return "truncated_json_object"
    if parse_error:
        return "invalid_json"
    return "unknown"


def _record_evidence_json_contract_status(
    agent_id: str,
    trace_worker: Dict[str, Any],
    manager_payload: Dict[str, Any],
    raw_text: str,
    prompt_text: str = "",
    parse_error: str = "",
    partial_json_recovery: bool = False,
    fallback_payload_used: bool = False,
) -> None:
    if agent_id != "Evidence Agent":
        return
    failure_type = _classify_evidence_json_failure(raw_text, parse_error=parse_error) if parse_error else ""
    if partial_json_recovery:
        status = "partial_recovered"
    elif fallback_payload_used:
        status = "fallback_used"
    elif parse_error:
        status = failure_type or "parse_error"
    else:
        status = "json_valid"
    fields = {
        "evidence_json_contract_mode": "json_only_v1",
        "evidence_json_parse_status": status,
        "evidence_json_failure_type": failure_type,
        "evidence_json_parse_error": str(parse_error or "")[:240],
        "evidence_json_partial_recovery": bool(partial_json_recovery),
        "evidence_json_fallback_payload_used": bool(fallback_payload_used),
        "evidence_json_raw_chars": len(str(raw_text or "")),
        "evidence_json_prompt_chars": len(str(prompt_text or "")),
    }
    if status not in {"json_valid", "partial_recovered"}:
        raw_value = str(raw_text or "")
        fields["evidence_json_raw_head"] = raw_value[:360]
        fields["evidence_json_raw_tail"] = raw_value[-360:] if len(raw_value) > 360 else raw_value
    trace_worker.update(fields)
    manager_payload.update(fields)


_EMPIRICAL_OBS_PATTERN = re.compile(
    r"\b(experiment|experiments|evaluation|evaluations|result|results|baseline|baselines|dataset|datasets|metric|metrics|performance|outperform|benchmark|ablation|table|figure|fig\.?)\b",
    re.IGNORECASE,
)
_EMPIRICAL_TABLE_PATTERN = re.compile(r"\b(table|figure|fig\.?|ablation)\b", re.IGNORECASE)
_EMPIRICAL_METHOD_PATTERN = re.compile(r"\b(method|methods|methodology|approach|model|framework|algorithm|architecture)\b", re.IGNORECASE)
_EMPIRICAL_NEGATIVE_PATTERN = re.compile(
    r"\b(lack|lacks|missing|insufficient|limited|weak|no|without|cannot verify|not provided|unclear|unsupported)\b",
    re.IGNORECASE,
)
_SUPPORT_STANCES = {"supports", "support", "supported", "partially_supports", "partially_support", "positive"}


def _text_blob(value: Any) -> str:
    if isinstance(value, dict):
        return " ".join(_text_blob(item) for item in value.values())
    if isinstance(value, list):
        return " ".join(_text_blob(item) for item in value)
    return str(value or "")


def _pattern_count(pattern: re.Pattern[str], text: str) -> int:
    return len(pattern.findall(text or ""))


def _evidence_item_blob(item: Dict[str, Any]) -> str:
    return " ".join(str(item.get(key) or "") for key in ("evidence", "source", "section", "rationale", "binding_rationale", "stance", "strength"))


def _record_evidence_empirical_observability(
    agent_id: str,
    trace_worker: Dict[str, Any],
    manager_payload: Dict[str, Any],
    raw_text: str,
    worker_payload: Optional[Dict[str, Any]] = None,
) -> None:
    if agent_id != "Evidence Agent":
        return
    raw = str(raw_text or "")
    raw_empirical_terms = _pattern_count(_EMPIRICAL_OBS_PATTERN, raw)
    raw_table_terms = _pattern_count(_EMPIRICAL_TABLE_PATTERN, raw)
    raw_negative_terms = _pattern_count(_EMPIRICAL_NEGATIVE_PATTERN, raw)
    evidence_items = []
    if isinstance(worker_payload, dict) and isinstance(worker_payload.get("evidence_map"), list):
        evidence_items = [item for item in worker_payload.get("evidence_map") or [] if isinstance(item, dict)]
    empirical_count = 0
    table_count = 0
    method_count = 0
    strong_empirical_count = 0
    support_empirical_count = 0
    for item in evidence_items:
        blob = _evidence_item_blob(item)
        empirical = bool(_EMPIRICAL_OBS_PATTERN.search(blob))
        if empirical:
            empirical_count += 1
        if _EMPIRICAL_TABLE_PATTERN.search(blob):
            table_count += 1
        if _EMPIRICAL_METHOD_PATTERN.search(blob):
            method_count += 1
        stance = str(item.get("stance") or "").strip().lower()
        strength = str(item.get("strength") or "").strip().lower()
        if empirical and stance in _SUPPORT_STANCES:
            support_empirical_count += 1
            if strength == "strong":
                strong_empirical_count += 1
    if raw_empirical_terms == 0:
        status = "no_raw_empirical_signal"
    elif not evidence_items:
        status = "raw_empirical_no_payload_evidence"
    elif empirical_count == 0:
        status = "raw_empirical_payload_no_empirical_evidence"
    elif strong_empirical_count == 0:
        status = "empirical_payload_without_strong_support"
    else:
        status = "strong_empirical_payload_formed"
    fields = {
        "evidence_empirical_observability_mode": "context_raw_payload_v1",
        "evidence_raw_contains_empirical_terms": raw_empirical_terms > 0,
        "evidence_raw_contains_table_or_figure_terms": raw_table_terms > 0,
        "evidence_raw_empirical_term_count": raw_empirical_terms,
        "evidence_raw_negative_empirical_term_count": raw_negative_terms if raw_empirical_terms else 0,
        "evidence_payload_evidence_count": len(evidence_items),
        "evidence_payload_empirical_evidence_count": empirical_count,
        "evidence_payload_table_or_figure_count": table_count,
        "evidence_payload_method_evidence_count": method_count,
        "evidence_payload_strong_empirical_count": strong_empirical_count,
        "evidence_payload_support_empirical_count": support_empirical_count,
        "evidence_payload_has_empirical_evidence": empirical_count > 0,
        "evidence_empirical_structuring_status": status,
    }
    trace_worker.update(fields)
    manager_payload.update(fields)


def _scoped_evidence_id(evidence_id: Any, turn_id: int) -> str:
    raw = str(evidence_id or "").strip()
    if not raw:
        raw = "evidence"
    if re.search(r"(?:^|-)turn-\d+(?:-|$)", raw):
        return raw
    safe = re.sub(r"[^A-Za-z0-9_.:-]+", "-", raw).strip("-") or "evidence"
    return f"{safe}-turn-{int(turn_id)}"


def _scope_evidence_ids_for_turn(payload: Dict[str, Any], turn_id: int) -> Dict[str, Any]:
    if not isinstance(payload, dict):
        return payload
    evidence_items = payload.get("evidence_map") or []
    if not isinstance(evidence_items, list):
        return payload
    id_map: Dict[str, str] = {}
    used: set[str] = set()
    for idx, evidence in enumerate(evidence_items, start=1):
        if not isinstance(evidence, dict):
            continue
        old_id = str(evidence.get("evidence_id") or f"evidence-{idx}")
        new_id = _scoped_evidence_id(old_id, turn_id)
        if new_id in used:
            new_id = f"{new_id}-{idx}"
        used.add(new_id)
        evidence["evidence_id"] = new_id
        id_map[old_id] = new_id
    if not id_map:
        return payload

    def _mapped(value: Any) -> Any:
        return id_map.get(str(value), value)

    for note in payload.get("conflict_notes") or []:
        if isinstance(note, dict) and note.get("evidence_id") is not None:
            note["evidence_id"] = _mapped(note.get("evidence_id"))
    for flaw in payload.get("flaw_candidates") or []:
        if not isinstance(flaw, dict):
            continue
        if isinstance(flaw.get("evidence_ids"), list):
            flaw["evidence_ids"] = [_mapped(item) for item in flaw.get("evidence_ids") or []]
        if isinstance(flaw.get("negative_evidence_ids"), list):
            flaw["negative_evidence_ids"] = [_mapped(item) for item in flaw.get("negative_evidence_ids") or []]
        if flaw.get("evidence_id") is not None:
            flaw["evidence_id"] = _mapped(flaw.get("evidence_id"))
    for claim in payload.get("claims") or []:
        if isinstance(claim, dict) and isinstance(claim.get("supporting_evidence_ids"), list):
            claim["supporting_evidence_ids"] = [_mapped(item) for item in claim.get("supporting_evidence_ids") or []]
    patch = payload.get("recovery_patch")
    if isinstance(patch, dict) and isinstance(patch.get("supporting_evidence_ids"), list):
        patch["supporting_evidence_ids"] = [_mapped(item) for item in patch.get("supporting_evidence_ids") or []]
    payload["evidence_id_scope_turn"] = int(turn_id)
    payload["evidence_id_scope_map"] = id_map
    return payload


def _find_items_by_ids(items: Sequence[Dict[str, Any]], key: str, ids: Sequence[str]) -> List[Dict[str, Any]]:
    lookup = {item.get(key): item for item in items if item.get(key)}
    return [lookup[item_id] for item_id in ids if item_id in lookup]


def _build_target_brief(task: Dict[str, Any], manager_payload: Dict[str, Any]) -> str:
    state = task.get("review_state", {})
    target_claims = _find_items_by_ids(state.get("claims", []), "claim_id", manager_payload.get("target_claim_ids", []))
    target_flaws = _find_items_by_ids(state.get("flaw_candidates", []), "flaw_id", manager_payload.get("target_flaw_ids", []))
    target_evidence = _find_items_by_ids(state.get("evidence_map", []), "evidence_id", manager_payload.get("target_evidence_ids", []))
    target_hypotheses = manager_payload.get("target_hypotheses", [])[:4]

    sections = []
    if target_claims:
        sections.append("Target Claims: " + json.dumps(target_claims, ensure_ascii=False))
    if target_flaws:
        sections.append("Target Flaws: " + json.dumps(target_flaws, ensure_ascii=False))
    if target_evidence:
        sections.append("Target Evidence: " + json.dumps(target_evidence, ensure_ascii=False))
    if target_hypotheses:
        sections.append("Target Hypotheses: " + json.dumps(target_hypotheses, ensure_ascii=False))
    if not sections:
        return "No explicit target objects were specified for this turn."
    return "\n".join(sections)


def _resolve_prompt_template(agent_id: str, manager_payload: Optional[Dict[str, Any]] = None) -> str:
    if (
        agent_id == "Critique Agent"
        and isinstance(manager_payload, dict)
        and manager_payload.get("review_issue_discovery_required")
    ):
        return REVIEW_ISSUE_DISCOVERY_PROMPT
    if (
        agent_id == "Evidence Agent"
        and isinstance(manager_payload, dict)
        and manager_payload.get("freeform_reviewer_negative_discovery_required")
        and manager_payload.get("freeform_reviewer_negative_enabled")
    ):
        return FREEFORM_REVIEWER_NEGATIVE_PROMPT
    if agent_id == "Evidence Agent" and isinstance(manager_payload, dict) and manager_payload.get("targeted_negative_search_required"):
        return TARGETED_NEGATIVE_EVIDENCE_PROMPT
    if agent_id == "Evidence Agent" and isinstance(manager_payload, dict) and _is_negative_evidence_formation_turn(manager_payload):
        return AGENT_SPECS[agent_id].prompt
    if isinstance(manager_payload, dict) and (
        _normalize_turn_mode(manager_payload.get("turn_mode")) == "recovery_patch"
        or _is_recovery_triggered_turn(manager_payload)
    ):
        return RECOVERY_PATCH_PROMPT
    return AGENT_SPECS[agent_id].prompt


def build_prompt(agent_id: str, env_prompt: str, team_context: str, step: int, manager_payload: Optional[Dict[str, Any]] = None) -> str:
    prompt_template = _resolve_prompt_template(agent_id, manager_payload=manager_payload)
    return (
        prompt_template.replace("{env_prompt}", env_prompt)
        .replace("{team_context}", team_context)
        .replace("{step}", str(step))
    )


def build_manager_observation(task: Dict[str, Any], worker_ids: Sequence[str]) -> str:
    base = render_manager_observation(task)
    state = task.get("review_state", {})
    routing = (
        "# Manager Routing Context\n"
        f"Available worker agents: {', '.join(worker_ids) if worker_ids else 'none'}\n"
        f"Review mode: {task.get('mode', 's4')}\n"
        f"Current phase: {state.get('phase', 'normal_review')}\n"
        f"Phase turn index: {state.get('phase_turn_index', 0)}\n"
        f"Risk readiness: {state.get('risk_profile', {}).get('readiness', 'not_ready')}\n"
        "Allowed action types: extract_claims, verify_evidence, analyze_flaws, request_evidence_recheck, challenge_previous_hypothesis, summarize_progress, ask_user_clarification, finalize.\n"
        "Decide which review objective is most urgent before routing workers or finalizing."
    )
    return _clip_text(f"{base}\n\n{routing}", MAX_MANAGER_OBSERVATION_CHARS)

def build_worker_observation(task: Dict[str, Any], manager_payload: Dict[str, Any], agent_id: str) -> str:
    if agent_id == "Claim Agent":
        base = render_claim_observation(task, manager_payload)
    elif agent_id == "Evidence Agent":
        base = render_evidence_observation(task, manager_payload)
    elif agent_id == "Critique Agent":
        base = render_critique_observation(task, manager_payload)
    elif agent_id.startswith("General Reviewer Agent") or agent_id == "Reviewer Agent":
        base = render_general_reviewer_observation(task, manager_payload)
    else:
        base = render_review_observation(task)
    focus = manager_payload.get("focus", "")
    rationale = manager_payload.get("rationale", "")
    phase = _normalize_phase(manager_payload.get("phase")) or _normalize_phase(task.get("review_state", {}).get("phase")) or "normal_review"
    phase_turn_index = int(manager_payload.get("phase_turn_index") or task.get("review_state", {}).get("phase_turn_index", 0) or 0)
    action_type = str(manager_payload.get("effective_action_type") or manager_payload.get("action_type") or "").strip()
    turn_mode = _normalize_turn_mode(manager_payload.get("turn_mode")) or ("recovery_patch" if action_type in RECOVERY_PATCH_ACTION_TYPES or _is_recovery_triggered_turn(manager_payload) else "normal_evidence")
    target_brief = _clip_text(_build_target_brief(task, manager_payload), 900)
    mode_block = (
        "# Turn Mode\n"
        f"Phase: {phase}\n"
        f"Phase Turn Index: {phase_turn_index}\n"
        f"Turn Mode: {turn_mode}\n"
        f"Recovery Patch Mode Entered: {turn_mode == 'recovery_patch'}\n"
    )
    if turn_mode == "recovery_patch":
        mode_block += (
            "Patch Mode Requirement: Output exactly one strict JSON object with either `action=apply_recovery_patch` or `action=blocked`. "
            "Supported target_type values are `claim`, `flaw`, `hypothesis`, `gap`, and `evidence_link`; use `gap` to close stale evidence gaps and `evidence_link` to unbind invalid evidence-to-claim links. "
            "Do not return normal evidence prose, critique paragraphs, or generic review text. System salvage remains internal and will be logged as `system_salvaged`.\n\n"
        )
    else:
        mode_block += "Patch Mode Requirement: inactive; follow the action type with normal structured review updates.\n\n"
    negative_evidence_required = bool(
        manager_payload.get("negative_evidence_formation_required")
        or manager_payload.get("policy_source") in {
            "negative_evidence_formation_override",
            "compact_negative_pass_override",
        }
        or (
            manager_payload.get("policy_source") == "targeted_negative_search_override"
            and manager_payload.get("targeted_negative_search_required")
        )
    )
    negative_mode_block = ""
    if negative_evidence_required:
        if manager_payload.get("policy_source") == "compact_negative_pass_override":
            negative_mode_block = (
                "# Compact Negative Pass\n"
                "negative_evidence_formation_required=true\n"
                "Primary task: use visible verified paper quotes to bind, downgrade, or classify targeted concerns in this critique turn. "
                "If no quote directly supports a paper-side weakness, keep the item as a potential concern or assessment limitation; "
                "do not fabricate negative evidence and do not create broad standalone questions.\n\n"
            )
        else:
            negative_mode_block = (
                "# Negative Evidence Formation Mode\n"
                "negative_evidence_formation_required=true\n"
                "Primary task: find a copied paper quote that contradicts, weakens, or demonstrates missing support for the target flaw and target claim. "
                "Legal outputs in this mode are only: (1) one negative evidence item with copied raw_quote, source_locator, claim_id, "
                "stance=missing or contradicts, negative_evidence_type, and required_evidence_type; or (2) an unresolved question with status=not_assessable. "
                "Do not add positive support in this mode. If no direct negative quote exists, emit the unresolved question instead of fabricating evidence.\n\n"
            )
    targeted_negative_search_block = ""
    if manager_payload.get("targeted_negative_search_required") and agent_id == "Evidence Agent":
        if (
            manager_payload.get("freeform_reviewer_negative_enabled")
            and manager_payload.get("freeform_reviewer_negative_stage") == "candidate_discovery"
        ):
            targeted_negative_search_block = (
                "# Freeform Reviewer Negative Search Mode\n"
                "freeform_reviewer_negative_enabled=true\n"
                "Primary task: act like a peer reviewer and propose reviewer_negative_candidates only. "
                "Do not output evidence_map items in the discovery stage.\n\n"
            )
        else:
            targeted_negative_search_block = (
                "# Targeted Negative Search Mode\n"
                "targeted_negative_search_required=true\n"
                "Primary task: use the visible Targeted Negative Search Tasks, including any reviewer-discovered candidate, to decide what paper-side weakness to check. "
                "For each attempted task, either output a negative/coverage evidence item with copied raw_quote, specific source_locator, "
                "claim_id, negative_evidence_type, required_evidence_type, and targeted_negative_search_task_id, or output an "
                "unresolved question with status=not_assessable. For absence tasks, the raw_quote may be a table/list/experiment description "
                "that enumerates evaluated datasets, baselines, metrics, or components; the evidence statement must name the missing entity "
                "from the task or target claim. Do not treat not_found as negative evidence and do not add positive support in this mode.\n\n"
            )
    # Gated, default off: the manager only sets hard_negative_diagnosis_required when the
    # DRMAS_HARDNEG_DIAGNOSIS experiment is enabled. Keying off the flag (not the always-present
    # hard_negative_discovery_override policy_source) keeps default Critique behavior at baseline.
    hard_negative_diagnosis_required = bool(
        manager_payload.get("hard_negative_diagnosis_required")
    )
    hard_negative_diagnosis_block = ""
    if hard_negative_diagnosis_required and agent_id == "Critique Agent":
        hard_negative_diagnosis_block = (
            "# Hard-Negative Diagnosis Mode\n"
            "hard_negative_diagnosis_required=true\n"
            "Primary task: use model judgment to test the target real claims for true paper-side weaknesses. "
            "Do not start from negative-sounding words. Use quote-bank or existing evidence only after diagnosing a real baseline, ablation, evaluation, result-claim, method, or reproducibility problem.\n\n"
        )
    review_issue_discovery_block = ""
    if manager_payload.get("review_issue_discovery_required") and agent_id == "Critique Agent":
        review_issue_discovery_block = (
            "# Review Issue Discovery Mode\n"
            "review_issue_discovery_required=true\n"
            "Primary task: act like a peer reviewer and select up to 3 safe items from review_issue_candidate_selector_menu. "
            "Output selected_menu_items with copied candidate_menu_id values; the runner expands valid ids for later verification. "
            "When a selector menu is visible, do not leave both selected_menu_items and rejected_menu_items empty. "
            "Do not output verified evidence, claim status changes, or recovery patches. "
            "Only output full review_issue_candidates as a fallback when no menu item fits and the free-form issue has a real claim, concrete target, copied inventory anchor, and counterevidence terms. "
            "Reject generic, already-covered, retrieval/context, author-limitation, or stale menu items briefly.\n\n"
        )
    routing = (
        f"{mode_block}"
        f"{negative_mode_block}"
        f"{targeted_negative_search_block}"
        f"{hard_negative_diagnosis_block}"
        f"{review_issue_discovery_block}"
        "# Manager Focus\n"
        f"Action Type: {manager_payload.get('action_type', 'extract_claims')}\n"
        f"Effective Action Type: {manager_payload.get('effective_action_type') or manager_payload.get('action_type', 'extract_claims')}\n"
        f"Phase Enter Reason: {_clip_text(manager_payload.get('phase_enter_reason', ''), 220)}\n"
        f"Phase Hold Reason: {_clip_text(manager_payload.get('phase_hold_reason', ''), 220)}\n"
        f"Focus: {_clip_text(focus, 220)}\n"
        f"Rationale: {_clip_text(rationale, 320)}\n"
        f"Target Claim IDs: {manager_payload.get('target_claim_ids', [])}\n"
        f"Target Flaw IDs: {manager_payload.get('target_flaw_ids', [])}\n"
        f"Target Evidence IDs: {manager_payload.get('target_evidence_ids', [])}\n"
        f"Target Hypotheses: {manager_payload.get('target_hypotheses', [])}\n"
        f"Executed agent: {agent_id}\n\n"
        f"# Targeted Review Objects\n{target_brief}"
    )
    if agent_id == "Evidence Agent":
        if manager_payload.get("targeted_negative_search_required"):
            targeted_routing = (
                f"{mode_block}"
                f"{targeted_negative_search_block}"
                "# Manager Focus\n"
                f"Action Type: {manager_payload.get('action_type', 'verify_evidence')}\n"
                f"Focus: {_clip_text(focus, 180)}\n"
                f"Target Claim IDs: {manager_payload.get('target_claim_ids', [])}\n"
            )
            return _clip_text(f"{base}\n\n{targeted_routing}", MAX_TARGETED_NEGATIVE_WORKER_OBSERVATION_CHARS)
        compact_target_brief = "\n".join(
            [
                f"Target Claim IDs: {manager_payload.get('target_claim_ids', [])}",
                f"Target Flaw IDs: {manager_payload.get('target_flaw_ids', [])}",
                f"Target Evidence IDs: {manager_payload.get('target_evidence_ids', [])}",
                f"Target Hypotheses: {_clip_text(manager_payload.get('target_hypotheses', []), 220)}",
            ]
        )
        compact_routing = (
            f"{mode_block}"
            f"{negative_mode_block}"
            f"{targeted_negative_search_block}"
            "# Manager Focus\n"
            f"Action Type: {manager_payload.get('action_type', 'extract_claims')}\n"
            f"Effective Action Type: {manager_payload.get('effective_action_type') or manager_payload.get('action_type', 'extract_claims')}\n"
            f"Focus: {_clip_text(focus, 180)}\n"
            f"Rationale: {_clip_text(rationale, 180)}\n"
            f"Executed agent: {agent_id}\n\n"
            f"# Targeted Review Objects\n{compact_target_brief}"
        )
        # Evidence prompt routing de-dup (Codex audit 2026-06-20): the previous layout was
        # `compact_routing + base + routing`, which repeated the SAME routing / Manager-Focus
        # / target block twice (nudging MiMo to restate the task — the P0 fallback raw head
        # was exactly this restatement). Drop the redundant TRAILING `routing`; keep the front
        # compact_routing so the negative-mode/target block stays inside the clip window (the
        # long base/paper-excerpt would otherwise push a trailing routing out and _clip_text
        # truncates from the tail), with base after it.
        return _clip_text(f"{compact_routing}\n\n{base}", MAX_WORKER_OBSERVATION_CHARS)
    if negative_evidence_required:
        return _clip_text(f"{routing}\n\n{base}", MAX_WORKER_OBSERVATION_CHARS)
    return _clip_text(f"{base}\n\n{routing}", MAX_WORKER_OBSERVATION_CHARS)


def _is_negative_evidence_formation_turn(manager_payload: Dict[str, Any]) -> bool:
    policy_source = str(manager_payload.get("policy_source") or "").strip()
    policy_requires_negative = policy_source in {"negative_evidence_formation_override", "compact_negative_pass_override"}
    targeted_requires_negative = (
        policy_source == "targeted_negative_search_override"
        and bool(manager_payload.get("targeted_negative_search_required"))
    )
    return bool(
        manager_payload.get("negative_evidence_formation_required")
        or policy_requires_negative
        or targeted_requires_negative
    )


def _targeted_negative_trace_from_unresolved(
    manager_payload: Dict[str, Any],
    payload: Dict[str, Any],
    reason: str,
) -> tuple[Dict[str, Any], int]:
    tasks = [
        item for item in manager_payload.get("targeted_negative_search_active_tasks", []) or []
        if isinstance(item, dict)
    ]
    task = tasks[0] if tasks else {}
    unresolved = {}
    for item in payload.get("unresolved_questions", []) or []:
        if not isinstance(item, dict):
            continue
        status = str(item.get("status") or "").strip().lower()
        if status == "not_assessable":
            unresolved = item
            break
    target_id = str(
        unresolved.get("target_id")
        or unresolved.get("claim_id")
        or task.get("claim_id")
        or ((manager_payload.get("target_claim_ids") or [""])[0])
        or ""
    ).strip()
    task_id = str(
        unresolved.get("targeted_negative_search_task_id")
        or task.get("task_id")
        or ""
    ).strip()
    negative_type = str(
        unresolved.get("negative_evidence_type")
        or task.get("negative_type")
        or ""
    ).strip()
    required_type = str(
        unresolved.get("required_evidence_type")
        or task.get("required_evidence_type")
        or ""
    ).strip()
    question = str(unresolved.get("question") or "").strip()
    if not question:
        question = (
            f"Targeted negative search for {negative_type or 'paper-negative evidence'} "
            f"on claim {target_id or 'unknown'} did not yield a visible copied quote with locator."
        )
    trace = {
        "question": question,
        "status": "not_assessable",
        "target_type": str(unresolved.get("target_type") or "claim"),
        "target_id": target_id,
        "target_classification": "targeted_negative_search",
        "targeted_negative_search_task_id": task_id,
        "negative_evidence_type": negative_type,
        "required_evidence_type": required_type,
        "source": str(unresolved.get("source") or "targeted_negative_search_sidechannel"),
        "hygiene_status_reason": str(unresolved.get("hygiene_status_reason") or reason),
        "related_claim_ids": [target_id] if target_id else [],
    }
    return trace, 1 if target_id or task_id or negative_type else 0


def _annotate_targeted_negative_evidence_items(
    items: Sequence[Dict[str, Any]],
    manager_payload: Dict[str, Any],
) -> tuple[List[Dict[str, Any]], int]:
    """Attach active targeted-negative task context to model-emitted evidence.

    The model often copies a quote but forgets to echo the task id or the
    coverage missing-item fields.  This helper restores only deterministic
    routing context from the single active task; it never creates evidence,
    never changes raw_quote, and never marks anything verified.
    """

    tasks = [
        item for item in (manager_payload or {}).get("targeted_negative_search_active_tasks", []) or []
        if isinstance(item, dict)
    ]
    if not (manager_payload or {}).get("targeted_negative_search_required") or len(tasks) != 1:
        return [dict(item) for item in items], 0
    task = tasks[0]
    task_id = str(task.get("task_id") or "").strip()
    if not task_id:
        return [dict(item) for item in items], 0
    changed = 0
    annotated: List[Dict[str, Any]] = []
    for raw_item in items:
        item = dict(raw_item)
        before = dict(item)
        if not str(item.get("targeted_negative_search_task_id") or "").strip():
            item["targeted_negative_search_task_id"] = task_id
        if not str(item.get("claim_id") or "").strip() and str(task.get("claim_id") or "").strip():
            item["claim_id"] = str(task.get("claim_id") or "").strip()
        if not str(item.get("negative_evidence_type") or item.get("negative_type") or "").strip() and str(task.get("negative_type") or "").strip():
            item["negative_evidence_type"] = str(task.get("negative_type") or "").strip()
        if not str(item.get("required_evidence_type") or "").strip() and str(task.get("required_evidence_type") or "").strip():
            item["required_evidence_type"] = str(task.get("required_evidence_type") or "").strip()
        if (
            not item.get("coverage_missing_items")
            and not item.get("missing_or_weak_items")
            and task.get("missing_or_weak_items")
        ):
            item["coverage_missing_items"] = list(task.get("missing_or_weak_items") or [])[:6]
        if (
            not str(item.get("reviewer_negative_candidate_id") or "").strip()
            and str(task.get("reviewer_negative_candidate_id") or "").strip()
        ):
            item["reviewer_negative_candidate_id"] = str(task.get("reviewer_negative_candidate_id") or "").strip()
        if item != before:
            changed += 1
        annotated.append(item)
    return annotated, changed


_TARGETED_NEGATIVE_QUOTE_PROPOSAL_SOURCES = {
    "freeform_reviewer_negative_candidate",
    "quote_bank_guided_review_negative_search",
}


def _runner_slug(prefix: str, seed: str, fallback_index: int) -> str:
    slug = re.sub(r"[^a-zA-Z0-9_-]+", "-", str(seed or "")).strip("-").lower()
    if not slug:
        slug = f"item-{fallback_index}"
    return f"{prefix}-{slug[:96]}"


def _targeted_negative_candidate_quote_proposals(
    items: Sequence[Dict[str, Any]],
    manager_payload: Dict[str, Any],
) -> tuple[List[Dict[str, Any]], int]:
    """Promote a single active candidate quote into a verifier-only proposal.

    Targeted quote-verification turns sometimes receive a concrete copied
    candidate quote from the manager, but the Evidence Agent returns an empty
    JSON payload.  This bridge does not mark the quote verified; it only puts
    the copied candidate into the normal evidence verifier so the existing
    grounding, semantic, and review-negative relation gates decide whether it
    counts.
    """

    manager_payload = manager_payload or {}
    policy_source = str(manager_payload.get("policy_source") or "").strip()
    targeted_negative_turn = bool(
        manager_payload.get("targeted_negative_search_required")
        or policy_source == "targeted_negative_search_override"
    )
    if not targeted_negative_turn:
        return [dict(item) for item in items], 0
    tasks = [
        task for task in manager_payload.get("targeted_negative_search_active_tasks", []) or []
        if isinstance(task, dict)
    ]
    if len(tasks) != 1:
        return [dict(item) for item in items], 0
    task = tasks[0]
    source = str(task.get("source") or "").strip()
    if source not in _TARGETED_NEGATIVE_QUOTE_PROPOSAL_SOURCES:
        return [dict(item) for item in items], 0
    quote = str(task.get("candidate_raw_quote") or "").strip()
    claim_id = str(task.get("claim_id") or "").strip()
    if not quote or not claim_id:
        return [dict(item) for item in items], 0
    quote_mode = str(task.get("quote_grounding_mode") or "").strip()
    if quote_mode == "absence_or_requirement_gap":
        return [dict(item) for item in items], 0

    task_id = str(task.get("task_id") or "").strip()
    quote_id = str(task.get("quote_id") or "").strip()
    quote_key = _runner_quote_bank_dedupe_key(quote)
    for item in items or []:
        if not isinstance(item, dict):
            continue
        if task_id and str(item.get("targeted_negative_search_task_id") or "").strip() == task_id:
            return [dict(entry) for entry in items], 0
        if quote_id and str(item.get("quote_id") or "").strip() == quote_id:
            return [dict(entry) for entry in items], 0
        raw_key = _runner_quote_bank_dedupe_key(str(item.get("raw_quote") or item.get("evidence") or ""))
        if raw_key and raw_key == quote_key:
            return [dict(entry) for entry in items], 0

    negative_type = str(task.get("negative_type") or "").strip() or _classify_negative_evidence_type(quote)
    required_type = str(task.get("required_evidence_type") or "").strip()
    safe_seed = task_id or quote_id or f"{claim_id}-{negative_type}"
    proposal = {
        "evidence_id": _runner_slug("evidence-targeted-candidate-quote", safe_seed, len(items) + 1),
        "claim_id": claim_id,
        "evidence": (
            "Candidate copied paper quote for review-negative verification: "
            f"{_compact_runner_text(quote, max_length=220)}"
        ),
        "source": "targeted-negative-candidate-quote",
        "source_locator": str(
            task.get("target_locator_hint")
            or task.get("source_locator")
            or "Candidate-Relevant Paper Windows"
        ),
        "raw_quote": quote,
        "stance": "missing",
        "strength": "missing",
        "negative_evidence_type": negative_type,
        "negative_evidence_actionability": (
            "actionable_candidate"
            if negative_type in _ACTIONABLE_NEGATIVE_EVIDENCE_TYPES
            else "assessment_limitation"
        ),
        "targeted_negative_search_task_id": task_id,
        "reviewer_negative_candidate_id": str(task.get("reviewer_negative_candidate_id") or "").strip(),
        "reviewer_negative_candidate": str(task.get("reviewer_negative_candidate") or task.get("search_question") or "").strip(),
        "quote_grounding_mode": quote_mode or "quote_groundable_internal_negative",
        "coverage_missing_items": list(task.get("missing_or_weak_items") or [])[:6],
        "coverage_observed_items": list(task.get("coverage_observed_items") or [])[:6],
        "targeted_negative_candidate_quote_proposal": True,
        "targeted_negative_candidate_quote_proposal_source": source,
        "runtime_evidence_verification_required": True,
        "binding_status": "bound_real_claim",
        "binding_confidence": 0.66,
        "binding_rationale": (
            "Manager supplied a copied candidate quote for targeted reviewer-negative verification; "
            "state merge must verify grounding and review-negative relation before it counts."
        ),
    }
    if quote_id:
        proposal["quote_id"] = quote_id
    if required_type:
        proposal["required_evidence_type"] = required_type
    return [dict(item) for item in items] + [proposal], 1


def _enforce_negative_evidence_formation_payload(
    worker_id: str,
    worker_payload: Dict[str, Any],
    manager_payload: Dict[str, Any],
    state: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    if worker_id != "Evidence Agent" or not _is_negative_evidence_formation_turn(manager_payload):
        return worker_payload
    payload = dict(worker_payload or {})
    sidechannel_trace = payload.get("targeted_negative_search_not_assessable")
    sidechannel_count = payload.get("targeted_negative_search_not_assessable_count")
    policy_source = str((manager_payload or {}).get("policy_source") or "").strip()
    targeted_negative_turn = bool(
        (manager_payload or {}).get("targeted_negative_search_required")
        or policy_source == "targeted_negative_search_override"
    )
    evidence_items = [item for item in payload.get("evidence_map", []) or [] if isinstance(item, dict)]
    evidence_items, task_context_filled_count = _annotate_targeted_negative_evidence_items(
        evidence_items,
        manager_payload or {},
    )
    if task_context_filled_count:
        payload["targeted_negative_search_task_context_filled_count"] = task_context_filled_count
    evidence_items, proposal_count = _targeted_negative_candidate_quote_proposals(
        evidence_items,
        manager_payload or {},
    )
    if proposal_count:
        payload["targeted_negative_candidate_quote_proposal_count"] = proposal_count
    kept = []
    dropped = []
    for item in evidence_items:
        stance = str(item.get("stance") or "").strip().lower()
        strength = str(item.get("strength") or "").strip().lower()
        if stance in _NEGATIVE_RECOVERY_STANCES or strength == "missing":
            kept.append(item)
        else:
            dropped.append(str(item.get("evidence_id") or item.get("evidence") or "positive-support"))

    salvage_items: List[Dict[str, Any]] = []
    grounded_quote_ids = _negative_quote_bank_grounded_quote_ids(kept, state)
    existing_quote_ids = set(grounded_quote_ids)
    for item in (state or {}).get("evidence_map", []) or []:
        if not isinstance(item, dict):
            continue
        quote_id = str(item.get("quote_id") or "").strip()
        if quote_id and _negative_evidence_record_type(item) not in {"generic_gap", "neutral_control_context"}:
            existing_quote_ids.add(quote_id)
    strict_reviewer_negative_turn = policy_source in {"hard_negative_discovery_override", "targeted_negative_search_override"}
    needed_salvage = 0
    if not strict_reviewer_negative_turn:
        if not grounded_quote_ids:
            needed_salvage = 1
        kept_actionable_grounded = [
            item for item in kept
            if _negative_evidence_record_is_actionable(item)
            and str(item.get("quote_id") or "").strip() in grounded_quote_ids
        ]
        if len(kept_actionable_grounded) < 1:
            needed_salvage = max(needed_salvage, 1)
        if manager_payload.get("negative_evidence_formation_required"):
            needed_salvage = max(needed_salvage, 2)
    elif not kept:
        payload["negative_quote_bank_salvage_blocked"] = True
        payload["negative_quote_bank_salvage_block_reason"] = "strict_reviewer_negative_turn_requires_model_emitted_quote"
    if needed_salvage:
        for entry in _select_negative_quote_bank_entries(
            state,
            manager_payload,
            max_entries=4,
            exclude_quote_ids=existing_quote_ids,
        ):
            salvage = _negative_quote_bank_salvage_payload(
                state,
                manager_payload,
                len(evidence_items) + len(salvage_items),
                entry_override=entry,
            )
            if not salvage:
                continue
            quote_id = str(salvage.get("quote_id") or "").strip()
            if quote_id and quote_id in existing_quote_ids:
                continue
            kept.append(salvage)
            salvage_items.append(salvage)
            if quote_id:
                existing_quote_ids.add(quote_id)
            flaw_updates = _negative_salvage_target_flaw_updates(
                manager_payload,
                str(salvage.get("evidence_id") or ""),
                str(salvage.get("claim_id") or ""),
                quote_id,
                str(salvage.get("negative_evidence_type") or "generic_gap"),
                _claim_text_lookup(state).get(str(salvage.get("claim_id") or ""), ""),
                str(salvage.get("raw_quote") or ""),
                str(salvage.get("source_locator") or ""),
            )
            if flaw_updates:
                payload["flaw_candidates"] = list(payload.get("flaw_candidates") or []) + flaw_updates
            if len(salvage_items) >= needed_salvage:
                break
    if salvage_items:
        payload["negative_quote_bank_salvage_used"] = True
        payload["negative_quote_bank_salvage_quote_id"] = salvage_items[0].get("quote_id", "")
        payload["negative_quote_bank_salvage_quote_ids"] = [item.get("quote_id", "") for item in salvage_items]

    payload["evidence_map"] = kept
    if dropped:
        payload["negative_evidence_formation_filtered_positive_count"] = len(dropped)
        notes = list(payload.get("unresolved_questions") or [])
        if salvage_items:
            # P0-4: keep this note paper-side / reviewer-neutral so it cannot
            # leak system-process language ("filtered", "salvage",
            # "hard-negative", etc.) into the user-facing report.
            notes.append(
                "The concern remains evidence-limited; treat it as tentative pending verified paper-negative evidence."
            )
        else:
            notes.append(
                "Available grounded evidence currently supports only a cautious concern; keep the item open until verified paper-negative evidence is found."
            )
        payload["unresolved_questions"] = notes[:8]
    if targeted_negative_turn and not kept:
        if not isinstance(sidechannel_trace, dict) or not sidechannel_trace:
            sidechannel_trace, sidechannel_count = _targeted_negative_trace_from_unresolved(
                manager_payload,
                payload,
                "no_visible_quote_grounded_negative_evidence",
            )
        payload["unresolved_questions"] = []
    if not kept and not payload.get("unresolved_questions") and not targeted_negative_turn:
        payload["unresolved_questions"] = [
            "Verified paper-negative evidence has not yet been located for the target concern."
        ]
    normalized = normalize_review_update_payload(payload)
    if proposal_count:
        normalized["targeted_negative_candidate_quote_proposal_count"] = proposal_count
    if isinstance(sidechannel_trace, dict) and sidechannel_trace:
        normalized["targeted_negative_search_not_assessable"] = sidechannel_trace
        normalized["targeted_negative_search_not_assessable_count"] = int(sidechannel_count or 1)
    return normalized


def _support_quote_bank_from_state(state: Dict[str, Any]) -> List[Dict[str, Any]]:
    meta = state.get("_latest_evidence_context_meta") if isinstance(state, dict) else {}
    bank = []
    if isinstance(meta, dict):
        bank = meta.get("evidence_quote_bank") or []
    if not bank and isinstance(state, dict):
        bank = state.get("evidence_quote_bank") or []
    return [item for item in bank if isinstance(item, dict)]


def _real_claims_by_id(state: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    claims = {}
    for item in (state or {}).get("claims", []) or []:
        if not isinstance(item, dict):
            continue
        claim_id = str(item.get("claim_id") or "").strip()
        if not claim_id or claim_id.startswith(("claim-context", "claim-fallback", "claim-recovery")):
            continue
        claims[claim_id] = item
    return claims


def _claim_has_any_support(state: Dict[str, Any], claim_id: str) -> bool:
    for item in (state or {}).get("evidence_map", []) or []:
        if not isinstance(item, dict):
            continue
        if str(item.get("claim_id") or "") != claim_id:
            continue
        if str(item.get("stance") or "").strip().lower() in {"supports", "partially_supports"}:
            return True
    return False


def _word_overlap_score(left: str, right: str) -> int:
    left_terms = {
        term
        for term in re.findall(r"[A-Za-z][A-Za-z0-9_-]{2,}", str(left or "").lower())
        if term not in {"the", "and", "for", "with", "from", "that", "this", "paper", "method"}
    }
    right_terms = {
        term
        for term in re.findall(r"[A-Za-z][A-Za-z0-9_-]{2,}", str(right or "").lower())
        if term not in {"the", "and", "for", "with", "from", "that", "this", "paper", "method"}
    }
    return len(left_terms & right_terms)


def _quote_bank_source_to_support_bucket(source: str) -> str:
    source = str(source or "").strip().lower()
    if source in {"results", "result", "table_or_figure", "ablation", "comparison", "claim_match_result"}:
        return "result_or_experiment"
    if source in {"method", "theory_or_proof", "claim_match_method"}:
        return "method_or_approach"
    if source == "abstract":
        return "abstract"
    if source in {"conclusion", "discussion"}:
        return "conclusion_or_discussion"
    return "other_or_unspecified"


_FIRST_SUPPORT_TITLE_RE = re.compile(r"^\s*\\title\s*\{", re.IGNORECASE)
_FIRST_SUPPORT_NEGATIVE_RE = re.compile(
    r"\b(underperform|worse|fail(?:s|ed)?|failure|limitation|limitations|"
    r"missing|lack(?:s|ing)?|insufficient|without|not evaluated|no ablation|"
    r"no baseline|decrease(?:s|d)?|reduction|weakness|threats? to validity)\b",
    re.IGNORECASE,
)
_FIRST_SUPPORT_METHOD_RE = re.compile(
    r"\b(method|methodology|algorithm|framework|module|optimization|objective|loss|"
    r"entropy|training|adaptation|approach|architecture)\b",
    re.IGNORECASE,
)
_FIRST_SUPPORT_RESULT_RE = re.compile(
    r"\b(table|figure|fig\.|experiment|evaluation|result|performance|benchmark|"
    r"baseline|ablation|outperform|improv(?:e|es|ed|ement)|accuracy|f1|auc)\b",
    re.IGNORECASE,
)


def _first_support_source_bucket(quote: Dict[str, Any]) -> str:
    source = str(quote.get("source_bucket") or "").strip().lower()
    if source != "claim_match":
        return source
    text = " ".join(
        str(quote.get(key) or "")
        for key in ("raw_quote", "source_locator", "support_role_hint")
    )
    if _FIRST_SUPPORT_RESULT_RE.search(text):
        return "claim_match_result"
    if _FIRST_SUPPORT_METHOD_RE.search(text):
        return "claim_match_method"
    return source


def _first_support_quote_is_negative(quote: Dict[str, Any]) -> bool:
    text = " ".join(
        str(quote.get(key) or "")
        for key in ("raw_quote", "source_locator", "support_role_hint")
    )
    source = str(quote.get("source_bucket") or "").strip().lower()
    if source == "negative_or_gap":
        return True
    return bool(_FIRST_SUPPORT_NEGATIVE_RE.search(text))


def _first_support_quote_is_title_or_abstract_stub(quote: Dict[str, Any]) -> bool:
    raw_quote = str(quote.get("raw_quote") or "").strip()
    locator = str(quote.get("source_locator") or "").strip().lower()
    source = str(quote.get("source_bucket") or "").strip().lower()
    if _FIRST_SUPPORT_TITLE_RE.search(raw_quote):
        return True
    if source == "abstract" and len(raw_quote) < 140:
        return True
    if locator.startswith("abstract") and _FIRST_SUPPORT_TITLE_RE.search(raw_quote):
        return True
    return False


def _first_support_claim_priority(claim: Dict[str, Any]) -> int:
    text = " ".join(
        str(claim.get(key) or "")
        for key in ("claim_type", "claim_kind", "claim", "evidence_need")
    ).lower()
    if any(term in text for term in ("empirical", "result", "ablation", "experiment", "metric", "performance")):
        return 4
    if any(term in text for term in ("method", "algorithm", "technical", "approach", "formula")):
        return 3
    if any(term in text for term in ("contribution", "novel", "significance")):
        return 2
    if any(term in text for term in ("limitation", "boundary", "uncertain")):
        return 0
    return 1


def _first_support_evidence_text(quote_text: str) -> str:
    snippet = re.sub(r"\s+", " ", str(quote_text or "")).strip()
    if len(snippet) > 220:
        snippet = snippet[:217].rstrip() + "..."
    return f"Copied paper quote provides initial claim support: {snippet}"


def _small_model_quote_bank_evidence_text(quote_text: str, locator: str = "") -> str:
    snippet = re.sub(r"\s+", " ", str(quote_text or "")).strip()
    if len(snippet) > 220:
        snippet = snippet[:217].rstrip() + "..."
    locator = str(locator or "").strip()
    if re.search(r"\bTable\s*\d+", locator, re.IGNORECASE):
        return f"{locator} reports: {snippet}"
    if re.search(r"\b(?:Figure|Fig\.)\s*\d+", locator, re.IGNORECASE):
        return f"{locator} shows: {snippet}"
    return f"The copied paper quote states: {snippet}"


def _small_model_quote_bank_support_item(
    state: Dict[str, Any],
    manager_payload: Dict[str, Any],
    claim_id: str,
    quote: Dict[str, Any],
    evidence_index: int,
    *,
    reason: str,
) -> Dict[str, Any]:
    quote_text = str(quote.get("raw_quote") or "").strip()
    source = _first_support_source_bucket(quote)
    support_bucket = _quote_bank_source_to_support_bucket(source)
    source_locator = str(quote.get("source_locator") or "")
    locator_specific = bool(re.search(r"\b(?:Table|Figure|Fig\.|Section|Sec\.)\s*\d+", source_locator, re.IGNORECASE))
    concrete_quote = bool(_QUOTE_CONCRETE_ANCHOR_RE.search(quote_text))
    deep_source = source in {"table_or_figure", "results", "claim_match_result", "ablation", "comparison"}
    strength = "strong" if deep_source and (locator_specific or concrete_quote) else "medium"
    binding_confidence = 0.62 if strength == "strong" else 0.48
    return {
        "evidence_id": f"evidence-small-model-quote-bank-{evidence_index}",
        "claim_id": claim_id,
        "evidence": _small_model_quote_bank_evidence_text(quote_text, source_locator),
        "source": source_locator or quote.get("source_bucket") or "paper quote bank",
        "source_locator": source_locator,
        "raw_quote": quote_text,
        "quote_id": quote.get("quote_id") or "",
        "source_span_start": int(quote.get("source_span_start", -1) or -1),
        "source_span_end": int(quote.get("source_span_end", -1) or -1),
        "strength": strength,
        "stance": "partially_supports",
        "binding_status": "bound_real_claim",
        "binding_confidence": binding_confidence,
        "binding_rationale": "Deterministic small-model augmentation binds a copied quote-bank span to the targeted real claim.",
        "grounded_judge_label": "self_claimed_by_agent",
        "grounded_judge_reason": "Quote copied from Evidence Quote Bank; verifier assigns final grounding and semantic labels.",
        "support_source_bucket": support_bucket,
        "support_quality_reason": (
            "Small-model quote-bank augmentation; final strength depends on verifier semantic alignment."
        ),
        "small_model_quote_bank_augmentation": True,
        "small_model_quote_bank_augmentation_reason": reason,
        "model_adapter_quote_bank_augmentation": True,
    }


def _apply_small_model_quote_bank_support_augmentation(
    worker_id: str,
    worker_payload: Dict[str, Any],
    state: Dict[str, Any],
    manager_payload: Dict[str, Any],
    trace_worker: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Add conservative quote-bank evidence when small models under-produce.

    MiMo-like models often understand the task but emit too few concrete
    evidence items or return empty content on long Evidence prompts.  This path
    does not invent text: it only copies program-extracted quote-bank spans,
    binds them to existing real paper claims, and lets the state verifier decide
    final grounding/semantic admission.
    """
    if worker_id != "Evidence Agent" or not isinstance(worker_payload, dict):
        return worker_payload
    mode = _normalize_model_adapter_mode(manager_payload.get("model_adapter_mode", "auto"))
    if not _model_adapter_quote_first_enabled(mode):
        return worker_payload
    if _is_negative_evidence_formation_turn(manager_payload):
        return worker_payload
    action_type = str(manager_payload.get("effective_action_type") or manager_payload.get("action_type") or "").strip()
    if action_type not in {"verify_evidence", "request_evidence_recheck", "challenge_previous_hypothesis"}:
        return worker_payload

    claims_by_id = _real_claims_by_id(state)
    if not claims_by_id:
        return worker_payload
    evidence_items = [item for item in worker_payload.get("evidence_map", []) or [] if isinstance(item, dict)]
    support_evidence_items = [
        item for item in evidence_items
        if str(item.get("stance") or "").strip().lower() in {"supports", "partially_supports"}
        and str(item.get("raw_quote") or item.get("quote_id") or "").strip()
    ]
    target_claim_ids = [
        str(item).strip()
        for item in (manager_payload.get("target_claim_ids") or [])
        if str(item).strip() in claims_by_id
    ] or list(claims_by_id.keys())[:4]
    if not target_claim_ids:
        return worker_payload

    quote_bank = [
        item for item in _support_quote_bank_from_state(state)
        if not _first_support_quote_is_negative(item)
        and str(item.get("raw_quote") or "").strip()
        and not _first_support_quote_is_title_or_abstract_stub(item)
    ]
    if not quote_bank:
        return worker_payload

    def support_group_key(item: Dict[str, Any]) -> str:
        quote_id = str(item.get("quote_id") or "").strip()
        if quote_id:
            return f"quote:{quote_id}"
        quote_text = re.sub(r"\s+", " ", str(item.get("raw_quote") or "")).strip().lower()
        if quote_text:
            return f"text:{quote_text[:160]}"
        locator = re.sub(r"\s+", " ", str(item.get("source_locator") or item.get("source") or "")).strip().lower()
        return f"locator:{locator[:120]}"

    existing_support_groups_by_claim: Dict[str, set[str]] = {}
    for item in list((state or {}).get("evidence_map", []) or []) + evidence_items:
        if not isinstance(item, dict):
            continue
        if str(item.get("stance") or "").strip().lower() not in {"supports", "partially_supports"}:
            continue
        claim_id = str(item.get("claim_id") or "").strip()
        if claim_id not in claims_by_id:
            continue
        group_key = support_group_key(item)
        if not group_key:
            continue
        existing_support_groups_by_claim.setdefault(claim_id, set()).add(group_key)

    existing_support_claims = {
        claim_id for claim_id, groups in existing_support_groups_by_claim.items() if groups
    }
    payload_support_claims = {
        str(item.get("claim_id") or "")
        for item in evidence_items
        if str(item.get("stance") or "").strip().lower() in {"supports", "partially_supports"}
    }
    used_pairs = {
        (str(item.get("claim_id") or ""), str(item.get("quote_id") or ""), re.sub(r"\s+", " ", str(item.get("raw_quote") or "")).strip().lower())
        for item in list((state or {}).get("evidence_map", []) or []) + evidence_items
        if isinstance(item, dict)
    }
    used_quote_ids = {quote_id for _, quote_id, _ in used_pairs if quote_id}

    def rank_pair(pair: tuple[str, Dict[str, Any]]) -> tuple[int, int, int, int, int, int, int, int, int, int, int]:
        claim_id, quote = pair
        claim = claims_by_id.get(claim_id, {})
        claim_text = " ".join(str(claim.get(key) or "") for key in ("claim", "evidence_need", "claim_type", "coverage_tags"))
        claim_lower = claim_text.lower()
        quote_text = " ".join(str(quote.get(key) or "") for key in ("raw_quote", "source_locator", "source_bucket", "support_role_hint"))
        source = _first_support_source_bucket(quote)
        source_priority = {
            "table_or_figure": 8,
            "results": 7,
            "claim_match_result": 7,
            "ablation": 6,
            "comparison": 5,
            "method": 4,
            "claim_match_method": 4,
            "theory_or_proof": 3,
            "claim_match": 2,
            "abstract": 0,
        }.get(source, 1)
        overlap = int(quote.get("claim_overlap_score") or 0) + _word_overlap_score(claim_text, quote_text)
        locator = str(quote.get("source_locator") or "")
        locator_specific = 1 if re.search(r"\b(?:Table|Figure|Fig\.|Section|Sec\.)\s*\d+", locator, re.IGNORECASE) else 0
        existing_group_count = len(existing_support_groups_by_claim.get(claim_id, set()))
        needs_second_independent = 1 if existing_group_count == 1 else 0
        uncovered_claim = 1 if existing_group_count == 0 and claim_id not in payload_support_claims else 0
        under_independent = 1 if existing_group_count < 2 else 0
        unused_quote = 1 if str(quote.get("quote_id") or "") not in used_quote_ids else 0
        concrete = 1 if _QUOTE_CONCRETE_ANCHOR_RE.search(str(quote.get("raw_quote") or "")) else 0
        quote_length = min(len(str(quote.get("raw_quote") or "")), 260)
        claim_priority = _first_support_claim_priority(claim)
        claim_source_match = 0
        if source in {"table_or_figure", "results", "claim_match_result", "ablation", "comparison"} and any(
            term in claim_lower for term in ("empirical", "experiment", "result", "performance", "metric", "benchmark", "baseline", "outperform")
        ):
            claim_source_match = 1
        elif source in {"method", "claim_match_method", "theory_or_proof"} and any(
            term in claim_lower for term in ("method", "algorithm", "approach", "objective", "architecture", "training", "model")
        ):
            claim_source_match = 1
        return (
            under_independent,
            needs_second_independent,
            uncovered_claim,
            unused_quote,
            claim_source_match,
            source_priority,
            claim_priority,
            locator_specific,
            concrete,
            overlap,
            quote_length,
        )

    pairs: List[tuple[str, Dict[str, Any]]] = []
    for claim_id in target_claim_ids:
        for quote in quote_bank:
            quote_key = re.sub(r"\s+", " ", str(quote.get("raw_quote") or "")).strip().lower()
            pair_key = (claim_id, str(quote.get("quote_id") or ""), quote_key)
            if pair_key in used_pairs:
                continue
            pairs.append((claim_id, quote))
    if not pairs:
        return worker_payload

    target_min = 2 if action_type in {"verify_evidence", "request_evidence_recheck"} else 1
    max_additions = max(0, target_min - len(support_evidence_items))
    independence_need = sum(
        1
        for claim_id in target_claim_ids
        if _first_support_claim_priority(claims_by_id.get(claim_id, {})) >= 2
        and len(existing_support_groups_by_claim.get(claim_id, set())) == 1
    )
    uncovered_need = sum(
        1
        for claim_id in target_claim_ids
        if _first_support_claim_priority(claims_by_id.get(claim_id, {})) >= 2
        and len(existing_support_groups_by_claim.get(claim_id, set())) == 0
        and claim_id not in payload_support_claims
    )
    if max_additions <= 0 and independence_need <= 0 and uncovered_need <= 0:
        return worker_payload
    max_additions = max(max_additions, min(independence_need, 2), 1 if uncovered_need else 0)
    max_additions = min(max_additions, 3)

    selected: List[tuple[str, Dict[str, Any]]] = []
    selected_groups_by_claim: Dict[str, set[str]] = {}
    selected_quote_ids: set[str] = set()
    for claim_id, quote in sorted(pairs, key=rank_pair, reverse=True):
        quote_id = str(quote.get("quote_id") or "")
        if quote_id:
            candidate_group = f"quote:{quote_id}"
        else:
            quote_group_text = re.sub(r"\s+", " ", str(quote.get("raw_quote") or "")).strip().lower()
            candidate_group = f"text:{quote_group_text[:160]}"
        current_groups = set(existing_support_groups_by_claim.get(claim_id, set()))
        current_groups.update(selected_groups_by_claim.get(claim_id, set()))
        if candidate_group in current_groups:
            continue
        if len(current_groups) >= 2:
            continue
        if quote_id and quote_id in selected_quote_ids:
            continue
        selected.append((claim_id, quote))
        selected_groups_by_claim.setdefault(claim_id, set()).add(candidate_group)
        if quote_id:
            selected_quote_ids.add(quote_id)
        if len(selected) >= max_additions:
            break
    if not selected:
        return worker_payload

    updated = dict(worker_payload)
    updated_items = list(evidence_items)
    base_index = len((state or {}).get("evidence_map", []) or []) + len(updated_items) + 1
    additions = [
        _small_model_quote_bank_support_item(
            state,
            manager_payload,
            claim_id,
            quote,
            base_index + idx,
            reason="small_model_underproduced_evidence",
        )
        for idx, (claim_id, quote) in enumerate(selected)
    ]
    updated_items.extend(additions)
    updated["evidence_map"] = updated_items
    updated["small_model_quote_bank_augmentation_count"] = int(updated.get("small_model_quote_bank_augmentation_count") or 0) + len(additions)
    manager_payload["small_model_quote_bank_augmentation_count"] = int(manager_payload.get("small_model_quote_bank_augmentation_count") or 0) + len(additions)
    if trace_worker is not None:
        trace_worker["small_model_quote_bank_augmentation_count"] = len(additions)
        trace_worker["small_model_quote_bank_augmentation_examples"] = [
            {
                "claim_id": item["claim_id"],
                "quote_id": item.get("quote_id", ""),
                "strength": item.get("strength", ""),
            }
            for item in additions[:3]
        ]
    normalized = normalize_review_update_payload(updated, required_fields=["evidence_map"])
    normalized["small_model_quote_bank_augmentation_count"] = int(updated.get("small_model_quote_bank_augmentation_count") or len(additions))
    return normalized


_EVIDENCE_DESCRIPTION_ONLY_RE = re.compile(
    r"^\s*(?:"
    r"an?\s+(?:direct\s+)?(?:quantitative\s+)?(?:comparison|description|analysis|evaluation|ablation|result|evidence|statement|discussion)\b|"
    r"(?:direct|quantitative|empirical|methodological)\s+(?:comparison|evidence|support|description)\b|"
    r"evidence\s+(?:of|for|that)\b|"
    r"the\s+paper\s+(?:provides|presents|includes|contains|describes|reports)\s+(?:evidence|a\s+description|an\s+analysis)\b"
    r")",
    re.IGNORECASE,
)
_QUOTE_CONCRETE_ANCHOR_RE = re.compile(
    r"\b(?:Table|Figure|Fig\.|Section|Sec\.)\s*\d+|"
    r"\b\d+(?:\.\d+)?\s*(?:%|points?|HOTA|MOTA|IDF1|AP|F1|accuracy|AUC|BLEU|ROUGE|mAP)?\b|"
    r"\b(?:outperform|improv|ablation|baseline|dataset|benchmark|validation|test set|result)\w*\b",
    re.IGNORECASE,
)
_EVIDENCE_CONCRETE_ANCHOR_RE = re.compile(
    r"\b(?:Table|Figure|Fig\.|Section|Sec\.)\s*\d+|"
    r"\b\d+(?:\.\d+)?\s*(?:%|points?|HOTA|MOTA|IDF1|AP|F1|accuracy|AUC|BLEU|ROUGE|mAP)?\b",
    re.IGNORECASE,
)


def _normalize_model_adapter_mode(mode: Any) -> str:
    normalized = str(mode or "auto").strip().lower().replace("-", "_")
    aliases = {
        "small": "small_model",
        "smallmodel": "small_model",
        "small_model": "small_model",
        "large": "large_model",
        "largemodel": "large_model",
        "large_model": "large_model",
        "disabled": "off",
        "false": "off",
        "none": "off",
        "0": "off",
        "true": "small_model",
        "1": "small_model",
        "auto": "auto",
        "off": "off",
    }
    return aliases.get(normalized, "auto")


def _model_adapter_quote_first_enabled(mode: Any) -> bool:
    normalized = _normalize_model_adapter_mode(mode)
    return normalized in {"auto", "small_model"}


def _quote_first_statement_from_item(item: Dict[str, Any]) -> str:
    quote = re.sub(r"\s+", " ", str(item.get("raw_quote") or "")).strip()
    if not quote:
        return ""
    locator = str(item.get("source_locator") or item.get("source") or "").strip()
    prefix = "The copied quote"
    if re.search(r"\bTable\s*\d+", locator, re.IGNORECASE):
        prefix = f"{locator} reports"
    elif re.search(r"\b(?:Figure|Fig\.)\s*\d+", locator, re.IGNORECASE):
        prefix = f"{locator} shows"
    elif re.search(r"\bablation\b", " ".join(str(item.get(k) or "") for k in ("support_source_bucket", "source", "source_locator", "raw_quote")), re.IGNORECASE):
        prefix = "The ablation quote states"
    elif re.search(r"\bmethod|approach|algorithm|framework\b", str(item.get("support_source_bucket") or item.get("source") or ""), re.IGNORECASE):
        prefix = "The method quote states"
    snippet = quote
    if len(snippet) > 190:
        snippet = snippet[:187].rstrip() + "..."
    # Avoid doubling punctuation after truncated LaTeX fragments.
    return f"{prefix}: {snippet}"


def _apply_quote_first_evidence_statement_adapter(
    worker_id: str,
    worker_payload: Dict[str, Any],
    manager_payload: Dict[str, Any],
    trace_worker: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Convert description-only evidence statements into quote-first statements.

    Smaller instruction-following models often output what evidence should be
    ("a direct quantitative comparison") rather than what the paper quote says.
    This adapter does not create new evidence or increase strength; it only
    makes the evidence statement faithful to an already copied quote so the
    verifier/reward pipeline can judge the item instead of a paraphrased request.
    """
    if worker_id != "Evidence Agent" or not isinstance(worker_payload, dict):
        return worker_payload
    mode = _normalize_model_adapter_mode(manager_payload.get("model_adapter_mode", "auto"))
    if not _model_adapter_quote_first_enabled(mode):
        if trace_worker is not None:
            trace_worker["model_adapter_mode"] = mode
            trace_worker["model_adapter_quote_first_enabled"] = False
        return worker_payload
    evidence_items = [item for item in worker_payload.get("evidence_map", []) or [] if isinstance(item, dict)]
    if not evidence_items:
        return worker_payload
    adapted = 0
    downgraded = 0
    examples: List[Dict[str, str]] = []
    for item in evidence_items:
        evidence_text = str(item.get("evidence") or "").strip()
        raw_quote = str(item.get("raw_quote") or "").strip()
        if not evidence_text or not raw_quote:
            continue
        description_only = bool(_EVIDENCE_DESCRIPTION_ONLY_RE.search(evidence_text))
        lacks_concrete_anchor = not bool(_EVIDENCE_CONCRETE_ANCHOR_RE.search(evidence_text))
        quote_has_anchor = bool(_QUOTE_CONCRETE_ANCHOR_RE.search(raw_quote))
        # Trigger on description-only statements, especially when the quote is
        # more concrete than the evidence field.  Leave already concrete
        # statements with table IDs/numbers untouched.
        if not description_only and not (lacks_concrete_anchor and quote_has_anchor and len(evidence_text.split()) <= 18):
            continue
        replacement = _quote_first_statement_from_item(item)
        if not replacement:
            continue
        item["agent_evidence_statement"] = evidence_text
        item["evidence"] = replacement
        item["model_adapter_quote_first_rewrite"] = True
        item["model_adapter_reason"] = "description_only_evidence_statement_rewritten_from_raw_quote"
        adapted += 1
        if str(item.get("strength") or "").lower() == "strong" and lacks_concrete_anchor:
            item["strength"] = "medium"
            item["model_adapter_strength_downgrade"] = True
            downgraded += 1
        if len(examples) < 3:
            examples.append({
                "evidence_id": str(item.get("evidence_id") or ""),
                "before": evidence_text[:160],
                "after": replacement[:160],
            })
    if adapted:
        worker_payload = dict(worker_payload)
        worker_payload["evidence_map"] = evidence_items
        worker_payload["model_adapter_quote_first_rewrite_count"] = adapted
        worker_payload["model_adapter_strength_downgrade_count"] = downgraded
        manager_payload["model_adapter_quote_first_rewrite_count"] = int(manager_payload.get("model_adapter_quote_first_rewrite_count") or 0) + adapted
        manager_payload["model_adapter_strength_downgrade_count"] = int(manager_payload.get("model_adapter_strength_downgrade_count") or 0) + downgraded
        if trace_worker is not None:
            trace_worker["model_adapter_mode"] = mode
            trace_worker["model_adapter_quote_first_enabled"] = True
            trace_worker["model_adapter_quote_first_rewrite_count"] = adapted
            trace_worker["model_adapter_strength_downgrade_count"] = downgraded
            trace_worker["model_adapter_quote_first_examples"] = examples
    elif trace_worker is not None:
        trace_worker["model_adapter_mode"] = mode
        trace_worker["model_adapter_quote_first_enabled"] = True
    return worker_payload


def _maybe_salvage_first_support_payload(
    worker_id: str,
    worker_payload: Dict[str, Any],
    state: Dict[str, Any],
    manager_payload: Dict[str, Any],
    trace_worker: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Prevent Evidence Agent first-support dead loops without fabricating strong evidence."""
    if worker_id != "Evidence Agent" or not isinstance(worker_payload, dict):
        return worker_payload
    if _is_negative_evidence_formation_turn(manager_payload):
        return worker_payload
    if worker_payload.get("evidence_map"):
        return worker_payload
    action_type = str(manager_payload.get("effective_action_type") or manager_payload.get("action_type") or "").strip()
    if action_type not in {"verify_evidence", "request_evidence_recheck"}:
        return worker_payload
    quote_bank = [
        item for item in _support_quote_bank_from_state(state)
        if not _first_support_quote_is_negative(item)
        and str(item.get("raw_quote") or "").strip()
    ]
    if not quote_bank:
        return worker_payload
    claims_by_id = _real_claims_by_id(state)
    target_claim_ids = [
        str(item).strip()
        for item in (manager_payload.get("target_claim_ids") or [])
        if str(item).strip() in claims_by_id
    ] or list(claims_by_id.keys())[:4]
    first_support_claim_ids = [
        claim_id for claim_id in target_claim_ids
        if claim_id and not _claim_has_any_support(state, claim_id)
    ]
    if not first_support_claim_ids:
        return worker_payload

    def rank_pair(pair: tuple[str, Dict[str, Any]]) -> tuple[int, int, int, int, int, int, int]:
        claim_id, quote = pair
        claim = claims_by_id.get(claim_id, {})
        claim_text = " ".join(str(claim.get(key) or "") for key in ("claim", "evidence_need", "claim_type"))
        quote_text = " ".join(str(quote.get(key) or "") for key in ("raw_quote", "source_locator", "source_bucket", "support_role_hint"))
        overlap = int(quote.get("claim_overlap_score") or 0) + _word_overlap_score(claim_text, quote_text)
        source = _first_support_source_bucket(quote)
        source_priority = {
            "table_or_figure": 7,
            "results": 6,
            "claim_match_result": 6,
            "ablation": 5,
            "comparison": 4,
            "method": 3,
            "claim_match_method": 3,
            "theory_or_proof": 2,
            "claim_match": 2,
            "abstract": 1,
        }.get(source, 0)
        locator = str(quote.get("source_locator") or "")
        locator_specific = 1 if re.search(r"\b(?:Table|Figure|Fig\.|Section|Sec\.)\s*\d+", locator, re.IGNORECASE) else 0
        non_abstract = 0 if source == "abstract" else 1
        non_title = 0 if _first_support_quote_is_title_or_abstract_stub(quote) else 1
        quote_length = min(len(str(quote.get("raw_quote") or "")), 260)
        claim_priority = _first_support_claim_priority(claim)
        # Source/depth quality must dominate lexical overlap. Otherwise a title
        # that repeats the claim's buzzwords beats a table/method quote and only
        # creates shallow medium support that the final view correctly drops.
        return (
            non_title,
            non_abstract,
            source_priority,
            claim_priority,
            locator_specific,
            overlap,
            quote_length,
        )

    pairs = [(claim_id, quote) for claim_id in first_support_claim_ids for quote in quote_bank]
    if not pairs:
        return worker_payload
    claim_id, quote = max(pairs, key=rank_pair)
    quote_text = str(quote.get("raw_quote") or "").strip()
    if not quote_text:
        return worker_payload
    source = _first_support_source_bucket(quote)
    evidence_id = f"evidence-first-support-{len((state or {}).get('evidence_map', []) or []) + 1}"
    evidence_item = {
        "evidence_id": evidence_id,
        "claim_id": claim_id,
        "evidence": _first_support_evidence_text(quote_text),
        "source": quote.get("source_locator") or quote.get("source_bucket") or "paper quote bank",
        "source_locator": quote.get("source_locator") or "",
        "raw_quote": quote_text,
        "quote_id": quote.get("quote_id") or "",
        "source_span_start": int(quote.get("source_span_start", -1) or -1),
        "source_span_end": int(quote.get("source_span_end", -1) or -1),
        "strength": "medium",
        "stance": "partially_supports",
        "binding_status": "bound_real_claim",
        "binding_confidence": 0.35,
        "binding_rationale": "Fallback first-support item uses a copied quote bank span; semantic strength remains conservative.",
        "grounded_judge_label": "self_claimed_by_agent",
        "grounded_judge_reason": "Quote was copied from Evidence Quote Bank; verifier assigns final grounding label.",
        "support_source_bucket": _quote_bank_source_to_support_bucket(source),
        "support_quality_reason": (
            "Conservative medium support prevents an empty evidence dead loop; "
            "quote selection prioritized non-abstract method/result/table anchors over title or abstract stubs."
        ),
        "first_support_fallback_from_quote_bank": True,
    }
    updated = dict(worker_payload)
    updated["evidence_map"] = [evidence_item]
    summary = str(updated.get("dialogue_summary") or "").strip()
    suffix = "First-support fallback copied one quote-bank span because the Evidence Agent returned only unresolved questions."
    updated["dialogue_summary"] = f"{summary} {suffix}".strip()
    manager_payload["first_support_fallback_from_quote_bank"] = True
    manager_payload["first_support_fallback_claim_id"] = claim_id
    manager_payload["first_support_fallback_quote_id"] = quote.get("quote_id") or ""
    if trace_worker is not None:
        trace_worker["first_support_fallback_from_quote_bank"] = True
        trace_worker["first_support_fallback_claim_id"] = claim_id
        trace_worker["first_support_fallback_quote_id"] = quote.get("quote_id") or ""
    return normalize_review_update_payload(updated, required_fields=["evidence_map"])

# PR4 step 1: route runner policy calls through the shared policy module while keeping local compatibility names.
AUTO_FINALIZE_MIN_TURNS = review_policy.AUTO_FINALIZE_MIN_TURNS
MIN_STATE_REQUIREMENTS = review_policy.MIN_STATE_REQUIREMENTS
ACTION_TO_WORKERS = review_policy.ACTION_TO_WORKERS
_state_counts = review_policy.state_counts
_payload_counts = review_policy.payload_counts
_general_worker_fallback = review_policy.general_worker_fallback
_pick_workers_for_action = review_policy.pick_workers_for_action
_mode_allowed_actions = review_policy.mode_allowed_actions
_infer_action_from_state = review_policy.infer_action_from_state
_infer_effective_action_type = review_policy.infer_effective_action_type
_state_is_complete = review_policy.state_is_complete
_build_auto_finalize_payload = review_policy.build_auto_finalize_payload
_apply_manager_policy_fallback = review_policy.apply_manager_policy_fallback
_apply_finalize_policy = review_policy.apply_finalize_policy
_resolve_result_final_decision = review_policy.resolve_result_final_decision
_default_manager_payload = review_policy.default_manager_payload
get_agent_plan = review_policy.get_agent_plan
_synthesize_summary_update = review_policy.synthesize_summary_update





def _fallback_evidence_labels(raw_text: str, action_type: str) -> tuple[str, str]:
    lowered = str(raw_text or "").lower()
    contradiction_terms = ("contradict", "inconsistent", "however", "but", "fails", "not support", "does not support", "weaker")
    missing_terms = ("missing", "unclear", "no evidence", "not provided", "lacks", "absent")
    if action_type == "challenge_previous_hypothesis" or any(term in lowered for term in contradiction_terms):
        return "weak", "contradicts"
    if action_type == "request_evidence_recheck" or any(term in lowered for term in missing_terms):
        return "missing", "missing"
    return "missing", "missing"




_PROMPT_ECHO_MARKERS = (
    "output contract",
    "return this schema",
    "evidence state slice.allowed_claim_ids",
    "json schema",
    "you are the",
    "i am the evidence agent",
    "my role is the evidence agent",
    "task introduction",
    "patch mode requirement",
    "strict json object",
    "must output exactly one",
    "no reasoning text",
    "machine-readable json",
    "specific json format",
    "my output should be",
    "one of two shapes",
    "found or not_assessable",
    "no prose",
    "no markdown",
    "inside ... block",
    "inside a ... block",
    "phase:",
    "turn mode:",
    "action type",
    "allowed_claim_ids",
    "system prompt",
    "key points from the task",
)


def _looks_like_prompt_or_schema_echo(text: str) -> bool:
    lowered = str(text or "").lower()
    if not lowered.strip():
        return False
    normalized = re.sub(r"[^a-z0-9]+", " ", lowered)
    hits = sum(
        1
        for marker in _PROMPT_ECHO_MARKERS
        if marker in lowered or re.sub(r"[^a-z0-9]+", " ", marker).strip() in normalized
    )
    if lowered.lstrip().startswith("output contract") or lowered.lstrip().startswith("return this schema"):
        return True
    if re.search(r"\bi am (?:the )?evidence agent\b", normalized) and "json" in normalized:
        return True
    return hits >= 2


_STRUCTURED_PAYLOAD_FRAGMENT_MARKERS = (
    '"flaw_candidates"',
    '"conflict_notes"',
    '"unresolved_questions"',
    '"dialogue_summary"',
    '"recommendation"',
    '"claim_id"',
    '"evidence_ids"',
    '"severity"',
    '"status"',
)


def _looks_like_structured_payload_fragment(text: str) -> bool:
    value = str(text or "").strip()
    if not value:
        return False
    lowered = value.lower()
    marker_hits = sum(1 for marker in _STRUCTURED_PAYLOAD_FRAGMENT_MARKERS if marker in lowered)
    if "<json>" in lowered and "</json>" not in lowered:
        return marker_hits >= 1
    stripped = lowered.lstrip()
    if stripped.startswith("{") or stripped.startswith("["):
        return marker_hits >= 2
    return False


def _fallback_evidence_blocked_payload(reason: str) -> Dict[str, Any]:
    return normalize_review_update_payload(
        {
            "unresolved_questions": [reason],
            "dialogue_summary": "Fallback evidence extraction was blocked because the malformed output was agent/schema text rather than paper evidence.",
            "recommendation": "undecided",
        }
    )


def _fallback_critique_blocked_payload(reason: str) -> Dict[str, Any]:
    return _build_emission_failure_payload(
        "CRITIQUE_TRUNCATED_STRUCTURED_OUTPUT_BLOCKED",
        reason,
    )


def _decision_view_flaw_layer_and_conflict(state: Dict[str, Any], flaw_id: str) -> tuple[str, bool]:
    target = str(flaw_id or "").strip()
    if not target:
        return "", False
    try:
        import copy as _copy

        view_state = _copy.deepcopy(state or {})
        view_state.pop("decision_hygiene", None)
        view = build_decision_hygiene_view(view_state)
    except Exception:
        return "", False
    for flaw in view.get("flaw_candidates", []) or []:
        if not isinstance(flaw, dict) or str(flaw.get("flaw_id") or "").strip() != target:
            continue
        layer = str(flaw.get("final_view_flaw_layer") or "").strip()
        conflicts = flaw.get("hygiene_negative_grounding_conflicts") or []
        active_conflicts = [
            conflict
            for conflict in conflicts
            if not (
                isinstance(conflict, dict)
                and str(conflict.get("reason") or "") == "negative_evidence_id_not_verified"
                and str(conflict.get("semantic_grounding_label") or "").strip() not in {
                    "",
                    "semantic_negative_verified",
                    "semantic_support_verified",
                }
            )
        ]
        return layer, bool(active_conflicts)
    return "", False


def _blocked_final_view_concern_recovery_payload(flaw_id: str, layer: str) -> Dict[str, Any]:
    readable_layer = str(layer or "potential_concern").strip() or "potential_concern"
    return normalize_review_update_payload(
        {
            "action": "blocked",
            "target_type": "flaw",
            "target_id": flaw_id,
            "blocked_reason": (
                f"Target flaw is already represented as final-view {readable_layer}; "
                "routing it to an assessment limitation would weaken a preserved negative finding."
            ),
            "missing_requirements": ["over-escalated confirmed weakness or active negative grounding conflict"],
            "recovery_terminal": True,
            "recovery_terminal_reason": _PROTECTED_POTENTIAL_CONCERN_TERMINAL_REASON,
            "recovery_repeat_allowed": False,
        }
    )


def _diagnosis_pending_concern_already_exists(state: Dict[str, Any], claim_id: str) -> bool:
    claim_id = str(claim_id or "").strip()
    if not claim_id:
        return False
    for item in state.get("diagnosis_pending_concerns", []) or []:
        if not isinstance(item, dict):
            continue
        if str(item.get("claim_id") or "").strip() == claim_id and str(item.get("status") or "").strip().lower() == "recorded":
            return True
    return False


def _claim_requirement_gap_recovery_patch_payload(
    state: Dict[str, Any],
    manager_payload: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    if not _diagpending_recovery_enabled():
        return None
    # Refactor 2026-06-21: use verified_coverage_gap_items (paper-level, over-flag eliminated)
    # instead of claim_requirement_gap_items (claim-centric, 56% over-flag).
    # We must build the hygiene view ourselves to get claim_requirement_audit.
    try:
        view_state = copy.deepcopy(state or {})
        view_state.pop("decision_hygiene", None)
        view = build_decision_hygiene_view(view_state)
    except Exception:
        return None
    requirement_audit = view.get("claim_requirement_audit") or {}
    if not isinstance(requirement_audit, dict):
        return None
    gaps = [
        item for item in requirement_audit.get("verified_coverage_gap_items", []) or []
        if isinstance(item, dict) and item.get("claim_id") and item.get("missing_requirements")
    ]
    if not gaps:
        return None
    preferred_claim_ids = [
        str(item or "").strip()
        for item in manager_payload.get("target_claim_ids", []) or []
        if str(item or "").strip()
    ]
    ordered_gaps = sorted(
        enumerate(gaps),
        key=lambda pair: (
            0 if str(pair[1].get("claim_id") or "").strip() in preferred_claim_ids else 1,
            -len(pair[1].get("missing_requirements") or []),
            pair[0],
        ),
    )
    for _, gap in ordered_gaps:
        claim_id = str(gap.get("claim_id") or "").strip()
        if not claim_id or _diagnosis_pending_concern_already_exists(state, claim_id):
            continue
        missing_requirements = [
            str(item or "").strip()
            for item in gap.get("missing_requirements") or []
            if str(item or "").strip()
        ]
        if not missing_requirements:
            continue
        missing_negative_types = [
            str(item or "").strip()
            for item in gap.get("missing_negative_types") or []
            if str(item or "").strip()
        ]
        claim_text = str(gap.get("claim") or "").strip()
        reason = (
            "Claim-requirement audit found missing verified support coverage; recovery records "
            "this as a diagnosis-pending potential concern without treating it as quote-grounded negative evidence."
        )
        return normalize_review_update_payload(
            {
                "action": "apply_recovery_patch",
                "target_type": "claim_requirement_gap",
                "target_id": claim_id,  # Use claim_id directly, not gap_id (gap_id is too long and causes UNKNOWN_TARGET)
                "old_status": "open",
                "new_status": "recorded",
                "supporting_evidence_ids": [],
                "missing_requirements": missing_requirements[:6],
                "missing_negative_types": missing_negative_types[:6],
                "reason_for_change": reason,
                "resolution_expectation": "partially_resolved",
                "confidence": 0.72,
                "recovery_patch_operation": "record_diagnosis_pending_concern",
                "diagnosis_pending_concern": {
                    "claim_id": claim_id,
                    "claim": claim_text,
                    "missing_requirements": missing_requirements[:6],
                    "missing_negative_types": missing_negative_types[:6],
                    "reason": reason,
                    "final_view": "potential_concern",
                    "status": "recorded",
                    "grounding_status": "diagnosis_pending_verification",
                    "basis": "claim_requirement_vs_verified_support",
                },
            }
        )
    return None


def _absence_audit_mark_contested_recovery_patch_payload(
    state: Dict[str, Any],
    manager_payload: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    """Record supported-claim vs reviewer-inferred absence as contested.

    Absence-audit evidence is generated in the final decision view from a
    deterministic claim-requirement audit. It is not quote-grounded evidence
    and must not downgrade claim status, but it can safely anchor a
    non-destructive contested relation when the same real claim has verified
    positive support.
    """
    if not _diagpending_recovery_enabled():
        return None
    try:
        view_state = copy.deepcopy(state or {})
        view_state.pop("decision_hygiene", None)
        view = build_decision_hygiene_view(view_state)
    except Exception:
        return None
    claim_lookup = {
        str(item.get("claim_id") or ""): item
        for item in (state or {}).get("claims", []) or []
        if isinstance(item, dict) and str(item.get("claim_id") or "")
    }
    raw_evidence_lookup = {
        str(item.get("evidence_id") or ""): item
        for item in (state or {}).get("evidence_map", []) or []
        if isinstance(item, dict) and str(item.get("evidence_id") or "")
    }
    absence_by_claim: Dict[str, List[str]] = {}
    for evidence in view.get("evidence_map", []) or []:
        if not isinstance(evidence, dict):
            continue
        if str(evidence.get("source") or "").strip() != "reviewer_absence_audit":
            continue
        if str(evidence.get("review_negative_label") or "").strip() != "review_negative_absence_audit_verified":
            continue
        if str(evidence.get("verified_grounding_label") or "").strip() != "paper_absence_audit_verified":
            continue
        if str(evidence.get("audit_basis") or "").strip() != "claim_requirement_vs_verified_support":
            continue
        claim_id = str(evidence.get("claim_id") or "").strip()
        evidence_id = str(evidence.get("evidence_id") or "").strip()
        if claim_id and evidence_id:
            absence_by_claim.setdefault(claim_id, []).append(evidence_id)
    if not absence_by_claim:
        return None
    preferred_claim_ids = [
        str(item or "").strip()
        for item in manager_payload.get("target_claim_ids", []) or []
        if str(item or "").strip()
    ]
    ordered_claim_ids = sorted(
        absence_by_claim,
        key=lambda claim_id: (
            0 if claim_id in preferred_claim_ids else 1,
            -len(absence_by_claim.get(claim_id, [])),
            claim_id,
        ),
    )
    for claim_id in ordered_claim_ids:
        claim = claim_lookup.get(claim_id)
        if not _is_recovery_contested_claim_target(claim or {}):
            continue
        old_status = str((claim or {}).get("status") or "uncertain").strip().lower() or "uncertain"
        if old_status not in {"supported", "partially_supported", "uncertain"}:
            continue
        negative_ids = list(dict.fromkeys(absence_by_claim.get(claim_id, [])))[:4]
        if not negative_ids or _contested_relation_already_exists(state, claim_id, negative_ids):
            continue
        support_ids = _verified_positive_support_ids_for_claim(claim or {}, raw_evidence_lookup)
        if not support_ids:
            continue
        issue_bundle_ids = []
        for evidence_id in negative_ids:
            evidence = next(
                (
                    item for item in view.get("evidence_map", []) or []
                    if isinstance(item, dict) and str(item.get("evidence_id") or "").strip() == evidence_id
                ),
                {},
            )
            bundle = evidence.get("review_issue_bundle") if isinstance(evidence, dict) else {}
            issue_id = str(evidence.get("review_issue_id") or (bundle or {}).get("issue_id") or "").strip() if isinstance(evidence, dict) else ""
            if issue_id:
                issue_bundle_ids.append(issue_id)
        issue_bundle_basis = bool(issue_bundle_ids)
        return normalize_review_update_payload(
            {
                "action": "apply_recovery_patch",
                "target_type": "claim",
                "target_id": claim_id,
                "old_status": old_status,
                "new_status": old_status,
                "supporting_evidence_ids": negative_ids,
                "reason_for_change": (
                    "Verified review issue bundle contests a claim that also has verified positive support; "
                    "recovery records a contested relation without changing claim status."
                    if issue_bundle_basis else
                    "Reviewer-inferred absence evidence contests a claim that also has verified positive support; "
                    "recovery records a contested relation without changing claim status."
                ),
                "resolution_expectation": "partially_resolved",
                "confidence": 0.66,
                "recovery_patch_operation": "mark_contested",
                "mark_contested": True,
                "contested_relation": {
                    "claim_id": claim_id,
                    "support_evidence_ids": support_ids[:4],
                    "negative_evidence_ids": negative_ids,
                    "relation_type": "supported_but_contested_by_review_issue",
                    "final_view": "potential_concern",
                    "negative_evidence_basis": "review_issue_bundle" if issue_bundle_basis else "reviewer_absence_audit",
                    "review_issue_bundle_ids": issue_bundle_ids[:4],
                },
            }
        )
    return None


def _scan_verified_negative_flaw_recovery_patch(
    state: Dict[str, Any],
    claim_lookup: Dict[str, Dict[str, Any]],
    evidence_lookup: Dict[str, Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    for flaw in state.get("flaw_candidates", []) or []:
        if not isinstance(flaw, dict):
            continue
        status = str(flaw.get("status") or "candidate").strip().lower()
        if status not in {"candidate", "confirmed"}:
            continue
        scan_verified_negative_ids = _flaw_verified_negative_evidence_ids_for_recovery(
            flaw,
            evidence_lookup,
        )
        scan_actionable_negative_ids = [
            evidence_id
            for evidence_id in scan_verified_negative_ids
            if _negative_evidence_record_is_actionable(evidence_lookup.get(evidence_id, {}))
        ]
        if not _flaw_has_real_recovery_claim_target(flaw, claim_lookup, evidence_lookup) and not scan_actionable_negative_ids:
            continue
        contested_patch = _mark_contested_patch_from_verified_negative_flaw(
            flaw,
            claim_lookup,
            evidence_lookup,
            state,
        )
        if contested_patch:
            return contested_patch
        if _flaw_contested_relation_already_exists(flaw, state, evidence_lookup):
            continue
        claim_patch = _claim_downgrade_patch_from_actionable_flaw(flaw, claim_lookup, evidence_lookup)
        if claim_patch:
            return claim_patch
    return None


def _fallback_recovery_patch_payload(state: Dict[str, Any], manager_payload: Dict[str, Any]) -> Dict[str, Any]:
    target_claim_ids = manager_payload.get("target_claim_ids", [])
    target_flaw_ids = manager_payload.get("target_flaw_ids", [])
    target_evidence_ids = manager_payload.get("target_evidence_ids", [])
    claim_lookup = {
        item.get("claim_id"): item
        for item in state.get("claims", [])
        if item.get("claim_id")
    }
    flaw_lookup = {
        item.get("flaw_id"): item
        for item in state.get("flaw_candidates", [])
        if item.get("flaw_id")
    }
    evidence_map = list(state.get("evidence_map", []))
    evidence_lookup = {
        str(item.get("evidence_id") or ""): item
        for item in evidence_map
        if isinstance(item, dict) and item.get("evidence_id")
    }
    deferred_terminal_block: Optional[Dict[str, Any]] = None
    deferred_block: Optional[Dict[str, Any]] = None

    # Non-destructive contested relations are the preferred recovery for a
    # verified review issue that coexists with verified positive support on the
    # same claim.  Run this before target-flaw lifecycle patches so a manager
    # target like ``flaw-reviewer-absence-*`` cannot be consumed by a terminal
    # reject or assessment-limitation route before the safer relation is tried.
    absence_contested_patch = _absence_audit_mark_contested_recovery_patch_payload(state, manager_payload)
    if absence_contested_patch is not None:
        return absence_contested_patch

    for flaw_id in list(target_flaw_ids or []):
        flaw = flaw_lookup.get(flaw_id)
        if not flaw:
            continue
        old_status = str(flaw.get("status") or "candidate").strip().lower()
        if old_status not in {"candidate", "confirmed"}:
            continue
        verified_negative_ids = _flaw_verified_negative_evidence_ids_for_recovery(
            flaw,
            evidence_lookup,
        )
        has_negative_anchor = bool(flaw.get("negative_evidence_ids"))
        actionable_negative_ids = [
            evidence_id
            for evidence_id in verified_negative_ids
            if _negative_evidence_record_is_actionable(evidence_lookup.get(evidence_id, {}))
        ]
        if not _flaw_has_real_recovery_claim_target(flaw, claim_lookup, evidence_lookup) and not actionable_negative_ids:
            blocked = _blocked_non_real_flaw_target_payload(flaw_id)
            if deferred_terminal_block is None:
                deferred_terminal_block = blocked
            continue
        if actionable_negative_ids:
            if old_status == "confirmed":
                return normalize_review_update_payload(
                    {
                        "action": "apply_recovery_patch",
                        "target_type": "flaw",
                        "target_id": flaw_id,
                        "old_status": old_status,
                        "new_status": "candidate",
                        "supporting_evidence_ids": actionable_negative_ids[:2],
                        "reason_for_change": (
                            "Verified actionable negative evidence keeps this item visible as a "
                            "potential concern, but recovery lowers the final-weakness status until "
                            "Critique Agent confirms the severity."
                        ),
                        "resolution_expectation": "partially_resolved",
                        "confidence": 0.62,
                    }
                )
            contested_patch = _mark_contested_patch_from_verified_negative_flaw(
                flaw,
                claim_lookup,
                evidence_lookup,
                state,
            )
            if contested_patch:
                return contested_patch
            if _flaw_contested_relation_already_exists(flaw, state, evidence_lookup):
                blocked = _blocked_final_view_concern_recovery_payload(flaw_id, "potential_concern")
                if deferred_terminal_block is None:
                    deferred_terminal_block = blocked
                continue
            claim_patch = _claim_downgrade_patch_from_actionable_flaw(flaw, claim_lookup, evidence_lookup)
            if claim_patch:
                return claim_patch
            blocked = _protected_potential_concern_blocked_payload(flaw_id)
            if deferred_terminal_block is None:
                deferred_terminal_block = blocked
            continue
        verified_quote_bank_negative_ids = _flaw_verified_negative_evidence_ids_for_recovery(
            flaw,
            evidence_lookup,
            quote_bank_only=True,
        )
        if verified_quote_bank_negative_ids:
            contested_patch = _mark_contested_patch_from_verified_negative_flaw(
                flaw,
                claim_lookup,
                evidence_lookup,
                state,
            )
            if contested_patch:
                return contested_patch
            if _flaw_contested_relation_already_exists(flaw, state, evidence_lookup):
                blocked = _blocked_final_view_concern_recovery_payload(flaw_id, "potential_concern")
                if deferred_terminal_block is None:
                    deferred_terminal_block = blocked
                continue
            layer, has_negative_grounding_conflict = _decision_view_flaw_layer_and_conflict(state, flaw_id)
            if has_negative_anchor and layer in {"potential_concern", "verified_potential_concern", "grounded_weakness"} and not has_negative_grounding_conflict:
                blocked = _blocked_final_view_concern_recovery_payload(flaw_id, layer)
                if deferred_terminal_block is None:
                    deferred_terminal_block = blocked
                continue
            if layer == "assessment_limitation" and not has_negative_grounding_conflict:
                blocked = normalize_review_update_payload(
                    {
                        "action": "blocked",
                        "target_type": "flaw",
                        "target_id": flaw_id,
                        "blocked_reason": (
                            "Target flaw is already represented as an assessment limitation in the decision view; "
                            "downgrading its raw candidate status would be a no-effect recovery patch."
                        ),
                        "missing_requirements": ["remaining negative grounding conflict or over-escalated concern status"],
                        "recovery_terminal": True,
                        "recovery_terminal_reason": _ASSESSMENT_LIMITATION_NO_EFFECT_TERMINAL_REASON,
                        "recovery_repeat_allowed": False,
                    }
                )
                if deferred_terminal_block is None:
                    deferred_terminal_block = blocked
                continue
            return normalize_review_update_payload(
                {
                    "action": "apply_recovery_patch",
                    "target_type": "flaw",
                    "target_id": flaw_id,
                    "old_status": old_status,
                    "new_status": "downgraded",
                    "supporting_evidence_ids": verified_quote_bank_negative_ids[:2],
                    "reason_for_change": (
                        "The flaw is grounded by paper-quoted negative or limitation evidence, "
                        "so recovery keeps it as an assessment limitation instead of escalating "
                        "it into an unsupported claim."
                    ),
                    "resolution_expectation": "partially_resolved",
                    "confidence": 0.6,
                }
            )
        supporting_ids = [str(item) for item in (flaw.get("evidence_ids") or []) if str(item) in evidence_lookup]
        if target_evidence_ids:
            selected = [item for item in supporting_ids if item in target_evidence_ids]
            supporting_ids = selected or supporting_ids
        if supporting_ids:
            layer, has_negative_grounding_conflict = _decision_view_flaw_layer_and_conflict(state, flaw_id)
            supporting_has_negative_anchor = has_negative_anchor or any(
                _negative_evidence_record_type(evidence_lookup.get(evidence_id, {}))
                not in {"", "generic_gap", "neutral_control_context", "bibliographic_or_title_noise", "neutral_instruction_noise"}
                for evidence_id in supporting_ids
            )
            if supporting_has_negative_anchor and layer in {"potential_concern", "verified_potential_concern", "grounded_weakness"} and not has_negative_grounding_conflict:
                blocked = _blocked_final_view_concern_recovery_payload(flaw_id, layer)
                if deferred_terminal_block is None:
                    deferred_terminal_block = blocked
                continue
            if layer == "assessment_limitation" and not has_negative_grounding_conflict:
                blocked = normalize_review_update_payload(
                    {
                        "action": "blocked",
                        "target_type": "flaw",
                        "target_id": flaw_id,
                        "blocked_reason": (
                            "Target flaw is already represented as an assessment limitation in the decision view; "
                            "downgrading its raw candidate status would be a no-effect recovery patch."
                        ),
                        "missing_requirements": ["remaining negative grounding conflict or over-escalated concern status"],
                        "recovery_terminal": True,
                        "recovery_terminal_reason": _ASSESSMENT_LIMITATION_NO_EFFECT_TERMINAL_REASON,
                        "recovery_repeat_allowed": False,
                    }
                )
                if deferred_terminal_block is None:
                    deferred_terminal_block = blocked
                continue
            return normalize_review_update_payload(
                {
                    "action": "apply_recovery_patch",
                    "target_type": "flaw",
                    "target_id": flaw_id,
                    "old_status": old_status,
                    "new_status": "downgraded",
                    "supporting_evidence_ids": supporting_ids[:2],
                    "reason_for_change": "The flaw lacks verified paper-negative grounding and should remain a non-confirmed assessment item.",
                    "resolution_expectation": "partially_resolved",
                    "confidence": 0.65,
                }
            )
        blocked = normalize_review_update_payload(
            {
                "action": "blocked",
                "target_type": "flaw",
                "target_id": flaw_id,
                "blocked_reason": "Target flaw lacks existing evidence ids for a safe downgrade patch.",
                "missing_requirements": ["existing evidence id aligned with target flaw"],
            }
        )
        if deferred_block is None:
            deferred_block = blocked
        continue

    if deferred_terminal_block is not None:
        return deferred_terminal_block
    scanned_negative_patch = _scan_verified_negative_flaw_recovery_patch(state, claim_lookup, evidence_lookup)
    if scanned_negative_patch is not None:
        return scanned_negative_patch
    absence_contested_patch = _absence_audit_mark_contested_recovery_patch_payload(state, manager_payload)
    if absence_contested_patch is not None:
        return absence_contested_patch
    claimreq_patch = _claim_requirement_gap_recovery_patch_payload(state, manager_payload)
    if claimreq_patch is not None:
        return claimreq_patch
    if deferred_block is not None:
        return deferred_block

    for flaw in state.get("flaw_candidates", []) or []:
        if not isinstance(flaw, dict):
            continue
        status = str(flaw.get("status") or "candidate").strip().lower()
        if status not in {"candidate", "confirmed"}:
            continue
        scan_verified_negative_ids = _flaw_verified_negative_evidence_ids_for_recovery(
            flaw,
            evidence_lookup,
        )
        scan_actionable_negative_ids = [
            evidence_id
            for evidence_id in scan_verified_negative_ids
            if _negative_evidence_record_is_actionable(evidence_lookup.get(evidence_id, {}))
        ]
        if not _flaw_has_real_recovery_claim_target(flaw, claim_lookup, evidence_lookup) and not scan_actionable_negative_ids:
            continue
        contested_patch = _mark_contested_patch_from_verified_negative_flaw(
            flaw,
            claim_lookup,
            evidence_lookup,
            state,
        )
        if contested_patch:
            return contested_patch
        if _flaw_contested_relation_already_exists(flaw, state, evidence_lookup):
            continue
        claim_patch = _claim_downgrade_patch_from_actionable_flaw(flaw, claim_lookup, evidence_lookup)
        if claim_patch:
            return claim_patch

    ordered_claim_ids = [
        str(claim_id).strip()
        for claim_id in list(target_claim_ids or [])
        if str(claim_id).strip()
        and _is_recovery_claim_status_target(claim_lookup.get(str(claim_id).strip(), {}))
    ]
    if not ordered_claim_ids:
        ordered_claim_ids = _recovery_candidate_claim_ids(state, "challenge_previous_hypothesis")
    if not ordered_claim_ids:
        absence_contested_patch = _absence_audit_mark_contested_recovery_patch_payload(state, manager_payload)
        if absence_contested_patch is not None:
            return absence_contested_patch
        claimreq_patch = _claim_requirement_gap_recovery_patch_payload(state, manager_payload)
        if claimreq_patch is not None:
            return claimreq_patch
        return normalize_review_update_payload(
            {
                "action": "blocked",
                "blocked_reason": "No strong real recovery target remained for a corrective patch.",
                "missing_requirements": ["real paper claim with verified contradictory or recovery evidence"],
            }
        )
    for claim_id in ordered_claim_ids:
        claim = claim_lookup.get(claim_id)
        if not claim:
            continue
        old_status = str(claim.get("status") or "uncertain")
        if old_status not in {"supported", "partially_supported", "uncertain"}:
            continue
        evidence_candidates = [
            item for item in evidence_map
            if item.get("claim_id") == claim_id
        ]
        if target_evidence_ids:
            evidence_candidates = [
                item for item in evidence_candidates
                if item.get("evidence_id") in target_evidence_ids
            ] or evidence_candidates
        contradictory_ids = [
            item.get("evidence_id")
            for item in evidence_candidates
            if item.get("evidence_id")
            and _allows_claim_status_downgrade_from_recovery(item)
        ]
        if contradictory_ids:
            return normalize_review_update_payload(
                {
                    "action": "apply_recovery_patch",
                    "target_type": "claim",
                    "target_id": claim_id,
                    "old_status": old_status,
                    "new_status": "unsupported",
                    "supporting_evidence_ids": contradictory_ids[:2],
                    "reason_for_change": "Contradictory or missing evidence weakens the current claim.",
                    "resolution_expectation": "partially_resolved",
                    "confidence": 0.35,
                }
            )

    # P0-1a contested-stable salvage path. After the flaw branch (downgrade
    # unverified flaws) and the claim branch (downgrade claims with direct
    # verified contradictions) both fail to emit, the only remaining
    # situation is "claim has verified positive + only quote-bank
    # verified-negative + related candidate flaw already grounded by the same
    # quote-bank evidence". The previous fallback returned blocked, which
    # the validator counts as BLOCKED_BY_POLICY. Routing the related flaw
    # candidate to a downgraded lifecycle terminus closes the limitation as
    # an acknowledged concern without overstating the negative finding, and
    # without violating the P0-5 guard that quote-bank evidence cannot
    # downgrade a claim status. Only triggers when every verified-negative
    # ground for the flaw is quote-bank-sourced (no direct verified
    # contradiction to lose).
    for claim_id in ordered_claim_ids:
        if not claim_lookup.get(claim_id):
            continue
        for flaw in state.get("flaw_candidates", []) or []:
            if not isinstance(flaw, dict):
                continue
            if claim_id not in (flaw.get("related_claim_ids") or []):
                continue
            old_status = str(flaw.get("status") or "candidate").strip().lower()
            if old_status not in {"candidate", "confirmed"}:
                continue
            verified_neg_ids: List[str] = []
            non_quote_bank_verified_neg = False
            actionable_quote_bank_verified_neg = False
            for raw in list(flaw.get("negative_evidence_ids") or []) + list(flaw.get("evidence_ids") or []):
                item = evidence_lookup.get(str(raw or "").strip())
                if not item or not _is_verified_negative_evidence_for_recovery(item):
                    continue
                source = str(item.get("source") or "").strip().lower()
                evidence_id = str(item.get("evidence_id") or "").strip()
                if not evidence_id:
                    continue
                if source == "quote-bank-negative-grounding":
                    if _negative_evidence_record_is_actionable(item):
                        actionable_quote_bank_verified_neg = True
                    if evidence_id not in verified_neg_ids:
                        verified_neg_ids.append(evidence_id)
                else:
                    non_quote_bank_verified_neg = True
            if non_quote_bank_verified_neg or actionable_quote_bank_verified_neg or not verified_neg_ids:
                continue
            flaw_id = str(flaw.get("flaw_id") or "").strip()
            if not flaw_id:
                continue
            return normalize_review_update_payload(
                {
                    "action": "apply_recovery_patch",
                    "target_type": "flaw",
                    "target_id": flaw_id,
                    "old_status": old_status,
                    "new_status": "downgraded",
                    "supporting_evidence_ids": verified_neg_ids[:2],
                    "reason_for_change": (
                        "The active flaw is grounded only by paper-quoted limitation or gap "
                        "language; that evidence acknowledges a concern but is not strong "
                        "enough to invalidate the claim. Closing the flaw lifecycle as "
                        "downgraded keeps the limitation visible without overstating it."
                    ),
                    "resolution_expectation": "partially_resolved",
                    "confidence": 0.55,
                }
            )

    claimreq_patch = _claim_requirement_gap_recovery_patch_payload(state, manager_payload)
    if claimreq_patch is not None:
        return claimreq_patch

    return normalize_review_update_payload(
        {
            "action": "blocked",
            "blocked_reason": "No grounded contradictory evidence id was available for a corrective recovery patch.",
            "missing_requirements": ["target claim with contradictory or missing evidence ids"],
        }
    )


def _build_emission_failure_payload(code: str, message: str) -> Dict[str, Any]:
    return normalize_review_update_payload(
        {
            "_emission_failure_code": code,
            "_emission_failure_message": message,
        }
    )


def _payload_has_standard_review_content(worker_payload: Dict[str, Any]) -> bool:
    return bool(
        worker_payload.get("claims")
        or worker_payload.get("evidence_map")
        or worker_payload.get("flaw_candidates")
        or worker_payload.get("conflict_notes")
        or worker_payload.get("dialogue_summary")
        or worker_payload.get("unresolved_questions")
    )


def _enforce_recovery_patch_mode_payload(
    agent_id: str,
    worker_payload: Dict[str, Any],
    raw_text: str,
    manager_payload: Optional[Dict[str, Any]] = None,
    parse_error: str = "",
) -> Dict[str, Any]:
    manager_payload = manager_payload or {}
    turn_mode = _normalize_turn_mode(manager_payload.get("turn_mode"))
    if turn_mode != "recovery_patch":
        if worker_payload.get("action") == "apply_recovery_patch" and not worker_payload.get("_recovery_patch_source"):
            worker_payload["_recovery_patch_source"] = "model_generated"
        return worker_payload

    action = worker_payload.get("action")
    if action == "apply_recovery_patch":
        if not worker_payload.get("_recovery_patch_source"):
            worker_payload["_recovery_patch_source"] = "model_generated"
        return worker_payload
    if action == "blocked":
        return worker_payload

    if manager_payload.get("decision") == "finalize" or not manager_payload.get("selected_agents"):
        code = "TRIGGERED_BUT_ROUTED_TO_SUMMARY"
        message = "Recovery patch mode was expected, but no recovery worker was actually routed for this turn."
    elif parse_error:
        if "<json>" in raw_text or "{" in raw_text:
            code = "OUTPUT_SCHEMA_MISSING"
            message = f"Recovery patch mode expected strict JSON patch output, but parsing failed: {parse_error}"
        else:
            code = "PATCH_MODE_PROMPT_IGNORED"
            message = "Recovery patch mode expected strict JSON patch output, but the worker returned unstructured text."
    elif _payload_has_standard_review_content(worker_payload):
        code = "WORKER_STAYED_IN_EVIDENCE_MODE"
        message = f"{agent_id} stayed in normal review-state generation instead of emitting apply_recovery_patch or blocked."
    else:
        code = "PATCH_MODE_PROMPT_IGNORED"
        message = f"{agent_id} did not emit apply_recovery_patch or blocked while recovery patch mode was active."

    return _build_emission_failure_payload(code, message)


def _recovery_patch_cites_only_real_evidence(
    worker_payload: Dict[str, Any],
    state: Dict[str, Any],
) -> bool:
    """True iff every supporting_evidence_id in the patch exists in evidence_map."""
    if worker_payload.get("action") != "apply_recovery_patch":
        return True
    known_ids = {
        str(item.get("evidence_id") or "")
        for item in state.get("evidence_map", []) or []
        if isinstance(item, dict) and str(item.get("evidence_id") or "")
    }
    cited = [str(eid).strip() for eid in (worker_payload.get("supporting_evidence_ids") or []) if str(eid).strip()]
    if not cited:
        return True
    return all(eid in known_ids for eid in cited)


def _claim_downgrade_patch_should_be_contested(worker_payload: Dict[str, Any], state: Dict[str, Any]) -> bool:
    if worker_payload.get("action") != "apply_recovery_patch":
        return False
    if str(worker_payload.get("target_type") or "").strip().lower() != "claim":
        return False
    if str(worker_payload.get("new_status") or "").strip().lower() != "unsupported":
        return False
    target_id = str(worker_payload.get("target_id") or "").strip()
    if not target_id:
        return False
    evidence_lookup = {
        str(item.get("evidence_id") or ""): item
        for item in state.get("evidence_map", []) or []
        if isinstance(item, dict) and item.get("evidence_id")
    }
    claim_lookup = {
        str(item.get("claim_id") or ""): item
        for item in state.get("claims", []) or []
        if isinstance(item, dict) and item.get("claim_id")
    }
    cited_ids: List[str] = []
    for key in ("supporting_evidence_ids", "negative_evidence_ids", "evidence_ids"):
        value = worker_payload.get(key)
        if isinstance(value, list):
            cited_ids.extend(str(evidence_id or "").strip() for evidence_id in value if str(evidence_id or "").strip())
        elif isinstance(value, str) and value.strip():
            cited_ids.append(value.strip())
    cited_evidence = [
        evidence_lookup.get(evidence_id, {}) or {}
        for evidence_id in dict.fromkeys(cited_ids)
    ]
    if any(_is_obligation_grounded_review_issue_for_recovery(item) for item in cited_evidence):
        return True
    if not _verified_positive_support_ids_for_claim(claim_lookup.get(target_id, {}) or {}, evidence_lookup):
        return False
    return any(
        _is_verified_negative_evidence_for_recovery(item)
        for item in cited_evidence
    )


def _claim_status_patch_targets_disallowed_claim(worker_payload: Dict[str, Any], state: Dict[str, Any]) -> bool:
    if worker_payload.get("action") != "apply_recovery_patch":
        return False
    if str(worker_payload.get("target_type") or "").strip().lower() != "claim":
        return False
    target_id = str(worker_payload.get("target_id") or "").strip()
    if not target_id:
        return True
    new_status = str(worker_payload.get("new_status") or "").strip().lower()
    old_status = str(worker_payload.get("old_status") or "").strip().lower()
    if not new_status or new_status == old_status:
        return False
    claim_lookup = {
        str(item.get("claim_id") or "").strip(): item
        for item in state.get("claims", []) or []
        if isinstance(item, dict) and str(item.get("claim_id") or "").strip()
    }
    return not _is_recovery_claim_status_target(claim_lookup.get(target_id, {}))


def _block_direct_route_to_limitation_if_preserved_concern(
    worker_payload: Dict[str, Any],
    state: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    if worker_payload.get("action") != "apply_recovery_patch":
        return None
    if str(worker_payload.get("target_type") or "").strip().lower() != "flaw":
        return None
    target_id = str(worker_payload.get("target_id") or "").strip()
    if not target_id:
        return None
    new_status = str(worker_payload.get("new_status") or "").strip().lower()
    operation = str(worker_payload.get("recovery_patch_operation") or "").strip().lower()
    reason = str(worker_payload.get("reason_for_change") or "").strip().lower()
    routes_to_limitation = (
        operation == "route_to_assessment_limitation"
        or new_status in {"downgraded", "assessment_limitation"}
        or "assessment limitation" in reason
    )
    if not routes_to_limitation:
        return None

    flaw_lookup = {
        str(item.get("flaw_id") or "").strip(): item
        for item in state.get("flaw_candidates", []) or []
        if isinstance(item, dict) and str(item.get("flaw_id") or "").strip()
    }
    flaw = flaw_lookup.get(target_id)
    if not isinstance(flaw, dict):
        return None
    evidence_lookup = {
        str(item.get("evidence_id") or "").strip(): item
        for item in state.get("evidence_map", []) or []
        if isinstance(item, dict) and str(item.get("evidence_id") or "").strip()
    }
    verified_negative_ids = _flaw_verified_negative_evidence_ids_for_recovery(flaw, evidence_lookup)
    has_negative_anchor = bool(verified_negative_ids or flaw.get("negative_evidence_ids"))
    if not has_negative_anchor:
        return None
    layer, has_negative_grounding_conflict = _decision_view_flaw_layer_and_conflict(state, target_id)
    protected_layer = layer in {"potential_concern", "verified_potential_concern", "grounded_weakness"}
    already_contested = _flaw_contested_relation_already_exists(flaw, state, evidence_lookup)
    if has_negative_grounding_conflict or not (protected_layer or already_contested):
        return None
    blocked = _blocked_final_view_concern_recovery_payload(target_id, layer or "potential_concern")
    blocked["_recovery_patch_source"] = "direct_route_to_limitation_blocked"
    blocked["direct_route_to_limitation_blocked_used"] = True
    return blocked


def _recovery_patch_has_unmatched_conflict_ids(worker_payload: Dict[str, Any], state: Dict[str, Any]) -> bool:
    if worker_payload.get("action") != "apply_recovery_patch":
        return False
    provided = {
        str(item or "").strip()
        for item in worker_payload.get("conflict_note_ids", []) or []
        if str(item or "").strip()
    }
    if not provided:
        return False
    target_type = str(worker_payload.get("target_type") or "").strip().lower()
    target_id = str(worker_payload.get("target_id") or "").strip()
    if target_type not in {"claim", "flaw"} or not target_id:
        return False
    related: set[str] = set()
    for note in state.get("conflict_notes", []) or []:
        if not isinstance(note, dict):
            continue
        conflict_id = str(note.get("conflict_id") or "").strip()
        if not conflict_id:
            continue
        if target_type == "claim" and str(note.get("claim_id") or "").strip() == target_id:
            related.add(conflict_id)
        elif target_type == "flaw" and str(note.get("flaw_id") or "").strip() == target_id:
            related.add(conflict_id)
    return bool(provided - related)


def _rebuild_recovery_patch_from_state(
    state: Dict[str, Any],
    manager_payload: Dict[str, Any],
    *,
    source: str,
    marker: str,
) -> Optional[Dict[str, Any]]:
    rebuilt = _fallback_recovery_patch_payload(state, manager_payload)
    if rebuilt.get("action") == "apply_recovery_patch" and _recovery_patch_cites_only_real_evidence(rebuilt, state):
        rebuilt["_recovery_patch_source"] = source
        rebuilt[marker] = True
        return rebuilt
    if (
        rebuilt.get("action") == "blocked"
        and str(rebuilt.get("target_type") or "").strip().lower() == "flaw"
        and str(rebuilt.get("target_id") or "").strip()
        and bool(rebuilt.get("recovery_terminal"))
        and str(rebuilt.get("recovery_terminal_reason") or "").strip()
    ):
        rebuilt["_recovery_patch_source"] = source
        rebuilt[marker] = True
        return rebuilt
    return None


def _recovery_patch_has_weak_target(worker_payload: Dict[str, Any], state: Dict[str, Any]) -> bool:
    if worker_payload.get("action") != "apply_recovery_patch":
        return False
    target_type = str(worker_payload.get("target_type") or "").strip().lower()
    target_id = str(worker_payload.get("target_id") or "").strip()
    if not target_id:
        return True
    if target_type == "hypothesis":
        return True
    if target_type == "claim":
        claim_lookup = {
            str(item.get("claim_id") or "").strip(): item
            for item in state.get("claims", []) or []
            if isinstance(item, dict) and str(item.get("claim_id") or "").strip()
        }
        return not _is_recovery_strong_claim_target(claim_lookup.get(target_id, {}))
    if target_type == "claim_requirement_gap":
        return False
    if target_type in {"flaw", "gap", "evidence_link"}:
        return False
    return True


def _blocked_weak_recovery_target_payload(worker_payload: Dict[str, Any]) -> Dict[str, Any]:
    blocked = normalize_review_update_payload(
        {
            "action": "blocked",
            "target_type": str(worker_payload.get("target_type") or ""),
            "target_id": str(worker_payload.get("target_id") or ""),
            "blocked_reason": (
                "Recovery patch targeted a hypothesis, fallback/context claim, empty id, "
                "or unsupported target type instead of a real claim/flaw/gap/evidence link."
            ),
            "missing_requirements": ["real recovery target with verified grounding"],
        }
    )
    blocked["_recovery_patch_source"] = "weak_target_blocked"
    blocked["weak_recovery_target_rebind_used"] = True
    return blocked


def _rebind_ghost_evidence_recovery_patch(
    worker_payload: Dict[str, Any],
    state: Dict[str, Any],
    manager_payload: Dict[str, Any],
) -> Dict[str, Any]:
    """ROADMAP P0 #1 hydration: if a model-generated recovery patch cites evidence
    ids that are not present in ReviewState (ghost ids, e.g. Critique negative
    quote-bank `quote-critique-negative-*`), rebuild it from real verified-negative
    evidence bound in state, or block it. Never let a ghost id reach the validator.
    """
    if worker_payload.get("action") != "apply_recovery_patch":
        return worker_payload
    if _recovery_patch_cites_only_real_evidence(worker_payload, state):
        return worker_payload
    # The patch references at least one ghost evidence id. Prefer a deterministic
    # rebuild from real verified-negative evidence already bound in state.
    rebuilt = _build_verified_negative_claim_recovery_patch(state, manager_payload)
    if rebuilt is None:
        rebuilt = _fallback_recovery_patch_payload(state, manager_payload)
    if rebuilt.get("action") == "apply_recovery_patch":
        # Final safety: the rebuild must itself cite only real evidence.
        if _recovery_patch_cites_only_real_evidence(rebuilt, state):
            rebuilt["_recovery_patch_source"] = rebuilt.get("_recovery_patch_source") or "ghost_evidence_rebind"
            rebuilt["ghost_evidence_rebind_used"] = True
            return rebuilt
    blocked = normalize_review_update_payload(
        {
            "action": "blocked",
            "target_type": str(worker_payload.get("target_type") or "claim"),
            "target_id": str(worker_payload.get("target_id") or ""),
            "blocked_reason": (
                "Recovery patch cited evidence ids that are not grounded in ReviewState; "
                "no verified paper-negative evidence is available for a safe downgrade."
            ),
            "missing_requirements": ["verified paper-negative evidence id bound to the target"],
        }
    )
    blocked["_recovery_patch_source"] = "ghost_evidence_blocked"
    blocked["ghost_evidence_rebind_used"] = True
    return blocked


def _maybe_salvage_recovery_payload(
    agent_id: str,
    worker_payload: Dict[str, Any],
    state: Dict[str, Any],
    manager_payload: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    manager_payload = manager_payload or {}
    action_type = manager_payload.get("effective_action_type") or manager_payload.get("action_type") or ""
    if worker_payload.get("action") == "apply_recovery_patch":
        if not worker_payload.get("_recovery_patch_source"):
            worker_payload["_recovery_patch_source"] = "model_generated"
        if _claim_status_patch_targets_disallowed_claim(worker_payload, state):
            rebuilt = _rebuild_recovery_patch_from_state(
                state,
                manager_payload,
                source="claim_status_target_rebind",
                marker="claim_status_target_rebind_used",
            )
            if rebuilt is not None:
                return rebuilt
        if _recovery_patch_has_unmatched_conflict_ids(worker_payload, state):
            rebuilt = _rebuild_recovery_patch_from_state(
                state,
                manager_payload,
                source="conflict_note_rebind",
                marker="conflict_note_rebind_used",
            )
            if rebuilt is not None:
                return rebuilt
        if _claim_downgrade_patch_should_be_contested(worker_payload, state):
            rebuilt = _fallback_recovery_patch_payload(state, manager_payload)
            if (
                rebuilt.get("action") == "apply_recovery_patch"
                and str(rebuilt.get("recovery_patch_operation") or "").strip() != "downgrade_claim_to_unsupported"
                and _recovery_patch_cites_only_real_evidence(rebuilt, state)
            ):
                rebuilt["_recovery_patch_source"] = "claim_downgrade_contested_rebuild"
                rebuilt["claim_downgrade_contested_rebuild_used"] = True
                return rebuilt
            return normalize_review_update_payload(
                {
                    "action": "blocked",
                    "target_type": "claim",
                    "target_id": str(worker_payload.get("target_id") or ""),
                    "blocked_reason": (
                        "Claim downgrade cited obligation-grounded review issue evidence; "
                        "recovery must record a supported-but-contested relation instead of changing claim status."
                    ),
                    "missing_requirements": ["non-destructive mark_contested recovery for verified review issue"],
                }
            )
        blocked_route = _block_direct_route_to_limitation_if_preserved_concern(worker_payload, state)
        if blocked_route is not None:
            rebuilt = _fallback_recovery_patch_payload(state, manager_payload)
            if rebuilt.get("action") == "apply_recovery_patch" and _recovery_patch_cites_only_real_evidence(rebuilt, state):
                rebuilt["_recovery_patch_source"] = "direct_route_to_limitation_retarget"
                rebuilt["direct_route_to_limitation_blocked_used"] = True
                return rebuilt
            return blocked_route
        if _recovery_patch_has_weak_target(worker_payload, state):
            rebuilt = _build_verified_negative_claim_recovery_patch(state, manager_payload)
            if rebuilt is None:
                rebuilt = _fallback_recovery_patch_payload(state, manager_payload)
            if rebuilt.get("action") == "apply_recovery_patch" and _recovery_patch_cites_only_real_evidence(rebuilt, state):
                rebuilt["_recovery_patch_source"] = rebuilt.get("_recovery_patch_source") or "weak_target_rebind"
                rebuilt["weak_recovery_target_rebind_used"] = True
                return rebuilt
            return _blocked_weak_recovery_target_payload(worker_payload)
        worker_payload = _rebind_ghost_evidence_recovery_patch(worker_payload, state, manager_payload)
        return worker_payload
    if agent_id != "Critique Agent" or action_type != "challenge_previous_hypothesis":
        return worker_payload
    if worker_payload.get("action") not in {"blocked", ""}:
        return worker_payload
    if worker_payload.get("action") == "" and not worker_payload.get("_emission_failure_code"):
        return worker_payload
    salvaged = _fallback_recovery_patch_payload(state, manager_payload)
    if salvaged.get("action") == "apply_recovery_patch":
        salvaged["_recovery_patch_source"] = "system_salvaged"
        return salvaged
    if salvaged.get("action") == "blocked":
        salvaged["_recovery_patch_source"] = salvaged.get("_recovery_patch_source") or "system_salvaged_blocked"
        return salvaged
    return worker_payload


def _recovery_verified_negative_claim_pairs(
    state: Dict[str, Any],
    manager_payload: Dict[str, Any],
) -> List[tuple[str, str]]:
    target_evidence_ids = {
        str(item).strip()
        for item in manager_payload.get("target_evidence_ids", []) or []
        if str(item).strip()
    }
    target_claim_ids = {
        str(item).strip()
        for item in manager_payload.get("target_claim_ids", []) or []
        if str(item).strip()
    }
    pairs: List[tuple[str, str]] = []
    for item in state.get("evidence_map", []) or []:
        if not isinstance(item, dict):
            continue
        evidence_id = str(item.get("evidence_id") or "").strip()
        claim_id = str(item.get("claim_id") or "").strip()
        if not evidence_id or not claim_id:
            continue
        if target_evidence_ids and evidence_id not in target_evidence_ids:
            continue
        if target_claim_ids and claim_id not in target_claim_ids:
            continue
        if not _allows_claim_status_downgrade_from_recovery(item):
            continue
        pairs.append((claim_id, evidence_id))
    return list(dict.fromkeys(pairs))


def _build_verified_negative_claim_recovery_patch(
    state: Dict[str, Any],
    manager_payload: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    claim_lookup = {
        str(item.get("claim_id") or ""): item
        for item in state.get("claims", []) or []
        if isinstance(item, dict) and item.get("claim_id")
    }
    for claim_id, evidence_id in _recovery_verified_negative_claim_pairs(state, manager_payload):
        claim = claim_lookup.get(claim_id)
        if not _is_recovery_claim_status_target(claim or {}):
            continue
        old_status = str((claim or {}).get("status") or "uncertain").strip().lower()
        if old_status not in {"supported", "partially_supported", "uncertain"}:
            continue
        if _verified_positive_support_ids_for_claim(claim or {}, {
            str(item.get("evidence_id") or ""): item
            for item in state.get("evidence_map", []) or []
            if isinstance(item, dict) and item.get("evidence_id")
        }):
            continue
        return normalize_review_update_payload(
            {
                "action": "apply_recovery_patch",
                "_recovery_patch_source": "system_salvaged_verified_negative",
                "target_type": "claim",
                "target_id": claim_id,
                "old_status": old_status,
                "new_status": "unsupported",
                "supporting_evidence_ids": [evidence_id],
                "reason_for_change": "Verified paper-negative evidence directly weakens the current claim, so recovery downgrades the claim instead of trusting an unsafe model patch.",
                "resolution_expectation": "partially_resolved",
                "confidence": 0.55,
            }
        )
    return None


def _recovery_patch_uses_verified_negative_evidence(
    worker_payload: Dict[str, Any],
    state: Dict[str, Any],
) -> bool:
    if worker_payload.get("action") != "apply_recovery_patch":
        return False
    evidence_lookup = {
        str(item.get("evidence_id") or ""): item
        for item in state.get("evidence_map", []) or []
        if isinstance(item, dict) and item.get("evidence_id")
    }
    for evidence_id in worker_payload.get("supporting_evidence_ids", []) or []:
        item = evidence_lookup.get(str(evidence_id))
        if item and _is_verified_negative_evidence_for_recovery(item):
            return True
    return False


def _blocked_recovery_missing_reason(worker_payloads: Sequence[Dict[str, Any]]) -> str:
    pieces: List[str] = []
    for item in worker_payloads or []:
        payload = item.get("payload", {}) if isinstance(item, dict) else {}
        if payload.get("action") != "blocked":
            continue
        for key in ("blocked_reason", "reason_for_change", "recovery_failure_message"):
            value = str(payload.get(key) or "").strip()
            if value:
                pieces.append(value)
        pieces.extend(str(value).strip() for value in (payload.get("missing_requirements", []) or []) if str(value).strip())
    reason = " ".join(dict.fromkeys(pieces))
    lowered = reason.lower()
    if not reason or not any(term in lowered for term in ("missing", "insufficient", "incomplete", "truncated", "full text", "cannot verify", "lacks")):
        return ""
    return _clip_text(reason, 500)


def _unique_recovery_missing_evidence_id(state: Dict[str, Any], claim_id: str) -> str:
    existing = {str(item.get("evidence_id") or "") for item in state.get("evidence_map", []) or []}
    safe_claim_id = re.sub(r"[^a-zA-Z0-9]+", "-", str(claim_id or "").strip()).strip("-").lower() or "claim"
    base = f"evidence-recovery-missing-{safe_claim_id}"
    candidate = base
    index = 1
    while candidate in existing:
        index += 1
        candidate = f"{base}-{index}"
    return candidate


def _build_blocked_missing_recovery_salvage(
    worker_payloads: Sequence[Dict[str, Any]],
    state: Dict[str, Any],
    manager_payload: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """Bug B fix: this salvage always synthesizes an `evidence-recovery-missing-*`
    marker and uses it as `supporting_evidence_id` of a `new_status=unsupported`
    patch. The downstream validator correctly rejects every such patch with
    `EVIDENCE_SEMANTIC_MISMATCH` ("Claim downgrade to unsupported cannot be
    justified by system recovery missing markers"). On the 2026-05-22 full39
    run this path produced 9/9 of the valid-but-no-commit cases — purely wasted
    emit→validate→reject round-trips.

    Per the 2026-05-21 design intent ("system missing marker 只能作为 assessment
    limitation / flaw lifecycle 信号"), the synthetic-marker claim downgrade is
    not a legal recovery action. Disable the salvage entirely; the original
    `blocked` Critique/Evidence payloads already convey the missing-evidence
    signal and the Manager can decide to gather verified negative evidence in a
    later turn.
    """
    return []


def _maybe_salvage_turn_level_recovery_patch(
    worker_payloads: List[Dict[str, Any]],
    state: Dict[str, Any],
    manager_payload: Optional[Dict[str, Any]] = None,
    trace_item: Optional[Dict[str, Any]] = None,
) -> None:
    manager_payload = manager_payload or {}
    action_type = manager_payload.get("effective_action_type") or manager_payload.get("action_type") or ""
    if action_type != "challenge_previous_hypothesis":
        return
    trusted_negative_patch = _build_verified_negative_claim_recovery_patch(state, manager_payload)
    existing_patch_index = next(
        (
            idx for idx, item in enumerate(worker_payloads)
            if item.get("payload", {}).get("action") == "apply_recovery_patch"
        ),
        None,
    )
    if existing_patch_index is not None:
        existing_payload = worker_payloads[existing_patch_index].get("payload", {})
        if _claim_status_patch_targets_disallowed_claim(existing_payload, state) or _recovery_patch_has_unmatched_conflict_ids(existing_payload, state):
            marker = (
                "claim_status_target_rebind_used"
                if _claim_status_patch_targets_disallowed_claim(existing_payload, state)
                else "conflict_note_rebind_used"
            )
            source = "claim_status_target_rebind" if marker == "claim_status_target_rebind_used" else "conflict_note_rebind"
            rebuilt = _rebuild_recovery_patch_from_state(
                state,
                manager_payload,
                source=source,
                marker=marker,
            )
            if rebuilt is not None:
                worker_payloads[existing_patch_index]["payload"] = rebuilt
                if trace_item is not None:
                    for call in trace_item.get("worker_calls", []):
                        if call.get("payload", {}).get("action") == "apply_recovery_patch":
                            call["payload"] = rebuilt
                            call["salvaged_recovery_patch"] = True
                            call["salvage_reason"] = source
                            break
                return
        if _recovery_patch_uses_verified_negative_evidence(existing_payload, state):
            return
        if trusted_negative_patch:
            worker_payloads[existing_patch_index]["payload"] = trusted_negative_patch
            if trace_item is not None:
                for call in trace_item.get("worker_calls", []):
                    if call.get("payload", {}).get("action") == "apply_recovery_patch":
                        call["payload"] = trusted_negative_patch
                        call["salvaged_recovery_patch"] = True
                        call["salvage_reason"] = "replaced_model_patch_with_verified_negative_evidence"
                        break
            return
        # A model patch exists but does not cite verified negative evidence.
        # Continue scanning same-turn Evidence Agent payloads; if they contain a
        # negative/missing target quote, replace the unsafe model patch below.

    target_claim_ids = list(dict.fromkeys(manager_payload.get("target_claim_ids", []) or []))
    if not target_claim_ids:
        return
    target_claim_id_set = set(target_claim_ids)
    contradiction_pairs = []
    for item in worker_payloads:
        payload = item.get("payload", {})
        for evidence in payload.get("evidence_map", []):
            claim_id = evidence.get("claim_id", "")
            evidence_id = evidence.get("evidence_id", "")
            stance = evidence.get("stance", "")
            strength = evidence.get("strength", "")
            if not claim_id or not evidence_id:
                continue
            if claim_id not in target_claim_id_set:
                continue
            if stance in {"contradicts", "missing"} or strength == "missing":
                contradiction_pairs.append((claim_id, evidence_id))
    if not contradiction_pairs:
        salvaged = trusted_negative_patch or _fallback_recovery_patch_payload(state, manager_payload)
        if salvaged.get("action") != "apply_recovery_patch":
            salvage_items = _build_blocked_missing_recovery_salvage(worker_payloads, state, manager_payload)
            if not salvage_items:
                return
        else:
            salvaged["_recovery_patch_source"] = "system_salvaged"
            salvage_items = [{"agent_id": "Critique Agent", "payload": salvaged}]
        for idx, item in enumerate(list(worker_payloads)):
            if item.get("agent_id") == "Critique Agent" and item.get("payload", {}).get("action") == "blocked":
                worker_payloads.pop(idx)
                break
        worker_payloads.extend(salvage_items)
        if trace_item is not None:
            for call in trace_item.get("worker_calls", []):
                if call.get("agent_id") == "Critique Agent" and call.get("payload", {}).get("action") == "blocked":
                    call["payload"] = salvage_items[-1]["payload"]
                    call["salvaged_recovery_patch"] = True
                    break
        return

    claim_lookup = {
        item.get("claim_id"): item
        for item in state.get("claims", [])
        if item.get("claim_id")
    }
    for claim_id, evidence_id in contradiction_pairs:
        claim = claim_lookup.get(claim_id)
        old_status = str((claim or {}).get("status") or "uncertain")
        if old_status not in {"supported", "partially_supported", "uncertain"}:
            continue
        patch = normalize_review_update_payload(
            {
                "action": "apply_recovery_patch",
                "_recovery_patch_source": "system_salvaged",
                "target_type": "claim",
                "target_id": claim_id,
                "old_status": old_status,
                "new_status": "unsupported",
                "supporting_evidence_ids": [evidence_id],
                "reason_for_change": "Turn-local contradictory evidence triggered deterministic recovery salvage.",
                "resolution_expectation": "partially_resolved",
                "confidence": 0.3,
            }
        )
        replaced_existing = False
        if existing_patch_index is not None:
            worker_payloads[existing_patch_index]["payload"] = patch
            replaced_existing = True
        else:
            for idx, item in enumerate(list(worker_payloads)):
                if item.get("agent_id") == "Critique Agent" and item.get("payload", {}).get("action") in {"blocked", "apply_recovery_patch"}:
                    worker_payloads.pop(idx)
                    break
            worker_payloads.append({"agent_id": "Critique Agent", "payload": patch})
        if trace_item is not None:
            for call in trace_item.get("worker_calls", []):
                if call.get("agent_id") == "Critique Agent" and call.get("payload", {}).get("action") in {"blocked", "apply_recovery_patch"}:
                    call["payload"] = patch
                    call["salvaged_recovery_patch"] = True
                    call["salvage_reason"] = "replaced_model_patch_with_turn_local_negative_evidence" if replaced_existing else "turn_local_negative_evidence"
                    break
        return



_META_CLAIM_RE = re.compile(
    r"\b(user|claim agent|evidence agent|review task|provided excerpt|json|schema|instruction|prompt|think block|cannot verify|need to extract)\b",
    re.IGNORECASE,
)
_CLAIM_LINE_RE = re.compile(r"^(?:[-*]\s*)?(?:\d+[.)]|claim\s*\d+[:.)])\s*(.+)$", re.IGNORECASE)
_CLAIM_CONTEXT_PATTERN = re.compile(
    r"\b(propose|proposes|present|presents|introduce|introduces|comprise|comprises|use|uses|utilize|utilizes|train|trains|evaluate|evaluates|experiment|experiments|benchmark|benchmarks|result|results|demonstrate|demonstrates|outperform|improve|improves|limitation|limited|only|scope|trade[- ]?off)\b",
    re.IGNORECASE,
)
_BROKEN_PAPER_TEXT_CLAIM_RE = re.compile(
    r"(?:\.\.\.|\[truncated\]|\{|\}|^\\?\)|^and\s+\.?$|^as\s+a\s+baseline\b|"
    r"\bSec\.\s*$|"
    r"^(?:abstract|introduction|related\s+work|method|results?|experiments?|ablation\s+study)\.?$)",
    re.IGNORECASE,
)
_PAPER_TEXT_SALVAGE_STOPWORDS = {
    "this",
    "that",
    "with",
    "from",
    "into",
    "paper",
    "method",
    "methods",
    "results",
    "result",
    "using",
    "used",
    "proposed",
}
_PAPER_TEXT_SALVAGE_VERBS = {
    "introduce",
    "introduces",
    "propose",
    "proposes",
    "present",
    "presents",
    "develop",
    "develops",
    "use",
    "uses",
    "achieve",
    "achieves",
    "improve",
    "improves",
    "outperform",
    "outperforms",
    "demonstrate",
    "demonstrates",
    "conduct",
    "conducts",
    "evaluate",
    "evaluates",
    "compare",
    "compares",
    "provide",
    "provides",
    "show",
    "shows",
}
_STRUCTURED_RAW_CLAIM_META_RE = re.compile(
    r"\b(claim agent|evidence agent|review task|provided excerpt|json|schema|prompt|think block|cannot verify|need to extract)\b"
    r"|\b(?:the\s+)?user\s+(?:asks?|asked|provided|requested|wants|message|goal)\b",
    re.IGNORECASE,
)


def _structured_raw_claim_has_meta_leakage(text: str) -> bool:
    return bool(_STRUCTURED_RAW_CLAIM_META_RE.search(str(text or "")))


def _iter_balanced_json_object_strings(raw_text: str) -> List[str]:
    text = str(raw_text or "")
    objects: List[str] = []
    for start, char in enumerate(text):
        if char != "{":
            continue
        depth = 0
        in_string = False
        escape = False
        for index in range(start, len(text)):
            current = text[index]
            if in_string:
                if escape:
                    escape = False
                elif current == "\\":
                    escape = True
                elif current == '"':
                    in_string = False
                continue
            if current == '"':
                in_string = True
            elif current == "{":
                depth += 1
            elif current == "}":
                depth -= 1
                if depth == 0:
                    objects.append(text[start:index + 1])
                    break
    return objects


def _claim_dicts_from_malformed_raw_json(raw_text: str) -> List[Dict[str, Any]]:
    """Recover complete claim objects from a truncated or prose-prefixed JSON reply."""
    claims: List[Dict[str, Any]] = []
    seen: set[Tuple[str, str]] = set()

    def add_claim(item: Any) -> None:
        if not isinstance(item, dict):
            return
        claim_text = str(item.get("claim") or item.get("text") or "").strip()
        if not claim_text:
            return
        claim_id = str(item.get("claim_id") or "").strip()
        key = (claim_id, re.sub(r"\W+", " ", claim_text.lower()).strip())
        if key in seen:
            return
        seen.add(key)
        claims.append(item)

    def _decode_json_string_fragment(value: str) -> str:
        try:
            return json.loads(f'"{value}"')
        except Exception:
            return value.replace('\\"', '"').replace("\\\\", "\\")

    def _field(segment: str, name: str) -> str:
        match = re.search(rf'"{re.escape(name)}"\s*:\s*"((?:\\.|[^"\\])*)"', segment)
        return _decode_json_string_fragment(match.group(1)).strip() if match else ""

    def _list_field(segment: str, name: str) -> List[str]:
        match = re.search(rf'"{re.escape(name)}"\s*:\s*\[(.*?)\]', segment, flags=re.DOTALL)
        if not match:
            return []
        values: List[str] = []
        for item_match in re.finditer(r'"((?:\\.|[^"\\])*)"', match.group(1)):
            decoded = _decode_json_string_fragment(item_match.group(1)).strip()
            if decoded:
                values.append(decoded)
        return values

    for object_text in _iter_balanced_json_object_strings(raw_text):
        try:
            parsed = json.loads(object_text)
        except Exception:
            continue
        if isinstance(parsed, dict) and isinstance(parsed.get("claims"), list):
            for item in parsed.get("claims", []):
                add_claim(item)
        else:
            add_claim(parsed)

    text = str(raw_text or "")
    starts = [match.start() for match in re.finditer(r'"claim_id"\s*:\s*"', text)]
    for offset, start in enumerate(starts):
        end = starts[offset + 1] if offset + 1 < len(starts) else len(text)
        segment = text[start:end]
        claim_id = _field(segment, "claim_id")
        claim_text = _field(segment, "claim")
        if not claim_id or not claim_text:
            continue
        item: Dict[str, Any] = {
            "claim_id": claim_id,
            "claim": claim_text,
        }
        for name in ("importance", "status", "claim_type", "evidence_need"):
            value = _field(segment, name)
            if value:
                item[name] = value
        coverage_tags = _list_field(segment, "coverage_tags")
        if coverage_tags:
            item["coverage_tags"] = coverage_tags
        add_claim(item)
    return claims


def _clean_fallback_claim_text(text: str) -> str:
    cleaned = " ".join(str(text or "").split())
    cleaned = re.sub(
        r"^(?:an?\s+)?(?:contribution|method|empirical|comparison|limitation|scope)\s+claim(?:\s+from\s+the\s+abstract)?\s*[:\-–]\s*",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(r"^(?:the paper|this paper|the authors)\s+(?:claims?|argues?|proposes?|demonstrates?|shows?)\s+(?:that\s+)?", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.split(r"\b(?:however|but)\b.*\b(?:infer|not detailed|not provided|excerpt)\b", cleaned, maxsplit=1, flags=re.IGNORECASE)[0].strip()
    cleaned = re.sub(r"\bI\s+(?:can|might|should)\s+infer\b.*$", "", cleaned, flags=re.IGNORECASE).strip()
    cleaned = cleaned.strip(' -:;{}')
    cleaned = re.sub(r"^(?:abstract|introduction|methods?|methodology|experiments?|evaluation|results?|discussion|conclusion)\s+(?=(?:we|our|the|this)\b)", "", cleaned, flags=re.IGNORECASE)
    return cleaned[:280]


def _fallback_claim_items_from_raw(
    raw_text: str,
    state: Dict[str, Any],
    target_claim_id: str = "",
    *,
    paper_claim_salvage: bool = False,
) -> List[Dict[str, Any]]:
    existing_ids = {str(item.get("claim_id") or "") for item in state.get("claims", []) if isinstance(item, dict)}
    next_idx = len(existing_ids) + 1
    structured_candidates = _claim_dicts_from_malformed_raw_json(raw_text)
    if structured_candidates:
        claims: List[Dict[str, Any]] = []
        seen_texts: set[str] = set()
        for raw_item in structured_candidates[:4]:
            raw_claim = _clean_fallback_claim_text(raw_item.get("claim") or raw_item.get("text") or "")
            if not raw_claim or _structured_raw_claim_has_meta_leakage(raw_claim) or len(raw_claim.split()) < 6:
                continue
            text_key = re.sub(r"\W+", " ", raw_claim.lower()).strip()
            if text_key in seen_texts:
                continue
            seen_texts.add(text_key)
            raw_claim_id = str(raw_item.get("claim_id") or "").strip()
            prefix = "claim-paper-fallback" if paper_claim_salvage else "claim-fallback"
            claim_id = raw_claim_id or f"{prefix}-{next_idx}"
            while claim_id in existing_ids or any(item["claim_id"] == claim_id for item in claims):
                next_idx += 1
                claim_id = f"{prefix}-{next_idx}"
            metadata = _claim_metadata_from_context(raw_claim) if paper_claim_salvage else {
                "claim_type": "other",
                "coverage_tags": [],
                "evidence_need": "method/result/table evidence",
            }
            if raw_item.get("claim_type"):
                metadata["claim_type"] = str(raw_item.get("claim_type"))
            if isinstance(raw_item.get("coverage_tags"), list):
                metadata["coverage_tags"] = [str(tag) for tag in raw_item.get("coverage_tags", []) if str(tag).strip()]
            if raw_item.get("evidence_need"):
                metadata["evidence_need"] = str(raw_item.get("evidence_need"))
            item = {
                "claim_id": claim_id,
                "claim": raw_claim,
                "importance": str(raw_item.get("importance") or ("high" if not claims else "medium")),
                "status": str(raw_item.get("status") or "uncertain"),
                "claim_kind": "paper_extracted" if paper_claim_salvage else "manager_fallback",
                **metadata,
            }
            if paper_claim_salvage:
                item.update({
                    "claim_origin_kind": "raw_salvaged_claim_agent_output",
                    "claim_origin": "malformed_claim_agent_output",
                    "claim_source": "claim_agent_raw_salvage",
                })
            claims.append(item)
            next_idx += 1
        if claims:
            return claims

    candidates: List[str] = []
    in_claim_region = False
    for raw_line in str(raw_text or "").splitlines():
        line = raw_line.strip()
        low = line.lower()
        if not line:
            continue
        if "claims to extract" in low or "claim to extract" in low or low.startswith("claims:"):
            in_claim_region = True
            continue
        match = _CLAIM_LINE_RE.match(line)
        if match and (in_claim_region or "claim" in low or len(candidates) > 0):
            candidate = _clean_fallback_claim_text(match.group(1))
            if candidate and not _META_CLAIM_RE.search(candidate) and len(candidate.split()) >= 6:
                candidates.append(candidate)
            continue
        if in_claim_region and len(candidates) >= 1 and low.startswith(("status", "since", "constraints", "analysis", "i will")):
            break
    claims: List[Dict[str, Any]] = []
    for candidate in candidates[:3]:
        prefix = "claim-paper-fallback" if paper_claim_salvage else "claim-fallback"
        claim_id = target_claim_id if target_claim_id and target_claim_id not in existing_ids and not claims else f"{prefix}-{next_idx}"
        while claim_id in existing_ids or any(item["claim_id"] == claim_id for item in claims):
            next_idx += 1
            claim_id = f"{prefix}-{next_idx}"
        metadata = _claim_metadata_from_context(candidate) if paper_claim_salvage else {
            "claim_type": "other",
            "coverage_tags": [],
            "evidence_need": "method/result/table evidence",
        }
        item = {
            "claim_id": claim_id,
            "claim": candidate,
            "importance": "high" if not claims else "medium",
            "status": "uncertain",
            "claim_kind": "paper_extracted" if paper_claim_salvage else "manager_fallback",
            **metadata,
        }
        if paper_claim_salvage:
            item.update({
                "claim_origin_kind": "raw_salvaged_claim_agent_output",
                "claim_origin": "malformed_claim_agent_output",
                "claim_source": "claim_agent_raw_salvage",
            })
        claims.append(item)
        next_idx += 1
    return claims


def _extract_claim_context_from_prompt(prompt_text: str) -> str:
    match = re.search(
        r"# Claim-Relevant Paper Excerpt\s*(.*?)(?:\n# Claim State Slice|\n# Recent Turn Log|\Z)",
        str(prompt_text or ""),
        flags=re.DOTALL,
    )
    return match.group(1).strip() if match else ""


def _clean_claim_context_text(text: str) -> str:
    value = str(text or "")
    value = re.sub(r"\[[a-z_]+\]\s*", " ", value)
    value = re.sub(r"\\(?:title|section|subsection)\*?\{([^{}]*)\}", r"\1. ", value)
    value = re.sub(r"\\(?:begin|end)\{abstract\}", " ", value)
    value = re.sub(r"\\[A-Za-z]+\*?(?:\[[^\]]*\])?(?:\{[^{}]*\})?", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def _claim_metadata_from_context(candidate: str) -> Dict[str, Any]:
    low = candidate.lower()
    if re.search(r"\b(limitation|limited|only|scope|trade[- ]?off|robustness|generalization)\b", low):
        return {"claim_type": "limitation_or_boundary", "coverage_tags": ["limitation", "scope"], "evidence_need": "scope or limitation evidence"}
    if re.search(r"\b(experiment|experiments|evaluate|evaluates|evaluated|evaluation|benchmark|benchmarks|result|results|outperform|outperforms|outperformed|outperforming|performance|metric|accuracy|f1|auc)\b", low):
        return {"claim_type": "empirical", "coverage_tags": ["empirical"], "evidence_need": "result/table/benchmark evidence"}
    if re.search(r"\b(method|framework|stage|stages|use|uses|used|using|training|trained|modeling|algorithm|architecture|objective|loss|contrastive|dataset construction|instruction tuning|analysis|indicator|interpretation)\b", low):
        return {"claim_type": "method", "coverage_tags": ["method"], "evidence_need": "method or implementation evidence"}
    if re.search(r"\b(propose|proposes|present|presents|introduce|introduces|contribution|new|first)\b", low):
        return {"claim_type": "contribution", "coverage_tags": ["contribution"], "evidence_need": "paper contribution evidence"}
    return {"claim_type": "other", "coverage_tags": [], "evidence_need": "paper evidence"}


def _paper_text_salvage_tokens(value: str) -> List[str]:
    return [
        token.lower()
        for token in re.findall(r"[A-Za-z][A-Za-z0-9_-]{3,}", str(value or "")[:720])
        if token.lower() not in _PAPER_TEXT_SALVAGE_STOPWORDS
    ]


def _paper_text_salvage_looks_like_claim(text: str) -> bool:
    value = " ".join(str(text or "").split())
    if not value:
        return False
    low = value.lower()
    words = re.findall(r"[A-Za-z][A-Za-z0-9_-]*", value[:220])
    if len(words) >= 2 and words[1].lower() in _PAPER_TEXT_SALVAGE_VERBS:
        subject = words[0]
        if subject in {"We", "we"} or subject[:1].isupper():
            return True
    for subject in (
        "we",
        "this paper",
        "the paper",
        "the method",
        "the framework",
        "the model",
        "the approach",
        "our method",
        "our approach",
        "our framework",
        "our model",
        "our system",
    ):
        prefix = f"{subject} "
        if low.startswith(prefix):
            tail = low[len(prefix):].split(" ", 1)[0].strip(".,:;()[]{}")
            if tail in _PAPER_TEXT_SALVAGE_VERBS:
                return True
    if "analysis" in low and ("leads to" in low or "lead to" in low):
        return "novel interpretation" in low or "indicator" in low
    return False


def _local_sentence_from_paper_prefix(prefix: str, paper_text: str) -> str:
    needle_base = " ".join(str(prefix or "").split())
    if len(needle_base) < 40:
        return ""
    flat = " ".join(str(paper_text or "").replace("\r", " ").replace("\n", " ").split())
    if not flat:
        return ""
    flat_low = flat.lower()
    needle_low = needle_base.lower()
    for width in (180, 140, 110, 80, 60, 45):
        needle = needle_low[:width].strip()
        if len(needle) < 35:
            continue
        pos = flat_low.find(needle)
        if pos < 0:
            continue
        left_marks = [flat.rfind(mark, 0, pos) for mark in (".", "?", "!")]
        left = max(left_marks)
        start = left + 1 if left >= 0 and pos - left <= 260 else max(0, pos - 80)
        right_candidates = [
            idx for idx in (flat.find(mark, pos + len(needle)) for mark in (".", "?", "!"))
            if idx >= 0
        ]
        right = min(right_candidates) if right_candidates else min(len(flat), pos + len(needle) + 420)
        if right - start > 520:
            right = start + 520
        sentence = _clean_fallback_claim_text(flat[start:right + 1])
        if sentence and len(sentence.split()) >= 8 and "..." not in sentence:
            return sentence[:360]
    return ""


def _complete_truncated_claim_sentence_from_paper(candidate: str, paper_text: str = "") -> str:
    text = " ".join(str(candidate or "").split())
    paper = str(paper_text or "")
    if "..." not in text or not paper.strip():
        return text
    prefix = text.split("...", 1)[0].strip()
    prefix_tokens = _paper_text_salvage_tokens(prefix)
    if len(prefix_tokens) < 5:
        return text
    local_sentence = _local_sentence_from_paper_prefix(prefix, paper)
    if local_sentence:
        return local_sentence
    # Fallback only inspects a bounded prefix of the paper and cleans individual
    # sentence candidates, avoiding repeated full-paper regex passes.
    flat_paper = " ".join(paper.replace("\r", " ").replace("\n", " ").split())[:80000]
    prefix_norm = re.sub(r"\W+", " ", prefix.lower()).strip()
    best_sentence = ""
    best_overlap = 0.0
    for sentence in re.split(r"(?<=[.!?])\s+", flat_paper):
        sentence_clean = _clean_fallback_claim_text(sentence)
        if not sentence_clean or "..." in sentence_clean or len(sentence_clean.split()) < len(prefix_tokens):
            continue
        sentence_norm = re.sub(r"\W+", " ", sentence_clean.lower()).strip()
        if prefix_norm and prefix_norm in sentence_norm:
            return sentence_clean[:360]
        sentence_tokens = set(_paper_text_salvage_tokens(sentence_norm))
        unique_prefix_tokens = list(dict.fromkeys(prefix_tokens))
        overlap = sum(1 for token in unique_prefix_tokens if token in sentence_tokens) / max(1, len(unique_prefix_tokens))
        if overlap > best_overlap:
            best_overlap = overlap
            best_sentence = sentence_clean
    if best_overlap >= 0.75 and best_sentence:
        return best_sentence[:360]
    return text


def _paper_text_salvage_claim_quality(candidate: str, paper_text: str = "") -> int:
    text = " ".join(str(candidate or "").split())
    if not text or len(text.split()) < 8:
        return -100
    if len(text) > 360:
        return -100
    if _META_CLAIM_RE.search(text) or _BROKEN_PAPER_TEXT_CLAIM_RE.search(text):
        return -100
    if not _paper_text_salvage_looks_like_claim(text):
        return -100
    first = text[:1]
    if first and first.islower():
        return -100
    normalized_paper = str(paper_text or "").lower()
    if normalized_paper:
        tokens = _paper_text_salvage_tokens(text)
        if tokens:
            hit_count = sum(1 for token in dict.fromkeys(tokens) if token in normalized_paper)
            if hit_count / max(1, len(dict.fromkeys(tokens))) < 0.6:
                return -100
    score = 0
    if re.search(r"\b(?:we|this\s+paper)\s+(?:introduce|propose|present|develop)\b", text, re.IGNORECASE):
        score += 8
    low = text.lower()
    if "analysis" in low and ("leads to" in low or "lead to" in low) and ("novel interpretation" in low or "indicator" in low):
        score += 7
    if re.search(r"\b(?:improve|improves|outperform|outperforms|achieve|achieves|mIoU|accuracy|F1|AUC)\b", text, re.IGNORECASE):
        score += 7
    if re.search(r"\b(?:ablation|baseline|comparison|SOTA|state[- ]of[- ]the[- ]art|benchmark|dataset|evaluation)\b", text, re.IGNORECASE):
        score += 4
    if re.search(r"\b(?:model|framework|approach|method|network|algorithm|training|selection|criteria|component)\b", text, re.IGNORECASE):
        score += 3
    score += min(5, len(text.split()) // 8)
    return score


def _fallback_paper_claim_items_from_context(
    prompt_text: str,
    state: Dict[str, Any],
    target_claim_id: str = "",
    max_claims: int = 4,
) -> List[Dict[str, Any]]:
    context = _clean_claim_context_text(_extract_claim_context_from_prompt(prompt_text))
    if not context or max_claims <= 0:
        return []
    existing_ids = {str(item.get("claim_id") or "") for item in state.get("claims", []) if isinstance(item, dict)}
    existing_texts = {
        re.sub(r"\W+", " ", str(item.get("claim") or "").lower()).strip()
        for item in state.get("claims", []) or []
        if isinstance(item, dict)
    }
    paper_text = str((state or {}).get("paper_text") or "")
    candidates: List[Tuple[int, int, str]] = []
    seen_candidate_keys: set[str] = set()
    for index, segment in enumerate(re.split(r"(?<=[.!?])\s+", context)):
        candidate = _clean_fallback_claim_text(segment)
        candidate = _complete_truncated_claim_sentence_from_paper(candidate, paper_text)
        key = re.sub(r"\W+", " ", candidate.lower()).strip()
        if not key or key in seen_candidate_keys or key in existing_texts:
            continue
        quality = _paper_text_salvage_claim_quality(candidate, paper_text=paper_text)
        if quality < 0:
            continue
        seen_candidate_keys.add(key)
        candidates.append((quality, index, candidate))
    if not candidates:
        return []
    candidates.sort(key=lambda item: (-item[0], item[1]))
    claims: List[Dict[str, Any]] = []
    used_ids = set(existing_ids)
    for quality, _, candidate in candidates[:max_claims]:
        if target_claim_id and target_claim_id not in used_ids and not claims and not target_claim_id.startswith(("claim-paper-context", "claim-context", "claim-fallback")):
            claim_id = target_claim_id
        else:
            claim_id = _runner_slug("claim", candidate, len(used_ids) + len(claims) + 1)
        while claim_id in used_ids or any(item["claim_id"] == claim_id for item in claims):
            claim_id = _runner_slug("claim", f"{candidate}-{len(used_ids) + len(claims) + 1}", len(used_ids) + len(claims) + 1)
        metadata = _claim_metadata_from_context(candidate)
        claims.append({
            "claim_id": claim_id,
            "claim": candidate,
            "importance": "high" if not claims else "medium",
            "status": "uncertain",
            "claim_kind": "paper_extracted",
            "claim_origin_kind": "paper_text_extracted_fallback",
            "claim_origin": "claim_relevant_paper_excerpt_sentence",
            "claim_source": "paper_text_claim_salvage",
            "claim_extraction_quality": quality,
            **metadata,
        })
        used_ids.add(claim_id)
    return claims


def _fallback_claim_items_from_context(
    prompt_text: str,
    state: Dict[str, Any],
    target_claim_id: str = "",
    max_claims: int = 4,
) -> List[Dict[str, Any]]:
    context = _clean_claim_context_text(_extract_claim_context_from_prompt(prompt_text))
    if not context or max_claims <= 0:
        return []
    existing_ids = {str(item.get("claim_id") or "") for item in state.get("claims", []) if isinstance(item, dict)}
    next_idx = len(existing_ids) + 1
    candidates: List[str] = []
    seen_candidate_keys: set[str] = set()
    for segment in re.split(r"(?<=[.!?])\s+", context):
        candidate = _clean_fallback_claim_text(segment)
        if not candidate or len(candidate.split()) < 8 or _META_CLAIM_RE.search(candidate):
            continue
        if not _CLAIM_CONTEXT_PATTERN.search(candidate):
            continue
        key = candidate.lower()
        if key not in seen_candidate_keys:
            candidates.append(candidate)
            seen_candidate_keys.add(key)
        if len(candidates) >= 12:
            break
    priority = {
        "empirical": 0,
        "method": 1,
        "limitation_or_boundary": 2,
        "contribution": 3,
        "comparison": 4,
        "other": 5,
    }
    candidates = sorted(
        candidates,
        key=lambda item: (priority.get(_claim_metadata_from_context(item)["claim_type"], 5), candidates.index(item)),
    )
    claims: List[Dict[str, Any]] = []
    for candidate in candidates[:max_claims]:
        claim_id = target_claim_id if target_claim_id and target_claim_id not in existing_ids and not claims else f"claim-paper-context-{next_idx}"
        while claim_id in existing_ids or any(item["claim_id"] == claim_id for item in claims):
            next_idx += 1
            claim_id = f"claim-paper-context-{next_idx}"
        metadata = _claim_metadata_from_context(candidate)
        claims.append({
            "claim_id": claim_id,
            "claim": candidate,
            "importance": "high" if not claims else "medium",
            "status": "uncertain",
            "claim_kind": "paper_extracted",
            "claim_origin_kind": "context_synthesized",
            "claim_origin": "context_derived_paper_excerpt",
            "claim_source": "claim_relevant_paper_excerpt",
            **metadata,
        })
        next_idx += 1
    return claims


def _claim_payload_coverage_tags(payload: Dict[str, Any], state: Dict[str, Any]) -> set[str]:
    tags: set[str] = set()
    for claim in list(state.get("claims", []) or []) + list(payload.get("claims", []) or []):
        if not isinstance(claim, dict):
            continue
        claim_type = str(claim.get("claim_type") or "").strip().lower()
        if claim_type == "method":
            tags.add("method")
        elif claim_type == "empirical":
            tags.add("empirical")
        elif claim_type == "limitation_or_boundary":
            tags.add("limitation")
        for tag in claim.get("coverage_tags", []) or []:
            if isinstance(tag, str) and tag.strip():
                tags.add(tag.strip().lower())
    return tags


def _maybe_augment_claim_payload_with_context_coverage(
    agent_id: str,
    worker_payload: Dict[str, Any],
    state: Dict[str, Any],
    manager_payload: Optional[Dict[str, Any]] = None,
    prompt_text: str = "",
) -> Dict[str, Any]:
    manager_payload = manager_payload or {}
    action_type = str(manager_payload.get("effective_action_type") or manager_payload.get("action_type") or "").strip()
    if agent_id != "Claim Agent" or action_type != "extract_claims":
        return worker_payload
    if not isinstance(worker_payload, dict) or not worker_payload.get("claims"):
        return worker_payload
    if len(worker_payload.get("claims", []) or []) >= 4:
        return worker_payload
    covered_tags = _claim_payload_coverage_tags(worker_payload, state)
    missing_tags = [tag for tag in ("method", "empirical", "limitation") if tag not in covered_tags]
    if not missing_tags:
        return worker_payload
    temp_state = dict(state or {})
    temp_state["claims"] = list(state.get("claims", []) or []) + list(worker_payload.get("claims", []) or [])
    candidates = _fallback_paper_claim_items_from_context(prompt_text, temp_state)
    if not candidates:
        candidates = _fallback_claim_items_from_context(prompt_text, temp_state)
    if not candidates:
        return worker_payload
    existing_texts = {
        re.sub(r"\W+", " ", str(item.get("claim") or "").lower()).strip()
        for item in temp_state.get("claims", []) or []
        if isinstance(item, dict)
    }
    additions: List[Dict[str, Any]] = []
    missing_set = set(missing_tags)
    for candidate in candidates:
        candidate_tags = set(candidate.get("coverage_tags", []) or [])
        claim_type = str(candidate.get("claim_type") or "")
        if claim_type == "method":
            candidate_tags.add("method")
        elif claim_type == "empirical":
            candidate_tags.add("empirical")
        elif claim_type == "limitation_or_boundary":
            candidate_tags.add("limitation")
        if not candidate_tags.intersection(missing_set):
            continue
        text_key = re.sub(r"\W+", " ", str(candidate.get("claim") or "").lower()).strip()
        if not text_key or text_key in existing_texts:
            continue
        additions.append(candidate)
        existing_texts.add(text_key)
        missing_set -= candidate_tags
        if len(worker_payload.get("claims", []) or []) + len(additions) >= 4 or not missing_set:
            break
    if not additions:
        return worker_payload
    updated = dict(worker_payload)
    updated["claims"] = list(worker_payload.get("claims", []) or []) + additions
    summary = str(updated.get("dialogue_summary") or "").strip()
    suffix = "Context coverage augmentation added missing claim roles from the paper excerpt."
    updated["dialogue_summary"] = f"{summary} {suffix}".strip()
    updated["claim_context_coverage_augmented"] = True
    updated["claim_context_coverage_added_ids"] = [item.get("claim_id") for item in additions if item.get("claim_id")]
    return normalize_review_update_payload(updated, required_fields=["claims"])


def _targeted_negative_not_assessable_payload(
    manager_payload: Dict[str, Any],
    claim_id: str,
    reason: str,
) -> Dict[str, Any]:
    tasks = [
        item for item in manager_payload.get("targeted_negative_search_active_tasks", []) or []
        if isinstance(item, dict)
    ]
    task = tasks[0] if tasks else {}
    target_id = str(task.get("claim_id") or claim_id or "").strip()
    task_id = str(task.get("task_id") or "").strip()
    negative_type = str(task.get("negative_type") or "").strip()
    required_type = str(task.get("required_evidence_type") or "").strip()
    question = (
        f"Targeted negative search for {negative_type or 'paper-negative evidence'} "
        f"on claim {target_id or 'unknown'} did not yield a visible copied quote with locator."
    )
    payload = normalize_review_update_payload(
        {
            "evidence_map": [],
            "unresolved_questions": [],
            "dialogue_summary": reason,
            "recommendation": "undecided",
        }
    )
    payload["targeted_negative_search_not_assessable"] = {
        "question": question,
        "status": "not_assessable",
        "target_type": "claim",
        "target_id": target_id,
        "target_classification": "targeted_negative_search",
        "targeted_negative_search_task_id": task_id,
        "negative_evidence_type": negative_type,
        "required_evidence_type": required_type,
        "source": "targeted_negative_search_fallback",
        "hygiene_status_reason": "no_visible_quote_grounded_negative_evidence",
        "related_claim_ids": [target_id] if target_id else [],
    }
    payload["targeted_negative_search_not_assessable_count"] = 1 if target_id or task_id or negative_type else 0
    return payload


def _fallback_worker_payload(
    agent_id: str,
    raw_text: str,
    state: Dict[str, Any],
    manager_payload: Optional[Dict[str, Any]] = None,
    prompt_text: str = "",
) -> Optional[Dict[str, Any]]:
    manager_payload = manager_payload or {}
    cleaned = " ".join(str(raw_text or "").split())
    if not cleaned:
        return None
    snippet = _clean_generation_snippet(raw_text, limit=260)
    if not snippet:
        snippet = "No usable structured content was returned by the model; preserve a minimal fallback update instead of dropping the turn."
    target_claim_ids = manager_payload.get("target_claim_ids", [])
    target_flaw_ids = manager_payload.get("target_flaw_ids", [])
    target_evidence_ids = manager_payload.get("target_evidence_ids", [])
    if agent_id == "Claim Agent":
        target_claim_id = target_claim_ids[0] if target_claim_ids else ""
        claims = _fallback_claim_items_from_raw(
            raw_text,
            state,
            target_claim_id=target_claim_id,
            paper_claim_salvage=True,
        )
        if not claims:
            claims = _fallback_paper_claim_items_from_context(
                prompt_text,
                state,
                target_claim_id=target_claim_id,
                max_claims=3,
            )
        if not claims:
            claims = _fallback_claim_items_from_context(prompt_text, state, target_claim_id=target_claim_id, max_claims=2)
        if not claims:
            return normalize_review_update_payload(
                {
                    "unresolved_questions": ["Claim fallback could not recover a paper claim from malformed output without using agent/meta text."],
                    "dialogue_summary": "Fallback claim extraction was blocked because the malformed output did not contain a clean paper claim.",
                    "recommendation": "undecided",
                }
            )
        return normalize_review_update_payload(
            {
                "claims": claims,
                "unresolved_questions": ["Verify whether fallback-recovered claims are directly supported by method, experiment, result, table, or figure evidence."],
                "dialogue_summary": "Fallback claim extraction salvaged paper-claim candidates after an empty or malformed claim response.",
                "recommendation": "undecided",
            },
            required_fields=["claims"],
        )
    if agent_id == "Evidence Agent":
        if manager_payload.get("targeted_negative_search_required"):
            real_claim_ids = [
                str(item.get("claim_id", ""))
                for item in state.get("claims", [])
                if isinstance(item, dict) and _is_negative_binding_claim_target(item)
            ]
        else:
            real_claim_ids = [
                str(item.get("claim_id", ""))
                for item in state.get("claims", [])
                if item.get("claim_id") and not str(item.get("claim_id", "")).startswith("claim-fallback")
            ]
        preferred_claim_id = target_claim_ids[0] if target_claim_ids else ""
        if preferred_claim_id not in real_claim_ids:
            preferred_claim_id = real_claim_ids[0] if real_claim_ids else ""
        if not preferred_claim_id:
            return normalize_review_update_payload(
                {
                    "unresolved_questions": ["Evidence fallback could not bind the raw output to an existing real claim id."],
                    "dialogue_summary": "Fallback evidence extraction was blocked because no real claim target was available.",
                    "recommendation": "undecided",
                }
            )
        claim_id = preferred_claim_id
        if manager_payload.get("targeted_negative_search_required"):
            return _targeted_negative_not_assessable_payload(
                manager_payload,
                claim_id,
                "Targeted negative-search fallback blocked malformed or explanatory model text; no quote-grounded negative evidence was added.",
            )
        if _looks_like_prompt_or_schema_echo(snippet):
            return _fallback_evidence_blocked_payload(
                "Evidence fallback output echoed prompt/schema instructions, so no paper-grounded evidence was added."
            )
        target_evidence_id = target_evidence_ids[0] if target_evidence_ids else ""
        action_type = manager_payload.get("effective_action_type") or manager_payload.get("action_type") or "verify_evidence"
        strength, stance = _fallback_evidence_labels(snippet, action_type)
        if strength == "strong":
            strength = "medium"
        conflict_notes = []
        if stance == "contradicts":
            conflict_notes.append({
                "note": "Fallback evidence contradicts the current claim and should trigger a hypothesis check only after real evidence verification.",
                "claim_id": claim_id,
                "evidence_id": target_evidence_id or f"evidence-fallback-{len(state.get('evidence_map', [])) + 1}",
                "conflict_type": "fallback_contradiction",
            })
        return normalize_review_update_payload(
            {
                "evidence_map": [
                    {
                        "evidence_id": target_evidence_id or f"evidence-fallback-{len(state.get('evidence_map', [])) + 1}",
                        "claim_id": claim_id,
                        "evidence": snippet,
                        "source": "fallback-extraction",
                        "strength": strength,
                        "stance": stance,
                        "binding_status": "fallback_unverified",
                        "binding_confidence": 0.0,
                        "binding_rationale": "Fallback evidence is unverified and should not count as accept-level strong support.",
                    }
                ],
                "conflict_notes": conflict_notes,
                "unresolved_questions": ["Locate a concrete table, figure, or experiment supporting or contradicting this claim."],
                "dialogue_summary": "Fallback evidence extraction was used because the raw output was not valid JSON.",
                "recommendation": "undecided",
            },
            required_fields=["evidence_map"],
        )
    if agent_id == "Critique Agent":
        claim_id = target_claim_ids[0] if target_claim_ids else (state.get("claims", [{}]) or [{}])[0].get("claim_id", "")
        evidence_id = target_evidence_ids[0] if target_evidence_ids else (state.get("evidence_map", [{}]) or [{}])[0].get("evidence_id", "")
        target_flaw_id = target_flaw_ids[0] if target_flaw_ids else ""
        action_type = manager_payload.get("effective_action_type") or manager_payload.get("action_type") or "analyze_flaws"
        if action_type == "challenge_previous_hypothesis":
            return _fallback_recovery_patch_payload(state, manager_payload)
        if _looks_like_prompt_or_schema_echo(snippet) or _looks_like_structured_payload_fragment(raw_text) or _looks_like_structured_payload_fragment(snippet):
            return _fallback_critique_blocked_payload(
                "Critique fallback output was truncated structured JSON/schema text, so no paper-grounded flaw was added."
            )
        return _fallback_critique_blocked_payload(
            "Critique fallback output was not valid structured critique JSON, so no paper-grounded flaw was added."
        )
    if agent_id.startswith("General Reviewer Agent") or agent_id == "Reviewer Agent":
        action_type = manager_payload.get("effective_action_type") or manager_payload.get("action_type") or "extract_claims"
        item_id = len(state.get("claims", [])) + 1
        target_claim_id = target_claim_ids[0] if target_claim_ids else (state.get("claims", [{}]) or [{}])[0].get("claim_id", "")
        target_evidence_id = target_evidence_ids[0] if target_evidence_ids else (state.get("evidence_map", [{}]) or [{}])[0].get("evidence_id", "")
        target_flaw_id = target_flaw_ids[0] if target_flaw_ids else ""
        if action_type in {"verify_evidence", "request_evidence_recheck"}:
            if _looks_like_prompt_or_schema_echo(snippet):
                return _fallback_evidence_blocked_payload(
                    "General-review fallback output echoed prompt/schema instructions, so no paper-grounded evidence was added."
                )
            strength, stance = _fallback_evidence_labels(snippet, action_type)
            conflict_notes = []
            evidence_id = target_evidence_id or f"evidence-general-{len(state.get('evidence_map', [])) + 1}"
            claim_id = target_claim_id or f"claim-general-{item_id}"
            if stance == "contradicts":
                conflict_notes.append({
                    "note": "Fallback general-review evidence contradicts the active claim and should trigger a challenge step.",
                    "claim_id": claim_id,
                    "evidence_id": evidence_id,
                    "conflict_type": "fallback_general_contradiction",
                })
            return normalize_review_update_payload(
                {
                    "evidence_map": [
                        {
                            "evidence_id": evidence_id,
                            "claim_id": claim_id,
                            "evidence": snippet,
                            "source": "fallback-extraction",
                            "strength": strength,
                            "stance": stance,
                        }
                    ],
                    "conflict_notes": conflict_notes,
                    "unresolved_questions": ["Replace this fallback evidence with grounded support from a section, figure, table, or experiment."],
                    "dialogue_summary": "Fallback general-review evidence extraction was used because the raw output was not valid JSON.",
                    "recommendation": "undecided",
                },
                required_fields=["evidence_map"],
            )
        if action_type in {"analyze_flaws", "challenge_previous_hypothesis"}:
            if _looks_like_prompt_or_schema_echo(snippet):
                return _fallback_critique_blocked_payload(
                    "General-review fallback output echoed prompt/schema instructions, so no paper-grounded flaw was added."
                )
            flaw_id = target_flaw_id or f"flaw-general-{len(state.get('flaw_candidates', [])) + 1}"
            flaw_status = "downgraded" if action_type == "challenge_previous_hypothesis" else "candidate"
            conflict_notes = [{
                "note": "Fallback general-review critique indicates the current conclusion may be overstated.",
                "claim_id": target_claim_id,
                "evidence_id": target_evidence_id,
                "flaw_id": flaw_id,
                "conflict_type": "fallback_general_critique_conflict",
            }] if target_claim_id or target_evidence_id else []
            return normalize_review_update_payload(
                {
                    "flaw_candidates": [
                        {
                            "flaw_id": flaw_id,
                            "title": snippet[:120],
                            "description": snippet,
                            "severity": "minor" if flaw_status == "candidate" else "minor",
                            "status": "downgraded",
                            "source": "fallback-extraction",
                            "grounding_status": "fallback_unverified",
                            "related_claim_ids": [target_claim_id] if target_claim_id else [],
                            "evidence_ids": [target_evidence_id] if target_evidence_id else [],
                            "confidence": 0.2,
                        }
                    ],
                    "conflict_notes": conflict_notes,
                    "unresolved_questions": ["Replace this fallback flaw with a grounded critique tied to the paper evidence."],
                    "dialogue_summary": "Fallback general-review flaw extraction was used because the raw output was not valid JSON.",
                    "recommendation": "undecided",
                },
                required_fields=["flaw_candidates"],
            )
        return normalize_review_update_payload(
            {
                "claims": [
                    {
                        "claim_id": target_claim_id or f"claim-general-{item_id}",
                        "claim": snippet,
                        "importance": "medium",
                        "status": "uncertain",
                    }
                ],
                "unresolved_questions": ["Review this fallback extraction and replace it with grounded structured findings."],
                "dialogue_summary": "Fallback general-review extraction was used because the raw output was not valid JSON.",
                "recommendation": "undecided",
            },
            required_fields=["claims"],
        )
    return None


def _r2_retry_log(msg: str) -> None:
    """Append a one-line R2 retry decision record to REVIEW_R2_RETRY_LOG, if set."""
    import os
    path = os.environ.get("REVIEW_R2_RETRY_LOG")
    if not path:
        return
    try:
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(msg + "\n")
    except Exception:
        pass


def _hygiene_zero_real_and_unsupported(state: Dict[str, Any]) -> tuple[bool, List[str]]:
    """Return (is_zero_real, unsupported_real_claim_ids) using the SAME hygiene lens
    as build_decision_hygiene_view / the dashboard (not the raw mid-rollout counts).
    """
    try:
        import copy as _copy
        view_state = _copy.deepcopy(state or {})
        view_state.pop("decision_hygiene", None)
        hygiene = build_decision_hygiene_view(view_state).get("decision_hygiene", {}) or {}
    except Exception:
        return (False, [])
    real_total = int(hygiene.get("real_strong_support_total", 0) or 0)
    support_by_claim = hygiene.get("real_strong_support_by_claim", {}) or {}
    real_ids = _real_claim_ids_from_state(state)
    unsupported = [cid for cid in real_ids if int(support_by_claim.get(cid, 0) or 0) == 0]
    return (real_total == 0, unsupported)


def _claims_without_real_strong_support(state: Dict[str, Any]) -> List[str]:
    """Real (paper-extracted) claim ids that currently have no real-strong support
    under the hygiene lens (consistent with the dashboard / final judgment)."""
    _, unsupported = _hygiene_zero_real_and_unsupported(state)
    return unsupported


def _maybe_zero_real_targeted_retry(
    manager_payload: Dict[str, Any],
    state: Dict[str, Any],
    step: int,
    turn_cap: int,
    worker_ids: Sequence[str],
    worker_limit: int,
) -> Dict[str, Any]:
    """R2: redirect a finalize/last-turn into a claim-scoped evidence retry when the
    paper has zero real-strong support and budget remains. Returns the (possibly
    rewritten) manager payload, with targeted_retry_triggered set when it fires."""
    if not isinstance(manager_payload, dict) or not isinstance(state, dict):
        return manager_payload
    requested = str(manager_payload.get("action_type") or "")
    decision = str(manager_payload.get("decision") or "")
    finalizing = decision == "finalize" or requested in {"finalize", "summarize_progress"}
    paper_id = str(state.get("paper_id") or "")
    if not finalizing:
        return manager_payload
    # need budget for one more substantive turn.
    if turn_cap > 0 and step >= turn_cap:
        _r2_retry_log(f"{paper_id} step={step} skip=no_budget cap={turn_cap}")
        return manager_payload
    # only one targeted retry per episode.
    if manager_payload.get("policy_source") == "zero_real_targeted_retry_override":
        return manager_payload
    for tl in (state.get("turn_logs") or []):
        if str((tl or {}).get("policy_source") or "") == "zero_real_targeted_retry_override":
            _r2_retry_log(f"{paper_id} step={step} skip=already_retried")
            return manager_payload
    is_zero_real, unsupported = _hygiene_zero_real_and_unsupported(state)
    if not is_zero_real:
        _r2_retry_log(f"{paper_id} step={step} skip=not_zero_real")
        return manager_payload
    if not unsupported:
        _r2_retry_log(f"{paper_id} step={step} skip=no_unsupported_claim")
        return manager_payload
    if "verify_evidence" not in _mode_allowed_actions(str(state.get("mode") or "s4")):
        _r2_retry_log(f"{paper_id} step={step} skip=verify_not_allowed")
        return manager_payload
    _r2_retry_log(f"{paper_id} step={step} FIRED targets={unsupported[:2]}")
    normalized = dict(manager_payload)
    normalized["policy_source"] = "zero_real_targeted_retry_override"
    normalized["decision"] = "continue"
    normalized["action_type"] = "verify_evidence"
    normalized["effective_action_type"] = "verify_evidence"
    normalized["final_decision"] = "undecided"
    normalized["final_report"] = ""
    normalized["target_claim_ids"] = unsupported[:2]
    normalized["targeted_retry_triggered"] = True
    normalized["selected_agents"] = [a for a in ["Evidence Agent"] if a in worker_ids][:worker_limit] or list(worker_ids[:1])
    notes = list(normalized.get("policy_notes", []))
    notes.append("Zero real-strong support at finalize; one targeted evidence retry on unsupported claims before finalizing.")
    normalized["policy_notes"] = list(dict.fromkeys(notes))[:8]
    return _apply_turn_mode(normalized)


def run_review_episode(
    extras: Dict[str, Any],
    mode: str,
    generate_fn: GenerateFn,
    max_turns: Optional[int] = None,
    max_workers_per_turn: Optional[int] = None,
    log_dir: Optional[str] = None,
    model_adapter_mode: str = "auto",
) -> Dict[str, Any]:
    plan = get_agent_plan(mode)
    turn_cap = int(max_turns or plan["max_turns_default"])
    worker_limit = max_workers_per_turn if max_workers_per_turn is not None else max(1, len(plan["workers"]))
    effective_adapter_mode = _normalize_model_adapter_mode((extras or {}).get("model_adapter_mode") or model_adapter_mode)
    env = ReviewEnv(max_turns=turn_cap, mode=plan["mode"], log_dir=log_dir, model_adapter_mode=effective_adapter_mode)
    env.reset(extras)

    try:
        obs = env._current_obs()
        reward = 0.0
        info: Dict[str, Any] = {}
        done = False
        runner_trace: List[Dict[str, Any]] = []
        while not done:
            step = int(obs["review_state"]["turn_id"]) + 1
            team_context = ""
            worker_ids = list(plan["workers"])

            manager_prompt = build_prompt(
                plan["manager"],
                build_manager_observation(obs, worker_ids),
                team_context,
                step,
            )
            manager_raw = generate_fn(plan["manager"], manager_prompt)
            try:
                manager_payload = normalize_agent_payload(
                    plan["manager"],
                    extract_tagged_json(manager_raw),
                    available_workers=worker_ids,
                )
            except Exception as exc:
                manager_payload = _default_manager_payload(str(exc))

            previous_action = ""
            if obs.get("turn_logs"):
                previous_action = obs["turn_logs"][-1].get("action_type", "")
            # Mainline-Final-Integrated P0-2 budget-aware refinement: attach
            # the current step + turn_cap to the manager payload BEFORE
            # ``_apply_manager_policy_fallback`` so the budget-aware
            # ``hard_negative_discovery_override`` gate inside the fallback
            # can detect the last-free-turn case and skip the override when
            # no positive support has formed yet.
            manager_payload["_phase_step"] = step
            manager_payload["_phase_turn_cap"] = turn_cap
            manager_payload = _apply_manager_policy_fallback(
                manager_payload=manager_payload,
                state=obs["review_state"],
                mode=plan["mode"],
                worker_ids=worker_ids,
                worker_limit=worker_limit,
                recent_turn_logs=obs.get("turn_logs", []),
            )
            manager_payload = _maybe_upgrade_visible_review_issue_discovery_turn(
                manager_payload,
                obs["review_state"],
                mode=plan["mode"],
                worker_ids=worker_ids,
                worker_limit=worker_limit,
                recent_turn_logs=obs.get("turn_logs", []),
                step=step,
                turn_cap=turn_cap,
            )
            manager_payload["_phase_step"] = step
            manager_payload["_phase_turn_cap"] = turn_cap
            manager_payload = _apply_recovery_phase_protocol(
                manager_payload=manager_payload,
                state=obs["review_state"],
                mode=plan["mode"],
                worker_ids=worker_ids,
                worker_limit=worker_limit,
                recent_turn_logs=obs.get("turn_logs", []),
            )
            manager_payload = _standardize_selector_style_review_issue_discovery_turn(
                manager_payload,
                obs["review_state"],
                mode=plan["mode"],
                worker_ids=worker_ids,
                worker_limit=worker_limit,
                recent_turn_logs=obs.get("turn_logs", []),
                step=step,
                turn_cap=turn_cap,
            )
            # R2: zero-real targeted retry (alters trajectory; last-resort before finalize).
            manager_payload = _maybe_zero_real_targeted_retry(
                manager_payload,
                obs["review_state"],
                step,
                turn_cap,
                worker_ids,
                worker_limit,
            )
            manager_payload["model_adapter_mode"] = obs["review_state"].get("model_adapter_mode", effective_adapter_mode)
            selected_workers = manager_payload.get("selected_agents", [])[:worker_limit]
            manager_payload["selected_agents"] = selected_workers
            manager_payload = _apply_turn_mode(manager_payload)
            if (
                _freeform_reviewer_negative_enabled()
                and manager_payload.get("targeted_negative_search_required")
                and "Evidence Agent" in selected_workers
            ):
                manager_payload["freeform_reviewer_negative_enabled"] = True
                manager_payload["freeform_reviewer_negative_mode"] = "reviewer_judgment_then_quote_v1"
            team_context = append_team_context(team_context, plan["manager"], json.dumps(manager_payload, ensure_ascii=False, sort_keys=True))

            worker_payloads = []
            trace_item = {
                "turn_id": step,
                "manager_agent": plan["manager"],
                "manager_prompt": manager_prompt,
                "manager_raw": manager_raw,
                "manager_action_type": manager_payload.get("action_type", "extract_claims"),
                "policy_source": manager_payload.get("policy_source", "manager_model"),
                "policy_notes": manager_payload.get("policy_notes", []),
                "strategy_changed": bool(previous_action and previous_action != manager_payload.get("action_type", "extract_claims")),
                "worker_calls": [],
            }
            if manager_payload.get("decision") != "finalize":
                for worker_id in selected_workers:
                    if worker_id == "Critique Agent":
                        manager_payload = _attach_review_issue_selector_snapshot(
                            manager_payload,
                            obs["review_state"],
                        )
                        manager_payload = _downgrade_empty_review_issue_discovery_turn(manager_payload)
                    worker_observation = build_worker_observation(obs, manager_payload, worker_id)
                    if obs.get("_latest_evidence_context_meta"):
                        obs.setdefault("review_state", {})["_latest_evidence_context_meta"] = dict(obs.get("_latest_evidence_context_meta") or {})
                    worker_prompt = build_prompt(
                        worker_id,
                        worker_observation,
                        team_context,
                        step,
                        manager_payload=manager_payload,
                    )
                    manager_payload.setdefault("worker_prompt_char_counts", {})[worker_id] = len(str(worker_prompt or ""))
                    worker_raw = generate_fn(worker_id, worker_prompt)
                    trace_worker = {
                        "agent_id": worker_id,
                        "prompt": worker_prompt,
                        "raw": worker_raw,
                    }
                    try:
                        worker_payload, partial_json_recovery = parse_agent_payload(worker_id, worker_raw, manager_payload=manager_payload)
                        _record_evidence_json_contract_status(
                            worker_id,
                            trace_worker,
                            manager_payload,
                            worker_raw,
                            prompt_text=worker_prompt,
                            partial_json_recovery=partial_json_recovery,
                        )
                        worker_payload = _enforce_recovery_patch_mode_payload(
                            worker_id,
                            worker_payload,
                            worker_raw,
                            manager_payload=manager_payload,
                        )
                        worker_payload = _maybe_salvage_recovery_payload(worker_id, worker_payload, obs["review_state"], manager_payload=manager_payload)
                        worker_payload = _maybe_augment_claim_payload_with_context_coverage(
                            worker_id,
                            worker_payload,
                            obs["review_state"],
                            manager_payload=manager_payload,
                            prompt_text=worker_prompt,
                        )
                        if partial_json_recovery:
                            trace_worker["partial_json_recovery"] = True
                    except Exception as exc:
                        trace_worker["parse_error"] = str(exc)
                        if _normalize_turn_mode(manager_payload.get("turn_mode")) == "recovery_patch":
                            worker_payload = None
                        else:
                            worker_payload = _fallback_worker_payload(
                                worker_id,
                                worker_raw,
                                obs["review_state"],
                                manager_payload=manager_payload,
                                prompt_text=worker_prompt,
                            )
                        fallback_payload_used = worker_payload is not None
                        _record_evidence_json_contract_status(
                            worker_id,
                            trace_worker,
                            manager_payload,
                            worker_raw,
                            prompt_text=worker_prompt,
                            parse_error=str(exc),
                            fallback_payload_used=fallback_payload_used,
                        )
                        if worker_payload is None:
                            worker_payload = _enforce_recovery_patch_mode_payload(
                                worker_id,
                                normalize_review_update_payload({}),
                                worker_raw,
                                manager_payload=manager_payload,
                                parse_error=str(exc),
                            )
                        else:
                            trace_worker["fallback_payload"] = worker_payload
                            worker_payload = _enforce_recovery_patch_mode_payload(
                                worker_id,
                                worker_payload,
                                worker_raw,
                                manager_payload=manager_payload,
                                parse_error=str(exc),
                            )
                        worker_payload = _maybe_salvage_recovery_payload(worker_id, worker_payload, obs["review_state"], manager_payload=manager_payload)
                        worker_payload = _maybe_augment_claim_payload_with_context_coverage(
                            worker_id,
                            worker_payload,
                            obs["review_state"],
                            manager_payload=manager_payload,
                            prompt_text=worker_prompt,
                        )
                    worker_payload = _maybe_seed_review_issue_discovery_payload(
                        worker_id,
                        worker_payload,
                        obs["review_state"],
                        manager_payload,
                        trace_worker=trace_worker,
                    )
                    if not worker_payload:
                        _record_evidence_empirical_observability(
                            worker_id,
                            trace_worker,
                            manager_payload,
                            worker_raw,
                            worker_payload=None,
                        )
                        trace_item["worker_calls"].append(trace_worker)
                        continue
                    if worker_id == "Evidence Agent":
                        worker_payload = _maybe_salvage_first_support_payload(
                            worker_id,
                            worker_payload,
                            obs["review_state"],
                            manager_payload,
                            trace_worker=trace_worker,
                        )
                        worker_payload = _apply_quote_first_evidence_statement_adapter(
                            worker_id,
                            worker_payload,
                            manager_payload,
                            trace_worker=trace_worker,
                        )
                        worker_payload = _apply_small_model_quote_bank_support_augmentation(
                            worker_id,
                            worker_payload,
                            obs["review_state"],
                            manager_payload,
                            trace_worker=trace_worker,
                        )
                        worker_payload = _scope_evidence_ids_for_turn(worker_payload, step)
                        worker_payload = _enforce_negative_evidence_formation_payload(worker_id, worker_payload, manager_payload, obs["review_state"])
                    _record_evidence_empirical_observability(
                        worker_id,
                        trace_worker,
                        manager_payload,
                        worker_raw,
                        worker_payload=worker_payload,
                    )
                    worker_row = {"agent_id": worker_id, "payload": worker_payload}
                    worker_row.update(_worker_payload_trace_flags(trace_worker))
                    worker_payloads.append(worker_row)
                    trace_worker["payload"] = worker_payload
                    trace_item["worker_calls"].append(trace_worker)
                    team_context = append_team_context(
                        team_context,
                        worker_id,
                        json.dumps(worker_payload, ensure_ascii=False, sort_keys=True),
                    )
                _maybe_salvage_turn_level_recovery_patch(
                    worker_payloads,
                    obs["review_state"],
                    manager_payload=manager_payload,
                    trace_item=trace_item,
                )

            manager_payload, selected_workers = _apply_finalize_policy(
                manager_payload=manager_payload,
                state=obs["review_state"],
                mode=plan["mode"],
                step=step,
                turn_cap=turn_cap,
                worker_ids=worker_ids,
                worker_limit=worker_limit,
                selected_workers=selected_workers,
                worker_payloads=worker_payloads,
                recent_turn_logs=obs.get("turn_logs", []),
            )
            manager_payload.setdefault("policy_source", "manager_model")
            manager_payload.setdefault("policy_notes", [])
            manager_payload["selected_agents"] = list(selected_workers)
            manager_payload["effective_action_type"] = _infer_effective_action_type(
                manager_payload,
                worker_payloads,
            )
            manager_payload["_phase_step"] = step
            manager_payload["_phase_turn_cap"] = turn_cap
            manager_payload = _apply_recovery_phase_protocol(
                manager_payload=manager_payload,
                state=obs["review_state"],
                mode=plan["mode"],
                worker_ids=worker_ids,
                worker_limit=worker_limit,
                recent_turn_logs=obs.get("turn_logs", []),
            )
            selected_workers = manager_payload.get("selected_agents", [])[:worker_limit]
            manager_payload["selected_agents"] = list(selected_workers)
            manager_payload = _apply_turn_mode(manager_payload)
            if _is_negative_evidence_formation_turn(manager_payload):
                filtered_worker_payloads = []
                for item in worker_payloads:
                    if not isinstance(item, dict):
                        filtered_worker_payloads.append(item)
                        continue
                    agent_id = str(item.get("agent_id") or "")
                    payload_item = item.get("payload")
                    if agent_id == "Evidence Agent" and isinstance(payload_item, dict):
                        item = dict(item)
                        item["payload"] = _enforce_negative_evidence_formation_payload(agent_id, payload_item, manager_payload, obs["review_state"])
                    filtered_worker_payloads.append(item)
                worker_payloads = filtered_worker_payloads
                for trace_worker in trace_item.get("worker_calls", []):
                    if str(trace_worker.get("agent_id") or "") != "Evidence Agent":
                        continue
                    payload_item = trace_worker.get("payload")
                    if isinstance(payload_item, dict):
                        trace_worker["payload"] = _enforce_negative_evidence_formation_payload("Evidence Agent", payload_item, manager_payload, obs["review_state"])

            _maybe_salvage_turn_level_recovery_patch(
                worker_payloads,
                obs["review_state"],
                manager_payload=manager_payload,
                trace_item=trace_item,
            )

            action = build_turn_action(
                manager_payload=manager_payload,
                worker_payloads=worker_payloads,
                mode=plan["mode"],
                turn_id=step,
            )
            obs, reward, done, info = env.step(action)
            trace_item["manager_payload"] = manager_payload
            trace_item["policy_source"] = manager_payload.get("policy_source", "manager_model")
            trace_item["policy_notes"] = manager_payload.get("policy_notes", [])
            trace_item["selected_workers"] = list(selected_workers)
            trace_item["clarification_requested"] = bool(manager_payload.get("requires_clarification", False))
            trace_item["step_done"] = done
            runner_trace.append(trace_item)

        review_state = info.get("review_state", obs.get("review_state"))
        final_report = info.get("final_report", "")
        final_decision = _resolve_result_final_decision(review_state or {}, final_report)
        if isinstance(review_state, dict):
            review_state["final_decision"] = final_decision
            if review_state.get("simulated_user_reply"):
                review_state["pending_user_question"] = ""
                review_state["clarification_needed"] = False

        # Extract diagnosis_pending_concern statistics from hygiene view
        diagnosis_pending_concerns = []
        diagnosis_pending_concern_count = 0
        if isinstance(review_state, dict):
            diagnosis_pending_concerns = review_state.get("diagnosis_pending_concerns", []) or []
            diagnosis_pending_concern_count = len(diagnosis_pending_concerns)

        return {
            "paper_id": obs["paper_id"],
            "mode": plan["mode"],
            "reward": reward,
            "done": done,
            "final_decision": final_decision,
            "final_report": final_report,
            "review_state": review_state,
            "turn_logs": info.get("review_logs", obs.get("turn_logs", [])),
            "reward_breakdown": info.get("reward_breakdown", {}),
            "decision_correct": info.get("decision_correct", 0.0),
            "accept_reject_correct": info.get("accept_reject_correct", 0.0),
            "parse_error": info.get("parse_error", ""),
            "runner_trace": runner_trace,
            "diagnosis_pending_concerns": diagnosis_pending_concerns,
            "diagnosis_pending_concern_count": diagnosis_pending_concern_count,
        }
    finally:
        env.close()


def run_review_batch(
    extras_list: Sequence[Dict[str, Any]],
    mode: str,
    generate_fn: GenerateFn,
    max_turns: Optional[int] = None,
    max_workers_per_turn: Optional[int] = None,
    log_dir: Optional[str] = None,
    model_adapter_mode: str = "auto",
) -> List[Dict[str, Any]]:
    plan = get_agent_plan(mode)
    turn_cap = int(max_turns or plan["max_turns_default"])
    worker_limit = max_workers_per_turn if max_workers_per_turn is not None else max(1, len(plan["workers"]))
    envs = [
        ReviewEnv(
            max_turns=turn_cap,
            mode=plan["mode"],
            log_dir=log_dir,
            model_adapter_mode=_normalize_model_adapter_mode((extras or {}).get("model_adapter_mode") or model_adapter_mode),
        )
        for extras in extras_list
    ]
    results: List[Optional[Dict[str, Any]]] = [None] * len(extras_list)
    task_states: List[Dict[str, Any]] = []
    try:
        for env, extras in zip(envs, extras_list):
            env.reset(extras)
            obs = env._current_obs()
            task_states.append({
                "env": env,
                "obs": obs,
                "done": False,
                "reward": 0.0,
                "info": {},
                "runner_trace": [],
            })

        while not all(task["done"] for task in task_states):
            manager_requests = []
            active_meta = []
            for idx, task in enumerate(task_states):
                if task["done"]:
                    continue
                obs = task["obs"]
                step = int(obs["review_state"]["turn_id"]) + 1
                worker_ids = list(plan["workers"])
                manager_prompt = build_prompt(
                    plan["manager"],
                    build_manager_observation(obs, worker_ids),
                    "",
                    step,
                )
                manager_requests.append((plan["manager"], manager_prompt))
                active_meta.append({
                    "index": idx,
                    "step": step,
                    "worker_ids": worker_ids,
                    "manager_prompt": manager_prompt,
                })

            manager_raws = _generate_many(generate_fn, manager_requests)

            for meta, manager_raw in zip(active_meta, manager_raws):
                idx = meta["index"]
                task = task_states[idx]
                obs = task["obs"]
                step = meta["step"]
                worker_ids = meta["worker_ids"]
                manager_prompt = meta["manager_prompt"]
                team_context = ""

                try:
                    manager_payload = normalize_agent_payload(
                        plan["manager"],
                        extract_tagged_json(manager_raw),
                        available_workers=worker_ids,
                    )
                except Exception as exc:
                    manager_payload = _default_manager_payload(str(exc))

                previous_action = ""
                if obs.get("turn_logs"):
                    previous_action = obs["turn_logs"][-1].get("action_type", "")
                # Mainline-Final-Integrated P0-2 budget-aware refinement: see
                # the matching block in the non-batched call path above.
                manager_payload["_phase_step"] = step
                manager_payload["_phase_turn_cap"] = turn_cap
                manager_payload = _apply_manager_policy_fallback(
                    manager_payload=manager_payload,
                    state=obs["review_state"],
                    mode=plan["mode"],
                    worker_ids=worker_ids,
                    worker_limit=worker_limit,
                    recent_turn_logs=obs.get("turn_logs", []),
                )
                manager_payload = _maybe_upgrade_visible_review_issue_discovery_turn(
                    manager_payload,
                    obs["review_state"],
                    mode=plan["mode"],
                    worker_ids=worker_ids,
                    worker_limit=worker_limit,
                    recent_turn_logs=obs.get("turn_logs", []),
                    step=step,
                    turn_cap=turn_cap,
                )
                manager_payload["_phase_step"] = step
                manager_payload["_phase_turn_cap"] = turn_cap
                manager_payload = _apply_recovery_phase_protocol(
                    manager_payload=manager_payload,
                    state=obs["review_state"],
                    mode=plan["mode"],
                    worker_ids=worker_ids,
                    worker_limit=worker_limit,
                    recent_turn_logs=obs.get("turn_logs", []),
                )
                manager_payload = _standardize_selector_style_review_issue_discovery_turn(
                    manager_payload,
                    obs["review_state"],
                    mode=plan["mode"],
                    worker_ids=worker_ids,
                    worker_limit=worker_limit,
                    recent_turn_logs=obs.get("turn_logs", []),
                    step=step,
                    turn_cap=turn_cap,
                )
                selected_workers = manager_payload.get("selected_agents", [])[:worker_limit]
                manager_payload["selected_agents"] = selected_workers
                manager_payload["model_adapter_mode"] = obs["review_state"].get("model_adapter_mode", model_adapter_mode)
                manager_payload = _apply_turn_mode(manager_payload)
                team_context = append_team_context(team_context, plan["manager"], json.dumps(manager_payload, ensure_ascii=False, sort_keys=True))

                trace_item = {
                    "turn_id": step,
                    "manager_agent": plan["manager"],
                    "manager_prompt": manager_prompt,
                    "manager_raw": manager_raw,
                    "manager_action_type": manager_payload.get("action_type", "extract_claims"),
                    "policy_source": manager_payload.get("policy_source", "manager_model"),
                    "policy_notes": manager_payload.get("policy_notes", []),
                    "strategy_changed": bool(previous_action and previous_action != manager_payload.get("action_type", "extract_claims")),
                    "worker_calls": [],
                }

                task["_batch_step"] = step
                task["_manager_payload"] = manager_payload
                task["_selected_workers"] = list(selected_workers)
                task["_team_context"] = team_context
                task["_worker_payloads"] = []
                task["_trace_item"] = trace_item

            for worker_pos in range(worker_limit):
                grouped_calls: Dict[str, List[Dict[str, Any]]] = {}
                for task in task_states:
                    if task["done"]:
                        continue
                    manager_payload = task.get("_manager_payload")
                    if not manager_payload or manager_payload.get("decision") == "finalize":
                        continue
                    selected_workers = task.get("_selected_workers", [])
                    if worker_pos >= len(selected_workers):
                        continue
                    worker_id = selected_workers[worker_pos]
                    obs = task["obs"]
                    step = task["_batch_step"]
                    if worker_id == "Critique Agent":
                        manager_payload = _attach_review_issue_selector_snapshot(
                            manager_payload,
                            obs["review_state"],
                        )
                        manager_payload = _downgrade_empty_review_issue_discovery_turn(manager_payload)
                        task["_manager_payload"] = manager_payload
                    worker_observation = build_worker_observation(obs, manager_payload, worker_id)
                    if obs.get("_latest_evidence_context_meta"):
                        obs.setdefault("review_state", {})["_latest_evidence_context_meta"] = dict(obs.get("_latest_evidence_context_meta") or {})
                    worker_prompt = build_prompt(
                        worker_id,
                        worker_observation,
                        task.get("_team_context", ""),
                        step,
                        manager_payload=manager_payload,
                    )
                    manager_payload.setdefault("worker_prompt_char_counts", {})[worker_id] = len(str(worker_prompt or ""))
                    grouped_calls.setdefault(worker_id, []).append({
                        "task": task,
                        "agent_id": worker_id,
                        "prompt": worker_prompt,
                    })

                for worker_id, items in grouped_calls.items():
                    worker_raws = _generate_many(generate_fn, [(worker_id, item["prompt"]) for item in items])
                    for item, worker_raw in zip(items, worker_raws):
                        task = item["task"]
                        manager_payload = task["_manager_payload"]
                        trace_worker = {
                            "agent_id": worker_id,
                            "prompt": item["prompt"],
                            "raw": worker_raw,
                        }
                        try:
                            worker_payload, partial_json_recovery = parse_agent_payload(worker_id, worker_raw, manager_payload=manager_payload)
                            _record_evidence_json_contract_status(
                                worker_id,
                                trace_worker,
                                manager_payload,
                                worker_raw,
                                prompt_text=item["prompt"],
                                partial_json_recovery=partial_json_recovery,
                            )
                            worker_payload = _enforce_recovery_patch_mode_payload(
                                worker_id,
                                worker_payload,
                                worker_raw,
                                manager_payload=manager_payload,
                            )
                            worker_payload = _maybe_salvage_recovery_payload(worker_id, worker_payload, task["obs"]["review_state"], manager_payload=manager_payload)
                            worker_payload = _maybe_augment_claim_payload_with_context_coverage(
                                worker_id,
                                worker_payload,
                                task["obs"]["review_state"],
                                manager_payload=manager_payload,
                                prompt_text=item["prompt"],
                            )
                            if partial_json_recovery:
                                trace_worker["partial_json_recovery"] = True
                        except Exception as exc:
                            trace_worker["parse_error"] = str(exc)
                            if _normalize_turn_mode(manager_payload.get("turn_mode")) == "recovery_patch":
                                worker_payload = None
                            else:
                                worker_payload = _fallback_worker_payload(
                                    worker_id,
                                    worker_raw,
                                    task["obs"]["review_state"],
                                    manager_payload=manager_payload,
                                    prompt_text=item["prompt"],
                                )
                            fallback_payload_used = worker_payload is not None
                            _record_evidence_json_contract_status(
                                worker_id,
                                trace_worker,
                                manager_payload,
                                worker_raw,
                                prompt_text=item["prompt"],
                                parse_error=str(exc),
                                fallback_payload_used=fallback_payload_used,
                            )
                            if worker_payload is None:
                                worker_payload = _enforce_recovery_patch_mode_payload(
                                    worker_id,
                                    normalize_review_update_payload({}),
                                    worker_raw,
                                    manager_payload=manager_payload,
                                    parse_error=str(exc),
                                )
                            else:
                                trace_worker["fallback_payload"] = worker_payload
                                worker_payload = _enforce_recovery_patch_mode_payload(
                                    worker_id,
                                    worker_payload,
                                    worker_raw,
                                    manager_payload=manager_payload,
                                    parse_error=str(exc),
                                )
                            worker_payload = _maybe_salvage_recovery_payload(worker_id, worker_payload, task["obs"]["review_state"], manager_payload=manager_payload)
                            worker_payload = _maybe_augment_claim_payload_with_context_coverage(
                                worker_id,
                                worker_payload,
                                task["obs"]["review_state"],
                                manager_payload=manager_payload,
                                prompt_text=item["prompt"],
                            )
                        worker_payload = _maybe_seed_review_issue_discovery_payload(
                            worker_id,
                            worker_payload,
                            task["obs"]["review_state"],
                            manager_payload,
                            trace_worker=trace_worker,
                        )
                        if not worker_payload:
                            _record_evidence_empirical_observability(
                                worker_id,
                                trace_worker,
                                manager_payload,
                                worker_raw,
                                worker_payload=None,
                            )
                            task["_trace_item"]["worker_calls"].append(trace_worker)
                            continue
                        if worker_id == "Evidence Agent":
                            worker_payload = _maybe_salvage_first_support_payload(
                                worker_id,
                                worker_payload,
                                task["obs"]["review_state"],
                                manager_payload,
                                trace_worker=trace_worker,
                            )
                            worker_payload = _apply_quote_first_evidence_statement_adapter(
                                worker_id,
                                worker_payload,
                                manager_payload,
                                trace_worker=trace_worker,
                            )
                            worker_payload = _apply_small_model_quote_bank_support_augmentation(
                                worker_id,
                                worker_payload,
                                task["obs"]["review_state"],
                                manager_payload,
                                trace_worker=trace_worker,
                            )
                            worker_payload = _scope_evidence_ids_for_turn(worker_payload, task.get("_batch_step", 0))
                            worker_payload = _enforce_negative_evidence_formation_payload(
                                worker_id,
                                worker_payload,
                                manager_payload,
                                task["obs"]["review_state"],
                            )
                        _record_evidence_empirical_observability(
                            worker_id,
                            trace_worker,
                            manager_payload,
                            worker_raw,
                            worker_payload=worker_payload,
                        )
                        worker_row = {"agent_id": worker_id, "payload": worker_payload}
                        worker_row.update(_worker_payload_trace_flags(trace_worker))
                        task["_worker_payloads"].append(worker_row)
                        trace_worker["payload"] = worker_payload
                        task["_trace_item"]["worker_calls"].append(trace_worker)
                        task["_team_context"] = append_team_context(
                            task.get("_team_context", ""),
                            worker_id,
                            json.dumps(worker_payload, ensure_ascii=False, sort_keys=True),
                        )

                for task in task_states:
                    if task["done"] or "_manager_payload" not in task:
                        continue
                    _maybe_salvage_turn_level_recovery_patch(
                        task["_worker_payloads"],
                        task["obs"]["review_state"],
                        manager_payload=task["_manager_payload"],
                        trace_item=task["_trace_item"],
                    )

            for task in task_states:
                if task["done"] or "_manager_payload" not in task:
                    continue
                obs = task["obs"]
                step = task["_batch_step"]
                worker_ids = list(plan["workers"])
                manager_payload = task["_manager_payload"]
                selected_workers = task.get("_selected_workers", [])
                worker_payloads = task.get("_worker_payloads", [])
                trace_item = task["_trace_item"]

                manager_payload, selected_workers = _apply_finalize_policy(
                    manager_payload=manager_payload,
                    state=obs["review_state"],
                    mode=plan["mode"],
                    step=step,
                    turn_cap=turn_cap,
                    worker_ids=worker_ids,
                    worker_limit=worker_limit,
                    selected_workers=selected_workers,
                    worker_payloads=worker_payloads,
                    recent_turn_logs=obs.get("turn_logs", []),
                )
                manager_payload.setdefault("policy_source", "manager_model")
                manager_payload.setdefault("policy_notes", [])
                manager_payload["selected_agents"] = list(selected_workers)
                manager_payload["effective_action_type"] = _infer_effective_action_type(
                    manager_payload,
                    worker_payloads,
                )
                manager_payload["_phase_step"] = step
                manager_payload["_phase_turn_cap"] = turn_cap
                manager_payload = _apply_recovery_phase_protocol(
                    manager_payload=manager_payload,
                    state=obs["review_state"],
                    mode=plan["mode"],
                    worker_ids=worker_ids,
                    worker_limit=worker_limit,
                    recent_turn_logs=obs.get("turn_logs", []),
                )
                selected_workers = manager_payload.get("selected_agents", [])[:worker_limit]
                manager_payload["selected_agents"] = list(selected_workers)
                manager_payload = _apply_turn_mode(manager_payload)
                _maybe_salvage_turn_level_recovery_patch(
                    worker_payloads,
                    obs["review_state"],
                    manager_payload=manager_payload,
                    trace_item=trace_item,
                )

                action = build_turn_action(
                    manager_payload=manager_payload,
                    worker_payloads=worker_payloads,
                    mode=plan["mode"],
                    turn_id=step,
                )
                next_obs, reward, done, info = task["env"].step(action)
                trace_item["manager_payload"] = manager_payload
                trace_item["policy_source"] = manager_payload.get("policy_source", "manager_model")
                trace_item["policy_notes"] = manager_payload.get("policy_notes", [])
                trace_item["selected_workers"] = list(selected_workers)
                trace_item["clarification_requested"] = bool(manager_payload.get("requires_clarification", False))
                trace_item["step_done"] = done
                task["runner_trace"].append(trace_item)
                task["obs"] = next_obs
                task["reward"] = reward
                task["done"] = done
                task["info"] = info
                task.pop("_batch_step", None)
                task.pop("_manager_payload", None)
                task.pop("_selected_workers", None)
                task.pop("_team_context", None)
                task.pop("_worker_payloads", None)
                task.pop("_trace_item", None)

        for idx, task in enumerate(task_states):
            obs = task["obs"]
            info = task["info"]
            review_state = info.get("review_state", obs.get("review_state"))
            final_report = info.get("final_report", "")
            final_decision = _resolve_result_final_decision(review_state or {}, final_report)
            if isinstance(review_state, dict):
                review_state["final_decision"] = final_decision
                if review_state.get("simulated_user_reply"):
                    review_state["pending_user_question"] = ""
                    review_state["clarification_needed"] = False

            # Extract diagnosis_pending_concern statistics
            diagnosis_pending_concerns = []
            diagnosis_pending_concern_count = 0
            if isinstance(review_state, dict):
                diagnosis_pending_concerns = review_state.get("diagnosis_pending_concerns", []) or []
                diagnosis_pending_concern_count = len(diagnosis_pending_concerns)

            results[idx] = {
                "paper_id": obs["paper_id"],
                "mode": plan["mode"],
                "reward": task["reward"],
                "done": task["done"],
                "final_decision": final_decision,
                "final_report": final_report,
                "review_state": review_state,
                "turn_logs": info.get("review_logs", obs.get("turn_logs", [])),
                "reward_breakdown": info.get("reward_breakdown", {}),
                "decision_correct": info.get("decision_correct", 0.0),
                "accept_reject_correct": info.get("accept_reject_correct", 0.0),
                "parse_error": info.get("parse_error", ""),
                "runner_trace": task["runner_trace"],
                "diagnosis_pending_concerns": diagnosis_pending_concerns,
                "diagnosis_pending_concern_count": diagnosis_pending_concern_count,
            }
    finally:
        for env in envs:
            env.close()
    return [item for item in results if item is not None]


class VllmReviewGenerator:
    def __init__(
        self,
        model_path: str,
        tensor_parallel_size: int = 1,
        gpu_memory_utilization: float = 0.55,
        max_model_len: int = 3072,
        temperature: float = 0.2,
        top_p: float = 0.95,
        max_tokens: int = 640,
        trust_remote_code: bool = True,
        enforce_eager: bool = False,
        max_num_seqs: int = 128,
        seed: Optional[int] = None,
        use_chat_template: bool = False,
    ):
        from vllm import LLM, SamplingParams

        self.use_chat_template = bool(use_chat_template)
        self.max_model_len = int(max_model_len)
        self.max_tokens = int(max_tokens)
        self.tokenizer = None
        self.llm = LLM(
            model=model_path,
            tensor_parallel_size=tensor_parallel_size,
            gpu_memory_utilization=gpu_memory_utilization,
            max_model_len=max_model_len,
            trust_remote_code=trust_remote_code,
            enforce_eager=enforce_eager,
            max_num_seqs=max_num_seqs,
        )
        sampling_kwargs = {
            "temperature": temperature,
            "top_p": top_p,
            "max_tokens": max_tokens,
        }
        if seed is not None:
            sampling_kwargs["seed"] = int(seed)
        try:
            self.sampling_params = SamplingParams(**sampling_kwargs)
        except TypeError:
            # Older vLLM builds may not expose SamplingParams.seed; keep runtime compatible.
            sampling_kwargs.pop("seed", None)
            self.sampling_params = SamplingParams(**sampling_kwargs)
        if self.use_chat_template:
            try:
                self.tokenizer = self.llm.get_tokenizer()
            except Exception:
                self.tokenizer = None

    def _prompt_token_ids(self, prompt: str) -> List[int]:
        if self.tokenizer is None:
            return []
        try:
            return list(self.tokenizer.encode(prompt, add_special_tokens=False))
        except TypeError:
            return list(self.tokenizer.encode(prompt))

    def _decode_prompt_tokens(self, tokens: Sequence[int]) -> str:
        if self.tokenizer is None:
            return ""
        return str(self.tokenizer.decode(list(tokens), skip_special_tokens=False))

    def _truncate_prompt_for_context(self, prompt: str, budget: Optional[int] = None) -> str:
        budget = int(budget or max(512, self.max_model_len - max(128, self.max_tokens) - 64))
        if self.tokenizer is None:
            return _clip_text(prompt, max(2400, budget * 2))
        tokens = self._prompt_token_ids(prompt)
        if len(tokens) <= budget:
            return prompt
        truncated = self._decode_prompt_tokens(tokens[:budget])
        return str(truncated).rstrip() + "\n...[prompt truncated to fit model context]"

    def _apply_chat_template(self, prompt: str) -> str:
        messages = [{"role": "user", "content": prompt}]
        try:
            return self.tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True,
                enable_thinking=False,
            )
        except TypeError:
            return self.tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True,
            )

    def _format_prompt(self, prompt: str) -> str:
        prompt_budget = max(512, self.max_model_len - max(128, self.max_tokens) - 128)
        if not self.use_chat_template or self.tokenizer is None:
            return self._truncate_prompt_for_context(prompt, budget=prompt_budget)

        raw_prompt = self._truncate_prompt_for_context(prompt, budget=prompt_budget)
        formatted_budget = max(512, self.max_model_len - max(128, self.max_tokens) - 32)
        for _ in range(3):
            formatted = str(self._apply_chat_template(raw_prompt))
            formatted_tokens = self._prompt_token_ids(formatted)
            if len(formatted_tokens) <= formatted_budget:
                return formatted
            raw_tokens = self._prompt_token_ids(raw_prompt)
            overflow = len(formatted_tokens) - formatted_budget
            next_budget = max(256, len(raw_tokens) - overflow - 64)
            raw_prompt = self._truncate_prompt_for_context(raw_prompt, budget=next_budget)

        formatted = str(self._apply_chat_template(raw_prompt))
        formatted_tokens = self._prompt_token_ids(formatted)
        if len(formatted_tokens) <= formatted_budget:
            return formatted
        return self._decode_prompt_tokens(formatted_tokens[:formatted_budget])

    def __call__(self, agent_id: str, prompt: str) -> str:
        outputs = self.llm.generate([self._format_prompt(prompt)], sampling_params=self.sampling_params)
        if not outputs or not outputs[0].outputs:
            raise RuntimeError(f"No generation returned for agent {agent_id}.")
        return outputs[0].outputs[0].text

    def generate_many(self, requests: Sequence[tuple[str, str]]) -> List[str]:
        prompts = [self._format_prompt(prompt) for _, prompt in requests]
        outputs = self.llm.generate(prompts, sampling_params=self.sampling_params)
        texts: List[str] = []
        for (agent_id, _), output in zip(requests, outputs):
            if not output.outputs:
                raise RuntimeError(f"No generation returned for agent {agent_id}.")
            texts.append(output.outputs[0].text)
        return texts


class ApiReviewGenerator:
    """Cloud API-based review generator using OpenAI-compatible endpoints.

    Supports DeepSeek, OpenAI, Qwen-Max, and any OpenAI-compatible API.
    Drop-in replacement for VllmReviewGenerator — same __call__ and generate_many
    interface.
    """

    def __init__(
        self,
        model: str = "deepseek-chat",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        temperature: float = 0.2,
        top_p: float = 0.95,
        max_tokens: int = 640,
        max_workers: int = 8,
        timeout: int = 120,
        max_retries: int = 6,
        retry_delay: float = 2.0,
        provider: str = "auto",
        system_prompt: Optional[str] = None,
    ):
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError(
                "openai package is required for API backend. "
                "Install with: pip install openai"
            )

        self.model = model
        self.temperature = temperature
        self.top_p = top_p
        self.max_tokens = max_tokens
        self.max_workers = max_workers
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.provider = str(provider or "auto").strip().lower()

        # JSON output reliability: small models (e.g. MiMo) tend to emit chain-of-thought
        # prose instead of the JSON contract, so the Evidence/Critique payloads fail to parse
        # (~90% fallback). When the provider supports it, response_format=json_object
        # grammar-constrains the completion to a valid JSON object from the first token, which
        # removes the "reasoning prose instead of JSON" failure mode. Mode "auto" probes once and
        # disables itself for the session if the provider rejects the parameter; "on" forces it,
        # "off" disables it. Env override: DRMAS_JSON_RESPONSE_FORMAT.
        self._json_response_format_mode = os.environ.get("DRMAS_JSON_RESPONSE_FORMAT", "auto").strip().lower()

        resolved_key = api_key or os.environ.get("MIMO_API_KEY") or os.environ.get("DEEPSEEK_API_KEY") or os.environ.get("OPENAI_API_KEY", "")
        resolved_url = (
            base_url
            or os.environ.get("MIMO_BASE_URL")
            or os.environ.get("DEEPSEEK_BASE_URL")
            or os.environ.get("OPENAI_BASE_URL")
            or "https://api.deepseek.com"
        )
        if self.provider == "auto":
            low = " ".join([str(model or ""), str(resolved_url or "")]).lower()
            if "xiaomimimo" in low or "mimo" in low:
                self.provider = "mimo"
            elif "deepseek" in low:
                self.provider = "deepseek"
            else:
                self.provider = "openai_compatible"

        if system_prompt is None and self.provider == "mimo":
            system_prompt = (
                "You are MiMo, an AI assistant developed by Xiaomi. "
                "Follow the user's structured output contract exactly. "
                "Output only the requested tagged JSON block; do not explain, "
                "do not use markdown fences, and do not include prose outside the tags."
            )
        self.system_prompt = str(system_prompt or "").strip()

        default_headers = {"api-key": resolved_key} if self.provider == "mimo" and resolved_key else None

        self.client = OpenAI(
            api_key=resolved_key,
            base_url=resolved_url,
            timeout=float(timeout),
            max_retries=0,  # we handle retries ourselves
            default_headers=default_headers,
        )
        print(f"[API] Initialized: model={model}, provider={self.provider}, base_url={resolved_url}, max_tokens={max_tokens}")

    def _messages(self, prompt: str) -> List[Dict[str, str]]:
        if self.system_prompt:
            return [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt},
            ]
        return [{"role": "user", "content": prompt}]

    def _completion_kwargs(self, prompt: str) -> Dict[str, Any]:
        kwargs: Dict[str, Any] = {
            "model": self.model,
            "messages": self._messages(prompt),
            "temperature": self.temperature,
            "top_p": self.top_p,
        }
        # Xiaomi MiMo's OpenAI-compatible docs use max_completion_tokens.
        # Other providers in this project have been tested with max_tokens.
        if self.provider == "mimo":
            kwargs["max_completion_tokens"] = self.max_tokens
            kwargs["extra_body"] = {"enable_thinking": False}
        else:
            kwargs["max_tokens"] = self.max_tokens
        if self._json_response_format_mode in {"auto", "on"}:
            # Force a valid JSON object (see __init__). The downstream parser accepts a bare
            # JSON object as well as the legacy <json>...</json> form, so this is compatible
            # with the existing prompts.
            kwargs["response_format"] = {"type": "json_object"}
        return kwargs

    @staticmethod
    def _content_to_text(content: Any) -> str:
        if content is None:
            return ""
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts: List[str] = []
            for item in content:
                if isinstance(item, str):
                    parts.append(item)
                elif isinstance(item, dict):
                    parts.append(str(item.get("text") or item.get("content") or item.get("output_text") or ""))
                else:
                    text_value = getattr(item, "text", None) or getattr(item, "content", None)
                    if text_value:
                        parts.append(str(text_value))
            return "\n".join(part for part in parts if part)
        return str(content)

    @classmethod
    def _message_to_text(cls, message: Any) -> str:
        for attr in ("content", "reasoning_content", "reasoning", "output_text", "text"):
            text = cls._content_to_text(getattr(message, attr, None))
            if text.strip():
                return text
        dump: Dict[str, Any] = {}
        if hasattr(message, "model_dump"):
            try:
                dump = message.model_dump()
            except Exception:
                dump = {}
        elif isinstance(message, dict):
            dump = message
        for key in ("content", "reasoning_content", "reasoning", "output_text", "text"):
            text = cls._content_to_text(dump.get(key))
            if text.strip():
                return text
        return ""

    @staticmethod
    def _looks_like_response_format_rejection(exc: Exception) -> bool:
        text = str(exc or "").lower()
        status_code = getattr(exc, "status_code", None) or getattr(exc, "status", None)
        if "response_format" not in text:
            return False
        if status_code in {400, 422}:
            return True
        return bool(
            re.search(
                r"\b(?:unsupported|invalid|unrecognized|unknown|not supported|extra_forbidden|"
                r"not permitted|bad request)\b",
                text,
            )
        )

    @staticmethod
    def _is_non_retryable_api_error(exc: Exception) -> bool:
        text = str(exc or "").lower()
        status_code = getattr(exc, "status_code", None) or getattr(exc, "status", None)
        if status_code in {401, 402, 403}:
            return True
        return bool(
            re.search(
                r"\b(?:insufficient[_ -]?balance|quota[_ -]?exceeded|billing|payment|required|"
                r"invalid[_ -]?api[_ -]?key|authentication|unauthorized|forbidden|permission denied)\b",
                text,
            )
        )

    def _call_api_once(self, prompt: str) -> str:
        kwargs = self._completion_kwargs(prompt)
        try:
            response = self.client.chat.completions.create(**kwargs)
        except Exception as exc:
            # Probe-and-fallback: if the provider rejects response_format, disable it for the
            # rest of the session and retry once without it. Other (transient) errors are
            # re-raised so the _call_api retry loop handles them normally.
            if (
                "response_format" in kwargs
                and self._json_response_format_mode == "auto"
                and self._looks_like_response_format_rejection(exc)
            ):
                self._json_response_format_mode = "off"
                kwargs.pop("response_format", None)
                print(
                    f"[{_timestamp()}] [API] response_format=json_object rejected; "
                    f"disabling for session ({str(exc)[:120]})",
                    flush=True,
                )
                response = self.client.chat.completions.create(**kwargs)
            else:
                raise
        message = response.choices[0].message
        return self._message_to_text(message)

    def _call_api(self, agent_id: str, prompt: str) -> str:
        """Call the API with retry logic."""
        last_error = None
        for attempt in range(self.max_retries):
            started = time.monotonic()
            print(
                f"[{_timestamp()}] [API] request start agent={agent_id} "
                f"attempt={attempt + 1}/{self.max_retries} prompt_chars={len(str(prompt or ''))}",
                flush=True,
            )
            try:
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                    future = pool.submit(self._call_api_once, prompt)
                    text = future.result(timeout=float(self.timeout) + 5.0)
                elapsed = time.monotonic() - started
                print(
                    f"[{_timestamp()}] [API] request success agent={agent_id} "
                    f"attempt={attempt + 1}/{self.max_retries} elapsed={elapsed:.1f}s raw_chars={len(str(text or ''))}",
                    flush=True,
                )
                return text
            except concurrent.futures.TimeoutError as e:
                elapsed = time.monotonic() - started
                last_error = TimeoutError(f"API request exceeded outer timeout after {elapsed:.1f}s")
                print(
                    f"[{_timestamp()}] [API] request timeout agent={agent_id} "
                    f"attempt={attempt + 1}/{self.max_retries} elapsed={elapsed:.1f}s",
                    flush=True,
                )
            except Exception as e:
                elapsed = time.monotonic() - started
                last_error = e
                print(
                    f"[{_timestamp()}] [API] request error agent={agent_id} "
                    f"attempt={attempt + 1}/{self.max_retries} elapsed={elapsed:.1f}s error={e}",
                    flush=True,
                )
                if self._is_non_retryable_api_error(e):
                    print(
                        f"[{_timestamp()}] [API] non-retryable error agent={agent_id}; "
                        f"aborting retries after attempt={attempt + 1}/{self.max_retries}",
                        flush=True,
                    )
                    raise RuntimeError(f"Non-retryable API error for {agent_id}: {e}") from e
            if attempt < self.max_retries - 1:
                wait = min(self.retry_delay * (2 ** attempt), 30.0)
                print(
                    f"[{_timestamp()}] [API] retry wait agent={agent_id} "
                    f"next_attempt={attempt + 2}/{self.max_retries} wait={wait:.1f}s",
                    flush=True,
                )
                time.sleep(wait)
        raise RuntimeError(f"API call failed after {self.max_retries} retries for {agent_id}: {last_error}")

    def __call__(self, agent_id: str, prompt: str) -> str:
        return self._call_api(agent_id, prompt)

    def generate_many(self, requests: Sequence[tuple[str, str]]) -> List[str]:
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=self.max_workers) as pool:
            futures = [pool.submit(self._call_api, agent_id, prompt) for agent_id, prompt in requests]
            return [f.result() for f in futures]


def _parse_jsonish_field(value: Any) -> Any:
    if isinstance(value, str):
        stripped = value.strip()
        if stripped.startswith("{") or stripped.startswith("["):
            try:
                return json.loads(stripped)
            except json.JSONDecodeError:
                return value
    return value


def _infer_model_adapter_mode(requested: str, model_name: Optional[str]) -> str:
    mode = _normalize_model_adapter_mode(requested)
    if mode != "auto":
        return mode
    name = str(model_name or "").lower()
    if any(token in name for token in ("deepseek", "gpt", "claude", "qwen-max", "qwen-plus", "qwen-turbo")):
        return "large_model"
    if any(token in name for token in ("mimo", "mini", "7b", "8b", "9b", "14b", "small")):
        return "small_model"
    return "auto"


def _row_to_env_kwargs(row: Dict[str, Any]) -> Dict[str, Any]:
    env_kwargs = _parse_jsonish_field(row.get("env_kwargs"))
    if not isinstance(env_kwargs, dict):
        env_kwargs = {}

    extra_info = _parse_jsonish_field(row.get("extra_info"))
    reward_model = _parse_jsonish_field(row.get("reward_model"))
    prompt = _parse_jsonish_field(row.get("prompt"))

    # Priority: env_kwargs.paper_text > row.paper_text > row.inputs > row.question
    # Note: 'inputs' usually contains a JSON list of messages in this dataset.
    inputs_val = row.get("inputs")
    paper_text = env_kwargs.get("paper_text") or row.get("paper_text") or (inputs_val if isinstance(inputs_val, str) and not inputs_val.strip().startswith("[") else "") or row.get("question") or ""

    if not paper_text:
        # Try to extract from 'prompt' list or 'inputs' if we can JSON parse it
        msg_list = prompt
        if not isinstance(msg_list, list) and isinstance(inputs_val, str) and inputs_val.strip().startswith("["):
            try:
                msg_list = json.loads(inputs_val)
            except:
                msg_list = None

        if isinstance(msg_list, list):
            for item in msg_list:
                if isinstance(item, dict) and item.get("role") == "user":
                    paper_text = item.get("content", "")
                    # If it's very long, it's likely the paper
                    if len(paper_text) > 1000:
                        break

    print(f"[DEBUG] paper_id: {env_kwargs.get('paper_id') or row.get('id')}, paper_text length: {len(paper_text)}")
    if paper_text:
        snippet = paper_text[:100].replace('\n', ' ')
        print(f"[DEBUG] paper_text snippet: {snippet}...")

    return {
        "paper_id": env_kwargs.get("paper_id") or row.get("paper_id") or row.get("id") or (extra_info or {}).get("id") or "unknown-paper",
        "paper_text": paper_text,
        "question": paper_text,
        "user_goal": row.get("user_goal")
        or "Review the paper, track claims and supporting evidence, surface major flaws, and end with an accept or reject recommendation.",
        "data_source": row.get("data_source") or "unknown",
        "ground_truth_decision": row.get("ground_truth_decision") or (reward_model or {}).get("decision") or "",
        "reference_review": row.get("reference_review") or (extra_info or {}).get("reference_review") or "",
        "reference_ratings": row.get("reference_ratings") or (reward_model or {}).get("rating"),
        "reviewer_comments": row.get("reviewer_comments") or "",
        "model_adapter_mode": env_kwargs.get("model_adapter_mode") or row.get("model_adapter_mode") or "auto",
    }


def load_review_rows(dataset_path: str, limit: Optional[int] = None, split: Optional[str] = None) -> List[Dict[str, Any]]:
    path = Path(dataset_path)
    if path.is_dir():
        split_name = split or "test"
        path = path / f"{split_name}.parquet"

    rows: List[Dict[str, Any]] = []
    try:
        import pandas as pd

        frame = pd.read_parquet(path)
        rows = frame.to_dict(orient="records")
    except Exception:
        import pyarrow.parquet as pq

        table = pq.read_table(path)
        rows = table.to_pylist()

    if limit is not None:
        rows = rows[:limit]
    return rows


def save_results(output_path: str, results: List[Dict[str, Any]]) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for item in results:
            handle.write(json.dumps(item, ensure_ascii=False) + "\n")


def _truncate_output(output_path: str) -> None:
    """Reset the output file so incremental appends start fresh."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("", encoding="utf-8")


def _append_result(output_path: str, result: Dict[str, Any]) -> None:
    """Append a single result as one JSONL line, flushing immediately so a
    crashed/killed process still leaves partial output on disk."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(result, ensure_ascii=False) + "\n"
    with path.open("a", encoding="utf-8") as handle:
        handle.write(line)
        handle.flush()
        try:
            os.fsync(handle.fileno())
        except OSError:
            pass


def _resolve_use_chat_template(model_path: str, requested: Optional[bool]) -> bool:
    if requested is not None:
        return bool(requested)
    return "qwen3" in str(model_path or "").lower()


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run multi-turn review inference without verl.")
    parser.add_argument("--backend", default="vllm", choices=["vllm", "api"], help="Inference backend: 'vllm' for local GPU, 'api' for cloud API (DeepSeek/OpenAI/etc).")
    parser.add_argument("--model-path", default=None, help="Local model path for vLLM backend.")
    parser.add_argument("--dataset-path", required=True, help="Parquet file or directory containing train/test parquet files.")
    parser.add_argument("--split", default="test")
    parser.add_argument("--mode", default="s4", choices=["s1", "s2", "s3", "s4"])
    parser.add_argument("--max-turns", type=int, default=None)
    parser.add_argument("--max-workers-per-turn", type=int, default=None)
    parser.add_argument("--manager-batch-size", type=int, default=1)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--output-path", default="outputs/review_infer/results.jsonl")
    parser.add_argument("--log-dir", default=None)
    parser.add_argument(
        "--model-adapter-mode",
        default="auto",
        choices=["auto", "small_model", "large_model", "off"],
        help=(
            "Evidence adapter mode. small_model enables quote-first evidence rewrites for models "
            "that paraphrase evidence; large_model/off disables rewrites; auto infers from model name."
        ),
    )
    # vLLM-specific arguments
    parser.add_argument("--tensor-parallel-size", type=int, default=1)
    parser.add_argument("--gpu-memory-utilization", type=float, default=0.55)
    parser.add_argument("--max-model-len", type=int, default=3072)
    parser.add_argument("--max-num-seqs", type=int, default=128)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--trust-remote-code", action="store_true", default=True)
    parser.add_argument("--no-trust-remote-code", dest="trust_remote_code", action="store_false")
    parser.add_argument("--enforce-eager", action="store_true", default=False)
    parser.add_argument("--no-enforce-eager", dest="enforce_eager", action="store_false")
    parser.add_argument("--use-chat-template", dest="use_chat_template", action="store_true", default=None, help="Wrap each prompt with the model tokenizer chat template before generation.")
    parser.add_argument("--no-use-chat-template", dest="use_chat_template", action="store_false", help="Disable tokenizer chat-template wrapping even when it would be selected by default.")
    # Shared sampling arguments
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--top-p", type=float, default=0.95)
    parser.add_argument("--max-tokens", type=int, default=None)
    # API backend arguments
    parser.add_argument("--api-model", default=None, help="Model name for API backend (e.g. deepseek-chat, gpt-4o, qwen-max). Defaults to 'deepseek-chat'.")
    parser.add_argument("--api-key", default=None, help="API key. Falls back to DEEPSEEK_API_KEY or OPENAI_API_KEY env var.")
    parser.add_argument("--api-base-url", default=None, help="API base URL. Falls back to DEEPSEEK_BASE_URL or OPENAI_BASE_URL env var. Default: https://api.deepseek.com")
    parser.add_argument("--api-provider", default="auto", choices=["auto", "mimo", "deepseek", "openai_compatible"], help="Provider-specific API compatibility mode.")
    parser.add_argument("--api-system-prompt", default=None, help="Optional system message for API backends. MiMo gets a provider default when omitted.")
    parser.add_argument("--api-max-workers", type=int, default=8, help="Max concurrent API calls for batch generation.")
    parser.add_argument("--api-timeout", type=int, default=120, help="API request timeout in seconds.")
    parser.add_argument("--api-max-retries", type=int, default=6, help="Max retries per API request.")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_arg_parser().parse_args(argv)
    rows = load_review_rows(args.dataset_path, limit=args.limit, split=args.split)
    mode_token_defaults = {"s1": 512, "s2": 512, "s3": 640, "s4": 640}
    selected_max_tokens = args.max_tokens if args.max_tokens is not None else mode_token_defaults.get(args.mode, 640)

    model_name_for_adapter = args.api_model if args.backend == "api" else args.model_path
    effective_model_adapter_mode = _infer_model_adapter_mode(args.model_adapter_mode, model_name_for_adapter)

    if args.backend == "api":
        api_model = args.api_model or "deepseek-chat"
        # API backend: higher max_tokens since cloud models have larger output limits
        api_max_tokens = selected_max_tokens if args.max_tokens is not None else 2048
        generator = ApiReviewGenerator(
            model=api_model,
            api_key=args.api_key,
            base_url=args.api_base_url,
            temperature=args.temperature,
            top_p=args.top_p,
            max_tokens=api_max_tokens,
            max_workers=args.api_max_workers,
            timeout=args.api_timeout,
            max_retries=args.api_max_retries,
            provider=args.api_provider,
            system_prompt=args.api_system_prompt,
        )
        print(f"[MAIN] Using API backend: model={api_model}")
    else:
        if not args.model_path:
            print("[ERROR] --model-path is required for vllm backend.")
            return 1
        selected_use_chat_template = _resolve_use_chat_template(args.model_path, args.use_chat_template)
        generator = VllmReviewGenerator(
            model_path=args.model_path,
            tensor_parallel_size=args.tensor_parallel_size,
            gpu_memory_utilization=args.gpu_memory_utilization,
            max_model_len=args.max_model_len,
            temperature=args.temperature,
            top_p=args.top_p,
            max_tokens=selected_max_tokens,
            trust_remote_code=args.trust_remote_code,
            enforce_eager=args.enforce_eager,
            max_num_seqs=args.max_num_seqs,
            seed=args.seed,
            use_chat_template=selected_use_chat_template,
        )
        print(f"[MAIN] Using vLLM backend: model={args.model_path}")
    print(f"[MAIN] model_adapter_mode={effective_model_adapter_mode} (requested={args.model_adapter_mode})")

    results: List[Dict[str, Any]] = []
    batch_size = max(1, int(args.manager_batch_size or 1))
    extras_rows = [_row_to_env_kwargs(row) for row in rows]
    for extras in extras_rows:
        if not extras.get("model_adapter_mode") or extras.get("model_adapter_mode") == "auto":
            extras["model_adapter_mode"] = effective_model_adapter_mode
    _truncate_output(args.output_path)
    if batch_size == 1:
        for extras in extras_rows:
            result = run_review_episode(
                extras=extras,
                mode=args.mode,
                generate_fn=generator,
                max_turns=args.max_turns,
                max_workers_per_turn=args.max_workers_per_turn,
                log_dir=args.log_dir,
                model_adapter_mode=effective_model_adapter_mode,
            )
            results.append(result)
            _append_result(args.output_path, result)
            print(
                json.dumps(
                    {
                        "paper_id": result["paper_id"],
                        "mode": result["mode"],
                        "reward": result["reward"],
                        "final_decision": result["review_state"].get("final_decision", "undecided"),
                        "model_adapter_mode": result["review_state"].get("model_adapter_mode", effective_model_adapter_mode),
                    },
                    ensure_ascii=False,
                ),
                flush=True,
            )
    else:
        for start in range(0, len(extras_rows), batch_size):
            batch_results = run_review_batch(
                extras_list=extras_rows[start : start + batch_size],
                mode=args.mode,
                generate_fn=generator,
                max_turns=args.max_turns,
                max_workers_per_turn=args.max_workers_per_turn,
                log_dir=args.log_dir,
                model_adapter_mode=effective_model_adapter_mode,
            )
            for result in batch_results:
                results.append(result)
                _append_result(args.output_path, result)
                print(
                    json.dumps(
                        {
                            "paper_id": result["paper_id"],
                            "mode": result["mode"],
                            "reward": result["reward"],
                            "final_decision": result["review_state"].get("final_decision", "undecided"),
                            "model_adapter_mode": result["review_state"].get("model_adapter_mode", effective_model_adapter_mode),
                        },
                        ensure_ascii=False,
                    ),
                    flush=True,
                )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
