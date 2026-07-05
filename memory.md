# Memory - DrMAS Paper Review (Compact)

Last compacted: 2026-06-27.

This file is the working memory for the paper-review project. Keep it short. Move detailed historical narratives into separate audit/checkpoint docs instead of expanding this file.

## Current Objective

Build a structured, evidence-grounded, auditable, recoverable paper-review assistant.

The current research story is not "maximize PASS" or "increase negative count at any cost". The core goal is:

- find real paper-side review issues;
- ground verified negative evidence in paper quotes + locators;
- verify reviewer-discovered issue bundles when the flaw is an obligation/inventory mismatch rather than a direct negative quote;
- preserve positive support when it is real;
- keep conflicts visible through non-destructive recovery;
- separate diagnostic/potential concerns, obligation-grounded review issues, and quote-grounded verified negatives.

## Hard Constraints

- Do not allow fallback/context claim status patches.
- Do not downgrade fallback/context/synthetic claims to unsupported.
- Do not let quote-bank evidence directly downgrade a claim status.
- Do not package generic gaps as negative evidence.
- Do not count Critique/model judgment as verified negative evidence.
- Do not inflate `recovery_effective_repair` with diagnosis-pending records.
- Do not relax validator gates just to raise recovery commit counts.
- Do not replace Evidence Agent recheck turns with Critique "thinking" unless explicitly running a gated experiment.

Verified negative evidence must have:

- `claim_id`
- `flaw_id`
- copied paper quote / `negative_quote` or equivalent `raw_quote`
- `negative_type`
- locator
- weakened dimension / reason
- paper grounding and semantic negative verification

Missing-baseline, missing-ablation, insufficient-evaluation, and reproducibility gaps are often absence/coverage judgments. They must not be counted as `review_negative_verified_count` unless there is a direct negative quote. They may count as `verified_review_issue_count` / obligation-grounded review issues only when the verifier has all of:

- locatable claim anchor;
- concrete reviewer-discovered missing/mismatch item;
- current claim requirement gap;
- observed inventory quote/list/table anchor that is either verified support inventory or copied text locatable in the paper.

## Current Review Issue Logic

### 2026-07-05 P32 entry after P31.6 manual audit

Current position: Stage 1/2 hardneg20 readiness is achieved for the current
ReviewState path.  Stage 3 contested/recovery is functional but not fully
saturated, and the next project-level stage is P32 clean reproducibility.

Latest authoritative fresh hardneg20:

- code baseline: `374b827 Tighten review issue precision after manual audit`
- raw:
  `mimo_v25_negqty_recoverycap_guard3_qhyg_targetneg_freeformrevneg_reviewissuebundle_hardneg20_mt7_b4w2_api4_r8t600_tok2048_20260705_205654.jsonl`
- artifacts: `P31_6_FRESH_20260705_205654_*`
- rows: 20/20; machine gate PASS; manual gate PASS; `p32_entry_ready=true`.
- `evidence_json_fallback_rate_pct=0`, `state_contamination_count=0`,
  `negative_evidence_unlinked_to_flaw=0`,
  `positive_or_neutral_negative_candidate_count=0`,
  `negative_grounding_conflict_count=0`,
  `semantic_negative_without_review_relation_count=0`.
- `verified_review_issue_count=10`, recomputed cluster count=6,
  quote-duplicate-merged cluster count=6.
- `critique_direct_verified_cluster_count=6`,
  `critique_payload_verified_cluster_count=6`,
  `critique_selected_existing_seed_cluster_count=0`.
- `candidate_menu_item_verified_count=6`, failed=8; failures are verifier or
  target-quality rejects, not relaxed away.
- manual audit: 6 A/B clusters, 0 C, 0 D, 0 unfilled;
  `critique_origin_manual_A_B_clusters=5`,
  `deterministic_seed_manual_A_B_clusters=0`.
- accepted issue types: direct `negative_result`, `missing_baseline`,
  `missing_ablation`, and `efficiency_cost_gap`.
- recovery: `mark_contested_commit_count=16`,
  `verified_issue_cluster_without_recovery_count=2`,
  `recovery_harmful_commit_committed=0`.

P32 entry artifact:

- `P32_ENTRY_AUDIT_20260705.md`
- `P32_CLEAN_R1_ATTEMPT_20260705_224419_STATUS.md` records the first P32
  clean-run attempt as incomplete: 16/20 rows, stopped by MiMo `402
  Insufficient account balance`, not counted as a P32 run.

Interpretation:

- The `Critique discovery -> verified issue -> contested relation` path is now
  functional on one fresh hardneg20 run without seed-shadow attribution.
- The paper narrative can update its internal evidence boundary, but should not
  rewrite final result tables until P32 repeated clean runs show stability.
- P32 should run 3 clean hardneg20 repeats with the same runtime code baseline,
  `DRMAS_JSON_RESPONSE_FORMAT=on`, and `MAX_TOKENS=2048`.
- The older P32 plan's `max_tokens=1536` is superseded by the current project
  constraint and validated fresh-run setting of 2048.
- First P32 run attempt used `code_commit=e7735c5`, `code_dirty=clean`, and
  `MAX_TOKENS=2048`, but failed due account balance after 16 rows.  Recharge
  MiMo and rerun from scratch; do not postprocess or manually audit the partial
  as a clean hardneg20.
- Added `scripts/p32_stability_report.py` to aggregate P32 clean-run evidence
  across generated P31.6 artifacts.  It excludes partial runs, requires raw
  jsonl row evidence, summarizes A/B count statistics, D rate, pairwise cluster
  Jaccard, same-paper/same-target recurrence, Critique-origin recurrence, and
  harmful recovery.  Default P32 threshold remains 3 complete runs.
- Validation for the stability tool: `tests/test_p31_6_gate_scripts.py` passed
  8/8; live artifact dry check included the 20/20 P31.6 run and excluded the
  16/20 P32 attempt.
- Do not jump to full39, do not touch `verl/`, and do not relax verifier or
  validator gates.

### Historical 2026-07-05 P31.35 trigger-menu checkpoint

Current position: Stage 1 tail / Stage 2 start.  The current functional target is
real `Critique discovery -> verified issue -> contested relation`, not seed
shadow attribution and not relaxed verifier gates.

Latest fresh hardneg20 before the trigger-menu patch:

- raw: `mimo_v25_negqty_recoverycap_guard3_qhyg_targetneg_freeformrevneg_reviewissuebundle_hardneg20_mt7_b4w2_api4_r8t600_tok2048_20260705_202504.jsonl`
- artifacts: `P31_6_FRESH_20260705_202504_*`
- rows: 20/20; protection PASS; entry gate FAIL.
- `evidence_json_fallback_rate_pct=0`, `state_contamination_count=0`.
- `verified_review_issue_count=23`, cluster count=20.
- `critique_direct_verified_cluster_count=2`, required >=3.
- `candidate_menu_item_count=6`, `candidate_menu_item_used_count=5`,
  `candidate_menu_item_verified_count=2`, `candidate_menu_item_failed_count=3`.
- selected-menu failure reasons: `full_text_protocol_or_result_counterevidence`,
  `efficiency_cost_menu_already_observed_in_inventory`,
  `missing_ablation_target_low_confidence`.

Interpretation:

- Safety/hygiene is clean, but Stage 2 still fails on real Critique direct
  coverage in the latest full hardneg20 evidence.
- The main root cause found after the run is menu starvation: many papers had
  verifier-ready selector menu supply, but `Critique Agent` never saw it because
  discovery was gated on `positive_inventory_ready` and
  `real_strong_support_count >= 1`.
- Do not fix this by relaxing the bundle verifier or by re-attributing seed
  clusters to Critique.  The correct lane is trigger/menu supply and selected
  candidate materialization.

Implemented after the 202504 run:

- selected prompt-time menu snapshots are no longer killed by a second current
  menu quality recheck when the exact menu item has already been selected;
  bundle verification remains the authoritative check.
- efficiency menu "already observed" rejection now checks actual inventory text,
  not claim text plus source text.
- selected efficiency candidates can use strict paper-text empirical/baseline
  inventory fallback when the prompt-time snapshot inventory is too short.
- visible/selector-style review issue discovery no longer requires positive
  inventory readiness or a real strong support row when a selector menu exists.
- mixed invalid candidate negative anchors are downgraded in the decision view
  instead of being counted as hard state contamination.

Validation:

- focused hygiene/gate tests: 16 passed.
- focused runner selected-menu/discovery tests: 25 passed.
- `py_compile` for touched runtime/tests: PASS, with only pre-existing invalid
  escape warnings in tests.

Runtime validation after loading `.env`:

- sample4 input: `p31_35_trigger_menu_sample4_20260705.parquet`.
- sample4 raw: `p31_35_trigger_menu_sample4_20260705_205100.jsonl`, rows=4.
- sample4 result: all 4 papers triggered `review_issue_discovery_override`;
  aggregate `critique_direct_verified_cluster_count=4`,
  `candidate_menu_item_used_count=4`, `candidate_menu_item_verified_count=4`,
  `candidate_menu_item_failed_count=0`, `state_contamination_count=0`.
- fresh hardneg20 raw:
  `mimo_v25_negqty_recoverycap_guard3_qhyg_targetneg_freeformrevneg_reviewissuebundle_hardneg20_mt7_b4w2_api4_r8t600_tok2048_20260705_205654.jsonl`
- latest artifacts: `P31_6_FRESH_20260705_205654_*`.
- rows: 20/20; machine gate PASS; manual gate REQUIRED; readiness remains
  false until the manual audit template is filled and validated.
- `evidence_json_fallback_rate_pct=0`, `state_contamination_count=0`,
  `harmful_state_contamination_count=0`.
- `verified_review_issue_count=24`, cluster count=15.
- `critique_direct_verified_cluster_count=12`,
  `critique_selected_existing_seed_cluster_count=0`.
- `candidate_menu_item_count=14`, `candidate_menu_item_used_count=14`,
  `candidate_menu_item_verified_count=12`, `candidate_menu_item_failed_count=2`.
- selected-menu failures are now verifier/quality rejects:
  `missing_entity_already_observed_in_inventory=1`,
  `efficiency_cost_menu_already_observed_in_inventory=1`.
- `positive_or_neutral_negative_candidate_count=0`,
  `negative_evidence_unlinked_to_flaw=0`,
  `negative_grounding_conflict_count=0`.
- `mark_contested_commit_count=16`,
  `verified_issue_cluster_without_recovery_count=3`.

Additional hygiene fix:

- Existing `reviewer_absence_audit` flaws in raw states can carry stale selected
  candidate claim snapshots.  The view layer now refreshes those flaw
  descriptions from the authoritative current claim table and linked verified
  issue evidence.  This removed a `meta_leakage` contamination on
  `NnExMNiTHw` without hiding the target.

Next required evidence:

1. Fill and validate `P31_6_FRESH_20260705_205654_MANUAL_AUDIT_TEMPLATE.*`,
   prioritizing the 11 Critique-origin clusters listed by the entry gate.
2. Treat Stage 2 as machine-live on hardneg20, but not paper-ready until manual
   A/B/C/D validation confirms precision.
3. If manual precision is acceptable, move the main engineering focus to Stage
   3 residual recovery coverage (`verified_issue_cluster_without_recovery=3`).

### 2026-07-05 P31.28 post-fix Critique-origin 5-paper sample + Stage 3 scheduler patch

Post-fix sample:

- input: `p31_28_postfix_critique5_input.parquet`
- raw: `p31_28_postfix_critique5_20260705_185055.jsonl`
- artifacts: `P31_28_POSTFIX_CRITIQUE5_20260705_185055_*`
- rows: 5/5; machine gate PASS; manual gate PASS.
- `evidence_json_fallback_rate_pct=0`, `state_contamination_count=0`.
- `verified_review_issue_count=13`, cluster count=11.
- `critique_direct_verified_cluster_count=4`, `candidate_menu_item_verified_count=4`.
- `candidate_menu_item_failed_count=0`, `critique_selected_existing_seed_cluster_count=0`.
- `positive_or_neutral_negative_candidate_count=0`, `negative_evidence_unlinked_to_flaw=0`, `negative_grounding_conflict_count=0`.
- `mark_contested_commit_count=3`, `verified_issue_cluster_without_recovery_count=6`.

Important audit result:

- The SPOT false positive is fixed in the fresh API path:
  `including_loss_verified=False` for `9zEBK3E9bX`.
- Manual Critique-origin-only audit labels:
  - A: `GE6iywJtsV / graph_control_module`
  - B: `NnExMNiTHw / acceptance_prediction_head`
  - C: `QAgwFiIY4p / coordinates_without_information_loss`
  - B: `YXn76HMetm / equalal_baseline`
- Manual validation: 3 A/B, 1 C, 0 D, 0 unfilled.  Entry gate now reports
  machine PASS and manual PASS when supplied with
  `P31_28_POSTFIX_CRITIQUE5_ONLY_MANUAL_AUDIT_VALIDATION_20260705_185055.json`.
- Do not reuse the pre-fix Graphormer manual judgment for post-fix QAg.  The
  post-fix QAg issue is a weak/over-specific C and must not be counted as a
  paper-facing Stage 2 success.

Interpretation:

- Stage 2 remains functional after removing the 9z false positive: direct
  Critique clusters are still >=3, protection is clean, and the manual
  Critique-origin gate passes on the 5-paper post-fix sample.
- This is small-sample evidence only.  It is not yet a hardneg20/full39 paper
  claim.
- Stage 3 remains incomplete, but the next failure mode is now sharper:
  recovery should distinguish open issues that need same-claim support first
  from already supported-but-contested issues that should enter `mark_contested`.

Implemented Stage 3 scheduler patch:

- Added `s4_verified_review_issue_support_recheck_bridge` in
  `review_manager_policy.py`.  Open verified review issues with no same-claim
  verified positive support now get one targeted `request_evidence_recheck`
  before recovery, instead of burning a blocked patch turn.
- Removed the phase blocker from the verified review issue recovery bridge, so
  eligible supported-but-contested review issues can route to
  `challenge_previous_hypothesis` even when `phase=recovery`.
- P31.28 probe with current code:
  - `NnExMNiTHw` routes to `s4_verified_review_issue_recovery_bridge`;
  - `GE6iywJtsV` routes to support recheck first;
  - `YXn76HMetm` stays out of contested because claim-3 is already
    `unsupported`.
- Validation: new policy tests 3 passed; neighbor selector/recovery policy
  tests 5 passed; `py_compile` passed.  A broader old recovery-bundle
  targeted selection still exposes pre-existing fixture/materialization
  failures and should not be reported as green.

### 2026-07-05 P31.27 hardneg20 Stage 2 machine pass + SPOT false-positive fix

Fresh hardneg20 run:

- raw: `mimo_v25_negqty_recoverycap_guard3_qhyg_targetneg_freeformrevneg_reviewissuebundle_hardneg20_mt7_b4w2_api4_r8t600_tok2048_20260705_182335.jsonl`
- artifacts: `P31_6_FRESH_20260705_182335_*`
- rows: 20/20; machine gate PASS; manual gate REQUIRED.
- `evidence_json_fallback_rate_pct=0`, `state_contamination_count=0`.
- `verified_review_issue_count=22`, cluster count=18.
- `critique_direct_verified_cluster_count=5`, `candidate_menu_item_verified_count=5`, `critique_selected_existing_seed_cluster_count=0`.
- `mark_contested_commit_count=10`, `verified_issue_cluster_without_recovery_count=10`.
- Weak hygiene warnings remain split from hard contamination: legacy/warning count=15 (`zero_real_support=7`, `stale_gap_persistence=8`).

Manual preaudit of the five Critique-origin clusters found four likely A/B
clusters (Diff-Shape graph control module, SpecDec++ acceptance prediction
head, PST/Graphormer baseline, HALO/EqualAL baseline) and one likely false
positive or downgrade:

- `9zEBK3E9bX / including_loss`: selected missing-ablation target was cut from
  "including loss balancing"; the paper text says Table 6 is an ablation study
  on pre-training strategies and explicitly mentions loss balancing.

Implemented fix:

- reject `including ...` missing-ablation targets as prose fragments;
- treat SPOT-style pre-training strategy ablation tables with explicit `loss
  balancing` as full-text counterevidence;
- allow missing-ablation component anchors from reviewer inventory quotes when
  the quote itself contains the target, even if `observed_items` is empty;
- allow deterministic component-ablation seed/menu supply from locatable
  claim-surface component anchors such as `learned routing component`.

Validation:

- focused hygiene missing-ablation/state tests: 56 passed;
- focused runner/gate selected-menu tests: 26 passed;
- `py_compile` for touched files: PASS;
- broad three-file suite is not green: 806 passed / 28 failed. Do not claim
  full-suite green.

Interpretation:

- Stage 2 is functionally live at machine-gate level, but paper-ready precision
  still requires fresh post-fix sample/hardneg20 evidence.
- Next major direction after rerun confirmation: Stage 3 contested/recovery
  coverage. Recovery is live but incomplete, not yet a finished narrative.

### 2026-07-05 P31.9 selected-menu audit instrumentation

Latest local commit before this pass: `b22eea6 Add P31.8 fresh guard full20 audit results` (local `main` ahead of `origin/main` by 1). P31.9 is an audit/instrumentation pass over the same fresh raw run, not a new API run.

Fresh raw run audited:

- raw: `mimo_v25_negqty_recoverycap_guard3_qhyg_targetneg_freeformrevneg_reviewissuebundle_hardneg20_mt7_b4w2_api4_r8t600_tok1536_20260704_191150.jsonl`
- previous fresh artifacts: `P31_8_FRESH_GUARD_FULL20_20260704_191150_*`
- new audit artifacts: `P31_9_CRITMENU_AUDIT_FROM_FRESH_20260704_191150_*`

P31.8/P31.9 facts from fresh full20:

- full20 completed: 20/20; protection PASS.
- `verified_review_issue_count=18`, `verified_review_issue_cluster_count=16`, `review_negative_verified_count=2`.
- `candidate_menu_item_verified_count=2`, but both are selected-menu matches to already verified deterministic seed clusters.
- P31.9 split shows `critique_direct_verified_cluster_count=0` and `critique_selected_existing_seed_cluster_count=2`.
- `candidate_menu_item_failed_detail_count=5`; failures are now listed in the entry-gate artifact.
- Machine gate still FAILS: `critique_payload_verified_cluster_count=2 < 3` and case-table Critique-origin clusters = 2 < 3.

Interpretation:

- The current system is safe and has enough total verifier-passing issue rows/clusters for analysis, but Critique autonomous discovery is not solved.
- Do not describe the two Critique-selected clusters as independent Critique-generated verified issues; they are selected-menu attributions to existing seed clusters.
- The next engineering target is selected-menu reliability and direct Critique candidate materialization, not higher seed quantity or looser verifier gates.
- Dashboard/gate artifacts must preserve selected-menu failure details so future runs can explain whether failures are stale/current-menu lookup, boundary-claim filtering, counterevidence, or already-observed inventory.

Next P31.9/P32-blocking work:

1. Make `critique_direct_verified_cluster_count >= 3` in a fresh run before claiming autonomous discovery.
2. Keep `critique_selected_existing_seed_cluster_count` separate from direct Critique clusters in dashboards and paper narrative.
3. Investigate menu starvation and selection: full20 selected only 7 menu items, with 5 failures.
4. Improve direct selected-menu candidate verification/materialization using the prompt-time menu snapshot, without fuzzy rebinding stale ids.
5. Keep recovery non-destructive; `mark_contested_commit_count=4` and `verified_issue_cluster_without_recovery_count=11` show recovery bridge remains incomplete.

There are deliberately separate lanes. Keep them separate in code, metrics, dashboards, and paper narrative.

### 2026-07-02 P31.2 Critique-as-menu-selector current-code full20

Current P31.2 authoritative fresh run:

- raw: `mimo_v25_negqty_recoverycap_guard3_qhyg_targetneg_freeformrevneg_reviewissuebundle_hardneg20_mt7_b4w2_api4_r8t600_tok1536_20260702_105402.jsonl`
- dashboard: `P31_2_FRESH_API4_105402_HARDNEG20_DASHBOARD.md/json`
- review issue cases: `P31_2_FRESH_API4_105402_REVIEW_ISSUE_CASE_TABLE.md/json`
- recovery cases: `P31_2_FRESH_API4_105402_RECOVERY_CASE_TABLE.md/json`

P31.2 facts:

- full hardneg20 completed: 20/20 papers;
- protection PASS, including `negative_evidence_unlinked_to_flaw=0`, `positive_or_neutral_negative_candidate_count=0`, `negative_grounding_conflict_count=0`, and `recovery_harmful_commit_committed=0`;
- evidence JSON reliability is fixed for this run: `evidence_json_valid_turns=62`, `evidence_json_fallback_turns=0`, `evidence_json_fallback_rate_pct=0`;
- prompt/runtime compaction is validated in the fresh API path: `critique_prompt_chars_median=11668`, `critique_prompt_chars_max=11673`, `critique_prompt_over_15k_turns=0`, `critique_prompt_over_30k_turns=0`;
- review issue output is conservative: `verified_review_issue_count=12`, `verified_review_issue_cluster_count=10`, `review_negative_verified_count=1`;
- recovery bridge remains safe but incomplete: `mark_contested_commit_count=5`, with 4 verified review issue repairs and 1 direct verified negative repair;
- Critique-as-selector is not solved: `review_issue_candidate_critique_payload_count=19`, `candidate_menu_item_used_count=7`, but `candidate_menu_item_verified_count=0` and `critique_payload_verified_cluster_count=1`;
- deterministic seeds still dominate verified clusters: `deterministic_seed_verified_cluster_count=8`.

Initial manual cluster audit artifact:

- `P31_2_FRESH_API4_105402_MANUAL_CLUSTER_AUDIT_20260702.md/json`
- audit boundary: case-table audit, not full-paper reread;
- system rows/clusters: 12 rows / 10 clusters;
- manual A/B clusters: 5 (`A=2`, `B=3`);
- manual C clusters: 3;
- manual D clusters: 2;
- Critique-origin clusters: 1, and it is B;
- menu-bound verified clusters: 0.

Interpretation:

- P31.2 succeeded on runtime stability, prompt size, JSON reliability, and protection hygiene.
- P31.2 did not meet the Critique-origin target (`critique_payload_verified_cluster_count >= 3`) and should not be treated as ready for P32 autonomous-discovery claims.
- The next work is not to loosen verifier gates or chase raw issue count. It is to improve selector-menu item quality, Critique select/reject behavior, and menu-bound candidate rebinding so Critique-origin clusters can survive strict verification.
- Two D-class lessons must become P31.3 guards: action/related-work phrases such as `analyze the mechanism` are not valid ablation targets; baseline names such as `RIPU` are not held-out coverage/scope targets.

Implemented P31.2 changes:

- review issue discovery targets now expose a compact `review_issue_candidate_selector_menu` in addition to the full per-claim `review_issue_candidate_menu`;
- menu ids are shorter (`rim-*`) and intended to be copied exactly by Critique;
- selector items include `why_review_worthy`, `expected_entity`, `inventory_anchor`, `counterevidence_aliases`, `slot`, `issue_type`, `required_evidence_type`, and `obligation_id`;
- per-claim prompt menu is capped to top-K quality-ranked items with per-type diversity, reducing prompt clutter;
- `REVIEW_ISSUE_DISCOVERY_PROMPT` was shortened to a menu-first discovery contract; it tells Critique to select/reject selector-menu items before free-form generation, and to copy `candidate_menu_id` exactly for selected items;
- compact prompt state now derives a short `evaluation_inventory` from evidence/paper text when the runtime state has not persisted one, so selector menu generation does not depend on tests manually injecting inventory;
- dashboard now reports Critique prompt length cap metrics: `critique_prompt_over_15k_turns` and `critique_prompt_over_30k_turns`;
- verifier/recovery semantics are unchanged: menu items are non-evidence hypotheses and still require claim anchor, concrete item, locatable inventory, target-quality, and counterevidence checks;
- runtime hot paths were budgeted so prompt construction and inventory/counterevidence scans no longer spin on full-text regex loops during hardneg20.

Validation in this environment:

- `py_compile` passed for touched runtime/prompt/test files;
- focused pytest passed: 6/6 for selector exposure, long-target omission, inventory derivation without cached state inventory, prompt contract, and related review-inference checks;
- offline prompt check on `P31_FRESH_API4_004622` raw: rows=20, selector menu present=17, long target leaks=0, empty inventory observations=0, Critique prompt median/max=10074 chars, over-15k turns=0, over-30k turns=0;
- prompt constant length is now 5910 chars, down from roughly 15k;
- fresh MiMo 105402 full20 validates runtime/prompt metrics and protection lines.

Next implementation required: P31.3 selector-quality/rebinding fixes based on the selector failure audit. Do not claim Critique discovery is solved until fresh-run evidence shows `critique_payload_verified_cluster_count >= 3` without precision regression.

P31.3 selector failure audit artifact:

- `P31_3_SELECTOR_FAILURE_AUDIT_20260702.md`
- 7 menu-used Critique candidates were audited.
- Root cause 1: prompt-time `rim-*` menu ids are not stable at verification time because the verifier recomputes menu lookup from the later state; exact ids can disappear.
- Root cause 2: when exact id lookup misses, fuzzy token fallback can bind the candidate to a different menu item, e.g. `a6SntIisgg` alignment-loss/module was rebound to local-branch.
- Root cause 3: several rendered menu items ask for evidence already present in inventory (`quantitative result table for X`, explicit ablation study), so verifier correctly rejects them as already observed/counterevidenced.
- Root cause 4: direct negative/boundary claims should not receive redundant missing-baseline menu items.
- P31.3 fix direction: candidate metadata from the prompt should be first-class; exact `candidate_menu_id` miss must not fuzzy-bind to another id; bad/already-satisfied menu items should be filtered before rendering.

P31.3 first selector-rebinding patch implemented:

- exact copied `candidate_menu_id` miss no longer fuzzy-binds to a different recomputed menu item;
- candidate copied `candidate_menu_id` is preserved into the gap/bundle path as `critique_payload_menu_metadata` when recomputed lookup misses;
- colliding/truncated `obligation_id` no longer injects an unrelated expected entity unless non-generic target tokens overlap the candidate text;
- partial menu-quality guards suppress already-observed result-table items when the table/result entity is visible in inventory, suppress self-reported ablation-study menu items for ablation claims, and reject action phrases such as `analyze the mechanism`;
- reviewer-candidate dedupe now includes `candidate_menu_id` or normalized missing target for Critique payload candidates, so distinct selected menu items on the same claim/type/requirement do not shadow each other;
- generic `insufficient_evaluation` menu items like `quantitative result table for ...` are suppressed before prompt rendering because they are usually retrieval-framed rather than obligation mismatches;
- focused tests passed: 8 selector/rebinding/menu-quality tests + 5 P31.2 prompt/runtime tests; `py_compile` passed;
- 105402 probes: selector remains nonempty on 15/20 papers with 48 total items; generic result-table and `analyze the mechanism` menu items are 0; `a6SntIisgg` alignment-loss/alignment-module candidates form separate gaps without local-branch injection.

Still open for P31.3:

- rerun MiMo full20 before claiming Critique selector improvement.
- if the next run still has `critique_payload_verified_cluster_count <= 1`, inspect whether Critique is rejecting cleaner menu items or still producing free-form candidates without verifier-ready metadata.

### 2026-07-01 P29 manual cluster audit and paper-facing count

Latest P29 artifacts:

- source run: `mimo_v25_negqty_recoverycap_guard3_qhyg_targetneg_freeformrevneg_reviewissuebundle_hardneg20_mt7_b4w2_api2_r8t600_tok1536_20260701_160531.jsonl`
- dashboard: `P29_DISCOVERY_EXPAND_MIMO_160531_TARGETGUARD3_HARDNEG20_DASHBOARD.md/json`
- review issue cases: `P29_DISCOVERY_EXPAND_MIMO_160531_TARGETGUARD3_REVIEW_ISSUE_CASE_TABLE.md/json`
- recovery cases: `P29_DISCOVERY_EXPAND_MIMO_160531_TARGETGUARD3_RECOVERY_CASE_TABLE.md/json`
- manual audit: `P29_MANUAL_CLUSTER_AUDIT_20260701.md/json`

P29 system metrics:

- Overall protection: PASS.
- `verified_review_issue_count=20`
- `verified_review_issue_cluster_count=15`
- `quote_grounded_direct_quote_duplicate_cluster_count=1`
- `quote_duplicate_merged_verified_review_issue_cluster_count=14`
- `review_negative_verified_count=2`
- `obligation_grounded_review_issue_count=18`
- `mark_contested_commit_count=11`
- `recovery_case_verified_review_issue_repair=8`
- `negative_evidence_unlinked_to_flaw=0`
- `positive_or_neutral_negative_candidate_count=0`
- `negative_grounding_conflict_count=0`

Cluster-level origin matters for the paper narrative:

- `verified_review_issue_cluster_origin_critique_payload_count=1`
- `verified_review_issue_cluster_origin_deterministic_seed_count=10`
- `verified_review_issue_cluster_origin_claim_obligation_fallback_count=2`
- `verified_review_issue_cluster_origin_direct_quote_count=2`

Manual audit result:

- System rows/clusters: 20 rows / 15 system clusters.
- One direct-quote duplicate cluster should be manually merged, leaving 14 manual-deduplicated clusters.
- Strict A/B clusters: 8.
- Permissive A/B clusters: 9, counting the HALO/EqualAL same-setting baseline issue as defensible.
- Label split: A=4, B=4, C=3, D=3, MERGE=1.

Paper-facing wording:

- Allowed: "P29 produced 20 verifier-passing rows and 15 system clusters. Manual spot-checking supports 8 strict A/B clusters, 9 under a permissive reading, after merging one direct-quote duplicate."
- Not allowed: "P29 found 15 true defects" or "Critique autonomously discovered 15 issues."
- The quantity gain is real, but most verified clusters still come from deterministic reviewer seeds rather than free-form Critique payloads.

Important audit findings:

- Strong A clusters: ReDrafter recurrent draft model ablation, SpecDec++ acceptance prediction head ablation, LogoRA global encoder ablation, NR-DCCA generalized noise regularization ablation.
- Defensible B clusters: SPOT occupancy-objective comparison, Diff-Shape GrCN reproducibility, PSRD reproducibility, secure-aggregator negative result.
- False positives/counterevidence misses: LAVT missing baseline, HALO RIPU protocol, HALO HFR missing ablation.
- Risky C clusters: CDiffuser planning-module ablation, HALO EqualAL same-setting baseline, OGL protocol/split/seed target.

Next work:

- Do a clean-commit MiMo full20 rerun with `API_MAX_WORKERS=4` now that the user prefers speed over conservative workers.
- If the clean rerun keeps strict A/B clusters below 10, improve non-ablation slots and counterevidence retrieval rather than relaxing verifier gates.

### 2026-06-30 P28.1 ClusterGuard Fix recompute on 223747

Latest authoritative P28.1 artifacts are offline recomputes of the `bc56c3a` API run:

- source run: `mimo_v25_negqty_recoverycap_guard3_qhyg_targetneg_freeformrevneg_reviewissuebundle_hardneg20_mt7_b4w2_api2_r8t600_tok1536_20260629_223747.jsonl`
- dashboard: `P28_1_FIX_RECOMPUTE_223747_HARDNEG20_DASHBOARD.md/json`
- audit: `P28_1_FIX_RECOMPUTE_223747_HARDNEG20_AUDIT.json`
- review issue cases: `P28_1_FIX_RECOMPUTE_223747_REVIEW_ISSUE_CASE_TABLE.md/json`
- recovery cases: `P28_1_FIX_RECOMPUTE_223747_RECOVERY_CASE_TABLE.md/json`

Why this fix exists:

- `P28_CLUSTERGUARD_API_223747` had good quantity (`verified_review_issue_count=19`, `verified_review_issue_cluster_count=15`) but protection failed because `positive_or_neutral_negative_candidate_count=1`.
- The failing case was `XH3OiIhtvf`: an EER quote explicitly said the system improved from the baseline (`2.36`, `8.57% relative improvement`) but was still present as a `result_claim_mismatch` negative candidate.
- The same run also showed baseline target precision risk: generic/truncated targets such as `high-retur`, `pre-training`, `distillation-based`, and `baseline_for_something-something` were counted as missing-baseline issue clusters.
- OGL target normalization was too wide: `orthogonal_direction_the_gradient` and `orthogonal_gradient_learning` were separate clusters for the same paper mechanism.

Implemented P28.1 code changes:

- Added a lower-is-better metric improvement guard for direct result negatives. For `result_claim_mismatch` / direct result lanes, quotes about lower-is-better metrics (`EER`, error rate, WER/CER, loss, MAE/RMSE/MSE, FPR/FNR, etc.) with improvement/reduction/lower/better cues are treated as `not_negative_evidence`, not as positive/neutral negative candidates.
- Added a missing-baseline target specificity gate. It rejects generic or truncated baseline targets such as `high-retur`, `pre-training`, `distillation-based`, `baseline_for_*`, and `Something-Something` dataset/task fragments while preserving named methods such as `EqualAL` / `LAVT`.
- Added funnel accounting for baseline target rejects: `review_issue_candidate_missing_baseline_target_rejected` and `review_issue_candidate_missing_baseline_generic_target_rejected`.
- Extended review-issue cluster normalization so `orthogonal direction to the gradient` / `orthogonality constraint` map to `orthogonal_gradient_learning`.

P28.1 recompute metrics:

- Overall protection: PASS.
- `positive_or_neutral_negative_candidate_count=0`
- `negative_evidence_unlinked_to_flaw=0`
- `semantic_negative_without_review_relation_count=0`
- `evidence_json_fallback_rate_pct=0`
- `review_negative_verified_count=1`
- `verified_review_issue_count=15`
- `verified_review_issue_cluster_count=10`
- `duplicate_review_issue_row_count=5`
- `reviewer_candidate_review_issue_count=14`
- `reviewer_candidate_review_issue_cluster_count=9`
- `claim_obligation_review_issue_count=0`
- `claim_obligation_review_issue_cluster_count=0`
- `review_issue_cluster_type_missing_ablation=6`
- `review_issue_cluster_type_missing_baseline=1`
- `review_issue_cluster_type_missing_robustness_or_generalization=1`
- `review_issue_cluster_type_reproducibility_gap=1`
- `review_issue_candidate_missing_baseline_target_rejected=1`
- `review_issue_candidate_missing_baseline_generic_target_rejected=1`
- `mark_contested_commit_count=8`
- `recovery_case_verified_review_issue_repair=6`

Interpretation:

