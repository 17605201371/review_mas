#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agent_system.environments.env_package.review.support_quality import derive_sample_support_summary, evidence_section_bucket

SUPPORT_STANCES = {"supports", "partially_supports"}


def norm(value: Any) -> str:
    return str(value or "").strip().lower()


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def load_gold_labels(path: Path | None) -> Dict[str, str]:
    if not path:
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    labels: Dict[str, str] = {}
    items = data.get("labels", data if isinstance(data, list) else []) if isinstance(data, (dict, list)) else []
    for item in items:
        if not isinstance(item, dict):
            continue
        pid = str(item.get("paper_id") or item.get("id") or "").strip()
        gold = norm(item.get("gold_decision") or item.get("decision") or item.get("label"))
        if pid and gold in {"accept", "reject"}:
            labels[pid] = gold
    return labels


def validate_gold_labels(rows: List[Dict[str, Any]], gold_labels: Dict[str, str], name: str) -> None:
    if not gold_labels:
        return
    missing = [str(row.get("paper_id")) for row in rows if str(row.get("paper_id")) not in gold_labels]
    if missing:
        raise ValueError(f"{name} has {len(missing)} rows missing locked gold labels: {missing[:8]}")


def infer_gold(row: Dict[str, Any], gold_labels: Dict[str, str] | None = None) -> str:
    pid = str(row.get("paper_id") or "")
    if gold_labels:
        return gold_labels.get(pid, "unknown")
    pred = norm(row.get("final_decision") or (row.get("review_state") or {}).get("final_decision"))
    corr = row.get("accept_reject_correct")
    if pred in {"accept", "reject"} and corr in {0, 0.0, 1, 1.0}:
        return pred if corr in {1, 1.0} else ("accept" if pred == "reject" else "reject")
    return norm(row.get("ground_truth_decision") or row.get("gold_decision")) or "unknown"


def is_real_claim(claim_id: Any) -> bool:
    cid = norm(claim_id)
    return bool(cid) and "fallback" not in cid and "general" not in cid


def support_bucket(ev: Dict[str, Any]) -> str:
    return evidence_section_bucket(ev)


def binary_metrics(rows: List[Dict[str, Any]], pred_key: str = "final_decision", gold_labels: Dict[str, str] | None = None) -> Dict[str, Any]:
    tp = tn = fp = fn = 0
    false_accept_ids: List[str] = []
    false_reject_ids: List[str] = []
    recovered_accept_ids: List[str] = []
    for row in rows:
        gold = infer_gold(row, gold_labels)
        pred = norm(row.get(pred_key) or (row.get("review_state") or {}).get(pred_key))
        if pred not in {"accept", "reject"}:
            pred = "reject"
        if gold == "accept" and pred == "accept":
            tp += 1
            recovered_accept_ids.append(str(row.get("paper_id")))
        elif gold == "reject" and pred == "reject":
            tn += 1
        elif gold == "reject" and pred == "accept":
            fp += 1
            false_accept_ids.append(str(row.get("paper_id")))
        elif gold == "accept" and pred == "reject":
            fn += 1
            false_reject_ids.append(str(row.get("paper_id")))
    n = len(rows) or 1
    accept_recall = tp / (tp + fn) if (tp + fn) else 0
    reject_recall = tn / (tn + fp) if (tn + fp) else 0
    accept_precision = tp / (tp + fp) if (tp + fp) else 0
    reject_precision = tn / (tn + fn) if (tn + fn) else 0
    accept_f1 = 2 * accept_precision * accept_recall / (accept_precision + accept_recall) if (accept_precision + accept_recall) else 0
    reject_f1 = 2 * reject_precision * reject_recall / (reject_precision + reject_recall) if (reject_precision + reject_recall) else 0
    return {
        "accuracy": (tp + tn) / n,
        "accept_recall": accept_recall,
        "reject_recall": reject_recall,
        "macro_f1": (accept_f1 + reject_f1) / 2,
        "predicted_accept_count": tp + fp,
        "predicted_reject_count": tn + fn,
        "false_accept_ids": false_accept_ids,
        "false_reject_ids": false_reject_ids,
        "recovered_accept_ids": recovered_accept_ids,
    }


