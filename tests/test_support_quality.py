from agent_system.environments.env_package.review.support_quality import (
    derive_claim_support_summary,
    derive_sample_support_summary,
    derive_support_quality,
    evidence_section_bucket,
    independence_group_id,
)


def test_abstract_support_is_shallow_claim_articulation():
    ev = {
        "evidence_id": "e1",
        "claim_id": "claim-1",
        "source": "Abstract",
        "evidence": "The abstract states that the method improves performance.",
        "strength": "strong",
        "stance": "supports",
        "binding_status": "bound_real_claim",
    }
    quality = derive_support_quality(ev)
    assert quality["evidence_section"] == "abstract"
    assert quality["support_role"] == "claim_articulation"
    assert quality["support_depth"] == "shallow"
    assert quality["is_abstract_only"] is True


def test_method_support_is_moderate_not_empirical():
    ev = {
        "evidence_id": "e1",
        "claim_id": "claim-1",
        "source": "Method section",
        "evidence": "The architecture defines a two-stage retrieval framework.",
        "strength": "strong",
        "stance": "supports",
        "binding_status": "bound_real_claim",
    }
    quality = derive_support_quality(ev)
    assert quality["evidence_section"] == "method"
    assert quality["support_role"] == "method_description"
    assert quality["support_depth"] == "moderate"
    assert quality["is_empirical_result"] is False


def test_result_table_and_ablation_are_deep_support():
    table_ev = {"source": "Table 2 results", "evidence": "The method outperforms baselines.", "claim_id": "claim-1"}
    ablation_ev = {"source": "Ablation study", "evidence": "Removing the module reduces performance.", "claim_id": "claim-1"}
    assert derive_support_quality(table_ev)["support_depth"] == "deep"
    assert derive_support_quality(table_ev)["is_table_or_figure_based"] is True
    assert derive_support_quality(ablation_ev)["support_depth"] == "deep"
    assert derive_support_quality(ablation_ev)["is_ablation_based"] is True


def test_theory_or_proof_support_is_deep_method_support():
    ev = {
        "source": "Theorem 2 proof",
        "evidence": "The theorem proves convergence under the stated assumptions.",
        "verified_source_bucket": "theory_or_proof",
        "claim_id": "claim-1",
        "strength": "strong",
        "stance": "supports",
    }
    quality = derive_support_quality(ev)
    assert quality["evidence_section"] == "theory_or_proof"
    assert quality["support_role"] == "theory_or_proof_support"
    assert quality["support_depth"] == "deep"
    assert quality["is_method_based"] is True
    assert quality["is_empirical_result"] is False


def test_framework_figure_is_method_not_empirical_result():
    ev = {
        "source": "Figure 1 framework overview",
        "evidence": "The figure shows the architecture pipeline, not experimental results.",
        "support_source_bucket": "result_or_experiment",
        "claim_id": "claim-1",
    }
    assert evidence_section_bucket(ev) == "method"
    assert derive_support_quality(ev)["is_empirical_result"] is False


def test_claim_matched_quote_locator_and_raw_quote_preserve_empirical_depth():
    ev = {
        "source": "paper",
        "source_locator": "Claim-matched evidence excerpt #1",
        "verified_source_bucket": "claim_match",
        "raw_quote": "Table 2: The retrieval reranker improves evidence retrieval accuracy by 12.4% over BM25 baselines.",
        "evidence": "The retrieval reranker improves evidence retrieval accuracy over BM25 baselines.",
        "claim_id": "claim-1",
        "strength": "strong",
        "stance": "supports",
        "binding_status": "bound_real_claim",
    }

    quality = derive_support_quality(ev)

    assert quality["evidence_section"] == "table_or_figure"
    assert quality["support_depth"] == "deep"
    assert quality["is_empirical_result"] is True


