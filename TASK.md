# TASK.md

## Current Task: P31 ReviewState Lifecycle / Critique Selector Integration

Authoritative roadmap: `P31_REVIEWSTATE_LIFECYCLE_ROADMAP_20260701.md`.

Goal:

- Make ReviewState-centered review issue discovery, bundle verification, clustering, manual audit, and non-destructive recovery stable enough for the paper narrative.
- Improve Critique payload integration without relaxing the verifier.
- Keep direct quote-grounded negative evidence strict; optimize obligation-grounded verified review issue bundles and safe `mark_contested` recovery.

## Current P31.28 Checkpoint 2026-07-05

Current stage:

```text
Stage 2 has post-fix small-sample runtime + manual evidence.  The SPOT / 9z
`including_loss` false positive no longer verifies, and the 5-paper
Critique-origin sample passes both the machine gate and the Critique-origin
manual gate.
```

Post-fix sample:

```text
input = p31_28_postfix_critique5_input.parquet
run = p31_28_postfix_critique5_20260705_185055
label = P31_28_POSTFIX_CRITIQUE5_20260705_185055
rows = 5
papers = 9zEBK3E9bX, GE6iywJtsV, NnExMNiTHw, QAgwFiIY4p, YXn76HMetm
machine_gate = PASS
manual_gate = PASS
evidence_json_fallback_rate_pct = 0
state_contamination_count = 0
verified_review_issue_count = 13
verified_review_issue_cluster_count = 11
critique_direct_verified_cluster_count = 4
candidate_menu_item_count = 6
candidate_menu_item_used_count = 4
candidate_menu_item_verified_count = 4
candidate_menu_item_failed_count = 0
positive_or_neutral_negative_candidate_count = 0
negative_evidence_unlinked_to_flaw = 0
negative_grounding_conflict_count = 0
mark_contested_commit_count = 3
verified_issue_cluster_without_recovery_count = 6
```

Key audit facts:

```text
including_loss_verified = False
red_flags = []
selected_menu_failures = 0
manual_critique_origin_A_B_clusters = 3
manual_D_clusters = 0
critique_origin_clusters =
  A: GE6iywJtsV / missing_ablation / graph_control_module
  B: NnExMNiTHw / missing_ablation / acceptance_prediction_head
  C: QAgwFiIY4p / missing_ablation / coordinates_without_information_loss
  B: YXn76HMetm / missing_baseline / equalal_baseline
manual_audit =
  P31_28_POSTFIX_CRITIQUE5_ONLY_MANUAL_AUDIT_20260705_185055.{json,md}
manual_validation =
  P31_28_POSTFIX_CRITIQUE5_ONLY_MANUAL_AUDIT_VALIDATION_20260705_185055.{json,md}
```

Interpretation:

```text
The false-positive guard works in a fresh API path: removing 9z/including_loss
did not collapse the Stage 2 machine gate.  Manual audit keeps the QAg
coordinates/information-loss item as C, not paper-facing evidence, but the
remaining GE/Nn/YXn Critique-origin clusters still give 3 A/B and 0 D.  Stage 2
is therefore small-sample paper-ready, not yet full hardneg20/full39-ready.

Stage 3 remains the next functional bottleneck.  In the post-fix sample,
`mark_contested_commit_count=3` but `verified_issue_cluster_without_recovery=6`.
The Stage 3 audit found two separate cases:
  - GE has open verified issues but no same-claim verified positive support, so
    it should first get a support recheck rather than a forced contested mark.
  - Nn has an eligible supported-but-contested claim, but the recovery bridge
    was blocked by `phase=recovery` and stayed on evidence recheck.
  - YXn claim-3 is already unsupported, so it is not a supported-but-contested
    target even though the manual issue is B.
```

Next step:

```text
Run a fresh 5-paper sample or hardneg20 after the Stage 3 scheduler patch.  The
expected functional change is that open verified review issues without same-claim
support get one `request_evidence_recheck`, while already supported verified
issues can enter `s4_verified_review_issue_recovery_bridge` even inside the
recovery phase.  Do not relax verifier/validator gates.
```

Implemented after manual audit:

- Added `s4_verified_review_issue_support_recheck_bridge`: open verified review
  issue bundles that lack same-claim verified positive support get one targeted
  `request_evidence_recheck` instead of a guaranteed blocked recovery patch.
- Removed the recovery-phase blocker from the verified review issue recovery
  bridge, so eligible supported-but-contested claims can still route to
  `challenge_previous_hypothesis` while `phase=recovery`.
- P31.28 probe after the patch:
  - `NnExMNiTHw` now routes to `s4_verified_review_issue_recovery_bridge`.
  - `GE6iywJtsV` routes to support recheck first.
  - `YXn76HMetm` does not route to contested because claim-3 is already
    `unsupported`.

Validation:

```text
manual audit validation = PASS
entry gate with manual validation = machine PASS / manual PASS
new support-recheck policy tests = 3 passed
neighbor selector/recovery policy tests = 5 passed
py_compile review_manager_policy.py + tests/test_review_inference_runner.py = PASS
known unrelated targeted recovery bundle tests still fail on missing issue
materialization in their fixture; do not count them as this patch's regression.
```

## Previous P31.27 Checkpoint 2026-07-05

Current stage:

```text
Stage 2 now has hardneg20 machine-gate evidence, but not final paper-ready
manual evidence.  The 20260705_182335 hardneg20 run passed the machine gate
with 5 direct Critique-selected verified clusters, while manual preaudit found
one likely false positive in SPOT / 9zEBK3E9bX: a selected missing-ablation
target `including_loss` was cut from "including loss balancing" despite the
paper text saying Table 6 is an ablation study on pre-training strategies.
```

Fresh hardneg20:

```text
run = mimo_v25_negqty_recoverycap_guard3_qhyg_targetneg_freeformrevneg_reviewissuebundle_hardneg20_mt7_b4w2_api4_r8t600_tok2048_20260705_182335
rows = 20
machine_gate = PASS
manual_gate = REQUIRED
evidence_json_fallback_rate_pct = 0
state_contamination_count = 0
state_contamination_count_legacy = 15
state_hygiene_warning_count = 15
verified_review_issue_count = 22
verified_review_issue_cluster_count = 18
critique_payload_verified_cluster_count = 5
critique_direct_verified_cluster_count = 5
critique_selected_existing_seed_cluster_count = 0
candidate_menu_item_count = 10
candidate_menu_item_used_count = 8
candidate_menu_item_verified_count = 5
candidate_menu_item_failed_count = 3
mark_contested_commit_count = 10
verified_issue_cluster_without_recovery_count = 10
```

Manual preaudit of Critique-origin clusters:

```text
Likely A/B:
  GE6iywJtsV / graph_control_module
  NnExMNiTHw / acceptance_prediction_head
  QAgwFiIY4p / paper-named_graphormer_baseline
  YXn76HMetm / equalal_baseline

Likely false positive or at least downgrade:
  9zEBK3E9bX / including_loss
```

Implemented after the preaudit:

- `including ...` missing-ablation targets are now rejected as prose fragments,
  preventing selector/menu supply from treating sentence glue like `including
  loss` as a contribution-bearing component.
- Full-text ablation counterevidence now recognizes SPOT-style pre-training
  strategy tables where `loss balancing` is explicitly covered by an ablation
  table and surrounding text.
- Missing-ablation component anchors can be inferred from a reviewer-provided
  inventory quote even when `observed_items` is empty, as long as the quote is
  current-paper component text and contains the target tokens.
- Deterministic component-ablation seed/menu supply can use a locatable
  claim-surface component anchor such as `learned routing component`, without
  requiring every valid claim sentence to contain `we propose`.

Validation:

```text
focused hygiene missing-ablation/state tests = 56 passed
focused runner/gate selected-menu tests = 26 passed
py_compile state.py/test files = PASS
three-file broad suite = 806 passed / 28 failed
```

Interpretation:

```text
The fresh hardneg20 proves the Stage 2 path is functional at machine-gate
level: Critique-selected menu candidates are entering strict verification and
forming non-seed-shadow clusters.  It does not yet prove paper-ready precision:
at least one machine-passing Critique cluster was a real false positive.  After
the fix, the expected Critique direct cluster count should still be >=3, but
that requires a fresh sample or hardneg20 rerun before it can be claimed.

Stage 3 is live but incomplete: `mark_contested_commit_count=10`, while
`verified_issue_cluster_without_recovery_count=10`.  The next major direction
after rerun confirmation is contested/recovery coverage, not more seed
quantity.
```

