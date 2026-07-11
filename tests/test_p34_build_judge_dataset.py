import json

from scripts.p34_build_judge_dataset import _negative_packets, locate_quote


def test_locate_quote_returns_original_exact_span():
    paper = "Before. Exact quote with metric 12.4%. After."
    span, match_type = locate_quote(paper, "Exact quote with metric 12.4%.")

    assert match_type == "unique_exact"
    assert span is not None
    assert paper[span[0]:span[1]] == "Exact quote with metric 12.4%."


def test_locate_quote_maps_whitespace_normalization_to_original_source():
    paper = "Before. A quote\nwith   irregular whitespace. After."
    span, match_type = locate_quote(paper, "A quote with irregular whitespace.")

    assert match_type == "unique_whitespace_normalized"
    assert span is not None
    assert paper[span[0]:span[1]] == "A quote\nwith   irregular whitespace."


def test_locate_quote_rejects_ambiguous_occurrences():
    span, match_type = locate_quote("same quote; same quote", "same quote")

    assert span is None
    assert match_type == "ambiguous_exact"


def test_negative_packet_provenance_is_sidecar_not_judge_visible():
    states = {"p1": {"paper_text": "# Results\nThe method reports accuracy."}}
    manual = {"hypotheses": [{
        "paper_id": "p1",
        "hypothesis_id": "h1",
        "claim_anchor": "The method reports accuracy.",
        "hypothesis": "The reported accuracy lacks uncertainty estimates.",
        "paper_anchor": "reports accuracy",
        "expected_evidence": "confidence intervals",
        "counterevidence_query": "confidence interval uncertainty standard deviation",
        "label": "B",
    }]}

    packets, labels, provenance = _negative_packets(states, manual)

    assert packets[0]["packet_id"] == labels[0]["packet_id"] == provenance[0]["packet_id"]
    assert provenance[0]["discovery_code"] == "M"
    assert "discovery_code" not in packets[0]
    assert "discovery_model" not in json.dumps(packets[0])
