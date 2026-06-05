#!/usr/bin/env python3
"""Comprehensive comparison: 10-sample subset vs 39-sample full test.

Answers:
  - Is the mainline's 10-sample reward an artifact of data skew?
  - How does full test decision acc compare to always-reject baseline?
  - Per-gold-decision reward breakdown (accept samples vs reject samples)
  - Sub-reward component differences
  - Bug B "confirmed-only flaws" simulation impact
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from statistics import mean

import pyarrow.parquet as pq


def load_jsonl(p):
    return [json.loads(l) for l in open(p)]


def norm(d):
    return str(d or "").strip().lower()


def stats(rows, gold_map, label):
    n = len(rows)
    rewards = [r["reward"] for r in rows]
    preds = Counter(r["final_decision"] for r in rows)
    decision_correct = sum(1 for r in rows if r.get("decision_correct", 0) >= 1.0)
    always_reject = sum(1 for r in rows if norm(gold_map.get(r["paper_id"], "")) == "reject")
    accept_recall_num = sum(
        1 for r in rows
        if norm(gold_map.get(r["paper_id"], "")) == "accept"
        and norm(r.get("final_decision", "")) == "accept"
    )
    accept_gold = sum(1 for r in rows if norm(gold_map.get(r["paper_id"], "")) == "accept")
    sub_means = defaultdict(list)
    for r in rows:
        for k, v in r.get("reward_breakdown", {}).items():
            if isinstance(v, (int, float)):
                sub_means[k].append(v)
    sub = {k: mean(vs) for k, vs in sub_means.items()}
    return dict(
        label=label, n=n,
        pred_dist=dict(preds),
        reward_mean=mean(rewards),
        reward_min=min(rewards), reward_max=max(rewards),
        decision_correct=decision_correct,
        decision_acc=decision_correct / n,
        always_reject_baseline=always_reject,
        always_reject_acc=always_reject / n,
        accept_recall=f"{accept_recall_num}/{accept_gold}",
        sub_rewards=sub,
    )


def simulate_bug_b_rule(rows, gold_map):
    """Simulate the 'confirmed-only flaws' proposed rule."""
    flips_r2a, flips_a2r = [], []
    cur_correct = new_correct = 0
    for r in rows:
        pid = r["paper_id"]
        gold = norm(gold_map.get(pid, ""))
        cur_pred = norm(r.get("final_decision", ""))
        rs = r.get("review_state", {})
        flaws = rs.get("flaw_candidates", [])
        crit_conf = sum(1 for f in flaws if f.get("severity") == "critical" and f.get("status") == "confirmed")
        major_conf = sum(1 for f in flaws if f.get("severity") == "major" and f.get("status") == "confirmed")
        crit_cand = sum(1 for f in flaws if f.get("severity") == "critical" and f.get("status") == "candidate")
        major_cand = sum(1 for f in flaws if f.get("severity") == "major" and f.get("status") == "candidate")
        strong = sum(
            1 for e in rs.get("evidence_map", [])
            if e.get("strength") == "strong" and e.get("stance") in {"supports", "partially_supports"}
        )
        unresolved = sum(1 for q in rs.get("unresolved_questions", []) if q.get("status") != "resolved")
        conflicts = len(rs.get("conflict_notes", []))

        if crit_conf > 0 or major_conf >= 2:
            new_pred = "reject"
        elif crit_cand >= 1 or major_cand >= 3 or unresolved >= 6 or conflicts >= 4:
            new_pred = "reject"
        elif strong >= 2 and major_cand <= 2 and unresolved < 6:
            new_pred = "accept"
        else:
            new_pred = "reject"

        if cur_pred == gold: cur_correct += 1
        if new_pred == gold: new_correct += 1

        if cur_pred != new_pred:
            if cur_pred == "reject" and new_pred == "accept":
                flips_r2a.append((pid, gold))
            else:
                flips_a2r.append((pid, gold))

    return dict(
        cur_correct=cur_correct, new_correct=new_correct,
        flips_r2a=flips_r2a, flips_a2r=flips_a2r,
    )


def tqc_distribution(rows):
    ctr = Counter()
    push_ctr = Counter()
    total = total_push = 0
    for r in rows:
        for t in r.get("turn_logs", []):
            ctr[t.get("recovery_readiness_label", "unknown")] += 1
            total += 1
            if t.get("recovery_push_triggered"):
                push_ctr[t.get("recovery_readiness_label", "unknown")] += 1
                total_push += 1
    return ctr, push_ctr, total, total_push


def main():
    gold = {
        r["id"]: r["decision"]
        for r in pq.read_table("/reviewF/datasets/drmas_review/test.parquet").to_pylist()
    }

    full = load_jsonl("outputs/results_main/review_infer/p25_1_fulltest_mainline.jsonl")
    tqc_sub = load_jsonl("outputs/results_main/review_infer/p25_1_tqc_v1_l3.jsonl")
    ff2_sub = load_jsonl("outputs/results_main/review_infer/p25_1_flaw_fix_v2_l3.jsonl")

    print("# Mainline: 10-sample subset vs 39-sample full test comparison\n")
    print("## Table 1: Overall comparison\n")
    print(f"{'config':<26s} {'n':>3s} {'reward':>8s} {'min':>8s} {'max':>8s}  "
          f"{'dec_corr':>10s}  {'baseline_ar':>12s}  {'acc_rec':>8s}  pred_dist")
    for s in [
        stats(ff2_sub, gold, "flaw_fix_v2 (10-subset)"),
        stats(tqc_sub, gold, "tqc_v1      (10-subset)"),
        stats(full,    gold, "fulltest    (39-full)"),
    ]:
        dec_s = f"{s['decision_correct']}/{s['n']}={100*s['decision_acc']:.1f}%"
        bas_s = f"{s['always_reject_baseline']}/{s['n']}={100*s['always_reject_acc']:.1f}%"
        print(
            f"{s['label']:<26s} {s['n']:>3d} "
            f"{s['reward_mean']:>8.4f} {s['reward_min']:>8.4f} {s['reward_max']:>8.4f}  "
            f"{dec_s:>10s}  {bas_s:>12s}  {s['accept_recall']:>8s}  {s['pred_dist']}"
        )

    print("\n## Table 2: Sub-reward component means\n")
    components = ["decision", "rating_align", "decision_line_bonus", "section_presence",
                  "summary_align", "strength_align", "weakness_align", "suggestion_align",
                  "global_align", "critique", "stance_align", "penalty", "total"]
    s_ff2 = stats(ff2_sub, gold, "")["sub_rewards"]
    s_tqc = stats(tqc_sub, gold, "")["sub_rewards"]
    s_full = stats(full, gold, "")["sub_rewards"]
    print(f"{'component':<22s} {'ff2 (10)':>10s} {'tqc (10)':>10s} {'full (39)':>12s} {'delta full-tqc':>16s}")
    for c in components:
        a, b, c2 = s_ff2.get(c, 0), s_tqc.get(c, 0), s_full.get(c, 0)
        delta = c2 - b
        print(f"{c:<22s} {a:>10.4f} {b:>10.4f} {c2:>12.4f} {delta:>+16.4f}")

    print("\n## Table 3: Per-gold-decision breakdown (39 full test)\n")
    by_gold = defaultdict(list)
    for r in full:
        by_gold[norm(gold.get(r["paper_id"], ""))].append(r)
    print(f"{'gold':<10s} {'n':>4s} {'reward_mean':>12s} {'decision':>10s} {'rating_align':>13s} "
          f"{'stance_align':>13s} {'critique':>10s} {'weakness_align':>15s}")
    for g in ["accept", "reject"]:
        rows = by_gold.get(g, [])
        if not rows:
            continue
        n = len(rows)
        rm = mean(r["reward"] for r in rows)
        dc = mean(r["reward_breakdown"].get("decision", 0) for r in rows)
        ra = mean(r["reward_breakdown"].get("rating_align", 0) for r in rows)
        sa = mean(r["reward_breakdown"].get("stance_align", 0) for r in rows)
        cr = mean(r["reward_breakdown"].get("critique", 0) for r in rows)
        wa = mean(r["reward_breakdown"].get("weakness_align", 0) for r in rows)
        print(f"{g:<10s} {n:>4d} {rm:>12.4f} {dc:>10.4f} {ra:>13.4f} {sa:>13.4f} {cr:>10.4f} {wa:>15.4f}")

    print("\n## Table 4: Confusion matrix (full test)\n")
    tp = tn = fp = fn = 0
    for r in full:
        g = norm(gold.get(r["paper_id"], ""))
        p = norm(r.get("final_decision", ""))
        if g == "accept" and p == "accept": tp += 1
        elif g == "reject" and p == "reject": tn += 1
        elif g == "reject" and p == "accept": fp += 1
        elif g == "accept" and p == "reject": fn += 1
    print(f"{'':<15s} {'pred=accept':>12s} {'pred=reject':>12s}")
    print(f"{'gold=accept':<15s} {tp:>12d} {fn:>12d}")
    print(f"{'gold=reject':<15s} {fp:>12d} {tn:>12d}")

    print("\n## Table 5: Bug B simulation on full test (confirmed-only flaws rule)\n")
    sim = simulate_bug_b_rule(full, gold)
    print(f"Current rule:   {sim['cur_correct']}/39 = {100*sim['cur_correct']/39:.1f}%")
    print(f"Proposed rule:  {sim['new_correct']}/39 = {100*sim['new_correct']/39:.1f}%")
    print(f"Delta: {sim['new_correct'] - sim['cur_correct']:+d} correct")
    print(f"\nFlips reject->accept (n={len(sim['flips_r2a'])}):")
    for pid, g in sim["flips_r2a"]:
        sign = "+" if g == "accept" else "-"
        print(f"  {sign} {pid}  gold={g}")
    print(f"\nFlips accept->reject (n={len(sim['flips_a2r'])}):")
    for pid, g in sim["flips_a2r"]:
        sign = "+" if g == "reject" else "-"
        print(f"  {sign} {pid}  gold={g}")

    print("\n## Table 6: TQC readiness distribution (full test)\n")
    ctr, push_ctr, total, total_push = tqc_distribution(full)
    print(f"{'readiness':<35s} {'turns':>6s} {'%':>6s} {'push':>6s} {'%push':>7s}")
    for k in ["ready_for_aggressive_recovery", "needs_target_refinement",
              "needs_evidence_grounding", "fallback_bridge_only", "not_ready_for_recovery"]:
        n = ctr.get(k, 0)
        np_ = push_ctr.get(k, 0)
        pct = 100 * n / total if total else 0
        pct_push = 100 * np_ / total_push if total_push else 0
        print(f"{k:<35s} {n:>6d} {pct:>5.1f}% {np_:>6d} {pct_push:>6.1f}%")
    print(f"{'TOTAL':<35s} {total:>6d}        {total_push:>6d}")

    print("\n## Table 7: Per-sample (39 full test, sorted by reward)\n")
    print(f"{'paper_id':<14s} {'gold':<8s} {'pred':<8s} {'reward':>8s} {'dec_c':>6s} {'rating':>7s} {'stance':>7s}")
    sorted_full = sorted(full, key=lambda r: r["reward"])
    for r in sorted_full:
        g = gold.get(r["paper_id"], "?")
        p = r.get("final_decision", "?")
        rb = r.get("reward_breakdown", {})
        print(f"{r['paper_id']:<14s} {g:<8s} {p:<8s} {r['reward']:>8.4f} "
              f"{r.get('decision_correct', 0):>6.1f} {rb.get('rating_align', 0):>7.4f} {rb.get('stance_align', 0):>7.4f}")


if __name__ == "__main__":
    main()
