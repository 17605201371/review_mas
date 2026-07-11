import base64
import hashlib
import io
import json
import re
import zipfile
from pathlib import Path

import pytest

from scripts.p34_annotation_server import AnnotationStore, _build_role_package, _render_portable_bundle


def _store(tmp_path):
    packets = tmp_path / "packets.jsonl"
    packets.write_text("\n".join([
        json.dumps({
            "packet_id": "positive-p1-001",
            "paper_id": "p1",
            "task_type": "evidence_relation",
            "claim": {"claim_text": "Accuracy improves."},
            "candidate_evidence": {"evidence_id": "e1", "quote": "Accuracy improves by 2%."},
        }),
        json.dumps({
            "packet_id": "claim-p1-01",
            "paper_id": "p1",
            "task_type": "claim_faithfulness",
            "claim": {"claim_text": "Accuracy improves."},
            "claim_source_spans": [{"source_id": "s1", "quote": "Accuracy improves by 2%."}],
        }),
    ]) + "\n")
    positive = tmp_path / "positive.json"
    positive.write_text(json.dumps({"labels": [{
        "packet_id": "positive-p1-001",
        "paper_id": "p1",
        "human_label": "",
        "human_reason": "",
        "allowed_labels": ["supports", "unrelated", "uncertain"],
    }]}))
    claims = tmp_path / "claims.json"
    claims.write_text(json.dumps({"labels": [{
        "packet_id": "claim-p1-01",
        "paper_id": "p1",
        "human_label": "",
        "human_reason": "",
        "allowed_labels": ["faithful", "overstated", "uncertain"],
    }]}))
    issues = tmp_path / "issues.json"
    issues.write_text(json.dumps({"labels": [{
        "packet_id": "review-p1-01",
        "paper_id": "p1",
        "task_type": "review_issue",
        "human_label": "",
        "human_reason": "",
        "allowed_labels": ["A", "B", "C", "D"],
    }]}))
    anchors = tmp_path / "anchors.json"
    anchors.write_text(json.dumps({
        "schema_version": "p34_paper_index_human_anchors_v1",
        "dataset_sha256": "abc",
        "cases": [{
            "paper_id": "p1",
            "expected_boundaries": [],
            "key_anchors": [],
            "false_boundaries": [],
            "machine_boundary_suggestions": [{"heading": "Method", "section_type": "method", "source_span_start": 10}],
            "machine_anchor_suggestions": [{"query": "Table 1", "text": "Table 1 accuracy", "source_span_start": 50, "source_span_end": 66}],
            "machine_false_boundary_suggestions": [],
            "human_review_complete": False,
        }],
    }))
    return AnnotationStore(
        packets_path=packets,
        positive_template_path=positive,
        claim_template_path=claims,
        issue_template_path=issues,
        anchors_path=anchors,
        output_dir=tmp_path / "outputs",
        signing_private_key_path=tmp_path / "private" / "annotation_ed25519.pem",
        repo=tmp_path,
    )


def test_label_workspace_persists_primary_and_keeps_secondary_independent(tmp_path):
    store = _store(tmp_path)

    initial = store.label_workspace("evidence_relation", "primary")
    result = store.save_label({
        "task": "evidence_relation",
        "annotator": "primary",
        "packet_id": "positive-p1-001",
        "human_label": "supports",
        "human_reason": "The quote directly states the measured gain.",
    })
    primary = store.label_workspace("evidence_relation", "primary")
    secondary = store.label_workspace("evidence_relation", "secondary")

    assert initial["progress"] == {"completed": 0, "total": 1}
    assert result["completed"] == 1
    assert primary["items"][0]["human_label"] == "supports"
    assert primary["items"][0]["task_type"] == "evidence_relation"
    assert primary["items"][0]["packet"]["candidate_evidence"]["evidence_id"] == "e1"
    assert secondary["items"][0]["human_label"] == ""
    saved = json.loads((tmp_path / "outputs" / "evidence_relation_primary.json").read_text())
    assert saved["labels"][0]["human_reason"] == "The quote directly states the measured gain."


