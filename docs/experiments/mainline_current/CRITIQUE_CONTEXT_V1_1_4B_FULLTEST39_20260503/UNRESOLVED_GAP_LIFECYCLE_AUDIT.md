# Unresolved / Gap Lifecycle Audit

## 结论

负面状态仍是 final decision collapse 的主要压力源。大量 unresolved 没有 target claim，很多 gap 是 `claim lacks grounded evidence` 这类可被后续 support 反证或需要 final-view 重新判定的中间状态。下一步仍不建议 live 清理，应先在 final-view policy 中区分 paper-grounded 与 stale/system burden。

## 汇总

| metric | value |
| --- | --- |
| stale_gap_count | 34 |
| paper_gap_count | 80 |
| meta_gap_count | 5 |
| stale_unresolved_count | 0 |
| meta_unresolved_count | 43 |
| targetless_unresolved_count | 172 |
| paper_unresolved_count | 0 |

## 逐样本

| paper_id | gold | pred | gaps | stale_gaps | paper_gaps | unresolved | targetless_unresolved | paper_unresolved |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ye3NrNrYOY | reject | reject | 3 | 3 | 0 | 6 | 2 | 0 |
| WNxlJJIEVj | reject | reject | 2 | 0 | 2 | 10 | 7 | 0 |
| uOrfve3prk | reject | reject | 4 | 1 | 3 | 6 | 5 | 0 |
| hj323oR3rw | accept | reject | 3 | 0 | 3 | 6 | 5 | 0 |
| 7Dub7UXTXN | reject | reject | 3 | 1 | 2 | 6 | 6 | 0 |
| 9zEBK3E9bX | reject | reject | 3 | 2 | 1 | 1 | 1 | 0 |
| XyB4VvF01X | reject | reject | 3 | 0 | 3 | 2 | 2 | 0 |
| GE6iywJtsV | reject | reject | 5 | 1 | 4 | 5 | 4 | 0 |
| QAAsnSRwgu | accept | reject | 4 | 2 | 2 | 1 | 1 | 0 |
| WpXq5n8yLb | reject | reject | 3 | 2 | 1 | 3 | 1 | 0 |
| X41c4uB4k0 | accept | reject | 2 | 0 | 2 | 10 | 7 | 0 |
| NnExMNiTHw | reject | reject | 5 | 1 | 4 | 4 | 4 | 0 |
| gzqrANCF4g | accept | reject | 4 | 1 | 3 | 3 | 3 | 0 |
| a6SntIisgg | reject | reject | 3 | 1 | 2 | 2 | 2 | 0 |
| cklg91aPGk | reject | reject | 3 | 2 | 1 | 3 | 3 | 0 |
| HPuLU6q7xq | reject | reject | 2 | 1 | 1 | 10 | 8 | 0 |
| fGXyvmWpw6 | reject | reject | 3 | 0 | 3 | 10 | 7 | 0 |
| QAgwFiIY4p | reject | reject | 3 | 2 | 1 | 1 | 1 | 0 |
| KI9NqjLVDT | accept | reject | 3 | 0 | 0 | 4 | 3 | 0 |
| 1HCN4pjTb4 | accept | reject | 3 | 1 | 2 | 5 | 5 | 0 |
| LebzzClHYw | accept | reject | 4 | 1 | 3 | 8 | 5 | 0 |
| BXY6fe7q31 | accept | reject | 3 | 1 | 2 | 3 | 2 | 0 |
| TPAj63ax4Y | reject | reject | 3 | 1 | 2 | 1 | 1 | 0 |
| mHv6wcBb0z | reject | reject | 3 | 0 | 3 | 10 | 10 | 0 |
| xUe1YqEgd6 | reject | reject | 3 | 0 | 3 | 7 | 7 | 0 |
| jVEoydFOl9 | accept | reject | 2 | 1 | 1 | 5 | 3 | 0 |
| YXn76HMetm | reject | reject | 4 | 2 | 2 | 7 | 7 | 0 |
| KOUAayk5Kx | reject | reject | 2 | 1 | 1 | 10 | 5 | 0 |
| XH3OiIhtvf | reject | reject | 3 | 0 | 3 | 5 | 4 | 0 |
| ZHr0JajZfH | reject | reject | 3 | 1 | 2 | 3 | 3 | 0 |
| WLgbjzKJkk | reject | reject | 4 | 1 | 3 | 4 | 4 | 0 |
| 9JRsAj3ymy | reject | reject | 3 | 0 | 3 | 8 | 7 | 0 |
| rEqETC88RY | reject | reject | 3 | 0 | 3 | 10 | 10 | 0 |
| aTBE70xiFw | reject | reject | 3 | 2 | 1 | 5 | 4 | 0 |
| LieTse3fQB | reject | reject | 2 | 1 | 1 | 6 | 5 | 0 |
| kam84eEmub | reject | reject | 1 | 0 | 1 | 10 | 7 | 0 |
| N0isTh3rml | reject | reject | 4 | 0 | 2 | 4 | 2 | 0 |
| 2L7KQ4qbHi | reject | reject | 1 | 0 | 1 | 7 | 5 | 0 |
| aRxLDcxFcL | reject | reject | 4 | 1 | 3 | 4 | 4 | 0 |
