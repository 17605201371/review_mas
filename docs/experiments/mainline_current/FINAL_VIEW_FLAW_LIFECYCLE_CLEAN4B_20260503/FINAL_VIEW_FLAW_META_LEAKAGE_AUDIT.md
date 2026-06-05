# Final-View Flaw Meta-Leakage Audit v1

## Aggregate

| metric | value |
|---|---:|
| `flaw_excerpt_limitation` | 7 |
| `flaw_fallback_or_malformed_artifact` | 15 |
| `flaw_grounded_candidate` | 8 |
| `flaw_grounded_confirmed_flaw` | 2 |
| `flaw_system_meta_limitation` | 3 |
| `flaw_ungrounded_candidate` | 16 |
| `gap_fallback_or_malformed_artifact` | 12 |
| `gap_paper_evidence_gap` | 135 |
| `unresolved_excerpt_limitation` | 17 |
| `unresolved_fallback_or_malformed_artifact` | 10 |
| `unresolved_paper_grounded_unresolved` | 1 |
| `unresolved_system_meta_limitation` | 1 |
| `unresolved_ungrounded_unresolved` | 161 |

## Meta / Artifact Flaw Examples

| paper_id | category | severity | status | title | excerpt |
|---|---|---|---|---|---|
| ye3NrNrYOY | system_meta_limitation | minor | downgraded | The user wants me to act as the "Critique Agent" in a multi-agent system reviewi | The user wants me to act as the "Critique Agent" in a multi-agent system reviewing an academic paper. I need to output a The user wants me to act as the "Critique Agent" in a multi |
| WNxlJJIEVj | fallback_or_malformed_artifact | minor | downgraded | { "flaw_candidates": [ { "flaw_id": "flaw-1", "title": "Lack of Empirical Valida | { "flaw_candidates": [ { "flaw_id": "flaw-1", "title": "Lack of Empirical Validation for Core Mechanism", "description": { "flaw_candidates": [ { "flaw_id": "flaw-1", "title": "Lac |
| uOrfve3prk | fallback_or_malformed_artifact | minor | downgraded | { "flaw_candidates": [ { "flaw_id": "flaw-1", "title": "Lack of empirical valida | { "flaw_candidates": [ { "flaw_id": "flaw-1", "title": "Lack of empirical validation for the proposed encoder-decoder fr { "flaw_candidates": [ { "flaw_id": "flaw-1", "title": "Lac |
| hj323oR3rw | fallback_or_malformed_artifact | minor | downgraded | { "flaw_candidates": [ { "flaw_id": "flaw-1", "title": "Lack of Empirical Valida | { "flaw_candidates": [ { "flaw_id": "flaw-1", "title": "Lack of Empirical Validation for Multimodal Complexity Claims", { "flaw_candidates": [ { "flaw_id": "flaw-1", "title": "Lack |
| QAAsnSRwgu | fallback_or_malformed_artifact | minor | downgraded | { "flaw_candidates": [ { "flaw_id": "flaw-evidence-gap-1", "title": "Lack of Emp | { "flaw_candidates": [ { "flaw_id": "flaw-evidence-gap-1", "title": "Lack of Empirical Validation for PDDL Integration", { "flaw_candidates": [ { "flaw_id": "flaw-evidence-gap-1",  |
| WpXq5n8yLb | system_meta_limitation | minor | downgraded | The user wants me to act as the "Critique Agent" in a multi-agent review system. | The user wants me to act as the "Critique Agent" in a multi-agent review system. My task is to identify concrete flaws, The user wants me to act as the "Critique Agent" in a multi- |
| X41c4uB4k0 | fallback_or_malformed_artifact | minor | downgraded | { "flaw_candidates": [ { "flaw_id": "flaw-1", "title": "Lack of quantitative evi | { "flaw_candidates": [ { "flaw_id": "flaw-1", "title": "Lack of quantitative evidence for training-free claim", "descrip { "flaw_candidates": [ { "flaw_id": "flaw-1", "title": "Lac |
| NnExMNiTHw | excerpt_limitation | major | candidate | Missing Methodological Details for Adaptive Mechanism | Missing Methodological Details for Adaptive Mechanism The paper claims SpecDec++ uses a trained acceptance prediction head to adaptively determine candidate lengths, but the excerp |
| gzqrANCF4g | excerpt_limitation | critical | candidate | Incomplete Paper Text Prevents Valid Claim Extraction and Evidence Verification | Incomplete Paper Text Prevents Valid Claim Extraction and Evidence Verification The provided paper excerpt is truncated mid-sentence ('...appropriate for LLM learning. In this pape |
| cklg91aPGk | fallback_or_malformed_artifact | minor | downgraded | { "flaw_candidates": [ { "flaw_id": "flaw-1", "title": "Lack of quantitative met | { "flaw_candidates": [ { "flaw_id": "flaw-1", "title": "Lack of quantitative metrics for 'competitive results'", "descri { "flaw_candidates": [ { "flaw_id": "flaw-1", "title": "Lac |
| HPuLU6q7xq | fallback_or_malformed_artifact | minor | downgraded | { "flaw_candidates": [ { "flaw_id": "flaw-1", "title": "Insufficient Evidence fo | { "flaw_candidates": [ { "flaw_id": "flaw-1", "title": "Insufficient Evidence for Core Framework Claims", "description": { "flaw_candidates": [ { "flaw_id": "flaw-1", "title": "Ins |
| KI9NqjLVDT | excerpt_limitation | critical | candidate | Claims lack grounding in provided text excerpt | Claims lack grounding in provided text excerpt The provided paper excerpt is truncated and does not contain the experimental results or methodological details required to verify cl |
| 1HCN4pjTb4 | fallback_or_malformed_artifact | minor | downgraded | { "flaw_candidates": [ { "flaw_id": "flaw-1", "title": "Lack of empirical ground | { "flaw_candidates": [ { "flaw_id": "flaw-1", "title": "Lack of empirical grounding for NC1 claim", "description": "Clai { "flaw_candidates": [ { "flaw_id": "flaw-1", "title": "Lac |
| mHv6wcBb0z | excerpt_limitation | major | candidate | Lack of Concrete Experimental Evidence for Model Collapse Claim | Lack of Concrete Experimental Evidence for Model Collapse Claim The paper asserts that DCCA suffers from 'model collapse' where performance drops drastically during training, but t |
| mHv6wcBb0z | excerpt_limitation | major | candidate | Missing Validation of Proposed Noise Regularization Method | Missing Validation of Proposed Noise Regularization Method While the paper introduces a noise regularization method to address model collapse, there is no evidence provided in the  |
| KOUAayk5Kx | fallback_or_malformed_artifact | minor | downgraded | { "flaw_candidates": [ { "flaw_id": "flaw-1", "title": "Lack of quantitative evi | { "flaw_candidates": [ { "flaw_id": "flaw-1", "title": "Lack of quantitative evidence for 'multi-model forgetting' pheno { "flaw_candidates": [ { "flaw_id": "flaw-1", "title": "Lac |
| XH3OiIhtvf | fallback_or_malformed_artifact | minor | downgraded | { "flaw_candidates": [ { "flaw_id": "flaw-1", "title": "Lack of Empirical Valida | { "flaw_candidates": [ { "flaw_id": "flaw-1", "title": "Lack of Empirical Validation for GAN-Based Data Diversification" { "flaw_candidates": [ { "flaw_id": "flaw-1", "title": "Lac |
| ZHr0JajZfH | system_meta_limitation | minor | downgraded | The user wants me to act as the "Critique Agent" in a multi-agent review system. | The user wants me to act as the "Critique Agent" in a multi-agent review system. My current task is to analyze flaws in The user wants me to act as the "Critique Agent" in a multi- |
| WLgbjzKJkk | excerpt_limitation | critical | candidate | Incomplete Abstract Prevents Claim Verification | Incomplete Abstract Prevents Claim Verification The provided paper text is truncated mid-sentence in the abstract ('...s'), and critical sections including the full methodology, ex |
| 9JRsAj3ymy | fallback_or_malformed_artifact | minor | downgraded | { "flaw_candidates": [ { "flaw_id": "flaw-1", "title": "Lack of Empirical Eviden | { "flaw_candidates": [ { "flaw_id": "flaw-1", "title": "Lack of Empirical Evidence for TSR and TF-TSR Claims", "descript { "flaw_candidates": [ { "flaw_id": "flaw-1", "title": "Lac |

## 结论

当前 final view 中存在大量 excerpt / system / fallback / malformed artifact 类负面项。这些项适合进入 Review Limitations 或 Potential Concerns，不应直接作为 confirmed paper weakness。
