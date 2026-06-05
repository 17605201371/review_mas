# Evidence ID Turn-Scoping v1 Compare

## 对比对象

- Baseline: `evidence_json_contract_v1_mixed16.jsonl`
- Candidate: `evidence_id_turn_scoping_v1_mixed16.jsonl`

## 总体指标

| 指标 | JSON Contract v1 | ID Turn-Scoping v1 | 变化 |
|---|---:|---:|---:|
| avg_reward | 0.460102 | 0.438927 | -0.021175 |
| payload evidence 总数 | 73 | 69 | -4 |
| payload unique evidence_id 总数 | 32 | 69 | 37 |
| payload ID 重复样本数 | 16 | 0 | -16 |
| final evidence 总数 | 32 | 69 | 37 |
| final unique evidence_id 总数 | 32 | 69 | 37 |
| final ID 重复样本数 | 0 | 0 | 0 |
| scope map turn 数 | 0 | 37 | 37 |
| payload real strong 总数 | 25 | 22 | -3 |
| payload 2+ real strong 样本数 | 9 | 8 | -1 |
| final real strong 总数 | 9 | 13 | 4 |
| final 2+ real strong 样本数 | 0 | 4 | 4 |
| unresolved 总数 | 87 | 89 | 2 |
| evidence gaps 总数 | 69 | 60 | -9 |
| candidate flaws 总数 | 25 | 20 | -5 |

## 关键观察

- payload ID 重复样本数从 16 降到 0。
- final evidence 总数从 32 增到 69。
- final real strong support 从 9 增到 13。
- final 2+ real strong support 样本数从 0 增到 4。
- evidence gaps 从 69 降到 60，candidate flaws 从 25 降到 20。
- avg_reward 小幅下降：0.460102 -> 0.438927。这不是本轮主指标，本轮主问题是 payload evidence 在 final state 中被覆盖。

## Candidate Case Table

| paper_id | payload evidence | payload unique | final evidence | final real strong | final 2+ real strong | unresolved | gaps | candidate flaws |
|---|---:|---:|---:|---:|---|---:|---:|---:|
| cWEfRkYj46 | 5 | 5 | 5 | 0 | false | 7 | 6 | 3 |
| xYzOkOGD96 | 4 | 4 | 4 | 0 | false | 5 | 4 | 1 |
| nrvoWOWcyg | 5 | 5 | 5 | 3 | true | 8 | 4 | 1 |
| bcHty5VvkQ | 6 | 6 | 6 | 0 | false | 9 | 3 | 1 |
| VEJzjAvaIy | 5 | 5 | 5 | 0 | false | 10 | 3 | 1 |
| k243qi7S50 | 5 | 5 | 5 | 0 | false | 10 | 4 | 2 |
| nrRkAAAufl | 4 | 4 | 4 | 2 | true | 3 | 4 | 1 |
| GSckuQMzBG | 4 | 4 | 4 | 1 | false | 3 | 3 | 1 |
| IdAyXxBud7 | 4 | 4 | 4 | 1 | false | 6 | 5 | 2 |
| JdWpIe70FL | 4 | 4 | 4 | 0 | false | 5 | 4 | 1 |
| pOq9vDIYev | 4 | 4 | 4 | 2 | true | 2 | 4 | 1 |
| YvWuac63bg | 4 | 4 | 4 | 0 | false | 3 | 3 | 1 |
| giU9fYGTND | 4 | 4 | 4 | 1 | false | 4 | 4 | 1 |
| qgyF6JVmar | 3 | 3 | 3 | 0 | false | 6 | 3 | 1 |
| cpGPPLLYYx | 4 | 4 | 4 | 1 | false | 4 | 3 | 1 |
| 77plFC53J5 | 4 | 4 | 4 | 2 | true | 4 | 3 | 1 |
