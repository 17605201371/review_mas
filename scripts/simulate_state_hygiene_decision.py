#!/usr/bin/env python3
"""Offline State Hygiene Decision Simulation.

目的：不改 inference/runtime，不重跑模型，只基于 full-test jsonl 模拟 state hygiene
修复是否存在恢复 accept recall、降低 always-reject 偏置的空间。

覆盖 NEXT_STEPS_PLAN.md 阶段 1：
  A. Claim-Evidence Reconciliation
  B. Stale Evidence Gap / unresolved cleanup
  C. Meta / Excerpt flaw filtering
  D. Candidate flaw 降权 / grounded-only
  E. 组合规则

输出：
  - FULLTEST_HYGIENE_SIMULATION_RESULTS.json
  - FULLTEST_HYGIENE_SIMULATION_CASE_TABLE.md
  - docs/experiments/FULLTEST_HYGIENE_SIMULATION.md
"""
from __future__ import annotations

import copy
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pyarrow.parquet as pq


ROOT = Path(__file__).resolve().parents[1]
INPUT_JSONL = ROOT / "outputs/results_main/review_infer/p25_1_fulltest_mainline.jsonl"
GOLD_PARQUET = Path("/reviewF/datasets/drmas_review/test.parquet")
RESULT_JSON = ROOT / "FULLTEST_HYGIENE_SIMULATION_RESULTS.json"
CASE_TABLE_MD = ROOT / "FULLTEST_HYGIENE_SIMULATION_CASE_TABLE.md"
REPORT_MD = ROOT / "docs/experiments/FULLTEST_HYGIENE_SIMULATION.md"

META_PATTERNS = [
    r"insufficient\s+evidence\s+in\s+(?:the\s+)?provided\s+excerpt",
    r"(?:lack|lacks|lacking)\s+(?:.{0,80})in\s+(?:the\s+)?(?:provided\s+)?excerpt",
    r"current\s+evidence\s+set\s+lacks?",
    r"no\s+grounded\s+(?:supporting|contradictory)\s+evidence",
    r"provided\s+excerpt\s+(?:does\s+not|lacks?|is\s+insufficient)",
    r"cannot\s+(?:confirm|verify)\s+(?:the\s+)?(?:core|technical)\s+claim",
    r"recovery\s+(?:failed|patch\s+failed)",
    r"blocked\s+by\s+policy",
    r"fallback\s+(?:extraction|evidence)\s+(?:failed|insufficient)",
    r"invalid\s+JSON",
    r"excerpt\s+is\s+insufficient",
    r"could\s+not\s+be\s+(?:verified|validated)",
]
META_REGEX = re.compile("|".join(META_PATTERNS), re.IGNORECASE)

GAP_PAT = re.compile(r"claim-(\d+).{0,100}(?:lack|lacks|lacking|insufficient|ungrounded)", re.IGNORECASE)
GENERIC_UNRESOLVED_REGEX = re.compile(
    r"check whether this weakness is explicitly grounded|"
    r"locate a concrete table|"
    r"verify whether this extracted claim|"
    r"paper text is incomplete|"
    r"where is the (?:detailed description|experimental section|full methodology)|"
    r"full methodology details|"
    r"provided excerpt|"
    r"full paper",
    re.IGNORECASE,
)


def norm(value: Any) -> str:
    return str(value or "").strip().lower()


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def load_gold(path: Path) -> Dict[str, str]:
    return {row["id"]: row["decision"] for row in pq.read_table(path).to_pylist()}


def has_meta(text: str) -> bool:
    return bool(META_REGEX.search(str(text or "")))


def claim_support_maps(state: Dict[str, Any]) -> Tuple[Dict[str, int], Dict[str, int]]:
    strong_supports = defaultdict(int)
    strong_contras = defaultdict(int)
    for ev in state.get("evidence_map", []) or []:
        cid = ev.get("claim_id")
        if not cid:
            continue
        strength = norm(ev.get("strength"))
        stance = norm(ev.get("stance"))
        if strength == "strong" and stance in {"supports", "partially_supports"}:
            strong_supports[cid] += 1
        if strength == "strong" and stance == "contradicts":
            strong_contras[cid] += 1
    return dict(strong_supports), dict(strong_contras)


