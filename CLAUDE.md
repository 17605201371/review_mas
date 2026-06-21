# CLAUDE.md — auto-loaded context for the code agent

> Cross-session handoff (this agent has no shared memory). **Full context:** read
> `HANDOFF_FOR_CODE_AGENT_20260619.md` and `AGENT.md` before non-trivial work.

## Project
Dr.MAS for Paper Review (verl/verl-agent fork). `ReviewState`-centric, evidence-driven,
multi-turn peer-review system; mode **S4** (Manager + Claim/Evidence/Critique agents); MiMo v2.5
API + small_model adapter. Paper contribution = **structured ReviewState + pos/neg evidence
lifecycle + contested relation + guarded recovery patch + final-view hygiene** (not accept/reject).
Goal: raise **verified negative concern** recall on hard-negative papers without breaking
hygiene/safety.

## ⚠️ Current P0 (blocking the whole narrative)
Real verified negatives ≈ **0** because the Evidence Agent's JSON parses ~10% of the time
(~90% fallback). Root cause (diagnosed 2026-06-19): the small model emits **chain-of-thought
prose instead of JSON** even at max_tokens=2048 with enable_thinking=False, so parsing fails from
char 1. Fix shipped (commit `6ce54d6`): `response_format={"type":"json_object"}` in
`review_runner.py`, env `DRMAS_JSON_RESPONSE_FORMAT` (auto|on|off, default auto; auto self-disables
if the provider rejects it). **Validate it (A/B on vs off) before anything else. Freeze all
downstream negative/recovery tuning until `evidence_json_fallback_rate_pct` < 20%.** Use
`--max-tokens 2048` (the old memory "768 is better" is WRONG — 768 truncates).

## Hard constraints (see AGENT.md)
Don't touch verl/PPO/rollout kernel; don't change validator main logic; keep S1–S4; change ONE
explainable factor per smoke run; logs overwrite (don't append). Conclusions in Chinese,
code/identifiers in English. Run hardneg20 guard3 before full39.

## Do-Not-Retry (already falsified & rolled back — do not repeat)
progression_gate / throttle / gate variants; sticky; global fallback suppress; any "block recovery
by a simple rule". **Giving negative discovery to Critique model-judgment instead of Evidence
quote-find+verify is twice-falsified net-negative** (`DRMAS_HARDNEG_DIAGNOSIS` A/B: reward
0.498→0.454, all negative/verified/actionable/contested/recovery →0). Keep diagnosis default-off.
Next real direction = **P-B**: claim-centric re-ranking of `verify_evidence` targets WITHOUT
stealing evidence-recheck turns (Evidence still forms+verifies negatives). Never: full39 over
hardneg20; loosen fallback/context claim status patch; quote-bank → claim downgrade; generic_gap →
negative; sacrifice semantic grounding for grounded_weakness count; remove recovery guard; break
`state_contamination=0` / `recovery_harmful_commit_risk=0` / `recovery_no_effect_commit=0`.

## Working agreement
User runs Codex + Claude as paired agents (one audits the other). **No green-for-green** — fix
tests to reflect true semantics, never with vacuous asserts; if you can't fix correctly, leave it
red and report it as a suspected code bug.

## Confirmed semantics (don't regress; details in HANDOFF §6)
3-layer verified-negative gate (paper-grounded + `semantic_negative_verified` +
`review_negative_verified`). `merge_review_state` strips model-claimed grounding — only quotes
verifiable against quote_bank/paper_text count. Trusted `verified_quote_match_type` excludes
`*_substring`. recovery: candidate→downgraded (verified actionable) = ACTIONABLE_CONCERN_PRESERVED;
confirmed→downgraded normalizes to candidate (downgrade_final_to_candidate). final-view layer:
actionable+confirmed→grounded_weakness, actionable+candidate→potential_concern, scope_*→
assessment_limitation. Focused test suite = 561 passed
(`PYTHONPATH=$(pwd) python3 -m pytest tests/test_recovery_patch.py tests/test_review_inference_runner.py tests/test_recovery_replay_harness.py tests/test_review_decision_hygiene.py tests/test_review_negative_author_limitation_guard.py -q`).

## Recent commits
- `6ce54d6` evidence-json: force valid JSON via response_format=json_object (P0 fix).
- `ae178bb` harden verified-negative gate + bring focused test suite green (Fix#3 salvage-locatable,
  review_prompts baseline-drift fix, guard script + regression tests).
