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

There are deliberately separate lanes. Keep them separate in code, metrics, dashboards, and paper narrative.

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

## Paper Narrative Blueprint (2026-07-01)

New paper-facing blueprint: `PAPER_NARRATIVE_BLUEPRINT_20260701.md`.

Core thesis:

- Do not sell DrMAS as a better free-form review generator or accept/reject classifier.
- Sell it as ReviewState maintenance: claims, evidence, reviewer issues, conflicts, final-view hygiene, and non-destructive recovery.
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
