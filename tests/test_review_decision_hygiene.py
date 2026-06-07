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
    _decision_primary_claim_ids,
    _evidence_human_anchor,
    _evidence_negative_locator_or_bucket_signal,
    _evidence_section_bucket,
    _final_strong_guard,
    _flaw_has_negative_grounding,
    _flaw_only_cites_supports,
    _fmt_audit_number,
    _is_real_paper_claim_id,
    _is_synthetic_recovery_marker_evidence_id,
    _is_system_assessment_limitation_flaw,
    _is_paper_negative_evidence_record,
    _is_grounded_paper_negative_evidence_record,
    _render_assessment_limitation_flaws,
    _render_potential_concerns,
    _report_visible_text,
    _render_strengths,
    _render_weaknesses,
    _should_promote_verified_medium_support,
    _stance_based_negative_evidence_ids,
    _strip_synthetic_recovery_markers,
    _support_survival_summary,
    build_decision_hygiene_view,
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
    state["flaw_candidates"] = [
        {
            "flaw_id": "flaw-1",
            "title": "Unsupported empirical claim",
            "description": "The primary empirical claim is contradicted by the result table.",
            "severity": "major",
            "status": "confirmed",
            "evidence_ids": ["e1"],
            "related_claim_ids": ["claim-1"],
        },
        {
            "flaw_id": "flaw-2",
            "title": "Missing baseline",
            "description": "The main comparison omits the strongest baseline.",
            "severity": "major",
            "status": "confirmed",
            "evidence_ids": ["e2"],
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
            {"evidence_id": "e1", "claim_id": "claim-1", "evidence": "Table 1 reports a 12 point improvement.", "source": "Table 1 results", "strength": "strong", "stance": "supports"},
            {"evidence_id": "e2", "claim_id": "claim-1", "evidence": "Ablation results confirm the core component drives the gain.", "source": "ablation", "strength": "strong", "stance": "supports"},
            {"evidence_id": "e3", "claim_id": "claim-1", "evidence": "Evaluation on three benchmarks improves over baselines.", "source": "evaluation", "strength": "strong", "stance": "supports"},
        ]
    }
    merged = merge_review_state(state, payload)
    assert [item["strength"] for item in merged["evidence_map"]] == ["strong", "strong", "strong"]
    view = build_decision_hygiene_view(merged)
    assert view["decision_hygiene"]["non_abstract_real_strong_support_count"] == 3
    assert infer_final_decision(merged, {}) == "reject"


