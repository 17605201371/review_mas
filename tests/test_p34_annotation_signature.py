import stat

from scripts.p34_annotation_signature import (
    audit_rows,
    load_or_create_keypair,
    load_public_key,
    sign_row,
    verify_row,
)


def _keys(tmp_path):
    private = tmp_path / "private" / "annotation_ed25519.pem"
    public = tmp_path / "workspace" / "annotation_signing_public.pem"
    info = load_or_create_keypair(private, public)
    return private, public, info


def test_ed25519_keypair_is_stable_and_private_key_is_outside_workspace(tmp_path):
    private, public, first = _keys(tmp_path)
    second = load_or_create_keypair(private, public)

    assert first == second
    assert first["public_key_sha256"] == load_public_key(public)["public_key_sha256"]
    assert stat.S_IMODE(private.stat().st_mode) == 0o600
    assert stat.S_IMODE(private.parent.stat().st_mode) == 0o700
    assert stat.S_IMODE(public.stat().st_mode) == 0o644
    assert private.parent != public.parent


def test_workspace_public_key_cannot_be_silently_replaced_by_another_private_key(tmp_path):
    private, public, _info = _keys(tmp_path)
    other_private = tmp_path / "other" / "annotation_ed25519.pem"
    other_public = tmp_path / "other" / "public.pem"
    load_or_create_keypair(other_private, other_public)

    try:
        load_or_create_keypair(other_private, public)
    except ValueError as exc:
        assert "does not match" in str(exc)
    else:
        raise AssertionError("Expected public/private key mismatch")

    assert load_or_create_keypair(private, public)["public_key_sha256"] == load_public_key(public)["public_key_sha256"]


def test_label_signature_rejects_content_tampering_and_packet_replay(tmp_path):
    private, public, _info = _keys(tmp_path)
    row = sign_row({
        "packet_id": "p1", "paper_id": "paper", "task_type": "evidence_relation",
        "human_label": "supports", "human_reason": "Direct support.",
        "annotator_id": "primary", "human_reviewer_id": "reviewer-a",
    }, "label", private)

    assert verify_row(row, "label", public)
    assert not verify_row({**row, "human_reason": "Changed."}, "label", public)
    assert not verify_row({**row, "packet_id": "p2"}, "label", public)
    assert not verify_row({**row, "annotator_id": "secondary"}, "label", public)


def test_anchor_signature_rejects_span_and_completion_tampering(tmp_path):
    private, public, _info = _keys(tmp_path)
    row = sign_row({
        "paper_id": "paper", "expected_boundaries": [{"heading": "Method", "source_span_start": 10}],
        "key_anchors": [{"text": "Table 1", "source_span_start": 20, "source_span_end": 27}],
        "false_boundaries": [], "human_review_complete": True, "human_review_notes": "Checked.",
        "annotator_id": "primary", "human_reviewer_id": "reviewer-a",
    }, "anchor", private)

    assert verify_row(row, "anchor", public)
    assert not verify_row({**row, "human_review_complete": False}, "anchor", public)
    changed = dict(row)
    changed["key_anchors"] = [{"text": "Table 1", "source_span_start": 21, "source_span_end": 28}]
    assert not verify_row(changed, "anchor", public)


def test_signature_audit_requires_signatures_only_for_submitted_rows(tmp_path):
    private, public, info = _keys(tmp_path)
    signed = sign_row({
        "packet_id": "signed", "human_label": "A", "annotator_id": "primary",
        "human_reviewer_id": "reviewer-a",
    }, "label", private)
    report = audit_rows([signed, {"packet_id": "blank", "human_label": ""}], "label", public)
    tampered = audit_rows([{**signed, "human_label": "D"}], "label", public)

    assert report["status"] == "PASS"
    assert report["public_key_sha256"] == info["public_key_sha256"]
    assert report["submitted_count"] == report["valid_count"] == 1
    assert tampered["status"] == "BLOCKED"
    assert tampered["invalid_ids"] == ["signed"]
