# State Hygiene Next Decision

**Base branch**: `codex/p25-1-explicit-mainline`  
**Baseline**: `p25.1 + explicit recovery phase`  
**Fast check model**: 4B only for this stage.

## 1. Current Finding

The new 4B state-hygiene focus run confirms the same structural failure mode as the 39-sample full-test audit: the system still predicts reject for every sample.

| scope | samples | predicted accept | predicted reject | accept recall | reject recall |
|---|---:|---:|---:|---:|---:|
| 4B focus set | 16 | 0 | 16 | 0.0000 | 1.0000 |

This should not be interpreted as a model-size comparison. The useful conclusion is that final decision is still dominated by reject-side blockers even when the run is reduced to a targeted state-hygiene subset.

## 2. Why Simple State Hygiene Is Not Enough Yet

Existing offline simulation on the 39-sample mainline already showed that these isolated fixes produced zero decision flips:

- Claim-evidence reconciliation.
- Stale evidence gap cleanup.
- Meta/excerpt flaw filtering.
- Candidate flaw half weighting or grounded-only counting.
- Liberal unresolved cleanup combined with the above.

The 4B focus run explains why: blocker counts remain high at the final decision interface.

| blocker | affected samples in 4B focus |
|---|---:|
| `unresolved>=6` | 14 |
| `strong<2` | 12 |
| `critical>=1` | 8 |
| `unresolved>3_blocks_accept` | 4 |
| `major>0_blocks_accept` | 2 |
| `major>=2` | 2 |

So the next step is not another recovery controller. The next step is to make the final decision interface measurable and hygiene-aware offline first.

## 3. Recovery Positioning

Recovery should remain in the system as a structured module: phase, patch, validation, commit, blocked/no-effect logging are already useful. However, recovery is still operating over dirty state:

- `unsupported_with_strong_support=11` on the 4B focus set.
- `stale_evidence_gap=8`.
- `ungrounded_flaw=14`.
- `unresolved_count=126`.

Therefore recovery commits should no longer be counted as success by count alone. The next recovery metric should be whether state consistency improves after recovery.

## 4. Next Single Cut

Do **not** implement a new runtime controller yet. The next single cut should be:

**Decision Interface Hygiene Simulation v1**

This is offline and 4B-fast. It should test final-decision variants without changing runtime behavior:

1. Count only confirmed or grounded flaws as hard blockers.
2. Treat candidate flaws as soft blockers unless they are evidence-grounded.
3. Remove or resolve unresolved questions that are stale relative to strong support.
4. Add a consistency guard: unsupported claims with >=2 strong support and no grounded contradiction cannot contribute negative support.
5. Report accept recall, reject recall, macro-F1, and stable reject control safety.

## 5. Go / No-Go

Go to minimal runtime state hygiene only if offline simulation satisfies all of these:

- Accept recall becomes non-zero.
- Stable reject controls do not collapse into false accepts.
- `unresolved>=6`, `critical>=1`, or `strong<2` blockers are reduced for the right cases.
- The rule improves state consistency, not just the final label.

If these do not hold, the issue is deeper: evidence extraction, unresolved lifecycle, flaw lifecycle, and final decision policy need to be diagnosed separately before runtime edits.


## 6. Decision Interface Simulation v1 Result

The 4B/offline decision-interface simulation confirms that isolated hygiene edits are not enough, but also identifies the next narrow target.

| variant | accept recall | reject recall | recovered accept | false accept | interpretation |
|---|---:|---:|---:|---:|---|
| `DI1_grounded_flaw_only` | 0.0000 | 1.0000 | 0 | 0 | Grounding flaw blockers alone does not break reject collapse. |
| `DI2_grounded_flaw_stale_cleanup` | 0.0000 | 1.0000 | 0 | 0 | Stale gap/unresolved cleanup helps blocker counts but still no accept recovery. |
| `DI3_balanced_hygiene` | 0.1111 | 0.8571 | 1 | 1 | Non-oracle recovery is possible but unsafe: one reject control flips false accept. |
| `DI4_confirmed_only_flaw` | 0.0000 | 1.0000 | 0 | 0 | Confirmed-only flaw counting is still dominated by unresolved/strong-support blockers. |
| `DI_ORACLE_no_candidates_no_unresolved` | 0.2222 | 1.0000 | 2 | 0 | Upper bound says candidate/unresolved lifecycle is the real lock, not just final label policy. |

