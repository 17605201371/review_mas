#!/usr/bin/env python3
"""Compare model-transfer behavior for ReviewState runs.

This audit is intentionally model-agnostic: it compares raw agent payloads,
accepted support, fallback dependence, final-view filtering, negative evidence,
and recovery metrics.  The goal is to distinguish "the model is not stronger"
from "the pipeline has compressed the stronger model's raw advantages".
"""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence


def _load_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def _mean(values: Sequence[float]) -> float:
    return round(statistics.mean(values), 4) if values else 0.0


def _safe_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _safe_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _iter_turns(row: Mapping[str, Any]) -> Iterable[Mapping[str, Any]]:
    for turn in row.get("turn_logs") or []:
        if isinstance(turn, Mapping):
            yield turn


def _iter_evidence(row: Mapping[str, Any]) -> Iterable[Mapping[str, Any]]:
    state = row.get("review_state") or {}
    for evidence in state.get("evidence_map") or []:
        if isinstance(evidence, Mapping):
            yield evidence


def _is_final_support(evidence: Mapping[str, Any]) -> bool:
    if evidence.get("included_in_final_view") is True:
        return True
    if str(evidence.get("stance") or "") not in {"supports", "partially_supports"}:
        return False
    if str(evidence.get("strength") or "") != "strong":
        return False
    if str(evidence.get("binding_status") or "") not in {"", "unchecked", "bound_real_claim"}:
        return False
    if str(evidence.get("verified_grounding_label") or "") not in {
        "paper_grounded_exact",
        "paper_grounded_normalized",
    }:
        return False
    if str(evidence.get("semantic_grounding_label") or "") != "semantic_support_verified":
        return False
    return True


def _is_empirical(evidence: Mapping[str, Any]) -> bool:
    bucket = str(
        evidence.get("support_source_bucket")
        or evidence.get("verified_source_bucket")
        or evidence.get("source_bucket")
        or ""
    )
    locator = str(evidence.get("source_locator") or "")
    return bucket in {"result_or_experiment", "table_or_figure", "ablation"} or any(
        term in locator.lower() for term in ("table", "figure", "fig.", "experiment", "evaluation", "ablation")
    )


def _is_trace_empirical(item: Mapping[str, Any]) -> bool:
    locator = str(item.get("source_locator") or "")
    quote_id = str(item.get("quote_id") or "")
    depth = str(item.get("final_support_depth") or item.get("support_depth") or "")
    return depth == "deep" or any(
        term in " ".join([locator, quote_id]).lower()
        for term in ("table", "figure", "fig.", "experiment", "evaluation", "ablation", "result")
    )


def _claim_quote_key(evidence: Mapping[str, Any]) -> str:
    claim_id = str(evidence.get("claim_id") or "")
    quote_id = str(evidence.get("quote_id") or "")
    raw_quote = " ".join(str(evidence.get("raw_quote") or "").split())[:160]
    return f"{claim_id}::{quote_id or raw_quote}"


