#!/usr/bin/env python3
"""Validate and atomically activate one P34 symmetric-discovery artifact set."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Mapping


SUFFIXES = {
    "packets": "_PACKETS.jsonl",
    "provenance": "_DISCOVERY_PROVENANCE.json",
    "manifest": "_MANIFEST.json",
    "manifest_md": "_MANIFEST.md",
    "cases": "_CASES.json",
    "human_template": "_HUMAN_AUDIT_TEMPLATE.json",
}


def _canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")


def _load_json(path: Path) -> Dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain an object")
    return value


def _load_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"{path}:{line_no} must contain an object")
        rows.append(value)
    return rows


def _paths(prefix: Path) -> Dict[str, Path]:
    return {key: Path(str(prefix) + suffix) for key, suffix in SUFFIXES.items()}


def validate_source(prefix: Path, allow_blocked_bootstrap: bool = False) -> Dict[str, Any]:
    paths = _paths(prefix)
    missing = [key for key, path in paths.items() if not path.exists()]
    if missing:
        return {"status": "BLOCKED", "blocking_issues": [f"missing_source_artifacts:{','.join(missing)}"]}
    manifest = _load_json(paths["manifest"])
    packets = _load_jsonl(paths["packets"])
    provenance = list(_load_json(paths["provenance"]).get("items") or [])
    labels = list(_load_json(paths["human_template"]).get("labels") or [])
    packet_ids = [str(item.get("packet_id") or "") for item in packets]
    provenance_ids = [str(item.get("packet_id") or "") for item in provenance if isinstance(item, dict)]
    label_ids = [str(item.get("packet_id") or "") for item in labels if isinstance(item, dict)]
    blocking = []
    source_status = str(manifest.get("status") or "")
    if source_status != "PASS_GENERATION" and not allow_blocked_bootstrap:
        blocking.append(f"source_manifest_not_pass_generation:{source_status or 'MISSING'}")
    if source_status == "PASS_GENERATION":
        if int(manifest.get("paper_count") or 0) != 20:
            blocking.append(f"paper_count_not_20:{manifest.get('paper_count')}")
        if set(manifest.get("model_codes") or []) != {"M", "P"}:
            blocking.append("model_codes_not_symmetric_M_P")
        for code in ("M", "P"):
            if int((manifest.get("candidate_counts_by_code") or {}).get(code) or 0) <= 0:
                blocking.append(f"no_candidates_for_discovery_code:{code}")
    if not bool(manifest.get("prompt_identity_symmetric")):
        blocking.append("prompt_identity_not_symmetric")
    if not bool(manifest.get("generator_identity_absent_from_packets")):
        blocking.append("generator_identity_present_in_packets")
    if int(manifest.get("invalid_span_packet_count") or 0) != 0:
        blocking.append(f"invalid_span_packets:{manifest.get('invalid_span_packet_count')}")
    duplicates = sorted(packet_id for packet_id, count in Counter(packet_ids).items() if packet_id and count > 1)
    if duplicates:
        blocking.append(f"duplicate_packet_ids:{len(duplicates)}")
    if any(not packet_id for packet_id in packet_ids):
        blocking.append("empty_packet_ids")
    if set(packet_ids) != set(provenance_ids):
        blocking.append("packet_provenance_id_mismatch")
    if set(packet_ids) != set(label_ids):
        blocking.append("packet_label_template_id_mismatch")
    if any(str(item.get("task_type") or "") != "review_issue" for item in packets):
        blocking.append("non_review_issue_packet_present")
    packet_bytes = b"".join(_canonical_bytes(item) for item in packets)
    provenance_bytes = _canonical_bytes(provenance)
    if hashlib.sha256(packet_bytes).hexdigest() != str(manifest.get("packets_sha256") or ""):
        blocking.append("packets_sha256_mismatch")
    if hashlib.sha256(provenance_bytes).hexdigest() != str(manifest.get("provenance_sha256") or ""):
        blocking.append("provenance_sha256_mismatch")
    return {
        "status": "PASS" if not blocking else "BLOCKED",
        "source_status": source_status,
        "bootstrap_nonpass": source_status != "PASS_GENERATION",
        "packet_count": len(packets),
        "provenance_count": len(provenance),
        "label_template_count": len(labels),
        "discovery_membership_counts": dict(Counter(
            code for item in provenance if isinstance(item, dict) for code in item.get("discovery_codes", []) or []
        )),
        "blocking_issues": blocking,
    }


def _atomic_copy(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    temporary.write_bytes(source.read_bytes())
    temporary.replace(destination)


def activate(source_prefix: Path, active_prefix: Path, allow_blocked_bootstrap: bool = False) -> Dict[str, Any]:
    validation = validate_source(source_prefix, allow_blocked_bootstrap)
    if validation["status"] != "PASS":
        return {
            "schema_version": "p34_symmetric_discovery_activation_v1",
            "status": "BLOCKED",
            "boundary": "Validated atomic activation; no label mutation and no ReviewState mutation",
            "source_prefix": str(source_prefix),
            "active_prefix": str(active_prefix),
            "validation": validation,
            "activated": False,
            "blocking_issues": validation["blocking_issues"],
        }
    source_paths, active_paths = _paths(source_prefix), _paths(active_prefix)
    for key in SUFFIXES:
        _atomic_copy(source_paths[key], active_paths[key])
    active_hashes = {key: hashlib.sha256(path.read_bytes()).hexdigest() for key, path in active_paths.items()}
    bootstrap = bool(validation.get("bootstrap_nonpass"))
    return {
        "schema_version": "p34_symmetric_discovery_activation_v1",
        "status": "ACTIVE_BLOCKED_BOOTSTRAP" if bootstrap else "ACTIVE_READY",
        "boundary": "Validated atomic activation; no label mutation and no ReviewState mutation",
        "source_prefix": str(source_prefix),
        "active_prefix": str(active_prefix),
        "validation": validation,
        "activated": True,
        "active_hashes": active_hashes,
        "blocking_issues": ["source_not_pass_generation"] if bootstrap else [],
    }


def render_markdown(report: Mapping[str, Any]) -> str:
    return "\n".join([
        "# P34 Symmetric Discovery Activation",
        "",
        f"- status: **{report['status']}**",
        f"- activated: `{report['activated']}`",
        f"- source_prefix: `{report['source_prefix']}`",
        f"- active_prefix: `{report['active_prefix']}`",
        f"- packet_count: `{(report.get('validation') or {}).get('packet_count', 0)}`",
        "",
        "## Blocking Issues",
        "",
        *([f"- `{item}`" for item in report.get("blocking_issues", [])] or ["- none"]),
    ]) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-prefix", required=True)
    parser.add_argument("--active-prefix", default="P34_2_SYMMETRIC_DISCOVERY_ACTIVE_20260711")
    parser.add_argument("--allow-blocked-bootstrap", action="store_true")
    parser.add_argument("--output-json", default="P34_2_SYMMETRIC_DISCOVERY_ACTIVE_ACTIVATION_20260711.json")
    parser.add_argument("--output-md", default="P34_2_SYMMETRIC_DISCOVERY_ACTIVE_ACTIVATION_20260711.md")
    args = parser.parse_args()
    report = activate(Path(args.source_prefix), Path(args.active_prefix), args.allow_blocked_bootstrap)
    Path(args.output_json).write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    Path(args.output_md).write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    return 0 if report["status"] in {"ACTIVE_READY", "ACTIVE_BLOCKED_BOOTSTRAP"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
