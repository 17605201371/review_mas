#!/usr/bin/env python3
"""Build frozen, label-separated P34 Judge AuditPackets from hardneg20 state."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from agent_system.environments.env_package.review.paper_index import PaperIndex, build_paper_index
from scripts.p34_dual_model_judge_guard import build_audit_packet


def _load_json(path: Path) -> Dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain an object")
    return value


def _load_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"{path}:{line_no} must contain an object")
            rows.append(value)
    return rows


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _canonical_json(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")


def _normalize_ws(value: str) -> str:
    return " ".join(str(value or "").split())


def locate_quote(paper_text: str, quote: str) -> Tuple[Optional[Tuple[int, int]], str]:
    text = str(paper_text or "")
    raw_quote = str(quote or "")
    if not raw_quote:
        return None, "missing_quote"
    exact_starts = [match.start() for match in re.finditer(re.escape(raw_quote), text)]
    if len(exact_starts) == 1:
        start = exact_starts[0]
        return (start, start + len(raw_quote)), "unique_exact"
    if len(exact_starts) > 1:
        return None, "ambiguous_exact"
    tokens = raw_quote.split()
    if not tokens:
        return None, "missing_quote"
    pattern = re.compile(r"\s+".join(re.escape(token) for token in tokens), re.DOTALL)
    matches = list(pattern.finditer(text))
    if len(matches) == 1 and _normalize_ws(matches[0].group(0)) == _normalize_ws(raw_quote):
        return (matches[0].start(), matches[0].end()), "unique_whitespace_normalized"
    if len(matches) > 1:
        return None, "ambiguous_normalized"
    return None, "not_located"


def _claim_lookup(state: Mapping[str, Any]) -> Dict[str, Dict[str, Any]]:
    return {
        str(item.get("claim_id") or ""): item
        for item in state.get("claims", [])
        if isinstance(item, dict) and str(item.get("claim_id") or "")
    }


def _positive_packet(
    paper_id: str,
    state: Mapping[str, Any],
    claim: Mapping[str, Any],
    evidence: Mapping[str, Any],
    pair_index: int,
) -> Tuple[Optional[Dict[str, Any]], Dict[str, Any]]:
    paper_text = str(state.get("paper_text") or "")
    span, match_type = locate_quote(paper_text, str(evidence.get("raw_quote") or ""))
    audit = {
        "paper_id": paper_id,
        "claim_id": str(claim.get("claim_id") or ""),
        "evidence_id": str(evidence.get("evidence_id") or ""),
        "old_verified_source_span_start": evidence.get("verified_source_span_start"),
        "old_verified_source_span_end": evidence.get("verified_source_span_end"),
        "new_match_type": match_type,
        "locatable": span is not None,
    }
    if span is None:
        return None, audit
    start, end = span
    index = build_paper_index(paper_text)
    containing = [
        section for section in index.sections
        if section.source_span_start <= start and end <= section.source_span_end
    ]
    containing.sort(key=lambda section: section.source_span_end - section.source_span_start)
    section = containing[0] if containing else None
    packet_id = f"positive-{paper_id}-{pair_index:03d}"
    packet = {
        "packet_id": packet_id,
        "packet_version": "p34_audit_packet_v1",
        "task_type": "evidence_relation",
        "paper_id": paper_id,
        "claim": {
            "claim_id": str(claim.get("claim_id") or ""),
            "claim_text": str(claim.get("claim") or ""),
            "claim_type": str(claim.get("claim_type") or "other"),
            "claim_source": str(claim.get("claim_source") or ""),
        },
        "candidate_evidence": {
            "evidence_id": str(evidence.get("evidence_id") or ""),
            "quote": paper_text[start:end],
            "source_span_start": start,
            "source_span_end": end,
            "source_locator": str(evidence.get("source_locator") or ""),
            "section_id": section.section_id if section else "",
            "section_type": section.section_type if section else "",
            "match_type": match_type,
        },
        "searched_section_ids": [section.section_id] if section else [],
        "counterevidence_candidates": [
            {
                "evidence_id": f"context-{idx + 1}",
                "section_id": result.result_id if result.result_type == "section" else "",
                "section_type": result.section_type,
                "quote": result.text[:1200],
                "source_span_start": result.source_span_start,
                "source_span_end": result.source_span_start + min(1200, len(result.text)),
            }
            for idx, result in enumerate(index.search(str(claim.get("claim") or ""), top_k=4))
        ],
        "unsearched_scope": "PaperIndex top-4 claim retrieval; relation Judge may return uncertain.",
    }
    audit["packet_id"] = packet_id
    audit["span_roundtrip_ok"] = paper_text[start:end] == packet["candidate_evidence"]["quote"]
    return packet, audit


def _negative_packets(
    states: Mapping[str, Mapping[str, Any]],
    manual_audit: Mapping[str, Any],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    packets = []
    labels = []
    provenance = []
    for index_no, item in enumerate(manual_audit.get("hypotheses", []), start=1):
        if not isinstance(item, dict):
            continue
        paper_id = str(item.get("paper_id") or "")
        state = states.get(paper_id)
        if not state:
            continue
        packet = build_audit_packet(paper_id, build_paper_index(str(state.get("paper_text") or "")), item)
        packet_id = f"negative-{paper_id}-{str(item.get('hypothesis_id') or index_no)}"
        packet["packet_id"] = packet_id
        packet["task_type"] = "review_issue"
        packet["verification_contract"] = {
            "alleged_defect": str(item.get("hypothesis") or ""),
            "required_resolution_evidence": str(item.get("expected_evidence") or ""),
            "falsification_query": str(item.get("counterevidence_query") or ""),
            "resolution_standard": (
                "Counterevidence resolves the issue only if it directly satisfies the required evidence or directly falsifies the alleged defect. "
                "A paper assertion that repeats the original claim is not a measurement, ablation, fairness analysis, or justification."
            ),
        }
        packets.append(packet)
        labels.append({
            "packet_id": packet_id,
            "paper_id": paper_id,
            "source_label": str(item.get("label") or ""),
            "source_label_semantics": "A/B/C/D from frozen P33 human audit",
            "target_verdict_mapping": {
                "A": "verified",
                "B": "verified",
                "C": "uncertain",
                "D": "rejected",
            }.get(str(item.get("label") or ""), ""),
            "manual_decision": str(item.get("manual_decision") or ""),
            "reason": str(item.get("reason") or ""),
        })
        provenance.append({
            "packet_id": packet_id,
            "paper_id": paper_id,
            "discovery_code": "M",
            "discovery_model": "mimo-v2.5",
            "discovery_source": "p33_freeform_critique_manual_audit",
            "source_hypothesis_id": str(item.get("hypothesis_id") or index_no),
        })
    return packets, labels, provenance


def _claim_packets(states: Mapping[str, Mapping[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    packets = []
    annotation_rows = []
    for paper_id, state in states.items():
        index = build_paper_index(str(state.get("paper_text") or ""))
        for claim_no, claim in enumerate(state.get("claims", []), start=1):
            if not isinstance(claim, dict) or not str(claim.get("claim") or "").strip():
                continue
            claim_text = str(claim.get("claim") or "")
            retrieved = index.search(claim_text, top_k=5)
            packet_id = f"claim-{paper_id}-{claim_no:02d}"
            packet = {
                "packet_id": packet_id,
                "packet_version": "p34_audit_packet_v1",
                "task_type": "claim_faithfulness",
                "paper_id": paper_id,
                "claim": {
                    "claim_id": str(claim.get("claim_id") or ""),
                    "claim_text": claim_text,
                    "claim_type": str(claim.get("claim_type") or "other"),
                    "claim_kind": str(claim.get("claim_kind") or "unknown"),
                },
                "claim_source_spans": [
                    {
                        "source_id": f"source-{idx + 1}",
                        "section_id": result.result_id if result.result_type == "section" else "",
                        "section_type": result.section_type,
                        "quote": result.text[:1400],
                        "source_span_start": result.source_span_start,
                        "source_span_end": result.source_span_start + min(1400, len(result.text)),
                        "matched_terms": list(result.matched_terms),
                    }
                    for idx, result in enumerate(retrieved)
                ],
                "searched_section_ids": list(dict.fromkeys(
                    result.result_id for result in retrieved if result.result_type == "section"
                )),
                "unsearched_scope": "PaperIndex top-5 claim retrieval; Claim Judge may return uncertain.",
            }
            packets.append(packet)
            annotation_rows.append({
                "packet_id": packet_id,
                "paper_id": paper_id,
                "task_type": "claim_faithfulness",
                "human_label": "",
                "allowed_labels": ["faithful", "overstated", "unsupported_extraction", "uncertain"],
                "human_reason": "",
                "source_claim_status_for_audit_only": str(claim.get("status") or ""),
                "source_claim_origin_for_audit_only": str(claim.get("claim_origin") or claim.get("claim_source") or ""),
            })
    return packets, annotation_rows


def _validate_packet_spans(packet: Mapping[str, Any], paper_text: str) -> bool:
    def records() -> Iterable[Mapping[str, Any]]:
        candidate = packet.get("candidate_evidence")
        if isinstance(candidate, dict):
            yield candidate
        for key in ("counterevidence_candidates", "retrieved_evidence", "claim_source_spans"):
            for item in packet.get(key, []) or []:
                if isinstance(item, dict):
                    yield item
    for item in records():
        start = item.get("source_span_start")
        end = item.get("source_span_end")
        quote = str(item.get("quote") or "")
        if not isinstance(start, int) or not isinstance(end, int) or paper_text[start:end] != quote:
            return False
    return True


def build_dataset(runner_jsonl: Path, manual_audit_path: Path) -> Dict[str, Any]:
    rows = _load_jsonl(runner_jsonl)
    states = {
        str(row.get("paper_id") or ""): row.get("review_state", {})
        for row in rows
        if isinstance(row.get("review_state"), dict)
    }
    positive_packets = []
    positive_source_audit = []
    positive_annotations = []
    for paper_id, state in states.items():
        claims = _claim_lookup(state)
        pair_no = 0
        for evidence in state.get("evidence_map", []):
            if not isinstance(evidence, dict):
                continue
            if str(evidence.get("semantic_grounding_label") or "") != "semantic_support_verified":
                continue
            claim = claims.get(str(evidence.get("claim_id") or ""))
            if not claim:
                continue
            pair_no += 1
            packet, audit = _positive_packet(paper_id, state, claim, evidence, pair_no)
            positive_source_audit.append(audit)
            if packet is None:
                continue
            positive_packets.append(packet)
            positive_annotations.append({
                "packet_id": packet["packet_id"],
                "paper_id": paper_id,
                "task_type": "evidence_relation",
                "human_label": "",
                "allowed_labels": ["supports", "partially_supports", "contradicts", "unrelated", "uncertain"],
                "human_reason": "",
                "machine_prelabel_for_audit_only": "supports",
                "machine_prelabel_source": "semantic_support_verified",
            })

    negative_packets, negative_labels, negative_discovery_provenance = _negative_packets(
        states, _load_json(manual_audit_path)
    )
    claim_packets, claim_annotations = _claim_packets(states)
    packets = positive_packets + negative_packets + claim_packets
    by_paper = {paper_id: state for paper_id, state in states.items()}
    invalid_span_packets = [
        packet["packet_id"] for packet in packets
        if not _validate_packet_spans(packet, str(by_paper[packet["paper_id"]].get("paper_text") or ""))
    ]
    packet_ids = [packet["packet_id"] for packet in packets]
    duplicate_ids = [packet_id for packet_id, count in Counter(packet_ids).items() if count > 1]
    packet_bytes = b"".join(_canonical_json(packet) for packet in packets)
    frozen_negative_label_bytes = _canonical_json(negative_labels)
    discovery_provenance_bytes = _canonical_json(negative_discovery_provenance)
    manifest = {
        "schema_version": "p34_judge_dataset_v2",
        "boundary": "Label-separated offline AuditPackets; no API calls and no ReviewState mutation",
        "runner_jsonl": str(runner_jsonl),
        "runner_jsonl_sha256": _sha256_bytes(runner_jsonl.read_bytes()),
        "manual_negative_audit": str(manual_audit_path),
        "manual_negative_audit_sha256": _sha256_bytes(manual_audit_path.read_bytes()),
        "paper_count": len(states),
        "packet_count": len(packets),
        "packet_type_counts": dict(Counter(packet["task_type"] for packet in packets)),
        "positive_source_candidate_count": len(positive_source_audit),
        "positive_packet_count": len(positive_packets),
        "positive_match_type_counts": dict(Counter(item["new_match_type"] for item in positive_source_audit)),
        "negative_packet_count": len(negative_packets),
        "negative_label_counts": dict(Counter(item["source_label"] for item in negative_labels)),
        "claim_packet_count": len(claim_packets),
        "invalid_span_packet_count": len(invalid_span_packets),
        "invalid_span_packet_ids": invalid_span_packets,
        "duplicate_packet_ids": duplicate_ids,
        "packets_sha256": _sha256_bytes(packet_bytes),
        "frozen_negative_labels_sha256": _sha256_bytes(frozen_negative_label_bytes),
        "negative_discovery_provenance_count": len(negative_discovery_provenance),
        "negative_discovery_code_counts": dict(
            Counter(item["discovery_code"] for item in negative_discovery_provenance)
        ),
        "negative_discovery_provenance_sha256": _sha256_bytes(discovery_provenance_bytes),
        "positive_human_labels_complete": False,
        "claim_human_labels_complete": False,
        "ready_for_full_judge": bool(
            len(positive_packets) >= 80
            and len(negative_packets) >= 60
            and not invalid_span_packets
            and not duplicate_ids
            and False
        ),
        "blocking_issues": [],
    }
    if len(positive_packets) < 80:
        manifest["blocking_issues"].append(f"positive_packets_below_80:{len(positive_packets)}")
    if len(negative_packets) < 60:
        manifest["blocking_issues"].append(f"negative_packets_below_60:{len(negative_packets)}")
    if invalid_span_packets:
        manifest["blocking_issues"].append(f"invalid_span_packets:{len(invalid_span_packets)}")
    if duplicate_ids:
        manifest["blocking_issues"].append(f"duplicate_packet_ids:{len(duplicate_ids)}")
    manifest["blocking_issues"].extend(["positive_human_labels_incomplete", "claim_human_labels_incomplete"])
    return {
        "manifest": manifest,
        "packets": packets,
        "negative_labels": negative_labels,
        "negative_discovery_provenance": negative_discovery_provenance,
        "positive_annotation_template": positive_annotations,
        "claim_annotation_template": claim_annotations,
        "positive_source_span_audit": positive_source_audit,
    }


def _render_manifest(manifest: Mapping[str, Any]) -> str:
    lines = [
        "# P34-2 Judge Dataset Manifest",
        "",
        f"- packet_count: `{manifest['packet_count']}`",
        f"- packet_type_counts: `{manifest['packet_type_counts']}`",
        f"- positive_packet_count: `{manifest['positive_packet_count']}`",
        f"- positive_match_type_counts: `{manifest['positive_match_type_counts']}`",
        f"- negative_packet_count: `{manifest['negative_packet_count']}`",
        f"- negative_label_counts: `{manifest['negative_label_counts']}`",
        f"- claim_packet_count: `{manifest['claim_packet_count']}`",
        f"- invalid_span_packet_count: `{manifest['invalid_span_packet_count']}`",
        f"- packets_sha256: `{manifest['packets_sha256']}`",
        f"- frozen_negative_labels_sha256: `{manifest['frozen_negative_labels_sha256']}`",
        f"- negative_discovery_code_counts: `{manifest['negative_discovery_code_counts']}`",
        f"- negative_discovery_provenance_sha256: `{manifest['negative_discovery_provenance_sha256']}`",
        f"- ready_for_full_judge: `{manifest['ready_for_full_judge']}`",
        "",
        "## Blocking Issues",
        "",
    ]
    lines.extend(f"- `{item}`" for item in manifest["blocking_issues"])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runner-jsonl", required=True)
    parser.add_argument("--manual-negative-audit", required=True)
    parser.add_argument("--output-prefix", required=True)
    args = parser.parse_args()
    result = build_dataset(Path(args.runner_jsonl), Path(args.manual_negative_audit))
    prefix = Path(args.output_prefix)
    packet_path = Path(str(prefix) + "_PACKETS.jsonl")
    packet_path.write_bytes(b"".join(_canonical_json(packet) for packet in result["packets"]))
    outputs = {
        "_MANIFEST.json": result["manifest"],
        "_NEGATIVE_LABELS_FROZEN.json": {"labels": result["negative_labels"]},
        "_NEGATIVE_DISCOVERY_PROVENANCE.json": {"items": result["negative_discovery_provenance"]},
        "_POSITIVE_HUMAN_AUDIT_TEMPLATE.json": {"labels": result["positive_annotation_template"]},
        "_CLAIM_HUMAN_AUDIT_TEMPLATE.json": {"labels": result["claim_annotation_template"]},
        "_POSITIVE_SOURCE_SPAN_AUDIT.json": {"items": result["positive_source_span_audit"]},
    }
    for suffix, value in outputs.items():
        Path(str(prefix) + suffix).write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    Path(str(prefix) + "_MANIFEST.md").write_text(_render_manifest(result["manifest"]), encoding="utf-8")
    print(json.dumps(result["manifest"], ensure_ascii=False))
    return 0 if not [item for item in result["manifest"]["blocking_issues"] if "human_labels_incomplete" not in item] else 1


if __name__ == "__main__":
    raise SystemExit(main())
