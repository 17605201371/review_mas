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
    _missing_ablation_target_quality,
    _negative_evidence_type_for_record,
    _review_negative_dedup_signature,
    _review_issue_cluster_signature_for_record,
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


def _state_without_cached_hygiene(state: Dict[str, Any]) -> Dict[str, Any]:
    clean = copy.deepcopy(state or {})
    clean.pop("decision_hygiene", None)
    state_audit = clean.get("state_audit")
    if isinstance(state_audit, dict):
        state_audit.pop("decision_hygiene", None)
    return clean


def _state_for_case_table(state: Dict[str, Any]) -> Dict[str, Any]:
    return build_decision_hygiene_view(_state_without_cached_hygiene(state))


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
        "anchor_type": _clip(bundle.get("inventory_anchor_type") or first.get("inventory_type") or first.get("inventory_source"), 120),
    }


def _bundle_claim_anchor(bundle: Dict[str, Any], state: Dict[str, Any], claim_id: str) -> str:
    anchor = bundle.get("claim_anchor")
    if isinstance(anchor, dict) and anchor.get("quote"):
        return _clip(anchor.get("quote"), 220)
    return _claim_text(state, claim_id)


def _slug(value: str) -> str:
    text = str(value or "").strip().lower()
    text = "".join(ch if ch.isalnum() else "-" for ch in text)
    text = "-".join(part for part in text.split("-") if part)
    return text[:120] or "unspecified"


def _case_cluster_fields(paper_id: str, bucket: str, evidence: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, str]:
    if bucket == "obligation_grounded_review_issue":
        issue_type, target = _review_issue_cluster_signature_for_record(evidence)
    else:
        label, claim_id, issue_type, anchor = _review_negative_dedup_signature(evidence, state)
        target = anchor.replace("quote:", "", 1)[:80] or claim_id or label or "direct_quote"
    key = f"{paper_id}|{bucket}|{issue_type}|{target}"
    return {
        "issue_cluster_key": key,
        "issue_cluster_id": f"review-issue-cluster-{_slug(key)}",
        "issue_cluster_target": target,
    }


def _reviewer_candidate_kind(candidate_id: str, source_of_expectation: str, discovery_origin: str = "") -> str:
    if str(discovery_origin or "").startswith("critique_payload"):
        return "critique_payload_candidate"
    if str(candidate_id or "").startswith("reviewer-seed"):
        return "deterministic_reviewer_seed"
    if str(candidate_id or "").startswith("review-issue-candidate"):
        return "critique_payload_candidate"
    if candidate_id:
        return "other_reviewer_candidate"
    if source_of_expectation == "claim_obligation":
        return "claim_obligation_fallback"
    if source_of_expectation == "direct_quote":
        return "direct_quote"
    return source_of_expectation or "unknown"


def _cluster_origin_kind(cluster_cases: List[Dict[str, Any]]) -> str:
    if any(case.get("critique_selected_menu_verified") for case in cluster_cases):
        return "critique_payload_candidate"
    kinds = {str(case.get("reviewer_candidate_kind") or "") for case in cluster_cases}
    sources = {str(case.get("source_of_expectation") or "") for case in cluster_cases}
    if "direct_quote" in kinds or "direct_quote" in sources:
        return "direct_quote"
    if "critique_payload_candidate" in kinds:
        return "critique_payload_candidate"
    if "claim_obligation" in sources or "claim_obligation_fallback" in kinds:
        return "claim_obligation_fallback"
    if "deterministic_reviewer_seed" in kinds:
        return "deterministic_reviewer_seed"
    if any(kind and kind != "unknown" for kind in kinds):
        return "other_reviewer_candidate"
    return "unknown"


