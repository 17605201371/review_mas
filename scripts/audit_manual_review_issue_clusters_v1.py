#!/usr/bin/env python3
"""Manual cluster-level audit for P29 review-issue outputs.

This script intentionally lives outside the verifier.  It records human audit
labels for paper-facing reporting and keeps verifier-passing counts separate
from manually defensible issue counts.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List


P29_20260701_AUDIT: Dict[str, Dict[str, str]] = {
    "review-issue-cluster-wnxljjievj-obligation-grounded-review-issue-missing-ablation-planning-module": {
        "manual_label": "C",
        "reason": "Planning Module is a real component, but the verified claim is about the contrastive mechanism and the paper already contains contrastive ablations; the target is weakly aligned.",
    },
    "review-issue-cluster-9zebk3e9bx-obligation-grounded-review-issue-missing-ablation-comparing-occupancy-prediction-alternative-pretext-tasks-ma": {
        "manual_label": "B",
        "reason": "Occupancy prediction is a claimed pretraining objective and alternative pretext comparisons are review-worthy; Table 6 may partially cover this, so it is defensible rather than strong.",
    },
    "review-issue-cluster-ge6iywjtsv-obligation-grounded-review-issue-reproducibility-gap-implementation-reproducibility-details": {
        "manual_label": "B",
        "reason": "The GrCN method is central and the visible paper text lacks common reproducibility details such as learning rate, seed, epochs, or implementation configuration.",
    },
    "review-issue-cluster-wpxq5n8ylb-obligation-grounded-review-issue-missing-ablation-recurrent-draft-model": {
        "manual_label": "A",
        "reason": "The recurrent draft model is explicitly named as one of three performance-driving mechanisms; paper text shows other ablations but not an isolated RNN draft-model ablation.",
    },
    "review-issue-cluster-nnexmnithw-obligation-grounded-review-issue-missing-ablation-acceptance-prediction-head": {
        "manual_label": "A",
        "reason": "The acceptance prediction head is a named core mechanism for adaptive candidate length and no ablation evidence was found in the visible full text.",
    },
    "review-issue-cluster-a6sntiisgg-obligation-grounded-review-issue-missing-ablation-global-encoder": {
        "manual_label": "A",
        "reason": "The global encoder is part of the paper's named local-global contribution; the visible ablation section focuses on losses rather than isolating the global branch.",
    },
    "review-issue-cluster-qagwfiiy4p-obligation-grounded-review-issue-reproducibility-gap-implementation-reproducibility-details": {
        "manual_label": "B",
        "reason": "The PSRD/PST method is central and the visible text gives little training configuration, seed, or hyperparameter detail; this is a valid reproducibility concern but somewhat generic.",
    },
    "review-issue-cluster-tpaj63ax4y-obligation-grounded-review-issue-missing-baseline-lavt": {
        "manual_label": "D",
        "reason": "The full paper table already includes LAVT as a fully supervised reference; the issue confuses cross-setting comparison with a missing same-setting baseline.",
    },
    "review-issue-cluster-mhv6wcbb0z-obligation-grounded-review-issue-missing-ablation-generalized-noise-regularization": {
        "manual_label": "A",
        "reason": "Generalized noise regularization is the paper-named central mechanism for NR-DCCA, and no visible ablation of the mechanism was found.",
    },
    "review-issue-cluster-yxn76hmetm-obligation-grounded-review-issue-missing-baseline-equalal-baseline": {
        "manual_label": "C",
        "permissive_label": "B",
        "reason": "EqualAL is paper-named related work, but same-setting comparability to HALO's active domain adaptation setting is uncertain from the verified bundle.",
    },
    "review-issue-cluster-yxn76hmetm-obligation-grounded-review-issue-evaluation-protocol-risk-same-budget-same-hardware-fair-comparison-protocol-": {
        "manual_label": "D",
        "reason": "The visible text provides ADA protocol, label budget, dataset, and training protocol details, so the same-budget/same-hardware target is overbroad and counterevidenced.",
    },
    "review-issue-cluster-yxn76hmetm-obligation-grounded-review-issue-missing-ablation-region-based-hyperbolic-feature-reweighting-hfr-mechanism-m": {
        "manual_label": "D",
        "reason": "The paper explicitly analyzes HFR and reports a +1.6 mIoU effect and robustness/stability benefit; this is a counterevidence miss.",
    },
    "review-issue-cluster-kouaayk5kx-obligation-grounded-review-issue-evaluation-protocol-risk-split-threshold-seed-same-budget-protocol-for-ogl-e": {
        "manual_label": "C",
        "reason": "The fairness/protocol concern is plausible, but the target bundles split, threshold, seed, and budget too broadly while the paper gives several settings and comparison details.",
    },
    "review-issue-cluster-xh3oiihtvf-quote-grounded-review-issue-result-claim-mismatch-incorporating-a-secure-aggregator-in-the-federated-model-re": {
        "manual_label": "MERGE",
        "merge_target": "review-issue-cluster-xh3oiihtvf-quote-grounded-review-issue-negative-result-incorporating-a-secure-aggregator-in-the-federated-model-results-",
        "reason": "This is the same secure-aggregator degradation quote and same claim area as the negative-result cluster; it should not count as a separate paper-facing issue.",
    },
    "review-issue-cluster-xh3oiihtvf-quote-grounded-review-issue-negative-result-incorporating-a-secure-aggregator-in-the-federated-model-results-": {
        "manual_label": "B",
        "reason": "The copied quote is a real paper-negative result showing secure aggregation hurts performance; it is defensible but not a strong independent issue because the paper itself acknowledges part of it.",
    },
}


def _load_cases(path: Path) -> List[Dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    cases = payload.get("cases") if isinstance(payload, dict) else payload
    if not isinstance(cases, list):
        raise ValueError(f"No cases list found in {path}")
    return [case for case in cases if isinstance(case, dict)]


def _cluster_representatives(cases: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen: set[str] = set()
    reps: List[Dict[str, Any]] = []
    for case in cases:
        cluster_id = str(case.get("issue_cluster_id") or "")
        if not cluster_id or cluster_id in seen:
            continue
        seen.add(cluster_id)
        reps.append(case)
    return reps


def _manual_record(case: Dict[str, Any], audit: Dict[str, Dict[str, str]]) -> Dict[str, Any]:
    cluster_id = str(case.get("issue_cluster_id") or "")
    label = audit.get(cluster_id)
    if label is None:
        raise KeyError(f"Manual audit missing cluster_id: {cluster_id}")
    record = {
        "cluster_id": cluster_id,
        "paper_id": str(case.get("paper_id") or ""),
        "issue_type": str(case.get("issue_type") or ""),
        "cluster_target": str(case.get("issue_cluster_target") or ""),
        "cluster_size": int(case.get("issue_cluster_size") or 1),
        "source": str(case.get("source_of_expectation") or ""),
        "discovery_origin": str(case.get("discovery_origin") or ""),
        "candidate_kind": str(case.get("reviewer_candidate_kind") or ""),
        "manual_label": label.get("manual_label", ""),
        "permissive_label": label.get("permissive_label", ""),
        "merge_target": label.get("merge_target", ""),
        "reason": label.get("reason", ""),
        "claim_anchor": str(case.get("claim_anchor") or ""),
        "inventory_or_quote": str(case.get("inventory_or_quote") or ""),
        "missing_or_mismatch": str(case.get("missing_or_mismatch") or ""),
    }
    return record


def build_manual_audit(cases: List[Dict[str, Any]], audit: Dict[str, Dict[str, str]]) -> Dict[str, Any]:
    reps = _cluster_representatives(cases)
    cluster_ids = {str(case.get("issue_cluster_id") or "") for case in reps}
    stale = sorted(set(audit) - cluster_ids)
    if stale:
        raise KeyError(f"Manual audit has stale cluster ids: {stale}")
    records = [_manual_record(case, audit) for case in reps]
    labels = Counter(record["manual_label"] for record in records)
    permissive_ab = sum(
        1
        for record in records
        if record["manual_label"] in {"A", "B"} or record.get("permissive_label") in {"A", "B"}
    )
    merge_count = labels.get("MERGE", 0)
    summary = {
        "system_row_count": len(cases),
        "system_cluster_count": len(records),
        "manual_merge_duplicate_count": merge_count,
        "manual_deduplicated_cluster_count": len(records) - merge_count,
        "manual_A_cluster_count": labels.get("A", 0),
        "manual_B_cluster_count": labels.get("B", 0),
        "manual_C_cluster_count": labels.get("C", 0),
        "manual_D_cluster_count": labels.get("D", 0),
        "manual_strict_AB_cluster_count": labels.get("A", 0) + labels.get("B", 0),
        "manual_permissive_AB_cluster_count": permissive_ab,
        "manual_false_positive_cluster_count": labels.get("D", 0),
    }
    origin_counts = Counter(record["candidate_kind"] or record["discovery_origin"] or "unknown" for record in records)
    source_counts = Counter(record["source"] or "unknown" for record in records)
    summary["cluster_origin_counts"] = dict(sorted(origin_counts.items()))
    summary["cluster_source_counts"] = dict(sorted(source_counts.items()))
    return {"summary": summary, "clusters": records}


def _md_escape(value: Any) -> str:
    return str(value or "").replace("|", "\\|").replace("\n", " ")


def render_markdown(payload: Dict[str, Any], source: Path) -> str:
    summary = payload["summary"]
    lines = [
        "# P29 Manual Review Issue Cluster Audit",
        "",
        f"- source case table: `{source}`",
        "- audit scope: P29 2026-07-01 verifier-passing issue clusters",
        "- audit unit: deduplicated system cluster, not raw row",
        "",
        "## Summary",
        "",
        f"- system rows: `{summary['system_row_count']}`",
        f"- system clusters: `{summary['system_cluster_count']}`",
        f"- manual duplicate merges: `{summary['manual_merge_duplicate_count']}`",
        f"- manual deduplicated clusters: `{summary['manual_deduplicated_cluster_count']}`",
        f"- strict A/B clusters: `{summary['manual_strict_AB_cluster_count']}`",
        f"- permissive A/B clusters: `{summary['manual_permissive_AB_cluster_count']}`",
        f"- A/B/C/D/MERGE: `{summary['manual_A_cluster_count']}` / `{summary['manual_B_cluster_count']}` / `{summary['manual_C_cluster_count']}` / `{summary['manual_D_cluster_count']}` / `{summary['manual_merge_duplicate_count']}`",
        "",
        "Paper-facing interpretation: P29 produced 20 verifier-passing rows and 15 system clusters. Manual spot-checking supports 8 strict A/B clusters, 9 under a permissive reading, after merging one direct-quote duplicate. The remaining risky cases are mostly counterevidence misses, overbroad protocol targets, or weak same-setting baseline assumptions.",
        "",
        "## Cluster Labels",
        "",
        "| paper | issue_type | target | origin | label | permissive | merge target | reason |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for record in payload["clusters"]:
        lines.append(
            "| "
            + " | ".join(
                _md_escape(record.get(key))
                for key in (
                    "paper_id",
                    "issue_type",
                    "cluster_target",
                    "candidate_kind",
                    "manual_label",
                    "permissive_label",
                    "merge_target",
                    "reason",
                )
            )
            + " |"
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build manual audit artifact for review issue clusters.")
    parser.add_argument("--case-table-json", required=True)
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--output-md", required=True)
    parser.add_argument("--preset", choices=["p29_20260701"], default="p29_20260701")
    args = parser.parse_args()

    audit = P29_20260701_AUDIT
    source = Path(args.case_table_json)
    payload = build_manual_audit(_load_cases(source), audit)
    Path(args.output_json).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    Path(args.output_md).write_text(render_markdown(payload, source), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
