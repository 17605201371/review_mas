#!/usr/bin/env python3
"""Run P34 symmetric discovery through activation, annotation reload, and gate refresh."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Mapping
from urllib.request import Request, urlopen

from scripts.p34_activate_symmetric_discovery import activate, render_markdown as render_activation_markdown
from scripts.p34_annotation_assignment import build_assignment, render_markdown as render_assignment_markdown


def _load_json(path: Path) -> Dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain an object")
    return value


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(path)


def _write_json(path: Path, value: Any) -> None:
    _atomic_write_text(path, json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def _post_json(url: str, timeout: float = 30.0) -> Dict[str, Any]:
    request = Request(url, data=b"{}", headers={"Content-Type": "application/json"}, method="POST")
    with urlopen(request, timeout=timeout) as response:
        value = json.loads(response.read().decode("utf-8"))
    if not isinstance(value, dict):
        raise ValueError("annotation service returned a non-object response")
    return value


def _discovery_command(args: argparse.Namespace, source_prefix: Path) -> list[str]:
    command = [
        sys.executable,
        str(Path(args.repo).resolve() / "scripts/p34_symmetric_discovery.py"),
        "--runner-jsonl", str(args.runner_jsonl),
        "--model-codes", "M", "P",
        "--max-context-chars", str(args.max_context_chars),
        "--max-hypotheses", str(args.max_hypotheses),
        "--max-tokens", str(args.max_tokens),
        "--max-workers", str(args.max_workers),
        "--timeout", str(args.timeout),
        "--max-retries", str(args.max_retries),
        "--env-file", str(args.env_file),
        "--output-prefix", str(source_prefix),
    ]
    if args.limit:
        command.extend(["--limit", str(args.limit)])
    if args.run_api:
        command.append("--run-api")
    return command


def run_pipeline(args: argparse.Namespace) -> Dict[str, Any]:
    repo = Path(args.repo).resolve()
    source_prefix = (repo / args.source_prefix).resolve()
    active_prefix = (repo / args.active_prefix).resolve()
    if args.reuse_generation:
        discovery = subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr="")
    else:
        discovery = subprocess.run(
            _discovery_command(args, source_prefix),
            cwd=repo,
            capture_output=True,
            text=True,
            timeout=args.pipeline_timeout,
            check=False,
        )
    manifest_path = Path(str(source_prefix) + "_MANIFEST.json")
    manifest = _load_json(manifest_path) if manifest_path.exists() else {}
    base = {
        "schema_version": "p34_symmetric_discovery_pipeline_v1",
        "boundary": "Discovery-to-human-label orchestration; no Judge admission and no ReviewState mutation",
        "run_api": bool(args.run_api),
        "generation_reused": bool(args.reuse_generation),
        "source_prefix": str(source_prefix),
        "active_prefix": str(active_prefix),
        "discovery_returncode": discovery.returncode,
        "discovery_manifest_status": str(manifest.get("status") or "MISSING"),
        "discovery_counts": {
            "papers": int(manifest.get("paper_count") or 0),
            "valid_cases": int(manifest.get("valid_case_count") or 0),
            "raw_candidates": int(manifest.get("raw_candidate_count") or 0),
            "neutral_clusters": int(manifest.get("neutral_cluster_count") or 0),
            "candidate_counts_by_code": dict(manifest.get("candidate_counts_by_code") or {}),
        },
        "active_changed": False,
        "activation": {},
        "annotation_assignment": {},
        "assignment_reload": {},
        "annotation_reload": {},
        "gate_refresh": {},
        "blocking_issues": [],
    }
    if not manifest:
        return {**base, "status": "BLOCKED_DISCOVERY_EXECUTION", "blocking_issues": ["discovery_manifest_missing"]}
    if args.reuse_generation and not args.run_api:
        return {
            **base,
            "status": "BLOCKED_DISCOVERY_EXECUTION",
            "blocking_issues": ["reuse_generation_requires_run_api_mode"],
        }
    if not args.run_api:
        status = "DRY_RUN_COMPLETE" if manifest.get("status") == "DRY_RUN" and discovery.returncode == 0 else "BLOCKED_DRY_RUN"
        blocking = [] if status == "DRY_RUN_COMPLETE" else [f"dry_run_manifest_status:{manifest.get('status')}"]
        return {**base, "status": status, "blocking_issues": blocking}
    if discovery.returncode != 0 or manifest.get("status") != "PASS_GENERATION":
        return {
            **base,
            "status": "BLOCKED_DISCOVERY",
            "blocking_issues": list(manifest.get("blocking_issues") or [f"discovery_returncode:{discovery.returncode}"]),
        }

    activation = activate(source_prefix, active_prefix)
    activation_json = repo / args.activation_report
    _write_json(activation_json, activation)
    _atomic_write_text(repo / args.activation_report_md, render_activation_markdown(activation))
    base["activation"] = activation
    if activation.get("status") != "ACTIVE_READY":
        return {
            **base,
            "status": "BLOCKED_ACTIVATION",
            "blocking_issues": list(activation.get("blocking_issues") or [str(activation.get("status"))]),
        }
    base["active_changed"] = True

    assignment = build_assignment(
        {
            "evidence_relation": repo / args.positive_template,
            "claim_faithfulness": repo / args.claim_template,
            "review_issue": Path(str(active_prefix) + "_HUMAN_AUDIT_TEMPLATE.json"),
        },
        {
            "evidence_relation": args.positive_secondary,
            "claim_faithfulness": args.claim_secondary,
            "review_issue": args.negative_secondary,
        },
        args.assignment_seed,
    )
    _write_json(repo / args.assignment_report, assignment)
    _atomic_write_text(repo / args.assignment_report_md, render_assignment_markdown(assignment))
    base["annotation_assignment"] = assignment

    if not args.skip_annotation_reload:
        try:
            reload_report = _post_json(args.annotation_url.rstrip("/") + "/api/reload-discovery", args.annotation_timeout)
            assignment_reload = _post_json(args.annotation_url.rstrip("/") + "/api/reload-assignment", args.annotation_timeout)
        except Exception as exc:
            return {
                **base,
                "status": "ACTIVE_READY_RELOAD_PENDING",
                "annotation_reload": {"status": "ERROR", "error_type": type(exc).__name__, "message": str(exc)[:500]},
                "blocking_issues": ["annotation_reload_failed"],
            }
        base["assignment_reload"] = assignment_reload
        base["annotation_reload"] = reload_report
        if assignment_reload.get("status") != "RELOADED" or reload_report.get("status") != "RELOADED":
            return {
                **base,
                "status": "ACTIVE_READY_RELOAD_PENDING",
                "blocking_issues": [
                    f"assignment_reload_status:{assignment_reload.get('status')}",
                    f"annotation_reload_status:{reload_report.get('status')}",
                ]
            }
        expected_negative_secondary = int(
            ((assignment.get("tasks") or {}).get("review_issue") or {}).get("secondary_packet_count") or 0
        )
        loaded_negative_secondary = int(
            (assignment_reload.get("secondary_counts") or {}).get("review_issue") or 0
        )
        if loaded_negative_secondary != expected_negative_secondary:
            return {
                **base,
                "status": "ACTIVE_READY_RELOAD_PENDING",
                "blocking_issues": [
                    f"review_issue_secondary_reload_mismatch:{loaded_negative_secondary}!={expected_negative_secondary}"
                ],
            }

    if not args.skip_gate_refresh:
        gate_path = repo / args.gate_report
        if gate_path.exists():
            gate_path.unlink()
        refresh = subprocess.run(
            [
                str(args.gate_python),
                str(repo / "scripts/p34_annotation_gate_refresh.py"),
                "--repo", str(repo),
                "--workspace", str((repo / args.workspace).resolve()),
            ],
            cwd=repo,
            capture_output=True,
            text=True,
            timeout=args.pipeline_timeout,
            check=False,
        )
        if refresh.returncode not in {0, 1} or not gate_path.exists():
            return {
                **base,
                "status": "ACTIVE_READY_GATE_REFRESH_PENDING",
                "gate_refresh": {
                    "returncode": refresh.returncode,
                    "stderr_tail": (refresh.stderr or "")[-1000:],
                },
                "blocking_issues": ["gate_refresh_failed"],
            }
        base["gate_refresh"] = _load_json(gate_path)

    packet_count = int((activation.get("validation") or {}).get("packet_count") or 0)
    if assignment.get("status") != "PASS":
        return {
            **base,
            "status": "ACTIVE_READY_ASSIGNMENT_BLOCKED",
            "blocking_issues": list(assignment.get("blocking_issues") or ["annotation_assignment_not_pass"]),
        }
    return {
        **base,
        "status": "READY_FOR_HUMAN_LABELS" if packet_count > 0 else "ACTIVE_READY_EMPTY",
        "blocking_issues": [] if packet_count > 0 else ["active_discovery_has_no_packets"],
    }


def render_markdown(report: Mapping[str, Any]) -> str:
    lines = [
        "# P34 Symmetric Discovery Pipeline",
        "",
        f"- status: **{report['status']}**",
        f"- run_api: `{report['run_api']}`",
        f"- discovery_manifest_status: `{report['discovery_manifest_status']}`",
        f"- active_changed: `{report['active_changed']}`",
        f"- discovery_counts: `{report['discovery_counts']}`",
        "",
        "## Blocking Issues",
        "",
    ]
    lines.extend(f"- `{item}`" for item in report.get("blocking_issues", [])) if report.get("blocking_issues") else lines.append("- none")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=".")
    parser.add_argument("--runner-jsonl", default="mimo_v25_negqty_recoverycap_guard3_targetneg_freeformrevneg_reviewissuebundle_p33admit_hardneg20_mt7_b4w2_api4_r5t600_tok2048_20260707_100900.jsonl")
    parser.add_argument("--source-prefix", default="P34_2_SYMMETRIC_DISCOVERY_CANDIDATE_20260711")
    parser.add_argument("--active-prefix", default="P34_2_SYMMETRIC_DISCOVERY_ACTIVE_20260711")
    parser.add_argument("--run-api", action="store_true")
    parser.add_argument("--reuse-generation", action="store_true")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--max-context-chars", type=int, default=12000)
    parser.add_argument("--max-hypotheses", type=int, default=8)
    parser.add_argument("--max-tokens", type=int, default=2048)
    parser.add_argument("--max-workers", type=int, default=8)
    parser.add_argument("--timeout", type=float, default=180.0)
    parser.add_argument("--max-retries", type=int, default=4)
    parser.add_argument("--pipeline-timeout", type=float, default=1800.0)
    parser.add_argument("--env-file", default=".env")
    parser.add_argument("--annotation-url", default="http://127.0.0.1:8765")
    parser.add_argument("--annotation-timeout", type=float, default=30.0)
    parser.add_argument("--skip-annotation-reload", action="store_true")
    parser.add_argument("--skip-gate-refresh", action="store_true")
    parser.add_argument("--gate-python", default=sys.executable)
    parser.add_argument("--workspace", default="P34_ANNOTATIONS_20260711")
    parser.add_argument("--positive-template", default="P34_2_JUDGE_DATASET_HARDNEG20_20260711_POSITIVE_HUMAN_AUDIT_TEMPLATE.json")
    parser.add_argument("--claim-template", default="P34_2_JUDGE_DATASET_HARDNEG20_20260711_CLAIM_HUMAN_AUDIT_TEMPLATE.json")
    parser.add_argument("--positive-secondary", type=int, default=20)
    parser.add_argument("--claim-secondary", type=int, default=15)
    parser.add_argument("--negative-secondary", type=int, default=20)
    parser.add_argument("--assignment-seed", default="P34-20260711-frozen-secondary-v1")
    parser.add_argument("--assignment-report", default="P34_ANNOTATION_ASSIGNMENT_20260711.json")
    parser.add_argument("--assignment-report-md", default="P34_ANNOTATION_ASSIGNMENT_20260711.md")
    parser.add_argument("--gate-report", default="P34_ANNOTATION_GATE_REFRESH_20260711.json")
    parser.add_argument("--activation-report", default="P34_2_SYMMETRIC_DISCOVERY_ACTIVE_ACTIVATION_20260711.json")
    parser.add_argument("--activation-report-md", default="P34_2_SYMMETRIC_DISCOVERY_ACTIVE_ACTIVATION_20260711.md")
    parser.add_argument("--output-json", default="P34_2_SYMMETRIC_DISCOVERY_PIPELINE_20260711.json")
    parser.add_argument("--output-md", default="P34_2_SYMMETRIC_DISCOVERY_PIPELINE_20260711.md")
    args = parser.parse_args()
    report = run_pipeline(args)
    repo = Path(args.repo).resolve()
    _write_json(repo / args.output_json, report)
    _atomic_write_text(repo / args.output_md, render_markdown(report))
    print(json.dumps(report, ensure_ascii=False))
    return 0 if report["status"] in {"DRY_RUN_COMPLETE", "READY_FOR_HUMAN_LABELS", "ACTIVE_READY_EMPTY"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