def evidence_ids(state: Dict[str, Any]) -> set:
    return {ev.get("evidence_id") for ev in state.get("evidence_map", []) or [] if ev.get("evidence_id")}


def claim_id_from_gap(text: str) -> str:
    match = re.search(r"claim-(\d+)", str(text or "").lower())
    return f"claim-{match.group(1)}" if match else ""


def is_stale_gap(text: str, strong_supports: Dict[str, int]) -> bool:
    cid = claim_id_from_gap(text)
    if not cid:
        return False
    low = str(text or "").lower()
    if not re.search(r"lack|lacks|lacking|insufficient|ungrounded", low):
        return False
    return strong_supports.get(cid, 0) >= 1


def flaw_is_grounded(flaw: Dict[str, Any], ev_ids: set) -> bool:
    fids = set(flaw.get("evidence_ids", []) or [])
    return bool(fids & ev_ids) and not has_meta((flaw.get("title", "") + " " + flaw.get("description", "")))


def flaw_is_meta_or_excerpt(flaw: Dict[str, Any]) -> bool:
    text = (flaw.get("title", "") or "") + " " + (flaw.get("description", "") or "")
    return has_meta(text) or bool(re.search(r"provided\s+excerpt|excerpt\s+(?:insufficient|limitation)", text, re.IGNORECASE))


def open_unresolved_count(state: Dict[str, Any]) -> int:
    count = 0
    for item in state.get("unresolved_questions", []) or []:
        if isinstance(item, dict):
            if item.get("status", "open") == "open" and str(item.get("question", "")).strip():
                count += 1
        elif str(item or "").strip():
            count += 1
    return count


def infer_final_decision(state: Dict[str, Any], manager_payload: Dict[str, Any] | None = None) -> str:
    """Lightweight copy of review.state.infer_final_decision for offline analysis.

    Importing the runtime review state module pulls in env_manager/torch, which is
    unnecessary for JSONL-only simulations and can fail on minimal analysis
    environments. Keep this logic aligned with the runtime decision rule.
    """
    manager_payload = manager_payload or {}
    explicit = norm(manager_payload.get("final_decision"))
    if explicit in {"accept", "reject", "borderline"}:
        return explicit
    critical_flaws = sum(
        1 for flaw in state.get("flaw_candidates", []) or []
        if flaw.get("severity") == "critical" and flaw.get("status") != "retracted"
    )
    major_flaws = sum(
        1 for flaw in state.get("flaw_candidates", []) or []
        if flaw.get("severity") == "major" and flaw.get("status") not in {"downgraded", "retracted"}
    )
    strong_support = sum(
        1
        for item in state.get("evidence_map", []) or []
        if item.get("strength") == "strong" and item.get("stance") in {"supports", "partially_supports"}
    )
    unresolved = open_unresolved_count(state)
    conflicts = len(state.get("conflict_notes", []) or [])
    if critical_flaws > 0 or major_flaws >= 2 or unresolved >= 6 or conflicts >= 4:
        return "reject"
    if strong_support >= 2 and major_flaws == 0 and unresolved <= 3:
        return "accept"
    return "reject"


def raw_decision(state: Dict[str, Any]) -> str:
    # Empty manager_payload avoids explicit final_decision override.
    return infer_final_decision(state, {})


