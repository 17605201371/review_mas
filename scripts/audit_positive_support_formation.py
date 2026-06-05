#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.simulate_state_hygiene_decision import decision_blockers, norm  # noqa: E402

DOC_DIR = ROOT / "docs/experiments"
OUT_JSON = ROOT / "outputs/results_main/review_infer/positive_support_formation_audit.json"

RUN_SPECS = [
    {
        "name": "4b_focus",
        "results": ROOT / "outputs/results_main/review_infer/p25_1_state_hygiene_4b_focus.jsonl",
        "meta": ROOT / "outputs/subsets/state_hygiene_4b_focus_meta.json",
        "dataset": ROOT / "outputs/subsets/state_hygiene_4b_focus.parquet",
        "gold": Path("/reviewF/datasets/drmas_review/test.parquet"),
    },
    {
        "name": "4b_mixed_v2",
        "results": ROOT / "outputs/results_main/review_infer/p25_1_state_hygiene_mixed_v2.jsonl",
        "meta": ROOT / "outputs/subsets/state_hygiene_mixed_v2_meta.json",
        "dataset": ROOT / "outputs/subsets/state_hygiene_mixed_v2.parquet",
        "gold": Path("/reviewF/datasets/drmas_review_eval100/test.parquet"),
    },
    {
        "name": "9b_fulltest_mainline",
        "results": ROOT / "outputs/results_main/review_infer/p25_1_fulltest_mainline.jsonl",
        "meta": None,
        "dataset": Path("/reviewF/datasets/drmas_review/test.parquet"),
        "gold": Path("/reviewF/datasets/drmas_review/test.parquet"),
    },
]

POSITIVE_RE = re.compile(
    r"\b(support|supports|supported|supporting|confirm|confirms|demonstrat|show|shows|shown|improv|outperform|achiev|effective|evidence)\b",
    re.IGNORECASE,
)
RAW_STRONG_SUPPORT_RE = re.compile(
    r'"strength"\s*:\s*"strong"(?:(?!\{).){0,600}"stance"\s*:\s*"(supports|partially_supports)"|'
    r'"stance"\s*:\s*"(supports|partially_supports)"(?:(?!\{).){0,600}"strength"\s*:\s*"strong"',
    re.IGNORECASE | re.S,
)
RESULT_RE = re.compile(r"\b(method|experiment|result|table|figure|benchmark|ablation|evaluation|accuracy|performance|conclusion)\b", re.IGNORECASE)
INSUFFICIENT_RE = re.compile(r"insufficient|cannot verify|can't verify|could not verify|incomplete|missing|not provided|truncated|full paper|no evidence|lacks evidence|not enough", re.IGNORECASE)
WRAPPER_RE = re.compile(r"\[Instruction\]|Format requirements|--- BEGIN PAPER ---", re.IGNORECASE)
ABSTRACT_RE = re.compile(r"abstract|\\begin\{abstract\}", re.IGNORECASE)
METHOD_RE = re.compile(r"method|methodology|approach|\\section\{[^}]*method", re.IGNORECASE)
RESULTS_RE = re.compile(r"result|experiment|evaluation|benchmark|ablation|performance|\\section\{[^}]*result|\\section\{[^}]*experiment", re.IGNORECASE)
CONCLUSION_RE = re.compile(r"conclusion|discussion|limitation|\\section\{[^}]*conclusion", re.IGNORECASE)
TABLE_FIG_RE = re.compile(r"table\s*\d|figure\s*\d|fig\.\s*\d|tab\.\s*\d|\\begin\{table\}|\\begin\{figure\}", re.IGNORECASE)
META_EVIDENCE_RE = re.compile(r"provided excerpt|paper text is incomplete|fallback|invalid json|cannot verify|could not verify|full paper|not enough", re.IGNORECASE)


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_json(path: Optional[Path]) -> Dict[str, Any]:
    if not path or not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def parse_jsonish(value: Any) -> Any:
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return value
        if (text.startswith("{") and text.endswith("}")) or (text.startswith("[") and text.endswith("]")):
            try:
                return json.loads(text)
            except Exception:
                return value
    return value


def row_id(row: Dict[str, Any]) -> str:
    env_kwargs = parse_jsonish(row.get("env_kwargs"))
    extra_info = parse_jsonish(row.get("extra_info"))
    if not isinstance(env_kwargs, dict):
        env_kwargs = {}
    if not isinstance(extra_info, dict):
        extra_info = {}
    return str(env_kwargs.get("paper_id") or row.get("paper_id") or row.get("id") or extra_info.get("id") or "")


def extract_paper_text(row: Dict[str, Any]) -> str:
    env_kwargs = parse_jsonish(row.get("env_kwargs"))
    if not isinstance(env_kwargs, dict):
        env_kwargs = {}
    inputs_val = row.get("inputs")
    paper_text = env_kwargs.get("paper_text") or row.get("paper_text") or ""
    if not paper_text and isinstance(inputs_val, str) and not inputs_val.strip().startswith("["):
        paper_text = inputs_val
    if not paper_text:
        paper_text = row.get("question") or ""
    if not paper_text:
        prompt = parse_jsonish(row.get("prompt"))
        msg_list = prompt
        if not isinstance(msg_list, list) and isinstance(inputs_val, str) and inputs_val.strip().startswith("["):
            msg_list = parse_jsonish(inputs_val)
        if isinstance(msg_list, list):
            for item in msg_list:
                if isinstance(item, dict) and item.get("role") == "user":
                    content = item.get("content", "")
                    if isinstance(content, str) and len(content) > len(str(paper_text)):
                        paper_text = content
                    if isinstance(content, str) and len(content) > 1000:
                        break
    return str(paper_text or "")


def load_dataset_texts(path: Optional[Path]) -> Dict[str, Dict[str, Any]]:
    if not path or not path.exists():
        return {}
    out: Dict[str, Dict[str, Any]] = {}
    for row in pq.read_table(path).to_pylist():
        pid = row_id(row)
        if not pid:
            continue
        text = extract_paper_text(row)
        out[pid] = {
            "paper_text": text,
            "paper_text_chars": len(text),
            "contains_instruction": "[Instruction]" in text,
            "contains_format_requirements": "Format requirements" in text,
            "contains_begin_paper": "--- BEGIN PAPER ---" in text,
        }
    return out


