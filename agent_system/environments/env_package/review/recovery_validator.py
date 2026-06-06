from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

RECOVERY_STATUS_TRANSITIONS = {
    "claim": {
        "supported": {"unsupported", "superseded"},
        "partially_supported": {"unsupported"},
        "uncertain": {"unsupported"},
    },
    "flaw": {
        "candidate": {"downgraded", "retracted"},
        "confirmed": {"downgraded", "retracted"},
    },
    "hypothesis": {
        "active": {"challenged"},
        "challenged": {"weakened", "overturned"},
    },
    "gap": {
        "open": {"resolved", "superseded", "converted", "not_assessable"},
    },
    "evidence_link": {
        "bound": {"unbound", "invalid_claim_id"},
        "bound_real_claim": {"unbound", "invalid_claim_id"},
        "unchecked": {"unbound", "invalid_claim_id"},
        "invalid_claim_id": {"unbound"},
        "unbound": {"invalid_claim_id"},
    },
}
VERIFIED_RECOVERY_GROUNDING_LABELS = {"paper_grounded_exact", "paper_grounded_normalized"}
VERIFIED_RECOVERY_SEMANTIC_LABELS = {"semantic_support_verified", "semantic_negative_verified"}

_HYPOTHESIS_STATUS_RE = re.compile(r"^\[([A-Z_]+)\]\s*")


def _base_validation(patch: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "validated": False,
        "commit_allowed": False,
        "failure_code": "",
        "failure_message": "",
        "target_type": patch.get("target_type", ""),
        "target_id": patch.get("target_id", ""),
        "old_status": patch.get("old_status", ""),
        "new_status": patch.get("new_status", ""),
        "supporting_evidence_ids": list(patch.get("supporting_evidence_ids", []) or []),
        "resolved_conflict_count": 0,
        "required_fix": "",
        "target_field": "",
        "target_index": None,
        "current_status": "",
        "matched_conflict_ids": [],
        "missing_requirements": list(patch.get("missing_requirements", []) or []),
    }


def _failure(validation: Dict[str, Any], code: str, message: str, required_fix: str, *, validated: bool = False) -> Dict[str, Any]:
    validation.update(
        {
            "validated": validated,
            "commit_allowed": False,
            "failure_code": code,
            "failure_message": message,
            "required_fix": required_fix,
        }
    )
    return validation


def _success(validation: Dict[str, Any], matched_conflict_ids: List[str]) -> Dict[str, Any]:
    validation.update(
        {
            "validated": True,
            "commit_allowed": True,
            "failure_code": "SUCCESS",
            "failure_message": "",
            "required_fix": "",
            "matched_conflict_ids": matched_conflict_ids,
            "resolved_conflict_count": len(matched_conflict_ids),
        }
    )
    return validation


def _extract_hypothesis_status(text: Any) -> str:
    match = _HYPOTHESIS_STATUS_RE.match(str(text or "").strip())
    if not match:
        return "active"
    return match.group(1).strip().lower()


def _strip_hypothesis_status(text: Any) -> str:
    return _HYPOTHESIS_STATUS_RE.sub("", str(text or "").strip(), count=1).strip()


def _match_hypothesis_target(target_id: str, text: str, index: int) -> bool:
    if not target_id:
        return False
    plain = _strip_hypothesis_status(text)
    candidates = {
        str(index),
        str(index + 1),
        f"hypothesis-{index}",
        f"hypothesis-{index + 1}",
        plain,
    }
    if target_id in candidates:
        return True
    return target_id in plain or plain in target_id or target_id in text