- P28.1 fixes the hard protection failure and makes the latest 223747 run paper-facing again, but it is a precision-control recompute, not a new API rerun.
- Quantity is now lower but cleaner: 19 rows / 15 clusters became 15 rows / 10 clusters; all claim-obligation fallback issue clusters were removed, leaving 9 reviewer-candidate clusters plus 1 quote-grounded issue.
- The defensible narrative is: strict quote-negative lane remains rare (`review_negative_verified_count=1`), while obligation-grounded issue bundles provide 10 system-clustered review issue clusters after protection and target-quality guards.
- Remaining risk: the 10 clusters still need manual A/B/C/D audit before paper-ready reporting, especially missing-ablation rows where an ablation section exists but may or may not isolate the exact mechanism.

### 2026-06-30 P28.2 Manual-audit precision checkpoint on 223747 (latest)

Latest P28.2 artifacts:

- dashboard: `P28_2_MANUALAUDIT_RECOMPUTE_223747_HARDNEG20_DASHBOARD.md/json`
- audit: `P28_2_MANUALAUDIT_RECOMPUTE_223747_HARDNEG20_AUDIT.json`
- review issue cases: `P28_2_MANUALAUDIT_RECOMPUTE_223747_REVIEW_ISSUE_CASE_TABLE.md/json`
- recovery cases: `P28_2_MANUALAUDIT_RECOMPUTE_223747_RECOVERY_CASE_TABLE.md/json`
- manual cluster audit: `P28_2_MANUAL_CLUSTER_AUDIT_223747.md`

Manual audit of P28.1's 10 clusters found four D-class clusters:

- `xUe1YqEgd6 / divided_attention`: target came from prior-work DivA, not LT-MS's own claim/inventory.
- `KOUAayk5Kx / orthogonal_gradient_learning`: paper has RandomNAS/GDAS vs RandomNAS-OGL/GDAS-OGL and with/without OGL comparisons, so missing-OGL-ablation is counterevidenced.
- `fGXyvmWpw6 / local_virtual_data_regularization`: paper has regularization ablation / `without regularization` evidence.
- `QAgwFiIY4p / additional benchmark dataset matching claim scope`: generic robustness target without concrete dataset/domain/protocol.

P28.2 code changes:

- missing-ablation target must be bound to current-paper claim/inventory context;
- explicit `with/without <target>` comparisons count as ablation counterevidence even without the word `ablation`;
- regularization ablation text resolves missing-regularization ablation claims;
- generic additional-benchmark claim-scope targets are not concrete enough for verified robustness/generalization issues.

P28.2 recompute metrics:

- Overall protection: PASS.
- `verified_review_issue_count=8`
- `verified_review_issue_cluster_count=6`
- `reviewer_candidate_review_issue_cluster_count=5`
- `claim_obligation_review_issue_cluster_count=0`
- `review_negative_verified_count=1`
- `review_issue_cluster_type_missing_ablation=3`
- `review_issue_cluster_type_missing_baseline=1`
- `review_issue_cluster_type_reproducibility_gap=1`
- `negative_evidence_unlinked_to_flaw=0`
- `positive_or_neutral_negative_candidate_count=0`
- `semantic_negative_without_review_relation_count=0`
- `mark_contested_commit_count=8`
- `recovery_case_verified_review_issue_repair=2`

Interpretation:

- P28.2 is a precision checkpoint, not a quantity win. It provides a cleaner lower-bound set of 6 system-clustered review-worthy issues after manual-audit-driven guard fixes.
- Do not loosen these guards to recover count. The next quantity work should improve reviewer-candidate recall for concrete paper-bound issues and stronger recovery bridge coverage.
- Paper-facing wording should not claim "10 verified true defects" for P28.1. Safer wording: P28.2 retains 6 high-confidence clusters after strict protection and manual-audit-driven precision filtering, with additional candidate recall work still needed.

### 2026-06-30 P28.3 Prompt-discovery + fragment guard recompute on new hardneg20

P28.3 ran a new MiMo hardneg20 sample with prompt-discovery changes and then applied a fresh offline precision recompute.

Run source:

- first API attempt: `mimo_v25_negqty_recoverycap_guard3_qhyg_targetneg_freeformrevneg_reviewissuebundle_hardneg20_mt7_b4w2_api2_r8t600_tok1536_20260630_013639.jsonl` wrote 4/20 rows, then failed after repeated MiMo `Connection error` retries;
- remaining run: `mimo_v25_p28_promptdisc_rem16_hardneg20_mt7_b1w2_api1_r20t600_tok1536_20260630_104423.jsonl` completed the remaining 16 rows;
- combined authoritative source: `P28_3_PROMPTDISC_COMBINED_20260630_013639_104423_HARDNEG20.jsonl`.

Current recompute artifacts:

- dashboard: `P28_3_FRAGMENTGUARD_RECOMPUTE_20260630_HARDNEG20_DASHBOARD.md/json`
- audit: `P28_3_FRAGMENTGUARD_RECOMPUTE_20260630_HARDNEG20_AUDIT.json`
- review issue cases: `P28_3_FRAGMENTGUARD_RECOMPUTE_20260630_REVIEW_ISSUE_CASE_TABLE.md/json`
- recovery cases: `P28_3_FRAGMENTGUARD_RECOMPUTE_20260630_RECOVERY_CASE_TABLE.md/json`

Code changes in this checkpoint:

- Critique review-issue discovery prompt now prefers exact paper-named baseline/method/component/dataset/protocol/resource targets and forbids vague targets such as `specific metric table`, `named benchmark`, `GNN`, `LLM`, `UDA`, generic `component/module`.
- Deterministic reproducibility seeding was added but then tightened with stopwords, generic target rejection, complex-method checks, and detail counterevidence. Offline recompute showed it is safe but currently not a quantity driver.
- Missing-ablation target guard now rejects malformed paper-text fragments such as `g$ and network`, strips action shells such as `which employs`, `employs`, `with`, `have designed`, and rejects generic `transformer-based network` targets.
- Prediction-head subtargets such as `biases in the prediction head`, `implement a small prediction head`, and `Weighted BCE Loss` cluster under `acceptance_prediction_head` instead of inflating separate issue clusters.
- OGL subtargets such as `base vectors of the gradient` / `pre-constructed gradient` map back to `orthogonal_gradient_learning`, and full-text `with/without OGL` or `RandomNAS/GDAS` vs `*-OGL` comparisons count as counterevidence.
- Ablation counterevidence matching is now local to the ablation/removal signal. A distant mention of the target elsewhere in the paper no longer makes an unrelated ablation table resolve the missing target.
- Component-anchor extraction now prefers current-paper definition sentences before generic first target hits, preventing claim-summary or related-work snippets from becoming inventory anchors.
- `scripts/audit_review_issue_case_table_v1.py` now clears cached `decision_hygiene` before recomputing, matching dashboard/recovery fresh recompute semantics.

P28.3 fragment-guard recompute metrics:

- Overall protection: PASS.
- `negative_evidence_unlinked_to_flaw=0`
- `semantic_negative_without_review_relation_count=0`
- `positive_or_neutral_negative_candidate_count=0`
- `review_negative_verified_count=1`
- `verified_review_issue_count=10` (dashboard row count; includes direct quote lane)
- `verified_review_issue_cluster_count=7`
- `duplicate_review_issue_row_count=3`
- `reviewer_candidate_review_issue_count=9`
- `reviewer_candidate_review_issue_cluster_count=6`
- `claim_obligation_review_issue_count=0`
- `review_issue_candidate_total=82`
- `review_issue_candidate_verified=9`
- `review_issue_candidate_counterevidence_rejected=33`
- `review_issue_candidate_missing_inventory_rejected=22`
- `review_issue_candidate_review_worthiness_rejected=8`
- `review_issue_candidate_missing_ablation_target_rejected=7`
- `mark_contested_commit_count=4`
- `recovery_case_verified_review_issue_repair=4`

Fresh case-table clusters after guard:

- direct quote protocol risk: `uOrfve3prk / evaluation_protocol_risk`
- reviewer-candidate missing ablation: `9zEBK3E9bX / occupancy_prediction_pretraining_task`
- reviewer-candidate missing ablation: `WpXq5n8yLb / recurrent_draft_model`
- reviewer-candidate missing ablation: `NnExMNiTHw / acceptance_prediction_head` (3 rows, 1 cluster)
- reviewer-candidate missing ablation: `a6SntIisgg / two-branch_encoder` (dashboard counts 2 rows, 1 cluster; case table dedups case rows)
- reviewer-candidate missing ablation: `mHv6wcBb0z / generalized_noise_regularization`
- reviewer-candidate missing baseline: `YXn76HMetm / EqualAL baseline`

Interpretation:

- P28.3 is a modest quantity gain over the P28.2 clean lower bound: `verified_review_issue_cluster_count` improves from 6 to 7 while protection remains PASS and `mark_contested` recovery stays at 4 verified-review-issue repairs.
- It is not a big quantity breakthrough. The strict story is "7 system-clustered verified review issue clusters after fragment guard", not "10 independent true defects".
- Missing-ablation remains dominant. Next quantity work should improve entity-level obligation diversity and normalized inventory coverage for baseline/protocol/reproducibility/efficiency issues, not loosen missing-ablation or direct quote-negative gates.

### 2026-06-30 P28.4 Reproducibility counterevidence precision fix

P28.4 is an offline recompute on the same P28.3 combined hardneg20 source. It fixes one verifier over-rejection: `reproducibility_gap` full-text counterevidence used to treat ordinary method/architecture text containing broad `training` wording as if it satisfied missing training configuration details. The new rule requires actual configuration evidence for configuration-style missing items: optimizer, learning rate, batch size, epochs, random seed, explicit implementation/training details, code release, GitHub, or equivalent config terms.

Artifacts:

- dashboard: `P28_4_REPROFIX_RECOMPUTE_20260630_HARDNEG20_DASHBOARD.md/json`
- audit: `P28_4_REPROFIX_RECOMPUTE_20260630_HARDNEG20_AUDIT.json`
- review issue cases: `P28_4_REPROFIX_RECOMPUTE_20260630_REVIEW_ISSUE_CASE_TABLE.md/json`
- recovery cases: `P28_4_REPROFIX_RECOMPUTE_20260630_RECOVERY_CASE_TABLE.md/json`

Validation:

- focused reproducibility tests were run by direct function invocation because this shell lacks `pytest`;
- `py_compile` passed for `state.py`, `tests/test_review_decision_hygiene.py`, and dashboard/case/recovery scripts;
- dashboard recompute used `--fail-on-violation` and passed.

P28.4 metrics vs P28.3:

- protection remains PASS;
- `negative_evidence_unlinked_to_flaw=0`;
- `semantic_negative_without_review_relation_count=0`;
- `positive_or_neutral_negative_candidate_count=0`;
- `review_negative_verified_count=1` unchanged;
- `verified_review_issue_count=10 -> 11`;
- `verified_review_issue_cluster_count=7 -> 8`;
- `reviewer_candidate_review_issue_count=9 -> 10`;
- `reviewer_candidate_review_issue_cluster_count=6 -> 7`;
- `mark_contested_commit_count=4` unchanged;
- `recovery_case_verified_review_issue_repair=4` unchanged.

New retained cluster:

- `GE6iywJtsV / reproducibility_gap / implementation_reproducibility_details`: the claim anchors `Diff-Shape` / `Graph ControllNet`; observed inventory locates the method architecture; manual grep found no learning rate, optimizer, batch size, epoch, seed, hyperparameter, implementation details, training details, configuration, GitHub, or code-release evidence. This is defensible as a reviewer issue but does not create a new recovery repair in the already completed run.

Interpretation:

- P28.4 is a small precision-preserving quantity gain, not a breakthrough. Paper-facing count should be "8 clustered verified review issues on this recompute", with direct quote negatives still rare and missing-ablation still dominant.
- The next real quantity lever is still better entity/inventory discovery for baseline, protocol, reproducibility, and efficiency issues in fresh API runs; do not loosen direct quote-negative or missing-ablation gates.

### 2026-06-29 P28 canonical checkpoint: missing-ablation target-quality guard

Current P28 code path:

- entity-level `claim_obligations` are derived from real paper claims only; fallback/context/synthetic claims remain excluded;
- normalized `evaluation_inventory` now exposes inventory buckets plus `inventory_items` with `inventory_type`, `observed_entity`, `claim_ids`, copied quote/list/table anchor, and locator;
- Critique issue discovery prompt is slot-based and can bind `obligation_id`, but candidate hints remain non-evidence;
- obligation-grounded `review_issue_bundle` verification stays separate from direct quote negatives;
- final view/dashboard report `verified_review_issue_count`, candidate funnel metrics, `claim_obligation_review_issue_count`, `reviewer_candidate_review_issue_count`, and `verified_issue_without_recovery_count`;
- recovery bridge schedules non-destructive `mark_contested` for claims with verified positive support plus same-claim verified review issue evidence; it does not change claim status.
- missing-ablation now has a target-quality gate: `high` / `medium` targets can count as verified review issues, while `low` / `reject` targets stay out of `verified_review_issue_count`.
- The gate rejects generic architecture/action targets such as `decoder`, `Encoder`, `convolutional network`, `predicts a textual representation`, and `is trained with full-batch gradient`; it preserves named or mechanistic targets such as `acceptance prediction head`, `orthogonal gradient`, `generalized noise regularization`, `LoRA module`, and paper-specific mechanism/loss/objective/head/stage/branch targets.

Latest P28 hardneg20 source run and canonical recompute:

- source run: `mimo_v25_negqty_recoverycap_guard3_qhyg_targetneg_freeformrevneg_reviewissuebundle_hardneg20_mt7_b4w2_api2_r8t600_tok1536_20260628_093956.jsonl`
- canonical dashboard: `P28_CANONICAL_HARDNEG20_DASHBOARD.md/json`
- canonical audit: `P28_CANONICAL_HARDNEG20_AUDIT.json`
- canonical review issue cases: `P28_CANONICAL_REVIEW_ISSUE_CASE_TABLE.md/json`
- canonical recovery cases: `P28_CANONICAL_RECOVERY_CASE_TABLE.md/json`
- fresh API run: `mimo_v25_negqty_recoverycap_guard3_qhyg_targetneg_freeformrevneg_reviewissuebundle_hardneg20_mt7_b4w2_api2_r8t600_tok1536_20260629_202551.jsonl`
- fresh dashboard: `P28_TARGETGUARD_FRESH_202551_HARDNEG20_DASHBOARD.md/json`
- fresh audit: `P28_TARGETGUARD_FRESH_202551_HARDNEG20_AUDIT.json`
- fresh review issue cases: `P28_TARGETGUARD_FRESH_202551_REVIEW_ISSUE_CASE_TABLE.md/json`
- fresh recovery cases: `P28_TARGETGUARD_FRESH_202551_RECOVERY_CASE_TABLE.md/json`

Canonical metrics after missing-ablation target-quality guard:

- `verified_review_issue_count=22`
- `review_negative_verified_count=0`
- `reviewer_candidate_review_issue_count=17`
- `claim_obligation_review_issue_count=5`
- `review_issue_candidate_total=64`
- `review_issue_candidate_verified=17`
- `review_issue_type_missing_ablation=11`
- `verified_missing_ablation_high_confidence=7`
- `verified_missing_ablation_medium_confidence=4`
- `review_issue_candidate_missing_ablation_target_rejected=3`
- `review_issue_candidate_missing_ablation_weak_action_rejected=1`
- `mark_contested_commit_count=12`
- `turns_with_verified_review_issue_bundle_evidence=4`
- `negative_evidence_unlinked_to_flaw=0`
- `positive_or_neutral_negative_candidate_count=0`

Fresh API 202551 metrics after the same guard:

- `verified_review_issue_count=19`
- `review_negative_verified_count=0`
- `reviewer_candidate_review_issue_count=19`
- `claim_obligation_review_issue_count=0`
- `review_issue_candidate_total=91`
- `review_issue_candidate_verified=19`
- `review_issue_type_missing_ablation=15`
- `verified_missing_ablation_high_confidence=12`
- `verified_missing_ablation_medium_confidence=3`
- `review_issue_candidate_missing_ablation_target_rejected=3`
- `review_issue_candidate_missing_ablation_weak_action_rejected=2`
- `review_issue_candidate_missing_ablation_generic_component_rejected=1`
- `mark_contested_commit_count=8`
- `turns_with_verified_review_issue_bundle_evidence=6`
- `negative_evidence_unlinked_to_flaw=0`
- `positive_or_neutral_negative_candidate_count=0`
- `evidence_json_fallback_rate_pct=0`
- The source `.jsonl` was generated before the final weak-action extension that rejects `study ...` / `fed ...` missing-ablation targets. Treat the recomputed `P28_TARGETGUARD_FRESH_202551_*` dashboard/case/recovery artifacts as authoritative for this checkpoint; raw embedded `final_report` text in the source jsonl can still contain pre-recompute live-report wording.

Important interpretation:

- 093956 proved the reviewer-candidate path, normalized inventory bridge, and recovery bridge are active. The prior "candidate recall too low" diagnosis is stale for current artifacts.
- The current bottleneck is precision, specifically template-like `missing_ablation` targets. The canonical guard reduces 31 raw verified issues to 22, and the fresh API run lands at 19, while keeping quantity above the paper-facing target and removing the obvious generic/action false positives (`decoder`, `Encoder`, `convolutional network`, `predicts a textual representation`, `is trained with full-batch gradient`, `study the square loss`, `fed into the trainable module`).
- Direct quote-grounded negatives remain rare (`review_negative_verified_count=0`). The defensible paper narrative is obligation-grounded review issue bundles, not copied negative quotes.
- Recovery still needs interpretation: canonical has `mark_contested_commit_count=12`, fresh has `mark_contested_commit_count=8`, and fresh recovery case table has 6 current verified-review-issue repairs. Do not use stale absence repairs as evidence of current verified issue recovery.
- Next work should manually audit the 19 fresh issue cases, especially medium-confidence missing-ablation targets and gradient/RNN-style targets, before treating the result as paper-ready.

### 2026-06-27 P28 follow-up: reviewer-candidate inventory bridge

Implemented after the P28 audit found `review_issue_candidate_total=4` but all four reviewer candidates were rejected for missing inventory anchors:

- `review_issue_slots` is now accepted as a fixed-slot Critique output shape and flattened into the existing `reviewer_negative_candidates` path. The old `review_issue_candidates` list remains supported for compatibility.
- Candidate observed inventory can cite `inventory_id` / `inventory_ref` without copying the quote. The verifier resolves the id against normalized inventory and still requires the resolved quote to be paper-locatable.
- Reviewer candidates that omit `observed_inventory` now get one deterministic inventory recheck before `missing_inventory` rejection. The recheck ranks same-claim inventory first, then type-matching paper inventory, and still runs the normal bundle gates: real claim anchor, concrete missing item, relevant/verifiable inventory, missing item not already observed, and full-text counterevidence.
- Review-issue discovery targets now expose an `inventory_menu` with `menu_id`, `inventory_id`, `inventory_type`, requirement types, locator, observed items, and copied quote so the model can bind candidates to inventory anchors instead of paraphrasing long context.
- Dashboard aggregation now exposes `verified_issue_contested_repair` and `stale_absence_contested_repair` so paper-facing recovery tables do not mix current verified issue repairs with stale absence-audit repairs.

Validation so far:

- `/opt/miniconda3/envs/DrMAS/bin/python -m pytest tests/test_review_decision_hygiene.py tests/test_review_inference_runner.py -q --tb=short` -> `611 passed`.
- This has not yet been re-run on hardneg20. Treat it as an engineering bridge for candidate-to-inventory binding, not as evidence that review issue recall has improved.

### 2026-06-27 COUNTERFIX1 hardneg20 checkpoint

Run and artifacts:

- combined API run: `mimo_v25_negqty_recoverycap_guard3_qhyg_targetneg_freeformrevneg_reviewissuebundle_hardneg20_issdisc1_combined20_mt7_tok1536_20260627_133540_140644.jsonl`
- dashboard: `mimo_v25_negqty_recoverycap_guard3_qhyg_targetneg_freeformrevneg_reviewissuebundle_hardneg20_issdisc1_combined20_mt7_tok1536_20260627_133540_140644_COUNTERFIX1_RECOMPUTE_VS_CANDKEY2_113021_DASHBOARD.md`
- review issue cases: `mimo_v25_negqty_recoverycap_guard3_qhyg_targetneg_freeformrevneg_reviewissuebundle_hardneg20_issdisc1_combined20_mt7_tok1536_20260627_133540_140644_COUNTERFIX1_RECOMPUTE_REVIEW_ISSUE_CASES.md`
- recovery cases: `mimo_v25_negqty_recoverycap_guard3_qhyg_targetneg_freeformrevneg_reviewissuebundle_hardneg20_issdisc1_combined20_mt7_tok1536_20260627_133540_140644_COUNTERFIX1_RECOMPUTE_RECOVERY_CASE.md`

Run construction:

- first run `20260627_133540` used the standard hardneg20 parameters (`DRMAS_NEG_QUOTE_HYGIENE=1`, `DRMAS_TARGETED_NEGATIVE_SEARCH=1`, `DRMAS_FREEFORM_REVIEWER_NEGATIVE=1`, `DRMAS_REVIEW_ISSUE_BUNDLE=1`, `max_turns=7`, `max_tokens=1536`, `API_MAX_WORKERS=2`, `API_MAX_RETRIES=8`) and completed the first 8 papers before MiMo 429 exhausted a Review Manager request.
- remaining 12 papers were run as `20260627_140644` with `API_MAX_WORKERS=1`, `API_MAX_RETRIES=12`, `API_TIMEOUT=600`, then merged in original dataset order.
- This is a valid combined hardneg20 result for review-state auditing, but runtime was affected by heavy MiMo 429 throttling.

Key metrics after COUNTERFIX1 recompute:

- protection PASS
- `real_strong_support_total=88`
- strict quote lane: `review_negative_verified_count=2`
- issue-bundle lane: `verified_review_issue_count=6`
- `quote_grounded_review_issue_count=2`
- `obligation_grounded_review_issue_count=4`
- `reviewer_candidate_review_issue_count=4`
- `claim_obligation_review_issue_count=0`
- `negative_evidence_candidate_count=6`
- `negative_evidence_unlinked_to_flaw=0`
- `verified_actionable_negative_flaw_count=5`
- `potential_concern_count=5`
- `mark_contested_commit_count=1`
- recovery case table: `verified_review_issue_repair=1`, `verified_review_negative_repair=0`

Interpretation:

- ISSUEDISC1's API run shows the new discovery prompt can produce real reviewer-candidate issues, but the raw post-run verifier was too conservative: before COUNTERFIX1 recompute the same run had only `verified_review_issue_count=3`.
- COUNTERFIX1 restores several real reviewer-discovered issues by narrowing counterevidence rather than loosening the evidence contract. It recovers the issue count to 6, with all 4 obligation-grounded cases coming from reviewer candidates rather than claim-obligation fallback.
- It still does not match CANDKEY2's `verified_review_issue_count=8` and recovery is clearly too weak (`mark_contested_commit_count=1`, `verified_review_issue_repair=1`). Do not freeze this version as final.
- Current best reading: discovery quality is improving, verifier quality is safer, but recovery scheduling/final-view integration is now the main bottleneck. Verified issue evidence exists in final audit, but recovery often records diagnosis-pending or rejects patches instead of contesting supported claims around verified issue bundles.

Representative COUNTERFIX1 cases:

- `uOrfve3prk`: reviewer-candidate insufficient evaluation / protocol risk around intervention-target diversity and causal intervention assumptions.
- `NnExMNiTHw`: reviewer-candidate insufficient evaluation for maximum candidate length sensitivity and missing ablation isolating the acceptance probability predictor.
- `fGXyvmWpw6`: strict quote-grounded efficiency/cost issue.

本轮代码变动逻辑:

- Expanded missing-ablation specificity so concrete component targets like acceptance predictor, policy, representation, alignment, descriptor, and coordinate are not dropped as generic ablation labels.
- Tightened full-text counterevidence for reviewer-inferred issues:
  - a linear-target evaluation no longer resolves a missing non-linear-target evaluation;
  - a general intervention evaluation no longer resolves missing diverse intervention-target robustness unless the paper actually evaluates diverse intervention targets;
  - mere causal-intervention method text no longer resolves a missing confounding/OOD protocol analysis unless it contains an actual analysis/evaluation.
- The validator remains strict: generic labels still fail; candidate hints are not evidence; verified issue bundles still require claim anchor + observed inventory + concrete missing/mismatch item + no current counterevidence.

Validation:

- `python3 -m py_compile agent_system/environments/env_package/review/state.py tests/test_review_decision_hygiene.py scripts/dashboard_run_comparison_v1.py scripts/audit_review_issue_case_table_v1.py scripts/audit_recovery_case_table_v1.py`
- Direct new test-function calls passed:
  - `test_review_issue_specificity_accepts_predictor_ablation_target`
  - `test_review_issue_counterevidence_does_not_resolve_nonlinear_gap_with_linear_result`
  - `test_review_issue_protocol_counterevidence_requires_confounding_analysis`
- Dashboard recompute with `--fail-on-violation` passed.

Next required work:

- Recovery: make verified review issue bundle evidence a stronger mark-contested target without allowing fallback/context claim status patches.
- Final-view/recovery audit: distinguish "verified issue exists but no recovery action was scheduled" from verifier failure.
- Discovery: continue improving candidate generation for missing baseline/ablation/result-claim mismatch, but do not relax bundle verification or count generic gaps.

### 2026-06-27 ISSUEDISC1 hardneg20 checkpoint (previous code + offline recompute)

Run and artifacts:

- base run: `mimo_v25_negqty_recoverycap_guard3_qhyg_targetneg_freeformrevneg_reviewissuebundle_hardneg20_mt7_b4w2_api2_r8t600_tok1536_20260627_113021.jsonl`
- dashboard: `mimo_v25_negqty_recoverycap_guard3_qhyg_targetneg_freeformrevneg_reviewissuebundle_hardneg20_mt7_b4w2_api2_r8t600_tok1536_20260627_113021_ISSUEDISC1_RECOMPUTE_VS_101215_DASHBOARD.md`
- review issue cases: `mimo_v25_negqty_recoverycap_guard3_qhyg_targetneg_freeformrevneg_reviewissuebundle_hardneg20_mt7_b4w2_api2_r8t600_tok1536_20260627_113021_ISSUEDISC1_RECOMPUTE_REVIEW_ISSUE_CASES.md`
- recovery cases: `mimo_v25_negqty_recoverycap_guard3_qhyg_targetneg_freeformrevneg_reviewissuebundle_hardneg20_mt7_b4w2_api2_r8t600_tok1536_20260627_113021_ISSUEDISC1_RECOMPUTE_RECOVERY_CASE.md`

ISSUEDISC1 is a discovery-quality change, not a verifier-relaxation change. It is meant to make the next API run produce better reviewer-discovered issue candidates.

Key offline recompute metrics on the 113021 hardneg20 run:

- protection PASS
- `review_negative_verified_count=1`
- `verified_review_issue_count=8`
- `obligation_grounded_review_issue_count=7`
- `reviewer_candidate_review_issue_count=4`
- `claim_obligation_review_issue_count=3`
- `negative_evidence_candidate_count=8`
- `negative_evidence_unlinked_to_flaw=0`
- `verified_actionable_negative_flaw_count=12`
- `potential_concern_count=12`
- `mark_contested_commit_count=10`
- recovery case table: `verified_review_issue_repair=4`, `verified_review_negative_repair=1`

Interpretation:

- The offline metrics are intentionally unchanged from CANDKEY2 because the changed logic mainly affects future model outputs. The recompute validates that the new guards do not break existing verified issue bundles or protection lines.
- The immediate problem being fixed is candidate wording that treats retrieval/context limits as paper flaws, e.g. "provided excerpt is truncated" or "current inventory does not show X". Those are not valid review issues.
- The next API run should be judged on whether reviewer-discovered candidates become more concrete paper-side obligation/inventory mismatches, not on direct quote-negative count alone.

本轮代码变动逻辑:

- Added `_REVIEW_ISSUE_RETRIEVAL_GAP_RE` and filtering in reviewer-negative candidate normalization and absence-gap extraction. Candidates framed as provided-excerpt/current-context/current-inventory/truncated-material gaps are rejected before they can become verified review issue inputs.
- Added non-evidence `review_issue_contrast_hints` to hard-negative/review-issue discovery targets. The hints summarize claim anchor, missing requirement types, observed inventory anchors, support source buckets, and issue seed questions so Critique can compare what the claim requires against what the paper inventory shows.
- Updated Evidence/Critique prompt rules to use `review_issue_contrast_hints` only for candidate construction and to return no candidate rather than inventing a retrieval-gap issue.
- Kept the verifier strict: verified review issue bundles still require claim anchor + observed inventory + concrete missing/mismatch item + no current counterevidence. Critique hints are not evidence.

Validation:

- `python3 -m py_compile agent_system/environments/env_package/review/state.py agent_system/review_prompts.py tests/test_review_decision_hygiene.py scripts/dashboard_run_comparison_v1.py scripts/audit_review_issue_case_table_v1.py scripts/audit_recovery_case_table_v1.py`
- Direct test-function calls passed because local Python environments lack pytest:
  - `test_reviewer_negative_candidate_normalizer_filters_retrieval_gap_framing`
  - `test_review_issue_discovery_targets_include_contrast_hints_without_verifying`
  - `test_reviewer_issue_bundle_keeps_missing_graph_tasks_when_only_node_classification_is_observed`
  - `test_reviewer_issue_bundle_rejects_missing_graph_tasks_when_all_named_tasks_are_observed`
  - `test_reviewer_candidate_same_requirement_different_issue_type_does_not_overwrite_valid_issue`
  - `test_review_issue_bundle_rejects_default_quantitative_gap_when_results_are_reported`
  - `test_review_issue_bundle_accepts_quantitative_gap_when_inventory_is_qualitative`
- Dashboard recompute with `--fail-on-violation` passed.

Next required API test:

```bash
DRMAS_NEG_QUOTE_HYGIENE=1 \
DRMAS_TARGETED_NEGATIVE_SEARCH=1 \
DRMAS_FREEFORM_REVIEWER_NEGATIVE=1 \
DRMAS_REVIEW_ISSUE_BUNDLE=1 \
API_MAX_WORKERS=2 API_MAX_RETRIES=8 API_TIMEOUT=600 MAX_TOKENS=1536 \
bash run_hardneg20_guard3.sh
```

After it finishes, regenerate dashboard + review issue case table + recovery case table and compare against CANDKEY2/ISSUEDISC1 recompute.

### 2026-06-27 CANDKEY2 hardneg20 checkpoint (previous latest API run)

Run and artifacts:

- run: `mimo_v25_negqty_recoverycap_guard3_qhyg_targetneg_freeformrevneg_reviewissuebundle_hardneg20_mt7_b4w2_api2_r8t600_tok1536_20260627_113021.jsonl`
- log: `mimo_v25_negqty_recoverycap_guard3_qhyg_targetneg_freeformrevneg_reviewissuebundle_hardneg20_mt7_b4w2_api2_r8t600_tok1536_20260627_113021.log`
- dashboard: `mimo_v25_negqty_recoverycap_guard3_qhyg_targetneg_freeformrevneg_reviewissuebundle_hardneg20_mt7_b4w2_api2_r8t600_tok1536_20260627_113021_CANDKEY2_RECOMPUTE_VS_101215_DASHBOARD.md`
- review issue cases: `mimo_v25_negqty_recoverycap_guard3_qhyg_targetneg_freeformrevneg_reviewissuebundle_hardneg20_mt7_b4w2_api2_r8t600_tok1536_20260627_113021_CANDKEY2_RECOMPUTE_REVIEW_ISSUE_CASES.md`
- recovery cases: `mimo_v25_negqty_recoverycap_guard3_qhyg_targetneg_freeformrevneg_reviewissuebundle_hardneg20_mt7_b4w2_api2_r8t600_tok1536_20260627_113021_CANDKEY2_RECOMPUTE_RECOVERY_CASE.md`

Run settings:

- `DRMAS_NEG_QUOTE_HYGIENE=1`
- `DRMAS_TARGETED_NEGATIVE_SEARCH=1`
- `DRMAS_FREEFORM_REVIEWER_NEGATIVE=1`
- `DRMAS_REVIEW_ISSUE_BUNDLE=1`
- `max_turns=7`, `max_tokens=1536`, `API_MAX_WORKERS=2`, `API_MAX_RETRIES=8`, `API_TIMEOUT=600`

Key metrics after recomputing with CANDKEY2:

- protection PASS
- `real_strong_support_total=71`
- strict quote lane: `review_negative_verified_count=1`
- issue-bundle lane: `verified_review_issue_count=8`
- `quote_grounded_review_issue_count=1`
- `obligation_grounded_review_issue_count=7`
- `reviewer_candidate_review_issue_count=4`
- `claim_obligation_review_issue_count=3`
- `total_review_negative_verified_count=8`
- `negative_evidence_candidate_count=8`
- `negative_evidence_linked_to_flaw_count=8`
- `negative_evidence_unlinked_to_flaw=0`
- `verified_actionable_negative_flaw_count=12`
- `potential_concern_count=12`
- `final_potential_concern_total=28`
- `mark_contested_commit_count=10`
- recovery case table: `verified_review_issue_repair=4`, `turns_with_verified_review_issue_bundle_evidence=5`
- protection safety lines: `positive_or_neutral_negative_candidate_count=0`, `semantic_negative_without_review_relation_count=0`

Important caveats:

- `author_limitation_only_count=2`, `negative_grounding_conflict_count=14`, and `assessment_limitation_flaw_count=29` remain elevated. They do not break protection, but they show quote-bank negative candidates still create limitation/noise pressure.
- CANDKEY2 is conservative relative to the earlier loose runs. It keeps the QUALITYFIX2 removals: generic `7Dub7UXTXN` baseline issue, `TPAj63ax4Y` default insufficient-evaluation issue, and duplicate XH3 quote-negative counting.
- The case table now separates `reviewer_candidate` issues from `claim_obligation` fallback issues. This is the main paper-narrative distinction: reviewer-candidate issues are model-proposed review concerns that survived bundle verification; claim-obligation issues are deterministic fallback gaps.
- Important reviewer-candidate cases in this recompute:
  - `uOrfve3prk` `evaluation_protocol_risk`, missing "Validation of normalized edit distance proxy against human judgment", anchored by intervention-success evaluation inventory.
  - `cklg91aPGk` `insufficient_evaluation`, missing "evaluation on link prediction task" and "evaluation on graph classification task", anchored by node-classification inventory. This case depends on exact task-phrase matching so node classification no longer counterevidences graph classification.