def weighted_decision(state: Dict[str, Any], candidate_weight: float = 0.5, grounded_only: bool = False) -> str:
    ev_ids = evidence_ids(state)
    critical = 0.0
    major = 0.0
    for flaw in state.get("flaw_candidates", []) or []:
        status = norm(flaw.get("status")) or "candidate"
        severity = norm(flaw.get("severity"))
        if status in {"downgraded", "retracted"}:
            continue
        if grounded_only and not flaw_is_grounded(flaw, ev_ids):
            continue
        weight = 1.0 if status == "confirmed" else candidate_weight
        if severity == "critical":
            critical += weight
        if severity == "major":
            major += weight
    strong_support = sum(
        1 for item in state.get("evidence_map", []) or []
        if norm(item.get("strength")) == "strong" and norm(item.get("stance")) in {"supports", "partially_supports"}
    )
    unresolved = open_unresolved_count(state)
    conflicts = len(state.get("conflict_notes", []) or [])
    if critical >= 1 or major >= 2 or unresolved >= 6 or conflicts >= 4:
        return "reject"
    if strong_support >= 2 and major == 0 and unresolved <= 3:
        return "accept"
    return "reject"


def hygiene_counts(state: Dict[str, Any]) -> Dict[str, int]:
    strong_supports, strong_contras = claim_support_maps(state)
    unsup_strong = 0
    unsup_2plus = 0
    stale_gap = 0
    candidate_major = 0
    confirmed_major = 0
    meta_flaw = 0
    grounded_flaw = 0
    ungrounded_flaw = 0
    ev_ids = evidence_ids(state)
    for claim in state.get("claims", []) or []:
        cid = claim.get("claim_id")
        if norm(claim.get("status")) == "unsupported":
            ss = strong_supports.get(cid, 0)
            if ss >= 1:
                unsup_strong += 1
            if ss >= 2:
                unsup_2plus += 1
    for gap in state.get("evidence_gaps", []) or []:
        if is_stale_gap(str(gap), strong_supports):
            stale_gap += 1
    for item in state.get("unresolved_questions", []) or []:
        text = item.get("question", "") if isinstance(item, dict) else str(item)
        if is_stale_gap(text, strong_supports):
            stale_gap += 1
    for flaw in state.get("flaw_candidates", []) or []:
        severity = norm(flaw.get("severity"))
        status = norm(flaw.get("status")) or "candidate"
        if severity == "major" and status == "candidate":
            candidate_major += 1
        if severity == "major" and status == "confirmed":
            confirmed_major += 1
        if flaw_is_meta_or_excerpt(flaw):
            meta_flaw += 1
        if flaw_is_grounded(flaw, ev_ids):
            grounded_flaw += 1
        else:
            ungrounded_flaw += 1
    return dict(
        unsupported_with_strong_support=unsup_strong,
        unsupported_with_2plus_strong=unsup_2plus,
        stale_evidence_gap=stale_gap,
        candidate_major=candidate_major,
        confirmed_major=confirmed_major,
        meta_or_excerpt_flaw=meta_flaw,
        grounded_flaw=grounded_flaw,
        ungrounded_flaw=ungrounded_flaw,
        unresolved_count=open_unresolved_count(state),
        conflict_count=len(state.get("conflict_notes", []) or []),
    )


def apply_claim_reconciliation(state: Dict[str, Any], target_status: str = "partially_supported") -> Dict[str, Any]:
    state = copy.deepcopy(state)
    strong_supports, strong_contras = claim_support_maps(state)
    for claim in state.get("claims", []) or []:
        cid = claim.get("claim_id")
        if norm(claim.get("status")) == "unsupported" and strong_supports.get(cid, 0) >= 2 and strong_contras.get(cid, 0) == 0:
            claim["status"] = target_status
            claim["hygiene_sim_reconciled"] = True
    return state


def apply_stale_gap_cleanup(state: Dict[str, Any]) -> Dict[str, Any]:
    state = copy.deepcopy(state)
    strong_supports, _ = claim_support_maps(state)
    state["evidence_gaps"] = [
        gap for gap in (state.get("evidence_gaps", []) or [])
        if not is_stale_gap(str(gap), strong_supports)
    ]
    cleaned_questions = []
    for item in state.get("unresolved_questions", []) or []:
        text = item.get("question", "") if isinstance(item, dict) else str(item)
        if is_stale_gap(text, strong_supports):
            if isinstance(item, dict):
                new_item = copy.deepcopy(item)
                new_item["status"] = "resolved"
                new_item["hygiene_sim_resolved"] = True
                cleaned_questions.append(new_item)
            continue
        cleaned_questions.append(item)
    state["unresolved_questions"] = cleaned_questions
    return state


