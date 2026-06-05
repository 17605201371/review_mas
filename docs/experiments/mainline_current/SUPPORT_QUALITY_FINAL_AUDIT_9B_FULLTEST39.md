# SUPPORT_QUALITY_FINAL_AUDIT_9B_FULLTEST39

## 结论
这份 9B fulltest39 的 support quality audit 说明：`real_strong_support` 不能直接当作足够强的审稿证据。当前 strong support 虽然主要能绑定到 real claim，但非 abstract、empirical/result、table/figure/ablation 和 independent support 仍明显不足。

因此，主试验必须把 support quality 纳入口径；否则 strong support 数量上升也不能证明系统真正提升了审稿质量。

## 1. Aggregate Support Quality

| metric | value |
| --- | ---: |
| real_strong_support_total | 15 |
| fallback_strong_support_total | 3 |
| abstract_strong_support_total | 7 |
| nonabstract_support_total | 8 |
| method_support_total | 6 |
| empirical_support_total | 2 |
| table_or_figure_support_total | 0 |
| independent_support_group_total | 14 |
| nonabstract_independent_group_total | 8 |
| empirical_independent_group_total | 2 |
| claims_with_2plus_independent_support | 1 |
| claims_with_only_abstract_support | 6 |
| claims_with_empirical_support | 2 |
| claims_with_method_plus_result_support | 1 |
| rows_with_2plus_real_strong | 4 |
| rows_with_2plus_independent_groups | 4 |
| rows_with_nonabstract_support | 6 |
| rows_with_empirical_support | 2 |
| rows_with_method_plus_result_support | 1 |
| rows_with_only_abstract_real_support | 3 |

## 2. Section / Role / Depth Distribution

### Evidence section distribution for real strong support

- `abstract`: 7
- `method`: 6
- `empirical_result`: 2

### Support role distribution

- `claim_articulation`: 7
- `method_description`: 6
- `empirical_result`: 2

### Support depth distribution

- `shallow`: 7
- `moderate`: 6
- `deep`: 2

解释：abstract / claim articulation 仍然占据明显比例；empirical/table/deep support 很少。这意味着 final decision 或论文主指标不能只使用 support count。

## 3. Accept / Reject Split

| group | rows | real_strong_avg | nonabstract_avg | empirical_avg | independent_group_avg | only_abstract_rows |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| true_accept_runtime | 0 | 0.000 | 0.000 | 0.000 | 0.000 | 0 |
| false_reject_gold_accept | 9 | 0.111 | 0.111 | 0.000 | 0.111 | 0 |
| gold_reject | 30 | 0.467 | 0.233 | 0.067 | 0.433 | 3 |

解释：runtime 没有 true accept；gold accept 的 false reject 中，仍有较多样本没有形成足够的 non-abstract / empirical / independent support。

## 4. Case Table

| paper_id | gold | pred | real_strong | abstract | nonabstract | method | empirical | table_fig | ind_groups | claims_2plus_groups | quality_label |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1HCN4pjTb4 | accept | reject | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | no_real_strong_support |
| BXY6fe7q31 | accept | reject | 1 | 0 | 1 | 1 | 0 | 0 | 1 | 0 | method_support_only |
| KI9NqjLVDT | accept | reject | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | no_real_strong_support |
| LebzzClHYw | accept | reject | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | no_real_strong_support |
| QAAsnSRwgu | accept | reject | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | no_real_strong_support |
| X41c4uB4k0 | accept | reject | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | no_real_strong_support |
| gzqrANCF4g | accept | reject | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | no_real_strong_support |
| hj323oR3rw | accept | reject | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | no_real_strong_support |
| jVEoydFOl9 | accept | reject | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | no_real_strong_support |
| 2L7KQ4qbHi | reject | reject | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | no_real_strong_support |
| 7Dub7UXTXN | reject | reject | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | no_real_strong_support |
| 9JRsAj3ymy | reject | reject | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | no_real_strong_support |
| 9zEBK3E9bX | reject | reject | 1 | 0 | 1 | 1 | 0 | 0 | 1 | 0 | method_support_only |
| GE6iywJtsV | reject | reject | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | no_real_strong_support |
| HPuLU6q7xq | reject | reject | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | no_real_strong_support |
| KOUAayk5Kx | reject | reject | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | no_real_strong_support |
| LieTse3fQB | reject | reject | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | no_real_strong_support |
| N0isTh3rml | reject | reject | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | no_real_strong_support |
| NnExMNiTHw | reject | reject | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | no_real_strong_support |
| QAgwFiIY4p | reject | reject | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | no_real_strong_support |
| TPAj63ax4Y | reject | reject | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | no_real_strong_support |
| WLgbjzKJkk | reject | reject | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | no_real_strong_support |
| WNxlJJIEVj | reject | reject | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | no_real_strong_support |
| WpXq5n8yLb | reject | reject | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | no_real_strong_support |
| XH3OiIhtvf | reject | reject | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | no_real_strong_support |
| XyB4VvF01X | reject | reject | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | no_real_strong_support |
| YXn76HMetm | reject | reject | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | no_real_strong_support |
| ZHr0JajZfH | reject | reject | 1 | 0 | 1 | 0 | 1 | 0 | 1 | 0 | empirical_support |
| a6SntIisgg | reject | reject | 1 | 1 | 0 | 0 | 0 | 0 | 1 | 0 | abstract_only_support |
| aRxLDcxFcL | reject | reject | 3 | 3 | 0 | 0 | 0 | 0 | 2 | 0 | abstract_only_support |
| aTBE70xiFw | reject | reject | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | no_real_strong_support |
| cklg91aPGk | reject | reject | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | no_real_strong_support |
| fGXyvmWpw6 | reject | reject | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | no_real_strong_support |
| kam84eEmub | reject | reject | 3 | 1 | 2 | 2 | 0 | 0 | 3 | 0 | method_support_only |
| mHv6wcBb0z | reject | reject | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | no_real_strong_support |
| rEqETC88RY | reject | reject | 2 | 0 | 2 | 1 | 1 | 0 | 2 | 1 | method_plus_result_support |
| uOrfve3prk | reject | reject | 2 | 1 | 1 | 1 | 0 | 0 | 2 | 0 | method_support_only |
| xUe1YqEgd6 | reject | reject | 1 | 1 | 0 | 0 | 0 | 0 | 1 | 0 | abstract_only_support |
| ye3NrNrYOY | reject | reject | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | no_real_strong_support |

## 5. 主试验口径建议

主试验中应同时报告：

- `real_strong_support_total`：只说明 support 是否绑定到真实 claim。
- `nonabstract_support_total`：说明 support 是否越过 abstract self-claim。
- `method_support_total` 与 `empirical_support_total`：说明 support 是否覆盖方法与结果证据。
- `table_or_figure_support_total` / `ablation_support_total`：说明是否有更深实验依据。
- `independent_support_group_total` 与 `claims_with_2plus_independent_support`：说明 support 是否独立，而不是重复引用同一类证据。

## 下一步

这份 audit 支持下一步做 `criterion-grounded decision view` 的离线对照，但不支持直接把 strong support 数量接入 accept/reject。更合理的做法是：用 support quality 作为 final-view decision/report 的约束特征，而不是 runtime controller。
