#!/usr/bin/env python3
"""Classify remaining final-view evidence gaps after hygiene cleanup."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from agent_system.environments.env_package.review.state import build_decision_hygiene_view


CLAIM_ID_RE = re.compile(r"\b(claim-[A-Za-z0-9_.:-]+)\b")


def _state_from_row(row: dict[str, Any]) -> dict[str, Any]:
    state = row.get("review_state") or row.get("final_state") or row.get("state") or {}
    return state if isinstance(state, dict) else {}


def _claim_map(state: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(claim.get("claim_id") or ""): claim
        for claim in state.get("claims", []) or []
        if isinstance(claim, dict) and claim.get("claim_id")
    }


def _evidence_for_claim(state: dict[str, Any], claim_id: str) -> list[dict[str, Any]]:
    return [
        ev for ev in state.get("evidence_map", []) or []
        if isinstance(ev, dict) and str(ev.get("claim_id") or "") == claim_id
    ]


def _real_strong(ev: dict[str, Any]) -> bool:
    return (
        ev.get("strength") == "strong"
        and ev.get("stance") in {"supports", "partially_supports"}
        and str(ev.get("binding_status") or "") in {"", "unchecked", "bound_real_claim"}
        and str(ev.get("source") or "") != "fallback-extraction"
    )


def classify_gap(gap: str, state: dict[str, Any]) -> dict[str, Any]:
    claim_ids = CLAIM_ID_RE.findall(gap or "")
    claims = _claim_map(state)
    if not claim_ids:
        return {"category": "unparsed_gap", "claim_id": "", "claim_status": "", "claim_importance": ""}
    claim_id = claim_ids[0]
    claim = claims.get(claim_id, {})
    evidence = _evidence_for_claim(state, claim_id)
    strong = [ev for ev in evidence if _real_strong(ev)]
    weak_or_medium = [
        ev for ev in evidence
        if ev.get("stance") in {"supports", "partially_supports"} and not _real_strong(ev)
    ]
    supporting_ids = claim.get("supporting_evidence_ids") or []
    status = str(claim.get("status") or "")
    importance = str(claim.get("importance") or "")
    if strong:
        category = "stale_gap_should_have_been_removed"
    elif supporting_ids and not evidence:
        category = "claim_support_ids_missing_from_evidence_map"
    elif weak_or_medium:
        category = "claim_has_only_weak_or_unusable_support"
    elif importance in {"low", "minor"}:
        category = "low_importance_claim_without_support"
    elif status in {"supported", "partially_supported"} and not strong:
        category = "claim_status_overstates_support"
    else:
        category = "claim_has_no_support"
    return {
        "category": category,
        "claim_id": claim_id,
        "claim_status": status,
        "claim_importance": importance,
        "evidence_count": len(evidence),
        "strong_count": len(strong),
        "weak_or_medium_support_count": len(weak_or_medium),
        "supporting_evidence_id_count": len(supporting_ids),
    }


def audit_row(row: dict[str, Any]) -> dict[str, Any]:
    state = _state_from_row(row)
    view = build_decision_hygiene_view(state)
    gaps = [str(gap) for gap in view.get("evidence_gaps", []) or []]
    details = []
    counts: Counter[str] = Counter()
    for gap in gaps:
        detail = classify_gap(gap, state)
        detail["gap"] = gap
        details.append(detail)
        counts[detail["category"]] += 1
    return {
        "paper_id": row.get("paper_id") or row.get("id"),
        "gold": str(row.get("gold_decision") or row.get("gold") or "").lower(),
        "open_gap_count": len(gaps),
        "gap_category_counts": dict(counts),
        "gap_details": details,
    }


def md_table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(x) for x in row) + " |")
    return "\n".join(lines)


def write_report(path: Path, summary: dict[str, Any], rows: list[dict[str, Any]]) -> None:
    high = sorted(rows, key=lambda row: row["open_gap_count"], reverse=True)[:15]
    lines = [
        "# OPEN_GAP_RESOLUTION_AUDIT_V1",
        "",
        "## 结论",
        "",
        "这份审计只看 final-view hygiene 后仍保留的 open evidence gaps。目标是判断剩余 gap 是真正缺 evidence，还是 evidence/claim 关联或 claim status 的问题。",
        "",
        "## Aggregate",
        "",
        md_table(
            ["metric", "value"],
            [
                ["rows", summary["rows"]],
                ["open_gap_total", summary["open_gap_total"]],
            ],
        ),
        "",
        "## Gap Categories",
        "",
        md_table(["category", "count"], sorted(summary["gap_categories"].items())),
        "",
        "## High-gap Cases",
        "",
        md_table(
            ["paper_id", "gold", "open_gap_count", "gap_categories"],
            [[row["paper_id"], row["gold"], row["open_gap_count"], row["gap_category_counts"]] for row in high],
        ),
        "",
        "## Decision",
        "",
        "- `claim_has_no_support` 表示 Evidence Agent 确实没有为该 claim 形成 support，优先回到 evidence/context 或 target selection。",
        "- `claim_has_only_weak_or_unusable_support` 表示 support 有但质量不足，不应直接 accept。",
        "- `claim_status_overstates_support` 或 `claim_support_ids_missing_from_evidence_map` 表示 state consistency / merge 还有修复空间。",
        "- 这轮不建议把 open gap 直接作为 reject blocker；它更适合作为 `not_assessable` 或 `borderline_insufficient` 的解释字段。",
    ]
    path.write_text("\n".join(lines) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output-json", required=True, type=Path)
    parser.add_argument("--output-md", required=True, type=Path)
    args = parser.parse_args()

    rows = [audit_row(json.loads(line)) for line in args.input.read_text().splitlines() if line.strip()]
    categories: Counter[str] = Counter()
    for row in rows:
        categories.update(row["gap_category_counts"])
    summary = {
        "input": str(args.input),
        "rows": len(rows),
        "open_gap_total": sum(row["open_gap_count"] for row in rows),
        "gap_categories": dict(categories),
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps({"summary": summary, "case_rows": rows}, ensure_ascii=False, indent=2) + "\n")
    write_report(args.output_md, summary, rows)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
