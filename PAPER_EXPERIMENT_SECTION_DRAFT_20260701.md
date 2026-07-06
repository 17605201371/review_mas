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

We use the hard-negative diagnostic set `hard_negative_20_20260611.parquet`, a 20-paper subset designed to stress negative-evidence and reviewer-issue handling. The main reported evidence is a two-run clean-repeat result using the current issue-bundle verifier, manual audit protocol, and recovery checks:

```text
P32_CLEAN_R1_PRECISION_RECOMPUTE_20260705_232527
P32_CLEAN_R3_PRECISION_RECOMPUTE_20260706_010000
```

Both accepted runs complete all 20 papers and pass the machine and manual gates. Exact raw run identifiers, regeneration commands, manual audit files, and artifact paths are recorded in the reproducibility appendix rather than in the main narrative.

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
- `recovery_harmful_commit_committed`.

### 4.4 Main Result: Verified Review Issue Bundles

Table 1 reports the P32 clean-repeat result. Across two accepted hardneg20 clean runs, DrMAS produces five recurring Critique-origin verified review issue clusters. The recurring clusters are manually judged A/B, have zero manual-D labels, and connect to contested recovery in both runs.

| Metric | Value |
| --- | ---: |
| accepted hardneg20 clean runs | 2 |
| completed papers per run | 20 |
| recurring Critique-origin verified issue clusters | 5 |
| Critique-origin cluster Jaccard mean | 1.000 |
| manual-D total across accepted runs | 0 |
| harmful recovery commits | 0 |
| recurring efficiency-cost-gap clusters | 1 |
| recurring missing-ablation clusters | 2 |
| recurring missing-baseline clusters | 2 |

**Table 1 caption.** Current P32 artifacts show recurring Critique-origin obligation-grounded review issue clusters across accepted hardneg20 clean runs. The main count is the recurring cluster count, not the raw row count from a single run.

The key interpretation is that the useful negative-review signal does not appear as copied paper-negative text. It appears as verified claim-inventory-obligation mismatch. This supports the ReviewState thesis: reviewer issues should be represented as auditable state objects rather than as unstructured negative snippets.

### 4.5 Manual Cluster Audit

Table 2 summarizes the recurring cluster audit. The audit unit is a deduplicated Critique-origin issue cluster that recurs across accepted clean runs, not a raw row. All five recurring clusters are manually judged A/B and connect to contested recovery in both runs.

| Paper | Issue type | Cluster target | Manual label | Recurrence | Contested recovery |
| --- | --- | --- | --- | ---: | ---: |
| fGXyvmWpw6 | efficiency_cost_gap | efficiency_resource_measurement | A | 2/2 | 2/2 |
| GE6iywJtsV | missing_ablation | graph_control_module | A/B | 2/2 | 2/2 |
| HPuLU6q7xq | missing_baseline | paper-named_gpt-4_baseline | B | 2/2 | 2/2 |
| NnExMNiTHw | missing_ablation | acceptance_prediction_head | A/B | 2/2 | 2/2 |
| YXn76HMetm | missing_baseline | paper-named_pixelpick_baseline | B | 2/2 | 2/2 |

**Table 2 caption.** Manual audit separates recurring verified issue clusters from raw verifier rows. We report five recurring A/B Critique-origin clusters as the conservative paper-facing quality count.

The issue distribution is intentionally reported as a limitation: the recurring clusters contain one efficiency-cost gap, two missing-ablation issues, and two missing-baseline issues. This is enough to demonstrate recurring Critique-origin issue-bundle verification, but not enough to claim broad reviewer issue diversity.

### 4.6 Recovery And Safety

Table 3 reports recovery and safety signals for the two accepted clean runs. The main recovery action is `mark_contested`: a supported claim can remain supported while being marked contested by a verified review issue. This is non-destructive state repair, not a decision override.

| Metric | Clean R1 | Clean R3 |
| --- | ---: | ---: |
| completed papers | 20 | 20 |
| machine gate | PASS | PASS |
| manual gate | PASS | PASS |
| manual A/B clusters | 7 | 7 |
| Critique-origin manual A/B clusters | 5 | 5 |
| manual-D clusters | 0 | 0 |
| mark-contested commits | 20 | 16 |
| verified-review-issue repairs | 17 | 14 |
| harmful recovery commits | 0 | 0 |

**Table 3 caption.** Recovery is evaluated as state repair. Verified issues can expose supported-but-contested claims without destructively downgrading claim status. Harmful recovery remains zero in both accepted clean runs.

