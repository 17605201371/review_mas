from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from agent_system.environments.env_package.review.paper_index import PaperIndex, PaperSearchResult, build_paper_index


_QUERY_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "has", "have", "in", "is", "it",
    "of", "on", "or", "paper", "that", "the", "their", "this", "to", "using", "we", "with",
}

_ROLE_SECTION_PRIORITIES = {
    "claim": ("abstract", "introduction", "method", "results", "limitations", "conclusion"),
    "evidence": ("results", "analysis", "method", "limitations", "discussion", "conclusion", "abstract"),
    "critique": ("results", "analysis", "limitations", "discussion", "method", "related_work", "conclusion"),
}

_ROLE_SEED_QUERIES = {
    "claim": (
        "main contribution proposed method",
        "experiments results performance",
        "limitations scope conclusion",
    ),
    "evidence": (
        "results table metric baseline comparison",
        "method implementation training protocol",
    ),
    "critique": (
        "ablation baseline comparison protocol robustness",
        "limitation failure worse cost efficiency runtime",
        "statistical significance variance reproducibility hyperparameter",
    ),
}


@dataclass(frozen=True)
class RetrievalPlan:
    role: str
    queries: Tuple[str, ...]
    preferred_section_types: Tuple[str, ...]
    target_claim_ids: Tuple[str, ...]
    max_results: int
    max_chars: int


def _compact_text(value: Any, max_chars: int = 600) -> str:
    return " ".join(str(value or "").split())[:max_chars]


def _query_terms(value: str) -> List[str]:
    return [
        token.lower()
        for token in re.findall(r"[A-Za-z][A-Za-z0-9_-]{2,}|\d+(?:\.\d+)?", str(value or ""))
        if token.lower() not in _QUERY_STOPWORDS
    ]


def _dedupe_queries(queries: Iterable[str], max_queries: int = 8) -> Tuple[str, ...]:
    results = []
    seen = set()
    for query in queries:
        compact = _compact_text(query, 500)
        terms = _query_terms(compact)
        if not terms:
            continue
        normalized = " ".join(terms)
        if normalized in seen:
            continue
        seen.add(normalized)
        results.append(compact)
        if len(results) >= max_queries:
            break
    return tuple(results)


def build_retrieval_plan(
    role: str,
    state: Mapping[str, Any],
    manager_payload: Optional[Mapping[str, Any]] = None,
    *,
    max_chars: int,
) -> RetrievalPlan:
    role = str(role or "evidence").strip().lower()
    if role not in _ROLE_SECTION_PRIORITIES:
        role = "evidence"
    manager_payload = manager_payload or {}
    target_claim_ids = tuple(str(item) for item in manager_payload.get("target_claim_ids", []) if str(item))
    claims = [item for item in state.get("claims", []) if isinstance(item, dict)]
    if target_claim_ids:
        targeted = [item for item in claims if str(item.get("claim_id") or "") in target_claim_ids]
        if targeted:
            claims = targeted
    queries: List[str] = []
    focus = str(manager_payload.get("focus") or state.get("active_focus") or state.get("last_focus") or "")
    if focus:
        queries.append(focus)
    for claim in claims[:5]:
        queries.append(" ".join(
            part for part in (
                str(claim.get("claim") or ""),
                str(claim.get("evidence_need") or ""),
                " ".join(str(item) for item in claim.get("claim_obligations", []) or []),
            ) if part
        ))
    if role == "evidence":
        for flaw in state.get("flaw_candidates", [])[:4]:
            if isinstance(flaw, dict):
                queries.append(" ".join(str(flaw.get(key) or "") for key in ("description", "required_evidence_type", "criterion")))
        for task in manager_payload.get("targeted_negative_search_active_tasks", []) or []:
            if isinstance(task, dict):
                queries.append(" ".join(str(task.get(key) or "") for key in ("search_question", "target_locator_hint", "expected_quote_cues")))
    elif role == "critique":
        for evidence in state.get("evidence_map", [])[:8]:
            if isinstance(evidence, dict):
                queries.append(" ".join(str(evidence.get(key) or "") for key in ("raw_quote", "source_locator", "required_evidence_type")))
        for gap in state.get("evidence_gaps", [])[:5]:
            if isinstance(gap, dict):
                queries.append(" ".join(str(gap.get(key) or "") for key in ("description", "required_evidence_type", "missing_item")))
    queries.extend(_ROLE_SEED_QUERIES[role])
    return RetrievalPlan(
        role=role,
        queries=_dedupe_queries(queries),
        preferred_section_types=_ROLE_SECTION_PRIORITIES[role],
        target_claim_ids=target_claim_ids,
        max_results=8 if role == "critique" else 7,
        max_chars=max_chars,
    )