def _row_metrics(row: Mapping[str, Any]) -> Dict[str, Any]:
    breakdown = row.get("reward_breakdown") or {}
    turns = list(_iter_turns(row))
    evidence_items = list(_iter_evidence(row))
    final_support = [ev for ev in evidence_items if _is_final_support(ev)]
    support_trace: List[Mapping[str, Any]] = []
    for turn in turns:
        for item in turn.get("support_survival_trace") or []:
            if isinstance(item, Mapping):
                support_trace.append(item)
    trace_included = [item for item in support_trace if item.get("included_in_final_view")]

    evidence_turns = [t for t in turns if "Evidence Agent" in (t.get("selected_agents") or [])]
    quote_bank_nonzero = sum(1 for t in evidence_turns if _safe_int(t.get("evidence_quote_bank_count")) > 0)
    payload_evidence_total = sum(_safe_int(t.get("evidence_payload_evidence_count")) for t in evidence_turns)
    question_only = sum(
        1
        for t in evidence_turns
        if _safe_int(t.get("evidence_quote_bank_count")) > 0
        and _safe_int(t.get("evidence_payload_evidence_count")) == 0
    )
    first_support_fallback = sum(1 for t in turns if t.get("first_support_fallback_from_quote_bank"))
    if trace_included:
        final_support_total = len(trace_included)
        final_support_fallback = sum(
            1
            for item in trace_included
            if str(item.get("support_id") or item.get("evidence_id") or "").startswith("evidence-first-support")
        )
        final_support_empirical = sum(1 for item in trace_included if _is_trace_empirical(item))
        final_support_specific_locator = sum(1 for item in trace_included if item.get("source_locator_specific"))
        independent_final_support_groups = len({_claim_quote_key(item) for item in trace_included})
    else:
        final_support_total = len(final_support)
        final_support_fallback = sum(
            1
            for ev in final_support
            if ev.get("first_support_fallback_from_quote_bank")
            or "Fallback first-support item" in str(ev.get("binding_rationale") or "")
            or str(ev.get("evidence_id") or "").startswith("evidence-first-support")
        )
        final_support_empirical = sum(1 for ev in final_support if _is_empirical(ev))
        final_support_specific_locator = sum(1 for ev in final_support if ev.get("source_locator_specific"))
        independent_final_support_groups = len({_claim_quote_key(ev) for ev in final_support})
    final_support_direct_model = max(0, final_support_total - final_support_fallback)

    drop_reasons: Dict[str, int] = {}
    for item in support_trace:
        if item.get("included_in_final_view"):
            continue
        reason = str(item.get("final_drop_reason") or item.get("support_admission_blocker") or "unknown")
        drop_reasons[reason] = drop_reasons.get(reason, 0) + 1

    return {
        "paper_id": row.get("paper_id"),
        "reward": _safe_float(row.get("reward")),
        "evidence_support_score": _safe_float(breakdown.get("evidence_support_score")),
        "es_coverage": _safe_float(breakdown.get("es_coverage")),
        "es_depth": _safe_float(breakdown.get("es_depth")),
        "es_empirical": _safe_float(breakdown.get("es_empirical")),
        "es_independent": _safe_float(breakdown.get("es_independent")),
        "critique": _safe_float(breakdown.get("critique")),
        "stance_align": _safe_float(breakdown.get("stance_align")),
        "evidence_agent_turns": len(evidence_turns),
        "quote_bank_nonzero_turns": quote_bank_nonzero,
        "payload_evidence_total": payload_evidence_total,
        "evidence_question_only_turns": question_only,
        "first_support_fallback_turns": first_support_fallback,
        "final_support_total": final_support_total,
        "final_support_direct_model": final_support_direct_model,
        "final_support_fallback": final_support_fallback,
        "final_support_empirical": final_support_empirical,
        "final_support_specific_locator": final_support_specific_locator,
        "independent_final_support_groups": independent_final_support_groups,
        "support_trace_total": len(support_trace),
        "support_trace_dropped": sum(1 for item in support_trace if not item.get("included_in_final_view")),
        "support_drop_reasons": drop_reasons,
        "negative_evidence_candidates": sum(1 for ev in evidence_items if str(ev.get("stance") or "") in {"missing", "contradicts"}),
        "verified_negative_flaws": sum(
            1
            for flaw in (row.get("review_state") or {}).get("flaw_candidates") or []
            if isinstance(flaw, Mapping)
            and (
                flaw.get("verified_negative_evidence")
                or str(flaw.get("flaw_lifecycle_status") or "") in {"verified_potential_concern", "grounded_weakness"}
            )
        ),
        "recovery_attempted": sum(_safe_int(t.get("recovery_attempted")) for t in turns),
        "recovery_committed": sum(_safe_int(t.get("recovery_committed") or t.get("recovery_patch_committed")) for t in turns),
        "recovery_effective_repair": sum(_safe_int(t.get("recovery_effective_repair")) for t in turns),
        "hygiene_delta_or_safe_block": sum(
            1
            for t in turns
            if t.get("recovery_effective_repair")
            or t.get("recovery_safe_resolution")
            or t.get("hygiene_delta_improved")
        ),
    }