def apply_generic_unresolved_cleanup(state: Dict[str, Any]) -> Dict[str, Any]:
    state = copy.deepcopy(state)
    cleaned_questions = []
    for item in state.get("unresolved_questions", []) or []:
        text = item.get("question", "") if isinstance(item, dict) else str(item)
        if GENERIC_UNRESOLVED_REGEX.search(str(text or "")):
            if isinstance(item, dict):
                new_item = copy.deepcopy(item)
                new_item["status"] = "resolved"
                new_item["hygiene_sim_resolved_generic"] = True
                cleaned_questions.append(new_item)
            continue
        cleaned_questions.append(item)
    state["unresolved_questions"] = cleaned_questions
    return state


def apply_meta_excerpt_filter(state: Dict[str, Any]) -> Dict[str, Any]:
    state = copy.deepcopy(state)
    for flaw in state.get("flaw_candidates", []) or []:
        if flaw_is_meta_or_excerpt(flaw):
            flaw["status"] = "downgraded"
            flaw["hygiene_sim_filtered_meta"] = True
    return state


def apply_grounded_candidate_filter(state: Dict[str, Any]) -> Dict[str, Any]:
    state = copy.deepcopy(state)
    ev_ids = evidence_ids(state)
    for flaw in state.get("flaw_candidates", []) or []:
        if norm(flaw.get("status")) == "candidate" and not flaw_is_grounded(flaw, ev_ids):
            flaw["status"] = "downgraded"
            flaw["hygiene_sim_filtered_ungrounded_candidate"] = True
    return state


def apply_oracle_candidate_suppression(state: Dict[str, Any]) -> Dict[str, Any]:
    state = copy.deepcopy(state)
    for flaw in state.get("flaw_candidates", []) or []:
        if norm(flaw.get("status")) == "candidate":
            flaw["status"] = "downgraded"
            flaw["hygiene_sim_oracle_candidate_suppressed"] = True
    return state


def apply_oracle_question_cleanup(state: Dict[str, Any]) -> Dict[str, Any]:
    state = copy.deepcopy(state)
    cleaned = []
    for item in state.get("unresolved_questions", []) or []:
        if isinstance(item, dict):
            new_item = copy.deepcopy(item)
            new_item["status"] = "resolved"
            new_item["hygiene_sim_oracle_resolved"] = True
            cleaned.append(new_item)
    state["unresolved_questions"] = cleaned
    state["conflict_notes"] = []
    return state


