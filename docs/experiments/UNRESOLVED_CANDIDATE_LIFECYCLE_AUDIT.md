# Unresolved + Candidate Flaw Lifecycle Audit

**Input**: `/root/zssmas_mainline/outputs/results_main/review_infer/p25_1_state_hygiene_4b_focus.jsonl`
**Samples**: 16
**Runtime behavior changed**: no

## 1. Aggregate Counts

| metric | count |
|---|---:|
| `candidate_flaw_count` | 20 |
| `candidate_from_excerpt_limitation_count` | 1 |
| `candidate_from_fallback_count` | 0 |
| `candidate_from_recovery_failure_count` | 0 |
| `candidate_used_for_reject_count` | 19 |
| `candidate_with_grounded_evidence_count` | 6 |
| `candidate_without_evidence_count` | 14 |
| `confirmed_flaw_count` | 1 |
| `downgraded_flaw_count` | 0 |
| `grounded_paper_unresolved_count` | 1 |
| `open_unresolved_count` | 126 |
| `retracted_flaw_count` | 0 |
| `unresolved_count` | 126 |
| `unresolved_from_fallback_count` | 1 |
| `unresolved_from_recovery_failure_count` | 0 |
| `unresolved_from_system_meta_count` | 6 |
| `unresolved_resolvable_by_existing_support_count` | 0 |
| `unresolved_with_evidence_count` | 0 |
| `unresolved_with_target_claim_count` | 1 |
| `weak_or_system_unresolved_count` | 125 |

## 2. Open Unresolved Labels

| label | count |
|---|---:|
| `weak_or_unowned_unresolved` | 91 |
| `generic_system_question` | 28 |
| `system_meta_or_excerpt` | 6 |
| `grounded_paper_unresolved` | 1 |

## 3. Flaw Labels

| label | count |
|---|---:|
| `ungrounded_candidate` | 13 |
| `grounded_candidate` | 6 |
| `confirmed_grounded_flaw` | 1 |
| `system_meta_candidate` | 1 |

## 4. Direction

- If weak/system unresolved dominates, the next simulation should close or downgrade those items before final decision.
- If grounded candidates dominate, candidate cleanup alone is unsafe; promotion/confirmation rules are needed.
- If ungrounded/meta candidates dominate reject use, candidate grounding filter is the next runtime candidate after offline validation.

## 5. Interpretation

The audit confirms lifecycle collapse, but it also warns against a crude runtime cleanup:

- `open_unresolved_count=126`, but only `1` item is classified as grounded paper unresolved. Most unresolved items are weak, generic, or system-facing.
- `candidate_flaw_count=20`; `14` are not grounded, but `19` candidates still qualify as reject-usable major/critical signals under current decision logic.
- `confirmed_flaw_count=1`, `downgraded_flaw_count=0`, `retracted_flaw_count=0`: there is almost no lifecycle movement after candidate creation.

The next effective fix is not to delete all weak unresolved/candidates. It is to add provenance and lifecycle rules precise enough to distinguish:

1. paper-grounded unresolved issue;
2. system uncertainty / review limitation;
3. grounded candidate flaw;
4. ungrounded candidate concern;
5. confirmed flaw.

Until that distinction exists, final decision will either remain all reject or become unsafe by false-accepting reject controls.

