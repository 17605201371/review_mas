# Negative Evidence Formation v2 Spec

## 目标

v2 不再扩大生成能力，而是收紧 blocker 语义：只有 paper-grounded、非 context-limited、非 abstract-only、绑定真实 claim、关联核心 criterion 的负向证据才能成为 trusted blocker。

## Trusted blocker 必要条件

1. criterion 属于 `empirical / soundness / novelty / significance`。
2. claim_id 是真实 claim，不是 fallback/general。
3. evidence/flaw anchor 包含 `result / experiment / table / figure / baseline / metric / ablation / dataset / benchmark`。
4. 不包含 `context not visible / abstract cuts off / cannot verify / missing from provided context` 等 context-limited 语言。
5. negative evidence 的 grounding strength 为 medium/strong；flaw 必须 confirmed 且 major/critical。
6. confidence >= 0.55。

## 不进入 trusted blocker 的情况

- abstract-only missing support。
- context-limited not-assessable。
- meta / fallback / parse / system limitation。
- anchor insufficient 的 weak candidate。

## 本轮定位

该 spec 仍是离线规则，不接入 final decision。