Next step:

```text
Run a fresh small sample that includes 9zEBK3E9bX or a fresh hardneg20 after the
SPOT false-positive fix.  If protection stays clean and direct Critique
clusters remain >=3 after removing `including_loss`, move the main engineering
focus to Stage 3 contested relation / recovery coverage.
```

## Previous P31.25/P31.26 Checkpoint 2026-07-05

Current stage:

```text
Stage 2 is active.  Selected-menu candidates now reach strict verification and
can verify cleanly, but direct Critique-origin clusters are still 2/3 on the
latest sample.  The main remaining risk is selector/menu identity fidelity:
candidate_menu_id must be a reliable pointer to exactly the selected target.
```

Implemented after P31.24:

- Added supply-quality guards for P31.24 failure modes:
  - runner/entity generated `quantitative result for ...` placeholders are
    filtered before they enter the selector menu;
  - entity-generated `quantitative result table for ...` placeholders are
    filtered without changing historical Critique-selected attribution;
  - generic `metric reporting protocol or comparability setting` menu targets
    are filtered as protocol-generic.
- Fixed `candidate_menu_id` collision for long same-prefix targets such as
  paper-named `EqualAL` vs `PixelPick`.  Menu ids are now disambiguated during
  ReviewState menu generation and runner seed-menu expansion, preventing a
  selected id from binding to a different target after lookup.

Validation:

```text
runner selector/menu focused suite = 16 passed
hygiene/gate focused suite = 28 passed
paper-named/id-collision focused tests = 13 passed
runner id-collision focused tests = 4 passed
py_compile state.py/review_runner.py/tests = PASS
git diff --check = PASS
```

Live sample:

```text
run = p31_25_supply_filter_sample3_20260705_180321
rows = 3
sample = HPuLU6q7xq, QAgwFiIY4p, YXn76HMetm
protection = PASS
evidence_json_fallback_rate_pct = 0
state_contamination_count = 0
verified_review_issue_cluster_count = 4
critique_payload_verified_cluster_count = 2
critique_direct_verified_cluster_count = 2
candidate_menu_item_count = 2
candidate_menu_item_used_count = 2
candidate_menu_item_verified_count = 2
candidate_menu_item_failed_count = 0
```

Interpretation:

```text
The supply filter improved selected-menu quality: no selected-menu verifier
failures remained in this sample, and 2/2 selected menu items verified.  The
machine gate still fails because direct Critique-origin clusters are 2/3, not
3/3.  During audit, YXn exposed a candidate_menu_id collision that could make
candidate_menu_item_verified_count look healthier than the exact target binding
really was.  That collision is now fixed in code, but needs a fresh sample
before claiming improved direct-cluster count.
```

Next step:

```text
Rerun the 3-paper sample after the id-collision fix.  If selected-menu
verified_count stays clean and direct Critique clusters reach >=3 with
protection still passing, then move to hardneg20.  If direct remains 2/3, audit
which paper lacks a Critique-origin cluster and improve selector exposure rather
than verifier looseness.
```

## Current P31.24 Checkpoint 2026-07-05

Current stage:

```text
Stage 1 / ReviewState credibility remains protected on the current path.
Stage 2 / real Critique-discovered review issues is active.
The immediate bottleneck is no longer selected-menu id loss: copied
candidate_menu_id values now materialize into verifier-ready candidates.  The
remaining bottleneck is selector supply quality: fresh selected menu candidates
are reaching the verifier but failing strict bundle checks.
```

Implemented:

- Critique `selected_menu_items` recovery no longer depends exclusively on the
  logged `review_issue_discovery_required` flag.  If a copied
  `candidate_menu_id` resolves against the current selector menu, the runner
  materializes it into a `critique_payload_menu_selected`
  `reviewer_negative_candidate`.
- Seed top-up remains gated on formal review-issue discovery; only copied menu
  id recovery was widened.
- Selected-menu materialization now uses structured menu rationale before model
  selection rationale and strips `...[truncated]` prompt-compaction markers, so
  retrieval/context-gap guards do not incorrectly drop menu-backed candidates.
- Runner seed supply can include concrete component-ablation targets exposed by
  ReviewState, still with strict bundle verification.

Validation:

```text
py_compile review_runner.py/tests/test_review_inference_runner.py = PASS
runner selector/menu focused suite = 14 passed
hygiene/gate focused suite = 24 passed
P31.23 WNxl offline selected-menu replay = recovered critique_payload_menu_selected candidate
```

Live sample:

```text
run = p31_24_selected_menu_recovery_sample3_20260705_171944
rows = 3
sample = ye3NrNrYOY, WNxlJJIEVj, uOrfve3prk
protection = PASS
evidence_json_fallback_rate_pct = 0
state_contamination_count = 0
candidate_menu_item_count = 3
candidate_menu_item_used_count = 3
candidate_menu_item_verified_count = 0
candidate_menu_item_failed_count = 3
candidate_menu_item_failed_by_reason =
  missing_entity_already_observed_in_inventory: 2
  observed_inventory_missing: 1
critique_direct_verified_cluster_count = 0
```

Interpretation:

```text
The Critique-selected-menu -> verifier path is now functionally live in a fresh
API sample, but this sample selected items that the strict verifier correctly
rejected.  Do not relax verifier/validator gates.  The next Stage 2 work is
selector supply/ranking: expose concrete paper-grounded items that are not
already observed in inventory and have copied inventory anchors.
```

Next step:

```text
Audit failed selected menu items from P31.24 and P31.22/P31.23, improve supply
filters/ranking for already-observed and missing-inventory cases, then rerun a
3-paper sample.  Only after selected-menu verified_count is nonzero with clean
protection should we run a fresh hardneg20.
```

## Previous P31.17 Checkpoint 2026-07-05

Current stage:

```text
Stage 1 / ReviewState credibility remains protected for the current path.
Stage 2 / real Critique-discovered negatives is active.
The immediate bottleneck was Graphormer-style paper-named baseline targets:
Critique selected the menu item, but bundle verification treated the method
name as generic/truncated and then could confuse Related Work mentions with
current comparison inventory.
```

Implemented:

- Paper-named baseline selector/menu provenance now survives the full selected
  menu path:
  - `paper_named_baseline_name`
  - `paper_named_baseline_expectation_quote`
  - `paper_named_baseline_expectation_locator`
  - `paper_named_baseline_expectation_grounding_label`
- Missing-baseline specificity now accepts single-word paper-named method
  targets such as `Graphormer` only when the bundle/menu provenance proves the
  exact grounded paper context.
- Related Work paper-named mentions are excluded from current observed
  comparison inventory for missing-baseline bundle verification; table/result
  comparison anchors remain valid inventory.
- Deterministic paper-named seed supply now shares the selector menu's
  conservative no-limited-cue supply path, while attribution remains separate
  from direct Critique-origin metrics.

Validation:

```text
py_compile state.py/test_review_decision_hygiene.py/review_runner.py = PASS
graphormer or paper_named suite = 12 passed
hygiene/gate selected-menu focused suite = 27 passed
runner selected-menu/discovery focused suite = 21 passed
git diff --check = PASS
```

Live sample status:

```text
attempted run = p31_17_paper_named_provenance_sample3_20260705_160710.jsonl
status = blocked before useful rows
reason = MiMo 401 Authentication Fails for currently loaded key ending b5zO
```

Known validation caveat:

```text
full tests/test_review_decision_hygiene.py is not green in this worktree:
444 passed / 23 failed.
Do not claim full-file green from P31.17; current evidence is the focused
suite set above.
```

Next step:

```text
Fix/refresh the active MiMo key, rerun the 3-paper sample, and inspect whether
QAgwFiIY4p/Graphormer now becomes a direct Critique-origin verified issue.
If the sample shows clean protection and at least two verifier-surviving
selected-menu clusters, run a fresh hardneg20.  Do not loosen verifier gates or
merge deterministic seed clusters into Critique-origin counts.
```

## Current P31.13 Checkpoint 2026-07-05

P0 MiMo JSON reliability is validated and downstream work is back on the
Critique selector/menu supply path.

