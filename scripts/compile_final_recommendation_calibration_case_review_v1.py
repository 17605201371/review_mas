#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence

FOCUS_IDS = ["KI9NqjLVDT", "LebzzClHYw", "kam84eEmub", "ye3NrNrYOY"]
CORE_CRITERIA = ["novelty", "significance", "soundness", "empirical", "clarity"]


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


def criterion_status(row: Dict[str, Any], name: str) -> str:
    rating = row.get(f"criterion_rating_{name}") or "missing"
    grounded = bool(row.get(f"criterion_grounded_{name}"))
    if rating == "moderate_or_strong" and grounded:
        return "positive_grounded"
    if rating == "moderate_or_strong" and not grounded:
        return "positive_ungrounded"
    if rating == "neutral_or_mentioned" and grounded:
        return "neutral_grounded"
    if rating == "neutral_or_mentioned":
        return "neutral_ungrounded"
    if row.get(f"criterion_not_assessable_{name}"):
        return "not_assessable"
    return "missing"


def diagnose(row: Dict[str, Any], cal: Dict[str, Any]) -> Dict[str, Any]:
    pid = row["paper_id"]
    label = cal["three_way_label"]
    gold = row["gold_decision"]
    empirical_ok = as_int(row, "empirical_support_total") >= 1 or criterion_status(row, "empirical") == "positive_grounded"
    has_hard_negative = as_int(row, "confirmed_critical_flaw_count") > 0 or as_int(row, "grounded_major_flaw_count") > 0 or bool(row.get("grounded_weak_core_criteria"))
    if gold == "accept" and label == "accept_like":
        if empirical_ok:
            diagnosis = "recovered_accept_high_precision"
            reason = "有真实 claim strong support、non-abstract support、独立 support group，并且 empirical adequacy 为 grounded positive；没有 grounded hard negative。"
        else:
            diagnosis = "recovered_accept_positive_but_empirical_weak"
            reason = "有正向 support，但 empirical grounding 不充分；若出现这种情况应降为 borderline。"
    elif gold == "reject" and label == "borderline_positive":
        diagnosis = "balanced_only_false_accept_risk"
        reason = "positive support/criterion 看似充足，但 empirical support 或 empirical grounded criterion 不足，因此 high-precision 拦截为 borderline，而不是 accept_like。"
    elif gold == "reject" and label == "accept_like":
        diagnosis = "unsafe_false_accept"
        reason = "该样本被 high-precision 接收，需要进一步加 hard-negative 或 empirical sufficiency gate。"
    else:
        diagnosis = "other"
        reason = "不属于本轮重点 case。"
    if has_hard_negative:
        reason += " 注意：存在 grounded hard-negative 指标，不能直接 accept。"
    return {"diagnosis": diagnosis, "reason": reason, "empirical_ok": empirical_ok, "has_hard_negative": has_hard_negative}


