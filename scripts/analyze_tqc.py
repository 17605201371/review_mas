#!/usr/bin/env python3
"""Analyze Target Quality Certificate (TQC) labels from a Layer 3 run.

Answers the following questions:
  Q1. Distribution of recovery_readiness_label across all turns.
  Q2. When recovery is actually pushed (recovery_push_triggered=True), what
      recovery_readiness_label does the turn have? Ideally 'ready_for_...';
      if many are 'not_ready' or 'needs_*', the system is entering recovery
      too early.
  Q3. Per-sample: mean readiness distribution vs final reward and
      decision_correct — do low-reward samples have more 'not_ready' pushes?
  Q4. Action-type × readiness cross-tab: which action types most often run on
      which readiness state?
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path


READINESS_ORDER = [
    "ready_for_aggressive_recovery",
    "needs_target_refinement",
    "needs_evidence_grounding",
    "fallback_bridge_only",
    "not_ready_for_recovery",
]


def load_rows(path: str) -> list[dict]:
    rows = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def q1_overall_distribution(rows: list[dict]) -> None:
    ctr: Counter = Counter()
    total = 0
    for r in rows:
        for t in r.get("turn_logs", []):
            ctr[t.get("recovery_readiness_label", "unknown")] += 1
            total += 1
    print("=== Q1. Overall recovery_readiness_label distribution ===")
    print(f"Total turns: {total}")
    for label in READINESS_ORDER + [k for k in ctr if k not in READINESS_ORDER]:
        n = ctr.get(label, 0)
        if n == 0 and label in READINESS_ORDER:
            continue
        pct = 100.0 * n / total if total else 0
        print(f"  {label:34s} {n:4d}  ({pct:5.1f}%)")
    print()


def q2_recovery_push_vs_readiness(rows: list[dict]) -> None:
    pushed_readiness: Counter = Counter()
    not_pushed_readiness: Counter = Counter()
    for r in rows:
        for t in r.get("turn_logs", []):
            label = t.get("recovery_readiness_label", "unknown")
            if t.get("recovery_push_triggered"):
                pushed_readiness[label] += 1
            else:
                not_pushed_readiness[label] += 1

    total_pushed = sum(pushed_readiness.values())
    total_not = sum(not_pushed_readiness.values())
    print("=== Q2. recovery_push_triggered vs recovery_readiness_label ===")
    print(f"Total pushed turns: {total_pushed}  |  non-push turns: {total_not}")
    print(f"{'readiness':<34s}{'pushed':>8s}{'push_pct':>10s}{'non_push':>10s}{'non_push_pct':>14s}")
    for label in READINESS_ORDER:
        p = pushed_readiness.get(label, 0)
        n = not_pushed_readiness.get(label, 0)
        p_pct = 100.0 * p / total_pushed if total_pushed else 0
        n_pct = 100.0 * n / total_not if total_not else 0
        print(f"  {label:<32s}{p:>8d}{p_pct:>9.1f}%{n:>10d}{n_pct:>13.1f}%")
    print()

    # Summary: what fraction of pushes are on non-ready state?
    non_ready_pushes = sum(
        pushed_readiness.get(lbl, 0)
        for lbl in READINESS_ORDER
        if lbl != "ready_for_aggressive_recovery"
    )
    ready_pushes = pushed_readiness.get("ready_for_aggressive_recovery", 0)
    if total_pushed:
        print(
            f"  >> {non_ready_pushes}/{total_pushed} ({100.0 * non_ready_pushes / total_pushed:.1f}%) "
            f"pushes occur on NON-ready target (ready pushes: {ready_pushes})"
        )
    print()


def q3_per_sample(rows: list[dict]) -> None:
    print("=== Q3. Per-sample breakdown ===")
    print(
        f"{'paper_id':<16s}  {'reward':>7s}  {'dec':>3s}  "
        f"{'ready':>5s}  {'need_tr':>7s}  {'need_eg':>7s}  "
        f"{'fb_br':>5s}  {'not_rdy':>7s}  {'push_total':>10s}  {'push_non_ready':>14s}"
    )
    for r in sorted(rows, key=lambda x: x["paper_id"]):
        ctr: Counter = Counter()
        push_total = 0
        push_non_ready = 0
        for t in r.get("turn_logs", []):
            label = t.get("recovery_readiness_label", "unknown")
            ctr[label] += 1
            if t.get("recovery_push_triggered"):
                push_total += 1
                if label != "ready_for_aggressive_recovery":
                    push_non_ready += 1
        print(
            f"{r['paper_id']:<16s}  {r.get('reward', 0):7.4f}  "
            f"{int(r.get('decision_correct', 0)):>3d}  "
            f"{ctr.get('ready_for_aggressive_recovery', 0):>5d}  "
            f"{ctr.get('needs_target_refinement', 0):>7d}  "
            f"{ctr.get('needs_evidence_grounding', 0):>7d}  "
            f"{ctr.get('fallback_bridge_only', 0):>5d}  "
            f"{ctr.get('not_ready_for_recovery', 0):>7d}  "
            f"{push_total:>10d}  {push_non_ready:>14d}"
        )
    print()


def q4_action_x_readiness(rows: list[dict]) -> None:
    print("=== Q4. Action type × readiness label ===")
    cross: dict[str, Counter] = defaultdict(Counter)
    for r in rows:
        for t in r.get("turn_logs", []):
            action = t.get("action_type", "unknown")
            label = t.get("recovery_readiness_label", "unknown")
            cross[action][label] += 1
    actions = sorted(cross.keys())
    header = f"{'action_type':<34s}" + "".join(f"{lbl[:15]:>16s}" for lbl in READINESS_ORDER)
    print(header)
    for a in actions:
        row = f"{a:<34s}"
        for lbl in READINESS_ORDER:
            row += f"{cross[a].get(lbl, 0):>16d}"
        print(row)
    print()


def q5_push_source_vs_readiness(rows: list[dict]) -> None:
    print("=== Q5. recovery_push_source × readiness label (for pushed turns) ===")
    cross: dict[str, Counter] = defaultdict(Counter)
    for r in rows:
        for t in r.get("turn_logs", []):
            if not t.get("recovery_push_triggered"):
                continue
            src = t.get("recovery_push_source", "none")
            label = t.get("recovery_readiness_label", "unknown")
            cross[src][label] += 1
    if not cross:
        print("  (no recovery pushes observed)")
        print()
        return
    sources = sorted(cross.keys())
    header = f"{'push_source':<40s}" + "".join(f"{lbl[:15]:>16s}" for lbl in READINESS_ORDER)
    print(header)
    for s in sources:
        row = f"{s:<40s}"
        for lbl in READINESS_ORDER:
            row += f"{cross[s].get(lbl, 0):>16d}"
        print(row)
    print()


def q6_recovery_entry_defers(rows: list[dict]) -> None:
    print("=== Q6. Recovery Entry Decision defers ===")
    total_defers = 0
    defer_reasons: Counter = Counter()
    defer_targets: Counter = Counter()
    per_sample: dict[str, int] = {}
    for r in rows:
        c = 0
        for t in r.get("turn_logs", []):
            if t.get("recovery_entry_deferred"):
                total_defers += 1
                c += 1
                defer_reasons[t.get("recovery_entry_defer_reason", "")] += 1
                defer_targets[t.get("action_type", "")] += 1
        if c > 0:
            per_sample[r["paper_id"]] = c
    print(f"Total defers: {total_defers}")
    if total_defers:
        print(f"  By reason:   {dict(defer_reasons)}")
        print(f"  Redirected to: {dict(defer_targets)}")
        print(f"  Per sample: {per_sample}")
    print()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("results_path", help="Path to Layer 3 JSONL with TQC observability")
    args = parser.parse_args()

    rows = load_rows(args.results_path)
    print(f"Loaded {len(rows)} samples from {args.results_path}")
    print()

    q1_overall_distribution(rows)
    q2_recovery_push_vs_readiness(rows)
    q3_per_sample(rows)
    q4_action_x_readiness(rows)
    q5_push_source_vs_readiness(rows)
    q6_recovery_entry_defers(rows)


if __name__ == "__main__":
    main()
