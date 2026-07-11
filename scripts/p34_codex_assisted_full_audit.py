#!/usr/bin/env python3
"""Materialize the Codex-assisted hardneg20 audit from dual independent reviews."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Mapping


NEGATIVE_OVERRIDES = {
    "WNxlJJIEVj": dict(zip(
        "3cda2a2b8de277 4b3cab2c7eaee1 df45009b067102 d9067649cd1a11 3e2163b0fb211f 94213e9d270192 8f5b4cc7d96852 6c85c7e5d05c23".split(),
        "B B B B D B B B".split(),
    )),
    "7Dub7UXTXN": {"45528755c3e113": "C"},
    "9zEBK3E9bX": dict(zip(
        "34a87343db7877 f0a76329ebedbf 6fc7238a7e8826 6e115c2171cd52 c72b886f40bf31 b63a1258b9948e 4fb36e68440370".split(),
        "D D C C D C C".split(),
    )),
    "XyB4VvF01X": dict(zip(
        "36c07b4ab25a45 887444bc3440d8 46724f519232a4 effc4642143d38 8e0bbc954d3abe 5d0ad0c9896ec9 5fa69b83bcbc8a".split(),
        "B B D D C D C".split(),
    )),
    "GE6iywJtsV": dict(zip(
        "e5e136adbc23f6 b3d1c22c88064d 78afd21eb5a1af f887f7452f430c 3e20176035e663 b687e012b6f2ad 5e89eda5580f7e 19aad8efd6870f".split(),
        "D B C D B C D C".split(),
    )),
    "WpXq5n8yLb": dict(zip(
        "8cd3d5cdebd22f bd183cb144d97a ec8d3bfb4374c1 b37616d2c52fbd 5465ea8aeb88af".split(),
        "D B B D B".split(),
    )),
    "NnExMNiTHw": dict(zip(
        "137aa33b453bec 968e2ce2224ca6 24caeb826ba7b0 2579fa7a02348d 512d93b101598f 295d7638a20494".split(),
        "B B C D D D".split(),
    )),
    "a6SntIisgg": {"3cd04ed33d429e": "D", "76e0142fbddbcb": "B"},
    "cklg91aPGk": dict(zip(
        "d64bd7cffdf0c0 bb17dc610fa73b dc5e2676ceb381 e96c3371954484 cc26dcc0948dbc".split(),
        "C D D C C".split(),
    )),
    "HPuLU6q7xq": {"b47ac67732010b": "B", "b7c56d167fb57f": "B", "59260f3f6c3f7a": "B"},
    "fGXyvmWpw6": dict(zip(
        "8638eee519ca47 6a1c40b1d7647c bb9570db59eb6a 1c67e96d6e56ab 89368d11557bb3 e176838cf7c2a9".split(),
        "D D D B B B".split(),
    )),
    "QAgwFiIY4p": {"9bdf772597276f": "D", "a7a699272b3ae3": "D"},
    "TPAj63ax4Y": dict(zip(
        "48113411580031 7263df1316a9f6 3f97bf5a930dca f5bed1596b7c8e d74c46fb640dea fd68f984eb1061".split(),
        "D C C D D D".split(),
    )),
    "mHv6wcBb0z": {"bac9bffd27eaf2": "C", "92c0a7bb8f0295": "C", "848c534c7c182f": "B"},
    "xUe1YqEgd6": dict(zip(
        "2ad2ddbd758aed 5b731085ec054a edcb32d6a15ae5 949ead22cec609 f9198e0c3ac7b2".split(),
        "D D C B D".split(),
    )),
    "YXn76HMetm": {"a9b0d1219d627f": "D", "ec7ead8f8b1b7f": "C", "1fdbb48c5e3e31": "D"},
    "KOUAayk5Kx": {"e3630833612a95": "C", "212e9eaaa0b1f5": "C"},
    "XH3OiIhtvf": {"598ff74f4da2bc": "B", "76ac542b689145": "B", "c6711f8788a4fe": "B"},
}


def _load(path: Path) -> Dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain an object")
    return value


def _pilot_labels(pilot: Mapping[str, Any], task: str) -> Dict[str, Dict[str, Any]]:
    return {str(key): dict(value) for key, value in (pilot.get("tasks", {}).get(task, {}) or {}).items()}


def _evidence_disagreement_label(left: str, right: str) -> str:
    labels = {left, right}
    for label in ("contradicts", "unrelated", "partially_supports", "uncertain", "supports"):
        if label in labels:
            return label
    return "uncertain"


def _final_row(
    paper_id: str,
    task: str,
    packet_id: str,
    left: Mapping[str, Any],
    right: Mapping[str, Any],
    pilot: Mapping[str, Any],
) -> Dict[str, Any]:
    pilot_row = _pilot_labels(pilot, task).get(packet_id) if paper_id == "ye3NrNrYOY" else None
    left_label = str(left.get("label") or "")
    right_label = str(right.get("label") or "")
    if pilot_row:
        label = str(pilot_row.get("suggested_label") or "")
        source = "codex_manual_pilot"
        confidence = "high"
        reason = str(pilot_row.get("reason_zh") or pilot_row.get("rationale_zh") or "")
    elif left_label == right_label:
        label = left_label
        source = "dual_model_agreement"
        confidence = "high" if task != "review_issue" or label in {"A", "D"} else "medium"
        reason = str(right.get("reason_zh") or left.get("reason_zh") or "")
    elif task == "evidence_relation":
        label = _evidence_disagreement_label(left_label, right_label)
        source = "codex_local_evidence_conservative_review"
        confidence = "medium"
        reason = f"局部证据关系从严裁决；M={left_label}，P={right_label}。{right.get('reason_zh') or left.get('reason_zh') or ''}"
    elif task == "claim_faithfulness":
        label = "overstated" if "overstated" in {left_label, right_label} else ("faithful" if "faithful" in {left_label, right_label} else "uncertain")
        source = "codex_scope_conservative_review"
        confidence = "medium"
        reason = f"按主张范围从严裁决；M={left_label}，P={right_label}。{right.get('reason_zh') or left.get('reason_zh') or ''}"
    else:
        suffix = packet_id.rsplit("-", 1)[-1]
        label = NEGATIVE_OVERRIDES.get(paper_id, {}).get(suffix, "C")
        source = "codex_negative_disagreement_review"
        confidence = "medium" if label in {"B", "D"} else "low"
        selected = left if left_label == label else right if right_label == label else {}
        reason = str(selected.get("reason_zh") or f"M={left_label}、P={right_label} 分歧；复核后保留为 {label}。")
    row = {
        "packet_id": packet_id,
        "label": label,
        "reason_zh": reason,
        "decision_source": source,
        "confidence": confidence,
        "independent_labels": {"M": left_label, "P": right_label},
    }
    if task == "review_issue":
        row["cluster_key"] = str(right.get("cluster_key") or left.get("cluster_key") or packet_id)
        row["canonical_issue_zh"] = str(right.get("canonical_issue_zh") or left.get("canonical_issue_zh") or "")
    return row


def build_report(independent: Mapping[str, Any], pilot: Mapping[str, Any]) -> Dict[str, Any]:
    papers = []
    totals = {task: Counter() for task in ("evidence_relation", "claim_faithfulness", "review_issue")}
    source_counts = Counter()
    for paper_id in independent.get("paper_ids", []):
        paper = {"paper_id": paper_id, "paper_summary_zh": independent["audits"]["P"][paper_id].get("paper_summary_zh"), "tasks": {}}
        for task in totals:
            left_rows = {str(row.get("packet_id") or ""): row for row in independent["audits"]["M"][paper_id][task]}
            right_rows = {str(row.get("packet_id") or ""): row for row in independent["audits"]["P"][paper_id][task]}
            rows = [_final_row(paper_id, task, packet_id, left_rows[packet_id], right_rows[packet_id], pilot) for packet_id in left_rows]
            paper["tasks"][task] = rows
            paper[f"{task}_counts"] = dict(Counter(row["label"] for row in rows))
            totals[task].update(row["label"] for row in rows)
            source_counts.update(row["decision_source"] for row in rows)
        paper["paper_index"] = {
            "M": independent["audits"]["M"][paper_id].get("paper_index", {}),
            "P": independent["audits"]["P"][paper_id].get("paper_index", {}),
        }
        papers.append(paper)
    return {
        "schema_version": "p34_codex_assisted_audit_v1",
        "status": "COMPLETE_AI_ASSISTED_AUDIT",
        "boundary": "Codex-assisted audit; not independent human gold and excluded from P34 gates, Judge targets, and ReviewState admission",
        "paper_count": len(papers),
        "summary": {task: dict(counts) for task, counts in totals.items()},
        "decision_source_counts": dict(source_counts),
        "papers": papers,
    }


def render(report: Mapping[str, Any]) -> str:
    lines = [
        "# P34 Hardneg20 Codex-Assisted Full Audit", "",
        "> 边界：这是 Codex 独立复核辅助结果，不是独立人类金标准，不进入 P34 gate、Judge target 或 ReviewState admission。", "",
        "## 汇总", "",
        f"- 论文：`{report['paper_count']}`",
        f"- 正向证据：`{report['summary']['evidence_relation']}`",
        f"- 主张忠实度：`{report['summary']['claim_faithfulness']}`",
        f"- 负向缺陷：`{report['summary']['review_issue']}`",
        f"- 裁决来源：`{report['decision_source_counts']}`", "",
        "## 逐篇", "",
    ]
    for paper in report["papers"]:
        lines.extend([
            f"### {paper['paper_id']}", "", str(paper.get("paper_summary_zh") or ""), "",
            f"- 正向证据：`{paper['evidence_relation_counts']}`",
            f"- 主张：`{paper['claim_faithfulness_counts']}`",
            f"- 负向：`{paper['review_issue_counts']}`", "",
        ])
        for row in paper["tasks"]["review_issue"]:
            lines.append(f"- `{row['label']}` {row['canonical_issue_zh']}  ")
            lines.append(f"  来源：`{row['decision_source']}`；置信度：`{row['confidence']}`；理由：{row['reason_zh']}")
        lines.append("")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--independent", default="P34_FULL_AI_PILOT_INDEPENDENT_HARDNEG20_20260711.json")
    parser.add_argument("--pilot", default="P34_CODEX_PILOT_AUDIT_YE3NRNRYOY_20260711.json")
    parser.add_argument("--output-json", default="P34_CODEX_ASSISTED_AUDIT_HARDNEG20_20260711.json")
    parser.add_argument("--output-md", default="P34_CODEX_ASSISTED_AUDIT_HARDNEG20_20260711.md")
    args = parser.parse_args()
    report = build_report(_load(Path(args.independent)), _load(Path(args.pilot)))
    Path(args.output_json).write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    Path(args.output_md).write_text(render(report), encoding="utf-8")
    print(json.dumps({"status": report["status"], "paper_count": report["paper_count"], "summary": report["summary"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
