#!/usr/bin/env python3
"""P31.6 readiness/status report.

This is a low-risk orchestration helper.  It does not run full20 by itself; it
summarizes the current run pointers, gate artifacts, manual audit status, and
optionally performs a one-call MiMo API preflight.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ENTRY_GATE_WITH_MANUAL = "P31_6_CRITORIGIN_RECOMPUTE_163953_ENTRY_GATE_WITH_MANUAL_AUDIT.json"
DEFAULT_ENTRY_GATE = "P31_6_CRITORIGIN_RECOMPUTE_163953_ENTRY_GATE_AUDIT.json"
DEFAULT_MANUAL_VALIDATION = "P31_6_CRITORIGIN_RECOMPUTE_163953_MANUAL_AUDIT_VALIDATION.json"


def _load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return ""


def _line_count(path: Path) -> int:
    try:
        return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())
    except FileNotFoundError:
        return 0


def _pid_running(pid_file: Path) -> Dict[str, Any]:
    pid_text = _read_text(pid_file)
    if not pid_text:
        return {"pid": "", "running": False, "pid_file_exists": pid_file.exists()}
    try:
        pid = int(pid_text)
    except ValueError:
        return {"pid": pid_text, "running": False, "pid_file_exists": True, "invalid_pid": True}
    try:
        os.kill(pid, 0)
        running = True
    except OSError:
        running = False
    return {"pid": str(pid), "running": running, "pid_file_exists": True}


def _default_entry_gate() -> str:
    if Path(DEFAULT_ENTRY_GATE_WITH_MANUAL).exists():
        return DEFAULT_ENTRY_GATE_WITH_MANUAL
    if Path(DEFAULT_ENTRY_GATE).exists():
        return DEFAULT_ENTRY_GATE
    return ""


def _api_preflight() -> Dict[str, Any]:
    try:
        if str(REPO_ROOT) not in sys.path:
            sys.path.insert(0, str(REPO_ROOT))
        _load_dotenv(REPO_ROOT / ".env")
        _disable_proxy_env_for_api()
        from agent_system.inference.review_runner import ApiReviewGenerator

        generator = ApiReviewGenerator(
            model="mimo-v2.5",
            provider="mimo",
            temperature=0.0,
            top_p=1.0,
            max_tokens=32,
            max_workers=1,
            timeout=30,
            max_retries=1,
        )
        text = generator("Review Manager Agent", '<json>{"ping":true}</json>')
        ok = bool(str(text or "").strip())
        return {"status": "ok" if ok else "empty_response", "ok": ok, "error": ""}
    except Exception as exc:  # pragma: no cover - exercised against live API.
        return {"status": "failed", "ok": False, "error": str(exc)}


def _disable_proxy_env_for_api() -> None:
    # The local macOS shell may export no_proxy entries containing bare IPv6
    # fragments such as "::1"; httpx can parse these as an invalid ":1" port.
    # Full20 launches already sanitize these variables, so keep preflight aligned.
    os.environ["NO_PROXY"] = "*"
    os.environ["no_proxy"] = "*"
    for key in ("HTTPS_PROXY", "HTTP_PROXY", "ALL_PROXY", "https_proxy", "http_proxy", "all_proxy"):
        os.environ[key] = ""


def _load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def _next_action(report: Dict[str, Any]) -> str:
    api = report.get("api_preflight") or {}
    gate = report.get("entry_gate") or {}
    latest = report.get("latest_run") or {}
    machine = str(gate.get("machine_gate_status") or "")
    manual = str(gate.get("manual_gate_status") or "")

    if api.get("status") == "failed":
        error = str(api.get("error") or "")
        if "402" in error or "insufficient_balance" in error.lower() or "balance" in error.lower():
            return "Restore MiMo account balance/key, then run scripts/p31_6_full20_pipeline.sh --launch --wait --update-latest."
        return "Fix API preflight failure, then rerun the P31.6 full20 pipeline."
    if latest.get("running"):
        return f"Monitor active run {latest.get('run_base')} until it reaches 20 rows, then postprocess."
    if machine == "PASS" and manual == "PASS":
        return "P31.6 gate appears ready for P32 review; verify manual audit provenance before entering P32."
    return "Run a fresh P31.6 full20 with scripts/p31_6_full20_pipeline.sh --launch --wait --update-latest, then fill and validate the manual audit template."


def build_report(args: argparse.Namespace) -> Dict[str, Any]:
    latest_run_base = args.run_base or _read_text(Path(".latest_hardneg20_run"))
    latest_jsonl = Path(f"{latest_run_base}.jsonl") if latest_run_base else Path("")
    latest_pid = Path(f"{latest_run_base}.pid") if latest_run_base else Path("")
    latest_log = Path(f"{latest_run_base}.log") if latest_run_base else Path("")
    pid_info = _pid_running(latest_pid) if latest_run_base else {"pid": "", "running": False, "pid_file_exists": False}

    entry_gate_path = args.entry_gate_json or _default_entry_gate()
    entry_gate: Dict[str, Any] = {}
    entry_gate_exists = bool(entry_gate_path and Path(entry_gate_path).exists())
    if entry_gate_exists:
        entry_gate = _load_json(Path(entry_gate_path))

    if args.manual_validation_json:
        manual_path = args.manual_validation_json
    elif args.entry_gate_json:
        manual_path = ""
    else:
        manual_path = DEFAULT_MANUAL_VALIDATION
    manual: Dict[str, Any] = {}
    manual_exists = bool(manual_path and Path(manual_path).exists())
    if manual_exists:
        manual = _load_json(Path(manual_path))

    api_status: Dict[str, Any] = {"status": "not_run", "ok": False, "error": ""}
    if args.api_preflight:
        api_status = _api_preflight()

    report = {
        "latest_run": {
            "run_base": latest_run_base,
            "jsonl": str(latest_jsonl) if latest_run_base else "",
            "jsonl_exists": latest_jsonl.exists() if latest_run_base else False,
            "jsonl_lines": _line_count(latest_jsonl) if latest_run_base else 0,
            "log": str(latest_log) if latest_run_base else "",
            "log_exists": latest_log.exists() if latest_run_base else False,
            **pid_info,
        },
        "latest_pointers": {
            ".latest_hardneg20_dashboard": _read_text(Path(".latest_hardneg20_dashboard")),
            ".latest_hardneg20_review_issue_cases": _read_text(Path(".latest_hardneg20_review_issue_cases")),
            ".latest_hardneg20_recovery_case": _read_text(Path(".latest_hardneg20_recovery_case")),
            ".latest_hardneg20_log": _read_text(Path(".latest_hardneg20_log")),
        },
        "entry_gate": {
            "path": entry_gate_path,
            "exists": entry_gate_exists,
            "machine_gate_status": entry_gate.get("machine_gate_status", ""),
            "manual_gate_status": entry_gate.get("manual_gate_status", ""),
            "blocking_issues": entry_gate.get("blocking_issues", []),
            "headline_metrics": entry_gate.get("headline_metrics", {}),
            "manual_audit_summary": entry_gate.get("manual_audit_summary", {}),
        },
        "manual_validation": {
            "path": manual_path,
            "exists": manual_exists,
            "summary": manual.get("summary", {}),
        },
        "api_preflight": api_status,
        "pipeline_command": "scripts/p31_6_full20_pipeline.sh --launch --wait --update-latest",
    }
    report["next_action"] = _next_action(report)
    report["p32_entry_ready"] = (
        report["entry_gate"]["machine_gate_status"] == "PASS"
        and report["entry_gate"]["manual_gate_status"] == "PASS"
    )
    return report


def _render_md(report: Dict[str, Any]) -> str:
    latest = report["latest_run"]
    gate = report["entry_gate"]
    manual = report["manual_validation"]
    api = report["api_preflight"]
    metrics = gate.get("headline_metrics") or {}
    manual_summary = manual.get("summary") or gate.get("manual_audit_summary") or {}

    lines = ["# P31.6 Readiness Status", ""]
    lines.append(f"- P32 entry ready: **{report['p32_entry_ready']}**")
    lines.append(f"- next action: {report['next_action']}")
    lines.append("")
    lines.append("## Latest Run")
    lines.append("")
    lines.append(f"- run base: `{latest.get('run_base', '')}`")
    lines.append(f"- rows: `{latest.get('jsonl_lines', 0)}`")
    lines.append(f"- running: `{latest.get('running', False)}`")
    lines.append(f"- pid: `{latest.get('pid', '')}`")
    lines.append("")
    lines.append("## Entry Gate")
    lines.append("")
    lines.append(f"- path: `{gate.get('path', '')}`")
    lines.append(f"- machine gate: **{gate.get('machine_gate_status', '')}**")
    lines.append(f"- manual gate: **{gate.get('manual_gate_status', '')}**")
    if gate.get("blocking_issues"):
        lines.append("- blocking issues:")
        for issue in gate["blocking_issues"]:
            lines.append(f"  - {issue}")
    lines.append("")
    lines.append("## Key Metrics")
    lines.append("")
    lines.append("| metric | value |")
    lines.append("|---|---:|")
    for key in (
        "verified_review_issue_count",
        "verified_review_issue_cluster_recomputed_count",
        "quote_duplicate_merged_verified_review_issue_cluster_count",
        "critique_payload_verified_cluster_count",
        "candidate_menu_item_verified_count",
        "candidate_menu_item_any_origin_verified_count",
        "critique_only_verified_cluster_count",
        "verified_review_issue_cluster_origin_critique_payload_count",
        "mark_contested_commit_count",
    ):
        lines.append(f"| `{key}` | {metrics.get(key, '')} |")
    lines.append("")
    lines.append("## Manual Audit")
    lines.append("")
    lines.append(f"- validation: `{manual.get('path', '')}`")
    lines.append(f"- status: **{manual_summary.get('status', '')}**")
    lines.append(f"- manual A/B clusters: `{manual_summary.get('manual_A_B_clusters', '')}`")
    lines.append(f"- manual D clusters: `{manual_summary.get('manual_D_clusters', '')}`")
    lines.append(f"- unfilled clusters: `{manual_summary.get('unfilled_clusters', '')}`")
    lines.append("")
    lines.append("## API Preflight")
    lines.append("")
    lines.append(f"- status: `{api.get('status', '')}`")
    if api.get("error"):
        lines.append(f"- error: `{api.get('error')}`")
    lines.append("")
    lines.append("## Command")
    lines.append("")
    lines.append("```bash")
    lines.append(report["pipeline_command"])
    lines.append("```")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-base", default="")
    parser.add_argument("--entry-gate-json", default="")
    parser.add_argument("--manual-validation-json", default="")
    parser.add_argument("--api-preflight", action="store_true")
    parser.add_argument("--output-json", default="")
    parser.add_argument("--output-md", default="")
    args = parser.parse_args()

    try:
        report = build_report(args)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if args.output_json:
        Path(args.output_json).write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.output_md:
        Path(args.output_md).write_text(_render_md(report), encoding="utf-8")

    print(f"P31.6 ready: {report['p32_entry_ready']}")
    print(f"next_action: {report['next_action']}")
    print(f"latest_run: {report['latest_run'].get('run_base')} rows={report['latest_run'].get('jsonl_lines')}")
    print(
        "gate: machine={machine} manual={manual}".format(
            machine=report["entry_gate"].get("machine_gate_status", ""),
            manual=report["entry_gate"].get("manual_gate_status", ""),
        )
    )
    print(f"api_preflight: {report['api_preflight'].get('status')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
