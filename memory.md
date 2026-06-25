# Memory - DrMAS Paper Review (Compact)

Last compacted: 2026-06-25.

This file is the working memory for the paper-review project. Keep it short. Move detailed historical narratives into separate audit/checkpoint docs instead of expanding this file.

## Current Objective

Build a structured, evidence-grounded, auditable, recoverable paper-review assistant.

The current research story is not "maximize PASS" or "increase negative count at any cost". The core goal is:

- find real paper-side review issues;
- ground verified negative evidence in paper quotes + locators;
- preserve positive support when it is real;
- keep conflicts visible through non-destructive recovery;
- separate diagnostic/potential concerns from quote-grounded verified negatives.

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

Missing-baseline, missing-ablation, insufficient-evaluation, and reproducibility gaps are often absence/coverage judgments. They may become `diagnosis_pending_potential_concern`, but they must not be counted as `verified_actionable_negative_flaw` unless Evidence Agent finds a real paper quote/locator and the verifier accepts it.

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
--max-tokens 768
--max-turns 7
--manager-batch-size 4
--api-timeout 600
--api-max-retries 10
```

For smoke8, `--api-max-workers 2` is safer. For hardneg20/full39, larger workers can be tried after confirming the endpoint is stable.

## Latest State: 2026-06-25

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
  --max-tokens 768 \
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