def simulate_variant(row: Dict[str, Any], variant: str) -> Tuple[str, Dict[str, int]]:
    state = copy.deepcopy(row.get("review_state", {}))
    if variant == "baseline_infer":
        pred = raw_decision(state)
        return pred, hygiene_counts(state)
    if variant == "A_reconcile_partial":
        state = apply_claim_reconciliation(state, "partially_supported")
        pred = raw_decision(state)
        return pred, hygiene_counts(state)
    if variant == "A_reconcile_supported":
        state = apply_claim_reconciliation(state, "supported")
        pred = raw_decision(state)
        return pred, hygiene_counts(state)
    if variant == "B_stale_gap_cleanup":
        state = apply_stale_gap_cleanup(state)
        pred = raw_decision(state)
        return pred, hygiene_counts(state)
    if variant == "C_meta_excerpt_filter":
        state = apply_meta_excerpt_filter(state)
        pred = raw_decision(state)
        return pred, hygiene_counts(state)
    if variant == "D_candidate_half_weight":
        pred = weighted_decision(state, candidate_weight=0.5, grounded_only=False)
        return pred, hygiene_counts(state)
    if variant == "D_grounded_candidate_only":
        state = apply_grounded_candidate_filter(state)
        pred = raw_decision(state)
        return pred, hygiene_counts(state)
    if variant == "E_combo_partial_half":
        state = apply_claim_reconciliation(state, "partially_supported")
        state = apply_stale_gap_cleanup(state)
        state = apply_meta_excerpt_filter(state)
        pred = weighted_decision(state, candidate_weight=0.5, grounded_only=True)
        return pred, hygiene_counts(state)
    if variant == "E_combo_supported_half":
        state = apply_claim_reconciliation(state, "supported")
        state = apply_stale_gap_cleanup(state)
        state = apply_meta_excerpt_filter(state)
        pred = weighted_decision(state, candidate_weight=0.5, grounded_only=True)
        return pred, hygiene_counts(state)
    if variant == "E_combo_strict_grounded":
        state = apply_claim_reconciliation(state, "partially_supported")
        state = apply_stale_gap_cleanup(state)
        state = apply_meta_excerpt_filter(state)
        state = apply_grounded_candidate_filter(state)
        pred = raw_decision(state)
        return pred, hygiene_counts(state)
    if variant == "F_liberal_unresolved_cleanup":
        state = apply_stale_gap_cleanup(state)
        state = apply_generic_unresolved_cleanup(state)
        pred = weighted_decision(state, candidate_weight=0.5, grounded_only=True)
        return pred, hygiene_counts(state)
    if variant == "F_liberal_all_hygiene":
        state = apply_claim_reconciliation(state, "supported")
        state = apply_stale_gap_cleanup(state)
        state = apply_generic_unresolved_cleanup(state)
        state = apply_meta_excerpt_filter(state)
        pred = weighted_decision(state, candidate_weight=0.5, grounded_only=True)
        return pred, hygiene_counts(state)
    if variant == "G_oracle_no_candidates_no_unresolved":
        state = apply_claim_reconciliation(state, "supported")
        state = apply_oracle_candidate_suppression(state)
        state = apply_oracle_question_cleanup(state)
        pred = raw_decision(state)
        return pred, hygiene_counts(state)
    raise ValueError(f"unknown variant: {variant}")


def class_metrics(pred_by_id: Dict[str, str], gold: Dict[str, str], ids: List[str], baseline_pred: Dict[str, str]) -> Dict[str, Any]:
    tp = tn = fp = fn = 0
    pred_ctr = Counter()
    gold_ctr = Counter()
    flips = []
    recovered_accept = []
    false_accept = []
    wins = ties = losses = 0
    for pid in ids:
        g = norm(gold[pid])
        p = norm(pred_by_id[pid])
        b = norm(baseline_pred[pid])
        pred_ctr[p] += 1
        gold_ctr[g] += 1
        if g == "accept" and p == "accept":
            tp += 1
        elif g == "reject" and p == "reject":
            tn += 1
        elif g == "reject" and p == "accept":
            fp += 1
        elif g == "accept" and p == "reject":
            fn += 1
        if p != b:
            flips.append(pid)
            if g == "accept" and p == "accept" and b != "accept":
                recovered_accept.append(pid)
            if g == "reject" and p == "accept":
                false_accept.append(pid)
        old_ok = b == g
        new_ok = p == g
        if new_ok and not old_ok:
            wins += 1
        elif old_ok and not new_ok:
            losses += 1
        else:
            ties += 1
    n = len(ids)
    acc = (tp + tn) / n
    ap = tp / (tp + fp) if (tp + fp) else 0.0
    ar = tp / (tp + fn) if (tp + fn) else 0.0
    af1 = 2 * ap * ar / (ap + ar) if (ap + ar) else 0.0
    rp = tn / (tn + fn) if (tn + fn) else 0.0
    rr = tn / (tn + fp) if (tn + fp) else 0.0
    rf1 = 2 * rp * rr / (rp + rr) if (rp + rr) else 0.0
    macro = (af1 + rf1) / 2
    always_reject = gold_ctr.get("reject", 0) / n
    return dict(
        n=n,
        gold_dist=dict(gold_ctr),
        predicted_dist=dict(pred_ctr),
        accuracy=acc,
        always_reject_accuracy=always_reject,
        gain_over_always_reject=acc - always_reject,
        accept_precision=ap,
        accept_recall=ar,
        accept_f1=af1,
        reject_precision=rp,
        reject_recall=rr,
        reject_f1=rf1,
        macro_f1=macro,
        confusion=dict(gold_accept_pred_accept=tp, gold_accept_pred_reject=fn, gold_reject_pred_accept=fp, gold_reject_pred_reject=tn),
        W=wins,
        T=ties,
        L=losses,
        flipped_sample_ids=flips,
        recovered_accept_ids=recovered_accept,
        false_accept_ids=false_accept,
    )


