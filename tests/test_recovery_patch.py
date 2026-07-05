import copy
import pytest

from agent_system.environments.env_package.review.recovery_patch import parse_recovery_payload
from agent_system.environments.env_package.review.recovery_validator import validate_recovery_patch
from agent_system.environments.env_package.review.state import (
    _build_recovery_state_delta,
    build_decision_hygiene_view,
    build_turn_log,
    merge_review_state,
)


# Shared full-grounding fields for a genuine reviewer-discovered verified negative.
# Codex hardened the recovery/grounding gates to require trusted grounding
# (verified source span + match_type) and an explicit review_negative_verified
# label; the runtime verifier sets these, so test fixtures must too.
_VERIFIED_NEGATIVE_FIELDS = {
    "raw_quote": "Table 5 shows the proposed method underperforms the baseline on 3 of 5 tasks.",
    "negative_evidence_type": "negative_result",
    "source": "Section 5 Experiments",
    "verified_grounding_label": "paper_grounded_exact",
    "verified_quote_match_type": "quote_bank_raw_canonical",
    "verified_source_span_start": 10,
    "verified_source_span_end": 84,
    "semantic_grounding_label": "semantic_negative_verified",
    "review_negative_label": "review_negative_verified",
}


@pytest.fixture
def mock_state():
    return {
        "claims": [
            {"claim_id": "c1", "status": "supported", "supporting_evidence_ids": ["e1"]},
            {"claim_id": "c2", "status": "partially_supported", "supporting_evidence_ids": ["e2"]},
        ],
        "evidence_map": [
            {"evidence_id": "e1", "claim_id": "c1", "strength": "medium", "stance": "contradicts"},
            {"evidence_id": "e2", "claim_id": "c2", "strength": "strong", "stance": "supports"},
            {"evidence_id": "e3", "claim_id": "c2", "strength": "medium", "stance": "contradicts"},
        ],
        "flaw_candidates": [
            {"flaw_id": "f1", "status": "candidate", "related_claim_ids": ["c1"], "evidence_ids": ["e1"]},
        ],
        "current_hypotheses": [
            "[ACTIVE] The system scales linearly.",
        ],
        "conflict_notes": [
            {"conflict_id": "conf1", "note": "conflict", "claim_id": "c1", "evidence_id": "e1", "flaw_id": "f1"},
        ],
        "turn_id": 1,
    }


def test_parser_salvages_patch_without_explicit_action():
    parsed = parse_recovery_payload(
        {
            "target_type": "flaw",
            "target_id": "f1",
            "old_status": "candidate",
            "new_status": "downgraded",
            "supporting_evidence_ids": ["e1"],
        }
    )

    assert parsed["is_recovery_payload"] is True
    assert parsed["parse_status"] == "valid_patch"
    assert parsed["action"] == "apply_recovery_patch"


def test_valid_patch_validator_allows_commit(mock_state):
    payload = {
        "action": "apply_recovery_patch",
        "target_type": "flaw",
        "target_id": "f1",
        "old_status": "candidate",
        "new_status": "downgraded",
        "supporting_evidence_ids": ["e1"],
        "conflict_note_ids": ["conf1"],
        "resolution_expectation": "resolved",
    }

    validation = validate_recovery_patch(mock_state, parse_recovery_payload(payload))

    assert validation["validated"] is True
    assert validation["commit_allowed"] is True
    assert validation["failure_code"] == "SUCCESS"


def test_unverified_flaw_downgrade_can_commit_without_evidence(mock_state):
    mock_state["flaw_candidates"].append({"flaw_id": "f-empty", "status": "candidate", "related_claim_ids": ["c1"]})

    new_state = merge_review_state(
        mock_state,
        {
            "action": "apply_recovery_patch",
            "target_type": "flaw",
            "target_id": "f-empty",
            "old_status": "candidate",
            "new_status": "downgraded",
            "reason_for_change": "No verified paper-negative evidence grounds this flaw.",
            "resolution_expectation": "partially_resolved",
        },
    )

    flaw = next(item for item in new_state["flaw_candidates"] if item["flaw_id"] == "f-empty")
    assert flaw["status"] == "downgraded"
    assert new_state["_latest_patch_log"]["recovery_committed"] is True
    assert new_state["_latest_patch_log"]["recovery_failure_code"] == "SUCCESS"


def test_grounded_flaw_downgrade_without_evidence_is_blocked(mock_state):
    mock_state["evidence_map"].append(
        {
            "evidence_id": "e-neg-grounded",
            "claim_id": "c1",
            "strength": "strong",
            "stance": "contradicts",
            "verified_grounding_label": "paper_grounded_exact",
            "semantic_grounding_label": "semantic_negative_verified",
            "verified_quote_match_type": "quote_bank_raw_canonical",
            "review_negative_label": "review_negative_verified",
            "verified_source_span_start": 10,
            "verified_source_span_end": 80,
        }
    )
    mock_state["flaw_candidates"].append(
        {
            "flaw_id": "f-grounded",
            "status": "candidate",
            "related_claim_ids": ["c1"],
            "evidence_ids": ["e-neg-grounded"],
            "negative_evidence_ids": ["e-neg-grounded"],
        }
    )

    new_state = merge_review_state(
        mock_state,
        {
            "action": "apply_recovery_patch",
            "target_type": "flaw",
            "target_id": "f-grounded",
            "old_status": "candidate",
            "new_status": "downgraded",
            "reason_for_change": "Attempt to downgrade a grounded flaw without citing counter-evidence.",
            "resolution_expectation": "partially_resolved",
        },
    )

    flaw = next(item for item in new_state["flaw_candidates"] if item["flaw_id"] == "f-grounded")
    assert flaw["status"] == "candidate"
    assert new_state["_latest_patch_log"]["recovery_committed"] is False
    assert new_state["_latest_patch_log"]["recovery_failure_code"] == "INSUFFICIENT_EVIDENCE"


def test_claim_patch_from_partially_supported_to_unsupported_commits(mock_state):
    payload = {
        "action": "apply_recovery_patch",
        "target_type": "claim",
        "target_id": "c2",
        "old_status": "partially_supported",
        "new_status": "unsupported",
        "supporting_evidence_ids": ["e3"],
        "resolution_expectation": "partially_resolved",
    }

    new_state = merge_review_state(mock_state, payload)

    assert new_state["claims"][1]["status"] == "unsupported"
    assert new_state["_latest_patch_log"]["recovery_committed"] is True
    assert new_state["_latest_patch_log"]["recovery_failure_code"] == "SUCCESS"




def test_claim_positive_recovery_with_verified_support_commits(mock_state):
    state = copy.deepcopy(mock_state)
    for evidence in state["evidence_map"]:
        if evidence["evidence_id"] == "e2":
            evidence["verified_grounding_label"] = "paper_grounded_exact"
            evidence["semantic_grounding_label"] = "semantic_support_verified"

    new_state = merge_review_state(
        state,
        {
            "action": "apply_recovery_patch",
            "target_type": "claim",
            "target_id": "c2",
            "old_status": "partially_supported",
            "new_status": "supported",
            "supporting_evidence_ids": ["e2"],
            "resolution_expectation": "partially_resolved",
        },
    )

    assert new_state["claims"][1]["status"] == "supported"
    assert new_state["_latest_patch_log"]["recovery_committed"] is True
    assert new_state["_latest_patch_log"]["recovery_failure_code"] == "SUCCESS"
    assert new_state["_latest_patch_log"]["recovery_patch_operation"] == "resolve_stale_gap"


def test_claim_positive_recovery_normalizes_negative_evidence_to_downgrade(mock_state):
    state = copy.deepcopy(mock_state)
    for evidence in state["evidence_map"]:
        if evidence["evidence_id"] == "e3":
            evidence["verified_grounding_label"] = "paper_grounded_exact"
            evidence["semantic_grounding_label"] = "semantic_negative_verified"

    new_state = merge_review_state(
        state,
        {
            "action": "apply_recovery_patch",
            "target_type": "claim",
            "target_id": "c2",
            "old_status": "partially_supported",
            "new_status": "supported",
            "supporting_evidence_ids": ["e3"],
            "resolution_expectation": "partially_resolved",
        },
    )

    assert new_state["claims"][1]["status"] == "unsupported"
    assert new_state["_latest_patch_log"]["recovery_committed"] is True
    assert new_state["_latest_patch_log"]["recovery_failure_code"] == "SUCCESS"
    assert new_state["_latest_patch_log"]["status_normalized_from"] == "supported"
    assert new_state["_latest_patch_log"]["status_normalized_to"] == "unsupported"


