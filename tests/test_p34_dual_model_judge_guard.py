from agent_system.environments.env_package.review.paper_index import build_paper_index
from scripts.p34_dual_model_judge_guard import (
    augment_audit_packet,
    build_audit_packet,
    build_judge_prompt,
    parse_judge,
    validate_packet_spans,
    search_result_window,
)


def _candidate():
    return {
        "hypothesis_id": "h1",
        "issue_type": "result_claim_mismatch",
        "claim_id": "claim-1",
        "claim_anchor": "The reranker improves accuracy over BM25.",
        "hypothesis": "The reported gain may use a different evaluation split.",
        "paper_anchor": "Table 1 reports reranker accuracy on BenchX.",
        "expected_evidence": "Matching split definitions for reranker and BM25.",
        "counterevidence_query": "BenchX split BM25 reranker Table 1 protocol",
        "named_entities_or_metrics": ["BenchX", "BM25", "accuracy"],
    }


def test_audit_packet_spans_roundtrip_and_prompt_is_blinded():
    paper = r"""\section{Experiments}
Table 1 reports reranker accuracy on BenchX against BM25 using the official test split.
"""
    index = build_paper_index(paper)
    packet = build_audit_packet("paper-1", index, _candidate())
    prompt = build_judge_prompt(packet)

    assert validate_packet_spans(packet, index) is True
    assert packet["retrieved_evidence"]
    assert "manual_label" not in prompt
    assert "generator_model" not in prompt
    assert "MiMo" not in prompt


def test_judge_parser_rejects_unknown_evidence_ids():
    index = build_paper_index("# Results\nBenchX accuracy is reported against BM25.")
    packet = build_audit_packet("paper-1", index, _candidate())
    parsed, error = parse_judge(
        '{"verdict":"verified","accepted_evidence_ids":["invented"],"counterevidence_ids":[],"searched_section_ids":[],"confidence":0.9,"rationale":"Supported."}',
        packet,
    )

    assert parsed["verdict"] == "verified"
    assert error == "unknown_evidence_id"


def test_judge_parser_accepts_valid_structured_verdict():
    index = build_paper_index("# Results\nBenchX accuracy is reported against BM25.")
    packet = build_audit_packet("paper-1", index, _candidate())
    evidence_id = packet["retrieved_evidence"][0]["evidence_id"]
    raw = (
        '{"verdict":"uncertain","accepted_evidence_ids":[],"counterevidence_ids":["'
        + evidence_id
        + '"],"searched_section_ids":[],"confidence":0.4,"rationale":"The packet does not establish identical splits."}'
    )

    parsed, error = parse_judge(raw, packet)

    assert error == ""
    assert parsed["verdict"] == "uncertain"


def test_supplemental_retrieval_adds_new_exact_spans_only():
    paper = r"""\section{Experiments}
Table 1 reports BenchX accuracy against BM25.
\section{Implementation Details}
We use the official BM25 implementation and identical BenchX splits for every method.
"""
    index = build_paper_index(paper)
    packet = build_audit_packet("paper-1", index, _candidate())
    packet["retrieved_evidence"] = [
        item for item in packet["retrieved_evidence"] if "official BM25 implementation" not in item["quote"]
    ]
    packet["counterevidence_candidates"] = list(packet["retrieved_evidence"])

    augmented = augment_audit_packet(packet, index, "official BM25 implementation identical BenchX splits")

    assert augmented["supplemental_retrieval"]["performed"] is True
    assert augmented["supplemental_retrieval"]["added_evidence_ids"]
    assert validate_packet_spans(augmented, index) is True


def test_search_result_window_centers_late_matched_terms():
    paper = "# Results\n" + ("setup text " * 300) + "Table 6 compares SPOT with BEV-MAE and AD-PT."
    index = build_paper_index(paper)
    result = index.search("Table 6 SPOT BEV-MAE AD-PT", top_k=1)[0]

    text, start, end = search_result_window(result, max_chars=300)

    assert "Table 6 compares SPOT" in text
    assert paper[start:end] == text
