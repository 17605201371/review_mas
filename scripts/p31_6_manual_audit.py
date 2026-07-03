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
from collections import Counter
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


def _cluster_template(cluster: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "label": "TODO",
        "paper_id": cluster.get("paper_id") or "",
        "issue_type": cluster.get("issue_type") or "",
        "cluster_target": cluster.get("issue_cluster_target") or "",
        "issue_cluster_key": cluster.get("issue_cluster_key") or "",
        "origin": cluster.get("discovery_origin") or cluster.get("reviewer_candidate_kind") or "",
        "claim_ids": cluster.get("claim_ids") or [],
        "missing_or_mismatch": cluster.get("missing_or_mismatch") or "",
        "claim_anchor": cluster.get("claim_anchor") or "",
        "inventory_or_quote_locator": cluster.get("inventory_or_quote_locator") or "",
        "inventory_or_quote": cluster.get("inventory_or_quote") or "",
        "manual_decision": "TODO",
        "false_positive_categories": [],
        "wording_caution": "",
        "reason": "TODO",
    }


def _build_template(args: argparse.Namespace) -> Dict[str, Any]:
    entry_gate = _load_json(Path(args.entry_gate_json))
    clusters = entry_gate.get("critique_origin_clusters") or []
    if not isinstance(clusters, list):
        raise ValueError("entry-gate JSON must contain a critique_origin_clusters list")
    return {
        "run_label": args.run_label or Path(args.entry_gate_json).stem.replace("_ENTRY_GATE_AUDIT", ""),
        "audit_date": args.audit_date,
        "source_entry_gate": args.entry_gate_json,
        "audit_boundary": (
            "Manual audit of Critique-origin verified review-issue clusters. "
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
            "manual_D_clusters_allowed": 0,
            "unfilled_clusters_allowed": 0,
        },
        "summary": {
            "critique_origin_clusters": len(clusters),
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
        reason = str(cluster.get("reason") or "").strip()
        decision = str(cluster.get("manual_decision") or "").strip()
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
        if cluster_unfilled:
            counts["unfilled"] += 1
        false_categories = cluster.get("false_positive_categories") or []
        if label == "D" and not false_categories:
            findings.append(
                f"{cluster.get('paper_id','')} / {cluster.get('cluster_target','')}: D label needs false_positive_categories"
            )
        normalized_clusters.append({**cluster, "label": label})

    manual_ab = counts["A"] + counts["B"]
    status = "PASS"
    blocking: List[str] = []
    if counts["unfilled"] > 0:
        status = "FAIL"
        blocking.append(f"unfilled_clusters/checks = {counts['unfilled']}")
    if not args.allow_d and counts["D"] > 0:
        status = "FAIL"
        blocking.append(f"manual_D_clusters = {counts['D']}")
    if manual_ab < args.min_critique_ab_clusters:
        status = "FAIL"
        blocking.append(
            f"manual_A_B_clusters = {manual_ab}, required >= {args.min_critique_ab_clusters}"
        )

    summary = {
        "critique_origin_clusters": len(clusters),
        "manual_A_clusters": counts["A"],
        "manual_B_clusters": counts["B"],
        "manual_A_B_clusters": manual_ab,
        "manual_C_clusters": counts["C"],
        "manual_D_clusters": counts["D"],
        "manual_MERGE_clusters": counts["MERGE"],
        "unfilled_clusters": counts["unfilled"],
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
        lines.append(f"claim_ids = {', '.join(cluster.get('claim_ids') or [])}")
        lines.append(f"missing = {cluster.get('missing_or_mismatch','')}")
        lines.append(f"claim_anchor = {_clip(cluster.get('claim_anchor'), 320)}")
        lines.append(f"inventory_locator = {cluster.get('inventory_or_quote_locator','')}")
        lines.append(f"inventory = {_clip(cluster.get('inventory_or_quote'), 320)}")
        lines.append(f"origin = {cluster.get('origin','')}")
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
    template.add_argument("--entry-gate-json", required=True)
    template.add_argument("--output-json", required=True)
    template.add_argument("--output-md", default="")
    template.add_argument("--run-label", default="")
    template.add_argument("--audit-date", default="")
    template.add_argument("--min-critique-ab-clusters", type=int, default=3)

    validate = sub.add_parser("validate", help="Validate a filled manual audit JSON.")
    validate.add_argument("--audit-json", required=True)
    validate.add_argument("--output-json", default="")
    validate.add_argument("--output-md", default="")
    validate.add_argument("--min-critique-ab-clusters", type=int, default=3)
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