def test_claim_unsupported_patch_rejects_support_only_evidence(mock_state):
    payload = {
        "action": "apply_recovery_patch",
        "target_type": "claim",
        "target_id": "c2",
        "old_status": "partially_supported",
        "new_status": "unsupported",
        "supporting_evidence_ids": ["e2"],
        "resolution_expectation": "partially_resolved",
    }

    new_state = merge_review_state(mock_state, payload)

    assert new_state["claims"][1]["status"] == "partially_supported"
    assert new_state["_latest_patch_log"]["recovery_committed"] is False
    assert new_state["_latest_patch_log"]["recovery_failure_code"] == "EVIDENCE_SEMANTIC_MISMATCH"


def test_cross_turn_recovery_guard_blocks_status_reelevation(mock_state):
    patch_state = merge_review_state(
        mock_state,
        {
            "action": "apply_recovery_patch",
            "target_type": "claim",
            "target_id": "c2",
            "old_status": "partially_supported",
            "new_status": "unsupported",
            "supporting_evidence_ids": ["e3"],
            "resolution_expectation": "partially_resolved",
        },
    )
    patch_state.pop("_transient_status_locks", None)

    reelevated = merge_review_state(
        patch_state,
        {
            "claims": [
                {
                    "claim_id": "c2",
                    "claim": "Later turn tries to restate c2 as still partially supported.",
                    "importance": "medium",
                    "status": "partially_supported",
                    "supporting_evidence_ids": ["e3"],
                }
            ],
            "evidence_map": [
                {
                    "evidence_id": "e2",
                    "claim_id": "c2",
                    "evidence": "Later turn reuses the old support evidence.",
                    "source": "fallback-extraction",
                    "strength": "strong",
                    "stance": "supports",
                }
            ],
        },
    )

    assert reelevated["claims"][1]["status"] == "unsupported"
    assert reelevated["_persistent_status_guards"]["claim:c2"] == "unsupported"


def test_same_turn_recovery_patch_blocks_stale_claim_status_overwrite(mock_state):
    patch_state = merge_review_state(
        mock_state,
        {
            "action": "apply_recovery_patch",
            "target_type": "claim",
            "target_id": "c2",
            "old_status": "partially_supported",
            "new_status": "unsupported",
            "supporting_evidence_ids": ["e3"],
            "resolution_expectation": "partially_resolved",
        },
    )

    overwritten = merge_review_state(
        patch_state,
        {
            "claims": [
                {
                    "claim_id": "c2",
                    "claim": "Claim c2 restated by a later worker.",
                    "importance": "medium",
                    "status": "partially_supported",
                    "supporting_evidence_ids": ["e3"],
                }
            ],
            "evidence_map": [
                {
                    "evidence_id": "e2",
                    "claim_id": "c2",
                    "evidence": "A later worker repeated stale support evidence.",
                    "source": "fallback-extraction",
                    "strength": "strong",
                    "stance": "supports",
                }
            ],
        },
    )

    assert overwritten["claims"][1]["status"] == "unsupported"
    assert overwritten["_transient_status_locks"]["claim:c2"] == "unsupported"


def test_valid_patch_flaw_downgrade_commits(mock_state):
    # New semantics: a verified actionable negative *candidate* flaw is preserved
    # (cannot be routed to downgraded -> ACTIONABLE_CONCERN_PRESERVED). The valid
    # committing path for such a flaw is confirmed->downgraded, which normalizes to
    # confirmed->candidate (downgrade_final_to_candidate) to de-escalate an
    # over-confirmed grounded weakness while keeping it an active potential concern.
    mock_state["flaw_candidates"][0]["status"] = "confirmed"
    mock_state["evidence_map"][0].update(_VERIFIED_NEGATIVE_FIELDS)
    payload = {
        "action": "apply_recovery_patch",
        "target_type": "flaw",
        "target_id": "f1",
        "old_status": "confirmed",
        "new_status": "downgraded",
        "supporting_evidence_ids": ["e1"],
        "conflict_note_ids": ["conf1"],
        "resolution_expectation": "resolved",
    }

    new_state = merge_review_state(mock_state, payload)

    assert new_state["_latest_patch_log"]["recovery_validated"] is True
    assert new_state["_latest_patch_log"]["recovery_committed"] is True
    assert new_state["_latest_patch_log"]["recovery_failure_code"] == "SUCCESS"
    assert new_state["_latest_patch_log"]["recovery_patch_operation"] == "downgrade_final_to_candidate"
    assert new_state["flaw_candidates"][0]["status"] == "candidate"
    assert len(new_state["conflict_notes"]) == 0


def test_hypothesis_patch_commits_and_reformats_status(mock_state):
    payload = {
        "action": "apply_recovery_patch",
        "target_type": "hypothesis",
        "target_id": "1",
        "old_status": "active",
        "new_status": "challenged",
        "supporting_evidence_ids": ["e1"],
        "conflict_note_ids": ["conf1"],
        "resolution_expectation": "partially_resolved",
    }

    new_state = merge_review_state(mock_state, payload)

    assert new_state["_latest_patch_log"]["recovery_committed"] is True
    assert new_state["current_hypotheses"][0].startswith("[CHALLENGED]")


def test_missing_target_id(mock_state):
    payload = {
        "action": "apply_recovery_patch",
        "target_type": "flaw",
        "target_id": "",
        "old_status": "candidate",
        "new_status": "downgraded",
        "supporting_evidence_ids": ["e1"],
    }

    validation = validate_recovery_patch(mock_state, parse_recovery_payload(payload))

    assert validation["failure_code"] == "MISSING_TARGET_ID"
    assert validation["commit_allowed"] is False


def test_invalid_target_type(mock_state):
    payload = {
        "action": "apply_recovery_patch",
        "target_type": "unknown",
        "target_id": "f1",
        "old_status": "candidate",
        "new_status": "downgraded",
        "supporting_evidence_ids": ["e1"],
    }

    new_state = merge_review_state(mock_state, payload)

    assert new_state["_latest_patch_log"]["recovery_validated"] is False
    assert new_state["_latest_patch_log"]["recovery_failure_code"] == "UNKNOWN_TARGET"


def test_invalid_status_transition(mock_state):
    payload = {
        "action": "apply_recovery_patch",
        "target_type": "flaw",
        "target_id": "f1",
        "old_status": "candidate",
        "new_status": "confirmed",
        "supporting_evidence_ids": ["e1"],
    }

    new_state = merge_review_state(mock_state, payload)

    assert new_state["_latest_patch_log"]["recovery_failure_code"] == "INVALID_STATUS_TRANSITION"
    assert new_state["_latest_patch_log"]["recovery_validated"] is False


def test_insufficient_evidence(mock_state):
    payload = {
        "action": "apply_recovery_patch",
        "target_type": "flaw",
        "target_id": "f1",
        "old_status": "candidate",
        "new_status": "downgraded",
        "supporting_evidence_ids": [],
    }

    new_state = merge_review_state(mock_state, payload)

    assert new_state["_latest_patch_log"]["recovery_failure_code"] == "INSUFFICIENT_EVIDENCE"
    assert new_state["_latest_patch_log"]["recovery_validated"] is True
    assert new_state["_latest_patch_log"]["recovery_committed"] is False


def test_semantic_mismatch(mock_state):
    payload = {
        "action": "apply_recovery_patch",
        "target_type": "flaw",
        "target_id": "f1",
        "old_status": "confirmed",
        "new_status": "downgraded",
        "supporting_evidence_ids": ["e1"],
    }

    new_state = merge_review_state(mock_state, payload)

    assert new_state["_latest_patch_log"]["recovery_failure_code"] == "SEMANTIC_MISMATCH"


def test_no_effect_patch(mock_state):
    payload = {
        "action": "apply_recovery_patch",
        "target_type": "flaw",
        "target_id": "f1",
        "old_status": "candidate",
        "new_status": "candidate",
        "supporting_evidence_ids": ["e1"],
    }

    new_state = merge_review_state(mock_state, payload)

    assert new_state["_latest_patch_log"]["recovery_failure_code"] == "NO_EFFECT_PATCH"
    assert new_state["_latest_patch_log"]["recovery_validated"] is True


