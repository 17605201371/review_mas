"""P1 #8 – Recovery Replay Harness.

Pure-function replay of a recovery patch against a review-state snapshot.
Designed for offline debugging of recovery failures without running full39.

Usage
-----
    from agent_system.environments.env_package.review.recovery_replay import (
        replay_recovery_case,
        ReplayResult,
    )

    result = replay_recovery_case({
        "case_id": "paper_X_turn_4",
        "review_state": { ... },      # state_snapshot dict
        "raw_payload": { ... },        # Critique Agent worker payload
        "expected": {                  # optional ground-truth
            "failure_code": "BLOCKED_BY_POLICY",
            "validated": False,
        },
    })
    assert result.matches_expected
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from agent_system.environments.env_package.review.recovery_patch import (
    parse_recovery_payload,
)
from agent_system.environments.env_package.review.recovery_validator import (
    validate_recovery_patch,
)


@dataclass
class ReplayResult:
    """Outcome of replaying a single recovery case."""

    case_id: str = ""
    parsed: Dict[str, Any] = field(default_factory=dict)
    validation: Dict[str, Any] = field(default_factory=dict)
    matches_expected: bool = True
    diff: List[Dict[str, str]] = field(default_factory=list)
    error: str = ""

    # convenience accessors
    @property
    def failure_code(self) -> str:
        return self.validation.get("failure_code", "")

    @property
    def validated(self) -> bool:
        return bool(self.validation.get("validated"))

    @property
    def commit_allowed(self) -> bool:
        return bool(self.validation.get("commit_allowed"))


def replay_recovery_case(case: Dict[str, Any]) -> ReplayResult:
    """Replay a recovery patch on a state snapshot and compare to expected.

    Parameters
    ----------
    case : dict
        Required keys:
            ``review_state`` – ReviewState dict (claims, evidence_map, …)
            ``raw_payload``  – Worker payload dict (action, target_id, …)
        Optional keys:
            ``case_id``  – label for this case
            ``expected`` – dict of field→value pairs to compare against
                           validation result (e.g. failure_code, validated)

    Returns
    -------
    ReplayResult
    """
    result = ReplayResult(case_id=str(case.get("case_id", "")))

    review_state = case.get("review_state")
    raw_payload = case.get("raw_payload")
    expected = case.get("expected") or {}

    if not isinstance(review_state, dict):
        result.error = "review_state must be a dict"
        result.matches_expected = False
        return result
    if not isinstance(raw_payload, dict):
        result.error = "raw_payload must be a dict"
        result.matches_expected = False
        return result

    # --- Step 1: parse ---
    try:
        parsed = parse_recovery_payload(raw_payload)
    except Exception as exc:
        result.error = f"parse_recovery_payload raised: {exc}"
        result.matches_expected = False
        return result
    result.parsed = parsed

    # --- Step 1b: rewind post-recovery snapshot if needed ---
    try:
        state_copy = copy.deepcopy(review_state)
        state_copy = _rewind_state_for_replay(state_copy, parsed)
    except Exception as exc:
        result.error = f"_rewind_state_for_replay raised: {exc}"
        result.matches_expected = False
        return result

    # --- Step 2: validate ---
    try:
        validation = validate_recovery_patch(state_copy, parsed)
    except Exception as exc:
        result.error = f"validate_recovery_patch raised: {exc}"
        result.matches_expected = False
        return result
    result.validation = validation

    # --- Step 3: compare with expected ---
    if expected:
        diff: List[Dict[str, str]] = []
        for key, exp_val in expected.items():
            act_val = validation.get(key)
            if _values_differ(exp_val, act_val):
                diff.append({
                    "field": key,
                    "expected": str(exp_val),
                    "actual": str(act_val),
                })
        result.diff = diff
        result.matches_expected = len(diff) == 0

    return result


def replay_batch(cases: List[Dict[str, Any]]) -> List[ReplayResult]:
    """Replay a list of cases and return all results."""
    return [replay_recovery_case(c) for c in cases]


def summarize_batch(results: List[ReplayResult]) -> Dict[str, Any]:
    """Aggregate batch results into a compact summary."""
    total = len(results)
    matched = sum(1 for r in results if r.matches_expected)
    errors = sum(1 for r in results if r.error)
    by_code: Dict[str, int] = {}
    for r in results:
        code = r.failure_code or "NO_CODE"
        by_code[code] = by_code.get(code, 0) + 1
    mismatches = [
        {"case_id": r.case_id, "diff": r.diff, "error": r.error}
        for r in results
        if not r.matches_expected
    ]
    return {
        "total": total,
        "matched": matched,
        "mismatched": total - matched,
        "errors": errors,
        "by_failure_code": by_code,
        "mismatch_details": mismatches,
    }


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _rewind_state_for_replay(
    state: Dict[str, Any], parsed: Dict[str, Any]
) -> Dict[str, Any]:
    """If the snapshot is post-recovery, rewind the target to old_status.

    The turn-log ``state_snapshot`` is captured *after* recovery mutations.
    When the target's current status equals ``new_status`` but differs from
    ``old_status``, we revert it so the validator can replay the transition.
    """
    target_type = parsed.get("target_type", "")
    target_id = parsed.get("target_id", "")
    old_status = parsed.get("old_status", "")
    new_status = parsed.get("new_status", "")
    if not (target_type and target_id and old_status and new_status):
        return state
    if old_status == new_status:
        return state

    field_map = {
        "claim": ("claims", "claim_id", "status"),
        "flaw": ("flaw_candidates", "flaw_id", "status"),
    }
    mapping = field_map.get(target_type)
    if not mapping:
        return state

    field_name, id_key, status_key = mapping
    items = state.get(field_name) or []
    for item in items:
        if item.get(id_key) == target_id:
            current = str(item.get(status_key, "")).lower()
            if current == new_status.lower() and current != old_status.lower():
                item[status_key] = old_status
            break
    return state


def _values_differ(expected: Any, actual: Any) -> bool:
    """Compare two values with type coercion for booleans and strings."""
    if isinstance(expected, bool):
        return bool(actual) != expected
    if isinstance(expected, str):
        return str(actual or "").lower() != expected.lower()
    return expected != actual
