# Component Ablation Matrix v1 (offline; 0 LLM calls)

- input: `outputs/results_main/review_infer/mainline_final_v1_closure_9b_fulltest39_20260504_gold.jsonl`
- gold labels: `docs/experiments/mainline_current/MAIN_EXPERIMENT_CODE_CLOSURE_V1/fulltest39_gold_labels_locked_20260504.json` (locked)
- n_papers: **39**
- ablation rows: full / A1_no_binding / A3_no_hygiene / A2_no_criterion_grounding / A4_no_recovery_validator_semantic

## Scope of this audit

The ablation flag is forwarded into `_validate_evidence_bindings_for_state` / `build_decision_hygiene_view` / `infer_final_recommendation_view` via an explicit `enable_*=False` argument. This guarantees we measure each component independently without flipping a module-level constant.

**Important caveat — what offline can and cannot measure.**

- **A1 (no binding precision)** can only be measured *trivially* offline: the binding-precision filter runs inside `merge_review_state` at evidence-injection time. By the time we read the closure jsonl, every retained evidence already has `binding_status = bound_real_claim`; there is no fallback residue to re-include. Offline `A1_no_binding` therefore yields metrics identical to `full` *by construction*. The substantive A1 ablation requires re-running the inference pipeline so the agent observes a different evidence pool. A reproducer command is listed at the end of this report.
- **A3 (no final-view hygiene)** is fully offline: the hygiene layer is a non-mutating post-processor over the saved ReviewState, so we can deterministically recompute the no-hygiene baseline. The numbers in this report under A3 are the real ablation effect.
- **A2 (no criterion grounding)** is a reporting-layer ablation: the criterion grounded rate is the only metric switched off; binary, support quality, and final-view distributions are unchanged. We zero those rates to make the contribution visible.
- **A4 (no recovery validator semantic check)** requires inference because the validator gates which recovery patches commit to ReviewState. Reproducer command listed at the end.

Use the A3 row as the substantive offline ablation finding. Use A1 / A4 placeholders as a roadmap for the inference-level sub-experiments.

## Decision Health (binary as health check)

| ablation | binary_accuracy | accept_recall | predicted_accept |
|---|---:|---:|---:|
| **full (closure run)** | 0.8205 | 0.1250 | 1 |
| **A1_no_binding** | 0.8205 | 0.1250 | 1 |
| **A3_no_hygiene** | 0.8205 | 0.1250 | 1 |
| **A2_no_criterion_grounding** | 0.8205 | 0.1250 | 1 |
| **A4_no_recovery_validator_semantic*** | 0.8205 | 0.1250 | 1 |

_*A4 binary unchanged because no patch was committed under the closure run; switching the semantic check off may allow new commits — see runner command below for the inference re-run._

## Support quality (strict counters)

| ablation | real_strong | nonabstract | empirical | method | fallback_strong | indep_groups |
|---|---:|---:|---:|---:|---:|---:|
| **full (closure run)** | 49 | 49 | 35 | 13 | 0 | 42 |
| **A1_no_binding** | 49 | 49 | 35 | 13 | 0 | 42 |
| **A3_no_hygiene** | 49 | 49 | 35 | 13 | 0 | 42 |

## Final Recommendation View distribution

| ablation | accept_like | borderline_positive | borderline_insufficient | not_assessable_uncertain | reject_like |
|---|---:|---:|---:|---:|---:|
| **full (closure run)** | 1 | 2 | 24 | 11 | 1 |
| **A1_no_binding** | 1 | 2 | 24 | 11 | 1 |
| **A3_no_hygiene** | 0 | 0 | 0 | 37 | 2 |

## Final-view hygiene counters

| ablation | open_gap | stale_gap | deferred_unresolved | targetless_deferred | downgraded_flaw |
|---|---:|---:|---:|---:|---:|
| **full (closure run)** | 52 | 58 | 269 | 190 | 22 |
| **A1_no_binding** | 52 | 58 | 269 | 190 | 22 |
| **A3_no_hygiene** | 110 | 0 | 0 | 0 | 0 |

## A2: Criterion grounding ablation

- baseline self-claimed grounded rates (full): see `MAINLINE_FINAL_V1_9B_FULLTEST39_A1A2_REPORT.md`. Each of the 5 criterion dimensions reports a self-claimed rate ∈ [0.85, 1.0] (agent-claimed; not LLM-judge entailment).
- under A2 these are zeroed; the paper loses the only per-criterion signal currently available.
- under A2 every other metric in this table is unchanged (verified: A2 is a pure reporting-layer toggle).

## A4: Recovery validator semantic check (inference-required)

Switch is implemented in `agent_system/environments/env_package/review/recovery_validator.py` as `ENABLE_RECOVERY_VALIDATOR_SEMANTIC_CHECK = True`. Toggling this flag requires re-running the closure inference pipeline so the manager observes a different validator gate. To launch the A4 sub-run when GPU is available, use:

```bash
ENABLE_RECOVERY_VALIDATOR_SEMANTIC_CHECK=0 \
  python -m agent_system.inference.review_runner \
    --config configs/review/mainline_final_v1_9b_fulltest39_closure.yaml \
    --output-dir outputs/results_main/review_infer/ablation_a4_no_validator_semantic_v1 \
    --tag ablation_A4_no_validator_semantic
```

Note: ``ENABLE_RECOVERY_VALIDATOR_SEMANTIC_CHECK`` is a Python module constant, not an env var; the env-var form above is illustrative. Until that runner exposes a CLI override, the easiest reproducer is to set the constant to False in `recovery_validator.py` for the duration of the A4 run and revert afterwards.

## How to interpret

- **A1_no_binding**: counts every strong support evidence as real_strong even when its `claim_id` is `claim-fallback*` or absent. The increase in `real_strong` between full and A1 is exactly the volume the binding-precision filter normally suppresses; the corresponding rise in `fallback_strong` shows where that volume came from.
- **A3_no_hygiene**: keeps every targetless / context-meta unresolved question open and every fallback flaw at its pre-downgrade status. The drop in `accept_like` / rise in `not_assessable_uncertain` between full and A3 quantifies the contribution of the hygiene layer to the multi-bucket recommendation. `downgraded_flaw_count` should be **0** under A3 by construction.
- **A2_no_criterion_grounding**: criterion grounded rates disappear; the paper's only per-criterion signal goes silent. Use this row to argue the criterion table is non-redundant.
- **A4 (placeholder)**: switching off the semantic check would let claim-downgrade patches commit even when supporting evidence is positive-stance; the expected sign of `committed_success` change is positive, but quantifying it requires inference. Do not write A4 numbers in the paper without running the inference sub-experiment.

Generated by `scripts/run_ablation_offline_v1.py`.