def test_evidence_target_mismatch(mock_state):
    payload = {
        "action": "apply_recovery_patch",
        "target_type": "flaw",
        "target_id": "f1",
        "old_status": "candidate",
        "new_status": "downgraded",
        "supporting_evidence_ids": ["e3"],
    }

    new_state = merge_review_state(mock_state, payload)

    assert new_state["_latest_patch_log"]["recovery_failure_code"] == "EVIDENCE_TARGET_MISMATCH"
    assert new_state["_latest_patch_log"]["recovery_committed"] is False


def test_blocked_by_policy(mock_state):
    payload = {
        "action": "blocked",
        "blocked_reason": "No evidence available.",
        "missing_requirements": ["grounded evidence ids"],
    }

    new_state = merge_review_state(mock_state, payload)

    assert new_state["_latest_patch_log"]["recovery_failure_code"] == "BLOCKED_BY_POLICY"
    assert new_state["_latest_patch_log"]["recovery_validated"] is False
    assert new_state["_latest_patch_log"]["recovery_blocked"] is True
    assert new_state["_latest_patch_log"]["missing_requirements"] == ["grounded evidence ids"]


def test_high_conflict_patch_without_conflict_ids_still_hits_validator(mock_state):
    payload = {
        "action": "apply_recovery_patch",
        "target_type": "flaw",
        "target_id": "f1",
        "old_status": "candidate",
        "new_status": "downgraded",
        "supporting_evidence_ids": ["e1"],
        "resolution_expectation": "resolved",
    }

    new_state = merge_review_state(mock_state, payload)

    assert new_state["_latest_patch_log"]["recovery_failure_code"] == "UNRESOLVED_CONFLICT"
    assert new_state["_latest_patch_log"]["recovery_validated"] is True
    assert new_state["_latest_patch_log"]["recovery_committed"] is False


def test_claim_patch_records_model_generated_source_by_default(mock_state):
    payload = {
        "action": "apply_recovery_patch",
        "target_type": "claim",
        "target_id": "c2",
        "old_status": "partially_supported",
        "new_status": "unsupported",
        "supporting_evidence_ids": ["e3"],
    }

    new_state = merge_review_state(mock_state, payload)

    assert new_state["_latest_patch_log"]["recovery_patch_source"] == "model_generated"


def test_claim_unsupported_patch_accepts_verified_negative_when_grounding_present(mock_state):
    state = copy.deepcopy(mock_state)
    state["evidence_quote_bank"] = [{"quote_id": "q-neg", "raw_quote": "The claim fails under the main ablation."}]
    for evidence in state["evidence_map"]:
        if evidence["evidence_id"] == "e3":
            evidence["verified_grounding_label"] = "paper_grounded_exact"
            evidence["semantic_grounding_label"] = "semantic_negative_verified"
            evidence["raw_quote"] = "The claim fails under the main ablation."
            evidence["quote_id"] = "q-neg"
            evidence["verified_quote_match_type"] = "quote_bank_id_canonical"
            evidence["verified_source_span_start"] = 10
            evidence["verified_source_span_end"] = 80
            evidence["review_negative_label"] = "review_negative_verified"

    new_state = merge_review_state(
        state,
        {
            "action": "apply_recovery_patch",
            "target_type": "claim",
            "target_id": "c2",
            "old_status": "partially_supported",
            "new_status": "unsupported",
            "supporting_evidence_ids": ["e3"],
            "resolution_expectation": "partially_resolved",
        },
    )

    assert new_state["claims"][1]["status"] == "unsupported"
    assert new_state["_latest_patch_log"]["recovery_committed"] is True
    assert new_state["_latest_patch_log"]["recovery_failure_code"] == "SUCCESS"


def test_claim_patch_with_verified_negative_normalizes_mistaken_positive_status(mock_state):
    state = copy.deepcopy(mock_state)
    state["claims"].append({"claim_id": "c3", "status": "uncertain", "supporting_evidence_ids": []})
    state["evidence_quote_bank"] = [{"quote_id": "q-neg-c3", "raw_quote": "The result remains worse than the strongest baseline."}]
    state["evidence_map"].append(
        {
            "evidence_id": "e-neg-c3",
            "claim_id": "c3",
            "strength": "missing",
            "stance": "missing",
            "verified_grounding_label": "paper_grounded_exact",
            "semantic_grounding_label": "semantic_negative_verified",
            "verified_quote_match_type": "quote_bank_raw_canonical",
            "review_negative_label": "review_negative_verified",
            "verified_source_span_start": 10,
            "verified_source_span_end": 80,
            "raw_quote": "The result remains worse than the strongest baseline.",
            "quote_id": "q-neg-c3",
        }
    )

    new_state = merge_review_state(
        state,
        {
            "action": "apply_recovery_patch",
            "target_type": "claim",
            "target_id": "c3",
            "old_status": "uncertain",
            "new_status": "partially_supported",
            "supporting_evidence_ids": ["e-neg-c3"],
            "resolution_expectation": "partially_resolved",
        },
    )

    claim = next(item for item in new_state["claims"] if item["claim_id"] == "c3")
    patch_log = new_state["_latest_patch_log"]
    assert claim["status"] == "unsupported"
    assert patch_log["recovery_committed"] is True
    assert patch_log["recovery_failure_code"] == "SUCCESS"
    assert patch_log["status_normalized_from"] == "partially_supported"
    assert patch_log["status_normalized_to"] == "unsupported"
    assert patch_log["recovery_patch_operation"] == "downgrade_claim_to_unsupported"


def test_not_assessable_gap_resolves_when_later_real_support_binds():
    state = {
        "claims": [
            {
                "claim_id": "claim-paper-fallback-1",
                "claim": "The method improves planning performance.",
                "status": "uncertain",
                "claim_origin_kind": "context_synthesized",
                "supporting_evidence_ids": [],
            }
        ],
        "evidence_map": [],
        "flaw_candidates": [],
        "evidence_gaps": [
            {
                "gap_id": "gap-fallback-1",
                "gap": "Claim claim-paper-fallback-1 lacks grounded supporting evidence.",
                "claim_id": "claim-paper-fallback-1",
                "status": "not_assessable",
                "source": "state_consistency",
                "resolution": "diagnostic_or_salvaged_claim_without_verified_support",
            }
        ],
    }

    new_state = merge_review_state(
        state,
        {
            "evidence_map": [
                {
                    "evidence_id": "e-real-support",
                    "claim_id": "claim-paper-fallback-1",
                    "evidence": "The method improves planning performance in the reported experiments.",
                    "stance": "supports",
                    "strength": "strong",
                    "verified_grounding_label": "paper_grounded_exact",
                    "semantic_grounding_label": "semantic_support_verified",
                    "raw_quote": "The method improves planning performance in the reported experiments.",
                    "source_locator": "Results section",
                }
            ]
        },
    )

    gap = next(item for item in new_state["evidence_gaps"] if item["claim_id"] == "claim-paper-fallback-1")
    assert gap["status"] == "resolved"
    assert gap["evidence_id"] == "e-real-support"
    assert gap["resolution"] == "supporting_evidence_bound"


def test_fallback_claim_status_patch_is_blocked_even_with_verified_negative_evidence():
    state = {
        "claims": [
            {
                "claim_id": "claim-paper-fallback-1",
                "claim": "Broad contribution claim from the abstract.",
                "status": "supported",
                "claim_origin_kind": "context_synthesized",
                "supporting_evidence_ids": ["e-support"],
            }
        ],
        "evidence_map": [
            {
                "evidence_id": "e-negative",
                "claim_id": "claim-paper-fallback-1",
                "evidence": "The reported result is worse than the strongest baseline.",
                "stance": "contradicts",
                "strength": "strong",
                "verified_grounding_label": "paper_grounded_exact",
                "semantic_grounding_label": "semantic_negative_verified",
                "verified_quote_match_type": "quote_bank_raw_canonical",
                "review_negative_label": "review_negative_verified",
                "verified_source_span_start": 10,
                "verified_source_span_end": 80,
                "negative_evidence_type": "negative_result",
            }
        ],
        "flaw_candidates": [],
        "conflict_notes": [],
    }

    new_state = merge_review_state(
        state,
        {
            "action": "apply_recovery_patch",
            "target_type": "claim",
            "target_id": "claim-paper-fallback-1",
            "old_status": "supported",
            "new_status": "unsupported",
            "supporting_evidence_ids": ["e-negative"],
            "resolution_expectation": "partially_resolved",
        },
    )

    claim = new_state["claims"][0]
    patch_log = new_state["_latest_patch_log"]
    assert claim["status"] == "supported"
    assert patch_log["recovery_committed"] is False
    assert patch_log["recovery_failure_code"] == "BLOCKED_BY_POLICY"
    assert patch_log["recovery_patch_operation"] == "reject_patch"
    assert patch_log["recovery_target_gate_label"] == "fallback_target"


