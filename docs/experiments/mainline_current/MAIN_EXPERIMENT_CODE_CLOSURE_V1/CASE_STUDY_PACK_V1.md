# Case Study Pack v1 (4 representative samples)

- input: `outputs/results_main/review_infer/mainline_final_v1_closure_9b_fulltest39_20260504_gold.jsonl`
- gold labels: `docs/experiments/mainline_current/MAIN_EXPERIMENT_CODE_CLOSURE_V1/fulltest39_gold_labels_locked_20260504.json` (locked)
- CEF consistency: `outputs/results_main/review_infer/cef_consistency_v1.json`
- recovery sub-funnel: `outputs/results_main/review_infer/recovery_subfunnel_v1.json`

Each case is intentionally one of four representative *types* required by the C-direction Limitation audit (`PAPER_C_DIRECTION_LIMITATION_AUDIT.md` 不足七 退路 + INTEGRATED #3). Together they show: a successful conservative accept, a correct reject with positive support, a false reject of a gold accept, and a recovery worker self-abstain. The auto-generated narrative paragraphs are drafts; the author refines them before submission.

## Index

| # | type | paper_id |
|---|---|---|
| 1 | Recovered accept_like | `jVEoydFOl9` |
| 2 | High-support gold reject (correct reject, borderline_positive view) | `9zEBK3E9bX` |
| 3 | False-reject of gold accept (reject_like view) | `gzqrANCF4g` |
| 4 | Blocked recovery (worker self-abstain dominant) | `ye3NrNrYOY` |

## Case — Recovered accept_like

- **paper_id**: `jVEoydFOl9`
- **gold**: `accept`
- **system binary**: `accept` (✓)
- **final-view recommendation**: `accept_like`
- **headline**: 唯一同时满足 binary accept 与 final-view accept_like 的样本；展示系统在 evidence 充分时安全恢复 accept 的能力。

### Claims

| claim_id | importance | status | supporting_evidence_ids |
|---|---|---|---|
| `claim-1` | high | unsupported | evidence-1-turn-2 |
| `claim-2` | high | supported | evidence-1-turn-5 |
| `claim-3` | high | supported | evidence-2-turn-2, evidence-2-turn-5 |

### Evidence

| evidence_id | source | bucket | stance | strength | claim_id |
|---|---|---|---|---|---|
| `evidence-1-turn-2` | results | result_or_experiment | supports | strong | `claim-1` |
| `evidence-2-turn-2` | method | method_or_approach | supports | strong | `claim-3` |
| `evidence-1-turn-5` | results | result_or_experiment | supports | strong | `claim-2` |
| `evidence-2-turn-5` | method | method_or_approach | supports | strong | `claim-3` |

### Flaws

| flaw_id | severity | status | grounding | related_claim_ids | title |
|---|---|---|---|---|---|
| `flaw-fallback-1` | minor | downgraded | fallback_unverified | claim-1 | { "flaw_candidates": [ { "flaw_id": "flaw-1", "title": "Lack of Grounded Evidence for Core Claims",  |

### Recovery funnel (this paper)

- emitted: **1**
- worker self-abstain (BLOCKED_BY_POLICY): **1**
- validator rejected: **0**
- committed: **0**
- sample worker self-abstain reasons:
  - _"Missing specific experimental results or tables required to validate the 300% improvement metric."_

### State auditability (CEF consistency, this paper)

- consistency_score = **1.0000**
- checks = 12, violations = 0

### Narrative (draft; author to refine)

**Why this case matters**: 唯一同时满足 binary accept 与 final-view accept_like 的样本；展示系统在 evidence 充分时安全恢复 accept 的能力。

**Binary decision**: gold = `accept`, system = `accept` → **correct**. Final-view bucket: **accept_like**.

**Evidence formation**: real_strong = 4, non-abstract = 4, empirical = 2, method = 2. This is the support footprint the final-view recommendation acted on.

**Recovery activity**: emitted = 1, worker self-abstain = 1, validator rejected = 0, committed = 0. Sample worker abstain reasons: "Missing specific experimental results or tables required to validate the 300% improvement metric."

**State auditability**: CEF consistency score = 1.0000 (violations / checks = 0/12). ID and lifecycle invariants hold for this paper.

**Author note**: the above paragraphs are auto-generated drafts; expand with paper-specific contribution / weakness narrative before submission. The structured tables above are the authoritative data.


## Case — High-support gold reject (correct reject, borderline_positive view)

- **paper_id**: `9zEBK3E9bX`
- **gold**: `reject`
- **system binary**: `reject` (✓)
- **final-view recommendation**: `borderline_positive`
- **headline**: 系统正确拒绝 gold reject 论文，但 evidence 层形成 3 条 real strong support；hard-negative grounding 不足，因此 final-view 落入 borderline_positive 而非 reject_like。

### Claims

| claim_id | importance | status | supporting_evidence_ids |
|---|---|---|---|
| `claim-1` | high | uncertain | _∅_ |
| `claim-2` | high | unsupported | evidence-1-turn-2 |
| `claim-3` | high | supported | evidence-2-turn-2, evidence-1-turn-5 |

### Evidence

| evidence_id | source | bucket | stance | strength | claim_id |
|---|---|---|---|---|---|
| `evidence-1-turn-2` | figure | result_or_experiment | supports | strong | `claim-2` |
| `evidence-2-turn-2` | figure | result_or_experiment | supports | strong | `claim-3` |
| `evidence-1-turn-5` | figure | result_or_experiment | supports | strong | `claim-3` |

### Flaws

| flaw_id | severity | status | grounding | related_claim_ids | title |
|---|---|---|---|---|---|
| `flaw-fallback-1` | minor | downgraded | fallback_unverified | claim-1 | { "flaw_candidates": [ { "flaw_id": "flaw-1", "title": "Critical Data Truncation Prevents Validity A |

### Recovery funnel (this paper)

- emitted: **1**
- worker self-abstain (BLOCKED_BY_POLICY): **1**
- validator rejected: **0**
- committed: **0**
- sample worker self-abstain reasons:
  - _"Missing full paper text and specific quantitative results regarding annotation burden reduction."_

### State auditability (CEF consistency, this paper)

- consistency_score = **1.0000**
- checks = 9, violations = 0

### Narrative (draft; author to refine)

**Why this case matters**: 系统正确拒绝 gold reject 论文，但 evidence 层形成 3 条 real strong support；hard-negative grounding 不足，因此 final-view 落入 borderline_positive 而非 reject_like。

**Binary decision**: gold = `reject`, system = `reject` → **correct**. Final-view bucket: **borderline_positive**.

**Evidence formation**: real_strong = 3, non-abstract = 3, empirical = 3, method = 0. This is the support footprint the final-view recommendation acted on.

**Recovery activity**: emitted = 1, worker self-abstain = 1, validator rejected = 0, committed = 0. Sample worker abstain reasons: "Missing full paper text and specific quantitative results regarding annotation burden reduction."

**State auditability**: CEF consistency score = 1.0000 (violations / checks = 0/9). ID and lifecycle invariants hold for this paper.

**Author note**: the above paragraphs are auto-generated drafts; expand with paper-specific contribution / weakness narrative before submission. The structured tables above are the authoritative data.


## Case — False-reject of gold accept (reject_like view)

- **paper_id**: `gzqrANCF4g`
- **gold**: `accept`
- **system binary**: `reject` (✗ false-reject)
- **final-view recommendation**: `reject_like`
- **headline**: gold accept 但 system 误判为 reject_like。同时是 CEF Consistency 唯一违规来源（2 条 flaw 引用了已被替换的 evidence id），可串联 State Hygiene 章节。

### Claims

| claim_id | importance | status | supporting_evidence_ids |
|---|---|---|---|
| `claim-1` | high | unsupported | _∅_ |
| `claim-2` | medium | supported | evidence-2-turn-2, evidence-1-turn-8 |

### Evidence

| evidence_id | source | bucket | stance | strength | claim_id |
|---|---|---|---|---|---|
| `evidence-1-turn-2` | abstract | abstract | contradicts | medium | `claim-1` |
| `evidence-2-turn-2` | results | result_or_experiment | supports | strong | `claim-2` |
| `evidence-1-turn-8` | results | other_or_unspecified | supports | medium | `claim-2` |

### Flaws

| flaw_id | severity | status | grounding | related_claim_ids | title |
|---|---|---|---|---|---|
| `flaw-1` | critical | candidate |  | claim-1 | Overstated Performance Claim Without Evidence |
| `flaw-2` | major | candidate |  | claim-1 | Incomplete Methodological Verification |

### Recovery funnel (this paper)

- emitted: **4**
- worker self-abstain (BLOCKED_BY_POLICY): **1**
- validator rejected: **3**
- committed: **0**
- sample worker self-abstain reasons:
  - _"Cannot verify claim without full text."_

### State auditability (CEF consistency, this paper)

- consistency_score = **0.8000**
- checks = 10, violations = 2
- violation records:
  - `R2_flaw_evidence_id_exists`: flaw_id=flaw-1, missing_evidence_id=evidence-1-turn-3
  - `R2_flaw_evidence_id_exists`: flaw_id=flaw-2, missing_evidence_id=evidence-1-turn-3

### Narrative (draft; author to refine)

**Why this case matters**: gold accept 但 system 误判为 reject_like。同时是 CEF Consistency 唯一违规来源（2 条 flaw 引用了已被替换的 evidence id），可串联 State Hygiene 章节。

**Binary decision**: gold = `accept`, system = `reject` → **false reject**. Final-view bucket: **reject_like**.

**Evidence formation**: real_strong = 1, non-abstract = 1, empirical = 1, method = 0. This is the support footprint the final-view recommendation acted on.

**Recovery activity**: emitted = 4, worker self-abstain = 1, validator rejected = 3, committed = 0. Sample worker abstain reasons: "Cannot verify claim without full text."

**State auditability**: CEF consistency score = 0.8000 (violations / checks = 2/10). This paper carries the only R2 violations in fulltest39 — flaw records reference an evidence id (`evidence-1-turn-3`) that has been replaced in the final ReviewState. The audit surfaces this lifecycle drift rather than hiding it; this is precisely the kind of intra-state inconsistency the C-direction *auditability* claim is intended to expose.

**Author note**: the above paragraphs are auto-generated drafts; expand with paper-specific contribution / weakness narrative before submission. The structured tables above are the authoritative data.


## Case — Blocked recovery (worker self-abstain dominant)

- **paper_id**: `ye3NrNrYOY`
- **gold**: `reject`
- **system binary**: `reject` (✓)
- **final-view recommendation**: `borderline_insufficient`
- **headline**: 5 个 recovery turn 全部是 worker self-abstain（action='blocked'），体现 BLOCKED_BY_POLICY 的真实语义：worker 在证据不足时主动拒绝构造 state mutation。

### Claims

| claim_id | importance | status | supporting_evidence_ids |
|---|---|---|---|
| `claim-1` | high | unsupported | evidence-2-turn-2 |
| `claim-2` | high | unsupported | evidence-1-turn-2 |
| `claim-3` | medium | uncertain | _∅_ |

### Evidence

| evidence_id | source | bucket | stance | strength | claim_id |
|---|---|---|---|---|---|
| `evidence-1-turn-2` | Figure 2 | result_or_experiment | supports | strong | `claim-2` |
| `evidence-2-turn-2` | Section 2 | method_or_approach | supports | strong | `claim-1` |

### Flaws

| flaw_id | severity | status | grounding | related_claim_ids | title |
|---|---|---|---|---|---|
| `flaw-fallback-1` | minor | downgraded | fallback_unverified | claim-1 | { "flaw_candidates": [ { "flaw_id": "flaw-1", "title": "Insufficient Evidence for Core Claims", "des |

### Recovery funnel (this paper)

- emitted: **5**
- worker self-abstain (BLOCKED_BY_POLICY): **5**
- validator rejected: **0**
- committed: **0**
- sample worker self-abstain reasons:
  - _"Missing full Table 4 data required to verify accuracy comparison against TCMT-FT."_
  - _"Missing quantitative results or statistical validation in the provided text."_
  - _"Missing ablation study data and methodology details required for evaluation."_

### State auditability (CEF consistency, this paper)

- consistency_score = **1.0000**
- checks = 6, violations = 0

### Narrative (draft; author to refine)

**Why this case matters**: 5 个 recovery turn 全部是 worker self-abstain（action='blocked'），体现 BLOCKED_BY_POLICY 的真实语义：worker 在证据不足时主动拒绝构造 state mutation。

**Binary decision**: gold = `reject`, system = `reject` → **correct**. Final-view bucket: **borderline_insufficient**.

**Evidence formation**: real_strong = 2, non-abstract = 2, empirical = 1, method = 1. This is the support footprint the final-view recommendation acted on.

**Recovery activity**: emitted = 5, worker self-abstain = 5, validator rejected = 0, committed = 0. Sample worker abstain reasons: "Missing full Table 4 data required to verify accuracy comparison against TCMT-FT."; "Missing quantitative results or statistical validation in the provided text."; "Missing ablation study data and methodology details required for evaluation."

**State auditability**: CEF consistency score = 1.0000 (violations / checks = 0/6). ID and lifecycle invariants hold for this paper.

**Author note**: the above paragraphs are auto-generated drafts; expand with paper-specific contribution / weakness narrative before submission. The structured tables above are the authoritative data.


---

Generated by `scripts/build_case_study_pack_v1.py`. Cases selected per the C-direction Limitation audit. Numbers reproducible from the inputs above.
