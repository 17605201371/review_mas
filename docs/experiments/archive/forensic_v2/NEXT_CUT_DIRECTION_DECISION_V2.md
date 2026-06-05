# Next Cut Direction Decision V2

## Decision Status

Do not implement another runtime control from this Layer 2 result alone. The observability patch is useful and should be retained, but the next runtime cut should wait for either a Layer 3 forensic run or a more selective rule.

## What The New Observability Shows

- `sanitize_bloat_turns = 0` in the Layer 2 run.
- Broad targets appear at the raw/inferred stage, not after sanitize.
- Fallback appears early in 2 of 5 cases, but one of those (`IqaQZ1Jdky`) reaches commit.
- Recovery push source is `sticky_recovery_bias` in all observed recovery-push turns.
- Commits occurred under `narrow_real_target`, not broad/fallback target quality.

## Priority Ranking Among The Three Candidate Cuts

1. Fallback Restraint, but only as selective fallback-role separation, not global suppression.
2. Progression Gate, only if Layer 3 shows aggressive recovery is pushed from raw broad/weak targets.
3. Sanitize Narrowing, currently lowest priority because no sanitize bloat was observed in Layer 2.

## Why Not Sanitize Narrowing Now

No `sanitize_bloat_detected` turn appeared in the Layer 2 run. The bad target shape is visible before sanitize.

## Why Not Progression Gate Now

The recovery pushes observed here were not broad/fallback pushes. A broad progression gate already showed a tendency to collapse throughput in earlier runs, and this Layer 2 evidence does not justify reintroducing it.

## Why Fallback Needs Care

Fallback is the most plausible upstream issue, but it is mixed: fallback can be part of a successful salvage/commit path. The previous global suppression attempt failed for exactly this reason. The next fallback cut must distinguish harmful fallback pollution from useful fallback salvage.

## Final Required Format

- target 最早变坏的步骤是：fallback-first in 2/5 and raw-broad-first in 1/5; sanitize-bloat not observed.
- 它发生在：`infer_action_from_state(...)` for raw broad targets; worker fallback evidence/turn-log path for fallback presence.
- fallback / sanitize / override 三者中，一号瓶颈是：fallback, but only as a selective role-separation problem, not a global suppression target.
- 当前 throttle/gate 为什么没看见坏点：the observed pushes are mostly `sticky_recovery_bias` on narrow targets, while broad/fallback issues often appear before or outside aggressive recovery push.
- 下一轮唯一建议实现的是：do not implement immediately; if forced after Layer 3, implement selective Fallback Restraint v2 that labels fallback evidence as salvage-only until grounded to a real claim.
- 另外两条为什么现在不做：sanitize narrowing has no Layer 2 hit; progression gate would likely suppress activity without targeting the observed failure mechanism.
