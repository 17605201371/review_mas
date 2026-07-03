# P31.6 Critique-Origin Status 2026-07-03

## Scope

P31.6 continues P31.5.  It is not a P32 entry checkpoint yet.

Goal: recover at least one more A/B-quality Critique-origin verified review-issue
cluster without relaxing the verifier, then enter P32 only after a fresh full20
run passes protection and manual quality audit.

Operational runbook:

```text
P31_6_FRESH_FULL20_RUNBOOK_20260703.md
```

## Code Changes

- Missing-ablation counterevidence now requires real ablation/comparison/result
  context for plain `without` language.  Method prose such as `without needing
  eigendecomposition` no longer resolves a missing-ablation issue by itself.
- Critique missing-ablation candidates may use locatable full-text component
  anchors before entering the unchanged strict bundle verifier.
- Reviewer-candidate missing targets stay primary over coarse automatic
  claim-obligation targets.
- `REVIEW_ISSUE_DISCOVERY_PROMPT` now treats the selector menu as the primary
  discovery channel and requires selected menu ids to be mirrored in
  `selected_menu_items`.
- `ApiReviewGenerator` fast-fails non-retryable API errors such as
  `402 insufficient_balance`, quota/billing, invalid key, authentication, and
  permission failures.
- `run_hardneg20_guard3.sh` now performs a one-call MiMo API preflight before
  creating run artifacts or launching a background full20 job.  Set
  `DRMAS_API_PREFLIGHT=0` only for manual debugging.
- The preflight now reports non-retryable failures as a concise one-line
  failure instead of printing a full Python traceback.

## Validation

```text
tests/test_review_decision_hygiene.py P31/P31.5 focused set = 21 passed
tests/test_review_inference_runner.py P31/API focused set = 8 passed
tests/test_review_inference_runner.py prompt/recovery focused set = 6 passed
tests/test_p31_6_gate_scripts.py = 5 passed
py_compile = passed
bash -n run_hardneg20_guard3.sh = passed
bash -n scripts/p31_6_generate_full20_artifacts.sh = passed
```

## Artifact Script

Helper:

```text
scripts/p31_6_generate_full20_artifacts.sh
scripts/p31_6_entry_gate_audit.py
scripts/p31_6_manual_audit.py
scripts/p31_6_full20_pipeline.sh
scripts/p31_6_status_report.py
```

Purpose:

- Generate the P31.6 dashboard, review issue case table, and recovery case table
  from a completed full20 `.jsonl`.
- Refuse partial/empty runs by default (`--min-lines 20`).
- Optionally update `.latest_hardneg20_*` pointers after successful generation
  with `--update-latest`.
- Generate an entry-gate audit report that checks the machine P32-entry
  requirements and lists Critique-origin clusters for manual A/B audit.
- Generate and validate a structured manual A/B audit for Critique-origin
  clusters.  The entry-gate script can optionally consume the validation JSON
  via `--manual-audit-validation-json`; use `--require-manual-audit` when making
  a P32-entry decision.
- `scripts/p31_6_generate_full20_artifacts.sh` now generates a fillable
  `*_MANUAL_AUDIT_TEMPLATE.md/json` by default after the entry-gate report.
  Use `--skip-manual-template` only when a template is not wanted.
- `scripts/p31_6_full20_pipeline.sh` wraps the standard fresh full20 workflow:
  launch with P31.6 flags, optionally wait for completion, and postprocess into
  dashboard/case/recovery/entry-gate/manual-template artifacts.
- `scripts/p31_6_status_report.py` summarizes the current P31.6 readiness
  state: latest run rows/running status, entry-gate status, manual-audit status,
  optional MiMo API preflight, and the next recommended command.

Validated commands:

```bash
scripts/p31_6_generate_full20_artifacts.sh \
  --input P31_5_TARGETQUALITY_FULL20_163953_UNCACHED.jsonl \
  --label P31_6_SCRIPT_DRYRUN_163953 \
  --dry-run

scripts/p31_6_generate_full20_artifacts.sh \
  --input P31_5_TARGETQUALITY_FULL20_163953_UNCACHED.jsonl \
  --label P31_6_SCRIPT_CHECK_163953
```

