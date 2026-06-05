#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Sequence, Tuple

CORE_WEAK_CRITERIA = {"technical_soundness", "empirical_adequacy"}
DATASETS = {
    "4b_mainline_fulltest39": Path("outputs/results_main/review_infer/criterion_grounded_decision_sim_v1_mainline_fulltest39.json"),
    "9b_fulltest39_dryrun": Path("outputs/results_main/review_infer/criterion_grounded_decision_sim_v1_9b_fulltest39_dryrun.json"),
}


def read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_md(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def md_table(headers: Sequence[str], rows: Sequence[Sequence[Any]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(value).replace("\n", " ") for value in row) + " |")
    return "\n".join(lines)


def as_int(row: Dict[str, Any], key: str) -> int:
    try:
        return int(row.get(key) or 0)
    except (TypeError, ValueError):
        return 0


def positive_count(row: Dict[str, Any]) -> int:
    return len(row.get("positive_grounded_criteria") or [])


def has_grounded_positive(row: Dict[str, Any], criterion: str) -> bool:
    return bool(row.get(f"criterion_grounded_{criterion}")) and row.get(f"criterion_rating_{criterion}") == "moderate_or_strong"


def has_core_weak(row: Dict[str, Any]) -> bool:
    return bool(set(row.get("grounded_weak_core_criteria") or []) & CORE_WEAK_CRITERIA)


def no_hard_negative(row: Dict[str, Any]) -> bool:
    return (
        as_int(row, "confirmed_critical_flaw_count") == 0
        and as_int(row, "grounded_major_flaw_count") == 0
        and not has_core_weak(row)
    )


def no_negative_evidence(row: Dict[str, Any]) -> bool:
    return as_int(row, "negative_evidence_total") == 0


def support_quality_base(row: Dict[str, Any]) -> bool:
    return (
        as_int(row, "real_strong_support_total") >= 2
        and as_int(row, "non_abstract_support_total") >= 1
        and as_int(row, "independent_support_group_total") >= 2
        and positive_count(row) >= 2
    )


def empirical_or_empirical_criterion(row: Dict[str, Any]) -> bool:
    return as_int(row, "empirical_support_total") >= 1 or has_grounded_positive(row, "empirical")


def current_runtime(row: Dict[str, Any]) -> str:
    return "accept" if str(row.get("current_decision") or "").lower() == "accept" else "reject"


def support_count(row: Dict[str, Any]) -> str:
    return "accept" if as_int(row, "real_strong_support_total") >= 2 else "reject"


def sim4_accept_like(row: Dict[str, Any]) -> str:
    return "accept" if row.get("sim4_label") == "accept_like" else "reject"


def calibrated_balanced(row: Dict[str, Any]) -> str:
    accept = (
        row.get("sim4_label") in {"accept_like", "borderline"}
        and no_hard_negative(row)
        and no_negative_evidence(row)
        and support_quality_base(row)
    )
    return "accept" if accept else "reject"


def calibrated_high_precision(row: Dict[str, Any]) -> str:
    accept = (
        row.get("sim4_label") in {"accept_like", "borderline"}
        and no_hard_negative(row)
        and no_negative_evidence(row)
        and support_quality_base(row)
        and empirical_or_empirical_criterion(row)
    )
    return "accept" if accept else "reject"


def calibrated_three_way(row: Dict[str, Any]) -> str:
    if calibrated_high_precision(row) == "accept":
        return "accept_like"
    if calibrated_balanced(row) == "accept":
        return "borderline_positive"
    if row.get("sim4_label") == "not_assessable":
        return "not_assessable"
    if row.get("sim4_label") == "borderline":
        return "borderline_insufficient"
    return "reject_like"


BINARY_RULES: Dict[str, Callable[[Dict[str, Any]], str]] = {
    "current_runtime": current_runtime,
    "support_count_real_ge2": support_count,
    "sim4_accept_like": sim4_accept_like,
    "calibrated_balanced": calibrated_balanced,
    "calibrated_high_precision": calibrated_high_precision,
}


def score_binary(rows: List[Dict[str, Any]], rule_name: str, fn: Callable[[Dict[str, Any]], str]) -> Dict[str, Any]:
    tp = tn = fp = fn_count = 0
    false_accept_ids: List[str] = []
    recovered_accept_ids: List[str] = []
    false_reject_ids: List[str] = []
    predicted_accept_ids: List[str] = []
    for row in rows:
        pred = fn(row)
        gold_accept = str(row.get("gold_decision") or "").lower() == "accept"
        pid = row.get("paper_id")
        if pred == "accept":
            predicted_accept_ids.append(pid)
        if pred == "accept" and gold_accept:
            tp += 1
            recovered_accept_ids.append(pid)
        elif pred == "accept" and not gold_accept:
            fp += 1
            false_accept_ids.append(pid)
        elif pred != "accept" and gold_accept:
            fn_count += 1
            false_reject_ids.append(pid)
        else:
            tn += 1
    total = len(rows) or 1
    accept_precision = tp / (tp + fp) if (tp + fp) else 0.0
    accept_recall = tp / (tp + fn_count) if (tp + fn_count) else 0.0
    reject_recall = tn / (tn + fp) if (tn + fp) else 0.0
    reject_precision = tn / (tn + fn_count) if (tn + fn_count) else 0.0
    accept_f1 = 2 * accept_precision * accept_recall / (accept_precision + accept_recall) if (accept_precision + accept_recall) else 0.0
    reject_f1 = 2 * reject_precision * reject_recall / (reject_precision + reject_recall) if (reject_precision + reject_recall) else 0.0
    return {
        "rule": rule_name,
        "predicted_accept_count": len(predicted_accept_ids),
        "true_accept_count": tp,
        "false_accept_count": fp,
        "false_reject_count": fn_count,
        "accuracy": round((tp + tn) / total, 4),
        "macro_f1": round((accept_f1 + reject_f1) / 2, 4),
        "accept_precision": round(accept_precision, 4),
        "accept_recall": round(accept_recall, 4),
        "reject_recall": round(reject_recall, 4),
        "predicted_accept_ids": predicted_accept_ids,
        "recovered_accept_ids": recovered_accept_ids,
        "false_accept_ids": false_accept_ids,
        "false_reject_ids": false_reject_ids,
    }


def score_three_way(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    labels: Dict[str, int] = {}
    case_rows = []
    strict_rows = []
    lenient_rows = []
    for row in rows:
        label = calibrated_three_way(row)
        labels[label] = labels.get(label, 0) + 1
        binary_strict = "accept" if label == "accept_like" else "reject"
        binary_lenient = "accept" if label in {"accept_like", "borderline_positive"} else "reject"
        strict_rows.append({**row, "_pred": binary_strict})
        lenient_rows.append({**row, "_pred": binary_lenient})
        case_rows.append({
            "paper_id": row.get("paper_id"),
            "gold_decision": row.get("gold_decision"),
            "three_way_label": label,
            "strict_binary": binary_strict,
            "lenient_binary": binary_lenient,
            "real_strong_support_total": as_int(row, "real_strong_support_total"),
            "non_abstract_support_total": as_int(row, "non_abstract_support_total"),
            "empirical_support_total": as_int(row, "empirical_support_total"),
            "independent_support_group_total": as_int(row, "independent_support_group_total"),
            "positive_grounded_criteria": row.get("positive_grounded_criteria") or [],
            "sim4_label": row.get("sim4_label"),
            "negative_evidence_total": as_int(row, "negative_evidence_total"),
            "grounded_major_flaw_count": as_int(row, "grounded_major_flaw_count"),
        })

    def pred_from_tmp(tmp_row: Dict[str, Any]) -> str:
        return tmp_row["_pred"]

    return {
        "label_counts": labels,
        "strict_mapping": score_binary(strict_rows, "calibrated_three_way_strict", pred_from_tmp),
        "lenient_mapping": score_binary(lenient_rows, "calibrated_three_way_lenient", pred_from_tmp),
        "case_rows": case_rows,
    }


def render_schema() -> str:
    return """# Final Recommendation Calibration v1 Schema

## 目标

本轮弥补 runtime accept collapse，但不直接改 runtime。校准只发生在 final-view / offline 层，用已有 support quality、criterion grounding、flaw lifecycle 信息重新聚合 recommendation。

## 为什么不能只调 strong support 数量

`real_strong_support_total >= 2` 会恢复更多 accept，但在 9B fulltest39 上会产生大量 false accept。原因是 strong support 仍可能只是局部 claim 成立，不等于 paper-level accept。

## 两个校准口径

### calibrated_high_precision

用于高精度 `accept_like`：

- `sim4_label` 为 `accept_like` 或 `borderline`；
- 无 confirmed critical flaw、grounded major flaw、core weak criterion；
- 无 negative evidence；
- real strong support >= 2；
- non-abstract support >= 1；
- independent support groups >= 2；
- positive grounded criteria >= 2；
- empirical support >= 1 或 empirical criterion grounded positive。

### calibrated_balanced

用于召回更多潜在 accept，但风险较高：

- 满足 high precision 的所有条件，除了 empirical support / empirical criterion 约束。

### calibrated_three_way

- high_precision 通过 -> `accept_like`；
- balanced 通过但 high_precision 不通过 -> `borderline_positive`；
- 其余按 not_assessable / borderline_insufficient / reject_like 保留。

## 使用边界

`calibrated_balanced` 不能直接作为正式 accept 规则；它用于发现 borderline positive。正式论文主口径应优先使用 `calibrated_three_way`。二分类 accuracy 只作为 health check。
"""


def render_results(summary: Dict[str, Any]) -> str:
    lines = ["# Final Recommendation Calibration v1 Results", ""]
    for dataset, payload in summary["datasets"].items():
        lines += [f"## {dataset}", ""]
        rows = []
        for rule, result in payload["binary_rules"].items():
            rows.append([
                rule,
                result["predicted_accept_count"],
                result["true_accept_count"],
                result["false_accept_count"],
                result["accept_precision"],
                result["accept_recall"],
                result["reject_recall"],
                result["macro_f1"],
                result["accuracy"],
            ])
        lines.append(md_table(["rule", "pred_accept", "true_accept", "false_accept", "accept_precision", "accept_recall", "reject_recall", "macro_f1", "accuracy"], rows))
        lines += ["", "### Three-way view", ""]
        tw = payload["three_way"]
        lines.append(md_table(["label", "count"], sorted(tw["label_counts"].items())))
        lines += ["", "### 推荐读法", ""]
        hp = payload["binary_rules"]["calibrated_high_precision"]
        bal = payload["binary_rules"]["calibrated_balanced"]
        lines.append(f"- high precision: recovered `{len(hp['recovered_accept_ids'])}` accept, false accept `{len(hp['false_accept_ids'])}`。")
        lines.append(f"- balanced: recovered `{len(bal['recovered_accept_ids'])}` accept, false accept `{len(bal['false_accept_ids'])}`。")
        lines.append("- 如果 balanced 比 high precision 多出的样本含 false accept，应作为 `borderline_positive`，不直接映射 accept。")
        lines.append("")
    return "\n".join(lines)


def render_case_table(summary: Dict[str, Any]) -> str:
    lines = ["# Final Recommendation Calibration v1 Case Table", ""]
    for dataset, payload in summary["datasets"].items():
        lines += [f"## {dataset}", ""]
        case_rows = payload["three_way"]["case_rows"]
        rows = []
        for row in case_rows:
            if row["three_way_label"] in {"accept_like", "borderline_positive"} or row["gold_decision"] == "accept":
                rows.append([
                    row["paper_id"],
                    row["gold_decision"],
                    row["three_way_label"],
                    row["real_strong_support_total"],
                    row["non_abstract_support_total"],
                    row["empirical_support_total"],
                    row["independent_support_group_total"],
                    ",".join(row["positive_grounded_criteria"]),
                    row["sim4_label"],
                    row["negative_evidence_total"],
                    row["grounded_major_flaw_count"],
                ])
        lines.append(md_table(["paper_id", "gold", "calibrated_label", "real", "nonabs", "empirical", "ind_groups", "positive_criteria", "sim4", "neg_evidence", "grounded_major"], rows))
        lines.append("")
    return "\n".join(lines)


def render_decision(summary: Dict[str, Any]) -> str:
    nine = summary["datasets"].get("9b_fulltest39_dryrun", {})
    four = summary["datasets"].get("4b_mainline_fulltest39", {})
    nine_hp = (nine.get("binary_rules") or {}).get("calibrated_high_precision", {})
    nine_bal = (nine.get("binary_rules") or {}).get("calibrated_balanced", {})
    four_hp = (four.get("binary_rules") or {}).get("calibrated_high_precision", {})
    return f"""# Final Recommendation Calibration v1 Decision

## 结论

本轮确实弥补了 accept collapse 的一部分，但不能把问题包装成已经解决。

在 9B fulltest39 dry-run 上：

- `calibrated_high_precision` 恢复 `{len(nine_hp.get('recovered_accept_ids') or [])}` 个 accept，false accept `{len(nine_hp.get('false_accept_ids') or [])}`，accept precision `{nine_hp.get('accept_precision')}`。
- `calibrated_balanced` 恢复 `{len(nine_bal.get('recovered_accept_ids') or [])}` 个 accept，但 false accept `{len(nine_bal.get('false_accept_ids') or [])}`。

因此，推荐口径是：

> high precision 通过的样本标为 `accept_like`；balanced 通过但 high precision 不通过的样本标为 `borderline_positive`，不直接映射 accept。

## 为什么这能弥补当前短板

原始 runtime final decision 是 all reject。高精度校准至少能恢复一部分有实证/criterion 支撑的 accept，同时避免 false accept。balanced 规则能提高 accept recall，但会引入 false accept，所以只能作为 borderline 发现器。

## 4B 的含义

4B mainline fulltest39 上 `calibrated_high_precision` 恢复 `{len(four_hp.get('recovered_accept_ids') or [])}` 个 accept。4B 的主要问题不是聚合规则，而是上游 positive support formation 不足；不能靠 final calibration 单独弥补。

## 保留 / 不保留

保留：

- `calibrated_three_way` 作为论文 final recommendation view 的校准口径。
- `calibrated_high_precision` 作为 strict accept-like 映射。
- `calibrated_balanced` 作为 borderline-positive 发现器。

不保留：

- 不把 balanced 直接映射为 accept。
- 不把 support count 单独作为 accept 规则。
- 不改 runtime final decision。

## 下一步

1. 将 `Final Recommendation Calibration v1` 写入主结果包。
2. 如果要做正式主试验，用 `calibrated_three_way` 报告 recommendation view；binary accept/reject 只作为 health check。
3. 继续保留 false accept case study，尤其检查 balanced-only 样本为何风险高。
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--doc-dir", type=Path, default=Path("docs/experiments/mainline_current"))
    parser.add_argument("--output-json", type=Path, default=Path("outputs/results_main/review_infer/final_recommendation_calibration_v1.json"))
    args = parser.parse_args()

    summary: Dict[str, Any] = {"datasets": {}, "rules": list(BINARY_RULES) + ["calibrated_three_way"]}
    for name, path in DATASETS.items():
        data = read_json(path)
        rows = data.get("case_rows", [])
        binary = {rule_name: score_binary(rows, rule_name, rule_fn) for rule_name, rule_fn in BINARY_RULES.items()}
        summary["datasets"][name] = {
            "input": str(path),
            "rows": len(rows),
            "gold_counts": {
                "accept": sum(1 for row in rows if row.get("gold_decision") == "accept"),
                "reject": sum(1 for row in rows if row.get("gold_decision") == "reject"),
            },
            "binary_rules": binary,
            "three_way": score_three_way(rows),
        }

    write_json(args.output_json, summary)
    write_md(args.doc_dir / "FINAL_RECOMMENDATION_CALIBRATION_V1_SCHEMA.md", render_schema())
    write_md(args.doc_dir / "FINAL_RECOMMENDATION_CALIBRATION_V1_RESULTS.md", render_results(summary))
    write_md(args.doc_dir / "FINAL_RECOMMENDATION_CALIBRATION_V1_CASE_TABLE.md", render_case_table(summary))
    write_md(args.doc_dir / "FINAL_RECOMMENDATION_CALIBRATION_V1_DECISION.md", render_decision(summary))
    print(json.dumps({"output_json": str(args.output_json), "docs": ["FINAL_RECOMMENDATION_CALIBRATION_V1_SCHEMA.md", "FINAL_RECOMMENDATION_CALIBRATION_V1_RESULTS.md", "FINAL_RECOMMENDATION_CALIBRATION_V1_CASE_TABLE.md", "FINAL_RECOMMENDATION_CALIBRATION_V1_DECISION.md"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
