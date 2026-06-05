# Evidence ID Turn-Scoping v1 Decision

## 结论

建议保留 Evidence ID Turn-Scoping v1，并进入 fulltest39 验证。

## 理由

1. 本轮定位的是明确状态合并 bug：Evidence Agent 多轮复用 `evidence-1` / `evidence-2`，导致 `_merge_items_by_id` 覆盖旧证据。
2. 修复后 payload ID 重复样本数从 16 降到 0。
3. final evidence 总量从 32 增到 69，说明 evidence retention 明显改善。
4. final real strong support 从 9 增到 13，final 2+ real strong support 样本数从 0 增到 4。这正好修复了上轮发现的“payload 层有 support，但 final state 丢失 support”的瓶颈。
5. evidence gaps 和 candidate flaws 没有恶化，反而下降。

## 风险

- final evidence 数量明显增加，后续需要关注 evidence_map 上限、prompt 后续引用长度和 final report 选择策略。
- avg_reward 小幅下降，说明这不是直接 reward optimization；需要 fulltest39 验证是否稳定。

## 下一步

1. 在 fulltest39 4B 上跑 Evidence ID Turn-Scoping v1。
2. 重点看 gold accept 样本的 final real strong support 是否恢复。
3. 如果 fulltest39 同样正向，再把它纳入 Mainline-Final-v1 runtime。
4. 暂时不要调 final decision 阈值，也不要回到 sticky/throttle/gate。
