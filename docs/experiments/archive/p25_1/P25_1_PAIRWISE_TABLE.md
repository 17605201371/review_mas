# P25.1 Pairwise Table

| paper_id | bucket | group | 4B emitted | 9B emitted | 4B validated | 9B validated | 4B committed | 9B committed | 4B failure top | 9B failure top | 4B state change | 9B state change | 4B reward | 9B reward | notes |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | --- | --- | ---: | ---: | --- |
| 2Cg4YrsCMA | reference_recovery | B | 3 | 2 | 4 | 5 | 1 | 1 | BLOCKED_BY_POLICY | BLOCKED_BY_POLICY | claim: uncertain -> unsupported x1 | claim: supported -> unsupported x1 | 0.4094 | 0.5133 | policy block may be bottleneck; reward up without better patch quality |
| 9EBSEkFSje | reference_recovery | C | 0 | 0 | 0 | 0 | 0 | 0 | none | none | none | none | 0.6713 | 0.7203 | reward up without better patch quality |
| GSckuQMzBG | reference_recovery | reverse_regression | 4 | 0 | 4 | 0 | 1 | 0 | NO_EFFECT_PATCH | none | claim: supported -> unsupported x1 | none | 0.4121 | 0.4329 | 9B reduces no-effect; reward up without better patch quality |
| IqaQZ1Jdky | reference_recovery | A | 3 | 3 | 5 | 6 | 0 | 1 | BLOCKED_BY_POLICY | BLOCKED_BY_POLICY | none | claim: uncertain -> unsupported x1 | 0.6116 | 0.5679 | 9B unlocks commit |
| NhLBhx5BVY | reference_recovery | C | 5 | 4 | 6 | 5 | 0 | 0 | NO_EFFECT_PATCH | BLOCKED_BY_POLICY | none | none | 0.4217 | 0.4897 | 9B reduces no-effect; policy block may be bottleneck; reward up without better patch quality |
| X41c4uB4k0 | historical_sentinel | C | 2 | 0 | 1 | 0 | 0 | 0 | SEMANTIC_MISMATCH | none | none | none | 0.1251 | 0.1711 | reward up without better patch quality |
| Ze49bGd4ON | reference_recovery | A | 0 | 2 | 0 | 5 | 0 | 1 | none | BLOCKED_BY_POLICY | none | claim: supported -> unsupported x1 | 0.5441 | 0.5951 | 9B unlocks commit |
| hj323oR3rw | historical_sentinel | C | 0 | 5 | 0 | 5 | 0 | 0 | none | BLOCKED_BY_POLICY | none | none | 0.1322 | 0.1682 | policy block may be bottleneck; reward up without better patch quality |
| kdriw2a8sl | reference_recovery | C | 2 | 1 | 4 | 1 | 0 | 0 | BLOCKED_BY_POLICY | BLOCKED_BY_POLICY | none | none | 0.5759 | 0.5339 | policy block may be bottleneck |
| qgyF6JVmar | reference_recovery | A | 3 | 1 | 5 | 2 | 0 | 1 | NO_EFFECT_PATCH | BLOCKED_BY_POLICY | none | claim: uncertain -> unsupported x1 | 0.6135 | 0.5305 | 9B unlocks commit; 9B reduces no-effect |
