# Flaw Lifecycle Final Audit

## 结论

flaw 层仍需要 final-view lifecycle：fallback/meta flaw 和 downgraded flaw 不应进入 confirmed weakness；grounded major/critical flaw 才能作为强 reject blocker。当前不应让 candidate flaw 直接等同 confirmed flaw。

## 汇总

| flaw_kind | count |
| --- | --- |
| fallback_or_meta | 42 |
| downgraded_or_resolved | 1 |
| grounded_major_or_critical | 3 |
| grounded_minor_or_candidate | 2 |
| ungrounded_candidate | 0 |

## 逐样本

| paper_id | gold | pred | total | fallback_meta | grounded_major | ungrounded_candidate | downgraded |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ye3NrNrYOY | reject | reject | 1 | 1 | 0 | 0 | 0 |
| WNxlJJIEVj | reject | reject | 2 | 2 | 0 | 0 | 0 |
| uOrfve3prk | reject | reject | 1 | 1 | 0 | 0 | 0 |
| hj323oR3rw | accept | reject | 2 | 2 | 0 | 0 | 0 |
| 7Dub7UXTXN | reject | reject | 2 | 2 | 0 | 0 | 0 |
| 9zEBK3E9bX | reject | reject | 1 | 1 | 0 | 0 | 0 |
| XyB4VvF01X | reject | reject | 1 | 1 | 0 | 0 | 0 |
| GE6iywJtsV | reject | reject | 2 | 2 | 0 | 0 | 0 |
| QAAsnSRwgu | accept | reject | 1 | 1 | 0 | 0 | 0 |
| WpXq5n8yLb | reject | reject | 1 | 1 | 0 | 0 | 0 |
| X41c4uB4k0 | accept | reject | 1 | 1 | 0 | 0 | 0 |
| NnExMNiTHw | reject | reject | 1 | 1 | 0 | 0 | 0 |
| gzqrANCF4g | accept | reject | 1 | 1 | 0 | 0 | 0 |
| a6SntIisgg | reject | reject | 1 | 1 | 0 | 0 | 0 |
| cklg91aPGk | reject | reject | 1 | 1 | 0 | 0 | 0 |
| HPuLU6q7xq | reject | reject | 1 | 1 | 0 | 0 | 0 |
| fGXyvmWpw6 | reject | reject | 2 | 2 | 0 | 0 | 0 |
| QAgwFiIY4p | reject | reject | 1 | 1 | 0 | 0 | 0 |
| KI9NqjLVDT | accept | reject | 2 | 0 | 1 | 0 | 0 |
| 1HCN4pjTb4 | accept | reject | 1 | 1 | 0 | 0 | 0 |
| LebzzClHYw | accept | reject | 0 | 0 | 0 | 0 | 0 |
| BXY6fe7q31 | accept | reject | 1 | 1 | 0 | 0 | 0 |
| TPAj63ax4Y | reject | reject | 1 | 1 | 0 | 0 | 0 |
| mHv6wcBb0z | reject | reject | 1 | 0 | 0 | 0 | 1 |
| xUe1YqEgd6 | reject | reject | 2 | 2 | 0 | 0 | 0 |
| jVEoydFOl9 | accept | reject | 2 | 2 | 0 | 0 | 0 |
| YXn76HMetm | reject | reject | 2 | 0 | 1 | 0 | 0 |
| KOUAayk5Kx | reject | reject | 1 | 1 | 0 | 0 | 0 |
| XH3OiIhtvf | reject | reject | 1 | 1 | 0 | 0 | 0 |
| ZHr0JajZfH | reject | reject | 1 | 1 | 0 | 0 | 0 |
| WLgbjzKJkk | reject | reject | 1 | 1 | 0 | 0 | 0 |
| 9JRsAj3ymy | reject | reject | 1 | 1 | 0 | 0 | 0 |
| rEqETC88RY | reject | reject | 1 | 1 | 0 | 0 | 0 |
| aTBE70xiFw | reject | reject | 1 | 1 | 0 | 0 | 0 |
| LieTse3fQB | reject | reject | 1 | 1 | 0 | 0 | 0 |
| kam84eEmub | reject | reject | 1 | 0 | 1 | 0 | 0 |
| N0isTh3rml | reject | reject | 2 | 2 | 0 | 0 | 0 |
| 2L7KQ4qbHi | reject | reject | 1 | 1 | 0 | 0 | 0 |
| aRxLDcxFcL | reject | reject | 1 | 1 | 0 | 0 | 0 |
