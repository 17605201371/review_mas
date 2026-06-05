# Progression Gate V1 Protocol

## Scope
- First add config alignment protection.
- Then add one pre-sanitize progression gate before aggressive recovery becomes final routing.
- Do not change sticky, sanitize, fallback generation, validator/lifecycle, reward, or dataset scope.

## Gate Placement
The gate runs in `review_manager_policy.apply_manager_policy_fallback()` after S4 recovery-oriented overrides and sticky recovery bias have selected a candidate action, but before `_sanitize_targets_for_action()` and before `review_runner._apply_recovery_phase_protocol()`.

## Gate Input
The main input is raw/pre-sanitize `target_claim_ids` from the manager payload or `infer_action_from_state(...)`, not post-sanitize targets.
The final sanitized target ids are logged separately for diagnosis.

## Blocked Aggressive Actions
- `request_evidence_recheck`
- `challenge_previous_hypothesis`

## Reasons
- `fallback_target`: raw target contains `claim-fallback-*`.
- `broad_target`: raw real target set is too broad, or challenge has multiple real targets.
- `weak_conflict`: recovery action lacks enough conflict/evidence signal.
- `multiple_reasons`: more than one reason applies.

## Safe Downgrade Order
1. keep current non-aggressive action if it is evidence/flaw/claim work
2. `verify_evidence`
3. `analyze_flaws`
4. current action only as a last fallback
