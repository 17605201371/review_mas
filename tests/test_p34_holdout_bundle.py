import json
from types import SimpleNamespace
from pathlib import Path

import pandas as pd

from scripts.p34_experiment_lock import build_lock
from scripts.p34_holdout_bundle import materialize_bundle, verify_bundle


def _write_dataset(path, ids):
    pd.DataFrame([
        {
            "id": paper_id,
            "inputs": f"Paper text for {paper_id}.",
            "outputs": f"Reference review for {paper_id}.",
            "decision": "Reject",
            "rating": [5],
            "reviewer_comments": f"Reviewer comment for {paper_id}.",
            "year": 2026,
            "mode": "test",
        }
        for paper_id in ids
    ]).to_parquet(path, index=False)


def _lock(tmp_path, finalize):
    hardneg_ids = [f"p{i:02d}" for i in range(20)]
    full_ids = hardneg_ids + [f"h{i:02d}" for i in range(19)]
    _write_dataset(tmp_path / "hardneg.parquet", hardneg_ids)
    _write_dataset(tmp_path / "full.parquet", full_ids)
    (tmp_path / "code.py").write_text("VALUE = 1\n")
    for name, status in {
        "two_by_two.json": "PASS",
        "paper_index.json": "PASS",
        "positive.json": "PASS",
        "claim.json": "PASS",
        "symmetric.json": "PASS_GENERATION",
        "assignment.json": "PASS",
    }.items():
        (tmp_path / name).write_text(json.dumps({"status": status}) + "\n")
    args = SimpleNamespace(
        repo=str(tmp_path), hardneg_dataset="hardneg.parquet", full_dataset="full.parquet",
        tracked_file=["code.py"], two_by_two_report="two_by_two.json",
        paper_index_audit="paper_index.json", positive_label_audit="positive.json",
        claim_label_audit="claim.json", symmetric_discovery_manifest="symmetric.json",
        annotation_assignment="assignment.json",
        gate_contract=str(Path(__file__).parents[1] / "P34_2_GATE_CONTRACT_20260711.json"),
        require_clean_git=False, git_clean_policy="off", finalize=finalize,
    )
    value = build_lock(args)
    path = tmp_path / ("final_lock.json" if finalize else "draft_lock.json")
    path.write_text(json.dumps(value, indent=2) + "\n")
    return path, tmp_path / "full.parquet"


def test_holdout_bundle_requires_finalized_lock_and_writes_nothing_public(tmp_path):
    lock_path, full_path = _lock(tmp_path, finalize=False)
    prefix = tmp_path / "blocked_holdout"

    report = materialize_bundle(lock_path, full_path, prefix)

    assert report["status"] == "BLOCKED"
    assert report["blocking_issues"] == ["experiment_lock_not_finalized"]
    assert not (tmp_path / "blocked_holdout_INPUT.parquet").exists()
    assert not (tmp_path / "blocked_holdout_SEALED_REFERENCES.json").exists()


def test_holdout_bundle_separates_public_papers_from_sealed_references(tmp_path):
    lock_path, full_path = _lock(tmp_path, finalize=True)
    prefix = tmp_path / "holdout19"

    report = materialize_bundle(lock_path, full_path, prefix)
    verified = verify_bundle(tmp_path / "holdout19_MANIFEST.json")
    public = pd.read_parquet(tmp_path / "holdout19_INPUT.parquet")
    sealed = json.loads((tmp_path / "holdout19_SEALED_REFERENCES.json").read_text())

    assert report["status"] == "READY"
    assert report["paper_count"] == 19
    assert report["hardneg_overlap_count"] == 0
    assert list(public.columns) == ["id", "inputs", "year", "mode"]
    assert len(public) == 19
    assert len(sealed["references"]) == 19
    assert "outputs" in sealed["references"][0]
    assert report["sealed_file_mode"] == "0o600"
    assert verified["status"] == "PASS"


def test_holdout_bundle_verifier_detects_public_label_leakage(tmp_path):
    lock_path, full_path = _lock(tmp_path, finalize=True)
    prefix = tmp_path / "holdout19"
    materialize_bundle(lock_path, full_path, prefix)
    public_path = tmp_path / "holdout19_INPUT.parquet"
    frame = pd.read_parquet(public_path)
    frame["decision"] = "Reject"
    frame.to_parquet(public_path, index=False)

    verified = verify_bundle(tmp_path / "holdout19_MANIFEST.json")

    assert verified["status"] == "DRIFT_OR_LEAKAGE_DETECTED"
    assert {item["kind"] for item in verified["mismatches"]} >= {
        "public_input_hash",
        "forbidden_public_columns",
    }