Latest fresh full20:

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
candidate_menu_item_verified_count = 2
```

Gate status:

```text
machine_gate = FAIL
critique_direct_verified_cluster_count = 0 < 3
case_table_critique_origin_cluster_count = 2 < 3
```

Implemented in the current code pass:

- Filter generic scope/result menu templates before they reach bundle
  verification, including `quantitative result table or metric for <entity>`,
  `metric/result table for the claimed effect`, and `held-out benchmark or
  stress setting for <entity>`.
- Remove primary-entity scope/result fallbacks from entity obligations and
  runner seed blueprint fallback.
- Reject bare temporal descriptors such as `long-term` as missing-ablation
  components while keeping named modules/components eligible.

Offline recompute over the same raw:

```text
artifacts = P31_13_MENU_QUALITY_RECOMPUTE_20260705_130323_*
verified_review_issue_count = 15
verified_review_issue_cluster_count = 12
critique_direct_verified_cluster_count = 0
critique_selected_existing_seed_cluster_count = 2
candidate_menu_item_verified_count = 2
candidate_menu_item_failed_by_stage =
  menu_quality_guard: 8
  counterevidence: 2
  claim_anchor: 2
  bundle_verification_or_not_materialized: 1
  concrete_item_check: 1
```

Validation:

```text
focused state/menu tests = 31 passed
focused runner selected-menu tests = 20 passed
focused hygiene/gate suite = 16 passed
py_compile state.py/review_runner.py/test files = PASS
```

Next step:

```text
Run a fresh response-format-on hardneg20 from current code.  Old-raw recompute
can only relabel or remove stale/template candidates; it cannot prove direct
Critique discovery because Critique already selected the old menu.
```

Fresh validation and precision update:

```text
fresh raw = mimo_v25_negqty_recoverycap_guard3_qhyg_targetneg_freeformrevneg_reviewissuebundle_hardneg20_mt7_b4w2_api4_r8t600_tok2048_20260705_132812.jsonl
fresh artifacts = P31_6_FRESH_20260705_132812_*
rows = 20
evidence_json_valid_turns = 62
evidence_json_fallback_turns = 1
evidence_json_fallback_rate_pct = 2
protection = PASS
state_contamination_count = 0
fresh critique_direct_verified_cluster_count = 2
fresh candidate_menu_item_verified_count = 2
```

Manual audit of the two fresh direct clusters found both were precision risks:

- `ye3NrNrYOY / evaluation_protocol_risk / metric_definition_threshold_selection_protocol`
  is a generic protocol target; paper text already gives Top-1 accuracy and
  official split details.
- `cklg91aPGk / missing_baseline / recent_gnn_graph-transformer_baselines...`
  is an external family baseline template, not a paper-named missing baseline.

Current code now rejects those at bundle verification, not only telemetry.  It
also rejects generic ablation targets such as `component-removal experiment for
the claimed mechanism` before verified issue creation:

```text
current-code recompute = P31_13_MENU_QUALITY_RECOMPUTE_20260705_132812_*
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

Updated next step:

```text
Do not rerun another full20 immediately.  First improve concrete selector menu
supply so Critique sees paper-named baseline targets, metric-specific protocol
targets, and ablation/component targets that are not already countered by
inventory.  Keep verifier/validator gates strict.
```

Stage 2 supply first pass:

- Paper-named baseline selector supply now has a menu-only widening path:
  deterministic seed verification still requires limited-comparison wording,
  but Critique selector menu may show a paper-named related/prior method when:
  the claim is comparative, the related method is named in the paper, current
  evaluation/comparison inventory is locatable, and the inventory does not
  already include that method.
- Related-work or baseline-list contexts that say the paper already compares
  against the named method are treated as counter-supply and do not generate
  missing-baseline menu candidates.
- Baseline menu inventory anchors are restricted to evaluation/comparison
  anchors, not plain related-work citations.
- Offline selector probe on fresh raw `20260705_132812` now shows 3
  paper-named baseline menu candidates from current code (`GPT-4`,
  `Graphormer`, `EqualAL`) and keeps old-run recompute metrics unchanged:
  protection PASS, `critique_direct_verified_cluster_count=0`,
  `candidate_menu_item_verified_count=0`.

## Current P31.11 Checkpoint 2026-07-05

P31.11 turns the Critique selector path into a more functional direct candidate
bridge, while keeping verifier and final-view guards strict.

Fresh run/artifacts:

```text
raw = mimo_v25_negqty_recoverycap_guard3_qhyg_targetneg_freeformrevneg_reviewissuebundle_hardneg20_mt7_b4w2_api4_r8t600_tok2048_20260705_030000.jsonl
dashboard = P31_11_FRESH_DIRECT_BRIDGE_20260705_030000_HARDNEG20_DASHBOARD.md/json
case table = P31_11_FRESH_DIRECT_BRIDGE_20260705_030000_REVIEW_ISSUE_CASE_TABLE.md/json
recovery table = P31_11_FRESH_DIRECT_BRIDGE_20260705_030000_RECOVERY_CASE_TABLE.md/json
entry gate = P31_11_FRESH_DIRECT_BRIDGE_20260705_030000_ENTRY_GATE_AUDIT.md/json
```

Current facts:

```text
protection = PASS
verified_review_issue_count = 21
verified_review_issue_cluster_count = 18
review_negative_verified_count = 1
critique_payload_verified_cluster_count = 2
critique_direct_verified_cluster_count = 2
candidate_menu_item_count = 14
candidate_menu_item_used_count = 14
candidate_menu_item_verified_count = 2
positive_or_neutral_negative_candidate_count = 0
positive_or_neutral_negative_rejected_count = 1
state_contamination_count = 0
state_contamination_count_legacy = 15
state_hygiene_warning_count = 15
mark_contested_commit_count = 11
verified_issue_cluster_without_recovery_count = 9
```

Implemented:

- Critique-selected menu ids are materialized as real `reviewer_negative_candidates`.
- Selected menu candidates preserve their snapshot claim id instead of being
  rebound to another claim and silently dropped.
- Selector now prioritizes high-quality verifier-survivable candidates before
  using slot diversity to fill remaining menu space.
- Seed top-up remains separate from direct Critique attribution.
- Positive/neutral negative-looking records are rejected diagnostics, not active
  protection failures.
- `state_contamination_count` now reports hard contamination only; weak target
  lifecycle issues remain in warning counters.
- Positive-context review-negative guard no longer rejects true baseline-beats-
  proposed negative results, while explicit lower-is-better metric improvements
  still reject as positive/neutral support.

Validation:

```text
focused hygiene/gate selector suite = 11 passed
runner selected-menu/discovery suite = 18 passed
py_compile = PASS
broader 3-file suite = 765 passed / 31 failed
sample3 MiMo hardneg smoke = completed 3/3 rows
```

Sample3 smoke:

```text
run = p31_11_sample3_direct_bridge_20260705_114014.jsonl
rows = 3
protection = PASS
verified_review_issue_count = 1
verified_review_issue_cluster_count = 1
candidate_menu_item_count = 5
candidate_menu_item_used_count = 5
candidate_menu_item_verified_count = 0
critique_direct_verified_cluster_count = 0
state_contamination_count = 0
```

Interpretation: the real API path now materializes selected-menu candidates,
but this 3-row sample did not produce a verifier-surviving Critique menu
candidate.  Failures were strict verifier/quality outcomes:
`missing_entity_already_observed_in_inventory`, `generic_item`, and
`selected_menu_item_not_in_current_menu_or_filtered`.  Treat this as a supply
and selector-quality signal, not a reason to loosen verification.

Entry gate remains blocked on real functional quantity:

```text
critique_direct_verified_cluster_count = 2 < 3
case_table_critique_origin_cluster_count = 2 < 3
```

Next step:

```text
Do not relax verifier gates.  Audit the remaining review-issue bundle boundary
failures only where they affect selector supply, then run a fresh hardneg20 to
test whether direct Critique verified clusters reach >=3.
```

## Current P31.9 Checkpoint 2026-07-05

P31.9 is an audit/instrumentation pass over the latest fresh P31.8 full20 raw run, not a new API run.

Artifacts:

```text
raw = mimo_v25_negqty_recoverycap_guard3_qhyg_targetneg_freeformrevneg_reviewissuebundle_hardneg20_mt7_b4w2_api4_r8t600_tok1536_20260704_191150.jsonl
dashboard = P31_9_CRITMENU_AUDIT_FROM_FRESH_20260704_191150_HARDNEG20_DASHBOARD.md/json
case table = P31_9_CRITMENU_AUDIT_FROM_FRESH_20260704_191150_REVIEW_ISSUE_CASE_TABLE.md/json
recovery table = P31_9_CRITMENU_AUDIT_FROM_FRESH_20260704_191150_RECOVERY_CASE_TABLE.md/json
entry gate = P31_9_CRITMENU_AUDIT_FROM_FRESH_20260704_191150_ENTRY_GATE_AUDIT.md/json
manual audit template = P31_9_CRITMENU_AUDIT_FROM_FRESH_20260704_191150_MANUAL_AUDIT_TEMPLATE.md/json
```

