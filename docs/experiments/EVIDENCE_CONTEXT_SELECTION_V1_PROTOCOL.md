# Evidence Context Selection v1 Protocol

## Goal

This iteration changes only what the Evidence Agent sees. It does not change final decision rules, recovery, sticky/throttle/gate logic, fallback suppression, state hygiene, reward, parser, or merge semantics.

The motivation is the mixed v2 audit: fresh Accept samples still collapsed to Reject because ReviewState rarely formed enough grounded strong positive support. Negative cleanup alone cannot recover Accept decisions when positive evidence never enters the state.

## Problem

The previous Evidence Agent observation used `_render_paper_excerpt(task, max_length=800)`, which directly returned the first 800 characters of `paper_text`. In many samples, this region is dominated by task wrapper, instruction text, title, and abstract opening. Evidence-rich regions such as method, experiment, results, tables, figures, ablations, and conclusion are often invisible.

## Change

Added Evidence-only helpers in `agent_system/environments/env_package/review/state.py`:

- `_clean_paper_body(text)`: strips task wrapper markers such as `--- BEGIN PAPER ---` / `--- END PAPER ---` and obvious instruction/format lines.
- `_render_evidence_context_with_meta(task, max_length=2400)`: builds a section-aware context from abstract/body start plus keyword windows around method/approach/model/framework, experiment/evaluation/results/analysis, table/figure/ablation, and conclusion/discussion.
- `_render_evidence_context(task, max_length=2400)`: returns only the context text.

Only `render_evidence_observation(...)` now uses the section-aware context. Claim/Critique/General observations still use the previous excerpt behavior.

## Logging

The Evidence Agent manager payload and turn logs now expose:

- `evidence_context_chars`
- `evidence_context_mode`
- `evidence_context_cleaned_wrapper`
- `evidence_context_contains_method`
- `evidence_context_contains_results`
- `evidence_context_contains_conclusion`
- `evidence_context_contains_table_or_figure`
- `evidence_context_snippet_sources`

## Evaluation Funnel

- Layer 0: static preview, no model run.
- Layer 1: 2-sample smoke run.
- Layer 2: 5-sample functional run.
- Layer 3: 16-sample balanced mixed v2 run.

Primary metrics are context visibility and positive support formation, not final accuracy.