def _evidence_case(row: Dict[str, Any], state: Dict[str, Any], evidence: Dict[str, Any]) -> Dict[str, Any]:
    claim_id = str(evidence.get("claim_id") or "")
    paper_id = _paper_id(row, state)
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
        inventory_anchor_type = inventory.get("anchor_type", "")
        source_of_expectation = _clip(bundle.get("source_of_expectation"), 80)
        review_issue_slot = _clip(bundle.get("review_issue_slot"), 80)
        entity_source = _clip(bundle.get("entity_source"), 80)
        discovery_origin = _clip(bundle.get("discovery_origin"), 100)
        rejection_reason = _clip(bundle.get("review_issue_bundle_rejection_reason"), 120)
        ablation_quality_info = _missing_ablation_target_quality(bundle) if neg_type == "missing_ablation" else {}
        ablation_target_quality = _clip(bundle.get("ablation_target_quality") or ablation_quality_info.get("quality"), 40)
        ablation_target_quality_reason = _clip(
            bundle.get("ablation_target_quality_reason") or ablation_quality_info.get("reason"),
            100,
        )
        reviewer_candidate_id = _clip(
            evidence.get("reviewer_negative_candidate_id") or bundle.get("reviewer_negative_candidate_id"),
            100,
        )
        candidate_menu_id = _clip(evidence.get("candidate_menu_id") or bundle.get("candidate_menu_id"), 120)
    else:
        verification_basis = _clip(evidence.get("verified_grounding_label") or evidence.get("review_negative_label"), 180)
        inventory_count = "1" if quote else "0"
        inventory_sources = _clip(evidence.get("source") or evidence.get("support_bucket"), 120)
        inventory_anchor_type = inventory_sources
        source_of_expectation = "direct_quote"
        review_issue_slot = "direct_quote"
        entity_source = ""
        discovery_origin = "direct_quote"
        rejection_reason = ""
        ablation_target_quality = ""
        ablation_target_quality_reason = ""
        reviewer_candidate_id = ""
        candidate_menu_id = ""

    cluster_fields = _case_cluster_fields(paper_id, bucket, evidence, state)
    reviewer_candidate_kind = _reviewer_candidate_kind(reviewer_candidate_id, source_of_expectation, discovery_origin)
    return {
        "paper_id": paper_id,
        "bucket": bucket,
        "issue_type": neg_type,
        "claim_id": claim_id,
        "source_of_expectation": source_of_expectation,
        "review_issue_slot": review_issue_slot,
        "entity_source": entity_source,
        "inventory_anchor_type": inventory_anchor_type,
        "discovery_origin": discovery_origin,
        "rejection_reason": rejection_reason,
        "reviewer_candidate_kind": reviewer_candidate_kind,
        "reviewer_candidate_id": reviewer_candidate_id,
        "candidate_menu_id": candidate_menu_id,
        "missing_or_mismatch": missing,
        "inventory_or_quote_locator": locator,
        "inventory_or_quote": quote,
        "inventory_count": inventory_count,
        "inventory_sources": inventory_sources,
        "ablation_target_quality": ablation_target_quality,
        "ablation_target_quality_reason": ablation_target_quality_reason,
        "verification_basis": verification_basis,
        "claim_anchor": claim_anchor,
        "evidence_id": str(evidence.get("evidence_id") or ""),
        **cluster_fields,
    }


