from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple


def _read_jsonl(path: Path) -> List[Dict[str, Any]]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def _state(row: Dict[str, Any]) -> Dict[str, Any]:
    return row.get("review_state") or row.get("final_state") or row.get("state") or {}


def _is_real_claim(claim_id: Any) -> bool:
    value = str(claim_id or "")
    return bool(value) and not value.startswith("claim-fallback")


def _binding_status_for_payload(evidence: Dict[str, Any]) -> str:
    status = str(evidence.get("binding_status") or "")
    if _is_real_claim(evidence.get("claim_id")) and status in {"", "unchecked", "bound_real_claim"}:
        return "bound_real_claim"
    return status


def _is_real_strong_support(evidence: Dict[str, Any], *, payload: bool) -> bool:
    binding = _binding_status_for_payload(evidence) if payload else str(evidence.get("binding_status") or "")
    return (
        evidence.get("strength") == "strong"
        and evidence.get("stance") in {"supports", "partially_supports"}
        and _is_real_claim(evidence.get("claim_id"))
        and binding == "bound_real_claim"
    )


def _payload_evidence_items(row: Dict[str, Any]) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    for turn in row.get("turn_logs") or []:
        turn_id = turn.get("turn_id") or turn.get("turn_index")
        for wrapped in turn.get("worker_payloads") or []:
            if not isinstance(wrapped, dict):
                continue
            payload = wrapped.get("payload")
            agent_id = wrapped.get("agent_id", "")
            if not isinstance(payload, dict):
                continue
            for evidence in payload.get("evidence_map", []) or []:
                if isinstance(evidence, dict):
                    copied = dict(evidence)
                    copied["_turn_id"] = turn_id
                    copied["_agent_id"] = agent_id
                    items.append(copied)
    return items


def _section(evidence: Dict[str, Any]) -> str:
    bucket = str(evidence.get("support_source_bucket") or "").strip()
    if bucket:
        return bucket
    source = " ".join(str(evidence.get(key) or "") for key in ("source", "evidence")).lower()
    if any(token in source for token in ("result", "experiment", "evaluation", "table", "figure", "ablation", "benchmark")):
        return "result_or_experiment"
    if any(token in source for token in ("method", "approach", "model", "framework", "algorithm")):
        return "method_or_approach"
    if "abstract" in source:
        return "abstract"
    return "other_or_unspecified"


def _normalize_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip().lower()


def _support_signature(evidence: Dict[str, Any]) -> Tuple[str, str, str, str]:
    text = _normalize_text(evidence.get("evidence"))
    # Keep signatures semantic enough to remove repeated model outputs but not collapse different sections.
    return (
        str(evidence.get("claim_id") or ""),
        text[:220],
        _normalize_text(evidence.get("source"))[:120],
        _section(evidence),
    )


