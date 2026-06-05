# P25.1 Fast Debug Plan

## Problem

A full 10-row 9B forensic run takes around 15-20 minutes. That is too slow for micro-iteration when the failure mode is still being localized.

## Adjustment

Use two tiers:

### Tier 1: Smoke Debug

Use 4 samples only:

- `qgyF6JVmar`: progression gate triggers repeatedly on fallback target
- `IqaQZ1Jdky`: fallback recovery still emits and commits once
- `NhLBhx5BVY`: canonical success-sensitive regression without gate trigger
- `9EBSEkFSje` or `meY36sGyyv`: baseline success lost without gate trigger

Purpose:

- confirm fields are logged
- confirm gate/phase interactions
- inspect whether patch emission is preserved
- catch obvious over-suppression before spending 20 minutes

### Tier 2: Fixed Forensic Full Check

Run the existing 10-row subset only after Tier 1 looks structurally sane.

Purpose:

- decision file
- retention/rollback judgment
- uploadable final compare

## Runtime Settings

For final comparability, keep:

- model: `/reviewF/datasets/Qwen3___5-9B`
- mode: `s4`
- max_turns: 8
- max_workers_per_turn: 2
- max_model_len: 3072
- max_tokens: 640
- temperature: 0.2
- top_p: 0.95
- seed: fixed explicitly for all paired debug runs

For smoke debug, the sample subset can change, but runtime parameters should remain identical unless the output is explicitly labeled non-comparable. If a run is used to compare a mechanism against a baseline, both baseline and candidate must be regenerated with the same seed.

## Rule

Do not use smoke-run metrics as final evidence. Use smoke only to avoid wasting full runs on obvious implementation bugs.
