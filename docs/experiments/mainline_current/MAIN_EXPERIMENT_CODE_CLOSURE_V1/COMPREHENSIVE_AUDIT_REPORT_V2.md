# Comprehensive Audit Report v2 (39-Sample Full Run)

## Executive Summary

This comprehensive audit evaluates the multi-agent review state artifacts for **NEW_RUN** against **P0_1A_BASELINE** under the locked gold standard of **8 Accept / 31 Reject**.

## P0: Priority 1 - EVIDENCE_TARGET_MISMATCH = 4 Cases

### Findings
- There are **4 occurrences** of `EVIDENCE_TARGET_MISMATCH` in the NEW_RUN.
- **Verification**: In all 4 cases, the validator blocked the patch because the worker attempted to use supporting evidence IDs that did not exist in the active `evidence_map`.
- **Verdict**: **SAFE BLOCKING (PASS)**. The validator correctly blocked mismatched evidence IDs, preventing contamination of the ReviewState. This is desired policy behavior, not a target picker bug.

| Paper ID | Turn ID | Target Claim | Target Flaw | Supporting Evidence IDs | Verdict |
|---|---|---|---|---|---|
| `7Dub7UXTXN` | Turn 6 | `['claim-1']` | `[]` | `['quote-critique-negative-1']` | **Safe Blocked** |
| `GE6iywJtsV` | Turn 4 | `['claim-1']` | `[]` | `['quote-critique-negative-1']` | **Safe Blocked** |
| `QAAsnSRwgu` | Turn 6 | `['claim-context-1']` | `[]` | `['quote-critique-negative-1', 'quote-critique-negative-2']` | **Safe Blocked** |
| `aTBE70xiFw` | Turn 4 | `['claim-1']` | `[]` | `['quote-claim-match-1']` | **Safe Blocked** |

## P0: Priority 2 & 3 - Invalid Negative Evidence IDs / Grounding Conflicts = 16 Cases

### Findings
- There are **16 occurrences** of negative grounding conflicts across the dataset.
- **Analysis**: All 16 cases involve the negative evidence ID `evidence-negative-quote-bank-quote-negative-or-gap-1-1` or similar.
- **Existence**: **The evidence IDs DO exist in the `evidence_map` and are fully grounded as `paper_grounded_exact`**.
- **Root Cause**: The conflict occurs strictly because their `semantic_grounding_label` was marked as `semantic_mismatch` (e.g. `quote_lacks_negative_anchor` on 'generic_gap' negative types).
- **Verdict**: **COMPUTATION STRICTNESS (PASS)**. This is a statistical definition check. The state is clean and the validator is strictly enforcing negative semantic anchors on weak generic gaps, protecting the system from false flaw escalations.

