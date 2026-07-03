#!/usr/bin/env python3
"""Generate and validate P31.6 manual A/B audit files.

The P31.6 machine gate can only prove that Critique-origin clusters exist and
that protection lines pass.  P32 entry still needs a human audit of those
clusters.  This helper keeps that audit structured and reproducible.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Tuple


VALID_LABELS = {"A", "B", "C", "D", "MERGE"}
PASS_LABELS = {"A", "B"}
TODO_VALUES = {"", "TODO", "TBD", "UNFILLED"}


def _load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def _clip(value: Any, limit: int = 180) -> str:
    text = " ".join(str(value or "").split())
    return text if len(text) <= limit else text[: limit - 3] + "..."


def _cluster_origin(cases: List[Dict[str, Any]]) -> str:
    kinds = {str(case.get("reviewer_candidate_kind") or "") for case in cases}
    origins = {str(case.get("discovery_origin") or "") for case in cases}
    sources = {str(case.get("source_of_expectation") or "") for case in cases}
    if "direct_quote" in kinds or "direct_quote" in sources:
        return "quote_grounded"
    if "critique_payload_candidate" in kinds or any(origin.startswith("critique_payload") for origin in origins):
        return "critique_payload"
    if "claim_obligation_fallback" in kinds or "claim_obligation" in sources:
        return "claim_obligation"
    if "deterministic_reviewer_seed" in kinds:
        return "deterministic_seed"
    return next(iter(kinds - {""}), "") or next(iter(origins - {""}), "") or "unknown"


def _clusters_from_case_table(case_table: Dict[str, Any], *, critique_origin_only: bool = False) -> List[Dict[str, Any]]:
    cases = case_table.get("cases") or []
    if not isinstance(cases, list):
        raise ValueError("case JSON must contain a cases list")
    grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for case in cases:
        if not isinstance(case, dict):
            continue
        key = str(case.get("issue_cluster_key") or case.get("issue_cluster_id") or case.get("evidence_id") or "")
        if key:
            grouped[key].append(case)
    clusters: List[Dict[str, Any]] = []
    for key, cluster_cases in sorted(grouped.items(), key=lambda item: item[0]):
        first = cluster_cases[0]
        origin = _cluster_origin(cluster_cases)
        if critique_origin_only and origin != "critique_payload":
            continue
        claim_ids = sorted({str(case.get("claim_id") or "") for case in cluster_cases if str(case.get("claim_id") or "")})
        clusters.append(
            {
                "issue_cluster_key": key,
                "paper_id": first.get("paper_id") or "",
                "issue_type": first.get("issue_type") or "",
                "issue_cluster_target": first.get("issue_cluster_target") or "",
                "case_count": len(cluster_cases),
                "claim_ids": claim_ids,
                "missing_or_mismatch": first.get("missing_or_mismatch") or "",
                "claim_anchor": first.get("claim_anchor") or "",
                "inventory_or_quote_locator": first.get("inventory_or_quote_locator") or "",
                "inventory_or_quote": first.get("inventory_or_quote") or "",
                "review_issue_slot": first.get("review_issue_slot") or "",
                "discovery_origin": first.get("discovery_origin") or "",
                "reviewer_candidate_kind": first.get("reviewer_candidate_kind") or "",
                "origin": origin,
            }
        )
    return clusters


def _cluster_template(cluster: Dict[str, Any]) -> Dict[str, Any]:
    origin = cluster.get("origin") or cluster.get("discovery_origin") or cluster.get("reviewer_candidate_kind") or ""
    return {
        "label": "TODO",
        "paper_id": cluster.get("paper_id") or "",
        "issue_type": cluster.get("issue_type") or "",
        "target_entity": cluster.get("issue_cluster_target") or cluster.get("target_entity") or "",
        "cluster_target": cluster.get("issue_cluster_target") or cluster.get("target_entity") or "",
        "issue_cluster_key": cluster.get("issue_cluster_key") or "",
        "origin": origin,
        "claim_ids": cluster.get("claim_ids") or [],
        "missing_or_mismatch": cluster.get("missing_or_mismatch") or "",
        "claim_anchor": cluster.get("claim_anchor") or "",
        "inventory_or_quote_locator": cluster.get("inventory_or_quote_locator") or "",
        "inventory_or_quote": cluster.get("inventory_or_quote") or "",
        "manual_decision": "TODO",
        "manual_merge_target": "",
        "raw_paper_evidence_checked": "TODO",
        "counterevidence_checked": "TODO",
        "paper_facing_usable": "TODO",
        "false_positive_categories": [],
        "wording_caution": "",
        "downgrade_reason": "",
        "reason": "TODO",
    }


def _build_template(args: argparse.Namespace) -> Dict[str, Any]:
    source = ""
    audit_scope = "Critique-origin verified review-issue clusters"
    if getattr(args, "case_json", ""):
        case_table = _load_json(Path(args.case_json))
        clusters = _clusters_from_case_table(
            case_table,
            critique_origin_only=bool(getattr(args, "critique_origin_only", False)),
        )
        source = args.case_json
        if getattr(args, "critique_origin_only", False):
            audit_scope = "Critique-origin verified review-issue clusters"
        else:
            audit_scope = "All verifier-passing system review-issue clusters"
    else:
        entry_gate = _load_json(Path(args.entry_gate_json))
        clusters = entry_gate.get("critique_origin_clusters") or []
        clusters = [
            {**cluster, "origin": "critique_payload"}
            if isinstance(cluster, dict) and not cluster.get("origin")
            else cluster
            for cluster in clusters
        ]
        source = args.entry_gate_json
    if not isinstance(clusters, list):
        raise ValueError("manual audit source must contain a clusters list")
    return {
        "run_label": args.run_label or Path(source).stem.replace("_ENTRY_GATE_AUDIT", "").replace("_REVIEW_ISSUE_CASE_TABLE", ""),
        "audit_date": args.audit_date,
        "source_entry_gate": args.entry_gate_json or "",
        "source_case_table": getattr(args, "case_json", "") or "",
        "audit_boundary": (
            f"Manual audit of {audit_scope}. "
            "Labels are cluster-level paper-readiness judgments from case-table evidence; "
            "final paper claims should still be spot-checked against the original paper text."
        ),
        "rubric": {
            "A": "clear review-worthy issue with strong claim/inventory/missing relation",
            "B": "defensible review concern; usable with careful wording",
            "C": "weak or over-specific concern; keep only as diagnosis/pending",
            "D": "false positive / contradicted by paper text",
            "MERGE": "duplicate of another audited cluster; do not count separately",
        },
        "thresholds": {
            "min_critique_origin_A_B_clusters": args.min_critique_ab_clusters,
            "min_all_A_B_clusters": getattr(args, "min_all_ab_clusters", 0),
            "manual_D_clusters_allowed": 0,
            "unfilled_clusters_allowed": 0,
        },
        "summary": {
            "system_clusters": len(clusters),
            "critique_origin_clusters": sum(1 for cluster in clusters if _cluster_template(cluster).get("origin") == "critique_payload"),
            "manual_A_clusters": 0,
            "manual_B_clusters": 0,
            "manual_A_B_clusters": 0,
            "manual_C_clusters": 0,
            "manual_D_clusters": 0,
            "manual_MERGE_clusters": 0,
            "unfilled_clusters": len(clusters),
            "status": "TODO",
        },
        "clusters": [_cluster_template(cluster) for cluster in clusters],
    }


def _normalize_label(value: Any) -> str:
    text = str(value or "").strip().upper()
    if text in {"A-", "A+"}:
        return "A"
    if text in {"B-", "B+"}:
        return "B"
    if text in {"C-", "C+"}:
        return "C"
    if text in {"D-", "D+"}:
        return "D"
    return text


def _is_todo(value: Any) -> bool:
    return str(value or "").strip().upper() in TODO_VALUES


def _validate_audit(args: argparse.Namespace) -> Tuple[Dict[str, Any], int]:
    audit = _load_json(Path(args.audit_json))
    clusters = audit.get("clusters") or []
    if not isinstance(clusters, list):
        raise ValueError("manual audit JSON must contain a clusters list")

    counts: Counter[str] = Counter()
    findings: List[str] = []
    normalized_clusters: List[Dict[str, Any]] = []

    for idx, cluster in enumerate(clusters, start=1):
        if not isinstance(cluster, dict):
            findings.append(f"cluster #{idx} is not an object")
            counts["unfilled"] += 1
            continue
        label = _normalize_label(cluster.get("label"))
        reason = str(cluster.get("reason") or cluster.get("downgrade_reason") or "").strip()
        decision = str(cluster.get("manual_decision") or "").strip()
        raw_checked = str(cluster.get("raw_paper_evidence_checked") or "").strip()
        counter_checked = str(cluster.get("counterevidence_checked") or "").strip()
        paper_usable = str(cluster.get("paper_facing_usable") or "").strip()
        cluster_unfilled = False
        if label not in VALID_LABELS:
            cluster_unfilled = True
            findings.append(
                f"{cluster.get('paper_id','')} / {cluster.get('cluster_target','')}: invalid or unfilled label `{cluster.get('label')}`"
            )
        else:
            counts[label] += 1
        if _is_todo(reason):
            cluster_unfilled = True
            findings.append(
                f"{cluster.get('paper_id','')} / {cluster.get('cluster_target','')}: reason is unfilled"
            )
        if _is_todo(decision):
            cluster_unfilled = True
            findings.append(
                f"{cluster.get('paper_id','')} / {cluster.get('cluster_target','')}: manual_decision is unfilled"
            )
        for field_name, field_value in (
            ("raw_paper_evidence_checked", raw_checked),
            ("counterevidence_checked", counter_checked),
            ("paper_facing_usable", paper_usable),
        ):
            if _is_todo(field_value):
                cluster_unfilled = True
                findings.append(
                    f"{cluster.get('paper_id','')} / {cluster.get('cluster_target','')}: {field_name} is unfilled"
                )
        if cluster_unfilled:
            counts["unfilled"] += 1
        false_categories = cluster.get("false_positive_categories") or []
        if label == "D" and not false_categories:
            findings.append(
                f"{cluster.get('paper_id','')} / {cluster.get('cluster_target','')}: D label needs false_positive_categories"
            )
        normalized_clusters.append({**cluster, "label": label})

    manual_ab = counts["A"] + counts["B"]
    normalized_origin_counts: Counter[str] = Counter()
    origin_ab_counts: Counter[str] = Counter()
    origin_d_counts: Counter[str] = Counter()
    for cluster in normalized_clusters:
        origin = str(cluster.get("origin") or "unknown")
        label = str(cluster.get("label") or "")
        normalized_origin_counts[origin] += 1
        if label in PASS_LABELS:
            origin_ab_counts[origin] += 1
        if label == "D":
            origin_d_counts[origin] += 1
    status = "PASS"
    blocking: List[str] = []
    if counts["unfilled"] > 0:
        status = "FAIL"
        blocking.append(f"unfilled_clusters/checks = {counts['unfilled']}")
    if not args.allow_d and counts["D"] > 0:
        status = "FAIL"
        blocking.append(f"manual_D_clusters = {counts['D']}")
    critique_ab = origin_ab_counts.get("critique_payload", 0)
    if critique_ab < args.min_critique_ab_clusters:
        status = "FAIL"
        blocking.append(
            f"critique_origin_manual_A_B_clusters = {critique_ab}, required >= {args.min_critique_ab_clusters}"
        )
    min_all = int(getattr(args, "min_all_ab_clusters", 0) or 0)
    if min_all and manual_ab < min_all:
        status = "FAIL"
        blocking.append(f"manual_A_B_clusters = {manual_ab}, required >= {min_all}")

    summary = {
        "system_clusters": len(clusters),
        "critique_origin_clusters": normalized_origin_counts.get("critique_payload", 0),
        "manual_A_clusters": counts["A"],
        "manual_B_clusters": counts["B"],
        "manual_A_B_clusters": manual_ab,
        "manual_C_clusters": counts["C"],
        "manual_D_clusters": counts["D"],
        "manual_MERGE_clusters": counts["MERGE"],
        "unfilled_clusters": counts["unfilled"],
        "manual_A_B_clusters_by_origin": dict(sorted(origin_ab_counts.items())),
        "manual_D_clusters_by_origin": dict(sorted(origin_d_counts.items())),
        "cluster_count_by_origin": dict(sorted(normalized_origin_counts.items())),
        "critique_origin_manual_A_B_clusters": origin_ab_counts.get("critique_payload", 0),
        "deterministic_seed_manual_A_B_clusters": origin_ab_counts.get("deterministic_seed", 0),
        "critique_origin_D_clusters": origin_d_counts.get("critique_payload", 0),
        "status": status,
        "blocking_issues": blocking,
    }
    report = {
        "run_label": audit.get("run_label") or "",
        "source_entry_gate": audit.get("source_entry_gate") or "",
        "audit_boundary": audit.get("audit_boundary") or "",
        "thresholds": {
            "min_critique_origin_A_B_clusters": args.min_critique_ab_clusters,
            "manual_D_clusters_allowed": "any" if args.allow_d else 0,
            "unfilled_clusters_allowed": 0,
        },
        "summary": summary,
        "findings": findings,
        "clusters": normalized_clusters,
    }
    return report, 0 if status == "PASS" else 1


def _render_template_md(audit: Dict[str, Any]) -> str:
    lines: List[str] = []
    lines.append(f"# P31.6 Manual Critique-Origin Audit: {audit.get('run_label','')}")
    lines.append("")
    lines.append(f"- source entry gate: `{audit.get('source_entry_gate','')}`")
    if audit.get("source_case_table"):
        lines.append(f"- source case table: `{audit.get('source_case_table','')}`")
    lines.append(f"- audit date: `{audit.get('audit_date','')}`")
    lines.append(f"- status: **{audit.get('summary',{}).get('status','TODO')}**")
    lines.append("")
    lines.append("## Rubric")
    lines.append("")
    for label, description in (audit.get("rubric") or {}).items():
        lines.append(f"- `{label}`: {description}")
    lines.append("")
    lines.append("## Clusters To Audit")
    lines.append("")
    for idx, cluster in enumerate(audit.get("clusters") or [], start=1):
        lines.append(f"### {idx}. {cluster.get('paper_id','')} / {cluster.get('cluster_target','')}")
        lines.append("")
        lines.append("```text")
        lines.append(f"issue_type = {cluster.get('issue_type','')}")
        lines.append(f"origin = {cluster.get('origin','')}")
        lines.append(f"claim_ids = {', '.join(cluster.get('claim_ids') or [])}")
        lines.append(f"missing = {cluster.get('missing_or_mismatch','')}")
        lines.append(f"claim_anchor = {_clip(cluster.get('claim_anchor'), 320)}")
        lines.append(f"inventory_locator = {cluster.get('inventory_or_quote_locator','')}")
        lines.append(f"inventory = {_clip(cluster.get('inventory_or_quote'), 320)}")
        lines.append("```")
        lines.append("")
        lines.append("Manual label: **TODO**")
        lines.append("")
        lines.append("Decision: TODO")
        lines.append("")
        lines.append("Rationale:")
        lines.append("")
        lines.append("- TODO")
        lines.append("")
    return "\n".join(lines)


def _render_validation_md(report: Dict[str, Any]) -> str:
    summary = report.get("summary") or {}
    lines: List[str] = []
    lines.append("# P31.6 Manual Audit Validation")
    lines.append("")
    lines.append(f"- run: `{report.get('run_label','')}`")
    lines.append(f"- status: **{summary.get('status','')}**")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append("| metric | value |")
    lines.append("|---|---:|")
    for key in (
        "critique_origin_clusters",
        "manual_A_clusters",
        "manual_B_clusters",
        "manual_A_B_clusters",
        "manual_C_clusters",
        "manual_D_clusters",
        "manual_MERGE_clusters",
        "unfilled_clusters",
        "critique_origin_manual_A_B_clusters",
        "deterministic_seed_manual_A_B_clusters",
        "critique_origin_D_clusters",
    ):
        lines.append(f"| `{key}` | {summary.get(key, 0)} |")
    lines.append("")
    if summary.get("blocking_issues"):
        lines.append("## Blocking Issues")
        lines.append("")
        for item in summary.get("blocking_issues") or []:
            lines.append(f"- {item}")
        lines.append("")
    if report.get("findings"):
        lines.append("## Findings")
        lines.append("")
        for finding in report["findings"]:
            lines.append(f"- {finding}")
        lines.append("")
    lines.append("## Cluster Labels")
    lines.append("")
    clusters = report.get("clusters") or []
    if not clusters:
        lines.append("_No clusters._")
    else:
        lines.append("| label | paper | type | target | decision | reason |")
        lines.append("|---|---|---|---|---|---|")
        for cluster in clusters:
            lines.append(
                "| {label} | {paper} | {itype} | {target} | {decision} | {reason} |".format(
                    label=str(cluster.get("label") or "").replace("|", "\\|"),
                    paper=str(cluster.get("paper_id") or "").replace("|", "\\|"),
                    itype=str(cluster.get("issue_type") or "").replace("|", "\\|"),
                    target=_clip(cluster.get("cluster_target"), 80).replace("|", "\\|"),
                    decision=_clip(cluster.get("manual_decision"), 80).replace("|", "\\|"),
                    reason=_clip(cluster.get("reason"), 160).replace("|", "\\|"),
                )
            )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    template = sub.add_parser("template", help="Generate a manual audit template from an entry-gate JSON.")
    template.add_argument("--entry-gate-json", default="")
    template.add_argument("--case-json", default="", help="Review issue case-table JSON. When set, audit all system clusters by default.")
    template.add_argument("--critique-origin-only", action="store_true", help="With --case-json, audit only Critique-origin clusters.")
    template.add_argument("--output-json", required=True)
    template.add_argument("--output-md", default="")
    template.add_argument("--run-label", default="")
    template.add_argument("--audit-date", default="")
    template.add_argument("--min-critique-ab-clusters", type=int, default=3)
    template.add_argument("--min-all-ab-clusters", type=int, default=0)

    validate = sub.add_parser("validate", help="Validate a filled manual audit JSON.")
    validate.add_argument("--audit-json", required=True)
    validate.add_argument("--output-json", default="")
    validate.add_argument("--output-md", default="")
    validate.add_argument("--min-critique-ab-clusters", type=int, default=3)
    validate.add_argument("--min-all-ab-clusters", type=int, default=0)
    validate.add_argument("--allow-d", action="store_true", help="Do not fail when D clusters are present.")

    args = parser.parse_args()
    try:
        if args.command == "template":
            audit = _build_template(args)
            Path(args.output_json).write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            if args.output_md:
                Path(args.output_md).write_text(_render_template_md(audit), encoding="utf-8")
            print(f"manual audit template clusters: {len(audit.get('clusters') or [])}")
            return 0
        report, exit_code = _validate_audit(args)
        if args.output_json:
            Path(args.output_json).write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        if args.output_md:
            Path(args.output_md).write_text(_render_validation_md(report), encoding="utf-8")
        print(f"manual audit validation: {report['summary']['status']}")
        for key, value in report["summary"].items():
            if key != "blocking_issues":
                print(f"{key}={value}")
        if report["summary"].get("blocking_issues"):
            print("blocking issues:")
            for issue in report["summary"]["blocking_issues"]:
                print(f"- {issue}")
        return exit_code
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