def test_mark_contested_patch_commits_without_claim_status_downgrade(mock_state):
    state = copy.deepcopy(mock_state)
    for evidence in state["evidence_map"]:
        if evidence["evidence_id"] == "e2":
            evidence.update(
                {
                    "verified_grounding_label": "paper_grounded_exact",
                    "semantic_grounding_label": "semantic_support_verified",
                }
            )
        if evidence["evidence_id"] == "e3":
            evidence.update(
                {
                    "verified_grounding_label": "paper_grounded_exact",
                    "semantic_grounding_label": "semantic_negative_verified",
                    "verified_quote_match_type": "quote_bank_raw_canonical",
                    "review_negative_label": "review_negative_verified",
                    "verified_source_span_start": 10,
                    "verified_source_span_end": 80,
                    "negative_evidence_type": "scope_overclaim",
                    "raw_quote": "The broad setting is left for future work.",
                }
            )

    new_state = merge_review_state(
        state,
        {
            "action": "apply_recovery_patch",
            "target_type": "claim",
            "target_id": "c2",
            "old_status": "partially_supported",
            "new_status": "partially_supported",
            "supporting_evidence_ids": ["e3"],
            "resolution_expectation": "partially_resolved",
            "recovery_patch_operation": "mark_contested",
            "mark_contested": True,
        },
    )

    claim = next(item for item in new_state["claims"] if item["claim_id"] == "c2")
    patch_log = new_state["_latest_patch_log"]
    assert claim["status"] == "partially_supported"
    assert patch_log["recovery_committed"] is True
    assert patch_log["recovery_patch_operation"] == "mark_contested"
    assert patch_log["recovery_state_delta"]["contested_relation_added"] is True
    assert patch_log.get("recovery_no_effect_commit") is not True
    assert new_state["contested_relations"][0]["claim_id"] == "c2"
    assert new_state["contested_relations"][0]["negative_evidence_ids"] == ["e3"]


def test_mark_contested_persists_reviewer_absence_audit_snapshot():
    claim = "The RankHead module improves ranking accuracy on Benchmark-X."
    support_quote = "Table 1 reports RankHead module accuracy results on Benchmark-X for Ours and BERT baselines."
    ablation_inventory_quote = "Table 2: Ablation study comparing Full model, w/o encoder, and w/o decoder on Benchmark-X."
    absence_id = "evidence-reviewer-absence-claim-1-ablation-or-component-mi"
    state = {
        "paper_text": f"{claim}\n\n{support_quote}\n\n{ablation_inventory_quote}",
        "claims": [
            {
                "claim_id": "claim-1",
                "claim": claim,
                "claim_kind": "paper_extracted",
                "claim_type": "method",
                "importance": "high",
                "status": "supported",
                "claim_obligations": ["ablation_or_component"],
            }
        ],
        "reviewer_negative_candidates": [],
        "evidence_map": [
            {
                "evidence_id": "e-support",
                "claim_id": "claim-1",
                "evidence": support_quote,
                "raw_quote": support_quote,
                "source": "Table 1",
                "source_locator": "Table 1",
                "strength": "strong",
                "stance": "supports",
                "binding_status": "bound_real_claim",
                "verified_grounding_label": "paper_grounded_exact",
                "verified_quote_match_type": "exact",
                "verified_source_span_start": len(claim) + 2,
                "verified_source_span_end": len(claim) + 2 + len(support_quote) - 1,
                "semantic_grounding_label": "semantic_support_verified",
                "support_source_bucket": "empirical_result",
            }
        ],
        "flaw_candidates": [],
        "evidence_gaps": [],
        "conflict_notes": [],
        "unresolved_questions": [],
    }

    new_state = merge_review_state(
        state,
        {
            "action": "apply_recovery_patch",
            "target_type": "claim",
            "target_id": "claim-1",
            "old_status": "supported",
            "new_status": "supported",
            "supporting_evidence_ids": [absence_id],
            "resolution_expectation": "partially_resolved",
            "recovery_patch_operation": "mark_contested",
            "mark_contested": True,
            "contested_relation": {
                "claim_id": "claim-1",
                "support_evidence_ids": ["e-support"],
                "negative_evidence_ids": [absence_id],
                "final_view": "potential_concern",
                "negative_evidence_basis": "reviewer_absence_audit",
            },
        },
    )

    patch_log = new_state["_latest_patch_log"]
    assert patch_log["recovery_committed"] is True
    assert patch_log["recovery_patch_operation"] == "mark_contested"
    absence_record = next(
        item for item in new_state["evidence_map"]
        if item.get("evidence_id") == absence_id
    )
    assert absence_record["source"] == "reviewer_absence_audit"
    assert absence_record["absence_audit_snapshot_at_recovery_commit"] is True
    assert new_state["contested_relations"][0]["negative_evidence_ids"] == [absence_id]
    assert new_state["contested_relations"][0]["negative_evidence_basis"] == "reviewer_absence_audit"

    hygiene = build_decision_hygiene_view(copy.deepcopy(new_state))["decision_hygiene"]
    assert hygiene["reviewer_absence_verified_count"] == 1
    assert hygiene["reviewer_absence_verified_type_counts"]["missing_ablation"] == 1


def test_mark_contested_duplicate_relation_is_blocked_as_no_effect(mock_state):
    state = copy.deepcopy(mock_state)
    for evidence in state["evidence_map"]:
        if evidence["evidence_id"] == "e2":
            evidence.update(
                {
                    "verified_grounding_label": "paper_grounded_exact",
                    "semantic_grounding_label": "semantic_support_verified",
                }
            )
        if evidence["evidence_id"] == "e3":
            evidence.update(
                {
                    "verified_grounding_label": "paper_grounded_exact",
                    "semantic_grounding_label": "semantic_negative_verified",
                    "verified_quote_match_type": "quote_bank_raw_canonical",
                    "review_negative_label": "review_negative_verified",
                    "verified_source_span_start": 10,
                    "verified_source_span_end": 80,
                    "negative_evidence_type": "scope_overclaim",
                    "raw_quote": "The broad setting is left for future work.",
                }
            )
    state["contested_relations"] = [
        {
            "relation_id": "contested-existing",
            "claim_id": "c2",
            "negative_evidence_ids": ["e3"],
            "support_evidence_ids": ["e2"],
            "final_view": "potential_concern",
            "status": "contested",
        }
    ]

    new_state = merge_review_state(
        state,
        {
            "action": "apply_recovery_patch",
            "target_type": "claim",
            "target_id": "c2",
            "old_status": "partially_supported",
            "new_status": "partially_supported",
            "supporting_evidence_ids": ["e3"],
            "resolution_expectation": "partially_resolved",
            "recovery_patch_operation": "mark_contested",
            "mark_contested": True,
        },
    )

    patch_log = new_state["_latest_patch_log"]
    assert patch_log["recovery_committed"] is False
    assert patch_log["recovery_patch_operation"] == "reject_patch"
    assert patch_log["recovery_failure_code"] == "BLOCKED_BY_POLICY"
    assert len(new_state["contested_relations"]) == 1


