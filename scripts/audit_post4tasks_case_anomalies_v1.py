#!/usr/bin/env python3
"""Offline case audit for post4tasks negative/recovery anomalies.

This script is intentionally read-only: it loads an existing review JSONL,
recomputes decision hygiene with the current code, and exports the concrete
cases behind open conflicts, evidence misbinding, semantic negative-anchor
rejections, and verified-negative flaw count anomalies.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from agent_system.environments.env_package.review.state import (
    _flaw_explicit_negative_evidence_ids,
    _is_grounded_paper_negative_evidence_record,
    _verified_actionable_negative_evidence_ids_for_flaw,
    _verified_negative_evidence_ids_for_flaw,
    build_decision_hygiene_view,
)


SCHEMA_VERSION = "post4tasks_case_anomaly_audit_v1_20260611"
SEMANTIC_NEGATIVE_LABELS = {"semantic_negative_verified", "semantic_support_verified"}


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def _paper_id(row: Dict[str, Any]) -> str:
    return str(row.get("paper_id") or (row.get("review_state") or {}).get("paper_id") or "")


def _stored_hygiene(row: Dict[str, Any]) -> Dict[str, Any]:
    return (((row.get("review_state") or {}).get("state_audit") or {}).get("decision_hygiene") or {})


def _claim_lookup(state: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    return {
        str(item.get("claim_id") or ""): item
        for item in state.get("claims", []) or []
        if isinstance(item, dict) and str(item.get("claim_id") or "")
    }


def _evidence_lookup(state: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    return {
        str(item.get("evidence_id") or ""): item
        for item in state.get("evidence_map", []) or []
        if isinstance(item, dict) and str(item.get("evidence_id") or "")
    }


def _flaw_lookup(state: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    return {
        str(item.get("flaw_id") or ""): item
        for item in state.get("flaw_candidates", []) or []
        if isinstance(item, dict) and str(item.get("flaw_id") or "")
    }


def _claim_text(claim: Optional[Dict[str, Any]]) -> str:
    return str((claim or {}).get("claim") or (claim or {}).get("text") or "")


def _evidence_quote(evidence: Optional[Dict[str, Any]]) -> str:
    return str((evidence or {}).get("raw_quote") or (evidence or {}).get("evidence") or "")


def _positive_support_ids(claim_id: str, claim: Optional[Dict[str, Any]], evidence_by_id: Dict[str, Dict[str, Any]]) -> List[str]:
    ids: List[str] = []
    for evidence_id in (claim or {}).get("supporting_evidence_ids", []) or []:
        eid = str(evidence_id or "").strip()
        if eid and eid not in ids:
            ids.append(eid)
    for evidence_id, evidence in evidence_by_id.items():
        if str(evidence.get("claim_id") or "") != claim_id:
            continue
        if str(evidence.get("stance") or "").strip().lower() not in {"supports", "partially_supports", "partial_support"}:
            continue
        if str(evidence.get("verified_grounding_label") or "").strip() not in {"paper_grounded_exact", "paper_grounded_normalized"}:
            continue
        if evidence_id not in ids:
            ids.append(evidence_id)
    return ids


def _matching_contested_relation(state: Dict[str, Any], claim_id: str, negative_evidence_id: str) -> Optional[Dict[str, Any]]:
    for relation in state.get("contested_relations", []) or []:
        if not isinstance(relation, dict):
            continue
        if claim_id and str(relation.get("claim_id") or "") != claim_id:
            continue
        neg_ids = {str(item) for item in relation.get("negative_evidence_ids", []) or []}
        if negative_evidence_id and negative_evidence_id not in neg_ids:
            continue
        return relation
    return None


def _mark_contested_turns(row: Dict[str, Any], claim_id: str = "", flaw_id: str = "", negative_evidence_id: str = "") -> List[Dict[str, Any]]:
    turns: List[Dict[str, Any]] = []
    for turn in row.get("turn_logs", []) or []:
        if not isinstance(turn, dict):
            continue
        if str(turn.get("recovery_patch_operation") or "") != "mark_contested":
            continue
        target_id = str(turn.get("recovery_target_id") or "")
        relation_claim = str(turn.get("contested_relation_claim_id") or "")
        relation_neg_ids = {str(item) for item in turn.get("contested_relation_negative_evidence_ids", []) or []}
        if flaw_id and target_id == flaw_id:
            turns.append(turn)
        elif claim_id and relation_claim == claim_id:
            turns.append(turn)
        elif negative_evidence_id and negative_evidence_id in relation_neg_ids:
            turns.append(turn)
    return turns


def audit_open_conflicts(row: Dict[str, Any], recomputed_state: Dict[str, Any]) -> List[Dict[str, Any]]:
    state = row.get("review_state") or {}
    pid = _paper_id(row)
    claims = _claim_lookup(state)
    evidence = _evidence_lookup(state)
    flaws = _flaw_lookup(state)
    recomputed_hygiene = recomputed_state.get("decision_hygiene") or {}
    if int(recomputed_hygiene.get("open_conflict_count") or 0) == 0:
        return []
    cases: List[Dict[str, Any]] = []
    for conflict in state.get("conflict_notes", []) or []:
        if not isinstance(conflict, dict):
            continue
        claim_id = str(conflict.get("claim_id") or "")
        flaw_id = str(conflict.get("flaw_id") or "")
        negative_evidence_id = str(conflict.get("evidence_id") or "")
        flaw = flaws.get(flaw_id, {})
        if not negative_evidence_id:
            neg_ids = list(flaw.get("negative_evidence_ids", []) or flaw.get("evidence_ids", []) or [])
            negative_evidence_id = str(neg_ids[0]) if neg_ids else ""
        ev = evidence.get(negative_evidence_id, {})
        relation = _matching_contested_relation(state, claim_id, negative_evidence_id)
        mark_turns = _mark_contested_turns(row, claim_id=claim_id, flaw_id=flaw_id, negative_evidence_id=negative_evidence_id)
        conflict_type = str(conflict.get("conflict_type") or "")
        if relation:
            remained = "contested_relation_written_but_conflict_note_remained_open"
        elif conflict_type in {"support_only_flaw_without_negative_grounding", "flaw_anchor_gap"} and int(recomputed_hygiene.get("open_conflict_count") or 0) == 0:
            remained = "stale_support_only_conflict_filtered_by_recomputed_view"
        elif mark_turns:
            remained = "mark_contested_attempted_without_matching_final_relation"
        else:
            remained = "no_matching_mark_contested_or_relation"
        cases.append({
            "paper_id": pid,
            "turn_id": mark_turns[-1].get("turn_id") if mark_turns else None,
            "claim_id": claim_id,
            "claim_text": _claim_text(claims.get(claim_id)),
            "flaw_id": flaw_id,
            "negative_evidence_id": negative_evidence_id,
            "positive_support_evidence_ids": _positive_support_ids(claim_id, claims.get(claim_id), evidence),
            "negative_quote": _evidence_quote(ev),
            "negative_locator": str(ev.get("source_locator") or ev.get("locator") or ""),
            "negative_type": str(ev.get("negative_evidence_type") or ""),
            "conflict_id": str(conflict.get("conflict_id") or ""),
            "conflict_reason": str(conflict.get("note") or conflict.get("conflict_type") or ""),
            "contested_relation_id": str((relation or {}).get("relation_id") or ""),
            "whether_mark_contested_attempted": bool(mark_turns),
            "whether_mark_contested_committed": any(bool(turn.get("recovery_patch_committed")) for turn in mark_turns),
            "why_conflict_remained_open": remained,
            "final_report_impact": "stored_open_conflict" if int(_stored_hygiene(row).get("open_conflict_count") or 0) else "no_stored_open_conflict",
        })
    return cases


def audit_misbinding(row: Dict[str, Any]) -> List[Dict[str, Any]]:
    state = row.get("review_state") or {}
    pid = _paper_id(row)
    claims = _claim_lookup(state)
    evidence = _evidence_lookup(state)
    flaws = _flaw_lookup(state)
    cases: List[Dict[str, Any]] = []
    for target in (_stored_hygiene(row).get("state_contamination_targets") or []):
        if not isinstance(target, dict) or str(target.get("error_type") or "") != "evidence_misbinding":
            continue
        target_id = str(target.get("target_id") or "")
        flaw = flaws.get(target_id, {})
        neg_ids = list(flaw.get("negative_evidence_ids", []) or flaw.get("evidence_ids", []) or [])
        evidence_id = str(neg_ids[0]) if neg_ids else target_id
        ev = evidence.get(evidence_id, {})
        claim_id = str(ev.get("claim_id") or (flaw.get("related_claim_ids") or [""])[0] or "")
        cases.append({
            "paper_id": pid,
            "turn_id": None,
            "claim_id": claim_id,
            "claim_text": _claim_text(claims.get(claim_id)),
            "evidence_id": evidence_id,
            "evidence_quote": _evidence_quote(ev),
            "evidence_locator": str(ev.get("source_locator") or ev.get("locator") or ""),
            "evidence_stance": str(ev.get("stance") or ""),
            "linked_claim_id": str(ev.get("claim_id") or ""),
            "expected_claim_id": str((flaw.get("related_claim_ids") or [""])[0] or ""),
            "flaw_id": target_id if str(target.get("target_type") or "") == "flaw" else str(flaw.get("flaw_id") or ""),
            "negative_evidence_id": evidence_id,
            "binding_rationale": str(ev.get("binding_rationale") or ""),
            "why_misbinding_counted": str(target.get("evidence_context") or target.get("reason") or target.get("error_type") or ""),
            "final_support_or_negative_view_impact": str(target.get("repairability") or ""),
        })
    return cases


def audit_semantic_negative_anchors(row: Dict[str, Any]) -> List[Dict[str, Any]]:
    state = row.get("review_state") or {}
    pid = _paper_id(row)
    claims = _claim_lookup(state)
    evidence = _evidence_lookup(state)
    cases: List[Dict[str, Any]] = []
    before = _stored_hygiene(row)
    after = (build_decision_hygiene_view(state).get("decision_hygiene") or {})
    for flaw in state.get("flaw_candidates", []) or []:
        if not isinstance(flaw, dict):
            continue
        flaw_id = str(flaw.get("flaw_id") or "")
        claim_id = str((flaw.get("related_claim_ids") or [""])[0] or "")
        for evidence_id in _flaw_explicit_negative_evidence_ids(flaw):
            ev = evidence.get(str(evidence_id), {})
            semantic_label = str(ev.get("semantic_grounding_label") or "")
            if semantic_label in SEMANTIC_NEGATIVE_LABELS:
                continue
            cases.append({
                "paper_id": pid,
                "turn_id": None,
                "claim_id": claim_id,
                "claim_text": _claim_text(claims.get(claim_id)),
                "flaw_id": flaw_id,
                "negative_evidence_id": str(evidence_id),
                "raw_negative_quote": _evidence_quote(ev),
                "negative_locator": str(ev.get("source_locator") or ev.get("locator") or ""),
                "negative_type": str(ev.get("negative_evidence_type") or ""),
                "semantic_label": semantic_label,
                "anchor_claim_text": _claim_text(claims.get(str(ev.get("claim_id") or claim_id))),
                "anchor_quote_text": _evidence_quote(ev),
                "why_semantic_anchor_conflict": "semantic_label_not_negative_verified",
                "why_negative_evidence_rejected": "semantic_mismatch_or_unverified_negative_anchor",
                "whether_id_is_legacy_or_normalized": "normalized_resolved" if evidence_id in evidence else "legacy_or_unresolved",
                "final_view_before": {
                    "negative_semantic_anchor_conflict_count": before.get("negative_semantic_anchor_conflict_count", 0),
                    "invalid_negative_evidence_id_count_legacy": before.get("invalid_negative_evidence_id_count_legacy", 0),
                },
                "final_view_after": {
                    "negative_semantic_anchor_conflict_count": after.get("negative_semantic_anchor_conflict_count", 0),
                    "negative_evidence_semantic_rejected_count": after.get("negative_evidence_semantic_rejected_count", 0),
                    "verified_negative_flaw_count": after.get("verified_negative_flaw_count", 0),
                },
            })
    return cases


def audit_verified_flaw_mapping(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    all_negative_ids: List[str] = []
    all_verified_flaw_ids: List[str] = []
    flaw_to_negative: Dict[str, List[str]] = {}
    negative_to_flaw: Dict[str, List[str]] = defaultdict(list)
    legacy_negative_ids: List[str] = []
    quote_bank_negative_ids: List[str] = []
    critique_negative_quote_bank_ids: List[str] = []
    programmatic_negative_ids: List[str] = []

    for row in rows:
        pid = _paper_id(row)
        state = row.get("review_state") or {}
        view = build_decision_hygiene_view(state)
        evidence = _evidence_lookup(view)
        for evidence_id, ev in evidence.items():
            if _is_grounded_paper_negative_evidence_record(ev, view):
                scoped_id = f"{pid}:{evidence_id}"
                all_negative_ids.append(scoped_id)
                source = str(ev.get("source") or "")
                quote_id = str(ev.get("quote_id") or "")
                if "quote-bank" in evidence_id or source == "quote-bank-negative-grounding":
                    quote_bank_negative_ids.append(scoped_id)
                if quote_id.startswith("quote-critique-negative") or source == "critique-negative-quote-bank":
                    critique_negative_quote_bank_ids.append(scoped_id)
                if source in {"quote-bank-negative-grounding", "programmatic-negative-grounding"}:
                    programmatic_negative_ids.append(scoped_id)
        for flaw in view.get("flaw_candidates", []) or []:
            if not isinstance(flaw, dict):
                continue
            status = str(flaw.get("status") or "candidate")
            flaw_id = str(flaw.get("flaw_id") or "")
            explicit_ids = [str(item) for item in _flaw_explicit_negative_evidence_ids(flaw)]
            for evidence_id in explicit_ids:
                if evidence_id not in evidence:
                    legacy_negative_ids.append(f"{pid}:{flaw_id}:{evidence_id}")
            if status in {"downgraded", "retracted"}:
                continue
            verified_ids = [str(item) for item in _verified_negative_evidence_ids_for_flaw(flaw, view)]
            if not verified_ids:
                continue
            scoped_flaw_id = f"{pid}:{flaw_id}"
            all_verified_flaw_ids.append(scoped_flaw_id)
            flaw_to_negative[scoped_flaw_id] = [f"{pid}:{evidence_id}" for evidence_id in verified_ids]
            for evidence_id in verified_ids:
                negative_to_flaw[f"{pid}:{evidence_id}"].append(scoped_flaw_id)

    dup_neg = {eid: flaws for eid, flaws in negative_to_flaw.items() if len(flaws) > 1}
    flaw_counts = Counter(all_verified_flaw_ids)
    neg_counts = Counter(all_negative_ids)
    return {
        "all_negative_evidence_ids": sorted(all_negative_ids),
        "all_verified_negative_flaw_ids": sorted(all_verified_flaw_ids),
        "flaw_to_negative_evidence_mapping": flaw_to_negative,
        "negative_evidence_to_flaw_mapping": dict(negative_to_flaw),
        "duplicate_flaw_ids": sorted([fid for fid, count in flaw_counts.items() if count > 1]),
        "duplicate_negative_evidence_ids": sorted([eid for eid, count in neg_counts.items() if count > 1]),
        "shared_negative_evidence_ids": dup_neg,
        "legacy_negative_evidence_ids": sorted(legacy_negative_ids),
        "quote_bank_negative_ids": sorted(quote_bank_negative_ids),
        "critique_negative_quote_bank_ids": sorted(critique_negative_quote_bank_ids),
        "programmatic_negative_ids": sorted(programmatic_negative_ids),
        "current_verified_negative_flaw_count": len(set(all_verified_flaw_ids)),
        "current_negative_evidence_candidate_count": len(set(all_negative_ids)),
        "current_verified_actionable_negative_flaw_count": sum(
            1
            for row in rows
            for flaw in (build_decision_hygiene_view(row.get("review_state") or {}).get("flaw_candidates") or [])
            if isinstance(flaw, dict)
            and str(flaw.get("status") or "candidate") not in {"downgraded", "retracted"}
            and _verified_actionable_negative_evidence_ids_for_flaw(flaw, build_decision_hygiene_view(row.get("review_state") or {}))
        ),
    }


def _sum_metric(rows: Iterable[Dict[str, Any]], key: str, *, recompute: bool) -> int:
    total = 0
    for row in rows:
        if recompute:
            hygiene = build_decision_hygiene_view(row.get("review_state") or {}).get("decision_hygiene") or {}
        else:
            hygiene = _stored_hygiene(row)
        if key == "contamination_evidence_misbinding":
            type_counts = hygiene.get("state_contamination_type_counts") or {}
            if isinstance(type_counts, dict):
                total += int(type_counts.get("evidence_misbinding") or 0)
            continue
        total += int(hygiene.get(key) or 0)
    return total


def generate(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    open_conflict_cases: List[Dict[str, Any]] = []
    misbinding_cases: List[Dict[str, Any]] = []
    semantic_cases: List[Dict[str, Any]] = []
    for row in rows:
        recomputed_state = build_decision_hygiene_view(row.get("review_state") or {})
        open_conflict_cases.extend(audit_open_conflicts(row, recomputed_state))
        misbinding_cases.extend(audit_misbinding(row))
        semantic_cases.extend(audit_semantic_negative_anchors(row))
    mapping = audit_verified_flaw_mapping(rows)
    keys = [
        "state_contamination_count",
        "contamination_evidence_misbinding",
        "open_conflict_count",
        "negative_semantic_anchor_conflict_count",
        "invalid_negative_evidence_id_count_legacy",
        "negative_evidence_semantic_rejected_count",
        "negative_evidence_candidate_count",
        "verified_negative_flaw_count",
        "verified_actionable_negative_flaw_count",
        "potential_concern_count",
    ]
    return {
        "schema_version": SCHEMA_VERSION,
        "paper_count": len(rows),
        "stored_metric_totals": {key: _sum_metric(rows, key, recompute=False) for key in keys},
        "recomputed_metric_totals": {key: _sum_metric(rows, key, recompute=True) for key in keys},
        "p0_1_open_conflict_cases": open_conflict_cases,
        "p0_2_evidence_misbinding_cases": misbinding_cases,
        "p0_3_negative_semantic_anchor_cases": semantic_cases,
        "p0_4_verified_negative_flaw_mapping": mapping,
    }


def _table(headers: List[str], rows: List[List[Any]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(item).replace("\n", " ") for item in row) + " |")
    return "\n".join(lines)


def render_md(audit: Dict[str, Any], input_path: Path) -> str:
    stored = audit["stored_metric_totals"]
    recomputed = audit["recomputed_metric_totals"]
    lines = [
        "# Post4tasks Case Anomaly Audit v1",
        "",
        f"- input: `{input_path}`",
        f"- schema: `{audit['schema_version']}`",
        f"- papers: `{audit['paper_count']}`",
        "",
        "## Metric Before/After Recompute",
        "",
        _table(["metric", "stored", "recomputed"], [[k, stored.get(k, 0), recomputed.get(k, 0)] for k in stored]),
        "",
        "## P0-1 Open Conflict Cases",
        "",
        _table(
            ["paper_id", "claim_id", "flaw_id", "conflict_id", "negative_evidence_id", "why_conflict_remained_open"],
            [[c.get("paper_id"), c.get("claim_id"), c.get("flaw_id"), c.get("conflict_id"), c.get("negative_evidence_id"), c.get("why_conflict_remained_open")] for c in audit["p0_1_open_conflict_cases"]],
        ),
        "",
        "## P0-2 Evidence Misbinding Cases",
        "",
        _table(
            ["paper_id", "claim_id", "flaw_id", "evidence_id", "why_misbinding_counted"],
            [[c.get("paper_id"), c.get("claim_id"), c.get("flaw_id"), c.get("evidence_id"), c.get("why_misbinding_counted")] for c in audit["p0_2_evidence_misbinding_cases"]],
        ),
        "",
        "## P0-3 Negative Semantic Anchor Cases",
        "",
        _table(
            ["paper_id", "claim_id", "flaw_id", "negative_evidence_id", "semantic_label", "final_view_after"],
            [[c.get("paper_id"), c.get("claim_id"), c.get("flaw_id"), c.get("negative_evidence_id"), c.get("semantic_label"), c.get("final_view_after")] for c in audit["p0_3_negative_semantic_anchor_cases"]],
        ),
        "",
        "## P0-4 Verified Negative Flaw Mapping",
        "",
        f"- all_negative_evidence_ids: `{len(audit['p0_4_verified_negative_flaw_mapping']['all_negative_evidence_ids'])}`",
        f"- all_verified_negative_flaw_ids: `{len(audit['p0_4_verified_negative_flaw_mapping']['all_verified_negative_flaw_ids'])}`",
        f"- duplicate_negative_evidence_ids: `{len(audit['p0_4_verified_negative_flaw_mapping']['duplicate_negative_evidence_ids'])}`",
        f"- legacy_negative_evidence_ids: `{len(audit['p0_4_verified_negative_flaw_mapping']['legacy_negative_evidence_ids'])}`",
        f"- shared_negative_evidence_ids: `{len(audit['p0_4_verified_negative_flaw_mapping']['shared_negative_evidence_ids'])}`",
        "",
        "## Interpretation",
        "",
        "- Stored smoke8 anomalies are attributable to stale support-only conflict accounting, handled semantic negative-anchor rejection, and inactive duplicate flaw counting.",
        "- Recomputed metrics should be used to decide whether a runtime rerun is necessary; this script does not mutate the original run.",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Post4tasks smoke/full case anomaly audit (offline).")
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output-json", required=True, type=Path)
    parser.add_argument("--output-md", required=True, type=Path)
    args = parser.parse_args()
    rows = load_jsonl(args.input)
    audit = generate(rows)
    args.output_json.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    args.output_md.write_text(render_md(audit, args.input), encoding="utf-8")
    print(f"[OK] case anomaly audit -> {args.output_json} {args.output_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
