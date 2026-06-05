# NEGATIVE_FINDINGS_p25_2_to_p25_5a

## Purpose

This document records why `p25.2` to `p25.5a` are retained as exploratory diagnostics instead of being merged into the paper mainline.

## Core Lesson 1

Naive policy calibration introduces an unlock/regression trade-off.

Observed pattern:
- some previously blocked recovery patches become committed
- some previously stable successful cases regress
- aggregate commit counts do not show reliable net gain

Implication:
- reducing `BLOCKED_BY_POLICY` is not enough
- future calibration must be judged by net gain and preserved success, not only by commit throughput

## Core Lesson 2

Late target-level or trajectory guards do not reliably stop drift once the recovery path has already diverged.

Observed pattern:
- guards sometimes activate after the critical divergence turn
- the system can still continue along a bad trajectory even when protection logic exists on paper

Implication:
- a guard protocol is not the same thing as effective guard actuation
- future control work needs earlier and more local intervention points

## Core Lesson 3

Activation and guard diagnostics can improve observability without yielding stable end-to-end benefit.

Observed pattern:
- later rounds generated useful diagnostics
- failure modes became clearer
- but clarity alone did not convert into a stable paper-quality gain

Implication:
- these rounds are valuable as negative findings and limitation material
- they should not be used as the main evidence for the core claim

## How To Use These Results In The Paper

Recommended placement:
- discussion
- limitations
- future work
- possibly a compact ablation/negative-findings subsection

Not recommended:
- do not use these rounds as the core evidence for the main contribution
- do not redefine the main story around these unstable calibration experiments

## Practical Rule

For writing and figure preparation:
- main result sections: use `p25.0` and `p25.1` only
- diagnostic sections: cite `p25.2` to `p25.5a` as negative findings
