# P25.0 Model Decision

## Recovery-Relevant Outcome
- 4B avg_reward / median_reward / decision_correct_rate: 0.5427 / 0.5501 / 1.0
- 9B avg_reward / median_reward / decision_correct_rate: 0.5398 / 0.5442 / 1.0
- 4B validation_to_commit_rate: 0.5
- 9B validation_to_commit_rate: 0.6667
- 4B NO_EFFECT_PATCH count: 8
- 9B NO_EFFECT_PATCH count: 1

Current decision: 9B is materially better on recovery quality; next step can move to 9B expansion.

## Interpretation
- this compare is frozen at the p24.4 pipeline; changes in outcome are attributable to model capacity unless hardware forces otherwise.
- reward differences are secondary; the main read should come from failure-code shifts and real state-change commits.
