#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence


DEFAULT_DOC = Path("docs/experiments/mainline_current/MAINLINE_FINAL_V1_PREFLIGHT_AUDIT.md")
DEFAULT_JSON = Path("outputs/results_main/review_infer/mainline_final_v1_preflight_audit.json")


def read_jsonl(path: Path) -> Iterable[Dict[str, Any]]:
    if not path.exists():
        return []
    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_md(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def md_table(headers: Sequence[str], rows: Sequence[Sequence[Any]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(item).replace("\n", " ") for item in row) + " |")
    return "\n".join(lines)


def artifact_status(root: Path, rel_path: str, purpose: str, required: bool = True) -> Dict[str, Any]:
    path = root / rel_path
    return {
        "path": rel_path,
        "purpose": purpose,
        "required": required,
        "exists": path.exists(),
        "size_bytes": path.stat().st_size if path.exists() else 0,
    }


def controller_flags(root: Path | None = None) -> Dict[str, bool]:
    if root is not None:
        root_path = str(root.resolve())
        if root_path not in sys.path:
            sys.path.insert(0, root_path)
    policy = importlib.import_module("agent_system.review_manager_policy")
    return {
        "ENABLE_STICKY_RECOVERY_BIAS": bool(getattr(policy, "ENABLE_STICKY_RECOVERY_BIAS", True)),
        "ENABLE_PROGRESSION_GATE": bool(getattr(policy, "ENABLE_PROGRESSION_GATE", True)),
        "ENABLE_SUPPORT_FORMATION_PASS": bool(getattr(policy, "ENABLE_SUPPORT_FORMATION_PASS", True)),
    }


def iter_turn_logs(row: Dict[str, Any]) -> Iterable[Dict[str, Any]]:
    for key in ("turn_logs", "turn_log"):
        value = row.get(key)
        if isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    yield item


def runtime_controller_counts(rows: Iterable[Dict[str, Any]]) -> Dict[str, int]:
    counts = {
        "sticky_recovery_bias": 0,
        "progression_gate_override": 0,
        "progression_gate_triggered": 0,
        "support_formation_override": 0,
        "support_formation_pass_triggered": 0,
    }
    for row in rows:
        for turn in iter_turn_logs(row):
            source = str(turn.get("policy_source") or "")
            if source in counts:
                counts[source] += 1
            if turn.get("progression_gate_triggered"):
                counts["progression_gate_triggered"] += 1
            if turn.get("support_formation_pass_triggered"):
                counts["support_formation_pass_triggered"] += 1
    return counts


def render_doc(audit: Dict[str, Any]) -> str:
    flag_rows = [[name, value, "must be False"] for name, value in audit["controller_flags"].items()]
    artifact_rows = [
        [
            item["path"],
            "yes" if item["exists"] else "NO",
            "required" if item["required"] else "optional",
            item["purpose"],
            item["size_bytes"],
        ]
        for item in audit["artifacts"]
    ]
    controller_rows = [[key, value] for key, value in audit["runtime_controller_counts"].items()]
    decision = audit["decision"]
    return f"""# Mainline-Final-v1 Preflight Audit

## 结论

- status: `{decision["status"]}`
- go_for_mainline_dry_run: `{decision["go_for_mainline_dry_run"]}`
- go_for_formal_main_experiment: `{decision["go_for_formal_main_experiment"]}`
- recommendation: {decision["recommendation"]}

## Runtime Controller 开关

{md_table(["flag", "current_value", "expected"], flag_rows)}

## Runtime Controller 触发计数

输入 jsonl: `{audit["runtime_jsonl"] or "not provided"}`

{md_table(["signal", "count"], controller_rows)}

## Artifact 检查

{md_table(["path", "exists", "required", "purpose", "size_bytes"], artifact_rows)}

## Blockers

{chr(10).join("- " + item for item in audit["blockers"]) if audit["blockers"] else "- none"}

## Warnings

{chr(10).join("- " + item for item in audit["warnings"]) if audit["warnings"] else "- none"}

## 解释

这份 preflight 只检查主线运行边界，不跑模型、不修改 runtime。它解决的是主试验前最容易污染结论的问题：旧 controller 是否误开、旧 controller 是否在 jsonl 中真实触发、关键论文结果产物是否存在。

正式主试验前必须满足：

- `ENABLE_STICKY_RECOVERY_BIAS=False`
- `ENABLE_PROGRESSION_GATE=False`
- `ENABLE_SUPPORT_FORMATION_PASS=False`
- 已选主线 jsonl 中 `sticky_recovery_bias / progression_gate_override / support_formation_override` 触发计数为 0
- `MAINLINE_FINAL_V1_SPEC.md`、`FINAL_RECOMMENDATION_POLICY_V1_FINAL.md`、主线结果表和 readiness audit 存在

若这些条件通过，可以继续做 dry-run / paper pack / 9B confirmation；但 binary accept/reject 仍只应作为 health check，不能单独作为论文主指标。
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument(
        "--runtime-jsonl",
        type=Path,
        default=Path("MAINLINE_FINAL_V1_CLEAN_4B_FULLTEST39_20260502.jsonl"),
    )
    parser.add_argument("--output-json", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--output-md", type=Path, default=DEFAULT_DOC)
    args = parser.parse_args()

    root = args.root
    flags = controller_flags(root)
    rows = list(read_jsonl(root / args.runtime_jsonl)) if args.runtime_jsonl else []
    counts = runtime_controller_counts(rows)

    artifacts = [
        artifact_status(root, "docs/experiments/mainline_current/MAINLINE_FINAL_V1_SPEC.md", "主线边界 spec"),
        artifact_status(root, "docs/experiments/mainline_current/FINAL_RECOMMENDATION_POLICY_V1_FINAL.md", "final recommendation policy 冻结口径"),
        artifact_status(root, "docs/experiments/mainline_current/MAINLINE_FINAL_V1_UNIFIED_RESULTS_TABLE.md", "统一主线结果表"),
        artifact_status(root, "docs/experiments/mainline_current/MAIN_EXPERIMENT_READINESS_AUDIT_V1.md", "主试验 readiness audit"),
        artifact_status(root, "docs/experiments/mainline_current/MAINLINE_FINAL_V1_ARTIFACT_INDEX.md", "artifact 索引"),
        artifact_status(root, "docs/experiments/mainline_current/PAPER_MAIN_RESULTS_TABLE_V1.md", "论文主结果表草稿"),
        artifact_status(root, "docs/experiments/mainline_current/SUPPORT_QUALITY_FINAL_AUDIT_9B_FULLTEST39.md", "9B support quality audit", required=False),
        artifact_status(root, "docs/experiments/mainline_current/CRITERION_COVERAGE_GROUNDING_9B_FULLTEST39.md", "9B criterion coverage/grounding audit", required=False),
    ]

    blockers: List[str] = []
    warnings: List[str] = []
    for name, value in flags.items():
        if value:
            blockers.append(f"{name} is enabled; mainline runtime expects it to be disabled.")
    for key in ("sticky_recovery_bias", "progression_gate_override", "support_formation_override"):
        if counts.get(key, 0) > 0:
            blockers.append(f"runtime jsonl has {counts[key]} turn(s) with policy_source={key}.")
    for key in ("progression_gate_triggered", "support_formation_pass_triggered"):
        if counts.get(key, 0) > 0:
            blockers.append(f"runtime jsonl has {counts[key]} turn(s) with {key}=true.")
    for item in artifacts:
        if item["required"] and not item["exists"]:
            blockers.append(f"missing required artifact: {item['path']}")
    if not rows:
        warnings.append("runtime jsonl was not found or empty; controller trigger checks only used static flags.")

    status = "pass" if not blockers else "fail"
    audit = {
        "status": status,
        "runtime_jsonl": str(args.runtime_jsonl) if args.runtime_jsonl else "",
        "controller_flags": flags,
        "runtime_controller_counts": counts,
        "artifacts": artifacts,
        "blockers": blockers,
        "warnings": warnings,
        "decision": {
            "status": status,
            "go_for_mainline_dry_run": not blockers,
            "go_for_formal_main_experiment": False,
            "recommendation": (
                "可以继续 dry-run / paper pack；正式主试验前仍需使用冻结的 final recommendation policy，并把 accept/reject 作为 health check。"
                if not blockers
                else "先修复 blockers，尤其是旧 controller 开关或 jsonl 触发污染。"
            ),
        },
    }
    write_json(root / args.output_json, audit)
    write_md(root / args.output_md, render_doc(audit))
    print(json.dumps({"status": status, "blockers": blockers, "warnings": warnings}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
