# Review-Semantic Negative Evidence Audit Plan (2026-06-18)

## 0. Purpose

This plan records the latest failure mode: several counted "negative evidence" items are not reviewer-discovered paper flaws. They are paper-text extractions, often author/self-context limitation wording or even positive statements, that were laundered into `negative_evidence` because they were paper-grounded and contained a negative-looking anchor word.

This is a paper-narrative issue, not just an engineering metric issue. The project must support the论文叙事:

> ReviewState should make review reasoning structured, evidence-grounded, auditable, and recoverable. It must not reduce paper review to keyword extraction from paper text.

Therefore, the next changes must separate:

- **paper-grounded quote**: the text exists in the paper;
- **paper-text negative cue**: the text contains words like limitation, missing, not evaluated;
- **review-negative evidence**: the quote genuinely weakens a target claim or grounds a reviewer concern;
- **claim-requirement diagnosis**: absence/coverage judgment that may be a potential concern but is not quote-verified negative evidence.

## 1. Latest Smoke8 Exposure

Run:

`mimo_v25_diagpendingfix_default_qhyg_smoke8_mt7_b4w2_api2_r10t600_20260618_000924.jsonl`

Comparison dashboard:

`mimo_v25_diagpendingfix_default_qhyg_smoke8_mt7_b4w2_api2_r10t600_20260618_000924_VS_QHYG_TRUENEG_DASHBOARD.md`

Key result:

| metric | qhyg_trueneg | diagpendingfix_default | delta |
|---|---:|---:|---:|
| overall protection | PASS | PASS | - |
| real_strong_support_total | 36 | 39 | +3 |
| negative_evidence_candidate_count | 11 | 5 | -6 |
| verified_negative_flaw_count | 10 | 6 | -4 |
| verified_actionable_negative_flaw_count | 2 | 3 | +1 |
| potential_concern_count | 2 | 3 | +1 |
| mark_contested_commit_count | 5 | 1 | -4 |
| recovery_effective_repair | 5 | 1 | -4 |
| negative_evidence_semantic_rejected_count | 1 | 7 | +6 |
| recovery_harmful_commit_risk | 0 | 0 | 0 |

Interpretation:

- Safety did not break.
- Positive support did not regress.
- But negative/recovery lifecycle regressed badly.
- More importantly, the remaining counted negative evidence is not reliably review-semantic.

Examples of counted decision-view negative candidates:

| paper | quote | current type | audit judgment |
|---|---|---|---|
| `WLgbjzKJkk` | `(2023)) that introduces one-to-many assignment to overcome this limitation.` | `scope_limitation` | Prior-work/context limitation, not a flaw in the reviewed paper. |
| `WLgbjzKJkk` | `In this paper, we present a novel viewpoint for addressing the above limitations...` | `scope_limitation` | Positive paper claim about addressing limitations, not negative evidence. |
| `QAAsnSRwgu` | `we do not evaluate the quality of the output...` | `insufficient_evaluation` | Real review-negative evidence candidate. |
| `QAAsnSRwgu` | `if there are limitations on computational resources, we prioritise models...` | `scope_limitation` | Resource/context limitation, not necessarily a paper flaw. |

This confirms the core bug:

> `paper_grounded + negative-looking word` is being treated as `review-negative`.

## 2. Workflow Audit Findings

### Finding A: Quote-Bank Construction Conflates Candidate Text With Flaw Evidence

Relevant code:

- `agent_system/environments/env_package/review/state.py`
  - `_build_evidence_quote_bank`: lines around 8663-8772
  - `_build_critique_negative_quote_bank`: lines around 8775-8871
  - `_classify_negative_evidence_type`: lines around 8134-8181

Problem:

- The quote bank is built with regex anchors over paper text.
- `_NEG_TYPE_SCOPE_LIMITATION_RE` treats broad words such as `limitation`, `limited`, `assumption`, `future work` as `scope_limitation`.
- A quote can become `negative_or_gap` because it contains a negative-looking word, even if the sentence is positive, prior-work context, or author motivation.

Impact:

- Quote-bank entries are useful as **candidates**, but the current flow lets them become evidence before a reviewer-style relation is established.

### Finding B: Deterministic Salvage Creates Negative Evidence Without Reviewer Diagnosis

Relevant code:

- `agent_system/inference/review_runner.py`
  - `_select_negative_quote_bank_entries`: lines around 833-910
  - `_negative_quote_bank_salvage_payload`: lines around 1019-1070
  - `_negative_salvage_target_flaw_updates`: lines around 944-1016
  - `_enforce_negative_evidence_formation_payload`: lines around 2664-2755

Problem:

- If an Evidence Agent negative turn has no grounded negative quote, `_enforce_negative_evidence_formation_payload` can force quote-bank salvage.
- Salvage writes:
  - `stance="missing"`
  - `strength="missing"`
  - `source="quote-bank-negative-grounding"`
  - `grounded_judge_label="paper_grounded"`
  - `binding_status="bound_real_claim"`
- `_negative_salvage_target_flaw_updates` can then create a flaw whose text starts with `Verified ... against claim ...`.

Impact:

- The system, not the reviewer model, is fabricating the review relation from a quote candidate.
- This is the highest-risk path for paper-narrative contamination.

### Finding C: Semantic Verification Checks Quote Existence And Negative Cue, Not Review Relation

Relevant code:

- `agent_system/environments/env_package/review/state.py`
  - `_assess_quote_semantic_grounding`: lines around 1371-1445

Problem:

- For negative-intent evidence, the verifier accepts `semantic_negative_verified` when the quote has a negative anchor word or enough lexical overlap.
- It does not ask: "Does this quote genuinely weaken the target claim?"
- It does not distinguish:
  - current-paper flaw;
  - prior-work limitation;
  - author says they address a limitation;
  - author states a boundary or resource preference;
  - positive result sentence with a negative-looking term.

Impact:

- The verifier proves the quote is real, but not that it is a review-negative relation.

### Finding D: Negative Evidence Gate Is Too Broad

Relevant code:

- `agent_system/environments/env_package/review/state.py`
  - `_is_paper_negative_evidence_record`: lines around 10033-10038
  - `_is_grounded_paper_negative_evidence_record`: lines around 10050-10063
  - `_flaw_valid_negative_evidence_ids`: lines around 10205-10228

Problem:

- A record becomes paper-negative if it has negative stance/missing strength and a real-claim-like ID.
- `_is_grounded_paper_negative_evidence_record` currently allows `semantic_negative_verified` **or** `semantic_support_verified`.
- The gate does not require a separate `review_negative_verified` relation.

Impact:

- Evidence can pass because it is paper-grounded and semantically related, even when the relation is support/context rather than review-negative.

### Finding E: Claim Gate Divergence Increases Risk

Relevant code:

- `agent_system/environments/env_package/review/state.py`
  - `_is_real_paper_claim_id_for_negative`: lines around 1730-1744
  - `_is_real_paper_negative_target`: lines around 3339-3372
- `agent_system/inference/review_runner.py`
  - `_is_negative_binding_claim_target`: lines around 357-385

Problem:

- Diagnosis target gating is stricter and checks origin/text leakage.
- Later decision-view negative evidence binding can be looser, especially around raw-salvaged `claim-paper-fallback-*` claims.

Impact:

- Salvaged paper text may be allowed to host verified negative concerns even when it is a weak basis for final review-negative evidence.

### Finding F: Manager Shortfall Pressure Incentivizes Forced Negative Formation

Relevant code:

- `agent_system/review_manager_policy.py`
  - hard-negative discovery override: lines around 2503-2626

Problem:

- Shortfall-driven routing asks the system to find negative evidence when metrics are low.
- When the model does not naturally produce valid negative evidence, the runner salvage path fills the gap from quote bank.

Impact:

- The system optimizes toward negative-count closure instead of reviewer-quality negative discovery.

### Finding G: Final-View And Recovery Depend On The Same Contaminated Gate

Relevant code:

- `agent_system/environments/env_package/review/state.py`
  - `_verified_actionable_negative_evidence_ids_for_flaw`: lines around 10241-10248
  - `_classify_flaw_final_view_layer`: lines around 10380-10412
- `agent_system/inference/review_runner.py`
  - recovery target selection reads verified-negative evidence and can `mark_contested`.

Problem:

- If a false review-negative record enters the verified negative set, downstream potential concern and recovery treat it as legitimate.

Impact:

