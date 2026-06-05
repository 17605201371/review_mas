# Unresolved + Candidate Flaw Lifecycle Audit

**Input**: `outputs/results_main/review_infer/criterion_aware_final_report_v1_mixed16.jsonl`
**Samples**: 16
**Runtime behavior changed**: no

## 1. Aggregate Counts

| metric | count |
|---|---:|
| `candidate_flaw_count` | 19 |
| `candidate_from_excerpt_limitation_count` | 1 |
| `candidate_from_fallback_count` | 0 |
| `candidate_from_recovery_failure_count` | 0 |
| `candidate_used_for_reject_count` | 18 |
| `candidate_with_grounded_evidence_count` | 9 |
| `candidate_without_evidence_count` | 10 |
| `confirmed_flaw_count` | 0 |
| `downgraded_flaw_count` | 0 |
| `grounded_paper_unresolved_count` | 11 |
| `open_unresolved_count` | 89 |
| `retracted_flaw_count` | 0 |
| `unresolved_count` | 89 |
| `unresolved_from_fallback_count` | 5 |
| `unresolved_from_recovery_failure_count` | 0 |
| `unresolved_from_system_meta_count` | 5 |
| `unresolved_resolvable_by_existing_support_count` | 1 |
| `unresolved_with_evidence_count` | 0 |
| `unresolved_with_target_claim_count` | 12 |
| `weak_or_system_unresolved_count` | 78 |

## 2. Open Unresolved Labels

| label | count |
|---|---:|
| `weak_or_unowned_unresolved` | 55 |
| `generic_system_question` | 17 |
| `grounded_paper_unresolved` | 11 |
| `system_meta_or_excerpt` | 5 |
| `resolvable_by_existing_support` | 1 |

## 3. Flaw Labels

| label | count |
|---|---:|
| `ungrounded_candidate` | 10 |
| `grounded_candidate` | 8 |
| `system_meta_candidate` | 1 |

## 4. Direction

- If weak/system unresolved dominates, the next simulation should close or downgrade those items before final decision.
- If grounded candidates dominate, candidate cleanup alone is unsafe; promotion/confirmation rules are needed.
- If ungrounded/meta candidates dominate reject use, candidate grounding filter is the next runtime candidate after offline validation.
