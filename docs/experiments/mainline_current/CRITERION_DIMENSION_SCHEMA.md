# Criterion Dimension Schema

This is an offline audit layer for review quality diagnostics. It does not modify runtime behavior, prompts, ReviewState, or final decisions.

## Dimensions

- `novelty_originality`: whether the final report discusses novelty/originality or contribution novelty.
- `significance_contribution`: whether the report discusses contribution significance, impact, usefulness, or importance.
- `technical_soundness`: whether it discusses method validity, assumptions, algorithms, or technical design.
- `empirical_adequacy`: whether it discusses experiments, datasets, metrics, baselines, tables, figures, or ablations.
- `clarity_reproducibility`: whether it discusses presentation clarity, implementation details, reproducibility, code, or hyperparameters.

## Field Semantics

- `criterion_covered_*`: the report mentions the dimension.
- `criterion_grounded_*`: the mention is linked to available evidence sections, explicit claim/evidence references, or a not-assessable statement.
- `unsupported_*_critique_count`: negative critique for the dimension without grounding.
- `criterion_not_assessable_*`: the report marks the dimension as not assessable because information is insufficient.
- `meta_leakage_*`: system/excerpt/recovery/fallback limitation appears as a dimension weakness.

## Guardrail

Criterion labels must not drive accept/reject in this phase. They are paper-evaluation diagnostics only.
