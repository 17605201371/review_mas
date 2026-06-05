# Final-View Invalid Binding Filter v1 Decision

## 结论

**保留为离线 final-view 过滤和论文分析层，不做 runtime mutation。**

本轮验证的是：invalid claim binding 是否可以在 final-view 中被安全剥离，而不是在 live state merge 阶段清空 claim_id。结果支持这个方向。

## 关键结果

- total strong support: `14`
- valid real strong support: `14`
- invalid-bound strong support: `0`
- fallback-bound strong support: `0`
- unbound strong support: `0`
- rows with invalid-bound evidence: `9`
- rows with valid 2+ support: `4`
- gold accept with valid 2+ support: `1`

## Decision simulation 安全下界

- strict accuracy: `0.7436`
- strict macro_f1: `0.5076`
- strict accept_recall: `0.1111`
- strict reject_recall: `0.9333`
- strict predicted_accept_count: `3`
- strict false_accept_ids: `['cklg91aPGk', 'fGXyvmWpw6']`
- strict recovered_accept_ids: `['gzqrANCF4g']`

## 判断

这层不应直接恢复 accept/reject；它的价值是让主试验指标区分：

1. 真正绑定到当前真实 claim 的 support；
2. 指向不存在 claim 的 invalid-bound support；
3. fallback/unbound support；
4. non-abstract / empirical / independent support。

`Evidence Claim Binding Guard v1` 失败说明不能在 live state 中清掉 invalid claim_id。当前正确做法是：保留 live evidence trajectory，在 final-view / support-quality / criterion-grounded simulation 中过滤不可靠 support。

## 下一步

把该 view 接入统一主试验分析表，而不是 runtime。下一轮应生成 `Mainline-Final-v1` 的最终论文结果包：runtime 指标、support-quality view、criterion-grounding view、case study 和 failure taxonomy。
