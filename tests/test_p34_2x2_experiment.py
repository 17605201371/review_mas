import json
import re
from types import SimpleNamespace

from scripts.p34_2x2_experiment import (
    aggregate_gate_reports,
    discovery_cluster_metrics,
    paired_macro_f1_bootstrap,
    run_2x2,
    validate_combined_preflight,
)
from scripts.p34_judge_runner import score_cases


def _packets():
    return [
        {
            "packet_id": "positive-1",
            "paper_id": "paper-1",
            "task_type": "evidence_relation",
            "candidate_evidence": {"quote": "Accuracy is 82%.", "source_span_start": 10, "source_span_end": 26},
        },
        {
            "packet_id": "claim-1",
            "paper_id": "paper-1",
            "task_type": "claim_faithfulness",
            "claim_source_spans": [{"quote": "Accuracy is 82%.", "source_span_start": 10, "source_span_end": 26}],
        },
        {
            "packet_id": "review-1",
            "paper_id": "paper-1",
            "task_type": "review_issue",
            "issue_hypothesis": {"issue_type": "statistical_or_reporting_gap"},
            "retrieved_evidence": [{"quote": "Accuracy is 82%.", "source_span_start": 10, "source_span_end": 26}],
        },
    ]


def test_preflight_requires_complete_labels_and_both_discovery_codes():
    paper_texts = {"paper-1": "Results.  Accuracy is 82%. End."}
    labels = {
        "positive-1": {
            "human_label": "supports", "task_type": "evidence_relation",
            "target_verdict_mapping": "supports", "label_contract_version": "p34_label_contract_v1",
        },
        "claim-1": {
            "human_label": "faithful", "task_type": "claim_faithfulness",
            "target_verdict_mapping": "faithful", "label_contract_version": "p34_label_contract_v1",
        },
        "review-1": {
            "source_label": "B", "task_type": "review_issue",
            "target_verdict_mapping": "verified", "label_contract_version": "p34_label_contract_v1",
        },
    }
    provenance = {"review-1": {"packet_id": "review-1", "discovery_codes": ["M", "P"]}}

    report = validate_combined_preflight(_packets(), provenance, labels, paper_texts, [])
    missing_p = validate_combined_preflight(
        _packets(), {"review-1": {"packet_id": "review-1", "discovery_codes": ["M"]}}, labels, paper_texts, []
    )

    assert report["status"] == "BLOCKED"
    assert report["review_issue_discovery_counts"] == {"M": 1, "P": 1}
    assert "positive_evidence_pairs_below_minimum:1/80" in report["blocking_issues"]
    assert "review_issue_ab_labels_below_minimum:1/37" in report["blocking_issues"]
    assert "review_issue_d_labels_below_minimum:0/9" in report["blocking_issues"]
    assert "review_issue_c_labels_below_minimum:0/1" in report["blocking_issues"]
    assert "no_review_issue_packets_for_discovery_code:P" in missing_p["blocking_issues"]


def test_preflight_rejects_implicit_or_wrong_task_label_contracts():
    paper_texts = {"paper-1": "Results.  Accuracy is 82%. End."}
    labels = {
        "positive-1": {"human_label": "supports"},
        "claim-1": {
            "human_label": "faithful", "task_type": "evidence_relation",
            "target_verdict_mapping": "faithful", "label_contract_version": "p34_label_contract_v1",
        },
        "review-1": {
            "source_label": "B", "task_type": "review_issue",
            "target_verdict_mapping": "verified", "label_contract_version": "p34_label_contract_v1",
        },
    }
    provenance = {"review-1": {"packet_id": "review-1", "discovery_codes": ["M", "P"]}}

    report = validate_combined_preflight(_packets(), provenance, labels, paper_texts, [])

    assert report["status"] == "BLOCKED"
    assert set(report["invalid_label_contract_packet_ids"]) == {"positive-1", "claim-1"}
    assert "invalid_label_contracts:2" in report["blocking_issues"]