Fresh/P31.9 facts:

```text
full20 completed = 20/20
protection = PASS
verified_review_issue_count = 18
verified_review_issue_cluster_count = 16
review_negative_verified_count = 2
critique_payload_verified_cluster_count = 2
critique_direct_verified_cluster_count = 0
critique_selected_existing_seed_cluster_count = 2
candidate_menu_item_verified_count = 2
candidate_menu_item_failed_detail_count = 5
mark_contested_commit_count = 4
verified_issue_cluster_without_recovery_count = 11
negative_evidence_unlinked_to_flaw = 0
positive_or_neutral_negative_candidate_count = 0
negative_grounding_conflict_count = 0
```

Entry gate:

```text
machine_gate = FAIL
manual_gate = REQUIRED
blocking = critique_payload_verified_cluster_count 2 < 3
blocking = case_table_critique_origin_cluster_count 2 < 3
```

Interpretation:

- The two Critique-selected clusters are not direct Critique-generated verified issues; both are selected-menu matches to existing deterministic seed clusters.
- P32 remains blocked until a fresh run has direct Critique verified clusters, not merely selected-existing attribution.
- P31.9 dashboard/gate artifacts now preserve selected-menu failure details.

Next step:

```text
Fix direct selected-menu candidate materialization and menu starvation.  Keep seed top-up separate from Critique autonomous discovery metrics; do not relax verifier gates.
```

## Current P31.7 Checkpoint 2026-07-03

P31.7A audit-fix is implemented: manual audit is cluster-level, dashboard/case
cluster counts are current-code recomputed and consistent, seed menu ids no
longer count as Critique-selected menu success, and high-risk false-positive
guards remain strict.

Current authoritative fresh run:

```text
raw = mimo_v25_negqty_recoverycap_guard3_qhyg_targetneg_freeformrevneg_reviewissuebundle_hardneg20_mt7_b4w2_api4_r8t600_tok1536_20260703_231747.jsonl
dashboard = P31_6_FRESH_20260703_231747_HARDNEG20_DASHBOARD.md/json
case table = P31_6_FRESH_20260703_231747_REVIEW_ISSUE_CASE_TABLE.md/json
recovery table = P31_6_FRESH_20260703_231747_RECOVERY_CASE_TABLE.md/json
entry gate = P31_6_FRESH_20260703_231747_ENTRY_GATE_AUDIT.md/json
manual audit template = P31_6_FRESH_20260703_231747_MANUAL_AUDIT_TEMPLATE.md/json
readiness = P31_6_FRESH_20260703_231747_READINESS_STATUS.md/json
```

Fresh P31.7 facts:

```text
full20 completed = 20/20
api_success = 271
api_errors = 0
protection = PASS
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
```

Entry gate:

```text
machine_gate = FAIL
manual_gate = REQUIRED
blocking = critique_payload_verified_cluster_count 0 < 3
blocking = candidate_menu_item_verified_count 0 < 2
blocking = case_table_critique_origin_cluster_count 0 < 3
cluster_count_consistency = PASS
protection = PASS
```

Interpretation:

- P31.7A succeeded as an audit/metric/protection cleanup.
- P31.7B first implementation did not solve autonomous Critique discovery.
  Simplifying the prompt to selected-menu primary made Critique more conservative
  and reduced total verified issue clusters from the prior fresh attempt's 20 to
  11.
- P32 remains blocked.  Do not treat deterministic-seed verified issue quantity
  as autonomous Critique discovery.

Next step:

```text
Design a second Critique autonomy pass around candidate-menu salience and
selection supervision.  The current model rarely selects menu ids and still
falls back to weak free-form candidates; do not loosen verifier gates.
```

## Current P31.6 Fresh Full20 Checkpoint 2026-07-03

Fresh MiMo full20 completed with API workers set to 4 after updating the local
MiMo credentials in `.env` and confirming API preflight success.

Artifacts:

```text
raw = mimo_v25_negqty_recoverycap_guard3_qhyg_targetneg_freeformrevneg_reviewissuebundle_hardneg20_mt7_b4w2_api4_r8t600_tok1536_20260703_082133.jsonl
dashboard = P31_6_FRESH_20260703_082133_HARDNEG20_DASHBOARD.md/json
case table = P31_6_FRESH_20260703_082133_REVIEW_ISSUE_CASE_TABLE.md/json
recovery table = P31_6_FRESH_20260703_082133_RECOVERY_CASE_TABLE.md/json
entry gate = P31_6_FRESH_20260703_082133_ENTRY_GATE_AUDIT.md/json
manual audit template = P31_6_FRESH_20260703_082133_MANUAL_AUDIT_TEMPLATE.md/json
readiness status = P31_6_FRESH_20260703_082133_READINESS_STATUS.md/json
```

Fresh P31.6 facts:

```text
full20 completed = 20/20
protection = PASS
evidence_json_fallback_rate_pct = 0
verified_review_issue_count = 14
verified_review_issue_cluster_count = 12
quote_duplicate_merged_verified_review_issue_cluster_count = 12
reviewer_candidate_review_issue_count = 13
reviewer_candidate_review_issue_critique_payload_count = 1
reviewer_candidate_review_issue_deterministic_seed_count = 12
critique_payload_verified_cluster_count = 1
case_table_critique_origin_cluster_count = 1
mark_contested_commit_count = 4
verified_review_issue_repair = 3
negative_evidence_unlinked_to_flaw = 0
positive_or_neutral_negative_candidate_count = 0
negative_grounding_conflict_count = 0
review_negative_verified_count = 0
```

Entry-gate result:

```text
machine_gate = FAIL
manual_gate = REQUIRED
blocking = critique_payload_verified_cluster_count 1 < 3
blocking = case_table_critique_origin_cluster_count 1 < 3
```

Interpretation:

- The fresh run is clean on protection and JSON reliability, but it regressed
  from the old-raw/current-code recompute Critique-origin count of 2 to 1.
- The only Critique-origin cluster listed for manual audit is
  `GE6iywJtsV / reproducibility_gap / implementation_reproducibility_details`.
- Verified issues are still dominated by deterministic seeds:
  10 missing-ablation clusters and 2 reproducibility clusters.
- P32 remains blocked.  Do not treat this fresh full20 as paper-ready.

Next step:

```text
Audit why Critique payload discovery/selection still collapses to one verified
cluster in fresh execution, focusing on selected-menu candidate construction,
bundle rejection reasons, and whether deterministic seed top-up is masking
weak Critique payload uptake.  Keep verifier strict.
```

Current authoritative fresh run:

```text
raw = mimo_v25_negqty_recoverycap_guard3_qhyg_targetneg_freeformrevneg_reviewissuebundle_hardneg20_mt7_b4w2_api4_r8t600_tok1536_20260702_131007.jsonl
dashboard = P31_3_FRESH_API4_131007_HARDNEG20_DASHBOARD.md/json
case table = P31_3_FRESH_API4_131007_REVIEW_ISSUE_CASE_TABLE.md/json
recovery table = P31_3_FRESH_API4_131007_RECOVERY_CASE_TABLE.md/json
```

Fresh P31.3 facts:

```text
full20 completed = 20/20
protection = PASS
verified_review_issue_count = 14
verified_review_issue_cluster_count = 11
critique_payload_verified_cluster_count = 2
candidate_menu_item_used_count = 6
candidate_menu_item_verified_count = 1
mark_contested_commit_count = 8
```

Current P31.4 working-tree facts:

