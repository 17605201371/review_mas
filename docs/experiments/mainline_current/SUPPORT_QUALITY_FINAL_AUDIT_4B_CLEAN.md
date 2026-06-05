# Support Quality Final Audit 4B Clean

## 结论

clean run 的 strong support 绑定仍然干净，但早先 `ablation=19 / table=0` 的口径不能直接当真：`empirical_or_ablation_support` 是通用标签，必须用更严格的 corrected bucket 区分 abstract/method/result/table/ablation。

## 汇总

| metric | value |
| --- | --- |
| real_strong_total | 28 |
| strong_abstract | 1 |
| strong_method | 6 |
| strong_empirical_result | 11 |
| strong_table_or_figure | 10 |
| strong_ablation | 0 |
| strong_unknown | 0 |
| fallback_or_unbound_strong | 0 |
| independent_group_total | 25 |
| rows_with_2plus_independent_groups | 7 |
| rows_with_method_plus_empirical | 4 |

## 逐样本

| paper_id | gold | pred | real | abstract | method | result | table_fig | ablation | independent_groups | method_plus_empirical |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ye3NrNrYOY | reject | reject | 1 | 0 | 0 | 0 | 1 | 0 | 1 | False |
| WNxlJJIEVj | reject | reject | 0 | 0 | 0 | 0 | 0 | 0 | 0 | False |
| uOrfve3prk | reject | reject | 2 | 0 | 1 | 1 | 0 | 0 | 2 | True |
| hj323oR3rw | accept | reject | 0 | 0 | 0 | 0 | 0 | 0 | 0 | False |
| 7Dub7UXTXN | reject | reject | 0 | 0 | 0 | 0 | 0 | 0 | 0 | False |
| 9zEBK3E9bX | reject | reject | 2 | 0 | 0 | 0 | 2 | 0 | 2 | False |
| XyB4VvF01X | reject | reject | 0 | 0 | 0 | 0 | 0 | 0 | 0 | False |
| GE6iywJtsV | reject | reject | 1 | 0 | 0 | 1 | 0 | 0 | 1 | False |
| QAAsnSRwgu | accept | reject | 0 | 0 | 0 | 0 | 0 | 0 | 0 | False |
| WpXq5n8yLb | reject | reject | 1 | 0 | 0 | 1 | 0 | 0 | 1 | False |
| X41c4uB4k0 | accept | reject | 1 | 0 | 0 | 1 | 0 | 0 | 1 | False |
| NnExMNiTHw | reject | reject | 1 | 0 | 0 | 0 | 1 | 0 | 1 | False |
| gzqrANCF4g | accept | reject | 0 | 0 | 0 | 0 | 0 | 0 | 0 | False |
| a6SntIisgg | reject | reject | 0 | 0 | 0 | 0 | 0 | 0 | 0 | False |
| cklg91aPGk | reject | reject | 1 | 0 | 0 | 0 | 1 | 0 | 1 | False |
| HPuLU6q7xq | reject | reject | 0 | 0 | 0 | 0 | 0 | 0 | 0 | False |
| fGXyvmWpw6 | reject | reject | 1 | 0 | 0 | 0 | 1 | 0 | 1 | False |
| QAgwFiIY4p | reject | reject | 2 | 0 | 0 | 2 | 0 | 0 | 2 | False |
| KI9NqjLVDT | accept | reject | 0 | 0 | 0 | 0 | 0 | 0 | 0 | False |
| 1HCN4pjTb4 | accept | reject | 0 | 0 | 0 | 0 | 0 | 0 | 0 | False |
| LebzzClHYw | accept | reject | 2 | 0 | 1 | 1 | 0 | 0 | 2 | True |
| BXY6fe7q31 | accept | reject | 3 | 0 | 0 | 0 | 3 | 0 | 2 | False |
| TPAj63ax4Y | reject | reject | 2 | 0 | 1 | 1 | 0 | 0 | 2 | True |
| mHv6wcBb0z | reject | reject | 0 | 0 | 0 | 0 | 0 | 0 | 0 | False |
| xUe1YqEgd6 | reject | reject | 0 | 0 | 0 | 0 | 0 | 0 | 0 | False |
| jVEoydFOl9 | accept | reject | 1 | 0 | 0 | 1 | 0 | 0 | 1 | False |
| YXn76HMetm | reject | reject | 0 | 0 | 0 | 0 | 0 | 0 | 0 | False |
| KOUAayk5Kx | reject | reject | 1 | 0 | 0 | 0 | 1 | 0 | 1 | False |
| XH3OiIhtvf | reject | reject | 0 | 0 | 0 | 0 | 0 | 0 | 0 | False |
| ZHr0JajZfH | reject | reject | 4 | 0 | 2 | 2 | 0 | 0 | 2 | True |
| WLgbjzKJkk | reject | reject | 0 | 0 | 0 | 0 | 0 | 0 | 0 | False |
| 9JRsAj3ymy | reject | reject | 0 | 0 | 0 | 0 | 0 | 0 | 0 | False |
| rEqETC88RY | reject | reject | 0 | 0 | 0 | 0 | 0 | 0 | 0 | False |
| aTBE70xiFw | reject | reject | 1 | 1 | 0 | 0 | 0 | 0 | 1 | False |
| LieTse3fQB | reject | reject | 1 | 0 | 1 | 0 | 0 | 0 | 1 | False |
| kam84eEmub | reject | reject | 0 | 0 | 0 | 0 | 0 | 0 | 0 | False |
| N0isTh3rml | reject | reject | 0 | 0 | 0 | 0 | 0 | 0 | 0 | False |
| 2L7KQ4qbHi | reject | reject | 0 | 0 | 0 | 0 | 0 | 0 | 0 | False |
| aRxLDcxFcL | reject | reject | 0 | 0 | 0 | 0 | 0 | 0 | 0 | False |
