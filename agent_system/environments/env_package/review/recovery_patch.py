from __future__ import annotations

import re
from typing import Any, Dict, List

RECOVERY_ACTIONS = {"apply_recovery_patch", "blocked"}
RECOVERY_SHAPE_KEYS = {
    "action",
    "target_type",
    "target_id",
    "old_status",
    "new_status",
    "supporting_evidence_ids",
    "conflict_note_ids",
    "reason_for_change",
    "resolution_expectation",
    "confidence",
    "blocked_reason",
    "missing_requirements",
}
RESOLUTION_EXPECTATIONS = {"resolved", "partially_resolved", "blocked"}
RECOVERY_PATCH_SOURCES = {"model_generated", "system_salvaged", "none"}
RECOVERY_PATCH_SOURCE_ALIASES = {"salvaged": "system_salvaged"}


def _normalize_text(value: Any, default: str = "", max_length: int = 400) -> str:
    if value is None:
        return default
    text = re.sub(r"\s+", " ", str(value)).strip()
    if not text:
        return default
    return text[:max_length]


def _normalize_list_of_strings(value: Any, max_items: int = 8, max_length: int = 160) -> List[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        value = [value]
    seen = set()
    results: List[str] = []
    for item in value:
        text = _normalize_text(item, max_length=max_length)
        if not text:
            continue
        lowered = text.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        results.append(text)
        if len(results) >= max_items:
            break
    return results


def _normalize_float(value: Any, default: float = 0.0) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = default
    return max(0.0, min(1.0, number))


def _normalize_patch_source(value: Any, default: str = "none") -> str:
    source = _normalize_text(value, max_length=40).lower()
    source = RECOVERY_PATCH_SOURCE_ALIASES.get(source, source)
    if source in RECOVERY_PATCH_SOURCES:
        return source
    return default


def looks_like_recovery_payload(payload: Any) -> bool:
    if not isinstance(payload, dict):
        return False
    action = _normalize_text(payload.get("action"), max_length=64).lower()
    if action in RECOVERY_ACTIONS:
        return True
    return any(
        [
            _normalize_text(payload.get("target_type"), max_length=32),
            _normalize_text(payload.get("target_id"), max_length=120),
            _normalize_text(payload.get("old_status"), max_length=64),
            _normalize_text(payload.get("new_status"), max_length=64),
            _normalize_text(payload.get("blocked_reason"), max_length=400),
            _normalize_list_of_strings(payload.get("supporting_evidence_ids")),
            _normalize_list_of_strings(payload.get("conflict_note_ids"), max_length=80),
            _normalize_list_of_strings(payload.get("missing_requirements")),
        ]
    )


def parse_recovery_payload(payload: Any) -> Dict[str, Any]:
    raw_payload = payload if isinstance(payload, dict) else {}
    action = _normalize_text(raw_payload.get("action"), max_length=64).lower()
    target_type = _normalize_text(raw_payload.get("target_type"), max_length=32).lower()
    target_id = _normalize_text(raw_payload.get("target_id"), max_length=120)
    old_status = _normalize_text(raw_payload.get("old_status"), max_length=64).lower()
    new_status = _normalize_text(raw_payload.get("new_status"), max_length=64).lower()
    supporting_evidence_ids = _normalize_list_of_strings(raw_payload.get("supporting_evidence_ids"))
    conflict_note_ids = _normalize_list_of_strings(raw_payload.get("conflict_note_ids"), max_length=80)
    reason_for_change = _normalize_text(raw_payload.get("reason_for_change"), max_length=240)
    resolution_expectation = _normalize_text(raw_payload.get("resolution_expectation"), max_length=32).lower()
    blocked_reason = _normalize_text(raw_payload.get("blocked_reason"), max_length=400)
    missing_requirements = _normalize_list_of_strings(raw_payload.get("missing_requirements"))
    recovery_patch_source = _normalize_patch_source(raw_payload.get("_recovery_patch_source"))

    if action not in RECOVERY_ACTIONS:
        if blocked_reason or missing_requirements:
            action = "blocked"
        elif target_type or target_id or new_status or supporting_evidence_ids or conflict_note_ids:
            action = "apply_recovery_patch"
        else:
            action = ""

    parse_status = "parse_failure"
    parse_error = ""
    if action == "blocked":
        parse_status = "blocked"
        if resolution_expectation not in RESOLUTION_EXPECTATIONS:
            resolution_expectation = "blocked"
    elif action == "apply_recovery_patch":
        parse_status = "valid_patch"
        if resolution_expectation not in {"resolved", "partially_resolved"}:
            resolution_expectation = "partially_resolved"
        if recovery_patch_source == "none":
            recovery_patch_source = "model_generated"
    else:
        parse_error = "Payload does not contain a recognizable recovery action."

    return {
        "is_recovery_payload": bool(action or looks_like_recovery_payload(raw_payload)),
        "parse_status": parse_status,
        "parse_error": parse_error,
        "action": action,
        "target_type": target_type,
        "target_id": target_id,
        "old_status": old_status,
        "new_status": new_status,
        "supporting_evidence_ids": supporting_evidence_ids,
        "conflict_note_ids": conflict_note_ids,
        "reason_for_change": reason_for_change,
        "resolution_expectation": resolution_expectation,
        "confidence": _normalize_float(raw_payload.get("confidence"), default=0.0),
        "recovery_patch_source": recovery_patch_source,
        "blocked_reason": blocked_reason,
        "missing_requirements": missing_requirements,
        "raw_payload": raw_payload,
    }
