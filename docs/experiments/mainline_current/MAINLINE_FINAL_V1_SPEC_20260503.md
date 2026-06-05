# Mainline-Final-v1 Spec 2026-05-03 Freeze

## 定位

这是当前论文主试验前的冻结规格。它覆盖最新 9B context v2.2 fulltest39 结果以及 final-view report renderer v2。目标是把主线和探索分支切开，避免继续用 sticky/throttle/gate/controller 类改动污染结论。

## Runtime 主线

正式 runtime 主线只包含以下内容：

1. `p25.1 + explicit recovery phase` 保留版。
2. Evidence Binding Robustness：strong support 必须绑定真实 claim；fallback/unbound strong support 不计入 real support。
3. Evidence JSON Robustness：Evidence Agent 输出 JSON contract，fallback payload 污染保持低位。
4. Evidence Context / context v2.2：Evidence Agent 使用更有正文证据价值的 context，支持 method/result/empirical support formation。
5. Config alignment / preflight：固定 model、subset、max_turns、max_model_len、max_tokens、seed、batch；保留 run config 和 preflight。

## Offline / Final-View 主线

以下模块只用于 derived view、report rendering 和论文审计，不改 live state，不改变 manager/recovery 轨迹：

1. Support Quality / Evidence Independence audit。
2. Criterion Coverage / Grounding audit。
3. Final-view flaw lifecycle / meta-leakage classification。
4. Recommendation view v2：`borderline_positive / not_assessable / reject_like / borderline_insufficient`，不直接映射为 accept。
5. Final-view report renderer v2：把负面内容分成 Confirmed Weaknesses、Potential Concerns、Review Limitations、Unresolved Questions。

## 明确排除

以下方向不进入当前主线：

1. sticky / target sticky 系列。
2. throttle / progression gate 系列。
3. live state hygiene mutation。
4. support formation pass runtime controller。
5. critique context runtime v1 / v1.1：已证明会增加 unresolved/meta burden，且降低 commit throughput。
6. final decision 阈值硬调。
7. novelty / soundness / empirical adequacy 直接裸接入 accept/reject。

## Final Decision 口径

Runtime `accept/reject` 只作为 health check。当前最新 9B run 仍为 39/39 reject：`accept_recall=0.0`、`reject_recall=1.0`、`macro_f1=0.4348`。论文主指标不能只用这个二分类。

正式论文主分析应同时报告：

- evidence binding precision；
- JSON/fallback robustness；
- real / non-abstract / empirical support；
- support independence；
- criterion coverage / grounding；
- flaw lifecycle / meta-leakage；
- final-view recommendation distribution；
- report partition hygiene；
- recovery effectiveness 作为辅助指标。

## 最新 9B 冻结指标

| metric | value |
|---|---:|
| `row_count` | 39 |
| `real_strong_support_total` | 49 |
| `nonabstract_strong_support_total` | 49 |
| `empirical_strong_support_total` | 38 |
| `fallback_strong_support_total` | 0 |
| `strong_support_binding_precision` | 1.0 |
| `evidence_json_invalid_or_missing_count` | 0 |
| `legacy_controller_active_turns` | 0 |
| `predicted_accept_count` | 0 |
| `accept_recall` | 0.0 |
| `reject_recall` | 1.0 |
| `patch_committed_count` | 1 |

## 结论

当前版本可以作为 9B 主试验 dry-run 基线和论文结果包底座。正式主试验可以继续跑，但论文叙事必须避免声称 binary decision 已解决；真正可写的贡献是 evidence binding、positive support formation、criterion grounding、final-view flaw lifecycle 和 report hygiene。
