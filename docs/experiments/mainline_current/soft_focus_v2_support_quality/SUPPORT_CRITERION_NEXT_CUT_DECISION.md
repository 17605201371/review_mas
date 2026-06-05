# Support + Criterion Next Cut Decision

- Rows: 39.
- False accepts: 1.
- False rejects: 9.
- False accepts with abstract-only support: 0.
- Gold-accept rows without non-abstract support: 1.
- Average covered criteria per report: 5.00.
- Unsupported criterion critiques: 0.
- Criterion meta-leakage signals: 0.

Next unique cut: **Evidence Context Selection v2**.

Reason: Gold-accept rows still lack non-abstract/empirical support, so accept-like evidence is not deep enough.

Guardrail: do not wire criterion labels directly into final decision yet. This audit only decides the next implementation direction.