- Recovery can become structurally clean but narratively wrong: it repairs state around a fake flaw.

### Finding H: Prompt/State Slices Can Recycle Unverified Negative-Looking Text

Relevant code:

- `agent_system/environments/env_package/review/state.py`
  - `_render_manager_state_slice`: lines around 9092-9126
  - `_render_critique_state_slice`: lines around 9438-9474
  - `_prioritize_critique_evidence`: lines around 10083-10097

Problem:

- Some prompt slices use `_is_paper_negative_evidence_record` rather than the grounded verified negative gate.
- That means records with negative stance/strength can be shown to Critique as `negative_evidence_candidates` before they pass review-semantic verification.
- Once shown back to Critique, these records can be treated as already discovered weaknesses and re-bound to flaws.

Impact:

- A paper-text snippet can be recycled through the agent loop until it looks like a review finding.
- This is especially risky for author limitation wording, prior-work limitation wording, and positive "we address limitations" statements.

Required fix:

- Prompt/state slices should expose three separate buckets:
  - `verified_review_negative_evidence`;
  - `candidate_negative_quotes_needing_review_relation`;
  - `rejected_or_context_negative_text`.
- Critique should only bind flaws from the first bucket.
- Candidate/rejected buckets may be used only to ask Evidence for verification or to route an assessment limitation.

### Finding I: Final Concern Rendering Can Give Verified Language To A Weak Relation

Relevant code:

- `agent_system/environments/env_package/review/state.py`
  - `_render_verified_negative_concern_line`: lines around 10592-10630
  - `_render_potential_concerns`: lines around 10664-10716

Problem:

- If a false negative evidence item reaches `_verified_actionable_negative_evidence_ids_for_flaw`, final report text says `Verified negative concern`.
- The line then explains a reviewer implication even though the system has only established quote existence and keyword-level negativity.

Impact:

- The user-facing report can overclaim: it presents an author/self limitation or positive claim as an auditable review defect.

Required fix:

- The "Verified negative concern" rendering path must require `review_negative_label == review_negative_verified`.
- Anything else must be rendered as:
  - diagnosis-pending potential concern;
  - author limitation / scope note;
  - assessment limitation;
  - or rejected audit sample, not a verified concern.

### Finding J: Dashboard Protection Lines Do Not Measure Review-Semantic Validity

Relevant code:

- `scripts/dashboard_run_comparison_v1.py`

Problem:

- Existing protection lines cover support validity, unlinked negatives, recovery safety, and locator specificity.
- They do not ask whether a counted negative is a reviewer-discovered paper defect rather than paper text with negative wording.

Impact:

- A run can show `Overall protection: PASS` while still violating the paper narrative.

Required fix:

- Add dashboard metrics for review-semantic labels and quote-bank salvage:
  - verified review-negative count;
  - author-limitation-only count;
  - prior-work limitation count;
  - positive/neutral negative-looking text count;
  - semantic-negative-without-review-relation count;
  - auto-salvaged flaw count.

### Finding K: Recovery Uses A Narrower But Still Insufficient Negative Gate

Relevant code:

- `agent_system/inference/review_runner.py`
  - `_is_verified_negative_evidence_for_recovery`: lines around 1073-1080
  - `_mark_contested_patch_from_verified_negative_flaw`: lines around 1279-1347
  - `_claim_downgrade_patch_from_actionable_flaw`: lines around 1158-1214
- `agent_system/environments/env_package/review/recovery_validator.py`
  - `VERIFIED_RECOVERY_SEMANTIC_LABELS`: lines around 34-35
  - `_is_verified_negative_recovery_evidence`: lines around 306-312
  - `_validate_mark_contested_evidence_semantics`: lines around 390-432
  - `_flaw_verified_actionable_negative_recovery_ids`: lines around 435-454

Problem:

- Recovery currently requires paper grounding and semantic labels, but not review-semantic negative verification.
- It can still mark a claim contested around a false negative if that record carries `semantic_negative_verified`.
- The direct recovery validator is especially risky because it still accepts `semantic_support_verified` as verified recovery evidence through `VERIFIED_RECOVERY_SEMANTIC_LABELS`.
- Direct `merge_review_state` / recovery patch validation can therefore preserve or downgrade flaws around quote-bank or support/context text that the final-view gate would later reject.

Impact:

- Recovery count can look meaningful while the underlying "repair" is around a fake flaw.
- The paper narrative is damaged twice: the system first mislabels paper text as a review defect, then records a "recovery" lifecycle around that false defect.

Required fix:

- Recovery negative validation must require the same `review_negative_verified` gate used by final-view flaw promotion.
- Claim downgrade remains blocked for quote-bank salvage; `mark_contested` should also require a real review-negative relation.
- `semantic_support_verified` must never satisfy a negative recovery evidence gate.
- Add tests where quote-bank `scope_limitation`, prior-work limitation, and positive "addressing limitations" text cannot validate `mark_contested`, `downgrade_final_to_candidate`, or `route_to_assessment_limitation` as real recovery.

### Finding L: Criterion Assessment Can Still Be Polluted By Active Flaw Text

Relevant code:

- `agent_system/environments/env_package/review/state.py`
  - `_active_flaws_for_criterion`: lines around 11073-11086
  - `_render_criterion_assessments`: lines around 11106-11210
  - `_build_review_diagnostic_parts`: lines around 11515-11518

Problem:

- The main grounded-weakness and potential-concern renderers now have stronger gates, but criterion assessment still selects active flaws by regex over flaw title/description.
- It does not require the flaw to have review-negative verified evidence before it can make criterion statuses `negative` or `mixed`.
- A fake negative flaw with words such as `baseline`, `evaluation`, `method`, `reproducibility`, or `prior work` can leak into `Technical Soundness`, `Empirical Adequacy`, `Clarity / Reproducibility`, or `Novelty / Originality`.

Impact:

- The user-facing "Key Weaknesses" section may say no grounded weakness passed the filter, while the criterion section still implies a paper defect.
- This is a report-layer contradiction and directly violates the paper narrative.

Required fix:

- Criterion assessment must separate:
  - review-negative verified flaws;
  - diagnosis-pending concerns;
  - ungrounded/assessment-limitation flaws.
- Criterion statuses may become `negative` only from review-negative verified flaws.
- Diagnosis-pending or unverified flaws should produce `mixed` / `not_assessable` wording that explicitly says human verification is needed.

### Finding M: Final Recommendation Still Carries An Active-Flaw Shortcut

Relevant code:

- `agent_system/environments/env_package/review/state.py`
  - `infer_final_recommendation_view`: lines around 5994-6115
  - `active_major_like`: lines around 6034-6040

Problem:

- The final recommendation view correctly checks `grounded_critical` and `grounded_major`, but it also uses `active_major_like`.
- `active_major_like` is any active major/critical non-fallback flaw, not necessarily a review-negative verified flaw.
- This can block `accept_like` or push borderline outcomes because a major fake flaw survived as active text.

Impact:

- Even if fake negatives are prevented from becoming grounded weaknesses, they can still affect high-level diagnostic signal through a shortcut.

Required fix:

- Replace `active_major_like` with a stricter bucket:
  - grounded review-negative major/critical flaws;
  - diagnosis-pending major concerns;
  - ungrounded major assessment limitations.
- Only the first bucket should act as a hard grounded blocker.

### Finding N: Critique Prompt Still Allows Quote-Bank Direct Evidence Creation

Relevant code:

- `agent_system/review_prompts.py`
  - Critique prompt lines around 247-258
  - line around 256: create an `evidence_map` item from `Critique Negative Quote Bank` before writing the flaw

Problem:

- The hard-negative prompt says quote bank is grounding material, not a flaw trigger, but later still instructs Critique to create one negative evidence item from the best quote if no negative evidence id exists.
- That direct creation uses `stance="missing"`, `contradicts`, or `weakens` before the review-semantic gate has proven the quote weakens the target claim.

Impact:

- The model is nudged to turn quote-bank snippets into negative evidence because the schema path makes that easy.
- This can recreate the same failure after code-level gates are tightened, especially under short output budgets where the model writes the evidence item and flaw but not the relation rationale.

Required fix:

- Critique may create `candidate_negative_quote` or `diagnosis_pending_verification`, but must not create a verified-looking negative evidence item from quote bank.
- The prompt should explicitly say: quote-bank-derived evidence is candidate-only until the state verifier assigns `review_negative_verified`.
- If the model has a diagnosis but no verified negative evidence id, it should emit a candidate flaw without `negative_evidence_ids`.

