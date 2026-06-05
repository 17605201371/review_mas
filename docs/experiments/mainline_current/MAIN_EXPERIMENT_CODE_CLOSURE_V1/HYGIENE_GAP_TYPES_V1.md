# Hygiene Gap Types Audit v1 (offline; 0 LLM calls)

- input jsonl: `outputs/results_main/review_infer/mainline_final_v1_closure_9b_fulltest39_20260504_gold.jsonl`
- judge source: `outputs/results_main/review_infer/grounded_judge_v1.json`
- n_papers: **39**
- n_flaws: **48**

## Type taxonomy

Flaws are classified into five mutually exclusive types (first-match priority):

1. **`schema_dump`** — title/description leaks a raw JSON schema (`{..."flaw_candidates": ...}`). Worker output escaped the prompt boundary.
2. **`truncation_meta`** — flaw is about paper-text availability (truncation, missing full text, cannot verify due to excerpt limits).
3. **`fallback_or_system_meta`** — flaw_id starts with `flaw-fallback`, or source/grounding_status marks it as fallback/system-meta produced by parser/recovery paths.
4. **`boilerplate_generic`** — matches generic reviewer templates (*"insufficient evidence for core claims"*, *"lacks rigorous evaluation"*, etc.) with no paper-specific anchor (no percentages / table refs / metric values / dataset names).
5. **`substantive`** — residual. Contains paper-specific signal.

## Type distribution

| type | total | visible post-hygiene | filtered by hygiene |
|---|---:|---:|---:|
| `schema_dump` | 25 | 0 | 0 |
| `truncation_meta` | 18 | 0 | 18 |
| `fallback_or_system_meta` | 0 | 0 | 0 |
| `boilerplate_generic` | 1 | 1 | 0 |
| `substantive` | 4 | 0 | 4 |

## Parity with `state.py::_is_fallback_or_meta_flaw`

- state.py classifies **42** flaws as meta/fallback.
- Of those, **42** also classified as non-`substantive` here.
- Agreement rate with state.py: **1.0000** (high agreement validates the classifier; low agreement signals drift to investigate).

## Hygiene diagnostics per type

*For flaws that hygiene filtered out (raw=candidate/confirmed → post=downgraded/retracted), how many did the LLM judge also flag as `not_paper_grounded` (hygiene correct) vs `paper_grounded` (hygiene false negative)? Only flaws with a judge verdict are counted in the denominator.*

| type | filtered | with_judge | correctly filtered | hygiene FN | hygiene_precision |
|---|---:|---:|---:|---:|---:|
| `schema_dump` | 0 | 0 | 0 | 0 | — |
| `truncation_meta` | 18 | 18 | 14 | 4 | 0.7778 |
| `boilerplate_generic` | 0 | 0 | 0 | 0 | — |
| `substantive` | 4 | 4 | 1 | 3 | 0.2500 |

## Examples per type

### `schema_dump` (25 flaws)