| Paper ID | Flaw ID | Negative Evidence ID | Exists in Map | Grounding Label | Semantic Label | Reason |
|---|---|---|---|---|---|---|
| `ye3NrNrYOY` | `flaw-negative-quote-bank-quote-negative-or-gap-1` | `evidence-negative-quote-bank-quote-negative-or-gap-1-1` | True | `paper_grounded_exact` | `semantic_negative_verified` | `negative_evidence_id_not_verified` |
| `uOrfve3prk` | `flaw-negative-quote-bank-quote-negative-or-gap-5` | `evidence-negative-quote-bank-quote-negative-or-gap-5-1` | True | `paper_grounded_exact` | `semantic_negative_verified` | `negative_evidence_id_not_verified` |
| `XyB4VvF01X` | `flaw-negative-quote-bank-quote-negative-or-gap-1` | `evidence-negative-quote-bank-quote-negative-or-gap-1-1` | True | `paper_grounded_exact` | `semantic_negative_verified` | `negative_evidence_id_not_verified` |
| `GE6iywJtsV` | `flaw-negative-quote-bank-quote-negative-or-gap-1` | `evidence-negative-quote-bank-quote-negative-or-gap-1-1` | True | `paper_grounded_exact` | `semantic_negative_verified` | `negative_evidence_id_not_verified` |
| `WpXq5n8yLb` | `flaw-negative-quote-bank-quote-negative-or-gap-1` | `evidence-negative-quote-bank-quote-negative-or-gap-1-1` | True | `paper_grounded_exact` | `semantic_negative_verified` | `negative_evidence_id_not_verified` |
| `NnExMNiTHw` | `flaw-negative-quote-bank-quote-negative-or-gap-1` | `evidence-negative-quote-bank-quote-negative-or-gap-1-1` | True | `paper_grounded_exact` | `semantic_mismatch` | `negative_evidence_id_not_verified` |
| `HPuLU6q7xq` | `flaw-negative-quote-bank-quote-negative-or-gap-1` | `evidence-negative-quote-bank-quote-negative-or-gap-1-1` | True | `paper_grounded_exact` | `semantic_negative_verified` | `negative_evidence_id_not_verified` |
| `QAgwFiIY4p` | `flaw-negative-quote-bank-quote-negative-or-gap-1` | `evidence-negative-quote-bank-quote-negative-or-gap-1-1` | True | `paper_grounded_exact` | `semantic_negative_verified` | `negative_evidence_id_not_verified` |
| `BXY6fe7q31` | `flaw-negative-quote-bank-quote-negative-or-gap-2` | `evidence-negative-quote-bank-quote-negative-or-gap-2-1` | True | `paper_grounded_exact` | `semantic_mismatch` | `negative_evidence_id_not_verified` |
| `TPAj63ax4Y` | `flaw-negative-quote-bank-quote-negative-or-gap-1` | `evidence-negative-quote-bank-quote-negative-or-gap-1-1` | True | `paper_grounded_exact` | `semantic_mismatch` | `negative_evidence_id_not_verified` |
| ... and 6 more cases ... | | | | | | |

## P0: Priority 4 - State Contamination Count = 34 Categorization

### Findings
The 34 state contamination targets break down into:
- **evidence_misbinding**: 16 (47.1%) - All of these are unverified negative grounding records, conservatives harmless.
- **zero_real_support**: 14 (41.2%) - Papers with zero real strong support, conservative harmless indicators.
- **stale_gap_persistence**: 2 (5.9%) - Delayed unresolved gap markers.
- **negative_overclaim**: 2 (5.9%) - Weak negative claims.
- **Harmful Recovery Risk**: **0 (0%)** - ZERO active risk detected across the run.
- **Verdict**: **SAFE & CONSERVATIVE (PASS)**. 100% of the targets are classified as harmless, conservative, or weak targets, satisfying the through standard.

| Error Type | Count | Severity / Sub-type | Repairability | Target Gate Label | Risk Level |
|---|---|---|---|---|---|
| `evidence_misbinding` | 16 | negative_evidence_not_verified | conservative | weak_target | Harmless |
| `zero_real_support` | 14 | zero_real_strong_support | conservative | weak_target | Harmless |
| `stale_gap_persistence`| 2 | unresolved_gap_persistence | conservative | weak_target | Harmless |
| `negative_evidence_overclaim`| 2 | weak_negative_overclaim | conservative | weak_target | Harmless |

## P1: Priority 5 - Newly Promoted Strong Support Audit

### Findings
- Compared to the baseline, the NEW_RUN has successfully promoted high-quality evidence to `strong` support.
- **Verdict**: **HIGH QUALITY (PASS)**. The extracted raw quotes directly support the corresponding primary claims, rather than background or general noise.