def summarize_run(rows: List[Dict[str, Any]], gold_labels: Dict[str, str] | None = None) -> Dict[str, Any]:
    c = Counter()
    per_case: List[Dict[str, Any]] = []
    for row in rows:
        state = row.get("review_state") or {}
        gold = infer_gold(row, gold_labels)
        pred = norm(row.get("final_decision") or state.get("final_decision")) or "unknown"
        c[f"gold_{gold}"] += 1
        c[f"pred_{pred}"] += 1
        c[f"{gold}->{pred}"] += 1
        real_strong = nonabstract = empirical = fallback_strong = fallback_extraction_strong = real_medium = 0
        for ev in state.get("evidence_map", []) or []:
            stance = norm(ev.get("stance"))
            strength = norm(ev.get("strength"))
            claim_id = ev.get("claim_id")
            if stance in SUPPORT_STANCES and strength == "strong":
                if norm(ev.get("source")) == "fallback-extraction":
                    fallback_extraction_strong += 1
                if is_real_claim(claim_id):
                    real_strong += 1
                    bucket = support_bucket(ev)
                    if bucket != "abstract":
                        nonabstract += 1
                    if bucket in {"empirical", "table_or_figure"}:
                        empirical += 1
                else:
                    fallback_strong += 1
            if stance in SUPPORT_STANCES and strength == "medium" and is_real_claim(claim_id):
                real_medium += 1
        evidence_turns = fallback_payloads = broad_target_turns = recovery_commits = patch_emitted = patch_committed = 0
        visible = Counter()
        policy_sources = Counter()
        evidence_json_status = Counter()
        progression_gate_triggered = 0
        support_formation_pass_triggered = 0
        for turn in row.get("turn_logs", []) or []:
            policy_source = norm(turn.get("policy_source"))
            if policy_source:
                policy_sources[policy_source] += 1
            if turn.get("progression_gate_triggered"):
                progression_gate_triggered += 1
            if turn.get("support_formation_pass_triggered"):
                support_formation_pass_triggered += 1
            status = norm(turn.get("evidence_json_parse_status"))
            if status:
                evidence_json_status[status] += 1
            if turn.get("recovery_patch_emitted"):
                patch_emitted += 1
            if turn.get("recovery_patch_committed") or turn.get("recovery_committed"):
                patch_committed += 1
            if turn.get("recovery_patch_committed") or turn.get("recovery_committed"):
                recovery_commits += 1
            if "Evidence Agent" in (turn.get("selected_agents") or []) or turn.get("evidence_context_mode"):
                evidence_turns += 1
                for key in ["method", "results", "conclusion", "table_or_figure"]:
                    if turn.get(f"evidence_context_contains_{key}"):
                        visible[key] += 1
                if len(turn.get("final_action_target_claim_ids") or []) > 1:
                    broad_target_turns += 1
                if turn.get("evidence_json_fallback_payload_used"):
                    fallback_payloads += 1
                for worker_payload in turn.get("worker_payloads", []) or []:
                    if worker_payload.get("agent_id") != "Evidence Agent":
                        continue
                    payload = worker_payload.get("payload") or {}
                    if any(str(ev.get("evidence_id", "")).startswith(("evidence-fallback-", "evidence-general-")) for ev in payload.get("evidence_map", []) or []):
                        fallback_payloads += 1
        flaw_count = len(state.get("flaw_candidates", []) or [])
        unresolved_count = len(state.get("unresolved_questions", []) or [])
        gap_count = len(state.get("evidence_gaps", []) or [])
        support_summary = derive_sample_support_summary(state)
        c["method_strong_support_total"] += support_summary.get("method_support_total", 0)
        c["table_or_figure_strong_support_total"] += support_summary.get("table_or_figure_support_total", 0)
        c["ablation_strong_support_total"] += support_summary.get("ablation_support_total", 0)
        c["independent_support_group_total"] += support_summary.get("independent_support_group_total", 0)
        c["claims_with_2plus_independent_support"] += support_summary.get("claims_with_2plus_independent_support", 0)
        c["claims_with_method_plus_result_support"] += support_summary.get("claims_with_method_plus_result_support", 0)
        c["real_strong_support_total"] += real_strong
        c["nonabstract_strong_support_total"] += nonabstract
        c["empirical_strong_support_total"] += empirical
        c["fallback_strong_support_total"] += fallback_strong
        c["fallback_extraction_strong_support_total"] += fallback_extraction_strong
        c["real_medium_support_total"] += real_medium
        c["evidence_turns"] += evidence_turns
        c["evidence_fallback_payloads"] += fallback_payloads
        c["broad_target_turns"] += broad_target_turns
        c["patch_emitted_count"] += patch_emitted
        c["patch_committed_count"] += patch_committed
        c["rows_with_any_commit"] += int(patch_committed > 0)
        c["progression_gate_triggered_turns"] += progression_gate_triggered
        c["support_formation_pass_triggered_turns"] += support_formation_pass_triggered
        for source, count in policy_sources.items():
            c[f"policy_source::{source}"] += count
        for status, count in evidence_json_status.items():
            c[f"evidence_json_status::{status}"] += count
        c["evidence_json_status_turn_count"] += sum(evidence_json_status.values())
        c["evidence_json_invalid_or_missing_count"] += sum(
            evidence_json_status.get(status, 0)
            for status in ("no_json_object", "invalid_json", "truncated_tagged_json")
        )
        c["evidence_json_fallback_used_count"] += evidence_json_status.get("fallback_used", 0)
        c["unresolved_count"] += unresolved_count
        c["evidence_gap_count"] += gap_count
        c["flaw_count"] += flaw_count
        c["rows_with_2plus_real_strong_support"] += int(real_strong >= 2)
        c["accept_rows_with_2plus_real_strong_support"] += int(gold == "accept" and real_strong >= 2)
        per_case.append({
            "paper_id": row.get("paper_id"),
            "gold_decision": gold,
            "final_decision": pred,
            "real_strong_support": real_strong,
            "nonabstract_strong_support": nonabstract,
            "empirical_strong_support": empirical,
            "independent_support_groups": support_summary.get("independent_support_group_total", 0),
            "claims_with_method_plus_result_support": support_summary.get("claims_with_method_plus_result_support", 0),
            "real_medium_support": real_medium,
            "fallback_strong_support": fallback_strong,
            "evidence_turns": evidence_turns,
            "fallback_payloads": fallback_payloads,
            "broad_target_turns": broad_target_turns,
            "unresolved_count": unresolved_count,
            "evidence_gap_count": gap_count,
            "flaw_count": flaw_count,
            "patch_committed_count": patch_committed,
            "reward": row.get("reward"),
        })
    summary = dict(c)
    metrics = binary_metrics(rows, gold_labels=gold_labels)
    summary.update(metrics)
    summary["gold_counts"] = {"accept": summary.get("gold_accept", 0), "reject": summary.get("gold_reject", 0), "unknown": summary.get("gold_unknown", 0)}
    summary["prediction_counts"] = {"accept": summary.get("pred_accept", 0), "reject": summary.get("pred_reject", 0), "unknown": summary.get("pred_unknown", 0)}
    summary["evidence_json_status_counts"] = {
        key.split("::", 1)[1]: value
        for key, value in summary.items()
        if key.startswith("evidence_json_status::")
    }
    summary["policy_source_counts"] = {
        key.split("::", 1)[1]: value
        for key, value in summary.items()
        if key.startswith("policy_source::")
    }
    summary["legacy_controller_active_turns"] = (
        summary["policy_source_counts"].get("sticky_recovery_bias", 0)
        + summary["policy_source_counts"].get("progression_gate_override", 0)
        + summary.get("progression_gate_triggered_turns", 0)
    )
    summary["avg_reward"] = sum(float(row.get("reward") or 0) for row in rows) / (len(rows) or 1)
    summary["evidence_fallback_payload_rate"] = summary.get("evidence_fallback_payloads", 0) / (summary.get("evidence_turns", 1) or 1)
    summary["broad_target_turn_rate"] = summary.get("broad_target_turns", 0) / (summary.get("evidence_turns", 1) or 1)
    summary["strong_support_binding_precision"] = summary.get("real_strong_support_total", 0) / (summary.get("real_strong_support_total", 0) + summary.get("fallback_strong_support_total", 0) or 1)
    return {"summary": summary, "case_rows": per_case}


