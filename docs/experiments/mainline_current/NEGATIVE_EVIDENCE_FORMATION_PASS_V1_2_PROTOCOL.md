# Negative Evidence Formation / Flaw Confirmation Pass v1 Protocol

## 定位

本轮是小样本诊断 pass，不改变 final decision，不写回 live ReviewState，不使用 reviewer comments。目标是验证系统能否从 paper text + 当前 ReviewState 中形成可信负向证据和 confirmed flaw。

## 输入

- 7 条 criterion Sim4 false accept。
- 3 条 criterion Sim4 recovered accept。
- 当前 final ReviewState。
- section-aware paper context。

## 输出

- `negative_evidence_items`
- `flaw_confirmation_items`
- `not_assessable_items`

## Trusted blocker 条件

- 绑定真实 claim_id。
- 非 fallback / system / excerpt limitation。
- 关联 empirical / soundness / novelty / significance。
- grounding strength 为 medium/strong。
- confidence >= 0.55。

## 约束

本 pass 只评估 formation 能力，不进入最终推荐聚合。
