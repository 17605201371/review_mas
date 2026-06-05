# Hygiene Gap Types Audit v1 (offline; 0 LLM calls)

- input jsonl: `outputs/results_main/review_infer/mainline_final_v1_flaw_fix_dprime2_9b_fulltest39_20260507.jsonl`
- judge source: `outputs/results_main/review_infer/grounded_judge_v1.json`
- n_papers: **32**
- n_flaws: **62**

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
| `schema_dump` | 0 | 0 | 0 |
| `truncation_meta` | 17 | 0 | 17 |
| `fallback_or_system_meta` | 0 | 0 | 0 |
| `boilerplate_generic` | 0 | 0 | 0 |
| `substantive` | 45 | 23 | 22 |

## Parity with `state.py::_is_fallback_or_meta_flaw`

- state.py classifies **18** flaws as meta/fallback.
- Of those, **17** also classified as non-`substantive` here.
- Agreement rate with state.py: **0.9444** (high agreement validates the classifier; low agreement signals drift to investigate).

## Hygiene diagnostics per type

*For flaws that hygiene filtered out (raw=candidate/confirmed → post=downgraded/retracted), how many did the LLM judge also flag as `not_paper_grounded` (hygiene correct) vs `paper_grounded` (hygiene false negative)? Only flaws with a judge verdict are counted in the denominator.*

| type | filtered | with_judge | correctly filtered | hygiene FN | hygiene_precision |
|---|---:|---:|---:|---:|---:|
| `truncation_meta` | 17 | 3 | 2 | 1 | 0.6667 |
| `substantive` | 22 | 6 | 2 | 4 | 0.3333 |

## Examples per type

### `schema_dump` (0 flaws)

_(none)_

### `truncation_meta` (17 flaws)

- `ye3NrNrYOY/flaw-2` [raw=candidate → post=downgraded] judge=—
    - **title**: Baseline comparison lacks methodological detail on 'fixed' components
    - **desc**:  Claim 2 states TCMT achieves better outcomes with fewer epochs compared to TCMT-FT (full fine-tuning). The text mentions holding 'transition function and mixing function fixed' but does not explicitly define these functi
- `7Dub7UXTXN/flaw-1` [raw=candidate → post=downgraded] judge=—
    - **title**: Lack of empirical validation for the 'low-rank weights' claim in deep networks
    - **desc**:  Claim claim-3 states that 'deep bias-free ReLU networks form low-rank weights similar to those in deep linear networks when the target function is linear.' However, the provided text and evidence map show no supporting e
- `7Dub7UXTXN/flaw-2` [raw=candidate → post=downgraded] judge=—
    - **title**: Missing proof details for the 'arbitrary input' expressivity result
    - **desc**:  The method section excerpt claims the authors prove that bias-free ReLU networks cannot represent odd functions 'for arbitrary input and use a simpler approach,' citing previous work for the sphere case. However, the pro

### `fallback_or_system_meta` (0 flaws)

_(none)_

### `boilerplate_generic` (0 flaws)

_(none)_

### `substantive` (45 flaws)

- `ye3NrNrYOY/flaw-1` [raw=candidate → post=candidate] judge=—
    - **title**: Ablation study lacks statistical significance testing and error bars
    - **desc**:  The ablation study in Section 3.3 claims performance increases with the number of latent causal variables (N), citing a figure (Figure 3 implied by context of N=4,8,12,16). However, the provided text and image placeholde
- `WNxlJJIEVj/flaw-1` [raw=candidate → post=downgraded] judge=paper_grounded
    - **title**: Lack of empirical validation for the core hypothesis regarding trajectory sensitivity
    - **desc**:  The paper asserts in the Abstract and Introduction that 'The performance of offline reinforcement learning (RL) is sensitive to the proportion of high-return trajectories in the offline dataset' and proposes a solution b
- `WNxlJJIEVj/flaw-2` [raw=candidate → post=downgraded] judge=paper_grounded
    - **title**: Unverified mechanism of state separation in generated trajectories
    - **desc**:  The paper claims the Contrastive Module 'pulls the states in generated trajectories toward high-return states and pushes them away from low-return states' (Abstract/Method). While the framework diagram (Figure) illustrat

## How to interpret

- The `type_distribution` row answers *"where does the flaw stream spend its volume?"* — a healthy system wants `substantive` to dominate; high `schema_dump` / `fallback_or_system_meta` counts mean workers or fallback paths are leaking into flaws.
- The `visible post-hygiene` column equals what the reviewer ultimately sees. **Every non-`substantive` type should drop to near 0 here** — if not, the hygiene layer has a gap for that type.
- The `hygiene_precision` column quantifies how often hygiene's filtering decision agrees with the LLM judge on a per-type basis. `schema_dump` / `truncation_meta` should be ~1.0 (easy, hygiene nearly never wrong). `boilerplate_generic` is the hardest type and where hygiene FN rate is expected to be highest.
- Pair this table with `GROUNDED_JUDGE_V1.md` (overall `Hygiene_Precision`) and `AUDIT_META_LEAKAGE_V1.md` (for meta-leakage text indicators).

Generated by `scripts/audit_hygiene_gap_types_v1.py`.