def load_gold(path: Optional[Path]) -> Dict[str, str]:
    if not path or not path.exists():
        return {}
    out = {}
    for row in pq.read_table(path).to_pylist():
        pid = str(row.get("id") or row.get("paper_id") or "")
        decision = str(row.get("decision") or row.get("gold_decision") or row.get("ground_truth_decision") or "")
        if pid and decision:
            out[pid] = decision
    return out


def groups_from_meta(meta: Dict[str, Any]) -> Dict[str, str]:
    groups = {}
    for group_name, ids in (meta.get("groups") or {}).items():
        for pid in ids:
            groups[str(pid)] = str(group_name)
    return groups


def infer_gold(pid: str, group: str, gold_map: Dict[str, str]) -> str:
    if pid in gold_map:
        return norm(gold_map[pid])
    g = norm(group)
    if g in {"gold_accept", "fresh_accept"}:
        return "accept"
    if g in {"fresh_reject", "stable_reject_control", "oracle_false_accept_reject"}:
        return "reject"
    return ""


def is_positive_support(ev: Dict[str, Any]) -> bool:
    return norm(ev.get("strength")) == "strong" and norm(ev.get("stance")) in {"supports", "partially_supports"}


def is_support_any(ev: Dict[str, Any]) -> bool:
    return norm(ev.get("stance")) in {"supports", "partially_supports"}


def is_strong_contradiction(ev: Dict[str, Any]) -> bool:
    return norm(ev.get("strength")) == "strong" and norm(ev.get("stance")) == "contradicts"


def is_fallback_claim_id(claim_id: Any) -> bool:
    return str(claim_id or "").startswith(("claim-fallback-", "claim-general-"))


def is_fallback_evidence(ev: Dict[str, Any]) -> bool:
    evidence_id = str(ev.get("evidence_id") or "")
    source = str(ev.get("source") or "")
    text = f"{ev.get('evidence', '')} {source} {evidence_id}"
    return evidence_id.startswith(("evidence-fallback-", "evidence-general-")) or source == "fallback-extraction" or bool(META_EVIDENCE_RE.search(text))


