#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Iterable


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_md(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def table_row(values: Iterable[Any]) -> str:
    return "| " + " | ".join(str(v).replace("\n", " ") for v in values) + " |"


def metric_rows(title: str, rows: list[list[Any]]) -> str:
    lines = [f"## {title}", "", table_row(["metric", "value"]), table_row(["---", "---:"])]
    lines.extend(table_row(row) for row in rows)
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mainline-summary", type=Path, default=Path("outputs/results_main/review_infer/mainline_final_v1_9b_fulltest39_dryrun_summary.json"))
    parser.add_argument("--criterion-sim", type=Path, default=Path("outputs/results_main/review_infer/criterion_grounded_decision_sim_v1_9b_fulltest39_dryrun.json"))
    parser.add_argument("--negative-anchor", type=Path, default=Path("outputs/results_main/review_infer/negative_evidence_anchor_confirmation_pass_v1_4b_diagnostic10_summary.json"))
    parser.add_argument("--support-filter", type=Path, default=Path("outputs/results_main/review_infer/final_view_support_quality_filter_v1_simulation.json"))
    parser.add_argument("--recommendation-view", type=Path, default=Path("outputs/results_main/review_infer/final_recommendation_view_v1_simulation.json"))
    parser.add_argument("--output-json", type=Path, default=Path("outputs/results_main/review_infer/mainline_final_v1_unified_results.json"))
    parser.add_argument("--doc-dir", type=Path, default=Path("docs/experiments/mainline_current"))
    args = parser.parse_args()

    mainline = read_json(args.mainline_summary)
    criterion = read_json(args.criterion_sim)
    negative = read_json(args.negative_anchor)
    support = read_json(args.support_filter)
    rec = read_json(args.recommendation_view)

    feature_totals = mainline.get("feature_totals", {})
    sim4_payload = (criterion.get("simulations") or {}).get("sim4_combined_criterion_support_hygiene", {})
    sim4 = sim4_payload.get("strict", sim4_payload) if isinstance(sim4_payload, dict) else {}
    support_sims = support.get("simulations", {})
    high_precision = support_sims.get("sqf_high_precision", {})
    two_positive = support_sims.get("sqf_two_positive_criteria", {})
    rec_counts = rec.get("label_counts", {})
    neg_groups = negative.get("group_summaries", {})

    unified = {
        "source_files": {
            "mainline_summary": str(args.mainline_summary),
            "criterion_sim": str(args.criterion_sim),
            "negative_anchor": str(args.negative_anchor),
            "support_filter": str(args.support_filter),
            "recommendation_view": str(args.recommendation_view),
        },
        "runtime_health": {
            "rows": mainline.get("rows"),
            "gold_counts": mainline.get("gold_counts", {}),
            "runtime_final_decision_counts": mainline.get("original_final_decision_counts", {}),
            "avg_reward": mainline.get("avg_reward"),
        },
        "support_state": feature_totals,
        "criterion_sim4": sim4,
        "negative_anchor_confirmation": neg_groups,
        "support_filter_high_precision": high_precision,
        "support_filter_two_positive": two_positive,
        "final_recommendation_view_counts": rec_counts,
        "decision": "ready_for_paper_level_dry_run_table_not_formal_binary_main_experiment",
    }
    write_json(args.output_json, unified)

    sections = [
        "# Mainline-Final-v1 Unified Results Table",
        "",
        "## 总结",
        "",
        "这份表汇总当前 `Mainline-Final-v1` 预跑结果。它不是正式二分类主实验结论，而是论文主线收口表：runtime final decision 作为 health check，final-view recommendation 作为更可信的诊断输出。",
        "",
        metric_rows(
            "Runtime Health",
            [
                ["rows", mainline.get("rows")],
                ["gold_accept", (mainline.get("gold_counts") or {}).get("accept", 0)],
                ["gold_reject", (mainline.get("gold_counts") or {}).get("reject", 0)],
                ["runtime_accept", (mainline.get("original_final_decision_counts") or {}).get("accept", 0)],
                ["runtime_reject", (mainline.get("original_final_decision_counts") or {}).get("reject", 0)],
                ["avg_reward", mainline.get("avg_reward")],
            ],
        ),
        "",
        metric_rows(
            "Evidence / Support State",
            [
                ["real_strong_support_total", feature_totals.get("real_strong_support_total")],
                ["non_abstract_support_total", feature_totals.get("non_abstract_support_total")],
                ["empirical_support_total", feature_totals.get("empirical_support_total")],
                ["raw_fallback_strong_support_excluded", feature_totals.get("fallback_strong_support_total")],
                ["rows_with_2plus_real_strong", feature_totals.get("rows_with_2plus_real_strong")],
                ["rows_with_2plus_nonabstract", feature_totals.get("rows_with_2plus_nonabstract")],
            ],
        ),
        "",
        "说明：`raw_fallback_strong_support_excluded` 是 raw ReviewState 中的 fallback-bound strong support 残留，只作为污染诊断指标；final-view recommendation 不把它计入 decision-eligible support。",
        "",
        metric_rows(
            "Criterion Sim4 Combined Rule",
            [
                ["predicted_accept_count", sim4.get("predicted_accept_count")],
                ["recovered_accept_count", len(sim4.get("recovered_accept_ids") or [])],
                ["false_accept_count", len(sim4.get("false_accept_ids") or [])],
                ["accept_recall", sim4.get("accept_recall")],
                ["reject_recall", sim4.get("reject_recall")],
                ["macro_f1", sim4.get("macro_f1")],
            ],
        ),
        "",
        metric_rows(
            "Negative Anchor Confirmation",
            [
                ["false_accept_trusted_blocker_rows", (neg_groups.get("false_accept") or {}).get("trusted_blocker_rows")],
                ["recovered_accept_trusted_blocker_rows", (neg_groups.get("recovered_accept") or {}).get("trusted_blocker_rows")],
                ["parse_error_rows_total", negative.get("parse_error_rows_total")],
            ],
        ),
        "",
        metric_rows(
            "Support Quality Filters",
            [
                ["two_positive_pred_accept", two_positive.get("predicted_accept_count")],
                ["two_positive_true_accept", two_positive.get("true_accept_count")],
                ["two_positive_false_accept", two_positive.get("false_accept_count")],
                ["high_precision_pred_accept", high_precision.get("predicted_accept_count")],
                ["high_precision_true_accept", high_precision.get("true_accept_count")],
                ["high_precision_false_accept", high_precision.get("false_accept_count")],
            ],
        ),
        "",
        metric_rows(
            "Final Recommendation View",
            [
                ["accept_like", rec_counts.get("accept_like", 0)],
                ["borderline_positive", rec_counts.get("borderline_positive", 0)],
                ["borderline_insufficient", rec_counts.get("borderline_insufficient", 0)],
                ["reject_like", rec_counts.get("reject_like", 0)],
                ["not_assessable", rec_counts.get("not_assessable", 0)],
            ],
        ),
        "",
        "## 当前决策",
        "",
        "- 不继续调 runtime accept/reject 阈值。",
        "- 不继续 sticky/throttle/progression gate。",
        "- 不继续强造 negative blocker。",
        "- 下一阶段应将 `Final Recommendation View v1` 纳入论文主表和 final report 展示层。",
    ]
    write_md(args.doc_dir / "MAINLINE_FINAL_V1_UNIFIED_RESULTS_TABLE.md", "\n".join(sections))
    print(json.dumps({"output_json": str(args.output_json), "doc": str(args.doc_dir / "MAINLINE_FINAL_V1_UNIFIED_RESULTS_TABLE.md")}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
