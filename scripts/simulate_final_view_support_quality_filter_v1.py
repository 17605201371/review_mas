#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple


CORE_WEAK_CRITERIA = {"technical_soundness", "empirical_adequacy"}


def read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_md(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def table_row(values: Iterable[Any]) -> str:
    return "| " + " | ".join(str(v).replace("\n", " ") for v in values) + " |"


def as_int(row: Dict[str, Any], key: str) -> int:
    try:
        return int(row.get(key) or 0)
    except (TypeError, ValueError):
        return 0


def grounded_empirical(row: Dict[str, Any]) -> bool:
    return bool(row.get("criterion_grounded_empirical")) and row.get("criterion_rating_empirical") in {
        "moderate_or_strong",
        "neutral_or_mentioned",
    }


def no_hard_negative(row: Dict[str, Any]) -> bool:
    return (
        as_int(row, "confirmed_critical_flaw_count") == 0
        and as_int(row, "grounded_major_flaw_count") == 0
        and not (set(row.get("grounded_weak_core_criteria") or []) & CORE_WEAK_CRITERIA)
        and as_int(row, "meta_leakage_count") == 0
    )


def sim4_accept(row: Dict[str, Any]) -> bool:
    return row.get("sim4_label") == "accept_like"


def positive_grounded_count(row: Dict[str, Any]) -> int:
    return len(row.get("positive_grounded_criteria") or [])


def rule_sim4(row: Dict[str, Any]) -> str:
    return "accept" if sim4_accept(row) else "reject"


def rule_nonabstract_independent(row: Dict[str, Any]) -> str:
    accept = (
        sim4_accept(row)
        and no_hard_negative(row)
        and as_int(row, "real_strong_support_total") >= 2
        and as_int(row, "non_abstract_support_total") >= 1
        and as_int(row, "independent_support_group_total") >= 2
        and positive_grounded_count(row) >= 1
    )
    return "accept" if accept else "reject"


def rule_two_positive_criteria(row: Dict[str, Any]) -> str:
    accept = (
        sim4_accept(row)
        and no_hard_negative(row)
        and as_int(row, "non_abstract_support_total") >= 1
        and as_int(row, "independent_support_group_total") >= 2
        and positive_grounded_count(row) >= 2
    )
    return "accept" if accept else "reject"


def rule_empirical_or_method_result(row: Dict[str, Any]) -> str:
    empirical_ok = as_int(row, "empirical_support_total") >= 1 or grounded_empirical(row)
    method_result_ok = as_int(row, "claims_with_method_plus_result_support") >= 1
    accept = (
        sim4_accept(row)
        and no_hard_negative(row)
        and as_int(row, "non_abstract_support_total") >= 1
        and as_int(row, "independent_support_group_total") >= 2
        and positive_grounded_count(row) >= 1
        and (empirical_ok or method_result_ok)
    )
    return "accept" if accept else "reject"


def rule_high_precision(row: Dict[str, Any]) -> str:
    accept = (
        sim4_accept(row)
        and no_hard_negative(row)
        and as_int(row, "non_abstract_support_total") >= 2
        and as_int(row, "independent_support_group_total") >= 2
        and positive_grounded_count(row) >= 2
        and (as_int(row, "empirical_support_total") >= 1 or grounded_empirical(row))
    )
    return "accept" if accept else "reject"


RULES = {
    "sim4_current_combined": rule_sim4,
    "sqf_nonabstract_independent": rule_nonabstract_independent,
    "sqf_two_positive_criteria": rule_two_positive_criteria,
    "sqf_empirical_or_method_result": rule_empirical_or_method_result,
    "sqf_high_precision": rule_high_precision,
}


def score(rows: List[Dict[str, Any]], rule_name: str) -> Dict[str, Any]:
    fn = RULES[rule_name]
    tp = tn = fp = fn_count = 0
    accept_ids: List[str] = []
    false_accept_ids: List[str] = []
    recovered_accept_ids: List[str] = []
    false_reject_ids: List[str] = []
    case_labels = []
    for row in rows:
        pred = fn(row)
        gold = str(row.get("gold_decision") or "").lower()
        pid = row.get("paper_id")
        if pred == "accept":
            accept_ids.append(pid)
        if gold == "accept" and pred == "accept":
            tp += 1
            recovered_accept_ids.append(pid)
        elif gold != "accept" and pred != "accept":
            tn += 1
        elif gold != "accept" and pred == "accept":
            fp += 1
            false_accept_ids.append(pid)
        else:
            fn_count += 1
            false_reject_ids.append(pid)
        case_labels.append({"paper_id": pid, "gold_decision": gold, "prediction": pred})
    total = len(rows) or 1
    precision_accept = tp / (tp + fp) if (tp + fp) else 0.0
    accept_recall = tp / (tp + fn_count) if (tp + fn_count) else 0.0
    reject_recall = tn / (tn + fp) if (tn + fp) else 0.0
    f1_accept = 2 * precision_accept * accept_recall / (precision_accept + accept_recall) if (precision_accept + accept_recall) else 0.0
    precision_reject = tn / (tn + fn_count) if (tn + fn_count) else 0.0
    f1_reject = 2 * precision_reject * reject_recall / (precision_reject + reject_recall) if (precision_reject + reject_recall) else 0.0
    return {
        "rule": rule_name,
        "accuracy": round((tp + tn) / total, 4),
        "macro_f1": round((f1_accept + f1_reject) / 2, 4),
        "predicted_accept_count": len(accept_ids),
        "true_accept_count": tp,
        "false_accept_count": fp,
        "false_reject_count": fn_count,
        "accept_recall": round(accept_recall, 4),
        "reject_recall": round(reject_recall, 4),
        "accept_precision": round(precision_accept, 4),
        "false_accept_ids": false_accept_ids,
        "recovered_accept_ids": recovered_accept_ids,
        "false_reject_ids": false_reject_ids,
    }


def render_schema() -> str:
    return """# Final-View Support Quality Filter v1 Schema

## 定位

本轮只做离线 final-view simulation，不改 runtime、不改 ReviewState、不改变已有 final report。

## 目的

前面的 negative blocker formation 在 false accept 上覆盖不足，因此本轮不再继续强造负面 blocker，而是检查是否可以通过更严格的正向证据质量过滤，减少 false accept。

## 输入信号

- `real_strong_support_total`
- `non_abstract_support_total`
- `independent_support_group_total`
- `empirical_support_total`
- `claims_with_method_plus_result_support`
- `positive_grounded_criteria`
- `confirmed_critical_flaw_count`
- `grounded_major_flaw_count`
- `grounded_weak_core_criteria`

## 规则边界

这些规则只用于论文分析和下一轮方向判断。不能直接作为 runtime accept/reject 规则。
"""


def render_results(scores: Dict[str, Dict[str, Any]]) -> str:
    lines = [
        "# Final-View Support Quality Filter v1 Simulation",
        "",
        table_row(["rule", "pred_accept", "true_accept", "false_accept", "false_reject", "accept_recall", "reject_recall", "macro_f1", "accuracy"]),
        table_row(["---", "---:", "---:", "---:", "---:", "---:", "---:", "---:", "---:"]),
    ]
    for name, result in scores.items():
        lines.append(
            table_row(
                [
                    name,
                    result["predicted_accept_count"],
                    result["true_accept_count"],
                    result["false_accept_count"],
                    result["false_reject_count"],
                    result["accept_recall"],
                    result["reject_recall"],
                    result["macro_f1"],
                    result["accuracy"],
                ]
            )
        )
    return "\n".join(lines)


def render_case_table(rows: List[Dict[str, Any]], labels: List[Dict[str, Any]]) -> str:
    label_map = {item["paper_id"]: item for item in labels}
    lines = [
        "# Final-View Support Quality Filter v1 Case Table",
        "",
        table_row(["paper_id", "gold", "high_precision_pred", "real_strong", "nonabs", "independent", "empirical", "positive_criteria", "grounded_weak_core"]),
        table_row(["---", "---", "---", "---:", "---:", "---:", "---:", "---", "---"]),
    ]
    for row in rows:
        pid = row["paper_id"]
        lines.append(
            table_row(
                [
                    pid,
                    row.get("gold_decision"),
                    label_map[pid]["prediction"],
                    as_int(row, "real_strong_support_total"),
                    as_int(row, "non_abstract_support_total"),
                    as_int(row, "independent_support_group_total"),
                    as_int(row, "empirical_support_total"),
                    ",".join(row.get("positive_grounded_criteria") or []),
                    ",".join(row.get("grounded_weak_core_criteria") or []),
                ]
            )
        )
    return "\n".join(lines)


def render_decision(scores: Dict[str, Dict[str, Any]]) -> str:
    hp = scores["sqf_high_precision"]
    best = max(scores.values(), key=lambda item: (item["macro_f1"], -item["false_accept_count"]))
    return f"""# Final-View Support Quality Filter v1 Decision

## 结论

本轮是离线模拟。它的作用是判断是否该把下一步从 negative blocker formation 转向 positive support sufficiency。

## 关键观察

- high_precision false_accept_count: `{hp['false_accept_count']}`
- high_precision recovered_accept_count: `{hp['true_accept_count']}`
- high_precision accept_recall: `{hp['accept_recall']}`
- high_precision reject_recall: `{hp['reject_recall']}`
- best_macro_f1_rule: `{best['rule']}`

## 判断

如果 stricter support quality filter 能显著降低 false accept，但 true accept 也被压得太低，说明当前不能直接 runtime 化 accept 规则。

下一步应做：

1. 保留 support quality 作为 final-view 诊断指标。
2. 继续把 `borderline / needs_human_review` 作为推荐层输出，而不是强行二分类。
3. 不再继续追求 negative blocker pass 覆盖所有 false accept；当前可见上下文不足以稳定确认这些 blocker。
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-json", default="outputs/results_main/review_infer/criterion_grounded_decision_sim_v1_9b_fulltest39_dryrun.json")
    parser.add_argument("--output-json", default="outputs/results_main/review_infer/final_view_support_quality_filter_v1_simulation.json")
    parser.add_argument("--doc-dir", default="docs/experiments/mainline_current")
    args = parser.parse_args()

    data = read_json(Path(args.input_json))
    rows = data.get("case_rows", [])
    scores = {name: score(rows, name) for name in RULES}
    labels = []
    hp_fn = RULES["sqf_high_precision"]
    for row in rows:
        labels.append({"paper_id": row["paper_id"], "gold_decision": row.get("gold_decision"), "prediction": hp_fn(row)})

    output = {"input_json": args.input_json, "rows": len(rows), "simulations": scores, "high_precision_case_labels": labels}
    write_json(Path(args.output_json), output)
    doc_dir = Path(args.doc_dir)
    write_md(doc_dir / "FINAL_VIEW_SUPPORT_QUALITY_FILTER_V1_SCHEMA.md", render_schema())
    write_md(doc_dir / "FINAL_VIEW_SUPPORT_QUALITY_FILTER_V1_SIMULATION.md", render_results(scores))
    write_md(doc_dir / "FINAL_VIEW_SUPPORT_QUALITY_FILTER_V1_CASE_TABLE.md", render_case_table(rows, labels))
    write_md(doc_dir / "FINAL_VIEW_SUPPORT_QUALITY_FILTER_V1_DECISION.md", render_decision(scores))
    print(json.dumps({"output_json": args.output_json, "rows": len(rows), "best_rule": max(scores.values(), key=lambda item: (item["macro_f1"], -item["false_accept_count"]))["rule"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