### Finding O: Prompt-State Reflow Can Recycle Rejected Negative Text

Relevant code:

- `agent_system/environments/env_package/review/state.py`
  - `_compact_evidence_for_prompt`: lines around 10270-10284
  - challenge-mode claim expansion in `_render_critique_state_slice`: lines around 9620-9638

Problem:

- `_compact_evidence_for_prompt` prioritizes `_is_paper_negative_evidence_record`, which is broader than review-negative verified evidence.
- The challenge-mode critique slice still unions claim ids from `_is_paper_negative_evidence_record`, even before the record passes the review-negative gate.

Impact:

- A rejected or merely candidate negative-looking snippet can keep reappearing in prompts, giving the agent loop repeated chances to re-bind it as a flaw.

Required fix:

- Verified review-negative records get first priority.
- Candidate/rejected negative-looking records should be passed in a separate bucket with a warning label and must not be presented as already discovered negative evidence.
- Challenge-mode expansion should use review-negative verified records or explicit target ids, not broad paper-negative stance alone.

## 2.1 End-To-End Narrative Contract

Every stage must preserve the following contract:

| Stage | Allowed narrative role | Disallowed shortcut |
|---|---|---|
| Claim extraction | Identify real paper claims and auditable claim requirements. | Treat context/fallback scaffolds as final review targets. |
| Evidence generation | Copy quotes and locators; classify support/negative candidates. | Turn negative-looking paper text into a flaw by itself. |
| Semantic grounding | Verify quote existence and semantic alignment. | Treat keyword negativity as review-negative validity. |
| Review-negative gate | Establish that the quote weakens a target claim or grounds a concrete reviewer concern. | Accept author limitation, prior-work limitation, or positive "addressing limitations" text as a defect. |
| Flaw promotion | Promote only review-negative verified evidence to verified flaw/concern. | Promote quote-bank salvage or support/context text. |
| Final concern rendering | Separate verified concern, diagnosis-pending gap, author limitation, and assessment limitation. | Use `Verified negative concern` wording for unverified review relations. |
| Recovery | Repair conflicts around real verified negative flaws. | Count recovery around fake negatives or diagnosis bookkeeping as effective repair. |
| Dashboard | Prove quality and failure visibility. | Let overall PASS hide review-semantic false positives. |

This contract is a paper-level invariant: any path that violates it must be removed, gated off, or demoted to audit-only status.

## 2.2 Newly Recorded Failure To Carry Forward

This issue must remain in the plan until fixed and tested:

> The latest smoke8 showed that counted "negative evidence" can be fake in the paper-review sense: it is often author/self limitation wording, prior-work limitation context, positive text about addressing limitations, or generic paper extraction. It is paper-grounded, but it is not a reviewer-discovered defect.

Known false-positive patterns:

- `addressing the above limitations`;
- `overcome this limitation`;
- prior-work statements such as another method introducing an assignment mechanism to overcome a limitation;
- positive robustness/outperformance sentences containing limitation or comparison words;
- resource prioritization statements that do not show a current-paper evaluation flaw.

Known true-positive direction:

- current paper explicitly states it does not evaluate claimed output quality;
- current paper reports no comparison, no ablation, no reproducibility detail, or weaker result in a way that directly weakens the target claim;
- structured claim-requirement audit proves a missing support category, but this remains diagnosis-pending unless quote/coverage verification passes.

## 2.3 Fix Order From This Audit

Do not chase negative/recovery quantity until these gates are in place:

1. Add review-semantic negative labels during evidence verification.
2. Require `review_negative_verified` in `_is_grounded_paper_negative_evidence_record`.
3. Demote quote-bank salvage so it cannot auto-create verified negative flaws.
4. Stop prompt slices from presenting unverified negative-looking records as `negative_evidence_candidates`.
5. Make final concern and recovery consume only review-semantic verified negatives.
6. Align `recovery_validator.py` with the same review-negative gate, including direct patch validation.
7. Make criterion assessment and final recommendation distinguish verified flaws from diagnosis-pending or ungrounded active flaw text.
8. Remove prompt wording that lets Critique create verified-looking negative evidence directly from quote bank.
9. Add dashboard protection lines for this failure class.
10. Add focused tests for the known false and true examples.

## 3. Immediate Direction

Do not chase higher negative counts until review-semantic validity is fixed.

The next objective is:

> Make verified negative evidence require a review-semantic relation, not just paper quote grounding.

It is acceptable for `negative_evidence_candidate_count` to drop temporarily. A smaller set of true review-negative evidence is better than a larger set of paper-text snippets.

## 4. Implementation Plan

### P0: Add A Review-Semantic Negative Gate

Add a new deterministic/view-layer label, for example:

```text
review_negative_label =
  review_negative_verified
  author_limitation_only
  prior_work_limitation
  positive_or_neutral_support
  resource_or_scope_context
  retrieval_context_only
  insufficient_claim_relation
```

Inputs:

- claim text;
- quote;
- negative type;
- source bucket;
- evidence text;
- locator;
- whether quote came from deterministic salvage.

Rules:

- Accept `review_negative_verified` only when the quote directly weakens the target claim or grounds a concrete reviewer concern.
- Reject as `prior_work_limitation` when the quote is about another method/work unless it directly undermines the reviewed paper's claim.
- Reject as `positive_or_neutral_support` when the quote says the method addresses limitations, improves robustness, outperforms baselines, or explains method design.
- Reject as `author_limitation_only` or `resource_or_scope_context` unless it states a concrete current-paper evidence gap relevant to a claim.
- Treat `scope_limitation` as `assessment_limitation` unless it passes a concrete claim-relation test.

Acceptance change:

```text
_is_grounded_paper_negative_evidence_record
  requires paper grounding
  requires semantic_negative_verified
  requires review_negative_label == review_negative_verified
```

Do not allow `semantic_support_verified` to count as grounded negative evidence.

### P1: Demote Automatic Quote-Bank Salvage

Change the salvage path so it no longer fabricates verified negative evidence.

Target behavior:

- `_negative_quote_bank_salvage_payload` may create `negative_quote_candidate` records for audit, but not verified negative evidence.
- Do not set `stance="missing"` by default for salvage.
- Do not auto-create `negative_evidence_ids` for flaws from salvage.
- Do not use wording like `Verified ... against claim` until a review-semantic gate passes.

Allowed exception:

- Salvage can create true negative evidence only when:
  - the quote entry is a true paper-negative type, not `scope_limitation`/`generic_gap`;
  - claim relation passes;
  - review-negative label is verified;
  - locator is specific enough;
  - claim target is a real auditable claim.

### P2: Tighten Quote-Bank Negative Candidate Selection

Reject or demote these quote patterns before they enter negative quote bank:

- `addressing/overcoming the limitation(s)` positive motivation;
- `introduces ... to overcome this limitation`;
- prior-work limitation unless explicitly tied to the reviewed paper's result/claim failure;
- positive result statements such as `outperforms`, `enhances robustness`, `guarantees accuracy`;
- resource preference statements that do not show a paper-evaluation gap;
- section/header/future-work text without a concrete current-paper weakness.

Keep as candidates only when the quote states a concrete current-paper issue:

- no/insufficient evaluation of claimed output quality;
- no baseline/comparison where the claim is comparative;
- missing ablation for a component/contribution claim;
- negative result or result-claim mismatch;
- concrete reproducibility gap;
- method assumption that narrows or invalidates a broad claim.

### P3: Separate Claim-Requirement Diagnosis From Quote-Verified Evidence

Absence-based review problems often do not have a quote saying "we failed to do X".

Correct treatment:

- `claim_requirement_gap` can render a potential concern.
- It should carry `diagnosis_pending_verification`.
- It must not increment verified negative evidence.
- It can prioritize Evidence Agent targets, but should not force a negative evidence item.

This keeps the review narrative honest:

- The system can say "the verified support inventory lacks baseline comparison for this claim."
- It must not say "verified negative evidence proves missing baseline" unless a quote or structured coverage check verifies it.

### P4: Recovery Must Depend On Review-Negative Verification

Recovery operations should use the new gate.

Rules:

- `mark_contested` requires:
  - real positive support;
  - `review_negative_verified` negative evidence;
  - same claim/flaw relation;
  - no fallback/context claim status patch.
