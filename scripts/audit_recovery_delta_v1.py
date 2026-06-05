#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def as_list(v: Any) -> List[Any]:
    return v if isinstance(v, list) else []


def risk_counts(turn: Dict[str, Any]) -> Dict[str, int]:
    risk = turn.get("risk_profile") or {}
    return {
        "open_question_count": int(risk.get("open_question_count") or 0),
        "major_flaw_count": int(risk.get("major_flaw_count") or 0),
        "conflict_count": int(risk.get("conflict_count") or 0),
        "gap_count": len(as_list(turn.get("evidence_gaps"))),
        "revision_summary_count": len(as_list(turn.get("revision_summary"))),
    }


def classify_commit(delta: Dict[str, int], turn: Dict[str, Any]) -> str:
    downs = sum(1 for key in ["open_question_count", "major_flaw_count", "conflict_count", "gap_count"] if delta[key] < 0)
    ups = sum(1 for key in ["open_question_count", "major_flaw_count", "conflict_count", "gap_count"] if delta[key] > 0)
    new_status = str(turn.get("new_status") or "")
    new_items = [str(x) for x in as_list(turn.get("new_items"))]
    has_recovery_missing = any("evidence-recovery-missing" in x for x in new_items)
    if downs > 0 and ups == 0:
        return "consistency_improved_proxy"
    if ups > 0 and downs == 0:
        return "burden_increased_proxy"
    if new_status in {"unsupported", "superseded"} and has_recovery_missing and downs == 0:
        return "conservative_downgrade_proxy"
    if downs == 0 and ups == 0:
        return "neutral_proxy"
    return "mixed_proxy"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="claim_coverage_full39_20260511_qwen35_merged.jsonl")
    parser.add_argument("--output-json", default="RECOVERY_DELTA_AUDIT_V1_FULL39.json")
    parser.add_argument("--output-md", default="RECOVERY_DELTA_AUDIT_V1_FULL39.md")
    args = parser.parse_args()

    rows = load_jsonl(Path(args.input))
    aggregate = Counter()
    per_event: List[Dict[str, Any]] = []
    per_paper: List[Dict[str, Any]] = []
    class_dist = Counter()
    source_dist = Counter()
    transition_dist = Counter()

    for row in rows:
        pid = row.get("paper_id")
        turns = row.get("turn_logs") or []
        paper_commits = 0
        for idx, turn in enumerate(turns):
            committed = bool(turn.get("recovery_patch_committed") or turn.get("recovery_committed"))
            if not committed:
                continue
            paper_commits += 1
            prev = turns[idx - 1] if idx > 0 else {}
            prev_counts = risk_counts(prev)
            curr_counts = risk_counts(turn)
            delta = {k: curr_counts[k] - prev_counts[k] for k in curr_counts}
            cls = classify_commit(delta, turn)
            class_dist[cls] += 1
            source_dist[str(turn.get("recovery_patch_source") or turn.get("recovery_push_source") or "unknown")] += 1
            transition_dist[f"{turn.get('old_status') or 'none'}->{turn.get('new_status') or 'none'}"] += 1
            detail = {
                "paper_id": pid,
                "turn_id": int(turn.get("turn_id") or idx + 1),
                "target_type": str(turn.get("recovery_target_type") or ""),
                "target_id": str(turn.get("recovery_target_id") or ""),
                "patch_source": str(turn.get("recovery_patch_source") or turn.get("recovery_push_source") or "unknown"),
                "old_status": str(turn.get("old_status") or ""),
                "new_status": str(turn.get("new_status") or ""),
                "new_items": as_list(turn.get("new_items")),
                "retracted_items": as_list(turn.get("retracted_items")),
                "downgraded_items": as_list(turn.get("downgraded_items")),
                "recovery_failure_code": str(turn.get("recovery_failure_code") or ""),
                "prev_counts": prev_counts,
                "curr_counts": curr_counts,
                "delta": delta,
                "proxy_class": cls,
            }
            per_event.append(detail)
            aggregate["recovery_committed"] += 1
            aggregate[f"proxy::{cls}"] += 1
            for key, value in delta.items():
                if value < 0:
                    aggregate[f"improved::{key}"] += 1
                elif value > 0:
                    aggregate[f"worsened::{key}"] += 1
        per_paper.append({"paper_id": pid, "recovery_commit_count": paper_commits})

    md = []
    md.append("# Recovery Delta Audit v1 (Full39)\n")
    md.append(f"- 输入文件: `{args.input}`")
    md.append(f"- recovery committed 事件数: {aggregate['recovery_committed']}")
    md.append("\n## 说明")
    md.append("- 这份审计基于 turn log 可见的前后计数代理，不是完整 state counterfactual。")
    md.append("- 当前能稳定比较的是：`open_question_count`、`major_flaw_count`、`conflict_count`、`evidence_gap_count`。")
    md.append("- `unsupported_with_strong_support` 这类更细粒度一致性指标，现有 turn log 还没有逐 turn 快照，不能在本脚本里直接证明。\n")
    md.append("## commit 代理分类")
    for key, value in class_dist.most_common():
        md.append(f"- `{key}`: {value}")
    md.append("\n## delta 命中次数")
    for key in ["open_question_count", "major_flaw_count", "conflict_count", "gap_count"]:
        md.append(f"- `{key}` improved: {aggregate[f'improved::{key}']}, worsened: {aggregate[f'worsened::{key}']}")
    md.append("\n## patch source 分布")
    for key, value in source_dist.most_common():
        md.append(f"- `{key}`: {value}")
    md.append("\n## status transition 分布")
    for key, value in transition_dist.most_common():
        md.append(f"- `{key}`: {value}")
    md.append("\n## 判断")
    if aggregate['recovery_committed'] == 0:
        md.append("- 当前 full39 没有 committed recovery，无法证明 recovery 是否改善状态。")
    elif aggregate['proxy::consistency_improved_proxy'] == 0:
        md.append("- 当前 committed recovery 仍主要表现为保守状态降级或中性提交，无法仅凭现有日志证明其显著改善状态一致性。")
    else:
        md.append("- 当前 committed recovery 中已经出现可观测的一致性改善代理，但仍需更细粒度 turn-state 快照去证明 unsupported-with-strong-support / stale-gap 等核心问题是否下降。")
    if aggregate['proxy::conservative_downgrade_proxy'] > 0:
        md.append("- `conservative_downgrade_proxy` 仍存在，说明 recovery 里仍有一部分更像“证据不足降级器”，而不是明确发现论文缺陷。")
    md.append("\n## 前 10 个 commit 事件")
    for event in per_event[:10]:
        md.append(
            f"- `{event['paper_id']}` turn {event['turn_id']} / {event['old_status']} -> {event['new_status']} / source=`{event['patch_source']}` / class=`{event['proxy_class']}` / delta={event['delta']}"
        )

    summary = {
        "input": args.input,
        "paper_count": len(rows),
        "recovery_committed": aggregate["recovery_committed"],
        "proxy_class_distribution": dict(class_dist),
        "patch_source_distribution": dict(source_dist),
        "status_transition_distribution": dict(transition_dist),
        "delta_improved_counts": {k: aggregate[f"improved::{k}"] for k in ["open_question_count", "major_flaw_count", "conflict_count", "gap_count"]},
        "delta_worsened_counts": {k: aggregate[f"worsened::{k}"] for k in ["open_question_count", "major_flaw_count", "conflict_count", "gap_count"]},
        "per_event": per_event,
        "per_paper": per_paper,
    }
    Path(args.output_json).write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    Path(args.output_md).write_text("\n".join(md) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