def _locate_target(state: Dict[str, Any], target_type: str, target_id: str) -> Optional[Dict[str, Any]]:
    if target_type == "claim":
        for idx, item in enumerate(state.get("claims", []) or []):
            if item.get("claim_id") == target_id:
                return {
                    "target_field": "claims",
                    "target_index": idx,
                    "current_status": str(item.get("status") or "").lower(),
                    "target_item": item,
                }
    elif target_type == "flaw":
        for idx, item in enumerate(state.get("flaw_candidates", []) or []):
            if item.get("flaw_id") == target_id:
                return {
                    "target_field": "flaw_candidates",
                    "target_index": idx,
                    "current_status": str(item.get("status") or "").lower(),
                    "target_item": item,
                }
    elif target_type == "hypothesis":
        for idx, text in enumerate(state.get("current_hypotheses", []) or []):
            if _match_hypothesis_target(target_id, str(text), idx):
                return {
                    "target_field": "current_hypotheses",
                    "target_index": idx,
                    "current_status": _extract_hypothesis_status(text),
                    "target_item": text,
                }
    elif target_type == "gap":
        for idx, item in enumerate(state.get("evidence_gaps", []) or []):
            gap_id = str(item.get("gap_id") or "")
            claim_id = str(item.get("claim_id") or "")
            if gap_id == target_id or (claim_id and claim_id == target_id):
                return {
                    "target_field": "evidence_gaps",
                    "target_index": idx,
                    "current_status": str(item.get("status") or "open").lower(),
                    "target_item": item,
                }
    elif target_type == "evidence_link":
        for idx, item in enumerate(state.get("evidence_map", []) or []):
            if item.get("evidence_id") == target_id:
                binding_status = str(item.get("binding_status") or "").lower()
                if not binding_status:
                    binding_status = "bound" if str(item.get("claim_id") or "") else "unbound"
                return {
                    "target_field": "evidence_map",
                    "target_index": idx,
                    "current_status": binding_status,
                    "target_item": item,
                }
    return None


def _collect_related_conflict_ids(state: Dict[str, Any], target_type: str, target_id: str) -> List[str]:
    related: List[str] = []
    for note in state.get("conflict_notes", []) or []:
        conflict_id = str(note.get("conflict_id") or "").strip()
        if not conflict_id:
            continue
        if target_type == "claim" and str(note.get("claim_id") or "") == target_id:
            related.append(conflict_id)
        elif target_type == "flaw" and str(note.get("flaw_id") or "") == target_id:
            related.append(conflict_id)
        elif target_type == "hypothesis":
            related.append(conflict_id)
    return related


def _validate_evidence_alignment(state: Dict[str, Any], target_type: str, target: Dict[str, Any], evidence_ids: List[str]) -> Optional[str]:
    known_evidence = {
        str(item.get("evidence_id") or ""): item
        for item in state.get("evidence_map", []) or []
        if item.get("evidence_id")
    }
    if any(evidence_id not in known_evidence for evidence_id in evidence_ids):
        return "One or more supporting_evidence_ids do not exist in the current ReviewState."

    evidence_id_set = set(evidence_ids)
    if target_type == "claim":
        target_claim_id = str(target.get("claim_id") or "")
        allowed_ids = set(target.get("supporting_evidence_ids", []) or [])
        allowed_ids.update(
            str(item.get("evidence_id") or "")
            for item in state.get("evidence_map", []) or []
            if str(item.get("claim_id") or "") == target_claim_id and item.get("evidence_id")
        )
        if allowed_ids and not (evidence_id_set & allowed_ids):
            return "Supporting evidence exists in state, but the patch references evidence unrelated to the target claim."
    elif target_type == "flaw":
        allowed_ids = set(target.get("evidence_ids", []) or [])
        related_claim_ids = set(target.get("related_claim_ids", []) or [])
        allowed_ids.update(
            str(item.get("evidence_id") or "")
            for item in state.get("evidence_map", []) or []
            if str(item.get("claim_id") or "") in related_claim_ids and item.get("evidence_id")
        )
        if allowed_ids and not (evidence_id_set & allowed_ids):
            return "Supporting evidence does not align with the target flaw or its related claims."
    elif target_type == "gap":
        target_claim_id = str(target.get("claim_id") or "")
        target_evidence_id = str(target.get("evidence_id") or "")
        if target_evidence_id and target_evidence_id not in evidence_id_set:
            return "Supporting evidence does not match the target gap evidence id."
        if target_claim_id and not any(str(known_evidence[eid].get("claim_id") or "") == target_claim_id for eid in evidence_id_set):
            return "Supporting evidence does not align with the target gap claim."
    elif target_type == "evidence_link":
        target_evidence_id = str(target.get("evidence_id") or "")
        if evidence_ids and target_evidence_id not in evidence_id_set:
            return "Evidence-link patches may only cite the target evidence id as supporting evidence."
    return None



