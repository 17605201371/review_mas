from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List


def read_jsonl(path: Path) -> List[Dict[str, Any]]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def state(row: Dict[str, Any]) -> Dict[str, Any]:
    return row.get("review_state") or {}


def gold_decision(row: Dict[str, Any]) -> str:
    pred = str(row.get("final_decision") or state(row).get("final_decision") or "").lower()
    correct = row.get("accept_reject_correct")
    if pred in {"accept", "reject"} and correct in {0, 0.0, 1, 1.0}:
        return pred if float(correct) >= 0.5 else ("reject" if pred == "accept" else "accept")
    return "unknown"


def is_real_claim(claim_id: Any) -> bool:
    value = str(claim_id or "")
    return bool(value) and not value.startswith("claim-fallback")


def payload_binding(evidence: Dict[str, Any]) -> str:
    status = str(evidence.get("binding_status") or "")
    if is_real_claim(evidence.get("claim_id")) and status in {"", "unchecked", "bound_real_claim"}:
        return "bound_real_claim"
    return status


def is_real_strong(evidence: Dict[str, Any], *, payload: bool) -> bool:
    binding = payload_binding(evidence) if payload else str(evidence.get("binding_status") or "")
    return (
        evidence.get("strength") == "strong"
        and evidence.get("stance") in {"supports", "partially_supports"}
        and is_real_claim(evidence.get("claim_id"))
        and binding == "bound_real_claim"
    )


def section(evidence: Dict[str, Any]) -> str:
    return str(evidence.get("support_source_bucket") or "unknown")


def evidence_turns(row: Dict[str, Any]) -> List[Dict[str, Any]]:
    turns = []
    for turn in row.get("turn_logs") or []:
        agents = [wrapped.get("agent_id") for wrapped in turn.get("worker_payloads") or [] if isinstance(wrapped, dict)]
        if "Evidence Agent" in agents or turn.get("effective_action_type") == "verify_evidence":
            turns.append(turn)
    return turns


def payload_evidence(row: Dict[str, Any]) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    for turn in row.get("turn_logs") or []:
        for wrapped in turn.get("worker_payloads") or []:
            if not isinstance(wrapped, dict):
                continue
            payload = wrapped.get("payload")
            if wrapped.get("agent_id") != "Evidence Agent" or not isinstance(payload, dict):
                continue
            for evidence in payload.get("evidence_map", []) or []:
                if isinstance(evidence, dict):
                    copied = dict(evidence)
                    copied["_turn_id"] = turn.get("turn_id")
                    items.append(copied)
    return items


def row_summary(row: Dict[str, Any]) -> Dict[str, Any]:
    st = state(row)
    p_items = payload_evidence(row)
    f_items = [ev for ev in st.get("evidence_map", []) or [] if isinstance(ev, dict)]
    p_strong = [ev for ev in p_items if is_real_strong(ev, payload=True)]
    f_strong = [ev for ev in f_items if is_real_strong(ev, payload=False)]
    ev_turns = evidence_turns(row)
    target_counts = [len(turn.get("target_claim_ids") or []) for turn in ev_turns]
    target_quality = Counter(str(turn.get("target_quality_label") or "unknown") for turn in ev_turns)
    policy_sources = Counter(str(turn.get("policy_source") or "unknown") for turn in ev_turns)
    return {
        "paper_id": row.get("paper_id"),
        "gold_decision": gold_decision(row),
        "pred_decision": str(row.get("final_decision") or st.get("final_decision") or "").lower(),
        "evidence_turns": len(ev_turns),
        "visible_method_turns": sum(bool(t.get("evidence_context_contains_method")) for t in ev_turns),
        "visible_results_turns": sum(bool(t.get("evidence_context_contains_results")) for t in ev_turns),
        "visible_table_or_figure_turns": sum(bool(t.get("evidence_context_contains_table_or_figure")) for t in ev_turns),
        "avg_target_count": round(sum(target_counts) / len(target_counts), 3) if target_counts else 0.0,
        "broad_target_turns": sum(count > 2 for count in target_counts),
        "fallback_target_turns": sum(bool(t.get("fallback_target_present")) for t in ev_turns),
        "target_quality_counts": dict(target_quality),
        "policy_sources": dict(policy_sources),
        "payload_evidence_count": len(p_items),
        "payload_real_strong": len(p_strong),
        "payload_nonabstract_strong": sum(section(ev) != "abstract" for ev in p_strong),
        "payload_empirical_strong": sum(section(ev) == "result_or_experiment" for ev in p_strong),
        "payload_method_strong": sum(section(ev) == "method_or_approach" for ev in p_strong),
        "final_real_strong": len(f_strong),
        "final_nonabstract_strong": sum(section(ev) != "abstract" for ev in f_strong),
        "final_empirical_strong": sum(section(ev) == "result_or_experiment" for ev in f_strong),
        "open_unresolved": sum(1 for q in st.get("unresolved_questions", []) or [] if not isinstance(q, dict) or q.get("status", "open") == "open"),
        "evidence_gaps": len(st.get("evidence_gaps", []) or []),
        "confirmed_major_or_critical": sum(1 for flaw in st.get("flaw_candidates", []) or [] if isinstance(flaw, dict) and flaw.get("status") == "confirmed" and flaw.get("severity") in {"major", "critical"}),
    }


