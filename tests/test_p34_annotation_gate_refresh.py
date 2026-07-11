from types import SimpleNamespace

from scripts import p34_annotation_gate_refresh as refresh


def _label_report(total, completed, status="BLOCKED"):
    missing = [f"p-{index}" for index in range(total - completed)]
    return {
        "status": status,
        "primary_validation": {
            "row_count": total,
            "missing_label_packet_ids": missing,
        },
    }


def test_refresh_is_fail_closed_and_never_enables_api(monkeypatch, tmp_path):
    holdout_lock_paths = []
    reports = iter([_label_report(104, 3), _label_report(73, 2), _label_report(0, 0)])
    monkeypatch.setattr(refresh, "_load_dotenv", lambda path: None)
    monkeypatch.setattr(refresh, "_label_audit", lambda *args, **kwargs: next(reports))
    monkeypatch.setattr(refresh, "build_paper_index_report", lambda *args, **kwargs: {
        "status": "NEEDS_MANUAL_ANCHORS",
        "completed_annotation_count": 1,
        "paper_count": 20,
    })
    monkeypatch.setattr(refresh, "render_paper_index_markdown", lambda report: "paper\n")
    monkeypatch.setattr(refresh, "run_2x2", lambda args: {
        "status": "BLOCKED",
        "run_api": args.run_api,
        "preflight": {
            "missing_label_packet_ids": ["a", "b"],
            "invalid_span_packet_ids": [],
        },
        "reports": {},
    })
    monkeypatch.setattr(refresh, "render_2x2_markdown", lambda report: "2x2\n")
    monkeypatch.setattr(refresh, "build_lock", lambda args: {
        "status": "BLOCKED_NOT_FROZEN" if args.finalize else "DRAFT_BLOCKED",
        "config_sha256": "abc123",
    })
    monkeypatch.setattr(refresh, "render_lock_markdown", lambda report: "lock\n")
    monkeypatch.setattr(refresh, "verify_lock", lambda path: {"status": "PASS", "finalized": False})
    monkeypatch.setattr(refresh, "materialize_bundle", lambda lock_path, *args: (
        holdout_lock_paths.append(lock_path) or {"status": "BLOCKED"}
    ))
    monkeypatch.setattr(refresh, "render_holdout_markdown", lambda report: "holdout\n")

    args = SimpleNamespace(
        repo=str(tmp_path), workspace="workspace", env_file=".env",
        assignment_manifest="assignment.json",
        hardneg_dataset="hardneg.parquet", full_dataset="full.parquet",
        base_packets="base.jsonl", discovery_packets="discovery.jsonl",
        discovery_provenance="provenance.json", discovery_manifest="manifest.json",
        paper_source_jsonl="papers.jsonl", positive_min_double=20,
        claim_min_double=15, negative_min_double=20, paper_index_tolerance=8,
        repeats=2, bootstrap_samples=2000, max_tokens=2048, max_workers=8,
        timeout=180.0, max_retries=4,
        positive_report="positive.json", positive_report_md="positive.md", positive_frozen="positive-frozen.json",
        claim_report="claim.json", claim_report_md="claim.md", claim_frozen="claim-frozen.json",
        negative_report="negative.json", negative_report_md="negative.md", negative_frozen="negative-frozen.json",
        paper_index_report="paper.json", paper_index_report_md="paper.md",
        two_by_two_prefix="2x2", two_by_two_report="2x2_REPORT.json", two_by_two_report_md="2x2_REPORT.md",
        lock_draft="lock.json", lock_draft_md="lock.md", lock_verify="verify.json", lock_verify_md="verify.md",
        lock_finalize_check="finalize.json", lock_finalize_check_md="finalize.md",
        holdout_prefix="holdout",
    )
    (tmp_path / "assignment.json").write_text('{"status":"BLOCKED","tasks":{}}')

    report = refresh.refresh_gates(args)

    assert report["status"] == "BLOCKED"
    assert report["run_api"] is False
    assert holdout_lock_paths == [tmp_path / "finalize.json"]
    assert report["counts"]["positive_primary_complete"] == 3
    assert report["counts"]["claim_primary_complete"] == 2
    assert report["counts"]["two_by_two_invalid_spans"] == 0
    assert report["config_sha256"] == "abc123"
    assert report["stages"]["lock_verification"] == "PASS"
    assert report["stages"]["holdout"] == "BLOCKED"
