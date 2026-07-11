import json
from types import SimpleNamespace

from scripts.p34_judge_runner import (
    _apply_discovery_provenance_filter,
    _classification_metrics,
    _load_labels_with_diagnostics,
    audit_prompt_batch,
    build_task_prompt,
    parse_task_verdict,
    score_cases,
    run_experiment,
)


def test_label_loader_reports_duplicates_without_silent_overwrite(tmp_path):
    first, second = tmp_path / "first.json", tmp_path / "second.json"
    first.write_text(json.dumps({"labels": [{"packet_id": "p1", "human_label": "supports"}]}))
    second.write_text(json.dumps({"labels": [
        {"packet_id": "p1", "human_label": "contradicts"},
        {"packet_id": "p2", "human_label": "faithful"},
    ]}))

    labels, diagnostics = _load_labels_with_diagnostics([first, second])

    assert labels["p1"]["human_label"] == "supports"
    assert labels["p2"]["human_label"] == "faithful"
    assert diagnostics["row_count"] == 3
    assert diagnostics["unique_packet_count"] == 2
    assert diagnostics["duplicate_count"] == 1
    assert diagnostics["duplicates"][0]["identical"] is False


def test_evidence_relation_prompt_and_parser_are_label_blinded():
    packet = {
        "packet_id": "positive-p1-1",
        "task_type": "evidence_relation",
        "paper_id": "p1",
        "claim": {"claim_id": "c1", "claim_text": "Accuracy improves."},
        "candidate_evidence": {
            "evidence_id": "e1",
            "quote": "Accuracy improves by 12.4%.",
            "source_span_start": 0,
            "source_span_end": 27,
            "section_id": "s1",
        },
        "searched_section_ids": ["s1"],
        "counterevidence_candidates": [],
    }
    prompt = build_task_prompt(packet, allow_supplemental=True)
    parsed, error = parse_task_verdict(
        '{"verdict":"supports","accepted_evidence_ids":["e1"],"counterevidence_ids":[],"searched_section_ids":["s1"],"confidence":0.9,"rationale":"The quote directly reports the claimed gain.","supplemental_retrieval_request":""}',
        packet,
    )

    assert "human_label" not in prompt
    assert error == ""
    assert parsed["verdict"] == "supports"


def test_prompt_blinding_audit_roundtrips_exact_packet_and_rejects_nested_identity_fields():
    clean = {
        "packet_id": "positive-p1-1", "task_type": "evidence_relation", "paper_id": "p1",
        "claim": {"claim_text": "Accuracy improves."},
        "candidate_evidence": {"evidence_id": "e1", "quote": "Accuracy improves."},
        "searched_section_ids": [], "counterevidence_candidates": [],
    }
    clean_prompt = build_task_prompt(clean, allow_supplemental=True)
    clean_audit = audit_prompt_batch(
        [("P34 Initial Judge M-P", clean_prompt)],
        [{"packet": clean, "group": "M-P"}],
        stage="initial:P",
    )
    contaminated = json.loads(json.dumps(clean))
    contaminated["claim"]["human_reviewer_id"] = "reviewer-secret"
    contaminated["discovery_code"] = "M"
    contaminated_prompt = build_task_prompt(contaminated, allow_supplemental=True)
    contaminated_audit = audit_prompt_batch(
        [("P34 Initial Judge M-P", contaminated_prompt)],
        [{"packet": contaminated, "group": "M-P"}],
        stage="initial:P",
    )

    assert clean_audit["status"] == "PASS"
    assert clean_audit["items"][0]["embedded_packet_exact_match"] is True
    assert clean_audit["items"][0]["packet_sha256"] == clean_audit["items"][0]["embedded_packet_sha256"]
    assert contaminated_audit["status"] == "BLOCKED"
    categories = {
        item["category"] for item in contaminated_audit["items"][0]["forbidden_field_violations"]
    }
    assert categories == {"human_label_or_identity", "discovery_identity"}


def test_run_experiment_blocks_contaminated_packet_before_provider_calls(monkeypatch, tmp_path):
    packet = {
        "packet_id": "positive-p1-1", "paper_id": "p1", "task_type": "evidence_relation",
        "claim": {"claim_text": "Accuracy improves.", "human_label": "supports"},
        "candidate_evidence": {
            "evidence_id": "e1", "quote": "Accuracy improves.",
            "source_span_start": 0, "source_span_end": 18,
        },
        "searched_section_ids": [], "counterevidence_candidates": [],
    }
    packets = tmp_path / "packets.jsonl"
    packets.write_text(json.dumps(packet) + "\n")
    labels = tmp_path / "labels.json"
    labels.write_text(json.dumps({"labels": [{
        "packet_id": "positive-p1-1", "human_label": "supports",
        "target_verdict_mapping": "supports",
    }]}))
    paper_source = tmp_path / "papers.jsonl"
    paper_source.write_text(json.dumps({
        "paper_id": "p1", "review_state": {"paper_id": "p1", "paper_text": "Accuracy improves."},
    }) + "\n")
    provider_calls = []

    class FakeGenerator:
        def __init__(self, **kwargs):
            pass

        def generate_many(self, requests):
            provider_calls.extend(requests)
            return []

    monkeypatch.setattr("scripts.p34_judge_runner.ApiReviewGenerator", FakeGenerator)
    report = run_experiment(SimpleNamespace(
        packets=str(packets), labels=[str(labels)], discovery_provenance="",
        paper_source_jsonl=str(paper_source), task_types=["evidence_relation"], packet_ids=[], limit=0,
        discovery_code="M", judge_codes=["P"], repeats=2, run_api=True,
        enforce_capability_gates=False, max_tokens=256, max_workers=1, timeout=10,
        max_retries=0, ledger_path=str(tmp_path / "ledger.json"), checkpoint_batch_size=1,
    ))

    assert report["status"] == "BLOCKED"
    assert report["prompt_blinding_audit"]["status"] == "BLOCKED"
    assert report["labels_withheld_from_prompts"] is False
    assert provider_calls == []
    assert not (tmp_path / "ledger.json").exists()


