# Positive Support Formation Audit

**运行行为是否改变**：否。
**审计范围**：4B focus、4B mixed v2、9B fulltest mainline 的现有 JSONL/trace。

## 1. 总览

| metric | value |
|---|---|
| samples | 71 |
| evidence_agent_calls | 369 |
| evidence_parse_errors | 151 |
| evidence_fallback_payloads | 127 |
| payload_strong_support_count | 75 |
| final_strong_positive_total | 54 |
| final_strong_positive_real_claim | 45 |
| final_strong_positive_fallback_claim | 9 |
| final_strong_positive_unsupported_claim | 33 |
| raw_positive_but_parse_failed_count | 12 |

## 2. POSITIVE_SUPPORT_FAILURE_CLASSIFICATION

| failure_class | samples |
|---|---|
| A_input_context_no_visible_support | 13 |
| C_payload_support_not_preserved | 6 |
| B_raw_positive_parse_failed | 4 |
| D_support_bound_to_fallback_claim | 1 |
| E_support_status_conflict | 1 |
| A_input_or_extraction_no_support | 1 |

该表只统计 gold=accept 样本；reject 样本不参与 positive support 断点分类。accept 样本数：26。

## 3. Accept 样本逐例

| run | paper_id | pred | failure_class | excerpt_chars | visible_results | visible_table | raw_positive | parse_errors | fallback_payloads | payload_strong | final_strong | real_claim_strong | blockers |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 4b_focus | hj323oR3rw | reject | D_support_bound_to_fallback_claim | 800 | False | False | 1 | 3 | 3 | 1 | 1 | 0 | critical>=1, unresolved>=6, strong<2 |
| 4b_focus | QAAsnSRwgu | reject | B_raw_positive_parse_failed | 800 | False | False | 2 | 3 | 3 | 2 | 2 | 2 | unresolved>=6, major>0_blocks_accept, unresolved>3_blocks_accept |
| 4b_focus | X41c4uB4k0 | reject | A_input_context_no_visible_support | 800 | False | False | 0 | 0 | 0 | 0 | 0 | 0 | critical>=1, unresolved>=6, strong<2 |
| 4b_focus | gzqrANCF4g | reject | C_payload_support_not_preserved | 800 | False | False | 2 | 0 | 0 | 2 | 1 | 1 | major>=2, unresolved>=6, strong<2 |
| 4b_focus | KI9NqjLVDT | reject | C_payload_support_not_preserved | 799 | False | False | 2 | 0 | 0 | 6 | 3 | 3 | unresolved>=6, major>0_blocks_accept, unresolved>3_blocks_accept |
| 4b_focus | 1HCN4pjTb4 | reject | A_input_context_no_visible_support | 799 | False | False | 0 | 3 | 3 | 0 | 0 | 0 | strong<2 |
| 4b_focus | LebzzClHYw | reject | A_input_context_no_visible_support | 800 | False | False | 0 | 2 | 2 | 0 | 0 | 0 | critical>=1, unresolved>=6, strong<2 |
| 4b_focus | BXY6fe7q31 | reject | E_support_status_conflict | 799 | False | False | 1 | 4 | 4 | 1 | 1 | 1 | unresolved>=6, strong<2 |
| 4b_focus | jVEoydFOl9 | reject | A_input_context_no_visible_support | 800 | False | False | 0 | 3 | 3 | 0 | 0 | 0 | critical>=1, unresolved>=6, strong<2 |
| 4b_mixed_v2 | cWEfRkYj46 | reject | A_input_context_no_visible_support | 800 | False | False | 0 | 3 | 3 | 0 | 0 | 0 | critical>=1, unresolved>=6, conflicts>=4, strong<2 |
| 4b_mixed_v2 | nrvoWOWcyg | reject | A_input_context_no_visible_support | 800 | False | False | 0 | 1 | 1 | 0 | 0 | 0 | unresolved>=6, conflicts>=4, strong<2 |
| 4b_mixed_v2 | VEJzjAvaIy | reject | A_input_context_no_visible_support | 800 | False | False | 0 | 4 | 4 | 0 | 0 | 0 | unresolved>=6, strong<2 |
| 4b_mixed_v2 | nrRkAAAufl | reject | A_input_or_extraction_no_support | 800 | True | False | 0 | 3 | 3 | 0 | 0 | 0 | strong<2 |
| 4b_mixed_v2 | IdAyXxBud7 | reject | C_payload_support_not_preserved | 799 | False | False | 2 | 1 | 1 | 2 | 1 | 0 | critical>=1, unresolved>=6, strong<2 |
| 4b_mixed_v2 | pOq9vDIYev | reject | A_input_context_no_visible_support | 800 | False | False | 0 | 3 | 3 | 0 | 0 | 0 | critical>=1, unresolved>=6, strong<2 |
| 4b_mixed_v2 | giU9fYGTND | reject | A_input_context_no_visible_support | 800 | False | False | 0 | 2 | 2 | 0 | 0 | 0 | critical>=1, unresolved>=6, strong<2 |
| 4b_mixed_v2 | cpGPPLLYYx | reject | A_input_context_no_visible_support | 799 | False | False | 0 | 2 | 2 | 0 | 0 | 0 | critical>=1, unresolved>=6, strong<2 |
| 9b_fulltest_mainline | hj323oR3rw | reject | C_payload_support_not_preserved | 800 | False | False | 1 | 3 | 3 | 3 | 2 | 2 | major>=2, major>0_blocks_accept, unresolved>3_blocks_accept |
| 9b_fulltest_mainline | QAAsnSRwgu | reject | B_raw_positive_parse_failed | 800 | False | False | 2 | 4 | 4 | 2 | 2 | 2 | critical>=1, unresolved>=6, unresolved>3_blocks_accept |
| 9b_fulltest_mainline | X41c4uB4k0 | reject | C_payload_support_not_preserved | 800 | False | False | 2 | 2 | 2 | 4 | 3 | 3 | unresolved>=6, major>0_blocks_accept, unresolved>3_blocks_accept |
| 9b_fulltest_mainline | gzqrANCF4g | reject | A_input_context_no_visible_support | 800 | False | False | 0 | 7 | 0 | 0 | 0 | 0 | strong<2 |
| 9b_fulltest_mainline | KI9NqjLVDT | reject | B_raw_positive_parse_failed | 799 | False | False | 1 | 3 | 1 | 0 | 0 | 0 | strong<2 |
| 9b_fulltest_mainline | 1HCN4pjTb4 | reject | A_input_context_no_visible_support | 799 | False | False | 0 | 4 | 4 | 0 | 0 | 0 | unresolved>=6, strong<2 |
| 9b_fulltest_mainline | LebzzClHYw | reject | A_input_context_no_visible_support | 800 | False | False | 0 | 0 | 0 | 0 | 0 | 0 | strong<2 |
| 9b_fulltest_mainline | BXY6fe7q31 | reject | C_payload_support_not_preserved | 799 | False | False | 2 | 0 | 0 | 2 | 1 | 1 | critical>=1, unresolved>=6, strong<2 |
| 9b_fulltest_mainline | jVEoydFOl9 | reject | B_raw_positive_parse_failed | 800 | False | False | 3 | 3 | 3 | 2 | 1 | 1 | critical>=1, unresolved>=6, strong<2 |