- `downgrade_final_to_candidate` requires a flaw over-escalation plus insufficient review-negative grounding.
- `route_to_assessment_limitation` handles author limitations or system assessment limitations.
- `resolve_stale_gap` handles support/negative evidence superseding an old gap.

Do not count recovery as meaningful if it only cleaned up an auto-salvaged fake flaw.

Implementation notes:

- Apply this in both runner helper code and `recovery_validator.py`; otherwise direct `merge_review_state` patch validation can bypass the final-view gate.
- `semantic_support_verified` must be valid only for positive recovery, never for negative recovery.
- A quote-bank/raw-quote negative record must carry:
  - `semantic_grounding_label == semantic_negative_verified`;
  - `review_negative_label == review_negative_verified`;
  - real claim/flaw alignment;
  - specific locator.
- Legacy fixture compatibility can remain only for synthetic tests that have no `raw_quote`, no `quote_id`, no quote-bank source, and no review-negative check field.

### P4.5: Report And Recommendation Must Not Trust Active-Flaw Text Alone

The final report has multiple output surfaces. All must preserve the same narrative contract.

Required changes:

- `_render_weaknesses` and `_render_potential_concerns` should keep their review-negative gate.
- `_render_criterion_assessments` must not make a criterion `negative` from regex-matched active flaw text unless the flaw has review-negative verified evidence.
- `infer_final_recommendation_view` must not use generic `active_major_like` as a hard grounded blocker.
- Criterion/report wording should separate:
  - `verified review-negative flaw`;
  - `diagnosis-pending concern`;
  - `assessment limitation`;
  - `rejected paper-text negative candidate`.

Tests:

- A major fake flaw whose evidence is positive/support or prior-work limitation must not make `Technical Soundness` or `Empirical Adequacy` negative.
- The same fake flaw must not block `accept_like` via `active_major_like`.
- A true review-negative verified flaw should still affect criteria and recommendation.

### P5: Add Metrics That Expose This Failure

Add dashboard metrics:

```text
review_negative_verified_count
paper_text_negative_candidate_count
author_limitation_only_count
prior_work_limitation_count
positive_or_neutral_negative_candidate_count
quote_bank_salvage_generated_negative_count
auto_salvaged_flaw_count
semantic_negative_without_review_relation_count
scope_limitation_as_verified_negative_count
review_negative_false_positive_sample_count
```

Protection lines:

```text
auto_salvaged_flaw_count == 0
semantic_negative_without_review_relation_count == 0
scope_limitation_as_verified_negative_count == 0
positive_or_neutral_negative_candidate_count == 0
```

The exact thresholds can be relaxed during audit mode, but they must be explicit so the dashboard does not hide this class of failure.

### P6: Add Focused Regression Tests

Reject as verified negative:

- `In this paper, we present a novel viewpoint for addressing the above limitations...`
- `... introduces one-to-many assignment to overcome this limitation.`
- `This hierarchical approach enhances robustness...`
- `Comparative analyses demonstrate that the method outperforms...`
- `DPS used Tweedie's formula ... useful when data is limited.`

Accept as review-negative candidate:

- `we do not evaluate the quality of the output...`
- `does not compare against recent strong baselines...`
- `no ablation study is provided...`
- `performance is worse than baseline on ...`
- `implementation details/hyperparameters are not provided...`

Test surfaces:

- quote classifier;
- review-negative relation gate;
- `_is_grounded_paper_negative_evidence_record`;
- final-view `potential_concern_count`;
- recovery `mark_contested` target selection;
- dashboard protection metrics.

### P7: Remove Or Default-Off Proven Bad Paths

After P0-P2 are implemented:

- remove or demote automatic negative quote-bank flaw creation;
- keep `DRMAS_HARDNEG_DIAGNOSIS=1` default off;
- keep `DRMAS_NEG_RECLASSIFY=1` default off unless a new A/B proves value;
- keep `DRMAS_TARGETED_NEGATIVE_SEARCH=1` experimental only;
- do not revive compact/aggressive negative passes without review-semantic gating.

This cleanup belongs in the plan because the project has already accumulated several paths that can inflate negative counts without improving paper-review validity.

### P8: Whole-Workflow Audit Checklist

Run this checklist before the next MIMO smoke:

| Stage | Audit question | Pass condition |
|---|---|---|
| Claim extraction | Are review targets real paper claims, not context/fallback scaffolds? | Negative/recovery targets never patch fallback/context claim status. |
| Evidence quote bank | Are negative-looking quotes only candidates? | Quote bank entries cannot become verified negative evidence without review-semantic labeling. |
| Evidence Agent | Does negative mode require a direct claim-weakening quote? | Otherwise emits `unresolved_questions` / `not_assessable`, not `stance=missing`. |
| Critique Agent | Does diagnosis precede quote use? | Quote bank cannot trigger flaw creation by itself. |
| State merge | Does verification check paper grounding, semantic negative, and review relation? | All three labels are required. |
| Flaw promotion | Can fake paper-text negative become `potential_concern`? | No; it becomes rejected candidate, assessment limitation, or diagnosis-pending concern. |
| Recovery validator | Can fake negative validate `mark_contested` or downgrade? | No; `review_negative_verified` is required. |
| Final report | Can active flaw text alone change criterion status? | No; criterion negatives require verified review-negative flaws. |
| Recommendation | Can unverified active major flaw block support-rich outcome? | No; it is diagnosis-pending or not-assessable, not a grounded blocker. |
| Dashboard | Does PASS expose false-positive negatives? | Protection lines include review-semantic false-positive counters. |

## 5. Validation Plan

### Step 1: Offline Audit On Latest Smoke8

Before rerunning API:

- compute all current negative candidates;
- label each with the new review-semantic categories;
- verify the known false examples are rejected.

Expected:

```text
review_negative_verified_count <= old negative_evidence_candidate_count
positive_or_neutral_negative_candidate_count > 0 on old run
auto_salvaged_flaw_count > 0 on old run
```

This proves the new audit catches the exposed issue.

### Step 2: Focused Tests

Run:

```bash
pytest tests/test_review_decision_hygiene.py tests/test_review_inference_runner.py tests/test_recovery_patch.py -q
```

Expected:

```text
all focused tests pass
new false-positive fixture tests pass
```

### Step 3: Smoke8 Rerun

Run default qhyg smoke8 with `max_turns=7`.

Acceptance is quality-first:

```text
overall protection = PASS
auto_salvaged_flaw_count = 0
semantic_negative_without_review_relation_count = 0
positive_or_neutral_negative_candidate_count = 0
negative_evidence_unlinked_to_flaw = 0
recovery_harmful_commit_risk = 0
recovery_no_effect_commit = 0
```

Do not require negative count to increase in the first run. The first goal is to remove fake review-negative evidence.

### Step 4: Hardneg20 Only After Smoke8 Is Clean

Hardneg20 should be used to measure whether true review-negative recall is still sufficient after filtering.

Report separately:

- verified review-negative evidence;
- diagnosis-pending claim requirement concerns;
- author/self limitation candidates;
- recovery around verified review-negative flaws.

## 6. Success Criteria

A future run is not successful because `negative_evidence_candidate_count` is high.

It is successful only if:

- quoted evidence is paper-grounded;
- the quote genuinely weakens a target claim or grounds a reviewer concern;
- absence-based concerns are separated as diagnosis-pending;
- recovery operates on real review-negative flaws;
- false paper-text extractions are visible as rejected candidates, not hidden inside verified metrics.

## 7. Current Worktree Audit Snapshot

This section records the state exposed by the latest audit before any new API rerun is trusted.

### 7.1 What Has Started To Move In The Right Direction

The current worktree already contains partial fixes for the exposed failure mode:

- `state.py` has a new review-semantic relation gate (`review_negative_label`) that can distinguish:
  - `review_negative_verified`;
  - `author_limitation_only`;
  - `prior_work_limitation`;
  - `positive_or_neutral_support`;
  - `resource_or_scope_context`;
  - `insufficient_claim_relation`.
- `_is_grounded_paper_negative_evidence_record` now requires:
  - real paper-negative stance;
  - verified paper grounding;
  - `semantic_grounding_label == semantic_negative_verified`;
  - `review_negative_label == review_negative_verified`.
- Recovery runner and direct `recovery_validator.py` paths have started to reject raw quote-bank / raw-quote negative evidence unless it carries `review_negative_verified`.
- Criterion assessment and final recommendation have started to separate verified review-negative flaws from diagnosis-pending or ungrounded active flaw text.
- Dashboard aggregation now exposes review-semantic counters such as:
  - `review_negative_verified_count`;
  - `semantic_negative_without_review_relation_count`;
  - `positive_or_neutral_negative_candidate_count`;
  - `quote_bank_salvage_generated_negative_count`;
  - `scope_limitation_as_verified_negative_count`.