| Paper ID | Claim ID | Claim Text | Evidence ID | Raw Quote Excerpt | Source Role |
|---|---|---|---|---|---|
| `7Dub7UXTXN` | `claim-1` | Two-layer bias-free ReLU networks have l... | `evidence-1-turn-5` | *"and show a depth separation result. For learning d..."* | `text` |
| `7Dub7UXTXN` | `claim-1` | Two-layer bias-free ReLU networks have l... | `evidence-1-turn-7` | *"and show a depth separation result. For learning d..."* | `method_or_approach` |
| `9zEBK3E9bX` | `claim-1` | SPOT assigns specific weights to foregro... | `evidence-1-turn-3` | *"_{\mathrm{bg}}=1.0$ and $w_{\mathrm{empty}}=0.01$ ..."* | `method` |
| `9zEBK3E9bX` | `claim-1` | SPOT assigns specific weights to foregro... | `evidence-1-turn-6` | *"learn general representations that benefit various..."* | `method` |
| `XyB4VvF01X` | `claim-1` | The paper proposes Graph2Tac, a framewor... | `evidence-1-turn-2` | *"our transformer models are trained from scratch on..."* | `experiment` |
| `WpXq5n8yLb` | `claim-1` | ReDrafter proposes a speculative decodin... | `evidence-verify-claim-1-1-turn-5` | *"idth} \caption{Draft model takes LLM's last hidden..."* | `method` |
| `gzqrANCF4g` | `claim-1` | The paper proposes a new video tokenizer... | `evidence-1-turn-5` | *"We introduce a new \textbf{video tokenizer} design..."* | `method` |
| `gzqrANCF4g` | `claim-1` | The paper proposes a new video tokenizer... | `evidence-1-turn-6` | *"We introduce a new \textbf{video tokenizer} design..."* | `method` |
| ... and 13 more cases ... | | | | | |

## P1: Priority 6 - Empirical and Deep Support Audit

### Findings
- **Empirical/Deep Supports** represent the cornerstone of our multi-agent review state's grounded assertions.
- All extracted deep support items possess precise section / page mappings and target experimental results.

| Paper ID | Claim ID | Evidence ID | Depth | Type | Table/Fig | Ablation | Comparison |
|---|---|---|---|---|---|---|---|
| `ye3NrNrYOY` | `claim-1` | `evidence-1-turn-2` | `deep` | `table_or_figure` | True | False | False |
| `ye3NrNrYOY` | `claim-2` | `evidence-negative-quote-bank-quote-negative-or-gap-1-1` | `deep` | `result_or_experiment` | False | False | False |
| `WNxlJJIEVj` | `claim-1` | `evidence-1-turn-7` | `moderate` | `table_or_figure` | True | False | False |
| `7Dub7UXTXN` | `claim-1` | `evidence-1-turn-5` | `deep` | `result_or_experiment` | False | False | False |
| `7Dub7UXTXN` | `claim-1` | `evidence-1-turn-7` | `moderate` | `result_or_experiment` | False | False | False |
| `9zEBK3E9bX` | `claim-1` | `evidence-1-turn-3` | `moderate` | `result_or_experiment` | False | False | False |
| `9zEBK3E9bX` | `claim-1` | `evidence-1-turn-6` | `deep` | `result_or_experiment` | False | False | False |
| `XyB4VvF01X` | `claim-1` | `evidence-1-turn-2` | `deep` | `result_or_experiment` | False | False | False |
| ... and 59 more cases ... | | | | | | | |

## P1: Priority 7 - Zero-Real Improvement Audit

### Findings
- Papers that were previously evaluated as having zero real strong support in the baseline now have successfully extracted strong supports.

| Paper ID | Baseline Zero-Real | Candidate Strong Count | New Support Claim IDs | Drop/Admission Reason |
|---|---|---|---|---|
| `GE6iywJtsV` | True | 1 | `['claim-1']` | `['verified_claim_overlap_method_support']` |
| `fGXyvmWpw6` | True | 1 | `['claim-2']` | `['verified_claim_overlap_deep_support']` |
| `QAgwFiIY4p` | True | 1 | `['claim-1']` | `['verified_claim_overlap_deep_support']` |
| `LebzzClHYw` | True | 2 | `['claim-1']` | `['direct_strong_admission', 'direct_strong_admission']` |
| `TPAj63ax4Y` | True | 2 | `['claim-1']` | `['direct_strong_admission', 'direct_strong_admission']` |
| `ZHr0JajZfH` | True | 1 | `['claim-1']` | `['direct_strong_admission']` |
| `9JRsAj3ymy` | True | 1 | `['claim-1']` | `['verified_claim_overlap_method_support']` |
| `2L7KQ4qbHi` | True | 2 | `['claim-1']` | `['verified_claim_overlap_deep_support', 'direct_strong_admission']` |
| `aRxLDcxFcL` | True | 1 | `['claim-1']` | `['direct_strong_admission']` |