- Some remaining case-table items are still judgment-sensitive, especially structural efficiency/reproducibility issues; do not present this as final solved quality.
- Continue to treat `review_negative_verified_count` and `verified_review_issue_count` as separate lanes.

本轮代码变动逻辑:

- `claim_surface_profile` is used only to help Critique propose concrete reviewer issue candidates; it is not evidence and cannot by itself verify a flaw.
- The verifier still requires claim anchor + observed inventory + concrete missing/mismatch item + no current counterevidence for obligation-grounded review issues.
- BINDINGFIX1 fixes a state-sync bug exposed by `fGXyvmWpw6`: a model/quote-bank flaw reused a deterministic `flaw-reviewer-absence-*` id while pointing to the wrong claim/evidence. The deterministic reviewer-absence materializer now refuses to let non-`reviewer_absence_audit` collisions block verified issue flaw materialization.
- Flaw materialization now filters issue evidence before linking: only current, claim-aligned, verifier-passing obligation-grounded evidence can enter an absence-audit flaw.
- Existing live-state verified review issue evidence is now synchronized into a view-only `reviewer_absence_audit` flaw when no valid flaw links it, including cases where the evidence was created in an earlier turn and is not rebuilt by the current top-gap pass.
- This preserves the hard protection invariant: every counted verified review issue/negative evidence item must be linked to a valid flaw, while fake author-limitation or quote-bank candidates remain excluded from verified negative accounting.
- QUALITYFIX2 adds a stricter baseline gate: `missing_baseline` must name a concrete baseline/comparison target, not only "same-setting baseline or comparison for the claimed improvement".
- QUALITYFIX2 adds a stricter insufficient-evaluation inventory gate: problem/introduction/background text and method-overview figures cannot verify a missing quantitative-result issue unless the quote itself has result/performance/metric/experiment or numeric evidence.
- QUALITYFIX2 deduplicates direct quote-grounded negative issues by canonical claim/type/quote signature instead of evidence id or span, so overlapping copies of the same negative result count once in dashboard and case tables.
- CANDPRIORITY1 changed `_add_reviewer_absence_audit_artifacts` to prioritize reviewer-discovered candidate gaps before deterministic `verified_coverage_gap_items`; deterministic gaps fill remaining slots instead of crowding out model-proposed review issues.
- CANDPRIORITY1 added `reviewer_candidate_review_issue_count` / `claim_obligation_review_issue_count` and matching claim/type metrics so dashboard and case tables can distinguish real reviewer-discovered issues from fallback structural gaps.
- CANDKEY2 fixes same-claim/same-requirement overwrites by deduping reviewer-absence gaps on `(claim_id, requirement, negative_type)` and by including the negative type in synthetic evidence ids.
- CANDKEY2 tightens task/domain counterevidence: when a missing item names a known task phrase, each named task must be independently observed. "node classification" no longer resolves missing "graph classification" or "link prediction".
- CANDKEY2 prevents generic default `insufficient_evaluation` issues from surviving when paper inventory/full text already reports empirical results with quantitative measures. This removes the `TPAj63ax4Y` default "quantitative result table or metric" false positive.
- CANDKEY2 still allows concrete "missing quantitative metric" issues when the observed inventory is qualitative but paper-locatable and target-matched, e.g. a figure qualitatively showing the relevant phenomenon while no quantitative metric is present.

Validation:

- `python3 -m py_compile agent_system/environments/env_package/review/state.py tests/test_review_decision_hygiene.py`
- Direct test-function calls passed because local Python environments lack pytest:
  - `test_review_issue_bundle_flaw_materialization_survives_non_audit_id_collision`
  - `test_merge_review_state_materializes_verified_review_issue_bundle_for_recovery`
  - `test_review_issue_bundle_accepts_efficiency_gap_when_paper_only_says_efficient`
  - `test_review_issue_bundle_accepts_speedup_claim_efficiency_gap_without_explicit_obligation`
- Additional QUALITYFIX2 direct test-function calls passed:
  - `test_review_issue_bundle_rejects_structural_baseline_without_named_missing_target`
  - `test_review_issue_bundle_rejects_intro_problem_inventory_for_insufficient_evaluation`
  - `test_quote_grounded_review_negative_count_deduplicates_same_quote_issue`
- Additional CANDPRIORITY1 direct test-function calls passed:
  - `test_reviewer_candidate_review_issue_takes_priority_over_deterministic_gap_budget`
  - `test_review_issue_specificity_accepts_protocol_validation_dimension_not_generic_baseline`
- Additional CANDKEY2 direct test-function calls passed:
  - `test_reviewer_issue_bundle_keeps_missing_graph_tasks_when_only_node_classification_is_observed`
  - `test_reviewer_issue_bundle_rejects_missing_graph_tasks_when_all_named_tasks_are_observed`
  - `test_reviewer_candidate_same_requirement_different_issue_type_does_not_overwrite_valid_issue`
  - `test_review_issue_bundle_rejects_default_quantitative_gap_when_results_are_reported`
  - `test_review_issue_bundle_accepts_quantitative_gap_when_inventory_is_qualitative`
- Dashboard recompute with `--fail-on-violation` passed.

### 2026-06-27 STRUCTEXPECT2 hardneg20 checkpoint (previous stable baseline)

Run and artifacts:

- run: `mimo_v25_negqty_recoverycap_guard3_qhyg_targetneg_freeformrevneg_reviewissuebundle_hardneg20_mt7_b4w2_api2_r8t600_tok1536_20260627_101215.jsonl`
- log: `mimo_v25_negqty_recoverycap_guard3_qhyg_targetneg_freeformrevneg_reviewissuebundle_hardneg20_mt7_b4w2_api2_r8t600_tok1536_20260627_101215.log`
- dashboard: `mimo_v25_negqty_recoverycap_guard3_qhyg_targetneg_freeformrevneg_reviewissuebundle_hardneg20_mt7_b4w2_api2_r8t600_tok1536_20260627_101215_STRUCTEXPECT2_RECOMPUTE_VS_090139_DASHBOARD.md`
- review issue cases: `mimo_v25_negqty_recoverycap_guard3_qhyg_targetneg_freeformrevneg_reviewissuebundle_hardneg20_mt7_b4w2_api2_r8t600_tok1536_20260627_101215_STRUCTEXPECT2_RECOMPUTE_REVIEW_ISSUE_CASES.md`
- recovery cases: `mimo_v25_negqty_recoverycap_guard3_qhyg_targetneg_freeformrevneg_reviewissuebundle_hardneg20_mt7_b4w2_api2_r8t600_tok1536_20260627_101215_STRUCTEXPECT2_RECOMPUTE_RECOVERY_CASE.md`

Run settings:

- `DRMAS_NEG_QUOTE_HYGIENE=1`
- `DRMAS_TARGETED_NEGATIVE_SEARCH=1`
- `DRMAS_FREEFORM_REVIEWER_NEGATIVE=1`
- `DRMAS_REVIEW_ISSUE_BUNDLE=1`
- `max_turns=7`, `max_tokens=1536`, `API_MAX_WORKERS=2`, `API_MAX_RETRIES=8`, `API_TIMEOUT=600`

Key metrics after recomputing with the current structural-expectation verifier:

- protection PASS
- `evidence_json_fallback_rate_pct=0`
- `real_strong_support_total=73`
- strict quote lane: `review_negative_verified_count=0`
- issue-bundle lane: `verified_review_issue_count=8`, all obligation-grounded
- `reviewer_absence_verified_count=8`
- `verified_actionable_negative_flaw_count=10`
- `potential_concern_count=10`
- dashboard recovery: `mark_contested_commit_count=3`, `recovery_effective_repair=3`
- recovery case table: `verified_review_issue_repair=2`; one prior mark-contested repair is now classified as stale reviewer-absence audit after the stricter verifier
- safety lines: `negative_evidence_unlinked_to_flaw=0`, `positive_or_neutral_negative_candidate_count=0`, `semantic_negative_without_review_relation_count=0`, `author_limitation_only_count=0`

Verified issue type mix:

- `missing_ablation=2`
- `missing_baseline=1`
- `insufficient_evaluation=3`
- `efficiency_cost_gap=1`
- `method_support_gap=1`

Representative verified issue cases:

- `9zEBK3E9bX`: SECO baseline missing for a label-efficiency comparison claim.
- `XyB4VvF01X`: Graph2Tac lacks an ablation isolating the hierarchical representation component.
- `cklg91aPGk`: PROP/PROPGCL has insufficient evaluation / missing ablation concerns tied to observed result inventory.
- `QAgwFiIY4p`: PST lacks quantitative parameter or compute-cost comparison for an efficiency-relevant performance claim.
- `mHv6wcBb0z`: NR-DCCA has method-support and insufficient-evaluation issues tied to observed method/result inventory.

Why this supersedes POSTQUALITY:

- POSTQUALITY used a stricter but underpowered post-run verifier and counted only 3 issue bundles.
- STRUCTEXPECT2 allows deterministic claim-obligation structural dimensions to verify as real review issues when the claim text itself contains the matching structural cue and the paper has observed inventory but no satisfying counterevidence.
- It still rejects self-justified obligations: model-provided `coverage_tags` / `claim_obligations` cannot by themselves create a baseline/ablation/efficiency obligation.
- The previously suspicious `7Dub7UXTXN` baseline issue disappeared because `claim_type=comparison` and model-filled obligations no longer self-justify a baseline gap.
- The previously suspicious LogoRA efficiency issue disappeared because `multi-scale` no longer matches the efficiency/scalability regex.
- Full-text structural counterevidence rejects structural gaps when the paper already has relevant baseline/result/scope/efficiency evidence.

Current interpretation:

- MiMo can propose real reviewer issues; the bottleneck is not JSON parsing or model ability.
- The strict direct quote-negative lane is still empty on this run; do not treat `review_negative_verified_count=0` as failure of the whole negative story.
- The defensible main metric for paper narrative is `verified_review_issue_count=8`, not direct quote-negative count.
- The next quantity increase should come from better issue-target construction, claim-specific obligation blueprints, and richer experiment/inventory extraction, not looser verification.
- Direct quote-negative evidence is still rare. The paper narrative should use `verified_review_issue_count` as the main real-review-issue metric and keep `review_negative_verified_count` as the strict direct quote lane.

Code changes in this checkpoint:

- Added structural default missing dimensions for deterministic claim-obligation gaps, e.g. efficiency requires runtime/memory/parameter/FLOP/hardware/compute-cost evidence instead of a generic "efficiency evidence" label.
- Added structural expectation basis checks. Claim-obligation gaps can verify when the claim text itself has a matching structural cue, observed inventory exists, and no current support/counterevidence satisfies the requirement.
- Tightened structural cues: `claim_type=comparison` alone no longer creates a baseline obligation; ablation/component cues must come from claim text; `multi-scale` no longer triggers an efficiency/scalability cue.
- Preserved reviewer-candidate-specific verification: concrete reviewer-discovered missing items still require target-specific evidence/counterevidence handling and are not replaced by broad structural matching.
- Added full-text structural counterevidence windows so generic structural dimensions are rejected if the paper already contains relevant result/baseline/scope/efficiency/method evidence.
- Fixed issue-type selection so reviewer candidate issue type takes priority when it is compatible with the requirement; deterministic requirement defaults are only fallbacks.
- Follow-up target-construction change: `review_issue_discovery_targets` now include a non-evidence `claim_surface_profile` extracted from the claim text, with surface entities, comparison targets, datasets/benchmarks, components/mechanisms, metrics/protocols, and resource dimensions.
- Issue candidate blueprints now use that profile to give Critique concrete examples such as "ablation isolating Motion-Fusion", "F1 reporting protocol", "FLOPs comparison", or "coverage for DAVIS2017"; these are candidate-construction hints only and still require the existing bundle verifier.
- Added first-class method-detail and empirical-result blueprints so Critique can propose method-support and insufficient-evaluation issues from claim obligations instead of relying only on baseline/ablation/protocol/reproducibility paths.
- `REVIEW_ISSUE_DISCOVERY_PROMPT` now explicitly tells Critique that `claim_surface_profile` is not evidence and must only be used to name concrete missing/mismatch items for later verification.

本轮代码变动逻辑:

- 保留两条负向通道: `review_negative_verified_count` 只统计论文文本中直接可引用的 quote-grounded reviewer negative; `verified_review_issue_count` 统计 claim obligation + observed inventory + concrete missing/mismatch item 组成的真实审稿问题包。
- 不再把“模型提出了一个缺陷”直接算真负向。review issue bundle 必须同时满足: claim anchor 可追溯、observed inventory quote/list/table 可定位、missing/mismatch item 是具体实体或具体实验维度、并且全文/现有 inventory 没有反证。
- 对 absence / coverage 类审稿问题，本轮允许“结构性审稿义务”成为 verified review issue 的来源，但前提是 claim 正文真的提出了对应结构需求。例如 claim 说 efficient / faster 才能要求 runtime/memory/parameter/FLOP/cost evidence; claim 明确有 mechanism/component 才能要求 component-isolation ablation。
- 不允许 coverage tag、claim_obligation 字段、claim_type 字段单独自证审稿义务，避免模型先写一个 obligation 再用它证明缺陷成立。
- 上游发现层现在会把 claim 正文里的实体、数据集、组件、指标、资源维度抽成 `claim_surface_profile`，交给 Critique 作为“提出什么审稿问题”的提示。它不参与验证，不会直接提高计数，只帮助下一轮 MiMo 更像真实审稿人一样提出具体问题。
- 蓝图不再只说“缺 baseline/ablation/evaluation”，而是尽量带上 claim 表面的具体候选对象；但最终是否进入 `verified_review_issue_count` 仍由 claim anchor、observed inventory、missing/mismatch、全文反证和 freshness gate 决定。
- 新增 surface marker 匹配是为了让 `$k$ -NN`、hyphen/LaTeX 这类论文表面写法能被识别，同时避免 `SECO` 命中 `SECOND` 这类假阳性。
- 新增 bundle-level auditable expectation gate 是为了防止 reviewer candidate 自己凭空制造“应该比较某对象”的义务; 缺失对象必须能从论文 claim、paper surface 或 observed inventory 中审计出来。
- `_sync_verified_review_issues` 不再保留已经被新版 verifier 否掉的旧 `obligation_grounded_review_issue`，避免 stale issue 继续污染 final view 和 recovery case table。
- Recovery 仍只做非破坏式修复: verified review issue bundle 可以触发 `mark_contested`，但不能放开 fallback/context claim status patch，也不能把 generic gap 包装成 verified negative。

### 2026-06-27 PAPERINV9 live hardneg20 checkpoint (previous high-recall result)

Current best hardneg20 result after prompt tightening, longer missing-item preservation, truncated-item rejection, ablation counterevidence checks, and limitation/boundary claim target gating:

- run: `mimo_v25_negqty_recoverycap_guard3_qhyg_targetneg_freeformrevneg_reviewissuebundle_hardneg20_mt7_b4w2_api2_r8t600_tok1536_20260627_061606.jsonl`
- dashboard: `mimo_v25_negqty_recoverycap_guard3_qhyg_targetneg_freeformrevneg_reviewissuebundle_hardneg20_mt7_b4w2_api2_r8t600_tok1536_20260627_061606_PAPERINV9_LIVE_VS_QUOTECLASS6_DASHBOARD.md`
- recovery case: `mimo_v25_negqty_recoverycap_guard3_qhyg_targetneg_freeformrevneg_reviewissuebundle_hardneg20_mt7_b4w2_api2_r8t600_tok1536_20260627_061606_PAPERINV9_LIVE_RECOVERY_CASE.md`
- review issue case table: `mimo_v25_negqty_recoverycap_guard3_qhyg_targetneg_freeformrevneg_reviewissuebundle_hardneg20_mt7_b4w2_api2_r8t600_tok1536_20260627_061606_PAPERINV9_LIVE_REVIEW_ISSUE_CASES.md`

Run settings:

- `DRMAS_NEG_QUOTE_HYGIENE=1`
- `DRMAS_TARGETED_NEGATIVE_SEARCH=1`
- `DRMAS_FREEFORM_REVIEWER_NEGATIVE=1`
- `DRMAS_REVIEW_ISSUE_BUNDLE=1`
- `max_turns=7`, `max_tokens=1536`, `API_MAX_WORKERS=2`, `API_MAX_RETRIES=8`, `API_TIMEOUT=600`

Key metrics:

- protection PASS
- `evidence_json_fallback_rate_pct=0`
- `real_strong_support_total=81`
- `review_negative_verified_count=1`
- `verified_review_issue_count=12`
- `obligation_grounded_review_issue_count=11`
- `verified_actionable_negative_flaw_count=10`
- `potential_concern_count=10`
- `mark_contested_commit_count=3`
- `recovery_effective_repair=3`
- `recovery_case_verified_review_issue_repair=3`
- `negative_evidence_unlinked_to_flaw=0`
- `positive_or_neutral_negative_candidate_count=0`
- `author_limitation_only_count=0`

Review issue type mix:

- `missing_ablation=4`
- `missing_baseline=1`
- `unfair_or_weak_baseline=1`
- `insufficient_evaluation=1`
- `missing_robustness_or_generalization=1`
- `method_support_gap=1`
- `reproducibility_gap=2`

Current interpretation:

- The main signal is now real reviewer-discovered review issues, not paper-self-negative quotes.
- Direct quote-negative remains strict and small (`review_negative_verified_count=1`).
- Obligation-grounded issue bundles are the main paper-narrative metric (`obligation_grounded_review_issue_count=11`).
- Recovery is no longer just bookkeeping: 3 `mark_contested` repairs are tied to verified review issue bundle evidence.
- The 053028 PAPERINV live run with 14 obligation-grounded issues is superseded as a loose pre-tightening checkpoint; do not cite it as the current result without saying it was before truncated-item and limitation-claim gates.

New verifier rules added in this checkpoint:

- Preserve `missing_or_weak_items` / coverage missing items up to 160 chars instead of truncating at 80.
- Reject verified bundles when the missing/mismatch item is visibly truncated or incomplete.
- Reject missing-ablation bundles when the claim anchor or observed inventory already reports the same ablation/variant signal.
- Reject bundles targeting `claim_type=limitation_or_boundary` or claims tagged as limitation/boundary.
- Prompt now requires complete noun-phrase missing items and forbids framing an issue as "the excerpt/current inventory does not show X".
- Review issue case table now includes inventory count, inventory sources, and verification basis for manual audit.

Remaining risks:

- Some cases remain judgment-sensitive, especially method-support and reproducibility issues on theoretical/method papers.
- Full paper text is available at runtime but not persisted in `review_state.paper_text`; dashboards prove from saved evidence/inventory, not from re-reading the original full text.
- Next improvement should persist compact paper-inventory/audit snippets, not raw full paper text, so offline dashboards can prove rejection reasons and verified issue basis more completely.

### 2026-06-27 paper-inventory live hardneg20 checkpoint

Superseded loose live MiMo run after deterministic paper-inventory / issue-bundle changes:

- run: `mimo_v25_negqty_recoverycap_guard3_qhyg_targetneg_freeformrevneg_reviewissuebundle_hardneg20_mt7_b4w2_api2_r8t600_tok1536_20260627_053028.jsonl`
- dashboard: `mimo_v25_negqty_recoverycap_guard3_qhyg_targetneg_freeformrevneg_reviewissuebundle_hardneg20_mt7_b4w2_api2_r8t600_tok1536_20260627_053028_PAPERINV_LIVE_VS_QUOTECLASS6_DASHBOARD.md`
- recovery case: `mimo_v25_negqty_recoverycap_guard3_qhyg_targetneg_freeformrevneg_reviewissuebundle_hardneg20_mt7_b4w2_api2_r8t600_tok1536_20260627_053028_PAPERINV_LIVE_RECOVERY_CASE.md`
- review issue case table: `mimo_v25_negqty_recoverycap_guard3_qhyg_targetneg_freeformrevneg_reviewissuebundle_hardneg20_mt7_b4w2_api2_r8t600_tok1536_20260627_053028_PAPERINV_LIVE_REVIEW_ISSUE_CASES.md`

Key live metrics:

- protection PASS
- `evidence_json_fallback_rate_pct=0`
- `real_strong_support_total=90`
- `review_negative_verified_count=0`
- `verified_review_issue_count=14`
- `obligation_grounded_review_issue_count=14`
- `verified_actionable_negative_flaw_count=12`
- `potential_concern_count=12`
- `mark_contested_commit_count=6`
- `recovery_effective_repair=6`
- `recovery_case_verified_review_issue_repair=6`
- `diagnosis_pending_potential_concern_count=71`

What changed:

- Added deterministic `paper_text_inventory` into `evaluation_inventory`, derived directly from full paper text. It records table/figure/experiment/method/protocol/efficiency anchors only; it is descriptive inventory, not support evidence and not negative evidence.
- Review issue bundle verification can now use verified support inventory, candidate observed inventory, or deterministic paper inventory as the observed-inventory side of a claim-obligation mismatch.
- Claim-restatement filtering prevents the claim sentence itself from becoming paper inventory.
- Issue-type relevance gates prevent theory/proof snippets from validating missing baseline/efficiency/ablation issues.
- Missing-item freshness now checks distinctive coverage tokens, so a missing heterophily/dataset-style issue is rejected if that exact entity is already present in observed inventory.
- Review issue case table now deduplicates obligation-grounded issues by paper/claim/type/missing item instead of by evidence id.

Interpretation:

- This is the first run where the paper narrative is working in the intended lane: real reviewer issues are mostly obligation-grounded bundles, not copied negative quotes.
- `review_negative_verified_count=0` is expected here; the direct quote-negative lane remains strict.
- The improvement is material versus strict-anchor (`verified_review_issue_count 2 -> 14`, `verified_review_issue_repair 2 -> 6`) without breaking protection.
- Remaining risk: some obligation-grounded cases are still judgment-sensitive. They should be manually audited before treating this as a frozen paper result, especially method-support and result-claim-mismatch cases.

### 2026-06-27 hardneg20 strict-anchor checkpoint

Latest real MiMo run:

- run: `mimo_v25_negqty_recoverycap_guard3_qhyg_targetneg_freeformrevneg_reviewissuebundle_hardneg20_mt7_b4w2_api2_r8t600_tok1536_20260627_041303.jsonl`
- dashboard: `mimo_v25_negqty_recoverycap_guard3_qhyg_targetneg_freeformrevneg_reviewissuebundle_hardneg20_mt7_b4w2_api2_r8t600_tok1536_20260627_041303_STRICTANCHOR3_VS_QUOTECLASS6_DASHBOARD.md`
- recovery case: `mimo_v25_negqty_recoverycap_guard3_qhyg_targetneg_freeformrevneg_reviewissuebundle_hardneg20_mt7_b4w2_api2_r8t600_tok1536_20260627_041303_STRICTANCHOR3_RECOVERY_CASE.md`
- review issue case table: `mimo_v25_negqty_recoverycap_guard3_qhyg_targetneg_freeformrevneg_reviewissuebundle_hardneg20_mt7_b4w2_api2_r8t600_tok1536_20260627_041303_STRICTANCHOR3_REVIEW_ISSUE_CASES.md`

Strict-anchor recompute metrics:

- protection PASS
- `evidence_json_fallback_rate_pct=0`
- `real_strong_support_total=66`
- `review_negative_verified_count=0`
- `verified_review_issue_count=2`
- `obligation_grounded_review_issue_count=2`
- `verified_actionable_negative_flaw_count=3`
- `potential_concern_count=3`
- `mark_contested_commit_count=5`
- `recovery_effective_repair=5`
- `recovery_case_verified_review_issue_repair=2`
- `diagnosis_pending_potential_concern_count=81`

Interpretation:

- The system is now safer than the earlier loose bundle view, but true verified review issue recall is still too low.
- Several initially counted cases were false positives caused by locatable but off-target inventory anchors: theorem/proof snippets for baseline/efficiency, data-statistics captions for method pipeline concerns, and efficiency quotes that already reported time/memory.
- The verifier now rejects those with issue-type-specific inventory relevance and "missing item already observed" checks.
- This exposes the real bottleneck: issue discovery and inventory construction are not structured enough. The next architectural step is not to relax bundle gates; it is to add stronger claim-obligation extraction and paper evaluation/method inventory passes so Critique proposes concrete, auditable missing items with the correct inventory anchor.

### 1. Quote-grounded reviewer negative

This is the strictest lane and is the only thing that may count as `review_negative_verified_count`.

Required properties:

- Evidence Agent or normalized evidence payload supplies a real paper-side quote:
  - `negative_quote`, `raw_quote`, or equivalent copied paper text.
  - locator / section / span information.
- The evidence is bound to an auditable real paper claim and flaw:
  - `claim_id`
  - `flaw_id`
  - `negative_type`
  - weakened dimension / reason.
- The verifier accepts paper grounding and review-negative semantics:
  - paper-grounded quote match, not merely model judgment.
  - semantic relation is a reviewer criticism of a claim, not a neutral observation.
  - evidence is linked to the flaw it is supposed to support.

Hard rejects for this lane:

- author self-limitations, future-work statements, or limitations-section text presented as if it were reviewer-discovered criticism;
- internal ablation/variant/results text that only says one variant is weaker than another;
- generic gaps without a concrete claim/flaw/quote/locator chain;
- Critique-only/model-only judgments without copied paper evidence;
- quote-bank salvage that fabricates negative semantics;
- fallback/context/synthetic claim status patch or downgrade.

Expected metric behavior:

- `review_negative_verified_count` only counts this lane.
- `negative_evidence_unlinked_to_flaw` must stay 0.
- `semantic_negative_without_review_relation_count` must stay 0.
- These records can support quote-grounded negative flaw promotion and recovery case type `verified_review_negative_repair`.

### 2. Obligation-grounded reviewer issue bundle

This lane handles real reviewer concerns that are usually not directly quote-negative, such as missing baseline, missing ablation, insufficient evaluation, missing reproducibility detail, or coverage gaps.

Source of truth:

- deterministic claim-requirement / coverage audit over an auditable real paper claim;
- Critique/reviewer candidate names a concrete missing or mismatched item, not a generic requirement label;
- observed inventory is anchored in verified support inventory or a candidate-supplied copied paper quote/list/table that the verifier can locate in full paper text;
- the claim still lacks the required evidence type after freshness re-check.

Current behavior:

- It may produce final-view potential concerns and review-issue metrics:
  - `reviewer_absence_verified_count`
  - `obligation_grounded_review_issue_count`
  - `verified_review_issue_count`
  - `total_review_negative_verified_count`
  - `verified_negative_flaw_count`
  - `verified_actionable_negative_flaw_count`
  - `potential_concern_count`
  - `final_potential_concern_total`
- It must not increment `review_negative_verified_count`.
- It must not be mixed into quote-grounded verified negative evidence.
- Runtime `mark_contested` may use a fresh final-view reviewer absence audit finding as evidence for a non-destructive contested relation.
- When such a recovery commit succeeds, the absence audit snapshot is persisted into `evidence_map` so the recovery case table has a real evidence object instead of `missing_evidence_id`.
- Absence/issue bundle records bypass negative-quote grounding only because their verification basis is claim obligation + observed paper inventory, not a copied negative quote.
- A freshness gate must re-check support inventory. If the missing requirement is later satisfied, the snapshot becomes stale and must not count.

Expected metric behavior:

- Recovery case audit labels these as `verified_review_issue_repair` / `obligation_grounded_review_issue`.
- `recovery_case_effective_repair_without_verified_negative` should stay 0.
- Stale snapshots should be visible as `stale_reviewer_absence_audit`, not counted as clean negative repair.

### 3. Diagnosis-pending potential concern

Generic claim-obligation gaps, model-only review suspicions, or candidates missing concrete observed inventory remain diagnosis-pending. They may be useful in the final report as potential concerns, but they must not count as verified review issues or quote-grounded negative evidence.

### Final and recovery routing

- Quote-grounded negatives and fresh reviewer-inferred absence findings may both surface as final potential concerns.
- `mark_contested` is the preferred non-destructive recovery operation when a claim has real support plus a verified negative/absence concern.
- `mark_contested` must not change claim status.
- `record_diagnosis_pending_concern` is a state record, not an effective repair.
- Recovery effective repair must be backed by either quote-grounded reviewer negative evidence or fresh obligation-grounded review issue evidence.
- Do not increase negative/recovery counts by weakening verifier gates. If quote-grounded negatives remain 0, the fix is better reviewer critique discovery plus evidence retrieval, not metric relabeling.

## Current Mainline

Use qhyg as the clean mainline layer:

```bash
DRMAS_NEG_QUOTE_HYGIENE=1
```

MiMo runs should use:

```bash
--api-provider mimo
--api-model mimo-v2.5
--model-adapter-mode small_model
--max-tokens 1536
--max-turns 7
--manager-batch-size 4
--api-timeout 600
--api-max-retries 10
```

For smoke8, `--api-max-workers 2` is safer. For hardneg20/full39, larger workers can be tried after confirming the endpoint is stable. Legacy `max_tokens=768` is too truncation-prone for evidence JSON and should not be used for negative-evidence validation unless intentionally reproducing an old run.

## Latest State: 2026-06-27

Active project directory: `/Users/zss/Downloads/zssmas-codex-p26-optimization-20260524`. Do not use `/Users/zss/Downloads/DrMAS-master`; it is stale.

Current effective code changes:

- `DRMAS_REVIEW_ISSUE_BUNDLE=1` is the current mainline direction.
- ReviewState now carries derived `evaluation_inventory` from verified support evidence. This is a stable inventory of observed paper evidence, not a new LLM judgment.
- Claim targets shown to Critique now include:
  - `claim_obligations`
  - `missing_requirements`
  - `verified_support_inventory`
  - `paper_evaluation_inventory`
- Critique `review_issue_candidates` may include `observed_inventory` with a copied table/list/experiment quote and locator.
- The verifier can now accept obligation-grounded issue bundles when candidate `observed_inventory` is locatable in full paper text, even if the quote is not a negative quote.
- Candidate inventory is rejected if the quote cannot be located in the paper.
- Candidate missing/mismatch items that only restate a requirement label, such as `ablation or component-isolation evidence` or `result/table/experiment evidence`, are rejected. A verified review issue must name a concrete baseline, component, dataset, metric, protocol, cost item, method detail, or reproducibility detail.
- Generic obligation-only gaps remain diagnosis-pending and do not count as verified review issues.
- Runtime `mark_contested` can use verified review issue bundles for non-destructive recovery.
- Recovery case audit now displays obligation-grounded issue evidence as `missing/mismatch item + observed inventory quote`, not as an internal audit sentence.

Important metric semantics:

- `review_negative_verified_count` is still reserved for quote-grounded reviewer negatives.
- Real review issues are counted through `verified_review_issue_count = quote_grounded_review_issue_count + obligation_grounded_review_issue_count`.
- Obligation-grounded review issues also appear through `reviewer_absence_verified_count`, `total_review_negative_verified_count`, final potential concerns, and recovery case audit fields.
- Do not merge reviewer-inferred absence into quote-grounded `review_negative_verified_count`.

Latest validated results:

- Main hardneg20 run:
  - Run: `mimo_v25_negqty_recoverycap_guard3_qhyg_targetneg_freeformrevneg_reviewissuebundle_hardneg20_mt7_b4w2_api4_r8t600_tok1536_20260627_031647.jsonl`
  - Dashboard: `mimo_v25_negqty_recoverycap_guard3_qhyg_targetneg_freeformrevneg_reviewissuebundle_hardneg20_mt7_b4w2_api4_r8t600_tok1536_20260627_031647_STRICTMISSINGITEM_RECOMPUTE_VS_QUOTECLASS6_DASHBOARD.md`
  - Recovery table: `mimo_v25_negqty_recoverycap_guard3_qhyg_targetneg_freeformrevneg_reviewissuebundle_hardneg20_mt7_b4w2_api4_r8t600_tok1536_20260627_031647_STRICTMISSINGITEM_RECOMPUTE_RECOVERY_CASE.md`
  - Review issue case table: `mimo_v25_negqty_recoverycap_guard3_qhyg_targetneg_freeformrevneg_reviewissuebundle_hardneg20_mt7_b4w2_api4_r8t600_tok1536_20260627_031647_STRICTMISSINGITEM_RECOMPUTE_REVIEW_ISSUE_CASES.md`
  - Compared to `mimo_v25_quoteclass6_prefix_absence_hardneg20_mt7_b4w2_api4_r8t600_tok1536_20260626_131605.jsonl`.
  - MiMo parameters: hard_negative_20, mt7, b4w2, api4, retries8, timeout600, max_tokens1536, qhyg + targeted negative + freeform reviewer negative + review issue bundle.
  - Runtime: completed 20/20; 429 throttling occurred but all requests recovered under retry.
  - Overall protection: PASS.
  - `evidence_json_fallback_rate_pct=0`.
  - Positive support did not regress: `real_strong_support_total=82` vs baseline 79, `empirical_real_strong_support_count=57` vs 55, `claims_with_deep_support=38` vs 37.
  - Strict direct quote lane: `review_negative_verified_count=1`, `quote_grounded_review_issue_count=1`.
  - Review issue lane after strict missing-item recompute:
    - `obligation_grounded_review_issue_count=13`
    - `verified_review_issue_count=14`
    - `verified_actionable_negative_flaw_count=13`
    - `potential_concern_count=13`
    - `total_review_negative_verified_count=14`
  - Issue type counts:
    - `missing_ablation=5`
    - `result_claim_mismatch=2`
    - `missing_robustness_or_generalization=2`
    - `method_support_gap=1`
    - `efficiency_cost_gap=1`
    - `insufficient_evaluation=1`
    - `unfair_or_weak_baseline=1`
  - Recovery:
    - `mark_contested_commit_count=8`
    - `recovery_effective_repair=8`
    - `recovery_case_verified_review_issue_repair=8`
    - `recovery_case_turns_with_verified_review_issue_bundle_evidence=8`
    - `recovery_no_effect_commit=0`
    - `recovery_harmful_commit_risk=0`
  - Hygiene:
    - `negative_evidence_unlinked_to_flaw=0`
    - `positive_or_neutral_negative_candidate_count=0`
    - `semantic_negative_without_review_relation_count=0`
    - `low_score_promoted_strong=0`

Interpretation:

- The system is now correctly oriented around real review issues, not only direct negative quotes.
- Strict quote-grounded negatives remain rare by design; do not loosen that verifier.
- The hardneg20 result is the first run where the review-issue story is quantitatively strong: verified review issues scale to 14/20 while positive support and protection pass.
- The remaining bottleneck is still direct quote-grounded negative recall and missing-baseline/reproducibility coverage. Do not solve that by weakening verifier gates; improve Critique candidate specificity and inventory extraction.