These are necessary changes, but they do not by themselves prove the pipeline is fixed.

### 7.2 Remaining Workflow Risks Found In This Audit

The following risks must stay in the plan until tests and a clean smoke confirm them:

1. **Runner quote-bank salvage still emits verified-looking objects.**

   `_negative_quote_bank_salvage_payload` still creates evidence with:

   ```text
   source = quote-bank-negative-grounding
   stance = missing
   strength = missing
   binding_status = bound_real_claim
   ```

   `_negative_salvage_target_flaw_updates` still places the salvaged evidence id into `negative_evidence_ids`.

   Even if final-view gates later reject it, this object can still circulate through prompts, recovery targeting, turn logs, and old tests as if it were negative evidence. The next implementation step should demote this path to a candidate-only object that cannot populate `negative_evidence_ids` until the review-negative gate passes.

2. **Critique prompt schema still offers a direct negative-evidence lane.**

   The prompt text now says quote-bank text is candidate-only, but the schema still asks the Critique Agent to output `evidence_map` rows with negative stances and `negative_evidence_ids`. This can recreate the old shortcut under tight token budgets.

   The prompt contract should be changed so Critique may output:

   ```text
   diagnosis_pending_verification flaw
   candidate_negative_quote reference
   unresolved question
   ```

   but not a verified-looking quote-bank negative evidence item.

3. **Review-negative relation heuristics need conservative tightening.**

   The new deterministic gate is directionally correct, but it is still regex/overlap based. In particular, `scope_overclaim` and broad-claim logic must not accept a quote simply because the claim is broad; the quote must contain a concrete current-paper restriction or contradiction.

4. **Legacy compatibility fallback can hide invalid fixtures.**

   Recovery validation currently has a narrow legacy allowance for unlabeled synthetic negative records without raw quote or quote id. This may be useful for old fixtures, but live review evidence must never rely on it. Tests should make that distinction explicit.

5. **Dashboard protection is observational, not sufficient.**

   The new counters expose false paper-text negatives, but protection lines should not be treated as proof until the state-level and prompt-level shortcuts are removed. A run can still show the new counters as zero if the false negative never receives semantic-negative labeling, while candidate salvage still pollutes workflow behavior.

6. **Focused tests are not yet semantically reconciled.**

   The broader focused suite is expected to fail until old fixtures are updated. Many old tests encoded the now-invalid assumption that `semantic_support_verified` or quote-bank `scope_limitation` can ground negative recovery. Those fixtures must either add a true `review_negative_verified` label or change expected outcomes to blocked / assessment limitation.

### 7.3 Narrative-Level Invariant For The Next Fix

The pipeline must preserve this invariant across all stages:

> A paper quote can be verified as text from the paper without being verified as a reviewer-discovered defect.

Therefore:

- `paper_grounded_exact` proves quote existence only.
- `semantic_negative_verified` proves the quote and negative statement are textually aligned.
- `review_negative_verified` is the only label that proves the quote weakens a target claim or grounds a real reviewer concern.
- Only `review_negative_verified` may drive:
  - `verified_negative_flaw_count`;
  - `verified_actionable_negative_flaw_count`;
  - `grounded_weakness`;
  - final `Verified negative concern` wording;
  - `mark_contested`;
  - `downgrade_final_to_candidate`;
  - rejection-like criterion/recommendation effects.

Everything else is candidate, diagnosis-pending, assessment limitation, or rejected audit material.

## 8. Immediate Repair Plan Before Rerunning MIMO

Do not rerun smoke8 as evidence of progress until the following local work is complete.

### Task 1: Remove Verified-Looking Quote-Bank Salvage

- Change runner salvage so quote-bank fallback produces candidate-only records.
- Do not set `stance=missing` / `strength=missing` for quote-bank candidate salvage unless review-negative verification passes.
- Do not attach quote-bank candidate ids to `negative_evidence_ids`.
- Add a separate audit marker such as `negative_quote_candidate_status=candidate_needs_review_relation`.

Expected effect:

```text
quote_bank_salvage_generated_negative_count may remain visible for audit
auto-salvaged verified negative flaw count = 0
semantic_negative_without_review_relation_count = 0
```

### Task 2: Tighten Critique Output Contract

- Remove baseline instructions that encourage creating negative `evidence_map` rows directly from quote bank.
- Keep diagnosis output as `flaw_candidates` with `grounding_status=diagnosis_pending_verification`.
- Require existing `review_negative_verified` evidence id before Critique can populate `negative_evidence_ids`.
- Keep `DRMAS_HARDNEG_DIAGNOSIS` experimental and default-off until multi-seed A/B proves no regression.

### Task 3: Tighten Review-Negative Relation Rules

- Reject positive limitation-solving language:
  - `addressing the above limitations`;
  - `overcome this limitation`;
  - positive robustness / outperform / improvement text.
- Reject prior-work limitation text unless the quote directly undermines the reviewed paper's claim.
- Reject resource prioritization text unless it states a concrete evaluation or reproducibility gap.
- For `scope_overclaim`, require a concrete quote-side restriction, not only a broad target claim.

### Task 4: Reconcile Tests With The New Semantics

- Add a helper fixture for true verified review-negative evidence:

  ```text
  verified_grounding_label = paper_grounded_exact
  semantic_grounding_label = semantic_negative_verified
  review_negative_label = review_negative_verified
  raw_quote + source_locator + claim_id + negative_evidence_type
  ```

- Update tests that used:
  - `semantic_support_verified` as negative grounding;
  - unlabeled quote-bank negatives;
  - generic `scope_limitation`;
  - future-work/self-limitation text.

  Those should now expect blocked, diagnosis-pending, or assessment-limitation behavior.

### Task 5: Add End-To-End Regression Tests For The Exposed Failure

Required false-negative fixtures:

- prior-work/context limitation;
- positive "we address limitations" text;
- positive robustness/outperformance text with negative-looking words;
- resource prioritization without evaluation failure.

Required true-negative fixtures:

- explicit current-paper no-evaluation quote;
- no baseline / no ablation / no reproducibility detail;
- negative result or result-claim mismatch tied to a real claim.

Required surfaces:

- evidence verification;
- final-view concern promotion;
- criterion assessment;
- final recommendation;
- recovery patch validation;
- dashboard protection metrics.

### Task 6: Validate Locally Before API

Run:

```bash
python -m py_compile agent_system/environments/env_package/review/state.py agent_system/environments/env_package/review/recovery_validator.py agent_system/inference/review_runner.py agent_system/review_prompts.py
pytest tests/test_review_decision_hygiene.py tests/test_review_inference_runner.py tests/test_recovery_patch.py -q
```

Only after these pass should the next MIMO smoke8 be used as evidence.

## 8.1 Current Execution Status After Contract/Trace Hygiene

The latest completed runs show that the recent changes are **not yet a restoration of true reviewer-discovered negative evidence**. They are a safety and observability step.

Completed run:

`mimo_v25_realneg_sidechannel_smoke8_mt7_b4w2_api1_r8t600_20260618_194813.jsonl`

Generated reports:

- `mimo_v25_realneg_sidechannel_smoke8_mt7_b4w2_api1_r8t600_20260618_194813_DASHBOARD.md`
- `mimo_v25_realneg_sidechannel_smoke8_mt7_b4w2_api1_r8t600_20260618_194813_AUDIT.json`
- `mimo_v25_realneg_sidechannel_smoke8_mt7_b4w2_api1_r8t600_20260618_194813_RECOVERY_CASE.md`

Key metrics:

| metric | contractguard baseline | sidechannel | judgment |
|---|---:|---:|---|
| overall protection | PASS | PASS | safe |
| real_strong_support_total | 48 | 45 | small support regression, not collapse |
| empirical_real_strong_support_count | 38 | 36 | acceptable for trace experiment |
| negative_evidence_candidate_count | 0 | 0 | no verified negative restored |
| review_negative_verified_count | 0 | 0 | no reviewer-negative relation restored |
| verified_negative_flaw_count | 0 | 0 | no verified flaw lifecycle |
| potential_concern_count | 0 | 0 | no final concern promotion |
| recovery_committed | 0 | 0 | no recovery around negative flaws |
| recovery_case_rows | 0 | 0 | no recovery cases |

