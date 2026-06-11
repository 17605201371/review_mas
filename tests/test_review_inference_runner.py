import json

from agent_system.inference.review_runner import (
    ApiReviewGenerator,
    _apply_small_model_quote_bank_support_augmentation,
    _apply_manager_policy_fallback,
    _enforce_negative_evidence_formation_payload,
    _enforce_recovery_patch_mode_payload,
    _fallback_claim_items_from_context,
    _infer_action_from_state,
    _is_verified_negative_evidence_for_recovery,
    _resolve_prompt_template,
    build_worker_observation,
    _recovery_candidate_claim_ids,
    _resolve_use_chat_template,
    _synthesize_summary_update,
    extract_tagged_json,
    run_review_episode,
    _fallback_worker_payload,
    _fallback_recovery_patch_payload,
    _ensure_recovery_targets,
    _maybe_salvage_recovery_payload,
    _maybe_salvage_turn_level_recovery_patch,
    _negative_quote_bank_salvage_payload,
    _quote_bank_from_state_or_meta,
    _scope_evidence_ids_for_turn,
)
from agent_system.environments.env_package.review.state import (
    _classify_negative_evidence_type,
    _is_specific_locator,
    _locator_from_text_anchor,
    _normalize_evidence_gaps,
    _render_evidence_context_with_meta,
    build_turn_log,
    claim_coverage_summary,
    merge_review_state,
    normalize_review_update_payload,
    render_claim_observation,
    render_critique_observation,
    render_evidence_observation,
    parse_turn_action,
    render_manager_observation,
)
from agent_system.review_manager_policy import infer_action_from_state


def test_qwen3_model_path_enables_chat_template_by_default():
    assert _resolve_use_chat_template("/reviewF/datasets/Qwen3___5-9B", None) is True
    assert _resolve_use_chat_template("/models/llama-3", None) is False
    assert _resolve_use_chat_template("/reviewF/datasets/Qwen3___5-9B", False) is False
    assert _resolve_use_chat_template("/models/llama-3", True) is True


def test_evidence_context_uses_latex_sections_for_results_and_tables():
    paper_text = """[Instruction]: Review this paper.
Format requirements: JSON only.
--- BEGIN PAPER ---
\\title{A Method Paper}
\\begin{abstract} We propose a method and mention experiments only briefly.\\end{abstract}
\\section{1 INTRODUCTION} This paper introduces the problem.
\\section{2 METHODOLOGY} The method uses a two-stage architecture and an optimization objective.
\\section{3 EXPERIMENTS} We evaluate on three benchmark datasets against strong baselines.
Table 1: Accuracy and F1 improve by 12.4% over the strongest baseline.
\\section{4 CONCLUSION} The experiments support the proposed method.
--- END PAPER ---"""

    context, meta = _render_evidence_context_with_meta({"paper_text": paper_text}, max_length=1800)

    assert meta["evidence_context_mode"] == "section_aware_claim_v3"
    assert meta["evidence_context_cleaned_wrapper"] is True
    assert "Format requirements" not in context
    assert "[results]" in context
    assert "[table_or_figure]" in context
    assert "[method]" in context
    assert "12.4%" in context
    assert meta["evidence_context_contains_results"] is True
    assert meta["evidence_context_contains_table_or_figure"] is True
    assert meta["evidence_context_contains_method"] is True


def test_evidence_context_prioritizes_target_claim_terms():
    paper_text = r"""--- BEGIN PAPER ---
Abstract: The paper proposes a general method.
\section{2 Method} The method includes a retrieval reranker trained with a contrastive objective.
\section{3 Experiments} We evaluate on BenchX and GenericSet. Table 1: GenericSet improves by 2.1%.
Table 2: The retrieval reranker improves evidence retrieval accuracy by 12.4% over BM25 baselines.
--- END PAPER ---"""
    state = {
        "claims": [
            {
                "claim_id": "claim-1",
                "claim": "The retrieval reranker improves evidence retrieval accuracy over BM25 baselines.",
                "evidence_need": "Look for retrieval reranker BM25 accuracy results.",
            }
        ]
    }

    context, meta = _render_evidence_context_with_meta(
        {"paper_text": paper_text, "review_state": state},
        max_length=1800,
        state=state,
        target_claim_ids=["claim-1"],
    )
    quote_bank = meta["evidence_quote_bank"]

    assert meta["evidence_context_mode"] == "section_aware_claim_v3"
    assert meta["evidence_context_claim_query_term_count"] > 0
    assert meta["evidence_quote_bank_claim_matched_count"] > 0
    assert "retrieval reranker improves evidence retrieval accuracy" in context
    assert int(quote_bank[0].get("claim_overlap_score") or 0) > 0
    assert "retrieval reranker" in quote_bank[0]["raw_quote"].lower()
    assert any(
        item["source_bucket"] == "claim_match" and int(item.get("claim_overlap_score") or 0) > 0
        for item in quote_bank[:2]
    )




def test_quote_bank_does_not_label_abstract_performance_as_results():
    paper_text = """--- BEGIN PAPER ---
\begin{abstract} We report notable performance improvements over prior systems.\end{abstract}
\section{1 Introduction} The introduction repeats that the method improves performance.
\section{2 Method} The method uses a reranking module and training objective.
\section{3 Experiments} We evaluate on BenchX. Table 1: Accuracy improves by 12.4% over the strongest baseline.
--- END PAPER ---"""

    _context, meta = _render_evidence_context_with_meta({"paper_text": paper_text}, max_length=1800)
    quote_bank = meta["evidence_quote_bank"]
    result_quotes = [item for item in quote_bank if item["source_bucket"] == "results"]

    assert all("abstract" not in item["raw_quote"].lower() for item in result_quotes)
    assert any("12.4%" in item["raw_quote"] or "Table 1" in item["raw_quote"] for item in result_quotes + [item for item in quote_bank if item["source_bucket"] == "table_or_figure"])


def test_worker_observation_keeps_quote_bank_before_clip():
    paper_text = """[Instruction]: Review this paper.
--- BEGIN PAPER ---
\\title{A Method Paper}
\\begin{abstract} We propose a robust reranker.\\end{abstract}
\\section{1 INTRODUCTION} This paper introduces the problem.
\\section{2 METHODOLOGY} The method uses a contrastive reranking module with a supervised objective.
\\section{3 EXPERIMENTS} We evaluate on three benchmark datasets against strong baselines.
Table 1: Accuracy and F1 improve by 12.4% over the strongest baseline.
\\section{4 CONCLUSION} The experiments support the proposed method.
--- END PAPER ---"""
    task = {
        "paper_id": "paper-quote-bank-clip",
        "mode": "s4",
        "max_turns": 5,
        "user_goal": "Audit evidence grounding.",
        "paper_text": paper_text,
        "review_state": {
            "turn_id": 1,
            "dialogue_summary": "Long prior discussion. " * 600,
            "claims": [
                {
                    "claim_id": "claim-1",
                    "claim": "The method improves F1 over baselines.",
                    "status": "uncertain",
                    "importance": "high",
                    "claim_kind": "paper_extracted",
                }
            ],
            "evidence_map": [],
            "flaw_candidates": [],
            "unresolved_questions": [],
        },
        "turn_logs": [],
    }
    manager_payload = {"action_type": "verify_evidence", "target_claim_ids": ["claim-1"]}

    obs = build_worker_observation(task, manager_payload, "Evidence Agent")

    assert len(obs) <= 4200
    assert "evidence_quote_bank" in obs
    assert "quote-table-or-figure" in obs or "quote-results" in obs
    assert "Copy raw_quote exactly" in obs
    assert "12.4%" in obs
    assert "[truncated]" in obs
    assert manager_payload["evidence_quote_bank_count"] >= 1
    assert task["_latest_evidence_context_meta"]["evidence_quote_bank_count"] >= 1


def test_context_claim_fallback_uses_real_paper_claim_ids():
    prompt = """# Claim-Relevant Paper Excerpt
    The paper proposes a retrieval reranker trained with a contrastive objective.
    Experiments on BenchX show the reranker improves F1 by 12.4% over BM25.
    # Claim State Slice
    """

    claims = _fallback_claim_items_from_context(prompt, {"claims": []}, max_claims=2)

    assert claims
    assert all(not item["claim_id"].startswith("claim-context") for item in claims)
    assert all(item["claim_id"].startswith("claim-paper-context") for item in claims)
    assert all(item["claim_kind"] == "paper_extracted" for item in claims)
    assert all(item["claim_origin_kind"] == "context_synthesized" for item in claims)


def test_small_model_quote_bank_augmentation_adds_conservative_support():
    state = {
        "claims": [
            {
                "claim_id": "claim-1",
                "claim": "The reranker improves F1 over BM25 baselines.",
                "claim_type": "empirical",
                "importance": "high",
                "claim_kind": "paper_extracted",
            },
            {
                "claim_id": "claim-2",
                "claim": "The method uses a contrastive objective.",
                "claim_type": "method",
                "importance": "high",
                "claim_kind": "paper_extracted",
            },
        ],
        "evidence_map": [],
        "evidence_quote_bank": [
            {
                "quote_id": "quote-table-1",
                "source_bucket": "table_or_figure",
                "source_locator": "Table 1",
                "raw_quote": "Table 1: The reranker improves F1 by 12.4% over BM25 baselines.",
                "source_span_start": 100,
                "source_span_end": 170,
            },
            {
                "quote_id": "quote-method-1",
                "source_bucket": "method",
                "source_locator": "Section 2",
                "raw_quote": "The reranker is trained with a contrastive objective over candidate evidence passages.",
                "source_span_start": 10,
                "source_span_end": 90,
            },
        ],
    }
    payload = {"evidence_map": [], "unresolved_questions": ["Need evidence."]}
    manager = {
        "action_type": "verify_evidence",
        "effective_action_type": "verify_evidence",
        "target_claim_ids": ["claim-1", "claim-2"],
        "model_adapter_mode": "small_model",
    }
    trace = {}

    updated = _apply_small_model_quote_bank_support_augmentation(
        "Evidence Agent",
        payload,
        state,
        manager,
        trace_worker=trace,
    )

    assert updated["small_model_quote_bank_augmentation_count"] == 2
    assert trace["small_model_quote_bank_augmentation_count"] == 2
    assert len(updated["evidence_map"]) == 2
    assert {item["claim_id"] for item in updated["evidence_map"]} == {"claim-1", "claim-2"}
    assert all(item["raw_quote"] for item in updated["evidence_map"])
    assert updated["evidence_map"][0]["binding_status"] == "bound_real_claim"


def test_small_model_quote_bank_augmentation_adds_second_independent_support():
    state = {
        "claims": [
            {
                "claim_id": "claim-1",
                "claim": "The reranker improves F1 over BM25 baselines.",
                "claim_type": "empirical",
                "importance": "high",
                "claim_kind": "paper_extracted",
            },
            {
                "claim_id": "claim-2",
                "claim": "The method uses a contrastive objective.",
                "claim_type": "method",
                "importance": "medium",
                "claim_kind": "paper_extracted",
            },
        ],
        "evidence_map": [
            {
                "evidence_id": "evidence-existing-1",
                "claim_id": "claim-1",
                "stance": "supports",
                "strength": "strong",
                "quote_id": "quote-table-1",
                "raw_quote": "Table 1: F1 improves by 12.4% over BM25.",
                "binding_status": "bound_real_claim",
            }
        ],
        "evidence_quote_bank": [
            {
                "quote_id": "quote-table-1",
                "source_bucket": "table_or_figure",
                "source_locator": "Table 1",
                "raw_quote": "Table 1: F1 improves by 12.4% over BM25.",
                "source_span_start": 100,
                "source_span_end": 150,
            },
            {
                "quote_id": "quote-table-2",
                "source_bucket": "table_or_figure",
                "source_locator": "Table 2",
                "raw_quote": "Table 2: The reranker also improves accuracy by 9.8% on the held-out set.",
                "source_span_start": 200,
                "source_span_end": 280,
            },
            {
                "quote_id": "quote-method-1",
                "source_bucket": "method",
                "source_locator": "Section 2",
                "raw_quote": "The reranker is trained with a contrastive objective over candidate evidence passages.",
                "source_span_start": 300,
                "source_span_end": 390,
            },
        ],
    }
    payload = {"evidence_map": []}
    manager = {
        "action_type": "verify_evidence",
        "effective_action_type": "verify_evidence",
        "target_claim_ids": ["claim-1", "claim-2"],
        "model_adapter_mode": "small_model",
    }

    updated = _apply_small_model_quote_bank_support_augmentation(
        "Evidence Agent",
        payload,
        state,
        manager,
        trace_worker={},
    )

    claim1_quotes = {
        item.get("quote_id")
        for item in updated["evidence_map"]
        if item.get("claim_id") == "claim-1"
    }
    assert "quote-table-2" in claim1_quotes
    assert "quote-table-1" not in claim1_quotes


def test_salvaged_claim_gap_is_not_assessable_not_open():
    state = {
        "claims": [
            {
                "claim_id": "claim-paper-fallback-1",
                "claim": "The paper reports an empirical improvement.",
                "claim_type": "empirical",
                "importance": "high",
                "claim_kind": "paper_extracted",
                "claim_origin_kind": "raw_salvaged_claim_agent_output",
                "claim_origin": "malformed_claim_agent_output",
            }
        ],
        "evidence_map": [],
        "flaw_candidates": [],
        "unresolved_questions": [],
        "evidence_gaps": [],
    }

    merged = merge_review_state(state, {})

    assert merged["evidence_gaps"]
    assert merged["evidence_gaps"][0]["status"] == "not_assessable"
    assert merged["evidence_gaps"][0]["resolution"] == "diagnostic_or_salvaged_claim_without_verified_support"


def test_api_message_to_text_uses_mimo_reasoning_fallbacks():
    class Message:
        content = None
        reasoning_content = "<json>{\"decision\":\"continue\"}</json>"

    assert ApiReviewGenerator._message_to_text(Message()) == "<json>{\"decision\":\"continue\"}</json>"
    assert ApiReviewGenerator._content_to_text([{"text": "hello"}, {"content": "world"}]) == "hello\nworld"


def test_negative_recheck_worker_observation_keeps_quote_bank_before_clip():
    paper_text = """[Instruction]: Review this paper.
--- BEGIN PAPER ---
\\title{A Method Paper}
\\begin{abstract} We propose a robust reranker.\\end{abstract}
\\section{1 INTRODUCTION} This paper introduces the problem.
\\section{2 METHODOLOGY} The method uses a contrastive reranking module with a supervised objective.
\\section{3 EXPERIMENTS} We evaluate on three benchmark datasets against strong baselines.
Table 1: Accuracy and F1 improve by 12.4% over the strongest baseline.
\\section{4 CONCLUSION} The experiments support the proposed method.
--- END PAPER ---"""
    task = {
        "paper_id": "paper-negative-recheck-quote-bank-clip",
        "mode": "s4",
        "max_turns": 5,
        "user_goal": "Audit negative evidence recheck grounding.",
        "paper_text": paper_text,
        "review_state": {
            "turn_id": 4,
            "phase": "recovery",
            "phase_turn_index": 1,
            "dialogue_summary": "Long prior discussion. " * 600,
            "claims": [
                {
                    "claim_id": "claim-1",
                    "claim": "The method improves F1 over baselines.",
                    "status": "uncertain",
                    "importance": "high",
                    "claim_kind": "paper_extracted",
                }
            ],
            "evidence_map": [],
            "flaw_candidates": [],
            "unresolved_questions": [],
        },
        "turn_logs": [],
    }
    manager_payload = {
        "action_type": "request_evidence_recheck",
        "effective_action_type": "request_evidence_recheck",
        "phase": "recovery",
        "phase_turn_index": 1,
        "negative_evidence_formation_required": True,
        "focus": "Search for copied paper quotes that weaken, limit, contradict, or show missing support for the strongest real claims.",
        "rationale": "Invalid JSON payload: " + ("unterminated string " * 80),
        "target_claim_ids": ["claim-1"],
        "target_flaw_ids": ["flaw-1"],
        "target_evidence_ids": ["evidence-1"],
        "target_hypotheses": ["The gain may depend on one benchmark. " * 20],
    }

    obs = build_worker_observation(task, manager_payload, "Evidence Agent")

    assert len(obs) <= 4200
    assert "Negative Evidence Formation Mode" in obs
    assert "Targeted Review Objects" in obs
    assert "claim-1" in obs
    assert "evidence_quote_bank" in obs
    assert "Copy raw_quote exactly" in obs
    assert "12.4%" in obs
    assert "[truncated]" in obs
    assert manager_payload["evidence_quote_bank_count"] >= 1


def test_evidence_context_includes_direction_specific_quote_anchors():
    paper_text = r"""--- BEGIN PAPER ---
Abstract: We study graph reasoning and convergence.
\section{2 Method} The system uses speculative decoding with adaptive candidate length routing.
\section{3 Theory} Theorem 1 proves convergence under bounded variance assumptions.
\section{4 Experiments} We evaluate knowledge graph reasoning. Hits@10 improves by 6.2% over the baseline.
\begin{figure}
\caption{Qualitative segmentation results show improved boundary consistency.}
\end{figure}
--- END PAPER ---"""
    state = {
        "claims": [
            {
                "claim_id": "claim-1",
                "claim": "The system improves knowledge graph reasoning and has convergence guarantees.",
                "evidence_need": "knowledge graph reasoning Hits@10 convergence theorem",
            }
        ]
    }

    context, meta = _render_evidence_context_with_meta(
        {"paper_text": paper_text, "review_state": state},
        max_length=2300,
        state=state,
        target_claim_ids=["claim-1"],
    )
    quote_bank = meta["evidence_quote_bank"]
    buckets = [item["source_bucket"] for item in quote_bank]

    assert "theory_or_proof" in buckets
    assert "table_or_figure" in buckets
    assert any("Hits@10" in item["raw_quote"] or "6.2%" in item["raw_quote"] for item in quote_bank)
    assert any("Theorem 1" in item["raw_quote"] for item in quote_bank)
    assert "[theory_or_proof]" in context


def test_runner_quote_bank_prefers_latest_context_meta():
    state = {
        "evidence_quote_bank": [
            {"quote_id": "quote-negative-or-gap-1", "raw_quote": "Old global limitation quote."},
            {"quote_id": "quote-results-1", "raw_quote": "Old global result quote."},
        ],
        "_latest_evidence_context_meta": {
            "evidence_quote_bank": [
                {"quote_id": "quote-negative-or-gap-1", "raw_quote": "Latest visible limitation quote."},
                {"quote_id": "quote-claim-match-1", "raw_quote": "Latest claim-matched support quote."},
            ]
        },
    }

    quote_bank = _quote_bank_from_state_or_meta(state)

    assert [item["quote_id"] for item in quote_bank] == [
        "quote-negative-or-gap-1",
        "quote-claim-match-1",
        "quote-results-1",
    ]
    assert quote_bank[0]["raw_quote"] == "Latest visible limitation quote."


def test_select_negative_quote_bank_entries_prefers_type_diversity():
    from agent_system.inference.review_runner import _select_negative_quote_bank_entries

    state = {
        "claims": [{"claim_id": "claim-main", "claim": "The method is broadly evaluated and reproducible."}],
        "_latest_evidence_context_meta": {
            "evidence_quote_bank": [
                {
                    "quote_id": "q-neg-result",
                    "source_bucket": "negative_or_gap",
                    "negative_evidence_type": "negative_result",
                    "raw_quote": "The main result is worse than the strongest baseline.",
                },
                {
                    "quote_id": "q-neg-result-2",
                    "source_bucket": "negative_or_gap",
                    "negative_evidence_type": "negative_result",
                    "raw_quote": "The method underperforms on the second benchmark.",
                },
                {
                    "quote_id": "q-ablation",
                    "source_bucket": "negative_or_gap",
                    "negative_evidence_type": "missing_ablation",
                    "raw_quote": "The component contribution is not isolated by an ablation analysis.",
                },
                {
                    "quote_id": "q-repro",
                    "source_bucket": "negative_or_gap",
                    "negative_evidence_type": "reproducibility_gap",
                    "raw_quote": "Training details and data split details are omitted, limiting reproducibility.",
                },
                {
                    "quote_id": "q-mismatch",
                    "source_bucket": "negative_or_gap",
                    "negative_evidence_type": "result_claim_mismatch",
                    "raw_quote": "The improvements are small and not consistent across tasks.",
                },
            ]
        },
    }

    selected = _select_negative_quote_bank_entries(
        state,
        {"target_claim_ids": ["claim-main"], "target_flaw_ids": []},
        max_entries=4,
    )

    selected_types = [item["negative_evidence_type"] for item in selected]
    assert len(selected_types) == len(set(selected_types))
    assert {"missing_ablation", "reproducibility_gap", "result_claim_mismatch"}.issubset(selected_types)


def test_evidence_context_sources_only_report_rendered_snippets():
    paper_text = """--- BEGIN PAPER ---
Title: Tiny Context
Abstract: A short abstract.
\\section{2 METHODOLOGY} The method uses an architecture and objective.
\\section{3 EXPERIMENTS} We evaluate performance on benchmarks and compare baselines.
Table 2: Accuracy improves by 9.1%.
--- END PAPER ---"""

    context, meta = _render_evidence_context_with_meta({"paper_text": paper_text}, max_length=520)

    for source in meta["evidence_context_snippet_sources"]:
        assert f"[{source}]" in context
    assert meta["evidence_context_contains_table_or_figure"] == ("[table_or_figure]" in context)
    assert meta["evidence_context_contains_results"] == ("[results]" in context)


def test_evidence_context_extracts_user_paper_from_chat_wrapper():
    paper_text = json.dumps(
        [
            {"role": "system", "content": "You are an expert reviewer. Do not leak this wrapper."},
            {
                "role": "user",
                "content": (
                    "\\title{Wrapped Paper}\n"
                    "\\begin{abstract} We propose a framework. Experiments demonstrate superior performance on BenchX.\\end{abstract}\n"
                    "\\section{Experiment} Table 1 reports accuracy gains over baselines."
                ),
            },
        ]
    )

    context, meta = _render_evidence_context_with_meta({"paper_text": paper_text}, max_length=1400)

    assert meta["evidence_context_cleaned_wrapper"] is True
    assert "expert reviewer" not in context
    assert "Wrapped Paper" in context
    assert "BenchX" in context
    assert meta["evidence_context_contains_results"] is True


def test_critique_observation_exposes_evidence_aware_state_slice():
    task = {
        "paper_id": "paper-critique-context",
        "mode": "s4",
        "max_turns": 4,
        "paper_text": """--- BEGIN PAPER ---
Abstract: The method improves benchmark performance.
\\section{Experiments} Table 1 reports a 3.5x speedup on MT-Bench using H100.
--- END PAPER ---""",
        "user_goal": "Assess critique grounding.",
        "review_state": {
            "claims": [{"claim_id": "claim-1", "claim": "The method improves benchmark performance.", "status": "supported"}],
            "evidence_map": [
                {
                    "evidence_id": "e1",
                    "claim_id": "claim-1",
                    "evidence": "Table 1 reports a 3.5x speedup on MT-Bench using H100.",
                    "source": "Table 1 results",
                    "strength": "strong",
                    "stance": "supports",
                    "binding_status": "bound_real_claim",
                },
                {
                    "evidence_id": "e2",
                    "claim_id": "claim-1",
                    "evidence": "Table 2 reports a weaker result than the claimed general improvement.",
                    "source": "Table 2 results",
                    "strength": "medium",
                    "stance": "contradicts",
                }
            ],
            "flaw_candidates": [],
            "unresolved_questions": [],
            "evidence_gaps": [],
            "conflict_notes": [],
            "turn_id": 1,
        },
    }

    observation = render_critique_observation(task, {"action_type": "analyze_flaws", "target_claim_ids": ["claim-1"]})

    assert "Critique-Relevant Paper Evidence Context" in observation
    assert "target_evidence" in observation
    assert "strong_support_by_claim" in observation
    assert "negative_evidence_candidates" in observation
    assert "unlinked_negative_evidence_candidates" in observation
    assert "e1" in observation
    assert "e2" in observation
    assert "3.5x speedup" in observation


def test_critique_observation_in_challenge_mode_exposes_negative_evidence_for_unfocused_claim():
    """Mainline-Final-Integrated P0-3 regression test.

    When the recovery phase routes the manager to ``challenge_previous_hypothesis``
    and the only grounded paper-negative evidence lives on a claim that is *not*
    in ``target_claim_ids``, the critique slice must still expose that negative
    evidence; otherwise the worker would reasonably report "No verified negative
    evidence found in current state slice" and the recovery patch would be
    blocked with ``BLOCKED_BY_POLICY``.
    """

    task = {
        "paper_id": "paper-critique-p03-slice",
        "mode": "s4",
        "max_turns": 4,
        "paper_text": "--- BEGIN PAPER ---\nAbstract.\n--- END PAPER ---",
        "user_goal": "Negative evidence on a different claim must remain visible.",
        "review_state": {
            "claims": [
                {"claim_id": "claim-1", "claim": "The method improves accuracy.", "status": "supported"},
                {"claim_id": "claim-2", "claim": "The evaluation is comprehensive.", "status": "uncertain"},
            ],
            "evidence_map": [
                {
                    "evidence_id": "e1-support",
                    "claim_id": "claim-1",
                    "evidence": "Table 1 supports the improvement.",
                    "source": "Table 1",
                    "strength": "strong",
                    "stance": "supports",
                    "verified_grounding_label": "paper_grounded_exact",
                    "semantic_grounding_label": "semantic_support_verified",
                },
                {
                    "evidence_id": "e2-negative",
                    "claim_id": "claim-2",
                    "evidence": "Verified paper quote indicates a limitation in evaluation coverage.",
                    "source": "Limitations section",
                    "strength": "missing",
                    "stance": "missing",
                    "verified_grounding_label": "paper_grounded_exact",
                    "semantic_grounding_label": "semantic_support_verified",
                },
            ],
            "flaw_candidates": [],
            "unresolved_questions": [],
            "evidence_gaps": [],
            "conflict_notes": [],
            "turn_id": 4,
        },
    }

    manager_payload = {
        "action_type": "challenge_previous_hypothesis",
        "target_claim_ids": ["claim-1"],
        "target_flaw_ids": [],
        "target_evidence_ids": [],
    }

    observation = render_critique_observation(task, manager_payload)

    # The negative evidence on ``claim-2`` must still appear in the slice
    # despite ``target_claim_ids`` only pointing at ``claim-1``.
    assert "e2-negative" in observation
    assert "claim-2" in observation
    # And the supporting evidence on ``claim-1`` must remain visible.
    assert "e1-support" in observation


def test_manager_observation_exposes_negative_evidence_binding_retry_slice():
    task = {
        "paper_id": "paper-manager-negative-binding",
        "mode": "s4",
        "max_turns": 4,
        "paper_text": "--- BEGIN PAPER ---\nTable 2 contradicts the claimed improvement.\n--- END PAPER ---",
        "user_goal": "Assess negative evidence binding.",
        "review_state": {
            "claims": [{"claim_id": "claim-1", "claim": "The method improves benchmark performance.", "status": "supported"}],
            "evidence_map": [
                {
                    "evidence_id": "e-neg",
                    "claim_id": "claim-1",
                    "evidence": "Table 2 contradicts the claimed improvement.",
                    "source": "Table 2",
                    "strength": "medium",
                    "stance": "contradicts",
                }
            ],
            "flaw_candidates": [],
            "unresolved_questions": [],
            "evidence_gaps": [],
            "conflict_notes": [],
            "turn_id": 2,
        },
    }

    observation = render_manager_observation(task)

    assert "unlinked_negative_evidence_candidates" in observation
    assert "negative_evidence_binding_retry_required" in observation
    assert "e-neg" in observation
    assert "true" in observation


def test_claim_payload_normalizes_coverage_metadata_and_summary():
    normalized = normalize_review_update_payload(
        {
            "claims": [
                {
                    "claim_id": "claim-1",
                    "claim": "The proposed architecture uses a two-stage retrieval framework.",
                    "importance": "high",
                    "status": "uncertain",
                },
                {
                    "claim_id": "claim-2",
                    "claim": "Experiments on three benchmarks outperform strong baselines in F1.",
                    "importance": "high",
                    "status": "uncertain",
                    "coverage_tags": ["empirical", "comparison"],
                },
            ]
        },
        required_fields=["claims"],
    )
    assert normalized["claims"][0]["claim_type"] == "method"
    assert "method" in normalized["claims"][0]["coverage_tags"]
    assert normalized["claims"][1]["claim_type"] == "empirical"
    coverage = claim_coverage_summary({"claims": normalized["claims"]})
    assert coverage["has_method_claim"] is True
    assert coverage["has_empirical_claim"] is True


def test_merge_claims_preserves_coverage_metadata_revisions():
    state = {
        "claims": [
            {
                "claim_id": "claim-1",
                "claim": "The paper proposes a framework.",
                "importance": "high",
                "status": "uncertain",
                "claim_type": "contribution",
                "coverage_tags": ["contribution"],
                "evidence_need": "paper evidence",
            }
        ],
        "evidence_map": [],
        "flaw_candidates": [],
        "unresolved_questions": [],
        "conflict_notes": [],
        "evidence_gaps": [],
        "current_hypotheses": [],
    }
    merged = merge_review_state(
        state,
        {
            "claims": [
                {
                    "claim_id": "claim-1",
                    "claim": "The framework uses a contrastive training objective.",
                    "importance": "high",
                    "status": "uncertain",
                    "claim_type": "method",
                    "coverage_tags": ["method"],
                    "evidence_need": "method/objective evidence",
                }
            ]
        },
    )
    claim = merged["claims"][0]
    assert claim["claim_type"] == "method"
    assert claim["coverage_tags"] == ["method"]
    assert any(event["field"] == "claim_type" for event in merged["revision_log"])


def test_claim_observation_exposes_coverage_guidance():
    task = {
        "paper_id": "paper-claim-guidance",
        "paper_text": "--- BEGIN PAPER ---\nAbstract: We propose a framework.\nExperiments compare against baselines.\n--- END PAPER ---",
        "user_goal": "Assess claim coverage.",
        "mode": "s4",
        "max_turns": 4,
        "review_state": {
            "claims": [{"claim_id": "claim-1", "claim": "The paper proposes a framework.", "status": "uncertain"}],
            "evidence_map": [],
            "flaw_candidates": [],
            "unresolved_questions": [],
            "evidence_gaps": [],
            "conflict_notes": [],
            "turn_id": 1,
        },
    }
    observation = render_claim_observation(task, {"action_type": "extract_claims"})
    assert "claim_coverage_guidance" in observation
    assert "missing_tags" in observation
    assert "empirical" in observation


def test_claim_agent_empty_claim_payload_is_salvaged_from_prompt_context():
    responses = {
        "Review Manager Agent": [
            '<json>{"decision":"continue","action_type":"extract_claims","selected_agents":["Claim Agent"],"focus":"extract claims","rationale":"Start with claims.","claims":[],"evidence_map":[],"flaw_candidates":[],"unresolved_questions":[],"dialogue_summary":"Start.","recommendation":"undecided","final_decision":"undecided","final_report":""}</json>',
        ],
        "Claim Agent": [
            '<json>{"claims":[],"unresolved_questions":["What details are available?"],"dialogue_summary":"No specific claims extracted.","recommendation":"undecided"}</json>',
        ],
    }
    call_counts = {key: 0 for key in responses}

    def fake_generate(agent_id: str, prompt: str) -> str:
        idx = call_counts[agent_id]
        call_counts[agent_id] += 1
        return responses[agent_id][idx]

    result = run_review_episode(
        extras={
            "paper_id": "paper-empty-claim-salvage",
            "paper_text": (
                "\\begin{abstract} In this paper, we propose Orca, a framework for training "
                "role-playing language models by integrating personality traits. Orca comprises "
                "four stages for personality inference, data augmentation, dataset construction, "
                "and personality-conditioned instruction tuning. Experiments demonstrate superior "
                "performance on OrcaBench. \\end{abstract}"
            ),
            "user_goal": "Extract claims even when the model returns an empty claim payload.",
            "data_source": "unit-test",
        },
        mode="s4",
        generate_fn=fake_generate,
        max_turns=1,
        max_workers_per_turn=1,
    )

    claims = result["review_state"]["claims"]
    assert claims
    assert all(not claim["claim_id"].startswith("claim-fallback") for claim in claims)
    assert any(claim["claim_type"] in {"contribution", "method", "empirical"} for claim in claims)
    assert result["runner_trace"][0]["worker_calls"][0]["fallback_payload"]["claims"]


def test_claim_agent_context_parse_fallback_is_capped_to_two_claims():
    prompt = """# Claim-Relevant Paper Excerpt
[abstract] We propose a new framework for adaptive retrieval-augmented generation in long-context settings.
[method] The framework uses a two-stage reranking method to select and compress supporting passages.
[results] Experiments on three benchmarks demonstrate improved accuracy over strong retrieval baselines.
[limitations] The method is limited to English scientific documents and requires expensive preprocessing.
# Claim State Slice
No claims yet.
"""

    payload = _fallback_worker_payload(
        "Claim Agent",
        "{malformed-json}",
        {"claims": []},
        manager_payload={"action_type": "extract_claims"},
        prompt_text=prompt,
    )

    assert payload is not None
    assert len(payload["claims"]) == 2
    assert all(claim["claim_id"].startswith("claim-paper-context") for claim in payload["claims"])
    assert all(claim["claim_kind"] == "paper_extracted" for claim in payload["claims"])
    assert all(claim["claim_origin_kind"] == "context_synthesized" for claim in payload["claims"])
    assert all(claim["claim_origin"] == "context_derived_paper_excerpt" for claim in payload["claims"])


def test_claim_payload_augments_missing_empirical_claim_from_prompt_context():
    responses = {
        "Review Manager Agent": [
            '<json>{"decision":"continue","action_type":"extract_claims","selected_agents":["Claim Agent"],"focus":"extract claims","rationale":"Start with claims.","claims":[],"evidence_map":[],"flaw_candidates":[],"unresolved_questions":[],"dialogue_summary":"Start.","recommendation":"undecided","final_decision":"undecided","final_report":""}</json>',
        ],
        "Claim Agent": [
            '<json>{"claims":[{"claim_id":"claim-1","claim":"The paper proposes Orca for role-playing language models.","importance":"high","status":"uncertain","claim_type":"contribution","coverage_tags":["contribution"],"evidence_need":"method evidence"}],"unresolved_questions":["Which experiments support Orca?"],"dialogue_summary":"Contribution claim extracted.","recommendation":"undecided"}</json>',
        ],
    }
    call_counts = {key: 0 for key in responses}

    def fake_generate(agent_id: str, prompt: str) -> str:
        idx = call_counts[agent_id]
        call_counts[agent_id] += 1
        return responses[agent_id][idx]

    result = run_review_episode(
        extras={
            "paper_id": "paper-empirical-claim-augmentation",
            "paper_text": (
                "\\begin{abstract} In this paper, we propose Orca, a framework for role-playing "
                "language models by integrating personality traits. Orca comprises four stages "
                "for data augmentation and personality-conditioned instruction tuning. We introduce "
                "OrcaBench, a benchmark for evaluating generated social-platform content. Experiments "
                "demonstrate superior performance on OrcaBench. \\end{abstract}"
            ),
            "user_goal": "Ensure claim extraction includes empirical coverage.",
            "data_source": "unit-test",
        },
        mode="s4",
        generate_fn=fake_generate,
        max_turns=1,
        max_workers_per_turn=1,
    )

    claims = result["review_state"]["claims"]
    assert len(claims) >= 2
    assert any(claim["claim_type"] == "empirical" for claim in claims)
    assert any("empirical" in claim["coverage_tags"] for claim in claims)


def test_scope_evidence_ids_rewrites_negative_evidence_ids():
    payload = {
        "evidence_map": [
            {
                "evidence_id": "evidence-1",
                "claim_id": "claim-1",
                "evidence": "Table 3 contradicts the claim.",
                "source": "Table 3",
                "strength": "medium",
                "stance": "contradicts",
            }
        ],
        "flaw_candidates": [
            {
                "flaw_id": "flaw-1",
                "title": "Underperformance",
                "description": "Table 3 contradicts the claim.",
                "severity": "major",
                "status": "confirmed",
                "related_claim_ids": ["claim-1"],
                "evidence_ids": ["evidence-1"],
                "negative_evidence_ids": ["evidence-1"],
            }
        ],
    }

    scoped = _scope_evidence_ids_for_turn(payload, 4)

    assert scoped["evidence_map"][0]["evidence_id"] == "evidence-1-turn-4"
    assert scoped["flaw_candidates"][0]["evidence_ids"] == ["evidence-1-turn-4"]
    assert scoped["flaw_candidates"][0]["negative_evidence_ids"] == ["evidence-1-turn-4"]

def test_extract_tagged_json_accepts_valid_response():
    payload = extract_tagged_json(
        '<think>Summarize claims.</think><json>{"decision":"continue","selected_agents":["Claim Agent"]}</json>'
    )
    assert payload["decision"] == "continue"
    assert payload["selected_agents"] == ["Claim Agent"]




def test_extract_tagged_json_skips_empty_echoed_tag_and_uses_later_payload():
    raw = (
        'Output contract: output exactly one <json></json> block.\n'
        '<json>{"evidence_map":[{"evidence_id":"evidence-1","claim_id":"claim-1"}],'
        '"dialogue_summary":"ok","recommendation":"undecided"}</json>'
    )
    payload = extract_tagged_json(raw)
    assert payload["evidence_map"][0]["claim_id"] == "claim-1"


def test_extract_tagged_json_chooses_schema_payload_over_nested_item():
    raw = (
        'preface {"evidence_id":"nested","claim_id":"claim-x"} '
        '{"evidence_map":[{"evidence_id":"evidence-1","claim_id":"claim-1"}],'
        '"unresolved_questions":[],"dialogue_summary":"ok","recommendation":"undecided"}'
    )
    payload = extract_tagged_json(raw)
    assert "evidence_map" in payload
    assert payload["evidence_map"][0]["evidence_id"] == "evidence-1"


def test_evidence_fallback_blocks_prompt_contract_echo():
    payload = _fallback_worker_payload(
        agent_id="Evidence Agent",
        raw_text="Output contract: - Output exactly one strict JSON object inside one <json>",
        state={"claims": [{"claim_id": "claim-main"}], "evidence_map": [], "flaw_candidates": []},
        manager_payload={"action_type": "verify_evidence", "target_claim_ids": ["claim-main"]},
    )

    assert payload["evidence_map"] == []
    assert payload["unresolved_questions"]