def _aggregate(label: str, rows: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    metrics = [_row_metrics(row) for row in rows]
    numeric_keys = [
        "reward",
        "evidence_support_score",
        "es_coverage",
        "es_depth",
        "es_empirical",
        "es_independent",
        "critique",
        "stance_align",
        "evidence_agent_turns",
        "quote_bank_nonzero_turns",
        "payload_evidence_total",
        "evidence_question_only_turns",
        "first_support_fallback_turns",
        "final_support_total",
        "final_support_direct_model",
        "final_support_fallback",
        "final_support_empirical",
        "final_support_specific_locator",
        "independent_final_support_groups",
        "support_trace_total",
        "support_trace_dropped",
        "negative_evidence_candidates",
        "verified_negative_flaws",
        "recovery_attempted",
        "recovery_committed",
        "recovery_effective_repair",
        "hygiene_delta_or_safe_block",
    ]
    totals = {key: sum(_safe_float(item.get(key)) for item in metrics) for key in numeric_keys}
    means = {key: _mean([_safe_float(item.get(key)) for item in metrics]) for key in numeric_keys}
    drop_reasons: Dict[str, int] = {}
    for item in metrics:
        for reason, count in (item.get("support_drop_reasons") or {}).items():
            drop_reasons[reason] = drop_reasons.get(reason, 0) + int(count)
    fallback_denominator = totals["final_support_total"] or 1
    payload_denominator = totals["payload_evidence_total"] or 1
    return {
        "label": label,
        "n": len(rows),
        "paper_ids": [row.get("paper_id") for row in rows],
        "means": means,
        "totals": totals,
        "support_drop_reasons": dict(sorted(drop_reasons.items(), key=lambda kv: (-kv[1], kv[0]))),
        "fallback_final_support_rate": round(totals["final_support_fallback"] / fallback_denominator, 4),
        "final_support_yield_from_payload": round(totals["final_support_total"] / payload_denominator, 4),
        "direct_model_final_support_rate": round(totals["final_support_direct_model"] / fallback_denominator, 4),
        "per_paper": metrics,
    }


def _fmt(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def _write_markdown(output: Path, aggregates: Sequence[Mapping[str, Any]], comparisons: Sequence[Mapping[str, Any]]) -> None:
    lines: List[str] = []
    lines.append("# Model Transfer Funnel Audit v1")
    lines.append("")
    lines.append("本审计用于区分“模型本身不强”和“框架把模型能力压平”。它不只看 final reward，而是看 raw payload → final support → recovery/flaw 的漏斗。")
    lines.append("")
    lines.append("## Aggregate Metrics")
    cols = [
        "label",
        "n",
        "reward",
        "evidence_support_score",
        "payload_evidence_total",
        "final_support_total",
        "final_support_direct_model",
        "final_support_fallback",
        "fallback_final_support_rate",
        "independent_final_support_groups",
        "support_trace_dropped",
        "evidence_question_only_turns",
        "recovery_effective_repair",
    ]
    lines.append("| " + " | ".join(cols) + " |")
    lines.append("|" + "|".join(["---"] * len(cols)) + "|")
    for agg in aggregates:
        row = []
        for col in cols:
            if col in {"label", "n", "fallback_final_support_rate"}:
                row.append(_fmt(agg.get(col)))
            elif col in {"payload_evidence_total", "final_support_total", "final_support_direct_model", "final_support_fallback", "independent_final_support_groups", "support_trace_dropped", "evidence_question_only_turns", "recovery_effective_repair"}:
                row.append(_fmt(agg["totals"].get(col)))
            else:
                row.append(_fmt(agg["means"].get(col)))
        lines.append("| " + " | ".join(row) + " |")
    lines.append("")
    lines.append("## Support Drop Reasons")
    for agg in aggregates:
        lines.append(f"### {agg['label']}")
        if not agg["support_drop_reasons"]:
            lines.append("- none")
        else:
            for reason, count in list(agg["support_drop_reasons"].items())[:12]:
                lines.append(f"- `{reason}`: {count}")
        lines.append("")
    if comparisons:
        lines.append("## Paired Comparison")
        lines.append("| paper_id | left | right | reward_delta | evidence_support_delta | final_support_delta | fallback_delta | payload_evidence_delta |")
        lines.append("|---|---|---:|---:|---:|---:|---:|---:|")
        for item in comparisons:
            lines.append(
                "| {paper_id} | {left_label} | {right_label} | {reward_delta:.4f} | {es_delta:.4f} | {final_support_delta:.0f} | {fallback_delta:.0f} | {payload_delta:.0f} |".format(**item)
            )
        lines.append("")
    lines.append("## Interpretation")
    if len(aggregates) >= 2:
        left, right = aggregates[0], aggregates[1]
        reward_delta = right["means"]["reward"] - left["means"]["reward"]
        es_delta = right["means"]["evidence_support_score"] - left["means"]["evidence_support_score"]
        fallback_delta = right["fallback_final_support_rate"] - left["fallback_final_support_rate"]
        lines.append(f"- `{right['label']}` 相对 `{left['label']}` 的平均 reward 差值为 `{reward_delta:.4f}`，evidence_support 差值为 `{es_delta:.4f}`。")
        lines.append(f"- final support fallback rate 差值为 `{fallback_delta:.4f}`。如果更强模型的 direct_model_final_support 增加，说明模型能力没有完全被规则压平。")
        lines.append("- 如果 raw payload 增加但 final support 没增加，优先检查 final-view guard / support-depth / semantic mismatch。")
        lines.append("- 如果 raw payload 没增加，优先检查 context selection、quote bank、target selection 和模型适配 prompt。")
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", action="append", nargs=2, metavar=("LABEL", "JSONL"), required=True)
    parser.add_argument("--compare", nargs=2, metavar=("LEFT_LABEL", "RIGHT_LABEL"))
    parser.add_argument("--output-md", required=True)
    parser.add_argument("--output-json", required=True)
    args = parser.parse_args()

    rows_by_label: Dict[str, List[Dict[str, Any]]] = {}
    aggregates: List[Dict[str, Any]] = []
    for label, path_str in args.run:
        rows = _load_jsonl(Path(path_str))
        rows_by_label[label] = rows
        aggregates.append(_aggregate(label, rows))

    comparisons: List[Dict[str, Any]] = []
    if args.compare:
        left_label, right_label = args.compare
        left = {row["paper_id"]: _row_metrics(row) for row in rows_by_label[left_label]}
        right = {row["paper_id"]: _row_metrics(row) for row in rows_by_label[right_label]}
        for paper_id in sorted(set(left) & set(right)):
            l_item, r_item = left[paper_id], right[paper_id]
            comparisons.append({
                "paper_id": paper_id,
                "left_label": left_label,
                "right_label": right_label,
                "reward_delta": r_item["reward"] - l_item["reward"],
                "es_delta": r_item["evidence_support_score"] - l_item["evidence_support_score"],
                "final_support_delta": r_item["final_support_total"] - l_item["final_support_total"],
                "fallback_delta": r_item["final_support_fallback"] - l_item["final_support_fallback"],
                "payload_delta": r_item["payload_evidence_total"] - l_item["payload_evidence_total"],
            })

    payload = {"aggregates": aggregates, "comparisons": comparisons}
    Path(args.output_json).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    _write_markdown(Path(args.output_md), aggregates, comparisons)


if __name__ == "__main__":
    main()
