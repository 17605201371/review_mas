# Coupled State Hygiene Simulation v1

**Input**: `/root/zssmas_mainline/outputs/results_main/review_infer/p25_1_state_hygiene_4b_focus.jsonl`
**Samples**: 16
**Runtime behavior changed**: no

## 1. Summary

| rule | acc | macro-F1 | accept R | reject R | pred A | pred R | recovered A | false A | decision |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| `baseline` | 0.4375 | 0.3043 | 0.0000 | 1.0000 | 0 | 16 | 0 | 0 | baseline |
| `C1_system_unresolved_meta_candidate` | 0.4375 | 0.3043 | 0.0000 | 1.0000 | 0 | 16 | 0 | 0 | reject |
| `C2_system_unresolved_ungrounded_candidate` | 0.4375 | 0.3043 | 0.0000 | 1.0000 | 0 | 16 | 0 | 0 | reject |
| `C3_unowned_unresolved_ungrounded_candidate` | 0.5625 | 0.5152 | 0.2222 | 1.0000 | 2 | 14 | 2 | 0 | candidate |
| `C4_oracle_negative_plus_support_guard` | 0.5625 | 0.5152 | 0.2222 | 1.0000 | 2 | 14 | 2 | 0 | candidate |

## 2. Flips

### C1_system_unresolved_meta_candidate

- recovered_accept_ids: `[]`
- false_accept_ids: `[]`
- all_flips: `[]`

### C2_system_unresolved_ungrounded_candidate

- recovered_accept_ids: `[]`
- false_accept_ids: `[]`
- all_flips: `[]`

### C3_unowned_unresolved_ungrounded_candidate

- recovered_accept_ids: `['QAAsnSRwgu', 'KI9NqjLVDT']`
- false_accept_ids: `[]`
- all_flips: `['QAAsnSRwgu', 'KI9NqjLVDT']`

### C4_oracle_negative_plus_support_guard

- recovered_accept_ids: `['QAAsnSRwgu', 'KI9NqjLVDT']`
- false_accept_ids: `[]`
- all_flips: `['QAAsnSRwgu', 'KI9NqjLVDT']`


## 3. Decision

Safe offline candidate(s): `['C3_unowned_unresolved_ungrounded_candidate', 'C4_oracle_negative_plus_support_guard']`.
Review case details before runtime implementation.

## 4. Interpretation

`C3_unowned_unresolved_ungrounded_candidate` is the first non-oracle rule that breaks reject collapse safely on the 4B focus set:

- recovered accepts: `QAAsnSRwgu`, `KI9NqjLVDT`
- false accepts: none
- accept recall: `0.2222`
- reject recall: `1.0000`
- macro-F1: `0.5152`

The key is coupling. Earlier isolated rules failed because they only cleaned negative state or only repaired positive support. C3 works because it combines:

1. non-fallback support accounting;
2. claim-status reconciliation for real claims with strong support;
3. closing system/generic/unowned unresolved items;
4. downgrading ungrounded major/critical candidate flaws;
5. rejecting fallback-bound support as accept evidence.

`aTBE70xiFw` stays reject because its strong positives are fallback-bound and therefore do not count as accept support.

## 5. Runtime Candidate

C3 is a plausible minimal runtime state-hygiene candidate, but it should be implemented conservatively:

- Run hygiene after each state merge or before final decision, not inside worker generation.
- Record all changes in `revision_log` with a `state_hygiene` source.
- Do not delete unresolved/flaws; mark them `resolved`, `downgraded`, or `review_limitation`.
- Count non-fallback strong support separately from fallback support.
- Keep final decision thresholds unchanged except for using hygiene-cleaned state.

Next step can move from offline simulation to a small runtime implementation of **Coupled State Hygiene v1**, then run the same 16-sample 4B focus set.