def _state_requires_verified_recovery_grounding(state: Dict[str, Any]) -> bool:
    if state.get("evidence_quote_bank"):
        return True
    return any(
        isinstance(item, dict) and str(item.get("verified_grounding_label") or "") not in {"", "unjudged"}
        for item in state.get("evidence_map", []) or []
    )


def _is_verified_recovery_evidence(item: Dict[str, Any]) -> bool:
    return (
        str(item.get("verified_grounding_label") or "").strip() in VERIFIED_RECOVERY_GROUNDING_LABELS
        and str(item.get("semantic_grounding_label") or "").strip() in VERIFIED_RECOVERY_SEMANTIC_LABELS
    )


def _is_verified_negative_recovery_evidence(item: Dict[str, Any]) -> bool:
    if not _is_verified_recovery_evidence(item):
        return False
    stance = str(item.get("stance") or "").strip().lower()
    strength = str(item.get("strength") or "").strip().lower()
    return stance in {"contradicts", "refutes", "weakens", "does_not_support", "missing", "unsupported", "insufficient"} or strength in {"missing", "insufficient"}


def _flaw_has_verified_negative_recovery_grounding(state: Dict[str, Any], flaw: Dict[str, Any]) -> bool:
    evidence_lookup = {
        str(item.get("evidence_id") or ""): item
        for item in state.get("evidence_map", []) or []
        if isinstance(item, dict) and item.get("evidence_id")
    }
    ids: List[str] = []
    for key in ("negative_evidence_ids", "hard_negative_evidence_ids", "contradicting_evidence_ids", "evidence_ids"):
        raw = flaw.get(key) or []
        if isinstance(raw, str):
            raw = [raw]
        ids.extend(str(item) for item in raw if str(item).strip())
    for evidence_id in ids:
        item = evidence_lookup.get(evidence_id)
        if isinstance(item, dict) and _is_verified_negative_recovery_evidence(item):
            return True
    return False


def _is_safe_flaw_downgrade_without_evidence(state: Dict[str, Any], target: Dict[str, Any], new_status: str) -> bool:
    if new_status not in {"downgraded", "retracted"}:
        return False
    for key in ("evidence_ids", "negative_evidence_ids", "hard_negative_evidence_ids", "contradicting_evidence_ids"):
        raw = target.get(key) or []
        if isinstance(raw, str):
            raw = [raw]
        if any(str(item).strip() for item in raw):
            return False
    return not _flaw_has_verified_negative_recovery_grounding(state, target)


def _validate_claim_unsupported_evidence_semantics(state: Dict[str, Any], evidence_ids: List[str]) -> Optional[str]:
    known_evidence = {
        str(item.get("evidence_id") or ""): item
        for item in state.get("evidence_map", []) or []
        if item.get("evidence_id")
    }
    requires_verified = _state_requires_verified_recovery_grounding(state)
    negative_ids: List[str] = []
    unverified_negative_ids: List[str] = []
    positive_ids: List[str] = []
    system_missing_ids: List[str] = []
    negative_text_re = re.compile(r"contradict|refut|does not support|fails to|unsupported|lacks", re.I)
    for evidence_id in evidence_ids:
        item = known_evidence.get(str(evidence_id)) or {}
        stance = str(item.get("stance") or "").strip().lower()
        strength = str(item.get("strength") or "").strip().lower()
        source = str(item.get("source") or "").strip().lower()
        evidence_text = str(item.get("evidence") or "")
        text = " ".join(str(item.get(key) or "") for key in ("evidence", "source", "rationale", "binding_rationale"))
        if _is_verified_negative_recovery_evidence(item):
            negative_ids.append(str(evidence_id))
            continue
        is_system_missing_marker = (
            str(evidence_id).startswith("evidence-recovery-missing")
            or source == "system recovery salvage"
            or stance in {"missing", "insufficient"}
            or strength in {"missing", "insufficient"}
            or "recovery could not verify" in evidence_text.lower()
        )
        if is_system_missing_marker:
            system_missing_ids.append(str(evidence_id))
            continue
        if stance in {"supports", "partially_supports"}:
            positive_ids.append(str(evidence_id))
            continue
        negative_like = stance in {"contradicts", "refutes", "does_not_support", "unsupported"} or bool(negative_text_re.search(text))
        if negative_like:
            if requires_verified and not _is_verified_recovery_evidence(item):
                unverified_negative_ids.append(str(evidence_id))
            else:
                negative_ids.append(str(evidence_id))
    if negative_ids:
        return None
    if system_missing_ids:
        return "Claim downgrade to unsupported cannot be justified by system recovery missing markers; route this as assessment limitation or gather verified paper-negative evidence."
    if unverified_negative_ids:
        return "Claim downgrade to unsupported requires verified paper-grounded negative evidence; unverified/paraphrase-only evidence cannot justify unsupported recovery."
    if positive_ids:
        return "Claim downgrade to unsupported cannot be justified only by support/partially-support evidence."
    return "Claim downgrade to unsupported requires verified paper-negative evidence, not system missing-evidence markers."