The real generation completed successfully and reproduced the authoritative
P31.6 metrics exactly.  It took about 8 minutes 20 seconds on the existing
full20 raw, with most time spent in dashboard recomputation.  The temporary
`P31_6_SCRIPT_CHECK_163953_*` validation outputs were removed after comparison.

Entry-gate audit artifact:

```text
P31_6_CRITORIGIN_RECOMPUTE_163953_ENTRY_GATE_AUDIT.md/json
```

Current machine gate:

```text
status = FAIL
reason = critique_payload_verified_cluster_count = 2 < 3
case_table_critique_origin_cluster_count = 2 < 3
protection = PASS
red_flag_scan = 0 simple lexical red flags
manual_gate = REQUIRED
```

The two current Critique-origin clusters listed for manual audit are:

```text
GE6iywJtsV / missing_robustness_or_generalization / cross-target_validation
YXn76HMetm / reproducibility_gap / hyperbolic_curvature
```

`scripts/p31_6_generate_full20_artifacts.sh` now includes this gate report by
default.  A failed entry gate still allows artifacts to be generated; pass
`--fail-entry-gate` when the desired behavior is to abort on gate failure.

Default fresh full20 post-processing now produces:

```text
*_HARDNEG20_DASHBOARD.md/json/audit.json
*_REVIEW_ISSUE_CASE_TABLE.md/json
*_RECOVERY_CASE_TABLE.md/json
*_ENTRY_GATE_AUDIT.md/json
*_MANUAL_AUDIT_TEMPLATE.md/json
*_READINESS_STATUS.md/json
```

One-command fresh run path after MiMo balance is usable:

```bash
scripts/p31_6_full20_pipeline.sh --launch --wait --update-latest
```

Equivalent manual path:

```bash
DRMAS_NEG_QUOTE_HYGIENE=1 \
DRMAS_TARGETED_NEGATIVE_SEARCH=1 \
DRMAS_FREEFORM_REVIEWER_NEGATIVE=1 \
DRMAS_REVIEW_ISSUE_BUNDLE=1 \
API_MAX_WORKERS=4 \
API_MAX_RETRIES=8 \
API_TIMEOUT=600 \
MAX_TOKENS=1536 \
bash run_hardneg20_guard3.sh
```

After the manual template is filled, run:

```bash
scripts/p31_6_manual_audit.py validate \
  --audit-json <LABEL>_MANUAL_AUDIT.json \
  --output-json <LABEL>_MANUAL_AUDIT_VALIDATION.json \
  --output-md <LABEL>_MANUAL_AUDIT_VALIDATION.md

scripts/p31_6_entry_gate_audit.py \
  --dashboard-json <LABEL>_HARDNEG20_DASHBOARD.json \
  --case-json <LABEL>_REVIEW_ISSUE_CASE_TABLE.json \
  --recovery-json <LABEL>_RECOVERY_CASE_TABLE.json \
  --manual-audit-validation-json <LABEL>_MANUAL_AUDIT_VALIDATION.json \
  --require-manual-audit
```

Manual audit artifacts for the current old-raw recompute:

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

Interpretation: the two current Critique-origin clusters remain defensible
B-level concerns, but the old raw still cannot enter P32 because it has only
two A/B Critique-origin clusters.

## Fresh Full20 With Updated MiMo Key

The local MiMo credentials were updated and API preflight succeeded.  A fresh
P31.6 full20 completed with `API_MAX_WORKERS=4`, `MAX_TOKENS=1536`,
`API_MAX_RETRIES=8`, and `API_TIMEOUT=600`.

Fresh run:

```text
mimo_v25_negqty_recoverycap_guard3_qhyg_targetneg_freeformrevneg_reviewissuebundle_hardneg20_mt7_b4w2_api4_r8t600_tok1536_20260703_082133.jsonl
```

