#!/usr/bin/env python3
"""Case-level table for verified review issues.

This report separates direct quote-grounded paper negatives from
obligation-grounded reviewer issues.  The second lane is the paper narrative's
main signal: claim anchor + observed paper inventory + concrete missing or
mismatched item.
"""
from __future__ import annotations

import argparse
import copy
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agent_system.environments.env_package.review.state import (
    _is_grounded_paper_negative_evidence_record,
    _is_obligation_grounded_review_issue_evidence_record,
    _negative_evidence_type_for_record,
    _review_negative_dedup_signature,
    build_decision_hygiene_view,
)


def _load_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _clip(value: Any, limit: int = 180) -> str:
    text = " ".join(str(value or "").split())
    return text if len(text) <= limit else text[: limit - 3] + "..."


def _paper_id(row: Dict[str, Any], state: Dict[str, Any]) -> str:
    return str(row.get("paper_id") or state.get("paper_id") or "")


def _claim_text(state: Dict[str, Any], claim_id: str) -> str:
    for claim in state.get("claims", []) or []:
        if isinstance(claim, dict) and str(claim.get("claim_id") or "") == claim_id:
            return _clip(claim.get("claim") or claim.get("text"), 220)
    return ""


def _bundle_missing(bundle: Dict[str, Any]) -> str:
    missing = bundle.get("missing_or_mismatch")
    if not isinstance(missing, dict):
        return ""
    values = [str(item) for item in (missing.get("items") or [missing.get("entity")]) if str(item or "").strip()]
    return "; ".join(_clip(item, 120) for item in values)


def _bundle_inventory(bundle: Dict[str, Any]) -> Dict[str, str]:
    inventory = [item for item in (bundle.get("observed_inventory") or []) if isinstance(item, dict)]
    first = inventory[0] if inventory else {}
    sources = []
    for item in inventory:
        source = str(item.get("inventory_source") or item.get("support_bucket") or "").strip()
        if source and source not in sources:
            sources.append(source)
    return {
        "locator": _clip(first.get("locator") or first.get("source_locator") or first.get("source"), 120),
        "quote": _clip(first.get("quote") or first.get("raw_quote") or first.get("evidence"), 220),
        "count": str(len(inventory)),
        "sources": ", ".join(sources[:4]),
    }


def _bundle_claim_anchor(bundle: Dict[str, Any], state: Dict[str, Any], claim_id: str) -> str:
    anchor = bundle.get("claim_anchor")
    if isinstance(anchor, dict) and anchor.get("quote"):
        return _clip(anchor.get("quote"), 220)
    return _claim_text(state, claim_id)


def _evidence_case(row: Dict[str, Any], state: Dict[str, Any], evidence: Dict[str, Any]) -> Dict[str, Any]:
    claim_id = str(evidence.get("claim_id") or "")
    neg_type = _negative_evidence_type_for_record(evidence)
    bucket = "quote_grounded_review_issue"
    missing = ""
    locator = _clip(evidence.get("source_locator") or evidence.get("source"), 120)
    quote = _clip(evidence.get("raw_quote") or evidence.get("evidence"), 220)
    claim_anchor = _claim_text(state, claim_id)

    if _is_obligation_grounded_review_issue_evidence_record(evidence, state):
        bucket = "obligation_grounded_review_issue"
        bundle = evidence.get("review_issue_bundle") if isinstance(evidence.get("review_issue_bundle"), dict) else {}
        missing = _bundle_missing(bundle)
        inventory = _bundle_inventory(bundle)
        locator = inventory["locator"] or locator
        quote = inventory["quote"] or quote
        claim_anchor = _bundle_claim_anchor(bundle, state, claim_id)
        verification_basis = _clip(bundle.get("review_issue_bundle_verification_basis"), 180)
        inventory_count = inventory.get("count", "0")
        inventory_sources = inventory.get("sources", "")
        source_of_expectation = _clip(bundle.get("source_of_expectation"), 80)
        reviewer_candidate_id = _clip(
            evidence.get("reviewer_negative_candidate_id") or bundle.get("reviewer_negative_candidate_id"),
            100,
        )
    else:
        verification_basis = _clip(evidence.get("verified_grounding_label") or evidence.get("review_negative_label"), 180)
        inventory_count = "1" if quote else "0"
        inventory_sources = _clip(evidence.get("source") or evidence.get("support_bucket"), 120)
        source_of_expectation = "direct_quote"
        reviewer_candidate_id = ""

    return {
        "paper_id": _paper_id(row, state),
        "bucket": bucket,
        "issue_type": neg_type,
        "claim_id": claim_id,
        "source_of_expectation": source_of_expectation,
        "reviewer_candidate_id": reviewer_candidate_id,
        "missing_or_mismatch": missing,
        "inventory_or_quote_locator": locator,
        "inventory_or_quote": quote,
        "inventory_count": inventory_count,
        "inventory_sources": inventory_sources,
        "verification_basis": verification_basis,
        "claim_anchor": claim_anchor,
        "evidence_id": str(evidence.get("evidence_id") or ""),
    }


