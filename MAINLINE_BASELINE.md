# MAINLINE_BASELINE

## Baseline Definition

`p25.1` is the only trusted paper mainline baseline for this repository.

This means:
- main claims must be supported by `p25.0` and `p25.1` only
- later calibration rounds are exploratory diagnostics, not main evidence
- future experiments should branch from this reset point instead of stacking more fixes on top of unstable heads

## Mainline Scope

The frozen paper mainline contains:
- `P25_0_*` frozen 4B vs 9B recovery-quality comparison documents
- `P25_1_*` 9B recovery-quality expansion documents
- result artifacts under `outputs/results_main/`

The mainline research statement is:

> In multi-turn review assistance, the key gain is not merely triggering recovery, but converting recovery into structured patches that successfully modify `ReviewState`; under this framing, 9B improves patch effectiveness more clearly than overall reward.

## Why p25.1

`p25.1` is the last point where:
- results remain interpretable
- the main narrative is stable
- 9B shows a clear advantage on recovery quality
- the conclusion does not depend on increasingly fragile post-hoc calibration rules

## What Is Not in the Mainline

The following rounds are not deleted, but they are not part of the paper main evidence:
- `p25.2` policy-block calibration
- `p25.3` stability-preserving calibration
- `p25.4` trajectory/guard style control experiments
- `p25.5a` guard activation diagnostics

These belong to:
- negative findings
- limitations
- future work

## Directory Contract

Mainline artifacts live under:
- `outputs/results_main/review_infer/`

Exploratory artifacts live under:
- `outputs/results_exp/review_infer/`

Any new paper-facing table, figure, or claim should source files only from `outputs/results_main/` unless the section is explicitly a diagnostic or limitation section.

## Immediate Next Steps

1. Draft the paper method section using the frozen `ReviewState` + recovery patch pipeline.
2. Draft experimental setup around `p25.0` and `p25.1`.
3. Prepare main tables and figures from the mainline result directory only.
4. Keep future experiments small, single-point, and reversible.
