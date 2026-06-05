# Final-View Flaw Meta-Leakage Audit v1

## Aggregate

| metric | value |
|---|---:|
| `flaw_excerpt_limitation` | 17 |
| `flaw_fallback_or_malformed_artifact` | 20 |
| `flaw_grounded_candidate` | 1 |
| `flaw_grounded_confirmed_flaw` | 3 |
| `flaw_system_meta_limitation` | 1 |
| `flaw_ungrounded_candidate` | 16 |
| `gap_fallback_or_malformed_artifact` | 27 |
| `gap_paper_evidence_gap` | 128 |
| `unresolved_excerpt_limitation` | 16 |
| `unresolved_fallback_or_malformed_artifact` | 18 |
| `unresolved_system_meta_limitation` | 3 |
| `unresolved_ungrounded_unresolved` | 172 |

## Meta / Artifact Flaw Examples

| paper_id | category | severity | status | title | excerpt |
|---|---|---|---|---|---|
| ye3NrNrYOY | excerpt_limitation | major | candidate | Lack of concrete evidence for core methodological claims | Lack of concrete evidence for core methodological claims The paper excerpt cuts off mid-sentence ('...we hold certain aspects of the ca'), preventing verification of the specific m |
| ye3NrNrYOY | excerpt_limitation | major | candidate | Missing experimental validation data | Missing experimental validation data Claim 3 asserts evaluation on specific datasets (Sth-Else) and protocols (all-way-k-shot), but no results, tables, or figures are provided in t |
| WNxlJJIEVj | fallback_or_malformed_artifact | major | candidate | { "flaw_candidates": [ { "flaw_id": "flaw-1", "title": "Lack of Empirical Valida | { "flaw_candidates": [ { "flaw_id": "flaw-1", "title": "Lack of Empirical Validation for Sensitivity Claims", "descripti { "flaw_candidates": [ { "flaw_id": "flaw-1", "title": "Lac |
| uOrfve3prk | fallback_or_malformed_artifact | major | candidate | { "flaw_candidates": [ { "flaw_id": "flaw-1", "title": "Claim-3 lacks concrete e | { "flaw_candidates": [ { "flaw_id": "flaw-1", "title": "Claim-3 lacks concrete evidence from Figure 1 or text", "descrip { "flaw_candidates": [ { "flaw_id": "flaw-1", "title": "Cla |
| hj323oR3rw | fallback_or_malformed_artifact | major | candidate | { "flaw_candidates": [ { "flaw_id": "flaw-1", "title": "Lack of Empirical Valida | { "flaw_candidates": [ { "flaw_id": "flaw-1", "title": "Lack of Empirical Validation for Novelty and Mechanism Claims", { "flaw_candidates": [ { "flaw_id": "flaw-1", "title": "Lack |
| 7Dub7UXTXN | fallback_or_malformed_artifact | major | candidate | { "flaw_candidates": [ { "flaw_id": "flaw-1", "title": "Lack of Mathematical Rig | { "flaw_candidates": [ { "flaw_id": "flaw-1", "title": "Lack of Mathematical Rigor in Expressivity Claim", "description" { "flaw_candidates": [ { "flaw_id": "flaw-1", "title": "Lac |
| 9zEBK3E9bX | fallback_or_malformed_artifact | major | candidate | { "flaw_candidates": [ { "flaw_id": "flaw-1", "title": "Lack of concrete experim | { "flaw_candidates": [ { "flaw_id": "flaw-1", "title": "Lack of concrete experimental evidence for general representatio { "flaw_candidates": [ { "flaw_id": "flaw-1", "title": "Lac |
| XyB4VvF01X | fallback_or_malformed_artifact | major | candidate | { "flaw_candidates": [ { "flaw_id": "flaw-1", "title": "Lack of quantitative per | { "flaw_candidates": [ { "flaw_id": "flaw-1", "title": "Lack of quantitative performance metrics for G2T's online learni { "flaw_candidates": [ { "flaw_id": "flaw-1", "title": "Lac |
| GE6iywJtsV | excerpt_limitation | major | candidate | Lack of concrete evidence for core architectural claims | Lack of concrete evidence for core architectural claims The provided text snippet is incomplete and cuts off mid-sentence in the abstract, failing to describe the specific mechanis |
| GE6iywJtsV | excerpt_limitation | major | candidate | Incomplete methodological description prevents verification of constraints | Incomplete methodological description prevents verification of constraints Without the full text of the method section, it is impossible to verify if the model actually enforces th |
| QAAsnSRwgu | excerpt_limitation | critical | confirmed | Incomplete Abstract and Missing Results Sections | Incomplete Abstract and Missing Results Sections The provided paper excerpt terminates abruptly within the abstract, cutting off the description of Hive's execution capabilities. F |
| WpXq5n8yLb | fallback_or_malformed_artifact | major | candidate | { "flaw_candidates": [ { "flaw_id": "flaw-1", "title": "Missing concrete evidenc | { "flaw_candidates": [ { "flaw_id": "flaw-1", "title": "Missing concrete evidence for RNN architecture claim", "descript { "flaw_candidates": [ { "flaw_id": "flaw-1", "title": "Mis |
| X41c4uB4k0 | fallback_or_malformed_artifact | major | candidate | { "flaw_candidates": [ { "flaw_id": "flaw-1", "title": "Lack of Quantitative Met | { "flaw_candidates": [ { "flaw_id": "flaw-1", "title": "Lack of Quantitative Metrics for Multi-objective Generation", "d { "flaw_candidates": [ { "flaw_id": "flaw-1", "title": "Lac |
| NnExMNiTHw | excerpt_limitation | critical | candidate | Lack of quantitative evidence for adaptive candidate length improvements | Lack of quantitative evidence for adaptive candidate length improvements The paper claims that adaptive candidate lengths improve speculative decoding performance (claim-1) and tha |
| gzqrANCF4g | excerpt_limitation | major | candidate | Lack of Quantitative Metrics and Experimental Setup Details | Lack of Quantitative Metrics and Experimental Setup Details The provided text (abstract) makes strong comparative claims about LLM performance versus Diffusion models and the effic |
| a6SntIisgg | fallback_or_malformed_artifact | major | candidate | { "flaw_candidates": [ { "flaw_id": "flaw-1", "title": "Lack of concrete evidenc | { "flaw_candidates": [ { "flaw_id": "flaw-1", "title": "Lack of concrete evidence for encoder architecture claims", "des { "flaw_candidates": [ { "flaw_id": "flaw-1", "title": "Lac |
| HPuLU6q7xq | fallback_or_malformed_artifact | major | candidate | { "flaw_candidates": [ { "flaw_id": "flaw-1", "title": "Lack of concrete evidenc | { "flaw_candidates": [ { "flaw_id": "flaw-1", "title": "Lack of concrete evidence for Orca framework architecture", "des { "flaw_candidates": [ { "flaw_id": "flaw-1", "title": "Lac |
| fGXyvmWpw6 | fallback_or_malformed_artifact | major | candidate | { "flaw_candidates": [ { "flaw_id": "flaw-1", "title": "Lack of empirical eviden | { "flaw_candidates": [ { "flaw_id": "flaw-1", "title": "Lack of empirical evidence for the amplification of heterogeneit { "flaw_candidates": [ { "flaw_id": "flaw-1", "title": "Lac |
| KI9NqjLVDT | excerpt_limitation | major | candidate | Lack of quantitative performance metrics for Claim 2 | Lack of quantitative performance metrics for Claim 2 The abstract claims ReMasker performs on par with or outperforms active models, but the provided text contains no numerical res |
| 1HCN4pjTb4 | fallback_or_malformed_artifact | major | candidate | { "flaw_candidates": [ { "flaw_id": "flaw-1", "title": "Lack of concrete theoret | { "flaw_candidates": [ { "flaw_id": "flaw-1", "title": "Lack of concrete theoretical proof for end-to-end Neural Collaps { "flaw_candidates": [ { "flaw_id": "flaw-1", "title": "Lac |

## 结论

当前 final view 中存在大量 excerpt / system / fallback / malformed artifact 类负面项。这些项适合进入 Review Limitations 或 Potential Concerns，不应直接作为 confirmed paper weakness。