def test_store_initializes_all_audit_inputs_without_overwriting_labels(tmp_path):
    store = _store(tmp_path)
    output_dir = tmp_path / "outputs"

    expected = {
        f"{task}_{annotator}.json"
        for task in ("evidence_relation", "claim_faithfulness", "review_issue")
        for annotator in ("primary", "secondary")
    }
    expected.update({
        "evidence_relation_resolution.json",
        "claim_faithfulness_resolution.json",
        "review_issue_resolution.json",
        "paper_index_anchors_primary.json",
        "paper_index_anchors_secondary.json",
    })
    assert expected.issubset({path.name for path in output_dir.iterdir()})
    assert json.loads((output_dir / "evidence_relation_primary.json").read_text())["labels"][0]["human_label"] == ""

    store.save_label({
        "task": "evidence_relation",
        "annotator": "primary",
        "packet_id": "positive-p1-001",
        "human_label": "supports",
        "human_reason": "Direct support.",
    })
    _store(tmp_path)

    assert json.loads((output_dir / "evidence_relation_primary.json").read_text())["labels"][0]["human_label"] == "supports"


def test_gate_status_and_refresh_accept_blocked_as_expected_state(monkeypatch, tmp_path):
    store = _store(tmp_path)
    report_path = tmp_path / "P34_ANNOTATION_GATE_REFRESH_20260711.json"
    report_path.write_text(json.dumps({
        "status": "BLOCKED",
        "run_api": False,
        "stages": {"two_by_two": "BLOCKED", "lock_verification": "PASS"},
        "counts": {"positive_primary_complete": 0, "positive_total": 1},
        "config_sha256": "abc",
        "blocking_issues": ["two_by_two:BLOCKED"],
    }))

    monkeypatch.setattr("scripts.p34_annotation_server.subprocess.run", lambda *args, **kwargs: type(
        "Completed", (), {"returncode": 1, "stdout": "", "stderr": ""}
    )())

    before = store.gate_status()
    after = store.refresh_gate_status()

    assert before["status"] == "BLOCKED"
    assert before["run_api"] is False
    assert after["refresh_returncode"] == 1
    assert after["refresh_completed"] is True
    assert after["stages"]["lock_verification"] == "PASS"


def test_quality_status_returns_operational_dashboard(tmp_path):
    store = _store(tmp_path)
    report_path = tmp_path / "P34_ANNOTATION_QUALITY_DASHBOARD_20260711.json"
    report_path.write_text(json.dumps({
        "schema_version": "p34_annotation_quality_report_v1",
        "status": "PARTIAL_ANNOTATION_READY",
        "tasks": {"review_issue": {"primary_complete": 0, "primary_total": 0}},
        "paper_index": {"complete": 0, "total": 1},
        "discovery": {"status": "ACTIVE_BLOCKED_BOOTSTRAP"},
        "actionable_now": ["evidence_relation:primary"],
        "blocking_issues": ["negative_discovery:ACTIVE_BLOCKED_BOOTSTRAP:0"],
    }))

    status = store.quality_status()

    assert status["status"] == "PARTIAL_ANNOTATION_READY"
    assert status["actionable_now"] == ["evidence_relation:primary"]
    assert status["report_path"] == str(report_path)


def test_annotator_identity_binding_is_immutable_and_role_distinct(tmp_path):
    store = _store(tmp_path)
    store.require_annotator_identity = True

    primary = store.register_annotator("primary", "reviewer-alpha")
    secondary = store.register_annotator("secondary", "reviewer-beta")
    primary_token = primary["auth_token"]
    secondary_token = secondary["auth_token"]
    primary_recovery = primary["recovery_code"]

    assert primary["status"] == "REGISTERED"
    assert secondary["reviewer_id"] == "reviewer-beta"
    with pytest.raises(ValueError, match="already bound to role primary"):
        store.register_annotator("adjudicator", "reviewer-alpha")
    with pytest.raises(ValueError, match="already bound to another"):
        store.register_annotator("primary", "reviewer-gamma")
    with pytest.raises(ValueError, match="must be registered"):
        store.save_label({
            "task": "evidence_relation", "annotator": "adjudicator",
            "packet_id": "positive-p1-001", "human_label": "supports",
            "human_reason": "Not registered.", "reviewer_id": "reviewer-gamma",
        })
    with pytest.raises(ValueError, match="does not match"):
        store.save_label({
            "task": "evidence_relation", "annotator": "primary",
            "packet_id": "positive-p1-001", "human_label": "supports",
            "human_reason": "Wrong identity.", "reviewer_id": "reviewer-beta",
            "auth_token": secondary_token,
        })
    with pytest.raises(ValueError, match="authentication token is invalid"):
        store.save_label({
            "task": "evidence_relation", "annotator": "primary",
            "packet_id": "positive-p1-001", "human_label": "supports",
            "human_reason": "Wrong token.", "reviewer_id": "reviewer-alpha",
            "auth_token": "not-the-token",
        })

    result = store.save_label({
        "task": "evidence_relation", "annotator": "primary",
        "packet_id": "positive-p1-001", "human_label": "supports",
        "human_reason": "Correct identity.", "reviewer_id": "reviewer-alpha",
        "auth_token": primary_token,
    })
    saved = json.loads((tmp_path / "outputs" / "evidence_relation_primary.json").read_text())

    assert result["completed"] == 1
    assert saved["labels"][0]["human_reviewer_id"] == "reviewer-alpha"
    registry = json.loads((tmp_path / "outputs" / "annotator_registry.json").read_text())
    assert registry["schema_version"] == "p34_annotator_registry_v3"
    assert registry["roles"]["primary"]["reviewer_id"] == "reviewer-alpha"
    assert registry["roles"]["secondary"]["reviewer_id"] == "reviewer-beta"
    assert registry["roles"]["primary"]["token_sha256"] != primary_token
    assert registry["roles"]["primary"]["recovery_code_sha256"] != primary_recovery
    assert primary_token not in json.dumps(registry)
    assert primary_recovery not in json.dumps(registry)


