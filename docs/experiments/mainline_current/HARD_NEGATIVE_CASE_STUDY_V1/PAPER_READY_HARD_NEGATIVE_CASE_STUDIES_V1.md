# PAPER_READY_HARD_NEGATIVE_CASE_STUDIES_V1

## 结论

这组案例用于论文 discussion / failure taxonomy：系统已经能形成 real-claim、non-abstract、empirical support，但 final recommendation 不能把正向 support 数量直接映射成 accept。原因有两面：

1. 部分 gold reject 样本也有高质量正向 support，但缺少稳定 paper-grounded hard-negative blocker；它们应进入 borderline / human-review，而不是自动 accept。
2. 部分 gold accept 样本仍残留 stale gap、fallback critique 或 meta burden；这些 raw negative burden 不能直接作为 reject 依据。

## Case 1: high-support reject, no grounded blocker (`9zEBK3E9bX`)

- `gold`: reject
- `recommendation_view`: borderline_positive
- `real_strong`: 3
- `nonabstract`: 3
- `empirical`: 3
- `independent_group_count`: 3
- `hard_negative_status`: unverified_blocker_candidate

### Positive chain

- `claim-2`: SPOT pre-trains 3D and 2D backbones to improve performance across datasets/tasks.
- `claim-3`: SPOT performs best among pre-training methods on various datasets.
- Evidence is empirical/result-oriented: Figure 1(a) and Figure 1(b) support scalable performance and best-performance claims.

### Negative chain

- The first blocker is only `open_missing_claim_support`: `Claim claim-1 lacks grounded supporting evidence.`
- The flaw is `flaw-fallback-1`, downgraded, source=`fallback-extraction`.
- Conflicts are fallback/state conflicts, not stable paper-grounded hard negatives.

### Interpretation

This is the strongest warning against a support-count accept rule: a reject paper can have several empirical supports. Without grounded hard-negative evidence, the right recommendation view is borderline/human-review, not automatic accept.

## Case 2: reject with an unverified paper-grounded conflict (`mHv6wcBb0z`)

- `gold`: reject
- `recommendation_view`: borderline_insufficient
- `real_strong`: 1
- `nonabstract`: 1
- `empirical`: 1
- `hard_negative_status`: unverified_blocker_candidate

### Positive chain

- `claim-1`: noise regularization prevents DCCA collapse by addressing weight matrix redundancy.
- Evidence is empirical/result-oriented: a figure suggests NR-DCCA avoids redundancy/collapse relative to standard DCCA.

### Negative chain

- There is a confirmed critical flaw titled `Incomplete Paper Text Prevents Valid Evidence Verification`.
- The conflict is paper-linked but still partly context-limited: it concerns tension between supported status and inability to verify the full paper.

### Interpretation

This case shows why hard-negative grounding must separate paper defects from context limitations. It has a plausible blocker, but the blocker is not yet a clean paper-grounded empirical/soundness flaw; therefore it should not be used as a broad runtime reject template.

## Case 3: accept-protect success (`jVEoydFOl9`)

- `gold`: accept
- `recommendation_view`: accept_like
- `real_strong`: 4
- `nonabstract`: 4
- `empirical`: 3
- `method`: 1
- `independent_group_count`: 4
- `hard_negative_status`: context_limited_no_grounded_blocker

### Positive chain

- `claim-1`: generalizes to 50+ KGs.
- `claim-2`: zero-shot performance exceeds supervised baselines by up to 300%.
- `claim-3`: relative entity/relation representations enable transfer across graphs.
- Evidence covers both method and empirical/result claims.

### Negative chain

- Raw gaps still say claims lack grounded evidence, but the evidence map already contains strong bound support.
- Fallback flaw is downgraded and source=`fallback-extraction`.
- Conflicts are fallback/state conflicts, not paper-grounded blockers.

### Interpretation

This case demonstrates why final-view hygiene is necessary: raw negative burden would reject a clearly support-rich accept sample. The current `accept_like` output is justified because there is no grounded blocker.

## Case 4: accept-protect borderline (`KI9NqjLVDT`)

- `gold`: accept
- `recommendation_view`: borderline_positive
- `real_strong`: 3
- `nonabstract`: 3
- `empirical`: 3
- `independent_group_count`: 3
- `hard_negative_status`: unverified_blocker_candidate

### Positive chain

- `claim-1`: ReMasker learns missingness-invariant representations.
- `claim-2`: ReMasker outperforms or matches 13 methods on 12 datasets.
- Evidence includes empirical benchmark support and theoretical/empirical support for missingness invariance.

### Negative chain

- The first blocker is `open_missing_claim_support` for `claim-3`.
- The fallback flaw is downgraded and not paper-grounded.

### Interpretation

This case should not be hard-rejected. It is a good example of `borderline_positive`: enough positive support exists, but one claim still lacks clean support. This is better modeled as human-review/borderline than binary reject.

## Paper-use summary

These cases support the paper's main claim: the system should not be evaluated only as an accept/reject classifier. Its useful behavior is evidence-aligned review assistance: it exposes positive support, distinguishes stale/meta negative burden from paper-grounded blockers, and routes uncertain cases to borderline/human review instead of forcing a brittle binary decision.
