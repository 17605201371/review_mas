# Evidence JSON Contract v1 决策

## 结论

**保留 `Evidence JSON Contract v1`。**

理由是：它直接命中了当前 Evidence Agent 的主要结构化输出问题，显著降低 fallback 污染，同时没有牺牲 real-claim positive support。相比上一轮 `Evidence JSON Robustness v1.1`，这轮在 mixed16 上取得了更好的状态构建信号。

## 是否满足保留条件

| 条件 | 结果 | 判断 |
| --- | --- | --- |
| fallback payload 不继续上升 | `8 -> 0` | 通过 |
| fallback strong support 不上升 | `0 -> 0` | 通过 |
| real strong support 不下降 | `5 -> 9` | 通过 |
| non-abstract strong support 不下降 | `2 -> 4` | 通过 |
| empirical strong support 不下降 | `4 -> 8` | 通过 |
| unresolved 不上升 | `101 -> 87` | 通过 |
| 日志字段可诊断 | 77 个 Evidence turn 有状态字段 | 通过 |

## 保留边界

本轮只保留以下内容：

- Evidence Agent JSON-only prompt contract。
- Evidence JSON parse status / failure type / fallback-used 日志字段。
- `normalize_manager_payload()` 中对 evidence_json 字段的保留，保证 turn log 不丢字段。

本轮不引入：

- final decision 阈值修改。
- live state hygiene mutation。
- sticky / throttle / progression gate。
- criterion 直接参与 accept/reject。

## 仍然存在的问题

1. Parse error 仍有 17 次，说明 JSON contract 不是最终 JSON robustness 的终点。
2. `invalid_bound_evidence=4`，说明某些样本 Evidence Agent 仍会输出不存在的 `claim_id`，或当前 state 只有 fallback claim 时仍试图绑定 `claim-1`。
3. 16 条 mixed subset 仍然没有 predicted accept，说明 final decision collapse 不是单靠 Evidence JSON contract 能解决的问题。

## 下一步

下一步应做 **4B fulltest39 Evidence JSON Contract v1 集成验证**：

1. 用当前保留主线跑 fulltest39。
2. 输出同一组指标：parse/fallback、real/non-abstract/empirical support、unresolved/gap/candidate flaw、decision health。
3. 如果 fulltest39 上仍保持 fallback payload 下降且 support 不受损，再将它并入 Mainline-Final-v1 runtime 组件。

同时继续保留 offline/final-view 分析路线：

- final-view hygiene。
- support quality / evidence independence。
- criterion coverage / grounding。
- criterion-grounded decision simulation。