Validation:

```bash
DRMAS_NEG_QUOTE_HYGIENE=1 DRMAS_TARGETED_NEGATIVE_SEARCH=1 \
DRMAS_FREEFORM_REVIEWER_NEGATIVE=1 DRMAS_REVIEW_ISSUE_BUNDLE=1 \
/opt/miniconda3/envs/DrMAS/bin/python -m pytest \
  tests/test_review_inference_runner.py \
  tests/test_review_decision_hygiene.py \
  tests/test_recovery_patch.py \
  tests/test_case_audit.py -q
```

Current result: `609 passed`.

Next steps:

- Run full39 with the same bundle flags and `max_tokens=1536`.
- Continue improving candidate discovery for `missing_baseline`, `reproducibility_gap`, and `evaluation_protocol_risk`.
- Keep strict missing-item guard active; generic requirement labels must remain diagnosis-pending, not verified issues.
- Continue improving recovery operation diversity, but do not inflate effective repair without verified quote-grounded negative or verified review issue bundle evidence.

## Previous State: 2026-06-25

Active project directory: `/Users/zss/Downloads/zssmas-codex-p26-optimization-20260524`. Do not use `/Users/zss/Downloads/DrMAS-master`; it is stale.

Current effective code changes:

- Final-view metrics now separate quote-grounded negatives from reviewer-inferred concerns:
  - `coverage_gap_potential_concern_count`
  - `reviewer_inferred_potential_concern_count`
  - `final_potential_concern_total`
- `semantic_negative_without_review_relation_count` now means only unhandled relation leakage. Relation-gated semantic-looking negatives are counted separately as `semantic_negative_rejected_by_review_relation_count`.
- `record_diagnosis_pending_concern` remains separate from `recovery_effective_repair`; it may commit a state record but must not inflate effective repair.
- `DRMAS_DIAGPENDING_RECOVERY=1` is a separate optional recovery-recording flag. It is not the same as `DRMAS_HARDNEG_DIAGNOSIS`.
- Targeted negative search may create tasks from claim requirement gaps, but those tasks still need copied paper text/table/list evidence to become evidence. Otherwise they stay diagnosis-pending/not-assessable.

Latest validated results:

- `mimo_v25_contextfix_targetneg_hardneg20_mt7_b4w2_api2_r5plus8t600_20260625_200722_MERGED20.jsonl`
  - Dashboard: `mimo_v25_contextfix_targetneg_hardneg20_mt7_b4w2_api2_r5plus8t600_20260625_200722_MERGED20_VS_TABLESCOPEFIX_DASHBOARD.md`
  - Overall protection: PASS.
  - `review_negative_verified_count=0`, `verified_actionable_negative_flaw_count=0`.
  - `verified_coverage_gap_count=12`, `coverage_gap_potential_concern_count=12`, `final_potential_concern_total=12`.
  - `semantic_negative_without_review_relation_count=0`, `semantic_negative_rejected_by_review_relation_count=1`.
- `mimo_v25_diagpending_policyfix_smoke8_mt7_b4w2_api2_r8t600_20260625_211433.jsonl`
  - Dashboard: `mimo_v25_diagpending_policyfix_smoke8_mt7_b4w2_api2_r8t600_20260625_211433_VS_CONTEXTFIX_OFF8_DASHBOARD.md`
  - Overall protection: PASS.
  - `review_negative_verified_count=0`, `verified_actionable_negative_flaw_count=0`.
  - `verified_coverage_gap_count=8`, `coverage_gap_potential_concern_count=8`, `final_potential_concern_total=8`.
  - `diagnosis_pending_concern_recorded_count=1`, `diagnosis_pending_concern_commit_count=1`, `recovery_committed=1`.
  - `recovery_effective_repair=0`, `recovery_no_effect_commit=0`, `recovery_harmful_commit_risk=0`.
  - `semantic_negative_without_review_relation_count=0`, `semantic_negative_rejected_by_review_relation_count=4`.

Interpretation:

- The system is now safer against fake negatives: author self-limitations, internal variant results, and weak paper observations are not counted as verified reviewer negatives.
- The system still has no quote-grounded verified negative evidence in the latest 8/20 runs. The paper narrative can currently claim clean coverage-gap / diagnosis-pending concern preservation, but not a restored verified-negative recovery lifecycle.
- Do not loosen the review-negative verifier to raise counts. The next real lever is better reviewer critique discovery plus evidence retrieval, while preserving the strict separation between `review_negative_verified` and reviewer-inferred coverage/diagnosis concerns.

Validation:

```bash
/opt/miniconda3/envs/DrMAS/bin/python -m pytest \
  tests/test_review_decision_hygiene.py \
  tests/test_recovery_patch.py \
  tests/test_review_inference_runner.py \
  tests/test_coverage_gap_recovery.py -q
```

Current result: `539 passed`.

## Previous State: 2026-06-22

Active project directory: `/Users/zss/Downloads/zssmas-codex-p26-optimization-20260524`. Do not use `/Users/zss/Downloads/DrMAS-master` for this work; that directory is stale.

Latest Codex code changes:

- Evidence negative-mode contract was tightened in `agent_system/review_prompts.py` and `agent_system/inference/review_runner.py`: negative mode should output either one quote-grounded negative evidence item or a `not_assessable` unresolved question; no positive support in negative mode.
- Evidence normalization now preserves `negative_type` as `negative_evidence_type`, plus `required_evidence_type` and `targeted_negative_search_task_id`.
- `state.py` now has a narrow table/list absence verifier for cases such as a DAVIS2017 missing claim when copied table/list text enumerates DAVIS2016/FBMS59/SegTrackV2 but not DAVIS2017. It intentionally blocks locator-only false positives.
- Recovery layer classification was adjusted so `record_diagnosis_pending_concern` is not misclassified as generic `patch_committed` when revision logs are truncated.
- Focused tests after these changes: `533 passed` across `tests/test_review_decision_hygiene.py`, `tests/test_recovery_patch.py`, and `tests/test_review_inference_runner.py`.

Latest hardneg20 run:

- Run: `mimo_v25_tablescopefix_hardneg20_mt7_b4w2_api2_r5t600_20260622_214828.jsonl`.
- Params: MiMo v2.5, hard_negative_20, `max_turns=7`, `max_tokens=2048`, `api_max_workers=2`, retries 5, timeout 600.
- Completed `20/20`, no API errors/timeouts/retries; avg reward `0.5628`, all final decisions `reject`.
- Negative/recovery target was not achieved: `review_negative_verified_count=0`, `verified_actionable_negative_flaw_count=0`, `negative_evidence_candidate_count=0`, `potential_concern_count=0`, `grounded_weakness_count=0`.
- Coverage/pending signal exists: `verified_coverage_gap_count=17`, `diagnosis_pending_potential_concern_count=74`, but `diagnosis_pending_concern_recorded_count=0`.
- Evidence JSON was stable in this run (`77/77 json_valid`), so JSON parsing is not the current blocker.

Current root-cause judgment:

- The run did not enable the full desired pipeline. `DRMAS_TARGETED_NEGATIVE_SEARCH`, `DRMAS_HARDNEG_DIAGNOSIS`, and `DRMAS_DIAGPENDING_RECOVERY` were effectively off, so this did not test "model diagnosis -> targeted Evidence verification -> recovery lifecycle".
- Hard-negative turns were weakly targeted: among 37 negative formation turns, target quality was `weak_target=19`, `empty_target=7`, `narrow_real_target=11`; 22 turns emitted zero evidence.
- Emitted negative-looking records were correctly rejected as author limitations, prior-work/background limitations, positive/neutral observations, or paraphrases without paper grounding.
- Old xUe1YqEgd6 restored negatives depended on a specific claim mentioning DAVIS2017; the fresh run extracted a broader "standard benchmarks" claim, so "table omits DAVIS2017" no longer bound. This is claim specificity / target construction variance, not a verifier regression.
- Final reports already render claim-requirement gap concerns, but dashboard `potential_concern_count` does not count those rendered concerns. Keep quote-grounded verified negatives and diagnosis-pending concerns separate, but align metrics with reader-visible concerns.

Next work:

1. Make Critique generate specific diagnosis targets for reviewer-inferred concerns.
2. Use those targets to drive Evidence Agent verification of tables/lists/results/baselines when possible.
3. Record diagnosis-pending concerns in recovery lifecycle only as diagnosis-pending, never as quote-grounded verified negative or `recovery_effective_repair`.
4. Stabilize claim specificity for benchmarks/datasets/metrics so absence verifiers have concrete entities to check.

## Previous State: 2026-06-18

Recent fix after Claude/Codex audit:

- `record_diagnosis_pending_concern` no longer counts as `recovery_effective_repair`.
- It has its own layer/metric: `diagnosis_pending_recorded_layer`.
- `no_effect_commit` remains false for diagnosis-pending records.
- The state-writing recording path is gated by `DRMAS_DIAGPENDING_RECOVERY=1`, default off.
- Deterministic claim-requirement audit and final-view/report rendering remain default on.
- The proposed independent scheduler for claim-requirement recording was removed. Recording must not steal Evidence/Recovery turns.
- Focused tests passed: `517 passed`.
- `py_compile` passed for `state.py`, `review_runner.py`, and dashboard script.

Current running validation:

- Clean default qhyg smoke8 started 2026-06-18 00:09.
- PID: `55328`
- Output: `mimo_v25_diagpendingfix_default_qhyg_smoke8_mt7_b4w2_api2_r10t600_20260618_000924.jsonl`
- Purpose: verify the low-risk 1+2 fix with `DRMAS_DIAGPENDING_RECOVERY` off.

The earlier mixed run with `DRMAS_CLAIMREQ_RECOVERY=1` was stopped at 0 output lines and should not be used.

Latest smoke8 result: 8/8 completed, protection PASS, but it exposed a more important narrative bug. Several counted negative candidates are paper-text/limitation extractions rather than reviewer-discovered flaws. Example false patterns include "addressing/overcoming limitations" and positive robustness/outperformance text being treated as negative because the quote is paper-grounded and contains a negative-looking word. Next work must add a review-semantic negative gate; paper-grounded quote existence is not enough.

Detailed plan: `REVIEW_SEMANTIC_NEGATIVE_EVIDENCE_AUDIT_PLAN_20260618.md`.

## Key Conclusions To Preserve

### QHYG Is The Current Clean Positive Layer

`DRMAS_NEG_QUOTE_HYGIENE=1` is the first clean positive direction:

- reduces bibliographic/title/future-work/noise negative quotes;
- keeps real negative evidence available;
- does not need validator relaxation;
- protects recovery and contested relation paths better than aggressive discovery.

Important qhyg baseline artifacts:

- smoke8 baseline: `mimo_v25_qhyg_trueneg_smoke8_mt7_b4w2_api4_r5t600_20260616_094629.jsonl`
- hardneg20 baseline: `mimo_v25_negqty_recoverycap_guard3_qhyg_hardneg20_mt7_b4w2_api4_r5t600_20260615_003753.jsonl`

### Claim-Requirement Audit Is Diagnostic, Not Verified Negative Evidence

Claim-requirement audit is useful for final-view diagnosis:

- it detects that a claim lacks required evidence coverage;
- it can render potential concerns in the user report;
- it should not create confirmed weaknesses;
- it should not count as verified negative evidence;
- it should not be injected into live Evidence/Critique/Manager observations as a soft "find this" prompt.

Past live-observation injection caused question-only Evidence outputs and support collapse. Keep claim-requirement gaps out of live prompts unless implementing a tightly gated target-prioritization experiment.

### P-B Is The Preferred Next Direction

The promising direction is:

- use claim-requirement gaps to reprioritize existing Evidence Agent `verify_evidence` / `request_evidence_recheck` targets;
- do not add extra rounds;
- do not route to Critique as model judgment;
- require Evidence Agent quote + locator + verifier before anything becomes verified negative evidence.

This is different from recording `diagnosis_pending_concern`. Recording is only bookkeeping; P-B should help Evidence actually find paper-grounded negative/support coverage.

### Recovery Should Stay Non-Destructive

Recovery should focus on:

- `mark_contested` when strong positive support and verified negative evidence conflict;
- `downgrade_final_to_candidate` when a flaw is over-escalated;
- `route_to_assessment_limitation` only for true limitations or safe terminal cases;
- preserving final-view potential concerns when already properly represented.

Recovery quality matters more than raw commit count. `route_to_assessment_limitation` should not be the only successful operation.

## No-Go Or Default-Off Directions

### `DRMAS_HARDNEG_DIAGNOSIS=1`

Default off. Clean A/B showed net-negative:

- request_evidence_recheck collapsed;
- analyze_flaws exploded;
- verified negative / actionable / contested / recovery all went to zero;
- real strong support dropped.

Reason: Critique model judgment replaced Evidence Agent quote finding. Keep as a no-go reference unless explicitly rerunning a controlled experiment.

### `DRMAS_NEGATIVE_PASS_MODE=compact`

Default off. Compact negative pass was net-negative in hardneg20:

- real strong support dropped;
- verified actionable negatives did not improve enough;
- recovery effective repair dropped;
- Evidence turns were displaced.

Do not revive as mainline without a new design.

### `DRMAS_NEG_DISCOVERY_MODE=aggressive`

Default off. Aggressive discovery increased some negative counts but harmed recovery and added no-effect risk. It mostly generated scope-limitation/noise pressure instead of actionable flaws.

### `DRMAS_NEG_RECLASSIFY=1`

View-only reclassification was mostly inert on real runs. It did not solve discovery. Keep default off unless using it for a narrow analysis.

### `DRMAS_TARGETED_NEGATIVE_SEARCH=1`

Experimental. Prior targeted Evidence prompt attempts often produced empty payloads because task blocks displaced quote/excerpt context or conflicted with JSON contract. If revived, keep tasks to 1-2, put quote/excerpt before task text, and use a minimal schema.

### `DRMAS_DIAGPENDING_RECOVERY=1`

Default off. It allows recording a diagnosis-pending concern in state, but must remain separate from `recovery_effective_repair`. It is not a way to increase true recovery quantity.

## Negative Evidence Types

Real quote-grounded negative types currently worth tracking:

- `scope_limitation`
- `negative_result`
- `direct_contradiction`
- `method_support_gap`
- `reproducibility_gap`

Actionable coverage/potential concern types should be kept separate unless quote-grounded:

- `missing_baseline`
- `missing_ablation`
- `insufficient_evaluation`
- `missing_robustness_or_generalization`
- `result_claim_mismatch`
- `efficiency_cost_gap`

Avoid adding weak/noisy types such as novelty/writing/ethics/dataset-bias unless there is a strong paper-grounded verifier. These tend to become generic gaps.

## 2026-06-28 P28 CLEAN5: entity-level review issue bundle quantity pass

Current target is `verified_review_issue_count`, not direct `review_negative_verified_count`. Direct quote-grounded negative evidence remains strict and low/zero by design; reviewer defects are counted through obligation-grounded issue bundles only when the system has a real claim anchor, a locatable observed inventory/table/component anchor, a concrete missing/mismatch item, and full-text counterevidence does not resolve it.

This turn added a conservative quantity path without loosening the verifier:

- Reviewer candidate claim rebinding: if a candidate is attached to the wrong claim but its own claim/weakness/question text clearly matches another real claim with the requested obligation, rebind before absence-audit gap generation.
- Paper-named baseline seed: only enabled when the paper itself admits a limited comparison opportunity (`absence/lack/no other ... studies/methods/baselines/comparisons`, or single/only baseline wording). It then extracts only citation-adjacent displayed method names from paper text, rejects title words/dataset names/current-paper names, and still requires observed comparison inventory plus full-text counterevidence checks.
- Baseline counterevidence tightened: related-work mentions no longer count as resolving a missing baseline unless the concrete baseline marker appears in a local experimental comparison/table/baseline-list context. Baseline lists (`Baseline methods include ...`) and table rows now block false positives.

Fresh hardneg20 artifact used for offline recompute:
`mimo_v25_negqty_recoverycap_guard3_qhyg_targetneg_freeformrevneg_reviewissuebundle_hardneg20_mt7_b4w2_api2_r8t600_tok1536_20260628_071024.jsonl`

CLEAN5 recompute artifacts:

- `P28_CLEAN5_FRESH_HARDNEG20_DASHBOARD.md/json`
- `P28_CLEAN5_FRESH_HARDNEG20_AUDIT.json`
- `P28_CLEAN5_FRESH_HARDNEG20_REVIEW_ISSUE_CASE_TABLE.md/json`
- `P28_CLEAN5_FRESH_HARDNEG20_RECOVERY_CASE_TABLE.md/json`

CLEAN5 headline metrics:

- `verified_review_issue_count=10`
- `reviewer_candidate_review_issue_count=9`
- `claim_obligation_review_issue_count=1`
- `review_negative_verified_count=0`
- `mark_contested_commit_count=14`
- `negative_evidence_unlinked_to_flaw=0`
- `positive_or_neutral_negative_candidate_count=0`
- `real_strong_support_total=47`
- protection lines: PASS

Manual audit notes:

- CLEAN2/CLEAN3 overcounted because general paper-named baseline extraction admitted false positives such as `Moreover baseline`, `RefCOCO baseline`, `GraphSAGE baseline`, `Transformer baseline`, and `MVTCAE baseline`. Those were not accepted as final; CLEAN5 adds the limited-comparison opportunity gate and stricter counterevidence.
- CLEAN5 adds the HALO case as a defensible paper-named missing-baseline issue: the paper states an absence of other ADA studies and compares the CS->ACDC result to RIPU while its own related-work inventory names EqualAL/Labor/PixelPick-style AL methods. The counted case is `YXn76HMetm`, missing same-setting comparison against paper-named `EqualAL`.
- Remaining risk: some component-ablation issues inherited from CLEAN1 are still terse and should be manually case-audited before paper-ready claims, especially duplicate-looking prediction-head cases. Do not inflate the count by relaxing these gates.

## 2026-06-29 P28 CLUSTERGUARD: row inflation control + review-worthiness gate

Authoritative source run for this checkpoint:
`mimo_v25_negqty_recoverycap_guard3_qhyg_targetneg_freeformrevneg_reviewissuebundle_hardneg20_mt7_b4w2_api2_r8t600_tok1536_20260629_202551.jsonl`

Previous `P28_TARGETGUARD_FRESH_202551` established that recall/bridge were no longer the main bottleneck: `verified_review_issue_count=19`, `reviewer_candidate_review_issue_count=19`, `mark_contested_commit_count=8`, protection lines PASS. Manual audit showed this should not be narrated as 19 true defects because rows contained duplicates and several D-class false positives.

This turn adds two precision-preserving quantity controls without relaxing verifier:

- Issue clustering: paper-facing counts now distinguish row count from cluster count. Cluster signature is `(issue_type, normalized_missing_target)` within each paper/final-view. Dashboard and case table expose `verified_review_issue_row_count`, `verified_review_issue_cluster_count`, `duplicate_review_issue_row_count`, cluster type counts, cluster target, cluster size, representative row, and cluster claim ids.
- Review-worthiness gate: verifier-passing bundles can still be demoted when the mismatch is not a review-worthy defect. Current guarded cases include ordinary `distributed_gradient` ablation targets, long-term modeling targets already covered by a component-ablation table, efficiency-cost gaps when full text contains concrete runtime/hardware/speedup measurements, and graph-classification coverage demands attached only to node-classification claims.
- Candidate funnel now records `review_issue_candidate_review_worthiness_rejected`, so demotions are visible rather than silently disappearing.

Offline recompute artifacts:

- `P28_CLUSTERGUARD_RECOMPUTE_202551_HARDNEG20_DASHBOARD.md/json`
- `P28_CLUSTERGUARD_RECOMPUTE_202551_HARDNEG20_AUDIT.json`
- `P28_CLUSTERGUARD_RECOMPUTE_202551_REVIEW_ISSUE_CASE_TABLE.md/json`
- `P28_CLUSTERGUARD_RECOMPUTE_202551_RECOVERY_CASE_TABLE.md/json`

CLUSTERGUARD headline metrics:

- `verified_review_issue_count=15`
- `verified_review_issue_row_count=15`
- `verified_review_issue_cluster_count=8`
- `duplicate_review_issue_row_count=7`
- `reviewer_candidate_review_issue_count=15`
- `reviewer_candidate_review_issue_cluster_count=8`
- `review_issue_type_missing_ablation=13`
- `review_issue_cluster_type_missing_ablation=6`
- `review_negative_verified_count=0` (direct quote-negative lane remains strict)
- `mark_contested_commit_count=8`
- `recovery_case_verified_review_issue_repair=5`
- `negative_evidence_unlinked_to_flaw=0`
- `positive_or_neutral_negative_candidate_count=0`
- protection lines: PASS

Demoted from TARGETGUARD by CLUSTERGUARD:

- `WpXq5n8yLb` efficiency-cost gap: paper has concrete H100/TensorRT/MLX/speedup/resource measurement context.
- `cklg91aPGk` graph-classification robustness: off-claim for a node-classification claim.
- `xUe1YqEgd6` long-term modeling ablation: observed inventory already reports component ablation over the main components.
- `XH3OiIhtvf` distributed-gradient ablation: ordinary training/distributed optimization mechanism, not a contribution-bound component flaw.

Current narrative: use cluster count as the paper-facing review-issue quantity. The result is not "19 true defects"; it is "15 verifier-passing rows, 8 deduplicated review-worthy clusters, with strict protection lines passing." Remaining bottleneck is issue diversity: missing-ablation still dominates (`13/15` rows, `6/8` clusters). Next work should improve entity-level obligation/inventory diversity, not loosen direct negative quote verification.

## 2026-06-29/30 P28 CLUSTERGUARD API rerun: real hardneg20 result failed one protection line

After the CLUSTERGUARD offline recompute, a real MiMo API hardneg20 rerun was executed with the current code and the same P28 flags:

```bash
DRMAS_NEG_QUOTE_HYGIENE=1 \
DRMAS_TARGETED_NEGATIVE_SEARCH=1 \
DRMAS_FREEFORM_REVIEWER_NEGATIVE=1 \
DRMAS_REVIEW_ISSUE_BUNDLE=1 \
MAX_TOKENS=1536 \
API_MAX_WORKERS=2 \
API_MAX_RETRIES=8 \
API_TIMEOUT=600 \
bash run_hardneg20_guard3.sh
```

Run artifacts:

- `mimo_v25_negqty_recoverycap_guard3_qhyg_targetneg_freeformrevneg_reviewissuebundle_hardneg20_mt7_b4w2_api2_r8t600_tok1536_20260629_223747.jsonl`
- `mimo_v25_negqty_recoverycap_guard3_qhyg_targetneg_freeformrevneg_reviewissuebundle_hardneg20_mt7_b4w2_api2_r8t600_tok1536_20260629_223747.log`
- `P28_CLUSTERGUARD_API_223747_HARDNEG20_DASHBOARD.md/json`
- `P28_CLUSTERGUARD_API_223747_HARDNEG20_AUDIT.json`
- `P28_CLUSTERGUARD_API_223747_REVIEW_ISSUE_CASE_TABLE.md/json`
- `P28_CLUSTERGUARD_API_223747_RECOVERY_CASE_TABLE.md/json`

API rerun headline metrics:

- `verified_review_issue_count=19`
- `verified_review_issue_row_count=19`
- `verified_review_issue_cluster_count=15`
- `duplicate_review_issue_row_count=4`
- `reviewer_candidate_review_issue_count=14`
- `reviewer_candidate_review_issue_cluster_count=10`
- `review_issue_type_missing_ablation=11`
- `review_issue_cluster_type_missing_ablation=7`
- `review_negative_verified_count=1`
- `mark_contested_commit_count=8`
- `recovery_case_verified_review_issue_repair=7`
- `negative_evidence_unlinked_to_flaw=0`
- `evidence_json_fallback_rate_pct=0`
- protection: FAIL because `positive_or_neutral_negative_candidate_count=1`

Do not treat `P28_CLUSTERGUARD_API_223747` as a passing paper result. The failing case is `XH3OiIhtvf`: evidence `evidence-critique-negative-1` was labeled `result_claim_mismatch` even though the quote says the federated model without secure aggregator improves EER from `2.57` to `2.36` (`8.57% relative improvement`). This is positive/neutral result text being misused as a negative. Next fix should add a semantic guard for improvement-direction metrics, especially error-rate metrics where lower is better, before accepting `result_claim_mismatch` direct negatives.

## Validation Commands

Focused review tests:

```bash
/opt/miniconda3/envs/DrMAS/bin/python -m pytest \
  tests/test_review_decision_hygiene.py \
  tests/test_review_inference_runner.py \
  tests/test_recovery_replay_harness.py \
  tests/test_recovery_patch.py -q
```

Syntax check:

```bash
/opt/miniconda3/envs/DrMAS/bin/python -m py_compile \
  agent_system/environments/env_package/review/state.py \
  agent_system/inference/review_runner.py \
  scripts/dashboard_run_comparison_v1.py
```

Clean default smoke8:

```bash
set -a; source .env; set +a
DRMAS_NEG_QUOTE_HYGIENE=1 NO_PROXY="*" HTTPS_PROXY="" HTTP_PROXY="" \
PYTHONPATH=/opt/miniconda3/envs/agent/lib/python3.12/site-packages:. \
/opt/miniconda3/envs/DrMAS/bin/python -u agent_system/inference/review_runner.py \
  --backend api \
  --api-provider mimo \
  --api-model mimo-v2.5 \
  --api-max-workers 2 \
  --api-max-retries 10 \
  --api-timeout 600 \
  --model-adapter-mode small_model \
  --dataset-path smoke8_sameids_20260604.parquet \
  --mode s4 \
  --max-turns 7 \
  --max-workers-per-turn 2 \
  --manager-batch-size 4 \
  --temperature 1.0 \
  --top-p 0.95 \
  --max-tokens 1536 \
  --output-path <output.jsonl> \
  --log-dir <log_dir>
```

Dashboard comparison:

```bash
PYTHONPATH=/opt/miniconda3/envs/agent/lib/python3.12/site-packages:. \
/opt/miniconda3/envs/DrMAS/bin/python scripts/dashboard_run_comparison_v1.py \
  --candidate <candidate.jsonl> \
  --baseline mimo_v25_qhyg_trueneg_smoke8_mt7_b4w2_api4_r5t600_20260616_094629.jsonl \
  --label-candidate <label> \
  --label-baseline qhyg_trueneg \
  --output-md <dashboard.md> \
  --output-json <dashboard.json> \
  --mode smoke
```

## Important Docs / Artifacts

- `PAPER_GOAL_AND_ROADMAP.md`
- `CHECKPOINT_TESTS_GREEN_AND_HARDNEG_GATE_20260616.md`
- `HARDNEGDIAG_AB_AUDIT_20260616.md`
- `HARDNEGDIAG_AB_DASHBOARD_20260616.md`
- `P_A_COMPACT_NEGATIVE_PASS_AUDIT_20260616.md`
- `CLAIMREQ_RUN_CAUSE_AUDIT_20260615.md`
- `REAL_NEGATIVE_EVIDENCE_TARGETED_SEARCH_PLAN_20260616.md`

## Archived History Summary

March-April built the DrMAS paper-review adaptation, moved from generic accept/reject framing toward evidence-grounded diagnostic review, and established that binary runtime decision is only a health check.

May work added evidence grounding fields, quote/locator audits, final-view diagnostic reports, support quality filtering, contested/recovery visibility, and case-audit tooling. Main lesson: schema-level quote fields are not enough; quote exactness and locator fidelity need verifier/audit support.

Early June work explored recovery target hydration, gap/evidence-link repair, programmatic locators, negative noise filtering, contested support, and claim-requirement audit. Useful pieces survived as final-view/dashboard hygiene and tests; live prompt/controller additions that displaced Evidence Agent support formation were rejected.

Do not expand this archive with detailed old run tables. Put detailed experiment writeups in separate markdown files and keep only current decisions here.

## P28.5 TargetRefine2 Current Checkpoint (2026-06-30)

Purpose: preserve the P28 reviewer-issue quantity gains without letting generic missing-ablation targets become verified review issues. This checkpoint tightens target quality and semantic ablation counterevidence, then recomputes over a fresh MiMo hardneg20 run.

Fresh API run used:

```bash
DRMAS_NEG_QUOTE_HYGIENE=1 \
DRMAS_TARGETED_NEGATIVE_SEARCH=1 \
DRMAS_FREEFORM_REVIEWER_NEGATIVE=1 \
DRMAS_REVIEW_ISSUE_BUNDLE=1 \
MAX_TOKENS=1536 \
API_MAX_WORKERS=2 \
API_MAX_RETRIES=8 \
API_TIMEOUT=600 \
bash run_hardneg20_guard3.sh
```

Fresh run files:

- `mimo_v25_negqty_recoverycap_guard3_qhyg_targetneg_freeformrevneg_reviewissuebundle_hardneg20_mt7_b4w2_api2_r8t600_tok1536_20260630_194911.jsonl`
- `P28_5_FRESH_194911_HARDNEG20_DASHBOARD.md/json`
- `P28_5_FRESH_194911_REVIEW_ISSUE_CASE_TABLE.md/json`
- `P28_5_FRESH_194911_RECOVERY_CASE_TABLE.md/json`

Raw fresh result before final target refinement:

- protection: PASS
- `verified_review_issue_count=22`
- `verified_review_issue_cluster_count=16`
- `reviewer_candidate_review_issue_count=22`
- `mark_contested_commit_count=14`
- `recovery_case_verified_review_issue_repair=14`

This raw count is not paper-ready. Manual audit found obvious false positives from malformed/generic missing-ablation targets, including `function generates the action representation`, bare `fusion`, bare `federated gradient`, `effective we expect the loss`, and generic `training of deep neural network`.

TargetRefine2 code changes:

- Reject missing-ablation action/prose fragments (`generates`, `expects`, `updated by the gradient`, `function generates ...`, empirical-loss fragments).
- Reject generic architecture/training targets (`deep neural network`, bare `fusion`, bare `gradient`, bare `federated gradient`) unless the target text itself contains a contribution-specific mechanism such as OGL/orthogonal gradient/matching/learning.
- Add semantic table counterevidence for ablation tables whose rows/captions use different wording, especially SPOT-style pre-training strategy tables and LogoRA-style model architecture/fusion-method tables.
- Dashboard/case table now separates reviewer candidates into `critique_payload_candidate`, `deterministic_reviewer_seed`, and other candidate kinds.
- Recovery table now separates actual harmful commits from blocked unsafe downgrade attempts.

Authoritative offline recompute after TargetRefine2:

- `P28_5_TARGETREFINE2_194911_HARDNEG20_DASHBOARD.md/json`
- `P28_5_TARGETREFINE2_194911_HARDNEG20_AUDIT.json`
- `P28_5_TARGETREFINE2_194911_REVIEW_ISSUE_CASE_TABLE.md/json`
- `P28_5_TARGETREFINE2_194911_RECOVERY_CASE_TABLE.md/json`
- `P28_5_TARGETREFINE2_MANUAL_CLUSTER_AUDIT_20260630.md`

TargetRefine2 metrics:

- protection: PASS
- `review_negative_verified_count=0`
- `verified_review_issue_count=13`
- `verified_review_issue_cluster_count=9`
- `duplicate_review_issue_row_count=4`
- `reviewer_candidate_review_issue_count=13`
- `reviewer_candidate_review_issue_critique_payload_count=2`
- `reviewer_candidate_review_issue_deterministic_seed_count=11`
- `claim_obligation_review_issue_count=0`
- `verified_missing_ablation_cluster_count=6`
- `mark_contested_commit_count=14`
- `recovery_case_verified_review_issue_repair=6`
- `recovery_harmful_commit_committed=0`
- `recovery_unsafe_downgrade_attempt_blocked=1`
- `negative_evidence_unlinked_to_flaw=0`
- `semantic_negative_without_review_relation_count=0`
- `positive_or_neutral_negative_candidate_count=0`

Manual cluster audit:

- System-verified clusters: 9
- Manual A/B clusters: 8/9
- Strong A clusters: recurrent draft model, acceptance prediction head, generalized noise regularization
- Defensible B clusters: class-balancing CE loss, GrCN/ControllNet reproducibility details, PropGCL transformation phase/weights, recent GNN/graph-transformer baselines, EqualAL baseline
- C cluster: `number_motion_components_beyond` because the paper already has K sensitivity up to K=4; asking beyond K=4 is plausible but too demanding for a paper-ready verified main-result count

Current paper-facing statement: TargetRefine2 verifies 9 obligation-grounded review issue clusters on hardneg20, with 8/9 manually judged A/B. It does not restore direct quote-grounded negative discovery (`review_negative_verified_count=0`). The contribution remains conservative obligation-grounded review issue verification plus non-destructive recovery.

Important caveat: TargetRefine2 is an offline recompute over a fresh API run. Because the final guard was applied after the API run, the recovery table still contains stale absence repairs (`effective_repair_without_verified_negative=8`). A fresh API rerun with the final TargetRefine2 code is required before using live recovery counts in the paper.

## P28.6 ConflictFix Narrative Checkpoint (2026-06-30)

Purpose: clean the remaining final-view hygiene conflicts without changing the strict verifier or inflating issue counts. This checkpoint fixes a metric/narrative hazard exposed by P28.5: old quote-bank negative candidates and stale reviewer-absence audit artifacts could remain as active `negative_grounding_conflict_count` even when they were not counted as verified review issues.

Code behavior:

- `quote-bank-negative-grounding` records that are not actually negative stance are treated as safe rejected negative anchors, not active negative-grounding conflicts.
- stale `reviewer_absence_audit` evidence/flaws that no longer pass the current review-issue bundle verifier are treated as rejected stale anchors, not active conflicts.
- ordinary direct negative misbindings still remain active conflicts.
- Added regression tests for quote-bank non-negative anchors and stale reviewer-absence audit anchors.

Authoritative P28.6 artifacts:

- `P28_6_PAPER_NARRATIVE_STATUS_20260630.md`
- `P28_6_CONFLICTFIX_TARGETREFINE2_194911_HARDNEG20_DASHBOARD.md/json`
- `P28_6_CONFLICTFIX_TARGETREFINE2_194911_HARDNEG20_AUDIT.json`
- `P28_6_CONFLICTFIX_TARGETREFINE2_194911_REVIEW_ISSUE_CASE_TABLE.md/json`
- `P28_6_CONFLICTFIX_TARGETREFINE2_194911_RECOVERY_CASE_TABLE.md/json`
- `P28_6_CONFLICTFIX_MIMO_PARTIAL16_224133_HARDNEG20_DASHBOARD.md/json`
- `P28_6_CONFLICTFIX_MIMO_PARTIAL16_224133_HARDNEG20_AUDIT.json`
- `P28_6_CONFLICTFIX_MIMO_PARTIAL16_224133_REVIEW_ISSUE_CASE_TABLE.md/json`
- `P28_6_CONFLICTFIX_MIMO_PARTIAL16_224133_RECOVERY_CASE_TABLE.md/json`

