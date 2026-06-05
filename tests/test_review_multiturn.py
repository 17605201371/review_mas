from agent_system.environments.env_package.review.envs import ReviewEnv
from agent_system.environments.env_package.review.state import (
    build_turn_action,
    create_initial_review_state,
    merge_review_state,
    normalize_manager_payload,
    parse_turn_action,
    render_final_review,
    _preserve_colliding_evidence_ids,
)


def _manager_payload(decision: str, final_report: str = ""):
    return {
        "decision": decision,
        "selected_agents": ["Claim Agent"] if decision == "continue" else [],
        "focus": "inspect the paper's main contribution",
        "rationale": "start from the central claim before deciding",
        "dialogue_summary": "The review is building an evidence-grounded understanding of the main claim.",
        "unresolved_questions": ["Is the main claim actually supported by the reported experiments?"],
        "claims": [],
        "evidence_map": [],
        "flaw_candidates": [],
        "recommendation": "undecided",
        "final_decision": "reject" if decision == "finalize" else "undecided",
        "final_report": final_report,
    }





def test_render_final_review_includes_grounded_criterion_section_without_changing_decision():
    state = {
        "claims": [
            {
                "claim_id": "claim-1",
                "claim": "The method improves benchmark accuracy using a new reranking architecture.",
                "importance": "high",
                "status": "supported",
                "supporting_evidence_ids": ["evidence-1", "evidence-2"],
            }
        ],
        "evidence_map": [
            {
                "evidence_id": "evidence-1",
                "claim_id": "claim-1",
                "evidence": "The method section describes the reranking architecture and training objective.",
                "source": "method section",
                "strength": "strong",
                "stance": "supports",
                "binding_status": "bound_real_claim",
            },
            {
                "evidence_id": "evidence-2",
                "claim_id": "claim-1",
                "evidence": "The results table reports accuracy gains over the baseline.",
                "source": "results table",
                "strength": "strong",
                "stance": "supports",
                "binding_status": "bound_real_claim",
            },
        ],
        "flaw_candidates": [],
        "unresolved_questions": [],
        "dialogue_summary": "The review found grounded support for the main contribution.",
    }

    report = render_final_review(state, {})

    assert report.startswith("Review Diagnostic Report")
    assert "Final Decision:" not in report.split("\n7. Audit Trace", 1)[0]
    assert "4. Criterion Assessment" in report
    assert "Novelty / Originality" in report
    assert "Significance / Contribution" in report
    assert "Technical Soundness" in report
    assert "Empirical Adequacy" in report
    assert "Clarity / Reproducibility" in report
    assert "evidence-1" in report
    assert "evidence-2" in report
    assert "Criterion assessments are diagnostic notes for human review" in report


def test_normalize_manager_payload_supports_action_targets_and_clarification():
    payload = normalize_manager_payload(
        {
            "decision": "continue",
            "action_type": "ask_user_clarification",
            "selected_agents": [],
            "focus": "Resolve the most important open issue.",
            "rationale": "The review target is ambiguous.",
            "target_claim_ids": ["claim-1"],
            "target_hypotheses": ["The main result may depend on one benchmark."],
            "requires_clarification": True,
            "clarification_question": "Should the review prioritize evidence quality or novelty?",
            "summary_update": "The manager needs clarification before the next specialist turn.",
        }
    )

    assert payload["action_type"] == "ask_user_clarification"
    assert payload["requires_clarification"] is True
    assert payload["clarification_question"] == "Should the review prioritize evidence quality or novelty?"
    assert payload["target_claim_ids"] == ["claim-1"]
    assert payload["target_hypotheses"]

def test_parse_turn_action_preserves_selected_agents_without_whitelist():
    action = build_turn_action(
        manager_payload=_manager_payload("continue"),
        worker_payloads=[],
        mode="s4",
        turn_id=1,
    )

    parsed = parse_turn_action(action, available_agents=None)

    assert parsed["manager"]["selected_agents"] == ["Claim Agent"]