def test_preflight_rejects_duplicate_and_orphan_label_rows():
    paper_texts = {"paper-1": "Results.  Accuracy is 82%. End."}
    labels = {
        "positive-1": {
            "human_label": "supports", "task_type": "evidence_relation",
            "target_verdict_mapping": "supports", "label_contract_version": "p34_label_contract_v1",
        },
        "claim-1": {
            "human_label": "faithful", "task_type": "claim_faithfulness",
            "target_verdict_mapping": "faithful", "label_contract_version": "p34_label_contract_v1",
        },
        "review-1": {
            "source_label": "B", "task_type": "review_issue",
            "target_verdict_mapping": "verified", "label_contract_version": "p34_label_contract_v1",
        },
        "orphan-1": {
            "human_label": "supports", "task_type": "evidence_relation",
            "target_verdict_mapping": "supports", "label_contract_version": "p34_label_contract_v1",
        },
    }
    provenance = {"review-1": {"packet_id": "review-1", "discovery_codes": ["M", "P"]}}
    diagnostics = {
        "row_count": 5,
        "duplicates": [{
            "packet_id": "positive-1", "first_source": "a.json",
            "duplicate_source": "b.json", "identical": False,
        }],
    }

    report = validate_combined_preflight(_packets(), provenance, labels, paper_texts, [], diagnostics)

    assert report["status"] == "BLOCKED"
    assert report["orphan_label_packet_ids"] == ["orphan-1"]
    assert report["duplicate_label_rows"][0]["packet_id"] == "positive-1"
    assert "duplicate_label_packet_ids:1" in report["blocking_issues"]
    assert "orphan_label_packet_ids:1" in report["blocking_issues"]


def test_discovery_metrics_use_neutral_cluster_membership():
    labels = {"review-1": {"source_label": "B"}}
    provenance = {"review-1": {"packet_id": "review-1", "discovery_codes": ["M", "P"]}}

    metrics = discovery_cluster_metrics(_packets(), provenance, labels)

    assert metrics["shared_cross_model_cluster_count"] == 1
    assert metrics["by_discovery_code"]["M"]["valid_cluster_count"] == 1
    assert metrics["by_discovery_code"]["P"]["adjudicated_precision_ab_over_abd"] == 1.0


def test_aggregate_gate_reports_computes_primary_cross_model_gain():
    common = {
        "schema_success_rate": 1.0,
        "test_retest_agreement": 1.0,
        "review_issue_verified_precision": 0.9,
        "review_issue_ab_verified_count": 34,
        "review_issue_ab_verified_recall": 0.9,
        "review_issue_d_verified_leakage_count": 0,
        "review_issue_abd_adjudication_coverage": 0.9,
        "evidence_relation_accepted_quote_span_locatability": 1.0,
    }
    groups = {
        "M-M": {**common, "task_classification": {"review_issue": {"macro_f1": 0.80}}},
        "M-P": {
            **common,
            "task_classification": {
                "review_issue": {"macro_f1": 0.90},
                "evidence_relation": {"accuracy": 0.90},
            },
        },
        "P-P": {**common, "task_classification": {"review_issue": {"macro_f1": 0.88}}},
        "P-M": {**common, "task_classification": {"review_issue": {"macro_f1": 0.78}}},
    }

    report = aggregate_gate_reports({"all": {"metrics": groups, "blocking_issues": []}}, {"blocking_issues": []})

    assert report["status"] == "PASS"
    assert report["review_issue_macro_f1_comparison"]["M-P_minus_M-M"] == 0.09999999999999998


