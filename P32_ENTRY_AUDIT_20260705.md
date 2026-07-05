# P32 Entry Audit

Date: 2026-07-05

Status: P31.6-to-P32 transition audit.  This is a stage-level planning and
claim-boundary artifact, not a new experiment.

## Executive Decision

P31.6 is ready to enter P32 clean reproducibility work.

The current hardneg20 evidence is strong enough to say that the
`Critique discovery -> verified issue -> contested relation` path is functional
under strict verification, not just seed-shadow attribution:

- fresh hardneg20 completed 20/20 rows;
- machine entry gate PASS;
- manual entry gate PASS;
- manual audit found 6 A/B clusters, 0 C, 0 D, and 0 unfilled clusters;
- 5 manually accepted A/B clusters are Critique-origin;
- protection and state-hygiene lines remain clean;
- recovery is active through `mark_contested`, with no harmful recovery commit.

This does not yet justify full39, broad benchmark, or accept/reject claims.
P32 should measure reproducibility and stability before any paper table is
rewritten around the new P31.6 numbers.

## Authoritative Evidence

Code baseline:

```text
374b827 Tighten review issue precision after manual audit
```

Fresh run:

```text
run = mimo_v25_negqty_recoverycap_guard3_qhyg_targetneg_freeformrevneg_reviewissuebundle_hardneg20_mt7_b4w2_api4_r8t600_tok2048_20260705_205654
jsonl = mimo_v25_negqty_recoverycap_guard3_qhyg_targetneg_freeformrevneg_reviewissuebundle_hardneg20_mt7_b4w2_api4_r8t600_tok2048_20260705_205654.jsonl
rows = 20
artifacts = P31_6_FRESH_20260705_205654_*
```

Entry gate:

```text
machine_gate_status = PASS
manual_gate_status = PASS
blocking_issues = []
p32_entry_ready = true
```

Headline metrics:

```text
verified_review_issue_count = 10
verified_review_issue_cluster_recomputed_count = 6
quote_duplicate_merged_verified_review_issue_cluster_count = 6
critique_payload_verified_cluster_count = 6
critique_direct_verified_cluster_count = 6
critique_selected_existing_seed_cluster_count = 0
candidate_menu_item_verified_count = 6
candidate_menu_item_failed_count = 8
mark_contested_commit_count = 16
verified_issue_cluster_without_recovery_count = 2
```

Manual audit:

```text
system_clusters = 6
critique_origin_clusters = 5
manual_A_clusters = 2
manual_B_clusters = 4
manual_A_B_clusters = 6
manual_C_clusters = 0
manual_D_clusters = 0
unfilled_clusters = 0
critique_origin_manual_A_B_clusters = 5
deterministic_seed_manual_A_B_clusters = 0
critique_origin_D_clusters = 0
```

Protection lines:

```text
evidence_json_fallback_rate_pct = 0
state_contamination_count = 0
negative_evidence_unlinked_to_flaw = 0
positive_or_neutral_negative_candidate_count = 0
negative_grounding_conflict_count = 0
semantic_negative_without_review_relation_count = 0
recovery_harmful_commit_committed = 0
```

Manual A/B clusters:

| label | paper | type | target | paper-facing use |
| --- | --- | --- | --- | --- |
| A | `XH3OiIhtvf` | `negative_result` | secure aggregator worsens/qualifies EER result | direct quote-grounded negative result; use with EER lower-is-better caution |
| A | `fGXyvmWpw6` | `efficiency_cost_gap` | `efficiency_resource_measurement` | clear resource-measurement support gap for efficiency claims |
| B | `HPuLU6q7xq` | `missing_baseline` | `paper-named_gpt-4_baseline` | defensible missing same-setting GPT-4 reference point; wording must stay scoped |
| B | `NnExMNiTHw` | `missing_ablation` | `acceptance_prediction_head` | defensible missing isolation of a central SpecDec++ head/training choice |
| B | `YXn76HMetm` | `missing_baseline` | `equalal_baseline` | defensible missing comparison to named AL segmentation prior work |
| B | `a6SntIisgg` | `missing_ablation` | `global_encoder` | defensible missing architectural isolation of the global encoder branch |

## What Changed Relative To The P28 Paper Drafts

