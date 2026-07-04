#!/usr/bin/env python3
"""P31.6 entry-gate audit for Critique-origin review-issue recovery.

This script is intentionally conservative: it can prove only the machine
checks needed before manual A/B audit.  It does not claim paper-ready quality.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple


PROTECTION_ZERO_METRICS = (
    "negative_evidence_unlinked_to_flaw",
    "positive_or_neutral_negative_candidate_count",
    "negative_grounding_conflict_count",
)

RED_FLAG_TERMS = {
    "retrieval_context": (
        "provided excerpt",
        "current context",
        "truncated",
        "not visible",
        "not shown",
        "not available",
        "not provided",
        "system did not see",
        "retrieval",
    ),
    "external_baseline": (
        "external baseline",
        "external baselines",
        "reference review",
        "oracle target",
        "oracle baseline",
    ),
    "author_limitation": (
        "future work",
        "we leave",
        "we plan",
        "we acknowledge",
        "limitation",
        "limitations",
    ),
}


def _load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def _as_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _clip(value: Any, limit: int = 180) -> str:
    text = " ".join(str(value or "").split())
    return text if len(text) <= limit else text[: limit - 3] + "..."


def _case_text(case: Dict[str, Any]) -> str:
    fields = (
        "paper_id",
        "issue_type",
        "claim_id",
        "source_of_expectation",
        "review_issue_slot",
        "entity_source",
        "discovery_origin",
        "missing_or_mismatch",
        "inventory_or_quote_locator",
        "inventory_or_quote",
        "verification_basis",
        "claim_anchor",
        "issue_cluster_key",
        "issue_cluster_target",
    )
    return "\n".join(str(case.get(field) or "") for field in fields).lower()


def _is_critique_origin(case: Dict[str, Any]) -> bool:
    if bool(case.get("critique_selected_menu_verified")):
        return True
    kind = str(case.get("reviewer_candidate_kind") or "")
    origin = str(case.get("discovery_origin") or "")
    candidate_id = str(case.get("reviewer_candidate_id") or "")
    if kind == "critique_payload_candidate":
        return True
    if origin.startswith("critique_payload"):
        return True
    if candidate_id.startswith("review-issue-candidate"):
        return True
    return False


def _cluster_cases(cases: Iterable[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    clusters: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for case in cases:
        key = str(case.get("issue_cluster_key") or case.get("evidence_id") or "")
        if key:
            clusters[key].append(case)
    return dict(clusters)


def _cluster_record(cluster_key: str, cases: List[Dict[str, Any]]) -> Dict[str, Any]:
    first = cases[0] if cases else {}
    claim_ids = sorted({str(case.get("claim_id") or "") for case in cases if case.get("claim_id")})
    evidence_ids = sorted({str(case.get("evidence_id") or "") for case in cases if case.get("evidence_id")})
    return {
        "issue_cluster_key": cluster_key,
        "paper_id": first.get("paper_id") or "",
        "issue_type": first.get("issue_type") or "",
        "issue_cluster_target": first.get("issue_cluster_target") or "",
        "case_count": len(cases),
        "claim_ids": claim_ids,
        "evidence_ids": evidence_ids,
        "missing_or_mismatch": _clip(first.get("missing_or_mismatch"), 220),
        "claim_anchor": _clip(first.get("claim_anchor"), 220),
        "inventory_or_quote_locator": _clip(first.get("inventory_or_quote_locator"), 140),
        "inventory_or_quote": _clip(first.get("inventory_or_quote"), 240),
        "review_issue_slot": first.get("review_issue_slot") or "",
        "discovery_origin": first.get("discovery_origin") or "",
        "reviewer_candidate_kind": first.get("reviewer_candidate_kind") or "",
    }


def _red_flags(cases: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    findings: List[Dict[str, Any]] = []
    for case in cases:
        haystack = _case_text(case)
        for category, terms in RED_FLAG_TERMS.items():
            for term in terms:
                if term in haystack:
                    findings.append(
                        {
                            "category": category,
                            "term": term,
                            "paper_id": case.get("paper_id") or "",
                            "issue_type": case.get("issue_type") or "",
                            "issue_cluster_key": case.get("issue_cluster_key") or "",
                            "missing_or_mismatch": _clip(case.get("missing_or_mismatch"), 160),
                        }
                    )
                    break
    return findings


def _render_md(report: Dict[str, Any]) -> str:
    lines: List[str] = []
    lines.append("# P31.6 Entry Gate Audit")
    lines.append("")
    lines.append(f"- dashboard: `{report['inputs'].get('dashboard_json', '')}`")
    lines.append(f"- review issue cases: `{report['inputs'].get('case_json', '')}`")
    if report["inputs"].get("recovery_json"):
        lines.append(f"- recovery cases: `{report['inputs'].get('recovery_json')}`")
    if report["inputs"].get("manual_audit_validation_json"):
        lines.append(f"- manual audit validation: `{report['inputs'].get('manual_audit_validation_json')}`")
    lines.append(f"- machine gate: **{report['machine_gate_status']}**")
    lines.append(f"- manual gate: **{report['manual_gate_status']}**")
    lines.append("")
    lines.append("## Machine Checks")
    lines.append("")
    lines.append("| check | actual | required | status |")
    lines.append("|---|---:|---:|---|")
    for check in report["checks"]:
        lines.append(
            f"| `{check['name']}` | {check['actual']} | {check['required']} | {check['status']} |"
        )
    lines.append("")
    if report["blocking_issues"]:
        lines.append("## Blocking Issues")
        lines.append("")
        for issue in report["blocking_issues"]:
            lines.append(f"- {issue}")
        lines.append("")
    if report.get("manual_audit_summary"):
        lines.append("## Manual Audit Summary")
        lines.append("")
        lines.append("| metric | value |")
        lines.append("|---|---:|")
        for key, value in report["manual_audit_summary"].items():
            if key == "blocking_issues":
                continue
            lines.append(f"| `{key}` | {value} |")
        lines.append("")
    lines.append("## Critique-Origin Clusters For Manual Audit")
    lines.append("")
    clusters = report["critique_origin_clusters"]
    if not clusters:
        lines.append("_No Critique-origin verified clusters found._")
    else:
        lines.append("| paper | type | target | claims | missing/mismatch | inventory anchor |")
        lines.append("|---|---|---|---|---|---|")
        for cluster in clusters:
            lines.append(
                "| {paper} | {itype} | {target} | {claims} | {missing} | {anchor} |".format(
                    paper=cluster.get("paper_id", ""),
                    itype=cluster.get("issue_type", ""),
                    target=_clip(cluster.get("issue_cluster_target"), 80).replace("|", "\\|"),
                    claims=", ".join(cluster.get("claim_ids") or []),
                    missing=_clip(cluster.get("missing_or_mismatch"), 100).replace("|", "\\|"),
                    anchor=_clip(cluster.get("inventory_or_quote_locator"), 80).replace("|", "\\|"),
                )
            )
    lines.append("")
    lines.append("## Critique Selected-Menu Attribution")
    lines.append("")
    selected_details = report.get("critique_selected_verified_cluster_details") or []
    if not selected_details:
        lines.append("_No selected-menu verified cluster attribution details found._")
    else:
        lines.append("| paper | type | target | menu ids | mode |")
        lines.append("|---|---|---|---|---|")
        for item in selected_details:
            lines.append(
                "| {paper} | {itype} | {target} | {menu_ids} | {mode} |".format(
                    paper=item.get("paper_id", ""),
                    itype=item.get("issue_type", ""),
                    target=_clip(item.get("issue_cluster_target"), 80).replace("|", "\\|"),
                    menu_ids=", ".join(item.get("candidate_menu_ids") or []),
                    mode=item.get("attribution_mode", ""),
                )
            )
    lines.append("")
    lines.append("## Selected-Menu Failure Details")
    lines.append("")
    failed_details = report.get("candidate_menu_item_failed_details") or []
    if not failed_details:
        lines.append("_No selected-menu failure details found._")
    else:
        lines.append("| paper | stage | reason | type | target | locator |")
        lines.append("|---|---|---|---|---|---|")
        for item in failed_details[:20]:
            lines.append(
                "| {paper} | {stage} | {reason} | {itype} | {target} | {locator} |".format(
                    paper=item.get("paper_id", ""),
                    stage=item.get("stop_stage", ""),
                    reason=item.get("rejection_reason", ""),
                    itype=item.get("issue_type", ""),
                    target=_clip(item.get("resolved_expected_entity"), 80).replace("|", "\\|"),
                    locator=_clip(item.get("inventory_locator"), 80).replace("|", "\\|"),
                )
            )
    lines.append("")
    lines.append("## Red-Flag Scan")
    lines.append("")
    flags = report["red_flags"]
    if not flags:
        lines.append("_No simple lexical red flags found in verified issue cases._")
    else:
        lines.append("| category | term | paper | type | missing/mismatch |")
        lines.append("|---|---|---|---|---|")
        for flag in flags:
            lines.append(
                "| {category} | `{term}` | {paper} | {itype} | {missing} |".format(
                    category=flag.get("category", ""),
                    term=flag.get("term", ""),
                    paper=flag.get("paper_id", ""),
                    itype=flag.get("issue_type", ""),
                    missing=_clip(flag.get("missing_or_mismatch"), 100).replace("|", "\\|"),
                )
            )
    lines.append("")
    lines.append("## Notes")
    lines.append("")
    for note in report["notes"]:
        lines.append(f"- {note}")
    lines.append("")
    return "\n".join(lines)


def build_report(args: argparse.Namespace) -> Tuple[Dict[str, Any], int]:
    dashboard = _load_json(Path(args.dashboard_json))
    case_table = _load_json(Path(args.case_json))
    recovery_table: Dict[str, Any] = {}
    if args.recovery_json:
        recovery_table = _load_json(Path(args.recovery_json))
    manual_validation: Dict[str, Any] = {}
    if args.manual_audit_validation_json:
        manual_validation = _load_json(Path(args.manual_audit_validation_json))

    metrics = ((dashboard.get("candidate") or {}).get("metrics") or {})
    cases = case_table.get("cases") or []
    if not isinstance(cases, list):
        raise ValueError("case JSON must contain a 'cases' list")

    clusters = _cluster_cases([case for case in cases if isinstance(case, dict)])
    critique_clusters = {
        key: value
        for key, value in clusters.items()
        if any(_is_critique_origin(case) for case in value)
    }
    critique_cluster_records = [
        _cluster_record(key, value)
        for key, value in sorted(critique_clusters.items(), key=lambda item: item[0])
    ]

    checks: List[Dict[str, Any]] = []
    blocking: List[str] = []

    def add_check(name: str, actual: Any, required: Any, ok: bool) -> None:
        status = "PASS" if ok else "FAIL"
        checks.append({"name": name, "actual": actual, "required": required, "status": status})
        if not ok:
            blocking.append(f"{name}: actual {actual}, required {required}")

    add_check("dashboard_protection_passed", bool(dashboard.get("protection_passed")), True, bool(dashboard.get("protection_passed")))
    add_check(
        "critique_payload_verified_cluster_count",
        _as_int(metrics.get("critique_payload_verified_cluster_count")),
        f">= {args.min_critique_clusters}",
        _as_int(metrics.get("critique_payload_verified_cluster_count")) >= args.min_critique_clusters,
    )
    add_check(
        "candidate_menu_item_verified_count",
        _as_int(metrics.get("candidate_menu_item_verified_count")),
        f">= {args.min_candidate_menu_verified}",
        _as_int(metrics.get("candidate_menu_item_verified_count")) >= args.min_candidate_menu_verified,
    )
    add_check(
        "case_table_critique_origin_cluster_count",
        len(critique_clusters),
        f">= {args.min_critique_clusters}",
        len(critique_clusters) >= args.min_critique_clusters,
    )
    case_summary = case_table.get("summary") if isinstance(case_table.get("summary"), dict) else {}
    case_cluster_count = _as_int(case_summary.get("verified_review_issue_cluster_count"), len(clusters))
    case_row_count = _as_int(case_summary.get("verified_review_issue_cases"), len(cases))
    case_duplicate_count = _as_int(case_summary.get("duplicate_review_issue_row_count"), max(0, case_row_count - case_cluster_count))
    dashboard_cluster_count = _as_int(metrics.get("verified_review_issue_cluster_count"))
    dashboard_recomputed_count = _as_int(metrics.get("verified_review_issue_cluster_recomputed_count"), dashboard_cluster_count)
    dashboard_quote_merged_count = _as_int(
        metrics.get("quote_duplicate_merged_verified_review_issue_cluster_count"),
        dashboard_cluster_count,
    )
    origin_cluster_sum = sum(
        _as_int(metrics.get(key))
        for key in (
            "verified_review_issue_cluster_origin_critique_payload_count",
            "verified_review_issue_cluster_origin_deterministic_seed_count",
            "verified_review_issue_cluster_origin_claim_obligation_fallback_count",
            "verified_review_issue_cluster_origin_direct_quote_count",
            "verified_review_issue_cluster_origin_other_candidate_count",
            "verified_review_issue_cluster_origin_other_count",
        )
    )
    add_check(
        "case_table_cluster_count_matches_rows_minus_duplicates",
        case_row_count - case_duplicate_count,
        case_cluster_count,
        case_row_count - case_duplicate_count == case_cluster_count,
    )
    add_check(
        "dashboard_case_cluster_count_match",
        dashboard_cluster_count,
        case_cluster_count,
        dashboard_cluster_count == case_cluster_count,
    )
    add_check(
        "dashboard_recomputed_cluster_count_match",
        dashboard_recomputed_count,
        case_cluster_count,
        dashboard_recomputed_count == case_cluster_count,
    )
    add_check(
        "dashboard_quote_merged_cluster_count_not_above_system",
        dashboard_quote_merged_count,
        f"<= {dashboard_cluster_count}",
        dashboard_quote_merged_count <= dashboard_cluster_count,
    )
    add_check(
        "dashboard_origin_cluster_counts_sum",
        origin_cluster_sum,
        dashboard_cluster_count,
        origin_cluster_sum == dashboard_cluster_count,
    )
    for name in PROTECTION_ZERO_METRICS:
        add_check(name, _as_int(metrics.get(name)), 0, _as_int(metrics.get(name)) == 0)

    flags = _red_flags(cases)
    if args.fail_on_red_flags:
        add_check("lexical_red_flag_count", len(flags), 0, len(flags) == 0)

    manual_summary = manual_validation.get("summary") if isinstance(manual_validation, dict) else {}
    if not isinstance(manual_summary, dict):
        manual_summary = {}
    manual_gate_status = "REQUIRED"
    if manual_validation:
        manual_status = str(manual_summary.get("status") or "").strip().upper()
        manual_gate_status = "PASS" if manual_status == "PASS" else "FAIL"
        add_check("manual_audit_status", manual_status or "MISSING", "PASS", manual_status == "PASS")
        add_check(
            "manual_critique_origin_A_B_clusters",
            _as_int(manual_summary.get("critique_origin_manual_A_B_clusters") or manual_summary.get("manual_A_B_clusters")),
            f">= {args.min_critique_clusters}",
            _as_int(manual_summary.get("critique_origin_manual_A_B_clusters") or manual_summary.get("manual_A_B_clusters")) >= args.min_critique_clusters,
        )
        add_check(
            "manual_D_clusters",
            _as_int(manual_summary.get("manual_D_clusters")),
            0,
            _as_int(manual_summary.get("manual_D_clusters")) == 0,
        )
        add_check(
            "manual_unfilled_clusters",
            _as_int(manual_summary.get("unfilled_clusters")),
            0,
            _as_int(manual_summary.get("unfilled_clusters")) == 0,
        )
    elif args.require_manual_audit:
        add_check("manual_audit_present", False, True, False)

    recovery_summary = recovery_table.get("summary") if isinstance(recovery_table, dict) else {}
    if not isinstance(recovery_summary, dict):
        recovery_summary = {}

    origin_counter = Counter()
    for case in cases:
        if isinstance(case, dict):
            origin_counter[str(case.get("reviewer_candidate_kind") or "unknown")] += 1

    report = {
        "inputs": {
            "dashboard_json": args.dashboard_json,
            "case_json": args.case_json,
            "recovery_json": args.recovery_json or "",
            "manual_audit_validation_json": args.manual_audit_validation_json or "",
        },
        "thresholds": {
            "min_critique_clusters": args.min_critique_clusters,
            "fail_on_red_flags": bool(args.fail_on_red_flags),
            "require_manual_audit": bool(args.require_manual_audit),
        },
        "machine_gate_status": "PASS" if not blocking else "FAIL",
        "manual_gate_status": manual_gate_status,
        "checks": checks,
        "blocking_issues": blocking,
        "headline_metrics": {
            "verified_review_issue_count": _as_int(metrics.get("verified_review_issue_count")),
            "verified_review_issue_cluster_recomputed_count": _as_int(metrics.get("verified_review_issue_cluster_recomputed_count")),
            "quote_duplicate_merged_verified_review_issue_cluster_count": _as_int(metrics.get("quote_duplicate_merged_verified_review_issue_cluster_count")),
            "critique_payload_verified_cluster_count": _as_int(metrics.get("critique_payload_verified_cluster_count")),
            "critique_direct_verified_cluster_count": _as_int(metrics.get("critique_direct_verified_cluster_count")),
            "critique_selected_existing_seed_cluster_count": _as_int(metrics.get("critique_selected_existing_seed_cluster_count")),
            "verified_review_issue_cluster_origin_critique_payload_count": _as_int(metrics.get("verified_review_issue_cluster_origin_critique_payload_count")),
            "mark_contested_commit_count": _as_int(metrics.get("mark_contested_commit_count")),
            "verified_issue_cluster_without_recovery_count": _as_int(metrics.get("verified_issue_cluster_without_recovery_count")),
            "candidate_menu_item_verified_count": _as_int(metrics.get("candidate_menu_item_verified_count")),
            "candidate_menu_item_failed_count": _as_int(metrics.get("candidate_menu_item_failed_count")),
        },
        "critique_selected_verified_cluster_details": metrics.get("critique_selected_verified_cluster_details") or [],
        "candidate_menu_item_failed_details": metrics.get("candidate_menu_item_failed_details") or [],
        "case_summary": case_summary,
        "recovery_summary": recovery_summary,
        "manual_audit_summary": manual_summary,
        "reviewer_candidate_kind_counts": dict(origin_counter),
        "critique_origin_clusters": critique_cluster_records,
        "red_flags": flags,
        "notes": [
            "Machine PASS is not paper-ready approval; manual A/B audit of the listed Critique-origin clusters is still required.",
            "The red-flag scan is lexical only and should be treated as triage, not a verifier.",
            "P32 entry remains blocked if the machine gate fails or manual audit finds external-baseline, retrieval/context, author-limitation, or other false positives.",
        ],
    }
    return report, 0 if not blocking else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dashboard-json", required=True, help="P31.6 dashboard JSON.")
    parser.add_argument("--case-json", required=True, help="Review issue case table JSON.")
    parser.add_argument("--recovery-json", default="", help="Recovery case table JSON.")
    parser.add_argument("--manual-audit-validation-json", default="", help="Validated manual audit report JSON.")
    parser.add_argument("--output-json", default="", help="Write machine-readable report.")
    parser.add_argument("--output-md", default="", help="Write markdown report.")
    parser.add_argument("--min-critique-clusters", type=int, default=3)
    parser.add_argument("--min-candidate-menu-verified", type=int, default=2)
    parser.add_argument("--fail-on-red-flags", action="store_true")
    parser.add_argument("--require-manual-audit", action="store_true")
    args = parser.parse_args()

    try:
        report, exit_code = build_report(args)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if args.output_json:
        Path(args.output_json).write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.output_md:
        Path(args.output_md).write_text(_render_md(report), encoding="utf-8")

    print(f"P31.6 machine gate: {report['machine_gate_status']}")
    print(f"manual gate: {report['manual_gate_status']}")
    for check in report["checks"]:
        print(f"{check['status']}: {check['name']} actual={check['actual']} required={check['required']}")
    if report["blocking_issues"]:
        print("blocking issues:")
        for issue in report["blocking_issues"]:
            print(f"- {issue}")
    print(f"critique-origin clusters listed for manual audit: {len(report['critique_origin_clusters'])}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