Interpretation:

- The fake-negative cleanup is working: no paper-text extraction, author limitation, positive/context quote, or quote-bank salvage is being counted as verified negative evidence in this run.
- The pipeline still fails the paper narrative goal because it has not recovered true reviewer-discovered negative evidence or recovery around it.
- The targeted negative search path currently helps identify what the system tried to check, but it does not yet produce quote-grounded verified negative evidence.
- A new `sidechannel2` smoke8 has been started after the final side-channel pass-through fix. Its purpose is to validate trace observability, not to claim negative/recovery restoration.

Updated invariant for the next implementation pass:

```text
No recovery credit without verified review-negative evidence.
No verified negative evidence without copied quote + locator + real claim/flaw binding + review_negative_verified relation.
No paper-text limitation/context/positive quote can enter the verified negative lifecycle.
```

## 8.2 Remaining Core Problem

The remaining bottleneck is not "negative type coverage" by itself. The system can name plausible review concerns such as `missing_ablation`, `missing_baseline`, `insufficient_evaluation`, and `reproducibility_gap`, but most of these are absence or coverage judgments. They often cannot be validated by a single quote where the paper admits the flaw.

Therefore the next real repair must split two channels:

1. **Reviewer diagnosis / claim-requirement gap**

   This channel may create `diagnosis_pending_verification` potential concerns. It should state what a reviewer needs to check and why the current support coverage is insufficient. It is allowed to be visible in the report as a potential concern, but it must not count as verified negative evidence.

2. **Quote-grounded verified negative evidence**

   This channel requires Evidence Agent or verifier output that contains an exact quote and locator, and the quote must directly weaken the target claim or ground a concrete reviewer concern. Only this channel can drive `verified_negative_flaw_count`, `mark_contested`, `downgrade_final_to_candidate`, and real recovery lifecycle metrics.

The next implementation should route diagnosis into better Evidence search targets without stealing positive evidence-recheck turns or fabricating negative evidence from quote bank text.

## 8.3 Current Semantic Gate Fix In Progress

Position in the plan:

- This is part of **Task 3: Add Review-Semantic Negative Relation Gate** and the later recovery lifecycle work.
- It does not relax the fake-negative guard. It narrows the path so a quote only counts as verified negative evidence when it has a review-negative relation.
- It addresses the live MiMo failure seen in `mimo_v25_realneg_recovery2_smoke8_mt7_b4w2_api1_r8t600_20260618_225604.jsonl`: the `QAAsnSRwgu` quote `we do not evaluate the quality of the output...` was paper-grounded and typed as `insufficient_evaluation`, but was misclassified as `semantic_support_verified` because MiMo emitted `stance="supports"`.

Code change:

- Added `_has_review_negative_semantic_intent` in `agent_system/environments/env_package/review/state.py`.
- `_assess_quote_semantic_grounding` now uses that helper for the negative semantic branch.
- The helper only rescues concrete current-paper gaps when:
  - the evidence has a true paper-negative type such as `insufficient_evaluation`;
  - the quote itself matches a concrete current-paper gap cue;
  - positive-context, prior-work, and author limitation/future-work shells are rejected.

Local verification completed:

- `python3 -m py_compile agent_system/environments/env_package/review/state.py tests/test_review_decision_hygiene.py agent_system/inference/review_runner.py agent_system/review_manager_policy.py`
- Manual invocation of targeted tests passed for:
  - current-paper evaluation gap with `stance="supports"` becomes `semantic_negative_verified` and `review_negative_verified`;
  - normal positive Table 2 support is not reclassified as negative even if `negative_evidence_type` is present;
  - author `future work` wording does not become a `scope_overclaim` concern;
  - true `scope_overclaim` still reaches potential concern when the quote directly contradicts broad scope;
  - contested support visibility still works for verified positive + verified negative evidence.

Additional test hygiene:

- Updated legacy tests so trusted negative fixtures include verifier metadata (`verified_source_span_start`, `verified_source_span_end`, `verified_quote_match_type`).
- Replaced an old `future work` scope-overclaim fixture with a direct scope contradiction quote.
- Changed the generic negative fixture away from `source="quote-bank-negative-grounding"` because quote-bank/system salvage must not count as reviewer-discovered verified negative evidence.

Live validation completed:

`mimo_v25_realneg_semanticfix1_smoke8_mt7_b4w2_api1_r8t600_20260619_001233.jsonl`

Command class:

```bash
DRMAS_NEG_QUOTE_HYGIENE=1 DRMAS_TARGETED_NEGATIVE_SEARCH=1
python3 -u agent_system/inference/review_runner.py \
  --backend api --api-provider mimo --api-model mimo-v2.5 \
  --dataset-path smoke8_sameids_20260604.parquet \
  --mode s4 --max-turns 7 --max-tokens 768 \
  --model-adapter-mode small_model --manager-batch-size 4 \
  --api-max-workers 1 --api-timeout 600 --api-max-retries 8
```

Result:

| metric | value |
|---|---:|
| papers | 8 |
| avg_reward | 0.5631 |
| overall protection | PASS |
| real_strong_support_total | 35 |
| empirical_real_strong_support_count | 30 |
| negative_evidence_candidate_count | 0 |
| review_negative_verified_count | 0 |
| verified_negative_flaw_count | 0 |
| potential_concern_count | 0 |
| recovery_committed | 0 |
| mark_contested_commit_count | 0 |
| diagnosis_pending_potential_concern_count | 30 |

Dashboard artifacts:

- `mimo_v25_realneg_semanticfix1_smoke8_mt7_b4w2_api1_r8t600_20260619_001233_VS_CONTRACTGUARD_DASHBOARD.md`
- `mimo_v25_realneg_semanticfix1_smoke8_mt7_b4w2_api1_r8t600_20260619_001233_AUDIT.json`
- `mimo_v25_realneg_semanticfix1_smoke8_mt7_b4w2_api1_r8t600_20260619_001233_RECOVERY_CASE.md`

Interpretation:

- The local semantic fix is correct but live MiMo did not exercise it.
- `QAAsnSRwgu` did not emit the `we do not evaluate the quality of the output...` evidence item in this run.
- The target quote was present in `_latest_evidence_context_meta.critique_negative_quote_bank`, but targeted negative search selected a `reproducibility_gap` task instead of the available `insufficient_evaluation` quote.
- Strict reviewer-negative mode correctly blocked quote-bank salvage (`strict_reviewer_negative_turn_requires_model_emitted_quote`), so no fake negative was counted.

Current status:

- Fake-negative protection is still working.
- Recovery remains at zero because no verified reviewer-negative evidence reached the state.
- The next bottleneck is targeted-negative task selection/discovery, not semantic verifier acceptance.

## 8.4 Quote-Bank-Guided Targeted Search Fix

Position in the plan:

- This is part of **Task 4: Stop Deterministic Negative Salvage From Creating Evidence** and the evidence-discovery half of **Task 3**.
- It keeps strict salvage blocked: program-extracted quote-bank text still cannot directly become verified negative evidence.
- It only uses true-paper-negative quote-bank entries to tell Evidence Agent what to verify and copy.

Code change:

- Added `_quote_bank_guided_targeted_negative_tasks` in `agent_system/environments/env_package/review/state.py`.
- `_targeted_negative_search_tasks` now prepends quote-bank-guided tasks when the quote bank contains true paper-negative candidates such as `insufficient_evaluation`.
- `_prompt_targeted_negative_tasks` now carries `quote_id`, `candidate_raw_quote`, and `source` into the compact targeted task shown to Evidence Agent.

Safety contract:

```text
quote-bank-guided task != verified evidence
Evidence Agent must still emit:
  claim_id
  quote_id
  raw_quote
  source_locator
  negative_evidence_type
  stance = missing or contradicts
Verifier must still produce:
  paper_grounded_exact
  semantic_negative_verified
  review_negative_verified
```

Local verification:

- `test_targeted_negative_search_tasks_prioritize_true_negative_quote_bank_candidate` passes.
- Replay on the completed `QAAsnSRwgu` state now produces the first targeted task:
  - `source=quote_bank_guided_review_negative_search`
  - `negative_type=insufficient_evaluation`
  - `quote_id=quote-critique-negative-1`
  - `candidate_raw_quote` contains `do not evaluate the quality of the output`.

Next validation:

- Re-run MiMo smoke8 with the same max-turns=7 API config.
- Success is not overall PASS alone. The minimum meaningful sign is that at least the QA quote becomes model-emitted evidence and passes `review_negative_verified`; only after that can recovery produce `mark_contested` or another legitimate operation.

## 8.5 Claim Identity Gate Fix

Position in the plan:

- This is part of **Task 2: real paper claim hygiene** and **Task 5: recovery around verified negative flaws**.
- It fixes the newest live failure mode from `mimo_v25_realneg_quotetask1_smoke8_mt7_b4w2_api1_r8t600_20260619_004444.jsonl`.
- It does not make fake negative evidence easier to count. It makes the binding stricter: context/fallback/recovery scaffolds cannot directly carry final verified negative evidence.

Observed live result:

- MiMo emitted a real reviewer-negative quote for `QAAsnSRwgu`:

```text
Note that we do not evaluate the quality of the output, that is we do not judge if the output is accurate but only focus on whether the expected task has been performed.
```

- The semantic and quote grounding side was promising:
  - `negative_evidence_type=insufficient_evaluation`;
  - `verified_grounding_label=paper_grounded_exact`;
  - `verified_quote_match_type=quote_bank_raw_canonical`;
  - `semantic_grounding_label=semantic_negative_verified`;
  - `review_negative_label=review_negative_verified`.
- But the evidence was bound to `claim-paper-context-2`, whose origin is `context_synthesized`.
- That binding is invalid for the paper narrative: a context scaffold is not a real review target and must not drive final verified negative evidence or recovery.

Root cause:

- `_classify_claim_kind` did not recognize `claim-paper-context-*`, `claim-paper-fallback-*`, or `claim-paper-recovery-*` as scaffold IDs.
- `_real_claim_ids_from_state` could therefore treat a `claim-paper-context-*` item as real if it carried `claim_kind=paper_extracted`.
- Later final-view gates rejected the same item via stricter negative-binding logic, creating an internal mismatch:
  - state-level validation was too permissive;
  - final/recovery gates were stricter;
  - recovery then fell back to `reject_patch` instead of `mark_contested`.
- A separate raw-salvaged fallback claim in the same case contained schema/meta tail text such as `claim_type=...` and `coverage_tags=...`, which blocked clean canonicalization into a natural `claim-*`.

Code change:

- `_classify_claim_kind` now classifies:
  - `claim-paper-context*` as `context_synthesized`;
  - `claim-paper-recovery*` as `recovery_marker`;
  - `claim-paper-fallback*` as `manager_fallback`.
- `_real_claim_ids_from_state` and `_decision_real_claim_ids` now exclude not-assessable claim-gap artifacts.
- Raw-salvaged claim cleanup now strips schema/meta suffixes before deciding whether to canonicalize.
- Clean raw-salvaged paper claims are canonicalized into natural `claim-*` IDs before they can become negative/recovery targets.

Local verification:

- Direct targeted tests passed:
  - `test_raw_salvaged_paper_claim_is_canonicalized_before_negative_binding`;
  - `test_hard_negative_diagnosis_target_gate_rejects_low_quality_fallback_and_leakage`;
  - `test_targeted_negative_search_tasks_use_real_claim_obligations_only`;
  - `test_targeted_negative_search_tasks_prioritize_true_negative_quote_bank_candidate`.
- Manual checks confirmed:
  - `claim-paper-context-2` is `context_synthesized`;
  - `claim-paper-recovery-1` is `recovery_marker`;
  - context/recovery scaffold IDs are not eligible for final negative binding;
  - QA-style raw salvage cleans to a natural paper claim and canonicalizes to a normal `claim-*`.

Recomputed old-run interpretation:

- Recomputing the old `quotetask1` output under the current code correctly stops counting the context-bound QA quote as valid verified negative evidence.
- The old run remains contaminated because it was produced before the canonicalization fix.

Next validation:

- Re-run MiMo v2.5 smoke8 with `max_turns=7`, `api_max_workers=1`, `api_timeout=600`, and `api_max_retries=8`.
- The key check is not only whether the QA quote appears again, but whether it binds to a natural canonical `claim-*` rather than `claim-paper-context-*`.
- If the quote binds correctly, recovery should have a legitimate target for `mark_contested`, downgrade, or limitation routing.

Live validation result:

`mimo_v25_realneg_claimgate1_smoke8_mt7_b4w2_api1_r8t600_20260619_074958.jsonl`

| metric | value |
|---|---:|
| papers | 8 |
| overall protection | PASS |
| real_strong_support_total | 24 |
| negative_evidence_candidate_count | 0 |
| review_negative_verified_count | 0 |
| verified_negative_flaw_count | 0 |
| potential_concern_count | 0 |
| recovery_committed | 0 |
| mark_contested_commit_count | 0 |

Interpretation:

- The run did **not** restore true reviewer-discovered negative evidence or recovery.
- It did confirm the safety side: context-bound/fallback/prompt-echo negative-looking text was not counted as verified negative evidence.
- For `QAAsnSRwgu`, the targeted negative turn still failed before verification:
  - Evidence Agent returned prompt/schema echo instead of valid JSON;
  - fallback converted this into `not_assessable`;
  - strict reviewer-negative mode correctly blocked quote-bank salvage.
- The target quote was visible in the prompt quote bank, but the active task was still a generic `claim_evidence_obligation` with empty `quote_id` and empty `candidate_raw_quote`.

Root cause refinement:

- Targeted tasks were built before the current Evidence context/quote bank was rendered.
- Therefore a newly discovered true-paper-negative quote could appear in `Evidence Quote Bank` but not in `targeted_negative_search_active_tasks`.
- This made the model infer the task instead of copying a specific quote, increasing JSON/prompt echo failure and preventing verified negative formation.

Code change:

- `render_evidence_observation` now refreshes targeted negative tasks after current `evidence_context_meta` is available.
- Quote-guided tasks now use current-turn `critique_negative_quote_bank` immediately.
- Quote-guided claim selection now adds type-aware bias:
  - `insufficient_evaluation`, `result_claim_mismatch`, and `negative_result` prefer empirical/comparison/output-quality claims;
  - baseline gaps prefer empirical/comparison claims;
  - ablation gaps prefer empirical/method component claims.

Local replay after the fix:

- Replaying the `QAAsnSRwgu` pre-targeted state now produces an active task with:
  - `claim_id=claim-an-empirical-claim-from-the-resu`;
  - `quote_id=quote-critique-negative-1`;
  - `negative_type=insufficient_evaluation`;
  - `candidate_raw_quote` containing `do not evaluate the quality of the output`.

Next validation:

- Re-run MiMo v2.5 smoke8.
- Minimum success is no longer just seeing the quote in the quote bank. The model must emit it in `evidence_map` with the natural empirical claim id and pass `review_negative_verified`.

## 2026-06-19 QUOTEACTIVE1 Result and Follow-up Fix

Validation run:

`mimo_v25_realneg_quoteactive1_smoke8_mt7_b4w2_api1_r8t600_20260619_082200.jsonl`

| metric | CONTRACTGUARD | QUOTEACTIVE1 |
|---|---:|---:|
| overall protection | PASS | PASS |
| real_strong_support_total | 38 | 18 |
| negative_evidence_candidate_count | 0 | 0 |
| review_negative_verified_count | 0 | 0 |
| verified_negative_flaw_count | 0 | 0 |
| potential_concern_count | 0 | 0 |
| recovery_committed | 0 | 0 |
| mark_contested_commit_count | 0 | 0 |
| diagnosis_pending_potential_concern_count | 23 | 37 |

Interpretation:

- The safety side held: unlinked negative evidence, neutral/positive negative candidates, and overclaim contamination stayed at 0.
- The paper-review narrative target was **not** met: no reviewer-discovered negative evidence and no recovery lifecycle were restored.
- Positive support regressed sharply (`real_strong_support_total` 38 -> 18), so this version cannot be frozen.

New failure diagnosis:

1. `QAAsnSRwgu` and `WLgbjzKJkk` had no real negative-search target because Claim Agent JSON was malformed/truncated, even though the raw output contained real `claim-1/2/3/4` objects.
2. Fallback skipped those complete raw claim objects and instead synthesized `claim-paper-context-*` claims from excerpts.
3. `targeted_negative_search` correctly excludes context claims, so QA never reached the quote-guided negative task path.
4. In the 6 papers that did trigger targeted search, active tasks were still abstract `claim_evidence_obligation` items with empty `quote_id` / `candidate_raw_quote`. These tasks ask Evidence Agent to infer requirement gaps, but the verifier requires a copied negative quote, so they mostly produced prompt/schema echo or `not_assessable`.

