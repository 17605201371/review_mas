# P25.1 Direction Decision

## Main Read
- 9B main expanded rows: 24 recovery-relevant + 2 sentinel rows in the actual run.
- Fixed reference compare rows: 8 recovery rows + 2 sentinel rows.
- 4B reference avg_reward / median_reward / decision_correct_rate: 0.5324 / 0.56 / 1.0
- 9B reference avg_reward / median_reward / decision_correct_rate: 0.548 / 0.5322 / 1.0
- 4B reference validation_to_commit_rate: 0.3333
- 9B reference validation_to_commit_rate: 0.6667
- 4B reference NO_EFFECT_PATCH: 12
- 9B reference NO_EFFECT_PATCH: 3
- 4B reference state changes: 2
- 9B reference state changes: 4
- Pairwise groups: A=3, B=1, C=5, reverse_regression=1, reward_only=6

## Research Questions
1. Does the 9B advantage remain stable on a larger recovery-relevant pool? yes.
2. Where does 9B gain come from? both fewer NO_EFFECT_PATCH and higher commit throughput.
3. What does the larger BLOCKED_BY_POLICY footprint mean? blocked cases likely reflect a stricter but still more productive 9B recovery policy; the gate is a visible secondary bottleneck, not the primary reason to stop scaling.
4. What should happen next? 9B is stable enough to become the main working model; next step can move to a larger 9B recovery benchmark instead of an immediate policy-block calibration.
