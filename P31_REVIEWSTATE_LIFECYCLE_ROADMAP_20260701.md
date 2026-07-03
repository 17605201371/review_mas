# P31 ReviewState Lifecycle Roadmap

Date: 2026-07-01

This document is the working plan after the P30 fresh full20 checkpoint. It combines the P30/P31 code audit with the longer-term project direction. The goal is not to maximize the number of verified rows. The goal is to make review issue discovery, verification, clustering, manual audit, and non-destructive recovery stable enough to support the paper narrative.

## North Star

Build an evidence-grounded, stateful, auditable, and recoverable review-assistance system that can maintain a paper's ReviewState across:

```text
claim extraction
-> support and neutral inventory grounding
-> reviewer issue candidate discovery
-> counterevidence-first bundle verification
-> cluster deduplication
-> manual A/B/C/D audit
-> non-destructive recovery
-> paper-facing report
```

The system should not be framed as an autonomous reviewer, an accept/reject classifier, or a free-form defect generator. The paper-facing claim is that structured ReviewState maintenance makes LLM-assisted review more auditable and safer.

## Current Checkpoint

Authoritative current run:

- Raw: `mimo_v25_negqty_recoverycap_guard3_qhyg_targetneg_freeformrevneg_reviewissuebundle_hardneg20_mt7_b4w2_api4_r8t600_tok1536_20260702_105402.jsonl`
- Dashboard: `P31_2_FRESH_API4_105402_HARDNEG20_DASHBOARD.md/json`
- Review issue case table: `P31_2_FRESH_API4_105402_REVIEW_ISSUE_CASE_TABLE.md/json`
- Recovery case table: `P31_2_FRESH_API4_105402_RECOVERY_CASE_TABLE.md/json`

P31.2 fresh full20 facts:

- Full hardneg20 completed: 20/20 papers.
- Protection PASS.
- `recovery_harmful_commit_committed=0`.
- `negative_evidence_unlinked_to_flaw=0`.
- `positive_or_neutral_negative_candidate_count=0`.
- `negative_grounding_conflict_count=0`.
- Evidence JSON reliability is clean: `evidence_json_valid_turns=62`, `evidence_json_fallback_turns=0`, `evidence_json_fallback_rate_pct=0`.
- Prompt/runtime compaction is validated in the live API path: `critique_prompt_chars_median=11668`, `critique_prompt_chars_max=11673`, `critique_prompt_over_15k_turns=0`, `critique_prompt_over_30k_turns=0`.
- Direct quote-grounded negative lane remains strict: `review_negative_verified_count=1`.
- Obligation-grounded issue lane: `verified_review_issue_count=12`, `verified_review_issue_cluster_count=10`.
- Recovery bridge is safe but incomplete: `mark_contested_commit_count=5`, with 4 verified review issue repairs and 1 direct verified negative repair.
- Critique menu uptake exists but does not yet verify: `review_issue_candidate_critique_payload_count=19`, `candidate_menu_item_used_count=7`, `candidate_menu_item_verified_count=0`, `critique_payload_verified_cluster_count=1`.
- Discovery is still seed-dominated: `deterministic_seed_verified_cluster_count=8`.
- Initial case-table manual audit: `P31_2_FRESH_API4_105402_MANUAL_CLUSTER_AUDIT_20260702.md/json`; 12 rows / 10 clusters become about 5 A/B clusters (`A=2`, `B=3`, `C=3`, `D=2`) before full-paper audit.
- Selector failure audit: `P31_3_SELECTOR_FAILURE_AUDIT_20260702.md`; 7 menu-used candidates produced 0 verified menu-bound clusters mainly because prompt-time menu ids are not stable after recomputed lookup, fuzzy fallback can bind the wrong menu item, and several menu items request evidence already present in inventory.
- P31.3 first selector-rebinding patch is implemented and focused-tested: exact menu-id misses no longer fuzzy-bind, copied menu ids are preserved as prompt-time metadata, and colliding obligation ids cannot inject unrelated targets through generic token overlap.

Interpretation:

- P31.2 is a runtime/prompt/protection success.
- P31.2 is not yet a Critique-discovery success: the target `critique_payload_verified_cluster_count >= 3` was not met.
- Do not proceed to P32 as if autonomous Critique discovery is solved. The next implementation focus is P31.3: stable menu metadata, exact-id-safe rebinding, already-satisfied menu filtering, and regression guards for the two D-class cluster types found in the manual audit.

P31.3 update, 2026-07-02:

- Superseding raw: `mimo_v25_negqty_recoverycap_guard3_qhyg_targetneg_freeformrevneg_reviewissuebundle_hardneg20_mt7_b4w2_api4_r8t600_tok1536_20260702_131007.jsonl`.
- Dashboard: `P31_3_FRESH_API4_131007_HARDNEG20_DASHBOARD.md/json`.
- Review issue case table: `P31_3_FRESH_API4_131007_REVIEW_ISSUE_CASE_TABLE.md/json`.
- Recovery case table: `P31_3_FRESH_API4_131007_RECOVERY_CASE_TABLE.md/json`.
- Result audit: `P31_3_FRESH_API4_131007_RESULT_AUDIT_20260702.md`.
- Manual cluster audit: `P31_3_FRESH_API4_131007_MANUAL_CLUSTER_AUDIT_20260702.md/json`.
- Selector menu failure audit: `P31_4_SELECTOR_MENU_FAILURE_AUDIT_20260702.md`.

P31.3 fresh full20 facts:

- Completed 20/20 after capping regex-heavy full-text scan paths that previously stalled the `20260702_124240` attempt at 8/20.
- Protection PASS: `negative_evidence_unlinked_to_flaw=0`, `positive_or_neutral_negative_candidate_count=0`, `negative_grounding_conflict_count=0`, `recovery_harmful_commit_committed=0`.
- Evidence JSON reliability remains clean: `evidence_json_valid_turns=63`, `evidence_json_fallback_turns=0`, `evidence_json_fallback_rate_pct=0`.
- Direct quote-grounded negative lane remains strict and empty: `review_negative_verified_count=0`.
- Obligation-grounded issue lane: `verified_review_issue_count=14`, `verified_review_issue_cluster_count=11`, `duplicate_review_issue_row_count=3`.
- Critique selector improved but is still below target: `critique_payload_verified_cluster_count=2`, `candidate_menu_item_used_count=6`, `candidate_menu_item_verified_count=1`.
- Discovery remains seed-dominated: `verified_review_issue_cluster_origin_critique_payload_count=2`, `verified_review_issue_cluster_origin_deterministic_seed_count=8`, `verified_review_issue_cluster_origin_claim_obligation_fallback_count=3`.
- Recovery bridge remains safe: `mark_contested_commit_count=8`, with `recovery_case_verified_review_issue_repair=6`.
- Initial cluster audit gives `A=1`, `B=4`, `C=3`, `D=3`; paper-facing A/B clusters are about 5, below the P31 validation target of 6.

P31.3 decision:

- P31.3 is a progress checkpoint, not a completion checkpoint.
- Do not proceed to P32 reproducibility as if Critique selector integration is solved.
- Next batch should be P31.4 selector-quality work. The first failure audit is now `P31_4_SELECTOR_MENU_FAILURE_AUDIT_20260702.md`: the 6 menu-used candidates produced only 1 verified case mainly because generic OOD/stress, broad scalability-to-cost, generic strong-baseline, theory-reproducibility, and qualitative-vs-quantitative result-table targets are not yet cleanly typed or rejected with candidate-level reasons.
- P31.4 implementation checkpoint 1 is now in the working tree: failed-menu candidate telemetry is recorded in `decision_hygiene`, dashboard aggregation exposes failed-menu counts/reasons, and selector/menu guards block generic OOD/stress, broad scalability-to-cost, generic strong-baseline, theory-reproducibility, already-studied ablation, contrast-as-module, and global-encoder-already-ablation-covered patterns. Uncached current-code recompute on old `131007` raw states gives 8 rows / 6 clusters with 5 explicit failed-menu candidates; this is precision control and not a fresh API result.
- P31.4 checkpoint 2 adds safe named-baseline normalization from Critique verification questions / counterevidence terms and records `qualitative_vs_quantitative_result_gap_unsupported_type` as an explicit failed-menu reason. This keeps qualitative-vs-quantitative result-table concerns diagnosis-pending rather than adding a new negative type in this batch. Current-code recompute on old `131007` still gives 8 rows / 6 clusters; the old `KOUAayk5Kx` menu candidate remains `not_verified_by_bundle`, so deeper per-candidate bundle stop-stage telemetry is the next useful diagnostic.
- P31.4 checkpoint 3 adds that stop-stage telemetry. Bundle construction now writes rejection reason/stage back to reviewer-candidate gaps, `decision_hygiene` exposes `review_issue_candidate_bundle_failures`, and failed selected-menu candidates use the true bundle failure detail instead of opaque `not_verified_by_bundle`. Uncached current-code recompute on old `131007` gives 8 rows / 6 clusters, protection PASS, `candidate_menu_item_failed_count=5`, `candidate_menu_item_failed_by_stage={menu_quality_guard:4,counterevidence:1}`, and `candidate_menu_item_failed_not_verified_by_bundle=0`. The old remaining KOUA-style case is now diagnosed as `missing_entity_already_observed_in_inventory`, i.e. counterevidence/inventory coverage rather than a verifier black box.
- P31.4 checkpoint 4 adds a narrow qualitative-vs-quantitative result-gap lane by reusing existing `result_claim_mismatch`, not by adding a broad new negative type. Candidates that ask for a direct quantitative same-setting result table are remapped only when they name a concrete target and still must pass claim anchor, inventory anchor, and full-text counterevidence. On old `131007`, the xUe DAVIS2017-motion candidate is now typed correctly but remains rejected because the paper has Table 3 quantitative DAVIS2017-motion results; this is the desired counterevidence behavior. Recompute `P31_4_QUALRESULT_RECOMPUTE_131007_*` remains 8 rows / 6 clusters, protection PASS, and reports `candidate_menu_item_failed_full_text_protocol_or_result_counterevidence=1`.
- P31.4 checkpoint 5 starts selector-quality improvement for the next fresh run: `_select_review_issue_candidate_menu_items` is now slot-diverse, taking the best item from distinct review slots before top-up, and the Critique-visible selector menu budget is raised from 4 to 6. This is discovery-input improvement, not verifier relaxation. Existing old-raw dashboard metrics remain unchanged (`P31_4_SELECTORDIVERSE_RECOMPUTE_131007_*`: 8 rows / 6 clusters, protection PASS) because raw model outputs are already fixed; the expected effect must be measured on the next fresh API run.
- P31.4 checkpoint 6 adds an explicit lightweight menu-decision path. `REVIEW_ISSUE_DISCOVERY_PROMPT` now allows `selected_menu_items` / `rejected_menu_items`; `normalize_review_update_payload` preserves these decisions; and `review_runner` expands selected visible menu ids back into pending verifier-ready reviewer candidates before deterministic seed top-up. This is a recovery/parse improvement for Critique menu selection, not evidence formation: expanded candidates still run through the same bundle verifier. Dashboard now reports `review_issue_selected_menu_recovery_turns` and `review_issue_selected_menu_recovered_count`. Old-raw recompute `P31_4_MENUDECISION_RECOMPUTE_131007_*` remains 8 rows / 6 clusters, protection PASS, with both new selected-menu recovery counters at 0 because the old raw output did not contain the new fields.