def test_run_review_episode_completes_with_fake_generator():
    responses = {
        "Review Manager Agent": [
            '<think>Route to specialist.</think><json>{"decision":"continue","selected_agents":["Claim Agent"],"focus":"main contribution","rationale":"Need the central claim first","dialogue_summary":"Start with the main contribution.","unresolved_questions":["What is the core claim?"],"claims":[],"evidence_map":[],"flaw_candidates":[],"recommendation":"undecided","final_decision":"undecided","final_report":""}</json>',
            '<think>Finalize after enough evidence.</think><json>{"decision":"finalize","selected_agents":[],"focus":"wrap up","rationale":"Enough signal to decide","dialogue_summary":"The main claim is clear but support is limited.","unresolved_questions":["Ablations are still missing."],"claims":[],"evidence_map":[],"flaw_candidates":[],"recommendation":"reject","final_decision":"reject","final_report":"Final Decision: Reject\\n\\nThe paper has a clear main idea, but the evidence remains too limited for acceptance."}</json>',
        ],
        "Claim Agent": [
            '<think>Extract the main claim.</think><json>{"claims":[{"claim_id":"claim-main","claim":"The method improves retrieval accuracy.","importance":"high","status":"uncertain","claim_type":"empirical","coverage_tags":["empirical","method"],"evidence_need":"result/table evidence"},{"claim_id":"claim-method","claim":"The paper proposes a retrieval model architecture.","importance":"medium","status":"uncertain","claim_type":"method","coverage_tags":["method"],"evidence_need":"method evidence"},{"claim_id":"claim-scope","claim":"The reported gains may depend on evaluation scope.","importance":"medium","status":"uncertain","claim_type":"limitation_or_boundary","coverage_tags":["limitation","scope"],"evidence_need":"scope/limitation evidence"}],"unresolved_questions":["Where is the strongest evidence for the gain?"],"dialogue_summary":"The main claim has been extracted.","recommendation":"undecided"}</json>'
        ],
    }
    call_counts = {key: 0 for key in responses}

    def fake_generate(agent_id: str, prompt: str) -> str:
        idx = call_counts[agent_id]
        call_counts[agent_id] += 1
        return responses[agent_id][idx]

    result = run_review_episode(
        extras={
            "paper_id": "paper-1",
            "paper_text": "The paper proposes a retrieval model and reports gains.",
            "user_goal": "Determine whether the main claim is supported.",
            "data_source": "unit-test",
            "ground_truth_decision": "reject",
            "reference_review": "Final Decision: Reject",
        },
        mode="s4",
        generate_fn=fake_generate,
        max_turns=2,
        max_workers_per_turn=1,
    )

    assert result["done"] is True
    assert result["review_state"]["turn_id"] == 2
    assert result["final_decision"] == "reject"
    assert result["review_state"]["final_decision"] == "reject"
    assert "Review Diagnostic Report" in result["final_report"]
    assert "7. Audit Trace" not in result["final_report"]
    assert "binary_decision" not in result["final_report"]
    assert "Final Decision:" not in result["final_report"]
    assert isinstance(result["review_state"].get("state_audit"), dict)
    assert len(result["turn_logs"]) == 2
    assert "revision_log" in result["review_state"]
    assert "conflict_notes" in result["review_state"]
    assert "evidence_gaps" in result["review_state"]
    assert "current_hypotheses" in result["review_state"]
    assert "revision_summary" in result["review_state"]
    assert isinstance(result["review_state"]["revision_summary"], list)
    assert "conflict_summary" in result["review_state"]
    assert isinstance(result["review_state"]["conflict_summary"], list)
    assert "risk_profile" in result["review_state"]
    assert "revision_events" in result["turn_logs"][0]
    assert "revised_entities" in result["turn_logs"][0]
    assert "conflict_events" in result["turn_logs"][0]
    assert "revision_summary" in result["turn_logs"][0]
    assert "conflict_summary" in result["turn_logs"][0]
    assert "risk_profile" in result["turn_logs"][0]
    assert all("reason" in event for event in result["review_state"]["revision_log"])


def test_run_review_episode_turn_logs_expose_revision_narrative_fields():
    responses = {
        "Review Manager Agent": [
            '<json>{"decision":"continue","action_type":"extract_claims","selected_agents":["Claim Agent"],"focus":"extract claims","rationale":"Start with the main claim.","dialogue_summary":"Start with claims.","unresolved_questions":["What evidence supports the claim?"],"claims":[],"evidence_map":[],"flaw_candidates":[],"recommendation":"undecided","final_decision":"undecided","final_report":""}</json>',
            '<json>{"decision":"continue","action_type":"analyze_flaws","selected_agents":["Critique Agent"],"focus":"analyze flaws","rationale":"Convert the current concern into a flaw candidate.","dialogue_summary":"Analyze flaw candidates.","unresolved_questions":["Is the claim overstated?"],"claims":[],"evidence_map":[],"flaw_candidates":[],"recommendation":"undecided","final_decision":"undecided","final_report":""}</json>',
            '<json>{"decision":"continue","action_type":"analyze_flaws","selected_agents":["Critique Agent"],"focus":"downgrade flaw","rationale":"Re-check whether the earlier flaw still holds.","dialogue_summary":"Downgrade the earlier flaw after review.","unresolved_questions":["Does the flaw still hold?"],"claims":[],"evidence_map":[],"flaw_candidates":[],"recommendation":"undecided","final_decision":"undecided","final_report":""}</json>',
            '<json>{"decision":"continue","action_type":"analyze_flaws","selected_agents":["Critique Agent"],"focus":"re-evaluate flaw","rationale":"Recovery re-evaluation of the earlier flaw.","dialogue_summary":"Recovery re-evaluation.","unresolved_questions":["Does the flaw still hold?"],"claims":[],"evidence_map":[],"flaw_candidates":[],"recommendation":"undecided","final_decision":"undecided","final_report":""}</json>',
            '<json>{"decision":"finalize","action_type":"finalize","selected_agents":[],"focus":"wrap up","rationale":"Enough structured state exists.","dialogue_summary":"Finalize the review.","unresolved_questions":["Does the flaw still hold?"],"claims":[],"evidence_map":[],"flaw_candidates":[],"recommendation":"reject","final_decision":"reject","final_report":"Final Decision: Reject\\n\\nThe claim is only weakly supported after rechecking the earlier flaw."}</json>',
        ],
        "Claim Agent": [
            '<json>{"claims":[{"claim_id":"claim-main","claim":"The method substantially improves retrieval accuracy.","importance":"high","status":"uncertain","claim_type":"empirical","coverage_tags":["empirical","method"],"evidence_need":"result/table evidence"},{"claim_id":"claim-method","claim":"The paper uses a retrieval model design to improve accuracy.","importance":"medium","status":"uncertain","claim_type":"method","coverage_tags":["method"],"evidence_need":"method evidence"},{"claim_id":"claim-scope","claim":"The improvement claim may be sensitive to evaluation scope.","importance":"medium","status":"uncertain","claim_type":"limitation_or_boundary","coverage_tags":["limitation","scope"],"evidence_need":"scope/limitation evidence"}],"unresolved_questions":["What evidence supports the main claim?"],"dialogue_summary":"Main claim extracted.","recommendation":"undecided"}</json>'
        ],
        "Evidence Agent": [
            '<json>{"evidence_map":[{"evidence_id":"evidence-1","claim_id":"claim-main","evidence":"Table 3 shows weaker gains than expected.","source":"Table 3","strength":"weak","stance":"contradicts"}],"conflict_notes":[{"note":"Table 3 contradicts the main claim.","claim_id":"claim-main","evidence_id":"evidence-1","conflict_type":"evidence_conflict"}],"dialogue_summary":"Contradictory evidence found.","recommendation":"undecided"}</json>',
            '<json>{"evidence_map":[{"evidence_id":"evidence-1","claim_id":"claim-main","evidence":"After re-evaluation, Table 3 still shows weak gains.","source":"Table 3","strength":"weak","stance":"contradicts"}],"conflict_notes":[{"note":"Re-evaluation confirms Table 3 contradicts the main claim.","claim_id":"claim-main","evidence_id":"evidence-1","conflict_type":"evidence_conflict"}],"dialogue_summary":"Re-evaluation confirms contradiction.","recommendation":"undecided"}</json>'
        ],
        "Critique Agent": [
            '<json>{"flaw_candidates":[{"flaw_id":"flaw-main","title":"Possible overclaim","description":"The empirical support for the main claim looks limited.","severity":"major","status":"candidate","related_claim_ids":["claim-main"],"evidence_ids":[],"confidence":0.6}],"conflict_notes":[{"conflict_id":"conflict-main","note":"The claim may be overstated relative to the available evidence.","claim_id":"claim-main","evidence_id":"","flaw_id":"flaw-main"}],"dialogue_summary":"A candidate flaw was added.","recommendation":"undecided"}</json>',
            '<json>{"flaw_candidates":[{"flaw_id":"flaw-main","title":"Possible overclaim","description":"Recovery re-evaluation: evidence still weak but flaw severity may be overstated.","severity":"minor","status":"candidate","related_claim_ids":["claim-main"],"evidence_ids":[],"confidence":0.5}],"dialogue_summary":"Recovery re-evaluation of the flaw.","recommendation":"undecided"}</json>',
            '<json>{"claims":[{"claim_id":"claim-main","claim":"The method substantially improves retrieval accuracy.","importance":"high","status":"supported"}],"flaw_candidates":[{"flaw_id":"flaw-main","title":"Possible overclaim","description":"The empirical support now looks less problematic after recheck.","severity":"major","status":"downgraded","related_claim_ids":["claim-main"],"evidence_ids":[],"confidence":0.4}],"dialogue_summary":"The earlier flaw was downgraded after review.","recommendation":"undecided"}</json>'
        ],
    }
    call_counts = {key: 0 for key in responses}

    def fake_generate(agent_id: str, prompt: str) -> str:
        idx = call_counts[agent_id]
        call_counts[agent_id] += 1
        return responses[agent_id][idx]

    result = run_review_episode(
        extras={
            "paper_id": "paper-log-narrative",
            "paper_text": "The paper reports a substantial retrieval gain with limited discussion of supporting evidence.",
            "user_goal": "Trace how the review state adds and revises flaws.",
            "data_source": "unit-test",
            "ground_truth_decision": "reject",
            "reference_review": "Final Decision: Reject",
        },
        mode="s4",
        generate_fn=fake_generate,
        max_turns=5,
        max_workers_per_turn=1,
    )

    assert result["done"] is True
    assert result["final_decision"] == "reject"
    assert len(result["turn_logs"]) >= 3

    claim_turn = result["turn_logs"][0]
    flaw_turn = result["turn_logs"][1]

    assert "claim:claim-main" in claim_turn["new_items"]
    assert any(item.startswith("flaw:flaw-main") for item in flaw_turn["new_items"])
    assert flaw_turn["conflicts_detected"]
    assert any("overstated" in note.lower() for note in flaw_turn["conflicts_detected"])

    recovery_turns = [tl for tl in result["turn_logs"] if tl.get("phase_after_action") == "recovery"]
    assert recovery_turns
    assert all(tl.get("phase_turn_index", 0) >= 1 for tl in recovery_turns)
    assert all(tl.get("action_type") in {"request_evidence_recheck", "challenge_previous_hypothesis"} for tl in recovery_turns)
    assert result["turn_logs"][-1]["phase_after_action"] in {"normal_review", "recovery"}


def test_run_review_episode_overrides_premature_finalize():
    responses = {
        "Review Manager Agent": [
            '<json>{"decision":"finalize","action_type":"finalize","selected_agents":[],"focus":"stop early","rationale":"I think this is enough.","dialogue_summary":"","unresolved_questions":[],"claims":[],"evidence_map":[],"flaw_candidates":[],"recommendation":"reject","final_decision":"reject","final_report":"Final Decision: Reject"}</json>',
            '<json>{"decision":"finalize","action_type":"finalize","selected_agents":[],"focus":"stop after cap","rationale":"Stop after the forced continuation.","dialogue_summary":"","unresolved_questions":[],"claims":[],"evidence_map":[],"flaw_candidates":[],"recommendation":"reject","final_decision":"reject","final_report":"Final Decision: Reject"}</json>',
        ],
    }
    call_counts = {key: 0 for key in responses}

    def fake_generate(agent_id: str, prompt: str) -> str:
        idx = call_counts[agent_id]
        call_counts[agent_id] += 1
        return responses[agent_id][idx]

    result = run_review_episode(
        extras={
            "paper_id": "paper-finalize-guard",
            "paper_text": "A paper with almost no structured analysis yet.",
            "user_goal": "Do not finalize until the state is complete.",
            "data_source": "unit-test",
            "ground_truth_decision": "reject",
            "reference_review": "Final Decision: Reject",
        },
        mode="s2",
        generate_fn=fake_generate,
        max_turns=2,
        max_workers_per_turn=1,
    )

    assert result["runner_trace"][0]["manager_payload"]["decision"] == "continue"
    assert result["runner_trace"][0]["manager_payload"]["action_type"] != "finalize"
    assert "incomplete" in result["runner_trace"][0]["manager_payload"]["rationale"].lower()
    assert result["runner_trace"][0]["policy_source"] == "finalize_guard_override"
    assert any("Finalize was overridden" in note for note in result["runner_trace"][0]["policy_notes"])
    assert result["turn_logs"][0]["policy_source"] == "finalize_guard_override"


def test_apply_manager_policy_fallback_overrides_s3_clarification_before_claims():
    state = {
        "claims": [],
        "evidence_map": [],
        "flaw_candidates": [],
        "unresolved_questions": [{"question": "Which issue should we prioritize?", "status": "open"}],
        "risk_profile": {"open_question_count": 1, "conflict_count": 0, "readiness": "not_ready"},
        "evidence_gaps": [],
        "current_hypotheses": [],
        "clarification_needed": True,
        "pending_user_question": "Which issue should we prioritize?",
    }
    manager_payload = {
        "decision": "continue",
        "action_type": "ask_user_clarification",
        "selected_agents": [],
        "focus": "Which issue should we prioritize?",
        "rationale": "Need clarification.",
        "pending_user_question": "Which issue should we prioritize?",
        "clarification_needed": True,
    }

    normalized = _apply_manager_policy_fallback(
        manager_payload=manager_payload,
        state=state,
        mode="s3",
        worker_ids=["General Reviewer Agent 1", "General Reviewer Agent 2"],
        worker_limit=1,
        recent_turn_logs=[],
    )

    assert normalized["action_type"] == "extract_claims"
    assert normalized["policy_source"] == "s3_preclaim_clarification_override"


def test_fallback_evidence_payload_marks_contradiction_for_challenge_action():
    payload = _fallback_worker_payload(
        agent_id="Evidence Agent",
        raw_text="However, Table 3 contradicts the main claim and the reported gain looks weaker than expected.",
        state={"claims": [{"claim_id": "claim-main"}], "evidence_map": [], "flaw_candidates": []},
        manager_payload={"action_type": "challenge_previous_hypothesis", "target_claim_ids": ["claim-main"]},
    )

    assert payload["evidence_map"]
    assert payload["evidence_map"][0]["stance"] == "contradicts"
    assert payload["conflict_notes"]



def test_fallback_critique_payload_returns_recovery_patch_for_challenge_action():
    payload = _fallback_worker_payload(
        agent_id="Critique Agent",
        raw_text="The current conclusion may be overstated relative to the evidence.",
        state={
            "claims": [{"claim_id": "claim-main", "status": "uncertain"}],
            "evidence_map": [{"evidence_id": "evidence-1", "claim_id": "claim-main", "stance": "contradicts", "verified_grounding_label": "paper_grounded_exact", "semantic_grounding_label": "semantic_negative_verified"}],
            "flaw_candidates": [],
        },
        manager_payload={"action_type": "challenge_previous_hypothesis", "target_claim_ids": ["claim-main"], "target_evidence_ids": ["evidence-1"]},
    )

    assert payload["action"] == "apply_recovery_patch"
    assert payload["target_type"] == "claim"
    assert payload["target_id"] == "claim-main"
    assert payload["new_status"] == "unsupported"
    assert payload["supporting_evidence_ids"] == ["evidence-1"]


def test_recovery_targeting_excludes_system_missing_marker_for_claim_downgrade():
    state = {
        "claims": [{"claim_id": "claim-main", "status": "supported"}],
        "evidence_map": [
            {
                "evidence_id": "evidence-recovery-missing-claim-main",
                "claim_id": "claim-main",
                "stance": "missing",
                "strength": "missing",
                "source": "system recovery salvage",
            }
        ],
        "flaw_candidates": [],
    }

    payload = _ensure_recovery_targets(
        {
            "action_type": "challenge_previous_hypothesis",
            "effective_action_type": "challenge_previous_hypothesis",
            "target_claim_ids": ["claim-main"],
            "target_evidence_ids": ["evidence-recovery-missing-claim-main"],
        },
        state,
        mode="s4",
        recovery_action="challenge_previous_hypothesis",
        recent_turn_logs=[],
    )

    assert payload.get("target_claim_ids") in (None, [])


def test_recovery_targeting_retains_manager_targets_with_real_positive_evidence():
    """When manager-sanitized target claims have real evidence but no verified negative
    evidence yet, the runner should keep those claims so Critique Agent can still
    challenge them (re-interpreting positive evidence as weak), instead of dropping
    target_claim_ids to [] which forces a noisy "missing target claim ID" block.

    Regression: full39 fresh1 run (20260521) showed 5 papers blocked on
    BLOCKED_BY_POLICY because the viability filter dropped every manager-sanitized
    target. Synthetic markers are still excluded.
    """
    state = {
        "claims": [
            {"claim_id": "claim-1", "status": "supported"},
            {"claim_id": "claim-2", "status": "partially_supported"},
        ],
        "evidence_map": [
            {
                "evidence_id": "evidence-real-1",
                "claim_id": "claim-1",
                "stance": "supports",
                "strength": "strong",
                "verified_grounding_label": "paper_grounded_exact",
                "binding_status": "bound_real_claim",
            },
            {
                "evidence_id": "evidence-real-2",
                "claim_id": "claim-2",
                "stance": "partially_supports",
                "strength": "medium",
                "verified_grounding_label": "paper_grounded_exact",
                "binding_status": "bound_real_claim",
            },
        ],
        "flaw_candidates": [],
    }

    payload = _ensure_recovery_targets(
        {
            "action_type": "challenge_previous_hypothesis",
            "effective_action_type": "challenge_previous_hypothesis",
            "target_claim_ids": ["claim-1", "claim-2"],
        },
        state,
        mode="s4",
        recovery_action="challenge_previous_hypothesis",
        recent_turn_logs=[],
    )

    # Manager-sanitized targets must survive — Critique should at least be given
    # a chance to challenge claims that have real (non-synthetic) evidence.
    assert payload.get("target_claim_ids") == ["claim-1", "claim-2"]


def test_recovery_targeting_drops_manager_targets_when_only_synthetic_evidence_exists():
    """Mirror of the above: when manager-provided targets exist but their only
    evidence is a synthetic recovery-salvage missing marker (no real paper grounding),
    target_claim_ids must still drop to [] so we do not ask Critique to challenge
    a claim that has no real evidence to reason over."""
    state = {
        "claims": [{"claim_id": "claim-only-synthetic", "status": "supported"}],
        "evidence_map": [
            {
                "evidence_id": "evidence-quote-bank-gap",
                "claim_id": "claim-only-synthetic",
                "stance": "missing",
                "strength": "missing",
                "source": "quote-bank-negative-grounding",
            }
        ],
        "flaw_candidates": [],
    }

    payload = _ensure_recovery_targets(
        {
            "action_type": "challenge_previous_hypothesis",
            "effective_action_type": "challenge_previous_hypothesis",
            "target_claim_ids": ["claim-only-synthetic"],
        },
        state,
        mode="s4",
        recovery_action="challenge_previous_hypothesis",
        recent_turn_logs=[],
    )

    assert payload.get("target_claim_ids") in (None, [])


def test_fallback_recovery_patch_blocks_system_missing_marker_claim_downgrade():
    state = {
        "claims": [{"claim_id": "claim-main", "status": "supported"}],
        "evidence_map": [
            {
                "evidence_id": "evidence-recovery-missing-claim-main",
                "claim_id": "claim-main",
                "stance": "missing",
                "strength": "missing",
                "source": "system recovery salvage",
            }
        ],
        "flaw_candidates": [],
    }

    payload = _fallback_recovery_patch_payload(
        state,
        {
            "action_type": "challenge_previous_hypothesis",
            "target_claim_ids": ["claim-main"],
            "target_evidence_ids": ["evidence-recovery-missing-claim-main"],
        },
    )

    assert payload["action"] == "blocked"
    assert "No grounded contradictory evidence" in payload["blocked_reason"]


def test_recovery_candidate_claim_ids_exclude_context_salvage_claims():
    state = {
        "claims": [
            {
                "claim_id": "claim-paper-context-1",
                "status": "partially_supported",
                "claim_kind": "paper_extracted",
                "claim_origin_kind": "context_synthesized",
            },
            {"claim_id": "claim-main", "status": "partially_supported", "claim_kind": "paper_extracted"},
        ],
        "evidence_map": [
            {
                "evidence_id": "evidence-context-neg",
                "claim_id": "claim-paper-context-1",
                "stance": "contradicts",
                "strength": "strong",
                "verified_grounding_label": "paper_grounded_exact",
                "semantic_grounding_label": "semantic_negative_verified",
            },
            {
                "evidence_id": "evidence-main-neg",
                "claim_id": "claim-main",
                "stance": "contradicts",
                "strength": "strong",
                "verified_grounding_label": "paper_grounded_exact",
                "semantic_grounding_label": "semantic_negative_verified",
            },
        ],
    }

    assert _recovery_candidate_claim_ids(state, "challenge_previous_hypothesis") == ["claim-main"]


def test_fallback_recovery_patch_rebinds_weak_manager_target_to_real_claim():
    state = {
        "claims": [
            {
                "claim_id": "claim-paper-context-1",
                "status": "partially_supported",
                "claim_kind": "paper_extracted",
                "claim_origin_kind": "context_synthesized",
            },
            {"claim_id": "claim-main", "status": "partially_supported", "claim_kind": "paper_extracted"},
        ],
        "evidence_map": [
            {
                "evidence_id": "evidence-main-neg",
                "claim_id": "claim-main",
                "stance": "contradicts",
                "strength": "strong",
                "verified_grounding_label": "paper_grounded_exact",
                "semantic_grounding_label": "semantic_negative_verified",
                "source": "results",
            }
        ],
        "flaw_candidates": [],
    }

    payload = _fallback_recovery_patch_payload(
        state,
        {
            "action_type": "challenge_previous_hypothesis",
            "effective_action_type": "challenge_previous_hypothesis",
            "target_claim_ids": ["claim-paper-context-1"],
            "target_evidence_ids": [],
        },
    )

    assert payload["action"] == "apply_recovery_patch"
    assert payload["target_type"] == "claim"
    assert payload["target_id"] == "claim-main"
    assert payload["supporting_evidence_ids"] == ["evidence-main-neg"]


def _build_pattern_a_state(*, extra_negative_evidence=None, flaw_extra_evidence_ids=None):
    """Helper: contested-stable state with verified positive support and a quote-bank
    verified-negative that grounds an active candidate flaw."""
    evidence_map = [
        {
            "evidence_id": "evidence-positive-strong",
            "claim_id": "claim-main",
            "stance": "supports",
            "strength": "strong",
            "verified_grounding_label": "paper_grounded_exact",
            "semantic_grounding_label": "semantic_support_verified",
            "support_source_bucket": "table_or_figure",
        },
        {
            "evidence_id": "evidence-negative-quote-bank-quote-1-1",
            "claim_id": "claim-main",
            "stance": "missing",
            "strength": "missing",
            "verified_grounding_label": "paper_grounded_exact",
            "semantic_grounding_label": "semantic_negative_verified",
            "support_source_bucket": "limitation_or_gap",
            "source": "quote-bank-negative-grounding",
        },
    ]
    if extra_negative_evidence:
        evidence_map.extend(extra_negative_evidence)
    flaw_evidence = ["evidence-negative-quote-bank-quote-1-1"]
    if flaw_extra_evidence_ids:
        flaw_evidence = flaw_evidence + list(flaw_extra_evidence_ids)
    return {
        "claims": [{"claim_id": "claim-main", "status": "supported"}],
        "evidence_map": evidence_map,
        "flaw_candidates": [
            {
                "flaw_id": "flaw-quote-bank-1",
                "status": "candidate",
                "related_claim_ids": ["claim-main"],
                "evidence_ids": flaw_evidence,
                "negative_evidence_ids": flaw_evidence,
            }
        ],
    }


def test_fallback_recovery_patch_pattern_a_marks_quote_bank_conflict_contested():
    """Contested-stable with verified positive + quote-bank negative records a non-destructive contested relation."""
    state = _build_pattern_a_state()

    payload = _fallback_recovery_patch_payload(
        state,
        {
            "action_type": "challenge_previous_hypothesis",
            "effective_action_type": "challenge_previous_hypothesis",
            "target_claim_ids": ["claim-main"],
            "target_flaw_ids": [],
            "target_evidence_ids": [],
        },
    )

    assert payload["action"] == "apply_recovery_patch"
    assert payload["target_type"] == "flaw"
    assert payload["target_id"] == "flaw-quote-bank-1"
    assert payload["old_status"] == "candidate"
    assert payload["new_status"] == "candidate"
    assert payload["supporting_evidence_ids"] == ["evidence-negative-quote-bank-quote-1-1"]
    assert payload["recovery_patch_operation"] == "mark_contested"
    assert payload["mark_contested"] is True


def test_fallback_recovery_patch_blocks_quote_bank_limitation_no_effect_downgrade():
    state = {
        "claims": [
            {
                "claim_id": "claim-paper-fallback-2",
                "claim": "Paper-salvaged fallback claim.",
                "status": "supported",
                "claim_kind": "paper_extracted",
                "claim_origin_kind": "raw_salvaged_claim_agent_output",
            }
        ],
        "evidence_map": [
            {
                "evidence_id": "evidence-negative-scope",
                "claim_id": "claim-paper-fallback-2",
                "evidence": "The paper only evaluates this setting in a limited scope.",
                "raw_quote": "The paper only evaluates this setting in a limited scope.",
                "stance": "missing",
                "strength": "missing",
                "verified_grounding_label": "paper_grounded_exact",
                "semantic_grounding_label": "semantic_negative_verified",
                "support_source_bucket": "limitation_or_gap",
                "source": "quote-bank-negative-grounding",
                "negative_evidence_type": "scope_limitation",
            }
        ],
        "flaw_candidates": [
            {
                "flaw_id": "flaw-negative-scope",
                "status": "candidate",
                "title": "Scope limitation",
                "description": "Scope limitation",
                "severity": "minor",
                "related_claim_ids": ["claim-paper-fallback-2"],
                "evidence_ids": ["evidence-negative-scope"],
                "negative_evidence_ids": ["evidence-negative-scope"],
                "source": "quote-bank-negative-grounding",
                "negative_evidence_type": "scope_limitation",
                "grounding_status": "grounded_candidate",
            }
        ],
        "evidence_gaps": [],
        "unresolved_questions": [],
        "conflict_notes": [],
    }

    payload = _fallback_recovery_patch_payload(
        state,
        {
            "action_type": "challenge_previous_hypothesis",
            "effective_action_type": "challenge_previous_hypothesis",
            "target_claim_ids": [],
            "target_flaw_ids": ["flaw-negative-scope"],
            "target_evidence_ids": [],
        },
    )

    assert payload["action"] == "blocked"
    assert payload["target_type"] == "flaw"
    assert payload["target_id"] == "flaw-negative-scope"
    assert "no-effect recovery patch" in payload["blocked_reason"]


def test_fallback_recovery_patch_marks_paper_salvaged_claim_contested():
    state = {
        "claims": [
            {
                "claim_id": "claim-paper-fallback-2",
                "claim": "Paper-salvaged claim with verified positive and negative evidence.",
                "status": "supported",
                "claim_kind": "paper_extracted",
                "claim_origin_kind": "raw_salvaged_claim_agent_output",
            }
        ],
        "evidence_map": [
            {
                "evidence_id": "evidence-pos",
                "claim_id": "claim-paper-fallback-2",
                "evidence": "Table 2 supports the claim.",
                "raw_quote": "Table 2 supports the claim.",
                "stance": "supports",
                "strength": "strong",
                "verified_grounding_label": "paper_grounded_exact",
                "semantic_grounding_label": "semantic_support_verified",
            },
            {
                "evidence_id": "evidence-neg",
                "claim_id": "claim-paper-fallback-2",
                "evidence": "The method performs worse than a baseline in one setting.",
                "raw_quote": "The method performs worse than a baseline in one setting.",
                "stance": "missing",
                "strength": "missing",
                "support_source_bucket": "limitation_or_gap",
                "source": "quote-bank-negative-grounding",
                "negative_evidence_type": "negative_result",
                "verified_grounding_label": "paper_grounded_exact",
                "semantic_grounding_label": "semantic_negative_verified",
            },
        ],
        "flaw_candidates": [
            {
                "flaw_id": "flaw-negative-result",
                "status": "candidate",
                "title": "Verified negative result",
                "description": "Verified negative result",
                "severity": "major",
                "related_claim_ids": ["claim-paper-fallback-2"],
                "evidence_ids": ["evidence-neg"],
                "negative_evidence_ids": ["evidence-neg"],
                "source": "quote-bank-negative-grounding",
                "negative_evidence_type": "negative_result",
                "grounding_status": "verified_actionable_candidate",
            }
        ],
    }

    payload = _fallback_recovery_patch_payload(
        state,
        {
            "action_type": "challenge_previous_hypothesis",
            "effective_action_type": "challenge_previous_hypothesis",
            "target_claim_ids": ["claim-paper-fallback-2"],
            "target_flaw_ids": ["flaw-negative-result"],
            "target_evidence_ids": [],
        },
    )

    assert payload["action"] == "apply_recovery_patch"
    assert payload["target_type"] == "flaw"
    assert payload["target_id"] == "flaw-negative-result"
    assert payload["old_status"] == "candidate"
    assert payload["new_status"] == "candidate"
    assert payload["supporting_evidence_ids"] == ["evidence-neg"]
    assert payload["recovery_patch_operation"] == "mark_contested"
    assert payload["mark_contested"] is True


def test_recovery_payload_salvages_critique_emission_failure_to_patch():
    state = _build_pattern_a_state()
    state["evidence_map"][1]["semantic_grounding_label"] = "semantic_mismatch"
    state["evidence_map"][1]["negative_evidence_type"] = "scope_limitation"

    payload = _maybe_salvage_recovery_payload(
        "Critique Agent",
        {
            "action": "",
            "_emission_failure_code": "PATCH_MODE_PROMPT_IGNORED",
            "_emission_failure_message": "Recovery patch mode expected strict JSON patch output.",
        },
        state,
        manager_payload={
            "action_type": "challenge_previous_hypothesis",
            "effective_action_type": "challenge_previous_hypothesis",
            "turn_mode": "recovery_patch",
            "target_claim_ids": [],
            "target_flaw_ids": ["flaw-quote-bank-1"],
            "target_evidence_ids": ["evidence-negative-quote-bank-quote-1-1"],
        },
    )

    assert payload["action"] == "apply_recovery_patch"
    assert payload["target_type"] == "flaw"
    assert payload["target_id"] == "flaw-quote-bank-1"
    assert payload["new_status"] == "downgraded"
    assert payload["_recovery_patch_source"] == "system_salvaged"


def test_model_claim_downgrade_with_positive_support_rebuilds_to_contested_flaw():
    state = _build_pattern_a_state()
    state["evidence_map"][1]["negative_evidence_type"] = "negative_result"
    state["evidence_map"][1]["claim_status_downgrade_allowed"] = True

    payload = _maybe_salvage_recovery_payload(
        "Critique Agent",
        {
            "action": "apply_recovery_patch",
            "target_type": "claim",
            "target_id": "claim-main",
            "old_status": "supported",
            "new_status": "unsupported",
            "supporting_evidence_ids": ["evidence-negative-quote-bank-quote-1-1"],
        },
        state,
        manager_payload={
            "action_type": "challenge_previous_hypothesis",
            "effective_action_type": "challenge_previous_hypothesis",
            "turn_mode": "recovery_patch",
            "target_claim_ids": ["claim-main"],
            "target_flaw_ids": ["flaw-quote-bank-1"],
            "target_evidence_ids": ["evidence-negative-quote-bank-quote-1-1"],
        },
    )

    assert payload["action"] == "apply_recovery_patch"
    assert payload["target_type"] == "flaw"
    assert payload["target_id"] == "flaw-quote-bank-1"
    assert payload["new_status"] == "candidate"
    assert payload["recovery_patch_operation"] == "mark_contested"
    assert payload["claim_downgrade_contested_rebuild_used"] is True


def test_fallback_recovery_patch_contests_direct_negative_when_positive_support_present():
    """Direct verified-negative evidence should still use a non-destructive
    contested relation when the claim retains verified positive support."""
    state = _build_pattern_a_state(
        extra_negative_evidence=[
            {
                "evidence_id": "evidence-direct-contradiction",
                "claim_id": "claim-main",
                "stance": "contradicts",
                "strength": "strong",
                "verified_grounding_label": "paper_grounded_exact",
                "semantic_grounding_label": "semantic_negative_verified",
                "support_source_bucket": "table_or_figure",
                "source": "evidence-agent-direct",
            }
        ],
        flaw_extra_evidence_ids=["evidence-direct-contradiction"],
    )

    payload = _fallback_recovery_patch_payload(
        state,
        {
            "action_type": "challenge_previous_hypothesis",
            "effective_action_type": "challenge_previous_hypothesis",
            "target_claim_ids": ["claim-main"],
            "target_flaw_ids": [],
            "target_evidence_ids": [],
        },
    )

    assert payload["action"] == "apply_recovery_patch"
    assert payload["target_type"] == "flaw"
    assert payload["target_id"] == "flaw-quote-bank-1"
    assert payload["new_status"] == "candidate"
    assert payload["recovery_patch_operation"] == "mark_contested"
    assert "evidence-direct-contradiction" in payload["supporting_evidence_ids"]
    assert payload["contested_relation"]["claim_id"] == "claim-main"


def test_fallback_recovery_patch_pattern_a_preserves_actionable_quote_bank_candidate():
    """Actionable quote-bank candidate flaws with real positive support become contested,
    not assessment limitations or claim-status downgrades."""
    state = _build_pattern_a_state()
    state["evidence_map"][1]["negative_evidence_type"] = "negative_result"
    state["evidence_map"][1]["raw_quote"] = "The proposed model performs worse than the baseline on the main benchmark."

    payload = _fallback_recovery_patch_payload(
        state,
        {
            "action_type": "challenge_previous_hypothesis",
            "effective_action_type": "challenge_previous_hypothesis",
            "target_claim_ids": ["claim-main"],
            "target_flaw_ids": [],
            "target_evidence_ids": [],
        },
    )

    assert payload["action"] == "apply_recovery_patch"
    assert payload["target_type"] == "flaw"
    assert payload["target_id"] == "flaw-quote-bank-1"
    assert payload["new_status"] == "candidate"
    assert payload["recovery_patch_operation"] == "mark_contested"


def test_fallback_recovery_patch_marks_targeted_protected_concern_terminal():
    state = _build_pattern_a_state()
    state["evidence_map"][1]["negative_evidence_type"] = "negative_result"
    state["evidence_map"][1]["raw_quote"] = "The proposed model performs worse than the baseline on the main benchmark."

    payload = _fallback_recovery_patch_payload(
        state,
        {
            "action_type": "challenge_previous_hypothesis",
            "effective_action_type": "challenge_previous_hypothesis",
            "target_claim_ids": ["claim-main"],
            "target_flaw_ids": ["flaw-quote-bank-1"],
            "target_evidence_ids": [],
        },
    )

    assert payload["action"] == "apply_recovery_patch"
    assert payload["target_type"] == "flaw"
    assert payload["target_id"] == "flaw-quote-bank-1"
    assert payload["new_status"] == "candidate"
    assert payload["recovery_patch_operation"] == "mark_contested"


def test_recovery_targeting_skips_terminal_protected_concern():
    from agent_system.inference import review_runner as _rr

    state = _build_pattern_a_state()
    state["evidence_map"][1]["negative_evidence_type"] = "negative_result"
    state["evidence_map"][1]["raw_quote"] = "The proposed model performs worse than the baseline on the main benchmark."
    recent_turn_logs = [
        {
            "effective_action_type": "challenge_previous_hypothesis",
            "recovery_target_type": "flaw",
            "recovery_target_id": "flaw-quote-bank-1",
            "recovery_terminal": True,
            "recovery_terminal_reason": "verified_actionable_negative_concern_preserved",
            "recovery_repeat_allowed": False,
        }
    ]

    assert _rr._recovery_candidate_flaw_ids(state, recent_turn_logs) == []

    payload = _ensure_recovery_targets(
        {
            "action_type": "challenge_previous_hypothesis",
            "target_claim_ids": [],
            "target_flaw_ids": ["flaw-quote-bank-1"],
            "target_evidence_ids": [],
        },
        state,
        "s4",
        "challenge_previous_hypothesis",
        recent_turn_logs,
    )

    assert payload.get("target_flaw_ids", []) == []


def test_fallback_recovery_patch_marks_real_claim_contested_from_allowed_actionable_negative():
    state = _build_pattern_a_state()
    state["evidence_map"][1]["negative_evidence_type"] = "negative_result"
    state["evidence_map"][1]["raw_quote"] = "The proposed model performs worse than the baseline on the main benchmark."
    state["evidence_map"][1]["claim_status_downgrade_allowed"] = True

    payload = _fallback_recovery_patch_payload(
        state,
        {
            "action_type": "challenge_previous_hypothesis",
            "effective_action_type": "challenge_previous_hypothesis",
            "target_claim_ids": ["claim-main"],
            "target_flaw_ids": [],
            "target_evidence_ids": [],
        },
    )

    assert payload["action"] == "apply_recovery_patch"
    assert payload["target_type"] == "flaw"
    assert payload["target_id"] == "flaw-quote-bank-1"
    assert payload["old_status"] == "candidate"
    assert payload["new_status"] == "candidate"
    assert payload["supporting_evidence_ids"] == ["evidence-negative-quote-bank-quote-1-1"]
    assert payload["recovery_patch_operation"] == "mark_contested"
    assert payload["contested_relation"]["claim_id"] == "claim-main"


def test_fallback_recovery_patch_contests_paper_fallback_only_through_flaw_target():
    state = _build_pattern_a_state()
    state["claims"] = [
        {
            "claim_id": "claim-paper-fallback-1",
            "claim": "Paper-salvaged fallback claim.",
            "status": "supported",
            "supporting_evidence_ids": ["evidence-positive-strong"],
            "claim_kind": "paper_extracted",
            "claim_origin_kind": "raw_salvaged_claim_agent_output",
        }
    ]
    state["evidence_map"][0]["claim_id"] = "claim-paper-fallback-1"
    state["evidence_map"][1]["claim_id"] = "claim-paper-fallback-1"
    state["evidence_map"][1]["negative_evidence_type"] = "negative_result"
    state["evidence_map"][1]["claim_status_downgrade_allowed"] = True
    state["flaw_candidates"][0]["related_claim_ids"] = ["claim-paper-fallback-1"]

    payload = _fallback_recovery_patch_payload(
        state,
        {
            "action_type": "challenge_previous_hypothesis",
            "effective_action_type": "challenge_previous_hypothesis",
            "target_claim_ids": ["claim-paper-fallback-1"],
            "target_flaw_ids": [],
            "target_evidence_ids": [],
        },
    )

    assert payload["action"] == "apply_recovery_patch"
    assert payload["target_type"] == "flaw"
    assert payload["target_id"] == "flaw-quote-bank-1"
    assert payload["new_status"] == "candidate"
    assert payload["recovery_patch_operation"] == "mark_contested"


