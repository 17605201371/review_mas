from __future__ import annotations

import hashlib
import math
import re
from collections import Counter, OrderedDict
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


_TOKEN_PATTERN = re.compile(r"[A-Za-z][A-Za-z0-9_-]{1,}|\d+(?:\.\d+)?")
_LATEX_HEADING_PATTERN = re.compile(
    r"(?m)^[ \t]*\\(?P<command>chapter|section|subsection|subsubsection|paragraph)\*?"
    r"(?:\[[^\]\n]*\])?\{(?P<heading>[^}\n]+)\}"
)
_MARKDOWN_HEADING_PATTERN = re.compile(r"(?m)^[ \t]*(?P<marks>#{1,6})[ \t]+(?P<heading>[^\n#].*?)[ \t]*#*[ \t]*$")
_PLAIN_HEADING_PATTERN = re.compile(
    r"(?m)^[ \t]*(?P<number>\d+(?:\.\d+){0,4})?[ \t]*"
    r"(?P<heading>Abstract|Introduction|Background|Related Work|Method(?:s|ology)?|Approach|"
    r"Model|Framework|Experiment(?:s)?|Evaluation(?:s)?|Results|Analysis|Ablation(?: Study)?|"
    r"Discussion|Limitation(?:s)?|Conclusion(?:s)?|Appendix)(?:[ \t]*[:.]?[ \t]*)$",
    re.IGNORECASE,
)
_ABSTRACT_ENV_PATTERN = re.compile(r"\\begin\{abstract\}(?P<body>.*?)\\end\{abstract\}", re.IGNORECASE | re.DOTALL)
_ENV_PATTERN = re.compile(
    r"\\begin\{(?P<env>table\*?|figure\*?|equation\*?|align\*?|gather\*?|itemize|enumerate)\}"
    r"(?P<body>.*?)\\end\{(?P=env)\}",
    re.IGNORECASE | re.DOTALL,
)
_CAPTION_PATTERN = re.compile(r"\\caption(?:\[[^\]]*\])?\{(?P<caption>[^{}]*(?:\{[^{}]*\}[^{}]*)*)\}", re.IGNORECASE)
_TEXT_CAPTION_PATTERN = re.compile(r"(?mi)^[ \t]*(?P<label>Table|Figure|Fig\.)[ \t]+(?P<number>[A-Za-z0-9.-]+)[ \t]*[:.]?[ \t]+(?P<caption>[^\n]+)$")

_SECTION_TYPE_PATTERNS: Sequence[Tuple[str, re.Pattern[str]]] = (
    ("abstract", re.compile(r"\babstract\b", re.IGNORECASE)),
    ("introduction", re.compile(r"\b(introduction|intro)\b", re.IGNORECASE)),
    ("related_work", re.compile(r"\b(related work|background|prior work)\b", re.IGNORECASE)),
    ("method", re.compile(r"\b(method|methods|methodology|approach|model|framework|architecture)\b", re.IGNORECASE)),
    ("results", re.compile(r"\b(experiment|experiments|evaluation|evaluations|results|benchmark)\b", re.IGNORECASE)),
    ("analysis", re.compile(r"\b(analysis|ablation|robustness|sensitivity|theory|proof|theorem)\b", re.IGNORECASE)),
    ("limitations", re.compile(r"\b(limitation|limitations|threats to validity)\b", re.IGNORECASE)),
    ("discussion", re.compile(r"\bdiscussion\b", re.IGNORECASE)),
    ("conclusion", re.compile(r"\b(conclusion|conclusions)\b", re.IGNORECASE)),
    ("appendix", re.compile(r"\b(appendix|supplementary|supplemental)\b", re.IGNORECASE)),
)

_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "has", "have", "in", "is", "it",
    "of", "on", "or", "our", "that", "the", "their", "this", "to", "using", "we", "with",
}


@dataclass(frozen=True)
class PaperSection:
    section_id: str
    section_type: str
    heading: str
    text: str
    source_span_start: int
    source_span_end: int
    parent_section_id: Optional[str]
    level: int
    confidence: float
    parser_mode: str


@dataclass(frozen=True)
class PaperArtifact:
    artifact_id: str
    artifact_type: str
    locator: str
    text: str
    source_span_start: int
    source_span_end: int
    section_id: Optional[str]
    confidence: float
    parser_mode: str