Follow-up code change:

- Claim fallback now first recovers complete claim objects from malformed/truncated raw JSON before falling back to context-derived claims.
- Raw-salvaged claims are still canonicalized into natural `claim-*` ids before they can become negative/recovery targets.
- Evidence targeted-negative tasks are now quote-guided only. Requirement gaps without a concrete candidate quote remain diagnosis-pending potential concerns, not Evidence Agent negative-search tasks.

Local verification:

- Direct tests passed:
  - `test_claim_fallback_salvages_complete_claim_objects_from_truncated_raw_json`;
  - `test_raw_salvaged_paper_claim_is_canonicalized_before_negative_binding`;
  - `test_hard_negative_diagnosis_target_gate_rejects_low_quality_fallback_and_leakage`;
  - `test_targeted_negative_search_tasks_skip_claim_obligations_without_quote_candidate`;
  - `test_targeted_negative_search_tasks_prioritize_true_negative_quote_bank_candidate`.
- Offline replay using the failed `QAAsnSRwgu` raw output now recovers 4 natural raw-salvaged `claim-*` claims.
- Offline replay on the actual QA paper now produces a quote-guided task:
  - `source=quote_bank_guided_review_negative_search`;
  - `claim_id=claim-the-proposed-hive-system-is-expe`;
  - `quote_id=quote-critique-negative-1`;
  - `negative_type=insufficient_evaluation`;
  - `candidate_raw_quote` contains `do not evaluate the quality of the output`.

Next validation:

- Re-run MiMo v2.5 smoke8 with `DRMAS_NEG_QUOTE_HYGIENE=1 DRMAS_TARGETED_NEGATIVE_SEARCH=1`.
- Minimum success for this stage:
  - QA targeted task must be quote-guided, not `claim_evidence_obligation`;
  - Evidence Agent must emit the candidate quote in `evidence_map`;
  - the emitted item must bind to a natural `claim-*` and pass `review_negative_verified`;
  - only then should recovery be expected to form `mark_contested`, downgrade, or limitation routing.

## 2026-06-19 CLAIMRAW1 Result and Partial-Claim Salvage Fix

Validation run:

`mimo_v25_realneg_claimraw1_smoke8_mt7_b4w2_api1_r8t600_20260619_101941.jsonl`

| metric | CONTRACTGUARD | CLAIMRAW1 |
|---|---:|---:|
| overall protection | PASS | PASS |
| real_strong_support_total | 38 | 28 |
| zero_real_papers | 1 | 1 |
| negative_evidence_candidate_count | 0 | 0 |
| review_negative_verified_count | 0 | 0 |
| verified_negative_flaw_count | 0 | 0 |
| recovery_committed | 0 | 0 |
| diagnosis_pending_potential_concern_count | 23 | 32 |
| state_contamination_count | 1 | 1 |

Interpretation:

- The previous support collapse improved materially (`real_strong_support_total` 18 -> 28), and the fake-negative guards still held.
- The core target still failed: no reviewer-discovered negative evidence and no recovery lifecycle.
- QA still did not enter targeted negative search in the actual run because the first Claim Agent response was truncated in the third claim object. The fallback salvaged only context claims plus one later method claim, leaving no empirical comparison claim for the QA negative quote.

New root cause:

- The malformed Claim Agent raw contained complete `claim-1` and `claim-2`, and a mostly complete `claim-3`.
- `claim-1/2` were incorrectly rejected by raw-salvage meta filtering because their legitimate paper text contained `user instructions` / `user inputs`.
- `claim-3` was not recovered because the object was truncated after `coverage_tags`, even though `claim_id`, `claim`, `claim_type`, and `evidence_need` were already complete.

Code change:

- Structured raw-claim salvage no longer treats the bare word `user` as prompt/meta leakage. It rejects only explicit meta phrases such as `the user asked`, `review task`, `json`, `schema`, `prompt`, or agent-role text.
- Raw salvage now also recovers partial claim objects from malformed JSON segments when `claim_id` and `claim` are complete.

Local verification:

- The actual `QAAsnSRwgu` CLAIMRAW1 raw now salvages:
  - `claim-1`: contribution claim about the Hive/PDDL multi-agent framework;
  - `claim-2`: method claim about hierarchical PDDL domain classification and merging;
  - `claim-3`: empirical comparison claim against HuggingGPT and ControlLLM.
- Offline replay on the actual QA paper now creates:
  - `source=quote_bank_guided_review_negative_search`;
  - `claim_id=claim-the-proposed-method-is-compared-`;
  - `negative_type=insufficient_evaluation`;
  - `quote_id=quote-critique-negative-1`;
  - `candidate_raw_quote=Note that we do not evaluate the quality of the output...`.

Next validation:

- Re-run MiMo v2.5 smoke8 (`CLAIMRAW2`).
- This run should prove whether the Evidence Agent will emit the QA quote in `evidence_map`; if it still returns prompt/schema echo or `not_assessable`, the next fix should target the targeted Evidence prompt/output contract, not claim salvage.

## 2026-06-19 CLAIMRAW2 Result and Evidence-JSON Reliability Pivot

Validation run:

`mimo_v25_realneg_claimraw2_smoke8_mt7_b4w2_api1_r8t600_20260619_104504.jsonl`

| metric | CONTRACTGUARD | CLAIMRAW2 |
|---|---:|---:|
| overall protection | PASS | PASS |
| real_strong_support_total | 38 | 32 |
| empirical_real_strong_support_count | 30 | 25 |
| negative_evidence_candidate_count | 0 | 0 |
| review_negative_verified_count | 0 | 0 |
| verified_negative_flaw_count | 0 | 0 |
| recovery_committed | 0 | 0 |
| evidence_json_valid_turns | 1 | 0 |
| evidence_json_partial_recovered_turns | 1 | 0 |
| evidence_json_fallback_turns | 37 | 32 |
| evidence_json_fallback_rate_pct | 95 | 100 |
| evidence_json_no_json_object_turns | 20 | 15 |
| evidence_json_invalid_json_turns | 17 | 13 |
| evidence_json_truncated_turns | 0 | 4 |

Interpretation:

- The raw-claim salvage fix worked for the QA case: the final state now contains natural `claim-1/2/3` paper-extracted claims, including the empirical comparison claim against HuggingGPT and ControlLLM.
- CLAIMRAW2 did **not** actually test the targeted quote-search route, because the run was launched without `DRMAS_TARGETED_NEGATIVE_SEARCH=1`. All eight papers had `targeted_negative_search_required=false`.
- Independent of that launch mistake, Claude's broader audit is directionally correct: the Evidence Agent output contract is currently the upstream bottleneck. CLAIMRAW2 had 32 evidence JSON status turns and all 32 fell back; no clean model-emitted evidence payload reached the negative verifier.
- Positive support can still appear because quote-bank/first-support fallback salvages support evidence. True reviewer-negative evidence intentionally has no equivalent quote-bank auto-salvage, so it remains zero when the model fails to emit clean JSON.

Current decision:

- Freeze further downstream negative/recovery tuning until Evidence Agent JSON reliability is visible and improved.
- Keep the fake-negative guards: do not count paper-text extraction, author limitation, prior-work limitation, positive/neutral prose, fallback/context claims, or quote-bank auto-salvage as verified reviewer-negative evidence.
- Add evidence JSON health metrics to dashboard so every future smoke/full run reports `evidence_json_valid_turns`, `evidence_json_fallback_turns`, fallback rate, and failure types.

Next validation:

- Re-run MiMo v2.5 smoke8 with `DRMAS_NEG_QUOTE_HYGIENE=1 DRMAS_TARGETED_NEGATIVE_SEARCH=1`.
- Raise `max_tokens` from 768 to at least 1536 for this diagnostic run to test whether the high fallback rate is token-budget/output-truncation limited.
- Acceptance for this stage is not just higher reward. Required signals:
  - evidence JSON fallback rate must drop materially from 95-100%;
  - targeted turns must actually appear in turn logs;
  - QA or another paper must emit a model-produced `evidence_map` item with copied quote, locator, real `claim-*`, negative type, and no prompt/schema echo;
  - only then should `review_negative_verified` and recovery (`mark_contested`, downgrade, limitation) be interpreted.
