"""P1 #8 – Unit tests for recovery replay harness.

Covers:
- Synthetic mini-cases for each failure code path
- Fixture-based replay of real cases extracted from full39 runs
- Batch replay + summary aggregation
- Edge cases (missing fields, empty state, etc.)
"""

from __future__ import annotations

import copy
import glob
import json
import os
from pathlib import Path
from typing import Any, Dict

import pytest

from agent_system.environments.env_package.review.recovery_replay import (
    ReplayResult,
    _rewind_state_for_replay,
    replay_batch,
    replay_recovery_case,
    summarize_batch,
)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

FIXTURE_DIR = Path(__file__).resolve().parent / "recovery_replay" / "cases"


def _mini_state(
    *,
    claim_id: str = "claim-1",
    claim_status: str = "supported",
    evidence_id: str = "ev-1",
    evidence_stance: str = "contradicts",
    evidence_grounding: str = "paper_grounded_exact",
    evidence_semantic: str = "semantic_negative_verified",
    flaw_id: str = "",
    flaw_status: str = "",
) -> Dict[str, Any]:
    """Build a minimal review state for testing."""
    state: Dict[str, Any] = {
        "claims": [{"claim_id": claim_id, "status": claim_status}],
        "evidence_map": [
            {
                "evidence_id": evidence_id,
                "claim_id": claim_id,
                "stance": evidence_stance,
                "grounding_label": evidence_grounding,
                "semantic_alignment_label": evidence_semantic,
                "text": "The experiments show degraded performance.",
            }
        ],
        "flaw_candidates": [],
        "current_hypotheses": [],
        "conflict_notes": [],
    }
    if flaw_id:
        state["flaw_candidates"].append(
            {"flaw_id": flaw_id, "status": flaw_status or "candidate"}
        )
    return state


def _mini_patch(
    *,
    action: str = "apply_recovery_patch",
    target_type: str = "claim",
    target_id: str = "claim-1",
    old_status: str = "supported",
    new_status: str = "unsupported",
    supporting_evidence_ids: list | None = None,
    blocked_reason: str = "",
    source: str = "model_generated",
) -> Dict[str, Any]:
    return {
        "action": action,
        "target_type": target_type,
        "target_id": target_id,
        "old_status": old_status,
        "new_status": new_status,
        "supporting_evidence_ids": supporting_evidence_ids if supporting_evidence_ids is not None else ["ev-1"],
        "blocked_reason": blocked_reason,
        "_recovery_patch_source": source,
    }


# ===================================================================
# 1. Synthetic cases – one per failure code
# ===================================================================


class TestSyntheticReplay:
    """Synthetic mini-state replay tests."""

    def test_success_claim_unsupported(self):
        case = {
            "case_id": "synth_success",
            "review_state": _mini_state(),
            "raw_payload": _mini_patch(),
            "expected": {"failure_code": "SUCCESS", "commit_allowed": True},
        }
        r = replay_recovery_case(case)
        assert r.matches_expected, r.diff
        assert r.failure_code == "SUCCESS"
        assert r.commit_allowed

    def test_blocked_by_policy(self):
        case = {
            "case_id": "synth_blocked",
            "review_state": _mini_state(),
            "raw_payload": _mini_patch(
                action="blocked", blocked_reason="No evidence"
            ),
            "expected": {"failure_code": "BLOCKED_BY_POLICY", "validated": True},
        }
        r = replay_recovery_case(case)
        assert r.matches_expected, r.diff

    def test_insufficient_evidence_no_evidence_ids(self):
        """Empty supporting_evidence_ids triggers INSUFFICIENT_EVIDENCE."""
        case = {
            "case_id": "synth_insuf",
            "review_state": _mini_state(),
            "raw_payload": _mini_patch(supporting_evidence_ids=[]),
            "expected": {"failure_code": "INSUFFICIENT_EVIDENCE"},
        }
        r = replay_recovery_case(case)
        assert r.matches_expected, r.diff

    def test_invalid_status_transition(self):
        """supported → confirmed is not an allowed claim transition."""
        case = {
            "case_id": "synth_invalid_trans",
            "review_state": _mini_state(claim_status="supported"),
            "raw_payload": _mini_patch(old_status="supported", new_status="confirmed"),
            "expected": {"failure_code": "INVALID_STATUS_TRANSITION"},
        }
        r = replay_recovery_case(case)
        assert r.matches_expected, r.diff

    def test_unknown_target_id(self):
        case = {
            "case_id": "synth_unknown",
            "review_state": _mini_state(),
            "raw_payload": _mini_patch(target_id="claim-999"),
            "expected": {"failure_code": "UNKNOWN_TARGET"},
        }
        r = replay_recovery_case(case)
        assert r.matches_expected, r.diff

    def test_flaw_downgrade_success(self):
        state = _mini_state(
            flaw_id="flaw-1",
            flaw_status="candidate",
            evidence_stance="contradicts",
        )
        patch = _mini_patch(
            target_type="flaw",
            target_id="flaw-1",
            old_status="candidate",
            new_status="downgraded",
        )
        case = {
            "case_id": "synth_flaw_downgrade",
            "review_state": state,
            "raw_payload": patch,
            "expected": {"failure_code": "SUCCESS", "commit_allowed": True},
        }
        r = replay_recovery_case(case)
        assert r.matches_expected, r.diff

    def test_parse_failure_empty_payload(self):
        case = {
            "case_id": "synth_parse_fail",
            "review_state": _mini_state(),
            "raw_payload": {},
            "expected": {"failure_code": "PARSE_ERROR"},
        }
        r = replay_recovery_case(case)
        assert r.matches_expected, r.diff


