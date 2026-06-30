# Experiment Section Draft

Date: 2026-07-01

This is a paper-facing draft for the experiments section. It intentionally reports the current evidence conservatively: DrMAS is evaluated as a ReviewState verification and recovery framework, not as an accept/reject predictor or a broad autonomous flaw generator.

## 4. Experiments

### 4.1 Research Questions

We evaluate DrMAS around four questions that follow from the ReviewState thesis.

**RQ1: Can the system verify reviewer issues without relying on copied negative quotes?**

This tests the obligation-grounded review issue bundle pathway. The expected evidence is not a negative sentence from the paper, but a verified mismatch among a paper claim, observed inventory, and a concrete missing or mismatched entity.

**RQ2: Does the final view suppress unsafe negative-evidence artifacts?**

This tests whether positive statements, author limitations, quote-bank artifacts, retrieval gaps, and stale absence records are prevented from becoming active negative-grounding conflicts.

**RQ3: Can verified issues trigger non-destructive recovery?**

This tests whether supported claims can remain supported while being marked contested by verified review issues, rather than being destructively downgraded.

**RQ4: What still limits the current system?**

This covers the remaining gap between a conservative state-verification framework and broad autonomous reviewer issue discovery.

### 4.2 Evaluation Setting

We use the hard-negative diagnostic set `hard_negative_20_20260611.parquet`, a 20-paper subset designed to stress negative-evidence and reviewer-issue handling. The main reported run is the P28.6 TargetRefine2 offline recompute over a completed MiMo v2.5 hardneg20 run:

```text
P28_6_CONFLICTFIX_TARGETREFINE2_194911_*
```

The run uses the P28 review-issue bundle pipeline with negative quote hygiene, targeted negative search, free-form reviewer issue candidates, and conservative final-view hygiene. We report the P28.6 recompute because it applies the final verifier and conflict-cleaning logic consistently to the completed run.

We also include a fresh MiMo rerun sanity check:

```text
P28_6_CONFLICTFIX_MIMO_PARTIAL16_224133_*
```

This run completed 16/20 papers before the MiMo API returned `402 Insufficient account balance`. We use it only as a partial consistency check, not as the main full20 result.

### 4.3 Metrics

We distinguish direct quote-grounded negatives from obligation-grounded review issues.

**Direct quote-grounded negative.** A paper quote that itself supports a reviewer-negative relation after grounding, semantic, and review-relation verification. This is counted by `review_negative_verified_count`.

**Obligation-grounded review issue.** A verified issue bundle supported by a real claim anchor, observed inventory anchor, concrete missing or mismatched entity, and a counterevidence check. This is counted by `verified_review_issue_count` and deduplicated by `verified_review_issue_cluster_count`.

We report rows and clusters separately. Rows are individual verified issue records. Clusters deduplicate repeated detections of the same issue target in the same paper. The paper-level headline uses clusters.

Safety and hygiene metrics include:

- `negative_grounding_conflict_count`;
- `negative_semantic_anchor_conflict_count`;
- `semantic_negative_without_review_relation_count`;
- `negative_evidence_unlinked_to_flaw`;
- `positive_or_neutral_negative_candidate_count`.

Recovery metrics include:

- `mark_contested_commit_count`;
- `recovery_case_verified_review_issue_repair`;
- `recovery_unsafe_downgrade_attempt_blocked`.

### 4.4 Main Result: Verified Review Issue Bundles

Table 1 reports the P28.6 full20 offline recompute. DrMAS verifies 13 review issue rows, which collapse to 9 issue clusters. Manual audit judges 8 of the 9 clusters as valid or defensible reviewer concerns.

| Metric | Value |
| --- | ---: |
| papers | 20 |
| direct quote-grounded reviewer negatives | 0 |
| verified review issue rows | 13 |
| verified review issue clusters | 9 |
| duplicate review issue rows | 4 |
| reviewer-candidate issue rows | 13 |
| critique-payload candidate rows | 2 |
| deterministic-seed candidate rows | 11 |
| claim-obligation fallback rows | 0 |
| verified missing-ablation clusters | 6 |
| active negative grounding conflicts | 0 |
| semantic anchor conflicts | 0 |
| semantic negatives without review relation | 0 |
| unlinked negative evidence | 0 |
| positive/neutral negative candidates | 0 |
| protection | PASS |

**Table 1 caption.** P28.6 verifies obligation-grounded review issue bundles conservatively. The main count is the deduplicated cluster count, not the raw row count. The direct quote-grounded negative lane remains strict and produces no verified direct negatives in this run.

The key interpretation is that the useful negative-review signal does not appear as copied paper-negative text. It appears as verified claim-inventory-obligation mismatch. This supports the ReviewState thesis: reviewer issues should be represented as auditable state objects rather than as unstructured negative snippets.

### 4.5 Manual Cluster Audit

Table 2 summarizes the manual cluster audit. Three clusters are strong A-class issues; five are defensible B-class issues; one is a C-class concern that should not be counted in a paper-ready precision headline.

| Cluster target | Issue type | Manual label | Paper use |
| --- | --- | --- | --- |
| recurrent draft model | missing_ablation | A | strong case study |
| acceptance prediction head | missing_ablation | A | strong case study |
| generalized noise regularization | missing_ablation | A | strong case study |
| class-balancing CE loss | missing_ablation | B | defensible example |
| GrCN / ControllNet reproducibility details | reproducibility_gap | B | defensible example |
| PropGCL transformation phase / weights | missing_ablation | B | defensible example |
| recent GNN / graph-transformer baselines | missing_baseline | B | defensible example |
| EqualAL baseline | missing_baseline | B | defensible example |
| number of motion components beyond K=4 | missing_ablation | C | exclude from conservative quality count |