def test_fallback_recovery_patch_downgrades_confirmed_actionable_flaw_to_candidate():
    """A confirmed actionable negative flaw gets de-escalated to potential concern,
    giving recovery a non-limitation operation without invalidating the claim."""
    state = _build_pattern_a_state()
    state["flaw_candidates"][0]["status"] = "confirmed"
    state["evidence_map"][1]["negative_evidence_type"] = "negative_result"
    state["evidence_map"][1]["raw_quote"] = "The proposed model performs worse than the baseline on the main benchmark."

    payload = _fallback_recovery_patch_payload(
        state,
        {
            "action_type": "challenge_previous_hypothesis",
            "effective_action_type": "challenge_previous_hypothesis",
            "target_claim_ids": ["claim-main"],
            "target_flaw_ids": ["flaw-quote-bank-1"],
            "target_evidence_ids": [],
        },
    )

    assert payload["action"] == "apply_recovery_patch"
    assert payload["target_type"] == "flaw"
    assert payload["target_id"] == "flaw-quote-bank-1"
    assert payload["old_status"] == "confirmed"
    assert payload["new_status"] == "candidate"
    assert payload["supporting_evidence_ids"] == ["evidence-negative-quote-bank-quote-1-1"]


def test_fallback_recovery_patch_pattern_a_skipped_when_flaw_target_already_set():
    """P0-1a: when manager already selected a target_flaw, the existing flaw
    branch handles it; Pattern A should not preempt that."""
    state = _build_pattern_a_state(
        extra_negative_evidence=[
            {
                "evidence_id": "evidence-not-grounded",
                "claim_id": "claim-other",
                "stance": "contradicts",
                "verified_grounding_label": "not_verified_paraphrase_only",
            }
        ],
    )
    # Add an unverified flaw the manager wants to downgrade via the original
    # flaw branch (status=confirmed, lacks verified-negative grounding).
    state["flaw_candidates"].append(
        {
            "flaw_id": "flaw-unverified",
            "status": "confirmed",
            "related_claim_ids": ["claim-main"],
            "evidence_ids": ["evidence-not-grounded"],
            "negative_evidence_ids": ["evidence-not-grounded"],
        }
    )

    payload = _fallback_recovery_patch_payload(
        state,
        {
            "action_type": "challenge_previous_hypothesis",
            "effective_action_type": "challenge_previous_hypothesis",
            "target_claim_ids": ["claim-main"],
            "target_flaw_ids": ["flaw-unverified"],
            "target_evidence_ids": ["evidence-not-grounded"],
        },
    )

    # Original flaw branch should fire on flaw-unverified, not the new
    # Pattern A path on the quote-bank-grounded flaw.
    assert payload["action"] == "apply_recovery_patch"
    assert payload["target_type"] == "flaw"
    assert payload["target_id"] == "flaw-unverified"
    assert payload["new_status"] == "downgraded"


def test_recovery_targeting_includes_unverified_flaw_burden():
    state = {
        "claims": [{"claim_id": "claim-main", "status": "supported"}],
        "evidence_map": [
            {
                "evidence_id": "evidence-unverified",
                "claim_id": "claim-main",
                "stance": "contradicts",
                "verified_grounding_label": "not_verified_paraphrase_only",
            }
        ],
        "flaw_candidates": [
            {
                "flaw_id": "flaw-unverified",
                "status": "confirmed",
                "related_claim_ids": ["claim-main"],
                "evidence_ids": ["evidence-unverified"],
                "negative_evidence_ids": ["evidence-unverified"],
            }
        ],
    }

    payload = _ensure_recovery_targets(
        {"action_type": "challenge_previous_hypothesis", "effective_action_type": "challenge_previous_hypothesis"},
        state,
        mode="s4",
        recovery_action="challenge_previous_hypothesis",
        recent_turn_logs=[],
    )

    assert payload["target_flaw_ids"] == ["flaw-unverified"]
    assert payload["target_evidence_ids"] == ["evidence-unverified"]


def test_fallback_recovery_patch_downgrades_flaw_without_verified_negative_grounding():
    state = {
        "claims": [{"claim_id": "claim-main", "status": "supported"}],
        "evidence_map": [
            {
                "evidence_id": "evidence-unverified",
                "claim_id": "claim-main",
                "stance": "contradicts",
                "verified_grounding_label": "not_verified_paraphrase_only",
            }
        ],
        "flaw_candidates": [
            {
                "flaw_id": "flaw-unverified",
                "status": "confirmed",
                "related_claim_ids": ["claim-main"],
                "evidence_ids": ["evidence-unverified"],
                "negative_evidence_ids": ["evidence-unverified"],
            }
        ],
    }

    payload = _fallback_recovery_patch_payload(
        state,
        {
            "action_type": "challenge_previous_hypothesis",
            "target_flaw_ids": ["flaw-unverified"],
            "target_evidence_ids": ["evidence-unverified"],
        },
    )

    assert payload["action"] == "apply_recovery_patch"
    assert payload["target_type"] == "flaw"
    assert payload["target_id"] == "flaw-unverified"
    assert payload["new_status"] == "downgraded"
    assert payload["supporting_evidence_ids"] == ["evidence-unverified"]


def test_fallback_critique_blocks_truncated_json_fragment():
    payload = _fallback_worker_payload(
        agent_id="Critique Agent",
        raw_text='<json>{"flaw_candidates":[{"flaw_id":"flaw-1","title":"Missing metrics","description":"The claim lacks quantitative validation"',
        state={
            "claims": [{"claim_id": "claim-main", "status": "uncertain"}],
            "evidence_map": [{"evidence_id": "evidence-1", "claim_id": "claim-main"}],
            "flaw_candidates": [],
        },
        manager_payload={"action_type": "analyze_flaws", "target_claim_ids": ["claim-main"], "target_evidence_ids": ["evidence-1"]},
    )

    assert payload["flaw_candidates"] == []
    assert payload["unresolved_questions"] == []
    assert payload["dialogue_summary"] == ""
    assert payload["_emission_failure_code"] == "CRITIQUE_TRUNCATED_STRUCTURED_OUTPUT_BLOCKED"
    assert "truncated structured JSON" in payload["_emission_failure_message"]


def test_fallback_critique_blocks_plain_text_parse_fallback_from_visible_state():
    payload = _fallback_worker_payload(
        agent_id="Critique Agent",
        raw_text="The paper claims broad robustness but only reports one narrow benchmark.",
        state={
            "claims": [{"claim_id": "claim-main", "status": "uncertain"}],
            "evidence_map": [{"evidence_id": "evidence-1", "claim_id": "claim-main"}],
            "flaw_candidates": [],
        },
        manager_payload={"action_type": "analyze_flaws", "target_claim_ids": ["claim-main"], "target_evidence_ids": ["evidence-1"]},
    )

    assert payload["flaw_candidates"] == []
    assert payload["unresolved_questions"] == []
    assert payload["dialogue_summary"] == ""
    assert payload["_emission_failure_code"] == "CRITIQUE_TRUNCATED_STRUCTURED_OUTPUT_BLOCKED"



def test_normalized_conflict_note_is_sanitized_and_truncated():
    from agent_system.environments.env_package.review.state import normalize_review_update_payload

    payload = normalize_review_update_payload(
        {
            "conflict_notes": [
                {
                    "note": "<think>This is a very long conflict note that should be cleaned before being stored.</think> "
                    "It should lose XML-style tags and be truncated to a compact summary that is easier to analyze in logs."
                }
            ]
        }
    )

    note = payload["conflict_notes"][0]["note"]
    assert "<think>" not in note
    assert len(note) <= 140
    assert note.startswith("This is a very long conflict note")


def test_extract_tagged_json_accepts_conflict_notes_payload():
    payload = extract_tagged_json(
        '<json>{"evidence_map":[{"evidence_id":"e1","claim_id":"c1","evidence":"Table 2 weakens the main claim.","source":"Table 2","strength":"weak","stance":"contradicts"}],"conflict_notes":[{"note":"Table 2 contradicts the earlier conclusion.","claim_id":"c1","evidence_id":"e1","conflict_type":"evidence_conflict"}]}</json>'
    )
    assert payload["conflict_notes"][0]["conflict_type"] == "evidence_conflict"


def test_fallback_general_reviewer_payload_marks_recheck_and_challenge_signals():
    recheck_payload = _fallback_worker_payload(
        agent_id="General Reviewer Agent 1",
        raw_text="The evidence is missing and no concrete table is cited.",
        state={"claims": [{"claim_id": "claim-main"}], "evidence_map": [], "flaw_candidates": []},
        manager_payload={"action_type": "request_evidence_recheck", "target_claim_ids": ["claim-main"]},
    )
    challenge_payload = _fallback_worker_payload(
        agent_id="General Reviewer Agent 1",
        raw_text="However, the reported experiment contradicts the earlier conclusion.",
        state={"claims": [{"claim_id": "claim-main"}], "evidence_map": [{"evidence_id": "evidence-1"}], "flaw_candidates": []},
        manager_payload={"action_type": "challenge_previous_hypothesis", "target_claim_ids": ["claim-main"], "target_evidence_ids": ["evidence-1"]},
    )

    assert recheck_payload["evidence_map"][0]["strength"] == "missing"
    assert challenge_payload["flaw_candidates"][0]["status"] == "downgraded"
    assert challenge_payload["conflict_notes"]


def test_fallback_general_reviewer_payload_respects_verify_evidence_action():
    payload = _fallback_worker_payload(
        agent_id="General Reviewer Agent 1",
        raw_text="The paper claims gains but does not cite a concrete table or experiment in this answer.",
        state={"claims": [{"claim_id": "claim-main"}], "evidence_map": [], "flaw_candidates": []},
        manager_payload={"action_type": "verify_evidence", "target_claim_ids": ["claim-main"]},
    )

    assert payload["evidence_map"]
    assert payload["evidence_map"][0]["claim_id"] == "claim-main"
    assert payload["claims"] == []


def test_apply_manager_policy_fallback_overrides_s3_claim_progress_to_verify_evidence():
    state = {
        "claims": [{"claim_id": "claim-main", "status": "uncertain"}],
        "evidence_map": [],
        "flaw_candidates": [],
        "unresolved_questions": [{"question": "What evidence supports the main claim?", "status": "open"}],
        "risk_profile": {"open_question_count": 1, "conflict_count": 0, "readiness": "not_ready"},
        "evidence_gaps": ["Claim claim-main lacks grounded supporting evidence."],
        "current_hypotheses": [],
        "clarification_needed": False,
        "pending_user_question": "",
    }
    manager_payload = {
        "decision": "continue",
        "action_type": "extract_claims",
        "selected_agents": ["General Reviewer Agent 1"],
        "focus": "extract more claims",
        "rationale": "Keep extracting.",
    }

    normalized = _apply_manager_policy_fallback(
        manager_payload=manager_payload,
        state=state,
        mode="s3",
        worker_ids=["General Reviewer Agent 1", "General Reviewer Agent 2"],
        worker_limit=1,
        recent_turn_logs=[],
    )

    assert normalized["action_type"] == "verify_evidence"
    assert normalized["policy_source"] == "s3_claim_progress_override"


def test_apply_manager_policy_fallback_overrides_s3_clarification_to_verify_evidence():
    state = {
        "claims": [{"claim_id": "claim-main", "status": "uncertain"}],
        "evidence_map": [],
        "flaw_candidates": [],
        "unresolved_questions": [{"question": "What evidence supports the main claim?", "status": "open"}],
        "risk_profile": {"open_question_count": 1, "conflict_count": 0, "readiness": "not_ready"},
        "evidence_gaps": ["Claim claim-main lacks grounded supporting evidence."],
        "current_hypotheses": [],
        "clarification_needed": True,
        "pending_user_question": "Which issue should we prioritize?",
    }
    manager_payload = {
        "decision": "continue",
        "action_type": "ask_user_clarification",
        "selected_agents": [],
        "focus": "Which issue should we prioritize?",
        "rationale": "Need clarification.",
        "pending_user_question": "Which issue should we prioritize?",
        "clarification_needed": True,
    }

    normalized = _apply_manager_policy_fallback(
        manager_payload=manager_payload,
        state=state,
        mode="s3",
        worker_ids=["General Reviewer Agent 1", "General Reviewer Agent 2"],
        worker_limit=1,
        recent_turn_logs=[],
    )

    assert normalized["action_type"] == "verify_evidence"
    assert normalized["policy_source"] == "s3_clarification_override"
    assert normalized["selected_agents"] == ["General Reviewer Agent 1"]


def test_infer_action_from_state_skips_clarification_for_s3():
    state = {
        "claims": [{"claim_id": "claim-main", "status": "uncertain"}],
        "evidence_map": [],
        "flaw_candidates": [],
        "unresolved_questions": [{"question": "Need stronger evidence.", "status": "open"}],
        "risk_profile": {"open_question_count": 1, "conflict_count": 0, "readiness": "not_ready"},
        "evidence_gaps": ["Claim claim-main lacks grounded supporting evidence."],
        "current_hypotheses": [],
        "clarification_needed": True,
        "pending_user_question": "Which aspect should the review prioritize?",
    }

    inferred = _infer_action_from_state("s3", state, recent_turn_logs=[])

    assert inferred["action_type"] == "verify_evidence"


def test_apply_manager_policy_fallback_overrides_s4_clarification_before_claims():
    state = {
        "claims": [],
        "evidence_map": [],
        "flaw_candidates": [],
        "unresolved_questions": [{"question": "What should be clarified first?", "status": "open"}],
        "risk_profile": {"open_question_count": 1, "conflict_count": 0, "readiness": "not_ready"},
        "evidence_gaps": [],
        "current_hypotheses": [],
        "clarification_needed": True,
        "pending_user_question": "What should be clarified first?",
    }
    manager_payload = {
        "decision": "continue",
        "action_type": "ask_user_clarification",
        "selected_agents": [],
        "focus": "What should be clarified first?",
        "rationale": "Need clarification.",
        "pending_user_question": "What should be clarified first?",
        "clarification_needed": True,
    }

    normalized = _apply_manager_policy_fallback(
        manager_payload=manager_payload,
        state=state,
        mode="s4",
        worker_ids=["Claim Agent", "Evidence Agent", "Critique Agent"],
        worker_limit=1,
        recent_turn_logs=[],
    )

    assert normalized["action_type"] == "extract_claims"
    assert normalized["policy_source"] == "s4_preclaim_clarification_override"
    assert normalized["selected_agents"] == ["Claim Agent"]


def test_infer_action_from_state_triggers_one_claim_coverage_expansion_after_narrow_claim_pass():
    state = {
        "claims": [
            {
                "claim_id": "claim-1",
                "claim": "The paper proposes a new framework.",
                "status": "uncertain",
                "claim_type": "contribution",
                "coverage_tags": ["contribution"],
            }
        ],
        "evidence_map": [],
        "flaw_candidates": [],
        "unresolved_questions": [],
        "risk_profile": {"open_question_count": 0, "conflict_count": 0, "readiness": "not_ready"},
        "evidence_gaps": [],
        "current_hypotheses": [],
        "clarification_needed": False,
        "pending_user_question": "",
    }

    inferred = _infer_action_from_state(
        "s4",
        state,
        recent_turn_logs=[{"action_type": "extract_claims"}],
    )

    assert inferred["action_type"] == "extract_claims"
    assert inferred["claim_coverage_expansion_required"] is True
    assert "empirical" in inferred["claim_coverage_missing_tags"]


def test_apply_manager_policy_fallback_routes_claim_coverage_expansion_to_claim_agent_once():
    state = {
        "claims": [
            {
                "claim_id": "claim-1",
                "claim": "The paper proposes a new framework.",
                "status": "uncertain",
                "claim_type": "contribution",
                "coverage_tags": ["contribution"],
            }
        ],
        "evidence_map": [],
        "flaw_candidates": [],
        "unresolved_questions": [],
        "risk_profile": {"open_question_count": 0, "conflict_count": 0, "readiness": "not_ready"},
        "evidence_gaps": [],
        "current_hypotheses": [],
        "clarification_needed": False,
        "pending_user_question": "",
    }
    normalized = _apply_manager_policy_fallback(
        manager_payload={
            "decision": "continue",
            "action_type": "verify_evidence",
            "selected_agents": ["Evidence Agent"],
            "focus": "verify evidence",
            "rationale": "Move forward.",
        },
        state=state,
        mode="s4",
        worker_ids=["Claim Agent", "Evidence Agent", "Critique Agent"],
        worker_limit=1,
        recent_turn_logs=[{"action_type": "extract_claims"}],
    )

    assert normalized["action_type"] == "extract_claims"
    assert normalized["decision"] == "continue"
    assert normalized["policy_source"] == "claim_coverage_expansion_override"
    assert normalized["selected_agents"] == ["Claim Agent"]
    assert normalized["claim_coverage_expansion_required"] is True
    assert "method" in normalized["claim_coverage_missing_tags"]


def test_claim_coverage_expansion_does_not_repeat_after_expansion_or_evidence():
    state = {
        "claims": [{"claim_id": "claim-1", "claim": "The paper proposes a framework.", "status": "uncertain"}],
        "evidence_map": [],
        "flaw_candidates": [],
        "unresolved_questions": [],
        "risk_profile": {"open_question_count": 0, "conflict_count": 0, "readiness": "not_ready"},
        "evidence_gaps": [],
        "current_hypotheses": [],
        "clarification_needed": False,
        "pending_user_question": "",
    }

    after_expansion = _infer_action_from_state(
        "s4",
        state,
        recent_turn_logs=[
            {"action_type": "extract_claims"},
            {"action_type": "extract_claims", "policy_source": "claim_coverage_expansion_override"},
        ],
    )
    assert after_expansion["action_type"] == "verify_evidence"

    with_evidence = dict(state)
    with_evidence["evidence_map"] = [
        {"evidence_id": "e1", "claim_id": "claim-1", "strength": "medium", "stance": "supports"}
    ]
    inferred_with_evidence = _infer_action_from_state(
        "s4",
        with_evidence,
        recent_turn_logs=[{"action_type": "extract_claims"}],
    )
    assert inferred_with_evidence["action_type"] != "extract_claims"



def test_apply_manager_policy_fallback_overrides_s4_clarification_to_evidence():
    state = {
        "claims": [{"claim_id": "claim-main", "status": "uncertain"}],
        "evidence_map": [],
        "flaw_candidates": [],
        "unresolved_questions": [{"question": "What evidence supports the main claim?", "status": "open"}],
        "risk_profile": {"open_question_count": 1, "conflict_count": 0, "readiness": "not_ready"},
        "evidence_gaps": ["Claim claim-main lacks grounded supporting evidence."],
        "current_hypotheses": [],
        "clarification_needed": True,
        "pending_user_question": "Should we clarify the target before checking evidence?",
    }
    manager_payload = {
        "decision": "continue",
        "action_type": "ask_user_clarification",
        "selected_agents": [],
        "focus": "Should we clarify the target before checking evidence?",
        "rationale": "Need clarification.",
        "pending_user_question": "Should we clarify the target before checking evidence?",
        "clarification_needed": True,
    }

    normalized = _apply_manager_policy_fallback(
        manager_payload=manager_payload,
        state=state,
        mode="s4",
        worker_ids=["Claim Agent", "Evidence Agent", "Critique Agent"],
        worker_limit=1,
        recent_turn_logs=[],
    )

    assert normalized["action_type"] == "verify_evidence"
    assert normalized["policy_source"] == "s4_clarification_to_evidence_override"
    assert normalized["selected_agents"] == ["Evidence Agent"]



def test_infer_action_from_state_prefers_recheck_for_weak_or_missing_evidence():
    state = {
        "claims": [{"claim_id": "claim-main", "status": "supported"}],
        "evidence_map": [{"evidence_id": "evidence-1", "claim_id": "claim-main", "strength": "missing", "stance": "missing"}],
        "flaw_candidates": [{"flaw_id": "flaw-main", "status": "candidate"}],
        "unresolved_questions": [{"question": "What concrete evidence is still missing?", "status": "open"}],
        "risk_profile": {"open_question_count": 1, "conflict_count": 0, "readiness": "not_ready"},
        "evidence_gaps": [],
        "current_hypotheses": [],
        "clarification_needed": False,
        "pending_user_question": "",
    }

    inferred = _infer_action_from_state("s4", state, recent_turn_logs=[])

    assert inferred["action_type"] == "request_evidence_recheck"



def test_infer_action_from_state_prefers_challenge_for_contradictory_evidence():
    state = {
        "claims": [{"claim_id": "claim-main", "status": "supported"}],
        "evidence_map": [{"evidence_id": "evidence-1", "claim_id": "claim-main", "strength": "medium", "stance": "contradicts"}],
        "flaw_candidates": [{"flaw_id": "flaw-main", "status": "candidate"}],
        "unresolved_questions": [{"question": "Does the contradictory result overturn the main conclusion?", "status": "open"}],
        "risk_profile": {"open_question_count": 1, "conflict_count": 0, "readiness": "not_ready"},
        "evidence_gaps": [],
        "current_hypotheses": ["The main conclusion may be too strong."],
        "clarification_needed": False,
        "pending_user_question": "",
    }

    inferred = _infer_action_from_state("s4", state, recent_turn_logs=[])

    assert inferred["action_type"] == "analyze_flaws"



def test_apply_manager_policy_fallback_overrides_s4_finalize_to_recheck_for_weak_evidence():
    state = {
        "claims": [{"claim_id": "claim-main", "status": "supported"}],
        "evidence_map": [{"evidence_id": "evidence-1", "claim_id": "claim-main", "strength": "missing", "stance": "missing"}],
        "flaw_candidates": [{"flaw_id": "flaw-main", "status": "candidate"}],
        "unresolved_questions": [{"question": "What evidence is still missing?", "status": "open"}],
        "risk_profile": {"open_question_count": 1, "conflict_count": 0, "readiness": "ready_to_finalize"},
        "evidence_gaps": [],
        "current_hypotheses": [],
        "clarification_needed": False,
        "pending_user_question": "",
    }
    manager_payload = {
        "decision": "continue",
        "action_type": "finalize",
        "selected_agents": [],
        "focus": "wrap up",
        "rationale": "Enough signal to decide.",
    }

    normalized = _apply_manager_policy_fallback(
        manager_payload=manager_payload,
        state=state,
        mode="s4",
        worker_ids=["Claim Agent", "Evidence Agent", "Critique Agent"],
        worker_limit=1,
        recent_turn_logs=[],
    )

    assert normalized["action_type"] == "request_evidence_recheck"
    assert normalized["policy_source"] == "s4_recheck_override"
    assert normalized["selected_agents"] == ["Evidence Agent"]



def test_apply_manager_policy_fallback_filters_unsupported_claim_targets_for_challenge():
    normalized = _apply_manager_policy_fallback(
        manager_payload={
            "decision": "continue",
            "action_type": "challenge_previous_hypothesis",
            "target_claim_ids": ["claim-stale", "claim-live"],
            "target_flaw_ids": [],
            "selected_agents": ["Critique Agent", "Evidence Agent"],
        },
        state={
            "claims": [
                {"claim_id": "claim-stale", "status": "unsupported"},
                {"claim_id": "claim-live", "status": "uncertain"},
            ],
            "flaw_candidates": [],
            "risk_profile": {"conflict_count": 1, "open_question_count": 0, "readiness": "not_ready"},
            "conflict_notes": [{"conflict_id": "c1"}],
            "evidence_map": [{"evidence_id": "e1", "claim_id": "claim-live", "stance": "contradicts", "strength": "weak"}],
        },
        mode="s4",
        worker_ids=["Claim Agent", "Evidence Agent", "Critique Agent"],
        worker_limit=2,
        recent_turn_logs=[],
    )

    assert normalized["action_type"] == "challenge_previous_hypothesis"
    assert normalized["target_claim_ids"] == ["claim-live"]
    assert "claim-stale" not in normalized["target_claim_ids"]


def test_apply_manager_policy_fallback_routes_context_challenge_to_negative_recheck():
    normalized = _apply_manager_policy_fallback(
        manager_payload={
            "decision": "continue",
            "action_type": "challenge_previous_hypothesis",
            "target_claim_ids": ["claim-paper-context-1"],
            "target_flaw_ids": [],
            "selected_agents": ["Critique Agent", "Evidence Agent"],
        },
        state={
            "claims": [
                {
                    "claim_id": "claim-paper-context-1",
                    "status": "uncertain",
                    "claim_kind": "paper_extracted",
                    "claim_origin_kind": "context_synthesized",
                },
                {"claim_id": "claim-main", "status": "supported", "claim_kind": "paper_extracted"},
            ],
            "flaw_candidates": [{"flaw_id": "flaw-main", "status": "candidate", "related_claim_ids": ["claim-main"]}],
            "risk_profile": {"conflict_count": 1, "open_question_count": 0, "readiness": "not_ready"},
            "conflict_notes": [{"conflict_id": "c1"}],
            "evidence_map": [{"evidence_id": "e1", "claim_id": "claim-main", "stance": "supports", "strength": "strong"}],
        },
        mode="s4",
        worker_ids=["Claim Agent", "Evidence Agent", "Critique Agent"],
        worker_limit=2,
        recent_turn_logs=[],
    )

    assert normalized["action_type"] == "request_evidence_recheck"
    assert normalized["policy_source"] in {"negative_evidence_formation_override", "recovery_target_refinement_override"}
    assert "claim-paper-context-1" not in normalized["target_claim_ids"]
    assert normalized["target_flaw_ids"] == ["flaw-main"]
    assert normalized["selected_agents"] == ["Evidence Agent"]


def test_apply_manager_policy_fallback_filters_context_recheck_to_real_claim():
    normalized = _apply_manager_policy_fallback(
        manager_payload={
            "decision": "continue",
            "action_type": "request_evidence_recheck",
            "target_claim_ids": ["claim-paper-context-1"],
            "selected_agents": ["Evidence Agent"],
        },
        state={
            "claims": [
                {
                    "claim_id": "claim-paper-context-1",
                    "status": "uncertain",
                    "claim_kind": "paper_extracted",
                    "claim_origin_kind": "context_synthesized",
                },
                {"claim_id": "claim-main", "status": "supported", "claim_kind": "paper_extracted"},
            ],
            "flaw_candidates": [],
            "risk_profile": {"conflict_count": 1, "open_question_count": 0, "readiness": "not_ready"},
            "conflict_notes": [{"conflict_id": "c1"}],
            "evidence_map": [{"evidence_id": "e1", "claim_id": "claim-main", "stance": "supports", "strength": "strong"}],
        },
        mode="s4",
        worker_ids=["Claim Agent", "Evidence Agent", "Critique Agent"],
        worker_limit=2,
        recent_turn_logs=[],
    )

    assert normalized["action_type"] == "request_evidence_recheck"
    assert normalized["target_claim_ids"] == ["claim-main"]
    assert "claim-paper-context-1" not in normalized["target_claim_ids"]


def test_apply_manager_policy_fallback_summarizes_context_challenge_without_real_target():
    normalized = _apply_manager_policy_fallback(
        manager_payload={
            "decision": "continue",
            "action_type": "challenge_previous_hypothesis",
            "target_claim_ids": ["claim-paper-fallback-1"],
            "target_flaw_ids": [],
            "selected_agents": ["Critique Agent", "Evidence Agent"],
        },
        state={
            "claims": [
                {
                    "claim_id": "claim-paper-fallback-1",
                    "status": "uncertain",
                    "claim_kind": "paper_extracted",
                    "claim_origin_kind": "raw_salvaged_claim_agent_output",
                }
            ],
            "flaw_candidates": [],
            "risk_profile": {"conflict_count": 1, "open_question_count": 0, "readiness": "not_ready"},
            "conflict_notes": [{"conflict_id": "c1"}],
            "current_hypotheses": ["Claim claim-paper-fallback-1 may be weak."],
            "evidence_map": [],
        },
        mode="s4",
        worker_ids=["Claim Agent", "Evidence Agent", "Critique Agent"],
        worker_limit=2,
        recent_turn_logs=[],
    )

    assert normalized["action_type"] == "summarize_progress"
    assert normalized["policy_source"] == "recovery_target_exhausted_override"
    assert normalized["target_claim_ids"] == []
    assert normalized["selected_agents"] == []


def test_apply_manager_policy_fallback_summarizes_when_recovery_targets_are_exhausted():
    normalized = _apply_manager_policy_fallback(
        manager_payload={
            "decision": "continue",
            "action_type": "challenge_previous_hypothesis",
            "target_claim_ids": ["claim-stale"],
            "target_flaw_ids": [],
            "selected_agents": ["Critique Agent", "Evidence Agent"],
        },
        state={
            "claims": [{"claim_id": "claim-stale", "status": "unsupported"}],
            "flaw_candidates": [],
            "risk_profile": {"conflict_count": 1, "open_question_count": 0, "readiness": "not_ready"},
            "conflict_notes": [{"conflict_id": "c1"}],
            "current_hypotheses": ["The earlier criticism may still be too weak."],
            "evidence_map": [{"evidence_id": "e1", "claim_id": "claim-stale", "stance": "contradicts", "strength": "weak"}],
        },
        mode="s4",
        worker_ids=["Claim Agent", "Evidence Agent", "Critique Agent"],
        worker_limit=2,
        recent_turn_logs=[],
    )

    assert normalized["action_type"] == "summarize_progress"
    assert normalized["policy_source"] == "recovery_target_exhausted_override"
    assert normalized["selected_agents"] == []
    assert normalized["target_claim_ids"] == []


def test_apply_manager_policy_fallback_overrides_s4_finalize_to_challenge_for_contradiction():
    state = {
        "claims": [{"claim_id": "claim-main", "status": "supported"}],
        "evidence_map": [{"evidence_id": "evidence-1", "claim_id": "claim-main", "strength": "medium", "stance": "contradicts"}],
        "flaw_candidates": [{"flaw_id": "flaw-main", "status": "candidate"}],
        "unresolved_questions": [{"question": "Does the contradiction overturn the conclusion?", "status": "open"}],
        "risk_profile": {"open_question_count": 1, "conflict_count": 0, "readiness": "ready_to_finalize"},
        "evidence_gaps": [],
        "current_hypotheses": ["The main conclusion may be too strong."],
        "clarification_needed": False,
        "pending_user_question": "",
    }
    manager_payload = {
        "decision": "continue",
        "action_type": "finalize",
        "selected_agents": [],
        "focus": "wrap up",
        "rationale": "Enough signal to decide.",
    }

    normalized = _apply_manager_policy_fallback(
        manager_payload=manager_payload,
        state=state,
        mode="s4",
        worker_ids=["Claim Agent", "Evidence Agent", "Critique Agent"],
        worker_limit=2,
        recent_turn_logs=[],
    )

    assert normalized["action_type"] == "analyze_flaws"
    assert normalized["policy_source"] == "negative_evidence_binding_retry_override"
    assert "Critique Agent" in normalized["selected_agents"]


def test_infer_action_from_state_prefers_binding_retry_for_unlinked_negative_evidence():
    state = {
        "claims": [{"claim_id": "claim-main", "status": "supported"}],
        "evidence_map": [
            {
                "evidence_id": "e-neg",
                "claim_id": "claim-main",
                "strength": "medium",
                "stance": "contradicts",
                "source": "Table 3",
            }
        ],
        "flaw_candidates": [],
        "unresolved_questions": [],
        "risk_profile": {"open_question_count": 0, "conflict_count": 0, "readiness": "not_ready"},
        "evidence_gaps": [],
        "current_hypotheses": [],
        "clarification_needed": False,
        "pending_user_question": "",
    }

    inferred = _infer_action_from_state("s4", state, recent_turn_logs=[])

    assert inferred["action_type"] == "analyze_flaws"
    assert inferred["target_claim_ids"] == ["claim-main"]
    assert inferred["target_evidence_ids"] == ["e-neg"]


def test_apply_manager_policy_fallback_routes_unlinked_negative_evidence_to_critique_binding_retry():
    state = {
        "claims": [{"claim_id": "claim-main", "status": "supported"}],
        "evidence_map": [
            {
                "evidence_id": "e-neg",
                "claim_id": "claim-main",
                "strength": "medium",
                "stance": "contradicts",
                "source": "Table 3",
            }
        ],
        "flaw_candidates": [],
        "unresolved_questions": [],
        "risk_profile": {"open_question_count": 0, "conflict_count": 0, "readiness": "ready_to_finalize"},
        "evidence_gaps": [],
        "current_hypotheses": [],
        "clarification_needed": False,
        "pending_user_question": "",
    }
    manager_payload = {
        "decision": "continue",
        "action_type": "finalize",
        "selected_agents": [],
        "focus": "wrap up",
        "rationale": "Enough signal to decide.",
    }

    normalized = _apply_manager_policy_fallback(
        manager_payload=manager_payload,
        state=state,
        mode="s4",
        worker_ids=["Claim Agent", "Evidence Agent", "Critique Agent"],
        worker_limit=2,
        recent_turn_logs=[],
    )

    assert normalized["action_type"] == "analyze_flaws"
    assert normalized["decision"] == "continue"
    assert normalized["policy_source"] == "negative_evidence_binding_retry_override"
    assert normalized["selected_agents"] == ["Critique Agent"]
    assert normalized["target_claim_ids"] == ["claim-main"]
    assert normalized["target_evidence_ids"] == ["e-neg"]
    assert normalized["negative_evidence_binding_retry_required"] is True


def test_actionable_missing_negative_evidence_routes_to_critique_binding_retry():
    state = {
        "claims": [{"claim_id": "claim-main", "claim": "The evaluation is comprehensive.", "status": "supported"}],
        "evidence_map": [
            {
                "evidence_id": "e-neg-missing-ablation",
                "claim_id": "claim-main",
                "evidence": "The paper says the evaluation lacks an ablation study.",
                "raw_quote": "The method does not include an ablation study.",
                "quote_id": "quote-negative-or-gap-1",
                "stance": "missing",
                "strength": "missing",
                "negative_evidence_type": "missing_ablation",
                "negative_evidence_actionability": "actionable_candidate",
                "verified_grounding_label": "paper_grounded_exact",
                "semantic_grounding_label": "semantic_negative_verified",
                "binding_status": "bound_real_claim",
            }
        ],
        "flaw_candidates": [
            {
                "flaw_id": "flaw-neg",
                "flaw": "The evaluation may miss ablations.",
                "status": "candidate",
                "severity": "major",
                "related_claim_ids": ["claim-main"],
                "evidence_ids": ["e-neg-missing-ablation"],
                "negative_evidence_ids": ["e-neg-missing-ablation"],
                "negative_evidence_type": "missing_ablation",
            }
        ],
        "unresolved_questions": [],
        "risk_profile": {"readiness": "ready_to_finalize"},
    }

    normalized = _apply_manager_policy_fallback(
        manager_payload={"decision": "continue", "action_type": "challenge_previous_hypothesis", "selected_agents": ["Critique Agent"]},
        state=state,
        mode="s4",
        worker_ids=["Claim Agent", "Evidence Agent", "Critique Agent"],
        worker_limit=2,
        recent_turn_logs=[{"policy_source": "hard_negative_discovery_override", "negative_evidence_formation_required": True}],
    )

    assert normalized["action_type"] == "analyze_flaws"
    assert normalized["policy_source"] == "negative_evidence_binding_retry_override"
    assert normalized["selected_agents"] == ["Critique Agent"]
    assert normalized["target_evidence_ids"] == ["e-neg-missing-ablation"]


def test_recovery_phase_preserves_negative_binding_retry_as_normal_critique_turn():
    from agent_system.inference.review_runner import _apply_recovery_phase_protocol

    payload = _apply_recovery_phase_protocol(
        {
            "decision": "continue",
            "action_type": "analyze_flaws",
            "effective_action_type": "analyze_flaws",
            "policy_source": "negative_evidence_binding_retry_override",
            "target_claim_ids": ["claim-main"],
            "target_evidence_ids": ["e-neg-missing-ablation"],
            "selected_agents": ["Critique Agent"],
        },
        {"phase": "recovery", "phase_turn_index": 1},
        "s4",
        ["Evidence Agent", "Critique Agent"],
        1,
        recent_turn_logs=[
            {
                "action_type": "request_evidence_recheck",
                "turn_mode": "normal_evidence",
                "policy_source": "hard_negative_discovery_override",
                "negative_evidence_formation_required": True,
            }
        ],
    )

    assert payload["phase"] == "normal_review"
    assert payload["turn_mode"] == "normal_evidence"
    assert payload["recovery_patch_mode_entered"] is False
    assert payload["action_type"] == "analyze_flaws"
    assert payload["selected_agents"] == ["Critique Agent"]
    assert any("bind the verified negative evidence" in note for note in payload.get("policy_notes", []))


def test_recovery_phase_defers_patch_after_negative_formation_for_normal_critique():
    from agent_system.inference.review_runner import _apply_recovery_phase_protocol

    payload = _apply_recovery_phase_protocol(
        {
            "decision": "continue",
            "action_type": "challenge_previous_hypothesis",
            "effective_action_type": "challenge_previous_hypothesis",
            "policy_source": "evidence_progress_override",
            "selected_agents": ["Critique Agent", "Evidence Agent"],
        },
        {
            "phase": "recovery",
            "phase_turn_index": 1,
            "evidence_map": [
                {
                    "evidence_id": "e-neg",
                    "claim_id": "claim-main",
                    "stance": "missing",
                    "strength": "missing",
                    "verified_grounding_label": "paper_grounded_exact",
                    "semantic_grounding_label": "semantic_negative_verified",
                    "source": "quote-bank-negative-grounding",
                    "negative_evidence_type": "missing_ablation",
                }
            ],
        },
        "s4",
        ["Evidence Agent", "Critique Agent"],
        1,
        recent_turn_logs=[
            {
                "action_type": "request_evidence_recheck",
                "turn_mode": "normal_evidence",
                "policy_source": "hard_negative_discovery_override",
                "negative_evidence_formation_required": True,
            }
        ],
    )

    assert payload["phase"] == "normal_review"
    assert payload["turn_mode"] == "normal_evidence"
    assert payload["recovery_patch_mode_entered"] is False
    assert payload["action_type"] == "analyze_flaws"
    assert payload["policy_source"] == "negative_evidence_binding_retry_override"
    assert payload["selected_agents"] == ["Critique Agent"]


