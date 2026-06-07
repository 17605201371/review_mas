from agent_system.environments.env_package.review.state import _apply_programmatic_source_locator


def test_programmatic_locator_derives_table_type_from_quote_id():
    state = {
        "evidence_quote_bank": [
            {
                "quote_id": "quote-table-or-figure-1",
                "source_locator": "Table 2",
                "source_bucket": "table_or_figure",
                "raw_quote": "Table 2 reports higher F1 scores for the proposed method.",
                "source_span_start": 100,
                "source_span_end": 160,
            }
        ]
    }
    evidence = {
        "quote_id": "quote-table-or-figure-1",
        "source_locator": "Results / Evaluation excerpt #1",
        "support_source_bucket": "result_or_experiment",
        "verified_source_span_start": 110,
        "verified_source_span_end": 150,
    }

    _apply_programmatic_source_locator(state, evidence)

    assert evidence["source_locator"] == "Table 2"
    assert evidence["locator_type"] == "table"
    assert evidence["source_locator_type"] == "table"
    assert evidence["locator_confidence"] >= 0.9
    assert evidence["source_locator_specific"] is True


def test_programmatic_locator_derives_algorithm_type_from_text_anchor():
    evidence = {
        "source_locator": "method excerpt",
        "raw_quote": "Algorithm 1 describes the iterative recovery procedure.",
        "verified_source_span_start": 10,
        "verified_source_span_end": 70,
    }

    _apply_programmatic_source_locator({}, evidence)

    assert evidence["source_locator"] == "Algorithm 1"
    assert evidence["locator_type"] == "algorithm"
    assert evidence["locator_confidence"] >= 0.8


def test_programmatic_locator_marks_generic_when_no_anchor_exists():
    evidence = {
        "source_locator": "Results / Evaluation excerpt #1",
        "raw_quote": "The method improves over the baseline in the provided experiments.",
    }

    _apply_programmatic_source_locator({}, evidence)

    assert evidence["source_locator_specific"] is False
    assert evidence["locator_type"] == "generic"
    assert evidence["locator_confidence"] == 0.0


def test_programmatic_locator_derives_theorem_type_from_text_anchor():
    evidence = {
        "source_locator": "theory excerpt",
        "raw_quote": "Theorem 2 establishes the convergence guarantee under bounded gradients.",
        "verified_source_span_start": 20,
        "verified_source_span_end": 95,
    }

    _apply_programmatic_source_locator({}, evidence)

    assert evidence["source_locator"] == "Theorem 2"
    assert evidence["locator_type"] == "theorem"
    assert evidence["source_locator_specific"] is True
    assert evidence["locator_confidence"] >= 0.8


def test_programmatic_locator_derives_figure_label_from_latex_ref():
    evidence = {
        "source_locator": "Table/Figure excerpt #1",
        "raw_quote": "As illustrated in \\cref{fig:framework}, the model has two stages.",
    }

    _apply_programmatic_source_locator({}, evidence)

    assert evidence["source_locator"] == "Figure: framework"
    assert evidence["locator_type"] == "figure"
    assert evidence["source_locator_specific"] is True
    assert evidence["locator_confidence"] >= 0.8


def test_programmatic_locator_derives_caption_anchor_from_latex_caption():
    evidence = {
        "source_locator": "Table/Figure excerpt #2",
        "raw_quote": "\\caption{Comparison of averaged D4RL scores on MuJoCo tasks.}",
    }

    _apply_programmatic_source_locator({}, evidence)

    assert evidence["source_locator"].startswith("Table/Figure caption: Comparison")
    assert evidence["locator_type"] == "table"
    assert evidence["source_locator_specific"] is True
    assert evidence["locator_confidence"] >= 0.75