The recurring clusters also exercise the non-destructive recovery path. Each recurring Critique-origin cluster has per-run `mark_contested` support, so the system can keep a supported claim in the state while exposing a verified issue as a contested relation. This supports the ReviewState-maintenance thesis: recovery is reported as auditable state repair, not as accept/reject correction.

### 4.7 Clean-Repeat Stability

Table 4 summarizes the clean-repeat stability check. The purpose is not to maximize issue count. The purpose is to show that the same Critique-origin issue clusters recur across accepted runs while manual-D and harmful recovery remain zero.

| Stability signal | Value |
| --- | ---: |
| accepted clean runs included | 2/2 |
| accepted-cluster Jaccard | 0.750 |
| Critique-origin cluster Jaccard | 1.000 |
| recurring A/B clusters | 6 |
| recurring Critique-origin A/B clusters | 5 |
| manual-D rate | 0.000 |
| harmful recovery total | 0 |

**Table 4 caption.** Clean-repeat stability is reported at the cluster level. The strongest signal is exact recurrence of the five Critique-origin A/B clusters while manual-D and harmful recovery stay at zero.

### 4.8 Discussion

The strongest current result is not the number of negative quotes. It is the repeated conversion of Critique-origin reviewer concerns into verified obligation-grounded state objects. This is consistent with the main insight: many useful review concerns are not negative sentences in the paper. They are reviewer-inferred obligation gaps that require structured verification.

Across two accepted clean runs, five Critique-origin issue clusters recur exactly and all five have A/B manual labels with contested-recovery support in both runs. This supports a conservative claim: DrMAS can turn reviewer-style concerns into auditable ReviewState objects and connect those objects to non-destructive recovery.

The result is not yet a broad autonomous review benchmark. The recurring issue distribution contains two missing-ablation clusters, two missing-baseline clusters, and one efficiency-cost gap. The appropriate next step is not to loosen the verifier, but to improve entity-level obligation extraction and Critique-driven candidate generation while preserving the same final-view protections.

### 4.9 Limitations

This experiment has five important limitations.

First, hardneg20 is a diagnostic set. It is useful for stress-testing ReviewState hygiene and reviewer issue verification, but it is not enough by itself to support broad benchmark claims.

Second, the issue distribution is narrow. The recurring clusters cover two missing-ablation concerns, two missing-baseline concerns, and one efficiency-cost gap. This supports the issue-bundle mechanism, not comprehensive reviewer issue coverage.

Third, the result is a clean-repeat diagnostic, not full39 generalization. Larger-domain evaluation should come after the ReviewState lifecycle and narrative are stable.

Fourth, the paper does not claim accept/reject accuracy improvement, PPO or RL gains, or broad autonomous flaw discovery. DrMAS is evaluated as review support and audit infrastructure.

Fifth, direct quote-grounded negative evidence remains a separate lane. The present result supports obligation-grounded issue verification and contested recovery; it should not be described as direct quote-grounded negative recall improvement.

### 4.10 Next Evaluation Step

Before treating these results as broad benchmark evidence, the next evaluation step is a larger-domain run such as full39 or additional paper domains. That expansion should happen only after preserving the same strict verifier, manual audit, and recovery gates. Acceptance criteria should include:

- recurring Critique-origin clusters remain inspectable at the cluster level;
- manual-D remains zero or is explicitly audited before paper use;
- harmful recovery remains zero;
- direct quote-grounded negatives stay separate from obligation-grounded issues;
- no accept/reject or PPO/RL claim is introduced without a separate evaluation.

For the current paper draft, the defensible claim is the hardneg20 clean-repeat result, not full39 generalization.

## Drop-In Result Paragraph

On two accepted hardneg20 clean runs, DrMAS produces five recurring Critique-origin obligation-grounded review issue clusters, all manually judged valid or defensible, with manual-D total 0, harmful recovery total 0, and Critique-origin cluster Jaccard 1.000. These clusters are verified through claim anchors, observed paper inventory or quote evidence, concrete missing or mismatched entities, and counterevidence checks. Recovery is non-destructive: each recurring Critique-origin cluster has per-run `mark_contested` support, so verified issues can mark supported claims as contested without downgrading claim status.

## Drop-In Limitation Paragraph

These results should be interpreted as diagnostic evidence for conservative ReviewState maintenance. They do not establish broad benchmark performance, full39 generalization, autonomous accept/reject accuracy, or PPO/RL gains. The direct quote-grounded negative lane remains separate from the obligation-grounded issue path.