def test_aggregate_gate_rejects_high_rates_with_low_absolute_recall_and_unlocatable_positive_evidence():
    common = {
        "schema_success_rate": 1.0,
        "test_retest_agreement": 1.0,
        "review_issue_verified_precision": 1.0,
        "review_issue_ab_verified_count": 1,
        "review_issue_ab_verified_recall": 1.0,
        "review_issue_d_verified_leakage_count": 0,
        "review_issue_abd_adjudication_coverage": 1.0,
        "evidence_relation_accepted_quote_span_locatability": 0.5,
    }
    groups = {
        "M-M": {**common, "task_classification": {"review_issue": {"macro_f1": 0.0}}},
        "M-P": {**common, "task_classification": {
            "review_issue": {"macro_f1": 1.0}, "evidence_relation": {"accuracy": 1.0},
        }},
        "P-P": {**common, "task_classification": {"review_issue": {"macro_f1": 1.0}}},
        "P-M": {**common, "task_classification": {"review_issue": {"macro_f1": 0.0}}},
    }

    report = aggregate_gate_reports({"all": {"metrics": groups, "blocking_issues": []}}, {"blocking_issues": []})

    assert report["status"] == "BLOCKED"
    assert "m_p_ab_verified_count_below_30:1" in report["blocking_issues"]
    assert "m_p_positive_accepted_span_locatability_below_1_0:0.5" in report["blocking_issues"]


def test_aggregate_gate_requires_paired_bootstrap_sample_size_and_all_review_classes():
    common = {
        "schema_success_rate": 1.0,
        "test_retest_agreement": 1.0,
        "review_issue_verified_precision": 1.0,
        "review_issue_ab_verified_count": 30,
        "review_issue_ab_verified_recall": 1.0,
        "review_issue_d_verified_leakage_count": 0,
        "review_issue_abd_adjudication_coverage": 1.0,
        "evidence_relation_accepted_quote_span_locatability": 1.0,
    }
    groups = {
        "M-M": {**common, "task_classification": {"review_issue": {"macro_f1": 0.0}}},
        "M-P": {**common, "task_classification": {
            "review_issue": {"macro_f1": 1.0}, "evidence_relation": {"accuracy": 1.0},
        }},
        "P-P": {**common, "task_classification": {"review_issue": {"macro_f1": 1.0}}},
        "P-M": {**common, "task_classification": {"review_issue": {"macro_f1": 0.0}}},
    }
    labels = {"review-1": {"source_label": "B", "target_verdict_mapping": "verified"}}
    final_cases = []
    for repeat in (1, 2):
        for group, verdict in (("M-M", "rejected"), ("M-P", "verified")):
            final_cases.append({
                "group": group, "packet_id": "review-1", "task_type": "review_issue",
                "repeat": repeat, "valid": True, "verdict": verdict,
            })

    report = aggregate_gate_reports(
        {"all": {"metrics": groups, "blocking_issues": [], "repeat_count": 2, "final_cases": final_cases}},
        {"blocking_issues": []}, labels=labels, bootstrap_samples=50,
    )

    assert report["status"] == "BLOCKED"
    assert "m_p_paired_bootstrap_packets_below_minimum:1/30" in report["blocking_issues"]
    assert "m_p_paired_bootstrap_missing_classes:rejected,uncertain" in report["blocking_issues"]


