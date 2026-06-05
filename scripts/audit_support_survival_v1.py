#!/usr/bin/env python3
"""Audit verified support survival from ReviewState evidence_map to final-view support.

This is an offline analysis script. It does not call a model and does not mutate
ReviewState. It recomputes the current decision hygiene view so support survival
uses the same code path as report rendering.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agent_system.environments.env_package.review.state import build_decision_hygiene_view


def _load_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def _counter_to_dict(counter: Counter) -> Dict[str, int]:
    return {str(k): int(v) for k, v in counter.most_common()}


def _admission_blocker_explanation(blocker: str) -> str:
    return {
        "verified_medium_support_not_final_strong": "verified medium support; final view still requires strong",
        "verified_abstract_support_not_final_strong": "verified abstract/contextual support; abstract bucket blocks final strong admission",
        "verified_contextual_support_not_final_strong": "verified contextual support; not eligible for final strong admission",
        "not_final_strong_strength": "verified support is not final strong strength",
        "duplicate_quote": "same claim and quote already counted; not independent final support",
        "overridden_by_negative_burden": "verified negative evidence linked to an active flaw suppresses this claim support",
        "claim_not_paper_extracted": "support is bound to a non-paper-extracted claim",
        "missing_verified_quote": "quote grounding is not verified against the paper quote bank",
        "semantic_mismatch": "quote is grounded but semantic support is not verified",
        "weak_support_depth": "support depth is shallow or missing",
    }.get(blocker, "unclassified final-view admission blocker")


def _row_trace(row: Dict[str, Any]) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    state = row.get("review_state") or {}
    if isinstance(state, dict) and row.get("paper_id") and not state.get("paper_id"):
        state = dict(state)
        state["paper_id"] = row.get("paper_id")
    view = build_decision_hygiene_view(state if isinstance(state, dict) else {})
    hygiene = view.get("decision_hygiene", {}) if isinstance(view, dict) else {}
    trace = hygiene.get("support_survival_trace") or []
    return hygiene, [item for item in trace if isinstance(item, dict)]


def audit(rows: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    rows = list(rows)
    global_counts = Counter()
    drop_by_reason = Counter()
    drop_by_claim_kind = Counter()
    admission_tier_counts = Counter()
    admission_blocker_counts = Counter()
    final_pairs = set()
    merged_pairs = set()
    paper_cases: List[Dict[str, Any]] = []
    reason_examples: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

    for row in rows:
        paper_id = str(row.get("paper_id") or "")
        hygiene, trace = _row_trace(row)
        local = Counter()
        local_drop = Counter()
        local_tier = Counter()
        local_blocker = Counter()
        local_final_pairs = set()
        local_merged_pairs = set()

        for item in trace:
            global_counts["merged_support_total"] += 1
            local["merged_support_total"] += 1
            tier = str(item.get("support_admission_tier") or "unknown")
            admission_tier_counts[tier] += 1
            local_tier[tier] += 1
            claim_id = str(item.get("claim_id") or "")
            quote_key = str(item.get("quote_id") or item.get("raw_quote") or item.get("evidence_id") or "")
            if claim_id or quote_key:
                pair = (paper_id, claim_id, quote_key)
                merged_pairs.add(pair)
                local_merged_pairs.add(pair)

            if item.get("semantic_grounding_label") == "semantic_support_verified":
                global_counts["semantic_verified_support_total"] += 1
                local["semantic_verified_support_total"] += 1
            if item.get("verified_grounding_label") in {"paper_grounded_exact", "paper_grounded_normalized"}:
                global_counts["verified_quote_support_total"] += 1
                local["verified_quote_support_total"] += 1
            if item.get("included_in_final_view"):
                global_counts["final_real_strong_total"] += 1
                local["final_real_strong_total"] += 1
                final_pairs.add((paper_id, claim_id, quote_key))
                local_final_pairs.add((claim_id, quote_key))
                if item.get("final_support_depth") == "deep":
                    global_counts["final_deep_support_total"] += 1
                    local["final_deep_support_total"] += 1
            else:
                reason = str(item.get("final_drop_reason") or "unknown")
                kind = str(item.get("claim_kind") or "unknown")
                blocker = str(item.get("support_admission_blocker") or reason)
                drop_by_reason[reason] += 1
                drop_by_claim_kind[kind] += 1
                admission_blocker_counts[blocker] += 1
                local_drop[reason] += 1
                local_blocker[blocker] += 1
                if len(reason_examples[reason]) < 8:
                    reason_examples[reason].append(
                        {
                            "paper_id": paper_id,
                            "evidence_id": item.get("evidence_id"),
                            "claim_id": claim_id,
                            "claim_kind": kind,
                            "quote_id": item.get("quote_id"),
                            "support_depth": item.get("support_depth"),
                            "semantic_grounding_label": item.get("semantic_grounding_label"),
                            "support_admission_tier": item.get("support_admission_tier"),
                            "support_admission_blocker": item.get("support_admission_blocker"),
                            "source_locator": item.get("source_locator"),
                        }
                    )

            for flag in (
                "quote_bank_claim_overlap_fallback_used",
                "semantic_weak_promotion_used",
                "strength_promotion_from_medium_used",
            ):
                if item.get(flag):
                    global_counts[flag + "_count"] += 1
                    local[flag + "_count"] += 1
                    if item.get("included_in_final_view"):
                        global_counts[flag + "_final_count"] += 1
                        local[flag + "_final_count"] += 1

        local["independent_merged_claim_quote_pairs"] = len(local_merged_pairs)
        local["independent_final_claim_quote_pairs"] = len(local_final_pairs)
        if trace or local_drop:
            paper_cases.append(
                {
                    "paper_id": paper_id,
                    **{k: int(v) for k, v in local.items()},
                    "drop_by_reason": _counter_to_dict(local_drop),
                    "support_admission_tier_counts": _counter_to_dict(local_tier),
                    "support_admission_blocker_counts": _counter_to_dict(local_blocker),
                    "hygiene_real_strong_support_total": int(hygiene.get("real_strong_support_total", 0) or 0),
                    "hygiene_claims_with_real_strong_support": int(hygiene.get("claims_with_real_strong_support", 0) or 0),
                }
            )

    global_counts["paper_count"] = len(rows)
    global_counts["independent_merged_claim_quote_pairs"] = len(merged_pairs)
    global_counts["independent_final_claim_quote_pairs"] = len(final_pairs)
    summary = {k: int(v) for k, v in global_counts.items()}
    merged = max(summary.get("merged_support_total", 0), 1)
    semantic = max(summary.get("semantic_verified_support_total", 0), 1)
    summary.update(
        {
            "semantic_to_final_survival_rate": round(summary.get("final_real_strong_total", 0) / semantic, 4),
            "merge_to_final_survival_rate": round(summary.get("final_real_strong_total", 0) / merged, 4),
            "drop_by_final_reason": _counter_to_dict(drop_by_reason),
            "drop_by_claim_kind": _counter_to_dict(drop_by_claim_kind),
            "support_admission_tier_counts": _counter_to_dict(admission_tier_counts),
            "support_admission_blocker_counts": _counter_to_dict(admission_blocker_counts),
            "reason_examples": {k: v for k, v in reason_examples.items()},
            "paper_cases": paper_cases,
        }
    )
    return summary


def write_markdown(result: Dict[str, Any], output: Path, input_path: Path) -> None:
    lines = [
        "# Support Survival Audit v1",
        "",
        f"- 输入结果: `{input_path}`",
        f"- papers: {result.get('paper_count', 0)}",
        "",
        "## Summary",
        f"- merged support total: {result.get('merged_support_total', 0)}",
        f"- verified quote support total: {result.get('verified_quote_support_total', 0)}",
        f"- semantic verified support total: {result.get('semantic_verified_support_total', 0)}",
        f"- final real strong total: {result.get('final_real_strong_total', 0)}",
        f"- final deep support total: {result.get('final_deep_support_total', 0)}",
        f"- independent merged claim-quote pairs: {result.get('independent_merged_claim_quote_pairs', 0)}",
        f"- independent final claim-quote pairs: {result.get('independent_final_claim_quote_pairs', 0)}",
        f"- semantic -> final survival rate: {result.get('semantic_to_final_survival_rate', 0)}",
        f"- merge -> final survival rate: {result.get('merge_to_final_survival_rate', 0)}",
        "",
        "## Promotion / Fallback Counters",
        f"- quote-bank overlap fallback used: {result.get('quote_bank_claim_overlap_fallback_used_count', 0)}",
        f"- quote-bank overlap fallback final: {result.get('quote_bank_claim_overlap_fallback_used_final_count', 0)}",
        f"- semantic weak promotion used: {result.get('semantic_weak_promotion_used_count', 0)}",
        f"- semantic weak promotion final: {result.get('semantic_weak_promotion_used_final_count', 0)}",
        f"- strength promotion from medium used: {result.get('strength_promotion_from_medium_used_count', 0)}",
        f"- strength promotion from medium final: {result.get('strength_promotion_from_medium_used_final_count', 0)}",
        "",
        "## Drop Reasons",
    ]
    for key, value in result.get("drop_by_final_reason", {}).items():
        lines.append(f"- `{key}`: {value}")
    lines.extend(["", "## Drop By Claim Kind"])
    for key, value in result.get("drop_by_claim_kind", {}).items():
        lines.append(f"- `{key}`: {value}")
    lines.extend(["", "## Support Admission Tiers"])
    for key, value in result.get("support_admission_tier_counts", {}).items():
        lines.append(f"- `{key}`: {value}")
    lines.extend(["", "## Support Admission Blockers"])
    for key, value in result.get("support_admission_blocker_counts", {}).items():
        lines.append(f"- `{key}`: {value}")
    lines.extend(["", "## Final-view Admission Diagnosis", "", "| blocker | count | interpretation |", "| --- | ---: | --- |"])
    for key, value in result.get("support_admission_blocker_counts", {}).items():
        lines.append(f"| `{key}` | {value} | {_admission_blocker_explanation(str(key))} |")
    lines.extend(["", "## Example Drops"])
    for reason, examples in result.get("reason_examples", {}).items():
        lines.append(f"### {reason}")
        for item in examples[:5]:
            lines.append(
                f"- `{item.get('paper_id')}` / `{item.get('evidence_id')}` / claim=`{item.get('claim_id')}` / "
                f"kind=`{item.get('claim_kind')}` / quote=`{item.get('quote_id')}` / depth=`{item.get('support_depth')}` / "
                f"semantic=`{item.get('semantic_grounding_label')}` / tier=`{item.get('support_admission_tier')}` / "
                f"blocker=`{item.get('support_admission_blocker')}` / locator=`{item.get('source_locator')}`"
            )
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit support survival from evidence_map to final-view support.")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--output-md", required=True)
    args = parser.parse_args()
    input_path = Path(args.input)
    result = audit(_load_jsonl(input_path))
    Path(args.output_json).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(result, Path(args.output_md), input_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
