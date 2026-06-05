# Meta-Leakage Audit v1

- input: `outputs/results_main/review_infer/mainline_final_v1_closure_9b_fulltest39_20260504_gold.jsonl`
- row_count: **39**
- tier weights: L1=3 (critical) / L2=2 (high) / L3=1 (soft)

**Two scopes are reported separately.** Only the *final_report* scope corresponds to text the human reviewer actually sees; this is the **primary** leakage measurement. The *state_field* scope is a hygiene volume measured inside `review_state.flaw_candidates[]` `title` / `description`, which often contains raw JSON dumps from the fallback flaw extractor but does not necessarily reach the reviewer.

## Scope: final_report (reviewer-visible — PRIMARY)

Hits inside the `final_report` string. These tokens are visible to a human reviewer and are the strict measurement of meta-leakage for the paper's *State Hygiene* claim.

- rows_with_any_leak: **39** (rate = 1.0000)
- rows_with_L1_leak: **39** (rate = 1.0000)
- rows_with_L2_leak: **14** (rate = 0.3590)
- raw_total_hits: **338**
- leakage_score_weighted_total: **725** (L1×3 + L2×2 + L3×1)
- mean_score_per_paper: 18.5897

### Tier breakdown

| tier | weight | hits |
|---|---:|---:|
| **L1** | 3 | 185 |
| **L2** | 2 | 17 |
| **L3** | 1 | 136 |

### Probe breakdown

| probe | tier | hits |
|---|---|---:|
| `inline_schema_id_dump` | L1 | 102 |
| `snake_case_decision_enum` | L1 | 78 |
| `review_halted` | L1 | 2 |
| `full_text_unavailable` | L1 | 2 |
| `missing_input_data` | L1 | 1 |
| `context_truncation_generic` | L2 | 13 |
| `text_truncation_prevents` | L2 | 3 |
| `abstract_truncated` | L2 | 1 |
| `by_end_of_review_process` | L3 | 36 |
| `not_fully_resolved_phrase` | L3 | 36 |
| `reviewer_agent_word` | L3 | 36 |
| `fallback_evidence_word` | L3 | 28 |

## Scope: state_field (internal hygiene volume — secondary)

Hits inside `review_state.flaw_candidates[].title|description` only. These reveal fallback-flaw extractor regressions (raw JSON dumps stored as flaw title) but do not directly expose the human reviewer.

- rows_with_any_leak: **32** (rate = 0.8205)
- rows_with_L1_leak: **25** (rate = 0.6410)
- rows_with_L2_leak: **10** (rate = 0.2564)
- raw_total_hits: **115**
- leakage_score_weighted_total: **330** (L1×3 + L2×2 + L3×1)
- mean_score_per_paper: 8.4615

### Tier breakdown

| tier | weight | hits |
|---|---:|---:|
| **L1** | 3 | 100 |
| **L2** | 2 | 15 |
| **L3** | 1 | 0 |

### Probe breakdown

| probe | tier | hits |
|---|---|---:|
| `json_schema_key_literal` | L1 | 100 |
| `context_truncation_generic` | L2 | 12 |
| `text_truncation_prevents` | L2 | 3 |

## Top 10 papers by final_report weighted_score

| paper_id | weighted | raw | L1 | L2 | L3 | state_raw | state_weighted |
|---|---:|---:|---:|---:|---:|---:|---:|
| `ye3NrNrYOY` | 36 | 15 | 10 | 1 | 4 | 5 | 14 |
| `uOrfve3prk` | 25 | 11 | 7 | 0 | 4 | 4 | 12 |
| `QAAsnSRwgu` | 25 | 12 | 5 | 3 | 4 | 4 | 12 |
| `QAgwFiIY4p` | 25 | 11 | 7 | 0 | 4 | 4 | 12 |
| `xUe1YqEgd6` | 25 | 11 | 7 | 0 | 4 | 4 | 12 |
| `WLgbjzKJkk` | 25 | 11 | 7 | 0 | 4 | 4 | 12 |
| `a6SntIisgg` | 24 | 11 | 6 | 1 | 4 | 3 | 6 |
| `TPAj63ax4Y` | 23 | 11 | 5 | 2 | 4 | 0 | 0 |
| `WNxlJJIEVj` | 22 | 10 | 6 | 0 | 4 | 0 | 0 |
| `X41c4uB4k0` | 22 | 10 | 6 | 0 | 4 | 4 | 12 |