def test_annotator_credentials_verify_rotate_and_single_use_recover(tmp_path):
    store = _store(tmp_path)
    store.require_annotator_identity = True
    first = store.register_annotator("primary", "reviewer-alpha")

    verified = store.verify_annotator("primary", "reviewer-alpha", first["auth_token"])
    assert verified == {
        "status": "VERIFIED",
        "role": "primary",
        "reviewer_id": "reviewer-alpha",
        "credential_generation": 1,
        "recovery_enabled": True,
    }
    with pytest.raises(ValueError, match="recovery code is invalid"):
        store.recover_annotator("primary", "reviewer-alpha", "wrong-recovery")

    rotated = store.rotate_annotator("primary", "reviewer-alpha", first["auth_token"])
    assert rotated["status"] == "ROTATED"
    assert rotated["credential_generation"] == 2
    with pytest.raises(ValueError, match="authentication token is invalid"):
        store.verify_annotator("primary", "reviewer-alpha", first["auth_token"])
    with pytest.raises(ValueError, match="recovery code is invalid"):
        store.recover_annotator("primary", "reviewer-alpha", first["recovery_code"])

    recovered = store.recover_annotator("primary", "reviewer-alpha", rotated["recovery_code"])
    assert recovered["status"] == "RECOVERED"
    assert recovered["credential_generation"] == 3
    with pytest.raises(ValueError, match="authentication token is invalid"):
        store.verify_annotator("primary", "reviewer-alpha", rotated["auth_token"])
    assert store.verify_annotator("primary", "reviewer-alpha", recovered["auth_token"])["status"] == "VERIFIED"

    registry = json.loads((tmp_path / "outputs" / "annotator_registry.json").read_text())
    role = registry["roles"]["primary"]
    assert role["credential_generation"] == 3
    assert role["recovery_count"] == 1
    for secret in (
        first["auth_token"], first["recovery_code"], rotated["auth_token"],
        rotated["recovery_code"], recovered["auth_token"], recovered["recovery_code"],
    ):
        assert secret not in json.dumps(registry)


def test_legacy_v2_registry_can_enable_recovery_by_authenticated_rotation(tmp_path):
    store = _store(tmp_path)
    store.require_annotator_identity = True
    first = store.register_annotator("primary", "reviewer-alpha")
    role = dict(store.annotator_registry["roles"]["primary"])
    role.pop("recovery_code_sha256")
    role.pop("credential_generation")
    role.pop("recovery_count")
    store.annotator_registry = {"schema_version": "p34_annotator_registry_v2", "roles": {"primary": role}}
    (tmp_path / "outputs" / "annotator_registry.json").write_text(json.dumps(store.annotator_registry))

    with pytest.raises(ValueError, match="recovery is not enabled"):
        store.recover_annotator("primary", "reviewer-alpha", first["recovery_code"])
    rotated = store.rotate_annotator("primary", "reviewer-alpha", first["auth_token"])

    assert rotated["credential_generation"] == 1
    assert store.annotator_registry["schema_version"] == "p34_annotator_registry_v3"
    assert store.annotator_registry["roles"]["primary"]["recovery_code_sha256"]


