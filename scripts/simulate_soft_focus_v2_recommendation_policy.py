#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

CRITERION_LABELS = {
    "novelty": "Novelty / Originality",
    "significance": "Significance / Contribution",
    "soundness": "Technical Soundness",
    "empirical": "Empirical Adequacy",
    "clarity": "Clarity / Reproducibility",
}


def read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_md(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def md_table(headers: Iterable[Any], rows: Iterable[Iterable[Any]]) -> str:
    headers = [str(h) for h in headers]
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(v).replace("\n", " ") for v in row) + " |")
    return "\n".join(lines)


def as_int(row: Dict[str, Any], key: str) -> int:
    try:
        return int(row.get(key) or 0)
    except (TypeError, ValueError):
        return 0


def trusted_hard_negative_count(row: Dict[str, Any]) -> int:
    if "trusted_major_or_critical_flaws" in row:
        return as_int(row, "trusted_major_or_critical_flaws")
    return as_int(row, "major_or_critical_flaws")


def parse_criterion_ratings(report: str) -> Dict[str, str]:
    ratings: Dict[str, str] = {}
    for key, label in CRITERION_LABELS.items():
        match = re.search(r"-\s+" + re.escape(label) + r":\s*([a-zA-Z_]+)", report or "")
        if match:
            ratings[key] = match.group(1).lower()
    return ratings


def row_report_lookup(jsonl_rows: List[Dict[str, Any]]) -> Dict[str, Dict[str, str]]:
    lookup: Dict[str, Dict[str, str]] = {}
    for row in jsonl_rows:
        state = row.get("review_state") or {}
        report = row.get("final_report") or state.get("final_report") or ""
        lookup[str(row.get("paper_id") or "")] = parse_criterion_ratings(report)
    return lookup


def support_count_real_ge2(row: Dict[str, Any], ratings: Dict[str, str]) -> bool:
    return as_int(row, "real_strong_support_total") >= 2


def support_quality_basic(row: Dict[str, Any], ratings: Dict[str, str]) -> bool:
    return (
        as_int(row, "real_strong_support_total") >= 2
        and as_int(row, "non_abstract_support_total") >= 1
        and as_int(row, "independent_support_group_total") >= 2
        and as_int(row, "empirical_support_total") >= 1
    )


def method_plus_result(row: Dict[str, Any], ratings: Dict[str, str]) -> bool:
    return (
        as_int(row, "method_support_total") >= 1
        and as_int(row, "empirical_support_total") >= 1
        and as_int(row, "independent_support_group_total") >= 2
    )


def criterion_positive(row: Dict[str, Any], ratings: Dict[str, str]) -> bool:
    positives = sum(1 for key in ("significance", "soundness", "empirical") if ratings.get(key) == "positive")
    return positives >= 2 and support_quality_basic(row, ratings)


def high_precision(row: Dict[str, Any], ratings: Dict[str, str]) -> bool:
    return (
        as_int(row, "real_strong_support_total") >= 3
        and as_int(row, "non_abstract_support_total") >= 3
        and as_int(row, "empirical_support_total") >= 1
        and as_int(row, "method_support_total") >= 1
        and as_int(row, "independent_support_group_total") >= 3
        and as_int(row, "unresolved_count") <= 4
        and ratings.get("novelty") == "positive"
        and ratings.get("soundness") == "positive"
        and ratings.get("empirical") == "positive"
    )


BINARY_RULES = {
    "runtime_current": lambda row, ratings: str(row.get("original_pred") or "").lower() == "accept",
    "support_count_real_ge2": support_count_real_ge2,
    "support_quality_basic": support_quality_basic,
    "method_plus_result": method_plus_result,
    "criterion_positive": criterion_positive,
    "high_precision_criterion_quality": high_precision,
}


def classify_three_way(row: Dict[str, Any], ratings: Dict[str, str]) -> str:
    if high_precision(row, ratings):
        return "accept_like"
    if support_quality_basic(row, ratings) and ratings.get("empirical") == "positive":
        return "borderline_positive"
    if as_int(row, "real_strong_support_total") == 0 and not any(v == "positive" for v in ratings.values()):
        return "not_assessable"
    if trusted_hard_negative_count(row) > 0 or as_int(row, "unresolved_count") >= 6:
        return "reject_like"
    return "borderline_insufficient"


