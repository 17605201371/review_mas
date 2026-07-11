import hashlib
import json
from types import SimpleNamespace

from scripts.p34_activate_symmetric_discovery import _canonical_bytes
from scripts import p34_symmetric_discovery_pipeline as pipeline


def _args(tmp_path, run_api):
    for name, task in (("positive.json", "evidence_relation"), ("claim.json", "claim_faithfulness")):
        (tmp_path / name).write_text(json.dumps({"labels": [{
            "packet_id": f"{task}-p1-1", "paper_id": "p1", "task_type": task,
        }]}))
    return SimpleNamespace(
        repo=str(tmp_path), runner_jsonl="runner.jsonl", source_prefix="candidate",
        active_prefix="active", run_api=run_api, reuse_generation=False, limit=0, max_context_chars=12000,
        max_hypotheses=8, max_tokens=2048, max_workers=8, timeout=180.0,
        max_retries=4, pipeline_timeout=60.0, env_file=".env",
        annotation_url="http://127.0.0.1:8765", annotation_timeout=5.0,
        skip_annotation_reload=False, skip_gate_refresh=False, workspace="workspace",
        gate_python="python3",
        positive_template="positive.json", claim_template="claim.json",
        positive_secondary=1, claim_secondary=1, negative_secondary=1,
        assignment_seed="seed", assignment_report="assignment.json",
        assignment_report_md="assignment.md",
        gate_report="gate.json", activation_report="activation.json",
        activation_report_md="activation.md",
    )


def _write_discovery(prefix, status):
    packets, provenance, labels, cases = [], [], [], []
    if status == "PASS_GENERATION":
        for paper_index in range(20):
            paper_id = f"p{paper_index + 1}"
            for code in ("M", "P"):
                packet_id = f"discovery-{paper_id}-{code.lower()}"
                packets.append({"packet_id": packet_id, "paper_id": paper_id, "task_type": "review_issue"})
                provenance.append({"packet_id": packet_id, "paper_id": paper_id, "discovery_codes": [code]})
                labels.append({"packet_id": packet_id, "paper_id": paper_id, "task_type": "review_issue", "allowed_labels": ["A", "B", "C", "D"]})
                cases.append({"paper_id": paper_id, "discovery_code": code, "valid": True, "candidate_count": 1})
    packet_bytes = b"".join(_canonical_bytes(item) for item in packets)
    manifest = {
        "status": status,
        "paper_count": 20,
        "valid_case_count": 40,
        "raw_candidate_count": len(packets),
        "neutral_cluster_count": len(packets),
        "candidate_counts_by_code": {"M": 20, "P": 20} if packets else {},
        "paper_coverage_by_code": {"M": 20, "P": 20} if packets else {},
        "model_codes": ["M", "P"],
        "prompt_identity_symmetric": True,
        "generator_identity_absent_from_packets": True,
        "invalid_span_packet_count": 0,
        "packets_sha256": hashlib.sha256(packet_bytes).hexdigest(),
        "provenance_sha256": hashlib.sha256(_canonical_bytes(provenance)).hexdigest(),
        "blocking_issues": [] if status in {"PASS_GENERATION", "DRY_RUN"} else ["api_errors:2"],
    }
    (prefix.parent / f"{prefix.name}_PACKETS.jsonl").write_bytes(packet_bytes)
    (prefix.parent / f"{prefix.name}_DISCOVERY_PROVENANCE.json").write_text(json.dumps({"items": provenance}))
    (prefix.parent / f"{prefix.name}_MANIFEST.json").write_text(json.dumps(manifest))
    (prefix.parent / f"{prefix.name}_MANIFEST.md").write_text("manifest\n")
    (prefix.parent / f"{prefix.name}_CASES.json").write_text(json.dumps({"cases": cases}))
    (prefix.parent / f"{prefix.name}_HUMAN_AUDIT_TEMPLATE.json").write_text(json.dumps({"labels": labels}))


def _completed(returncode=0):
    return type("Completed", (), {"returncode": returncode, "stdout": "", "stderr": ""})()


def test_pipeline_dry_run_does_not_change_active(monkeypatch, tmp_path):
    args = _args(tmp_path, run_api=False)
    (tmp_path / "active_MANIFEST.json").write_text("sentinel")

    def fake_run(command, **kwargs):
        _write_discovery(tmp_path / "candidate", "DRY_RUN")
        return _completed(0)

    monkeypatch.setattr(pipeline.subprocess, "run", fake_run)
    report = pipeline.run_pipeline(args)

    assert report["status"] == "DRY_RUN_COMPLETE"
    assert report["active_changed"] is False
    assert (tmp_path / "active_MANIFEST.json").read_text() == "sentinel"


