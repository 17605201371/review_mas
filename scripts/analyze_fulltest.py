#!/usr/bin/env python3
"""Analyze full test.parquet inference results.

Answers:
  Q1. Decision accuracy vs always-reject baseline (77% on 30/9 split)
  Q2. Accept / reject confusion matrix
  Q3. Reward distribution and per-gold breakdown
  Q4. Would a "confirmed-only" flaw rule change any predictions?
  Q5. TQC readiness distribution on full test
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path


def load_rows(p: str) -> list[dict]:
    rows = []
    with open(p) as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def load_gold(parquet_path: str) -> dict[str, str]:
    import pyarrow.parquet as pq
    t = pq.read_table(parquet_path).to_pylist()
    return {r["id"]: r["decision"] for r in t}


def norm(d: str) -> str:
    return str(d or "").strip().lower()


def q1_accuracy(rows, gold_map):
    print("=== Q1. Decision accuracy ===")
    total = len(rows)
    correct_pred = 0
    always_reject_correct = 0
    preds = Counter()
    golds = Counter()
    for r in rows:
        pid = r["paper_id"]
        pred = norm(r.get("final_decision", ""))
        gold = norm(gold_map.get(pid, ""))
        preds[pred] += 1
        golds[gold] += 1
        if pred == gold:
            correct_pred += 1
        if "reject" == gold:
            always_reject_correct += 1
    print(f"Samples: {total}")
    print(f"System: {correct_pred}/{total} = {100*correct_pred/total:.1f}%")
    print(f"Always-reject baseline: {always_reject_correct}/{total} = {100*always_reject_correct/total:.1f}%")
    print(f"Prediction distribution: {dict(preds)}")
    print(f"Gold distribution:       {dict(golds)}")
    print()


def q2_confusion(rows, gold_map):
    print("=== Q2. Confusion matrix ===")
    tp = tn = fp = fn = 0
    for r in rows:
        gold = norm(gold_map.get(r["paper_id"], ""))
        pred = norm(r.get("final_decision", ""))
        if gold == "accept" and pred == "accept": tp += 1
        elif gold == "reject" and pred == "reject": tn += 1
        elif gold == "reject" and pred == "accept": fp += 1
        elif gold == "accept" and pred == "reject": fn += 1
    print(f"{'':<15s} {'pred=accept':>12s} {'pred=reject':>12s}")
    print(f"{'gold=accept':<15s} {tp:>12d} {fn:>12d}")
    print(f"{'gold=reject':<15s} {fp:>12d} {tn:>12d}")
    total_acc = tp + fn
    if total_acc:
        print(f"\nAccept recall: {tp}/{total_acc} = {100*tp/total_acc:.1f}%")
    if (tp + fp):
        print(f"Accept precision: {tp}/{tp+fp} = {100*tp/(tp+fp):.1f}%")
    print()


def q3_reward(rows, gold_map):
    print("=== Q3. Reward distribution ===")
    rewards = [r.get("reward", 0) for r in rows]
    print(f"Overall mean: {sum(rewards)/len(rewards):.4f}")
    for g in ["accept", "reject"]:
        rg = [r["reward"] for r in rows if norm(gold_map.get(r["paper_id"], "")) == g]
        if rg:
            print(f"  gold={g}: n={len(rg)}  mean={sum(rg)/len(rg):.4f}  min={min(rg):.4f}  max={max(rg):.4f}")
    print()


def q4_simulate_confirmed_only(rows, gold_map):
    """Simulate the proposed "confirmed only" decision rule on stored review_state."""
    print("=== Q4. Simulate 'confirmed-only flaws' decision rule ===")
    flips_a2r = []  # accept -> reject flips
    flips_r2a = []  # reject -> accept flips
    new_correct = 0
    cur_correct = 0
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

        # Proposed rule
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

    n = len(rows)
    print(f"Current rule:   {cur_correct}/{n} = {100*cur_correct/n:.1f}%")
    print(f"Proposed rule:  {new_correct}/{n} = {100*new_correct/n:.1f}%")
    print(f"Delta: {new_correct - cur_correct:+d} correct")
    print(f"Flips reject->accept (n={len(flips_r2a)}):")
    for pid, g in flips_r2a:
        sign = "+" if g == "accept" else "-"
        print(f"  {sign} {pid}  gold={g}")
    print(f"Flips accept->reject (n={len(flips_a2r)}):")
    for pid, g in flips_a2r:
        sign = "+" if g == "reject" else "-"
        print(f"  {sign} {pid}  gold={g}")
    print()


def q5_tqc_distribution(rows):
    print("=== Q5. TQC readiness distribution on full test ===")
    ctr = Counter()
    total = 0
    push_ctr = Counter()
    total_push = 0
    for r in rows:
        for t in r.get("turn_logs", []):
            ctr[t.get("recovery_readiness_label", "unknown")] += 1
            total += 1
            if t.get("recovery_push_triggered"):
                push_ctr[t.get("recovery_readiness_label", "unknown")] += 1
                total_push += 1
    for k in ["ready_for_aggressive_recovery", "needs_target_refinement",
              "needs_evidence_grounding", "fallback_bridge_only", "not_ready_for_recovery"]:
        n = ctr.get(k, 0)
        np_ = push_ctr.get(k, 0)
        pct = 100 * n / total if total else 0
        pct_push = 100 * np_ / total_push if total_push else 0
        print(f"  {k:34s} turns={n:4d} ({pct:5.1f}%)   push={np_:4d} ({pct_push:5.1f}%)")
    print()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("results_jsonl")
    parser.add_argument("--gold-parquet", default="/reviewF/datasets/drmas_review/test.parquet")
    args = parser.parse_args()

    rows = load_rows(args.results_jsonl)
    gold = load_gold(args.gold_parquet)
    print(f"Loaded {len(rows)} predictions from {args.results_jsonl}")
    print(f"Gold ids available: {len(gold)}")
    missing = [r["paper_id"] for r in rows if r["paper_id"] not in gold]
    if missing:
        print(f"WARNING: {len(missing)} predictions have no matching gold. First few: {missing[:3]}")
    print()

    q1_accuracy(rows, gold)
    q2_confusion(rows, gold)
    q3_reward(rows, gold)
    q4_simulate_confirmed_only(rows, gold)
    q5_tqc_distribution(rows)


if __name__ == "__main__":
    main()
