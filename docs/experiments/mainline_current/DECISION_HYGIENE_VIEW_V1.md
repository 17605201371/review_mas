# Decision Hygiene View v1

## Purpose

This patch keeps the paper-review mainline focused on ReviewState quality rather than label hacking. The goal is not to relax accept/reject thresholds. The goal is to prevent stale default rejects, fallback-bound evidence, ungrounded flaw candidates, and stale gaps from dominating the final recommendation after real claim-bound support has already been accumulated.

## Scope

This is a final decision/report-time derived view only. It does not mutate live ReviewState during multi-turn inference, and it does not change manager routing, recovery phase behavior, validator/lifecycle rules, reward, sticky, throttle, fallback generation, or evidence extraction.

## Implemented Behavior

- `build_decision_hygiene_view(state)` deep-copies ReviewState and derives a clean final-decision view.
- Accept-level support now counts only strong support bound to real, non-fallback claim IDs.
- Stale fallback/meta gaps and conflicts are removed from the decision view.
- Meta/system unresolved questions are deferred in the decision view instead of being treated as paper defects.
- Stale unresolved questions such as `Claim X lacks grounded supporting evidence` are deferred when the same claim already has real strong support.
- Ungrounded or fallback flaw candidates are downgraded in the decision view and are not rendered as active key weaknesses.
- `infer_final_decision(...)` derives the recommendation from structured state evidence instead of trusting manager text or stale `final_decision` first.
- `resolve_result_final_decision(...)` now gives structured-state inference priority over stale stored/report decisions.

## Offline Check

On `outputs/results_main/review_infer/evidence_binding_v1_mixed16.jsonl`, the derived view recovered three accept-like samples without rerunning the model:

- `VEJzjAvaIy`: reject -> accept, with 2 real strong supports.
- `pOq9vDIYev`: reject -> accept, with 4 real strong supports.
- `cpGPPLLYYx`: reject -> accept, with 2 real strong supports.

This confirms the intended effect: the change surfaces positive real-claim support already present in the state rather than creating new evidence or relaxing decision thresholds.

## Verification

- `python -m py_compile agent_system/environments/env_package/review/state.py agent_system/review_manager_policy.py tests/test_review_decision_hygiene.py`
- `python -m pytest tests/test_review_decision_hygiene.py tests/test_review_multiturn.py tests/test_recovery_patch.py -q`
- Result: `26 passed` for the focused review-state/recovery test set.

## Known Residual Risk

`tests/test_review_inference_runner.py` still has older progression-throttle policy expectation failures. Those are not caused by this final decision hygiene patch and should be handled separately, because changing them here would mix controller-policy work into a decision-view fix.

## Mixed16 Model Rerun

A 4B mixed16 rerun was executed with `max_turns=8`, `manager_batch_size=4`, `max_model_len=3072`, `max_num_seqs=128`, and `gpu_memory_utilization=0.6`.

Output files:

- `outputs/results_main/review_infer/decision_hygiene_view_v1_mixed16.jsonl`
- `outputs/results_main/review_infer/decision_hygiene_view_v1_mixed16_analysis.json`
- `decision_hygiene_view_v1_mixed16.log`
- `DECISION_HYGIENE_VIEW_V1_RUN_COMPARE.md`

Key results:

- Final decisions: 3 accept, 13 reject.
- `final_strong_support_total`: 14.
- `strong_support_on_real_claim`: 14.
- `strong_support_on_fallback_claim`: 0.
- `strong_support_binding_precision`: 1.0.
- `rows_with_2plus_real_strong_support`: 5.
- `evidence_fallback_payload_count`: 21.

Interpretation: the decision hygiene view no longer rewards fallback-bound strong support and can produce non-reject recommendations when real claim support and active blockers align. The v1 unresolved lifecycle extension recovered `cWEfRkYj46` by deferring stale/system uncertainty while leaving samples with unresolved grounded questions or active major/critical flaws as reject. Remaining false-negative pressure is mainly from unresolved lifecycle quality, not fallback evidence binding.