## Operating Principles

- Optimize manual A/B cluster quality, recovery safety, and reproducibility before raw row count.
- Keep direct quote-grounded negative evidence strict; do not force `review_negative_verified_count` upward.
- Treat deterministic seeds as verifier stress/top-up targets, not autonomous discovery evidence.
- Report row count and cluster count separately.
- Use manual A/B/C/D cluster audit for paper-facing precision claims.
- Never relax counterevidence, target-quality, author-limitation, retrieval-gap, or fallback/context claim guards to increase count.
- Keep recovery non-destructive: mark supported claims as contested instead of downgrading claim status.

## P31: Critique Payload Integration

Objective:

Turn Critique from free-form prose candidate generation into verifier-ready candidate selection and light refinement.

Target outcomes on hardneg20:

- `critique_payload_verified_cluster_count >= 3`.
- `critique_payload_A_B_precision >= 60%` after manual cluster audit.
- Deterministic seed and Critique payload origins are reported separately.
- Protection remains PASS, including `recovery_harmful_commit_committed=0`.

### P31.1 Add Verifier-Ready Candidate Menus

Add a `review_issue_candidate_menu_for_claim` view shown to Critique. Each item should be non-evidence and contain:

```json
{
  "candidate_menu_id": "menu-claim-2-missing-ablation-acceptance-head",
  "claim_id": "claim-2",
  "obligation_id": "obligation-claim-2-missing-ablation-acceptance-head",
  "issue_type": "missing_ablation",
  "required_evidence_type": "ablation_or_component",
  "expected_entity": "acceptance prediction head",
  "entity_source": "method_component",
  "inventory_id": "paper-inventory-7",
  "inventory_quote": "copied table/list/experiment anchor",
  "inventory_locator": "Table 4",
  "inventory_type": "ablation",
  "target_quality_hint": "high|medium|reject",
  "counterevidence_search_terms": ["acceptance head", "prediction head", "ablation"]
}
```

Rules:

- Menu items are hypothesis targets, not evidence.
- Each menu item must have a locatable inventory quote/list/table anchor or a trusted verified support inventory anchor.
- Menu items should be generated from the same obligation/inventory substrate currently used by deterministic seeds.
- Generic entities such as `component`, `module`, `encoder`, `decoder`, `model`, `network`, `protocol details`, or `stronger baseline` must not be menu items unless explicitly contribution-bound and target-quality checked.

### P31.2 Update Critique Prompt Contract

Update `REVIEW_ISSUE_DISCOVERY_PROMPT` so Critique preferentially selects from the candidate menu.

Candidate output should include:

```json
{
  "candidate_id": "review-issue-candidate-1",
  "candidate_menu_id": "menu-claim-2-missing-ablation-acceptance-head",
  "obligation_id": "obligation-claim-2-missing-ablation-acceptance-head",
  "claim_id": "claim-2",
  "issue_type": "missing_ablation",
  "required_evidence_type": "ablation_or_component",
  "missing_or_weak_items": ["acceptance prediction head"],
  "observed_inventory": [
    {
      "inventory_id": "paper-inventory-7",
      "quote": "copied table/list/experiment anchor",
      "locator": "Table 4",
      "observed_items": ["threshold h", "candidate length 20"]
    }
  ],
  "possible_counterevidence_terms": ["acceptance head", "prediction head", "ablation"],
  "why_not_covered_by_inventory": "short hypothesis, not proof",
  "status": "pending_absence_audit"
}
```

Prompt rules:

- Prefer selecting or lightly rewriting a menu item.
- Free-form candidates are allowed only when they provide a concrete entity and locatable observed inventory anchor.
- Critique must propose possible counterevidence terms for each candidate.
- Critique must not frame issues as missing from the provided excerpt/current context/current inventory.
- Critique must leave unsafe slots empty.

### P31.3 Candidate-To-Menu Rebinding

Add rebinding in `_reviewer_candidate_absence_gap_items`:

```text
IF candidate has candidate_menu_id
OR candidate matches a menu item by claim_id + issue_type + expected_entity tokens
THEN copy menu requirement, expected_entity, inventory anchor, and obligation_id
AND set discovery_origin = critique_payload_menu_bound
AND run the same strict bundle verifier
```

This should not bypass:

- claim anchor locatability
- observed inventory verification
- target-quality guard
- full-text counterevidence
- review-worthiness guard
- author limitation / retrieval-gap guards

### P31.4 Safe Introduced-Requirement Path

Current P30 failure mode:

- Critique proposes reasonable narrower issues.
- The broad requirement is already marked satisfied by some support.
- Candidate dies as `no_selected_requirement`.

P31 change:

- For baseline, ablation, scope/robustness, protocol, and reproducibility candidates, allow bundle verification even when the broad requirement is satisfied, but only when:
  - candidate is real-claim-bound;
  - candidate has concrete missing/mismatch entity;
  - candidate has locatable observed inventory;
  - expectation is auditable from paper surface, claim surface, or menu item;
  - full-text counterevidence does not resolve it.

This is an entry-path widening, not verifier relaxation.

### P31.5 Origin-Split Funnel Metrics

Add dashboard and case-table fields:

```text
critique_payload_candidate_count
critique_payload_gap_count
critique_payload_menu_bound_count
critique_payload_bundle_built_count
critique_payload_verified_count
critique_payload_verified_cluster_count
critique_payload_rejected_by_reason
deterministic_seed_candidate_count
deterministic_seed_verified_cluster_count
candidate_menu_item_count
candidate_menu_item_used_count
candidate_menu_item_verified_count
```

Case table should show:

```text
discovery_origin
candidate_menu_id
obligation_id
expected_entity
inventory_anchor_type
counterevidence_reason
review_worthiness_reason
manual_label
manual_label_reason
```

### P31.6 Safety Fixes To Bundle With P31

Fix the known recovery and verifier risks:

- Recovery downgrade-to-contested should collect cited ids from `supporting_evidence_ids`, `negative_evidence_ids`, and `evidence_ids`, not only `supporting_evidence_ids`.
- Reject generic protocol missing items such as `explicit evaluation protocol details for protocol`.
- Treat explicit train/test split, label-budget, training setup, or same-setting protocol quotes as counterevidence for generic protocol issues.
- Reject malformed missing-ablation targets such as `ranch_encoder`.
- Keep plain `global encoder` out of verified issues unless explicitly contribution-bound and inventory-bound.

## P31 Validation

Unit tests:

- Critique candidate with `candidate_menu_id` binds to menu obligation and inventory.
- Menu-bound Critique candidate can verify only when the strict bundle verifier passes.
- Free-form Critique candidate without locatable inventory remains diagnosis-pending.
- A candidate whose broad requirement is satisfied can still enter verification when it names a narrower inventory-grounded issue.
- Counterevidence still blocks stale or already-covered issues.
- Generic protocol target is rejected.
- Malformed ablation target is rejected.
- Recovery rebuilds destructive downgrade patches into `mark_contested` when issue/evidence ids appear in any supported id field.

Offline recompute first:

```text
source raw: P30 fresh full20 20260701_211251
expected: protection PASS
expected: critique_payload_gap_count > 0
expected: critique_payload_verified_cluster_count improves from 0
expected: no increase in D-class obvious false positives
```

Fresh MiMo full20 rerun after offline sanity:

```text
max_turns=7
api_max_workers=4
api_max_retries=8
api_timeout=600
max_tokens=1536
```

Acceptance:

```text
protection PASS
recovery_harmful_commit_committed = 0
negative_evidence_unlinked_to_flaw = 0
positive_or_neutral_negative_candidate_count = 0
negative_grounding_conflict_count = 0
critique_payload_verified_cluster_count >= 3
manual strict A/B clusters >= 6
D clusters <= 3 if possible; every D gets a regression note
```

## P31.5: Manual Audit Checkpoint

Objective:

Freeze a reusable manual audit protocol and produce a clean P30/P31 manual cluster audit artifact.

Artifacts:

- `P31_MANUAL_CLUSTER_AUDIT_YYYYMMDD.md`
- `P31_MANUAL_CLUSTER_AUDIT_YYYYMMDD.json`

Audit unit:

- Deduplicated issue cluster, not raw row.

Labels:

- `A`: strong real review issue, paper-facing.
- `B`: defensible concern, usable with caveat.
- `C`: weak or diagnosis-pending; do not headline as verified defect.
- `D`: false positive or not review-worthy; must create regression target if recurring.
- `MERGE`: duplicate cluster merged into another cluster.

Targets:

```text
hardneg20 strict A/B clusters >= 6
D clusters <= 3
all D labels have explicit reason
all D reasons mapped to code/prompt/dashboard follow-up
```

## P32: Reproducibility Runs

Objective:

Stop relying on one clean full20 run. Measure stability.

Run plan:

```text
3 clean hardneg20 runs
same code commit
code_dirty = clean
MiMo API4 unless API instability requires fallback
same dashboard/case/recovery/manual-audit pipeline
```

Metrics:

```text
manual strict A/B cluster count mean/std/min/max
D cluster rate
cluster Jaccard overlap
same-paper issue recurrence
same target entity recurrence
critique_payload cluster recurrence
harmful recovery count across all runs
```

Acceptance:

```text
harmful recovery = 0 across all runs
D rate <= 20-25%
manual strict A/B count stable enough to report
at least some recurring A/B clusters across runs
```

## P33: Full39 Evaluation

Objective:

Move from hardneg20 diagnostic set to broader paper-facing evaluation.

Prerequisites:

- P31 Critique integration has at least some verified Critique-origin clusters.
- P31/P32 protection lines pass.
- Manual audit protocol is stable.
- D-class regression guards are in place.

Full39 targets:

```text
manual strict A/B clusters >= 12-15
permissive A/B clusters >= 16-20
D rate <= 20%
non-ablation A/B clusters >= 30%
recovery_harmful_commit_committed = 0
negative_evidence_unlinked_to_flaw = 0
positive_or_neutral_negative_candidate_count = 0
```

Important:

- Do not hide direct quote-negative count if it remains zero.
- Present direct quote-grounded negative and obligation-grounded review issue as separate lanes.
- Report seed-origin and Critique-origin clusters separately.

## P34: Paper-Ready Benchmark

Objective:

Convert the system from development checkpoint to paper-ready benchmark.

Needed components:

- Manual annotated issue cluster dataset.
- Baseline comparisons.
- System ablations.
- Multi-run stability.
- Case studies.
- Recovery safety analysis.

Candidate baselines:

```text
single-agent free-form review generation
multi-agent without ReviewState
ReviewState without counterevidence guard
ReviewState without cluster guard
ReviewState without non-destructive recovery
deterministic-seed-only
Critique-payload-only
```