def _window_result(result: PaperSearchResult, max_chars: int) -> Tuple[str, int, int]:
    text = str(result.text or "")
    if len(text) <= max_chars:
        return text, result.source_span_start, result.source_span_end
    lowered = text.lower()
    positions = [lowered.find(term.lower()) for term in result.matched_terms if lowered.find(term.lower()) >= 0]
    starts = [0] + [max(0, min(len(text) - max_chars, position - max_chars // 4)) for position in positions]
    best_start = max(
        starts,
        key=lambda start: (
            sum(term.lower() in lowered[start:start + max_chars] for term in result.matched_terms),
            sum(lowered[start:start + max_chars].count(term.lower()) for term in result.matched_terms),
        ),
    )
    window = text[best_start:best_start + max_chars]
    source_start = result.source_span_start + best_start
    return window, source_start, source_start + len(window)


def _result_key(result: PaperSearchResult) -> Tuple[int, int]:
    return result.source_span_start, result.source_span_end


def retrieve_with_plan(index: PaperIndex, plan: RetrievalPlan) -> List[Dict[str, Any]]:
    candidates: Dict[Tuple[int, int], Dict[str, Any]] = {}
    for query_index, query in enumerate(plan.queries):
        results = index.search(query, top_k=8)
        for result in results:
            key = _result_key(result)
            current = candidates.get(key)
            if current is not None and float(current["score"]) >= float(result.score):
                continue
            window_chars = {"claim": 700, "evidence": 680, "critique": 560}[plan.role]
            window, start, end = _window_result(result, window_chars)
            candidates[key] = {
                "retrieval_id": "",
                "query_id": f"query-{query_index + 1:02d}",
                "query": query,
                "result_id": result.result_id,
                "result_type": result.result_type,
                "section_type": result.section_type,
                "heading": result.heading,
                "text": window,
                "source_span_start": start,
                "source_span_end": end,
                "matched_terms": list(result.matched_terms),
                "score": round(float(result.score), 6),
                "parser_mode": result.parser_mode,
            }
    selected: List[Dict[str, Any]] = []
    selected_keys = set()
    for section_type in plan.preferred_section_types:
        matching = [
            (key, item) for key, item in candidates.items()
            if item["section_type"] == section_type and key not in selected_keys
        ]
        if not matching:
            continue
        key, item = max(matching, key=lambda pair: (float(pair[1]["score"]), -int(pair[1]["source_span_start"])))
        selected.append(item)
        selected_keys.add(key)
        if len(selected) >= plan.max_results:
            break
    remaining = sorted(
        ((key, item) for key, item in candidates.items() if key not in selected_keys),
        key=lambda pair: (
            1 if pair[1]["section_type"] in {"preamble", "other", "chunk"} else 0,
            -float(pair[1]["score"]),
            int(pair[1]["source_span_start"]),
        ),
    )
    for key, item in remaining:
        selected.append(item)
        selected_keys.add(key)
        if len(selected) >= plan.max_results:
            break
    for section_type in plan.preferred_section_types:
        section = next((item for item in index.sections if item.section_type == section_type), None)
        if section is None or (section.source_span_start, section.source_span_end) in selected_keys:
            continue
        fallback_chars = {"claim": 700, "evidence": 680, "critique": 560}[plan.role]
        text = section.text[:fallback_chars]
        selected.append({
            "retrieval_id": "",
            "query_id": "role-priority-fallback",
            "query": section_type,
            "result_id": section.section_id,
            "result_type": "section",
            "section_type": section.section_type,
            "heading": section.heading,
            "text": text,
            "source_span_start": section.source_span_start,
            "source_span_end": section.source_span_start + len(text),
            "matched_terms": [],
            "score": 0.0,
            "parser_mode": section.parser_mode,
        })
        selected_keys.add((section.source_span_start, section.source_span_end))
        if len(selected) >= plan.max_results:
            break
    for index_no, item in enumerate(selected, start=1):
        item["retrieval_id"] = f"retrieval-{index_no:02d}"
    return selected


def render_retrieval_context(
    paper_text: str,
    role: str,
    state: Mapping[str, Any],
    manager_payload: Optional[Mapping[str, Any]],
    *,
    max_chars: int,
) -> Tuple[str, Dict[str, Any]]:
    index = build_paper_index(paper_text)
    plan = build_retrieval_plan(role, state, manager_payload, max_chars=max_chars)
    results = retrieve_with_plan(index, plan)
    parts = []
    included = []
    remaining = max_chars
    for result in results:
        label = (
            f"[{result['retrieval_id']} section={result['section_type']} id={result['result_id']} "
            f"span={result['source_span_start']}:{result['source_span_end']} query={result['query_id']}] "
        )
        budget = min(len(result["text"]), max(0, remaining - len(label) - 2))
        if budget < 40:
            break
        text = result["text"][:budget]
        parts.append(label + text)
        included.append({**result, "text": text, "source_span_end": result["source_span_start"] + len(text)})
        remaining -= len(label) + len(text) + 2
    context = "\n\n".join(parts).strip()
    roundtrip_ok = all(
        paper_text[item["source_span_start"]:item["source_span_end"]] == item["text"]
        for item in included
    )
    meta = {
        "paper_index_retrieval_role": plan.role,
        "paper_index_retrieval_queries": list(plan.queries),
        "paper_index_retrieval_query_count": len(plan.queries),
        "paper_index_retrieval_result_count": len(included),
        "paper_index_retrieval_section_types": list(dict.fromkeys(item["section_type"] for item in included)),
        "paper_index_retrieval_results": included,
        "paper_index_retrieval_roundtrip_ok": roundtrip_ok,
        "paper_index_retrieval_chars": len(context),
        "paper_index_summary": index.audit_summary(),
    }
    return context or "No paper text available.", meta