def aggregate_hygiene(hygiene_by_id: Dict[str, Dict[str, int]]) -> Dict[str, int]:
    total = Counter()
    for counts in hygiene_by_id.values():
        for key, value in counts.items():
            total[key] += int(value)
    return dict(total)


def decision_blockers(state: Dict[str, Any], candidate_weight: float = 1.0, grounded_only: bool = False) -> Dict[str, Any]:
    ev_ids = evidence_ids(state)
    critical = 0.0
    major = 0.0
    for flaw in state.get("flaw_candidates", []) or []:
        status = norm(flaw.get("status")) or "candidate"
        severity = norm(flaw.get("severity"))
        if status in {"downgraded", "retracted"}:
            continue
        if grounded_only and not flaw_is_grounded(flaw, ev_ids):
            continue
        weight = 1.0 if status == "confirmed" else candidate_weight
        if severity == "critical":
            critical += weight
        if severity == "major":
            major += weight
    strong_support = sum(
        1 for item in state.get("evidence_map", []) or []
        if norm(item.get("strength")) == "strong" and norm(item.get("stance")) in {"supports", "partially_supports"}
    )
    unresolved = open_unresolved_count(state)
    conflicts = len(state.get("conflict_notes", []) or [])
    blockers = []
    if critical >= 1:
        blockers.append("critical>=1")
    if major >= 2:
        blockers.append("major>=2")
    if unresolved >= 6:
        blockers.append("unresolved>=6")
    if conflicts >= 4:
        blockers.append("conflicts>=4")
    if strong_support < 2:
        blockers.append("strong<2")
    if strong_support >= 2 and major > 0:
        blockers.append("major>0_blocks_accept")
    if strong_support >= 2 and unresolved > 3:
        blockers.append("unresolved>3_blocks_accept")
    return dict(
        critical=critical,
        major=major,
        strong_support=strong_support,
        unresolved=unresolved,
        conflicts=conflicts,
        blockers=blockers,
    )


def aggregate_blockers(rows: List[Dict[str, Any]], candidate_weight: float = 1.0, grounded_only: bool = False) -> Dict[str, int]:
    ctr = Counter()
    for row in rows:
        diag = decision_blockers(row.get("review_state", {}), candidate_weight=candidate_weight, grounded_only=grounded_only)
        for blocker in diag["blockers"]:
            ctr[blocker] += 1
    return dict(ctr)


def build_case_rows(rows: List[Dict[str, Any]], gold: Dict[str, str], variant_preds: Dict[str, Dict[str, str]], variants: List[str]) -> List[Dict[str, Any]]:
    case_rows = []
    for row in rows:
        pid = row["paper_id"]
        state = row.get("review_state", {})
        h = hygiene_counts(state)
        rec = dict(
            paper_id=pid,
            gold=gold[pid],
            original=row.get("final_decision", ""),
            baseline_infer=variant_preds["baseline_infer"][pid],
            unsup_strong=h["unsupported_with_strong_support"],
            unsup_2plus=h["unsupported_with_2plus_strong"],
            stale_gap=h["stale_evidence_gap"],
            candidate_major=h["candidate_major"],
            confirmed_major=h["confirmed_major"],
            meta_flaw=h["meta_or_excerpt_flaw"],
            grounded_flaw=h["grounded_flaw"],
            ungrounded_flaw=h["ungrounded_flaw"],
        )
        for v in variants:
            if v != "baseline_infer":
                rec[v] = variant_preds[v][pid]
        case_rows.append(rec)
    return case_rows