def build_review_issue_case_table(rows: Iterable[Dict[str, Any]]) -> tuple[List[Dict[str, Any]], Dict[str, int]]:
    cases: List[Dict[str, Any]] = []
    summary: Counter[str] = Counter()
    seen: set[tuple[str, str, str, str]] = set()
    for row in rows:
        raw_state = row.get("review_state") if isinstance(row, dict) else {}
        if not isinstance(raw_state, dict):
            continue
        state = _state_for_case_table(raw_state)
        state_audit = state.get("state_audit") if isinstance(state, dict) else {}
        hygiene = state.get("decision_hygiene") if isinstance(state.get("decision_hygiene"), dict) else {}
        if not hygiene and isinstance(state_audit, dict):
            hygiene = state_audit.get("decision_hygiene") if isinstance(state_audit.get("decision_hygiene"), dict) else {}
        paper_id = _paper_id(row, state)
        critique_selected_cluster_details: Dict[str, Dict[str, Any]] = {}
        for item in (hygiene.get("critique_selected_verified_clusters") or []) if isinstance(hygiene, dict) else []:
            if not isinstance(item, dict):
                continue
            issue_type = str(item.get("issue_type") or "").strip()
            target = str(item.get("issue_cluster_target") or "").strip()
            if not issue_type or not target:
                cluster_key = str(item.get("issue_cluster_key") or "")
                if "|" in cluster_key:
                    issue_type, target = cluster_key.split("|", 1)
            if issue_type and target:
                case_cluster_key = f"{paper_id}|obligation_grounded_review_issue|{issue_type}|{target}"
                critique_selected_cluster_details[case_cluster_key] = item
        use_cached_issue_filter = isinstance(hygiene, dict) and "review_issue_bundle_items" in hygiene
        cached_issue_evidence_ids = {
            str(item.get("evidence_id") or "").strip()
            for item in (hygiene.get("review_issue_bundle_items") or [])
            if isinstance(item, dict) and str(item.get("evidence_id") or "").strip()
        }
        for evidence in state.get("evidence_map", []) or []:
            if not isinstance(evidence, dict):
                continue
            evidence_id = str(evidence.get("evidence_id") or "").strip()
            current_obligation_issue = _is_obligation_grounded_review_issue_evidence_record(evidence, state)
            current_direct_quote = _is_grounded_paper_negative_evidence_record(evidence, state)
            if current_obligation_issue and (not use_cached_issue_filter or evidence_id in cached_issue_evidence_ids):
                bucket = "obligation_grounded_review_issue"
            elif current_direct_quote:
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
            selected_detail = critique_selected_cluster_details.get(str(case.get("issue_cluster_key") or ""))
            if selected_detail:
                case["critique_selected_menu_verified"] = True
                case["critique_selected_candidate_menu_ids"] = "; ".join(
                    str(menu_id)
                    for menu_id in (selected_detail.get("candidate_menu_ids") or [])
                    if str(menu_id)
                )
                case["critique_selected_candidate_ids"] = "; ".join(
                    str(candidate_id)
                    for candidate_id in (selected_detail.get("candidate_ids") or [])
                    if str(candidate_id)
                )
                case["critique_selected_attribution_mode"] = str(selected_detail.get("attribution_mode") or "")
            else:
                case["critique_selected_menu_verified"] = False
                case["critique_selected_candidate_menu_ids"] = ""
                case["critique_selected_candidate_ids"] = ""
                case["critique_selected_attribution_mode"] = ""
            cases.append(case)
            summary["verified_review_issue_cases"] += 1
            summary[f"bucket::{bucket}"] += 1
            summary[f"type::{neg_type}"] += 1
            if case.get("source_of_expectation"):
                summary[f"source::{case.get('source_of_expectation')}"] += 1
            if case.get("reviewer_candidate_kind"):
                summary[f"candidate_kind::{case.get('reviewer_candidate_kind')}"] += 1
            if case.get("candidate_menu_id"):
                summary["candidate_menu_bound_cases"] += 1
            if case.get("critique_selected_menu_verified"):
                summary["critique_selected_menu_verified_cases"] += 1
    clusters: Dict[str, List[Dict[str, Any]]] = {}
    for case in cases:
        clusters.setdefault(str(case.get("issue_cluster_key") or ""), []).append(case)
    for cluster_cases in clusters.values():
        claim_ids = sorted({str(case.get("claim_id") or "") for case in cluster_cases if str(case.get("claim_id") or "")})
        for index, case in enumerate(cluster_cases):
            case["issue_cluster_size"] = len(cluster_cases)
            case["issue_cluster_representative"] = index == 0
            case["issue_cluster_claim_ids"] = ", ".join(claim_ids)
    summary["verified_review_issue_cluster_count"] = len([key for key in clusters if key])
    summary["duplicate_review_issue_row_count"] = max(0, len(cases) - summary["verified_review_issue_cluster_count"])
    summary["reviewer_candidate_review_issue_cluster_count"] = len(
        {
            str(case.get("issue_cluster_key") or "")
            for case in cases
            if str(case.get("source_of_expectation") or "") == "reviewer_candidate"
        }
    )
    direct_quote_cluster_keys: set[str] = set()
    direct_quote_semantic_keys: set[str] = set()
    for key, cluster_cases in clusters.items():
        if not key or not cluster_cases:
            continue
        representative = cluster_cases[0]
        summary[f"cluster_type::{representative.get('issue_type')}"] += 1
        origin_kind = _cluster_origin_kind(cluster_cases)
        summary[f"cluster_origin::{origin_kind}"] += 1
        source = str(representative.get("source_of_expectation") or "unknown")
        slot = str(representative.get("review_issue_slot") or "unknown")
        summary[f"cluster_source::{source}"] += 1
        summary[f"cluster_slot::{slot}"] += 1
        if any(case.get("candidate_menu_id") for case in cluster_cases):
            summary["candidate_menu_bound_clusters"] += 1
        if any(case.get("critique_selected_menu_verified") for case in cluster_cases):
            summary["critique_selected_verified_cluster_count"] += 1
        if representative.get("bucket") == "quote_grounded_review_issue":
            direct_quote_cluster_keys.add(key)
            semantic_key = "|".join(
                str(representative.get(field) or "")
                for field in ("paper_id", "issue_cluster_claim_ids", "issue_cluster_target")
            )
            direct_quote_semantic_keys.add(semantic_key)
    summary["quote_grounded_review_issue_cluster_count"] = len(direct_quote_cluster_keys)
    summary["quote_grounded_direct_quote_duplicate_cluster_count"] = max(
        0,
        len(direct_quote_cluster_keys) - len(direct_quote_semantic_keys),
    )
    summary["quote_duplicate_merged_verified_review_issue_cluster_count"] = max(
        0,
        summary["verified_review_issue_cluster_count"] - summary["quote_grounded_direct_quote_duplicate_cluster_count"],
    )
    return cases, dict(summary)


