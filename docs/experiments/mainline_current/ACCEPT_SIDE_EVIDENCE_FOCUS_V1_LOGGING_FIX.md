# Accept-Side Evidence Focus v1 Logging Fix

## 背景

Focus v1 首轮运行已产生结果，但 `evidence_focus_*` 字段没有进入 jsonl turn log，原因是 `build_turn_log(...)` 没有显式序列化这些 manager payload 字段。

## 修复

本轮只补日志，不改变推理行为：

- `evidence_focus_mode`
- `evidence_focus_applied`
- `evidence_focus_reason`
- `evidence_focus_original_claim_ids`
- `evidence_focus_selected_claim_ids`
- `evidence_focus_original_claim_count`
- `evidence_focus_selected_claim_count`

静态验证已确认 `build_turn_log(...)` 可以写出这些字段。现有 Focus v1 fulltest39 结果不包含这些字段；后续重新运行 Soft Focus 或 Focus v1 时会完整落盘。
