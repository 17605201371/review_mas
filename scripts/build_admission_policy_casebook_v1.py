#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agent_system.environments.env_package.review.state import build_decision_hygiene_view


SCHEMA_VERSION = "admission_policy_casebook_v1_20260521"
TARGET_BLOCKERS = {
    "verified_medium_support_not_final_strong": "medium_nonabstract",
    "verified_abstract_support_not_final_strong": "abstract_contextual",
    "duplicate_quote": "duplicate_quote",
    "overridden_by_negative_burden": "negative_burden",
    "claim_not_paper_extracted": "claim_not_paper_extracted",
}


def _load_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def _text(value: Any, limit: int = 220) -> str:
    text = " ".join(str(value or "").split())
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 1)].rstrip() + "…"


def _claim_lookup(state: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    claims: Dict[str, Dict[str, Any]] = {}
    for claim in state.get("claims", []) or []:
        if isinstance(claim, dict):
            claim_id = str(claim.get("claim_id") or "")
            if claim_id:
                claims[claim_id] = claim
    return claims


def _quote_key(item: Dict[str, Any]) -> str:
    return str(item.get("quote_id") or item.get("raw_quote") or item.get("evidence_id") or "")


def _row_view(row: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    state = row.get("review_state") or {}
    if isinstance(state, dict) and row.get("paper_id") and not state.get("paper_id"):
        state = dict(state)
        state["paper_id"] = row.get("paper_id")
    view = build_decision_hygiene_view(state if isinstance(state, dict) else {})
    return state if isinstance(state, dict) else {}, view if isinstance(view, dict) else {}


def _case_record(
    *,
    row: Dict[str, Any],
    claim: Dict[str, Any],
    item: Dict[str, Any],
    category: str,
    claim_had_final_support: bool,
) -> Dict[str, Any]:
    return {
        "category": category,
        "paper_id": str(row.get("paper_id") or item.get("paper_id") or ""),
        "evidence_id": str(item.get("evidence_id") or ""),
        "support_id": str(item.get("support_id") or item.get("evidence_id") or ""),
        "claim_id": str(item.get("claim_id") or ""),
        "claim_kind": str(item.get("claim_kind") or ""),
        "claim_text": _text(claim.get("claim") or claim.get("text") or claim.get("claim_text") or ""),
        "claim_had_final_support": bool(claim_had_final_support),
        "quote_id": str(item.get("quote_id") or ""),
        "raw_quote": _text(item.get("raw_quote") or ""),
        "source_locator": str(item.get("source_locator") or ""),
        "declared_support_source_bucket": str(item.get("declared_support_source_bucket") or ""),
        "decision_support_source_bucket": str(item.get("decision_support_source_bucket") or ""),
        "initial_strength": str(item.get("initial_strength") or ""),
        "final_strength": str(item.get("final_strength") or ""),
        "support_depth": str(item.get("support_depth") or ""),
        "final_support_depth": str(item.get("final_support_depth") or ""),
        "support_admission_tier": str(item.get("support_admission_tier") or ""),
        "support_admission_blocker": str(item.get("support_admission_blocker") or ""),
        "final_drop_reason": str(item.get("final_drop_reason") or ""),
        "verified_grounding_label": str(item.get("verified_grounding_label") or ""),
        "verified_quote_match_type": str(item.get("verified_quote_match_type") or ""),
        "verified_claim_overlap_score": item.get("verified_claim_overlap_score", 0),
        "semantic_grounding_label": str(item.get("semantic_grounding_label") or ""),
        "semantic_alignment_score": item.get("semantic_alignment_score", 0),
        "strength_promotion_from_medium_used": bool(item.get("strength_promotion_from_medium_used")),
        "strength_promotion_reason": str(item.get("strength_promotion_reason") or ""),
    }


def build_casebook(rows: Iterable[Dict[str, Any]], *, input_path: str = "") -> Dict[str, Any]:
    rows = list(rows)
    cases: List[Dict[str, Any]] = []
    category_counts = Counter()
    blocker_counts = Counter()
    tier_counts = Counter()
    current_final_real_strong_total = 0
    current_claims_with_real_strong_support = 0
    medium_pairs = set()
    abstract_pairs = set()
    medium_new_claims = set()
    medium_or_abstract_new_claims = set()

    for row in rows:
        state, view = _row_view(row)
        hygiene = view.get("decision_hygiene", {}) if isinstance(view, dict) else {}
        current_final_real_strong_total += int(hygiene.get("real_strong_support_total") or 0)
        current_claims_with_real_strong_support += int(hygiene.get("claims_with_real_strong_support") or 0)
        claims_by_id = _claim_lookup(state)
        support_by_claim = hygiene.get("real_strong_support_by_claim") or {}
        for item in hygiene.get("support_survival_trace") or []:
            if not isinstance(item, dict) or item.get("included_in_final_view"):
                continue
            blocker = str(item.get("support_admission_blocker") or item.get("final_drop_reason") or "")
            category = TARGET_BLOCKERS.get(blocker)
            if not category:
                continue
            paper_id = str(row.get("paper_id") or item.get("paper_id") or "")
            claim_id = str(item.get("claim_id") or "")
            pair = (paper_id, claim_id, _quote_key(item))
            claim_pair = (paper_id, claim_id)
            claim_had_final_support = int(support_by_claim.get(claim_id) or 0) > 0
            if category == "medium_nonabstract":
                medium_pairs.add(pair)
                if not claim_had_final_support:
                    medium_new_claims.add(claim_pair)
                    medium_or_abstract_new_claims.add(claim_pair)
            if category == "abstract_contextual":
                abstract_pairs.add(pair)
                if not claim_had_final_support:
                    medium_or_abstract_new_claims.add(claim_pair)
            category_counts[category] += 1
            blocker_counts[blocker] += 1
            tier_counts[str(item.get("support_admission_tier") or "unknown")] += 1
            cases.append(
                _case_record(
                    row=row,
                    claim=claims_by_id.get(claim_id, {}),
                    item=item,
                    category=category,
                    claim_had_final_support=claim_had_final_support,
                )
            )

    medium_shadow_gain = len(medium_pairs)
    medium_or_abstract_shadow_gain = len(medium_pairs | abstract_pairs)
    return {
        "schema_version": SCHEMA_VERSION,
        "input_path": input_path,
        "paper_count": len(rows),
        "case_count": len(cases),
        "current_final_real_strong_total": current_final_real_strong_total,
        "current_claims_with_real_strong_support_total": current_claims_with_real_strong_support,
        "category_counts": dict(category_counts),
        "support_admission_tier_counts": dict(tier_counts),
        "support_admission_blocker_counts": dict(blocker_counts),
        "shadow_gain_estimate": {
            "medium_nonabstract_additional_support_if_admitted": medium_shadow_gain,
            "medium_nonabstract_projected_final_real_strong_total": current_final_real_strong_total + medium_shadow_gain,
            "medium_nonabstract_newly_supported_claim_count": len(medium_new_claims),
            "medium_or_abstract_additional_support_if_admitted": medium_or_abstract_shadow_gain,
            "medium_or_abstract_projected_final_real_strong_total": current_final_real_strong_total + medium_or_abstract_shadow_gain,
            "medium_or_abstract_newly_supported_claim_count": len(medium_or_abstract_new_claims),
        },
        "cases": cases,
    }


def write_markdown(result: Dict[str, Any], output: Path) -> None:
    shadow = result.get("shadow_gain_estimate", {}) or {}
    lines = [
        "# Admission Policy Casebook v1",
        "",
        f"- input: `{result.get('input_path', '')}`",
        f"- papers: {result.get('paper_count', 0)}",
        f"- cases: {result.get('case_count', 0)}",
        f"- current final real strong total: {result.get('current_final_real_strong_total', 0)}",
        "",
        "## Shadow Gain Estimate",
        f"- medium non-abstract additional support if admitted: {shadow.get('medium_nonabstract_additional_support_if_admitted', 0)}",
        f"- medium non-abstract projected final real strong total: {shadow.get('medium_nonabstract_projected_final_real_strong_total', 0)}",
        f"- medium non-abstract newly supported claims: {shadow.get('medium_nonabstract_newly_supported_claim_count', 0)}",
        f"- medium or abstract additional support if admitted: {shadow.get('medium_or_abstract_additional_support_if_admitted', 0)}",
        f"- medium or abstract projected final real strong total: {shadow.get('medium_or_abstract_projected_final_real_strong_total', 0)}",
        f"- medium or abstract newly supported claims: {shadow.get('medium_or_abstract_newly_supported_claim_count', 0)}",
        "",
        "## Category Counts",
    ]
    for key, value in (result.get("category_counts") or {}).items():
        lines.append(f"- `{key}`: {value}")
    lines.extend(["", "## Blocker Counts"])
    for key, value in (result.get("support_admission_blocker_counts") or {}).items():
        lines.append(f"- `{key}`: {value}")
    lines.extend(["", "## Cases", "", "| category | paper | evidence | claim | strength | depth | declared bucket | decision bucket | overlap | blocker | quote |", "| --- | --- | --- | --- | --- | --- | --- | --- | ---: | --- | --- |"])
    for case in result.get("cases") or []:
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{case.get('category', '')}`",
                    f"`{case.get('paper_id', '')}`",
                    f"`{case.get('evidence_id', '')}`",
                    f"`{case.get('claim_id', '')}`",
                    f"{case.get('final_strength', '')}",
                    f"{case.get('support_depth', '')}",
                    f"{case.get('declared_support_source_bucket', '')}",
                    f"{case.get('decision_support_source_bucket', '')}",
                    f"{case.get('verified_claim_overlap_score', 0)}",
                    f"`{case.get('support_admission_blocker', '')}`",
                    _text(case.get("raw_quote", ""), 120).replace("|", "\\|"),
                ]
            )
            + " |"
        )
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build an admission policy casebook from review JSONL artifacts.")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--output-md", required=True)
    args = parser.parse_args()

    input_path = Path(args.input)
    result = build_casebook(_load_jsonl(input_path), input_path=str(input_path))
    Path(args.output_json).write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(result, Path(args.output_md))
    print(json.dumps({"case_count": result["case_count"], "schema_version": SCHEMA_VERSION}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
