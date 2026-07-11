#!/usr/bin/env python3
"""Materialize or verify the label-sealed P34 holdout19 execution bundle."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Mapping

import pandas as pd

from agent_system.inference.review_runner import _row_to_env_kwargs, load_review_rows
from scripts.p34_experiment_lock import verify_lock


FORBIDDEN_PUBLIC_COLUMNS = {
    "outputs",
    "decision",
    "rating",
    "reviewer_comments",
    "reference_review",
    "reference_ratings",
    "ground_truth_decision",
    "reward_model",
    "extra_info",
}
PUBLIC_COLUMNS = ("id", "inputs", "year", "mode")
SEALED_COLUMNS = ("id", "outputs", "decision", "rating", "reviewer_comments")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_json(path: Path) -> Dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain an object")
    return value


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if hasattr(value, "tolist"):
        return _json_safe(value.tolist())
    if hasattr(value, "item"):
        return _json_safe(value.item())
    return str(value)


def _rows_by_id(dataset_path: Path) -> Dict[str, Dict[str, Any]]:
    result = {}
    for row in load_review_rows(str(dataset_path)):
        mapped = _row_to_env_kwargs(row)
        paper_id = str(row.get("id") or row.get("paper_id") or mapped.get("paper_id") or "")
        if paper_id:
            result[paper_id] = dict(row)
    return result


def _blocked_report(lock_path: Path, lock_check: Mapping[str, Any], reason: str) -> Dict[str, Any]:
    return {
        "schema_version": "p34_holdout_bundle_v1",
        "status": "BLOCKED",
        "boundary": "Holdout materialization authorization; no holdout files written",
        "lock_manifest": str(lock_path),
        "lock_manifest_sha256": _sha256(lock_path) if lock_path.exists() else "",
        "lock_verification": dict(lock_check),
        "blocking_issues": [reason],
    }


def materialize_bundle(lock_path: Path, full_dataset: Path, output_prefix: Path) -> Dict[str, Any]:
    lock_check = verify_lock(lock_path)
    lock = _load_json(lock_path)
    if lock_check["status"] != "PASS":
        return _blocked_report(lock_path, lock_check, "experiment_lock_drift_detected")
    if not lock.get("finalized") or lock.get("status") != "FROZEN_READY":
        return _blocked_report(lock_path, lock_check, "experiment_lock_not_finalized")
    expected_full_hash = str(((lock.get("datasets") or {}).get("full39") or {}).get("sha256") or "")
    if not full_dataset.exists() or _sha256(full_dataset) != expected_full_hash:
        return _blocked_report(lock_path, lock_check, "full39_dataset_hash_mismatch")
    holdout_ids = list((lock.get("paper_split") or {}).get("holdout_ids") or [])
    hardneg_ids = set((lock.get("paper_split") or {}).get("hardneg_ids") or [])
    if len(holdout_ids) != 19 or len(set(holdout_ids)) != 19 or hardneg_ids & set(holdout_ids):
        return _blocked_report(lock_path, lock_check, "invalid_locked_holdout_split")
    rows = _rows_by_id(full_dataset)
    missing = [paper_id for paper_id in holdout_ids if paper_id not in rows]
    if missing:
        return _blocked_report(lock_path, lock_check, f"holdout_ids_missing_from_full39:{len(missing)}")
    public_rows: List[Dict[str, Any]] = []
    sealed_rows: List[Dict[str, Any]] = []
    for paper_id in holdout_ids:
        row = rows[paper_id]
        mapped = _row_to_env_kwargs(row)
        public_rows.append({
            "id": paper_id,
            "inputs": str(row.get("inputs") or mapped.get("paper_text") or ""),
            "year": row.get("year"),
            "mode": row.get("mode"),
        })
        sealed_rows.append({
            "id": paper_id,
            "outputs": _json_safe(row.get("outputs")),
            "decision": _json_safe(row.get("decision")),
            "rating": _json_safe(row.get("rating")),
            "reviewer_comments": _json_safe(row.get("reviewer_comments")),
        })
    public_path = Path(str(output_prefix) + "_INPUT.parquet")
    labels_path = Path(str(output_prefix) + "_SEALED_REFERENCES.json")
    manifest_path = Path(str(output_prefix) + "_MANIFEST.json")
    public_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(public_rows, columns=PUBLIC_COLUMNS).to_parquet(public_path, index=False)
    labels_path.write_text(
        json.dumps({
            "schema_version": "p34_holdout_sealed_references_v1",
            "warning": "Do not expose this file to discovery, Judge, runtime prompts, or pre-adjudication analysis.",
            "paper_ids": holdout_ids,
            "references": sealed_rows,
        }, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    os.chmod(labels_path, 0o600)
    public_frame = pd.read_parquet(public_path)
    blocking = []
    leaked = sorted(FORBIDDEN_PUBLIC_COLUMNS & set(public_frame.columns))
    if leaked:
        blocking.append("forbidden_public_columns:" + ",".join(leaked))
    if list(public_frame["id"].astype(str)) != holdout_ids:
        blocking.append("public_holdout_id_order_mismatch")
    if any(not str(value or "").strip() for value in public_frame["inputs"]):
        blocking.append("empty_public_paper_text")
    manifest = {
        "schema_version": "p34_holdout_bundle_v1",
        "status": "READY" if not blocking else "BLOCKED",
        "boundary": "Label-sealed paper-level holdout execution bundle",
        "experiment_lock": str(lock_path),
        "experiment_lock_sha256": _sha256(lock_path),
        "experiment_config_sha256": lock.get("config_sha256"),
        "full39_dataset": str(full_dataset),
        "full39_dataset_sha256": _sha256(full_dataset),
        "paper_count": len(holdout_ids),
        "paper_ids": holdout_ids,
        "hardneg_overlap_count": len(hardneg_ids & set(holdout_ids)),
        "public_input": str(public_path),
        "public_input_sha256": _sha256(public_path),
        "public_columns": list(public_frame.columns),
        "forbidden_public_columns": sorted(FORBIDDEN_PUBLIC_COLUMNS),
        "sealed_references": str(labels_path),
        "sealed_references_sha256": _sha256(labels_path),
        "sealed_reference_columns": list(SEALED_COLUMNS),
        "sealed_file_mode": oct(labels_path.stat().st_mode & 0o777),
        "blocking_issues": blocking,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return manifest


def verify_bundle(manifest_path: Path) -> Dict[str, Any]:
    manifest = _load_json(manifest_path)
    mismatches = []
    lock_path = Path(str(manifest.get("experiment_lock") or ""))
    lock_check = verify_lock(lock_path) if lock_path.exists() else {"status": "MISSING"}
    if lock_check.get("status") != "PASS":
        mismatches.append({"kind": "experiment_lock", "actual": lock_check.get("status")})
    else:
        lock = _load_json(lock_path)
        if not lock.get("finalized") or lock.get("status") != "FROZEN_READY":
            mismatches.append({"kind": "experiment_lock_not_finalized"})
        if lock.get("config_sha256") != manifest.get("experiment_config_sha256"):
            mismatches.append({"kind": "experiment_config_hash_mismatch"})
    public_path = Path(str(manifest.get("public_input") or ""))
    labels_path = Path(str(manifest.get("sealed_references") or ""))
    for kind, path, expected in (
        ("public_input_hash", public_path, manifest.get("public_input_sha256")),
        ("sealed_references_hash", labels_path, manifest.get("sealed_references_sha256")),
    ):
        actual = _sha256(path) if path.exists() else "MISSING"
        if actual != expected:
            mismatches.append({"kind": kind, "expected": expected, "actual": actual})
    if public_path.exists():
        frame = pd.read_parquet(public_path)
        leaked = sorted(FORBIDDEN_PUBLIC_COLUMNS & set(frame.columns))
        if leaked:
            mismatches.append({"kind": "forbidden_public_columns", "columns": leaked})
        ids = list(frame["id"].astype(str)) if "id" in frame else []
        if ids != list(manifest.get("paper_ids") or []):
            mismatches.append({"kind": "public_paper_ids_mismatch"})
        if len(ids) != 19 or len(set(ids)) != 19:
            mismatches.append({"kind": "public_not_19_unique", "count": len(ids), "unique": len(set(ids))})
    if labels_path.exists() and oct(labels_path.stat().st_mode & 0o777) != "0o600":
        mismatches.append({"kind": "sealed_file_mode", "actual": oct(labels_path.stat().st_mode & 0o777)})
    return {
        "schema_version": "p34_holdout_bundle_verify_v1",
        "status": "PASS" if not mismatches else "DRIFT_OR_LEAKAGE_DETECTED",
        "manifest": str(manifest_path),
        "manifest_sha256": _sha256(manifest_path),
        "mismatch_count": len(mismatches),
        "mismatches": mismatches,
    }


def render_markdown(report: Mapping[str, Any]) -> str:
    lines = ["# P34 Holdout Bundle", "", f"- status: **{report['status']}**"]
    if "paper_ids" in report:
        lines.extend([
            f"- paper_count: `{report['paper_count']}`",
            f"- hardneg_overlap_count: `{report['hardneg_overlap_count']}`",
            f"- public_columns: `{report['public_columns']}`",
            f"- public_input_sha256: `{report['public_input_sha256']}`",
            f"- sealed_references_sha256: `{report['sealed_references_sha256']}`",
            f"- sealed_file_mode: `{report['sealed_file_mode']}`", "",
            "## Paper IDs", "",
            *[f"- `{paper_id}`" for paper_id in report["paper_ids"]], "",
            "## Blocking Issues", "",
            *([f"- `{item}`" for item in report["blocking_issues"]] or ["- none"]),
        ])
    elif "mismatches" in report:
        lines.extend([
            f"- mismatch_count: `{report['mismatch_count']}`", "",
            "## Mismatches", "",
            *([f"- `{item}`" for item in report["mismatches"]] or ["- none"]),
        ])
    else:
        lines.extend(["", "## Blocking Issues", "", *[f"- `{item}`" for item in report.get("blocking_issues", [])]])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lock-manifest", required=True)
    parser.add_argument("--full-dataset", default="fulltest39_20260606.parquet")
    parser.add_argument("--output-prefix", required=True)
    parser.add_argument("--verify-bundle")
    args = parser.parse_args()
    report = (
        verify_bundle(Path(args.verify_bundle))
        if args.verify_bundle
        else materialize_bundle(Path(args.lock_manifest), Path(args.full_dataset), Path(args.output_prefix))
    )
    report_json = Path(str(args.output_prefix) + "_REPORT.json")
    report_md = Path(str(args.output_prefix) + "_REPORT.md")
    report_json.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    report_md.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps({
        "status": report["status"],
        "paper_count": report.get("paper_count", 0),
        "blocking_issues": report.get("blocking_issues", []),
        "mismatch_count": report.get("mismatch_count", 0),
    }, ensure_ascii=False))
    return 0 if report["status"] in {"READY", "PASS"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