def test_score_cases_uses_all_preregistered_gold_as_recall_and_coverage_denominators():
    labels = {}
    cases = []
    for index in range(37):
        packet_id = f"ab-{index}"
        labels[packet_id] = {"source_label": "B", "target_verdict_mapping": "verified"}
        verdicts = ["verified", "verified"] if index < 30 else ["verified", "rejected"]
        for repeat, verdict in enumerate(verdicts, start=1):
            cases.append({
                "group": "M-P", "packet_id": packet_id, "task_type": "review_issue",
                "repeat": repeat, "valid": True, "verdict": verdict, "parsed": {},
            })
    for index in range(9):
        packet_id = f"d-{index}"
        labels[packet_id] = {"source_label": "D", "target_verdict_mapping": "rejected"}
        for repeat in (1, 2):
            cases.append({
                "group": "M-P", "packet_id": packet_id, "task_type": "review_issue",
                "repeat": repeat, "valid": True, "verdict": "rejected", "parsed": {},
            })
    labels["c-1"] = {"source_label": "C", "target_verdict_mapping": "uncertain"}
    for repeat in (1, 2):
        cases.append({
            "group": "M-P", "packet_id": "c-1", "task_type": "review_issue",
            "repeat": repeat, "valid": True, "verdict": "verified", "parsed": {},
        })

    metrics = score_cases(cases, labels, repeats=2)["M-P"]

    assert metrics["review_issue_ab_label_count"] == 37
    assert metrics["review_issue_ab_verified_count"] == 30
    assert metrics["review_issue_ab_verified_recall"] == 30 / 37
    assert metrics["review_issue_abd_adjudication_coverage"] == 39 / 46
    assert metrics["review_issue_verified_precision"] == 30 / 31
    assert metrics["review_issue_c_to_uncertain_rate"] == 0.0


def test_score_cases_requires_accepted_evidence_for_decisive_positive_locatability():
    labels = {
        "positive-a": {"target_verdict_mapping": "supports"},
        "positive-b": {"target_verdict_mapping": "supports"},
    }
    cases = []
    for packet_id, accepted in (("positive-a", ["e1"]), ("positive-b", [])):
        for repeat in (1, 2):
            cases.append({
                "group": "M-P", "packet_id": packet_id, "task_type": "evidence_relation",
                "repeat": repeat, "valid": True, "verdict": "supports",
                "parsed": {"accepted_evidence_ids": accepted},
            })

    metrics = score_cases(cases, labels, repeats=2)["M-P"]

    assert metrics["evidence_relation_decisive_count"] == 2
    assert metrics["evidence_relation_accepted_quote_span_locatable_count"] == 1
    assert metrics["evidence_relation_accepted_quote_span_locatability"] == 0.5


def test_paired_bootstrap_uses_same_stable_packets_for_self_and_cross_judges():
    labels = {}
    final_cases = []
    for index in range(20):
        packet_id = f"review-{index}"
        target = "verified" if index < 10 else "rejected"
        labels[packet_id] = {"target_verdict_mapping": target, "source_label": "B" if target == "verified" else "D"}
        self_verdict = "rejected" if target == "verified" else "verified"
        for repeat in (1, 2):
            final_cases.extend([
                {
                    "group": "M-M", "packet_id": packet_id, "task_type": "review_issue",
                    "repeat": repeat, "valid": True, "verdict": self_verdict,
                },
                {
                    "group": "M-P", "packet_id": packet_id, "task_type": "review_issue",
                    "repeat": repeat, "valid": True, "verdict": target,
                },
            ])
    reports = {"M": {"repeat_count": 2, "final_cases": final_cases}}

    result = paired_macro_f1_bootstrap(
        reports, labels, self_group="M-M", cross_group="M-P", samples=400, seed=7
    )

    assert result["paired_packet_count"] == 20
    assert result["difference"] == 1.0
    assert result["ci95_low"] > 0.0


