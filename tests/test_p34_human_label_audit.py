import json

from scripts.p34_human_label_audit import _cohen_kappa, audit_labels
from scripts.p34_annotation_signature import load_or_create_keypair, sign_row


def _write(path, labels):
    path.write_text(json.dumps({"labels": labels}))


def test_cohen_kappa_perfect_agreement():
    assert _cohen_kappa([("supports", "supports"), ("unrelated", "unrelated")]) == 1.0


def test_label_audit_blocks_unresolved_disagreement(tmp_path):
    primary = tmp_path / "a.json"
    secondary = tmp_path / "b.json"
    _write(primary, [
        {"packet_id": "p1", "paper_id": "paper", "human_label": "supports", "allowed_labels": ["supports", "unrelated"], "human_reason": "Direct."}
    ])
    _write(secondary, [
        {"packet_id": "p1", "paper_id": "paper", "human_label": "unrelated", "allowed_labels": ["supports", "unrelated"], "human_reason": "Mismatch."}
    ])

    report = audit_labels(primary, secondary, None, min_double_labeled=1, require_reason=True)

    assert report["status"] == "BLOCKED"
    assert report["disagreement_count"] == 1
    assert report["unresolved_disagreements"]


def test_empty_primary_and_secondary_labels_are_not_double_agreement(tmp_path):
    primary = tmp_path / "a.json"
    secondary = tmp_path / "b.json"
    base = {"packet_id": "p1", "paper_id": "paper", "allowed_labels": ["supports", "unrelated"]}
    _write(primary, [{**base, "human_label": "", "human_reason": ""}])
    _write(secondary, [{**base, "human_label": "", "human_reason": ""}])

    report = audit_labels(primary, secondary, None, min_double_labeled=0, require_reason=True)

    assert report["status"] == "BLOCKED"
    assert report["frozen_labels"][0]["label_source"] == "primary"


def test_label_audit_freezes_resolved_labels(tmp_path):
    primary = tmp_path / "a.json"
    secondary = tmp_path / "b.json"
    resolution = tmp_path / "r.json"
    base = {"packet_id": "p1", "paper_id": "paper", "allowed_labels": ["supports", "unrelated"]}
    _write(primary, [{**base, "human_label": "supports", "human_reason": "Direct."}])
    _write(secondary, [{**base, "human_label": "unrelated", "human_reason": "Mismatch."}])
    _write(resolution, [{**base, "human_label": "supports", "human_reason": "Adjudicated."}])

    report = audit_labels(primary, secondary, resolution, min_double_labeled=1, require_reason=True)

    assert report["status"] == "PASS"
    assert report["frozen_labels"][0]["human_label"] == "supports"
    assert report["frozen_labels"][0]["label_source"] == "adjudicated_resolution"
    assert report["frozen_labels"][0]["task_type"] == "evidence_relation"
    assert report["frozen_labels"][0]["target_verdict_mapping"] == "supports"
    assert report["frozen_labels"][0]["label_contract_version"] == "p34_label_contract_v1"


def test_label_audit_maps_abcd_review_issue_labels_for_judge_scoring(tmp_path):
    primary = tmp_path / "a.json"
    secondary = tmp_path / "b.json"
    base = {
        "packet_id": "review-1",
        "paper_id": "paper",
        "task_type": "review_issue",
        "allowed_labels": ["A", "B", "C", "D"],
        "human_label": "B",
        "human_reason": "A specific paper-internal absence audit establishes the issue.",
    }
    _write(primary, [base])
    _write(secondary, [base])

    report = audit_labels(primary, secondary, None, min_double_labeled=1, require_reason=True)

    assert report["status"] == "PASS"
    assert report["frozen_labels"][0]["source_label"] == "B"
    assert report["frozen_labels"][0]["target_verdict_mapping"] == "verified"


def test_label_audit_enforces_frozen_secondary_assignment(tmp_path):
    primary = tmp_path / "a.json"
    secondary = tmp_path / "b.json"
    rows = [
        {"packet_id": "p1", "paper_id": "paper", "human_label": "supports", "allowed_labels": ["supports"], "human_reason": "Direct."},
        {"packet_id": "p2", "paper_id": "paper", "human_label": "supports", "allowed_labels": ["supports"], "human_reason": "Direct."},
    ]
    _write(primary, rows)
    _write(secondary, [rows[1]])

    report = audit_labels(
        primary, secondary, None, min_double_labeled=1, require_reason=True,
        required_secondary_ids={"p1"},
    )

    assert report["status"] == "BLOCKED"
    assert report["unexpected_secondary_packet_ids"] == ["p2"]
    assert report["missing_assigned_secondary_packet_ids"] == ["p1"]
    assert "secondary_labels_outside_assignment:1" in report["blocking_issues"]
    assert "assigned_secondary_labels_incomplete:1" in report["blocking_issues"]