def test_mark_contested_blocks_claim_status_downgrade_request(mock_state):
    state = copy.deepcopy(mock_state)
    for evidence in state["evidence_map"]:
        if evidence["evidence_id"] == "e2":
            evidence.update(
                {
                    "verified_grounding_label": "paper_grounded_exact",
                    "semantic_grounding_label": "semantic_support_verified",
                }
            )
        if evidence["evidence_id"] == "e3":
            evidence.update(
                {
                    "verified_grounding_label": "paper_grounded_exact",
                    "semantic_grounding_label": "semantic_negative_verified",
                    "verified_quote_match_type": "quote_bank_raw_canonical",
                    "review_negative_label": "review_negative_verified",
                    "verified_source_span_start": 10,
                    "verified_source_span_end": 80,
                    "negative_evidence_type": "scope_overclaim",
                    "raw_quote": "The broad setting is left for future work.",
                }
            )

    new_state = merge_review_state(
        state,
        {
            "action": "apply_recovery_patch",
            "target_type": "claim",
            "target_id": "c2",
            "old_status": "partially_supported",
            "new_status": "unsupported",
            "supporting_evidence_ids": ["e3"],
            "resolution_expectation": "partially_resolved",
            "recovery_patch_operation": "mark_contested",
            "mark_contested": True,
            "contested_relation": {
                "claim_id": "c2",
                "support_evidence_ids": ["e2"],
                "negative_evidence_ids": ["e3"],
            },
        },
    )

    claim = next(item for item in new_state["claims"] if item["claim_id"] == "c2")
    patch_log = new_state["_latest_patch_log"]
    assert claim["status"] == "partially_supported"
    assert patch_log["recovery_committed"] is False
    assert patch_log["recovery_failure_code"] == "BLOCKED_BY_POLICY"
    assert patch_log["recovery_patch_operation"] == "reject_patch"
    assert "non-destructive" in patch_log["recovery_failure_message"]


def test_claim_unsupported_patch_blocks_when_verified_positive_support_remains(mock_state):
    state = copy.deepcopy(mock_state)
    for evidence in state["evidence_map"]:
        if evidence["evidence_id"] == "e2":
            evidence.update(
                {
                    "verified_grounding_label": "paper_grounded_exact",
                    "semantic_grounding_label": "semantic_support_verified",
                }
            )
        if evidence["evidence_id"] == "e3":
            evidence.update(
                {
                    "verified_grounding_label": "paper_grounded_exact",
                    "semantic_grounding_label": "semantic_negative_verified",
                    "verified_quote_match_type": "quote_bank_raw_canonical",
                    "review_negative_label": "review_negative_verified",
                    "verified_source_span_start": 10,
                    "verified_source_span_end": 80,
                    "negative_evidence_type": "negative_result",
                    "raw_quote": "The main result is worse than the strongest baseline.",
                }
            )

    new_state = merge_review_state(
        state,
        {
            "action": "apply_recovery_patch",
            "target_type": "claim",
            "target_id": "c2",
            "old_status": "partially_supported",
            "new_status": "unsupported",
            "supporting_evidence_ids": ["e3"],
            "resolution_expectation": "partially_resolved",
        },
    )

    claim = next(item for item in new_state["claims"] if item["claim_id"] == "c2")
    patch_log = new_state["_latest_patch_log"]
    assert claim["status"] == "partially_supported"
    assert patch_log["recovery_committed"] is False
    assert patch_log["recovery_failure_code"] == "BLOCKED_BY_POLICY"
    assert patch_log["recovery_patch_operation"] == "reject_patch"
    assert "verified positive support" in patch_log["recovery_failure_message"]


def test_mark_contested_blocks_paper_salvaged_claim_patch_without_status_downgrade():
    state = {
        "claims": [
            {
                "claim_id": "claim-paper-fallback-1",
                "claim": "Paper-salvaged claim with both positive and negative grounding.",
                "status": "supported",
                "claim_kind": "paper_extracted",
                "claim_origin_kind": "raw_salvaged_claim_agent_output",
            }
        ],
        "evidence_map": [
            {
                "evidence_id": "e-pos",
                "claim_id": "claim-paper-fallback-1",
                "stance": "supports",
                "strength": "strong",
                "verified_grounding_label": "paper_grounded_exact",
                "semantic_grounding_label": "semantic_support_verified",
            },
            {
                "evidence_id": "e-neg",
                "claim_id": "claim-paper-fallback-1",
                "stance": "missing",
                "strength": "missing",
                "source": "quote-bank-negative-grounding",
                "negative_evidence_type": "negative_result",
                "verified_grounding_label": "paper_grounded_exact",
                "semantic_grounding_label": "semantic_negative_verified",
                "verified_quote_match_type": "quote_bank_raw_canonical",
                "review_negative_label": "review_negative_verified",
                "verified_source_span_start": 10,
                "verified_source_span_end": 80,
            },
        ],
        "flaw_candidates": [],
    }

    new_state = merge_review_state(
        state,
        {
            "action": "apply_recovery_patch",
            "target_type": "claim",
            "target_id": "claim-paper-fallback-1",
            "old_status": "supported",
            "new_status": "supported",
            "supporting_evidence_ids": ["e-neg"],
            "resolution_expectation": "partially_resolved",
            "recovery_patch_operation": "mark_contested",
            "mark_contested": True,
            "contested_relation": {
                "claim_id": "claim-paper-fallback-1",
                "support_evidence_ids": ["e-pos"],
                "negative_evidence_ids": ["e-neg"],
            },
        },
    )

    claim = new_state["claims"][0]
    patch_log = new_state["_latest_patch_log"]
    assert claim["status"] == "supported"
    assert patch_log["recovery_committed"] is False
    assert patch_log["recovery_failure_code"] == "BLOCKED_BY_POLICY"
    assert patch_log["recovery_patch_operation"] == "reject_patch"
    assert patch_log["recovery_target_gate_label"] == "fallback_target"


def test_mark_contested_flaw_target_allows_paper_salvaged_relation_without_status_downgrade():
    state = {
        "claims": [
            {
                "claim_id": "claim-paper-fallback-1",
                "claim": "Paper-salvaged claim with both positive and negative grounding.",
                "status": "supported",
                "claim_kind": "paper_extracted",
                "claim_origin_kind": "raw_salvaged_claim_agent_output",
            }
        ],
        "evidence_map": [
            {
                "evidence_id": "e-pos",
                "claim_id": "claim-paper-fallback-1",
                "stance": "supports",
                "strength": "strong",
                "verified_grounding_label": "paper_grounded_exact",
                "semantic_grounding_label": "semantic_support_verified",
            },
            {
                "evidence_id": "e-neg",
                "claim_id": "claim-paper-fallback-1",
                "stance": "missing",
                "strength": "missing",
                "source": "quote-bank-negative-grounding",
                "negative_evidence_type": "negative_result",
                "verified_grounding_label": "paper_grounded_exact",
                "semantic_grounding_label": "semantic_negative_verified",
                "verified_quote_match_type": "quote_bank_raw_canonical",
                "review_negative_label": "review_negative_verified",
                "verified_source_span_start": 10,
                "verified_source_span_end": 80,
            },
        ],
        "flaw_candidates": [
            {
                "flaw_id": "flaw-neg",
                "status": "candidate",
                "related_claim_ids": ["claim-paper-fallback-1"],
                "evidence_ids": ["e-neg"],
                "negative_evidence_ids": ["e-neg"],
                "negative_evidence_type": "negative_result",
            }
        ],
    }

    new_state = merge_review_state(
        state,
        {
            "action": "apply_recovery_patch",
            "target_type": "flaw",
            "target_id": "flaw-neg",
            "old_status": "candidate",
            "new_status": "candidate",
            "supporting_evidence_ids": ["e-neg"],
            "resolution_expectation": "partially_resolved",
            "recovery_patch_operation": "mark_contested",
            "mark_contested": True,
            "contested_relation": {
                "claim_id": "claim-paper-fallback-1",
                "support_evidence_ids": ["e-pos"],
                "negative_evidence_ids": ["e-neg"],
            },
        },
    )

    claim = new_state["claims"][0]
    flaw = new_state["flaw_candidates"][0]
    patch_log = new_state["_latest_patch_log"]
    assert claim["status"] == "supported"
    assert flaw["status"] == "candidate"
    assert patch_log["recovery_committed"] is True
    assert patch_log["recovery_patch_operation"] == "mark_contested"
    assert patch_log["recovery_target_gate_label"] == "negative_verified_target"
    assert patch_log["recovery_state_delta"]["contested_relation_added"] is True
    assert patch_log.get("recovery_no_effect_commit") is not True
    assert new_state["contested_relations"][0]["claim_id"] == "claim-paper-fallback-1"


