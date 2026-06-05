# SUPPORT_QUALITY_CODE_CLOSURE_V1

## 结论

本轮把 support quality 从分散脚本规则沉到可复用代码模块：`agent_system/environments/env_package/review/support_quality.py`。这不是新的 runtime controller，而是主试验指标口径收口。

## 已实现字段

- evidence-level：`evidence_section`、`support_role`、`support_depth`、`is_abstract_only`、`is_non_abstract`、`is_method_based`、`is_empirical_result`、`is_table_or_figure_based`、`is_ablation_based`、`independence_group_id`。
- claim-level：`claim_real_strong_support_count`、`claim_non_abstract_support_count`、`claim_empirical_support_count`、`claim_method_support_count`、`claim_independent_support_group_count`、`claim_support_depth_label`、`claim_has_only_abstract_support`、`claim_has_method_plus_result_support`。
- sample-level：`real_strong_support_total`、`nonabstract_support_total`、`empirical_support_total`、`method_support_total`、`table_or_figure_support_total`、`ablation_support_total`、`independent_support_group_total`、`claims_with_2plus_independent_support`。

## 关键修复

`figure` 不再天然等于 empirical result。`framework / overview / architecture / pipeline / diagram` 类型 figure 被归为 method support，除非同时有 result / metric / benchmark / ablation / table 信号。

## 测试

新增 `tests/test_support_quality.py`，覆盖：abstract shallow、method moderate、result/table/ablation deep、framework figure 不误判 empirical、重复 evidence source 不重复算 independent group。