def test_merge_review_state_records_revisions_and_conflicts():
    state = create_initial_review_state(mode="s4")
    state = merge_review_state(
        state,
        {
            "claims": [
                {
                    "claim_id": "claim-main",
                    "claim": "The proposed reranker improves retrieval accuracy over prior systems.",
                    "importance": "high",
                    "status": "uncertain",
                }
            ],
            "flaw_candidates": [
                {
                    "flaw_id": "flaw-main",
                    "title": "Missing ablation",
                    "description": "The paper does not isolate the contribution of the reranker.",
                    "severity": "major",
                    "status": "candidate",
                    "related_claim_ids": ["claim-main"],
                    "evidence_ids": [],
                    "confidence": 0.7,
                }
            ],
            "unresolved_questions": [
                {"question": "Where is the strongest evidence for the reranker gain?", "status": "open"}
            ],
            "evidence_gaps": ["Need an ablation that isolates the reranker contribution."],
            "current_hypotheses": ["The main claim may be overstated."],
        },
    )

    state = merge_review_state(
        state,
        {
            "claims": [
                {
                    "claim_id": "claim-main",
                    "claim": "The proposed reranker improves retrieval accuracy over prior systems.",
                    "importance": "high",
                    "status": "supported",
                    "supporting_evidence_ids": ["evidence-1"],
                }
            ],
            "evidence_map": [
                {
                    "evidence_id": "evidence-1",
                    "claim_id": "claim-main",
                    "evidence": "Table 2 reports a counterexample setting that weakens the broad claim.",
                    "source": "Table 2",
                    "strength": "strong",
                    "stance": "contradicts",
                }
            ],
            "flaw_candidates": [
                {
                    "flaw_id": "flaw-main",
                    "title": "Missing ablation",
                    "description": "The paper does not isolate the contribution of the reranker.",
                    "severity": "major",
                    "status": "retracted",
                    "related_claim_ids": ["claim-main"],
                    "evidence_ids": ["evidence-1"],
                    "confidence": 0.2,
                }
            ],
            "unresolved_questions": [
                {"question": "Where is the strongest evidence for the reranker gain?", "status": "resolved"}
            ],
        },
    )

    assert state["claims"][0]["status"] == "uncertain"
    assert state["flaw_candidates"][0]["status"] == "retracted"
    assert state["unresolved_questions"][0]["status"] == "resolved"
    assert any(event["entity_type"] == "claim" and event["field"] == "status" for event in state["revision_log"])
    assert any(event["entity_type"] == "flaw" and event["field"] == "status" for event in state["revision_log"])
    assert any("conflicts with claim" in note["note"] or "should be rechecked" in note["note"] for note in state["conflict_notes"])
    assert state["revision_summary"]
    assert state["conflict_summary"]
    assert state["risk_profile"]["readiness"] == "not_ready"
    assert any(
        "lacks grounded supporting evidence" in gap["gap"]
        and gap["status"] == "converted"
        and gap["resolution"] == "converted_to_evidence_conflict"
        for gap in state["evidence_gaps"]
    )




def test_merge_review_state_guards_invalid_lifecycle_transitions():
    state = create_initial_review_state(mode="s4")
    state = merge_review_state(
        state,
        {
            "claims": [
                {
                    "claim_id": "claim-old",
                    "claim": "An earlier formulation was replaced by a newer one.",
                    "status": "superseded",
                }
            ],
            "unresolved_questions": [
                {"question": "Is the old formulation still relevant?", "status": "resolved"}
            ],
        },
    )

    state = merge_review_state(
        state,
        {
            "claims": [
                {
                    "claim_id": "claim-old",
                    "claim": "An earlier formulation was replaced by a newer one.",
                    "status": "supported",
                }
            ],
            "unresolved_questions": [
                {"question": "Is the old formulation still relevant?", "status": "deferred"}
            ],
        },
    )

    assert state["claims"][0]["status"] == "superseded"
    assert state["unresolved_questions"][0]["status"] == "resolved"
    assert any(note.get("conflict_type") == "lifecycle_guard" for note in state["conflict_notes"])