Artifacts:

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
verified_review_issue_count = 14
verified_review_issue_cluster_count = 12
quote_duplicate_merged_verified_review_issue_cluster_count = 12
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
review_negative_verified_count = 0
```

Fresh entry gate:

```text
machine_gate = FAIL
manual_gate = REQUIRED
critique_payload_verified_cluster_count = 1 < 3
case_table_critique_origin_cluster_count = 1 < 3
```

The only fresh Critique-origin cluster listed for manual audit is:

```text
GE6iywJtsV / reproducibility_gap / implementation_reproducibility_details
```

Interpretation:

- Fresh execution is clean on protection and JSON reliability.
- It is worse than the old-raw/current-code recompute for the P31.6 gate:
  Critique-origin verified clusters dropped from 2 to 1.
- Verified issue quantity remains mostly deterministic-seed driven:
  10 missing-ablation clusters and 2 reproducibility clusters.
- P32 remains blocked.  This fresh run must not be treated as a paper-ready
  P31.6 success.

## Follow-up Audit After Fresh Failure

Fresh failure is not caused by API or JSON reliability:

```text
evidence_json_fallback_rate_pct = 0
protection = PASS
```

The failure is in Critique-origin discovery/materialization:

```text
review_issue_candidate_critique_payload_count = 15
critique_payload_menu_bound_count = 4
critique_payload_bundle_built_count = 1
critique_payload_verified_cluster_count = 1
```

Paper-level findings:

- `YXn76HMetm`: Claim Agent fell back to `claim-paper-context-*` claims after
  empty/malformed claim extraction.  The manager never set
  `review_issue_discovery_required`, so no review issue menu or
  reviewer-negative candidates were produced.  This explains why the old
  YXn Critique-origin B cluster disappeared in fresh execution.
- `KOUAayk5Kx`: Critique produced an OGL missing-ablation candidate, but it was
  not verified.  A narrow code fix now recognizes
  `ablation on orthogonality constraint` as a concrete missing-ablation target
  and gives it a reviewer-candidate mechanism/claim relevance basis.  After
  uncached recompute, the candidate correctly fails at
  `observed_inventory_missing` because the provided anchor is only a qualitative
  Figure 3 cell diagram, not an ablation/variant/removal/list/table inventory
  anchor.  Do not force this candidate through.
- `GE6iywJtsV`: Two menu ids were selected; one reproducibility menu item
  verified, while the train/test split protocol item remained
  `not_verified_by_bundle`.
- Fresh Critique also selected non-review menu ids such as `rim-evidence-*` in
  some papers.  The prompt/observation rules now explicitly forbid selecting
  evidence ids, quote ids, claim ids, or invented ids as `selected_menu_items`.

Code/test follow-up:

```text
state.py: missing-ablation specificity now checks normalized target text and accepts contribution-bound orthogonality/regularization targets.
state.py: reviewer-candidate ablation relevance can bind a named mechanism candidate to a claim when both mention the same paper-specific method/acronym and the candidate describes a core mechanism.
review_prompts.py/state.py prompt rules: selected_menu_items must copy review-issue candidate menu ids, normally rim-c*, and must not use rim-evidence ids.
tests: focused P31.6 regressions passed (5 decision-hygiene tests, 3 inference/prompt tests).
```

Current interpretation remains unchanged:

```text
P32 blocked.
Do not relax verifier.
Next real work is robust real-claim extraction / review-issue discovery triggering for papers like YXn, plus better telemetry for menu candidates that fail before bundle verification.
```

## Offline Current-Code Recompute

Input raw:

```text
P31_5_TARGETQUALITY_FULL20_163953_UNCACHED.jsonl
```

Generated artifacts:

```text
P31_6_CRITORIGIN_RECOMPUTE_163953_HARDNEG20_DASHBOARD.md/json/audit.json
P31_6_CRITORIGIN_RECOMPUTE_163953_REVIEW_ISSUE_CASE_TABLE.md/json
P31_6_CRITORIGIN_RECOMPUTE_163953_RECOVERY_CASE_TABLE.md/json
```

Headline metrics:

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
recovery_case_verified_review_issue_repair = 5
verified_issue_cluster_without_recovery_count = 10
protection = PASS
```