- `ye3NrNrYOY/flaw-fallback-1` [raw=downgraded → post=downgraded] judge=not_paper_grounded
    - **title**: { "flaw_candidates": [ { "flaw_id": "flaw-1", "title": "Insufficient Evidence for Core Claims", "description": "The prov
    - **desc**:  { "flaw_candidates": [ { "flaw_id": "flaw-1", "title": "Insufficient Evidence for Core Claims", "description": "The provided paper excerpt is truncated (cut-off abstract, missing methodology, no tables). Consequently, th
- `uOrfve3prk/flaw-fallback-1` [raw=downgraded → post=downgraded] judge=not_paper_grounded
    - **title**: { "flaw_candidates": [ { "flaw_id": "flaw-1", "title": "Lack of Grounded Evidence for Core Claims", "description": "Clai
    - **desc**:  { "flaw_candidates": [ { "flaw_id": "flaw-1", "title": "Lack of Grounded Evidence for Core Claims", "description": "Claims claim-1 and claim-2 are marked as 'supported' but the supporting evidence IDs provided in the cri
- `hj323oR3rw/flaw-fallback-1` [raw=downgraded → post=downgraded] judge=paper_grounded
    - **title**: { "flaw_candidates": [ { "flaw_id": "flaw-1", "title": "Lack of Empirical Verification for Core Mechanism", "description
    - **desc**:  { "flaw_candidates": [ { "flaw_id": "flaw-1", "title": "Lack of Empirical Verification for Core Mechanism", "description": "Claim 2 asserts that the proposed Adaptive Entropy-aware Optimization improves unknown class det

### `truncation_meta` (18 flaws)

- `XyB4VvF01X/flaw-1` [raw=candidate → post=downgraded] judge=paper_grounded
    - **title**: Insufficient Evidence for Core Claims
    - **desc**:  The current review state relies on truncated abstract and results snippets to support high-importance claims regarding hierarchical learning and specific performance gains (17.4% to 26.1%). Without the full methodologica
- `XyB4VvF01X/flaw-2` [raw=candidate → post=downgraded] judge=not_paper_grounded
    - **title**: Lack of Methodological Transparency
    - **desc**:  The abstract mentions 'hierarchical representations' but the provided text cuts off before explaining the architecture or the specific mechanism for hierarchy induction. This prevents a critique of whether the proposed m
- `GE6iywJtsV/flaw-1` [raw=candidate → post=downgraded] judge=not_paper_grounded
    - **title**: Incomplete Paper Excerpt Prevents Evidence Verification
    - **desc**:  The provided paper excerpt cuts off mid-sentence in the abstract ('However, existing models face challenges in reliably ...'). Consequently, the core claims regarding the model's novelty, the specific constraints applied

### `fallback_or_system_meta` (0 flaws)

_(none)_

### `boilerplate_generic` (1 flaws)

- `gzqrANCF4g/flaw-1` [raw=candidate → post=candidate] judge=not_paper_grounded
    - **title**: Overstated Performance Claim Without Evidence
    - **desc**:  Claim 1 asserts that the proposed video tokenizer enables LLMs to beat diffusion models. However, the provided abstract explicitly states that LLMs currently 'do not perform as well as diffusion models.' Without the full

### `substantive` (4 flaws)

- `WNxlJJIEVj/flaw-1` [raw=candidate → post=downgraded] judge=paper_grounded
    - **title**: Unsubstantiated Assumption of State Separability
    - **desc**:  Claim-2 asserts that states in high-return trajectories have a 'clear boundary' from low-return trajectories. This is a strong geometric assumption that is rarely true in complex environments (e.g., high-return states of
- `WNxlJJIEVj/flaw-2` [raw=candidate → post=downgraded] judge=paper_grounded
    - **title**: Circularity in Problem Definition and Solution
    - **desc**:  The paper identifies the problem as 'low-return trajectory ratios' and proposes a solution that generates 'high-return states'. However, the method relies on a Contrastive Module to distinguish these states. If the under
- `HPuLU6q7xq/flaw-2` [raw=candidate → post=downgraded] judge=not_paper_grounded
    - **title**: Missing Empirical Validation
    - **desc**:  The abstract mentions enhancing role-playing abilities but provides no data, metrics, or experimental results to support the efficacy of the proposed framework. A review cannot assess performance claims without results.

## How to interpret

- The `type_distribution` row answers *"where does the flaw stream spend its volume?"* — a healthy system wants `substantive` to dominate; high `schema_dump` / `fallback_or_system_meta` counts mean workers or fallback paths are leaking into flaws.
- The `visible post-hygiene` column equals what the reviewer ultimately sees. **Every non-`substantive` type should drop to near 0 here** — if not, the hygiene layer has a gap for that type.
- The `hygiene_precision` column quantifies how often hygiene's filtering decision agrees with the LLM judge on a per-type basis. `schema_dump` / `truncation_meta` should be ~1.0 (easy, hygiene nearly never wrong). `boilerplate_generic` is the hardest type and where hygiene FN rate is expected to be highest.
- Pair this table with `GROUNDED_JUDGE_V1.md` (overall `Hygiene_Precision`) and `AUDIT_META_LEAKAGE_V1.md` (for meta-leakage text indicators).

Generated by `scripts/audit_hygiene_gap_types_v1.py`.