def _claim_requirement_gap_state():
    return {
        "claims": [
            {
                "claim_id": "claim-1",
                "claim": "The method outperforms strong baselines and generalizes across diverse datasets.",
                "claim_type": "empirical",
                "importance": "high",
                "claim_kind": "paper_extracted",
                "status": "supported",
            }
        ],
        "evidence_map": [
            {
                "evidence_id": "e-method-1",
                "claim_id": "claim-1",
                "evidence": "The method uses a reranking module.",
                "source_locator": "Section 3",
                "raw_quote": "The method uses a reranking module trained with a contrastive objective.",
                "stance": "supports",
                "strength": "medium",
                "binding_status": "bound_real_claim",
                "verified_grounding_label": "paper_grounded_exact",
                "semantic_grounding_label": "semantic_support_verified",
                "support_source_bucket": "method_or_approach",
            }
        ],
        "flaw_candidates": [],
        "conflict_notes": [],
        "unresolved_questions": [],
        "evidence_gaps": [],
    }


def test_record_diagnosis_pending_concern_commits_without_claim_or_flaw_status_change():
    state = _claim_requirement_gap_state()
    hygiene = build_decision_hygiene_view(copy.deepcopy(state))["decision_hygiene"]
    pre_verified_negative_flaw_count = hygiene["verified_negative_flaw_count"]
    gap = hygiene["claim_requirement_gap_items"][0]

    new_state = merge_review_state(
        state,
        {
            "action": "apply_recovery_patch",
            "target_type": "claim_requirement_gap",
            "target_id": gap["gap_id"],
            "old_status": "open",
            "new_status": "recorded",
            "supporting_evidence_ids": [],
            "missing_requirements": gap["missing_requirements"],
            "missing_negative_types": gap["missing_negative_types"],
            "resolution_expectation": "partially_resolved",
            "recovery_patch_operation": "record_diagnosis_pending_concern",
            "diagnosis_pending_concern": {
                "claim_id": "claim-1",
                "missing_requirements": gap["missing_requirements"],
                "missing_negative_types": gap["missing_negative_types"],
                "final_view": "potential_concern",
            },
        },
    )

    patch_log = new_state["_latest_patch_log"]
    assert new_state["claims"][0]["status"] == "supported"
    assert new_state["flaw_candidates"] == []
    assert patch_log["recovery_committed"] is True
    assert patch_log["recovery_patch_operation"] == "record_diagnosis_pending_concern"
    assert patch_log["recovery_target_gate_label"] == "diagnosis_pending_target"
    assert patch_log["recovery_state_delta"]["diagnosis_pending_concern_added"] is True
    assert new_state["diagnosis_pending_concerns"][0]["claim_id"] == "claim-1"
    assert new_state["diagnosis_pending_concerns"][0]["grounding_status"] == "diagnosis_pending_verification"
    assert new_state["diagnosis_pending_concerns"][0]["basis"] == "claim_requirement_vs_verified_support"
    view = build_decision_hygiene_view(copy.deepcopy(new_state))
    assert view["decision_hygiene"]["verified_negative_flaw_count"] == pre_verified_negative_flaw_count
    assert view["decision_hygiene"]["diagnosis_pending_concern_recorded_count"] == 1
    turn_log = build_turn_log(
        2,
        {
            "action_type": "challenge_previous_hypothesis",
            "effective_action_type": "challenge_previous_hypothesis",
            "turn_mode": "recovery_patch",
        },
        [{"agent_id": "Critique Agent", "payload": new_state["_latest_patch_log"]}],
        new_state,
        revision_events=new_state.get("revision_log", []),
    )
    assert turn_log["recovery_effective_repair"] is False
    assert turn_log["recovery_layer"] == "diagnosis_pending_recorded"
    assert turn_log["recovery_layer_diagnosis_pending_recorded"] is True
    assert turn_log["recovery_no_effect_commit"] is False
    assert turn_log["diagnosis_pending_concern_claim_id"] == "claim-1"


def test_record_diagnosis_pending_concern_layer_uses_state_delta_without_revision_event():
    state = _claim_requirement_gap_state()
    hygiene = build_decision_hygiene_view(copy.deepcopy(state))["decision_hygiene"]
    gap = hygiene["claim_requirement_gap_items"][0]

    new_state = merge_review_state(
        state,
        {
            "action": "apply_recovery_patch",
            "target_type": "claim_requirement_gap",
            "target_id": gap["gap_id"],
            "old_status": "open",
            "new_status": "recorded",
            "supporting_evidence_ids": [],
            "missing_requirements": gap["missing_requirements"],
            "missing_negative_types": gap["missing_negative_types"],
            "resolution_expectation": "partially_resolved",
            "recovery_patch_operation": "record_diagnosis_pending_concern",
        },
    )

    turn_log = build_turn_log(
        2,
        {
            "action_type": "challenge_previous_hypothesis",
            "effective_action_type": "challenge_previous_hypothesis",
            "turn_mode": "recovery_patch",
        },
        [{"agent_id": "Critique Agent", "payload": new_state["_latest_patch_log"]}],
        new_state,
        revision_events=[],
    )

    assert turn_log["recovery_layer"] == "diagnosis_pending_recorded"
    assert turn_log["recovery_layer_state_mutation_applied"] is True
    assert turn_log["recovery_layer_diagnosis_pending_recorded"] is True
    assert turn_log["recovery_effective_repair"] is False
    assert turn_log["recovery_no_effect_commit"] is False


def test_record_diagnosis_pending_concern_duplicate_is_no_effect():
    state = _claim_requirement_gap_state()
    hygiene = build_decision_hygiene_view(copy.deepcopy(state))["decision_hygiene"]
    gap = hygiene["claim_requirement_gap_items"][0]
    payload = {
        "action": "apply_recovery_patch",
        "target_type": "claim_requirement_gap",
        "target_id": gap["gap_id"],
        "old_status": "open",
        "new_status": "recorded",
        "supporting_evidence_ids": [],
        "missing_requirements": gap["missing_requirements"],
        "missing_negative_types": gap["missing_negative_types"],
        "resolution_expectation": "partially_resolved",
        "recovery_patch_operation": "record_diagnosis_pending_concern",
    }

    first_state = merge_review_state(state, payload)
    second_state = merge_review_state(first_state, payload)

    patch_log = second_state["_latest_patch_log"]
    assert len(second_state["diagnosis_pending_concerns"]) == 1
    assert patch_log["recovery_committed"] is False
    assert patch_log["recovery_patch_operation"] == "reject_patch"
    assert patch_log["recovery_failure_code"] == "NO_EFFECT_PATCH"


def test_record_diagnosis_pending_concern_rejects_fallback_claim_gap_target():
    state = {
        "claims": [
            {
                "claim_id": "claim-paper-fallback-1",
                "claim": "The recovered text appears to ask what the paper proposes.",
                "claim_type": "empirical",
                "claim_kind": "paper_extracted",
                "claim_origin_kind": "raw_salvaged_claim_agent_output",
                "status": "supported",
            }
        ],
        "evidence_map": [],
        "flaw_candidates": [],
    }

    new_state = merge_review_state(
        state,
        {
            "action": "apply_recovery_patch",
            "target_type": "claim_requirement_gap",
            "target_id": "claim-paper-fallback-1",
            "old_status": "open",
            "new_status": "recorded",
            "missing_requirements": ["baseline_or_comparison"],
            "recovery_patch_operation": "record_diagnosis_pending_concern",
        },
    )

    patch_log = new_state["_latest_patch_log"]
    assert patch_log["recovery_committed"] is False
    assert patch_log["recovery_failure_code"] == "UNKNOWN_TARGET"
    assert "diagnosis_pending_concerns" not in new_state


def test_downgraded_flaw_negative_ids_do_not_report_active_misbinding():
    state = {
        "claims": [{"claim_id": "c1", "claim": "The method improves results.", "status": "supported"}],
        "evidence_map": [
            {
                "evidence_id": "e-neutral",
                "claim_id": "c1",
                "evidence": "Table 2 reports comparison results.",
                "stance": "missing",
                "strength": "missing",
                "verified_grounding_label": "",
            }
        ],
        "flaw_candidates": [
            {
                "flaw_id": "f-archived",
                "status": "downgraded",
                "related_claim_ids": ["c1"],
                "evidence_ids": ["e-neutral"],
                "negative_evidence_ids": ["e-neutral"],
            }
        ],
    }

    view = build_decision_hygiene_view(state)
    hygiene = view["decision_hygiene"]
    assert hygiene["negative_grounding_conflict_count"] == 0
    assert hygiene["state_contamination_type_counts"].get("evidence_misbinding", 0) == 0


