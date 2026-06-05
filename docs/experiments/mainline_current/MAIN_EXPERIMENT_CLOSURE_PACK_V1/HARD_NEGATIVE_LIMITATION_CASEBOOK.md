# HARD_NEGATIVE_LIMITATION_CASEBOOK

## 核心限制

当前系统能形成正向 evidence support，但还不能稳定形成 paper-grounded hard-negative blocker。这是 final recommendation 不能进一步激进映射为 accept 的主要原因。

## 最新量化信号

- high-support gold reject / false-accept-risk：`20` 条。
- accept-protect：`4` 条。
- hard-negative status：`{'unverified_blocker_candidate': 37, 'grounded_blocker_found': 1, 'context_limited_no_grounded_blocker': 1}`。
- recovered accept：`['jVEoydFOl9']`。
- false accept：`[]`。

## 论文使用方式

这部分应写入 limitation / discussion：hard-negative grounding 是剩余研究瓶颈，不是当前 runtime controller 已解决的问题。下一阶段可研究 criterion-specific negative evidence extraction，但不应在本论文主线里硬接 runtime decision。
