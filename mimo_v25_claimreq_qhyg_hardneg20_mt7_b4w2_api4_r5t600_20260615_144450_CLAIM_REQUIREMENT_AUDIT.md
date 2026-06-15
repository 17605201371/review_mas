# Claim Requirement Audit: claimreq_144450 vs qhyg_003753

## Summary
| metric | qhyg_003753 | claimreq_144450 | delta |
|---|---:|---:|---:|
| `claim_requirement_missing_total` | 14 | 13 | -1 |
| `papers_with_requirement_gaps` | 4 | 3 | -1 |
| `primary_claims_with_requirement_gaps` | 10 | 5 | -5 |
| `final_report_claim_gap_visible_papers` | 0 | 20 | 20 |

## Missing Type Counts
| missing type | qhyg_003753 | claimreq_144450 | delta |
|---|---:|---:|---:|
| `insufficient_evaluation` | 1 | 5 | 4 |
| `method_support_gap` | 2 | 0 | -2 |
| `missing_ablation` | 1 | 0 | -1 |
| `missing_baseline` | 8 | 4 | -4 |
| `reproducibility_gap` | 0 | 1 | 1 |
| `scope_overclaim` | 2 | 3 | 1 |

## Candidate Sample Cases
- `uOrfve3prk` / `claim-3`: missing=['empirical_result', 'baseline_or_comparison', 'scope_coverage'] types=['insufficient_evaluation', 'missing_baseline', 'scope_overclaim'] support=[] claim=Logit Lens outperforms other interpretability methods in Intervention Success Rate across all evaluated models.
- `uOrfve3prk` / `claim-2`: missing=['scope_coverage'] types=['scope_overclaim'] support=['evidence-first-support-1-turn-2', 'evidence-small-model-quote-bank-2-turn-2'] claim=The evaluation method uses Intervention Success Rate and normalized edit distance to measure the correctness and intensity of explanations across methods.
- `uOrfve3prk` / `claim-4`: missing=['reproducibility_detail'] types=['reproducibility_gap'] support=[] claim=The hyperparameter α must be tuned per method, model, and intervention feature, making cross-method comparisons of intervention effects difficult without normalization.
- `XyB4VvF01X` / `claim-1`: missing=['empirical_result'] types=['insufficient_evaluation'] support=[] claim=The paper proposes Graph2Tac, a method for learning hierarchical representations of mathematical concepts from formal theory graphs to improve automated theorem proving.
- `XyB4VvF01X` / `claim-3`: missing=['baseline_or_comparison'] types=['missing_baseline'] support=['evidence-first-support-4-turn-6', 'evidence-small-model-quote-bank-5-turn-6'] claim=In evaluation on 2000 Coq theorems, the Graph2Tac model outperforms several strong baselines, including k-NN and text-based transformers, within a 10-minute time limit per theorem.
- `XyB4VvF01X` / `claim-4`: missing=['empirical_result', 'scope_coverage'] types=['insufficient_evaluation', 'scope_overclaim'] support=[] claim=The method's evaluation is limited to theorems randomly sampled from specific Coq packages, which may not represent all theorem proving scenarios or theorem types.
- `cklg91aPGk` / `claim-3`: missing=['empirical_result', 'baseline_or_comparison'] types=['insufficient_evaluation', 'missing_baseline'] support=[] claim=PROPGCL achieves state-of-the-art performance on 4 out of 6 homophily node classification benchmarks.
- `cklg91aPGk` / `claim-4`: missing=['empirical_result', 'baseline_or_comparison'] types=['insufficient_evaluation', 'missing_baseline'] support=[] claim=PROPGCL shows strong performance on heterophily datasets where many traditional GCL methods struggle.

## Interpretation
本审计只统计 auditable real paper claims 的 claim requirement gap；context/fallback/salvage scaffold claim 已排除。缺口表示当前 verified support 没覆盖 claim 所需证据类型，不等同 confirmed paper weakness。
