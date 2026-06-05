#!/usr/bin/env python3
"""Rerender final reports for an existing review-infer jsonl.

Reads a closure-run jsonl whose rows contain ``review_state`` and
``final_report``, applies the current ``render_final_review`` renderer
(post-hygiene fix), and writes a new jsonl with ``final_report`` rewritten
in-place.  The rest of each row (including ``review_state``,
``final_decision``, ``reward``, ``turn_logs``) is preserved verbatim so
downstream audits stay reproducible.

The script is **offline and read-only with respect to runtime state**.  It
does not change ``final_decision``, ``recovery`` data, or any state-mutation
field; only the human-facing ``final_report`` text is regenerated using the
new layered renderer (Grounded paper weaknesses / Potential concerns
requiring verification / Unresolved assessment limitations).

A short summary is also emitted on stdout and, optionally, written to a
companion JSON file.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agent_system.environments.env_package.review.state import (  # noqa: E402
    build_decision_hygiene_view,
    render_final_review,
)


def _bucket(report: str) -> str:
    match = re.search(r"^Final Recommendation View:\s*(.+)$", report or "", re.M)
    raw = (match.group(1).strip() if match else "").lower()
    if "accept" in raw and "like" in raw:
        return "accept_like"
    if "borderline" in raw and "positive" in raw:
        return "borderline_positive"
    if "borderline" in raw and "insufficient" in raw:
        return "borderline_insufficient"
    if "reject" in raw and "like" in raw:
        return "reject_like"
    if "not assessable" in raw or "uncertain" in raw:
        return "not_assessable_uncertain"
    return raw or "missing"


def rerender(input_path: Path, output_path: Path) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    with input_path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))

    rewritten: List[Dict[str, Any]] = []
    grounded_weakness_papers = 0
    potential_concern_papers = 0
    layered_limitation_papers = 0
    reconciled_claim_papers = 0
    bucket_counts: Counter = Counter()

    for row in rows:
        state = row.get("review_state") or {}
        manager_payload = row.get("manager_payload") or {}
        new_report = render_final_review(state, manager_payload)
        view = build_decision_hygiene_view(state)
        hygiene = view.get("decision_hygiene", {}) or {}

        if "Grounded paper weaknesses:\n" in new_report and "none passed" not in new_report.split("Grounded paper weaknesses:")[1].split("\n")[0]:
            grounded_weakness_papers += 1
        if "Potential concerns requiring verification:" in new_report:
            potential_concern_papers += 1
        if "Unresolved assessment limitations:" in new_report:
            layered_limitation_papers += 1
        if int(hygiene.get("claims_reconciled_with_strong_support_count", 0) or 0) > 0:
            reconciled_claim_papers += 1
        bucket_counts[_bucket(new_report)] += 1

        new_row = dict(row)
        new_row["final_report"] = new_report
        new_row.setdefault("final_report_renderer", "layered_v1_2026_05_10")
        rewritten.append(new_row)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as fh:
        for row in rewritten:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")

    summary = {
        "input": str(input_path),
        "output": str(output_path),
        "row_count": len(rows),
        "grounded_weakness_papers": grounded_weakness_papers,
        "potential_concern_papers": potential_concern_papers,
        "layered_limitation_papers": layered_limitation_papers,
        "claim_reconciled_papers": reconciled_claim_papers,
        "final_view_bucket_counts": dict(bucket_counts),
    }
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Rerender final_report fields with the layered hygiene renderer.",
    )
    parser.add_argument(
        "--input-jsonl",
        default="critique_semantic_full39_20260509_qwen35_combined.jsonl",
        help="Path to the input jsonl (one paper per line, must include review_state).",
    )
    parser.add_argument(
        "--output-jsonl",
        default="critique_semantic_full39_20260509_qwen35_combined_rerendered.jsonl",
        help="Where to write the rewritten jsonl.",
    )
    parser.add_argument(
        "--summary-json",
        default="",
        help="Optional path for a small summary JSON file.",
    )
    args = parser.parse_args()

    input_path = Path(args.input_jsonl)
    output_path = Path(args.output_jsonl)

    if not input_path.exists():
        raise SystemExit(f"input jsonl not found: {input_path}")

    summary = rerender(input_path, output_path)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if args.summary_json:
        Path(args.summary_json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.summary_json).write_text(
            json.dumps(summary, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


if __name__ == "__main__":
    main()