P28.6 full20 offline recompute over `20260630_194911`:

- protection: PASS
- `paper_count=20`
- `review_negative_verified_count=0`
- `verified_review_issue_count=13`
- `verified_review_issue_cluster_count=9`
- `duplicate_review_issue_row_count=4`
- `reviewer_candidate_review_issue_count=13`
- `reviewer_candidate_review_issue_critique_payload_count=2`
- `reviewer_candidate_review_issue_deterministic_seed_count=11`
- `claim_obligation_review_issue_count=0`
- `verified_missing_ablation_cluster_count=6`
- `mark_contested_commit_count=14`
- `recovery_case_verified_review_issue_repair=6`
- `negative_grounding_conflict_count=0`
- `negative_semantic_anchor_conflict_count=0`
- `semantic_negative_without_review_relation_count=0`
- `negative_evidence_unlinked_to_flaw=0`
- `positive_or_neutral_negative_candidate_count=0`

P28.6 fresh MiMo partial16 recompute over `20260630_224133`:

- protection: PASS
- `paper_count=16`
- `verified_review_issue_count=12`
- `verified_review_issue_cluster_count=8`
- `reviewer_candidate_review_issue_count=12`
- `reviewer_candidate_review_issue_critique_payload_count=0`
- `reviewer_candidate_review_issue_deterministic_seed_count=12`
- `mark_contested_commit_count=5`
- `recovery_case_verified_review_issue_repair=5`
- `negative_grounding_conflict_count=0`
- `negative_semantic_anchor_conflict_count=0`

MiMo status: a lightweight MiMo API test reached the service but returned `402 Insufficient account balance`; the fresh run stopped at 16/20 for the same reason. Do not claim a fresh full20 P28.6 rerun until MiMo balance/key is restored.

Current paper-facing statement: P28.6 supports the ReviewState narrative that DrMAS verifies obligation-grounded review issue bundles conservatively. On hardneg20 offline recompute it yields 9 issue clusters, with the prior TargetRefine2 manual audit judging 8/9 clusters A/B. It does not restore direct quote-grounded negative discovery (`review_negative_verified_count=0`). Phrase live recovery carefully: full20 recovery numbers are offline recompute over a completed run; the freshest live-rerun evidence is partial16.

## P29 Discovery-Layer Expansion Checkpoint (2026-07-01)

Purpose: increase verified review issue quantity by expanding discovery/entity/inventory inputs while keeping verifier gates strict. This is not a direct quote-negative recall push; `review_negative_verified_count` remains a separate strict lane.

Implemented logic:

- Critique review-issue discovery now targets up to 12 candidates and is prompted slot-by-slot across missing baseline, missing ablation, scope/robustness, protocol/reproducibility, efficiency/resource, and result-claim mismatch.
- Deterministic reviewer seeds were expanded as top-up only. Seeds keep `review_issue_slot` and `discovery_origin` so dashboard/case tables can distinguish model payload candidates from deterministic stress targets.
- Claim surface and normalized inventory extraction were expanded to expose paper-named baselines/methods, datasets, metrics, core mechanisms, protocol/resource details, reproducibility cues, and inventory anchor types.
- Bundle verification remains strict: concrete entity, locatable claim anchor, locatable inventory quote/list/table anchor, no counterevidence, no retrieval/context/truncated framing, no generic missing item.
- Missing-ablation target guard rejects generic components/action fragments and malformed extracted text; retained missing-ablation targets are labeled high/medium confidence.
- Protocol/reproducibility seeding is guarded by explicit protocol/fairness/split/seed/threshold/same-budget/hardware cues and rejects template-only protocol gaps.
- Dashboard now includes `negative_grounding_conflict_count == 0` as a protection line.
- Final-view hygiene now view-only downgrades candidate flaws whose explicit `negative_evidence_ids` are unresolved or point to support evidence, including quote-bank candidate anchors and stale reviewer-absence anchors. Confirmed invalid negative bindings still surface as real hygiene conflicts.
- Potential-only negative false-positive filtering no longer treats explicit `worse` / `underperform` wording as positive context merely because a "strongest baseline" phrase appears.

Authoritative P29 fresh MiMo full20 run:

- raw run: `mimo_v25_negqty_recoverycap_guard3_qhyg_targetneg_freeformrevneg_reviewissuebundle_hardneg20_mt7_b4w2_api2_r8t600_tok1536_20260701_160531.jsonl`
- dashboard: `P29_DISCOVERY_EXPAND_MIMO_160531_TARGETGUARD3_HARDNEG20_DASHBOARD.md/json`
- audit: `P29_DISCOVERY_EXPAND_MIMO_160531_TARGETGUARD3_HARDNEG20_AUDIT.json`
- review issue cases: `P29_DISCOVERY_EXPAND_MIMO_160531_TARGETGUARD3_REVIEW_ISSUE_CASE_TABLE.md/json`
- recovery cases: `P29_DISCOVERY_EXPAND_MIMO_160531_TARGETGUARD3_RECOVERY_CASE_TABLE.md/json`

P29 TARGETGUARD3 metrics:

- protection: PASS
- `paper_count=20`
- `verified_review_issue_count=20`
- `verified_review_issue_cluster_count=15`
- `review_negative_verified_count=2`
- `quote_grounded_review_issue_count=2`
- `obligation_grounded_review_issue_count=18`
- `reviewer_candidate_review_issue_count=16`
- `claim_obligation_review_issue_count=2`
- `review_issue_candidate_total=78`
- `review_issue_candidate_verified=15`
- `review_issue_candidate_critique_payload_count=19`
- `review_issue_candidate_deterministic_seed_count=59`
- `review_issue_verified_slot_missing_ablation=12`
- `review_issue_verified_slot_missing_baseline=2`
- `review_issue_verified_slot_protocol_or_reproducibility=4`
- `mark_contested_commit_count=11`
- `recovery_case_verified_review_issue_repair=8`
- `negative_grounding_conflict_count=0`
- `negative_semantic_anchor_conflict_count=0`
- `negative_evidence_unlinked_to_flaw=0`
- `positive_or_neutral_negative_candidate_count=0`
- `semantic_negative_without_review_relation_count=0`

Interpretation:

- P29 meets the requested quantity target (`20` rows / `15` system clusters) on a fresh MiMo full20 run while protection lines pass.
- Do not headline this as 15 confirmed human-equivalent defects. Paper-facing reporting should use cluster count plus manual A/B audit. Manual audit is still required; likely risk items include medium-confidence missing-ablation targets such as `Planning Module`, `Global Encoder`, protocol strictness clusters, and duplicate direct quote clusters on the secure-aggregator paper.
- Missing-ablation still dominates (`12/20` rows, `7` clusters). The system is now stronger for quantity, but issue-type diversity remains the next research risk.
- Recovery bridge is working but incomplete: `mark_contested_commit_count=11`, with `8` verified-review-issue repairs; `verified_issue_cluster_without_recovery_count=6` remains.

## Paper Narrative Blueprint (2026-07-01)

New paper-facing blueprint: `PAPER_NARRATIVE_BLUEPRINT_20260701.md`.

Claim/evidence guardrail: `PAPER_CLAIMS_EVIDENCE_MATRIX_20260701.md`.

Introduction-section draft: `PAPER_INTRODUCTION_DRAFT_20260701.md`.

Method-section draft: `PAPER_METHOD_SECTION_DRAFT_20260701.md`.

Experiment-section draft: `PAPER_EXPERIMENT_SECTION_DRAFT_20260701.md`.

Related-work draft: `PAPER_RELATED_WORK_DRAFT_20260701.md`.

Bibliography candidates: `PAPER_BIBLIOGRAPHY_CANDIDATES_20260701.md`.

Cleaned draft BibTeX: `PAPER_REFERENCES_DRAFT_20260701.bib`.

Bibliography audit: `PAPER_BIBLIOGRAPHY_AUDIT_20260701.md`.

Figure specs: `PAPER_FIGURE_SPECS_20260701.md`.

Renderable figure draft: `PAPER_FIGURES_DRAFT_20260701.md` plus `paper_figures/*.{mmd,svg,pdf}`.

Manuscript skeleton: `PAPER_MANUSCRIPT_SKELETON_20260701.md`.

Continuous manuscript draft: `PAPER_CONTINUOUS_DRAFT_20260701.md`.

Clean paper body draft: `PAPER_CLEAN_BODY_DRAFT_20260701.md`.

Abstract revision audit: `PAPER_ABSTRACT_REVISION_AUDIT_20260701.md`.

Terminology guide: `PAPER_TERMINOLOGY_GUIDE_20260701.md`.

Submission readiness audit: `PAPER_READINESS_AUDIT_20260701.md`.

Production checklist: `PAPER_MANUSCRIPT_PRODUCTION_CHECKLIST_20260701.md`.

Reproducibility appendix draft: `PAPER_REPRODUCIBILITY_APPENDIX_20260701.md`.

Empirical framing decision: `PAPER_EMPIRICAL_FRAMING_DECISION_20260701.md`.

Advisor review packet: `PAPER_ADVISOR_REVIEW_PACKET_20260701.md`.

Advisor one-page brief: `PAPER_ADVISOR_ONE_PAGE_BRIEF_20260701.md`.

Venue fit decision: `PAPER_VENUE_FIT_DECISION_20260701.md`.

Reviewer pre-mortem: `PAPER_REVIEWER_PREMORTEM_20260701.md`.

Result consistency audit: `PAPER_RESULT_CONSISTENCY_AUDIT_20260701.md`.

Issue-bundle case study: `PAPER_REVIEW_ISSUE_CASE_STUDY_20260701.md`.

Manual audit protocol: `PAPER_MANUAL_AUDIT_PROTOCOL_20260701.md`.

Core thesis:

- Do not sell DrMAS as a better free-form review generator or accept/reject classifier.
- Sell it as ReviewState maintenance: claims, evidence, reviewer issues, conflicts, final-view validation, and non-destructive recovery.
- Main result is not direct negative quote discovery. Direct quote lane remains strict and currently has `review_negative_verified_count=0`.
- Main current evidence is obligation-grounded issue verification: P28.6 full20 offline recompute has 9 verified issue clusters, with 8/9 manually judged A/B, and protection lines passing.

Paper claims allowed now:

- DrMAS separates direct quote-grounded negatives from obligation-grounded reviewer issues.
- DrMAS verifies non-quote reviewer issues through claim anchors, observed inventory, concrete missing/mismatch entities, and counterevidence checks.
- P28.6 maintains zero active negative-grounding conflicts, zero semantic anchor conflicts, zero unlinked negative evidence, and zero positive/neutral negative candidates.
- Recovery should be described as non-destructive state repair (`mark_contested`), not decision fixing.

Paper claims not allowed yet:

- Do not claim broad autonomous defect discovery.
- Do not headline row count; use cluster count and manual A/B cluster count.
- Do not claim a fresh full20 P28.6 rerun until MiMo balance is restored and the run completes.
- Do not claim Critique payload discovery is mature; most current verified issues are deterministic seeds.
- Do not frame DrMAS as a replacement for human reviewer judgment, or as satisfying venue policy or manuscript-confidentiality requirements by itself.

Current writing status:

- Introduction, method, experiment, related work, bibliography-candidate, cleaned draft-BibTeX, bibliography-audit, figure-spec, renderable-figure, manuscript-skeleton, continuous-manuscript, clean-body, readiness-audit, production-checklist, reproducibility-appendix, and empirical-framing decision drafts now exist.
- The continuous manuscript was polished to reduce P28-specific wording outside experiments, replace development-log table language with paper-facing interpretation, and move the former draft-status/open-items section into `PAPER_MANUSCRIPT_PRODUCTION_CHECKLIST_20260701.md`.
- The clean body draft removes workflow metadata from the continuous draft and replaces bracketed figure placeholders with rendered SVG figure references and paper-facing captions. It has been further polished to keep P28/run identifiers, dataset filenames, and API error-code details out of the main experiment narrative. It is now the preferred manuscript body for advisor/internal review.
- The clean and continuous draft abstracts were simplified to avoid reading like a dashboard: headline is now 9 obligation-grounded issue clusters with 8 manually judged valid/defensible; 13 raw rows are left to the experiment table; direct quote-grounded negative count 0 remains visible as a caveat. A later compression pass keeps the same evidence in five sentence roles: problem, typed ReviewState method, two-lane distinction, diagnostic result, and conservative non-autonomous positioning. Rationale is in `PAPER_ABSTRACT_REVISION_AUDIT_20260701.md`.
- The clean and continuous drafts now use paper-facing terminology in the main prose: final-view validation, recovery action, diagnostic set, and no P28/run-id/API-error-code wording in the main text. Terminology guardrails are in `PAPER_TERMINOLOGY_GUIDE_20260701.md`.
- The clean and continuous method sections now include a short algorithmic lifecycle block: extract claims/obligations, ground support and neutral inventory, form candidates, verify the two critical-content lanes separately, audit the final view, add non-destructive contested relations, and render from audited state rather than raw model prose.
- The clean and continuous limitations now explicitly explain deterministic reviewer seeds as auditable verifier stress targets, not evidence of autonomous issue discovery.
- The clean and continuous discussions now include a responsible-use boundary: DrMAS is review support and audit infrastructure, not an autonomous reviewer, accept/reject classifier, or source of final review judgments; deployment must respect manuscript confidentiality and venue LLM-assistance policy.
- The continuous draft has been synchronized with the clean body on rendered SVG figure references, the illustrative issue-bundle subsection, manual-audit A/B/C wording, and final-view validation terminology. The remaining intended difference is that the continuous draft keeps top-of-file draft metadata while the clean body is the advisor-facing manuscript body.
- The advisor one-page brief is now the fastest human-facing entry point. It asks whether to proceed with the conservative ReviewState framework story, then summarizes thesis, novelty, evidence, mandatory caveats, advisor questions, and recommended next step. The fuller advisor review packet remains the file index and question list.
- The venue-fit decision aid recommends a systems/method or human-AI review-support framing, treats peer-review automation workshops as a high-fit near-term path, and warns against benchmark-heavy ML/NLP positioning unless fresh full20, repeated seeds, broader issue diversity, or a second diagnostic/oracle analysis is added.
- The reviewer pre-mortem operationalizes the risk story: likely objections are empirical scale, direct-negative zero, deterministic reviewer seeds, missing-ablation skew, small manual audit, engineering-artifact framing, and case-study trust. It lists honest responses, forbidden responses, and exact manuscript actions.
- The result consistency audit checks that clean/continuous manuscript metrics match P28.6 dashboards and case-table artifacts. It confirms the paper-facing tuple: 13 rows, 9 clusters, 8/9 A/B manual clusters, direct quote-grounded negatives 0, full20 mark-contested 14, verified-review-issue repairs 6, partial16 clusters 8, and protection lines 0/PASS.
- The issue-bundle case study explains the SpecDec++ acceptance-prediction-head cluster as a concrete ReviewState example: claim anchor + neutral inventory anchor + missing component-isolation ablation + high target quality + non-destructive `mark_contested` recovery. The clean and continuous drafts now include a compact main-text audit table for this case and leave the detailed audit in `PAPER_REVIEW_ISSUE_CASE_STUDY_20260701.md`.
- The manual audit protocol defines A/B/C/D cluster labels, states that the audit unit is deduplicated issue cluster rather than raw row, and forbids treating 8/9 as population precision or independent defects. The clean body now includes the short A/B/C definition before the manual cluster audit table.
- The reproducibility appendix maps the paper concepts to implementation anchors, regeneration scripts, authoritative artifacts, expected metric tuples, and explicit non-claims. It is transparency/supporting material, not a new experiment or broader-performance claim.
- The empirical framing decision is no longer open for the conservative draft: use P28.6 offline full20 as the main diagnostic result and fresh MiMo partial16 only as a live sanity check. Fresh full20 remains required for stronger benchmark-style claims, not for continuing the framework paper narrative.
- Related work in the continuous draft now uses citation keys from cleaned `PAPER_REFERENCES_DRAFT_20260701.bib`; `PAPER_BIBLIOGRAPHY_CANDIDATES_20260701.md` maps those keys to API-verified candidate references; `PAPER_BIBLIOGRAPHY_AUDIT_20260701.md` records record-level metadata risks. On 2026-07-01 the peer-review-specific coverage was strengthened with Crossref-verified DOI records for a 2025 automated scholarly paper review survey and a 2025 peer-review challenges/opportunities article. Final BibTeX still needs target-venue export/verification.
- Figure specs, Mermaid sources, manually redrawn SVG drafts, and PDF exports now cover ReviewState lifecycle, two critical-content lanes, row-to-cluster-to-manual-audit funnel, and optional non-destructive recovery. The SVG files parse with `xmllint`, render with `rsvg-convert`, and were visually checked via temporary PNG renders. They still need target-template placement/cropping checks.
- Next paper-writing work should follow `PAPER_MANUSCRIPT_PRODUCTION_CHECKLIST_20260701.md`: use `PAPER_ADVISOR_ONE_PAGE_BRIEF_20260701.md`, `PAPER_ADVISOR_REVIEW_PACKET_20260701.md`, `PAPER_VENUE_FIT_DECISION_20260701.md`, `PAPER_REVIEWER_PREMORTEM_20260701.md`, and `PAPER_MANUAL_AUDIT_PROTOCOL_20260701.md` for advisor/internal review before heavy venue-template work; choose the venue family first; decide whether the manual audit needs a second annotator; decide whether the compact issue-bundle table stays in main text or moves to appendix; then convert `PAPER_CLEAN_BODY_DRAFT_20260701.md` into the target venue template, replace cleaned draft BibTeX with final venue records, place rendered figures in the target template, fold the reproducibility appendix into the target paper format, and maintain the conservative offline-full20/partial16 framing unless a fresh full20 rerun becomes available and passes the same checks.
- 2026-07-01 P29 clean MiMo API4 full20 rerun completed successfully after the API key/account issue was resolved. Authoritative clean rerun artifacts:
  - raw/log/meta: `mimo_v25_negqty_recoverycap_guard3_qhyg_targetneg_freeformrevneg_reviewissuebundle_hardneg20_mt7_b4w2_api4_r8t600_tok1536_20260701_192659.{jsonl,log,meta}`
  - dashboard: `P29_CLEAN_API4_192659_HARDNEG20_DASHBOARD.{md,json}`
  - case table: `P29_CLEAN_API4_192659_REVIEW_ISSUE_CASE_TABLE.{md,json}`
  - recovery table: `P29_CLEAN_API4_192659_RECOVERY_CASE_TABLE.{md,json}`
  - manual cluster audit: `P29_CLEAN_API4_192659_MANUAL_CLUSTER_AUDIT_20260701.{md,json}`
  - meta confirms `code_commit=d08b81e`, `code_dirty=clean`, `api_max_workers=4`, `max_tokens=1536`, `api_max_retries=8`, `api_timeout=600`, `review_issue_bundle=1`; run finished 20/20 in about 34 minutes.
- P29 clean API4 headline metrics:
  - Protection PASS; `negative_evidence_unlinked_to_flaw=0`, `positive_or_neutral_negative_candidate_count=0`, `negative_grounding_conflict_count=0`, `semantic_negative_without_review_relation_count=0`.
  - Evidence JSON reliability is no longer the bottleneck in this run: `evidence_json_valid_turns=61`, `evidence_json_fallback_turns=0`, `evidence_json_fallback_rate_pct=0`.
  - Direct quote negative lane remains strict and empty: `review_negative_verified_count=0`.
  - Obligation-grounded issue lane: `verified_review_issue_count=22`, `verified_review_issue_cluster_count=18`, `quote_duplicate_merged_verified_review_issue_cluster_count=18`.
  - Discovery origin is still mostly deterministic: `reviewer_candidate_review_issue_critique_payload_count=2`, `reviewer_candidate_review_issue_deterministic_seed_count=20`; cluster origins are 2 critique-payload vs 16 deterministic-seed.
  - Cluster type mix remains skewed: 10 missing-ablation clusters, 2 missing-baseline clusters, 1 scope/robustness cluster, and 5 protocol/reproducibility clusters.
  - Recovery bridge works but is incomplete: `mark_contested_commit_count=6`, `recovery_case_verified_review_issue_repair=6`, `verified_issue_cluster_without_recovery_count=11`.
- P29 clean API4 manual cluster audit must be used for paper-facing interpretation, not the raw verifier count. Manual first-pass labels over 18 system clusters: `A=3`, `B=3`, `C=3`, `D=9`, `MERGE=0`; strict A/B clusters = 6, permissive A/B clusters = 8. Strong A clusters are ReDrafter recurrent draft model, SpecDec++ acceptance prediction head, and NR-DCCA generalized noise regularization. Defensible B clusters are SPOT unified scene representation, Diff-Shape GrCN reproducibility, and PSRD/PST reproducibility. Risky/false-positive clusters include supplement-coverage/retrieval misses, overbroad protocol targets, counterevidenced LT-MS/HALO/FVL ablation targets, generic FL aggregation, and the RIS baseline overgeneralization.
- Interpretation update: P29 clean API4 proves the pipeline can now run a full20 with 4 API workers, stable JSON, protection PASS, and more verifier-passing issue rows/clusters. It does **not** improve the paper-facing manual A/B result versus the earlier conservative P29/P28.6 interpretation. Do not write "18 true defects" or "P29 achieves 10+ manually valid clusters." Correct wording: "P29 clean API4 produced 22 verifier-passing obligation-grounded issue rows and 18 system clusters; a conservative manual first pass supports 6 strict A/B clusters, or 8 under a permissive reading."
- Next technical work if quantity remains the goal: improve quality before adding more seeds. Priority fixes are stronger counterevidence matching for ablation/protocol claims, better extraction/normalization of malformed targets such as `ional_branch`, stricter rejection of generic mechanisms such as FL aggregation/local network updates and one-head architecture descriptions, and more genuine Critique-payload discovery so deterministic reviewer seeds do not dominate the result.

## P30 Quality Hardening and Fresh Full20 (2026-07-01)

P30 is a precision/hygiene hardening pass after the P29 clean API4 manual audit. It is not a quantity-expansion pass. The accepted diagnosis was that P29's `22` verifier-passing rows / `18` clusters contained too many D-class false positives: missed counterevidence, malformed or generic missing-ablation targets, supplement/retrieval gaps treated as reproducibility defects, and one harmful destructive recovery commit.

Code changes:

- Missing-ablation target quality now rejects weak/generic/malformed targets such as `it only comprises one head`, `via aggregation of local network`, `ional branch`, `carefully initialize the hyperbolic network`, generic encoder/decoder/network/module/component targets, and ordinary action fragments.
- Semantic counterevidence was strengthened for ablation cases: total/overall loss gaps can be blocked by regularization/lambda/distillation/data-update ablations; quadratic/space-time motion model gaps can be blocked by component ablations covering the polynomial/quadratic motion model; HFR/initialization gaps can be blocked by HFR/initialization ablation or analysis.
- Protocol/reproducibility counterevidence now treats explicit setup/settings/training protocol, dataset split, label-budget, and supplement/appendix hyperparameter/config/implementation pointers as blockers rather than verified defects.
- Scope/robustness counterevidence now blocks stale coverage gaps when the full text contains directly relevant heterophily or large-benchmark evaluations such as OGBN benchmarks.
- Missing-baseline specificity rejects generic/truncated blueprints such as `standard RIS/segmentation baselines and datasets used by the claim scope`.
- Recovery now treats obligation-grounded review issues as non-destructive only. Model-generated `downgrade_claim_to_unsupported` patches citing obligation-grounded issue evidence are rebuilt into `mark_contested`; claim-status downgrades from paper-absence-audit / obligation-grounded issue evidence are blocked.
- Dashboard protection now includes `recovery_harmful_commit_committed == 0`.

Validation:

- `py_compile` passed on the touched Python files.
- Direct regression invocation passed for the new target-guard, counterevidence, supplement/protocol, scope, baseline, and recovery downgrade-to-contested tests. Full `pytest` was unavailable in the local Python environments.
- Offline recompute on the P29 raw run (`20260701_192659`) produced `11` verified rows / `7` clusters; this confirmed the stricter guard removes many P29 D-class rows, but the old raw still has `recovery_harmful_commit_committed=1` because offline recompute cannot rewrite historical recovery logs.

Authoritative P30 fresh full20 rerun:

- raw/log/meta: `mimo_v25_negqty_recoverycap_guard3_qhyg_targetneg_freeformrevneg_reviewissuebundle_hardneg20_mt7_b4w2_api4_r8t600_tok1536_20260701_211251.{jsonl,log,meta}`
- dashboard: `P30_FRESH_API4_211251_HARDNEG20_DASHBOARD.{md,json}` plus audit JSON
- review issue case table: `P30_FRESH_API4_211251_REVIEW_ISSUE_CASE_TABLE.{md,json}`
- recovery table: `P30_FRESH_API4_211251_RECOVERY_CASE_TABLE.{md,json}`
- full20 completed 20/20 with MiMo API4, `max_turns=7`, `max_tokens=1536`, `api_max_workers=4`, `api_max_retries=8`, `api_timeout=600`.

P30 fresh headline metrics:

- Protection PASS, including the new hard line `recovery_harmful_commit_committed=0`.
- Evidence JSON remains healthy: `evidence_json_valid_turns=67`, `evidence_json_fallback_turns=0`, `evidence_json_fallback_rate_pct=0`.
- Direct quote-grounded negative lane remains strict and empty: `review_negative_verified_count=0`.
- Obligation-grounded issue lane after quality guard: `verified_review_issue_count=13`, `verified_review_issue_cluster_count=12`, `duplicate_review_issue_row_count=1`.
- Type mix: `6` missing-ablation clusters, `1` missing-baseline cluster, `2` scope/robustness clusters, and `3` protocol/reproducibility clusters.
- Discovery remains seed-dominated: `reviewer_candidate_review_issue_critique_payload_count=0`, `reviewer_candidate_review_issue_deterministic_seed_count=13`; cluster origins are `12` deterministic seed clusters and `0` Critique-payload clusters.
- Funnel: `review_issue_candidate_total=88`, `verified=13`, `counterevidence_rejected=44`, `missing_inventory_rejected=22`, `review_worthiness_rejected=11`, `missing_ablation_target_rejected=9`, `missing_baseline_target_rejected=7`.
- Recovery bridge is clean and non-destructive: `mark_contested_commit_count=8`, `recovery_case_verified_review_issue_repair=8`, `turns_with_verified_review_issue_bundle_evidence=8`, `verified_issue_cluster_without_recovery_count=4`.

Interpretation update:

- P30 successfully fixes the most important P29 safety failure: harmful destructive recovery is gone on a fresh run, and quality guards remove many weak P29 false positives.
- P30 does not satisfy the earlier quantity target of `20+` rows. It deliberately trades quantity for precision, ending at `13` rows / `12` clusters.
- The paper-facing result should not be "P30 finds more defects." Correct wording: "P30 shows that stricter counterevidence and recovery hygiene preserve a clean full20 run with 13 verifier-passing obligation-grounded rows / 12 clusters and zero harmful recovery commits."
- The remaining bottleneck is autonomous discovery quality, not verifier looseness. Critique-payload verified issues are still `0`; deterministic seeds dominate. If the next goal is more validated defects, the next pass should improve Critique candidate generation with entity-level menus and stronger observed-inventory grounding, while keeping the P30 verifier and recovery guards.

## P31 Planning Note: Critique Payload Discovery Integration Gap (2026-07-01)

P30 follow-up audit clarified that Critique payload discovery is not absent; it is failing to connect to the verifier-ready obligation/inventory path. In the P30 fresh full20 raw run, Critique produced `31` `review-issue-candidate-*` payload candidates, but `0` became verified review issues. The verified P30 issues (`13` rows / `12` clusters) were all deterministic-seed driven.

Per-candidate failure attribution over the 31 Critique payload candidates:

- `no_selected_requirement`: 12
- full-text counterevidence: 10 (`baseline/comparison`, `ablation`, `protocol/result`, and `evaluation/scope` counterevidence)
- missing-ablation target quality failures: 5 (`weak_action`, `empty`, or not bound to claim/inventory)
- generic/truncated missing-baseline target: 2
- missing inventory: 1

Interpretation:

- The main failure is not JSON reliability or MiMo's inability to propose reviewer-style concerns. Critique can propose plausible candidates, but the downstream path still treats model candidates mostly as selectors over the existing type-level claim-requirement audit.
- `_render_critique_state_slice` exposes `review_issue_discovery_targets` by reusing `_hard_negative_diagnosis_targets`; this is a diagnosis view, not a verifier-ready candidate menu. Deterministic seeds have access to stronger structured obligation + inventory anchors internally, so they survive more often.
- `_reviewer_candidate_absence_gap_items` requires a candidate to select a missing claim requirement or pass a narrow candidate-introduced override. Reasonable narrower review issues can die when the broad requirement is already marked satisfied by any support evidence.
- Most counterevidence and target-quality rejections are desirable and should not be fixed by loosening the verifier.

Recommended P31 direction:

- Add a verifier-ready `review_issue_candidate_menu_for_claim` shown to Critique. Each menu item should expose `candidate_menu_id`, `obligation_id`, `claim_id`, `issue_type`, `required_evidence_type`, `expected_entity`, `inventory_id`, copied inventory quote/list/table anchor, locator, and target-quality hints. It must remain non-evidence.
- Update `REVIEW_ISSUE_DISCOVERY_PROMPT` so Critique preferentially selects or lightly rewrites menu items and returns `candidate_menu_id`/`obligation_id`; free-form candidates are allowed only when they provide a concrete entity and locatable observed-inventory anchor.
- Add candidate-to-menu rebinding in `_reviewer_candidate_absence_gap_items`: when a Critique candidate matches a verifier-ready menu item by claim/type/entity, copy the menu requirement and inventory anchor, set `discovery_origin=critique_payload_menu_bound`, and then run the same strict bundle verifier.
- Widen the safe introduced-requirement path only for claim-bound, inventory-grounded candidates. For baseline, ablation, scope, protocol, and reproducibility issues, a Critique candidate may enter bundle verification even if the broad requirement is currently satisfied, but only when it has a locatable observed inventory anchor and an auditable paper-surface expectation. Counterevidence and worthiness gates stay unchanged.
- Add dashboard funnel metrics split by origin: `critique_payload_rejected_by_reason`, `critique_payload_gap_count`, `critique_payload_bundle_built_count`, `critique_payload_menu_bound_count`, `critique_payload_verified_count`, and `critique_payload_verified_cluster_count`.
- Keep deterministic seeds as fallback/verifier stress tests, not the paper-facing autonomous discovery story.

Safety fixes to include with P31 if implementation proceeds:

- Recovery downgrade-to-contested logic should gather cited issue/evidence ids from `supporting_evidence_ids`, `negative_evidence_ids`, and `evidence_ids`; the current code only checks `supporting_evidence_ids`, so some safe `mark_contested` opportunities are missed.
- Reject generic protocol missing items such as `explicit evaluation protocol details for protocol`; explicit split/training-setting quotes should count as counterevidence for such generic protocol issues.
- Reject malformed missing-ablation targets such as `ranch_encoder` and keep plain `global encoder` out of verified issues unless explicitly contribution-bound.

## P31 Implementation Checkpoint: Candidate Menu Plumbing (2026-07-01)

P31 first implementation batch is now in the working tree, but it is not yet a fresh-run result. The changes move Critique discovery toward verifier-ready candidate selection without relaxing the P30 verifier:

- `review_issue_candidate_menu` is generated per diagnosis target from the same obligation/inventory substrate used by deterministic seeds. Menu items carry `candidate_menu_id`, `claim_id`, `obligation_id`, `issue_type`, `required_evidence_type`, `expected_entity`, entity source, observed inventory quote/list/table anchor, target-quality hint, and counterevidence search terms. Menu items remain non-evidence.
- `REVIEW_ISSUE_DISCOVERY_PROMPT` now asks Critique to prefer selecting or lightly refining a menu item, and to copy `candidate_menu_id`, `obligation_id`, expected entity, issue type, requirement, observed inventory anchor, and counterevidence terms.
- `normalize_review_update_payload` preserves `candidate_menu_id`, `review_issue_slot`, `entity_source`, `discovery_origin`, and `possible_counterevidence_terms` on reviewer issue candidates.
- `_reviewer_candidate_absence_gap_items` now performs candidate-to-menu rebinding by explicit `candidate_menu_id` or claim/type/entity token match. Bound candidates copy the menu requirement, missing entity, obligation id, inventory anchor, entity source, and counterevidence terms, and are marked with `discovery_origin=critique_payload_menu_bound` before entering the unchanged strict bundle verifier.
- Verified bundle/evidence/review-issue records now preserve `candidate_menu_id` and menu metadata so dashboard, case table, and recovery audits can distinguish menu-bound Critique issues from deterministic seeds.
- Dashboard/case-table metrics now expose origin-split funnel fields: `critique_payload_gap_count`, `critique_payload_menu_bound_count`, `critique_payload_bundle_built_count`, `critique_payload_verified_count`, `critique_payload_menu_bound_verified_count`, `critique_payload_verified_cluster_count`, `candidate_menu_item_count`, `candidate_menu_item_used_count`, and `candidate_menu_item_verified_count`.
- Safety fixes landed with this batch: destructive claim downgrades citing verified issue evidence are detected from `supporting_evidence_ids`, `negative_evidence_ids`, or `evidence_ids`; generic protocol targets like `explicit evaluation protocol details for protocol` are rejected; malformed ablation target `ranch_encoder` is rejected.

Validation:

- `py_compile` passes for touched runtime files, scripts, and tests.
- Local Python environments do not have `pytest`; focused direct Python assertions passed for candidate-menu normalization, menu-bound Critique bundle verification, generic protocol rejection, `ranch_encoder` rejection, and recovery id-union detection.
- Offline recompute on P30 fresh raw (`20260701_211251`) produced `P31_MENU_RECOMPUTE_211251_*` dashboard and case-table artifacts with protection PASS. Because the raw run predates the menu prompt, verified Critique/menu contribution remains `0`; however the new funnel shows Critique candidates are now auditable: `review_issue_candidate_critique_payload_count=31`, `critique_payload_gap_count=18`, `critique_payload_menu_bound_count=5`, `critique_payload_verified_count=0`, `candidate_menu_item_count=98`.