def test_credential_management_is_disabled_in_role_only_compatibility_mode(tmp_path):
    store = _store(tmp_path)
    credential = store.register_annotator("primary", "reviewer-alpha")

    with pytest.raises(ValueError, match="requires the identity gate"):
        store.verify_annotator("primary", "reviewer-alpha", credential["auth_token"])
    with pytest.raises(ValueError, match="requires the identity gate"):
        store.rotate_annotator("primary", "reviewer-alpha", credential["auth_token"])
    with pytest.raises(ValueError, match="requires the identity gate"):
        store.recover_annotator("primary", "reviewer-alpha", credential["recovery_code"])


def test_annotation_exchange_is_role_isolated_hashed_and_importable(tmp_path):
    store = _store(tmp_path)
    store.require_annotator_identity = True
    store.assignment = {
        "assignment_sha256": "assignment-v1",
        "tasks": {
            "evidence_relation": {"secondary_packet_ids": ["positive-p1-001"]},
            "claim_faithfulness": {"secondary_packet_ids": []},
            "review_issue": {"secondary_packet_ids": []},
        },
    }
    primary_token = store.register_annotator("primary", "reviewer-a")["auth_token"]
    secondary_token = store.register_annotator("secondary", "reviewer-b")["auth_token"]
    store.save_label({
        "task": "evidence_relation",
        "annotator": "primary",
        "packet_id": "positive-p1-001",
        "reviewer_id": "reviewer-a",
        "auth_token": primary_token,
        "human_label": "supports",
        "human_reason": "Primary-only reasoning.",
    })

    bundle = store.export_label_bundle("evidence_relation", "secondary", secondary_token)

    assert bundle["reviewer_id"] == "reviewer-b"
    assert bundle["assignment_sha256"] == "assignment-v1"
    assert [item["packet_id"] for item in bundle["items"]] == ["positive-p1-001"]
    assert bundle["labels"] == [{
        "packet_id": "positive-p1-001", "human_label": "", "human_reason": "",
    }]
    assert "primary_label" not in bundle["items"][0]
    assert "Primary-only reasoning." not in json.dumps(bundle)

    portable = _render_portable_bundle(
        Path(__file__).parents[1] / "scripts" / "p34_portable_annotation.html", bundle
    )
    encoded = re.search(r'const bundleBase64 = "([A-Za-z0-9+/=]+)";', portable).group(1)
    embedded = json.loads(base64.b64decode(encoded).decode("utf-8"))
    assert "__P34_BUNDLE_BASE64__" not in portable
    assert embedded["bundle_sha256"] == bundle["bundle_sha256"]
    assert embedded["labels"] == bundle["labels"]
    assert "auth_token" not in embedded
    for forbidden in ("fetch(", "XMLHttpRequest", "WebSocket", "<script src=", "<link href=", "http://", "https://"):
        assert forbidden not in portable
    assert "URL.createObjectURL" in portable
    assert 'id="download"' in portable
    assert len(embedded["items"]) == len(embedded["labels"]) == 1

    bundle["labels"][0].update({
        "human_label": "supports", "human_reason": "Independent secondary judgment.",
    })
    bundle["auth_token"] = secondary_token
    result = store.import_label_bundle(bundle)
    saved = json.loads((tmp_path / "outputs" / "evidence_relation_secondary.json").read_text())

    assert result["imported_count"] == 1
    assert result["completed"] == 1
    assert saved["labels"][0]["human_reviewer_id"] == "reviewer-b"
    assert saved["labels"][0]["human_reason"] == "Independent secondary judgment."


