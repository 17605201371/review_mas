#!/usr/bin/env python3
"""Orchestrate the provenance-safe P34 M/P 2x2 Judge experiment."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
from collections import Counter
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, List, Mapping, Sequence, Tuple

from scripts.p33_freeform_critique_probe import _disable_proxy_env_for_api, _load_dotenv
from scripts.p34_dual_model_judge_guard import MODEL_CODES
from scripts.p34_judge_runner import (
    TASK_VERDICTS,
    _label_target,
    _load_discovery_provenance,
    _load_jsonl,
    _load_labels_with_diagnostics,
    _load_paper_texts,
    run_experiment,
)


REQUIRED_TASK_TYPES = {"evidence_relation", "review_issue", "claim_faithfulness"}
MIN_POSITIVE_EVIDENCE_PAIRS = 80
MIN_REVIEW_AB_LABELS = 37
MIN_REVIEW_D_LABELS = 9
MIN_REVIEW_C_LABELS = 1
MIN_PAIRED_BOOTSTRAP_PACKETS = 30
DEFAULT_GATE_CONTRACT_PATH = Path("P34_2_GATE_CONTRACT_20260711.json")


def capability_thresholds() -> Dict[str, Any]:
    return {
        "minimum_cardinality": {
            "evidence_relation": MIN_POSITIVE_EVIDENCE_PAIRS,
            "review_issue_ab": MIN_REVIEW_AB_LABELS,
            "review_issue_d": MIN_REVIEW_D_LABELS,
            "review_issue_c": MIN_REVIEW_C_LABELS,
        },
        "schema_success_rate": 0.99,
        "test_retest_agreement": 0.85,
        "m_p_review_issue_verified_precision": 0.80,
        "m_p_review_issue_ab_verified_recall": 30 / 37,
        "m_p_review_issue_ab_verified_absolute_count": 30,
        "m_p_review_issue_d_verified_leakage_count": 0,
        "m_p_review_issue_abd_adjudication_coverage": 0.80,
        "m_p_positive_evidence_accuracy": 0.85,
        "m_p_positive_accepted_quote_span_locatability": 1.0,
        "m_p_macro_f1_gain": 0.08,
        "m_p_paired_bootstrap_minimum_packets": MIN_PAIRED_BOOTSTRAP_PACKETS,
        "m_p_paired_bootstrap_required_classes": ["rejected", "uncertain", "verified"],
    }


def load_gate_contract(path: Path) -> Dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or value.get("schema_version") != "p34_2_gate_contract_v1":
        raise ValueError("unsupported P34-2 gate contract schema")
    thresholds = value.get("thresholds")
    if not isinstance(thresholds, dict):
        raise ValueError("P34-2 gate contract must contain thresholds")
    expected = capability_thresholds()
    missing = sorted(set(expected) - set(thresholds))
    if missing:
        raise ValueError("P34-2 gate contract missing thresholds: " + ",".join(missing))
    cardinality = thresholds.get("minimum_cardinality")
    if not isinstance(cardinality, dict):
        raise ValueError("P34-2 gate contract minimum_cardinality must be an object")
    missing_cardinality = sorted(set(expected["minimum_cardinality"]) - set(cardinality))
    if missing_cardinality:
        raise ValueError("P34-2 gate contract missing cardinality: " + ",".join(missing_cardinality))
    for key, item in cardinality.items():
        if not isinstance(item, int) or item <= 0:
            raise ValueError(f"P34-2 gate contract cardinality must be positive: {key}")
    for key in (
        "schema_success_rate", "test_retest_agreement", "m_p_review_issue_verified_precision",
        "m_p_review_issue_ab_verified_recall", "m_p_review_issue_abd_adjudication_coverage",
        "m_p_positive_evidence_accuracy", "m_p_positive_accepted_quote_span_locatability",
    ):
        item = thresholds.get(key)
        if not isinstance(item, (int, float)) or not 0.0 <= float(item) <= 1.0:
            raise ValueError(f"P34-2 gate contract rate is invalid: {key}")
    for key in ("m_p_review_issue_ab_verified_absolute_count", "m_p_paired_bootstrap_minimum_packets"):
        item = thresholds.get(key)
        if not isinstance(item, int) or item <= 0:
            raise ValueError(f"P34-2 gate contract count is invalid: {key}")
    if thresholds.get("m_p_review_issue_d_verified_leakage_count") != 0:
        raise ValueError("P34-2 D leakage threshold must remain zero")
    gain = thresholds.get("m_p_macro_f1_gain")
    if not isinstance(gain, (int, float)) or not 0.0 < float(gain) <= 1.0:
        raise ValueError("P34-2 macro-F1 gain threshold is invalid")
    if sorted(thresholds.get("m_p_paired_bootstrap_required_classes") or []) != ["rejected", "uncertain", "verified"]:
        raise ValueError("P34-2 paired bootstrap classes are invalid")
    return dict(thresholds)


def _canonical_line(value: Mapping[str, Any]) -> bytes:
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")


def combine_packets(base_packets_path: Path, discovery_packets_path: Path) -> Tuple[List[Dict[str, Any]], List[str]]:
    base = [item for item in _load_jsonl(base_packets_path) if str(item.get("task_type") or "") != "review_issue"]
    discovery = [item for item in _load_jsonl(discovery_packets_path) if str(item.get("task_type") or "") == "review_issue"]
    packets = base + discovery
    packet_ids = [str(item.get("packet_id") or "") for item in packets]
    duplicates = sorted(packet_id for packet_id, count in Counter(packet_ids).items() if packet_id and count > 1)
    return packets, duplicates


def _packet_records(packet: Mapping[str, Any]):
    candidate = packet.get("candidate_evidence")
    if isinstance(candidate, dict):
        yield candidate
    for key in ("counterevidence_candidates", "retrieved_evidence", "claim_source_spans"):
        for item in packet.get(key, []) or []:
            if isinstance(item, dict):
                yield item


def validate_combined_preflight(
    packets: Sequence[Mapping[str, Any]],
    provenance: Mapping[str, Mapping[str, Any]],
    labels: Mapping[str, Mapping[str, Any]],
    paper_texts: Mapping[str, str],
    duplicates: Sequence[str],
    label_diagnostics: Mapping[str, Any] | None = None,
    thresholds: Mapping[str, Any] | None = None,
) -> Dict[str, Any]:
    thresholds = dict(thresholds or capability_thresholds())
    minimums = dict(thresholds["minimum_cardinality"])
    task_counts = Counter(str(item.get("task_type") or "") for item in packets)
    review_packets = [item for item in packets if str(item.get("task_type") or "") == "review_issue"]
    review_ids = {str(item.get("packet_id") or "") for item in review_packets}
    review_source_label_counts = Counter(
        str(labels.get(packet_id, {}).get("source_label") or labels.get(packet_id, {}).get("human_label") or "")
        for packet_id in review_ids
    )
    codes = Counter()
    missing_provenance = []
    for packet_id in sorted(review_ids):
        item = provenance.get(packet_id)
        if not item:
            missing_provenance.append(packet_id)
            continue
        for code in item.get("discovery_codes", []) or []:
            if str(code) in MODEL_CODES:
                codes[str(code)] += 1
    missing_labels = []
    invalid_label_contracts = []
    packet_ids = {str(item.get("packet_id") or "") for item in packets if str(item.get("packet_id") or "")}
    orphan_label_ids = sorted(set(labels) - packet_ids)
    duplicate_label_rows = list((label_diagnostics or {}).get("duplicates") or [])
    for item in packets:
        packet_id = str(item.get("packet_id") or "")
        task_type = str(item.get("task_type") or "")
        label = labels.get(packet_id, {})
        if task_type == "review_issue":
            complete = str(label.get("source_label") or label.get("human_label") or "") in {"A", "B", "C", "D"}
        else:
            complete = bool(str(label.get("human_label") or "").strip())
        if not complete:
            missing_labels.append(packet_id)
        else:
            target = _label_target(label, task_type)
            if (
                str(label.get("label_contract_version") or "") != "p34_label_contract_v1"
                or str(label.get("task_type") or "") != task_type
                or target not in TASK_VERDICTS.get(task_type, set())
            ):
                invalid_label_contracts.append(packet_id)
    invalid_spans = []
    for packet in packets:
        paper_id = str(packet.get("paper_id") or "")
        paper_text = str(paper_texts.get(paper_id) or "")
        if not paper_text:
            invalid_spans.append(str(packet.get("packet_id") or ""))
            continue
        for item in _packet_records(packet):
            start, end = item.get("source_span_start"), item.get("source_span_end")
            quote = str(item.get("quote") or "")
            if not isinstance(start, int) or not isinstance(end, int) or paper_text[start:end] != quote:
                invalid_spans.append(str(packet.get("packet_id") or ""))
                break
    issues = []
    missing_task_types = sorted(REQUIRED_TASK_TYPES - set(task_counts))
    if missing_task_types:
        issues.append("missing_task_types:" + ",".join(missing_task_types))
    if task_counts.get("evidence_relation", 0) < int(minimums["evidence_relation"]):
        issues.append(
            f"positive_evidence_pairs_below_minimum:{task_counts.get('evidence_relation', 0)}/{minimums['evidence_relation']}"
        )
    review_ab_count = review_source_label_counts["A"] + review_source_label_counts["B"]
    if review_ab_count < int(minimums["review_issue_ab"]):
        issues.append(f"review_issue_ab_labels_below_minimum:{review_ab_count}/{minimums['review_issue_ab']}")
    if review_source_label_counts["D"] < int(minimums["review_issue_d"]):
        issues.append(
            f"review_issue_d_labels_below_minimum:{review_source_label_counts['D']}/{minimums['review_issue_d']}"
        )
    if review_source_label_counts["C"] < int(minimums["review_issue_c"]):
        issues.append(
            f"review_issue_c_labels_below_minimum:{review_source_label_counts['C']}/{minimums['review_issue_c']}"
        )
    if duplicates:
        issues.append(f"duplicate_packet_ids:{len(duplicates)}")
    if duplicate_label_rows:
        issues.append(f"duplicate_label_packet_ids:{len(duplicate_label_rows)}")
    if orphan_label_ids:
        issues.append(f"orphan_label_packet_ids:{len(orphan_label_ids)}")
    if missing_provenance:
        issues.append(f"review_issue_packets_missing_provenance:{len(missing_provenance)}")
    for code in ("M", "P"):
        if codes.get(code, 0) == 0:
            issues.append(f"no_review_issue_packets_for_discovery_code:{code}")
    if missing_labels:
        issues.append(f"packets_missing_human_labels:{len(missing_labels)}")
    if invalid_label_contracts:
        issues.append(f"invalid_label_contracts:{len(invalid_label_contracts)}")
    if invalid_spans:
        issues.append(f"invalid_packet_spans:{len(invalid_spans)}")
    return {
        "status": "PASS" if not issues else "BLOCKED",
        "packet_count": len(packets),
        "task_counts": dict(task_counts),
        "review_issue_discovery_counts": dict(codes),
        "review_issue_source_label_counts": dict(review_source_label_counts),
        "minimum_cardinality": minimums,
        "duplicate_packet_ids": list(duplicates),
        "label_row_count": int((label_diagnostics or {}).get("row_count") or len(labels)),
        "label_unique_packet_count": len(labels),
        "duplicate_label_rows": duplicate_label_rows,
        "orphan_label_packet_ids": orphan_label_ids,
        "missing_provenance_packet_ids": missing_provenance,
        "missing_label_packet_ids": missing_labels,
        "invalid_label_contract_packet_ids": invalid_label_contracts,
        "invalid_span_packet_ids": sorted(set(invalid_spans)),
        "blocking_issues": issues,
    }


def discovery_cluster_metrics(
    packets: Sequence[Mapping[str, Any]],
    provenance: Mapping[str, Mapping[str, Any]],
    labels: Mapping[str, Mapping[str, Any]],
) -> Dict[str, Any]:
    packet_lookup = {str(item.get("packet_id") or ""): item for item in packets}
    metrics = {}
    for code in ("M", "P"):
        packet_ids = sorted(
            packet_id
            for packet_id, item in provenance.items()
            if code in set(item.get("discovery_codes", []) or []) and packet_id in packet_lookup
        )
        label_counts = Counter(
            str(labels.get(packet_id, {}).get("source_label") or labels.get(packet_id, {}).get("human_label") or "")
            for packet_id in packet_ids
        )
        adjudicated = sum(label_counts[label] for label in ("A", "B", "D"))
        valid = label_counts["A"] + label_counts["B"]
        valid_packets = [packet_lookup[packet_id] for packet_id in packet_ids if str(labels.get(packet_id, {}).get("source_label") or labels.get(packet_id, {}).get("human_label") or "") in {"A", "B"}]
        issue_types = {
            str((packet.get("issue_hypothesis") or {}).get("issue_type") or "other")
            for packet in valid_packets
        }
        metrics[code] = {
            "cluster_count": len(packet_ids),
            "label_counts": dict(label_counts),
            "adjudicated_precision_ab_over_abd": valid / adjudicated if adjudicated else None,
            "valid_cluster_count": valid,
            "valid_paper_coverage_count": len({str(packet.get("paper_id") or "") for packet in valid_packets}),
            "valid_issue_type_breadth": len(issue_types),
            "valid_issue_types": sorted(issue_types),
        }
    shared = sum(
        {"M", "P"}.issubset(set(item.get("discovery_codes", []) or []))
        for item in provenance.values()
        if str(item.get("packet_id") or "") in packet_lookup
    )
    return {"by_discovery_code": metrics, "shared_cross_model_cluster_count": shared}


def _task_metric(group: Mapping[str, Any], task_type: str, key: str) -> Any:
    return ((group.get("task_classification") or {}).get(task_type) or {}).get(key)


def _stable_predictions(
    reports: Mapping[str, Mapping[str, Any]],
    group: str,
    task_type: str,
) -> Dict[str, str]:
    by_packet: Dict[str, List[Mapping[str, Any]]] = {}
    expected_repeats = None
    for report in reports.values():
        if expected_repeats is None and report.get("repeat_count") is not None:
            expected_repeats = int(report.get("repeat_count") or 0)
        for case in report.get("final_cases", []) or []:
            if (
                str(case.get("group") or "") == group
                and str(case.get("task_type") or "") == task_type
            ):
                by_packet.setdefault(str(case.get("packet_id") or ""), []).append(case)
    stable = {}
    for packet_id, cases in by_packet.items():
        valid = [item for item in cases if item.get("valid")]
        if expected_repeats and len(valid) != expected_repeats:
            continue
        verdicts = {str(item.get("verdict") or "") for item in valid}
        if len(verdicts) == 1:
            stable[packet_id] = next(iter(verdicts))
    return stable


def _macro_f1_fixed_classes(rows: Sequence[Mapping[str, str]], classes: Sequence[str]) -> float:
    scores = []
    for label in classes:
        true_positive = sum(item["target"] == label and item["verdict"] == label for item in rows)
        false_positive = sum(item["target"] != label and item["verdict"] == label for item in rows)
        false_negative = sum(item["target"] == label and item["verdict"] != label for item in rows)
        precision = true_positive / (true_positive + false_positive) if true_positive + false_positive else 0.0
        recall = true_positive / (true_positive + false_negative) if true_positive + false_negative else 0.0
        scores.append(2 * precision * recall / (precision + recall) if precision + recall else 0.0)
    return sum(scores) / len(scores) if scores else 0.0


def paired_macro_f1_bootstrap(
    reports: Mapping[str, Mapping[str, Any]],
    labels: Mapping[str, Mapping[str, Any]],
    *,
    self_group: str,
    cross_group: str,
    task_type: str = "review_issue",
    samples: int = 2000,
    seed: int = 34,
) -> Dict[str, Any]:
    self_predictions = _stable_predictions(reports, self_group, task_type)
    cross_predictions = _stable_predictions(reports, cross_group, task_type)
    packet_ids = sorted(set(self_predictions) & set(cross_predictions))
    rows = []
    for packet_id in packet_ids:
        target = _label_target(labels.get(packet_id, {}), task_type)
        if target:
            rows.append({
                "packet_id": packet_id,
                "target": target,
                "self_verdict": self_predictions[packet_id],
                "cross_verdict": cross_predictions[packet_id],
            })
    classes = sorted({item["target"] for item in rows})
    if not rows or not classes:
        return {
            "self_group": self_group,
            "cross_group": cross_group,
            "paired_packet_count": 0,
            "classes": [],
            "self_macro_f1": None,
            "cross_macro_f1": None,
            "difference": None,
            "ci95_low": None,
            "ci95_high": None,
            "bootstrap_samples": samples,
            "seed": seed,
        }
    self_rows = [{"target": item["target"], "verdict": item["self_verdict"]} for item in rows]
    cross_rows = [{"target": item["target"], "verdict": item["cross_verdict"]} for item in rows]
    self_f1 = _macro_f1_fixed_classes(self_rows, classes)
    cross_f1 = _macro_f1_fixed_classes(cross_rows, classes)
    rng = random.Random(seed)
    differences = []
    for _ in range(max(1, samples)):
        sampled = [rows[rng.randrange(len(rows))] for _ in rows]
        sampled_self = [{"target": item["target"], "verdict": item["self_verdict"]} for item in sampled]
        sampled_cross = [{"target": item["target"], "verdict": item["cross_verdict"]} for item in sampled]
        differences.append(
            _macro_f1_fixed_classes(sampled_cross, classes)
            - _macro_f1_fixed_classes(sampled_self, classes)
        )
    differences.sort()
    low_index = int(0.025 * (len(differences) - 1))
    high_index = int(0.975 * (len(differences) - 1))
    return {
        "self_group": self_group,
        "cross_group": cross_group,
        "paired_packet_count": len(rows),
        "classes": classes,
        "self_macro_f1": self_f1,
        "cross_macro_f1": cross_f1,
        "difference": cross_f1 - self_f1,
        "ci95_low": differences[low_index],
        "ci95_high": differences[high_index],
        "bootstrap_samples": samples,
        "seed": seed,
    }


def aggregate_gate_reports(
    reports: Mapping[str, Mapping[str, Any]],
    preflight: Mapping[str, Any],
    labels: Mapping[str, Mapping[str, Any]] | None = None,
    bootstrap_samples: int = 2000,
    thresholds: Mapping[str, Any] | None = None,
) -> Dict[str, Any]:
    thresholds = dict(thresholds or capability_thresholds())
    group_metrics = {}
    blocking = list(preflight.get("blocking_issues", []))
    if blocking and not reports:
        return {
            "status": "BLOCKED",
            "group_metrics": {},
            "review_issue_macro_f1_comparison": {
                "M-M": None,
                "M-P": None,
                "M-P_minus_M-M": None,
                "P-P": None,
                "P-M": None,
                "P-M_minus_P-P": None,
            },
            "paired_bootstrap": {},
            "blocking_issues": list(dict.fromkeys(blocking)),
        }
    for report in reports.values():
        blocking.extend(str(item) for item in report.get("blocking_issues", []))
        group_metrics.update(report.get("metrics", {}))
    required_groups = {"M-M", "M-P", "P-M", "P-P"}
    missing_groups = sorted(required_groups - set(group_metrics))
    if missing_groups:
        blocking.append("missing_2x2_groups:" + ",".join(missing_groups))
    for group in sorted(required_groups & set(group_metrics)):
        values = group_metrics[group]
        if float(values.get("schema_success_rate") or 0.0) < float(thresholds["schema_success_rate"]):
            blocking.append(f"schema_success_below_0_99:{group}")
        if float(values.get("test_retest_agreement") or 0.0) < float(thresholds["test_retest_agreement"]):
            blocking.append(f"test_retest_below_0_85:{group}")
    primary = group_metrics.get("M-P", {})
    if primary:
        precision = primary.get("review_issue_verified_precision")
        recall = primary.get("review_issue_ab_verified_recall")
        recall_count = int(primary.get("review_issue_ab_verified_count") or 0)
        coverage = primary.get("review_issue_abd_adjudication_coverage")
        if precision is None or precision < float(thresholds["m_p_review_issue_verified_precision"]):
            blocking.append(f"m_p_verified_precision_below_0_80:{precision}")
        if recall is None or recall < float(thresholds["m_p_review_issue_ab_verified_recall"]):
            blocking.append(f"m_p_ab_recall_below_30_37:{recall}")
        if recall_count < int(thresholds["m_p_review_issue_ab_verified_absolute_count"]):
            blocking.append(f"m_p_ab_verified_count_below_30:{recall_count}")
        if int(primary.get("review_issue_d_verified_leakage_count") or 0) != int(thresholds["m_p_review_issue_d_verified_leakage_count"]):
            blocking.append(f"m_p_d_leakage_nonzero:{primary.get('review_issue_d_verified_leakage_count')}")
        if coverage is None or coverage < float(thresholds["m_p_review_issue_abd_adjudication_coverage"]):
            blocking.append(f"m_p_abd_coverage_below_0_80:{coverage}")
        positive_accuracy = _task_metric(primary, "evidence_relation", "accuracy")
        if positive_accuracy is None or positive_accuracy < float(thresholds["m_p_positive_evidence_accuracy"]):
            blocking.append(f"m_p_positive_accuracy_below_0_85:{positive_accuracy}")
        locatability = primary.get("evidence_relation_accepted_quote_span_locatability")
        if locatability is None or locatability < float(thresholds["m_p_positive_accepted_quote_span_locatability"]):
            blocking.append(f"m_p_positive_accepted_span_locatability_below_1_0:{locatability}")
    mm_review_f1 = _task_metric(group_metrics.get("M-M", {}), "review_issue", "macro_f1")
    mp_review_f1 = _task_metric(group_metrics.get("M-P", {}), "review_issue", "macro_f1")
    pp_review_f1 = _task_metric(group_metrics.get("P-P", {}), "review_issue", "macro_f1")
    pm_review_f1 = _task_metric(group_metrics.get("P-M", {}), "review_issue", "macro_f1")
    primary_gain = mp_review_f1 - mm_review_f1 if mp_review_f1 is not None and mm_review_f1 is not None else None
    reverse_gain = pm_review_f1 - pp_review_f1 if pm_review_f1 is not None and pp_review_f1 is not None else None
    paired_bootstrap = {}
    if labels is not None:
        paired_bootstrap = {
            "M-P_vs_M-M": paired_macro_f1_bootstrap(
                reports, labels, self_group="M-M", cross_group="M-P", samples=bootstrap_samples, seed=34
            ),
            "P-M_vs_P-P": paired_macro_f1_bootstrap(
                reports, labels, self_group="P-P", cross_group="P-M", samples=bootstrap_samples, seed=35
            ),
        }
    primary_ci_low = (paired_bootstrap.get("M-P_vs_M-M") or {}).get("ci95_low")
    primary_paired = paired_bootstrap.get("M-P_vs_M-M") or {}
    if labels is not None:
        paired_count = int(primary_paired.get("paired_packet_count") or 0)
        paired_minimum = int(thresholds["m_p_paired_bootstrap_minimum_packets"])
        if paired_count < paired_minimum:
            blocking.append(
                f"m_p_paired_bootstrap_packets_below_minimum:{paired_count}/{paired_minimum}"
            )
        required_classes = set(thresholds["m_p_paired_bootstrap_required_classes"])
        missing_classes = sorted(required_classes - set(primary_paired.get("classes") or []))
        if missing_classes:
            blocking.append("m_p_paired_bootstrap_missing_classes:" + ",".join(missing_classes))
    if not (
        primary_gain is not None
        and primary_gain >= float(thresholds["m_p_macro_f1_gain"])
        or primary_ci_low is not None
        and primary_ci_low > 0.0
    ):
        blocking.append(f"m_p_macro_f1_gain_or_ci_failed:gain={primary_gain}:ci_low={primary_ci_low}")
    return {
        "status": "PASS" if not blocking else "BLOCKED",
        "group_metrics": group_metrics,
        "review_issue_macro_f1_comparison": {
            "M-M": mm_review_f1,
            "M-P": mp_review_f1,
            "M-P_minus_M-M": primary_gain,
            "P-P": pp_review_f1,
            "P-M": pm_review_f1,
            "P-M_minus_P-P": reverse_gain,
        },
        "paired_bootstrap": paired_bootstrap,
        "blocking_issues": list(dict.fromkeys(blocking)),
    }


def run_2x2(args: argparse.Namespace) -> Dict[str, Any]:
    gate_contract_path = Path(getattr(args, "gate_contract", "") or DEFAULT_GATE_CONTRACT_PATH)
    gate_contract_issues = []
    try:
        thresholds = load_gate_contract(gate_contract_path)
    except Exception as exc:
        thresholds = capability_thresholds()
        gate_contract_issues.append(f"gate_contract_invalid:{type(exc).__name__}:{str(exc)[:300]}")
    base_path, discovery_path = Path(args.base_packets), Path(args.discovery_packets)
    provenance_path = Path(args.discovery_provenance)
    combined_packets, duplicates = combine_packets(base_path, discovery_path)
    combined_path = Path(str(args.output_prefix) + "_COMBINED_PACKETS.jsonl")
    combined_path.write_bytes(b"".join(_canonical_line(item) for item in combined_packets))
    provenance = _load_discovery_provenance(provenance_path)
    labels, label_diagnostics = _load_labels_with_diagnostics([Path(path) for path in args.labels])
    paper_texts = _load_paper_texts(Path(args.paper_source_jsonl))
    preflight = validate_combined_preflight(
        combined_packets, provenance, labels, paper_texts, duplicates, label_diagnostics, thresholds
    )
    if gate_contract_issues:
        preflight["blocking_issues"] = list(dict.fromkeys(preflight["blocking_issues"] + gate_contract_issues))
        preflight["status"] = "BLOCKED"
    discovery_metrics = discovery_cluster_metrics(combined_packets, provenance, labels)
    reports = {}
    configured_ledger_path = str(getattr(args, "ledger_path", "") or (str(args.output_prefix) + "_API_LEDGER.json"))
    checkpoint_batch_size = int(getattr(args, "checkpoint_batch_size", 8) or 8)
    if preflight["status"] == "PASS":
        common = {
            "packets": str(combined_path),
            "labels": list(args.labels),
            "discovery_provenance": str(provenance_path),
            "paper_source_jsonl": args.paper_source_jsonl,
            "packet_ids": [],
            "limit": 0,
            "judge_codes": ["M", "P"],
            "repeats": args.repeats,
            "run_api": args.run_api,
            "enforce_capability_gates": False,
            "max_tokens": args.max_tokens,
            "max_workers": args.max_workers,
            "timeout": args.timeout,
            "max_retries": args.max_retries,
            "ledger_path": configured_ledger_path,
            "checkpoint_batch_size": checkpoint_batch_size,
        }
        reports["M"] = run_experiment(SimpleNamespace(**common, discovery_code="M", task_types=sorted(REQUIRED_TASK_TYPES)))
        reports["P"] = run_experiment(SimpleNamespace(**common, discovery_code="P", task_types=["review_issue"]))
    aggregate = aggregate_gate_reports(reports, preflight, labels, args.bootstrap_samples, thresholds)
    prompt_blinding_by_discovery = {}
    for code, report in reports.items():
        audit = dict(report.get("prompt_blinding_audit") or {"status": "NOT_RUN"})
        prompt_blinding_by_discovery[code] = {
            "status": str(audit.get("status") or "NOT_RUN"),
            "request_count": int(audit.get("request_count") or 0),
            "issue_count": int(audit.get("issue_count") or 0),
            "manifest_sha256": str(audit.get("manifest_sha256") or ""),
            "issues": list(audit.get("issues") or []),
        }
    prompt_blinding_status = (
        "NOT_RUN" if not prompt_blinding_by_discovery
        else "PASS" if all(item.get("status") == "PASS" for item in prompt_blinding_by_discovery.values())
        else "BLOCKED"
    )
    prompt_blinding_manifest_sha256 = (
        hashlib.sha256(_canonical_line({
            code: item.get("manifest_sha256") for code, item in sorted(prompt_blinding_by_discovery.items())
        })).hexdigest()
        if prompt_blinding_by_discovery else ""
    )
    ledger_cache_hits = sum(int(report.get("request_ledger_cache_hit_count") or 0) for report in reports.values())
    ledger_api_requests = sum(int(report.get("request_ledger_api_request_count") or 0) for report in reports.values())
    return {
        "schema_version": "p34_2x2_experiment_v2",
        "status": aggregate["status"],
        "boundary": "Provenance-safe frozen 2x2 Judge experiment; no ReviewState mutation",
        "run_api": bool(args.run_api),
        "request_ledger_path": configured_ledger_path,
        "request_ledger_cache_hit_count": ledger_cache_hits,
        "request_ledger_api_request_count": ledger_api_requests,
        "request_ledger_prompt_storage": "sha256_only",
        "prompt_blinding_status": prompt_blinding_status,
        "prompt_blinding_manifest_sha256": prompt_blinding_manifest_sha256,
        "prompt_blinding_by_discovery": prompt_blinding_by_discovery,
        "models": {code: MODEL_CODES[code] for code in ("M", "P")},
        "gate_contract_path": str(gate_contract_path),
        "gate_contract_sha256": hashlib.sha256(gate_contract_path.read_bytes()).hexdigest() if gate_contract_path.exists() else "",
        "capability_thresholds": thresholds,
        "input_hashes": {
            "base_packets": hashlib.sha256(base_path.read_bytes()).hexdigest(),
            "discovery_packets": hashlib.sha256(discovery_path.read_bytes()).hexdigest(),
            "discovery_provenance": hashlib.sha256(provenance_path.read_bytes()).hexdigest(),
            "combined_packets": hashlib.sha256(combined_path.read_bytes()).hexdigest(),
            "labels": {path: hashlib.sha256(Path(path).read_bytes()).hexdigest() for path in args.labels},
            "gate_contract": hashlib.sha256(gate_contract_path.read_bytes()).hexdigest() if gate_contract_path.exists() else "",
        },
        "label_load_diagnostics": label_diagnostics,
        "combined_packets_path": str(combined_path),
        "preflight": preflight,
        "discovery_metrics": discovery_metrics,
        "reports": reports,
        **aggregate,
    }


def render_markdown(report: Mapping[str, Any]) -> str:
    lines = [
        "# P34 Provenance-Safe 2x2 Experiment", "",
        f"- status: **{report['status']}**",
        f"- run_api: `{report['run_api']}`",
        f"- preflight: `{report['preflight']['status']}`",
        f"- packet_counts: `{report['preflight']['task_counts']}`",
        f"- capability_thresholds: `{report['capability_thresholds']}`", "",
        f"- label_rows/unique: `{report['preflight']['label_row_count']}/{report['preflight']['label_unique_packet_count']}`",
        f"- duplicate_label_rows: `{len(report['preflight']['duplicate_label_rows'])}`",
        f"- orphan_label_rows: `{len(report['preflight']['orphan_label_packet_ids'])}`", "",
        f"- request_ledger_cache_hits: `{report.get('request_ledger_cache_hit_count', 0)}`",
        f"- request_ledger_api_requests: `{report.get('request_ledger_api_request_count', 0)}`", "",
        f"- prompt_blinding_status: `{report.get('prompt_blinding_status', 'NOT_RUN')}`",
        f"- prompt_blinding_manifest_sha256: `{report.get('prompt_blinding_manifest_sha256', '')}`", "",
        "## Discovery Metrics", "",
        f"`{report['discovery_metrics']}`", "",
        "## Review-Issue Macro-F1", "",
        f"`{report['review_issue_macro_f1_comparison']}`", "",
        "## Paired Bootstrap", "",
        f"`{report['paired_bootstrap']}`", "",
        "## Group Metrics", "",
    ]
    lines.extend(f"- `{group}`: `{metrics}`" for group, metrics in report["group_metrics"].items())
    lines.extend(["", "## Blocking Issues", ""])
    lines.extend(f"- `{item}`" for item in report["blocking_issues"]) if report["blocking_issues"] else lines.append("- none")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-packets", required=True)
    parser.add_argument("--discovery-packets", required=True)
    parser.add_argument("--discovery-provenance", required=True)
    parser.add_argument("--labels", nargs="+", required=True)
    parser.add_argument("--paper-source-jsonl", required=True)
    parser.add_argument("--repeats", type=int, default=2)
    parser.add_argument("--bootstrap-samples", type=int, default=2000)
    parser.add_argument("--gate-contract", default=str(DEFAULT_GATE_CONTRACT_PATH))
    parser.add_argument("--run-api", action="store_true")
    parser.add_argument("--env-file", default=".env")
    parser.add_argument("--max-tokens", type=int, default=2048)
    parser.add_argument("--max-workers", type=int, default=8)
    parser.add_argument("--timeout", type=float, default=180.0)
    parser.add_argument("--max-retries", type=int, default=4)
    parser.add_argument("--ledger-path", default="")
    parser.add_argument("--checkpoint-batch-size", type=int, default=8)
    parser.add_argument("--output-prefix", required=True)
    args = parser.parse_args()
    _load_dotenv(Path(args.env_file))
    _disable_proxy_env_for_api()
    MODEL_CODES["M"] = str(os.getenv("MIMO_MODEL") or MODEL_CODES["M"])
    MODEL_CODES["P"] = str(os.getenv("MIMO_PRO_MODEL") or MODEL_CODES["P"])
    report = run_2x2(args)
    Path(str(args.output_prefix) + "_REPORT.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    Path(str(args.output_prefix) + "_REPORT.md").write_text(render_markdown(report), encoding="utf-8")
    for code, subreport in report["reports"].items():
        Path(str(args.output_prefix) + f"_{code}_REPORT.json").write_text(json.dumps(subreport, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": report["status"],
        "preflight": {
            "status": report["preflight"]["status"],
            "packet_count": report["preflight"]["packet_count"],
            "task_counts": report["preflight"]["task_counts"],
            "review_issue_discovery_counts": report["preflight"]["review_issue_discovery_counts"],
            "missing_label_count": len(report["preflight"]["missing_label_packet_ids"]),
            "invalid_span_count": len(report["preflight"]["invalid_span_packet_ids"]),
        },
        "review_issue_macro_f1_comparison": report["review_issue_macro_f1_comparison"],
        "blocking_issues": report["blocking_issues"],
    }, ensure_ascii=False))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
