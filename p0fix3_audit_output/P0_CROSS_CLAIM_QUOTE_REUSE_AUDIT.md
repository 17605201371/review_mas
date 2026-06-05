# P0-4: Cross-Claim Quote Reuse & Independence Audit

## Summary

- `same_quote_same_claim_count`: 1
- `same_quote_cross_claim_count`: 2
- `claims_with_2plus_independent_support`: 2
- `total_unique_quotes_in_support`: 6
- `total_final_support_items`: 20

## Cross-Claim Quote Reuse

### Quote `quote-table-or-figure-1` -> claims: ['claim-1', 'claim-context-1', 'claim-2']
  - paper=9zEBK3E9bX claim=claim-2 ev=evidence-first-support-1-turn- str=strong role=empirical_result
  - paper=9zEBK3E9bX claim=claim-1 ev=evidence-first-support-2-turn- str=strong role=empirical_result
  - paper=QAAsnSRwgu claim=claim-2 ev=evidence-first-support-1-turn- str=strong role=empirical_result
  - paper=QAAsnSRwgu claim=claim-1 ev=evidence-first-support-3-turn- str=strong role=empirical_result
  - paper=WLgbjzKJkk claim=claim-2 ev=evidence-first-support-1-turn- str=medium role=empirical_result
  - paper=WLgbjzKJkk claim=claim-1 ev=evidence-first-support-2-turn- str=medium role=empirical_result
  - paper=WNxlJJIEVj claim=claim-1 ev=evidence-first-support-2-turn- str=strong role=empirical_result
  - paper=X41c4uB4k0 claim=claim-contex ev=evidence-first-support-1-turn- str=medium role=empirical_result
  - paper=hj323oR3rw claim=claim-2 ev=evidence-first-support-1-turn- str=strong role=empirical_result
  - paper=hj323oR3rw claim=claim-1 ev=evidence-first-support-3-turn- str=strong role=empirical_result

### Quote `quote-table-or-figure-2` -> claims: ['claim-context-2', 'claim-3', 'claim-2', 'claim-1']
  - paper=WNxlJJIEVj claim=claim-2 ev=evidence-first-support-1-turn- str=strong role=empirical_result
  - paper=WNxlJJIEVj claim=claim-3 ev=evidence-first-support-3-turn- str=strong role=empirical_result
  - paper=X41c4uB4k0 claim=claim-contex ev=evidence-first-support-3-turn- str=medium role=empirical_result
  - paper=ZHr0JajZfH claim=claim-2 ev=evidence-first-support-1-turn- str=strong role=empirical_result
  - paper=ZHr0JajZfH claim=claim-1 ev=evidence-first-support-2-turn- str=strong role=empirical_result

## Same Quote Same Claim (multi-turn)

- Quote `quote-negative-or-gap-1` used 2x for claim `claim-2`

## Independence

`claims_with_2plus_independent_support = 2`

- claim `claim-1`: 8 independence groups
- claim `claim-2`: 7 independence groups
