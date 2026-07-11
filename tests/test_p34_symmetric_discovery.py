import json

from scripts.p34_symmetric_discovery import (
    build_neutral_packets,
    candidate_similarity,
    cluster_candidates,
    parse_discoveries,
)


def _candidate(code, candidate_id, hypothesis, entities):
    return {
        "source_candidate_id": candidate_id,
        "paper_id": "paper-1",
        "issue_type": "statistical_or_reporting_gap",
        "claim_id": "claim-1",
        "claim_anchor": "The method improves accuracy on BenchX.",
        "hypothesis": hypothesis,
        "paper_anchor": "improves accuracy on BenchX",
        "expected_evidence": "confidence intervals or standard deviations for BenchX accuracy",
        "counterevidence_query": "BenchX confidence interval standard deviation error bar",
        "named_entities_or_metrics": entities,
        "confidence": 0.8,
        "_discovery_code": code,
        "_discovery_model": "mimo-v2.5" if code == "M" else "mimo-v2.5-pro",
    }


def test_parse_discoveries_retains_provenance_only_in_internal_candidate():
    raw = json.dumps({"hypotheses": [{
        "hypothesis_id": "h1",
        "issue_type": "missing_ablation",
        "claim_id": "claim-1",
        "claim_anchor": "Module A improves accuracy.",
        "hypothesis": "The contribution attributed to Module A is not isolated by an ablation.",
        "paper_anchor": "Module A improves accuracy on BenchX.",
        "expected_evidence": "an ablation removing Module A under the same BenchX protocol",
        "counterevidence_query": "Module A ablation remove BenchX same protocol",
        "named_entities_or_metrics": ["Module A", "BenchX"],
        "confidence": 0.9,
    }]})

    candidates, error = parse_discoveries(raw, "paper-1", "P", 8)

    assert error == ""
    assert candidates[0]["_discovery_code"] == "P"
    assert candidates[0]["issue_type"] == "missing_ablation"


def test_cross_model_duplicate_candidates_form_one_neutral_cluster():
    left = _candidate(
        "M", "M-paper-1-h1",
        "BenchX accuracy is reported without confidence intervals or standard deviations.",
        ["BenchX", "accuracy"],
    )
    right = _candidate(
        "P", "P-paper-1-h1",
        "The BenchX accuracy result lacks standard deviations or confidence intervals.",
        ["BenchX", "accuracy"],
    )

    assert candidate_similarity(left, right) >= 0.58
    clusters = cluster_candidates([left, right])

    assert len(clusters) == 1
    assert {item["_discovery_code"] for item in clusters[0]} == {"M", "P"}


def test_neutral_packet_hides_generator_identity_and_sidecar_preserves_both_models():
    paper_text = "# Results\nThe method improves accuracy on BenchX. Accuracy is 82.1%."
    states = {"paper-1": {"paper_text": paper_text}}
    left = _candidate(
        "M", "M-paper-1-h1",
        "BenchX accuracy is reported without confidence intervals or standard deviations.",
        ["BenchX", "accuracy"],
    )
    right = _candidate(
        "P", "P-paper-1-h1",
        "The BenchX accuracy result lacks standard deviations or confidence intervals.",
        ["BenchX", "accuracy"],
    )

    packets, provenance, annotations = build_neutral_packets(states, [left, right])

    assert len(packets) == len(provenance) == len(annotations) == 1
    assert provenance[0]["discovery_codes"] == ["M", "P"]
    assert annotations[0]["allowed_labels"] == ["A", "B", "C", "D"]
    serialized_packet = json.dumps(packets[0])
    assert "mimo-v2.5" not in serialized_packet
    assert "_discovery_code" not in serialized_packet
    for item in packets[0]["retrieved_evidence"]:
        assert paper_text[item["source_span_start"]:item["source_span_end"]] == item["quote"]
