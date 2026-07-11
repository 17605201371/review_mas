#!/usr/bin/env python3
"""Build or verify the immutable P34 experiment lock before holdout execution."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Mapping, Sequence

from agent_system.inference.review_runner import _row_to_env_kwargs, load_review_rows
from scripts.p33_freeform_critique_probe import _load_dotenv
from scripts.p34_2x2_experiment import load_gate_contract


DEFAULT_TRACKED_FILES = [
    "P34_DUAL_MODEL_CONSENSUS_PLAN_20260711.md",
    "P34_2_GATE_CONTRACT_20260711.json",
    "agent_system/review_prompts.py",
    "agent_system/inference/review_runner.py",
    "agent_system/environments/env_package/review/state.py",
    "agent_system/environments/env_package/review/field_authority.py",
    "agent_system/environments/env_package/review/paper_index.py",
    "agent_system/environments/env_package/review/review_retrieval.py",
    "scripts/p34_symmetric_discovery.py",
    "scripts/p34_activate_symmetric_discovery.py",
    "scripts/p34_symmetric_discovery_pipeline.py",
    "scripts/p34_build_judge_dataset.py",
    "scripts/p34_judge_runner.py",
    "scripts/p34_request_ledger.py",
    "scripts/p34_2x2_experiment.py",
    "scripts/p34_annotation_server.py",
    "scripts/p34_annotation_signature.py",
    "scripts/p34_annotation_app.html",
    "scripts/p34_portable_annotation.html",
    "scripts/p34_portable_paper_index.html",
    "scripts/p34_annotation_gate_refresh.py",
    "scripts/p34_annotation_quality_report.py",
    "scripts/p34_annotation_assignment.py",
    "scripts/p34_paper_index_audit.py",
    "scripts/p34_role_retrieval_audit.py",
    "scripts/p34_experiment_lock.py",
    "scripts/p34_holdout_bundle.py",
    "scripts/p34_human_label_audit.py",
]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")


def _load_json(path: Path) -> Dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain an object")
    return value


def _paper_ids(path: Path) -> List[str]:
    ids = []
    for row in load_review_rows(str(path)):
        mapped = _row_to_env_kwargs(row)
        paper_id = str(row.get("id") or row.get("paper_id") or mapped.get("paper_id") or "")
        if paper_id:
            ids.append(paper_id)
    return ids


def derive_paper_split(hardneg_ids: Sequence[str], full_ids: Sequence[str]) -> Dict[str, Any]:
    hardneg_set, full_set = set(hardneg_ids), set(full_ids)
    duplicate_hardneg = sorted(item for item in hardneg_set if hardneg_ids.count(item) > 1)
    duplicate_full = sorted(item for item in full_set if full_ids.count(item) > 1)
    holdout = sorted(full_set - hardneg_set)
    overlap = sorted(full_set & hardneg_set)
    unexpected_hardneg = sorted(hardneg_set - full_set)
    blocking = []
    if len(hardneg_ids) != 20 or len(hardneg_set) != 20:
        blocking.append(f"hardneg_not_20_unique:{len(hardneg_ids)}/{len(hardneg_set)}")
    if len(full_ids) != 39 or len(full_set) != 39:
        blocking.append(f"full_not_39_unique:{len(full_ids)}/{len(full_set)}")
    if len(overlap) != 20:
        blocking.append(f"hardneg_full_overlap_not_20:{len(overlap)}")
    if len(holdout) != 19:
        blocking.append(f"holdout_not_19:{len(holdout)}")
    if unexpected_hardneg:
        blocking.append(f"hardneg_ids_missing_from_full:{len(unexpected_hardneg)}")
    return {
        "status": "PASS" if not blocking else "BLOCKED",
        "hardneg_count": len(hardneg_ids),
        "hardneg_unique_count": len(hardneg_set),
        "full_count": len(full_ids),
        "full_unique_count": len(full_set),
        "overlap_count": len(overlap),
        "holdout_count": len(holdout),
        "hardneg_ids": sorted(hardneg_set),
        "holdout_ids": holdout,
        "overlap_ids": overlap,
        "duplicate_hardneg_ids": duplicate_hardneg,
        "duplicate_full_ids": duplicate_full,
        "unexpected_hardneg_ids": unexpected_hardneg,
        "blocking_issues": blocking,
    }


def _git_state(repo: Path, tracked_files: Sequence[str]) -> Dict[str, Any]:
    def run(*args: str) -> str:
        return subprocess.run(
            ["git", *args], cwd=repo, check=True, capture_output=True, text=True
        ).stdout.strip()
    try:
        full_status = [line for line in run("status", "--porcelain").splitlines() if line]
        tracked_status = [
            line for line in run("status", "--porcelain", "--", *tracked_files).splitlines() if line
        ] if tracked_files else []
        return {
            "available": True,
            "head": run("rev-parse", "HEAD"),
            "branch": run("branch", "--show-current"),
            "dirty_entry_count": len(full_status),
            "clean": not full_status,
            "full_dirty_entry_count": len(full_status),
            "full_clean": not full_status,
            "tracked_dirty_entry_count": len(tracked_status),
            "tracked_clean": not tracked_status,
            "tracked_dirty_entries": tracked_status,
        }
    except Exception as exc:
        return {
            "available": False,
            "error": type(exc).__name__,
            "clean": False,
            "full_clean": False,
            "tracked_clean": False,
        }


def _status_of(path: Path) -> str:
    if not path.exists():
        return "MISSING"
    value = _load_json(path)
    return str(value.get("status") or "UNKNOWN")


def build_lock(args: argparse.Namespace) -> Dict[str, Any]:
    repo = Path(args.repo).resolve()
    hardneg_path = (repo / args.hardneg_dataset).resolve()
    full_path = (repo / args.full_dataset).resolve()
    hardneg_ids, full_ids = _paper_ids(hardneg_path), _paper_ids(full_path)
    split = derive_paper_split(hardneg_ids, full_ids)
    tracked_files = args.tracked_file or DEFAULT_TRACKED_FILES
    gate_contract_path = (repo / getattr(args, "gate_contract", "P34_2_GATE_CONTRACT_20260711.json")).resolve()
    gate_contract_error = ""
    try:
        p34_2_thresholds = load_gate_contract(gate_contract_path)
    except Exception as exc:
        p34_2_thresholds = {}
        gate_contract_error = f"{type(exc).__name__}:{str(exc)[:300]}"
    file_hashes = {}
    missing_files = []
    for relative in tracked_files:
        path = (repo / relative).resolve()
        try:
            display = str(path.relative_to(repo))
        except ValueError:
            display = str(path)
        if not path.exists() or not path.is_file():
            missing_files.append(display)
            continue
        file_hashes[display] = _sha256(path)
    readiness_paths = {
        "two_by_two": (repo / args.two_by_two_report).resolve(),
        "paper_index": (repo / args.paper_index_audit).resolve(),
        "positive_labels": (repo / args.positive_label_audit).resolve(),
        "claim_labels": (repo / args.claim_label_audit).resolve(),
        "symmetric_discovery": (repo / args.symmetric_discovery_manifest).resolve(),
        "annotation_assignment": (repo / args.annotation_assignment).resolve(),
    }
    readiness = {
        key: {
            "path": str(path.relative_to(repo)) if path.is_relative_to(repo) else str(path),
            "sha256": _sha256(path) if path.exists() else "",
            "status": _status_of(path),
        }
        for key, path in readiness_paths.items()
    }
    model_config = {
        "provider": "mimo",
        "base_url": str(os.getenv("MIMO_BASE_URL") or "https://api.xiaomimimo.com/v1"),
        "M": str(os.getenv("MIMO_MODEL") or "mimo-v2.5"),
        "P": str(os.getenv("MIMO_PRO_MODEL") or "mimo-v2.5-pro"),
        "temperature": 0.0,
        "top_p": 1.0,
        "max_tokens": 2048,
        "max_context_chars": 12000,
        "max_hypotheses": 8,
        "judge_repeats": 2,
        "checkpoint_batch_size": 8,
        "request_ledger_schema": "p34_request_ledger_v1",
        "bootstrap_samples": 2000,
        "api_keys_in_manifest": False,
    }
    clean_policy = str(getattr(args, "git_clean_policy", "") or "").strip().lower()
    if not clean_policy:
        clean_policy = "full" if bool(getattr(args, "require_clean_git", False)) else "off"
    if clean_policy not in {"off", "tracked", "full"}:
        raise ValueError("git_clean_policy must be off, tracked, or full")
    thresholds = {
        "p34_2": p34_2_thresholds,
        "paper_index": {
            "boundary_recall_min": 0.90,
            "anchor_recall_min": 0.90,
            "false_boundary_rate_max": 0.10,
        },
    }
    locked_payload = {
        "datasets": {
            "hardneg20": {"path": args.hardneg_dataset, "sha256": _sha256(hardneg_path)},
            "full39": {"path": args.full_dataset, "sha256": _sha256(full_path)},
        },
        "paper_split": split,
        "tracked_file_hashes": file_hashes,
        "gate_contract": {
            "path": str(gate_contract_path.relative_to(repo)) if gate_contract_path.is_relative_to(repo) else str(gate_contract_path),
            "sha256": _sha256(gate_contract_path) if gate_contract_path.exists() else "",
            "schema_version": "p34_2_gate_contract_v1" if not gate_contract_error else "INVALID",
        },
        "readiness_artifacts": readiness,
        "model_config": model_config,
        "thresholds": thresholds,
    }
    blocking = list(split["blocking_issues"])
    if missing_files:
        blocking.append(f"missing_tracked_files:{len(missing_files)}")
    if gate_contract_error:
        blocking.append(f"gate_contract_invalid:{gate_contract_error}")
    required_statuses = {
        "two_by_two": {"PASS"},
        "paper_index": {"PASS"},
        "positive_labels": {"PASS"},
        "claim_labels": {"PASS"},
        "symmetric_discovery": {"PASS_GENERATION"},
        "annotation_assignment": {"PASS"},
    }
    for key, allowed in required_statuses.items():
        if readiness[key]["status"] not in allowed:
            blocking.append(f"readiness_not_pass:{key}:{readiness[key]['status']}")
    git = _git_state(repo, tracked_files)
    if clean_policy == "full" and not git.get("full_clean"):
        blocking.append(f"git_full_worktree_not_clean:{git.get('full_dirty_entry_count', 'unknown')}")
    if clean_policy == "tracked" and not git.get("tracked_clean"):
        blocking.append(f"git_tracked_scope_not_clean:{git.get('tracked_dirty_entry_count', 'unknown')}")
    if args.finalize and blocking:
        status = "BLOCKED_NOT_FROZEN"
    elif args.finalize:
        status = "FROZEN_READY"
    else:
        status = "DRAFT_BLOCKED" if blocking else "DRAFT_READY"
    return {
        "schema_version": "p34_experiment_lock_v2",
        "status": status,
        "finalized": bool(args.finalize and not blocking),
        "boundary": "Experiment configuration and paper split lock; contains no API credentials",
        "repo": str(repo),
        "git": git,
        "git_clean_policy": clean_policy,
        **locked_payload,
        "missing_tracked_files": missing_files,
        "config_sha256": hashlib.sha256(_canonical_bytes(locked_payload)).hexdigest(),
        "blocking_issues": blocking,
    }


def verify_lock(manifest_path: Path) -> Dict[str, Any]:
    manifest = _load_json(manifest_path)
    repo = Path(str(manifest.get("repo") or ".")).resolve()
    mismatches = []
    for relative, expected in (manifest.get("tracked_file_hashes") or {}).items():
        path = (repo / relative).resolve() if not Path(relative).is_absolute() else Path(relative)
        actual = _sha256(path) if path.exists() else "MISSING"
        if actual != expected:
            mismatches.append({"kind": "tracked_file", "path": relative, "expected": expected, "actual": actual})
    for name, item in (manifest.get("datasets") or {}).items():
        path = (repo / str(item.get("path") or "")).resolve()
        actual = _sha256(path) if path.exists() else "MISSING"
        if actual != item.get("sha256"):
            mismatches.append({"kind": "dataset", "path": str(path), "expected": item.get("sha256"), "actual": actual})
    for name, item in (manifest.get("readiness_artifacts") or {}).items():
        stored_path = Path(str(item.get("path") or ""))
        path = (repo / stored_path).resolve() if not stored_path.is_absolute() else stored_path
        actual = _sha256(path) if path.exists() else "MISSING"
        if actual != item.get("sha256"):
            mismatches.append({
                "kind": "readiness_artifact",
                "path": str(path),
                "expected": item.get("sha256"),
                "actual": actual,
            })
    gate_contract = manifest.get("gate_contract") or {}
    gate_contract_path = Path(str(gate_contract.get("path") or ""))
    gate_contract_path = (repo / gate_contract_path).resolve() if not gate_contract_path.is_absolute() else gate_contract_path
    gate_contract_actual = _sha256(gate_contract_path) if gate_contract_path.exists() else "MISSING"
    if gate_contract_actual != gate_contract.get("sha256"):
        mismatches.append({
            "kind": "gate_contract",
            "path": str(gate_contract_path),
            "expected": gate_contract.get("sha256"),
            "actual": gate_contract_actual,
        })
    else:
        try:
            if load_gate_contract(gate_contract_path) != ((manifest.get("thresholds") or {}).get("p34_2") or {}):
                mismatches.append({"kind": "gate_contract_threshold_mismatch", "path": str(gate_contract_path)})
        except Exception as exc:
            mismatches.append({"kind": "gate_contract_invalid", "path": str(gate_contract_path), "error": type(exc).__name__})
    expected_model = manifest.get("model_config") or {}
    current_model = {
        "base_url": str(os.getenv("MIMO_BASE_URL") or "https://api.xiaomimimo.com/v1"),
        "M": str(os.getenv("MIMO_MODEL") or "mimo-v2.5"),
        "P": str(os.getenv("MIMO_PRO_MODEL") or "mimo-v2.5-pro"),
    }
    for key, actual in current_model.items():
        if str(expected_model.get(key) or "") != actual:
            mismatches.append({
                "kind": "model_config",
                "path": key,
                "expected": expected_model.get(key),
                "actual": actual,
            })
    locked_payload = {
        "datasets": manifest.get("datasets"),
        "paper_split": manifest.get("paper_split"),
        "tracked_file_hashes": manifest.get("tracked_file_hashes"),
        "gate_contract": manifest.get("gate_contract"),
        "readiness_artifacts": manifest.get("readiness_artifacts"),
        "model_config": manifest.get("model_config"),
        "thresholds": manifest.get("thresholds"),
    }
    actual_config_hash = hashlib.sha256(_canonical_bytes(locked_payload)).hexdigest()
    if actual_config_hash != manifest.get("config_sha256"):
        mismatches.append({
            "kind": "manifest_config_hash",
            "path": str(manifest_path),
            "expected": manifest.get("config_sha256"),
            "actual": actual_config_hash,
        })
    return {
        "status": "PASS" if not mismatches else "DRIFT_DETECTED",
        "manifest_path": str(manifest_path),
        "manifest_sha256": _sha256(manifest_path),
        "finalized": bool(manifest.get("finalized")),
        "config_sha256": manifest.get("config_sha256"),
        "mismatch_count": len(mismatches),
        "mismatches": mismatches,
    }


def render_markdown(report: Mapping[str, Any]) -> str:
    lines = [
        "# P34 Experiment Lock", "",
        f"- status: **{report['status']}**",
    ]
    if "paper_split" in report:
        lines.extend([
            f"- finalized: `{report['finalized']}`",
            f"- config_sha256: `{report['config_sha256']}`",
            f"- hardneg/full/holdout: `{report['paper_split']['hardneg_count']}/{report['paper_split']['full_count']}/{report['paper_split']['holdout_count']}`",
            f"- git: `{report['git']}`", "",
            "## Holdout IDs", "",
            *[f"- `{paper_id}`" for paper_id in report["paper_split"]["holdout_ids"]], "",
            "## Blocking Issues", "",
            *([f"- `{item}`" for item in report["blocking_issues"]] or ["- none"]),
        ])
    else:
        lines.extend([
            f"- finalized: `{report['finalized']}`",
            f"- config_sha256: `{report['config_sha256']}`",
            f"- mismatch_count: `{report['mismatch_count']}`", "",
            "## Mismatches", "",
            *([f"- `{item}`" for item in report["mismatches"]] or ["- none"]),
        ])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=".")
    parser.add_argument("--hardneg-dataset", default="hard_negative_20_20260611.parquet")
    parser.add_argument("--full-dataset", default="fulltest39_20260606.parquet")
    parser.add_argument("--tracked-file", action="append", default=[])
    parser.add_argument("--gate-contract", default="P34_2_GATE_CONTRACT_20260711.json")
    parser.add_argument("--two-by-two-report", default="P34_2_2X2_PREFLIGHT_CURRENT_20260711_REPORT.json")
    parser.add_argument("--paper-index-audit", default="P34_1_PAPER_INDEX_AUDIT_HARDNEG20_20260711.json")
    parser.add_argument("--positive-label-audit", default="P34_2_POSITIVE_HUMAN_LABEL_READINESS_20260711.json")
    parser.add_argument("--claim-label-audit", default="P34_2_CLAIM_HUMAN_LABEL_READINESS_20260711.json")
    parser.add_argument("--symmetric-discovery-manifest", default="P34_2_SYMMETRIC_DISCOVERY_ACTIVE_20260711_MANIFEST.json")
    parser.add_argument("--annotation-assignment", default="P34_ANNOTATION_ASSIGNMENT_20260711.json")
    parser.add_argument("--env-file", default=".env")
    parser.add_argument("--finalize", action="store_true")
    parser.add_argument("--require-clean-git", action="store_true")
    parser.add_argument("--git-clean-policy", choices=("off", "tracked", "full"), default="")
    parser.add_argument("--verify-manifest")
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--output-md", required=True)
    args = parser.parse_args()
    _load_dotenv(Path(args.env_file))
    report = verify_lock(Path(args.verify_manifest)) if args.verify_manifest else build_lock(args)
    Path(args.output_json).write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    Path(args.output_md).write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps({
        "status": report["status"],
        "finalized": report.get("finalized"),
        "config_sha256": report.get("config_sha256"),
        "blocking_issues": report.get("blocking_issues", []),
        "mismatch_count": report.get("mismatch_count", 0),
    }, ensure_ascii=False))
    return 0 if report["status"] in {"DRAFT_READY", "FROZEN_READY", "PASS"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