def build_review_issue_case_table(rows: Iterable[Dict[str, Any]]) -> tuple[List[Dict[str, Any]], Dict[str, int]]:
    cases: List[Dict[str, Any]] = []
    summary: Counter[str] = Counter()
    seen: set[tuple[str, str, str, str]] = set()
    for row in rows:
        raw_state = row.get("review_state") if isinstance(row, dict) else {}
        if not isinstance(raw_state, dict):
            continue
        state = build_decision_hygiene_view(copy.deepcopy(raw_state))
        for evidence in state.get("evidence_map", []) or []:
            if not isinstance(evidence, dict):
                continue
            if _is_obligation_grounded_review_issue_evidence_record(evidence, state):
                bucket = "obligation_grounded_review_issue"
            elif _is_grounded_paper_negative_evidence_record(evidence, state):
                bucket = "quote_grounded_review_issue"
            else:
                continue
            neg_type = _negative_evidence_type_for_record(evidence)
            claim_id = str(evidence.get("claim_id") or "")
            if bucket == "obligation_grounded_review_issue":
                bundle = evidence.get("review_issue_bundle") if isinstance(evidence.get("review_issue_bundle"), dict) else {}
                key = (
                    _paper_id(row, state),
                    bucket,
                    neg_type,
                    claim_id,
                    _bundle_missing(bundle),
                )
            else:
                key = (_paper_id(row, state), bucket, *_review_negative_dedup_signature(evidence, state))
            if key in seen:
                continue
            seen.add(key)
            case = _evidence_case(row, state, evidence)
            cases.append(case)
            summary["verified_review_issue_cases"] += 1
            summary[f"bucket::{bucket}"] += 1
            summary[f"type::{neg_type}"] += 1
            if case.get("source_of_expectation"):
                summary[f"source::{case.get('source_of_expectation')}"] += 1
    return cases, dict(summary)


def _md_escape(value: Any) -> str:
    return str(value or "").replace("|", "\\|").replace("\n", " ")


def render_markdown(input_path: Path, cases: List[Dict[str, Any]], summary: Dict[str, int]) -> str:
    lines = [
        "# Review Issue Case Table",
        "",
        f"- run: `{input_path}`",
        f"- verified review issue cases: `{summary.get('verified_review_issue_cases', 0)}`",
        f"- quote-grounded cases: `{summary.get('bucket::quote_grounded_review_issue', 0)}`",
        f"- obligation-grounded cases: `{summary.get('bucket::obligation_grounded_review_issue', 0)}`",
        f"- reviewer-candidate cases: `{summary.get('source::reviewer_candidate', 0)}`",
        f"- claim-obligation fallback cases: `{summary.get('source::claim_obligation', 0)}`",
        "",
        "| paper_id | bucket | issue_type | claim_id | source | candidate id | missing/mismatch | inventory count | inventory sources | verification basis | inventory/quote locator | inventory/quote | claim anchor |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for case in cases:
        lines.append(
            "| "
            + " | ".join(
                _md_escape(case.get(key))
                for key in (
                    "paper_id",
                    "bucket",
                    "issue_type",
                    "claim_id",
                    "source_of_expectation",
                    "reviewer_candidate_id",
                    "missing_or_mismatch",
                    "inventory_count",
                    "inventory_sources",
                    "verification_basis",
                    "inventory_or_quote_locator",
                    "inventory_or_quote",
                    "claim_anchor",
                )
            )
            + " |"
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a verified review-issue case table from a run jsonl.")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--output-md", required=True)
    args = parser.parse_args()

    input_path = Path(args.input)
    cases, summary = build_review_issue_case_table(_load_jsonl(input_path))
    Path(args.output_json).write_text(
        json.dumps({"summary": summary, "cases": cases}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    Path(args.output_md).write_text(render_markdown(input_path, cases, summary), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
