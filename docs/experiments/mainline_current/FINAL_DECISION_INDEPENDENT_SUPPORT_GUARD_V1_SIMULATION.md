# Final Decision Independent Support Guard v1 Simulation

## 结论

- original_counts: `{'reject': 37, 'accept': 2}`
- guarded_counts: `{'reject': 39}`
- flipped_rows: `2`

## Flips

| paper_id | gold_inferred | original | guarded | real_strong | claims_with_support | nonabstract | unresolved | conflicts |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| ZHr0JajZfH | reject | accept | reject | 3 | 2 | 3 | 2 | 0 |
| kam84eEmub | reject | accept | reject | 3 | 1 | 3 | 3 | 0 |

## 判断

该 guard 挡住了 empirical structuring v1 fulltest39 中由重复/浅层 strong support 触发的 runtime accept。它不恢复 accept recall，只用于保持 binary final decision 的安全性；正式论文推荐仍应使用 derived recommendation view。
