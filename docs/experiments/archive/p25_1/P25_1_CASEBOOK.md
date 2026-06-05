# P25.1 Casebook

## Case 1: 9B truly improves over 4B
- paper_id: `IqaQZ1Jdky`
- bucket: `reference_recovery`
- group: `A`
- 4B: emitted=3, validated=5, committed=0, top_failure=BLOCKED_BY_POLICY, state_change=none, reward=0.6116
- 9B: emitted=3, validated=6, committed=1, top_failure=BLOCKED_BY_POLICY, state_change=claim: uncertain -> unsupported x1, reward=0.5679
- reading: 9B unlocks commit

## Case 2: both models succeed
- paper_id: `2Cg4YrsCMA`
- bucket: `reference_recovery`
- group: `B`
- 4B: emitted=3, validated=4, committed=1, top_failure=BLOCKED_BY_POLICY, state_change=claim: uncertain -> unsupported x1, reward=0.4094
- 9B: emitted=2, validated=5, committed=1, top_failure=BLOCKED_BY_POLICY, state_change=claim: supported -> unsupported x1, reward=0.5133
- reading: policy block may be bottleneck; reward up without better patch quality

## Case 3: both models fail
- paper_id: `9EBSEkFSje`
- bucket: `reference_recovery`
- group: `C`
- 4B: emitted=0, validated=0, committed=0, top_failure=none, state_change=none, reward=0.6713
- 9B: emitted=0, validated=0, committed=0, top_failure=none, state_change=none, reward=0.7203
- reading: reward up without better patch quality

## Case 4: 9B reward rises without patch-quality gain
- paper_id: `2Cg4YrsCMA`
- bucket: `reference_recovery`
- group: `B`
- 4B: emitted=3, validated=4, committed=1, top_failure=BLOCKED_BY_POLICY, state_change=claim: uncertain -> unsupported x1, reward=0.4094
- 9B: emitted=2, validated=5, committed=1, top_failure=BLOCKED_BY_POLICY, state_change=claim: supported -> unsupported x1, reward=0.5133
- reading: policy block may be bottleneck; reward up without better patch quality

## Case 5: hardest recovery case
- paper_id: `NhLBhx5BVY`
- bucket: `reference_recovery`
- group: `C`
- 4B: emitted=5, validated=6, committed=0, top_failure=NO_EFFECT_PATCH, state_change=none, reward=0.4217
- 9B: emitted=4, validated=5, committed=0, top_failure=BLOCKED_BY_POLICY, state_change=none, reward=0.4897
- reading: 9B reduces no-effect; policy block may be bottleneck; reward up without better patch quality

## Case 6: historical sentinel case
- paper_id: `X41c4uB4k0`
- bucket: `historical_sentinel`
- group: `C`
- 4B: emitted=2, validated=1, committed=0, top_failure=SEMANTIC_MISMATCH, state_change=none, reward=0.1251
- 9B: emitted=0, validated=0, committed=0, top_failure=none, state_change=none, reward=0.1711
- reading: reward up without better patch quality

