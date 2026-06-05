#!/usr/bin/env python3
"""Audit final-view negative lifecycle and hard-negative grounding."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from agent_system.environments.env_package.review.state import (
    build_decision_hygiene_view,
    infer_final_recommendation_view,
)


META_PATTERNS = re.compile(
    r"fallback|parser|could not bind|unbound|excerpt|truncat|cut off|cut-off|not fully legible|"
    r"not legible|full text|full paper|provided text|provided paper|available text|not visible|"
    r"not shown|not provided|cannot verify|unable to verify|missing input|incomplete abstract",
    re.I,
)
HARD_NEGATIVE_PATTERNS = re.compile(
    r"contradict|unsupported|insufficient|missing baseline|no baseline|lack(s|ing)? ablation|"
    r"lack(s|ing)? experiment|invalid|flaw|weakness|fails to|does not support|not demonstrate|"
    r"empirical.*insufficient|soundness|technical.*issue|method.*invalid",
    re.I,
)


def _state_from_row(row: dict[str, Any]) -> dict[str, Any]:
    state = row.get("review_state") or row.get("final_state") or row.get("state") or {}
    return state if isinstance(state, dict) else {}


def _text(value: Any) -> str:
    if isinstance(value, dict):
        return " ".join(str(v) for v in value.values() if isinstance(v, (str, int, float)))
    return str(value or "")


def _real_support_counts(state: dict[str, Any]) -> Counter[str]:
    counts: Counter[str] = Counter()
    real_claim_ids = {
        str(claim.get("claim_id") or "")
        for claim in state.get("claims", []) or []
        if claim.get("claim_id") and not str(claim.get("claim_id")).startswith("claim-fallback")
    }
    for evidence in state.get("evidence_map", []) or []:
        if not isinstance(evidence, dict):
            continue
        claim_id = str(evidence.get("claim_id") or "")
        if claim_id not in real_claim_ids:
            continue
        if str(evidence.get("binding_status") or "") not in {"", "unchecked", "bound_real_claim"}:
            continue
        if evidence.get("strength") == "strong" and evidence.get("stance") in {"supports", "partially_supports"}:
            counts[claim_id] += 1
    return counts


def classify_unresolved(item: Any, support_counts: Counter[str]) -> str:
    if not isinstance(item, dict):
        text = _text(item)
        return "context_limitation" if META_PATTERNS.search(text) else "targetless_open_question"
    text = _text(item.get("question") or item)
    related_claim_ids = [str(x) for x in item.get("related_claim_ids", []) or [] if x]
    related_evidence_ids = [str(x) for x in (item.get("related_evidence_ids") or item.get("evidence_ids") or []) if x]
    related_flaw_ids = [str(x) for x in (item.get("related_flaw_ids") or item.get("flaw_ids") or []) if x]
    if META_PATTERNS.search(text):
        return "context_limitation"
    for claim_id in related_claim_ids:
        if support_counts.get(claim_id, 0) > 0 and re.search(r"lacks grounded|missing evidence|supporting evidence", text, re.I):
            return "resolved_by_real_support"
    if HARD_NEGATIVE_PATTERNS.search(text) and (related_claim_ids or related_evidence_ids or related_flaw_ids):
        return "unverified_hard_negative"
    if related_claim_ids or related_evidence_ids or related_flaw_ids:
        return "paper_grounded_unresolved"
    return "targetless_open_question"


def classify_gap(gap: Any, support_counts: Counter[str]) -> str:
    text = _text(gap)
    if "claim-fallback" in text or META_PATTERNS.search(text):
        return "fallback_or_context_gap"
    for claim_id, count in support_counts.items():
        if count > 0 and claim_id in text:
            return "stale_gap_resolved_by_support"
    return "open_gap"


def classify_flaw(flaw: Any) -> str:
    if not isinstance(flaw, dict):
        return "ungrounded_candidate"
    text = _text(flaw)
    source = str(flaw.get("source") or "").lower()
    flaw_id = str(flaw.get("flaw_id") or "")
    status = str(flaw.get("status") or "candidate")
    severity = str(flaw.get("severity") or "")
    evidence_ids = flaw.get("evidence_ids") or []
    if flaw_id.startswith("flaw-fallback") or source in {"fallback", "fallback-extraction", "system_meta", "system-meta"} or META_PATTERNS.search(text):
        return "fallback_or_meta_flaw"
    if status in {"downgraded", "retracted"}:
        return "downgraded_or_retracted"
    if severity in {"critical", "major"} and evidence_ids:
        return "grounded_major_or_critical"
    if evidence_ids:
        return "grounded_minor_or_candidate"
    return "ungrounded_candidate"


def classify_conflict(conflict: Any, support_counts: Counter[str]) -> str:
    if not isinstance(conflict, dict):
        return "open_conflict"
    text = _text(conflict)
    conflict_type = str(conflict.get("conflict_type") or "")
    evidence_id = str(conflict.get("evidence_id") or "")
    claim_id = str(conflict.get("claim_id") or "")
    if conflict_type.startswith("fallback") or evidence_id.startswith("evidence-fallback") or META_PATTERNS.search(text):
        return "fallback_or_context_conflict"
    if claim_id and support_counts.get(claim_id, 0) > 0 and "fallback" in text.lower():
        return "stale_conflict_resolved_by_support"
    return "open_conflict"


def audit_row(row: dict[str, Any]) -> dict[str, Any]:
    state = _state_from_row(row)
    support_counts = _real_support_counts(state)
    view = infer_final_recommendation_view(state, {})
    hygiene_view = build_decision_hygiene_view(state)
    unresolved_counts = Counter(classify_unresolved(item, support_counts) for item in state.get("unresolved_questions", []) or [])
    gap_counts = Counter(classify_gap(item, support_counts) for item in state.get("evidence_gaps", []) or [])
    flaw_counts = Counter(classify_flaw(item) for item in state.get("flaw_candidates", []) or [])
    conflict_counts = Counter(classify_conflict(item, support_counts) for item in state.get("conflict_notes", []) or [])
    return {
        "paper_id": row.get("paper_id") or row.get("id"),
        "gold": str(row.get("gold_decision") or row.get("gold") or "").lower(),
        "runtime_pred": str(row.get("final_decision") or row.get("prediction") or "").lower(),
        "recommendation_view": view.get("recommendation_view"),
        "recommendation_reason": view.get("reason"),
        "real_strong": view.get("real_strong_support_total"),
        "nonabstract": view.get("non_abstract_real_strong_support_count"),
        "empirical": view.get("empirical_real_strong_support_count"),
        "raw_unresolved_count": len(state.get("unresolved_questions", []) or []),
        "raw_gap_count": len(state.get("evidence_gaps", []) or []),
        "raw_flaw_count": len(state.get("flaw_candidates", []) or []),
        "raw_conflict_count": len(state.get("conflict_notes", []) or []),
        "hygiene_open_unresolved_count": len([q for q in hygiene_view.get("unresolved_questions", []) or [] if isinstance(q, dict) and q.get("status", "open") == "open"]),
        "hygiene_gap_count": len(hygiene_view.get("evidence_gaps", []) or []),
        "hygiene_conflict_count": len(hygiene_view.get("conflict_notes", []) or []),
        "unresolved_category_counts": dict(unresolved_counts),
        "gap_category_counts": dict(gap_counts),
        "flaw_category_counts": dict(flaw_counts),
        "conflict_category_counts": dict(conflict_counts),
    }


def md_table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(x) for x in row) + " |")
    return "\n".join(lines)


def write_report(output_md: Path, summary: dict[str, Any], rows: list[dict[str, Any]]) -> None:
    top_rows = sorted(rows, key=lambda r: (r["raw_unresolved_count"] + r["raw_gap_count"] + r["raw_flaw_count"]), reverse=True)[:12]
    lines = [
        "# NEGATIVE_LIFECYCLE_HARD_NEGATIVE_AUDIT_V1",
        "",
        "## 结论",
        "",
        "这份审计说明：raw negative burden 仍然很高，但其中相当一部分是 context limitation、targetless open question、stale gap 或 fallback/meta flaw，不能直接当作 paper-grounded reject blocker。正式推荐应继续使用 final-view lifecycle，而不是 raw unresolved/flaw count。",
        "",
        "## Aggregate",
        "",
        md_table(
            ["metric", "value"],
            [
                ["rows", summary["rows"]],
                ["raw_unresolved_total", summary["raw_unresolved_total"]],
                ["raw_gap_total", summary["raw_gap_total"]],
                ["raw_flaw_total", summary["raw_flaw_total"]],
                ["raw_conflict_total", summary["raw_conflict_total"]],
                ["hygiene_open_unresolved_total", summary["hygiene_open_unresolved_total"]],
                ["hygiene_gap_total", summary["hygiene_gap_total"]],
                ["hygiene_conflict_total", summary["hygiene_conflict_total"]],
            ],
        ),
        "",
        "## Unresolved Categories",
        "",
        md_table(["category", "count"], sorted(summary["unresolved_categories"].items())),
        "",
        "## Gap Categories",
        "",
        md_table(["category", "count"], sorted(summary["gap_categories"].items())),
        "",
        "## Flaw Categories",
        "",
        md_table(["category", "count"], sorted(summary["flaw_categories"].items())),
        "",
        "## Conflict Categories",
        "",
        md_table(["category", "count"], sorted(summary["conflict_categories"].items())),
        "",
        "## High Burden Cases",
        "",
        md_table(
            [
                "paper_id",
                "gold",
                "view",
                "real",
                "empirical",
                "raw_unresolved",
                "raw_gap",
                "raw_flaw",
                "hygiene_open_unresolved",
                "hygiene_gap",
            ],
            [
                [
                    r["paper_id"],
                    r["gold"],
                    r["recommendation_view"],
                    r["real_strong"],
                    r["empirical"],
                    r["raw_unresolved_count"],
                    r["raw_gap_count"],
                    r["raw_flaw_count"],
                    r["hygiene_open_unresolved_count"],
                    r["hygiene_gap_count"],
                ]
                for r in top_rows
            ],
        ),
        "",
        "## 下一步",
        "",
        "- 不应把 raw unresolved / gap / flaw count 直接接入 reject。",
        "- 应继续在 final-view 中区分 context limitation、targetless unresolved、unverified hard-negative 与 grounded blocker。",
        "- 若要提高 accept recovery，应优先提高 grounded hard-negative / criterion assessment 质量，而不是放宽 accept threshold。",
    ]
    output_md.write_text("\n".join(lines) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output-json", required=True, type=Path)
    parser.add_argument("--output-md", required=True, type=Path)
    args = parser.parse_args()

    rows = [audit_row(json.loads(line)) for line in args.input.read_text().splitlines() if line.strip()]
    unresolved = Counter()
    gaps = Counter()
    flaws = Counter()
    conflicts = Counter()
    for row in rows:
        unresolved.update(row["unresolved_category_counts"])
        gaps.update(row["gap_category_counts"])
        flaws.update(row["flaw_category_counts"])
        conflicts.update(row["conflict_category_counts"])
    summary = {
        "input": str(args.input),
        "rows": len(rows),
        "raw_unresolved_total": sum(row["raw_unresolved_count"] for row in rows),
        "raw_gap_total": sum(row["raw_gap_count"] for row in rows),
        "raw_flaw_total": sum(row["raw_flaw_count"] for row in rows),
        "raw_conflict_total": sum(row["raw_conflict_count"] for row in rows),
        "hygiene_open_unresolved_total": sum(row["hygiene_open_unresolved_count"] for row in rows),
        "hygiene_gap_total": sum(row["hygiene_gap_count"] for row in rows),
        "hygiene_conflict_total": sum(row["hygiene_conflict_count"] for row in rows),
        "unresolved_categories": dict(unresolved),
        "gap_categories": dict(gaps),
        "flaw_categories": dict(flaws),
        "conflict_categories": dict(conflicts),
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps({"summary": summary, "case_rows": rows}, ensure_ascii=False, indent=2) + "\n")
    write_report(args.output_md, summary, rows)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
