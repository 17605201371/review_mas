# Final-View Invalid Binding Filter v1 Schema

## 定位

本轮是离线 final-view simulation，不改 runtime、不改 ReviewState、不重跑模型。

## 目的

`Evidence ID Turn-Scoping v1` 修复了 evidence_id 覆盖，但暴露出 invalid claim binding。`Evidence Claim Binding Guard v1` 证明 live 清空 invalid claim_id 会伤害 accept 侧 support formation。因此，本轮把 invalid binding 放到 final-view 层处理。

## 过滤规则

- `valid_real`: evidence.claim_id 存在于当前 ReviewState claims，且不是 fallback/general claim。
- `invalid_bound`: evidence.claim_id 不为空，但不存在于当前真实 claims。
- `fallback_bound`: evidence.claim_id 指向 claim-fallback / claim-general。
- `unbound`: evidence.claim_id 为空。

只有 `valid_real` 且 stance 支持、strength strong 的 evidence 进入 accept-like support 计数。

## 边界

该层只用于报告、case table 和 decision simulation。它不修改 live state，也不影响 manager / recovery / evidence formation。