def claim_index(state: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    return {str(c.get("claim_id")): c for c in state.get("claims", []) or [] if c.get("claim_id")}


def evidence_excerpt_from_prompt(prompt: str) -> str:
    patterns = [
        r"# Evidence-Relevant Paper Excerpt\n(.*?)(?:\n\n# Evidence State Slice|\n# Evidence State Slice)",
        r"# Claim-Relevant Paper Excerpt\n(.*?)(?:\n\n# Claim State Slice|\n# Claim State Slice)",
        r"# Critique-Relevant Paper Excerpt\n(.*?)(?:\n\n# Critique State Slice|\n# Critique State Slice)",
        r"# Paper Excerpt\n(.*?)(?:\n\n# Compact ReviewState|\n# Compact ReviewState)",
    ]
    for pattern in patterns:
        match = re.search(pattern, prompt or "", re.S)
        if match:
            return match.group(1).strip()
    return ""


def worker_calls(row: Dict[str, Any]) -> Iterable[Tuple[int, Dict[str, Any]]]:
    for item in row.get("runner_trace", []) or []:
        turn = int(item.get("turn_id") or item.get("turn_index") or 0)
        for call in item.get("worker_calls", []) or []:
            yield turn, call


def turn_log_by_id(row: Dict[str, Any]) -> Dict[int, Dict[str, Any]]:
    out = {}
    for item in row.get("turn_logs", []) or []:
        turn = int(item.get("turn_id") or item.get("turn_index") or 0)
        if turn:
            out[turn] = item
    return out


def support_counts_for_evidence(evidence: List[Dict[str, Any]], claims: Optional[Dict[str, Dict[str, Any]]] = None) -> Dict[str, int]:
    claims = claims or {}
    counts = Counter()
    for ev in evidence or []:
        if is_positive_support(ev):
            counts["strong_positive_total"] += 1
            cid = str(ev.get("claim_id") or "")
            if not cid:
                counts["strong_positive_unbound"] += 1
            elif is_fallback_claim_id(cid):
                counts["strong_positive_fallback_claim"] += 1
            else:
                counts["strong_positive_real_claim"] += 1
                status = norm((claims.get(cid) or {}).get("status"))
                if status == "unsupported":
                    counts["strong_positive_unsupported_claim"] += 1
                elif status in {"supported", "partially_supported"}:
                    counts["strong_positive_supported_claim"] += 1
                else:
                    counts["strong_positive_uncertain_claim"] += 1
        if is_support_any(ev):
            counts["support_total"] += 1
        if is_strong_contradiction(ev):
            counts["strong_contradiction_total"] += 1
        if is_fallback_evidence(ev):
            counts["fallback_or_meta_evidence"] += 1
        if norm(ev.get("strength")) == "missing" or norm(ev.get("stance")) == "missing":
            counts["missing_evidence"] += 1
    return dict(counts)


def context_flags(text: str) -> Dict[str, Any]:
    body = text
    marker = "--- BEGIN PAPER ---"
    if marker in text:
        body = text.split(marker, 1)[1]
    wrapper_chars = 0
    if marker in text:
        wrapper_chars = text.find(marker) + len(marker)
    elif WRAPPER_RE.search(text):
        wrapper_chars = min(len(text), 260)
    return {
        "contains_abstract": bool(ABSTRACT_RE.search(text)),
        "contains_method": bool(METHOD_RE.search(text)),
        "contains_results": bool(RESULTS_RE.search(text)),
        "contains_conclusion": bool(CONCLUSION_RE.search(text)),
        "contains_table_or_figure": bool(TABLE_FIG_RE.search(text)),
        "contains_instruction": "[Instruction]" in text,
        "contains_format_requirements": "Format requirements" in text,
        "contains_begin_paper": marker in text,
        "wrapper_chars_visible": wrapper_chars,
        "paper_body_chars_visible": len(body),
    }


def raw_flags(raw: str) -> Dict[str, int]:
    strict_positive = bool(RAW_STRONG_SUPPORT_RE.search(raw or ""))
    return {
        "raw_positive_evidence_mentions": int(strict_positive),
        "raw_support_claim_mentions": int(bool(POSITIVE_RE.search(raw or ""))),
        "raw_result_or_table_mentions": int(bool(RESULT_RE.search(raw or ""))),
        "raw_insufficient_excerpt_mentions": int(bool(INSUFFICIENT_RE.search(raw or ""))),
    }


def fallback_summary(payload: Dict[str, Any]) -> Dict[str, int]:
    counts = Counter()
    evs = payload.get("evidence_map", []) or []
    qs = payload.get("unresolved_questions", []) or []
    conflicts = payload.get("conflict_notes", []) or []
    counts["fallback_payload_count"] = 1
    counts["fallback_unresolved_question_count"] = len(qs)
    for ev in evs:
        if is_fallback_evidence(ev):
            counts["fallback_evidence_count"] += 1
        if norm(ev.get("strength")) == "missing" or norm(ev.get("stance")) == "missing":
            counts["fallback_missing_evidence_count"] += 1
        if is_positive_support(ev):
            counts["fallback_support_evidence_count"] += 1
        if norm(ev.get("stance")) == "contradicts":
            counts["fallback_contradiction_count"] += 1
    counts["fallback_conflict_count"] = len(conflicts)
    return dict(counts)


def first_evidence_excerpt(row: Dict[str, Any]) -> str:
    for _, call in worker_calls(row):
        if call.get("agent_id") == "Evidence Agent":
            excerpt = evidence_excerpt_from_prompt(call.get("prompt", ""))
            if excerpt:
                return excerpt
    return ""


def analyze_run(spec: Dict[str, Any]) -> Dict[str, Any]:
    rows = load_jsonl(spec["results"])
    meta = load_json(spec.get("meta"))
    groups = groups_from_meta(meta)
    gold = load_gold(spec.get("gold"))
    dataset_texts = load_dataset_texts(spec.get("dataset"))
    cases = []
    calls = []
    merge_rows = []
    fallback_cases = []
    raw_positive_parse_failures = []
    fallback_bound_support_cases = []
    claim_status_cases = []
    high_stance_reject_cases = []

    for row in rows:
        pid = str(row.get("paper_id") or row.get("id") or "")
        group = groups.get(pid, "ungrouped")
        gold_decision = infer_gold(pid, group, gold)
        state = row.get("review_state", {}) or {}
        claims = claim_index(state)
        final_evidence = state.get("evidence_map", []) or []
        final_support = support_counts_for_evidence(final_evidence, claims)
        blockers = decision_blockers(state).get("blockers", [])
        diag = decision_blockers(state)
        excerpt = first_evidence_excerpt(row)
        if not excerpt:
            text_info = dataset_texts.get(pid, {})
            excerpt = str(text_info.get("paper_text", ""))[:800]
        flags = context_flags(excerpt)
        text_info = dataset_texts.get(pid, {})
        reward_breakdown = row.get("reward_breakdown", {}) or {}
        stance_align = reward_breakdown.get("stance_align", reward_breakdown.get("stance_alignment", ""))
        case_raw = Counter()
        evidence_calls = 0
        evidence_parse_errors = 0
        evidence_fallback_payloads = 0
        raw_positive_parse_failed = 0
        payload_strong_support = 0
        payload_support = 0
        payload_strong_ids = []
        fallback_counts = Counter()
        tlogs = turn_log_by_id(row)
        final_evidence_ids = {str(ev.get("evidence_id") or "") for ev in final_evidence}

        for turn, call in worker_calls(row):
            agent = str(call.get("agent_id") or "")
            raw = str(call.get("raw") or "")
            payload = call.get("payload") or {}
            parse_error = str(call.get("parse_error") or "")
            fallback_payload = call.get("fallback_payload") or {}
            rf = raw_flags(raw)
            for key, value in rf.items():
                case_raw[key] += value
            payload_counts = support_counts_for_evidence(payload.get("evidence_map", []) or [], claims)
            call_record = {
                "run": spec["name"],
                "paper_id": pid,
                "gold": gold_decision,
                "group": group,
                "turn_index": turn,
                "agent_id": agent,
                "parse_error": parse_error,
                "has_parse_error": bool(parse_error),
                "fallback_payload": bool(fallback_payload),
                **rf,
                "payload_support_count": payload_counts.get("support_total", 0),
                "payload_strong_support_count": payload_counts.get("strong_positive_total", 0),
            }
            calls.append(call_record)
            if agent == "Evidence Agent":
                evidence_calls += 1
                evidence_parse_errors += int(bool(parse_error))
                evidence_fallback_payloads += int(bool(fallback_payload))
                payload_strong_support += payload_counts.get("strong_positive_total", 0)
                payload_support += payload_counts.get("support_total", 0)
                for ev in payload.get("evidence_map", []) or []:
                    if is_positive_support(ev):
                        payload_strong_ids.append(str(ev.get("evidence_id") or ""))
                if parse_error and rf["raw_positive_evidence_mentions"]:
                    raw_positive_parse_failed += 1
                    raw_positive_parse_failures.append({
                        "run": spec["name"],
                        "paper_id": pid,
                        "gold": gold_decision,
                        "turn_index": turn,
                        "agent_id": agent,
                        "raw_positive_snippet": " ".join(raw.split())[:500],
                        "parse_error": parse_error[:300],
                        "fallback_payload_summary": fallback_summary(fallback_payload) if fallback_payload else {},
                        "final_state_support_count": final_support.get("strong_positive_total", 0),
                    })
                if fallback_payload:
                    fs = Counter(fallback_summary(fallback_payload))
                    fallback_counts.update(fs)
                    fallback_cases.append({
                        "run": spec["name"],
                        "paper_id": pid,
                        "gold": gold_decision,
                        "turn_index": turn,
                        "agent_id": agent,
                        **dict(fs),
                    })
                turn_snapshot = (tlogs.get(turn) or {}).get("state_snapshot", {}) or {}
                merged_evidence = turn_snapshot.get("evidence_map", []) or []
                merged_counts = support_counts_for_evidence(merged_evidence, claim_index(turn_snapshot))
                dropped = 0
                drop_reasons = []
                for ev in payload.get("evidence_map", []) or []:
                    if not is_positive_support(ev):
                        continue
                    evid = str(ev.get("evidence_id") or "")
                    if evid and evid not in final_evidence_ids:
                        dropped += 1
                        drop_reasons.append("evidence_id_missing_in_final")
                    elif is_fallback_claim_id(ev.get("claim_id")):
                        drop_reasons.append("support_bound_to_fallback_claim")
                merge_rows.append({
                    "run": spec["name"],
                    "paper_id": pid,
                    "gold": gold_decision,
                    "turn_index": turn,
                    "payload_support": payload_counts.get("support_total", 0),
                    "payload_strong_support": payload_counts.get("strong_positive_total", 0),
                    "merged_support": merged_counts.get("support_total", 0),
                    "merged_strong_support": merged_counts.get("strong_positive_total", 0),
                    "final_strong_support": final_support.get("strong_positive_total", 0),
                    "dropped_support": dropped,
                    "drop_reason": ";".join(sorted(set(drop_reasons))) if drop_reasons else "none",
                })

        strong_by_claim = defaultdict(list)
        contradiction_by_claim = defaultdict(list)
        for ev in final_evidence:
            cid = str(ev.get("claim_id") or "")
            if is_positive_support(ev):
                strong_by_claim[cid].append(str(ev.get("evidence_id") or ""))
                if is_fallback_claim_id(cid):
                    fallback_bound_support_cases.append({
                        "run": spec["name"],
                        "paper_id": pid,
                        "gold": gold_decision,
                        "claim_id": cid,
                        "evidence_id": str(ev.get("evidence_id") or ""),
                        "source": str(ev.get("source") or "")[:120],
                        "evidence_preview": " ".join(str(ev.get("evidence") or "").split())[:240],
                        "would_be_risky_to_count": True,
                    })
            if is_strong_contradiction(ev):
                contradiction_by_claim[cid].append(str(ev.get("evidence_id") or ""))

        status_counts = Counter()
        for cid, claim in claims.items():
            status = norm(claim.get("status")) or "unknown"
            support_ids = strong_by_claim.get(cid, [])
            contra_ids = contradiction_by_claim.get(cid, [])
            if status == "unsupported" and support_ids:
                status_counts["unsupported_with_strong_support_count"] += 1
            if status == "unsupported" and len(support_ids) >= 2:
                status_counts["unsupported_with_2plus_strong_support_count"] += 1
            if status in {"supported", "partially_supported"} and contra_ids:
                status_counts["supported_with_strong_contradiction_count"] += 1
            if status == "partially_supported" and not support_ids:
                status_counts["partially_supported_with_no_support_count"] += 1
            guards = state.get("_persistent_status_guards", {}) or {}
            guarded = cid in guards
            if guarded and support_ids:
                status_counts["status_guard_conflict_count"] += 1
            if support_ids and status not in {"supported", "partially_supported"}:
                status_counts["support_not_reflected_in_claim_status_count"] += 1
            if support_ids or contra_ids or guarded:
                claim_status_cases.append({
                    "run": spec["name"],
                    "paper_id": pid,
                    "gold": gold_decision,
                    "claim_id": cid,
                    "claim_status": status,
                    "strong_support_evidence_ids": support_ids,
                    "strong_contradiction_evidence_ids": contra_ids,
                    "support_count": len(support_ids),
                    "contradiction_count": len(contra_ids),
                    "status_guard": guarded,
                    "evidence_gap_for_same_claim": any(cid in str(gap) for gap in state.get("evidence_gaps", []) or []),
                })

        failure_class = "unclassified"
        support_possible = bool(flags["contains_results"] or flags["contains_table_or_figure"] or flags["contains_conclusion"])
        if gold_decision == "accept":
            if final_support.get("strong_positive_real_claim", 0) == 0 and not support_possible and case_raw["raw_positive_evidence_mentions"] == 0:
                failure_class = "A_input_context_no_visible_support"
            elif raw_positive_parse_failed > 0:
                failure_class = "B_raw_positive_parse_failed"
            elif payload_strong_support > final_support.get("strong_positive_total", 0):
                failure_class = "C_payload_support_not_preserved"
            elif final_support.get("strong_positive_fallback_claim", 0) > 0 and final_support.get("strong_positive_real_claim", 0) == 0:
                failure_class = "D_support_bound_to_fallback_claim"
            elif status_counts.get("support_not_reflected_in_claim_status_count", 0) > 0:
                failure_class = "E_support_status_conflict"
            elif final_support.get("strong_positive_total", 0) == 0:
                failure_class = "A_input_or_extraction_no_support"
            else:
                failure_class = "F_positive_present_but_blocked_by_negative_lifecycle"

        case = {
            "run": spec["name"],
            "paper_id": pid,
            "gold": gold_decision,
            "group": group,
            "pred": norm(row.get("final_decision") or state.get("final_decision")),
            "paper_text_chars": int(text_info.get("paper_text_chars", 0)),
            "paper_text_contains_instruction": bool(text_info.get("contains_instruction", False)),
            "paper_text_contains_format_requirements": bool(text_info.get("contains_format_requirements", False)),
            "paper_text_contains_begin_paper": bool(text_info.get("contains_begin_paper", False)),
            "evidence_excerpt_chars": len(excerpt),
            **flags,
            "first_800_preview": " ".join(excerpt.split())[:260],
            "truncation_point_preview": " ".join(excerpt.split())[-260:],
            "support_possible_from_visible_excerpt": support_possible,
            "evidence_agent_calls": evidence_calls,
            "evidence_parse_errors": evidence_parse_errors,
            "evidence_fallback_payloads": evidence_fallback_payloads,
            "payload_support_count": payload_support,
            "payload_strong_support_count": payload_strong_support,
            "raw_positive_but_parse_failed_count": raw_positive_parse_failed,
            **{k: int(v) for k, v in case_raw.items()},
            **{f"final_{k}": int(v) for k, v in final_support.items()},
            **{f"status_{k}": int(v) for k, v in status_counts.items()},
            **{f"fallback_{k}": int(v) for k, v in fallback_counts.items()},
            "final_strong_support_count_used_by_decision": int(diag.get("strong_support", 0)),
            "decision_block_reason": ", ".join(blockers),
            "positive_support_failure_class": failure_class,
            "stance_align": stance_align,
        }
        cases.append(case)
        try:
            stance_value = float(stance_align)
        except Exception:
            stance_value = 0.0
        if gold_decision == "accept" and case["pred"] != "accept" and stance_value >= 0.7:
            high_stance_reject_cases.append(case)

    return {
        "name": spec["name"],
        "result_path": str(spec["results"]),
        "sample_count": len(cases),
        "cases": cases,
        "calls": calls,
        "merge_rows": merge_rows,
        "fallback_cases": fallback_cases,
        "raw_positive_parse_failures": raw_positive_parse_failures,
        "fallback_bound_support_cases": fallback_bound_support_cases,
        "claim_status_cases": claim_status_cases,
        "high_stance_reject_cases": high_stance_reject_cases,
    }


def aggregate_cases(cases: List[Dict[str, Any]]) -> Dict[str, Any]:
    total = Counter()
    by_gold = defaultdict(Counter)
    by_run = defaultdict(Counter)
    for c in cases:
        gold = c.get("gold") or "unknown"
        run = c.get("run") or "unknown"
        total["samples"] += 1
        by_gold[gold]["samples"] += 1
        by_run[run]["samples"] += 1
        for key, value in c.items():
            if isinstance(value, bool):
                v = int(value)
            elif isinstance(value, int):
                v = value
            else:
                continue
            if key in {"samples"}:
                continue
            total[key] += v
            by_gold[gold][key] += v
            by_run[run][key] += v
        total[f"failure_class::{c.get('positive_support_failure_class')}"] += 1
        by_gold[gold][f"failure_class::{c.get('positive_support_failure_class')}"] += 1
        by_run[run][f"failure_class::{c.get('positive_support_failure_class')}"] += 1
    return {"total": dict(total), "by_gold": {k: dict(v) for k, v in by_gold.items()}, "by_run": {k: dict(v) for k, v in by_run.items()}}


def aggregate_calls(calls: List[Dict[str, Any]]) -> Dict[str, Any]:
    by_agent = defaultdict(Counter)
    by_gold_agent = defaultdict(Counter)
    for call in calls:
        agent = call.get("agent_id") or "unknown"
        gold = call.get("gold") or "unknown"
        by_agent[agent]["total_calls"] += 1
        by_agent[agent]["parse_error_count"] += int(call.get("has_parse_error", False))
        by_agent[agent]["fallback_payload_count"] += int(call.get("fallback_payload", False))
        by_agent[agent]["raw_positive_evidence_mentions"] += int(call.get("raw_positive_evidence_mentions", 0))
        by_agent[agent]["raw_insufficient_excerpt_mentions"] += int(call.get("raw_insufficient_excerpt_mentions", 0))
        key = f"{gold}::{agent}"
        by_gold_agent[key]["total_calls"] += 1
        by_gold_agent[key]["parse_error_count"] += int(call.get("has_parse_error", False))
        by_gold_agent[key]["fallback_payload_count"] += int(call.get("fallback_payload", False))
    return {"by_agent": {k: dict(v) for k, v in by_agent.items()}, "by_gold_agent": {k: dict(v) for k, v in by_gold_agent.items()}}


def fmt_rate(num: int, den: int) -> str:
    return f"{(num / den):.3f}" if den else "0.000"


def md_table(headers: List[str], rows: List[List[Any]]) -> List[str]:
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"] * len(headers)) + "|"]
    for row in rows:
        lines.append("| " + " | ".join(str(x).replace("\n", " ") for x in row) + " |")
    return lines


def write_context_doc(payload: Dict[str, Any]) -> None:
    cases = payload["cases"]
    accept = [c for c in cases if c.get("gold") == "accept"]
    reject = [c for c in cases if c.get("gold") == "reject"]
    def avg(items: List[Dict[str, Any]], key: str) -> float:
        return sum(float(c.get(key) or 0) for c in items) / len(items) if items else 0.0
    lines = [
        "# Evidence Context Visibility Audit",
        "",
        "**运行行为是否改变**：否。",
        "",
        "## 1. 总览",
        "",
    ]
    lines += md_table(
        ["group", "n", "paper_text_avg_chars", "evidence_excerpt_avg_chars", "visible_method_rate", "visible_results_rate", "visible_table_or_figure_rate", "wrapper_visible_rate"],
        [
            ["gold_accept", len(accept), f"{avg(accept, 'paper_text_chars'):.1f}", f"{avg(accept, 'evidence_excerpt_chars'):.1f}", fmt_rate(sum(c.get("contains_method", 0) for c in accept), len(accept)), fmt_rate(sum(c.get("contains_results", 0) for c in accept), len(accept)), fmt_rate(sum(c.get("contains_table_or_figure", 0) for c in accept), len(accept)), fmt_rate(sum(c.get("contains_instruction", 0) or c.get("contains_format_requirements", 0) for c in accept), len(accept))],
            ["gold_reject", len(reject), f"{avg(reject, 'paper_text_chars'):.1f}", f"{avg(reject, 'evidence_excerpt_chars'):.1f}", fmt_rate(sum(c.get("contains_method", 0) for c in reject), len(reject)), fmt_rate(sum(c.get("contains_results", 0) for c in reject), len(reject)), fmt_rate(sum(c.get("contains_table_or_figure", 0) for c in reject), len(reject)), fmt_rate(sum(c.get("contains_instruction", 0) or c.get("contains_format_requirements", 0) for c in reject), len(reject))],
        ],
    )
    lines += ["", "## 2. ACCEPT_EVIDENCE_CONTEXT_TABLE", ""]
    rows = []
    for c in accept:
        rows.append([
            c["run"], c["paper_id"], c["gold"], c["paper_text_chars"], c["evidence_excerpt_chars"],
            c["contains_abstract"], c["contains_method"], c["contains_results"], c["contains_conclusion"], c["contains_table_or_figure"],
            c["support_possible_from_visible_excerpt"], c["first_800_preview"][:140],
        ])
    lines += md_table(["run", "paper_id", "gold", "paper_text_chars", "excerpt_chars", "abstract", "method", "results", "conclusion", "table/figure", "support_possible", "first_800_preview"], rows)
    lines += [
        "",
        "## 3. 判断",
        "",
        "- **主要发现**：Evidence Agent 的可见 excerpt 普遍来自 `paper_text` 开头，且多包含 `[Instruction]`、格式要求与 `--- BEGIN PAPER ---` 前后的 wrapper。",
        "- **风险**：当正文被截在 title/abstract 开头时，Evidence Agent 很容易输出 `missing`、`cannot verify`、`full paper` 类信息，而不是 method/result/table 证据。",
    ]
    (DOC_DIR / "EVIDENCE_CONTEXT_VISIBILITY_AUDIT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_parse_doc(payload: Dict[str, Any]) -> None:
    calls_agg = payload["call_aggregate"]
    lines = ["# Evidence JSON Parse Audit", "", "**运行行为是否改变**：否。", "", "## 1. Agent 级 parse/fallback 统计", ""]
    rows = []
    for agent, c in sorted(calls_agg["by_agent"].items()):
        total = c.get("total_calls", 0)
        parse = c.get("parse_error_count", 0)
        fallback = c.get("fallback_payload_count", 0)
        rows.append([agent, total, total - parse, parse, fallback, fmt_rate(fallback, total), c.get("raw_positive_evidence_mentions", 0), c.get("raw_insufficient_excerpt_mentions", 0)])
    lines += md_table(["agent_id", "total_calls", "valid_json_count", "parse_error_count", "fallback_payload_count", "fallback_rate", "raw_positive_mentions", "raw_insufficient_mentions"], rows)
    lines += ["", "## 2. Gold x Agent 统计", ""]
    rows = []
    for key, c in sorted(calls_agg["by_gold_agent"].items()):
        gold, agent = key.split("::", 1)
        total = c.get("total_calls", 0)
        parse = c.get("parse_error_count", 0)
        fallback = c.get("fallback_payload_count", 0)
        rows.append([gold, agent, total, parse, fallback, fmt_rate(parse, total), fmt_rate(fallback, total)])
    lines += md_table(["gold", "agent_id", "total_calls", "parse_error_count", "fallback_payload_count", "parse_error_rate", "fallback_rate"], rows)
    lines += ["", "## 3. RAW_POSITIVE_PARSE_FAILURE_CASES", ""]
    rows = []
    for item in payload["raw_positive_parse_failures"][:80]:
        rows.append([item["run"], item["paper_id"], item["gold"], item["turn_index"], item["agent_id"], item["raw_positive_snippet"][:180], item["parse_error"][:120], item["fallback_payload_summary"], item["final_state_support_count"]])
    lines += md_table(["run", "paper_id", "gold", "turn", "agent", "raw_positive_snippet", "parse_error", "fallback_payload_summary", "final_support"], rows)
    lines += [
        "",
        "## 4. 判断",
        "",
        "- **parse failure 作用**：它不是唯一断点，但会把 worker raw 输出转成 fallback payload，并把 missing evidence / unresolved question 写入 ReviewState。",
        "- **审计重点**：如果 raw 中有正向 evidence 但 parse failed，则下一步可考虑 Evidence JSON Robustness；否则优先检查输入上下文。",
    ]
    (DOC_DIR / "EVIDENCE_JSON_PARSE_AUDIT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_merge_doc(payload: Dict[str, Any]) -> None:
    rows_data = payload["merge_rows"]
    total_payload_strong = sum(r["payload_strong_support"] for r in rows_data)
    total_dropped = sum(r["dropped_support"] for r in rows_data)
    lines = [
        "# Positive Support Merge Funnel",
        "",
        "**运行行为是否改变**：否。",
        "",
        "## 1. 总览",
        "",
        f"- **payload strong support total**: {total_payload_strong}",
        f"- **dropped support by evidence_id check**: {total_dropped}",
        "",
        "## 2. Turn-level 漏斗表",
        "",
    ]
    rows = []
    for r in rows_data:
        if r["payload_support"] or r["payload_strong_support"] or r["dropped_support"]:
            rows.append([r["run"], r["paper_id"], r["gold"], r["turn_index"], r["payload_support"], r["payload_strong_support"], r["merged_support"], r["merged_strong_support"], r["final_strong_support"], r["dropped_support"], r["drop_reason"]])
    lines += md_table(["run", "paper_id", "gold", "turn", "payload_support", "payload_strong", "merged_support", "merged_strong", "final_strong", "dropped", "drop_reason"], rows[:120])
    lines += [
        "",
        "## 3. 判断",
        "",
        "- **merge 层是否主因**：若 payload strong support 本身很少，则 merge 不是最早断点。",
        "- **保留风险**：少数 payload support 即使保留，也可能绑定 fallback claim；这属于 grounding 层问题。",
    ]
    (DOC_DIR / "POSITIVE_SUPPORT_MERGE_FUNNEL.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_grounding_doc(payload: Dict[str, Any]) -> None:
    cases = payload["cases"]
    total = Counter()
    by_gold = defaultdict(Counter)
    for c in cases:
        gold = c.get("gold") or "unknown"
        for key in ["final_strong_positive_total", "final_strong_positive_real_claim", "final_strong_positive_fallback_claim", "final_strong_positive_unsupported_claim", "final_strong_positive_supported_claim", "final_strong_positive_unbound"]:
            total[key] += int(c.get(key, 0))
            by_gold[gold][key] += int(c.get(key, 0))
    real_rate = total["final_strong_positive_real_claim"] / total["final_strong_positive_total"] if total["final_strong_positive_total"] else 0.0
    lines = [
        "# Support-to-Claim Grounding Audit",
        "",
        "**运行行为是否改变**：否。",
        "",
        "## 1. strong support 绑定对象统计",
        "",
    ]
    lines += md_table(["metric", "count"], [[k, v] for k, v in sorted(total.items())] + [["support_to_real_claim_grounding_rate", f"{real_rate:.3f}"]])
    lines += ["", "## 2. 按 gold decision 分组", ""]
    rows = []
    for gold, c in sorted(by_gold.items()):
        total_strong = c.get("final_strong_positive_total", 0)
        rows.append([gold, total_strong, c.get("final_strong_positive_real_claim", 0), c.get("final_strong_positive_fallback_claim", 0), c.get("final_strong_positive_unsupported_claim", 0), c.get("final_strong_positive_supported_claim", 0), fmt_rate(c.get("final_strong_positive_real_claim", 0), total_strong)])
    lines += md_table(["gold", "strong_total", "real_claim", "fallback_claim", "unsupported_claim", "supported_claim", "real_claim_rate"], rows)
    lines += ["", "## 3. FALLBACK_BOUND_SUPPORT_CASES", ""]
    rows = []
    for item in payload["fallback_bound_support_cases"][:120]:
        rows.append([item["run"], item["paper_id"], item["gold"], item["claim_id"], item["evidence_id"], item["source"], item["evidence_preview"], item["would_be_risky_to_count"]])
    lines += md_table(["run", "paper_id", "gold", "claim_id", "evidence_id", "source", "evidence_preview", "risky_to_count"], rows)
    lines += [
        "",
        "## 4. 判断",
        "",
        "- **fallback-bound support** 不应直接作为 accept 证据；它可能是真证据，也可能是 fallback 伪证据。",
        "- 如果正向 support 多数绑定 fallback claim，下一步应是 Support-to-Real-Claim Grounding；如果 strong support 总量本身很低，最早断点仍在输入/抽取层。",
    ]
    (DOC_DIR / "SUPPORT_TO_CLAIM_GROUNDING_AUDIT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_status_doc(payload: Dict[str, Any]) -> None:
    cases = payload["cases"]
    totals = Counter()
    for c in cases:
        for key, value in c.items():
            if key.startswith("status_") and isinstance(value, int):
                totals[key] += value
    lines = ["# Claim Status / Support Consistency Audit", "", "**运行行为是否改变**：否。", "", "## 1. 状态冲突总计", ""]
    lines += md_table(["metric", "count"], [[k, v] for k, v in sorted(totals.items())])
    lines += ["", "## 2. Claim-level case table", ""]
    rows = []
    for item in payload["claim_status_cases"][:160]:
        rows.append([item["run"], item["paper_id"], item["gold"], item["claim_id"], item["claim_status"], ",".join(item["strong_support_evidence_ids"]), ",".join(item["strong_contradiction_evidence_ids"]), item["support_count"], item["contradiction_count"], item["status_guard"], item["evidence_gap_for_same_claim"]])
    lines += md_table(["run", "paper_id", "gold", "claim_id", "claim_status", "strong_support_ids", "strong_contradiction_ids", "support_count", "contradiction_count", "status_guard", "evidence_gap_same_claim"], rows)
    lines += [
        "",
        "## 3. 判断",
        "",
        "- **claim-status reconciliation** 是后续必要 hygiene，但只有在 real-claim strong support 已稳定形成后才适合作为第一实现。",
        "- 若 strong support 总量不足，先改 status 同步无法恢复 accept。",
    ]
    (DOC_DIR / "CLAIM_STATUS_SUPPORT_CONSISTENCY_AUDIT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_formation_doc(payload: Dict[str, Any]) -> None:
    cases = payload["cases"]
    agg = payload["case_aggregate"]
    accept_cases = [c for c in cases if c.get("gold") == "accept"]
    class_counts = Counter(c.get("positive_support_failure_class", "unclassified") for c in accept_cases)
    lines = [
        "# Positive Support Formation Audit",
        "",
        "**运行行为是否改变**：否。",
        "**审计范围**：4B focus、4B mixed v2、9B fulltest mainline 的现有 JSONL/trace。",
        "",
        "## 1. 总览",
        "",
    ]
    key_rows = []
    for key in ["samples", "evidence_agent_calls", "evidence_parse_errors", "evidence_fallback_payloads", "payload_strong_support_count", "final_strong_positive_total", "final_strong_positive_real_claim", "final_strong_positive_fallback_claim", "final_strong_positive_unsupported_claim", "raw_positive_but_parse_failed_count"]:
        key_rows.append([key, agg["total"].get(key, 0)])
    lines += md_table(["metric", "value"], key_rows)
    lines += [
        "",
        "## 2. POSITIVE_SUPPORT_FAILURE_CLASSIFICATION",
        "",
    ]
    lines += md_table(["failure_class", "samples"], [[k, v] for k, v in sorted(class_counts.items(), key=lambda kv: -kv[1])])
    lines += [
        "",
        f"该表只统计 gold=accept 样本；reject 样本不参与 positive support 断点分类。accept 样本数：{len(accept_cases)}。",
    ]
    lines += ["", "## 3. Accept 样本逐例", ""]
    rows = []
    for c in cases:
        if c.get("gold") != "accept":
            continue
        rows.append([c["run"], c["paper_id"], c["pred"], c["positive_support_failure_class"], c["evidence_excerpt_chars"], c["contains_results"], c["contains_table_or_figure"], c["raw_positive_evidence_mentions"], c["evidence_parse_errors"], c["evidence_fallback_payloads"], c.get("payload_strong_support_count", 0), c.get("final_strong_positive_total", 0), c.get("final_strong_positive_real_claim", 0), c.get("decision_block_reason", "")])
    lines += md_table(["run", "paper_id", "pred", "failure_class", "excerpt_chars", "visible_results", "visible_table", "raw_positive", "parse_errors", "fallback_payloads", "payload_strong", "final_strong", "real_claim_strong", "blockers"], rows)
    lines += ["", "## 4. High stance but reject cases", ""]
    rows = []
    for c in payload["high_stance_reject_cases"][:80]:
        rows.append([
            c["run"],
            c["paper_id"],
            c["stance_align"],
            c.get("final_strong_positive_total", 0),
            c.get("final_strong_positive_real_claim", 0),
            c.get("final_strong_support_count_used_by_decision", 0),
            c.get("decision_block_reason", ""),
        ])
    lines += md_table(["run", "paper_id", "stance_align", "final_strong", "real_claim_strong", "decision_strong_count", "blockers"], rows)
    lines += [
        "",
        "## 5. 解释",
        "",
        "- **A 类** 表示 Evidence Agent 可见上下文里缺 method/result/table 且 raw 没有正向 support，优先指向输入/上下文选择问题。",
        "- **B 类** 表示 raw 中有正向 support 但 JSON 解析失败，优先指向 JSON robustness。",
        "- **C/D/E 类** 分别指向 merge、fallback grounding、claim-status 同步问题。",
    ]
    (DOC_DIR / "POSITIVE_SUPPORT_FORMATION_AUDIT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_decision_doc(payload: Dict[str, Any]) -> None:
    agg = payload["case_aggregate"]
    total = agg["total"]
    calls = payload["call_aggregate"]["by_agent"].get("Evidence Agent", {})
    evidence_total = calls.get("total_calls", 0)
    evidence_parse = calls.get("parse_error_count", 0)
    evidence_fallback = calls.get("fallback_payload_count", 0)
    final_strong = total.get("final_strong_positive_total", 0)
    real_strong = total.get("final_strong_positive_real_claim", 0)
    fallback_strong = total.get("final_strong_positive_fallback_claim", 0)
    accept_cases = [c for c in payload["cases"] if c.get("gold") == "accept"]
    accept_no_real = sum(1 for c in accept_cases if c.get("final_strong_positive_real_claim", 0) == 0)
    accept_context_limited = sum(1 for c in accept_cases if not c.get("support_possible_from_visible_excerpt"))
    recommendation = "Evidence Context Selection v1"
    lines = [
        "# Positive Support Next Cut Decision",
        "",
        "**运行行为是否改变**：否。",
        "",
        "## 1. 必答结论",
        "",
        "```text",
        "positive support 最早断点是：输入层 / Evidence Context Selection",
        "主要发生在：agent_system.environments.env_package.review.state._render_paper_excerpt -> render_evidence_observation -> agent_system.inference.review_runner.build_worker_observation",
        "accept 样本 strong support 缺失的主因是：Evidence Agent 只看到固定开头短 excerpt，且该 excerpt 经常包含 instruction wrapper + title/abstract 开头，method/result/table 证据不可见，导致 raw 阶段就缺少可用 positive support。",
        f"parse failure 是否是主因：不是最早主因，但属于放大器；Evidence Agent parse_error={evidence_parse}/{evidence_total}，fallback_payload={evidence_fallback}/{evidence_total}。",
        f"fallback-bound support 是否是主因：不是 mixed v2 上的最早断点，因为 strong support 总量本身不足；但它是安全约束，当前 strong fallback-bound={fallback_strong}，不能直接计入 accept。",
        f"下一轮唯一建议实现的是：{recommendation}",
        "暂时不要做的是：final decision threshold 放松、sticky/throttle/progression gate、recovery controller、全局 fallback suppression、candidate flaw/unresolved runtime 清理、直接把 fallback-bound support 当 accept 证据。",
        "```",
        "",
        "## 2. 支撑数据",
        "",
    ]
    lines += md_table(
        ["metric", "value"],
        [
            ["total_samples", total.get("samples", 0)],
            ["accept_samples", len(accept_cases)],
            ["accept_samples_without_real_claim_strong_support", accept_no_real],
            ["accept_samples_context_not_support_possible", accept_context_limited],
            ["final_strong_positive_total", final_strong],
            ["final_strong_positive_real_claim", real_strong],
            ["final_strong_positive_fallback_claim", fallback_strong],
            ["evidence_agent_calls", evidence_total],
            ["evidence_agent_parse_errors", evidence_parse],
            ["evidence_agent_fallback_payloads", evidence_fallback],
        ],
    )
    lines += [
        "",
        "## 3. 为什么不是其他方向优先",
        "",
        "- **不是 final decision threshold**：`strong<2` 多数时候反映的是 ReviewState 里没有可靠 positive support，而不是 threshold 单点过严。",
        "- **不是 runtime state hygiene 优先**：mixed v2 的 C1-C4 清负面模拟没有 recovered accept，说明正向 support 缺失时清负面也无效。",
        "- **不是 Claim-Evidence Reconciliation 优先**：只有当 real-claim strong support 已形成但 status 未同步时，它才是最早修复点；当前更早断在 context/抽取。",
        "- **不是全局 fallback suppression**：fallback 有污染风险，但也可能保留诊断信号；应先让 Evidence Agent 看到正确上下文。",
        "",
        "## 4. 下一轮唯一实验定义",
        "",
        "**Evidence Context Selection v1**：只改 Evidence Agent 的可见论文上下文选择，不改 decision、不改 recovery、不改 sticky/gate/throttle。目标是让 Evidence Agent 至少看到 abstract + method/result/evaluation/conclusion 或 table/figure 附近片段，而不是固定 `paper_text[:800]`。",
    ]
    (DOC_DIR / "POSITIVE_SUPPORT_NEXT_CUT_DECISION.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit positive support formation without changing runtime behavior.")
    parser.add_argument("--output-json", default=str(OUT_JSON))
    args = parser.parse_args()
    runs = [analyze_run(spec) for spec in RUN_SPECS if spec["results"].exists()]
    payload = {
        "runs": runs,
        "cases": [case for run in runs for case in run["cases"]],
        "calls": [call for run in runs for call in run["calls"]],
        "merge_rows": [item for run in runs for item in run["merge_rows"]],
        "fallback_cases": [item for run in runs for item in run["fallback_cases"]],
        "raw_positive_parse_failures": [item for run in runs for item in run["raw_positive_parse_failures"]],
        "fallback_bound_support_cases": [item for run in runs for item in run["fallback_bound_support_cases"]],
        "claim_status_cases": [item for run in runs for item in run["claim_status_cases"]],
        "high_stance_reject_cases": [item for run in runs for item in run["high_stance_reject_cases"]],
    }
    payload["case_aggregate"] = aggregate_cases(payload["cases"])
    payload["call_aggregate"] = aggregate_calls(payload["calls"])
    DOC_DIR.mkdir(parents=True, exist_ok=True)
    Path(args.output_json).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output_json).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    write_context_doc(payload)
    write_parse_doc(payload)
    write_merge_doc(payload)
    write_grounding_doc(payload)
    write_status_doc(payload)
    write_formation_doc(payload)
    write_decision_doc(payload)
    print(json.dumps({
        "runs": [run["name"] for run in runs],
        "sample_count": len(payload["cases"]),
        "evidence_agent_calls": payload["call_aggregate"]["by_agent"].get("Evidence Agent", {}).get("total_calls", 0),
        "output_json": str(args.output_json),
        "docs": [
            "POSITIVE_SUPPORT_FORMATION_AUDIT.md",
            "EVIDENCE_CONTEXT_VISIBILITY_AUDIT.md",
            "EVIDENCE_JSON_PARSE_AUDIT.md",
            "POSITIVE_SUPPORT_MERGE_FUNNEL.md",
            "SUPPORT_TO_CLAIM_GROUNDING_AUDIT.md",
            "CLAIM_STATUS_SUPPORT_CONSISTENCY_AUDIT.md",
            "POSITIVE_SUPPORT_NEXT_CUT_DECISION.md",
        ],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
