#!/usr/bin/env python3
"""Run label-blinded P34 Judge experiments over frozen AuditPackets."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from agent_system.environments.env_package.review.paper_index import build_paper_index
from agent_system.inference.review_runner import ApiReviewGenerator
from scripts.p33_freeform_critique_probe import _disable_proxy_env_for_api, _extract_json_object, _load_dotenv
from scripts.p34_dual_model_judge_guard import MODEL_CODES, augment_audit_packet, build_judge_prompt
from scripts.p34_request_ledger import RequestLedger, generate_resumable


TASK_VERDICTS = {
    "review_issue": {"verified", "rejected", "uncertain"},
    "evidence_relation": {"supports", "partially_supports", "contradicts", "unrelated", "uncertain"},
    "claim_faithfulness": {"faithful", "overstated", "unsupported_extraction", "uncertain"},
}

PROMPT_PACKET_MARKER = "\nAuditPacket: "


def _canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")


def _blinding_key_category(key: str) -> str:
    lowered = str(key or "").strip().lower()
    if (
        "label" in lowered
        or "reviewer" in lowered
        or "annotator" in lowered
        or "adjudicat" in lowered
        or lowered in {"manual_decision", "human_reason", "target_verdict", "target_verdict_mapping"}
    ):
        return "human_label_or_identity"
    if (
        lowered.startswith("_discovery_")
        or lowered.startswith("discovery_")
        or lowered in {"generator_identity", "generator_model", "source_candidate_id", "source_candidate_ids"}
    ):
        return "discovery_identity"
    return ""


def _packet_blinding_violations(value: Any, path: str = "packet") -> List[Dict[str, str]]:
    violations: List[Dict[str, str]] = []
    if isinstance(value, Mapping):
        for key, item in value.items():
            category = _blinding_key_category(str(key))
            item_path = f"{path}.{key}"
            if category:
                violations.append({"path": item_path, "key": str(key), "category": category})
            violations.extend(_packet_blinding_violations(item, item_path))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            violations.extend(_packet_blinding_violations(item, f"{path}[{index}]"))
    return violations


def audit_prompt_batch(
    requests: Sequence[Tuple[str, str]],
    metas: Sequence[Mapping[str, Any]],
    *,
    stage: str,
) -> Dict[str, Any]:
    issues = []
    manifest = []
    if len(requests) != len(metas):
        issues.append(f"request_meta_count_mismatch:{len(requests)}/{len(metas)}")
    for index, ((title, prompt), meta) in enumerate(zip(requests, metas)):
        packet = meta.get("packet") if isinstance(meta.get("packet"), Mapping) else {}
        packet_id = str(packet.get("packet_id") or "")
        violations = _packet_blinding_violations(packet)
        if violations:
            issues.append(f"forbidden_packet_fields:{packet_id}:{len(violations)}")
        embedded = None
        parse_error = ""
        if prompt.count(PROMPT_PACKET_MARKER) != 1:
            parse_error = "audit_packet_marker_count"
        else:
            try:
                embedded = json.loads(prompt.split(PROMPT_PACKET_MARKER, 1)[1])
            except Exception as exc:
                parse_error = f"embedded_packet_parse:{type(exc).__name__}"
        exact_match = embedded == packet if embedded is not None else False
        if parse_error:
            issues.append(f"prompt_packet_parse_failed:{packet_id}:{parse_error}")
        elif not exact_match:
            issues.append(f"prompt_packet_mismatch:{packet_id}")
        manifest.append({
            "index": index,
            "stage": stage,
            "packet_id": packet_id,
            "task_type": str(packet.get("task_type") or ""),
            "title_sha256": hashlib.sha256(str(title).encode("utf-8")).hexdigest(),
            "prompt_sha256": hashlib.sha256(str(prompt).encode("utf-8")).hexdigest(),
            "packet_sha256": hashlib.sha256(_canonical_json_bytes(packet)).hexdigest(),
            "embedded_packet_sha256": (
                hashlib.sha256(_canonical_json_bytes(embedded)).hexdigest() if isinstance(embedded, Mapping) else ""
            ),
            "embedded_packet_exact_match": exact_match,
            "forbidden_field_violations": violations,
        })
    manifest_sha256 = hashlib.sha256(_canonical_json_bytes(manifest)).hexdigest()
    return {
        "status": "PASS" if not issues else "BLOCKED",
        "stage": stage,
        "request_count": len(requests),
        "manifest_sha256": manifest_sha256,
        "issue_count": len(issues),
        "issues": issues,
        "items": manifest,
    }


def combine_prompt_blinding_audits(audits: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    stages = {str(item.get("stage") or f"stage-{index}"): dict(item) for index, item in enumerate(audits)}
    issues = [str(issue) for item in audits for issue in item.get("issues", []) or []]
    summary = {
        "status": "PASS" if not issues and all(item.get("status") == "PASS" for item in audits) else "BLOCKED",
        "request_count": sum(int(item.get("request_count") or 0) for item in audits),
        "issue_count": len(issues),
        "issues": issues,
        "stages": stages,
    }
    summary["manifest_sha256"] = hashlib.sha256(_canonical_json_bytes({
        key: value.get("manifest_sha256") for key, value in stages.items()
    })).hexdigest()
    return summary


def _load_jsonl(path: Path) -> List[Dict[str, Any]]:
    values = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"{path}:{line_no} must contain an object")
            values.append(value)
    return values


def _load_labels_with_diagnostics(paths: Sequence[Path]) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, Any]]:
    labels: Dict[str, Dict[str, Any]] = {}
    sources: Dict[str, str] = {}
    duplicates = []
    row_count = 0
    for path in paths:
        value = json.loads(path.read_text(encoding="utf-8"))
        rows = value.get("labels", []) if isinstance(value, dict) else []
        for item in rows:
            if not isinstance(item, dict) or not str(item.get("packet_id") or ""):
                continue
            row_count += 1
            packet_id = str(item["packet_id"])
            if packet_id in labels:
                duplicates.append({
                    "packet_id": packet_id,
                    "first_source": sources[packet_id],
                    "duplicate_source": str(path),
                    "identical": labels[packet_id] == item,
                })
                continue
            labels[packet_id] = item
            sources[packet_id] = str(path)
    return labels, {
        "source_paths": [str(path) for path in paths],
        "row_count": row_count,
        "unique_packet_count": len(labels),
        "duplicate_count": len(duplicates),
        "duplicates": duplicates,
        "packet_sources": sources,
    }


def _load_labels(paths: Sequence[Path]) -> Dict[str, Dict[str, Any]]:
    return _load_labels_with_diagnostics(paths)[0]


def _load_discovery_provenance(path: Path) -> Dict[str, Dict[str, Any]]:
    value = json.loads(path.read_text(encoding="utf-8"))
    rows = value.get("items", []) if isinstance(value, dict) else []
    if not isinstance(rows, list):
        raise ValueError(f"{path} must contain an items list")
    result = {}
    for item in rows:
        if not isinstance(item, dict):
            continue
        packet_id = str(item.get("packet_id") or "")
        discovery_codes = {
            str(code)
            for code in (
                item.get("discovery_codes", [])
                if isinstance(item.get("discovery_codes"), list)
                else [item.get("discovery_code")]
            )
            if str(code) in MODEL_CODES
        }
        if packet_id and discovery_codes:
            item = dict(item)
            item["discovery_codes"] = sorted(discovery_codes)
            result[packet_id] = dict(item)
    return result


def _apply_discovery_provenance_filter(
    packets: Sequence[Dict[str, Any]],
    discovery_code: str,
    provenance: Mapping[str, Mapping[str, Any]],
) -> Tuple[List[Dict[str, Any]], List[str]]:
    review_packets = [item for item in packets if str(item.get("task_type") or "") == "review_issue"]
    non_review_packets = [item for item in packets if str(item.get("task_type") or "") != "review_issue"]
    if not review_packets:
        return list(packets), []
    if not provenance:
        return non_review_packets, ["review_issue_discovery_provenance_missing"]
    missing = [
        str(item.get("packet_id") or "")
        for item in review_packets
        if str(item.get("packet_id") or "") not in provenance
    ]
    selected = [
        item
        for item in review_packets
        if discovery_code
        in set(provenance.get(str(item.get("packet_id") or ""), {}).get("discovery_codes", []))
    ]
    issues = []
    if missing:
        issues.append(f"review_issue_packets_missing_provenance:{len(missing)}")
    if not selected:
        issues.append(f"no_review_issue_packets_for_discovery_code:{discovery_code}")
    return non_review_packets + selected, issues


def _configuration_blocked_report(
    args: argparse.Namespace,
    packets_path: Path,
    packets: Sequence[Mapping[str, Any]],
    labels: Mapping[str, Mapping[str, Any]],
    issues: Sequence[str],
    provenance_path: Optional[Path],
    prompt_blinding_audit: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    blinding_status = str((prompt_blinding_audit or {}).get("status") or "NOT_RUN")
    return {
        "status": "BLOCKED",
        "boundary": "P34 label-blinded Judge sidecar; no ReviewState mutation",
        "run_api": bool(args.run_api),
        "discovery_code": args.discovery_code,
        "judge_codes": args.judge_codes,
        "models": {
            code: MODEL_CODES[code]
            for code in set([args.discovery_code] + args.judge_codes)
            if code in MODEL_CODES
        },
        "packets_path": str(packets_path),
        "packets_sha256": hashlib.sha256(packets_path.read_bytes()).hexdigest(),
        "discovery_provenance_path": str(provenance_path or ""),
        "discovery_provenance_sha256": (
            hashlib.sha256(provenance_path.read_bytes()).hexdigest() if provenance_path else ""
        ),
        "packet_count": len(packets),
        "packet_type_counts": dict(Counter(str(item.get("task_type") or "") for item in packets)),
        "label_count": len(labels),
        "labels_withheld_from_prompts": blinding_status != "BLOCKED",
        "generator_identity_withheld_from_prompts": blinding_status != "BLOCKED",
        "prompt_blinding_audit": dict(prompt_blinding_audit or {"status": "NOT_RUN", "stages": {}}),
        "repeat_count": args.repeats,
        "initial_valid_count": 0,
        "initial_expected_count": 0,
        "final_valid_count": 0,
        "final_expected_count": 0,
        "supplemental_retrieval_count": 0,
        "packet_span_roundtrip_ok": True,
        "api_errors": [],
        "metrics": {},
        "blocking_issues": list(issues),
        "initial_cases": [],
        "final_cases": [],
    }


def _load_paper_texts(path: Path) -> Dict[str, str]:
    texts = {}
    for row in _load_jsonl(path):
        state = row.get("review_state") if isinstance(row.get("review_state"), dict) else {}
        paper_id = str(row.get("paper_id") or state.get("paper_id") or "")
        if paper_id:
            texts[paper_id] = str(state.get("paper_text") or row.get("paper_text") or "")
    return texts


def _packet_ids(packet: Mapping[str, Any]) -> Tuple[set[str], set[str]]:
    evidence_ids = set()
    section_ids = set(str(item) for item in packet.get("searched_section_ids", []) or [])
    candidate = packet.get("candidate_evidence")
    if isinstance(candidate, dict):
        evidence_ids.add(str(candidate.get("evidence_id") or ""))
        if candidate.get("section_id"):
            section_ids.add(str(candidate["section_id"]))
    for key in ("retrieved_evidence", "counterevidence_candidates", "claim_source_spans"):
        for item in packet.get(key, []) or []:
            if not isinstance(item, dict):
                continue
            evidence_ids.add(str(item.get("evidence_id") or item.get("source_id") or ""))
            if item.get("section_id"):
                section_ids.add(str(item["section_id"]))
    evidence_ids.discard("")
    section_ids.discard("")
    return evidence_ids, section_ids


def build_task_prompt(packet: Mapping[str, Any], *, allow_supplemental: bool) -> str:
    task_type = str(packet.get("task_type") or "")
    if task_type == "review_issue":
        schema = {
            "verdict": "verified|rejected|uncertain",
            "defect_relation": "established|refuted|insufficient",
            "paper_anchor_valid": True,
            "counterevidence_resolves_issue": False,
            "required_evidence_satisfaction": "complete|partial|absent|not_applicable",
            "counterevidence_directness": "direct|indirect|none",
            "review_concern_remains": True,
            "paper_internal_verifiability": "yes|partial|no",
            "accepted_evidence_ids": ["evidence supporting the defect relation"],
            "counterevidence_ids": ["evidence refuting or resolving the issue"],
            "searched_section_ids": ["section id"],
            "confidence": 0.0,
            "rationale": "one sentence under 60 words",
            "supplemental_retrieval_request": "one query under 18 words" if allow_supplemental else "must be empty",
        }
        task = (
            "Judge the defect relation, not whether the paper's original claim has support. "
            "Evidence showing the supposedly missing table, ablation, baseline, protocol, or analysis is counterevidence that refutes the defect. "
            "A sentence asserting efficiency is not runtime, memory, FLOP, or complexity evidence. A sentence declaring a metric comparable is not a justification of cross-method comparability. "
            "Related but differently targeted ablations are indirect evidence and do not automatically resolve the requested ablation. "
            "A hypothesis that requires external literature, community-standard knowledge, or real-world prevalence not contained in the paper is not a verified paper-internal defect. "
            "Set paper_internal_verifiability=no when the decisive premise cannot be checked from the paper packet. "
            "Use verified when a material paper-facing concern remains after checking direct counterevidence. "
            "Use rejected only when direct evidence completely satisfies the verification contract or directly falsifies the alleged defect. "
            "Use uncertain when evidence is partial or search scope is insufficient."
        )
    elif task_type == "evidence_relation":
        schema = {
            "verdict": "supports|partially_supports|contradicts|unrelated|uncertain",
            "accepted_evidence_ids": ["candidate evidence id"],
            "counterevidence_ids": ["context evidence id"],
            "searched_section_ids": ["section id"],
            "confidence": 0.0,
            "rationale": "one sentence under 60 words",
            "supplemental_retrieval_request": "one query under 18 words" if allow_supplemental else "must be empty",
        }
        task = (
            "Judge whether candidate_evidence supports the claim. Distinguish partial support, contradiction, and unrelated text. "
            "Exact quotation alone does not establish the relation."
        )
    elif task_type == "claim_faithfulness":
        schema = {
            "verdict": "faithful|overstated|unsupported_extraction|uncertain",
            "accepted_evidence_ids": ["source id"],
            "counterevidence_ids": ["source id"],
            "searched_section_ids": ["section id"],
            "confidence": 0.0,
            "rationale": "one sentence under 60 words",
            "supplemental_retrieval_request": "one query under 18 words" if allow_supplemental else "must be empty",
        }
        task = (
            "Judge whether the extracted claim faithfully represents the cited paper sources, overstates them, or is unsupported extraction."
        )
    else:
        raise ValueError(f"unsupported task_type: {task_type}")
    retrieval_rule = (
        "If scope is insufficient, return uncertain and optionally request one precise search query under 18 words."
        if allow_supplemental
        else "One supplemental retrieval round is already complete; the request field must be empty."
    )
    evidence_ids, section_ids = _packet_ids(packet)
    return (
        "You are a blinded structured peer-review Judge. " + task + " " + retrieval_rule + " "
        "Use only ids in the packet. Never infer generator identity or human labels. Return one compact JSON object and stop.\n"
        f"Allowed evidence/source ids: {json.dumps(sorted(evidence_ids), ensure_ascii=False)}\n"
        f"Allowed section ids: {json.dumps(sorted(section_ids), ensure_ascii=False)}\n"
        f"Schema: {json.dumps(schema, ensure_ascii=False)}\n"
        f"AuditPacket: {json.dumps(packet, ensure_ascii=False)}"
    )


def parse_task_verdict(raw: str, packet: Mapping[str, Any]) -> Tuple[Dict[str, Any], str]:
    parsed, error = _extract_json_object(raw)
    if error or not isinstance(parsed, dict):
        return {}, error or "invalid_json"
    task_type = str(packet.get("task_type") or "")
    verdict = str(parsed.get("verdict") or "").strip().lower()
    if verdict not in TASK_VERDICTS.get(task_type, set()):
        return parsed, "invalid_verdict"
    if task_type == "review_issue":
        defect_relation = str(parsed.get("defect_relation") or "").strip().lower()
        if defect_relation not in {"established", "refuted", "insufficient"}:
            return parsed, "invalid_defect_relation"
        if not isinstance(parsed.get("paper_anchor_valid"), bool):
            return parsed, "invalid_paper_anchor_valid"
        if not isinstance(parsed.get("counterevidence_resolves_issue"), bool):
            return parsed, "invalid_counterevidence_resolves_issue"
        satisfaction = str(parsed.get("required_evidence_satisfaction") or "").strip().lower()
        directness = str(parsed.get("counterevidence_directness") or "").strip().lower()
        concern_remains = parsed.get("review_concern_remains")
        internal_verifiability = str(parsed.get("paper_internal_verifiability") or "").strip().lower()
        if satisfaction not in {"complete", "partial", "absent", "not_applicable"}:
            return parsed, "invalid_required_evidence_satisfaction"
        if directness not in {"direct", "indirect", "none"}:
            return parsed, "invalid_counterevidence_directness"
        if not isinstance(concern_remains, bool):
            return parsed, "invalid_review_concern_remains"
        if internal_verifiability not in {"yes", "partial", "no"}:
            return parsed, "invalid_paper_internal_verifiability"
        if verdict == "verified" and (
            defect_relation != "established"
            or parsed["counterevidence_resolves_issue"]
            or not concern_remains
            or satisfaction == "complete"
            or internal_verifiability != "yes"
        ):
            return parsed, "inconsistent_verified_verdict"
        if verdict == "rejected" and (
            internal_verifiability != "no"
            and (
                concern_remains
                or not parsed["counterevidence_resolves_issue"]
                or directness != "direct"
                or satisfaction not in {"complete", "not_applicable"}
            )
        ):
            return parsed, "inconsistent_rejected_verdict"
        if verdict == "uncertain" and (
            defect_relation != "insufficient"
            or satisfaction not in {"partial", "absent"}
            or internal_verifiability == "yes" and satisfaction == "absent"
        ):
            return parsed, "inconsistent_uncertain_verdict"
    evidence_ids, section_ids = _packet_ids(packet)
    used_evidence = set()
    for key in ("accepted_evidence_ids", "counterevidence_ids"):
        values = parsed.get(key, [])
        if not isinstance(values, list):
            return parsed, f"invalid_{key}"
        used_evidence.update(str(item) for item in values)
    used_sections = parsed.get("searched_section_ids", [])
    if not isinstance(used_sections, list):
        return parsed, "invalid_searched_section_ids"
    if not used_evidence.issubset(evidence_ids):
        return parsed, "unknown_evidence_id"
    if not set(str(item) for item in used_sections).issubset(section_ids):
        return parsed, "unknown_section_id"
    if not str(parsed.get("rationale") or "").strip():
        return parsed, "missing_rationale"
    return parsed, ""


def _selected_packets(packets: Sequence[Dict[str, Any]], task_types: Sequence[str], limit: int, packet_ids: Sequence[str]) -> List[Dict[str, Any]]:
    allowed_types = set(task_types)
    wanted = set(packet_ids)
    selected = [
        packet for packet in packets
        if (not allowed_types or str(packet.get("task_type") or "") in allowed_types)
        and (not wanted or str(packet.get("packet_id") or "") in wanted)
    ]
    return selected[:limit] if limit > 0 else selected


def _case_record(meta: Mapping[str, Any], raw: str) -> Dict[str, Any]:
    parsed, error = parse_task_verdict(raw, meta["packet"])
    return {
        "group": meta["group"],
        "packet_id": meta["packet"]["packet_id"],
        "paper_id": meta["packet"]["paper_id"],
        "task_type": meta["packet"]["task_type"],
        "repeat": meta["repeat"],
        "judge_model": meta["judge_model"],
        "valid": not error,
        "error": error,
        "verdict": str(parsed.get("verdict") or ""),
        "parsed": parsed,
        "raw_response": raw,
    }


def _label_target(label: Mapping[str, Any], task_type: str) -> str:
    direct = str(label.get("target_verdict_mapping") or "")
    if direct:
        return direct
    if task_type == "review_issue":
        return {
            "A": "verified",
            "B": "verified",
            "C": "uncertain",
            "D": "rejected",
        }.get(str(label.get("human_label") or ""), "")
    return str(label.get("human_label") or "")


def _classification_metrics(rows: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    labeled = [
        (str(item.get("target") or ""), str(item.get("verdict") or ""))
        for item in rows
        if str(item.get("target") or "")
    ]
    classes = sorted({target for target, _ in labeled})
    confusion = {
        target: dict(Counter(prediction for row_target, prediction in labeled if row_target == target))
        for target in classes
    }
    per_class = {}
    for label in classes:
        true_positive = sum(target == label and prediction == label for target, prediction in labeled)
        false_positive = sum(target != label and prediction == label for target, prediction in labeled)
        false_negative = sum(target == label and prediction != label for target, prediction in labeled)
        precision = true_positive / (true_positive + false_positive) if true_positive + false_positive else 0.0
        recall = true_positive / (true_positive + false_negative) if true_positive + false_negative else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        per_class[label] = {
            "support": sum(target == label for target, _ in labeled),
            "precision": precision,
            "recall": recall,
            "f1": f1,
        }
    return {
        "labeled_count": len(labeled),
        "accuracy": sum(target == prediction for target, prediction in labeled) / len(labeled) if labeled else None,
        "macro_f1": sum(item["f1"] for item in per_class.values()) / len(per_class) if per_class else None,
        "classes": classes,
        "per_class": per_class,
        "confusion": confusion,
    }


def score_cases(cases: Sequence[Mapping[str, Any]], labels: Mapping[str, Mapping[str, Any]], repeats: int) -> Dict[str, Any]:
    by_group: Dict[str, List[Mapping[str, Any]]] = defaultdict(list)
    for case in cases:
        by_group[str(case.get("group") or "")].append(case)
    group_metrics = {}
    for group, group_cases in sorted(by_group.items()):
        by_packet: Dict[str, List[Mapping[str, Any]]] = defaultdict(list)
        for case in group_cases:
            by_packet[str(case.get("packet_id") or "")].append(case)
        stable = sum(
            len(items) == repeats and all(item.get("valid") for item in items) and len({item.get("verdict") for item in items}) == 1
            for items in by_packet.values()
        )
        adjudicated = []
        stable_by_packet = {}
        for packet_id, items in by_packet.items():
            valid = [item for item in items if item.get("valid")]
            if len(valid) != repeats or len({item.get("verdict") for item in valid}) != 1:
                continue
            target = _label_target(labels.get(packet_id, {}), str(valid[0].get("task_type") or ""))
            row = {
                "packet_id": packet_id,
                "verdict": valid[0]["verdict"],
                "target": target,
                "task_type": valid[0]["task_type"],
                "parsed": valid[0].get("parsed") or {},
            }
            adjudicated.append(row)
            stable_by_packet[packet_id] = row
        labeled = [item for item in adjudicated if item["target"]]
        classification = _classification_metrics(labeled)
        task_classification = {
            task_type: _classification_metrics([item for item in labeled if item["task_type"] == task_type])
            for task_type in sorted({item["task_type"] for item in labeled})
        }
        review_packet_ids = [
            packet_id for packet_id, items in by_packet.items()
            if items and str(items[0].get("task_type") or "") == "review_issue"
        ]
        review_labels = {
            packet_id: str(labels.get(packet_id, {}).get("source_label") or labels.get(packet_id, {}).get("human_label") or "")
            for packet_id in review_packet_ids
        }
        ab_ids = [packet_id for packet_id in review_packet_ids if review_labels[packet_id] in {"A", "B"}]
        d_ids = [packet_id for packet_id in review_packet_ids if review_labels[packet_id] == "D"]
        c_ids = [packet_id for packet_id in review_packet_ids if review_labels[packet_id] == "C"]
        stable_review = [stable_by_packet[packet_id] for packet_id in review_packet_ids if packet_id in stable_by_packet]
        verified = [item for item in stable_review if item["verdict"] == "verified"]
        true_verified = [item for item in verified if review_labels[item["packet_id"]] in {"A", "B"}]
        ab_verified_count = sum(
            packet_id in stable_by_packet and stable_by_packet[packet_id]["verdict"] == "verified"
            for packet_id in ab_ids
        )
        abd_non_uncertain_count = sum(
            packet_id in stable_by_packet and stable_by_packet[packet_id]["verdict"] != "uncertain"
            for packet_id in ab_ids + d_ids
        )
        c_uncertain_count = sum(
            packet_id in stable_by_packet and stable_by_packet[packet_id]["verdict"] == "uncertain"
            for packet_id in c_ids
        )
        evidence_rows = [item for item in adjudicated if item["task_type"] == "evidence_relation"]
        decisive_evidence_rows = [item for item in evidence_rows if item["verdict"] != "uncertain"]
        locatable_evidence_rows = [
            item for item in decisive_evidence_rows
            if isinstance(item.get("parsed", {}).get("accepted_evidence_ids"), list)
            and bool(item["parsed"]["accepted_evidence_ids"])
        ]
        group_metrics[group] = {
            "case_count": len(group_cases),
            "packet_count": len(by_packet),
            "schema_success_rate": sum(bool(item.get("valid")) for item in group_cases) / len(group_cases) if group_cases else 0.0,
            "test_retest_agreement": stable / len(by_packet) if by_packet else 0.0,
            "adjudicated_packet_count": len(adjudicated),
            "labeled_packet_count": len(labeled),
            "labeled_accuracy": classification["accuracy"],
            "labeled_macro_f1": classification["macro_f1"],
            "classification": classification,
            "task_classification": task_classification,
            "review_issue_verified_precision": len(true_verified) / len(verified) if verified else None,
            "review_issue_verified_absolute_count": len(verified),
            "review_issue_ab_label_count": len(ab_ids),
            "review_issue_ab_verified_count": ab_verified_count,
            "review_issue_ab_verified_recall": ab_verified_count / len(ab_ids) if ab_ids else None,
            "review_issue_d_verified_leakage_count": sum(
                packet_id in stable_by_packet and stable_by_packet[packet_id]["verdict"] == "verified"
                for packet_id in d_ids
            ),
            "review_issue_d_count": len(d_ids),
            "review_issue_abd_adjudication_coverage": (
                abd_non_uncertain_count / (len(ab_ids) + len(d_ids)) if ab_ids or d_ids else None
            ),
            "review_issue_c_count": len(c_ids),
            "review_issue_c_to_uncertain_count": c_uncertain_count,
            "review_issue_c_to_uncertain_rate": c_uncertain_count / len(c_ids) if c_ids else None,
            "evidence_relation_decisive_count": len(decisive_evidence_rows),
            "evidence_relation_accepted_quote_span_locatable_count": len(locatable_evidence_rows),
            "evidence_relation_accepted_quote_span_locatability": (
                len(locatable_evidence_rows) / len(decisive_evidence_rows) if decisive_evidence_rows else None
            ),
            "verdict_counts": dict(Counter(str(item.get("verdict") or "") for item in group_cases if item.get("valid"))),
        }
    return group_metrics


def run_experiment(args: argparse.Namespace) -> Dict[str, Any]:
    packets_path = Path(args.packets)
    packets = _selected_packets(_load_jsonl(packets_path), args.task_types, 0, args.packet_ids)
    labels = _load_labels([Path(path) for path in args.labels])
    provenance_path = Path(args.discovery_provenance) if args.discovery_provenance else None
    provenance = _load_discovery_provenance(provenance_path) if provenance_path else {}
    packets, provenance_issues = _apply_discovery_provenance_filter(
        packets, args.discovery_code, provenance
    )
    if provenance_issues:
        return _configuration_blocked_report(
            args, packets_path, packets, labels, provenance_issues, provenance_path
        )
    if args.limit > 0:
        packets = packets[: args.limit]
    paper_texts = _load_paper_texts(Path(args.paper_source_jsonl))
    judge_system_prompt = "Return exactly one compact JSON object. No chain-of-thought or markdown."
    generators = {
        code: ApiReviewGenerator(
            model=MODEL_CODES[code], provider="mimo", temperature=0.0, top_p=1.0,
            max_tokens=args.max_tokens, max_workers=args.max_workers,
            timeout=args.timeout, max_retries=args.max_retries,
            system_prompt=judge_system_prompt,
        )
        for code in args.judge_codes
    } if args.run_api else {}
    ledger_path_value = str(getattr(args, "ledger_path", "") or "")
    ledger = RequestLedger(Path(ledger_path_value)) if args.run_api and ledger_path_value else None
    checkpoint_batch_size = int(getattr(args, "checkpoint_batch_size", 8) or 8)
    request_ledger_stats: List[Dict[str, Any]] = []

    def execute_requests(
        stage: str,
        judge_code: str,
        requests: Sequence[Tuple[str, str]],
        metas: Sequence[Mapping[str, Any]],
    ) -> Tuple[List[Optional[str]], List[Dict[str, Any]]]:
        if not args.run_api:
            responses = [
                '{"verdict":"uncertain","accepted_evidence_ids":[],"counterevidence_ids":[],"searched_section_ids":[],"confidence":0.0,"rationale":"dry run","supplemental_retrieval_request":""}'
            ] * len(requests)
            request_ledger_stats.append({
                "stage": stage, "judge_code": judge_code, "request_count": len(requests),
                "cache_hit_count": 0, "api_request_count": 0, "new_success_count": 0, "error_count": 0,
            })
            return responses, []
        contexts = [
            {
                "stage": stage,
                "judge_code": judge_code,
                "group": str(meta.get("group") or ""),
                "packet_id": str((meta.get("packet") or {}).get("packet_id") or ""),
                "task_type": str((meta.get("packet") or {}).get("task_type") or ""),
                "repeat": int(meta.get("repeat") or 0),
            }
            for meta in metas
        ]
        generation_config = {
            "provider": "mimo",
            "base_url": str(os.getenv("MIMO_BASE_URL") or "https://api.xiaomimimo.com/v1"),
            "model": MODEL_CODES[judge_code],
            "temperature": 0.0,
            "top_p": 1.0,
            "max_tokens": args.max_tokens,
            "system_prompt": judge_system_prompt,
            "json_response_format": str(os.getenv("DRMAS_JSON_RESPONSE_FORMAT") or "auto"),
        }
        if ledger is None:
            raise ValueError("run_api requires a request ledger path")
        responses, errors, stats = generate_resumable(
            generators[judge_code], requests, contexts, generation_config, ledger, checkpoint_batch_size
        )
        request_ledger_stats.append({"stage": stage, "judge_code": judge_code, **stats})
        return responses, errors

    initial_requests: Dict[str, List[Tuple[str, str]]] = {code: [] for code in args.judge_codes}
    initial_meta: Dict[str, List[Dict[str, Any]]] = {code: [] for code in args.judge_codes}
    for judge_code in args.judge_codes:
        group = args.discovery_code + "-" + judge_code
        for packet in packets:
            initial_requests[judge_code].append((f"P34 Initial Judge {group}", build_task_prompt(packet, allow_supplemental=True)))
            initial_meta[judge_code].append({"group": group, "packet": packet, "repeat": 0, "judge_model": MODEL_CODES[judge_code]})
    initial_blinding = combine_prompt_blinding_audits([
        audit_prompt_batch(
            initial_requests[judge_code], initial_meta[judge_code], stage=f"initial:{judge_code}"
        )
        for judge_code in args.judge_codes
    ])
    if initial_blinding["status"] != "PASS":
        return _configuration_blocked_report(
            args,
            packets_path,
            packets,
            labels,
            [f"prompt_blinding_failed:{item}" for item in initial_blinding["issues"]],
            provenance_path,
            initial_blinding,
        )
    initial_cases = []
    api_errors: List[Dict[str, str]] = []
    for judge_code in args.judge_codes:
        responses, errors = execute_requests(
            "initial", judge_code, initial_requests[judge_code], initial_meta[judge_code]
        )
        error_by_index = {int(item["index"]): item for item in errors}
        for index, (meta, raw) in enumerate(zip(initial_meta[judge_code], responses)):
            if raw is not None:
                initial_cases.append(_case_record(meta, raw))
                continue
            error = error_by_index.get(index, {"error_type": "MissingResponse", "message": "missing response"})
            api_errors.append({
                "stage": "initial",
                "judge_code": judge_code,
                "error_type": str(error["error_type"]),
                "message": str(error["message"])[:500],
            })
            initial_cases.append({
                "group": meta["group"],
                "packet_id": meta["packet"]["packet_id"],
                "paper_id": meta["packet"]["paper_id"],
                "task_type": meta["packet"]["task_type"],
                "repeat": meta["repeat"],
                "judge_model": meta["judge_model"],
                "valid": False,
                "error": f"api_error:{error['error_type']}",
                "verdict": "",
                "parsed": {},
                "raw_response": "",
            })

    final_requests: Dict[str, List[Tuple[str, str]]] = {code: [] for code in args.judge_codes}
    final_meta: Dict[str, List[Dict[str, Any]]] = {code: [] for code in args.judge_codes}
    packet_span_roundtrip_ok = True
    for case in initial_cases:
        if not case["valid"]:
            continue
        packet = next(packet for packet in packets if packet["packet_id"] == case["packet_id"])
        request = str(case["parsed"].get("supplemental_retrieval_request") or "").strip()
        supplemental = bool(case["verdict"] == "uncertain" and request)
        final_packet = packet
        if supplemental:
            paper_text = paper_texts.get(str(packet.get("paper_id") or ""), "")
            if paper_text:
                final_packet = augment_audit_packet(packet, build_paper_index(paper_text), request)
                for item in final_packet.get("retrieved_evidence", []):
                    start, end = item.get("source_span_start"), item.get("source_span_end")
                    if not isinstance(start, int) or not isinstance(end, int) or paper_text[start:end] != str(item.get("quote") or ""):
                        packet_span_roundtrip_ok = False
        judge_code = case["group"].split("-")[1]
        prompt = build_task_prompt(final_packet, allow_supplemental=False)
        for repeat in range(1, args.repeats + 1):
            final_requests[judge_code].append((f"P34 Final Judge {case['group']}", prompt))
            final_meta[judge_code].append({
                "group": case["group"], "packet": final_packet, "repeat": repeat,
                "judge_model": MODEL_CODES[judge_code], "initial_case": case,
                "supplemental_retrieval_performed": supplemental,
            })
    final_stage_audits = [
        audit_prompt_batch(final_requests[judge_code], final_meta[judge_code], stage=f"final:{judge_code}")
        for judge_code in args.judge_codes
    ]
    prompt_blinding_audit = combine_prompt_blinding_audits([
        *list(initial_blinding["stages"].values()),
        *final_stage_audits,
    ])
    final_cases = []
    if prompt_blinding_audit["status"] == "PASS":
        for judge_code in args.judge_codes:
            responses, errors = execute_requests(
                "final", judge_code, final_requests[judge_code], final_meta[judge_code]
            )
            error_by_index = {int(item["index"]): item for item in errors}
            for index, (meta, raw) in enumerate(zip(final_meta[judge_code], responses)):
                if raw is not None:
                    record = _case_record(meta, raw)
                    record["initial_verdict"] = meta["initial_case"]["verdict"]
                    record["supplemental_retrieval_performed"] = meta["supplemental_retrieval_performed"]
                    final_cases.append(record)
                    continue
                error = error_by_index.get(index, {"error_type": "MissingResponse", "message": "missing response"})
                api_errors.append({
                    "stage": "final",
                    "judge_code": judge_code,
                    "error_type": str(error["error_type"]),
                    "message": str(error["message"])[:500],
                })
                final_cases.append({
                    "group": meta["group"],
                    "packet_id": meta["packet"]["packet_id"],
                    "paper_id": meta["packet"]["paper_id"],
                    "task_type": meta["packet"]["task_type"],
                    "repeat": meta["repeat"],
                    "judge_model": meta["judge_model"],
                    "valid": False,
                    "error": f"api_error:{error['error_type']}",
                    "verdict": "",
                    "parsed": {},
                    "raw_response": "",
                    "initial_verdict": meta["initial_case"]["verdict"],
                    "supplemental_retrieval_performed": meta["supplemental_retrieval_performed"],
                })
    metrics = score_cases(final_cases, labels, args.repeats)
    blocking = []
    if prompt_blinding_audit["status"] != "PASS":
        blocking.extend(f"prompt_blinding_failed:{item}" for item in prompt_blinding_audit["issues"])
    blocking.extend(
        f"api_error:{item['stage']}:{item['judge_code']}:{item['error_type']}"
        for item in api_errors
    )
    expected_initial = len(packets) * len(args.judge_codes)
    expected_final = expected_initial * args.repeats
    if sum(case["valid"] for case in initial_cases) != expected_initial:
        blocking.append("initial_schema_failure")
    if sum(case["valid"] for case in final_cases) != expected_final:
        blocking.append("final_schema_failure")
    if not packet_span_roundtrip_ok:
        blocking.append("supplemental_span_roundtrip_failure")
    for group, values in metrics.items():
        if values["test_retest_agreement"] < 0.85:
            blocking.append(f"test_retest_below_0_85:{group}")
        if args.enforce_capability_gates and group.endswith("-P"):
            precision = values.get("review_issue_verified_precision")
            recall = values.get("review_issue_ab_verified_recall")
            coverage = values.get("review_issue_abd_adjudication_coverage")
            if precision is None or precision < 0.8:
                blocking.append(f"verified_precision_below_0_80:{group}:{precision}")
            if recall is None or recall < (30 / 37):
                blocking.append(f"ab_verified_recall_below_30_37:{group}:{recall}")
            if int(values.get("review_issue_d_verified_leakage_count") or 0) != 0:
                blocking.append(f"d_verified_leakage_nonzero:{group}:{values.get('review_issue_d_verified_leakage_count')}")
            if coverage is None or coverage < 0.8:
                blocking.append(f"abd_coverage_below_0_80:{group}:{coverage}")
    return {
        "status": "PASS" if not blocking else "BLOCKED",
        "boundary": "P34 label-blinded Judge sidecar; no ReviewState mutation",
        "run_api": bool(args.run_api),
        "discovery_code": args.discovery_code,
        "judge_codes": args.judge_codes,
        "models": {code: MODEL_CODES[code] for code in set([args.discovery_code] + args.judge_codes) if code in MODEL_CODES},
        "packets_path": str(packets_path),
        "packets_sha256": hashlib.sha256(packets_path.read_bytes()).hexdigest(),
        "discovery_provenance_path": str(provenance_path or ""),
        "discovery_provenance_sha256": (
            hashlib.sha256(provenance_path.read_bytes()).hexdigest() if provenance_path else ""
        ),
        "packet_count": len(packets),
        "packet_type_counts": dict(Counter(packet["task_type"] for packet in packets)),
        "label_count": len(labels),
        "labels_withheld_from_prompts": prompt_blinding_audit["status"] == "PASS",
        "generator_identity_withheld_from_prompts": prompt_blinding_audit["status"] == "PASS",
        "prompt_blinding_audit": prompt_blinding_audit,
        "repeat_count": args.repeats,
        "initial_valid_count": sum(case["valid"] for case in initial_cases),
        "initial_expected_count": expected_initial,
        "final_valid_count": sum(case["valid"] for case in final_cases),
        "final_expected_count": expected_final,
        "supplemental_retrieval_count": sum(case.get("supplemental_retrieval_performed", False) for case in final_cases) // max(1, args.repeats),
        "packet_span_roundtrip_ok": packet_span_roundtrip_ok,
        "api_errors": api_errors,
        "request_ledger_path": ledger_path_value,
        "request_ledger_stats": request_ledger_stats,
        "request_ledger_cache_hit_count": sum(item["cache_hit_count"] for item in request_ledger_stats),
        "request_ledger_api_request_count": sum(item["api_request_count"] for item in request_ledger_stats),
        "metrics": metrics,
        "blocking_issues": blocking,
        "initial_cases": initial_cases,
        "final_cases": final_cases,
    }


def render_markdown(report: Mapping[str, Any]) -> str:
    lines = [
        "# P34 Judge Experiment",
        "",
        f"- status: **{report['status']}**",
        f"- run_api: `{report['run_api']}`",
        f"- packet_count: `{report['packet_count']}`",
        f"- packet_type_counts: `{report['packet_type_counts']}`",
        f"- initial_schema: `{report['initial_valid_count']}/{report['initial_expected_count']}`",
        f"- final_schema: `{report['final_valid_count']}/{report['final_expected_count']}`",
        f"- supplemental_retrieval_count: `{report['supplemental_retrieval_count']}`",
        f"- packet_span_roundtrip_ok: `{report['packet_span_roundtrip_ok']}`",
        f"- api_error_count: `{len(report.get('api_errors', []))}`",
        f"- request_ledger_cache_hits: `{report.get('request_ledger_cache_hit_count', 0)}`",
        f"- request_ledger_api_requests: `{report.get('request_ledger_api_request_count', 0)}`",
        "",
        "## Metrics",
        "",
    ]
    for group, metrics in report["metrics"].items():
        lines.append(f"- `{group}`: `{metrics}`")
    lines.extend(["", "## API Errors", ""])
    lines.extend(f"- `{item}`" for item in report.get("api_errors", [])) if report.get("api_errors") else lines.append("- none")
    lines.extend(["", "## Blocking Issues", ""])
    lines.extend(f"- `{item}`" for item in report["blocking_issues"]) if report["blocking_issues"] else lines.append("- none")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packets", required=True)
    parser.add_argument("--labels", nargs="*", default=[])
    parser.add_argument("--discovery-provenance")
    parser.add_argument("--paper-source-jsonl", required=True)
    parser.add_argument("--task-types", nargs="*", default=[])
    parser.add_argument("--packet-ids", nargs="*", default=[])
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--discovery-code", choices=["M", "P"], required=True)
    parser.add_argument("--judge-codes", nargs="+", choices=["M", "P"], default=["M", "P"])
    parser.add_argument("--repeats", type=int, default=2)
    parser.add_argument("--run-api", action="store_true")
    parser.add_argument("--enforce-capability-gates", action="store_true")
    parser.add_argument("--env-file", default=".env")
    parser.add_argument("--max-tokens", type=int, default=2048)
    parser.add_argument("--max-workers", type=int, default=8)
    parser.add_argument("--timeout", type=float, default=180.0)
    parser.add_argument("--max-retries", type=int, default=4)
    parser.add_argument("--ledger-path", default="")
    parser.add_argument("--checkpoint-batch-size", type=int, default=8)
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--output-md", required=True)
    args = parser.parse_args()
    if args.run_api and not args.ledger_path:
        args.ledger_path = str(Path(args.output_json).with_suffix(".ledger.json"))
    _load_dotenv(Path(args.env_file))
    _disable_proxy_env_for_api()
    MODEL_CODES["M"] = str(os.getenv("MIMO_MODEL") or MODEL_CODES["M"])
    MODEL_CODES["P"] = str(os.getenv("MIMO_PRO_MODEL") or MODEL_CODES["P"])
    report = run_experiment(args)
    Path(args.output_json).write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    Path(args.output_md).write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("status", "packet_count", "initial_valid_count", "initial_expected_count", "final_valid_count", "final_expected_count", "metrics", "blocking_issues")}, ensure_ascii=False))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
