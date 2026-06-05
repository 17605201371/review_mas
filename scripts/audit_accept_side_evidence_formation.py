from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

SUPPORT_STANCES = {"supports", "partially_supports"}
NON_ABSTRACT_BUCKETS = {"method_or_approach", "result_or_experiment", "table_or_figure", "ablation", "conclusion"}
EMPIRICAL_BUCKETS = {"result_or_experiment", "table_or_figure", "ablation"}


def read_jsonl(path: Path) -> List[Dict[str, Any]]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def review_state(row: Dict[str, Any]) -> Dict[str, Any]:
    return row.get("review_state") or {}


def final_prediction(row: Dict[str, Any]) -> str:
    return str(row.get("final_decision") or review_state(row).get("final_decision") or "").lower()


def gold_decision(row: Dict[str, Any]) -> str:
    pred = final_prediction(row)
    correct = row.get("accept_reject_correct")
    if pred in {"accept", "reject"} and correct in {0, 0.0, 1, 1.0}:
        return pred if float(correct) >= 0.5 else ("reject" if pred == "accept" else "accept")
    return "unknown"


def is_real_claim(claim_id: Any) -> bool:
    value = str(claim_id or "")
    return bool(value) and not value.startswith("claim-fallback")


def binding_status(evidence: Dict[str, Any], *, payload: bool) -> str:
    status = str(evidence.get("binding_status") or "")
    if payload and is_real_claim(evidence.get("claim_id")) and status in {"", "unchecked", "bound_real_claim"}:
        return "bound_real_claim"
    return status


def source_bucket(evidence: Dict[str, Any]) -> str:
    return str(evidence.get("support_source_bucket") or "unknown")


def is_real_support(evidence: Dict[str, Any], *, payload: bool, strength: str | None = None) -> bool:
    if evidence.get("stance") not in SUPPORT_STANCES:
        return False
    if strength is not None and evidence.get("strength") != strength:
        return False
    if not is_real_claim(evidence.get("claim_id")):
        return False
    return binding_status(evidence, payload=payload) == "bound_real_claim"


def is_nonabstract(evidence: Dict[str, Any]) -> bool:
    return source_bucket(evidence) in NON_ABSTRACT_BUCKETS


def is_empirical(evidence: Dict[str, Any]) -> bool:
    return source_bucket(evidence) in EMPIRICAL_BUCKETS


def worker_payloads(row: Dict[str, Any], agent_id: str | None = None) -> Iterable[Tuple[Dict[str, Any], Dict[str, Any]]]:
    for turn in row.get("turn_logs") or []:
        for wrapped in turn.get("worker_payloads") or []:
            if not isinstance(wrapped, dict):
                continue
            if agent_id is not None and wrapped.get("agent_id") != agent_id:
                continue
            payload = wrapped.get("payload")
            if isinstance(payload, dict):
                yield turn, payload


def payload_evidence(row: Dict[str, Any]) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    for turn, payload in worker_payloads(row, "Evidence Agent"):
        for evidence in payload.get("evidence_map", []) or []:
            if isinstance(evidence, dict):
                copied = dict(evidence)
                copied["_turn_id"] = turn.get("turn_id")
                copied["_turn_index"] = turn.get("turn_index")
                copied["_target_claim_ids"] = list(turn.get("target_claim_ids") or [])
                items.append(copied)
    return items


def evidence_turns(row: Dict[str, Any]) -> List[Dict[str, Any]]:
    turns = []
    for turn in row.get("turn_logs") or []:
        agents = [wrapped.get("agent_id") for wrapped in turn.get("worker_payloads") or [] if isinstance(wrapped, dict)]
        if "Evidence Agent" in agents or turn.get("effective_action_type") == "verify_evidence":
            turns.append(turn)
    return turns


