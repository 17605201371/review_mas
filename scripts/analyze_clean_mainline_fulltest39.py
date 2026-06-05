#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence

try:
    import pyarrow.parquet as pq
except Exception:  # pragma: no cover
    pq = None

SUPPORT_STANCES = {"supports", "partially_supports"}
LEGACY_POLICY_SOURCES = {"sticky_recovery_bias", "progression_gate_override", "support_formation_override"}
LEGACY_BOOL_FIELDS = {"progression_gate_triggered", "support_formation_pass_triggered"}


def norm(value: Any) -> str:
    return str(value or "").strip().lower()


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


def load_gold_labels(dataset_path: Path) -> Dict[str, str]:
    gold: Dict[str, str] = {}
    if not dataset_path.exists() or pq is None:
        return gold
    rows = pq.read_table(dataset_path).to_pylist()
    for row in rows:
        env = row.get("env_kwargs") or {}
        pid = row.get("id") or env.get("paper_id")
        decision = norm(row.get("decision") or env.get("ground_truth_decision"))
        if pid and decision in {"accept", "reject"}:
            gold[str(pid)] = decision
    return gold


def infer_gold(row: Dict[str, Any], gold_map: Dict[str, str]) -> str:
    pid = str(row.get("paper_id") or "")
    if pid in gold_map:
        return gold_map[pid]
    explicit = norm(row.get("gold_decision") or row.get("ground_truth_decision"))
    if explicit in {"accept", "reject"}:
        return explicit
    pred = norm(row.get("final_decision") or (row.get("review_state") or {}).get("final_decision"))
    try:
        correct = float(row.get("accept_reject_correct", row.get("decision_correct")))
    except (TypeError, ValueError):
        return "unknown"
    if pred in {"accept", "reject"}:
        return pred if correct >= 0.5 else ("reject" if pred == "accept" else "accept")
    return "unknown"


def is_real_claim(claim_id: Any) -> bool:
    cid = norm(claim_id)
    return bool(cid) and "fallback" not in cid and "general" not in cid and "unbound" not in cid


def source_bucket(ev: Dict[str, Any]) -> str:
    text = " ".join(str(ev.get(k, "")) for k in ["source", "support_source_bucket", "support_quality", "support_quality_reason", "binding_rationale", "evidence"]).lower()
    if "abstract" in text:
        return "abstract"
    if "ablation" in text:
        return "ablation"
    if any(x in text for x in ["table", "figure", "fig."]):
        return "table_or_figure"
    if any(x in text for x in ["experiment", "evaluation", "result", "baseline", "dataset", "metric", "benchmark", "performance"]):
        return "empirical"
    if any(x in text for x in ["method", "approach", "model", "framework", "algorithm", "architecture"]):
        return "method"
    return "unknown"


