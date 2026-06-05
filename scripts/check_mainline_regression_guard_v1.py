#!/usr/bin/env python3
"""Offline regression guard for the Mainline-Final-v1 paper-facing artifacts.

The guard reports cross-metric failures instead of optimizing a single score.
It is intentionally conservative: by default it writes a report and exits 0;
use --fail-on-regression in CI if these checks should block a run.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agent_system.environments.env_package.review.state import build_decision_hygiene_view, render_user_report

SUPPORT_STANCES = {"supports", "support", "partially_supports", "partially_supporting"}
VERIFIED_LABELS = {"paper_grounded_exact", "paper_grounded_normalized"}
LEAK_TERMS = (
    "7. Audit Trace",
    "audit trace",
    "binary_decision",
    "recommendation_view",
    "Final Decision:",
    "internal ids",
    "internal id",
    "system did not see",
    "evidence was filtered",
    "Positive/support evidence was filtered",
    "negative evidence formation",
    "copied negative_or_gap",
    "hard-negative evidence",
    "system salvage",
    "system recovery",
    "recovery operation",
    "recovery patch",
    "evidence-recovery-missing",
)


def _load_jsonl(path: Path) -> List[Dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _real_claim_ids(state: Dict[str, Any]) -> set[str]:
    ids: set[str] = set()
    for claim in state.get("claims", []) or []:
        if not isinstance(claim, dict):
            continue
        cid = str(claim.get("claim_id") or "")
        if not cid or cid.startswith(("claim-context", "claim-fallback", "context", "recovery")):
            continue
        if claim.get("claim_origin_kind") in {"context_synthesized", "fallback"}:
            continue
        ids.add(cid)
    return ids


def _is_strong_support(evidence: Dict[str, Any]) -> bool:
    return str(evidence.get("strength") or "").lower() == "strong" and str(evidence.get("stance") or "").lower() in SUPPORT_STANCES


def _is_verified(evidence: Dict[str, Any]) -> bool:
    return str(evidence.get("verified_grounding_label") or "") in VERIFIED_LABELS


def _is_semantic_support(evidence: Dict[str, Any]) -> bool:
    return str(evidence.get("semantic_grounding_label") or "") == "semantic_support_verified"


def _is_negative(evidence: Dict[str, Any]) -> bool:
    fields = " ".join(str(evidence.get(key) or "").lower() for key in ("stance", "strength", "support_source_bucket", "source", "evidence_type"))
    return any(token in fields for token in ("missing", "contradict", "negative", "gap", "limitation")) and not any(token in fields for token in ("supports", "supporting"))


def _report_leaks(text: str) -> List[str]:
    lowered = text.lower()
    leaks: List[str] = []
    for term in LEAK_TERMS:
        if term.lower() in lowered:
            leaks.append(term)
    return leaks


def audit(rows: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    rows = list(rows)
    counts = Counter()
    leak_cases: List[Dict[str, Any]] = []
    recovery_failures = Counter()
    active_flaw_total = 0
    active_flaw_with_grounded_negative = 0
    final_support_pairs = set()

    for row in rows:
        paper_id = str(row.get("paper_id") or "")
        state = row.get("review_state") or {}
        if not isinstance(state, dict):
            continue
        real_claims = _real_claim_ids(state)
        report = str(row.get("final_report") or "")
        stored_user_report = str(state.get("user_report") or "")
        computed_user_report = render_user_report(state, {})
        report_leaks = _report_leaks(report)
        stored_user_report_leaks = _report_leaks(stored_user_report)
        computed_user_report_leaks = _report_leaks(computed_user_report)
        if report_leaks:
            counts["stored_final_report_leak_count"] += 1
            if len(leak_cases) < 12:
                leak_cases.append({"paper_id": paper_id, "artifact": "stored_final_report", "leaks": report_leaks})
        if stored_user_report_leaks:
            counts["stored_user_report_leak_count"] += 1
            if len(leak_cases) < 12:
                leak_cases.append({"paper_id": paper_id, "artifact": "stored_user_report", "leaks": stored_user_report_leaks})
        if computed_user_report_leaks:
            counts["computed_user_report_leak_count"] += 1
            if len(leak_cases) < 12:
                leak_cases.append({"paper_id": paper_id, "artifact": "computed_user_report", "leaks": computed_user_report_leaks})

        grounded_negative_ids = set()
        for evidence in state.get("evidence_map", []) or []:
            if not isinstance(evidence, dict):
                continue
            if _is_negative(evidence) and _is_verified(evidence) and str(evidence.get("semantic_grounding_label") or "") == "semantic_negative_verified":
                eid = str(evidence.get("evidence_id") or "")
                if eid:
                    grounded_negative_ids.add(eid)

        hygiene_view = build_decision_hygiene_view(state)
        hygiene = hygiene_view.get("decision_hygiene", {}) if isinstance(hygiene_view, dict) else {}
        trace = hygiene.get("support_survival_trace") or []
        for item in trace:
            if not isinstance(item, dict):
                continue
            counts["strong_support_total"] += 1
            if item.get("claim_kind") == "paper_extracted":
                counts["real_strong_support_total"] += 1
                if item.get("verified_grounding_label") in VERIFIED_LABELS:
                    counts["verified_real_strong_support_total"] += 1
                if item.get("semantic_grounding_label") == "semantic_support_verified":
                    counts["semantic_verified_real_strong_support_total"] += 1
                if item.get("included_in_final_view"):
                    final_support_pairs.add((paper_id, str(item.get("claim_id") or ""), str(item.get("quote_id") or item.get("raw_quote") or item.get("evidence_id") or "")))
            else:
                counts["nonreal_strong_support_total"] += 1
                if item.get("included_in_final_view"):
                    counts["final_nonreal_strong_support_total"] += 1

        for evidence in state.get("evidence_map", []) or []:
            if not isinstance(evidence, dict):
                continue
            if _is_negative(evidence):
                counts["negative_evidence_total"] += 1
                if _is_verified(evidence):
                    counts["verified_negative_evidence_total"] += 1
                if _is_verified(evidence) and str(evidence.get("semantic_grounding_label") or "") == "semantic_negative_verified":
                    counts["semantic_verified_negative_evidence_total"] += 1

        for flaw in state.get("flaw_candidates", []) or []:
            if not isinstance(flaw, dict) or flaw.get("status") in {"downgraded", "retracted"}:
                continue
            active_flaw_total += 1
            flaw_negative_ids = {str(eid) for eid in (flaw.get("verified_negative_evidence_ids") or []) if eid}
            flaw_negative_ids.update(str(eid) for eid in (flaw.get("negative_evidence_ids") or []) if eid)
            if flaw_negative_ids & grounded_negative_ids:
                active_flaw_with_grounded_negative += 1

        for log in row.get("turn_logs", []) or []:
            if not isinstance(log, dict):
                continue
            if log.get("recovery_attempted"):
                counts["recovery_attempted"] += 1
            if log.get("recovery_patch_validated"):
                counts["recovery_patch_validated"] += 1
            if log.get("recovery_patch_committed"):
                counts["recovery_patch_committed"] += 1
            code = str(log.get("recovery_failure_code") or "")
            if code:
                recovery_failures[code] += 1

    counts["paper_count"] = len(rows)
    counts["active_flaw_total"] = active_flaw_total
    counts["active_flaw_with_grounded_negative"] = active_flaw_with_grounded_negative
    counts["active_flaw_without_grounded_negative"] = max(0, active_flaw_total - active_flaw_with_grounded_negative)
    counts["independent_semantic_verified_real_support_pairs"] = len(final_support_pairs)

    failures: List[str] = []
    warnings: List[str] = []
    if counts["computed_user_report_leak_count"]:
        failures.append("computed_user_report_leaks_machine_audit_terms")
    if counts["stored_final_report_leak_count"]:
        warnings.append("stored_final_report_contains_machine_audit_terms_or_old_artifact")
    if counts["stored_user_report_leak_count"]:
        warnings.append("stored_user_report_contains_legacy_process_terms")
    if counts["final_nonreal_strong_support_total"]:
        failures.append("final_nonreal_strong_support_present")
    if counts["nonreal_strong_support_total"]:
        warnings.append("merged_nonreal_support_dropped_before_final_view")
    if counts["semantic_verified_real_strong_support_total"] < 15:
        warnings.append("semantic_verified_real_support_low")
    if counts["active_flaw_total"] and active_flaw_with_grounded_negative / max(active_flaw_total, 1) < 0.5:
        warnings.append("grounded_negative_flaw_coverage_below_half")
    if counts["recovery_attempted"] and not counts["recovery_patch_committed"]:
        warnings.append("recovery_attempted_without_commit")

    for key in (
        "stored_final_report_leak_count",
        "stored_user_report_leak_count",
        "computed_user_report_leak_count",
        "strong_support_total",
        "nonreal_strong_support_total",
        "final_nonreal_strong_support_total",
        "real_strong_support_total",
        "verified_real_strong_support_total",
        "semantic_verified_real_strong_support_total",
        "negative_evidence_total",
        "verified_negative_evidence_total",
        "semantic_verified_negative_evidence_total",
        "recovery_attempted",
        "recovery_patch_validated",
        "recovery_patch_committed",
        "independent_semantic_verified_real_support_pairs",
    ):
        counts.setdefault(key, 0)

    result = {k: int(v) for k, v in counts.items()}
    result.update(
        {
            "active_flaw_grounded_negative_rate": round(active_flaw_with_grounded_negative / max(active_flaw_total, 1), 4),
            "recovery_failure_codes": {str(k): int(v) for k, v in recovery_failures.most_common()},
            "failures": failures,
            "warnings": warnings,
            "leak_cases": leak_cases,
            "guard_passed": not failures,
        }
    )
    return result


def write_markdown(result: Dict[str, Any], output: Path, input_path: Path) -> None:
    lines = [
        "# Mainline Regression Guard v1",
        "",
        f"- 输入结果: `{input_path}`",
        f"- guard passed: `{result.get('guard_passed')}`",
        "",
        "## Core Metrics",
    ]
    for key in (
        "paper_count",
        "stored_final_report_leak_count",
        "stored_user_report_leak_count",
        "computed_user_report_leak_count",
        "strong_support_total",
        "real_strong_support_total",
        "verified_real_strong_support_total",
        "semantic_verified_real_strong_support_total",
        "nonreal_strong_support_total",
        "final_nonreal_strong_support_total",
        "independent_semantic_verified_real_support_pairs",
        "negative_evidence_total",
        "verified_negative_evidence_total",
        "semantic_verified_negative_evidence_total",
        "active_flaw_total",
        "active_flaw_with_grounded_negative",
        "active_flaw_without_grounded_negative",
        "recovery_attempted",
        "recovery_patch_validated",
        "recovery_patch_committed",
    ):
        lines.append(f"- {key}: {result.get(key, 0)}")
    lines.append(f"- active_flaw_grounded_negative_rate: {result.get('active_flaw_grounded_negative_rate', 0)}")
    lines.extend(["", "## Failures"])
    if result.get("failures"):
        lines.extend(f"- `{item}`" for item in result["failures"])
    else:
        lines.append("- 无")
    lines.extend(["", "## Warnings"])
    if result.get("warnings"):
        lines.extend(f"- `{item}`" for item in result["warnings"])
    else:
        lines.append("- 无")
    lines.extend(["", "## Recovery Failure Codes"])
    for key, value in result.get("recovery_failure_codes", {}).items():
        lines.append(f"- `{key}`: {value}")
    lines.extend(["", "## Leak Cases"])
    for item in result.get("leak_cases", [])[:10]:
        lines.append(f"- `{item.get('paper_id')}` / {item.get('artifact')}: {', '.join(item.get('leaks') or [])}")
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Check cross-metric regressions for mainline full-run artifacts.")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--output-md", required=True)
    parser.add_argument("--fail-on-regression", action="store_true")
    args = parser.parse_args()
    input_path = Path(args.input)
    result = audit(_load_jsonl(input_path))
    Path(args.output_json).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(result, Path(args.output_md), input_path)
    if args.fail_on_regression and not result.get("guard_passed"):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
