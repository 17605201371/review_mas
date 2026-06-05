#!/usr/bin/env python3
"""R7 (spec task 11): Case Audit Generator.

Reads a saved review_infer jsonl, recomputes decision hygiene offline (zero GPU)
via build_decision_hygiene_view, and emits case bundles for paper presentation
and human spot-checking.

Case types: positive_strong, empirical_support, verified_moderate,
negative_concern, contested_support, recovery_success, recovery_blocked,
dropped_support.

Each bundle contains: claim, quote, locator, positive_evidence, negative_evidence,
state_transition, final_report_snippet, audit_flags, manual_label (empty slot).

Guard rails: reads saved state only; never runs the model; a record that cannot
be processed is recorded with an audit flag and skipped (generation continues);
a case type with no matches yields an empty list rather than failing.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agent_system.environments.env_package.review.state import (
    build_decision_hygiene_view,
    _build_support_survival_trace,
    _negative_burden_claim_ids,
)

SCHEMA_VERSION = "case_audit_v1_20260602"

CASE_TYPES = [
    "positive_strong",
    "empirical_support",
    "verified_moderate",
    "negative_concern",
    "contested_support",
    "recovery_success",
    "recovery_blocked",
    "dropped_support",
]


def _load_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def _text(value: Any, limit: int = 240) -> str:
    text = " ".join(str(value or "").split())
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 1)].rstrip() + "\u2026"


def _claim_lookup(state: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    for claim in state.get("claims", []) or []:
        if isinstance(claim, dict) and str(claim.get("claim_id") or ""):
            out[str(claim["claim_id"])] = claim
    return out


def _evidence_lookup(state: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    for ev in state.get("evidence_map", []) or []:
        if isinstance(ev, dict) and str(ev.get("evidence_id") or ""):
            out[str(ev["evidence_id"])] = ev
    return out


def _bundle(case_type, paper_id, claim, quote, locator, pos_ev, neg_ev,
            state_transition, final_report_snippet, audit_flags) -> Dict[str, Any]:
    return {
        "case_type": case_type,
        "paper_id": paper_id,
        "claim": _text(claim),
        "quote": _text(quote),
        "locator": locator,
        "positive_evidence": pos_ev,
        "negative_evidence": neg_ev,
        "state_transition": state_transition,
        "final_report_snippet": _text(final_report_snippet, 400),
        "audit_flags": audit_flags,
        "manual_label": "",  # empty slot for human annotation
    }


def _row_state(row: Dict[str, Any]) -> Dict[str, Any]:
    state = row.get("review_state") or {}
    if not isinstance(state, dict):
        return {}
    if row.get("paper_id") and not state.get("paper_id"):
        state = dict(state)
        state["paper_id"] = row.get("paper_id")
    return state


def generate(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    bundles: Dict[str, List[Dict[str, Any]]] = {ct: [] for ct in CASE_TYPES}
    errors: List[Dict[str, Any]] = []
    for row in rows:
        paper_id = str(row.get("paper_id") or "")
        try:
            state = _row_state(row)
            view = build_decision_hygiene_view(state)
            claims = _claim_lookup(state)
            ev_by_id = _evidence_lookup(state)
            final_report = state.get("final_report") or row.get("final_report") or ""
            trace = _build_support_survival_trace(state)
            negative_claim_ids = _negative_burden_claim_ids(state)

            for item in trace:
                claim_id = str(item.get("claim_id") or "")
                claim_text = (claims.get(claim_id) or {}).get("claim") or ""
                quote = item.get("raw_quote") or item.get("evidence") or ""
                locator = {
                    "source_locator": item.get("source_locator") or "",
                    "locator_type": item.get("locator_type") or item.get("source_locator_type") or "generic",
                    "locator_confidence": item.get("locator_confidence") or item.get("source_locator_confidence") or 0.0,
                }
                tier = str(item.get("support_admission_tier") or "")
                included = bool(item.get("included_in_final_view"))
                transition = {
                    "support_admission_tier": tier,
                    "included_in_final_view": included,
                    "final_support_depth": item.get("final_support_depth") or "",
                    "support_drop_reason": item.get("support_drop_reason") or "",
                }
                flags = []
                if item.get("empirical_admission_block_reason"):
                    flags.append(str(item.get("empirical_admission_block_reason")))
                pos_ev = {"evidence_id": item.get("evidence_id"), "quote": _text(quote)}

                # positive strong (included, real strong)
                if included and tier == "verified_strong":
                    bundles["positive_strong"].append(_bundle(
                        "positive_strong", paper_id, claim_text, quote, locator,
                        pos_ev, None, transition, final_report, flags))
                    if item.get("is_empirical_admissible") or item.get("final_support_depth") == "deep":
                        bundles["empirical_support"].append(_bundle(
                            "empirical_support", paper_id, claim_text, quote, locator,
                            pos_ev, None, transition, final_report, flags))
                # verified moderate
                if tier == "verified_moderate":
                    bundles["verified_moderate"].append(_bundle(
                        "verified_moderate", paper_id, claim_text, quote, locator,
                        pos_ev, None, transition, final_report, flags))
                # contested
                if item.get("contested_support"):
                    bundles["contested_support"].append(_bundle(
                        "contested_support", paper_id, claim_text, quote, locator,
                        pos_ev, {"negative_burden_claim": claim_id in negative_claim_ids},
                        transition, final_report, flags))
                # dropped support (not included, had a drop reason)
                if not included and item.get("support_drop_reason"):
                    bundles["dropped_support"].append(_bundle(
                        "dropped_support", paper_id, claim_text, quote, locator,
                        pos_ev, None, transition, final_report,
                        flags + [str(item.get("support_drop_reason"))]))

            # negative concern: claims carrying verified negative burden
            for claim_id in negative_claim_ids:
                claim_text = (claims.get(claim_id) or {}).get("claim") or ""
                bundles["negative_concern"].append(_bundle(
                    "negative_concern", paper_id, claim_text, "", {},
                    None, {"claim_id": claim_id, "verified_negative_concern": True},
                    {}, final_report, []))

            # recovery success / blocked from latest patch log
            patch = state.get("_latest_patch_log") or {}
            if isinstance(patch, dict) and patch.get("recovery_attempted"):
                code = str(patch.get("recovery_failure_code") or "")
                rec_bundle = _bundle(
                    "recovery_success" if patch.get("recovery_committed") else "recovery_blocked",
                    paper_id,
                    (claims.get(str(patch.get("recovery_target_id") or "")) or {}).get("claim") or "",
                    "", {},
                    None,
                    {"target_type": patch.get("recovery_target_type"), "target_id": patch.get("recovery_target_id")},
                    {"old_status": patch.get("old_status"), "new_status": patch.get("new_status"),
                     "failure_code": code},
                    final_report,
                    [code] if code else [])
                if patch.get("recovery_committed"):
                    bundles["recovery_success"].append(rec_bundle)
                else:
                    bundles["recovery_blocked"].append(rec_bundle)
        except Exception as exc:  # never abort the whole run on one bad record
            errors.append({"paper_id": paper_id, "error": f"{type(exc).__name__}: {exc}"})
            continue

    return {
        "schema_version": SCHEMA_VERSION,
        "paper_count": len(rows),
        "case_counts": {ct: len(bundles[ct]) for ct in CASE_TYPES},
        "bundles": bundles,
        "errors": errors,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="R7 case audit generator (offline, zero GPU)")
    ap.add_argument("--input", required=True, help="saved review_infer jsonl")
    ap.add_argument("--output", required=True, help="output json path")
    ap.add_argument("--limit-per-type", type=int, default=0, help="cap bundles per case type (0=all)")
    args = ap.parse_args()

    rows = _load_jsonl(Path(args.input))
    result = generate(rows)
    if args.limit_per_type > 0:
        for ct in CASE_TYPES:
            result["bundles"][ct] = result["bundles"][ct][: args.limit_per_type]
    Path(args.output).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] case audit -> {args.output}")
    print(f"paper_count={result['paper_count']} errors={len(result['errors'])}")
    print("case_counts:", json.dumps(result["case_counts"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