def test_blocked_api_generation_preserves_previous_active(monkeypatch, tmp_path):
    args = _args(tmp_path, run_api=True)
    (tmp_path / "active_MANIFEST.json").write_text("previous-active")

    def fake_run(command, **kwargs):
        _write_discovery(tmp_path / "candidate", "BLOCKED")
        return _completed(1)

    monkeypatch.setattr(pipeline.subprocess, "run", fake_run)
    report = pipeline.run_pipeline(args)

    assert report["status"] == "BLOCKED_DISCOVERY"
    assert report["active_changed"] is False
    assert (tmp_path / "active_MANIFEST.json").read_text() == "previous-active"


def test_successful_pipeline_activates_reloads_and_refreshes_gates(monkeypatch, tmp_path):
    args = _args(tmp_path, run_api=True)

    def fake_run(command, **kwargs):
        if any("p34_symmetric_discovery.py" in str(item) for item in command):
            _write_discovery(tmp_path / "candidate", "PASS_GENERATION")
            return _completed(0)
        (tmp_path / "gate.json").write_text(json.dumps({"status": "BLOCKED", "run_api": False}))
        return _completed(1)

    monkeypatch.setattr(pipeline.subprocess, "run", fake_run)
    calls = []
    def fake_post(url, *args, **kwargs):
        calls.append(url.rsplit("/", 1)[-1])
        if url.endswith("reload-assignment"):
            return {"status": "RELOADED", "secondary_counts": {"review_issue": 1}}
        return {"status": "RELOADED", "packet_count": 40}
    monkeypatch.setattr(pipeline, "_post_json", fake_post)

    report = pipeline.run_pipeline(args)

    assert report["status"] == "READY_FOR_HUMAN_LABELS"
    assert report["active_changed"] is True
    assert report["activation"]["status"] == "ACTIVE_READY"
    assert report["annotation_assignment"]["status"] == "PASS"
    assert report["assignment_reload"]["status"] == "RELOADED"
    assert report["annotation_reload"]["status"] == "RELOADED"
    assert calls == ["reload-discovery", "reload-assignment"]
    assert report["gate_refresh"]["run_api"] is False
    assert (tmp_path / "active_PACKETS.jsonl").exists()


def test_pipeline_rejects_stale_gate_report_after_refresh_crash(monkeypatch, tmp_path):
    args = _args(tmp_path, run_api=True)
    (tmp_path / "gate.json").write_text(json.dumps({"status": "STALE"}))

    def fake_run(command, **kwargs):
        if any("p34_symmetric_discovery.py" in str(item) for item in command):
            _write_discovery(tmp_path / "candidate", "PASS_GENERATION")
            return _completed(0)
        return _completed(1)

    monkeypatch.setattr(pipeline.subprocess, "run", fake_run)
    monkeypatch.setattr(
        pipeline,
        "_post_json",
        lambda url, *args, **kwargs: (
            {"status": "RELOADED", "secondary_counts": {"review_issue": 1}}
            if url.endswith("reload-assignment")
            else {"status": "RELOADED", "packet_count": 40}
        ),
    )

    report = pipeline.run_pipeline(args)

    assert report["status"] == "ACTIVE_READY_GATE_REFRESH_PENDING"
    assert report["blocking_issues"] == ["gate_refresh_failed"]
    assert not (tmp_path / "gate.json").exists()


def test_pipeline_can_reuse_strictly_validated_generation_without_provider_call(monkeypatch, tmp_path):
    args = _args(tmp_path, run_api=True)
    args.reuse_generation = True
    _write_discovery(tmp_path / "candidate", "PASS_GENERATION")
    subprocess_calls = []

    def fake_run(command, **kwargs):
        subprocess_calls.append(command)
        (tmp_path / "gate.json").write_text(json.dumps({"status": "BLOCKED", "run_api": False}))
        return _completed(1)

    monkeypatch.setattr(pipeline.subprocess, "run", fake_run)
    monkeypatch.setattr(
        pipeline,
        "_post_json",
        lambda url, *args, **kwargs: (
            {"status": "RELOADED", "secondary_counts": {"review_issue": 1}}
            if url.endswith("reload-assignment")
            else {"status": "RELOADED", "packet_count": 40}
        ),
    )

    report = pipeline.run_pipeline(args)

    assert report["status"] == "READY_FOR_HUMAN_LABELS"
    assert report["generation_reused"] is True
    assert len(subprocess_calls) == 1
    assert "p34_annotation_gate_refresh.py" in " ".join(map(str, subprocess_calls[0]))