def real_claim_ids(row: Dict[str, Any]) -> List[str]:
    ids: List[str] = []
    for claim in review_state(row).get("claims", []) or []:
        if isinstance(claim, dict) and is_real_claim(claim.get("claim_id")):
            ids.append(str(claim.get("claim_id")))
    return ids


def high_importance_claim_ids(row: Dict[str, Any]) -> List[str]:
    ids: List[str] = []
    for claim in review_state(row).get("claims", []) or []:
        if not isinstance(claim, dict):
            continue
        if is_real_claim(claim.get("claim_id")) and str(claim.get("importance") or "").lower() in {"high", "critical"}:
            ids.append(str(claim.get("claim_id")))
    return ids or real_claim_ids(row)


def claim_text_map(row: Dict[str, Any]) -> Dict[str, str]:
    result: Dict[str, str] = {}
    for claim in review_state(row).get("claims", []) or []:
        if isinstance(claim, dict) and is_real_claim(claim.get("claim_id")):
            result[str(claim.get("claim_id"))] = str(claim.get("claim") or "")
    return result


def target_coverage(row: Dict[str, Any]) -> Dict[str, int]:
    coverage: Dict[str, int] = defaultdict(int)
    for turn in evidence_turns(row):
        for claim_id in turn.get("target_claim_ids") or []:
            if is_real_claim(claim_id):
                coverage[str(claim_id)] += 1
    return dict(coverage)


def count_critique_fallbacks(row: Dict[str, Any]) -> int:
    count = 0
    for _, payload in worker_payloads(row, "Critique Agent"):
        for flaw in payload.get("flaw_candidates", []) or []:
            if not isinstance(flaw, dict):
                continue
            fid = str(flaw.get("flaw_id") or "")
            text = " ".join(str(flaw.get(key) or "") for key in ("title", "description"))
            if fid.startswith("flaw-fallback") or "Fallback critique" in text or text.lstrip().startswith("{"):
                count += 1
    return count


def count_evidence_fallbacks(row: Dict[str, Any]) -> int:
    count = 0
    for evidence in payload_evidence(row):
        if (
            str(evidence.get("source") or "") == "fallback-extraction"
            or str(evidence.get("evidence_id") or "").startswith("evidence-fallback")
            or str(evidence.get("binding_status") or "") in {"fallback_unverified", "fallback_bound"}
        ):
            count += 1
    return count