```text
old-raw recompute = P31_4_MENUFIX_RECOMPUTE_163953_*
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

Latest fresh validation attempt:

```text
run = mimo_v25_negqty_recoverycap_guard3_qhyg_targetneg_freeformrevneg_reviewissuebundle_hardneg20_mt7_b4w2_api4_r8t600_tok1536_20260702_213525.jsonl
status = partial only, 8/20 rows
blocker = MiMo API 402 insufficient account balance
artifacts = P31_4_MENUFIX_PARTIAL8_213525_*
verified_review_issue_count = 4
verified_review_issue_cluster_count = 4
critique_payload_verified_cluster_count = 0
review_issue_selected_menu_recovery_turns = 1
candidate_menu_item_used_count = 1
candidate_menu_item_verified_count = 0
protection counters = 0
```

Interpretation:

- P31.3 is a progress checkpoint, not completion.
- P31.4 is precision, observability, and selector-input work; old raw output will not show runtime quantity gains.
- The selected-menu path is now proven to enter the candidate path, but partial8 shows selected/menu candidates are still being rejected by the strict bundle verifier.
- `213525` is not an authoritative full20 result because the API account balance failed mid-run.
- Critique selector target remains unmet: `critique_payload_verified_cluster_count >= 3`.

Recent P31.4 code changes:

- Candidate-level failed-menu telemetry and bundle stop-stage attribution.
- Narrow qualitative-vs-quantitative same-setting result gap remap through existing `result_claim_mismatch`, with full counterevidence still enforced.
- Slot-diverse selector menu selection and Critique-visible menu budget raised from 4 to 6.
- Lightweight `selected_menu_items` / `rejected_menu_items` path: selected visible menu ids are expanded into pending verifier-ready candidates before deterministic seed top-up.
- Selected menu recovery now uses current per-claim menu ids, not only selector top-6, and `critique_payload*` origins are counted consistently across state/dashboard/case tables.

Next step:

```text
After MiMo balance is available, rerun fresh API hardneg20 from current code; otherwise continue selector target-quality work offline.
Acceptance for moving toward P32:
  critique_payload_verified_cluster_count >= 3
  protection PASS
  manual A/B quality does not regress
  no verifier relaxation / no generic retrieval-context gaps
  review_issue_selected_menu_recovery_turns / recovered_count are reported for prompt uptake diagnosis
```

Hard constraints:

- Do not use `/Users/zss/Downloads/DrMAS-master`; it is stale.
- Do not relax bundle verifier, author-limitation guard, retrieval-gap guard, target-quality guard, or fallback/context claim guards.
- Do not use reference reviews as system input.
- Keep recovery non-destructive: use `mark_contested`, not claim downgrade.

## Current P31.5 Checkpoint

Implemented a narrow selector target-quality guard:

- Missing-ablation menu items are suppressed when claim/inventory text already contains ablation counterevidence for the same target.
- Verb-form action fragments such as `constrain module` are rejected as weak missing-ablation targets; noun/mechanism targets such as `constraint module` remain eligible as medium-confidence when contribution/performance context supports them.
- Component-ablation deterministic seeds now apply the same target-quality and ablation-counterevidence checks, so preposition fragments like `by the dynamic tree attention` and already-covered ablation targets are not generated as future seeds.
- Local ablation figure/table/study anchors now resolve missing-ablation targets when at least two concrete target tokens match; negated phrases such as `no ablation for ...` do not count as counterevidence.
- Failed selected-menu telemetry now separates stale/filtered selected ids (`selected_menu_item_not_in_current_menu_or_filtered`) from true bundle-verifier failures.

Validation:

```text
py_compile state.py/review_runner.py/dashboard/case-table/tests = passed
ablation resolver/menu failure focused tests = 4 passed
target/menu/seed selector focused tests = 8 passed
selected-menu recovery focused tests = 5 passed
P31_5_TARGETQUALITY_PARTIAL8_213525_UNCACHED_* protection = PASS
```

Partial8 recompute facts:

```text
source run = 20260702_213525 partial, 8/20 only; UNCACHED current-code recompute
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
protection counters = 0
```

Do not treat this as a completed full20 result.  The next concrete work remains P31.5 selector target-quality / candidate construction, because selected-menu plumbing fires but no Critique-selected candidate has reached a verified cluster yet.

## Current P31.5 Full20 Checkpoint 2026-07-02

The P31.5 minimum Critique-origin target is now met on a complete full20 current-code recompute over the existing `20260702_163953` raw MiMo run.

Artifacts:

```text
P31_5_TARGETQUALITY_FULL20_163953_UNCACHED_HARDNEG20_DASHBOARD.md/json/audit.json
P31_5_TARGETQUALITY_FULL20_163953_UNCACHED_REVIEW_ISSUE_CASE_TABLE.md/json
P31_5_TARGETQUALITY_FULL20_163953_UNCACHED_RECOVERY_CASE_TABLE.md/json
```

Key code changes:

- Normalize multi-name Critique missing-baseline lists, e.g. `FairNAS/SNAS/ProxylessNAS/EWC/GEM`, into verifier-ready same-setting baseline items.
- Allow a single acronym baseline only when the candidate text explicitly contextualizes it as a baseline/method/comparison target; stale cases still fall to full-text counterevidence.
- Preserve freeform Critique attribution over runner seed metadata when overlapping gaps merge.
- Add scope/generalization cues for `generalizable`, `cross-target`, `target shapes/classes`, and `molecular classes`.
- Reuse a precomputed non-generic candidate relevance basis at bundle expectation time, preserving strict inventory and counterevidence checks.

Validation:

```text
focused state pytest = 17 passed
focused runner pytest = 5 passed
py_compile = passed
dashboard --fail-on-violation = PASS
```

Full20 metrics:

```text
verified_review_issue_count = 18
verified_review_issue_cluster_recomputed_count = 16
critique_payload_verified_cluster_count = 3
verified_review_issue_cluster_origin_critique_payload_count = 3
reviewer_candidate_review_issue_critique_payload_count = 3
reviewer_candidate_review_issue_deterministic_seed_count = 13
negative_evidence_unlinked_to_flaw = 0
positive_or_neutral_negative_candidate_count = 0
negative_grounding_conflict_count = 0
mark_contested_commit_count = 5
protection = PASS
```

Critique-origin clusters to manually audit before P32:

```text
GE6iywJtsV / cross-target validation
YXn76HMetm / hyperbolic curvature + active-learning reproducibility details
KOUAayk5Kx / FairNAS/SNAS/ProxylessNAS/EWC/GEM missing baseline
```

Next step:

```text
Manual A/B/C/D audit of the 3 Critique-origin clusters and spot-check surrounding case-table rows.
If manual quality is acceptable and protection remains PASS, move to P32 reproducibility/result-freezing.
If YXn inventory anchor is judged too weak, tighten reproducibility inventory relevance before P32.
```

## Current P31.5 Manual Audit Update 2026-07-03

Manual audit:

```text
P31_5_CRITIQUE_ORIGIN_MANUAL_AUDIT_20260703.md
```

The pre-audit `critique_payload_verified_cluster_count = 3` is superseded.
Manual audit rejected the KOUA missing-baseline cluster as an external baseline-list
false positive because the paper already reports comparison with `13
state-of-the-art one-shot NAS competitors`.

New precision guard:

```text
full_text_broad_baseline_comparison_counterevidence
```

Prompt-side follow-up:

```text
Critique discovery now explicitly says not to invent external well-known baseline lists when the paper already reports a broad same-setting comparison set; missing-baseline candidates should be paper-named or menu/inventory-auditable.
```

Current full20 after guard:

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

Decision:

```text
P31.5 remains active.
Do not enter P32 yet.
Need at least one more A/B Critique-origin cluster without reintroducing external-baseline false positives.
```

## Current P31.6 Status 2026-07-03

Standalone status document:

```text
P31_6_CRITIQUE_ORIGIN_STATUS_20260703.md
```

Implemented a discovery-input / counterevidence precision batch:

- plain `without` no longer counts as missing-ablation counterevidence unless it
  is in ablation/comparison/result context;
- Critique missing-ablation candidates may use locatable full-text component
  anchors before the unchanged strict bundle verifier;
- reviewer-candidate missing targets stay primary over coarse automatic
  claim-obligation targets;
- Critique prompt now makes the selector menu the primary channel and requires
  selected menu ids to be mirrored in `selected_menu_items`.

Validation:

```text
P31/P31.5 focused state tests = 21 passed
P31 prompt/recovery focused tests = 6 passed
py_compile = passed
P31_6_CRITORIGIN_RECOMPUTE_163953 dashboard protection = PASS
```

Current old-raw recompute:

```text
verified_review_issue_count = 19
verified_review_issue_cluster_recomputed_count = 16
critique_payload_verified_cluster_count = 2
verified_review_issue_cluster_origin_critique_payload_count = 2
negative_evidence_unlinked_to_flaw = 0
positive_or_neutral_negative_candidate_count = 0
negative_grounding_conflict_count = 0
mark_contested_commit_count = 5
```

Next:

```text
Run a fresh MiMo full20 with P31.6 code/prompt.
Generate dashboard, review issue case table, and recovery table.
Manually audit Critique-origin clusters.
Enter P32 only if critique_payload_verified_cluster_count >= 3 with A/B quality
and protection PASS.
```

Fresh run attempt `20260703_011822` was stopped with `jsonl_lines=0` because
the MiMo API returned `402 insufficient_balance` before any paper completed.  Do
not treat it as a partial result.  Retry the same P31.6 full20 command only after
the active MiMo key/account has usable balance.

Runtime reliability follow-up:

```text
ApiReviewGenerator now fast-fails non-retryable API errors
(402 insufficient_balance/quota/billing/auth/permission) instead of retrying.
Focused API/P31 prompt tests = 8 passed.
```

Launcher follow-up:

```text
run_hardneg20_guard3.sh now performs a one-call API preflight before creating
run artifacts or launching the background full20 job.
DRMAS_API_PREFLIGHT=0 disables this only for manual debugging.
bash -n passed.
Current MiMo key still returns 402 insufficient_balance; launcher exits before
creating a new .meta/.pid/.jsonl or background process.
Latest retry 20260703_014718 still fast-failed 402, but the launcher now
suppresses the Python traceback and prints a concise preflight failure line.
```

Artifact-generation follow-up:

```text
scripts/p31_6_generate_full20_artifacts.sh is now executable and validated.
bash -n passed.
Dry-run on P31_5_TARGETQUALITY_FULL20_163953_UNCACHED.jsonl passed.
Real generation on the same full20 raw reproduced the authoritative P31.6
metrics exactly:
  verified_review_issue_count = 19
  verified_review_issue_cluster_recomputed_count = 16
  critique_payload_verified_cluster_count = 2
  negative_evidence_unlinked_to_flaw = 0
  positive_or_neutral_negative_candidate_count = 0
  negative_grounding_conflict_count = 0
  mark_contested_commit_count = 5
  protection = PASS
