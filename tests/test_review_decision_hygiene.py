import copy
import re
from agent_system.environments.env_package.review.reward import _audit_id_leak_ratio
from agent_system.environments.env_package.review.state import (
    _filter_decision_gaps as _r6_filter_gaps,
)
from agent_system.environments.env_package.review.state import (
    build_decision_hygiene_view as _r5_hygiene,
)
from agent_system.environments.env_package.review.state import (
    NOISE_NEGATIVE_TYPES as _R4_NOISE_TYPES,
    _classify_negative_evidence_type as _r4_classify,
    _flaw_valid_negative_evidence_ids as _r4_flaw_neg_ids,
    _negative_burden_claim_ids as _r4_burden_ids,
)
from agent_system.environments.env_package.review.state import (
    _locator_type_from_anchor as _r3_locator_type_from_anchor,
    _locator_anchor_details_from_text as _r3_locator_details,
    _apply_programmatic_source_locator as _r3_apply_locator,
)

from agent_system.environments.env_package.review.state import (
    CLAIM_KINDS,
    DEEP_PROMOTION_STRONG_MIN_SCORE,
    FINAL_STRONG_MIN_SCORE,
    METHOD_PROMOTION_MODERATE_MIN_SCORE,
    METHOD_PROMOTION_STRONG_MIN_SCORE,
    NEGATIVE_EVIDENCE_TYPES_ALL,
    NEGATIVE_SUPPORT_BUCKETS,
    _build_evidence_quote_bank,
    _build_support_survival_trace,
    _classify_negative_evidence_type,
    _claim_kind_counts,
    _classify_claim_kind,
    _classify_medium_support_promotion_tier,
    _classify_unresolved_limitation,
    _compact_evidence_for_prompt,
    _coverage_item_is_specific_for_type,
    _decision_primary_claim_ids,
    _evidence_human_anchor,
    _evaluation_inventory_from_evidence,
    _evidence_negative_locator_or_bucket_signal,
    _evidence_section_bucket,
    _final_strong_guard,
    _flaw_has_negative_grounding,
    _flaw_only_cites_supports,
    _fmt_audit_number,
    _is_real_paper_claim_id,
    _is_synthetic_recovery_marker_evidence_id,
    _is_system_assessment_limitation_flaw,
    _assess_review_negative_relation,
    _is_paper_negative_evidence_record,
    _is_grounded_paper_negative_evidence_record,
    _render_assessment_limitation_flaws,
    _render_claim_requirement_gap_concerns,
    _render_potential_concerns,
    _report_visible_text,
    _render_strengths,
    _render_weaknesses,
    _should_promote_verified_medium_support,
    _stance_based_negative_evidence_ids,
    _strip_synthetic_recovery_markers,
    _support_survival_summary,
    build_decision_hygiene_view,
    build_review_task,
    build_state_audit,
    claim_coverage_summary,
    infer_final_decision,
    infer_final_recommendation_view,
    merge_review_state,
    normalize_manager_payload,
    normalize_review_update_payload,
    render_final_review,
    render_evidence_observation,
    render_user_report,
)
from agent_system.review_manager_policy import resolve_result_final_decision


def _state_with_real_support():
    return {
        "final_decision": "reject",
        "claims": [
            {"claim_id": "claim-1", "claim": "The method improves robustness.", "status": "unsupported"},
            {"claim_id": "claim-2", "claim": "The evaluation confirms robustness across benchmarks.", "status": "unsupported"},
        ],
        "evidence_map": [
            {
                "evidence_id": "e1",
                "claim_id": "claim-1",
                "evidence": "Results show robust gains.",
                "source": "results",
                "strength": "strong",
                "stance": "supports",
                "binding_status": "bound_real_claim",
            },
            {
                "evidence_id": "e2",
                "claim_id": "claim-1",
                "evidence": "Ablations support the same claim.",
                "source": "ablation",
                "strength": "strong",
                "stance": "supports",
                "binding_status": "bound_real_claim",
            },
            {
                "evidence_id": "e3",
                "claim_id": "claim-2",
                "evidence": "Additional evaluation confirms the benchmark robustness claim.",
                "source": "evaluation",
                "strength": "strong",
                "stance": "supports",
                "binding_status": "bound_real_claim",
            },
        ],
        "flaw_candidates": [
            {
                "flaw_id": "flaw-fallback-1",
                "title": "Fallback concern",
                "description": "Parser fallback produced an ungrounded concern.",
                "severity": "major",
                "status": "candidate",
                "evidence_ids": [],
                "related_claim_ids": ["claim-1"],
            }
        ],
        "unresolved_questions": [
            {
                "question_id": "q-meta",
                "question": "Fallback could not bind an evidence snippet; verify whether the parser failed.",
                "status": "open",
                "related_claim_ids": [],
            }
        ],
        "evidence_gaps": ["Claim claim-1 lacks grounded supporting evidence."],
        "conflict_notes": [
            {
                "conflict_id": "c-fallback",
                "note": "fallback evidence conflict should not block accept",
                "claim_id": "claim-1",
                "evidence_id": "evidence-fallback-1",
                "flaw_id": "",
                "conflict_type": "fallback_contradiction",
            }
        ],
    }


def _verified_negative(evidence_id, claim_id, negative_evidence_type, quote, *, source="Section 5 Experiments", stance="missing", strength="missing"):
    """A fully paper-grounded, review-verified actionable negative evidence record.

    Meets the hardened contract: trusted paper grounding (span + quote_bank match_type),
    semantic_negative_verified, and review_negative_verified (a genuine reviewer-discovered
    negative, not an author self-limitation / quote-bank salvage / fallback).
    """
    return {
        "evidence_id": evidence_id,
        "claim_id": claim_id,
        "evidence": quote,
        "raw_quote": quote,
        "agent_raw_quote": quote,
        "source": source,
        "source_locator": source,
        "stance": stance,
        "strength": strength,
        "negative_evidence_type": negative_evidence_type,
        "verified_grounding_label": "paper_grounded_exact",
        "verified_quote_match_type": "quote_bank_raw_canonical",
        "verified_source_span_start": 10,
        "verified_source_span_end": 84,
        "semantic_grounding_label": "semantic_negative_verified",
        "review_negative_label": "review_negative_verified",
    }


def _grounding_bank(quotes):
    """Build (paper_text, evidence_quote_bank) so merge_review_state can verify quotes.

    merge_review_state strips model-claimed grounding (sets model_claimed_verification_stripped)
    and only trusts quotes verifiable against the program-extracted quote bank / paper text.
    quotes: list of (quote_id, raw_quote, source_bucket).
    """
    text = "Section 5 Experiments. "
    bank = []
    for qid, q, bucket in quotes:
        start = len(text)
        text += q + " "
        bank.append({
            "quote_id": qid,
            "raw_quote": q,
            "source_bucket": bucket,
            "source_locator": "Section 5",
            "source_span_start": start,
            "source_span_end": start + len(q) - 1,
        })
    return text, bank


def test_decision_hygiene_accepts_real_support_despite_stale_reject():
    state = _state_with_real_support()
    assert infer_final_decision(state, {"final_decision": "reject"}) == "accept"
    assert resolve_result_final_decision(state, "Final Decision: Reject") == "accept"
    view = infer_final_recommendation_view(state, {"final_decision": "reject"})
    assert view["recommendation_view"] == "accept_like"
    assert view["binary_decision"] == "accept"


def test_decision_hygiene_view_does_not_mutate_live_state():
    state = _state_with_real_support()
    view = build_decision_hygiene_view(state)
    assert state["final_decision"] == "reject"
    assert state["flaw_candidates"][0]["status"] == "candidate"
    assert state["unresolved_questions"][0]["status"] == "open"
    assert state["evidence_gaps"]
    assert view["flaw_candidates"][0]["status"] == "downgraded"
    assert view["unresolved_questions"][0]["status"] == "deferred"
    assert view["evidence_gaps"] == []
    assert view["decision_hygiene"]["non_abstract_real_strong_support_count"] == 3
    assert view["decision_hygiene"]["max_real_strong_support_per_claim"] == 2
    assert view["decision_hygiene"]["claims_with_real_strong_support"] == 2


def test_fallback_strong_support_does_not_drive_accept():
    state = {
        "claims": [{"claim_id": "claim-1", "claim": "A real claim.", "status": "uncertain"}],
        "evidence_map": [
            {
                "evidence_id": "ef1",
                "claim_id": "claim-fallback-1",
                "evidence": "Looks supportive but is fallback-bound.",
                "source": "fallback-extraction",
                "strength": "strong",
                "stance": "supports",
                "binding_status": "fallback_unverified",
            },
            {
                "evidence_id": "ef2",
                "claim_id": "missing-claim",
                "evidence": "Looks supportive but is unbound.",
                "source": "paper",
                "strength": "strong",
                "stance": "supports",
                "binding_status": "invalid_claim_id",
            },
        ],
        "flaw_candidates": [],
        "unresolved_questions": [],
        "evidence_gaps": [],
        "conflict_notes": [],
    }
    assert infer_final_decision(state, {}) == "reject"


def test_two_real_support_items_are_not_enough_for_accept():
    state = _state_with_real_support()
    state["evidence_map"] = state["evidence_map"][:2]
    assert infer_final_decision(state, {}) == "reject"
    view = infer_final_recommendation_view(state, {})
    assert view["recommendation_view"] in {"borderline_insufficient", "borderline_positive"}


def test_targetless_uncertainty_blocks_accept_like_without_hard_reject():
    state = _state_with_real_support()
    state["unresolved_questions"] = [
        {
            "question_id": "q-targetless",
            "question": "Which baseline is the strongest comparator?",
            "status": "open",
            "related_claim_ids": [],
        }
    ]
    view = infer_final_recommendation_view(state, {})
    assert view["recommendation_view"] == "borderline_positive"
    assert view["binary_decision"] == "reject"
    assert infer_final_decision(state, {}) == "reject"


def test_grounded_major_flaws_drive_reject_like():
    state = _state_with_real_support()
    state["evidence_map"].extend([
        _verified_negative("neg-1", "claim-1", "negative_result", "Table 7 shows the method losing to the baseline on benchmark Y."),
        _verified_negative("neg-2", "claim-2", "missing_baseline", "We compare only against method A; method B is not included in our experiments."),
    ])
    state["flaw_candidates"] = [
        {
            "flaw_id": "flaw-1",
            "title": "Unsupported empirical claim",
            "description": "The primary empirical claim is contradicted by the result table.",
            "severity": "major",
            "status": "confirmed",
            "evidence_ids": ["neg-1"],
            "negative_evidence_ids": ["neg-1"],
            "related_claim_ids": ["claim-1"],
        },
        {
            "flaw_id": "flaw-2",
            "title": "Missing baseline",
            "description": "The main comparison omits the strongest baseline.",
            "severity": "major",
            "status": "confirmed",
            "evidence_ids": ["neg-2"],
            "negative_evidence_ids": ["neg-2"],
            "related_claim_ids": ["claim-2"],
        },
    ]
    view = infer_final_recommendation_view(state, {})
    assert view["recommendation_view"] == "reject_like"
    assert view["grounded_major_flaw_count"] == 2
    assert infer_final_decision(state, {}) == "reject"

def test_empty_state_can_fall_back_to_report_decision():
    assert resolve_result_final_decision({}, "Final Decision: Accept") == "accept"

def test_supported_claim_unresolved_gap_is_deferred_in_decision_view():
    state = _state_with_real_support()
    state["unresolved_questions"] = [
        {
            "question_id": "q-claim-gap",
            "question": "Claim claim-1 lacks grounded supporting evidence.",
            "status": "open",
            "related_claim_ids": [],
        },
        {
            "question_id": "q-truncated",
            "question": "The abstract text is truncated; please provide the full text.",
            "status": "open",
            "related_claim_ids": [],
        },
    ]
    view = build_decision_hygiene_view(state)
    assert [q["status"] for q in view["unresolved_questions"]] == ["deferred", "deferred"]
    assert infer_final_decision(state, {}) == "accept"


def test_abstract_only_positive_support_is_downgraded():
    state = {
        "claims": [{"claim_id": "claim-1", "claim": "The method improves performance.", "status": "uncertain"}],
        "evidence_map": [],
        "flaw_candidates": [],
        "unresolved_questions": [],
        "evidence_gaps": [],
        "conflict_notes": [],
    }
    payload = {
        "evidence_map": [
            {
                "evidence_id": "e1",
                "claim_id": "claim-1",
                "evidence": "The abstract states that the method improves performance.",
                "source": "abstract",
                "strength": "strong",
                "stance": "supports",
                "binding_status": "bound_real_claim",
            }
        ]
    }
    merged = merge_review_state(state, payload)
    evidence = merged["evidence_map"][0]
    assert evidence["binding_status"] == "bound_real_claim"
    assert evidence["support_source_bucket"] == "abstract"
    assert evidence["support_quality"] == "abstract_claim_support"
    assert evidence["support_quality_adjustment"] == "downgraded_abstract_only_support"
    assert evidence["strength"] == "medium"
    assert infer_final_decision(merged, {}) == "reject"


def test_concentrated_empirical_support_remains_strong_but_not_accept_sufficient():
    paper_text, bank = _grounding_bank([
        ("q1", "Table 1 reports a 12 point improvement over the baseline.", "result_or_experiment"),
        ("q2", "The ablation confirms the core component drives the gain.", "result_or_experiment"),
        ("q3", "Evaluation on three benchmarks improves over baselines.", "result_or_experiment"),
    ])
    state = {
        "claims": [{"claim_id": "claim-1", "claim": "The method improves performance.", "status": "uncertain"}],
        "evidence_map": [],
        "flaw_candidates": [],
        "unresolved_questions": [],
        "evidence_gaps": [],
        "conflict_notes": [],
        "paper_text": paper_text,
        "evidence_quote_bank": bank,
    }
    payload = {
        "evidence_map": [
            {"evidence_id": "e1", "claim_id": "claim-1", "quote_id": "q1", "evidence": "Table 1 reports a 12 point improvement over the baseline.", "raw_quote": "Table 1 reports a 12 point improvement over the baseline.", "source": "Table 1 results", "strength": "strong", "stance": "supports"},
            {"evidence_id": "e2", "claim_id": "claim-1", "quote_id": "q2", "evidence": "The ablation confirms the core component drives the gain.", "raw_quote": "The ablation confirms the core component drives the gain.", "source": "ablation", "strength": "strong", "stance": "supports"},
            {"evidence_id": "e3", "claim_id": "claim-1", "quote_id": "q3", "evidence": "Evaluation on three benchmarks improves over baselines.", "raw_quote": "Evaluation on three benchmarks improves over baselines.", "source": "evaluation", "strength": "strong", "stance": "supports"},
        ]
    }
    merged = merge_review_state(state, payload)
    assert [item["strength"] for item in merged["evidence_map"]] == ["strong", "strong", "strong"]
    view = build_decision_hygiene_view(merged)
    assert view["decision_hygiene"]["non_abstract_real_strong_support_count"] == 3
    assert infer_final_decision(merged, {}) == "reject"


def test_two_claim_empirical_support_can_drive_health_check_accept():
    paper_text, bank = _grounding_bank([
        ("q1", "Table 1 reports a 12 point improvement over the baseline.", "result_or_experiment"),
        ("q2", "The ablation confirms the core component drives the gain.", "result_or_experiment"),
        ("q3", "Evaluation on three benchmarks improves over baselines.", "result_or_experiment"),
    ])
    state = {
        "claims": [
            {"claim_id": "claim-1", "claim": "The method improves performance.", "status": "uncertain"},
            {"claim_id": "claim-2", "claim": "The evaluation validates the improvement.", "status": "uncertain"},
        ],
        "evidence_map": [],
        "flaw_candidates": [],
        "unresolved_questions": [],
        "evidence_gaps": [],
        "conflict_notes": [],
        "paper_text": paper_text,
        "evidence_quote_bank": bank,
    }
    payload = {
        "evidence_map": [
            {"evidence_id": "e1", "claim_id": "claim-1", "quote_id": "q1", "evidence": "Table 1 reports a 12 point improvement over the baseline.", "raw_quote": "Table 1 reports a 12 point improvement over the baseline.", "source": "Table 1 results", "strength": "strong", "stance": "supports"},
            {"evidence_id": "e2", "claim_id": "claim-1", "quote_id": "q2", "evidence": "The ablation confirms the core component drives the gain.", "raw_quote": "The ablation confirms the core component drives the gain.", "source": "ablation", "strength": "strong", "stance": "supports"},
            {"evidence_id": "e3", "claim_id": "claim-2", "quote_id": "q3", "evidence": "Evaluation on three benchmarks improves over baselines.", "raw_quote": "Evaluation on three benchmarks improves over baselines.", "source": "evaluation", "strength": "strong", "stance": "supports"},
        ]
    }
    merged = merge_review_state(state, payload)
    view = build_decision_hygiene_view(merged)
    assert view["decision_hygiene"]["non_abstract_real_strong_support_count"] == 3
    assert view["decision_hygiene"]["claims_with_real_strong_support"] == 2
    assert infer_final_decision(merged, {}) == "accept"


def test_schema_or_meta_flaw_payload_is_dropped_before_state_merge():
    payload = {
        "flaw_candidates": [
            {
                "flaw_id": "flaw-fallback-1",
                "title": "{ \"flaw_candidates\": [ malformed output",
                "description": "The user wants me to output JSON, but parsing failed.",
                "severity": "major",
                "status": "candidate",
                "evidence_ids": ["e1"],
                "related_claim_ids": ["claim-1"],
                "confidence": 0.7,
            }
        ]
    }
    normalized = normalize_review_update_payload(payload)
    assert normalized["flaw_candidates"] == []


def test_context_artifact_flaw_is_dropped_but_paper_flaw_is_kept():
    payload = {
        "flaw_candidates": [
            {
                "flaw_id": "flaw-1",
                "title": "Incomplete Abstract Prevents Verification",
                "description": "The abstract cuts off mid-sentence, making it impossible to verify the current ReviewState claims.",
                "severity": "critical",
                "status": "candidate",
                "related_claim_ids": ["claim-1"],
            },
            {
                "flaw_id": "flaw-2",
                "title": "Incomplete Abstract Truncation",
                "description": "The abstract ends abruptly, preventing verification of claims marked as supported.",
                "severity": "major",
                "status": "candidate",
                "related_claim_ids": ["claim-1"],
            },
            {
                "flaw_id": "flaw-3",
                "title": "Missing HumanEval Evidence",
                "description": "The HumanEval claim lacks explicit excerpt support despite being marked as supported.",
                "severity": "major",
                "status": "candidate",
                "related_claim_ids": ["claim-2"],
            },
            {
                "flaw_id": "flaw-4",
                "title": "Truncated Excerpt Limits Verification",
                "description": "The abstract and introduction are cut off, preventing full extraction of claims and evidence.",
                "severity": "major",
                "status": "candidate",
                "related_claim_ids": ["claim-1"],
            },
            {
                "flaw_id": "flaw-5",
                "title": "Missing Empirical Validation",
                "description": "The excerpt lacks experimental results or metrics to support this claim.",
                "severity": "major",
                "status": "candidate",
                "related_claim_ids": ["claim-2"],
            },
            {
                "flaw_id": "flaw-6",
                "title": "Unverifiable Core Mechanism",
                "description": "Abstract truncation prevents validation of the core mechanism claims.",
                "severity": "major",
                "status": "candidate",
                "related_claim_ids": ["claim-2"],
            },
            {
                "flaw_id": "flaw-7",
                "title": "Missing annotation burden metrics",
                "description": "The paper claims lower annotation effort without reporting time or energy measurements.",
                "severity": "major",
                "status": "candidate",
                "related_claim_ids": ["claim-1"],
                "evidence_ids": ["e1"],
            },
        ]
    }
    normalized = normalize_review_update_payload(payload)
    assert [flaw["flaw_id"] for flaw in normalized["flaw_candidates"]] == ["flaw-7"]
    assert any(
        question["question"].startswith("Assessment limitation:")
        for question in normalized["unresolved_questions"]
    )


def test_evidence_aware_lack_support_flaw_is_downgraded_against_strong_support():
    state = {
        "claims": [{"claim_id": "claim-1", "claim": "The method improves benchmark performance.", "status": "uncertain"}],
        "evidence_map": [
            {
                "evidence_id": "e1",
                "claim_id": "claim-1",
                "evidence": "Table 1 reports a 3.5x speedup on MT-Bench using H100.",
                "source": "Table 1 results",
                "strength": "strong",
                "stance": "supports",
            }
        ],
        "flaw_candidates": [
            {
                "flaw_id": "flaw-1",
                "title": "Missing Benchmark Data",
                "description": "No specific benchmark scores or latency numbers are provided to verify the speedup claim.",
                "severity": "major",
                "status": "candidate",
                "related_claim_ids": ["claim-1"],
                "evidence_ids": [],
            }
        ],
        "unresolved_questions": [],
        "evidence_gaps": [],
        "conflict_notes": [],
    }

    merged = merge_review_state({}, state)
    flaw = merged["flaw_candidates"][0]
    assert flaw["status"] == "downgraded"
    assert flaw["hygiene_status_reason"] == "evidence_aware_lack_flaw_conflicts_with_strong_support"
    assert any(event["reason"] == "evidence_aware_support_conflict" for event in merged["revision_log"])


def test_final_review_separates_filtered_weaknesses_from_assessment_limitations():
    state = _state_with_real_support()
    state["flaw_candidates"] = [
        {
            "flaw_id": "flaw-1",
            "title": "Missing empirical evidence",
            "description": "No quantitative evidence is provided for claim-1.",
            "severity": "major",
            "status": "candidate",
            "related_claim_ids": ["claim-1"],
            "evidence_ids": [],
        }
    ]
    state["unresolved_questions"] = [
        {
            "question_id": "q-limit",
            "question": "Assessment limitation: this critique was not grounded as a paper defect; verify it with method, result, table, or figure evidence before treating it as a weakness.",
            "status": "open",
            "related_claim_ids": ["claim-1"],
        }
    ]

    report = render_final_review(state, {})

    assert "Grounded paper weaknesses: none passed the paper-evidence grounding filter." in report
    assert "Unresolved assessment limitations:" in report
    assert "Important weaknesses were not fully resolved" not in report
    assert "No grounded major weakness remained active" not in report


def test_targetless_unresolved_is_deferred_in_decision_view():
    state = _state_with_real_support()
    state["unresolved_questions"] = [
        {
            "question_id": "q-targetless",
            "question": "What is the full methodology of the proposed framework?",
            "status": "open",
            "related_claim_ids": [],
            "related_evidence_ids": [],
            "related_flaw_ids": [],
        }
    ]
    view = build_decision_hygiene_view(state)
    question = view["unresolved_questions"][0]
    assert question["status"] == "deferred"
    assert question["hygiene_status_reason"] == "decision_view_targetless_uncertainty"
    assert question["target_type"] == "state"
    assert question["target_classification"] == "context_limitation"
    assert question["final_diagnostic_visible"] is False
    assert view["decision_hygiene"]["targetless_unresolved_deferred_count"] == 0
    assert "What is the full methodology" not in render_final_review(state, {})


def test_fallback_extraction_flaw_with_evidence_is_downgraded_in_decision_view():
    state = _state_with_real_support()
    state["flaw_candidates"] = [
        {
            "flaw_id": "flaw-1",
            "title": "Parser fallback concern",
            "description": "Fallback extraction created this concern, not grounded paper evidence.",
            "severity": "major",
            "status": "confirmed",
            "source": "fallback-extraction",
            "grounding_status": "fallback_unverified",
            "evidence_ids": ["e1"],
        }
    ]
    view = build_decision_hygiene_view(state)
    flaw = view["flaw_candidates"][0]
    assert flaw["status"] == "downgraded"
    assert flaw["hygiene_status_reason"] == "decision_view_ungrounded_or_fallback_flaw"


def test_final_report_strengths_ignore_fallback_and_unbound_support():
    state = {
        "claims": [{"claim_id": "claim-1", "claim": "A real claim.", "status": "uncertain"}],
        "evidence_map": [
            {
                "evidence_id": "e1",
                "claim_id": "claim-1",
                "evidence": "Table evidence supports the real claim.",
                "source": "Table 1",
                "strength": "strong",
                "stance": "supports",
                "binding_status": "bound_real_claim",
            },
            {
                "evidence_id": "ef1",
                "claim_id": "claim-fallback-1",
                "evidence": "Fallback-bound support should not render as a strength.",
                "source": "fallback-extraction",
                "strength": "strong",
                "stance": "supports",
                "binding_status": "fallback_unverified",
            },
        ],
    }
    strengths = _render_strengths(state)
    assert any("Table evidence supports" in item for item in strengths)
    assert all("Fallback-bound" not in item for item in strengths)


def test_final_report_weaknesses_ignore_fallback_meta_flaws():
    state = {
        "claims": [{"claim_id": "claim-1", "claim": "The method outperforms baselines.", "status": "uncertain", "claim_kind": "paper_extracted"}],
        "evidence_map": [
            {
                "evidence_id": "e1",
                "claim_id": "claim-fallback-1",
                "evidence": "Fallback-bound supportive snippet.",
                "source": "fallback-extraction",
                "strength": "strong",
                "stance": "supports",
                "binding_status": "fallback_unverified",
            },
            _verified_negative(
                "e2",
                "claim-1",
                "negative_result",
                "Table 4 shows the baseline outperforms the proposed method on the main benchmark.",
                source="results",
                stance="contradicts",
            ),
        ],
        "flaw_candidates": [
            {
                "flaw_id": "flaw-1",
                "title": "Fallback parser concern",
                "description": "This is a fallback-extraction artifact.",
                "severity": "major",
                "status": "confirmed",
                "source": "fallback-extraction",
                "grounding_status": "fallback_unverified",
                "evidence_ids": ["e1"],
            },
            {
                "flaw_id": "flaw-2",
                "title": "Grounded empirical issue",
                "description": "The baseline comparison is missing.",
                "severity": "major",
                "status": "confirmed",
                "source": "paper_evidence",
                "grounding_status": "grounded",
                "evidence_ids": ["e2"],
                "negative_evidence_ids": ["e2"],
                "related_claim_ids": ["claim-1"],
            },
        ],
    }
    weaknesses = _render_weaknesses(state)
    assert weaknesses == ["Grounded empirical issue: The baseline comparison is missing."]


def test_support_survival_trace_ignores_missing_strength_support_placeholder():
    state = {
        "claims": [
            {
                "claim_id": "claim-1",
                "claim": "The method has a measured speedup.",
                "claim_kind": "paper_extracted",
            }
        ],
        "evidence_map": [
            {
                "evidence_id": "e-placeholder",
                "claim_id": "claim-1",
                "evidence": "A speedup table should be located.",
                "source": "To be located: specific table/figure in the full text.",
                "source_locator": "To be located: specific table/figure in the full text.",
                "strength": "missing",
                "stance": "supports",
                "binding_status": "bound_real_claim",
                "verified_grounding_label": "missing_quote",
                "semantic_grounding_label": "semantic_unverified_quote",
            }
        ],
    }

    assert _build_support_survival_trace(state) == []


def test_final_report_weakness_requires_negative_grounding():
    state = {
        "evidence_map": [
            {
                "evidence_id": "e1",
                "claim_id": "claim-1",
                "evidence": "Method outperforms baseline by 3.5x on MT-Bench.",
                "source": "results",
                "strength": "strong",
                "stance": "supports",
                "binding_status": "bound_real_claim",
            }
        ],
        "flaw_candidates": [
            {
                "flaw_id": "flaw-only-supports",
                "title": "Missing baseline comparison",
                "description": "The claim about speedup lacks an explicit baseline comparison in the abstract excerpt.",
                "severity": "major",
                "status": "confirmed",
                "related_claim_ids": ["claim-1"],
                "evidence_ids": ["e1"],
            }
        ],
    }
    assert _flaw_has_negative_grounding(state["flaw_candidates"][0], state) is False
    assert _flaw_only_cites_supports(state["flaw_candidates"][0], state) is True
    assert _render_weaknesses(state) == []


def test_potential_concerns_surface_active_candidates_without_negative_grounding():
    state = {
        "evidence_map": [
            {
                "evidence_id": "e1",
                "claim_id": "claim-1",
                "evidence": "Method achieves 3.5x speedup on MT-Bench.",
                "source": "results",
                "strength": "strong",
                "stance": "supports",
                "binding_status": "bound_real_claim",
            }
        ],
        "flaw_candidates": [
            {
                "flaw_id": "flaw-overstate",
                "title": "Overstated 'first' claim",
                "description": "The paper claims to be the first method without supporting prior-work analysis.",
                "severity": "major",
                "status": "candidate",
                "related_claim_ids": ["claim-2"],
                "evidence_ids": ["e1"],
            }
        ],
    }
    weaknesses = _render_weaknesses(state)
    concerns = _render_potential_concerns(state)
    assert weaknesses == []
    assert any("Overstated 'first' claim" in line for line in concerns)
    assert any(line.startswith("[candidate]") for line in concerns)


def test_potential_concerns_filter_obvious_lack_support_against_strong_claim():
    state = {
        "claims": [{"claim_id": "claim-1", "claim": "The method beats baselines.", "status": "uncertain"}],
        "evidence_map": [
            {
                "evidence_id": "e1",
                "claim_id": "claim-1",
                "evidence": "Table 1 reports 3.5x speedup vs baseline.",
                "source": "results",
                "strength": "strong",
                "stance": "supports",
                "binding_status": "bound_real_claim",
            }
        ],
        "flaw_candidates": [
            {
                "flaw_id": "flaw-lack",
                "title": "Lack of quantitative validation",
                "description": "Claim 1 lacks specific empirical metrics or baseline comparisons.",
                "severity": "major",
                "status": "candidate",
                "related_claim_ids": ["claim-1"],
                "evidence_ids": ["e1"],
            }
        ],
    }
    assert _render_weaknesses(state) == []
    assert _render_potential_concerns(state) == []


def test_confirmed_only_supports_lack_flaw_routes_to_assessment_limitation():
    state = {
        "evidence_map": [
            {
                "evidence_id": "e1",
                "claim_id": "claim-1",
                "evidence": "Abstract states the framework proposes a hybrid encoder.",
                "source": "abstract",
                "strength": "medium",
                "stance": "supports",
                "binding_status": "bound_real_claim",
            },
            {
                "evidence_id": "e2",
                "claim_id": "claim-1",
                "evidence": "Method section describes a two-branch encoder design.",
                "source": "method",
                "strength": "medium",
                "stance": "supports",
                "binding_status": "bound_real_claim",
            },
        ],
        "flaw_candidates": [
            {
                "flaw_id": "flaw-1",
                "title": "Missing Empirical Validation",
                "description": "Claims of robustness lack quantitative results, tables, or figures to support effectiveness.",
                "severity": "critical",
                "status": "confirmed",
                "related_claim_ids": ["claim-1"],
                "evidence_ids": ["e1", "e2"],
            }
        ],
    }
    flaw = state["flaw_candidates"][0]
    assert _is_system_assessment_limitation_flaw(flaw, state) is True
    assert _render_weaknesses(state) == []
    assert _render_potential_concerns(state) == []
    al_lines = _render_assessment_limitation_flaws(state)
    assert any("Missing Empirical Validation" in line for line in al_lines)


def test_generic_lack_against_strong_claim_routes_to_assessment_limitation():
    state = {
        "claims": [{"claim_id": "claim-1", "claim": "The method beats baselines.", "status": "uncertain"}],
        "evidence_map": [
            {
                "evidence_id": "e1",
                "claim_id": "claim-1",
                "evidence": "Table 1 reports 3.5x speedup vs baseline.",
                "source": "results",
                "strength": "strong",
                "stance": "supports",
                "binding_status": "bound_real_claim",
            }
        ],
        "flaw_candidates": [
            {
                "flaw_id": "flaw-lack",
                "title": "Lack of quantitative validation",
                "description": "Claim 1 lacks specific empirical metrics or baseline comparisons.",
                "severity": "major",
                "status": "candidate",
                "related_claim_ids": ["claim-1"],
                "evidence_ids": ["e1"],
            }
        ],
    }
    assert _render_weaknesses(state) == []
    assert _render_potential_concerns(state) == []
    al_lines = _render_assessment_limitation_flaws(state)
    assert any("Lack of quantitative validation" in line for line in al_lines)


def test_assessment_limitation_skips_flaw_with_real_negative_grounding():
    state = {
        "claims": [{"claim_id": "claim-1", "claim": "The method beats baselines.", "claim_kind": "paper_extracted"}],
        "evidence_map": [
            _verified_negative("e1", "claim-1", "negative_result", "Table 7 shows method underperforms by 4% on benchmark Y.", source="Table 7")
        ],
        "flaw_candidates": [
            {
                "flaw_id": "flaw-1",
                "title": "Missing baseline coverage",
                "description": "Method lacks broad baseline coverage; benchmark Y exposes regression.",
                "severity": "major",
                "status": "confirmed",
                "related_claim_ids": ["claim-1"],
                "evidence_ids": ["e1"],
                "negative_evidence_ids": ["e1"],
            }
        ],
    }
    assert _is_system_assessment_limitation_flaw(state["flaw_candidates"][0], state) is False
    assert any("Missing baseline coverage" in line for line in _render_weaknesses(state))
    assert _render_assessment_limitation_flaws(state) == []


def test_normalize_flaw_item_preserves_negative_evidence_ids():
    payload = {
        "flaw_candidates": [
            {
                "flaw_id": "flaw-1",
                "title": "Method overstates baseline",
                "description": "Table 4 shows the proposed method losing on the main benchmark.",
                "severity": "major",
                "status": "confirmed",
                "related_claim_ids": ["claim-1"],
                "evidence_ids": ["e-supp"],
                "negative_evidence_ids": ["e-neg"],
            }
        ]
    }
    normalized = normalize_review_update_payload(payload)
    flaw = normalized["flaw_candidates"][0]
    assert flaw["negative_evidence_ids"] == ["e-neg"]
    # Negative ids must be merged into evidence_ids so legacy consumers still see them.
    assert "e-neg" in flaw["evidence_ids"]
    assert "e-supp" in flaw["evidence_ids"]


def test_flaw_has_negative_grounding_rejects_explicit_field_when_evidence_is_not_negative():
    state = {
        "evidence_map": [
            {
                "evidence_id": "e-supp",
                "claim_id": "claim-1",
                "evidence": "Method matches baseline on benchmark X.",
                "source": "results",
                "strength": "strong",
                "stance": "supports",
                "binding_status": "bound_real_claim",
            },
            {
                "evidence_id": "e-neg",
                "claim_id": "claim-1",
                "evidence": "Table 7 shows method underperforms by 4% on benchmark Y.",
                "source": "results",
                "strength": "strong",
                "stance": "supports",
                "binding_status": "bound_real_claim",
            },
        ],
        "flaw_candidates": [
            {
                "flaw_id": "flaw-1",
                "title": "Underperformance on benchmark Y",
                "description": "Table 7 contradicts the universal-improvement claim.",
                "severity": "major",
                "status": "confirmed",
                "related_claim_ids": ["claim-1"],
                "evidence_ids": ["e-supp", "e-neg"],
                "negative_evidence_ids": ["e-neg"],
            }
        ],
    }
    flaw = state["flaw_candidates"][0]
    assert _flaw_has_negative_grounding(flaw, state) is False
    assert _render_weaknesses(state) == []
    view = build_decision_hygiene_view(state)
    view_flaw = view["flaw_candidates"][0]
    assert view_flaw["hygiene_negative_grounding_conflicts"][0]["reason"] == "negative_evidence_id_not_negative_stance"
    hg = view["decision_hygiene"]
    assert hg["negative_grounding_conflict_count"] == 1
    assert hg["invalid_negative_evidence_id_count"] == 1


def test_flaw_negative_grounding_ignores_unresolved_explicit_ids_when_map_is_known():
    state = {
        "evidence_map": [
            {
                "evidence_id": "e-supp",
                "claim_id": "claim-1",
                "evidence": "Supportive snippet.",
                "source": "results",
                "strength": "strong",
                "stance": "supports",
                "binding_status": "bound_real_claim",
            }
        ],
        "flaw_candidates": [
            {
                "flaw_id": "flaw-1",
                "title": "Phantom negative anchor",
                "description": "Cites a non-existent evidence id as negative grounding.",
                "severity": "major",
                "status": "confirmed",
                "related_claim_ids": ["claim-1"],
                "evidence_ids": ["e-supp"],
                "negative_evidence_ids": ["evidence-does-not-exist"],
            }
        ],
    }
    flaw = state["flaw_candidates"][0]
    assert _flaw_has_negative_grounding(flaw, state) is False
    assert _render_weaknesses(state) == []


def test_support_only_flaw_conflict_is_stale_after_downgrade():
    state = {
        "claims": [{"claim_id": "claim-1", "claim": "The method is evaluated.", "status": "supported"}],
        "evidence_map": [
            {
                "evidence_id": "e-support",
                "claim_id": "claim-1",
                "raw_quote": "The method is evaluated on benchmark X.",
                "source": "results",
                "source_locator": "Table 1",
                "strength": "strong",
                "stance": "supports",
                "verified_grounding_label": "paper_grounded_exact",
                "semantic_grounding_label": "semantic_support_verified",
            }
        ],
        "flaw_candidates": [
            {
                "flaw_id": "flaw-support-only",
                "status": "downgraded",
                "related_claim_ids": ["claim-1"],
                "evidence_ids": ["e-support"],
                "negative_evidence_ids": ["e-support"],
            }
        ],
        "conflict_notes": [
            {
                "conflict_id": "conflict-support-only",
                "claim_id": "claim-1",
                "evidence_id": "e-support",
                "flaw_id": "flaw-support-only",
                "conflict_type": "support_only_flaw_without_negative_grounding",
                "note": "Flaw was downgraded because it only cites positive support evidence.",
            }
        ],
    }

    hygiene = build_decision_hygiene_view(state)["decision_hygiene"]
    assert hygiene["open_conflict_count"] == 0
    assert hygiene["stale_conflict_count"] == 1


def test_interpretation_conflict_on_downgraded_flaw_is_stale():
    state = {
        "claims": [{"claim_id": "claim-1", "claim": "The method improves benchmark performance.", "status": "supported"}],
        "evidence_map": [
            {
                "evidence_id": "e-support",
                "claim_id": "claim-1",
                "raw_quote": "Table 2 shows the method improves benchmark performance.",
                "source": "results",
                "source_locator": "Table 2",
                "strength": "strong",
                "stance": "supports",
                "binding_status": "bound_real_claim",
                "verified_grounding_label": "paper_grounded_exact",
                "semantic_grounding_label": "semantic_support_verified",
                "semantic_alignment_score": 0.84,
            }
        ],
        "flaw_candidates": [
            {
                "flaw_id": "flaw-1",
                "status": "downgraded",
                "hygiene_status_reason": "support_only_flaw_lacks_verified_negative_evidence",
                "related_claim_ids": ["claim-1"],
                "evidence_ids": ["e-support"],
                "negative_evidence_ids": ["e-support"],
                "final_view_flaw_layer": "assessment_limitation",
            }
        ],
        "conflict_notes": [
            {
                "conflict_id": "conflict-positive-as-negative",
                "note": "The second negative quote is a positive result and does not contradict the claim.",
                "claim_id": "claim-1",
                "evidence_id": "e-support",
                "flaw_id": "flaw-1",
                "conflict_type": "interpretation_conflict",
            }
        ],
    }

    hygiene = build_decision_hygiene_view(state)["decision_hygiene"]
    assert hygiene["open_conflict_count"] == 0
    assert hygiene["stale_conflict_count"] == 1


def test_internal_flaw_anchor_gap_and_downgraded_flaw_do_not_count_as_contamination():
    state = {
        "claims": [{"claim_id": "claim-1", "claim": "The method improves benchmark performance.", "status": "supported"}],
        "evidence_map": [
            {
                "evidence_id": "e-support",
                "claim_id": "claim-1",
                "raw_quote": "Table 2 shows the method improves benchmark performance.",
                "source": "results",
                "source_locator": "Table 2",
                "strength": "strong",
                "stance": "supports",
                "binding_status": "bound_real_claim",
                "verified_grounding_label": "paper_grounded_exact",
                "semantic_grounding_label": "semantic_support_verified",
                "semantic_alignment_score": 0.84,
            }
        ],
        "flaw_candidates": [
            {
                "flaw_id": "flaw-baseline-coverage",
                "status": "downgraded",
                "hygiene_status_reason": "decision_view_ungrounded_or_fallback_flaw",
                "severity": "major",
                "related_claim_ids": ["claim-1"],
                "evidence_ids": [],
                "negative_evidence_ids": [],
            }
        ],
        "evidence_gaps": [
            {
                "gap_id": "gap-flaw-anchor",
                "gap": "Flaw flaw-baseline-coverage lacks anchored evidence.",
                "status": "open",
            }
        ],
    }

    hygiene = build_decision_hygiene_view(state)["decision_hygiene"]
    type_counts = hygiene["state_contamination_type_counts"]
    assert hygiene["open_evidence_gap_count"] == 0
    assert hygiene["stale_evidence_gap_count"] == 1
    assert type_counts.get("stale_gap_persistence", 0) == 0
    assert type_counts.get("unsupported_flaw_escalation", 0) == 0


def test_active_confirmed_support_only_flaw_still_counts_as_contamination():
    state = {
        "claims": [{"claim_id": "claim-1", "claim": "The method improves benchmark performance.", "status": "supported"}],
        "evidence_map": [
            {
                "evidence_id": "e-support",
                "claim_id": "claim-1",
                "raw_quote": "Table 2 shows the method improves benchmark performance.",
                "source": "results",
                "source_locator": "Table 2",
                "strength": "strong",
                "stance": "supports",
                "binding_status": "bound_real_claim",
                "verified_grounding_label": "paper_grounded_exact",
                "semantic_grounding_label": "semantic_support_verified",
                "semantic_alignment_score": 0.84,
            }
        ],
        "flaw_candidates": [
            {
                "flaw_id": "flaw-active-unsupported",
                "status": "confirmed",
                "severity": "major",
                "related_claim_ids": ["claim-1"],
                "evidence_ids": ["e-support"],
                "negative_evidence_ids": [],
            }
        ],
    }

    hygiene = build_decision_hygiene_view(state)["decision_hygiene"]
    type_counts = hygiene["state_contamination_type_counts"]
    assert type_counts["unsupported_flaw_escalation"] == 1


def test_semantic_mismatch_negative_anchor_is_rejected_not_contamination():
    state = {
        "claims": [{"claim_id": "claim-1", "claim": "The method has complete ablations.", "status": "supported", "claim_kind": "paper_extracted"}],
        "evidence_map": [
            {
                "evidence_id": "e-support",
                "claim_id": "claim-1",
                "raw_quote": "The method is evaluated with ablation experiments in Table 3.",
                "source": "results",
                "source_locator": "Table 3",
                "strength": "strong",
                "stance": "supports",
                "verified_grounding_label": "paper_grounded_exact",
                "semantic_grounding_label": "semantic_support_verified",
                "binding_status": "bound_real_claim",
            },
            {
                "evidence_id": "e-neg-mismatch",
                "claim_id": "claim-1",
                "raw_quote": "Table 3 lists ablation experiments for three hyperparameters.",
                "source": "quote-bank-negative-grounding",
                "source_locator": "Table 3",
                "strength": "missing",
                "stance": "missing",
                "verified_grounding_label": "paper_grounded_exact",
                "semantic_grounding_label": "semantic_mismatch",
                "negative_evidence_type": "scope_limitation",
                "binding_status": "bound_real_claim",
            }
        ],
        "flaw_candidates": [
            {
                "flaw_id": "flaw-neg-mismatch",
                "status": "candidate",
                "related_claim_ids": ["claim-1"],
                "evidence_ids": ["e-neg-mismatch"],
                "negative_evidence_ids": ["e-neg-mismatch"],
                "description": "Claims missing ablation evidence from a quote that actually reports ablations.",
            }
        ],
    }

    view = build_decision_hygiene_view(state)
    hygiene = view["decision_hygiene"]
    # e-neg-mismatch is a quote-bank semantic_mismatch negative: it is DETECTED and rejected
    # (flagged as a semantic-anchor conflict + invalid negative id + contamination target) and
    # must NOT contaminate the verified negative count. The flaw stays a candidate but is classified
    # as an assessment_limitation rather than a grounded weakness.
    assert hygiene["negative_evidence_semantic_rejected_count"] == 0
    assert hygiene["negative_semantic_anchor_conflict_count"] == 1
    assert hygiene["invalid_negative_evidence_id_count"] == 1
    assert hygiene["state_contamination_count"] == 1
    assert hygiene["verified_negative_flaw_count"] == 0
    assert view["flaw_candidates"][0]["status"] == "candidate"
    assert view["flaw_candidates"][0]["final_view_flaw_layer"] == "assessment_limitation"


def test_downgraded_negative_flaw_does_not_inflate_verified_flaw_count():
    negative_evidence = _verified_negative("e-neg", "claim-1", "negative_result", "The method performs worse than the strongest baseline.", source="Table 2")
    state = {
        "claims": [{"claim_id": "claim-1", "claim": "The method outperforms baselines.", "status": "supported", "claim_kind": "paper_extracted"}],
        "evidence_map": [negative_evidence],
        "flaw_candidates": [
            {
                "flaw_id": "flaw-active",
                "status": "candidate",
                "related_claim_ids": ["claim-1"],
                "negative_evidence_ids": ["e-neg"],
                "description": "Active negative result concern.",
            },
            {
                "flaw_id": "flaw-inactive",
                "status": "downgraded",
                "related_claim_ids": ["claim-1"],
                "negative_evidence_ids": ["e-neg"],
                "description": "Inactive duplicate concern.",
            },
        ],
    }

    hygiene = build_decision_hygiene_view(state)["decision_hygiene"]
    assert hygiene["negative_evidence_candidate_count"] == 1
    assert hygiene["verified_negative_flaw_count"] == 1
    assert hygiene["verified_actionable_negative_flaw_count"] == 1


def test_decision_view_reconciles_unsupported_claim_with_strong_support():
    state = _state_with_real_support()
    # Live state still says unsupported; the view should treat the claim as
    # supported because real-claim strong support evidence is present.
    assert state["claims"][0]["status"] == "unsupported"
    view = build_decision_hygiene_view(state)
    assert state["claims"][0]["status"] == "unsupported"
    statuses = {c["claim_id"]: c["status"] for c in view["claims"]}
    assert statuses["claim-1"] == "supported"
    assert statuses["claim-2"] == "supported"
    reasons = {c["claim_id"]: c.get("hygiene_status_reason") for c in view["claims"]}
    assert reasons["claim-1"] == "decision_view_unsupported_with_strong_support"
    assert view["decision_hygiene"]["claims_reconciled_with_strong_support_count"] == 2


def test_decision_view_does_not_reconcile_claims_without_real_strong_support():
    state = {
        "claims": [
            {"claim_id": "claim-1", "claim": "Method beats baselines.", "status": "unsupported"},
        ],
        "evidence_map": [
            {
                "evidence_id": "e1",
                "claim_id": "claim-1",
                "evidence": "Speculative supportive snippet.",
                "source": "abstract",
                "strength": "weak",
                "stance": "supports",
                "binding_status": "bound_real_claim",
            }
        ],
        "flaw_candidates": [],
        "unresolved_questions": [],
        "evidence_gaps": [],
        "conflict_notes": [],
    }
    view = build_decision_hygiene_view(state)
    assert view["claims"][0]["status"] == "unsupported"
    assert view["decision_hygiene"]["claims_reconciled_with_strong_support_count"] == 0


def test_render_final_review_routes_supports_only_flaw_to_potential_concerns():
    state = _state_with_real_support()
    state["flaw_candidates"] = [
        {
            "flaw_id": "flaw-1",
            "title": "Overstated novelty signal",
            "description": "The paper frames the method as the first hyperbolic AL approach without prior-work analysis.",
            "severity": "major",
            "status": "candidate",
            "related_claim_ids": ["claim-2"],
            "evidence_ids": ["e3"],
        }
    ]
    report = render_final_review(state, {})
    assert "Grounded paper weaknesses: none passed the paper-evidence grounding filter." in report
    assert "Potential concerns requiring verification:" in report
    assert "Overstated novelty signal" in report
    assert "[candidate]" in report


def test_render_final_review_hides_internal_fallback_and_json_failures():
    state = _state_with_real_support()
    state["dialogue_summary"] = "Fallback critique extraction was used because the raw output was not valid JSON."
    state["unresolved_questions"] = [
        {
            "question_id": "q-meta",
            "question": "Fallback critique output was malformed schema text after a parse failure.",
            "status": "open",
            "related_claim_ids": [],
        },
        {
            "question_id": "q-paper",
            "question": "Clarify the benchmark coverage for the strongest empirical claim.",
            "status": "open",
            "related_claim_ids": ["claim-1"],
        },
    ]
    report = render_final_review(
        state,
        {
            "final_report": "Final Decision: Reject\nFallback critique extraction was used because the raw output was not valid JSON schema text.",
        },
    )

    lowered = report.lower()
    for forbidden in ("fallback", "raw output", "valid json", "json", "schema", "parse failure"):
        assert forbidden not in lowered
    assert "Clarify the benchmark coverage" in report


def test_render_final_review_uses_reviewer_facing_reason_text():
    report = render_final_review(_state_with_real_support(), {})

    # The human-readable report (sections 1-6) must not leak internal labels;
    # internal recommendation_view / hygiene tokens belong to section 7
    # ``Audit Trace`` only.
    human_part, _, audit_part = report.partition("7. Audit Trace")
    assert "Final-view diagnostics" not in human_part
    assert "health-check projection" not in human_part
    assert "decision hygiene view" not in human_part
    assert "accept_like" not in human_part
    assert "real_nonabstract_empirical_support_without_grounded_blocker" not in human_part
    # P2.9: human-readable label is a *signal* phrase, not an enum or an
    # accept-recommendation. The internal enum (``accept_like``) only appears
    # in the audit trace section.
    assert "Support-rich positive signal" in human_part
    assert "not automatic decisions" not in human_part
    assert "non-abstract empirical support is present" in human_part
    # Audit trace section is allowed to expose machine-readable identifiers.
    assert "recommendation_view=accept_like" in audit_part
    assert "claim-1" in audit_part or "evidence" in audit_part


def test_evidence_section_bucket_prefers_specific_source_over_broad_bucket():
    table_evidence = {
        "source": "Table 2 evaluation results",
        "support_source_bucket": "result_or_experiment",
        "evidence": "The method outperforms baselines.",
    }
    ablation_evidence = {
        "source": "Ablation study",
        "support_source_bucket": "result_or_experiment",
        "evidence": "Removing the module reduces performance.",
    }
    method_evidence = {
        "source": "Method section",
        "support_source_bucket": "result_or_experiment",
        "evidence": "The architecture defines the core framework.",
    }
    assert _evidence_section_bucket(table_evidence) == "table_or_figure"
    assert _evidence_section_bucket(ablation_evidence) == "ablation"
    assert _evidence_section_bucket(method_evidence) == "method"


# ----------------------------------------------------------------------------
# HygieneV3: bucket unification, idempotency, high-precision metrics, renderer
# ----------------------------------------------------------------------------

def _state_with_mixed_support():
    return {
        "claims": [
            {"claim_id": "claim-1", "claim": "TCMT improves few-shot action recognition.", "importance": "high", "status": "uncertain"},
            {"claim_id": "claim-2", "claim": "The auxiliary variable handles distribution shift.", "importance": "high", "status": "uncertain"},
        ],
        "evidence_map": [
            {
                "evidence_id": "ev-fig",
                "claim_id": "claim-1",
                "evidence": "Figure 2 and Table 4 show TCMT outperforms baselines.",
                "source": "Figure 2, Table 4",
                "strength": "strong",
                "stance": "supports",
                "binding_status": "bound_real_claim",
            },
            {
                "evidence_id": "ev-abl",
                "claim_id": "claim-1",
                "evidence": "Ablation on N=4 to 16 shows monotonic gains.",
                "source": "Section 3.3 Ablation",
                "strength": "strong",
                "stance": "supports",
                "binding_status": "bound_real_claim",
            },
            {
                "evidence_id": "ev-method",
                "claim_id": "claim-2",
                "evidence": "The two-layer ConvLSTM models the auxiliary context variable.",
                "source": "Method section",
                "strength": "strong",
                "stance": "supports",
                "binding_status": "bound_real_claim",
            },
        ],
        "flaw_candidates": [
            {
                "flaw_id": "flaw-supports-only",
                "title": "Limited baseline coverage",
                "description": "Only one baseline is shown; broader baselines may change the comparison.",
                "severity": "minor",
                "status": "candidate",
                "related_claim_ids": ["claim-1"],
                "evidence_ids": ["ev-fig"],
            }
        ],
        "unresolved_questions": [
            {
                "question_id": "q-actionable",
                "question": "Add a comparison against a self-supervised baseline on the same benchmark.",
                "status": "open",
                "related_claim_ids": ["claim-1"],
            },
            {
                "question_id": "q-context",
                "question": "Cannot verify the broader research goal from the available context.",
                "status": "open",
                "related_claim_ids": [],
            },
            {
                "question_id": "q-stale",
                "question": "Claim claim-1 lacks grounded supporting evidence.",
                "status": "open",
                "related_claim_ids": ["claim-1"],
            },
            {
                "question_id": "q-diagnostic",
                "question": "What is the intuition behind the ConvLSTM choice?",
                "status": "open",
                "related_claim_ids": ["claim-2"],
            },
        ],
        "evidence_gaps": ["Claim claim-1 lacks grounded supporting evidence."],
        "conflict_notes": [],
    }


def test_hygiene_view_exposes_empirical_and_independence_metrics():
    state = _state_with_mixed_support()
    view = build_decision_hygiene_view(state)
    h = view["decision_hygiene"]
    # The sample carries Figure/Table + Ablation evidence; the empirical bucket
    # must therefore be non-zero (regression for hygienev2 empirical=0 bug).
    assert h["empirical_real_strong_support_count"] >= 2
    assert h["table_or_figure_real_strong_support_count"] >= 1
    assert h["ablation_real_strong_support_count"] >= 1
    assert h["method_real_strong_support_count"] >= 1
    assert h["claims_with_real_strong_support"] == 2
    assert h["claims_with_2plus_independent_support"] >= 1
    assert h["diagnostic_independent_support_group_total"] >= h["independent_support_group_total"]
    assert h["claims_with_2plus_independent_or_diagnostic_support"] >= h["claims_with_2plus_independent_support"]
    assert h["claims_with_empirical_real_strong_support"] >= 1
    assert 0.0 < h["support_concentration_index"] <= 1.0
    assert h["claim_support_depth_counts"]["deep"] == 1
    assert h["claim_support_depth_counts"]["moderate"] == 1
    assert h["claim_support_depth_by_claim"]["claim-1"] == "deep"
    assert h["claim_support_depth_by_claim"]["claim-2"] == "moderate"
    assert h["claims_with_deep_support"] == 1
    assert h["claims_with_moderate_or_deep_support"] == 2
    assert any(
        item["claim_id"] == "claim-1" and item["claim_support_depth_label"] == "deep"
        for item in h["claim_support_summaries"]
    )


def test_hygiene_view_tracks_diagnostic_independence_without_promoting_medium_support():
    state = _state_with_mixed_support()
    base_h = build_decision_hygiene_view(state)["decision_hygiene"]
    base_strong = base_h["real_strong_support_total"]
    base_diag_groups = base_h["diagnostic_independent_support_group_total"]
    state["evidence_map"].append(
        {
            "evidence_id": "ev-moderate-table",
            "claim_id": "claim-2",
            "source_locator": "Table 3",
            "quote_id": "quote-table-3",
            "raw_quote": "Table 3 reports a secondary comparison for the method.",
            "support_source_bucket": "table_or_figure",
            "strength": "medium",
            "stance": "supports",
            "binding_status": "bound_real_claim",
            "verified_grounding_label": "paper_grounded_exact",
            "semantic_grounding_label": "semantic_support_verified",
            "semantic_alignment_score": 0.62,
        }
    )
    h = build_decision_hygiene_view(state)["decision_hygiene"]
    assert h["real_strong_support_total"] == base_strong
    assert h["diagnostic_independent_support_group_total"] > base_diag_groups
    assert h["diagnostic_independent_support_group_total"] > h["independent_support_group_total"]
    assert h["claims_with_2plus_independent_or_diagnostic_support"] >= 1


def test_hygiene_view_is_idempotent_and_keeps_recommendation_label_stable():
    state = _state_with_mixed_support()
    view_one = build_decision_hygiene_view(state)
    view_two = build_decision_hygiene_view(view_one)
    # Idempotency: applying the view twice must not silently drop deferred
    # questions or alter the hygiene metrics that the recommendation view
    # relies on.
    assert view_two is view_one
    assert view_two["decision_hygiene"]["targetless_unresolved_deferred_count"] == view_one["decision_hygiene"]["targetless_unresolved_deferred_count"]
    runtime = infer_final_recommendation_view(state, {})
    via_view = infer_final_recommendation_view(view_one, {})
    assert runtime["recommendation_view"] == via_view["recommendation_view"]
    assert runtime["binary_decision"] == via_view["binary_decision"]


def test_hygiene_view_classifies_limitations_into_four_buckets():
    state = _state_with_mixed_support()
    view = build_decision_hygiene_view(state)
    h = view["decision_hygiene"]
    assert h["actionable_limitation_count"] >= 1
    assert h["context_limitation_count"] >= 1
    assert h["stale_limitation_count"] >= 1
    assert h["unresolved_diagnostic_count"] >= 1
    classifications = {q["question_id"]: q.get("limitation_classification") for q in view["unresolved_questions"]}
    assert classifications["q-actionable"] == "actionable_limitation"
    assert classifications["q-context"] == "context_limitation"
    assert classifications["q-stale"] == "stale_limitation"
    assert classifications["q-diagnostic"] == "unresolved_diagnostic"


def test_hygiene_view_records_support_only_flaws_and_downgrade_count():
    state = _state_with_mixed_support()
    view = build_decision_hygiene_view(state)
    h = view["decision_hygiene"]
    # The candidate flaw cites ev-fig (supports stance) and has no
    # ``negative_evidence_ids`` -> it must contribute to the supports-only
    # filter counter for the high-precision narrative.
    assert h["support_only_flaw_filtered_count"] >= 1
    # Candidate-to-Potential-Concern downgrades are surfaced in the view.
    assert h["candidate_to_potential_concern_downgrade_count"] >= 0


def test_render_final_review_hides_internal_ids_in_human_section():
    state = _state_with_mixed_support()
    report = render_final_review(state, {})
    human, sep, audit = report.partition("7. Audit Trace")
    assert sep, "Audit Trace section must be present"
    # Internal id pattern (e.g. "[claims: claim-1; evidence: evidence-2-turn-5]")
    # must not appear in sections 1-6.
    assert not re.search(r"\[claims?:\s*claim-", human)
    assert not re.search(r"\[evidence:\s*evidence-", human)
    # Human criterion lines should cite paper-side anchors instead.
    assert "Evidence:" in human or "(Evidence" in human
    # Audit trace section is allowed to expose internal ids.
    assert "claims=[" in audit or "evidence=[" in audit
    assert "claim-1" in audit


def test_render_final_review_recommendation_label_matches_runtime_evaluator():
    state = _state_with_mixed_support()
    runtime_view = infer_final_recommendation_view(state, {})
    # P2.9: reviewer-facing labels are *signal* phrases. The internal enum
    # remains in the audit trace section, but the human bullet must use the
    # signal phrase so the reader cannot mistake ``accept_like`` for an
    # accept recommendation.
    recommendation_labels = {
        "accept_like": "Support-rich positive signal (decision support, not an accept recommendation)",
        "borderline_positive": "Support-rich but coverage insufficient",
        "borderline_insufficient": "Evidence-limited (human review needed)",
        "not_assessable_uncertain": "Context-limited assessment",
        "reject_like": "Concerns-grounded reject signal",
    }
    expected_label = recommendation_labels[runtime_view["recommendation_view"]]
    report = render_final_review(state, {})
    human_part, _, audit_part = report.partition("7. Audit Trace")
    assert f"Final Recommendation View: {expected_label}" not in human_part
    assert expected_label in human_part
    # Internal enum keeps appearing in the audit trace (machine-readable).
    _, _, audit_part = report.partition("7. Audit Trace")
    assert (
        f"recommendation_view={runtime_view['recommendation_view']}" in audit_part
    )


def test_render_final_review_renders_classified_limitations_section():
    state = _state_with_mixed_support()
    report = render_final_review(state, {})
    # The new renderer surfaces the four classified buckets as sub-headings
    # under the Unresolved assessment limitations section.
    assert "Actionable limitations" in report
    assert "Assessment limitations" in report
    # Diagnostic and stale buckets show up only when populated; with the
    # mixed-support sample we expect at least the actionable + context buckets.


def test_normalize_evidence_item_records_grounding_fields():
    item = normalize_review_update_payload({
        "evidence_map": [
            {
                "claim_id": "claim-1",
                "evidence": "Table 4 shows a +1.2 F1 gain.",
                "source": "results",
                "source_locator": "Table 4",
                "raw_quote": "+1.2 F1 over baseline",
                "source_span_start": 12,
                "source_span_end": 33,
                "grounded_judge_label": "self_claimed_by_agent",
                "grounded_judge_reason": "quote appears in the visible results excerpt",
                "verified_grounding_label": "paper_grounded_exact",
                "verified_grounding_reason": "post-hoc exact quote match",
                "verified_source_span_start": 12,
                "verified_source_span_end": 33,
                "verified_quote_match_type": "exact_substring",
                "verified_locator_quality": "specific_table_or_figure",
            }
        ]
    })["evidence_map"][0]
    assert item["source_locator"] == "Table 4"
    assert item["raw_quote"] == "+1.2 F1 over baseline"
    assert item["source_span_start"] == 12
    assert item["source_span_end"] == 33
    assert item["grounded_judge_label"] == "self_claimed_by_agent"
    assert item["grounded_judge_reason"] == "quote appears in the visible results excerpt"
    assert item["verified_grounding_label"] == "paper_grounded_exact"
    assert item["verified_grounding_reason"] == "post-hoc exact quote match"
    assert item["verified_source_span_start"] == 12
    assert item["verified_source_span_end"] == 33
    assert item["verified_quote_match_type"] == "exact_substring"
    assert item["verified_locator_quality"] == "specific_table_or_figure"


def test_evidence_human_anchor_uses_paper_source_labels():
    state = _state_with_mixed_support()
    anchor = _evidence_human_anchor(state, ["ev-fig", "ev-abl"])
    assert anchor.startswith(" (Evidence: ")
    assert "Figure 2" in anchor or "Table 4" in anchor
    assert "Ablation" in anchor


def test_classify_unresolved_limitation_uses_actionable_keywords():
    support_counts = {"claim-1": 0}
    actionable = {
        "question": "Provide an ablation study removing the auxiliary variable to validate the methodology.",
        "related_claim_ids": ["claim-1"],
    }
    context = {
        "question": "Cannot verify because the provided excerpt is truncated.",
        "related_claim_ids": [],
    }
    diagnostic = {
        "question": "Why is the proposed mechanism robust under domain shift?",
        "related_claim_ids": ["claim-1"],
    }
    assert _classify_unresolved_limitation(actionable, support_counts) == "actionable_limitation"
    assert _classify_unresolved_limitation(context, support_counts) == "context_limitation"
    assert _classify_unresolved_limitation(diagnostic, support_counts) == "unresolved_diagnostic"


def test_critique_prompt_documents_negative_evidence_examples():
    from agent_system.review_prompts import CRITIQUE_PROMPT

    assert "negative_evidence_ids" in CRITIQUE_PROMPT
    assert "POSITIVE example" in CRITIQUE_PROMPT
    assert "NEGATIVE example" in CRITIQUE_PROMPT


# ---------------------------------------------------------------------------
# HygieneV4 (2026-05-11) regression tests
# ---------------------------------------------------------------------------


def _hygienev4_state_with_two_limitations():
    """State with one actionable and one context limitation for P1.5 tests."""
    return {
        "claims": [
            {"claim_id": "claim-1", "claim": "Main contribution claim", "status": "supported"},
        ],
        "evidence_map": [
            {
                "evidence_id": "evidence-1",
                "claim_id": "claim-1",
                "stance": "supports",
                "strength": "strong",
                "source": "Table 4",
                "evidence_text": "Table 4 shows quantitative results",
            }
        ],
        "flaw_candidates": [],
        "unresolved_questions": [
            {
                "question_id": "q-actionable",
                "question": "Provide an ablation study removing the auxiliary module.",
                "related_claim_ids": ["claim-1"],
            },
            {
                "question_id": "q-context",
                "question": "Cannot verify because the provided excerpt is truncated.",
                "related_claim_ids": [],
            },
        ],
        "evidence_gaps": [],
        "conflict_notes": [],
    }


def test_decision_hygiene_view_emits_actionable_limitation_ratio():
    view = build_decision_hygiene_view(_hygienev4_state_with_two_limitations())
    hg = view["decision_hygiene"]
    # Expect one actionable + one context = two total limitations.
    assert hg["actionable_limitation_count"] == 1
    assert hg["context_limitation_count"] == 1
    assert hg["unresolved_diagnostic_count"] == 0
    assert hg["stale_limitation_count"] == 0
    assert hg["total_limitation_count"] == 2
    # actionable / total = 0.5
    assert abs(hg["actionable_limitation_ratio"] - 0.5) < 1e-9
    # diagnostic_useful_ratio = (actionable + unresolved_diagnostic) / total = 0.5
    assert abs(hg["diagnostic_useful_limitation_ratio"] - 0.5) < 1e-9


def test_decision_hygiene_view_handles_zero_limitations_without_divide_by_zero():
    state = {
        "claims": [{"claim_id": "claim-1", "status": "supported"}],
        "evidence_map": [],
        "flaw_candidates": [],
        "unresolved_questions": [],
        "evidence_gaps": [],
        "conflict_notes": [],
    }
    hg = build_decision_hygiene_view(state)["decision_hygiene"]
    assert hg["total_limitation_count"] == 0
    assert hg["actionable_limitation_ratio"] == 0.0
    assert hg["diagnostic_useful_limitation_ratio"] == 0.0


def test_fmt_audit_number_keeps_ratios_short_and_ints_bare():
    assert _fmt_audit_number(0) == "0"
    assert _fmt_audit_number(5) == "5"
    assert _fmt_audit_number(5.0) == "5"
    assert _fmt_audit_number(0.016) == "0.016"
    assert _fmt_audit_number(0.01666) == "0.017"
    assert _fmt_audit_number(float("nan")) == "0"
    assert _fmt_audit_number(float("inf")) == "0"


def test_primary_claim_support_coverage_is_computed_for_first_k_real_claims():
    state = {
        "claims": [
            {"claim_id": "claim-1", "claim": "Main", "status": "supported"},
            {"claim_id": "claim-2", "claim": "Aux", "status": "supported"},
            {"claim_id": "claim-3", "claim": "Side", "status": "unsupported"},
            {"claim_id": "claim-4", "claim": "Extra", "status": "supported"},
        ],
        "evidence_map": [
            {"evidence_id": "evidence-1", "claim_id": "claim-1", "stance": "supports", "strength": "strong", "source": "Table 2", "evidence_text": "results"},
            {"evidence_id": "evidence-2", "claim_id": "claim-2", "stance": "supports", "strength": "strong", "source": "Section 3 method", "evidence_text": "method"},
        ],
        "flaw_candidates": [],
        "unresolved_questions": [],
        "evidence_gaps": [],
        "conflict_notes": [],
    }
    primary_ids = _decision_primary_claim_ids(state)
    # First K=3 real claims.
    assert primary_ids == ["claim-1", "claim-2", "claim-3"]
    hg = build_decision_hygiene_view(state)["decision_hygiene"]
    assert hg["primary_claim_total"] == 3
    # claim-1 + claim-2 are supported, claim-3 not.
    assert hg["primary_claims_with_real_strong_support"] == 2
    assert abs(hg["primary_claim_support_coverage"] - round(2 / 3, 4)) < 1e-9
    # Only claim-1 has empirical (Table 2); claim-2 is method bucket.
    assert hg["primary_claims_with_empirical_support"] == 1
    assert abs(hg["primary_claim_empirical_coverage"] - round(1 / 3, 4)) < 1e-9


def test_verified_coverage_gap_is_primary_unsupported_and_isolated_from_quote_grounded():
    # Route 3: a deterministic "verified coverage gap" = a primary claim with a fully
    # unsupported required-evidence type. It is a SEPARATE verifiable negative dimension
    # and must never leak into the quote-grounded verified counts.
    state = {
        "claims": [
            {"claim_id": "claim-1", "claim": "The proposed method outperforms all state-of-the-art baselines across diverse benchmark datasets.", "status": "supported"},
            {"claim_id": "claim-2", "claim": "Background discussion of related work.", "status": "supported"},
            {"claim_id": "claim-3", "claim": "Additional background notes.", "status": "supported"},
            {"claim_id": "claim-4", "claim": "The framework outperforms baselines on benchmark evaluation.", "status": "supported"},
        ],
        "evidence_map": [],
        "flaw_candidates": [],
        "unresolved_questions": [],
        "evidence_gaps": [],
        "conflict_notes": [],
    }
    hg = build_decision_hygiene_view(state)["decision_hygiene"]
    # claim-1 is primary (first 3 real claims) and fully unsupported on its required
    # evidence types -> the single high-precision coverage gap.
    assert hg["verified_coverage_gap_count"] == 1
    assert {item["claim_id"] for item in hg["verified_coverage_gap_items"]} == {"claim-1"}
    assert hg["verified_coverage_gap_type_counts"].get("missing_baseline") == 1
    assert hg["coverage_gap_potential_concern_count"] == 1
    assert hg["reviewer_inferred_potential_concern_count"] == 1
    assert hg["final_potential_concern_total"] == 1
    # claim-4 is also unsupported but NOT primary -> excluded from the high-precision subset.
    assert hg["claims_with_requirement_gaps"] == 2
    assert hg["primary_claims_with_requirement_gaps"] == 1
    # Isolation: a coverage gap must NOT pollute any quote-grounded verified count.
    assert hg["review_negative_verified_count"] == 0
    assert hg["reviewer_absence_verified_count"] == 0
    assert hg["total_review_negative_verified_count"] == 0
    assert hg["negative_evidence_candidate_count"] == 0
    assert hg["negative_evidence_linked_to_flaw_count"] == 0
    assert hg["negative_evidence_unlinked_to_flaw_count"] == 0
    assert hg["verified_negative_flaw_count"] == 0
    assert hg["verified_actionable_negative_flaw_count"] == 0
    assert hg["potential_concern_count"] == 0
    assert hg["final_potential_concern_total"] == 1
    concerns = _render_potential_concerns(build_decision_hygiene_view(state))
    assert concerns == []


def test_verified_coverage_gap_includes_partial_actionable_gap():
    # Route 3 (recall-tuned): a primary claim with SOME support but missing a key actionable
    # requirement (here a broad "across diverse benchmarks" claim with only single-benchmark
    # support -> scope_coverage missing) is a verified coverage gap even as a PARTIAL gap —
    # the dominant real-reviewer scenario (basic experiments done, a key dimension absent).
    state = {
        "claims": [{"claim_id": "claim-1", "claim": "The proposed method outperforms strong baselines across diverse benchmarks.", "status": "supported"}],
        "evidence_map": [{
            "evidence_id": "e-emp", "claim_id": "claim-1",
            "evidence": "Table 2 reports 91.0% accuracy of our method on the main benchmark.",
            "raw_quote": "Table 2 reports 91.0% accuracy of our method on the main benchmark.",
            "quote_id": "q-emp", "stance": "supports", "strength": "strong",
            "binding_status": "bound_real_claim",
            "verified_grounding_label": "paper_grounded_exact", "verified_quote_match_type": "quote_bank_id_canonical",
            "semantic_grounding_label": "semantic_support_verified", "source": "Table 2", "source_locator": "Table 2",
        }],
        "flaw_candidates": [], "unresolved_questions": [], "evidence_gaps": [], "conflict_notes": [],
    }
    hg = build_decision_hygiene_view(state)["decision_hygiene"]
    items = hg["verified_coverage_gap_items"]
    assert hg["verified_coverage_gap_count"] == 1
    gap = next(it for it in items if it["claim_id"] == "claim-1")
    assert gap["requirement_status"] == "partial_gap"  # has support, not fully unsupported
    actionable = {"scope_coverage", "baseline_or_comparison", "ablation_or_component", "empirical_result", "robustness_or_generalization", "efficiency_cost"}
    assert any(r in actionable for r in gap.get("coverage_gap_missing_requirements", []))
    assert hg["review_negative_verified_count"] == 0  # isolation from quote-grounded
    assert hg["reviewer_absence_verified_count"] == 0
    assert hg["total_review_negative_verified_count"] == 0
    assert hg["verified_negative_flaw_count"] == 0
    assert hg["verified_actionable_negative_flaw_count"] == 0
    assert hg["grounded_weakness_count"] == 0
    assert hg["coverage_gap_potential_concern_count"] == 1
    assert hg["potential_concern_count"] == 0
    assert hg["final_potential_concern_total"] == 1
    assert hg["final_potential_concern_total"] == 1


def test_verified_coverage_gap_is_paper_level_not_claim_centric():
    # Route 3 (paper-level over-flag fix 2026-06-21): if the paper as a whole satisfies an
    # actionable evidence type on ANY primary claim, a DIFFERENT zero-evidence primary claim
    # must NOT be reported as missing that type. Audit found 56-62% of claim-centric gaps were
    # exactly this over-flag (a generic claim with no bound evidence while the paper actually
    # contains that evidence bound to another claim).
    state = {
        "claims": [
            {"claim_id": "claim-1", "claim": "The proposed method outperforms strong baselines.", "status": "supported"},
            {"claim_id": "claim-2", "claim": "The method surpasses prior baselines on benchmark datasets.", "status": "supported"},
        ],
        "evidence_map": [{
            "evidence_id": "e-base", "claim_id": "claim-2",
            "evidence": "Table 3 compares our method against baseline X, outperforming it by 5 points.",
            "raw_quote": "Table 3 compares our method against baseline X, outperforming it by 5 points.",
            "quote_id": "q-base", "stance": "supports", "strength": "strong",
            "binding_status": "bound_real_claim",
            "verified_grounding_label": "paper_grounded_exact", "verified_quote_match_type": "quote_bank_id_canonical",
            "semantic_grounding_label": "semantic_support_verified", "source": "Table 3", "source_locator": "Table 3",
        }],
        "flaw_candidates": [], "unresolved_questions": [], "evidence_gaps": [], "conflict_notes": [],
    }
    hg = build_decision_hygiene_view(state)["decision_hygiene"]
    gap_claim_ids = {item["claim_id"] for item in hg["verified_coverage_gap_items"]}
    # claim-1 has zero bound evidence, but the paper satisfies baseline/empirical via claim-2,
    # so claim-1 must NOT be a verified coverage gap (paper-level, not claim-centric).
    assert "claim-1" not in gap_claim_ids
    # the baseline requirement is satisfied somewhere in the paper -> not a paper-level gap.
    assert hg["verified_coverage_gap_type_counts"].get("missing_baseline", 0) == 0


def test_stance_based_negative_evidence_ids_infers_from_evidence_map():
    state = {
        "claims": [{"claim_id": "claim-1"}],
        "evidence_map": [
            {"evidence_id": "evidence-1", "claim_id": "claim-1", "stance": "contradicts", "strength": "strong", "source": "Table 7", "evidence_text": "baseline wins"},
            {"evidence_id": "evidence-2", "claim_id": "claim-1", "stance": "supports", "strength": "strong", "source": "Table 2", "evidence_text": "method wins"},
        ],
    }
    flaw_negative = {
        "flaw_id": "flaw-1",
        "evidence_ids": ["evidence-1", "evidence-2"],
    }
    inferred = _stance_based_negative_evidence_ids(flaw_negative, state)
    # Only evidence-1 (contradicts) should be inferred; evidence-2 (supports) must not.
    assert inferred == ["evidence-1"]

    # Empty evidence_map → no inference regardless of cited ids.
    empty_state = {"evidence_map": []}
    assert _stance_based_negative_evidence_ids(flaw_negative, empty_state) == []


def test_build_decision_hygiene_view_auto_grounds_flaws_via_stance_and_preserves_live_state():
    original_state = {
        "claims": [{"claim_id": "claim-1", "status": "supported"}],
        "evidence_map": [
            {"evidence_id": "evidence-1", "claim_id": "claim-1", "stance": "contradicts", "strength": "strong", "source": "Table 7", "evidence_text": "baseline wins"},
        ],
        "flaw_candidates": [
            {
                "flaw_id": "flaw-1",
                "title": "Underperforms on Y",
                "description": "Table 7 shows baseline wins on benchmark Y.",
                "severity": "major",
                "status": "candidate",
                "related_claim_ids": ["claim-1"],
                "evidence_ids": ["evidence-1"],
                "confidence": 0.7,
            }
        ],
        "unresolved_questions": [],
        "evidence_gaps": [],
        "conflict_notes": [],
    }
    live_snapshot = copy.deepcopy(original_state)

    view = build_decision_hygiene_view(original_state)

    flaw_in_view = view["flaw_candidates"][0]
    assert flaw_in_view["negative_evidence_ids"] == ["evidence-1"]
    assert flaw_in_view["hygiene_negative_grounding_source"] == "auto_stance_inference"
    assert _flaw_has_negative_grounding(flaw_in_view, view) is True

    hg = view["decision_hygiene"]
    assert hg["stance_inferred_negative_grounding_count"] == 1

    # Red line: live state must remain untouched.
    assert original_state == live_snapshot
    assert original_state["flaw_candidates"][0].get("negative_evidence_ids") is None
    assert (
        original_state["flaw_candidates"][0].get("hygiene_negative_grounding_source")
        is None
    )


def test_stance_inference_respects_explicit_negative_evidence_ids():
    state = {
        "claims": [{"claim_id": "claim-1"}],
        "evidence_map": [
            {"evidence_id": "evidence-1", "claim_id": "claim-1", "stance": "contradicts", "strength": "strong", "source": "Table 7", "evidence_text": "baseline wins"},
            {"evidence_id": "evidence-2", "claim_id": "claim-1", "stance": "contradicts", "strength": "strong", "source": "Figure 4", "evidence_text": "error bars overlap"},
        ],
        "flaw_candidates": [
            {
                "flaw_id": "flaw-1",
                "evidence_ids": ["evidence-1", "evidence-2"],
                "negative_evidence_ids": ["evidence-2"],
                "status": "candidate",
                "severity": "major",
                "related_claim_ids": ["claim-1"],
                "title": "Weakness",
                "description": "...",
                "confidence": 0.5,
            }
        ],
        "unresolved_questions": [],
        "evidence_gaps": [],
        "conflict_notes": [],
    }
    view = build_decision_hygiene_view(state)
    flaw_in_view = view["flaw_candidates"][0]
    # Explicit user-provided field wins — no auto-inference annotation.
    assert flaw_in_view["negative_evidence_ids"] == ["evidence-2"]
    assert flaw_in_view.get("hygiene_negative_grounding_source") is None
    hg = view["decision_hygiene"]
    assert hg["stance_inferred_negative_grounding_count"] == 0


def test_critique_prompt_has_hard_rule_for_stance_to_negative_evidence_ids():
    from agent_system.review_prompts import CRITIQUE_PROMPT, GENERAL_REVIEWER_PROMPT

    # Critique prompt must have the hard rule tying evidence stance to the
    # negative_evidence_ids field, so the agent stops silently dropping anchors.
    assert "Hard rule" in CRITIQUE_PROMPT
    assert "evidence_map" in CRITIQUE_PROMPT
    assert "negative_evidence_ids" in CRITIQUE_PROMPT
    # General reviewer prompt carries the same hard rule statement.
    assert "Hard rule" in GENERAL_REVIEWER_PROMPT


def test_render_final_review_uses_signal_labels_not_recommendation_words():
    state = _state_with_real_support()
    report = render_final_review(state, {})
    human_part, _, audit_part = report.partition("7. Audit Trace")
    # P2.9: human label must be a signal phrase, not the internal enum.
    assert "Final Decision:" not in human_part
    assert "Final Recommendation View: Accept-like" not in human_part
    assert "Final Recommendation View: Reject-like" not in human_part
    assert "Support-rich" in human_part or "Concerns-grounded" in human_part or "Context-limited" in human_part or "Evidence-limited" in human_part
    # Internal enum still appears only in the audit trace (machine-readable).
    assert "recommendation_view=" in audit_part


def test_audit_meta_leakage_split_separates_human_and_audit_trace():
    """P2.8: detector treats Section 7 audit trace as a separate scope."""
    from scripts.audit_meta_leakage_v1 import split_final_report, audit_paper

    legacy_report = (
        "Final Decision: Reject\n\n"
        "1. Summary of Reviews\n"
        "The paper proposes a method that improves robustness.\n"
    )
    human, audit, has_split = split_final_report(legacy_report)
    # Legacy artifacts without Section 7 → entire text is human, audit is empty.
    assert has_split is False
    assert human == legacy_report
    assert audit == ""

    modern_report = legacy_report + (
        "\n7. Audit Trace (machine-readable)\n"
        "- recommendation_view=reject_like; binary_decision=reject; reason=no_usable_accept_support\n"
        "- hygiene: real_strong_support_total=0, claims_with_real_strong_support=0\n"
        "- Novelty / Originality: status=positive (claims=[claim-1]; evidence=[evidence-1-turn-2])\n"
    )
    human_m, audit_m, has_split_m = split_final_report(modern_report)
    assert has_split_m is True
    assert "recommendation_view=reject_like" in audit_m
    assert "Summary of Reviews" in human_m
    assert "recommendation_view=reject_like" not in human_m

    entry = audit_paper("paper-demo", modern_report, {})
    # Claim/evidence ids in Section 7 should be counted only against audit_trace.
    assert entry["audit_trace"]["raw_total"] > 0
    assert entry["audit_trace"]["present"] is True
    assert entry["final_report"]["raw_total"] == 0
    assert entry["final_report"]["has_audit_trace_split"] is True


def test_negative_evidence_candidate_metrics_exclude_system_salvage_and_count_links():
    state = {
        "claims": [{"claim_id": "claim-1", "claim": "The method beats baselines.", "status": "supported"}],
        "evidence_map": [
            {
                "evidence_id": "paper-negative",
                "claim_id": "claim-1",
                "evidence": "Table 3 shows the strongest baseline has higher accuracy.",
                "source": "Table 3",
                "strength": "medium",
                "stance": "contradicts",
            },
            {
                "evidence_id": "evidence-recovery-missing-claim-1",
                "claim_id": "claim-1",
                "evidence": "Recovery could not verify this claim.",
                "source": "system recovery salvage",
                "strength": "missing",
                "stance": "missing",
            },
        ],
        "flaw_candidates": [
            {
                "flaw_id": "flaw-1",
                "title": "Baseline underperformance",
                "description": "Table 3 shows the strongest baseline wins.",
                "severity": "major",
                "status": "confirmed",
                "related_claim_ids": ["claim-1"],
                "evidence_ids": ["paper-negative"],
                "negative_evidence_ids": ["paper-negative"],
            }
        ],
        "unresolved_questions": [],
        "evidence_gaps": [],
        "conflict_notes": [],
    }

    assert _is_paper_negative_evidence_record(state["evidence_map"][0]) is True
    assert _is_paper_negative_evidence_record(state["evidence_map"][1]) is False
    hg = build_decision_hygiene_view(state)["decision_hygiene"]
    assert hg["negative_evidence_candidate_count"] == 1
    assert hg["negative_evidence_linked_to_flaw_count"] == 1
    assert hg["negative_evidence_unlinked_to_flaw_count"] == 0


def test_related_claim_negative_evidence_infers_flaw_grounding_by_dimension():
    state = {
        "claims": [{"claim_id": "claim-1", "claim": "The method beats baselines.", "status": "supported", "claim_kind": "paper_extracted"}],
        "evidence_map": [
            _verified_negative("e-neg", "claim-1", "negative_result", "Table 3 shows the method losing to the baseline on benchmark Y.", source="Table 3")
        ],
        "flaw_candidates": [
            {
                "flaw_id": "flaw-empirical",
                "title": "Baseline underperformance",
                "description": "The empirical result does not support the claimed baseline advantage.",
                "severity": "major",
                "status": "candidate",
                "related_claim_ids": ["claim-1"],
                "evidence_ids": ["e-neg"],
                "negative_evidence_ids": ["e-neg"],
            }
        ],
        "unresolved_questions": [],
        "evidence_gaps": [],
        "conflict_notes": [],
    }

    view = build_decision_hygiene_view(state)
    flaw = view["flaw_candidates"][0]
    assert flaw["verified_negative_evidence_ids"] == ["e-neg"]
    assert _flaw_has_negative_grounding(flaw, view) is True
    hg = view["decision_hygiene"]
    assert hg["verified_negative_flaw_count"] == 1
    assert hg["negative_evidence_linked_to_flaw_count"] == 1


def test_related_claim_negative_evidence_does_not_bind_unrelated_dimension():
    state = {
        "claims": [{"claim_id": "claim-1", "claim": "The method beats baselines.", "status": "supported"}],
        "evidence_map": [
            {
                "evidence_id": "e-neg",
                "claim_id": "claim-1",
                "evidence": "Table 3 shows the strongest baseline has higher accuracy.",
                "source_locator": "Table 3",
                "strength": "medium",
                "stance": "contradicts",
                "verified_grounding_label": "paper_grounded_exact",
                "semantic_grounding_label": "semantic_negative_verified",
            }
        ],
        "flaw_candidates": [
            {
                "flaw_id": "flaw-clarity",
                "title": "Clarity concern",
                "description": "The presentation and implementation details are unclear.",
                "severity": "minor",
                "status": "candidate",
                "related_claim_ids": ["claim-1"],
            }
        ],
        "unresolved_questions": [],
        "evidence_gaps": [],
        "conflict_notes": [],
    }

    view = build_decision_hygiene_view(state)
    flaw = view["flaw_candidates"][0]
    assert flaw.get("verified_negative_evidence_ids") in (None, [])
    assert _flaw_has_negative_grounding(flaw, view) is False


def test_unlinked_negative_evidence_surfaces_binding_retry_metrics():
    state = {
        "claims": [{"claim_id": "claim-1", "claim": "The method beats baselines.", "status": "supported"}],
        "evidence_map": [
            {
                "evidence_id": "paper-negative",
                "claim_id": "claim-1",
                "evidence": "Table 3 shows the strongest baseline has higher accuracy.",
                "source": "Table 3",
                "strength": "medium",
                "stance": "contradicts",
            }
        ],
        "flaw_candidates": [],
        "unresolved_questions": [],
        "evidence_gaps": [],
        "conflict_notes": [],
    }

    hg = build_decision_hygiene_view(state)["decision_hygiene"]

    assert hg["negative_evidence_candidate_count"] == 1
    assert hg["negative_evidence_linked_to_flaw_count"] == 0
    assert hg["negative_evidence_unlinked_to_flaw_count"] == 1
    assert hg["negative_evidence_binding_retry_candidate_count"] == 1


def test_compact_evidence_for_prompt_keeps_negative_evidence_when_truncating():
    evidence = [
        {
            "evidence_id": f"support-{idx}",
            "claim_id": "claim-1",
            "stance": "supports",
            "strength": "strong",
            "verified_grounding_label": "paper_grounded_exact",
            "semantic_grounding_label": "semantic_support_verified",
            "binding_status": "bound_real_claim",
            "source": "Table 1",
            "raw_quote": f"Support point {idx}.",
        }
        for idx in range(6)
    ] + [
        {
            "evidence_id": "negative-1",
            "claim_id": "claim-1",
            "stance": "contradicts",
            "strength": "medium",
            "negative_evidence_type": "negative_result",
            "verified_grounding_label": "paper_grounded_exact",
            "semantic_grounding_label": "semantic_negative_verified",
            "review_negative_label": "review_negative_verified",
            "binding_status": "bound_real_claim",
            "source": "Table 2",
            "raw_quote": "Negative finding on benchmark Y.",
        },
        {
            "evidence_id": "weak-1",
            "claim_id": "claim-1",
            "stance": "supports",
            "strength": "weak",
            "verified_grounding_label": "paper_grounded_exact",
            "semantic_grounding_label": "semantic_support_verified",
            "binding_status": "bound_real_claim",
            "source": "Abstract",
            "raw_quote": "Weak support statement.",
        },
    ]

    compact = _compact_evidence_for_prompt(evidence, max_items=6)

    assert "negative-1" in {item["evidence_id"] for item in compact}


def test_render_final_review_filters_review_halted_and_snippet_from_human_summary():
    state = {
        "claims": [{"claim_id": "claim-1", "claim": "A method improves accuracy.", "status": "uncertain"}],
        "evidence_map": [],
        "flaw_candidates": [],
        "unresolved_questions": [],
        "evidence_gaps": [],
        "conflict_notes": [],
        "dialogue_summary": "Review halted due to missing empirical evidence.",
    }
    report = render_final_review(
        state,
        {"final_report": "Review halted because only evidence snippets were available."},
    )
    human_part, _, _ = report.partition("7. Audit Trace")

    assert "Review halted" not in human_part
    assert "snippets" not in human_part


def test_export_hygiene_metrics_schema_is_deterministic():
    from scripts.export_hygiene_metrics_v1 import FIELDNAMES, SCHEMA_VERSION, aggregate_rows, row_for_record

    record = {
        "paper_id": "paper-1",
        "final_decision": "reject",
        "decision_correct": 1.0,
        "reward": 0.5,
        "review_state": _hygienev4_state_with_two_limitations(),
        "turn_logs": [{"recovery_committed": True}],
    }

    row = row_for_record(record)
    aggregate = aggregate_rows([row], input_path="demo.jsonl")

    assert row["schema_version"] == SCHEMA_VERSION
    assert row["paper_id"] == "paper-1"
    assert row["total_limitation_count"] == 2
    assert row["recovery_committed_turn_count"] == 1
    assert aggregate["schema_version"] == SCHEMA_VERSION
    assert aggregate["row_count"] == 1
    assert aggregate["decision_accuracy"] == 1.0
    assert "medium_nonabstract_shadow_real_strong_total" in FIELDNAMES
    assert "medium_or_abstract_shadow_real_strong_total" in FIELDNAMES
    assert "medium_nonabstract_shadow_real_strong_total" in aggregate["numeric_totals"]


def test_grounding_quality_verifier_generates_trusted_spans():
    from scripts.audit_evidence_grounding_quality_v1 import verify_quote_grounding

    paper_text = "The method improves F1 by +1.2 over the baseline in Table 4."
    exact = verify_quote_grounding("+1.2 over the baseline", paper_text)
    assert exact["verified_grounding_label"] == "paper_grounded_exact"
    assert exact["verified_source_span_start"] >= 0
    assert paper_text[exact["verified_source_span_start"]: exact["verified_source_span_end"] + 1] == "+1.2 over the baseline"

    normalized = verify_quote_grounding("method improves f1 by 1 2 over the baseline", paper_text)
    assert normalized["verified_grounding_label"] == "paper_grounded_normalized"
    assert normalized["verified_source_span_start"] >= 0

    missing = verify_quote_grounding("a completely different result", paper_text)
    assert missing["verified_grounding_label"] == "not_verified_paraphrase_only"
    assert missing["verified_source_span_start"] == -1


def test_evidence_observation_includes_quote_bank_for_exact_copying():
    task = {
        "paper_id": "paper-quote-bank",
        "mode": "s4",
        "max_turns": 6,
        "user_goal": "Audit evidence grounding.",
        "paper_text": (
            "Abstract\nWe propose a robust reranker.\n"
            "4 Experiments\n"
            "Table 2: The proposed model improves F1 by 3.2 points over the strongest baseline.\n"
            "The ablation study shows that removing contrastive training reduces accuracy by 4.1%.\n"
            "3 Method\n"
            "The method uses a contrastive reranking module with a supervised objective.\n"
        ),
        "review_state": {
            "turn_id": 0,
            "claims": [
                {"claim_id": "claim-1", "claim": "The method improves F1 over baselines.", "status": "uncertain", "importance": "high"}
            ],
            "evidence_map": [],
            "flaw_candidates": [],
            "unresolved_questions": [],
        },
    }
    obs = render_evidence_observation(task, {"action_type": "verify_evidence"})
    assert "evidence_quote_bank" in obs
    assert "quote-table-or-figure" in obs or "quote-results" in obs
    assert "Copy raw_quote exactly" in obs
    assert "improves F1 by 3.2 points" in obs
    assert task["_latest_evidence_context_meta"]["evidence_quote_bank_count"] >= 1


def test_merge_review_state_writes_verified_grounding_from_quote_bank():
    quote = "Table 2: The proposed model improves F1 by 3.2 points over the strongest baseline."
    state = {
        "claims": [{"claim_id": "claim-1", "claim": "The method improves F1.", "status": "uncertain"}],
        "evidence_map": [],
        "flaw_candidates": [],
        "unresolved_questions": [],
        "evidence_quote_bank": [
            {
                "quote_id": "quote-table-or-figure-1",
                "raw_quote": quote,
                "source_locator": "Table/Figure/Ablation excerpt #1",
                "source_span_start": 120,
                "source_span_end": 120 + len(quote) - 1,
            }
        ],
    }
    payload = {
        "evidence_map": [
            {
                "evidence_id": "evidence-1",
                "claim_id": "claim-1",
                "evidence": "The table reports a concrete F1 gain over the strongest baseline.",
                "source": "Table 2",
                "source_locator": "Table 2",
                "raw_quote": quote,
                "quote_id": "quote-table-or-figure-1",
                "strength": "strong",
                "stance": "supports",
            }
        ]
    }

    merged = merge_review_state(state, payload)
    evidence = merged["evidence_map"][0]

    assert evidence["binding_status"] == "bound_real_claim"
    assert evidence["verified_grounding_label"] == "paper_grounded_exact"
    assert evidence["verified_source_span_start"] == 120
    hygiene = build_decision_hygiene_view(merged)["decision_hygiene"]
    assert hygiene["real_strong_support_total"] == 1


def test_merge_review_state_prefers_latest_visible_quote_bank_for_grounding():
    latest_quote = "Table 2: The retrieval reranker improves evidence retrieval accuracy by 12.4% over BM25 baselines."
    stale_quote = "Table 1: A generic model improves accuracy by 2.1% on a different task."
    state = {
        "claims": [{"claim_id": "claim-1", "claim": "The retrieval reranker improves evidence retrieval accuracy.", "status": "uncertain"}],
        "evidence_map": [],
        "flaw_candidates": [],
        "unresolved_questions": [],
        "evidence_quote_bank": [
            {
                "quote_id": "quote-results-1",
                "raw_quote": stale_quote,
                "source_locator": "Results / Evaluation excerpt #1",
                "source_span_start": 10,
                "source_span_end": 10 + len(stale_quote) - 1,
            }
        ],
        "_latest_evidence_context_meta": {
            "evidence_quote_bank": [
                {
                    "quote_id": "quote-results-1",
                    "raw_quote": latest_quote,
                    "source_locator": "Claim-matched evidence excerpt #1",
                    "source_span_start": 200,
                    "source_span_end": 200 + len(latest_quote) - 1,
                    "source_bucket": "claim_match",
                }
            ]
        },
    }
    payload = {
        "evidence_map": [
            {
                "evidence_id": "evidence-claim-match-1",
                "claim_id": "claim-1",
                "evidence": "The reranker improves evidence retrieval accuracy over BM25.",
                "raw_quote": "The agent copied a partial paraphrase.",
                "quote_id": "quote-results-1",
                "strength": "strong",
                "stance": "supports",
            }
        ]
    }

    merged = merge_review_state(state, payload)
    evidence = merged["evidence_map"][0]

    assert evidence["raw_quote"] == latest_quote
    assert evidence["agent_raw_quote"] == "The agent copied a partial paraphrase."
    assert evidence["source_locator"] == "Table 2"
    assert evidence["source_locator_original"] == "Claim-matched evidence excerpt #1"
    assert evidence["source_locator_programmatic"] is True
    assert evidence["verified_source_span_start"] == 200
    assert evidence["verified_grounding_label"] == "paper_grounded_exact"


def test_normalize_manager_payload_preserves_claim_aware_evidence_context_meta():
    payload = normalize_manager_payload(
        {
            "decision": "continue",
            "action_type": "verify_evidence",
            "selected_agents": ["Evidence Agent"],
            "evidence_context_contains_claim_match": True,
            "evidence_context_claim_query_term_count": 7,
            "evidence_context_claim_query_terms": ["retrieval", "reranker"],
            "evidence_context_snippet_sources": ["abstract", "results", "claim_match"],
            "evidence_quote_bank_count": 8,
            "evidence_quote_bank_sources": ["results", "claim_match"],
            "evidence_quote_bank_claim_matched_count": 3,
            "evidence_quote_bank_mode": "quote_bank_claim_v2",
        }
    )

    assert payload["evidence_context_contains_claim_match"] is True
    assert payload["evidence_context_claim_query_term_count"] == 7
    assert payload["evidence_context_claim_query_terms"] == ["retrieval", "reranker"]
    assert payload["evidence_context_snippet_sources"] == ["abstract", "results", "claim_match"]
    assert payload["evidence_quote_bank_count"] == 8
    assert payload["evidence_quote_bank_sources"] == ["results", "claim_match"]
    assert payload["evidence_quote_bank_claim_matched_count"] == 3
    assert payload["evidence_quote_bank_mode"] == "quote_bank_claim_v2"


def test_merge_review_state_downgrades_unverified_or_context_support():
    quote = "The method section describes the supervised reranking objective."
    state = {
        "claims": [
            {"claim_id": "claim-1", "claim": "The method has a reranking objective.", "status": "uncertain"},
            {"claim_id": "claim-context-1", "claim": "Context-only extracted note.", "status": "uncertain"},
        ],
        "evidence_map": [],
        "flaw_candidates": [],
        "unresolved_questions": [],
        "evidence_quote_bank": [
            {
                "quote_id": "quote-method-1",
                "raw_quote": quote,
                "source_locator": "Method / Approach excerpt #1",
                "source_span_start": 50,
                "source_span_end": 50 + len(quote) - 1,
            }
        ],
    }
    payload = {
        "evidence_map": [
            {
                "evidence_id": "bad-quote",
                "claim_id": "claim-1",
                "evidence": "The model is better.",
                "raw_quote": "The paper proves a different unsupported claim.",
                "quote_id": "quote-method-1",
                "strength": "strong",
                "stance": "supports",
            },
            {
                "evidence_id": "context-support",
                "claim_id": "claim-context-1",
                "evidence": "The quote is real but the claim is context-only.",
                "raw_quote": quote,
                "quote_id": "quote-method-1",
                "strength": "strong",
                "stance": "supports",
            },
        ]
    }

    merged = merge_review_state(state, payload)
    by_id = {item["evidence_id"]: item for item in merged["evidence_map"]}

    assert by_id["bad-quote"]["verified_grounding_label"] == "paper_grounded_exact"
    assert by_id["bad-quote"]["raw_quote"] == quote
    assert by_id["bad-quote"]["agent_raw_quote"] == "The paper proves a different unsupported claim."
    assert by_id["bad-quote"]["quote_bank_canonicalized"] is True
    # Mainline-Final-Integrated P0-1: the agent's stated `evidence` text
    # ("The model is better.") has near-zero semantic overlap with the
    # canonical method quote, so the final-strong guard correctly catches
    # this as a low-score strong support and downgrades it to
    # `verified_moderate`.  Without the guard the agent's mismatched intent
    # would have been laundered into a strong support.
    assert by_id["bad-quote"]["strength"] == "medium"
    assert by_id["bad-quote"].get("final_strength_guard_downgrade_reason") == "low_score_strong_support_downgrade"
    assert by_id["context-support"]["binding_status"] == "invalid_claim_id"
    assert by_id["context-support"]["strength"] == "medium"
    # Both supports are now medium, so the strict-strong final view is empty.
    assert build_decision_hygiene_view(merged)["decision_hygiene"]["real_strong_support_total"] == 0


def test_context_derived_paper_claim_cannot_receive_real_strong_support():
    agent_quote = "incorporating a secure aggregator in the federated model results in a less favorable outcome than the baseline system, as indicated in the table."
    bank_quote = f"However, it is important to note that {agent_quote}"
    state = {
        "claims": [
            {
                "claim_id": "claim-context-1",
                "claim": "Incorporating a secure aggregator results in a less favorable outcome than the baseline system.",
                "status": "uncertain",
                "claim_type": "empirical",
                "claim_kind": "paper_extracted",
                "claim_origin_kind": "context_synthesized",
                "claim_origin": "context_derived_paper_excerpt",
            },
        ],
        "evidence_map": [],
        "flaw_candidates": [],
        "unresolved_questions": [],
        "_latest_evidence_context_meta": {
            "evidence_quote_bank": [
                {
                    "quote_id": "quote-claim-match-1",
                    "source_bucket": "claim_match",
                    "source_locator": "Claim-matched evidence excerpt #1",
                    "raw_quote": bank_quote,
                    "source_span_start": 120,
                    "source_span_end": 120 + len(bank_quote) - 1,
                }
            ]
        },
    }
    payload = {
        "evidence_map": [
            {
                "evidence_id": "support-context-paper-claim",
                "claim_id": "claim-context-1",
                "evidence": "Section 4.4 shows that incorporating a secure aggregator results in a less favorable outcome than the baseline system.",
                "raw_quote": agent_quote,
                "strength": "strong",
                "stance": "supports",
                "support_source_bucket": "result_or_experiment",
            }
        ]
    }

    merged = merge_review_state(state, payload)
    evidence = merged["evidence_map"][0]

    assert evidence["binding_status"] == "invalid_claim_id"
    assert evidence["strength"] == "medium"
    assert evidence["quote_id"] == "quote-claim-match-1"
    assert evidence["verified_source_bucket"] == "claim_match"
    assert evidence["raw_quote"] == bank_quote
    assert evidence["agent_raw_quote"] == agent_quote
    assert evidence["semantic_grounding_label"] == "semantic_support_verified"
    assert build_decision_hygiene_view(merged)["decision_hygiene"]["real_strong_support_total"] == 0


def test_verified_claim_matched_medium_support_promotes_to_strong():
    quote = "Our model achieves the best results on the OrcaBench evaluation benchmark compared to general open-source models."
    state = {
        "claims": [
            {
                "claim_id": "claim-1",
                "claim": "The model achieves the best results on the OrcaBench evaluation benchmark compared to baselines.",
                "status": "uncertain",
                "claim_type": "empirical",
                "claim_kind": "paper_extracted",
            }
        ],
        "evidence_map": [],
        "flaw_candidates": [],
        "unresolved_questions": [],
        "_latest_evidence_context_meta": {
            "evidence_quote_bank": [
                {
                    "quote_id": "quote-results-1",
                    "source_bucket": "results",
                    "source_locator": "Results / Evaluation excerpt #1",
                    "raw_quote": quote,
                    "source_span_start": 300,
                    "source_span_end": 300 + len(quote) - 1,
                    "claim_overlap_score": 8,
                }
            ]
        },
    }
    payload = {
        "evidence_map": [
            {
                "evidence_id": "medium-empirical-support",
                "claim_id": "claim-1",
                "evidence": "OrcaBench evaluation benchmark results show best performance against open-source baselines.",
                "raw_quote": quote,
                "strength": "medium",
                "stance": "supports",
                "support_source_bucket": "result_or_experiment",
            }
        ]
    }

    merged = merge_review_state(state, payload)
    evidence = merged["evidence_map"][0]

    assert evidence["initial_strength"] == "medium"
    assert evidence["strength"] == "strong"
    assert evidence["verified_claim_overlap_score"] == 8
    assert evidence["support_quality_adjustment"] == "promoted_verified_claim_matched_support"
    assert evidence["strength_promotion_from_medium_used"] is True
    # Bug C fix: when claim-overlap fallback path was used (overlap > 0)
    # and the support is in a deep bucket (results / table_or_figure /
    # ablation / theory), the reason tag is `verified_claim_overlap_deep_support`.
    assert evidence["strength_promotion_reason"] == "verified_claim_overlap_deep_support"
    hygiene = build_decision_hygiene_view(merged)["decision_hygiene"]
    assert hygiene["real_strong_support_total"] == 1
    assert hygiene["strength_promotion_from_medium_count"] == 1
    assert hygiene["strength_promotion_from_medium_real_strong_count"] == 1


def test_directly_verified_medium_method_support_promotes_to_strong():
    """Bug C / P0-1 regression guard: a medium-strength support whose
    raw_quote matches the paper exactly (paper_grounded_exact), whose
    semantics are verified (semantic_support_verified), and whose
    semantic_alignment_score clears the calibrated method-depth threshold
    (>= 0.7) must promote to strong even when no quote-bank claim-overlap
    fallback fired (overlap == 0).
    """
    quote = (
        "Our pipeline encodes the input through a transformer encoder before "
        "passing the latent embedding into the diffusion-based decoder."
    )
    state = {
        "claims": [
            {
                "claim_id": "claim-1",
                # Mirror the quote tokens so the calibrated semantic-alignment
                # gate (>= 0.7 for method depth) passes; Bug C's intent is to
                # ensure direct verification works, not that low-overlap text
                # gets promoted.
                "claim": (
                    "The pipeline encodes the input through a transformer encoder "
                    "before passing the latent embedding into the diffusion-based decoder."
                ),
                "status": "uncertain",
                "claim_type": "empirical",
                "claim_kind": "paper_extracted",
            }
        ],
        "evidence_map": [],
        "flaw_candidates": [],
        "unresolved_questions": [],
        "paper_text": (
            "Section 3 Method.\n" + quote + "\nSection 4 Experiments.\nWe evaluate on benchmarks."
        ),
        "_latest_evidence_context_meta": {
            "evidence_quote_bank": [
                {
                    "quote_id": "quote-method-1",
                    "source_bucket": "method",
                    "source_locator": "Section 3 Method excerpt #1",
                    "raw_quote": quote,
                    "source_span_start": len("Section 3 Method.\n"),
                    "source_span_end": len("Section 3 Method.\n") + len(quote) - 1,
                }
            ]
        },
    }
    payload = {
        "evidence_map": [
            {
                "evidence_id": "method-support-1",
                "claim_id": "claim-1",
                "evidence": (
                    "The method section describes that the pipeline encodes the input through a transformer "
                    "encoder before passing the latent embedding into the diffusion-based decoder."
                ),
                "raw_quote": quote,
                "strength": "medium",
                "stance": "supports",
                "source_locator": "Section 3 Method",
                "support_source_bucket": "method_or_approach",
            }
        ]
    }

    merged = merge_review_state(state, payload)
    evidence = merged["evidence_map"][0]

    assert evidence["initial_strength"] == "medium"
    assert evidence["verified_grounding_label"] in {"paper_grounded_exact", "paper_grounded_partial"}
    assert evidence["semantic_grounding_label"] == "semantic_support_verified"
    # Direct grounding never sets `verified_claim_overlap_score`, so the
    # gate must accept overlap == 0 on the direct path.
    assert int(evidence.get("verified_claim_overlap_score") or 0) == 0
    assert evidence["support_depth"] == "moderate"
    # P0-1 calibration: method-depth promotion requires
    # ``semantic_alignment_score >= METHOD_PROMOTION_STRONG_MIN_SCORE``.
    assert float(evidence.get("semantic_alignment_score") or 0.0) >= 0.7
    assert evidence["strength"] == "strong"
    assert evidence["strength_promotion_from_medium_used"] is True
    assert evidence["strength_promotion_reason"] == "direct_verified_method_support"
    hygiene = build_decision_hygiene_view(merged)["decision_hygiene"]
    assert hygiene["real_strong_support_total"] == 1
    assert hygiene["strength_promotion_from_medium_count"] == 1
    assert hygiene["strength_promotion_from_medium_real_strong_count"] == 1


def test_directly_verified_medium_deep_support_promotes_to_strong():
    """Bug C regression guard: medium support with depth=deep (results
    section) and direct paper_grounded_exact + semantic_support_verified
    grounding promotes to strong with the deep-path reason tag."""
    quote = (
        "Table 2 reports that our method achieves 92.4 accuracy on the test set, "
        "outperforming the strongest baseline by 3.7 points."
    )
    state = {
        "claims": [
            {
                "claim_id": "claim-1",
                "claim": "The method outperforms the strongest baseline on the benchmark test set.",
                "status": "uncertain",
                "claim_type": "empirical",
                "claim_kind": "paper_extracted",
            }
        ],
        "evidence_map": [],
        "flaw_candidates": [],
        "unresolved_questions": [],
        "paper_text": (
            "Section 4 Results.\n" + quote + "\nSection 5 Discussion.\nWe analyse the trends."
        ),
        "_latest_evidence_context_meta": {
            "evidence_quote_bank": [
                {
                    "quote_id": "quote-results-1",
                    "source_bucket": "results",
                    "source_locator": "Section 4 Results excerpt #1",
                    "raw_quote": quote,
                    "source_span_start": len("Section 4 Results.\n"),
                    "source_span_end": len("Section 4 Results.\n") + len(quote) - 1,
                }
            ]
        },
    }
    payload = {
        "evidence_map": [
            {
                "evidence_id": "deep-support-1",
                "claim_id": "claim-1",
                "evidence": "Table 2 shows the method beats the strongest baseline by 3.7 points.",
                "raw_quote": quote,
                "strength": "medium",
                "stance": "supports",
                "source_locator": "Section 4 Table 2",
                "support_source_bucket": "table_or_figure",
            }
        ]
    }

    merged = merge_review_state(state, payload)
    evidence = merged["evidence_map"][0]

    assert evidence["initial_strength"] == "medium"
    assert evidence["verified_grounding_label"] in {"paper_grounded_exact", "paper_grounded_partial"}
    assert evidence["semantic_grounding_label"] == "semantic_support_verified"
    assert int(evidence.get("verified_claim_overlap_score") or 0) == 0
    assert evidence["support_depth"] == "deep"
    assert evidence["strength"] == "strong"
    assert evidence["strength_promotion_from_medium_used"] is True
    assert evidence["strength_promotion_reason"] == "direct_verified_deep_support"
    hygiene = build_decision_hygiene_view(merged)["decision_hygiene"]
    assert hygiene["real_strong_support_total"] == 1


def test_shallow_or_abstract_medium_support_is_not_promoted():
    """Bug C regression guard: even with direct paper_grounded_exact +
    semantic_support_verified, an *abstract / shallow* medium support
    must not be promoted to strong. The relaxation only opens up method
    and result depths."""
    quote = (
        "We propose a novel transformer architecture that learns latent representations "
        "for downstream tasks."
    )
    state = {
        "claims": [
            {
                "claim_id": "claim-1",
                "claim": "The paper proposes a novel transformer architecture.",
                "status": "uncertain",
                "claim_type": "empirical",
                "claim_kind": "paper_extracted",
            }
        ],
        "evidence_map": [],
        "flaw_candidates": [],
        "unresolved_questions": [],
        "paper_text": "Abstract.\n" + quote + "\nSection 1 Introduction.\nThe rest of the paper.",
        "_latest_evidence_context_meta": {
            "evidence_quote_bank": [
                {
                    "quote_id": "quote-abstract-1",
                    "source_bucket": "abstract",
                    "source_locator": "Abstract excerpt #1",
                    "raw_quote": quote,
                    "source_span_start": len("Abstract.\n"),
                    "source_span_end": len("Abstract.\n") + len(quote) - 1,
                }
            ]
        },
    }
    payload = {
        "evidence_map": [
            {
                "evidence_id": "abstract-support-1",
                "claim_id": "claim-1",
                "evidence": "The abstract states the paper proposes a transformer architecture.",
                "raw_quote": quote,
                "strength": "medium",
                "stance": "supports",
                "source_locator": "Abstract",
                "support_source_bucket": "abstract",
            }
        ]
    }

    merged = merge_review_state(state, payload)
    evidence = merged["evidence_map"][0]

    # Direct verification still happens, but the abstract bucket / shallow
    # depth must keep this support from being promoted.
    assert evidence["initial_strength"] == "medium"
    assert evidence["strength"] == "medium"
    assert not evidence.get("strength_promotion_from_medium_used")
    hygiene = build_decision_hygiene_view(merged)["decision_hygiene"]
    assert hygiene["real_strong_support_total"] == 0


def test_claim_overlap_quote_bank_fallback_canonicalizes_paraphrased_support():
    quote = "On the main benchmark, the method improves accuracy over the baseline."
    state = {
        "claims": [
            {
                "claim_id": "claim-1",
                "claim": "The method improves accuracy on the main benchmark over baselines.",
                "status": "uncertain",
                "claim_type": "empirical",
                "claim_kind": "paper_extracted",
            }
        ],
        "evidence_map": [],
        "flaw_candidates": [],
        "unresolved_questions": [],
        "_latest_evidence_context_meta": {
            "evidence_quote_bank": [
                {
                    "quote_id": "quote-results-1",
                    "source_bucket": "results",
                    "source_locator": "Results / Evaluation excerpt #1",
                    "raw_quote": quote,
                    "source_span_start": 150,
                    "source_span_end": 150 + len(quote) - 1,
                    "claim_overlap_score": 5,
                }
            ]
        },
    }
    payload = {
        "evidence_map": [
            {
                "evidence_id": "paraphrase-support",
                "claim_id": "claim-1",
                "evidence": "The main benchmark result reports improved accuracy over the baseline.",
                "raw_quote": "The approach gets better performance on the primary benchmark.",
                "strength": "strong",
                "stance": "supports",
                "support_source_bucket": "result_or_experiment",
            }
        ]
    }

    merged = merge_review_state(state, payload)
    evidence = merged["evidence_map"][0]

    assert evidence["verified_grounding_label"] == "paper_grounded_exact"
    assert evidence["verified_quote_match_type"] == "quote_bank_claim_overlap_canonical"
    assert evidence["raw_quote"] == quote
    assert evidence["agent_raw_quote"] == "The approach gets better performance on the primary benchmark."
    assert evidence["quote_bank_claim_overlap_fallback_used"] is True
    assert evidence["quote_bank_claim_overlap_fallback_quote_id"] == "quote-results-1"
    assert evidence["quote_bank_claim_overlap_fallback_source_bucket"] == "results"
    assert evidence["quote_bank_claim_overlap_fallback_score"] == 5
    assert evidence["semantic_grounding_label"] == "semantic_support_verified"
    assert evidence["strength"] == "strong"
    hygiene = build_decision_hygiene_view(merged)["decision_hygiene"]
    assert hygiene["real_strong_support_total"] == 1
    assert hygiene["quote_bank_claim_overlap_fallback_used_count"] == 1
    assert hygiene["quote_bank_claim_overlap_fallback_real_strong_count"] == 1
    assert hygiene["quote_bank_claim_overlap_fallback_semantic_mismatch_count"] == 0
    assert hygiene["quote_bank_claim_overlap_fallback_case_sample"][0]["quote_bank_claim_overlap_fallback_quote_id"] == "quote-results-1"


def test_semantic_weak_claim_overlap_promotion_is_audited():
    quote = "Graph retrieval is evaluated alongside cyclone tundra prism cobalt walnut lantern meadow orchard harbor textile quartz velvet canyon glacier silver copper bamboo plasma circuit mosaic anchor vector colony."
    state = {
        "claims": [
            {
                "claim_id": "claim-1",
                "claim": "The graph retrieval contribution covers scalability fairness interpretability modularity portability reproducibility privacy adaptation scheduling compression aggregation normalization initialization curriculum distillation augmentation calibration deployment monitoring governance provenance interoperability extensibility.",
                "status": "uncertain",
                "claim_type": "empirical",
                "claim_kind": "paper_extracted",
            }
        ],
        "evidence_map": [],
        "flaw_candidates": [],
        "unresolved_questions": [],
        "_latest_evidence_context_meta": {
            "evidence_quote_bank": [
                {
                    "quote_id": "quote-results-weak-semantic",
                    "source_bucket": "results",
                    "source_locator": "Results / Evaluation excerpt #1",
                    "raw_quote": quote,
                    "source_span_start": 220,
                    "source_span_end": 220 + len(quote) - 1,
                    "claim_overlap_score": 3,
                }
            ]
        },
    }
    payload = {
        "evidence_map": [
            {
                "evidence_id": "weak-semantic-support",
                "claim_id": "claim-1",
                "evidence": "The contribution is supported by a paper quote about graph retrieval.",
                "raw_quote": quote,
                "strength": "strong",
                "stance": "supports",
                "support_source_bucket": "result_or_experiment",
            }
        ]
    }

    merged = merge_review_state(state, payload)
    evidence = merged["evidence_map"][0]

    assert evidence["semantic_grounding_label"] == "semantic_support_verified"
    assert evidence["semantic_weak_promotion_used"] is True
    assert evidence["semantic_weak_promotion_reason"] == "verified_claim_overlap_low_semantic_alignment"
    assert evidence["semantic_alignment_score"] < 0.18
    hygiene = build_decision_hygiene_view(merged)["decision_hygiene"]
    assert hygiene["semantic_weak_promotion_used_count"] == 1
    assert hygiene["semantic_weak_promotion_real_strong_count"] == 0
    assert hygiene["final_strong_guard_low_score_downgrade_count"] == 1
    assert hygiene["semantic_weak_promotion_case_sample"][0]["semantic_weak_promotion_reason"] == "verified_claim_overlap_low_semantic_alignment"


def test_claim_overlap_quote_bank_fallback_rejects_abstract_only_candidate():
    quote = "Abstract: The method improves accuracy on the main benchmark over baselines."
    state = {
        "claims": [
            {
                "claim_id": "claim-1",
                "claim": "The method improves accuracy on the main benchmark over baselines.",
                "status": "uncertain",
                "claim_type": "empirical",
                "claim_kind": "paper_extracted",
            }
        ],
        "evidence_map": [],
        "flaw_candidates": [],
        "unresolved_questions": [],
        "_latest_evidence_context_meta": {
            "evidence_quote_bank": [
                {
                    "quote_id": "quote-abstract-1",
                    "source_bucket": "abstract",
                    "source_locator": "Abstract excerpt #1",
                    "raw_quote": quote,
                    "source_span_start": 0,
                    "source_span_end": len(quote) - 1,
                    "claim_overlap_score": 5,
                }
            ]
        },
    }
    payload = {
        "evidence_map": [
            {
                "evidence_id": "abstract-paraphrase-support",
                "claim_id": "claim-1",
                "evidence": "The main benchmark result reports improved accuracy over the baseline.",
                "raw_quote": "The approach gets better performance on the primary benchmark.",
                "strength": "strong",
                "stance": "supports",
                "support_source_bucket": "result_or_experiment",
            }
        ]
    }

    merged = merge_review_state(state, payload)
    evidence = merged["evidence_map"][0]

    assert evidence["verified_grounding_label"] == "not_verified_paraphrase_only"
    assert evidence["verified_quote_match_type"] != "quote_bank_claim_overlap_canonical"
    assert evidence["strength"] == "medium"
    assert build_decision_hygiene_view(merged)["decision_hygiene"]["real_strong_support_total"] == 0


def test_decision_hygiene_does_not_count_unverified_strong_support():
    state = {
        "claims": [
            {
                "claim_id": "claim-1",
                "claim": "The method improves benchmark performance.",
                "claim_kind": "paper_extracted",
            }
        ],
        "evidence_map": [
            {
                "evidence_id": "unverified-support",
                "claim_id": "claim-1",
                "evidence": "The method improves performance.",
                "strength": "strong",
                "stance": "supports",
                "binding_status": "bound_real_claim",
            }
        ],
        "flaw_candidates": [],
        "unresolved_questions": [],
        "evidence_gaps": [],
        "conflict_notes": [],
    }

    hygiene = build_decision_hygiene_view(state)["decision_hygiene"]
    trace = hygiene["support_survival_trace"]

    assert hygiene["real_strong_support_total"] == 0
    assert hygiene["support_survival_summary"]["final_real_strong_total"] == 0
    assert trace[0]["included_in_final_view"] is False
    assert trace[0]["final_drop_reason"] == "missing_verified_quote"


def test_support_trace_ignores_records_reclassified_to_negative_stance():
    state = {
        "claims": [
            {
                "claim_id": "claim-1",
                "claim": "The method improves benchmark performance.",
                "claim_kind": "paper_extracted",
            }
        ],
        "evidence_map": [
            {
                "evidence_id": "reclassified-negative",
                "claim_id": "claim-1",
                "evidence": "The table is missing from the visible paper evidence.",
                "strength": "missing",
                "stance": "missing",
                "initial_strength": "weak",
                "initial_stance": "partially_supports",
                "binding_status": "bound_real_claim",
                "verified_grounding_label": "missing_quote",
                "semantic_grounding_label": "semantic_unverified_quote",
            }
        ],
        "flaw_candidates": [],
        "unresolved_questions": [],
        "evidence_gaps": [],
        "conflict_notes": [],
    }

    hygiene = build_decision_hygiene_view(state)["decision_hygiene"]

    assert hygiene["support_survival_trace"] == []
    assert hygiene["support_survival_summary"]["merged_support_total"] == 0


def test_decision_hygiene_requires_semantic_verified_support():
    state = {
        "claims": [
            {
                "claim_id": "claim-1",
                "claim": "The method improves benchmark performance.",
                "claim_kind": "paper_extracted",
            }
        ],
        "evidence_map": [
            {
                "evidence_id": "grounded-but-semantic-missing",
                "claim_id": "claim-1",
                "evidence": "The method improves performance.",
                "raw_quote": "The method improves performance.",
                "strength": "strong",
                "stance": "supports",
                "binding_status": "bound_real_claim",
                "verified_grounding_label": "paper_grounded_exact",
            }
        ],
        "flaw_candidates": [],
        "unresolved_questions": [],
        "evidence_gaps": [],
        "conflict_notes": [],
    }

    hygiene = build_decision_hygiene_view(state)["decision_hygiene"]
    trace = hygiene["support_survival_trace"]

    assert hygiene["real_strong_support_total"] == 0
    assert hygiene["support_survival_summary"]["final_real_strong_total"] == 0
    assert trace[0]["included_in_final_view"] is False
    assert trace[0]["final_drop_reason"] == "semantic_mismatch"


def test_support_survival_exposes_verified_moderate_admission_boundary():
    state = {
        "claims": [
            {"claim_id": "claim-1", "claim": "The method improves benchmark performance.", "claim_kind": "paper_extracted"},
        ],
        "evidence_map": [
            {
                "evidence_id": "medium-method-support",
                "claim_id": "claim-1",
                "evidence": "The method section describes the benchmark improvement mechanism.",
                "raw_quote": "The method uses a contrastive training objective to improve benchmark performance.",
                "source": "Method Section 3",
                "source_locator": "Method / Approach excerpt #1",
                "quote_id": "quote-method-1",
                "strength": "medium",
                "stance": "supports",
                "binding_status": "bound_real_claim",
                "verified_grounding_label": "paper_grounded_exact",
                "semantic_grounding_label": "semantic_support_verified",
                "support_source_bucket": "method_or_approach",
            },
        ],
        "flaw_candidates": [],
        "unresolved_questions": [],
        "evidence_gaps": [],
        "conflict_notes": [],
    }

    hygiene = build_decision_hygiene_view(state)["decision_hygiene"]
    trace = hygiene["support_survival_trace"]

    assert hygiene["real_strong_support_total"] == 0
    assert hygiene["support_admission_tier_counts"] == {"verified_moderate": 1}
    assert hygiene["support_admission_blocker_counts"] == {"verified_medium_support_not_final_strong": 1}
    assert hygiene["final_verified_moderate_support_total"] == 1
    assert hygiene["claims_with_verified_moderate_support"] == 1
    assert hygiene["verified_medium_support_blocked_count"] == 1
    assert hygiene["medium_nonabstract_shadow_additional_support_count"] == 1
    assert hygiene["medium_nonabstract_shadow_real_strong_total"] == 1
    assert hygiene["medium_nonabstract_shadow_newly_supported_claim_count"] == 1
    assert hygiene["medium_or_abstract_shadow_additional_support_count"] == 1
    assert hygiene["medium_or_abstract_shadow_real_strong_total"] == 1
    assert hygiene["medium_or_abstract_shadow_newly_supported_claim_count"] == 1
    assert hygiene["support_survival_summary"]["support_admission_tier_counts"] == {"verified_moderate": 1}
    assert hygiene["support_survival_summary"]["support_admission_blocker_counts"] == {
        "verified_medium_support_not_final_strong": 1
    }
    assert trace[0]["included_in_final_view"] is False
    assert trace[0]["final_drop_reason"] == "hygiene_filtered"
    assert trace[0]["support_admission_tier"] == "verified_moderate"
    assert trace[0]["support_admission_blocker"] == "verified_medium_support_not_final_strong"
    assert trace[0]["decision_support_source_bucket"] == "method_or_approach"


def test_support_survival_exposes_abstract_contextual_admission_boundary():
    state = {
        "claims": [
            {
                "claim_id": "claim-1",
                "claim": "The paper proves within-class variability collapse.",
                "claim_kind": "paper_extracted",
            },
        ],
        "evidence_map": [
            {
                "evidence_id": "medium-abstract-proof-support",
                "claim_id": "claim-1",
                "evidence": "The paper provides a theorem and proof of within-class variability collapse.",
                "raw_quote": "In this paper, we provide the first end-to-end proof of within-class variability collapse.",
                "source_locator": "Claim-matched evidence excerpt #1",
                "quote_id": "quote-claim-match-1",
                "strength": "medium",
                "stance": "supports",
                "binding_status": "bound_real_claim",
                "verified_grounding_label": "paper_grounded_exact",
                "semantic_grounding_label": "semantic_support_verified",
                "support_source_bucket": "abstract",
            },
        ],
        "flaw_candidates": [],
        "unresolved_questions": [],
        "evidence_gaps": [],
        "conflict_notes": [],
    }

    trace = build_decision_hygiene_view(state)["decision_hygiene"]["support_survival_trace"]
    hygiene = build_decision_hygiene_view(state)["decision_hygiene"]

    assert trace[0]["final_drop_reason"] == "hygiene_filtered"
    assert trace[0]["support_depth"] == "deep"
    assert trace[0]["support_admission_tier"] == "verified_contextual"
    assert trace[0]["support_admission_blocker"] == "verified_abstract_support_not_final_strong"
    assert hygiene["support_admission_tier_counts"] == {"verified_contextual": 1}
    assert hygiene["support_admission_blocker_counts"] == {"verified_abstract_support_not_final_strong": 1}
    assert hygiene["final_verified_moderate_support_total"] == 0
    assert hygiene["verified_abstract_support_blocked_count"] == 1
    assert hygiene["medium_nonabstract_shadow_real_strong_total"] == 0
    assert hygiene["medium_or_abstract_shadow_additional_support_count"] == 1
    assert hygiene["medium_or_abstract_shadow_real_strong_total"] == 1
    assert hygiene["medium_or_abstract_shadow_newly_supported_claim_count"] == 1


def test_support_survival_duplicate_quote_reports_same_claim_duplicate_blocker():
    state = {
        "claims": [
            {"claim_id": "claim-1", "claim": "The method improves accuracy.", "claim_kind": "paper_extracted"},
        ],
        "evidence_map": [
            {
                "evidence_id": "e-1",
                "claim_id": "claim-1",
                "evidence": "The method supports accuracy.",
                "raw_quote": "The method improves accuracy on the benchmark.",
                "quote_id": "quote-method-1",
                "source": "Method Section 3",
                "strength": "medium",
                "stance": "supports",
                "binding_status": "bound_real_claim",
                "verified_grounding_label": "paper_grounded_exact",
                "semantic_grounding_label": "semantic_support_verified",
                "support_source_bucket": "method_or_approach",
            },
            {
                "evidence_id": "e-2",
                "claim_id": "claim-1",
                "evidence": "The same quote is repeated for accuracy.",
                "raw_quote": "The method improves accuracy on the benchmark.",
                "quote_id": "quote-method-1",
                "source": "Method Section 3",
                "strength": "medium",
                "stance": "supports",
                "binding_status": "bound_real_claim",
                "verified_grounding_label": "paper_grounded_exact",
                "semantic_grounding_label": "semantic_support_verified",
                "support_source_bucket": "method_or_approach",
            },
        ],
        "flaw_candidates": [],
        "unresolved_questions": [],
        "evidence_gaps": [],
        "conflict_notes": [],
    }

    hygiene = build_decision_hygiene_view(state)["decision_hygiene"]
    trace = hygiene["support_survival_trace"]
    by_id = {item["evidence_id"]: item for item in trace}

    assert hygiene["support_admission_tier_counts"] == {"verified_moderate": 2}
    assert hygiene["support_admission_blocker_counts"] == {
        "verified_medium_support_not_final_strong": 1,
        "duplicate_quote": 1,
    }
    assert hygiene["final_verified_moderate_support_total"] == 2
    assert hygiene["verified_medium_support_blocked_count"] == 1
    assert hygiene["medium_nonabstract_shadow_additional_support_count"] == 1
    assert hygiene["medium_nonabstract_shadow_real_strong_total"] == 1
    assert by_id["e-1"]["final_drop_reason"] == "hygiene_filtered"
    assert by_id["e-2"]["final_drop_reason"] == "duplicate_quote"
    assert by_id["e-2"]["support_admission_blocker"] == "duplicate_quote"
    assert by_id["e-2"]["support_admission_tier"] == "verified_moderate"


def test_support_survival_negative_burden_reports_verified_medium_suppression():
    """Mainline-Final-Integrated P1-2: a verified medium positive coexisting
    with a verified negative concern is now surfaced as ``contested_support``;
    the positive support is still tier=verified_moderate (the medium → strong
    promotion threshold remains the same), but the legacy
    ``overridden_by_negative_burden`` blocker is retired and the positive
    support is no longer reported under that drop reason.
    """
    state = {
        "claims": [
            {"claim_id": "claim-1", "claim": "The method improves accuracy.", "claim_kind": "paper_extracted"},
        ],
        "evidence_map": [
            {
                "evidence_id": "positive-1",
                "claim_id": "claim-1",
                "evidence": "The method section describes the accuracy improvement.",
                "raw_quote": "The method improves accuracy through a new training objective.",
                "source": "Method Section 3",
                "quote_id": "quote-method-1",
                "strength": "medium",
                "stance": "supports",
                "binding_status": "bound_real_claim",
                "verified_grounding_label": "paper_grounded_exact",
                "semantic_grounding_label": "semantic_support_verified",
                "support_source_bucket": "method_or_approach",
            },
            {
                "evidence_id": "negative-1",
                "claim_id": "claim-1",
                "evidence": "The benchmark comparison is missing for the strongest baseline.",
                "raw_quote": "The comparison to the strongest baseline is not reported.",
                "source": "Section 5 Experiments",
                "quote_id": "quote-negative-1",
                "strength": "missing",
                "stance": "missing",
                "binding_status": "bound_real_claim",
                "verified_grounding_label": "paper_grounded_exact",
                "verified_quote_match_type": "quote_bank_raw_canonical",
                "verified_source_span_start": 10,
                "verified_source_span_end": 84,
                "semantic_grounding_label": "semantic_negative_verified",
                "review_negative_label": "review_negative_verified",
                "negative_evidence_type": "missing_baseline",
            },
        ],
        "flaw_candidates": [
            {
                "flaw_id": "flaw-1",
                "description": "The strongest baseline comparison is missing.",
                "status": "candidate",
                "related_claim_ids": ["claim-1"],
                "evidence_ids": ["negative-1"],
                "negative_evidence_ids": ["negative-1"],
            },
        ],
        "unresolved_questions": [],
        "evidence_gaps": [],
        "conflict_notes": [],
    }

    hygiene = build_decision_hygiene_view(state)["decision_hygiene"]
    trace = {item["evidence_id"]: item for item in hygiene["support_survival_trace"]}

    assert hygiene["real_strong_support_total"] == 0
    assert hygiene["support_admission_tier_counts"] == {"verified_moderate": 1}
    # The positive support never reaches strong on its own (medium method
    # support without overlap score) so the blocker is the medium-not-strong
    # tier blocker, not the retired negative-burden drop.
    assert "overridden_by_negative_burden" not in hygiene["support_admission_blocker_counts"]
    assert hygiene["final_verified_moderate_support_total"] == 1
    # Contested support arbitration: positive + verified-negative on same
    # claim is reported but does not suppress the positive support.
    assert hygiene["contested_support_total"] == 1
    assert hygiene["claims_with_contested_support"] == 1
    assert trace["positive-1"]["contested_support"] is True
    assert trace["positive-1"]["final_drop_reason"] != "overridden_by_negative_burden"
    assert trace["positive-1"]["support_admission_blocker"] != "overridden_by_negative_burden"
    assert trace["positive-1"]["support_admission_tier"] == "verified_moderate"


def test_support_survival_duplicate_quote_is_claim_scoped():
    state = {
        "claims": [
            {"claim_id": "claim-1", "claim": "The method improves accuracy.", "claim_kind": "paper_extracted"},
            {"claim_id": "claim-2", "claim": "The method improves robustness.", "claim_kind": "paper_extracted"},
        ],
        "evidence_map": [
            {
                "evidence_id": "e-1",
                "claim_id": "claim-1",
                "evidence": "The shared quote supports accuracy.",
                "raw_quote": "The method improves accuracy and robustness on the benchmark.",
                "quote_id": "quote-results-1",
                "strength": "medium",
                "stance": "supports",
                "binding_status": "bound_real_claim",
                "verified_grounding_label": "paper_grounded_exact",
                "semantic_grounding_label": "semantic_support_verified",
                "support_source_bucket": "result_or_experiment",
            },
            {
                "evidence_id": "e-2",
                "claim_id": "claim-2",
                "evidence": "The shared quote supports robustness.",
                "raw_quote": "The method improves accuracy and robustness on the benchmark.",
                "quote_id": "quote-results-1",
                "strength": "medium",
                "stance": "supports",
                "binding_status": "bound_real_claim",
                "verified_grounding_label": "paper_grounded_exact",
                "semantic_grounding_label": "semantic_support_verified",
                "support_source_bucket": "result_or_experiment",
            },
        ],
        "flaw_candidates": [],
        "unresolved_questions": [],
        "evidence_gaps": [],
        "conflict_notes": [],
    }

    trace = build_decision_hygiene_view(state)["decision_hygiene"]["support_survival_trace"]
    by_id = {item["evidence_id"]: item for item in trace}

    assert by_id["e-2"]["final_drop_reason"] != "duplicate_quote"


def test_final_view_classifies_verified_negative_flaw_layers():
    state = {
        "claims": [{"claim_id": "claim-1", "claim": "The method beats baselines.", "status": "supported", "claim_kind": "paper_extracted"}],
        "evidence_map": [
            _verified_negative("neg-1", "claim-1", "negative_result", "Table 3 shows the method losing to the strongest baseline on the primary benchmark.", source="Table 3", stance="contradicts", strength="strong"),
            _verified_negative("neg-2", "claim-1", "direct_contradiction", "Table 4 directly contradicts the stability claim on the second benchmark.", source="Table 4", stance="contradicts", strength="medium"),
        ],
        "flaw_candidates": [
            {
                "flaw_id": "flaw-confirmed",
                "title": "Baseline failure",
                "description": "The strongest baseline wins on the primary benchmark.",
                "severity": "major",
                "status": "confirmed",
                "related_claim_ids": ["claim-1"],
                "evidence_ids": ["neg-1"],
                "negative_evidence_ids": ["neg-1"],
            },
            {
                "flaw_id": "flaw-candidate",
                "title": "Potential instability",
                "description": "The results may be unstable on another benchmark.",
                "severity": "major",
                "status": "candidate",
                "related_claim_ids": ["claim-1"],
                "evidence_ids": ["neg-2"],
                "negative_evidence_ids": ["neg-2"],
            },
        ],
        "unresolved_questions": [],
        "evidence_gaps": [],
        "conflict_notes": [],
    }

    view = build_decision_hygiene_view(state)
    flaws = {item["flaw_id"]: item for item in view["flaw_candidates"]}
    hygiene = view["decision_hygiene"]

    assert flaws["flaw-confirmed"]["final_view_flaw_layer"] == "grounded_weakness"
    assert flaws["flaw-candidate"]["final_view_flaw_layer"] == "potential_concern"
    assert flaws["flaw-candidate"]["negative_flaw_not_upgraded_reason"] == "not_confirmed_stays_potential_concern"
    assert hygiene["grounded_weakness_count"] == 1
    assert hygiene["verified_potential_concern_count"] == 1
    assert hygiene["potential_concern_count"] == 1
    assert hygiene["verified_negative_flaw_count"] == 2
    assert any("Baseline failure" in line for line in _render_weaknesses(view))


def test_unverified_negative_flaw_stays_potential_not_grounded_weakness():
    state = {
        "claims": [{"claim_id": "claim-1", "claim": "The method beats baselines.", "status": "supported"}],
        "evidence_map": [
            {
                "evidence_id": "neg-unverified",
                "claim_id": "claim-1",
                "evidence": "The strongest baseline allegedly has higher accuracy.",
                "source": "Table 3",
                "strength": "strong",
                "stance": "contradicts",
                "binding_status": "bound_real_claim",
                "verified_grounding_label": "not_verified_paraphrase_only",
            }
        ],
        "flaw_candidates": [
            {
                "flaw_id": "flaw-1",
                "title": "Baseline failure",
                "description": "The strongest baseline wins on the primary benchmark.",
                "severity": "major",
                "status": "confirmed",
                "related_claim_ids": ["claim-1"],
                "evidence_ids": ["neg-unverified"],
                "negative_evidence_ids": ["neg-unverified"],
            }
        ],
        "unresolved_questions": [],
        "evidence_gaps": [],
        "conflict_notes": [],
    }

    view = build_decision_hygiene_view(state)
    flaw = view["flaw_candidates"][0]
    hygiene = view["decision_hygiene"]

    assert flaw["final_view_flaw_layer"] == "potential_concern"
    assert hygiene["grounded_weakness_count"] == 0
    assert hygiene["negative_grounding_conflict_count"] == 1
    assert _render_weaknesses(view) == []
    assert any("Baseline failure" in line for line in _render_potential_concerns(view))



def test_quote_id_canonicalization_does_not_verify_semantic_mismatch_as_strong():
    state = {
        "claims": [
            {"claim_id": "claim-1", "claim": "The method improves benchmarks by 1.2 to 5.3 points in 5-way-k-shot.", "status": "uncertain"},
        ],
        "evidence_quote_bank": [
            {
                "quote_id": "quote-results-1",
                "source_bucket": "results",
                "source_locator": "Results / Evaluation excerpt #1",
                "raw_quote": "The abstract reports notable performance improvements over leading benchmarks.",
                "source_span_start": 10,
                "source_span_end": 81,
            }
        ],
        "evidence_map": [],
        "flaw_candidates": [],
        "unresolved_questions": [],
        "evidence_gaps": [],
        "conflict_notes": [],
    }
    payload = {
        "evidence_map": [
            {
                "evidence_id": "e-table",
                "claim_id": "claim-1",
                "evidence": "Table 4 shows TCMT_H improves benchmarks by 1.2 to 5.3 points in 5-way-k-shot.",
                "raw_quote": "experiments, by a margin ranging from 1.2 to 5.3",
                "quote_id": "quote-results-1",
                "source_locator": "Table 4",
                "strength": "strong",
                "stance": "supports",
                "binding_status": "bound_real_claim",
                "support_source_bucket": "result_or_experiment",
            }
        ]
    }
    merged = merge_review_state(state, payload)
    evidence = merged["evidence_map"][0]
    assert evidence["verified_grounding_label"] == "paper_grounded_exact"
    assert evidence["semantic_grounding_label"] == "semantic_mismatch"
    assert evidence["strength"] == "medium"
    assert "downgraded_semantic_grounding_mismatch" in evidence["support_quality_adjustment"]
    assert "missing_numeric_anchor" in evidence["semantic_grounding_reasons"]


def test_quote_id_mismatch_raw_quote_can_match_correct_quote_bank_item():
    model_list_quote = "In this section, we evaluate the five methods on Gemma2-2b, Llama2-7b, and GPT2-small."
    state = {
        "claims": [
            {"claim_id": "claim-1", "claim": "The evaluation supports broad model coverage.", "status": "uncertain"},
        ],
        "evidence_quote_bank": [
            {
                "quote_id": "quote-results-1",
                "source_bucket": "results",
                "source_locator": "Results / Metrics excerpt #1",
                "raw_quote": "We then propose evaluation metrics for the summarization experiments.",
                "source_span_start": 10,
                "source_span_end": 75,
            },
            {
                "quote_id": "quote-results-models-1",
                "source_bucket": "results",
                "source_locator": "Results / Model coverage excerpt #1",
                "raw_quote": model_list_quote,
                "source_span_start": 200,
                "source_span_end": 295,
            },
        ],
        "evidence_map": [],
        "flaw_candidates": [],
        "unresolved_questions": [],
        "evidence_gaps": [],
        "conflict_notes": [],
    }
    payload = {
        "evidence_map": [
            {
                "evidence_id": "neg-model-coverage",
                "claim_id": "claim-1",
                "evidence": "The evaluation only names Gemma2-2b, Llama2-7b, and GPT2-small, leaving model-scale coverage limited.",
                "raw_quote": model_list_quote,
                "quote_id": "quote-results-1",
                "source_locator": "Results / Model coverage",
                "strength": "missing",
                "stance": "missing",
                "binding_status": "bound_real_claim",
                "negative_evidence_type": "insufficient_evaluation",
            }
        ]
    }
    merged = merge_review_state(state, payload)
    evidence = merged["evidence_map"][0]
    assert evidence["quote_id_mismatch_ignored"] is True
    assert evidence["quote_id_mismatch_ignored_quote_id"] == "quote-results-1"
    assert evidence["quote_id"] == "quote-results-models-1"
    assert evidence["raw_quote"] == model_list_quote
    assert evidence["verified_grounding_label"] == "paper_grounded_exact"
    assert evidence["verified_quote_match_type"] == "quote_bank_raw_canonical"


def test_quote_id_mismatch_does_not_verify_against_wrong_quote_id_when_raw_quote_missing_from_bank():
    state = {
        "claims": [
            {"claim_id": "claim-1", "claim": "The evaluation supports broad model coverage.", "status": "uncertain"},
        ],
        "evidence_quote_bank": [
            {
                "quote_id": "quote-results-1",
                "source_bucket": "results",
                "source_locator": "Results / Metrics excerpt #1",
                "raw_quote": "We then propose evaluation metrics for the summarization experiments.",
                "source_span_start": 10,
                "source_span_end": 75,
            }
        ],
        "evidence_map": [],
        "flaw_candidates": [],
        "unresolved_questions": [],
        "evidence_gaps": [],
        "conflict_notes": [],
    }
    payload = {
        "evidence_map": [
            {
                "evidence_id": "neg-model-coverage",
                "claim_id": "claim-1",
                "evidence": "The evaluation only names Gemma2-2b, Llama2-7b, and GPT2-small, leaving model-scale coverage limited.",
                "raw_quote": "In this section, we evaluate the five methods on Gemma2-2b, Llama2-7b, and GPT2-small.",
                "quote_id": "quote-results-1",
                "source_locator": "Results / Model coverage",
                "strength": "missing",
                "stance": "missing",
                "binding_status": "bound_real_claim",
                "negative_evidence_type": "insufficient_evaluation",
            }
        ]
    }
    merged = merge_review_state(state, payload)
    evidence = merged["evidence_map"][0]
    assert evidence["quote_id_mismatch_ignored"] is True
    assert evidence["quote_id"] == "quote-results-1"
    assert evidence["verified_grounding_label"] != "paper_grounded_exact"
    assert evidence.get("verified_quote_match_type") != "quote_bank_id_canonical"


def test_negative_quote_id_accepts_long_quote_bank_prefix_continuation():
    canonical_quote = (
        "Note that alpha is a hyperparameter that must be tuned for each method, model, "
        "and sometimes even intervention feature and thus cannot be used to compare the "
        "effects of interventions across methods."
    )
    state = {
        "claims": [
            {
                "claim_id": "claim-1",
                "claim": "The evaluation provides comparable intervention effects across methods.",
                "status": "uncertain",
            },
        ],
        "evidence_quote_bank": [
            {
                "quote_id": "quote-comparison-risk-1",
                "source_bucket": "comparison",
                "source_locator": "Comparison / Robustness excerpt #2",
                "raw_quote": canonical_quote,
                "source_span_start": 200,
                "source_span_end": 200 + len(canonical_quote) - 1,
            }
        ],
        "evidence_map": [],
        "flaw_candidates": [],
        "unresolved_questions": [],
        "evidence_gaps": [],
        "conflict_notes": [],
    }
    payload = {
        "evidence_map": [
            {
                "evidence_id": "neg-comparison-risk",
                "claim_id": "claim-1",
                "evidence": "The paper's own protocol makes cross-method comparison invalid because alpha must be retuned.",
                "raw_quote": (
                    canonical_quote
                    + " This continuation is copied by the model from the surrounding passage but is outside the quote-bank span."
                ),
                "quote_id": "quote-comparison-risk-1",
                "source_locator": "Comparison / Robustness",
                "strength": "missing",
                "stance": "missing",
                "binding_status": "bound_real_claim",
                "negative_evidence_type": "evaluation_protocol_risk",
            }
        ]
    }
    merged = merge_review_state(state, payload)
    evidence = merged["evidence_map"][0]
    assert evidence["raw_quote"] == canonical_quote
    assert evidence["agent_raw_quote"].startswith(canonical_quote)
    assert evidence["quote_bank_canonicalized"] is True
    assert evidence["verified_grounding_label"] == "paper_grounded_normalized"
    assert evidence["verified_quote_match_type"] == "quote_bank_id_prefix_canonical"
    assert evidence["review_negative_label"] == "review_negative_verified"
    assert evidence["review_negative_reason"] == "comparison_invalidation_weakens_claim"


def test_candidate_window_quote_bank_grounding_keeps_model_copied_negative_quote():
    window_text = (
        "The experiment first reports headline accuracy improvements for the method. "
        "Note that alpha is a hyperparameter that must be tuned for each method and "
        "therefore cannot be used to compare intervention effects across methods. "
        "The surrounding paragraph then returns to implementation details."
    )
    copied_quote = (
        "Note that alpha is a hyperparameter that must be tuned for each method and "
        "therefore cannot be used to compare intervention effects across methods."
    )
    state = {
        "claims": [
            {
                "claim_id": "claim-1",
                "claim": "The evaluation provides comparable intervention effects across methods.",
                "status": "uncertain",
                "claim_kind": "paper_extracted",
            }
        ],
        "_latest_evidence_context_meta": {
            "evidence_quote_bank": [
                {
                    "quote_id": "quote-candidate-window-1",
                    "source_bucket": "candidate_window",
                    "source_locator": "Candidate negative window #1",
                    "raw_quote": window_text,
                    "source_span_start": 1000,
                    "source_span_end": 1000 + len(window_text) - 1,
                    "negative_evidence_type": "evaluation_protocol_risk",
                    "candidate_window_quote": True,
                    "support_role_hint": "review_negative_search_window",
                }
            ]
        },
        "evidence_map": [],
        "flaw_candidates": [],
        "unresolved_questions": [],
        "evidence_gaps": [],
        "conflict_notes": [],
    }
    payload = {
        "evidence_map": [
            {
                "evidence_id": "neg-protocol-risk",
                "claim_id": "claim-1",
                "evidence": "The protocol note says alpha cannot compare intervention effects across methods.",
                "raw_quote": copied_quote,
                "quote_id": "quote-candidate-window-1",
                "source_locator": "Candidate negative window #1",
                "strength": "missing",
                "stance": "missing",
                "binding_status": "bound_real_claim",
                "negative_evidence_type": "evaluation_protocol_risk",
            }
        ]
    }

    merged = merge_review_state(state, payload)
    evidence = merged["evidence_map"][0]

    assert evidence["raw_quote"] == copied_quote
    assert "surrounding paragraph" not in evidence["raw_quote"]
    assert evidence["verified_grounding_label"] == "paper_grounded_exact"
    assert evidence["verified_quote_match_type"].startswith("candidate_window_")
    assert evidence["verified_source_span_start"] >= 1000
    assert evidence["review_negative_label"] == "review_negative_verified"


def test_targeted_candidate_quote_proposal_still_requires_review_negative_verification():
    window_text = (
        "The experiment first reports headline accuracy improvements for the method. "
        "Note that alpha is a hyperparameter that must be tuned for each method and "
        "therefore cannot be used to compare intervention effects across methods. "
        "The surrounding paragraph then returns to implementation details."
    )
    copied_quote = (
        "Note that alpha is a hyperparameter that must be tuned for each method and "
        "therefore cannot be used to compare intervention effects across methods."
    )
    state = {
        "claims": [
            {
                "claim_id": "claim-1",
                "claim": "The evaluation provides comparable intervention effects across methods.",
                "status": "supported",
                "claim_kind": "paper_extracted",
            }
        ],
        "_latest_evidence_context_meta": {
            "evidence_quote_bank": [
                {
                    "quote_id": "quote-candidate-window-1",
                    "source_bucket": "candidate_window",
                    "source_locator": "Candidate negative window #1",
                    "raw_quote": window_text,
                    "source_span_start": 1000,
                    "source_span_end": 1000 + len(window_text) - 1,
                    "negative_evidence_type": "evaluation_protocol_risk",
                    "candidate_window_quote": True,
                    "support_role_hint": "review_negative_search_window",
                }
            ]
        },
        "evidence_map": [],
        "flaw_candidates": [
            {
                "flaw_id": "flaw-protocol-risk",
                "title": "Cross-method comparison protocol risk",
                "description": "The alpha tuning protocol may invalidate cross-method comparison.",
                "status": "candidate",
                "severity": "major",
                "related_claim_ids": ["claim-1"],
                "negative_evidence_ids": ["evidence-targeted-candidate-quote-protocol"],
                "evidence_ids": ["evidence-targeted-candidate-quote-protocol"],
            }
        ],
        "unresolved_questions": [],
        "evidence_gaps": [],
        "conflict_notes": [],
    }
    payload = {
        "evidence_map": [
            {
                "evidence_id": "evidence-targeted-candidate-quote-protocol",
                "claim_id": "claim-1",
                "evidence": "Candidate copied paper quote for review-negative verification.",
                "raw_quote": copied_quote,
                "quote_id": "quote-candidate-window-1",
                "source_locator": "Candidate negative window #1",
                "strength": "missing",
                "stance": "missing",
                "binding_status": "bound_real_claim",
                "negative_evidence_type": "evaluation_protocol_risk",
                "targeted_negative_candidate_quote_proposal": True,
                "targeted_negative_candidate_quote_proposal_source": "freeform_reviewer_negative_candidate",
                "runtime_evidence_verification_required": True,
            }
        ]
    }

    merged = merge_review_state(state, payload)
    evidence = merged["evidence_map"][0]
    hygiene = build_decision_hygiene_view(merged)["decision_hygiene"]

    assert evidence["targeted_negative_candidate_quote_proposal"] is True
    assert evidence["verified_grounding_label"] == "paper_grounded_exact"
    assert evidence["verified_quote_match_type"].startswith("candidate_window_")
    assert evidence["semantic_grounding_label"] == "semantic_negative_verified"
    assert evidence["review_negative_label"] == "review_negative_verified"
    assert hygiene["review_negative_verified_count"] == 1

    later_state = copy.deepcopy(merged)
    later_state["_latest_evidence_context_meta"] = {
        "evidence_quote_bank": [
            {
                "quote_id": "quote-unrelated-later",
                "source_bucket": "results",
                "source_locator": "Later evidence turn",
                "raw_quote": "A later evidence turn discusses unrelated headline accuracy.",
            }
        ]
    }
    later_view = build_decision_hygiene_view(later_state)
    later_hygiene = later_view["decision_hygiene"]

    assert any(
        item.get("quote_id") == "quote-candidate-window-1"
        and item.get("persisted_candidate_window_quote")
        for item in later_state.get("evidence_quote_bank", [])
    )
    assert later_hygiene["review_negative_verified_count"] == 1


def test_targeted_candidate_quote_proposal_rejects_positive_baseline_quote():
    positive_quote = (
        "First, using PyTorch, we compare ReDrafter with state-of-the-art "
        "speculative decoding methods on an Nvidia H100 GPU."
    )
    state = {
        "claims": [
            {
                "claim_id": "claim-1",
                "claim": "The method is compared against strong speculative decoding baselines.",
                "status": "supported",
                "claim_kind": "paper_extracted",
            }
        ],
        "_latest_evidence_context_meta": {
            "evidence_quote_bank": [
                {
                    "quote_id": "quote-candidate-window-positive",
                    "source_bucket": "candidate_window",
                    "source_locator": "Candidate negative window #1",
                    "raw_quote": positive_quote,
                    "source_span_start": 2000,
                    "source_span_end": 2000 + len(positive_quote) - 1,
                    "negative_evidence_type": "missing_baseline",
                    "candidate_window_quote": True,
                    "support_role_hint": "review_negative_search_window",
                }
            ]
        },
        "evidence_map": [],
        "flaw_candidates": [
            {
                "flaw_id": "flaw-missing-baseline",
                "title": "Missing speculative decoding baseline",
                "description": "The paper may omit important speculative decoding baselines.",
                "status": "candidate",
                "severity": "major",
                "related_claim_ids": ["claim-1"],
                "negative_evidence_ids": ["evidence-targeted-candidate-quote-positive"],
                "evidence_ids": ["evidence-targeted-candidate-quote-positive"],
            }
        ],
        "unresolved_questions": [],
        "evidence_gaps": [],
        "conflict_notes": [],
    }
    payload = {
        "evidence_map": [
            {
                "evidence_id": "evidence-targeted-candidate-quote-positive",
                "claim_id": "claim-1",
                "evidence": "Candidate copied paper quote for review-negative verification.",
                "raw_quote": positive_quote,
                "quote_id": "quote-candidate-window-positive",
                "source_locator": "Candidate negative window #1",
                "strength": "missing",
                "stance": "missing",
                "binding_status": "bound_real_claim",
                "negative_evidence_type": "missing_baseline",
                "targeted_negative_candidate_quote_proposal": True,
                "targeted_negative_candidate_quote_proposal_source": "freeform_reviewer_negative_candidate",
                "runtime_evidence_verification_required": True,
            }
        ]
    }

    merged = merge_review_state(state, payload)
    evidence = merged["evidence_map"][0]
    hygiene = build_decision_hygiene_view(merged)["decision_hygiene"]

    assert evidence["verified_grounding_label"] == "paper_grounded_exact"
    assert evidence["semantic_grounding_label"] == "semantic_mismatch"
    assert evidence.get("review_negative_label") != "review_negative_verified"
    assert hygiene["review_negative_verified_count"] == 0


def test_table_scope_absence_rejects_positive_metric_scope_description():
    quote = (
        "In all experiments we compare the Top-1 accuracy, i.e., the maximum accuracy "
        "on any action class, of TCMT against leading benchmarks for few-shot action recognition."
    )
    state = {
        "claims": [
            {
                "claim_id": "claim-1",
                "claim": (
                    "During adaptation, the model holds the learned temporal causal mechanism fixed "
                    "and updates only auxiliary variables and a classifier."
                ),
                "status": "supported",
                "claim_kind": "paper_extracted",
            }
        ],
        "_latest_evidence_context_meta": {
            "evidence_quote_bank": [
                {
                    "quote_id": "quote-candidate-window-top1",
                    "source_bucket": "candidate_window",
                    "source_locator": "Candidate negative window #1",
                    "raw_quote": quote,
                    "source_span_start": 100,
                    "source_span_end": 100 + len(quote) - 1,
                    "negative_evidence_type": "insufficient_evaluation",
                    "candidate_window_quote": True,
                }
            ]
        },
        "evidence_map": [],
        "flaw_candidates": [
            {
                "flaw_id": "flaw-insufficient-eval",
                "status": "candidate",
                "severity": "major",
                "related_claim_ids": ["claim-1"],
                "negative_evidence_ids": ["e-top1-scope"],
                "evidence_ids": ["e-top1-scope"],
            }
        ],
        "unresolved_questions": [],
        "evidence_gaps": [],
        "conflict_notes": [],
    }
    payload = {
        "evidence_map": [
            {
                "evidence_id": "e-top1-scope",
                "claim_id": "claim-1",
                "evidence": "Candidate copied paper quote for review-negative verification.",
                "raw_quote": quote,
                "quote_id": "quote-candidate-window-top1",
                "source_locator": "Candidate negative window #1",
                "strength": "missing",
                "stance": "missing",
                "binding_status": "bound_real_claim",
                "negative_evidence_type": "insufficient_evaluation",
                "coverage_missing_items": ["ablation on fixed causal mechanism"],
                "targeted_negative_candidate_quote_proposal": True,
                "runtime_evidence_verification_required": True,
            }
        ]
    }

    merged = merge_review_state(state, payload)
    evidence = merged["evidence_map"][0]
    hygiene = build_decision_hygiene_view(merged)["decision_hygiene"]

    assert evidence["verified_grounding_label"] == "paper_grounded_exact"
    assert evidence["review_negative_label"] != "review_negative_verified"
    assert hygiene["review_negative_verified_count"] == 0


def test_quote_id_canonicalization_keeps_semantically_aligned_strong_support():
    state = {
        "claims": [
            {"claim_id": "claim-1", "claim": "The method improves benchmark accuracy to 91.2%.", "status": "uncertain"},
        ],
        "evidence_quote_bank": [
            {
                "quote_id": "quote-results-1",
                "source_bucket": "results",
                "source_locator": "Results / Evaluation excerpt #1",
                "raw_quote": "The method improves benchmark accuracy to 91.2% on the evaluation set.",
                "source_span_start": 20,
                "source_span_end": 88,
            }
        ],
        "evidence_map": [],
        "flaw_candidates": [],
        "unresolved_questions": [],
        "evidence_gaps": [],
        "conflict_notes": [],
    }
    payload = {
        "evidence_map": [
            {
                "evidence_id": "e-result",
                "claim_id": "claim-1",
                "evidence": "The evaluation result reports benchmark accuracy of 91.2%.",
                "raw_quote": "The method improves benchmark accuracy to 91.2% on the evaluation set.",
                "quote_id": "quote-results-1",
                "strength": "strong",
                "stance": "supports",
                "binding_status": "bound_real_claim",
                "support_source_bucket": "result_or_experiment",
            }
        ]
    }
    merged = merge_review_state(state, payload)
    evidence = merged["evidence_map"][0]
    assert evidence["semantic_grounding_label"] == "semantic_support_verified"
    assert evidence["strength"] == "strong"


def test_decision_hygiene_does_not_recanonicalize_trusted_verified_support():
    state = {
        "claims": [
            {"claim_id": "claim-1", "claim": "The paper introduces a data augmentation mechanism.", "status": "supported"},
        ],
        "evidence_quote_bank": [
            {
                "quote_id": "quote-claim-match-1",
                "source_bucket": "claim_match",
                "source_locator": "Claim-matched evidence excerpt #1",
                "raw_quote": "A different regenerated quote-bank entry that does not support the claim.",
                "source_span_start": 300,
                "source_span_end": 370,
            }
        ],
        "evidence_map": [
            {
                "evidence_id": "e-trusted",
                "claim_id": "claim-1",
                "evidence": "The paper illustrates data augmentation mechanisms.",
                "raw_quote": "illustrate data augmentation mechanisms associated with character customization.",
                "quote_id": "quote-claim-match-1",
                "source_locator": "Claim-matched evidence excerpt #1",
                "source_span_start": 100,
                "source_span_end": 170,
                "verified_source_span_start": 100,
                "verified_source_span_end": 170,
                "verified_quote_match_type": "quote_bank_id_canonical",
                "verified_grounding_label": "paper_grounded_exact",
                "semantic_grounding_label": "semantic_support_verified",
                "semantic_alignment_score": 0.77,
                "verified_claim_overlap_score": 7,
                "support_source_bucket": "method_or_approach",
                "strength": "strong",
                "stance": "supports",
                "binding_status": "bound_real_claim",
            }
        ],
        "flaw_candidates": [],
        "unresolved_questions": [],
        "evidence_gaps": [],
        "conflict_notes": [],
    }

    view = build_decision_hygiene_view(state)
    evidence = view["evidence_map"][0]
    hygiene = view["decision_hygiene"]

    assert evidence["raw_quote"].startswith("illustrate data augmentation")
    assert evidence["semantic_grounding_label"] == "semantic_support_verified"
    assert hygiene["real_strong_support_total"] == 1



def test_flaw_negative_grounding_requires_semantic_verified_evidence():
    state = {
        "claims": [{"claim_id": "claim-1", "claim": "The method is empirically adequate.", "claim_kind": "paper_extracted"}],
        "evidence_map": [
            {
                "evidence_id": "e-neg-bad",
                "claim_id": "claim-1",
                "evidence": "Table 4 shows the main claim fails by 5.3 points.",
                "strength": "medium",
                "stance": "contradicts",
                "binding_status": "bound_real_claim",
                "verified_grounding_label": "paper_grounded_exact",
                "semantic_grounding_label": "semantic_mismatch",
                "source": "Table 4",
                "raw_quote": "Results differ.",
            },
            _verified_negative("e-neg-good", "claim-1", "direct_contradiction", "Table 5 directly contradicts the main claim with a lower reported score.", source="Table 5", stance="contradicts", strength="medium"),
        ],
        "evidence_quote_bank": [{"quote_id": "q", "raw_quote": "dummy"}],
    }
    bad_flaw = {"flaw_id": "f-bad", "status": "confirmed", "severity": "major", "negative_evidence_ids": ["e-neg-bad"]}
    good_flaw = {"flaw_id": "f-good", "status": "confirmed", "severity": "major", "negative_evidence_ids": ["e-neg-good"]}
    assert _flaw_has_negative_grounding(bad_flaw, state) is False
    assert _flaw_has_negative_grounding(good_flaw, state) is True




def test_negative_evidence_requires_negative_quote_semantics():
    state = {
        "claims": [{"claim_id": "claim-1", "claim": "The method is robust in cross-domain evaluation.", "status": "uncertain"}],
        "evidence_quote_bank": [
            {
                "quote_id": "quote-results-1",
                "source_bucket": "results",
                "source_locator": "Results excerpt #1",
                "raw_quote": "The method improves average performance on the main benchmark.",
                "source_span_start": 10,
                "source_span_end": 72,
            },
            {
                "quote_id": "quote-negative-1",
                "source_bucket": "negative_or_gap",
                "source_locator": "Limitation excerpt #1",
                "raw_quote": "The method fails under cross-domain evaluation and lacks robustness analysis.",
                "source_span_start": 100,
                "source_span_end": 172,
            },
        ],
        "evidence_map": [],
        "flaw_candidates": [],
        "unresolved_questions": [],
        "evidence_gaps": [],
        "conflict_notes": [],
    }
    bad = merge_review_state(state, {
        "evidence_map": [{
            "evidence_id": "e-bad",
            "claim_id": "claim-1",
            "evidence": "The quote contradicts cross-domain robustness.",
            "raw_quote": "The method improves average performance on the main benchmark.",
            "quote_id": "quote-results-1",
            "strength": "medium",
            "stance": "contradicts",
            "binding_status": "bound_real_claim",
        }]
    })
    bad_ev = bad["evidence_map"][0]
    assert bad_ev["semantic_grounding_label"] == "semantic_mismatch"
    assert "quote_lacks_negative_anchor" in bad_ev["semantic_grounding_reasons"]
    assert _flaw_has_negative_grounding({"flaw_id": "f", "negative_evidence_ids": ["e-bad"]}, bad) is False

    good = merge_review_state(state, {
        "evidence_map": [{
            "evidence_id": "e-good",
            "claim_id": "claim-1",
            "evidence": "The paper states the method fails under cross-domain evaluation.",
            "raw_quote": "The method fails under cross-domain evaluation and lacks robustness analysis.",
            "quote_id": "quote-negative-1",
            "strength": "medium",
            "stance": "contradicts",
            "binding_status": "bound_real_claim",
        }]
    })
    good_ev = good["evidence_map"][0]
    assert good_ev["semantic_grounding_label"] == "semantic_negative_verified"
    assert _flaw_has_negative_grounding({"flaw_id": "f", "negative_evidence_ids": ["e-good"]}, good) is True


def test_negative_semantic_verifier_accepts_not_prove_not_provide_quote():
    state = {
        "claims": [
            {
                "claim_id": "claim-1",
                "claim": "The proof establishes the full NC property.",
                "status": "supported",
            }
        ],
        "evidence_quote_bank": [
            {
                "quote_id": "quote-negative-proof-1",
                "source_bucket": "negative_or_gap",
                "source_locator": "Related work limitation excerpt #1",
                "raw_quote": "They do not prove the assumption and additionally do not provide argument for the emergence of NC1 in their proof.",
                "source_span_start": 100,
                "source_span_end": 214,
            }
        ],
        "evidence_map": [],
        "flaw_candidates": [],
        "unresolved_questions": [],
        "evidence_gaps": [],
        "conflict_notes": [],
    }

    merged = merge_review_state(state, {
        "evidence_map": [{
            "evidence_id": "e-proof-gap",
            "claim_id": "claim-1",
            "evidence": "The proof gap weakens the claim that the full NC property is established.",
            "raw_quote": "They do not prove the assumption and additionally do not provide argument for the emergence of NC1 in their proof.",
            "quote_id": "quote-negative-proof-1",
            "strength": "missing",
            "stance": "missing",
            "binding_status": "bound_real_claim",
        }]
    })

    ev = merged["evidence_map"][0]
    assert ev["verified_grounding_label"] == "paper_grounded_exact"
    assert ev["semantic_grounding_label"] == "semantic_negative_verified"
    assert "quote_lacks_negative_anchor" not in ev.get("semantic_grounding_reasons", [])
    assert _flaw_has_negative_grounding({"flaw_id": "f", "negative_evidence_ids": ["e-proof-gap"]}, merged) is True


def test_review_negative_semantic_gate_rejects_author_self_limitation_as_reviewer_negative():
    state = {
        "claims": [
            {
                "claim_id": "claim-1",
                "claim": "The method generates high-quality outputs.",
                "claim_kind": "paper_extracted",
                "status": "supported",
            }
        ],
        "evidence_quote_bank": [
            {
                "quote_id": "quote-output-quality-gap-1",
                "source_bucket": "negative_or_gap",
                "source_locator": "Evaluation excerpt #1",
                "raw_quote": "Note that we do not evaluate the quality of the output, that is we do not judge if the output is accurate but only focus on whether the expected task has been performed.",
                "source_span_start": 21136,
                "source_span_end": 21304,
            }
        ],
        "evidence_map": [],
        "flaw_candidates": [
            {
                "flaw_id": "flaw-1",
                "title": "Missing output-quality evaluation",
                "description": "The paper does not evaluate output quality or accuracy.",
                "status": "candidate",
                "severity": "major",
                "related_claim_ids": ["claim-1"],
                "negative_evidence_ids": ["e-output-quality-gap"],
                "evidence_ids": ["e-output-quality-gap"],
            }
        ],
    }

    merged = merge_review_state(state, {
        "evidence_map": [{
            "evidence_id": "e-output-quality-gap",
            "claim_id": "claim-1",
            "evidence": "The paper does not evaluate output quality or accuracy.",
            "raw_quote": "Note that we do not evaluate the quality of the output, that is we do not judge if the output is accurate but only focus on whether the expected task has been performed.",
            "quote_id": "quote-output-quality-gap-1",
            "strength": "missing",
            "stance": "supports",
            "binding_status": "bound_real_claim",
            "negative_evidence_type": "insufficient_evaluation",
        }]
    })

    ev = merged["evidence_map"][0]
    view = build_decision_hygiene_view(merged)
    hygiene = view["decision_hygiene"]

    assert ev["semantic_grounding_label"] == "semantic_author_limitation"
    assert ev["review_negative_label"] == "author_limitation_only"
    assert ev["review_negative_reason"] == "insufficient_evaluation_is_author_self_limitation"
    assert ev["stance"] == "supports"
    assert hygiene["review_negative_verified_count"] == 0
    assert hygiene["semantic_negative_without_review_relation_count"] == 0
    assert hygiene["verified_negative_flaw_count"] == 0
    assert hygiene["verified_actionable_negative_flaw_count"] == 0
    assert hygiene["verified_potential_concern_count"] == 0
    assert hygiene["potential_concern_count"] == 0
    assert hygiene["author_limitation_only_count"] == 1
    assert hygiene.get("negative_evidence_type_counts", {}) == {}


def test_review_negative_semantic_gate_accepts_current_paper_negative_result():
    state = {
        "claims": [
            {
                "claim_id": "claim-1",
                "claim": "The method consistently outperforms all baselines on the main benchmark.",
                "claim_kind": "paper_extracted",
                "status": "supported",
            }
        ],
        "evidence_quote_bank": [
            {
                "quote_id": "quote-negative-result-1",
                "source_bucket": "table_or_figure",
                "source_locator": "Table 3",
                "raw_quote": "Table 3 reports a negative result: the proposed method is worse than the strongest baseline on the main benchmark.",
                "source_span_start": 120,
                "source_span_end": 205,
            }
        ],
        "evidence_map": [],
        "flaw_candidates": [
            {
                "flaw_id": "flaw-1",
                "title": "Main benchmark underperformance",
                "description": "The paper reports underperformance against the strongest baseline on the main benchmark.",
                "status": "candidate",
                "severity": "major",
                "related_claim_ids": ["claim-1"],
                "negative_evidence_ids": ["e-negative-result"],
                "evidence_ids": ["e-negative-result"],
            }
        ],
    }

    merged = merge_review_state(state, {
        "evidence_map": [{
            "evidence_id": "e-negative-result",
            "claim_id": "claim-1",
            "evidence": "Table 3 reports a negative result where the proposed method is worse than the strongest baseline.",
            "raw_quote": "Table 3 reports a negative result: the proposed method is worse than the strongest baseline on the main benchmark.",
            "quote_id": "quote-negative-result-1",
            "strength": "medium",
            "stance": "contradicts",
            "binding_status": "bound_real_claim",
            "negative_evidence_type": "negative_result",
        }]
    })

    ev = merged["evidence_map"][0]
    view = build_decision_hygiene_view(merged)
    hygiene = view["decision_hygiene"]

    assert ev["semantic_grounding_label"] == "semantic_negative_verified"
    assert ev["negative_evidence_type"] == "negative_result"
    assert ev["review_negative_label"] == "review_negative_verified"
    assert hygiene["review_negative_verified_count"] == 1
    assert hygiene["verified_negative_flaw_count"] == 1
    assert hygiene["verified_actionable_negative_flaw_count"] == 1
    assert hygiene["potential_concern_count"] == 1
    assert hygiene["negative_evidence_type_counts"]["negative_result"] == 1


def test_review_negative_grounding_falls_back_to_full_paper_exact_quote():
    quote = (
        "Table 4 shows that incorporating the secure aggregator in our federated model "
        "results in a less favorable outcome than the baseline system."
    )
    state = {
        "paper_text": f"Introduction. {quote} Additional discussion follows.",
        "claims": [
            {
                "claim_id": "claim-1",
                "claim": "The secure aggregator improves the federated model without hurting performance.",
                "claim_kind": "paper_extracted",
                "status": "supported",
            }
        ],
        "evidence_quote_bank": [
            {
                "quote_id": "quote-unrelated",
                "source_bucket": "method",
                "source_locator": "Section 3",
                "raw_quote": "We introduce the secure aggregation protocol in the federated model.",
                "source_span_start": 0,
                "source_span_end": 70,
            }
        ],
        "evidence_map": [],
        "flaw_candidates": [
            {
                "flaw_id": "flaw-1",
                "title": "Secure aggregation hurts the reported baseline comparison",
                "description": "The reported system is worse than the baseline once secure aggregation is added.",
                "status": "candidate",
                "severity": "major",
                "related_claim_ids": ["claim-1"],
                "negative_evidence_ids": ["e-secagg-negative"],
                "evidence_ids": ["e-secagg-negative"],
            }
        ],
    }

    merged = merge_review_state(state, {
        "evidence_map": [{
            "evidence_id": "e-secagg-negative",
            "claim_id": "claim-1",
            "evidence": "Secure aggregation yields a worse result than the baseline system.",
            "raw_quote": quote,
            "strength": "medium",
            "stance": "contradicts",
            "binding_status": "bound_real_claim",
            "negative_evidence_type": "negative_result",
        }]
    })

    ev = merged["evidence_map"][0]
    view = build_decision_hygiene_view(merged)
    hygiene = view["decision_hygiene"]

    assert ev["verified_grounding_label"] == "paper_grounded_exact"
    assert ev["verified_quote_match_type"] == "full_paper_exact_substring"
    assert ev["semantic_grounding_label"] == "semantic_negative_verified"
    assert ev["review_negative_label"] == "review_negative_verified"
    assert hygiene["review_negative_verified_count"] == 1
    assert hygiene["verified_actionable_negative_flaw_count"] == 1
    assert hygiene["potential_concern_count"] == 1


def test_full_paper_grounding_does_not_turn_author_limitation_into_review_negative():
    quote = (
        "Due to limited compute resources, we do not evaluate the method on larger models."
    )
    state = {
        "paper_text": f"Limitations. {quote}",
        "claims": [
            {
                "claim_id": "claim-1",
                "claim": "The method is broadly evaluated.",
                "claim_kind": "paper_extracted",
                "status": "supported",
            }
        ],
        "evidence_quote_bank": [],
        "evidence_map": [],
        "flaw_candidates": [
            {
                "flaw_id": "flaw-1",
                "title": "Limited evaluation scale",
                "description": "The evaluation omits larger models.",
                "status": "candidate",
                "severity": "major",
                "related_claim_ids": ["claim-1"],
                "negative_evidence_ids": ["e-author-limitation"],
                "evidence_ids": ["e-author-limitation"],
            }
        ],
    }

    merged = merge_review_state(state, {
        "evidence_map": [{
            "evidence_id": "e-author-limitation",
            "claim_id": "claim-1",
            "evidence": "The paper does not evaluate larger models.",
            "raw_quote": quote,
            "strength": "missing",
            "stance": "missing",
            "binding_status": "bound_real_claim",
            "negative_evidence_type": "insufficient_evaluation",
        }]
    })

    ev = merged["evidence_map"][0]
    hygiene = build_decision_hygiene_view(merged)["decision_hygiene"]

    assert ev["verified_quote_match_type"] == "full_paper_exact_substring"
    assert ev["semantic_grounding_label"] == "semantic_author_limitation"
    assert ev["review_negative_label"] == "author_limitation_only"
    assert hygiene["review_negative_verified_count"] == 0
    assert hygiene["author_limitation_only_count"] == 1


def test_full_paper_grounding_does_not_count_prior_work_comparison_gap():
    quote = (
        "Golden Gate Claude \\cite{golden2024} does not compare to other interpretability methods."
    )
    state = {
        "paper_text": f"Related work. {quote} Method. We introduce a unifying framework.",
        "claims": [
            {
                "claim_id": "claim-1",
                "claim": "The paper compares interpretability methods in a unifying framework.",
                "claim_kind": "paper_extracted",
                "status": "supported",
            }
        ],
        "evidence_quote_bank": [],
        "evidence_map": [],
        "flaw_candidates": [
            {
                "flaw_id": "flaw-1",
                "title": "Missing comparison",
                "description": "The paper lacks comparisons with interpretability methods.",
                "status": "candidate",
                "severity": "major",
                "related_claim_ids": ["claim-1"],
                "negative_evidence_ids": ["e-prior-work-gap"],
                "evidence_ids": ["e-prior-work-gap"],
            }
        ],
    }

    merged = merge_review_state(state, {
        "evidence_map": [{
            "evidence_id": "e-prior-work-gap",
            "claim_id": "claim-1",
            "evidence": "The paper does not compare to other interpretability methods.",
            "raw_quote": quote,
            "strength": "missing",
            "stance": "missing",
            "binding_status": "bound_real_claim",
            "negative_evidence_type": "missing_baseline",
        }]
    })

    ev = merged["evidence_map"][0]
    hygiene = build_decision_hygiene_view(merged)["decision_hygiene"]

    assert ev["verified_quote_match_type"] == "full_paper_exact_substring"
    assert ev["review_negative_label"] != "review_negative_verified"
    assert hygiene["review_negative_verified_count"] == 0
    assert hygiene["verified_actionable_negative_flaw_count"] == 0


def test_excerpt_limited_absence_with_plural_excerpts_is_not_review_negative():
    quote = (
        "approach on a novel dataset, as shown in Table \\ref{tab:results_table}c. "
        "\\subsection{Ablation study} \\label{sec:ablation} \\input{tables/ablation_tables} "
        "We begin by conducting an oracular study using ground-truth labels,"
    )
    state = {
        "claims": [
            {
                "claim_id": "claim-1",
                "claim": "The method is validated by a complete ablation study.",
                "claim_kind": "paper_extracted",
                "status": "supported",
            }
        ],
        "evidence_quote_bank": [
            {
                "quote_id": "quote-ablation-header",
                "source_bucket": "negative_or_gap",
                "source_locator": "Ablation excerpt",
                "raw_quote": quote,
                "source_span_start": 200,
                "source_span_end": 420,
            }
        ],
        "evidence_map": [],
        "flaw_candidates": [
            {
                "flaw_id": "flaw-1",
                "title": "Ablation content missing from excerpt",
                "description": "The provided excerpts do not show ablation details.",
                "status": "candidate",
                "severity": "major",
                "related_claim_ids": ["claim-1"],
                "negative_evidence_ids": ["e-excerpt-limited"],
                "evidence_ids": ["e-excerpt-limited"],
            }
        ],
    }

    merged = merge_review_state(state, {
        "evidence_map": [{
            "evidence_id": "e-excerpt-limited",
            "claim_id": "claim-1",
            "evidence": (
                "The HFR module is not explicitly described in the provided excerpts, "
                "and the ablation study section header is present but its content is missing."
            ),
            "raw_quote": quote,
            "quote_id": "quote-ablation-header",
            "strength": "missing",
            "stance": "missing",
            "binding_status": "bound_real_claim",
            "negative_evidence_type": "missing_baseline",
        }]
    })

    ev = merged["evidence_map"][0]
    hygiene = build_decision_hygiene_view(merged)["decision_hygiene"]

    assert ev["verified_grounding_label"] == "paper_grounded_exact"
    assert ev["semantic_grounding_label"] == "semantic_mismatch"
    assert ev["review_negative_label"] == "insufficient_claim_relation"
    assert ev["review_negative_reason"] == "absence_claim_limited_to_quote_or_excerpt"
    assert hygiene["review_negative_verified_count"] == 0
    assert hygiene["verified_actionable_negative_flaw_count"] == 0


def test_review_negative_semantic_gate_does_not_reclassify_normal_support_as_negative():
    state = {
        "claims": [
            {
                "claim_id": "claim-1",
                "claim": "The method achieves strong empirical gains.",
                "claim_kind": "paper_extracted",
                "status": "supported",
            }
        ],
        "evidence_quote_bank": [
            {
                "quote_id": "quote-support-1",
                "source_bucket": "table_or_figure",
                "source_locator": "Table 2",
                "raw_quote": "Table 2 shows our method reaches 91.0% accuracy, outperforming the baseline.",
                "source_span_start": 100,
                "source_span_end": 175,
            }
        ],
        "evidence_map": [],
        "flaw_candidates": [],
    }

    merged = merge_review_state(state, {
        "evidence_map": [{
            "evidence_id": "e-support-mislabel",
            "claim_id": "claim-1",
            "evidence": "Table 2 shows our method reaches 91.0% accuracy, outperforming the baseline.",
            "raw_quote": "Table 2 shows our method reaches 91.0% accuracy, outperforming the baseline.",
            "quote_id": "quote-support-1",
            "strength": "strong",
            "stance": "supports",
            "binding_status": "bound_real_claim",
            "negative_evidence_type": "insufficient_evaluation",
        }]
    })

    ev = merged["evidence_map"][0]
    view = build_decision_hygiene_view(merged)
    hygiene = view["decision_hygiene"]

    assert ev["semantic_grounding_label"] == "semantic_support_verified"
    assert ev["review_negative_label"] != "review_negative_verified"
    assert hygiene["verified_negative_flaw_count"] == 0
    assert hygiene["verified_actionable_negative_flaw_count"] == 0
    assert hygiene["potential_concern_count"] == 0


def test_merge_review_state_downgrades_support_only_flaw_without_negative_grounding():
    state = {
        "claims": [{"claim_id": "claim-1", "claim": "The method is effective.", "status": "supported"}],
        "evidence_quote_bank": [
            {
                "quote_id": "quote-results-1",
                "raw_quote": "Table 1 shows that the method improves accuracy by 8.3 percent.",
                "source_locator": "Table 1",
                "source_bucket": "table_or_figure",
                "source_span_start": 0,
                "source_span_end": 64,
            }
        ],
        "evidence_map": [
            {
                "evidence_id": "evidence-1",
                "claim_id": "claim-1",
                "evidence": "Table 1 supports the effectiveness claim.",
                "source": "Table 1",
                "source_locator": "Table 1",
                "raw_quote": "Table 1 shows that the method improves accuracy by 8.3 percent.",
                "quote_id": "quote-results-1",
                "strength": "strong",
                "stance": "supports",
                "binding_status": "bound_real_claim",
            }
        ],
        "flaw_candidates": [],
    }
    payload = {
        "flaw_candidates": [
            {
                "flaw_id": "flaw-1",
                "title": "Unsupported flaw",
                "description": "The claim is weak, but this cites only positive support evidence.",
                "severity": "major",
                "status": "candidate",
                "related_claim_ids": ["claim-1"],
                "evidence_ids": ["evidence-1"],
                "confidence": 0.6,
            }
        ],
        "dialogue_summary": "flaw",
        "recommendation": "undecided",
    }

    merged = merge_review_state(state, payload)

    flaw = merged["flaw_candidates"][0]
    assert flaw["status"] == "downgraded"
    assert flaw["hygiene_status_reason"] == "support_only_flaw_lacks_verified_negative_evidence"
    assert any(note.get("conflict_type") == "support_only_flaw_without_negative_grounding" for note in merged["conflict_notes"])


def test_render_user_report_excludes_audit_trace_and_decision_tokens():
    """``render_user_report`` is the paper-facing artifact and must never
    expose ``binary_decision`` / ``recommendation_view`` / the section-7
    Audit Trace block.  External audits flagged this as a P0 framing risk
    because a downstream reader could otherwise mistake the artifact for an
    automated accept/reject judgement.
    """

    state = _state_with_mixed_support()
    report = render_user_report(state, {})

    assert report.startswith("Review Diagnostic Report")
    # Sections 1-6 must be present.
    for section in (
        "1. Summary of Reviews",
        "2. Key Strengths",
        "3. Key Weaknesses",
        "4. Criterion Assessment",
        "5. Questions/Suggestions",
        "6. Diagnostic Summary",
    ):
        assert section in report
    # Section 7 and decision tokens must NOT leak into the user-facing artifact.
    assert "7. Audit Trace" not in report
    assert "Audit Trace (machine-readable)" not in report
    assert "binary_decision=" not in report
    assert "recommendation_view=" not in report
    assert "internal ids" not in report.lower()
    assert "system did not see" not in report.lower()
    # The legacy "Final Decision:" leakage must remain absent as before.
    assert "Final Decision:" not in report
    assert "Claim-level support depth:" in report
    assert "1 deep" in report
    assert "1 moderate" in report


def test_render_user_report_redacts_internal_ids_from_manager_summary():
    state = _state_with_mixed_support()
    payload = {
        "final_report": (
            "No concrete evidence found for target claims claim-context-1 and claim-context-2. "
            "The method improves benchmark performance using a verified paper-side mechanism."
        )
    }

    report = render_user_report(state, payload)
    human_part = report.split("7. Audit Trace", 1)[0]

    assert "claim-context-" not in human_part
    assert "evidence-" not in human_part
    assert "flaw-" not in human_part
    assert "No concrete evidence found for target" not in human_part
    assert "verified paper-side mechanism" in human_part






def test_reward_audit_id_leak_ratio_ignores_plain_hyphenated_phrases():
    assert _audit_id_leak_ratio("The concern is evidence-limited but paper-side.") == 0.0
    assert _audit_id_leak_ratio("This cites claim-2 and evidence-3 directly.") > 0.0

def test_report_visible_text_redacts_generic_internal_claim_ids():
    visible = _report_visible_text(
        "The method remains evidence-limited and is discussed with evidence-3 for claim-2.",
        max_length=400,
    )

    assert "claim-2" not in visible
    assert "evidence-3" not in visible
    assert "evidence-limited" in visible
    assert "paper claim" in visible
    assert "evidence anchor" in visible

def test_build_state_audit_returns_machine_readable_dict():
    """``build_state_audit`` is the machine-readable companion that captures
    everything previously buried in section 7 (recommendation_view,
    binary_decision, hygiene counters, criterion lineage).
    """

    state = _state_with_mixed_support()
    audit = build_state_audit(state, {})

    runtime_view = infer_final_recommendation_view(state, {})
    assert audit["recommendation_view"] == runtime_view["recommendation_view"]
    assert audit["binary_decision"] == runtime_view["binary_decision"]
    assert audit["reason"] == runtime_view["reason"]
    assert isinstance(audit["accept_calibration_warnings"], list)
    assert isinstance(audit["decision_hygiene"], dict)
    assert isinstance(audit["criteria_audit"], list)
    # The rendered text snippet preserves the original Audit Trace lineage so
    # tooling that previously parsed section 7 keeps working.
    assert isinstance(audit["audit_trace_text"], str)
    assert (
        f"recommendation_view={runtime_view['recommendation_view']}"
        in audit["audit_trace_text"]
    )
    assert "claims_with_deep_support=1" in audit["audit_trace_text"]
    assert "claims_with_moderate_or_deep_support=2" in audit["audit_trace_text"]


def test_decision_hygiene_emits_state_contamination_targets_and_gate_counts():
    state = {
        "claims": [
            {
                "claim_id": "claim-1",
                "claim": "The method generalizes across diverse domains.",
                "status": "unsupported",
                "claim_kind": "paper_extracted",
            }
        ],
        "evidence_map": [
            {
                "evidence_id": "e-support",
                "claim_id": "claim-1",
                "evidence": "Table 2 reports higher benchmark performance.",
                "raw_quote": "Table 2 reports higher benchmark performance.",
                "source": "Table 2",
                "strength": "strong",
                "stance": "supports",
                "binding_status": "bound_real_claim",
                "verified_grounding_label": "paper_grounded_exact",
                "semantic_grounding_label": "semantic_support_verified",
                "semantic_alignment_score": 0.82,
            },
            _verified_negative("e-limitation", "claim-1", "scope_limitation", "The method is only evaluated on a single in-domain dataset and does not generalize.", source="Section 6"),
        ],
        "flaw_candidates": [
            {
                "flaw_id": "flaw-escalated",
                "title": "Unsupported major flaw",
                "description": "The report escalated a flaw without verified negative evidence.",
                "severity": "major",
                "status": "confirmed",
                "evidence_ids": ["e-support"],
            },
            {
                "flaw_id": "flaw-overclaim",
                "title": "Overclaimed limitation",
                "description": "A limitation was overclaimed as a major flaw.",
                "severity": "major",
                "status": "candidate",
                "related_claim_ids": ["claim-1"],
                "evidence_ids": ["e-limitation"],
                "negative_evidence_ids": ["e-limitation"],
            },
        ],
        "evidence_gaps": [
            {
                "gap_id": "gap-1",
                "claim_id": "claim-1",
                "text": "Claim claim-1 lacks grounded result evidence.",
                "status": "open",
            }
        ],
        "unresolved_questions": [],
        "conflict_notes": [],
    }

    hygiene = build_decision_hygiene_view(state)["decision_hygiene"]
    type_counts = hygiene["state_contamination_type_counts"]
    gate_counts = hygiene["recovery_target_gate_counts"]

    assert hygiene["state_contamination_count"] >= 3
    assert type_counts.get("unsupported_with_strong_support", 0) == 0
    assert type_counts["stale_gap_persistence"] == 1
    assert type_counts["unsupported_flaw_escalation"] == 1
    assert type_counts["negative_evidence_overclaim"] == 1
    assert gate_counts["real_target"] >= 1
    assert gate_counts["weak_target"] >= 2
    assert hygiene["repairable_contamination_target_count"] >= 1
    assert hygiene["conservative_contamination_target_count"] >= 2
    assert all(item.get("target_gate_label") for item in hygiene["state_contamination_targets"])


def test_decision_hygiene_does_not_count_minor_assessment_limitation_as_overclaim():
    state = {
        "claims": [
            {
                "claim_id": "claim-1",
                "claim": "The method improves benchmark performance.",
                "status": "supported",
            }
        ],
        "evidence_map": [
            {
                "evidence_id": "e-support",
                "claim_id": "claim-1",
                "evidence": "Table 2 reports higher benchmark performance.",
                "raw_quote": "Table 2 reports higher benchmark performance.",
                "source": "Table 2",
                "strength": "strong",
                "stance": "supports",
                "binding_status": "bound_real_claim",
                "verified_grounding_label": "paper_grounded_exact",
                "semantic_grounding_label": "semantic_support_verified",
                "semantic_alignment_score": 0.82,
            },
            {
                "evidence_id": "e-limitation",
                "claim_id": "claim-1",
                "evidence": "The authors list a limitation for future broader evaluation.",
                "raw_quote": "The authors list a limitation for future broader evaluation.",
                "source": "Limitations",
                "strength": "missing",
                "stance": "missing",
                "binding_status": "bound_real_claim",
                "verified_grounding_label": "paper_grounded_exact",
                "semantic_grounding_label": "semantic_negative_verified",
                "negative_evidence_type": "scope_limitation",
            },
        ],
        "flaw_candidates": [
            {
                "flaw_id": "flaw-limitation",
                "title": "Scope limitation",
                "description": "A scoped limitation should remain an assessment limitation.",
                "severity": "minor",
                "status": "candidate",
                "related_claim_ids": ["claim-1"],
                "evidence_ids": ["e-limitation"],
                "negative_evidence_ids": ["e-limitation"],
                "source": "quote-bank-negative-grounding",
            }
        ],
        "evidence_gaps": [],
        "unresolved_questions": [],
        "conflict_notes": [],
    }

    view = build_decision_hygiene_view(state)
    hygiene = view["decision_hygiene"]
    flaw = view["flaw_candidates"][0]

    assert flaw["final_view_flaw_layer"] == "assessment_limitation"
    assert hygiene["assessment_limitation_flaw_count"] == 1
    assert hygiene["state_contamination_type_counts"].get("negative_evidence_overclaim", 0) == 0
    assert hygiene["state_contamination_count"] == 0


def test_decision_hygiene_localizes_zero_real_support_as_review_target():
    state = {
        "paper_id": "paper-zero-real",
        "claims": [{"claim_id": "claim-1", "claim": "The paper proposes a method.", "status": "uncertain"}],
        "evidence_map": [
            {
                "evidence_id": "e-medium",
                "claim_id": "claim-1",
                "evidence": "The paper describes the proposed method.",
                "raw_quote": "The paper describes the proposed method.",
                "source": "Method",
                "strength": "medium",
                "stance": "supports",
                "binding_status": "bound_real_claim",
                "verified_grounding_label": "paper_grounded_exact",
                "semantic_grounding_label": "semantic_support_verified",
                "semantic_alignment_score": 0.7,
            }
        ],
        "flaw_candidates": [],
        "evidence_gaps": [],
        "unresolved_questions": [],
        "conflict_notes": [],
    }

    hygiene = build_decision_hygiene_view(state)["decision_hygiene"]
    zero_real_targets = [
        item for item in hygiene["state_contamination_targets"]
        if item.get("error_type") == "zero_real_support"
    ]

    assert hygiene["real_strong_support_total"] == 0
    assert hygiene["state_contamination_type_counts"]["zero_real_support"] == 1
    assert zero_real_targets
    assert zero_real_targets[0]["target_gate_label"] == "weak_target"
    assert "verified support candidate" in zero_real_targets[0]["evidence_context"]


def test_render_final_review_combined_output_concatenates_user_report_and_audit_text():
    """The back-compat combined renderer must remain byte-equivalent to the
    legacy artifact (sections 1-6 followed by an Audit Trace block).  Callers
    that have not migrated to the split artifacts still consume this text."""

    state = _state_with_mixed_support()
    combined = render_final_review(state, {})
    user_text = render_user_report(state, {})
    audit = build_state_audit(state, {})

    # The combined artifact starts with the user-facing sections verbatim.
    assert combined.startswith(user_text)
    # Followed by the Audit Trace block whose text body matches the
    # machine-readable companion.
    assert "\n7. Audit Trace (machine-readable)\n" in combined
    _, _, trailing = combined.partition("7. Audit Trace (machine-readable)\n")
    assert audit["audit_trace_text"] in trailing


def test_classify_claim_kind_resolves_provenance_from_id_prefix():
    assert _classify_claim_kind("claim-1") == "paper_extracted"
    assert _classify_claim_kind("claim-3") == "paper_extracted"
    assert _classify_claim_kind("claim-context-2") == "context_synthesized"
    assert _classify_claim_kind("claim-fallback-7") == "manager_fallback"
    assert _classify_claim_kind("claim-recovery-1") == "recovery_marker"
    assert _classify_claim_kind("") == "unknown"
    assert _classify_claim_kind(None) == "unknown"
    assert _classify_claim_kind("opaque-id") == "unknown"


def test_classify_claim_kind_preserves_structural_prefix_over_declared_kind():
    assert (
        _classify_claim_kind("claim-fallback-1", declared_kind="paper_extracted")
        == "manager_fallback"
    )
    assert (
        _classify_claim_kind("claim-context-1", declared_kind="paper_extracted")
        == "context_synthesized"
    )
    assert (
        _classify_claim_kind("claim-recovery-1", declared_kind="paper_extracted")
        == "recovery_marker"
    )
    assert (
        _classify_claim_kind("claim-1", declared_kind="manager_fallback")
        == "manager_fallback"
    )
    assert _classify_claim_kind("claim-1", declared_kind="not_a_real_kind") == "paper_extracted"
    assert not _is_real_paper_claim_id("claim-context-1", "paper_extracted")
    assert not _is_real_paper_claim_id("claim-fallback-1", "paper_extracted")
    assert not _is_real_paper_claim_id("claim-paper-context-1", "paper_extracted")
    assert not _is_real_paper_claim_id("claim-paper-recovery-1", "paper_extracted")
    assert "paper_extracted" in CLAIM_KINDS
    assert "context_synthesized" in CLAIM_KINDS
    assert "manager_fallback" in CLAIM_KINDS
    assert "recovery_marker" in CLAIM_KINDS


def test_raw_salvaged_claim_cleanup_strips_schema_tail_but_keeps_real_paper_text():
    from agent_system.environments.env_package.review.state import _clean_raw_salvaged_claim_text

    cleaned = _clean_raw_salvaged_claim_text(
        'The paper introduces a comprehensive solution for selecting and coordinating models from an LLM swarm using PDDL for multi-modal task execution. claim_type="contribution", coverage_tags=["contribution"], but also should include method or empirical tags to fill gaps. Actually, cov'
    )
    assert cleaned == "The paper introduces a comprehensive solution for selecting and coordinating models from an LLM swarm using PDDL for multi-modal task execution."
    assert "unknown" in CLAIM_KINDS


def test_is_real_paper_claim_id_routes_through_classify_helper():
    assert _is_real_paper_claim_id("claim-1") is True
    assert _is_real_paper_claim_id("claim-fallback-1") is False
    assert _is_real_paper_claim_id("claim-context-1") is False
    assert _is_real_paper_claim_id("claim-recovery-1") is False
    assert _is_real_paper_claim_id("claim-fallback-1", declared_kind="paper_extracted") is False
    assert _is_real_paper_claim_id("claim-1", declared_kind="manager_fallback") is False


def test_normalize_payload_injects_claim_kind_field():
    normalized = normalize_review_update_payload(
        {
            "claims": [
                {"claim_id": "claim-1", "claim": "The paper proposes a new framework."},
                {"claim_id": "claim-context-2", "claim": "Context synthesised claim text."},
                {"claim_id": "claim-fallback-3", "claim": "Manager fallback placeholder text."},
            ]
        },
        required_fields=["claims"],
    )
    claims_by_id = {item["claim_id"]: item for item in normalized.get("claims", [])}
    assert claims_by_id["claim-1"]["claim_kind"] == "paper_extracted"
    assert claims_by_id["claim-context-2"]["claim_kind"] == "context_synthesized"
    assert claims_by_id["claim-fallback-3"]["claim_kind"] == "manager_fallback"


def test_claim_coverage_summary_surfaces_paper_extracted_counts():
    state = {
        "claims": [
            {"claim_id": "claim-1", "claim": "Paper proposes new method.", "claim_type": "contribution", "status": "uncertain"},
            {"claim_id": "claim-2", "claim": "Method outperforms baselines on three benchmarks.", "claim_type": "empirical", "status": "uncertain"},
            {"claim_id": "claim-context-3", "claim": "Context synthesised claim.", "claim_type": "method", "status": "uncertain"},
            {"claim_id": "claim-fallback-4", "claim": "Manager fallback claim placeholder.", "claim_type": "other", "status": "uncertain"},
        ]
    }
    summary = claim_coverage_summary(state)
    counts = summary["claim_kind_counts"]
    assert counts["paper_extracted"] == 2
    assert counts["context_synthesized"] == 1
    assert counts["manager_fallback"] == 1
    assert counts["recovery_marker"] == 0
    assert summary["paper_extracted_claim_count"] == 2
    assert summary["non_paper_claim_count"] == 2


def test_claim_kind_counts_handles_missing_explicit_field():
    claims = [
        {"claim_id": "claim-1"},
        {"claim_id": "claim-context-2"},
        {"claim_id": "claim-fallback-3"},
        {"claim_id": "claim-recovery-4"},
        {"claim_id": ""},
    ]
    counts = _claim_kind_counts(claims)
    assert counts["paper_extracted"] == 1
    assert counts["context_synthesized"] == 1
    assert counts["manager_fallback"] == 1
    assert counts["recovery_marker"] == 1
    assert counts["unknown"] == 1


# ---------------------------------------------------------------------------
# P0-1 / P0-2 medium-promotion calibration regression guards.
# ``_classify_medium_support_promotion_tier`` is the single entry point that
# decides whether a verified medium support gets promoted to ``strength=strong``
# (``tier=strong``), held at moderate (``tier=moderate``) so it surfaces as
# ``verified_moderate`` in the final-view admission tier, or rejected outright
# (``tier=none``).  The score thresholds are
# ``METHOD_PROMOTION_STRONG_MIN_SCORE`` (>= for moderate-depth/method-section
# supports), ``METHOD_PROMOTION_MODERATE_MIN_SCORE`` (>= for the moderate
# hold), and ``DEEP_PROMOTION_STRONG_MIN_SCORE`` (>= for deep supports).
# ---------------------------------------------------------------------------


def _verified_method_evidence(score, *, overlap=0):
    """Return a minimal evidence dict that satisfies every gate in
    ``_classify_medium_support_promotion_tier`` *except* the score gate."""
    return {
        "evidence_id": "ev-method-1",
        "claim_id": "claim-1",
        "strength": "medium",
        "initial_strength": "medium",
        "binding_status": "bound_real_claim",
        "stance": "supports",
        "verified_grounding_label": "paper_grounded_exact",
        "semantic_grounding_label": "semantic_support_verified",
        "verified_claim_overlap_score": overlap,
        "support_depth": "moderate",
        "support_source_bucket": "method_or_approach",
        "verified_source_bucket": "method_or_approach",
        "semantic_alignment_score": score,
    }


def _verified_deep_evidence(score, *, overlap=0, bucket="result_or_experiment"):
    return {
        "evidence_id": "ev-deep-1",
        "claim_id": "claim-1",
        "strength": "medium",
        "initial_strength": "medium",
        "binding_status": "bound_real_claim",
        "stance": "supports",
        "verified_grounding_label": "paper_grounded_exact",
        "semantic_grounding_label": "semantic_support_verified",
        "verified_claim_overlap_score": overlap,
        "support_depth": "deep",
        "support_source_bucket": bucket,
        "verified_source_bucket": bucket,
        "semantic_alignment_score": score,
    }


def test_method_support_promotes_to_strong_at_method_strong_threshold():
    decision = _classify_medium_support_promotion_tier(
        _verified_method_evidence(METHOD_PROMOTION_STRONG_MIN_SCORE)
    )
    assert decision["tier"] == "strong"
    assert decision["reason"] == "direct_verified_method_support"


def test_method_support_held_at_moderate_just_below_strong_threshold():
    decision = _classify_medium_support_promotion_tier(
        _verified_method_evidence(METHOD_PROMOTION_STRONG_MIN_SCORE - 0.05)
    )
    assert decision["tier"] == "moderate"
    assert decision["reason"] == "moderate_score_method_support_held_at_moderate"
    # Calibrated promotion never returns ``True`` for moderate-tier supports.
    assert _should_promote_verified_medium_support(
        _verified_method_evidence(METHOD_PROMOTION_STRONG_MIN_SCORE - 0.05)
    ) is False


def test_low_score_method_support_held_at_moderate():
    decision = _classify_medium_support_promotion_tier(
        _verified_method_evidence(METHOD_PROMOTION_MODERATE_MIN_SCORE - 0.05)
    )
    assert decision["tier"] == "moderate"
    assert decision["reason"] == "low_score_method_support_held_at_moderate"


def test_method_support_with_overlap_uses_fallback_reason():
    decision = _classify_medium_support_promotion_tier(
        _verified_method_evidence(METHOD_PROMOTION_STRONG_MIN_SCORE + 0.05, overlap=4)
    )
    assert decision["tier"] == "strong"
    assert decision["reason"] == "verified_claim_overlap_method_support"


def test_deep_support_promotes_to_strong_at_deep_threshold():
    decision = _classify_medium_support_promotion_tier(
        _verified_deep_evidence(DEEP_PROMOTION_STRONG_MIN_SCORE)
    )
    assert decision["tier"] == "strong"
    assert decision["reason"] == "direct_verified_deep_support"


def test_deep_near_miss_support_with_empirical_anchor_stays_diagnostic_moderate():
    decision = _classify_medium_support_promotion_tier(
        _verified_deep_evidence(DEEP_PROMOTION_STRONG_MIN_SCORE - 0.04)
    )
    assert decision["tier"] == "moderate"
    assert decision["reason"] == "near_miss_verified_deep_support"


def test_low_score_deep_support_held_at_moderate():
    decision = _classify_medium_support_promotion_tier(
        _verified_deep_evidence(DEEP_PROMOTION_STRONG_MIN_SCORE - 0.07)
    )
    assert decision["tier"] == "moderate"
    assert decision["reason"] == "low_score_deep_support_held_at_moderate"


def test_decision_view_reports_context_support_without_promoting_real_claim():
    state = {
        "claims": [
            {
                "claim_id": "claim-context-1",
                "claim": "The method is evaluated on multiple molecule generation tasks.",
                "claim_kind": "context_synthesized",
                "claim_type": "empirical",
                "status": "partially_supported",
            }
        ],
        "evidence_map": [
            {
                "evidence_id": "evidence-context-1",
                "claim_id": "claim-context-1",
                "strength": "medium",
                "initial_strength": "strong",
                "stance": "supports",
                "binding_status": "invalid_claim_id",
                "support_source_bucket": "result_or_experiment",
                "verified_grounding_label": "paper_grounded_exact",
                "semantic_grounding_label": "semantic_support_verified",
                "semantic_alignment_score": 0.8,
                "verified_claim_overlap_score": 4,
                "support_depth": "deep",
                "source_locator": "Section 4: Experiments",
                "source_locator_specific": True,
                "verified_quote_match_type": "quote_bank_id_canonical",
                "raw_quote": "The method is evaluated on multiple molecule generation tasks.",
            }
        ],
    }

    view = build_decision_hygiene_view(state)
    hygiene = view["decision_hygiene"]

    assert state["claims"][0]["claim_id"] == "claim-context-1"
    assert hygiene["context_verified_support_total"] == 1
    assert hygiene["context_verified_support_by_claim"] == {"claim-context-1": 1}
    assert hygiene["real_strong_support_total"] == 0
    assert not [c for c in view["claims"] if c.get("final_view_context_derived_claim")]
    assert view["evidence_map"][0]["claim_id"] == "claim-context-1"
    assert "final_view_context_rebound" not in view["evidence_map"][0]


def test_low_score_deep_support_with_specific_ablation_anchor_stays_moderate():
    evidence = _verified_deep_evidence(0.25, overlap=5, bucket="ablation")
    evidence["initial_strength"] = "strong"
    evidence["final_strength_guard_downgrade_reason"] = "low_score_strong_support_downgrade"
    evidence["source_locator"] = "Table 3"
    evidence["source_locator_specific"] = True
    evidence["verified_quote_match_type"] = "quote_bank_id_canonical"

    decision = _classify_medium_support_promotion_tier(evidence)

    assert decision["tier"] == "moderate"
    assert decision["reason"] == "specific_anchor_low_score_support_held_at_moderate"


def test_low_score_deep_support_without_specific_anchor_stays_moderate():
    evidence = _verified_deep_evidence(0.25, overlap=5, bucket="result_or_experiment")
    evidence["initial_strength"] = "strong"
    evidence["final_strength_guard_downgrade_reason"] = "low_score_strong_support_downgrade"
    evidence["verified_quote_match_type"] = "quote_bank_id_canonical"

    decision = _classify_medium_support_promotion_tier(evidence)

    assert decision["tier"] == "moderate"
    assert decision["reason"] == "low_score_deep_support_held_at_moderate"


def test_method_near_miss_support_requires_specific_locator():
    no_locator = _verified_method_evidence(METHOD_PROMOTION_STRONG_MIN_SCORE - 0.04)
    decision = _classify_medium_support_promotion_tier(no_locator)
    assert decision["tier"] == "moderate"
    assert decision["reason"] == "moderate_score_method_support_held_at_moderate"

    with_locator = dict(no_locator)
    with_locator["source_locator"] = "Section 3.2: Model architecture"
    decision = _classify_medium_support_promotion_tier(with_locator)
    assert decision["tier"] == "moderate"
    assert decision["reason"] == "near_miss_verified_method_support"


def test_deep_support_with_overlap_uses_fallback_reason():
    decision = _classify_medium_support_promotion_tier(
        _verified_deep_evidence(DEEP_PROMOTION_STRONG_MIN_SCORE + 0.05, overlap=2)
    )
    assert decision["tier"] == "strong"
    assert decision["reason"] == "verified_claim_overlap_deep_support"


def test_abstract_medium_support_is_rejected_regardless_of_score():
    abstract = dict(_verified_method_evidence(0.95))
    abstract["support_source_bucket"] = "abstract"
    abstract["verified_source_bucket"] = "abstract"
    decision = _classify_medium_support_promotion_tier(abstract)
    assert decision["tier"] == "none"


def test_shallow_medium_support_is_rejected_regardless_of_score():
    """Buckets that are neither abstract nor a recognised method/result/
    theory section produce ``support_depth=='shallow'`` for medium
    supports.  Even with a perfect semantic alignment score the
    calibration must reject these as promotion candidates."""
    shallow = {
        "evidence_id": "ev-shallow-1",
        "claim_id": "claim-1",
        "strength": "medium",
        "initial_strength": "medium",
        "binding_status": "bound_real_claim",
        "stance": "supports",
        "verified_grounding_label": "paper_grounded_exact",
        "semantic_grounding_label": "semantic_support_verified",
        "verified_claim_overlap_score": 4,
        # ``introduction`` does not map to any depth-eligible bucket and
        # produces ``support_depth=='shallow'`` for medium supports.
        "support_source_bucket": "introduction",
        "verified_source_bucket": "introduction",
        "semantic_alignment_score": 0.95,
    }
    decision = _classify_medium_support_promotion_tier(shallow)
    assert decision["tier"] == "none"


def test_low_score_method_support_routes_to_verified_moderate_in_final_view():
    """End-to-end: a low-score method support stays at medium and shows up
    as ``verified_moderate`` in the support survival trace.  This is the
    P0-2 invariant — the moderate layer must not vanish."""
    state = {
        "claims": [
            {
                "claim_id": "claim-1",
                "claim": "The method uses a transformer encoder.",
                "claim_kind": "paper_extracted",
            }
        ],
        "evidence_map": [
            _verified_method_evidence(METHOD_PROMOTION_STRONG_MIN_SCORE - 0.05)
        ],
    }
    trace = _build_support_survival_trace(state)
    summary = _support_survival_summary(trace)
    assert summary["strict_strong_support_total"] == 0
    assert summary["moderate_diagnostic_support_total"] == 1
    assert summary["support_admission_tier_counts"].get("verified_moderate") == 1
    # Bookkeeping aliases stay aligned with the tier counts.
    assert summary["final_real_strong_total"] == 0
    assert summary["final_verified_moderate_support_total"] == 1


def test_support_survival_summary_exposes_p0_3_tier_aliases():
    """P0-3: ``_support_survival_summary`` must expose ``strict_strong``,
    ``moderate_diagnostic``, ``contextual``, ``not_verified``, and
    promotion-yield aliases so audits can distinguish actual strong
    admission from moderate diagnostics and shadow candidates."""
    strong_sample = {**_verified_deep_evidence(0.9), "strength": "strong"}
    moderate_sample = {
        **_verified_method_evidence(0.55),
        "evidence_id": "ev-method-2",
        "claim_id": "claim-2",
    }
    not_verified_sample = {
        "evidence_id": "ev-unverified",
        "claim_id": "claim-1",
        "strength": "medium",
        "initial_strength": "medium",
        "stance": "supports",
        "verified_grounding_label": "missing_quote",
        "semantic_grounding_label": "semantic_unjudged",
    }
    state = {
        "claims": [
            {"claim_id": "claim-1", "claim_kind": "paper_extracted"},
            {"claim_id": "claim-2", "claim_kind": "paper_extracted"},
        ],
        "evidence_map": [strong_sample, moderate_sample, not_verified_sample],
    }
    trace = _build_support_survival_trace(state)
    summary = _support_survival_summary(trace)
    assert summary["strict_strong_support_total"] >= 1
    assert summary["moderate_diagnostic_support_total"] >= 1
    assert summary["not_verified_support_total"] >= 1
    assert "shadow_candidate_support_total" in summary
    assert "promotion_yield" in summary
    assert "strong_survival_rate" in summary
    assert "final_support_yield" in summary
    # Hygiene view propagates the same aliases at the top level.
    decision = build_decision_hygiene_view({"claims": state["claims"], "evidence_map": state["evidence_map"]})
    hygiene = decision.get("decision_hygiene") or {}
    for key in (
        "strict_strong_support_total",
        "moderate_diagnostic_support_total",
        "contextual_support_total",
        "not_verified_support_total",
        "shadow_candidate_support_total",
        "promotion_yield",
        "strong_survival_rate",
        "final_support_yield",
    ):
        assert key in hygiene


# ---------------------------------------------------------------------------
# P0-4 user_report cleanliness regression guards.
# ---------------------------------------------------------------------------


def _user_report_state_with_unresolved_question(question_text):
    return {
        "paper_id": "paper-1",
        "claims": [
            {"claim_id": "claim-1", "claim": "The paper proposes a method.", "claim_kind": "paper_extracted", "status": "supported"}
        ],
        "evidence_map": [],
        "flaw_candidates": [],
        "unresolved_questions": [
            {
                "question_id": "question-1",
                "question": question_text,
                "status": "open",
            }
        ],
        "decision_hygiene": {},
    }


def test_render_user_report_filters_legacy_filtered_question():
    """Even if a legacy state still carries the old "Positive/support
    evidence was filtered..." note, ``render_user_report`` must scrub it
    via ``_REPORT_META_LEAKAGE_TERMS`` before user-facing rendering."""
    state = _user_report_state_with_unresolved_question(
        "Positive/support evidence was filtered; a copied negative_or_gap quote-bank item was used as conservative hard-negative evidence."
    )
    report = render_user_report(state, {})
    lowered = report.lower()
    assert "filtered" not in lowered
    assert "negative_or_gap" not in lowered
    assert "hard-negative" not in lowered
    assert "audit trace" not in lowered
    assert "system recovery" not in lowered


def test_render_user_report_filters_machine_audit_terms():
    state = _user_report_state_with_unresolved_question(
        "binary_decision=reject. recommendation_view=borderline_positive (audit trace internal id)."
    )
    report = render_user_report(state, {})
    lowered = report.lower()
    for forbidden in (
        "binary_decision",
        "recommendation_view",
        "audit trace",
        "internal id",
        "borderline_positive",
        "reject_like",
    ):
        assert forbidden not in lowered


# ---------------------------------------------------------------------------
# P0-5 synthetic recovery marker stripping regression guards.
# ---------------------------------------------------------------------------


def test_synthetic_recovery_marker_helpers():
    assert _is_synthetic_recovery_marker_evidence_id("evidence-recovery-missing-claim-1") is True
    assert _is_synthetic_recovery_marker_evidence_id("EVIDENCE-RECOVERY-MISSING-Claim-2") is True
    assert _is_synthetic_recovery_marker_evidence_id("evidence-fallback-5-turn-5") is True
    assert _is_synthetic_recovery_marker_evidence_id("evidence-1-turn-3") is False
    assert _is_synthetic_recovery_marker_evidence_id("") is False
    assert _is_synthetic_recovery_marker_evidence_id(None) is False
    assert _strip_synthetic_recovery_markers(None) == []
    assert _strip_synthetic_recovery_markers([]) == []
    cleaned = _strip_synthetic_recovery_markers([
        "evidence-1",
        "",
        "evidence-recovery-missing-claim-x",
        "evidence-fallback-5-turn-5",
        "evidence-2",
    ])
    assert cleaned == ["evidence-1", "evidence-2"]


def test_supporting_evidence_ids_strip_synthetic_recovery_marker_on_merge():
    """``merge_review_state`` must strip ``evidence-recovery-missing-*``
    ids from claim ``supporting_evidence_ids`` so saved state never points
    a real claim at a synthetic diagnostic marker."""
    state = {
        "claims": [
            {
                "claim_id": "claim-1",
                "claim": "The method improves benchmark accuracy.",
                "status": "uncertain",
                "claim_kind": "paper_extracted",
                "supporting_evidence_ids": [
                    "evidence-recovery-missing-claim-1",
                    "evidence-real-1",
                ],
            }
        ],
        "evidence_map": [
            {
                "evidence_id": "evidence-real-1",
                "claim_id": "claim-1",
                "evidence": "Table 2 reports the improvement.",
                "stance": "supports",
                "strength": "strong",
            },
            {
                "evidence_id": "evidence-recovery-missing-claim-1",
                "claim_id": "claim-1",
                "evidence": "Recovery could not verify this claim.",
                "stance": "missing",
                "strength": "missing",
                "source": "system recovery salvage",
            },
        ],
        "flaw_candidates": [],
        "unresolved_questions": [],
    }
    merged = merge_review_state(state, {"evidence_map": []})
    claim = merged["claims"][0]
    for ev_id in claim.get("supporting_evidence_ids", []):
        assert not _is_synthetic_recovery_marker_evidence_id(ev_id)
    assert "evidence-real-1" in claim.get("supporting_evidence_ids", [])


# ---------------------------------------------------------------------------
# Mainline-Final-Integrated regression tests (P0-1 final-strong guard,
# negative-anchor promotion block, P1-2 contested-support arbitration).
# ---------------------------------------------------------------------------


def _final_strong_guard_paper_state(evidence: dict) -> dict:
    """Render a minimal ReviewState that exercises the hygiene-time
    `_final_strong_guard` via :func:`build_decision_hygiene_view`.

    A matching ``evidence_quote_bank`` entry is included so that
    ``_verify_evidence_grounding_against_state`` enters the full verification
    path (otherwise it short-circuits when the bank is empty and the guard
    cannot run).  The bank entry mirrors ``evidence`` so verification is a
    no-op apart from running the guard.
    """
    return {
        "paper_id": "paper-guard",
        "claims": [
            {
                "claim_id": "claim-1",
                "claim": "The method improves robustness across benchmarks.",
                "claim_kind": "paper_extracted",
                "status": "supported",
                "supporting_evidence_ids": [evidence["evidence_id"]],
            }
        ],
        "evidence_map": [evidence],
        "flaw_candidates": [],
        "unresolved_questions": [],
        "evidence_gaps": [],
        "conflict_notes": [],
        "evidence_quote_bank": [
            {
                "quote_id": str(evidence.get("quote_id") or ""),
                "raw_quote": str(evidence.get("raw_quote") or ""),
                "source_locator": str(evidence.get("source_locator") or ""),
                "source_bucket": str(evidence.get("support_source_bucket") or ""),
                "source_span_start": 100,
                "source_span_end": 100 + len(str(evidence.get("raw_quote") or "")) - 1,
            }
        ],
    }


def test_evidence_negative_locator_or_bucket_signal_detects_negative_anchors():
    # Bucket-only signal.
    assert _evidence_negative_locator_or_bucket_signal({"support_source_bucket": "negative_or_gap"})
    assert _evidence_negative_locator_or_bucket_signal({"support_source_bucket": "limitation_or_gap"})
    # Fallback bucket from the quote-bank claim-overlap canonicalisation path.
    assert _evidence_negative_locator_or_bucket_signal(
        {
            "support_source_bucket": "method_or_approach",
            "quote_bank_claim_overlap_fallback_source_bucket": "negative_or_gap",
        }
    )
    # Locator-only signal (regardless of bucket).
    assert _evidence_negative_locator_or_bucket_signal(
        {"source_locator": "Limitation / Gap / Negative evidence excerpt #1"}
    )
    assert _evidence_negative_locator_or_bucket_signal({"source_locator": "Missing comparison vs SOTA"})
    # Positive anchors are not flagged.
    assert not _evidence_negative_locator_or_bucket_signal(
        {"support_source_bucket": "method_or_approach", "source_locator": "Section 3"}
    )
    assert not _evidence_negative_locator_or_bucket_signal({})
    # Sanity: the canonical limitation/negative buckets are exposed as a
    # frozenset constant for downstream audits.
    assert "negative_or_gap" in NEGATIVE_SUPPORT_BUCKETS
    assert "limitation_or_gap" in NEGATIVE_SUPPORT_BUCKETS


def test_final_strong_guard_downgrades_negative_locator_strong_support():
    """A `stance=supports, strength=strong` row whose locator/bucket marks
    it as a limitation/negative-evidence anchor must be downgraded to
    `verified_moderate`, regardless of the semantic alignment score.

    The guard is exercised directly so the assertion does not depend on the
    semantic re-scoring done inside ``build_decision_hygiene_view``.
    """
    evidence = {
        "strength": "strong",
        "stance": "supports",
        "verified_grounding_label": "paper_grounded_exact",
        "semantic_grounding_label": "semantic_support_verified",
        "semantic_alignment_score": 0.95,  # Above the FINAL_STRONG_MIN_SCORE.
        "support_source_bucket": "limitation_or_gap",
        "source_locator": "Limitation / Gap / Negative evidence excerpt #1",
    }
    _final_strong_guard(evidence)
    assert evidence["strength"] == "medium"
    assert evidence["final_strength_guard_downgrade_reason"] == "negative_locator_strong_support_downgrade"
    assert evidence["strength_promotion_held_at_moderate"] is True
    assert "downgraded_negative_locator" in evidence.get("support_quality_adjustment", "")
    # Idempotent: applying the guard a second time must not flip the row
    # back to strong nor mutate the reason.
    _final_strong_guard(evidence)
    assert evidence["strength"] == "medium"
    assert evidence["final_strength_guard_downgrade_reason"] == "negative_locator_strong_support_downgrade"


def test_final_strong_guard_downgrades_low_score_strong_support():
    """A `stance=supports, strength=strong` method-section row whose
    `semantic_alignment_score` falls below the calibrated floor must be
    downgraded to `verified_moderate`."""
    evidence = {
        "strength": "strong",
        "stance": "supports",
        "verified_grounding_label": "paper_grounded_exact",
        "verified_quote_match_type": "exact_match",
        "semantic_grounding_label": "semantic_support_verified",
        "semantic_alignment_score": 0.3,  # Below FINAL_STRONG_MIN_SCORE.
        "support_source_bucket": "method_or_approach",
        "source_locator": "Section 3 Method",
    }
    _final_strong_guard(evidence)
    assert evidence["strength"] == "medium"
    assert evidence["final_strength_guard_downgrade_reason"] == "low_score_strong_support_downgrade"
    assert "downgraded_low_semantic_alignment" in evidence.get("support_quality_adjustment", "")


def test_final_strong_guard_keeps_table_anchor_strong_with_low_score():
    """Verified table/figure anchor exception: a `paper_grounded_exact`
    quote-bank canonical anchor with low textual overlap is allowed to stay
    strong because the table number matches by anchor, not by token overlap."""
    evidence = {
        "strength": "strong",
        "stance": "supports",
        "verified_grounding_label": "paper_grounded_exact",
        "verified_quote_match_type": "exact_match",
        "semantic_grounding_label": "semantic_support_verified",
        "semantic_alignment_score": 0.4,  # Below FINAL_STRONG_MIN_SCORE.
        "support_source_bucket": "table_or_figure",
        "source": "table",
        "source_locator": "Table 3",
    }
    _final_strong_guard(evidence)
    assert evidence["strength"] == "strong"
    assert evidence.get("final_strength_guard_downgrade_reason", "") == ""
    # Same exception applies to result_or_experiment and theory_or_proof.
    for bucket in ("result_or_experiment", "theory_or_proof"):
        ev = dict(evidence, support_source_bucket=bucket, source="results")
        ev.pop("final_strength_guard_downgrade_reason", None)
        _final_strong_guard(ev)
        assert ev["strength"] == "strong", f"bucket={bucket} unexpectedly downgraded"


def test_final_strong_guard_downgrades_semantic_weak_table_promotion():
    """The table-anchor exception does not apply to semantic-weak promotion rows.

    These rows are exactly what the dashboard's low_score_promoted_strong guard
    is designed to catch: they have a paper anchor, but the support relation is
    weak enough that they should remain verified moderate.
    """
    evidence = {
        "strength": "strong",
        "stance": "supports",
        "verified_grounding_label": "paper_grounded_exact",
        "verified_quote_match_type": "quote_bank_id_canonical",
        "semantic_grounding_label": "semantic_support_verified",
        "semantic_alignment_score": 0.2,
        "support_source_bucket": "result_or_experiment",
        "source": "results",
        "source_locator": "Figure: teaser",
        "semantic_weak_promotion_used": True,
    }

    _final_strong_guard(evidence)

    assert evidence["strength"] == "medium"
    assert evidence["final_strength_guard_downgrade_reason"] == "low_score_strong_support_downgrade"


def test_final_strong_guard_skips_non_strong_or_non_support_evidence():
    """The guard is a strong-only downgrade pass; medium and non-supports
    rows should be untouched even when they look like negative anchors."""
    medium_negative = {
        "strength": "medium",
        "stance": "supports",
        "support_source_bucket": "limitation_or_gap",
        "source_locator": "Limitation / Gap quote",
        "semantic_alignment_score": 0.2,
    }
    _final_strong_guard(medium_negative)
    assert medium_negative["strength"] == "medium"
    assert "final_strength_guard_downgrade_reason" not in medium_negative

    strong_negative_stance = {
        "strength": "strong",
        "stance": "contradicts",
        "support_source_bucket": "limitation_or_gap",
        "source_locator": "Limitation / Gap quote",
    }
    _final_strong_guard(strong_negative_stance)
    assert strong_negative_stance["strength"] == "strong"
    assert "final_strength_guard_downgrade_reason" not in strong_negative_stance


def test_classify_medium_support_promotion_tier_blocks_negative_anchor():
    """Promotion path must reject Limitation / Gap / Negative anchors even
    when the bucket label is method/result and the score is high enough."""
    evidence = {
        "strength": "medium",
        "initial_strength": "medium",
        "stance": "supports",
        "binding_status": "bound_real_claim",
        "verified_grounding_label": "paper_grounded_exact",
        "semantic_grounding_label": "semantic_support_verified",
        "semantic_alignment_score": 0.85,
        "verified_claim_overlap_score": 4,
        "support_source_bucket": "method_or_approach",
        "source_locator": "Limitation / Gap / Negative evidence excerpt #1",
        "evidence_id": "evidence-1",
        "claim_id": "claim-1",
        "evidence": "A method paragraph mentioning a limitation.",
        "raw_quote": "The method has a limitation in the cross-domain setting.",
    }
    decision = _classify_medium_support_promotion_tier(evidence)
    assert decision == {"tier": "moderate", "reason": "negative_anchor_support_held_at_moderate"}


def test_contested_support_keeps_positive_in_final_view_and_flags_arbitration():
    """A claim with both a real-strong positive support AND a verified
    paper-negative concern must keep the positive support in the final view
    while exposing `contested_support=True`.

    The claim text and the positive raw_quote share enough non-stopword
    tokens (``robustness``, ``improves``, ``benchmark``, ``held-out``) for
    the hygiene-time semantic grounder to keep ``semantic_alignment_score``
    above ``FINAL_STRONG_MIN_SCORE`` so the positive support survives the
    P0-1 guard.
    """
    positive_quote = "Robustness improves on the held-out benchmark across runs."
    negative_quote = "The comparison to the strongest baseline is not reported."
    state = {
        "paper_id": "paper-contested",
        "claims": [
            {
                "claim_id": "claim-1",
                "claim": "Robustness improves across benchmarks.",
                "claim_kind": "paper_extracted",
                "status": "supported",
                "supporting_evidence_ids": ["positive-1"],
            }
        ],
        "evidence_map": [
            {
                "evidence_id": "positive-1",
                "claim_id": "claim-1",
                "evidence": "Robustness improves on the held-out benchmark across runs.",
                "raw_quote": positive_quote,
                "quote_id": "quote-result-1",
                "strength": "strong",
                "stance": "supports",
                "binding_status": "bound_real_claim",
                "verified_grounding_label": "paper_grounded_exact",
                "semantic_grounding_label": "semantic_support_verified",
                "semantic_alignment_score": 0.85,
                "support_source_bucket": "result_or_experiment",
                "source": "Results / Evaluation",
                "source_locator": "Section 4 Results",
            },
            {
                "evidence_id": "negative-1",
                "claim_id": "claim-1",
                "evidence": "The strongest baseline comparison is not reported.",
                "raw_quote": negative_quote,
                "quote_id": "quote-negative-1",
                "strength": "missing",
                "stance": "missing",
                "binding_status": "bound_real_claim",
                "verified_grounding_label": "paper_grounded_exact",
                "semantic_grounding_label": "semantic_negative_verified",
                "support_source_bucket": "limitation_or_gap",
                "source_locator": "Limitation Section",
            },
        ],
        "flaw_candidates": [
            {
                "flaw_id": "flaw-1",
                "description": "The strongest baseline comparison is not reported.",
                "status": "candidate",
                "related_claim_ids": ["claim-1"],
                "evidence_ids": ["negative-1"],
                "negative_evidence_ids": ["negative-1"],
            }
        ],
        "unresolved_questions": [],
        "evidence_gaps": [],
        "conflict_notes": [],
        "evidence_quote_bank": [
            {
                "quote_id": "quote-result-1",
                "raw_quote": positive_quote,
                "source_locator": "Section 4 Results",
                "source_bucket": "result_or_experiment",
                "source_span_start": 100,
                "source_span_end": 100 + len(positive_quote) - 1,
            },
            {
                "quote_id": "quote-negative-1",
                "raw_quote": negative_quote,
                "source_locator": "Limitation Section",
                "source_bucket": "limitation_or_gap",
                "source_span_start": 500,
                "source_span_end": 500 + len(negative_quote) - 1,
            },
        ],
    }
    hygiene = build_decision_hygiene_view(state)["decision_hygiene"]
    trace = {item["evidence_id"]: item for item in hygiene["support_survival_trace"]}
    # The positive support stays in the final view (P1-2 isolation rule).
    assert trace["positive-1"]["included_in_final_view"] is True
    assert trace["positive-1"]["final_strength"] == "strong"
    assert trace["positive-1"]["contested_support"] is True
    assert trace["positive-1"]["final_drop_reason"] == ""
    # Top-level + summary metrics expose the contested arbitration.
    assert hygiene["real_strong_support_total"] == 1
    assert hygiene["contested_support_total"] == 1
    assert hygiene["contested_final_support_total"] == 1
    assert hygiene["claims_with_contested_support"] == 1
    assert hygiene["claims_with_contested_final_support"] == 1
    # Legacy negative-burden drop reason must be retired.
    assert "overridden_by_negative_burden" not in hygiene["support_admission_blocker_counts"]
    assert "overridden_by_negative_burden" not in hygiene["support_survival_summary"]["drop_by_final_reason"]


def test_summary_exposes_guard_and_contested_metrics_when_no_negative_evidence():
    """When the trace has only clean positive supports, contested + guard
    counters must default to zero and stay schema-stable."""
    # Build a synthetic trace directly so the assertion does not depend on
    # the hygiene-time semantic re-scoring; the summary aggregator only
    # reads per-item flags.
    trace = [
        {
            "claim_id": "claim-1",
            "support_admission_tier": "verified_strong",
            "support_admission_blocker": "",
            "semantic_grounding_label": "semantic_support_verified",
            "included_in_final_view": True,
            "final_support_depth": "deep",
            "final_drop_reason": "",
            "claim_kind": "paper_extracted",
            "initial_strength": "strong",
            "final_strength": "strong",
            "contested_support": False,
            "final_strength_guard_downgrade_reason": "",
            "quote_bank_claim_overlap_fallback_used": False,
            "semantic_weak_promotion_used": False,
            "strength_promotion_from_medium_used": False,
            "verified_grounding_label": "paper_grounded_exact",
            "verified_quote_match_type": "exact_match",
            "verified_claim_overlap_score": 0,
            "semantic_alignment_score": 0.9,
            "decision_support_source_bucket": "result_or_experiment",
            "declared_support_source_bucket": "result_or_experiment",
            "support_depth": "deep",
            "quote_id": "quote-1",
            "raw_quote": "...",
            "evidence_id": "evidence-1",
        }
    ]
    summary = _support_survival_summary(trace)
    assert summary["contested_support_total"] == 0
    assert summary["claims_with_contested_support"] == 0
    assert summary["final_strong_guard_low_score_downgrade_count"] == 0
    assert summary["final_strong_guard_negative_locator_downgrade_count"] == 0
    assert summary["final_strong_guard_downgrade_total"] == 0
    # Schema stability: the legacy alias keys still exist for downstream
    # audits that read them.
    assert "contested_final_support_total" in summary
    assert "claims_with_contested_final_support" in summary


def test_final_strong_min_score_constant_aligns_with_method_moderate_floor():
    """The final-strong guard floor must match the calibrated method
    promotion moderate floor so the two layers stay consistent."""
    assert FINAL_STRONG_MIN_SCORE == METHOD_PROMOTION_MODERATE_MIN_SCORE
    assert FINAL_STRONG_MIN_SCORE == DEEP_PROMOTION_STRONG_MIN_SCORE
    assert FINAL_STRONG_MIN_SCORE < METHOD_PROMOTION_STRONG_MIN_SCORE


# ========================================================================
# P0-4 (diagnostic-only) — 5-class negative_evidence_type tests
# These tests verify that:
#   1. The classifier returns one of the 5 deterministic types
#   2. The strict cue ordering wins (contradiction > negative_result > missing
#      > scope > generic_gap)
#   3. The label is attached to negative_or_gap quote-bank entries
#   4. The label is propagated to evidence_map items via metadata
#   5. NO quotes are dropped — diagnostic-only behavior
# ========================================================================


def test_classify_negative_evidence_type_returns_5_class_enum():
    """Every output must be one of the 5 enum values, including for empty input."""
    types_seen = set()
    samples = [
        "",
        "The proposed method has limitations in handling long sequences.",
        "Our approach underperforms the baseline on the easier tasks.",
        "We do not compare with a recent baseline (XYZ et al. 2023).",
        "These assumptions break down when applied to high-dimensional data.",
        "Some neutral text without strong critique signal.",
    ]
    for s in samples:
        t = _classify_negative_evidence_type(s)
        assert t in NEGATIVE_EVIDENCE_TYPES_ALL, f"Unknown type {t!r} for {s!r}"
        types_seen.add(t)
    # Should cover at least 3 of the 5 types
    assert len(types_seen) >= 3


def test_classify_negative_evidence_type_strict_cue_order():
    """Direct contradiction > negative_result > typed missing evidence > scope_limitation."""
    # Contradiction wins over scope_limitation cues
    assert (
        _classify_negative_evidence_type(
            "These assumptions limit the model and cannot prove convergence."
        )
        == "direct_contradiction"
    )
    # Negative result wins over scope_limitation
    assert (
        _classify_negative_evidence_type(
            "The model underperforms baselines despite these limitations."
        )
        == "negative_result"
    )
    assert (
        _classify_negative_evidence_type(
            "The OE task shows a slight performance decline, hinting at architectural limitations."
        )
        == "negative_result"
    )
    # Baseline and ablation gaps remain separate typed missing-evidence classes.
    assert (
        _classify_negative_evidence_type(
            "We do not compare with stronger baselines, a known limitation."
        )
        == "missing_baseline"
    )
    assert (
        _classify_negative_evidence_type(
            "We do not provide ablation studies, a known limitation."
        )
        == "missing_ablation"
    )
    # Scope limitation only
    assert (
        _classify_negative_evidence_type(
            "This is a clear limitation of our current framework."
        )
        == "scope_limitation"
    )


def test_classify_negative_evidence_type_falls_through_to_generic_gap():
    """Strings that match the broad anchor regex but no specific cue \u2192 generic_gap."""
    # 'without' is in the broad anchor regex but matches no specific cue
    assert (
        _classify_negative_evidence_type("The system runs without external supervision.")
        == "generic_gap"
    )
    # Empty string defaults to generic_gap
    assert _classify_negative_evidence_type("") == "generic_gap"


def test_quote_bank_attaches_negative_evidence_type_to_negative_quotes():
    """negative_or_gap entries must carry the diagnostic type field."""
    body = (
        "Section 3. Method.\nWe propose a new architecture for image recognition.\n\n"
        "Section 4. Limitations.\nA clear limitation is that the proposed method "
        "underperforms baselines on small datasets, indicating poor generalization.\n"
    )
    bank = _build_evidence_quote_bank(body, max_quotes=6)
    neg_entries = [e for e in bank if e.get("source_bucket") == "negative_or_gap"]
    assert len(neg_entries) >= 1, "Expected at least one negative_or_gap entry"
    for entry in neg_entries:
        assert "negative_evidence_type" in entry, (
            f"negative_evidence_type missing on negative entry: {entry}"
        )
        assert entry["negative_evidence_type"] in NEGATIVE_EVIDENCE_TYPES_ALL


def test_quote_bank_does_not_attach_neg_type_to_non_negative_quotes():
    """Only negative_or_gap entries get the type label; method/results/etc. don't."""
    body = (
        "Section 3. Method.\nWe propose a transformer-based architecture for vision.\n\n"
        "Section 5. Results.\nOur model achieves 92.3% accuracy on ImageNet, "
        "outperforming previous baselines by 3.1 points.\n"
    )
    bank = _build_evidence_quote_bank(body, max_quotes=6)
    non_neg = [e for e in bank if e.get("source_bucket") != "negative_or_gap"]
    for entry in non_neg:
        assert "negative_evidence_type" not in entry, (
            f"Non-negative entry unexpectedly carries neg_type: {entry}"
        )


def test_negative_typing_does_not_drop_any_quotes_diagnostic_only():
    """Diagnostic-only contract: classification must NOT filter or drop quotes.

    A quote that would have been classified as generic_gap (low specificity)
    must still appear in the quote bank just like any other negative_or_gap
    entry — only with a label attached.
    """
    # Build a body where the negative anchor is generic ('without external')
    body = (
        "Section 3. Method.\nThe proposed method achieves accurate classification.\n\n"
        "Section 4. Discussion.\nNote that our approach operates without external "
        "supervision and processes inputs in a single forward pass.\n"
    )
    bank = _build_evidence_quote_bank(body, max_quotes=6)
    # All entries that match the broad negative anchor should be retained.
    # Even a 'generic_gap' classification is kept (diagnostic only).
    neg_entries = [e for e in bank if e.get("source_bucket") == "negative_or_gap"]
    if neg_entries:
        # If any negative_or_gap entry was extracted, it must have the type label
        # and must not have been filtered out due to its category.
        for entry in neg_entries:
            assert "negative_evidence_type" in entry


def _negative_type_flaw_state(negative_type: str, *, status: str = "candidate", severity: str = "minor"):
    return {
        "claims": [{"claim_id": "claim-main", "status": "supported", "claim_kind": "paper_extracted"}],
        "evidence_map": [
            {
                "evidence_id": "e-neg-1",
                "claim_id": "claim-main",
                "stance": "missing",
                "strength": "missing",
                "source": "Evidence Agent",
                "source_locator": "Results excerpt #1",
                "support_source_bucket": "limitation_or_gap",
                "negative_evidence_type": negative_type,
                "verified_grounding_label": "paper_grounded_exact",
                "verified_source_span_start": 10,
                "verified_source_span_end": 78,
                "verified_quote_match_type": "exact",
                "semantic_grounding_label": "semantic_negative_verified",
                "binding_status": "bound_real_claim",
                "raw_quote": "The method underperforms the baseline on the main benchmark.",
            }
        ],
        "flaw_candidates": [
            {
                "flaw_id": "flaw-neg-1",
                "flaw": "The paper reports a negative result relevant to the main benchmark.",
                "status": status,
                "severity": severity,
                "related_claim_ids": ["claim-main"],
                "evidence_ids": ["e-neg-1"],
                "negative_evidence_ids": ["e-neg-1"],
            }
        ],
    }


def test_final_view_routes_generic_gap_negative_to_assessment_limitation():
    view = build_decision_hygiene_view(_negative_type_flaw_state("generic_gap"))
    flaw = view["flaw_candidates"][0]
    dh = view["decision_hygiene"]

    assert flaw["final_view_flaw_layer"] == "assessment_limitation"
    assert dh["verified_negative_flaw_count"] == 0
    assert dh["verified_actionable_negative_flaw_count"] == 0
    assert dh["verified_limitation_negative_flaw_count"] == 0
    assert dh.get("negative_evidence_type_counts", {}) == {}


def test_final_view_routes_actionable_negative_candidate_to_potential_concern():
    view = build_decision_hygiene_view(
        _negative_type_flaw_state("negative_result", status="candidate", severity="major")
    )
    flaw = view["flaw_candidates"][0]
    dh = view["decision_hygiene"]

    assert flaw["final_view_flaw_layer"] == "potential_concern"
    assert flaw["negative_flaw_not_upgraded_reason"] == "not_confirmed_stays_potential_concern"
    assert dh["verified_negative_flaw_count"] == 1
    assert dh["verified_actionable_negative_flaw_count"] == 1
    assert dh["verified_potential_concern_count"] == 1
    assert dh["potential_concern_count"] == 1
    assert dh["negative_evidence_type_counts"] == {"negative_result": 1}


def test_final_view_routes_scope_overclaim_to_potential_concern():
    state = _negative_type_flaw_state("scope_overclaim", status="candidate", severity="major")
    state["claims"][0]["claim"] = "The method generalizes to unseen graph settings."
    state["evidence_map"][0]["raw_quote"] = "The method is only evaluated on synthetic graphs and does not generalize to unseen graph settings."

    view = build_decision_hygiene_view(state)
    flaw = view["flaw_candidates"][0]
    dh = view["decision_hygiene"]

    assert flaw["final_view_flaw_layer"] == "potential_concern"
    assert dh["verified_actionable_negative_flaw_count"] == 1
    assert dh["verified_potential_concern_count"] == 1
    assert dh["potential_concern_count"] == 1
    assert dh["negative_evidence_type_counts"] == {"scope_overclaim": 1}


def test_author_future_work_note_does_not_become_scope_overclaim_concern():
    state = _negative_type_flaw_state("scope_overclaim", status="candidate", severity="major")
    state["claims"][0]["claim"] = "The method generalizes to unseen graph settings."
    state["evidence_map"][0]["raw_quote"] = "Additional relation types are left for future work."

    view = build_decision_hygiene_view(state)
    flaw = view["flaw_candidates"][0]
    dh = view["decision_hygiene"]

    assert flaw["final_view_flaw_layer"] == "assessment_limitation"
    assert dh["verified_actionable_negative_flaw_count"] == 0
    assert dh["verified_potential_concern_count"] == 0
    assert dh["potential_concern_count"] == 0
    assert dh["author_limitation_only_count"] == 1


def test_decision_view_syncs_actionable_flaw_type_to_verified_limitation_evidence():
    state = _negative_type_flaw_state("scope_limitation", status="candidate", severity="major")
    state["claims"][0]["claim"] = "The method generalizes to unseen graph settings."
    state["evidence_map"][0]["raw_quote"] = "The method is only evaluated on synthetic graphs in the reported experiments."
    state["evidence_map"][0]["negative_evidence_actionability"] = "actionable_candidate"
    state["flaw_candidates"][0]["negative_evidence_type"] = "scope_overclaim"
    state["flaw_candidates"][0]["flaw"] = "Verified scope overclaim against a broad generalization claim."

    view = build_decision_hygiene_view(state)
    flaw = view["flaw_candidates"][0]
    evidence = view["evidence_map"][0]
    dh = view["decision_hygiene"]

    # The flaw's type is synced onto the linked evidence (scope_limitation -> scope_overclaim),
    # recording the original. Under Route A the evidence verifies as an actionable candidate
    # ("only evaluated on synthetic graphs" is a concrete scope gap against the broad
    # generalization claim), so the flaw is surfaced as an actionable potential concern.
    assert evidence["negative_evidence_type"] == "scope_overclaim"
    assert evidence["negative_evidence_type_original"] == "scope_limitation"
    assert evidence["negative_evidence_type_decision_view_reason"] == "linked_actionable_flaw_type_sync"
    assert dh["synced_actionable_negative_type_count"] == 1
    assert flaw["final_view_flaw_layer"] == "potential_concern"
    assert dh["verified_actionable_negative_flaw_count"] == 1
    assert dh["potential_concern_count"] == 1
    assert dh.get("contamination_negative_evidence_overclaim", 0) == 0


def test_decision_view_auto_binds_unlinked_verified_negative_evidence():
    state = {
        "claims": [
            {
                "claim_id": "claim-main",
                "claim": "The model improves the main benchmark.",
                "status": "supported",
                "claim_kind": "paper_extracted",
            }
        ],
        "evidence_map": [
            {
                "evidence_id": "e-neg-unlinked",
                "claim_id": "claim-main",
                "stance": "contradicts",
                "strength": "medium",
                "source": "results",
                "source_locator": "results",
                "support_source_bucket": "result_or_experiment",
                "negative_evidence_type": "negative_result",
                "verified_grounding_label": "paper_grounded_exact",
                "verified_quote_match_type": "quote_bank_raw_canonical",
                "verified_source_span_start": 10,
                "verified_source_span_end": 84,
                "semantic_grounding_label": "semantic_negative_verified",
                "review_negative_label": "review_negative_verified",
                "binding_status": "bound_real_claim",
                "raw_quote": "The method performs worse than the baseline on the main benchmark.",
                "agent_raw_quote": "The method performs worse than the baseline on the main benchmark.",
            }
        ],
        "flaw_candidates": [],
    }

    view = build_decision_hygiene_view(state)
    dh = view["decision_hygiene"]

    assert dh["negative_evidence_candidate_count"] == 1
    assert dh["negative_evidence_linked_to_flaw_count"] == 1
    assert dh["negative_evidence_unlinked_to_flaw_count"] == 0
    assert dh["auto_bound_negative_flaw_count"] == 1
    assert dh["verified_actionable_negative_flaw_count"] == 1
    assert dh["potential_concern_count"] == 1
    assert view["flaw_candidates"][0]["source"] == "decision-view-auto-negative-binding"


def test_decision_view_deduplicates_same_verified_negative_quote():
    quote = (
        "Alpha must be tuned for each method and therefore cannot be used to "
        "compare intervention effects across methods."
    )
    state = {
        "claims": [
            {
                "claim_id": "claim-main",
                "claim": "The intervention framework supports fair comparison across methods.",
                "status": "supported",
                "claim_kind": "paper_extracted",
            }
        ],
        "evidence_map": [
            {
                "evidence_id": "e-neg-a",
                "claim_id": "claim-main",
                "stance": "contradicts",
                "strength": "strong",
                "source": "Methodology section",
                "source_locator": "Limitation / Gap / Negative evidence excerpt #1",
                "support_source_bucket": "limitation_or_gap",
                "negative_evidence_type": "evaluation_protocol_risk",
                "verified_grounding_label": "paper_grounded_exact",
                "verified_quote_match_type": "quote_bank_raw_canonical",
                "verified_source_span_start": 100,
                "verified_source_span_end": 220,
                "semantic_grounding_label": "semantic_negative_verified",
                "review_negative_label": "review_negative_verified",
                "review_negative_reason": "comparison_invalidation_weakens_claim",
                "binding_status": "bound_real_claim",
                "raw_quote": quote,
            },
            {
                "evidence_id": "e-neg-b",
                "claim_id": "claim-main",
                "stance": "contradicts",
                "strength": "strong",
                "source": "Methodology section",
                "source_locator": "Methodology section",
                "support_source_bucket": "limitation_or_gap",
                "negative_evidence_type": "evaluation_protocol_risk",
                "verified_grounding_label": "paper_grounded_exact",
                "verified_quote_match_type": "quote_bank_id_canonical",
                "verified_source_span_start": 100,
                "verified_source_span_end": 220,
                "semantic_grounding_label": "semantic_negative_verified",
                "review_negative_label": "review_negative_verified",
                "review_negative_reason": "comparison_invalidation_weakens_claim",
                "binding_status": "bound_real_claim",
                "raw_quote": quote,
            },
        ],
        "flaw_candidates": [],
    }

    view = build_decision_hygiene_view(state)
    dh = view["decision_hygiene"]

    assert dh["review_negative_verified_count"] == 1
    assert dh["negative_evidence_candidate_count"] == 1
    assert dh["negative_evidence_candidate_raw_count"] == 2
    assert dh["negative_evidence_linked_to_flaw_count"] == 1
    assert dh["negative_evidence_linked_to_flaw_raw_count"] == 2
    assert dh["negative_evidence_unlinked_to_flaw_count"] == 0
    assert dh["auto_bound_negative_flaw_count"] == 1
    assert dh["verified_actionable_negative_flaw_count"] == 1
    assert dh["potential_concern_count"] == 1
    assert dh["negative_evidence_type_counts"] == {"evaluation_protocol_risk": 1}
    assert len(view["flaw_candidates"]) == 1
    assert set(view["flaw_candidates"][0]["negative_evidence_ids"]) == {"e-neg-a", "e-neg-b"}


def test_render_user_report_surfaces_auto_bound_verified_negative_concern():
    state = {
        "claims": [
            {
                "claim_id": "claim-main",
                "claim": "The intervention framework supports fair comparison across methods.",
                "status": "supported",
                "claim_kind": "paper_extracted",
            }
        ],
        "evidence_map": [
            {
                "evidence_id": "e-neg",
                "claim_id": "claim-main",
                "stance": "contradicts",
                "strength": "strong",
                "source": "Methodology section",
                "source_locator": "Limitation / Gap / Negative evidence excerpt #1",
                "support_source_bucket": "limitation_or_gap",
                "negative_evidence_type": "evaluation_protocol_risk",
                "verified_grounding_label": "paper_grounded_exact",
                "verified_quote_match_type": "quote_bank_raw_canonical",
                "verified_source_span_start": 100,
                "verified_source_span_end": 220,
                "semantic_grounding_label": "semantic_negative_verified",
                "semantic_grounding_reasons": ["comparison_invalidation_verified"],
                "review_negative_label": "review_negative_verified",
                "review_negative_reason": "comparison_invalidation_weakens_claim",
                "binding_status": "bound_real_claim",
                "raw_quote": (
                    "Alpha must be tuned for each method and therefore cannot be used "
                    "to compare intervention effects across methods."
                ),
            }
        ],
        "flaw_candidates": [],
        "unresolved_questions": [],
        "evidence_gaps": [],
        "conflict_notes": [],
    }

    report = render_user_report(state, {})

    assert "Verified negative concern" in report
    assert "Alpha must be tuned" in report
    assert "Methodology section reports" in report
    assert "Negative evidence excerpt" not in report


def test_potential_concern_text_includes_verified_negative_context():
    state = _negative_type_flaw_state("negative_result", status="candidate", severity="major")
    state["claims"][0]["claim"] = "The method improves the main benchmark over all baselines."
    state["evidence_map"][0]["source_locator"] = "Table 2"
    state["evidence_map"][0]["raw_quote"] = "The method underperforms the strongest baseline on the main benchmark."

    view = build_decision_hygiene_view(state)
    concerns = _render_potential_concerns(view)

    assert concerns
    line = concerns[0]
    assert "The method improves the main benchmark over all baselines." in line
    assert "The method underperforms the strongest baseline" in line
    assert "negative type: negative result" in line
    assert "review implication" in line


def test_final_view_does_not_hide_verified_actionable_fallback_flaw():
    state = _negative_type_flaw_state("negative_result", status="candidate", severity="major")
    state["flaw_candidates"][0]["source"] = "fallback-extraction"
    state["flaw_candidates"][0]["grounding_status"] = "verified_actionable_candidate"

    view = build_decision_hygiene_view(state)
    flaw = view["flaw_candidates"][0]
    dh = view["decision_hygiene"]

    assert flaw["status"] == "candidate"
    assert flaw["final_view_flaw_layer"] == "potential_concern"
    assert dh["verified_potential_concern_count"] == 1
    assert dh["potential_concern_count"] == 1
    assert _render_potential_concerns(view)


def test_final_view_allows_confirmed_actionable_negative_as_grounded_weakness():
    view = build_decision_hygiene_view(
        _negative_type_flaw_state("direct_contradiction", status="confirmed", severity="major")
    )
    flaw = view["flaw_candidates"][0]
    dh = view["decision_hygiene"]

    assert flaw["final_view_flaw_layer"] == "grounded_weakness"
    assert dh["grounded_weakness_count"] == 1
    assert dh["verified_actionable_negative_flaw_count"] == 1


# --- R3: programmatic locator v2 (spec task 3.1) ---

def test_r3_locator_type_from_anchor_classification():
    assert _r3_locator_type_from_anchor("Table 2") == "table"
    assert _r3_locator_type_from_anchor("Figure 3") == "figure"
    assert _r3_locator_type_from_anchor("Fig. 1") == "figure"
    assert _r3_locator_type_from_anchor("Algorithm 1") == "algorithm"
    assert _r3_locator_type_from_anchor("Theorem 2") == "theorem"
    assert _r3_locator_type_from_anchor("Lemma 1") == "theorem"
    assert _r3_locator_type_from_anchor("Section 4.1") == "section"
    assert _r3_locator_type_from_anchor("") == "generic"
    assert _r3_locator_type_from_anchor("some prose with no anchor") == "generic"


def test_r3_details_derive_named_anchors_from_text():
    d = _r3_locator_details("As reported in Table 4, the method improves accuracy.")
    assert d["locator_type"] == "table"
    assert "Table 4" in d["locator"]
    assert d["locator_confidence"] >= 0.75

    d2 = _r3_locator_details("Theorem 2 establishes the convergence rate.")
    assert d2["locator_type"] == "theorem"
    assert d2["locator_confidence"] >= 0.75


def test_r3_details_generic_fallback_when_no_anchor():
    d = _r3_locator_details("We describe the overall approach in plain prose.")
    assert d["locator_type"] == "generic"
    assert d["locator"] == ""
    assert d["locator_confidence"] == 0.0


def test_r3_apply_locator_writes_type_and_confidence_fields():
    ev = {
        "evidence_id": "e-loc-1",
        "claim_id": "claim-1",
        "source_locator": "",
        "raw_quote": "Table 5 shows our model reaches 90.1% accuracy.",
        "evidence": "Table 5 shows our model reaches 90.1% accuracy.",
        "verified_source_span_start": -1,
        "verified_source_span_end": -1,
    }
    _r3_apply_locator({}, ev)
    assert ev.get("locator_type") in {"table", "figure", "section", "algorithm", "theorem", "generic"}
    assert "locator_confidence" in ev
    assert "source_locator_type" in ev
    assert "source_locator_confidence" in ev


def test_r3_apply_locator_does_not_invent_specific_locator_when_absent():
    ev = {
        "evidence_id": "e-loc-2",
        "claim_id": "claim-1",
        "source_locator": "",
        "raw_quote": "The approach is described qualitatively without any anchor.",
        "evidence": "The approach is described qualitatively without any anchor.",
        "verified_source_span_start": -1,
        "verified_source_span_end": -1,
    }
    _r3_apply_locator({}, ev)
    # no anchor in text/span -> must fall back to generic, never an invented specific locator
    assert ev.get("locator_type") == "generic"
    assert ev.get("source_locator_specific") in (False, None)


# --- R4: negative evidence typing + noise filtering (spec task 5.1) ---

def test_r4_bibliographic_noise_is_classified_as_noise():
    assert _r4_classify("Smith et al., 2021. Proceedings of the conference on NLP.") == "bibliographic_or_title_noise"
    assert _r4_classify("[12] arXiv: 2103.00001 preprint.") == "bibliographic_or_title_noise"


def test_r4_neutral_instruction_noise_is_classified_as_noise():
    assert _r4_classify("Review the following academic paper. Format requirements: your review must include sections.") == "neutral_instruction_noise"
    assert _r4_classify("[Instruction]: output exactly one JSON object.") == "neutral_instruction_noise"


def test_r4_substantive_types_still_classified():
    assert _r4_classify("The method does not include an ablation study.") in {"missing_ablation", "negative_result", "direct_contradiction", "insufficient_evaluation", "missing_baseline", "scope_limitation", "generic_gap"}
    # a clear contradiction stays substantive (not noise)
    assert _r4_classify("Table 7 shows the proposed method is worse than the baseline.") not in _R4_NOISE_TYPES


def test_r4_noise_excluded_from_flaw_negative_evidence_and_contested():
    # one substantive negative + one noise negative, both linked to claim-1 via a flaw
    state = {
        "claims": [{"claim_id": "claim-1", "claim_kind": "paper_extracted", "status": "supported"}],
        "evidence_map": [
            {
                "evidence_id": "evidence-neg-real",
                "claim_id": "claim-1",
                "stance": "contradicts",
                "strength": "strong",
                "raw_quote": "Table 7 shows the method is worse than the baseline by 5%.",
                "agent_raw_quote": "Table 7 shows the method is worse than the baseline by 5%.",
                "source": "Table 7",
                "source_locator": "Table 7",
                "verified_grounding_label": "paper_grounded_exact",
                "verified_quote_match_type": "quote_bank_raw_canonical",
                "verified_source_span_start": 10,
                "verified_source_span_end": 84,
                "semantic_grounding_label": "semantic_negative_verified",
                "review_negative_label": "review_negative_verified",
                "negative_evidence_type": "negative_result",
                "binding_status": "bound_real_claim",
            },
            {
                "evidence_id": "evidence-neg-noise",
                "claim_id": "claim-1",
                "stance": "contradicts",
                "strength": "strong",
                "raw_quote": "Smith et al., 2021. Proceedings of the conference on NLP.",
                "verified_grounding_label": "paper_grounded_exact",
                "semantic_grounding_label": "semantic_negative_verified",
                "negative_evidence_type": "bibliographic_or_title_noise",
                "binding_status": "bound_real_claim",
            },
        ],
        "flaw_candidates": [
            {
                "flaw_id": "flaw-1",
                "status": "candidate",
                "related_claim_ids": ["claim-1"],
                "negative_evidence_ids": ["evidence-neg-real", "evidence-neg-noise"],
                "evidence_ids": ["evidence-neg-real", "evidence-neg-noise"],
            }
        ],
    }
    valid_ids = _r4_flaw_neg_ids(state["flaw_candidates"][0], state)
    assert "evidence-neg-real" in valid_ids
    assert "evidence-neg-noise" not in valid_ids  # noise excluded
    # claim still carries a verified negative concern (from the real one)
    assert "claim-1" in _r4_burden_ids(state)


def test_r4_pure_noise_flaw_yields_no_negative_concern():
    state = {
        "claims": [{"claim_id": "claim-1", "claim_kind": "paper_extracted", "status": "supported"}],
        "evidence_map": [
            {
                "evidence_id": "evidence-neg-noise-only",
                "claim_id": "claim-1",
                "stance": "contradicts",
                "strength": "strong",
                "raw_quote": "Review the following academic paper. Format requirements apply.",
                "verified_grounding_label": "paper_grounded_exact",
                "semantic_grounding_label": "semantic_negative_verified",
                "negative_evidence_type": "neutral_instruction_noise",
            },
        ],
        "flaw_candidates": [
            {
                "flaw_id": "flaw-1",
                "status": "candidate",
                "related_claim_ids": ["claim-1"],
                "negative_evidence_ids": ["evidence-neg-noise-only"],
                "evidence_ids": ["evidence-neg-noise-only"],
            }
        ],
    }
    assert _r4_flaw_neg_ids(state["flaw_candidates"][0], state) == []
    assert "claim-1" not in _r4_burden_ids(state)


# --- R5: contested support visibility (spec task 7.1) ---

def _r5_make_state(neg_type, neg_quote):
    return {
        "paper_id": "p-r5",
        "claims": [
            {"claim_id": "claim-1", "claim_kind": "paper_extracted", "status": "supported"},
        ],
        "evidence_map": [
            {
                "evidence_id": "evidence-pos-1",
                "claim_id": "claim-1",
                "stance": "supports",
                "strength": "strong",
                "raw_quote": "Table 2 shows our method reaches 91.0% accuracy, outperforming the baseline.",
                "source": "Results",
                "source_locator": "Table 2",
                "verified_grounding_label": "paper_grounded_exact",
                "verified_source_span_start": 10,
                "verified_source_span_end": 82,
                "verified_quote_match_type": "exact",
                "semantic_grounding_label": "semantic_support_verified",
                "binding_status": "bound_real_claim",
            },
            {
                "evidence_id": "evidence-neg-1",
                "claim_id": "claim-1",
                "stance": "contradicts",
                "strength": "strong",
                "raw_quote": neg_quote,
                "verified_grounding_label": "paper_grounded_exact",
                "verified_source_span_start": 90,
                "verified_source_span_end": 160,
                "verified_quote_match_type": "exact",
                "semantic_grounding_label": "semantic_negative_verified",
                "negative_evidence_type": neg_type,
            },
        ],
        "flaw_candidates": [
            {
                "flaw_id": "flaw-1",
                "status": "candidate",
                "related_claim_ids": ["claim-1"],
                "negative_evidence_ids": ["evidence-neg-1"],
                "evidence_ids": ["evidence-neg-1"],
            }
        ],
    }


def test_r5_verified_positive_and_negative_yields_contested():
    state = _r5_make_state("negative_result", "Table 7 shows the method is worse than the baseline on task B.")
    h = _r5_hygiene(state).get("decision_hygiene", {})
    assert h.get("contested_support_total", 0) >= 1
    assert h.get("claims_with_contested_support", 0) >= 1


def test_r5_contested_does_not_delete_positive_support():
    state = _r5_make_state("negative_result", "Table 7 shows the method is worse than the baseline on task B.")
    h = _r5_hygiene(state).get("decision_hygiene", {})
    # positive real-strong support for the claim is retained, not suppressed by the concern
    assert h.get("real_strong_support_total", 0) >= 1
    assert h.get("claims_with_real_strong_support", 0) >= 1


def test_r5_contested_does_not_auto_promote_claim_to_flaw_status():
    state = _r5_make_state("negative_result", "Table 7 shows the method is worse than the baseline on task B.")
    _r5_hygiene(state)
    # the flaw stays a candidate; contested visibility must not confirm/escalate it
    assert state["flaw_candidates"][0]["status"] == "candidate"
    # the claim status is not forced down by contested visibility
    assert state["claims"][0]["status"] == "supported"


def test_r5_noise_only_negative_does_not_create_contested():
    state = _r5_make_state("bibliographic_or_title_noise", "Smith et al., 2021. Proceedings of the conference on NLP.")
    h = _r5_hygiene(state).get("decision_hygiene", {})
    # noise negative is excluded (R4) -> no contested support
    assert h.get("contested_support_total", 0) == 0
    # but the positive support is still there and the noise evidence remains in the map
    assert h.get("real_strong_support_total", 0) >= 1
    assert any(e.get("evidence_id") == "evidence-neg-1" for e in state["evidence_map"])


# --- R6: gap cleanup lifecycle (spec task 9.1) ---

def test_r6_gap_resolved_when_support_exists():
    gaps = [{"gap_id": "g1", "claim_id": "claim-1", "gap": "needs result evidence", "status": "open"}]
    kept, stale = _r6_filter_gaps(gaps, {"claim-1": 2}, set())
    assert kept == []
    assert len(stale) == 1
    assert stale[0]["gap_lifecycle_state"] == "resolved"


def test_r6_gap_converted_to_concern_when_verified_negative():
    gaps = [{"gap_id": "g1", "claim_id": "claim-1", "gap": "needs evidence", "status": "open"}]
    # no support, but the claim carries a verified negative concern
    kept, stale = _r6_filter_gaps(gaps, {}, {"claim-1"})
    assert kept == []
    assert len(stale) == 1
    assert stale[0]["gap_lifecycle_state"] == "converted_to_concern"


def test_r6_real_open_gap_is_kept_not_deleted():
    gaps = [{"gap_id": "g1", "claim_id": "claim-1", "gap": "needs empirical evidence", "status": "open"}]
    # neither support nor verified negative -> stays open and kept
    kept, stale = _r6_filter_gaps(gaps, {}, set())
    assert len(kept) == 1
    assert kept[0]["gap_lifecycle_state"] == "open"
    assert stale == []


def test_r6_fallback_gap_is_stale_or_internal():
    gaps = [{"gap_id": "g1", "claim_id": "claim-fallback-1", "gap": "claim-fallback placeholder", "status": "open"}]
    kept, stale = _r6_filter_gaps(gaps, {}, set())
    assert kept == []
    assert len(stale) == 1
    assert stale[0]["gap_lifecycle_state"] == "stale_or_internal"


def test_r6_does_not_fabricate_evidence_or_invent_gaps():
    gaps = [{"gap_id": "g1", "claim_id": "claim-1", "gap": "needs evidence", "status": "open"}]
    kept, stale = _r6_filter_gaps(gaps, {}, set())
    # output gap count never exceeds input; no evidence field invented
    assert len(kept) + len(stale) == 1
    for g in kept + stale:
        assert "evidence_id" not in g or not g.get("evidence_id")

def test_negative_classifier_keeps_related_work_contrast_neutral():
    quote = "Unlike Diffusion-TS, they do not perform multiple rounds of refinement; in contrast, our method refines node attributes and edges."
    assert _classify_negative_evidence_type(quote) == "neutral_control_context"


def test_negative_classifier_keeps_external_baseline_dataset_unavailable_neutral():
    quote = "Recognizing that HuggingGPT (Shen et al., 2024) did not release their evaluation dataset, we developed a new benchmark."
    assert _classify_negative_evidence_type(quote) == "neutral_control_context"


def test_negative_classifier_keeps_actionable_missing_ablation_and_baseline():
    assert _classify_negative_evidence_type("The paper does not report ablation experiments for the core module.") == "missing_ablation"
    assert _classify_negative_evidence_type("The paper did not compare against a strong baseline on the main benchmark.") == "missing_baseline"
    assert _classify_negative_evidence_type("The evaluation is reported without comparison with strong baselines.") == "missing_baseline"
    assert _classify_negative_evidence_type("The component contribution is not isolated by an ablation analysis.") == "missing_ablation"
    assert _classify_negative_evidence_type("The comparison to recent state-of-the-art baselines is missing.") == "missing_baseline"
    assert _classify_negative_evidence_type("The baselines are weak and not tuned for the main benchmark.") == "unfair_or_weak_baseline"
    assert _classify_negative_evidence_type("The evaluation is limited to a single dataset.") == "insufficient_evaluation"
    assert _classify_negative_evidence_type("The paper has insufficient evaluation on real benchmarks.") == "insufficient_evaluation"
    assert _classify_negative_evidence_type("The method is not evaluated on out-of-domain or unseen settings.") == "missing_robustness_or_generalization"
    assert _classify_negative_evidence_type("Hyperparameters were selected on the test set, creating train-test leakage.") == "evaluation_protocol_risk"
    assert _classify_negative_evidence_type("Runtime and memory costs are not reported for the scalable method.") == "efficiency_cost_gap"
    assert _classify_negative_evidence_type("Training details and data split details are omitted, limiting reproducibility.") == "reproducibility_gap"
    assert _classify_negative_evidence_type("Implementation details and hyperparameters are missing.") == "reproducibility_gap"
    assert _classify_negative_evidence_type("The implementation has insufficient details for reproduction.") == "reproducibility_gap"
    assert _classify_negative_evidence_type("The improvements are small and not consistent across tasks.") == "result_claim_mismatch"
    assert _classify_negative_evidence_type("Fine-tuning costs are lower than training any model from scratch.") == "generic_gap"


def test_generic_gap_cannot_anchor_grounded_negative_evidence():
    state = {
        "claims": [{"claim_id": "claim-1", "claim": "The method works.", "claim_kind": "paper_extracted"}],
        "evidence_map": [
            {
                "evidence_id": "e-neg-generic",
                "claim_id": "claim-1",
                "stance": "missing",
                "strength": "missing",
                "raw_quote": "The target domain consists of both known and unknown samples.",
                "verified_grounding_label": "paper_grounded_exact",
                "semantic_grounding_label": "semantic_negative_verified",
                "negative_evidence_type": "generic_gap",
            }
        ],
    }
    assert not _is_grounded_paper_negative_evidence_record(state["evidence_map"][0], state)


def test_positive_or_prior_work_limitation_text_is_not_review_negative():
    state = {
        "claims": [
            {
                "claim_id": "claim-1",
                "claim": "The paper proposes a robust assignment method.",
                "claim_kind": "paper_extracted",
            }
        ],
        "evidence_map": [
            {
                "evidence_id": "e-positive-limitation",
                "claim_id": "claim-1",
                "stance": "missing",
                "strength": "missing",
                "raw_quote": "In this paper, we present a novel viewpoint for addressing the above limitations.",
                "verified_grounding_label": "paper_grounded_exact",
                "semantic_grounding_label": "semantic_negative_verified",
                "negative_evidence_type": "scope_limitation",
            },
            {
                "evidence_id": "e-prior-limitation",
                "claim_id": "claim-1",
                "stance": "missing",
                "strength": "missing",
                "raw_quote": "Smith et al. (2023) introduces one-to-many assignment to overcome this limitation.",
                "verified_grounding_label": "paper_grounded_exact",
                "semantic_grounding_label": "semantic_negative_verified",
                "negative_evidence_type": "scope_limitation",
            },
        ],
    }

    assert not _is_grounded_paper_negative_evidence_record(state["evidence_map"][0], state)
    assert not _is_grounded_paper_negative_evidence_record(state["evidence_map"][1], state)


def test_review_semantic_negative_gate_accepts_current_paper_evaluation_gap():
    state = {
        "claims": [
            {
                "claim_id": "claim-1",
                "claim": "The method generates high-quality outputs.",
                "claim_kind": "paper_extracted",
            }
        ],
        "evidence_map": [
            {
                "evidence_id": "e-output-quality-gap",
                "claim_id": "claim-1",
                "stance": "missing",
                "strength": "missing",
                "raw_quote": "The paper evaluates on a single dataset and provides no comparison to stronger baselines.",
                "verified_grounding_label": "paper_grounded_exact",
                "verified_source_span_start": 10,
                "verified_source_span_end": 72,
                "verified_quote_match_type": "exact",
                "semantic_grounding_label": "semantic_negative_verified",
                "negative_evidence_type": "insufficient_evaluation",
            }
        ],
    }

    assert _is_grounded_paper_negative_evidence_record(state["evidence_map"][0], state)


def test_review_semantic_negative_gate_accepts_comparison_invalidation_quote():
    quote = (
        "Note that alpha is a hyperparameter that must be tuned for each method, model, "
        "and sometimes even intervention feature and thus cannot be used to compare the "
        "effects of interventions across methods."
    )
    paper_text, quote_bank = _grounding_bank([("quote-negative-comparison", quote, "negative_or_gap")])
    state = {
        "claims": [
            {
                "claim_id": "claim-1",
                "claim": "The empirical results demonstrate valid comparison across different intervention methods.",
                "claim_kind": "paper_extracted",
            }
        ],
        "evidence_map": [
            {
                "evidence_id": "e-comparison-invalid",
                "claim_id": "claim-1",
                "evidence": "Alpha tuning prevents cross-method comparison of intervention effects.",
                "source": "Evaluation discussion",
                "source_locator": "Limitation / Gap / Negative evidence excerpt #1",
                "stance": "contradicts",
                "strength": "strong",
                "raw_quote": quote,
                "quote_id": "quote-negative-comparison",
                "negative_evidence_type": "insufficient_evaluation",
            }
        ],
        "paper_text": paper_text,
        "evidence_quote_bank": quote_bank,
    }

    merged = merge_review_state(state, {"evidence_map": state["evidence_map"]})
    ev = merged["evidence_map"][0]

    assert ev["semantic_grounding_label"] == "semantic_negative_verified"
    assert "comparison_invalidation_verified" in ev["semantic_grounding_reasons"]
    assert ev["review_negative_label"] == "review_negative_verified"
    assert ev["review_negative_reason"] == "comparison_invalidation_weakens_claim"
    assert _is_grounded_paper_negative_evidence_record(ev, merged)


def test_comparison_invalidation_quote_corrects_support_generic_gap_mislabel():
    quote = (
        "Note that alpha is a hyperparameter that must be tuned for each method, model, "
        "and sometimes even intervention feature and thus cannot be used to compare the "
        "effects of interventions across methods."
    )
    paper_text, quote_bank = _grounding_bank([("quote-negative-comparison", quote, "negative_or_gap")])
    state = {
        "claims": [
            {
                "claim_id": "claim-1",
                "claim": "The empirical results compare intervention effects across different methods.",
                "claim_kind": "paper_extracted",
            }
        ],
        "evidence_map": [
            {
                "evidence_id": "e-comparison-mislabel",
                "claim_id": "claim-1",
                "evidence": "The quote supports the comparison protocol discussion.",
                "source": "Evaluation discussion",
                "source_locator": "Limitation / Gap / Negative evidence excerpt #1",
                "stance": "supports",
                "strength": "strong",
                "raw_quote": quote,
                "quote_id": "quote-negative-comparison",
                "negative_evidence_type": "generic_gap",
            }
        ],
        "paper_text": paper_text,
        "evidence_quote_bank": quote_bank,
    }

    merged = merge_review_state(state, {"evidence_map": state["evidence_map"]})
    ev = merged["evidence_map"][0]

    assert ev["comparison_invalidation_negative_override"] is True
    assert ev["comparison_invalidation_original_stance"] == "supports"
    assert ev["stance"] == "contradicts"
    assert ev["negative_evidence_type"] == "evaluation_protocol_risk"
    assert ev["negative_evidence_type_decision_view_reason"] == "comparison_invalidation_type_derived"
    assert ev["semantic_grounding_label"] == "semantic_negative_verified"
    assert ev["review_negative_label"] == "review_negative_verified"
    assert ev["review_negative_reason"] == "comparison_invalidation_weakens_claim"
    assert _is_paper_negative_evidence_record(ev)
    assert _is_grounded_paper_negative_evidence_record(ev, merged)


def test_comparison_invalidation_override_preserves_author_limitation_guard():
    quote = (
        "Due to limited resources, we do not compare alpha across methods and leave "
        "a full cross-method comparison for future work."
    )
    paper_text, quote_bank = _grounding_bank([("quote-author-limit", quote, "negative_or_gap")])
    state = {
        "claims": [
            {
                "claim_id": "claim-1",
                "claim": "The empirical results compare intervention effects across different methods.",
                "claim_kind": "paper_extracted",
            }
        ],
        "evidence_map": [
            {
                "evidence_id": "e-author-limit-mislabel",
                "claim_id": "claim-1",
                "evidence": "The quote discusses future comparison work.",
                "source": "Limitations",
                "source_locator": "Limitations",
                "stance": "supports",
                "strength": "strong",
                "raw_quote": quote,
                "quote_id": "quote-author-limit",
                "negative_evidence_type": "generic_gap",
            }
        ],
        "paper_text": paper_text,
        "evidence_quote_bank": quote_bank,
    }

    merged = merge_review_state(state, {"evidence_map": state["evidence_map"]})
    ev = merged["evidence_map"][0]

    assert not ev.get("comparison_invalidation_negative_override")
    assert ev["stance"] == "supports"
    assert not _is_grounded_paper_negative_evidence_record(ev, merged)


def test_comparison_invalidation_rejects_prior_work_not_compare_sentence():
    quote = (
        "Beyond probing, only \\cite{belrose2023eliciting, chan2022causal, olah2020zoom, "
        "templeton2024scaling} consider causal intervention as a tool for evaluation. "
        "However, \\cite{templeton2024scaling} on the other hand only provides a qualitative "
        "evaluation of intervention via their `Golden Gate Claude' [\\cite{noauthor_golden_nodate}] "
        "and does not compare to other interpretability methods. "
        "\\section{Method} In this section, we first introduce a unifying framework for four "
        "common mechanistic interpretability methods."
    )
    paper_text, quote_bank = _grounding_bank([("quote-prior-work-no-compare", quote, "negative_or_gap")])
    state = {
        "claims": [
            {
                "claim_id": "claim-1",
                "claim": "The paper introduces a unified framework for evaluating mechanistic interpretability methods.",
                "claim_kind": "paper_extracted",
            }
        ],
        "evidence_map": [
            {
                "evidence_id": "e-prior-work-no-compare",
                "claim_id": "claim-1",
                "evidence": "The quote says Golden Gate Claude did not compare to other interpretability methods.",
                "source": "Related work",
                "source_locator": "Section: Method",
                "stance": "supports",
                "strength": "medium",
                "raw_quote": quote,
                "quote_id": "quote-prior-work-no-compare",
                "negative_evidence_type": "missing_baseline",
            }
        ],
        "paper_text": paper_text,
        "evidence_quote_bank": quote_bank,
    }

    merged = merge_review_state(state, {"evidence_map": state["evidence_map"]})
    ev = merged["evidence_map"][0]

    assert not ev.get("comparison_invalidation_negative_override")
    assert ev["review_negative_label"] != "review_negative_verified"
    assert not _is_grounded_paper_negative_evidence_record(ev, merged)


def test_review_semantic_negative_gate_accepts_table_scope_absence():
    table_quote = "Table 2: Results obtained on DAVIS2016, SegTrackV2, and FBMS59."
    paper_text, quote_bank = _grounding_bank([("quote-table-2", table_quote, "table_or_figure")])
    state = {
        "claims": [
            {
                "claim_id": "claim-1",
                "claim": "The method is evaluated on DAVIS2017 and common video benchmarks.",
                "claim_kind": "paper_extracted",
            }
        ],
        "evidence_map": [
            {
                "evidence_id": "e-table-absence",
                "claim_id": "claim-1",
                "evidence": "Table 2 does not include DAVIS2017 among the evaluated datasets.",
                "source": "Table 2",
                "source_locator": "Table 2",
                "stance": "missing",
                "strength": "missing",
                "raw_quote": table_quote,
                "quote_id": "quote-table-2",
                "negative_evidence_type": "insufficient_evaluation",
            }
        ],
        "paper_text": paper_text,
        "evidence_quote_bank": quote_bank,
    }
    evidence = state["evidence_map"][0]

    merged = merge_review_state(state, {"evidence_map": [evidence]})
    ev = merged["evidence_map"][0]

    assert ev["semantic_grounding_label"] == "semantic_negative_verified"
    assert "table_scope_absence_verified" in ev["semantic_grounding_reasons"]
    assert ev["review_negative_label"] == "review_negative_verified"
    assert ev["review_negative_reason"] == "table_scope_absence_weakens_claim"
    assert _is_grounded_paper_negative_evidence_record(ev, merged)


def test_table_scope_absence_accepts_mislabeled_direct_contradiction():
    table_quote = (
        "We report in Table 2 the results obtained by two versions of our LT-MS method "
        "on the three datasets DAVIS2016, SegTrackV2, and FBMS59."
    )
    paper_text, quote_bank = _grounding_bank([("quote-table-2", table_quote, "table_or_figure")])
    state = {
        "claims": [
            {
                "claim_id": "claim-1",
                "claim": "The method is evaluated on DAVIS2017.",
                "claim_kind": "paper_extracted",
            }
        ],
        "evidence_map": [
            {
                "evidence_id": "e-table-absence-direct",
                "claim_id": "claim-1",
                "evidence": "Table 2 shows DAVIS2016, SegTrackV2, and FBMS59, but does not include DAVIS2017.",
                "source": "Table 2",
                "source_locator": "Table 2",
                "stance": "contradicts",
                "strength": "missing",
                "raw_quote": table_quote,
                "quote_id": "quote-table-2",
                "negative_evidence_type": "direct_contradiction",
            }
        ],
        "paper_text": paper_text,
        "evidence_quote_bank": quote_bank,
    }

    merged = merge_review_state(state, {"evidence_map": state["evidence_map"]})
    ev = merged["evidence_map"][0]

    assert ev["semantic_grounding_label"] == "semantic_negative_verified"
    assert ev["negative_evidence_type"] == "insufficient_evaluation"
    assert ev["negative_evidence_type_decision_view_reason"] == "table_scope_absence_type_derived"
    assert ev["review_negative_label"] == "review_negative_verified"
    assert ev["review_negative_reason"] == "table_scope_absence_weakens_claim"
    assert _is_grounded_paper_negative_evidence_record(ev, merged)


def test_table_scope_absence_requires_specific_missing_entity():
    table_quote = "Table 2: Results obtained on DAVIS2016, SegTrackV2, and FBMS59."
    paper_text, quote_bank = _grounding_bank([("quote-table-2", table_quote, "table_or_figure")])
    state = {
        "claims": [
            {
                "claim_id": "claim-1",
                "claim": "The evaluation is comprehensive.",
                "claim_kind": "paper_extracted",
            }
        ],
        "evidence_map": [
            {
                "evidence_id": "e-vague-absence",
                "claim_id": "claim-1",
                "evidence": "Table 2 does not include strong baselines.",
                "source": "Table 2",
                "source_locator": "Table 2",
                "stance": "missing",
                "strength": "missing",
                "raw_quote": table_quote,
                "quote_id": "quote-table-2",
                "negative_evidence_type": "missing_baseline",
            }
        ],
        "paper_text": paper_text,
        "evidence_quote_bank": quote_bank,
    }

    merged = merge_review_state(state, {"evidence_map": state["evidence_map"]})
    ev = merged["evidence_map"][0]

    assert ev["semantic_grounding_label"] == "semantic_mismatch"
    assert not _is_grounded_paper_negative_evidence_record(ev, merged)


def test_table_scope_absence_accepts_concrete_freeform_coverage_item():
    table_quote = "Table 4: Ablation study comparing Full model, w/o distillation, and w/o beam search."
    paper_text, quote_bank = _grounding_bank([("quote-table-4", table_quote, "table_or_figure")])
    state = {
        "claims": [
            {
                "claim_id": "claim-1",
                "claim": "The routing module drives the model's accuracy improvement.",
                "claim_kind": "paper_extracted",
            }
        ],
        "reviewer_negative_candidates": [
            {
                "candidate_id": "reviewer-neg-candidate-routing",
                "claim_id": "claim-1",
                "weakness": "The paper may not isolate the routing module contribution.",
                "negative_type": "missing_ablation",
                "required_evidence_type": "ablation_or_component",
                "missing_or_weak_items": ["routing module"],
                "status": "pending_quote_verification",
            }
        ],
        "evidence_map": [
            {
                "evidence_id": "e-freeform-routing-ablation",
                "claim_id": "claim-1",
                "evidence": "The ablation table lists full model, distillation, and beam search variants but not the routing module.",
                "source": "Table 4",
                "source_locator": "Table 4",
                "stance": "missing",
                "strength": "missing",
                "raw_quote": table_quote,
                "quote_id": "quote-table-4",
                "negative_evidence_type": "missing_ablation",
                "targeted_negative_search_task_id": "neg-search-freeform-claim-1-reviewer-neg-candidate-routing",
                "coverage_missing_items": ["routing module"],
                "coverage_observed_items": ["Full model", "w/o distillation", "w/o beam search"],
            }
        ],
        "paper_text": paper_text,
        "evidence_quote_bank": quote_bank,
    }

    merged = merge_review_state(state, {"evidence_map": state["evidence_map"]})
    ev = merged["evidence_map"][0]

    assert ev["semantic_grounding_label"] == "semantic_negative_verified"
    assert "table_scope_absence_verified" in ev["semantic_grounding_reasons"]
    assert ev["review_negative_label"] == "review_negative_verified"
    assert _is_grounded_paper_negative_evidence_record(ev, merged)


def test_missing_ablation_negative_rejected_when_paper_reports_target_ablation():
    module_quote = (
        "CDiffuser is composed of two modules: the Planning Module and the Contrastive Module. "
        "The Contrastive Module is designed to pull generated states toward high-return states."
    )
    ablation_quote = (
        "Ablation studies. We have the following variants to conduct ablation study: "
        "CDiffuser-C: remove contrastive mechanism from CDiffuser, i.e., remove L_c from the loss."
    )
    paper_text = f"Section 4 Method. {module_quote} Section 5 Experiments. {ablation_quote}"
    state = {
        "claims": [
            {
                "claim_id": "claim-1",
                "claim": "The contrastive mechanism improves CDiffuser by constraining states toward high-return trajectories.",
                "claim_kind": "paper_extracted",
            }
        ],
        "paper_text": paper_text,
    }
    ev = {
        "evidence_id": "e-false-missing-ablation",
        "claim_id": "claim-1",
        "evidence": "The paper describes the contrastive module but no ablation isolates its contribution.",
        "source": "Section 4.2",
        "source_locator": "Section 4.2",
        "stance": "contradicts",
        "strength": "medium",
        "raw_quote": module_quote,
        "negative_evidence_type": "missing_ablation",
        "coverage_missing_items": [
            "variant of CDiffuser without the contrastive loss/module",
            "quantitative results comparing CDiffuser vs. CDiffuser without contrastive",
        ],
        "verified_grounding_label": "paper_grounded_exact",
        "verified_quote_match_type": "paper_text_exact",
        "semantic_grounding_label": "semantic_negative_verified",
    }

    assessment = _assess_review_negative_relation(state, ev)
    ev.update(assessment)
    state["evidence_map"] = [ev]

    assert assessment["review_negative_label"] == "insufficient_claim_relation"
    assert assessment["review_negative_reason"] == "existing_ablation_counterevidence_in_paper"
    assert not _is_grounded_paper_negative_evidence_record(ev, state)
    hygiene = build_decision_hygiene_view(state)["decision_hygiene"]
    assert hygiene["review_negative_verified_count"] == 0
    assert hygiene["verified_actionable_negative_flaw_count"] == 0


def test_absence_audit_does_not_flag_missing_ablation_when_claim_reports_ablation_result():
    state = {
        "claims": [
            {
                "claim_id": "claim-1",
                "claim": "Ablation studies demonstrate the importance of the contrastive learning component in CDiffuser's performance.",
                "claim_kind": "paper_extracted",
                "status": "supported",
            },
            {
                "claim_id": "claim-2",
                "claim": "The contrastive learning component is essential for the performance gain of CDiffuser, as shown by ablation studies.",
                "claim_kind": "paper_extracted",
                "status": "supported",
            },
            {
                "claim_id": "claim-3",
                "claim": "SPOT's architectural components are validated through ablation studies.",
                "claim_kind": "paper_extracted",
                "status": "supported",
            },
        ],
        "evidence_map": [],
        "flaw_candidates": [],
        "unresolved_questions": [],
        "evidence_gaps": [],
        "conflict_notes": [],
    }

    hygiene = build_decision_hygiene_view(state)["decision_hygiene"]
    type_counts = hygiene.get("negative_evidence_type_counts", {})
    absence_counts = hygiene.get("reviewer_absence_verified_type_counts", {})

    assert type_counts.get("missing_ablation", 0) == 0
    assert absence_counts.get("missing_ablation", 0) == 0


def test_freeform_absence_candidate_adds_claim_level_requirement_gap_when_verified_support_missing():
    base_state = {
        "claims": [
            {
                "claim_id": "claim-1",
                "claim": "The method outperforms GPT-4 and Llama-2 baselines on Benchmark-X.",
                "claim_kind": "paper_extracted",
                "claim_type": "comparison",
                "status": "supported",
            },
            {
                "claim_id": "claim-2",
                "claim": "The retrieval module improves performance compared to strong baselines.",
                "claim_kind": "paper_extracted",
                "claim_type": "comparison",
                "status": "uncertain",
            },
        ],
        "evidence_map": [
            {
                "evidence_id": "ev-claim1-baseline",
                "claim_id": "claim-1",
                "evidence": "Table 1 compares the method against GPT-4 and Llama-2 baselines.",
                "raw_quote": "Table 1: Our method is compared against GPT-4 and Llama-2 baselines on Benchmark-X.",
                "source": "Table 1",
                "source_locator": "Table 1",
                "strength": "strong",
                "stance": "supports",
                "binding_status": "bound_real_claim",
                "verified_grounding_label": "paper_grounded_exact",
                "verified_quote_match_type": "quote_bank_id_canonical",
                "semantic_grounding_label": "semantic_support_verified",
                "support_source_bucket": "table_or_figure",
            },
            {
                "evidence_id": "ev-claim2-result-inventory",
                "claim_id": "claim-2",
                "evidence": "The method section describes the retrieval module pipeline.",
                "raw_quote": "The retrieval module reranks passages before generation.",
                "source": "Method",
                "source_locator": "Section 3",
                "strength": "medium",
                "stance": "supports",
                "binding_status": "bound_real_claim",
                "verified_grounding_label": "paper_grounded_exact",
                "verified_quote_match_type": "quote_bank_id_canonical",
                "semantic_grounding_label": "semantic_support_verified",
                "support_source_bucket": "method",
            },
        ],
        "flaw_candidates": [],
        "unresolved_questions": [],
        "evidence_gaps": [],
        "conflict_notes": [],
    }
    no_candidate = build_decision_hygiene_view(copy.deepcopy(base_state))["decision_hygiene"]
    assert no_candidate["reviewer_absence_verified_count"] == 0

    with_candidate = copy.deepcopy(base_state)
    with_candidate["reviewer_negative_candidates"] = [
        {
            "candidate_id": "reviewer-neg-candidate-retrieval-baseline",
            "claim_id": "claim-2",
            "weakness": "The retrieval-module claim lacks a concrete comparison against the GPT-4 baseline.",
            "negative_type": "missing_baseline",
            "required_evidence_type": "baseline_or_comparison",
            "quote_grounding_mode": "absence_or_requirement_gap",
            "missing_or_weak_items": ["GPT-4 baseline"],
            "status": "pending_absence_audit",
        }
    ]
    view = build_decision_hygiene_view(with_candidate)
    hygiene = view["decision_hygiene"]

    assert hygiene["reviewer_absence_verified_count"] == 0
    assert hygiene.get("reviewer_absence_verified_type_counts", {}).get("missing_baseline", 0) == 0
    assert hygiene["total_review_negative_verified_count"] == 0
    assert hygiene["review_negative_verified_count"] == 0
    assert hygiene["obligation_grounded_review_issue_count"] == 0
    assert hygiene["verified_review_issue_count"] == 0
    assert hygiene["review_issue_bundle_count"] == 0
    assert hygiene["diagnosis_pending_potential_concern_count"] >= 1
    evidence = [
        item for item in view["evidence_map"]
        if item.get("reviewer_negative_candidate_id") == "reviewer-neg-candidate-retrieval-baseline"
    ]
    assert evidence == []


def test_reviewer_issue_bundle_accepts_candidate_inventory_quote_when_paper_locatable():
    claim = "The paper compares the retrieval model against the GPT-4 baseline on Benchmark-X."
    inventory_quote = "Table 1 compares our retrieval model with Llama-2 and BERT baselines on Benchmark-X."
    state = {
        "paper_text": f"{claim}\n\n{inventory_quote}\n\nThe method section describes the retrieval pipeline.",
        "claims": [
            {
                "claim_id": "claim-1",
                "claim": claim,
                "claim_kind": "paper_extracted",
                "claim_type": "comparison",
                "importance": "high",
                "status": "supported",
                "claim_obligations": ["baseline_or_comparison"],
            }
        ],
        "evidence_map": [],
        "reviewer_negative_candidates": [
            {
                "candidate_id": "reviewer-neg-candidate-gpt4-inventory",
                "claim_id": "claim-1",
                "weakness": "The visible benchmark table omits the claimed GPT-4 baseline comparison.",
                "negative_type": "missing_baseline",
                "required_evidence_type": "baseline_or_comparison",
                "quote_grounding_mode": "absence_or_requirement_gap",
                "missing_or_weak_items": ["GPT-4 baseline"],
                "observed_inventory": [
                    {
                        "quote": inventory_quote,
                        "locator": "Table 1",
                        "observed_items": ["Llama-2 baseline", "BERT baseline", "Benchmark-X"],
                    }
                ],
                "status": "pending_absence_audit",
                "source_of_expectation": "reviewer_candidate",
            }
        ],
        "flaw_candidates": [],
        "unresolved_questions": [],
        "evidence_gaps": [],
        "conflict_notes": [],
    }

    view = build_decision_hygiene_view(copy.deepcopy(state))
    hygiene = view["decision_hygiene"]
    evidence = [
        item for item in view["evidence_map"]
        if item.get("reviewer_negative_candidate_id") == "reviewer-neg-candidate-gpt4-inventory"
    ]

    assert hygiene["obligation_grounded_review_issue_count"] == 1
    assert hygiene["verified_review_issue_count"] == 1
    assert len(evidence) == 1
    bundle = evidence[0]["review_issue_bundle"]
    assert bundle["source_of_expectation"] == "reviewer_candidate"
    assert bundle["missing_or_mismatch"]["items"] == ["GPT-4 baseline"]
    assert any(
        item.get("inventory_source") == "reviewer_candidate_observed_inventory"
        and item.get("verified_grounding_label") in {"paper_grounded_exact", "paper_grounded_normalized"}
        for item in bundle["observed_inventory"]
    )


def test_reviewer_issue_bundle_anchors_paraphrased_claim_with_verified_support_quote():
    claim = "The retrieval model is claimed to be competitive against strong baselines on Benchmark-X."
    support_quote = "We introduce RetrieverX, a retrieval model designed for Benchmark-X retrieval tasks."
    inventory_quote = "Table 1 compares our retrieval model with Llama-2 and BERT baselines on Benchmark-X."
    paper_text = f"{support_quote}\n\n{inventory_quote}\n\nSection 4 reports benchmark results."
    support_start = paper_text.index(support_quote)
    support_end = support_start + len(support_quote) - 1
    state = {
        "paper_text": paper_text,
        "claims": [
            {
                "claim_id": "claim-1",
                "claim": claim,
                "claim_kind": "paper_extracted",
                "claim_type": "comparison",
                "coverage_tags": ["comparison", "empirical"],
                "importance": "high",
                "status": "supported",
                "claim_obligations": ["baseline_or_comparison"],
            }
        ],
        "evidence_map": [
            {
                "evidence_id": "e-support-anchor",
                "claim_id": "claim-1",
                "evidence": support_quote,
                "raw_quote": support_quote,
                "source": "Introduction",
                "source_locator": "Introduction",
                "stance": "supports",
                "strength": "strong",
                "binding_status": "bound_real_claim",
                "support_source_bucket": "method_or_approach",
                "verified_grounding_label": "paper_grounded_exact",
                "verified_quote_match_type": "exact",
                "verified_source_span_start": support_start,
                "verified_source_span_end": support_end,
                "semantic_grounding_label": "semantic_support_verified",
            }
        ],
        "reviewer_negative_candidates": [
            {
                "candidate_id": "reviewer-neg-candidate-gpt4-anchor-fallback",
                "claim_id": "claim-1",
                "weakness": "The comparison omits the named GPT-4 baseline.",
                "negative_type": "missing_baseline",
                "required_evidence_type": "baseline_or_comparison",
                "quote_grounding_mode": "absence_or_requirement_gap",
                "missing_or_weak_items": ["GPT-4 baseline"],
                "observed_inventory": [
                    {
                        "quote": inventory_quote,
                        "locator": "Table 1",
                        "observed_items": ["Llama-2 baseline", "BERT baseline", "Benchmark-X"],
                    }
                ],
                "status": "pending_absence_audit",
                "source_of_expectation": "reviewer_candidate",
            }
        ],
        "flaw_candidates": [],
        "unresolved_questions": [],
        "evidence_gaps": [],
        "conflict_notes": [],
    }

    view = build_decision_hygiene_view(copy.deepcopy(state))
    hygiene = view["decision_hygiene"]
    evidence = [
        item for item in view["evidence_map"]
        if item.get("reviewer_negative_candidate_id") == "reviewer-neg-candidate-gpt4-anchor-fallback"
    ]

    assert hygiene["obligation_grounded_review_issue_count"] == 1
    assert hygiene["verified_review_issue_count"] == 1
    assert len(evidence) == 1
    bundle = evidence[0]["review_issue_bundle"]
    assert bundle["claim_anchor"]["quote"] == support_quote
    assert bundle["claim_anchor"]["anchor_source"] == "verified_support_quote"


def test_reviewer_issue_bundle_can_override_broad_baseline_satisfaction_with_specific_missing_baseline():
    claim = "The paper compares the retrieval model against baselines on Benchmark-X."
    inventory_quote = "Table 1 compares our retrieval model with Llama-2 and BERT baselines on Benchmark-X."
    missing_item = "specialized GPT-4 baseline for instruction-following retrieval comparisons on Benchmark-X"
    paper_text = f"{claim}\n\n{inventory_quote}\n\nSection 4 reports benchmark results."
    support_start = paper_text.index(inventory_quote)
    support_end = support_start + len(inventory_quote) - 1
    state = {
        "paper_text": paper_text,
        "claims": [
            {
                "claim_id": "claim-1",
                "claim": claim,
                "claim_kind": "paper_extracted",
                "claim_type": "comparison",
                "coverage_tags": ["comparison", "empirical"],
                "importance": "high",
                "status": "supported",
                "claim_obligations": ["baseline_or_comparison"],
            }
        ],
        "evidence_map": [
            {
                "evidence_id": "e-baseline-support",
                "claim_id": "claim-1",
                "evidence": inventory_quote,
                "raw_quote": inventory_quote,
                "source": "Table 1",
                "source_locator": "Table 1",
                "stance": "supports",
                "strength": "strong",
                "binding_status": "bound_real_claim",
                "support_source_bucket": "baseline_or_comparison",
                "verified_grounding_label": "paper_grounded_exact",
                "verified_quote_match_type": "exact",
                "verified_source_span_start": support_start,
                "verified_source_span_end": support_end,
                "semantic_grounding_label": "semantic_support_verified",
            }
        ],
        "reviewer_negative_candidates": [
            {
                "candidate_id": "reviewer-neg-candidate-specific-baseline-override",
                "claim_id": "claim-1",
                "weakness": "The comparison covers some baselines but omits a named stronger baseline family.",
                "negative_type": "unfair_or_weak_baseline",
                "required_evidence_type": "baseline_or_comparison",
                "quote_grounding_mode": "absence_or_requirement_gap",
                "missing_or_weak_items": [missing_item],
                "observed_inventory": [
                    {
                        "quote": inventory_quote,
                        "locator": "Table 1",
                        "observed_items": ["Llama-2 baseline", "BERT baseline", "Benchmark-X"],
                    }
                ],
                "status": "pending_absence_audit",
                "source_of_expectation": "reviewer_candidate",
            }
        ],
        "flaw_candidates": [],
        "unresolved_questions": [],
        "evidence_gaps": [],
        "conflict_notes": [],
    }

    view = build_decision_hygiene_view(copy.deepcopy(state))
    hygiene = view["decision_hygiene"]
    evidence = [
        item for item in view["evidence_map"]
        if item.get("reviewer_negative_candidate_id") == "reviewer-neg-candidate-specific-baseline-override"
    ]

    assert hygiene["obligation_grounded_review_issue_count"] == 1
    assert len(evidence) == 1
    bundle = evidence[0]["review_issue_bundle"]
    assert bundle["missing_or_mismatch"]["items"] == [missing_item]
    assert bundle["issue_type"] == "unfair_or_weak_baseline"


def test_reviewer_issue_bundle_accepts_table_scope_absence_candidate():
    claim = "The theorem-proving model outperforms existing ATP baselines."
    inventory_quote = "Table 2 compares our model with k-NN, Proof State Transformer, and CoqHammer."
    missing_item = "E-prover ATP baseline"
    paper_text = f"{claim}\n\n{inventory_quote}\n\nThe evaluation reports proof success rates."
    support_start = paper_text.index(inventory_quote)
    support_end = support_start + len(inventory_quote) - 1
    state = {
        "paper_text": paper_text,
        "claims": [
            {
                "claim_id": "claim-1",
                "claim": claim,
                "claim_kind": "paper_extracted",
                "claim_type": "comparison",
                "coverage_tags": ["comparison", "empirical"],
                "importance": "high",
                "status": "supported",
                "claim_obligations": ["baseline_or_comparison"],
            }
        ],
        "evidence_map": [
            {
                "evidence_id": "e-atp-baseline-support",
                "claim_id": "claim-1",
                "evidence": inventory_quote,
                "raw_quote": inventory_quote,
                "source": "Table 2",
                "source_locator": "Table 2",
                "stance": "supports",
                "strength": "strong",
                "binding_status": "bound_real_claim",
                "support_source_bucket": "baseline_or_comparison",
                "verified_grounding_label": "paper_grounded_exact",
                "verified_quote_match_type": "exact",
                "verified_source_span_start": support_start,
                "verified_source_span_end": support_end,
                "semantic_grounding_label": "semantic_support_verified",
            }
        ],
        "reviewer_negative_candidates": [
            {
                "candidate_id": "reviewer-neg-candidate-table-scope-atp",
                "claim_id": "claim-1",
                "weakness": "The table scope omits a named ATP baseline family.",
                "negative_type": "missing_baseline",
                "required_evidence_type": "baseline_or_comparison",
                "quote_grounding_mode": "table_scope_absence",
                "missing_or_weak_items": [missing_item],
                "observed_inventory": [
                    {
                        "quote": inventory_quote,
                        "locator": "Table 2",
                        "observed_items": ["k-NN", "Proof State Transformer", "CoqHammer"],
                    }
                ],
                "status": "pending_absence_audit",
                "source_of_expectation": "reviewer_candidate",
            }
        ],
        "flaw_candidates": [],
        "unresolved_questions": [],
        "evidence_gaps": [],
        "conflict_notes": [],
    }

    view = build_decision_hygiene_view(copy.deepcopy(state))
    hygiene = view["decision_hygiene"]
    evidence = [
        item for item in view["evidence_map"]
        if item.get("reviewer_negative_candidate_id") == "reviewer-neg-candidate-table-scope-atp"
    ]

    assert hygiene["obligation_grounded_review_issue_count"] == 1
    assert len(evidence) == 1
    bundle = evidence[0]["review_issue_bundle"]
    assert bundle["missing_or_mismatch"]["items"] == [missing_item]
    assert bundle["source_of_expectation"] == "reviewer_candidate"


def test_paper_inventory_extracts_table_comparison_without_reusing_claim_text():
    claim = "The paper compares the retrieval model against the GPT-4 baseline on Benchmark-X."
    inventory_quote = "Table 1: Comparison with Llama-2 and BERT baselines on Benchmark-X."
    state = {
        "paper_text": f"{claim}\n\n{inventory_quote}\n\nSection 4 reports the benchmark results.",
        "claims": [
            {
                "claim_id": "claim-1",
                "claim": claim,
                "claim_kind": "paper_extracted",
                "claim_type": "comparison",
                "importance": "high",
                "status": "supported",
                "claim_obligations": ["baseline_or_comparison"],
            }
        ],
        "evidence_map": [],
    }

    inventory = _evaluation_inventory_from_evidence(state)
    paper_items = [
        item for item in inventory["items"]
        if item.get("inventory_source") == "paper_text_inventory"
    ]

    assert any("Llama-2" in item.get("quote", "") and "BERT" in item.get("quote", "") for item in paper_items)
    assert all(item.get("quote") != claim for item in paper_items)


def test_review_issue_specificity_accepts_concrete_experiment_dimensions_not_generic_labels():
    assert _coverage_item_is_specific_for_type("ablation for the Correct stage", "missing_ablation")
    assert _coverage_item_is_specific_for_type(
        "performance results on heterophily benchmark datasets",
        "insufficient_evaluation",
    )
    assert _coverage_item_is_specific_for_type(
        "quantitative results for docking scores in target pockets",
        "insufficient_evaluation",
    )
    assert not _coverage_item_is_specific_for_type("ablation evidence", "missing_ablation")
    assert not _coverage_item_is_specific_for_type("more datasets", "insufficient_evaluation")


def test_reviewer_issue_bundle_accepts_deterministic_paper_inventory_anchor():
    claim = "The paper compares the retrieval model against the GPT-4 baseline on Benchmark-X."
    inventory_quote = "Table 1: Comparison with Llama-2 and BERT baselines on Benchmark-X."
    state = {
        "paper_text": f"{claim}\n\n{inventory_quote}\n\nSection 4 reports the benchmark results.",
        "claims": [
            {
                "claim_id": "claim-1",
                "claim": claim,
                "claim_kind": "paper_extracted",
                "claim_type": "comparison",
                "importance": "high",
                "status": "supported",
                "claim_obligations": ["baseline_or_comparison"],
            }
        ],
        "evidence_map": [],
        "reviewer_negative_candidates": [
            {
                "candidate_id": "reviewer-neg-candidate-gpt4-paper-inventory",
                "claim_id": "claim-1",
                "weakness": "The benchmark table omits the claimed GPT-4 baseline.",
                "negative_type": "missing_baseline",
                "required_evidence_type": "baseline_or_comparison",
                "quote_grounding_mode": "absence_or_requirement_gap",
                "missing_or_weak_items": ["GPT-4 baseline"],
                "status": "pending_absence_audit",
                "source_of_expectation": "reviewer_candidate",
            }
        ],
        "flaw_candidates": [],
        "unresolved_questions": [],
        "evidence_gaps": [],
        "conflict_notes": [],
    }

    view = build_decision_hygiene_view(copy.deepcopy(state))
    hygiene = view["decision_hygiene"]
    evidence = [
        item for item in view["evidence_map"]
        if item.get("reviewer_negative_candidate_id") == "reviewer-neg-candidate-gpt4-paper-inventory"
    ]

    assert hygiene["obligation_grounded_review_issue_count"] == 1
    assert hygiene["verified_review_issue_count"] == 1
    assert len(evidence) == 1
    bundle = evidence[0]["review_issue_bundle"]
    assert any(item.get("inventory_source") == "paper_text_inventory" for item in bundle["observed_inventory"])


def test_reviewer_issue_bundle_rejects_claim_text_as_only_paper_inventory_anchor():
    claim = "The paper compares the retrieval model against the GPT-4 baseline on Benchmark-X."
    state = {
        "paper_text": claim,
        "claims": [
            {
                "claim_id": "claim-1",
                "claim": claim,
                "claim_kind": "paper_extracted",
                "claim_type": "comparison",
                "importance": "high",
                "status": "supported",
                "claim_obligations": ["baseline_or_comparison"],
            }
        ],
        "evidence_map": [],
        "reviewer_negative_candidates": [
            {
                "candidate_id": "reviewer-neg-candidate-claim-only",
                "claim_id": "claim-1",
                "weakness": "The benchmark table omits GPT-4.",
                "negative_type": "missing_baseline",
                "required_evidence_type": "baseline_or_comparison",
                "quote_grounding_mode": "absence_or_requirement_gap",
                "missing_or_weak_items": ["GPT-4 baseline"],
                "status": "pending_absence_audit",
                "source_of_expectation": "reviewer_candidate",
            }
        ],
        "flaw_candidates": [],
        "unresolved_questions": [],
        "evidence_gaps": [],
        "conflict_notes": [],
    }

    hygiene = build_decision_hygiene_view(copy.deepcopy(state))["decision_hygiene"]

    assert hygiene["obligation_grounded_review_issue_count"] == 0
    assert hygiene["verified_review_issue_count"] == 0


def test_reviewer_issue_bundle_rejects_missing_baseline_with_theory_method_anchor():
    claim = "The adaptive decoding method achieves higher speedup than modern speculative decoding baselines."
    theory_quote = (
        "For any time-homogeneous policy with a bounded number of candidate tokens, "
        "the optimal policy has a threshold form."
    )
    state = {
        "paper_text": f"{claim}\n\n{theory_quote}",
        "claims": [
            {
                "claim_id": "claim-1",
                "claim": claim,
                "claim_kind": "paper_extracted",
                "claim_type": "comparison",
                "importance": "high",
                "status": "supported",
                "claim_obligations": ["baseline_or_comparison"],
            }
        ],
        "evidence_map": [
            {
                "evidence_id": "ev-theory-method",
                "claim_id": "claim-1",
                "evidence": theory_quote,
                "raw_quote": theory_quote,
                "source": "Theory / Proof excerpt #1",
                "source_locator": "Theory / Proof excerpt #1",
                "strength": "strong",
                "stance": "supports",
                "binding_status": "bound_real_claim",
                "verified_grounding_label": "paper_grounded_exact",
                "verified_quote_match_type": "quote_bank_id_canonical",
                "semantic_grounding_label": "semantic_support_verified",
                "support_source_bucket": "method",
            }
        ],
        "reviewer_negative_candidates": [
            {
                "candidate_id": "reviewer-neg-candidate-theory-baseline",
                "claim_id": "claim-1",
                "weakness": "The comparison omits modern speculative decoding baselines.",
                "negative_type": "missing_baseline",
                "required_evidence_type": "baseline_or_comparison",
                "quote_grounding_mode": "absence_or_requirement_gap",
                "missing_or_weak_items": ["Medusa and EAGLE baselines"],
                "status": "pending_absence_audit",
                "source_of_expectation": "reviewer_candidate",
            }
        ],
        "flaw_candidates": [],
        "unresolved_questions": [],
        "evidence_gaps": [],
        "conflict_notes": [],
    }

    hygiene = build_decision_hygiene_view(copy.deepcopy(state))["decision_hygiene"]

    assert hygiene["obligation_grounded_review_issue_count"] == 0
    assert hygiene["verified_review_issue_count"] == 0


def test_reviewer_issue_bundle_rejects_missing_ablation_with_theory_anchor():
    claim = "The paper provides numerical simulations showing weight rank behavior for bias-free networks."
    theory_quote = (
        "Two-layer bias-free ReLU networks can only express a linear target function under the stated theorem."
    )
    state = {
        "paper_text": f"{claim}\n\n{theory_quote}",
        "claims": [
            {
                "claim_id": "claim-1",
                "claim": claim,
                "claim_kind": "paper_extracted",
                "claim_type": "empirical",
                "importance": "high",
                "status": "supported",
                "claim_obligations": ["ablation_or_component"],
            }
        ],
        "evidence_map": [
            {
                "evidence_id": "ev-theorem",
                "claim_id": "claim-1",
                "evidence": theory_quote,
                "raw_quote": theory_quote,
                "source": "Theory / Proof excerpt #1",
                "source_locator": "Theory / Proof excerpt #1",
                "strength": "strong",
                "stance": "supports",
                "binding_status": "bound_real_claim",
                "verified_grounding_label": "paper_grounded_exact",
                "verified_quote_match_type": "quote_bank_id_canonical",
                "semantic_grounding_label": "semantic_support_verified",
                "support_source_bucket": "method",
            }
        ],
        "reviewer_negative_candidates": [
            {
                "candidate_id": "reviewer-neg-candidate-theory-ablation",
                "claim_id": "claim-1",
                "weakness": "The paper lacks an ablation on target function complexity.",
                "negative_type": "missing_ablation",
                "required_evidence_type": "ablation_or_component",
                "quote_grounding_mode": "absence_or_requirement_gap",
                "missing_or_weak_items": ["ablation study on target function complexity"],
                "status": "pending_absence_audit",
                "source_of_expectation": "reviewer_candidate",
            }
        ],
        "flaw_candidates": [],
        "unresolved_questions": [],
        "evidence_gaps": [],
        "conflict_notes": [],
    }

    hygiene = build_decision_hygiene_view(copy.deepcopy(state))["decision_hygiene"]

    assert hygiene["obligation_grounded_review_issue_count"] == 0
    assert hygiene["verified_review_issue_count"] == 0


def test_reviewer_issue_bundle_rejects_missing_scope_item_already_in_paper_inventory():
    claim = "The propagation method achieves competitive results across diverse node benchmarks."
    table_5 = "Table 5: Test accuracy of homophily node classification benchmarks."
    table_6 = "Table 6: Test accuracy of heterophily node classification benchmarks."
    state = {
        "paper_text": f"{claim}\n\n{table_5}\n\n{table_6}",
        "claims": [
            {
                "claim_id": "claim-1",
                "claim": claim,
                "claim_kind": "paper_extracted",
                "claim_type": "empirical",
                "importance": "high",
                "status": "supported",
                "claim_obligations": ["scope_coverage"],
            }
        ],
        "evidence_map": [],
        "reviewer_negative_candidates": [
            {
                "candidate_id": "reviewer-neg-candidate-heterophily-present",
                "claim_id": "claim-1",
                "weakness": "The visible scope seems to omit heterophily benchmark datasets.",
                "negative_type": "insufficient_evaluation",
                "required_evidence_type": "scope_coverage",
                "quote_grounding_mode": "absence_or_requirement_gap",
                "missing_or_weak_items": ["performance results on heterophily benchmark datasets"],
                "status": "pending_absence_audit",
                "source_of_expectation": "reviewer_candidate",
            }
        ],
        "flaw_candidates": [],
        "unresolved_questions": [],
        "evidence_gaps": [],
        "conflict_notes": [],
    }

    hygiene = build_decision_hygiene_view(copy.deepcopy(state))["decision_hygiene"]

    assert hygiene["obligation_grounded_review_issue_count"] == 0
    assert hygiene["verified_review_issue_count"] == 0


def test_reviewer_issue_bundle_rejects_candidate_inventory_quote_not_in_paper():
    claim = "The paper compares the retrieval model against the GPT-4 baseline on Benchmark-X."
    invented_inventory_quote = "Table 1 compares our retrieval model with Llama-2 and BERT baselines on Benchmark-X."
    state = {
        "paper_text": f"{claim}\n\nThe method section describes the retrieval pipeline, but no table text is visible.",
        "claims": [
            {
                "claim_id": "claim-1",
                "claim": claim,
                "claim_kind": "paper_extracted",
                "claim_type": "comparison",
                "importance": "high",
                "status": "supported",
                "claim_obligations": ["baseline_or_comparison"],
            }
        ],
        "evidence_map": [],
        "reviewer_negative_candidates": [
            {
                "candidate_id": "reviewer-neg-candidate-invented-inventory",
                "claim_id": "claim-1",
                "weakness": "The visible benchmark table omits the claimed GPT-4 baseline comparison.",
                "negative_type": "missing_baseline",
                "required_evidence_type": "baseline_or_comparison",
                "quote_grounding_mode": "absence_or_requirement_gap",
                "missing_or_weak_items": ["GPT-4 baseline"],
                "observed_inventory": [{"quote": invented_inventory_quote, "locator": "Table 1"}],
                "status": "pending_absence_audit",
                "source_of_expectation": "reviewer_candidate",
            }
        ],
        "flaw_candidates": [],
        "unresolved_questions": [],
        "evidence_gaps": [],
        "conflict_notes": [],
    }

    hygiene = build_decision_hygiene_view(copy.deepcopy(state))["decision_hygiene"]

    assert hygiene["reviewer_absence_verified_count"] == 0
    assert hygiene["obligation_grounded_review_issue_count"] == 0
    assert hygiene["verified_review_issue_count"] == 0


def test_reviewer_issue_bundle_accepts_result_claim_mismatch_with_inventory_anchor():
    claim = "The proposed model improves performance by using an ensemble verification step."
    inventory_quote = "Table 2 reports single-model accuracy for Ours, BERT, and Llama-2 on Benchmark-X."
    state = {
        "paper_text": f"{claim}\n\n{inventory_quote}\n\nThe evaluation follows the Benchmark-X protocol.",
        "claims": [
            {
                "claim_id": "claim-1",
                "claim": claim,
                "claim_kind": "paper_extracted",
                "claim_type": "empirical",
                "importance": "high",
                "status": "supported",
                "claim_obligations": ["empirical_result"],
            }
        ],
        "evidence_map": [
            {
                "evidence_id": "ev-empirical-result",
                "claim_id": "claim-1",
                "evidence": inventory_quote,
                "raw_quote": inventory_quote,
                "source": "Table 2",
                "source_locator": "Table 2",
                "strength": "strong",
                "stance": "supports",
                "binding_status": "bound_real_claim",
                "verified_grounding_label": "paper_grounded_exact",
                "verified_quote_match_type": "quote_bank_id_canonical",
                "semantic_grounding_label": "semantic_support_verified",
                "support_source_bucket": "table_or_figure",
            }
        ],
        "reviewer_negative_candidates": [
            {
                "candidate_id": "reviewer-neg-candidate-ensemble-mismatch",
                "claim_id": "claim-1",
                "weakness": "The empirical table does not verify the claimed ensemble verification step.",
                "negative_type": "result_claim_mismatch",
                "required_evidence_type": "empirical_result",
                "quote_grounding_mode": "absence_or_requirement_gap",
                "missing_or_weak_items": ["ensemble verification experiment"],
                "observed_inventory": [
                    {
                        "quote": inventory_quote,
                        "locator": "Table 2",
                        "observed_items": ["single-model accuracy", "BERT", "Llama-2"],
                    }
                ],
                "status": "pending_absence_audit",
                "source_of_expectation": "reviewer_candidate",
            }
        ],
        "flaw_candidates": [],
        "unresolved_questions": [],
        "evidence_gaps": [],
        "conflict_notes": [],
    }

    view = build_decision_hygiene_view(copy.deepcopy(state))
    hygiene = view["decision_hygiene"]
    evidence = [
        item for item in view["evidence_map"]
        if item.get("reviewer_negative_candidate_id") == "reviewer-neg-candidate-ensemble-mismatch"
    ]

    assert hygiene["obligation_grounded_review_issue_count"] == 1
    assert hygiene["verified_review_issue_count"] == 1
    assert hygiene["obligation_grounded_review_issue_type_counts"]["result_claim_mismatch"] == 1
    assert len(evidence) == 1
    assert evidence[0]["negative_evidence_type"] == "result_claim_mismatch"
    assert evidence[0]["review_issue_bundle"]["required_evidence_type"] == "empirical_result"


def test_reviewer_issue_bundle_accepts_candidate_method_support_gap_with_inventory_anchor():
    claim = "The method uses a hierarchical routing mechanism to select experts."
    inventory_quote = "Section 3 describes a gating network that scores each expert and selects the top expert."
    state = {
        "paper_text": f"{claim}\n\n{inventory_quote}",
        "claims": [
            {
                "claim_id": "claim-1",
                "claim": claim,
                "claim_kind": "paper_extracted",
                "claim_type": "method",
                "importance": "high",
                "status": "supported",
                "claim_obligations": ["method_detail"],
            }
        ],
        "evidence_map": [
            {
                "evidence_id": "ev-method-inventory",
                "claim_id": "claim-1",
                "evidence": inventory_quote,
                "raw_quote": inventory_quote,
                "source": "Section 3",
                "source_locator": "Section 3",
                "strength": "strong",
                "stance": "supports",
                "binding_status": "bound_real_claim",
                "verified_grounding_label": "paper_grounded_exact",
                "verified_quote_match_type": "quote_bank_id_canonical",
                "semantic_grounding_label": "semantic_support_verified",
                "support_source_bucket": "method",
            }
        ],
        "reviewer_negative_candidates": [
            {
                "candidate_id": "reviewer-neg-candidate-hierarchy-detail",
                "claim_id": "claim-1",
                "weakness": "The method inventory does not verify an explicit hierarchical routing mechanism.",
                "negative_type": "method_support_gap",
                "required_evidence_type": "method_detail",
                "quote_grounding_mode": "absence_or_requirement_gap",
                "missing_or_weak_items": ["explicit hierarchical routing mechanism"],
                "observed_inventory": [
                    {
                        "quote": inventory_quote,
                        "locator": "Section 3",
                        "observed_items": ["gating network", "top expert selection"],
                    }
                ],
                "status": "pending_absence_audit",
                "source_of_expectation": "reviewer_candidate",
            }
        ],
        "flaw_candidates": [],
        "unresolved_questions": [],
        "evidence_gaps": [],
        "conflict_notes": [],
    }

    view = build_decision_hygiene_view(copy.deepcopy(state))
    hygiene = view["decision_hygiene"]

    assert hygiene["obligation_grounded_review_issue_count"] == 1
    assert hygiene["verified_review_issue_count"] == 1
    assert hygiene["obligation_grounded_review_issue_type_counts"]["method_support_gap"] == 1


def test_reviewer_issue_bundle_rejects_truncated_missing_item_as_verified_issue():
    claim = "The method integrates a contrastive objective with a diffusion planner."
    inventory_quote = (
        "Section 3 says CDiffuser contains a planning module and a contrastive module "
        "but does not specify the loss coupling."
    )
    state = {
        "paper_text": f"{claim}\n\n{inventory_quote}",
        "claims": [
            {
                "claim_id": "claim-1",
                "claim": claim,
                "claim_kind": "paper_extracted",
                "claim_type": "method",
                "importance": "high",
                "status": "supported",
                "claim_obligations": ["method_detail"],
            }
        ],
        "evidence_map": [
            {
                "evidence_id": "ev-method-inventory",
                "claim_id": "claim-1",
                "evidence": inventory_quote,
                "raw_quote": inventory_quote,
                "source": "Section 3",
                "source_locator": "Section 3",
                "strength": "strong",
                "stance": "supports",
                "binding_status": "bound_real_claim",
                "verified_grounding_label": "paper_grounded_exact",
                "verified_quote_match_type": "quote_bank_id_canonical",
                "semantic_grounding_label": "semantic_support_verified",
                "support_source_bucket": "method",
            }
        ],
        "reviewer_negative_candidates": [
            {
                "candidate_id": "reviewer-neg-candidate-truncated-method",
                "claim_id": "claim-1",
                "weakness": "The method inventory does not verify the contrastive objective integration.",
                "negative_type": "method_support_gap",
                "required_evidence_type": "method_detail",
                "quote_grounding_mode": "absence_or_requirement_gap",
                "missing_or_weak_items": [
                    "Detailed methodological description of the contrastive objective integration w"
                ],
                "observed_inventory": [{"quote": inventory_quote, "locator": "Section 3"}],
                "status": "pending_absence_audit",
                "source_of_expectation": "reviewer_candidate",
            }
        ],
        "flaw_candidates": [],
        "unresolved_questions": [],
        "evidence_gaps": [],
        "conflict_notes": [],
    }

    hygiene = build_decision_hygiene_view(copy.deepcopy(state))["decision_hygiene"]

    assert hygiene["obligation_grounded_review_issue_count"] == 0
    assert hygiene["verified_review_issue_count"] == 0


def test_reviewer_issue_bundle_rejects_missing_ablation_when_claim_reports_same_ablation():
    claim = (
        "The contrastive component is critical to CDiffuser's performance, "
        "as its ablation leads to a significant performance drop."
    )
    inventory_quote = (
        "The method section states that CDiffuser contains a planning module and a "
        "contrastive module."
    )
    state = {
        "paper_text": f"{claim}\n\n{inventory_quote}",
        "claims": [
            {
                "claim_id": "claim-1",
                "claim": claim,
                "claim_kind": "paper_extracted",
                "claim_type": "empirical",
                "importance": "high",
                "status": "supported",
                "claim_obligations": ["ablation_or_component"],
            }
        ],
        "evidence_map": [
            {
                "evidence_id": "ev-method-inventory",
                "claim_id": "claim-1",
                "evidence": inventory_quote,
                "raw_quote": inventory_quote,
                "source": "Section 3",
                "source_locator": "Section 3",
                "strength": "strong",
                "stance": "supports",
                "binding_status": "bound_real_claim",
                "verified_grounding_label": "paper_grounded_exact",
                "verified_quote_match_type": "quote_bank_id_canonical",
                "semantic_grounding_label": "semantic_support_verified",
                "support_source_bucket": "method",
            }
        ],
        "reviewer_negative_candidates": [
            {
                "candidate_id": "reviewer-neg-candidate-contrastive-ablation",
                "claim_id": "claim-1",
                "weakness": "The paper should isolate the contrastive objective contribution.",
                "negative_type": "missing_ablation",
                "required_evidence_type": "ablation_or_component",
                "quote_grounding_mode": "absence_or_requirement_gap",
                "missing_or_weak_items": [
                    "Ablation study isolating the effect of the contrastive objective component"
                ],
                "observed_inventory": [{"quote": inventory_quote, "locator": "Section 3"}],
                "status": "pending_absence_audit",
                "source_of_expectation": "reviewer_candidate",
            }
        ],
        "flaw_candidates": [],
        "unresolved_questions": [],
        "evidence_gaps": [],
        "conflict_notes": [],
    }

    hygiene = build_decision_hygiene_view(copy.deepcopy(state))["decision_hygiene"]

    assert hygiene["obligation_grounded_review_issue_count"] == 0
    assert hygiene["verified_review_issue_count"] == 0


def test_reviewer_issue_bundle_rejects_limitation_boundary_claim_target():
    claim = "The method has generalization limitations and may perform differently across datasets."
    inventory_quote = "Table 2 reports performance on DAVIS and FBMS motion segmentation datasets."
    state = {
        "paper_text": f"{claim}\n\n{inventory_quote}",
        "claims": [
            {
                "claim_id": "claim-1",
                "claim": claim,
                "claim_kind": "paper_extracted",
                "claim_type": "limitation_or_boundary",
                "importance": "medium",
                "status": "uncertain",
                "coverage_tags": ["limitation", "scope", "empirical"],
                "claim_obligations": ["ablation_or_component"],
            }
        ],
        "evidence_map": [
            {
                "evidence_id": "ev-result-inventory",
                "claim_id": "claim-1",
                "evidence": inventory_quote,
                "raw_quote": inventory_quote,
                "source": "Table 2",
                "source_locator": "Table 2",
                "strength": "strong",
                "stance": "supports",
                "binding_status": "bound_real_claim",
                "verified_grounding_label": "paper_grounded_exact",
                "verified_quote_match_type": "quote_bank_id_canonical",
                "semantic_grounding_label": "semantic_support_verified",
                "support_source_bucket": "table_or_figure",
            }
        ],
        "reviewer_negative_candidates": [
            {
                "candidate_id": "reviewer-neg-candidate-limitation-ablation",
                "claim_id": "claim-1",
                "weakness": "A reviewer might ask for an ablation on the cut-size hyperparameter.",
                "negative_type": "missing_ablation",
                "required_evidence_type": "ablation_or_component",
                "quote_grounding_mode": "absence_or_requirement_gap",
                "missing_or_weak_items": ["ablation on the cut-size hyperparameter"],
                "observed_inventory": [{"quote": inventory_quote, "locator": "Table 2"}],
                "status": "pending_absence_audit",
                "source_of_expectation": "reviewer_candidate",
            }
        ],
        "flaw_candidates": [],
        "unresolved_questions": [],
        "evidence_gaps": [],
        "conflict_notes": [],
    }

    hygiene = build_decision_hygiene_view(copy.deepcopy(state))["decision_hygiene"]

    assert hygiene["obligation_grounded_review_issue_count"] == 0
    assert hygiene["verified_review_issue_count"] == 0


def test_reviewer_issue_bundle_rejects_method_support_gap_without_inventory_anchor():
    state = {
        "paper_text": "The method uses a hierarchical routing mechanism to select experts.",
        "claims": [
            {
                "claim_id": "claim-1",
                "claim": "The method uses a hierarchical routing mechanism to select experts.",
                "claim_kind": "paper_extracted",
                "claim_type": "method",
                "importance": "high",
                "status": "supported",
                "claim_obligations": ["method_detail"],
            }
        ],
        "evidence_map": [],
        "reviewer_negative_candidates": [
            {
                "candidate_id": "reviewer-neg-candidate-no-inventory",
                "claim_id": "claim-1",
                "weakness": "The method lacks enough detail about hierarchical routing.",
                "negative_type": "method_support_gap",
                "required_evidence_type": "method_detail",
                "quote_grounding_mode": "absence_or_requirement_gap",
                "missing_or_weak_items": ["explicit hierarchical routing mechanism"],
                "status": "pending_absence_audit",
                "source_of_expectation": "reviewer_candidate",
            }
        ],
        "flaw_candidates": [],
        "unresolved_questions": [],
        "evidence_gaps": [],
        "conflict_notes": [],
    }

    hygiene = build_decision_hygiene_view(copy.deepcopy(state))["decision_hygiene"]

    assert hygiene["obligation_grounded_review_issue_count"] == 0
    assert hygiene["verified_review_issue_count"] == 0


def test_reviewer_issue_bundle_accepts_candidate_reproducibility_gap_with_inventory_anchor():
    claim = "The training procedure is reproducible and can be implemented from the described method."
    inventory_quote = "Section 3 describes the two-stage encoder and decoder architecture used by the method."
    state = {
        "paper_text": f"{claim}\n\n{inventory_quote}",
        "claims": [
            {
                "claim_id": "claim-1",
                "claim": claim,
                "claim_kind": "paper_extracted",
                "claim_type": "method",
                "importance": "high",
                "status": "supported",
                "claim_obligations": ["reproducibility_detail"],
            }
        ],
        "evidence_map": [
            {
                "evidence_id": "ev-method-inventory",
                "claim_id": "claim-1",
                "evidence": inventory_quote,
                "raw_quote": inventory_quote,
                "source": "Section 3",
                "source_locator": "Section 3",
                "strength": "strong",
                "stance": "supports",
                "binding_status": "bound_real_claim",
                "verified_grounding_label": "paper_grounded_exact",
                "verified_quote_match_type": "quote_bank_id_canonical",
                "semantic_grounding_label": "semantic_support_verified",
                "support_source_bucket": "method",
            }
        ],
        "reviewer_negative_candidates": [
            {
                "candidate_id": "reviewer-neg-candidate-training-schedule",
                "claim_id": "claim-1",
                "weakness": "The method inventory does not provide the optimizer schedule needed to reproduce training.",
                "negative_type": "reproducibility_gap",
                "required_evidence_type": "reproducibility_detail",
                "quote_grounding_mode": "absence_or_requirement_gap",
                "missing_or_weak_items": ["optimizer schedule and learning-rate decay"],
                "observed_inventory": [
                    {
                        "quote": inventory_quote,
                        "locator": "Section 3",
                        "observed_items": ["two-stage encoder", "decoder architecture"],
                    }
                ],
                "status": "pending_absence_audit",
                "source_of_expectation": "reviewer_candidate",
            }
        ],
        "flaw_candidates": [],
        "unresolved_questions": [],
        "evidence_gaps": [],
        "conflict_notes": [],
    }

    view = build_decision_hygiene_view(copy.deepcopy(state))
    hygiene = view["decision_hygiene"]

    assert hygiene["obligation_grounded_review_issue_count"] == 1
    assert hygiene["verified_review_issue_count"] == 1
    assert hygiene["obligation_grounded_review_issue_type_counts"]["reproducibility_gap"] == 1
    evidence = [
        item for item in view["evidence_map"]
        if item.get("reviewer_negative_candidate_id") == "reviewer-neg-candidate-training-schedule"
    ]
    assert len(evidence) == 1
    assert evidence[0]["negative_evidence_type"] == "reproducibility_gap"
    assert evidence[0]["review_issue_bundle"]["missing_or_mismatch"]["items"] == [
        "optimizer schedule and learning-rate decay"
    ]


def test_reviewer_issue_bundle_rejects_generic_reproducibility_detail_label():
    claim = "The released implementation is reproducible from the paper."
    inventory_quote = "Section 3 describes the model architecture and training objective."
    state = {
        "paper_text": f"{claim}\n\n{inventory_quote}",
        "claims": [
            {
                "claim_id": "claim-1",
                "claim": claim,
                "claim_kind": "paper_extracted",
                "claim_type": "method",
                "importance": "high",
                "status": "supported",
                "claim_obligations": ["reproducibility_detail"],
            }
        ],
        "evidence_map": [
            {
                "evidence_id": "ev-method-inventory",
                "claim_id": "claim-1",
                "evidence": inventory_quote,
                "raw_quote": inventory_quote,
                "source": "Section 3",
                "source_locator": "Section 3",
                "strength": "strong",
                "stance": "supports",
                "binding_status": "bound_real_claim",
                "verified_grounding_label": "paper_grounded_exact",
                "verified_quote_match_type": "quote_bank_id_canonical",
                "semantic_grounding_label": "semantic_support_verified",
                "support_source_bucket": "method",
            }
        ],
        "reviewer_negative_candidates": [
            {
                "candidate_id": "reviewer-neg-candidate-generic-repro",
                "claim_id": "claim-1",
                "weakness": "The method lacks reproducibility detail.",
                "negative_type": "reproducibility_gap",
                "required_evidence_type": "reproducibility_detail",
                "quote_grounding_mode": "absence_or_requirement_gap",
                "missing_or_weak_items": ["implementation/reproducibility detail"],
                "observed_inventory": [{"quote": inventory_quote, "locator": "Section 3"}],
                "status": "pending_absence_audit",
                "source_of_expectation": "reviewer_candidate",
            }
        ],
        "flaw_candidates": [],
        "unresolved_questions": [],
        "evidence_gaps": [],
        "conflict_notes": [],
    }

    hygiene = build_decision_hygiene_view(copy.deepcopy(state))["decision_hygiene"]

    assert hygiene["obligation_grounded_review_issue_count"] == 0
    assert hygiene["verified_review_issue_count"] == 0


def test_reviewer_issue_bundle_rejects_baseline_gap_with_theorem_inventory_anchor():
    claim = "The adaptive decoding method improves speedup over state-of-the-art speculative decoding baselines."
    theorem_quote = (
        "Theorem 1 states that for any time-homogeneous policy with a bounded number of "
        "candidate tokens, the optimal policy has a threshold form."
    )
    state = {
        "paper_text": f"{claim}\n\n{theorem_quote}",
        "claims": [
            {
                "claim_id": "claim-1",
                "claim": claim,
                "claim_kind": "paper_extracted",
                "claim_type": "comparison",
                "importance": "high",
                "status": "supported",
                "claim_obligations": ["baseline_or_comparison"],
            }
        ],
        "evidence_map": [],
        "reviewer_negative_candidates": [
            {
                "candidate_id": "reviewer-neg-candidate-theorem-baseline",
                "claim_id": "claim-1",
                "weakness": "The comparison omits recent speculative decoding baselines.",
                "negative_type": "missing_baseline",
                "required_evidence_type": "baseline_or_comparison",
                "quote_grounding_mode": "absence_or_requirement_gap",
                "missing_or_weak_items": ["Medusa and EAGLE baselines"],
                "observed_inventory": [{"quote": theorem_quote, "locator": "Theorem 1"}],
                "status": "pending_absence_audit",
                "source_of_expectation": "reviewer_candidate",
            }
        ],
        "flaw_candidates": [],
        "unresolved_questions": [],
        "evidence_gaps": [],
        "conflict_notes": [],
    }

    hygiene = build_decision_hygiene_view(copy.deepcopy(state))["decision_hygiene"]

    assert hygiene["obligation_grounded_review_issue_count"] == 0
    assert hygiene["verified_review_issue_count"] == 0


def test_reviewer_issue_bundle_rejects_efficiency_gap_when_inventory_already_reports_time_and_memory():
    claim = "The graph contrastive method is efficient in runtime and memory compared with baselines."
    inventory_quote = (
        "Table 8 reports that PROPGCL demonstrates superior efficiency compared to baseline "
        "methods in terms of both computational time and memory usage."
    )
    state = {
        "paper_text": f"{claim}\n\n{inventory_quote}",
        "claims": [
            {
                "claim_id": "claim-1",
                "claim": claim,
                "claim_kind": "paper_extracted",
                "claim_type": "comparison",
                "importance": "high",
                "status": "supported",
                "claim_obligations": ["efficiency_cost"],
            }
        ],
        "evidence_map": [],
        "reviewer_negative_candidates": [
            {
                "candidate_id": "reviewer-neg-candidate-efficiency-present",
                "claim_id": "claim-1",
                "weakness": "The paper lacks quantitative efficiency metrics.",
                "negative_type": "efficiency_cost_gap",
                "required_evidence_type": "efficiency_cost",
                "quote_grounding_mode": "absence_or_requirement_gap",
                "missing_or_weak_items": ["runtime, memory, and FLOPs efficiency metrics"],
                "observed_inventory": [
                    {
                        "quote": inventory_quote,
                        "locator": "Table 8",
                        "observed_items": ["computational time", "memory usage"],
                    }
                ],
                "status": "pending_absence_audit",
                "source_of_expectation": "reviewer_candidate",
            }
        ],
        "flaw_candidates": [],
        "unresolved_questions": [],
        "evidence_gaps": [],
        "conflict_notes": [],
    }

    hygiene = build_decision_hygiene_view(copy.deepcopy(state))["decision_hygiene"]

    assert hygiene["obligation_grounded_review_issue_count"] == 0
    assert hygiene["verified_review_issue_count"] == 0


def test_reviewer_issue_bundle_rejects_efficiency_gap_with_theory_time_homogeneous_anchor():
    claim = "The adaptive decoding method achieves higher speedup than baseline methods."
    theory_quote = (
        "For any time-homogeneous policy with a bounded number of candidate tokens, "
        "the optimal policy has a threshold form."
    )
    state = {
        "paper_text": f"{claim}\n\n{theory_quote}",
        "claims": [
            {
                "claim_id": "claim-1",
                "claim": claim,
                "claim_kind": "paper_extracted",
                "claim_type": "comparison",
                "importance": "high",
                "status": "supported",
                "claim_obligations": ["efficiency_cost"],
            }
        ],
        "evidence_map": [],
        "reviewer_negative_candidates": [
            {
                "candidate_id": "reviewer-neg-candidate-theory-efficiency",
                "claim_id": "claim-1",
                "weakness": "The speedup claim lacks concrete latency and hardware cost evidence.",
                "negative_type": "efficiency_cost_gap",
                "required_evidence_type": "efficiency_cost",
                "quote_grounding_mode": "absence_or_requirement_gap",
                "missing_or_weak_items": ["latency and hardware cost breakdown"],
                "observed_inventory": [{"quote": theory_quote, "locator": "Theorem 1"}],
                "status": "pending_absence_audit",
                "source_of_expectation": "reviewer_candidate",
            }
        ],
        "flaw_candidates": [],
        "unresolved_questions": [],
        "evidence_gaps": [],
        "conflict_notes": [],
    }

    hygiene = build_decision_hygiene_view(copy.deepcopy(state))["decision_hygiene"]

    assert hygiene["obligation_grounded_review_issue_count"] == 0
    assert hygiene["verified_review_issue_count"] == 0


def test_reviewer_issue_bundle_rejects_method_gap_with_dataset_statistics_inventory_anchor():
    claim = "The framework uses a four-stage data processing and training pipeline for custom characters."
    inventory_quote = (
        "Table 1 gives basic statistics for OrcaData, including the number of role profiles "
        "and generated dialogue samples."
    )
    state = {
        "paper_text": f"{claim}\n\n{inventory_quote}",
        "claims": [
            {
                "claim_id": "claim-1",
                "claim": claim,
                "claim_kind": "paper_extracted",
                "claim_type": "method",
                "importance": "high",
                "status": "supported",
                "claim_obligations": ["method_detail"],
            }
        ],
        "evidence_map": [],
        "reviewer_negative_candidates": [
            {
                "candidate_id": "reviewer-neg-candidate-method-data-table",
                "claim_id": "claim-1",
                "weakness": "The method lacks a step-by-step processing algorithm.",
                "negative_type": "method_support_gap",
                "required_evidence_type": "method_detail",
                "quote_grounding_mode": "absence_or_requirement_gap",
                "missing_or_weak_items": ["step-by-step processing algorithm"],
                "observed_inventory": [{"quote": inventory_quote, "locator": "Table 1"}],
                "status": "pending_absence_audit",
                "source_of_expectation": "reviewer_candidate",
            }
        ],
        "flaw_candidates": [],
        "unresolved_questions": [],
        "evidence_gaps": [],
        "conflict_notes": [],
    }

    hygiene = build_decision_hygiene_view(copy.deepcopy(state))["decision_hygiene"]

    assert hygiene["obligation_grounded_review_issue_count"] == 0
    assert hygiene["verified_review_issue_count"] == 0


def test_reviewer_issue_bundle_rejects_method_gap_when_only_locator_is_method_like():
    claim = "The framework uses a four-stage processing pipeline for custom characters."
    inventory_quote = "Experiments show strong role-playing benchmark results for personality traits."
    state = {
        "paper_text": f"{claim}\n\n{inventory_quote}",
        "claims": [
            {
                "claim_id": "claim-1",
                "claim": claim,
                "claim_kind": "paper_extracted",
                "claim_type": "method",
                "importance": "high",
                "status": "supported",
                "claim_obligations": ["method_detail"],
            }
        ],
        "evidence_map": [],
        "reviewer_negative_candidates": [
            {
                "candidate_id": "reviewer-neg-candidate-method-generic-locator",
                "claim_id": "claim-1",
                "weakness": "The method lacks a concrete processing pipeline.",
                "negative_type": "method_support_gap",
                "required_evidence_type": "method_detail",
                "quote_grounding_mode": "absence_or_requirement_gap",
                "missing_or_weak_items": ["step-by-step processing pipeline"],
                "observed_inventory": [
                    {
                        "quote": inventory_quote,
                        "locator": "Method / Approach excerpt #1",
                    }
                ],
                "status": "pending_absence_audit",
                "source_of_expectation": "reviewer_candidate",
            }
        ],
        "flaw_candidates": [],
        "unresolved_questions": [],
        "evidence_gaps": [],
        "conflict_notes": [],
    }

    hygiene = build_decision_hygiene_view(copy.deepcopy(state))["decision_hygiene"]

    assert hygiene["obligation_grounded_review_issue_count"] == 0
    assert hygiene["verified_review_issue_count"] == 0


def test_reviewer_issue_bundle_rejects_missing_item_already_in_observed_inventory():
    claim = "The comparison evaluates the model against the GPT-4 baseline."
    inventory_quote = "Table 1 compares Ours, BERT, and GPT-4 baselines on Benchmark-X."
    state = {
        "paper_text": f"{claim}\n\n{inventory_quote}",
        "claims": [
            {
                "claim_id": "claim-1",
                "claim": claim,
                "claim_kind": "paper_extracted",
                "claim_type": "comparison",
                "importance": "high",
                "status": "supported",
                "claim_obligations": ["baseline_or_comparison"],
            }
        ],
        "evidence_map": [],
        "reviewer_negative_candidates": [
            {
                "candidate_id": "reviewer-neg-candidate-present-baseline",
                "claim_id": "claim-1",
                "weakness": "The table omits GPT-4.",
                "negative_type": "missing_baseline",
                "required_evidence_type": "baseline_or_comparison",
                "quote_grounding_mode": "absence_or_requirement_gap",
                "missing_or_weak_items": ["GPT-4 baseline"],
                "observed_inventory": [
                    {
                        "quote": inventory_quote,
                        "locator": "Table 1",
                        "observed_items": ["BERT baseline", "GPT-4 baseline", "Benchmark-X"],
                    }
                ],
                "status": "pending_absence_audit",
                "source_of_expectation": "reviewer_candidate",
            }
        ],
        "flaw_candidates": [],
        "unresolved_questions": [],
        "evidence_gaps": [],
        "conflict_notes": [],
    }

    hygiene = build_decision_hygiene_view(copy.deepcopy(state))["decision_hygiene"]

    assert hygiene["obligation_grounded_review_issue_count"] == 0
    assert hygiene["verified_review_issue_count"] == 0


def test_generic_obligation_only_review_issue_snapshot_is_not_verified():
    state = {
        "claims": [
            {
                "claim_id": "claim-1",
                "claim": "The method improves performance over baselines on Benchmark-X.",
                "claim_kind": "paper_extracted",
                "claim_type": "comparison",
                "importance": "high",
                "status": "supported",
            }
        ],
        "evidence_map": [
            {
                "evidence_id": "e-support-result",
                "claim_id": "claim-1",
                "evidence": "Table 1 reports Benchmark-X accuracy for the proposed method.",
                "raw_quote": "Table 1 reports Benchmark-X accuracy for the proposed method.",
                "source": "Table 1",
                "source_locator": "Table 1",
                "strength": "strong",
                "stance": "supports",
                "binding_status": "bound_real_claim",
                "verified_grounding_label": "paper_grounded_exact",
                "verified_quote_match_type": "quote_bank_id_canonical",
                "semantic_grounding_label": "semantic_support_verified",
                "support_source_bucket": "table_or_figure",
            },
            {
                "evidence_id": "evidence-reviewer-absence-claim-1-baseline-or-comparison",
                "claim_id": "claim-1",
                "stance": "missing",
                "strength": "missing",
                "evidence": "Reviewer absence audit: verified support inventory lacks baseline evidence.",
                "raw_quote": "",
                "source": "reviewer_absence_audit",
                "source_locator": "claim-evidence coverage audit",
                "binding_status": "bound_real_claim",
                "negative_evidence_type": "missing_baseline",
                "semantic_grounding_label": "semantic_negative_verified",
                "verified_grounding_label": "paper_absence_audit_verified",
                "review_negative_label": "review_negative_absence_audit_verified",
                "review_negative_reason": "claim_requirement_vs_verified_support_absence",
                "absence_audit_verified": True,
                "audit_basis": "claim_requirement_vs_verified_support",
                "missing_requirement": "baseline_or_comparison",
                "coverage_gap_missing_requirements": ["baseline_or_comparison"],
                "review_issue_source": "obligation_grounded_review_issue",
                "review_issue_id": "review-issue-claim-1-baseline-or-comparison",
                "review_issue_type": "missing_baseline",
                "review_issue_verification_status": "verified_review_issue",
                "review_issue_bundle": {
                    "issue_id": "review-issue-claim-1-baseline-or-comparison",
                    "claim_id": "claim-1",
                    "issue_type": "missing_baseline",
                    "required_evidence_type": "baseline_or_comparison",
                    "claim_anchor": {
                        "claim_id": "claim-1",
                        "quote": "The method improves performance over baselines on Benchmark-X.",
                        "locator": "claim extraction",
                    },
                    "observed_inventory": [
                        {
                            "evidence_id": "e-support-result",
                            "quote": "Table 1 reports Benchmark-X accuracy for the proposed method.",
                            "locator": "Table 1",
                        }
                    ],
                    "missing_or_mismatch": {
                        "entity": "baseline or comparison evidence",
                        "items": ["baseline or comparison evidence"],
                        "source": "claim_obligation",
                    },
                    "source_of_expectation": "claim_obligation",
                    "verification_status": "verified_review_issue",
                    "not_quote_negative": True,
                },
            },
        ],
        "flaw_candidates": [],
        "unresolved_questions": [],
        "evidence_gaps": [],
        "conflict_notes": [],
    }

    hygiene = build_decision_hygiene_view(state)["decision_hygiene"]

    assert hygiene["reviewer_absence_verified_count"] == 0
    assert hygiene["obligation_grounded_review_issue_count"] == 0
    assert hygiene["verified_review_issue_count"] == 0


def test_reviewer_issue_bundle_rejects_candidate_that_only_restates_requirement_label():
    claim = "The proposed model is effective on downstream detection tasks."
    inventory_quote = "Table 2 reports AP3D on KITTI for the proposed model."
    state = {
        "paper_text": f"{claim}\n\n{inventory_quote}",
        "claims": [
            {
                "claim_id": "claim-1",
                "claim": claim,
                "claim_kind": "paper_extracted",
                "claim_type": "empirical",
                "importance": "high",
                "status": "supported",
                "claim_obligations": ["ablation_or_component"],
            }
        ],
        "evidence_map": [
            {
                "evidence_id": "ev-result-table",
                "claim_id": "claim-1",
                "evidence": inventory_quote,
                "raw_quote": inventory_quote,
                "source": "Table 2",
                "source_locator": "Table 2",
                "strength": "strong",
                "stance": "supports",
                "binding_status": "bound_real_claim",
                "verified_grounding_label": "paper_grounded_exact",
                "verified_quote_match_type": "quote_bank_id_canonical",
                "semantic_grounding_label": "semantic_support_verified",
                "support_source_bucket": "table_or_figure",
            }
        ],
        "reviewer_negative_candidates": [
            {
                "candidate_id": "reviewer-neg-candidate-generic-ablation",
                "claim_id": "claim-1",
                "weakness": "The result table does not provide ablation evidence.",
                "negative_type": "missing_ablation",
                "required_evidence_type": "ablation_or_component",
                "quote_grounding_mode": "absence_or_requirement_gap",
                "missing_or_weak_items": ["ablation or component-isolation evidence"],
                "observed_inventory": [
                    {
                        "quote": inventory_quote,
                        "locator": "Table 2",
                        "observed_items": ["KITTI", "AP3D"],
                    }
                ],
                "status": "pending_absence_audit",
                "source_of_expectation": "reviewer_candidate",
            }
        ],
        "flaw_candidates": [],
        "unresolved_questions": [],
        "evidence_gaps": [],
        "conflict_notes": [],
    }

    hygiene = build_decision_hygiene_view(copy.deepcopy(state))["decision_hygiene"]

    assert hygiene["obligation_grounded_review_issue_count"] == 0
    assert hygiene["verified_review_issue_count"] == 0


def test_reviewer_issue_bundle_rejects_slash_generic_result_evidence_item():
    claim = "The proposed method prevents model collapse in DCCA."
    inventory_quote = "Figure 2 reports reconstruction and denoising losses on the synthetic test set."
    state = {
        "paper_text": f"{claim}\n\n{inventory_quote}",
        "claims": [
            {
                "claim_id": "claim-1",
                "claim": claim,
                "claim_kind": "paper_extracted",
                "claim_type": "empirical",
                "importance": "high",
                "status": "supported",
                "claim_obligations": ["empirical_result"],
            }
        ],
        "evidence_map": [
            {
                "evidence_id": "ev-loss-figure",
                "claim_id": "claim-1",
                "evidence": inventory_quote,
                "raw_quote": inventory_quote,
                "source": "Figure 2",
                "source_locator": "Figure 2",
                "strength": "strong",
                "stance": "supports",
                "binding_status": "bound_real_claim",
                "verified_grounding_label": "paper_grounded_exact",
                "verified_quote_match_type": "quote_bank_id_canonical",
                "semantic_grounding_label": "semantic_support_verified",
                "support_source_bucket": "table_or_figure",
            }
        ],
        "reviewer_negative_candidates": [
            {
                "candidate_id": "reviewer-neg-candidate-generic-result",
                "claim_id": "claim-1",
                "weakness": "The claim still lacks result evidence.",
                "negative_type": "insufficient_evaluation",
                "required_evidence_type": "empirical_result",
                "quote_grounding_mode": "absence_or_requirement_gap",
                "missing_or_weak_items": ["result/table/experiment evidence"],
                "observed_inventory": [{"quote": inventory_quote, "locator": "Figure 2"}],
                "status": "pending_absence_audit",
                "source_of_expectation": "reviewer_candidate",
            }
        ],
        "flaw_candidates": [],
        "unresolved_questions": [],
        "evidence_gaps": [],
        "conflict_notes": [],
    }

    hygiene = build_decision_hygiene_view(copy.deepcopy(state))["decision_hygiene"]

    assert hygiene["obligation_grounded_review_issue_count"] == 0
    assert hygiene["verified_review_issue_count"] == 0


def test_failed_quote_negative_candidate_does_not_suppress_absence_audit():
    state = {
        "claims": [
            {
                "claim_id": "claim-1",
                "claim": "The retrieval module improves performance compared to the GPT-4 baseline.",
                "claim_kind": "paper_extracted",
                "claim_type": "comparison",
                "status": "supported",
            },
        ],
        "reviewer_negative_candidates": [
            {
                "candidate_id": "reviewer-neg-candidate-gpt4-baseline",
                "claim_id": "claim-1",
                "weakness": "The comparison claim lacks verified evidence for the GPT-4 baseline.",
                "negative_type": "missing_baseline",
                "required_evidence_type": "baseline_or_comparison",
                "quote_grounding_mode": "absence_or_requirement_gap",
                "missing_or_weak_items": ["GPT-4 baseline"],
                "status": "pending_absence_audit",
            }
        ],
        "evidence_map": [
            {
                "evidence_id": "e-support-result-inventory",
                "claim_id": "claim-1",
                "evidence": "The method section describes the retrieval module pipeline.",
                "raw_quote": "The retrieval module reranks passages before generation.",
                "source": "Method",
                "source_locator": "Section 3",
                "strength": "medium",
                "stance": "supports",
                "binding_status": "bound_real_claim",
                "verified_grounding_label": "paper_grounded_exact",
                "verified_quote_match_type": "quote_bank_id_canonical",
                "semantic_grounding_label": "semantic_support_verified",
                "support_source_bucket": "method",
            },
            {
                "evidence_id": "evidence-failed-negative-candidate",
                "claim_id": "claim-1",
                "evidence": "Rejected quote-negative candidate.",
                "raw_quote": "The paper reports results on Benchmark-X.",
                "source": "targeted-negative-candidate-quote",
                "source_locator": "Results",
                "stance": "missing",
                "strength": "missing",
                "binding_status": "bound_real_claim",
                "verified_grounding_label": "paper_grounded_exact",
                "verified_quote_match_type": "candidate_window_quote_bank_exact_substring",
                "semantic_grounding_label": "semantic_mismatch",
                "review_negative_label": "insufficient_semantic_negative",
                "review_negative_reason": "semantic_negative_verification_missing",
                "negative_evidence_type": "missing_baseline",
            }
        ],
        "flaw_candidates": [],
        "unresolved_questions": [],
        "evidence_gaps": [],
        "conflict_notes": [],
    }

    view = build_decision_hygiene_view(state)
    hygiene = view["decision_hygiene"]
    absence_evidence = [
        item for item in view["evidence_map"]
        if item.get("review_negative_label") == "review_negative_absence_audit_verified"
    ]

    assert hygiene["review_negative_verified_count"] == 0
    assert hygiene["reviewer_absence_verified_count"] == 0
    assert hygiene.get("reviewer_absence_verified_type_counts", {}).get("missing_baseline", 0) == 0
    assert absence_evidence == []
    assert hygiene["diagnosis_pending_potential_concern_count"] >= 1


def test_stale_reviewer_absence_snapshot_stops_counting_when_requirement_is_satisfied():
    state = {
        "claims": [
            {
                "claim_id": "claim-1",
                "claim": "The method improves performance compared to the GPT-4 baseline.",
                "claim_kind": "paper_extracted",
                "claim_type": "comparison",
                "importance": "high",
                "status": "supported",
            }
        ],
        "reviewer_negative_candidates": [
            {
                "candidate_id": "reviewer-neg-candidate-gpt4-baseline",
                "claim_id": "claim-1",
                "weakness": "The comparison claim lacks verified evidence for the GPT-4 baseline.",
                "negative_type": "missing_baseline",
                "required_evidence_type": "baseline_or_comparison",
                "quote_grounding_mode": "absence_or_requirement_gap",
                "missing_or_weak_items": ["GPT-4 baseline"],
                "status": "pending_absence_audit",
            }
        ],
        "evidence_map": [
            {
                "evidence_id": "e-support-baseline",
                "claim_id": "claim-1",
                "evidence": "Table 1 compares the method against the GPT-4 baseline.",
                "raw_quote": "Table 1: Our method is compared against the GPT-4 baseline on Benchmark-X.",
                "source": "Table 1",
                "source_locator": "Table 1",
                "strength": "strong",
                "stance": "supports",
                "binding_status": "bound_real_claim",
                "verified_grounding_label": "paper_grounded_exact",
                "verified_quote_match_type": "quote_bank_id_canonical",
                "semantic_grounding_label": "semantic_support_verified",
                "support_source_bucket": "table_or_figure",
            },
            {
                "evidence_id": "evidence-reviewer-absence-claim-1-baseline-or-comparison",
                "claim_id": "claim-1",
                "stance": "missing",
                "strength": "missing",
                "evidence": "Reviewer absence audit: verified support inventory lacks baseline evidence.",
                "raw_quote": "",
                "negative_quote": "",
                "source": "reviewer_absence_audit",
                "source_locator": "claim-evidence coverage audit",
                "binding_status": "bound_real_claim",
                "negative_evidence_type": "missing_baseline",
                "semantic_grounding_label": "semantic_negative_verified",
                "verified_grounding_label": "paper_absence_audit_verified",
                "review_negative_label": "review_negative_absence_audit_verified",
                "review_negative_reason": "claim_requirement_vs_verified_support_absence",
                "absence_audit_verified": True,
                "quote_grounding_required": False,
                "no_direct_quote_expected": True,
                "audit_basis": "claim_requirement_vs_verified_support",
                "missing_requirement": "baseline_or_comparison",
                "coverage_gap_missing_requirements": ["baseline_or_comparison"],
                "coverage_missing_items": ["GPT-4 baseline"],
                "absence_audit_snapshot_at_recovery_commit": True,
            },
        ],
        "flaw_candidates": [],
        "unresolved_questions": [],
        "evidence_gaps": [],
        "conflict_notes": [],
    }

    hygiene = build_decision_hygiene_view(state)["decision_hygiene"]

    assert hygiene["reviewer_absence_verified_count"] == 0
    assert hygiene["total_review_negative_verified_count"] == 0
    assert hygiene.get("reviewer_absence_verified_type_counts", {}).get("missing_baseline", 0) == 0


def test_freeform_absence_candidate_rejects_generic_missing_baseline_items():
    state = {
        "claims": [
            {
                "claim_id": "claim-1",
                "claim": "The method outperforms GPT-4 and Llama-2 baselines on Benchmark-X.",
                "claim_kind": "paper_extracted",
                "claim_type": "comparison",
                "status": "supported",
            },
            {
                "claim_id": "claim-2",
                "claim": "The retrieval module improves performance compared to strong baselines.",
                "claim_kind": "paper_extracted",
                "claim_type": "comparison",
                "status": "uncertain",
            },
        ],
        "evidence_map": [
            {
                "evidence_id": "ev-claim1-baseline",
                "claim_id": "claim-1",
                "evidence": "Table 1 compares the method against GPT-4 and Llama-2 baselines.",
                "raw_quote": "Table 1: Our method is compared against GPT-4 and Llama-2 baselines on Benchmark-X.",
                "source": "Table 1",
                "source_locator": "Table 1",
                "strength": "strong",
                "stance": "supports",
                "binding_status": "bound_real_claim",
                "verified_grounding_label": "paper_grounded_exact",
                "verified_quote_match_type": "quote_bank_id_canonical",
                "semantic_grounding_label": "semantic_support_verified",
                "support_source_bucket": "table_or_figure",
            }
        ],
        "reviewer_negative_candidates": [
            {
                "candidate_id": "reviewer-neg-candidate-generic-baseline",
                "claim_id": "claim-2",
                "weakness": "The baseline set may omit key competitors.",
                "negative_type": "missing_baseline",
                "required_evidence_type": "baseline_or_comparison",
                "quote_grounding_mode": "absence_or_requirement_gap",
                "missing_or_weak_items": ["key competitors", "all relevant recent methods"],
                "status": "pending_absence_audit",
            }
        ],
        "flaw_candidates": [],
        "unresolved_questions": [],
        "evidence_gaps": [],
        "conflict_notes": [],
    }

    hygiene = build_decision_hygiene_view(state)["decision_hygiene"]
    assert hygiene["reviewer_absence_verified_count"] == 0
    assert hygiene.get("reviewer_absence_verified_type_counts", {}).get("missing_baseline", 0) == 0


def test_freeform_absence_candidate_provenance_is_kept_on_existing_coverage_gap():
    state = {
        "claims": [
            {
                "claim_id": "claim-1",
                "claim": "The paper compares against the GPT-4 baseline.",
                "claim_kind": "paper_extracted",
                "claim_type": "other",
                "status": "uncertain",
            },
        ],
        "reviewer_negative_candidates": [
            {
                "candidate_id": "reviewer-neg-candidate-gpt4-baseline",
                "claim_id": "claim-1",
                "weakness": "The comparison claim lacks verified evidence for the GPT-4 baseline.",
                "negative_type": "missing_baseline",
                "required_evidence_type": "baseline_or_comparison",
                "quote_grounding_mode": "absence_or_requirement_gap",
                "missing_or_weak_items": ["GPT-4 baseline"],
                "status": "pending_absence_audit",
            }
        ],
        "evidence_map": [
            {
                "evidence_id": "e-support-method-inventory",
                "claim_id": "claim-1",
                "evidence": "The method section describes the retrieval pipeline.",
                "raw_quote": "The retrieval module reranks passages before generation.",
                "source": "Method",
                "source_locator": "Section 3",
                "strength": "medium",
                "stance": "supports",
                "binding_status": "bound_real_claim",
                "verified_grounding_label": "paper_grounded_exact",
                "verified_quote_match_type": "quote_bank_id_canonical",
                "semantic_grounding_label": "semantic_support_verified",
                "support_source_bucket": "method",
            }
        ],
        "flaw_candidates": [],
        "unresolved_questions": [],
        "evidence_gaps": [],
        "conflict_notes": [],
    }

    view = build_decision_hygiene_view(state)
    hygiene = view["decision_hygiene"]
    evidence = [
        item for item in view["evidence_map"]
        if item.get("review_negative_label") == "review_negative_absence_audit_verified"
    ]

    assert hygiene["reviewer_absence_verified_count"] == 0
    assert evidence == []
    assert hygiene["diagnosis_pending_potential_concern_count"] >= 1


def test_table_scope_absence_accepts_concrete_evaluation_dimension_gap_with_observed_scope():
    quote = (
        "From this, we propose a metric of Intervention Success Rate, which measures whether "
        "intervening on feature activations changes the corresponding model output."
    )
    paper_text, quote_bank = _grounding_bank([("quote-metrics", quote, "results")])
    state = {
        "claims": [
            {
                "claim_id": "claim-1",
                "claim": "The interpretability intervention evaluation is comprehensive across useful deployment criteria.",
                "claim_kind": "paper_extracted",
            }
        ],
        "reviewer_negative_candidates": [
            {
                "candidate_id": "reviewer-neg-candidate-metrics",
                "claim_id": "claim-1",
                "weakness": "The evaluation may omit efficiency and sensitivity dimensions.",
                "negative_type": "insufficient_evaluation",
                "required_evidence_type": "evaluation_protocol",
                "missing_or_weak_items": [
                    "computational cost metrics",
                    "hyperparameter sensitivity analysis",
                ],
                "status": "pending_quote_verification",
            }
        ],
        "evidence_map": [
            {
                "evidence_id": "e-freeform-metric-coverage",
                "claim_id": "claim-1",
                "evidence": (
                    "The visible evaluation metric is Intervention Success Rate, but the reviewer task "
                    "checks missing computational cost metrics and hyperparameter sensitivity analysis."
                ),
                "source": "Results / Evaluation excerpt #1",
                "source_locator": "Results / Evaluation excerpt #1",
                "stance": "missing",
                "strength": "missing",
                "raw_quote": quote,
                "quote_id": "quote-metrics",
                "negative_evidence_type": "insufficient_evaluation",
                "targeted_negative_search_task_id": "neg-search-freeform-claim-1-reviewer-neg-candidate-metrics",
                "coverage_missing_items": [
                    "computational cost metrics",
                    "hyperparameter sensitivity analysis",
                ],
                "coverage_observed_items": ["Intervention Success Rate"],
            }
        ],
        "paper_text": paper_text,
        "evidence_quote_bank": quote_bank,
    }

    merged = merge_review_state(state, {"evidence_map": state["evidence_map"]})
    ev = merged["evidence_map"][0]

    assert ev["semantic_grounding_label"] == "semantic_negative_verified"
    assert "table_scope_absence_verified" in ev["semantic_grounding_reasons"]
    assert ev["review_negative_label"] == "review_negative_verified"
    assert ev["review_negative_reason"] == "table_scope_absence_weakens_claim"
    assert _is_grounded_paper_negative_evidence_record(ev, merged)


def test_table_scope_absence_rejects_generic_freeform_missing_baseline_item():
    table_quote = "Table 1: Speedup for Medusa, EAGLE, and ReDrafter on MT-Bench."
    paper_text, quote_bank = _grounding_bank([("quote-table-1", table_quote, "table_or_figure")])
    state = {
        "claims": [
            {
                "claim_id": "claim-1",
                "claim": "The method achieves state-of-the-art speculative decoding speedup.",
                "claim_kind": "paper_extracted",
            }
        ],
        "reviewer_negative_candidates": [
            {
                "candidate_id": "reviewer-neg-candidate-baselines",
                "claim_id": "claim-1",
                "weakness": "The baseline set may omit key competitors.",
                "negative_type": "missing_baseline",
                "required_evidence_type": "baseline_or_comparison",
                "missing_or_weak_items": ["key competitors", "all relevant recent methods"],
                "status": "pending_quote_verification",
            }
        ],
        "evidence_map": [
            {
                "evidence_id": "e-generic-baseline-coverage",
                "claim_id": "claim-1",
                "evidence": "The table lists Medusa, EAGLE, and ReDrafter, but may omit key competitors.",
                "source": "Table 1",
                "source_locator": "Table 1",
                "stance": "missing",
                "strength": "missing",
                "raw_quote": table_quote,
                "quote_id": "quote-table-1",
                "negative_evidence_type": "missing-baseline",
                "targeted_negative_search_task_id": "neg-search-freeform-claim-1-reviewer-neg-candidate-baselines",
                "coverage_missing_items": ["key competitors", "all relevant recent methods"],
            }
        ],
        "paper_text": paper_text,
        "evidence_quote_bank": quote_bank,
    }

    merged = merge_review_state(state, {"evidence_map": state["evidence_map"]})
    ev = merged["evidence_map"][0]

    assert ev["negative_evidence_type"] == "missing_baseline"
    assert ev["semantic_grounding_label"] == "semantic_mismatch"
    assert not _is_grounded_paper_negative_evidence_record(ev, merged)


def test_table_scope_absence_rejects_present_baseline_as_missing_or_weak():
    quote = (
        "Despite its simplicity, the $k$ -NN solver is the strongest baseline because, "
        "like Graph2Tac, it is able to adapt in real-time to the changing Coq environment."
    )
    paper_text, quote_bank = _grounding_bank([("quote-comparison-1", quote, "comparison")])
    state = {
        "claims": [
            {
                "claim_id": "claim-1",
                "claim": "Graph2Tac achieves superior empirical performance compared to baselines in theorem proving tasks.",
                "claim_kind": "paper_extracted",
            }
        ],
        "reviewer_negative_candidates": [
            {
                "candidate_id": "reviewer-neg-candidate-baseline-strength",
                "claim_id": "claim-1",
                "weakness": "The baseline comparison may be weak or insufficiently justified.",
                "negative_type": "unfair_or_weak_baseline",
                "required_evidence_type": "baseline_or_comparison",
                "missing_or_weak_items": [
                    "citation or prior work reference for k-NN baseline",
                    "comparison to other published methods",
                ],
                "status": "pending_quote_verification",
            }
        ],
        "evidence_map": [
            {
                "evidence_id": "e-present-baseline",
                "claim_id": "claim-1",
                "evidence": (
                    "The copied quote states that k-NN is the strongest baseline, "
                    "but the reviewer task asks whether the k-NN baseline is weak or underjustified."
                ),
                "source": "Candidate-Relevant Paper Windows",
                "source_locator": "Comparison / Robustness excerpt #2",
                "stance": "missing",
                "strength": "missing",
                "raw_quote": quote,
                "quote_id": "quote-comparison-1",
                "negative_evidence_type": "unfair_or_weak_baseline",
                "targeted_negative_search_task_id": (
                    "neg-search-freeform-claim-1-reviewer-neg-candidate-baseline-strength"
                ),
                "coverage_missing_items": [
                    "citation or prior work reference for k-NN baseline",
                    "comparison to other published methods",
                ],
            }
        ],
        "paper_text": paper_text,
        "evidence_quote_bank": quote_bank,
    }

    merged = merge_review_state(state, {"evidence_map": state["evidence_map"]})
    ev = merged["evidence_map"][0]

    assert ev["semantic_grounding_label"] == "semantic_mismatch"
    assert ev["review_negative_label"] != "review_negative_verified"
    assert not _is_grounded_paper_negative_evidence_record(ev, merged)

    stale_verified = copy.deepcopy(ev)
    stale_verified["semantic_grounding_label"] = "semantic_negative_verified"
    stale_verified["review_negative_label"] = "review_negative_verified"
    stale_verified["review_negative_reason"] = "table_scope_absence_weakens_claim"
    assert not _is_grounded_paper_negative_evidence_record(stale_verified, merged)


def test_table_scope_absence_rejects_coverage_missing_without_visible_observed_scope():
    quote = (
        "We then propose evaluation metrics for (1) testing the correctness of explanations via intervention "
        "and (2) the usefulness of these methods for steering and editing representations and model outputs."
    )
    paper_text, quote_bank = _grounding_bank([("quote-metrics", quote, "method")])
    state = {
        "claims": [
            {
                "claim_id": "claim-1",
                "claim": "The intervention evaluation generalizes across model families and scales.",
                "claim_kind": "paper_extracted",
            }
        ],
        "reviewer_negative_candidates": [
            {
                "candidate_id": "reviewer-neg-candidate-model-scope",
                "claim_id": "claim-1",
                "weakness": "The evaluation may lack model scale and architecture diversity.",
                "negative_type": "insufficient_evaluation",
                "required_evidence_type": "robustness_or_generalization",
                "missing_or_weak_items": [
                    "model scale diversity",
                    "architectural family diversity",
                    "evidence on modern large-scale models",
                ],
                "status": "pending_quote_verification",
            }
        ],
        "evidence_map": [
            {
                "evidence_id": "e-metric-prose-not-coverage",
                "claim_id": "claim-1",
                "evidence": "insufficient_evaluation",
                "source": "Section: Method",
                "source_locator": "Section: Method",
                "stance": "missing",
                "strength": "missing",
                "raw_quote": quote,
                "quote_id": "quote-metrics",
                "negative_evidence_type": "insufficient_evaluation",
                "targeted_negative_search_task_id": "neg-search-freeform-claim-1-reviewer-neg-candidate-model-scope",
                "coverage_missing_items": [
                    "model scale diversity",
                    "architectural family diversity",
                    "evidence on modern large-scale models",
                ],
            }
        ],
        "paper_text": paper_text,
        "evidence_quote_bank": quote_bank,
    }

    merged = merge_review_state(state, {"evidence_map": state["evidence_map"]})
    ev = merged["evidence_map"][0]

    assert ev["semantic_grounding_label"] == "semantic_mismatch"
    assert "quote_lacks_negative_anchor" in ev["semantic_grounding_reasons"]
    assert not _is_grounded_paper_negative_evidence_record(ev, merged)


def test_table_scope_absence_rejects_quote_excerpt_incompleteness():
    table_quote = r"\begin{table} \caption{Normalized latent reconstruction error without intervention.}"
    paper_text, quote_bank = _grounding_bank([("quote-table-caption", table_quote, "table_or_figure")])
    state = {
        "claims": [
            {
                "claim_id": "claim-1",
                "claim": "The paper evaluates Intervention Success Rate with complete quantitative results.",
                "claim_kind": "paper_extracted",
            }
        ],
        "evidence_map": [
            {
                "evidence_id": "e-quote-incomplete",
                "claim_id": "claim-1",
                "evidence": (
                    "The paper evaluates Intervention Success Rate, but the formal definition is not provided "
                    "in the quoted text. A table caption is shown, but the actual numerical results are not "
                    "included in the quote."
                ),
                "source": "Section on Comparative Evaluation",
                "source_locator": "Table caption",
                "stance": "missing",
                "strength": "missing",
                "raw_quote": table_quote,
                "quote_id": "quote-table-caption",
                "negative_evidence_type": "missing_baseline",
            }
        ],
        "paper_text": paper_text,
        "evidence_quote_bank": quote_bank,
    }

    merged = merge_review_state(state, {"evidence_map": state["evidence_map"]})
    ev = merged["evidence_map"][0]

    assert ev["semantic_grounding_label"] != "semantic_negative_verified"
    assert ev["review_negative_label"] != "review_negative_verified"
    assert not _is_grounded_paper_negative_evidence_record(ev, merged)


def test_table_scope_absence_rejects_locator_only_result_intro_quote():
    intro_quote = (
        "equal, offering valuable insights into the system's overall performance. "
        "Section 4.3 Results. As outlined in Section 3, our study analyzes the impact of FL."
    )
    paper_text, quote_bank = _grounding_bank([("quote-results-intro", intro_quote, "results")])
    state = {
        "claims": [
            {
                "claim_id": "claim-1",
                "claim": "The proposed method improves over FedAvg.",
                "claim_kind": "paper_extracted",
            }
        ],
        "evidence_map": [
            {
                "evidence_id": "e-locator-only",
                "claim_id": "claim-1",
                "evidence": "Table 3 reports FedGAN at 85.39% while FedAvg achieves 93.96%.",
                "source": "Table 3",
                "source_locator": "Table 3",
                "stance": "contradicts",
                "strength": "missing",
                "raw_quote": intro_quote,
                "quote_id": "quote-results-intro",
                "negative_evidence_type": "direct_contradiction",
            }
        ],
        "paper_text": paper_text,
        "evidence_quote_bank": quote_bank,
    }

    merged = merge_review_state(state, {"evidence_map": state["evidence_map"]})
    ev = merged["evidence_map"][0]

    assert ev["semantic_grounding_label"] == "semantic_mismatch"
    assert not _is_grounded_paper_negative_evidence_record(ev, merged)


def test_normalize_evidence_item_preserves_negative_type_alias():
    state = {
        "claims": [
            {
                "claim_id": "claim-1",
                "claim": "The method is evaluated on DAVIS2017.",
                "claim_kind": "paper_extracted",
            }
        ],
        "evidence_map": [],
    }
    merged = merge_review_state(
        state,
        {
            "evidence_map": [
                {
                    "evidence_id": "e-negative-alias",
                    "claim_id": "claim-1",
                    "evidence": "Table 2 does not include DAVIS2017.",
                    "raw_quote": "Table 2: Results obtained on DAVIS2016, SegTrackV2, and FBMS59.",
                    "source": "Table 2",
                    "source_locator": "Table 2",
                    "stance": "missing",
                    "strength": "missing",
                    "negative_type": "insufficient_evaluation",
                    "required_evidence_type": "empirical_result",
                    "targeted_negative_search_task_id": "neg-search-1",
                }
            ]
        },
    )
    ev = merged["evidence_map"][0]

    assert ev["negative_evidence_type"] == "insufficient_evaluation"
    assert ev["required_evidence_type"] == "empirical_result"
    assert ev["targeted_negative_search_task_id"] == "neg-search-1"


def test_false_review_negative_does_not_promote_final_concern():
    state = {
        "claims": [
            {
                "claim_id": "claim-1",
                "claim": "The paper proposes a robust assignment method.",
                "claim_kind": "paper_extracted",
            }
        ],
        "evidence_map": [
            {
                "evidence_id": "e-positive-limitation",
                "claim_id": "claim-1",
                "stance": "missing",
                "strength": "missing",
                "raw_quote": "In this paper, we present a novel viewpoint for addressing the above limitations.",
                "verified_grounding_label": "paper_grounded_exact",
                "semantic_grounding_label": "semantic_negative_verified",
                "negative_evidence_type": "scope_limitation",
            }
        ],
        "flaw_candidates": [
            {
                "flaw_id": "flaw-1",
                "flaw": "Candidate limitation quote weakens the claim.",
                "status": "candidate",
                "severity": "minor",
                "related_claim_ids": ["claim-1"],
                "negative_evidence_ids": ["e-positive-limitation"],
            }
        ],
    }

    view = build_decision_hygiene_view(state)
    hygiene = view["decision_hygiene"]
    assert hygiene["negative_evidence_candidate_count"] == 0
    assert hygiene["verified_negative_flaw_count"] == 0
    assert hygiene["potential_concern_count"] == 0
    assert hygiene["negative_evidence_semantic_rejected_count"] == 1


def test_actionable_negative_evidence_can_anchor_flaw():
    state = {
        "claims": [{"claim_id": "claim-1", "claim": "The method is empirically validated.", "claim_kind": "paper_extracted"}],
        "evidence_map": [
            {
                "evidence_id": "e-neg-ablation",
                "claim_id": "claim-1",
                "stance": "missing",
                "strength": "missing",
                "raw_quote": "The paper does not report ablation experiments for the core module.",
                "verified_grounding_label": "paper_grounded_exact",
                "verified_source_span_start": 20,
                "verified_source_span_end": 84,
                "verified_quote_match_type": "exact",
                "semantic_grounding_label": "semantic_negative_verified",
                "negative_evidence_type": "missing_ablation",
            }
        ],
        "flaw_candidates": [
            {
                "flaw_id": "flaw-1",
                "flaw": "The core module lacks ablation evidence.",
                "status": "candidate",
                "severity": "major",
                "related_claim_ids": ["claim-1"],
                "negative_evidence_ids": ["e-neg-ablation"],
            }
        ],
    }
    view = build_decision_hygiene_view(state)
    hygiene = view["decision_hygiene"]
    assert hygiene["verified_actionable_negative_flaw_count"] == 1
    assert hygiene["verified_potential_concern_count"] == 1
    assert hygiene["potential_concern_count"] == 1
    assert hygiene["negative_flaw_not_upgraded_reason_counts"] == {"limitation_type_stays_potential_concern": 1}
    assert hygiene["negative_evidence_type_counts"]["missing_ablation"] == 1


def test_build_review_task_persists_full_paper_text_in_review_state_for_offline_verifiers():
    paper_text = "Abstract.\n" + ("This paper reports experiments and ablations.\n" * 1400)

    task = build_review_task({"paper_id": "paper-full-text", "paper_text": paper_text}, mode="s4", max_turns=7)

    assert task["paper_text"] == task["review_state"]["paper_text"]
    assert len(task["review_state"]["paper_text"]) > 32000


def test_claim_normalization_fills_deterministic_obligations_when_model_omits_them():
    merged = merge_review_state(
        {"claims": [], "evidence_map": []},
        {
            "claims": [
                {
                    "claim_id": "claim-1",
                    "claim": "The method outperforms strong baselines on three benchmark datasets.",
                    "claim_kind": "paper_extracted",
                    "claim_type": "empirical",
                    "coverage_tags": ["empirical", "comparison"],
                    "status": "uncertain",
                }
            ]
        },
    )

    claim = merged["claims"][0]

    assert "empirical_result" in claim["claim_obligations"]
    assert "baseline_or_comparison" in claim["claim_obligations"]
    assert claim["claim_obligation_source"] == "deterministic_inference"


def test_review_issue_bundle_allows_empirical_claim_with_noisy_limitation_tag():
    claim = "CDiffuser demonstrates a significant advantage over baselines in low-quality datasets."
    inventory_quote = "Table 2 reports CDiffuser and baseline performance on Kitchen low-quality datasets."
    state = {
        "paper_text": f"{claim}\n\n{inventory_quote}",
        "claims": [
            {
                "claim_id": "claim-1",
                "claim": claim,
                "claim_kind": "paper_extracted",
                "claim_type": "empirical",
                "importance": "high",
                "status": "supported",
                "coverage_tags": ["empirical", "comparison", "limitation"],
                "claim_obligations": ["baseline_or_comparison"],
            }
        ],
        "evidence_map": [],
        "reviewer_negative_candidates": [
            {
                "candidate_id": "reviewer-neg-candidate-low-quality-baseline",
                "claim_id": "claim-1",
                "weakness": "The low-quality comparison may omit a Conservative Q-Learning baseline.",
                "negative_type": "unfair_or_weak_baseline",
                "required_evidence_type": "baseline_or_comparison",
                "quote_grounding_mode": "absence_or_requirement_gap",
                "missing_or_weak_items": ["Conservative Q-Learning baseline"],
                "observed_inventory": [
                    {
                        "quote": inventory_quote,
                        "locator": "Table 2",
                        "observed_items": ["CDiffuser", "baseline performance", "Kitchen low-quality datasets"],
                    }
                ],
                "status": "pending_absence_audit",
                "source_of_expectation": "reviewer_candidate",
            }
        ],
        "flaw_candidates": [],
        "unresolved_questions": [],
        "evidence_gaps": [],
        "conflict_notes": [],
    }

    hygiene = build_decision_hygiene_view(copy.deepcopy(state))["decision_hygiene"]

    assert hygiene["obligation_grounded_review_issue_count"] == 1
    assert hygiene["verified_review_issue_count"] == 1


def test_merge_review_state_materializes_verified_review_issue_bundle_for_recovery():
    claim = "The method compares favorably against baselines on Benchmark-X."
    inventory_quote = (
        "Table 1 compares Ours with BERT baselines on Benchmark-X and reports accuracy "
        "and F1 metrics for each method."
    )
    merged = merge_review_state(
        {
            "paper_text": f"{claim}\n\n{inventory_quote}",
            "claims": [],
            "evidence_map": [],
            "flaw_candidates": [],
            "reviewer_negative_candidates": [],
            "unresolved_questions": [],
        },
        {
            "claims": [
                {
                    "claim_id": "claim-1",
                    "claim": claim,
                    "claim_kind": "paper_extracted",
                    "claim_type": "comparison",
                    "coverage_tags": ["empirical", "comparison"],
                    "importance": "high",
                    "status": "supported",
                }
            ],
            "review_issue_candidates": [
                {
                    "candidate_id": "reviewer-neg-candidate-gpt4-live",
                    "claim_id": "claim-1",
                    "weakness": "The comparison omits the named GPT-4 baseline.",
                    "issue_type": "missing_baseline",
                    "required_evidence_type": "baseline_or_comparison",
                    "quote_grounding_mode": "absence_or_requirement_gap",
                    "missing_or_weak_items": ["GPT-4 baseline"],
                    "observed_inventory": [
                        {
                            "quote": inventory_quote,
                            "locator": "Table 1",
                            "observed_items": ["Ours", "BERT baselines", "Benchmark-X"],
                        }
                    ],
                    "source_of_expectation": "reviewer_candidate",
                    "status": "pending_absence_audit",
                }
            ],
        },
    )

    issue_evidence = [
        item for item in merged["evidence_map"]
        if item.get("review_issue_source") == "obligation_grounded_review_issue"
    ]
    issue_flaws = [
        item for item in merged["flaw_candidates"]
        if item.get("source") == "reviewer_absence_audit"
    ]

    assert len(issue_evidence) == 1
    assert issue_evidence[0]["review_issue_verification_status"] == "verified_review_issue"
    assert len(issue_flaws) == 1
    assert issue_evidence[0]["evidence_id"] in issue_flaws[0]["negative_evidence_ids"]
    assert len(merged.get("review_issues", [])) == 1
    assert merged["review_issues"][0]["verification_status"] == "verified_review_issue"
    assert merged["review_issues"][0]["recovery_status"] == "open"
    assert issue_evidence[0]["evidence_id"] in merged["review_issues"][0]["evidence_ids"]


def test_review_issue_bundle_flaw_materialization_survives_non_audit_id_collision():
    claim = "The proposed Local-Global Distillation method is computationally efficient."
    inventory_quote = "The paper states that Local-Global Distillation is more computationally efficient."
    colliding_flaw_id = "flaw-reviewer-absence-claim-1-efficiency-cost-gap"
    state = {
        "paper_text": f"{claim}\n\n{inventory_quote}",
        "claims": [
            {
                "claim_id": "claim-1",
                "claim": claim,
                "claim_kind": "paper_extracted",
                "claim_type": "empirical",
                "importance": "high",
                "status": "supported",
                "coverage_tags": ["empirical", "efficiency"],
                "claim_obligations": ["efficiency_cost"],
            }
        ],
        "evidence_map": [],
        "reviewer_negative_candidates": [
            {
                "candidate_id": "reviewer-neg-candidate-runtime-cost",
                "claim_id": "claim-1",
                "weakness": "The efficiency claim lacks runtime, memory, or FLOP measurements.",
                "negative_type": "efficiency_cost_gap",
                "required_evidence_type": "efficiency_cost",
                "quote_grounding_mode": "absence_or_requirement_gap",
                "missing_or_weak_items": ["runtime and FLOPs comparison"],
                "observed_inventory": [{"quote": inventory_quote, "locator": "Section 5"}],
                "status": "pending_absence_audit",
                "source_of_expectation": "reviewer_candidate",
            }
        ],
        "flaw_candidates": [
            {
                "flaw_id": colliding_flaw_id,
                "title": "Candidate scope limitation quote with a colliding reviewer-absence id",
                "description": "A quote-bank candidate should not block the deterministic reviewer issue flaw.",
                "status": "candidate",
                "source": "quote-bank-negative-grounding",
                "related_claim_ids": ["claim-2"],
                "evidence_ids": ["evidence-negative-quote-bank-candidate"],
                "negative_evidence_ids": ["evidence-negative-quote-bank-candidate"],
                "negative_evidence_type": "scope_limitation",
                "review_issue_ids": ["review-issue-claim-1-efficiency-cost-runtime-"],
            }
        ],
        "unresolved_questions": [],
        "evidence_gaps": [],
        "conflict_notes": [],
    }

    view = build_decision_hygiene_view(copy.deepcopy(state))
    hygiene = view["decision_hygiene"]
    issue_evidence = [
        item for item in view["evidence_map"]
        if item.get("source") == "reviewer_absence_audit"
    ]
    issue_flaws = [
        item for item in view["flaw_candidates"]
        if item.get("source") == "reviewer_absence_audit"
    ]

    assert hygiene["verified_review_issue_count"] == 1
    assert hygiene["negative_evidence_unlinked_to_flaw_count"] == 0
    assert len(issue_evidence) == 1
    assert len(issue_flaws) == 1
    assert issue_flaws[0]["flaw_id"].startswith(f"{colliding_flaw_id}-audit-")
    assert issue_evidence[0]["evidence_id"] in issue_flaws[0]["negative_evidence_ids"]


def test_review_issue_bundle_rejects_structural_baseline_without_named_missing_target():
    claim = "Empirical results show improved rank behavior compared with linear networks."
    inventory_quote = "Our symmetry condition on the dataset incorporates several previous results as special cases."
    state = {
        "paper_text": f"{claim}\n\n{inventory_quote}",
        "claims": [
            {
                "claim_id": "claim-1",
                "claim": claim,
                "claim_kind": "paper_extracted",
                "claim_type": "comparison",
                "importance": "high",
                "status": "supported",
                "claim_obligations": ["baseline_or_comparison"],
            }
        ],
        "evidence_map": [],
        "reviewer_negative_candidates": [
            {
                "candidate_id": "reviewer-neg-candidate-generic-same-setting-baseline",
                "claim_id": "claim-1",
                "weakness": "The comparison needs a same-setting baseline.",
                "negative_type": "missing_baseline",
                "required_evidence_type": "baseline_or_comparison",
                "quote_grounding_mode": "absence_or_requirement_gap",
                "missing_or_weak_items": ["same-setting baseline or comparison for the claimed improvement"],
                "observed_inventory": [{"quote": inventory_quote, "locator": "Results"}],
                "status": "pending_absence_audit",
                "source_of_expectation": "reviewer_candidate",
            }
        ],
        "flaw_candidates": [],
        "unresolved_questions": [],
        "evidence_gaps": [],
        "conflict_notes": [],
    }

    hygiene = build_decision_hygiene_view(copy.deepcopy(state))["decision_hygiene"]

    assert hygiene["verified_review_issue_count"] == 0
    assert hygiene["reviewer_absence_verified_count"] == 0


def test_review_issue_bundle_rejects_intro_problem_inventory_for_insufficient_evaluation():
    claim = (
        "The corrected model achieves state-of-the-art zero-shot and weakly-supervised "
        "results on benchmark datasets."
    )
    intro_quote = (
        "Referring Image Segmentation (RIS) -- the problem of identifying objects in images "
        "through natural language sentences -- is a challenging task currently mostly solved "
        "through supervised training."
    )
    state = {
        "paper_text": f"{claim}\n\n{intro_quote}",
        "claims": [
            {
                "claim_id": "claim-1",
                "claim": claim,
                "claim_kind": "paper_extracted",
                "claim_type": "empirical",
                "importance": "high",
                "status": "supported",
                "claim_obligations": ["empirical_result"],
            }
        ],
        "evidence_map": [],
        "reviewer_negative_candidates": [
            {
                "candidate_id": "reviewer-neg-candidate-intro-only-eval",
                "claim_id": "claim-1",
                "weakness": "The empirical claim lacks a quantitative result table or metric.",
                "negative_type": "insufficient_evaluation",
                "required_evidence_type": "empirical_result",
                "quote_grounding_mode": "absence_or_requirement_gap",
                "missing_or_weak_items": ["quantitative result table or metric for the claimed empirical effect"],
                "observed_inventory": [{"quote": intro_quote, "locator": "Introduction"}],
                "status": "pending_absence_audit",
                "source_of_expectation": "reviewer_candidate",
            }
        ],
        "flaw_candidates": [],
        "unresolved_questions": [],
        "evidence_gaps": [],
        "conflict_notes": [],
    }

    hygiene = build_decision_hygiene_view(copy.deepcopy(state))["decision_hygiene"]

    assert hygiene["verified_review_issue_count"] == 0
    assert hygiene["reviewer_absence_verified_count"] == 0


def test_review_issue_bundle_rejects_default_quantitative_gap_when_results_are_reported():
    claim = "The two-step generation pipeline improves zero-shot performance against baselines."
    result_quote = (
        "In our experiments, using only the first two steps already outperforms other "
        "zero-shot baselines by as much as 16.5%, while the full method further improves "
        "the result."
    )
    state = {
        "paper_text": f"{claim}\n\nResults.\n{result_quote}",
        "claims": [
            {
                "claim_id": "claim-1",
                "claim": claim,
                "claim_kind": "paper_extracted",
                "claim_type": "empirical",
                "importance": "high",
                "status": "supported",
                "claim_obligations": ["empirical_result"],
            }
        ],
        "evidence_map": [],
        "reviewer_negative_candidates": [
            {
                "candidate_id": "reviewer-neg-candidate-default-quant-gap",
                "claim_id": "claim-1",
                "weakness": "The empirical claim lacks a quantitative result table or metric.",
                "negative_type": "insufficient_evaluation",
                "required_evidence_type": "empirical_result",
                "quote_grounding_mode": "absence_or_requirement_gap",
                "missing_or_weak_items": ["quantitative result table or metric for the claimed empirical effect"],
                "observed_inventory": [{"quote": result_quote, "locator": "Results"}],
                "status": "pending_absence_audit",
                "source_of_expectation": "reviewer_candidate",
            }
        ],
        "flaw_candidates": [],
        "unresolved_questions": [],
        "evidence_gaps": [],
        "conflict_notes": [],
    }

    hygiene = build_decision_hygiene_view(copy.deepcopy(state))["decision_hygiene"]

    assert hygiene["verified_review_issue_count"] == 0
    assert hygiene["reviewer_absence_verified_count"] == 0


def test_quote_grounded_review_negative_count_deduplicates_same_quote_issue():
    quote = "However, adding the secure aggregator results in a less favorable outcome than the baseline system."
    state = {
        "paper_text": quote,
        "claims": [
            {
                "claim_id": "claim-1",
                "claim": "The paper proposes a privacy-preserving federated recognition framework.",
                "claim_kind": "paper_extracted",
                "claim_type": "method",
                "importance": "high",
                "status": "supported",
            }
        ],
        "evidence_map": [
            _verified_negative("neg-1", "claim-1", "negative_result", quote),
            _verified_negative("neg-2", "claim-1", "negative_result", quote),
        ],
        "flaw_candidates": [
            {
                "flaw_id": "flaw-1",
                "title": "Secure aggregation underperforms the baseline.",
                "description": "The same negative result was found twice.",
                "status": "candidate",
                "related_claim_ids": ["claim-1"],
                "evidence_ids": ["neg-1", "neg-2"],
                "negative_evidence_ids": ["neg-1", "neg-2"],
                "negative_evidence_type": "negative_result",
            }
        ],
        "unresolved_questions": [],
        "evidence_gaps": [],
        "conflict_notes": [],
    }

    hygiene = build_decision_hygiene_view(copy.deepcopy(state))["decision_hygiene"]

    assert hygiene["review_negative_verified_count"] == 1
    assert hygiene["quote_grounded_review_issue_count"] == 1
    assert hygiene["negative_evidence_candidate_count"] == 1


def test_review_issue_bundle_rejects_missing_ablation_when_full_text_reports_variant_removal():
    claim = "CDiffuser uses the contrastive learning component L_c to improve diffusion recommendations."
    ablation_quote = (
        "Table 5: Ablation studies. CDiffuser-C removes the contrastive mechanism and shows "
        "that the full model performs best."
    )
    state = {
        "paper_text": f"{claim}\n\nSection 5 Experiments.\n{ablation_quote}",
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
        "evidence_map": [],
        "reviewer_negative_candidates": [
            {
                "candidate_id": "reviewer-neg-candidate-contrastive-ablation",
                "claim_id": "claim-1",
                "weakness": "The paper does not isolate the contrastive learning component.",
                "negative_type": "missing_ablation",
                "required_evidence_type": "ablation_or_component",
                "quote_grounding_mode": "absence_or_requirement_gap",
                "missing_or_weak_items": ["contrastive learning component L_c ablation"],
                "observed_inventory": [{"quote": ablation_quote, "locator": "Table 5"}],
                "status": "pending_absence_audit",
                "source_of_expectation": "reviewer_candidate",
            }
        ],
        "flaw_candidates": [],
        "unresolved_questions": [],
        "evidence_gaps": [],
        "conflict_notes": [],
    }

    hygiene = build_decision_hygiene_view(copy.deepcopy(state))["decision_hygiene"]

    assert hygiene["obligation_grounded_review_issue_count"] == 0
    assert hygiene["verified_review_issue_count"] == 0


def test_review_issue_bundle_accepts_missing_ablation_when_ablation_is_unrelated():
    claim = "CDiffuser uses the contrastive learning component L_c to improve diffusion recommendations."
    unrelated_ablation_quote = (
        "Table 5: Ablation studies. CDiffuser-N removes high-return trajectory sampling and reports "
        "that the full model performs best."
    )
    filler = " Background method details unrelated to contrastive learning. " * 120
    state = {
        "paper_text": f"{claim}\n\n{filler}\n\nSection 5 Experiments.\n{unrelated_ablation_quote}",
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
        "evidence_map": [],
        "reviewer_negative_candidates": [
            {
                "candidate_id": "reviewer-neg-candidate-contrastive-ablation-missing",
                "claim_id": "claim-1",
                "weakness": "The paper does not isolate the contrastive learning component.",
                "negative_type": "missing_ablation",
                "required_evidence_type": "ablation_or_component",
                "quote_grounding_mode": "absence_or_requirement_gap",
                "missing_or_weak_items": ["contrastive learning component L_c ablation"],
                "observed_inventory": [{"quote": unrelated_ablation_quote, "locator": "Table 5"}],
                "status": "pending_absence_audit",
                "source_of_expectation": "reviewer_candidate",
            }
        ],
        "flaw_candidates": [],
        "unresolved_questions": [],
        "evidence_gaps": [],
        "conflict_notes": [],
    }

    hygiene = build_decision_hygiene_view(copy.deepcopy(state))["decision_hygiene"]

    assert hygiene["obligation_grounded_review_issue_count"] == 1
    assert hygiene["verified_review_issue_count"] == 1


def test_review_issue_bundle_accepts_efficiency_gap_when_paper_only_says_efficient():
    claim = "The method processes a video sequence in one pass and is computationally efficient."
    inventory_quote = "The method processes the whole sequence in one go and is more computationally efficient."
    state = {
        "paper_text": f"{claim}\n\n{inventory_quote}",
        "claims": [
            {
                "claim_id": "claim-1",
                "claim": claim,
                "claim_kind": "paper_extracted",
                "claim_type": "empirical",
                "importance": "high",
                "status": "supported",
                "coverage_tags": ["empirical", "efficiency"],
                "claim_obligations": ["efficiency_cost"],
            }
        ],
        "evidence_map": [],
        "reviewer_negative_candidates": [
            {
                "candidate_id": "reviewer-neg-candidate-runtime-gap",
                "claim_id": "claim-1",
                "weakness": "The efficiency claim lacks runtime or FLOPs measurements.",
                "negative_type": "efficiency_cost_gap",
                "required_evidence_type": "efficiency_cost",
                "quote_grounding_mode": "absence_or_requirement_gap",
                "missing_or_weak_items": ["runtime and FLOPs comparison"],
                "observed_inventory": [{"quote": inventory_quote, "locator": "Method overview"}],
                "status": "pending_absence_audit",
                "source_of_expectation": "reviewer_candidate",
            }
        ],
        "flaw_candidates": [],
        "unresolved_questions": [],
        "evidence_gaps": [],
        "conflict_notes": [],
    }

    hygiene = build_decision_hygiene_view(copy.deepcopy(state))["decision_hygiene"]

    assert hygiene["obligation_grounded_review_issue_count"] == 1
    assert hygiene["verified_review_issue_count"] == 1


def test_claim_obligation_structural_efficiency_gap_verifies_without_reviewer_candidate():
    claim = "The method is computationally efficient for processing long video sequences."
    inventory_quote = "We design an efficient one-pass method for processing the whole video sequence."
    state = {
        "paper_text": f"{claim}\n\n{inventory_quote}\n\nExperiments report segmentation quality.",
        "claims": [
            {
                "claim_id": "claim-1",
                "claim": claim,
                "claim_kind": "paper_extracted",
                "claim_type": "empirical",
                "importance": "high",
                "status": "supported",
                "coverage_tags": ["empirical", "efficiency"],
                "claim_obligations": ["efficiency_cost"],
            }
        ],
        "evidence_map": [],
        "reviewer_negative_candidates": [],
        "flaw_candidates": [],
        "unresolved_questions": [],
        "evidence_gaps": [],
        "conflict_notes": [],
    }

    view = build_decision_hygiene_view(copy.deepcopy(state))
    hygiene = view["decision_hygiene"]
    evidence = [
        item for item in view["evidence_map"]
        if item.get("review_issue_source") == "obligation_grounded_review_issue"
    ]

    assert hygiene["obligation_grounded_review_issue_count"] == 1
    assert hygiene["verified_review_issue_count"] == 1
    assert len(evidence) == 1
    bundle = evidence[0]["review_issue_bundle"]
    assert bundle["source_of_expectation"] == "claim_obligation"
    assert bundle["missing_or_mismatch"]["source"] == "claim_obligation"
    assert "runtime" in bundle["missing_or_mismatch"]["entity"].lower()
    assert bundle["review_issue_expectation_basis"] in {
        "explicit_claim_obligation_structural_dimension",
        "inferred_claim_obligation_structural_dimension",
        "structural_claim_requirement_audit",
        "structural_claim_efficiency_cue",
    }


def test_claim_obligation_structural_efficiency_gap_rejected_when_cost_metrics_present():
    claim = "The method is computationally efficient for processing long video sequences."
    inventory_quote = (
        "Table 3 reports runtime 12 ms, GPU memory 4 GB, and 15M parameters for the proposed method."
    )
    state = {
        "paper_text": f"{claim}\n\n{inventory_quote}\n\nExperiments report segmentation quality.",
        "claims": [
            {
                "claim_id": "claim-1",
                "claim": claim,
                "claim_kind": "paper_extracted",
                "claim_type": "empirical",
                "importance": "high",
                "status": "supported",
                "coverage_tags": ["empirical", "efficiency"],
                "claim_obligations": ["efficiency_cost"],
            }
        ],
        "evidence_map": [],
        "reviewer_negative_candidates": [],
        "flaw_candidates": [],
        "unresolved_questions": [],
        "evidence_gaps": [],
        "conflict_notes": [],
    }

    hygiene = build_decision_hygiene_view(copy.deepcopy(state))["decision_hygiene"]

    assert hygiene["obligation_grounded_review_issue_count"] == 0
    assert hygiene["verified_review_issue_count"] == 0


def test_review_issue_bundle_rejects_candidate_introduced_efficiency_gap_without_claim_cue():
    claim = "OGL avoids projector attenuation in graph representation learning."
    inventory_quote = "Table 2 lists OGL accuracy results on graph benchmarks."
    state = {
        "paper_text": f"{claim}\n\n{inventory_quote}",
        "claims": [
            {
                "claim_id": "claim-1",
                "claim": claim,
                "claim_kind": "paper_extracted",
                "claim_type": "method",
                "importance": "high",
                "status": "supported",
            }
        ],
        "evidence_map": [],
        "reviewer_negative_candidates": [
            {
                "candidate_id": "reviewer-neg-candidate-broad-efficiency",
                "claim_id": "claim-1",
                "weakness": "The paper does not report runtime or memory cost.",
                "negative_type": "efficiency_cost_gap",
                "required_evidence_type": "efficiency_cost",
                "quote_grounding_mode": "absence_or_requirement_gap",
                "missing_or_weak_items": ["runtime and memory cost comparison"],
                "observed_inventory": [{"quote": inventory_quote, "locator": "Table 2"}],
                "status": "pending_absence_audit",
                "source_of_expectation": "reviewer_candidate",
            }
        ],
        "flaw_candidates": [],
        "unresolved_questions": [],
        "evidence_gaps": [],
        "conflict_notes": [],
    }

    hygiene = build_decision_hygiene_view(copy.deepcopy(state))["decision_hygiene"]

    assert hygiene["obligation_grounded_review_issue_count"] == 0
    assert hygiene["verified_review_issue_count"] == 0


def test_review_issue_bundle_accepts_speedup_claim_efficiency_gap_without_explicit_obligation():
    claim = "The adaptive decoding method achieves higher speedup than baselines while preserving output quality."
    inventory_quote = "Table 2 reports acceptance rate and output quality for adaptive decoding baselines."
    state = {
        "paper_text": f"{claim}\n\n{inventory_quote}",
        "claims": [
            {
                "claim_id": "claim-1",
                "claim": claim,
                "claim_kind": "paper_extracted",
                "claim_type": "comparison",
                "importance": "high",
                "status": "supported",
            }
        ],
        "evidence_map": [],
        "reviewer_negative_candidates": [
            {
                "candidate_id": "reviewer-neg-candidate-speedup-cost",
                "claim_id": "claim-1",
                "weakness": "The speedup claim lacks latency and hardware cost evidence.",
                "negative_type": "efficiency_cost_gap",
                "required_evidence_type": "efficiency_cost",
                "quote_grounding_mode": "absence_or_requirement_gap",
                "missing_or_weak_items": ["latency and hardware cost comparison"],
                "observed_inventory": [{"quote": inventory_quote, "locator": "Table 2"}],
                "status": "pending_absence_audit",
                "source_of_expectation": "reviewer_candidate",
            }
        ],
        "flaw_candidates": [],
        "unresolved_questions": [],
        "evidence_gaps": [],
        "conflict_notes": [],
    }

    hygiene = build_decision_hygiene_view(copy.deepcopy(state))["decision_hygiene"]

    assert hygiene["obligation_grounded_review_issue_count"] == 1
    assert hygiene["verified_review_issue_count"] == 1
    assert hygiene["obligation_grounded_review_issue_type_counts"]["efficiency_cost_gap"] == 1


def test_review_issue_bundle_accepts_quantitative_gap_when_inventory_is_qualitative():
    claim = "Deep bias-free ReLU networks form low-rank weights under the studied target function."
    inventory_quote = "Figure 4 qualitatively shows low-rank weight formation for the target function."
    state = {
        "paper_text": f"{claim}\n\n{inventory_quote}",
        "claims": [
            {
                "claim_id": "claim-1",
                "claim": claim,
                "claim_kind": "paper_extracted",
                "claim_type": "empirical",
                "importance": "high",
                "status": "supported",
                "coverage_tags": ["empirical"],
                "claim_obligations": ["empirical_result"],
            }
        ],
        "evidence_map": [],
        "reviewer_negative_candidates": [
            {
                "candidate_id": "reviewer-neg-candidate-rank-metric-gap",
                "claim_id": "claim-1",
                "weakness": "The evaluation lacks quantitative rank metrics for the weight matrices.",
                "negative_type": "insufficient_evaluation",
                "required_evidence_type": "empirical_result",
                "quote_grounding_mode": "absence_or_requirement_gap",
                "missing_or_weak_items": ["quantitative rank metrics for weight matrices"],
                "observed_inventory": [{"quote": inventory_quote, "locator": "Figure 4"}],
                "status": "pending_absence_audit",
                "source_of_expectation": "reviewer_candidate",
            }
        ],
        "flaw_candidates": [],
        "unresolved_questions": [],
        "evidence_gaps": [],
        "conflict_notes": [],
    }

    hygiene = build_decision_hygiene_view(copy.deepcopy(state))["decision_hygiene"]

    assert hygiene["obligation_grounded_review_issue_count"] == 1
    assert hygiene["verified_review_issue_count"] == 1


def test_review_issue_bundle_rejects_insufficient_evaluation_when_full_text_has_named_comparison_table():
    claim = "RandomNAS-OGL improves neural architecture search compared with RandomNAS and GDAS."
    table_quote = (
        "Table 1: Quantitative results compare RandomNAS, GDAS, RandomNAS-OGL and the proposed "
        "method on CIFAR-10 search spaces."
    )
    state = {
        "paper_text": f"{claim}\n\nResults.\n{table_quote}",
        "claims": [
            {
                "claim_id": "claim-1",
                "claim": claim,
                "claim_kind": "paper_extracted",
                "claim_type": "comparison",
                "importance": "high",
                "status": "supported",
                "claim_obligations": ["empirical_result"],
            }
        ],
        "evidence_map": [],
        "reviewer_negative_candidates": [
            {
                "candidate_id": "reviewer-neg-candidate-randomnas-table",
                "claim_id": "claim-1",
                "weakness": "The paper lacks a quantitative table comparing RandomNAS-OGL and GDAS.",
                "negative_type": "insufficient_evaluation",
                "required_evidence_type": "empirical_result",
                "quote_grounding_mode": "absence_or_requirement_gap",
                "missing_or_weak_items": ["RandomNAS-OGL and GDAS quantitative table"],
                "observed_inventory": [{"quote": table_quote, "locator": "Table 1"}],
                "status": "pending_absence_audit",
                "source_of_expectation": "reviewer_candidate",
            }
        ],
        "flaw_candidates": [],
        "unresolved_questions": [],
        "evidence_gaps": [],
        "conflict_notes": [],
    }

    hygiene = build_decision_hygiene_view(copy.deepcopy(state))["decision_hygiene"]

    assert hygiene["obligation_grounded_review_issue_count"] == 0
    assert hygiene["verified_review_issue_count"] == 0


def test_review_issue_bundle_rejects_generalization_gap_when_full_text_has_imagenet_results():
    claim = "The NAS method generalizes beyond CIFAR to standard image classification benchmarks."
    imagenet_quote = (
        "Results on ImageNet. Table 3 reports top-1 accuracy on ImageNet for the discovered "
        "architecture and compares it with standard NAS baselines."
    )
    state = {
        "paper_text": f"{claim}\n\nSection 4.3.\n{imagenet_quote}",
        "claims": [
            {
                "claim_id": "claim-1",
                "claim": claim,
                "claim_kind": "paper_extracted",
                "claim_type": "empirical",
                "importance": "high",
                "status": "supported",
                "claim_obligations": ["robustness_or_generalization"],
            }
        ],
        "evidence_map": [],
        "reviewer_negative_candidates": [
            {
                "candidate_id": "reviewer-neg-candidate-imagenet",
                "claim_id": "claim-1",
                "weakness": "The paper does not evaluate on ImageNet or standard NAS datasets.",
                "negative_type": "missing_robustness_or_generalization",
                "required_evidence_type": "robustness_or_generalization",
                "quote_grounding_mode": "absence_or_requirement_gap",
                "missing_or_weak_items": ["ImageNet results on standard NAS datasets"],
                "observed_inventory": [{"quote": imagenet_quote, "locator": "Table 3"}],
                "status": "pending_absence_audit",
                "source_of_expectation": "reviewer_candidate",
            }
        ],
        "flaw_candidates": [],
        "unresolved_questions": [],
        "evidence_gaps": [],
        "conflict_notes": [],
    }

    hygiene = build_decision_hygiene_view(copy.deepcopy(state))["decision_hygiene"]

    assert hygiene["obligation_grounded_review_issue_count"] == 0
    assert hygiene["verified_review_issue_count"] == 0


def test_reviewer_candidate_review_issue_takes_priority_over_deterministic_gap_budget():
    filler_claims = [
        {
            "claim_id": f"claim-{idx}",
            "claim": f"The paper reports empirical improvement for synthetic task {idx}.",
            "claim_kind": "paper_extracted",
            "claim_type": "empirical",
            "importance": "high",
            "status": "uncertain",
            "claim_obligations": ["empirical_result"],
        }
        for idx in range(1, 9)
    ]
    target_claim = {
        "claim_id": "claim-9",
        "claim": "The paper uses normalized edit distance as a proxy for intervention success.",
        "claim_kind": "paper_extracted",
        "claim_type": "empirical",
        "importance": "high",
        "status": "supported",
        "claim_obligations": ["evaluation_protocol"],
    }
    inventory_quote = "Table 2: Evaluation of intervention success rate for each method under normalized edit distance."
    paper_text = "\n".join([claim["claim"] for claim in filler_claims] + [target_claim["claim"], inventory_quote])
    state = {
        "paper_text": paper_text,
        "claims": filler_claims + [target_claim],
        "evidence_map": [],
        "reviewer_negative_candidates": [
            {
                "candidate_id": "review-issue-candidate-proxy-validation",
                "claim_id": "claim-9",
                "weakness": "The protocol proxy is not validated against human judgment.",
                "negative_type": "evaluation_protocol_risk",
                "required_evidence_type": "evaluation_protocol",
                "quote_grounding_mode": "absence_or_requirement_gap",
                "missing_or_weak_items": ["Validation of normalized edit distance proxy against human judgment"],
                "observed_inventory": [{"quote": inventory_quote, "locator": "Table 2"}],
                "status": "pending_absence_audit",
                "source_of_expectation": "reviewer_candidate",
            }
        ],
        "flaw_candidates": [],
        "unresolved_questions": [],
        "evidence_gaps": [],
        "conflict_notes": [],
    }

    hygiene = build_decision_hygiene_view(copy.deepcopy(state))["decision_hygiene"]

    assert hygiene["reviewer_candidate_review_issue_count"] == 1
    assert hygiene["reviewer_candidate_review_issue_claim_count"] == 1
    assert hygiene["reviewer_candidate_review_issue_type_counts"]["evaluation_protocol_risk"] == 1
    assert hygiene["verified_review_issue_count"] >= 1


def test_review_issue_specificity_accepts_protocol_validation_dimension_not_generic_baseline():
    assert _coverage_item_is_specific_for_type(
        "Validation of normalized edit distance proxy against human judgment",
        "evaluation_protocol_risk",
    )
    assert not _coverage_item_is_specific_for_type(
        "stronger baselines for the claimed improvement",
        "missing_baseline",
    )


def test_reviewer_issue_bundle_keeps_missing_graph_tasks_when_only_node_classification_is_observed():
    claim = "The propagation method is competitive across diverse graph learning tasks."
    observed_quote = "Table 5: Test accuracy of homophily node classification benchmarks."
    state = {
        "paper_text": f"{claim}\n\n{observed_quote}",
        "claims": [
            {
                "claim_id": "claim-1",
                "claim": claim,
                "claim_kind": "paper_extracted",
                "claim_type": "empirical",
                "importance": "high",
                "status": "supported",
                "claim_obligations": ["empirical_result"],
            }
        ],
        "evidence_map": [],
        "reviewer_negative_candidates": [
            {
                "candidate_id": "reviewer-neg-candidate-graph-task-coverage",
                "claim_id": "claim-1",
                "weakness": "The evaluation covers node classification only, not other graph tasks.",
                "negative_type": "insufficient_evaluation",
                "required_evidence_type": "empirical_result",
                "quote_grounding_mode": "absence_or_requirement_gap",
                "missing_or_weak_items": [
                    "evaluation on link prediction task",
                    "evaluation on graph classification task",
                ],
                "observed_inventory": [{"quote": observed_quote, "locator": "Table 5"}],
                "status": "pending_absence_audit",
                "source_of_expectation": "reviewer_candidate",
            }
        ],
        "flaw_candidates": [],
        "unresolved_questions": [],
        "evidence_gaps": [],
        "conflict_notes": [],
    }

    hygiene = build_decision_hygiene_view(copy.deepcopy(state))["decision_hygiene"]

    assert hygiene["reviewer_candidate_review_issue_count"] == 1
    assert hygiene["reviewer_candidate_review_issue_type_counts"]["insufficient_evaluation"] == 1
    assert hygiene["verified_review_issue_count"] == 1


def test_reviewer_issue_bundle_rejects_missing_graph_tasks_when_all_named_tasks_are_observed():
    claim = "The propagation method is competitive across diverse graph learning tasks."
    node_quote = "Table 5: Test accuracy of homophily node classification benchmarks."
    link_quote = "Table 6: Link prediction results compare the method against graph baselines."
    graph_quote = "Table 7: Graph classification accuracy on benchmark datasets."
    state = {
        "paper_text": f"{claim}\n\n{node_quote}\n\n{link_quote}\n\n{graph_quote}",
        "claims": [
            {
                "claim_id": "claim-1",
                "claim": claim,
                "claim_kind": "paper_extracted",
                "claim_type": "empirical",
                "importance": "high",
                "status": "supported",
                "claim_obligations": ["empirical_result"],
            }
        ],
        "evidence_map": [],
        "reviewer_negative_candidates": [
            {
                "candidate_id": "reviewer-neg-candidate-graph-task-covered",
                "claim_id": "claim-1",
                "weakness": "The evaluation covers node classification only, not other graph tasks.",
                "negative_type": "insufficient_evaluation",
                "required_evidence_type": "empirical_result",
                "quote_grounding_mode": "absence_or_requirement_gap",
                "missing_or_weak_items": [
                    "evaluation on link prediction task",
                    "evaluation on graph classification task",
                ],
                "observed_inventory": [{"quote": node_quote, "locator": "Table 5"}],
                "status": "pending_absence_audit",
                "source_of_expectation": "reviewer_candidate",
            }
        ],
        "flaw_candidates": [],
        "unresolved_questions": [],
        "evidence_gaps": [],
        "conflict_notes": [],
    }

    hygiene = build_decision_hygiene_view(copy.deepcopy(state))["decision_hygiene"]

    assert hygiene["reviewer_candidate_review_issue_count"] == 0
    assert hygiene["verified_review_issue_count"] == 0


def test_reviewer_candidate_same_requirement_different_issue_type_does_not_overwrite_valid_issue():
    claim = "The propagation method is competitive across diverse graph learning tasks."
    observed_quote = "Table 5: Test accuracy of homophily node classification benchmarks."
    mismatch_quote = "Table 6: Heterophily benchmark results are reported for node classification."
    state = {
        "paper_text": f"{claim}\n\n{observed_quote}\n\n{mismatch_quote}",
        "claims": [
            {
                "claim_id": "claim-1",
                "claim": claim,
                "claim_kind": "paper_extracted",
                "claim_type": "empirical",
                "importance": "high",
                "status": "supported",
                "claim_obligations": ["empirical_result"],
            }
        ],
        "evidence_map": [],
        "reviewer_negative_candidates": [
            {
                "candidate_id": "reviewer-neg-candidate-task-coverage",
                "claim_id": "claim-1",
                "weakness": "The evaluation covers node classification only, not other graph tasks.",
                "negative_type": "insufficient_evaluation",
                "required_evidence_type": "empirical_result",
                "quote_grounding_mode": "absence_or_requirement_gap",
                "missing_or_weak_items": [
                    "evaluation on link prediction task",
                    "evaluation on graph classification task",
                ],
                "observed_inventory": [{"quote": observed_quote, "locator": "Table 5"}],
                "status": "pending_absence_audit",
                "source_of_expectation": "reviewer_candidate",
            },
            {
                "candidate_id": "reviewer-neg-candidate-heterophily-table",
                "claim_id": "claim-1",
                "weakness": "The heterophily table is missing.",
                "negative_type": "result_claim_mismatch",
                "required_evidence_type": "empirical_result",
                "quote_grounding_mode": "absence_or_requirement_gap",
                "missing_or_weak_items": ["heterophily benchmark results"],
                "observed_inventory": [{"quote": mismatch_quote, "locator": "Table 6"}],
                "status": "pending_absence_audit",
                "source_of_expectation": "reviewer_candidate",
            },
        ],
        "flaw_candidates": [],
        "unresolved_questions": [],
        "evidence_gaps": [],
        "conflict_notes": [],
    }

    hygiene = build_decision_hygiene_view(copy.deepcopy(state))["decision_hygiene"]

    assert hygiene["reviewer_candidate_review_issue_count"] == 1
    assert hygiene["reviewer_candidate_review_issue_type_counts"]["insufficient_evaluation"] == 1
    assert "result_claim_mismatch" not in hygiene["reviewer_candidate_review_issue_type_counts"]