def test_claim_parser_rejects_wrong_schema_verdict():
    packet = {
        "packet_id": "claim-p1-1",
        "task_type": "claim_faithfulness",
        "paper_id": "p1",
        "claim": {"claim_id": "c1", "claim_text": "A claim"},
        "claim_source_spans": [],
        "searched_section_ids": [],
    }
    _parsed, error = parse_task_verdict(
        '{"verdict":"supports","accepted_evidence_ids":[],"counterevidence_ids":[],"searched_section_ids":[],"confidence":0.9,"rationale":"Wrong schema."}',
        packet,
    )

    assert error == "invalid_verdict"


def test_review_issue_metrics_report_d_leakage_and_ab_recall():
    labels = {
        "n-a": {"source_label": "A", "target_verdict_mapping": "verified"},
        "n-d": {"source_label": "D", "target_verdict_mapping": "rejected"},
    }
    cases = []
    for repeat in (1, 2):
        cases.extend([
            {"group": "M-P", "packet_id": "n-a", "task_type": "review_issue", "valid": True, "verdict": "verified", "repeat": repeat},
            {"group": "M-P", "packet_id": "n-d", "task_type": "review_issue", "valid": True, "verdict": "verified", "repeat": repeat},
        ])

    metrics = score_cases(cases, labels, repeats=2)["M-P"]

    assert metrics["test_retest_agreement"] == 1.0
    assert metrics["review_issue_ab_verified_recall"] == 1.0
    assert metrics["review_issue_d_verified_leakage_count"] == 1
    assert metrics["review_issue_verified_precision"] == 0.5


def test_review_issue_parser_rejects_verified_when_counterevidence_resolves_issue():
    packet = {
        "packet_id": "n1",
        "task_type": "review_issue",
        "paper_id": "p1",
        "issue_hypothesis": {"hypothesis": "The paper lacks an ablation."},
        "retrieved_evidence": [{"evidence_id": "e1", "section_id": "s1", "quote": "Ablation study", "source_span_start": 0, "source_span_end": 14}],
        "searched_section_ids": ["s1"],
        "counterevidence_candidates": [],
    }
    _parsed, error = parse_task_verdict(
        '{"verdict":"verified","defect_relation":"established","paper_anchor_valid":true,"counterevidence_resolves_issue":true,"required_evidence_satisfaction":"complete","counterevidence_directness":"direct","review_concern_remains":false,"paper_internal_verifiability":"yes","accepted_evidence_ids":[],"counterevidence_ids":["e1"],"searched_section_ids":["s1"],"confidence":0.9,"rationale":"An ablation exists.","supplemental_retrieval_request":""}',
        packet,
    )

    assert error == "inconsistent_verified_verdict"


def test_review_issue_parser_accepts_assertion_only_efficiency_gap_as_verified():
    packet = {
        "packet_id": "n2",
        "task_type": "review_issue",
        "paper_id": "p1",
        "issue_hypothesis": {"hypothesis": "The paper claims efficiency without runtime measurements."},
        "retrieved_evidence": [{"evidence_id": "e1", "section_id": "s1", "quote": "Our method is efficient.", "source_span_start": 0, "source_span_end": 24}],
        "searched_section_ids": ["s1"],
        "counterevidence_candidates": [],
    }
    parsed, error = parse_task_verdict(
        '{"verdict":"verified","defect_relation":"established","paper_anchor_valid":true,"counterevidence_resolves_issue":false,"required_evidence_satisfaction":"absent","counterevidence_directness":"none","review_concern_remains":true,"paper_internal_verifiability":"yes","accepted_evidence_ids":["e1"],"counterevidence_ids":[],"searched_section_ids":["s1"],"confidence":0.9,"rationale":"The paper repeats an efficiency assertion but reports no measurements.","supplemental_retrieval_request":""}',
        packet,
    )

    assert error == ""
    assert parsed["verdict"] == "verified"