def test_merge_review_state_derives_anchor_gaps_and_revision_reasons():
    state = create_initial_review_state(mode="s4")
    state = merge_review_state(
        state,
        {
            "claims": [
                {
                    "claim_id": "claim-main",
                    "claim": "The system improves retrieval.",
                    "status": "uncertain",
                }
            ],
            "evidence_map": [
                {
                    "evidence_id": "evidence-pos",
                    "claim_id": "claim-main",
                    "evidence": "Section 4 reports consistent gains on two benchmarks.",
                    "source": "Section 4",
                    "strength": "strong",
                    "stance": "supports",
                }
            ],
            "flaw_candidates": [
                {
                    "flaw_id": "flaw-anchor",
                    "title": "Insufficient analysis",
                    "description": "The flaw is asserted without anchored evidence.",
                    "severity": "major",
                    "status": "confirmed",
                    "related_claim_ids": ["claim-main"],
                    "evidence_ids": [],
                }
            ],
        },
    )

    claim = state["claims"][0]
    flaw = state["flaw_candidates"][0]
    assert claim["status"] == "supported"
    assert claim["supporting_evidence_ids"] == ["evidence-pos"]
    assert flaw["status"] == "candidate"
    assert state["risk_profile"]["readiness"] == "needs_targeted_recheck"
    assert any(event["reason"] == "evidence_sync" for event in state["revision_log"])
    assert any(event["reason"] == "missing_anchor_evidence" for event in state["revision_log"])
    assert any(
        "lacks anchored evidence" in gap["gap"] and gap["status"] == "open"
        for gap in state["evidence_gaps"]
    )

def test_review_env_supports_continue_then_finalize():
    env = ReviewEnv(max_turns=2, mode="s4")
    env.reset(
        {
            "paper_id": "paper-1",
            "paper_text": "The paper claims it improves retrieval accuracy by using a new reranker and reports gains on two benchmarks.",
            "user_goal": "Find the main claim and whether the evidence supports it.",
            "data_source": "unit-test",
            "ground_truth_decision": "reject",
            "reference_review": "Final Decision: Reject\n\nThe evidence is limited and key ablations are missing.",
        }
    )

    continue_action = build_turn_action(
        manager_payload=_manager_payload("continue"),
        worker_payloads=[
            {
                "agent_id": "Claim Agent",
                "payload": {
                    "claims": [
                        {
                            "claim_id": "claim-main",
                            "claim": "The proposed reranker improves retrieval accuracy over prior systems.",
                            "importance": "high",
                            "status": "uncertain",
                        }
                    ],
                    "unresolved_questions": ["Where is the strongest evidence for the reranker gain?"],
                    "dialogue_summary": "The main contribution claim has been extracted but remains unverified.",
                    "recommendation": "undecided",
                },
            }
        ],
        mode="s4",
        turn_id=1,
    )
    next_obs, reward, done, info = env.step(continue_action)

    assert done is False
    assert reward == 0.0
    assert next_obs["review_state"]["turn_id"] == 1
    assert len(next_obs["review_state"]["claims"]) == 1
    assert next_obs["review_state"]["active_focus"] == "inspect the paper's main contribution"
    assert info["turn_log"]["selected_agents"] == ["Claim Agent"]
    assert "revision_events" in info["turn_log"]
    assert "revised_entities" in info["turn_log"]
    assert "conflict_events" in info["turn_log"]
    assert "revision_summary" in info["turn_log"]
    assert "conflict_summary" in info["turn_log"]
    assert "risk_profile" in info["turn_log"]

    finalize_action = build_turn_action(
        manager_payload=_manager_payload(
            "finalize",
            final_report=(
                "Final Decision: Reject\n\n"
                "1. Summary of Reviews\nThe paper presents an interesting reranker idea but the supporting evaluation remains thin.\n\n"
                "2. Key Strengths\n- The core claim is clear and relevant.\n\n"
                "3. Key Weaknesses\n- The strongest benchmark evidence is not convincingly tied to the main claim.\n"
                "- Important ablations are missing.\n\n"
                "4. Questions/Suggestions\n- Show stronger evidence for the reported gains.\n\n"
                "5. Reason for Decision\nThe current evidence record is too incomplete for acceptance."
            ),
        ),
        worker_payloads=[],
        mode="s4",
        turn_id=2,
    )
    final_obs, reward, done, info = env.step(finalize_action)

    assert done is True
    assert reward >= 0.0
    assert final_obs["review_state"]["turn_id"] == 2
    assert "conflict_notes" in final_obs["review_state"]
    assert "revision_log" in final_obs["review_state"]
    assert info["final_report"].startswith("Review Diagnostic Report")
    assert "7. Audit Trace" not in info["final_report"]
    assert "binary_decision" not in info["final_report"]
    assert "Final Decision:" not in info["final_report"]
    assert isinstance(final_obs["review_state"].get("state_audit"), dict)
    assert info["turn_log"]["decision"] == "finalize"