Interpretation:

- This checkpoint proves the P31 plumbing and metrics work on historical raw data. It does not prove autonomous Critique discovery improved yet.
- The next necessary evidence is a fresh MiMo hardneg20 run with the P31 prompt/menu code. Acceptance should use the roadmap gates: protection PASS, `recovery_harmful_commit_committed=0`, and ideally `critique_payload_verified_cluster_count >= 3` without manual A/B quality regression.

## P31 Fresh API4 Full20 and Reporting Hotspot Fix (2026-07-02)

P31 fresh run attempt `20260701_234505` was terminated as a partial diagnostic run:

- raw: `mimo_v25_negqty_recoverycap_guard3_qhyg_targetneg_freeformrevneg_reviewissuebundle_hardneg20_mt7_b4w2_api4_r8t600_tok1536_20260701_234505.jsonl`
- status: partial `4/20`.
- failure mode: the second batch stalled on `XyB4VvF01X`; MiMo API calls had completed, but the Python process stayed at ~99% CPU with no new log output. macOS `sample` showed the process dominated by Python regex/string operations.
- diagnosis: P31 final-view/dashboard metrics were observationally useful but too heavy. They re-entered menu/gap/full-text/counterevidence computation during hygiene/report generation instead of only reading already verified runtime records.

Code/reporting fixes:

- `_review_issue_candidate_funnel_metrics` is now lightweight and observational. It no longer reruns candidate menu lookup, `_reviewer_candidate_absence_gap_items`, paper-inventory search, review-worthiness checks, or full-text counterevidence during final-view metric aggregation. The strict verifier remains on the real bundle verification path.
- `scripts/dashboard_run_comparison_v1.py` now uses cached runtime hygiene from `decision_hygiene` or `state_audit.decision_hygiene` before rebuilding `build_decision_hygiene_view`.
- Dashboard cluster-origin metrics now use cached verified bundle/direct-negative labels instead of rerunning state-level negative/review-issue verifiers over every evidence row.
- Dashboard support trace no longer rebuilds support survival trace when no cached trace is present.
- `scripts/audit_review_issue_case_table_v1.py` and `scripts/audit_recovery_case_table_v1.py` now use cached hygiene when present. The review issue case table additionally uses cached `review_issue_bundle_items` as the authoritative row filter, so case-table row count matches runtime dashboard count rather than current-code offline revalidation.
- Validation: `py_compile` passed for touched runtime/report scripts. P30 fresh raw dashboard/case/recovery generation to `/tmp` completed quickly after the fixes and protection remained PASS.

Authoritative P31 fresh full20 rerun:

- raw/log/meta: `mimo_v25_negqty_recoverycap_guard3_qhyg_targetneg_freeformrevneg_reviewissuebundle_hardneg20_mt7_b4w2_api4_r8t600_tok1536_20260702_004622.{jsonl,log,meta}`
- dashboard: `P31_FRESH_API4_004622_HARDNEG20_DASHBOARD.{md,json}` plus `P31_FRESH_API4_004622_HARDNEG20_AUDIT.json`
- review issue case table: `P31_FRESH_API4_004622_REVIEW_ISSUE_CASE_TABLE.{md,json}`
- recovery table: `P31_FRESH_API4_004622_RECOVERY_CASE_TABLE.{md,json}`
- manual cluster audit: `P31_FRESH_API4_004622_MANUAL_CLUSTER_AUDIT_20260702.{md,json}`
- latest pointers were updated to the P31 004622 artifacts.

P31 fresh headline metrics:

- Completed 20/20 with MiMo API4, `max_turns=7`, `max_tokens=1536`, `api_max_workers=4`, `api_max_retries=8`, `api_timeout=600`.
- Protection PASS: `negative_evidence_unlinked_to_flaw=0`, `positive_or_neutral_negative_candidate_count=0`, `negative_grounding_conflict_count=0`, `recovery_harmful_commit_committed=0`.
- Evidence JSON remains healthy: `evidence_json_fallback_rate_pct=0`.
- Direct quote-grounded negative lane remains strict and empty: `review_negative_verified_count=0`.
- Obligation-grounded issue lane: `verified_review_issue_count=19`, `verified_review_issue_cluster_count=14`, `duplicate_review_issue_row_count=5`.
- Discovery origin improved but remains seed-dominated: `reviewer_candidate_review_issue_critique_payload_count=1`, `reviewer_candidate_review_issue_deterministic_seed_count=18`, `critique_payload_verified_count=1`, `critique_payload_verified_cluster_count=1`, `deterministic_seed_verified_cluster_count=13`.
- Candidate menu metrics show a mismatch: `candidate_menu_item_count=3`, `candidate_menu_item_verified_count=3`, but `candidate_menu_item_used_count=0`. Some verified records carry menu ids, but Critique candidates still did not select menu ids directly.
- Recovery remains clean: `mark_contested_commit_count=9`, `recovery_case_verified_review_issue_repair=8`, `turns_with_verified_review_issue_bundle_evidence=8`, `verified_issue_cluster_without_recovery_count=7`.

Manual cluster audit:

- Initial case-table audit over 14 runtime clusters: `A=3`, `B=5`, `C=4`, `D=1`, `MERGE=1`; strict A/B clusters = `8`.
- A-class clusters: SpecDec++ acceptance prediction head missing ablation, NR-DCCA generalized noise regularization missing ablation, HALO/EqualAL same-setting missing baseline.
- B-class clusters include SPOT sz-Softmax loss ablation, Diff-Shape GrCN reproducibility, ReDrafter recurrent draft model ablation, LogoRA global encoder ablation, and the single Critique-origin sparse/linear graph-transformer baseline concern.
- D-class cluster: `7Dub7UXTXN` simulated-loss missing ablation, which appears to turn a theory/loss-analysis claim into an empirical ablation demand.
- MERGE cluster: the two `cklg91aPGk` GCL coverage/scope clusters are same-paper/same-target duplicates and should not be counted independently.

Interpretation:

- P31 is a partial success. It moves Critique-origin verified clusters from `0` to `1`, while preserving protection PASS and recovery safety.
- P31 does **not** satisfy the roadmap target `critique_payload_verified_cluster_count >= 3`. Do not claim autonomous Critique discovery is solved.
- P31's paper-facing line should be: "P31 produced 19 runtime-counted verifier-passing rows / 14 clusters with 8 initial A/B clusters, including one Critique-origin A/B cluster, under strict protection and non-destructive recovery."
- Remaining bottleneck: Critique does not reliably use the verifier-ready menu. Next work should make Critique a menu selector/refiner, reduce menu prompt length, and add a guard against theory/loss-analysis claims being converted into empirical missing-ablation defects.

Follow-up code changes after the P31 fresh audit:

- Added a missing-ablation target-quality guard for theory/loss-analysis contexts. Loss targets such as `component-isolation ablation for simulated loss` are rejected when the claim/inventory context is theorem/learning-dynamics/global-minimum/expressivity oriented and lacks empirical benchmark/performance framing.
- Kept empirical contribution-bound loss targets valid: `sz-Softmax loss` style targets remain high/medium when tied to benchmark/performance context.
- Strengthened `REVIEW_ISSUE_DISCOVERY_PROMPT` so menu-derived candidates must copy `candidate_menu_id` exactly; free-form candidates without a menu id must explain why no menu item fits and provide their own copied inventory anchor.
- Added focused regression assertions in `tests/test_review_decision_hygiene.py`; direct invocation passed for target-quality and existing theory-anchor rejection tests. `py_compile` passed for touched runtime/prompt/test files.
- No fresh MiMo rerun has been run after these follow-up code changes yet. The next fresh run should check whether `candidate_menu_item_used_count` rises above 0 and whether `critique_payload_verified_cluster_count` moves toward the P31 target of 3.

## P31.3 Fresh API4 131007 Checkpoint and Manual Audit (2026-07-02)

P31.3 follow-up found and addressed a runtime hotspot before the authoritative run:

- Fresh attempt `20260702_124240` stalled at `8/20`; sampling showed hot CPU in Python regex/string scanning during finalization.
- Runtime scan caps were added to `_paper_has_with_without_target_counterevidence`, `_paper_has_ablation_counterevidence_for_missing_claim`, and `_review_issue_full_text_structural_windows`.
- This was a performance boundary only; the strict verifier semantics were not relaxed.

Authoritative P31.3 rerun:

- raw/log/meta: `mimo_v25_negqty_recoverycap_guard3_qhyg_targetneg_freeformrevneg_reviewissuebundle_hardneg20_mt7_b4w2_api4_r8t600_tok1536_20260702_131007.{jsonl,log,meta}`
- dashboard: `P31_3_FRESH_API4_131007_HARDNEG20_DASHBOARD.{md,json}` plus `P31_3_FRESH_API4_131007_HARDNEG20_AUDIT.json`
- review issue case table: `P31_3_FRESH_API4_131007_REVIEW_ISSUE_CASE_TABLE.{md,json}`
- recovery table: `P31_3_FRESH_API4_131007_RECOVERY_CASE_TABLE.{md,json}`
- result audit: `P31_3_FRESH_API4_131007_RESULT_AUDIT_20260702.md`
- manual cluster audit: `P31_3_FRESH_API4_131007_MANUAL_CLUSTER_AUDIT_20260702.{md,json}`
- selector menu failure audit: `P31_4_SELECTOR_MENU_FAILURE_AUDIT_20260702.md`
- latest pointers now target the `131007` artifacts.

P31.3 headline metrics:

- Completed 20/20 with MiMo API4.
- Protection PASS: `negative_evidence_unlinked_to_flaw=0`, `positive_or_neutral_negative_candidate_count=0`, `negative_grounding_conflict_count=0`, `recovery_harmful_commit_committed=0`.
- Evidence JSON remained clean: `evidence_json_valid_turns=63`, `evidence_json_fallback_turns=0`, `evidence_json_fallback_rate_pct=0`.
- Direct quote-grounded negative lane remained strict and empty: `review_negative_verified_count=0`.
- Obligation-grounded review issues: `verified_review_issue_count=14`, `verified_review_issue_cluster_count=11`, `duplicate_review_issue_row_count=3`.
- Critique selector improved but did not meet the target: `critique_payload_verified_cluster_count=2`, `candidate_menu_item_used_count=6`, `candidate_menu_item_verified_count=1`.
- Discovery remained seed-dominated: `verified_review_issue_cluster_origin_critique_payload_count=2`, `verified_review_issue_cluster_origin_deterministic_seed_count=8`, `verified_review_issue_cluster_origin_claim_obligation_fallback_count=3`.
- Recovery remained non-destructive: `mark_contested_commit_count=8`, including `recovery_case_verified_review_issue_repair=6`.

Manual cluster audit over 11 verifier-passing clusters:

- `A=1`, `B=4`, `C=3`, `D=3`, so initial paper-facing A/B clusters are about `5`.
- Strongest retained cluster: `NnExMNiTHw / acceptance_prediction_head` missing ablation.
- Critique-origin A/B clusters: `XyB4VvF01X / implementation_reproducibility_details` and `mHv6wcBb0z / non-DCCA multi-view learning baselines`.
- D-class regression targets:
  - `a6SntIisgg / global_encoder`: likely blocked by explicit ablation table/component evidence.
  - `fGXyvmWpw6 / effect_distillation_steps_architecture_choices_has_been_studied`: malformed ablation target.
  - `xUe1YqEgd6 / frame-by-frame_module`: contrast/baseline framing treated as a current-paper module.

Interpretation:

- P31.3 is a real progress checkpoint: runtime is fixed, protection remains clean, recovery improved, and Critique-origin verified clusters increased from 1 to 2.
- P31.3 is not complete against the roadmap: the target `critique_payload_verified_cluster_count >= 3` was not met, and manual A/B clusters are about 5, below the validation target of 6.
- Do not proceed to P32 reproducibility yet. P31.4 selector failure audit is now recorded in `P31_4_SELECTOR_MENU_FAILURE_AUDIT_20260702.md`. The 6 menu-used candidates produced only 1 verified case; failures mainly involve generic OOD/stress targets, scalability-to-cost inference without resource anchors, generic strong-baseline targets, theory-reproducibility targets, and one qualitative-vs-quantitative result-table gap that is not yet cleanly typed.
- Next implementation target: add candidate-level failed-menu telemetry, then add selector/menu guards for these failure classes without relaxing the strict bundle verifier.

## P31.4 Selector/Menu Precision Checkpoint 1 (2026-07-02)

Implemented after `P31_4_SELECTOR_MENU_FAILURE_AUDIT_20260702.md`:

- `decision_hygiene` now records candidate-level failed-menu telemetry:
  - `candidate_menu_item_failed_count`
  - `candidate_menu_item_failed_by_reason`
  - `failed_menu_candidate_items`
- Dashboard aggregation now reports `candidate_menu_item_failed_count` and main failed-menu reason counters.
- Menu generation and candidate-to-gap paths now reject generic selected-menu targets before verifier materialization:
  - generic OOD/stress/scope targets without concrete dataset/setting/shift;
  - efficiency-cost targets inferred only from broad scalability/transferability wording without resource anchors;
  - generic strong-baseline targets such as `other strong one-shot NAS baselines`;
  - theory/loss-analysis reproducibility targets that ask for generic hyperparameters/split/seed/code without concrete empirical experiment anchors.
- Missing-ablation target quality now rejects already-studied phrases such as `effect ... has been studied module` and contrast/baseline-as-module targets such as `frame-by-frame module`.
- Bundle worthiness now rejects the `global_encoder` pattern when the claim/inventory already reports component ablation coverage.

Validation:

```text
py_compile state.py/dashboard/tests = passed
new P31.4 focused tests = 5 passed
P31 selector/rebinding focused tests = 14 passed
P31 inference prompt/runtime focused tests = 5 passed
```

Uncached current-code recompute on old `131007` raw states:

```text
papers = 20
verified_review_issue_count = 8
verified_review_issue_cluster_count = 6
critique_payload_verified_cluster_count = 2
candidate_menu_item_used_count = 6
candidate_menu_item_verified_count = 1
candidate_menu_item_failed_count = 5
failed reasons = {
  reproducibility_menu_theory_context: 1,
  scope_menu_generic_target: 1,
  efficiency_cost_menu_without_resource_anchor: 1,
  missing_baseline_menu_generic_target: 2
}
protection counters remain 0
```

Interpretation:

- This is a precision-control checkpoint, not a fresh API result.
- The previously opaque five selected-menu failures are now explainable at candidate level.
- The old raw run drops from 14 rows / 11 clusters to 8 rows / 6 clusters under current-code recompute, which is expected after blocking the D-class and generic menu targets.
- Next design decision: either add a narrow `qualitative_vs_quantitative_result_gap` lane and safe named-baseline normalization, or leave those candidates diagnosis-pending with explicit failed-menu reasons. Do not proceed to P32 or a fresh rerun until that choice is made.

## P31.4 Selector/Menu Precision Checkpoint 2 (2026-07-02)

Implemented next:

- Safe named-baseline normalization for missing-baseline reviewer candidates:
  - only applies when the original missing item is generic;
  - requires at least two concrete baseline names in the candidate's verification question / counterevidence terms;
  - rewrites them into concrete items such as `same-setting comparison against SNAS baseline`;
  - still requires observed comparison inventory and full-text counterevidence survival.
- Qualitative-vs-quantitative result-table gaps are kept diagnosis-pending with explicit failed-menu reason `qualitative_vs_quantitative_result_gap_unsupported_type`; no new negative type was added in this batch.
- Baseline counterevidence terms now treat task/dataset words such as `NAS`, `one-shot`, `CIFAR-10`, and `ImageNet` as generic, so a table mentioning RandomNAS/GDAS on CIFAR-10 does not automatically cover missing SNAS/DARTS/ProxylessNAS.
- Dashboard now reports `candidate_menu_item_failed_qualitative_vs_quantitative_result_gap_unsupported_type`.

Validation:

```text
py_compile state.py/dashboard/tests = passed
P31.4 taxonomy/normalization focused tests = 5 passed
P31 selector/rebinding focused tests = 16 passed
P31 inference prompt/runtime focused tests = 5 passed
```

Uncached current-code recompute on old `131007` raw states:

```text
papers = 20
verified_review_issue_count = 8
verified_review_issue_cluster_count = 6
critique_payload_verified_cluster_count = 2
candidate_menu_item_used_count = 6
candidate_menu_item_verified_count = 1
candidate_menu_item_failed_count = 5
failed reasons = {
  reproducibility_menu_theory_context: 1,
  scope_menu_generic_target: 1,
  efficiency_cost_menu_without_resource_anchor: 1,
  qualitative_vs_quantitative_result_gap_unsupported_type: 1,
  not_verified_by_bundle: 1
}
protection counters remain 0
```

Interpretation:

- The qualitative-vs-quantitative case is now explicitly classified instead of hidden under generic baseline failure.
- Safe named-baseline normalization is implemented and tested, but old `KOUAayk5Kx` still remains `not_verified_by_bundle`; this should not be forced through by loosening the baseline verifier.
- Next useful step is deeper per-candidate bundle stop-stage telemetry for selected menu candidates that reach `not_verified_by_bundle`, so the remaining blockage can be attributed precisely.

## P31.4 Selector/Menu Precision Checkpoint 3 (2026-07-02)

Implemented deeper stop-stage telemetry for menu-bound reviewer candidates:

- `_build_review_issue_bundle_from_gap` now records bundle rejection reason/stage on the gap before returning `None`.
- `_add_reviewer_absence_audit_artifacts` collects these records into `review_issue_candidate_bundle_failures`.
- `decision_hygiene.failed_menu_candidate_items` now uses the true bundle failure detail when a selected-menu candidate would otherwise be reported as `not_verified_by_bundle`.
- Dashboard now reports `candidate_menu_item_failed_by_stage` plus fixed counters for menu-quality, counterevidence, and `missing_entity_already_observed_in_inventory`.
- Added a regression test for a menu-bound missing-baseline candidate blocked by paper-side counterevidence; it must report `stop_stage=counterevidence`.

Validation:

```text
py_compile state.py/dashboard/tests = passed
P31.4 bundle-stop focused tests = 4 passed
P31 selector/rebinding focused tests = 17 passed
P31 inference prompt/runtime focused tests = 5 passed
```

Uncached current-code recompute on old `131007` raw states:

```text
artifacts = P31_4_BUNDLESTOP_RECOMPUTE_131007_*
papers = 20
verified_review_issue_count = 8
verified_review_issue_cluster_count = 6
critique_payload_verified_cluster_count = 2
candidate_menu_item_used_count = 6
candidate_menu_item_verified_count = 1
candidate_menu_item_failed_count = 5
candidate_menu_item_failed_by_reason = {
  reproducibility_menu_theory_context: 1,
  scope_menu_generic_target: 1,
  efficiency_cost_menu_without_resource_anchor: 1,
  qualitative_vs_quantitative_result_gap_unsupported_type: 1,
  missing_entity_already_observed_in_inventory: 1
}
candidate_menu_item_failed_by_stage = {
  menu_quality_guard: 4,
  counterevidence: 1
}
candidate_menu_item_failed_not_verified_by_bundle = 0
negative_evidence_unlinked_to_flaw = 0
positive_or_neutral_negative_candidate_count = 0
negative_grounding_conflict_count = 0
```

Interpretation:

- The remaining selected-menu failures are now explainable: four are selector/menu target-quality problems; one is correctly blocked because the supposedly missing baseline/entity is already observed in paper inventory.
- This checkpoint improves observability and precision; it is not a fresh API result and does not increase verified issue quantity.
- Next P31 work should improve menu generation/selection quality and decide whether to add a narrow qualitative-vs-quantitative result-table issue type. Do not relax bundle verification to recover these cases.

## P31.4 Selector/Menu Precision Checkpoint 4-5 (2026-07-02)

Implemented two follow-up changes after bundle stop-stage telemetry:

1. Narrow qualitative-vs-quantitative result-gap handling:
   - Added a narrow remap for Critique/menu candidates that ask for a direct quantitative same-setting result table after only qualitative/textual comparison evidence.
   - Reuses existing `result_claim_mismatch`; no broad new negative type was added.
   - Requires a concrete target and still runs claim-anchor, inventory-anchor, and full-text counterevidence checks.
   - The old `xUe1YqEgd6` DAVIS2017-motion candidate is now typed correctly but rejected correctly because the paper has Table 3 quantitative DAVIS2017-motion results.

2. Selector-diverse menu input:
   - `_select_review_issue_candidate_menu_items` now first selects the best item from distinct review slots, then tops up by the existing rank under per-type caps.
   - Critique-visible selector menu budget increased from 4 to 6.
   - This is intended to improve the next fresh run's Critique selector input; it cannot change old raw model outputs.

Validation:

```text
py_compile state.py/dashboard/tests = passed
qualitative-vs-quantitative focused tests = 2 passed
menu/selector focused tests = 10 passed
P31 selector/rebinding focused tests = 18 passed
P31 inference prompt/runtime focused tests = 5 passed
dashboard recompute on old raw = protection PASS
```

Old-raw recompute facts:

```text
P31_4_QUALRESULT_RECOMPUTE_131007_*:
  verified_review_issue_count = 8
  verified_review_issue_cluster_count = 6
  critique_payload_verified_cluster_count = 2
  candidate_menu_item_failed_full_text_protocol_or_result_counterevidence = 1
  protection counters = 0

P31_4_SELECTORDIVERSE_RECOMPUTE_131007_*:
  verified_review_issue_count = 8
  verified_review_issue_cluster_count = 6
  critique_payload_verified_cluster_count = 2
  candidate_menu_item_used_count = 6
  candidate_menu_item_verified_count = 1
  candidate_menu_item_failed_count = 5
  protection counters = 0
```

Interpretation:

- P31.4 is now a precision/observability and selector-input checkpoint, not a quantity checkpoint.
- The next meaningful evidence is a fresh API run with the selector-diverse prompt; success target remains `critique_payload_verified_cluster_count >= 3` without protection regressions and without lowering bundle verifier standards.

## P31.4 Selector/Menu Decision Checkpoint 6 (2026-07-02)

Implemented a lightweight selected-menu decision path so Critique does not have to copy a full candidate object for every menu selection:

- `REVIEW_ISSUE_DISCOVERY_PROMPT` now allows `selected_menu_items` and `rejected_menu_items`.
- `normalize_review_update_payload` preserves selected/rejected menu decisions.
- `review_runner` expands selected visible selector-menu ids into pending verifier-ready reviewer issue candidates before deterministic seed top-up.
- Expansion is limited to current visible menu ids; hallucinated/stale menu ids are ignored.
- Expanded items remain hypotheses (`quote_grounding_mode=absence_or_requirement_gap`, `status=pending_absence_audit`) and still run through the same strict bundle verifier; no evidence/flaws are created by selection metadata.
- Dashboard now reports `review_issue_selected_menu_recovery_turns` and `review_issue_selected_menu_recovered_count`.

Validation:

```text
py_compile state.py/review_runner.py/review_prompts.py/dashboard/tests = passed
selected-menu recovery + prompt/parser focused tests = 8 passed
P31 menu/rebinding focused tests = 9 passed
dashboard recompute on old raw = protection PASS
```

Old-raw recompute:

```text
P31_4_MENUDECISION_RECOMPUTE_131007_*:
  verified_review_issue_count = 8
  verified_review_issue_cluster_count = 6
  critique_payload_verified_cluster_count = 2
  candidate_menu_item_used_count = 6
  candidate_menu_item_verified_count = 1
  candidate_menu_item_failed_count = 5
  review_issue_selected_menu_recovery_turns = 0
  review_issue_selected_menu_recovered_count = 0
  protection counters = 0
```

Interpretation:

- This checkpoint affects future Critique outputs. Old raw outputs predate `selected_menu_items`, so the new dashboard counters are 0 there.
- Next fresh API run should check whether Critique uses this lighter channel and whether `critique_payload_verified_cluster_count` reaches the P31 target of at least 3.

## P31.4 Menu-Fix Checkpoint 7 (2026-07-02)

Implemented and validated a plumbing/observability fix for the selected-menu path. This does not relax the review-issue bundle verifier.

Code logic now:

- Critique may output full `review_issue_candidates` or lightweight `selected_menu_items`.
- `selected_menu_items` are selection metadata only. They create no evidence/flaws and are expanded only into pending reviewer issue candidates.
- The runner now accepts a selected menu id if it can be regenerated from the current prompt's per-claim menu, not just the compact selector top-6. Stale/hallucinated ids are still ignored.
- Expanded candidates carry `discovery_origin=critique_payload_menu_selected`, `quote_grounding_mode=absence_or_requirement_gap`, and `status=pending_absence_audit`.
- State/dashboard/case-table provenance now treats all `critique_payload*` origins as Critique-origin, including `critique_payload_menu_selected`.
- Dashboard reads selected-menu recovery telemetry from `runner_trace` as a fallback because older/compact `turn_logs.worker_payloads` may only persist `{agent_id, payload}`.

Validation:

```text
py_compile state.py/review_runner.py/dashboard/case-table/tests = passed
selected-menu recovery focused tests = 5 passed
menu/provenance hygiene focused tests = 5 passed
P31_4_MENUFIX_RECOMPUTE_163953_* protection = PASS
```

Old-raw recompute (`163953`) now exposes the hidden selected-menu event:

```text
verified_review_issue_count = 14
verified_review_issue_cluster_count = 12
critique_payload_verified_cluster_count = 0
review_issue_selected_menu_recovery_turns = 1
review_issue_selected_menu_recovered_count = 1
candidate_menu_item_used_count = 3
candidate_menu_item_verified_count = 1
mark_contested_commit_count = 5
protection counters = 0
```

Fresh validation attempt `20260702_213525` stopped at 8/20 because MiMo returned `402 insufficient account balance` during Critique calls. This run is partial only and must not be treated as authoritative full20.

Partial8 facts:

```text
artifacts = P31_4_MENUFIX_PARTIAL8_213525_*
verified_review_issue_count = 4
verified_review_issue_cluster_count = 4
critique_payload_verified_cluster_count = 0
review_issue_selected_menu_recovery_turns = 1
review_issue_selected_menu_recovered_count = 1
candidate_menu_item_used_count = 1
candidate_menu_item_verified_count = 0
mark_contested_commit_count = 2
protection counters = 0
```

Audit conclusion:

- The selected-menu path really fired: `WpXq5n8yLb` selected `rim-c2-ma-ablation-isolating-dynamic-tree-attent`, which became `review-issue-candidate-selected-menu-1` with `discovery_origin=critique_payload_menu_selected`.
- It was rejected by strict verifier with `missing_ablation_counterevidence_in_claim_or_inventory`; another Critique candidate failed `missing_ablation_target_not_claim_or_inventory_bound`.
- Therefore the current P31.4 bottleneck is not missing runner/normalizer plumbing. It is Critique/menu target quality and counterevidence survival.
- Do not proceed to P32 until a complete full20 run reaches `critique_payload_verified_cluster_count >= 3`, protection remains PASS, and manual A/B quality does not regress.

## P31.5 Target-Quality Checkpoint 1 (2026-07-02)

Continued P31 without relaxing the review-issue bundle verifier.  This checkpoint is a selector/menu quality guard, not a quantity run.

Code logic added/validated:

- Menu generation now omits missing-ablation menu items when the proposed target is already resolved by claim/inventory ablation counterevidence.
- Missing-ablation target quality now treats verb-form `constrain/constraining` targets as weak-action fragments.  This rejects malformed items such as `component-isolation ablation for constrain module` while preserving noun/mechanism targets such as `constraint module` as medium-confidence when contribution/performance context exists.
- Component-ablation deterministic seeds now reuse the same target-quality and ablation-counterevidence checks, so malformed preposition fragments such as `component-isolation ablation for by the dynamic tree attention` and already-covered ablation targets do not consume future seed/menu budget.
- Ablation counterevidence resolution now treats local `ablation` figure/table/study anchors as resolving a target when at least two non-generic target tokens match, while explicitly not treating `no/missing/without ablation` as counterevidence.
- Failed selected-menu telemetry now reports stale/filtered selected ids as `selected_menu_item_not_in_current_menu_or_filtered` instead of opaque `not_verified_by_bundle`.
- The selected-menu path remains hypothesis-only: selected items create pending candidates, not evidence; strict bundle verification still decides whether they count.

Validation:

```text
py_compile state.py/review_runner.py/dashboard/case-table/tests = passed
ablation resolver/menu failure focused tests = 4 passed
target/menu/seed selector focused tests = 8 passed
selected-menu recovery focused tests = 5 passed
P31_5_TARGETQUALITY_PARTIAL8_213525_UNCACHED_* protection = PASS
```

Partial8 current-code offline recompute from `20260702_213525` after stripping persisted hygiene caches:

```text
artifacts = P31_5_TARGETQUALITY_PARTIAL8_213525_UNCACHED_*
paper_count = 8
verified_review_issue_count = 4
verified_review_issue_cluster_recomputed_count = 4
quote_duplicate_merged_verified_review_issue_cluster_count = 4
case-table verified review issue cases/clusters = 4
quote-grounded direct cases/clusters = 1
obligation-grounded cases/clusters = 3
critique_payload_verified_cluster_count = 0
review_issue_selected_menu_recovery_turns = 1
candidate_menu_item_used_count = 1
candidate_menu_item_verified_count = 0
candidate_menu_item_failed_selected_menu_item_not_in_current_menu_or_filtered = 1
candidate_menu_item_failed_not_verified_by_bundle = 0
mark_contested_commit_count = 2
protection counters = 0
```

Interpretation:

- Use the `UNCACHED` artifacts for P31.5 current-code audits.  The earlier cached partial8 artifacts can preserve stale `decision_hygiene` and report the old opaque `not_verified_by_bundle` reason.
- The dynamic-tree-attention selected menu item from `WpXq5n8yLb` is now diagnosed as a selected id filtered out of the current menu, which is the expected effect of the ablation-counterevidence guard.
- P31.5 has improved guard coverage, but it has not yet solved the main target: `critique_payload_verified_cluster_count` remains `0`.
- `213525` remains partial only because the original API run stopped at 8/20 on MiMo `402 insufficient account balance`; do not update `.latest_hardneg20_*` or treat these artifacts as full20.
- Next work should continue selector target-quality and menu candidate construction, then run a fresh full20 only when the API balance is available.

## P31.5 Critique-Origin Full20 Checkpoint (2026-07-02)

Continued P31.5 on the complete `20260702_163953` MiMo full20 raw run using an `UNCACHED` current-code recompute.  This is an offline verifier/current-code recompute, not a fresh API rerun.

Artifacts:

```text
source_raw = mimo_v25_negqty_recoverycap_guard3_qhyg_targetneg_freeformrevneg_reviewissuebundle_hardneg20_mt7_b4w2_api4_r8t600_tok1536_20260702_163953.jsonl
uncached_input = P31_5_TARGETQUALITY_FULL20_163953_UNCACHED.jsonl
dashboard = P31_5_TARGETQUALITY_FULL20_163953_UNCACHED_HARDNEG20_DASHBOARD.md/json/audit.json
review_issue_case_table = P31_5_TARGETQUALITY_FULL20_163953_UNCACHED_REVIEW_ISSUE_CASE_TABLE.md/json
recovery_case_table = P31_5_TARGETQUALITY_FULL20_163953_UNCACHED_RECOVERY_CASE_TABLE.md/json
```

Code logic added in this checkpoint:

- Freeform Critique missing-baseline candidates with multiple bare method names are normalized into verifier-ready `same-setting comparison against X baseline` items.  This fixed the KOUA OGL case where `FairNAS/SNAS/ProxylessNAS/EWC/GEM` previously died before bundle verification.
- Single bare acronym normalization remains blocked by default, but is allowed when candidate text explicitly contextualizes the acronym as a baseline/method/comparison target, e.g. `supervised baseline TRIS`.  Full-text counterevidence still blocks stale cases.
- Missing-baseline target specificity now allows non-generic all-caps named methods such as `EWC` and `GEM` while still rejecting generic family acronyms such as `NAS`.
- Gap merge priority now preserves real Critique/freeform attribution over runner seed metadata.  Runner seeds can supplement metadata but cannot overwrite `review-issue-candidate*` candidate ids or `freeform_reviewer_negative` origin.
- Scope/generalization structural cues now include `generalizable/generalizability`, `cross-target`, `target shapes/classes`, and `molecular classes`, fixing the GE6 cross-target validation false negative.
- Bundle expectation can reuse a precomputed non-generic `candidate_obligation_relevance_basis` from the gap stage, fixing the YXn HALO reproducibility candidate without relaxing inventory/counterevidence gates.

Validation:

```text
pytest tests/test_review_decision_hygiene.py focused P31.5 set = 17 passed
pytest tests/test_review_inference_runner.py focused selector/recovery set = 5 passed
py_compile state.py/review_runner.py/dashboard/case-table/tests = passed
dashboard --fail-on-violation = PASS
```

Full20 current-code recompute facts:

```text
paper_count = 20
verified_review_issue_count = 18
verified_review_issue_cluster_recomputed_count = 16
quote_duplicate_merged_verified_review_issue_cluster_count = 16
quote_grounded_review_issue_cluster_count = 1
reviewer_candidate_review_issue_count = 16
reviewer_candidate_review_issue_critique_payload_count = 3
critique_payload_gap_count = 14
critique_payload_bundle_built_count = 3
critique_payload_verified_count = 3
critique_payload_verified_cluster_count = 3
verified_review_issue_cluster_origin_critique_payload_count = 3
reviewer_candidate_review_issue_deterministic_seed_count = 13
candidate_menu_item_used_count = 3
candidate_menu_item_verified_count = 1
candidate_menu_item_failed_not_verified_by_bundle = 0
negative_evidence_unlinked_to_flaw = 0
positive_or_neutral_negative_candidate_count = 0
negative_grounding_conflict_count = 0
mark_contested_commit_count = 5
protection = PASS
```

The three Critique-origin verified clusters are:

```text
GE6iywJtsV: missing_robustness_or_generalization / cross-target validation
YXn76HMetm: reproducibility_gap / hyperbolic curvature and active-learning protocol details
KOUAayk5Kx: missing_baseline / FairNAS, SNAS, ProxylessNAS, EWC, GEM
```

Interpretation:

- P31.5's minimum quantitative target is now met on the complete full20 recompute: `critique_payload_verified_cluster_count = 3` with protection PASS.
- This does not mean all three are paper-ready without manual audit.  The next step before P32 is to manually grade the three Critique-origin clusters and spot-check that the new YXn reproducibility inventory anchor is acceptable for the paper narrative.
- Do not claim a fresh API full20 for this checkpoint; it is a current-code recompute over existing full20 raw state.

