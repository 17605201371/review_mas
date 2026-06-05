#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List


def read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_md(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def table_row(values: Iterable[Any]) -> str:
    return "| " + " | ".join(str(v).replace("\n", " ") for v in values) + " |"


def metric_count(payload: Dict[str, Any], count_key: str, ids_key: str) -> Any:
    if payload.get(count_key) is not None:
        return payload.get(count_key)
    if isinstance(payload.get(ids_key), list):
        return len(payload.get(ids_key) or [])
    return None


def pick_cases(rows: List[Dict[str, Any]], label: str, gold: str | None = None, limit: int = 3) -> List[Dict[str, Any]]:
    out = []
    for row in rows:
        if row.get("recommendation_view") != label:
            continue
        if gold and row.get("gold_decision") != gold:
            continue
        out.append(row)
    return out[:limit]


def render_main_results(unified: Dict[str, Any], metric_audit: Dict[str, Any]) -> str:
    runtime = unified.get("runtime_health", {})
    support = unified.get("support_state", {})
    sim4 = unified.get("criterion_sim4", {})
    neg = unified.get("negative_anchor_confirmation", {})
    sq2 = unified.get("support_filter_two_positive", {})
    sqhp = unified.get("support_filter_high_precision", {})
    rec = unified.get("final_recommendation_view_counts", {})
    lines = [
        "# Paper Main Results Table v1",
        "",
        "## 论文主线定位",
        "",
        "本表用于论文主结果草稿。核心结论不是模型已经解决二分类 accept/reject，而是系统能把 runtime state、support quality、criterion grounding 和 final-view recommendation 分层诊断出来。",
        "",
        "## Main Results",
        "",
        table_row(["component", "metric", "value", "interpretation"]),
        table_row(["---", "---", "---:", "---"]),
        table_row(["Runtime health", "runtime reject", (runtime.get("runtime_final_decision_counts") or {}).get("reject", 0), "runtime final decision 仍然 collapse，不能作为唯一主指标"]),
        table_row(["Runtime health", "avg reward", runtime.get("avg_reward"), "仅作为辅助信号"]),
        table_row(["Support state", "decision real strong", support.get("real_strong_support_total"), "真实 claim strong support，排除 fallback/general claim"]),
        table_row(["Support state", "non-abstract strong", support.get("non_abstract_support_total"), "比 abstract-only 更接近论文证据"]),
        table_row(["Support state", "empirical strong", support.get("empirical_support_total"), "结果/实验类证据仍不足"]),
        table_row(["Support state", "raw fallback strong excluded", support.get("fallback_strong_support_total"), "raw state 残留，已从 final-view recommendation 排除"]),
        table_row(["Criterion Sim4", "predicted accept", sim4.get("predicted_accept_count"), "二分类映射召回有限且 false accept 高"]),
        table_row(["Criterion Sim4", "false accept", metric_count(sim4, "false_accept_count", "false_accept_ids"), "说明不能直接宽松映射 accept"]),
        table_row(["Negative anchor", "false accept trusted blockers", (neg.get("false_accept") or {}).get("trusted_blocker_rows"), "负向 blocker formation 覆盖不足"]),
        table_row(["Negative anchor", "recovered accept trusted blockers", (neg.get("recovered_accept") or {}).get("trusted_blocker_rows"), "仍有误伤风险"]),
        table_row(["Support filter", "high precision false accept", sqhp.get("false_accept_count"), "高精度可行但召回低"]),
        table_row(["Support filter", "high precision true accept", sqhp.get("true_accept_count"), "只恢复少量 accept"]),
        table_row(["Recommendation view", "accept_like", rec.get("accept_like", 0), "高精度正向推荐"]),
        table_row(["Recommendation view", "borderline_positive", rec.get("borderline_positive", 0), "有正向信号但不应硬 accept"]),
        table_row(["Recommendation view", "not_assessable", rec.get("not_assessable", 0), "证据不足时诚实表达不确定性"]),
        table_row(["Metric consistency", "accept_like rows with fallback strong", len(metric_audit.get("accept_like_rows_with_raw_fallback_strong") or []), "确认 fallback raw 残留未污染 accept_like"]),
        "",
        "## 写论文时的核心表述",
        "",
        "1. `accept/reject` 作为 health check，显示传统 final decision 层存在 collapse。",
        "2. `Final Recommendation View` 作为主输出，更符合审稿辅助系统定位。",
        "3. raw fallback-bound support 保留为污染诊断指标，但不进入 decision-eligible support。",
        "4. 当前系统能产生高精度 `accept_like`，但大量样本仍应标为 borderline 或 not_assessable。",
    ]
    return "\n".join(lines)


def render_casebook(rec_rows: List[Dict[str, Any]]) -> str:
    sections = [
        ("Accept-like true accept", pick_cases(rec_rows, "accept_like", "accept", 3)),
        ("Borderline positive gold accept", pick_cases(rec_rows, "borderline_positive", "accept", 4)),
        ("Borderline positive gold reject", pick_cases(rec_rows, "borderline_positive", "reject", 5)),
        ("Not assessable gold accept", pick_cases(rec_rows, "not_assessable", "accept", 4)),
        ("Reject-like gold reject", pick_cases(rec_rows, "reject_like", "reject", 3)),
    ]
    lines = [
        "# Final Recommendation Casebook v1",
        "",
        "## 用途",
        "",
        "本 casebook 用于论文写作：说明为什么多类 recommendation view 比硬二分类更合适。",
        "",
    ]
    for title, rows in sections:
        lines += [
            f"## {title}",
            "",
            table_row(["paper_id", "gold", "recommendation", "real_strong", "nonabs", "independent", "empirical", "positive_criteria", "hard_negative"]),
            table_row(["---", "---", "---", "---:", "---:", "---:", "---:", "---", "---"]),
        ]
        for row in rows:
            lines.append(
                table_row(
                    [
                        row.get("paper_id"),
                        row.get("gold_decision"),
                        row.get("recommendation_view"),
                        row.get("real_strong_support_total"),
                        row.get("non_abstract_support_total"),
                        row.get("independent_support_group_total"),
                        row.get("empirical_support_total"),
                        ",".join(row.get("positive_grounded_criteria") or []),
                        row.get("has_hard_negative"),
                    ]
                )
            )
        lines.append("")
    return "\n".join(lines)


def render_negative_findings() -> str:
    return """# Paper Negative Findings Summary v1

## 负结果 1：后置 controller 不能解决主问题

sticky / throttle / progression gate 多轮实验显示，坏路径通常在 target/evidence/state 更早阶段已经形成。继续叠 controller 容易带来 regression，不适合作为主线。

## 负结果 2：强造 negative blocker 覆盖不足

`Negative Evidence Anchor Extraction v1` 能抽到正文锚点，但 `Anchor Confirmation Pass v1` 在 false accept 上没有形成 trusted blocker，反而误伤 recovered accept。这说明当前 evidence visibility 和 4B confirmation 能力不足以支撑 hard reject blocker。

## 负结果 3：硬二分类会掩盖系统不确定性

criterion/support-based accept 规则可以恢复部分 accept，但 false accept 风险明显；高精度 support filter 可降低 false accept，但召回过低。多类 final-view recommendation 比硬二分类更适合当前论文定位。

## 负结果 4：raw state 仍有 fallback 残留

raw ReviewState 中仍存在 fallback-bound strong support，但 final-view recommendation 已将其排除。论文中应明确区分 raw diagnostic state 和 decision-eligible derived view。
"""


def render_next_decision() -> str:
    return """# Paper Next Experiment Decision v1

## 当前判断

当前已经进入论文主线收口阶段，不应再继续新增 controller。下一步应围绕 `Mainline-Final-v1` 做论文表格、case study 和小范围确认。

## 下一步唯一建议

做 `Paper Result Pack v1` 的人工/脚本化整理：

1. 主表：runtime health、support state、criterion grounding、recommendation view。
2. Casebook：每类 recommendation 选择代表样本。
3. Negative findings：sticky/throttle/negative blocker/live hygiene 的限制。
4. 写作草稿：把系统定位为 evidence-grounded review assistance，而不是黑箱 accept/reject classifier。

## 暂时不做

- 不跑新的 9B full experiment。
- 不调 final decision 阈值。
- 不把 criterion 分数直接接入 decision。
- 不继续 sticky / throttle / progression gate。
- 不继续 negative blocker formation pass。
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--unified-json", type=Path, default=Path("outputs/results_main/review_infer/mainline_final_v1_unified_results.json"))
    parser.add_argument("--metric-audit-json", type=Path, default=Path("outputs/results_main/review_infer/mainline_final_v1_metric_consistency_audit.json"))
    parser.add_argument("--recommendation-json", type=Path, default=Path("outputs/results_main/review_infer/final_recommendation_view_v1_simulation.json"))
    parser.add_argument("--doc-dir", type=Path, default=Path("docs/experiments/mainline_current"))
    args = parser.parse_args()

    unified = read_json(args.unified_json)
    metric_audit = read_json(args.metric_audit_json)
    rec_rows = read_json(args.recommendation_json).get("case_rows", [])

    write_md(args.doc_dir / "PAPER_MAIN_RESULTS_TABLE_V1.md", render_main_results(unified, metric_audit))
    write_md(args.doc_dir / "FINAL_RECOMMENDATION_CASEBOOK_V1.md", render_casebook(rec_rows))
    write_md(args.doc_dir / "PAPER_NEGATIVE_FINDINGS_SUMMARY_V1.md", render_negative_findings())
    write_md(args.doc_dir / "PAPER_NEXT_EXPERIMENT_DECISION_V1.md", render_next_decision())
    print(json.dumps({"docs": [
        "PAPER_MAIN_RESULTS_TABLE_V1.md",
        "FINAL_RECOMMENDATION_CASEBOOK_V1.md",
        "PAPER_NEGATIVE_FINDINGS_SUMMARY_V1.md",
        "PAPER_NEXT_EXPERIMENT_DECISION_V1.md",
    ]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