def summarize_row(row: Dict[str, Any]) -> Dict[str, Any]:
    turns = evidence_turns(row)
    payload_items = payload_evidence(row)
    final_items = [ev for ev in review_state(row).get("evidence_map", []) or [] if isinstance(ev, dict)]
    p_strong = [ev for ev in payload_items if is_real_support(ev, payload=True, strength="strong")]
    p_medium = [ev for ev in payload_items if is_real_support(ev, payload=True, strength="medium")]
    p_support_any = [ev for ev in payload_items if is_real_support(ev, payload=True, strength=None)]
    f_strong = [ev for ev in final_items if is_real_support(ev, payload=False, strength="strong")]
    target_counts = [len(turn.get("target_claim_ids") or []) for turn in turns]
    high_claims = high_importance_claim_ids(row)
    coverage = target_coverage(row)
    targeted_high = sum(1 for cid in high_claims if coverage.get(cid, 0) > 0)
    unresolved = [q for q in review_state(row).get("unresolved_questions", []) or [] if not isinstance(q, dict) or q.get("status", "open") == "open"]
    gaps = review_state(row).get("evidence_gaps", []) or []
    confirmed_major = [
        flaw
        for flaw in review_state(row).get("flaw_candidates", []) or []
        if isinstance(flaw, dict) and flaw.get("status") == "confirmed" and flaw.get("severity") in {"major", "critical"}
    ]
    tags: List[str] = []
    if not turns:
        tags.append("no_evidence_turn")
    if turns and not any(t.get("evidence_context_contains_method") or t.get("evidence_context_contains_results") or t.get("evidence_context_contains_table_or_figure") for t in turns):
        tags.append("weak_context_visibility")
    if turns and sum(count > 2 for count in target_counts) / max(len(turns), 1) >= 0.5:
        tags.append("broad_target_dominant")
    if high_claims and targeted_high / max(len(high_claims), 1) < 0.5:
        tags.append("core_claim_under_targeted")
    if len(p_medium) >= 2 and len(p_strong) == 0:
        tags.append("medium_support_not_promoted")
    if any(is_nonabstract(ev) for ev in p_medium) and len(p_strong) == 0:
        tags.append("nonabstract_support_under_strengthened")
    if count_evidence_fallbacks(row) > 0:
        tags.append("evidence_json_fallback_present")
    if count_critique_fallbacks(row) > 0:
        tags.append("critique_fallback_interference")
    if len(unresolved) >= 6:
        tags.append("high_unresolved_burden")
    if not p_support_any:
        tags.append("no_real_support_payload")
    primary = tags[0] if tags else "unclear"
    if "no_real_support_payload" in tags and "broad_target_dominant" in tags:
        primary = "broad_target_no_support"
    elif "medium_support_not_promoted" in tags or "nonabstract_support_under_strengthened" in tags:
        primary = "support_strength_calibration"
    elif "core_claim_under_targeted" in tags:
        primary = "core_claim_under_targeted"
    elif "weak_context_visibility" in tags:
        primary = "context_visibility"
    elif "critique_fallback_interference" in tags:
        primary = "critique_fallback_interference"
    elif "high_unresolved_burden" in tags:
        primary = "negative_burden_after_evidence"
    return {
        "paper_id": row.get("paper_id"),
        "gold_decision": gold_decision(row),
        "pred_decision": final_prediction(row),
        "evidence_turns": len(turns),
        "visible_method_turns": sum(bool(t.get("evidence_context_contains_method")) for t in turns),
        "visible_results_turns": sum(bool(t.get("evidence_context_contains_results")) for t in turns),
        "visible_table_turns": sum(bool(t.get("evidence_context_contains_table_or_figure")) for t in turns),
        "avg_target_count": round(sum(target_counts) / len(target_counts), 3) if target_counts else 0.0,
        "broad_target_turns": sum(count > 2 for count in target_counts),
        "targeted_high_claims": targeted_high,
        "high_claim_count": len(high_claims),
        "payload_support_any": len(p_support_any),
        "payload_real_strong": len(p_strong),
        "payload_real_medium": len(p_medium),
        "payload_nonabstract_medium": sum(is_nonabstract(ev) for ev in p_medium),
        "payload_empirical_medium": sum(is_empirical(ev) for ev in p_medium),
        "payload_nonabstract_strong": sum(is_nonabstract(ev) for ev in p_strong),
        "payload_empirical_strong": sum(is_empirical(ev) for ev in p_strong),
        "final_real_strong": len(f_strong),
        "evidence_fallback_payloads": count_evidence_fallbacks(row),
        "critique_fallback_payloads": count_critique_fallbacks(row),
        "open_unresolved": len(unresolved),
        "evidence_gaps": len(gaps),
        "confirmed_major_or_critical": len(confirmed_major),
        "failure_tags": tags,
        "primary_failure_mode": primary,
        "claim_target_coverage": coverage,
        "claim_texts": claim_text_map(row),
        "medium_support_examples": [
            {
                "claim_id": ev.get("claim_id"),
                "section": source_bucket(ev),
                "source": ev.get("source"),
                "text": str(ev.get("evidence") or "")[:240],
            }
            for ev in p_medium[:4]
        ],
    }


