# Criterion Next Step Decision

## Summary

- Rows: 39
- Average covered criteria per report: 5.0
- Total unsupported criterion critiques: 0
- Total meta-leakage signals: 0
- Lowest coverage dimensions: novelty_originality, significance_contribution

## Decision

Next step: **audit_only**.

Reason: Coverage and grounding are sufficient for now; keep as paper diagnostic metrics.

## Guardrail

Do not let novelty, soundness, empirical adequacy, clarity, or significance directly affect accept/reject yet. If implemented later, criterion outputs should first become a structured final-report section or grounding schema, not a decision rule.