def build_cases(criterion_rows: List[Dict[str, Any]], calibration_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    criterion_by_id = {row["paper_id"]: row for row in criterion_rows}
    cal_by_id = {row["paper_id"]: row for row in calibration_rows}
    cases: List[Dict[str, Any]] = []
    for pid in FOCUS_IDS:
        row = criterion_by_id[pid]
        cal = cal_by_id[pid]
        diag = diagnose(row, cal)
        cases.append({
            "paper_id": pid,
            "gold_decision": row.get("gold_decision"),
            "calibrated_label": cal.get("three_way_label"),
            "strict_binary": cal.get("strict_binary"),
            "lenient_binary": cal.get("lenient_binary"),
            "diagnosis": diag["diagnosis"],
            "diagnosis_reason": diag["reason"],
            "real_strong_support_total": as_int(row, "real_strong_support_total"),
            "non_abstract_support_total": as_int(row, "non_abstract_support_total"),
            "empirical_support_total": as_int(row, "empirical_support_total"),
            "independent_support_group_total": as_int(row, "independent_support_group_total"),
            "abstract_only_support_count": as_int(row, "abstract_only_support_count"),
            "positive_grounded_criteria": row.get("positive_grounded_criteria") or [],
            "criterion_statuses": {name: criterion_status(row, name) for name in CORE_CRITERIA},
            "confirmed_critical_flaw_count": as_int(row, "confirmed_critical_flaw_count"),
            "grounded_major_flaw_count": as_int(row, "grounded_major_flaw_count"),
            "negative_evidence_total": as_int(row, "negative_evidence_total"),
            "stale_gap_count": as_int(row, "stale_gap_count"),
            "unsupported_with_strong_support_count": as_int(row, "unsupported_with_strong_support_count"),
            "sim4_label": row.get("sim4_label"),
        })
    return cases


def render_doc(cases: List[Dict[str, Any]]) -> str:
    summary_rows = []
    for c in cases:
        summary_rows.append([
            c["paper_id"],
            c["gold_decision"],
            c["calibrated_label"],
            c["diagnosis"],
            c["real_strong_support_total"],
            c["non_abstract_support_total"],
            c["empirical_support_total"],
            c["independent_support_group_total"],
            ",".join(c["positive_grounded_criteria"]),
        ])
    lines = [
        "# Final Recommendation Calibration Case Review v1",
        "",
        "## 目的",
        "",
        "本文件解释 `Final Recommendation Calibration v1` 为什么能部分弥补 all-reject，同时为什么不能把 balanced 规则直接映射成 accept。本轮只做离线 case review，不改 runtime。",
        "",
        "## 总览",
        "",
        md_table(["paper_id", "gold", "calibrated_label", "diagnosis", "real", "nonabs", "empirical", "ind_groups", "positive_criteria"], summary_rows),
        "",
        "## 逐案分析",
        "",
    ]
    for c in cases:
        crit = c["criterion_statuses"]
        lines += [
            f"### {c['paper_id']} — {c['diagnosis']}",
            "",
            f"- gold decision: `{c['gold_decision']}`",
            f"- calibrated label: `{c['calibrated_label']}`",
            f"- strict binary: `{c['strict_binary']}`; lenient binary: `{c['lenient_binary']}`",
            f"- support: real `{c['real_strong_support_total']}`, non-abstract `{c['non_abstract_support_total']}`, empirical `{c['empirical_support_total']}`, independent groups `{c['independent_support_group_total']}`, abstract-only `{c['abstract_only_support_count']}`",
            f"- positive grounded criteria: `{', '.join(c['positive_grounded_criteria']) or 'none'}`",
            f"- criterion statuses: novelty `{crit['novelty']}`, significance `{crit['significance']}`, soundness `{crit['soundness']}`, empirical `{crit['empirical']}`, clarity `{crit['clarity']}`",
            f"- negative state: confirmed critical `{c['confirmed_critical_flaw_count']}`, grounded major `{c['grounded_major_flaw_count']}`, negative evidence `{c['negative_evidence_total']}`, stale gaps `{c['stale_gap_count']}`, unsupported-with-strong `{c['unsupported_with_strong_support_count']}`",
            f"- interpretation: {c['diagnosis_reason']}",
            "",
        ]
    lines += [
        "## 结论",
        "",
        "1. `KI9NqjLVDT` 和 `LebzzClHYw` 说明 high-precision 规则可以恢复一部分 gold accept，且不会依赖单纯 strong-support-count。",
        "2. `kam84eEmub` 和 `ye3NrNrYOY` 说明 balanced 规则会把局部正向 support 误读成 paper-level accept，主要缺口是 empirical support / empirical grounded criterion。",
        "3. 因此正式推荐口径应保留三层：`accept_like`、`borderline_positive`、`not_assessable/reject_like`，不要把 borderline 直接当 accept。",
        "4. 下一步如果继续优化，应优先改善 empirical evidence formation 和 hard-negative grounding，而不是继续调 accept/reject 阈值。",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--criterion-json", type=Path, default=Path("outputs/results_main/review_infer/criterion_grounded_decision_sim_v1_9b_fulltest39_dryrun.json"))
    parser.add_argument("--calibration-json", type=Path, default=Path("outputs/results_main/review_infer/final_recommendation_calibration_v1.json"))
    parser.add_argument("--output-json", type=Path, default=Path("outputs/results_main/review_infer/final_recommendation_calibration_case_review_v1.json"))
    parser.add_argument("--doc", type=Path, default=Path("docs/experiments/mainline_current/FINAL_RECOMMENDATION_CALIBRATION_CASE_REVIEW_V1.md"))
    args = parser.parse_args()
    criterion = read_json(args.criterion_json)
    calibration = read_json(args.calibration_json)
    criterion_rows = criterion.get("case_rows", [])
    calibration_rows = calibration["datasets"]["9b_fulltest39_dryrun"]["three_way"]["case_rows"]
    cases = build_cases(criterion_rows, calibration_rows)
    payload = {"focus_ids": FOCUS_IDS, "cases": cases}
    write_json(args.output_json, payload)
    write_md(args.doc, render_doc(cases))
    print(json.dumps({"output_json": str(args.output_json), "doc": str(args.doc), "cases": len(cases)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
