# P32 Paper Narrative Freeze

- status: **PASS**
- source: `P32_NARRATIVE_EVIDENCE_R1_R3_20260706.json`
- empirical scope: two accepted hardneg20 clean runs

## Thesis

DrMAS should be framed as a ReviewState-centered verification and recovery framework for LLM-assisted peer review, not as a free-form review generator, accept/reject classifier, or PPO-trained policy result.

## Headline Numbers

- included clean runs: `2`
- recurring Critique-origin clusters: `5`
- Critique-origin Jaccard mean: `1.000`
- manual-D total: `0`
- harmful recovery total: `0`

## Replacement Snippets

### Abstract Result Sentence

On two accepted hardneg20 clean runs, DrMAS produces 5 recurring Critique-origin obligation-grounded review issue clusters, all manually judged valid or defensible, with manual-D total 0, harmful recovery total 0, and Critique-origin cluster Jaccard 1.000.

### Experiment Result Paragraph

We evaluate the current DrMAS pipeline on 2 accepted hardneg20 clean runs. Across these runs, 5 Critique-origin verified review issue clusters recur exactly.  These clusters are obligation-grounded rather than direct quote-grounded negatives: each is verified through a claim anchor, observed paper inventory or quote evidence, a concrete missing or mismatched entity, and counterevidence checks.  Manual audit labels the recurring clusters as A/B with zero D labels, while harmful recovery remains 0.

### Recovery Paragraph

The recurring clusters also exercise the non-destructive recovery path.  Each recurring Critique-origin cluster has per-run `mark_contested` support, so the system can keep a supported claim in the state while exposing a verified issue as a contested relation.  This supports the ReviewState-maintenance thesis: recovery is reported as auditable state repair, not as accept/reject correction.

### Table Caption

Recurring Critique-origin obligation-grounded review issue clusters across two accepted hardneg20 clean runs.  The table reports deduplicated cluster-level evidence, manual A/B labels, and whether the issue connects to contested recovery in both runs.

### Limitation Paragraph

These results should be interpreted as diagnostic evidence for conservative ReviewState maintenance.  They do not establish broad benchmark performance, full39 generalization, autonomous accept/reject accuracy, or PPO/RL gains.  The direct quote-grounded negative lane remains separate from the obligation-grounded issue path.

## Table-Ready Cluster Summary

| paper | issue type | target | paper-facing issue | labels | recurrence | contested recovery | wording caution |
|---|---|---|---|---|---:|---:|---|
| fgxyvmwpw6 | efficiency_cost_gap | efficiency_resource_measurement | missing resource-cost evidence for the efficiency resource measurement claim | A | 2/2 | 2/2 |  |
| ge6iywjtsv | missing_ablation | graph_control_module | missing component-isolation ablation for graph control module | A, B | 2/2 | 2/2 |  |
| hpulu6q7xq | missing_baseline | paper-named_gpt-4_baseline | missing same-setting named baseline comparison for paper-named gpt-4 baseline | B | 2/2 | 2/2 | Frame as absence of a strong closed-model reference point, not proof that GPT-4 was required or feasible. |
| nnexmnithw | missing_ablation | acceptance_prediction_head | missing component-isolation ablation for acceptance prediction head | A, B | 2/2 | 2/2 |  |
| yxn76hmetm | missing_baseline | paper-named_pixelpick_baseline | missing same-setting named baseline comparison for paper-named pixelpick baseline | B | 2/2 | 2/2 | Frame as missing named AL baseline comparisons under comparable settings, not as absence of all SOTA/ADA baselines. |

## Not Claimed

- full39 generalization
- accept/reject accuracy improvement
- broad autonomous flaw discovery
- PPO or RL performance gain
- direct quote-grounded negative recall improvement

## Next Paper Edit

Replace stale P28/P28.6 result language with the snippets in this artifact, then move run IDs and regeneration commands to the reproducibility appendix.
