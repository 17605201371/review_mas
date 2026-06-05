# Accept-Side Support Formation Plan v1

## 当前判断

干净主线恢复了解释性，但暴露出 accept-side positive support formation 不足：gold accept 样本不是没有 evidence turns，而是 Evidence Agent 多数只输出 abstract-level medium support，没有稳定形成 non-abstract / empirical strong support。

## 下一刀

先做 `Evidence Context Selection v2`，理由：

- v1 的 section visibility 口径偏乐观，可能把 abstract 中的 `results/table/figure` 词误认为真实结果段；
- accept 样本的 medium support 主要来自 abstract，不能直接升级为 strong；
- 先让 Evidence Agent 看到更真实的 Method/Results/Table section，再判断是否需要 target focusing 或 strength calibration。

## 判定

保留条件：

- `evidence_context_mode=section_aware_v2` 正常落盘；
- accept 样本 non-abstract / empirical support 不低于 clean baseline，最好上升；
- fallback strong support 仍为 0；
- evidence fallback used 不明显增加；
- old controller active turns 仍为 0。

回退条件：

- JSON fallback 明显增加；
- false accept 明显增加且没有 accept-side support 收益；
- non-abstract support 没有提升，或 context 选择退化为重复/无关片段。
