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

### 2026-06-27 CANDPRIORITY1 hardneg20 checkpoint (latest)

Run and artifacts:

- run: `mimo_v25_negqty_recoverycap_guard3_qhyg_targetneg_freeformrevneg_reviewissuebundle_hardneg20_mt7_b4w2_api2_r8t600_tok1536_20260627_113021.jsonl`
- log: `mimo_v25_negqty_recoverycap_guard3_qhyg_targetneg_freeformrevneg_reviewissuebundle_hardneg20_mt7_b4w2_api2_r8t600_tok1536_20260627_113021.log`
- dashboard: `mimo_v25_negqty_recoverycap_guard3_qhyg_targetneg_freeformrevneg_reviewissuebundle_hardneg20_mt7_b4w2_api2_r8t600_tok1536_20260627_113021_CANDPRIORITY1_RECOMPUTE_VS_101215_DASHBOARD.md`
- review issue cases: `mimo_v25_negqty_recoverycap_guard3_qhyg_targetneg_freeformrevneg_reviewissuebundle_hardneg20_mt7_b4w2_api2_r8t600_tok1536_20260627_113021_CANDPRIORITY1_RECOMPUTE_REVIEW_ISSUE_CASES.md`
- recovery cases: `mimo_v25_negqty_recoverycap_guard3_qhyg_targetneg_freeformrevneg_reviewissuebundle_hardneg20_mt7_b4w2_api2_r8t600_tok1536_20260627_113021_CANDPRIORITY1_RECOMPUTE_RECOVERY_CASE.md`

Run settings:

- `DRMAS_NEG_QUOTE_HYGIENE=1`
- `DRMAS_TARGETED_NEGATIVE_SEARCH=1`
- `DRMAS_FREEFORM_REVIEWER_NEGATIVE=1`
- `DRMAS_REVIEW_ISSUE_BUNDLE=1`
- `max_turns=7`, `max_tokens=1536`, `API_MAX_WORKERS=2`, `API_MAX_RETRIES=8`, `API_TIMEOUT=600`

Key metrics after recomputing with CANDPRIORITY1:

- protection PASS
- `real_strong_support_total=71`
- strict quote lane: `review_negative_verified_count=1`
- issue-bundle lane: `verified_review_issue_count=8`
- `quote_grounded_review_issue_count=1`
- `obligation_grounded_review_issue_count=7`
- `reviewer_candidate_review_issue_count=3`
- `claim_obligation_review_issue_count=4`
- `total_review_negative_verified_count=8`
- `negative_evidence_candidate_count=8`
- `negative_evidence_linked_to_flaw_count=8`
- `negative_evidence_unlinked_to_flaw=0`
- `verified_actionable_negative_flaw_count=10`
- `potential_concern_count=10`
- `final_potential_concern_total=27`
- `mark_contested_commit_count=10`
- recovery case table: `verified_review_issue_repair=5`, `verified_review_negative_repair=1`
- protection safety lines: `positive_or_neutral_negative_candidate_count=0`, `semantic_negative_without_review_relation_count=0`

Important caveats:

- `author_limitation_only_count=2`, `negative_grounding_conflict_count=13`, and `assessment_limitation_flaw_count=27` remain elevated. They do not break protection, but they show quote-bank negative candidates still create limitation/noise pressure.
- CANDPRIORITY1 is still conservative relative to the earlier loose runs. It keeps the QUALITYFIX2 removals: generic `7Dub7UXTXN` baseline issue, intro/problem-only `TPAj63ax4Y` insufficient-evaluation issue, and duplicate XH3 quote-negative counting.
- The case table now separates `reviewer_candidate` issues from `claim_obligation` fallback issues. This is the main paper-narrative distinction: reviewer-candidate issues are model-proposed review concerns that survived bundle verification; claim-obligation issues are deterministic fallback gaps.
- New reviewer-candidate case added by this recompute: `uOrfve3prk` `evaluation_protocol_risk`, missing "Validation of normalized edit distance proxy against human judgment", anchored by intervention-success evaluation inventory.
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
- CANDPRIORITY1 changes `_add_reviewer_absence_audit_artifacts` to prioritize reviewer-discovered candidate gaps before deterministic `verified_coverage_gap_items`; deterministic gaps now fill remaining slots instead of crowding out model-proposed review issues.
- CANDPRIORITY1 adds `reviewer_candidate_review_issue_count` / `claim_obligation_review_issue_count` and matching claim/type metrics so dashboard and case tables can distinguish real reviewer-discovered issues from fallback structural gaps.
- CANDPRIORITY1 keeps baseline specificity strict but lets protocol/evaluation candidates use concrete review dimensions such as human-judgment validation, proxy validation, threshold/protocol checks, substructure tasks, or result-table dimensions.

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
