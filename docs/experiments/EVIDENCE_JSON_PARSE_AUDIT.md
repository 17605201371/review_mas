# Evidence JSON Parse Audit

**运行行为是否改变**：否。

## 1. Agent 级 parse/fallback 统计

| agent_id | total_calls | valid_json_count | parse_error_count | fallback_payload_count | fallback_rate | raw_positive_mentions | raw_insufficient_mentions |
|---|---|---|---|---|---|---|---|
| Claim Agent | 71 | 53 | 18 | 18 | 0.254 | 0 | 29 |
| Critique Agent | 278 | 189 | 89 | 89 | 0.320 | 0 | 258 |
| Evidence Agent | 369 | 218 | 151 | 127 | 0.344 | 58 | 312 |

## 2. Gold x Agent 统计

| gold | agent_id | total_calls | parse_error_count | fallback_payload_count | parse_error_rate | fallback_rate |
|---|---|---|---|---|---|---|
| accept | Claim Agent | 26 | 8 | 8 | 0.308 | 0.308 |
| accept | Critique Agent | 101 | 33 | 33 | 0.327 | 0.327 |
| accept | Evidence Agent | 137 | 63 | 54 | 0.460 | 0.394 |
| reject | Claim Agent | 45 | 10 | 10 | 0.222 | 0.222 |
| reject | Critique Agent | 177 | 56 | 56 | 0.316 | 0.316 |
| reject | Evidence Agent | 232 | 88 | 73 | 0.379 | 0.315 |

## 3. RAW_POSITIVE_PARSE_FAILURE_CASES