def test_annotation_exchange_rejects_stale_or_malformed_batch_without_partial_save(tmp_path):
    store = _store(tmp_path)
    store.require_annotator_identity = True
    primary_token = store.register_annotator("primary", "reviewer-a")["auth_token"]
    bundle = store.export_label_bundle("evidence_relation", "primary", primary_token)
    bundle["auth_token"] = primary_token
    bundle["labels"][0]["human_label"] = "supports"
    bundle["labels"].append(dict(bundle["labels"][0]))

    with pytest.raises(ValueError, match="malformed or duplicate"):
        store.import_label_bundle(bundle)

    saved = json.loads((tmp_path / "outputs" / "evidence_relation_primary.json").read_text())
    assert saved["labels"][0]["human_label"] == ""

    bundle = store.export_label_bundle("evidence_relation", "primary", primary_token)
    bundle["auth_token"] = primary_token
    bundle["labels"][0]["human_label"] = "supports"
    bundle["bundle_sha256"] = "tampered"
    with pytest.raises(ValueError, match="stale or does not match"):
        store.import_label_bundle(bundle)

    saved = json.loads((tmp_path / "outputs" / "evidence_relation_primary.json").read_text())
    assert saved["labels"][0]["human_label"] == ""


def test_annotation_exchange_rejects_an_older_bundle_after_newer_labels_are_imported(tmp_path):
    store = _store(tmp_path)
    store.require_annotator_identity = True
    primary_token = store.register_annotator("primary", "reviewer-a")["auth_token"]
    older = store.export_label_bundle("evidence_relation", "primary", primary_token)
    older["auth_token"] = primary_token
    newer = json.loads(json.dumps(older))
    newer["labels"][0].update({"human_label": "supports", "human_reason": "New result."})
    store.import_label_bundle(newer)

    older["labels"][0].update({"human_label": "unrelated", "human_reason": "Stale result."})
    with pytest.raises(ValueError, match="stale or does not match"):
        store.import_label_bundle(older)

    saved = json.loads((tmp_path / "outputs" / "evidence_relation_primary.json").read_text())
    assert saved["labels"][0]["human_label"] == "supports"
    assert saved["labels"][0]["human_reason"] == "New result."


def test_paper_index_exchange_validates_exact_spans_and_rejects_stale_bundles(tmp_path):
    store = _store(tmp_path)
    store.require_annotator_identity = True
    token = store.register_annotator("primary", "anchor-reviewer")["auth_token"]
    paper_text = "Method details. Table 1 accuracy is 82%. End."
    store.paper_texts["p1"] = paper_text
    boundary_heading = "Method"
    anchor_text = "Table 1 accuracy"
    anchor_start = paper_text.index(anchor_text)
    bundle = store.export_anchor_bundle("primary", token)

    assert bundle["schema_version"] == "p34_paper_index_exchange_v1"
    assert bundle["items"][0]["paper_text"] == paper_text
    assert "auth_token" not in bundle
    portable = _render_portable_bundle(
        Path(__file__).parents[1] / "scripts" / "p34_portable_paper_index.html", bundle
    )
    encoded = re.search(r'const bundleBase64 = "([A-Za-z0-9+/=]+)";', portable).group(1)
    embedded = json.loads(base64.b64decode(encoded).decode("utf-8"))
    assert embedded["items"][0]["paper_text"] == paper_text
    assert "auth_token" not in embedded
    for forbidden in ("fetch(", "XMLHttpRequest", "WebSocket", "<script src=", "http://", "https://"):
        assert forbidden not in portable

    original = json.loads(json.dumps(bundle))
    bundle["auth_token"] = token
    bundle["cases"][0].update({
        "expected_boundaries": [{
            "heading": boundary_heading, "section_type": "method", "source_span_start": 0,
        }],
        "key_anchors": [{
            "query": "Table 1", "text": anchor_text, "section_types": ["results"],
            "source_span_start": anchor_start, "source_span_end": anchor_start + len(anchor_text),
        }],
        "false_boundaries": [],
        "human_review_complete": True,
        "human_review_notes": "Exact source spans checked.",
    })
    result = store.import_anchor_bundle(bundle)
    saved = json.loads((tmp_path / "outputs" / "paper_index_anchors_primary.json").read_text())

    assert result["imported_count"] == 1
    assert result["completed"] == 1
    assert saved["cases"][0]["human_reviewer_id"] == "anchor-reviewer"
    assert saved["cases"][0]["key_anchors"][0]["text"] == anchor_text

    original["auth_token"] = token
    with pytest.raises(ValueError, match="stale or does not match"):
        store.import_anchor_bundle(original)