Main questions:

- Does ReviewState improve auditability?
- Does counterevidence-first verification improve precision?
- Does non-destructive recovery preserve useful conflicts without damaging supported claims?
- Does Critique payload discovery add reviewer-worthy issues beyond deterministic verifier stress targets?

## Paper Narrative Guardrails

Allowed claims:

- The system separates direct quote-grounded negatives from obligation-grounded review issues.
- The system verifies non-quote review issues through claim anchors, observed inventory, concrete missing/mismatch entities, and counterevidence checks.
- The system preserves positive support while adding contested relations for verified issues.
- P30/P31 style runs demonstrate clean recovery safety when guards are active.

Forbidden claims:

- Do not claim the system is an autonomous reviewer.
- Do not claim row counts are true independent defects.
- Do not claim broad autonomous defect discovery while deterministic seeds dominate.
- Do not claim `review_negative_verified_count=0` is a success metric; it is a caveat showing the strict direct quote lane.
- Do not claim reviewer issue count improvements without manual A/B cluster audit.

Preferred wording:

```text
DrMAS verifies reviewer-worthy issue bundles rather than merely generating review prose. It distinguishes copied quote-grounded negatives from obligation-grounded claim/inventory mismatches, filters candidates through counterevidence-first guards, clusters issue rows into auditable units, and uses non-destructive recovery to preserve supported-but-contested claims.
```

## Immediate Next Action

Recommended next implementation batch:

```text
1. Add deeper per-candidate bundle stop-stage telemetry for menu candidates that reach `not_verified_by_bundle`.
2. Use that telemetry to decide whether the remaining named-baseline case is blocked by expectation basis, counterevidence, inventory relevance, or materialization.
3. Rerun one clean hardneg20 MiMo API4 full20 only after the stop-stage telemetry is available and the current precision guards are stable.
4. Generate dashboard, review issue case table, recovery table, and manual cluster audit.
```

Decision point after P31:

```text
IF critique_payload_verified_cluster_count >= 3
AND protection PASS
AND manual A/B quality does not regress
THEN proceed to P32 reproducibility runs.

IF Critique payload remains below 3 verified clusters
THEN do not chase quantity. Continue selector-quality work or treat deterministic seed verifier as the current system capability and frame Critique discovery as future work.
```

## Implementation Checkpoint 2026-07-01

Current working-tree status against P31:

- Done: verifier-ready `review_issue_candidate_menu` is exposed on review issue discovery targets.
- Done: Critique prompt contract now instructs models to select/copy menu items and return `candidate_menu_id`, `obligation_id`, inventory anchors, and counterevidence terms.
- Done: reviewer issue candidate normalization preserves `candidate_menu_id`, `review_issue_slot`, `entity_source`, `discovery_origin`, and `possible_counterevidence_terms`.
- Done: `_reviewer_candidate_absence_gap_items` can rebind Critique candidates to menu items by explicit id or claim/type/entity token match and set `discovery_origin=critique_payload_menu_bound`.
- Done: verified bundle/evidence/review-issue records preserve `candidate_menu_id` and menu metadata.
- Done: dashboard and case-table scripts expose origin-split P31 fields including `critique_payload_gap_count`, `critique_payload_menu_bound_count`, `critique_payload_verified_count`, `critique_payload_verified_cluster_count`, and candidate-menu counts.
- Done: bundled safety fixes for recovery id union, generic protocol target rejection, and malformed `ranch_encoder` ablation target rejection.

Validation so far:

```text
py_compile: passed on touched runtime files, scripts, and tests
pytest: unavailable in both local Python environments
direct Python assertions: passed for normalizer, menu-bound verification, protocol guard, ranch_encoder guard, and recovery id union
offline P30 raw recompute: generated P31_MENU_RECOMPUTE_211251_* with protection PASS
```

Offline P30 raw recompute facts:

```text
verified_review_issue_count = 12
verified_review_issue_cluster_count = 11
review_issue_candidate_critique_payload_count = 31
critique_payload_gap_count = 18
critique_payload_menu_bound_count = 5
critique_payload_verified_count = 0
critique_payload_verified_cluster_count = 0
candidate_menu_item_count = 98
candidate_menu_item_used_count = 0
candidate_menu_item_verified_count = 0
```

Interpretation:

- The code and metrics plumbing are now in place.
- The historical P30 raw run cannot prove prompt improvement because its Critique payloads were generated before `review_issue_candidate_menu` existed.
- Next required evidence is a fresh MiMo hardneg20 run with P31 enabled, followed by dashboard, review issue case table, recovery table, and manual cluster audit.

## Fresh Run Checkpoint 2026-07-02

P31 fresh MiMo API4 hardneg20 completed after a reporting/runtime hotspot fix.

The first fresh attempt, `20260701_234505`, stalled at `4/20` after API calls finished for the second batch. The stalled paper was `XyB4VvF01X`; process sampling showed CPU dominated by Python regex/string work. The fix was to keep final-view and report metrics observational:

- `_review_issue_candidate_funnel_metrics` no longer reruns menu lookup, candidate gap construction, paper inventory search, worthiness checks, or full-text counterevidence.
- Dashboard and audit scripts now prefer cached runtime hygiene from `decision_hygiene` / `state_audit.decision_hygiene`.
- Dashboard cluster-origin metrics now read cached verified bundle labels instead of rerunning state verifiers.
- Review issue case table now filters rows using cached `review_issue_bundle_items`, aligning case-table rows with runtime dashboard counts.

Authoritative fresh run:

```text
raw = mimo_v25_negqty_recoverycap_guard3_qhyg_targetneg_freeformrevneg_reviewissuebundle_hardneg20_mt7_b4w2_api4_r8t600_tok1536_20260702_004622.jsonl
dashboard = P31_FRESH_API4_004622_HARDNEG20_DASHBOARD.md/json
review issue cases = P31_FRESH_API4_004622_REVIEW_ISSUE_CASE_TABLE.md/json
recovery cases = P31_FRESH_API4_004622_RECOVERY_CASE_TABLE.md/json
manual audit = P31_FRESH_API4_004622_MANUAL_CLUSTER_AUDIT_20260702.md/json
```

Headline metrics:

```text
protection = PASS
review_negative_verified_count = 0
verified_review_issue_count = 19
verified_review_issue_cluster_count = 14
reviewer_candidate_review_issue_critique_payload_count = 1
reviewer_candidate_review_issue_deterministic_seed_count = 18
critique_payload_verified_count = 1
critique_payload_verified_cluster_count = 1
deterministic_seed_verified_cluster_count = 13
candidate_menu_item_count = 3
candidate_menu_item_used_count = 0
candidate_menu_item_verified_count = 3
mark_contested_commit_count = 9
recovery_case_verified_review_issue_repair = 8
recovery_harmful_commit_committed = 0
negative_evidence_unlinked_to_flaw = 0
positive_or_neutral_negative_candidate_count = 0
negative_grounding_conflict_count = 0
```

Manual audit:

```text
system rows = 19
system clusters = 14
manual A/B clusters = 8
manual C clusters = 4
manual D clusters = 1
manual MERGE clusters = 1
critique-origin A/B clusters = 1
```

Decision:

- P31 is a partial success: Critique-origin verified clusters improved from `0` to `1` while protection and recovery safety remained clean.
- P31 does not meet the target `critique_payload_verified_cluster_count >= 3`; do not proceed to P32 as if autonomous Critique discovery is solved.
- Next implementation should focus on Critique-as-menu-selector: shorter top-K menus, explicit select/reject output, stronger `candidate_menu_id` copying, and better same-setting baseline validation.
- Add a precision guard for theory/loss-analysis claims being converted into empirical missing-ablation defects, based on the `7Dub7UXTXN` D-class cluster.

Follow-up implemented after this checkpoint:

- Missing-ablation target quality now rejects theory/loss-analysis loss targets such as `component-isolation ablation for simulated loss` when the context is learning-dynamics/global-minimum/expressivity/theorem oriented and lacks empirical benchmark/performance framing.
- Empirical contribution-bound loss targets remain allowed when tied to benchmark/performance context.
- `REVIEW_ISSUE_DISCOVERY_PROMPT` now treats menu selection as a stronger contract: any menu-derived candidate must copy `candidate_menu_id` exactly; free-form candidates without a menu id must explain why no menu item fits and provide their own copied inventory anchor.
- Focused direct tests passed for the new theory/loss target-quality guard and the existing theory-anchor review-issue rejection. `py_compile` passed for touched files.

Fresh validation after these follow-up changes:

```text
run = mimo_v25_negqty_recoverycap_guard3_qhyg_targetneg_freeformrevneg_reviewissuebundle_hardneg20_mt7_b4w2_api4_r8t600_tok1536_20260702_105402.jsonl
papers = 20/20
protection = PASS
evidence_json_fallback_rate_pct = 0
critique_prompt_chars_median = 11668
critique_prompt_chars_max = 11673
critique_prompt_over_15k_turns = 0
critique_prompt_over_30k_turns = 0
verified_review_issue_count = 12
verified_review_issue_cluster_count = 10
review_negative_verified_count = 1
mark_contested_commit_count = 5
review_issue_candidate_critique_payload_count = 19
candidate_menu_item_used_count = 7
candidate_menu_item_verified_count = 0
critique_payload_verified_cluster_count = 1
deterministic_seed_verified_cluster_count = 8
```

Decision:

- Runtime stability, prompt compaction, JSON reliability, and protection lines are validated.
- Critique-as-menu-selector is only partially validated: Critique selected menu items, but no menu-bound item became verified and only one Critique-origin cluster survived.
- P31.2 should continue into a P31.3 selector-quality/rebinding pass before P32 reproducibility.

## P31.2 Selector-Menu Working-Tree Update 2026-07-02

Implemented the first two Critique-as-menu-selector / prompt-runtime passes. These are discovery-layer and prompt-compaction changes only; they do not relax the bundle verifier.

Code changes:

- Added compact `review_issue_candidate_selector_menu` to the Critique state slice when review issue discovery is active.
- Kept the full per-claim `review_issue_candidate_menu`, but capped prompt-facing menus to top-K quality-ranked items (`max_items=4` per claim) with per-type diversity.
- Replaced long prompt-facing menu ids with shorter `rim-*` ids so MiMo has a simpler exact-copy target.
- Added selector item fields: `slot`, `why_review_worthy`, compact `inventory_anchor`, and `counterevidence_aliases`.
- Updated `REVIEW_ISSUE_DISCOVERY_PROMPT` and Critique observation rules so menu selection is the primary route: Critique should select/reject selector-menu items first, copy `candidate_menu_id` exactly for selected items, and use free-form candidates only when no menu item fits and it can provide its own concrete entity plus copied inventory anchor.
- Shortened `REVIEW_ISSUE_DISCOVERY_PROMPT` from the old long rule stack to a 5910-character menu-first contract.
- `compact_review_state_for_prompt` now derives compact `evaluation_inventory` from evidence/paper text when the runtime state has not persisted one, preventing selector menu loss in compact prompt paths.
- Dashboard now reports `critique_prompt_over_15k_turns` and `critique_prompt_over_30k_turns` in addition to Critique prompt median/max.
- Existing rebinding and verifier behavior remain unchanged: a selected menu item is still a hypothesis, not evidence.

