#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence


def read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_md(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def md_table(headers: Sequence[str], rows: Sequence[Sequence[Any]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(value).replace("\n", " ") for value in row) + " |")
    return "\n".join(lines)


def taxonomy(row: Dict[str, Any]) -> str:
    if row["gold_decision"] == "reject" and row["support_quality_label"] == "accept_like_valid_support":
        if row["empirical_valid_real_support"] == 0:
            return "false_accept_valid_but_non_empirical_support"
        if row["grounded_major_flaw_count"] > 0:
            return "false_accept_support_ignores_grounded_flaw"
        return "false_accept_support_not_paper_level_sufficient"
    if row["gold_decision"] == "accept" and row["support_quality_label"] == "accept_like_valid_support":
        return "recovered_accept_valid_support"
    if row["gold_decision"] == "accept" and row["valid_real_strong_support"] == 0:
        return "false_reject_no_valid_real_support"
    if row["gold_decision"] == "accept" and row["valid_real_strong_support"] > 0:
        if row["non_abstract_valid_real_support"] == 0:
            return "false_reject_support_abstract_or_unknown_only"
        if row["independent_valid_real_support_groups"] < 2:
            return "false_reject_insufficient_independent_support"
        if row["empirical_valid_real_support"] == 0:
            return "false_reject_missing_empirical_support"
        return "false_reject_valid_support_but_negative_burden"
    if row["support_quality_label"] == "not_assessable_invalid_support_only":
        return "not_assessable_invalid_support_only"
    if row["support_quality_label"] == "borderline_valid_support":
        return "borderline_valid_support"
    return row["support_quality_label"]


def render_case_study(rows: List[Dict[str, Any]], strict: Dict[str, Any]) -> str:
    focus_ids = set(strict.get("false_accept_ids", []) + strict.get("recovered_accept_ids", []) + strict.get("false_reject_ids", [])[:8])
    focus = [row for row in rows if row["paper_id"] in focus_ids]
    table_rows = []
    for row in focus:
        table_rows.append(
            [
                row["paper_id"],
                row["gold_decision"],
                row["current_decision"],
                row["support_quality_label"],
                taxonomy(row),
                row["valid_real_strong_support"],
                row["non_abstract_valid_real_support"],
                row["empirical_valid_real_support"],
                row["independent_valid_real_support_groups"],
                row["grounded_major_flaw_count"],
                row["unresolved_count"],
                row["evidence_gap_count"],
            ]
        )
    return (
        "# Mainline-Final-v1 Case Study Pack\n\n"
        "## 定位\n\n"
        "本文件解释 final-view invalid-binding/support-quality 过滤后的关键样本。它不用于调 runtime，也不作为 final decision 规则。\n\n"
        "## 重点样本\n\n"
        + md_table(
            [
                "paper_id",
                "gold",
                "current",
                "view_label",
                "taxonomy",
                "valid_real_strong",
                "nonabs",
                "empirical",
                "ind_groups",
                "grounded_major",
                "unresolved",
                "gaps",
            ],
            table_rows,
        )
        + "\n\n## 读法\n\n"
        "- `recovered_accept_valid_support` 表示当前 final-view 能恢复的 accept，但仍需要人工 case study 确认其 support 是否 paper-level sufficient。\n"
        "- `false_accept_*` 表示 strong support 虽然 valid-looking，但不能自动推出 paper-level accept。\n"
        "- `false_reject_*` 表示 gold accept 未恢复的主因：没有 valid real support、support 太浅、独立性不足、缺 empirical support，或负面 burden 仍过强。\n"
    )


def render_taxonomy(rows: List[Dict[str, Any]]) -> str:
    counts = Counter(taxonomy(row) for row in rows)
    count_rows = [[name, count] for name, count in counts.most_common()]
    gold_accept_rows = [row for row in rows if row["gold_decision"] == "accept"]
    reject_rows = [row for row in rows if row["gold_decision"] == "reject"]
    return (
        "# Mainline-Final-v1 Failure Taxonomy\n\n"
        "## Taxonomy 分布\n\n"
        + md_table(["taxonomy", "count"], count_rows)
        + "\n\n## Accept 样本状态\n\n"
        + md_table(
            ["metric", "value"],
            [
                ["gold_accept_count", len(gold_accept_rows)],
                ["accept_with_valid_real_strong", sum(row["valid_real_strong_support"] > 0 for row in gold_accept_rows)],
                ["accept_with_2plus_valid_real_strong", sum(row["valid_real_strong_support"] >= 2 for row in gold_accept_rows)],
                ["accept_with_nonabs_support", sum(row["non_abstract_valid_real_support"] > 0 for row in gold_accept_rows)],
                ["accept_with_empirical_support", sum(row["empirical_valid_real_support"] > 0 for row in gold_accept_rows)],
                ["accept_with_2plus_independent_groups", sum(row["independent_valid_real_support_groups"] >= 2 for row in gold_accept_rows)],
            ],
        )
        + "\n\n## Reject 样本风险\n\n"
        + md_table(
            ["metric", "value"],
            [
                ["gold_reject_count", len(reject_rows)],
                ["reject_with_accept_like_valid_support", sum(row["support_quality_label"] == "accept_like_valid_support" for row in reject_rows)],
                ["reject_with_borderline_valid_support", sum(row["support_quality_label"] == "borderline_valid_support" for row in reject_rows)],
                ["reject_with_empirical_support", sum(row["empirical_valid_real_support"] > 0 for row in reject_rows)],
                ["reject_with_2plus_independent_groups", sum(row["independent_valid_real_support_groups"] >= 2 for row in reject_rows)],
            ],
        )
        + "\n\n## 结论\n\n"
        "当前主瓶颈不再是 fallback strong support，而是 valid-looking support 是否真正达到 paper-level sufficiency。下一步论文主结果应把 false accept/false reject 分解为 support depth、independence、empirical adequacy 和 grounded flaw 四类，而不是继续调 accept/reject 阈值。\n"
    )


def render_decision(summary: Dict[str, Any], rows: List[Dict[str, Any]]) -> str:
    strict = summary["strict"]
    counts = Counter(taxonomy(row) for row in rows)
    return f"""# Mainline-Final-v1 Case Study Next Step

## 当前判断

当前已经不适合继续做 runtime controller。`Evidence ID Turn-Scoping v1` 应保留；`Claim Binding Guard v1` 不应保留；`Final-View Invalid Binding Filter v1` 应作为离线分析层保留。

## 为什么不继续调 final decision

strict support-quality view 恢复 `{len(strict['recovered_accept_ids'])}` 个 accept，但产生 `{len(strict['false_accept_ids'])}` 个 false accept。说明现在的关键不是简单放宽或收紧阈值，而是解释哪些 support 真正 paper-level sufficient。

## 当前主要 failure taxonomy

{md_table(['taxonomy', 'count'], [[k, v] for k, v in counts.most_common()])}

## 下一步

下一步应进入论文结果收口：

1. 固定 `Evidence ID Turn-Scoping v1` 作为 runtime 保留组件。
2. 将 invalid-binding / support-quality / criterion-grounding 作为 final-view 诊断指标写入主实验表。
3. 用 case study 解释 recovered accept、false accept 和 false reject 的机制。
4. 不再新增 sticky/throttle/gate 或 live state hygiene mutation。
5. 若还要跑实验，应只做最终 9B confirmation 或论文主表复现实验，不再大改框架。
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-json", type=Path, required=True)
    parser.add_argument("--doc-dir", type=Path, default=Path("docs/experiments/mainline_current"))
    args = parser.parse_args()
    data = read_json(args.input_json)
    rows = data.get("case_rows", [])
    for row in rows:
        row["taxonomy"] = taxonomy(row)
    args.doc_dir.mkdir(parents=True, exist_ok=True)
    write_md(args.doc_dir / "MAINLINE_FINAL_V1_CASE_STUDY_PACK.md", render_case_study(rows, data["strict"]))
    write_md(args.doc_dir / "MAINLINE_FINAL_V1_FAILURE_TAXONOMY.md", render_taxonomy(rows))
    write_md(args.doc_dir / "MAINLINE_FINAL_V1_CASE_STUDY_NEXT_STEP.md", render_decision(data, rows))
    print(json.dumps({"rows": len(rows), "taxonomy": Counter(row["taxonomy"] for row in rows)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