## 4. High stance but reject cases

| run | paper_id | stance_align | final_strong | real_claim_strong | decision_strong_count | blockers |
|---|---|---|---|---|---|---|
| 4b_focus | X41c4uB4k0 | 0.8222 | 0 | 0 | 0 | critical>=1, unresolved>=6, strong<2 |
| 4b_focus | gzqrANCF4g | 0.7227 | 1 | 1 | 1 | major>=2, unresolved>=6, strong<2 |
| 4b_focus | BXY6fe7q31 | 0.7333 | 1 | 1 | 1 | unresolved>=6, strong<2 |
| 4b_mixed_v2 | cWEfRkYj46 | 0.7167 | 0 | 0 | 0 | critical>=1, unresolved>=6, conflicts>=4, strong<2 |
| 4b_mixed_v2 | nrvoWOWcyg | 0.7143 | 0 | 0 | 0 | unresolved>=6, conflicts>=4, strong<2 |
| 4b_mixed_v2 | giU9fYGTND | 0.7717 | 0 | 0 | 0 | critical>=1, unresolved>=6, strong<2 |
| 9b_fulltest_mainline | BXY6fe7q31 | 0.9455 | 1 | 1 | 1 | critical>=1, unresolved>=6, strong<2 |

## 5. 解释

- **A 类** 表示 Evidence Agent 可见上下文里缺 method/result/table 且 raw 没有正向 support，优先指向输入/上下文选择问题。
- **B 类** 表示 raw 中有正向 support 但 JSON 解析失败，优先指向 JSON robustness。
- **C/D/E 类** 分别指向 merge、fallback grounding、claim-status 同步问题。
