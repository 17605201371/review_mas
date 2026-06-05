#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence

EMPIRICAL_TERMS = [
    "experiment", "experiments", "evaluation", "evaluate", "evaluated", "result", "results",
    "baseline", "baselines", "ablation", "dataset", "datasets", "metric", "metrics",
    "accuracy", "performance", "table", "figure", "comparison", "quantitative", "benchmark",
]
NEGATIVE_TERMS = [
    "lack", "lacks", "missing", "insufficient", "not visible", "not provided", "unclear",
    "cannot verify", "does not", "no quantitative", "no evidence", "needs verification",
    "unsupported", "gap", "weakness", "flaw", "incomplete", "truncated",
]
META_TERMS = ["excerpt", "truncated", "provided context", "not visible", "system", "could not", "current context"]
FOCUS_IDS = {"KI9NqjLVDT", "LebzzClHYw", "kam84eEmub", "ye3NrNrYOY"}


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


def text_has(text: str, terms: List[str]) -> bool:
    t = (text or "").lower()
    return any(term in t for term in terms)


def section_of_evidence(item: Dict[str, Any]) -> str:
    source = str(item.get("source") or "").lower()
    ev = str(item.get("evidence") or "").lower()
    if "abstract" in source or "abstract" in ev:
        return "abstract"
    if any(x in source or x in ev for x in ["table", "figure"]):
        return "table_or_figure"
    if any(x in source or x in ev for x in ["experiment", "evaluation", "result", "baseline", "dataset", "metric", "ablation"]):
        return "empirical"
    if any(x in source or x in ev for x in ["method", "approach", "model", "framework"]):
        return "method"
    return "unknown"