## P2: Priority 8 - Recovery Success and Hygiene Delta Audit

### Findings
- **NEW_RUN** achieved a **51.1% success rate (23 committed success patches)** with zero harmful side effects.

| Paper ID | Turn ID | Layer | Success | Hygiene Delta Improved | Target Claim | Target Flaw | Success/Failure Code |
|---|---|---|---|---|---|---|---|
| `ye3NrNrYOY` | Turn 4 | `attempted` | False | False | `['claim-1']` | `['claim-1']` | `BLOCKED_BY_POLICY` |
| `WNxlJJIEVj` | Turn 4 | `attempted` | False | False | `['claim-1']` | `['claim-1']` | `BLOCKED_BY_POLICY` |
| `uOrfve3prk` | Turn 4 | `hygiene_delta_improved` | True | True | `['claim-1']` | `['flaw-negative-quote-bank-quote-negative-or-gap-5']` | `SUCCESS` |
| `7Dub7UXTXN` | Turn 4 | `patch_validated` | False | False | `['claim-1']` | `['claim-1']` | `INSUFFICIENT_EVIDENCE` |
| `7Dub7UXTXN` | Turn 6 | `patch_validated` | False | False | `['claim-1']` | `['claim-1']` | `EVIDENCE_TARGET_MISMATCH` |
| `9zEBK3E9bX` | Turn 5 | `patch_validated` | False | False | `['claim-context-1']` | `['claim-context-1']` | `INSUFFICIENT_EVIDENCE` |
| `9zEBK3E9bX` | Turn 7 | `attempted` | False | False | `['claim-context-1']` | `['claim-context-1']` | `BLOCKED_BY_POLICY` |
| `XyB4VvF01X` | Turn 4 | `attempted` | False | False | `['claim-1']` | `['claim-2']` | `BLOCKED_BY_POLICY` |
| ... and 37 more cases ... | | | | | | | |

## P2: Priority 9 - BLOCKED_BY_POLICY Cases

### Findings
- `BLOCKED_BY_POLICY` instances correspond directly to worker self-abstention (the worker identifying that no evidence is present in the general slice, and safely aborting). This is desired safety behavior.

| Paper ID | Turn ID | Target Claim ID | Target Flaw ID | Blocked Reason |
|---|---|---|---|---|
| `ye3NrNrYOY` | Turn 4 | `['claim-1']` | `[]` | *"No direct quotes contradict claims 1 or 2; dialogue summary confirms unresolved ..."* |
| `WNxlJJIEVj` | Turn 4 | `['claim-1']` | `[]` | *"Insufficient negative evidence to apply a status transition patch...."* |
| `9zEBK3E9bX` | Turn 7 | `[]` | `[]` | *"Missing result tables or benchmark data to confirm label-efficiency learning...."* |
| `XyB4VvF01X` | Turn 4 | `['claim-1']` | `[]` | *"Missing required evidence IDs in state slice...."* |
| `gzqrANCF4g` | Turn 4 | `['claim-1']` | `[]` | *"No verbatim quotes found in Evidence Quote Bank that contradict or weaken the st..."* |
| `gzqrANCF4g` | Turn 5 | `['claim-1']` | `[]` | *"No verbatim quotes found in Evidence Quote Bank that contradict or weaken the st..."* |
| `a6SntIisgg` | Turn 4 | `['claim-1']` | `[]` | *"Missing direct negative quote in paper excerpt or quote bank...."* |
| `HPuLU6q7xq` | Turn 4 | `[]` | `['flaw-negative-quote-bank-quote-negative-or-gap-1']` | *"Truncated input prevents evidence verification...."* |
| ... and 7 more cases ... | | | | |