@dataclass(frozen=True)
class PaperSearchResult:
    result_id: str
    result_type: str
    section_type: str
    heading: str
    text: str
    source_span_start: int
    source_span_end: int
    score: float
    matched_terms: Tuple[str, ...]
    parser_mode: str


@dataclass(frozen=True)
class PaperCoverage:
    expected_section_types: Tuple[str, ...]
    found_section_types: Tuple[str, ...]
    missing_section_types: Tuple[str, ...]
    coverage_rate: float
    parser_modes: Tuple[str, ...]
    fallback_used: bool


@dataclass(frozen=True)
class _Heading:
    start: int
    end: int
    heading: str
    level: int
    parser_mode: str
    confidence: float


def _tokens(text: str) -> List[str]:
    return [token.lower() for token in _TOKEN_PATTERN.findall(text or "") if token.lower() not in _STOPWORDS]


def _section_type(heading: str) -> str:
    for section_type, pattern in _SECTION_TYPE_PATTERNS:
        if pattern.search(heading or ""):
            return section_type
    return "other"


def _content_bounds(text: str) -> Tuple[int, int]:
    begin = re.search(r"---\s*BEGIN\s+PAPER\s*---", text, re.IGNORECASE)
    end = re.search(r"---\s*END\s+PAPER\s*---", text, re.IGNORECASE)
    start_pos = begin.end() if begin else 0
    end_pos = end.start() if end and end.start() >= start_pos else len(text)
    return start_pos, end_pos