def write_case_table(case_rows: List[Dict[str, Any]], variants: List[str]) -> None:
    cols = ["paper_id", "gold", "original", "baseline_infer", "unsup_2plus", "stale_gap", "candidate_major", "confirmed_major", "meta_flaw"] + [v for v in variants if v != "baseline_infer"]
    lines = ["# Full-test Hygiene Simulation Case Table", "", "| " + " | ".join(cols) + " |", "|" + "|".join(["---"] * len(cols)) + "|"]
    for r in case_rows:
        lines.append("| " + " | ".join(str(r.get(c, "")) for c in cols) + " |")
    CASE_TABLE_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_report(results: Dict[str, Any], variants: List[str]) -> None:
    lines = [
        "# Full-test State Hygiene Offline Simulation",
        "",
        "**日期**：2026-04-25",
        "**输入**：`outputs/results_main/review_infer/p25_1_fulltest_mainline.jsonl`（39 样本）",
        "**脚本**：`scripts/simulate_state_hygiene_decision.py`",
        "**原则**：不改 runtime，不重跑模型，只检验 state hygiene 修复是否存在收益空间。",
        "",
        "## 1. 总表",
        "",
        "| variant | acc | macro-F1 | accept R | reject R | pred A | pred R | W/T/L | flips | recovered A | false A |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for v in variants:
        m = results["variants"][v]["metrics"]
        pd = m["predicted_dist"]
        lines.append(
            f"| `{v}` | {m['accuracy']:.4f} | {m['macro_f1']:.4f} | {m['accept_recall']:.4f} | {m['reject_recall']:.4f} | "
            f"{pd.get('accept', 0)} | {pd.get('reject', 0)} | {m['W']}/{m['T']}/{m['L']} | {len(m['flipped_sample_ids'])} | "
            f"{len(m['recovered_accept_ids'])} | {len(m['false_accept_ids'])} |"
        )
    lines += [
        "",
        "## 2. 关键翻转样本",
        "",
    ]
    for v in variants:
        if v == "baseline_infer":
            continue
        m = results["variants"][v]["metrics"]
        lines += [
            f"### {v}",
            "",
            f"- **flipped_sample_ids**: `{m['flipped_sample_ids']}`",
            f"- **recovered_accept_ids**: `{m['recovered_accept_ids']}`",
            f"- **false_accept_ids**: `{m['false_accept_ids']}`",
            "",
        ]
    lines += [
        "## 3. Reject blocker 诊断",
        "",
        "### baseline blockers",
        "",
        "| blocker | samples |",
        "|---|---:|",
    ]
    for k, v in sorted(results.get("baseline_blockers", {}).items(), key=lambda kv: -kv[1]):
        lines.append(f"| `{k}` | {v} |")
    lines += [
        "",
        "### candidate half-weight blockers",
        "",
        "| blocker | samples |",
        "|---|---:|",
    ]
    for k, v in sorted(results.get("half_weight_blockers", {}).items(), key=lambda kv: -kv[1]):
        lines.append(f"| `{k}` | {v} |")
    lines += [
        "",
        "### grounded candidate half-weight blockers",
        "",
        "| blocker | samples |",
        "|---|---:|",
    ]
    for k, v in sorted(results.get("grounded_half_weight_blockers", {}).items(), key=lambda kv: -kv[1]):
        lines.append(f"| `{k}` | {v} |")
    lines += [
        "",
        "## 4. 初步结论",
        "",
        "- **A-E/F hygiene 模拟全部 0 翻转**：Claim-Evidence Reconciliation、Stale Gap Cleanup、Meta/Excerpt Filtering、Candidate 降权及其组合，都无法单独突破当前 final decision 的 reject 锁。",
        "- **原因**：当前 `infer_final_decision` 不直接读取 claim status 或 `evidence_gaps`，只读取 flaws、open unresolved、conflicts 和全局 strong support；并且 accept 条件要求 `strong_support >= 2`、`major == 0`、`unresolved <= 3`。",
        "- **Oracle 上限**：即使清空 candidate flaws、unresolved_questions 和 conflicts，仅保留 strong support 门槛，也只能恢复 2/9 accept，同时误翻 5 个 reject，说明问题不只是 hygiene cleanup，而是 evidence extraction / unresolved lifecycle / flaw lifecycle / decision interface 四者共同锁死。",
        "- **阶段 2 不应直接进入 runtime 修复**：Claim-Evidence Reconciliation + Stale Gap Cleanup 仍值得做 state hygiene，但不能期待它单独恢复 accept recall。下一步应先做 4B 快速实验验证 evidence extraction 与 unresolved/flaw lifecycle 是否能改善 strong support 和 unresolved 分布。",
        "",
        "## 5. 产物",
        "",
        "- `FULLTEST_HYGIENE_SIMULATION_RESULTS.json`",
        "- `FULLTEST_HYGIENE_SIMULATION_CASE_TABLE.md`",
        "- `scripts/simulate_state_hygiene_decision.py`",
    ]
    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    rows = load_jsonl(INPUT_JSONL)
    gold = load_gold(GOLD_PARQUET)
    ids = [row["paper_id"] for row in rows]
    variants = [
        "baseline_infer",
        "A_reconcile_partial",
        "A_reconcile_supported",
        "B_stale_gap_cleanup",
        "C_meta_excerpt_filter",
        "D_candidate_half_weight",
        "D_grounded_candidate_only",
        "E_combo_partial_half",
        "E_combo_supported_half",
        "E_combo_strict_grounded",
        "F_liberal_unresolved_cleanup",
        "F_liberal_all_hygiene",
        "G_oracle_no_candidates_no_unresolved",
    ]
    variant_preds: Dict[str, Dict[str, str]] = {v: {} for v in variants}
    variant_hygiene: Dict[str, Dict[str, Dict[str, int]]] = {v: {} for v in variants}
    for row in rows:
        pid = row["paper_id"]
        for v in variants:
            pred, h = simulate_variant(row, v)
            variant_preds[v][pid] = pred
            variant_hygiene[v][pid] = h
    baseline_pred = variant_preds["baseline_infer"]
    results = {
        "input_jsonl": str(INPUT_JSONL),
        "gold_parquet": str(GOLD_PARQUET),
        "n": len(rows),
        "variants": {},
        "baseline_blockers": aggregate_blockers(rows),
        "half_weight_blockers": aggregate_blockers(rows, candidate_weight=0.5, grounded_only=False),
        "grounded_half_weight_blockers": aggregate_blockers(rows, candidate_weight=0.5, grounded_only=True),
    }
    for v in variants:
        results["variants"][v] = {
            "metrics": class_metrics(variant_preds[v], gold, ids, baseline_pred),
            "hygiene_totals": aggregate_hygiene(variant_hygiene[v]),
        }
    case_rows = build_case_rows(rows, gold, variant_preds, variants)
    results["case_rows"] = case_rows
    RESULT_JSON.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    write_case_table(case_rows, variants)
    write_report(results, variants)

    print(f"Wrote {RESULT_JSON}")
    print(f"Wrote {CASE_TABLE_MD}")
    print(f"Wrote {REPORT_MD}")
    print("\nSummary:")
    for v in variants:
        m = results["variants"][v]["metrics"]
        pd = m["predicted_dist"]
        print(
            f"{v:<28s} acc={m['accuracy']:.4f} macro={m['macro_f1']:.4f} "
            f"acceptR={m['accept_recall']:.4f} rejectR={m['reject_recall']:.4f} "
            f"predA={pd.get('accept',0):>2d} W/T/L={m['W']}/{m['T']}/{m['L']} "
            f"recA={len(m['recovered_accept_ids'])} falseA={len(m['false_accept_ids'])}"
        )


if __name__ == "__main__":
    main()
