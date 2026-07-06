#!/usr/bin/env python3
"""Freeze paper-facing P32 narrative snippets from narrative evidence artifacts.

This script turns the P32 narrative evidence report into bounded manuscript
language: claim wording, result paragraphs, a table-ready cluster summary, and
explicit non-claims.  It is a summarizer only and does not rerun experiments or
change verifier decisions.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence


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


def _fmt(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)


def _short(value: Any, limit: int = 150) -> str:
    text = " ".join(str(value or "").split())
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "..."


def _preferred_run(per_run: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    if not per_run:
        return {}
    ranked = sorted(
        per_run,
        key=lambda row: (
            0 if str(row.get("manual_label") or "").upper() == "A" else 1,
            0 if str(row.get("wording_caution") or "").strip() == "" else 1,
            -_as_int(row.get("recovery_mark_contested_count"), 0),
            str(row.get("run_label") or ""),
        ),
    )
    return ranked[0]


def _cluster_plain_language(issue_type: str, target: str) -> str:
    target_text = str(target or "").replace("_", " ")
    if issue_type == "efficiency_cost_gap":
        return f"missing resource-cost evidence for the {target_text} claim"
    if issue_type == "missing_ablation":
        return f"missing component-isolation ablation for {target_text}"
    if issue_type == "missing_baseline":
        return f"missing same-setting named baseline comparison for {target_text}"
    return f"{issue_type.replace('_', ' ')} around {target_text}"


def _table_row(cluster: Dict[str, Any]) -> Dict[str, Any]:
    preferred = _preferred_run(cluster.get("per_run") or [])
    issue_type = str(cluster.get("issue_type") or "")
    target = str(cluster.get("cluster_target") or "")
    return {
        "paper_id": cluster.get("paper_id", ""),
        "issue_type": issue_type,
        "cluster_target": target,
        "paper_facing_issue": _cluster_plain_language(issue_type, target),
        "manual_labels": ", ".join(cluster.get("manual_labels") or []),
        "recurrence": f"{cluster.get('recurrence_count', 0)}/2",
        "contested_recovery": f"{cluster.get('runs_with_contested_recovery', 0)}/{cluster.get('recurrence_count', 0)}",
        "representative_claim_anchor": preferred.get("claim_anchor", ""),
        "representative_missing_or_mismatch": preferred.get("missing_or_mismatch", ""),
        "wording_caution": preferred.get("wording_caution", ""),
    }


def _headline(report: Dict[str, Any], rows: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    issue_counts: Dict[str, int] = {}
    for row in rows:
        issue_type = str(row.get("issue_type") or "")
        issue_counts[issue_type] = issue_counts.get(issue_type, 0) + 1
    return {
        "runs_included": _as_int(report.get("runs_included")),
        "recurring_critique_origin_clusters": _as_int(report.get("recurring_critique_origin_cluster_count")),
        "critique_origin_cluster_jaccard_mean": report.get("critique_origin_cluster_jaccard_mean"),
        "manual_D_clusters_total": _as_int(report.get("manual_D_clusters_total")),
        "harmful_recovery_total": _as_int(report.get("harmful_recovery_total")),
        "issue_type_counts": issue_counts,
    }


def _snippets(headline: Dict[str, Any]) -> Dict[str, str]:
    runs = headline["runs_included"]
    recurring = headline["recurring_critique_origin_clusters"]
    jaccard = _fmt(headline["critique_origin_cluster_jaccard_mean"])
    manual_d = headline["manual_D_clusters_total"]
    harmful = headline["harmful_recovery_total"]
    return {
        "abstract_result_sentence": (
            f"On two accepted hardneg20 clean runs, DrMAS produces {recurring} recurring "
            "Critique-origin obligation-grounded review issue clusters, all manually judged "
            f"valid or defensible, with manual-D total {manual_d}, harmful recovery total "
            f"{harmful}, and Critique-origin cluster Jaccard {jaccard}."
        ),
        "experiment_result_paragraph": (
            f"We evaluate the current DrMAS pipeline on {runs} accepted hardneg20 clean runs. "
            f"Across these runs, {recurring} Critique-origin verified review issue clusters "
            "recur exactly.  These clusters are obligation-grounded rather than direct "
            "quote-grounded negatives: each is verified through a claim anchor, observed "
            "paper inventory or quote evidence, a concrete missing or mismatched entity, "
            "and counterevidence checks.  Manual audit labels the recurring clusters as "
            f"A/B with zero D labels, while harmful recovery remains {harmful}."
        ),
        "recovery_paragraph": (
            "The recurring clusters also exercise the non-destructive recovery path.  Each "
            "recurring Critique-origin cluster has per-run `mark_contested` support, so the "
            "system can keep a supported claim in the state while exposing a verified issue "
            "as a contested relation.  This supports the ReviewState-maintenance thesis: "
            "recovery is reported as auditable state repair, not as accept/reject correction."
        ),
        "table_caption": (
            "Recurring Critique-origin obligation-grounded review issue clusters across two "
            "accepted hardneg20 clean runs.  The table reports deduplicated cluster-level "
            "evidence, manual A/B labels, and whether the issue connects to contested "
            "recovery in both runs."
        ),
        "limitation_paragraph": (
            "These results should be interpreted as diagnostic evidence for conservative "
            "ReviewState maintenance.  They do not establish broad benchmark performance, "
            "full39 generalization, autonomous accept/reject accuracy, or PPO/RL gains.  "
            "The direct quote-grounded negative lane remains separate from the "
            "obligation-grounded issue path."
        ),
    }


def build_freeze(args: argparse.Namespace) -> Dict[str, Any]:
    source_path = Path(args.narrative_json)
    report = _load_json(source_path)
    clusters = [cluster for cluster in report.get("recurring_critique_origin_clusters") or [] if isinstance(cluster, dict)]
    rows = [_table_row(cluster) for cluster in clusters]
    headline = _headline(report, rows)

    blocking: List[str] = []
    if report.get("status") != "PASS":
        blocking.append(f"narrative evidence status is {report.get('status') or 'MISSING'}")
    if headline["runs_included"] < _as_int(args.min_runs, 2):
        blocking.append(f"included runs {headline['runs_included']} < required {args.min_runs}")
    if headline["recurring_critique_origin_clusters"] < _as_int(args.min_clusters, 5):
        blocking.append(
            "recurring Critique-origin clusters "
            f"{headline['recurring_critique_origin_clusters']} < required {args.min_clusters}"
        )
    if headline["manual_D_clusters_total"] != 0:
        blocking.append(f"manual-D total is {headline['manual_D_clusters_total']}")
    if headline["harmful_recovery_total"] != 0:
        blocking.append(f"harmful recovery total is {headline['harmful_recovery_total']}")
    for cluster in clusters:
        if _as_int(cluster.get("runs_with_contested_recovery")) < _as_int(cluster.get("recurrence_count")):
            blocking.append(f"cluster lacks per-run contested recovery: {cluster.get('cluster_key')}")

    status = "PASS" if not blocking else "INCOMPLETE"
    return {
        "status": status,
        "source_narrative_json": str(source_path),
        "blocking_issues": blocking,
        "paper_thesis": (
            "DrMAS should be framed as a ReviewState-centered verification and recovery "
            "framework for LLM-assisted peer review, not as a free-form review generator, "
            "accept/reject classifier, or PPO-trained policy result."
        ),
        "empirical_scope": "two accepted hardneg20 clean runs",
        "headline_numbers": headline,
        "table_rows": rows,
        "replacement_snippets": _snippets(headline),
        "not_claimed": [
            "full39 generalization",
            "accept/reject accuracy improvement",
            "broad autonomous flaw discovery",
            "PPO or RL performance gain",
            "direct quote-grounded negative recall improvement",
        ],
        "recommended_next_paper_edit": (
            "Replace stale P28/P28.6 result language with the snippets in this artifact, "
            "then move run IDs and regeneration commands to the reproducibility appendix."
        ),
    }


def _render_md(freeze: Dict[str, Any]) -> str:
    lines: List[str] = []
    lines.append("# P32 Paper Narrative Freeze")
    lines.append("")
    lines.append(f"- status: **{freeze['status']}**")
    lines.append(f"- source: `{freeze['source_narrative_json']}`")
    lines.append(f"- empirical scope: {freeze['empirical_scope']}")
    lines.append("")
    lines.append("## Thesis")
    lines.append("")
    lines.append(freeze["paper_thesis"])
    lines.append("")
    if freeze["blocking_issues"]:
        lines.append("## Blocking Issues")
        lines.append("")
        for issue in freeze["blocking_issues"]:
            lines.append(f"- {issue}")
        lines.append("")
    lines.append("## Headline Numbers")
    lines.append("")
    headline = freeze["headline_numbers"]
    lines.append(f"- included clean runs: `{headline['runs_included']}`")
    lines.append(f"- recurring Critique-origin clusters: `{headline['recurring_critique_origin_clusters']}`")
    lines.append(f"- Critique-origin Jaccard mean: `{_fmt(headline['critique_origin_cluster_jaccard_mean'])}`")
    lines.append(f"- manual-D total: `{headline['manual_D_clusters_total']}`")
    lines.append(f"- harmful recovery total: `{headline['harmful_recovery_total']}`")
    lines.append("")
    lines.append("## Replacement Snippets")
    lines.append("")
    for title, key in (
        ("Abstract Result Sentence", "abstract_result_sentence"),
        ("Experiment Result Paragraph", "experiment_result_paragraph"),
        ("Recovery Paragraph", "recovery_paragraph"),
        ("Table Caption", "table_caption"),
        ("Limitation Paragraph", "limitation_paragraph"),
    ):
        lines.append(f"### {title}")
        lines.append("")
        lines.append(freeze["replacement_snippets"][key])
        lines.append("")
    lines.append("## Table-Ready Cluster Summary")
    lines.append("")
    lines.append("| paper | issue type | target | paper-facing issue | labels | recurrence | contested recovery | wording caution |")
    lines.append("|---|---|---|---|---|---:|---:|---|")
    for row in freeze["table_rows"]:
        lines.append(
            "| {paper} | {issue_type} | {target} | {issue} | {labels} | {recurrence} | {recovery} | {caution} |".format(
                paper=str(row["paper_id"]).replace("|", "\\|"),
                issue_type=str(row["issue_type"]).replace("|", "\\|"),
                target=str(row["cluster_target"]).replace("|", "\\|"),
                issue=_short(row["paper_facing_issue"], 120).replace("|", "\\|"),
                labels=str(row["manual_labels"]).replace("|", "\\|"),
                recurrence=row["recurrence"],
                recovery=row["contested_recovery"],
                caution=_short(row["wording_caution"], 120).replace("|", "\\|"),
            )
        )
    lines.append("")
    lines.append("## Not Claimed")
    lines.append("")
    for item in freeze["not_claimed"]:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("## Next Paper Edit")
    lines.append("")
    lines.append(freeze["recommended_next_paper_edit"])
    return "\n".join(lines) + "\n"


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--narrative-json", required=True)
    parser.add_argument("--output-json", default="")
    parser.add_argument("--output-md", default="")
    parser.add_argument("--min-runs", type=int, default=2)
    parser.add_argument("--min-clusters", type=int, default=5)
    parser.add_argument("--fail-on-incomplete", action="store_true")
    args = parser.parse_args(argv)

    freeze = build_freeze(args)
    if args.output_json:
        Path(args.output_json).write_text(json.dumps(freeze, indent=2), encoding="utf-8")
    if args.output_md:
        Path(args.output_md).write_text(_render_md(freeze), encoding="utf-8")
    if not args.output_json and not args.output_md:
        print(json.dumps(freeze, indent=2))
    if args.fail_on_incomplete and freeze["status"] != "PASS":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
