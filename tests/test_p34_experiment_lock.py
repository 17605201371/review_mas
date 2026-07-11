import json
import subprocess
from types import SimpleNamespace
from pathlib import Path

import pandas as pd

from scripts.p34_experiment_lock import DEFAULT_TRACKED_FILES, build_lock, derive_paper_split, verify_lock


def test_default_lock_tracks_human_gold_and_lock_semantics():
    assert "P34_2_GATE_CONTRACT_20260711.json" in DEFAULT_TRACKED_FILES
    assert "scripts/p34_annotation_server.py" in DEFAULT_TRACKED_FILES
    assert "scripts/p34_annotation_signature.py" in DEFAULT_TRACKED_FILES
    assert "scripts/p34_annotation_app.html" in DEFAULT_TRACKED_FILES
    assert "scripts/p34_portable_annotation.html" in DEFAULT_TRACKED_FILES
    assert "scripts/p34_portable_paper_index.html" in DEFAULT_TRACKED_FILES
    assert "scripts/p34_annotation_gate_refresh.py" in DEFAULT_TRACKED_FILES
    assert "scripts/p34_annotation_quality_report.py" in DEFAULT_TRACKED_FILES
    assert "scripts/p34_annotation_assignment.py" in DEFAULT_TRACKED_FILES
    assert "scripts/p34_activate_symmetric_discovery.py" in DEFAULT_TRACKED_FILES
    assert "scripts/p34_symmetric_discovery_pipeline.py" in DEFAULT_TRACKED_FILES
    assert "scripts/p34_request_ledger.py" in DEFAULT_TRACKED_FILES
    assert "scripts/p34_human_label_audit.py" in DEFAULT_TRACKED_FILES
    assert "scripts/p34_paper_index_audit.py" in DEFAULT_TRACKED_FILES
    assert "scripts/p34_build_judge_dataset.py" in DEFAULT_TRACKED_FILES
    assert "scripts/p34_experiment_lock.py" in DEFAULT_TRACKED_FILES


def _write_dataset(path, ids):
    rows = [
        {
            "id": paper_id,
            "inputs": f"Paper text for {paper_id}.",
            "outputs": "Human review.",
            "decision": "Reject",
            "rating": [5],
            "reviewer_comments": "Comment.",
        }
        for paper_id in ids
    ]
    pd.DataFrame(rows).to_parquet(path, index=False)


def test_derive_paper_split_requires_exact_20_plus_19_partition():
    hardneg = [f"p{i:02d}" for i in range(20)]
    full = hardneg + [f"h{i:02d}" for i in range(19)]

    split = derive_paper_split(hardneg, full)

    assert split["status"] == "PASS"
    assert split["overlap_count"] == 20
    assert split["holdout_count"] == 19
    assert split["holdout_ids"] == sorted(full[20:])


def test_experiment_lock_freezes_files_datasets_readiness_and_detects_drift(tmp_path):
    hardneg_ids = [f"p{i:02d}" for i in range(20)]
    full_ids = hardneg_ids + [f"h{i:02d}" for i in range(19)]
    _write_dataset(tmp_path / "hardneg.parquet", hardneg_ids)
    _write_dataset(tmp_path / "full.parquet", full_ids)
    (tmp_path / "code.py").write_text("VALUE = 1\n")
    readiness = {
        "two_by_two.json": "PASS",
        "paper_index.json": "PASS",
        "positive.json": "PASS",
        "claim.json": "PASS",
        "symmetric.json": "PASS_GENERATION",
        "assignment.json": "PASS",
    }
    for name, status in readiness.items():
        (tmp_path / name).write_text(json.dumps({"status": status}) + "\n")
    args = SimpleNamespace(
        repo=str(tmp_path),
        hardneg_dataset="hardneg.parquet",
        full_dataset="full.parquet",
        tracked_file=["code.py"],
        two_by_two_report="two_by_two.json",
        paper_index_audit="paper_index.json",
        positive_label_audit="positive.json",
        claim_label_audit="claim.json",
        symmetric_discovery_manifest="symmetric.json",
        annotation_assignment="assignment.json",
        gate_contract=str(Path(__file__).parents[1] / "P34_2_GATE_CONTRACT_20260711.json"),
        require_clean_git=False,
        git_clean_policy="off",
        finalize=True,
    )

    lock = build_lock(args)
    manifest = tmp_path / "lock.json"
    manifest.write_text(json.dumps(lock, indent=2) + "\n")
    verified = verify_lock(manifest)
    (tmp_path / "code.py").write_text("VALUE = 2\n")
    drifted = verify_lock(manifest)

    assert lock["status"] == "FROZEN_READY"
    assert lock["schema_version"] == "p34_experiment_lock_v2"
    assert lock["thresholds"]["p34_2"]["minimum_cardinality"]["evidence_relation"] == 80
    assert lock["finalized"] is True
    assert lock["paper_split"]["holdout_count"] == 19
    assert verified["status"] == "PASS"
    assert drifted["status"] == "DRIFT_DETECTED"
    assert drifted["mismatches"][0]["kind"] == "tracked_file"


def test_tracked_git_policy_ignores_unrelated_dirty_files_but_blocks_critical_drift(tmp_path):
    hardneg_ids = [f"p{i:02d}" for i in range(20)]
    full_ids = hardneg_ids + [f"h{i:02d}" for i in range(19)]
    _write_dataset(tmp_path / "hardneg.parquet", hardneg_ids)
    _write_dataset(tmp_path / "full.parquet", full_ids)
    (tmp_path / "code.py").write_text("VALUE = 1\n")
    for name, status in {
        "two_by_two.json": "PASS", "paper_index.json": "PASS", "positive.json": "PASS",
        "claim.json": "PASS", "symmetric.json": "PASS_GENERATION", "assignment.json": "PASS",
    }.items():
        (tmp_path / name).write_text(json.dumps({"status": status}) + "\n")
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "p34@example.invalid"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "P34 Test"], cwd=tmp_path, check=True)
    subprocess.run(["git", "add", "code.py"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-m", "freeze code"], cwd=tmp_path, check=True, capture_output=True)
    (tmp_path / "unrelated.txt").write_text("dirty but outside critical scope\n")
    common = dict(
        repo=str(tmp_path), hardneg_dataset="hardneg.parquet", full_dataset="full.parquet",
        tracked_file=["code.py"], gate_contract=str(Path(__file__).parents[1] / "P34_2_GATE_CONTRACT_20260711.json"),
        two_by_two_report="two_by_two.json", paper_index_audit="paper_index.json",
        positive_label_audit="positive.json", claim_label_audit="claim.json",
        symmetric_discovery_manifest="symmetric.json", annotation_assignment="assignment.json",
        require_clean_git=False, finalize=True,
    )

    tracked = build_lock(SimpleNamespace(**common, git_clean_policy="tracked"))
    full = build_lock(SimpleNamespace(**common, git_clean_policy="full"))
    (tmp_path / "code.py").write_text("VALUE = 2\n")
    tracked_drift = build_lock(SimpleNamespace(**common, git_clean_policy="tracked"))

    assert tracked["status"] == "FROZEN_READY"
    assert tracked["config_sha256"] == full["config_sha256"]
    assert tracked["git"]["tracked_clean"] is True
    assert tracked["git"]["full_clean"] is False
    assert "git_full_worktree_not_clean" in full["blocking_issues"][0]
    assert tracked_drift["status"] == "BLOCKED_NOT_FROZEN"
    assert any(item.startswith("git_tracked_scope_not_clean:1") for item in tracked_drift["blocking_issues"])
