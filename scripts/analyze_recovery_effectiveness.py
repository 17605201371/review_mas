#!/usr/bin/env python3
"""Recovery effectiveness analysis on full 39-sample test.

Question: 当 recovery_push 触发时, recovery 真的在修 error 吗?

维度:
  A. 整体 push 成功率 / 失败模式分布
  B. 按 readiness label 分桶: ready vs not_ready 的 push 是否有行为差异
  C. 按 push_source 分桶: sticky / evidence_progress / s4_override / manager_model 差异
  D. 每次 push 前后的 state delta (new_items / retracted / revision_events)
  E. target claim 的 status 变化 (new -> uncertain -> supported 等)
  F. recovery 成功与 final reward / stance_align 的相关性

证据 positioning: 这是"error recovery"维度的核心评估, 不用 decision accuracy 作指标.
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from statistics import mean, median
from typing import Dict, List


def load_jsonl(p):
    return [json.loads(l) for l in open(p)]


def main():
    rows = load_jsonl("outputs/results_main/review_infer/p25_1_fulltest_mainline.jsonl")
    total_samples = len(rows)

    # ---------------------------------------------------------------
    # Pass 1: collect all push events with pre/post summary
    # ---------------------------------------------------------------
    push_events: List[Dict] = []
    all_turns_count = 0
    for sample_idx, r in enumerate(rows):
        pid = r["paper_id"]
        tl = r.get("turn_logs", [])
        for i, t in enumerate(tl):
            all_turns_count += 1
            if not t.get("recovery_push_triggered"):
                continue
            # recovery attempted on this turn
            event = dict(
                sample=pid,
                turn_idx=i + 1,
                max_turns=len(tl),
                push_source=t.get("recovery_push_source", "unknown"),
                readiness=t.get("recovery_readiness_label", "unknown"),
                candidate_action=t.get("recovery_candidate_action", ""),
                effective_action=t.get("effective_action_type", ""),
                final_action=t.get("final_action_type", ""),
                target_type=t.get("recovery_target_type", ""),
                target_id=t.get("recovery_target_id", ""),
                target_claim_count=len(t.get("final_action_target_claim_ids", [])),
                target_flaw_count=len(t.get("target_flaw_ids", [])),
                tqc_source=t.get("tqc_target_source", ""),
                tqc_width=t.get("tqc_target_width", ""),
                tqc_grounding=t.get("tqc_evidence_grounding", ""),
                tqc_conflict=t.get("tqc_conflict_strength", ""),
                recovery_attempted=t.get("recovery_attempted", False),
                recovery_emitted=t.get("recovery_emitted", False),
                recovery_validated=t.get("recovery_validated", False),
                recovery_committed=t.get("recovery_committed", False),
                recovery_success=t.get("recovery_success", False),
                recovery_failure_code=t.get("recovery_failure_code", ""),
                resolved_conflict_count=t.get("resolved_conflict_count", 0),
                new_items_count=len(t.get("new_items", []) or []),
                retracted_items_count=len(t.get("retracted_items", []) or []),
                downgraded_items_count=len(t.get("downgraded_items", []) or []),
                revision_events_count=len(t.get("revision_events", []) or []),
                revised_entity_count=len(t.get("revised_entities", []) or []),
                old_status=t.get("old_status", ""),
                new_status=t.get("new_status", ""),
                status_changed=bool(t.get("new_status")) and t.get("new_status") != t.get("old_status"),
                conflicts_detected_count=len(t.get("conflicts_detected", []) or []),
                sample_reward=r["reward"],
                sample_stance_align=r.get("reward_breakdown", {}).get("stance_align", 0),
                sample_critique=r.get("reward_breakdown", {}).get("critique", 0),
                sample_dec_correct=r.get("decision_correct", 0),
            )
            push_events.append(event)

    print(f"Total samples: {total_samples}")
    print(f"Total turns: {all_turns_count}")
    print(f"Total recovery_push_triggered events: {len(push_events)}")
    print(f"Push rate: {100*len(push_events)/all_turns_count:.1f}% of all turns\n")

    # ---------------------------------------------------------------
    # A. Push commit / success / failure distribution
    # ---------------------------------------------------------------
    print("=" * 80)
    print("A. Recovery push outcome distribution")
    print("=" * 80)
    n = len(push_events)
    committed = sum(1 for e in push_events if e["recovery_committed"])
    validated_only = sum(1 for e in push_events if e["recovery_validated"] and not e["recovery_committed"])
    emitted_only = sum(1 for e in push_events if e["recovery_emitted"] and not e["recovery_validated"])
    attempted_only = sum(1 for e in push_events if e["recovery_attempted"] and not e["recovery_emitted"])
    not_attempted = sum(1 for e in push_events if not e["recovery_attempted"])
    print(f"  committed          = {committed}/{n} ({100*committed/n:.1f}%)")
    print(f"  validated not committed = {validated_only}/{n} ({100*validated_only/n:.1f}%)")
    print(f"  emitted not validated   = {emitted_only}/{n} ({100*emitted_only/n:.1f}%)")
    print(f"  attempted not emitted   = {attempted_only}/{n} ({100*attempted_only/n:.1f}%)")
    print(f"  not attempted           = {not_attempted}/{n} ({100*not_attempted/n:.1f}%)")
    print()

    # Failure code distribution
    print(f"  failure_code distribution:")
    fc_ctr = Counter(e["recovery_failure_code"] for e in push_events)
    for code, cnt in fc_ctr.most_common():
        label = code if code else "(empty/success)"
        print(f"    {label:<30s}  {cnt:>4d} ({100*cnt/n:.1f}%)")
    print()

    # ---------------------------------------------------------------
    # B. Push by readiness label
    # ---------------------------------------------------------------
    print("=" * 80)
    print("B. Push outcome by TQC readiness label")
    print("=" * 80)
    print(f"{'readiness':<35s} {'pushes':>8s} {'committed':>10s} {'%commit':>9s} {'status_chg':>11s} {'new_items':>10s} {'revis_evt':>10s}")
    by_readiness = defaultdict(list)
    for e in push_events:
        by_readiness[e["readiness"]].append(e)
    for k in ["ready_for_aggressive_recovery", "needs_target_refinement",
              "needs_evidence_grounding", "fallback_bridge_only", "not_ready_for_recovery"]:
        evs = by_readiness.get(k, [])
        if not evs:
            print(f"{k:<35s} {'0':>8s}")
            continue
        nn = len(evs)
        com = sum(1 for e in evs if e["recovery_committed"])
        sc = sum(1 for e in evs if e["status_changed"])
        ni = mean(e["new_items_count"] for e in evs)
        re_ = mean(e["revision_events_count"] for e in evs)
        print(f"{k:<35s} {nn:>8d} {com:>10d} {100*com/nn:>8.1f}% "
              f"{100*sc/nn:>10.1f}% {ni:>10.2f} {re_:>10.2f}")
    print()

    # ---------------------------------------------------------------
    # C. Push by source
    # ---------------------------------------------------------------
    print("=" * 80)
    print("C. Push outcome by push source")
    print("=" * 80)
    print(f"{'push_source':<35s} {'pushes':>8s} {'committed':>10s} {'%commit':>9s} {'status_chg':>11s} {'new_items':>10s} {'conflicts_res':>14s}")
    by_src = defaultdict(list)
    for e in push_events:
        by_src[e["push_source"]].append(e)
    for src, evs in sorted(by_src.items(), key=lambda kv: -len(kv[1])):
        nn = len(evs)
        com = sum(1 for e in evs if e["recovery_committed"])
        sc = sum(1 for e in evs if e["status_changed"])
        ni = mean(e["new_items_count"] for e in evs)
        cr = sum(e["resolved_conflict_count"] for e in evs)
        print(f"{src:<35s} {nn:>8d} {com:>10d} {100*com/nn:>8.1f}% "
              f"{100*sc/nn:>10.1f}% {ni:>10.2f} {cr:>14d}")
    print()

    # ---------------------------------------------------------------
    # D. State delta magnitude per push (aggregate)
    # ---------------------------------------------------------------
    print("=" * 80)
    print("D. State delta magnitude (per push event)")
    print("=" * 80)
    for field in ["new_items_count", "retracted_items_count", "downgraded_items_count",
                  "revision_events_count", "revised_entity_count", "resolved_conflict_count"]:
        vals = [e[field] for e in push_events]
        nonzero = sum(1 for v in vals if v > 0)
        print(f"  {field:<28s} mean={mean(vals):>6.2f}  median={median(vals):>5.1f}  max={max(vals):>3d}  nonzero={nonzero}/{n}={100*nonzero/n:.1f}%")
    print()

    # ---------------------------------------------------------------
    # E. Status transitions (old_status -> new_status)
    # ---------------------------------------------------------------
    print("=" * 80)
    print("E. Target status transitions (pushes that produced a status change)")
    print("=" * 80)
    status_changes = Counter()
    for e in push_events:
        if e["status_changed"]:
            status_changes[(e["old_status"] or "(empty)", e["new_status"] or "(empty)", e["target_type"])] += 1
    if status_changes:
        print(f"{'target_type':<10s} {'old_status':<15s} {'new_status':<15s} {'count':>6s}")
        for (old, new, ttype), cnt in status_changes.most_common():
            print(f"{ttype:<10s} {old:<15s} {new:<15s} {cnt:>6d}")
    else:
        print("  No status transitions recorded on push turns.")
    print()

    # ---------------------------------------------------------------
    # F. Per-sample aggregate: push count vs final reward
    # ---------------------------------------------------------------
    print("=" * 80)
    print("F. Per-sample: push-rate vs final alignment scores")
    print("=" * 80)
    by_sample = defaultdict(list)
    for e in push_events:
        by_sample[e["sample"]].append(e)
    # Compute per-sample: push count, commit rate, status change rate, reward, stance, critique
    rows_out = []
    for r in rows:
        pid = r["paper_id"]
        evs = by_sample.get(pid, [])
        n_push = len(evs)
        n_commit = sum(1 for e in evs if e["recovery_committed"])
        n_status = sum(1 for e in evs if e["status_changed"])
        commit_rate = n_commit / n_push if n_push else 0
        rows_out.append(dict(
            pid=pid,
            push=n_push,
            commit=n_commit,
            commit_rate=commit_rate,
            status_chg=n_status,
            reward=r["reward"],
            stance=r["reward_breakdown"].get("stance_align", 0),
            critique=r["reward_breakdown"].get("critique", 0),
            dec_c=r.get("decision_correct", 0),
        ))
    # Correlate: commit_rate vs reward
    by_commit_bucket = defaultdict(list)
    for row in rows_out:
        bucket = (
            "0% (no commits)" if row["commit_rate"] == 0
            else "<=50%" if row["commit_rate"] <= 0.5
            else ">50%"
        )
        by_commit_bucket[bucket].append(row)
    print(f"{'commit_rate_bucket':<25s} {'n':>4s} {'reward_mean':>12s} {'stance_mean':>12s} {'critique_mean':>14s} {'dec_c_mean':>11s}")
    for bucket in ["0% (no commits)", "<=50%", ">50%"]:
        rs = by_commit_bucket.get(bucket, [])
        if not rs:
            continue
        print(f"{bucket:<25s} {len(rs):>4d} "
              f"{mean(r['reward'] for r in rs):>12.4f} "
              f"{mean(r['stance'] for r in rs):>12.4f} "
              f"{mean(r['critique'] for r in rs):>14.4f} "
              f"{mean(r['dec_c'] for r in rs):>11.4f}")
    print()

    # Per-sample raw table
    print("Per-sample detail (sorted by commit_rate desc):")
    print(f"{'paper_id':<14s} {'push':>5s} {'commit':>7s} {'c_rate':>7s} {'status':>7s} {'reward':>8s} {'stance':>7s} {'critique':>9s} {'dec_c':>6s}")
    for row in sorted(rows_out, key=lambda r: -r["commit_rate"]):
        print(f"{row['pid']:<14s} {row['push']:>5d} {row['commit']:>7d} "
              f"{100*row['commit_rate']:>6.1f}% {row['status_chg']:>7d} "
              f"{row['reward']:>8.4f} {row['stance']:>7.4f} {row['critique']:>9.4f} {row['dec_c']:>6.1f}")
    print()

    # ---------------------------------------------------------------
    # G. Per-sample: does push actually correlate with improvement?
    # ---------------------------------------------------------------
    print("=" * 80)
    print("G. Samples with zero recovery commits vs samples with commits")
    print("=" * 80)
    zero = [r for r in rows_out if r["commit"] == 0]
    some = [r for r in rows_out if r["commit"] > 0]
    print(f"Zero commits: n={len(zero)}  reward_mean={mean(r['reward'] for r in zero):.4f}  "
          f"stance={mean(r['stance'] for r in zero):.4f}  critique={mean(r['critique'] for r in zero):.4f}")
    if some:
        print(f"Some commits: n={len(some)}  reward_mean={mean(r['reward'] for r in some):.4f}  "
              f"stance={mean(r['stance'] for r in some):.4f}  critique={mean(r['critique'] for r in some):.4f}")


if __name__ == "__main__":
    main()
