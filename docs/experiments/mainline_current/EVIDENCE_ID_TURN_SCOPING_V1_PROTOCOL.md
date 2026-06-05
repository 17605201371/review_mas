# Evidence ID Turn-Scoping v1 Protocol

## 目标

本轮修复 Evidence Agent 多轮输出反复使用 `evidence-1` / `evidence-2` 导致 ReviewState merge 覆盖旧证据的问题。该问题会让 payload 层已经形成的 strong support 在 final ReviewState 中消失，直接伤害论文主线里的 evidence-grounded state construction。

## 改动范围

- 只改 Evidence Agent payload 进入 worker payload 之后、merge state 之前的 evidence_id 规范化。
- 不改 Evidence Agent prompt。
- 不改 final decision。
- 不改 recovery / sticky / throttle / progression gate。
- 不改 live state hygiene。

## 规则

1. Evidence Agent 每个 turn 输出的 evidence_id 追加 turn scope，例如 `evidence-1-turn-2`。
2. 如果同一 payload 内仍有重复 ID，则追加局部序号。
3. 同步更新同一 payload 内引用该 evidence_id 的字段，包括 conflict notes、flaw candidates、claim supporting evidence ids 和 recovery patch supporting evidence ids。
4. 写入观测字段 `evidence_id_scope_turn` 和 `evidence_id_scope_map`，用于后续审计。

## 论文意义

这不是增加证据生成能力，而是修复 evidence retention：确保多轮 evidence formation 的结果不会因为局部 ID 重复在状态合并时被覆盖。
