# Bibliography Candidates

Date: 2026-07-01

Status: verified candidate list and bibliography provenance note. This file maps the current related-work citation placeholders to papers whose metadata was checked through public metadata APIs during drafting. It is intended to reduce hallucinated citations before turning the continuous draft into a camera-ready manuscript.

Verification sources used in this pass:

- Semantic Scholar Graph API for the LLM peer-review paper during the initial candidate pass.
- arXiv API for arXiv papers and full author lists.
- DBLP public API for several NeurIPS/CoRR proceedings records.
- ACL Anthology BibTeX for FEVER and SciFact.
- Crossref API for DOI-backed conference/journal entries.

Do not treat this as a final camera-ready bibliography. Before submission, export venue-style BibTeX from DBLP, ACL Anthology, arXiv, Crossref, or publisher pages and re-check author lists.

Cleaned draft BibTeX file: `PAPER_REFERENCES_DRAFT_20260701.bib`.

Bibliography audit: `PAPER_BIBLIOGRAPHY_AUDIT_20260701.md`.

## Placeholder Mapping

| Placeholder in draft | Candidate references | Current status |
| --- | --- | --- |
| `[CITATION: LLM peer-review evaluation]` | Liang et al., "Can large language models provide useful feedback on research papers? A large-scale empirical analysis" | arXiv metadata used in cleaned BibTeX; final venue metadata still pending |
| `[CITATION: RAG and grounded scientific assistance]` | Lewis et al., "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks"; Gao et al., "Enabling Large Language Models to Generate Text with Citations"; Wadden et al., "Fact or Fiction: Verifying Scientific Claims" | Lewis verified via DBLP/NeurIPS; Gao kept as arXiv; Wadden verified via ACL/Crossref |
| `[CITATION: factuality and attribution verification]` | Rashkin et al., "Measuring Attribution in Natural Language Generation Models"; Thorne et al., "FEVER"; Wadden et al., "Fact or Fiction" | Rashkin kept as arXiv; Thorne and Wadden verified via ACL/Crossref |
| `[CITATION: multi-agent LLM systems]` | Wu et al., "AutoGen"; Li et al., "CAMEL" | AutoGen kept as arXiv/CoRR; CAMEL verified via DBLP/NeurIPS |
| `[CITATION: LLM self-correction]` | Madaan et al., "Self-Refine"; Shinn et al., "Reflexion" | Self-Refine verified via DBLP/NeurIPS; Reflexion verified via Crossref/NeurIPS plus arXiv author list |
| `[CITATION: argument mining and evidence graphs]` | Lawrence and Reed, "Argument Mining: A Survey"; Thorne et al., "FEVER"; Wadden et al., "Fact or Fiction" | Lawrence verified via Crossref; Thorne and Wadden verified via ACL/Crossref |

## Verified Candidate Details

### LLM-Assisted Peer Review

1. Weixin Liang et al. "Can large language models provide useful feedback on research papers? A large-scale empirical analysis."
   - Metadata source: Semantic Scholar Graph API.
   - Year returned: 2023.
   - Venue returned: NEJM AI.
   - External IDs returned: arXiv `2310.01783`, DOI `10.48550/arXiv.2310.01783`.
   - Use for: motivating LLM peer-review feedback and review-generation evaluation.
   - Caution: verify final venue/publisher metadata before final BibTeX.

### Retrieval-Augmented And Grounded Generation

2. Patrick Lewis et al. "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks."
   - Metadata source: DBLP and arXiv API.
   - arXiv: `2005.11401`.
   - Venue record returned: NeurIPS 2020.
   - First arXiv date returned: 2020-05-22.
   - Use for: retrieval-augmented generation background.
   - Caution: add final venue page range if required.

3. Tianyu Gao, Howard Yen, Jiatong Yu, and Danqi Chen. "Enabling Large Language Models to Generate Text with Citations."
   - Metadata source: arXiv API.
   - arXiv: `2305.14627`.
   - First arXiv date returned: 2023-05-24.
   - Use for: citation-grounded generation and generated text with citations.

### Scientific Claim Verification And Factuality

4. David Wadden, Shanchuan Lin, Kyle Lo, Lucy Lu Wang, Madeleine van Zuylen, Arman Cohan, and Hannaneh Hajishirzi. "Fact or Fiction: Verifying Scientific Claims."
   - Metadata source: ACL Anthology BibTeX, Crossref DOI metadata, and arXiv API.
   - arXiv: `2004.14974`.
   - ACL Anthology: `2020.emnlp-main.609`.
   - First arXiv date returned: 2020-04-30.
   - Use for: scientific claim verification and evidence grounding.