# ===================================================================
# 2. Rewind logic
# ===================================================================


class TestRewindState:
    """Tests for _rewind_state_for_replay."""

    def test_rewind_claim_from_post_recovery(self):
        state = _mini_state(claim_status="unsupported")
        parsed = {
            "target_type": "claim",
            "target_id": "claim-1",
            "old_status": "supported",
            "new_status": "unsupported",
        }
        rewound = _rewind_state_for_replay(copy.deepcopy(state), parsed)
        assert rewound["claims"][0]["status"] == "supported"

    def test_no_rewind_when_already_old_status(self):
        state = _mini_state(claim_status="supported")
        parsed = {
            "target_type": "claim",
            "target_id": "claim-1",
            "old_status": "supported",
            "new_status": "unsupported",
        }
        rewound = _rewind_state_for_replay(copy.deepcopy(state), parsed)
        assert rewound["claims"][0]["status"] == "supported"

    def test_rewind_flaw_from_downgraded(self):
        state = _mini_state(flaw_id="f1", flaw_status="downgraded")
        parsed = {
            "target_type": "flaw",
            "target_id": "f1",
            "old_status": "candidate",
            "new_status": "downgraded",
        }
        rewound = _rewind_state_for_replay(copy.deepcopy(state), parsed)
        assert rewound["flaw_candidates"][0]["status"] == "candidate"

    def test_no_rewind_for_blocked_action(self):
        state = _mini_state()
        parsed = {
            "target_type": "",
            "target_id": "",
            "old_status": "",
            "new_status": "",
        }
        rewound = _rewind_state_for_replay(copy.deepcopy(state), parsed)
        assert rewound["claims"][0]["status"] == "supported"


# ===================================================================
# 3. Edge cases
# ===================================================================


class TestEdgeCases:
    def test_missing_review_state(self):
        r = replay_recovery_case({"raw_payload": _mini_patch()})
        assert not r.matches_expected
        assert "review_state" in r.error

    def test_missing_raw_payload(self):
        r = replay_recovery_case({"review_state": _mini_state()})
        assert not r.matches_expected
        assert "raw_payload" in r.error

    def test_no_expected_always_matches(self):
        case = {
            "review_state": _mini_state(),
            "raw_payload": _mini_patch(),
        }
        r = replay_recovery_case(case)
        assert r.matches_expected
        assert r.failure_code  # still has a result

    def test_result_properties(self):
        case = {
            "case_id": "prop_test",
            "review_state": _mini_state(),
            "raw_payload": _mini_patch(),
        }
        r = replay_recovery_case(case)
        assert r.case_id == "prop_test"
        assert isinstance(r.validated, bool)
        assert isinstance(r.commit_allowed, bool)
        assert isinstance(r.failure_code, str)


# ===================================================================
# 4. Batch & summary
# ===================================================================


class TestBatchReplay:
    def test_batch_two_cases(self):
        cases = [
            {
                "case_id": "a",
                "review_state": _mini_state(),
                "raw_payload": _mini_patch(),
                "expected": {"failure_code": "SUCCESS"},
            },
            {
                "case_id": "b",
                "review_state": _mini_state(),
                "raw_payload": _mini_patch(action="blocked", blocked_reason="X"),
                "expected": {"failure_code": "BLOCKED_BY_POLICY"},
            },
        ]
        results = replay_batch(cases)
        assert len(results) == 2
        assert all(r.matches_expected for r in results)

        summary = summarize_batch(results)
        assert summary["total"] == 2
        assert summary["matched"] == 2
        assert summary["mismatched"] == 0

    def test_summary_captures_mismatch(self):
        cases = [
            {
                "case_id": "wrong",
                "review_state": _mini_state(),
                "raw_payload": _mini_patch(),
                "expected": {"failure_code": "BLOCKED_BY_POLICY"},
            },
        ]
        results = replay_batch(cases)
        summary = summarize_batch(results)
        assert summary["mismatched"] == 1
        assert len(summary["mismatch_details"]) == 1


# ===================================================================
# 5. Fixture-based replay (if fixtures exist)
# ===================================================================


class TestFixtureReplay:
    """Replay real fixture cases extracted from full39 runs."""

    @pytest.fixture
    def fixture_cases(self):
        if not FIXTURE_DIR.exists():
            pytest.skip(f"No fixture dir: {FIXTURE_DIR}")
        paths = sorted(FIXTURE_DIR.glob("*.json"))
        if not paths:
            pytest.skip("No fixture JSON files found")
        cases = []
        for p in paths:
            with open(p) as f:
                cases.append(json.load(f))
        return cases

    def test_all_fixtures_match(self, fixture_cases):
        results = replay_batch(fixture_cases)
        summary = summarize_batch(results)
        for r in results:
            if not r.matches_expected:
                pytest.fail(
                    f"Case {r.case_id} mismatch: {r.diff} error={r.error}"
                )
        assert summary["matched"] == summary["total"]

    def test_all_fixtures_no_errors(self, fixture_cases):
        results = replay_batch(fixture_cases)
        for r in results:
            assert not r.error, f"Case {r.case_id}: {r.error}"

    def test_fixture_count(self, fixture_cases):
        assert len(fixture_cases) >= 4, (
            f"Expected >=4 fixture cases, got {len(fixture_cases)}"
        )