def test_verified_negative_flaw_routes_finalize_to_critique_review():
    state = {
        "claims": [{"claim_id": "claim-main", "claim": "The evaluation is comprehensive.", "status": "supported"}],
        "evidence_map": [
            {
                "evidence_id": "e-neg-scope",
                "claim_id": "claim-main",
                "stance": "missing",
                "strength": "missing",
                "negative_evidence_type": "scope_limitation",
                "negative_evidence_actionability": "assessment_limitation",
                "verified_grounding_label": "paper_grounded_exact",
                "semantic_grounding_label": "semantic_negative_verified",
                "binding_status": "bound_real_claim",
            }
        ],
        "flaw_candidates": [
            {
                "flaw_id": "flaw-scope",
                "status": "candidate",
                "severity": "minor",
                "related_claim_ids": ["claim-main"],
                "evidence_ids": ["e-neg-scope"],
                "negative_evidence_ids": ["e-neg-scope"],
                "negative_evidence_type": "scope_limitation",
            }
        ],
    }

    normalized = _apply_manager_policy_fallback(
        manager_payload={"decision": "continue", "action_type": "finalize", "policy_source": "manager_model", "selected_agents": []},
        state=state,
        mode="s4",
        worker_ids=["Claim Agent", "Evidence Agent", "Critique Agent"],
        worker_limit=2,
        recent_turn_logs=[{"policy_source": "hard_negative_discovery_override", "negative_evidence_formation_required": True}],
    )

    assert normalized["action_type"] == "analyze_flaws"
    assert normalized["policy_source"] == "negative_evidence_binding_retry_override"
    assert normalized["selected_agents"] == ["Critique Agent"]
    assert normalized["target_flaw_ids"] == ["flaw-scope"]
    assert normalized["target_evidence_ids"] == ["e-neg-scope"]


def test_programmatic_locator_treats_named_sections_as_specific():
    anchor = _locator_from_text_anchor("\\section{Experiments} We evaluate on BenchX and report Table 1 results.")
    assert anchor == "Table 1"
    section_anchor = _locator_from_text_anchor("\\section{Methodology} The architecture has two stages.")
    assert section_anchor == "Section: Methodology"
    assert _is_specific_locator(section_anchor) is True


def test_negative_evidence_type_classifier_keeps_baseline_eval_reproducibility_separate():
    assert _classify_negative_evidence_type("The paper lacks an ablation study for the main module.") == "missing_ablation"
    assert _classify_negative_evidence_type("The method does not compare against a strong retrieval baseline.") == "missing_baseline"
    assert _classify_negative_evidence_type("The evaluation is limited to one small dataset and is not evaluated on real benchmarks.") == "insufficient_evaluation"
    assert _classify_negative_evidence_type("The implementation details and hyperparameters are missing, limiting reproducibility.") == "reproducibility_gap"
    assert _classify_negative_evidence_type("This limitation restricts applicability to a narrow domain.") == "scope_limitation"


def test_evidence_gap_normalization_preserves_legacy_string_lifecycle():
    gaps = _normalize_evidence_gaps(["Claim claim-main lacks grounded supporting evidence."])

    assert gaps == [
        {
            "gap_id": "gap-claim-main-claim-claim-main-lack",
            "gap": "Claim claim-main lacks grounded supporting evidence.",
            "status": "open",
            "claim_id": "claim-main",
            "evidence_id": "",
            "flaw_id": "",
            "source": "legacy_string",
            "resolution": "",
        }
    ]


def test_infer_action_from_state_ignores_closed_evidence_gap_lifecycle_rows():
    state = {
        "claims": [{"claim_id": "claim-main", "status": "supported"}],
        "evidence_map": [
            {
                "evidence_id": "evidence-1",
                "claim_id": "claim-main",
                "strength": "strong",
                "stance": "supports",
                "source": "Table 1",
            }
        ],
        "flaw_candidates": [
            {
                "flaw_id": "flaw-main",
                "status": "retracted",
                "related_claim_ids": ["claim-main"],
                "evidence_ids": ["evidence-1"],
            }
        ],
        "unresolved_questions": [],
        "risk_profile": {"open_question_count": 0, "conflict_count": 0, "readiness": "ready_to_finalize"},
        "evidence_gaps": [
            {
                "gap_id": "gap-old",
                "gap": "Claim claim-main lacks grounded supporting evidence.",
                "status": "converted",
                "claim_id": "claim-main",
                "evidence_id": "evidence-1",
                "resolution": "converted_to_evidence_conflict",
            }
        ],
        "current_hypotheses": [],
        "clarification_needed": False,
        "pending_user_question": "",
    }

    inferred = infer_action_from_state("s4", state, recent_turn_logs=[])

    assert inferred["action_type"] != "verify_evidence"
    assert inferred["action_type"] != "request_evidence_recheck"


def test_negative_evidence_binding_retry_does_not_repeat_recently_retried_evidence():
    state = {
        "claims": [{"claim_id": "claim-main", "status": "supported"}],
        "evidence_map": [
            {
                "evidence_id": "e-neg",
                "claim_id": "claim-main",
                "strength": "medium",
                "stance": "contradicts",
                "source": "Table 3",
            }
        ],
        "flaw_candidates": [],
        "unresolved_questions": [],
        "risk_profile": {"open_question_count": 0, "conflict_count": 0, "readiness": "ready_to_finalize"},
        "evidence_gaps": [],
        "current_hypotheses": [],
        "clarification_needed": False,
        "pending_user_question": "",
    }
    recent_turn_logs = [
        {
            "action_type": "analyze_flaws",
            "policy_source": "negative_evidence_binding_retry_override",
            "target_evidence_ids": ["e-neg"],
        }
    ]

    inferred = _infer_action_from_state("s4", state, recent_turn_logs=recent_turn_logs)

    assert inferred["action_type"] != "analyze_flaws"
    assert inferred.get("target_evidence_ids") != ["e-neg"]


def test_negative_evidence_binding_retry_skips_already_linked_negative_flaw():
    state = {
        "claims": [{"claim_id": "claim-main", "status": "supported"}],
        "evidence_map": [
            {
                "evidence_id": "e-neg",
                "claim_id": "claim-main",
                "strength": "medium",
                "stance": "contradicts",
                "source": "Table 3",
            }
        ],
        "flaw_candidates": [
            {
                "flaw_id": "flaw-main",
                "status": "confirmed",
                "severity": "major",
                "related_claim_ids": ["claim-main"],
                "evidence_ids": ["e-neg"],
                "negative_evidence_ids": ["e-neg"],
            }
        ],
        "unresolved_questions": [],
        "risk_profile": {"open_question_count": 0, "conflict_count": 0, "readiness": "ready_to_finalize"},
        "evidence_gaps": [],
        "current_hypotheses": [],
        "clarification_needed": False,
        "pending_user_question": "",
    }

    inferred = _infer_action_from_state("s4", state, recent_turn_logs=[])

    assert inferred["action_type"] != "analyze_flaws"
    assert inferred.get("target_evidence_ids") != ["e-neg"]


def test_apply_manager_policy_fallback_keeps_broad_recheck_as_lighter_recovery():
    state = {
        "claims": [
            {"claim_id": "claim-a", "status": "supported"},
            {"claim_id": "claim-b", "status": "uncertain"},
        ],
        "evidence_map": [
            {"evidence_id": "evidence-a", "claim_id": "claim-a", "strength": "missing", "stance": "missing"},
            {"evidence_id": "evidence-b", "claim_id": "claim-b", "strength": "weak", "stance": "supports"},
        ],
        "flaw_candidates": [{"flaw_id": "flaw-main", "status": "candidate"}],
        "unresolved_questions": [{"question": "Which claim still lacks usable evidence?", "status": "open"}],
        "risk_profile": {"open_question_count": 1, "conflict_count": 0, "readiness": "ready_to_finalize"},
        "evidence_gaps": [],
        "current_hypotheses": [],
        "clarification_needed": False,
        "pending_user_question": "",
    }
    manager_payload = {
        "decision": "continue",
        "action_type": "finalize",
        "selected_agents": [],
        "focus": "wrap up",
        "rationale": "Enough signal to decide.",
    }

    normalized = _apply_manager_policy_fallback(
        manager_payload=manager_payload,
        state=state,
        mode="s4",
        worker_ids=["Claim Agent", "Evidence Agent", "Critique Agent"],
        worker_limit=1,
        recent_turn_logs=[],
    )

    assert normalized["action_type"] == "request_evidence_recheck"
    assert normalized["policy_source"] != "progression_throttle_override"
    assert normalized["selected_agents"] == ["Evidence Agent"]
    assert normalized["target_claim_ids"] == ["claim-a", "claim-b"]


def test_apply_manager_policy_fallback_routes_unverified_flaw_before_evidence_gap():
    state = {
        "claims": [
            {"claim_id": "claim-a", "status": "supported"},
            {"claim_id": "claim-b", "status": "uncertain"},
        ],
        "evidence_map": [
            {"evidence_id": "evidence-a", "claim_id": "claim-a", "strength": "strong", "stance": "supports"},
        ],
        "flaw_candidates": [{"flaw_id": "flaw-main", "status": "candidate", "severity": "major"}],
        "unresolved_questions": [{"question": "Which claim still lacks usable evidence?", "status": "open"}],
        "risk_profile": {"open_question_count": 4, "conflict_count": 0, "readiness": "needs_targeted_recheck"},
        "evidence_gaps": ["Claim claim-b lacks grounded supporting evidence."],
        "current_hypotheses": [],
        "clarification_needed": False,
        "pending_user_question": "",
    }
    manager_payload = {
        "decision": "continue",
        "action_type": "analyze_flaws",
        "selected_agents": ["Critique Agent"],
        "focus": "continue flaw analysis",
        "rationale": "Need another flaw pass.",
    }

    normalized = _apply_manager_policy_fallback(
        manager_payload=manager_payload,
        state=state,
        mode="s4",
        worker_ids=["Claim Agent", "Evidence Agent", "Critique Agent"],
        worker_limit=2,
        recent_turn_logs=[
            {"action_type": "extract_claims", "turn_mode": "normal_evidence"},
            {"action_type": "verify_evidence", "turn_mode": "normal_evidence"},
            {"action_type": "analyze_flaws", "turn_mode": "normal_evidence"},
        ],
    )

    assert normalized["action_type"] == "request_evidence_recheck"
    assert normalized["policy_source"] == "s4_recovery_relevant_override"
    assert normalized["selected_agents"] == ["Evidence Agent"]
    assert normalized.get("target_flaw_ids", []) in ([], ["flaw-main"])
    assert normalized["recovery_push_triggered"] is True



def test_apply_manager_policy_clears_stale_finalize_when_unverified_flaw_blocks_report():
    state = {
        "claims": [
            {"claim_id": "claim-a", "status": "supported"},
            {"claim_id": "claim-b", "status": "uncertain"},
        ],
        "evidence_map": [
            {"evidence_id": "evidence-a", "claim_id": "claim-a", "strength": "strong", "stance": "supports"},
        ],
        "flaw_candidates": [{"flaw_id": "flaw-main", "status": "candidate", "severity": "major"}],
        "unresolved_questions": [{"question": "Does this candidate flaw have verified negative evidence?", "status": "open"}],
        "risk_profile": {"open_question_count": 1, "conflict_count": 0, "readiness": "ready_to_finalize"},
        "evidence_gaps": [],
        "current_hypotheses": [],
        "clarification_needed": False,
        "pending_user_question": "",
    }
    manager_payload = {
        "decision": "finalize",
        "action_type": "finalize",
        "selected_agents": [],
        "focus": "wrap up",
        "rationale": "Enough signal to decide.",
        "final_decision": "reject",
        "final_report": "Final Decision: Reject",
    }

    normalized = _apply_manager_policy_fallback(
        manager_payload=manager_payload,
        state=state,
        mode="s4",
        worker_ids=["Claim Agent", "Evidence Agent", "Critique Agent"],
        worker_limit=2,
        recent_turn_logs=[
            {"action_type": "extract_claims", "turn_mode": "normal_evidence"},
            {"action_type": "verify_evidence", "turn_mode": "normal_evidence"},
            {"action_type": "analyze_flaws", "turn_mode": "normal_evidence"},
        ],
    )

    assert normalized["decision"] == "continue"
    assert normalized["action_type"] == "request_evidence_recheck"
    assert normalized["policy_source"] == "s4_recovery_relevant_override"
    assert normalized["target_flaw_ids"] == ["flaw-main"]
    assert normalized["final_decision"] == "undecided"
    assert normalized["final_report"] == ""
    assert normalized["selected_agents"] == ["Evidence Agent"]



def test_apply_manager_policy_fallback_keeps_fallback_challenge_without_legacy_throttle():
    state = {
        "claims": [{"claim_id": "claim-fallback-1", "claim": "Fallback extracted claim.", "status": "uncertain"}],
        "evidence_map": [{"evidence_id": "evidence-1", "claim_id": "claim-fallback-1", "strength": "strong", "stance": "contradicts"}],
        "flaw_candidates": [{"flaw_id": "flaw-main", "status": "candidate"}],
        "unresolved_questions": [{"question": "Is the fallback claim even grounded?", "status": "open"}],
        "risk_profile": {"open_question_count": 1, "conflict_count": 1, "readiness": "ready_to_finalize"},
        "conflict_notes": [{"claim_id": "claim-fallback-1", "evidence_id": "evidence-1", "note": "Conflict is attached to a fallback claim."}],
        "evidence_gaps": [],
        "current_hypotheses": ["The current conclusion may be too strong."],
        "clarification_needed": False,
        "pending_user_question": "",
    }
    manager_payload = {
        "decision": "continue",
        "action_type": "finalize",
        "selected_agents": [],
        "focus": "wrap up",
        "rationale": "Enough signal to decide.",
    }

    normalized = _apply_manager_policy_fallback(
        manager_payload=manager_payload,
        state=state,
        mode="s4",
        worker_ids=["Claim Agent", "Evidence Agent", "Critique Agent"],
        worker_limit=1,
        recent_turn_logs=[],
    )

    assert normalized["action_type"] == "challenge_previous_hypothesis"
    assert normalized["policy_source"] in {"s4_conflict_recovery_override", "s4_challenge_override"}
    assert normalized["selected_agents"] == ["Critique Agent"]
    assert normalized["progression_throttle_applied"] is False
    assert normalized["progression_throttle_issues"] == []



def test_apply_manager_policy_fallback_does_not_rethrottle_recent_progression_chain():
    state = {
        "claims": [{"claim_id": "claim-fallback-1", "claim": "Fallback extracted claim.", "status": "uncertain"}],
        "evidence_map": [{"evidence_id": "evidence-1", "claim_id": "claim-fallback-1", "strength": "strong", "stance": "contradicts"}],
        "flaw_candidates": [{"flaw_id": "flaw-main", "status": "candidate"}],
        "unresolved_questions": [{"question": "Is the fallback claim even grounded?", "status": "open"}],
        "risk_profile": {"open_question_count": 1, "conflict_count": 1, "readiness": "ready_to_finalize"},
        "conflict_notes": [{"claim_id": "claim-fallback-1", "evidence_id": "evidence-1", "note": "Conflict is attached to a fallback claim."}],
        "evidence_gaps": [],
        "current_hypotheses": ["The current conclusion may be too strong."],
        "clarification_needed": False,
        "pending_user_question": "",
    }
    manager_payload = {
        "decision": "continue",
        "action_type": "finalize",
        "selected_agents": [],
        "focus": "wrap up",
        "rationale": "Enough signal to decide.",
    }

    normalized = _apply_manager_policy_fallback(
        manager_payload=manager_payload,
        state=state,
        mode="s4",
        worker_ids=["Claim Agent", "Evidence Agent", "Critique Agent"],
        worker_limit=1,
        recent_turn_logs=[{"policy_source": "progression_throttle_override", "action_type": "request_evidence_recheck"}],
    )

    assert normalized["policy_source"] != "progression_throttle_override"
    assert normalized["action_type"] == "challenge_previous_hypothesis"


def test_apply_manager_policy_fallback_keeps_grounded_single_claim_challenge():
    state = {
        "claims": [{"claim_id": "claim-main", "claim": "Main result.", "status": "supported"}],
        "evidence_map": [{"evidence_id": "evidence-1", "claim_id": "claim-main", "strength": "strong", "stance": "contradicts", "verified_grounding_label": "paper_grounded_exact", "semantic_grounding_label": "semantic_support_verified"}],
        "flaw_candidates": [{"flaw_id": "flaw-main", "status": "candidate", "related_claim_ids": ["claim-main"], "negative_evidence_ids": ["evidence-1"]}],
        "unresolved_questions": [{"question": "Does the contradiction overturn the conclusion?", "status": "open"}],
        "risk_profile": {"open_question_count": 1, "conflict_count": 1, "readiness": "ready_to_finalize"},
        "conflict_notes": [{"claim_id": "claim-main", "evidence_id": "evidence-1", "note": "Strong contradiction on the main claim."}],
        "evidence_gaps": [],
        "current_hypotheses": ["The current conclusion may be too strong."],
        "clarification_needed": False,
        "pending_user_question": "",
    }
    manager_payload = {
        "decision": "continue",
        "action_type": "finalize",
        "selected_agents": [],
        "focus": "wrap up",
        "rationale": "Enough signal to decide.",
    }

    normalized = _apply_manager_policy_fallback(
        manager_payload=manager_payload,
        state=state,
        mode="s4",
        worker_ids=["Claim Agent", "Evidence Agent", "Critique Agent"],
        worker_limit=2,
        recent_turn_logs=[],
    )

    assert normalized["action_type"] == "challenge_previous_hypothesis"
    assert normalized["policy_source"] in {"s4_conflict_recovery_override", "s4_challenge_override"}
    assert normalized["target_claim_ids"] == ["claim-main"]


def test_apply_manager_policy_fallback_keeps_grounded_multi_claim_challenge_without_throttle():
    state = {
        "claims": [
            {"claim_id": "claim-a", "claim": "First grounded claim.", "status": "supported"},
            {"claim_id": "claim-b", "claim": "Second grounded claim.", "status": "partially_supported"},
        ],
        "evidence_map": [
            {"evidence_id": "evidence-a", "claim_id": "claim-a", "strength": "strong", "stance": "contradicts", "verified_grounding_label": "paper_grounded_exact", "semantic_grounding_label": "semantic_support_verified"},
            {"evidence_id": "evidence-b", "claim_id": "claim-b", "strength": "strong", "stance": "contradicts", "verified_grounding_label": "paper_grounded_exact", "semantic_grounding_label": "semantic_support_verified"},
        ],
        "flaw_candidates": [{"flaw_id": "flaw-main", "status": "candidate", "related_claim_ids": ["claim-a", "claim-b"], "negative_evidence_ids": ["evidence-a", "evidence-b"]}],
        "unresolved_questions": [{"question": "Which grounded claim is actually overturned?", "status": "open"}],
        "risk_profile": {"open_question_count": 1, "conflict_count": 2, "readiness": "ready_to_finalize"},
        "conflict_notes": [
            {"claim_id": "claim-a", "evidence_id": "evidence-a", "note": "Contradiction on grounded claim A."},
            {"claim_id": "claim-b", "evidence_id": "evidence-b", "note": "Contradiction on grounded claim B."},
        ],
        "evidence_gaps": [],
        "current_hypotheses": ["The current conclusion may be too strong."],
        "clarification_needed": False,
        "pending_user_question": "",
    }
    manager_payload = {
        "decision": "continue",
        "action_type": "finalize",
        "selected_agents": [],
        "focus": "wrap up",
        "rationale": "Enough signal to decide.",
    }

    normalized = _apply_manager_policy_fallback(
        manager_payload=manager_payload,
        state=state,
        mode="s4",
        worker_ids=["Claim Agent", "Evidence Agent", "Critique Agent"],
        worker_limit=2,
        recent_turn_logs=[],
    )

    assert normalized["action_type"] == "challenge_previous_hypothesis"
    assert normalized["policy_source"] != "progression_throttle_override"
    assert normalized["progression_throttle_applied"] is False
    assert normalized["target_claim_ids"] == ["claim-a", "claim-b"]


def test_apply_manager_policy_fallback_keeps_broad_three_claim_challenge_without_legacy_throttle():
    state = {
        "claims": [
            {"claim_id": "claim-a", "claim": "First grounded claim.", "status": "supported"},
            {"claim_id": "claim-b", "claim": "Second grounded claim.", "status": "partially_supported"},
            {"claim_id": "claim-c", "claim": "Third grounded claim.", "status": "uncertain"},
        ],
        "evidence_map": [
            {"evidence_id": "evidence-a", "claim_id": "claim-a", "strength": "strong", "stance": "contradicts", "verified_grounding_label": "paper_grounded_exact", "semantic_grounding_label": "semantic_support_verified"},
            {"evidence_id": "evidence-b", "claim_id": "claim-b", "strength": "strong", "stance": "contradicts", "verified_grounding_label": "paper_grounded_exact", "semantic_grounding_label": "semantic_support_verified"},
            {"evidence_id": "evidence-c", "claim_id": "claim-c", "strength": "strong", "stance": "contradicts", "verified_grounding_label": "paper_grounded_exact", "semantic_grounding_label": "semantic_support_verified"},
        ],
        "flaw_candidates": [{"flaw_id": "flaw-main", "status": "candidate", "related_claim_ids": ["claim-a", "claim-b", "claim-c"], "negative_evidence_ids": ["evidence-a", "evidence-b", "evidence-c"]}],
        "unresolved_questions": [{"question": "Which grounded claim should be challenged first?", "status": "open"}],
        "risk_profile": {"open_question_count": 1, "conflict_count": 3, "readiness": "ready_to_finalize"},
        "conflict_notes": [
            {"claim_id": "claim-a", "evidence_id": "evidence-a", "note": "Contradiction on grounded claim A."},
            {"claim_id": "claim-b", "evidence_id": "evidence-b", "note": "Contradiction on grounded claim B."},
            {"claim_id": "claim-c", "evidence_id": "evidence-c", "note": "Contradiction on grounded claim C."},
        ],
        "evidence_gaps": [],
        "current_hypotheses": ["The current conclusion may be too strong."],
        "clarification_needed": False,
        "pending_user_question": "",
    }
    manager_payload = {
        "decision": "continue",
        "action_type": "finalize",
        "selected_agents": [],
        "focus": "wrap up",
        "rationale": "Enough signal to decide.",
        "target_claim_ids": ["claim-a", "claim-b", "claim-c"],
    }

    normalized = _apply_manager_policy_fallback(
        manager_payload=manager_payload,
        state=state,
        mode="s4",
        worker_ids=["Claim Agent", "Evidence Agent", "Critique Agent"],
        worker_limit=2,
        recent_turn_logs=[],
    )

    assert normalized["action_type"] == "challenge_previous_hypothesis"
    assert normalized["policy_source"] in {"s4_conflict_recovery_override", "s4_challenge_override"}
    assert normalized["progression_throttle_applied"] is False
    assert normalized["progression_throttle_issues"] == []



def test_apply_manager_policy_fallback_overrides_s4_to_flaw_analysis_after_evidence():
    state = {
        "claims": [{"claim_id": "claim-main", "status": "supported"}],
        "evidence_map": [{"evidence_id": "evidence-1", "claim_id": "claim-main"}],
        "flaw_candidates": [],
        "unresolved_questions": [{"question": "What is the strongest weakness?", "status": "open"}],
        "risk_profile": {"open_question_count": 1, "conflict_count": 0, "readiness": "not_ready"},
        "evidence_gaps": [],
        "current_hypotheses": [],
        "clarification_needed": True,
        "pending_user_question": "Should we ask for clarification instead of flaw analysis?",
    }
    manager_payload = {
        "decision": "continue",
        "action_type": "ask_user_clarification",
        "selected_agents": [],
        "focus": "Should we ask for clarification instead of flaw analysis?",
        "rationale": "Need clarification.",
        "pending_user_question": "Should we ask for clarification instead of flaw analysis?",
        "clarification_needed": True,
    }

    normalized = _apply_manager_policy_fallback(
        manager_payload=manager_payload,
        state=state,
        mode="s4",
        worker_ids=["Claim Agent", "Evidence Agent", "Critique Agent"],
        worker_limit=1,
        recent_turn_logs=[],
    )

    assert normalized["action_type"] == "analyze_flaws"
    assert normalized["policy_source"] == "s4_evidence_to_flaw_override"
    assert normalized["selected_agents"] == ["Critique Agent"]


def test_run_review_episode_supports_clarification_placeholder():
    responses = {
        "Review Manager Agent": [
            '<json>{"decision":"continue","action_type":"ask_user_clarification","selected_agents":[],"focus":"Need a priority.","rationale":"The paper has several open directions and needs prioritization.","requires_clarification":true,"clarification_question":"Should the review prioritize empirical support or novelty?","dialogue_summary":"Clarification is needed before deeper review.","unresolved_questions":["Which review axis matters most?"],"claims":[],"evidence_map":[],"flaw_candidates":[],"recommendation":"undecided","final_decision":"undecided","final_report":""}</json>',
            '<json>{"decision":"finalize","action_type":"finalize","selected_agents":[],"focus":"Wrap up.","rationale":"The clarification placeholder was recorded.","dialogue_summary":"Clarification placeholder recorded.","unresolved_questions":["Which review axis matters most?"],"claims":[],"evidence_map":[],"flaw_candidates":[],"recommendation":"reject","final_decision":"reject","final_report":"Final Decision: Reject\n\nThe review remains blocked by unresolved priorities."}</json>',
        ],
    }
    call_counts = {key: 0 for key in responses}

    def fake_generate(agent_id: str, prompt: str) -> str:
        idx = call_counts[agent_id]
        call_counts[agent_id] += 1
        return responses[agent_id][idx]

    result = run_review_episode(
        extras={
            "paper_id": "paper-clarify",
            "paper_text": "A paper with several possible review targets.",
            "user_goal": "Record clarification needs.",
            "data_source": "unit-test",
            "ground_truth_decision": "reject",
            "reference_review": "Final Decision: Reject",
        },
        mode="s1",
        generate_fn=fake_generate,
        max_turns=2,
        max_workers_per_turn=1,
    )

    assert result["review_state"]["pending_user_question"] == ""
    assert result["review_state"]["simulated_user_reply"]
    assert any(item["question"] == "Should the review prioritize empirical support or novelty?" and item["status"] == "resolved" for item in result["review_state"]["unresolved_questions"])
    assert result["turn_logs"][0]["action_type"] == "ask_user_clarification"
    assert result["turn_logs"][0]["requires_clarification"] is True


def test_run_review_episode_routes_challenge_action_to_relevant_workers():
    responses = {
        "Review Manager Agent": [
            '<json>{"decision":"continue","action_type":"challenge_previous_hypothesis","selected_agents":[],"focus":"Recheck the strongest hypothesis.","rationale":"Conflicting evidence should challenge the current conclusion.","target_claim_ids":["claim-main"],"target_hypotheses":["The improvement may be overstated."],"dialogue_summary":"The review now challenges an earlier hypothesis.","unresolved_questions":["Does Table 3 contradict the main claim?"],"claims":[{"claim_id":"claim-main","claim":"The method improves retrieval accuracy.","importance":"high","status":"uncertain"}],"evidence_map":[{"evidence_id":"evidence-1","claim_id":"claim-main","evidence":"Table 3 shows weaker gains on one benchmark.","source":"Table 3","strength":"strong","stance":"contradicts"}],"flaw_candidates":[{"flaw_id":"flaw-1","title":"Potential overclaim","description":"The main claim may be too broad.","severity":"major","related_claim_ids":["claim-main"],"evidence_ids":["evidence-1"],"confidence":0.8}],"recommendation":"undecided","final_decision":"undecided","final_report":""}</json>',
            '<json>{"decision":"finalize","action_type":"finalize","selected_agents":[],"focus":"Wrap up.","rationale":"Enough state exists to decide.","dialogue_summary":"The challenged hypothesis has been reviewed.","unresolved_questions":["Does Table 3 contradict the main claim?"],"claims":[],"evidence_map":[],"flaw_candidates":[],"recommendation":"reject","final_decision":"reject","final_report":"Final Decision: Reject\n\nThe challenged hypothesis remained unresolved after rechecking."}</json>',
        ],
        "Claim Agent": [
            '<json>{"claims":[{"claim_id":"claim-main","claim":"The method improves retrieval accuracy.","importance":"high","status":"uncertain"}],"unresolved_questions":["Which experiment most directly supports the main claim?"],"dialogue_summary":"A fallback claim-focused pass was added.","recommendation":"undecided"}</json>'
        ],
        "Evidence Agent": [
            '<json>{"evidence_map":[{"evidence_id":"evidence-2","claim_id":"claim-main","evidence":"Appendix C reports unstable gains across seeds.","source":"Appendix C","strength":"medium","stance":"contradicts"}],"unresolved_questions":["Are the gains robust across seeds?"],"dialogue_summary":"Additional contradictory evidence was found.","recommendation":"reject"}</json>',
            '<json>{"evidence_map":[],"unresolved_questions":["The remaining flaw still lacks verified negative evidence."],"dialogue_summary":"No stronger verified negative evidence was found.","recommendation":"reject"}</json>'
        ],
        "Critique Agent": [
            '<json>{"flaw_candidates":[{"flaw_id":"flaw-2","title":"Robustness concern","description":"The gains appear unstable across seeds.","severity":"major","related_claim_ids":["claim-main"],"evidence_ids":["evidence-2"],"confidence":0.7}],"unresolved_questions":["Why are the gains unstable?"],"dialogue_summary":"The critique now focuses on robustness.","recommendation":"reject"}</json>',
            '<json>{"flaw_candidates":[{"flaw_id":"flaw-2","status":"downgraded","title":"Robustness concern","description":"The concern remains plausible but lacks verified negative evidence.","severity":"minor","related_claim_ids":["claim-main"],"evidence_ids":[],"confidence":0.4}],"unresolved_questions":["The robustness concern should remain a potential concern."],"dialogue_summary":"The critique downgraded the unverified flaw.","recommendation":"reject"}</json>'
        ],
    }
    call_counts = {key: 0 for key in responses}

    def fake_generate(agent_id: str, prompt: str) -> str:
        idx = call_counts[agent_id]
        call_counts[agent_id] += 1
        return responses[agent_id][idx]

    result = run_review_episode(
        extras={
            "paper_id": "paper-challenge",
            "paper_text": "A paper with potentially overstated empirical gains.",
            "user_goal": "Challenge unstable hypotheses.",
            "data_source": "unit-test",
            "ground_truth_decision": "reject",
            "reference_review": "Final Decision: Reject",
        },
        mode="s4",
        generate_fn=fake_generate,
        max_turns=2,
        max_workers_per_turn=2,
    )

    assert result["runner_trace"][0]["manager_action_type"] == "request_evidence_recheck"
    assert result["runner_trace"][0]["selected_workers"] == ["Evidence Agent"]
    assert result["turn_logs"][0]["action_type"] == "request_evidence_recheck"


def test_infer_action_from_state_prefers_recheck_over_summary_when_focus_stalls_with_weak_evidence():
    state = {
        "claims": [{"claim_id": "claim-main", "status": "uncertain"}],
        "evidence_map": [{"evidence_id": "evidence-1", "claim_id": "claim-main", "strength": "weak", "stance": "partially_supports"}],
        "flaw_candidates": [{"flaw_id": "flaw-1", "status": "candidate", "severity": "major"}],
        "unresolved_questions": [{"question": "Is Table 2 enough?", "status": "open", "question_id": "q1", "related_claim_ids": ["claim-main"]}],
        "evidence_gaps": [],
        "current_hypotheses": [],
        "conflict_notes": [],
        "risk_profile": {
            "dominant_risks": [],
            "support_signals": ["1 claim remains only weakly supported."],
            "open_question_count": 1,
            "major_flaw_count": 1,
            "conflict_count": 0,
            "readiness": "needs_targeted_recheck",
        },
        "clarification_needed": False,
        "pending_user_question": "",
    }
    recent_turn_logs = [
        {"action_type": "verify_evidence", "focus": "Check Table 2 for support."},
        {"action_type": "verify_evidence", "focus": "Check Table 2 for support."},
    ]

    action = _infer_action_from_state("s3", state, recent_turn_logs=recent_turn_logs)

    assert action["action_type"] == "request_evidence_recheck"
    assert any(token in action["rationale"].lower() for token in {"weak", "missing", "revisit"})


def test_run_review_episode_respects_mode_action_constraints():
    responses = {
        "Review Manager Agent": [
            '<json>{"decision":"continue","action_type":"challenge_previous_hypothesis","selected_agents":[],"focus":"Challenge a hypothesis.","rationale":"Try a stronger action even in s2.","target_hypotheses":["The gain may be overstated."],"claims":[{"claim_id":"claim-main","claim":"The method improves retrieval accuracy.","importance":"high","status":"uncertain"}],"unresolved_questions":["Which evidence is strongest?"],"dialogue_summary":"Trying to challenge early.","recommendation":"undecided","final_decision":"undecided","final_report":""}</json>',
            '<json>{"decision":"finalize","action_type":"finalize","selected_agents":[],"focus":"Wrap up.","rationale":"Stop after routing fallback.","claims":[],"evidence_map":[],"flaw_candidates":[],"unresolved_questions":["Which evidence is strongest?"],"dialogue_summary":"Fallback routing complete.","recommendation":"reject","final_decision":"reject","final_report":"Final Decision: Reject\n\nThe review remained incomplete."}</json>',
        ],
    }
    call_counts = {key: 0 for key in responses}

    def fake_generate(agent_id: str, prompt: str) -> str:
        idx = call_counts[agent_id]
        call_counts[agent_id] += 1
        return responses[agent_id][idx]

    result = run_review_episode(
        extras={
            "paper_id": "paper-mode-constraint",
            "paper_text": "A paper still in early review state.",
            "user_goal": "Keep s2 actions conservative.",
            "data_source": "unit-test",
            "ground_truth_decision": "reject",
            "reference_review": "Final Decision: Reject",
        },
        mode="s2",
        generate_fn=fake_generate,
        max_turns=2,
        max_workers_per_turn=1,
    )

    assert result["runner_trace"][0]["manager_payload"]["action_type"] in {"extract_claims", "verify_evidence", "summarize_progress", "ask_user_clarification", "finalize"}
    assert result["runner_trace"][0]["manager_payload"]["action_type"] != "challenge_previous_hypothesis"
    assert result["runner_trace"][0]["policy_source"] == "mode_constraint_override"
    assert any("not allowed in mode s2" in note for note in result["runner_trace"][0]["policy_notes"])
    assert result["turn_logs"][0]["policy_source"] == "mode_constraint_override"


def test_build_worker_observation_includes_targeted_objects_and_fallback_uses_targets():
    from agent_system.inference.review_runner import build_worker_observation, _fallback_worker_payload

    task = {
        "review_state": {
            "claims": [{"claim_id": "claim-main", "claim": "The method improves retrieval accuracy.", "status": "uncertain"}],
            "evidence_map": [{"evidence_id": "evidence-1", "claim_id": "claim-main", "evidence": "Table 2 shows weak gains.", "source": "Table 2", "strength": "weak", "stance": "partially_supports"}],
            "flaw_candidates": [{"flaw_id": "flaw-1", "title": "Potential overclaim", "description": "The main claim may be too broad.", "severity": "major", "status": "candidate"}],
            "unresolved_questions": [],
            "evidence_gaps": [],
            "current_hypotheses": ["The gain may depend on one benchmark."],
            "revision_summary": [],
            "conflict_summary": [],
            "risk_profile": {"readiness": "needs_targeted_recheck"},
            "turn_id": 1,
            "mode": "s4",
            "dialogue_summary": "Need to recheck one hypothesis.",
            "last_focus": "recheck evidence",
            "active_focus": "recheck evidence",
            "final_decision": "undecided",
            "pending_user_question": "",
            "simulated_user_reply": "",
            "clarification_needed": False,
            "conflict_notes": [],
            "revision_log": [],
        },
        "paper_id": "paper-targets",
        "paper_text": "A paper with one contested claim.",
        "user_goal": "Target the contested objects.",
        "data_source": "unit-test",
        "max_turns": 3,
        "mode": "s4",
        "turn_logs": [],
    }
    manager_payload = {
        "action_type": "challenge_previous_hypothesis",
        "focus": "Recheck the contested claim.",
        "rationale": "Conflicting evidence should challenge the current hypothesis.",
        "target_claim_ids": ["claim-main"],
        "target_flaw_ids": ["flaw-1"],
        "target_evidence_ids": ["evidence-1"],
        "target_hypotheses": ["The gain may depend on one benchmark."],
    }

    obs = build_worker_observation(task, manager_payload, "Evidence Agent")
    fallback = _fallback_worker_payload("Evidence Agent", "Raw fallback evidence text", task["review_state"], manager_payload=manager_payload)

    assert "Targeted Review Objects" in obs
    assert "claim-main" in obs and "evidence-1" in obs and "flaw-1" in obs
    assert fallback["evidence_map"][0]["claim_id"] == "claim-main"
    assert fallback["evidence_map"][0]["evidence_id"] == "evidence-1"


def test_evidence_observation_omits_fallback_claim_targets():
    task = {
        "paper_id": "fallback-evidence-slice",
        "mode": "s4",
        "max_turns": 4,
        "user_goal": "Verify claims without binding support to fallback ids.",
        "review_state": {
            "turn_id": 1,
            "claims": [
                {
                    "claim_id": "claim-fallback-1",
                    "claim": "Fallback recovered claim should not be evidence-bound as a real claim.",
                    "status": "uncertain",
                }
            ],
            "evidence_map": [],
            "flaw_candidates": [],
            "unresolved_questions": [],
            "conflict_notes": [],
            "evidence_gaps": [],
        },
        "paper_text": "--- BEGIN PAPER ---\nAbstract: The paper proposes a method.\nMethod: Details appear here.\n--- END PAPER ---",
        "turn_logs": [],
    }
    manager_payload = {
        "action_type": "verify_evidence",
        "target_claim_ids": ["claim-fallback-1"],
        "target_evidence_ids": [],
        "focus": "Verify fallback claim.",
    }

    obs = render_evidence_observation(task, manager_payload)
    state_slice = obs.split("# Evidence State Slice\n", 1)[1].split("\n\n# Recent Turn Log", 1)[0]

    assert '"allowed_claim_ids": []' in state_slice
    assert '"target_claims": []' in state_slice
    assert '"fallback_claim_targets_omitted": [\n    "claim-fallback-1"\n  ]' in state_slice
    assert manager_payload["fallback_claim_targets_omitted"] == ["claim-fallback-1"]
    assert manager_payload["fallback_claim_targets_omitted_count"] == 1

    turn_log = build_turn_log(1, manager_payload, [], task["review_state"])

    assert turn_log["fallback_claim_targets_omitted"] == ["claim-fallback-1"]
    assert turn_log["fallback_claim_targets_omitted_count"] == 1