def test_merge_review_state_prioritizes_real_strong_evidence_when_retaining_evidence_map():
    state = create_initial_review_state("s4")
    state = merge_review_state(
        state,
        {
            "claims": [
                {
                    "claim_id": "claim-1",
                    "claim": "The method improves empirical performance.",
                    "importance": "high",
                    "status": "uncertain",
                }
            ],
            "evidence_map": [
                {
                    "evidence_id": f"evidence-weak-{idx}",
                    "claim_id": "claim-1",
                    "evidence": f"Abstract-level weak support {idx}.",
                    "source": "abstract",
                    "strength": "weak",
                    "stance": "supports",
                    "binding_status": "bound_real_claim",
                }
                for idx in range(12)
            ],
        },
    )

    state = merge_review_state(
        state,
        {
            "evidence_map": [
                {
                    "evidence_id": "evidence-strong-result",
                    "claim_id": "claim-1",
                    "evidence": "Table 2 reports a statistically significant improvement over the baseline.",
                    "source": "results table",
                    "strength": "strong",
                    "stance": "supports",
                    "binding_status": "bound_real_claim",
                    "support_source_bucket": "results",
                    "support_quality": "empirical_result",
                },
                {
                    "evidence_id": "evidence-strong-method",
                    "claim_id": "claim-1",
                    "evidence": "The method section describes the architecture and training objective supporting the claim.",
                    "source": "method section",
                    "strength": "strong",
                    "stance": "supports",
                    "binding_status": "bound_real_claim",
                    "support_source_bucket": "method",
                    "support_quality": "method_description",
                },
            ]
        },
    )

    retained_ids = {item["evidence_id"] for item in state["evidence_map"]}
    assert len(state["evidence_map"]) == 12
    assert "evidence-strong-result" in retained_ids
    assert "evidence-strong-method" in retained_ids



def test_preserve_colliding_evidence_ids_renames_materially_different_items():
    existing = [
        {
            "evidence_id": "evidence-1",
            "claim_id": "claim-1",
            "evidence": "The abstract claims the method improves accuracy.",
            "source": "abstract",
            "strength": "medium",
            "stance": "supports",
            "binding_status": "bound_real_claim",
        }
    ]
    incoming = [
        {
            "evidence_id": "evidence-1",
            "claim_id": "claim-1",
            "evidence": "Table 2 reports statistically significant gains over a strong baseline.",
            "source": "results table",
            "strength": "strong",
            "stance": "supports",
            "binding_status": "bound_real_claim",
        }
    ]

    rewritten, renames, collision_count = _preserve_colliding_evidence_ids(existing, incoming)

    assert collision_count == 1
    assert renames == {"evidence-1": rewritten[0]["evidence_id"]}
    assert rewritten[0]["evidence_id"] != "evidence-1"
    assert rewritten[0]["original_evidence_id"] == "evidence-1"
    assert rewritten[0]["evidence_id_collision_preserved"] is True


def test_preserve_colliding_evidence_ids_keeps_matching_signature_updates():
    existing = [
        {
            "evidence_id": "evidence-1",
            "claim_id": "claim-1",
            "evidence": "Table 2 reports statistically significant gains over a strong baseline.",
            "source": "results table",
            "strength": "strong",
            "stance": "supports",
            "binding_status": "bound_real_claim",
        }
    ]
    incoming = [dict(existing[0])]

    rewritten, renames, collision_count = _preserve_colliding_evidence_ids(existing, incoming)

    assert collision_count == 0
    assert renames == {}
    assert rewritten[0]["evidence_id"] == "evidence-1"
    assert not rewritten[0].get("evidence_id_collision_preserved")

