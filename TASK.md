# TASK.md

## Current Task: P31 ReviewState Lifecycle / Critique Selector Integration

Authoritative roadmap: `P31_REVIEWSTATE_LIFECYCLE_ROADMAP_20260701.md`.

Goal:

- Make ReviewState-centered review issue discovery, bundle verification, clustering, manual audit, and non-destructive recovery stable enough for the paper narrative.
- Improve Critique payload integration without relaxing the verifier.
- Keep direct quote-grounded negative evidence strict; optimize obligation-grounded verified review issue bundles and safe `mark_contested` recovery.

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