def test_duplicate_support_source_counts_as_one_independent_group():
    claim = {"claim_id": "claim-1"}
    evidence = [
        {"evidence_id": "e1", "claim_id": "claim-1", "source": "Table 1 results", "strength": "strong", "stance": "supports", "binding_status": "bound_real_claim"},
        {"evidence_id": "e2", "claim_id": "claim-1", "source": "Table 1 results", "strength": "strong", "stance": "supports", "binding_status": "bound_real_claim"},
        {"evidence_id": "e3", "claim_id": "claim-1", "source": "Ablation study", "strength": "strong", "stance": "supports", "binding_status": "bound_real_claim"},
    ]
    summary = derive_claim_support_summary(claim, evidence)
    assert summary["claim_real_strong_support_count"] == 3
    assert summary["claim_independent_support_group_count"] == 2
    assert summary["claim_support_depth_label"] == "deep"




def test_single_verified_empirical_support_is_claim_deep():
    claim = {"claim_id": "claim-1"}
    evidence = [
        {
            "evidence_id": "e1",
            "claim_id": "claim-1",
            "source": "paper",
            "source_locator": "Table 2",
            "raw_quote": "Table 2 shows higher F1 than the BM25 baseline.",
            "support_source_bucket": "table_or_figure",
            "strength": "strong",
            "stance": "supports",
            "binding_status": "bound_real_claim",
        }
    ]
    summary = derive_claim_support_summary(claim, evidence)
    assert summary["claim_empirical_support_count"] == 1
    assert summary["claim_independent_support_group_count"] == 1
    assert summary["claim_has_deep_evidence"] is True
    assert summary["claim_support_depth_label"] == "deep"


def test_independence_group_uses_locator_and_quote_anchor():
    base = {
        "claim_id": "claim-1",
        "source": "Results",
        "strength": "strong",
        "stance": "supports",
        "binding_status": "bound_real_claim",
    }
    ev_table1 = {**base, "source_locator": "Table 1", "quote_id": "quote-table-1"}
    ev_table2 = {**base, "source_locator": "Table 2", "quote_id": "quote-table-2"}
    ev_table1_dup = {**base, "source_locator": "Table 1", "quote_id": "quote-table-1"}

    assert independence_group_id(ev_table1) != independence_group_id(ev_table2)
    assert independence_group_id(ev_table1) == independence_group_id(ev_table1_dup)


def test_sample_summary_tracks_method_plus_result_claims():
    state = {
        "claims": [{"claim_id": "claim-1"}, {"claim_id": "claim-2"}],
        "evidence_map": [
            {"evidence_id": "e1", "claim_id": "claim-1", "source": "Method section", "strength": "strong", "stance": "supports", "binding_status": "bound_real_claim"},
            {"evidence_id": "e2", "claim_id": "claim-1", "source": "Table 1 results", "strength": "strong", "stance": "supports", "binding_status": "bound_real_claim"},
            {"evidence_id": "e3", "claim_id": "claim-2", "source": "Abstract", "strength": "strong", "stance": "supports", "binding_status": "bound_real_claim"},
        ],
    }
    summary = derive_sample_support_summary(state)
    assert summary["real_strong_support_total"] == 3
    assert summary["claims_with_method_plus_result_support"] == 1
    assert summary["claims_with_only_abstract_support"] == 1


def test_independence_group_separates_same_quote_with_different_locator_role():
    base = {
        "claim_id": "claim-1",
        "source": "Results",
        "quote_id": "quote-shared",
        "raw_quote": "The result section reports both overall accuracy and ablation effects.",
        "strength": "strong",
        "stance": "supports",
        "binding_status": "bound_real_claim",
    }
    overall = {**base, "source_locator": "Table 1", "support_source_bucket": "result_or_experiment"}
    ablation = {**base, "source_locator": "Ablation Study", "support_source_bucket": "ablation"}

    assert independence_group_id(overall) != independence_group_id(ablation)


# --- R1: empirical-admission tightening (task 1.1) ---