The temporary P31_6_SCRIPT_CHECK_163953_* outputs were removed after
comparison.  Expect the dashboard step to take several minutes on full20
because it recomputes decision hygiene.
```

P31.6 entry-gate follow-up:

```text
scripts/p31_6_entry_gate_audit.py added.
It reads dashboard/case/recovery JSON, checks the machine P32-entry gates, and
lists Critique-origin clusters for manual A/B audit.
Current old-raw report:
  P31_6_CRITORIGIN_RECOMPUTE_163953_ENTRY_GATE_AUDIT.md/json
  machine_gate = FAIL
  critique_payload_verified_cluster_count = 2 (<3)
  case_table_critique_origin_cluster_count = 2 (<3)
  protection = PASS
  lexical red flags = 0
  manual_gate = REQUIRED
The artifact generator now includes ENTRY_GATE_AUDIT outputs by default.  A
failed gate does not abort artifact generation unless --fail-entry-gate is set.
Latest lightweight MiMo API check at 20260703_015444 still returned
402 insufficient_balance, so no fresh full20 was started.
```

P31.6 manual-audit follow-up:

```text
Operational runbook:
  P31_6_FRESH_FULL20_RUNBOOK_20260703.md

scripts/p31_6_manual_audit.py added.
Subcommands:
  template  -> create a fillable Critique-origin manual A/B audit from an
               ENTRY_GATE_AUDIT.json
  validate  -> validate filled audit JSON and enforce:
               manual_A_B_clusters >= 3
               manual_D_clusters = 0
               unfilled_clusters = 0

Current old-raw artifacts:
  P31_6_CRITORIGIN_RECOMPUTE_163953_MANUAL_AUDIT_TEMPLATE.md/json
  P31_6_CRITORIGIN_RECOMPUTE_163953_MANUAL_AUDIT.json
  P31_6_CRITORIGIN_RECOMPUTE_163953_MANUAL_AUDIT_VALIDATION.md/json
  P31_6_CRITORIGIN_RECOMPUTE_163953_ENTRY_GATE_WITH_MANUAL_AUDIT.md/json

scripts/p31_6_generate_full20_artifacts.sh now generates
  <LABEL>_MANUAL_AUDIT_TEMPLATE.md/json
and <LABEL>_READINESS_STATUS.md/json by default after the entry-gate report.
Use --skip-manual-template / --skip-status-report only when those outputs are
not wanted.  Dry-run confirmed the default post-processing chain:
  dashboard -> review issue cases -> recovery cases -> entry gate -> manual template -> readiness status
Regression coverage:
  tests/test_p31_6_gate_scripts.py = 5 passed
  focused inference tests = 8 passed
  bash -n / py_compile = passed

Pipeline wrapper:
  scripts/p31_6_full20_pipeline.sh added.
  Use after MiMo balance is usable:
    scripts/p31_6_full20_pipeline.sh --launch --wait --update-latest
  This launches with P31.6 flags, waits for completion, and postprocesses into
  dashboard/case/recovery/entry-gate/manual-template artifacts.
  Dry-run validated both launch and existing-run postprocess command paths.
  Real launch check at 20260703_021333 still fast-failed on 402 before creating
  any run artifacts.

Readiness/status report:
  scripts/p31_6_status_report.py added.
  Current report:
    P31_6_READINESS_STATUS_20260703.md/json
  Summary:
    p32_entry_ready = False
    machine_gate = FAIL
    manual_gate = FAIL
    critique_payload_verified_cluster_count = 2
    manual_A_B_clusters = 2
    api_preflight = failed, 402 insufficient_balance
    latest refresh = 20260703_022822
  Next action from report:
    Restore MiMo account balance/key, then run:
      scripts/p31_6_full20_pipeline.sh --launch --wait --update-latest

Current structured manual audit:
  manual_A_clusters = 0
  manual_B_clusters = 2
  manual_A_B_clusters = 2
  manual_D_clusters = 0
  unfilled_clusters = 0
  status = FAIL because manual_A_B_clusters < 3

This confirms the old raw has two defensible B-level Critique-origin clusters
but remains below the P32 entry threshold.
Latest lightweight MiMo API check at 20260703_020340 still returned
402 insufficient_balance, so fresh full20 remains pending.
Latest lightweight MiMo API check at 20260703_020928 still returned
402 insufficient_balance, so fresh full20 remains pending.
```

P31.7/P31.8 current status:

```text
Latest authoritative fresh full20:
  P31_6_FRESH_20260703_231747_*
  verified_review_issue_count = 16
  verified_review_issue_cluster_count = 11
  critique_payload_verified_cluster_count = 0
  candidate_menu_item_verified_count = 0
  review_issue_candidate_critique_payload_count = 3
  review_issue_candidate_deterministic_seed_count = 56
  mark_contested_commit_count = 9
  protection = PASS
  machine_gate = FAIL
  manual_gate = REQUIRED

P31.7 conclusion:
  Audit/cluster consistency succeeded.
  Critique autonomous discovery failed.
  P32 remains blocked.

P31.8 implemented local code patch:
  - selector menu prioritizes verifier-survival rank instead of forced slot diversity
  - visible selector menu reduced to 6 items / max 2 per issue type
  - efficiency/resource menu items hidden when inventory already contains resource evidence
  - selected-menu candidates carry a normalized menu snapshot for same-id/same-claim/same-type verifier recovery
  - Critique instruction changed from select 1-3 to select 1-2 safe menu ids
  - DRMAS_CRITIQUE_DISCOVERY_FIRST added; DRMAS_CRITIQUE_ONLY_DISCOVERY_EVAL=1 enables it
  - pending_absence_audit / pending_issue_bundle_verification now count as pending reviewer candidates
  - recovery/conflict/sticky/support overrides no longer overwrite an already scheduled review_issue_discovery_required turn
  - P31_8_CRITIQUE_SELECTION_CLOSED_LOOP_PLAN_ZH_20260703.md added

Validation:
  py_compile state/runner/prompts/policy/test file = PASS
  lightweight smoke assertions for P31.8 selector/snapshot logic = PASS
  pytest unavailable in current Python environments because pytest is not installed

