#!/usr/bin/env python3
"""Build an operational quality dashboard for P34 human annotation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Mapping


TASK_NAMES = {
    "evidence_relation": "positive_evidence_relation",
    "claim_faithfulness": "claim_faithfulness",
    "review_issue": "negative_review_issue",
}


def _load_json(path: Path) -> Dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain an object")
    return value


def _task_quality(task: str, report: Mapping[str, Any]) -> Dict[str, Any]:
    validation = dict(report.get("primary_validation") or {})
    signature = dict(report.get("signature_audit") or {})
    total = int(validation.get("row_count") or 0)
    primary_complete = total - len(validation.get("missing_label_packet_ids") or [])
    assigned_secondary = int(report.get("assigned_secondary_count") or 0)
    missing_secondary = len(report.get("missing_assigned_secondary_packet_ids") or [])
    secondary_complete = max(0, assigned_secondary - missing_secondary)
    invalid_signatures = sum(
        len((signature.get(role) or {}).get("invalid_ids") or [])
        for role in ("primary", "secondary", "resolution")
    )
    disagreements = int(report.get("disagreement_count") or 0)
    unresolved = len(report.get("unresolved_disagreements") or [])
    return {
        "task_type": task,
        "display_name": TASK_NAMES[task],
        "status": str(report.get("status") or "MISSING"),
        "primary_complete": primary_complete,
        "primary_total": total,
        "primary_completion_rate": primary_complete / total if total else None,
        "secondary_complete": secondary_complete,
        "secondary_assigned": assigned_secondary,
        "secondary_completion_rate": secondary_complete / assigned_secondary if assigned_secondary else None,
        "double_labeled_count": int(report.get("double_labeled_count") or 0),
        "minimum_double_labeled": int(report.get("minimum_double_labeled") or 0),
        "agreement_count": int(report.get("agreement_count") or 0),
        "raw_agreement": report.get("raw_agreement"),
        "cohen_kappa": report.get("cohen_kappa"),
        "disagreement_count": disagreements,
        "unresolved_disagreement_count": unresolved,
        "invalid_signature_count": invalid_signatures,
        "blocking_issues": list(report.get("blocking_issues") or []),
    }


def build_quality_report(
    *,
    positive: Mapping[str, Any],
    claim: Mapping[str, Any],
    negative: Mapping[str, Any],
    paper_index: Mapping[str, Any],
    assignment: Mapping[str, Any],
    discovery_manifest: Mapping[str, Any],
    annotator_registry: Mapping[str, Any],
    two_by_two: Mapping[str, Any],
    discovery_health: Mapping[str, Any] | None = None,
) -> Dict[str, Any]:
    tasks = {
        "evidence_relation": _task_quality("evidence_relation", positive),
        "claim_faithfulness": _task_quality("claim_faithfulness", claim),
        "review_issue": _task_quality("review_issue", negative),
    }
    roles = dict(annotator_registry.get("roles") or {})
    registered_roles = {
        role: bool(isinstance(roles.get(role), dict) and roles[role].get("reviewer_id"))
        for role in ("primary", "secondary", "adjudicator")
    }
    credential_readiness = {
        role: {
            "registered": registered_roles[role],
            "recovery_enabled": bool(isinstance(roles.get(role), dict) and roles[role].get("recovery_code_sha256")),
            "credential_generation": int(roles[role].get("credential_generation") or 0)
            if isinstance(roles.get(role), dict) else 0,
        }
        for role in ("primary", "secondary", "adjudicator")
    }
    discovery_status = str(discovery_manifest.get("status") or "MISSING")
    discovery_packets = int(
        discovery_manifest.get("packet_count")
        or discovery_manifest.get("neutral_cluster_count")
        or discovery_manifest.get("raw_candidate_count")
        or discovery_manifest.get("valid_case_count")
        or 0
    )
    discovery_ready = discovery_status == "PASS_GENERATION" and discovery_packets > 0
    health = dict(discovery_health or {})
    health_error_codes = []
    for item in health.get("api_errors") or []:
        message = str((item or {}).get("message") or "") if isinstance(item, Mapping) else str(item)
        if "402" in message or "insufficient_balance" in message.lower() or "insufficient account balance" in message.lower():
            health_error_codes.append("insufficient_balance")
        elif isinstance(item, Mapping):
            health_error_codes.append(str(item.get("error_type") or "provider_error"))
        else:
            health_error_codes.append("provider_error")
    paper_total = int(paper_index.get("paper_count") or 0)
    paper_complete = int(paper_index.get("completed_annotation_count") or 0)
    paper_signature = dict(paper_index.get("signature_audit") or {})
    paper_invalid_signatures = len(paper_signature.get("invalid_ids") or [])
    integrity_issues = []
    for task, quality in tasks.items():
        if quality["invalid_signature_count"]:
            integrity_issues.append(f"{task}:invalid_signatures:{quality['invalid_signature_count']}")
    if paper_invalid_signatures:
        integrity_issues.append(f"paper_index:invalid_signatures:{paper_invalid_signatures}")
    invalid_spans = len((two_by_two.get("preflight") or {}).get("invalid_span_packet_ids") or [])
    if invalid_spans:
        integrity_issues.append(f"two_by_two:invalid_spans:{invalid_spans}")

    actionable_now = []
    for task in ("evidence_relation", "claim_faithfulness"):
        if tasks[task]["primary_total"]:
            actionable_now.extend([f"{task}:primary", f"{task}:secondary"])
    if paper_total:
        actionable_now.append("paper_index:primary")
    if discovery_ready:
        actionable_now.extend(["review_issue:primary", "review_issue:secondary"])

    any_progress = any(item["primary_complete"] or item["secondary_complete"] for item in tasks.values()) or paper_complete > 0
    all_annotation_complete = all(item["status"] == "PASS" for item in tasks.values()) and str(paper_index.get("status")) == "PASS"
    if integrity_issues:
        status = "BLOCKED_INTEGRITY"
    elif all_annotation_complete and str(two_by_two.get("status")) == "PASS":
        status = "READY_FOR_2X2_API"
    elif any_progress:
        status = "ANNOTATION_IN_PROGRESS"
    elif discovery_ready:
        status = "READY_FOR_FULL_ANNOTATION"
    else:
        status = "PARTIAL_ANNOTATION_READY"

    blockers = []
    if not discovery_ready:
        blockers.append(f"negative_discovery:{discovery_status}:{discovery_packets}")
    for role in ("primary", "secondary"):
        if not registered_roles[role]:
            blockers.append(f"reviewer_role_unregistered:{role}")
        elif not credential_readiness[role]["recovery_enabled"]:
            blockers.append(f"reviewer_recovery_not_enabled:{role}")
    blockers.extend(integrity_issues)
    return {
        "schema_version": "p34_annotation_quality_report_v1",
        "status": status,
        "boundary": "Operational annotation quality and launch visibility; no labels, gates, or ReviewState are mutated",
        "tasks": tasks,
        "paper_index": {
            "status": str(paper_index.get("status") or "MISSING"),
            "complete": paper_complete,
            "total": paper_total,
            "completion_rate": paper_complete / paper_total if paper_total else None,
            "boundary_recall": paper_index.get("boundary_recall"),
            "anchor_retrieval_recall": paper_index.get("anchor_retrieval_recall"),
            "false_boundary_rate": paper_index.get("false_boundary_rate"),
            "invalid_signature_count": paper_invalid_signatures,
        },
        "discovery": {
            "status": discovery_status,
            "packet_count": discovery_packets,
            "candidate_counts_by_code": dict(discovery_manifest.get("candidate_counts_by_code") or {}),
            "ready_for_annotation": discovery_ready,
            "health_probe_status": str(health.get("status") or "NOT_RUN"),
            "health_probe_error_codes": sorted(set(health_error_codes)),
        },
        "assignment": {
            "status": str(assignment.get("status") or "MISSING"),
            "sha256": str(assignment.get("assignment_sha256") or ""),
        },
        "reviewer_registration": registered_roles,
        "reviewer_credentials": credential_readiness,
        "two_by_two": {
            "status": str(two_by_two.get("status") or "MISSING"),
            "schema_version": str(two_by_two.get("schema_version") or ""),
            "gate_contract_sha256": str(two_by_two.get("gate_contract_sha256") or ""),
            "prompt_blinding_status": str(two_by_two.get("prompt_blinding_status") or "NOT_RUN"),
            "prompt_blinding_manifest_sha256": str(two_by_two.get("prompt_blinding_manifest_sha256") or ""),
            "minimum_cardinality": dict((two_by_two.get("capability_thresholds") or {}).get("minimum_cardinality") or {}),
            "missing_label_count": len((two_by_two.get("preflight") or {}).get("missing_label_packet_ids") or []),
            "invalid_span_count": invalid_spans,
        },
        "actionable_now": actionable_now,
        "blocking_issues": blockers,
    }


def render_markdown(report: Mapping[str, Any]) -> str:
    lines = [
        "# P34 Annotation Quality Dashboard",
        "",
        f"- status: **{report['status']}**",
        f"- actionable_now: `{report['actionable_now']}`",
        f"- reviewer_registration: `{report['reviewer_registration']}`",
        f"- discovery: `{report['discovery']}`",
        "",
        "## Tasks",
        "",
    ]
    for task, item in report["tasks"].items():
        lines.append(
            f"- `{task}`: primary={item['primary_complete']}/{item['primary_total']}, "
            f"secondary={item['secondary_complete']}/{item['secondary_assigned']}, "
            f"agreement={item['raw_agreement']}, kappa={item['cohen_kappa']}, "
            f"unresolved={item['unresolved_disagreement_count']}, invalid_signatures={item['invalid_signature_count']}"
        )
    lines.extend([
        "",
        "## PaperIndex",
        "",
        f"`{report['paper_index']}`",
        "",
        "## Blocking Issues",
        "",
    ])
    lines.extend(f"- `{item}`" for item in report["blocking_issues"]) if report["blocking_issues"] else lines.append("- none")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--positive", required=True)
    parser.add_argument("--claim", required=True)
    parser.add_argument("--negative", required=True)
    parser.add_argument("--paper-index", required=True)
    parser.add_argument("--assignment", required=True)
    parser.add_argument("--discovery-manifest", required=True)
    parser.add_argument("--annotator-registry", required=True)
    parser.add_argument("--two-by-two", required=True)
    parser.add_argument("--discovery-health")
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--output-md", required=True)
    args = parser.parse_args()
    report = build_quality_report(
        positive=_load_json(Path(args.positive)),
        claim=_load_json(Path(args.claim)),
        negative=_load_json(Path(args.negative)),
        paper_index=_load_json(Path(args.paper_index)),
        assignment=_load_json(Path(args.assignment)),
        discovery_manifest=_load_json(Path(args.discovery_manifest)),
        annotator_registry=_load_json(Path(args.annotator_registry)) if Path(args.annotator_registry).exists() else {},
        two_by_two=_load_json(Path(args.two_by_two)),
        discovery_health=_load_json(Path(args.discovery_health)) if args.discovery_health and Path(args.discovery_health).exists() else {},
    )
    Path(args.output_json).write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    Path(args.output_md).write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    return 0 if report["status"] in {"READY_FOR_FULL_ANNOTATION", "READY_FOR_2X2_API"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