def extract_criterion_summary(path: Path) -> Dict[str, Any]:
    data = load_json(path)
    agg = data.get("aggregate", {}) if isinstance(data, dict) else {}
    rows = len(data.get("rows", []) or []) if isinstance(data, dict) else 0
    out: Dict[str, Any] = {"rows": rows}
    for dim in ["novelty_originality", "significance_contribution", "technical_soundness", "empirical_adequacy", "clarity_reproducibility"]:
        covered = int(agg.get(f"covered_{dim}", 0) or 0)
        grounded = int(agg.get(f"grounded_{dim}", 0) or 0)
        out[f"{dim}_coverage_rate"] = covered / rows if rows else 0
        out[f"{dim}_grounded_rate"] = grounded / rows if rows else 0
    out["total_covered"] = agg.get("total_covered", 0)
    out["total_grounded"] = agg.get("total_grounded", 0)
    out["total_unsupported"] = agg.get("total_unsupported", 0)
    out["total_meta_leakage"] = agg.get("total_meta_leakage", 0)
    return out


def write_report(payload: Dict[str, Any], path: Path) -> None:
    retained = payload["retained_integrated"]["summary"]
    isolation = payload["isolation_v1_1"].get("summary", {})
    if not isolation:
        isolation = {
            "accuracy": 0.0,
            "accept_recall": 0.0,
            "reject_recall": 0.0,
            "macro_f1": 0.0,
            "predicted_accept_count": 0,
        }
    flaw = payload.get("flaw_lifecycle", {})
    flaw_metrics = flaw.get("metrics", {})
    criterion = payload.get("criterion_dimension", {})
    lines = [
        "# Mainline-Final-v1 4B Fulltest39 Dry Run Report",
        "",
        "## 结论",
        "",
        "本报告是主试验前 dry run，不新增模型推理。结果显示：runtime 输入卫生和 evidence binding 已经比早期稳定，但 final decision 仍然 reject-skew，且少量 accept 可能是 false accept；主要论文结论不应建立在 accept/reject accuracy 上，而应报告 evidence binding、support quality、final-view hygiene、criterion grounding 与 meta-leakage。",
        "",
        "## Decision Health",
        "",
        "| dataset | accuracy | accept recall | reject recall | macro-F1 | predicted accept |",
        "|---|---:|---:|---:|---:|---:|",
        f"| retained integrated | {retained['accuracy']:.4f} | {retained['accept_recall']:.4f} | {retained['reject_recall']:.4f} | {retained['macro_f1']:.4f} | {retained['predicted_accept_count']} |",
        f"| isolation v1.1 | {isolation['accuracy']:.4f} | {isolation['accept_recall']:.4f} | {isolation['reject_recall']:.4f} | {isolation['macro_f1']:.4f} | {isolation['predicted_accept_count']} |",
        "",
        "## Evidence / Support Quality",
        "",
        "| dataset | real strong | nonabstract strong | empirical strong | method | table/figure | ablation | independent groups | claims 2+ independent | fallback strong | fallback payload rate |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        f"| retained integrated | {retained.get('real_strong_support_total',0)} | {retained.get('nonabstract_strong_support_total',0)} | {retained.get('empirical_strong_support_total',0)} | {retained.get('method_strong_support_total',0)} | {retained.get('table_or_figure_strong_support_total',0)} | {retained.get('ablation_strong_support_total',0)} | {retained.get('independent_support_group_total',0)} | {retained.get('claims_with_2plus_independent_support',0)} | {retained.get('fallback_strong_support_total',0)} | {retained.get('evidence_fallback_payload_rate',0):.4f} |",
        f"| isolation v1.1 | {isolation.get('real_strong_support_total',0)} | {isolation.get('nonabstract_strong_support_total',0)} | {isolation.get('empirical_strong_support_total',0)} | {isolation.get('method_strong_support_total',0)} | {isolation.get('table_or_figure_strong_support_total',0)} | {isolation.get('ablation_strong_support_total',0)} | {isolation.get('independent_support_group_total',0)} | {isolation.get('claims_with_2plus_independent_support',0)} | {isolation.get('fallback_strong_support_total',0)} | {isolation.get('evidence_fallback_payload_rate',0):.4f} |",
        "",
        "## State / Recovery / Flaw View",
        "",
        "| dataset | unresolved | evidence gaps | flaws | patch emitted | patch committed | rows any commit | broad target turn rate |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
        f"| retained integrated | {retained.get('unresolved_count',0)} | {retained.get('evidence_gap_count',0)} | {retained.get('flaw_count',0)} | {retained.get('patch_emitted_count',0)} | {retained.get('patch_committed_count',0)} | {retained.get('rows_with_any_commit',0)} | {retained.get('broad_target_turn_rate',0):.4f} |",
        f"| isolation v1.1 | {isolation.get('unresolved_count',0)} | {isolation.get('evidence_gap_count',0)} | {isolation.get('flaw_count',0)} | {isolation.get('patch_emitted_count',0)} | {isolation.get('patch_committed_count',0)} | {isolation.get('rows_with_any_commit',0)} | {isolation.get('broad_target_turn_rate',0):.4f} |",
        "",
        "## Final-View Flaw Lifecycle",
        "",
        f"- derived labels: `{flaw_metrics.get('derived_label_counts', {})}`",
        f"- strict recovered accepts: `{flaw_metrics.get('derived_strict_accept_like_only', {}).get('recovered_accept_ids', [])}`",
        f"- strict false accepts: `{flaw_metrics.get('derived_strict_accept_like_only', {}).get('false_accept_ids', [])}`",
        "- 解读：flaw lifecycle 不恢复 strict accept，但把大量样本从 hard reject 转成 borderline / not_assessable，说明 report 层必须区分论文缺陷与系统/截断/未验证候选缺陷。",
        "",
        "## Criterion Coverage / Grounding",
        "",
        "| criterion | coverage rate | grounded rate |",
        "|---|---:|---:|",
    ]
    for dim in ["novelty_originality", "significance_contribution", "technical_soundness", "empirical_adequacy", "clarity_reproducibility"]:
        lines.append(f"| `{dim}` | {criterion.get(dim + '_coverage_rate', 0):.4f} | {criterion.get(dim + '_grounded_rate', 0):.4f} |")
    lines += [
        "",
        "## Controller / Metric Hygiene",
        "",
        "| dataset | evidence JSON status turns | invalid/missing JSON | fallback-used status | progression gate turns | support formation pass turns | legacy controller active turns |",
        "|---|---:|---:|---:|---:|---:|---:|",
        f"| retained integrated | {retained.get('evidence_json_status_turn_count',0)} | {retained.get('evidence_json_invalid_or_missing_count',0)} | {retained.get('evidence_json_fallback_used_count',0)} | {retained.get('progression_gate_triggered_turns',0)} | {retained.get('support_formation_pass_triggered_turns',0)} | {retained.get('legacy_controller_active_turns',0)} |",
        f"| isolation v1.1 | {isolation.get('evidence_json_status_turn_count',0)} | {isolation.get('evidence_json_invalid_or_missing_count',0)} | {isolation.get('evidence_json_fallback_used_count',0)} | {isolation.get('progression_gate_triggered_turns',0)} | {isolation.get('support_formation_pass_triggered_turns',0)} | {isolation.get('legacy_controller_active_turns',0)} |",
        "",
        "注意：`invalid/missing JSON` 只统计 `no_json_object` / `invalid_json` / `truncated_tagged_json`，不再把所有 evidence status turn 误命名为 parse errors。`legacy controller active turns` 用于暴露 sticky/progression gate 是否仍污染主线解释。",
        "",
        "## Go / No-Go",
        "",
        "当前建议：可以进入 `Mainline-Final-v1` 论文主线收口和 9B 小确认，但不要把当前 4B fulltest39 当作正式主实验结果。正式主实验前应先固定 unified metrics，并把 final-view flaw lifecycle / criterion grounding 作为 report/hygiene 层输出，同时清理或明确保留旧 controller。",
        "",
        "不要做：Support Formation Pass runtime、Evidence Context v3、sticky/throttle/gate、live state hygiene mutation、final decision 阈值硬调。",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_case_table(payload: Dict[str, Any], path: Path) -> None:
    rows = payload["retained_integrated"]["case_rows"]
    flaw_cases = {row["paper_id"]: row for row in payload.get("flaw_lifecycle", {}).get("case_rows", [])}
    lines = ["# Mainline-Final-v1 Case Table", "", "| paper_id | gold | final | derived flaw label | real strong | nonabstract strong | empirical strong | independent groups | method+result claims | real medium | fallback payloads | unresolved | flaws | reward |", "|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for row in rows:
        flaw = flaw_cases.get(str(row["paper_id"]), {})
        lines.append(
            f"| {row['paper_id']} | {row['gold_decision']} | {row['final_decision']} | {flaw.get('derived_label','')} | "
            f"{row['real_strong_support']} | {row['nonabstract_strong_support']} | {row['empirical_strong_support']} | {row.get('independent_support_groups', 0)} | {row.get('claims_with_method_plus_result_support', 0)} | {row['real_medium_support']} | "
            f"{row['fallback_payloads']} | {row['unresolved_count']} | {row['flaw_count']} | {float(row.get('reward') or 0):.4f} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--retained", default="INTEGRATED_MAINLINE_4B_FULLTEST39_RETAINED.jsonl")
    parser.add_argument("--isolation", default="outputs/results_main/review_infer/evidence_fallback_target_isolation_v1_1_fulltest39.jsonl")
    parser.add_argument("--flaw-lifecycle", default="outputs/results_main/review_infer/final_view_flaw_lifecycle_v1_fulltest39.json")
    parser.add_argument("--criterion", default="docs/experiments/mainline_current/criterion_dimension_summary.json")
    parser.add_argument("--output-json", default="outputs/results_main/review_infer/mainline_final_v1_4b_fulltest39_summary.json")
    parser.add_argument("--report", default="docs/experiments/mainline_current/MAINLINE_FINAL_V1_4B_FULLTEST39_REPORT.md")
    parser.add_argument("--case-table", default="docs/experiments/mainline_current/MAINLINE_FINAL_V1_4B_CASE_TABLE.md")
    parser.add_argument("--gold-labels", default="")
    args = parser.parse_args()

    retained_rows = load_jsonl(Path(args.retained))
    isolation_path = Path(args.isolation) if args.isolation else None
    isolation_rows = load_jsonl(isolation_path) if isolation_path and isolation_path.is_file() else []
    gold_labels = load_gold_labels(Path(args.gold_labels)) if args.gold_labels else {}
    validate_gold_labels(retained_rows, gold_labels, "retained")
    if isolation_rows:
        validate_gold_labels(isolation_rows, gold_labels, "isolation")
    payload = {
        "retained_input": args.retained,
        "isolation_input": args.isolation,
        "gold_labels_input": args.gold_labels,
        "retained_integrated": summarize_run(retained_rows, gold_labels),
        "isolation_v1_1": summarize_run(isolation_rows, gold_labels) if isolation_rows else {"summary": {}, "case_rows": []},
        "flaw_lifecycle": load_json(Path(args.flaw_lifecycle)),
        "criterion_dimension": extract_criterion_summary(Path(args.criterion)),
    }
    out = Path(args.output_json)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    report = Path(args.report)
    report.parent.mkdir(parents=True, exist_ok=True)
    write_report(payload, report)
    write_case_table(payload, Path(args.case_table))
    print(json.dumps({
        "retained_summary": payload["retained_integrated"]["summary"],
        "isolation_summary": payload["isolation_v1_1"]["summary"],
        "flaw_labels": payload["flaw_lifecycle"].get("metrics", {}).get("derived_label_counts", {}),
        "criterion": payload["criterion_dimension"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