def load_mainline_rows(path: Path) -> Dict[str, Dict[str, Any]]:
    rows = {}
    with path.open(encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            row = json.loads(line)
            rows[row.get("paper_id")] = row
    return rows


def evidence_stats(review_state: Dict[str, Any]) -> Dict[str, Any]:
    evidence = review_state.get("evidence_map") or []
    empirical_items = []
    negative_empirical_items = []
    abstract_items = []
    method_items = []
    for item in evidence:
        blob = " ".join(str(item.get(k) or "") for k in ["evidence", "source", "stance", "strength"])
        sec = section_of_evidence(item)
        if sec == "abstract":
            abstract_items.append(item.get("evidence_id"))
        if sec == "method":
            method_items.append(item.get("evidence_id"))
        if sec in {"empirical", "table_or_figure"} or text_has(blob, EMPIRICAL_TERMS):
            empirical_items.append(item.get("evidence_id"))
            if text_has(blob, NEGATIVE_TERMS):
                negative_empirical_items.append(item.get("evidence_id"))
    return {
        "evidence_total": len(evidence),
        "empirical_evidence_ids": [x for x in empirical_items if x],
        "negative_empirical_evidence_ids": [x for x in negative_empirical_items if x],
        "abstract_evidence_count": len(abstract_items),
        "method_evidence_count": len(method_items),
        "empirical_evidence_count": len(empirical_items),
        "negative_empirical_evidence_count": len(negative_empirical_items),
    }


def flaw_stats(review_state: Dict[str, Any]) -> Dict[str, Any]:
    flaws = review_state.get("flaws") or []
    if not flaws:
        flaws = review_state.get("flaw_candidates") or []
    grounded_negative = []
    meta_negative = []
    empirical_flaws = []
    for flaw in flaws:
        blob = json.dumps(flaw, ensure_ascii=False).lower()
        fid = flaw.get("flaw_id") or flaw.get("id") or flaw.get("target_id") or f"flaw-{len(grounded_negative)+len(meta_negative)+1}"
        has_evidence = bool(flaw.get("evidence_ids") or flaw.get("supporting_evidence_ids") or flaw.get("evidence_id"))
        severe = any(x in blob for x in ["critical", "major", "high"])
        negative = text_has(blob, NEGATIVE_TERMS) or severe
        empirical = text_has(blob, EMPIRICAL_TERMS)
        meta = text_has(blob, META_TERMS)
        if empirical:
            empirical_flaws.append(fid)
        if negative and has_evidence and not meta:
            grounded_negative.append(fid)
        if negative and meta:
            meta_negative.append(fid)
    unresolved = review_state.get("unresolved_questions") or review_state.get("unresolved") or []
    unresolved_empirical = []
    unresolved_meta = []
    for idx, q in enumerate(unresolved):
        blob = json.dumps(q, ensure_ascii=False).lower()
        if text_has(blob, EMPIRICAL_TERMS):
            unresolved_empirical.append(f"u{idx+1}")
        if text_has(blob, META_TERMS):
            unresolved_meta.append(f"u{idx+1}")
    return {
        "flaw_total": len(flaws),
        "empirical_flaw_ids": empirical_flaws,
        "grounded_negative_flaw_ids": grounded_negative,
        "meta_negative_flaw_ids": meta_negative,
        "unresolved_total": len(unresolved),
        "unresolved_empirical_count": len(unresolved_empirical),
        "unresolved_meta_count": len(unresolved_meta),
    }


def classify_case(row: Dict[str, Any], cal: Dict[str, Any], evs: Dict[str, Any], fls: Dict[str, Any]) -> str:
    gold = row.get("gold_decision")
    label = cal.get("three_way_label")
    if gold == "accept" and label == "accept_like":
        return "recovered_accept_with_empirical_or_grounded_empirical"
    if gold == "reject" and label == "borderline_positive":
        if evs["empirical_evidence_count"] == 0 and row.get("criterion_grounded_empirical") is False:
            return "false_accept_risk_missing_empirical_grounding"
        if fls["grounded_negative_flaw_ids"]:
            return "false_accept_risk_hard_negative_not_used"
        return "false_accept_risk_positive_not_sufficient"
    if gold == "accept" and label not in {"accept_like", "borderline_positive"}:
        if as_int(row, "real_strong_support_total") == 0:
            return "false_reject_no_real_support"
        if evs["empirical_evidence_count"] == 0 and not row.get("criterion_grounded_empirical"):
            return "false_reject_missing_empirical_grounding"
        return "false_reject_negative_burden_or_quality_filter"
    return "other"


def build_rows(criterion_rows: List[Dict[str, Any]], calibration_rows: List[Dict[str, Any]], mainline: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    cal_by_id = {row["paper_id"]: row for row in calibration_rows}
    out = []
    for row in criterion_rows:
        pid = row["paper_id"]
        main = mainline.get(pid, {})
        state = main.get("review_state") or {}
        evs = evidence_stats(state)
        fls = flaw_stats(state)
        cal = cal_by_id.get(pid, {})
        item = {
            "paper_id": pid,
            "gold_decision": row.get("gold_decision"),
            "runtime_decision": row.get("current_decision"),
            "calibrated_label": cal.get("three_way_label"),
            "strict_binary": cal.get("strict_binary"),
            "lenient_binary": cal.get("lenient_binary"),
            "real_strong_support_total": as_int(row, "real_strong_support_total"),
            "non_abstract_support_total": as_int(row, "non_abstract_support_total"),
            "empirical_support_total": as_int(row, "empirical_support_total"),
            "independent_support_group_total": as_int(row, "independent_support_group_total"),
            "positive_grounded_criteria": row.get("positive_grounded_criteria") or [],
            "criterion_grounded_empirical": bool(row.get("criterion_grounded_empirical")),
            "criterion_rating_empirical": row.get("criterion_rating_empirical"),
            "criterion_grounded_soundness": bool(row.get("criterion_grounded_soundness")),
            "criterion_rating_soundness": row.get("criterion_rating_soundness"),
            "grounded_major_flaw_count": as_int(row, "grounded_major_flaw_count"),
            "confirmed_critical_flaw_count": as_int(row, "confirmed_critical_flaw_count"),
            "negative_evidence_total": as_int(row, "negative_evidence_total"),
            **evs,
            **fls,
        }
        item["audit_label"] = classify_case(row, cal, evs, fls)
        out.append(item)
    return out


def render_empirical(rows: List[Dict[str, Any]]) -> str:
    accept_rows = [r for r in rows if r["gold_decision"] == "accept"]
    recovered = [r for r in rows if r["audit_label"] == "recovered_accept_with_empirical_or_grounded_empirical"]
    missing = [r for r in accept_rows if "missing_empirical" in r["audit_label"] or (r["empirical_support_total"] == 0 and not r["criterion_grounded_empirical"])]
    table = []
    for r in accept_rows:
        table.append([r["paper_id"], r["calibrated_label"], r["audit_label"], r["real_strong_support_total"], r["non_abstract_support_total"], r["empirical_support_total"], r["criterion_grounded_empirical"], r["empirical_evidence_count"], r["unresolved_empirical_count"]])
    return "\n".join([
        "# Empirical Evidence Sufficiency Audit v1",
        "",
        "## 结论",
        "",
        f"gold accept 样本 `{len(accept_rows)}` 条，其中 high-precision 恢复 `{len(recovered)}` 条。未恢复样本主要不是 final aggregation 阈值问题，而是 empirical/result/table/ablation support 仍不足，或 empirical criterion 没有 grounded positive。",
        "",
        "## Accept-side case table",
        "",
        md_table(["paper_id", "calibrated", "audit_label", "real", "nonabs", "empirical_support", "empirical_criterion_grounded", "state_empirical_evidence", "unresolved_empirical"], table),
        "",
        "## 解释",
        "",
        "- `calibrated_high_precision` 要求 empirical support 或 grounded empirical adequacy，是为了防止把局部 claim support 误当成 paper-level accept。",
        "- high-precision 召回低，说明下一步如果要继续提高 accept recall，应优先改善 empirical evidence formation，而不是继续放松 recommendation 规则。",
    ])


def render_negative(rows: List[Dict[str, Any]]) -> str:
    reject_rows = [r for r in rows if r["gold_decision"] == "reject"]
    risk = [r for r in rows if r["audit_label"].startswith("false_accept_risk")]
    table = []
    for r in risk:
        table.append([r["paper_id"], r["calibrated_label"], r["audit_label"], r["real_strong_support_total"], r["non_abstract_support_total"], r["empirical_support_total"], r["criterion_grounded_empirical"], r["grounded_negative_flaw_ids"], r["negative_empirical_evidence_ids"], r["unresolved_empirical_count"]])
    return "\n".join([
        "# Hard-Negative Grounding Audit v1",
        "",
        "## 结论",
        "",
        f"gold reject 样本 `{len(reject_rows)}` 条，其中 balanced-only false-accept risk `{len(risk)}` 条。风险样本的共同点是 positive support 足以触发 balanced，但 empirical support / empirical criterion 不足，且没有被可靠 hard-negative blocker 拦住。",
        "",
        "## Balanced false-accept risk table",
        "",
        md_table(["paper_id", "calibrated", "audit_label", "real", "nonabs", "empirical_support", "empirical_criterion_grounded", "grounded_negative_flaws", "negative_empirical_evidence", "unresolved_empirical"], table),
        "",
        "## 解释",
        "",
        "- 当前 hard-negative formation 不足以支撑直接 reject-side blocker，因此不能简单把 balanced 规则变成 accept。",
        "- 如果要继续优化，应该定向检查 reject 样本是否存在未抽取的 empirical insufficiency、missing baseline、missing quantitative result 或 method-only support 风险。",
    ])


def render_case_table(rows: List[Dict[str, Any]]) -> str:
    focus = [r for r in rows if r["audit_label"] != "other" or r["paper_id"] in {"KI9NqjLVDT", "LebzzClHYw", "kam84eEmub", "ye3NrNrYOY"}]
    table = []
    for r in focus:
        table.append([r["paper_id"], r["gold_decision"], r["calibrated_label"], r["audit_label"], r["real_strong_support_total"], r["non_abstract_support_total"], r["empirical_support_total"], r["criterion_grounded_empirical"], r["empirical_evidence_count"], r["grounded_major_flaw_count"], r["confirmed_critical_flaw_count"]])
    return "\n".join([
        "# Empirical / Negative Grounding Case Table v1",
        "",
        md_table(["paper_id", "gold", "calibrated", "audit_label", "real", "nonabs", "empirical_support", "empirical_criterion", "state_empirical_evidence", "grounded_major", "critical"], table),
    ])


def render_decision(rows: List[Dict[str, Any]]) -> str:
    recovered = [r for r in rows if r["audit_label"] == "recovered_accept_with_empirical_or_grounded_empirical"]
    risk = [r for r in rows if r["audit_label"].startswith("false_accept_risk")]
    missing_accept = [r for r in rows if r["gold_decision"] == "accept" and r["calibrated_label"] not in {"accept_like", "borderline_positive"}]
    return "\n".join([
        "# Next Cut After Calibration Decision",
        "",
        "## 当前判断",
        "",
        f"high-precision 已恢复 `{len(recovered)}` 个 accept；balanced-only false-accept risk 有 `{len(risk)}` 个。剩余 gold accept 中仍有 `{len(missing_accept)}` 个没有进入 positive recommendation。",
        "",
        "这说明下一步不是继续调 final recommendation 阈值，而是补上两类上游证据：empirical evidence formation 和 hard-negative grounding。",
        "",
        "## 下一刀选择",
        "",
        "优先做 `Empirical Evidence Targeted Audit/Pass v1`，但先保持离线审计，不直接改 runtime。原因：",
        "",
        "1. false accept risk 的共同缺口是 empirical support 或 empirical grounded criterion 不足。",
        "2. high-precision 恢复 accept 依赖 empirical adequacy grounded positive，而不是单纯 support count。",
        "3. 4B 上 calibration 恢复 0 accept，说明上游 positive support formation 仍不足。",
        "",
        "## 暂时不做",
        "",
        "- 不继续调 accept/reject 阈值。",
        "- 不把 balanced 规则直接映射 accept。",
        "- 不恢复 sticky/throttle/gate。",
        "- 不做蒸馏。",
        "",
        "## 如果继续实现",
        "",
        "下一轮应只做一个小切口：让 Evidence/criterion final-view 分析更可靠地区分 empirical/result/table support 与 abstract/method-only support，并对 reject 样本补 hard-negative grounding case study。",
    ])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--criterion-json", type=Path, default=Path("outputs/results_main/review_infer/criterion_grounded_decision_sim_v1_9b_fulltest39_dryrun.json"))
    parser.add_argument("--calibration-json", type=Path, default=Path("outputs/results_main/review_infer/final_recommendation_calibration_v1.json"))
    parser.add_argument("--mainline-jsonl", type=Path, default=Path("outputs/results_main/review_infer/mainline_final_v1_9b_fulltest39_dryrun.jsonl"))
    parser.add_argument("--output-json", type=Path, default=Path("outputs/results_main/review_infer/empirical_negative_grounding_audit_v1.json"))
    parser.add_argument("--doc-dir", type=Path, default=Path("docs/experiments/mainline_current"))
    args = parser.parse_args()
    criterion = read_json(args.criterion_json)
    calibration = read_json(args.calibration_json)
    mainline = load_mainline_rows(args.mainline_jsonl)
    rows = build_rows(
        criterion.get("case_rows", []),
        calibration["datasets"]["9b_fulltest39_dryrun"]["three_way"]["case_rows"],
        mainline,
    )
    summary = {
        "rows": len(rows),
        "audit_label_counts": {},
        "next_cut": {
            "recommendation": "Empirical Evidence Targeted Audit/Pass v1",
            "mode": "offline_or_final_view_first",
            "do_not_do": [
                "accept/reject threshold tuning",
                "balanced-to-accept remapping",
                "sticky/throttle/progression gate",
                "distillation",
            ],
        },
        "case_rows": rows,
    }
    for row in rows:
        summary["audit_label_counts"][row["audit_label"]] = summary["audit_label_counts"].get(row["audit_label"], 0) + 1
    write_json(args.output_json, summary)
    write_md(args.doc_dir / "EMPIRICAL_EVIDENCE_SUFFICIENCY_AUDIT_V1.md", render_empirical(rows))
    write_md(args.doc_dir / "HARD_NEGATIVE_GROUNDING_AUDIT_V1.md", render_negative(rows))
    write_md(args.doc_dir / "EMPIRICAL_NEGATIVE_CASE_TABLE_V1.md", render_case_table(rows))
    write_md(args.doc_dir / "NEXT_CUT_AFTER_CALIBRATION_DECISION.md", render_decision(rows))
    print(json.dumps({"output_json": str(args.output_json), "rows": len(rows), "audit_label_counts": summary["audit_label_counts"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
