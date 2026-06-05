# Final-View Hygiene Fix v1 Result

## 结论

本轮修复没有改变 live trajectory，也没有放松 binary accept/reject 阈值；它把 targetless unresolved 与 fallback/meta flaw 从 final-view 的强负面证据中剥离，减少 final report 和 criterion section 的系统性污染。runtime binary decision 仍然是保守 health check，不作为论文主指标。

## 汇总

| metric | value |
| --- | --- |
| raw_open_unresolved | 190 |
| view_open_unresolved | 1 |
| raw_active_flaws | 25 |
| view_active_flaws | 2 |
| raw_evidence_gaps | 147 |
| view_evidence_gaps | 112 |
| deferred_unresolved_count | 189 |
| targetless_unresolved_deferred_count | 120 |
| downgraded_flaw_count | 23 |
| stale_evidence_gap_count | 35 |
| stale_conflict_count | 31 |

## Decision Health

```json
{
  "original_runtime": {
    "accuracy": 0.7692,
    "macro_f1": 0.4348,
    "accept_recall": 0.0,
    "reject_recall": 1.0,
    "predicted_accept_count": 0,
    "false_accept_ids": [],
    "false_reject_ids": [
      "hj323oR3rw",
      "QAAsnSRwgu",
      "X41c4uB4k0",
      "gzqrANCF4g",
      "KI9NqjLVDT",
      "1HCN4pjTb4",
      "LebzzClHYw",
      "BXY6fe7q31",
      "jVEoydFOl9"
    ],
    "recovered_accept_ids": []
  },
  "hygiene_view_runtime_rule": {
    "accuracy": 0.7692,
    "macro_f1": 0.4348,
    "accept_recall": 0.0,
    "reject_recall": 1.0,
    "predicted_accept_count": 0,
    "false_accept_ids": [],
    "false_reject_ids": [
      "hj323oR3rw",
      "QAAsnSRwgu",
      "X41c4uB4k0",
      "gzqrANCF4g",
      "KI9NqjLVDT",
      "1HCN4pjTb4",
      "LebzzClHYw",
      "BXY6fe7q31",
      "jVEoydFOl9"
    ],
    "recovered_accept_ids": []
  }
}
```

## 逐样本