def test_evidence_observation_replaces_fallback_target_with_real_candidates():
    task = {
        "paper_id": "fallback-with-real-candidate",
        "mode": "s4",
        "max_turns": 4,
        "user_goal": "Verify real claims even when the manager target is fallback.",
        "review_state": {
            "turn_id": 1,
            "claims": [
                {
                    "claim_id": "claim-real-1",
                    "claim": "The method improves evidence retrieval quality.",
                    "status": "uncertain",
                },
                {
                    "claim_id": "claim-fallback-1",
                    "claim": "Fallback recovered claim should not be evidence-bound as a real claim.",
                    "status": "uncertain",
                },
            ],
            "evidence_map": [],
            "flaw_candidates": [],
            "unresolved_questions": [],
            "conflict_notes": [],
            "evidence_gaps": [],
        },
        "paper_text": "--- BEGIN PAPER ---\nAbstract: The paper proposes a method.\nResults: The method improves retrieval quality.\n--- END PAPER ---",
        "turn_logs": [],
    }
    manager_payload = {
        "action_type": "verify_evidence",
        "target_claim_ids": ["claim-fallback-1"],
        "target_evidence_ids": [],
        "focus": "Verify fallback claim.",
    }

    obs = render_evidence_observation(task, manager_payload)
    state_slice = obs.split("# Evidence State Slice\n", 1)[1].split("\n\n# Recent Turn Log", 1)[0]

    assert '"allowed_claim_ids": [\n    "claim-real-1"\n  ]' in state_slice
    assert '"claim_id": "claim-real-1"' in state_slice
    assert '"claim_id": "claim-fallback-1"' not in state_slice
    assert manager_payload["fallback_claim_targets_omitted"] == ["claim-fallback-1"]
    assert manager_payload["fallback_targets_replaced_with_real_candidates"] is True

    turn_log = build_turn_log(1, manager_payload, [], task["review_state"])

    assert turn_log["fallback_claim_targets_omitted"] == ["claim-fallback-1"]
    assert turn_log["fallback_targets_replaced_with_real_candidates"] is True


def test_synthesize_summary_update_uses_state_signals():
    state = {
        "risk_profile": {
            "dominant_risks": ["2 evidence gaps remain unresolved."],
            "support_signals": ["1 claim is strongly supported."],
        },
        "revision_summary": ["claim:claim-main updated status from uncertain to supported (evidence_sync)."],
        "conflict_summary": ["[evidence_conflict] Claim claim-main is challenged by contradictory evidence and should be rechecked."],
    }

    summary = _synthesize_summary_update(state, "summarize_progress")

    assert "summarized" in summary.lower()
    assert "support signals" in summary.lower()
    assert "dominant risks" in summary.lower()


def test_merge_review_state_marks_clarification_question_open_then_resolved():
    from agent_system.environments.env_package.review.state import create_initial_review_state, merge_review_state

    state = create_initial_review_state(mode="s4")
    state = merge_review_state(
        state,
        {
            "requires_clarification": True,
            "clarification_question": "Should the review prioritize empirical support or novelty?",
            "summary_update": "The manager paused for clarification.",
        },
    )
    assert state["clarification_needed"] is True
    assert state["pending_user_question"] == "Should the review prioritize empirical support or novelty?"
    assert any(item["question"] == "Should the review prioritize empirical support or novelty?" and item["status"] == "open" for item in state["unresolved_questions"])

    state = merge_review_state(
        state,
        {
            "requires_clarification": False,
            "simulated_user_reply": "Prioritize empirical support first.",
        },
    )
    assert state["clarification_needed"] is False
    assert state["pending_user_question"] == ""
    assert state["simulated_user_reply"] == "Prioritize empirical support first."
    assert any(item["question"] == "Should the review prioritize empirical support or novelty?" and item["status"] == "resolved" for item in state["unresolved_questions"])



def test_normalize_manager_payload_keeps_policy_provenance():
    from agent_system.environments.env_package.review.state import normalize_manager_payload

    payload = normalize_manager_payload(
        {
            "decision": "continue",
            "action_type": "verify_evidence",
            "selected_agents": ["Evidence Agent"],
            "policy_source": "fallback_inference",
            "policy_notes": [
                "Manager action_type was invalid and was replaced by inferred policy.",
                "Focus was filled from inferred policy context.",
            ],
        },
        available_agents=["Evidence Agent", "Critique Agent"],
    )

    assert payload["policy_source"] == "fallback_inference"
    assert payload["policy_notes"] == [
        "Manager action_type was invalid and was replaced by inferred policy.",
        "Focus was filled from inferred policy context.",
    ]


def test_role_specific_observations_are_focus_aware_and_not_full_paper_replays():
    from agent_system.inference.review_runner import build_manager_observation, build_worker_observation

    repeated_sentence = "This paper studies retrieval robustness under domain shift. "
    task = {
        "review_state": {
            "claims": [{"claim_id": "claim-main", "claim": "The method improves retrieval accuracy.", "status": "uncertain"}],
            "evidence_map": [{"evidence_id": "evidence-1", "claim_id": "claim-main", "evidence": "Table 2 shows gains.", "source": "Table 2", "strength": "medium", "stance": "supports"}],
            "flaw_candidates": [{"flaw_id": "flaw-1", "title": "Potential overclaim", "description": "The gains may not generalize.", "severity": "major", "status": "candidate", "related_claim_ids": ["claim-main"], "evidence_ids": ["evidence-1"]}],
            "unresolved_questions": [{"question_id": "q1", "question": "Are the gains robust?", "status": "open", "related_claim_ids": ["claim-main"]}],
            "evidence_gaps": ["Need stronger evidence for cross-domain robustness."],
            "current_hypotheses": ["The gains may depend on one benchmark."],
            "revision_summary": ["claim-main remains uncertain pending stronger evidence."],
            "conflict_summary": ["No direct conflict yet, but evidence is incomplete."],
            "risk_profile": {"readiness": "needs_targeted_recheck", "dominant_risks": ["evidence gap"], "support_signals": []},
            "dialogue_summary": "The review is tracking one main claim and a robustness risk.",
            "last_focus": "check robustness evidence",
            "active_focus": "check robustness evidence",
            "turn_id": 1,
            "mode": "s4",
        },
        "paper_id": "paper-observation",
        "paper_text": repeated_sentence * 80,
        "user_goal": "Ground the main claim and locate weaknesses.",
        "data_source": "unit-test",
        "max_turns": 4,
        "mode": "s4",
        "turn_logs": [{"turn_id": 1, "decision": "continue", "selected_agents": ["Claim Agent"], "focus": "extract claims"}],
    }
    manager_payload = {
        "action_type": "verify_evidence",
        "focus": "check robustness evidence",
        "rationale": "The main claim needs grounded support.",
        "target_claim_ids": ["claim-main"],
        "target_flaw_ids": ["flaw-1"],
        "target_evidence_ids": ["evidence-1"],
        "target_hypotheses": ["The gains may depend on one benchmark."],
    }

    manager_obs = build_manager_observation(task, ["Claim Agent", "Evidence Agent", "Critique Agent"])
    claim_obs = build_worker_observation(task, manager_payload, "Claim Agent")
    evidence_obs = build_worker_observation(task, manager_payload, "Evidence Agent")
    critique_obs = build_worker_observation(task, manager_payload, "Critique Agent")

    assert "# Manager Risk and Progress Slice" in manager_obs
    assert "# Claim State Slice" in claim_obs
    assert "# Evidence State Slice" in evidence_obs
    assert "# Critique State Slice" in critique_obs
    assert "# Paper Content" not in manager_obs
    assert "# Paper Content" not in claim_obs
    assert "# Paper Content" not in evidence_obs
    assert "# Paper Content" not in critique_obs
    assert len(manager_obs) < len(task["paper_text"])
    assert len(claim_obs) < len(task["paper_text"])
    assert len(evidence_obs) < len(task["paper_text"])
    assert len(critique_obs) < len(task["paper_text"])


def test_action_aware_worker_observation_prioritizes_targets_and_local_state():
    from agent_system.inference.review_runner import build_worker_observation

    task = {
        "review_state": {
            "claims": [
                {"claim_id": "claim-main", "claim": "The method improves retrieval accuracy.", "status": "uncertain"},
                {"claim_id": "claim-side", "claim": "The method also reduces latency.", "status": "supported"},
            ],
            "evidence_map": [
                {"evidence_id": "evidence-1", "claim_id": "claim-main", "evidence": "Table 2 shows gains.", "source": "Table 2", "strength": "medium", "stance": "supports"},
                {"evidence_id": "evidence-2", "claim_id": "claim-side", "evidence": "Appendix reports latency gains.", "source": "Appendix", "strength": "weak", "stance": "supports"},
            ],
            "flaw_candidates": [
                {"flaw_id": "flaw-1", "title": "Potential overclaim", "description": "The gains may not generalize.", "severity": "major", "status": "candidate", "related_claim_ids": ["claim-main"], "evidence_ids": ["evidence-1"]},
            ],
            "unresolved_questions": [{"question_id": "q1", "question": "Are the gains robust?", "status": "open", "related_claim_ids": ["claim-main"]}],
            "evidence_gaps": ["Need stronger evidence for cross-domain robustness."],
            "current_hypotheses": ["The gains may depend on one benchmark."],
            "revision_summary": ["claim-main remains uncertain pending stronger evidence."],
            "conflict_summary": ["Main claim still lacks strong grounding."],
            "risk_profile": {"readiness": "needs_targeted_recheck"},
            "dialogue_summary": "The review is now focused on robustness.",
            "last_focus": "recheck claim-main evidence",
            "active_focus": "recheck claim-main evidence",
            "turn_id": 2,
            "mode": "s4",
        },
        "paper_id": "paper-action-aware",
        "paper_text": "This paper studies retrieval robustness under domain shift. " * 40,
        "user_goal": "Ground claim-main before finalizing.",
        "data_source": "unit-test",
        "max_turns": 4,
        "mode": "s4",
        "turn_logs": [],
    }
    manager_payload = {
        "action_type": "request_evidence_recheck",
        "focus": "recheck claim-main evidence",
        "rationale": "claim-main still lacks strong grounding.",
        "target_claim_ids": ["claim-main"],
        "target_evidence_ids": ["evidence-1"],
        "target_flaw_ids": ["flaw-1"],
        "target_hypotheses": ["The gains may depend on one benchmark."],
    }

    evidence_obs = build_worker_observation(task, manager_payload, "Evidence Agent")

    assert '"action_type": "request_evidence_recheck"' in evidence_obs
    assert 'claim-main' in evidence_obs
    assert 'claim-side' not in evidence_obs
    assert 'Need stronger evidence for cross-domain robustness.' in evidence_obs
    assert 'Are the gains robust?' in evidence_obs


def test_manager_observation_prioritizes_risk_and_open_questions():
    from agent_system.inference.review_runner import build_manager_observation

    task = {
        "review_state": {
            "claims": [{"claim_id": "claim-main", "claim": "The method improves retrieval accuracy.", "status": "uncertain"}],
            "evidence_map": [{"evidence_id": "evidence-1", "claim_id": "claim-main", "evidence": "Table 2 shows gains.", "source": "Table 2", "strength": "medium", "stance": "supports"}],
            "flaw_candidates": [{"flaw_id": "flaw-1", "title": "Potential overclaim", "description": "The gains may not generalize.", "severity": "major", "status": "candidate", "related_claim_ids": ["claim-main"], "evidence_ids": ["evidence-1"]}],
            "unresolved_questions": [
                {"question_id": "q1", "question": "Are the gains robust?", "status": "open", "related_claim_ids": ["claim-main"]},
                {"question_id": "q2", "question": "Was this ablation already addressed?", "status": "resolved", "related_claim_ids": ["claim-main"]},
            ],
            "evidence_gaps": ["Need stronger robustness evidence."],
            "current_hypotheses": ["The gains may depend on one benchmark."],
            "revision_summary": ["claim-main remains uncertain pending stronger evidence."],
            "conflict_summary": ["Main claim still lacks strong grounding."],
            "risk_profile": {"readiness": "needs_targeted_recheck", "support_signals": ["One benchmark shows moderate gains."]},
            "dialogue_summary": "The review is deciding whether more evidence recheck is needed.",
            "last_focus": "recheck claim-main evidence",
            "active_focus": "recheck claim-main evidence",
            "turn_id": 2,
            "mode": "s4",
            "pending_user_question": "",
            "clarification_needed": False,
        },
        "paper_id": "paper-manager-view",
        "paper_text": "This paper studies retrieval robustness under domain shift. " * 40,
        "user_goal": "Decide the next review move based on risk and unresolved issues.",
        "data_source": "unit-test",
        "max_turns": 4,
        "mode": "s4",
        "turn_logs": [{"turn_id": 1, "decision": "continue", "selected_agents": ["Evidence Agent"], "focus": "verify evidence"}],
    }

    obs = build_manager_observation(task, ["Claim Agent", "Evidence Agent", "Critique Agent"])

    assert "# Manager Risk and Progress Slice" in obs
    assert 'open_unresolved_questions' in obs
    assert 'Are the gains robust?' in obs
    assert 'Was this ablation already addressed?' not in obs
    assert 'Need stronger robustness evidence.' in obs
    assert 'One benchmark shows moderate gains.' in obs


def test_general_reviewer_observation_uses_action_aware_compact_slice():
    from agent_system.inference.review_runner import build_worker_observation

    task = {
        "review_state": {
            "claims": [
                {"claim_id": "claim-main", "claim": "The method improves retrieval accuracy.", "status": "uncertain"},
                {"claim_id": "claim-side", "claim": "The method also reduces latency.", "status": "supported"},
            ],
            "evidence_map": [
                {"evidence_id": "evidence-1", "claim_id": "claim-main", "evidence": "Table 2 shows gains.", "source": "Table 2", "strength": "medium", "stance": "supports"},
                {"evidence_id": "evidence-2", "claim_id": "claim-side", "evidence": "Appendix reports latency gains.", "source": "Appendix", "strength": "weak", "stance": "supports"},
            ],
            "flaw_candidates": [
                {"flaw_id": "flaw-1", "title": "Potential overclaim", "description": "The gains may not generalize.", "severity": "major", "status": "candidate", "related_claim_ids": ["claim-main"], "evidence_ids": ["evidence-1"]},
                {"flaw_id": "flaw-2", "title": "Latency caveat", "description": "Latency measurement is incomplete.", "severity": "minor", "status": "candidate", "related_claim_ids": ["claim-side"], "evidence_ids": ["evidence-2"]},
            ],
            "unresolved_questions": [
                {"question_id": "q1", "question": "Are the gains robust?", "status": "open", "related_claim_ids": ["claim-main"]},
                {"question_id": "q2", "question": "Was the latency caveat resolved?", "status": "resolved", "related_claim_ids": ["claim-side"]},
            ],
            "evidence_gaps": ["Need stronger evidence for cross-domain robustness."],
            "current_hypotheses": ["The gains may depend on one benchmark."],
            "revision_summary": ["claim-main remains uncertain pending stronger evidence."],
            "conflict_summary": ["Main claim still lacks strong grounding."],
            "risk_profile": {"readiness": "needs_targeted_recheck"},
            "dialogue_summary": "The general reviewer should summarize the main risk picture.",
            "last_focus": "summarize claim-main review state",
            "active_focus": "summarize claim-main review state",
            "turn_id": 2,
            "mode": "s3",
        },
        "paper_id": "paper-general-reviewer",
        "paper_text": "This paper studies retrieval robustness under domain shift. " * 40,
        "user_goal": "Summarize the main risk picture for claim-main.",
        "data_source": "unit-test",
        "max_turns": 4,
        "mode": "s3",
        "turn_logs": [],
    }
    manager_payload = {
        "action_type": "summarize_progress",
        "focus": "summarize claim-main review state",
        "rationale": "Need a concise risk-oriented synthesis.",
        "target_claim_ids": ["claim-main"],
        "target_evidence_ids": ["evidence-1"],
        "target_flaw_ids": ["flaw-1"],
    }

    obs = build_worker_observation(task, manager_payload, "General Reviewer Agent 1")

    assert '# General Review Slice' in obs
    assert 'claim-main' in obs
    assert 'claim-side' not in obs
    assert 'flaw-1' in obs
    assert 'flaw-2' not in obs
    assert 'Are the gains robust?' in obs
    assert 'Was the latency caveat resolved?' not in obs


def test_run_review_episode_overrides_redundant_evidence_verification_after_evidence_exists():
    responses = {
        "Review Manager Agent": [
            '<json>{"decision":"continue","action_type":"extract_claims","selected_agents":["Claim Agent"],"focus":"extract main claims","rationale":"Start with claims.","claims":[],"evidence_map":[],"flaw_candidates":[],"unresolved_questions":[],"dialogue_summary":"Start with claims.","recommendation":"undecided","final_decision":"undecided","final_report":""}</json>',
            '<json>{"decision":"continue","action_type":"verify_evidence","selected_agents":["Evidence Agent"],"focus":"ground claims","rationale":"Need evidence.","claims":[],"evidence_map":[],"flaw_candidates":[],"unresolved_questions":[],"dialogue_summary":"Ground claims.","recommendation":"undecided","final_decision":"undecided","final_report":""}</json>',
            '<json>{"decision":"continue","action_type":"verify_evidence","selected_agents":["Evidence Agent"],"focus":"check more evidence","rationale":"Keep verifying.","claims":[],"evidence_map":[],"flaw_candidates":[],"unresolved_questions":[],"dialogue_summary":"Still checking evidence.","recommendation":"undecided","final_decision":"undecided","final_report":""}</json>',
            # Mainline-Final-Integrated P0-2: with the new override placement
            # the manager turn after evidence formation is steered into
            # ``analyze_flaws`` rather than ``finalize`` so that a flaw is
            # discovered after the negative-evidence pass; the original test
            # contract -- one analyze_flaws turn ending with at least one
            # flaw_candidate -- is preserved.
            '<json>{"decision":"continue","action_type":"analyze_flaws","selected_agents":["Critique Agent"],"focus":"identify weaknesses","rationale":"Analyze flaws now.","claims":[],"evidence_map":[],"flaw_candidates":[],"unresolved_questions":[],"dialogue_summary":"Analyze flaws.","recommendation":"undecided","final_decision":"undecided","final_report":""}</json>',
            '<json>{"decision":"finalize","action_type":"finalize","selected_agents":[],"focus":"wrap up final","rationale":"Final.","claims":[],"evidence_map":[],"flaw_candidates":[],"unresolved_questions":[],"dialogue_summary":"Final.","recommendation":"reject","final_decision":"reject","final_report":"Final Decision: Reject"}</json>',
        ],
        "Claim Agent": [
            '<json>{"claims":[{"claim_id":"claim-main","claim":"The method improves retrieval robustness.","importance":"high","status":"uncertain","claim_type":"empirical","coverage_tags":["empirical","method"],"evidence_need":"result/table evidence"},{"claim_id":"claim-method","claim":"The method uses a robustness-oriented retrieval design.","importance":"medium","status":"uncertain","claim_type":"method","coverage_tags":["method"],"evidence_need":"method evidence"},{"claim_id":"claim-scope","claim":"The robustness gains may be limited by evaluation scope.","importance":"medium","status":"uncertain","claim_type":"limitation_or_boundary","coverage_tags":["limitation","scope"],"evidence_need":"scope/limitation evidence"}],"unresolved_questions":["What evidence supports the main claim?"],"dialogue_summary":"Main claim extracted.","recommendation":"undecided"}</json>'
        ],
        "Evidence Agent": [
            '<json>{"evidence_map":[{"evidence_id":"evidence-1","claim_id":"claim-main","evidence":"Table 2 shows moderate robustness gains.","source":"Table 2","strength":"medium","stance":"supports"}],"unresolved_questions":["What weakness remains despite the gains?"],"dialogue_summary":"Evidence grounding added.","recommendation":"undecided"}</json>',
            '<json>{"evidence_map":[{"evidence_id":"evidence-2","claim_id":"claim-main","evidence":"The recheck still lacks broader robustness evidence.","source":"Table 2","strength":"missing","stance":"missing"}],"unresolved_questions":["Do the gains generalize beyond Table 2?"],"dialogue_summary":"Recovery evidence recheck added missing-evidence signal.","recommendation":"reject"}</json>',
            '<json>{"evidence_map":[{"evidence_id":"evidence-3","claim_id":"claim-main","evidence":"No direct negative quote verifies the robustness flaw.","source":"Evidence recheck","strength":"missing","stance":"missing"}],"unresolved_questions":["No verified negative quote was found for flaw-1."],"dialogue_summary":"Negative evidence formation did not find a verified quote.","recommendation":"reject"}</json>',
            # Mainline-Final-Integrated P0-2: extra slot for any follow-up
            # ``request_evidence_recheck`` driven by recovery-relevant
            # overrides at later turns.
            '<json>{"evidence_map":[{"evidence_id":"evidence-4","claim_id":"claim-main","evidence":"No further evidence located.","source":"Evidence recheck","strength":"missing","stance":"missing"}],"unresolved_questions":["No verified quote was found."],"dialogue_summary":"Follow-up evidence recheck.","recommendation":"reject"}</json>',
        ],
        "Critique Agent": [
            '<json>{"flaw_candidates":[{"flaw_id":"flaw-1","title":"Limited robustness evidence","description":"The robustness gains rely on a narrow benchmark set.","severity":"major","related_claim_ids":["claim-main"],"evidence_ids":["evidence-1"],"confidence":0.7}],"unresolved_questions":["Do the gains generalize beyond Table 2?"],"dialogue_summary":"Grounded flaw analysis added.","recommendation":"reject"}</json>',
            '<json>{"action":"blocked","target_type":"flaw","target_id":"flaw-1","old_status":"candidate","new_status":"candidate","blocked_reason":"No verified negative evidence supports downgrading or retracting the flaw.","missing_requirements":["verified negative evidence"]}</json>'
        ],
    }
    call_counts = {key: 0 for key in responses}

    def fake_generate(agent_id: str, prompt: str) -> str:
        idx = call_counts[agent_id]
        call_counts[agent_id] += 1
        return responses[agent_id][idx]

    result = run_review_episode(
        extras={
            "paper_id": "paper-flaw-override",
            "paper_text": "A paper with some evidence but an unarticulated weakness.",
            "user_goal": "Move beyond repeated evidence verification once evidence exists.",
            "data_source": "unit-test",
            "ground_truth_decision": "reject",
            "reference_review": "Final Decision: Reject",
        },
        mode="s4",
        generate_fn=fake_generate,
        max_turns=5,
        max_workers_per_turn=2,
    )

    # Mainline-Final-Integrated P0-2: at T3 the manager would still infer
    # ``analyze_flaws`` via ``flaw_progress_override`` (verify→analyze chain),
    # but the new ``hard_negative_discovery_override`` placement preempts it
    # because evidence_map>=1 and no grounded negative evidence exists.  T3
    # therefore routes to ``request_evidence_recheck`` and the paper enters
    # the recovery phase, where the subsequent turns are managed by the
    # recovery phase protocol (challenge / recheck) rather than a free
    # ``analyze_flaws`` turn.  The original test contract — that a redundant
    # verify_evidence turn is overridden once evidence already exists — is
    # preserved by checking the override fires and the recovery phase is
    # entered, instead of requiring a particular downstream worker call.
    neg_turn = result["turn_logs"][2]
    assert neg_turn["effective_action_type"] in {"analyze_flaws", "request_evidence_recheck"}
    assert neg_turn["policy_source"] in {
        "flaw_progress_override",
        "s4_evidence_to_flaw_override",
        "hard_negative_discovery_override",
    }
    assert any(
        ("flaw analysis" in note.lower() or "hard-negative" in note.lower())
        for note in neg_turn["policy_notes"]
    )
    # Either the legacy flaw_progress route ran (and produced a flaw) or the
    # new hard-negative discovery route ran (and produced a missing-stance
    # evidence item in evidence_map).
    em_after = result["review_state"]["evidence_map"]
    has_negative_evidence = any(
        str(item.get("stance") or "").lower() in {"missing", "contradicts"}
        for item in em_after
        if isinstance(item, dict)
    )
    assert len(result["review_state"]["flaw_candidates"]) >= 1 or has_negative_evidence


def test_run_review_episode_overrides_redundant_claim_extraction_after_claims_exist():
    responses = {
        "Review Manager Agent": [
            '<json>{"decision":"continue","action_type":"extract_claims","selected_agents":["Claim Agent"],"focus":"extract main claims","rationale":"Start with claims.","claims":[],"evidence_map":[],"flaw_candidates":[],"unresolved_questions":[],"dialogue_summary":"Start with claims.","recommendation":"undecided","final_decision":"undecided","final_report":""}</json>',
            '<json>{"decision":"continue","action_type":"extract_claims","selected_agents":["Claim Agent"],"focus":"extract more claims","rationale":"Keep extracting.","claims":[],"evidence_map":[],"flaw_candidates":[],"unresolved_questions":[],"dialogue_summary":"Still extracting claims.","recommendation":"undecided","final_decision":"undecided","final_report":""}</json>',
            '<json>{"decision":"finalize","action_type":"finalize","selected_agents":[],"focus":"wrap up","rationale":"Enough signal to decide.","claims":[],"evidence_map":[],"flaw_candidates":[],"unresolved_questions":[],"dialogue_summary":"Wrap up.","recommendation":"reject","final_decision":"reject","final_report":"Final Decision: Reject"}</json>',
        ],
        "Claim Agent": [
            '<json>{"claims":[{"claim_id":"claim-main","claim":"The method improves retrieval robustness.","importance":"high","status":"uncertain","claim_type":"empirical","coverage_tags":["empirical","method"],"evidence_need":"result/table evidence"},{"claim_id":"claim-method","claim":"The method uses a robustness-oriented retrieval design.","importance":"medium","status":"uncertain","claim_type":"method","coverage_tags":["method"],"evidence_need":"method evidence"},{"claim_id":"claim-scope","claim":"The robustness gains may be limited by evaluation scope.","importance":"medium","status":"uncertain","claim_type":"limitation_or_boundary","coverage_tags":["limitation","scope"],"evidence_need":"scope/limitation evidence"}],"unresolved_questions":["What evidence supports the main claim?"],"dialogue_summary":"Main claim extracted.","recommendation":"undecided"}</json>'
        ],
        "Evidence Agent": [
            '<json>{"evidence_map":[{"evidence_id":"evidence-1","claim_id":"claim-main","evidence":"Table 2 shows moderate robustness gains.","source":"Table 2","strength":"medium","stance":"supports"}],"unresolved_questions":["Are the gains consistent across settings?"],"dialogue_summary":"Evidence grounding added.","recommendation":"undecided"}</json>',
            # Mainline-Final-Integrated P0-2: a second Evidence Agent response
            # is added for the ``hard_negative_discovery_override`` request
            # that fires before ``finalize`` once evidence_map is non-empty.
            '<json>{"evidence_map":[{"evidence_id":"evidence-2","claim_id":"claim-main","evidence":"No direct negative quote was found.","source":"Recheck pass","strength":"missing","stance":"missing"}],"unresolved_questions":["No verified negative quote was located."],"dialogue_summary":"Negative discovery pass returned no verified quote.","recommendation":"reject"}</json>',
        ],
    }
    call_counts = {key: 0 for key in responses}

    def fake_generate(agent_id: str, prompt: str) -> str:
        idx = call_counts[agent_id]
        call_counts[agent_id] += 1
        return responses[agent_id][idx]

    result = run_review_episode(
        extras={
            "paper_id": "paper-extract-override",
            "paper_text": "A paper claiming better robustness with limited evidence.",
            "user_goal": "Move beyond repeated claim extraction once claims exist.",
            "data_source": "unit-test",
            "ground_truth_decision": "reject",
            "reference_review": "Final Decision: Reject",
        },
        mode="s4",
        generate_fn=fake_generate,
        max_turns=3,
        max_workers_per_turn=2,
    )

    # ``evidence_progress_override`` still fires at T2 because the
    # ``hard_negative_discovery_override`` gate requires ``evidence_map >= 1``
    # at decision time, and the very first verify pass starts from
    # ``evidence_map == 0``.  The original test contract is preserved.
    assert result["turn_logs"][1]["action_type"] == "verify_evidence"
    assert result["turn_logs"][1]["policy_source"] == "evidence_progress_override"
    assert any("moved beyond claim extraction" in note for note in result["turn_logs"][1]["policy_notes"])
    assert len(result["review_state"]["evidence_map"]) >= 1


# ============================================================
# P2: Conflict → Recovery focused tests
# ============================================================


def test_conflict_block_override_prevents_premature_auto_finalize():
    """When unresolved conflicts exist and no recovery action has been taken,
    auto-finalize should be blocked and redirected to a recovery action."""
    from agent_system.review_manager_policy import apply_finalize_policy, _has_prior_recovery_action

    state = {
        "claims": [{"claim_id": "claim-main", "status": "uncertain"}],
        "evidence_map": [{"evidence_id": "evidence-1", "claim_id": "claim-main", "strength": "weak", "stance": "contradicts"}],
        "flaw_candidates": [{"flaw_id": "flaw-1", "status": "candidate", "severity": "major"}],
        "unresolved_questions": [{"question": "Is the claim overstated?", "status": "open"}],
        "conflict_notes": [{"note": "Evidence contradicts the claim.", "claim_id": "claim-main", "evidence_id": "evidence-1"}],
        "risk_profile": {"open_question_count": 1, "conflict_count": 1, "readiness": "not_ready"},
        "evidence_gaps": [],
        "current_hypotheses": [],
        "clarification_needed": False,
        "pending_user_question": "",
    }
    manager_payload = {
        "decision": "continue",
        "action_type": "analyze_flaws",
        "selected_agents": ["Critique Agent"],
        "focus": "analyze flaws",
        "rationale": "Check flaws.",
        "policy_notes": [],
    }
    worker_payloads = [
        {"agent_id": "Critique Agent", "payload": {"flaw_candidates": [{"flaw_id": "flaw-1", "severity": "major"}]}}
    ]
    recent_turn_logs = [
        {"action_type": "extract_claims", "effective_action_type": "extract_claims", "policy_source": "manager_model"},
        {"action_type": "verify_evidence", "effective_action_type": "verify_evidence", "policy_source": "evidence_progress_override"},
    ]

    # step 4 with turn_cap 5 should normally auto-finalize since state is complete,
    # but conflict_block should prevent it
    result, selected = apply_finalize_policy(
        manager_payload=manager_payload,
        state=state,
        mode="s4",
        step=4,
        turn_cap=5,
        worker_ids=["Claim Agent", "Evidence Agent", "Critique Agent"],
        worker_limit=1,
        selected_workers=["Critique Agent"],
        worker_payloads=worker_payloads,
        recent_turn_logs=recent_turn_logs,
    )

    assert result["decision"] == "continue"
    assert result["policy_source"] == "conflict_block_override"
    assert result["action_type"] in {"challenge_previous_hypothesis", "request_evidence_recheck"}
    assert any("unresolved conflict" in note.lower() for note in result["policy_notes"])


def test_s4_conflict_recovery_override_routes_to_challenge():
    """When the manager requests analyze_flaws but conflicts exist (and no prior
    recovery action), the policy fallback should redirect to challenge/recheck."""
    state = {
        "claims": [{"claim_id": "claim-main", "status": "uncertain"}],
        "evidence_map": [{"evidence_id": "evidence-1", "claim_id": "claim-main", "strength": "medium", "stance": "contradicts"}],
        "flaw_candidates": [{"flaw_id": "flaw-1", "status": "candidate", "severity": "major"}],
        "unresolved_questions": [],
        "conflict_notes": [{"note": "Contradicts.", "claim_id": "claim-main", "evidence_id": "evidence-1"}],
        "risk_profile": {"open_question_count": 0, "conflict_count": 1, "readiness": "not_ready"},
        "evidence_gaps": [],
        "current_hypotheses": [],
        "clarification_needed": False,
        "pending_user_question": "",
    }
    manager_payload = {
        "decision": "continue",
        "action_type": "analyze_flaws",
        "selected_agents": ["Critique Agent"],
        "focus": "analyze flaws",
        "rationale": "Continue with flaws.",
    }

    normalized = _apply_manager_policy_fallback(
        manager_payload=manager_payload,
        state=state,
        mode="s4",
        worker_ids=["Claim Agent", "Evidence Agent", "Critique Agent"],
        worker_limit=2,
        recent_turn_logs=[
            {"action_type": "extract_claims", "effective_action_type": "extract_claims", "policy_source": "manager_model"},
        ],
    )

    assert normalized["action_type"] == "challenge_previous_hypothesis"
    assert normalized["policy_source"] in {"s4_conflict_recovery_override", "s4_challenge_override"}


def test_blocked_recovery_payload_is_salvaged_to_patch():
    blocked = {
        "action": "blocked",
        "blocked_reason": "No valid downgrade/retraction is justifiable given current evidence.",
        "missing_requirements": [],
    }
    salvaged = _maybe_salvage_recovery_payload(
        agent_id="Critique Agent",
        worker_payload=blocked,
        state={
            "claims": [{"claim_id": "claim-main", "status": "uncertain"}],
            "evidence_map": [{"evidence_id": "evidence-1", "claim_id": "claim-main", "stance": "contradicts", "verified_grounding_label": "paper_grounded_exact", "semantic_grounding_label": "semantic_negative_verified"}],
        },
        manager_payload={
            "action_type": "challenge_previous_hypothesis",
            "effective_action_type": "challenge_previous_hypothesis",
            "target_claim_ids": ["claim-main"],
            "target_evidence_ids": ["evidence-1"],
        },
    )

    assert salvaged["action"] == "apply_recovery_patch"
    assert salvaged["target_type"] == "claim"
    assert salvaged["target_id"] == "claim-main"
    assert salvaged["new_status"] == "unsupported"
    assert salvaged["_recovery_patch_source"] == "system_salvaged"




def test_build_turn_log_does_not_mark_plain_recheck_as_recovery_attempt():
    turn_log = build_turn_log(
        turn_id=3,
        manager_payload={
            "decision": "continue",
            "action_type": "request_evidence_recheck",
            "effective_action_type": "verify_evidence",
            "policy_source": "manager_model",
            "selected_agents": ["Evidence Agent"],
            "target_claim_ids": ["claim-main"],
        },
        worker_payloads=[
            {
                "agent_id": "Evidence Agent",
                "payload": {
                    "evidence_map": [
                        {
                            "evidence_id": "e1",
                            "claim_id": "claim-main",
                            "evidence": "Need stronger support.",
                            "source": "Table 2",
                            "strength": "missing",
                            "stance": "missing",
                        }
                    ]
                },
            }
        ],
        state={
            "claims": [{"claim_id": "claim-main", "status": "uncertain"}],
            "evidence_map": [],
            "flaw_candidates": [],
            "risk_profile": {},
            "revision_summary": [],
            "conflict_summary": [],
            "evidence_gaps": [],
            "unresolved_questions": [],
            "pending_user_question": "",
            "simulated_user_reply": "",
        },
        revision_events=[],
        conflict_events=[],
        previous_action_type="verify_evidence",
    )

    assert turn_log["recovery_attempted"] is False
    assert turn_log["recovery_patch_mode_entered"] is False
    assert turn_log["recovery_emission_expected"] is False
    assert turn_log["recovery_emitted"] is False
    assert turn_log["turn_mode"] == "normal_evidence"
    assert turn_log["emission_failure_code"] == ""
    assert turn_log["recovery_failure_code"] == ""
    assert turn_log["recovery_details"] == []


def test_build_turn_log_uses_patch_log_as_single_recovery_truth_source():
    turn_log = build_turn_log(
        turn_id=5,
        manager_payload={
            "decision": "continue",
            "action_type": "challenge_previous_hypothesis",
            "effective_action_type": "challenge_previous_hypothesis",
            "policy_source": "manager_model",
            "target_claim_ids": ["claim-main"],
        },
        worker_payloads=[
            {
                "agent_id": "Critique Agent",
                "payload": {
                    "action": "apply_recovery_patch",
                    "target_type": "claim",
                    "target_id": "claim-main",
                    "old_status": "supported",
                    "new_status": "unsupported",
                    "supporting_evidence_ids": ["e1"],
                    "_recovery_patch_source": "model_generated",
                },
            }
        ],
        state={
            "claims": [{"claim_id": "claim-main", "status": "unsupported"}],
            "evidence_map": [],
            "flaw_candidates": [],
            "risk_profile": {},
            "revision_summary": [],
            "conflict_summary": [],
            "evidence_gaps": [],
            "unresolved_questions": [],
            "pending_user_question": "",
            "simulated_user_reply": "",
            "_latest_patch_log": {
                "recovery_attempted": True,
                "recovery_validated": True,
                "recovery_committed": True,
                "recovery_failure_code": "SUCCESS",
                "recovery_failure_message": "",
                "recovery_target_id": "claim-main",
                "recovery_target_type": "claim",
                "old_status": "supported",
                "new_status": "unsupported",
                "recovery_patch_source": "model_generated",
                "recovery_state_delta": {"consistency_improved": True},
            },
        },
        revision_events=[],
        conflict_events=[],
        previous_action_type="verify_evidence",
    )

    assert turn_log["recovery_attempted"] is True
    assert turn_log["recovery_validated"] is True
    assert turn_log["recovery_committed"] is True
    assert turn_log["recovery_success"] is False
    assert turn_log["recovery_blocked_by"] == ""
    assert turn_log["recovery_patch_source"] == "model_generated"
    # The stratified 4-layer taxonomy must reflect that the patch was
    # validated and committed by the validator but the ReviewState did NOT
    # actually mutate (no revision events were recorded for this turn).
    assert turn_log["recovery_layer_validated"] is True
    assert turn_log["recovery_layer_committed"] is True
    assert turn_log["recovery_layer_state_mutation_applied"] is False
    assert turn_log["recovery_layer_hygiene_delta_improved"] is False
    assert turn_log["recovery_effective_repair"] is False
    assert turn_log["recovery_layer"] == "patch_committed"


def test_build_turn_log_recovery_layer_marks_effective_repair_when_state_mutates():
    """When the validator committed a patch *and* the ReviewState recorded a
    status-field revision event, the 4-layer taxonomy must escalate to the
    top layer (``hygiene_delta_improved``) and the paper-facing
    ``recovery_effective_repair`` counter must be ``True``.
    """

    turn_log = build_turn_log(
        turn_id=6,
        manager_payload={
            "decision": "continue",
            "action_type": "challenge_previous_hypothesis",
            "effective_action_type": "challenge_previous_hypothesis",
            "policy_source": "manager_model",
            "target_claim_ids": ["claim-main"],
        },
        worker_payloads=[
            {
                "agent_id": "Critique Agent",
                "payload": {
                    "action": "apply_recovery_patch",
                    "target_type": "claim",
                    "target_id": "claim-main",
                    "old_status": "supported",
                    "new_status": "unsupported",
                    "supporting_evidence_ids": ["e1"],
                    "_recovery_patch_source": "model_generated",
                },
            }
        ],
        state={
            "claims": [{"claim_id": "claim-main", "status": "unsupported"}],
            "evidence_map": [],
            "flaw_candidates": [],
            "risk_profile": {},
            "revision_summary": [],
            "conflict_summary": [],
            "evidence_gaps": [],
            "unresolved_questions": [],
            "pending_user_question": "",
            "simulated_user_reply": "",
            "_latest_patch_log": {
                "recovery_attempted": True,
                "recovery_validated": True,
                "recovery_committed": True,
                "recovery_failure_code": "SUCCESS",
                "recovery_failure_message": "",
                "recovery_target_id": "claim-main",
                "recovery_target_type": "claim",
                "old_status": "supported",
                "new_status": "unsupported",
                "recovery_patch_source": "model_generated",
                "recovery_state_delta": {"consistency_improved": True},
            },
        },
        revision_events=[
            {
                "entity_type": "claim",
                "entity_id": "claim-main",
                "field": "status",
                "old_value": "supported",
                "new_value": "unsupported",
                "reason": "real_strong_support_missing",
            }
        ],
        conflict_events=[],
        previous_action_type="verify_evidence",
    )

    assert turn_log["recovery_success"] is True
    assert turn_log["recovery_commit_applied"] is True
    assert turn_log["recovery_layer_validated"] is True
    assert turn_log["recovery_layer_committed"] is True
    assert turn_log["recovery_layer_state_mutation_applied"] is True
    assert turn_log["recovery_layer_hygiene_delta_improved"] is True
    assert turn_log["recovery_effective_repair"] is True
    assert turn_log["recovery_layer"] == "hygiene_delta_improved"