**Table 2 caption.** Manual audit separates system-verified issue clusters from paper-ready review-worthy clusters. We report 8/9 A/B clusters as the conservative quality count.

The issue distribution is intentionally reported as a limitation: 6 of the 9 clusters are missing-ablation issues, 2 are missing-baseline issues, and 1 is a reproducibility issue. This is enough to demonstrate the issue-bundle verification mechanism, but not enough to claim broad reviewer issue diversity.

### 4.6 Recovery And Safety

Table 3 reports recovery and safety signals. The main recovery action is `mark_contested`: a supported claim can remain supported while being marked contested by a verified review issue. This is non-destructive state repair, not a decision override.

| Metric | Full20 offline | Fresh partial16 |
| --- | ---: | ---: |
| completed papers | 20 | 16 |
| mark-contested commits | 14 | 5 |
| verified-review-issue repairs | 6 | 5 |
| unsafe downgrade attempts blocked | 1 | 2 |
| active negative grounding conflicts | 0 | 0 |
| semantic anchor conflicts | 0 | 0 |
| unlinked negative evidence | 0 | 0 |
| positive/neutral negative candidates | 0 | 0 |

**Table 3 caption.** Recovery is evaluated as state repair. Verified issues can expose supported-but-contested claims without destructively downgrading claim status. The fresh partial16 rerun is included only as a consistency check because the MiMo account balance stopped the run before all 20 papers completed.

The recovery result should be phrased carefully. The full20 result is an offline recompute over a completed run, so its recovery counts should not be described as a fresh full20 live rerun. The fresh partial16 run gives a cleaner live-run sanity check, but it is incomplete.

### 4.7 Diagnostic Progress Across P28

Table 4 describes the role of the latest P28 steps. The sequence should not be presented as simple metric maximization. P28.6 is a precision and hygiene checkpoint.

| Stage | Main effect | Paper interpretation |
| --- | --- | --- |
| Raw P28.5 | higher issue row count but generic or malformed missing-ablation targets | useful recall signal, not paper-ready |
| TargetRefine2 | rejects generic targets and keeps 9 verified clusters | precision checkpoint |
| ConflictFix P28.6 | moves stale or quote-bank false negative anchors out of active conflicts | final-view hygiene checkpoint |

**Table 4 caption.** The P28 progression improves precision and final-view hygiene. It does not solve direct quote-grounded negative discovery.

### 4.8 Discussion

The strongest current result is not the number of negative quotes. In fact, direct quote-grounded reviewer negatives remain at zero. This is consistent with the main insight: many useful review concerns are not negative sentences in the paper. They are reviewer-inferred obligation gaps that require structured verification.

The system currently verifies 9 issue clusters and passes the measured hygiene protections. This supports a conservative claim: DrMAS can turn reviewer-style concerns into auditable ReviewState objects and prevent several common false-negative-evidence failure modes.

The result is not yet a broad autonomous review benchmark. Most verified issues come from deterministic reviewer seeds rather than Critique payload candidates, and the issue distribution is missing-ablation heavy. The appropriate next step is not to loosen the verifier, but to improve entity-level obligation extraction and Critique-driven candidate generation while preserving the same final-view protections.

### 4.9 Limitations

This experiment has five important limitations.

First, the direct quote-grounded negative lane remains weak: `review_negative_verified_count=0`.

Second, the issue distribution is narrow. The current verified clusters are mostly missing-ablation issues.

Third, the candidate source distribution shows that autonomous Critique discovery is immature: only 2 verified rows come from Critique payload candidates, while 11 come from deterministic reviewer seeds.

Fourth, the fresh MiMo rerun is incomplete. It stopped at 16/20 papers because the MiMo API returned `402 Insufficient account balance`.

Fifth, hardneg20 is a diagnostic set. It is useful for stress-testing ReviewState hygiene and reviewer issue verification, but it is not enough by itself to support broad benchmark claims.

### 4.10 Required Next Experiment

Before treating these results as final paper evidence, we need a fresh full20 P28.6 run with the current code. Acceptance criteria:

- `verified_review_issue_cluster_count >= 8`;
- manual A/B clusters >= 7;
- `negative_grounding_conflict_count=0`;
- `negative_semantic_anchor_conflict_count=0`;
- `semantic_negative_without_review_relation_count=0`;
- `negative_evidence_unlinked_to_flaw=0`;
- `positive_or_neutral_negative_candidate_count=0`.

If MiMo balance remains unavailable, the paper should explicitly describe the full20 result as an offline recompute and the partial16 result as the freshest live sanity check.

## Drop-In Result Paragraph

On hardneg20, P28.6 verifies 13 obligation-grounded review issue rows, which deduplicate to 9 issue clusters. Manual audit judges 8 of these 9 clusters as valid or defensible reviewer concerns. The direct quote-grounded negative lane remains strict and produces no verified direct negatives, indicating that the useful review signal comes primarily from claim-inventory-obligation mismatch rather than copied negative paper text. Final-view hygiene remains clean: active negative-grounding conflicts, semantic anchor conflicts, semantic negatives without review relation, unlinked negative evidence, and positive/neutral negative candidates are all zero. Recovery is non-destructive: verified review issues can mark supported claims as contested without downgrading claim status.

## Drop-In Limitation Paragraph

These results should be interpreted as evidence for conservative ReviewState verification, not broad autonomous flaw discovery. The issue distribution is missing-ablation heavy, most verified issue rows come from deterministic reviewer seeds rather than Critique payload candidates, and the fresh MiMo rerun completed only 16 of 20 papers before the API account balance was exhausted. Direct quote-grounded negative discovery remains unsolved in the current system.