def _md_escape(value: Any) -> str:
    return str(value or "").replace("|", "\\|").replace("\n", " ")


def render_markdown(input_path: Path, cases: List[Dict[str, Any]], summary: Dict[str, int]) -> str:
    lines = [
        "# Review Issue Case Table",
        "",
        f"- run: `{input_path}`",
        f"- verified review issue cases: `{summary.get('verified_review_issue_cases', 0)}`",
        f"- verified review issue clusters: `{summary.get('verified_review_issue_cluster_count', 0)}`",
        f"- duplicate issue rows: `{summary.get('duplicate_review_issue_row_count', 0)}`",
        f"- quote-grounded cases: `{summary.get('bucket::quote_grounded_review_issue', 0)}`",
        f"- obligation-grounded cases: `{summary.get('bucket::obligation_grounded_review_issue', 0)}`",
        f"- reviewer-candidate cases: `{summary.get('source::reviewer_candidate', 0)}`",
        f"- critique-payload candidate cases: `{summary.get('candidate_kind::critique_payload_candidate', 0)}`",
        f"- deterministic-seed candidate cases: `{summary.get('candidate_kind::deterministic_reviewer_seed', 0)}`",
        f"- candidate-menu-bound cases: `{summary.get('candidate_menu_bound_cases', 0)}`",
        f"- candidate-menu-bound clusters: `{summary.get('candidate_menu_bound_clusters', 0)}`",
        f"- critique-selected verified cases: `{summary.get('critique_selected_menu_verified_cases', 0)}`",
        f"- critique-selected verified clusters: `{summary.get('critique_selected_verified_cluster_count', 0)}`",
        f"- reviewer-candidate clusters: `{summary.get('reviewer_candidate_review_issue_cluster_count', 0)}`",
        f"- claim-obligation fallback cases: `{summary.get('source::claim_obligation', 0)}`",
        f"- direct quote clusters: `{summary.get('quote_grounded_review_issue_cluster_count', 0)}`",
        f"- direct quote duplicate merge candidates: `{summary.get('quote_grounded_direct_quote_duplicate_cluster_count', 0)}`",
        f"- quote-duplicate-merged clusters: `{summary.get('quote_duplicate_merged_verified_review_issue_cluster_count', 0)}`",
        f"- critique-payload clusters: `{summary.get('cluster_origin::critique_payload_candidate', 0)}`",
        f"- deterministic-seed clusters: `{summary.get('cluster_origin::deterministic_reviewer_seed', 0)}`",
        f"- claim-obligation fallback clusters: `{summary.get('cluster_origin::claim_obligation_fallback', 0)}`",
        "",
        "| paper_id | cluster id | cluster target | cluster size | representative | cluster claim ids | bucket | issue_type | slot | claim_id | source | discovery origin | entity source | candidate kind | critique selected | selected menu ids | candidate id | candidate menu id | missing/mismatch | inventory count | inventory sources | inventory anchor type | ablation target quality | ablation target reason | verification basis | rejection reason | inventory/quote locator | inventory/quote | claim anchor |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for case in cases:
        lines.append(
            "| "
            + " | ".join(
                _md_escape(case.get(key))
                for key in (
                    "paper_id",
                    "issue_cluster_id",
                    "issue_cluster_target",
                    "issue_cluster_size",
                    "issue_cluster_representative",
                    "issue_cluster_claim_ids",
                    "bucket",
                    "issue_type",
                    "review_issue_slot",
                    "claim_id",
                    "source_of_expectation",
                    "discovery_origin",
                    "entity_source",
                    "reviewer_candidate_kind",
                    "critique_selected_menu_verified",
                    "critique_selected_candidate_menu_ids",
                    "reviewer_candidate_id",
                    "candidate_menu_id",
                    "missing_or_mismatch",
                    "inventory_count",
                    "inventory_sources",
                    "inventory_anchor_type",
                    "ablation_target_quality",
                    "ablation_target_quality_reason",
                    "verification_basis",
                    "rejection_reason",
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