def test_build_turn_log_recovery_layer_recognises_partially_supported_to_unsupported_commit():
    """``partially_supported -> unsupported`` is a substantive claim demotion
    and must be recognised by ``COMMIT_TRANSITIONS`` so the resulting recovery
    turn reaches the ``hygiene_delta_improved`` layer.

    The V17 hardneg8 audit surfaced a turn with this exact transition that
    was previously mis-labelled ``commit_applied=False`` even though the
    state genuinely mutated.
    """

    turn_log = build_turn_log(
        turn_id=4,
        manager_payload={
            "decision": "continue",
            "action_type": "challenge_previous_hypothesis",
            "effective_action_type": "challenge_previous_hypothesis",
            "policy_source": "manager_model",
            "target_claim_ids": ["claim-1"],
        },
        worker_payloads=[
            {
                "agent_id": "Critique Agent",
                "payload": {
                    "action": "apply_recovery_patch",
                    "target_type": "claim",
                    "target_id": "claim-1",
                    "old_status": "partially_supported",
                    "new_status": "unsupported",
                    "supporting_evidence_ids": ["e3"],
                    "_recovery_patch_source": "system_salvaged",
                },
            }
        ],
        state={
            "claims": [{"claim_id": "claim-1", "status": "unsupported"}],
            "evidence_map": [],
            "flaw_candidates": [],
            "risk_profile": {},
            "revision_summary": [],
            "conflict_summary": [],
            "evidence_gaps": [],
            "unresolved_questions": [],
            "pending_user_question": "",
            "simulated_user_reply": "",
            "_latest_patch_log": {
                "recovery_attempted": True,
                "recovery_validated": True,
                "recovery_committed": True,
                "recovery_failure_code": "SUCCESS",
                "recovery_failure_message": "",
                "recovery_target_id": "claim-1",
                "recovery_target_type": "claim",
                "old_status": "partially_supported",
                "new_status": "unsupported",
                "recovery_patch_source": "system_salvaged",
                "recovery_state_delta": {"consistency_improved": True},
            },
        },
        revision_events=[
            {
                "entity_type": "claim",
                "entity_id": "claim-1",
                "field": "status",
                "before": "partially_supported",
                "after": "unsupported",
                "reason": "recovery_patch_committed",
            }
        ],
        conflict_events=[],
        previous_action_type="verify_evidence",
    )

    assert turn_log["recovery_success"] is True
    assert turn_log["recovery_commit_applied"] is True
    assert turn_log["recovery_layer_state_mutation_applied"] is True
    assert turn_log["recovery_layer_hygiene_delta_improved"] is True
    assert turn_log["recovery_effective_repair"] is True
    assert turn_log["recovery_layer"] == "hygiene_delta_improved"


def test_build_turn_log_does_not_reuse_previous_patch_log_on_summary_turn():
    turn_log = build_turn_log(
        turn_id=7,
        manager_payload={
            "decision": "continue",
            "action_type": "summarize_progress",
            "effective_action_type": "summarize_progress",
            "policy_source": "recovery_target_exhausted_override",
            "target_claim_ids": [],
        },
        worker_payloads=[],
        state={
            "claims": [{"claim_id": "claim-main", "status": "unsupported"}],
            "evidence_map": [],
            "flaw_candidates": [],
            "risk_profile": {},
            "revision_summary": [],
            "conflict_summary": [],
            "evidence_gaps": [],
            "unresolved_questions": [],
            "pending_user_question": "",
            "simulated_user_reply": "",
            "_latest_patch_log": {
                "recovery_attempted": True,
                "recovery_validated": True,
                "recovery_committed": True,
                "recovery_failure_code": "SUCCESS",
                "recovery_target_id": "claim-main",
                "old_status": "uncertain",
                "new_status": "unsupported",
            },
        },
        revision_events=[],
        conflict_events=[],
        previous_action_type="challenge_previous_hypothesis",
    )

    assert turn_log["recovery_attempted"] is False
    assert turn_log["recovery_validated"] is False
    assert turn_log["recovery_committed"] is False
    assert turn_log["recovery_failure_code"] == ""
    assert turn_log["recovery_target_id"] == ""


def test_turn_level_recovery_salvage_replaces_blocked_critique_payload():
    worker_payloads = [
        {
            "agent_id": "Critique Agent",
            "payload": {
                "action": "blocked",
                "blocked_reason": "No valid downgrade/retraction is justifiable given current evidence.",
                "missing_requirements": [],
            },
        },
        {
            "agent_id": "Evidence Agent",
            "payload": {
                "evidence_map": [
                    {
                        "evidence_id": "evidence-1",
                        "claim_id": "claim-main",
                        "evidence": "Table 3 weakens the claim.",
                        "source": "Table 3",
                        "strength": "weak",
                        "stance": "contradicts",
                    }
                ]
            },
        },
    ]
    trace_item = {"worker_calls": [{"agent_id": "Critique Agent", "payload": worker_payloads[0]["payload"]}]}
    _maybe_salvage_turn_level_recovery_patch(
        worker_payloads,
        state={"claims": [{"claim_id": "claim-main", "status": "uncertain"}]},
        manager_payload={
            "action_type": "challenge_previous_hypothesis",
            "effective_action_type": "challenge_previous_hypothesis",
            "target_claim_ids": ["claim-main"],
        },
        trace_item=trace_item,
    )

    assert worker_payloads[0]["agent_id"] == "Evidence Agent"
    assert worker_payloads[-1]["payload"]["action"] == "apply_recovery_patch"
    assert worker_payloads[-1]["payload"]["_recovery_patch_source"] == "system_salvaged"
    assert worker_payloads[-1]["payload"]["target_id"] == "claim-main"
    assert trace_item["worker_calls"][0]["salvaged_recovery_patch"] is True
    from agent_system.environments.env_package.review.state import merge_review_state

    state = {"claims": [{"claim_id": "claim-main", "status": "uncertain"}], "evidence_map": []}
    for worker in worker_payloads:
        state = merge_review_state(state, worker["payload"])
    assert state["claims"][0]["status"] == "unsupported"
    assert state["_latest_patch_log"]["recovery_committed"] is True


def test_turn_level_recovery_salvage_skips_when_only_synthetic_marker_available():
    """Bug B fix: when both Critique and Evidence return blocked with only
    missing-evidence reasons (i.e. no real contradictory or verified-negative
    evidence is available), the turn-level salvage must NOT synthesize an
    `evidence-recovery-missing-*` marker patch. Such patches are always
    rejected by the validator as `EVIDENCE_SEMANTIC_MISMATCH` and only waste
    an emit→validate→reject round-trip. The original blocked payloads must
    remain untouched so the recovery turn is recorded as `blocked` rather
    than `recovery_attempted` with a doomed patch.
    """
    worker_payloads = [
        {
            "agent_id": "Critique Agent",
            "payload": {
                "action": "blocked",
                "target_type": "claim",
                "target_id": "claim-main",
                "old_status": "partially_supported",
                "new_status": "partially_supported",
                "blocked_reason": "Paper excerpt is incomplete; full text required to validate the result.",
                "missing_requirements": ["Complete results table."],
            },
        },
        {
            "agent_id": "Evidence Agent",
            "payload": {
                "action": "blocked",
                "target_type": "claim",
                "target_id": "claim-main",
                "old_status": "partially_supported",
                "new_status": "partially_supported",
                "blocked_reason": "Insufficient evidence is available to verify the claim.",
                "missing_requirements": ["Grounded quantitative evidence."],
            },
        },
    ]
    snapshot_critique_payload = dict(worker_payloads[0]["payload"])
    snapshot_evidence_payload = dict(worker_payloads[1]["payload"])
    manager_payload = {
        "action_type": "challenge_previous_hypothesis",
        "effective_action_type": "challenge_previous_hypothesis",
        "target_claim_ids": ["claim-main"],
        "target_evidence_ids": [],
    }
    trace_item = {"worker_calls": [{"agent_id": "Critique Agent", "payload": worker_payloads[0]["payload"]}]}
    _maybe_salvage_turn_level_recovery_patch(
        worker_payloads,
        state={
            "claims": [{"claim_id": "claim-main", "status": "partially_supported"}],
            "evidence_map": [
                {"evidence_id": "evidence-positive", "claim_id": "claim-main", "strength": "strong", "stance": "supports"}
            ],
        },
        manager_payload=manager_payload,
        trace_item=trace_item,
    )

    # No synthetic-marker patch was injected: both original blocked payloads survive.
    assert len(worker_payloads) == 2
    assert worker_payloads[0]["agent_id"] == "Critique Agent"
    assert worker_payloads[0]["payload"] == snapshot_critique_payload
    assert worker_payloads[1]["agent_id"] == "Evidence Agent"
    assert worker_payloads[1]["payload"] == snapshot_evidence_payload
    # Manager target_evidence_ids is not polluted with a synthetic id.
    assert manager_payload["target_evidence_ids"] == []
    # Trace is not mutated to claim a salvage happened.
    assert "salvaged_recovery_patch" not in trace_item["worker_calls"][0]

    from agent_system.environments.env_package.review.state import merge_review_state

    state = {"claims": [{"claim_id": "claim-main", "status": "partially_supported"}], "evidence_map": []}
    for worker in worker_payloads:
        state = merge_review_state(state, worker["payload"])
    # Claim status is unchanged and there is no doomed-patch failure log.
    assert state["claims"][0]["status"] == "partially_supported"
    latest = state.get("_latest_patch_log") or {}
    assert latest.get("recovery_committed", False) is False
    assert latest.get("recovery_failure_code", "") != "EVIDENCE_SEMANTIC_MISMATCH"


def test_build_blocked_missing_recovery_salvage_returns_empty_list():
    """Bug B regression guard: the helper that used to mint synthetic
    `evidence-recovery-missing-*` markers and an `unsupported` claim patch
    is permanently disabled. It must return [] regardless of inputs so
    that no doomed patch is ever produced."""
    from agent_system.inference.review_runner import _build_blocked_missing_recovery_salvage

    worker_payloads = [
        {
            "agent_id": "Critique Agent",
            "payload": {
                "action": "blocked",
                "target_type": "claim",
                "target_id": "claim-main",
                "blocked_reason": "Insufficient evidence to validate the claim.",
                "missing_requirements": ["Complete results table."],
            },
        }
    ]
    state = {"claims": [{"claim_id": "claim-main", "status": "supported"}], "evidence_map": []}
    manager_payload = {
        "action_type": "challenge_previous_hypothesis",
        "target_claim_ids": ["claim-main"],
        "target_evidence_ids": [],
    }
    salvage_items = _build_blocked_missing_recovery_salvage(worker_payloads, state, manager_payload)
    assert salvage_items == []
    # Should not mutate manager_payload or state with synthetic markers.
    assert manager_payload["target_evidence_ids"] == []
    assert state["evidence_map"] == []


def test_apply_recovery_phase_protocol_blocks_early_finalize_until_recovery_is_terminal():
    from agent_system.inference.review_runner import _apply_recovery_phase_protocol

    payload = _apply_recovery_phase_protocol(
        manager_payload={
            "decision": "finalize",
            "action_type": "summarize_progress",
            "policy_source": "manager_model",
        },
        state={
            "phase": "recovery",
            "phase_turn_index": 1,
            "claims": [{"claim_id": "claim-main", "status": "supported"}],
            "evidence_map": [
                {
                    "evidence_id": "e-neg",
                    "claim_id": "claim-main",
                    "stance": "missing",
                    "strength": "missing",
                    "verified_grounding_label": "paper_grounded_exact",
                    "semantic_grounding_label": "semantic_negative_verified",
                }
            ],
            "flaw_candidates": [],
            "conflict_notes": [{"conflict_id": "c1", "status": "open"}],
            "_latest_patch_log": {
                "recovery_attempted": True,
                "recovery_validated": False,
                "recovery_committed": False,
                "recovery_failure_code": "",
            },
        },
        mode="s4",
        worker_ids=["Claim Agent", "Evidence Agent", "Critique Agent"],
        worker_limit=3,
        recent_turn_logs=[
            {
                "turn_id": 1,
                "phase_after_action": "recovery",
                "recovery_patch_mode_entered": True,
                "recovery_committed": False,
                "action_type": "challenge_previous_hypothesis",
                "effective_action_type": "challenge_previous_hypothesis",
            }
        ],
    )

    assert payload["phase"] == "recovery"
    assert payload["turn_mode"] in {"normal_evidence", "recovery_patch"}
    assert payload["decision"] == "continue"
    assert payload["action_type"] in {"challenge_previous_hypothesis", "request_evidence_recheck"}
    assert payload["finalize_blocked_by_phase"] is True
    assert payload["early_finalize_attempted"] is True
    assert payload["phase_hold_reason"]


def test_apply_recovery_phase_protocol_respects_exhausted_recovery_target_summary():
    from agent_system.inference.review_runner import _apply_recovery_phase_protocol

    payload = _apply_recovery_phase_protocol(
        manager_payload={
            "decision": "continue",
            "action_type": "summarize_progress",
            "effective_action_type": "summarize_progress",
            "policy_source": "recovery_target_exhausted_override",
            "target_claim_ids": [],
            "selected_agents": [],
        },
        state={
            "phase": "recovery",
            "phase_turn_index": 1,
            "conflict_notes": [{"conflict_id": "c1", "status": "open"}],
            "_latest_patch_log": {
                "recovery_attempted": True,
                "recovery_validated": False,
                "recovery_committed": False,
                "recovery_failure_code": "",
            },
        },
        mode="s4",
        worker_ids=["Claim Agent", "Evidence Agent", "Critique Agent"],
        worker_limit=2,
        recent_turn_logs=[
            {
                "turn_id": 4,
                "phase_after_action": "recovery",
                "recovery_patch_mode_entered": True,
                "action_type": "challenge_previous_hypothesis",
                "effective_action_type": "challenge_previous_hypothesis",
            }
        ],
    )

    assert payload["phase"] == "normal_review"
    assert payload["action_type"] == "summarize_progress"
    assert payload["turn_mode"] == "normal_evidence"
    assert payload["recovery_patch_mode_entered"] is False
    assert payload["selected_agents"] == []
    assert payload["finalize_blocked_by_phase"] is False


def test_apply_recovery_phase_protocol_routes_exhausted_recovery_to_support_recheck():
    from agent_system.inference.review_runner import _apply_recovery_phase_protocol

    payload = _apply_recovery_phase_protocol(
        manager_payload={
            "decision": "continue",
            "action_type": "summarize_progress",
            "effective_action_type": "summarize_progress",
            "policy_source": "recovery_target_exhausted_override",
            "target_claim_ids": [],
            "selected_agents": [],
        },
        state={
            "phase": "recovery",
            "phase_turn_index": 1,
            "claims": [
                {
                    "claim_id": "claim-main",
                    "claim": "The method improves benchmark performance.",
                    "status": "uncertain",
                    "claim_kind": "paper_extracted",
                },
                {
                    "claim_id": "claim-supported",
                    "claim": "The method uses a transformer encoder.",
                    "status": "supported",
                    "claim_kind": "paper_extracted",
                },
            ],
            "evidence_map": [
                {
                    "evidence_id": "e-supported",
                    "claim_id": "claim-supported",
                    "stance": "supports",
                    "strength": "strong",
                    "raw_quote": "The method uses a transformer encoder.",
                    "verified_grounding_label": "paper_grounded_exact",
                    "semantic_grounding_label": "semantic_support_verified",
                    "binding_status": "bound_real_claim",
                }
            ],
            "flaw_candidates": [],
            "conflict_notes": [{"conflict_id": "c1", "status": "open"}],
            "_latest_patch_log": {
                "recovery_attempted": True,
                "recovery_validated": False,
                "recovery_committed": False,
                "recovery_failure_code": "BLOCKED_BY_POLICY",
            },
        },
        mode="s4",
        worker_ids=["Claim Agent", "Evidence Agent", "Critique Agent"],
        worker_limit=2,
        recent_turn_logs=[
            {
                "turn_id": 4,
                "phase_after_action": "recovery",
                "recovery_patch_mode_entered": True,
                "action_type": "challenge_previous_hypothesis",
                "effective_action_type": "challenge_previous_hypothesis",
            }
        ],
    )

    assert payload["phase"] == "normal_review"
    assert payload["action_type"] == "request_evidence_recheck"
    assert payload["turn_mode"] == "normal_evidence"
    assert payload["recovery_patch_mode_entered"] is False
    assert payload["selected_agents"] == ["Evidence Agent"]
    assert payload["target_claim_ids"] == ["claim-main"]
    assert payload["policy_source"] == "recovery_target_exhausted_evidence_recheck_override"


def test_apply_recovery_phase_protocol_recheck_drops_context_targets_and_rehydrates_real_claims():
    from agent_system.inference.review_runner import _apply_recovery_phase_protocol

    payload = _apply_recovery_phase_protocol(
        manager_payload={
            "decision": "continue",
            "action_type": "request_evidence_recheck",
            "effective_action_type": "request_evidence_recheck",
            "policy_source": "evidence_progress_override",
            "target_claim_ids": ["claim-paper-context-1"],
            "selected_agents": ["Evidence Agent"],
        },
        state={
            "phase": "normal_review",
            "claims": [
                {"claim_id": "claim-paper-context-1", "status": "uncertain", "claim_origin_kind": "context_synthesized"},
                {"claim_id": "claim-main", "status": "supported"},
            ],
            "evidence_map": [{"evidence_id": "e1", "claim_id": "claim-main", "stance": "supports", "strength": "strong"}],
            "flaw_candidates": [],
            "conflict_notes": [{"conflict_id": "c1", "status": "open"}],
        },
        mode="s4",
        worker_ids=["Claim Agent", "Evidence Agent", "Critique Agent"],
        worker_limit=2,
        recent_turn_logs=[],
    )

    assert payload["action_type"] == "request_evidence_recheck"
    assert payload["target_claim_ids"] == ["claim-main"]
    assert "claim-paper-context-1" not in payload["target_claim_ids"]


def test_recovery_candidate_flaw_ids_keeps_actionable_verified_negative_flaw():
    from agent_system.inference.review_runner import _recovery_candidate_flaw_ids

    state = {
        "evidence_map": [
            {
                "evidence_id": "e-negative",
                "claim_id": "claim-main",
                "stance": "contradicts",
                "strength": "strong",
                "verified_grounding_label": "paper_grounded_exact",
                "semantic_grounding_label": "semantic_negative_verified",
                "negative_evidence_type": "direct_contradiction",
            }
        ],
        "flaw_candidates": [
            {
                "flaw_id": "flaw-actionable",
                "status": "candidate",
                "related_claim_ids": ["claim-main"],
                "negative_evidence_ids": ["e-negative"],
            }
        ],
    }

    assert _recovery_candidate_flaw_ids(state) == ["flaw-actionable"]


def test_recovery_candidate_flaw_ids_prefers_confirmed_actionable_flaw_for_safe_downgrade():
    from agent_system.inference.review_runner import _recovery_candidate_flaw_ids

    state = {
        "evidence_map": [
            {
                "evidence_id": "e-candidate-negative",
                "claim_id": "claim-main",
                "stance": "contradicts",
                "strength": "strong",
                "verified_grounding_label": "paper_grounded_exact",
                "semantic_grounding_label": "semantic_negative_verified",
                "negative_evidence_type": "negative_result",
            },
            {
                "evidence_id": "e-confirmed-negative",
                "claim_id": "claim-main",
                "stance": "contradicts",
                "strength": "strong",
                "verified_grounding_label": "paper_grounded_exact",
                "semantic_grounding_label": "semantic_negative_verified",
                "negative_evidence_type": "negative_result",
            },
        ],
        "flaw_candidates": [
            {
                "flaw_id": "flaw-candidate",
                "status": "candidate",
                "related_claim_ids": ["claim-main"],
                "negative_evidence_ids": ["e-candidate-negative"],
            },
            {
                "flaw_id": "flaw-confirmed",
                "status": "confirmed",
                "related_claim_ids": ["claim-main"],
                "negative_evidence_ids": ["e-confirmed-negative"],
            },
        ],
    }

    assert _recovery_candidate_flaw_ids(state) == ["flaw-confirmed", "flaw-candidate"]


def test_apply_recovery_phase_protocol_upgrades_recheck_when_verified_negative_flaw_ready():
    from agent_system.inference.review_runner import _apply_recovery_phase_protocol

    payload = _apply_recovery_phase_protocol(
        manager_payload={
            "decision": "continue",
            "action_type": "request_evidence_recheck",
            "effective_action_type": "request_evidence_recheck",
            "policy_source": "evidence_progress_override",
            "target_claim_ids": ["claim-main"],
            "selected_agents": ["Evidence Agent"],
        },
        state={
            "phase": "recovery",
            "phase_turn_index": 1,
            "claims": [{"claim_id": "claim-main", "status": "supported"}],
            "evidence_map": [
                {
                    "evidence_id": "e-negative",
                    "claim_id": "claim-main",
                    "stance": "contradicts",
                    "strength": "strong",
                    "verified_grounding_label": "paper_grounded_exact",
                    "semantic_grounding_label": "semantic_negative_verified",
                    "negative_evidence_type": "direct_contradiction",
                }
            ],
            "flaw_candidates": [
                {
                    "flaw_id": "flaw-actionable",
                    "status": "candidate",
                    "related_claim_ids": ["claim-main"],
                    "negative_evidence_ids": ["e-negative"],
                }
            ],
            "conflict_notes": [{"conflict_id": "c1", "status": "open"}],
        },
        mode="s4",
        worker_ids=["Claim Agent", "Evidence Agent", "Critique Agent"],
        worker_limit=2,
        recent_turn_logs=[],
    )

    assert payload["action_type"] == "challenge_previous_hypothesis"
    assert payload["turn_mode"] == "recovery_patch"
    assert payload["recovery_patch_mode_entered"] is True
    assert payload["policy_source"] == "recovery_recheck_to_patch_override"
    assert payload["target_flaw_ids"] == ["flaw-actionable"]
    assert payload["target_evidence_ids"] == ["e-negative"]
    assert any("verified negative flaw target" in note for note in payload.get("policy_notes", []))


def test_apply_recovery_phase_protocol_does_not_upgrade_recheck_without_patch_ready_target():
    from agent_system.inference.review_runner import _apply_recovery_phase_protocol

    payload = _apply_recovery_phase_protocol(
        manager_payload={
            "decision": "continue",
            "action_type": "request_evidence_recheck",
            "effective_action_type": "request_evidence_recheck",
            "policy_source": "evidence_progress_override",
            "target_claim_ids": ["claim-main"],
            "selected_agents": ["Evidence Agent"],
        },
        state={
            "phase": "recovery",
            "phase_turn_index": 1,
            "claims": [{"claim_id": "claim-main", "status": "supported"}],
            "evidence_map": [{"evidence_id": "e1", "claim_id": "claim-main", "stance": "supports", "strength": "strong"}],
            "flaw_candidates": [],
            "conflict_notes": [{"conflict_id": "c1", "status": "open"}],
        },
        mode="s4",
        worker_ids=["Claim Agent", "Evidence Agent", "Critique Agent"],
        worker_limit=2,
        recent_turn_logs=[
            {
                "turn_id": 4,
                "phase_after_action": "recovery",
                "turn_mode": "normal_evidence",
                "action_type": "request_evidence_recheck",
                "effective_action_type": "request_evidence_recheck",
            }
        ],
    )

    assert payload["action_type"] == "request_evidence_recheck"
    assert payload["turn_mode"] == "normal_evidence"
    assert payload["recovery_patch_mode_entered"] is False
    assert any("did not upgrade recheck to patch" in note for note in payload.get("policy_notes", []))


def test_apply_recovery_phase_protocol_cancels_context_claim_patch_even_with_real_evidence():
    from agent_system.inference.review_runner import _apply_recovery_phase_protocol

    payload = _apply_recovery_phase_protocol(
        manager_payload={
            "decision": "continue",
            "action_type": "challenge_previous_hypothesis",
            "effective_action_type": "challenge_previous_hypothesis",
            "policy_source": "evidence_progress_override",
            "target_claim_ids": ["claim-paper-context-1"],
            "selected_agents": ["Critique Agent", "Evidence Agent"],
        },
        state={
            "phase": "recovery",
            "phase_turn_index": 1,
            "claims": [
                {"claim_id": "claim-paper-context-1", "status": "supported", "claim_origin_kind": "context_synthesized"}
            ],
            "evidence_map": [
                {
                    "evidence_id": "e-context",
                    "claim_id": "claim-paper-context-1",
                    "stance": "supports",
                    "strength": "strong",
                    "source": "quote-bank",
                }
            ],
            "flaw_candidates": [],
            "conflict_notes": [{"conflict_id": "c1", "status": "open"}],
        },
        mode="s4",
        worker_ids=["Claim Agent", "Evidence Agent", "Critique Agent"],
        worker_limit=2,
        recent_turn_logs=[],
    )

    assert payload["action_type"] == "summarize_progress"
    assert payload["phase"] == "normal_review"
    assert payload["recovery_patch_mode_entered"] is False
    assert payload["target_claim_ids"] == []
    assert payload["policy_source"] == "recovery_target_exhausted_override"


def test_apply_recovery_phase_protocol_allows_terminal_entry_for_recovery_relevant_gap():
    from agent_system.inference.review_runner import _apply_recovery_phase_protocol

    payload = _apply_recovery_phase_protocol(
        manager_payload={
            "decision": "finalize",
            "action_type": "request_evidence_recheck",
            "effective_action_type": "request_evidence_recheck",
            "policy_source": "s4_recovery_relevant_override",
        },
        state={
            "phase": "normal_review",
            "phase_turn_index": 4,
            "claims": [{"claim_id": "claim-main", "status": "uncertain"}],
            "evidence_map": [{"evidence_id": "e1", "claim_id": "claim-main", "strength": "strong", "stance": "supports"}],
            "flaw_candidates": [],
            "conflict_notes": [],
            "evidence_gaps": ["Claim claim-main lacks complete grounded support."],
            "risk_profile": {"readiness": "needs_targeted_recheck", "open_question_count": 3, "conflict_count": 0},
        },
        mode="s4",
        worker_ids=["Claim Agent", "Evidence Agent", "Critique Agent"],
        worker_limit=2,
        recent_turn_logs=[],
    )

    assert payload["phase"] == "recovery"
    assert payload["action_type"] == "request_evidence_recheck"
    assert payload["turn_mode"] == "normal_evidence"
    assert payload["finalize_blocked_by_phase"] is True


def test_apply_recovery_phase_protocol_upgrades_completed_recheck_to_patch():
    from agent_system.inference.review_runner import _apply_recovery_phase_protocol

    payload = _apply_recovery_phase_protocol(
        manager_payload={
            "decision": "finalize",
            "action_type": "summarize_progress",
            "policy_source": "manager_model",
        },
        state={
            "phase": "recovery",
            "phase_turn_index": 1,
            "claims": [{"claim_id": "claim-main", "status": "supported"}],
            "evidence_map": [
                {
                    "evidence_id": "e1",
                    "claim_id": "claim-main",
                    "strength": "missing",
                    "stance": "missing",
                    "verified_grounding_label": "paper_grounded_exact",
                    "semantic_grounding_label": "semantic_negative_verified",
                }
            ],
            "flaw_candidates": [],
            "conflict_notes": [],
            "_latest_patch_log": {},
        },
        mode="s4",
        worker_ids=["Claim Agent", "Evidence Agent", "Critique Agent"],
        worker_limit=2,
        recent_turn_logs=[
            {
                "turn_id": 3,
                "phase_after_action": "recovery",
                "turn_mode": "normal_evidence",
                "recovery_patch_mode_entered": False,
                "recovery_committed": False,
                "recovery_failure_code": "",
                "action_type": "request_evidence_recheck",
                "effective_action_type": "request_evidence_recheck",
            }
        ],
    )

    assert payload["phase"] == "recovery"
    assert payload["action_type"] == "challenge_previous_hypothesis"
    assert payload["turn_mode"] == "recovery_patch"
    assert payload["policy_source"] == "recovery_recheck_to_patch_override"
    assert payload["selected_agents"] == ["Critique Agent", "Evidence Agent"]
    assert payload["target_claim_ids"] == ["claim-main"]
    assert payload["target_evidence_ids"] == ["e1"]


def test_build_turn_log_records_phase_fields_and_recovery_aliases():
    turn_log = build_turn_log(
        turn_id=4,
        manager_payload={
            "decision": "continue",
            "action_type": "challenge_previous_hypothesis",
            "effective_action_type": "challenge_previous_hypothesis",
            "policy_source": "recovery_phase_override",
            "phase_before_action": "recovery",
            "phase": "recovery",
            "phase_hold_reason": "Recovery phase held for another turn.",
            "phase_turn_index": 2,
            "finalize_blocked_by_phase": True,
            "selected_agents": ["Critique Agent"],
        },
        worker_payloads=[
            {
                "agent_id": "Critique Agent",
                "payload": {
                    "action": "apply_recovery_patch",
                    "target_type": "claim",
                    "target_id": "claim-main",
                    "old_status": "supported",
                    "new_status": "unsupported",
                    "supporting_evidence_ids": ["e1"],
                    "_recovery_patch_source": "system_salvaged",
                },
            }
        ],
        state={
            "claims": [{"claim_id": "claim-main", "status": "unsupported"}],
            "evidence_map": [],
            "flaw_candidates": [],
            "risk_profile": {},
            "revision_summary": [],
            "conflict_summary": [],
            "evidence_gaps": [],
            "unresolved_questions": [],
            "pending_user_question": "",
            "simulated_user_reply": "",
            "phase": "recovery",
            "phase_turn_index": 2,
            "_latest_patch_log": {
                "recovery_attempted": True,
                "recovery_validated": True,
                "recovery_committed": True,
                "recovery_failure_code": "SUCCESS",
                "recovery_target_id": "claim-main",
                "recovery_target_type": "claim",
                "old_status": "supported",
                "new_status": "unsupported",
                "recovery_target_gate_label": "real_target",
                "recovery_patch_operation": "downgrade_claim_to_unsupported",
                "recovery_target_commit_allowed": True,
                "recovery_patch_source": "system_salvaged",
            },
        },
        revision_events=[],
        conflict_events=[],
        previous_action_type="verify_evidence",
    )

    assert turn_log["phase_before_action"] == "recovery"
    assert turn_log["phase_after_action"] == "recovery"
    assert turn_log["phase_turn_index"] == 2
    assert turn_log["phase_hold_reason"] == "Recovery phase held for another turn."
    assert turn_log["finalize_blocked_by_phase"] is True
    assert turn_log["recovery_patch_source"] == "system_salvaged"
    assert turn_log["recovery_patch_emitted"] is True
    assert turn_log["recovery_patch_validated"] is True
    assert turn_log["recovery_patch_committed"] is True
    assert turn_log["recovery_target_gate_label"] == "real_target"
    assert turn_log["recovery_patch_operation"] == "downgrade_claim_to_unsupported"
    assert turn_log["recovery_target_commit_allowed"] is True


def test_claim_contradiction_strength_ignores_unrelated_conflict_note_evidence_ids():
    from agent_system.review_manager_policy import _claim_contradiction_strength

    score = _claim_contradiction_strength(
        {
            "evidence_map": [
                {"claim_id": "claim-main", "evidence_id": "e-main", "stance": "contradicts", "strength": "weak"},
                {"claim_id": "claim-alt", "evidence_id": "e-alt", "stance": "supports", "strength": "weak"},
            ],
            "conflict_notes": [
                {"claim_id": "claim-alt", "evidence_id": "e-alt", "note": "Unrelated alt-claim conflict."},
            ],
        },
        "claim-main",
        recent_turn_logs=[],
    )

    assert score == 1


def test_manager_policy_fallback_does_not_create_sticky_for_first_weak_recovery_target():
    payload = _apply_manager_policy_fallback(
        manager_payload={
            "decision": "continue",
            "action_type": "request_evidence_recheck",
            "target_claim_ids": ["claim-main"],
            "phase": "recovery",
            "policy_source": "manager_model",
        },
        state={
            "phase": "recovery",
            "sticky_target_id": "",
            "sticky_target_type": "",
            "sticky_target_active": False,
            "sticky_target_turns_remaining": 0,
            "claims": [
                {"claim_id": "claim-main", "status": "supported"},
            ],
            "evidence_map": [
                {"claim_id": "claim-main", "evidence_id": "e-main", "stance": "missing", "strength": "weak"},
            ],
            "flaw_candidates": [],
            "risk_profile": {},
            "conflict_notes": [],
            "evidence_gaps": [],
            "current_hypotheses": [],
            "unresolved_questions": [],
        },
        mode="s4",
        worker_ids=["Evidence Agent", "Critique Agent"],
        worker_limit=2,
        recent_turn_logs=[],
    )

    assert payload["target_claim_ids"] == ["claim-main"]
    assert payload["sticky_target_applied"] is False
    assert payload["sticky_target_id"] == ""


def test_manager_policy_fallback_does_not_create_sticky_for_singleton_challenge_target():
    payload = _apply_manager_policy_fallback(
        manager_payload={
            "decision": "continue",
            "action_type": "challenge_previous_hypothesis",
            "target_claim_ids": ["claim-main"],
            "phase": "recovery",
            "policy_source": "manager_model",
        },
        state={
            "phase": "recovery",
            "sticky_target_id": "",
            "sticky_target_type": "",
            "sticky_target_active": False,
            "sticky_target_turns_remaining": 0,
            "claims": [
                {"claim_id": "claim-main", "claim": "Main claim.", "status": "supported"},
            ],
            "evidence_map": [
                {"claim_id": "claim-main", "evidence_id": "e1", "stance": "contradicts", "strength": "strong"},
            ],
            "flaw_candidates": [],
            "risk_profile": {},
            "conflict_notes": [{"claim_id": "claim-main", "evidence_id": "e1", "note": "Conflict exists."}],
            "evidence_gaps": [],
            "current_hypotheses": [],
            "unresolved_questions": [],
        },
        mode="s4",
        worker_ids=["Evidence Agent", "Critique Agent"],
        worker_limit=2,
        recent_turn_logs=[
            {
                "action_type": "challenge_previous_hypothesis",
                "target_claim_ids": ["claim-main"],
                "recovery_failure_code": "BLOCKED_BY_POLICY",
            }
        ],
    )

    assert payload["target_claim_ids"] == ["claim-main"]
    assert payload["sticky_target_applied"] is False
    assert payload["sticky_target_id"] == ""


def test_manager_policy_fallback_does_not_create_sticky_on_request_evidence_recheck_even_after_blocked_same_claim():
    payload = _apply_manager_policy_fallback(
        manager_payload={
            "decision": "continue",
            "action_type": "request_evidence_recheck",
            "target_claim_ids": ["claim-main"],
            "phase": "recovery",
            "policy_source": "manager_model",
        },
        state={
            "phase": "recovery",
            "sticky_target_id": "",
            "sticky_target_type": "",
            "sticky_target_active": False,
            "sticky_target_turns_remaining": 0,
            "claims": [
                {"claim_id": "claim-main", "status": "supported", "claim": "The main contribution improves temporal consistency."},
            ],
            "evidence_map": [
                {"claim_id": "claim-main", "evidence_id": "e-main", "stance": "missing", "strength": "strong"},
            ],
            "flaw_candidates": [],
            "risk_profile": {},
            "conflict_notes": [],
            "evidence_gaps": [],
            "current_hypotheses": [],
            "unresolved_questions": [],
        },
        mode="s4",
        worker_ids=["Evidence Agent", "Critique Agent"],
        worker_limit=2,
        recent_turn_logs=[
            {
                "action_type": "request_evidence_recheck",
                "effective_action_type": "request_evidence_recheck",
                "target_claim_ids": ["claim-main"],
                "recovery_failure_code": "BLOCKED_BY_POLICY",
            }
        ],
    )

    assert payload["sticky_target_applied"] is False
    assert payload["sticky_target_id"] == ""
    assert payload["target_claim_ids"] == ["claim-main"]


def test_manager_policy_fallback_creates_sticky_on_multi_target_challenge_after_blocked_recovery_on_same_claim():
    payload = _apply_manager_policy_fallback(
        manager_payload={
            "decision": "continue",
            "action_type": "challenge_previous_hypothesis",
            "target_claim_ids": ["claim-alt", "claim-main"],
            "phase": "recovery",
            "policy_source": "manager_model",
        },
        state={
            "phase": "recovery",
            "sticky_target_id": "",
            "sticky_target_type": "",
            "sticky_target_active": False,
            "sticky_target_turns_remaining": 0,
            "claims": [
                {"claim_id": "claim-main", "status": "supported", "claim": "The main contribution improves temporal consistency."},
                {"claim_id": "claim-alt", "status": "supported", "claim": "An alternate claim."},
            ],
            "evidence_map": [
                {"claim_id": "claim-main", "evidence_id": "e-main", "stance": "contradicts", "strength": "strong"},
                {"claim_id": "claim-alt", "evidence_id": "e-alt", "stance": "supports", "strength": "weak"},
            ],
            "flaw_candidates": [],
            "risk_profile": {},
            "conflict_notes": [],
            "evidence_gaps": [],
            "current_hypotheses": [],
            "unresolved_questions": [],
        },
        mode="s4",
        worker_ids=["Evidence Agent", "Critique Agent"],
        worker_limit=2,
        recent_turn_logs=[
                {
                    "action_type": "request_evidence_recheck",
                    "effective_action_type": "request_evidence_recheck",
                    "target_claim_ids": ["claim-main"],
                    "recovery_failure_code": "BLOCKED_BY_POLICY",
            }
        ],
    )

    assert payload["sticky_target_applied"] is True
    assert payload["sticky_target_id"] == "claim-main"
    assert payload["target_claim_ids"] == ["claim-main"]