Interpretation:

- Old-raw recompute still fails the P32 entry gate because
  `critique_payload_verified_cluster_count = 2`, below the required `>= 3`.
- The released extra verified rows are deterministic-seed rows, not a new
  Critique-origin cluster.
- KOUA OGL remains correctly rejected because the paper contains explicit
  `methods with or without OGL` results.
- xUe FlyingThings3D and ye3 HMDB/SSv2 candidates remain rejected for good
  reasons: training-set/held-out confusion and full-text evaluation coverage.

## Fresh Run Attempt

Attempted run:

```text
mimo_v25_negqty_recoverycap_guard3_qhyg_targetneg_freeformrevneg_reviewissuebundle_hardneg20_mt7_b4w2_api4_r8t600_tok1536_20260703_011822
```

Status:

```text
jsonl_lines = 0
status = stopped
reason = MiMo API returned 402 insufficient_balance before any paper completed
```

Do not use this as a partial/full20 result.

Latest preflight retry:

```text
attempt = 20260703_014718
result = fast-fail 402 insufficient_balance
new run artifacts = none
traceback = suppressed
```

Latest lightweight API check:

```text
attempt = 20260703_015444
result = 402 insufficient_balance
fresh full20 started = no
```

Latest lightweight API check:

```text
attempt = 20260703_020340
result = 402 insufficient_balance
fresh full20 started = no
```

Latest lightweight API check:

```text
attempt = 20260703_020928
result = 402 insufficient_balance
fresh full20 started = no
```

Latest pipeline launch check:

```text
attempt = 20260703_021333
command = scripts/p31_6_full20_pipeline.sh --launch --no-postprocess
result = fast-fail 402 insufficient_balance
new run artifacts = none
```

Latest readiness refresh:

```text
attempt = 20260703_022439
api_preflight = failed, 402 insufficient_balance
p32_entry_ready = False
```

Latest readiness refresh:

```text
attempt = 20260703_022822
api_preflight = failed, 402 insufficient_balance
p32_entry_ready = False
```

Readiness report:

```text
P31_6_READINESS_STATUS_20260703.md/json
```

Current readiness summary:

```text
p32_entry_ready = False
machine_gate = FAIL
manual_gate = FAIL
critique_payload_verified_cluster_count = 2
manual_A_B_clusters = 2
api_preflight = failed, 402 insufficient_balance
next_action = restore MiMo balance/key, then run scripts/p31_6_full20_pipeline.sh --launch --wait --update-latest
```

## Next Fresh Full20 Command

Run only after the active MiMo key/account has usable balance:

```bash
set -a
source .env
set +a
DRMAS_NEG_QUOTE_HYGIENE=1 \
DRMAS_TARGETED_NEGATIVE_SEARCH=1 \
DRMAS_FREEFORM_REVIEWER_NEGATIVE=1 \
DRMAS_REVIEW_ISSUE_BUNDLE=1 \
API_MAX_WORKERS=4 \
API_MAX_RETRIES=8 \
API_TIMEOUT=600 \
MAX_TOKENS=1536 \
bash run_hardneg20_guard3.sh
```

The script will run the preflight first.  If the key still lacks balance, it
should exit before creating new run artifacts.

## P32 Entry Gate

Proceed to P32 only if the fresh full20 result satisfies:

```text
critique_payload_verified_cluster_count >= 3
protection = PASS
negative_evidence_unlinked_to_flaw = 0
positive_or_neutral_negative_candidate_count = 0
negative_grounding_conflict_count = 0
manual A/B quality does not regress
no external-baseline, retrieval/context, or author-limitation false positives
```