5. James Thorne, Andreas Vlachos, Christos Christodoulopoulos, and Arpit Mittal. "FEVER: a Large-scale Dataset for Fact Extraction and VERification."
   - Metadata source: ACL Anthology BibTeX, DBLP, and Crossref API.
   - Year returned: 2018.
   - DOI: `10.18653/v1/n18-1074`.
   - Container returned: NAACL-HLT 2018, Volume 1 (Long Papers).
   - Use for: fact extraction and verification background.

6. Hannah Rashkin et al. "Measuring Attribution in Natural Language Generation Models."
   - Metadata source: arXiv API.
   - arXiv: `2112.12870`.
   - First arXiv date returned: 2021-12-23.
   - Use for: attribution and attributable generation.
   - Caution: the earlier placeholder phrase "Attributable to Identified Sources" did not verify as an exact title in this pass; use this verified attribution paper unless a better exact source is later found.

### Agentic LLM Systems And Self-Correction

7. Qingyun Wu et al. "AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation."
   - Metadata source: arXiv API.
   - arXiv: `2308.08155`.
   - First arXiv date returned: 2023-08-16.
   - Use for: multi-agent LLM systems.

8. Guohao Li, Hasan Abed Al Kader Hammoud, Hani Itani, Dmitrii Khizbullin, and Bernard Ghanem. "CAMEL: Communicative Agents for \"Mind\" Exploration of Large Language Model Society."
   - Metadata source: DBLP and arXiv API.
   - arXiv: `2303.17760`.
   - Venue record returned: NeurIPS 2023.
   - First arXiv date returned: 2023-03-31.
   - Use for: multi-agent communicative LLM systems.

9. Aman Madaan et al. "Self-Refine: Iterative Refinement with Self-Feedback."
   - Metadata source: DBLP and arXiv API.
   - arXiv: `2303.17651`.
   - Venue record returned: NeurIPS 2023.
   - First arXiv date returned: 2023-03-30.
   - Use for: LLM self-correction and iterative refinement.

10. Noah Shinn, Federico Cassano, Edward Berman, Ashwin Gopinath, Karthik Narasimhan, and Shunyu Yao. "Reflexion: Language Agents with Verbal Reinforcement Learning."
    - Metadata source: Crossref and arXiv API.
    - arXiv: `2303.11366`.
    - Venue record returned: NeurIPS 2023.
    - DOI returned: `10.52202/075280-0377`.
    - First arXiv date returned: 2023-03-20.
    - Use for: language-agent reflection and self-improvement.

### Argument Mining And Claim-Evidence Structure

11. John Lawrence and Chris Reed. "Argument Mining: A Survey."
    - Metadata source: Crossref API.
    - Year returned: 2020.
    - DOI: `10.1162/coli_a_00364`.
    - Container returned: Computational Linguistics.
    - Use for: argument mining and claim/relation structure background.

## Remaining Citation Gaps

These areas still need better venue-specific citations before final submission:

1. A second or third LLM peer-review evaluation paper beyond Liang et al.
2. A paper specifically about LLM review generation benchmarks, if the final related work needs more coverage.
3. A structured peer-review or decision-support reference, if available, to support the ReviewState framing.
4. A citation for citation-faithfulness evaluation beyond ALCE, if the venue expects broader factuality coverage.

## How To Use In The Draft

Recommended placeholder replacements:

```text
[CITATION: LLM peer-review evaluation]
  -> \citep{liang2023llmfeedback}

[CITATION: RAG and grounded scientific assistance]
  -> \citep{lewis2020rag,gao2023alce,wadden2020scifact}

[CITATION: factuality and attribution verification]
  -> \citep{rashkin2021attribution,thorne2018fever,wadden2020scifact}

[CITATION: multi-agent LLM systems]
  -> \citep{wu2023autogen,li2023camel}

[CITATION: LLM self-correction]
  -> \citep{madaan2023selfrefine,shinn2023reflexion}

[CITATION: argument mining and evidence graphs]
  -> \citep{lawrence2020argumentmining,thorne2018fever,wadden2020scifact}
```

Keep final prose conservative: these references situate DrMAS but do not prove the P28.6 result. The P28.6 result is supported by local artifacts, not by related work.
