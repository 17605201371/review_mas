# AGENT.md

This file records persistent execution constraints for the review project.

## Project Goal

Build a **ReviewState-centered, evidence-driven, revisable multi-turn review assistance system**.

The project studies:
- whether multi-turn interaction improves evidence alignment and flaw localization
- whether role-specialized agents reduce error accumulation
- how revisable state supports error recovery and future clarification loops

## Primary Constraints

Before making substantial code changes, always check these root-level planning files:
- `REVIEW_REALIGN_PLAN.md`
- `REVIEW_PR1_STATE_PLAN.md`
- `REVIEW_PR2_MANAGER_POLICY_PLAN.md`
- `REVIEW_PR3_OBSERVATION_PLAN.md`

These files are the implementation guardrails.
Do not drift away from them unless the user explicitly updates the plan.

## High-Priority Principles

1. Do not drift toward a generic multi-agent orchestration framework.
2. Keep `ReviewState` as the center of reasoning progress.
3. Prioritize:
   - evidence alignment
   - flaw localization
   - error recovery
   - future clarification support
4. Preserve `S1 / S2 / S3 / S4` unless a planned change explicitly updates them.
5. Prefer revisable state and grounded critique over fluent but weak review text.

## Out of Scope Unless Explicitly Requested

- no framework-wide structured-state redesign
- no changes to `verl/`, PPO trainer, or rollout collector internals
- no RL-first work before review-state logic is stable
- no extra agents unless they directly support the research question

## Development Order

- PR1: revisable `ReviewState`
- PR2: manager as dialogue policy
- PR3: focus-aware observation rendering

Do not skip ahead unless explicitly requested.

## Server Workflow

- Default working copy: `/root/zssmas`
- Default execution target: server first, not local repo first
- Keep logs and outputs under `outputs/review_infer` unless a task requires another location

## Operation Visibility Rules

When fixing bugs, modifying code, or performing important operations:
- explicitly state what operation is being performed
- keep the user informed of progress in plain language
- do not silently perform major changes
- when changing behavior, say what changed and why

When running training or inference:
- always expose the log path for the user to inspect
- prefer log files under `outputs/` or another explicit project path
- make long-running commands observable by giving the live or final log location
- overwrite logs for repeated runs instead of appending unless the user asks otherwise

## Project Memory Rules

- record important code changes, decisions, and milestones in the root `memory.md`
- record the current active task in the root `TASK.md`
- update these files when the task meaningfully changes or when a major code milestone is completed
- treat `memory.md` and `TASK.md` as required maintenance, not optional notes