| paper_id | gold | orig_pred | hygiene_pred | raw_unres | view_unres | raw_gaps | view_gaps | raw_flaws | view_flaws | targetless_def | downgraded_flaws | real_strong | nonabs_strong |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ye3NrNrYOY | reject | reject | reject | 6 | 0 | 3 | 2 | 0 | 0 | 4 | 0 | 1 | 1 |
| WNxlJJIEVj | reject | reject | reject | 5 | 0 | 3 | 3 | 0 | 0 | 3 | 0 | 0 | 0 |
| uOrfve3prk | reject | reject | reject | 1 | 0 | 3 | 1 | 0 | 0 | 0 | 0 | 2 | 2 |
| hj323oR3rw | accept | reject | reject | 5 | 0 | 3 | 3 | 0 | 0 | 4 | 0 | 0 | 0 |
| 7Dub7UXTXN | reject | reject | reject | 6 | 0 | 6 | 6 | 3 | 0 | 6 | 3 | 0 | 0 |
| 9zEBK3E9bX | reject | reject | reject | 1 | 0 | 3 | 1 | 0 | 0 | 0 | 0 | 2 | 2 |
| XyB4VvF01X | reject | reject | reject | 7 | 0 | 4 | 4 | 0 | 0 | 6 | 0 | 0 | 0 |
| GE6iywJtsV | reject | reject | reject | 5 | 0 | 3 | 2 | 0 | 0 | 4 | 0 | 1 | 1 |
| QAAsnSRwgu | accept | reject | reject | 4 | 0 | 3 | 0 | 0 | 0 | 1 | 0 | 0 | 0 |
| WpXq5n8yLb | reject | reject | reject | 6 | 0 | 4 | 3 | 0 | 0 | 4 | 0 | 1 | 1 |
| X41c4uB4k0 | accept | reject | reject | 1 | 0 | 4 | 3 | 0 | 0 | 0 | 0 | 1 | 1 |
| NnExMNiTHw | reject | reject | reject | 7 | 0 | 6 | 5 | 3 | 0 | 7 | 3 | 1 | 1 |
| gzqrANCF4g | accept | reject | reject | 8 | 0 | 5 | 5 | 1 | 0 | 7 | 1 | 0 | 0 |
| a6SntIisgg | reject | reject | reject | 3 | 0 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| cklg91aPGk | reject | reject | reject | 3 | 0 | 3 | 2 | 0 | 0 | 2 | 0 | 1 | 1 |
| HPuLU6q7xq | reject | reject | reject | 3 | 0 | 3 | 3 | 0 | 0 | 1 | 0 | 0 | 0 |
| fGXyvmWpw6 | reject | reject | reject | 1 | 0 | 5 | 4 | 0 | 0 | 0 | 0 | 1 | 1 |
| QAgwFiIY4p | reject | reject | reject | 4 | 0 | 6 | 5 | 3 | 2 | 4 | 1 | 2 | 2 |
| KI9NqjLVDT | accept | reject | reject | 5 | 0 | 4 | 1 | 1 | 0 | 3 | 1 | 0 | 0 |
| 1HCN4pjTb4 | accept | reject | reject | 3 | 0 | 3 | 3 | 0 | 0 | 1 | 0 | 0 | 0 |
| LebzzClHYw | accept | reject | reject | 1 | 0 | 3 | 1 | 0 | 0 | 0 | 0 | 2 | 2 |
| BXY6fe7q31 | accept | reject | reject | 10 | 0 | 4 | 3 | 1 | 0 | 4 | 1 | 3 | 3 |
| TPAj63ax4Y | reject | reject | reject | 5 | 0 | 6 | 4 | 3 | 0 | 5 | 3 | 2 | 2 |
| mHv6wcBb0z | reject | reject | reject | 7 | 1 | 3 | 3 | 2 | 0 | 5 | 2 | 0 | 0 |
| xUe1YqEgd6 | reject | reject | reject | 1 | 0 | 4 | 4 | 0 | 0 | 0 | 0 | 0 | 0 |
| jVEoydFOl9 | accept | reject | reject | 3 | 0 | 5 | 4 | 1 | 0 | 3 | 1 | 1 | 1 |
| YXn76HMetm | reject | reject | reject | 7 | 0 | 5 | 5 | 2 | 0 | 7 | 2 | 0 | 0 |
| KOUAayk5Kx | reject | reject | reject | 1 | 0 | 3 | 2 | 0 | 0 | 0 | 0 | 1 | 1 |
| XH3OiIhtvf | reject | reject | reject | 5 | 0 | 3 | 3 | 0 | 0 | 4 | 0 | 0 | 0 |
| ZHr0JajZfH | reject | reject | reject | 7 | 0 | 3 | 1 | 0 | 0 | 4 | 0 | 4 | 4 |
| WLgbjzKJkk | reject | reject | reject | 10 | 0 | 4 | 4 | 1 | 0 | 8 | 1 | 0 | 0 |
| 9JRsAj3ymy | reject | reject | reject | 7 | 0 | 6 | 3 | 0 | 0 | 3 | 0 | 0 | 0 |
| rEqETC88RY | reject | reject | reject | 1 | 0 | 4 | 4 | 0 | 0 | 0 | 0 | 0 | 0 |
| aTBE70xiFw | reject | reject | reject | 3 | 0 | 6 | 5 | 3 | 0 | 3 | 3 | 1 | 1 |
| LieTse3fQB | reject | reject | reject | 8 | 0 | 2 | 1 | 0 | 0 | 4 | 0 | 1 | 1 |
| kam84eEmub | reject | reject | reject | 10 | 0 | 1 | 1 | 0 | 0 | 4 | 0 | 0 | 0 |
| N0isTh3rml | reject | reject | reject | 10 | 0 | 3 | 3 | 1 | 0 | 5 | 1 | 0 | 0 |
| 2L7KQ4qbHi | reject | reject | reject | 9 | 0 | 1 | 1 | 0 | 0 | 4 | 0 | 0 | 0 |
| aRxLDcxFcL | reject | reject | reject | 1 | 0 | 4 | 4 | 0 | 0 | 0 | 0 | 0 | 0 |