def test_paper_index_batch_rejects_invalid_completed_case_before_write(tmp_path):
    store = _store(tmp_path)
    store.require_annotator_identity = True
    token = store.register_annotator("primary", "anchor-reviewer")["auth_token"]
    store.paper_texts["p1"] = "Method details. Table 1 accuracy is 82%. End."
    bundle = store.export_anchor_bundle("primary", token)
    bundle["auth_token"] = token
    bundle["cases"][0].update({
        "expected_boundaries": [{"heading": "Method", "section_type": "method", "source_span_start": 0}],
        "key_anchors": [{
            "query": "Table 1", "text": "wrong text", "source_span_start": 16, "source_span_end": 26,
        }],
        "false_boundaries": [], "human_review_complete": True,
    })

    with pytest.raises(ValueError, match="anchor does not match paper source"):
        store.import_anchor_bundle(bundle)

    saved = json.loads((tmp_path / "outputs" / "paper_index_anchors_primary.json").read_text())
    assert saved["cases"][0]["human_review_complete"] is False


def test_role_package_is_deterministic_manifested_and_contains_no_credentials(tmp_path):
    store = _store(tmp_path)
    store.require_annotator_identity = True
    token = store.register_annotator("primary", "package-reviewer")["auth_token"]
    label_template = Path(__file__).parents[1] / "scripts" / "p34_portable_annotation.html"
    anchor_template = Path(__file__).parents[1] / "scripts" / "p34_portable_paper_index.html"

    first_name, first_bytes, first_manifest = _build_role_package(
        store, "primary", token, label_template, anchor_template
    )
    second_name, second_bytes, second_manifest = _build_role_package(
        store, "primary", token, label_template, anchor_template
    )

    assert first_name == second_name
    assert first_bytes == second_bytes
    assert first_manifest == second_manifest
    assert token.encode() not in first_bytes
    with zipfile.ZipFile(io.BytesIO(first_bytes)) as archive:
        names = archive.namelist()
        manifest = json.loads(archive.read("manifest.json"))
        assert names[0] == "manifest.json"
        assert set(item["task_type"] for item in manifest["files"]) == {
            "claim_faithfulness", "evidence_relation", "paper_index", "review_issue",
        }
        assert manifest["reviewer_id"] == "package-reviewer"
        assert "auth_token" not in json.dumps(manifest)
        for item in manifest["files"]:
            content = archive.read(item["filename"])
            assert item["html_sha256"] == hashlib.sha256(content).hexdigest()


def test_reload_issue_artifacts_preserves_matching_and_archives_orphans(tmp_path):
    store = _store(tmp_path)
    store.save_label({
        "task": "review_issue",
        "annotator": "primary",
        "packet_id": "review-p1-01",
        "human_label": "A",
        "human_reason": "Old discovery label.",
    })
    packets = tmp_path / "active_PACKETS.jsonl"
    template = tmp_path / "active_HUMAN_AUDIT_TEMPLATE.json"
    provenance = tmp_path / "active_DISCOVERY_PROVENANCE.json"
    packets.write_text(json.dumps({
        "packet_id": "discovery-p2-new",
        "paper_id": "p2",
        "task_type": "review_issue",
        "issue_hypothesis": {"hypothesis": "New concern"},
    }) + "\n")
    template.write_text(json.dumps({"labels": [{
        "packet_id": "discovery-p2-new",
        "paper_id": "p2",
        "task_type": "review_issue",
        "human_label": "",
        "human_reason": "",
        "allowed_labels": ["A", "B", "C", "D"],
    }]}))
    provenance.write_text(json.dumps({"items": [{
        "packet_id": "discovery-p2-new",
        "paper_id": "p2",
        "discovery_codes": ["M", "P"],
    }]}))
    store.issue_packets_path = packets
    store.issue_template_path = template
    store.issue_provenance_path = provenance

    result = store.reload_issue_artifacts()
    workspace = store.label_workspace("review_issue", "primary")
    saved = json.loads((tmp_path / "outputs" / "review_issue_primary.json").read_text())

    assert result["status"] == "RELOADED"
    assert result["packet_count"] == 1
    assert result["orphaned_label_counts"]["primary"] == 1
    assert workspace["items"][0]["packet_id"] == "discovery-p2-new"
    assert workspace["items"][0]["packet"]["issue_hypothesis"]["hypothesis"] == "New concern"
    assert saved["labels"][0]["human_label"] == ""
    assert saved["orphaned_labels"][0]["packet_id"] == "review-p1-01"


def test_label_workspace_rejects_invalid_label(tmp_path):
    store = _store(tmp_path)

    with pytest.raises(ValueError, match="not allowed"):
        store.save_label({
            "task": "evidence_relation",
            "annotator": "primary",
            "packet_id": "positive-p1-001",
            "human_label": "verified",
        })


