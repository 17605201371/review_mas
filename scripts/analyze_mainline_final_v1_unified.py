#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence

SUPPORT_STANCES = {"supports", "partially_supports"}
CRITERIA = ["novelty", "significance", "soundness", "empirical", "clarity"]


def norm(value: Any) -> str:
    return str(value or "").strip().lower()


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_md(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def table(headers: Sequence[str], rows: Sequence[Sequence[Any]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(x).replace("\n", " ") for x in row) + " |")
    return "\n".join(lines)


def infer_gold(row: Dict[str, Any]) -> str:
    explicit = norm(row.get("gold_decision") or row.get("ground_truth_decision"))
    if explicit in {"accept", "reject"}:
        return explicit
    pred = norm(row.get("final_decision") or (row.get("review_state") or {}).get("final_decision"))
    corr = row.get("accept_reject_correct")
    if pred in {"accept", "reject"} and corr in {0, 0.0, 1, 1.0}:
        return pred if corr in {1, 1.0} else ("accept" if pred == "reject" else "reject")
    return "unknown"


def is_real_claim(claim_id: Any) -> bool:
    cid = norm(claim_id)
    return bool(cid) and "fallback" not in cid and "general" not in cid


def source_bucket(ev: Dict[str, Any]) -> str:
    text = " ".join(str(ev.get(k, "")) for k in ["source", "support_source_bucket", "support_quality", "evidence", "section"] ).lower()
    if "abstract" in text:
        return "abstract"
    if any(x in text for x in ["ablation"]):
        return "ablation"
    if any(x in text for x in ["table", "figure", "fig."]):
        return "table_or_figure"
    if any(x in text for x in ["experiment", "evaluation", "result", "baseline", "dataset", "metric", "benchmark", "performance"]):
        return "empirical"
    if any(x in text for x in ["method", "approach", "model", "framework", "algorithm", "architecture"]):
        return "method"
    return "unknown"


def binary_metrics(rows: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    tp = tn = fp = fn = 0
    false_accept: List[str] = []
    false_reject: List[str] = []
    recovered: List[str] = []
    for row in rows:
        gold = infer_gold(row)
        pred = norm(row.get("final_decision") or (row.get("review_state") or {}).get("final_decision"))
        if pred not in {"accept", "reject"}:
            pred = "reject"
        pid = str(row.get("paper_id"))
        if gold == "accept" and pred == "accept":
            tp += 1; recovered.append(pid)
        elif gold == "reject" and pred == "reject":
            tn += 1
        elif gold == "reject" and pred == "accept":
            fp += 1; false_accept.append(pid)
        elif gold == "accept" and pred == "reject":
            fn += 1; false_reject.append(pid)
    n = max(1, tp + tn + fp + fn)
    accept_recall = tp / max(1, tp + fn)
    reject_recall = tn / max(1, tn + fp)
    accept_precision = tp / max(1, tp + fp)
    reject_precision = tn / max(1, tn + fn)
    accept_f1 = 0 if accept_precision + accept_recall == 0 else 2 * accept_precision * accept_recall / (accept_precision + accept_recall)
    reject_f1 = 0 if reject_precision + reject_recall == 0 else 2 * reject_precision * reject_recall / (reject_precision + reject_recall)
    return {
        "accuracy": round((tp + tn) / n, 4),
        "macro_f1": round((accept_f1 + reject_f1) / 2, 4),
        "accept_recall": round(accept_recall, 4),
        "reject_recall": round(reject_recall, 4),
        "predicted_accept_count": tp + fp,
        "predicted_reject_count": tn + fn,
        "false_accept_ids": false_accept,
        "false_reject_ids": false_reject,
        "recovered_accept_ids": recovered,
    }


def summarize_runtime(rows: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    c = Counter()
    case_rows: List[Dict[str, Any]] = []
    for row in rows:
        state = row.get("review_state") or {}
        gold = infer_gold(row)
        pred = norm(row.get("final_decision") or state.get("final_decision")) or "unknown"
        c[f"gold_{gold}"] += 1
        c[f"pred_{pred}"] += 1
        real = nonabs = empirical = method = table_fig = ablation = fallback = 0
        for ev in state.get("evidence_map", []) or []:
            if not isinstance(ev, dict):
                continue
            stance = norm(ev.get("stance"))
            strength = norm(ev.get("strength"))
            if stance not in SUPPORT_STANCES or strength != "strong":
                continue
            if not is_real_claim(ev.get("claim_id")):
                fallback += 1
                continue
            real += 1
            bucket = source_bucket(ev)
            if bucket != "abstract":
                nonabs += 1
            if bucket in {"empirical", "table_or_figure", "ablation"}:
                empirical += 1
            if bucket == "method":
                method += 1
            if bucket == "table_or_figure":
                table_fig += 1
            if bucket == "ablation":
                ablation += 1
        evidence_json_status = Counter()
        fallback_payloads = patch_emitted = patch_committed = legacy = 0
        for turn in row.get("turn_logs", []) or []:
            status = norm(turn.get("evidence_json_parse_status"))
            if status:
                evidence_json_status[status] += 1
            if turn.get("evidence_json_fallback_payload_used"):
                fallback_payloads += 1
            if turn.get("recovery_patch_emitted"):
                patch_emitted += 1
            if turn.get("recovery_patch_committed") or turn.get("recovery_committed"):
                patch_committed += 1
            if turn.get("progression_gate_triggered") or norm(turn.get("policy_source")) in {"sticky_recovery_bias", "progression_gate_override"}:
                legacy += 1
        c["real_strong_support_total"] += real
        c["nonabstract_strong_support_total"] += nonabs
        c["empirical_strong_support_total"] += empirical
        c["method_strong_support_total"] += method
        c["table_or_figure_strong_support_total"] += table_fig
        c["ablation_strong_support_total"] += ablation
        c["fallback_strong_support_total"] += fallback
        c["rows_with_2plus_real_strong_support"] += int(real >= 2)
        c["accept_rows_with_2plus_real_strong_support"] += int(gold == "accept" and real >= 2)
        c["unresolved_count"] += len(state.get("unresolved_questions", []) or [])
        c["evidence_gap_count"] += len(state.get("evidence_gaps", []) or [])
        c["flaw_count"] += len(state.get("flaw_candidates", []) or [])
        c["patch_emitted_count"] += patch_emitted
        c["patch_committed_count"] += patch_committed
        c["rows_with_any_commit"] += int(patch_committed > 0)
        c["evidence_json_invalid_or_missing_count"] += sum(evidence_json_status.get(k, 0) for k in ["no_json_object", "invalid_json", "truncated_tagged_json"])
        c["evidence_json_fallback_used_count"] += evidence_json_status.get("fallback_used", 0) + fallback_payloads
        c["evidence_json_status_turn_count"] += sum(evidence_json_status.values())
        c["legacy_controller_active_turns"] += legacy
        case_rows.append({
            "paper_id": row.get("paper_id"),
            "gold_decision": gold,
            "runtime_final_decision": pred,
            "real_strong_support": real,
            "nonabstract_strong_support": nonabs,
            "empirical_strong_support": empirical,
            "method_strong_support": method,
            "unresolved_count": len(state.get("unresolved_questions", []) or []),
            "evidence_gap_count": len(state.get("evidence_gaps", []) or []),
            "flaw_count": len(state.get("flaw_candidates", []) or []),
            "patch_committed_count": patch_committed,
            "reward": row.get("reward"),
        })
    summary = dict(c)
    summary.update(binary_metrics(rows))
    summary["gold_counts"] = {"accept": c.get("gold_accept", 0), "reject": c.get("gold_reject", 0), "unknown": c.get("gold_unknown", 0)}
    summary["prediction_counts"] = {"accept": c.get("pred_accept", 0), "reject": c.get("pred_reject", 0), "unknown": c.get("pred_unknown", 0)}
    summary["strong_support_binding_precision"] = round(summary.get("real_strong_support_total", 0) / max(1, summary.get("real_strong_support_total", 0) + summary.get("fallback_strong_support_total", 0)), 4)
    summary["avg_reward"] = round(sum(float(row.get("reward") or 0) for row in rows) / max(1, len(rows)), 4)
    return {"summary": summary, "case_rows": case_rows}


def summarize_classifier(data: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "aggregate": data.get("aggregate", {}),
        "metrics": data.get("metrics", {}),
        "view_counts": data.get("aggregate", {}).get("view_counts", {}),
    }


def summarize_report_renderer(data: Dict[str, Any]) -> Dict[str, Any]:
    return data.get("aggregate", {})


def summarize_method_soundness(data: Dict[str, Any]) -> Dict[str, Any]:
    return data.get("summary", {})


def summarize_recommendation_policy(data: Dict[str, Any]) -> Dict[str, Any]:
    scores = data.get("scores", [])
    return {
        "scores": scores,
        "three_way_counts": data.get("three_way_counts", {}),
    }


def render_report(payload: Dict[str, Any]) -> str:
    rt = payload["runtime"]["summary"]
    cls = payload["classifier"]
    renderer = payload["report_renderer"]
    method = payload["method_soundness"]
    rec = payload["recommendation_policy"]
    score_rows = []
    for row in rec.get("scores", [])[:8]:
        score_rows.append([row.get("rule"), row.get("accuracy"), row.get("macro_f1"), row.get("accept_recall"), row.get("reject_recall"), row.get("predicted_accept_count"), ", ".join(row.get("false_accept_ids") or []) or "无", ", ".join(row.get("recovered_accept_ids") or []) or "无"])
    return "\n\n".join([
        "# Mainline-Final-v1 Unified Fulltest39 Report",
        "## 总结论",
        "当前系统已经具备较稳定的 evidence binding、fallback flaw guard、final-view hard-negative lifecycle 和 report 分区展示。正式主试验前的剩余工作不是继续新增 controller，而是冻结统一指标口径，并将 accept/reject 仅作为 health check；论文主线应报告 support quality、criterion grounding、hard-negative lifecycle 与 final-view report hygiene。",
        "## Runtime Decision Health",
        table(["metric", "value"], [
            ["accuracy", rt.get("accuracy")],
            ["macro_f1", rt.get("macro_f1")],
            ["accept_recall", rt.get("accept_recall")],
            ["reject_recall", rt.get("reject_recall")],
            ["predicted_accept_count", rt.get("predicted_accept_count")],
            ["false_accept_ids", ", ".join(rt.get("false_accept_ids") or []) or "无"],
            ["recovered_accept_ids", ", ".join(rt.get("recovered_accept_ids") or []) or "无"],
        ]),
        "## Evidence / Support Quality",
        table(["metric", "value"], [
            ["real_strong_support_total", rt.get("real_strong_support_total")],
            ["nonabstract_strong_support_total", rt.get("nonabstract_strong_support_total")],
            ["empirical_strong_support_total", rt.get("empirical_strong_support_total")],
            ["method_strong_support_total", rt.get("method_strong_support_total")],
            ["table_or_figure_strong_support_total", rt.get("table_or_figure_strong_support_total")],
            ["fallback_strong_support_total", rt.get("fallback_strong_support_total")],
            ["strong_support_binding_precision", rt.get("strong_support_binding_precision")],
            ["rows_with_2plus_real_strong_support", rt.get("rows_with_2plus_real_strong_support")],
            ["accept_rows_with_2plus_real_strong_support", rt.get("accept_rows_with_2plus_real_strong_support")],
        ]),
        "## State / Recovery / Runtime Hygiene",
        table(["metric", "value"], [
            ["unresolved_count", rt.get("unresolved_count")],
            ["evidence_gap_count", rt.get("evidence_gap_count")],
            ["flaw_count", rt.get("flaw_count")],
            ["patch_emitted_count", rt.get("patch_emitted_count")],
            ["patch_committed_count", rt.get("patch_committed_count")],
            ["rows_with_any_commit", rt.get("rows_with_any_commit")],
            ["evidence_json_invalid_or_missing_count", rt.get("evidence_json_invalid_or_missing_count")],
            ["evidence_json_fallback_used_count", rt.get("evidence_json_fallback_used_count")],
            ["legacy_controller_active_turns", rt.get("legacy_controller_active_turns")],
        ]),
        "## Final-View Unresolved / Candidate-Flaw Classifier",
        table(["metric", "value"], [
            ["view_counts", cls.get("view_counts")],
            ["accuracy", cls.get("metrics", {}).get("accuracy")],
            ["macro_f1", cls.get("metrics", {}).get("macro_f1")],
            ["accept_recall", cls.get("metrics", {}).get("accept_recall")],
            ["reject_recall", cls.get("metrics", {}).get("reject_recall")],
            ["false_accept_ids", ", ".join(cls.get("metrics", {}).get("false_accept_ids") or []) or "无"],
            ["recovered_accept_ids", ", ".join(cls.get("metrics", {}).get("recovered_accept_ids") or []) or "无"],
        ]),
        "## Final-View Report Renderer",
        table(["metric", "value"], [[k, v] for k, v in renderer.items() if k != "section_totals"] + [["section_totals", renderer.get("section_totals")]]),
        "## Method / Soundness Gap Audit",
        table(["metric", "value"], [[k, v] for k, v in method.items()]),
        "## Recommendation Policy Simulation",
        table(["rule", "accuracy", "macro_f1", "accept_recall", "reject_recall", "pred_accept", "false_accept", "recovered_accept"], score_rows),
        "## 当前判断",
        "这轮统一表确认：系统已有可解释的 final-view report 与高精度 conservative recommendation view，但 runtime 二分类仍不能作为主指标。下一步应做正式主试验前的 9B 小确认或 9B fulltest dry run，前提是固定本表中的指标口径，不再新增 sticky/throttle/gate 类 runtime controller。",
    ])


def render_case_table(payload: Dict[str, Any]) -> str:
    runtime_cases = {row["paper_id"]: row for row in payload["runtime"]["case_rows"]}
    classifier_cases = {row["paper_id"]: row for row in payload["classifier_rows"]}
    report_cases = {row["paper_id"]: row for row in payload["report_rows"]}
    rows = []
    for pid, row in runtime_cases.items():
        cls = classifier_cases.get(pid, {})
        rep = report_cases.get(pid, {})
        sec = rep.get("section_counts") or {}
        rows.append([
            pid, row.get("gold_decision"), row.get("runtime_final_decision"), cls.get("classifier_view"),
            row.get("real_strong_support"), row.get("nonabstract_strong_support"), row.get("empirical_strong_support"), row.get("method_strong_support"),
            row.get("unresolved_count"), row.get("flaw_count"), sec.get("confirmed_weaknesses", 0), sec.get("potential_concerns", 0), sec.get("review_limitations", 0), sec.get("unresolved_questions", 0),
        ])
    return "# Mainline-Final-v1 Unified Case Table\n\n" + table(["paper_id", "gold", "runtime", "view", "real", "nonabs", "empirical", "method", "unresolved", "flaws", "confirmed", "potential", "limitations", "questions"], rows)


def render_decision(payload: Dict[str, Any]) -> str:
    rt = payload["runtime"]["summary"]
    renderer = payload["report_renderer"]
    return f"""# Mainline-Final-v1 Unified Next Step Decision

## 结论

本轮统一分析支持进入主试验 dry-run 收口，但仍不建议把 runtime accept/reject 当作论文主指标。当前最可靠的成果是：evidence binding 干净、fallback flaw 被隔离、final-view classifier 保守、final report 能把确认缺陷/候选问题/审稿限制/未解决问题分区展示。

## 关键判断

- runtime predicted accept: `{rt.get('predicted_accept_count')}`
- runtime accept recall: `{rt.get('accept_recall')}`
- runtime false accept: `{rt.get('false_accept_ids')}`
- real strong support: `{rt.get('real_strong_support_total')}`
- fallback strong support: `{rt.get('fallback_strong_support_total')}`
- confirmed weakness meta leak rows: `{renderer.get('confirmed_weakness_meta_leak_rows')}`

## 下一步

下一步应做 `Mainline-Final-v1 9B confirmation`，但必须使用本轮统一指标口径：Decision Health 只作 health check，主指标是 Support Quality、Hard-Negative Lifecycle、Criterion Grounding、Report Hygiene 和 Recovery Effectiveness。不要继续新增 runtime controller，也不要硬调 accept/reject 阈值。
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime-jsonl", type=Path, default=Path("outputs/results_main/review_infer/fallback_flaw_guard_v1_4b_fulltest39.jsonl"))
    parser.add_argument("--classifier-json", type=Path, default=Path("outputs/results_main/review_infer/final_view_unresolved_candidate_classifier_v1.json"))
    parser.add_argument("--report-json", type=Path, default=Path("outputs/results_main/review_infer/final_view_report_renderer_v1_summary.json"))
    parser.add_argument("--method-json", type=Path, default=Path("outputs/results_main/review_infer/fallback_flaw_guard_v1_method_soundness_audit.json"))
    parser.add_argument("--recommendation-json", type=Path, default=Path("outputs/results_main/review_infer/fallback_flaw_guard_v1_recommendation_policy.json"))
    parser.add_argument("--output-json", type=Path, default=Path("outputs/results_main/review_infer/mainline_final_v1_unified_fulltest39_metrics.json"))
    parser.add_argument("--doc-dir", type=Path, default=Path("docs/experiments/mainline_current"))
    args = parser.parse_args()

    runtime_rows = load_jsonl(args.runtime_jsonl)
    classifier = load_json(args.classifier_json)
    report = load_json(args.report_json)
    method = load_json(args.method_json)
    recommendation = load_json(args.recommendation_json)
    payload = {
        "inputs": {k: str(v) for k, v in vars(args).items() if k.endswith("json") or k.endswith("jsonl")},
        "runtime": summarize_runtime(runtime_rows),
        "classifier": summarize_classifier(classifier),
        "classifier_rows": classifier.get("rows", []),
        "report_renderer": summarize_report_renderer(report),
        "report_rows": report.get("rows", []),
        "method_soundness": summarize_method_soundness(method),
        "recommendation_policy": summarize_recommendation_policy(recommendation),
    }
    write_json(args.output_json, payload)
    write_md(args.doc_dir / "MAINLINE_FINAL_V1_UNIFIED_FULLTEST39_REPORT.md", render_report(payload))
    write_md(args.doc_dir / "MAINLINE_FINAL_V1_UNIFIED_CASE_TABLE.md", render_case_table(payload))
    write_md(args.doc_dir / "MAINLINE_FINAL_V1_UNIFIED_NEXT_STEP_DECISION.md", render_decision(payload))
    print(json.dumps({"output_json": str(args.output_json), "runtime": payload["runtime"]["summary"], "classifier": payload["classifier"], "report_renderer": payload["report_renderer"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
