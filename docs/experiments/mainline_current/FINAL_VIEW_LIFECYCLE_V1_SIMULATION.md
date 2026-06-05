# Final-View Lifecycle v1 离线模拟

输入：`outputs/results_main/review_infer/criterion_aware_final_report_v1_mixed16.jsonl`
运行方式：不重跑模型，不改 live ReviewState，只在 final-view 上模拟 unresolved/candidate lifecycle。

## 结果表

| rule | accuracy | macro-F1 | accept recall | reject recall | predicted accept | false accept | recovered accept |
|---|---:|---:|---:|---:|---:|---|---|
| `original` | 0.5000 | 0.3333 | 0.0000 | 1.0000 | 0 | `-` | `-` |
| `close_weak_unresolved` | 0.5000 | 0.3333 | 0.0000 | 1.0000 | 0 | `-` | `-` |
| `downgrade_ungrounded_candidates` | 0.5000 | 0.3333 | 0.0000 | 1.0000 | 0 | `-` | `-` |
| `combined` | 0.5000 | 0.3333 | 0.0000 | 1.0000 | 0 | `-` | `-` |

## 判断

- 单独关闭 weak/system unresolved 没有恢复 accept，说明 unresolved cleanup 不是当前单独有效的一刀。
- 单独降级 ungrounded/system candidate 也没有恢复 accept，说明 candidate cleanup 不能替代 positive support formation。
- 组合规则同样没有恢复 accept，说明当前 latest mixed16 的主要限制仍是 real strong support 不足，而不是 final-view lifecycle 阈值。

## 下一步

不要把 lifecycle cleanup 直接接入 runtime。下一步应回到 Evidence Binding / Support Quality 路线：提高 real-claim、non-abstract、independent support formation，同时保留 criterion-aware report section。
