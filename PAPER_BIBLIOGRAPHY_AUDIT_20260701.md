# Paper Bibliography Audit

Date: 2026-07-01

Status: bibliography cleanup audit for `PAPER_REFERENCES_DRAFT_20260701.bib`. This is not a claim about DrMAS results. It records which references were normalized, which metadata sources were used, and which records still need venue-template verification before submission.

## Summary

The draft bibliography has been upgraded from placeholder-style records to cleaner BibTeX:

- removed `others` author placeholders;
- removed `note = {Draft metadata ...}` fields;
- expanded arXiv author lists from arXiv metadata;
- replaced confirmed ACL papers with ACL Anthology-style proceedings records;
- replaced confirmed NeurIPS papers with proceedings records where DBLP/Crossref metadata was available;
- kept uncertain or arXiv-only records as `@misc` instead of inventing venue metadata.

This improves citation readiness, but the bibliography is still not camera-ready. Before submission, export final records from the target venue's preferred bibliography source and re-check style requirements.

## Record-Level Audit

| Key | Current Entry Type | Metadata Basis | Remaining Risk |
| --- | --- | --- | --- |
| `liang2023llmfeedback` | `@misc` arXiv | arXiv metadata for `2310.01783`; Semantic Scholar previously indicated a venue, but live venue metadata was not stable enough to encode here | Verify whether final journal/venue metadata should replace arXiv |
| `lewis2020rag` | `@inproceedings` NeurIPS | DBLP returned NeurIPS 2020 proceedings URL and full author list; arXiv author list cross-checked | Add page range if target style requires it |
| `gao2023alce` | `@misc` arXiv | arXiv metadata for `2305.14627`; ACL/Crossref lookup did not return a stable venue record in this pass | Verify final venue if published |
| `wadden2020scifact` | `@inproceedings` EMNLP | ACL Anthology BibTeX for `2020.emnlp-main.609`; Crossref DOI matched | Low; re-export from ACL before final submission |
| `thorne2018fever` | `@inproceedings` NAACL | ACL Anthology BibTeX for `N18-1074`; DBLP DOI matched | Low; re-export from ACL before final submission |
| `rashkin2021attribution` | `@misc` arXiv | arXiv metadata for `2112.12870` | Verify if a final venue record exists |
| `wu2023autogen` | `@misc` arXiv | arXiv metadata and DBLP CoRR record | Keep as arXiv unless a final venue record is required |
| `li2023camel` | `@inproceedings` NeurIPS | DBLP returned NeurIPS 2023 proceedings URL; arXiv author list cross-checked | Verify exact title capitalization and page range |
| `madaan2023selfrefine` | `@inproceedings` NeurIPS | DBLP returned NeurIPS 2023 proceedings URL; arXiv author list cross-checked | Verify page range |
| `shinn2023reflexion` | `@inproceedings` NeurIPS | Crossref returned NeurIPS 36, DOI, and pages; arXiv supplied full author list including Edward Berman | Verify final NeurIPS BibTeX because Crossref author list omitted one arXiv author |
| `lawrence2020argumentmining` | `@article` | Crossref DOI `10.1162/coli_a_00364` returned journal, volume, issue, pages, and authors | Low; re-export from publisher if needed |

## Current Citation Coverage

The continuous manuscript currently uses 11 bibliography keys across 14 citation occurrences. The coverage is adequate for a conservative draft:

- LLM-assisted peer review: `liang2023llmfeedback`
- retrieval-augmented and citation-grounded generation: `lewis2020rag`, `gao2023alce`, `wadden2020scifact`
- factuality, attribution, and verification: `rashkin2021attribution`, `thorne2018fever`, `wadden2020scifact`
- multi-agent LLM systems: `wu2023autogen`, `li2023camel`
- LLM self-correction: `madaan2023selfrefine`, `shinn2023reflexion`
- argument mining and evidence structure: `lawrence2020argumentmining`, `thorne2018fever`, `wadden2020scifact`

## Remaining Citation Gaps

These are not blockers for the current internal draft, but they are likely reviewer-facing weaknesses:

1. Add one or two more LLM peer-review/review-generation evaluation references beyond Liang et al. if the final related work section expands.
2. Add a structured peer-review, argument-state, or review-decision support reference if a strong ReviewState-adjacent prior work source is identified.
3. Decide whether ALCE and attribution references are sufficient for citation faithfulness, or whether the final venue expects a broader factuality literature slice.
4. Re-export final BibTeX in the style expected by the target venue.

## Checks Performed

The cleanup pass checked:

- arXiv metadata for arXiv IDs used in the bibliography;
- DBLP public API for NeurIPS/RAG/CAMEL/Self-Refine metadata where it responded;
- ACL Anthology BibTeX for FEVER and SciFact;
- Crossref DOI metadata for SciFact, Reflexion, and Argument Mining.

The pass deliberately avoided filling uncertain venue fields from memory.
