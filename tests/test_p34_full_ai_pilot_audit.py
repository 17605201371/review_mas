from scripts.p34_full_ai_pilot_audit import build_paper_payload, calibrate, validate_output


def _payload():
    return {
        "evidence_relation": [{"packet_id": "e1"}],
        "claim_faithfulness": [{"packet_id": "c1"}],
        "review_issue": [{"packet_id": "r1"}],
        "paper_index": {"artifacts": [{"artifact_id": "a1"}]},
    }


def _output():
    return {
        "evidence_relation": [{"packet_id": "e1", "label": "supports", "reason_zh": "理由"}],
        "claim_faithfulness": [{"packet_id": "c1", "label": "faithful", "reason_zh": "理由"}],
        "review_issue": [{"packet_id": "r1", "label": "B", "reason_zh": "理由", "cluster_key": "gap", "canonical_issue_zh": "问题"}],
        "paper_index": {"key_artifact_ids": ["a1"], "missing_section_headings": [], "false_boundary_headings": [], "reason_zh": "理由"},
        "paper_summary_zh": "摘要",
    }


def test_validate_output_requires_exact_ids_labels_and_known_artifacts():
    valid, errors = validate_output(_output(), _payload())
    assert valid is True
    assert errors == []

    broken = _output()
    broken["review_issue"][0]["label"] = "verified"
    valid, errors = validate_output(broken, _payload())
    assert valid is False
    assert "review_issue:invalid_label" in errors

    duplicate = _output()
    duplicate["evidence_relation"].append(dict(duplicate["evidence_relation"][0]))
    valid, errors = validate_output(duplicate, _payload())
    assert valid is False
    assert "evidence_relation:duplicate_id" in errors

    missing_reason = _output()
    missing_reason["claim_faithfulness"][0]["reason_zh"] = ""
    valid, errors = validate_output(missing_reason, _payload())
    assert valid is False
    assert "claim_faithfulness:missing_reason" in errors


def test_calibration_reports_exact_label_agreement():
    pilot = {"tasks": {
        "evidence_relation": {"e1": {"suggested_label": "supports"}},
        "claim_faithfulness": {"c1": {"suggested_label": "overstated"}},
        "review_issue": {"r1": {"suggested_label": "B"}},
    }}
    result = calibrate(_output(), pilot)

    assert result["matched"] == 2
    assert result["total"] == 3
    assert result["agreement"] == 2 / 3


def test_build_paper_payload_indexes_the_paper_text_not_the_paper_id():
    paper_text = "# Method\nWe introduce a structured method.\n# Results\nTable 1 reports accuracy."
    templates = {
        "evidence_relation": {"labels": []},
        "claim_faithfulness": {"labels": []},
        "review_issue": {"labels": []},
        "paper_index": {"cases": [{"paper_id": "paper-1"}]},
    }

    payload = build_paper_payload("paper-1", paper_text, {}, templates)

    headings = {item["heading"] for item in payload["paper_index"]["explicit_sections"]}
    assert {"Method", "Results"}.issubset(headings)