def test_secondary_workspace_and_save_are_restricted_to_frozen_assignment(tmp_path):
    store = _store(tmp_path)
    store.assignment = {"tasks": {"evidence_relation": {"secondary_packet_ids": []}}}

    workspace = store.label_workspace("evidence_relation", "secondary")

    assert workspace["progress"] == {"completed": 0, "total": 0}
    with pytest.raises(ValueError, match="not assigned"):
        store.save_label({
            "task": "evidence_relation",
            "annotator": "secondary",
            "packet_id": "positive-p1-001",
            "human_label": "supports",
            "human_reason": "Attempted convenience sample.",
        })


def test_reload_assignment_rewrites_secondary_files_to_exact_frozen_ids(tmp_path):
    store = _store(tmp_path)
    assignment = tmp_path / "assignment.json"
    assignment.write_text(json.dumps({
        "status": "BLOCKED",
        "assignment_sha256": "abc",
        "tasks": {
            "evidence_relation": {"secondary_packet_ids": ["positive-p1-001"]},
            "claim_faithfulness": {"secondary_packet_ids": []},
            "review_issue": {"secondary_packet_ids": []},
        },
    }))
    store.assignment_path = assignment

    result = store.reload_assignment()
    evidence = json.loads((tmp_path / "outputs" / "evidence_relation_secondary.json").read_text())
    claims = json.loads((tmp_path / "outputs" / "claim_faithfulness_secondary.json").read_text())

    assert result["status"] == "RELOADED"
    assert result["secondary_counts"] == {
        "claim_faithfulness": 0,
        "evidence_relation": 1,
        "review_issue": 0,
    }
    assert [item["packet_id"] for item in evidence["labels"]] == ["positive-p1-001"]
    assert claims["labels"] == []


def test_review_issue_workspace_uses_abcd_labels(tmp_path):
    store = _store(tmp_path)

    workspace = store.label_workspace("review_issue", "primary")

    assert workspace["items"][0]["allowed_labels"] == ["A", "B", "C", "D"]


def test_adjudicator_workspace_only_contains_real_disagreements_and_persists_resolution(tmp_path):
    store = _store(tmp_path)
    common = {"task": "evidence_relation", "packet_id": "positive-p1-001"}
    store.save_label({
        **common,
        "annotator": "primary",
        "human_label": "supports",
        "human_reason": "The quote directly states the gain.",
    })
    store.save_label({
        **common,
        "annotator": "secondary",
        "human_label": "unrelated",
        "human_reason": "The quote does not establish the exact claim scope.",
    })

    workspace = store.label_workspace("evidence_relation", "adjudicator")
    result = store.save_label({
        **common,
        "annotator": "adjudicator",
        "human_label": "supports",
        "human_reason": "The claim and quote share the same method and measured contribution.",
    })
    resolved = store.label_workspace("evidence_relation", "adjudicator")
    resolution_file = json.loads((tmp_path / "outputs" / "evidence_relation_resolution.json").read_text())

    assert workspace["progress"] == {"completed": 0, "total": 1}
    assert workspace["items"][0]["primary_label"] == "supports"
    assert workspace["items"][0]["secondary_label"] == "unrelated"
    assert result["completed"] == 1
    assert resolved["items"][0]["human_label"] == "supports"
    assert resolution_file["labels"][0]["primary_label_for_audit"] == "supports"
    assert resolution_file["labels"][0]["secondary_label_for_audit"] == "unrelated"


def test_anchor_workspace_requires_real_boundary_and_anchor_before_completion(tmp_path):
    store = _store(tmp_path)

    with pytest.raises(ValueError, match="requires at least one boundary and one anchor"):
        store.save_anchor_case({
            "annotator": "primary",
            "paper_id": "p1",
            "expected_boundaries": [],
            "key_anchors": [],
            "false_boundaries": [],
            "human_review_complete": True,
        })

    result = store.save_anchor_case({
        "annotator": "primary",
        "paper_id": "p1",
        "expected_boundaries": [{"heading": "Method", "section_type": "method", "source_span_start": 10, "human_action": "accept"}],
        "key_anchors": [{"query": "Table 1", "text": "Table 1 accuracy", "source_span_start": 50, "source_span_end": 66}],
        "false_boundaries": [],
        "human_review_complete": True,
        "human_review_notes": "Checked against the original paper text.",
    })
    workspace = store.anchor_workspace("primary")
    saved = json.loads((tmp_path / "outputs" / "paper_index_anchors_primary.json").read_text())

    assert result["completed"] == 1
    assert workspace["progress"] == {"completed": 1, "total": 1}
    assert saved["cases"][0]["expected_boundaries"] == [
        {"heading": "Method", "section_type": "method", "source_span_start": 10}
    ]
    assert saved["cases"][0]["human_review_complete"] is True


