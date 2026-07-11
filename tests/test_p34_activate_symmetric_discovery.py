import hashlib
import json

from scripts.p34_activate_symmetric_discovery import _canonical_bytes, activate, validate_source


def _write_source(prefix, status="PASS_GENERATION"):
    packets = []
    provenance = []
    labels = []
    cases = []
    for paper_index in range(20):
        paper_id = f"p{paper_index + 1}"
        for code in ("M", "P"):
            packet_id = f"discovery-{paper_id}-{code.lower()}"
            packets.append({"packet_id": packet_id, "paper_id": paper_id, "task_type": "review_issue"})
            provenance.append({"packet_id": packet_id, "paper_id": paper_id, "discovery_codes": [code]})
            labels.append({"packet_id": packet_id, "paper_id": paper_id, "task_type": "review_issue", "allowed_labels": ["A", "B", "C", "D"]})
            cases.append({"paper_id": paper_id, "discovery_code": code, "valid": True, "candidate_count": 1})
    packet_bytes = b"".join(_canonical_bytes(packet) for packet in packets)
    manifest = {
        "status": status,
        "paper_count": 20 if status == "PASS_GENERATION" else 1,
        "model_codes": ["M", "P"],
        "candidate_counts_by_code": {"M": 20, "P": 20},
        "paper_coverage_by_code": {"M": 20, "P": 20},
        "prompt_identity_symmetric": True,
        "generator_identity_absent_from_packets": True,
        "invalid_span_packet_count": 0,
        "packets_sha256": hashlib.sha256(packet_bytes).hexdigest(),
        "provenance_sha256": hashlib.sha256(_canonical_bytes(provenance)).hexdigest(),
    }
    (prefix.parent / f"{prefix.name}_PACKETS.jsonl").write_bytes(packet_bytes)
    (prefix.parent / f"{prefix.name}_DISCOVERY_PROVENANCE.json").write_text(json.dumps({"items": provenance}))
    (prefix.parent / f"{prefix.name}_MANIFEST.json").write_text(json.dumps(manifest))
    (prefix.parent / f"{prefix.name}_MANIFEST.md").write_text("manifest\n")
    (prefix.parent / f"{prefix.name}_CASES.json").write_text(json.dumps({"cases": cases}))
    (prefix.parent / f"{prefix.name}_HUMAN_AUDIT_TEMPLATE.json").write_text(json.dumps({"labels": labels}))


def test_activation_validates_and_atomically_copies_ready_artifacts(tmp_path):
    source, active = tmp_path / "source", tmp_path / "active"
    _write_source(source)

    report = activate(source, active)

    assert report["status"] == "ACTIVE_READY"
    assert report["activated"] is True
    assert report["validation"]["discovery_membership_counts"] == {"M": 20, "P": 20}
    assert report["validation"]["valid_candidate_paper_coverage_by_code"] == {"M": 20, "P": 20}
    assert (tmp_path / "active_PACKETS.jsonl").read_bytes() == (tmp_path / "source_PACKETS.jsonl").read_bytes()


def test_activation_blocks_provenance_or_template_mismatch(tmp_path):
    source = tmp_path / "source"
    _write_source(source)
    (tmp_path / "source_HUMAN_AUDIT_TEMPLATE.json").write_text(json.dumps({"labels": []}))

    report = activate(source, tmp_path / "active")

    assert report["status"] == "BLOCKED"
    assert report["activated"] is False
    assert "packet_label_template_id_mismatch" in report["blocking_issues"]
    assert not (tmp_path / "active_PACKETS.jsonl").exists()


def test_nonpass_source_requires_explicit_bootstrap_mode(tmp_path):
    source = tmp_path / "source"
    _write_source(source, status="BLOCKED")

    blocked = validate_source(source)
    bootstrap = activate(source, tmp_path / "active", allow_blocked_bootstrap=True)

    assert blocked["status"] == "BLOCKED"
    assert bootstrap["status"] == "ACTIVE_BLOCKED_BOOTSTRAP"
    assert bootstrap["activated"] is True


def test_activation_blocks_when_one_model_covers_only_19_papers(tmp_path):
    source = tmp_path / "source"
    _write_source(source)
    cases_path = tmp_path / "source_CASES.json"
    cases = json.loads(cases_path.read_text())
    cases["cases"] = [
        item for item in cases["cases"]
        if not (item["paper_id"] == "p20" and item["discovery_code"] == "M")
    ]
    cases_path.write_text(json.dumps(cases))

    report = activate(source, tmp_path / "active")

    assert report["status"] == "BLOCKED"
    assert "case_count_not_40:39" in report["blocking_issues"]
    assert "valid_candidate_paper_coverage_M_not_20:19" in report["blocking_issues"]
