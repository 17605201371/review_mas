#!/usr/bin/env python3
"""Validate, compare, resolve, and freeze P34 human Judge labels."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from scripts.p34_annotation_signature import audit_rows, load_public_key


LABEL_CONTRACT_VERSION = "p34_label_contract_v1"
TASK_LABEL_TO_TARGET = {
    "evidence_relation": {
        "supports": "supports",
        "partially_supports": "partially_supports",
        "contradicts": "contradicts",
        "unrelated": "unrelated",
        "uncertain": "uncertain",
    },
    "claim_faithfulness": {
        "faithful": "faithful",
        "overstated": "overstated",
        "unsupported_extraction": "unsupported_extraction",
        "uncertain": "uncertain",
    },
    "review_issue": {
        "A": "verified",
        "B": "verified",
        "C": "uncertain",
        "D": "rejected",
    },
}


def _load_rows(path: Path) -> List[Dict[str, Any]]:
    value = json.loads(path.read_text(encoding="utf-8"))
    rows = value.get("labels", []) if isinstance(value, dict) else []
    if not isinstance(rows, list):
        raise ValueError(f"{path} must contain a labels list")
    return [item for item in rows if isinstance(item, dict)]


def _by_id(rows: Sequence[Mapping[str, Any]]) -> Dict[str, Mapping[str, Any]]:
    result = {}
    for item in rows:
        packet_id = str(item.get("packet_id") or "")
        if packet_id:
            result[packet_id] = item
    return result


def _label(item: Mapping[str, Any]) -> str:
    return str(item.get("human_label") or "").strip()


def _allowed(item: Mapping[str, Any]) -> set[str]:
    return {str(value) for value in item.get("allowed_labels", []) if str(value)}


def _infer_task_type(item: Mapping[str, Any], label: str) -> str:
    explicit = str(item.get("task_type") or "")
    if explicit:
        return explicit
    allowed = _allowed(item)
    candidates = [
        task
        for task, mapping in TASK_LABEL_TO_TARGET.items()
        if label in mapping and allowed and allowed.issubset(mapping)
    ]
    return candidates[0] if len(candidates) == 1 else ""


def _validate_primary(rows: Sequence[Mapping[str, Any]], require_reason: bool) -> Dict[str, Any]:
    ids = [str(item.get("packet_id") or "") for item in rows]
    duplicate_ids = sorted(packet_id for packet_id, count in Counter(ids).items() if packet_id and count > 1)
    missing_ids = [index for index, packet_id in enumerate(ids) if not packet_id]
    missing_labels = []
    invalid_labels = []
    missing_reasons = []
    for item in rows:
        packet_id = str(item.get("packet_id") or "")
        label = _label(item)
        allowed = _allowed(item)
        if not label:
            missing_labels.append(packet_id)
        elif allowed and label not in allowed:
            invalid_labels.append({"packet_id": packet_id, "label": label, "allowed": sorted(allowed)})
        if require_reason and label and not str(item.get("human_reason") or "").strip():
            missing_reasons.append(packet_id)
    return {
        "row_count": len(rows),
        "duplicate_packet_ids": duplicate_ids,
        "missing_packet_id_indexes": missing_ids,
        "missing_label_packet_ids": missing_labels,
        "invalid_labels": invalid_labels,
        "missing_reason_packet_ids": missing_reasons,
        "complete": not (duplicate_ids or missing_ids or missing_labels or invalid_labels or missing_reasons),
    }


def _cohen_kappa(pairs: Sequence[Tuple[str, str]]) -> Optional[float]:
    if not pairs:
        return None
    labels = sorted({label for pair in pairs for label in pair})
    total = len(pairs)
    observed = sum(a == b for a, b in pairs) / total
    a_counts = Counter(a for a, _ in pairs)
    b_counts = Counter(b for _, b in pairs)
    expected = sum((a_counts[label] / total) * (b_counts[label] / total) for label in labels)
    if expected >= 1.0:
        return 1.0 if observed >= 1.0 else 0.0
    return (observed - expected) / (1.0 - expected)


def audit_labels(
    primary_path: Path,
    secondary_path: Optional[Path],
    resolution_path: Optional[Path],
    min_double_labeled: int,
    require_reason: bool,
    required_secondary_ids: Optional[set[str]] = None,
    expected_task_type: Optional[str] = None,
    require_distinct_reviewer_ids: bool = False,
    verification_key: Optional[Path] = None,
    require_submission_signatures: bool = False,
) -> Dict[str, Any]:
    primary_rows = _load_rows(primary_path)
    primary = _by_id(primary_rows)
    primary_validation = _validate_primary(primary_rows, require_reason)
    secondary_rows = _load_rows(secondary_path) if secondary_path else []
    secondary = _by_id(secondary_rows)
    resolution_rows = _load_rows(resolution_path) if resolution_path else []
    resolutions = _by_id(resolution_rows)
    primary_reviewer_ids = sorted({
        str(item.get("human_reviewer_id") or "") for item in primary_rows
        if _label(item) and str(item.get("human_reviewer_id") or "")
    })
    secondary_reviewer_ids = sorted({
        str(item.get("human_reviewer_id") or "") for item in secondary_rows
        if _label(item) and str(item.get("human_reviewer_id") or "")
    })
    resolution_reviewer_ids = sorted({
        str(item.get("human_reviewer_id") or "") for item in resolution_rows
        if _label(item) and str(item.get("human_reviewer_id") or "")
    })
    labeled_secondary_ids = {packet_id for packet_id, item in secondary.items() if _label(item)}
    assigned_secondary_ids = set(required_secondary_ids or [])
    unexpected_secondary_ids = sorted(labeled_secondary_ids - assigned_secondary_ids) if required_secondary_ids is not None else []
    missing_assigned_secondary_ids = sorted(assigned_secondary_ids - labeled_secondary_ids) if required_secondary_ids is not None else []
    eligible_secondary_ids = assigned_secondary_ids if required_secondary_ids is not None else set(secondary)
    overlap_ids = sorted(
        packet_id
        for packet_id in primary
        if packet_id in eligible_secondary_ids
        and _label(primary[packet_id])
        and _label(secondary.get(packet_id, {}))
    )
    pairs = [(_label(primary[packet_id]), _label(secondary[packet_id])) for packet_id in overlap_ids]
    agreement_count = sum(a == b for a, b in pairs)
    disagreements = [
        {"packet_id": packet_id, "primary": _label(primary[packet_id]), "secondary": _label(secondary[packet_id])}
        for packet_id in overlap_ids
        if _label(primary[packet_id]) != _label(secondary[packet_id])
    ]
    unresolved = [item for item in disagreements if not _label(resolutions.get(item["packet_id"], {}))]
    frozen = []
    source_task_type_mismatches = []
    unmapped_frozen_packet_ids = []
    for packet_id, item in primary.items():
        final_label = _label(item)
        source = "primary"
        if final_label and packet_id in secondary and _label(secondary[packet_id]) == final_label:
            source = "double_agreement"
        if packet_id in resolutions and _label(resolutions[packet_id]):
            final_label = _label(resolutions[packet_id])
            source = "adjudicated_resolution"
        source_task_type = str(item.get("task_type") or "")
        task_type = str(expected_task_type or _infer_task_type(item, final_label))
        if expected_task_type and source_task_type and source_task_type != expected_task_type:
            source_task_type_mismatches.append(packet_id)
        target = (TASK_LABEL_TO_TARGET.get(task_type) or {}).get(final_label, "")
        if final_label and not target:
            unmapped_frozen_packet_ids.append(packet_id)
        frozen_item = {
            "packet_id": packet_id,
            "paper_id": str(item.get("paper_id") or ""),
            "task_type": task_type,
            "human_label": final_label,
            "human_reason": str((resolutions.get(packet_id) or item).get("human_reason") or ""),
            "label_source": source,
            "allowed_labels": sorted(_allowed(item)),
            "target_verdict_mapping": target,
            "label_contract_version": LABEL_CONTRACT_VERSION,
        }
        if final_label in {"A", "B", "C", "D"}:
            frozen_item["source_label"] = final_label
        frozen.append(frozen_item)
    blocking = []
    if not primary_validation["complete"]:
        blocking.append("primary_labels_incomplete_or_invalid")
    if len(overlap_ids) < min_double_labeled:
        blocking.append(f"double_labeled_below_minimum:{len(overlap_ids)}/{min_double_labeled}")
    if unresolved:
        blocking.append(f"unresolved_disagreements:{len(unresolved)}")
    if unexpected_secondary_ids:
        blocking.append(f"secondary_labels_outside_assignment:{len(unexpected_secondary_ids)}")
    if missing_assigned_secondary_ids:
        blocking.append(f"assigned_secondary_labels_incomplete:{len(missing_assigned_secondary_ids)}")
    if source_task_type_mismatches:
        blocking.append(f"source_task_type_mismatch:{len(source_task_type_mismatches)}")
    if unmapped_frozen_packet_ids:
        blocking.append(f"unmapped_frozen_labels:{len(unmapped_frozen_packet_ids)}")
    if require_distinct_reviewer_ids:
        if len(primary_reviewer_ids) != 1:
            blocking.append(f"primary_reviewer_identity_count_not_1:{len(primary_reviewer_ids)}")
        if len(secondary_reviewer_ids) != 1:
            blocking.append(f"secondary_reviewer_identity_count_not_1:{len(secondary_reviewer_ids)}")
        if primary_reviewer_ids and secondary_reviewer_ids and primary_reviewer_ids[0] == secondary_reviewer_ids[0]:
            blocking.append("primary_secondary_reviewer_identity_not_distinct")
        if disagreements:
            if len(resolution_reviewer_ids) != 1:
                blocking.append(f"adjudicator_reviewer_identity_count_not_1:{len(resolution_reviewer_ids)}")
            elif resolution_reviewer_ids[0] in set(primary_reviewer_ids + secondary_reviewer_ids):
                blocking.append("adjudicator_reviewer_identity_not_distinct")
    signature_audit = {
        "required": require_submission_signatures,
        "primary": {"status": "NOT_CHECKED", "submitted_count": 0, "valid_count": 0, "invalid_ids": []},
        "secondary": {"status": "NOT_CHECKED", "submitted_count": 0, "valid_count": 0, "invalid_ids": []},
        "resolution": {"status": "NOT_CHECKED", "submitted_count": 0, "valid_count": 0, "invalid_ids": []},
    }
    if require_submission_signatures:
        if verification_key is None:
            blocking.append("annotation_verification_key_missing")
        else:
            signature_audit.update({
                "primary": audit_rows(primary_rows, "label", verification_key),
                "secondary": audit_rows(secondary_rows, "label", verification_key),
                "resolution": audit_rows(resolution_rows, "label", verification_key),
            })
            for source in ("primary", "secondary", "resolution"):
                invalid_count = len(signature_audit[source]["invalid_ids"])
                if invalid_count:
                    blocking.append(f"invalid_{source}_submission_signatures:{invalid_count}")
    frozen_bytes = (json.dumps(frozen, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")
    return {
        "status": "PASS" if not blocking else "BLOCKED",
        "primary_path": str(primary_path),
        "primary_sha256": hashlib.sha256(primary_path.read_bytes()).hexdigest(),
        "secondary_path": str(secondary_path) if secondary_path else "",
        "secondary_sha256": hashlib.sha256(secondary_path.read_bytes()).hexdigest() if secondary_path and secondary_path.exists() else "",
        "resolution_path": str(resolution_path) if resolution_path else "",
        "primary_validation": primary_validation,
        "double_labeled_count": len(overlap_ids),
        "minimum_double_labeled": min_double_labeled,
        "assigned_secondary_count": len(assigned_secondary_ids) if required_secondary_ids is not None else None,
        "unexpected_secondary_packet_ids": unexpected_secondary_ids,
        "missing_assigned_secondary_packet_ids": missing_assigned_secondary_ids,
        "expected_task_type": str(expected_task_type or ""),
        "label_contract_version": LABEL_CONTRACT_VERSION,
        "source_task_type_mismatch_packet_ids": source_task_type_mismatches,
        "unmapped_frozen_packet_ids": unmapped_frozen_packet_ids,
        "mapped_frozen_label_count": sum(bool(item.get("target_verdict_mapping")) for item in frozen),
        "require_distinct_reviewer_ids": require_distinct_reviewer_ids,
        "primary_reviewer_ids": primary_reviewer_ids,
        "secondary_reviewer_ids": secondary_reviewer_ids,
        "resolution_reviewer_ids": resolution_reviewer_ids,
        "signature_audit": signature_audit,
        "agreement_count": agreement_count,
        "raw_agreement": agreement_count / len(pairs) if pairs else None,
        "cohen_kappa": _cohen_kappa(pairs),
        "disagreement_count": len(disagreements),
        "disagreements": disagreements,
        "unresolved_disagreements": unresolved,
        "frozen_label_count": len(frozen),
        "frozen_labels_sha256": hashlib.sha256(frozen_bytes).hexdigest(),
        "blocking_issues": blocking,
        "frozen_labels": frozen,
    }


def render_markdown(report: Mapping[str, Any]) -> str:
    return "\n".join([
        "# P34 Human Label Audit",
        "",
        f"- status: **{report['status']}**",
        f"- primary_rows: `{report['primary_validation']['row_count']}`",
        f"- primary_complete: `{report['primary_validation']['complete']}`",
        f"- double_labeled_count: `{report['double_labeled_count']}`",
        f"- raw_agreement: `{report['raw_agreement']}`",
        f"- cohen_kappa: `{report['cohen_kappa']}`",
        f"- submission_signatures_required: `{report.get('signature_audit', {}).get('required', False)}`",
        f"- disagreement_count: `{report['disagreement_count']}`",
        f"- frozen_labels_sha256: `{report['frozen_labels_sha256']}`",
        "",
        "## Blocking Issues",
        "",
        *([f"- `{item}`" for item in report["blocking_issues"]] or ["- none"]),
    ]) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--primary", required=True)
    parser.add_argument("--secondary")
    parser.add_argument("--resolution")
    parser.add_argument("--assignment")
    parser.add_argument("--assignment-task")
    parser.add_argument("--task-type", choices=sorted(TASK_LABEL_TO_TARGET))
    parser.add_argument("--allow-role-only-identity", action="store_true")
    parser.add_argument("--verification-key")
    parser.add_argument("--allow-unsigned-submissions", action="store_true")
    parser.add_argument("--min-double-labeled", type=int, default=20)
    parser.add_argument("--allow-empty-reason", action="store_true")
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--output-md", required=True)
    parser.add_argument("--output-frozen-labels", required=True)
    args = parser.parse_args()
    required_secondary_ids = None
    if args.assignment:
        if not args.assignment_task:
            raise ValueError("--assignment-task is required with --assignment")
        assignment = json.loads(Path(args.assignment).read_text(encoding="utf-8"))
        required_secondary_ids = set(
            ((assignment.get("tasks") or {}).get(args.assignment_task) or {}).get("secondary_packet_ids") or []
        )
    verification_key = (
        Path(args.verification_key)
        if args.verification_key
        else Path(args.primary).parent / "annotation_signing_public.pem"
    )
    if verification_key.exists():
        load_public_key(verification_key)
    else:
        verification_key = None
    report = audit_labels(
        Path(args.primary), Path(args.secondary) if args.secondary else None,
        Path(args.resolution) if args.resolution else None,
        args.min_double_labeled, not args.allow_empty_reason, required_secondary_ids,
        args.task_type or args.assignment_task, not args.allow_role_only_identity,
        verification_key, not args.allow_unsigned_submissions,
    )
    Path(args.output_json).write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    Path(args.output_md).write_text(render_markdown(report), encoding="utf-8")
    Path(args.output_frozen_labels).write_text(
        json.dumps({"labels": report["frozen_labels"], "sha256": report["frozen_labels_sha256"]}, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({key: report[key] for key in ("status", "double_labeled_count", "raw_agreement", "cohen_kappa", "frozen_label_count", "blocking_issues")}))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