def _dedupe_supports(evidence_items: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    best_by_signature: Dict[Tuple[str, str, str, str], Dict[str, Any]] = {}
    for evidence in evidence_items:
        signature = _support_signature(evidence)
        current = best_by_signature.get(signature)
        if current is None:
            best_by_signature[signature] = evidence
            continue
        # Prefer non-abstract / empirical evidence if duplicate text appears with richer metadata.
        current_score = _support_quality_score(current)
        new_score = _support_quality_score(evidence)
        if new_score > current_score:
            best_by_signature[signature] = evidence
    return list(best_by_signature.values())


def _support_quality_score(evidence: Dict[str, Any]) -> int:
    section = _section(evidence)
    score = 0
    if section == "result_or_experiment":
        score += 4
    elif section == "method_or_approach":
        score += 3
    elif section == "abstract":
        score += 1
    else:
        score += 2
    if evidence.get("stance") == "supports":
        score += 1
    if evidence.get("binding_confidence"):
        try:
            score += int(float(evidence.get("binding_confidence")) * 2)
        except Exception:
            pass
    return score


def _independence_group(evidence: Dict[str, Any]) -> Tuple[str, str]:
    section = _section(evidence)
    source = _normalize_text(evidence.get("source"))
    if any(token in source for token in ("table", "figure", "ablation", "experiment", "result", "evaluation", "benchmark")):
        return (str(evidence.get("claim_id") or ""), "empirical:" + source[:80])
    if any(token in source for token in ("method", "approach", "model", "framework", "algorithm")):
        return (str(evidence.get("claim_id") or ""), "method:" + source[:80])
    return (str(evidence.get("claim_id") or ""), section + ":" + source[:80])


def _confirmed_blockers(state: Dict[str, Any]) -> Dict[str, int]:
    counts = Counter()
    for flaw in state.get("flaw_candidates", []) or []:
        if not isinstance(flaw, dict):
            continue
        status = str(flaw.get("status") or "")
        severity = str(flaw.get("severity") or "")
        evidence_ids = flaw.get("evidence_ids") or []
        if status == "confirmed" and evidence_ids:
            if severity == "critical":
                counts["confirmed_critical"] += 1
            if severity in {"critical", "major"}:
                counts["confirmed_major_or_critical"] += 1
        elif status == "candidate" and severity in {"critical", "major"}:
            counts["candidate_major_or_critical"] += 1
    unresolved_open = 0
    for item in state.get("unresolved_questions", []) or []:
        if isinstance(item, dict):
            unresolved_open += int(item.get("status", "open") == "open")
        else:
            unresolved_open += 1
    counts["open_unresolved"] = unresolved_open
    counts["evidence_gaps"] = len(state.get("evidence_gaps", []) or [])
    return dict(counts)


def _gold_from_row(row: Dict[str, Any]) -> str:
    final_decision = str(row.get("final_decision") or _state(row).get("final_decision") or "").lower()
    correct = row.get("accept_reject_correct")
    if final_decision in {"accept", "reject"} and correct in {0, 0.0, 1, 1.0}:
        if float(correct) >= 0.5:
            return final_decision
        return "reject" if final_decision == "accept" else "accept"
    return "unknown"


def _metrics(case_rows: List[Dict[str, Any]], pred_key: str, *, borderline_as: str = "reject") -> Dict[str, Any]:
    tp = tn = fp = fn = 0
    predicted_accept_ids: List[str] = []
    false_accept_ids: List[str] = []
    recovered_accept_ids: List[str] = []
    false_reject_ids: List[str] = []
    borderline_ids: List[str] = []
    for row in case_rows:
        gold = row["gold_decision"]
        if gold not in {"accept", "reject"}:
            continue
        pred = row[pred_key]
        if pred == "borderline":
            borderline_ids.append(row["paper_id"])
            pred = borderline_as
        if pred == "accept":
            predicted_accept_ids.append(row["paper_id"])
        if pred == "accept" and gold == "accept":
            tp += 1
            recovered_accept_ids.append(row["paper_id"])
        elif pred == "accept" and gold == "reject":
            fp += 1
            false_accept_ids.append(row["paper_id"])
        elif pred == "reject" and gold == "reject":
            tn += 1
        elif pred == "reject" and gold == "accept":
            fn += 1
            false_reject_ids.append(row["paper_id"])
    total = tp + tn + fp + fn
    accuracy = (tp + tn) / total if total else 0.0
    accept_recall = tp / (tp + fn) if (tp + fn) else 0.0
    reject_recall = tn / (tn + fp) if (tn + fp) else 0.0
    accept_precision = tp / (tp + fp) if (tp + fp) else 0.0
    reject_precision = tn / (tn + fn) if (tn + fn) else 0.0
    accept_f1 = 2 * accept_precision * accept_recall / (accept_precision + accept_recall) if (accept_precision + accept_recall) else 0.0
    reject_f1 = 2 * reject_precision * reject_recall / (reject_precision + reject_recall) if (reject_precision + reject_recall) else 0.0
    return {
        "accuracy": round(accuracy, 4),
        "macro_f1": round((accept_f1 + reject_f1) / 2, 4),
        "accept_recall": round(accept_recall, 4),
        "reject_recall": round(reject_recall, 4),
        "predicted_accept_count": len(predicted_accept_ids),
        "borderline_count": len(borderline_ids),
        "false_accept_ids": false_accept_ids,
        "recovered_accept_ids": recovered_accept_ids,
        "false_reject_ids": false_reject_ids,
        "borderline_ids": borderline_ids,
    }


def _case_from_row(row: Dict[str, Any]) -> Dict[str, Any]:
    state = _state(row)
    payload_supports = _dedupe_supports(ev for ev in _payload_evidence_items(row) if _is_real_strong_support(ev, payload=True))
    final_supports = [ev for ev in state.get("evidence_map", []) or [] if isinstance(ev, dict) and _is_real_strong_support(ev, payload=False)]
    lineage_nonabstract = [ev for ev in payload_supports if _section(ev) != "abstract"]
    lineage_empirical = [ev for ev in payload_supports if _section(ev) == "result_or_experiment"]
    lineage_method = [ev for ev in payload_supports if _section(ev) == "method_or_approach"]
    groups = {_independence_group(ev) for ev in payload_supports}
    nonabstract_groups = {_independence_group(ev) for ev in lineage_nonabstract}
    blockers = _confirmed_blockers(state)
    paper_id = row.get("paper_id") or state.get("paper_id") or ""
    current_pred = str(row.get("final_decision") or state.get("final_decision") or "reject").lower()

    no_confirmed_critical = blockers.get("confirmed_critical", 0) == 0
    no_confirmed_major = blockers.get("confirmed_major_or_critical", 0) == 0
    lineage_2plus = len(payload_supports) >= 2
    nonabstract_2plus = len(lineage_nonabstract) >= 2
    independent_2plus = len(groups) >= 2
    nonabstract_independent_2plus = len(nonabstract_groups) >= 2
    method_plus_empirical = bool(lineage_method) and bool(lineage_empirical)

    sim_lineage_support = "accept" if lineage_2plus and no_confirmed_critical else "reject"
    sim_nonabstract_independent = "accept" if nonabstract_2plus and nonabstract_independent_2plus and no_confirmed_critical else "reject"
    sim_conservative = "accept" if (nonabstract_independent_2plus or method_plus_empirical) and no_confirmed_major and blockers.get("open_unresolved", 0) <= 4 else "reject"
    if no_confirmed_major and (len(lineage_nonabstract) >= 1 or len(payload_supports) >= 2) and blockers.get("open_unresolved", 0) <= 6:
        sim_borderline = "borderline"
    else:
        sim_borderline = sim_conservative

    return {
        "paper_id": paper_id,
        "gold_decision": _gold_from_row(row),
        "current_pred": current_pred,
        "lineage_real_strong": len(payload_supports),
        "lineage_nonabstract": len(lineage_nonabstract),
        "lineage_empirical": len(lineage_empirical),
        "lineage_method": len(lineage_method),
        "lineage_independent_groups": len(groups),
        "lineage_nonabstract_independent_groups": len(nonabstract_groups),
        "final_real_strong": len(final_supports),
        **blockers,
        "sim_lineage_support": sim_lineage_support,
        "sim_nonabstract_independent": sim_nonabstract_independent,
        "sim_conservative": sim_conservative,
        "sim_borderline": sim_borderline,
    }


def run_simulation(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    case_rows = [_case_from_row(row) for row in rows]
    return {
        "aggregate": {
            "rows": len(case_rows),
            "lineage_real_strong_total": sum(r["lineage_real_strong"] for r in case_rows),
            "lineage_nonabstract_total": sum(r["lineage_nonabstract"] for r in case_rows),
            "lineage_empirical_total": sum(r["lineage_empirical"] for r in case_rows),
            "lineage_method_total": sum(r["lineage_method"] for r in case_rows),
            "rows_with_2plus_lineage_real_strong": sum(r["lineage_real_strong"] >= 2 for r in case_rows),
            "rows_with_2plus_nonabstract_independent": sum(r["lineage_nonabstract_independent_groups"] >= 2 for r in case_rows),
            "rows_with_method_plus_empirical": sum(r["lineage_method"] >= 1 and r["lineage_empirical"] >= 1 for r in case_rows),
            "final_real_strong_total": sum(r["final_real_strong"] for r in case_rows),
        },
        "metrics": {
            "current_pred": _metrics(case_rows, "current_pred"),
            "sim_lineage_support": _metrics(case_rows, "sim_lineage_support"),
            "sim_nonabstract_independent": _metrics(case_rows, "sim_nonabstract_independent"),
            "sim_conservative": _metrics(case_rows, "sim_conservative"),
            "sim_borderline_strict": _metrics(case_rows, "sim_borderline", borderline_as="reject"),
            "sim_borderline_lenient": _metrics(case_rows, "sim_borderline", borderline_as="accept"),
        },
        "case_table": case_rows,
    }


def write_docs(result: Dict[str, Any], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    aggregate = result["aggregate"]
    metrics = result["metrics"]
    cases = result["case_table"]

    (output_dir / "EVIDENCE_LINEAGE_SUPPORT_VIEW_V1_SCHEMA.md").write_text(
        "# Evidence Lineage Support View v1 Schema\n\n"
        "本层是离线 final-view，不改 live ReviewState、不重跑模型。它从 `turn_logs[*].worker_payloads[*].payload.evidence_map` 收集 Evidence Agent 曾经产生过的 evidence，过滤真实 claim 上的 strong support，并按 `(claim_id, evidence text, source, section)` 去重。\n\n"
        "核心字段：`lineage_real_strong`、`lineage_nonabstract`、`lineage_empirical`、`lineage_method`、`lineage_independent_groups`、`lineage_nonabstract_independent_groups`。\n\n"
        "该 view 的目的不是直接改 accept/reject，而是衡量 final state 压缩前已经出现过多少可用正向证据。\n"
    )

    lines = ["# Evidence Lineage Support View v1 Results\n\n"]
    lines.append("## Aggregate\n\n")
    for key, value in aggregate.items():
        lines.append(f"- `{key}`: {value}\n")
    lines.append("\n## Decision Simulations\n\n")
    lines.append("| simulation | accuracy | macro_f1 | accept_recall | reject_recall | predicted_accept | borderline | false_accept_ids | recovered_accept_ids |\n")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---|---|\n")
    for name, data in metrics.items():
        lines.append(
            f"| {name} | {data['accuracy']} | {data['macro_f1']} | {data['accept_recall']} | {data['reject_recall']} | "
            f"{data['predicted_accept_count']} | {data['borderline_count']} | {','.join(data['false_accept_ids'])} | {','.join(data['recovered_accept_ids'])} |\n"
        )
    (output_dir / "EVIDENCE_LINEAGE_SUPPORT_VIEW_V1_RESULTS.md").write_text("".join(lines))

    case_lines = ["# Evidence Lineage Support View v1 Case Table\n\n"]
    case_lines.append("| paper_id | gold | current | lineage_real | nonabstract | empirical | method | indep_groups | final_real | confirmed_major_or_critical | unresolved | sim_conservative | sim_borderline |\n")
    case_lines.append("|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|\n")
    for row in cases:
        case_lines.append(
            f"| {row['paper_id']} | {row['gold_decision']} | {row['current_pred']} | {row['lineage_real_strong']} | {row['lineage_nonabstract']} | "
            f"{row['lineage_empirical']} | {row['lineage_method']} | {row['lineage_independent_groups']} | {row['final_real_strong']} | "
            f"{row.get('confirmed_major_or_critical', 0)} | {row.get('open_unresolved', 0)} | {row['sim_conservative']} | {row['sim_borderline']} |\n"
        )
    (output_dir / "EVIDENCE_LINEAGE_SUPPORT_VIEW_V1_CASE_TABLE.md").write_text("".join(case_lines))

    decision = ["# Evidence Lineage Support View v1 Decision\n\n"]
    decision.append("## 结论\n\n")
    decision.append("保留为离线 final-view / audit 层，不进入 live state merge。payload lineage 证明 Evidence Agent 已经形成过比 final ReviewState 更多的 real strong support；但直接用 lineage support 作为 accept 规则仍会产生 false accept 风险。\n\n")
    decision.append("## 下一步\n\n")
    decision.append("下一步应把 lineage support view 与 criterion grounding / final-view hygiene 结合，形成报告与诊断层；暂时不要把它接入 runtime accept/reject。更具体地说，应做 `Final-View Evidence Lineage Report v1`，展示哪些正向证据被 final state 压缩掉，并辅助论文分析 support formation loss。\n")
    (output_dir / "EVIDENCE_LINEAGE_SUPPORT_VIEW_V1_DECISION.md").write_text("".join(decision))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    result = run_simulation(_read_jsonl(Path(args.input)))
    Path(args.output_json).write_text(json.dumps(result, indent=2, ensure_ascii=False))
    write_docs(result, Path(args.output_dir))
    print(json.dumps({"aggregate": result["aggregate"], "metrics": result["metrics"]}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