def test_two_claim_empirical_support_can_drive_health_check_accept():
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
    }
    payload = {
        "evidence_map": [
            {"evidence_id": "e1", "claim_id": "claim-1", "evidence": "Table 1 reports a 12 point improvement.", "source": "Table 1 results", "strength": "strong", "stance": "supports"},
            {"evidence_id": "e2", "claim_id": "claim-1", "evidence": "Ablation results confirm the core component drives the gain.", "source": "ablation", "strength": "strong", "stance": "supports"},
            {"evidence_id": "e3", "claim_id": "claim-2", "evidence": "Evaluation on three benchmarks improves over baselines.", "source": "evaluation", "strength": "strong", "stance": "supports"},
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
    assert view["decision_hygiene"]["targetless_unresolved_deferred_count"] == 1
    assert infer_final_decision(state, {}) == "reject"


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
            {
                "evidence_id": "e2",
                "claim_id": "claim-1",
                "evidence": "Table 4 shows the baseline outperforms the proposed method on the main benchmark.",
                "source": "results",
                "strength": "strong",
                "stance": "contradicts",
                "binding_status": "bound_real_claim",
            },
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
            },
        ],
    }
    weaknesses = _render_weaknesses(state)
    assert weaknesses == ["Grounded empirical issue: The baseline comparison is missing."]


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
        "evidence_map": [
            {
                "evidence_id": "e1",
                "claim_id": "claim-1",
                "evidence": "Table 7 shows method underperforms by 4% on benchmark Y.",
                "source": "results",
                "strength": "strong",
                "stance": "contradicts",
                "binding_status": "bound_real_claim",
            }
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
                "flaw_id": "flaw-empirical",
                "title": "Baseline underperformance",
                "description": "The empirical result does not support the claimed baseline advantage.",
                "severity": "major",
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
        {"evidence_id": f"support-{idx}", "claim_id": "claim-1", "stance": "supports", "strength": "strong"}
        for idx in range(6)
    ] + [
        {"evidence_id": "negative-1", "claim_id": "claim-1", "stance": "contradicts", "strength": "medium"},
        {"evidence_id": "weak-1", "claim_id": "claim-1", "stance": "supports", "strength": "weak"},
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
    assert hygiene["semantic_weak_promotion_real_strong_count"] == 1
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
                "source": "Limitation Section",
                "quote_id": "quote-negative-1",
                "strength": "missing",
                "stance": "missing",
                "binding_status": "bound_real_claim",
                "verified_grounding_label": "paper_grounded_exact",
                "semantic_grounding_label": "semantic_negative_verified",
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
        "claims": [{"claim_id": "claim-1", "claim": "The method beats baselines.", "status": "supported"}],
        "evidence_map": [
            {
                "evidence_id": "neg-1",
                "claim_id": "claim-1",
                "evidence": "Table 3 shows the strongest baseline has higher accuracy.",
                "source": "Table 3",
                "strength": "strong",
                "stance": "contradicts",
                "binding_status": "bound_real_claim",
                "verified_grounding_label": "paper_grounded_exact",
                "verified_quote_match_type": "quote_bank_exact_substring",
                "semantic_grounding_label": "semantic_negative_verified",
            },
            {
                "evidence_id": "neg-2",
                "claim_id": "claim-1",
                "evidence": "Another table hints at instability.",
                "source": "Table 4",
                "strength": "medium",
                "stance": "contradicts",
                "binding_status": "bound_real_claim",
                "verified_grounding_label": "paper_grounded_normalized",
                "semantic_grounding_label": "semantic_negative_verified",
            },
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
        "claims": [{"claim_id": "claim-1", "claim": "The method is empirically adequate."}],
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
            },
            {
                "evidence_id": "e-neg-good",
                "claim_id": "claim-1",
                "evidence": "The table contradicts the claim.",
                "strength": "medium",
                "stance": "contradicts",
                "binding_status": "bound_real_claim",
                "verified_grounding_label": "paper_grounded_exact",
                "semantic_grounding_label": "semantic_support_verified",
            },
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
                "claim": "The method improves benchmark performance.",
                "status": "unsupported",
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
                "strength": "medium",
                "stance": "missing",
                "binding_status": "bound_real_claim",
                "verified_grounding_label": "paper_grounded_exact",
                "semantic_grounding_label": "semantic_negative_verified",
                "negative_evidence_type": "scope_limitation",
            },
        ],
        "flaw_candidates": [
            {
                "flaw_id": "flaw-escalated",
                "title": "Unsupported major flaw",
                "description": "The report escalated a flaw without verified negative evidence.",
                "severity": "major",
                "status": "confirmed",
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

    assert hygiene["state_contamination_count"] >= 4
    assert type_counts["unsupported_with_strong_support"] == 1
    assert type_counts["stale_gap_persistence"] == 1
    assert type_counts["unsupported_flaw_escalation"] == 1
    assert type_counts["negative_evidence_overclaim"] == 1
    assert gate_counts["real_target"] >= 2
    assert gate_counts["weak_target"] >= 2
    assert hygiene["repairable_contamination_target_count"] >= 2
    assert hygiene["conservative_contamination_target_count"] >= 2
    assert all(item.get("target_gate_label") for item in hygiene["state_contamination_targets"])


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
    assert "paper_extracted" in CLAIM_KINDS
    assert "context_synthesized" in CLAIM_KINDS
    assert "manager_fallback" in CLAIM_KINDS
    assert "recovery_marker" in CLAIM_KINDS
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
        "claims": [{"claim_id": "claim-main", "status": "supported"}],
        "evidence_map": [
            {
                "evidence_id": "e-neg-1",
                "claim_id": "claim-main",
                "stance": "missing",
                "strength": "missing",
                "source": "quote-bank-negative-grounding",
                "support_source_bucket": "limitation_or_gap",
                "negative_evidence_type": negative_type,
                "verified_grounding_label": "paper_grounded_exact",
                "semantic_grounding_label": "semantic_negative_verified",
                "binding_status": "bound_real_claim",
                "raw_quote": "The method underperforms the baseline on the main benchmark.",
            }
        ],
        "flaw_candidates": [
            {
                "flaw_id": "flaw-neg-1",
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
                "verified_grounding_label": "paper_grounded_exact",
                "semantic_grounding_label": "semantic_negative_verified",
                "negative_evidence_type": "negative_result",
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