## P31.5 Manual Audit / Precision Guard Update (2026-07-03)

Manual audit file:

```text
P31_5_CRITIQUE_ORIGIN_MANUAL_AUDIT_20260703.md
```

Audit result:

- `GE6iywJtsV / cross-target validation`: **B-**, keep with careful wording as limited cross-target/reference-distribution validation, not missing protein-target validation.
- `YXn76HMetm / hyperbolic curvature reproducibility`: **B**, keep as reproducibility concern; note that the inventory anchor is method/pipeline-heavy.
- `KOUAayk5Kx / FairNAS-SNAS-ProxylessNAS-EWC-GEM missing baseline`: **C/D**, reject from verified issue.  Full text says the paper compares with `13 state-of-the-art one-shot NAS competitors`; the named missing list is external and partly off-setting.

Code precision guard added:

```text
full_text_broad_baseline_comparison_counterevidence
```

This blocks freeform reviewer external baseline lists when the paper already
contains a broad same-setting comparison such as `13 state-of-the-art ...
competitors` and none of the named missing baselines appear in the paper text.
The Critique review-issue discovery prompt now carries the matching instruction:
do not invent an external list of well-known baselines when the paper already
reports a broad same-setting comparison set; use paper-named/menu-auditable
baselines instead.

Validation after guard:

```text
focused state pytest = 18 passed
focused runner/prompt pytest = 6 passed
py_compile = passed
dashboard --fail-on-violation = PASS
```

Current full20 metrics after guard:

```text
verified_review_issue_count = 17
verified_review_issue_cluster_recomputed_count = 15
quote_duplicate_merged_verified_review_issue_cluster_count = 15
reviewer_candidate_review_issue_count = 15
reviewer_candidate_review_issue_critique_payload_count = 2
critique_payload_verified_cluster_count = 2
verified_review_issue_cluster_origin_critique_payload_count = 2
negative_evidence_unlinked_to_flaw = 0
positive_or_neutral_negative_candidate_count = 0
negative_grounding_conflict_count = 0
mark_contested_commit_count = 5
protection = PASS
```

Interpretation:

- The pre-audit `critique_payload_verified_cluster_count = 3` is superseded.
- P31.5 is **not P32-ready** after quality audit because quality-preserving Critique-origin clusters are now `2`, below the `>=3` gate.
- Continue P31.5 discovery/selector quality work; do not relax verifier or re-allow external baseline lists unless the missing baseline is paper-named or otherwise auditable from the paper.

## P31.6 Critique-Origin Recovery Attempt (2026-07-03)

Continued P31.5 after the manual audit rejected the KOUA external-baseline
false positive.  The goal remains to recover at least one more A/B-quality
Critique-origin verified cluster before entering P32, without relaxing the
bundle verifier.

Standalone status document:

```text
P31_6_CRITIQUE_ORIGIN_STATUS_20260703.md
```

Code changes:

- Tightened missing-ablation counterevidence so plain method prose such as
  `without needing eigendecomposition` no longer resolves a missing-ablation
  issue.  `with/without` only counts as ablation counterevidence when the local
  window has explicit comparison/result/ablation context.
- Allowed Critique missing-ablation candidates without model-supplied
  `observed_inventory` to reach the strict verifier when the paper text contains
  a locatable component anchor.  The later bundle verifier, target-quality guard,
  and full-text counterevidence checks still decide whether it counts.
- Preserved reviewer-candidate missing targets ahead of template-derived
  claim-obligation entities, so a coarse automatic obligation cannot replace a
  concrete Critique target as the primary missing entity.
- Strengthened `REVIEW_ISSUE_DISCOVERY_PROMPT`: the selector menu is now the
  primary discovery channel; Critique is told to select 2-4 safe menu items when
  available, always copy selected `candidate_menu_id`s into `selected_menu_items`,
  and mirror menu-derived slot candidates there.

Focused validation:

```text
tests/test_review_decision_hygiene.py P31/P31.5 focused set = 21 passed
tests/test_review_inference_runner.py P31 prompt/recovery focused set = 6 passed
py_compile = passed
```

Current-code offline recompute over the existing full20 raw:

```text
artifacts = P31_6_CRITORIGIN_RECOMPUTE_163953_*
dashboard --fail-on-violation = PASS

verified_review_issue_count = 19
verified_review_issue_cluster_recomputed_count = 16
quote_duplicate_merged_verified_review_issue_cluster_count = 16
reviewer_candidate_review_issue_critique_payload_count = 2
critique_payload_verified_cluster_count = 2
verified_review_issue_cluster_origin_critique_payload_count = 2
negative_evidence_unlinked_to_flaw = 0
positive_or_neutral_negative_candidate_count = 0
negative_grounding_conflict_count = 0
mark_contested_commit_count = 5
protection = PASS
```

Interpretation:

- The old full20 raw still does **not** satisfy the P32 entry gate.  The two new
  verified rows released by the counterevidence fix are deterministic-seed rows
  (`ye3NrNrYOY` missing-ablation clusters), not new Critique-origin clusters.
- KOUA OGL missing-ablation remains rejected because the paper contains Figure 5
  with explicit `methods with or without OGL` results; keeping it rejected is the
  safer paper-narrative choice.
- xUe FlyingThings3D and ye3 HMDB/SSv2 candidates remain rejected for good
  reasons: xUe confuses the training dataset with held-out evaluation, while ye3
  is covered by full-text evaluation evidence.
- The next required evidence is a **fresh MiMo full20** with the P31.6 prompt and
  discovery-input changes.  P32 entry still requires
  `critique_payload_verified_cluster_count >= 3`, protection PASS, and manual A/B
  quality with no external-baseline/retrieval/context false positives.

Fresh-run attempt:

```text
run = mimo_v25_negqty_recoverycap_guard3_qhyg_targetneg_freeformrevneg_reviewissuebundle_hardneg20_mt7_b4w2_api4_r8t600_tok1536_20260703_011822
status = stopped
jsonl_lines = 0
reason = MiMo API returned 402 insufficient_balance before any paper completed
```

Do not use this run as a full20/partial result.  The next fresh validation still
requires a usable MiMo account balance/key, then rerun the same P31.6 command and
generate dashboard, review issue case table, recovery table, and manual audit.

Follow-up runtime reliability fix:

- `ApiReviewGenerator` now fast-fails non-retryable API errors such as
  `402 insufficient_balance`, quota/billing errors, invalid API keys, and
  authentication/permission failures instead of waiting through every retry.
- This does not change model behavior or verifier semantics; it only prevents
  failed full20 launches from spending minutes on guaranteed-failing retries.

Validation:

```text
tests/test_review_inference_runner.py API/P31 prompt focused set = 8 passed
py_compile review_runner + inference tests = passed
```

Hardneg20 launcher preflight:

- `run_hardneg20_guard3.sh` now runs a one-call MiMo API preflight before
  writing `.meta`, `.pid`, `.jsonl`, or starting the background full20 job.
- `DRMAS_API_PREFLIGHT=0` can disable it for manual debugging, but the default
  is on.
- The launcher now catches preflight exceptions and prints a concise failure
  line instead of a full Python traceback.
- Current validation with the active `.env` key fails fast on
  `402 insufficient_balance` in about one second and leaves existing run artifact
  counts unchanged (`before_meta=14`, `after_meta=14`).

```text
bash -n run_hardneg20_guard3.sh = passed
P31.6 launcher preflight with current MiMo key = fast-fail 402, no background launch
latest retry = 20260703_014718, no new run artifacts, traceback suppressed
latest lightweight API check = 20260703_020928, still 402 insufficient_balance, no fresh full20
latest pipeline launch check = 20260703_021333, still 402 insufficient_balance, no run artifacts
```

P31.6 artifact script status:

- Operational runbook: `P31_6_FRESH_FULL20_RUNBOOK_20260703.md`.
- `scripts/p31_6_generate_full20_artifacts.sh` is executable and validated.
- It generates the dashboard, review issue case table, and recovery case table
  from a completed full20 `.jsonl`, rejects partial/empty inputs by default via
  `--min-lines 20`, and can update `.latest_hardneg20_*` pointers with
  `--update-latest`.
- It now also generates a P31.6 entry-gate audit report by default.  Gate
  failure is non-fatal for artifact generation unless `--fail-entry-gate` is
  passed.
- `scripts/p31_6_entry_gate_audit.py` checks the machine P32-entry requirements
  from dashboard/case/recovery JSON and lists Critique-origin clusters for
  manual A/B audit.  It intentionally does not replace manual quality judgment.
- `scripts/p31_6_manual_audit.py` now provides the manual-audit half of the
  gate:
  `template` creates a fillable Critique-origin audit from an
  `ENTRY_GATE_AUDIT.json`; `validate` enforces
  `manual_A_B_clusters >= 3`, `manual_D_clusters = 0`, and
  `unfilled_clusters = 0`.
- `scripts/p31_6_generate_full20_artifacts.sh` now generates
  `<LABEL>_MANUAL_AUDIT_TEMPLATE.md/json` by default after the entry-gate
  report and `<LABEL>_READINESS_STATUS.md/json` by default after the status
  check.  Use `--skip-manual-template` / `--skip-status-report` only when those
  outputs are not wanted.
  Dry-run validated the full post-processing chain:
  dashboard -> review issue cases -> recovery cases -> entry gate -> manual
  template -> readiness status.
- Regression coverage added in `tests/test_p31_6_gate_scripts.py`:
  machine gate fails when Critique-origin clusters are below threshold, manual
  audit validation passes for three A/B clusters, and entry gate consumes a
  passing manual validation report.  Current count: 5 passed, including status
  report behavior and the guard that explicit fresh entry-gate reports do not
  accidentally reuse stale default manual-validation files.
- `scripts/p31_6_full20_pipeline.sh` wraps the standard P31.6 fresh full20
  lifecycle.  After MiMo balance is usable, run:

```bash
scripts/p31_6_full20_pipeline.sh --launch --wait --update-latest
```

  The wrapper launches with the agreed P31.6 flags, can wait for completion,
  and then calls the artifact generator so dashboard/cases/recovery/entry-gate
  and manual-template outputs are produced in one path.  Dry-run validated both
  launch and existing-run postprocess command paths.
- `scripts/p31_6_status_report.py` now emits a consolidated readiness report:
  latest run rows/running state, entry-gate status, manual-audit status,
  optional MiMo API preflight, and next recommended command.  Current report:
  `P31_6_READINESS_STATUS_20260703.md/json`.

Current readiness summary:

```text
p32_entry_ready = False
machine_gate = FAIL
manual_gate = FAIL
critique_payload_verified_cluster_count = 2
manual_A_B_clusters = 2
api_preflight = failed, 402 insufficient_balance
latest refresh = 20260703_022822
next_action = restore MiMo balance/key, then run scripts/p31_6_full20_pipeline.sh --launch --wait --update-latest
```
- Validation on `P31_5_TARGETQUALITY_FULL20_163953_UNCACHED.jsonl`:
  `bash -n` passed, dry-run passed, and real generation reproduced the current
  authoritative P31.6 metrics exactly:

```text
verified_review_issue_count = 19
verified_review_issue_cluster_recomputed_count = 16
quote_duplicate_merged_verified_review_issue_cluster_count = 16
critique_payload_verified_cluster_count = 2
verified_review_issue_cluster_origin_critique_payload_count = 2
negative_evidence_unlinked_to_flaw = 0
positive_or_neutral_negative_candidate_count = 0
negative_grounding_conflict_count = 0
mark_contested_commit_count = 5
protection = PASS
```

- The temporary `P31_6_SCRIPT_CHECK_163953_*` validation artifacts were removed
  after comparison.  The dashboard recomputation step took about 8 minutes 20
  seconds on full20, so future validations should use a long enough timeout.
- Current old-raw entry gate artifact:
  `P31_6_CRITORIGIN_RECOMPUTE_163953_ENTRY_GATE_AUDIT.md/json`.
  Machine gate fails only because Critique-origin cluster count is still 2:

```text
critique_payload_verified_cluster_count = 2 < 3
case_table_critique_origin_cluster_count = 2 < 3
protection = PASS
lexical red flags = 0
manual gate = REQUIRED
```

- Current old-raw structured manual audit artifacts:

```text
P31_6_CRITORIGIN_RECOMPUTE_163953_MANUAL_AUDIT_TEMPLATE.md/json
P31_6_CRITORIGIN_RECOMPUTE_163953_MANUAL_AUDIT.json
P31_6_CRITORIGIN_RECOMPUTE_163953_MANUAL_AUDIT_VALIDATION.md/json
P31_6_CRITORIGIN_RECOMPUTE_163953_ENTRY_GATE_WITH_MANUAL_AUDIT.md/json
```

Structured manual audit result:

```text
manual_A_clusters = 0
manual_B_clusters = 2
manual_A_B_clusters = 2
manual_D_clusters = 0
unfilled_clusters = 0
manual_status = FAIL
reason = manual_A_B_clusters = 2 < 3
```

Interpretation: the two current Critique-origin clusters are still defensible
B-level concerns, but the old raw remains below the P32 entry threshold.

- P32 remains gated on a fresh full20 with
  `critique_payload_verified_cluster_count >= 3` and manual A/B quality; the
  current old-raw recompute is still only 2 Critique-origin clusters.

## P31.6 fresh full20 with updated MiMo credentials (2026-07-03)

The local MiMo credentials in `.env` were updated and an API preflight passed
against `https://api.xiaomimimo.com/v1`.  A fresh P31.6 full20 was then run with
`api_max_workers=4`, `max_turns=7`, and `max_tokens=1536`.

Fresh run:

```text
mimo_v25_negqty_recoverycap_guard3_qhyg_targetneg_freeformrevneg_reviewissuebundle_hardneg20_mt7_b4w2_api4_r8t600_tok1536_20260703_082133.jsonl
```

Generated artifacts:

```text
P31_6_FRESH_20260703_082133_HARDNEG20_DASHBOARD.md/json/audit.json
P31_6_FRESH_20260703_082133_REVIEW_ISSUE_CASE_TABLE.md/json
P31_6_FRESH_20260703_082133_RECOVERY_CASE_TABLE.md/json
P31_6_FRESH_20260703_082133_ENTRY_GATE_AUDIT.md/json
P31_6_FRESH_20260703_082133_MANUAL_AUDIT_TEMPLATE.md/json
P31_6_FRESH_20260703_082133_READINESS_STATUS.md/json
```

Fresh metrics:

```text
full20 completed = 20/20
protection = PASS
evidence_json_valid_turns = 78
evidence_json_fallback_turns = 0
evidence_json_fallback_rate_pct = 0
verified_review_issue_count = 14
verified_review_issue_cluster_count = 12
quote_duplicate_merged_verified_review_issue_cluster_count = 12
obligation_grounded_review_issue_count = 14
review_negative_verified_count = 0
reviewer_candidate_review_issue_count = 13
reviewer_candidate_review_issue_critique_payload_count = 1
reviewer_candidate_review_issue_deterministic_seed_count = 12
critique_payload_verified_cluster_count = 1
verified_review_issue_cluster_origin_critique_payload_count = 1
verified_review_issue_cluster_origin_deterministic_seed_count = 10
verified_review_issue_cluster_origin_claim_obligation_fallback_count = 1
mark_contested_commit_count = 4
verified_review_issue_repair = 3
negative_evidence_unlinked_to_flaw = 0
positive_or_neutral_negative_candidate_count = 0
negative_grounding_conflict_count = 0
```

Entry gate:

```text
machine_gate = FAIL
manual_gate = REQUIRED
critique_payload_verified_cluster_count = 1 < 3
case_table_critique_origin_cluster_count = 1 < 3
```

Interpretation:

- This fresh full20 is operationally clean: no JSON fallback, no protection
  violations, no verified negative linkage conflict.
- It is not P32-ready because Critique-origin discovery remains too weak.  The
  fresh run regressed below the old-raw/current-code recompute, which had 2
  Critique-origin clusters.
- The only fresh Critique-origin cluster listed for manual audit is
  `GE6iywJtsV / reproducibility_gap / implementation_reproducibility_details`.
- Verified issue quantity is still mostly deterministic-seed driven, especially
  missing-ablation clusters.  Do not describe this as autonomous Critique
  discovery success.

Next work before P32:

```text
Audit Critique payload uptake in fresh execution: selected-menu construction,
why only one critique_payload bundle verifies, candidate-menu failed cases,
and whether deterministic seed top-up is hiding low Critique recall.  Keep the
bundle verifier strict; do not relax author-limitation, retrieval-gap,
target-quality, or counterevidence gates.
```

Follow-up audit after the fresh P31.6 failure:

```text
YXn76HMetm: Claim Agent produced claim-paper-context fallback claims after an
empty/malformed claim extraction.  Manager never set review_issue_discovery_required,
so no review issue menu or reviewer_negative_candidates were produced.  The old
YXn Critique-origin B cluster disappeared because real-claim extraction/discovery
did not fire, not because the verifier rejected it.

KOUAayk5Kx: Critique produced an OGL missing-ablation candidate.  Code now
recognizes "ablation on orthogonality constraint" / generalized regularization
targets as concrete missing-ablation targets and gives paper-specific mechanism
overlap (e.g. OGL in claim + candidate) a candidate relevance basis.  Uncached
recompute shows the candidate then fails correctly at observed_inventory_missing:
the only supplied anchor is a qualitative Figure 3 cell diagram, not an
ablation/variant/removal/list/table inventory anchor.  Do not force it through.

GE6iywJtsV: two menu ids were selected; only the reproducibility menu item
verified.  The protocol item remains not_verified_by_bundle.

Prompt hygiene: fresh Critique sometimes selected rim-evidence ids as if they
were review-issue menu ids.  The prompt and runtime selector rules now state
that selected_menu_items must copy review-issue candidate menu ids, normally
rim-c*, and must never use rim-evidence ids, quote ids, evidence ids, claim ids,
or invented ids.
```

Validation after this follow-up:

```text
tests/test_review_decision_hygiene.py focused P31.6/OGL tests = 5 passed
tests/test_review_inference_runner.py focused prompt/menu tests = 3 passed
P31_6_ORTHOFIX_UNCACHED_082133 and P31_6_MECHREL_UNCACHED_082133 still fail
the P31.6 machine gate with critique_payload_verified_cluster_count = 1.
```

## P31.7 audit-fix + Critique selector simplification (2026-07-03)

P31.7 was implemented as a quality closure rather than a quantity push.  The
authoritative plan file is now
`P31_7_CRITIQUE_AUTONOMOUS_DISCOVERY_PLAN_ZH_20260703.md`; the older long-term
plan file `P31_P34_REVIEWSTATE_LONG_TERM_PLAN_ZH_20260702.md` was removed.

Code changes:

```text
scripts/dashboard_run_comparison_v1.py
- current-code dashboard recompute now rebuilds decision_hygiene instead of
  trusting stale cached run hygiene.
- displayed verified_review_issue_cluster_count now matches current verifier /
  case table cluster count.
- added candidate_menu_item_any_origin_verified_count so seed-carried menu ids
  can be audited without counting as Critique-selected success.

scripts/audit_review_issue_case_table_v1.py
- case table uses current verifier checks for both obligation-grounded issues
  and direct quote negatives; stale cached issue ids only act as a stale filter.

scripts/p31_6_manual_audit.py
- manual audit template can be generated from case table clusters, not just
  Critique-origin gate entries.
- validation now requires per-cluster manual_label, raw_paper_evidence_checked,
  counterevidence_checked, paper_facing_usable, and downgrade_reason/decision.
- manual A/B gate is origin-aware: critique_origin_manual_A_B_clusters is used
  for P32 readiness.

scripts/p31_6_entry_gate_audit.py
- checks case/dashboard cluster consistency, origin-count sum, selected-menu
  verified count, and manual Critique-origin A/B counts.

agent_system/environments/env_package/review/state.py
- selector menu expanded to slot-balanced 10-12 items with per-claim/per-type
  caps.
- high-risk guards reject theory/resource and theory/robustness overreach,
  generic graph held-out coverage when graph benchmark coverage exists,
  malformed missing-ablation targets, and generic LoRA/transformer/network
  targets unless contribution-bound.
- Critique-visible state slice now exposes short menu failure lessons and
  selected_menu_items as the primary channel.
- candidate_menu_item_verified_count now counts only Critique payload/menu
  selected verified ids; deterministic/runner seeds with menu ids are only
  counted in candidate_menu_item_any_origin_verified_count.

agent_system/inference/review_runner.py
- selected-menu recovery happens before deterministic seed top-up.
- DRMAS_CRITIQUE_ONLY_DISCOVERY_EVAL isolates Critique-origin metrics from seed
  top-up.
- seed_topup_after_critique_failure_count and selected-menu traces are carried
  into dashboard metrics.

agent_system/review_manager_policy.py + agent_system/review_prompts.py
- Review issue discovery focus was changed from "fill review_issue_candidates"
  to "select 1-3 copied candidate_menu_id values"; full candidates are only a
  free-form fallback when no menu item fits.
```

Regression validation:

```text
py_compile state/runner/policy/prompts/dashboard/case/gate/manual/status = pass
focused P31.7 tests = 18 passed
```

Offline recompute over the prior P31.6 fresh raw:

```text
raw = 20260703_212637 full20
artifacts = P31_7_AUDITFIX_RECOMPUTE_212637_*
verified_review_issue_count = 20
verified_review_issue_cluster_count = 13
duplicate_review_issue_row_count = 7
critique_payload_verified_cluster_count = 0
candidate_menu_item_verified_count = 0
review_issue_candidate_critique_payload_count = 10
review_issue_candidate_deterministic_seed_count = 68
mark_contested_commit_count = 8
protection = PASS
cluster_count_consistency = PASS
machine_gate = FAIL
```

Fresh full20 with the final P31.7 selector prompt:

```text
raw = mimo_v25_negqty_recoverycap_guard3_qhyg_targetneg_freeformrevneg_reviewissuebundle_hardneg20_mt7_b4w2_api4_r8t600_tok1536_20260703_231747.jsonl
artifacts = P31_6_FRESH_20260703_231747_*
full20 completed = 20/20
api_success = 271
api_errors = 0
verified_review_issue_count = 16
verified_review_issue_cluster_count = 11
duplicate_review_issue_row_count = 5
critique_payload_verified_cluster_count = 0
candidate_menu_item_verified_count = 0
candidate_menu_item_any_origin_verified_count = 0
review_issue_candidate_critique_payload_count = 3
review_issue_candidate_deterministic_seed_count = 56
seed_topup_after_critique_failure_count = 7
mark_contested_commit_count = 9
negative_evidence_unlinked_to_flaw = 0
positive_or_neutral_negative_candidate_count = 0
negative_grounding_conflict_count = 0
protection = PASS
cluster_count_consistency = PASS
machine_gate = FAIL
manual_gate = REQUIRED
```

Interpretation:

- P31.7A succeeded: audit artifacts are cluster-level, stale hygiene inflation
  is removed, case/dashboard cluster counts match, and protection lines remain
  clean.
- P31.7B did not meet the autonomous Critique discovery target.  The simplified
  selector prompt made MiMo more conservative: total verified clusters dropped
  to 11 and Critique-origin verified clusters stayed at 0.
- P32 remains blocked.  Do not claim autonomous Critique discovery.  Current
  stable capability is strict verifier + deterministic/entity seed coverage +
  non-destructive recovery, not Critique autonomous issue discovery.

Next technical direction:

```text
Do not loosen verifier gates.  The next pass should improve candidate-menu
salience and selection supervision: fewer but higher-salience menu items,
paper-facing rationale per menu item, stronger examples of copied menu ids,
and a Critique-only small eval before another full20.
```

### P31.8 Critique selection closed-loop patch

P31.8 keeps the P31.7 conclusion: P32 remains blocked because autonomous
Critique discovery has not produced verified clusters.  This pass changes the
selector/runner interface without relaxing any verifier gate.

Code changes:

```text
agent_system/environments/env_package/review/state.py
- _select_review_issue_candidate_menu_items no longer forces slot diversity
  before rank.  The visible menu now prioritizes candidates most likely to
  survive strict bundle verification.
- review_issue_candidate_selector_menu default budget is reduced to 6 items
  with max 2 per issue type.
- efficiency_cost_gap menu items are hidden when the inventory anchor already
  reports runtime / latency / memory / FLOP / hardware/resource evidence.
- selected menu candidates may carry a normalized
  review_issue_candidate_menu_item snapshot.  If current menu lookup no longer
  renders the id, the verifier can recover the same-id/same-claim/same-type
  snapshot and still run the original strict claim/inventory/counterevidence
  checks.

agent_system/inference/review_runner.py
- selected_menu_items expanded by the runner now include the prompt-time menu
  item snapshot.
- selector lookup uses the same 6-item / max-2-per-type visible budget.

agent_system/review_manager_policy.py
- pending_absence_audit / pending_issue_bundle_verification reviewer candidates
  now count as pending, so discovery does not repeat over already selected
  absence/bundle candidates.
- Added DRMAS_CRITIQUE_DISCOVERY_FIRST, automatically enabled by
  DRMAS_CRITIQUE_ONLY_DISCOVERY_EVAL=1.  It attempts to schedule one Critique
  selector discovery pass before negative-evidence formation or recovery when
  claims/evidence exist and no recent reviewer discovery has happened.
- Recovery/conflict/sticky/support overrides now avoid overwriting an already
  scheduled review_issue_discovery_required turn.

agent_system/review_prompts.py + runner routing text
- Critique selection instruction changed from selecting 1-3 items to selecting
  1-2 safe menu items.

tests/test_review_decision_hygiene.py
- Added P31.8 regressions for verifier-survival menu ranking, already-covered
  efficiency/resource menu suppression, and selected-menu snapshot recovery.

P31_8_CRITIQUE_SELECTION_CLOSED_LOOP_PLAN_ZH_20260703.md
- Added as the authoritative P31.8 plan.
```

Validation:

```text
py_compile:
  state.py / review_runner.py / review_prompts.py / review_manager_policy.py
  tests/test_review_decision_hygiene.py
  PASS

lightweight smoke assertions:
  selector prioritizes high-quality missing_ablation over low-survival slot coverage
  efficiency/resource menu item is hidden when inventory already reports resource measures
  selected-menu snapshot survives current menu lookup miss and verifies through strict bundle path
  PASS

pytest:
  not runnable in the current system Python or bundled Python because pytest is
  not installed; no dependency installation was performed.
```

Next step:

```text
Run a small Critique-only eval with DRMAS_CRITIQUE_ONLY_DISCOVERY_EVAL=1 before
any fresh full20.  If Critique-only verified clusters remain 0, continue fixing
menu construction/salience rather than loosening verifier or entering P32.
```

P31.8 attribution fix (20260704):

```text
Problem found after P31.8 stable-id smoke:
  Critique sometimes selected a valid selector-menu issue, but deterministic
  seed evidence verified the same issue cluster first.  Final-view evidence
  dedupe then kept only the seed-origin record, so Critique metrics stayed at
  0 even when the selected menu item matched a verified cluster.

Code fix:
  agent_system/environments/env_package/review/state.py
    - _review_issue_candidate_funnel_metrics now builds a verified cluster
      lookup and performs read-only attribution for selected-menu candidates.
    - A selected menu candidate counts as Critique-selected verified only when
      it carries the prompt-time review_issue_candidate_menu_item snapshot and
      its (claim_id, issue_type, normalized target) matches an already verified
      review-issue cluster.
    - No new evidence is created; verifier output is unchanged; stale /
      hallucinated menu ids without a snapshot still fail.
    - New metrics/details:
        candidate_menu_item_verified_by_existing_cluster_count
        critique_selected_verified_cluster_count
        critique_selected_verified_by_existing_cluster_count
        critique_selected_verified_clusters

  scripts/dashboard_run_comparison_v1.py
    - Aggregates and renders the new selected-by-existing-cluster metrics.

  scripts/audit_review_issue_case_table_v1.py
    - Always recomputes decision_hygiene with current code instead of trusting
      cached run hygiene.
    - Marks clusters with critique_selected_menu_verified when hygiene says a
      Critique selected-menu item matched that verified cluster.

  scripts/p31_6_entry_gate_audit.py
    - Treats critique_selected_menu_verified clusters as Critique-origin for
      the P31.8/P32 machine gate, without changing evidence origin.

Validation:
  py_compile state/dashboard/case-table/entry-gate/tests = PASS
  focused pytest = 5 passed
  broader tests/test_review_decision_hygiene.py remains stale in this branch
  (411 passed / 32 existing behavior-shift failures); not fixed in this pass.

Smoke recompute:
  P31_8_ATTRFIX8_20260704_132142_*
    papers = 8
    verified_review_issue_count = 7
    verified_review_issue_cluster_count = 5
    critique_payload_verified_cluster_count = 3
    candidate_menu_item_verified_count = 3
    candidate_menu_item_verified_by_existing_cluster_count = 3
    protection = PASS
    entry gate machine = PASS, manual = REQUIRED

Full20 current-code recompute from existing raw:
  input:
    mimo_v25_negqty_recoverycap_guard3_qhyg_targetneg_freeformrevneg_reviewissuebundle_hardneg20_mt7_b4w2_api4_r8t600_tok1536_20260704_115546.jsonl
  outputs:
    P31_8_ATTRFIX_FULL20_20260704_115546_HARDNEG20_DASHBOARD.md/json
    P31_8_ATTRFIX_FULL20_20260704_115546_REVIEW_ISSUE_CASE_TABLE.md/json
    P31_8_ATTRFIX_FULL20_20260704_115546_RECOVERY_CASE_TABLE.md/json
    P31_8_ATTRFIX_FULL20_20260704_115546_ENTRY_GATE_AUDIT.md/json
    P31_8_ATTRFIX_FULL20_20260704_115546_MANUAL_AUDIT_TEMPLATE.md/json
  metrics:
    verified_review_issue_count = 22
    verified_review_issue_cluster_count = 15
    reviewer_candidate_review_issue_cluster_count = 13
    critique_payload_verified_cluster_count = 7
    critique_selected_verified_cluster_count = 7
    candidate_menu_item_verified_count = 8
    candidate_menu_item_verified_by_existing_cluster_count = 7
    mark_contested_commit_count = 9
    negative_evidence_unlinked_to_flaw = 0
    positive_or_neutral_negative_candidate_count = 0
    negative_grounding_conflict_count = 0
    protection = PASS
    entry gate machine = PASS, manual = REQUIRED

Interpretation:
  P31.8 machine-side Critique autonomous discovery is now no longer 0 on the
  existing full20 raw.  This is attribution/measurement repair, not verifier
  relaxation.  P32 remains blocked until the generated manual audit template is
  filled and validates with enough A/B Critique-origin clusters.

Manual audit draft:
  files:
    P31_8_ATTRFIX_FULL20_20260704_115546_MANUAL_AUDIT_FILLED_DRAFT.json
    P31_8_ATTRFIX_FULL20_20260704_115546_MANUAL_AUDIT_VALIDATION_STRICT.md/json
    P31_8_ATTRFIX_FULL20_20260704_115546_MANUAL_AUDIT_VALIDATION_ALLOW_D.md/json
    P31_8_ATTRFIX_FULL20_20260704_115546_ENTRY_GATE_WITH_MANUAL_STRICT.md/json
  labels:
    A = 3
      NnExMNiTHw acceptance_prediction_head
      WpXq5n8yLb recurrent_draft_model
      mHv6wcBb0z generalized_noise_regularization
    B = 3
      GE6iywJtsV graph_control_module
      a6SntIisgg global_encoder
      fGXyvmWpw6 efficiency_resource_measurement
    D = 1
      TPAj63ax4Y zero-shot_choice_mechanism_module
  strict validation:
    manual_A_B_clusters = 6
    critique_origin_manual_A_B_clusters = 6
    manual_D_clusters = 1
    unfilled_clusters = 0
    status = FAIL because manual_D_clusters = 1
  allow-D validation:
    status = PASS, but only if the D cluster is excluded from paper-facing
    tables/claims.
  interpretation:
    Quantity target is now plausible (6 A/B Critique-origin clusters in this
    draft), but P32 should remain blocked until the zero-shot-choice D cluster
    is removed by guard/counterevidence logic or explicitly filtered from the
    paper-facing main table.

P31.8 guard follow-up (20260704):

```text
Problem:
  Manual audit marked TPAj63ax4Y / zero-shot_choice_mechanism_module as D.
  The paper explicitly says it performs ablations over this stage's zero-shot
  instance choice pipeline, but the missing_ablation counterevidence resolver
  did not catch the stage-level phrasing.

Code fix:
  agent_system/environments/env_package/review/state.py
    - _ablation_counterevidence_window_resolves_semantic_table now treats
      "ablations over this stage / zero-shot instance choice pipeline" as
      counterevidence for selected-stage / zero-shot-choice missing_ablation
      targets.
  tests/test_review_decision_hygiene.py
    - Added regression for zero-shot choice stage ablation counterevidence.

Validation:
  focused pytest + gate script tests = 10 passed
  py_compile = PASS

Current authoritative current-code full20 recompute:
  P31_8_ATTRFIX_GUARD_FULL20_20260704_115546_*
  verified_review_issue_count = 22
  verified_review_issue_cluster_count = 14
  critique_payload_verified_cluster_count = 6
  candidate_menu_item_verified_count = 7
  case_table_critique_origin_cluster_count = 6
  protection = PASS
  machine gate = PASS

Manual audit after guard:
  P31_8_ATTRFIX_GUARD_FULL20_20260704_115546_MANUAL_AUDIT_FILLED_DRAFT.json
  manual_A_clusters = 3
  manual_B_clusters = 3
  manual_A_B_clusters = 6
  manual_D_clusters = 0
  unfilled_clusters = 0
  manual validation = PASS
  P31_8_ATTRFIX_GUARD_FULL20_20260704_115546_ENTRY_GATE_WITH_MANUAL_AUDIT.md/json = PASS

Interpretation:
  P31.8 is now a P32-entry candidate on the existing full20 raw: strict
  verifier/protection passed, Critique-selected cluster attribution is nonzero,
  and the manual audit draft has 6 A/B Critique-origin clusters with D=0.
  Remaining caution: this is a current-code recompute over an existing raw run,
  not a new API full20 generated after the guard.
```
```

Critique-only smoke results:

```text
P31_8_CRITONLY1_20260704_000010:
  rows = 1
  verified_review_issue_count = 2
  verified_review_issue_cluster_count = 2
  critique_payload_verified_cluster_count = 0
  candidate_menu_item_verified_count = 0
  candidate_menu_item_count = 0
  protection counters = 0
  finding: review_issue_discovery_required was present only after a recovery
  override; selector menu was absent, so Critique had nothing valid to select.

P31_8_CRITONLY1_20260704_000542:
  rows = 1
  verified_review_issue_count = 2
  verified_review_issue_cluster_count = 1
  critique_payload_verified_cluster_count = 0
  candidate_menu_item_verified_count = 0
  candidate_menu_item_count = 0
  protection counters = 0
  finding: review_issue_discovery_required did not fire at all; negative
  evidence formation / recovery routing consumed the opportunity.

P31_8_CRITONLY1_20260704_001006:
  rows = 1
  verified_review_issue_count = 2
  verified_review_issue_cluster_count = 2
  critique_payload_verified_cluster_count = 0
  candidate_menu_item_verified_count = 0
  candidate_menu_item_count = 0
  protection counters = 0
  finding: discovery-first made Critique run earlier, but early
  negative_evidence_binding_retry / conflict recovery still prevented a normal
  selector-discovery lifecycle on this sample.
```

Updated diagnosis:

```text
P31.8 menu quality/snapshot fixes are valid but insufficient.  The remaining
blocker is architectural scheduling: Critique autonomous discovery is still an
opportunistic branch inside hard-negative/recovery routing, so it can be
preempted before a selector menu exists or before the selector turn is cleanly
executed.  Next pass should introduce an explicit review_issue_discovery phase
or turn reservation, not another verifier or prompt relaxation.
```

## 2026-07-05 P31.11 direct Critique selector bridge checkpoint

Implemented a functional bridge from Critique selector menu choices to verified
review issue candidates without relaxing verifier gates:

- Runner expands selected `candidate_menu_id` values into real
  `reviewer_negative_candidates`.
- Selected menu candidates now preserve the copied menu snapshot claim id, so a
  candidate selected from `claim-3` is not rebound to a different claim and
  dropped before bundle verification.
- The selector prioritizes high-quality verifier-survivable menu items before
  using slot diversity to fill remaining menu capacity.
- Seed top-up remains separate from direct Critique attribution.
- Positive/neutral negative-looking records are counted as rejected diagnostics;
  active `positive_or_neutral_negative_candidate_count` stays limited to linked
  active false-negative candidates.
- `state_contamination_count` now means hard contamination only; weak target
  lifecycle records remain visible under warning/legacy counters.
- The review-negative positive-context guard was narrowed so true
  baseline-beats-proposed negative results survive, while explicit
  lower-is-better metric improvements still reject as positive/neutral support.

Fresh hardneg20 raw:

```text
mimo_v25_negqty_recoverycap_guard3_qhyg_targetneg_freeformrevneg_reviewissuebundle_hardneg20_mt7_b4w2_api4_r8t600_tok2048_20260705_030000.jsonl
```

Current metrics:

```text
protection_passed = True
verified_review_issue_count = 21
verified_review_issue_cluster_count = 18
review_negative_verified_count = 1
critique_payload_verified_cluster_count = 2
critique_direct_verified_cluster_count = 2
candidate_menu_item_verified_count = 2
positive_or_neutral_negative_candidate_count = 0
positive_or_neutral_negative_rejected_count = 1
state_contamination_count = 0
state_contamination_count_legacy = 15
state_hygiene_warning_count = 15
mark_contested_commit_count = 11
```

Validation:

```text
focused hygiene/gate selector suite = 11 passed
runner selected-menu/discovery suite = 18 passed
py_compile = PASS
broader 3-file suite = 765 passed / 31 failed
```

Sample smoke after the selector fix:

```text
run = p31_11_sample3_direct_bridge_20260705_114014.jsonl
rows = 3
verified_review_issue_count = 1
verified_review_issue_cluster_count = 1
candidate_menu_item_count = 5
candidate_menu_item_used_count = 5
candidate_menu_item_verified_count = 0
critique_direct_verified_cluster_count = 0
state_contamination_count = 0
```

The sample confirms the live API path can render and materialize selected-menu
candidates.  It did not produce a verified Critique menu candidate on these
three papers: failures were `missing_entity_already_observed_in_inventory`,
`generic_item`, and `selected_menu_item_not_in_current_menu_or_filtered`.
Conclusion: continue improving selector/menu supply quality and diagnostics;
do not loosen the verifier.

Entry gate still fails for the real remaining functional gap:

```text
critique_direct_verified_cluster_count 2 < 3
case_table_critique_origin_cluster_count 2 < 3
```

Next direction: keep verifier strict, audit remaining review-issue bundle
boundary failures only where they affect selector supply, then run a fresh
hardneg20 to see whether direct Critique verified clusters reach >=3.

P31.12 selected-menu failure telemetry audit (20260705):

- Tried to start the required `DRMAS_JSON_RESPONSE_FORMAT=on` live sample A/B
  first, but MiMo returned `401 authentication failure`; no valid sample rows
  were produced.  Existing dashboards still show `evidence_json_fallback_rate_pct=0`,
  but a fresh on/off A/B remains blocked until the API key is valid.
- Fixed selected-menu failure attribution in
  `agent_system/environments/env_package/review/state.py`:
  - A selected menu candidate with a valid copied
    `review_issue_candidate_menu_item` snapshot no longer gets mislabeled as
    `selected_menu_item_not_in_current_menu_or_filtered` solely because the
    current recomputed menu lookup is empty.
  - Merged review-issue gaps now preserve `candidate_menu_ids`,
    `reviewer_negative_candidate_ids`, and menu snapshots so bundle failure
    telemetry can be assigned to every selected menu item merged into the gap.
- Added regression:
  `test_selected_menu_candidate_with_snapshot_without_bundle_detail_is_not_filtered`.
- Recomputed sample3 artifacts:
  `P31_12_SAMPLE3_MENU_FAILURE_RECOMPUTE_20260705_120426_*`.
- Final sample3 menu-failure distribution:

```text
candidate_menu_item_failed_selected_menu_item_not_in_current_menu_or_filtered = 0
candidate_menu_item_failed_by_reason =
  missing_entity_already_observed_in_inventory: 2
  generic_item: 1
  full_text_evaluation_or_scope_counterevidence: 1
  not_verified_by_bundle: 1
```

- Validation:

```text
focused hygiene/gate selector suite = 12 passed
runner selected-menu/discovery suite = 18 passed
py_compile state.py and tests/test_review_decision_hygiene.py = PASS
broader 3-file suite = 767 passed / 30 failed
```

Conclusion: the sample3 blocker is no longer a stale-menu diagnostic problem.
It is a real menu supply / selector quality problem.  Next work should use the
failure mix above to improve concrete verifier-survivable menu targets after
the JSON response-format A/B is rerun with a valid MiMo key.

P31.12 JSON response-format A/B follow-up (20260705):

- Checked the MiMo credentials path.  The `.env` `MIMO_API_KEY` is valid; the
  earlier 401 happened because the failing command did not source `.env` and
  runner fell through to the shell `OPENAI_API_KEY`.
- `DRMAS_JSON_RESPONSE_FORMAT=on` sample3 completed successfully:

```text
run = p31_12_jsonfmt_on_sample3_20260705_121250
rows = 3
evidence_json_valid_turns = 10
evidence_json_fallback_turns = 0
evidence_json_fallback_rate_pct = 0
evidence_json_no_json_object_turns = 0
state_contamination_count = 0
positive_or_neutral_negative_candidate_count = 0
```

- Generated artifacts:
  `P31_12_JSONFMT_ON_SAMPLE3_20260705_121250_*`.
- `DRMAS_JSON_RESPONSE_FORMAT=off` sample3 did not complete: MiMo returned
  `402 insufficient account balance` after several successful API calls, and
  `p31_12_jsonfmt_off_sample3_20260705_121616.jsonl` has 0 rows.
- Current conclusion: response-format `on` is freshly smoke-validated on 3
  papers with fallback rate 0, but the requested live on/off A/B is incomplete
  until account balance is restored.

P31.12 JSON response-format A/B completed after balance top-up (20260705):

```text
on run  = p31_12_jsonfmt_on_sample3_20260705_121250
off run = p31_12_jsonfmt_off_sample3_20260705_123405

on:
  rows = 3
  evidence_json_valid_turns = 10
  evidence_json_fallback_turns = 0
  evidence_json_fallback_rate_pct = 0
  evidence_json_no_json_object_turns = 0
  api_success_calls = 41
  raw_chars_avg = 2503
  raw_chars_max = 5989

off:
  rows = 3
  evidence_json_valid_turns = 2
  evidence_json_fallback_turns = 10
  evidence_json_fallback_rate_pct = 83
  evidence_json_no_json_object_turns = 0
  api_success_calls = 44
  raw_chars_avg = 5733
  raw_chars_max = 9809
```

Conclusion: P0 is validated.  MiMo needs `response_format=json_object`
(`DRMAS_JSON_RESPONSE_FORMAT=on` or default `auto`) for this pipeline; turning
it off immediately restores the high fallback regime.  Continue downstream
Critique selector/menu supply work only under the response-format-on/auto path.

P31.13 menu-quality supply guard update (20260705):

- Fresh response-format-on hardneg20 completed:

```text
raw = mimo_v25_negqty_recoverycap_guard3_qhyg_targetneg_freeformrevneg_reviewissuebundle_hardneg20_mt7_b4w2_api4_r8t600_tok2048_20260705_130323.jsonl
artifacts = P31_6_FRESH_20260705_130323_*
rows = 20
evidence_json_valid_turns = 73
evidence_json_fallback_turns = 0
evidence_json_fallback_rate_pct = 0
protection = PASS
state_contamination_count = 0
verified_review_issue_count = 16
verified_review_issue_cluster_count = 13
critique_direct_verified_cluster_count = 0
critique_selected_existing_seed_cluster_count = 2
candidate_menu_item_count = 16
candidate_menu_item_used_count = 16
candidate_menu_item_verified_count = 2
```

- Entry gate still failed for the real functional gap:

```text
critique_direct_verified_cluster_count = 0 < 3
case_table_critique_origin_cluster_count = 2 < 3
```

- Failure audit showed the selected menu was dominated by verifier-hostile
  template targets such as `quantitative result table or metric for RNN/OGL/EER`,
  `metric result table for the claimed effect`, and `held-out benchmark or
  stress setting for NR-DCCA`.
- Implemented supply-side guards only:
  - reject generic scope/result menu templates in
    `_review_issue_candidate_menu_quality_failure`;
  - stop `_review_issue_entity_obligation_candidates` from casting primary
    method entities as missing scope/result obligations;
  - stop `_seed_items_from_review_issue_blueprint` from fabricating generic
    primary-entity scope/result fallbacks;
  - reject bare temporal descriptors such as `long-term` as missing-ablation
    components while keeping named modules/components eligible.
- Offline recompute over the same raw:

```text
artifacts = P31_13_MENU_QUALITY_RECOMPUTE_20260705_130323_*
verified_review_issue_count = 15
verified_review_issue_cluster_count = 12
critique_direct_verified_cluster_count = 0
critique_selected_existing_seed_cluster_count = 2
candidate_menu_item_verified_count = 2
candidate_menu_item_failed_count = 14
candidate_menu_item_failed_by_stage =
  menu_quality_guard: 8
  counterevidence: 2
  claim_anchor: 2
  bundle_verification_or_not_materialized: 1
  concrete_item_check: 1
state_contamination_count = 0
positive_or_neutral_negative_candidate_count = 0
negative_evidence_unlinked_to_flaw = 0
negative_grounding_conflict_count = 0
```

Conclusion: this pass tightened menu supply and removed one generic verified
cluster; it does not and cannot create new direct Critique discoveries from an
old raw.  The next meaningful validation is a fresh response-format-on full20
so Critique sees the new selector menu.  Do not loosen verifier/validator gates
or count selected-existing seed clusters as direct Critique discovery.

P31.13 fresh full20 and precision follow-up (20260705):

- Ran a fresh response-format-on hardneg20 from commit `7b0aafb`:

```text
raw = mimo_v25_negqty_recoverycap_guard3_qhyg_targetneg_freeformrevneg_reviewissuebundle_hardneg20_mt7_b4w2_api4_r8t600_tok2048_20260705_132812.jsonl
artifacts = P31_6_FRESH_20260705_132812_*
rows = 20
evidence_json_valid_turns = 62
evidence_json_fallback_turns = 1
evidence_json_fallback_rate_pct = 2
protection = PASS
state_contamination_count = 0
verified_review_issue_count = 17
verified_review_issue_cluster_count = 13
critique_direct_verified_cluster_count = 2
candidate_menu_item_verified_count = 2
```

- Manual audit of the two direct clusters found high false-positive risk:
  - `ye3NrNrYOY / evaluation_protocol_risk / metric_definition_threshold_selection_protocol`
    was a generic protocol target; the paper text actually defines Top-1
    accuracy and official splits.
  - `cklg91aPGk / missing_baseline / recent_gnn_graph-transformer_baselines...`
    was an external family baseline template, similar to the prior NAS
    external-list false positive.
- Added hard bundle-level target guards for reviewer/menu candidates:
  - generic evaluation-protocol templates are rejected before verified issue
    creation;
  - hardcoded external baseline-family menu templates are rejected before
    verified issue creation;
  - generic ablation templates such as `component-removal experiment for the
    claimed mechanism` are rejected before verified issue creation;
  - runner protocol fallback no longer fabricates `evaluation protocol details
    for <primary>`.
- Current-code recompute over the same fresh raw:

```text
artifacts = P31_13_MENU_QUALITY_RECOMPUTE_20260705_132812_*
verified_review_issue_count = 15
verified_review_issue_cluster_count = 11
critique_direct_verified_cluster_count = 0
critique_payload_verified_cluster_count = 0
candidate_menu_item_verified_count = 0
candidate_menu_item_failed_count = 11
candidate_menu_item_failed_by_stage =
  counterevidence: 5
  menu_quality_guard: 6
candidate_menu_item_failed_by_reason =
  missing_entity_already_observed_in_inventory: 4
  evaluation_protocol_menu_generic_target: 3
  missing_ablation_counterevidence_in_claim_or_inventory: 1
  missing_baseline_menu_external_family_target: 1
  missing_ablation_menu_generic_target: 2
state_contamination_count = 0
positive_or_neutral_negative_candidate_count = 0
negative_evidence_unlinked_to_flaw = 0
negative_grounding_conflict_count = 0
```

Conclusion: the apparent direct=2 fresh improvement was not paper-safe.  The
strict current-code result is direct=0, but that is the correct precision
position.  Next functional work should improve concrete menu supply (paper-named
baseline targets, metric-specific protocol targets, and ablation targets not
already countered), not relax verification or count external template targets.

P31.13 Stage 2 supply first pass:

- Added a menu-only paper-named baseline supply path.  Deterministic seed
  verification still requires limited-comparison wording, but selector menu
  generation may expose a paper-named related/prior method when there is a
  locatable evaluation/comparison inventory anchor and the named method is not
  already in that inventory.
- Added guards so contexts like `We compare ... with GraphFormer` do not become
  missing-baseline candidates; baseline menu inventory anchors also reject plain
  related-work citations.
- Offline selector probe over fresh raw `20260705_132812`: rows=20,
  rows_with_menu=11, menu_items=16, paper_named_baseline_menu=3
  (`GPT-4`, `Graphormer`, `EqualAL`).  Current-code artifact recompute remains
  protection PASS with direct Critique verified clusters still 0.

P31.13 Stage 2 live sample checkpoint:

- Ran a response-format-on 3-paper API sample over the three papers where the
  offline selector exposed paper-named baseline menu candidates:

```text
run = p31_13_paper_named_menu_sample3_20260705_144239
rows = 3
evidence_json_valid_turns = 10
evidence_json_fallback_turns = 0
evidence_json_fallback_rate_pct = 0
protection = PASS
state_contamination_count = 0
positive_or_neutral_negative_candidate_count = 0
negative_evidence_unlinked_to_flaw = 0
negative_grounding_conflict_count = 0
critique_direct_verified_cluster_count = 1
candidate_menu_item_count = 3
candidate_menu_item_used_count = 3
candidate_menu_item_verified_count = 1
candidate_menu_item_failed_count = 2
candidate_menu_item_failed_by_stage = counterevidence: 2
candidate_menu_item_failed_by_reason =
  missing_entity_already_observed_in_inventory: 1
  missing_ablation_counterevidence_in_claim_or_inventory: 1
```

- The verified Critique-origin cluster was
  `YXn76HMetm|missing_robustness_or_generalization|coverage_held-out_for_ripu`.
  It came from a selected menu path, but from the existing runner/obligation
  menu style, not from the new paper-named baseline supply path.
- Conclusion: the functional path is live in a small API sample, but the new
  paper-named baseline supply has not yet been proven by model selection.  The
  next major stage should improve selector attention and menu supply quality,
  then rerun a fresh hardneg20.  Do not treat this as a full20 pass and do not
  relax verifier/validator gates.

P31.15 Stage 2 selector/attribution follow-up:

- Fixed paper-named baseline menu supply for live-state failure modes:
  - claims with `baseline_or_comparison` obligations and positive result
    wording such as `best results` can now expose paper-named baseline menu
    candidates;
  - baseline comparison inventory anchors now accept result language such as
    `outperforms all baselines`, `state-of-the-art`, `SOTA`, `improves`, and
    plural `experiments/benchmarks/datasets`;
  - paper-named baseline inventory skips anchors explicitly bound to another
    claim and falls back to unbound full-paper evaluation/comparison anchors.
- Fixed selected-menu vs seed shadowing:
  - if a later Critique-selected menu candidate shares an evidence id with an
    earlier deterministic absence-audit record, the selected candidate can
    update the record while lower-priority seed records cannot overwrite it;
  - duplicate verified review-issue representatives now prefer Critique-origin
    records over deterministic seed records for the same signature.
- Validation:
  - focused hygiene/menu suite: `39 passed`
  - runner selected-menu/discovery suite: `20 passed`
  - hygiene/gate focused suite: `20 passed`
  - `py_compile` passed for `state.py`, runner, dashboard, and gate scripts.
- Live samples:
  - `p31_14_paper_named_menu_sample3_20260705_145715` showed the attribution
    bug: `EqualAL` was selected and could be verified, but stored as
    `deterministic_paper_named_baseline_seed`.  Rebuilding the view after the
    fix gives `critique_direct_verified_cluster_count=1` and
    `critique_selected_existing_seed_cluster_count=0`.
  - `p31_15_paper_named_menu_sample3_20260705_151151` protection stayed clean
    (`evidence_json_fallback_rate_pct=0`, hard contamination/positive-neutral
    active negatives/grounding conflicts all 0), but no menu items were selected
    (`candidate_menu_item_used_count=0`).  HPu had a visible paper-named GPT-4
    menu snapshot; YXn could generate current-code EqualAL/HFR menu items but
    had no runtime selector snapshot.
- Conclusion: Stage 2 supply and attribution are materially better, but direct
  Critique discovery is still not stable enough for full20.  Next functional
  direction is manager trigger / selector-attention reliability, not verifier
  relaxation and not broader statistics.

P31.16 Stage 2 manager trigger / selector-menu checkpoint:

- Manager review-issue selector availability now uses the same wider selector
  budget as the prompt path (`max_items=12`, `max_per_claim=3`,
  `max_per_type=4`) instead of the old narrow availability check.
- Hard-negative discovery no longer routes to Critique selector mode when
  review-issue bundle is enabled but no concrete selector menu item is visible;
  it falls back to Evidence targeted negative search instead.
- Runner marks empty selector snapshots and downgrades stale
  `review_issue_discovery_required` turns before building the Critique prompt,
  preventing empty-menu turns from eliciting invented `rim-c...` ids.
- Validation:
  - targeted runner/manager selector tests: `5 passed`
  - runner selector/discovery focused suite: `21 passed`
  - hygiene/gate focused suite: `21 passed`
  - `py_compile` for review_manager_policy.py, review_runner.py, and
    test_review_inference_runner.py: PASS
- Live sample:
  - run: `p31_16_trigger_menu_sample3_20260705_155155`
  - input: `p31_16_trigger_sample3_input.parquet`
  - papers: HPuLU6q7xq, QAgwFiIY4p, YXn76HMetm
  - environment: response_format=on, qhyg=1, targetneg=1, freeformrevneg=1,
    reviewissuebundle=1, max_tokens=2048
  - evidence_json_fallback_rate_pct=0, protection PASS,
    verified_review_issue_cluster_count=3,
    critique_direct_verified_cluster_count=1,
    candidate_menu_item_used_count=2,
    candidate_menu_item_verified_count=1,
    state_contamination_count=0,
    positive_or_neutral_negative_candidate_count=0,
    negative_evidence_unlinked_to_flaw=0,
    negative_grounding_conflict_count=0.
- Trace/case findings:
  - YXn76HMetm received selector snapshot count 3, Critique selected EqualAL
    (`rim-c2-mb-same-setting-comparison-against`), runner recovered it, and the
    final case table records `missing_baseline / equalal_baseline` with
    `discovery_origin=critique_payload_menu_selected`.
  - QAgwFiIY4p no longer had an empty-menu selector turn; it received snapshot
    count 1 and selected Graphormer, but bundle verification rejected it as
    `missing_baseline_target_generic_or_truncated`.
  - HPuLU6q7xq did not enter selector discovery in this stochastic sample; it
    followed negative binding / recovery routing.  Its final state can still
    generate two insufficient-evaluation runner-seed menu items.
- Conclusion: the Critique-selected-menu -> verifier -> direct Critique-origin
  case-table path is alive in a fresh API sample with clean protection metrics.
  Stage 2 is not complete.  Next work should improve paper-named baseline
  target quality (Graphormer-style rejection) and stabilize discovery trigger
  timing when menus exist but recovery/binding routes consume the turn.  Do not
  relax verifier/validator gates and do not count deterministic seed clusters
  as Critique discovery.

P31.17 Stage 2 paper-named baseline provenance checkpoint:

- Fixed the QAgwFiIY4p/Graphormer selected-menu failure mode without relaxing
  generic baseline guards:
  - paper-named baseline menu items now carry
    `paper_named_baseline_name`, expectation quote, locator, and grounding
    label through compact selector snapshots and normalized selected-menu
    candidates;
  - missing-baseline target specificity accepts single-word paper-named method
    targets such as `Graphormer` only when bundle/menu provenance proves the
    exact method name from a grounded paper context;
  - spurious ordinary words such as `Labor` and external graph-family template
    targets remain rejected.
- Fixed the next verifier bottleneck for paper-named targets:
  - Related Work mentions of the paper-named method are no longer treated as
    current observed comparison inventory for missing-baseline bundle
    verification;
  - current comparison/result anchors such as Table/result comparison quotes
    still remain eligible observed inventory.
- Deterministic paper-named seed supply now uses the same conservative
  no-limited-cue path as selector menu supply: it still requires a grounded
  related/prior method context plus a concrete current comparison inventory
  that omits the named method.
- Validation:
  - `graphormer or paper_named`: `12 passed`
  - hygiene/gate selected-menu focused suite: `27 passed`
  - runner selected-menu/discovery focused suite: `21 passed`
  - `py_compile` for `state.py`, `test_review_decision_hygiene.py`, and
    `review_runner.py`: PASS
  - `git diff --check`: PASS
- Live sample attempt:
  - attempted run:
    `p31_17_paper_named_provenance_sample3_20260705_160710.jsonl`
  - result: not started past manager calls because MiMo returned
    `401 Authentication Fails` for the currently loaded key ending `b5zO`.
  - No fresh sample metrics can be claimed from this attempt.
- Broader validation caveat:
  - full `tests/test_review_decision_hygiene.py` currently reports
    `444 passed / 23 failed`; sampled failures include old metric-key/schema
    assertions and unrelated review-issue behaviors.  The P31.17 claim is
    limited to the focused suites above, not full-file green.
- Next:
  - rerun the 3-paper sample after the active MiMo key is corrected;
  - if Graphormer/EqualAL-style selected-menu candidates verify cleanly with
    protection still passing, proceed to a fresh hardneg20;
  - keep direct Critique-origin counts separate from deterministic seeds.

P31.24 Stage 2 selected-menu recovery checkpoint (20260705):

- Fixed a real selected-menu materialization gap:
  - Critique `selected_menu_items` are now recovered whenever the copied
    `candidate_menu_id` resolves against the current selector menu, even if the
    turn was routed through the older freeform selector flag and did not retain
    `review_issue_discovery_required` in the logged manager payload.
  - Seed top-up still requires the formal review-issue discovery turn; the
    relaxed condition is only for recovering copied selected menu ids.
  - Selected-menu candidate rationale now prefers the menu item's structured
    `why_review_worthy` and strips `...[truncated]`, so model selection
    rationales or prompt-compaction artifacts cannot make normalizer treat a
    menu candidate as a retrieval/context gap.
- Runner selector supply also accepts component-ablation seed targets when
  `ReviewState` exposes concrete component anchors; this is supply only and
  still flows through strict bundle verification.
- Validation:
  - `py_compile review_runner.py tests/test_review_inference_runner.py = PASS`
  - runner selector/menu focused suite = 14 passed
  - hygiene/gate focused suite = 24 passed
  - offline replay of P31.23 WNxl selected-menu payload now appends a
    `critique_payload_menu_selected` candidate with preserved `candidate_menu_id`.
- Live sample:
  - run = `p31_24_selected_menu_recovery_sample3_20260705_171944`
  - rows = 3, sample papers = ye3NrNrYOY, WNxlJJIEVj, uOrfve3prk
  - protection = PASS
  - evidence_json_fallback_rate_pct = 0
  - state_contamination_count = 0
  - candidate_menu_item_count = 3
  - candidate_menu_item_used_count = 3
  - candidate_menu_item_verified_count = 0
  - candidate_menu_item_failed_count = 3
  - failure reasons:
    `missing_entity_already_observed_in_inventory` = 2,
    `observed_inventory_missing` = 1.
- Interpretation: the functional path now reaches the strict verifier in a
  fresh API sample; verifier rejection is real and should not be bypassed.
  Stage 2 remains incomplete because this sample produced no verified direct
  Critique clusters.  Next work should improve selector supply/ranking so
  visible menu items are concrete verifier-survivable issues, not already
  covered inventory checks.

P31.25/P31.26 Stage 2 selector supply and menu-id fidelity checkpoint (20260705):

- Implemented supply-quality filters for the concrete P31.24 verifier failures:
  - runner/entity-generated `quantitative result for ...` placeholder targets
    are filtered before entering the selector menu;
  - entity-generated `quantitative result table for ...` placeholders are
    filtered without changing posthoc attribution of historical
    Critique-selected snapshots;
  - `metric reporting protocol or comparability setting` is treated as a
    generic protocol menu target.
- Ran fresh sample:
  - run = `p31_25_supply_filter_sample3_20260705_180321`
  - sample papers = HPuLU6q7xq, QAgwFiIY4p, YXn76HMetm
  - protection = PASS
  - evidence_json_fallback_rate_pct = 0
  - state_contamination_count = 0
  - verified_review_issue_cluster_count = 4
  - critique_payload_verified_cluster_count = 2
  - critique_direct_verified_cluster_count = 2
  - candidate_menu_item_count = 2
  - candidate_menu_item_used_count = 2
  - candidate_menu_item_verified_count = 2
  - candidate_menu_item_failed_count = 0
  - entry gate still failed only on direct Critique clusters 2/3 and case-table
    Critique-origin clusters 2/3.
- Audit finding from P31.25:
  - YXn exposed a `candidate_menu_id` collision: long same-prefix
    paper-named targets such as `EqualAL` and `PixelPick` collapsed to
    `rim-c2-mb-same-setting-comparison-against`, allowing a selected menu id
    to bind to a different target during lookup.
  - Fixed by disambiguating menu ids during ReviewState menu generation and
    runner seed-menu expansion.
- Validation after the collision fix:
  - runner selector/menu focused suite = 16 passed
  - hygiene/gate focused suite = 28 passed
  - paper-named/id-collision focused tests = 13 passed
  - runner id-collision focused tests = 4 passed
  - `py_compile` = PASS
  - `git diff --check` = PASS
- Interpretation: selected-menu quality improved, but Stage 2 is not complete.
  The next sample must be rerun after the id-collision fix before claiming
  direct Critique cluster improvement or moving to hardneg20.

P31.29/P31.30 bridge-guard sample checkpoint (20260705):

- P31.29 exposed a real scheduler regression from the newly added
  support-recheck bridge:
  - run = `p31_29_stage3_support_bridge_critique5_20260705_191746`
  - machine gate = FAIL
  - `critique_direct_verified_cluster_count = 1`
  - `candidate_menu_item_count = 1`
  - `candidate_menu_item_verified_count = 1`
  - `mark_contested_commit_count = 3`
  - `state_contamination_count = 0`
  - `recovery_no_effect_commit = 0`
  - `recovery_harmful_commit_risk = 0`
  - diagnosis: recovery/support scheduling improved contested repair but could
    fire before Critique review-issue discovery had been attempted, leaving the
    run dominated by deterministic seed issues.
- Fix:
  - added `_review_issue_discovery_untried_for_recovery_bridge`;
  - the finalize-policy bridge and fallback-policy bridge now share this guard;
  - support recheck / mark_contested recovery waits for the Critique discovery
    attempt when targeted reviewer-negative discovery is enabled.
- Validation after code fix:
  - `pytest tests/test_review_inference_runner.py -q -k 'visible_augmented_selector_menu or selector_style_recovery_bridge_standardizes or selected_menu_recovery_does_not_require_formal_discovery_flag or review_issue_discovery_first or verified_review_issue_support_recheck or verified_review_issue_recovery_bridge_runs_inside_recovery_phase'`
    = 9 passed
  - targeted support-bridge regression subset = 4 passed
  - `py_compile agent_system/review_manager_policy.py tests/test_review_inference_runner.py`
    = PASS, with only existing invalid-escape warnings.
- P31.30 fresh 5-paper sample after the guard:
  - run = `p31_30_bridge_guard_critique5_20260705_193123`
  - rows = 5
  - machine gate = PASS
  - manual gate = PASS after critique-only manual audit validation
  - protection = PASS
  - `critique_direct_verified_cluster_count = 4`
  - `candidate_menu_item_count = 7`
  - `candidate_menu_item_used_count = 5`
  - `candidate_menu_item_verified_count = 4`
  - `candidate_menu_item_failed_count = 1`
  - `verified_review_issue_cluster_count = 5`
  - `mark_contested_commit_count = 5`
  - `verified_issue_cluster_without_recovery_count = 1`
  - `state_contamination_count = 0`
  - `positive_or_neutral_negative_candidate_count = 0`
  - `negative_evidence_unlinked_to_flaw = 0`
  - `negative_grounding_conflict_count = 0`
  - `recovery_no_effect_commit = 0`
  - `recovery_harmful_commit_risk = 0`
- Manual audit files:
  - `P31_30_BRIDGE_GUARD_CRITIQUE5_ONLY_MANUAL_AUDIT_20260705_193123.json`
  - `P31_30_BRIDGE_GUARD_CRITIQUE5_ONLY_MANUAL_AUDIT_VALIDATION_20260705_193123.json`
  - labels: GE constraint module = B; Nn acceptance prediction head = B; QAg
    Graphormer same-task baseline = B; YX PixelPick/EqualAL baseline = B.
- Interpretation:
  - The desired order is now live on the 5-paper sample:
    Critique discovery -> strict bundle verification -> verified issue ->
    support/recovery bridge -> mark_contested.
  - Do not claim hardneg20/full39 stability yet.  Next real step is fresh
    hardneg20 with the same guard, followed by manual audit of Critique-origin
    clusters.  Do not relax verifier/validator gates.

P31.6 hardneg20 precision/manual-audit checkpoint (20260705):

- Fresh hardneg20 run:
  - run =
    `mimo_v25_negqty_recoverycap_guard3_qhyg_targetneg_freeformrevneg_reviewissuebundle_hardneg20_mt7_b4w2_api4_r8t600_tok2048_20260705_205654`
  - rows = 20
  - env = `DRMAS_JSON_RESPONSE_FORMAT=on`, `max_tokens=2048`
- First manual audit of the pre-filter 15-cluster template found a real
  precision problem:
  - manual A/B clusters = 6
  - manual D clusters = 9
  - false positives included already-covered paper-named baselines, malformed
    missing-ablation fragments, evaluation-tool targets, and semantic ablation
    counterevidence that the verifier was not catching.
- Fixes added in `ReviewState` verifier hygiene:
  - reject malformed missing-ablation targets such as `ensure ...`,
    preposition fragments, `in causal representation`, and evaluation-tool
    targets such as GLIDE/target-pocket checks;
  - strengthen full-text baseline counterevidence for named baseline lists,
    table/caption rows, and high-frequency targets such as CLIP;
  - add semantic ablation counterevidence for SPOT-style pre-training/occupancy
    ablations, NR-DCCA vs DCCA comparisons, and TCMT causal-representation
    component comparisons;
  - keep the verifier strict: this filters false positives and does not relax
    verified-negative gates.
- After recomputing artifacts from the same raw run:
  - machine gate = PASS
  - manual gate = PASS
  - `P31.6 ready = True`
  - `critique_direct_verified_cluster_count = 6`
  - `candidate_menu_item_verified_count = 6`
  - `case_table_critique_origin_cluster_count = 5`
  - `manual_A_clusters = 2`
  - `manual_B_clusters = 4`
  - `manual_D_clusters = 0`
  - `critique_origin_manual_A_B_clusters = 5`
  - `state_contamination_count = 0`
  - `positive_or_neutral_negative_candidate_count = 0`
  - `negative_evidence_unlinked_to_flaw = 0`
  - `negative_grounding_conflict_count = 0`
- Manual audit files:
  - `P31_6_FRESH_20260705_205654_MANUAL_AUDIT.json`
  - `P31_6_FRESH_20260705_205654_MANUAL_AUDIT_VALIDATION.json`
  - labels: XH secure aggregator negative result = A; fGX efficiency resource
    measurement = A; HP GPT-4 baseline = B; Nn acceptance prediction head = B;
    YX EqualAL baseline = B; a6 Global Encoder = B.
- Validation:
  - new verifier precision regressions = 4 passed
  - focused hygiene/gate suite = 20 passed
  - runner selector/discovery focused suite = 25 passed
  - `py_compile` for changed modules/scripts = PASS
- Interpretation:
  - Stage 2 hardneg20 entry evidence is now credible enough to move toward P32
    review, with both machine and manual gates passing.
  - This is not permission to loosen gates or jump to full39.  Next work should
    carry the manual wording caveats into the P32 narrative, preserve the
    strict verifier behavior, and only then decide whether a broader run is
    needed for the paper story.