def test_label_audit_passes_when_exact_assigned_subset_is_complete(tmp_path):
    primary = tmp_path / "a.json"
    secondary = tmp_path / "b.json"
    rows = [
        {"packet_id": "p1", "paper_id": "paper", "human_label": "supports", "allowed_labels": ["supports"], "human_reason": "Direct."},
        {"packet_id": "p2", "paper_id": "paper", "human_label": "supports", "allowed_labels": ["supports"], "human_reason": "Direct."},
    ]
    _write(primary, rows)
    _write(secondary, [rows[0]])

    report = audit_labels(
        primary, secondary, None, min_double_labeled=1, require_reason=True,
        required_secondary_ids={"p1"},
    )

    assert report["status"] == "PASS"
    assert report["assigned_secondary_count"] == 1
    assert report["double_labeled_count"] == 1


def test_label_audit_requires_distinct_primary_secondary_and_adjudicator_identities(tmp_path):
    primary, secondary, resolution = tmp_path / "a.json", tmp_path / "b.json", tmp_path / "r.json"
    base = {
        "packet_id": "p1", "paper_id": "paper", "task_type": "evidence_relation",
        "allowed_labels": ["supports", "unrelated"],
    }
    _write(primary, [{
        **base, "human_label": "supports", "human_reason": "Direct.",
        "human_reviewer_id": "reviewer-a",
    }])
    _write(secondary, [{
        **base, "human_label": "unrelated", "human_reason": "Mismatch.",
        "human_reviewer_id": "reviewer-a",
    }])
    _write(resolution, [{
        **base, "human_label": "supports", "human_reason": "Resolved.",
        "human_reviewer_id": "reviewer-a",
    }])

    blocked = audit_labels(
        primary, secondary, resolution, 1, True, {"p1"}, "evidence_relation", True
    )
    secondary_rows = json.loads(secondary.read_text())
    secondary_rows["labels"][0]["human_reviewer_id"] = "reviewer-b"
    secondary.write_text(json.dumps(secondary_rows))
    resolution_rows = json.loads(resolution.read_text())
    resolution_rows["labels"][0]["human_reviewer_id"] = "reviewer-c"
    resolution.write_text(json.dumps(resolution_rows))
    passed = audit_labels(
        primary, secondary, resolution, 1, True, {"p1"}, "evidence_relation", True
    )

    assert blocked["status"] == "BLOCKED"
    assert "primary_secondary_reviewer_identity_not_distinct" in blocked["blocking_issues"]
    assert "adjudicator_reviewer_identity_not_distinct" in blocked["blocking_issues"]
    assert passed["status"] == "PASS"
    assert passed["primary_reviewer_ids"] == ["reviewer-a"]
    assert passed["secondary_reviewer_ids"] == ["reviewer-b"]
    assert passed["resolution_reviewer_ids"] == ["reviewer-c"]


def test_label_audit_blocks_direct_file_tampering_when_signatures_are_required(tmp_path):
    primary, secondary = tmp_path / "a.json", tmp_path / "b.json"
    private = tmp_path / "private" / "annotation_ed25519.pem"
    public = tmp_path / "annotation_signing_public.pem"
    load_or_create_keypair(private, public)
    base = {
        "packet_id": "p1", "paper_id": "paper", "task_type": "evidence_relation",
        "allowed_labels": ["supports", "unrelated"], "human_label": "supports",
        "human_reason": "Direct.",
    }
    primary_row = sign_row({
        **base, "annotator_id": "primary", "human_reviewer_id": "reviewer-a",
    }, "label", private)
    secondary_row = sign_row({
        **base, "annotator_id": "secondary", "human_reviewer_id": "reviewer-b",
    }, "label", private)
    _write(primary, [primary_row])
    _write(secondary, [secondary_row])

    passed = audit_labels(
        primary, secondary, None, 1, True, {"p1"}, "evidence_relation", True,
        public, True,
    )
    tampered_value = json.loads(primary.read_text())
    tampered_value["labels"][0]["human_label"] = "unrelated"
    primary.write_text(json.dumps(tampered_value))
    blocked = audit_labels(
        primary, secondary, None, 1, True, {"p1"}, "evidence_relation", True,
        public, True,
    )

    assert passed["status"] == "PASS"
    assert passed["signature_audit"]["primary"]["valid_count"] == 1
    assert blocked["status"] == "BLOCKED"
    assert "invalid_primary_submission_signatures:1" in blocked["blocking_issues"]