| run | paper_id | gold | turn | agent | raw_positive_snippet | parse_error | fallback_payload_summary | final_support |
|---|---|---|---|---|---|---|---|---|
| 4b_focus | QAAsnSRwgu | accept | 2 | Evidence Agent | <think> </think> <json> { "evidence_map": [ { "evidence_id": "evidence-1", "claim_id": "claim-1", "evidence": "The abstract states: 'we introduce a comprehensive solution for selec | Invalid JSON payload: Expecting ',' delimiter: line 50 column 6 (char 2088) | {'fallback_payload_count': 1, 'fallback_unresolved_question_count': 1, 'fallback_evidence_count': 1, 'fallback_missing_evidence_count': 1, 'fallback_conflict_count': 0} | 2 |
| 9b_fulltest_mainline | WNxlJJIEVj | reject | 4 | Evidence Agent | <json> { "evidence_map": [ { "evidence_id": "evidence-1", "claim_id": "claim-1", "evidence": "The abstract states: 'The performance of offline reinforcement learning (RL) is sensit | Invalid JSON payload: Expecting ':' delimiter: line 14 column 36 (char 678) | {'fallback_payload_count': 1, 'fallback_unresolved_question_count': 1, 'fallback_evidence_count': 1, 'fallback_missing_evidence_count': 1, 'fallback_conflict_count': 0} | 1 |
| 9b_fulltest_mainline | uOrfve3prk | reject | 4 | Evidence Agent | </think> <json> { "evidence_map": [ { "evidence_id": "evidence-1", "claim_id": "claim-1", "evidence": "The paper proposes a unified framework that integrates interpretability and c | Invalid JSON payload: Expecting ',' delimiter: line 50 column 6 (char 2445) | {'fallback_payload_count': 1, 'fallback_unresolved_question_count': 1, 'fallback_evidence_count': 1, 'fallback_missing_evidence_count': 1, 'fallback_conflict_count': 0} | 2 |
| 9b_fulltest_mainline | QAAsnSRwgu | accept | 5 | Evidence Agent | { "action": "blocked", "blocked_reason": "insufficient evidence to transition", "missing_requirements": ["evidence for claim-1"] } # Task Introduction # Review Task Paper ID: QAAsn | Invalid JSON payload: Extra data: line 7 column 1 (char 138) | {'fallback_payload_count': 1, 'fallback_unresolved_question_count': 1, 'fallback_evidence_count': 1, 'fallback_contradiction_count': 1, 'fallback_conflict_count': 1} | 2 |
| 9b_fulltest_mainline | fGXyvmWpw6 | reject | 4 | Evidence Agent | </think> <json> { "evidence_map": [ { "evidence_id": "evidence-1", "claim_id": "claim-1", "evidence": "The paper states that Federated Learning (FL) is 'susceptible to performance  | Invalid JSON payload: Expecting ',' delimiter: line 50 column 6 (char 2353) | {'fallback_payload_count': 1, 'fallback_unresolved_question_count': 1, 'fallback_evidence_count': 1, 'fallback_missing_evidence_count': 1, 'fallback_conflict_count': 0} | 2 |
| 9b_fulltest_mainline | KI9NqjLVDT | accept | 2 | Evidence Agent | <json> { "evidence_map": [ { "evidence_id": "evidence-1", "claim_id": "claim-1", "evidence": "The paper introduces ReMasker as a new method for imputing missing values in tabular d | Invalid JSON payload: Extra data: line 37 column 1 (char 1809) | {'fallback_payload_count': 1, 'fallback_unresolved_question_count': 1, 'fallback_evidence_count': 1, 'fallback_missing_evidence_count': 1, 'fallback_conflict_count': 0} | 0 |
| 9b_fulltest_mainline | mHv6wcBb0z | reject | 7 | Evidence Agent | { "action": "blocked", "blocked_reason": "Insufficient evidence to transition claim-1; missing quantitative results.", "missing_requirements": ["Quantitative experimental data show | Invalid JSON payload: Extra data: line 7 column 1 (char 270) | {'fallback_payload_count': 1, 'fallback_unresolved_question_count': 1, 'fallback_evidence_count': 1, 'fallback_contradiction_count': 1, 'fallback_conflict_count': 1} | 1 |
| 9b_fulltest_mainline | jVEoydFOl9 | accept | 6 | Evidence Agent | { "action": "blocked", "target_type": "claim|flaw|hypothesis", "target_id": "claim-1", system_salvaged": true, "blocked_reason": "Insufficient evidence to transition status.", "mis | Invalid JSON payload: Expecting property name enclosed in double quotes: line 5 column 3 (char 95) | {'fallback_payload_count': 1, 'fallback_unresolved_question_count': 1, 'fallback_evidence_count': 1, 'fallback_contradiction_count': 1, 'fallback_conflict_count': 1} | 1 |
| 9b_fulltest_mainline | KOUAayk5Kx | reject | 4 | Evidence Agent | </think> <json> { "evidence_map": [ { "evidence_id": "evidence-1", "claim_id": "claim-1", "evidence": "The abstract explicitly states: 'However, there is an issue of multi-model fo | Invalid JSON payload: Expecting ',' delimiter: line 43 column 6 (char 2130) | {'fallback_payload_count': 1, 'fallback_unresolved_question_count': 1, 'fallback_evidence_count': 1, 'fallback_contradiction_count': 1, 'fallback_conflict_count': 1} | 1 |
| 9b_fulltest_mainline | 9JRsAj3ymy | reject | 4 | Evidence Agent | <json> { "evidence_map": [ { "evidence_id": "evidence-1", "claim_id": "claim-1", "evidence": "The paper proposes a Time-Sensitive Replay method for continual learning.", "source":  | Invalid JSON payload: Expecting property name enclosed in double quotes: line 21 column 30 (char 633) | {'fallback_payload_count': 1, 'fallback_unresolved_question_count': 1, 'fallback_evidence_count': 1, 'fallback_missing_evidence_count': 1, 'fallback_conflict_count': 0} | 0 |
| 9b_fulltest_mainline | aTBE70xiFw | reject | 4 | Evidence Agent | <json> { "evidence_map": [ { "evidence_id": "evidence-1", "claim_id": "claim-1", "evidence": "Deep neural networks (DNNs) have proven powerful for denoising individual images, but  | Invalid JSON payload: Expecting ',' delimiter: line 13 column 54 (char 436) | {'fallback_payload_count': 1, 'fallback_unresolved_question_count': 1, 'fallback_evidence_count': 1, 'fallback_contradiction_count': 1, 'fallback_conflict_count': 1} | 2 |
| 9b_fulltest_mainline | aRxLDcxFcL | reject | 4 | Evidence Agent | </think> <json> { "evidence_map": [ { "evidence_id": "evidence-1", "claim_id": "claim-1", "evidence": "We present Virtual Community, a social world simulation platform designed to  | Invalid JSON payload: Expecting ',' delimiter: line 50 column 6 (char 2530) | {'fallback_payload_count': 1, 'fallback_unresolved_question_count': 1, 'fallback_evidence_count': 1, 'fallback_missing_evidence_count': 1, 'fallback_conflict_count': 0} | 3 |

## 4. 判断

- **parse failure 作用**：它不是唯一断点，但会把 worker raw 输出转成 fallback payload，并把 missing evidence / unresolved question 写入 ReviewState。
- **审计重点**：如果 raw 中有正向 evidence 但 parse failed，则下一步可考虑 Evidence JSON Robustness；否则优先检查输入上下文。
