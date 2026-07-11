from scripts.p34_annotation_quality_report import build_quality_report


def _audit(task, total, assigned=0, primary_done=0, secondary_done=0, **overrides):
    report = {
        "status": "BLOCKED",
        "primary_validation": {
            "row_count": total,
            "missing_label_packet_ids": [f"missing-{index}" for index in range(total - primary_done)],
        },
        "assigned_secondary_count": assigned,
        "missing_assigned_secondary_packet_ids": [
            f"secondary-{index}" for index in range(assigned - secondary_done)
        ],
        "double_labeled_count": min(primary_done, secondary_done),
        "minimum_double_labeled": assigned,
        "agreement_count": 0,
        "raw_agreement": None,
        "cohen_kappa": None,
        "disagreement_count": 0,
        "unresolved_disagreements": [],
        "signature_audit": {
            role: {"invalid_ids": []} for role in ("primary", "secondary", "resolution")
        },
        "blocking_issues": [],
    }
    report.update(overrides)
    return report


def test_quality_report_exposes_partial_annotation_work_while_discovery_is_blocked():
    report = build_quality_report(
        positive=_audit("evidence_relation", 104, 20),
        claim=_audit("claim_faithfulness", 73, 15),
        negative=_audit("review_issue", 0, 0),
        paper_index={"status": "NEEDS_MANUAL_ANCHORS", "paper_count": 20, "completed_annotation_count": 0},
        assignment={"status": "BLOCKED", "assignment_sha256": "abc"},
        discovery_manifest={"status": "ACTIVE_BLOCKED_BOOTSTRAP", "packet_count": 0},
        annotator_registry={"roles": {}},
        two_by_two={
            "schema_version": "p34_2x2_experiment_v2", "status": "BLOCKED",
            "gate_contract_sha256": "a" * 64,
            "capability_thresholds": {"minimum_cardinality": {"evidence_relation": 80}},
            "preflight": {"missing_label_packet_ids": ["p1"], "invalid_span_packet_ids": []},
        },
        discovery_health={
            "status": "BLOCKED",
            "api_errors": [{"message": "Error code: 402 insufficient_balance"}],
        },
    )

    assert report["status"] == "PARTIAL_ANNOTATION_READY"
    assert "evidence_relation:primary" in report["actionable_now"]
    assert "review_issue:primary" not in report["actionable_now"]
    assert "negative_discovery:ACTIVE_BLOCKED_BOOTSTRAP:0" in report["blocking_issues"]
    assert report["tasks"]["evidence_relation"]["primary_complete"] == 0
    assert report["discovery"]["health_probe_error_codes"] == ["insufficient_balance"]
    assert report["two_by_two"]["schema_version"] == "p34_2x2_experiment_v2"
    assert report["two_by_two"]["gate_contract_sha256"] == "a" * 64
    assert report["two_by_two"]["prompt_blinding_status"] == "NOT_RUN"


def test_quality_report_tracks_progress_agreement_and_integrity_failure():
    positive = _audit(
        "evidence_relation", 4, 2, primary_done=2, secondary_done=2,
        double_labeled_count=2, agreement_count=1, raw_agreement=0.5,
        cohen_kappa=0.0, disagreement_count=1,
        unresolved_disagreements=[{"packet_id": "p2"}],
    )
    positive["signature_audit"]["primary"]["invalid_ids"] = ["p1"]
    report = build_quality_report(
        positive=positive,
        claim=_audit("claim_faithfulness", 1),
        negative=_audit("review_issue", 2, 1),
        paper_index={"status": "NEEDS_MANUAL_ANCHORS", "paper_count": 2, "completed_annotation_count": 1, "signature_audit": {"invalid_ids": []}},
        assignment={"status": "PASS", "assignment_sha256": "abc"},
        discovery_manifest={"status": "PASS_GENERATION", "packet_count": 2, "candidate_counts_by_code": {"M": 1, "P": 1}},
        annotator_registry={"roles": {"primary": {"reviewer_id": "a"}, "secondary": {"reviewer_id": "b"}}},
        two_by_two={"status": "BLOCKED", "preflight": {"missing_label_packet_ids": [], "invalid_span_packet_ids": []}},
    )

    assert report["status"] == "BLOCKED_INTEGRITY"
    assert report["tasks"]["evidence_relation"]["raw_agreement"] == 0.5
    assert report["tasks"]["evidence_relation"]["unresolved_disagreement_count"] == 1
    assert report["tasks"]["evidence_relation"]["invalid_signature_count"] == 1
    assert report["reviewer_registration"] == {"primary": True, "secondary": True, "adjudicator": False}
    assert report["reviewer_credentials"]["primary"] == {
        "registered": True,
        "recovery_enabled": False,
        "credential_generation": 0,
    }
    assert "reviewer_recovery_not_enabled:primary" in report["blocking_issues"]