def test_manager_policy_fallback_does_not_create_sticky_for_fallback_claim_targets():
    payload = _apply_manager_policy_fallback(
        manager_payload={
            "decision": "continue",
            "action_type": "challenge_previous_hypothesis",
            "target_claim_ids": ["claim-fallback-1"],
            "phase": "recovery",
            "policy_source": "manager_model",
        },
        state={
            "phase": "recovery",
            "sticky_target_id": "",
            "sticky_target_type": "",
            "sticky_target_active": False,
            "sticky_target_turns_remaining": 0,
            "claims": [
                {"claim_id": "claim-fallback-1", "claim": "Do not output any text outside the JSON block.", "status": "supported"},
            ],
            "evidence_map": [
                {"claim_id": "claim-fallback-1", "evidence_id": "e-main", "stance": "contradicts", "strength": "strong"},
            ],
            "flaw_candidates": [],
            "risk_profile": {},
            "conflict_notes": [],
            "evidence_gaps": [],
            "current_hypotheses": [],
            "unresolved_questions": [],
        },
        mode="s4",
        worker_ids=["Evidence Agent", "Critique Agent"],
        worker_limit=2,
        recent_turn_logs=[
            {
                "action_type": "challenge_previous_hypothesis",
                "effective_action_type": "challenge_previous_hypothesis",
                "target_claim_ids": ["claim-fallback-1"],
            }
        ],
    )

    assert payload["sticky_target_applied"] is False
    assert payload["sticky_target_id"] == ""


def test_manager_policy_fallback_creates_sticky_for_unique_strongest_target_among_multi_claim_challenge():
    payload = _apply_manager_policy_fallback(
        manager_payload={
            "decision": "continue",
            "action_type": "challenge_previous_hypothesis",
            "target_claim_ids": ["claim-alt", "claim-main"],
            "phase": "recovery",
            "policy_source": "manager_model",
        },
        state={
            "phase": "recovery",
            "sticky_target_id": "",
            "sticky_target_type": "",
            "sticky_target_active": False,
            "sticky_target_turns_remaining": 0,
            "claims": [
                {"claim_id": "claim-main", "claim": "Main claim.", "status": "supported"},
                {"claim_id": "claim-alt", "claim": "Alt claim.", "status": "supported"},
            ],
            "evidence_map": [
                {"claim_id": "claim-main", "evidence_id": "e-main", "stance": "contradicts", "strength": "strong"},
                {"claim_id": "claim-alt", "evidence_id": "e-alt", "stance": "contradicts", "strength": "weak"},
            ],
            "flaw_candidates": [],
            "risk_profile": {},
            "conflict_notes": [],
            "evidence_gaps": [],
            "current_hypotheses": [],
            "unresolved_questions": [],
        },
        mode="s4",
        worker_ids=["Evidence Agent", "Critique Agent"],
        worker_limit=2,
        recent_turn_logs=[
            {
                "action_type": "challenge_previous_hypothesis",
                "effective_action_type": "challenge_previous_hypothesis",
                "target_claim_ids": ["claim-alt", "claim-main"],
            }
        ],
    )

    assert payload["sticky_target_applied"] is True
    assert payload["sticky_target_id"] == "claim-main"
    assert payload["target_claim_ids"] == ["claim-main", "claim-alt"]


def test_manager_policy_fallback_does_not_create_sticky_when_multi_claim_challenge_is_tied():
    payload = _apply_manager_policy_fallback(
        manager_payload={
            "decision": "continue",
            "action_type": "challenge_previous_hypothesis",
            "target_claim_ids": ["claim-main", "claim-alt"],
            "phase": "recovery",
            "policy_source": "manager_model",
        },
        state={
            "phase": "recovery",
            "sticky_target_id": "",
            "sticky_target_type": "",
            "sticky_target_active": False,
            "sticky_target_turns_remaining": 0,
            "claims": [
                {"claim_id": "claim-main", "claim": "Main claim.", "status": "supported"},
                {"claim_id": "claim-alt", "claim": "Alt claim.", "status": "supported"},
            ],
            "evidence_map": [
                {"claim_id": "claim-main", "evidence_id": "e-main", "stance": "contradicts", "strength": "strong"},
                {"claim_id": "claim-alt", "evidence_id": "e-alt", "stance": "contradicts", "strength": "strong"},
            ],
            "flaw_candidates": [],
            "risk_profile": {},
            "conflict_notes": [],
            "evidence_gaps": [],
            "current_hypotheses": [],
            "unresolved_questions": [],
        },
        mode="s4",
        worker_ids=["Evidence Agent", "Critique Agent"],
        worker_limit=2,
        recent_turn_logs=[
            {
                "action_type": "challenge_previous_hypothesis",
                "effective_action_type": "challenge_previous_hypothesis",
                "target_claim_ids": ["claim-main", "claim-alt"],
            }
        ],
    )

    assert payload["sticky_target_applied"] is False
    assert payload["sticky_target_id"] == ""
    assert payload["target_claim_ids"] == ["claim-main", "claim-alt"]


def test_manager_policy_fallback_applies_sticky_target_before_sanitize():
    payload = _apply_manager_policy_fallback(
        manager_payload={
            "decision": "continue",
            "action_type": "challenge_previous_hypothesis",
            "target_claim_ids": ["claim-alt", "claim-main"],
            "phase": "recovery",
            "policy_source": "manager_model",
        },
        state={
            "phase": "recovery",
            "sticky_target_id": "claim-main",
            "sticky_target_type": "claim",
            "sticky_target_active": True,
            "sticky_target_turns_remaining": 1,
            "claims": [
                {"claim_id": "claim-main", "claim": "Main claim.", "status": "supported"},
                {"claim_id": "claim-alt", "claim": "Alt claim.", "status": "supported"},
            ],
            "evidence_map": [
                {"claim_id": "claim-main", "stance": "contradicts", "strength": "weak"},
                {"claim_id": "claim-alt", "stance": "supports", "strength": "weak"},
            ],
            "flaw_candidates": [],
            "risk_profile": {},
            "conflict_notes": [],
            "evidence_gaps": [],
            "current_hypotheses": [],
            "unresolved_questions": [],
        },
        mode="s4",
        worker_ids=["Evidence Agent", "Critique Agent"],
        worker_limit=2,
        recent_turn_logs=[],
    )

    assert payload["target_claim_ids"] == ["claim-main"]
    assert payload["sticky_target_id"] == "claim-main"
    assert payload["sticky_target_reused"] is True
    assert payload["target_switch_blocked_by_sticky"] is True


def test_manager_policy_fallback_reuses_sticky_on_request_evidence_recheck():
    payload = _apply_manager_policy_fallback(
        manager_payload={
            "decision": "continue",
            "action_type": "request_evidence_recheck",
            "target_claim_ids": ["claim-alt", "claim-main"],
            "phase": "recovery",
            "policy_source": "manager_model",
        },
        state={
            "phase": "recovery",
            "sticky_target_id": "claim-main",
            "sticky_target_type": "claim",
            "sticky_target_active": True,
            "sticky_target_turns_remaining": 1,
            "claims": [
                {"claim_id": "claim-main", "claim": "Main claim.", "status": "supported"},
                {"claim_id": "claim-alt", "claim": "Alt claim.", "status": "supported"},
            ],
            "evidence_map": [
                {"claim_id": "claim-main", "stance": "contradicts", "strength": "weak"},
                {"claim_id": "claim-alt", "stance": "supports", "strength": "weak"},
            ],
            "flaw_candidates": [],
            "risk_profile": {},
            "conflict_notes": [],
            "evidence_gaps": [],
            "current_hypotheses": [],
            "unresolved_questions": [],
        },
        mode="s4",
        worker_ids=["Evidence Agent", "Critique Agent"],
        worker_limit=2,
        recent_turn_logs=[],
    )

    assert payload["target_claim_ids"] == ["claim-main", "claim-alt"]
    assert payload["sticky_target_id"] == "claim-main"
    assert payload["sticky_target_active"] is False
    assert payload["sticky_target_reused"] is True
    assert payload["sticky_target_turns_remaining"] == 0
    assert payload["target_switch_blocked_by_sticky"] is True


def test_manager_policy_fallback_keeps_current_targets_when_sticky_target_is_not_in_recheck_candidates():
    payload = _apply_manager_policy_fallback(
        manager_payload={
            "decision": "continue",
            "action_type": "request_evidence_recheck",
            "target_claim_ids": ["claim-alt"],
            "phase": "recovery",
            "policy_source": "manager_model",
        },
        state={
            "phase": "recovery",
            "sticky_target_id": "claim-main",
            "sticky_target_type": "claim",
            "sticky_target_active": True,
            "sticky_target_turns_remaining": 1,
            "claims": [
                {"claim_id": "claim-main", "claim": "Main claim.", "status": "supported"},
                {"claim_id": "claim-alt", "claim": "Alt claim.", "status": "supported"},
            ],
            "evidence_map": [
                {"claim_id": "claim-main", "stance": "contradicts", "strength": "weak"},
                {"claim_id": "claim-alt", "stance": "supports", "strength": "weak"},
            ],
            "flaw_candidates": [],
            "risk_profile": {},
            "conflict_notes": [],
            "evidence_gaps": [],
            "current_hypotheses": [],
            "unresolved_questions": [],
        },
        mode="s4",
        worker_ids=["Evidence Agent", "Critique Agent"],
        worker_limit=2,
        recent_turn_logs=[],
    )

    assert payload["target_claim_ids"] == ["claim-alt"]
    assert payload["sticky_target_id"] == "claim-main"
    assert payload["sticky_target_active"] is False
    assert payload["sticky_target_reused"] is False
    assert payload["sticky_target_turns_remaining"] == 0
    assert payload["target_switch_blocked_by_sticky"] is False


def test_manager_policy_fallback_does_not_count_singleton_recheck_as_sticky_reuse():
    payload = _apply_manager_policy_fallback(
        manager_payload={
            "decision": "continue",
            "action_type": "request_evidence_recheck",
            "target_claim_ids": ["claim-main"],
            "phase": "recovery",
            "policy_source": "manager_model",
        },
        state={
            "phase": "recovery",
            "sticky_target_id": "claim-main",
            "sticky_target_type": "claim",
            "sticky_target_active": True,
            "sticky_target_turns_remaining": 1,
            "claims": [
                {"claim_id": "claim-main", "claim": "Main claim.", "status": "supported"},
                {"claim_id": "claim-alt", "claim": "Alt claim.", "status": "supported"},
            ],
            "evidence_map": [
                {"claim_id": "claim-main", "stance": "contradicts", "strength": "weak"},
                {"claim_id": "claim-alt", "stance": "supports", "strength": "weak"},
            ],
            "flaw_candidates": [],
            "risk_profile": {},
            "conflict_notes": [],
            "evidence_gaps": [],
            "current_hypotheses": [],
            "unresolved_questions": [],
        },
        mode="s4",
        worker_ids=["Evidence Agent", "Critique Agent"],
        worker_limit=2,
        recent_turn_logs=[],
    )

    assert payload["target_claim_ids"] == ["claim-main"]
    assert payload["sticky_target_applied"] is False
    assert payload["sticky_target_reused"] is False
    assert payload["sticky_target_turns_remaining"] == 0
    assert payload["sticky_target_active"] is False
    assert payload["target_switch_blocked_by_sticky"] is False


def test_build_turn_log_splits_sticky_fields_between_state_and_payload():
    turn_log = build_turn_log(
        turn_id=3,
        manager_payload={
            "decision": "continue",
            "action_type": "challenge_previous_hypothesis",
            "effective_action_type": "challenge_previous_hypothesis",
            "phase_before_action": "recovery",
            "phase": "recovery",
            "phase_turn_index": 2,
            "sticky_target_id": "claim-main",
            "sticky_target_type": "claim",
            "sticky_target_active": True,
            "sticky_target_turns_remaining": 1,
            "sticky_release_reason": "",
            "sticky_target_applied": True,
            "sticky_target_reused": False,
            "sticky_target_released": False,
            "target_switch_blocked_by_sticky": True,
            "selected_agents": ["Critique Agent"],
        },
        worker_payloads=[],
        state={
            "claims": [{"claim_id": "claim-main", "status": "supported"}],
            "evidence_map": [],
            "flaw_candidates": [],
            "risk_profile": {},
            "revision_summary": [],
            "conflict_summary": [],
            "evidence_gaps": [],
            "unresolved_questions": [],
            "pending_user_question": "",
            "simulated_user_reply": "",
            "phase": "recovery",
            "phase_turn_index": 2,
            "sticky_target_id": "claim-main",
            "sticky_target_type": "claim",
            "sticky_target_active": True,
            "sticky_target_turns_remaining": 1,
            "sticky_release_reason": "",
            "sticky_target_applied": False,
            "sticky_target_reused": False,
            "sticky_target_released": False,
            "target_switch_blocked_by_sticky": False,
            "_latest_patch_log": {},
        },
        revision_events=[],
        conflict_events=[],
        previous_action_type="verify_evidence",
    )

    assert turn_log["sticky_target_id"] == "claim-main"
    assert turn_log["sticky_target_active"] is True
    assert turn_log["sticky_target_turns_remaining"] == 1
    assert turn_log["sticky_target_applied"] is True
    assert turn_log["sticky_target_reused"] is False
    assert turn_log["sticky_target_released"] is False
    assert turn_log["target_switch_blocked_by_sticky"] is True


def test_turn_level_recovery_salvage_requires_explicit_target_claim():
    worker_payloads = [
        {
            "agent_id": "Critique Agent",
            "payload": {
                "action": "blocked",
                "blocked_reason": "No valid downgrade/retraction is justifiable given current evidence.",
                "missing_requirements": [],
            },
        },
        {
            "agent_id": "Evidence Agent",
            "payload": {
                "evidence_map": [
                    {
                        "evidence_id": "evidence-1",
                        "claim_id": "claim-main",
                        "evidence": "Table 3 weakens the claim.",
                        "source": "Table 3",
                        "strength": "weak",
                        "stance": "contradicts",
                    }
                ]
            },
        },
    ]
    trace_item = {"worker_calls": []}
    _maybe_salvage_turn_level_recovery_patch(
        worker_payloads,
        state={"claims": [{"claim_id": "claim-main", "status": "uncertain"}]},
        manager_payload={
            "action_type": "challenge_previous_hypothesis",
            "effective_action_type": "challenge_previous_hypothesis",
            "target_claim_ids": [],
        },
        trace_item=trace_item,
    )

    assert worker_payloads[0]["payload"]["action"] == "blocked"
    assert trace_item["worker_calls"] == []


def test_fallback_critique_returns_recovery_patch_during_challenge():
    """During challenge_previous_hypothesis, the critique fallback should emit
    a structured recovery patch instead of polluting the state with flaw text."""
    state = {
        "claims": [{"claim_id": "claim-main", "status": "partially_supported", "supporting_evidence_ids": []}],
        "evidence_map": [{"evidence_id": "evidence-1", "claim_id": "claim-main", "stance": "contradicts", "verified_grounding_label": "paper_grounded_exact", "semantic_grounding_label": "semantic_negative_verified"}],
        "flaw_candidates": [
            {"flaw_id": "flaw-existing", "status": "candidate", "severity": "major",
             "related_claim_ids": ["claim-main"], "evidence_ids": ["evidence-1"]}
        ],
    }
    payload = _fallback_worker_payload(
        agent_id="Critique Agent",
        raw_text="The earlier claim now looks unsupported after the contradiction.",
        state=state,
        manager_payload={
            "action_type": "challenge_previous_hypothesis",
            "effective_action_type": "challenge_previous_hypothesis",
            "target_claim_ids": ["claim-main"],
            "target_flaw_ids": [],
            "target_evidence_ids": ["evidence-1"],
        },
    )

    assert payload["action"] == "apply_recovery_patch"
    assert payload["target_type"] == "claim"
    assert payload["target_id"] == "claim-main"
    assert payload["old_status"] == "partially_supported"
    assert payload["new_status"] == "unsupported"
    assert payload["supporting_evidence_ids"] == ["evidence-1"]


# ────────────────────────────────────────────────────────────────
# P2.1 Recovery Tests
# ────────────────────────────────────────────────────────────────


def test_recovery_test_a_conflict_blocks_summarize_finalize():
    """Test A: When conflicts exist and target flaws are still active/confirmed,
    the manager must NOT directly summarize or finalize — it must trigger recovery."""
    state = {
        "claims": [{"claim_id": "claim-main", "status": "uncertain"}],
        "evidence_map": [{"evidence_id": "evidence-1", "claim_id": "claim-main", "strength": "weak", "stance": "contradicts"}],
        "flaw_candidates": [{"flaw_id": "flaw-main", "status": "confirmed", "evidence_ids": []}],
        "unresolved_questions": [{"question": "Is the flaw still valid?", "status": "open"}],
        "risk_profile": {"open_question_count": 1, "conflict_count": 2, "readiness": "not_ready"},
        "evidence_gaps": ["Flaw flaw-main lacks anchored evidence."],
        "conflict_notes": [
            {"conflict_id": "c1", "note": "Evidence contradicts claim.", "claim_id": "claim-main", "evidence_id": "evidence-1", "flaw_id": "flaw-main", "conflict_type": "evidence_conflict"},
            {"conflict_id": "c2", "note": "Flaw flaw-main lacks anchored evidence.", "claim_id": "", "evidence_id": "", "flaw_id": "flaw-main", "conflict_type": "flaw_anchor_gap"},
        ],
        "current_hypotheses": [],
        "clarification_needed": False,
        "pending_user_question": "",
    }

    # Try summarize_progress — should be redirected to recovery
    payload_summarize = {
        "decision": "continue",
        "action_type": "summarize_progress",
        "selected_agents": [],
        "focus": "wrap up",
        "rationale": "Summarize current state.",
    }
    result_summarize = _apply_manager_policy_fallback(
        manager_payload=payload_summarize,
        state=state,
        mode="s4",
        worker_ids=["Claim Agent", "Evidence Agent", "Critique Agent"],
        worker_limit=2,
        recent_turn_logs=[],
    )
    assert result_summarize["action_type"] in {"challenge_previous_hypothesis", "request_evidence_recheck"}
    # Any override that redirects to a recovery action is acceptable
    assert result_summarize["policy_source"] != "manager_model", \
        f"Expected a policy override, got {result_summarize['policy_source']}"

    # Try finalize — should also be redirected
    payload_finalize = {
        "decision": "continue",
        "action_type": "finalize",
        "selected_agents": [],
        "focus": "wrap up",
        "rationale": "Finalize now.",
    }
    result_finalize = _apply_manager_policy_fallback(
        manager_payload=payload_finalize,
        state=state,
        mode="s4",
        worker_ids=["Claim Agent", "Evidence Agent", "Critique Agent"],
        worker_limit=2,
        recent_turn_logs=[],
    )
    assert result_finalize["action_type"] in {"challenge_previous_hypothesis", "request_evidence_recheck"}


def test_auto_finalize_blocks_unverified_flaw_lifecycle_before_final_report():
    from agent_system.review_manager_policy import apply_finalize_policy

    state = {
        "claims": [
            {"claim_id": "claim-main", "claim": "The method improves robustness.", "status": "supported"},
            {"claim_id": "claim-method", "claim": "The method is technically sound.", "status": "partially_supported"},
        ],
        "evidence_map": [
            {"evidence_id": "evidence-1", "claim_id": "claim-main", "strength": "strong", "stance": "supports", "binding_status": "bound_real_claim"},
        ],
        "flaw_candidates": [{"flaw_id": "flaw-unverified", "status": "candidate", "severity": "major"}],
        "unresolved_questions": [{"question": "Does the candidate flaw have verified negative evidence?", "status": "open"}],
        "risk_profile": {"open_question_count": 1, "conflict_count": 0, "readiness": "ready_to_finalize"},
        "evidence_gaps": [],
        "conflict_notes": [],
        "current_hypotheses": [],
    }
    payload = {
        "decision": "continue",
        "action_type": "verify_evidence",
        "effective_action_type": "verify_evidence",
        "selected_agents": ["Evidence Agent"],
        "focus": "Continue evidence work.",
        "rationale": "Evidence was checked.",
        "target_claim_ids": ["claim-main"],
        "final_decision": "undecided",
        "final_report": "",
    }

    result, selected = apply_finalize_policy(
        manager_payload=payload,
        state=state,
        mode="s4",
        step=4,
        turn_cap=8,
        worker_ids=["Claim Agent", "Evidence Agent", "Critique Agent"],
        worker_limit=2,
        selected_workers=["Evidence Agent"],
        worker_payloads=[],
        recent_turn_logs=[
            {"action_type": "extract_claims"},
            {"action_type": "verify_evidence"},
            {"action_type": "analyze_flaws"},
        ],
    )

    assert result["decision"] == "continue"
    assert result["action_type"] == "request_evidence_recheck"
    assert result["policy_source"] == "negative_evidence_formation_override"
    assert result["negative_evidence_formation_required"] is True
    assert result["target_flaw_ids"] == ["flaw-unverified"]
    assert result["final_decision"] == "undecided"
    assert result["final_report"] == ""
    assert selected[0] == "Evidence Agent"


def test_negative_evidence_formation_falls_back_to_real_claim_targets():
    state = {
        "claims": [
            {"claim_id": "claim-context-1", "claim": "Context helper claim", "status": "supported"},
            {"claim_id": "claim-main", "claim": "The method improves robustness.", "status": "supported"},
        ],
        "evidence_map": [],
        "flaw_candidates": [
            {
                "flaw_id": "flaw-no-target",
                "status": "candidate",
                "severity": "major",
                "description": "The robustness claim may be overstated.",
                "related_claim_ids": [],
                "evidence_ids": [],
                "negative_evidence_ids": [],
            }
        ],
        "risk_profile": {"readiness": "ready_to_finalize"},
        "evidence_gaps": [],
        "conflict_notes": [],
        "current_hypotheses": [],
    }
    payload = _apply_manager_policy_fallback(
        {"action_type": "finalize", "decision": "finalize", "policy_source": "manager_model"},
        state,
        "s4",
        ["Evidence Agent", "Critique Agent"],
        2,
        [],
    )

    assert payload["policy_source"] == "negative_evidence_formation_override"
    assert payload["action_type"] == "request_evidence_recheck"
    assert payload["negative_evidence_formation_required"] is True
    assert payload["target_flaw_ids"] == ["flaw-no-target"]
    assert payload["target_claim_ids"] == ["claim-main"]


def test_recovery_test_b_confirmed_flaw_downgraded_via_missing_anchor():
    """Test B: When a flaw is confirmed but has no evidence_ids, the
    missing_anchor_evidence consistency check should transition it to candidate,
    and _classify_revision_events should count this as a downgrade."""
    from agent_system.environments.env_package.review.state import _classify_revision_events

    # Simulate the revision event produced by the missing_anchor_evidence logic
    revision_events = [
        {
            "event_id": "revision-flaw-flaw-1-status-1",
            "entity_type": "flaw",
            "entity_id": "flaw-1",
            "field": "status",
            "before": "confirmed",
            "after": "candidate",
            "reason": "missing_anchor_evidence",
        }
    ]

    result = _classify_revision_events(revision_events)

    # The confirmed→candidate transition MUST be classified as a downgrade
    assert "flaw:flaw-1" in result["downgraded_items"], \
        f"Expected flaw:flaw-1 in downgraded_items, got {result['downgraded_items']}"
    assert "missing_anchor_evidence" in result["revision_reasons"]


def test_recovery_test_c_claim_supported_to_unsupported_is_downgrade():
    """Test C: When a claim transitions from supported → unsupported
    (e.g., due to contradicting evidence), _classify_revision_events
    should classify this as a downgrade."""
    from agent_system.environments.env_package.review.state import _classify_revision_events

    # Claim status revision event
    revision_events = [
        {
            "event_id": "revision-claim-claim-1-status-1",
            "entity_type": "claim",
            "entity_id": "claim-1",
            "field": "status",
            "before": "supported",
            "after": "unsupported",
            "reason": "incoming_status_update",
        }
    ]

    result = _classify_revision_events(revision_events)

    assert "claim:claim-1" in result["downgraded_items"], \
        f"Expected claim:claim-1 in downgraded_items, got {result['downgraded_items']}"

    # Also test supported → uncertain
    revision_events_uncertain = [
        {
            "event_id": "revision-claim-claim-2-status-1",
            "entity_type": "claim",
            "entity_id": "claim-2",
            "field": "status",
            "before": "supported",
            "after": "uncertain",
            "reason": "consistency_reconciliation",
        }
    ]

    result2 = _classify_revision_events(revision_events_uncertain)
    assert "claim:claim-2" in result2["downgraded_items"]

    # Also test superseded = retraction
    revision_events_superseded = [
        {
            "event_id": "revision-claim-claim-3-status-1",
            "entity_type": "claim",
            "entity_id": "claim-3",
            "field": "status",
            "before": "supported",
            "after": "superseded",
            "reason": "incoming_status_update",
        }
    ]

    result3 = _classify_revision_events(revision_events_superseded)
    assert "claim:claim-3" in result3["retracted_items"]



    worker_payload = {
        "evidence_map": [
            {
                "evidence_id": "e1",
                "claim_id": "claim-1",
                "evidence": "Table 2 remains weak.",
                "source": "Table 2",
                "strength": "weak",
                "stance": "contradicts",
            }
        ],
        "dialogue_summary": "Still checking evidence.",
    }
    coerced = _enforce_recovery_patch_mode_payload(
        "Evidence Agent",
        worker_payload,
        raw_text='<json>{"evidence_map":[{"evidence_id":"e1"}]}</json>',
        manager_payload={
            "action_type": "request_evidence_recheck",
            "effective_action_type": "request_evidence_recheck",
            "turn_mode": "recovery_patch",
            "selected_agents": ["Evidence Agent"],
        },
    )

    assert coerced["action"] == ""
    assert coerced["evidence_map"] == []
    assert coerced["_emission_failure_code"] == "WORKER_STAYED_IN_EVIDENCE_MODE"
    assert "Evidence Agent" in coerced["_emission_failure_message"]


def test_build_prompt_keeps_recheck_turn_in_normal_evidence_mode():
    from agent_system.inference.review_runner import build_prompt, build_worker_observation

    task = {
        "paper_id": "paper-p24-3",
        "paper_text": "The paper reports weak evidence for its main claim.",
        "user_goal": "Recheck whether the main claim is still supportable.",
        "mode": "s4",
        "max_turns": 5,
        "review_state": {
            "turn_id": 2,
            "mode": "s4",
            "dialogue_summary": "Need a corrective update.",
            "claims": [{"claim_id": "claim-main", "claim": "Main claim", "status": "supported"}],
            "evidence_map": [{"evidence_id": "e1", "claim_id": "claim-main", "evidence": "Weak table.", "source": "Table 2", "strength": "weak", "stance": "contradicts"}],
            "flaw_candidates": [],
            "unresolved_questions": [],
            "conflict_notes": [],
            "revision_log": [],
            "evidence_gaps": [],
            "active_focus": "Re-evaluate the weak evidence.",
            "current_hypotheses": [],
            "revision_summary": [],
            "conflict_summary": [],
            "risk_profile": {},
            "pending_user_question": "",
            "simulated_user_reply": "",
            "clarification_needed": False,
            "last_focus": "Re-evaluate the weak evidence.",
        },
        "turn_logs": [],
    }
    manager_payload = {
        "action_type": "request_evidence_recheck",
        "effective_action_type": "request_evidence_recheck",
        "selected_agents": ["Evidence Agent"],
        "focus": "Recheck the weak evidence for the main claim.",
        "rationale": "The turn should gather structured evidence before any corrective patch.",
        "target_claim_ids": ["claim-main"],
        "target_evidence_ids": ["e1"],
        "target_flaw_ids": [],
        "target_hypotheses": [],
    }

    worker_obs = build_worker_observation(task, manager_payload, "Evidence Agent")
    prompt = build_prompt("Evidence Agent", worker_obs, "", 3, manager_payload=manager_payload)

    assert "Turn Mode: normal_evidence" in worker_obs
    assert "Patch Mode Requirement: inactive" in worker_obs
    assert "You are operating in recovery patch mode" not in prompt


def test_build_prompt_switches_challenge_turn_into_recovery_patch_mode():
    from agent_system.inference.review_runner import build_prompt, build_worker_observation

    task = {
        "paper_id": "paper-p24-3",
        "paper_text": "The paper reports weak evidence for its main claim.",
        "user_goal": "Challenge whether the main claim is still supportable.",
        "mode": "s4",
        "max_turns": 5,
        "review_state": {
            "turn_id": 2,
            "mode": "s4",
            "dialogue_summary": "Need a corrective update.",
            "claims": [{"claim_id": "claim-main", "claim": "Main claim", "status": "supported"}],
            "evidence_map": [{"evidence_id": "e1", "claim_id": "claim-main", "evidence": "Weak table.", "source": "Table 2", "strength": "weak", "stance": "contradicts"}],
            "flaw_candidates": [],
            "unresolved_questions": [],
            "conflict_notes": [],
            "revision_log": [],
            "evidence_gaps": [],
            "active_focus": "Challenge the weak evidence.",
            "current_hypotheses": [],
            "revision_summary": [],
            "conflict_summary": [],
            "risk_profile": {},
            "pending_user_question": "",
            "simulated_user_reply": "",
            "clarification_needed": False,
            "last_focus": "Challenge the weak evidence.",
        },
        "turn_logs": [],
    }
    manager_payload = {
        "action_type": "challenge_previous_hypothesis",
        "effective_action_type": "challenge_previous_hypothesis",
        "selected_agents": ["Critique Agent"],
        "focus": "Convert this challenge into a corrective patch.",
        "rationale": "The turn should repair or block, not restate evidence.",
        "target_claim_ids": ["claim-main"],
        "target_evidence_ids": ["e1"],
        "target_flaw_ids": [],
        "target_hypotheses": [],
    }

    worker_obs = build_worker_observation(task, manager_payload, "Critique Agent")
    prompt = build_prompt("Critique Agent", worker_obs, "", 3, manager_payload=manager_payload)

    assert "Turn Mode: recovery_patch" in worker_obs
    assert "Patch Mode Requirement" in worker_obs
    assert "You are operating in recovery patch mode" in prompt
    assert "apply_recovery_patch" in prompt



def test_evidence_worker_observation_exposes_negative_evidence_formation_mode():
    task = {
        "paper_id": "paper-negative-formation-observation",
        "mode": "s4",
        "paper_text": "--- BEGIN PAPER ---\nThe experiment fails to improve the baseline in Table 2.\n--- END PAPER ---",
        "data_source": "unit-test",
        "max_turns": 4,
        "user_goal": "Audit negative evidence formation.",
        "review_state": {
            "turn_id": 1,
            "claims": [{"claim_id": "claim-1", "claim": "The method improves the baseline.", "status": "supported"}],
            "evidence_map": [],
            "flaw_candidates": [
                {
                    "flaw_id": "flaw-1",
                    "status": "candidate",
                    "severity": "major",
                    "description": "The improvement claim may be contradicted by Table 2.",
                    "related_claim_ids": ["claim-1"],
                }
            ],
        },
    }
    manager_payload = {
        "action_type": "request_evidence_recheck",
        "policy_source": "negative_evidence_formation_override",
        "target_flaw_ids": ["flaw-1"],
        "target_claim_ids": ["claim-1"],
    }

    observation = build_worker_observation(task, manager_payload, "Evidence Agent")

    assert "Negative Evidence Formation Mode" in observation
    assert "negative_evidence_formation_required=true" in observation
    assert "Target Flaws" in observation
    assert "flaw-1" in observation

def test_recovery_negative_evidence_requires_semantic_verified_label():
    base = {
        "evidence_id": "e-neg-1",
        "claim_id": "claim-1",
        "stance": "contradicts",
        "strength": "strong",
        "verified_grounding_label": "paper_grounded_exact",
    }
    assert _is_verified_negative_evidence_for_recovery({**base, "semantic_grounding_label": "semantic_negative_verified"}) is True
    assert _is_verified_negative_evidence_for_recovery({**base, "semantic_grounding_label": "semantic_support_verified"}) is True
    assert _is_verified_negative_evidence_for_recovery({**base, "semantic_grounding_label": "semantic_unjudged"}) is False
    assert _is_verified_negative_evidence_for_recovery({**base, "semantic_grounding_label": "semantic_mismatch"}) is False
    assert _is_verified_negative_evidence_for_recovery({**base, "semantic_grounding_label": "semantic_weak"}) is False


def test_unverified_flaw_routes_to_negative_evidence_formation_before_recovery_patch():
    state = {
        "claims": [
            {"claim_id": "claim-1", "claim": "The method improves robustness.", "status": "supported"},
        ],
        "evidence_map": [
            {
                "evidence_id": "e-pos-1",
                "claim_id": "claim-1",
                "evidence": "The method improves robustness in experiments.",
                "stance": "supports",
                "strength": "strong",
                "verified_grounding_label": "paper_grounded_exact",
                "semantic_grounding_label": "semantic_support_verified",
                "binding_status": "bound_real_claim",
            }
        ],
        "flaw_candidates": [
            {
                "flaw_id": "flaw-1",
                "title": "Robustness concern",
                "description": "The robustness claim may be overstated.",
                "status": "candidate",
                "severity": "major",
                "related_claim_ids": ["claim-1"],
                "evidence_ids": ["e-pos-1"],
                "negative_evidence_ids": [],
            }
        ],
        "risk_profile": {"readiness": "needs_targeted_recheck"},
    }
    payload = _apply_manager_policy_fallback(
        {"action_type": "finalize", "decision": "finalize", "policy_source": "manager_model"},
        state,
        "s4",
        ["Evidence Agent", "Critique Agent"],
        2,
        [],
    )
    assert payload["action_type"] == "request_evidence_recheck"
    assert payload["policy_source"] == "negative_evidence_formation_override"
    assert payload["negative_evidence_formation_required"] is True
    assert payload["target_flaw_ids"] == ["flaw-1"]
    assert payload["target_claim_ids"] == ["claim-1"]


def test_negative_evidence_formation_does_not_loop_after_recent_retry():
    state = {
        "claims": [{"claim_id": "claim-1", "claim": "The method improves robustness.", "status": "supported"}],
        "evidence_map": [{"evidence_id": "e-pos-1", "claim_id": "claim-1", "stance": "supports", "strength": "strong"}],
        "flaw_candidates": [
            {
                "flaw_id": "flaw-1",
                "status": "candidate",
                "severity": "major",
                "related_claim_ids": ["claim-1"],
                "evidence_ids": ["e-pos-1"],
                "negative_evidence_ids": [],
            }
        ],
        "risk_profile": {"readiness": "needs_targeted_recheck"},
    }
    recent_turn_logs = [
        {
            "policy_source": "negative_evidence_formation_override",
            "action_type": "request_evidence_recheck",
            "target_flaw_ids": ["flaw-1"],
            "target_claim_ids": ["claim-1"],
        }
    ]
    payload = _apply_manager_policy_fallback(
        {"action_type": "finalize", "decision": "finalize", "policy_source": "manager_model"},
        state,
        "s4",
        ["Evidence Agent", "Critique Agent"],
        2,
        recent_turn_logs,
    )
    assert payload.get("negative_evidence_formation_required") is not True
    assert payload["policy_source"] != "negative_evidence_formation_override"



def test_negative_evidence_formation_payload_filters_positive_support():
    payload = normalize_review_update_payload({
        "evidence_map": [
            {
                "evidence_id": "evidence-positive",
                "claim_id": "claim-1",
                "evidence": "The abstract supports the claim.",
                "source": "Abstract",
                "stance": "supports",
                "strength": "strong",
            },
            {
                "evidence_id": "evidence-negative",
                "claim_id": "claim-1",
                "evidence": "The paper says the baseline comparison is missing.",
                "source": "Limitations",
                "stance": "missing",
                "strength": "missing",
            },
        ],
        "dialogue_summary": "mixed",
        "recommendation": "undecided",
    })

    filtered = _enforce_negative_evidence_formation_payload(
        "Evidence Agent",
        payload,
        {"policy_source": "negative_evidence_formation_override"},
    )

    assert [item["evidence_id"] for item in filtered["evidence_map"]] == ["evidence-negative"]
    assert filtered["unresolved_questions"]
    last_question = filtered["unresolved_questions"][-1]
    if isinstance(last_question, dict):
        last_question = last_question.get("question", "")
    # P0-4: paper-side, reviewer-neutral phrasing (no system-process language).
    assert "verified paper-negative evidence" in last_question
    forbidden = (
        "positive/support evidence",
        "filtered",
        "salvage",
        "hard-negative",
        "system",
    )
    for term in forbidden:
        assert term not in last_question.lower()


def test_negative_evidence_formation_salvages_negative_quote_bank_when_model_returns_positive_only():
    state = {
        "claims": [
            {
                "claim_id": "claim-1",
                "claim": "The method is empirically validated against strong baselines.",
                "status": "uncertain",
            }
        ],
        "evidence_quote_bank": [
            {
                "quote_id": "quote-negative-or-gap-1",
                "source_bucket": "negative_or_gap",
                "source_locator": "Limitations excerpt #1",
                "raw_quote": "The method does not compare against retrieval-heavy baselines and lacks an ablation study.",
                "source_span_start": 10,
                "source_span_end": 94,
            }
        ],
        "evidence_map": [],
        "flaw_candidates": [],
    }
    payload = normalize_review_update_payload({
        "evidence_map": [
            {
                "evidence_id": "e-positive",
                "claim_id": "claim-1",
                "evidence": "The abstract reports improvements.",
                "source": "Abstract",
                "stance": "supports",
                "strength": "strong",
            }
        ],
        "dialogue_summary": "positive only",
        "recommendation": "undecided",
    })

    filtered = _enforce_negative_evidence_formation_payload(
        "Evidence Agent",
        payload,
        {
            "policy_source": "hard_negative_discovery_override",
            "target_claim_ids": ["claim-1"],
            "target_flaw_ids": ["flaw-1"],
            "negative_evidence_formation_required": True,
        },
        state,
    )

    assert len(filtered["evidence_map"]) == 1
    salvaged = filtered["evidence_map"][0]
    assert salvaged["quote_id"] == "quote-negative-or-gap-1"
    assert salvaged["source"] == "quote-bank-negative-grounding"
    assert salvaged["stance"] == "missing"
    assert salvaged["claim_id"] == "claim-1"
    assert salvaged["negative_evidence_type"] == "missing_ablation"
    assert salvaged["negative_evidence_actionability"] == "actionable_candidate"
    assert salvaged["claim_status_downgrade_allowed"] is False
    assert filtered["flaw_candidates"][0]["flaw_id"] == "flaw-1"
    assert filtered["flaw_candidates"][0]["negative_evidence_type"] == "missing_ablation"
    assert filtered["flaw_candidates"][0]["severity"] == "major"
    assert salvaged["evidence_id"] in filtered["flaw_candidates"][0]["negative_evidence_ids"]

    merged = merge_review_state({**state, "flaw_candidates": [{"flaw_id": "flaw-1", "flaw": "Baseline comparison may be missing.", "status": "candidate"}]}, filtered)
    evidence = merged["evidence_map"][0]
    assert evidence["verified_grounding_label"] == "paper_grounded_exact"
    assert evidence["semantic_grounding_label"] == "semantic_negative_verified"
    flaw = next(item for item in merged["flaw_candidates"] if item["flaw_id"] == "flaw-1")
    assert evidence["evidence_id"] in flaw.get("negative_evidence_ids", [])


