# P25.0 Casebook

## Case 1: 4B NO_EFFECT_PATCH, 9B success
No clean instance in this bounded compare; nearest cases should be read from the pairwise table.

## Case 2: 4B BLOCKED_BY_POLICY, 9B success
No clean instance in this bounded compare; nearest cases should be read from the pairwise table.

## Case 3: both commit successfully
- paper_id: `IqaQZ1Jdky`
- bucket: `recovery_relevant`
- 4B: emitted=4, committed=2, top_failure=BLOCKED_BY_POLICY, reward=0.5253
- 9B: emitted=2, committed=1, top_failure=BLOCKED_BY_POLICY, reward=0.5829
- reading: reward up without better patch quality

## Case 4: both emit but both fail
- paper_id: `GSckuQMzBG`
- bucket: `recovery_relevant`
- 4B: emitted=4, committed=0, top_failure=NO_EFFECT_PATCH, reward=0.429
- 9B: emitted=3, committed=0, top_failure=BLOCKED_BY_POLICY, reward=0.404
- reading: stable

## Case 5: 9B reward higher but patch quality not better
- paper_id: `9EBSEkFSje`
- bucket: `recovery_relevant`
- 4B: emitted=0, committed=0, top_failure=BLOCKED_BY_POLICY, reward=0.6434
- 9B: emitted=5, committed=0, top_failure=INSUFFICIENT_EVIDENCE, reward=0.647
- reading: reward up without better patch quality

## Case 6: historical sentinel improvement
No clean instance in this bounded compare; nearest cases should be read from the pairwise table.