def test_run_experiment_resumes_initial_and_repeat_calls_from_ledger(monkeypatch, tmp_path):
    packet = {
        "packet_id": "positive-p1-1",
        "paper_id": "p1",
        "task_type": "evidence_relation",
        "claim": {"claim_id": "c1", "claim_text": "Accuracy improves."},
        "candidate_evidence": {
            "evidence_id": "e1", "quote": "Accuracy improves by 12.4%.",
            "source_span_start": 0, "source_span_end": 27, "section_id": "s1",
        },
        "searched_section_ids": ["s1"],
        "counterevidence_candidates": [],
    }
    packets = tmp_path / "packets.jsonl"
    packets.write_text(json.dumps(packet) + "\n")
    labels = tmp_path / "labels.json"
    labels.write_text(json.dumps({"labels": [{
        "packet_id": "positive-p1-1", "paper_id": "p1", "task_type": "evidence_relation",
        "human_label": "supports", "target_verdict_mapping": "supports",
        "label_contract_version": "p34_label_contract_v1",
    }]}))
    paper_source = tmp_path / "papers.jsonl"
    paper_source.write_text(json.dumps({"paper_id": "p1", "review_state": {"paper_id": "p1", "paper_text": "Accuracy improves by 12.4%."}}) + "\n")
    instances = []

    class FakeGenerator:
        def __init__(self, **kwargs):
            self.calls = []
            instances.append(self)

        def generate_many(self, requests):
            self.calls.append(list(requests))
            return [
                '{"verdict":"supports","accepted_evidence_ids":["e1"],"counterevidence_ids":[],"searched_section_ids":["s1"],"confidence":0.9,"rationale":"Direct support.","supplemental_retrieval_request":""}'
                for _ in requests
            ]

    monkeypatch.setattr("scripts.p34_judge_runner.ApiReviewGenerator", FakeGenerator)
    args = SimpleNamespace(
        packets=str(packets), labels=[str(labels)], discovery_provenance="",
        paper_source_jsonl=str(paper_source), task_types=["evidence_relation"], packet_ids=[], limit=0,
        discovery_code="M", judge_codes=["P"], repeats=2, run_api=True,
        enforce_capability_gates=False, max_tokens=2048, max_workers=2, timeout=30,
        max_retries=0, ledger_path=str(tmp_path / "ledger.json"), checkpoint_batch_size=1,
    )

    first = run_experiment(args)
    second = run_experiment(args)

    assert first["initial_valid_count"] == 1
    assert first["final_valid_count"] == 2
    assert first["request_ledger_api_request_count"] == 3
    assert second["request_ledger_cache_hit_count"] == 3
    assert second["request_ledger_api_request_count"] == 0
    assert sum(len(instance.calls) for instance in instances[1:]) == 0


def test_review_issue_parser_rejects_external_only_verified_defect():
    packet = {
        "packet_id": "n3",
        "task_type": "review_issue",
        "paper_id": "p1",
        "issue_hypothesis": {"hypothesis": "The protocol is not a community standard."},
        "retrieved_evidence": [],
        "searched_section_ids": [],
        "counterevidence_candidates": [],
    }
    _parsed, error = parse_task_verdict(
        '{"verdict":"verified","defect_relation":"established","paper_anchor_valid":true,"counterevidence_resolves_issue":false,"required_evidence_satisfaction":"absent","counterevidence_directness":"none","review_concern_remains":true,"paper_internal_verifiability":"no","accepted_evidence_ids":[],"counterevidence_ids":[],"searched_section_ids":[],"confidence":0.8,"rationale":"External knowledge is required.","supplemental_retrieval_request":""}',
        packet,
    )

    assert error == "inconsistent_verified_verdict"


def test_review_issue_packets_require_matching_discovery_provenance():
    packets = [
        {"packet_id": "m-1", "task_type": "review_issue"},
        {"packet_id": "p-1", "task_type": "review_issue"},
        {"packet_id": "positive-1", "task_type": "evidence_relation"},
    ]
    provenance = {
        "m-1": {"packet_id": "m-1", "discovery_codes": ["M"]},
        "p-1": {"packet_id": "p-1", "discovery_codes": ["P"]},
    }

    selected_m, issues_m = _apply_discovery_provenance_filter(packets, "M", provenance)
    selected_p, issues_p = _apply_discovery_provenance_filter(packets, "P", provenance)
    blocked, issues_missing = _apply_discovery_provenance_filter(packets, "P", {})

    assert {item["packet_id"] for item in selected_m} == {"m-1", "positive-1"}
    assert {item["packet_id"] for item in selected_p} == {"p-1", "positive-1"}
    assert issues_m == issues_p == []
    assert {item["packet_id"] for item in blocked} == {"positive-1"}
    assert issues_missing == ["review_issue_discovery_provenance_missing"]


def test_classification_metrics_reports_macro_f1_and_confusion():
    metrics = _classification_metrics([
        {"target": "verified", "verdict": "verified"},
        {"target": "verified", "verdict": "uncertain"},
        {"target": "rejected", "verdict": "rejected"},
    ])

    assert metrics["accuracy"] == 2 / 3
    assert metrics["classes"] == ["rejected", "verified"]
    assert metrics["confusion"]["verified"] == {"verified": 1, "uncertain": 1}
    assert 0.0 < metrics["macro_f1"] < 1.0
