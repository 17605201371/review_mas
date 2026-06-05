# Target Evolution Trace V2

## Purpose

This patch is observability-only. It records target evolution checkpoints without changing manager action selection, sanitize behavior, validator/lifecycle logic, reward, or worker execution.

## Checkpoints

| checkpoint | fields | source | meaning |
| --- | --- | --- | --- |
| raw target | `raw_target_claim_ids`, `raw_target_count`, `raw_target_is_broad` | `infer_action_from_state(...)` in `agent_system/review_manager_policy.py` | inferred target before policy fallback, sticky, sanitize, or final action application |
| post fallback target | `post_fallback_target_claim_ids`, `post_fallback_target_count`, `fallback_target_present`, `fallback_claim_ids_used`, `fallback_evidence_ids_used`, `fallback_contradiction_emitted` | `apply_manager_policy_fallback(...)`, plus worker payload inspection in `build_turn_log(...)` | target after manager/policy fallback and before sanitize; worker fallback ids are observed but do not alter behavior |
| post sanitize target | `post_sanitize_target_claim_ids`, `post_sanitize_target_count`, `sanitize_bloat_detected`, `sanitize_bloat_delta`, `sanitize_expanded_from_raw`, `sanitize_expanded_from_fallback` | immediately after `_sanitize_targets_for_action(...)` | target after existing sanitize rules |
| final action target | `final_action_target_claim_ids`, `final_action_target_count`, `final_action_type`, `final_effective_action_type` | end of `apply_manager_policy_fallback(...)` and serialized by `build_turn_log(...)` | target that actually drives the turn |

## Layer 2 Observation

In the five-sample Layer 2 run, `sanitize_bloat_detected = 0`. Broad targets appeared at the raw/inferred stage, not because sanitize expanded a narrow target.

## Important Boundary

This does not prove sanitize is always safe. It only shows that in the current Layer 2 subset, the earliest visible target broadening is upstream of sanitize.