Validation:

```text
py_compile: passed for state.py, review_prompts.py, review_runner.py, and touched tests
focused pytest: 6 passed for selector exposure, prompt contract, inventory derivation without cached state inventory, and long-target omission
offline prompt check on P31_FRESH_API4_004622 raw: rows=20, selector menu present=17, target leaks=0, empty inventory observations=0
offline rendered Critique prompt chars: median=10074, max=10074, over_15k=0, over_30k=0
```

Next required evidence:

```text
manual A/B/C/D audit for P31_2_FRESH_API4_105402's 10 clusters
root-cause audit for menu-used-but-not-verified candidates
P31.3 selector-quality patch
fresh MiMo hardneg20 after P31.3
```

Decision rule:

```text
IF critique_payload_verified_cluster_count >= 3
AND protection remains PASS
AND manual A/B quality does not regress
THEN proceed to P32 reproducibility runs.

ELSE keep deterministic-seed and Critique-origin capabilities separate,
and continue redesigning the selector menu rather than raising raw issue count.
```

## P31.4 Status Update 2026-07-02 Late

Current code now supports and observes the lightweight selected-menu path more accurately:

- selected menu ids can be recovered from the current per-claim menu, not only the compact selector top-6;
- `critique_payload_menu_selected` is counted as Critique-origin across state/dashboard/case-table metrics;
- dashboard reads selected-menu recovery telemetry from `runner_trace` when compact turn logs omit the top-level flags.

Validation on old/current raw:

```text
P31_4_MENUFIX_RECOMPUTE_163953_*:
  verified_review_issue_count = 14
  verified_review_issue_cluster_count = 12
  critique_payload_verified_cluster_count = 0
  review_issue_selected_menu_recovery_turns = 1
  review_issue_selected_menu_recovered_count = 1
  candidate_menu_item_used_count = 3
  candidate_menu_item_verified_count = 1
  protection counters = 0
```

Fresh validation attempt:

```text
P31_4_MENUFIX_PARTIAL8_213525_*:
  status = partial only, 8/20 rows
  blocker = MiMo API 402 insufficient account balance
  verified_review_issue_count = 4
  verified_review_issue_cluster_count = 4
  critique_payload_verified_cluster_count = 0
  review_issue_selected_menu_recovery_turns = 1
  candidate_menu_item_verified_count = 0
  protection counters = 0
```

Interpretation:

- Selected-menu plumbing is no longer the primary suspected blocker; it fired and produced a `critique_payload_menu_selected` candidate.
- The surviving issue is candidate quality versus strict bundle verification: the selected `WpXq5n8yLb` dynamic-tree-attention menu candidate was rejected by counterevidence, and another Critique candidate was rejected as not claim/inventory-bound.
- Do not proceed to P32. A complete full20 rerun is required after MiMo balance is restored, or P31.4 should continue with selector target-quality improvements before spending another full run.

## P31.5 Target-Quality Checkpoint 2026-07-02

Implemented the first selector/menu quality guard after the P31.4 plumbing audit:

- suppress missing-ablation menu candidates when claim/inventory ablation counterevidence already resolves the same target;
- classify verb-form `constrain/constraining` target fragments as weak actions, so `component-isolation ablation for constrain module` is rejected;
- keep noun/mechanism targets such as `constraint module` eligible at medium confidence when contribution/performance context supports them;
- apply the same target-quality and ablation-counterevidence gates to component-ablation deterministic seeds, preventing malformed fragments such as `component-isolation ablation for by the dynamic tree attention` and already-covered ablation targets from consuming future seed/menu budget;
- broaden local ablation counterevidence resolution for figure/table/study anchors only when at least two concrete target tokens match, while excluding negated `no/missing/without ablation` phrases;
- report stale/filtered selected-menu ids as `selected_menu_item_not_in_current_menu_or_filtered`, separating menu-quality filtering from true bundle-verifier failure;
- keep the strict bundle verifier unchanged.

Focused validation:

```text
py_compile state.py/review_runner.py/dashboard/case-table/tests = passed
ablation resolver/menu failure tests = 4 passed
target/menu/seed selector tests = 8 passed
selected-menu recovery tests = 5 passed
```

Offline current-code recompute on the partial 8-paper `213525` run:

```text
artifacts = P31_5_TARGETQUALITY_PARTIAL8_213525_UNCACHED_*
status = partial only, not full20
protection = PASS
verified_review_issue_count = 4
verified_review_issue_cluster_recomputed_count = 4
case-table verified clusters = 4
quote-grounded direct clusters = 1
obligation-grounded clusters = 3
critique_payload_verified_cluster_count = 0
candidate_menu_item_used_count = 1
candidate_menu_item_verified_count = 0
candidate_menu_item_failed_selected_menu_item_not_in_current_menu_or_filtered = 1
candidate_menu_item_failed_not_verified_by_bundle = 0
mark_contested_commit_count = 2
```

Interpretation:

- The current bottleneck is still selected Critique/menu candidate quality, not verifier strictness or runner plumbing.
- Use `UNCACHED` recompute artifacts for current-code paper-facing audits; cached partial artifacts can preserve stale `decision_hygiene`.
- The `WpXq5n8yLb` dynamic-tree-attention selected menu item is now treated as filtered from the current menu because the paper already has a tree-attention ablation anchor.
- Continue P31.5 before P32.  The required next evidence remains a complete full20 with `critique_payload_verified_cluster_count >= 3`, protection PASS, and stable manual A/B quality.