def aggregate(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not rows:
        return {}
    numeric_keys = [
        "evidence_turns", "visible_method_turns", "visible_results_turns", "visible_table_turns",
        "avg_target_count", "broad_target_turns", "targeted_high_claims", "high_claim_count",
        "payload_support_any", "payload_real_strong", "payload_real_medium", "payload_nonabstract_medium",
        "payload_empirical_medium", "payload_nonabstract_strong", "payload_empirical_strong", "final_real_strong",
        "evidence_fallback_payloads", "critique_fallback_payloads", "open_unresolved", "evidence_gaps",
        "confirmed_major_or_critical",
    ]
    tag_counter: Counter[str] = Counter()
    primary_counter: Counter[str] = Counter()
    for row in rows:
        tag_counter.update(row.get("failure_tags") or [])
        primary_counter.update([row.get("primary_failure_mode") or "unclear"])
    return {
        "rows": len(rows),
        **{f"avg_{key}": round(sum(float(row.get(key, 0) or 0) for row in rows) / len(rows), 4) for key in numeric_keys},
        "rows_payload_2plus_real_strong": sum(row["payload_real_strong"] >= 2 for row in rows),
        "rows_payload_2plus_real_medium": sum(row["payload_real_medium"] >= 2 for row in rows),
        "rows_with_nonabstract_medium": sum(row["payload_nonabstract_medium"] > 0 for row in rows),
        "rows_with_broad_target_dominant": sum("broad_target_dominant" in row.get("failure_tags", []) for row in rows),
        "rows_with_core_claim_under_targeted": sum("core_claim_under_targeted" in row.get("failure_tags", []) for row in rows),
        "failure_tag_distribution": dict(tag_counter),
        "primary_failure_distribution": dict(primary_counter),
    }


def write_docs(result: Dict[str, Any], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    accept = result["accept_aggregate"]
    reject = result["reject_aggregate"]
    audit = ["# Accept-Side Evidence Formation Audit v1\n\n"]
    audit.append("本审计只读 fulltest39 的 turn payload 和 final ReviewState，不改 runtime、不重跑模型。目标是定位 gold accept 为什么没有形成真实 strong support。\n\n")
    audit.append("## Accept vs Reject 对比\n\n")
    audit.append("| group | rows | avg evidence turns | avg real strong | avg real medium | rows medium>=2 | rows strong>=2 | avg nonabs medium | avg broad turns | avg targeted high claims | avg unresolved | critique fallback avg |\n")
    audit.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|\n")
    for name, data in [("gold_accept", accept), ("gold_reject", reject)]:
        audit.append(
            f"| {name} | {data.get('rows',0)} | {data.get('avg_evidence_turns',0)} | {data.get('avg_payload_real_strong',0)} | {data.get('avg_payload_real_medium',0)} | "
            f"{data.get('rows_payload_2plus_real_medium',0)} | {data.get('rows_payload_2plus_real_strong',0)} | {data.get('avg_payload_nonabstract_medium',0)} | "
            f"{data.get('avg_broad_target_turns',0)} | {data.get('avg_targeted_high_claims',0)} | {data.get('avg_open_unresolved',0)} | {data.get('avg_critique_fallback_payloads',0)} |\n"
        )
    audit.append("\n## Gold accept 失败模式分布\n\n")
    for key, value in accept.get("primary_failure_distribution", {}).items():
        audit.append(f"- `{key}`: {value}\n")
    audit.append("\n## 结论\n\n")
    audit.append("当前 gold accept 的主问题不是 final decision 阈值。若 medium 支持主要来自 abstract，则不能直接升级为 strong；应先检查 Evidence context 是否真正包含非 abstract 的 method/result/table 片段，以及 broad target 是否让模型只抽取浅层自述。\n")
    (output_dir / "ACCEPT_SIDE_EVIDENCE_FORMATION_AUDIT_V1.md").write_text("".join(audit))

    case = ["# Accept-Side Evidence Formation Case Table v1\n\n"]
    case.append("| paper_id | gold | pred | ev_turns | real_strong | real_medium | nonabs_medium | broad_turns | targeted_high/high | unresolved | critique_fb | primary_failure | tags |\n")
    case.append("|---|---|---|---:|---:|---:|---:|---:|---|---:|---:|---|---|\n")
    for row in result["case_table"]:
        if row["gold_decision"] != "accept":
            continue
        case.append(
            f"| {row['paper_id']} | {row['gold_decision']} | {row['pred_decision']} | {row['evidence_turns']} | {row['payload_real_strong']} | "
            f"{row['payload_real_medium']} | {row['payload_nonabstract_medium']} | {row['broad_target_turns']} | {row['targeted_high_claims']}/{row['high_claim_count']} | "
            f"{row['open_unresolved']} | {row['critique_fallback_payloads']} | {row['primary_failure_mode']} | {', '.join(row['failure_tags'])} |\n"
        )
    (output_dir / "ACCEPT_SIDE_EVIDENCE_FORMATION_CASE_TABLE_V1.md").write_text("".join(case))

    next_lines = ["# Accept-Side Evidence Formation Next Cut v1\n\n"]
    accept_primary = Counter(accept.get("primary_failure_distribution", {}))
    nonabstract_medium_rows = int(accept.get("rows_with_nonabstract_medium", 0) or 0)
    threshold = max(2, accept.get("rows", 0) // 3)
    if nonabstract_medium_rows >= threshold and accept_primary.get("support_strength_calibration", 0) >= threshold:
        recommendation = "Evidence Support Strength Calibration v1（先离线/小样本验证）"
        reason = "gold accept 中存在较多 non-abstract medium 支持但没有升级为 strong，说明强度校准可能过保守。"
    elif accept.get("rows_with_broad_target_dominant", 0) >= threshold:
        recommendation = "Evidence Context Selection v2 + Accept-Side Evidence Focus v1"
        reason = "gold accept 的 evidence turns 普遍 broad，且 medium 支持主要来自 abstract；下一刀应先让 Evidence Agent 看到并抽取真实 method/result/table 片段，而不是把 abstract medium 直接升级为 strong。"
    elif accept.get("rows_with_core_claim_under_targeted", 0) >= threshold:
        recommendation = "Accept-Side Core Claim Targeting v1"
        reason = "gold accept 的高重要 claim 没有被 Evidence Agent 稳定覆盖，先修 target coverage 比继续加上下文更值。"
    else:
        recommendation = "Accept-Side Evidence Context v2"
        reason = "当前正向支持不足不能完全由强度校准或 target 覆盖解释，下一步应检查 accept 样本的 method/result/table snippet 是否足够针对核心贡献。"
    next_lines.append("## 下一刀建议\n\n")
    next_lines.append(f"建议：`{recommendation}`。\n\n")
    next_lines.append(f"理由：{reason}\n\n")
    next_lines.append("## 不建议现在做\n\n")
    next_lines.append("- 不调 accept/reject 阈值。\n")
    next_lines.append("- 不把 payload-lineage support 直接接入 final decision。\n")
    next_lines.append("- 不回到 sticky/throttle/gate 控制器。\n")
    next_lines.append("- 不做 live state hygiene mutation。\n")
    (output_dir / "ACCEPT_SIDE_EVIDENCE_FORMATION_NEXT_CUT_V1.md").write_text("".join(next_lines))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    rows = [summarize_row(row) for row in read_jsonl(Path(args.input))]
    accept_rows = [row for row in rows if row["gold_decision"] == "accept"]
    reject_rows = [row for row in rows if row["gold_decision"] == "reject"]
    result = {"input": args.input, "accept_aggregate": aggregate(accept_rows), "reject_aggregate": aggregate(reject_rows), "case_table": rows}
    Path(args.output_json).write_text(json.dumps(result, indent=2, ensure_ascii=False))
    write_docs(result, Path(args.output_dir))
    print(json.dumps({"accept_aggregate": result["accept_aggregate"], "reject_aggregate": result["reject_aggregate"]}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