def test_claim_unsupported_patch_rejects_unverified_negative_when_grounding_present(mock_state):
    state = copy.deepcopy(mock_state)
    state["evidence_quote_bank"] = [{"quote_id": "q-neg", "raw_quote": "The claim fails under the main ablation."}]
    for evidence in state["evidence_map"]:
        if evidence["evidence_id"] == "e3":
            evidence["verified_grounding_label"] = "not_verified_paraphrase_only"

    new_state = merge_review_state(
        state,
        {
            "action": "apply_recovery_patch",
            "target_type": "claim",
            "target_id": "c2",
            "old_status": "partially_supported",
            "new_status": "unsupported",
            "supporting_evidence_ids": ["e3"],
            "resolution_expectation": "partially_resolved",
        },
    )

    assert new_state["claims"][1]["status"] == "partially_supported"
    assert new_state["_latest_patch_log"]["recovery_committed"] is False
    assert new_state["_latest_patch_log"]["recovery_failure_code"] == "EVIDENCE_SEMANTIC_MISMATCH"
    assert "verified paper-grounded negative evidence" in new_state["_latest_patch_log"]["recovery_failure_message"]



def test_claim_unsupported_patch_rejects_system_missing_marker_with_quote_bank(mock_state):
    state = copy.deepcopy(mock_state)
    state["evidence_quote_bank"] = [
        {"quote_id": "q-pos", "raw_quote": "The table reports a verified positive result."}
    ]
    state["evidence_map"].append(
        {
            "evidence_id": "evidence-recovery-missing-c2",
            "claim_id": "c2",
            "strength": "missing",
            "stance": "missing",
            "source": "system recovery salvage",
            "evidence": "Recovery could not verify this claim because required evidence is missing or inaccessible.",
            "verified_grounding_label": "missing_quote",
        }
    )

    new_state = merge_review_state(
        state,
        {
            "action": "apply_recovery_patch",
            "target_type": "claim",
            "target_id": "c2",
            "old_status": "partially_supported",
            "new_status": "unsupported",
            "supporting_evidence_ids": ["evidence-recovery-missing-c2"],
            "resolution_expectation": "partially_resolved",
        },
    )

    patch_log = new_state["_latest_patch_log"]
    assert new_state["claims"][1]["status"] == "partially_supported"
    assert patch_log["recovery_committed"] is False
    assert patch_log["recovery_failure_code"] == "EVIDENCE_SEMANTIC_MISMATCH"
    assert "system recovery missing markers" in patch_log["recovery_failure_message"]



def test_claim_unsupported_patch_rejects_partial_support_with_lacks_language(mock_state):
    state = copy.deepcopy(mock_state)
    state["evidence_quote_bank"] = [
        {"quote_id": "q-partial", "raw_quote": "The method updates only classifier network."}
    ]
    state["evidence_map"].append(
        {
            "evidence_id": "e-partial-lacks",
            "claim_id": "c2",
            "strength": "medium",
            "stance": "partially_supports",
            "source": "Methodology",
            "evidence": "The method updates only classifier network but lacks explicit latent causal definition.",
            "verified_grounding_label": "paper_grounded_exact",
            "quote_id": "q-partial",
        }
    )

    new_state = merge_review_state(
        state,
        {
            "action": "apply_recovery_patch",
            "target_type": "claim",
            "target_id": "c2",
            "old_status": "partially_supported",
            "new_status": "unsupported",
            "supporting_evidence_ids": ["e-partial-lacks"],
            "resolution_expectation": "partially_resolved",
        },
    )

    patch_log = new_state["_latest_patch_log"]
    assert new_state["claims"][1]["status"] == "partially_supported"
    assert patch_log["recovery_committed"] is False
    assert patch_log["recovery_failure_code"] == "EVIDENCE_SEMANTIC_MISMATCH"
    assert "support/partially-support evidence" in patch_log["recovery_failure_message"]


def test_recovery_commit_records_state_quality_delta(mock_state):
    new_state = merge_review_state(
        mock_state,
        {
            "action": "apply_recovery_patch",
            "target_type": "claim",
            "target_id": "c1",
            "old_status": "supported",
            "new_status": "unsupported",
            "supporting_evidence_ids": ["e1"],
            "conflict_note_ids": ["conf1"],
            "resolution_expectation": "resolved",
        },
    )

    patch_log = new_state["_latest_patch_log"]
    assert patch_log["recovery_committed"] is True
    assert patch_log["recovery_state_delta"]["delta"]["open_conflict_count"] == -1
    assert patch_log["recovery_consistency_improved"] is True
    assert patch_log["negative_recovery_commit"] is False
    assert patch_log["recovery_patch_operation"] == "downgrade_claim_to_unsupported"
    assert patch_log["recovery_target_gate_label"] == "real_target"
    assert patch_log["recovery_target_commit_allowed"] is True


def test_recovery_patch_commit_emits_revision_log_entry(mock_state):
    """A committed recovery patch that produces a real status transition must
    append an entry to ``state['revision_log']``.

    Without this, the env-level diff tracker treats every recovery commit as
    a no-op state change and the per-turn ``commit_applied`` /
    ``recovery_layer_state_mutation_applied`` counters falsely report
    ``False`` even when the entity genuinely transitioned (root cause of the
    V16 ``recovery_committed=True`` vs ``recovery_success=False`` gap).
    """

    previous_revision_count = len(mock_state.get("revision_log", []))

    new_state = merge_review_state(
        mock_state,
        {
            "action": "apply_recovery_patch",
            "target_type": "claim",
            "target_id": "c1",
            "old_status": "supported",
            "new_status": "unsupported",
            "supporting_evidence_ids": ["e1"],
            "conflict_note_ids": ["conf1"],
            "resolution_expectation": "resolved",
        },
    )

    assert new_state["_latest_patch_log"]["recovery_committed"] is True
    assert new_state["claims"][0]["status"] == "unsupported"
    new_events = new_state.get("revision_log", [])[previous_revision_count:]
    assert any(
        event.get("entity_type") == "claim"
        and event.get("entity_id") == "c1"
        and event.get("field") == "status"
        and event.get("reason") == "recovery_patch_committed"
        for event in new_events
    ), f"missing recovery revision event: {new_events!r}"


def test_recovery_patch_revision_log_supports_flaw_downgrade(mock_state):
    """The same revision-log emission must work for flaw-target patches."""

    previous_revision_count = len(mock_state.get("revision_log", []))
    # New semantics: a verified actionable negative is preserved, so
    # route_to_assessment_limitation only commits for an UNVERIFIED (not
    # paper-grounded) negative flaw. Use an unverified typed negative so the
    # downgrade routes to assessment limitation and emits a revision event.
    mock_state["evidence_map"][0].update(
        {
            "stance": "missing",
            "strength": "missing",
            "negative_evidence_type": "missing_baseline",
            "raw_quote": "We compare only against method A; method B is not included in our experiments.",
            "source": "Section 5 Experiments",
        }
    )
    mock_state["flaw_candidates"][0]["negative_evidence_ids"] = ["e1"]

    new_state = merge_review_state(
        mock_state,
        {
            "action": "apply_recovery_patch",
            "target_type": "flaw",
            "target_id": "f1",
            "old_status": "candidate",
            "new_status": "downgraded",
            "supporting_evidence_ids": ["e1"],
        },
    )

    assert new_state["_latest_patch_log"]["recovery_committed"] is True
    assert new_state["flaw_candidates"][0]["status"] == "downgraded"
    assert new_state["_latest_patch_log"]["recovery_patch_operation"] == "route_to_assessment_limitation"
    assert new_state["_latest_patch_log"]["recovery_target_gate_label"] == "real_target"
    new_events = new_state.get("revision_log", [])[previous_revision_count:]
    assert any(
        event.get("entity_type") == "flaw"
        and event.get("entity_id") == "f1"
        and event.get("field") == "status"
        and event.get("before") == "candidate"
        and event.get("after") == "downgraded"
        and event.get("reason") == "recovery_patch_committed"
        for event in new_events
    ), f"missing recovery revision event: {new_events!r}"