def test_anchor_completion_rejects_placeholder_or_invalid_span_items(tmp_path):
    store = _store(tmp_path)

    with pytest.raises(ValueError, match="invalid boundary"):
        store.save_anchor_case({
            "annotator": "primary",
            "paper_id": "p1",
            "expected_boundaries": [{"heading": "", "section_type": "method", "source_span_start": 0}],
            "key_anchors": [{"query": "Table 1", "text": "Table 1 accuracy", "source_span_start": 50, "source_span_end": 66}],
            "false_boundaries": [],
            "human_review_complete": True,
        })

    with pytest.raises(ValueError, match="invalid anchor"):
        store.save_anchor_case({
            "annotator": "primary",
            "paper_id": "p1",
            "expected_boundaries": [{"heading": "Method", "section_type": "method", "source_span_start": 10}],
            "key_anchors": [{"query": "Table 1", "text": "", "source_span_start": 66, "source_span_end": 50}],
            "false_boundaries": [],
            "human_review_complete": True,
        })

    with pytest.raises(ValueError, match="invalid false boundary"):
        store.save_anchor_case({
            "annotator": "primary",
            "paper_id": "p1",
            "expected_boundaries": [{"heading": "Method", "section_type": "method", "source_span_start": 10}],
            "key_anchors": [{"query": "Table 1", "text": "Table 1 accuracy", "source_span_start": 50, "source_span_end": 66}],
            "false_boundaries": [{"heading": "References", "source_span_start": 90, "reason": ""}],
            "human_review_complete": True,
        })


def test_anchor_completion_requires_exact_paper_source_spans_when_available(tmp_path):
    store = _store(tmp_path)
    paper = "# Method\nTable 1 accuracy improves."
    store.paper_texts = {"p1": paper}
    quote = "Table 1 accuracy improves."
    start = paper.index(quote)

    with pytest.raises(ValueError, match="anchor does not match"):
        store.save_anchor_case({
            "annotator": "primary",
            "paper_id": "p1",
            "expected_boundaries": [{"heading": "Method", "section_type": "method", "source_span_start": 0}],
            "key_anchors": [{"query": "Table 1", "text": "wrong text", "source_span_start": start, "source_span_end": start + len(quote)}],
            "false_boundaries": [],
            "human_review_complete": True,
        })

    result = store.save_anchor_case({
        "annotator": "primary",
        "paper_id": "p1",
        "expected_boundaries": [{"heading": "Method", "section_type": "method", "source_span_start": 0}],
        "key_anchors": [{"query": "Table 1", "text": quote, "source_span_start": start, "source_span_end": start + len(quote)}],
        "false_boundaries": [],
        "human_review_complete": True,
    })

    assert result["completed"] == 1

def test_anchor_reload_refreshes_machine_suggestions_but_preserves_human_fields(tmp_path):
    store = _store(tmp_path)
    store.save_anchor_case({
        "annotator": "primary",
        "paper_id": "p1",
        "expected_boundaries": [{"heading": "Method", "section_type": "method", "source_span_start": 10}],
        "key_anchors": [{"query": "Table 1", "text": "Table 1 accuracy", "source_span_start": 50, "source_span_end": 66}],
        "false_boundaries": [],
        "human_review_complete": False,
        "human_review_notes": "Human draft survives.",
    })
    store._anchor_rows["p1"] = {
        **store._anchor_rows["p1"],
        "machine_boundary_suggestions": [{"heading": "Updated Method", "section_type": "method", "source_span_start": 12}],
    }

    workspace = store.anchor_workspace("primary")
    item = workspace["items"][0]

    assert item["machine_boundary_suggestions"][0]["heading"] == "Updated Method"
    assert item["expected_boundaries"][0]["heading"] == "Method"
    assert item["human_review_notes"] == "Human draft survives."