Critique-only smoke results:
  P31_8_CRITONLY1_20260704_000010:
    rows = 1
    verified_review_issue_count = 2
    cluster_count = 2
    critique_payload_verified_cluster_count = 0
    candidate_menu_item_verified_count = 0
    finding = discovery flag survived only inside recovery override; selector menu absent
  P31_8_CRITONLY1_20260704_000542:
    rows = 1
    verified_review_issue_count = 2
    cluster_count = 1
    critique_payload_verified_cluster_count = 0
    candidate_menu_item_verified_count = 0
    finding = discovery did not fire; negative formation/recovery consumed turn budget
  P31_8_CRITONLY1_20260704_001006:
    rows = 1
    verified_review_issue_count = 2
    cluster_count = 2
    critique_payload_verified_cluster_count = 0
    candidate_menu_item_verified_count = 0
    finding = discovery-first ran Critique earlier, but early binding/conflict recovery still prevented clean selector lifecycle

Next action:
  Do not run full20 or enter P32.
  Next code pass should add an explicit review_issue_discovery phase/turn reservation so Critique gets a clean selector-discovery turn before negative binding / recovery routes can consume the budget.
```

P31.8 attribution fix update (20260704):

```text
Completed:
  - Fixed final-view attribution for selected-menu Critique candidates that
    match an already verified deterministic-seed review-issue cluster.
  - The fix is read-only accounting: no verifier relaxation, no duplicate
    evidence, and no stale/hallucinated id recovery without a prompt-time menu
    snapshot.
  - Dashboard and case-table scripts now surface the selected-menu attribution,
    and entry-gate audit counts those clusters as Critique-origin for the
    machine gate.

Current full20 recompute from existing raw:
  P31_8_ATTRFIX_FULL20_20260704_115546_*
  verified_review_issue_count = 22
  verified_review_issue_cluster_count = 15
  critique_payload_verified_cluster_count = 7
  candidate_menu_item_verified_count = 8
  candidate_menu_item_verified_by_existing_cluster_count = 7
  mark_contested_commit_count = 9
  protection = PASS
  machine gate = PASS
  manual gate = REQUIRED

Generated:
  P31_8_ATTRFIX_FULL20_20260704_115546_HARDNEG20_DASHBOARD.md/json
  P31_8_ATTRFIX_FULL20_20260704_115546_REVIEW_ISSUE_CASE_TABLE.md/json
  P31_8_ATTRFIX_FULL20_20260704_115546_RECOVERY_CASE_TABLE.md/json
  P31_8_ATTRFIX_FULL20_20260704_115546_ENTRY_GATE_AUDIT.md/json
  P31_8_ATTRFIX_FULL20_20260704_115546_MANUAL_AUDIT_TEMPLATE.md/json

Remaining blocker:
  P32 is still blocked until the manual audit template is filled and validates
  with enough A/B Critique-origin clusters and zero paper-facing D clusters.
  Do not claim paper-ready Critique autonomous discovery until that manual gate
  passes.

Manual audit draft result:
  P31_8_ATTRFIX_FULL20_20260704_115546_MANUAL_AUDIT_FILLED_DRAFT.json
  A clusters = 3
  B clusters = 3
  A/B Critique-origin clusters = 6
  D clusters = 1
  strict validation = FAIL because manual_D_clusters = 1
  allow-D validation = PASS only if the D cluster is excluded from paper-facing
  reporting.

Actionable next step:
  Add a guard/counterevidence rule for TPAj63ax4Y-style missing_ablation
  candidates where the paper explicitly states that it performs ablations over
  the selected stage/pipeline.  Then recompute full20 and expect the D cluster
  to disappear while preserving the 6 A/B clusters.

Guard follow-up completed:
  - Added zero-shot-choice / selected-stage ablation counterevidence guard.
  - Recomputed:
      P31_8_ATTRFIX_GUARD_FULL20_20260704_115546_*
  - verified_review_issue_count = 22
  - verified_review_issue_cluster_count = 14
  - critique_payload_verified_cluster_count = 6
  - candidate_menu_item_verified_count = 7
  - protection = PASS
  - manual_A_B_clusters = 6
  - manual_D_clusters = 0
  - entry gate with manual audit = PASS

Next:
  Treat P31_8_ATTRFIX_GUARD_FULL20_20260704_115546 as the current P32-entry
  candidate, with the caveat that it is a current-code recompute over an
  existing full20 raw run.  A fresh API full20 can be run later for final
  confirmation, but do not reopen verifier relaxation.
```

P31.12 current task update (20260705):

```text
Current priority:
  AGENTS.md makes evidence JSON reliability the P0 gate.  Existing fresh full20
  and sample3 dashboards show evidence_json_fallback_rate_pct=0, but the
  requested DRMAS_JSON_RESPONSE_FORMAT on/off live A/B could not be completed
  because the current MiMo key returned 401 authentication failure.

Completed offline:
  - Audited sample3 selected-menu failures.
  - Fixed funnel telemetry so a selected menu candidate with a valid copied
    review_issue_candidate_menu_item snapshot is not mislabeled as
    selected_menu_item_not_in_current_menu_or_filtered merely because the
    current recomputed menu is empty.
  - Preserved merged candidate_menu_ids / reviewer_negative_candidate_ids in
    review-issue gap metadata, so bundle failure telemetry is attributed to
    every selected menu id merged into the same gap.
  - Recomputed sample3 artifacts:
      P31_12_SAMPLE3_MENU_FAILURE_RECOMPUTE_20260705_120426_*

Sample3 telemetry after fix:
  candidate_menu_item_failed_selected_menu_item_not_in_current_menu_or_filtered = 0
  candidate_menu_item_failed_by_reason =
    missing_entity_already_observed_in_inventory: 2
    generic_item: 1
    full_text_evaluation_or_scope_counterevidence: 1
    not_verified_by_bundle: 1

Validation:
  focused hygiene/gate selector suite = 12 passed
  runner selected-menu/discovery suite = 18 passed
  py_compile state.py/test_review_decision_hygiene.py = PASS
  broader 3-file suite = 767 passed / 30 failed

Next:
  1. With a valid MiMo key, rerun the DRMAS_JSON_RESPONSE_FORMAT on/off sample
     A/B before claiming the P0 is freshly validated.
  2. Then improve Critique selector/menu supply quality based on the now-real
     failure mix: already-observed, generic target, full-text counterevidence,
     and not-materialized bundle candidates.
  3. Do not loosen verifier/validator gates and do not enter P32 until the
     fresh hardneg20 gate is satisfied.

Follow-up:
  - MiMo key in .env is valid; the earlier 401 came from running without
    sourcing .env and falling through to OPENAI_API_KEY.
  - DRMAS_JSON_RESPONSE_FORMAT=on sample3 completed:
      run = p31_12_jsonfmt_on_sample3_20260705_121250
      rows = 3
      evidence_json_valid_turns = 10
      evidence_json_fallback_turns = 0
      evidence_json_fallback_rate_pct = 0
      evidence_json_no_json_object_turns = 0
  - DRMAS_JSON_RESPONSE_FORMAT=off sample3 could not complete because MiMo
    returned 402 insufficient account balance after multiple calls; output
    jsonl has 0 rows.
  - P0 is partially revalidated for response_format=on, but the requested live
    on/off A/B remains incomplete until account balance is restored.

Final A/B after balance top-up:
  - DRMAS_JSON_RESPONSE_FORMAT=off completed:
      run = p31_12_jsonfmt_off_sample3_20260705_123405
      rows = 3
      evidence_json_valid_turns = 2
      evidence_json_fallback_turns = 10
      evidence_json_fallback_rate_pct = 83
      evidence_json_no_json_object_turns = 0
  - Direct comparison:
      on:  evidence_json_fallback_rate_pct = 0   (10 valid / 0 fallback)
      off: evidence_json_fallback_rate_pct = 83  (2 valid / 10 fallback)
  - Conclusion: P0 is validated.  Keep response_format=json_object enabled
    for MiMo; downstream selector/menu work can continue only under the
    response-format-on/auto path.
```

P31.13 long-horizon stage checkpoint (20260705):

```text
Current project stage:
  Stage 1 / ReviewState credibility is mostly closed for the current path:
  response_format=on is validated, hard contamination is 0, positive/neutral
  active negative candidates are 0, and the menu quality guards removed the
  unsafe direct=2 false positives from the fresh raw recompute.

Stage 2 / real Critique-discovered negatives is now the active work:
  A 3-paper response-format-on API sample over paper-named-baseline candidates
  completed:
    run = p31_13_paper_named_menu_sample3_20260705_144239
    rows = 3
    evidence_json_fallback_rate_pct = 0
    protection = PASS
    critique_direct_verified_cluster_count = 1
    candidate_menu_item_used_count = 3
    candidate_menu_item_verified_count = 1