The current paper-facing documents from 2026-07-01 are conservative P28-era
drafts.  They correctly warned that:

- the fresh live rerun was only partial16;
- Critique-origin recall was weak;
- deterministic seeds dominated the verified issue rows;
- direct quote-grounded negative evidence was 0 in the P28 result.

P31.6 changes the engineering state:

- fresh hardneg20 is now complete at 20/20;
- Critique-origin clusters now pass both machine and manual gates;
- seed-shadow attribution is explicitly blocked by
  `critique_selected_existing_seed_cluster_count = 0`;
- one direct quote-grounded negative-result cluster is validated manually;
- the accepted cluster set is smaller after precision guards, but manual D is 0.

The paper draft should not be rewritten immediately as if stability is proven.
P32 must first test whether the P31.6 result recurs across clean runs.

## Claims Now Defensible

Allowed for internal/P32 planning:

- DrMAS now has a functional strict-verifier path from Critique-selected menu
  candidates into verified review issue clusters.
- On one fresh hardneg20 run, P31.6 produced 6 manually accepted A/B clusters,
  including 5 Critique-origin clusters.
- The accepted clusters cover direct negative result, missing baseline,
  missing ablation, and efficiency/resource-measurement gaps.
- The current chain reaches non-destructive recovery: `mark_contested` commits
  are present and harmful recovery remains 0.
- The strict state-hygiene story survived the new discovery path.

Allowed only with caveats:

- "Critique contributes independent verified issue clusters" is now supported
  for this hardneg20 run, but not yet as a multi-run stability claim.
- "Direct quote-grounded negative evidence exists" is supported for one
  manually accepted cluster, but direct negative discovery is not solved
  broadly.
- "Recovery is functional" is supported by `mark_contested_commit_count = 16`,
  but recovery coverage is not saturated because 2 verified clusters still lack
  recovery.

## Claims Still Forbidden

Do not claim:

- DrMAS is ready for full39.
- DrMAS broadly improves review quality.
- DrMAS improves accept/reject accuracy.
- Critique autonomously discovers most paper flaws in general.
- The direct quote-grounded negative lane is solved.
- The current A/B count is a population-level precision estimate.
- The system handles all issue types with broad diversity.
- Recovery fixes paper decisions.

## P32 Clean Reproducibility Plan

P32 should use the current code behavior, not introduce another verifier
relaxation or prompt-tuning round.

Recommended configuration:

```text
DRMAS_JSON_RESPONSE_FORMAT=on
MAX_TOKENS=2048
API_MAX_WORKERS=4
api_max_retries=8
api_timeout=600
max_turns=7
```

If the API becomes unstable, reduce `API_MAX_WORKERS` to 2.  Do not reduce
`MAX_TOKENS` to 1536 even though the older P32 plan mentioned it; current
project evidence says 2048 is the validated safe setting and 768/shorter
settings risk truncation.

Run plan:

1. Run API preflight and record status before launching P32 run 1.
2. Execute 3 clean hardneg20 runs from the same runtime code baseline.
3. Regenerate dashboard, review issue case table, recovery case table, entry
   gate audit, and manual audit template for each run.
4. Fill A/B/C/D manual labels at the cluster level for every system cluster
   used in P32 reporting.
5. Produce a P32 stability report with:
   - manual strict A/B count mean/std/min/max;
   - D cluster rate;
   - cluster Jaccard overlap;
   - same-paper issue recurrence;
   - same-target entity recurrence;
   - Critique-origin cluster recurrence;
   - deterministic seed cluster recurrence;
   - harmful recovery count across all runs;
   - verified issue recovery coverage.

P32 acceptance:

```text
all runs complete 20/20
all protection gates PASS
evidence_json_fallback_rate_pct < 20%, preferably 0
harmful recovery = 0 across all runs
manual D rate <= 20-25%
manual strict A/B count variance explainable
recurring A/B clusters exist
Critique-origin A/B clusters recur or failure is explicitly diagnosed
```

If P32 fails, return to P31 selector/menu supply or verifier precision work.
Do not jump to full39 and do not loosen validation gates.

## Immediate Next Action

Run API preflight, then launch P32 clean hardneg20 run 1 using the same code
path and `MAX_TOKENS=2048`.  The result should be treated as stability evidence,
not as another opportunity to tune the verifier mid-stream.