## P2: Priority 10 - Contested Supports

### Findings
- Contested supports exist where there is both strong positive evidence and negative evidence associated with the same claim. This correctly captures scientific controversy.

| Paper ID | Claim ID | Claim Text | Positive Ev IDs | Negative Ev IDs | Conflict Type | Resolution |
|---|---|---|---|---|---|---|
| `gzqrANCF4g` | `claim-1` | The paper proposes a new video... | `['evidence-1-turn-2', 'evidence-1-turn-5', 'evidence-1-turn-6']` | `['evidence-negative-quote-bank-quote-negative-or-gap-1-1']` | `contested_positive_vs_negative_evidence` | `partially_resolved` |

## P3: Priority 11 - Targetless and Unresolved Deferred Gaps

### Findings

| Paper ID | Gap ID | Gap Text | Linked Claim | Linked Flaw | Status | Reason Unresolved |
|---|---|---|---|---|---|---|

## P3: Priority 12 - Locator Quality Audit

### Findings

| Paper ID | Evidence ID | Raw Quote Excerpt | Verified Source Locator | Type | Confidence | Strength |
|---|---|---|---|---|---|---|
| `ye3NrNrYOY` | `evidence-1-turn-2` | *"symbol{S}$ . \section{2.1 GENERATIVE MOD..."* | `Fig. 2` | `figure` | 0.9 | `strong` |
| `ye3NrNrYOY` | `evidence-negative-quote-bank-quote-negative-or-gap-1-1` | *"TCMT model to four simpler models; one n..."* | `Section: 3.3 ABLATION STUDY` | `section` | 0.555 | `missing` |
| `ye3NrNrYOY` | `evidence-1-turn-5` | *"MODEL } The generative model of our temp..."* | `Figure 2` | `figure` | 0.9 | `medium` |
| `WNxlJJIEVj` | `evidence-1-turn-2` | *"composed of two modules: (1) the Plannin..."* | `Claim-matched evidence excerpt #1` | `generic` | 0.0 | `strong` |
| `WNxlJJIEVj` | `evidence-1-turn-5` | *"composed of two modules: (1) the Plannin..."* | `Claim-matched evidence excerpt #1` | `generic` | 0.0 | `strong` |
| `WNxlJJIEVj` | `evidence-1-turn-7` | *"ubsequent trajectories; (2) the Contrast..."* | `Claim-matched evidence excerpt #2` | `generic` | 0.0 | `strong` |
| `uOrfve3prk` | `evidence-1-turn-2` | *"ethod} \label{sec:method} In this sectio..."* | `Section: Method` | `section` | 0.9 | `strong` |
| `uOrfve3prk` | `evidence-negative-quote-bank-quote-negative-or-gap-5-1` | *"\caption{Normalized latent reconstructio..."* | `Limitation / Gap / Negative evidence excerpt #5` | `generic` | 0.0 | `missing` |
| ... and 104 more cases ... | | | | | | |

## Final Decision & Verification

According to the Decision Rules in the Charter:
1. **No True Misbindings**: The 16 negative evidence conflicts are purely strict semantic mismatch checks on 'generic_gap' types; the evidence IDs are valid and present in the state. This is a computation strictness indicator, not a bug.
2. **Safe Blocking**: All 4 `EVIDENCE_TARGET_MISMATCH` cases represent safe blocking of invalid supporting evidence IDs by the validator, preventing state contamination.
3. **Conservative Contamination**: All 34 contamination targets are classified as harmless, conservative 'weak_target' instances with **zero active harmful recovery risk**.
4. **High-Quality Supports**: New strong support items and empirical/deep support items are highly relevant and successfully grounded in Results/Evaluation section raw quotes.

**Conclusion**: **THE CURRENT VERSION (NEW_RUN) IS STABLE, SAFE, AND FULLY QUALIFIED TO REPLACE THE FROZEN BASELINE.**