Important caveat:
  The one verified direct cluster was selected-menu/critique-origin, but it was
  an existing runner/obligation menu item:
    YXn76HMetm / coverage or held-out evaluation for RIPU
  The new paper-named baseline menu supply has not yet been selected and
  verified in a live API run.

Next major direction:
  Make menu supply and selector attention work together so Critique reliably
  selects concrete verifier-survivable candidates.  Then run a fresh hardneg20
  and only advance if direct Critique clusters pass with manual audit quality.
  Keep verifier/validator strict; do not count seed-origin or external-template
  targets as Critique discovery.
```

P31.15 current Stage 2 task update (20260705):

```text
Completed in this step:
  - Paper-named baseline menu supply now survives the live-state failure modes:
      best-results claims with baseline obligations;
      SOTA/improves/outperforms/all-baselines result anchors;
      unbound full-paper comparison inventory when claim-bound inventory is
      absent, while skipping inventory explicitly bound to another claim.
  - Selected-menu attribution now outranks deterministic seed shadowing:
      selected Critique menu records can update earlier absence-audit seed
      evidence with the same evidence_id;
      lower-priority seed records cannot overwrite selected records;
      duplicate review-issue representative selection prefers Critique origin.

Validation:
  focused hygiene/menu suite = 39 passed
  runner selected-menu/discovery suite = 20 passed
  hygiene/gate focused suite = 20 passed
  py_compile relevant files = PASS

Live sample findings:
  p31_14 showed the bug: EqualAL was selected and verifier-survivable but
  attributed to deterministic_paper_named_baseline_seed.  Current-code rebuild
  gives direct Critique = 1 for that raw.
  p31_15 was a fresh live run after the attribution fix.  Protection stayed
  clean, but candidate_menu_item_used_count=0: HPu had a visible GPT-4 menu
  snapshot that Critique did not select, and YXn had current-code menu supply
  but no runtime selector snapshot.

Next major direction:
  Do not run full20 yet.  Make manager trigger / selector attention reliable:
  when verifier-ready menu items exist, a review-issue discovery turn should be
  triggered and Critique should select/reject visible items explicitly.  Keep
  all bundle verifier and hygiene gates strict.
```

P31.16 current Stage 2 task update (20260705):

```text
Completed in this step:
  - Manager selector availability now matches the prompt-scale selector budget
    (`max_items=12`, `max_per_claim=3`, `max_per_type=4`).
  - Empty-menu review-issue selector discovery is blocked at manager routing:
    with review_issue_bundle enabled and no visible selector menu, hard-negative
    discovery falls back to Evidence targeted negative search.
  - Runner adds an empty-snapshot guard: stale
    review_issue_discovery_required turns are downgraded before building the
    Critique prompt, so Critique is not asked to select from a non-existent menu.

Validation:
  targeted runner/manager selector tests = 5 passed
  runner selector/discovery focused suite = 21 passed
  hygiene/gate focused suite = 21 passed
  py_compile review_manager_policy.py/review_runner.py/test_review_inference_runner.py = PASS

Live sample:
  run = p31_16_trigger_menu_sample3_20260705_155155
  input = p31_16_trigger_sample3_input.parquet
  papers = HPuLU6q7xq, QAgwFiIY4p, YXn76HMetm
  env = DRMAS_JSON_RESPONSE_FORMAT=on, qhyg=1, targetneg=1,
        freeformrevneg=1, reviewissuebundle=1, max_tokens=2048

Sample metrics:
  evidence_json_valid_turns = 11
  evidence_json_fallback_turns = 0
  evidence_json_fallback_rate_pct = 0
  protection = PASS
  verified_review_issue_cluster_count = 3
  critique_payload_verified_cluster_count = 1
  critique_direct_verified_cluster_count = 1
  critique_selected_existing_seed_cluster_count = 0
  candidate_menu_item_count = 2
  candidate_menu_item_used_count = 2
  candidate_menu_item_verified_count = 1
  candidate_menu_item_failed_count = 1
  state_contamination_count = 0
  positive_or_neutral_negative_candidate_count = 0
  negative_evidence_unlinked_to_flaw = 0
  negative_grounding_conflict_count = 0

Trace findings:
  - YXn76HMetm: selector snapshot count 3; Critique selected EqualAL;
    final case table has missing_baseline/equalal_baseline with
    discovery_origin=critique_payload_menu_selected.
  - QAgwFiIY4p: selector snapshot count 1; Critique selected Graphormer, but
    bundle verifier rejected it as missing_baseline_target_generic_or_truncated.
  - HPuLU6q7xq: no selector discovery in this stochastic sample; it followed
    negative binding / recovery routing, though the final state can generate
    two insufficient-evaluation menu items.

Next:
  1. Fix paper-named baseline target quality for Graphormer-style candidates
     without reopening generic external-family false positives.
  2. Stabilize discovery trigger timing so menu-bearing states are not consumed
     by negative binding/recovery routes before Critique gets a selector pass.
  3. After another sample shows at least two verifier-surviving selected menu
     clusters with clean protection, run a fresh hardneg20; do not run full20
     from the current sample alone.
```

P31.29/P31.30 Stage 2->3 bridge-guard checkpoint (20260705):

```text
Problem found:
  P31.29 fresh 5-paper sample exposed a regression introduced by the new
  support-recheck bridge.  The bridge improved recovery safety but fired before
  Critique review-issue discovery had a real chance to run.

P31.29 metrics:
  run = p31_29_stage3_support_bridge_critique5_20260705_191746
  machine gate = FAIL
  protection = FAIL only because empirical_real_strong_support_count = 2 < 3
  critique_direct_verified_cluster_count = 1
  candidate_menu_item_count = 1
  candidate_menu_item_verified_count = 1
  mark_contested_commit_count = 3
  verified_issue_cluster_without_recovery_count = 5
  state_contamination_count = 0
  recovery_no_effect_commit = 0
  recovery_harmful_commit_risk = 0

Fix:
  - Added a shared `_review_issue_discovery_untried_for_recovery_bridge`
    predicate.
  - Both finalize-policy and fallback-policy recovery/support bridges now wait
    until Critique review-issue discovery has been attempted when targeted
    reviewer-negative discovery is enabled.
  - This keeps the order functional: Critique discovery first, then support
    recheck / contested recovery.

Validation:
  - bridge/discovery focused pytest = 9 passed
  - support-bridge regression pytest = 4 passed
  - py_compile review_manager_policy.py and test_review_inference_runner.py =
    PASS

Fresh sample after fix:
  run = p31_30_bridge_guard_critique5_20260705_193123
  rows = 5
  machine gate = PASS
  manual gate = PASS after critique-only manual audit validation
  protection = PASS
  critique_direct_verified_cluster_count = 4
  candidate_menu_item_count = 7
  candidate_menu_item_used_count = 5
  candidate_menu_item_verified_count = 4
  candidate_menu_item_failed_count = 1
  empirical_real_strong_support_count = 6
  verified_review_issue_cluster_count = 5
  mark_contested_commit_count = 5
  verified_issue_cluster_without_recovery_count = 1
  state_contamination_count = 0
  positive_or_neutral_negative_candidate_count = 0
  negative_evidence_unlinked_to_flaw = 0
  negative_grounding_conflict_count = 0
  recovery_no_effect_commit = 0
  recovery_harmful_commit_risk = 0

Manual audit:
  file = P31_30_BRIDGE_GUARD_CRITIQUE5_ONLY_MANUAL_AUDIT_20260705_193123.json
  validation = P31_30_BRIDGE_GUARD_CRITIQUE5_ONLY_MANUAL_AUDIT_VALIDATION_20260705_193123.json
  critique_origin_clusters = 4
  manual_A_B_clusters = 4
  manual_D_clusters = 0
  labels:
    GE6iywJtsV / consisting_constrain_module = B
    NnExMNiTHw / acceptance_prediction_head = B
    QAgwFiIY4p / paper-named_graphormer_baseline = B
    YXn76HMetm / paper-named_pixelpick_baseline = B

Interpretation:
  P31.30 is the first post-bridge sample where the full small-sample path is
  live at once: Critique selected concrete menu candidates, the strict bundle
  verifier accepted four direct Critique-origin clusters, and recovery converted
  verified issues into audited mark_contested repairs without state hygiene
  regressions.  This is still only a 5-paper checkpoint.  Next step is a fresh
  hardneg20 before claiming Stage 2/3 stability or moving toward full39/P32.
```