## Final-report sample excerpts (top 3 worst, final_report scope)

### `ye3NrNrYOY` (final_report weighted_score=36)

- **inline_schema_id_dump** (L1):
  - _...but this is not a global novelty proof. [claims: claim-1, claim-2; evidence: evidence-2-turn-2] - Significance / Con..._
  - _...support rather than fallback evidence. [claims: claim-1, claim-2; evidence: evidence-1-turn-2, evidence-2-turn-2] -..._
- **snake_case_decision_enum** (L1):
  - _...ine_insufficient Recommendation Reason: some_real_support_but_not_enough_quality_or_coverage_for_accept_like  1. Summary of Reviews Review halted due to missing input d..._
  - _...endation view: borderline_insufficient (some_real_support_but_not_enough_quality_or_coverage_for_accept_like). Final-view diagnostics: open evidence gaps=1, stale evide..._
- **review_halted** (L1):
  - _..._for_accept_like  1. Summary of Reviews Review halted due to missing input data. The abstract is truncated, and t..._
- **missing_input_data** (L1):
  - _...Summary of Reviews Review halted due to missing input data. The abstract is truncated, and the full text is unavailabl..._
- **full_text_unavailable** (L1):
  - _...ata. The abstract is truncated, and the full text is unavailable, preventing verification of claims and extraction of eviden..._
- **abstract_truncated** (L2):
  - _...w halted due to missing input data. The abstract is truncated, and the full text is unavailable, preventing verificatio..._
- **by_end_of_review_process** (L3):
  - _...tant weaknesses were not fully resolved by the end of the review process.  4. Criterion Assessment - Novelty / Originality: positive..._
- **not_fully_resolved_phrase** (L3):
  - _...Weaknesses - Important weaknesses were not fully resolved by the end of the review process.  4. Criterion Assessment..._