def binary_metrics(case_rows: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    tp = tn = fp = fn = 0
    false_accept_ids: List[str] = []
    false_reject_ids: List[str] = []
    recovered_accept_ids: List[str] = []
    for row in case_rows:
        gold = row["gold_decision"]
        pred = row["final_decision"] if row["final_decision"] in {"accept", "reject"} else "reject"
        pid = row["paper_id"]
        if gold == "accept" and pred == "accept":
            tp += 1
            recovered_accept_ids.append(pid)
        elif gold == "reject" and pred == "reject":
            tn += 1
        elif gold == "reject" and pred == "accept":
            fp += 1
            false_accept_ids.append(pid)
        elif gold == "accept" and pred == "reject":
            fn += 1
            false_reject_ids.append(pid)
    n = max(1, tp + tn + fp + fn)
    accept_recall = tp / max(1, tp + fn)
    reject_recall = tn / max(1, tn + fp)
    accept_precision = tp / max(1, tp + fp)
    reject_precision = tn / max(1, tn + fn)
    accept_f1 = 0.0 if accept_precision + accept_recall == 0 else 2 * accept_precision * accept_recall / (accept_precision + accept_recall)
    reject_f1 = 0.0 if reject_precision + reject_recall == 0 else 2 * reject_precision * reject_recall / (reject_precision + reject_recall)
    return {
        "accuracy": round((tp + tn) / n, 4),
        "macro_f1": round((accept_f1 + reject_f1) / 2, 4),
        "accept_recall": round(accept_recall, 4),
        "reject_recall": round(reject_recall, 4),
        "predicted_accept_count": tp + fp,
        "predicted_reject_count": tn + fn,
        "true_accept_count": tp,
        "true_reject_count": tn,
        "false_accept_count": fp,
        "false_reject_count": fn,
        "false_accept_ids": false_accept_ids,
        "false_reject_ids": false_reject_ids,
        "recovered_accept_ids": recovered_accept_ids,
    }


def analyze(rows: Sequence[Dict[str, Any]], gold_map: Dict[str, str]) -> Dict[str, Any]:
    c = Counter()
    status_counts = Counter()
    policy_counts = Counter()
    failure_codes = Counter()
    source_commit_counts = Counter()
    case_rows: List[Dict[str, Any]] = []

    for row in rows:
        state = row.get("review_state") or {}
        pid = str(row.get("paper_id") or "")
        gold = infer_gold(row, gold_map)
        pred = norm(row.get("final_decision") or state.get("final_decision")) or "unknown"
        c[f"gold_{gold}"] += 1
        c[f"pred_{pred}"] += 1
        real = nonabstract = empirical = method = table_fig = ablation = abstract = fallback = fallback_extraction = unbound = 0
        support_claims = set()
        for ev in state.get("evidence_map", []) or []:
            if not isinstance(ev, dict):
                continue
            stance = norm(ev.get("stance"))
            strength = norm(ev.get("strength"))
            if stance not in SUPPORT_STANCES or strength != "strong":
                continue
            claim_id = ev.get("claim_id")
            if norm(ev.get("source")) == "fallback-extraction":
                fallback_extraction += 1
            if not is_real_claim(claim_id):
                fallback += 1
                if not claim_id:
                    unbound += 1
                continue
            real += 1
            support_claims.add(str(claim_id))
            bucket = source_bucket(ev)
            if bucket == "abstract":
                abstract += 1
            else:
                nonabstract += 1
            if bucket in {"empirical", "table_or_figure", "ablation"}:
                empirical += 1
            if bucket == "method":
                method += 1
            if bucket == "table_or_figure":
                table_fig += 1
            if bucket == "ablation":
                ablation += 1
        patch_emitted = patch_validated = patch_committed = fallback_payloads = legacy_turns = 0
        model_generated_commits = system_salvaged_commits = 0
        for turn in row.get("turn_logs", []) or []:
            status = norm(turn.get("evidence_json_parse_status"))
            if status:
                status_counts[status] += 1
            if turn.get("evidence_json_fallback_payload_used"):
                fallback_payloads += 1
            source = norm(turn.get("policy_source"))
            if source:
                policy_counts[source] += 1
            if source in LEGACY_POLICY_SOURCES or any(turn.get(field) for field in LEGACY_BOOL_FIELDS):
                legacy_turns += 1
            if turn.get("recovery_patch_emitted"):
                patch_emitted += 1
            if turn.get("recovery_patch_validated"):
                patch_validated += 1
            if turn.get("recovery_patch_committed") or turn.get("recovery_committed"):
                patch_committed += 1
                ps = norm(turn.get("recovery_patch_source")) or "unknown"
                source_commit_counts[ps] += 1
                if ps == "model_generated":
                    model_generated_commits += 1
                if ps == "system_salvaged":
                    system_salvaged_commits += 1
            fc = norm(turn.get("recovery_failure_code")) or norm(turn.get("emission_failure_code"))
            if fc:
                failure_codes[fc] += 1
        c["real_strong_support_total"] += real
        c["nonabstract_strong_support_total"] += nonabstract
        c["empirical_strong_support_total"] += empirical
        c["method_strong_support_total"] += method
        c["table_or_figure_strong_support_total"] += table_fig
        c["ablation_strong_support_total"] += ablation
        c["abstract_strong_support_total"] += abstract
        c["fallback_strong_support_total"] += fallback
        c["fallback_extraction_strong_support_total"] += fallback_extraction
        c["unbound_strong_support_total"] += unbound
        c["rows_with_2plus_real_strong_support"] += int(real >= 2)
        c["accept_rows_with_2plus_real_strong_support"] += int(gold == "accept" and real >= 2)
        c["rows_with_empirical_support"] += int(empirical > 0)
        c["accept_rows_with_empirical_support"] += int(gold == "accept" and empirical > 0)
        c["claims_with_strong_support_total"] += len(support_claims)
        c["unresolved_count"] += len(state.get("unresolved_questions", []) or [])
        c["evidence_gap_count"] += len(state.get("evidence_gaps", []) or [])
        c["flaw_count"] += len(state.get("flaw_candidates", []) or [])
        c["conflict_note_count"] += len(state.get("conflict_notes", []) or [])
        c["patch_emitted_count"] += patch_emitted
        c["patch_validated_count"] += patch_validated
        c["patch_committed_count"] += patch_committed
        c["rows_with_any_commit"] += int(patch_committed > 0)
        c["evidence_json_fallback_payload_turns"] += fallback_payloads
        c["legacy_controller_active_turns"] += legacy_turns
        c["model_generated_commit_count"] += model_generated_commits
        c["system_salvaged_commit_count"] += system_salvaged_commits
        c["reward_sum"] += float(row.get("reward") or 0)
        case_rows.append({
            "paper_id": pid,
            "gold_decision": gold,
            "final_decision": pred,
            "reward": round(float(row.get("reward") or 0), 4),
            "real_strong_support": real,
            "nonabstract_strong_support": nonabstract,
            "empirical_strong_support": empirical,
            "method_strong_support": method,
            "table_or_figure_strong_support": table_fig,
            "abstract_strong_support": abstract,
            "fallback_strong_support": fallback,
            "support_claim_count": len(support_claims),
            "unresolved_count": len(state.get("unresolved_questions", []) or []),
            "evidence_gap_count": len(state.get("evidence_gaps", []) or []),
            "flaw_count": len(state.get("flaw_candidates", []) or []),
            "patch_committed_count": patch_committed,
            "legacy_controller_active_turns": legacy_turns,
        })
    summary = dict(c)
    summary.update(binary_metrics(case_rows))
    summary["row_count"] = len(rows)
    summary["gold_counts"] = {"accept": summary.get("gold_accept", 0), "reject": summary.get("gold_reject", 0), "unknown": summary.get("gold_unknown", 0)}
    summary["prediction_counts"] = {"accept": summary.get("pred_accept", 0), "reject": summary.get("pred_reject", 0), "unknown": summary.get("pred_unknown", 0)}
    summary["avg_reward"] = round(summary.get("reward_sum", 0) / max(1, len(rows)), 4)
    summary["strong_support_binding_precision"] = round(summary.get("real_strong_support_total", 0) / max(1, summary.get("real_strong_support_total", 0) + summary.get("fallback_strong_support_total", 0)), 4)
    summary["evidence_json_status_counts"] = dict(status_counts)
    summary["evidence_json_status_turn_count"] = sum(status_counts.values())
    summary["evidence_json_invalid_or_missing_count"] = sum(status_counts.get(k, 0) for k in ["no_json_object", "invalid_json", "truncated_tagged_json"])
    summary["evidence_json_fallback_used_status_count"] = status_counts.get("fallback_used", 0)
    summary["policy_source_counts"] = dict(policy_counts)
    summary["recovery_failure_code_counts"] = dict(failure_codes)
    summary["recovery_commit_source_counts"] = dict(source_commit_counts)
    return {"summary": summary, "case_rows": case_rows}


def render_report(payload: Dict[str, Any], criterion_summary: Dict[str, Any] | None = None) -> str:
    s = payload["summary"]
    criterion_agg = ((criterion_summary or {}).get("aggregate") or {}) if isinstance(criterion_summary, dict) else {}
    criterion_rows = []
    for label in ["novelty_originality", "significance_contribution", "technical_soundness", "empirical_adequacy", "clarity_reproducibility"]:
        criterion_rows.append([
            label,
            criterion_agg.get(f"covered_{label}", "n/a"),
            criterion_agg.get(f"grounded_{label}", "n/a"),
            criterion_agg.get(f"unsupported_{label}", "n/a"),
            criterion_agg.get(f"meta_leakage_{label}", "n/a"),
        ])
    decision_note = "这轮是干净主线 dry run：旧 sticky / progression gate / support formation pass 触发计数为 0。它可以作为后续论文结果包和 9B 确认的基线，但仍不是正式主实验。"
    if s.get("accept_recall", 0) == 0:
        decision_note += " Runtime accept/reject 仍然没有恢复真实 accept，因此二分类推荐只能作为 health check。"
    return "\n\n".join([
        "# Mainline-Final-v1 Clean 4B Fulltest39 Report",
        "## 结论",
        decision_note,
        "## Decision Health",
        table(["metric", "value"], [
            ["rows", s.get("row_count")],
            ["gold_counts", s.get("gold_counts")],
            ["prediction_counts", s.get("prediction_counts")],
            ["accuracy", s.get("accuracy")],
            ["macro_f1", s.get("macro_f1")],
            ["accept_recall", s.get("accept_recall")],
            ["reject_recall", s.get("reject_recall")],
            ["predicted_accept_count", s.get("predicted_accept_count")],
            ["false_accept_ids", ", ".join(s.get("false_accept_ids") or []) or "无"],
            ["false_reject_ids", ", ".join(s.get("false_reject_ids") or []) or "无"],
            ["avg_reward", s.get("avg_reward")],
        ]),
        "## Evidence / Support Formation",
        table(["metric", "value"], [
            ["real_strong_support_total", s.get("real_strong_support_total")],
            ["nonabstract_strong_support_total", s.get("nonabstract_strong_support_total")],
            ["empirical_strong_support_total", s.get("empirical_strong_support_total")],
            ["method_strong_support_total", s.get("method_strong_support_total")],
            ["table_or_figure_strong_support_total", s.get("table_or_figure_strong_support_total")],
            ["ablation_strong_support_total", s.get("ablation_strong_support_total")],
            ["abstract_strong_support_total", s.get("abstract_strong_support_total")],
            ["fallback_strong_support_total", s.get("fallback_strong_support_total")],
            ["strong_support_binding_precision", s.get("strong_support_binding_precision")],
            ["rows_with_2plus_real_strong_support", s.get("rows_with_2plus_real_strong_support")],
            ["accept_rows_with_2plus_real_strong_support", s.get("accept_rows_with_2plus_real_strong_support")],
            ["rows_with_empirical_support", s.get("rows_with_empirical_support")],
            ["accept_rows_with_empirical_support", s.get("accept_rows_with_empirical_support")],
        ]),
        "## JSON / Fallback Hygiene",
        table(["metric", "value"], [
            ["evidence_json_status_counts", s.get("evidence_json_status_counts")],
            ["evidence_json_status_turn_count", s.get("evidence_json_status_turn_count")],
            ["evidence_json_invalid_or_missing_count", s.get("evidence_json_invalid_or_missing_count")],
            ["evidence_json_fallback_used_status_count", s.get("evidence_json_fallback_used_status_count")],
            ["evidence_json_fallback_payload_turns", s.get("evidence_json_fallback_payload_turns")],
        ]),
        "## State / Recovery",
        table(["metric", "value"], [
            ["unresolved_count", s.get("unresolved_count")],
            ["evidence_gap_count", s.get("evidence_gap_count")],
            ["flaw_count", s.get("flaw_count")],
            ["conflict_note_count", s.get("conflict_note_count")],
            ["patch_emitted_count", s.get("patch_emitted_count")],
            ["patch_validated_count", s.get("patch_validated_count")],
            ["patch_committed_count", s.get("patch_committed_count")],
            ["rows_with_any_commit", s.get("rows_with_any_commit")],
            ["model_generated_commit_count", s.get("model_generated_commit_count")],
            ["system_salvaged_commit_count", s.get("system_salvaged_commit_count")],
            ["recovery_failure_code_counts", s.get("recovery_failure_code_counts")],
        ]),
        "## Controller Cleanliness",
        table(["metric", "value"], [
            ["legacy_controller_active_turns", s.get("legacy_controller_active_turns")],
            ["policy_source_counts", s.get("policy_source_counts")],
        ]),
        "## Criterion Coverage / Grounding",
        table(["criterion", "covered", "grounded", "unsupported", "meta_leakage"], criterion_rows),
        "## 下一步",
        "这轮先保留为 clean 4B dry-run 基线。下一步不应再加 controller；应基于这份干净 jsonl 做 final recommendation policy / support-quality / hard-negative grounding 的离线收口，确认 recommendation 口径后再做 9B 小确认。",
    ])


def render_case_table(case_rows: Sequence[Dict[str, Any]]) -> str:
    rows = []
    for r in case_rows:
        rows.append([
            r["paper_id"], r["gold_decision"], r["final_decision"], r["reward"],
            r["real_strong_support"], r["nonabstract_strong_support"], r["empirical_strong_support"],
            r["table_or_figure_strong_support"], r["support_claim_count"],
            r["unresolved_count"], r["evidence_gap_count"], r["flaw_count"], r["patch_committed_count"],
            r["legacy_controller_active_turns"],
        ])
    return "# Mainline-Final-v1 Clean 4B Fulltest39 Case Table\n\n" + table([
        "paper_id", "gold", "final", "reward", "real_strong", "nonabstract", "empirical", "table_fig", "support_claims", "unresolved", "gaps", "flaws", "commits", "legacy_turns"
    ], rows)


def render_decision(payload: Dict[str, Any]) -> str:
    s = payload["summary"]
    keep = s.get("legacy_controller_active_turns") == 0 and s.get("fallback_strong_support_total") == 0
    formal_ready = False
    reasons = [
        "旧 controller 触发为 0，clean pipeline 口径已经可用于 dry run。",
        "fallback strong support 为 0，Evidence Binding 成果没有回退。",
    ]
    if s.get("accept_recall", 0) == 0:
        reasons.append("真实 accept 仍未被 runtime final decision 恢复，accept/reject 不能作为正式主指标。")
    if s.get("unresolved_count", 0) > 150:
        reasons.append("unresolved / evidence gap 负担仍高，final-view lifecycle 与 recommendation policy 仍需离线收口。")
    if s.get("evidence_json_invalid_or_missing_count", 0) > 0:
        reasons.append("Evidence JSON 仍有 invalid/missing 状态，但 fallback-used 很低，属于可监控风险。")
    return "\n".join([
        "# Mainline-Final-v1 Clean 4B Fulltest39 Decision",
        "",
        "## 结论",
        f"- dry_run_baseline_retained: `{str(keep)}`",
        f"- go_for_formal_main_experiment: `{str(formal_ready)}`",
        "- recommendation: 保留为干净 4B dry-run 基线；正式主试验前继续做 recommendation policy / support-quality / hard-negative grounding 的离线收口。",
        "",
        "## 理由",
        *[f"- {x}" for x in reasons],
        "",
        "## 禁止回退方向",
        "- 不回 sticky / throttle / progression gate。",
        "- 不做 live state hygiene mutation。",
        "- 不用强 support 数量直接硬调 accept/reject。",
    ])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--dataset", default="/reviewF/datasets/drmas_review/test.parquet", type=Path)
    parser.add_argument("--criterion-json", type=Path)
    parser.add_argument("--output-json", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--case-table", required=True, type=Path)
    parser.add_argument("--decision", required=True, type=Path)
    args = parser.parse_args()
    rows = load_jsonl(args.input)
    gold = load_gold_labels(args.dataset)
    payload = analyze(rows, gold)
    payload["input"] = str(args.input)
    payload["dataset"] = str(args.dataset)
    criterion = None
    if args.criterion_json and args.criterion_json.exists():
        criterion = json.loads(args.criterion_json.read_text(encoding="utf-8"))
        payload["criterion_summary"] = criterion
    write_json(args.output_json, payload)
    write_md(args.report, render_report(payload, criterion))
    write_md(args.case_table, render_case_table(payload["case_rows"]))
    write_md(args.decision, render_decision(payload))
    print(json.dumps({"summary": payload["summary"], "outputs": {"json": str(args.output_json), "report": str(args.report), "case_table": str(args.case_table), "decision": str(args.decision)}}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
