from agent_system.environments.env_package.review.state import (
    _build_evidence_quote_bank,
    _prompt_quote_bank_entries,
)


def test_quote_bank_exposes_ablation_and_comparison_sources_with_role_hints():
    body = """\section{Introduction} We propose a model.\n\section{Experiments} We compare with the strongest baseline and outperform it by 4.2 F1.\n\section{Ablation} Ablation study shows that removing the routing module reduces accuracy by 3.1%.\n\section{Method} The routing module selects candidate paths.
"""

    bank = _build_evidence_quote_bank(body, max_quotes=8, claim_query_terms={"routing", "baseline", "accuracy"})
    buckets = [item["source_bucket"] for item in bank]

    assert "ablation" in buckets
    assert "comparison" in buckets

    prompt_entries = _prompt_quote_bank_entries(bank, max_items=8)
    by_bucket = {item["source_bucket"]: item for item in prompt_entries}
    assert by_bucket["ablation"]["support_role_hint"] == "ablation_support"
    assert by_bucket["comparison"]["support_role_hint"] == "comparison_support"
    assert by_bucket["ablation"]["raw_quote"]
    assert by_bucket["comparison"]["raw_quote"]
