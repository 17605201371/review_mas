import copy
import pytest

from agent_system.environments.env_package.review.recovery_patch import parse_recovery_payload
from agent_system.environments.env_package.review.recovery_validator import validate_recovery_patch
from agent_system.environments.env_package.review.state import build_decision_hygiene_view, merge_review_state


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

    new_state = merge_review_state(mock_state, payload)

    assert new_state["_latest_patch_log"]["recovery_validated"] is True
    assert new_state["_latest_patch_log"]["recovery_committed"] is True
    assert new_state["_latest_patch_log"]["recovery_failure_code"] == "SUCCESS"
    assert new_state["flaw_candidates"][0]["status"] == "downgraded"
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
    assert patch_log["recovery_patch_operation"] == "mark_contested"


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
    assert patch_log["recovery_patch_operation"] == "mark_contested"
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