def aggregate(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not rows:
        return {}
    keys = [
        "evidence_turns",
        "visible_method_turns",
        "visible_results_turns",
        "visible_table_or_figure_turns",
        "payload_evidence_count",
        "payload_real_strong",
        "payload_nonabstract_strong",
        "payload_empirical_strong",
        "payload_method_strong",
        "final_real_strong",
        "final_nonabstract_strong",
        "final_empirical_strong",
        "open_unresolved",
        "evidence_gaps",
        "confirmed_major_or_critical",
        "broad_target_turns",
        "fallback_target_turns",
    ]
    return {
        "rows": len(rows),
        **{f"avg_{key}": round(sum(row[key] for row in rows) / len(rows), 4) for key in keys},
        "rows_payload_2plus_real_strong": sum(row["payload_real_strong"] >= 2 for row in rows),
        "rows_final_2plus_real_strong": sum(row["final_real_strong"] >= 2 for row in rows),
    }


def write_docs(result: Dict[str, Any], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    accept = result["accept_aggregate"]
    reject = result["reject_aggregate"]
    lines = ["# Accept Support Failure Audit v1\n\n"]
    lines.append("本审计只读已有 fulltest39 jsonl，不改 runtime、不重跑模型。目标是解释 gold accept 为什么在 payload lineage 层仍缺少足够 real strong support。\n\n")
    lines.append("## Accept vs Reject aggregate\n\n")
    lines.append("| group | rows | avg evidence turns | avg payload real strong | rows payload 2+ | avg final real strong | rows final 2+ | avg visible results turns | avg broad target turns | avg unresolved | avg evidence gaps |\n")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|\n")
    for name, data in [("gold_accept", accept), ("gold_reject", reject)]:
        lines.append(
            f"| {name} | {data.get('rows',0)} | {data.get('avg_evidence_turns',0)} | {data.get('avg_payload_real_strong',0)} | {data.get('rows_payload_2plus_real_strong',0)} | "
            f"{data.get('avg_final_real_strong',0)} | {data.get('rows_final_2plus_real_strong',0)} | {data.get('avg_visible_results_turns',0)} | {data.get('avg_broad_target_turns',0)} | "
            f"{data.get('avg_open_unresolved',0)} | {data.get('avg_evidence_gaps',0)} |\n"
        )
    lines.append("\n## 结论\n\n")
    lines.append("如果 gold accept 在 payload 层也缺少 2+ real strong support，那么瓶颈不是 final decision，而是 accept-side evidence formation：Evidence Agent 虽然能看到 method/results/table，但没有把这些上下文稳定转成支持 gold-accept 论文的真实 claim evidence。\n")
    (output_dir / "ACCEPT_SUPPORT_FAILURE_AUDIT_V1.md").write_text("".join(lines))

    case_lines = ["# Accept Support Failure Case Table v1\n\n"]
    case_lines.append("| paper_id | gold | pred | ev_turns | payload_real | payload_nonabs | payload_empirical | final_real | visible_results | broad_targets | unresolved | gaps | confirmed_major |\n")
    case_lines.append("|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|\n")
    for row in result["case_table"]:
        case_lines.append(
            f"| {row['paper_id']} | {row['gold_decision']} | {row['pred_decision']} | {row['evidence_turns']} | {row['payload_real_strong']} | "
            f"{row['payload_nonabstract_strong']} | {row['payload_empirical_strong']} | {row['final_real_strong']} | {row['visible_results_turns']} | "
            f"{row['broad_target_turns']} | {row['open_unresolved']} | {row['evidence_gaps']} | {row['confirmed_major_or_critical']} |\n"
        )
    (output_dir / "ACCEPT_SUPPORT_FAILURE_CASE_TABLE_V1.md").write_text("".join(case_lines))

    decision = ["# Accept Support Failure Next Step\n\n"]
    decision.append("## 当前判断\n\n")
    decision.append("final-view lineage 证明 payload-to-state 有明显损失，但 accept 样本本身在 payload 层仍没有足够 positive support。因此下一步不应把 lineage support 直接接入 decision，也不应调 accept 阈值。\n\n")
    decision.append("## 下一刀\n\n")
    decision.append("建议做 `Accept-Side Evidence Formation Audit / Context v2`：只围绕 gold accept 论文，检查 Evidence Agent 的 target claim 是否覆盖核心贡献、是否需要更好的 result/table/method snippet selection，以及是否需要让 Evidence Agent 对同一真实 claim 输出多条独立支持。仍然先离线/小样本，不做全局 decision 改动。\n")
    (output_dir / "ACCEPT_SUPPORT_FAILURE_NEXT_STEP.md").write_text("".join(decision))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    rows = [row_summary(row) for row in read_jsonl(Path(args.input))]
    accept_rows = [row for row in rows if row["gold_decision"] == "accept"]
    reject_rows = [row for row in rows if row["gold_decision"] == "reject"]
    result = {
        "accept_aggregate": aggregate(accept_rows),
        "reject_aggregate": aggregate(reject_rows),
        "case_table": rows,
    }
    Path(args.output_json).write_text(json.dumps(result, indent=2, ensure_ascii=False))
    write_docs(result, Path(args.output_dir))
    print(json.dumps({"accept_aggregate": result["accept_aggregate"], "reject_aggregate": result["reject_aggregate"]}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
