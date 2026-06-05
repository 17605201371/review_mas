#!/usr/bin/env python3
"""Full-test Decision Bias + State Hygiene Audit.

依据 EVALUATION_METRICS_CHARTER.md 第五节统一评估表, 在 full 39-sample 上
输出 A-E 五类指标.

用途:
  - 建立 mainline 的基线 hygiene 画像
  - 作为后续任何改动的对照
  - 在论文里给出具体的 state hygiene quantification
"""
from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from statistics import mean
from typing import Dict, List

import pyarrow.parquet as pq

# ---------------------------------------------------------------------------
# 0. Meta-phrase 模式: 检测系统元信息是否泄漏到 paper weakness
# ---------------------------------------------------------------------------
# 这些短语源自 recovery_failure_message, evidence_gaps 等系统输出, 不应出现在
# flaw description / final report 的 weakness 区.
META_PATTERNS = [
    r"insufficient\s+evidence\s+in\s+(?:the\s+)?provided\s+excerpt",
    r"(?:lack|lacks|lacking)\s+(?:.{0,60})in\s+(?:the\s+)?(?:provided\s+)?excerpt",
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


def text_has_meta(text: str) -> bool:
    if not text:
        return False
    return bool(META_REGEX.search(text))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def norm(s: str) -> str:
    return str(s or "").strip().lower()


def load_jsonl(p):
    return [json.loads(l) for l in open(p)]


# ---------------------------------------------------------------------------
# A. Decision Health
# ---------------------------------------------------------------------------
def section_A(rows: List[Dict], gold: Dict[str, str]):
    print("=" * 80)
    print("A. Decision Health")
    print("=" * 80)
    tp = tn = fp = fn = 0
    pred_ctr = Counter()
    gold_ctr = Counter()
    for r in rows:
        g = norm(gold.get(r["paper_id"], ""))
        p = norm(r.get("final_decision", ""))
        gold_ctr[g] += 1
        pred_ctr[p] += 1
        if g == "accept" and p == "accept": tp += 1
        elif g == "reject" and p == "reject": tn += 1
        elif g == "reject" and p == "accept": fp += 1
        elif g == "accept" and p == "reject": fn += 1
    n = len(rows)
    acc = (tp + tn) / n if n else 0

    # Accept class
    a_prec = tp / (tp + fp) if (tp + fp) else 0.0
    a_rec = tp / (tp + fn) if (tp + fn) else 0.0
    a_f1 = 2 * a_prec * a_rec / (a_prec + a_rec) if (a_prec + a_rec) else 0.0
    # Reject class
    r_prec = tn / (tn + fn) if (tn + fn) else 0.0
    r_rec = tn / (tn + fp) if (tn + fp) else 0.0
    r_f1 = 2 * r_prec * r_rec / (r_prec + r_rec) if (r_prec + r_rec) else 0.0
    macro_f1 = (a_f1 + r_f1) / 2

    ar = gold_ctr.get("reject", 0) / n if n else 0  # always-reject baseline
    gain = acc - ar

    print(f"  samples: {n}")
    print(f"  gold dist:       {dict(gold_ctr)}")
    print(f"  predicted dist:  {dict(pred_ctr)}")
    print()
    print(f"  confusion matrix:")
    print(f"    {'':<18s} {'pred=accept':>12s} {'pred=reject':>12s}")
    print(f"    {'gold=accept':<18s} {tp:>12d} {fn:>12d}")
    print(f"    {'gold=reject':<18s} {fp:>12d} {tn:>12d}")
    print()
    print(f"  accuracy:                 {acc:.4f}")
    print(f"  always-reject baseline:   {ar:.4f}")
    print(f"  gain over baseline:       {gain:+.4f}")
    print()
    print(f"  accept:  precision={a_prec:.4f}  recall={a_rec:.4f}  f1={a_f1:.4f}")
    print(f"  reject:  precision={r_prec:.4f}  recall={r_rec:.4f}  f1={r_f1:.4f}")
    print(f"  macro-F1:                 {macro_f1:.4f}")
    print()
    return dict(accuracy=acc, macro_f1=macro_f1, accept_recall=a_rec,
                baseline_acc=ar, gain=gain, predicted_accept=pred_ctr.get("accept", 0))


# ---------------------------------------------------------------------------
# B. State Hygiene
# ---------------------------------------------------------------------------
def section_B(rows: List[Dict]):
    print("=" * 80)
    print("B. State Hygiene")
    print("=" * 80)
    # Per-sample metrics
    ctr_total = Counter()
    per_sample = []

    for r in rows:
        pid = r["paper_id"]
        rs = r.get("review_state", {})
        claims = rs.get("claims", [])
        evidence = rs.get("evidence_map", [])
        flaws = rs.get("flaw_candidates", [])
        gaps = rs.get("evidence_gaps", [])
        report = r.get("final_report", "") or ""

        # Build per-claim strong support count
        strong_supports_by_claim = defaultdict(int)
        for e in evidence:
            if norm(e.get("strength")) == "strong" and norm(e.get("stance")) in {"supports", "partially_supports"}:
                strong_supports_by_claim[e.get("claim_id")] += 1
        strong_contra_by_claim = defaultdict(int)
        for e in evidence:
            if norm(e.get("strength")) == "strong" and norm(e.get("stance")) == "contradicts":
                strong_contra_by_claim[e.get("claim_id")] += 1

        # B1. unsupported with strong support
        unsup_with_strong = 0
        unsup_with_2plus = 0
        for c in claims:
            if norm(c.get("status")) == "unsupported":
                ss = strong_supports_by_claim.get(c.get("claim_id"), 0)
                if ss >= 1:
                    unsup_with_strong += 1
                if ss >= 2:
                    unsup_with_2plus += 1

        # B2. supported with strong contradiction
        sup_with_contra = 0
        for c in claims:
            if norm(c.get("status")) in {"supported", "partially_supported"}:
                if strong_contra_by_claim.get(c.get("claim_id"), 0) >= 1:
                    sup_with_contra += 1

        # B3. stale evidence gap: gap text exists but claim has strong support
        stale_gap = 0
        for gap_text in gaps:
            # try to extract claim id in the gap string (e.g., "Claim claim-1 lacks...")
            m = re.search(r"claim-(\d+)", str(gap_text).lower())
            if m:
                cid = f"claim-{m.group(1)}"
                if strong_supports_by_claim.get(cid, 0) >= 1:
                    stale_gap += 1

        # B4. candidate major used for reject: if final is reject and there are >=2 candidate major flaws
        candidate_major = sum(
            1 for f in flaws
            if norm(f.get("severity")) == "major" and norm(f.get("status")) == "candidate"
        )
        confirmed_major = sum(
            1 for f in flaws
            if norm(f.get("severity")) == "major" and norm(f.get("status")) == "confirmed"
        )
        candidate_reject = 1 if (norm(r.get("final_decision")) == "reject"
                                  and candidate_major >= 2 and confirmed_major == 0) else 0

        # B5. recovery failure echo: flaw description or evidence_gap contains meta phrases
        echo = 0
        for f in flaws:
            if text_has_meta(f.get("description", "") + " " + f.get("title", "")):
                echo += 1
        gap_echo = sum(1 for g in gaps if text_has_meta(str(g)))

        # B6. system meta in final report
        # Extract weakness section
        report_weakness_meta = 0
        m = re.search(r"Key\s+Weaknesses(.+?)(?:\d\.|$)", report, re.IGNORECASE | re.DOTALL)
        if m:
            weakness_block = m.group(1)
            # Count bullet lines matching meta
            for line in weakness_block.split("\n"):
                if text_has_meta(line):
                    report_weakness_meta += 1

        # B7. excerpt-limitation-as-weakness
        excerpt_limit = sum(
            1 for f in flaws
            if re.search(r"provided\s+excerpt", (f.get("description") or "") + " " + (f.get("title") or ""), re.IGNORECASE)
        )

        ctr_total["unsupported_with_strong_support"] += unsup_with_strong
        ctr_total["unsupported_with_2plus_strong"] += unsup_with_2plus
        ctr_total["supported_with_strong_contradiction"] += sup_with_contra
        ctr_total["stale_evidence_gap"] += stale_gap
        ctr_total["candidate_major_used_for_reject (sample)"] += candidate_reject
        ctr_total["recovery_failure_echo_flaws"] += echo
        ctr_total["meta_in_evidence_gaps"] += gap_echo
        ctr_total["system_meta_phrase_in_final_weakness"] += report_weakness_meta
        ctr_total["excerpt_limitation_as_weakness_flaw"] += excerpt_limit

        per_sample.append(dict(
            pid=pid,
            unsup_strong=unsup_with_strong,
            unsup_2plus=unsup_with_2plus,
            sup_contra=sup_with_contra,
            stale_gap=stale_gap,
            candidate_reject=candidate_reject,
            meta_flaws=echo,
            meta_gaps=gap_echo,
            meta_report=report_weakness_meta,
            excerpt_flaws=excerpt_limit,
        ))

    n = len(rows)
    print(f"{'metric':<50s} {'total':>7s} {'%samples affected':>20s}")
    for label, total_count in ctr_total.items():
        n_affected = sum(1 for s in per_sample if
                         (label == "unsupported_with_strong_support" and s["unsup_strong"]) or
                         (label == "unsupported_with_2plus_strong" and s["unsup_2plus"]) or
                         (label == "supported_with_strong_contradiction" and s["sup_contra"]) or
                         (label == "stale_evidence_gap" and s["stale_gap"]) or
                         (label == "candidate_major_used_for_reject (sample)" and s["candidate_reject"]) or
                         (label == "recovery_failure_echo_flaws" and s["meta_flaws"]) or
                         (label == "meta_in_evidence_gaps" and s["meta_gaps"]) or
                         (label == "system_meta_phrase_in_final_weakness" and s["meta_report"]) or
                         (label == "excerpt_limitation_as_weakness_flaw" and s["excerpt_flaws"])
                         )
        print(f"  {label:<50s} {total_count:>5d}   {100*n_affected/n:>6.1f}% ({n_affected}/{n})")
    print()
    return per_sample, ctr_total


# ---------------------------------------------------------------------------
# C. Evidence / Flaw Grounding
# ---------------------------------------------------------------------------
def section_C(rows: List[Dict]):
    print("=" * 80)
    print("C. Evidence / Flaw Grounding")
    print("=" * 80)

    ctr = Counter()
    per_sample = []
    for r in rows:
        rs = r.get("review_state", {})
        flaws = rs.get("flaw_candidates", [])
        evidence_ids_set = {e.get("evidence_id") for e in rs.get("evidence_map", [])}

        grounded = ungrounded = fallback = meta = 0
        confirmed = candidate = downgraded = retracted = 0
        for f in flaws:
            st = norm(f.get("status"))
            if st == "confirmed": confirmed += 1
            elif st == "candidate": candidate += 1
            elif st == "downgraded": downgraded += 1
            elif st == "retracted": retracted += 1

            # Grounded: has evidence_id AND evidence_id exists AND description does not contain meta
            f_eids = set(f.get("evidence_ids", []) or [])
            has_real_ev = bool(f_eids & evidence_ids_set)
            is_meta = text_has_meta((f.get("description") or "") + " " + (f.get("title") or ""))

            if is_meta:
                meta += 1
            if has_real_ev and not is_meta:
                grounded += 1
            elif has_real_ev and is_meta:
                # both: still ungrounded-by-meaning
                ungrounded += 1
            elif not has_real_ev:
                ungrounded += 1
                if not is_meta:
                    # Has no evidence but also not meta -> generic ungrounded
                    pass
                else:
                    fallback += 1  # ungrounded + meta = likely fallback-generated

        ctr["grounded_weakness"] += grounded
        ctr["ungrounded_weakness"] += ungrounded
        ctr["fallback_generated_flaw"] += fallback
        ctr["confirmed_flaw"] += confirmed
        ctr["candidate_flaw"] += candidate
        ctr["downgraded_flaw"] += downgraded
        ctr["retracted_flaw"] += retracted
        ctr["meta_flaw"] += meta

        per_sample.append(dict(
            pid=r["paper_id"],
            grounded=grounded, ungrounded=ungrounded, fallback=fallback, meta=meta,
            confirmed=confirmed, candidate=candidate,
        ))

    n = len(rows)
    total_flaws = (ctr["grounded_weakness"] + ctr["ungrounded_weakness"])
    print(f"{'metric':<30s} {'total':>6s}  rate (of flaws)")
    for k, v in ctr.items():
        rate = f"{100*v/total_flaws:.1f}%" if total_flaws else "-"
        print(f"  {k:<30s} {v:>6d}  {rate}")
    print()
    print(f"  total flaws (grounded+ungrounded) = {total_flaws}")
    print(f"  grounded rate = {100*ctr['grounded_weakness']/total_flaws:.1f}%" if total_flaws else "")
    return per_sample, ctr


# ---------------------------------------------------------------------------
# D. Recovery (already covered in analyze_recovery_effectiveness.py, summarize)
# ---------------------------------------------------------------------------
def section_D(rows: List[Dict]):
    print("=" * 80)
    print("D. Recovery Effectiveness")
    print("=" * 80)
    attempts = validated = committed = emitted = 0
    blocked_by_policy = 0
    no_effect = 0
    push_count = 0
    total_turns = 0

    for r in rows:
        for t in r.get("turn_logs", []):
            total_turns += 1
            if t.get("recovery_attempted"): attempts += 1
            if t.get("recovery_emitted"): emitted += 1
            if t.get("recovery_validated"): validated += 1
            if t.get("recovery_committed"): committed += 1
            if t.get("recovery_push_triggered"): push_count += 1
            if t.get("recovery_failure_code") == "BLOCKED_BY_POLICY":
                blocked_by_policy += 1
            # no-effect patch: committed but 0 new_items, 0 revision_events
            if (t.get("recovery_committed")
                and not t.get("new_items")
                and not t.get("revision_events")):
                no_effect += 1

    n = len(rows)
    print(f"  total turns: {total_turns}")
    print(f"  recovery_attempt_count:     {attempts}")
    print(f"  recovery_emitted_count:     {emitted}")
    print(f"  recovery_validated_count:   {validated}")
    print(f"  recovery_committed_count:   {committed}")
    print(f"  recovery_push_triggered:    {push_count}")
    print(f"  recovery_commit_rate:       {100*committed/attempts:.1f}%" if attempts else "N/A")
    print(f"  blocked_by_policy_count:    {blocked_by_policy}")
    print(f"  no_effect_patch_count:      {no_effect}")
    print()


# ---------------------------------------------------------------------------
# E. Target Quality
# ---------------------------------------------------------------------------
def section_E(rows: List[Dict]):
    print("=" * 80)
    print("E. Target Quality")
    print("=" * 80)
    label_ctr = Counter()
    recovery_by_label = Counter()
    total_turns = 0
    target_drift_events = 0

    for r in rows:
        prev_target_set = None
        for t in r.get("turn_logs", []):
            total_turns += 1
            label = t.get("target_quality_label", "unknown")
            label_ctr[label] += 1
            if t.get("recovery_push_triggered"):
                recovery_by_label[label] += 1
            cur = frozenset(t.get("final_action_target_claim_ids", []) or [])
            if prev_target_set is not None and cur and prev_target_set and cur != prev_target_set:
                # target changed across consecutive turns
                if not (cur.issubset(prev_target_set) or prev_target_set.issubset(cur)):
                    target_drift_events += 1
            prev_target_set = cur

    print(f"  total turns: {total_turns}")
    print(f"  target_drift_events (non-subset change turn-to-turn): {target_drift_events}")
    print()
    print(f"  {'target_quality_label':<30s} {'turns':>7s} {'%':>7s} {'recovery_pushes':>16s}")
    for label, cnt in sorted(label_ctr.items(), key=lambda kv: -kv[1]):
        pct = 100 * cnt / total_turns
        rp = recovery_by_label.get(label, 0)
        print(f"  {label:<30s} {cnt:>7d} {pct:>6.1f}% {rp:>16d}")
    print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    rows = load_jsonl("outputs/results_main/review_infer/p25_1_fulltest_mainline.jsonl")
    gold = {
        r["id"]: r["decision"]
        for r in pq.read_table("/reviewF/datasets/drmas_review/test.parquet").to_pylist()
    }

    print("# Full-test Decision Bias + State Hygiene Audit")
    print(f"# Source: outputs/results_main/review_infer/p25_1_fulltest_mainline.jsonl (n={len(rows)})")
    print(f"# Reference: EVALUATION_METRICS_CHARTER.md")
    print()

    section_A(rows, gold)
    section_B(rows)
    section_C(rows)
    section_D(rows)
    section_E(rows)

    # 额外: meta phrase 样本级案例
    print("=" * 80)
    print("APPENDIX: Meta-leak sample cases (show 5 worst)")
    print("=" * 80)
    meta_cases = []
    for r in rows:
        rs = r.get("review_state", {})
        flaws = rs.get("flaw_candidates", [])
        report = r.get("final_report", "") or ""
        meta_flaw_count = sum(1 for f in flaws
                              if text_has_meta((f.get("description") or "") + " " + (f.get("title") or "")))
        m = re.search(r"Key\s+Weaknesses(.+?)(?:\d\.|$)", report, re.IGNORECASE | re.DOTALL)
        meta_weak_count = 0
        if m:
            for line in m.group(1).split("\n"):
                if text_has_meta(line):
                    meta_weak_count += 1
        total = meta_flaw_count + meta_weak_count
        if total > 0:
            meta_cases.append((total, r["paper_id"], meta_flaw_count, meta_weak_count,
                               gold.get(r["paper_id"], "?"), r.get("final_decision", "?")))
    meta_cases.sort(reverse=True)
    print(f"{'paper_id':<14s} {'gold':<8s} {'pred':<8s} {'meta_flaws':>11s} {'meta_weak':>10s} {'total':>6s}")
    for total, pid, mf, mw, g, p in meta_cases[:10]:
        print(f"{pid:<14s} {g:<8s} {p:<8s} {mf:>11d} {mw:>10d} {total:>6d}")


if __name__ == "__main__":
    main()