### Updated conclusion

Do not implement a runtime final-decision relaxation yet. The only non-oracle variant that recovers accept also creates a false accept. The safe signal is narrower: oracle cleanup works only when candidate flaws and unresolved questions are removed together, which means the next engineering cut should focus on **unresolved/candidate lifecycle hygiene**, not broad decision-threshold relaxation.

### Next single cut

**Unresolved + Candidate Lifecycle Audit v1** should be the next step. It must remain offline first and answer:

1. Which unresolved questions are stale/generic/system-generated versus genuinely paper-blocking?
2. Which candidate flaws are ungrounded/meta versus grounded and decision-relevant?
3. Which cleanup rules recover `QAAsnSRwgu` and `KI9NqjLVDT` without flipping `aTBE70xiFw` or the stable reject controls?

Only after that should we implement runtime cleanup. Claim-evidence reconciliation and stale gap cleanup remain useful for state consistency, but they are not sufficient as the first runtime fix.

## 7. Lifecycle Audit Update

The unresolved/candidate lifecycle audit makes the diagnosis sharper:

| signal | value |
|---|---:|
| open unresolved | 126 |
| grounded paper unresolved | 1 |
| weak/system unresolved | 125 |
| candidate flaws | 20 |
| grounded candidates | 6 |
| ungrounded candidates | 14 |
| candidates used for reject | 19 |
| confirmed flaws | 1 |
| downgraded/retracted flaws | 0 |

A naive lifecycle cleanup (`DI5_lifecycle_cleanup`) is not safe: it recovers 0 accept and false-accepts `aTBE70xiFw`. Therefore the next runtime change should still be deferred. The next step is a more precise offline rule design for provenance-aware lifecycle transitions, not broad deletion/downgrade.

### Revised next single cut

**Lifecycle Provenance Rule Simulation v1**:

- Add offline rules that classify unresolved items as `paper_blocking`, `system_uncertainty`, `review_limitation`, or `duplicate/stale`.
- Add offline rules that classify candidate flaws as `grounded_candidate`, `ungrounded_candidate`, `system_meta_candidate`, or `confirmed_grounded_flaw`.
- Simulate final decision using only `paper_blocking` unresolved items and `confirmed/grounded` flaws as hard blockers.
- The rule must recover `QAAsnSRwgu` or `KI9NqjLVDT` without flipping `aTBE70xiFw` or stable reject controls.

## 8. Lifecycle Provenance Rule Simulation v1 Result

A more precise provenance simulation was run after the lifecycle audit. It tested rules that close system/generic unresolved items, downgrade meta/ungrounded candidate flaws, and combine these with claim/evidence reconciliation.

Result: **no non-oracle rule recovered accept safely**.

| rule family | recovered accept | false accept | conclusion |
|---|---:|---:|---|
| grounded-only decision | 0 | 0 | No positive recovery; still all reject. |
| close system/generic unresolved | 0 | 1 | Unsafe; flips `aTBE70xiFw`. |
| downgrade ungrounded/meta candidates | 0 | 0 | No positive recovery. |
| targeted lifecycle + reconcile | 0 | 1 | Unsafe; same false accept. |

### Updated diagnosis

The lifecycle collapse diagnosis is still correct, but cleanup-only rules are not sufficient. The accept samples do not merely need negative objects removed; they also need stronger positive support separation. The repeated `strong<2` blocker means final decision has too little reliable positive evidence to distinguish gold accepts from reject controls after cleanup.

### Revised next single cut

Do not implement runtime lifecycle cleanup yet. The next cut should be **Positive Evidence / Support Separation Audit v1**:

1. Compare recovered-oracle accept candidates (`QAAsnSRwgu`, `KI9NqjLVDT`) against false-flip reject (`aTBE70xiFw`).
2. Inspect strong/medium support evidence quality and whether support is tied to real paper claims or fallback/meta claims.
3. Determine why `strong<2` remains in 12/16 samples even after cleanup.
4. Only after this audit decide whether to fix evidence extraction, claim support mapping, or final decision support accounting.

This keeps the project aligned with the core thesis: recovery/state updates matter only if ReviewState separates grounded positive evidence from unverified negative concerns.

## 9. Positive Support Separation Audit Result

The support audit explains why lifecycle cleanup alone failed:

| support signal | count |
|---|---:|
| strong positive evidence total | 14 |
| strong positive on supported claim | 1 |
| strong positive on unsupported claim | 7 |
| strong positive on fallback claim | 6 |
| samples with `strong<2` blocker | 12 |

The oracle-recovered accept cases differ from the false-flip reject case in a useful way:

- `QAAsnSRwgu`: has one supported strong positive and one unsupported strong positive.
- `KI9NqjLVDT`: has three strong positives, but all are attached to unsupported non-fallback claims.
- `aTBE70xiFw`: has two strong positives, but both are fallback-bound.

### Final revised next single cut

**Support Grounding + Claim-Status Reconciliation Simulation v1**:

1. Count only non-fallback strong support as final-decision positive evidence.
2. Reconcile non-fallback unsupported claims with strong support and no strong contradiction.
3. Do not count fallback-bound support as accept evidence.
4. Combine with conservative unresolved/candidate handling only after support separation passes.

This is the first rule family that has a plausible safety discriminator between recovered accept candidates and the known false-flip reject.

## 10. Support Grounding Simulation Result

Support grounding and claim-status reconciliation were tested offline. Standalone support rules still produced zero flips:

| rule | recovered accept | false accept | conclusion |
|---|---:|---:|---|
| `SG1_nonfallback_support` | 0 | 0 | Safe but no recovery. |
| `SG2_reconcile_status` | 0 | 0 | Claim status reconciliation alone is insufficient. |
| `SG3_reconcile_plus_soft_unresolved` | 0 | 0 | Soft unresolved threshold still blocked. |
| `SG4_oracle_negatives_with_support_guard` | 2 | 0 | Works only with oracle negative cleanup. |

### Final next direction

The evidence now rules out three isolated fixes:

1. final-decision relaxation alone;
2. lifecycle cleanup alone;
3. support reconciliation alone.

The next useful step is **Coupled State Hygiene Simulation v1**, still offline and still 4B-fast. It must combine non-fallback support accounting with conservative unresolved/candidate lifecycle cleanup, and it must preserve the `aTBE70xiFw` reject safety case.

## 11. Coupled State Hygiene Simulation v1 Result

The coupled simulation produced the first safe non-oracle improvement.

| rule | recovered accept | false accept | accept recall | reject recall | macro-F1 |
|---|---:|---:|---:|---:|---:|
| `C1_system_unresolved_meta_candidate` | 0 | 0 | 0.0000 | 1.0000 | 0.3043 |
| `C2_system_unresolved_ungrounded_candidate` | 0 | 0 | 0.0000 | 1.0000 | 0.3043 |
| `C3_unowned_unresolved_ungrounded_candidate` | 2 | 0 | 0.2222 | 1.0000 | 0.5152 |
| `C4_oracle_negative_plus_support_guard` | 2 | 0 | 0.2222 | 1.0000 | 0.5152 |

### Decision

`C3_unowned_unresolved_ungrounded_candidate` is now the first runtime-worthy candidate. It reaches the same decision improvement as the oracle negative cleanup while preserving `aTBE70xiFw` as reject.

### Next engineering step

Implement **Coupled State Hygiene v1** minimally:

1. non-fallback strong support accounting;
2. reconcile unsupported real claims with strong support and no strong contradiction;
3. mark system/generic/unowned unresolved questions as resolved/review-limitation;
4. downgrade ungrounded major/critical candidate flaws;
5. log every change as `state_hygiene`, then evaluate on the same 16-sample 4B focus set before any larger run.