## P31.5 Full20 Update 2026-07-02

P31.5 now reaches the minimum Critique-origin lifecycle target on a complete full20 current-code recompute over the existing `20260702_163953` MiMo raw state.

Authoritative artifacts:

```text
P31_5_TARGETQUALITY_FULL20_163953_UNCACHED_HARDNEG20_DASHBOARD.md/json/audit.json
P31_5_TARGETQUALITY_FULL20_163953_UNCACHED_REVIEW_ISSUE_CASE_TABLE.md/json
P31_5_TARGETQUALITY_FULL20_163953_UNCACHED_RECOVERY_CASE_TABLE.md/json
```

Current metrics:

```text
paper_count = 20
verified_review_issue_count = 18
verified_review_issue_cluster_recomputed_count = 16
critique_payload_verified_cluster_count = 3
verified_review_issue_cluster_origin_critique_payload_count = 3
reviewer_candidate_review_issue_critique_payload_count = 3
mark_contested_commit_count = 5
negative_evidence_unlinked_to_flaw = 0
positive_or_neutral_negative_candidate_count = 0
negative_grounding_conflict_count = 0
protection = PASS
```

What changed:

- Critique missing-baseline lists are normalized without treating generic single acronyms as verified targets.
- Freeform Critique attribution now beats runner seed metadata when overlapping gaps merge.
- Scope/generalization expectation recognition covers `generalizable`, `cross-target`, target-shape/class, and molecular-class language.
- Bundle expectation can reuse a vetted candidate relevance basis from the gap stage while leaving claim anchor, inventory relevance, counterevidence, and author-limitation guards intact.

P31.5 status:

```text
quantitative gate = met
strict verifier/protection = met
manual A/B quality gate = pending
fresh API rerun = not performed for this checkpoint
```

P32 entry condition:

```text
Manual audit the 3 Critique-origin clusters:
  GE6iywJtsV / cross-target validation
  YXn76HMetm / hyperbolic curvature + active-learning reproducibility details
  KOUAayk5Kx / FairNAS/SNAS/ProxylessNAS/EWC/GEM missing baseline

Proceed to P32 only if these are A/B quality or any weak row is fixed by a precision guard.
```

## P31.5 Manual Audit Update 2026-07-03

Manual audit file:

```text
P31_5_CRITIQUE_ORIGIN_MANUAL_AUDIT_20260703.md
```

Outcome:

```text
GE6iywJtsV / cross-target validation = B- keep with wording caution
YXn76HMetm / hyperbolic curvature reproducibility = B keep
KOUAayk5Kx / FairNAS-SNAS-ProxylessNAS-EWC-GEM missing baseline = C/D reject
```

The KOUA row is now blocked by:

```text
full_text_broad_baseline_comparison_counterevidence
```

The Critique discovery prompt now mirrors this rule: missing-baseline candidates should be paper-named or menu/inventory-auditable, and the model should not invent an external list of well-known baselines when the paper already reports a broad same-setting comparison set.

Current full20 after the precision guard:

```text
verified_review_issue_count = 17
verified_review_issue_cluster_recomputed_count = 15
critique_payload_verified_cluster_count = 2
verified_review_issue_cluster_origin_critique_payload_count = 2
negative_evidence_unlinked_to_flaw = 0
positive_or_neutral_negative_candidate_count = 0
negative_grounding_conflict_count = 0
protection = PASS
```

Updated P32 entry status:

```text
P31.5 quantitative pre-audit gate = superseded
P31.5 quality-preserving Critique-origin count = 2
P32 entry = blocked by insufficient A/B Critique-origin clusters
Next = continue discovery/selector quality work to recover one more A/B cluster without relaxing verifier
```

## P31.6 Critique-Origin Recovery Attempt 2026-07-03

P31.6 keeps P31 active; it is not a P32 entry checkpoint.

Implemented:

- Missing-ablation counterevidence now requires real ablation/comparison/result
  context for plain `without` language.  Method prose such as `without needing
  eigendecomposition` no longer blocks a missing-ablation issue by itself.
- Critique missing-ablation candidates can use a deterministic full-text
  component anchor when they did not copy an inventory quote, but they still pass
  through the same bundle verifier, target-quality guard, and full-text
  counterevidence checks.
- Reviewer-candidate targets remain primary when merged with coarse
  claim-obligation targets.
- The Critique review-issue discovery prompt now treats
  `review_issue_candidate_selector_menu` as the primary selector, asks for 2-4
  safe selected menu items when available, and requires every menu-derived
  candidate id to be mirrored in `selected_menu_items`.

Validation:

```text
P31/P31.5 focused state tests = 21 passed
P31 prompt/recovery focused tests = 6 passed
py_compile = passed
```

Offline current-code recompute over the existing `163953` full20 raw:

```text
artifacts = P31_6_CRITORIGIN_RECOMPUTE_163953_*
verified_review_issue_count = 19
verified_review_issue_cluster_recomputed_count = 16
quote_duplicate_merged_verified_review_issue_cluster_count = 16
critique_payload_verified_cluster_count = 2
verified_review_issue_cluster_origin_critique_payload_count = 2
mark_contested_commit_count = 5
protection = PASS
```

Decision:

```text
P31.6 old-raw recompute still does not meet the P32 gate.
The current old raw has only two acceptable Critique-origin clusters; remaining
Critique failures are mostly correct rejections.
Next required step = fresh MiMo full20 with P31.6 prompt/menu-selection changes,
then dashboard + review issue case table + recovery table + manual audit.
```