def test_method_quote_for_empirical_claim_is_not_admissible():
    ev = {
        "evidence_id": "e-m1",
        "claim_id": "claim-1",
        "source": "Method",
        "evidence": "We design a transformer encoder with a contrastive loss.",
        "strength": "strong",
        "stance": "supports",
        "binding_status": "bound_real_claim",
    }
    claim = {"claim_id": "claim-1", "claim_type": "empirical",
             "coverage_tags": ["empirical", "effectiveness"]}
    q = derive_support_quality(ev, claim)
    assert q["is_empirical_result"] is False
    assert q["is_empirical_admissible"] is False
    assert q["empirical_admission_block_reason"] == "method_quote_for_empirical_claim"


def test_dataset_setup_quote_is_not_admissible_empirical():
    ev = {
        "evidence_id": "e-d1",
        "claim_id": "claim-1",
        "source": "Experiments",
        "evidence": "We use the ImageNet dataset and the standard train/test split for experiments.",
        "strength": "strong",
        "stance": "supports",
        "binding_status": "bound_real_claim",
    }
    q = derive_support_quality(ev, {"claim_id": "claim-1"})
    assert q["is_empirical_admissible"] is False
    assert q["empirical_admission_block_reason"] == "dataset_setup_not_effectiveness"


def test_generic_evaluate_intent_is_not_admissible_empirical():
    ev = {
        "evidence_id": "e-g1",
        "claim_id": "claim-1",
        "source": "Experiments",
        "evidence": "We evaluate our approach on several tasks.",
        "strength": "strong",
        "stance": "supports",
        "binding_status": "bound_real_claim",
    }
    q = derive_support_quality(ev, {"claim_id": "claim-1"})
    assert q["is_empirical_admissible"] is False
    assert q["empirical_admission_block_reason"] == "generic_evaluate_intent"


def test_real_result_with_outcome_remains_admissible_empirical():
    ev = {
        "evidence_id": "e-r1",
        "claim_id": "claim-1",
        "source": "Results",
        "evidence": "Table 2 shows our method outperforms the baseline by 3.5% accuracy.",
        "strength": "strong",
        "stance": "supports",
        "binding_status": "bound_real_claim",
    }
    claim = {"claim_id": "claim-1", "claim_type": "empirical", "coverage_tags": ["empirical"]}
    q = derive_support_quality(ev, claim)
    assert q["is_empirical_result"] is True
    assert q["is_empirical_admissible"] is True
    assert q["empirical_admission_block_reason"] == ""


def test_dataset_mention_with_concrete_outcome_stays_admissible():
    # dataset wording is fine when a concrete empirical outcome is also reported
    ev = {
        "evidence_id": "e-r2",
        "claim_id": "claim-1",
        "source": "Results",
        "evidence": "On the ImageNet dataset our model reaches 81.2% top-1, surpassing prior work.",
        "strength": "strong",
        "stance": "supports",
        "binding_status": "bound_real_claim",
    }
    q = derive_support_quality(ev, {"claim_id": "claim-1"})
    assert q["is_empirical_result"] is True
    assert q["is_empirical_admissible"] is True
    assert q["empirical_admission_block_reason"] == ""


def test_comparison_support_is_deep_empirical_result_without_losing_table_bucket():
    table_ev = {
        "source": "Table 3",
        "evidence": "Table 3 compares the model against strong baselines and shows better F1.",
        "support_source_bucket": "table_or_figure",
        "claim_id": "claim-1",
    }
    comparison_ev = {
        "source": "Comparison section",
        "evidence": "The method outperforms the strongest baseline across all datasets.",
        "support_source_bucket": "comparison",
        "claim_id": "claim-1",
    }

    table_quality = derive_support_quality(table_ev)
    comparison_quality = derive_support_quality(comparison_ev)

    assert table_quality["evidence_section"] == "table_or_figure"
    assert table_quality["support_role"] == "comparison_support"
    assert comparison_quality["evidence_section"] == "result"
    assert comparison_quality["support_role"] == "comparison_support"
    assert comparison_quality["support_depth"] == "deep"
