#!/usr/bin/env python3
"""P32 multi-run stability report for clean hardneg20 reproducibility.

This script consumes already-generated P31.6 artifacts.  It does not rerun
models, does not recompute verifier decisions, and deliberately excludes
partial runs from clean-run acceptance.
"""
from __future__ import annotations

import argparse
import json
import statistics
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple


PASS_LABELS = {"A", "B"}
ZERO_PROTECTION_METRICS = (
    "negative_evidence_unlinked_to_flaw",
    "positive_or_neutral_negative_candidate_count",
    "negative_grounding_conflict_count",
    "semantic_negative_without_review_relation_count",
    "state_contamination_count",
    "recovery_harmful_commit_committed",
)


def _load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def _load_json_optional(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    return _load_json(path)


def _line_count(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open("r", encoding="utf-8") as handle:
        return sum(1 for line in handle if line.strip())


def _as_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _normalize_label(value: Any) -> str:
    text = str(value or "").strip().upper()
    if text in {"A+", "A-"}:
        return "A"
    if text in {"B+", "B-"}:
        return "B"
    if text in {"C+", "C-"}:
        return "C"
    if text in {"D+", "D-"}:
        return "D"
    return text


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


def _paper_key(item: Dict[str, Any]) -> str:
    return _norm_token(item.get("paper_id"))


def _target_key(item: Dict[str, Any]) -> str:
    return _norm_token(item.get("cluster_target") or item.get("issue_cluster_target") or item.get("target_entity"))


def _jaccard(left: Set[str], right: Set[str]) -> float:
    if not left and not right:
        return 1.0
    union = left | right
    if not union:
        return 0.0
    return len(left & right) / len(union)


def _pairwise_jaccards(sets: Sequence[Set[str]]) -> List[float]:
    scores: List[float] = []
    for idx, left in enumerate(sets):
        for right in sets[idx + 1 :]:
            scores.append(_jaccard(left, right))
    return scores


def _stats(values: Sequence[int]) -> Dict[str, Any]:
    if not values:
        return {"count": 0, "mean": None, "stdev": None, "min": None, "max": None}
    return {
        "count": len(values),
        "mean": statistics.mean(values),
        "stdev": statistics.stdev(values) if len(values) > 1 else 0.0,
        "min": min(values),
        "max": max(values),
    }


def _float_stats(values: Sequence[float]) -> Dict[str, Any]:
    if not values:
        return {"count": 0, "mean": None, "stdev": None, "min": None, "max": None}
    return {
        "count": len(values),
        "mean": statistics.mean(values),
        "stdev": statistics.stdev(values) if len(values) > 1 else 0.0,
        "min": min(values),
        "max": max(values),
    }


def _parse_run_spec(spec: str) -> Tuple[str, str]:
    if "=" in spec:
        label, run_base = spec.split("=", 1)
        return label.strip(), run_base.strip()
    return spec.strip(), ""


def _artifact_paths(label: str) -> Dict[str, Path]:
    return {
        "entry_gate": Path(f"{label}_ENTRY_GATE_AUDIT.json"),
        "manual_validation": Path(f"{label}_MANUAL_AUDIT_VALIDATION.json"),
        "case_table": Path(f"{label}_REVIEW_ISSUE_CASE_TABLE.json"),
        "recovery_table": Path(f"{label}_RECOVERY_CASE_TABLE.json"),
        "dashboard": Path(f"{label}_HARDNEG20_DASHBOARD.json"),
    }


def _dashboard_jsonl_path(dashboard: Dict[str, Any]) -> str:
    candidate = dashboard.get("candidate") or {}
    path = str(candidate.get("path") or "")
    return path


def _manual_clusters(manual: Dict[str, Any]) -> List[Dict[str, Any]]:
    clusters = manual.get("clusters") or []
    return [cluster for cluster in clusters if isinstance(cluster, dict)]


def _case_clusters(case_table: Dict[str, Any]) -> Set[str]:
    cases = case_table.get("cases") or []
    keys: Set[str] = set()
    for case in cases:
        if isinstance(case, dict):
            key = _cluster_key(case)
            if key:
                keys.add(key)
    return keys


def _is_zero_protection_clean(metrics: Dict[str, Any]) -> bool:
    return all(_as_int(metrics.get(metric), 0) == 0 for metric in ZERO_PROTECTION_METRICS)


def _build_run(label: str, run_base: str, *, min_rows: int) -> Dict[str, Any]:
    paths = _artifact_paths(label)
    entry_gate = _load_json_optional(paths["entry_gate"])
    manual = _load_json_optional(paths["manual_validation"])
    case_table = _load_json_optional(paths["case_table"])
    recovery = _load_json_optional(paths["recovery_table"])
    dashboard = _load_json_optional(paths["dashboard"])

    dashboard_path = _dashboard_jsonl_path(dashboard)
    jsonl_path: Optional[Path]
    if run_base:
        jsonl_path = Path(f"{run_base}.jsonl")
    elif dashboard_path:
        jsonl_path = Path(dashboard_path)
    else:
        jsonl_path = None
    jsonl_rows = _line_count(jsonl_path) if jsonl_path is not None else 0

    metrics = ((dashboard.get("candidate") or {}).get("metrics") or {}) if dashboard else {}
    manual_summary = manual.get("summary") or entry_gate.get("manual_audit_summary") or {}
    recovery_summary = recovery.get("summary") or {}
    clusters = _manual_clusters(manual)
    ab_clusters = [cluster for cluster in clusters if _normalize_label(cluster.get("label")) in PASS_LABELS]
    d_clusters = [cluster for cluster in clusters if _normalize_label(cluster.get("label")) == "D"]
    critique_ab_clusters = [
        cluster
        for cluster in ab_clusters
        if str(cluster.get("origin") or "").strip() == "critique_payload"
    ]
    deterministic_ab_clusters = [
        cluster
        for cluster in ab_clusters
        if str(cluster.get("origin") or "").strip() == "deterministic_seed"
    ]

    blocking: List[str] = []
    if not paths["entry_gate"].exists():
        blocking.append(f"missing entry gate: {paths['entry_gate']}")
    if not paths["manual_validation"].exists():
        blocking.append(f"missing manual validation: {paths['manual_validation']}")
    if jsonl_rows < min_rows:
        blocking.append(f"jsonl rows {jsonl_rows} < required {min_rows}")
    if entry_gate.get("machine_gate_status") != "PASS":
        blocking.append(f"machine gate is {entry_gate.get('machine_gate_status') or 'MISSING'}")
    if entry_gate.get("manual_gate_status") != "PASS":
        blocking.append(f"manual gate is {entry_gate.get('manual_gate_status') or 'MISSING'}")
    if manual_summary.get("status") != "PASS":
        blocking.append(f"manual validation status is {manual_summary.get('status') or 'MISSING'}")
    if not bool((dashboard or {}).get("protection_passed", False)):
        blocking.append("dashboard protection is not PASS")
    if not _is_zero_protection_clean(metrics):
        dirty = [metric for metric in ZERO_PROTECTION_METRICS if _as_int(metrics.get(metric), 0) != 0]
        blocking.append(f"nonzero protection metrics: {', '.join(dirty)}")

    run = {
        "label": label,
        "run_base": run_base or (str(jsonl_path).removesuffix(".jsonl") if jsonl_path is not None else ""),
        "jsonl": str(jsonl_path) if jsonl_path is not None else "",
        "jsonl_rows": jsonl_rows,
        "dashboard_paper_count": _as_int(metrics.get("paper_count"), 0),
        "artifact_paths": {key: str(path) for key, path in paths.items()},
        "machine_gate_status": entry_gate.get("machine_gate_status", ""),
        "manual_gate_status": entry_gate.get("manual_gate_status", ""),
        "manual_status": manual_summary.get("status", ""),
        "protection_passed": bool((dashboard or {}).get("protection_passed", False)),
        "manual_A_B_clusters": _as_int(manual_summary.get("manual_A_B_clusters"), len(ab_clusters)),
        "manual_D_clusters": _as_int(manual_summary.get("manual_D_clusters"), len(d_clusters)),
        "manual_C_clusters": _as_int(manual_summary.get("manual_C_clusters"), 0),
        "unfilled_clusters": _as_int(manual_summary.get("unfilled_clusters"), 0),
        "system_clusters": _as_int(manual_summary.get("system_clusters"), len(clusters)),
        "critique_origin_manual_A_B_clusters": _as_int(
            manual_summary.get("critique_origin_manual_A_B_clusters"),
            len(critique_ab_clusters),
        ),
        "deterministic_seed_manual_A_B_clusters": _as_int(
            manual_summary.get("deterministic_seed_manual_A_B_clusters"),
            len(deterministic_ab_clusters),
        ),
        "critique_direct_verified_cluster_count": _as_int(metrics.get("critique_direct_verified_cluster_count"), 0),
        "candidate_menu_item_verified_count": _as_int(metrics.get("candidate_menu_item_verified_count"), 0),
        "verified_review_issue_cluster_count": _as_int(
            metrics.get("quote_duplicate_merged_verified_review_issue_cluster_count")
            or metrics.get("verified_review_issue_cluster_recomputed_count")
            or metrics.get("verified_review_issue_cluster_count"),
            0,
        ),
        "mark_contested_commit_count": _as_int(metrics.get("mark_contested_commit_count"), 0),
        "verified_issue_cluster_without_recovery_count": _as_int(metrics.get("verified_issue_cluster_without_recovery_count"), 0),
        "recovery_harmful_commit_committed": _as_int(metrics.get("recovery_harmful_commit_committed"), 0),
        "recovery_case_verified_review_issue_repair": _as_int(
            metrics.get("recovery_case_verified_review_issue_repair")
            or recovery_summary.get("bucket::verified_review_issue_repair"),
            0,
        ),
        "evidence_json_fallback_rate_pct": _as_int(metrics.get("evidence_json_fallback_rate_pct"), 0),
        "accepted_cluster_keys": sorted({_cluster_key(cluster) for cluster in ab_clusters if _cluster_key(cluster)}),
        "critique_accepted_cluster_keys": sorted({_cluster_key(cluster) for cluster in critique_ab_clusters if _cluster_key(cluster)}),
        "system_cluster_keys": sorted(_case_clusters(case_table)),
        "accepted_papers": sorted({_paper_key(cluster) for cluster in ab_clusters if _paper_key(cluster)}),
        "accepted_targets": sorted({_target_key(cluster) for cluster in ab_clusters if _target_key(cluster)}),
        "accepted_issue_type_counts": dict(Counter(str(cluster.get("issue_type") or "") for cluster in ab_clusters)),
        "blocking_issues": blocking,
    }
    run["clean_included"] = not blocking
    if run["system_clusters"]:
        run["manual_D_rate"] = run["manual_D_clusters"] / run["system_clusters"]
    else:
        run["manual_D_rate"] = None
    return run


def _recurrence(items: Iterable[Iterable[str]]) -> Dict[str, int]:
    counts: Counter[str] = Counter()
    for item_set in items:
        counts.update(set(item_set))
    return dict(sorted(counts.items(), key=lambda item: (-item[1], item[0])))


def build_report(args: argparse.Namespace) -> Dict[str, Any]:
    runs = [_build_run(*_parse_run_spec(spec), min_rows=args.min_rows) for spec in args.run]
    included = [run for run in runs if run["clean_included"]]
    excluded = [run for run in runs if not run["clean_included"]]

    ab_counts = [run["manual_A_B_clusters"] for run in included]
    d_rates = [run["manual_D_rate"] for run in included if run["manual_D_rate"] is not None]
    accepted_sets = [set(run["accepted_cluster_keys"]) for run in included]
    critique_sets = [set(run["critique_accepted_cluster_keys"]) for run in included]
    accepted_jaccards = _pairwise_jaccards(accepted_sets)
    critique_jaccards = _pairwise_jaccards(critique_sets)

    accepted_recurrence = _recurrence(run["accepted_cluster_keys"] for run in included)
    critique_recurrence = _recurrence(run["critique_accepted_cluster_keys"] for run in included)
    paper_recurrence = _recurrence(run["accepted_papers"] for run in included)
    target_recurrence = _recurrence(run["accepted_targets"] for run in included)

    recurring_ab = {key: count for key, count in accepted_recurrence.items() if count >= 2}
    recurring_critique_ab = {key: count for key, count in critique_recurrence.items() if count >= 2}
    harmful_total = sum(run["recovery_harmful_commit_committed"] for run in included)

    acceptance_checks = [
        {
            "name": "minimum_clean_runs",
            "actual": len(included),
            "required": args.min_runs,
            "status": "PASS" if len(included) >= args.min_runs else "FAIL",
        },
        {
            "name": "all_clean_runs_complete",
            "actual": all(run["jsonl_rows"] >= args.min_rows for run in included) if included else False,
            "required": True,
            "status": "PASS" if included and all(run["jsonl_rows"] >= args.min_rows for run in included) else "FAIL",
        },
        {
            "name": "all_protection_pass",
            "actual": all(run["protection_passed"] for run in included) if included else False,
            "required": True,
            "status": "PASS" if included and all(run["protection_passed"] for run in included) else "FAIL",
        },
        {
            "name": "harmful_recovery_total",
            "actual": harmful_total,
            "required": 0,
            "status": "PASS" if harmful_total == 0 and included else "FAIL",
        },
        {
            "name": "max_manual_D_rate",
            "actual": max(d_rates) if d_rates else None,
            "required": f"<= {args.max_d_rate}",
            "status": "PASS" if d_rates and max(d_rates) <= args.max_d_rate else "FAIL",
        },
        {
            "name": "recurring_A_B_clusters",
            "actual": len(recurring_ab),
            "required": ">= 1",
            "status": "PASS" if len(included) >= 2 and recurring_ab else "FAIL",
        },
        {
            "name": "recurring_critique_origin_A_B_clusters",
            "actual": len(recurring_critique_ab),
            "required": ">= 1",
            "status": "PASS" if len(included) >= 2 and recurring_critique_ab else "FAIL",
        },
    ]

    status = "PASS" if all(check["status"] == "PASS" for check in acceptance_checks) else "INCOMPLETE"
    if excluded and not included:
        status = "BLOCKED"

    return {
        "status": status,
        "thresholds": {
            "min_runs": args.min_runs,
            "min_rows": args.min_rows,
            "max_d_rate": args.max_d_rate,
        },
        "runs_total": len(runs),
        "runs_included": len(included),
        "runs_excluded": len(excluded),
        "acceptance_checks": acceptance_checks,
        "manual_A_B_cluster_count_stats": _stats(ab_counts),
        "manual_D_rate_stats": _float_stats(d_rates),
        "accepted_cluster_jaccard_stats": _float_stats(accepted_jaccards),
        "critique_origin_cluster_jaccard_stats": _float_stats(critique_jaccards),
        "recurrence": {
            "accepted_clusters": accepted_recurrence,
            "critique_origin_accepted_clusters": critique_recurrence,
            "same_paper_issue": paper_recurrence,
            "same_target_entity": target_recurrence,
        },
        "runs": runs,
    }


def _fmt(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)


def _render_md(report: Dict[str, Any]) -> str:
    lines: List[str] = []
    lines.append("# P32 Stability Report")
    lines.append("")
    lines.append(f"- status: **{report['status']}**")
    lines.append(f"- runs included: `{report['runs_included']}` / `{report['runs_total']}`")
    lines.append(f"- runs excluded: `{report['runs_excluded']}`")
    lines.append("")
    lines.append("## Acceptance Checks")
    lines.append("")
    lines.append("| check | actual | required | status |")
    lines.append("|---|---:|---:|---|")
    for check in report["acceptance_checks"]:
        lines.append(f"| `{check['name']}` | {_fmt(check['actual'])} | {check['required']} | {check['status']} |")
    lines.append("")
    lines.append("## Run Summary")
    lines.append("")
    lines.append("| label | rows | included | machine | manual | A/B | D | D rate | Critique A/B | harmful recovery | blockers |")
    lines.append("|---|---:|---|---|---|---:|---:|---:|---:|---:|---|")
    for run in report["runs"]:
        blockers = "; ".join(run["blocking_issues"])
        lines.append(
            "| {label} | {rows} | {included} | {machine} | {manual} | {ab} | {d} | {d_rate} | {crit_ab} | {harmful} | {blockers} |".format(
                label=run["label"],
                rows=run["jsonl_rows"],
                included="yes" if run["clean_included"] else "no",
                machine=run["machine_gate_status"],
                manual=run["manual_gate_status"],
                ab=run["manual_A_B_clusters"],
                d=run["manual_D_clusters"],
                d_rate=_fmt(run["manual_D_rate"]),
                crit_ab=run["critique_origin_manual_A_B_clusters"],
                harmful=run["recovery_harmful_commit_committed"],
                blockers=blockers.replace("|", "\\|"),
            )
        )
    lines.append("")
    lines.append("## Stability Metrics")
    lines.append("")
    lines.append("| metric | count | mean | stdev | min | max |")
    lines.append("|---|---:|---:|---:|---:|---:|")
    for key in (
        "manual_A_B_cluster_count_stats",
        "manual_D_rate_stats",
        "accepted_cluster_jaccard_stats",
        "critique_origin_cluster_jaccard_stats",
    ):
        stats = report[key]
        lines.append(
            f"| `{key}` | {stats['count']} | {_fmt(stats['mean'])} | {_fmt(stats['stdev'])} | {_fmt(stats['min'])} | {_fmt(stats['max'])} |"
        )
    lines.append("")
    lines.append("## Recurrence")
    lines.append("")
    for title, key in (
        ("Accepted Clusters", "accepted_clusters"),
        ("Critique-Origin Accepted Clusters", "critique_origin_accepted_clusters"),
        ("Same-Paper Issue Recurrence", "same_paper_issue"),
        ("Same-Target Entity Recurrence", "same_target_entity"),
    ):
        lines.append(f"### {title}")
        lines.append("")
        items = report["recurrence"][key]
        if not items:
            lines.append("_No included-run recurrence data._")
            lines.append("")
            continue
        lines.append("| item | runs |")
        lines.append("|---|---:|")
        for item, count in list(items.items())[:20]:
            lines.append(f"| `{item}` | {count} |")
        lines.append("")
    lines.append("## Notes")
    lines.append("")
    lines.append("- Partial runs are excluded from clean-run acceptance even when they contain useful diagnostic rows.")
    lines.append("- This report summarizes existing artifacts only; it does not relax verifier, manual-audit, or recovery gates.")
    return "\n".join(lines) + "\n"


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--run",
        action="append",
        required=True,
        help="Artifact label, or LABEL=RUN_BASE to bind the label to a raw jsonl run.",
    )
    parser.add_argument("--output-json", default="")
    parser.add_argument("--output-md", default="")
    parser.add_argument("--min-runs", type=int, default=3)
    parser.add_argument("--min-rows", type=int, default=20)
    parser.add_argument("--max-d-rate", type=float, default=0.25)
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
