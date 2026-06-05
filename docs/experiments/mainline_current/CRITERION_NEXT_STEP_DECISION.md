# Criterion Next Step Decision

## Input

Primary audit input: `outputs/results_main/review_infer/decision_hygiene_view_v1_fulltest39_4b.jsonl`

Cross-check outputs were also generated under `outputs/results_main/criterion_audit/mixed16` and `outputs/results_main/criterion_audit/fulltest39`.

## Summary

- Rows: 39
- Average covered criteria per report: 2.41
- Total unsupported criterion critiques: 0
- Total meta-leakage signals: 0
- Lowest coverage dimensions: novelty_originality, clarity_reproducibility

## Interpretation

The current final reports discuss significance and technical soundness relatively often, but they under-cover novelty/originality, clarity/reproducibility, and empirical adequacy. This means the system can produce useful review judgments, but the final report is not yet shaped like a complete reviewer form.

Grounding is also weaker than coverage. For example, significance is covered in most reports, but only a subset has criterion-level grounding under the current offline heuristic. This should be treated as a report-structure and grounding problem, not as a reason to change accept/reject.

Meta-leakage is not the dominant failure in this audit. The main gap is missing or under-grounded criterion coverage, especially novelty and clarity.

## Decision

Next step: **add_criterion_section_to_final_report**.

Reason: Average criterion coverage is below 3 dimensions per report, with novelty and clarity particularly under-covered. The next implementation should add a structured final-report section for core review dimensions, but it must require evidence/claim grounding for each criterion entry.

## Do Not Do Yet

- Do not add `low_novelty -> reject` or similar criterion-based decision rules.
- Do not let novelty, soundness, empirical adequacy, clarity, or significance directly affect accept/reject.
- Do not change runtime recovery, evidence binding, state hygiene, or final decision thresholds in this step.

## Next Implementation Shape

A safe next step is `Criterion-Aware Final Report Section v1`: render a final-report section with five explicit dimensions:

- novelty/originality
- significance/contribution
- technical soundness
- empirical adequacy
- clarity/reproducibility

Each dimension should be one of: `positive`, `negative`, `mixed`, or `not_assessable`, and should cite claim/evidence ids when available. Ungrounded criterion claims should be phrased as uncertainty or limitations, not as paper weaknesses.

## Guardrail

Criterion outputs are paper-evaluation diagnostics first. They may improve report completeness and paper-level evaluation richness, but they are not reliable enough to become decision features until evidence binding, state hygiene, and flaw lifecycle are stable.