def test_full_2x2_orchestration_runs_all_groups_and_resumes_from_shared_ledger(monkeypatch, tmp_path):
    paper_text = "Results. Accuracy is 82%. The paper reports complete evaluation details. End."
    quote = "Accuracy is 82%."
    start = paper_text.index(quote)
    end = start + len(quote)
    source = {
        "evidence_id": "e1", "source_id": "e1", "section_id": "s1",
        "section_type": "results", "quote": quote,
        "source_span_start": start, "source_span_end": end,
    }
    base_packets = [
        *[
            {
                "packet_id": f"positive-{index}", "paper_id": "paper-1", "task_type": "evidence_relation",
                "claim": {"claim_text": "Accuracy is 82%."}, "candidate_evidence": dict(source),
                "counterevidence_candidates": [], "searched_section_ids": ["s1"],
            }
            for index in range(1, 81)
        ],
        {
            "packet_id": "claim-1", "paper_id": "paper-1", "task_type": "claim_faithfulness",
            "claim": {"claim_text": "Accuracy is 82%."}, "claim_source_spans": [dict(source)],
            "searched_section_ids": ["s1"],
        },
    ]
    review_targets = {
        **{f"review-ab-{index}": ("A" if index == 1 else "B", "verified") for index in range(1, 38)},
        **{f"review-d-{index}": ("D", "rejected") for index in range(1, 10)},
        **{f"review-c-{index}": ("C", "uncertain") for index in range(1, 15)},
    }
    discovery_packets = [
        {
            "packet_id": packet_id, "paper_id": "paper-1", "task_type": "review_issue",
            "claim": {"claim_text": "Accuracy is 82%."},
            "issue_hypothesis": {
                "hypothesis": f"Synthetic auditable issue {packet_id}",
                "issue_type": "statistical_or_reporting_gap",
            },
            "verification_contract": {
                "alleged_defect": f"Synthetic auditable issue {packet_id}",
                "required_resolution_evidence": "Direct paper evidence.",
                "falsification_query": "evaluation details",
            },
            "retrieved_evidence": [dict(source)], "counterevidence_candidates": [],
            "searched_section_ids": ["s1"],
        }
        for packet_id in review_targets
    ]
    labels = [
        *[
            {
                "packet_id": f"positive-{index}", "paper_id": "paper-1", "task_type": "evidence_relation",
                "human_label": "supports", "target_verdict_mapping": "supports",
                "label_contract_version": "p34_label_contract_v1",
            }
            for index in range(1, 81)
        ],
        {
            "packet_id": "claim-1", "paper_id": "paper-1", "task_type": "claim_faithfulness",
            "human_label": "faithful", "target_verdict_mapping": "faithful",
            "label_contract_version": "p34_label_contract_v1",
        },
        *[
            {
                "packet_id": packet_id, "paper_id": "paper-1", "task_type": "review_issue",
                "human_label": source_label, "source_label": source_label,
                "target_verdict_mapping": target, "label_contract_version": "p34_label_contract_v1",
            }
            for packet_id, (source_label, target) in review_targets.items()
        ],
    ]
    base_path = tmp_path / "base.jsonl"
    discovery_path = tmp_path / "discovery.jsonl"
    provenance_path = tmp_path / "provenance.json"
    labels_path = tmp_path / "labels.json"
    paper_path = tmp_path / "papers.jsonl"
    base_path.write_text("".join(json.dumps(item) + "\n" for item in base_packets))
    discovery_path.write_text("".join(json.dumps(item) + "\n" for item in discovery_packets))
    provenance_path.write_text(json.dumps({"items": [
        {"packet_id": packet_id, "paper_id": "paper-1", "discovery_codes": ["M", "P"]}
        for packet_id in review_targets
    ]}))
    labels_path.write_text(json.dumps({"labels": labels}))
    paper_path.write_text(json.dumps({
        "paper_id": "paper-1", "review_state": {"paper_id": "paper-1", "paper_text": paper_text},
    }) + "\n")

    instances = []

    class FakeGenerator:
        def __init__(self, model, **kwargs):
            self.model = model
            self.calls = []
            instances.append(self)

        def generate_many(self, requests):
            self.calls.extend(requests)
            results = []
            for _title, prompt in requests:
                packet_id = re.search(r'"packet_id": "([^"]+)"', prompt).group(1)
                task_type = re.search(r'"task_type": "([^"]+)"', prompt).group(1)
                if task_type == "evidence_relation":
                    verdict = "supports"
                elif task_type == "claim_faithfulness":
                    verdict = "faithful"
                else:
                    target = review_targets[packet_id][1]
                    is_pro = "pro" in self.model
                    verdict = target if is_pro else ("rejected" if target == "verified" else "verified")
                payload = {
                    "verdict": verdict,
                    "accepted_evidence_ids": ["e1"] if task_type != "review_issue" or verdict == "verified" else [],
                    "counterevidence_ids": ["e1"] if task_type == "review_issue" and verdict == "rejected" else [],
                    "searched_section_ids": ["s1"], "confidence": 0.95,
                    "rationale": "Synthetic deterministic Judge response.",
                    "supplemental_retrieval_request": "",
                }
                if task_type == "review_issue":
                    relation = "established" if verdict == "verified" else "refuted" if verdict == "rejected" else "insufficient"
                    payload.update({
                        "defect_relation": relation,
                        "paper_anchor_valid": True,
                        "counterevidence_resolves_issue": verdict == "rejected",
                        "required_evidence_satisfaction": "absent" if verdict == "verified" else "complete" if verdict == "rejected" else "partial",
                        "counterevidence_directness": "direct" if verdict == "rejected" else "none",
                        "review_concern_remains": verdict != "rejected",
                        "paper_internal_verifiability": "yes" if verdict != "uncertain" else "partial",
                    })
                results.append(json.dumps(payload))
            return results

    monkeypatch.setattr("scripts.p34_judge_runner.ApiReviewGenerator", FakeGenerator)
    args = SimpleNamespace(
        base_packets=str(base_path), discovery_packets=str(discovery_path),
        discovery_provenance=str(provenance_path), labels=[str(labels_path)],
        paper_source_jsonl=str(paper_path), repeats=2, bootstrap_samples=200,
        run_api=True, max_tokens=512, max_workers=4, timeout=30.0, max_retries=0,
        ledger_path=str(tmp_path / "ledger.json"), checkpoint_batch_size=3,
        output_prefix=str(tmp_path / "full"),
    )

    first = run_2x2(args)
    first_call_count = sum(len(instance.calls) for instance in instances)
    instances.clear()
    second = run_2x2(args)
    second_call_count = sum(len(instance.calls) for instance in instances)

    assert first["status"] == "PASS"
    assert first["schema_version"] == "p34_2x2_experiment_v2"
    assert len(first["gate_contract_sha256"]) == 64
    assert first["capability_thresholds"]["minimum_cardinality"]["evidence_relation"] == 80
    assert first["prompt_blinding_status"] == "PASS"
    assert len(first["prompt_blinding_manifest_sha256"]) == 64
    assert {code: item["status"] for code, item in first["prompt_blinding_by_discovery"].items()} == {
        "M": "PASS", "P": "PASS",
    }
    assert first["preflight"]["status"] == "PASS"
    assert set(first["group_metrics"]) == {"M-M", "M-P", "P-M", "P-P"}
    assert first["review_issue_macro_f1_comparison"]["M-P_minus_M-M"] == 1.0
    assert first["preflight"]["task_counts"]["evidence_relation"] == 80
    assert first["preflight"]["review_issue_source_label_counts"] == {"A": 1, "B": 36, "D": 9, "C": 14}
    assert first["request_ledger_api_request_count"] == 1206
    assert first_call_count == 1206
    assert second["status"] == "PASS"
    assert second["request_ledger_cache_hit_count"] == 1206
    assert second["request_ledger_api_request_count"] == 0
    assert second_call_count == 0

    instances.clear()
    args.gate_contract = str(tmp_path / "missing-contract.json")
    missing_contract = run_2x2(args)
    assert missing_contract["status"] == "BLOCKED"
    assert missing_contract["request_ledger_api_request_count"] == 0
    assert missing_contract["prompt_blinding_status"] == "NOT_RUN"
    assert missing_contract["prompt_blinding_manifest_sha256"] == ""
    assert any(item.startswith("gate_contract_invalid:FileNotFoundError") for item in missing_contract["blocking_issues"])
    assert sum(len(instance.calls) for instance in instances) == 0
