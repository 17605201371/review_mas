# Support + Criterion Next Cut Decision

- Rows: 16.
- False accepts: 0.
- False rejects: 8.
- False accepts with abstract-only support: 0.
- Gold-accept rows without non-abstract support: 4.
- Average covered criteria per report: 2.81.
- Unsupported criterion critiques: 0.
- Criterion meta-leakage signals: 0.

Next unique cut: **Evidence Context Selection v2**.

Reason: Gold-accept rows still lack non-abstract/empirical support, so accept-like evidence is not deep enough.

Guardrail: do not wire criterion labels directly into final decision yet. This audit only decides the next implementation direction.