def _can_normalize_claim_patch_to_unsupported(state: Dict[str, Any], old_status: str, evidence_ids: List[str]) -> bool:
    if not evidence_ids:
        return False
    allowed = RECOVERY_STATUS_TRANSITIONS.get("claim", {})
    if "unsupported" not in allowed.get(old_status, set()):
        return False
    return _validate_claim_unsupported_evidence_semantics(state, evidence_ids) is None

def validate_recovery_patch(state: Dict[str, Any], patch: Dict[str, Any]) -> Dict[str, Any]:
    validation = _base_validation(patch)
    try:
        parse_status = patch.get("parse_status")
        if parse_status == "parse_failure":
            return _failure(
                validation,
                "PARSE_ERROR",
                patch.get("parse_error") or "Recovery parser could not recognize the output.",
                "Return either apply_recovery_patch or blocked with the required structured fields.",
                validated=False,
            )

        if patch.get("action") == "blocked":
            return _failure(
                validation,
                "BLOCKED_BY_POLICY",
                patch.get("blocked_reason") or "Recovery worker explicitly reported blocked.",
                "; ".join(patch.get("missing_requirements", []) or []) or "Provide the missing evidence or target mapping before retrying.",
                validated=True,
            )

        target_type = patch.get("target_type", "")
        if target_type not in RECOVERY_STATUS_TRANSITIONS:
            return _failure(
                validation,
                "UNKNOWN_TARGET",
                f"Unsupported recovery target_type: {target_type or 'missing'}.",
                "Use one of: claim, flaw, hypothesis, gap, evidence_link.",
                validated=False,
            )

        if not patch.get("target_id"):
            return _failure(
                validation,
                "MISSING_TARGET_ID",
                "Recovery patch is missing target_id.",
                "Provide the exact target_id for the claim, flaw, or hypothesis to update.",
                validated=False,
            )

        if not patch.get("old_status") or not patch.get("new_status"):
            return _failure(
                validation,
                "PARSE_ERROR",
                "Recovery patch is missing old_status or new_status.",
                "Provide both old_status and new_status in the patch schema.",
                validated=False,
            )

        located = _locate_target(state, target_type, patch["target_id"])
        if not located:
            return _failure(
                validation,
                "UNKNOWN_TARGET",
                f"Target id '{patch['target_id']}' was not found in the current ReviewState.",
                "Use an existing target_id from the current ReviewState.",
                validated=False,
            )

        validation.update(located)
        current_status = str(located.get("current_status") or "").lower()
        old_status = str(patch.get("old_status") or "").lower()
        new_status = str(patch.get("new_status") or "").lower()
        evidence_ids = list(patch.get("supporting_evidence_ids", []) or [])

        if (
            target_type == "claim"
            and new_status in {"supported", "partially_supported", "uncertain"}
            and _can_normalize_claim_patch_to_unsupported(state, old_status, evidence_ids)
        ):
            validation["status_normalized_from"] = new_status
            validation["status_normalized_to"] = "unsupported"
            validation["normalization_reason"] = "verified_negative_evidence_requires_conservative_claim_downgrade"
            new_status = "unsupported"
            validation["new_status"] = new_status

        if current_status == new_status:
            return _failure(
                validation,
                "NO_EFFECT_PATCH",
                f"Target '{patch['target_id']}' is already in status '{new_status}'.",
                "Choose a corrective status different from the current state.",
                validated=True,
            )

        allowed_transitions = RECOVERY_STATUS_TRANSITIONS[target_type]
        if old_status not in allowed_transitions or new_status not in allowed_transitions[old_status]:
            return _failure(
                validation,
                "INVALID_STATUS_TRANSITION",
                f"Recovery does not allow transition {target_type}:{old_status}->{new_status}.",
                "Use a corrective lifecycle transition allowed by the recovery protocol.",
                validated=False,
            )

        if current_status != old_status:
            return _failure(
                validation,
                "SEMANTIC_MISMATCH",
                f"Expected current status '{old_status}', but ReviewState currently stores '{current_status}'.",
                "Refresh the target status from the latest ReviewState before retrying.",
                validated=False,
            )

        if not evidence_ids:
            if target_type == "flaw" and _is_safe_flaw_downgrade_without_evidence(state, located.get("target_item", {}), new_status):
                return _success(validation, [])
            if target_type == "evidence_link" and new_status in {"unbound", "invalid_claim_id"}:
                return _success(validation, [])
            if target_type == "gap" and new_status in {"superseded", "converted", "not_assessable"}:
                return _success(validation, [])
            return _failure(
                validation,
                "INSUFFICIENT_EVIDENCE",
                "A recovery commit requires at least one supporting_evidence_id already grounded in ReviewState. Flaw downgrades, evidence-link unbinding, and non-assessable gap closure have narrow evidence-free paths.",
                "Reference concrete evidence ids already present in ReviewState, or use a narrow evidence-free lifecycle operation.",
                validated=True,
            )

        evidence_mismatch = _validate_evidence_alignment(state, target_type, located.get("target_item", {}), evidence_ids)
        if evidence_mismatch:
            return _failure(
                validation,
                "EVIDENCE_TARGET_MISMATCH",
                evidence_mismatch,
                "Bind the patch to evidence ids that exist in state and align with the target item.",
                validated=True,
            )

        if target_type == "claim" and new_status == "unsupported":
            semantic_mismatch = _validate_claim_unsupported_evidence_semantics(state, evidence_ids)
            if semantic_mismatch:
                return _failure(
                    validation,
                    "EVIDENCE_SEMANTIC_MISMATCH",
                    semantic_mismatch,
                    "Use contradiction, missing-evidence, or negative grounding evidence for unsupported claim recovery.",
                    validated=True,
                )

        related_conflict_ids = _collect_related_conflict_ids(state, target_type, patch["target_id"])
        provided_conflict_ids = list(patch.get("conflict_note_ids", []) or [])
        if provided_conflict_ids:
            unresolved = [conflict_id for conflict_id in provided_conflict_ids if conflict_id not in related_conflict_ids]
            if unresolved:
                return _failure(
                    validation,
                    "UNRESOLVED_CONFLICT",
                    "Patch references conflict notes that do not match the target item's active conflicts.",
                    "Reference only active conflict_note_ids attached to the target item.",
                    validated=True,
                )
        elif patch.get("resolution_expectation") == "resolved" and related_conflict_ids:
            return _failure(
                validation,
                "UNRESOLVED_CONFLICT",
                "Recovery claims full resolution but does not reference which conflict notes were resolved.",
                "Provide conflict_note_ids or downgrade resolution_expectation to partially_resolved.",
                validated=True,
            )

        return _success(validation, provided_conflict_ids)
    except Exception as exc:  # pragma: no cover - defensive guard for future debugging
        return _failure(
            validation,
            "CHECKER_TOO_STRICT",
            f"Recovery validator raised an internal error: {exc}",
            "Debug or relax the recovery checker before trusting this result.",
            validated=False,
        )
