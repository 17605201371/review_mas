#!/usr/bin/env python3
"""Evaluate the runtime final recommendation view on an existing jsonl run."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

from agent_system.environments.env_package.review.state import (
    infer_final_decision,
    infer_final_recommendation_view,
)


def _state_from_row(row: dict[str, Any]) -> dict[str, Any]:
    state = row.get("review_state") or row.get("final_state") or row.get("state") or {}
    return state if isinstance(state, dict) else {}


def evaluate(input_jsonl: Path) -> dict[str, Any]:
    rows = []
    view_counts: Counter[str] = Counter()
    binary_counts: Counter[str] = Counter()
    gold_counts: Counter[str] = Counter()
    accept_like_ids: list[str] = []
    recovered_accept_ids: list[str] = []
    false_accept_ids: list[str] = []

    for line in input_jsonl.read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        state = _state_from_row(row)
        paper_id = row.get("paper_id") or row.get("id") or row.get("paper")
        gold = str(row.get("gold_decision") or row.get("gold") or "").lower()
        view = infer_final_recommendation_view(state, {})
        binary = infer_final_decision(state, {})

        view_label = str(view.get("recommendation_view") or "reject_like")
        view_counts[view_label] += 1
        binary_counts[binary] += 1
        gold_counts[gold] += 1
        if view_label == "accept_like":
            accept_like_ids.append(str(paper_id))
            if gold == "accept":
                recovered_accept_ids.append(str(paper_id))
            elif gold == "reject":
                false_accept_ids.append(str(paper_id))

        rows.append(
            {
                "paper_id": paper_id,
                "gold": gold,
                "recommendation_view": view_label,
                "binary_decision": binary,
                "reason": view.get("reason"),
                "real_strong": view.get("real_strong_support_total"),
                "nonabstract": view.get("non_abstract_real_strong_support_count"),
                "empirical": view.get("empirical_real_strong_support_count"),
                "open_unresolved": view.get("open_unresolved_count"),
                "targetless_uncertainty": view.get("targetless_uncertainty_count"),
                "context_or_meta_uncertainty": view.get("context_or_meta_uncertainty_count"),
                "open_evidence_gap": view.get("open_evidence_gap_count"),
                "stale_evidence_gap": view.get("stale_evidence_gap_count"),
                "grounded_major": view.get("grounded_major_flaw_count"),
                "grounded_critical": view.get("grounded_critical_flaw_count"),
            }
        )

    return {
        "input": str(input_jsonl),
        "row_count": len(rows),
        "gold_counts": dict(gold_counts),
        "recommendation_view_counts": dict(view_counts),
        "binary_decision_counts": dict(binary_counts),
        "accept_like_ids": accept_like_ids,
        "recovered_accept_ids": recovered_accept_ids,
        "false_accept_ids": false_accept_ids,
        "case_rows": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    result = evaluate(args.input)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k: result[k] for k in (
        "row_count",
        "gold_counts",
        "recommendation_view_counts",
        "binary_decision_counts",
        "accept_like_ids",
        "recovered_accept_ids",
        "false_accept_ids",
    )}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