def score_rule(rows: List[Dict[str, Any]], ratings: Dict[str, Dict[str, str]], name: str, fn) -> Dict[str, Any]:
    tp = tn = fp = fn_count = 0
    false_accept_ids: List[str] = []
    recovered_accept_ids: List[str] = []
    false_reject_ids: List[str] = []
    predicted_accept_ids: List[str] = []
    for row in rows:
        pid = str(row.get("paper_id") or "")
        pred_accept = bool(fn(row, ratings.get(pid, {})))
        gold_accept = row.get("gold_decision") == "accept"
        if pred_accept:
            predicted_accept_ids.append(pid)
        if pred_accept and gold_accept:
            tp += 1
            recovered_accept_ids.append(pid)
        elif pred_accept and not gold_accept:
            fp += 1
            false_accept_ids.append(pid)
        elif (not pred_accept) and gold_accept:
            fn_count += 1
            false_reject_ids.append(pid)
        else:
            tn += 1
    total = len(rows) or 1
    accept_precision = tp / (tp + fp) if tp + fp else 0.0
    accept_recall = tp / (tp + fn_count) if tp + fn_count else 0.0
    reject_recall = tn / (tn + fp) if tn + fp else 0.0
    reject_precision = tn / (tn + fn_count) if tn + fn_count else 0.0
    accept_f1 = 2 * accept_precision * accept_recall / (accept_precision + accept_recall) if accept_precision + accept_recall else 0.0
    reject_f1 = 2 * reject_precision * reject_recall / (reject_precision + reject_recall) if reject_precision + reject_recall else 0.0
    return {
        "rule": name,
        "accuracy": round((tp + tn) / total, 4),
        "macro_f1": round((accept_f1 + reject_f1) / 2, 4),
        "accept_recall": round(accept_recall, 4),
        "reject_recall": round(reject_recall, 4),
        "predicted_accept_count": len(predicted_accept_ids),
        "false_accept_ids": false_accept_ids,
        "recovered_accept_ids": recovered_accept_ids,
        "false_reject_ids": false_reject_ids,
        "predicted_accept_ids": predicted_accept_ids,
    }


def build_case_rows(rows: List[Dict[str, Any]], ratings: Dict[str, Dict[str, str]]) -> List[Dict[str, Any]]:
    case_rows: List[Dict[str, Any]] = []
    for row in rows:
        pid = str(row.get("paper_id") or "")
        item = {
            "paper_id": pid,
            "gold_decision": row.get("gold_decision"),
            "runtime_pred": row.get("original_pred"),
            "three_way": classify_three_way(row, ratings.get(pid, {})),
            "criterion_ratings": ratings.get(pid, {}),
            "real_strong_support_total": as_int(row, "real_strong_support_total"),
            "non_abstract_support_total": as_int(row, "non_abstract_support_total"),
            "empirical_support_total": as_int(row, "empirical_support_total"),
            "method_support_total": as_int(row, "method_support_total"),
            "independent_support_group_total": as_int(row, "independent_support_group_total"),
            "unresolved_count": as_int(row, "unresolved_count"),
            "major_or_critical_flaws": as_int(row, "major_or_critical_flaws"),
            "trusted_major_or_critical_flaws": trusted_hard_negative_count(row),
            "support_quality_label": row.get("support_quality_label"),
        }
        for rule_name, rule_fn in BINARY_RULES.items():
            item[rule_name] = "accept" if rule_fn(row, ratings.get(pid, {})) else "reject"
        case_rows.append(item)
    return case_rows


def render_results(scores: List[Dict[str, Any]]) -> str:
    rows = [
        [s["rule"], s["accuracy"], s["macro_f1"], s["accept_recall"], s["reject_recall"], s["predicted_accept_count"], ",".join(s["false_accept_ids"]), ",".join(s["recovered_accept_ids"])]
        for s in scores
    ]
    return "# Soft Focus v2 Final Recommendation Calibration\n\n" + md_table(
        ["rule", "accuracy", "macro_f1", "accept_recall", "reject_recall", "pred_accept", "false_accept_ids", "recovered_accept_ids"], rows
    )


def render_hard_negative(case_rows: List[Dict[str, Any]]) -> str:
    false_accepts = [r for r in case_rows if r["gold_decision"] == "reject" and r["runtime_pred"] == "accept"]
    rows = []
    for r in false_accepts:
        ratings = r["criterion_ratings"]
        blockers = []
        if r["method_support_total"] == 0:
            blockers.append("no_method_support")
        if ratings.get("soundness") != "positive":
            blockers.append("soundness_not_positive")
        if ratings.get("novelty") != "positive":
            blockers.append("novelty_not_positive")
        if r.get("trusted_major_or_critical_flaws", r["major_or_critical_flaws"]) > 0:
            blockers.append("trusted_major_or_critical_flaw_present")
        rows.append([
            r["paper_id"],
            r["real_strong_support_total"],
            r["empirical_support_total"],
            r["method_support_total"],
            r["independent_support_group_total"],
            r["unresolved_count"],
            r.get("trusted_major_or_critical_flaws", r["major_or_critical_flaws"]),
            ratings,
            ",".join(blockers),
        ])
    text = "# Soft Focus v2 Hard-Negative Audit\n\n"
    false_ids = ", ".join(r["paper_id"] for r in false_accepts) or "none"
    text += f"runtime false accept（{false_ids}）不是 fallback binding 问题，而是 result support 足够强时，final decision 没有要求 method/soundness/novelty 形成足够的 grounded positive。\n\n"
    text += md_table(["paper_id", "real_strong", "empirical", "method", "independent", "unresolved", "trusted_major_flaw", "criterion_ratings", "blockers"], rows)
    return text