def test_recovery_delta_quote_bank_limitation_cleanup_not_counted_as_assessment_limitation():
    # New semantics: quote-bank-negative-grounding is an UNTRUSTED verifier source, so a
    # quote-bank scope_limitation flaw downgrade no longer counts as a trusted route to an
    # assessment limitation (assessment_limitation_flaw_count stays 0, nothing tolerated-worsened).
    before = {
        "claims": [{"claim_id": "c1", "claim": "The method improves accuracy.", "status": "supported"}],
        "evidence_map": [
            {
                "evidence_id": "e-negative",
                "claim_id": "c1",
                "evidence": "A limitation quote.",
                "raw_quote": "A limitation quote.",
                "stance": "missing",
                "strength": "missing",
                "source": "quote-bank-negative-grounding",
                "negative_evidence_type": "scope_limitation",
            }
        ],
        "flaw_candidates": [
            {
                "flaw_id": "f1",
                "status": "candidate",
                "flaw": "Potential limitation.",
                "severity": "minor",
                "related_claim_ids": ["c1"],
                "evidence_ids": ["e-negative"],
                "negative_evidence_ids": ["e-negative"],
                "source": "quote-bank-negative-grounding",
                "negative_evidence_type": "scope_limitation",
            }
        ],
        "evidence_gaps": [],
        "unresolved_questions": [],
        "conflict_notes": [],
    }
    after = copy.deepcopy(before)
    after["flaw_candidates"][0]["status"] = "downgraded"

    delta = _build_recovery_state_delta(before, after)

    assert delta["delta"]["negative_grounding_conflict_count"] == -1
    assert delta["delta"]["assessment_limitation_flaw_count"] == 0
    assert delta["tolerated_worsened_keys"] == []
    assert delta["worsened_keys"] == []
    assert delta["consistency_improved"] is True


def test_recovery_patch_blocks_no_effect_assessment_limitation_downgrade():
    state = {
        "claims": [
            {
                "claim_id": "claim-paper-fallback-1",
                "claim": "Paper-salvaged fallback claim.",
                "status": "supported",
                "claim_kind": "paper_extracted",
                "claim_origin_kind": "raw_salvaged_claim_agent_output",
            }
        ],
        "evidence_map": [
            {
                "evidence_id": "e-negative-scope",
                "claim_id": "claim-paper-fallback-1",
                "evidence": "The comparison table is only contextual and does not contest a real claim.",
                "raw_quote": "The comparison table is only contextual and does not contest a real claim.",
                "stance": "missing",
                "strength": "missing",
                "source": "quote-bank-negative-grounding",
                "verified_grounding_label": "paper_grounded_exact",
                "semantic_grounding_label": "semantic_negative_verified",
                "verified_quote_match_type": "quote_bank_raw_canonical",
                "review_negative_label": "review_negative_verified",
                "verified_source_span_start": 10,
                "verified_source_span_end": 80,
                "negative_evidence_type": "scope_limitation",
            }
        ],
        "flaw_candidates": [
            {
                "flaw_id": "f-scope",
                "status": "candidate",
                "title": "Scope limitation",
                "description": "Scope limitation",
                "severity": "minor",
                "related_claim_ids": ["claim-paper-fallback-1"],
                "evidence_ids": ["e-negative-scope"],
                "negative_evidence_ids": ["e-negative-scope"],
                "source": "quote-bank-negative-grounding",
                "negative_evidence_type": "scope_limitation",
                "grounding_status": "grounded_candidate",
            }
        ],
        "evidence_gaps": [],
        "unresolved_questions": [],
        "conflict_notes": [],
    }

    new_state = merge_review_state(
        state,
        {
            "action": "apply_recovery_patch",
            "target_type": "flaw",
            "target_id": "f-scope",
            "old_status": "candidate",
            "new_status": "downgraded",
            "supporting_evidence_ids": ["e-negative-scope"],
        },
    )

    patch_log = new_state["_latest_patch_log"]
    assert new_state["flaw_candidates"][0]["status"] == "candidate"
    assert patch_log["recovery_committed"] is False
    assert patch_log["recovery_failure_code"] == "BLOCKED_BY_POLICY"
    assert patch_log["recovery_patch_operation"] == "reject_patch"
    assert patch_log["recovery_target_gate_label"] == "real_target"
    assert patch_log["recovery_terminal"] is True
    assert patch_log["recovery_terminal_reason"] == "assessment_limitation_no_effect_preserved"
    assert patch_log["recovery_repeat_allowed"] is False


def test_recovery_patch_can_deescalate_confirmed_flaw_to_candidate(mock_state):
    mock_state["flaw_candidates"][0]["status"] = "confirmed"

    new_state = merge_review_state(
        mock_state,
        {
            "action": "apply_recovery_patch",
            "target_type": "flaw",
            "target_id": "f1",
            "old_status": "confirmed",
            "new_status": "candidate",
            "supporting_evidence_ids": ["e1"],
            "resolution_expectation": "partially_resolved",
        },
    )

    assert new_state["_latest_patch_log"]["recovery_committed"] is True
    assert new_state["flaw_candidates"][0]["status"] == "candidate"
    assert new_state["_latest_patch_log"]["recovery_patch_operation"] == "downgrade_final_to_candidate"


def test_recovery_patch_blocks_actionable_candidate_to_assessment_limitation(mock_state):
    mock_state["evidence_map"][0].update(
        {
            "verified_grounding_label": "paper_grounded_exact",
            "semantic_grounding_label": "semantic_negative_verified",
            "verified_quote_match_type": "quote_bank_raw_canonical",
            "review_negative_label": "review_negative_verified",
            "verified_source_span_start": 10,
            "verified_source_span_end": 80,
            "negative_evidence_type": "negative_result",
            "raw_quote": "The method performs worse than the baseline.",
        }
    )
    mock_state["flaw_candidates"][0]["negative_evidence_ids"] = ["e1"]

    new_state = merge_review_state(
        mock_state,
        {
            "action": "apply_recovery_patch",
            "target_type": "flaw",
            "target_id": "f1",
            "old_status": "candidate",
            "new_status": "downgraded",
            "supporting_evidence_ids": ["e1"],
            "resolution_expectation": "partially_resolved",
        },
    )

    assert new_state["_latest_patch_log"]["recovery_committed"] is False
    assert new_state["_latest_patch_log"]["recovery_failure_code"] == "ACTIONABLE_CONCERN_PRESERVED"
    assert new_state["_latest_patch_log"]["recovery_target_gate_label"] == "negative_verified_target"
    assert new_state["_latest_patch_log"]["recovery_terminal"] is True
    assert new_state["_latest_patch_log"]["recovery_terminal_reason"] == "verified_actionable_negative_concern_preserved"
    assert new_state["_latest_patch_log"]["recovery_repeat_allowed"] is False
    assert new_state["flaw_candidates"][0]["status"] == "candidate"


def test_recovery_patch_normalizes_confirmed_actionable_downgrade_to_candidate(mock_state):
    mock_state["evidence_map"][0].update(
        {
            "verified_grounding_label": "paper_grounded_exact",
            "semantic_grounding_label": "semantic_negative_verified",
            "verified_quote_match_type": "quote_bank_raw_canonical",
            "review_negative_label": "review_negative_verified",
            "verified_source_span_start": 10,
            "verified_source_span_end": 80,
            "negative_evidence_type": "negative_result",
            "raw_quote": "The method performs worse than the baseline.",
        }
    )
    mock_state["flaw_candidates"][0]["status"] = "confirmed"
    mock_state["flaw_candidates"][0]["negative_evidence_ids"] = ["e1"]

    new_state = merge_review_state(
        mock_state,
        {
            "action": "apply_recovery_patch",
            "target_type": "flaw",
            "target_id": "f1",
            "old_status": "confirmed",
            "new_status": "downgraded",
            "supporting_evidence_ids": ["e1"],
            "resolution_expectation": "partially_resolved",
        },
    )

    assert new_state["_latest_patch_log"]["recovery_committed"] is True
    assert new_state["flaw_candidates"][0]["status"] == "candidate"
    assert new_state["_latest_patch_log"]["recovery_patch_operation"] == "downgrade_final_to_candidate"
    assert new_state["_latest_patch_log"]["new_status"] == "candidate"
