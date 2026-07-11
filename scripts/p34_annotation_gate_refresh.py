#!/usr/bin/env python3
"""Refresh all human-label, preflight, lock, and holdout gates for P34."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, Mapping

from scripts.p33_freeform_critique_probe import _load_dotenv
from scripts.p34_2x2_experiment import render_markdown as render_2x2_markdown
from scripts.p34_2x2_experiment import run_2x2
from scripts.p34_annotation_signature import audit_rows, load_public_key
from scripts.p34_annotation_quality_report import build_quality_report, render_markdown as render_quality_markdown
from scripts.p34_experiment_lock import build_lock, render_markdown as render_lock_markdown, verify_lock
from scripts.p34_holdout_bundle import materialize_bundle, render_markdown as render_holdout_markdown
from scripts.p34_human_label_audit import audit_labels, render_markdown as render_label_markdown
from scripts.p34_paper_index_audit import build_report as build_paper_index_report
from scripts.p34_paper_index_audit import render_markdown as render_paper_index_markdown


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(path)


def _write_json(path: Path, value: Any) -> None:
    _atomic_write_text(path, json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def _load_json(path: Path) -> Dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain an object")
    return value


def _write_label_outputs(report: Mapping[str, Any], json_path: Path, md_path: Path, frozen_path: Path) -> None:
    _write_json(json_path, report)
    _atomic_write_text(md_path, render_label_markdown(report))
    _write_json(
        frozen_path,
        {"labels": report["frozen_labels"], "sha256": report["frozen_labels_sha256"]},
    )


def _label_audit(
    workspace: Path,
    task: str,
    minimum_double_labeled: int,
    output_json: Path,
    output_md: Path,
    frozen_output: Path,
    required_secondary_ids: set[str] | None,
    verification_key: Path | None,
) -> Dict[str, Any]:
    report = audit_labels(
        workspace / f"{task}_primary.json",
        workspace / f"{task}_secondary.json",
        workspace / f"{task}_resolution.json",
        minimum_double_labeled,
        True,
        required_secondary_ids,
        task,
        True,
        verification_key,
        True,
    )
    _write_label_outputs(report, output_json, output_md, frozen_output)
    return report


def _lock_args(args: argparse.Namespace, *, finalize: bool) -> SimpleNamespace:
    return SimpleNamespace(
        repo=str(args.repo),
        hardneg_dataset=str(args.hardneg_dataset),
        full_dataset=str(args.full_dataset),
        tracked_file=[],
        gate_contract=str(getattr(args, "gate_contract", "P34_2_GATE_CONTRACT_20260711.json")),
        two_by_two_report=str(args.two_by_two_report),
        paper_index_audit=str(args.paper_index_report),
        positive_label_audit=str(args.positive_report),
        claim_label_audit=str(args.claim_report),
        symmetric_discovery_manifest=str(args.discovery_manifest),
        annotation_assignment=str(args.assignment_manifest),
        require_clean_git=False,
        git_clean_policy="tracked" if finalize else "off",
        finalize=bool(finalize),
    )


def refresh_gates(args: argparse.Namespace) -> Dict[str, Any]:
    repo = Path(args.repo).resolve()
    workspace = (repo / args.workspace).resolve()
    _load_dotenv((repo / args.env_file).resolve())
    assignment_path = repo / args.assignment_manifest
    assignment = _load_json(assignment_path) if assignment_path.exists() else {"status": "MISSING", "tasks": {}}
    verification_key = workspace / "annotation_signing_public.pem"
    if verification_key.exists():
        load_public_key(verification_key)
    else:
        verification_key = None

    def assigned(task: str) -> set[str]:
        return set((((assignment.get("tasks") or {}).get(task) or {}).get("secondary_packet_ids") or []))

    positive = _label_audit(
        workspace,
        "evidence_relation",
        args.positive_min_double,
        repo / args.positive_report,
        repo / args.positive_report_md,
        repo / args.positive_frozen,
        assigned("evidence_relation"),
        verification_key,
    )
    claim = _label_audit(
        workspace,
        "claim_faithfulness",
        args.claim_min_double,
        repo / args.claim_report,
        repo / args.claim_report_md,
        repo / args.claim_frozen,
        assigned("claim_faithfulness"),
        verification_key,
    )
    negative = _label_audit(
        workspace,
        "review_issue",
        args.negative_min_double,
        repo / args.negative_report,
        repo / args.negative_report_md,
        repo / args.negative_frozen,
        assigned("review_issue"),
        verification_key,
    )

    paper_index = build_paper_index_report(
        repo / args.hardneg_dataset,
        workspace / "paper_index_anchors_primary.json",
        None,
        args.paper_index_tolerance,
    )
    anchor_path = workspace / "paper_index_anchors_primary.json"
    anchor_rows = (_load_json(anchor_path).get("cases") or []) if anchor_path.exists() else []
    paper_index_signature_audit = (
        audit_rows(anchor_rows, "anchor", verification_key)
        if verification_key is not None
        else {"status": "BLOCKED", "submitted_count": 0, "valid_count": 0, "invalid_ids": [], "error": "verification_key_missing"}
    )
    paper_index["signature_audit"] = paper_index_signature_audit
    paper_index.setdefault("gates", {})["submission_signatures_valid"] = paper_index_signature_audit["status"] == "PASS"
    if paper_index_signature_audit["status"] != "PASS":
        paper_index["status"] = "FAIL"
    _write_json(repo / args.paper_index_report, paper_index)
    _atomic_write_text(repo / args.paper_index_report_md, render_paper_index_markdown(paper_index))

    two_by_two_args = SimpleNamespace(
        base_packets=str(repo / args.base_packets),
        discovery_packets=str(repo / args.discovery_packets),
        discovery_provenance=str(repo / args.discovery_provenance),
        labels=[
            str(repo / args.positive_frozen),
            str(repo / args.claim_frozen),
            str(repo / args.negative_frozen),
        ],
        paper_source_jsonl=str(repo / args.paper_source_jsonl),
        repeats=args.repeats,
        bootstrap_samples=args.bootstrap_samples,
        gate_contract=str(repo / getattr(args, "gate_contract", "P34_2_GATE_CONTRACT_20260711.json")),
        run_api=False,
        max_tokens=args.max_tokens,
        max_workers=args.max_workers,
        timeout=args.timeout,
        max_retries=args.max_retries,
        output_prefix=str(repo / args.two_by_two_prefix),
    )
    two_by_two = run_2x2(two_by_two_args)
    _write_json(repo / args.two_by_two_report, two_by_two)
    _atomic_write_text(repo / args.two_by_two_report_md, render_2x2_markdown(two_by_two))
    for code, subreport in two_by_two.get("reports", {}).items():
        _write_json(Path(str(repo / args.two_by_two_prefix) + f"_{code}_REPORT.json"), subreport)

    draft_lock = build_lock(_lock_args(args, finalize=False))
    _write_json(repo / args.lock_draft, draft_lock)
    _atomic_write_text(repo / args.lock_draft_md, render_lock_markdown(draft_lock))
    lock_verification = verify_lock(repo / args.lock_draft)
    _write_json(repo / args.lock_verify, lock_verification)
    _atomic_write_text(repo / args.lock_verify_md, render_lock_markdown(lock_verification))

    finalize_check = build_lock(_lock_args(args, finalize=True))
    _write_json(repo / args.lock_finalize_check, finalize_check)
    _atomic_write_text(repo / args.lock_finalize_check_md, render_lock_markdown(finalize_check))

    holdout = materialize_bundle(repo / args.lock_finalize_check, repo / args.full_dataset, repo / args.holdout_prefix)
    _write_json(Path(str(repo / args.holdout_prefix) + "_REPORT.json"), holdout)
    _atomic_write_text(Path(str(repo / args.holdout_prefix) + "_REPORT.md"), render_holdout_markdown(holdout))

    registry_path = workspace / "annotator_registry.json"
    registry = _load_json(registry_path) if registry_path.exists() else {}
    discovery_manifest_path = repo / args.discovery_manifest
    discovery_manifest = _load_json(discovery_manifest_path) if discovery_manifest_path.exists() else {}
    discovery_health_path = repo / getattr(
        args,
        "discovery_health_report",
        "P34_2_SYMMETRIC_DISCOVERY_HEALTH_PROBE_20260711_MANIFEST.json",
    )
    discovery_health = _load_json(discovery_health_path) if discovery_health_path.exists() else {}
    quality = build_quality_report(
        positive=positive,
        claim=claim,
        negative=negative,
        paper_index=paper_index,
        assignment=assignment,
        discovery_manifest=discovery_manifest,
        annotator_registry=registry,
        two_by_two=two_by_two,
        discovery_health=discovery_health,
    )
    quality_report = repo / getattr(args, "quality_report", "P34_ANNOTATION_QUALITY_DASHBOARD_20260711.json")
    quality_report_md = repo / getattr(args, "quality_report_md", "P34_ANNOTATION_QUALITY_DASHBOARD_20260711.md")
    _write_json(quality_report, quality)
    _atomic_write_text(quality_report_md, render_quality_markdown(quality))

    stages = {
        "annotation_assignment": str(assignment.get("status") or "MISSING"),
        "positive_labels": positive["status"],
        "claim_labels": claim["status"],
        "negative_labels": negative["status"],
        "paper_index": paper_index["status"],
        "two_by_two": two_by_two["status"],
        "draft_lock": draft_lock["status"],
        "lock_verification": lock_verification["status"],
        "finalize_check": finalize_check["status"],
        "holdout": holdout["status"],
    }
    blocking = []
    for stage, status in stages.items():
        if stage == "lock_verification":
            if status != "PASS":
                blocking.append(f"{stage}:{status}")
        elif stage == "draft_lock":
            if status not in {"DRAFT_READY", "FROZEN_READY"}:
                blocking.append(f"{stage}:{status}")
        elif status not in {"PASS", "PASS_GENERATION", "FROZEN_READY", "READY"}:
            blocking.append(f"{stage}:{status}")
    return {
        "schema_version": "p34_annotation_gate_refresh_v1",
        "status": "PASS" if not blocking else "BLOCKED",
        "boundary": "Human-label-to-holdout gate refresh; API execution and ReviewState mutation disabled",
        "run_api": False,
        "workspace": str(workspace),
        "stages": stages,
        "counts": {
            "assigned_positive_secondary": len(assigned("evidence_relation")),
            "assigned_claim_secondary": len(assigned("claim_faithfulness")),
            "assigned_negative_secondary": len(assigned("review_issue")),
            "positive_primary_complete": positive["primary_validation"]["row_count"]
            - len(positive["primary_validation"]["missing_label_packet_ids"]),
            "positive_total": positive["primary_validation"]["row_count"],
            "claim_primary_complete": claim["primary_validation"]["row_count"]
            - len(claim["primary_validation"]["missing_label_packet_ids"]),
            "claim_total": claim["primary_validation"]["row_count"],
            "negative_primary_complete": negative["primary_validation"]["row_count"]
            - len(negative["primary_validation"]["missing_label_packet_ids"]),
            "negative_total": negative["primary_validation"]["row_count"],
            "paper_index_complete": paper_index["completed_annotation_count"],
            "paper_index_total": paper_index["paper_count"],
            "two_by_two_missing_labels": len(two_by_two["preflight"]["missing_label_packet_ids"]),
            "two_by_two_invalid_spans": len(two_by_two["preflight"]["invalid_span_packet_ids"]),
        },
        "annotation_quality": {
            "status": quality["status"],
            "actionable_now": quality["actionable_now"],
            "blocking_issues": quality["blocking_issues"],
        },
        "config_sha256": draft_lock["config_sha256"],
        "blocking_issues": blocking,
    }


def render_summary(report: Mapping[str, Any]) -> str:
    lines = [
        "# P34 Annotation Gate Refresh",
        "",
        f"- status: **{report['status']}**",
        f"- run_api: `{report['run_api']}`",
        f"- workspace: `{report['workspace']}`",
        f"- config_sha256: `{report['config_sha256']}`",
        "",
        "## Stages",
        "",
    ]
    lines.extend(f"- `{name}`: `{status}`" for name, status in report["stages"].items())
    lines.extend(["", "## Counts", "", f"`{report['counts']}`", "", "## Blocking Issues", ""])
    lines.extend(f"- `{item}`" for item in report["blocking_issues"]) if report["blocking_issues"] else lines.append("- none")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=".")
    parser.add_argument("--workspace", default="P34_ANNOTATIONS_20260711")
    parser.add_argument("--assignment-manifest", default="P34_ANNOTATION_ASSIGNMENT_20260711.json")
    parser.add_argument("--env-file", default=".env")
    parser.add_argument("--hardneg-dataset", default="hard_negative_20_20260611.parquet")
    parser.add_argument("--full-dataset", default="fulltest39_20260606.parquet")
    parser.add_argument("--base-packets", default="P34_2_JUDGE_DATASET_HARDNEG20_20260711_PACKETS.jsonl")
    parser.add_argument("--discovery-packets", default="P34_2_SYMMETRIC_DISCOVERY_ACTIVE_20260711_PACKETS.jsonl")
    parser.add_argument("--discovery-provenance", default="P34_2_SYMMETRIC_DISCOVERY_ACTIVE_20260711_DISCOVERY_PROVENANCE.json")
    parser.add_argument("--discovery-manifest", default="P34_2_SYMMETRIC_DISCOVERY_ACTIVE_20260711_MANIFEST.json")
    parser.add_argument("--discovery-health-report", default="P34_2_SYMMETRIC_DISCOVERY_HEALTH_PROBE_20260711_MANIFEST.json")
    parser.add_argument("--paper-source-jsonl", default="mimo_v25_negqty_recoverycap_guard3_targetneg_freeformrevneg_reviewissuebundle_p33admit_hardneg20_mt7_b4w2_api4_r5t600_tok2048_20260707_100900.jsonl")
    parser.add_argument("--positive-min-double", type=int, default=20)
    parser.add_argument("--claim-min-double", type=int, default=15)
    parser.add_argument("--negative-min-double", type=int, default=20)
    parser.add_argument("--paper-index-tolerance", type=int, default=8)
    parser.add_argument("--repeats", type=int, default=2)
    parser.add_argument("--bootstrap-samples", type=int, default=2000)
    parser.add_argument("--gate-contract", default="P34_2_GATE_CONTRACT_20260711.json")
    parser.add_argument("--max-tokens", type=int, default=2048)
    parser.add_argument("--max-workers", type=int, default=8)
    parser.add_argument("--timeout", type=float, default=180.0)
    parser.add_argument("--max-retries", type=int, default=4)
    parser.add_argument("--positive-report", default="P34_2_POSITIVE_HUMAN_LABEL_READINESS_20260711.json")
    parser.add_argument("--positive-report-md", default="P34_2_POSITIVE_HUMAN_LABEL_READINESS_20260711.md")
    parser.add_argument("--positive-frozen", default="P34_2_POSITIVE_LABELS_FROZEN_20260711.json")
    parser.add_argument("--claim-report", default="P34_2_CLAIM_HUMAN_LABEL_READINESS_20260711.json")
    parser.add_argument("--claim-report-md", default="P34_2_CLAIM_HUMAN_LABEL_READINESS_20260711.md")
    parser.add_argument("--claim-frozen", default="P34_2_CLAIM_LABELS_FROZEN_20260711.json")
    parser.add_argument("--negative-report", default="P34_2_NEGATIVE_HUMAN_LABEL_READINESS_20260711.json")
    parser.add_argument("--negative-report-md", default="P34_2_NEGATIVE_HUMAN_LABEL_READINESS_20260711.md")
    parser.add_argument("--negative-frozen", default="P34_2_NEGATIVE_LABELS_FROZEN_20260711.json")
    parser.add_argument("--paper-index-report", default="P34_1_PAPER_INDEX_AUDIT_HARDNEG20_20260711.json")
    parser.add_argument("--paper-index-report-md", default="P34_1_PAPER_INDEX_AUDIT_HARDNEG20_20260711.md")
    parser.add_argument("--two-by-two-prefix", default="P34_2_2X2_PREFLIGHT_CURRENT_20260711")
    parser.add_argument("--two-by-two-report", default="P34_2_2X2_PREFLIGHT_CURRENT_20260711_REPORT.json")
    parser.add_argument("--two-by-two-report-md", default="P34_2_2X2_PREFLIGHT_CURRENT_20260711_REPORT.md")
    parser.add_argument("--lock-draft", default="P34_EXPERIMENT_LOCK_DRAFT_20260711.json")
    parser.add_argument("--lock-draft-md", default="P34_EXPERIMENT_LOCK_DRAFT_20260711.md")
    parser.add_argument("--lock-verify", default="P34_EXPERIMENT_LOCK_DRAFT_VERIFY_20260711.json")
    parser.add_argument("--lock-verify-md", default="P34_EXPERIMENT_LOCK_DRAFT_VERIFY_20260711.md")
    parser.add_argument("--lock-finalize-check", default="P34_EXPERIMENT_LOCK_FINALIZE_CHECK_20260711.json")
    parser.add_argument("--lock-finalize-check-md", default="P34_EXPERIMENT_LOCK_FINALIZE_CHECK_20260711.md")
    parser.add_argument("--holdout-prefix", default="P34_HOLDOUT19_CURRENT_20260711")
    parser.add_argument("--output-json", default="P34_ANNOTATION_GATE_REFRESH_20260711.json")
    parser.add_argument("--output-md", default="P34_ANNOTATION_GATE_REFRESH_20260711.md")
    parser.add_argument("--quality-report", default="P34_ANNOTATION_QUALITY_DASHBOARD_20260711.json")
    parser.add_argument("--quality-report-md", default="P34_ANNOTATION_QUALITY_DASHBOARD_20260711.md")
    args = parser.parse_args()
    report = refresh_gates(args)
    repo = Path(args.repo).resolve()
    _write_json(repo / args.output_json, report)
    _atomic_write_text(repo / args.output_md, render_summary(report))
    print(json.dumps(report, ensure_ascii=False))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