def render_case_table(case_rows: List[Dict[str, Any]]) -> str:
    rows = []
    for r in case_rows:
        rows.append([
            r["paper_id"], r["gold_decision"], r["runtime_pred"], r["three_way"],
            r["real_strong_support_total"], r["non_abstract_support_total"], r["empirical_support_total"], r["method_support_total"],
            r["independent_support_group_total"], r["unresolved_count"], r.get("trusted_major_or_critical_flaws", r["major_or_critical_flaws"]), r["criterion_ratings"],
        ])
    return "# Soft Focus v2 Recommendation Case Table\n\n" + md_table(
        ["paper_id", "gold", "runtime", "three_way", "real", "nonabs", "empirical", "method", "independent", "unresolved", "trusted_major_flaw", "criterion_ratings"], rows
    )


def render_decision(scores: List[Dict[str, Any]], case_rows: List[Dict[str, Any]]) -> str:
    hp = next(s for s in scores if s["rule"] == "high_precision_criterion_quality")
    three_counts = dict(Counter(r["three_way"] for r in case_rows))
    return f"""# Soft Focus v2 Recommendation Policy Decision

## 结论

`Soft Evidence Focus v2` 的 evidence formation 可以保留，但 runtime binary final decision 不能保留为主判断。应使用 hard-negative-aware 的 final recommendation view。

## 最稳规则

`high_precision_criterion_quality` 是当前最稳的离线规则：

- recovered accept: {', '.join(hp['recovered_accept_ids']) or 'none'}
- false accept: {', '.join(hp['false_accept_ids']) or 'none'}
- accept recall: {hp['accept_recall']}
- reject recall: {hp['reject_recall']}
- macro-F1: {hp['macro_f1']}

该规则恢复较少，但能挡住 runtime false accept `NnExMNiTHw`。它要求 support 不只是 result 数量足够，还必须有 method support，并且 novelty / technical soundness / empirical adequacy 都是 positive。

## Recommendation view 分布

当前视图分布：{three_counts}

- `accept_like`: 高精度、可映射 accept 的样本。
- `borderline_positive`: 有正向 support，但缺少 method/soundness/novelty 或 hard-negative 仍不清楚，不能映射 accept。
- `reject_like` / `not_assessable`: 不应硬转 accept。
- `borderline_insufficient`: 证据或 criterion 条件不足，单独保留为诊断状态。

## 下一步

1. 将 `high_precision_criterion_quality` 作为论文中的 strict accept-like 口径。
2. 将 `borderline_positive` 单独报告，不映射为 accept。
3. 不再继续调 runtime final decision 阈值；runtime accept/reject 只作为 health check。
4. 下一轮若要提升 recall，应优先改善 method/soundness evidence formation，而不是放宽 high-precision rule。
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--jsonl", required=True, type=Path)
    parser.add_argument("--support-summary", required=True, type=Path)
    parser.add_argument("--output-json", required=True, type=Path)
    parser.add_argument("--doc-dir", required=True, type=Path)
    parser.add_argument("--doc-prefix", default="SOFT_FOCUS_V2", help="Prefix for generated markdown files")
    args = parser.parse_args()

    jsonl_rows = load_jsonl(args.jsonl)
    ratings = row_report_lookup(jsonl_rows)
    support_rows = read_json(args.support_summary)["rows"]
    case_rows = build_case_rows(support_rows, ratings)
    scores = [score_rule(support_rows, ratings, name, fn) for name, fn in BINARY_RULES.items()]
    output = {
        "jsonl": str(args.jsonl),
        "support_summary": str(args.support_summary),
        "scores": scores,
        "three_way_counts": dict(Counter(r["three_way"] for r in case_rows)),
        "case_rows": case_rows,
    }
    write_json(args.output_json, output)
    prefix = args.doc_prefix
    write_md(args.doc_dir / f"{prefix}_FINAL_RECOMMENDATION_CALIBRATION.md", render_results(scores))
    write_md(args.doc_dir / f"{prefix}_HARD_NEGATIVE_AUDIT.md", render_hard_negative(case_rows))
    write_md(args.doc_dir / f"{prefix}_RECOMMENDATION_CASE_TABLE.md", render_case_table(case_rows))
    write_md(args.doc_dir / f"{prefix}_RECOMMENDATION_POLICY_DECISION.md", render_decision(scores, case_rows))
    print(json.dumps({"output_json": str(args.output_json), "scores": scores, "three_way_counts": output["three_way_counts"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
