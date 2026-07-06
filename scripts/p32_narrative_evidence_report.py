#!/usr/bin/env python3
"""Build a paper-facing narrative evidence report from P32 clean-run artifacts.

The report is a summarizer only: it consumes already-generated stability,
manual-audit, case-table, and recovery-table artifacts.  It does not rerun
models, rewrite verifier decisions, or relax manual/recovery gates.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set


PASS_LABELS = {"A", "B"}


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


def _norm_token(value: Any) -> str:
    return " ".join(str(value or "").strip().lower().replace("|", " ").split())


def _cluster_key_from_parts(paper_id: Any, issue_type: Any, target: Any) -> str:
    return "|".join((_norm_token(paper_id), _norm_token(issue_type), _norm_token(target)))


def _cluster_key(item: Dict[str, Any]) -> str:
    explicit = str(item.get("issue_cluster_key") or "").strip()
    if explicit:
        parts = explicit.split("|")
        if len(parts) >= 4:
            return _cluster_key_from_parts(parts[0], parts[2], parts[3])
        return _norm_token(explicit)
    target = item.get("cluster_target") or item.get("issue_cluster_target") or item.get("target_entity")
    return _cluster_key_from_parts(item.get("paper_id"), item.get("issue_type"), target)


def _parse_cluster_key(key: str) -> Dict[str, str]:
    parts = str(key or "").split("|")
    return {
        "paper_id": parts[0] if len(parts) > 0 else "",
        "issue_type": parts[1] if len(parts) > 1 else "",
        "cluster_target": parts[2] if len(parts) > 2 else "",
    }


def _manual_clusters(path: Path) -> List[Dict[str, Any]]:
    payload = _load_json(path)
    clusters = payload.get("clusters") or []
    return [cluster for cluster in clusters if isinstance(cluster, dict)]


def _case_rows(path: Path) -> List[Dict[str, Any]]:
    payload = _load_json(path)
    cases = payload.get("cases") or []
    return [case for case in cases if isinstance(case, dict)]


def _recovery_rows(path: Path) -> List[Dict[str, Any]]:
    payload = _load_json(path)
    cases = payload.get("cases") or []
    return [case for case in cases if isinstance(case, dict)]


def _matching_case_rows(rows: Iterable[Dict[str, Any]], key: str) -> List[Dict[str, Any]]:
    return [row for row in rows if _cluster_key(row) == key]


def _evidence_ids(rows: Iterable[Dict[str, Any]]) -> Set[str]:
    ids: Set[str] = set()
    for row in rows:
        evidence_id = str(row.get("evidence_id") or "").strip()
        if evidence_id:
            ids.add(evidence_id)
    return ids


def _recovery_support(rows: Iterable[Dict[str, Any]], evidence_ids: Set[str]) -> List[Dict[str, Any]]:
    support: List[Dict[str, Any]] = []
    seen: Set[str] = set()
    if not evidence_ids:
        return support
    for row in rows:
        if row.get("operation") != "mark_contested":
            continue
        if not bool(row.get("committed")) or not bool(row.get("effective_repair")):
            continue
        row_evidence_ids = {str(value).strip() for value in row.get("supporting_evidence_ids") or [] if str(value).strip()}
        for evidence in row.get("evidence") or []:
            if isinstance(evidence, dict):
                evidence_id = str(evidence.get("evidence_id") or "").strip()
                if evidence_id:
                    row_evidence_ids.add(evidence_id)
        overlap = sorted(evidence_ids & row_evidence_ids)
        if overlap:
            dedupe_key = "|".join(
                (
                    str(row.get("target_type") or ""),
                    str(row.get("target_id") or ""),
                    ",".join(overlap),
                )
            )
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)
            support.append(
                {
                    "target_type": row.get("target_type", ""),
                    "target_id": row.get("target_id", ""),
                    "target_text": row.get("target_text", ""),
                    "evidence_ids": overlap,
                    "narrative_bucket": row.get("narrative_bucket", ""),
                    "operation": row.get("operation", ""),
                }
            )
    return support


def _representative_manual_item(items: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    if not items:
        return {}
    ranked = sorted(
        items,
        key=lambda item: (
            0 if str(item.get("label") or "").upper() == "A" else 1,
            0 if str(item.get("wording_caution") or "").strip() == "" else 1,
            str(item.get("paper_id") or ""),
        ),
    )
    return ranked[0]


def _run_artifact_paths(run: Dict[str, Any]) -> Dict[str, Path]:
    paths = run.get("artifact_paths") or {}
    return {
        "manual_validation": Path(str(paths.get("manual_validation") or "")),
        "case_table": Path(str(paths.get("case_table") or "")),
        "recovery_table": Path(str(paths.get("recovery_table") or "")),
    }


def _build_cluster_evidence(key: str, recurrence_count: int, runs: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    per_run: List[Dict[str, Any]] = []
    all_labels: List[str] = []
    all_issue_types: List[str] = []
    all_targets: List[str] = []
    contested_run_count = 0

    for run in runs:
        if key not in set(run.get("critique_accepted_cluster_keys") or []):
            continue
        paths = _run_artifact_paths(run)
        manual_items = [item for item in _manual_clusters(paths["manual_validation"]) if _cluster_key(item) == key]
        pass_items = [item for item in manual_items if str(item.get("label") or "").upper() in PASS_LABELS]
        representative = _representative_manual_item(pass_items or manual_items)
        case_rows = _matching_case_rows(_case_rows(paths["case_table"]), key)
        evidence_ids = _evidence_ids(case_rows)
        recovery_support = _recovery_support(_recovery_rows(paths["recovery_table"]), evidence_ids)
        if recovery_support:
            contested_run_count += 1

        label = str(representative.get("label") or "").upper()
        if label:
            all_labels.append(label)
        if representative.get("issue_type"):
            all_issue_types.append(str(representative.get("issue_type")))
        target = representative.get("cluster_target") or representative.get("target_entity")
        if target:
            all_targets.append(str(target))

        per_run.append(
            {
                "run_label": run.get("label", ""),
                "manual_label": label,
                "paper_id": representative.get("paper_id", ""),
                "issue_type": representative.get("issue_type", ""),
                "cluster_target": target or "",
                "claim_ids": representative.get("claim_ids") or [],
                "claim_anchor": representative.get("claim_anchor", ""),
                "missing_or_mismatch": representative.get("missing_or_mismatch", ""),
                "inventory_or_quote_locator": representative.get("inventory_or_quote_locator", ""),
                "inventory_or_quote": representative.get("inventory_or_quote", ""),
                "paper_facing_usable": representative.get("paper_facing_usable", ""),
                "wording_caution": representative.get("wording_caution", ""),
                "manual_reason": representative.get("reason", ""),
                "case_evidence_ids": sorted(evidence_ids),
                "case_row_count": len(case_rows),
                "critique_selected_menu_verified": any(bool(row.get("critique_selected_menu_verified")) for row in case_rows),
                "critique_selected_attribution_modes": sorted(
                    {
                        str(row.get("critique_selected_attribution_mode") or "")
                        for row in case_rows
                        if str(row.get("critique_selected_attribution_mode") or "")
                    }
                ),
                "recovery_mark_contested_count": len(recovery_support),
                "recovery_mark_contested_targets": recovery_support,
            }
        )

    parsed = _parse_cluster_key(key)
    issue_type = Counter(all_issue_types).most_common(1)[0][0] if all_issue_types else parsed["issue_type"]
    cluster_target = Counter(all_targets).most_common(1)[0][0] if all_targets else parsed["cluster_target"]
    labels = sorted(set(all_labels))
    return {
        "cluster_key": key,
        "paper_id": parsed["paper_id"],
        "issue_type": issue_type,
        "cluster_target": cluster_target,
        "recurrence_count": recurrence_count,
        "manual_labels": labels,
        "runs_with_contested_recovery": contested_run_count,
        "per_run": per_run,
    }


def build_report(args: argparse.Namespace) -> Dict[str, Any]:
    stability_path = Path(args.stability_json)
    stability = _load_json(stability_path)
    runs = [run for run in stability.get("runs") or [] if isinstance(run, dict) and bool(run.get("clean_included"))]
    recurrence = ((stability.get("recurrence") or {}).get("critique_origin_accepted_clusters") or {})
    recurring = {
        str(key): _as_int(count)
        for key, count in recurrence.items()
        if _as_int(count) >= max(2, _as_int(args.min_recurrence, 2))
    }
    clusters = [_build_cluster_evidence(key, count, runs) for key, count in sorted(recurring.items())]

    missing_recovery = [
        cluster["cluster_key"]
        for cluster in clusters
        if cluster["runs_with_contested_recovery"] < cluster["recurrence_count"]
    ]
    harmful_recovery_total = sum(_as_int(run.get("recovery_harmful_commit_committed"), 0) for run in runs)
    manual_d_total = sum(_as_int(run.get("manual_D_clusters"), 0) for run in runs)
    status = "PASS"
    blocking: List[str] = []
    if stability.get("status") != "PASS":
        blocking.append(f"stability status is {stability.get('status') or 'MISSING'}")
    if len(clusters) < _as_int(args.min_recurring_critique_clusters, 1):
        blocking.append(
            "recurring critique-origin cluster count "
            f"{len(clusters)} < required {args.min_recurring_critique_clusters}"
        )
    if manual_d_total != 0:
        blocking.append(f"manual D clusters total is {manual_d_total}")
    if harmful_recovery_total != 0:
        blocking.append(f"harmful recovery total is {harmful_recovery_total}")
    if args.require_cluster_recovery and missing_recovery:
        blocking.append("clusters missing per-run contested recovery support: " + ", ".join(missing_recovery))
    if blocking:
        status = "INCOMPLETE"

    return {
        "status": status,
        "source_stability_json": str(stability_path),
        "blocking_issues": blocking,
        "runs_included": len(runs),
        "recurring_critique_origin_cluster_count": len(clusters),
        "manual_D_clusters_total": manual_d_total,
        "harmful_recovery_total": harmful_recovery_total,
        "critique_origin_cluster_jaccard_mean": (stability.get("critique_origin_cluster_jaccard_stats") or {}).get("mean"),
        "run_summary": [
            {
                "label": run.get("label", ""),
                "jsonl_rows": run.get("jsonl_rows", 0),
                "machine_gate_status": run.get("machine_gate_status", ""),
                "manual_gate_status": run.get("manual_gate_status", ""),
                "manual_A_B_clusters": run.get("manual_A_B_clusters", 0),
                "manual_D_clusters": run.get("manual_D_clusters", 0),
                "critique_origin_manual_A_B_clusters": run.get("critique_origin_manual_A_B_clusters", 0),
                "mark_contested_commit_count": run.get("mark_contested_commit_count", 0),
                "recovery_harmful_commit_committed": run.get("recovery_harmful_commit_committed", 0),
            }
            for run in runs
        ],
        "recurring_critique_origin_clusters": clusters,
        "narrative_constraints": [
            "This is clean hardneg20 repeat evidence, not a full39/domain-general benchmark claim.",
            "The recurrent items are obligation-grounded verified review issues; they are not all direct quote-grounded negative evidence.",
            "The report makes no accept/reject accuracy claim and does not touch PPO or rollout internals.",
            "The report summarizes existing strict verifier, manual-audit, and recovery artifacts; it does not relax any gate.",
        ],
    }


def _fmt(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)


def _short(value: Any, limit: int = 180) -> str:
    text = " ".join(str(value or "").split())
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "..."


def _render_md(report: Dict[str, Any]) -> str:
    lines: List[str] = []
    lines.append("# P32 Narrative Evidence Report")
    lines.append("")
    lines.append(f"- status: **{report['status']}**")
    lines.append(f"- source stability: `{report['source_stability_json']}`")
    lines.append(f"- included runs: `{report['runs_included']}`")
    lines.append(f"- recurring Critique-origin A/B clusters: `{report['recurring_critique_origin_cluster_count']}`")
    lines.append(f"- Critique-origin cluster Jaccard mean: `{_fmt(report['critique_origin_cluster_jaccard_mean'])}`")
    lines.append(f"- manual D clusters total: `{report['manual_D_clusters_total']}`")
    lines.append(f"- harmful recovery total: `{report['harmful_recovery_total']}`")
    lines.append("")
    if report["blocking_issues"]:
        lines.append("## Blocking Issues")
        lines.append("")
        for issue in report["blocking_issues"]:
            lines.append(f"- {issue}")
        lines.append("")
    lines.append("## Run Evidence")
    lines.append("")
    lines.append("| run | rows | machine | manual | A/B | D | Critique A/B | contested commits | harmful recovery |")
    lines.append("|---|---:|---|---|---:|---:|---:|---:|---:|")
    for run in report["run_summary"]:
        lines.append(
            "| {label} | {rows} | {machine} | {manual} | {ab} | {d} | {crit_ab} | {contested} | {harmful} |".format(
                label=run["label"],
                rows=run["jsonl_rows"],
                machine=run["machine_gate_status"],
                manual=run["manual_gate_status"],
                ab=run["manual_A_B_clusters"],
                d=run["manual_D_clusters"],
                crit_ab=run["critique_origin_manual_A_B_clusters"],
                contested=run["mark_contested_commit_count"],
                harmful=run["recovery_harmful_commit_committed"],
            )
        )
    lines.append("")
    lines.append("## Recurring Critique-Origin Clusters")
    lines.append("")
    for cluster in report["recurring_critique_origin_clusters"]:
        lines.append(f"### `{cluster['cluster_key']}`")
        lines.append("")
        lines.append(f"- issue: `{cluster['issue_type']}` / `{cluster['cluster_target']}`")
        lines.append(f"- recurrence: `{cluster['recurrence_count']}` runs")
        lines.append(f"- manual labels: `{', '.join(cluster['manual_labels'])}`")
        lines.append(
            f"- runs with contested recovery support: `{cluster['runs_with_contested_recovery']}` / `{cluster['recurrence_count']}`"
        )
        lines.append("")
        lines.append("| run | label | claim anchor | missing/mismatch | inventory/quote | recovery | caution |")
        lines.append("|---|---|---|---|---|---:|---|")
        for row in cluster["per_run"]:
            caution = _short(row["wording_caution"], 120)
            lines.append(
                "| {run} | {label} | {claim} | {missing} | {inventory} | {recovery} | {caution} |".format(
                    run=row["run_label"],
                    label=row["manual_label"],
                    claim=_short(row["claim_anchor"], 120).replace("|", "\\|"),
                    missing=_short(row["missing_or_mismatch"], 120).replace("|", "\\|"),
                    inventory=_short(row["inventory_or_quote"], 120).replace("|", "\\|"),
                    recovery=row["recovery_mark_contested_count"],
                    caution=caution.replace("|", "\\|"),
                )
            )
        lines.append("")
    lines.append("## Narrative Constraints")
    lines.append("")
    for note in report["narrative_constraints"]:
        lines.append(f"- {note}")
    return "\n".join(lines) + "\n"


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stability-json", required=True)
    parser.add_argument("--output-json", default="")
    parser.add_argument("--output-md", default="")
    parser.add_argument("--min-recurrence", type=int, default=2)
    parser.add_argument("--min-recurring-critique-clusters", type=int, default=1)
    parser.add_argument("--require-cluster-recovery", action="store_true")
    parser.add_argument("--fail-on-incomplete", action="store_true")
    args = parser.parse_args(argv)

    report = build_report(args)
    if args.output_json:
        Path(args.output_json).write_text(json.dumps(report, indent=2), encoding="utf-8")
    if args.output_md:
        Path(args.output_md).write_text(_render_md(report), encoding="utf-8")
    if not args.output_json and not args.output_md:
        print(json.dumps(report, indent=2))
    if args.fail_on_incomplete and report["status"] != "PASS":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