class PaperIndex:
    """Auditable structural index whose spans always refer to the original paper text."""

    def __init__(self, paper_text: str, *, chunk_size: int = 1800, chunk_overlap: int = 240) -> None:
        self.paper_text = str(paper_text or "")
        self.content_start, self.content_end = _content_bounds(self.paper_text)
        self.chunk_size = max(400, int(chunk_size))
        self.chunk_overlap = max(0, min(int(chunk_overlap), self.chunk_size // 2))
        self.sections = tuple(self._parse_sections())
        self.artifacts = tuple(self._parse_artifacts())
        self.parser_modes = tuple(sorted({item.parser_mode for item in self.sections + self.artifacts}))
        self.fallback_used = any(item.parser_mode == "sequential_chunk" for item in self.sections)
        self._sections_by_id = {section.section_id: section for section in self.sections}

    @property
    def source_hash(self) -> str:
        return hashlib.sha256(self.paper_text.encode("utf-8")).hexdigest()

    def _heading_candidates(self) -> List[_Heading]:
        candidates: List[_Heading] = []
        latex_levels = {"chapter": 1, "section": 1, "subsection": 2, "subsubsection": 3, "paragraph": 4}
        for match in _LATEX_HEADING_PATTERN.finditer(self.paper_text, self.content_start, self.content_end):
            candidates.append(_Heading(match.start(), match.end(), match.group("heading").strip(), latex_levels[match.group("command").lower()], "latex", 0.99))
        for match in _MARKDOWN_HEADING_PATTERN.finditer(self.paper_text, self.content_start, self.content_end):
            candidates.append(_Heading(match.start(), match.end(), match.group("heading").strip(), len(match.group("marks")), "markdown", 0.98))
        for match in _PLAIN_HEADING_PATTERN.finditer(self.paper_text, self.content_start, self.content_end):
            heading = match.group("heading").strip()
            number = match.group("number") or ""
            level = min(5, number.count(".") + 1) if number else 1
            candidates.append(_Heading(match.start(), match.end(), heading, level, "plain_heading", 0.86))

        candidates.sort(key=lambda item: (item.start, -item.confidence, item.end))
        deduped: List[_Heading] = []
        for candidate in candidates:
            if deduped and candidate.start < deduped[-1].end:
                continue
            deduped.append(candidate)
        return deduped

    def _parse_sections(self) -> List[PaperSection]:
        headings = self._heading_candidates()
        sections: List[PaperSection] = []
        if headings:
            if headings[0].start > self.content_start and self.paper_text[self.content_start:headings[0].start].strip():
                sections.append(self._make_section(len(sections), "preamble", "preamble", self.content_start, headings[0].start, None, 0, 0.72, "structural_preamble"))
            level_stack: List[Tuple[int, str]] = []
            for index, heading in enumerate(headings):
                end = headings[index + 1].start if index + 1 < len(headings) else self.content_end
                while level_stack and level_stack[-1][0] >= heading.level:
                    level_stack.pop()
                parent_id = level_stack[-1][1] if level_stack else None
                section_id = f"section-{len(sections) + 1:04d}"
                sections.append(
                    PaperSection(
                        section_id=section_id,
                        section_type=_section_type(heading.heading),
                        heading=heading.heading,
                        text=self.paper_text[heading.start:end],
                        source_span_start=heading.start,
                        source_span_end=end,
                        parent_section_id=parent_id,
                        level=heading.level,
                        confidence=heading.confidence,
                        parser_mode=heading.parser_mode,
                    )
                )
                level_stack.append((heading.level, section_id))
            return sections

        abstract = _ABSTRACT_ENV_PATTERN.search(self.paper_text, self.content_start, self.content_end)
        if abstract:
            sections.append(self._make_section(len(sections), "abstract", "abstract", abstract.start(), abstract.end(), None, 1, 0.96, "latex_environment"))
        chunk_start = self.content_start
        if abstract and abstract.start() <= self.content_start + 200:
            chunk_start = abstract.end()
        step = max(1, self.chunk_size - self.chunk_overlap)
        while chunk_start < self.content_end:
            chunk_end = min(self.content_end, chunk_start + self.chunk_size)
            if chunk_end < self.content_end:
                boundary = self.paper_text.rfind("\n\n", chunk_start + self.chunk_size // 2, chunk_end)
                if boundary > chunk_start:
                    chunk_end = boundary
            if self.paper_text[chunk_start:chunk_end].strip():
                sections.append(self._make_section(len(sections), f"Sequential chunk {len(sections) + 1}", "chunk", chunk_start, chunk_end, None, 1, 0.55, "sequential_chunk"))
            if chunk_end >= self.content_end:
                break
            chunk_start = max(chunk_start + 1, chunk_end - self.chunk_overlap)
        return sections

    def _make_section(
        self,
        index: int,
        heading: str,
        section_type: str,
        start: int,
        end: int,
        parent_id: Optional[str],
        level: int,
        confidence: float,
        parser_mode: str,
    ) -> PaperSection:
        return PaperSection(
            section_id=f"section-{index + 1:04d}",
            section_type=section_type,
            heading=heading,
            text=self.paper_text[start:end],
            source_span_start=start,
            source_span_end=end,
            parent_section_id=parent_id,
            level=level,
            confidence=confidence,
            parser_mode=parser_mode,
        )

    def _section_for_span(self, start: int, end: int) -> Optional[str]:
        containing = [section for section in self.sections if section.source_span_start <= start and end <= section.source_span_end]
        if not containing:
            return None
        containing.sort(key=lambda section: section.source_span_end - section.source_span_start)
        return containing[0].section_id

    def _parse_artifacts(self) -> List[PaperArtifact]:
        artifacts: List[PaperArtifact] = []
        for match in _ENV_PATTERN.finditer(self.paper_text, self.content_start, self.content_end):
            env = match.group("env").lower().rstrip("*")
            artifact_type = "equation" if env in {"equation", "align", "gather"} else "list" if env in {"itemize", "enumerate"} else env
            caption = _CAPTION_PATTERN.search(match.group(0))
            locator = caption.group("caption").strip() if caption else env
            artifacts.append(self._artifact(len(artifacts), artifact_type, locator, match.start(), match.end(), "latex_environment", 0.99))
            if caption:
                caption_start = match.start() + caption.start()
                caption_end = match.start() + caption.end()
                artifacts.append(self._artifact(len(artifacts), "caption", caption.group("caption").strip(), caption_start, caption_end, "latex_caption", 0.99))
        occupied = [(item.source_span_start, item.source_span_end) for item in artifacts]
        for match in _TEXT_CAPTION_PATTERN.finditer(self.paper_text, self.content_start, self.content_end):
            if any(start <= match.start() < end for start, end in occupied):
                continue
            locator = f"{match.group('label')} {match.group('number')}"
            artifacts.append(self._artifact(len(artifacts), "caption", locator, match.start(), match.end(), "text_caption", 0.9))
        return artifacts

    def _artifact(self, index: int, artifact_type: str, locator: str, start: int, end: int, parser_mode: str, confidence: float) -> PaperArtifact:
        return PaperArtifact(
            artifact_id=f"artifact-{index + 1:04d}",
            artifact_type=artifact_type,
            locator=locator,
            text=self.paper_text[start:end],
            source_span_start=start,
            source_span_end=end,
            section_id=self._section_for_span(start, end),
            confidence=confidence,
            parser_mode=parser_mode,
        )

    def get_section(self, section_id: str) -> Optional[PaperSection]:
        return self._sections_by_id.get(str(section_id or ""))

    def get_span(self, start: int, end: int) -> str:
        if start < 0 or end < start or end > len(self.paper_text):
            raise ValueError("span is outside the original paper text")
        return self.paper_text[start:end]

    def search(self, query: str, section_types: Optional[Sequence[str]] = None, top_k: int = 5) -> List[PaperSearchResult]:
        query_tokens = _tokens(query)
        if not query_tokens or top_k <= 0:
            return []
        allowed = {item.lower() for item in section_types or []}
        documents: List[Tuple[str, str, str, str, int, int, str]] = []
        for section in self.sections:
            if allowed and section.section_type not in allowed:
                continue
            documents.append((section.section_id, "section", section.section_type, section.heading, section.source_span_start, section.source_span_end, section.parser_mode))
        for artifact in self.artifacts:
            artifact_section = self.get_section(artifact.section_id or "")
            section_type = artifact_section.section_type if artifact_section else artifact.artifact_type
            if allowed and section_type not in allowed and artifact.artifact_type not in allowed:
                continue
            documents.append((artifact.artifact_id, "artifact", section_type, artifact.locator, artifact.source_span_start, artifact.source_span_end, artifact.parser_mode))
        if not documents:
            return []

        tokenized = [Counter(_tokens(self.paper_text[start:end])) for _, _, _, _, start, end, _ in documents]
        document_frequency = Counter(token for counts in tokenized for token in counts)
        total_documents = len(documents)
        results: List[PaperSearchResult] = []
        for document, counts in zip(documents, tokenized):
            matched = sorted({token for token in query_tokens if counts.get(token, 0)})
            if not matched:
                continue
            length_norm = 1.0 + math.log1p(sum(counts.values()))
            score = sum((1.0 + math.log1p(counts[token])) * math.log((total_documents + 1.0) / (document_frequency[token] + 0.5)) for token in matched) / length_norm
            result_id, result_type, section_type, heading, start, end, parser_mode = document
            results.append(PaperSearchResult(result_id, result_type, section_type, heading, self.paper_text[start:end], start, end, score, tuple(matched), parser_mode))
        results.sort(key=lambda item: (-item.score, item.source_span_start, item.result_id))
        return results[:top_k]

    def coverage(self, expected_section_types: Iterable[str]) -> PaperCoverage:
        expected = tuple(dict.fromkeys(str(item).strip().lower() for item in expected_section_types if str(item).strip()))
        found_set = {section.section_type for section in self.sections}
        found = tuple(item for item in expected if item in found_set)
        missing = tuple(item for item in expected if item not in found_set)
        return PaperCoverage(expected, found, missing, len(found) / len(expected) if expected else 1.0, self.parser_modes, self.fallback_used)

    def audit_summary(self) -> Dict[str, object]:
        return {
            "source_hash": self.source_hash,
            "source_chars": len(self.paper_text),
            "content_span_start": self.content_start,
            "content_span_end": self.content_end,
            "section_count": len(self.sections),
            "artifact_count": len(self.artifacts),
            "section_type_counts": dict(Counter(item.section_type for item in self.sections)),
            "artifact_type_counts": dict(Counter(item.artifact_type for item in self.artifacts)),
            "parser_modes": list(self.parser_modes),
            "fallback_used": self.fallback_used,
            "span_roundtrip_ok": all(self.get_span(item.source_span_start, item.source_span_end) == item.text for item in self.sections + self.artifacts),
        }


_INDEX_CACHE: "OrderedDict[Tuple[str, int, int], PaperIndex]" = OrderedDict()


def build_paper_index(paper_text: str, *, chunk_size: int = 1800, chunk_overlap: int = 240, cache_size: int = 32) -> PaperIndex:
    text = str(paper_text or "")
    key = (hashlib.sha256(text.encode("utf-8")).hexdigest(), int(chunk_size), int(chunk_overlap))
    cached = _INDEX_CACHE.get(key)
    if cached is not None and cached.paper_text == text:
        _INDEX_CACHE.move_to_end(key)
        return cached
    index = PaperIndex(text, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    _INDEX_CACHE[key] = index
    _INDEX_CACHE.move_to_end(key)
    while len(_INDEX_CACHE) > max(1, int(cache_size)):
        _INDEX_CACHE.popitem(last=False)
    return index