def test_negative_quote_bank_salvage_allows_claim_downgrade_for_negative_result_only():
    state = {
        "claims": [
            {
                "claim_id": "claim-1",
                "claim": "The method improves under heterogeneous federated settings.",
                "status": "supported",
            }
        ],
        "evidence_quote_bank": [
            {
                "quote_id": "quote-negative-result",
                "source_bucket": "negative_or_gap",
                "source_locator": "Figure 4 discussion",
                "raw_quote": "Worse yet, accuracy declines under heterogeneous client data.",
                "negative_evidence_type": "negative_result",
            }
        ],
    }

    salvaged = _negative_quote_bank_salvage_payload(
        state,
        {"target_claim_ids": ["claim-1"], "target_flaw_ids": []},
        0,
    )

    assert salvaged is not None
    assert salvaged["negative_evidence_type"] == "negative_result"
    assert salvaged["negative_evidence_actionability"] == "actionable_candidate"
    assert salvaged["verified_source_bucket"] == "negative_or_gap"
    assert salvaged["claim_status_downgrade_allowed"] is True


def test_negative_quote_bank_salvage_promotes_scope_limitation_for_broad_claim():
    state = {
        "claims": [
            {
                "claim_id": "claim-1",
                "claim": "The model generalizes to unseen knowledge graphs in zero-shot settings.",
                "status": "supported",
            }
        ],
        "evidence_quote_bank": [
            {
                "quote_id": "quote-future-work",
                "source_bucket": "negative_or_gap",
                "source_locator": "Limitations excerpt",
                "raw_quote": "Additional interaction types are left for future work.",
                "negative_evidence_type": "scope_limitation",
            }
        ],
    }

    salvaged = _negative_quote_bank_salvage_payload(
        state,
        {"target_claim_ids": ["claim-1"], "target_flaw_ids": ["flaw-scope"]},
        0,
    )

    assert salvaged is not None
    assert salvaged["negative_evidence_type"] == "scope_overclaim"
    assert salvaged["negative_evidence_actionability"] == "actionable_candidate"
    assert salvaged["claim_status_downgrade_allowed"] is False

    merged = merge_review_state(state, {"evidence_map": [salvaged]})
    assert merged["evidence_map"][0]["negative_evidence_type"] == "scope_overclaim"


def test_negative_quote_bank_salvage_prefers_concrete_scope_limit_for_broad_capability_claim():
    state = {
        "claims": [
            {
                "claim_id": "claim-1",
                "claim": "The method defies multi-model forgetting in one-shot NAS.",
                "status": "supported",
            }
        ],
        "evidence_quote_bank": [
            {
                "quote_id": "quote-section-header",
                "source_bucket": "negative_or_gap",
                "source_locator": "Conclusion and future work",
                "raw_quote": "The goal of this work is to train a supernet in an effective way to overcome multi-model forgetting.",
                "negative_evidence_type": "scope_limitation",
            },
            {
                "quote_id": "quote-concrete-future-work",
                "source_bucket": "negative_or_gap",
                "source_locator": "Conclusion and future work",
                "raw_quote": "In future work, a more effective way to store all gradient vectors can be explored to improve the supernet predictive ability.",
                "negative_evidence_type": "scope_limitation",
            },
        ],
    }

    salvaged = _negative_quote_bank_salvage_payload(
        state,
        {"target_claim_ids": ["claim-1"], "target_flaw_ids": ["flaw-scope"]},
        0,
    )

    assert salvaged is not None
    assert salvaged["quote_id"] == "quote-concrete-future-work"
    assert salvaged["negative_evidence_type"] == "scope_overclaim"
    assert salvaged["negative_evidence_actionability"] == "actionable_candidate"


def test_negative_evidence_formation_adds_quote_bank_when_negative_item_lacks_negative_anchor():
    state = {
        "claims": [{"claim_id": "claim-1", "claim": "The method is validated against baselines."}],
        "evidence_quote_bank": [
            {
                "quote_id": "quote-negative-or-gap-1",
                "source_bucket": "negative_or_gap",
                "source_locator": "Limitations excerpt #1",
                "raw_quote": "The method does not compare against retrieval-heavy baselines and lacks an ablation study.",
                "source_span_start": 3,
                "source_span_end": 87,
            }
        ],
        "evidence_map": [],
        "flaw_candidates": [],
    }
    payload = normalize_review_update_payload({
        "evidence_map": [
            {
                "evidence_id": "e-generic-negative",
                "claim_id": "claim-1",
                "evidence": "No significant accuracy difference found between methods.",
                "source": "experiment",
                "raw_quote": "In our experiments, we aim to answer research questions.",
                "quote_id": "quote-results-1",
                "stance": "missing",
                "strength": "strong",
            }
        ],
    })

    filtered = _enforce_negative_evidence_formation_payload(
        "Evidence Agent",
        payload,
        {"policy_source": "hard_negative_discovery_override", "target_claim_ids": ["claim-1"]},
        state,
    )

    assert len(filtered["evidence_map"]) == 2
    assert any(item.get("source") == "quote-bank-negative-grounding" for item in filtered["evidence_map"])


def test_negative_evidence_formation_can_use_latest_context_quote_bank_meta():
    state = {
        "claims": [{"claim_id": "claim-1", "claim": "The method is evaluated against baselines."}],
        "evidence_quote_bank": [],
        "_latest_evidence_context_meta": {
            "evidence_quote_bank": [
                {
                    "quote_id": "quote-negative-or-gap-1",
                    "source_bucket": "negative_or_gap",
                    "source_locator": "Limitations excerpt #1",
                    "raw_quote": "The evaluation does not compare against retrieval-heavy baselines.",
                    "source_span_start": 3,
                    "source_span_end": 68,
                }
            ]
        },
    }
    payload = normalize_review_update_payload({"evidence_map": []})

    filtered = _enforce_negative_evidence_formation_payload(
        "Evidence Agent",
        payload,
        {"policy_source": "hard_negative_discovery_override", "target_claim_ids": ["claim-1"]},
        state,
    )

    assert len(filtered["evidence_map"]) == 1
    assert filtered["evidence_map"][0]["quote_id"] == "quote-negative-or-gap-1"


def test_negative_evidence_formation_adds_quote_bank_when_model_negative_quote_is_unmatched():
    state = {
        "claims": [{"claim_id": "claim-1", "claim": "The method is evaluated against strong baselines."}],
        "evidence_quote_bank": [
            {
                "quote_id": "quote-negative-or-gap-1",
                "source_bucket": "negative_or_gap",
                "source_locator": "Limitations excerpt #1",
                "raw_quote": "The evaluation does not compare against retrieval-heavy baselines.",
                "source_span_start": 3,
                "source_span_end": 68,
            }
        ],
        "evidence_map": [],
        "flaw_candidates": [],
    }
    payload = normalize_review_update_payload({
        "evidence_map": [
            {
                "evidence_id": "e-unmatched-negative",
                "claim_id": "claim-1",
                "evidence": "No significant improvement is reported over strong baselines.",
                "source": "experiment",
                "raw_quote": "No significant improvement is reported over strong baselines.",
                "stance": "missing",
                "strength": "missing",
            }
        ],
    })

    filtered = _enforce_negative_evidence_formation_payload(
        "Evidence Agent",
        payload,
        {"policy_source": "hard_negative_discovery_override", "target_claim_ids": ["claim-1"]},
        state,
    )

    assert len(filtered["evidence_map"]) == 2
    quote_bank_items = [item for item in filtered["evidence_map"] if item.get("source") == "quote-bank-negative-grounding"]
    assert quote_bank_items
    assert quote_bank_items[0]["quote_id"] == "quote-negative-or-gap-1"


def test_negative_quote_bank_salvage_can_use_critique_negative_quote_meta():
    task = {
        "paper_id": "paper-critique-negative-meta",
        "mode": "s4",
        "max_turns": 7,
        "user_goal": "Review the paper.",
        "paper_text": """--- BEGIN PAPER ---
\\begin{abstract} We propose a method for retrieval-heavy evaluation.\\end{abstract}
\\section{4 Experiments} Table 1 reports model accuracy.
\\section{5 Limitations} The evaluation does not compare against retrieval-heavy baselines.
--- END PAPER ---""",
        "review_state": {
            "turn_id": 0,
            "claims": [{"claim_id": "claim-1", "claim": "The method is evaluated against retrieval-heavy baselines.", "status": "supported"}],
            "evidence_map": [],
            "flaw_candidates": [],
        },
    }

    render_critique_observation(task, {"target_claim_ids": ["claim-1"]})
    state = dict(task["review_state"])
    state["_latest_evidence_context_meta"] = dict(task["_latest_evidence_context_meta"])
    state["_latest_evidence_context_meta"]["evidence_quote_bank"] = []
    salvaged = _negative_quote_bank_salvage_payload(
        state,
        {"target_claim_ids": ["claim-1"]},
        0,
    )

    assert salvaged is not None
    assert salvaged["quote_id"].startswith("quote-critique-negative-")
    assert salvaged["negative_evidence_type"] == "missing_baseline"


def test_evidence_quote_bank_includes_negative_gap_quotes():
    paper_text = """--- BEGIN PAPER ---
\begin{abstract} We propose a method and report improvements.\end{abstract}
\section{1 Introduction} The method is motivated by retrieval tasks.
\section{4 Experiments} Table 1: Accuracy improves by 8.3%.
\section{5 Limitations} The method does not compare against retrieval-heavy baselines and lacks an ablation study.
--- END PAPER ---"""

    _context, meta = _render_evidence_context_with_meta({"paper_text": paper_text}, max_length=1800)
    quote_bank = meta["evidence_quote_bank"]

    assert any(item["source_bucket"] == "negative_or_gap" for item in quote_bank)
    assert any("does not compare" in item["raw_quote"].lower() or "lacks an ablation" in item["raw_quote"].lower() for item in quote_bank)


def test_evidence_worker_observation_exposes_target_flaws_for_negative_mode():
    task = {
        "paper_id": "paper-negative-target",
        "mode": "s4",
        "max_turns": 8,
        "user_goal": "Review the paper.",
        "paper_text": """--- BEGIN PAPER ---
\begin{abstract} We propose a method.\end{abstract}
\section{4 Experiments} Table 1: Accuracy improves by 8.3%.
\section{5 Limitations} The method does not compare against retrieval-heavy baselines.
--- END PAPER ---""",
        "review_state": {
            "turn_id": 0,
            "claims": [{"claim_id": "claim-1", "claim": "The method is empirically strong.", "status": "supported"}],
            "evidence_map": [],
            "flaw_candidates": [
                {
                    "flaw_id": "flaw-1",
                    "description": "The empirical comparison is incomplete.",
                    "status": "candidate",
                    "severity": "major",
                    "related_claim_ids": ["claim-1"],
                    "evidence_ids": [],
                }
            ],
            "unresolved_questions": [],
            "evidence_gaps": [],
        },
    }

    observation = build_worker_observation(
        task,
        {
            "policy_source": "negative_evidence_formation_override",
            "action_type": "request_evidence_recheck",
            "target_claim_ids": ["claim-1"],
            "target_flaw_ids": ["flaw-1"],
            "negative_evidence_formation_required": True,
        },
        "Evidence Agent",
    )

    assert "negative_evidence_formation_required=true" in observation
    assert "target_flaws" in observation
    assert "flaw-1" in observation
    assert "negative_or_gap" in observation


def test_s4_runs_hard_negative_discovery_once_when_no_negative_evidence():
    state = {
        "claims": [
            {"claim_id": "claim-1", "claim": "The method is empirically strong.", "status": "supported"},
            {"claim_id": "claim-2", "claim": "The evaluation is comprehensive.", "status": "supported"},
        ],
        "evidence_map": [
            {
                "evidence_id": "evidence-1",
                "claim_id": "claim-1",
                "evidence": "Table 1 supports the claim.",
                "stance": "supports",
                "strength": "strong",
                "verified_grounding_label": "paper_grounded_exact",
                "semantic_grounding_label": "semantic_support_verified",
            },
            {
                "evidence_id": "evidence-2",
                "claim_id": "claim-2",
                "evidence": "Section 4 supports the evaluation claim.",
                "stance": "supports",
                "strength": "medium",
                "verified_grounding_label": "paper_grounded_exact",
                "semantic_grounding_label": "semantic_support_verified",
            },
        ],
        "flaw_candidates": [],
        "evidence_gaps": [],
        "unresolved_questions": [],
    }

    payload = _apply_manager_policy_fallback(
        {"decision": "continue", "action_type": "analyze_flaws", "selected_agents": ["Critique Agent"]},
        state,
        "s4",
        ["Evidence Agent", "Critique Agent"],
        1,
        recent_turn_logs=[],
    )

    assert payload["policy_source"] == "hard_negative_discovery_override"
    assert payload["action_type"] == "request_evidence_recheck"
    assert payload["negative_evidence_formation_required"] is True
    assert payload["selected_agents"] == ["Evidence Agent"]






def test_parse_turn_action_filters_positive_evidence_in_hard_negative_mode():
    action = json.dumps(
        {
            "mode": "s4",
            "turn_id": 3,
            "manager": {
                "decision": "continue",
                "action_type": "request_evidence_recheck",
                "policy_source": "hard_negative_discovery_override",
            },
            "workers": [
                {
                    "agent_id": "Evidence Agent",
                    "payload": {
                        "evidence_map": [
                            {"evidence_id": "e-pos", "claim_id": "claim-1", "stance": "supports", "strength": "strong", "evidence": "Positive support."}
                        ]
                    },
                }
            ],
        }
    )

    parsed = parse_turn_action(action)
    payload = parsed["workers"][0]["payload"]

    assert payload["evidence_map"] == []
    assert payload["unresolved_questions"]
    assert "Positive" not in json.dumps(payload, ensure_ascii=False)


def test_negative_evidence_formation_uses_evidence_prompt_during_recovery_action():
    prompt = _resolve_prompt_template(
        "Evidence Agent",
        {
            "policy_source": "hard_negative_discovery_override",
            "negative_evidence_formation_required": True,
            "action_type": "request_evidence_recheck",
            "turn_mode": "normal_evidence",
        },
    )

    assert "Evidence Agent" in prompt
    assert "recovery patch" not in prompt.lower()


def test_hard_negative_discovery_payload_filters_positive_support():
    payload = _enforce_negative_evidence_formation_payload(
        "Evidence Agent",
        {
            "evidence_map": [
                {"evidence_id": "e-pos", "claim_id": "claim-1", "stance": "supports", "strength": "strong", "evidence": "Positive support."}
            ]
        },
        {"policy_source": "hard_negative_discovery_override"},
    )

    assert payload["evidence_map"] == []
    assert payload["unresolved_questions"]
    note = str(payload["unresolved_questions"][0])
    # P0-4: paper-side, reviewer-neutral phrasing (no system-process language).
    assert "verified paper-negative evidence" in note
    forbidden = (
        "positive/support evidence",
        "filtered",
        "salvage",
        "hard-negative",
        "system",
    )
    for term in forbidden:
        assert term not in note.lower()


def test_s4_hard_negative_discovery_overrides_redundant_extract_claims():
    state = {
        "claims": [
            {"claim_id": "claim-1", "claim": "The method improves benchmark accuracy.", "status": "supported"},
            {"claim_id": "claim-2", "claim": "The evaluation covers strong baselines.", "status": "supported"},
        ],
        "evidence_map": [
            {"evidence_id": "evidence-1", "claim_id": "claim-1", "evidence": "Table 1 supports the improvement.", "stance": "supports", "strength": "strong"},
            {"evidence_id": "evidence-2", "claim_id": "claim-2", "evidence": "Section 4 describes baselines.", "stance": "supports", "strength": "medium"},
        ],
        "flaw_candidates": [],
        "evidence_gaps": [],
        "unresolved_questions": [],
    }

    payload = _apply_manager_policy_fallback(
        {"decision": "continue", "action_type": "extract_claims", "selected_agents": ["Claim Agent"]},
        state,
        "s4",
        ["Evidence Agent", "Critique Agent", "Claim Agent"],
        1,
        recent_turn_logs=[],
    )

    assert payload["policy_source"] == "hard_negative_discovery_override"
    assert payload["action_type"] == "request_evidence_recheck"
    assert payload["negative_evidence_formation_required"] is True
    assert payload["selected_agents"] == ["Evidence Agent"]


def test_hard_negative_discovery_does_not_loop_after_recent_attempt():
    state = {
        "claims": [{"claim_id": "claim-1", "claim": "The method is empirically strong.", "status": "supported"}],
        "evidence_map": [{"evidence_id": "evidence-1", "claim_id": "claim-1", "evidence": "Support.", "stance": "supports", "strength": "strong"}],
        "flaw_candidates": [],
    }

    payload = _apply_manager_policy_fallback(
        {"decision": "continue", "action_type": "analyze_flaws", "selected_agents": ["Critique Agent"]},
        state,
        "s4",
        ["Evidence Agent", "Critique Agent"],
        1,
        recent_turn_logs=[{"policy_source": "hard_negative_discovery_override", "negative_evidence_formation_required": True}],
    )

    assert payload.get("policy_source") != "hard_negative_discovery_override"


# ----------------------------------------------------------------------
# Mainline-Final-Integrated P0-2 budget-aware refinement tests.
# ----------------------------------------------------------------------


def _hard_negative_budget_state_with_medium_support_only():
    """A paper with one medium positive support and no negative evidence:
    the original P0-2 gate would fire ``hard_negative_discovery_override``
    on this state, but the budget-aware refinement skips it when there is
    only one free turn left and no positive support has formed yet."""
    return {
        "claims": [
            {"claim_id": "claim-1", "claim": "The method is empirically strong.", "status": "supported"},
            {"claim_id": "claim-2", "claim": "The evaluation is comprehensive.", "status": "supported"},
        ],
        "evidence_map": [
            {
                "evidence_id": "evidence-1",
                "claim_id": "claim-1",
                "evidence": "Section 4 supports the claim with a partial result.",
                "stance": "supports",
                "strength": "medium",
                "verified_grounding_label": "paper_grounded_exact",
                "semantic_grounding_label": "semantic_support_verified",
            },
        ],
        "flaw_candidates": [],
        "evidence_gaps": [],
        "unresolved_questions": [],
    }


def test_hard_negative_discovery_skipped_when_last_free_turn_and_no_positive_inventory():
    state = _hard_negative_budget_state_with_medium_support_only()

    # max_turns=4, step=3: the override turn would consume T3 and the
    # recovery commit T4 -- the same pattern that collapsed real strong
    # support on full39.  With no real_strong and only one medium
    # support, ``_positive_inventory_ready`` is False and the gate must
    # skip the override so T3 can keep grounding positive support.
    payload = _apply_manager_policy_fallback(
        {
            "decision": "continue",
            "action_type": "analyze_flaws",
            "selected_agents": ["Critique Agent"],
            "_phase_step": 3,
            "_phase_turn_cap": 4,
        },
        state,
        "s4",
        ["Evidence Agent", "Critique Agent"],
        1,
        recent_turn_logs=[],
    )

    assert payload.get("policy_source") != "hard_negative_discovery_override"
    assert payload["action_type"] != "request_evidence_recheck"
    # The skip reason is surfaced in policy_notes for offline audit.
    assert any(
        "hard_negative_discovery_override skipped budget_aware_skip" in str(note)
        for note in payload.get("policy_notes", [])
    )


def test_hard_negative_discovery_fires_when_last_free_turn_but_positive_inventory_ready():
    state = _hard_negative_budget_state_with_medium_support_only()
    # Promote the existing medium support to strong: positive inventory
    # is now ready, so the gate is allowed to fire even on the last free
    # turn (the paper does not need T3 for more support formation).
    state["evidence_map"][0]["strength"] = "strong"

    payload = _apply_manager_policy_fallback(
        {
            "decision": "continue",
            "action_type": "analyze_flaws",
            "selected_agents": ["Critique Agent"],
            "_phase_step": 3,
            "_phase_turn_cap": 4,
        },
        state,
        "s4",
        ["Evidence Agent", "Critique Agent"],
        1,
        recent_turn_logs=[],
    )

    assert payload["policy_source"] == "hard_negative_discovery_override"
    assert payload["action_type"] == "request_evidence_recheck"
    assert payload["negative_evidence_formation_required"] is True


def test_hard_negative_discovery_fires_with_room_to_spare_even_without_positive_inventory():
    state = _hard_negative_budget_state_with_medium_support_only()

    # max_turns=5, step=3: remaining_after_current = 2.  There is still a
    # follow-up support-formation turn after the recovery commit, so the
    # gate fires even though ``_positive_inventory_ready`` is False.
    payload = _apply_manager_policy_fallback(
        {
            "decision": "continue",
            "action_type": "analyze_flaws",
            "selected_agents": ["Critique Agent"],
            "_phase_step": 3,
            "_phase_turn_cap": 5,
        },
        state,
        "s4",
        ["Evidence Agent", "Critique Agent"],
        1,
        recent_turn_logs=[],
    )

    assert payload["policy_source"] == "hard_negative_discovery_override"
    assert payload["action_type"] == "request_evidence_recheck"


def test_hard_negative_discovery_skipped_when_no_follow_up_turn_remains():
    state = _hard_negative_budget_state_with_medium_support_only()
    # Even with positive inventory ready, firing on the very last turn
    # leaves no room for the recovery commit and is always wasted.
    state["evidence_map"][0]["strength"] = "strong"

    payload = _apply_manager_policy_fallback(
        {
            "decision": "continue",
            "action_type": "finalize",
            "selected_agents": [],
            "_phase_step": 4,
            "_phase_turn_cap": 4,
        },
        state,
        "s4",
        ["Evidence Agent", "Critique Agent"],
        1,
        recent_turn_logs=[],
    )

    assert payload.get("policy_source") != "hard_negative_discovery_override"
    assert payload["action_type"] != "request_evidence_recheck"


def test_hard_negative_discovery_fires_when_phase_step_unknown_legacy_behavior():
    state = _hard_negative_budget_state_with_medium_support_only()

    # Older callers / unit tests that do not supply ``_phase_step`` /
    # ``_phase_turn_cap`` should retain the original always-fire behaviour
    # so we don't silently weaken existing coverage.
    payload = _apply_manager_policy_fallback(
        {"decision": "continue", "action_type": "analyze_flaws", "selected_agents": ["Critique Agent"]},
        state,
        "s4",
        ["Evidence Agent", "Critique Agent"],
        1,
        recent_turn_logs=[],
    )

    assert payload["policy_source"] == "hard_negative_discovery_override"
    assert payload["action_type"] == "request_evidence_recheck"


def test_critique_observation_exposes_negative_quote_bank_without_neutral_controls():
    paper_text = (
        "--- BEGIN PAPER ---\n"
        "Abstract. We propose a diagnostic benchmark.\n"
        "\n\section{Method} The method uses a transformer encoder for review diagnosis.\n"
        "\n\section{Limitations} The current evaluation does not include an ablation study "
        "or compare against a strong retrieval baseline. The implementation was also tested "
        "with and without guidance as a neutral control.\n"
        "--- END PAPER ---"
    )
    task = {
        "paper_id": "paper-critique-negative-bank",
        "mode": "s4",
        "max_turns": 4,
        "paper_text": paper_text,
        "user_goal": "Expose actionable negative quotes to critique.",
        "review_state": {
            "claims": [
                {
                    "claim_id": "claim-1",
                    "claim": "The evaluation is comprehensive and includes ablation comparisons.",
                    "status": "uncertain",
                    "claim_kind": "paper_extracted",
                }
            ],
            "evidence_map": [],
            "flaw_candidates": [],
            "unresolved_questions": [],
            "evidence_gaps": [],
            "conflict_notes": [],
            "turn_id": 2,
        },
    }

    observation = render_critique_observation(
        task,
        {"action_type": "analyze_flaws", "target_claim_ids": ["claim-1"]},
    )

    assert "Critique Negative Quote Bank" in observation
    assert "quote-critique-negative-" in observation
    assert "Critique Negative Grounding Rules" in observation
    assert "negative_evidence_ids" in observation
    assert "missing_ablation" in observation or "direct_contradiction" in observation
    assert "does not include an ablation" in observation
    assert "with and without guidance" not in observation.split("# Critique Negative Quote Bank", 1)[1].split("# Critique State Slice", 1)[0]


# --- P0 #1 ghost-evidence hydration for recovery patches (B fix) ---

def test_ghost_evidence_patch_rebinds_to_real_verified_negative():
    from agent_system.inference import review_runner as _rr
    state = {
        "claims": [{"claim_id": "claim-1", "status": "partially_supported"}],
        "evidence_map": [
            {
                "evidence_id": "evidence-neg-1",
                "claim_id": "claim-1",
                "stance": "contradicts",
                "strength": "strong",
                "verified_grounding_label": "paper_grounded_exact",
                "semantic_grounding_label": "semantic_negative_verified",
                "source": "results",
            }
        ],
    }
    manager_payload = {
        "effective_action_type": "challenge_previous_hypothesis",
        "target_claim_ids": ["claim-1"],
        "target_evidence_ids": ["evidence-neg-1"],
    }
    worker_payload = {
        "action": "apply_recovery_patch",
        "target_type": "claim",
        "target_id": "claim-1",
        "old_status": "partially_supported",
        "new_status": "unsupported",
        "supporting_evidence_ids": ["quote-critique-negative-1"],
    }
    out = _rr._maybe_salvage_recovery_payload("Critique Agent", dict(worker_payload), state, manager_payload)
    known = {e["evidence_id"] for e in state["evidence_map"]}
    assert out.get("action") == "apply_recovery_patch"
    cited = out.get("supporting_evidence_ids") or []
    assert cited and all(c in known for c in cited)
    assert out.get("ghost_evidence_rebind_used") is True


def test_model_generated_hypothesis_patch_rebinds_to_real_verified_negative():
    from agent_system.inference import review_runner as _rr
    state = {
        "claims": [{"claim_id": "claim-1", "status": "partially_supported"}],
        "current_hypotheses": ["Claim claim-1 may be overstated."],
        "evidence_map": [
            {
                "evidence_id": "evidence-neg-1",
                "claim_id": "claim-1",
                "stance": "contradicts",
                "strength": "strong",
                "verified_grounding_label": "paper_grounded_exact",
                "semantic_grounding_label": "semantic_negative_verified",
                "source": "results",
            }
        ],
    }
    manager_payload = {
        "effective_action_type": "challenge_previous_hypothesis",
        "target_claim_ids": ["claim-1"],
        "target_evidence_ids": ["evidence-neg-1"],
    }
    worker_payload = {
        "action": "apply_recovery_patch",
        "_recovery_patch_source": "model_generated",
        "target_type": "hypothesis",
        "target_id": "Claim claim-1 may be overstated.",
        "old_status": "active",
        "new_status": "challenged",
        "supporting_evidence_ids": ["evidence-neg-1"],
    }

    out = _rr._maybe_salvage_recovery_payload("Critique Agent", dict(worker_payload), state, manager_payload)

    assert out.get("action") == "apply_recovery_patch"
    assert out.get("target_type") == "claim"
    assert out.get("target_id") == "claim-1"
    assert out.get("supporting_evidence_ids") == ["evidence-neg-1"]
    assert out.get("weak_recovery_target_rebind_used") is True


def test_model_generated_context_claim_patch_blocks_without_real_rebind_target():
    from agent_system.inference import review_runner as _rr
    state = {
        "claims": [
            {
                "claim_id": "claim-paper-context-1",
                "status": "partially_supported",
                "claim_kind": "paper_extracted",
                "claim_origin_kind": "context_synthesized",
            }
        ],
        "evidence_map": [
            {"evidence_id": "evidence-pos-1", "claim_id": "claim-paper-context-1", "stance": "supports", "strength": "strong"}
        ],
    }
    manager_payload = {
        "effective_action_type": "challenge_previous_hypothesis",
        "target_claim_ids": ["claim-paper-context-1"],
    }
    worker_payload = {
        "action": "apply_recovery_patch",
        "_recovery_patch_source": "model_generated",
        "target_type": "claim",
        "target_id": "claim-paper-context-1",
        "old_status": "partially_supported",
        "new_status": "unsupported",
        "supporting_evidence_ids": ["evidence-pos-1"],
    }

    out = _rr._maybe_salvage_recovery_payload("Critique Agent", dict(worker_payload), state, manager_payload)

    assert out.get("action") == "blocked"
    assert out.get("weak_recovery_target_rebind_used") is True
    assert out.get("target_id") == "claim-paper-context-1"


def test_verified_negative_claim_salvage_skips_paper_fallback_claim():
    from agent_system.inference import review_runner as _rr

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
                "evidence_id": "evidence-neg-fallback",
                "claim_id": "claim-paper-fallback-1",
                "stance": "contradicts",
                "strength": "strong",
                "source": "quote-bank-negative-grounding",
                "verified_grounding_label": "paper_grounded_exact",
                "semantic_grounding_label": "semantic_negative_verified",
                "negative_evidence_type": "negative_result",
                "claim_status_downgrade_allowed": True,
            }
        ],
    }

    out = _rr._build_verified_negative_claim_recovery_patch(
        state,
        {
            "effective_action_type": "challenge_previous_hypothesis",
            "target_claim_ids": ["claim-paper-fallback-1"],
            "target_evidence_ids": ["evidence-neg-fallback"],
        },
    )

    assert out is None


def test_ghost_evidence_patch_blocks_when_no_real_negative():
    from agent_system.inference import review_runner as _rr
    state = {
        "claims": [{"claim_id": "claim-1", "status": "partially_supported"}],
        "evidence_map": [
            {"evidence_id": "evidence-pos-1", "claim_id": "claim-1", "stance": "supports", "strength": "strong"}
        ],
    }
    manager_payload = {
        "effective_action_type": "challenge_previous_hypothesis",
        "target_claim_ids": ["claim-1"],
        "target_evidence_ids": [],
    }
    worker_payload = {
        "action": "apply_recovery_patch",
        "target_type": "claim",
        "target_id": "claim-1",
        "old_status": "partially_supported",
        "new_status": "unsupported",
        "supporting_evidence_ids": ["quote-critique-negative-1"],
    }
    out = _rr._maybe_salvage_recovery_payload("Critique Agent", dict(worker_payload), state, manager_payload)
    assert out.get("action") == "blocked"
    assert "quote-critique-negative-1" not in (out.get("supporting_evidence_ids") or [])


def test_recovery_patch_with_real_evidence_is_untouched():
    from agent_system.inference import review_runner as _rr
    state = {
        "claims": [{"claim_id": "claim-1", "status": "partially_supported"}],
        "evidence_map": [
            {"evidence_id": "evidence-neg-1", "claim_id": "claim-1", "stance": "contradicts", "strength": "strong",
             "verified_grounding_label": "paper_grounded_exact", "semantic_grounding_label": "semantic_negative_verified"}
        ],
    }
    manager_payload = {"effective_action_type": "challenge_previous_hypothesis", "target_claim_ids": ["claim-1"]}
    worker_payload = {
        "action": "apply_recovery_patch", "target_type": "claim", "target_id": "claim-1",
        "old_status": "partially_supported", "new_status": "unsupported",
        "supporting_evidence_ids": ["evidence-neg-1"],
    }
    out = _rr._maybe_salvage_recovery_payload("Critique Agent", dict(worker_payload), state, manager_payload)
    assert out.get("action") == "apply_recovery_patch"
    assert out.get("supporting_evidence_ids") == ["evidence-neg-1"]
    assert not out.get("ghost_evidence_rebind_used")


def test_stale_claim_downgrade_old_status_is_refreshed():
    from agent_system.environments.env_package.review import state as _state
    live = {
        "claims": [{"claim_id": "claim-1", "status": "supported"}],
    }
    parsed = {
        "target_type": "claim",
        "target_id": "claim-1",
        "old_status": "partially_supported",
        "new_status": "unsupported",
    }
    _state._refresh_stale_claim_downgrade_old_status(live, parsed)
    assert parsed["old_status"] == "supported"
    assert parsed.get("old_status_refreshed_from") == "partially_supported"


def test_stale_refresh_skips_when_transition_illegal():
    from agent_system.environments.env_package.review import state as _state
    live = {"claims": [{"claim_id": "claim-1", "status": "unsupported"}]}
    parsed = {"target_type": "claim", "target_id": "claim-1",
              "old_status": "partially_supported", "new_status": "unsupported"}
    _state._refresh_stale_claim_downgrade_old_status(live, parsed)
    # unsupported -> unsupported is not a legal recovery transition; do not refresh
    assert parsed["old_status"] == "partially_supported"
    assert "old_status_refreshed_from" not in parsed


# --- R2: zero-real targeted retry (spec task 12.1) ---

from agent_system.inference.review_runner import (
    _maybe_zero_real_targeted_retry as _r2_retry,
    _claims_without_real_strong_support as _r2_unsupported,
)


def _r2_zero_real_state():
    # a real claim with only a method-only (non-real-strong) evidence -> zero real strong
    return {
        "mode": "s4",
        "claims": [{"claim_id": "claim-1", "claim_kind": "paper_extracted",
                    "claim": "The method is effective.", "status": "uncertain"}],
        "evidence_map": [],
        "turn_logs": [],
    }


def test_r2_triggers_on_zero_real_finalize_with_budget():
    state = _r2_zero_real_state()
    mp = {"decision": "finalize", "action_type": "finalize", "selected_agents": []}
    out = _r2_retry(mp, state, step=4, turn_cap=7, worker_ids=["Evidence Agent", "Claim Agent"], worker_limit=2)
    assert out.get("targeted_retry_triggered") is True
    assert out.get("action_type") == "verify_evidence"
    assert out.get("policy_source") == "zero_real_targeted_retry_override"
    assert "Evidence Agent" in out.get("selected_agents", [])
    assert out.get("target_claim_ids") == ["claim-1"]


def test_r2_does_not_trigger_when_real_strong_exists():
    state = {
        "mode": "s4",
        "claims": [{"claim_id": "claim-1", "claim_kind": "paper_extracted",
                    "claim": "Effective.", "status": "supported"}],
        "evidence_map": [
            {"evidence_id": "evidence-1", "claim_id": "claim-1", "stance": "supports",
             "strength": "strong", "raw_quote": "Table 2 shows 91% accuracy outperforming baseline.",
             "source": "Results", "source_locator": "Table 2",
             "verified_grounding_label": "paper_grounded_exact",
             "semantic_grounding_label": "semantic_support_verified",
             "binding_status": "bound_real_claim"},
        ],
        "turn_logs": [],
    }
    mp = {"decision": "finalize", "action_type": "finalize", "selected_agents": []}
    out = _r2_retry(mp, state, step=4, turn_cap=7, worker_ids=["Evidence Agent"], worker_limit=2)
    assert not out.get("targeted_retry_triggered")
    assert out.get("action_type") == "finalize"


def test_r2_does_not_trigger_without_budget():
    state = _r2_zero_real_state()
    mp = {"decision": "finalize", "action_type": "finalize", "selected_agents": []}
    out = _r2_retry(mp, state, step=7, turn_cap=7, worker_ids=["Evidence Agent"], worker_limit=2)
    assert not out.get("targeted_retry_triggered")


def test_r2_does_not_trigger_when_not_finalizing():
    state = _r2_zero_real_state()
    mp = {"decision": "continue", "action_type": "verify_evidence", "selected_agents": ["Evidence Agent"]}
    out = _r2_retry(mp, state, step=3, turn_cap=7, worker_ids=["Evidence Agent"], worker_limit=2)
    assert not out.get("targeted_retry_triggered")


def test_r2_only_one_retry_per_episode():
    state = _r2_zero_real_state()
    # a prior turn already used the retry override
    state["turn_logs"] = [{"policy_source": "zero_real_targeted_retry_override"}]
    mp = {"decision": "finalize", "action_type": "finalize", "selected_agents": []}
    out = _r2_retry(mp, state, step=5, turn_cap=7, worker_ids=["Evidence Agent"], worker_limit=2)
    assert not out.get("targeted_retry_triggered")


def test_r2_unsupported_lists_only_zero_support_real_claims():
    state = _r2_zero_real_state()
    assert _r2_unsupported(state) == ["claim-1"]


# --- P2: model adapter for description-only evidence statements ---

from agent_system.inference.review_runner import (
    _apply_quote_first_evidence_statement_adapter as _p2_quote_first_adapter,
)


def test_p2_quote_first_adapter_rewrites_description_only_evidence():
    manager_payload = {"action_type": "verify_evidence"}
    trace = {}
    payload = {
        "evidence_map": [
            {
                "evidence_id": "evidence-1",
                "claim_id": "claim-1",
                "evidence": "A direct, quantitative comparison of CO-MOT performance against a strong baseline.",
                "raw_quote": "Table 2 reports CO-MOT achieves 83.2 HOTA on DanceTrack.",
                "source_locator": "Table 2",
                "strength": "strong",
                "stance": "supports",
            }
        ]
    }

    out = _p2_quote_first_adapter("Evidence Agent", payload, manager_payload, trace_worker=trace)
    ev = out["evidence_map"][0]

    assert ev["agent_evidence_statement"].startswith("A direct, quantitative comparison")
    assert ev["evidence"].startswith("Table 2 reports:")
    assert "83.2 HOTA" in ev["evidence"]
    assert ev["model_adapter_quote_first_rewrite"] is True
    assert out["model_adapter_quote_first_rewrite_count"] == 1
    assert trace["model_adapter_quote_first_rewrite_count"] == 1


def test_p2_quote_first_adapter_preserves_concrete_evidence_statement():
    manager_payload = {"action_type": "verify_evidence"}
    payload = {
        "evidence_map": [
            {
                "evidence_id": "evidence-1",
                "claim_id": "claim-1",
                "evidence": "Table 2 reports CO-MOT achieves 83.2 HOTA on DanceTrack.",
                "raw_quote": "Table 2 reports CO-MOT achieves 83.2 HOTA on DanceTrack.",
                "source_locator": "Table 2",
                "strength": "strong",
                "stance": "supports",
            }
        ]
    }

    out = _p2_quote_first_adapter("Evidence Agent", payload, manager_payload)
    ev = out["evidence_map"][0]

    assert ev["evidence"] == "Table 2 reports CO-MOT achieves 83.2 HOTA on DanceTrack."
    assert "agent_evidence_statement" not in ev
    assert "model_adapter_quote_first_rewrite_count" not in out


def test_p2_quote_first_adapter_respects_large_model_mode():
    payload = {
        "evidence_map": [
            {
                "evidence_id": "evidence-1",
                "claim_id": "claim-1",
                "evidence": "A direct, quantitative comparison of CO-MOT performance against a strong baseline.",
                "raw_quote": "Table 2 reports CO-MOT achieves 83.2 HOTA on DanceTrack.",
                "source_locator": "Table 2",
                "strength": "strong",
                "stance": "supports",
            }
        ]
    }

    out = _p2_quote_first_adapter(
        "Evidence Agent",
        payload,
        {"model_adapter_mode": "large_model"},
    )

    ev = out["evidence_map"][0]
    assert ev["evidence"].startswith("A direct, quantitative comparison")
    assert "model_adapter_quote_first_rewrite_count" not in out