- **fallback_evidence_word** (L3):
  - _...based on real-claim support rather than fallback evidence. [claims: claim-1, claim-2; evidence: evidence-1-turn-2, ev..._
- **reviewer_agent_word** (L3):
  - _...re not fully resolved by the end of the review process.  4. Criterion Assessment - Novelty / Originality: positive..._

### `uOrfve3prk` (final_report weighted_score=25)

- **inline_schema_id_dump** (L1):
  - _...but this is not a global novelty proof. [claims: claim-1, claim-2; evidence: evidence-2-turn-2] - Significance / Con..._
  - _...support rather than fallback evidence. [claims: claim-1, claim-2; evidence: evidence-1-turn-2, evidence-2-turn-2] -..._
- **snake_case_decision_enum** (L1):
  - _...ine_insufficient Recommendation Reason: some_real_support_but_not_enough_quality_or_coverage_for_accept_like  1. Summary of Reviews Fallback critique extraction was use..._
  - _...endation view: borderline_insufficient (some_real_support_but_not_enough_quality_or_coverage_for_accept_like). Final-view diagnostics: open evidence gaps=1, stale evide..._
- **by_end_of_review_process** (L3):
  - _...tant weaknesses were not fully resolved by the end of the review process.  4. Criterion Assessment - Novelty / Originality: positive..._
- **not_fully_resolved_phrase** (L3):
  - _...Weaknesses - Important weaknesses were not fully resolved by the end of the review process.  4. Criterion Assessment..._
- **fallback_evidence_word** (L3):
  - _...based on real-claim support rather than fallback evidence. [claims: claim-1, claim-2; evidence: evidence-1-turn-2, ev..._
- **reviewer_agent_word** (L3):
  - _...re not fully resolved by the end of the review process.  4. Criterion Assessment - Novelty / Originality: positive..._

### `QAAsnSRwgu` (final_report weighted_score=25)

- **inline_schema_id_dump** (L1):
  - _...support rather than fallback evidence. [claims: claim-1, claim-2, claim-3; evidence: evidence-1-turn-2] - Technical..._
  - _...r at least part of the empirical story. [claims: claim-2; evidence: evidence-1-turn-2] - Clarity / Reproducibility:..._
- **snake_case_decision_enum** (L1):
  - _...ine_insufficient Recommendation Reason: some_real_support_but_not_enough_quality_or_coverage_for_accept_like  1. Summary of Reviews Fallback critique extraction was use..._
  - _...endation view: borderline_insufficient (some_real_support_but_not_enough_quality_or_coverage_for_accept_like). Final-view diagnostics: open evidence gaps=2, stale evide..._
- **context_truncation_generic** (L2):
  - _..., benchmark metrics, and inference code snippets. The planning approach combines LLM reasoning with formal..._
  - _..., benchmark metrics, and inference code snippets.. - Supporting evidence is reported in figure: Figure 1 sh..._
- **by_end_of_review_process** (L3):
  - _...tant weaknesses were not fully resolved by the end of the review process.  4. Criterion Assessment - Novelty / Originality: not_asse..._
- **not_fully_resolved_phrase** (L3):
  - _...Weaknesses - Important weaknesses were not fully resolved by the end of the review process.  4. Criterion Assessment..._
- **fallback_evidence_word** (L3):
  - _...based on real-claim support rather than fallback evidence. [claims: claim-1, claim-2, claim-3; evidence: evidence-1-t..._
- **reviewer_agent_word** (L3):
  - _...re not fully resolved by the end of the review process.  4. Criterion Assessment - Novelty / Originality: not_asse..._

## State-field sample excerpts (worst paper, state_field scope)

### `9zEBK3E9bX` (state_field weighted_score=16)

- **json_schema_key_literal** (L1):
  - _[flaw_candidates.flaw-fallback-1.title] ...{ "flaw_candidates": [ { "flaw_id": "flaw-1", "title": "Critical Data Truncatio..._
  - _[flaw_candidates.flaw-fallback-1.title] ...{ "flaw_candidates": [ { "flaw_id": "flaw-1", "title": "Critical Data Truncation Prevents Vali..._
- **text_truncation_prevents** (L2):
  - _[flaw_candidates.flaw-fallback-1.title] ..._id": "flaw-1", "title": "Critical Data Truncation Prevents Validity Assessment", "descrip..._
  - _[flaw_candidates.flaw-fallback-1.description] ..._id": "flaw-1", "title": "Critical Data Truncation Prevents Validity Assessment", "description": "The provided paper te..._

## How to interpret

- The **final_report scope** is the strict measurement: every hit is text that a human reviewer would actually read. The dominant L1 contributors here are `inline_schema_id_dump` (e.g. `[claims: claim-1; evidence: evidence-2-turn-2]`) and `snake_case_decision_enum` (e.g. `some_real_support_but_not_enough_quality_or_coverage_for_accept_like` copied from the recommendation enum). Both come from the final-report writer prompt rendering internal schema tokens verbatim.
- The **state_field scope** is a separate hygiene volume. The fallback flaw extractor on some papers stores the raw JSON envelope (e.g. `{ "flaw_candidates": [ { "flaw_id": "flaw-1", ...} ] }`) inside the flaw `title` / `description` fields. This is invisible to a reviewer reading the final report, but it is a real hygiene regression that should be reported alongside the State Hygiene narrative.
- L2 hits surface context-window or truncation language in natural prose (`abstract is truncated`, `text truncation prevents`). They are factually accurate but reveal a coverage limit the paper should disclose explicitly rather than emit silently.
- L3 hits are boilerplate (`by the end of the review process`, `not fully resolved`, `fallback evidence`). They are the easiest to clean up at the report-writer prompt level.
- The `total_meta_leakage` field consumed by `analyze_mainline_final_v1.py:346` is filled when this script is invoked with `--write-back-criterion`; the value written is the **final_report scope raw_total** (the strict reviewer-visible volume).

Generated by `scripts/audit_meta_leakage_v1.py`.
