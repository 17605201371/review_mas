from __future__ import annotations

import copy
import json
import re
import os
from collections import Counter
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from agent_system.environments.env_package.review.recovery_patch import (
    looks_like_recovery_payload,
    parse_recovery_payload,
)
from agent_system.environments.env_package.review.recovery_validator import validate_recovery_patch, RECOVERY_STATUS_TRANSITIONS


REVIEW_MODES = {"s1", "s2", "s3", "s4"}
FINAL_DECISIONS = {"accept", "reject", "undecided"}
TURN_DECISIONS = {"continue", "finalize"}
CLAIM_IMPORTANCE = {"high", "medium", "low"}
CLAIM_STATUS = {"new", "uncertain", "supported", "partially_supported", "unsupported", "superseded"}
CLAIM_TYPES = {"contribution", "method", "empirical", "limitation_or_boundary", "comparison", "other"}
CLAIM_COVERAGE_TAGS = {"contribution", "method", "empirical", "limitation", "scope", "comparison"}
CLAIM_KINDS = {
    "paper_extracted",
    "context_synthesized",
    "manager_fallback",
    "recovery_marker",
    "unknown",
}
EVIDENCE_STRENGTH = {"strong", "medium", "weak", "missing"}
EVIDENCE_STANCE = {"supports", "partially_supports", "contradicts", "missing"}
EVIDENCE_GAP_STATUSES = {"open", "resolved", "closed", "superseded", "converted", "not_assessable"}
GROUNDING_JUDGE_LABELS = {"unjudged", "self_claimed_by_agent", "paper_grounded", "not_paper_grounded", "unclear"}
VERIFIED_GROUNDING_LABELS = {"unjudged", "paper_grounded_exact", "paper_grounded_normalized", "not_verified_paraphrase_only", "missing_quote"}
VERIFIED_PAPER_GROUNDED_LABELS = {"paper_grounded_exact", "paper_grounded_normalized"}
SEMANTIC_GROUNDING_LABELS = {
    "semantic_unjudged",
    "semantic_support_verified",
    "semantic_negative_verified",
    "semantic_support_weak",
    "semantic_negative_weak",
    "semantic_mismatch",
    "semantic_unverified_quote",
}
FLAW_SEVERITY = {"critical", "major", "minor"}
FLAW_STATUS = {"candidate", "confirmed", "downgraded", "retracted"}
QUESTION_STATUS = {"open", "resolved", "deferred"}
MANAGER_ACTION_TYPES = {"extract_claims", "verify_evidence", "analyze_flaws", "request_evidence_recheck", "challenge_previous_hypothesis", "summarize_progress", "ask_user_clarification", "finalize"}
RECOVERY_ACTION_TYPES = {"challenge_previous_hypothesis", "request_evidence_recheck"}
RECOVERY_PATCH_ACTION_TYPES = {"challenge_previous_hypothesis"}
TURN_MODES = {"normal_evidence", "recovery_patch"}
REVIEW_PHASES = {"normal_review", "recovery"}
PROTECTED_POTENTIAL_CONCERN_TERMINAL_REASON = "verified_actionable_negative_concern_preserved"

ENABLE_EVIDENCE_ID_COLLISION_PRESERVATION = False

CLAIM_STATUS_TRANSITIONS = {
    "new": {"new", "uncertain", "partially_supported", "supported", "unsupported", "superseded"},
    "uncertain": {"uncertain", "partially_supported", "supported", "unsupported", "superseded"},
    "supported": {"supported", "partially_supported", "uncertain", "unsupported", "superseded"},
    "partially_supported": {"partially_supported", "supported", "uncertain", "unsupported", "superseded"},
    "unsupported": {"unsupported", "uncertain", "partially_supported", "superseded"},
    "superseded": {"superseded", "uncertain"},
}
FLAW_STATUS_TRANSITIONS = {
    "candidate": {"candidate", "confirmed", "downgraded", "retracted"},
    "confirmed": {"confirmed", "downgraded", "retracted"},
    "downgraded": {"downgraded", "confirmed", "retracted"},
    "retracted": {"retracted", "downgraded", "candidate"},
}
QUESTION_STATUS_TRANSITIONS = {
    "open": {"open", "resolved", "deferred"},
    "resolved": {"resolved", "open"},
    "deferred": {"deferred", "open", "resolved"},
}


def _normalize_text(value: Any, default: str = "", max_length: int = 2000) -> str:
    if value is None:
        return default
    text = re.sub(r"\s+", " ", str(value)).strip()
    if not text:
        return default
    return text[:max_length]


def _normalize_paper_text(value: Any, default: str = "", max_length: int = 32000) -> str:
    if value is None:
        return default
    text = str(value).replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t\f\v]+", " ", text)
    text = re.sub(r"\n[ \t]+", "\n", text)
    text = re.sub(r"\n{4,}", "\n\n\n", text)
    text = text.strip()
    if not text:
        return default
    return text[:max_length]


def _normalize_conflict_note_text(value: Any, max_length: int = 140) -> str:
    text = str(value or "")
    text = text.replace("<think>", " ").replace("</think>", " ")
    text = text.replace("<json>", " ").replace("</json>", " ")
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return ""
    if len(text) <= max_length:
        return text
    return text[: max(0, max_length - 3)].rstrip() + "..."


    if value is None:
        return default
    text = re.sub(r"\s+", " ", str(value)).strip()
    if not text:
        return default
    return text[:max_length]


def _normalize_list_of_strings(value: Any, max_items: int = 8, max_length: int = 300) -> List[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        value = [value]
    seen = set()
    results: List[str] = []
    for item in value:
        text = _normalize_text(item, max_length=max_length)
        if not text:
            continue
        key = text.lower()
        if key in seen:
            continue
        seen.add(key)
        results.append(text)
        if len(results) >= max_items:
            break
    return results


def _normalize_choice(value: Any, allowed: Iterable[str], default: str) -> str:
    allowed_set = set(allowed)
    text = _normalize_text(value, default=default, max_length=64).lower()
    return text if text in allowed_set else default


# P0-5: synthetic recovery markers and parser fallback evidence are
# diagnostic placeholders generated when no real paper-grounded evidence could
# be found. They must never be cited as ``supporting_evidence_ids`` for a claim
# or recovery patch. The downstream `recovery_validator` rejects these patches,
# and this helper also keeps turn logs/dashboard inputs clean.
_SYNTHETIC_RECOVERY_MARKER_PREFIXES = (
    "evidence-recovery-missing",
    "evidence-context-",
    "evidence-fallback-",
    "evidence-placeholder-",
    "evidence-synthetic-",
)


def _is_synthetic_recovery_marker_evidence_id(evidence_id: Any) -> bool:
    text = str(evidence_id or "").strip().lower()
    if not text:
        return False
    return any(text.startswith(prefix) for prefix in _SYNTHETIC_RECOVERY_MARKER_PREFIXES)


def _strip_synthetic_recovery_markers(values: Any) -> List[str]:
    """Return a copy of ``values`` with synthetic recovery markers removed.

    ``values`` may be ``None``, a single id, or a list.  The result preserves
    order and skips empty entries.  This is the single source of truth used
    at every site that writes ``supporting_evidence_ids`` so reviewers and
    downstream validators see a consistent view.
    """
    if values is None:
        return []
    if isinstance(values, (str, bytes)):
        items = [values]
    elif isinstance(values, list):
        items = list(values)
    else:
        items = [values]
    cleaned: List[str] = []
    for item in items:
        text = str(item or "").strip()
        if not text:
            continue
        if _is_synthetic_recovery_marker_evidence_id(text):
            continue
        cleaned.append(text)
    return cleaned


def _infer_gap_entity_ids(text: str) -> Dict[str, str]:
    result = {"claim_id": "", "flaw_id": ""}
    claim_match = re.search(r"\bClaim\s+([A-Za-z0-9_.:-]+)", text or "", re.IGNORECASE)
    if claim_match:
        result["claim_id"] = claim_match.group(1)
    flaw_match = re.search(r"\bFlaw\s+([A-Za-z0-9_.:-]+)", text or "", re.IGNORECASE)
    if flaw_match:
        result["flaw_id"] = flaw_match.group(1)
    return result


def _evidence_gap_text(item: Any) -> str:
    if isinstance(item, dict):
        return _normalize_text(
            item.get("gap") or item.get("text") or item.get("description") or item.get("evidence_gap"),
            max_length=240,
        )
    return _normalize_text(item, max_length=240)


def _normalize_evidence_gap_item(item: Any, fallback_index: int) -> Optional[Dict[str, Any]]:
    text = _evidence_gap_text(item)
    if not text:
        return None
    inferred = _infer_gap_entity_ids(text)
    if isinstance(item, dict):
        related_claim_ids = item.get("related_claim_ids") or []
        if not isinstance(related_claim_ids, list):
            related_claim_ids = [related_claim_ids]
        claim_id = _normalize_text(item.get("claim_id") or (related_claim_ids[0] if related_claim_ids else "") or inferred["claim_id"], max_length=80)
        evidence_id = _normalize_text(item.get("evidence_id"), max_length=80)
        flaw_id = _normalize_text(item.get("flaw_id") or inferred["flaw_id"], max_length=80)
        status = _normalize_choice(item.get("status"), EVIDENCE_GAP_STATUSES, "open")
        source = _normalize_text(item.get("source"), default="worker_reported", max_length=80)
        resolution = _normalize_text(item.get("resolution"), max_length=160)
        gap_id = _normalize_text(item.get("gap_id"), max_length=80)
    else:
        claim_id = inferred["claim_id"]
        evidence_id = ""
        flaw_id = inferred["flaw_id"]
        status = "open"
        source = "legacy_string"
        resolution = ""
        gap_id = ""
    if not gap_id:
        gap_id = _slugify("gap", f"{claim_id or flaw_id}:{text}", fallback_index)
    return {
        "gap_id": gap_id,
        "gap": text,
        "status": status,
        "claim_id": claim_id,
        "evidence_id": evidence_id,
        "flaw_id": flaw_id,
        "source": source,
        "resolution": resolution,
    }


def _normalize_evidence_gaps(value: Any, max_items: int = 10) -> List[Dict[str, Any]]:
    if value is None:
        return []
    if not isinstance(value, list):
        value = [value]
    results: List[Dict[str, Any]] = []
    seen: set[str] = set()
    for idx, item in enumerate(value, start=1):
        normalized = _normalize_evidence_gap_item(item, idx)
        if normalized is None:
            continue
        key = _evidence_gap_key(normalized)
        if key in seen:
            continue
        seen.add(key)
        results.append(normalized)
        if len(results) >= max_items:
            break
    return results


def _evidence_gap_key(item: Dict[str, Any]) -> str:
    claim_id = str(item.get("claim_id") or "")
    flaw_id = str(item.get("flaw_id") or "")
    text = str(item.get("gap") or "").lower()
    return f"{claim_id}|{flaw_id}|{text}"


def _merge_evidence_gaps(existing: Any, incoming: Any, max_items: int = 10) -> List[Dict[str, Any]]:
    merged: Dict[str, Dict[str, Any]] = {}
    for gap in _normalize_evidence_gaps(existing, max_items=max_items * 2) + _normalize_evidence_gaps(incoming, max_items=max_items * 2):
        key = _evidence_gap_key(gap)
        old = merged.get(key)
        if old is None:
            merged[key] = gap
            continue
        if old.get("status") != "open" and gap.get("status") == "open":
            continue
        updated = dict(old)
        updated.update({field: value for field, value in gap.items() if value or field == "status"})
        merged[key] = updated
    return list(merged.values())[:max_items]


def _set_evidence_gap_status(
    gaps: Any,
    *,
    claim_id: str = "",
    flaw_id: str = "",
    status: str,
    evidence_id: str = "",
    resolution: str = "",
) -> List[Dict[str, Any]]:
    normalized = _normalize_evidence_gaps(gaps, max_items=20)
    resolved_status = _normalize_choice(status, EVIDENCE_GAP_STATUSES, "resolved")
    for gap in normalized:
        gap_claim_id = str(gap.get("claim_id") or "")
        gap_flaw_id = str(gap.get("flaw_id") or "")
        text = str(gap.get("gap") or "")
        claim_matches = bool(claim_id and (gap_claim_id == claim_id or claim_id in text))
        flaw_matches = bool(flaw_id and (gap_flaw_id == flaw_id or flaw_id in text))
        if not claim_matches and not flaw_matches:
            continue
        current_gap_status = str(gap.get("status") or "open")
        can_resolve_assessment_limitation = (
            resolved_status == "resolved"
            and current_gap_status == "not_assessable"
            and bool(evidence_id)
        )
        if current_gap_status == "open" or can_resolve_assessment_limitation:
            gap["status"] = resolved_status
            if evidence_id:
                gap["evidence_id"] = evidence_id
            if resolution:
                gap["resolution"] = resolution
    return normalized[:10]


def _open_evidence_gaps(value: Any) -> List[Dict[str, Any]]:
    gaps = value.get("evidence_gaps", []) if isinstance(value, dict) else value
    return [gap for gap in _normalize_evidence_gaps(gaps, max_items=20) if gap.get("status") == "open"]


_CLAIM_EMPIRICAL_PATTERN = re.compile(
    r"\b(experiment|experiments|evaluation|evaluations|result|results|benchmark|baseline|dataset|datasets|metric|metrics|table|figure|fig\.?|ablation|outperform|performance|accuracy|f1|auc|rouge|bleu)\b",
    re.IGNORECASE,
)
_CLAIM_METHOD_PATTERN = re.compile(
    r"\b(method|methods|methodology|approach|model|framework|algorithm|architecture|training|objective|optimization|module|mechanism)\b",
    re.IGNORECASE,
)
_CLAIM_LIMITATION_PATTERN = re.compile(
    r"\b(limitation|limitations|fail|fails|failure|weakness|challenge|risk|sensitive|sensitivity|robustness|generalization|scope|assumption|constraint|trade[- ]?off|only|limited)\b",
    re.IGNORECASE,
)
_CLAIM_COMPARISON_PATTERN = re.compile(
    r"\b(compare|compared|comparison|baseline|state-of-the-art|sota|outperform|surpass|better than|against)\b",
    re.IGNORECASE,
)
_CLAIM_CONTRIBUTION_PATTERN = re.compile(
    r"\b(propose|proposes|present|presents|introduce|introduces|contribution|novel|new|first|paper)\b",
    re.IGNORECASE,
)


def _normalize_claim_coverage_tags(item: Dict[str, Any], claim_text: str, claim_type: str) -> List[str]:
    raw_tags = _normalize_list_of_strings(
        item.get("coverage_tags") or item.get("claim_tags") or item.get("claim_coverage_tags"),
        max_items=6,
        max_length=40,
    )
    tags = [tag.lower() for tag in raw_tags if tag.lower() in CLAIM_COVERAGE_TAGS]
    combined_text = " ".join(
        str(value or "")
        for value in (
            claim_text,
            item.get("evidence_need"),
            item.get("rationale"),
            item.get("source"),
        )
    )
    if claim_type == "method" or _CLAIM_METHOD_PATTERN.search(combined_text):
        tags.append("method")
    if claim_type == "empirical" or _CLAIM_EMPIRICAL_PATTERN.search(combined_text):
        tags.append("empirical")
    if claim_type == "limitation_or_boundary" or _CLAIM_LIMITATION_PATTERN.search(combined_text):
        tags.append("limitation")
    if claim_type == "comparison" or _CLAIM_COMPARISON_PATTERN.search(combined_text):
        tags.append("comparison")
    if "scope" in combined_text.lower() or "boundary" in combined_text.lower():
        tags.append("scope")
    if claim_type == "contribution" or _CLAIM_CONTRIBUTION_PATTERN.search(combined_text):
        tags.append("contribution")
    return list(dict.fromkeys(tags))[:6]


def _infer_claim_type(item: Dict[str, Any], claim_text: str) -> str:
    explicit_type = _normalize_text(item.get("claim_type") or item.get("type"), max_length=64).lower()
    if explicit_type in CLAIM_TYPES:
        return explicit_type
    if explicit_type in {"limitation", "boundary", "scope"}:
        return "limitation_or_boundary"
    combined_text = " ".join(
        str(value or "")
        for value in (
            claim_text,
            item.get("evidence_need"),
            item.get("rationale"),
            item.get("source"),
        )
    )
    if _CLAIM_LIMITATION_PATTERN.search(combined_text):
        return "limitation_or_boundary"
    if _CLAIM_EMPIRICAL_PATTERN.search(combined_text):
        return "empirical"
    if _CLAIM_METHOD_PATTERN.search(combined_text):
        return "method"
    if _CLAIM_COMPARISON_PATTERN.search(combined_text):
        return "comparison"
    if _CLAIM_CONTRIBUTION_PATTERN.search(combined_text):
        return "contribution"
    return "other"


def _default_claim_evidence_need(claim_type: str, coverage_tags: Sequence[str]) -> str:
    tags = set(coverage_tags or [])
    if claim_type == "empirical" or "empirical" in tags:
        return "result/experiment/table evidence"
    if claim_type == "method" or "method" in tags:
        return "method/algorithm evidence"
    if claim_type == "limitation_or_boundary" or "limitation" in tags or "scope" in tags:
        return "scope, limitation, or failure-mode evidence"
    if claim_type == "comparison" or "comparison" in tags:
        return "baseline/comparison evidence"
    return "paper evidence"


def _normalize_float(value: Any, default: float = 0.5, min_value: float = 0.0, max_value: float = 1.0) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = default
    return max(min_value, min(max_value, number))


def _normalize_int(value: Any, default: int = -1, min_value: int = -1, max_value: int = 10_000_000) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        number = default
    return max(min_value, min(max_value, number))


def _slugify(prefix: str, seed: str, fallback_index: int) -> str:
    digest = re.sub(r"[^a-z0-9]+", "-", seed.lower()).strip("-")[:32]
    if not digest:
        digest = f"{prefix}-{fallback_index}"
    return f"{prefix}-{digest}"


def _normalize_question_item(item: Any, fallback_index: int) -> Optional[Dict[str, Any]]:
    if isinstance(item, dict):
        question_text = _normalize_text(item.get("question") or item.get("text"), max_length=300)
        if not question_text:
            return None
        question_id = _normalize_text(item.get("question_id"), max_length=80) or _slugify("question", question_text, fallback_index)
        return {
            "question_id": question_id,
            "question": question_text,
            "status": _normalize_choice(item.get("status"), QUESTION_STATUS, "open"),
            "related_claim_ids": _normalize_list_of_strings(item.get("related_claim_ids"), max_items=6, max_length=80),
        }

    question_text = _normalize_text(item, max_length=300)
    if not question_text:
        return None
    return {
        "question_id": _slugify("question", question_text, fallback_index),
        "question": question_text,
        "status": "open",
        "related_claim_ids": [],
    }


def _normalize_conflict_item(item: Any, fallback_index: int) -> Optional[Dict[str, Any]]:
    if isinstance(item, dict):
        note = _normalize_conflict_note_text(item.get("note") or item.get("description") or item.get("text"), max_length=140)
        if not note:
            return None
        conflict_id = _normalize_text(item.get("conflict_id"), max_length=80) or _slugify("conflict", note, fallback_index)
        return {
            "conflict_id": conflict_id,
            "note": note,
            "claim_id": _normalize_text(item.get("claim_id"), max_length=80),
            "evidence_id": _normalize_text(item.get("evidence_id"), max_length=80),
            "flaw_id": _normalize_text(item.get("flaw_id"), max_length=80),
            "conflict_type": _normalize_text(item.get("conflict_type"), default="state_conflict", max_length=80),
        }

    note = _normalize_conflict_note_text(item, max_length=140)
    if not note:
        return None
    return {
        "conflict_id": _slugify("conflict", note, fallback_index),
        "note": note,
        "claim_id": "",
        "evidence_id": "",
        "flaw_id": "",
        "conflict_type": "state_conflict",
    }


def _classify_claim_kind(claim_id: Any, declared_kind: Any = "") -> str:
    value = str(claim_id or "").strip().lower()
    if value.startswith("claim-fallback") or value.startswith("fallback"):
        return "manager_fallback"
    if value.startswith("claim-context") or value.startswith("context"):
        return "context_synthesized"
    if value.startswith("claim-recovery") or value.startswith("recovery"):
        return "recovery_marker"
    declared = str(declared_kind or "").strip().lower()
    if declared in CLAIM_KINDS:
        return declared
    if not value:
        return "unknown"
    if value.startswith("claim-"):
        return "paper_extracted"
    return "unknown"


def _normalize_claim_item(item: Any, fallback_index: int) -> Optional[Dict[str, Any]]:
    if not isinstance(item, dict):
        return None
    claim_text = _normalize_text(item.get("claim") or item.get("text"), max_length=500)
    if not claim_text:
        return None
    claim_id = _normalize_text(item.get("claim_id"), max_length=80) or _slugify("claim", claim_text, fallback_index)
    claim_type = _infer_claim_type(item, claim_text)
    coverage_tags = _normalize_claim_coverage_tags(item, claim_text, claim_type)
    claim_kind = _classify_claim_kind(claim_id, item.get("claim_kind"))
    normalized = {
        "claim_id": claim_id,
        "claim": claim_text,
        "importance": _normalize_choice(item.get("importance"), CLAIM_IMPORTANCE, "medium"),
        "status": _normalize_choice(item.get("status"), CLAIM_STATUS, "uncertain"),
        "claim_type": claim_type,
        "claim_kind": claim_kind,
        "evidence_need": _normalize_text(
            item.get("evidence_need") or item.get("verification_need"),
            default=_default_claim_evidence_need(claim_type, coverage_tags),
            max_length=160,
        ),
        "coverage_tags": coverage_tags,
        "supporting_evidence_ids": _strip_synthetic_recovery_markers(
            _normalize_list_of_strings(item.get("supporting_evidence_ids"), max_items=6, max_length=80)
        ),
    }
    for field in ("claim_origin", "claim_origin_kind", "claim_source", "claim_extraction_source"):
        value = _normalize_text(item.get(field), max_length=120)
        if value:
            normalized[field] = value
    return normalized


def _evidence_source_bucket(item: Dict[str, Any]) -> str:
    """Return the decision-layer source bucket for an evidence item.

    Delegates to :func:`support_quality.evidence_section_bucket` so the entire
    pipeline (normalisation, hygiene view, recommendation view) shares a single
    classifier instead of maintaining drifting keyword lists.
    """
    from .support_quality import evidence_section_bucket

    section = evidence_section_bucket(item)
    return _SECTION_TO_DECISION_BUCKET.get(section, "other_or_unspecified")


def _support_quality_label(item: Dict[str, Any]) -> str:
    bucket = str(item.get("support_source_bucket") or _evidence_source_bucket(item))
    if bucket == "abstract":
        return "abstract_claim_support"
    if bucket in _EMPIRICAL_DECISION_BUCKETS:
        return "empirical_or_ablation_support"
    if bucket in _METHOD_DECISION_BUCKETS:
        return "method_grounded_support"
    if bucket == "conclusion_or_discussion":
        return "summary_level_support"
    return "unspecified_support"


def _normalize_evidence_item(item: Any, fallback_index: int) -> Optional[Dict[str, Any]]:
    if not isinstance(item, dict):
        return None
    evidence_text = _normalize_text(item.get("evidence") or item.get("text"), max_length=600)
    if not evidence_text:
        return None
    evidence_id = _normalize_text(item.get("evidence_id"), max_length=80) or _slugify("evidence", evidence_text, fallback_index)
    claim_id = _normalize_text(item.get("claim_id"), max_length=80)
    source = _normalize_text(item.get("source"), default="paper", max_length=120)
    source_locator = _normalize_text(item.get("source_locator") or source, max_length=160)
    raw_quote = _normalize_text(item.get("raw_quote") or item.get("quote"), max_length=240)
    quote_id = _normalize_text(item.get("quote_id") or item.get("source_quote_id"), max_length=80)
    grounded_judge_label = _normalize_choice(
        item.get("grounded_judge_label"), GROUNDING_JUDGE_LABELS, "self_claimed_by_agent"
    )
    normalized = {
        "evidence_id": evidence_id,
        "claim_id": claim_id,
        "evidence": evidence_text,
        "source": source,
        "source_locator": source_locator,
        "raw_quote": raw_quote,
        "quote_id": quote_id,
        "source_span_start": _normalize_int(item.get("source_span_start") if item.get("source_span_start") is not None else item.get("span_start"), default=-1),
        "source_span_end": _normalize_int(item.get("source_span_end") if item.get("source_span_end") is not None else item.get("span_end"), default=-1),
        "strength": _normalize_choice(item.get("strength"), EVIDENCE_STRENGTH, "medium"),
        "stance": _normalize_choice(item.get("stance"), EVIDENCE_STANCE, "supports"),
        "binding_status": _normalize_text(item.get("binding_status"), default="unchecked", max_length=80),
        "binding_confidence": _normalize_float(item.get("binding_confidence"), default=0.0),
        "binding_rationale": _normalize_text(item.get("binding_rationale"), max_length=240),
        "grounded_judge_label": grounded_judge_label,
        "grounded_judge_reason": _normalize_text(item.get("grounded_judge_reason"), max_length=240),
        "verified_grounding_label": _normalize_choice(
            item.get("verified_grounding_label"), VERIFIED_GROUNDING_LABELS, "unjudged"
        ),
        "verified_grounding_reason": _normalize_text(item.get("verified_grounding_reason"), max_length=240),
        "verified_source_span_start": _normalize_int(item.get("verified_source_span_start"), default=-1),
        "verified_source_span_end": _normalize_int(item.get("verified_source_span_end"), default=-1),
        "verified_quote_match_type": _normalize_text(item.get("verified_quote_match_type"), max_length=80),
        "verified_locator_quality": _normalize_text(item.get("verified_locator_quality"), max_length=80),
        "semantic_grounding_label": _normalize_choice(
            item.get("semantic_grounding_label"), SEMANTIC_GROUNDING_LABELS, "semantic_unjudged"
        ),
        "semantic_grounding_reasons": _normalize_list_of_strings(
            item.get("semantic_grounding_reasons"), max_items=8, max_length=80
        ),
        "semantic_alignment_score": _normalize_float(item.get("semantic_alignment_score"), default=0.0),
        "semantic_grounding_checked": bool(item.get("semantic_grounding_checked")),
        "quote_evidence_semantic_mismatch": bool(item.get("quote_evidence_semantic_mismatch")),
        "verified_claim_overlap_score": _normalize_int(item.get("verified_claim_overlap_score"), default=0, min_value=0),
        "quote_bank_claim_overlap_fallback_used": bool(item.get("quote_bank_claim_overlap_fallback_used")),
        "quote_bank_claim_overlap_fallback_quote_id": _normalize_text(item.get("quote_bank_claim_overlap_fallback_quote_id"), max_length=80),
        "quote_bank_claim_overlap_fallback_source_bucket": _normalize_text(item.get("quote_bank_claim_overlap_fallback_source_bucket"), max_length=80),
        "quote_bank_claim_overlap_fallback_score": _normalize_int(item.get("quote_bank_claim_overlap_fallback_score"), default=0, min_value=0),
        "semantic_weak_promotion_used": bool(item.get("semantic_weak_promotion_used")),
        "semantic_weak_promotion_reason": _normalize_text(item.get("semantic_weak_promotion_reason"), max_length=120),
        "strength_promotion_from_medium_used": bool(item.get("strength_promotion_from_medium_used")),
        "strength_promotion_reason": _normalize_text(item.get("strength_promotion_reason"), max_length=120),
    }
    negative_evidence_type = _normalize_text(item.get("negative_evidence_type"), max_length=80)
    if negative_evidence_type:
        normalized["negative_evidence_type"] = negative_evidence_type
    negative_actionability = _normalize_text(item.get("negative_evidence_actionability"), max_length=80)
    if negative_actionability:
        normalized["negative_evidence_actionability"] = negative_actionability
    verified_source_bucket = _normalize_text(item.get("verified_source_bucket"), max_length=80)
    if verified_source_bucket:
        normalized["verified_source_bucket"] = verified_source_bucket
    if "claim_status_downgrade_allowed" in item:
        normalized["claim_status_downgrade_allowed"] = bool(item.get("claim_status_downgrade_allowed"))
    normalized["support_source_bucket"] = _normalize_text(
        item.get("support_source_bucket") or _evidence_source_bucket(normalized),
        default="other_or_unspecified",
        max_length=80,
    )
    normalized["support_quality"] = _normalize_text(
        item.get("support_quality") or _support_quality_label(normalized),
        default="unspecified_support",
        max_length=80,
    )
    normalized["support_quality_reason"] = _normalize_text(item.get("support_quality_reason"), max_length=240)
    return normalized


def _normalize_quote_with_offsets(text: str) -> Tuple[str, List[int]]:
    chars: List[str] = []
    offsets: List[int] = []
    previous_space = True
    for idx, char in enumerate(str(text or "").lower()):
        if char.isalnum():
            chars.append(char)
            offsets.append(idx)
            previous_space = False
        elif not previous_space:
            chars.append(" ")
            offsets.append(idx)
            previous_space = True
    while chars and chars[0] == " ":
        chars.pop(0)
        offsets.pop(0)
    while chars and chars[-1] == " ":
        chars.pop()
        offsets.pop()
    return "".join(chars), offsets


def _verify_quote_against_reference(raw_quote: str, reference_text: str, reference_start: int = -1) -> Dict[str, Any]:
    quote = _normalize_text(raw_quote, max_length=240)
    reference = str(reference_text or "")
    if not quote:
        return {
            "verified_grounding_label": "missing_quote",
            "verified_quote_match_type": "missing_quote",
            "verified_source_span_start": -1,
            "verified_source_span_end": -1,
            "verified_grounding_reason": "raw_quote is empty; no quote-bank verification possible",
        }

    exact_start = reference.find(quote)
    if exact_start >= 0:
        source_start = exact_start + reference_start if reference_start >= 0 else exact_start
        source_end = source_start + len(quote) - 1
        return {
            "verified_grounding_label": "paper_grounded_exact",
            "verified_quote_match_type": "quote_bank_exact_substring",
            "verified_source_span_start": source_start,
            "verified_source_span_end": source_end,
            "verified_grounding_reason": "raw_quote exactly matches a program-extracted quote-bank item",
        }

    normalized_quote, _ = _normalize_quote_with_offsets(quote)
    normalized_reference, reference_offsets = _normalize_quote_with_offsets(reference)
    normalized_start = normalized_reference.find(normalized_quote) if normalized_quote else -1
    if normalized_start >= 0 and reference_offsets:
        normalized_end = normalized_start + len(normalized_quote) - 1
        local_start = reference_offsets[normalized_start]
        local_end = reference_offsets[min(normalized_end, len(reference_offsets) - 1)]
        source_start = local_start + reference_start if reference_start >= 0 else local_start
        source_end = local_end + reference_start if reference_start >= 0 else local_end
        return {
            "verified_grounding_label": "paper_grounded_normalized",
            "verified_quote_match_type": "quote_bank_normalized_substring",
            "verified_source_span_start": source_start,
            "verified_source_span_end": source_end,
            "verified_grounding_reason": "raw_quote matches a program-extracted quote-bank item after normalization",
        }

    return {
        "verified_grounding_label": "not_verified_paraphrase_only",
        "verified_quote_match_type": "not_found_in_quote_bank",
        "verified_source_span_start": -1,
        "verified_source_span_end": -1,
        "verified_grounding_reason": "raw_quote was not found in the ReviewState quote bank",
    }


_SEMANTIC_STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "from", "into", "using", "used", "paper", "claim",
    "shows", "show", "demonstrates", "demonstrate", "indicates", "indicate", "reports", "report", "based",
    "evidence", "support", "supports", "supported", "method", "model", "result", "results", "table", "figure",
}
_SEMANTIC_TOKEN_RE = re.compile(r"[a-z][a-z0-9_\-]{2,}|\d+(?:\.\d+)?%?", re.IGNORECASE)
_SEMANTIC_NUMBER_RE = re.compile(r"\b\d+(?:\.\d+)?%?\b")
_SEMANTIC_TABLE_RE = re.compile(r"\b(table|figure|fig\.)\s*\d+\b", re.IGNORECASE)
_SEMANTIC_RESULT_TERMS_RE = re.compile(
    r"\b(experiment|experiments|evaluation|evaluations|result|results|benchmark|baseline|dataset|metric|performance|outperform|accuracy|f1|auc|bleu|rouge|ablation|table|figure|fig\.)\b",
    re.IGNORECASE,
)
_SEMANTIC_ABSTRACT_MARKER_RE = re.compile(r"\\end\{abstract\}|\\begin\{abstract\}|\babstract\b", re.IGNORECASE)
_SEMANTIC_NEGATIVE_TERMS_RE = re.compile(
    r"\b(contradict|contradicts|contradicted|refute|refutes|weakens|weaken|undermine|undermines|unsupported|does not support|not supported|(?:do|does|did)\s+not\s+(?:prove|provide|show|report|evaluate|compare|include|establish)|not\s+(?:proven|proved|provided|reported|evaluated|compared|included|established)|lack|lacks|lacked|lacking|absent|insufficient|without|missing|open question|no significant|not significant|worse|underperform|fail|fails|failed|failure|limitation|limitations|threats? to validity|future work|not evaluated|not compared|no ablation|no baseline|missing baseline|no comparison|no evaluation)\b",
    re.IGNORECASE,
)
_GENERIC_LOCATOR_RE = re.compile(
    r"^(?:results?\s*/\s*evaluation\s+excerpt|limitation.*excerpt|"
    r"negative.*excerpt|evaluation\s+excerpt|excerpt\s*#?\s*\d*|"
    r"paper\s+text|unknown|n/?a|none)\s*$",
    re.IGNORECASE,
)
_SPECIFIC_LOCATOR_RE = re.compile(
    r"(?:section\s+\d|section\s*:\s*[a-z][a-z0-9 /_-]{2,}|"
    r"\btable\s+[a-z]?\d|\bfigure\s+[a-z]?\d|\bfig\.\s*[a-z]?\d|"
    r"\b(?:table|figure|fig\.)\s*:\s*[a-z0-9][a-z0-9 /_.:-]{2,}|"
    r"\b(?:table|figure|fig\.)\s+caption\s*:\s*[a-z0-9][a-z0-9 /_.:-]{2,}|"
    r"\balgorithm\s+[a-z]?\d|\b(?:theorem|lemma|proposition|corollary)\s+[a-z]?\d|"
    r"\b(?:algorithm|theorem|lemma|proposition|corollary)\s*:\s*[a-z0-9][a-z0-9 /_.:-]{2,}|"
    r"\bsec\.\s*\d+|\b\d+\.\d+)",
    re.IGNORECASE,
)


def _semantic_tokens(text: str) -> set[str]:
    tokens = set()
    for token in _SEMANTIC_TOKEN_RE.findall(str(text or "").lower()):
        clean = token.strip("-_")
        if len(clean) < 3 or clean in _SEMANTIC_STOPWORDS:
            continue
        tokens.add(clean)
    return tokens


def _semantic_numeric_anchors(text: str) -> set[str]:
    numbers = set()
    value_text = str(text or "")
    for match in _SEMANTIC_NUMBER_RE.finditer(value_text):
        raw = match.group(0)
        prefix = value_text[max(0, match.start() - 24):match.start()].lower()
        value = raw.rstrip("%")
        try:
            numeric = float(value)
        except ValueError:
            continue
        # Years and table/figure ordinals are weak semantic anchors; table/figure ids
        # are checked separately so they do not overconstrain broad claims.
        if 1900 <= numeric <= 2099:
            continue
        if re.search(r"(?:section|sec\.|subsection)\s*$", prefix):
            continue
        if numeric < 10 and "." not in value and not raw.endswith("%"):
            continue
        numbers.add(raw.lower())
    return numbers


def _semantic_table_anchors(text: str) -> set[str]:
    anchors = set()
    for match in _SEMANTIC_TABLE_RE.finditer(str(text or "")):
        kind = match.group(1).lower().replace("fig.", "figure")
        number = re.search(r"\d+", match.group(0))
        if number:
            anchors.add(f"{kind} {number.group(0)}")
    return anchors


def _claim_text_for_evidence(state: Dict[str, Any], claim_id: str) -> str:
    for claim in state.get("claims", []) or []:
        if isinstance(claim, dict) and str(claim.get("claim_id") or "") == claim_id:
            return str(claim.get("claim") or claim.get("text") or "")
    return ""


def _quote_bank_entries_for_grounding(state: Dict[str, Any]) -> List[Dict[str, Any]]:
    entries: List[Dict[str, Any]] = []
    latest_meta = (state or {}).get("_latest_evidence_context_meta") or {}
    for source in (
        latest_meta.get("evidence_quote_bank", []) if isinstance(latest_meta, dict) else [],
        (state or {}).get("evidence_quote_bank", []),
    ):
        for entry in source or []:
            if isinstance(entry, dict):
                entries.append(entry)
    deduped: List[Dict[str, Any]] = []
    seen: set[str] = set()
    for entry in entries:
        quote_id = str(entry.get("quote_id") or "")
        raw_quote = str(entry.get("raw_quote") or "")
        key = f"id:{quote_id}" if quote_id else f"raw:{_quote_bank_dedupe_key(raw_quote)}"
        if key in seen:
            continue
        seen.add(key)
        deduped.append(entry)
    return deduped


def _apply_quote_bank_entry_metadata(item: Dict[str, Any], entry: Dict[str, Any], *, canonicalize_quote: bool = False, overwrite_locator: bool = False) -> None:
    quote_id = str(entry.get("quote_id") or "")
    if quote_id:
        item["quote_id"] = quote_id
    canonical_quote = str(entry.get("raw_quote") or "")
    if canonicalize_quote and canonical_quote:
        agent_raw_quote = str(item.get("raw_quote") or "")
        if agent_raw_quote and agent_raw_quote != canonical_quote:
            item["agent_raw_quote"] = agent_raw_quote
            item["quote_bank_canonicalized"] = True
        item["raw_quote"] = canonical_quote
    locator = str(entry.get("source_locator") or "")
    if locator and (overwrite_locator or not item.get("source_locator") or item.get("source_locator") == item.get("source")):
        item["source_locator"] = locator
    span_start = _normalize_int(entry.get("source_span_start"), default=-1)
    span_end = _normalize_int(entry.get("source_span_end"), default=-1)
    if span_start >= 0:
        item["source_span_start"] = span_start
    if span_end >= 0:
        item["source_span_end"] = span_end
    overlap_score = _normalize_int(entry.get("claim_overlap_score"), default=0, min_value=0)
    if overlap_score > 0:
        item["verified_claim_overlap_score"] = overlap_score
    # P0-4 (diagnostic-only): propagate the 5-class negative_evidence_type label
    # from the quote-bank entry to the evidence item so offline audits can read
    # it without re-classifying. No flow effect.
    neg_type = str(entry.get("negative_evidence_type") or "").strip()
    if neg_type:
        item["negative_evidence_type"] = neg_type
    bucket = str(entry.get("source_bucket") or "")
    if not bucket:
        return
    item["verified_source_bucket"] = bucket
    if bucket == "table_or_figure":
        item["support_source_bucket"] = "table_or_figure"
    elif bucket == "ablation":
        item["support_source_bucket"] = "ablation"
    elif bucket == "comparison":
        item["support_source_bucket"] = "result_or_experiment"
    elif bucket == "results":
        item["support_source_bucket"] = "result_or_experiment"
    elif bucket == "method":
        item["support_source_bucket"] = "method_or_approach"
    elif bucket == "theory_or_proof":
        item["support_source_bucket"] = "method_or_approach"
    elif bucket == "abstract":
        item["support_source_bucket"] = "abstract"
    elif bucket == "negative_or_gap":
        item["support_source_bucket"] = "limitation_or_gap"
    elif bucket == "conclusion":
        item["support_source_bucket"] = "conclusion_or_discussion"
    elif bucket == "claim_match" and not item.get("support_source_bucket"):
        item["support_source_bucket"] = _evidence_source_bucket(item)
    if not item.get("support_role"):
        role_hint = str(entry.get("support_role_hint") or "").strip()
        if role_hint:
            item["support_role"] = role_hint


def _verified_claim_overlap_score(evidence: Dict[str, Any]) -> int:
    return _normalize_int(evidence.get("verified_claim_overlap_score"), default=0, min_value=0)


def _has_verified_claim_overlap_support(evidence: Dict[str, Any], *, min_score: int = 1) -> bool:
    if _verified_claim_overlap_score(evidence) < min_score:
        return False
    source_bucket = str(evidence.get("support_source_bucket") or evidence.get("verified_source_bucket") or "")
    if source_bucket in {"abstract", "negative_or_gap", "limitation_or_gap"}:
        return False
    return True


def _select_claim_overlap_quote_bank_entry(
    state: Dict[str, Any],
    item: Dict[str, Any],
    quote_bank: Sequence[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    if str(item.get("stance") or "") not in {"supports", "partially_supports"}:
        return None
    if _evidence_has_negative_intent(item):
        return None
    binding_status = str(item.get("binding_status") or "").strip()
    if binding_status not in {"", "unchecked", "bound_real_claim"}:
        return None
    claim_id = str(item.get("claim_id") or "")
    if not claim_id or claim_id not in _real_claim_ids_from_state(state or {}):
        return None
    claim_text = _claim_text_for_evidence(state or {}, claim_id)
    evidence_text = str(item.get("evidence") or "")
    candidates: List[Tuple[int, float, int, int, Dict[str, Any]]] = []
    source_priority = {"table_or_figure": 6, "results": 5, "theory_or_proof": 4, "claim_match": 3, "method": 2, "conclusion": 1}
    for index, entry in enumerate(quote_bank):
        bucket = str(entry.get("source_bucket") or "")
        if bucket in {"abstract", "negative_or_gap"}:
            continue
        quote = str(entry.get("raw_quote") or "").strip()
        if len(_quote_bank_dedupe_key(quote)) < 40:
            continue
        if _SEMANTIC_NEGATIVE_TERMS_RE.search(quote):
            continue
        overlap = _normalize_int(entry.get("claim_overlap_score"), default=0, min_value=0)
        if overlap <= 0:
            continue
        claim_score = _semantic_alignment_score(claim_text, quote)
        evidence_score = _semantic_alignment_score(evidence_text, quote)
        score = max(claim_score, evidence_score)
        if score < 0.08:
            continue
        if overlap < 2 and score < 0.14:
            continue
        candidates.append((overlap, score, source_priority.get(bucket, 0), -index, entry))
    if not candidates:
        return None
    return max(candidates, key=lambda candidate: candidate[:4])[-1]


def _semantic_alignment_score(source_text: str, quote: str) -> float:
    source_tokens = _semantic_tokens(source_text)
    quote_tokens = _semantic_tokens(quote)
    if not source_tokens or not quote_tokens:
        return 0.0
    denominator = max(1, min(len(source_tokens), len(quote_tokens), 24))
    return min(1.0, len(source_tokens & quote_tokens) / denominator)


def _evidence_has_negative_intent(evidence: Dict[str, Any]) -> bool:
    stance = str(evidence.get("stance") or "").strip().lower()
    strength = str(evidence.get("strength") or "").strip().lower()
    return (
        stance in {"contradicts", "contradict", "refutes", "refute", "weakens", "weaken", "undermines", "undermine", "partially_contradicts", "partially_refutes", "negative", "missing", "not_grounded", "unsupported", "opposes", "oppose"}
        or strength == "missing"
    )


# P0-1 Medium Promotion Calibration thresholds (semantic_alignment_score):
#   - method-depth (moderate): score >= METHOD_PROMOTION_STRONG_MIN_SCORE → strong;
#     METHOD_PROMOTION_MODERATE_MIN_SCORE <= score < strong-threshold → held at moderate;
#     score < moderate-threshold → held at moderate (low-score). All non-strong
#     outcomes preserve the medium/moderate tier so that
#     `_support_admission_tier` can surface them as `verified_moderate`.
#   - deep (results / table_or_figure / theory): score >= DEEP_PROMOTION_STRONG_MIN_SCORE → strong;
#     score < threshold → held at moderate.
METHOD_PROMOTION_STRONG_MIN_SCORE = 0.7
METHOD_PROMOTION_MODERATE_MIN_SCORE = 0.6
DEEP_PROMOTION_STRONG_MIN_SCORE = 0.6
DEEP_PROMOTION_NEAR_MISS_MIN_SCORE = 0.55
METHOD_PROMOTION_NEAR_MISS_MIN_SCORE = 0.65

# Mainline-Final-Integrated P0-1: final-strong guard threshold.  A support
# that the hygiene view re-scores below this number is held at
# ``verified_moderate`` even if it carried ``strength=strong`` from the live
# state.  Promotion-time scores may be higher than the hygiene re-score because
# ``build_decision_hygiene_view`` runs semantic grounding with the full final
# evidence pool; the guard catches the cases where the re-score drops below
# the calibrated promotion floor.
FINAL_STRONG_MIN_SCORE = 0.6

# Mainline-Final-Integrated P0-1: bucket / locator signals that mark a quote
# as a Limitation / Gap / Negative-evidence anchor.  Such anchors should
# never be admitted as positive strong support: they are at best flaw
# anchors.  The two source buckets are emitted by
# ``support_quality.evidence_section_bucket`` (``limitation_or_gap``) and
# by the quote-bank canonicalisation path (``negative_or_gap``).  The
# regex covers the locators that the runner writes when it canonicalises a
# negative quote-bank entry into a support row (see
# ``_negative_quote_bank_salvage_payload`` and the locator strings produced
# by ``_apply_quote_bank_entry_metadata``).
NEGATIVE_SUPPORT_BUCKETS = frozenset({"negative_or_gap", "limitation_or_gap"})
_NEGATIVE_SUPPORT_LOCATOR_RE = re.compile(
    r"\b(limitation|gap|negative\s+evidence|negative\s+excerpt|missing\s+comparison|no\s+ablation)\b",
    re.IGNORECASE,
)
# Buckets whose verified table/figure/theorem anchors may legitimately carry a
# low semantic_alignment_score (e.g. a table number with sparse textual
# overlap).  The guard exempts these only when grounding is paper_grounded_exact
# and the verified quote match type signals an exact reproduction.
_TABLE_OR_RESULT_ANCHOR_BUCKETS = frozenset(
    {"table_or_figure", "result_or_experiment", "ablation", "comparison", "theory_or_proof"}
)


def _evidence_negative_locator_or_bucket_signal(evidence: Dict[str, Any]) -> bool:
    """Return True iff the support is anchored on a Limitation / Gap / negative
    quote bucket or locator.

    The check covers ``support_source_bucket`` (the original Evidence Agent
    label) and ``quote_bank_claim_overlap_fallback_source_bucket`` (the bucket
    that was canonicalised into this support via the quote-bank claim-overlap
    fallback path).  It also matches the ``source_locator`` string against the
    deterministic Limitation / Gap regex so quotes copied verbatim from the
    paper's limitation section are recognised even when the Evidence Agent
    did not emit the negative bucket label.
    """
    if not isinstance(evidence, dict):
        return False
    bucket = str(evidence.get("support_source_bucket") or "").strip().lower()
    if bucket in NEGATIVE_SUPPORT_BUCKETS:
        return True
    fallback_bucket = str(
        evidence.get("quote_bank_claim_overlap_fallback_source_bucket") or ""
    ).strip().lower()
    if fallback_bucket in NEGATIVE_SUPPORT_BUCKETS:
        return True
    locator = str(evidence.get("source_locator") or "")
    if _NEGATIVE_SUPPORT_LOCATOR_RE.search(locator):
        return True
    return False


def _has_specific_or_empirical_locator_signal(evidence: Dict[str, Any]) -> bool:
    """Return True for verified supports with concrete empirical/method anchors.

    This is intentionally narrower than a global score-threshold relaxation: a
    near-miss moderate support only upgrades when it is paper-grounded,
    semantically verified, non-abstract, and anchored by a specific locator or
    by an empirical/table source bucket.
    """
    locator = str((evidence or {}).get("source_locator") or "")
    if _is_specific_locator(locator):
        return True
    if bool((evidence or {}).get("source_locator_specific")):
        return True
    declared_bucket = str((evidence or {}).get("support_source_bucket") or "").strip()
    decision_bucket = _decision_support_source_bucket(evidence or {})
    return declared_bucket in _TABLE_OR_RESULT_ANCHOR_BUCKETS or decision_bucket in _TABLE_OR_RESULT_ANCHOR_BUCKETS


def _verified_moderate_near_miss_promotion_path(evidence: Dict[str, Any]) -> str:
    """Classify safe near-miss verified moderate supports.

    The path is used both by the promotion rule and by dashboards. It avoids
    reviving abstract, negative, shallow, unverified, or semantic-mismatch
    rows; only concrete deep/method supports just below the strong threshold
    qualify.
    """
    if not isinstance(evidence, dict):
        return ""
    if str(evidence.get("stance") or "") not in {"supports", "partially_supports"}:
        return ""
    if _evidence_has_negative_intent(evidence) or _evidence_negative_locator_or_bucket_signal(evidence):
        return ""
    if str(evidence.get("verified_grounding_label") or "") not in VERIFIED_PAPER_GROUNDED_LABELS:
        return ""
    if str(evidence.get("semantic_grounding_label") or "") != "semantic_support_verified":
        return ""
    declared_bucket = str(evidence.get("support_source_bucket") or "").strip()
    decision_bucket = _decision_support_source_bucket(evidence)
    if declared_bucket == "abstract" or decision_bucket == "abstract":
        return ""
    if not _has_specific_or_empirical_locator_signal(evidence):
        return ""
    score = _normalize_float(evidence.get("semantic_alignment_score"), default=0.0)
    depth = _support_depth_label(evidence)
    if depth == "deep" and DEEP_PROMOTION_NEAR_MISS_MIN_SCORE <= score < DEEP_PROMOTION_STRONG_MIN_SCORE:
        return "near_miss_verified_deep_support"
    if depth == "moderate" and METHOD_PROMOTION_NEAR_MISS_MIN_SCORE <= score < METHOD_PROMOTION_STRONG_MIN_SCORE:
        return "near_miss_verified_method_support"
    return ""


def _final_strong_guard(evidence: Dict[str, Any]) -> None:
    """Mainline-Final-Integrated P0-1: downgrade low-score / negative-anchor
    strong supports during hygiene rendering.

    Two failure modes are caught:

    - **Negative locator / bucket**: the quote is from a Limitation / Gap /
      Negative evidence section, so it is at best a contextual flaw anchor.
      Downgrade to ``strength=medium`` unconditionally and tag the
      adjustment with ``downgraded_negative_locator``.  This catches the
      cross-pollination case where the quote-bank fallback canonicalised a
      ``negative_or_gap`` bucket onto a ``stance=supports`` support row.
    - **Low semantic alignment**: the hygiene re-scored
      ``semantic_alignment_score`` is below :data:`FINAL_STRONG_MIN_SCORE`.
      Downgrade unless the support is anchored by a verified table /
      figure / theorem quote where low textual overlap is expected.  Such
      anchor exceptions still require ``verified_grounding_label`` to be
      ``paper_grounded_exact`` and the verified-quote match-type to indicate
      an exact reproduction.

    The function is idempotent and operates in place on ``evidence``.  It does
    not touch the live ReviewState; it only runs from
    :func:`_verify_evidence_grounding_against_state`, which itself is only
    invoked by :func:`build_decision_hygiene_view`.
    """
    if not isinstance(evidence, dict):
        return
    if str(evidence.get("strength") or "") != "strong":
        return
    if str(evidence.get("stance") or "") not in {"supports", "partially_supports"}:
        return

    downgrade_reason = ""
    if _evidence_negative_locator_or_bucket_signal(evidence):
        downgrade_reason = "negative_locator_strong_support_downgrade"
    else:
        score = _normalize_float(evidence.get("semantic_alignment_score"), default=0.0)
        if score < FINAL_STRONG_MIN_SCORE:
            decision_bucket = _decision_support_source_bucket(evidence)
            grounding_label = str(evidence.get("verified_grounding_label") or "")
            match_type = str(evidence.get("verified_quote_match_type") or "").lower()
            near_miss_path = _verified_moderate_near_miss_promotion_path(evidence)
            anchor_exception = (
                decision_bucket in _TABLE_OR_RESULT_ANCHOR_BUCKETS
                and grounding_label == "paper_grounded_exact"
                and match_type
                in {
                    "exact",
                    "exact_match",
                    "exact_quote",
                    "quote_bank_id_canonical",
                    "quote_bank_raw_canonical",
                }
            )
            if not anchor_exception:
                downgrade_reason = "low_score_strong_support_downgrade"

    if not downgrade_reason:
        return

    evidence["strength"] = "medium"
    evidence["final_strength_guard_downgrade_reason"] = downgrade_reason
    evidence["strength_promotion_held_at_moderate"] = True
    if evidence.get("strength_promotion_from_medium_used"):
        evidence["strength_promotion_from_medium_used"] = False
    previous = str(evidence.get("support_quality_adjustment") or "")
    adjustment = (
        "downgraded_negative_locator"
        if downgrade_reason == "negative_locator_strong_support_downgrade"
        else "downgraded_low_semantic_alignment"
    )
    evidence["support_quality_adjustment"] = (
        f"{previous};{adjustment}" if previous and adjustment not in previous else (previous or adjustment)
    )


def _classify_medium_support_promotion_tier(evidence: Dict[str, Any]) -> Dict[str, Any]:
    """Decide whether a verified medium support should be promoted to strong.

    Returns ``{"tier": <strong|moderate|none>, "reason": <str>}``.  ``strong``
    promotes the support to ``strength=strong`` and tags
    ``strength_promotion_reason`` with the matching path.  ``moderate`` keeps
    the support at medium (so it surfaces as ``verified_moderate`` in the
    final-view admission tier) but records *why* the promotion was held.
    ``none`` means the support was not even a promotion candidate.
    """
    none = {"tier": "none", "reason": ""}
    if str(evidence.get("strength") or "") != "medium":
        return none
    initial_strength = str(evidence.get("initial_strength") or "")
    restored_from_low_score_guard = (
        initial_strength == "strong"
        and str(evidence.get("final_strength_guard_downgrade_reason") or "") == "low_score_strong_support_downgrade"
    )
    if initial_strength not in {"", "medium"} and not restored_from_low_score_guard:
        return none
    # Bug C fix: align with `_is_real_bound_support` instead of requiring the
    # explicit `bound_real_claim` tag.  Manager/binding pipelines mark a
    # support as bound by leaving `binding_status` empty or as `unchecked`
    # while the Evidence Agent has already merged the support into the real
    # claim's evidence_map — refusing those here forces every paper without
    # an explicit late-stage rebinding to stay zero-real.
    if str(evidence.get("binding_status") or "") not in {"", "unchecked", "bound_real_claim"}:
        return none
    if str(evidence.get("stance") or "") not in {"supports", "partially_supports"}:
        return none
    if _evidence_has_negative_intent(evidence):
        return none
    grounding_label = str(evidence.get("verified_grounding_label") or "")
    if grounding_label not in VERIFIED_PAPER_GROUNDED_LABELS:
        return none
    semantic_label = str(evidence.get("semantic_grounding_label") or "")
    if semantic_label != "semantic_support_verified":
        return none
    # Bug C fix: `verified_claim_overlap_score` is only populated on the
    # quote-bank claim-overlap *fallback* path (see
    # `_apply_quote_bank_entry_metadata`).  Supports that grounded directly
    # via `paper_grounded_exact` + `semantic_support_verified` never receive
    # an overlap score at all, so the original `> 0` gate silently rejected
    # the strongest grounding path.  Allow direct, fully-verified supports
    # to bypass the overlap requirement; keep the gate for weaker grounding
    # paths where overlap is the safety net.
    has_overlap = _normalize_int(evidence.get("verified_claim_overlap_score"), default=0, min_value=0) > 0
    is_direct_verified = grounding_label == "paper_grounded_exact" and semantic_label == "semantic_support_verified"
    if not (has_overlap or is_direct_verified):
        return none
    # Bug C fix: `support_depth` returns `moderate` for method-section
    # supports (see `support_quality.support_depth`).  A method-section
    # support that is fully paper-grounded, semantically verified, bound to
    # a real claim, non-abstract, and non-shallow is genuine real-strong
    # evidence — it is not the same as a `shallow` (abstract) support.
    # Allow {deep, moderate} but keep `shallow` and empty as hard rejects.
    depth = _support_depth_label(evidence)
    if depth not in {"deep", "moderate"}:
        return none
    source_bucket = str(evidence.get("support_source_bucket") or evidence.get("verified_source_bucket") or "")
    declared_bucket = str(evidence.get("support_source_bucket") or "").strip()
    decision_bucket = _decision_support_source_bucket(evidence)
    if source_bucket == "abstract":
        return none
    # Mainline-Final-Integrated P0-1: never promote a Limitation / Gap /
    # Negative-evidence anchor to strong, regardless of method/deep depth.
    # The same signals that block ``_final_strong_guard`` from admitting an
    # already-strong support are applied here so the promotion path itself
    # cannot launder a negative anchor into ``verified_strong``.
    if _evidence_negative_locator_or_bucket_signal(evidence):
        return {
            "tier": "moderate",
            "reason": "negative_anchor_support_held_at_moderate",
        }
    score = _normalize_float(evidence.get("semantic_alignment_score"), default=0.0)
    near_miss_path = _verified_moderate_near_miss_promotion_path(evidence)
    if depth == "deep":
        if score >= DEEP_PROMOTION_STRONG_MIN_SCORE:
            reason = (
                "verified_claim_overlap_deep_support" if has_overlap else "direct_verified_deep_support"
            )
            return {"tier": "strong", "reason": reason}
        match_type = str(evidence.get("verified_quote_match_type") or "").lower()
        locator = str(evidence.get("source_locator") or "")
        specific_anchor = bool(evidence.get("source_locator_specific")) or _is_specific_locator(locator)
        anchor_verified = (
            specific_anchor
            and grounding_label == "paper_grounded_exact"
            and match_type
            in {
                "exact",
                "exact_match",
                "exact_quote",
                "quote_bank_id_canonical",
                "quote_bank_raw_canonical",
            }
            and (declared_bucket in _TABLE_OR_RESULT_ANCHOR_BUCKETS or decision_bucket in _TABLE_OR_RESULT_ANCHOR_BUCKETS)
        )
        if anchor_verified:
            return {"tier": "moderate", "reason": "specific_anchor_low_score_support_held_at_moderate"}
        if near_miss_path == "near_miss_verified_deep_support":
            return {"tier": "moderate", "reason": near_miss_path}
        return {
            "tier": "moderate",
            "reason": "low_score_deep_support_held_at_moderate",
        }
    # depth == "moderate" (method-section)
    if score >= METHOD_PROMOTION_STRONG_MIN_SCORE:
        reason = (
            "verified_claim_overlap_method_support" if has_overlap else "direct_verified_method_support"
        )
        return {"tier": "strong", "reason": reason}
    if near_miss_path == "near_miss_verified_method_support":
        return {"tier": "moderate", "reason": near_miss_path}
    if score >= METHOD_PROMOTION_MODERATE_MIN_SCORE:
        return {
            "tier": "moderate",
            "reason": "moderate_score_method_support_held_at_moderate",
        }
    return {
        "tier": "moderate",
        "reason": "low_score_method_support_held_at_moderate",
    }


def _should_promote_verified_medium_support(evidence: Dict[str, Any]) -> bool:
    """Backward-compatible helper: True iff the verified medium support is
    eligible for promotion to ``strength=strong``.  Score-based moderate
    holds return False here while still being promotion *candidates* in the
    audit/shadow path."""
    return _classify_medium_support_promotion_tier(evidence)["tier"] == "strong"


def _has_trusted_existing_grounding(evidence: Dict[str, Any]) -> bool:
    if str(evidence.get("verified_grounding_label") or "") not in VERIFIED_PAPER_GROUNDED_LABELS:
        return False
    if str(evidence.get("semantic_grounding_label") or "") not in {
        "semantic_support_verified",
        "semantic_negative_verified",
    }:
        return False
    if not str(evidence.get("raw_quote") or "").strip():
        return False
    start = _normalize_int(evidence.get("verified_source_span_start"), default=-1)
    end = _normalize_int(evidence.get("verified_source_span_end"), default=-1)
    if start < 0 or end <= start:
        return False
    match_type = str(evidence.get("verified_quote_match_type") or "").strip().lower()
    return match_type in {
        "exact",
        "exact_match",
        "normalized",
        "normalized_match",
        "quote_bank_id_canonical",
        "quote_bank_raw_canonical",
        "quote_bank_claim_overlap_canonical",
    }


def _apply_final_support_promotion_and_guard(evidence: Dict[str, Any]) -> None:
    promotion_decision = _classify_medium_support_promotion_tier(evidence)
    promotion_tier = promotion_decision["tier"]
    promotion_reason = promotion_decision["reason"]
    if promotion_tier == "strong":
        evidence["strength"] = "strong"
        evidence["support_quality_adjustment"] = "promoted_verified_claim_matched_support"
        evidence["strength_promotion_from_medium_used"] = True
        evidence["strength_promotion_held_at_moderate"] = False
        evidence["strength_promotion_reason"] = promotion_reason
    elif promotion_tier == "moderate":
        evidence["strength_promotion_held_at_moderate"] = True
        evidence["strength_promotion_from_medium_used"] = False
        evidence["strength_promotion_reason"] = promotion_reason
    _final_strong_guard(evidence)


def _assess_quote_semantic_grounding(state: Dict[str, Any], evidence: Dict[str, Any]) -> Dict[str, Any]:
    """Check whether a paper-grounded quote semantically supports the evidence item.

    Quote existence is necessary but not sufficient: a copied abstract quote should
    not verify an evidence statement about a specific table, metric, or margin.
    This verifier is intentionally conservative and uses deterministic anchors
    before accepting strong support.
    """
    quote = str(evidence.get("raw_quote") or "")
    if not quote or evidence.get("verified_grounding_label") not in VERIFIED_PAPER_GROUNDED_LABELS:
        return {
            "semantic_grounding_label": "semantic_unverified_quote",
            "semantic_grounding_reasons": ["quote_not_verified"],
            "semantic_alignment_score": 0.0,
            "semantic_grounding_checked": True,
            "quote_evidence_semantic_mismatch": True,
        }

    claim_text = _claim_text_for_evidence(state or {}, str(evidence.get("claim_id") or ""))
    evidence_text = str(evidence.get("evidence") or "")
    agent_raw_quote = str(evidence.get("agent_raw_quote") or "")
    support_bucket = str(evidence.get("support_source_bucket") or evidence.get("verified_source_bucket") or "")
    source_locator = str(evidence.get("source_locator") or "")
    check_text = " ".join([claim_text, evidence_text, agent_raw_quote]).strip()
    reasons: List[str] = []

    check_numbers = _semantic_numeric_anchors(" ".join([evidence_text, agent_raw_quote]))
    quote_numbers = _semantic_numeric_anchors(quote)
    if check_numbers and not (check_numbers & quote_numbers):
        reasons.append("missing_numeric_anchor")

    check_tables = _semantic_table_anchors(" ".join([evidence_text, agent_raw_quote, source_locator]))
    quote_tables = _semantic_table_anchors(quote)
    if check_tables and not (check_tables & quote_tables):
        if not re.search(r"\b(table|figure|fig\.)\b", quote, re.IGNORECASE):
            reasons.append("missing_table_or_figure_anchor")

    quote_looks_abstract = bool(_SEMANTIC_ABSTRACT_MARKER_RE.search(quote[:260]))
    bucket_claims_result = support_bucket in {"result_or_experiment", "table_or_figure", "results"}
    if bucket_claims_result and quote_looks_abstract and not _SEMANTIC_TABLE_RE.search(quote):
        reasons.append("abstract_quote_used_for_result_support")

    score = _semantic_alignment_score(check_text, quote)
    has_anchor_match = bool((check_numbers & quote_numbers) or (check_tables & quote_tables))
    negative_intent = _evidence_has_negative_intent(evidence)
    quote_has_negative_anchor = bool(_SEMANTIC_NEGATIVE_TERMS_RE.search(quote))

    claim_overlap_verified = _has_verified_claim_overlap_support(evidence, min_score=2)

    semantic_weak_promotion_used = False
    semantic_weak_promotion_reason = ""

    if negative_intent:
        if not quote_has_negative_anchor:
            reasons.append("quote_lacks_negative_anchor")
        if reasons:
            label = "semantic_mismatch"
        elif has_anchor_match or score >= 0.14 or quote_has_negative_anchor:
            label = "semantic_negative_verified"
        elif score >= 0.08:
            label = "semantic_negative_weak"
            reasons.append("low_semantic_overlap")
        else:
            label = "semantic_mismatch"
            reasons.append("low_semantic_overlap")
    elif reasons:
        label = "semantic_mismatch"
    elif has_anchor_match or score >= 0.18:
        label = "semantic_support_verified"
    elif claim_overlap_verified and score >= 0.08:
        label = "semantic_support_verified"
        semantic_weak_promotion_used = True
        semantic_weak_promotion_reason = "verified_claim_overlap_low_semantic_alignment"
    elif score >= 0.08:
        label = "semantic_support_weak"
        reasons.append("low_semantic_overlap")
    else:
        label = "semantic_mismatch"
        reasons.append("low_semantic_overlap")

    return {
        "semantic_grounding_label": label,
        "semantic_grounding_reasons": reasons,
        "semantic_alignment_score": round(score, 4),
        "semantic_grounding_checked": True,
        "quote_evidence_semantic_mismatch": label == "semantic_mismatch",
        "semantic_weak_promotion_used": semantic_weak_promotion_used,
        "semantic_weak_promotion_reason": semantic_weak_promotion_reason,
    }


def _verify_evidence_grounding_against_state(state: Dict[str, Any], evidence: Dict[str, Any]) -> Dict[str, Any]:
    item = dict(evidence)
    if state.get("paper_id") and not item.get("paper_id"):
        item["paper_id"] = str(state.get("paper_id") or "")
    if not item.get("support_id"):
        item["support_id"] = str(item.get("evidence_id") or "")
    if not item.get("turn_id"):
        item["turn_id"] = _evidence_turn_index(item)
    if "initial_strength" not in item:
        item["initial_strength"] = str(item.get("strength") or "")
    if "initial_stance" not in item:
        item["initial_stance"] = str(item.get("stance") or "")
    item["source_locator_specific"] = _is_specific_locator(str(item.get("source_locator") or ""))
    item["support_depth"] = _support_depth_label(item)
    item["final_strength"] = str(item.get("strength") or "")
    item["final_support_depth"] = str(item.get("support_depth") or "")
    if _has_trusted_existing_grounding(item):
        _apply_programmatic_source_locator(state, item)
        _apply_final_support_promotion_and_guard(item)
        item["support_depth"] = _support_depth_label(item)
        item["final_strength"] = str(item.get("strength") or "")
        item["final_support_depth"] = str(item.get("support_depth") or "")
        return item
    quote_bank = _quote_bank_entries_for_grounding(state or {})
    if not quote_bank:
        return item

    quote_id = str(item.get("quote_id") or "")
    ordered_refs: List[Dict[str, Any]] = []
    seen_ids: set[int] = set()
    for entry in quote_bank:
        if quote_id and str(entry.get("quote_id") or "") == quote_id:
            ordered_refs.append(entry)
            seen_ids.add(id(entry))
    for entry in quote_bank:
        if id(entry) not in seen_ids:
            ordered_refs.append(entry)

    verification = _verify_quote_against_reference("", "")
    matched_quote_id_entry: Optional[Dict[str, Any]] = None
    if quote_id:
        for entry in quote_bank:
            if str(entry.get("quote_id") or "") == quote_id:
                matched_quote_id_entry = entry
                break

    if matched_quote_id_entry is not None:
        # The quote bank is program-extracted from the visible paper body, so a
        # valid quote_id is a stronger grounding anchor than the model's copied
        # raw_quote.  Preserve the model text for audit, but canonicalize the
        # evidence quote to the quote-bank source span.
        canonical_quote = str(matched_quote_id_entry.get("raw_quote") or "")
        _apply_quote_bank_entry_metadata(
            item,
            matched_quote_id_entry,
            canonicalize_quote=True,
            overwrite_locator=True,
        )
        verification = _verify_quote_against_reference(
            canonical_quote,
            canonical_quote,
            _normalize_int(matched_quote_id_entry.get("source_span_start"), default=-1),
        )
        verification["verified_quote_match_type"] = "quote_bank_id_canonical"
        verification["verified_grounding_reason"] = "quote_id matched a program-extracted quote-bank item; raw_quote was canonicalized to that item"
    else:
        for entry in ordered_refs:
            verification = _verify_quote_against_reference(
                str(item.get("raw_quote") or ""),
                str(entry.get("raw_quote") or ""),
                _normalize_int(entry.get("source_span_start"), default=-1),
            )
            if verification.get("verified_grounding_label") in VERIFIED_PAPER_GROUNDED_LABELS:
                canonical_quote = str(entry.get("raw_quote") or "")
                _apply_quote_bank_entry_metadata(
                    item,
                    entry,
                    canonicalize_quote=bool(canonical_quote),
                    overwrite_locator=False,
                )
                if canonical_quote:
                    verification = _verify_quote_against_reference(
                        canonical_quote,
                        canonical_quote,
                        _normalize_int(entry.get("source_span_start"), default=-1),
                    )
                    verification["verified_quote_match_type"] = "quote_bank_raw_canonical"
                    verification["verified_grounding_reason"] = "raw_quote matched a program-extracted quote-bank item; raw_quote was canonicalized to that item"
                break

    if verification.get("verified_grounding_label") not in VERIFIED_PAPER_GROUNDED_LABELS:
        overlap_entry = _select_claim_overlap_quote_bank_entry(state or {}, item, quote_bank)
        if overlap_entry is not None:
            canonical_quote = str(overlap_entry.get("raw_quote") or "")
            _apply_quote_bank_entry_metadata(
                item,
                overlap_entry,
                canonicalize_quote=bool(canonical_quote),
                overwrite_locator=False,
            )
            if canonical_quote:
                item["quote_bank_claim_overlap_fallback_used"] = True
                item["quote_bank_claim_overlap_fallback_quote_id"] = str(overlap_entry.get("quote_id") or "")
                item["quote_bank_claim_overlap_fallback_source_bucket"] = str(overlap_entry.get("source_bucket") or "")
                item["quote_bank_claim_overlap_fallback_score"] = _normalize_int(overlap_entry.get("claim_overlap_score"), default=0, min_value=0)
                verification = _verify_quote_against_reference(
                    canonical_quote,
                    canonical_quote,
                    _normalize_int(overlap_entry.get("source_span_start"), default=-1),
                )
                verification["verified_quote_match_type"] = "quote_bank_claim_overlap_canonical"
                verification["verified_grounding_reason"] = "raw_quote was not copied exactly, but a non-abstract claim-overlap quote-bank item was canonicalized"

    item.update(verification)
    semantic = _assess_quote_semantic_grounding(state, item)
    item.update(semantic)
    if item.get("verified_grounding_label") not in VERIFIED_PAPER_GROUNDED_LABELS and item.get("strength") == "strong":
        item["strength"] = "medium"
        item["support_quality_adjustment"] = "downgraded_unverified_quote_grounding"
    if item.get("strength") == "strong" and item.get("stance") in {"supports", "partially_supports"} and item.get("semantic_grounding_label") != "semantic_support_verified":
        item["strength"] = "medium"
        previous_adjustment = str(item.get("support_quality_adjustment") or "")
        semantic_adjustment = "downgraded_semantic_grounding_mismatch"
        item["support_quality_adjustment"] = (
            f"{previous_adjustment};{semantic_adjustment}" if previous_adjustment else semantic_adjustment
        )
    # P0-1/P0-2 calibration: classify the medium support into a promotion
    # tier based on `semantic_alignment_score`.  ``strong`` upgrades the
    # support to ``strength=strong`` with the legacy reason tags.  ``moderate``
    # keeps the support at medium so it surfaces as ``verified_moderate`` in
    # the final-view admission tier; the held-at-moderate reason is recorded
    # for audit (no impact on `_is_real_bound_support`, which still requires
    # ``strength=='strong'``).
    _apply_programmatic_source_locator(state, item)
    _apply_final_support_promotion_and_guard(item)
    item["support_depth"] = _support_depth_label(item)
    item["final_strength"] = str(item.get("strength") or "")
    item["final_support_depth"] = str(item.get("support_depth") or "")
    return item


def _verify_evidence_items_for_state(state: Dict[str, Any], evidence_items: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [_verify_evidence_grounding_against_state(state, item) for item in evidence_items]


def _is_verified_paper_grounded_evidence(evidence: Dict[str, Any]) -> bool:
    return str(evidence.get("verified_grounding_label") or "") in VERIFIED_PAPER_GROUNDED_LABELS


def _is_legacy_non_abstract_support_grounding(evidence: Dict[str, Any]) -> bool:
    source_text = " ".join(
        str(evidence.get(key) or "")
        for key in ("source", "source_locator", "support_source_bucket", "verified_source_bucket")
    ).strip().lower()
    if not source_text or "abstract" in source_text:
        return False
    if any(
        term in source_text
        for term in (
            "result",
            "experiment",
            "evaluation",
            "benchmark",
            "ablation",
            "table",
            "figure",
            "method",
            "section",
            "proof",
            "theorem",
        )
    ):
        return True
    bucket = _decision_support_source_bucket(evidence)
    return bucket in _EMPIRICAL_DECISION_BUCKETS or bucket in _METHOD_DECISION_BUCKETS


def _is_usable_support_grounding(evidence: Dict[str, Any]) -> bool:
    if _evidence_has_negative_intent(evidence):
        return False
    label = str(evidence.get("verified_grounding_label") or "").strip()
    semantic_label = str(evidence.get("semantic_grounding_label") or "").strip()
    if (
        label in {"", "unjudged"}
        and semantic_label in {"", "semantic_unjudged"}
        and not str(evidence.get("raw_quote") or "").strip()
        and not str(evidence.get("quote_id") or "").strip()
        and not str(evidence.get("verified_quote_match_type") or "").strip()
        and not bool(evidence.get("semantic_grounding_checked"))
    ):
        return _is_legacy_non_abstract_support_grounding(evidence)
    if label not in VERIFIED_PAPER_GROUNDED_LABELS:
        return False
    if semantic_label != "semantic_support_verified":
        return False
    return True


def _has_final_support_strength(evidence: Dict[str, Any]) -> bool:
    """Return True when evidence is safe to count as final-view support.

    The normal path is a verified ``strength=strong`` row.  The narrow fallback
    handles rows that were generated as strong support, then temporarily
    downgraded during an earlier semantic-mismatch pass, but later recovered by
    quote-bank canonicalisation and semantic verification.  This avoids losing
    verified support because of a stale downgrade marker while keeping negative,
    abstract, shallow, and low-score rows out of final support.
    """
    if str(evidence.get("strength") or "") == "strong":
        return True
    if str(evidence.get("initial_strength") or "") != "strong":
        return False
    if str(evidence.get("strength") or "") != "medium":
        return False
    if str(evidence.get("final_strength_guard_downgrade_reason") or ""):
        return False
    adjustment = str(evidence.get("support_quality_adjustment") or "").lower()
    if "downgraded_negative_locator" in adjustment:
        return False
    if _evidence_negative_locator_or_bucket_signal(evidence):
        return False
    if not _is_usable_support_grounding(evidence):
        return False
    depth = _support_depth_label(evidence)
    if depth not in {"deep", "moderate"}:
        return False
    declared_bucket = str(evidence.get("support_source_bucket") or "").strip()
    decision_bucket = _decision_support_source_bucket(evidence)
    if declared_bucket == "abstract" or decision_bucket == "abstract":
        return False
    score = _normalize_float(evidence.get("semantic_alignment_score"), default=0.0)
    threshold = DEEP_PROMOTION_STRONG_MIN_SCORE if depth == "deep" else METHOD_PROMOTION_STRONG_MIN_SCORE
    return score >= threshold or bool(_verified_moderate_near_miss_promotion_path(evidence))


def _support_observability_record(evidence: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "evidence_id": str(evidence.get("evidence_id") or ""),
        "support_id": str(evidence.get("support_id") or evidence.get("evidence_id") or ""),
        "claim_id": str(evidence.get("claim_id") or ""),
        "quote_id": str(evidence.get("quote_id") or ""),
        "raw_quote": str(evidence.get("raw_quote") or "")[:220],
        "agent_raw_quote": str(evidence.get("agent_raw_quote") or "")[:220],
        "source_locator": str(evidence.get("source_locator") or ""),
        "verified_quote_match_type": str(evidence.get("verified_quote_match_type") or ""),
        "semantic_grounding_label": str(evidence.get("semantic_grounding_label") or ""),
        "semantic_alignment_score": evidence.get("semantic_alignment_score", 0.0),
        "verified_claim_overlap_score": _verified_claim_overlap_score(evidence),
        "source_bucket": str(evidence.get("verified_source_bucket") or evidence.get("support_source_bucket") or ""),
        "support_depth": _support_depth_label(evidence),
        "strength": str(evidence.get("strength") or ""),
        "initial_strength": str(evidence.get("initial_strength") or ""),
        "quote_bank_claim_overlap_fallback_used": bool(evidence.get("quote_bank_claim_overlap_fallback_used")),
        "quote_bank_claim_overlap_fallback_quote_id": str(evidence.get("quote_bank_claim_overlap_fallback_quote_id") or ""),
        "quote_bank_claim_overlap_fallback_source_bucket": str(evidence.get("quote_bank_claim_overlap_fallback_source_bucket") or ""),
        "quote_bank_claim_overlap_fallback_score": _normalize_int(evidence.get("quote_bank_claim_overlap_fallback_score"), default=0, min_value=0),
        "semantic_weak_promotion_used": bool(evidence.get("semantic_weak_promotion_used")),
        "semantic_weak_promotion_reason": str(evidence.get("semantic_weak_promotion_reason") or ""),
        "strength_promotion_from_medium_used": bool(evidence.get("strength_promotion_from_medium_used")),
        "strength_promotion_reason": str(evidence.get("strength_promotion_reason") or ""),
        "included_in_final_view": False,
    }


def _is_real_paper_claim_id(claim_id: Any, declared_kind: Any = "") -> bool:
    return _classify_claim_kind(claim_id, declared_kind) == "paper_extracted"


def _is_specific_locator(locator: str) -> bool:
    loc = str(locator or "").strip().strip("'\"")
    if not loc:
        return False
    if _GENERIC_LOCATOR_RE.match(loc):
        return False
    return bool(_SPECIFIC_LOCATOR_RE.search(loc))



_LOCATOR_NAMED_ANCHOR_RE = re.compile(
    r"\b(?:Table|Figure|Fig\.|Algorithm|Theorem|Lemma|Proposition|Corollary)\s*[A-Z]?\d+(?:[.\-]\d+)?\b",
    re.IGNORECASE,
)
_LOCATOR_TABLE_FIGURE_RE = re.compile(
    r"\b(?:Table|Figure|Fig\.)\s*[A-Z]?\d+(?:[.\-]\d+)?\b",
    re.IGNORECASE,
)
_LOCATOR_LATEX_SECTION_RE = re.compile(
    r"\\(?:sub)*section\*?\{([^{}]{2,96})\}",
    re.IGNORECASE,
)
_LOCATOR_LATEX_REF_RE = re.compile(
    r"\\(?:c|C)?ref\{([^{}]{2,120})\}|\\autoref\{([^{}]{2,120})\}",
    re.IGNORECASE,
)
_LOCATOR_LATEX_CAPTION_RE = re.compile(
    r"\\caption\{([^{}]{8,180})\}",
    re.IGNORECASE,
)
_LOCATOR_SECTION_REF_RE = re.compile(
    r"\b(?:Sec\.|Section)\s*(\d+(?:\.\d+){0,3})\b",
    re.IGNORECASE,
)
_LOCATOR_NUMBERED_SECTION_RE = re.compile(
    r"(?:^|\n)\s*(\d+(?:\.\d+){0,3})\s+([A-Z][^\n]{2,96})"
)


def _format_locator_anchor(match: re.Match[str]) -> str:
    raw = re.sub(r"\s+", " ", match.group(0)).strip()
    raw = raw.replace("Fig.", "Figure")
    return raw[:96]


def _locator_type_from_anchor(anchor: str) -> str:
    value = str(anchor or "").strip().lower()
    if not value:
        return "generic"
    if re.search(r"\btable\b", value):
        return "table"
    if re.search(r"\bfigure|\bfig\.", value):
        return "figure"
    if re.search(r"\balgorithm\b", value):
        return "algorithm"
    if re.search(r"\b(theorem|lemma|proposition|corollary)\b", value):
        return "theorem"
    if re.search(r"\b(section|sec\.)\b|\b\d+\.\d+", value):
        return "section"
    return "generic"


def _latex_label_locator(label: str) -> str:
    first = str(label or "").split(",", 1)[0].strip()
    if not first:
        return ""
    prefix, _, raw_name = first.partition(":")
    prefix_l = prefix.strip().lower()
    name = raw_name.strip() or first
    name = re.sub(r"[_-]+", " ", name)
    name = re.sub(r"\s+", " ", name).strip()
    if prefix_l in {"fig", "figure"}:
        return f"Figure: {name[:72]}"
    if prefix_l in {"tab", "table"}:
        return f"Table: {name[:72]}"
    if prefix_l in {"sec", "section"}:
        return f"Section: {name[:72]}"
    if prefix_l in {"alg", "algorithm"}:
        return f"Algorithm: {name[:72]}"
    if prefix_l in {"thm", "theorem", "lem", "lemma", "prop", "proposition", "cor", "corollary"}:
        return f"Theorem: {name[:72]}"
    return ""


def _locator_anchor_details_from_text(text: str) -> Dict[str, Any]:
    value = str(text or "")
    named = _LOCATOR_NAMED_ANCHOR_RE.search(value)
    if named:
        locator = _format_locator_anchor(named)
        return {"locator": locator, "locator_type": _locator_type_from_anchor(locator), "locator_confidence": 0.9}
    section_ref = _LOCATOR_SECTION_REF_RE.search(value)
    if section_ref:
        locator = f"Section {section_ref.group(1)}"
        return {"locator": locator, "locator_type": "section", "locator_confidence": 0.85}
    latex_ref = _LOCATOR_LATEX_REF_RE.search(value)
    if latex_ref:
        locator = _latex_label_locator(latex_ref.group(1) or latex_ref.group(2) or "")
        if locator:
            return {"locator": locator, "locator_type": _locator_type_from_anchor(locator), "locator_confidence": 0.82}
    caption = _LOCATOR_LATEX_CAPTION_RE.search(value)
    if caption:
        caption_text = re.sub(r"\s+", " ", caption.group(1)).strip()
        if caption_text:
            return {
                "locator": f"Table/Figure caption: {caption_text[:72]}",
                "locator_type": "table",
                "locator_confidence": 0.78,
            }
    latex = _LOCATOR_LATEX_SECTION_RE.search(value)
    if latex:
        title = re.sub(r"\s+", " ", latex.group(1)).strip()
        if title:
            return {"locator": f"Section: {title[:80]}", "locator_type": "section", "locator_confidence": 0.75}
    numbered = _LOCATOR_NUMBERED_SECTION_RE.search(value)
    if numbered:
        number = numbered.group(1).strip()
        title = re.sub(r"\s+", " ", numbered.group(2)).strip()
        title = re.sub(r"\s{2,}.*$", "", title)
        return {"locator": f"Section {number}: {title[:72]}", "locator_type": "section", "locator_confidence": 0.75}
    return {"locator": "", "locator_type": "generic", "locator_confidence": 0.0}


def _locator_from_text_anchor(text: str) -> str:
    return str(_locator_anchor_details_from_text(text).get("locator") or "")


def _locator_span_overlap(a_start: int, a_end: int, b_start: int, b_end: int) -> int:
    if a_start < 0 or a_end <= a_start or b_start < 0 or b_end <= b_start:
        return 0
    return max(0, min(a_end, b_end) - max(a_start, b_start))


def _programmatic_source_locator_details(state: Dict[str, Any], evidence: Dict[str, Any]) -> Dict[str, Any]:
    current = str((evidence or {}).get("source_locator") or "").strip()
    if _is_specific_locator(current):
        return {
            "locator": current,
            "locator_type": _locator_type_from_anchor(current),
            "locator_confidence": 0.9,
            "reason": "existing_specific_locator",
        }
    direct_text = " ".join(
        str((evidence or {}).get(key) or "")
        for key in ("source_locator", "raw_quote", "agent_raw_quote", "evidence")
    )
    direct = _locator_anchor_details_from_text(direct_text)
    if direct.get("locator") and _is_specific_locator(str(direct.get("locator") or "")):
        direct["reason"] = "derived_from_evidence_text_anchor"
        return direct
    span_start = _normalize_int(
        (evidence or {}).get("verified_source_span_start")
        if (evidence or {}).get("verified_source_span_start") is not None
        else (evidence or {}).get("source_span_start"),
        default=-1,
    )
    span_end = _normalize_int(
        (evidence or {}).get("verified_source_span_end")
        if (evidence or {}).get("verified_source_span_end") is not None
        else (evidence or {}).get("source_span_end"),
        default=-1,
    )
    quote_id = str((evidence or {}).get("quote_id") or "")
    support_bucket = str(
        (evidence or {}).get("support_source_bucket")
        or (evidence or {}).get("verified_source_bucket")
        or ""
    )
    entries = _quote_bank_entries_for_grounding(state or {})
    best_near: Tuple[int, Dict[str, Any]] = (10**9, {"locator": "", "locator_type": "generic", "locator_confidence": 0.0, "reason": ""})
    for entry in entries:
        entry_locator = str(entry.get("source_locator") or "")
        entry_quote = str(entry.get("raw_quote") or "")
        if _is_specific_locator(entry_locator):
            entry_details = {
                "locator": entry_locator,
                "locator_type": _locator_type_from_anchor(entry_locator),
                "locator_confidence": 0.9,
            }
        else:
            entry_details = _locator_anchor_details_from_text(entry_quote)
        entry_anchor = str(entry_details.get("locator") or "")
        if not entry_anchor or not _is_specific_locator(entry_anchor):
            continue
        entry_start = _normalize_int(entry.get("source_span_start"), default=-1)
        entry_end = _normalize_int(entry.get("source_span_end"), default=-1)
        same_quote = bool(quote_id and str(entry.get("quote_id") or "") == quote_id)
        overlaps = _locator_span_overlap(span_start, span_end, entry_start, entry_end) > 0
        if same_quote or overlaps:
            return {
                "locator": entry_anchor,
                "locator_type": str(entry_details.get("locator_type") or _locator_type_from_anchor(entry_anchor)),
                "locator_confidence": 0.95 if same_quote else 0.9,
                "reason": "derived_from_quote_id" if same_quote else "derived_from_verified_span_overlap",
            }
        if span_start >= 0 and entry_start >= 0:
            distance = min(abs(span_start - entry_start), abs(span_start - entry_end))
            entry_bucket = str(entry.get("source_bucket") or "")
            compatible_bucket = (
                support_bucket in {"table_or_figure", "result_or_experiment", "results"}
                or entry_bucket in {"table_or_figure", "results"}
            )
            if compatible_bucket and distance < best_near[0] and distance <= 650:
                best_near = (
                    distance,
                    {
                        "locator": entry_anchor,
                        "locator_type": str(entry_details.get("locator_type") or _locator_type_from_anchor(entry_anchor)),
                        "locator_confidence": max(0.55, round(0.75 - min(distance, 650) / 2600, 3)),
                        "reason": "derived_from_nearby_quote_bank_anchor",
                    },
                )
    return best_near[1]


def _programmatic_source_locator(state: Dict[str, Any], evidence: Dict[str, Any]) -> str:
    return str(_programmatic_source_locator_details(state or {}, evidence or {}).get("locator") or "")


def _apply_programmatic_source_locator(state: Dict[str, Any], evidence: Dict[str, Any]) -> None:
    details = _programmatic_source_locator_details(state or {}, evidence or {})
    inferred = str(details.get("locator") or "")
    locator_type = str(details.get("locator_type") or "generic")
    locator_confidence = _normalize_float(details.get("locator_confidence"), default=0.0)
    evidence["locator_type"] = locator_type
    evidence["source_locator_type"] = locator_type
    evidence["locator_confidence"] = locator_confidence
    evidence["source_locator_confidence"] = locator_confidence
    if not inferred or not _is_specific_locator(inferred):
        evidence["source_locator_specific"] = _is_specific_locator(str(evidence.get("source_locator") or ""))
        return
    current = str(evidence.get("source_locator") or "")
    if current != inferred:
        evidence.setdefault("source_locator_original", current)
        evidence["source_locator"] = inferred
        evidence["source_locator_programmatic"] = True
        evidence["source_locator_programmatic_reason"] = str(details.get("reason") or "derived_from_verified_quote_or_quote_bank_anchor")
    evidence["source_locator_specific"] = True

def _real_claim_ids_from_state(state: Dict[str, Any]) -> set[str]:
    real_ids: set[str] = set()
    for item in state.get("claims", []) or []:
        claim_id = str(item.get("claim_id", "") or "")
        if not claim_id:
            continue
        if _is_real_paper_claim_id(claim_id, item.get("claim_kind") if isinstance(item, dict) else ""):
            real_ids.add(claim_id)
    return real_ids


def _claim_kind_counts(claims: Sequence[Dict[str, Any]]) -> Dict[str, int]:
    counts = {kind: 0 for kind in sorted(CLAIM_KINDS)}
    for item in claims or []:
        if not isinstance(item, dict):
            continue
        kind = _classify_claim_kind(item.get("claim_id"), item.get("claim_kind"))
        counts[kind] = counts.get(kind, 0) + 1
    return counts


def claim_coverage_summary(state: Dict[str, Any]) -> Dict[str, Any]:
    claims = [
        item
        for item in (state or {}).get("claims", []) or []
        if isinstance(item, dict) and str(item.get("claim_id") or "") and not str(item.get("claim_id") or "").startswith("claim-fallback")
    ]
    tag_counts = {tag: 0 for tag in sorted(CLAIM_COVERAGE_TAGS)}
    type_counts = {claim_type: 0 for claim_type in sorted(CLAIM_TYPES)}
    claim_summaries: List[Dict[str, Any]] = []
    for claim in claims:
        claim_text = _normalize_text(claim.get("claim"), max_length=500)
        claim_type = _normalize_text(claim.get("claim_type"), max_length=64).lower()
        if claim_type not in CLAIM_TYPES:
            claim_type = _infer_claim_type(claim, claim_text)
        type_counts[claim_type] = type_counts.get(claim_type, 0) + 1
        tags = _normalize_list_of_strings(claim.get("coverage_tags"), max_items=6, max_length=40)
        tags = [tag.lower() for tag in tags if tag.lower() in CLAIM_COVERAGE_TAGS]
        if not tags:
            tags = _normalize_claim_coverage_tags(claim, claim_text, claim_type)
        for tag in tags:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
        claim_summaries.append(
            {
                "claim_id": claim.get("claim_id", ""),
                "claim_type": claim_type,
                "coverage_tags": tags[:6],
                "evidence_need": _normalize_text(
                    claim.get("evidence_need"),
                    default=_default_claim_evidence_need(claim_type, tags),
                    max_length=160,
                ),
            }
        )
    missing_core_tags = [
        tag
        for tag in ("method", "empirical")
        if tag_counts.get(tag, 0) <= 0
    ]
    missing_review_tags = list(missing_core_tags)
    if tag_counts.get("limitation", 0) <= 0 and tag_counts.get("scope", 0) <= 0:
        missing_review_tags.append("limitation")
    thin_coverage = len(claims) < 3 or bool(missing_core_tags)
    full_claims_for_kinds = [
        item
        for item in (state or {}).get("claims", []) or []
        if isinstance(item, dict) and str(item.get("claim_id") or "")
    ]
    claim_kind_counts = _claim_kind_counts(full_claims_for_kinds)
    paper_extracted_count = claim_kind_counts.get("paper_extracted", 0)
    non_paper_claim_count = sum(
        value for key, value in claim_kind_counts.items() if key != "paper_extracted"
    )
    return {
        "claim_count": len(claims),
        "claim_type_counts": {key: value for key, value in type_counts.items() if value},
        "coverage_tag_counts": {key: value for key, value in tag_counts.items() if value},
        "missing_core_coverage_tags": missing_core_tags,
        "missing_review_coverage_tags": missing_review_tags,
        "has_method_claim": tag_counts.get("method", 0) > 0,
        "has_empirical_claim": tag_counts.get("empirical", 0) > 0,
        "has_limitation_sensitive_claim": tag_counts.get("limitation", 0) > 0 or tag_counts.get("scope", 0) > 0,
        "has_comparison_claim": tag_counts.get("comparison", 0) > 0,
        "claim_coverage_status": "thin" if thin_coverage else "expanded",
        "claim_coverage_expansion_recommended": thin_coverage,
        "claim_kind_counts": claim_kind_counts,
        "paper_extracted_claim_count": paper_extracted_count,
        "non_paper_claim_count": non_paper_claim_count,
        "claims": claim_summaries[:8],
    }


def _validate_evidence_bindings_for_state(state: Dict[str, Any], evidence_items: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    real_claim_ids = _real_claim_ids_from_state(state)
    validated: List[Dict[str, Any]] = []
    for evidence in evidence_items:
        item = dict(evidence)
        claim_id = str(item.get("claim_id", "") or "")
        source = str(item.get("source", "") or "")
        binding_status = "bound_real_claim"
        if source == "fallback-extraction":
            binding_status = "fallback_unverified"
        elif not claim_id:
            binding_status = "unbound"
        elif claim_id.startswith("claim-fallback"):
            binding_status = "fallback_bound"
        elif claim_id not in real_claim_ids:
            binding_status = "invalid_claim_id"
        item["binding_status"] = binding_status
        item["support_source_bucket"] = _normalize_text(
            item.get("support_source_bucket") or _evidence_source_bucket(item),
            default="other_or_unspecified",
            max_length=80,
        )
        item["support_quality"] = _normalize_text(
            item.get("support_quality") or _support_quality_label(item),
            default="unspecified_support",
            max_length=80,
        )
        positive_support = item.get("stance") in {"supports", "partially_supports"}
        if binding_status != "bound_real_claim" and item.get("strength") == "strong":
            item["strength"] = "medium" if positive_support else item.get("strength")
            item["support_quality_adjustment"] = "downgraded_unbound_or_fallback_support"
        if binding_status == "fallback_unverified" and item.get("strength") == "strong":
            item["strength"] = "medium"
            item["support_quality_adjustment"] = "downgraded_fallback_support"
        if (
            binding_status == "bound_real_claim"
            and positive_support
            and item.get("strength") == "strong"
            and item.get("support_source_bucket") == "abstract"
        ):
            item["strength"] = "medium"
            item["support_quality"] = "abstract_claim_support"
            item["support_quality_adjustment"] = "downgraded_abstract_only_support"
        validated.append(item)
    return validated


_CONTEXT_LIMITATION_FLAW_TERMS = (
    "provided excerpt",
    "provided abstract excerpt",
    "provided text",
    "excerpt",
    "abstract cuts off",
    "abstract ends abruptly",
    "abstract ends mid-sentence",
    "abstract is truncated",
    "abstract truncated",
    "truncated abstract",
    "truncated excerpt",
    "truncated evidence",
    "truncated text",
    "evidence is truncated",
    "evidence text is truncated",
    "evidence truncated",
    "text is truncated",
    "truncated paper",
    "cuts off mid-sentence",
    "ends mid-sentence",
    "cut off",
    "incomplete abstract prevents",
    "abstract truncation",
    "incomplete abstract truncation",
    "incomplete abstract verification",
    "incomplete paper text",
    "missing abstract details",
    "explicit excerpt support",
    "excerpt support",
    "full extraction",
    "full text",
    "in the abstract",
)
_GENERIC_LACK_SUPPORT_PATTERN = re.compile(
    r"\b(?:lack(?:s|ing)?|missing|insufficient|unsubstantiated|unverified|unverifiable|unsupported)\b.{0,90}\b(?:empirical|quantitative|experimental|validation|metrics?|scores?|numbers?|benchmark|baseline|ablation|evidence|results?|evaluation|performance)\b"
    r"|\b(?:no|without)\s+(?:specific\s+|concrete\s+|clear\s+|explicit\s+|sufficient\s+)?(?:empirical|quantitative|experimental|validation|metrics?|scores?|numbers?|benchmark|baseline|ablation|evidence|results?|evaluation|performance)\b",
    re.IGNORECASE,
)


def _combined_flaw_text(title: str, description: str, source: str = "") -> str:
    return f"{title} {description} {source}".lower()


def _is_context_limitation_flaw_text(text: str) -> bool:
    lowered = str(text or "").lower()
    return any(term in lowered for term in _CONTEXT_LIMITATION_FLAW_TERMS)


def _is_schema_or_meta_artifact_flaw(flaw_id: str, text: str) -> bool:
    lowered = str(text or "").lower()
    return (
        flaw_id.startswith("flaw-fallback")
        or "\"flaw_candidates\"" in lowered
        or lowered.strip().startswith("{")
        or "the user wants me" in lowered
        or "raw output" in lowered
        or "valid json" in lowered
        or "parse failure" in lowered
        or "schema" in lowered
        or _is_context_limitation_flaw_text(lowered)
        or "evidence map" in lowered
        or "non-existent evidence" in lowered
        or "marked supported" in lowered
        or "marked as supported" in lowered
        or "dialogue confirms" in lowered
    )


def _context_limitation_question_from_flaw_item(item: Any, fallback_index: int) -> Optional[Dict[str, Any]]:
    if not isinstance(item, dict):
        return None
    title = _normalize_text(item.get("title") or item.get("flaw"), max_length=160)
    description = _normalize_text(item.get("description"), max_length=600)
    source = _normalize_text(item.get("source"), max_length=80)
    text = _combined_flaw_text(title, description, source)
    if not _is_context_limitation_flaw_text(text):
        return None
    seed = title or description or f"context-limitation-{fallback_index}"
    return {
        "question_id": _slugify("question", f"assessment-limitation-{seed}", fallback_index),
        "question": "Assessment limitation: this critique was not grounded as a paper defect; verify it with method, result, table, or figure evidence before treating it as a weakness.",
        "status": "open",
        "related_claim_ids": _normalize_list_of_strings(item.get("related_claim_ids"), max_items=6, max_length=80),
    }


def _normalize_flaw_item(item: Any, fallback_index: int) -> Optional[Dict[str, Any]]:
    if not isinstance(item, dict):
        return None
    title = _normalize_text(item.get("title") or item.get("flaw"), max_length=160)
    description = _normalize_text(item.get("description"), max_length=600)
    if not title and not description:
        return None
    seed = title or description
    flaw_id = _normalize_text(item.get("flaw_id"), max_length=80) or _slugify("flaw", seed, fallback_index)
    source = _normalize_text(item.get("source"), max_length=80)
    grounding_status = _normalize_text(item.get("grounding_status"), max_length=80)
    severity = _normalize_choice(item.get("severity"), FLAW_SEVERITY, "major")
    status = _normalize_choice(item.get("status"), FLAW_STATUS, "candidate")
    confidence = _normalize_float(item.get("confidence"), default=0.5)
    text = _combined_flaw_text(title, description, source)
    is_schema_or_meta_artifact = _is_schema_or_meta_artifact_flaw(flaw_id, text)
    if is_schema_or_meta_artifact:
        return None
    is_fallback_or_meta = source in {"fallback", "fallback-extraction", "system_meta"}
    if is_fallback_or_meta:
        source = source or "fallback-extraction"
        grounding_status = grounding_status or "fallback_unverified"
        severity = "minor"
        status = "downgraded"
        confidence = min(confidence, 0.25)
    evidence_ids = _normalize_list_of_strings(item.get("evidence_ids"), max_items=6, max_length=80)
    raw_negative_ids = _normalize_list_of_strings(
        item.get("negative_evidence_ids")
        or item.get("hard_negative_evidence_ids")
        or item.get("contradicting_evidence_ids"),
        max_items=6,
        max_length=80,
    )
    # ``negative_evidence_ids`` is the explicit hard-negative anchor for the
    # flaw (evidence that contradicts/refutes/weakens the related claim, or
    # evidence demonstrating a missing required artifact).  We keep it as a
    # subset of ``evidence_ids`` so legacy consumers that only read
    # ``evidence_ids`` still see the same anchor list, while the renderer can
    # ask ``_flaw_has_negative_grounding`` to require an explicit anchor for
    # *Grounded paper weaknesses*.
    negative_evidence_ids: List[str] = []
    if raw_negative_ids:
        negative_evidence_ids = [eid for eid in raw_negative_ids if eid]
        for eid in negative_evidence_ids:
            if eid not in evidence_ids:
                evidence_ids.append(eid)
        if len(evidence_ids) > 6:
            evidence_ids = evidence_ids[:6]
    normalized = {
        "flaw_id": flaw_id,
        "title": title or description[:120],
        "description": description or title,
        "severity": severity,
        "status": status,
        "related_claim_ids": _normalize_list_of_strings(item.get("related_claim_ids"), max_items=6, max_length=80),
        "evidence_ids": evidence_ids,
        "confidence": confidence,
    }
    if negative_evidence_ids:
        normalized["negative_evidence_ids"] = negative_evidence_ids
    if source:
        normalized["source"] = source
    if grounding_status:
        normalized["grounding_status"] = grounding_status
    negative_evidence_type = _normalize_text(item.get("negative_evidence_type"), max_length=80)
    if negative_evidence_type:
        normalized["negative_evidence_type"] = negative_evidence_type
    if is_fallback_or_meta:
        normalized["hygiene_status_reason"] = "fallback_or_meta_flaw_not_paper_defect"
    return normalized


def _normalize_questions(value: Any) -> List[Dict[str, Any]]:
    if value is None:
        return []
    if not isinstance(value, list):
        value = [value]
    results = []
    seen = set()
    for idx, item in enumerate(value, start=1):
        normalized = _normalize_question_item(item, idx)
        if normalized is None:
            continue
        key = (normalized["question_id"], normalized["question"].lower())
        if key in seen:
            continue
        seen.add(key)
        results.append(normalized)
        if len(results) >= 10:
            break
    return results


def _sanitize_conflict_excerpt(text: Any, max_length: int = 96) -> str:
    value = str(text or "")
    value = value.replace("<think>", " ").replace("</think>", " ")
    value = value.replace("<json>", " ").replace("</json>", " ")
    value = " ".join(value.split())
    if len(value) <= max_length:
        return value
    return value[: max(0, max_length - 3)].rstrip() + "..."


def _normalize_conflicts(value: Any) -> List[Dict[str, Any]]:
    if value is None:
        return []
    if not isinstance(value, list):
        value = [value]
    results = []
    seen = set()
    for idx, item in enumerate(value, start=1):
        normalized = _normalize_conflict_item(item, idx)
        if normalized is None:
            continue
        key = (
            normalized["note"].lower(),
            normalized.get("claim_id", ""),
            normalized.get("evidence_id", ""),
            normalized.get("flaw_id", ""),
        )
        if key in seen:
            continue
        seen.add(key)
        results.append(normalized)
        if len(results) >= 12:
            break
    return results


def _append_revision_event(
    revisions: List[Dict[str, Any]],
    entity_type: str,
    entity_id: str,
    field: str,
    before: Any,
    after: Any,
    reason: str = "incoming_update",
) -> None:
    if before == after:
        return
    revisions.append(
        {
            "event_id": _slugify("revision", f"{entity_type}-{entity_id}-{field}-{len(revisions) + 1}", len(revisions) + 1),
            "entity_type": entity_type,
            "entity_id": entity_id,
            "field": field,
            "before": copy.deepcopy(before),
            "after": copy.deepcopy(after),
            "reason": reason,
        }
    )


def _coerce_status_transition(entity_type: str, entity_id: str, before: Any, proposed: Any) -> tuple[Any, Optional[Dict[str, Any]]]:
    if before in (None, "") or before == proposed:
        return proposed, None

    transition_sets = {
        "claim": CLAIM_STATUS_TRANSITIONS,
        "flaw": FLAW_STATUS_TRANSITIONS,
        "unresolved_question": QUESTION_STATUS_TRANSITIONS,
    }
    allowed = transition_sets.get(entity_type, {}).get(before, {before, proposed})
    if proposed in allowed:
        return proposed, None

    return before, {
        "conflict_id": _slugify("conflict", f"{entity_type}-{entity_id}-lifecycle-{before}-{proposed}", 1),
        "note": f"Ignored unsupported lifecycle transition for {entity_type} {entity_id}: {before} -> {proposed}.",
        "claim_id": entity_id if entity_type == "claim" else "",
        "evidence_id": "",
        "flaw_id": entity_id if entity_type == "flaw" else "",
        "conflict_type": "lifecycle_guard",
    }


def _merge_items_with_revisions(
    existing: List[Dict[str, Any]],
    incoming: List[Dict[str, Any]],
    key: str,
    entity_type: str,
    tracked_fields: Iterable[str],
    max_items: int,
) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    merged = copy.deepcopy(existing)
    index = {item[key]: idx for idx, item in enumerate(merged) if key in item}
    revisions: List[Dict[str, Any]] = []
    lifecycle_conflicts: List[Dict[str, Any]] = []
    for item in incoming:
        item_key = item[key]
        if item_key in index:
            current = merged[index[item_key]]
            updated = copy.deepcopy(item)
            if entity_type == "evidence":
                for lifecycle_field in ("initial_strength", "initial_stance"):
                    if current.get(lifecycle_field):
                        updated[lifecycle_field] = current.get(lifecycle_field)
            if "status" in tracked_fields and "status" in updated:
                coerced_status, lifecycle_note = _coerce_status_transition(entity_type, item_key, current.get("status"), updated.get("status"))
                updated["status"] = coerced_status
                if lifecycle_note is not None:
                    lifecycle_conflicts.append(lifecycle_note)
            for field in tracked_fields:
                old_value = current.get(field)
                new_value = updated.get(field, old_value)
                if old_value != new_value:
                    reason = "incoming_status_update" if field == "status" else "incoming_update"
                    _append_revision_event(revisions, entity_type, item_key, field, old_value, new_value, reason=reason)
            current.update(updated)
        else:
            merged.append(copy.deepcopy(item))
            index[item_key] = len(merged) - 1
    return merged[:max_items], revisions, lifecycle_conflicts


def _evidence_retention_score(item: Dict[str, Any]) -> int:
    claim_id = str(item.get("claim_id") or "")
    strength = str(item.get("strength") or "").lower()
    stance = str(item.get("stance") or "").lower()
    source = str(item.get("source") or "").lower()
    binding_status = str(item.get("binding_status") or "").lower()
    support_bucket = str(item.get("support_source_bucket") or "").lower()
    support_quality = str(item.get("support_quality") or "").lower()
    evidence_text = str(item.get("evidence") or "").lower()
    combined_text = " ".join([source, support_bucket, support_quality, evidence_text])

    score = 0
    if claim_id and not claim_id.startswith("claim-fallback"):
        score += 100
    else:
        score -= 120
    if binding_status == "bound_real_claim":
        score += 60
    elif binding_status in {"fallback_bound", "fallback_unverified", "unbound"}:
        score -= 80
    if strength == "strong":
        score += 70
    elif strength == "medium":
        score += 25
    elif strength == "weak":
        score += 5
    if stance in {"supports", "support", "partially_supports", "corroborates"}:
        score += 30
    elif stance == "contradicts":
        score += 25
    if any(token in combined_text for token in ("table", "figure", "ablation", "experiment", "evaluation", "result", "baseline", "dataset", "metric")):
        score += 35
    elif any(token in combined_text for token in ("method", "approach", "framework", "model", "algorithm")):
        score += 25
    elif "abstract" in combined_text:
        score += 5
    if source == "fallback-extraction":
        score -= 60
    return score


def _retain_evidence_items(items: List[Dict[str, Any]], max_items: int = 12) -> List[Dict[str, Any]]:
    if len(items) <= max_items:
        return items
    indexed = list(enumerate(items))
    ranked = sorted(indexed, key=lambda pair: (-_evidence_retention_score(pair[1]), pair[0]))
    selected_indices = {idx for idx, _ in ranked[:max_items]}
    return [item for idx, item in indexed if idx in selected_indices]


def _evidence_signature(item: Dict[str, Any]) -> tuple[str, str, str, str, str, str]:
    return (
        _normalize_text(item.get("claim_id"), max_length=80).lower(),
        _normalize_text(item.get("evidence"), max_length=600).lower(),
        _normalize_text(item.get("source"), max_length=120).lower(),
        _normalize_text(item.get("strength"), max_length=40).lower(),
        _normalize_text(item.get("stance"), max_length=40).lower(),
        _normalize_text(item.get("binding_status"), max_length=80).lower(),
    )


def _next_evidence_id(used_ids: set[str]) -> str:
    max_numeric_id = 0
    for evidence_id in used_ids:
        match = re.fullmatch(r"evidence-(\d+)", str(evidence_id or ""))
        if match:
            max_numeric_id = max(max_numeric_id, int(match.group(1)))
    candidate_index = max_numeric_id + 1
    while True:
        candidate = f"evidence-{candidate_index}"
        if candidate not in used_ids:
            return candidate
        candidate_index += 1


def _preserve_colliding_evidence_ids(
    existing: List[Dict[str, Any]],
    incoming: List[Dict[str, Any]],
) -> tuple[List[Dict[str, Any]], Dict[str, str], int]:
    existing_signatures = {
        str(item.get("evidence_id") or ""): _evidence_signature(item)
        for item in existing
        if item.get("evidence_id")
    }
    used_ids = {str(item.get("evidence_id") or "") for item in existing if item.get("evidence_id")}
    incoming_signatures: Dict[str, tuple[str, str, str, str, str, str]] = {}
    collision_aliases: Dict[tuple[str, tuple[str, str, str, str, str, str]], str] = {}
    renamed_by_original: Dict[str, set[str]] = {}
    rewritten: List[Dict[str, Any]] = []
    collision_count = 0

    for evidence in incoming:
        item = copy.deepcopy(evidence)
        evidence_id = str(item.get("evidence_id") or "")
        signature = _evidence_signature(item)
        existing_signature = existing_signatures.get(evidence_id)
        incoming_signature = incoming_signatures.get(evidence_id)
        material_collision = (
            bool(evidence_id)
            and (
                (existing_signature is not None and existing_signature != signature)
                or (incoming_signature is not None and incoming_signature != signature)
            )
        )
        if material_collision:
            alias_key = (evidence_id, signature)
            new_id = collision_aliases.get(alias_key)
            if new_id is None:
                new_id = _next_evidence_id(used_ids)
                collision_aliases[alias_key] = new_id
                used_ids.add(new_id)
                collision_count += 1
            item["original_evidence_id"] = evidence_id
            item["evidence_id"] = new_id
            item["evidence_id_collision_preserved"] = True
            item["evidence_id_collision_reason"] = "materially_different_same_evidence_id"
            renamed_by_original.setdefault(evidence_id, set()).add(new_id)
            evidence_id = new_id
        elif evidence_id:
            used_ids.add(evidence_id)
            item["evidence_id_collision_preserved"] = bool(item.get("evidence_id_collision_preserved"))

        if evidence_id:
            incoming_signatures[evidence_id] = _evidence_signature(item)
        rewritten.append(item)

    unambiguous_renames = {
        original_id: next(iter(new_ids))
        for original_id, new_ids in renamed_by_original.items()
        if len(new_ids) == 1
    }
    return rewritten, unambiguous_renames, collision_count


def _rewrite_evidence_references_for_renamed_ids(payload: Dict[str, Any], rename_map: Dict[str, str]) -> None:
    if not rename_map:
        return

    def rewrite_id(value: Any) -> Any:
        value_str = str(value or "")
        return rename_map.get(value_str, value)

    def rewrite_list(values: Any) -> List[str]:
        # P0-5: synthetic recovery markers must not survive a rename pass —
        # strip them so claims/recovery patches never reference them.
        return _strip_synthetic_recovery_markers(
            [str(rewrite_id(value)) for value in _normalize_list_of_strings(values, max_items=12, max_length=80)]
        )

    for claim in payload.get("claims", []) or []:
        if isinstance(claim, dict):
            claim["supporting_evidence_ids"] = rewrite_list(claim.get("supporting_evidence_ids", []))
    for flaw in payload.get("flaw_candidates", []) or []:
        if isinstance(flaw, dict):
            flaw["evidence_ids"] = rewrite_list(flaw.get("evidence_ids", []))
    for conflict in payload.get("conflict_notes", []) or []:
        if isinstance(conflict, dict) and conflict.get("evidence_id"):
            conflict["evidence_id"] = rewrite_id(conflict.get("evidence_id"))
    for key in ("target_evidence_ids", "supporting_evidence_ids"):
        if key in payload:
            payload[key] = rewrite_list(payload.get(key, []))


def _merge_question_items(
    existing: List[Dict[str, Any]],
    incoming: List[Dict[str, Any]],
) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    merged = copy.deepcopy(existing)
    by_id = {item["question_id"]: idx for idx, item in enumerate(merged) if "question_id" in item}
    by_text = {item.get("question", "").lower(): idx for idx, item in enumerate(merged) if item.get("question")}
    revisions: List[Dict[str, Any]] = []
    lifecycle_conflicts: List[Dict[str, Any]] = []
    for item in incoming:
        idx = by_id.get(item["question_id"])
        if idx is None:
            idx = by_text.get(item["question"].lower())
        if idx is None:
            merged.append(copy.deepcopy(item))
            idx = len(merged) - 1
            by_id[item["question_id"]] = idx
            by_text[item["question"].lower()] = idx
            continue
        current = merged[idx]
        updated = copy.deepcopy(item)
        coerced_status, lifecycle_note = _coerce_status_transition(
            "unresolved_question",
            current["question_id"],
            current.get("status"),
            updated.get("status"),
        )
        updated["status"] = coerced_status
        if lifecycle_note is not None:
            lifecycle_conflicts.append(lifecycle_note)
        for field in ("question", "status", "related_claim_ids"):
            old_value = current.get(field)
            new_value = updated.get(field, old_value)
            if old_value != new_value:
                reason = "incoming_status_update" if field == "status" else "incoming_update"
                _append_revision_event(revisions, "unresolved_question", current["question_id"], field, old_value, new_value, reason=reason)
        current.update(updated)
    return merged[:10], revisions, lifecycle_conflicts


def _merge_conflict_notes(
    existing: List[Dict[str, Any]],
    incoming: List[Dict[str, Any]],
    max_items: int = 12,
) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    merged = copy.deepcopy(existing)
    seen = {
        (
            item.get("note", "").lower(),
            item.get("claim_id", ""),
            item.get("evidence_id", ""),
            item.get("flaw_id", ""),
        )
        for item in merged
    }
    added: List[Dict[str, Any]] = []
    for item in incoming:
        key = (
            item.get("note", "").lower(),
            item.get("claim_id", ""),
            item.get("evidence_id", ""),
            item.get("flaw_id", ""),
        )
        if key in seen:
            continue
        seen.add(key)
        copied = copy.deepcopy(item)
        merged.append(copied)
        added.append(copied)
    return merged[:max_items], added[:max_items]


def _collect_claim_evidence(state: Dict[str, Any], claim_id: str) -> List[Dict[str, Any]]:
    return [item for item in state.get("evidence_map", []) if item.get("claim_id") == claim_id]


def _real_strong_support_counts(state: Dict[str, Any]) -> Dict[str, int]:
    real_claim_ids = _real_claim_ids_from_state(state)
    counts: Dict[str, int] = {}
    for item in state.get("evidence_map", []) or []:
        claim_id = str(item.get("claim_id") or "")
        if (
            claim_id in real_claim_ids
            and item.get("strength") == "strong"
            and item.get("stance") in {"supports", "partially_supports"}
            and str(item.get("source") or "") != "fallback-extraction"
            and str(item.get("binding_status") or "bound_real_claim") in {"", "unchecked", "bound_real_claim"}
        ):
            counts[claim_id] = counts.get(claim_id, 0) + 1
    return counts


def _generic_lack_support_flaw_conflicts_with_support(flaw: Dict[str, Any], support_counts: Dict[str, int]) -> bool:
    if flaw.get("status") in {"downgraded", "retracted"}:
        return False
    if flaw.get("evidence_ids"):
        return False
    text = " ".join(str(flaw.get(key) or "") for key in ("title", "description")).lower()
    if "anchored evidence" in text or "grounded evidence" in text:
        return False
    if not _GENERIC_LACK_SUPPORT_PATTERN.search(text):
        return False
    related_claim_ids = [str(item) for item in flaw.get("related_claim_ids", []) or [] if str(item)]
    return any(support_counts.get(claim_id, 0) > 0 for claim_id in related_claim_ids)


def _claim_gap_should_be_not_assessable(claim: Dict[str, Any]) -> bool:
    """Route low-provenance claim gaps away from paper-negative burden.

    Small-model claim salvage and context-synthesized claims are useful
    diagnostic coverage scaffolds, but an unsupported scaffold claim should not
    become an open paper flaw.  The claim remains in ReviewState for follow-up;
    its lack of support is represented as an assessment limitation instead of
    an actionable evidence gap.
    """
    claim_id = str(claim.get("claim_id") or "").strip().lower()
    origin_kind = str(claim.get("claim_origin_kind") or "").strip().lower()
    origin = " ".join(
        str(claim.get(key) or "")
        for key in ("claim_origin", "claim_source", "source_stage", "provenance")
    ).lower()
    return (
        claim_id.startswith("claim-paper-context-")
        or claim_id.startswith("claim-paper-fallback-")
        or origin_kind in {"context_synthesized", "raw_salvaged_claim_agent_output"}
        or "context_derived" in origin
        or "raw_salvage" in origin
        or "malformed_claim_agent_output" in origin
    )


def _refresh_state_consistency(state: Dict[str, Any]) -> tuple[Dict[str, Any], List[Dict[str, Any]], List[Dict[str, Any]]]:
    refreshed = copy.deepcopy(state)
    derived_revisions: List[Dict[str, Any]] = []
    derived_conflicts: List[Dict[str, Any]] = []
    derived_gaps = _normalize_evidence_gaps(refreshed.get("evidence_gaps", []), max_items=20)
    hypotheses = list(refreshed.get("current_hypotheses", []))
    transient_status_locks = dict(refreshed.get("_transient_status_locks", {}) or {})
    persistent_status_guards = dict(refreshed.get("_persistent_status_guards", {}) or {})

    claims = refreshed.get("claims", [])
    flaws = refreshed.get("flaw_candidates", [])
    for claim in claims:
        claim_id = claim.get("claim_id", "")
        lock_status = transient_status_locks.get(_status_lock_key("claim", claim_id))
        guarded_status = persistent_status_guards.get(_status_lock_key("claim", claim_id))
        linked_evidence = _collect_claim_evidence(refreshed, claim_id)
        supporting = [item for item in linked_evidence if item.get("stance") in {"supports", "partially_supports"}]
        contradicting = [item for item in linked_evidence if item.get("stance") == "contradicts"]
        positive_ids = [item.get("evidence_id", "") for item in supporting if item.get("evidence_id")]
        merged_support_ids = _strip_synthetic_recovery_markers(
            _normalize_list_of_strings(
                list(claim.get("supporting_evidence_ids", [])) + positive_ids,
                max_items=6,
                max_length=80,
            )
        )
        if claim.get("supporting_evidence_ids", []) != merged_support_ids:
            _append_revision_event(
                derived_revisions,
                "claim",
                claim_id,
                "supporting_evidence_ids",
                claim.get("supporting_evidence_ids", []),
                merged_support_ids,
                reason="evidence_sync",
            )
            claim["supporting_evidence_ids"] = merged_support_ids

        current_status = claim.get("status", "uncertain")
        desired_status = current_status
        strong_support = any(item.get("strength") == "strong" for item in supporting)
        if supporting and contradicting:
            desired_status = "partially_supported"
            note = {
                "conflict_id": _slugify("conflict", f"{claim_id}-mixed-evidence-{len(derived_conflicts)+1}", len(derived_conflicts) + 1),
                "note": f"Claim {claim_id} now has mixed supporting and contradictory evidence.",
                "claim_id": claim_id,
                "evidence_id": contradicting[0].get("evidence_id", ""),
                "flaw_id": "",
                "conflict_type": "mixed_evidence",
            }
            derived_conflicts.append(note)
            hypothesis = f"Claim {claim_id} may only be partially supported because the evidence is mixed."
            if hypothesis not in hypotheses:
                hypotheses.append(hypothesis)
            derived_gaps = _set_evidence_gap_status(
                derived_gaps,
                claim_id=claim_id,
                status="resolved",
                evidence_id=positive_ids[0] if positive_ids else "",
                resolution="supporting_evidence_bound",
            )
        elif contradicting:
            note = {
                "conflict_id": _slugify("conflict", f"{claim_id}-derived-{len(derived_conflicts)+1}", len(derived_conflicts) + 1),
                "note": f"Claim {claim_id} is challenged by contradictory evidence and should be rechecked.",
                "claim_id": claim_id,
                "evidence_id": contradicting[0].get("evidence_id", ""),
                "flaw_id": "",
                "conflict_type": "evidence_conflict",
            }
            derived_conflicts.append(note)
            hypothesis = f"Claim {claim_id} may be overstated because conflicting evidence has appeared."
            if hypothesis not in hypotheses:
                hypotheses.append(hypothesis)
            derived_gaps = _set_evidence_gap_status(
                derived_gaps,
                claim_id=claim_id,
                status="converted",
                evidence_id=contradicting[0].get("evidence_id", ""),
                resolution="converted_to_evidence_conflict",
            )
            if current_status == "supported":
                desired_status = "uncertain"
        elif supporting:
            desired_status = "supported" if strong_support else "partially_supported"
            derived_gaps = _set_evidence_gap_status(
                derived_gaps,
                claim_id=claim_id,
                status="resolved",
                evidence_id=positive_ids[0] if positive_ids else "",
                resolution="supporting_evidence_bound",
            )
        else:
            gap_text = f"Claim {claim_id or claim.get('claim', '')[:40]} lacks grounded supporting evidence."
            gap_status = "not_assessable" if _claim_gap_should_be_not_assessable(claim) else "open"
            gap_resolution = (
                "diagnostic_or_salvaged_claim_without_verified_support"
                if gap_status == "not_assessable"
                else ""
            )
            derived_gaps = _merge_evidence_gaps(
                derived_gaps,
                [
                    {
                        "gap": gap_text,
                        "claim_id": claim_id,
                        "status": gap_status,
                        "source": "state_consistency",
                        "resolution": gap_resolution,
                    }
                ],
                max_items=20,
            )
            if current_status == "supported":
                desired_status = "uncertain"

        if guarded_status:
            desired_status = guarded_status
        if lock_status:
            desired_status = lock_status

        if desired_status != current_status:
            coerced_status, lifecycle_note = _coerce_status_transition("claim", claim_id, current_status, desired_status)
            if lifecycle_note is not None:
                derived_conflicts.append(lifecycle_note)
            if coerced_status != current_status:
                _append_revision_event(
                    derived_revisions,
                    "claim",
                    claim_id,
                    "status",
                    current_status,
                    coerced_status,
                    reason="consistency_reconciliation",
                )
                claim["status"] = coerced_status

    support_counts = _real_strong_support_counts(refreshed)
    for question in refreshed.get("unresolved_questions", []) or []:
        if not isinstance(question, dict):
            continue
        if str(question.get("status") or "open") != "open":
            continue
        related_claim_ids = [str(item) for item in (question.get("related_claim_ids") or []) if str(item)]
        if not any(support_counts.get(claim_id, 0) > 0 for claim_id in related_claim_ids):
            continue
        question_text = str(question.get("question") or "")
        if not _GENERIC_LACK_SUPPORT_PATTERN.search(question_text):
            continue
        old_status = question.get("status", "open")
        question["status"] = "resolved"
        question["resolved_by"] = "verified_real_claim_support"
        question["hygiene_status_reason"] = "state_consistency_resolved_by_real_claim_support"
        question_id = str(question.get("question_id") or question.get("question") or "unresolved_question")
        _append_revision_event(
            derived_revisions,
            "unresolved_question",
            question_id,
            "status",
            old_status,
            "resolved",
            reason="state_consistency_resolved_by_real_claim_support",
        )

    for flaw in flaws:
        flaw_id = flaw.get("flaw_id", "")
        if flaw.get("status") == "confirmed" and not flaw.get("evidence_ids"):
            _append_revision_event(
                derived_revisions,
                "flaw",
                flaw_id,
                "status",
                "confirmed",
                "candidate",
                reason="missing_anchor_evidence",
            )
            flaw["status"] = "candidate"
            derived_conflicts.append(
                {
                    "conflict_id": _slugify("conflict", f"{flaw_id}-missing-evidence-{len(derived_conflicts)+1}", len(derived_conflicts) + 1),
                    "note": f"Flaw {flaw_id} was downgraded because it lacks anchored evidence.",
                    "claim_id": (flaw.get("related_claim_ids") or [""])[0],
                    "evidence_id": "",
                    "flaw_id": flaw_id,
                    "conflict_type": "flaw_anchor_gap",
                }
            )
        if _generic_lack_support_flaw_conflicts_with_support(flaw, support_counts):
            old_status = flaw.get("status", "candidate")
            flaw["status"] = "downgraded"
            flaw["hygiene_status_reason"] = "evidence_aware_lack_flaw_conflicts_with_strong_support"
            _append_revision_event(
                derived_revisions,
                "flaw",
                flaw_id,
                "status",
                old_status,
                "downgraded",
                reason="evidence_aware_support_conflict",
            )
        if (
            flaw.get("status") in {"candidate", "confirmed"}
            and not _flaw_has_negative_grounding(flaw, refreshed)
            and _flaw_only_cites_supports(flaw, refreshed)
        ):
            old_status = flaw.get("status", "candidate")
            flaw["status"] = "downgraded"
            flaw["hygiene_status_reason"] = "support_only_flaw_lacks_verified_negative_evidence"
            _append_revision_event(
                derived_revisions,
                "flaw",
                flaw_id,
                "status",
                old_status,
                "downgraded",
                reason="support_only_flaw_without_verified_negative_grounding",
            )
            derived_conflicts.append(
                {
                    "conflict_id": _slugify("conflict", f"{flaw_id}-support-only-flaw-{len(derived_conflicts)+1}", len(derived_conflicts) + 1),
                    "note": f"Flaw {flaw_id} was downgraded because it only cites positive support evidence and lacks verified negative grounding.",
                    "claim_id": (flaw.get("related_claim_ids") or [""])[0],
                    "evidence_id": (flaw.get("evidence_ids") or [""])[0],
                    "flaw_id": flaw_id,
                    "conflict_type": "support_only_flaw_without_negative_grounding",
                }
            )
        if flaw.get("status") in {"candidate", "confirmed"} and not flaw.get("evidence_ids"):
            gap_text = f"Flaw {flaw_id or flaw.get('title', '')[:40]} lacks anchored evidence."
            derived_gaps = _merge_evidence_gaps(
                derived_gaps,
                [
                    {
                        "gap": gap_text,
                        "claim_id": (flaw.get("related_claim_ids") or [""])[0],
                        "flaw_id": flaw_id,
                        "status": "open",
                        "source": "state_consistency",
                    }
                ],
                max_items=20,
            )
        elif flaw.get("status") in {"candidate", "confirmed"} and flaw.get("evidence_ids"):
            derived_gaps = _set_evidence_gap_status(
                derived_gaps,
                flaw_id=flaw_id,
                status="resolved",
                evidence_id=(flaw.get("evidence_ids") or [""])[0],
                resolution="anchored_flaw_evidence_bound",
            )
        if flaw.get("status") in {"retracted", "downgraded"}:
            derived_gaps = _set_evidence_gap_status(
                derived_gaps,
                flaw_id=flaw_id,
                status="superseded",
                evidence_id=(flaw.get("evidence_ids") or [""])[0],
                resolution="flaw_inactive",
            )
            hypothesis = f"Flaw {flaw.get('flaw_id', '')} no longer provides a stable rejection signal."
            if hypothesis not in hypotheses:
                hypotheses.append(hypothesis)

    refreshed["evidence_gaps"] = _normalize_evidence_gaps(derived_gaps, max_items=10)
    refreshed["current_hypotheses"] = _normalize_list_of_strings(hypotheses, max_items=8, max_length=240)
    refreshed["conflict_notes"], added_conflicts = _merge_conflict_notes(
        refreshed.get("conflict_notes", []),
        _normalize_conflicts(derived_conflicts),
        max_items=12,
    )
    return refreshed, derived_revisions, added_conflicts


def _open_unresolved_questions(state: Dict[str, Any]) -> List[str]:
    results = []
    for item in state.get("unresolved_questions", []):
        if isinstance(item, dict):
            if item.get("status", "open") == "open":
                question_text = _normalize_text(item.get("question"), max_length=300)
                if question_text:
                    results.append(question_text)
        else:
            text = _normalize_text(item, max_length=300)
            if text:
                results.append(text)
    return results


_DECISION_HYGIENE_META_TERMS = (
    "fallback",
    "could not bind",
    "unbound",
    "verify whether",
    "locate a concrete",
    "check whether",
    "excerpt",
    "cuts off",
    "truncated",
    "incomplete abstract",
    "available text",
    "not yet visible",
    "please provide",
    "full text",
    "cannot be extracted",
    "unable to",
    "cannot verify",
    "lacks grounded",
    "lacks grounded supporting evidence",
    "ensure the evidence",
    "resolve the",
)


def _decision_real_claim_ids(state: Dict[str, Any]) -> set[str]:
    return {
        str(item.get("claim_id") or "")
        for item in state.get("claims", []) or []
        if item.get("claim_id") and _is_real_paper_claim_id(item.get("claim_id"), item.get("claim_kind"))
    }


def _is_real_bound_support(item: Dict[str, Any], real_claim_ids: set[str]) -> bool:
    claim_id = str(item.get("claim_id") or "")
    binding_status = str(item.get("binding_status") or "").strip()
    return (
        claim_id in real_claim_ids
        and binding_status in {"", "unchecked", "bound_real_claim"}
        and _has_final_support_strength(item)
        and item.get("stance") in {"supports", "partially_supports"}
        and _is_usable_support_grounding(item)
    )


def _context_verified_support_diagnostics(state: Dict[str, Any]) -> Dict[str, Any]:
    """Count verified context-claim support without promoting it to real support.

    Context-derived claims are useful diagnostics for zero-real coverage cases, but
    they must not be converted into real paper claims in the final decision view.
    """
    claims = state.get("claims", []) or []
    evidence_map = state.get("evidence_map", []) or []
    context_ids = {
        str(claim.get("claim_id") or "")
        for claim in claims
        if isinstance(claim, dict)
        and _classify_claim_kind(claim.get("claim_id"), claim.get("claim_kind")) == "context_synthesized"
    }
    counts_by_claim: Dict[str, int] = {}
    evidence_ids: List[str] = []
    for evidence in evidence_map:
        if not isinstance(evidence, dict):
            continue
        claim_id = str(evidence.get("claim_id") or "")
        if claim_id not in context_ids:
            continue
        if str(evidence.get("stance") or "") not in {"supports", "partially_supports"}:
            continue
        if _evidence_has_negative_intent(evidence) or _evidence_negative_locator_or_bucket_signal(evidence):
            continue
        if str(evidence.get("verified_grounding_label") or "") not in VERIFIED_PAPER_GROUNDED_LABELS:
            continue
        if str(evidence.get("semantic_grounding_label") or "") != "semantic_support_verified":
            continue
        if not _has_final_support_strength(evidence):
            continue
        counts_by_claim[claim_id] = counts_by_claim.get(claim_id, 0) + 1
        evidence_id = str(evidence.get("evidence_id") or "")
        if evidence_id:
            evidence_ids.append(evidence_id)
    return {
        "context_verified_support_total": sum(counts_by_claim.values()),
        "context_verified_support_by_claim": counts_by_claim,
        "context_verified_support_evidence_ids": evidence_ids[:20],
    }

def _decision_real_strong_support_counts(state: Dict[str, Any]) -> Dict[str, int]:
    real_claim_ids = _decision_real_claim_ids(state)
    counts: Dict[str, int] = {}
    for item in state.get("evidence_map", []) or []:
        if _is_real_bound_support(item, real_claim_ids):
            claim_id = str(item.get("claim_id") or "")
            counts[claim_id] = counts.get(claim_id, 0) + 1
    return counts


_SECTION_TO_DECISION_BUCKET = {
    "abstract": "abstract",
    "result": "result_or_experiment",
    "table_or_figure": "table_or_figure",
    "ablation": "ablation",
    "method": "method_or_approach",
    "theory_or_proof": "method_or_approach",
    "conclusion": "conclusion_or_discussion",
    "unknown": "other_or_unspecified",
}

_EMPIRICAL_DECISION_BUCKETS = frozenset({
    "result_or_experiment",
    "results",
    "result",
    "experiment",
    "ablation",
    "table_or_figure",
})

_METHOD_DECISION_BUCKETS = frozenset({
    "method_or_approach",
    "method_or_design",
    "method",
    "theory_or_proof",
    "proof",
    "theory",
})


def _decision_support_source_bucket(item: Dict[str, Any]) -> str:
    """Map an evidence item to a decision-layer source bucket.

    The single source of truth is :func:`support_quality.evidence_section_bucket`,
    which already prioritises specific source/evidence text (figure, table,
    ablation, etc.) over the looser ``support_source_bucket`` field returned by
    the agents.  Decision-layer naming (``result_or_experiment``,
    ``method_or_approach`` …) is preserved via :data:`_SECTION_TO_DECISION_BUCKET`
    so older callers and metric definitions continue to resolve.
    """
    from .support_quality import evidence_section_bucket

    section = evidence_section_bucket(item)
    return _SECTION_TO_DECISION_BUCKET.get(section, "other_or_unspecified")


_PRIMARY_CLAIM_MAX = 3


def _decision_primary_claim_ids(state: Dict[str, Any]) -> List[str]:
    """Return the IDs of *primary* (a.k.a. core) claims using a stable heuristic.

    HygieneV3 has no explicit ``priority`` field on a claim. As a transparent
    proxy, the first ``min(_PRIMARY_CLAIM_MAX, len(claims))`` real claims (in the
    order the agent emitted them; fallback claims excluded) are treated as
    *primary*. This matches reviewer practice — papers typically lead with the
    main contribution claim before diving into auxiliary observations.

    The proxy is intentionally simple so that ``primary_claim_support_coverage``
    is reproducible without any additional LLM call. A future cut can replace
    this with an explicit priority field; the metric name stays the same.
    """
    real_claim_ids = _decision_real_claim_ids(state)
    primary: List[str] = []
    for claim in state.get("claims", []) or []:
        if not isinstance(claim, dict):
            continue
        claim_id = str(claim.get("claim_id") or "")
        if not claim_id or claim_id not in real_claim_ids:
            continue
        primary.append(claim_id)
        if len(primary) >= _PRIMARY_CLAIM_MAX:
            break
    return primary


def _decision_real_strong_support_quality(state: Dict[str, Any]) -> Dict[str, Any]:
    from .support_quality import derive_claim_support_summary, derive_support_quality, independence_group_id

    real_claim_ids = _decision_real_claim_ids(state)
    primary_claim_ids = _decision_primary_claim_ids(state)
    primary_set = set(primary_claim_ids)
    real_claims = [
        claim
        for claim in state.get("claims", []) or []
        if isinstance(claim, dict) and str(claim.get("claim_id") or "") in real_claim_ids
    ]
    claim_by_id = {
        str(claim.get("claim_id") or ""): claim
        for claim in state.get("claims", []) or []
        if isinstance(claim, dict) and str(claim.get("claim_id") or "")
    }
    empirical_blocked_total = 0
    source_counts: Dict[str, int] = {}
    support_by_claim: Dict[str, int] = {}
    empirical_by_claim: Dict[str, int] = {}
    method_by_claim: Dict[str, int] = {}
    independence_groups_by_claim: Dict[str, set[str]] = {}
    independence_groups_total: set[str] = set()
    for item in state.get("evidence_map", []) or []:
        if not _is_real_bound_support(item, real_claim_ids):
            continue
        claim_id = str(item.get("claim_id") or "")
        support_by_claim[claim_id] = support_by_claim.get(claim_id, 0) + 1
        bucket = _decision_support_source_bucket(item)
        source_counts[bucket] = source_counts.get(bucket, 0) + 1
        if bucket in _EMPIRICAL_DECISION_BUCKETS:
            # R1: tighten empirical admission. A support in an empirical bucket
            # that is blocked (method-quote-for-empirical-claim / dataset-setup /
            # generic-evaluate-intent) does NOT count as empirical. It still
            # counts as real-strong support (admission not relaxed).
            _r1_quality = derive_support_quality(item, claim_by_id.get(claim_id))
            if _r1_quality.get("empirical_admission_block_reason"):
                empirical_blocked_total += 1
            else:
                empirical_by_claim[claim_id] = empirical_by_claim.get(claim_id, 0) + 1
        if bucket in _METHOD_DECISION_BUCKETS:
            method_by_claim[claim_id] = method_by_claim.get(claim_id, 0) + 1
        group_id = independence_group_id(item)
        independence_groups_by_claim.setdefault(claim_id, set()).add(group_id)
        independence_groups_total.add(group_id)
    non_abstract = sum(count for bucket, count in source_counts.items() if bucket != "abstract")
    empirical_total = sum(empirical_by_claim.values())
    method_total = sum(count for bucket, count in source_counts.items() if bucket in _METHOD_DECISION_BUCKETS)
    total_support = sum(support_by_claim.values())
    if total_support > 0 and support_by_claim:
        max_share = max(count / total_support for count in support_by_claim.values())
        top_claim_id = max(support_by_claim.items(), key=lambda pair: pair[1])[0]
    else:
        max_share = 0.0
        top_claim_id = ""
    primary_with_support = sum(
        1 for cid in primary_claim_ids if support_by_claim.get(cid, 0) > 0
    )
    primary_with_empirical = sum(
        1 for cid in primary_claim_ids if empirical_by_claim.get(cid, 0) > 0
    )
    primary_with_2plus_independent = sum(
        1
        for cid in primary_claim_ids
        if len(independence_groups_by_claim.get(cid, set())) >= 2
    )
    primary_total = len(primary_claim_ids)
    primary_coverage = (primary_with_support / primary_total) if primary_total else 0.0
    primary_empirical_coverage = (
        (primary_with_empirical / primary_total) if primary_total else 0.0
    )
    claim_support_summaries = [
        derive_claim_support_summary(claim, state.get("evidence_map", []) or [])
        for claim in real_claims
    ]
    depth_counts = {label: 0 for label in ("deep", "moderate", "shallow", "none")}
    depth_by_claim: Dict[str, str] = {}
    for summary in claim_support_summaries:
        depth = str(summary.get("claim_support_depth_label") or "none")
        if depth not in depth_counts:
            depth = "none"
        depth_counts[depth] += 1
        claim_id = str(summary.get("claim_id") or "")
        if claim_id:
            depth_by_claim[claim_id] = depth
    primary_depth_counts = {label: 0 for label in ("deep", "moderate", "shallow", "none")}
    for claim_id in primary_claim_ids:
        primary_depth_counts[depth_by_claim.get(claim_id, "none")] += 1
    return {
        "real_strong_support_source_counts": source_counts,
        "real_strong_support_by_claim": support_by_claim,
        "max_real_strong_support_per_claim": max(support_by_claim.values(), default=0),
        "claims_with_real_strong_support": sum(1 for count in support_by_claim.values() if count > 0),
        "claims_with_2plus_real_strong_support": sum(1 for count in support_by_claim.values() if count >= 2),
        "claims_with_2plus_independent_support": sum(
            1 for groups in independence_groups_by_claim.values() if len(groups) >= 2
        ),
        "claims_with_empirical_real_strong_support": sum(
            1 for count in empirical_by_claim.values() if count > 0
        ),
        "abstract_real_strong_support_count": source_counts.get("abstract", 0),
        "non_abstract_real_strong_support_count": non_abstract,
        "empirical_real_strong_support_count": empirical_total,
        "empirical_blocked_real_strong_count": empirical_blocked_total,
        "method_real_strong_support_count": method_total,
        "result_or_experiment_real_strong_support_count": source_counts.get("result_or_experiment", 0),
        "table_or_figure_real_strong_support_count": source_counts.get("table_or_figure", 0),
        "ablation_real_strong_support_count": source_counts.get("ablation", 0),
        "independent_support_group_total": len(independence_groups_total),
        "support_concentration_index": round(max_share, 4),
        "support_concentration_top_claim_id": top_claim_id,
        # P1.6 core / primary claim coverage (heuristic: first K real claims).
        "primary_claim_total": primary_total,
        "primary_claim_ids": primary_claim_ids,
        "primary_claims_with_real_strong_support": primary_with_support,
        "primary_claims_with_empirical_support": primary_with_empirical,
        "primary_claims_with_2plus_independent_support": primary_with_2plus_independent,
        "primary_claim_support_coverage": round(primary_coverage, 4),
        "primary_claim_empirical_coverage": round(primary_empirical_coverage, 4),
        "claim_support_summaries": claim_support_summaries,
        "claim_support_depth_by_claim": depth_by_claim,
        "claim_support_depth_counts": depth_counts,
        "primary_claim_support_depth_counts": primary_depth_counts,
        "claims_with_deep_support": depth_counts.get("deep", 0),
        "claims_with_moderate_or_deep_support": depth_counts.get("deep", 0) + depth_counts.get("moderate", 0),
        "claims_with_only_shallow_support": depth_counts.get("shallow", 0),
        "claims_without_real_strong_support": depth_counts.get("none", 0),
        "primary_claims_with_deep_support": primary_depth_counts.get("deep", 0),
        "primary_claims_with_moderate_or_deep_support": primary_depth_counts.get("deep", 0) + primary_depth_counts.get("moderate", 0),
    }


def _is_decision_meta_text(text: Any) -> bool:
    lowered = str(text or "").lower()
    return any(term in lowered for term in _DECISION_HYGIENE_META_TERMS)


_REPORT_META_LEAKAGE_TERMS = (
    "fallback",
    "raw output",
    "valid json",
    "not valid json",
    "parse failure",
    "json",
    "schema",
    "extraction was used",
    "parser failed",
    "parsing failed",
    "malformed output",
    "review halted",
    "excerpt",
    "snippet",
    "truncated",
    "cut off",
    "full text",
    "incomplete paper text",
    "missing abstract details",
    "final-view diagnostics",
    "health-check projection",
    "decision hygiene view",
    "binary final decision line",
    "accept_like",
    "reject_like",
    "borderline_positive",
    "borderline_insufficient",
    "not_assessable_uncertain",
    # P0-4: legacy process-language phrases that should never reach the
    # user-facing report.  These are matched case-insensitively in
    # `_is_report_meta_leakage_text`.
    "positive/support evidence was filtered",
    "negative evidence formation",
    "system did not see",
    "audit trace",
    "internal id",
    "internal ids",
    "binary_decision",
    "recommendation_view",
    "recovery operation",
    "recovery patch",
    "evidence was filtered",
    "copied negative_or_gap",
    "hard-negative evidence",
    "system salvage",
    "system recovery",
    "evidence-recovery-missing",
    "review diagnostic report",
    "summary of reviews",
    "key strengths",
    "key weaknesses",
)


_REPORT_INTERNAL_ID_REPLACEMENTS = (
    (re.compile(r"\bclaim-context-\d+\b", re.I), "context-synthesized claim"),
    (re.compile(r"\bclaim-fallback-[A-Za-z0-9_.:-]+\b", re.I), "fallback claim"),
    (re.compile(r"\bclaim-recovery-[A-Za-z0-9_.:-]+\b", re.I), "recovery marker claim"),
    (re.compile(r"\bevidence-recovery-missing-[A-Za-z0-9_.:-]+\b", re.I), "recovery evidence marker"),
    (re.compile(r"\bevidence-fallback-[A-Za-z0-9_.:-]+\b", re.I), "fallback evidence marker"),
    (re.compile(r"\bclaim-\d+(?:-[A-Za-z0-9_.:-]+)?\b", re.I), "paper claim"),
    (re.compile(r"\bevidence-\d+(?:-[A-Za-z0-9_.:-]+)?\b", re.I), "evidence anchor"),
    (re.compile(r"\bevidence-(?:negative|critique|recovery|fallback|general|placeholder)-[A-Za-z0-9_.:-]+\b", re.I), "evidence anchor"),
    (re.compile(r"\bflaw-fallback-[A-Za-z0-9_.:-]+\b", re.I), "fallback concern"),
    (re.compile(r"\bflaw-\d+(?:-[A-Za-z0-9_.:-]+)?\b", re.I), "review concern"),
    (re.compile(r"\bquote-\d+(?:-[A-Za-z0-9_.:-]+)?\b", re.I), "paper quote"),
)


_REPORT_PROCESS_SENTENCE_PATTERNS = (
    re.compile(r"No concrete evidence found for target claims?[^.!?]*(?:[.!?]|$)", re.I),
    re.compile(r"No concrete evidence found for target claim[^.!?]*(?:[.!?]|$)", re.I),
)


def _is_report_meta_leakage_text(text: Any) -> bool:
    lowered = str(text or "").lower()
    return any(term in lowered for term in _REPORT_META_LEAKAGE_TERMS)


def _redact_report_internal_ids(text: str) -> str:
    """Remove internal ReviewState ids from paper-facing report text.

    Audit artifacts keep raw ids. The user-facing diagnostic report should
    describe paper-side content without implementation identifiers such as
    ``claim-context-1`` or ``evidence-7``.
    """
    value = text or ""
    for pattern, replacement in _REPORT_INTERNAL_ID_REPLACEMENTS:
        value = pattern.sub(replacement, value)
    return re.sub(r"\s+", " ", value).strip()


def _strip_report_process_sentences(text: str) -> str:
    value = text or ""
    for pattern in _REPORT_PROCESS_SENTENCE_PATTERNS:
        value = pattern.sub(" ", value)
    return re.sub(r"\s+", " ", value).strip()


def _report_visible_text(text: Any, default: str = "", max_length: int = 800) -> str:
    value = _normalize_text(text, max_length=max_length)
    if not value or _is_report_meta_leakage_text(value):
        return default
    value = _strip_report_process_sentences(_redact_report_internal_ids(value))
    if not value or _is_report_meta_leakage_text(value):
        return default
    return value


def _filter_report_visible_items(items: Sequence[Any], max_items: int = 4) -> List[str]:
    visible: List[str] = []
    for item in items:
        text = _report_visible_text(item, max_length=300)
        if text:
            visible.append(text)
        if len(visible) >= max_items:
            break
    return visible


def _is_targetless_unresolved_question(question: Dict[str, Any]) -> bool:
    """Treat targetless open questions as review uncertainty, not paper defects."""
    related_claim_ids = question.get("related_claim_ids") or []
    related_evidence_ids = question.get("related_evidence_ids") or question.get("evidence_ids") or []
    related_flaw_ids = question.get("related_flaw_ids") or question.get("flaw_ids") or []
    return not related_claim_ids and not related_evidence_ids and not related_flaw_ids


def _is_fallback_or_meta_flaw(flaw: Dict[str, Any]) -> bool:
    """Return true for flaws that describe parser/system limits rather than paper defects."""
    flaw_id = str(flaw.get("flaw_id") or "")
    source = str(flaw.get("source") or "").lower()
    grounding = str(flaw.get("grounding_status") or "").lower()
    reason = str(flaw.get("hygiene_status_reason") or "").lower()
    text = " ".join(
        str(flaw.get(key) or "")
        for key in ("title", "description", "evidence", "rationale")
    )
    combined = f"{source} {grounding} {reason} {text}"
    return (
        flaw_id.startswith("flaw-fallback")
        or source in {"fallback", "fallback-extraction", "system_meta", "system-meta"}
        or grounding in {"fallback_unverified", "system_meta", "ungrounded_meta"}
        or "fallback" in combined.lower()
        or _is_decision_meta_text(combined)
    )


def _filter_decision_gaps(
    gaps: Sequence[Any],
    support_counts: Dict[str, int],
    negative_burden_claim_ids: Optional[set] = None,
    claim_lookup: Optional[Dict[str, Dict[str, Any]]] = None,
) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Route evidence gaps through the R6 lifecycle.

    Returns (kept, stale). ``kept`` are gaps that remain user-facing OPEN; ``stale``
    are gaps removed from the user-facing view (resolved / converted_to_concern /
    stale_or_internal). Every gap is tagged with an explicit ``gap_lifecycle_state``.
    Real open gaps are never deleted (they stay in ``kept``); evidence is never
    fabricated (only relabeled); an unresolved gap is never treated as negative
    evidence.
    """
    negative_burden_claim_ids = negative_burden_claim_ids or set()
    claim_lookup = claim_lookup or {}
    kept: List[Dict[str, Any]] = []
    stale: List[Dict[str, Any]] = []
    for gap in _normalize_evidence_gaps(gaps, max_items=20):
        text = _evidence_gap_text(gap)
        claim_id = str(gap.get("claim_id") or "")
        if gap.get("status") != "open":
            # Already-closed lifecycle rows are not stale burden.  Earlier
            # dashboards counted resolved gaps as `stale_gap_persistence`,
            # which made successful support-bound closure look like remaining
            # contamination.
            continue
        if "claim-fallback" in text:
            stale.append({**gap, "status": "superseded", "gap_lifecycle_state": "stale_or_internal", "resolution": gap.get("resolution") or "fallback_gap_not_paper_grounded"})
            continue
        claim_record = claim_lookup.get(claim_id) if claim_id else None
        if claim_record and _claim_gap_should_be_not_assessable(claim_record):
            stale.append({**gap, "status": "not_assessable", "gap_lifecycle_state": "assessment_limitation", "resolution": gap.get("resolution") or "diagnostic_or_salvaged_claim_without_verified_support"})
            continue
        if re.search(r"\bflaw\s+[A-Za-z0-9_.:-]+\s+lacks\s+anchored\s+evidence", text, re.I):
            stale.append({**gap, "status": "superseded", "gap_lifecycle_state": "stale_or_internal", "resolution": gap.get("resolution") or "flaw_anchor_gap_hidden_from_decision_view"})
            continue
        if any(count > 0 and (supported_claim_id == claim_id or supported_claim_id in text) for supported_claim_id, count in support_counts.items()):
            stale.append({**gap, "status": "resolved", "gap_lifecycle_state": "resolved", "resolution": gap.get("resolution") or "stale_resolved_by_support"})
            continue
        if claim_id and claim_id in negative_burden_claim_ids:
            # R6: a gap whose claim now carries a verified negative concern is
            # converted into that concern rather than left as an open gap.
            stale.append({**gap, "status": "converted", "gap_lifecycle_state": "converted_to_concern", "resolution": gap.get("resolution") or "converted_to_verified_negative_concern"})
            continue
        kept.append({**gap, "gap_lifecycle_state": "open"})
    return kept, stale


def _filter_decision_conflicts(conflicts: Sequence[Dict[str, Any]], support_counts: Dict[str, int]) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    kept: List[Dict[str, Any]] = []
    stale: List[Dict[str, Any]] = []
    for conflict in conflicts or []:
        conflict_type = str(conflict.get("conflict_type") or "")
        note = str(conflict.get("note") or "").lower()
        claim_id = str(conflict.get("claim_id") or "")
        evidence_id = str(conflict.get("evidence_id") or "")
        if conflict_type.startswith("fallback") or evidence_id.startswith("evidence-fallback"):
            stale.append(conflict)
            continue
        if claim_id and support_counts.get(claim_id, 0) > 0 and ("fallback" in note or "evidence-fallback" in note):
            stale.append(conflict)
            continue
        kept.append(conflict)
    return kept, stale


_LIMITATION_ACTIONABLE_RE = re.compile(
    r"\b(baseline|baselines|ablation|ablations|metric|metrics|benchmark|benchmarks|"
    r"experiment|experiments|evaluation|dataset|datasets|table|figure|comparison|"
    r"analysis|sensitivity|hyperparameter|hyper-parameter|reproducib|seed|"
    r"statistical|significance|standard deviation|confidence interval|computational cost|"
    r"runtime|throughput|fairness|robustness|coverage|methodology)\b",
    re.IGNORECASE,
)


def _classify_unresolved_limitation(question: Dict[str, Any], support_counts: Dict[str, int]) -> str:
    """Classify an unresolved question into one of four limitation buckets.

    Returns one of:

    - ``stale_limitation``: the question is already resolved by current support
      or meta-noise that no longer applies.
    - ``context_limitation``: the question reflects context/parser limits
      (truncation, missing excerpt, system-meta) rather than a paper concern.
    - ``actionable_limitation``: the question is tied to a real claim/evidence
      and references concrete artefacts the authors could address (baseline,
      ablation, metric, benchmark, …).
    - ``unresolved_diagnostic``: tied to claim/evidence/flaw but lacks an
      actionable hook; reviewers must decide whether to confirm manually.
    """
    if not isinstance(question, dict):
        return "context_limitation"
    text = str(question.get("question") or "")
    reason = str(question.get("hygiene_status_reason") or "")

    if reason in {
        "decision_view_resolved_by_real_claim_support",
        "decision_view_already_resolved",
    }:
        return "stale_limitation"
    claim_gap_match = re.search(r"claim\s+([A-Za-z0-9_.:-]+)\s+lacks\s+grounded", text, re.I)
    if claim_gap_match and support_counts.get(claim_gap_match.group(1), 0) > 0:
        return "stale_limitation"

    if reason in {"decision_view_meta_uncertainty", "decision_view_targetless_uncertainty"}:
        return "context_limitation"
    if _is_decision_meta_text(text):
        return "context_limitation"

    has_anchor = bool(
        question.get("related_claim_ids")
        or question.get("related_evidence_ids")
        or question.get("evidence_ids")
        or question.get("related_flaw_ids")
        or question.get("flaw_ids")
    )
    if not has_anchor and _is_targetless_unresolved_question(question):
        return "context_limitation"

    if _LIMITATION_ACTIONABLE_RE.search(text):
        return "actionable_limitation"
    if has_anchor:
        return "unresolved_diagnostic"
    return "context_limitation"


def _evidence_turn_index(evidence: Dict[str, Any]) -> int:
    raw_id = str(evidence.get("evidence_id") or "")
    match = re.search(r"(?:^|-)turn-(\d+)(?:-|$)", raw_id)
    if match:
        return _normalize_int(match.group(1), default=0)
    return _normalize_int(evidence.get("turn_id"), default=0)


def _claim_lookup_by_id(state: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    return {
        str(item.get("claim_id") or ""): item
        for item in state.get("claims", []) or []
        if isinstance(item, dict) and str(item.get("claim_id") or "")
    }


def _support_depth_label(evidence: Dict[str, Any]) -> str:
    try:
        from .support_quality import derive_support_quality

        return str(derive_support_quality(evidence).get("support_depth") or "")
    except Exception:
        return ""


def _support_survival_drop_reason(
    evidence: Dict[str, Any],
    *,
    real_claim_ids: set[str],
    claim_kind: str,
    included_in_final_view: bool,
    merged_into_state: bool = True,
    target_too_broad: bool = False,
    duplicate_quote: bool = False,
    open_gap_claim_ids: Optional[set[str]] = None,
) -> str:
    """Classify why a support did not survive into the final view.

    Mainline-Final-Integrated P1-2: this function no longer treats a
    coexisting verified negative concern as a blocker.  Positive and negative
    evidence on the same claim are surfaced as ``contested_support`` (see
    :func:`_build_support_survival_trace`) but the positive support stays in
    the final view.  ``overridden_by_negative_burden`` is therefore retired.
    """
    if included_in_final_view:
        return ""
    claim_id = str(evidence.get("claim_id") or "")
    if target_too_broad:
        return "target_too_broad"
    if not merged_into_state:
        return "hygiene_filtered"
    if not claim_id:
        return "not_bound_to_real_claim"
    if claim_kind and claim_kind != "paper_extracted":
        return "claim_not_paper_extracted"
    if claim_id not in real_claim_ids:
        return "not_real_claim"
    binding_status = str(evidence.get("binding_status") or "").strip()
    if binding_status not in {"", "unchecked", "bound_real_claim"}:
        return "not_bound_to_real_claim"
    label = str(evidence.get("verified_grounding_label") or "").strip()
    if label not in VERIFIED_PAPER_GROUNDED_LABELS:
        return "missing_verified_quote"
    semantic_label = str(evidence.get("semantic_grounding_label") or "").strip()
    if semantic_label != "semantic_support_verified":
        return "semantic_mismatch"
    if claim_id in (open_gap_claim_ids or set()):
        return "overridden_by_open_gap"
    depth = _support_depth_label(evidence)
    if depth in {"", "shallow", "none"}:
        return "weak_support_depth"
    if duplicate_quote:
        return "duplicate_quote"
    return "hygiene_filtered"


def _support_admission_tier(
    evidence: Dict[str, Any],
    *,
    real_claim_ids: set[str],
    claim_kind: str,
    included_in_final_view: bool,
) -> str:
    if included_in_final_view:
        return "verified_strong"
    claim_id = str(evidence.get("claim_id") or "")
    if not claim_id:
        return "not_verified"
    binding_status = str(evidence.get("binding_status") or "").strip()
    label = str(evidence.get("verified_grounding_label") or "").strip()
    semantic_label = str(evidence.get("semantic_grounding_label") or "").strip()
    if binding_status not in {"", "unchecked", "bound_real_claim"}:
        return "not_verified"
    if label not in VERIFIED_PAPER_GROUNDED_LABELS:
        return "not_verified"
    if semantic_label != "semantic_support_verified":
        return "not_verified"
    if claim_kind and claim_kind != "paper_extracted":
        return "verified_contextual"
    if claim_id not in real_claim_ids:
        return "verified_contextual"
    depth = _support_depth_label(evidence)
    declared_bucket = str(evidence.get("support_source_bucket") or "").strip()
    decision_bucket = _decision_support_source_bucket(evidence)
    if depth in {"", "shallow", "none"}:
        return "verified_contextual"
    if declared_bucket == "abstract" or decision_bucket == "abstract":
        return "verified_contextual"
    if str(evidence.get("strength") or "") == "medium":
        return "verified_moderate"
    return "verified_contextual"


def _support_admission_blocker(
    evidence: Dict[str, Any],
    *,
    final_drop_reason: str,
    support_admission_tier: str,
) -> str:
    if not final_drop_reason:
        return ""
    if final_drop_reason != "hygiene_filtered":
        return final_drop_reason
    strength = str(evidence.get("strength") or "")
    if strength != "strong":
        declared_bucket = str(evidence.get("support_source_bucket") or "").strip()
        decision_bucket = _decision_support_source_bucket(evidence)
        if declared_bucket == "abstract" or decision_bucket == "abstract":
            return "verified_abstract_support_not_final_strong"
        if support_admission_tier == "verified_moderate":
            return "verified_medium_support_not_final_strong"
        if support_admission_tier == "verified_contextual":
            return "verified_contextual_support_not_final_strong"
        return "not_final_strong_strength"
    return "hygiene_filtered"


def _negative_burden_claim_ids(state: Dict[str, Any]) -> set[str]:
    """Return the set of real-claim ids that carry a verified negative concern.

    Mainline-Final-Integrated P1-2: this set is the contested-support marker
    in :func:`_build_support_survival_trace`.  It no longer suppresses the
    positive support in :func:`_support_survival_drop_reason`; it is reported
    separately as ``contested_support`` so the positive evidence remains in
    the final view while reviewers see that a verified concern coexists on
    the same claim.
    """
    claim_ids: set[str] = set()
    for flaw in state.get("flaw_candidates", []) or []:
        if not isinstance(flaw, dict):
            continue
        if flaw.get("status") in {"downgraded", "retracted"}:
            continue
        if not _verified_negative_evidence_ids_for_flaw(flaw, state):
            continue
        for claim_id in flaw.get("related_claim_ids") or []:
            if claim_id:
                claim_ids.add(str(claim_id))
    return claim_ids


def _contested_support_claim_ids(state: Dict[str, Any]) -> set[str]:
    """Alias for :func:`_negative_burden_claim_ids` under the new name."""
    return _negative_burden_claim_ids(state)


def _build_support_survival_trace(state: Dict[str, Any]) -> List[Dict[str, Any]]:
    real_claim_ids = _decision_real_claim_ids(state)
    claims_by_id = _claim_lookup_by_id(state)
    open_gap_claim_ids = {
        str(gap.get("claim_id") or "")
        for gap in _open_evidence_gaps(state)
        if str(gap.get("claim_id") or "")
    }
    contested_claim_ids = _contested_support_claim_ids(state)
    quote_seen: set[str] = set()
    trace: List[Dict[str, Any]] = []
    for evidence in state.get("evidence_map", []) or []:
        if not isinstance(evidence, dict):
            continue
        stance = str(evidence.get("initial_stance") or evidence.get("stance") or "").strip()
        if stance not in {"supports", "partially_supports"}:
            continue
        claim_id = str(evidence.get("claim_id") or "")
        claim = claims_by_id.get(claim_id, {})
        claim_kind = _classify_claim_kind(claim_id, claim.get("claim_kind") if isinstance(claim, dict) else "")
        quote_value = str(evidence.get("quote_id") or evidence.get("raw_quote") or "")
        quote_key = f"{claim_id}|{quote_value}" if quote_value else ""
        duplicate_quote = bool(quote_key and quote_key in quote_seen)
        if quote_key:
            quote_seen.add(quote_key)
        included = _is_real_bound_support(evidence, real_claim_ids)
        final_depth = _support_depth_label(evidence)
        admission_tier = _support_admission_tier(
            evidence,
            real_claim_ids=real_claim_ids,
            claim_kind=claim_kind,
            included_in_final_view=included,
        )
        final_drop_reason = _support_survival_drop_reason(
            evidence,
            real_claim_ids=real_claim_ids,
            claim_kind=claim_kind,
            included_in_final_view=included,
            duplicate_quote=duplicate_quote,
            open_gap_claim_ids=open_gap_claim_ids,
        )
        contested_support = bool(claim_id and claim_id in contested_claim_ids)
        trace.append(
            {
                "support_id": str(evidence.get("support_id") or evidence.get("evidence_id") or ""),
                "evidence_id": str(evidence.get("evidence_id") or ""),
                "paper_id": str(state.get("paper_id") or ""),
                "turn_id": _evidence_turn_index(evidence),
                "claim_id": claim_id,
                "claim_kind": claim_kind,
                "quote_id": str(evidence.get("quote_id") or ""),
                "raw_quote": str(evidence.get("raw_quote") or ""),
                "agent_raw_quote": str(evidence.get("agent_raw_quote") or ""),
                "source_locator": str(evidence.get("source_locator") or ""),
                "locator_type": str(evidence.get("locator_type") or evidence.get("source_locator_type") or "generic"),
                "source_locator_type": str(evidence.get("source_locator_type") or evidence.get("locator_type") or "generic"),
                "locator_confidence": _normalize_float(
                    evidence.get("locator_confidence")
                    if evidence.get("locator_confidence") is not None
                    else evidence.get("source_locator_confidence"),
                    default=0.0,
                ),
                "source_locator_confidence": _normalize_float(
                    evidence.get("source_locator_confidence")
                    if evidence.get("source_locator_confidence") is not None
                    else evidence.get("locator_confidence"),
                    default=0.0,
                ),
                "source_locator_specific": _is_specific_locator(str(evidence.get("source_locator") or "")),
                "decision_support_source_bucket": _decision_support_source_bucket(evidence),
                "declared_support_source_bucket": str(evidence.get("support_source_bucket") or ""),
                "initial_strength": str(evidence.get("initial_strength") or evidence.get("strength") or ""),
                "initial_stance": str(evidence.get("initial_stance") or evidence.get("stance") or ""),
                "verified_grounding_label": str(evidence.get("verified_grounding_label") or ""),
                "verified_quote_match_type": str(evidence.get("verified_quote_match_type") or ""),
                "verified_claim_overlap_score": _verified_claim_overlap_score(evidence),
                "semantic_alignment_score": evidence.get("semantic_alignment_score", 0.0),
                "semantic_grounding_label": str(evidence.get("semantic_grounding_label") or ""),
                "quote_bank_claim_overlap_fallback_used": bool(evidence.get("quote_bank_claim_overlap_fallback_used")),
                "quote_bank_claim_overlap_fallback_quote_id": str(evidence.get("quote_bank_claim_overlap_fallback_quote_id") or ""),
                "quote_bank_claim_overlap_fallback_source_bucket": str(evidence.get("quote_bank_claim_overlap_fallback_source_bucket") or ""),
                "quote_bank_claim_overlap_fallback_score": _normalize_int(evidence.get("quote_bank_claim_overlap_fallback_score"), default=0, min_value=0),
                "semantic_weak_promotion_used": bool(evidence.get("semantic_weak_promotion_used")),
                "semantic_weak_promotion_reason": str(evidence.get("semantic_weak_promotion_reason") or ""),
                "strength_promotion_from_medium_used": bool(evidence.get("strength_promotion_from_medium_used")),
                "strength_promotion_reason": str(evidence.get("strength_promotion_reason") or ""),
                "verified_moderate_near_miss_promotion_path": _verified_moderate_near_miss_promotion_path(evidence),
                "final_strength_guard_downgrade_reason": str(evidence.get("final_strength_guard_downgrade_reason") or ""),
                "support_depth": final_depth,
                "merged_into_state": True,
                "merge_drop_reason": "",
                "final_strength": str(evidence.get("strength") or ""),
                "final_support_depth": final_depth,
                "support_admission_tier": admission_tier,
                "support_admission_blocker": _support_admission_blocker(
                    evidence,
                    final_drop_reason=final_drop_reason,
                    support_admission_tier=admission_tier,
                ),
                "contested_support": contested_support,
                "included_in_final_view": included,
                "final_drop_reason": final_drop_reason,
            }
        )
    return trace


def _support_survival_summary(trace: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    drop_by_reason: Dict[str, int] = {}
    drop_by_claim_kind: Dict[str, int] = {}
    semantic_verified = 0
    final_deep = 0
    fallback_used = 0
    fallback_real_strong = 0
    fallback_semantic_mismatch = 0
    semantic_weak_promotion_used = 0
    semantic_weak_promotion_real_strong = 0
    strength_promotion_from_medium = 0
    strength_promotion_from_medium_real_strong = 0
    near_miss_deep_moderate_support = 0
    near_miss_method_moderate_support = 0
    near_miss_specific_locator_moderate = 0
    near_miss_promoted_to_final = 0
    support_admission_tier_counts: Dict[str, int] = {}
    support_admission_blocker_counts: Dict[str, int] = {}
    verified_moderate_claim_ids: set[str] = set()
    included_claim_ids: set[str] = set()
    diagnostic_independent_groups_by_claim: Dict[str, set[str]] = {}
    medium_nonabstract_shadow_keys: set[tuple[str, str]] = set()
    abstract_shadow_keys: set[tuple[str, str]] = set()
    medium_deep_nonabstract_promotion_candidate = 0
    # Mainline-Final-Integrated P1-2: contested-support arbitration counters.
    contested_support_total = 0
    contested_final_support_total = 0
    contested_claim_ids: set[str] = set()
    contested_final_claim_ids: set[str] = set()
    # Mainline-Final-Integrated P0-1: final-strong guard observability.
    final_strong_guard_low_score_downgrade_count = 0
    final_strong_guard_negative_locator_downgrade_count = 0
    fallback_cases: List[Dict[str, Any]] = []
    semantic_weak_promotion_cases: List[Dict[str, Any]] = []
    for item in trace:
        claim_id = str(item.get("claim_id") or "")
        tier = str(item.get("support_admission_tier") or "unknown")
        support_admission_tier_counts[tier] = support_admission_tier_counts.get(tier, 0) + 1
        if tier == "verified_moderate" and claim_id:
            verified_moderate_claim_ids.add(claim_id)
        if claim_id and item.get("claim_kind") == "paper_extracted" and tier in {"verified_strong", "verified_moderate"}:
            locator_key = re.sub(
                r"\s+",
                " ",
                str(item.get("source_locator") or item.get("locator_type") or "").strip().lower(),
            )[:120]
            quote_key = str(item.get("quote_id") or item.get("raw_quote") or item.get("evidence_id") or "")[:240]
            role_key = str(item.get("decision_support_source_bucket") or item.get("support_depth") or "unknown")
            group_key = f"{claim_id}|{role_key}|{locator_key}|{quote_key}"
            diagnostic_independent_groups_by_claim.setdefault(claim_id, set()).add(group_key)
        if item.get("semantic_grounding_label") == "semantic_support_verified":
            semantic_verified += 1
        if item.get("included_in_final_view") and item.get("final_support_depth") == "deep":
            final_deep += 1
        if item.get("included_in_final_view") and claim_id:
            included_claim_ids.add(claim_id)
        if item.get("contested_support"):
            contested_support_total += 1
            if claim_id:
                contested_claim_ids.add(claim_id)
            if item.get("included_in_final_view"):
                contested_final_support_total += 1
                if claim_id:
                    contested_final_claim_ids.add(claim_id)
        guard_reason = str(item.get("final_strength_guard_downgrade_reason") or "")
        if guard_reason == "low_score_strong_support_downgrade":
            final_strong_guard_low_score_downgrade_count += 1
        elif guard_reason == "negative_locator_strong_support_downgrade":
            final_strong_guard_negative_locator_downgrade_count += 1
        if item.get("quote_bank_claim_overlap_fallback_used"):
            fallback_used += 1
            if item.get("included_in_final_view"):
                fallback_real_strong += 1
            if item.get("semantic_grounding_label") == "semantic_mismatch":
                fallback_semantic_mismatch += 1
            if len(fallback_cases) < 10:
                record = _support_observability_record(item)
                record["included_in_final_view"] = bool(item.get("included_in_final_view"))
                record["final_drop_reason"] = str(item.get("final_drop_reason") or "")
                fallback_cases.append(record)
        if item.get("semantic_weak_promotion_used"):
            semantic_weak_promotion_used += 1
            if item.get("included_in_final_view"):
                semantic_weak_promotion_real_strong += 1
            if len(semantic_weak_promotion_cases) < 10:
                record = _support_observability_record(item)
                record["included_in_final_view"] = bool(item.get("included_in_final_view"))
                record["final_drop_reason"] = str(item.get("final_drop_reason") or "")
                semantic_weak_promotion_cases.append(record)
        near_miss_path = str(item.get("verified_moderate_near_miss_promotion_path") or "")
        if near_miss_path == "near_miss_verified_deep_support":
            near_miss_deep_moderate_support += 1
        elif near_miss_path == "near_miss_verified_method_support":
            near_miss_method_moderate_support += 1
        if near_miss_path and item.get("source_locator_specific"):
            near_miss_specific_locator_moderate += 1
        if near_miss_path and item.get("included_in_final_view"):
            near_miss_promoted_to_final += 1
        if item.get("strength_promotion_from_medium_used"):
            strength_promotion_from_medium += 1
            if item.get("included_in_final_view"):
                strength_promotion_from_medium_real_strong += 1
        if not item.get("included_in_final_view"):
            reason = str(item.get("final_drop_reason") or "unknown")
            drop_by_reason[reason] = drop_by_reason.get(reason, 0) + 1
            claim_kind = str(item.get("claim_kind") or "unknown")
            drop_by_claim_kind[claim_kind] = drop_by_claim_kind.get(claim_kind, 0) + 1
            blocker = str(item.get("support_admission_blocker") or reason)
            support_admission_blocker_counts[blocker] = support_admission_blocker_counts.get(blocker, 0) + 1
            shadow_key = (
                claim_id,
                str(item.get("quote_id") or item.get("raw_quote") or item.get("evidence_id") or ""),
            )
            if blocker == "verified_medium_support_not_final_strong":
                medium_nonabstract_shadow_keys.add(shadow_key)
                declared_bucket = str(item.get("declared_support_source_bucket") or "")
                decision_bucket = str(item.get("decision_support_source_bucket") or "")
                overlap = _normalize_int(item.get("verified_claim_overlap_score"), default=0, min_value=0)
                grounding_label = str(item.get("verified_grounding_label") or "")
                semantic_label = str(item.get("semantic_grounding_label") or "")
                # P0-3: align shadow promotion candidates with the calibrated
                # promotion thresholds.  A medium support only counts as a
                # real shadow strong candidate when it would have been promoted
                # under the new score gate (otherwise it is just a
                # `verified_moderate` diagnostic).
                support_depth = str(item.get("support_depth") or "")
                depth_ok = support_depth in {"deep", "moderate"}
                bucket_ok = declared_bucket != "abstract" and decision_bucket != "abstract"
                grounding_ok = (
                    overlap > 0
                    or (
                        grounding_label == "paper_grounded_exact"
                        and semantic_label == "semantic_support_verified"
                    )
                )
                score_value = _normalize_float(
                    item.get("semantic_alignment_score"), default=0.0
                )
                if support_depth == "deep":
                    score_ok = score_value >= DEEP_PROMOTION_STRONG_MIN_SCORE
                elif support_depth == "moderate":
                    score_ok = score_value >= METHOD_PROMOTION_STRONG_MIN_SCORE
                else:
                    score_ok = False
                if depth_ok and bucket_ok and grounding_ok and score_ok:
                    medium_deep_nonabstract_promotion_candidate += 1
            if blocker == "verified_abstract_support_not_final_strong":
                abstract_shadow_keys.add(shadow_key)
    final_total = sum(1 for item in trace if item.get("included_in_final_view"))
    diagnostic_independent_group_total = sum(len(groups) for groups in diagnostic_independent_groups_by_claim.values())
    diagnostic_claims_with_2plus_independent = sum(
        1 for groups in diagnostic_independent_groups_by_claim.values() if len(groups) >= 2
    )
    medium_or_abstract_shadow_keys = medium_nonabstract_shadow_keys | abstract_shadow_keys
    medium_new_claim_ids = {
        claim_id
        for claim_id, _ in medium_nonabstract_shadow_keys
        if claim_id and claim_id not in included_claim_ids
    }
    medium_or_abstract_new_claim_ids = {
        claim_id
        for claim_id, _ in medium_or_abstract_shadow_keys
        if claim_id and claim_id not in included_claim_ids
    }
    merged_real_strong = sum(
        1
        for item in trace
        if item.get("initial_strength") == "strong" and item.get("claim_kind") == "paper_extracted"
    )
    # P0-3: cleaner tier-based aliases for downstream audits.  These do not
    # replace the legacy fields above (kept for backward compatibility); they
    # expose the same numbers under names that cannot be misread as
    # "shadow == final strong".
    strict_strong_support_total = support_admission_tier_counts.get("verified_strong", 0)
    moderate_diagnostic_support_total = support_admission_tier_counts.get("verified_moderate", 0)
    contextual_support_total = support_admission_tier_counts.get("verified_contextual", 0)
    not_verified_support_total = support_admission_tier_counts.get("not_verified", 0)
    shadow_candidate_support_total = medium_deep_nonabstract_promotion_candidate
    promotion_yield = (
        round(strength_promotion_from_medium_real_strong / strength_promotion_from_medium, 4)
        if strength_promotion_from_medium
        else 0.0
    )
    strong_survival_rate = (
        round(strict_strong_support_total / merged_real_strong, 4) if merged_real_strong else 0.0
    )
    final_support_yield = (
        round(
            (strict_strong_support_total + moderate_diagnostic_support_total) / len(trace),
            4,
        )
        if trace
        else 0.0
    )
    return {
        "merged_support_total": len(trace),
        "merged_real_strong_total": merged_real_strong,
        "semantic_verified_support_total": semantic_verified,
        "final_real_strong_total": final_total,
        "final_deep_support_total": final_deep,
        "merge_to_semantic_survival_rate": round(semantic_verified / len(trace), 4) if trace else 0.0,
        "semantic_to_final_survival_rate": round(final_total / semantic_verified, 4) if semantic_verified else 0.0,
        "merge_to_final_survival_rate": round(final_total / len(trace), 4) if trace else 0.0,
        "drop_by_final_reason": drop_by_reason,
        "drop_by_claim_kind": drop_by_claim_kind,
        "quote_bank_claim_overlap_fallback_used_count": fallback_used,
        "quote_bank_claim_overlap_fallback_real_strong_count": fallback_real_strong,
        "quote_bank_claim_overlap_fallback_semantic_mismatch_count": fallback_semantic_mismatch,
        "quote_bank_claim_overlap_fallback_case_sample": fallback_cases,
        "semantic_weak_promotion_used_count": semantic_weak_promotion_used,
        "semantic_weak_promotion_real_strong_count": semantic_weak_promotion_real_strong,
        "semantic_weak_promotion_case_sample": semantic_weak_promotion_cases,
        "strength_promotion_from_medium_count": strength_promotion_from_medium,
        "strength_promotion_from_medium_real_strong_count": strength_promotion_from_medium_real_strong,
        "near_miss_deep_moderate_support_count": near_miss_deep_moderate_support,
        "near_miss_method_moderate_support_count": near_miss_method_moderate_support,
        "near_miss_specific_locator_moderate_count": near_miss_specific_locator_moderate,
        "near_miss_promoted_to_final_count": near_miss_promoted_to_final,
        "support_admission_tier_counts": support_admission_tier_counts,
        "support_admission_blocker_counts": support_admission_blocker_counts,
        "final_verified_moderate_support_total": moderate_diagnostic_support_total,
        "claims_with_verified_moderate_support": len(verified_moderate_claim_ids),
        "diagnostic_independent_support_group_total": diagnostic_independent_group_total,
        "claims_with_2plus_independent_or_diagnostic_support": diagnostic_claims_with_2plus_independent,
        "verified_medium_support_blocked_count": support_admission_blocker_counts.get("verified_medium_support_not_final_strong", 0),
        "verified_abstract_support_blocked_count": support_admission_blocker_counts.get("verified_abstract_support_not_final_strong", 0),
        "medium_deep_nonabstract_promotion_candidate_count": medium_deep_nonabstract_promotion_candidate,
        "medium_nonabstract_shadow_additional_support_count": len(medium_nonabstract_shadow_keys),
        "medium_nonabstract_shadow_real_strong_total": final_total + len(medium_nonabstract_shadow_keys),
        "medium_nonabstract_shadow_newly_supported_claim_count": len(medium_new_claim_ids),
        "medium_or_abstract_shadow_additional_support_count": len(medium_or_abstract_shadow_keys),
        "medium_or_abstract_shadow_real_strong_total": final_total + len(medium_or_abstract_shadow_keys),
        "medium_or_abstract_shadow_newly_supported_claim_count": len(medium_or_abstract_new_claim_ids),
        # P0-3: cleaner tier-based aliases.
        "strict_strong_support_total": strict_strong_support_total,
        "moderate_diagnostic_support_total": moderate_diagnostic_support_total,
        "contextual_support_total": contextual_support_total,
        "not_verified_support_total": not_verified_support_total,
        "shadow_candidate_support_total": shadow_candidate_support_total,
        "promotion_yield": promotion_yield,
        "strong_survival_rate": strong_survival_rate,
        "final_support_yield": final_support_yield,
        # Mainline-Final-Integrated P1-2: contested-support arbitration counts.
        "contested_support_total": contested_support_total,
        "contested_final_support_total": contested_final_support_total,
        "claims_with_contested_support": len(contested_claim_ids),
        "claims_with_contested_final_support": len(contested_final_claim_ids),
        # Mainline-Final-Integrated P0-1: final-strong guard observability.
        "final_strong_guard_low_score_downgrade_count": final_strong_guard_low_score_downgrade_count,
        "final_strong_guard_negative_locator_downgrade_count": final_strong_guard_negative_locator_downgrade_count,
        "final_strong_guard_downgrade_total": (
            final_strong_guard_low_score_downgrade_count
            + final_strong_guard_negative_locator_downgrade_count
        ),
    }


def _contamination_record(
    target_type: str,
    target_id: str,
    error_type: str,
    affected_relation: str,
    evidence_context: str = "",
    confidence: float = 0.75,
    repairability: str = "review",
) -> Dict[str, Any]:
    target_id = str(target_id or "").strip()
    confidence = max(0.0, min(1.0, float(confidence or 0.0)))
    record = {
        "target_type": str(target_type or "state"),
        "target_id": target_id,
        "error_type": str(error_type or "unknown"),
        "affected_relation": str(affected_relation or ""),
        "evidence_context": _normalize_text(evidence_context, max_length=240),
        "localization_confidence": round(confidence, 3),
        "repairability": str(repairability or "review"),
    }
    record["target_gate_label"] = _recovery_target_gate_label(
        record["target_type"],
        record["target_id"],
        confidence=confidence,
        repairability=record["repairability"],
    )
    return record


def _recovery_target_gate_label(
    target_type: str,
    target_id: str,
    *,
    confidence: float = 1.0,
    repairability: str = "full",
) -> str:
    target_type = str(target_type or "").strip()
    target_id = str(target_id or "").strip()
    repairability = str(repairability or "").strip()
    if not target_id:
        return "empty_target"
    if target_id.startswith(
        (
            "claim-fallback",
            "claim-context",
            "claim-paper-fallback",
            "claim-paper-context",
            "flaw-fallback",
            "evidence-fallback",
        )
    ):
        return "fallback_target"
    if target_type not in {"claim", "flaw", "evidence_link", "gap", "final_item", "state"}:
        return "weak_target"
    if confidence < 0.55 or repairability in {"conservative", "review", "observe", "none"}:
        return "weak_target"
    return "real_target"


def _gate_counts(records: Sequence[Dict[str, Any]]) -> Dict[str, int]:
    counts: Counter[str] = Counter()
    for item in records or []:
        counts[str((item or {}).get("target_gate_label") or "unknown")] += 1
    return dict(counts)


def _type_counts(records: Sequence[Dict[str, Any]], key: str) -> Dict[str, int]:
    counts: Counter[str] = Counter()
    for item in records or []:
        value = str((item or {}).get(key) or "").strip()
        if value:
            counts[value] += 1
    return dict(counts)


def _state_contamination_targets(
    view: Dict[str, Any],
    support_counts: Dict[str, int],
    stale_gap_records: Sequence[Dict[str, Any]],
    negative_grounding_conflicts: Sequence[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    claims_by_id = _claim_lookup_by_id(view)
    real_claim_ids = _decision_real_claim_ids(view)

    if sum(int(count or 0) for count in (support_counts or {}).values()) == 0:
        verified_support_candidates = sum(
            1
            for evidence in view.get("evidence_map", []) or []
            if isinstance(evidence, dict)
            and str(evidence.get("stance") or "") in {"supports", "partially_supports"}
            and _is_verified_paper_grounded_evidence(evidence)
        )
        records.append(_contamination_record(
            "state",
            str(view.get("paper_id") or ""),
            "zero_real_support",
            "final_view.support_coverage",
            (
                f"No verified real-claim strong support survived final-view filtering; "
                f"{verified_support_candidates} verified support candidate(s) remain below final support threshold."
            ),
            confidence=0.75,
            repairability="review",
        ))

    for claim_id, count in sorted((support_counts or {}).items()):
        claim = claims_by_id.get(claim_id, {})
        status = str(claim.get("status") or "")
        reason = str(claim.get("hygiene_status_reason") or "")
        if (status in {"unsupported", "uncertain", "new", ""} or reason == "decision_view_unsupported_with_strong_support") and count > 0:
            records.append(_contamination_record(
                "claim",
                claim_id,
                "unsupported_with_strong_support",
                "claim.status_vs_verified_support",
                f"{count} verified support item(s) exist while status remains {claim.get('status', '') or 'unset'}",
                confidence=0.95,
                repairability="full",
            ))

    for gap in stale_gap_records or []:
        gap_id = str((gap or {}).get("gap_id") or "")
        text = str((gap or {}).get("text") or "")
        match = re.search(r"claim\s+([A-Za-z0-9_.:-]+)\s+lacks\s+grounded", text, re.I)
        target_id = match.group(1) if match else gap_id
        records.append(_contamination_record(
            "gap",
            target_id,
            "stale_gap_persistence",
            "gap.status_vs_verified_support",
            text,
            confidence=0.9 if match else 0.65,
            repairability="conservative",
        ))

    for conflict in negative_grounding_conflicts or []:
        records.append(_contamination_record(
            "flaw",
            str((conflict or {}).get("flaw_id") or ""),
            "evidence_misbinding",
            "flaw.negative_evidence_ids",
            str((conflict or {}).get("reason") or ""),
            confidence=0.9,
            repairability="conservative",
        ))

    for flaw in view.get("flaw_candidates", []) or []:
        if not isinstance(flaw, dict):
            continue
        flaw_id = str(flaw.get("flaw_id") or "")
        status = str(flaw.get("status") or "candidate")
        layer = str(flaw.get("final_view_flaw_layer") or "")
        hygiene_reason = str(flaw.get("hygiene_status_reason") or "")
        valid_negative_ids = _flaw_valid_negative_evidence_ids(flaw, view)
        actionable_negative_ids = _verified_actionable_negative_evidence_ids_for_flaw(flaw, view)
        if status in {"candidate", "confirmed"} and _is_fallback_or_meta_flaw(flaw):
            records.append(_contamination_record(
                "flaw",
                flaw_id,
                "meta_leakage",
                "flaw.source_stage",
                str(flaw.get("flaw") or flaw.get("description") or ""),
                confidence=0.9,
                repairability="conservative",
            ))
        if (status == "confirmed" or hygiene_reason == "decision_view_ungrounded_or_fallback_flaw") and not valid_negative_ids:
            records.append(_contamination_record(
                "flaw",
                flaw_id,
                "unsupported_flaw_escalation",
                "flaw.status_vs_negative_evidence",
                str(flaw.get("flaw") or flaw.get("description") or ""),
                confidence=0.85,
                repairability="full",
            ))
        severity = str(flaw.get("severity") or "").strip().lower()
        minor_assessment_limitation = (
            layer == "assessment_limitation"
            and status == "candidate"
            and severity in {"", "minor", "low"}
        )
        if (
            valid_negative_ids
            and not actionable_negative_ids
            and status in {"confirmed", "candidate"}
            and not minor_assessment_limitation
        ):
            records.append(_contamination_record(
                "flaw",
                flaw_id,
                "negative_evidence_overclaim",
                "flaw.severity_vs_negative_type",
                str(flaw.get("flaw") or flaw.get("description") or ""),
                confidence=0.8,
                repairability="conservative",
            ))
        if status in {"downgraded", "retracted"} and layer in {"grounded_weakness", "verified_potential_concern"}:
            records.append(_contamination_record(
                "flaw",
                flaw_id,
                "stale_flaw_persistence",
                "flaw.status_vs_final_view_layer",
                str(flaw.get("flaw") or flaw.get("description") or ""),
                confidence=0.9,
                repairability="full",
            ))

    for evidence in view.get("evidence_map", []) or []:
        if not isinstance(evidence, dict):
            continue
        claim_id = str(evidence.get("claim_id") or "")
        if claim_id and claim_id not in real_claim_ids and _is_real_support_evidence(evidence):
            records.append(_contamination_record(
                "evidence_link",
                str(evidence.get("evidence_id") or ""),
                "evidence_misbinding",
                "evidence.claim_id",
                f"support evidence is bound to non-real claim {claim_id}",
                confidence=0.95,
                repairability="full",
            ))

    latest_patch_log = view.get("_latest_patch_log", {}) if isinstance(view, dict) else {}
    if latest_patch_log.get("negative_recovery_commit"):
        records.append(_contamination_record(
            "state",
            str(latest_patch_log.get("recovery_target_id") or ""),
            "harmful_recovery_risk",
            "recovery_patch.state_delta",
            str(latest_patch_log.get("recovery_failure_message") or ""),
            confidence=0.8,
            repairability="review",
        ))

    return records[:80]


def build_decision_hygiene_view(state: Dict[str, Any]) -> Dict[str, Any]:
    """Build a final-decision/report view without mutating live ReviewState.

    This view removes stale fallback/meta negatives and keeps only real-claim
    bound strong evidence as accept-level support. It must not be used during
    turn-by-turn manager routing because doing so changes the evidence formation
    trajectory.

    The view is **idempotent**: if ``state`` already exposes a
    ``decision_hygiene`` dictionary populated by an earlier call, the function
    returns ``state`` untouched.  Composing the view multiple times previously
    silently shifted runtime metrics (e.g. ``targetless_unresolved_deferred_count``
    became 0 on the second pass because deferred questions are no longer
    ``open``), which made the renderer's recommendation label drift away from
    the canonical runtime view.
    """
    if isinstance(state, dict) and isinstance(state.get("decision_hygiene"), dict) and state.get("decision_hygiene"):
        return state

    view = copy.deepcopy(state or {})
    view["evidence_map"] = _verify_evidence_items_for_state(view, view.get("evidence_map", []) or [])
    context_support_diagnostics = _context_verified_support_diagnostics(view)
    support_counts = _decision_real_strong_support_counts(view)
    _r6_negative_burden_claim_ids = _negative_burden_claim_ids(view)
    claim_lookup_for_gaps = {
        str(item.get("claim_id") or ""): item
        for item in view.get("claims", []) or []
        if isinstance(item, dict) and str(item.get("claim_id") or "")
    }
    kept_gaps, stale_gaps = _filter_decision_gaps(
        view.get("evidence_gaps", []),
        support_counts,
        _r6_negative_burden_claim_ids,
        claim_lookup_for_gaps,
    )
    kept_conflicts, stale_conflicts = _filter_decision_conflicts(view.get("conflict_notes", []), support_counts)
    view["evidence_gaps"] = _normalize_evidence_gaps(kept_gaps, max_items=10)
    view["conflict_notes"] = kept_conflicts[:12]
    negative_evidence_ids = {
        str(item.get("evidence_id") or "")
        for item in view.get("evidence_map", []) or []
        if _is_grounded_paper_negative_evidence_record(item, view) and str(item.get("evidence_id") or "")
    }

    # Track which evidence_gap rows would have been kept versus marked stale by
    # the view; downstream renderers use the breakdown to expose
    # ``stale_resolved_by_support`` to humans without mutating live state.
    stale_gap_records = [
        {
            "gap_id": str(item.get("gap_id") or ""),
            "text": _evidence_gap_text(item),
            "status": str(item.get("status") or ""),
            "classification": str(item.get("resolution") or "stale_resolved_by_support"),
        }
        for item in stale_gaps
    ]

    # View-only claim-status reconciliation: when a real claim already carries
    # bound real-claim strong support evidence, the decision view should not
    # still mark it as ``unsupported`` / ``uncertain`` / ``new``. Leaving the
    # contradictory status in place lets the renderer emit reports that say
    # "no grounded support" while the evidence map shows multiple strong
    # supports. This reconciliation is applied to the local ``view`` deepcopy
    # only — the live ``state`` is not mutated, so runtime status lifecycle
    # and recovery logic are unaffected.
    reconciled_claim_ids: List[str] = []
    for claim in view.get("claims", []) or []:
        if not isinstance(claim, dict):
            continue
        claim_id = str(claim.get("claim_id") or "")
        if not claim_id:
            continue
        if support_counts.get(claim_id, 0) <= 0:
            continue
        current_status = str(claim.get("status") or "")
        if current_status not in {"unsupported", "uncertain", "new", ""}:
            continue
        claim["status"] = "supported"
        claim["hygiene_status_reason"] = "decision_view_unsupported_with_strong_support"
        reconciled_claim_ids.append(claim_id)

    deferred_questions = []
    targetless_questions = []
    targetless_questions_raw = []
    limitation_classifications: Dict[str, int] = {
        "actionable_limitation": 0,
        "context_limitation": 0,
        "unresolved_diagnostic": 0,
        "stale_limitation": 0,
    }
    classified_questions: List[Dict[str, Any]] = []
    claim_gap_pattern = re.compile(r"claim\s+([A-Za-z0-9_.:-]+)\s+lacks\s+grounded", re.I)
    for question in view.get("unresolved_questions", []) or []:
        if not isinstance(question, dict):
            continue
        question_text = str(question.get("question", ""))
        if question.get("status", "open") == "open":
            reason = ""
            match = claim_gap_pattern.search(question_text)
            if match and support_counts.get(match.group(1), 0) > 0:
                reason = "decision_view_resolved_by_real_claim_support"
            elif _is_decision_meta_text(question_text):
                reason = "decision_view_meta_uncertainty"
            elif _is_targetless_unresolved_question(question):
                reason = "decision_view_targetless_uncertainty"
            if reason:
                question["status"] = "deferred"
                question["hygiene_status_reason"] = reason
                if reason == "decision_view_targetless_uncertainty":
                    question.setdefault("target_type", "state")
                    question.setdefault("target_classification", "context_limitation")
                    question["final_diagnostic_visible"] = False
                question_ref = question.get("question_id") or question.get("question", "")
                deferred_questions.append(question_ref)
                if reason == "decision_view_targetless_uncertainty":
                    targetless_questions_raw.append(question_ref)
                if (
                    reason == "decision_view_targetless_uncertainty"
                    and not question.get("target_type")
                    and not question.get("target_classification")
                ):
                    targetless_questions.append(question_ref)
        classification = _classify_unresolved_limitation(question, support_counts)
        question["limitation_classification"] = classification
        limitation_classifications[classification] = limitation_classifications.get(classification, 0) + 1
        classified_questions.append(question)
    view["unresolved_questions"] = classified_questions

    downgraded_flaws = []
    support_only_flaws: List[str] = []
    stance_inferred_flaws: List[str] = []
    linked_negative_evidence_ids: set[str] = set()
    negative_grounding_conflicts: List[Dict[str, Any]] = []
    flaw_layer_counts: Dict[str, int] = {
        "grounded_weakness": 0,
        "verified_potential_concern": 0,
        "potential_concern": 0,
        "assessment_limitation": 0,
    }
    verified_negative_flaw_ids: List[str] = []
    actionable_negative_flaw_ids: List[str] = []
    verified_potential_concern_ids: List[str] = []
    negative_flaw_not_upgraded_reasons: Counter[str] = Counter()
    limitation_negative_flaw_ids: List[str] = []
    negative_evidence_type_counts: Counter[str] = Counter()
    for flaw in view.get("flaw_candidates", []) or []:
        if not isinstance(flaw, dict):
            continue

        # View-only stance-based negative grounding inference.  If the agent
        # already cited evidence whose ``stance`` is contradicts/refutes/
        # weakens/missing but forgot to echo it into ``negative_evidence_ids``,
        # derive the anchor list from the state itself.  Live state is not
        # touched — only this deepcopy view.  The explicit field takes
        # precedence and is never overwritten.
        if not _flaw_explicit_negative_evidence_ids(flaw):
            inferred_ids = _stance_based_negative_evidence_ids(flaw, view)
            if inferred_ids:
                flaw["negative_evidence_ids"] = inferred_ids
                flaw["hygiene_negative_grounding_source"] = "auto_stance_inference"
                stance_inferred_flaws.append(str(flaw.get("flaw_id") or ""))
        conflicts = _flaw_negative_grounding_conflicts(flaw, view)
        if conflicts:
            flaw["hygiene_negative_grounding_conflicts"] = conflicts
            negative_grounding_conflicts.extend(conflicts)
        for eid in _flaw_valid_negative_evidence_ids(flaw, view):
            if eid in negative_evidence_ids:
                linked_negative_evidence_ids.add(eid)

        # Negative-evidence-only flaws are valid anchored critique candidates.
        # Earlier logic only looked at ``evidence_ids`` and downgraded flaws
        # that correctly stored anchors in ``negative_evidence_ids`` before
        # they could enter the potential-concern lifecycle.
        pre_verified_negative_ids = _verified_negative_evidence_ids_for_flaw(flaw, view)
        has_evidence = bool(flaw.get("evidence_ids") or _flaw_valid_negative_evidence_ids(flaw, view))
        evidence_conflict = _generic_lack_support_flaw_conflicts_with_support(flaw, support_counts)
        original_status = flaw.get("status", "candidate")
        if (
            original_status in {"candidate", "confirmed"}
            and not pre_verified_negative_ids
            and (not has_evidence or _is_fallback_or_meta_flaw(flaw) or evidence_conflict)
        ):
            flaw["status"] = "downgraded"
            flaw["hygiene_status_reason"] = "decision_view_evidence_aware_lack_flaw_conflict" if evidence_conflict else "decision_view_ungrounded_or_fallback_flaw"
            downgraded_flaws.append(str(flaw.get("flaw_id") or ""))
        if (
            flaw.get("status") not in {"downgraded", "retracted"}
            and not _flaw_has_negative_grounding(flaw, view)
            and _flaw_only_cites_supports(flaw, view)
        ):
            support_only_flaws.append(str(flaw.get("flaw_id") or ""))

        verified_negative_ids = _verified_negative_evidence_ids_for_flaw(flaw, view)
        if verified_negative_ids:
            flaw["verified_negative_evidence_ids"] = verified_negative_ids
            verified_negative_flaw_ids.append(str(flaw.get("flaw_id") or ""))
            flaw_type_counts = _negative_evidence_type_counts_for_flaw(flaw, view)
            if flaw_type_counts:
                flaw["negative_evidence_type_counts"] = flaw_type_counts
                negative_evidence_type_counts.update(flaw_type_counts)
            if _verified_actionable_negative_evidence_ids_for_flaw(flaw, view):
                actionable_negative_flaw_ids.append(str(flaw.get("flaw_id") or ""))
                if str(flaw.get("status") or "candidate") != "confirmed":
                    flaw_id = str(flaw.get("flaw_id") or "")
                    if flaw_id:
                        verified_potential_concern_ids.append(flaw_id)
                    if any(neg_type in {"scope_limitation", "missing_ablation", "missing_baseline", "insufficient_evaluation", "reproducibility_gap"} for neg_type in flaw_type_counts):
                        reason = "limitation_type_stays_potential_concern"
                    elif any(neg_type in {"direct_contradiction", "negative_result"} for neg_type in flaw_type_counts):
                        reason = "not_confirmed_stays_potential_concern"
                    else:
                        reason = "verified_candidate_stays_potential_concern"
                    flaw["negative_flaw_not_upgraded_reason"] = reason
                    negative_flaw_not_upgraded_reasons[reason] += 1
            elif any(neg_type in LIMITATION_NEGATIVE_EVIDENCE_TYPES for neg_type in flaw_type_counts):
                limitation_negative_flaw_ids.append(str(flaw.get("flaw_id") or ""))
        layer = _classify_flaw_final_view_layer(flaw, view)
        flaw["final_view_flaw_layer"] = layer
        flaw_layer_counts[layer] = flaw_layer_counts.get(layer, 0) + 1

    support_quality = _decision_real_strong_support_quality(view)
    support_survival_trace = _build_support_survival_trace(view)
    support_survival_summary = _support_survival_summary(support_survival_trace)
    actionable_lim = limitation_classifications["actionable_limitation"]
    context_lim = limitation_classifications["context_limitation"]
    unresolved_diag_lim = limitation_classifications["unresolved_diagnostic"]
    stale_lim = limitation_classifications["stale_limitation"]
    total_lim = actionable_lim + context_lim + unresolved_diag_lim + stale_lim
    actionable_ratio = (actionable_lim / total_lim) if total_lim else 0.0
    diagnostic_useful_ratio = (
        ((actionable_lim + unresolved_diag_lim) / total_lim) if total_lim else 0.0
    )
    claim_coverage = claim_coverage_summary(view)
    contamination_targets = _state_contamination_targets(
        view,
        support_counts,
        stale_gap_records,
        negative_grounding_conflicts,
    )
    contamination_type_counts = _type_counts(contamination_targets, "error_type")
    contamination_gate_counts = _gate_counts(contamination_targets)
    repairable_target_count = sum(
        1
        for item in contamination_targets
        if str(item.get("target_gate_label") or "") == "real_target"
    )
    conservative_target_count = sum(
        1
        for item in contamination_targets
        if str(item.get("target_gate_label") or "") == "weak_target"
    )
    view["decision_hygiene"] = {
        "real_strong_support_total": sum(support_counts.values()),
        "real_strong_support_by_claim": support_counts,
        **context_support_diagnostics,
        **support_quality,
        "support_survival_trace": support_survival_trace,
        "support_survival_summary": support_survival_summary,
        "quote_bank_claim_overlap_fallback_used_count": support_survival_summary.get("quote_bank_claim_overlap_fallback_used_count", 0),
        "quote_bank_claim_overlap_fallback_real_strong_count": support_survival_summary.get("quote_bank_claim_overlap_fallback_real_strong_count", 0),
        "quote_bank_claim_overlap_fallback_semantic_mismatch_count": support_survival_summary.get("quote_bank_claim_overlap_fallback_semantic_mismatch_count", 0),
        "quote_bank_claim_overlap_fallback_case_sample": support_survival_summary.get("quote_bank_claim_overlap_fallback_case_sample", []),
        "semantic_weak_promotion_used_count": support_survival_summary.get("semantic_weak_promotion_used_count", 0),
        "semantic_weak_promotion_real_strong_count": support_survival_summary.get("semantic_weak_promotion_real_strong_count", 0),
        "semantic_weak_promotion_case_sample": support_survival_summary.get("semantic_weak_promotion_case_sample", []),
        "strength_promotion_from_medium_count": support_survival_summary.get("strength_promotion_from_medium_count", 0),
        "strength_promotion_from_medium_real_strong_count": support_survival_summary.get("strength_promotion_from_medium_real_strong_count", 0),
        "near_miss_deep_moderate_support_count": support_survival_summary.get("near_miss_deep_moderate_support_count", 0),
        "near_miss_method_moderate_support_count": support_survival_summary.get("near_miss_method_moderate_support_count", 0),
        "near_miss_specific_locator_moderate_count": support_survival_summary.get("near_miss_specific_locator_moderate_count", 0),
        "near_miss_promoted_to_final_count": support_survival_summary.get("near_miss_promoted_to_final_count", 0),
        "support_admission_tier_counts": support_survival_summary.get("support_admission_tier_counts", {}),
        "support_admission_blocker_counts": support_survival_summary.get("support_admission_blocker_counts", {}),
        "final_verified_moderate_support_total": support_survival_summary.get("final_verified_moderate_support_total", 0),
        "claims_with_verified_moderate_support": support_survival_summary.get("claims_with_verified_moderate_support", 0),
        "diagnostic_independent_support_group_total": support_survival_summary.get("diagnostic_independent_support_group_total", 0),
        "claims_with_2plus_independent_or_diagnostic_support": support_survival_summary.get("claims_with_2plus_independent_or_diagnostic_support", 0),
        "verified_medium_support_blocked_count": support_survival_summary.get("verified_medium_support_blocked_count", 0),
        "verified_abstract_support_blocked_count": support_survival_summary.get("verified_abstract_support_blocked_count", 0),
        "medium_deep_nonabstract_promotion_candidate_count": support_survival_summary.get("medium_deep_nonabstract_promotion_candidate_count", 0),
        "medium_nonabstract_shadow_additional_support_count": support_survival_summary.get("medium_nonabstract_shadow_additional_support_count", 0),
        "medium_nonabstract_shadow_real_strong_total": support_survival_summary.get("medium_nonabstract_shadow_real_strong_total", 0),
        "medium_nonabstract_shadow_newly_supported_claim_count": support_survival_summary.get("medium_nonabstract_shadow_newly_supported_claim_count", 0),
        "medium_or_abstract_shadow_additional_support_count": support_survival_summary.get("medium_or_abstract_shadow_additional_support_count", 0),
        "medium_or_abstract_shadow_real_strong_total": support_survival_summary.get("medium_or_abstract_shadow_real_strong_total", 0),
        "medium_or_abstract_shadow_newly_supported_claim_count": support_survival_summary.get("medium_or_abstract_shadow_newly_supported_claim_count", 0),
        # P0-3: cleaner tier-based aliases.
        "strict_strong_support_total": support_survival_summary.get("strict_strong_support_total", 0),
        "moderate_diagnostic_support_total": support_survival_summary.get("moderate_diagnostic_support_total", 0),
        "contextual_support_total": support_survival_summary.get("contextual_support_total", 0),
        "not_verified_support_total": support_survival_summary.get("not_verified_support_total", 0),
        "shadow_candidate_support_total": support_survival_summary.get("shadow_candidate_support_total", 0),
        "promotion_yield": support_survival_summary.get("promotion_yield", 0.0),
        "strong_survival_rate": support_survival_summary.get("strong_survival_rate", 0.0),
        "final_support_yield": support_survival_summary.get("final_support_yield", 0.0),
        # Mainline-Final-Integrated P1-2 + P0-1 top-level metrics.
        "contested_support_total": support_survival_summary.get("contested_support_total", 0),
        "contested_final_support_total": support_survival_summary.get("contested_final_support_total", 0),
        "claims_with_contested_support": support_survival_summary.get("claims_with_contested_support", 0),
        "claims_with_contested_final_support": support_survival_summary.get("claims_with_contested_final_support", 0),
        "final_strong_guard_low_score_downgrade_count": support_survival_summary.get("final_strong_guard_low_score_downgrade_count", 0),
        "final_strong_guard_negative_locator_downgrade_count": support_survival_summary.get("final_strong_guard_negative_locator_downgrade_count", 0),
        "final_strong_guard_downgrade_total": support_survival_summary.get("final_strong_guard_downgrade_total", 0),
        "open_evidence_gap_count": len(kept_gaps),
        "stale_evidence_gap_count": len(stale_gaps),
        "stale_evidence_gap_records": stale_gap_records,
        "deferred_context_or_meta_unresolved_count": len(deferred_questions) - len(targetless_questions),
        "deferred_unresolved_count": len(deferred_questions),
        "targetless_unresolved_deferred_count": len(targetless_questions),
        "targetless_unresolved_deferred_raw_count": len(targetless_questions_raw),
        "open_conflict_count": len(kept_conflicts),
        "stale_conflict_count": len(stale_conflicts),
        "downgraded_flaw_count": len(downgraded_flaws),
        "claims_reconciled_with_strong_support_count": len(reconciled_claim_ids),
        "support_only_flaw_filtered_count": len(support_only_flaws),
        "candidate_to_potential_concern_downgrade_count": len(downgraded_flaws),
        "flaw_layer_counts": flaw_layer_counts,
        "grounded_weakness_count": flaw_layer_counts.get("grounded_weakness", 0),
        "verified_potential_concern_count": len(set(fid for fid in verified_potential_concern_ids if fid)),
        "potential_concern_count": flaw_layer_counts.get("potential_concern", 0),
        "assessment_limitation_flaw_count": flaw_layer_counts.get("assessment_limitation", 0),
        "verified_negative_flaw_count": len(set(fid for fid in verified_negative_flaw_ids if fid)),
        "verified_actionable_negative_flaw_count": len(set(fid for fid in actionable_negative_flaw_ids if fid)),
        "verified_limitation_negative_flaw_count": len(set(fid for fid in limitation_negative_flaw_ids if fid)),
        "negative_evidence_type_counts": dict(negative_evidence_type_counts),
        "negative_flaw_not_upgraded_reason_counts": dict(negative_flaw_not_upgraded_reasons),
        "state_contamination_count": len(contamination_targets),
        "state_contamination_count_legacy": len(contamination_targets),
        "harmful_state_contamination_count": 0,
        "repairable_state_warning_count": repairable_target_count,
        "conservative_state_warning_count": conservative_target_count,
        "state_hygiene_warning_count": conservative_target_count,
        "weak_target_warning_count": conservative_target_count,
        "state_contamination_targets": contamination_targets,
        "state_contamination_type_counts": contamination_type_counts,
        "recovery_target_gate_counts": contamination_gate_counts,
        "repairable_contamination_target_count": repairable_target_count,
        "conservative_contamination_target_count": conservative_target_count,
        "blocked_fallback_contamination_target_count": contamination_gate_counts.get("fallback_target", 0),
        "blocked_empty_contamination_target_count": contamination_gate_counts.get("empty_target", 0),
        "negative_evidence_candidate_count": len(negative_evidence_ids),
        "negative_evidence_linked_to_flaw_count": len(linked_negative_evidence_ids),
        "negative_evidence_unlinked_to_flaw_count": max(0, len(negative_evidence_ids) - len(linked_negative_evidence_ids)),
        "negative_evidence_binding_retry_candidate_count": max(0, len(negative_evidence_ids) - len(linked_negative_evidence_ids)),
        "negative_grounding_conflict_count": len(negative_grounding_conflicts),
        "invalid_negative_evidence_id_count": len(negative_grounding_conflicts),
        "invalid_negative_evidence_id_count_legacy": len(negative_grounding_conflicts),
        "negative_semantic_anchor_conflict_count": len(negative_grounding_conflicts),
        "generic_gap_semantic_rejected_count": len(negative_grounding_conflicts),
        "negative_evidence_semantic_rejected_count": len(negative_grounding_conflicts),
        "claim_coverage_status": claim_coverage["claim_coverage_status"],
        "claim_coverage_tag_counts": claim_coverage["coverage_tag_counts"],
        "claim_coverage_missing_core_tags": claim_coverage["missing_core_coverage_tags"],
        "claim_coverage_expansion_recommended": claim_coverage["claim_coverage_expansion_recommended"],
        # P0.1 hard-negative grounding auto-recovery: when the agent cites
        # evidence with a negative stance but forgot to populate
        # ``negative_evidence_ids``, the view infers the anchor list from the
        # evidence_map. Count surfaces how often the auto-inference rescued a
        # grounded weakness from being demoted to a potential concern.
        "stance_inferred_negative_grounding_count": len(stance_inferred_flaws),
        "actionable_limitation_count": actionable_lim,
        "context_limitation_count": context_lim,
        "unresolved_diagnostic_count": unresolved_diag_lim,
        "stale_limitation_count": stale_lim,
        # P1.5 high-precision limitation usefulness metrics:
        # actionable_limitation_ratio = actionable / total_limitations (1.0 = every limitation
        # is reviewer-actionable, 0.0 = system only flags context gaps).
        # diagnostic_useful_ratio = (actionable + unresolved_diagnostic) / total_limitations
        # (treats unresolved diagnostics as still-useful for downstream human review).
        "total_limitation_count": total_lim,
        "actionable_limitation_ratio": actionable_ratio,
        "diagnostic_useful_limitation_ratio": diagnostic_useful_ratio,
    }
    return view


def _grounded_active_flaws_for_decision(state: Dict[str, Any], severities: set[str]) -> List[Dict[str, Any]]:
    flaws: List[Dict[str, Any]] = []
    for flaw in state.get("flaw_candidates", []) or []:
        if not isinstance(flaw, dict):
            continue
        if flaw.get("status") in {"downgraded", "retracted"}:
            continue
        if flaw.get("severity") not in severities:
            continue
        if _is_fallback_or_meta_flaw(flaw):
            continue
        if not flaw.get("evidence_ids"):
            continue
        flaws.append(flaw)
    return flaws


def _decision_support_bucket_count(hygiene: Dict[str, Any], bucket_names: set[str]) -> int:
    source_counts = hygiene.get("real_strong_support_source_counts", {}) or {}
    return sum(int(source_counts.get(bucket, 0) or 0) for bucket in bucket_names)


def infer_final_recommendation_view(state: Dict[str, Any], manager_payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Return an evidence-grounded recommendation view for final reporting.

    This is the paper-facing final recommendation layer. It separates strict
    accept-like outcomes from borderline and not-assessable outcomes so the
    binary health-check decision does not need to pretend every uncertain case
    is either a clean accept or a clean reject.
    """
    decision_state = build_decision_hygiene_view(state or {})
    hygiene = decision_state.get("decision_hygiene", {}) or {}

    strong_support = int(hygiene.get("real_strong_support_total", 0) or 0)
    claims_with_support = int(hygiene.get("claims_with_real_strong_support", 0) or 0)
    non_abstract_support = int(hygiene.get("non_abstract_real_strong_support_count", 0) or 0)
    empirical_support = _decision_support_bucket_count(
        hygiene,
        {"result_or_experiment", "results", "result", "experiment", "ablation", "table_or_figure"},
    )
    method_support = _decision_support_bucket_count(
        hygiene,
        {"method_or_approach", "method_or_design", "method", "theory_or_proof", "proof", "theory"},
    )
    targetless_uncertainty = max(
        int(hygiene.get("targetless_unresolved_deferred_count", 0) or 0),
        int(hygiene.get("targetless_unresolved_deferred_raw_count", 0) or 0),
    )
    context_or_meta_uncertainty = int(hygiene.get("deferred_context_or_meta_unresolved_count", 0) or 0)
    open_gap_count = int(hygiene.get("open_evidence_gap_count", 0) or 0)
    stale_gap_count = int(hygiene.get("stale_evidence_gap_count", 0) or 0)
    independent_support_claims = int(hygiene.get("claims_with_2plus_independent_support", 0) or 0)
    primary_claim_support_coverage = float(hygiene.get("primary_claim_support_coverage", 0.0) or 0.0)
    primary_claim_empirical_coverage = float(hygiene.get("primary_claim_empirical_coverage", 0.0) or 0.0)
    support_concentration = float(hygiene.get("support_concentration_index", 0.0) or 0.0)
    total_limitation_count = int(hygiene.get("total_limitation_count", 0) or 0)
    context_limitation_count = int(hygiene.get("context_limitation_count", 0) or 0)
    unlinked_negative_evidence_count = int(hygiene.get("negative_evidence_unlinked_to_flaw_count", 0) or 0)
    unresolved = len(_open_unresolved_questions(decision_state))
    conflicts = len(decision_state.get("conflict_notes", []) or [])
    grounded_critical = _grounded_active_flaws_for_decision(decision_state, {"critical"})
    grounded_major = _grounded_active_flaws_for_decision(decision_state, {"major"})
    active_major_like = [
        flaw for flaw in decision_state.get("flaw_candidates", []) or []
        if isinstance(flaw, dict)
        and flaw.get("severity") in {"critical", "major"}
        and flaw.get("status") not in {"downgraded", "retracted"}
        and not _is_fallback_or_meta_flaw(flaw)
    ]

    support_ready = (
        strong_support >= 3
        and claims_with_support >= 2
        and non_abstract_support >= 2
        and (empirical_support >= 1 or (method_support >= 1 and non_abstract_support >= 3))
    )
    high_confidence_support_path = (
        strong_support >= 4
        and claims_with_support >= 3
        and non_abstract_support >= 4
        and empirical_support >= 2
        and unresolved == 0
        and targetless_uncertainty <= 3
        and open_gap_count == 0
        and conflicts == 0
    )
    strong_borderline_accept_path = (
        support_ready
        and strong_support >= 3
        and claims_with_support >= 3
        and non_abstract_support >= 3
        and empirical_support >= 2
        and unresolved == 0
        and targetless_uncertainty <= 3
        and open_gap_count == 0
        and not grounded_critical
        and not grounded_major
        and not active_major_like
        and conflicts == 0
    )
    clean_accept_path = (
        (support_ready or high_confidence_support_path)
        and not grounded_critical
        and not grounded_major
        and not active_major_like
        and unresolved == 0
        and (targetless_uncertainty == 0 or high_confidence_support_path)
        and conflicts == 0
    )

    if grounded_critical or len(grounded_major) >= 2:
        view = "reject_like"
        reason = "grounded_major_or_critical_flaw"
        binary = "reject"
    elif clean_accept_path:
        view = "accept_like"
        reason = (
            "high_confidence_real_empirical_support_without_grounded_blocker"
            if high_confidence_support_path and targetless_uncertainty
            else "real_nonabstract_empirical_support_without_grounded_blocker"
        )
        binary = "accept"
    elif support_ready and not grounded_critical and len(grounded_major) < 2:
        view = "borderline_positive"
        reason = "positive_support_present_but_uncertainty_or_unverified_negative_remains"
        binary = "accept" if strong_borderline_accept_path else "reject"
    elif strong_support > 0 or non_abstract_support > 0:
        view = "borderline_insufficient"
        reason = "some_real_support_but_not_enough_quality_or_coverage_for_accept_like"
        binary = "reject"
    elif unresolved >= 3 or targetless_uncertainty >= 2:
        view = "not_assessable_uncertain"
        reason = "insufficient_grounded_support_with_open_uncertainty"
        binary = "reject"
    else:
        view = "reject_like"
        reason = "no_usable_accept_support"
        binary = "reject"

    accept_calibration_warnings: List[str] = []
    if view == "accept_like" or binary == "accept":
        if independent_support_claims <= 0:
            accept_calibration_warnings.append("no_claim_with_2plus_independent_support")
        if primary_claim_support_coverage < 1.0:
            accept_calibration_warnings.append("primary_claim_support_incomplete")
        if primary_claim_empirical_coverage < 1.0:
            accept_calibration_warnings.append("primary_claim_empirical_incomplete")
        if support_concentration > 0.75:
            accept_calibration_warnings.append("support_concentrated_on_one_claim")
        if context_limitation_count > 0 or context_or_meta_uncertainty > 0:
            accept_calibration_warnings.append("context_limitations_present")
        if unlinked_negative_evidence_count > 0:
            accept_calibration_warnings.append("unlinked_negative_evidence_present")

    return {
        "recommendation_view": view,
        "binary_decision": binary,
        "reason": reason,
        "real_strong_support_total": strong_support,
        "claims_with_real_strong_support": claims_with_support,
        "non_abstract_real_strong_support_count": non_abstract_support,
        "empirical_real_strong_support_count": empirical_support,
        "method_real_strong_support_count": method_support,
        "claims_with_2plus_independent_support": independent_support_claims,
        "primary_claim_support_coverage": primary_claim_support_coverage,
        "primary_claim_empirical_coverage": primary_claim_empirical_coverage,
        "support_concentration_index": support_concentration,
        "total_limitation_count": total_limitation_count,
        "context_limitation_count": context_limitation_count,
        "negative_evidence_unlinked_to_flaw_count": unlinked_negative_evidence_count,
        "accept_calibration_warning_count": len(accept_calibration_warnings),
        "accept_calibration_warnings": accept_calibration_warnings,
        "open_unresolved_count": unresolved,
        "targetless_uncertainty_count": targetless_uncertainty,
        "context_or_meta_uncertainty_count": context_or_meta_uncertainty,
        "open_evidence_gap_count": open_gap_count,
        "stale_evidence_gap_count": stale_gap_count,
        "conflict_count": conflicts,
        "grounded_critical_flaw_count": len(grounded_critical),
        "grounded_major_flaw_count": len(grounded_major),
        "active_major_like_flaw_count": len(active_major_like),
    }


def _build_revision_summary(revision_log: List[Dict[str, Any]]) -> List[str]:
    summary: List[str] = []
    seen = set()
    for event in reversed(revision_log[-12:]):
        entity_type = event.get("entity_type", "item")
        entity_id = event.get("entity_id", "")
        field = event.get("field", "")
        reason = event.get("reason", "incoming_update")
        before = _normalize_text(event.get("before"), max_length=80)
        after = _normalize_text(event.get("after"), max_length=80)
        line = f"{entity_type}:{entity_id} updated {field} from {before or 'empty'} to {after or 'empty'} ({reason})."
        key = line.lower()
        if key in seen:
            continue
        seen.add(key)
        summary.append(line)
        if len(summary) >= 6:
            break
    return summary


def _build_conflict_summary(conflict_notes: List[Dict[str, Any]]) -> List[str]:
    summary: List[str] = []
    seen = set()
    for note in reversed(conflict_notes[-12:]):
        conflict_type = _normalize_text(note.get("conflict_type"), default="state_conflict", max_length=80)
        text = _normalize_text(note.get("note"), max_length=220)
        if not text:
            continue
        line = f"[{conflict_type}] {text}"
        key = line.lower()
        if key in seen:
            continue
        seen.add(key)
        summary.append(line)
        if len(summary) >= 6:
            break
    return summary


def _build_risk_profile(state: Dict[str, Any]) -> Dict[str, Any]:
    claims = state.get("claims", [])
    flaws = state.get("flaw_candidates", [])
    open_questions = _open_unresolved_questions(state)
    conflict_summary = state.get("conflict_summary", [])[:4]
    evidence_gaps = _open_evidence_gaps(state)[:4]

    supported_claims = [claim for claim in claims if claim.get("status") == "supported"]
    mixed_claims = [claim for claim in claims if claim.get("status") == "partially_supported"]
    uncertain_claims = [claim for claim in claims if claim.get("status") in {"new", "uncertain", "unsupported"}]
    active_flaws = [
        flaw for flaw in flaws
        if flaw.get("status") not in {"retracted"}
    ]
    major_flaws = [
        flaw for flaw in active_flaws
        if flaw.get("severity") in {"critical", "major"} and flaw.get("status") != "downgraded"
    ]

    dominant_risks = []
    if major_flaws:
        dominant_risks.append(f"{len(major_flaws)} high-severity flaw(s) remain active.")
    if conflict_summary:
        dominant_risks.append(f"{len(conflict_summary)} recent conflict signal(s) require recheck.")
    if evidence_gaps:
        dominant_risks.append(f"{len(evidence_gaps)} evidence gap(s) remain unresolved.")
    if open_questions:
        dominant_risks.append(f"{len(open_questions)} open review question(s) still block closure.")

    support_signals = []
    if supported_claims:
        support_signals.append(f"{len(supported_claims)} claim(s) are strongly supported.")
    if mixed_claims:
        support_signals.append(f"{len(mixed_claims)} claim(s) are only partially supported.")
    if uncertain_claims:
        support_signals.append(f"{len(uncertain_claims)} claim(s) remain uncertain or unsupported.")

    readiness = "not_ready"
    if not dominant_risks and supported_claims and not open_questions:
        readiness = "ready_to_finalize"
    elif supported_claims or mixed_claims:
        readiness = "needs_targeted_recheck"

    return {
        "dominant_risks": dominant_risks[:4],
        "support_signals": support_signals[:4],
        "open_question_count": len(open_questions),
        "major_flaw_count": len(major_flaws),
        "conflict_count": len(state.get("conflict_notes", [])),
        "readiness": readiness,
    }


def _update_state_summaries(state: Dict[str, Any]) -> Dict[str, Any]:
    updated = copy.deepcopy(state)
    updated["revision_summary"] = _build_revision_summary(updated.get("revision_log", []))
    updated["conflict_summary"] = _build_conflict_summary(updated.get("conflict_notes", []))
    updated["risk_profile"] = _build_risk_profile(updated)
    return updated


def normalize_review_update_payload(payload: Any, required_fields: Optional[Iterable[str]] = None) -> Dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("Review payload must be a JSON object.")

    claims = [
        normalized
        for idx, item in enumerate(payload.get("claims", []), start=1)
        if (normalized := _normalize_claim_item(item, idx)) is not None
    ]
    evidence_map = [
        normalized
        for idx, item in enumerate(payload.get("evidence_map", []), start=1)
        if (normalized := _normalize_evidence_item(item, idx)) is not None
    ]
    raw_flaws = payload.get("flaw_candidates", []) or []
    if not isinstance(raw_flaws, list):
        raw_flaws = [raw_flaws]
    flaw_candidates = [
        normalized
        for idx, item in enumerate(raw_flaws, start=1)
        if (normalized := _normalize_flaw_item(item, idx)) is not None
    ]
    context_limitation_questions = [
        normalized
        for idx, item in enumerate(raw_flaws, start=1)
        if (normalized := _context_limitation_question_from_flaw_item(item, idx)) is not None
    ]
    unresolved_questions = _normalize_questions(payload.get("unresolved_questions")) + context_limitation_questions
    conflict_notes = _normalize_conflicts(payload.get("conflict_notes"))
    evidence_gaps = _normalize_evidence_gaps(payload.get("evidence_gaps"), max_items=10)
    current_hypotheses = _normalize_list_of_strings(payload.get("current_hypotheses"), max_items=8, max_length=240)
    dialogue_summary = _normalize_text(payload.get("dialogue_summary"), max_length=1000)
    summary_update = _normalize_text(payload.get("summary_update"), max_length=1000)
    recommendation = _normalize_choice(payload.get("recommendation"), FINAL_DECISIONS, "undecided")
    active_focus = _normalize_text(payload.get("active_focus") or payload.get("focus"), max_length=400)
    pending_user_question = _normalize_text(payload.get("pending_user_question") or payload.get("clarification_question"), max_length=400)
    simulated_user_reply = _normalize_text(payload.get("simulated_user_reply"), max_length=400)
    clarification_needed = bool(payload.get("clarification_needed")) or bool(payload.get("requires_clarification"))
    evidence_id_scope_map: Dict[str, str] = {}
    raw_scope_map = payload.get("evidence_id_scope_map")
    if isinstance(raw_scope_map, dict):
        for old_id, new_id in raw_scope_map.items():
            normalized_old = _normalize_text(old_id, max_length=80)
            normalized_new = _normalize_text(new_id, max_length=80)
            if normalized_old and normalized_new:
                evidence_id_scope_map[normalized_old] = normalized_new
            if len(evidence_id_scope_map) >= 24:
                break
    try:
        evidence_id_scope_turn = max(0, int(payload.get("evidence_id_scope_turn", 0) or 0))
    except (TypeError, ValueError):
        evidence_id_scope_turn = 0
    evidence_json_contract_mode = _normalize_text(payload.get("evidence_json_contract_mode"), max_length=80)
    evidence_json_parse_status = _normalize_text(payload.get("evidence_json_parse_status"), max_length=80)
    evidence_json_failure_type = _normalize_text(payload.get("evidence_json_failure_type"), max_length=80)
    evidence_json_parse_error = _normalize_text(payload.get("evidence_json_parse_error"), max_length=240)
    evidence_json_partial_recovery = bool(payload.get("evidence_json_partial_recovery", False))
    evidence_json_fallback_payload_used = bool(payload.get("evidence_json_fallback_payload_used", False))
    try:
        evidence_json_raw_chars = max(0, int(payload.get("evidence_json_raw_chars", 0) or 0))
    except (TypeError, ValueError):
        evidence_json_raw_chars = 0
    try:
        evidence_json_prompt_chars = max(0, int(payload.get("evidence_json_prompt_chars", 0) or 0))
    except (TypeError, ValueError):
        evidence_json_prompt_chars = 0

    normalized_payload = {
        "claims": claims[:8],
        "evidence_map": evidence_map[:12],
        "flaw_candidates": flaw_candidates[:8],
        "unresolved_questions": unresolved_questions,
        "conflict_notes": conflict_notes[:12],
        "evidence_gaps": evidence_gaps,
        "current_hypotheses": current_hypotheses,
        "dialogue_summary": dialogue_summary,
        "summary_update": summary_update,
        "recommendation": recommendation,
        "active_focus": active_focus,
        "pending_user_question": pending_user_question,
        "simulated_user_reply": simulated_user_reply,
        "clarification_needed": clarification_needed,
        "action": _normalize_text(payload.get("action")),
        "target_type": _normalize_text(payload.get("target_type")),
        "target_id": _normalize_text(payload.get("target_id")),
        "old_status": _normalize_text(payload.get("old_status")),
        "new_status": _normalize_text(payload.get("new_status")),
        "supporting_evidence_ids": _strip_synthetic_recovery_markers(
            _normalize_list_of_strings(payload.get("supporting_evidence_ids"))
        ),
        "conflict_note_ids": _normalize_list_of_strings(payload.get("conflict_note_ids")),
        "reason_for_change": _normalize_text(payload.get("reason_for_change")),
        "resolution_expectation": _normalize_text(payload.get("resolution_expectation")),
        "confidence": payload.get("confidence"),
        "blocked_reason": _normalize_text(payload.get("blocked_reason")),
        "missing_requirements": _normalize_list_of_strings(payload.get("missing_requirements")),
        "_recovery_patch_source": _normalize_text(payload.get("_recovery_patch_source"), max_length=40),
        "recovery_terminal": bool(payload.get("recovery_terminal") or payload.get("terminal_recovery_block")),
        "recovery_terminal_reason": _normalize_text(
            payload.get("recovery_terminal_reason") or payload.get("terminal_recovery_reason"),
            max_length=120,
        ),
        "recovery_repeat_allowed": bool(payload.get("recovery_repeat_allowed", True)),
        "_emission_failure_code": _normalize_text(payload.get("_emission_failure_code"), max_length=80),
        "_emission_failure_message": _normalize_text(payload.get("_emission_failure_message"), max_length=240),
        "evidence_id_scope_turn": evidence_id_scope_turn,
        "evidence_id_scope_map": evidence_id_scope_map,
        "evidence_json_contract_mode": evidence_json_contract_mode,
        "evidence_json_parse_status": evidence_json_parse_status,
        "evidence_json_failure_type": evidence_json_failure_type,
        "evidence_json_parse_error": evidence_json_parse_error,
        "evidence_json_partial_recovery": evidence_json_partial_recovery,
        "evidence_json_fallback_payload_used": evidence_json_fallback_payload_used,
        "evidence_json_raw_chars": evidence_json_raw_chars,
        "evidence_json_prompt_chars": evidence_json_prompt_chars,
    }

    if required_fields:
        missing = [
            field
            for field in required_fields
            if field in {"claims", "evidence_map", "flaw_candidates"} and not normalized_payload[field]
        ]
        if missing:
            raise ValueError(f"Review payload is missing required content for: {', '.join(missing)}")

    return normalized_payload


def normalize_manager_payload(payload: Any, available_agents: Optional[Iterable[str]] = None) -> Dict[str, Any]:
    normalized_payload = normalize_review_update_payload(payload)
    allowed_agents = list(available_agents or [])
    decision = _normalize_choice(payload.get("decision"), TURN_DECISIONS, "continue")
    action_type = _normalize_choice(payload.get("action_type"), MANAGER_ACTION_TYPES, "extract_claims")
    selected_agents = []
    for agent_name in payload.get("selected_agents", []):
        name = _normalize_text(agent_name, max_length=120)
        if name and (not allowed_agents or name in allowed_agents) and name not in selected_agents:
            selected_agents.append(name)

    final_decision = _normalize_choice(payload.get("final_decision"), FINAL_DECISIONS, "undecided")
    final_report = _normalize_text(payload.get("final_report"), max_length=4000)
    focus = _normalize_text(payload.get("focus"), max_length=400)
    rationale = _normalize_text(payload.get("rationale"), max_length=600)
    target_claim_ids = _normalize_list_of_strings(payload.get("target_claim_ids"), max_items=6, max_length=80)
    target_flaw_ids = _normalize_list_of_strings(payload.get("target_flaw_ids"), max_items=6, max_length=80)
    target_evidence_ids = _normalize_list_of_strings(payload.get("target_evidence_ids"), max_items=6, max_length=80)
    target_hypotheses = _normalize_list_of_strings(payload.get("target_hypotheses"), max_items=6, max_length=240)
    requires_clarification = bool(payload.get("requires_clarification")) or normalized_payload.get("clarification_needed", False)
    clarification_question = normalized_payload.get("pending_user_question", "")
    summary_update = normalized_payload.get("summary_update", "")
    policy_source = _normalize_text(payload.get("policy_source"), default="manager_model", max_length=120)
    policy_notes = _normalize_list_of_strings(payload.get("policy_notes"), max_items=8, max_length=240)
    effective_action_type = _normalize_choice(payload.get("effective_action_type"), MANAGER_ACTION_TYPES, action_type)
    auto_finalized = bool(payload.get("auto_finalized", False))
    turn_mode = _normalize_choice(payload.get("turn_mode"), TURN_MODES, "")
    phase = _normalize_choice(payload.get("phase"), REVIEW_PHASES, "")
    phase_before_action = _normalize_choice(payload.get("phase_before_action"), REVIEW_PHASES, "")
    phase_enter_reason = _normalize_text(payload.get("phase_enter_reason"), max_length=240)
    phase_exit_reason = _normalize_text(payload.get("phase_exit_reason"), max_length=240)
    phase_hold_reason = _normalize_text(payload.get("phase_hold_reason"), max_length=240)
    try:
        phase_turn_index = max(0, int(payload.get("phase_turn_index", 0) or 0))
    except (TypeError, ValueError):
        phase_turn_index = 0
    sticky_target_id = _normalize_text(payload.get("sticky_target_id"), max_length=80)
    sticky_target_type = _normalize_text(payload.get("sticky_target_type"), max_length=40)
    sticky_release_reason = _normalize_text(payload.get("sticky_release_reason"), max_length=120)
    try:
        sticky_target_turns_remaining = max(0, int(payload.get("sticky_target_turns_remaining", 0) or 0))
    except (TypeError, ValueError):
        sticky_target_turns_remaining = 0
    sticky_target_active = bool(payload.get("sticky_target_active", False))
    sticky_target_applied = bool(payload.get("sticky_target_applied", False))
    sticky_target_reused = bool(payload.get("sticky_target_reused", False))
    sticky_target_released = bool(payload.get("sticky_target_released", False))
    target_switch_blocked_by_sticky = bool(payload.get("target_switch_blocked_by_sticky", False))
    early_finalize_attempted = bool(payload.get("early_finalize_attempted", False))
    finalize_blocked_by_phase = bool(payload.get("finalize_blocked_by_phase", False))
    progression_gate_triggered = bool(payload.get("progression_gate_triggered", False))
    support_formation_pass_triggered = bool(payload.get("support_formation_pass_triggered", False))
    negative_evidence_formation_required = bool(payload.get("negative_evidence_formation_required", False))
    negative_evidence_binding_retry_required = bool(payload.get("negative_evidence_binding_retry_required", False))
    support_formation_pass_reason = _normalize_text(payload.get("support_formation_pass_reason"), max_length=160)
    support_formation_pass_from_action = _normalize_text(payload.get("support_formation_pass_from_action"), max_length=80)
    progression_gate_reason = _normalize_text(payload.get("progression_gate_reason"), max_length=80)
    progression_gate_raw_target_ids = _normalize_list_of_strings(payload.get("progression_gate_raw_target_ids"), max_items=8, max_length=80)
    progression_gate_sanitized_target_ids = _normalize_list_of_strings(payload.get("progression_gate_sanitized_target_ids"), max_items=8, max_length=80)
    blocked_aggressive_recovery_action = _normalize_text(payload.get("blocked_aggressive_recovery_action"), max_length=80)
    fallback_target_gate_blocked = bool(payload.get("fallback_target_gate_blocked", False))
    broad_target_gate_blocked = bool(payload.get("broad_target_gate_blocked", False))
    weak_conflict_gate_blocked = bool(payload.get("weak_conflict_gate_blocked", False))
    raw_target_claim_ids = _normalize_list_of_strings(payload.get("raw_target_claim_ids"), max_items=8, max_length=80)
    post_fallback_target_claim_ids = _normalize_list_of_strings(payload.get("post_fallback_target_claim_ids"), max_items=8, max_length=80)
    fallback_claim_ids_used = _normalize_list_of_strings(payload.get("fallback_claim_ids_used"), max_items=8, max_length=80)
    fallback_evidence_ids_used = _normalize_list_of_strings(payload.get("fallback_evidence_ids_used"), max_items=8, max_length=80)
    post_sanitize_target_claim_ids = _normalize_list_of_strings(payload.get("post_sanitize_target_claim_ids"), max_items=8, max_length=80)
    final_action_target_claim_ids = _normalize_list_of_strings(payload.get("final_action_target_claim_ids"), max_items=8, max_length=80)
    recovery_push_reasons = _normalize_list_of_strings(payload.get("recovery_push_reasons"), max_items=8, max_length=80)
    target_quality_reasons = _normalize_list_of_strings(payload.get("target_quality_reasons"), max_items=8, max_length=80)
    def _safe_int(value: Any) -> int:
        try:
            return max(0, int(value or 0))
        except (TypeError, ValueError):
            return 0
    raw_target_count = _safe_int(payload.get("raw_target_count", len(raw_target_claim_ids)))
    post_fallback_target_count = _safe_int(payload.get("post_fallback_target_count", len(post_fallback_target_claim_ids)))
    post_sanitize_target_count = _safe_int(payload.get("post_sanitize_target_count", len(post_sanitize_target_claim_ids)))
    final_action_target_count = _safe_int(payload.get("final_action_target_count", len(final_action_target_claim_ids)))
    sanitize_bloat_delta = _safe_int(payload.get("sanitize_bloat_delta", 0))
    raw_target_is_broad = bool(payload.get("raw_target_is_broad", False))
    fallback_target_present = bool(payload.get("fallback_target_present", False))
    fallback_contradiction_emitted = bool(payload.get("fallback_contradiction_emitted", False))
    sanitize_bloat_detected = bool(payload.get("sanitize_bloat_detected", False))
    sanitize_expanded_from_raw = bool(payload.get("sanitize_expanded_from_raw", False))
    sanitize_expanded_from_fallback = bool(payload.get("sanitize_expanded_from_fallback", False))
    final_action_type = _normalize_choice(payload.get("final_action_type"), MANAGER_ACTION_TYPES, action_type)
    final_effective_action_type = _normalize_choice(payload.get("final_effective_action_type"), MANAGER_ACTION_TYPES, effective_action_type)
    recovery_candidate_action = _normalize_choice(payload.get("recovery_candidate_action"), MANAGER_ACTION_TYPES, action_type)
    recovery_push_triggered = bool(payload.get("recovery_push_triggered", False))
    recovery_push_source = _normalize_text(payload.get("recovery_push_source"), default="none", max_length=120)
    target_quality_label = _normalize_choice(
        payload.get("target_quality_label"),
        {"narrow_real_target", "broad_target", "fallback_target", "weak_target", "empty_target"},
        "empty_target",
    )
    # Target Quality Certificate fields (observability-only)
    tqc_target_source = _normalize_choice(
        payload.get("tqc_target_source"),
        {"empty_or_unknown", "fallback_claim", "mixed_real_and_fallback", "real_claim"},
        "empty_or_unknown",
    )
    tqc_target_width = _normalize_choice(
        payload.get("tqc_target_width"),
        {"empty", "single_target", "small_target_set", "broad_target_set"},
        "empty",
    )
    tqc_evidence_grounding = _normalize_choice(
        payload.get("tqc_evidence_grounding"),
        {"no_aligned_evidence", "fallback_evidence_only", "weak_evidence", "grounded_evidence"},
        "no_aligned_evidence",
    )
    tqc_conflict_strength = _normalize_choice(
        payload.get("tqc_conflict_strength"),
        {"weak_conflict", "missing_evidence_only", "unresolved_but_ungrounded", "strong_grounded_conflict"},
        "weak_conflict",
    )
    recovery_readiness_label = _normalize_choice(
        payload.get("recovery_readiness_label"),
        {
            "not_ready_for_recovery",
            "fallback_bridge_only",
            "needs_target_refinement",
            "needs_evidence_grounding",
            "ready_for_aggressive_recovery",
        },
        "not_ready_for_recovery",
    )
    recovery_readiness_reasons = _normalize_list_of_strings(
        payload.get("recovery_readiness_reasons"), max_items=8, max_length=80
    )
    recovery_entry_deferred = bool(payload.get("recovery_entry_deferred", False))
    recovery_entry_defer_reason = _normalize_text(payload.get("recovery_entry_defer_reason"), max_length=80)
    recovery_entry_deferred_from = _normalize_text(payload.get("recovery_entry_deferred_from"), max_length=80)
    fallback_claim_targets_omitted = _normalize_list_of_strings(
        payload.get("fallback_claim_targets_omitted"), max_items=8, max_length=80
    )
    try:
        fallback_claim_targets_omitted_count = max(
            0, int(payload.get("fallback_claim_targets_omitted_count", len(fallback_claim_targets_omitted)) or 0)
        )
    except (TypeError, ValueError):
        fallback_claim_targets_omitted_count = len(fallback_claim_targets_omitted)
    fallback_targets_replaced_with_real_candidates = bool(
        payload.get("fallback_targets_replaced_with_real_candidates", False)
    )
    evidence_context_contains_claim_match = bool(payload.get("evidence_context_contains_claim_match", False))
    evidence_context_contains_empirical_terms = bool(payload.get("evidence_context_contains_empirical_terms", False))
    evidence_context_empirical_term_count = _safe_int(payload.get("evidence_context_empirical_term_count", 0))
    evidence_context_table_or_figure_term_count = _safe_int(payload.get("evidence_context_table_or_figure_term_count", 0))
    evidence_context_method_term_count = _safe_int(payload.get("evidence_context_method_term_count", 0))
    evidence_context_claim_query_term_count = _safe_int(payload.get("evidence_context_claim_query_term_count", 0))
    evidence_context_claim_query_terms = _normalize_list_of_strings(
        payload.get("evidence_context_claim_query_terms"), max_items=12, max_length=80
    )
    evidence_context_snippet_sources = _normalize_list_of_strings(
        payload.get("evidence_context_snippet_sources"), max_items=12, max_length=80
    )
    evidence_quote_bank_count = _safe_int(payload.get("evidence_quote_bank_count", 0))
    evidence_quote_bank_sources = _normalize_list_of_strings(
        payload.get("evidence_quote_bank_sources"), max_items=12, max_length=80
    )
    evidence_quote_bank_claim_matched_count = _safe_int(payload.get("evidence_quote_bank_claim_matched_count", 0))
    evidence_quote_bank_mode = _normalize_text(payload.get("evidence_quote_bank_mode"), max_length=80)
    evidence_empirical_observability_mode = _normalize_text(
        payload.get("evidence_empirical_observability_mode"), max_length=80
    )
    evidence_raw_contains_empirical_terms = bool(payload.get("evidence_raw_contains_empirical_terms", False))
    evidence_raw_contains_table_or_figure_terms = bool(payload.get("evidence_raw_contains_table_or_figure_terms", False))
    evidence_raw_empirical_term_count = _safe_int(payload.get("evidence_raw_empirical_term_count", 0))
    evidence_raw_negative_empirical_term_count = _safe_int(payload.get("evidence_raw_negative_empirical_term_count", 0))
    evidence_payload_evidence_count = _safe_int(payload.get("evidence_payload_evidence_count", 0))
    evidence_payload_empirical_evidence_count = _safe_int(payload.get("evidence_payload_empirical_evidence_count", 0))
    evidence_payload_table_or_figure_count = _safe_int(payload.get("evidence_payload_table_or_figure_count", 0))
    evidence_payload_method_evidence_count = _safe_int(payload.get("evidence_payload_method_evidence_count", 0))
    evidence_payload_strong_empirical_count = _safe_int(payload.get("evidence_payload_strong_empirical_count", 0))
    evidence_payload_support_empirical_count = _safe_int(payload.get("evidence_payload_support_empirical_count", 0))
    evidence_payload_has_empirical_evidence = bool(payload.get("evidence_payload_has_empirical_evidence", False))
    evidence_empirical_structuring_status = _normalize_text(
        payload.get("evidence_empirical_structuring_status"), max_length=120
    )
    evidence_json_contract_mode = _normalize_text(
        payload.get("evidence_json_contract_mode"), max_length=80
    )
    evidence_json_parse_status = _normalize_text(
        payload.get("evidence_json_parse_status"), max_length=80
    )
    evidence_json_failure_type = _normalize_text(
        payload.get("evidence_json_failure_type"), max_length=80
    )
    evidence_json_parse_error = _normalize_text(
        payload.get("evidence_json_parse_error"), max_length=240
    )
    evidence_json_partial_recovery = bool(payload.get("evidence_json_partial_recovery", False))
    evidence_json_fallback_payload_used = bool(payload.get("evidence_json_fallback_payload_used", False))
    evidence_json_raw_chars = _safe_int(payload.get("evidence_json_raw_chars", 0))
    evidence_json_prompt_chars = _safe_int(payload.get("evidence_json_prompt_chars", 0))
    evidence_focus_mode = _normalize_text(payload.get("evidence_focus_mode"), max_length=80)
    evidence_focus_reason = _normalize_text(payload.get("evidence_focus_reason"), max_length=160)
    evidence_focus_original_claim_ids = _normalize_list_of_strings(
        payload.get("evidence_focus_original_claim_ids"), max_items=8, max_length=80
    )
    evidence_focus_selected_claim_ids = _normalize_list_of_strings(
        payload.get("evidence_focus_selected_claim_ids"), max_items=8, max_length=80
    )
    evidence_focus_preferred_claim_ids = _normalize_list_of_strings(
        payload.get("evidence_focus_preferred_claim_ids"), max_items=8, max_length=80
    )
    evidence_focus_applied = bool(payload.get("evidence_focus_applied", False))
    evidence_focus_original_claim_count = _safe_int(
        payload.get("evidence_focus_original_claim_count", len(evidence_focus_original_claim_ids))
    )
    evidence_focus_selected_claim_count = _safe_int(
        payload.get("evidence_focus_selected_claim_count", len(evidence_focus_selected_claim_ids))
    )
    evidence_focus_preferred_claim_count = _safe_int(
        payload.get("evidence_focus_preferred_claim_count", len(evidence_focus_preferred_claim_ids))
    )

    if decision == "finalize":
        action_type = "finalize"
        selected_agents = []

    if not turn_mode:
        turn_mode = "recovery_patch" if action_type in RECOVERY_PATCH_ACTION_TYPES or effective_action_type in RECOVERY_PATCH_ACTION_TYPES else "normal_evidence"
    if not phase:
        phase = "recovery" if action_type in RECOVERY_ACTION_TYPES or effective_action_type in RECOVERY_ACTION_TYPES or turn_mode == "recovery_patch" else "normal_review"
    if not phase_before_action:
        phase_before_action = phase

    return {
        **normalized_payload,
        "decision": decision,
        "action_type": action_type,
        "selected_agents": selected_agents,
        "focus": focus,
        "rationale": rationale,
        "target_claim_ids": target_claim_ids,
        "target_flaw_ids": target_flaw_ids,
        "target_evidence_ids": target_evidence_ids,
        "target_hypotheses": target_hypotheses,
        "requires_clarification": requires_clarification,
        "clarification_question": clarification_question,
        "summary_update": summary_update,
        "policy_source": policy_source,
        "policy_notes": policy_notes,
        "effective_action_type": effective_action_type,
        "turn_mode": turn_mode,
        "recovery_patch_mode_entered": turn_mode == "recovery_patch",
        "phase": phase,
        "phase_before_action": phase_before_action,
        "phase_enter_reason": phase_enter_reason,
        "phase_exit_reason": phase_exit_reason,
        "phase_hold_reason": phase_hold_reason,
        "phase_turn_index": phase_turn_index,
        "sticky_target_id": sticky_target_id,
        "sticky_target_type": sticky_target_type,
        "sticky_target_active": sticky_target_active,
        "sticky_target_applied": sticky_target_applied,
        "sticky_target_reused": sticky_target_reused,
        "sticky_target_released": sticky_target_released,
        "sticky_release_reason": sticky_release_reason,
        "sticky_target_turns_remaining": sticky_target_turns_remaining,
        "target_switch_blocked_by_sticky": target_switch_blocked_by_sticky,
        "progression_gate_triggered": progression_gate_triggered,
        "support_formation_pass_triggered": support_formation_pass_triggered,
        "negative_evidence_formation_required": negative_evidence_formation_required,
        "negative_evidence_binding_retry_required": negative_evidence_binding_retry_required,
        "support_formation_pass_reason": support_formation_pass_reason,
        "support_formation_pass_from_action": support_formation_pass_from_action,
        "progression_gate_reason": progression_gate_reason,
        "progression_gate_raw_target_ids": progression_gate_raw_target_ids,
        "progression_gate_sanitized_target_ids": progression_gate_sanitized_target_ids,
        "blocked_aggressive_recovery_action": blocked_aggressive_recovery_action,
        "fallback_target_gate_blocked": fallback_target_gate_blocked,
        "broad_target_gate_blocked": broad_target_gate_blocked,
        "weak_conflict_gate_blocked": weak_conflict_gate_blocked,
        "raw_target_claim_ids": raw_target_claim_ids,
        "raw_target_count": raw_target_count,
        "raw_target_is_broad": raw_target_is_broad,
        "post_fallback_target_claim_ids": post_fallback_target_claim_ids,
        "post_fallback_target_count": post_fallback_target_count,
        "fallback_target_present": fallback_target_present,
        "fallback_claim_ids_used": fallback_claim_ids_used,
        "fallback_evidence_ids_used": fallback_evidence_ids_used,
        "fallback_contradiction_emitted": fallback_contradiction_emitted,
        "post_sanitize_target_claim_ids": post_sanitize_target_claim_ids,
        "post_sanitize_target_count": post_sanitize_target_count,
        "sanitize_bloat_detected": sanitize_bloat_detected,
        "sanitize_bloat_delta": sanitize_bloat_delta,
        "sanitize_expanded_from_raw": sanitize_expanded_from_raw,
        "sanitize_expanded_from_fallback": sanitize_expanded_from_fallback,
        "final_action_target_claim_ids": final_action_target_claim_ids,
        "final_action_target_count": final_action_target_count,
        "final_action_type": final_action_type,
        "final_effective_action_type": final_effective_action_type,
        "recovery_candidate_action": recovery_candidate_action,
        "recovery_push_triggered": recovery_push_triggered,
        "recovery_push_source": recovery_push_source,
        "recovery_push_reasons": recovery_push_reasons,
        "target_quality_label": target_quality_label,
        "target_quality_reasons": target_quality_reasons,
        "tqc_target_source": tqc_target_source,
        "tqc_target_width": tqc_target_width,
        "tqc_evidence_grounding": tqc_evidence_grounding,
        "tqc_conflict_strength": tqc_conflict_strength,
        "recovery_readiness_label": recovery_readiness_label,
        "recovery_readiness_reasons": recovery_readiness_reasons,
        "recovery_entry_deferred": recovery_entry_deferred,
        "recovery_entry_defer_reason": recovery_entry_defer_reason,
        "recovery_entry_deferred_from": recovery_entry_deferred_from,
        "fallback_claim_targets_omitted": fallback_claim_targets_omitted,
        "fallback_claim_targets_omitted_count": fallback_claim_targets_omitted_count,
        "fallback_targets_replaced_with_real_candidates": fallback_targets_replaced_with_real_candidates,
        "evidence_context_contains_claim_match": evidence_context_contains_claim_match,
        "evidence_context_contains_empirical_terms": evidence_context_contains_empirical_terms,
        "evidence_context_empirical_term_count": evidence_context_empirical_term_count,
        "evidence_context_table_or_figure_term_count": evidence_context_table_or_figure_term_count,
        "evidence_context_method_term_count": evidence_context_method_term_count,
        "evidence_context_claim_query_term_count": evidence_context_claim_query_term_count,
        "evidence_context_claim_query_terms": evidence_context_claim_query_terms,
        "evidence_context_snippet_sources": evidence_context_snippet_sources,
        "evidence_quote_bank_count": evidence_quote_bank_count,
        "evidence_quote_bank_sources": evidence_quote_bank_sources,
        "evidence_quote_bank_claim_matched_count": evidence_quote_bank_claim_matched_count,
        "evidence_quote_bank_mode": evidence_quote_bank_mode,
        "evidence_empirical_observability_mode": evidence_empirical_observability_mode,
        "evidence_raw_contains_empirical_terms": evidence_raw_contains_empirical_terms,
        "evidence_raw_contains_table_or_figure_terms": evidence_raw_contains_table_or_figure_terms,
        "evidence_raw_empirical_term_count": evidence_raw_empirical_term_count,
        "evidence_raw_negative_empirical_term_count": evidence_raw_negative_empirical_term_count,
        "evidence_payload_evidence_count": evidence_payload_evidence_count,
        "evidence_payload_empirical_evidence_count": evidence_payload_empirical_evidence_count,
        "evidence_payload_table_or_figure_count": evidence_payload_table_or_figure_count,
        "evidence_payload_method_evidence_count": evidence_payload_method_evidence_count,
        "evidence_payload_strong_empirical_count": evidence_payload_strong_empirical_count,
        "evidence_payload_support_empirical_count": evidence_payload_support_empirical_count,
        "evidence_payload_has_empirical_evidence": evidence_payload_has_empirical_evidence,
        "evidence_empirical_structuring_status": evidence_empirical_structuring_status,
        "evidence_json_contract_mode": evidence_json_contract_mode,
        "evidence_json_parse_status": evidence_json_parse_status,
        "evidence_json_failure_type": evidence_json_failure_type,
        "evidence_json_parse_error": evidence_json_parse_error,
        "evidence_json_partial_recovery": evidence_json_partial_recovery,
        "evidence_json_fallback_payload_used": evidence_json_fallback_payload_used,
        "evidence_json_raw_chars": evidence_json_raw_chars,
        "evidence_json_prompt_chars": evidence_json_prompt_chars,
        "evidence_focus_mode": evidence_focus_mode,
        "evidence_focus_applied": evidence_focus_applied,
        "evidence_focus_reason": evidence_focus_reason,
        "evidence_focus_original_claim_ids": evidence_focus_original_claim_ids,
        "evidence_focus_selected_claim_ids": evidence_focus_selected_claim_ids,
        "evidence_focus_preferred_claim_ids": evidence_focus_preferred_claim_ids,
        "evidence_focus_original_claim_count": evidence_focus_original_claim_count,
        "evidence_focus_selected_claim_count": evidence_focus_selected_claim_count,
        "evidence_focus_preferred_claim_count": evidence_focus_preferred_claim_count,
        "early_finalize_attempted": early_finalize_attempted,
        "finalize_blocked_by_phase": finalize_blocked_by_phase,
        "auto_finalized": auto_finalized,
        "final_decision": final_decision,
        "final_report": final_report,
    }

def create_initial_review_state(mode: str = "s4") -> Dict[str, Any]:
    normalized_mode = mode.lower() if mode else "s4"
    if normalized_mode not in REVIEW_MODES:
        normalized_mode = "s4"
    return {
        "claims": [],
        "evidence_map": [],
        "flaw_candidates": [],
        "unresolved_questions": [],
        "conflict_notes": [],
        "revision_log": [],
        "evidence_gaps": [],
        "active_focus": "",
        "current_hypotheses": [],
        "revision_summary": [],
        "conflict_summary": [],
        "risk_profile": {
            "dominant_risks": [],
            "support_signals": [],
            "open_question_count": 0,
            "major_flaw_count": 0,
            "conflict_count": 0,
            "readiness": "not_ready",
        },
        "pending_user_question": "",
        "simulated_user_reply": "",
        "clarification_needed": False,
        "dialogue_summary": "",
        "turn_id": 0,
        "mode": normalized_mode,
        "final_decision": "undecided",
        "final_report": "",
        "last_focus": "",
        "phase": "normal_review",
        "phase_enter_reason": "",
        "phase_exit_reason": "",
        "phase_hold_reason": "",
        "phase_turn_index": 0,
        "sticky_target_id": "",
        "sticky_target_type": "",
        "sticky_target_active": False,
        "sticky_target_applied": False,
        "sticky_target_reused": False,
        "sticky_target_released": False,
        "sticky_release_reason": "",
        "sticky_target_turns_remaining": 0,
        "target_switch_blocked_by_sticky": False,
        "recovery_relevant": False,
        "historical_sentinel": False,
        "evidence_quote_bank": [],
        "evidence_grounding_verifier": "quote_bank_claim_v2",
        "_persistent_status_guards": {},
    }


def build_review_task(extras: Dict[str, Any], mode: str, max_turns: int) -> Dict[str, Any]:
    paper_text = _normalize_paper_text(
        extras.get("paper_text") or extras.get("question") or extras.get("paper") or extras.get("task_description"),
        max_length=32000,
    )
    user_goal = _normalize_text(
        extras.get("user_goal"),
        default="Review the paper, track evidence for key claims, surface major flaws, and produce a final accept or reject recommendation.",
        max_length=800,
    )
    review_state = create_initial_review_state(mode=mode)
    paper_id = _normalize_text(extras.get("paper_id"), default="unknown-paper", max_length=120)
    model_adapter_mode = _normalize_text(extras.get("model_adapter_mode"), default="auto", max_length=40).lower()
    if model_adapter_mode not in {"auto", "small_model", "large_model", "off"}:
        model_adapter_mode = "auto"
    review_state["paper_id"] = paper_id
    review_state["model_adapter_mode"] = model_adapter_mode
    paper_body, _ = _clean_paper_body(paper_text)
    review_state["evidence_quote_bank"] = _build_evidence_quote_bank(paper_body, max_quotes=12)
    review_state["recovery_relevant"] = bool(extras.get("recovery_relevant", False))
    review_state["historical_sentinel"] = bool(extras.get("historical_sentinel", False))
    return {
        "paper_id": paper_id,
        "paper_text": paper_text,
        "user_goal": user_goal,
        "data_source": _normalize_text(extras.get("data_source"), default="unknown", max_length=80),
        "ground_truth_decision": _normalize_text(extras.get("ground_truth_decision"), default="", max_length=32).lower(),
        "reference_review": _normalize_text(extras.get("reference_review"), max_length=8000),
        "reference_ratings": extras.get("reference_ratings"),
        "reviewer_comments": _normalize_text(extras.get("reviewer_comments"), max_length=8000),
        "recovery_relevant": bool(extras.get("recovery_relevant", False)),
        "historical_sentinel": bool(extras.get("historical_sentinel", False)),
        "model_adapter_mode": model_adapter_mode,
        "max_turns": max(1, int(max_turns)),
        "mode": mode,
        "review_state": review_state,
        "turn_logs": [],
    }


def _format_hypothesis_status_text(text: Any, new_status: str) -> str:
    plain_text = re.sub(r"^\[[A-Z_]+\]\s*", "", str(text or "").strip())
    return f"[{str(new_status or '').upper()}] {plain_text}".strip()


_RECOVERY_STATE_DELTA_KEYS = (
    "open_conflict_count",
    "open_evidence_gap_count",
    "stale_evidence_gap_count",
    "claims_reconciled_with_strong_support_count",
    "grounded_weakness_count",
    "verified_potential_concern_count",
    "potential_concern_count",
    "assessment_limitation_flaw_count",
    "negative_grounding_conflict_count",
    "confirmed_flaw_without_verified_negative_count",
    "meta_or_fallback_flaw_count",
)
_RECOVERY_BURDEN_DELTA_KEYS = {
    "open_conflict_count",
    "open_evidence_gap_count",
    "stale_evidence_gap_count",
    "claims_reconciled_with_strong_support_count",
    "assessment_limitation_flaw_count",
    "negative_grounding_conflict_count",
    "confirmed_flaw_without_verified_negative_count",
    "meta_or_fallback_flaw_count",
}


def _recovery_state_quality_snapshot(state: Dict[str, Any]) -> Dict[str, int]:
    seed = copy.deepcopy(state or {})
    seed.pop("decision_hygiene", None)
    try:
        view = build_decision_hygiene_view(seed)
    except Exception:  # pragma: no cover - snapshot must never block recovery commit logging
        view = seed
    hygiene = view.get("decision_hygiene", {}) if isinstance(view, dict) else {}
    snapshot: Dict[str, int] = {}
    for key in _RECOVERY_STATE_DELTA_KEYS:
        try:
            snapshot[key] = int(hygiene.get(key, 0) or 0)
        except (TypeError, ValueError):
            snapshot[key] = 0
    confirmed_without_verified = 0
    meta_or_fallback_flaws = 0
    for flaw in view.get("flaw_candidates", []) or []:
        if not isinstance(flaw, dict):
            continue
        if _is_fallback_or_meta_flaw(flaw):
            meta_or_fallback_flaws += 1
        if str(flaw.get("status") or "") == "confirmed" and not _flaw_has_negative_grounding(flaw, view):
            confirmed_without_verified += 1
    snapshot["confirmed_flaw_without_verified_negative_count"] = confirmed_without_verified
    snapshot["meta_or_fallback_flaw_count"] = meta_or_fallback_flaws
    return snapshot


def _build_recovery_state_delta(before: Dict[str, Any], after: Dict[str, Any]) -> Dict[str, Any]:
    before_snapshot = _recovery_state_quality_snapshot(before)
    after_snapshot = _recovery_state_quality_snapshot(after)
    delta = {
        key: int(after_snapshot.get(key, 0) or 0) - int(before_snapshot.get(key, 0) or 0)
        for key in _RECOVERY_STATE_DELTA_KEYS
    }
    improved_keys = [key for key in _RECOVERY_BURDEN_DELTA_KEYS if delta.get(key, 0) < 0]
    worsened_keys = [key for key in _RECOVERY_BURDEN_DELTA_KEYS if delta.get(key, 0) > 0]
    tolerated_worsened_keys: List[str] = []
    if delta.get("negative_grounding_conflict_count", 0) < 0 and "assessment_limitation_flaw_count" in worsened_keys:
        # A route-to-limitation patch can legitimately repair an invalid
        # negative-evidence binding by moving a non-actionable flaw out of the
        # concern path. Count that as repair while still keeping pure
        # concern->limitation moves from becoming effective repairs.
        worsened_keys = [key for key in worsened_keys if key != "assessment_limitation_flaw_count"]
        tolerated_worsened_keys.append("assessment_limitation_flaw_count")
    return {
        "before": before_snapshot,
        "after": after_snapshot,
        "delta": delta,
        "improved_keys": sorted(improved_keys),
        "worsened_keys": sorted(worsened_keys),
        "tolerated_worsened_keys": sorted(tolerated_worsened_keys),
        "consistency_improved": bool(improved_keys and not worsened_keys),
        "negative_recovery_commit": bool(worsened_keys and not improved_keys),
    }


def _recovery_patch_operation(parsed_patch: Dict[str, Any], validation: Dict[str, Any]) -> str:
    if parsed_patch.get("action") == "blocked" or not validation.get("commit_allowed", False):
        return "reject_patch"
    target_type = str(validation.get("target_type") or parsed_patch.get("target_type") or "")
    old_status = str(validation.get("old_status") or parsed_patch.get("old_status") or "").lower()
    new_status = str(validation.get("new_status") or parsed_patch.get("new_status") or "").lower()
    if target_type == "evidence_link" and new_status in {"unbound", "invalid_claim_id"}:
        return "rebind_evidence"
    if target_type == "gap" and new_status == "resolved":
        return "resolve_stale_gap"
    if target_type == "gap" and new_status in {"converted", "not_assessable", "superseded"}:
        return "convert_negative_to_gap"
    if target_type == "flaw" and old_status == "confirmed" and new_status == "candidate":
        return "downgrade_final_to_candidate"
    if target_type == "flaw" and new_status in {"downgraded", "retracted"}:
        return "route_to_assessment_limitation"
    if target_type == "claim" and new_status == "unsupported":
        return "mark_contested"
    if target_type == "claim" and new_status in {"supported", "partially_supported"}:
        return "resolve_stale_gap"
    if target_type == "hypothesis":
        return "mark_contested"
    return "reject_patch"


def _recovery_patch_target_gate_label(parsed_patch: Dict[str, Any], validation: Dict[str, Any]) -> str:
    target_type = str(validation.get("target_type") or parsed_patch.get("target_type") or "")
    target_id = str(validation.get("target_id") or parsed_patch.get("target_id") or "")
    if not target_id:
        return "empty_target"
    raw_payload = parsed_patch.get("raw_payload") or {}
    terminal_reason = str(
        parsed_patch.get("recovery_terminal_reason")
        or raw_payload.get("recovery_terminal_reason")
        or raw_payload.get("terminal_recovery_reason")
        or ""
    ).strip()
    if (
        target_type == "flaw"
        and (
            validation.get("failure_code") == "ACTIONABLE_CONCERN_PRESERVED"
            or terminal_reason == PROTECTED_POTENTIAL_CONCERN_TERMINAL_REASON
        )
    ):
        return "negative_verified_target"
    if validation.get("failure_code") in {"UNKNOWN_TARGET", "MISSING_TARGET_ID"}:
        confidence = 0.2
        repairability = "none"
    elif validation.get("validated", False):
        confidence = 0.9
        repairability = "full" if validation.get("commit_allowed", False) else "conservative"
    else:
        confidence = 0.45
        repairability = "review"
    return _recovery_target_gate_label(
        target_type,
        target_id,
        confidence=confidence,
        repairability=repairability,
    )


def _build_recovery_patch_log(parsed_patch: Dict[str, Any], validation: Dict[str, Any]) -> Dict[str, Any]:
    failure_code = validation.get("failure_code", "")
    blocked = failure_code == "BLOCKED_BY_POLICY"
    patch_validated = bool(validation.get("validated", False)) and not blocked
    operation = _recovery_patch_operation(parsed_patch, validation)
    target_gate_label = _recovery_patch_target_gate_label(parsed_patch, validation)
    raw_payload = parsed_patch.get("raw_payload") or {}
    failure_message = str(validation.get("failure_message") or "")
    terminal_reason = str(
        parsed_patch.get("recovery_terminal_reason")
        or raw_payload.get("recovery_terminal_reason")
        or raw_payload.get("terminal_recovery_reason")
        or ""
    ).strip()
    recovery_terminal = bool(parsed_patch.get("recovery_terminal") or raw_payload.get("recovery_terminal") or raw_payload.get("terminal_recovery_block"))
    if failure_code == "ACTIONABLE_CONCERN_PRESERVED" or "final potential concern" in failure_message.lower():
        recovery_terminal = True
        terminal_reason = terminal_reason or PROTECTED_POTENTIAL_CONCERN_TERMINAL_REASON
    repeat_allowed = bool(parsed_patch.get("recovery_repeat_allowed", raw_payload.get("recovery_repeat_allowed", True)))
    if recovery_terminal:
        repeat_allowed = False
    return {
        "recovery_attempted": parsed_patch.get("is_recovery_payload", False),
        "recovery_validated": patch_validated,
        "recovery_blocked": blocked,
        "recovery_committed": bool(validation.get("commit_allowed", False)),
        "recovery_patch_operation": operation,
        "recovery_target_gate_label": target_gate_label,
        "recovery_target_commit_allowed": bool(target_gate_label == "real_target" and validation.get("commit_allowed", False)),
        "recovery_failure_code": failure_code,
        "recovery_failure_message": failure_message,
        "recovery_target_type": validation.get("target_type") or parsed_patch.get("target_type", ""),
        "recovery_target_id": validation.get("target_id") or parsed_patch.get("target_id", ""),
        "old_status": validation.get("old_status") or parsed_patch.get("old_status", ""),
        "new_status": validation.get("new_status") or parsed_patch.get("new_status", ""),
        "status_normalized_from": validation.get("status_normalized_from", ""),
        "status_normalized_to": validation.get("status_normalized_to", ""),
        "normalization_reason": validation.get("normalization_reason", ""),
        "supporting_evidence_ids": _strip_synthetic_recovery_markers(
            list(validation.get("supporting_evidence_ids", parsed_patch.get("supporting_evidence_ids", [])) or [])
        ),
        "resolved_conflict_count": int(validation.get("resolved_conflict_count", 0) or 0),
        "required_fix": validation.get("required_fix", ""),
        "missing_requirements": list(validation.get("missing_requirements", parsed_patch.get("missing_requirements", [])) or []),
        "recovery_patch_source": parsed_patch.get("recovery_patch_source", "none"),
        "recovery_terminal": recovery_terminal,
        "recovery_terminal_reason": terminal_reason,
        "recovery_repeat_allowed": repeat_allowed,
        "recovery_state_delta": {},
        "recovery_consistency_improved": False,
        "negative_recovery_commit": False,
    }


def _status_lock_key(entity_type: str, entity_id: str) -> str:
    return f"{entity_type}:{entity_id}".strip(":")


def _set_transient_status_lock(state: Dict[str, Any], entity_type: str, entity_id: str, status: str) -> None:
    if not entity_id or not status:
        return
    locks = dict(state.get("_transient_status_locks", {}) or {})
    locks[_status_lock_key(entity_type, entity_id)] = status
    state["_transient_status_locks"] = locks


def _set_persistent_status_guard(state: Dict[str, Any], entity_type: str, entity_id: str, status: str) -> None:
    if not entity_id or not status:
        return
    guards = dict(state.get("_persistent_status_guards", {}) or {})
    guards[_status_lock_key(entity_type, entity_id)] = status
    state["_persistent_status_guards"] = guards


def _apply_status_guards(
    items: List[Dict[str, Any]],
    key: str,
    entity_type: str,
    guards: Dict[str, str],
) -> List[Dict[str, Any]]:
    if not guards:
        return items
    protected: List[Dict[str, Any]] = []
    for item in items:
        updated = copy.deepcopy(item)
        item_id = str(updated.get(key, "") or "")
        guarded_status = guards.get(_status_lock_key(entity_type, item_id))
        if guarded_status and updated.get("status") != guarded_status:
            updated["status"] = guarded_status
        protected.append(updated)
    return protected


def _refresh_stale_claim_downgrade_old_status(state: Dict[str, Any], parsed_patch: Dict[str, Any]) -> None:
    """Hydration before emit: align a claim-downgrade patch's stale ``old_status``
    with the live ReviewState status so the recovery validator decides commit vs
    block on evidence merits rather than on a stale-status technicality.

    Only claim patches targeting ``unsupported`` are touched, and only when the
    live status -> unsupported transition is itself a legal recovery transition.
    The verified-negative-evidence requirement in the validator is unchanged.
    """
    if not isinstance(parsed_patch, dict):
        return
    if str(parsed_patch.get("target_type") or "").strip().lower() != "claim":
        return
    if str(parsed_patch.get("new_status") or "").strip().lower() != "unsupported":
        return
    target_id = str(parsed_patch.get("target_id") or "").strip()
    if not target_id:
        return
    live_status = ""
    for claim in state.get("claims", []) or []:
        if isinstance(claim, dict) and str(claim.get("claim_id") or "").strip() == target_id:
            live_status = str(claim.get("status") or "").strip().lower()
            break
    if not live_status:
        return
    old_status = str(parsed_patch.get("old_status") or "").strip().lower()
    if old_status == live_status:
        return
    allowed = RECOVERY_STATUS_TRANSITIONS.get("claim", {})
    if "unsupported" not in allowed.get(live_status, set()):
        return
    parsed_patch["old_status"] = live_status
    parsed_patch["old_status_refreshed_from"] = old_status


def _flaw_limitation_patch_is_no_effect(state: Dict[str, Any], validation: Dict[str, Any], new_status: str) -> bool:
    if str(validation.get("target_type") or "") != "flaw":
        return False
    if str(new_status or "").strip().lower() not in {"downgraded", "retracted"}:
        return False
    if not list(validation.get("supporting_evidence_ids", []) or []):
        return False
    target_id = str(validation.get("target_id") or "").strip()
    if not target_id:
        return False
    try:
        view_state = copy.deepcopy(state or {})
        view_state.pop("decision_hygiene", None)
        view = build_decision_hygiene_view(view_state)
    except Exception:  # pragma: no cover - commit guard must not crash recovery
        return False
    for flaw in view.get("flaw_candidates", []) or []:
        if not isinstance(flaw, dict) or str(flaw.get("flaw_id") or "").strip() != target_id:
            continue
        layer = str(flaw.get("final_view_flaw_layer") or "").strip()
        conflicts = flaw.get("hygiene_negative_grounding_conflicts") or []
        return layer == "assessment_limitation" and not bool(conflicts)
    return False


def _apply_recovery_update(state: Dict[str, Any], payload: Dict[str, Any]) -> Dict[str, Any]:
    parsed_patch = parse_recovery_payload(payload)
    _refresh_stale_claim_downgrade_old_status(state, parsed_patch)
    validation = validate_recovery_patch(state, parsed_patch)
    merged = copy.deepcopy(state)
    merged["_latest_patch_log"] = _build_recovery_patch_log(parsed_patch, validation)

    if not validation.get("commit_allowed"):
        return merged

    target_field = validation.get("target_field")
    target_index = validation.get("target_index")
    new_status = str(validation.get("new_status") or parsed_patch.get("new_status") or "").lower()
    if _flaw_limitation_patch_is_no_effect(state, validation, new_status):
        merged["_latest_patch_log"].update(
            {
                "recovery_validated": False,
                "recovery_blocked": True,
                "recovery_committed": False,
                "recovery_patch_operation": "reject_patch",
                "recovery_failure_code": "BLOCKED_BY_POLICY",
                "recovery_failure_message": (
                    "Recovery patch was blocked because the target flaw is already an assessment limitation "
                    "with no remaining negative-grounding conflict; committing it would be a no-effect lifecycle change."
                ),
                "required_fix": "Choose a target with a remaining grounding conflict or an over-escalated confirmed concern.",
                "recovery_target_commit_allowed": False,
            }
        )
        return merged
    # Capture the pre-mutation status so we can emit a structured revision
    # event after a successful commit.  Without this, the env-level
    # ``revision_log`` diff-tracker treats every recovery commit as a
    # no-op state change, which falsely zeroes out the
    # ``recovery_layer_state_mutation_applied`` counter even when the
    # ReviewState entity really transitioned (root cause of the
    # ``recovery_committed`` vs ``recovery_success`` measurement gap
    # surfaced by the V16 audit).
    target_entity_type = ""
    target_entity_id = ""
    pre_status_value: Any = ""
    if target_field == "current_hypotheses":
        target_entity_type = "current_hypothesis"
        try:
            hypotheses_pre = list(merged.get("current_hypotheses", []) or [])
            pre_status_value = hypotheses_pre[int(target_index)] if target_index is not None else ""
        except (IndexError, TypeError, ValueError):
            pre_status_value = ""
        target_entity_id = f"index-{target_index}" if target_index is not None else ""
    elif target_field in {"claims", "flaw_candidates"}:
        target_entity_type = "claim" if target_field == "claims" else "flaw"
        try:
            items_pre = list(merged.get(target_field, []) or [])
            pre_item = items_pre[int(target_index)] if target_index is not None else {}
            pre_status_value = str(pre_item.get("status") or "")
        except (IndexError, TypeError, ValueError):
            pre_status_value = ""
        target_entity_id = str(validation.get("target_id") or parsed_patch.get("target_id") or "")
    elif target_field in {"evidence_map", "evidence_gaps"}:
        target_entity_type = "evidence_link" if target_field == "evidence_map" else "gap"
        try:
            items_pre = list(merged.get(target_field, []) or [])
            pre_item = items_pre[int(target_index)] if target_index is not None else {}
            if target_field == "evidence_map":
                pre_status_value = str(pre_item.get("binding_status") or ("bound" if pre_item.get("claim_id") else "unbound"))
            else:
                pre_status_value = str(pre_item.get("status") or "open")
        except (IndexError, TypeError, ValueError):
            pre_status_value = ""
        target_entity_id = str(validation.get("target_id") or parsed_patch.get("target_id") or "")

    try:
        if target_field == "current_hypotheses":
            hypotheses = list(merged.get("current_hypotheses", []) or [])
            hypotheses[int(target_index)] = _format_hypothesis_status_text(hypotheses[int(target_index)], new_status)
            merged["current_hypotheses"] = hypotheses
        elif target_field in {"claims", "flaw_candidates"}:
            items = list(merged.get(target_field, []) or [])
            items[int(target_index)]["status"] = new_status
            merged[target_field] = items
            target_id = str(validation.get("target_id") or parsed_patch.get("target_id") or "")
            if target_field == "claims":
                _set_transient_status_lock(merged, "claim", target_id, new_status)
                _set_persistent_status_guard(merged, "claim", target_id, new_status)
            elif target_field == "flaw_candidates":
                _set_transient_status_lock(merged, "flaw", target_id, new_status)
                _set_persistent_status_guard(merged, "flaw", target_id, new_status)
        elif target_field == "evidence_map":
            items = list(merged.get("evidence_map", []) or [])
            item = dict(items[int(target_index)])
            item["binding_status"] = new_status
            item["recovery_binding_resolution"] = parsed_patch.get("reason_for_change") or "recovery_patch_committed"
            if new_status in {"unbound", "invalid_claim_id"}:
                previous_claim_id = str(item.get("claim_id") or "")
                if previous_claim_id and not item.get("original_claim_id"):
                    item["original_claim_id"] = previous_claim_id
                item["claim_id"] = ""
            items[int(target_index)] = item
            merged["evidence_map"] = items
        elif target_field == "evidence_gaps":
            items = list(merged.get("evidence_gaps", []) or [])
            item = dict(items[int(target_index)])
            item["status"] = new_status
            if parsed_patch.get("supporting_evidence_ids"):
                item["evidence_id"] = str((parsed_patch.get("supporting_evidence_ids") or [""])[0] or "")
            item["resolution"] = parsed_patch.get("reason_for_change") or "recovery_patch_committed"
            items[int(target_index)] = item
            merged["evidence_gaps"] = _normalize_evidence_gaps(items, max_items=10)
        else:
            merged["_latest_patch_log"]["recovery_committed"] = False
            merged["_latest_patch_log"]["recovery_failure_code"] = "CHECKER_TOO_STRICT"
            merged["_latest_patch_log"]["recovery_failure_message"] = f"Unknown target_field returned by recovery validator: {target_field}"
            return merged
    except Exception as exc:  # pragma: no cover - defensive state-commit guard
        merged["_latest_patch_log"]["recovery_committed"] = False
        merged["_latest_patch_log"]["recovery_failure_code"] = "CHECKER_TOO_STRICT"
        merged["_latest_patch_log"]["recovery_failure_message"] = f"Recovery state commit failed: {exc}"
        return merged

    resolved_conflict_ids = list(validation.get("matched_conflict_ids", []) or parsed_patch.get("conflict_note_ids", []) or [])
    if resolved_conflict_ids:
        resolved_set = set(resolved_conflict_ids)
        merged["conflict_notes"] = [
            note
            for note in merged.get("conflict_notes", [])
            if str(note.get("conflict_id") or "") not in resolved_set
        ]

    # Record the recovery-induced status transition on the canonical
    # ``revision_log`` so downstream collectors (env diff-tracker,
    # ``_classify_revision_events`` in ``build_review_turn_log``) can detect
    # the state mutation alongside ordinary merge revisions.
    if target_entity_type and target_entity_id:
        recovery_revisions: List[Dict[str, Any]] = []
        post_status_value: Any
        if target_field == "current_hypotheses":
            try:
                post_status_value = list(merged.get("current_hypotheses", []) or [])[int(target_index)]
            except (IndexError, TypeError, ValueError):
                post_status_value = ""
        else:
            post_status_value = new_status
        if pre_status_value != post_status_value:
            _append_revision_event(
                recovery_revisions,
                target_entity_type,
                target_entity_id,
                "status",
                pre_status_value,
                post_status_value,
                reason="recovery_patch_committed",
            )
        if recovery_revisions:
            merged["revision_log"] = (merged.get("revision_log", []) + recovery_revisions)[-40:]
            merged = _update_state_summaries(merged)

    recovery_state_delta = _build_recovery_state_delta(state, merged)
    merged["_latest_patch_log"]["recovery_state_delta"] = recovery_state_delta
    merged["_latest_patch_log"]["recovery_consistency_improved"] = bool(recovery_state_delta.get("consistency_improved", False))
    merged["_latest_patch_log"]["negative_recovery_commit"] = bool(recovery_state_delta.get("negative_recovery_commit", False))

    return merged


def merge_review_state(state: Dict[str, Any], payload: Dict[str, Any]) -> Dict[str, Any]:
    if looks_like_recovery_payload(payload):
        return _apply_recovery_update(state, payload)

    normalized_payload = dict(payload)
    normalized_payload.update(normalize_review_update_payload(payload))

    merged = copy.deepcopy(state)
    transient_status_locks = dict(merged.get("_transient_status_locks", {}) or {})
    persistent_status_guards = dict(merged.get("_persistent_status_guards", {}) or {})
    combined_status_guards = {**persistent_status_guards, **transient_status_locks}
    if combined_status_guards:
        normalized_payload["claims"] = _apply_status_guards(
            normalized_payload.get("claims", []),
            key="claim_id",
            entity_type="claim",
            guards=combined_status_guards,
        )
        normalized_payload["flaw_candidates"] = _apply_status_guards(
            normalized_payload.get("flaw_candidates", []),
            key="flaw_id",
            entity_type="flaw",
            guards=combined_status_guards,
        )

    revision_events: List[Dict[str, Any]] = []
    conflict_events: List[Dict[str, Any]] = []

    merged["claims"], claim_revisions, claim_lifecycle_conflicts = _merge_items_with_revisions(
        merged.get("claims", []),
        normalized_payload.get("claims", []),
        key="claim_id",
        entity_type="claim",
        tracked_fields=("claim", "importance", "status", "claim_type", "claim_kind", "claim_origin", "claim_origin_kind", "claim_source", "claim_extraction_source", "evidence_need", "coverage_tags", "supporting_evidence_ids"),
        max_items=8,
    )
    revision_events.extend(claim_revisions)
    conflict_events.extend(claim_lifecycle_conflicts)

    normalized_payload["evidence_map"] = _validate_evidence_bindings_for_state(
        merged,
        normalized_payload.get("evidence_map", []),
    )
    normalized_payload["evidence_map"] = _verify_evidence_items_for_state(
        merged,
        normalized_payload.get("evidence_map", []),
    )
    if ENABLE_EVIDENCE_ID_COLLISION_PRESERVATION:
        normalized_payload["evidence_map"], evidence_id_renames, _evidence_collision_count = _preserve_colliding_evidence_ids(
            merged.get("evidence_map", []),
            normalized_payload.get("evidence_map", []),
        )
        _rewrite_evidence_references_for_renamed_ids(normalized_payload, evidence_id_renames)

    merged["evidence_map"], evidence_revisions, evidence_lifecycle_conflicts = _merge_items_with_revisions(
        merged.get("evidence_map", []),
        normalized_payload.get("evidence_map", []),
        key="evidence_id",
        entity_type="evidence",
        tracked_fields=("claim_id", "evidence", "source", "source_locator", "raw_quote", "agent_raw_quote", "quote_id", "quote_bank_canonicalized", "quote_bank_claim_overlap_fallback_used", "quote_bank_claim_overlap_fallback_quote_id", "quote_bank_claim_overlap_fallback_source_bucket", "quote_bank_claim_overlap_fallback_score", "source_span_start", "source_span_end", "strength", "stance", "binding_status", "binding_confidence", "binding_rationale", "grounded_judge_label", "grounded_judge_reason", "verified_grounding_label", "verified_grounding_reason", "verified_source_span_start", "verified_source_span_end", "verified_quote_match_type", "verified_locator_quality", "verified_source_bucket", "verified_claim_overlap_score", "semantic_grounding_label", "semantic_grounding_reasons", "semantic_alignment_score", "semantic_grounding_checked", "quote_evidence_semantic_mismatch", "semantic_weak_promotion_used", "semantic_weak_promotion_reason", "support_source_bucket", "negative_evidence_type", "negative_evidence_actionability", "claim_status_downgrade_allowed", "support_quality", "support_quality_reason", "support_quality_adjustment", "strength_promotion_from_medium_used", "strength_promotion_reason", "original_evidence_id", "evidence_id_collision_preserved", "evidence_id_collision_reason"),
        max_items=64,
    )
    merged["evidence_map"] = _retain_evidence_items(merged.get("evidence_map", []), max_items=12)
    revision_events.extend(evidence_revisions)
    conflict_events.extend(evidence_lifecycle_conflicts)

    merged["flaw_candidates"], flaw_revisions, flaw_lifecycle_conflicts = _merge_items_with_revisions(
        merged.get("flaw_candidates", []),
        normalized_payload.get("flaw_candidates", []),
        key="flaw_id",
        entity_type="flaw",
        tracked_fields=("title", "description", "severity", "status", "related_claim_ids", "evidence_ids", "negative_evidence_ids", "verified_negative_evidence_ids", "grounding_status", "source"),
        max_items=8,
    )
    revision_events.extend(flaw_revisions)
    conflict_events.extend(flaw_lifecycle_conflicts)

    merged["unresolved_questions"], question_revisions, question_lifecycle_conflicts = _merge_question_items(
        merged.get("unresolved_questions", []),
        normalized_payload.get("unresolved_questions", []),
    )
    revision_events.extend(question_revisions)
    conflict_events.extend(question_lifecycle_conflicts)

    pending_conflicts = (
        claim_lifecycle_conflicts
        + evidence_lifecycle_conflicts
        + flaw_lifecycle_conflicts
        + question_lifecycle_conflicts
        + normalized_payload.get("conflict_notes", [])
    )
    merged["conflict_notes"], explicit_conflicts = _merge_conflict_notes(
        merged.get("conflict_notes", []),
        pending_conflicts,
        max_items=12,
    )
    conflict_events.extend(explicit_conflicts)

    derived_conflicts = []
    known_claim_ids = {claim.get("claim_id", "") for claim in merged.get("claims", [])}
    for evidence in normalized_payload.get("evidence_map", []):
        if evidence.get("stance") == "contradicts" and evidence.get("claim_id") in known_claim_ids:
            derived_conflicts.append(
                {
                    "conflict_id": _slugify("conflict", f"{evidence.get('claim_id', '')}-{evidence.get('evidence_id', '')}", len(derived_conflicts) + 1),
                    "note": (
                        f"Evidence {evidence.get('evidence_id', '')} conflicts with claim {evidence.get('claim_id', '')}."
                        if evidence.get("source") == "fallback-extraction"
                        else f"Evidence {evidence.get('evidence_id', '')} conflicts with claim {evidence.get('claim_id', '')}: {_sanitize_conflict_excerpt(evidence.get('evidence', ''))}"
                    ),
                    "claim_id": evidence.get("claim_id", ""),
                    "evidence_id": evidence.get("evidence_id", ""),
                    "flaw_id": "",
                }
            )
    for flaw in normalized_payload.get("flaw_candidates", []):
        if flaw.get("status") in {"downgraded", "retracted"}:
            derived_conflicts.append(
                {
                    "conflict_id": _slugify("conflict", f"{flaw.get('flaw_id', '')}-{flaw.get('status', '')}", len(derived_conflicts) + 1),
                    "note": f"Flaw {flaw.get('flaw_id', '')} was {flaw.get('status', '')}, indicating its earlier support weakened.",
                    "claim_id": (flaw.get("related_claim_ids") or [""])[0],
                    "evidence_id": (flaw.get("evidence_ids") or [""])[0],
                    "flaw_id": flaw.get("flaw_id", ""),
                }
            )
    merged["conflict_notes"], derived_conflict_events = _merge_conflict_notes(
        merged.get("conflict_notes", []),
        _normalize_conflicts(derived_conflicts),
        max_items=12,
    )
    conflict_events.extend(derived_conflict_events)

    merged["evidence_gaps"] = _merge_evidence_gaps(
        merged.get("evidence_gaps", []),
        normalized_payload.get("evidence_gaps", []),
        max_items=10,
    )

    merged_hypotheses = merged.get("current_hypotheses", []) + normalized_payload.get("current_hypotheses", [])
    merged["current_hypotheses"] = _normalize_list_of_strings(merged_hypotheses, max_items=8, max_length=240)

    dialogue_summary = _normalize_text(payload.get("summary_update") or payload.get("dialogue_summary"), max_length=1000)
    if dialogue_summary:
        merged["dialogue_summary"] = dialogue_summary

    pending_user_question = _normalize_text(payload.get("pending_user_question") or payload.get("clarification_question"), max_length=400)
    if pending_user_question:
        merged["pending_user_question"] = pending_user_question
    simulated_user_reply = _normalize_text(payload.get("simulated_user_reply"), max_length=400)
    if simulated_user_reply:
        merged["simulated_user_reply"] = simulated_user_reply
        merged["clarification_needed"] = False
        if merged.get("pending_user_question"):
            merged["unresolved_questions"], clarification_revisions, clarification_conflicts = _merge_question_items(
                merged.get("unresolved_questions", []),
                [
                    {
                        "question_id": _slugify("question", merged["pending_user_question"], 1),
                        "question": merged["pending_user_question"],
                        "status": "resolved",
                        "related_claim_ids": [],
                    }
                ],
            )
            revision_events.extend(clarification_revisions)
            conflict_events.extend(clarification_conflicts)
            merged["pending_user_question"] = ""
    if "clarification_needed" in payload or "requires_clarification" in payload:
        merged["clarification_needed"] = bool(payload.get("clarification_needed") or payload.get("requires_clarification"))
        if merged.get("clarification_needed") and merged.get("pending_user_question"):
            merged["unresolved_questions"], clarification_revisions, clarification_conflicts = _merge_question_items(
                merged.get("unresolved_questions", []),
                [
                    {
                        "question_id": _slugify("question", merged["pending_user_question"], 1),
                        "question": merged["pending_user_question"],
                        "status": "open",
                        "related_claim_ids": [],
                    }
                ],
            )
            revision_events.extend(clarification_revisions)
            conflict_events.extend(clarification_conflicts)

    active_focus = _normalize_text(payload.get("active_focus") or payload.get("focus"), max_length=400)
    if active_focus:
        merged["active_focus"] = active_focus

    recommendation = _normalize_choice(payload.get("recommendation"), FINAL_DECISIONS, "undecided")
    if recommendation != "undecided":
        merged["final_decision"] = recommendation

    merged, consistency_revisions, consistency_conflicts = _refresh_state_consistency(merged)
    revision_events.extend(consistency_revisions)
    conflict_events.extend(consistency_conflicts)

    if revision_events:
        merged["revision_log"] = (merged.get("revision_log", []) + revision_events)[-40:]
    else:
        merged["revision_log"] = merged.get("revision_log", [])

    merged = _update_state_summaries(merged)
    return merged


def build_turn_action(
    manager_payload: Dict[str, Any],
    worker_payloads: List[Dict[str, Any]],
    mode: str,
    turn_id: int,
) -> str:
    return json.dumps(
        {
            "mode": mode,
            "turn_id": turn_id,
            "manager": manager_payload,
            "workers": worker_payloads,
        },
        ensure_ascii=False,
        sort_keys=True,
    )


def _manager_requires_negative_evidence_formation(manager_payload: Dict[str, Any]) -> bool:
    policy_source = str((manager_payload or {}).get("policy_source") or "").strip()
    return bool(
        (manager_payload or {}).get("negative_evidence_formation_required")
        or policy_source in {"negative_evidence_formation_override", "hard_negative_discovery_override"}
    )


def _filter_positive_evidence_for_negative_formation(agent_id: str, payload: Dict[str, Any], manager_payload: Dict[str, Any]) -> Dict[str, Any]:
    if agent_id != "Evidence Agent" or not _manager_requires_negative_evidence_formation(manager_payload):
        return payload
    evidence_items = [item for item in payload.get("evidence_map", []) or [] if isinstance(item, dict)]
    kept = [item for item in evidence_items if _is_negative_evidence_record(item)]
    if len(kept) == len(evidence_items):
        return payload
    updated = dict(payload)
    updated["evidence_map"] = kept
    notes = list(updated.get("unresolved_questions") or [])
    notes.append(
        {
            "question_id": "question-negative-evidence-positive-filtered",
            # P0-4: question_id stays for machine-readable lifecycle, but the
            # human-facing text is paper-side / reviewer-neutral so it does
            # not leak "filtered" / "hard-negative" / "system" terms into
            # the user_report.
            "question": "Verified paper-negative evidence has not yet been located for the target concern.",
            "status": "open",
            "related_claim_ids": [],
        }
    )
    updated["unresolved_questions"] = notes[:8]
    return normalize_review_update_payload(updated)


def parse_turn_action(action: str, available_agents: Optional[Iterable[str]] = None) -> Dict[str, Any]:
    try:
        payload = json.loads(action)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid review action JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError("Review action must be a JSON object.")

    manager_payload = normalize_manager_payload(payload.get("manager", {}), available_agents)
    workers: List[Dict[str, Any]] = []
    for worker in payload.get("workers", []):
        if not isinstance(worker, dict):
            continue
        agent_id = _normalize_text(worker.get("agent_id"), max_length=120)
        if not agent_id:
            continue
        worker_payload = normalize_review_update_payload(worker.get("payload", {}))
        worker_payload = _filter_positive_evidence_for_negative_formation(agent_id, worker_payload, manager_payload)
        workers.append(
            {
                "agent_id": agent_id,
                "payload": worker_payload,
            }
        )

    return {
        "mode": _normalize_text(payload.get("mode"), default="s4", max_length=8).lower(),
        "turn_id": int(payload.get("turn_id", 0)),
        "manager": manager_payload,
        "workers": workers,
    }


def infer_review_mode(explicit_mode: Optional[str], agent_ids: List[str], max_steps: int) -> str:
    if explicit_mode:
        normalized = explicit_mode.lower()
        if normalized in REVIEW_MODES:
            return normalized
    worker_ids = [agent_id for agent_id in agent_ids if agent_id not in {"Review Manager Agent", "Meta Reviewer Agent"}]
    if len(agent_ids) == 1 and max_steps <= 1:
        return "s1"
    if len(agent_ids) == 1:
        return "s2"
    generalist_names = {"Reviewer Agent", "General Reviewer Agent 1", "General Reviewer Agent 2", "General Reviewer Agent 3"}
    if worker_ids and set(worker_ids).issubset(generalist_names):
        return "s3"
    return "s4"


def compact_review_state_for_prompt(state: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "turn_id": state.get("turn_id", 0),
        "mode": state.get("mode", "s4"),
        "phase": state.get("phase", "normal_review"),
        "phase_turn_index": state.get("phase_turn_index", 0),
        "phase_enter_reason": state.get("phase_enter_reason", ""),
        "phase_exit_reason": state.get("phase_exit_reason", ""),
        "phase_hold_reason": state.get("phase_hold_reason", ""),
        "sticky_target_id": state.get("sticky_target_id", ""),
        "sticky_target_type": state.get("sticky_target_type", ""),
        "sticky_target_active": state.get("sticky_target_active", False),
        "sticky_target_turns_remaining": state.get("sticky_target_turns_remaining", 0),
        "sticky_release_reason": state.get("sticky_release_reason", ""),
        "dialogue_summary": state.get("dialogue_summary", ""),
        "last_focus": state.get("last_focus", ""),
        "active_focus": state.get("active_focus", state.get("last_focus", "")),
        "claim_coverage": claim_coverage_summary(state),
        "claims": state.get("claims", [])[:5],
        "evidence_map": _compact_evidence_for_prompt(state.get("evidence_map", []), max_items=6),
        "flaw_candidates": state.get("flaw_candidates", [])[:5],
        "unresolved_questions": state.get("unresolved_questions", [])[:6],
        "evidence_gaps": _open_evidence_gaps(state)[:6],
        "current_hypotheses": state.get("current_hypotheses", [])[:5],
        "revision_summary": state.get("revision_summary", [])[:4],
        "conflict_summary": state.get("conflict_summary", [])[:4],
        "risk_profile": copy.deepcopy(state.get("risk_profile", {})),
        "pending_user_question": state.get("pending_user_question", ""),
        "simulated_user_reply": state.get("simulated_user_reply", ""),
        "clarification_needed": state.get("clarification_needed", False),
        "conflict_notes": state.get("conflict_notes", [])[-4:],
        "revision_log": state.get("revision_log", [])[-4:],
        "final_decision": state.get("final_decision", "undecided"),
    }

def _render_review_header(task: Dict[str, Any]) -> str:
    return (
        f"# Review Task\n"
        f"Paper ID: {task['paper_id']}\n"
        f"Mode: {task['mode']}\n"
        f"Current Turn: {task['review_state']['turn_id'] + 1}/{task['max_turns']}\n"
        f"User Goal: {task['user_goal']}\n"
    )


def _render_recent_turn_summary(task: Dict[str, Any], max_items: int = 2) -> str:
    recent_logs = task.get("turn_logs", [])[-max_items:]
    recent_log_lines = []
    for item in recent_logs:
        decision = item.get("decision", "continue")
        agents = ", ".join(item.get("selected_agents", [])) or "manager-only"
        focus = item.get("focus") or "no explicit focus"
        recent_log_lines.append(f"Turn {item.get('turn_id', 0)}: decision={decision}; agents={agents}; focus={focus}")
    return "\n".join(recent_log_lines) if recent_log_lines else "No previous turns."


def _render_focus_context(state: Dict[str, Any], fallback_focus: str = "") -> str:
    active_focus = state.get("active_focus") or state.get("last_focus") or fallback_focus or "No explicit focus yet."
    return (
        f"Active Focus: {active_focus}\n"
        f"Dialogue Summary: {state.get('dialogue_summary') or 'No dialogue summary yet.'}"
    )


def _render_paper_excerpt(task: Dict[str, Any], max_length: int = 1200) -> str:
    paper_text = _normalize_text(task.get("paper_text"), max_length=max_length * 3)
    if not paper_text:
        return "No paper text available."
    return paper_text[:max_length]


def _clean_paper_body(text: str) -> Tuple[str, bool]:
    # Preserve line breaks here so section-header based evidence context
    # selection can distinguish real Method/Results sections from abstract
    # mentions. Snippets are whitespace-normalized later when rendered.
    raw = str(text or "").strip()[:64000]
    if not raw:
        return "", False
    cleaned_wrapper = False
    if raw.startswith("[") and '"role"' in raw and '"content"' in raw:
        try:
            messages = json.loads(raw)
        except Exception:
            messages = None
        if isinstance(messages, list):
            user_contents = [
                str(item.get("content") or "")
                for item in messages
                if isinstance(item, dict) and item.get("role") == "user" and item.get("content")
            ]
            if user_contents:
                raw = "\n".join(user_contents)[:64000]
                cleaned_wrapper = True
    begin_match = re.search(r"---\s*BEGIN\s+PAPER\s*---", raw, flags=re.IGNORECASE)
    end_match = re.search(r"---\s*END\s+PAPER\s*---", raw, flags=re.IGNORECASE)
    if begin_match:
        raw = raw[begin_match.end():]
        cleaned_wrapper = True
    if end_match:
        # Recompute after begin trimming because positions may have changed.
        end_match = re.search(r"---\s*END\s+PAPER\s*---", raw, flags=re.IGNORECASE)
        if end_match:
            raw = raw[:end_match.start()]
            cleaned_wrapper = True
    lines = []
    skip_prefixes = ("[instruction]", "format requirements", "you are", "return json", "output json")
    for line in raw.splitlines():
        stripped = line.strip()
        low = stripped.lower()
        if not stripped:
            continue
        if any(low.startswith(prefix) for prefix in skip_prefixes):
            cleaned_wrapper = True
            continue
        lines.append(stripped)
    return "\n".join(lines).strip(), cleaned_wrapper


_EVIDENCE_SECTION_PATTERNS: List[Tuple[str, re.Pattern[str]]] = [
    ("abstract", re.compile(r"\babstract\b", re.IGNORECASE)),
    ("method", re.compile(r"\b(method|methods|methodology|approach|model|framework)\b", re.IGNORECASE)),
    ("results", re.compile(r"\b(experiment|experiments|evaluation|results|analysis)\b", re.IGNORECASE)),
    ("table_or_figure", re.compile(r"\b(table|figure|ablation)\b", re.IGNORECASE)),
    ("conclusion", re.compile(r"\b(conclusion|conclusions|discussion)\b", re.IGNORECASE)),
]

_SECTION_HEADER_PREFIX = r"(?:^|\n)\s*(?:#{1,6}\s*)?(?:\d+(?:\.\d+)*\.?\s*)?"
_LATEX_SECTION_PREFIX = r"(?:^|\n)\s*\\(?:sub)*section\*?\{[^}]*"
_EVIDENCE_SECTION_HEADER_PATTERNS: List[Tuple[str, re.Pattern[str]]] = [
    ("method", re.compile(_LATEX_SECTION_PREFIX + r"\b(method|methods|methodology|approach|model|framework|architecture)\b[^}]*\}", re.IGNORECASE)),
    ("results", re.compile(_LATEX_SECTION_PREFIX + r"\b(experiment|experiments|evaluation|evaluations|results|analysis|benchmark)\b[^}]*\}", re.IGNORECASE)),
    ("table_or_figure", re.compile(_LATEX_SECTION_PREFIX + r"\b(ablation|tables?|figures?)\b[^}]*\}", re.IGNORECASE)),
    ("theory_or_proof", re.compile(_LATEX_SECTION_PREFIX + r"\b(theory|theorem|proof|analysis|convergence|generalization)\b[^}]*\}", re.IGNORECASE)),
    ("conclusion", re.compile(_LATEX_SECTION_PREFIX + r"\b(conclusion|conclusions|discussion)\b[^}]*\}", re.IGNORECASE)),
    ("method", re.compile(_SECTION_HEADER_PREFIX + r"(method|methods|methodology|approach|model|framework)\s*[:.\-]?\s*(?:\n|$)", re.IGNORECASE)),
    ("results", re.compile(_SECTION_HEADER_PREFIX + r"(experiment|experiments|evaluation|evaluations|results|analysis)\s*[:.\-]?\s*(?:\n|$)", re.IGNORECASE)),
    ("table_or_figure", re.compile(_SECTION_HEADER_PREFIX + r"(ablation|tables?|figures?)\s*[:.\-]?\s*(?:\n|$)", re.IGNORECASE)),
    ("theory_or_proof", re.compile(_SECTION_HEADER_PREFIX + r"(theory|theorem|proof|analysis|convergence|generalization)\s*[:.\-]?\s*(?:\n|$)", re.IGNORECASE)),
    ("conclusion", re.compile(_SECTION_HEADER_PREFIX + r"(conclusion|conclusions|discussion)\s*[:.\-]?\s*(?:\n|$)", re.IGNORECASE)),
]
_EVIDENCE_DETAIL_ANCHOR_PATTERNS: List[Tuple[str, re.Pattern[str]]] = [
    (
        "ablation",
        re.compile(
            r"\b(ablation study|ablation results?|ablation analysis|without (?:the )?\w+ module|remove(?:d|s)? (?:the )?\w+ module)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "comparison",
        re.compile(
            r"\b(compare(?:d|s)? with|comparison with|baseline(?:s)?|state-of-the-art|sota|outperform(?:s|ed)?|surpass(?:es|ed)?|better than|robustness|sensitivity)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "table_or_figure",
        re.compile(
            r"(?:^|\n)\s*(?:Table|Figure|Fig\.)\s*\d+\s*[:.\-]|\\begin\{(?:table|figure)\}|\\caption\{",
            re.IGNORECASE,
        ),
    ),
    (
        "results",
        re.compile(
            r"\b(outperform(?:s|ed)?|surpass(?:es|ed)?|improv(?:e|es|ed|ement)|achiev(?:e|es|ed)|accuracy|f1|auc|mse|rmse|bleu|rouge|"
            r"win rate|success rate|baseline|state-of-the-art|sota|performance|mean square error|benchmark result|"
            r"mrr|hits@?\d+|pass@?\d+|exact match|speedup|latency|throughput|tokens? per second|"
            r"segmentation|tracking|detection|recognition|miou|map|psnr|ssim|fid|clip score|"
            r"validity|qed|docking|molecule|drug design|link prediction|node classification|knowledge graph reasoning)\b|\d+(?:\.\d+)?\s*%",
            re.IGNORECASE,
        ),
    ),
    (
        "method",
        re.compile(
            r"\b(speculative decoding|candidate length|routing|preference-conditioned|instruction tuning|role-playing|knowledge graph|message passing|graph neural|diffusion model|denoising|masked autoencoding)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "theory_or_proof",
        re.compile(
            r"\b(theorem|lemma|proposition|corollary|proof|provably|convergence|generalization bound|sample complexity|regret bound|neural collapse)\b",
            re.IGNORECASE,
        ),
    ),
]
_EVIDENCE_NEGATIVE_ANCHOR_PATTERNS: List[Tuple[str, re.Pattern[str]]] = [
    (
        "negative_or_gap",
        re.compile(
            r"\b("
            r"no\s+(?:ablation|baseline|comparison|evaluation)|"
            r"missing\s+(?:ablation|baseline|comparison|evaluation)|"
            r"not\s+(?:evaluated|compared|significant)|no\s+significant|"
            r"(?:do|does|did)\s+not\s+(?:report|provide|include|evaluate|compare|validate|establish|show)\b|"
            r"lack(?:s|ed|ing)?\s+(?:ablation|baseline|comparison|evaluation|implementation|detail)|"
            r"insufficient\s+(?:evaluation|experiment|baseline|comparison|detail)|"
            r"worse|underperform(?:s|ed)?|fail(?:s|ed)?\s+to\s+(?:show|evaluate|compare|generalize|generalise)|"
            r"threats?\s+to\s+validity|future\s+work|limitation|limitations"
            r")\b",
            re.IGNORECASE,
        ),
    ),
]

# P0-4 diagnostic typing: classify each `negative_or_gap` quote into one of 5
# deterministic categories. THIS IS LABEL-ONLY — no noise filter, no flow
# gating, no grounded_weakness restriction. Downstream code may inspect the
# `negative_evidence_type` field for analysis/audit purposes only.
_NEG_TYPE_DIRECT_CONTRADICTION_RE = re.compile(
    r"\b(contradict(?:s|ed|ory)?|inconsistent with|fail(?:s|ed)? to (?:prove|hold|show|generalize|generalise|account|cover|address)|"
    r"do(?:es)? not (?:prove|hold|generalize|generalise|cover|address)|"
    r"not (?:proven?|generalized?|generalised?)|disprove|cannot show|cannot prove|"
    r"violates? the assumption|breaks? down)\b",
    re.IGNORECASE,
)
_NEG_TYPE_NEGATIVE_RESULT_RE = re.compile(
    r"\b(worse|underperform(?:s|ed)?|lower than|insufficient|no improvement|degrad(?:e|es|ed|ation)|"
    r"deteriorat(?:e|es|ed|ion)|declin(?:e|es|ed|ing)|poor performance|less accurate|drop in|"
    r"negative result|no significant|not significant)\b",
    re.IGNORECASE,
)
_NEG_TYPE_MISSING_ABLATION_RE = re.compile(
    r"\b(no ablation|missing ablation|lacks? (?:an? )?ablation|"
    r"do(?:es)? not (?:report|provide|include).*\bablation)\b",
    re.IGNORECASE,
)
_NEG_TYPE_MISSING_BASELINE_RE = re.compile(
    r"\b(not compare(?:d)?|missing baseline|no baseline|without comparison|"
    r"without (?:a |the )?(?:strong )?baseline|lacks? (?:a |the )?(?:strong )?baseline|"
    r"do(?:es)? not (?:compare|report|provide|include).*\b(baseline|comparison)|"
    r"(?:baseline|comparison)[^.!?]{0,100}(?:is |are |was |were )?not (?:reported|included|provided)|"
    r"not (?:reported|included|provided)[^.!?]{0,100}\b(baseline|comparison))\b",
    re.IGNORECASE,
)
_NEG_TYPE_INSUFFICIENT_EVALUATION_RE = re.compile(
    r"\b(not evaluated|insufficient evaluation|limited evaluation|evaluation is limited|"
    r"small-scale evaluation|few datasets?|limited datasets?|insufficient experiments?|"
    r"do(?:es)? not (?:evaluate|test|validate)|no evaluation)\b",
    re.IGNORECASE,
)
_NEG_TYPE_REPRODUCIBILITY_GAP_RE = re.compile(
    r"\b(reproducibility|reproducible|implementation detail|hyperparameter|code unavailable|"
    r"not release(?:d)? code|lack(?:s|ing)? implementation|missing implementation|"
    r"cannot reproduce|insufficient detail)\b",
    re.IGNORECASE,
)
_NEG_TYPE_SCOPE_LIMITATION_RE = re.compile(
    r"\b(limitation|limitations|limited|restrict(?:s|ed|ion|ions)?|"
    r"threats? to validity|future work|out of scope|"
    r"assumes?|assumption requires?|only (?:applies|applicable|valid))\b",
    re.IGNORECASE,
)
_NEG_TYPE_NEUTRAL_CONTEXT_RE = re.compile(
    r"\b(with and without|with or without|without information loss|without privacy|"
    r"without the user's privacy|without user privacy|without guidance|"
    r"without intervention|without augmentations?|without dynamic tree attention|"
    r"trained without (?:a |the )?(?:definition|auxiliary) task|"
    r"unlike [^.!?]{0,100}\bthey do not\b|in contrast[^.!?]{0,100}\bthey do not\b|"
    r"(?:baseline|method|approach|system|framework|hugginggpt)[^.!?]{0,120}did not release (?:their |the )?(?:evaluation )?dataset|"
    r"without [^.!?]{0,80}\bwith(?:out)?\b)\b",
    re.IGNORECASE,
)


_NEG_TYPE_BIB_TITLE_NOISE_RE = re.compile(
    r"(arxiv:\s*\d|doi:\s*10\.|\bet al\.|\bpp\.\s*\d|"
    r"\bvol\.\s*\d|\bno\.\s*\d|\bproceedings of\b|\bin proc\.|"
    r"\bpreprint\b|\bconference on\b|\bjournal of\b|"
    r"\b(19|20)\d{2}[a-z]?\)\.|"
    r"^\s*\[\d+\]\s|\breferences?\b\s*$|\bbibliography\b)",
    re.IGNORECASE | re.MULTILINE,
)
_NEG_TYPE_NEUTRAL_INSTRUCTION_NOISE_RE = re.compile(
    r"(\breview the following\b|\bformat requirements?\b|"
    r"\byour review must\b|\byou (?:are|will be) (?:given|asked|provided)\b|"
    r"\bplease (?:provide|write|format|follow)\b|"
    r"\b\[instruction\]|\bthe following (?:paper|academic paper)\b|"
    r"\boutput (?:exactly|the following|a json)\b|"
    r"\bsystem prompt\b|\binstruction(?:s)?:\s)",
    re.IGNORECASE,
)


def _classify_negative_evidence_type(quote: str) -> str:
    """Diagnostic classifier for paper-grounded negative quotes.

    Neutral contrast and external-baseline context is filtered before actionable
    labels so related-work statements do not become hard-negative evidence.
    Bibliographic noise is checked after paper-side cues to avoid treating an
    otherwise meaningful sentence as a reference solely because it contains
    ``et al.``.
    """
    if not quote:
        return "generic_gap"
    if _NEG_TYPE_NEUTRAL_INSTRUCTION_NOISE_RE.search(quote):
        return "neutral_instruction_noise"
    if _NEG_TYPE_NEUTRAL_CONTEXT_RE.search(quote):
        return "neutral_control_context"
    if re.search(r"did not release (?:their |the )?(?:evaluation )?dataset", quote, re.IGNORECASE) and re.search(r"(benchmark|baseline|hugginggpt|et al\.|we developed)", quote, re.IGNORECASE):
        return "neutral_control_context"
    if _NEG_TYPE_DIRECT_CONTRADICTION_RE.search(quote):
        return "direct_contradiction"
    if _NEG_TYPE_NEGATIVE_RESULT_RE.search(quote):
        return "negative_result"
    if _NEG_TYPE_MISSING_ABLATION_RE.search(quote):
        return "missing_ablation"
    if _NEG_TYPE_MISSING_BASELINE_RE.search(quote):
        return "missing_baseline"
    if _NEG_TYPE_INSUFFICIENT_EVALUATION_RE.search(quote):
        return "insufficient_evaluation"
    if _NEG_TYPE_REPRODUCIBILITY_GAP_RE.search(quote):
        return "reproducibility_gap"
    if _NEG_TYPE_SCOPE_LIMITATION_RE.search(quote):
        return "scope_limitation"
    if _NEG_TYPE_BIB_TITLE_NOISE_RE.search(quote):
        return "bibliographic_or_title_noise"
    return "generic_gap"


NOISE_NEGATIVE_TYPES = frozenset({"bibliographic_or_title_noise", "neutral_instruction_noise"})
NEGATIVE_EVIDENCE_TYPES_ALL = frozenset(
    {"direct_contradiction", "negative_result", "missing_ablation", "missing_baseline",
     "insufficient_evaluation", "reproducibility_gap",
     "scope_limitation", "neutral_control_context", "generic_gap",
     "bibliographic_or_title_noise", "neutral_instruction_noise"}
)
ACTIONABLE_NEGATIVE_EVIDENCE_TYPES = frozenset(
    {"direct_contradiction", "negative_result", "missing_ablation", "missing_baseline", "insufficient_evaluation"}
)
LIMITATION_NEGATIVE_EVIDENCE_TYPES = frozenset({"scope_limitation", "reproducibility_gap", "generic_gap"})


def _negative_evidence_type_for_record(record: Dict[str, Any]) -> str:
    explicit = str((record or {}).get("negative_evidence_type") or "").strip()
    quote = str((record or {}).get("raw_quote") or (record or {}).get("evidence") or "")
    if explicit == "generic_gap" and _NEG_TYPE_NEUTRAL_CONTEXT_RE.search(quote):
        return "neutral_control_context"
    if explicit:
        return explicit
    stance = str((record or {}).get("stance") or "").strip().lower()
    if stance in {"contradicts", "contradict", "refutes", "refute", "partially_contradicts", "partially_refutes"}:
        return "direct_contradiction"
    return _classify_negative_evidence_type(quote)

_EVIDENCE_NONABSTRACT_FALLBACK_PATTERNS: List[Tuple[str, re.Pattern[str]]] = [
    ("method", re.compile(r"\b(method|methodology|approach|model|framework|algorithm|architecture|objective|training|decoding|routing|graph neural|diffusion)\b", re.IGNORECASE)),
    ("ablation", re.compile(r"\b(ablation|ablations|ablation study|ablation results|without (?:the )?\w+ module|remove(?:d|s)? (?:the )?\w+ module)\b", re.IGNORECASE)),
    ("comparison", re.compile(r"\b(compare|comparison|compared|baseline|baselines|state-of-the-art|sota|outperform|surpass|better than|against|robustness|sensitivity)\b", re.IGNORECASE)),
    ("results", re.compile(r"\b(experiment|evaluation|results|benchmark|baseline|dataset|metric|performance|outperform|mrr|hits@?|miou|fid|validity|docking)\b", re.IGNORECASE)),
    ("table_or_figure", re.compile(r"\b(table|figure|fig\.?)\b", re.IGNORECASE)),
    ("theory_or_proof", re.compile(r"\b(theorem|lemma|proposition|proof|convergence|generalization|provably)\b", re.IGNORECASE)),
    ("conclusion", re.compile(r"\b(conclusion|discussion)\b", re.IGNORECASE)),
]

_EVIDENCE_EMPIRICAL_PATTERN = re.compile(
    r"\b(experiment|experiments|evaluation|evaluations|result|results|baseline|baselines|dataset|datasets|metric|metrics|performance|outperform|benchmark|ablation|comparison|robustness|sensitivity|table|figure|fig\.?)\b",
    re.IGNORECASE,
)
_EVIDENCE_TABLE_PATTERN = re.compile(r"\b(table|figure|fig\.?)\b", re.IGNORECASE)
_EVIDENCE_METHOD_PATTERN = re.compile(r"\b(method|methods|methodology|approach|model|framework|algorithm|architecture)\b", re.IGNORECASE)
_EVIDENCE_SNIPPET_SOURCE_ORDER = ["abstract", "ablation", "comparison", "results", "table_or_figure", "claim_match", "theory_or_proof", "negative_or_gap", "method", "conclusion", "body_start"]
_EVIDENCE_SNIPPET_BUDGETS = {
    "abstract": 320,
    "ablation": 560,
    "comparison": 560,
    "results": 650,
    "table_or_figure": 600,
    "method": 520,
    "theory_or_proof": 520,
    "claim_match": 520,
    "conclusion": 260,
    "negative_or_gap": 520,
    "body_start": 1200,
}
_EVIDENCE_SNIPPET_MAX_PER_SOURCE = {
    "ablation": 2,
    "comparison": 2,
    "results": 2,
    "table_or_figure": 2,
    "claim_match": 2,
    "theory_or_proof": 1,
    "negative_or_gap": 1,
}
_CLAIM_QUERY_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "be",
    "by",
    "for",
    "from",
    "in",
    "is",
    "it",
    "its",
    "of",
    "on",
    "or",
    "our",
    "paper",
    "propose",
    "proposes",
    "proposed",
    "show",
    "shows",
    "that",
    "the",
    "their",
    "this",
    "to",
    "using",
    "we",
    "with",
}


def _count_pattern(pattern: re.Pattern[str], text: str) -> int:
    return len(pattern.findall(text or ""))


def _claim_query_terms_from_state(state: Dict[str, Any], target_claim_ids: Optional[Sequence[str]] = None) -> set[str]:
    if not isinstance(state, dict):
        return set()
    target_set = {str(item or "") for item in (target_claim_ids or []) if str(item or "")}
    claims = [
        item
        for item in state.get("claims", []) or []
        if isinstance(item, dict)
        and str(item.get("claim_id") or "")
        and (not target_set or str(item.get("claim_id") or "") in target_set)
    ]
    if not claims and target_set:
        claims = [item for item in state.get("claims", []) or [] if isinstance(item, dict)]
    text = " ".join(
        str(claim.get(key) or "")
        for claim in claims[:4]
        for key in ("claim", "evidence_need", "claim_type")
    )
    terms = {
        token
        for token in re.findall(r"[A-Za-z][A-Za-z0-9_-]{2,}", text.lower())
        if token not in _CLAIM_QUERY_STOPWORDS and not token.isdigit()
    }
    return set(list(terms)[:24])


def _claim_overlap_score(text: str, query_terms: set[str]) -> int:
    if not query_terms:
        return 0
    tokens = set(re.findall(r"[A-Za-z][A-Za-z0-9_-]{2,}", str(text or "").lower()))
    return len(tokens & query_terms)


def _window_around(text: str, pos: int, window: int = 520) -> str:
    start = max(0, pos - window // 3)
    end = min(len(text), pos + window)
    snippet = text[start:end].strip()
    return re.sub(r"\s+", " ", snippet)


def _truncate_snippet_text(text: str, max_chars: int) -> str:
    normalized = re.sub(r"\s+", " ", text or "").strip()
    if len(normalized) <= max_chars:
        return normalized
    cutoff = max(0, max_chars - 4)
    truncated = normalized[:cutoff].rsplit(" ", 1)[0].strip()
    return f"{truncated} ..." if truncated else normalized[:max_chars]


def _quote_bank_dedupe_key(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", str(text or "").lower())).strip()


def _quote_fragment_around(text: str, pos: int, max_chars: int = 220) -> str:
    if not text:
        return ""
    pos = max(0, min(pos, len(text) - 1))
    while pos < len(text) - 1 and text[pos].isspace():
        pos += 1
    line_start = text.rfind("\n", 0, pos) + 1
    line_end = text.find("\n", pos)
    if line_end < 0:
        line_end = len(text)
    line = text[line_start:line_end].strip()
    if 55 <= len(line) <= max_chars:
        return line
    if line and len(line) > max_chars and re.search(r"\b(?:Table|Figure|Fig\.|Section|Sec\.)\s*\d+|\\(?:section|subsection)\b", line, re.IGNORECASE):
        return re.sub(r"\s+", " ", line[:max_chars].rsplit(" ", 1)[0].strip())

    # Prefer sentence/line boundaries over fixed windows.  Mid-token fragments
    # are exact-matchable but hard for the model and semantic verifier to use.
    boundary_start = max(
        text.rfind("\n", max(0, pos - max_chars), pos),
        text.rfind(". ", max(0, pos - max_chars), pos),
        text.rfind("? ", max(0, pos - max_chars), pos),
        text.rfind("! ", max(0, pos - max_chars), pos),
    )
    if boundary_start >= 0:
        start = boundary_start + (1 if text[boundary_start] == "\n" else 2)
        end_limit = min(len(text), start + max_chars)
        next_candidates = [
            idx + 1
            for idx in (
                text.find(". ", max(pos + 20, start), end_limit),
                text.find("? ", max(pos + 20, start), end_limit),
                text.find("! ", max(pos + 20, start), end_limit),
                text.find("\n", max(pos + 20, start), end_limit),
            )
            if idx != -1
        ]
        end = min(next_candidates) if next_candidates else end_limit
        candidate = re.sub(r"\s+", " ", text[start:end].strip())
        if 45 <= len(candidate) <= max_chars and not re.match(r"^[a-z]{1,3}\s", candidate):
            return candidate

    segment_start = max(0, pos - max_chars // 3)
    while segment_start > 0 and segment_start < len(text) and not text[segment_start - 1].isspace():
        segment_start -= 1
    segment_end = min(len(text), segment_start + max_chars)
    segment = text[segment_start:segment_end].strip()
    if len(segment) > max_chars:
        segment = segment[:max_chars].rsplit(" ", 1)[0].strip()
    return re.sub(r"\s+", " ", segment).strip()


def _refine_evidence_quote_source(source: str, quote: str) -> str:
    """Prefer the most concrete empirical source visible in the quote itself."""
    text = str(quote or "")
    if re.search(r"\b(ablation study|ablation results?|ablation analysis|ablat(?:e|ed|ion|ions)|without (?:the )?\w+ module|remove(?:d|s)? (?:the )?\w+ module)\b", text, re.IGNORECASE):
        return "ablation"
    if re.search(r"(?:^|\n)\s*(?:Table|Figure|Fig\.)\s*\d+\s*[:.\-]|\b(?:Table|Figure|Fig\.)\s*\d+", text, re.IGNORECASE):
        return "table_or_figure"
    if source in {"claim_match", "results", "comparison"} and re.search(
        r"\b(compare(?:d|s)? with|comparison with|baseline(?:s)?|state-of-the-art|sota|outperform(?:s|ed)?|surpass(?:es|ed)?|better than|robustness|sensitivity)\b",
        text,
        re.IGNORECASE,
    ):
        return "comparison"
    return source


def _quote_source_locator(source: str, quote: str, index: int) -> str:
    table = re.search(r"\b(Table|Figure|Fig\.)\s*\d+", quote, re.IGNORECASE)
    if table:
        return table.group(0)
    labels = {
        "results": "Results / Evaluation excerpt",
        "table_or_figure": "Table/Figure excerpt",
        "ablation": "Ablation excerpt",
        "comparison": "Comparison / Robustness excerpt",
        "negative_or_gap": "Limitation / Gap / Negative evidence excerpt",
        "method": "Method / Approach excerpt",
        "theory_or_proof": "Theory / Proof excerpt",
        "claim_match": "Claim-matched evidence excerpt",
        "abstract": "Abstract excerpt",
        "conclusion": "Conclusion / Discussion excerpt",
        "body_start": "Paper body excerpt",
    }
    return f"{labels.get(source, source or 'Paper excerpt')} #{index}"


def _build_evidence_quote_bank(body: str, max_quotes: int = 6, claim_query_terms: Optional[set[str]] = None) -> List[Dict[str, Any]]:
    if not body:
        return []
    query_terms = claim_query_terms or set()
    anchors: List[Tuple[str, int]] = []
    header_positions = [
        match.start()
        for source, pattern in _EVIDENCE_SECTION_HEADER_PATTERNS
        for match in [pattern.search(body)]
        if source != "abstract" and match
    ]
    first_nonabstract_pos = min(header_positions) if header_positions else min(len(body), max(900, len(body) // 8))
    fallback_start = min(len(body), max(900, first_nonabstract_pos))
    if fallback_start >= len(body):
        fallback_start = min(first_nonabstract_pos, len(body))

    # Put deeper empirical and negative anchors first so the agent copies real
    # result/method/limitation text instead of rewriting abstract-level claims.
    # Result-like keywords before the first real section are usually
    # abstract/introduction claims and should not be labeled as results evidence.
    for source, pattern in list(_EVIDENCE_DETAIL_ANCHOR_PATTERNS) + list(_EVIDENCE_NEGATIVE_ANCHOR_PATTERNS):
        for match in pattern.finditer(body):
            pos = match.start()
            if source in {"results", "table_or_figure", "negative_or_gap"} and pos < first_nonabstract_pos:
                continue
            anchors.append((source, pos))
            if len([1 for s, _ in anchors if s == source]) >= 4:
                break
    for source, pattern in _EVIDENCE_SECTION_HEADER_PATTERNS:
        match = pattern.search(body)
        if match:
            anchors.append((source, match.start()))
    for source, pattern in _EVIDENCE_NONABSTRACT_FALLBACK_PATTERNS:
        for match in pattern.finditer(body):
            pos = match.start()
            if pos < first_nonabstract_pos:
                continue
            anchors.append((source, pos))
            break
    for term in sorted(query_terms, key=lambda item: (-len(item), item))[:12]:
        match = re.search(rf"\b{re.escape(term)}\b", body[fallback_start:], re.IGNORECASE)
        if match:
            anchors.append(("claim_match", fallback_start + match.start()))
    anchors.append(("abstract", 0))

    source_order = {"claim_match": 0, "ablation": 1, "comparison": 2, "table_or_figure": 3, "results": 4, "theory_or_proof": 5, "negative_or_gap": 6, "method": 7, "conclusion": 8, "abstract": 9, "body_start": 10}
    anchors = sorted(
        anchors,
        key=lambda item: (
            0 if query_terms and _claim_overlap_score(_quote_fragment_around(body, item[1]), query_terms) > 0 else 1,
            -_claim_overlap_score(_quote_fragment_around(body, item[1]), query_terms),
            source_order.get(item[0], 9),
            item[1],
        ),
    )

    quote_bank: List[Dict[str, Any]] = []
    seen: set[str] = set()
    source_counts: Dict[str, int] = {}
    for source, pos in anchors:
        if len(quote_bank) >= max_quotes:
            break
        if source_counts.get(source, 0) >= (2 if source in {"ablation", "comparison", "results", "table_or_figure", "negative_or_gap", "claim_match", "theory_or_proof"} else 1):
            continue
        quote = _quote_fragment_around(body, pos)
        source = _refine_evidence_quote_source(source, quote)
        if (
            source != "negative_or_gap"
            and any(pattern.search(quote) for _, pattern in _EVIDENCE_NEGATIVE_ANCHOR_PATTERNS)
            and not re.search(r"\b(Table|Figure|Fig\.)\s*\d+", quote, re.IGNORECASE)
        ):
            source = "negative_or_gap"
        key = _quote_bank_dedupe_key(quote)
        if len(key) < 40 or key in seen:
            continue
        seen.add(key)
        source_counts[source] = source_counts.get(source, 0) + 1
        quote_id = f"quote-{source.replace('_', '-')}-{source_counts[source]}"
        verified_quote = _verify_quote_against_reference(quote, body, reference_start=0)
        span_start = int(verified_quote.get("verified_source_span_start", -1))
        span_end = int(verified_quote.get("verified_source_span_end", -1))
        overlap_score = _claim_overlap_score(quote, query_terms)
        entry: Dict[str, Any] = {
            "quote_id": quote_id,
            "source_bucket": source,
            "source_locator": _quote_source_locator(source, quote, source_counts[source]),
            "raw_quote": quote,
            "source_span_start": span_start,
            "source_span_end": span_end,
            "claim_overlap_score": overlap_score,
            "support_role_hint": (
                "ablation_support" if source == "ablation" else
                "comparison_support" if source == "comparison" else
                "empirical_result" if source in {"results", "table_or_figure"} else
                "method_description" if source == "method" else
                "theory_or_proof_support" if source == "theory_or_proof" else
                "paper_evidence"
            ),
            "copy_rule": "Copy raw_quote exactly; do not paraphrase.",
        }
        # P0-4 (diagnostic-only): attach a 5-class negative_evidence_type label
        # to negative_or_gap quotes. No filtering, no gating — audit field only.
        if source == "negative_or_gap":
            entry["negative_evidence_type"] = _classify_negative_evidence_type(quote)
        quote_bank.append(entry)
    return quote_bank


def _build_critique_negative_quote_bank(body: str, max_quotes: int = 6) -> List[Dict[str, Any]]:
    """Build a Critique-only bank of actionable paper-side negative anchors.

    This bank is intentionally separate from the positive evidence quote bank:
    it is not capped by the positive support context budget and it prioritizes
    direct contradiction, negative-result, and missing-ablation cues.  Entries
    remain quote/span-grounded; neutral control contexts are excluded before the
    Critique Agent sees them.
    """
    if not body:
        return []
    header_positions = [
        match.start()
        for source, pattern in _EVIDENCE_SECTION_HEADER_PATTERNS
        for match in [pattern.search(body)]
        if source != "abstract" and match
    ]
    first_nonabstract_pos = min(header_positions) if header_positions else min(len(body), max(900, len(body) // 8))
    candidates: List[Tuple[int, int, str]] = []
    for _, pattern in _EVIDENCE_NEGATIVE_ANCHOR_PATTERNS:
        for match in pattern.finditer(body, pos=first_nonabstract_pos):
            quote = _quote_fragment_around(body, match.start(), max_chars=260)
            sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+", quote) if part.strip()]
            actionable_sentences: List[str] = []
            limitation_sentences: List[str] = []
            for sentence in sentences or [quote]:
                sentence_type = _classify_negative_evidence_type(sentence)
                if sentence_type in ACTIONABLE_NEGATIVE_EVIDENCE_TYPES:
                    actionable_sentences.append(sentence)
                elif sentence_type in {"scope_limitation", "reproducibility_gap"}:
                    limitation_sentences.append(sentence)
            if actionable_sentences:
                quote = " ".join(actionable_sentences[:2])
                neg_type = _classify_negative_evidence_type(quote)
            elif limitation_sentences:
                quote = " ".join(limitation_sentences[:2])
                neg_type = _classify_negative_evidence_type(quote)
            else:
                neg_type = _classify_negative_evidence_type(quote)
            if neg_type in {"neutral_control_context", "generic_gap", "bibliographic_or_title_noise", "neutral_instruction_noise"}:
                continue
            score = 0 if neg_type in ACTIONABLE_NEGATIVE_EVIDENCE_TYPES else 1
            candidates.append((score, match.start(), quote))
    candidates.sort(key=lambda item: (item[0], item[1]))

    quote_bank: List[Dict[str, Any]] = []
    seen: set[str] = set()
    for _, pos, quote in candidates:
        if len(quote_bank) >= max_quotes:
            break
        key = _quote_bank_dedupe_key(quote)
        if len(key) < 40 or key in seen:
            continue
        seen.add(key)
        neg_type = _classify_negative_evidence_type(quote)
        if neg_type in {"neutral_control_context", "generic_gap", "bibliographic_or_title_noise", "neutral_instruction_noise"}:
            continue
        verified_quote = _verify_quote_against_reference(quote, body, reference_start=0)
        span_start = int(verified_quote.get("verified_source_span_start", -1))
        span_end = int(verified_quote.get("verified_source_span_end", -1))
        quote_index = len(quote_bank) + 1
        quote_bank.append({
            "quote_id": f"quote-critique-negative-{quote_index}",
            "source_bucket": "negative_or_gap",
            "source_locator": _quote_source_locator("negative_or_gap", quote, quote_index),
            "raw_quote": quote,
            "source_span_start": span_start,
            "source_span_end": span_end,
            "negative_evidence_type": neg_type,
            "copy_rule": "Copy raw_quote exactly; use only for paper-side negative evidence.",
        })
    return quote_bank


def _assemble_evidence_context(snippets: List[Tuple[str, str]], max_length: int, claim_query_terms: Optional[set[str]] = None) -> Tuple[str, List[str]]:
    ordered: List[Tuple[str, str]] = []
    for wanted_source in _EVIDENCE_SNIPPET_SOURCE_ORDER:
        matching = [(source, snippet) for source, snippet in snippets if source == wanted_source]
        matching.sort(key=lambda item: -_claim_overlap_score(item[1], claim_query_terms or set()))
        ordered.extend(matching)
    ordered.extend((source, snippet) for source, snippet in snippets if source not in _EVIDENCE_SNIPPET_SOURCE_ORDER)

    parts: List[str] = []
    included_sources: List[str] = []
    source_counts: Dict[str, int] = {}
    remaining = max_length
    for source, snippet in ordered:
        if remaining < 100:
            break
        max_count = _EVIDENCE_SNIPPET_MAX_PER_SOURCE.get(source, 1)
        if source_counts.get(source, 0) >= max_count:
            continue
        label = f"[{source}] "
        budget = min(_EVIDENCE_SNIPPET_BUDGETS.get(source, 480), remaining - len(label))
        if budget < 80:
            continue
        rendered_snippet = _truncate_snippet_text(snippet, budget)
        if len(rendered_snippet) < 60:
            continue
        part = f"{label}{rendered_snippet}"
        if len(part) > remaining:
            part = _truncate_snippet_text(part, remaining)
        parts.append(part)
        remaining -= len(part) + 2
        source_counts[source] = source_counts.get(source, 0) + 1
        if source not in included_sources:
            included_sources.append(source)
    return "\n\n".join(parts).strip(), included_sources


def _render_evidence_context_with_meta(
    task: Dict[str, Any],
    max_length: int = 2400,
    state: Optional[Dict[str, Any]] = None,
    target_claim_ids: Optional[Sequence[str]] = None,
) -> Tuple[str, Dict[str, Any]]:
    body, cleaned_wrapper = _clean_paper_body(task.get("paper_text", ""))
    claim_query_terms = _claim_query_terms_from_state(state or task.get("review_state", {}) or {}, target_claim_ids)
    if not body:
        meta = {
            "evidence_context_chars": 0,
            "evidence_context_mode": "section_aware_claim_v3",
            "evidence_context_cleaned_wrapper": cleaned_wrapper,
            "evidence_context_contains_method": False,
            "evidence_context_contains_results": False,
            "evidence_context_contains_conclusion": False,
            "evidence_context_contains_table_or_figure": False,
            "evidence_context_contains_claim_match": False,
            "evidence_context_contains_empirical_terms": False,
            "evidence_context_empirical_term_count": 0,
            "evidence_context_table_or_figure_term_count": 0,
            "evidence_context_method_term_count": 0,
            "evidence_context_claim_query_term_count": len(claim_query_terms),
            "evidence_context_claim_query_terms": sorted(claim_query_terms)[:12],
            "evidence_context_snippet_sources": [],
            "evidence_quote_bank_count": 0,
            "evidence_quote_bank_sources": [],
            "evidence_quote_bank_claim_matched_count": 0,
            "evidence_quote_bank_mode": "quote_bank_claim_v2",
        }
        return "No paper text available.", meta

    snippets: List[Tuple[str, str]] = []
    seen_spans: List[Tuple[int, int, str]] = []

    def add_snippet(source: str, pos: int, window: int = 520) -> None:
        start = max(0, pos - window // 4)
        end = min(len(body), pos + window)
        for old_start, old_end, old_source in seen_spans:
            overlap = min(end, old_end) - max(start, old_start)
            if overlap > 160 and old_source == source:
                return
        seen_spans.append((start, end, source))
        snippet = _window_around(body, pos, window=window)
        if snippet:
            snippets.append((source, snippet))

    add_snippet("abstract", 0, window=680)

    # v2: prefer real section headers. v1 matched generic words such as
    # "results" inside the abstract, which made logs claim results/table
    # visibility while the Evidence Agent still saw mostly abstract self-claims.
    header_sources: set[str] = set()
    for source, pattern in _EVIDENCE_SECTION_HEADER_PATTERNS:
        match = pattern.search(body)
        if match:
            header_sources.add(source)
            add_snippet(source, match.start(), window=900 if source in {"results", "table_or_figure"} else 620)

    first_nonabstract_pos = min(
        [match.start() for _, pattern in _EVIDENCE_SECTION_HEADER_PATTERNS for match in [pattern.search(body)] if match] or [max(900, len(body) // 8)]
    )
    fallback_start = min(len(body), max(900, first_nonabstract_pos))
    if fallback_start >= len(body):
        fallback_start = min(first_nonabstract_pos, len(body))

    # Add concrete evidence-bearing anchors even when a broad Results section
    # starts with setup text. These anchors are intentionally later/deeper than
    # the abstract and favor numeric metrics, baselines, captions, and ablations.
    for source, pattern in list(_EVIDENCE_DETAIL_ANCHOR_PATTERNS) + list(_EVIDENCE_NEGATIVE_ANCHOR_PATTERNS):
        matches = list(pattern.finditer(body, pos=fallback_start))[:2]
        for match in matches:
            add_snippet(source, match.start(), window=760 if source == "results" else 680)

    claim_match_count = 0
    for term in sorted(claim_query_terms, key=lambda item: (-len(item), item))[:12]:
        match = re.search(rf"\b{re.escape(term)}\b", body[fallback_start:], re.IGNORECASE)
        if match:
            add_snippet("claim_match", fallback_start + match.start(), window=700)
            claim_match_count += 1
            if claim_match_count >= 3:
                break

    for source, pattern in _EVIDENCE_NONABSTRACT_FALLBACK_PATTERNS:
        if source in header_sources:
            continue
        match = pattern.search(body, pos=fallback_start)
        if match:
            add_snippet(source, match.start(), window=620 if source in {"results", "table_or_figure"} else 520)

    if not snippets:
        snippets.append(("body_start", re.sub(r"\s+", " ", body[:max_length]).strip()))

    context, sources = _assemble_evidence_context(snippets, max_length=max_length, claim_query_terms=claim_query_terms)
    quote_bank = _build_evidence_quote_bank(body, max_quotes=12, claim_query_terms=claim_query_terms)
    source_set = set(sources)
    empirical_term_count = _count_pattern(_EVIDENCE_EMPIRICAL_PATTERN, context)
    table_term_count = _count_pattern(_EVIDENCE_TABLE_PATTERN, context)
    method_term_count = _count_pattern(_EVIDENCE_METHOD_PATTERN, context)
    meta = {
        "evidence_context_chars": len(context),
        "evidence_context_mode": "section_aware_claim_v3",
        "evidence_context_cleaned_wrapper": cleaned_wrapper,
        "evidence_context_contains_method": "method" in source_set,
        "evidence_context_contains_results": "results" in source_set,
        "evidence_context_contains_conclusion": "conclusion" in source_set,
        "evidence_context_contains_table_or_figure": "table_or_figure" in source_set,
        "evidence_context_contains_ablation": "ablation" in source_set,
        "evidence_context_contains_comparison": "comparison" in source_set,
        "evidence_context_contains_claim_match": "claim_match" in source_set,
        "evidence_context_contains_empirical_terms": empirical_term_count > 0,
        "evidence_context_empirical_term_count": empirical_term_count,
        "evidence_context_table_or_figure_term_count": table_term_count,
        "evidence_context_method_term_count": method_term_count,
        "evidence_context_claim_query_term_count": len(claim_query_terms),
        "evidence_context_claim_query_terms": sorted(claim_query_terms)[:12],
        "evidence_context_snippet_sources": sources,
        "evidence_quote_bank_count": len(quote_bank),
        "evidence_quote_bank_sources": [item.get("source_bucket", "") for item in quote_bank],
        "evidence_quote_bank_claim_matched_count": sum(1 for item in quote_bank if int(item.get("claim_overlap_score") or 0) > 0),
        "evidence_quote_bank_mode": "quote_bank_claim_v2",
    }
    meta["evidence_quote_bank"] = quote_bank
    return context or "No paper text available.", meta

def _render_evidence_context(task: Dict[str, Any], max_length: int = 2400) -> str:
    context, _ = _render_evidence_context_with_meta(task, max_length=max_length)
    return context



def _recovery_hydration_slice(state: Dict[str, Any], *, max_targets: int = 3) -> Dict[str, Any]:
    """Expose final-view contamination targets to manager/critique prompts.

    This is prompt/context hydration only.  It does not mutate live ReviewState
    and does not relax the recovery validator.  The goal is to make recovery
    target selection explicit instead of relying on broad active_focus text.
    """
    try:
        decision_view = build_decision_hygiene_view(copy.deepcopy(state or {}))
    except Exception:
        return {
            "state_contamination_targets": [],
            "recovery_target_gate_counts": {},
            "recovery_hydration_available": False,
        }
    hygiene = decision_view.get("decision_hygiene", {}) if isinstance(decision_view, dict) else {}
    targets = list(hygiene.get("state_contamination_targets") or [])
    priority = {"real_target": 0, "weak_target": 1, "fallback_target": 2, "empty_target": 3}
    targets.sort(
        key=lambda item: (
            priority.get(str(item.get("target_gate_label") or ""), 9),
            -float(item.get("localization_confidence") or 0.0),
            str(item.get("error_type") or ""),
        )
    )
    hydrated_targets: List[Dict[str, Any]] = []
    for item in targets[:max_targets]:
        hydrated_targets.append({
            "target_type": str(item.get("target_type") or ""),
            "target_id": str(item.get("target_id") or ""),
            "error_type": str(item.get("error_type") or ""),
            "affected_relation": str(item.get("affected_relation") or ""),
            "target_gate_label": str(item.get("target_gate_label") or ""),
            "repairability": str(item.get("repairability") or ""),
            "localization_confidence": item.get("localization_confidence", 0),
            "evidence_context": str(item.get("evidence_context") or "")[:96],
        })
    return {
        "state_contamination_targets": hydrated_targets,
        "recovery_target_gate_counts": hygiene.get("recovery_target_gate_counts") or {},
        "negative_evidence_type_counts": hygiene.get("negative_evidence_type_counts") or {},
        "negative_grounding_conflict_count": int(hygiene.get("negative_grounding_conflict_count") or 0),
        "verified_actionable_negative_flaw_count": int(hygiene.get("verified_actionable_negative_flaw_count") or 0),
        "verified_limitation_negative_flaw_count": int(hygiene.get("verified_limitation_negative_flaw_count") or 0),
        "recovery_hydration_available": True,
    }

def _render_manager_state_slice(state: Dict[str, Any]) -> Dict[str, Any]:
    unresolved = state.get("unresolved_questions", [])[:5]
    open_unresolved = [item for item in unresolved if item.get("status") != "resolved"]
    negative_binding = _negative_evidence_binding_view(state)
    negative_evidence = negative_binding["negative_evidence_candidates"]
    unlinked_negative_evidence = negative_binding["unlinked_negative_evidence_candidates"]
    claim_coverage = claim_coverage_summary(state)
    recovery_hydration = _recovery_hydration_slice(state, max_targets=2)
    for _verbose_key in (
        "negative_evidence_type_counts",
        "verified_actionable_negative_flaw_count",
        "verified_limitation_negative_flaw_count",
    ):
        recovery_hydration.pop(_verbose_key, None)
    return {
        "phase": state.get("phase", "normal_review"),
        "phase_turn_index": state.get("phase_turn_index", 0),
        "phase_enter_reason": state.get("phase_enter_reason", ""),
        "phase_exit_reason": state.get("phase_exit_reason", ""),
        "phase_hold_reason": state.get("phase_hold_reason", ""),
        "sticky_target_id": state.get("sticky_target_id", ""),
        "sticky_target_type": state.get("sticky_target_type", ""),
        "sticky_target_active": state.get("sticky_target_active", False),
        "sticky_target_turns_remaining": state.get("sticky_target_turns_remaining", 0),
        "sticky_release_reason": state.get("sticky_release_reason", ""),
        "active_focus": state.get("active_focus", state.get("last_focus", "")),
        "risk_profile": copy.deepcopy(state.get("risk_profile", {})),
        "claim_coverage": claim_coverage,
        "open_unresolved_questions": open_unresolved[:5],
        "evidence_gaps": _open_evidence_gaps(state)[:5],
        "negative_evidence_candidates": negative_evidence[:4],
        "unlinked_negative_evidence_candidates": unlinked_negative_evidence[:4],
        "negative_evidence_binding_retry_required": bool(unlinked_negative_evidence),
        "invalid_negative_grounding_conflicts": negative_binding["invalid_negative_grounding_conflicts"][:4],
        "recovery_hydration": recovery_hydration,
        "current_hypotheses": state.get("current_hypotheses", [])[:4],
        "conflict_summary": state.get("conflict_summary", [])[:4],
        "revision_summary": state.get("revision_summary", [])[:4],
        "support_signals": (state.get("risk_profile", {}) or {}).get("support_signals", [])[:4],
        "pending_user_question": state.get("pending_user_question", ""),
        "clarification_needed": state.get("clarification_needed", False),
    }


def _filter_items_by_ids(items: Sequence[Dict[str, Any]], key: str, target_ids: Optional[Sequence[str]], fallback_limit: int) -> List[Dict[str, Any]]:
    target_ids = [item_id for item_id in (target_ids or []) if item_id]
    if not target_ids:
        return list(items[:fallback_limit])
    filtered = [item for item in items if item.get(key) in target_ids]
    return filtered or list(items[:fallback_limit])


def _render_claim_state_slice(state: Dict[str, Any], action_type: str = "extract_claims", target_claim_ids: Optional[Sequence[str]] = None) -> Dict[str, Any]:
    claims = _filter_items_by_ids(state.get("claims", []), "claim_id", target_claim_ids, 5)
    coverage = claim_coverage_summary(state)
    uncertain_or_new = [
        item for item in claims
        if item.get("status") in {"new", "uncertain", "superseded", "unsupported"}
    ]
    if not uncertain_or_new:
        uncertain_or_new = [
            item for item in state.get("claims", [])
            if item.get("status") in {"new", "uncertain", "superseded", "unsupported"}
        ][:4]
    current_hypotheses = state.get("current_hypotheses", [])[:4] if action_type in {"extract_claims", "challenge_previous_hypothesis"} else []
    return {
        "sticky_target_id": state.get("sticky_target_id", ""),
        "sticky_target_type": state.get("sticky_target_type", ""),
        "sticky_target_active": state.get("sticky_target_active", False),
        "sticky_target_turns_remaining": state.get("sticky_target_turns_remaining", 0),
        "sticky_release_reason": state.get("sticky_release_reason", ""),
        "active_focus": state.get("active_focus", state.get("last_focus", "")),
        "action_type": action_type,
        "claims": claims[:5],
        "claim_coverage": coverage,
        "claim_coverage_guidance": {
            "required_tags": ["method", "empirical"],
            "recommended_tags": ["limitation", "scope", "comparison"],
            "missing_tags": coverage.get("missing_review_coverage_tags", []),
        },
        "claims_needing_revision": uncertain_or_new[:4],
        "current_hypotheses": current_hypotheses,
        "revision_summary": state.get("revision_summary", [])[:3],
        "dialogue_summary": state.get("dialogue_summary", ""),
    }


def _render_evidence_state_slice(state: Dict[str, Any], target_claim_ids: Optional[Sequence[str]] = None, target_evidence_ids: Optional[Sequence[str]] = None, target_flaw_ids: Optional[Sequence[str]] = None, action_type: str = "verify_evidence") -> Dict[str, Any]:
    selected_claims = _filter_items_by_ids(state.get("claims", []), "claim_id", target_claim_ids, 4)
    real_claim_ids = _real_claim_ids_from_state(state)
    omitted_fallback_claim_ids = [
        item.get("claim_id")
        for item in selected_claims
        if str(item.get("claim_id", "")).startswith("claim-fallback")
    ]
    claims = [item for item in selected_claims if item.get("claim_id") in real_claim_ids]
    fallback_targets_replaced_with_real_candidates = bool(omitted_fallback_claim_ids and not claims)
    if not claims:
        claims = [
            item for item in state.get("claims", [])
            if item.get("claim_id") in real_claim_ids
        ][:4]
    if action_type == "challenge_previous_hypothesis":
        claims = [item for item in claims if item.get("status") in {"supported", "uncertain", "partially_supported"}] or claims

    original_claims = list(claims)
    evidence = state.get("evidence_map", [])
    target_flaw_id_set = {str(item) for item in (target_flaw_ids or []) if str(item)}
    flaw_candidates = state.get("flaw_candidates", []) or []
    target_flaws = [
        item for item in flaw_candidates
        if isinstance(item, dict) and (not target_flaw_id_set or str(item.get("flaw_id") or "") in target_flaw_id_set)
    ][:4]

    def claim_has_strong_support(claim_id: str) -> bool:
        for item in evidence:
            if not isinstance(item, dict):
                continue
            if item.get("claim_id") != claim_id:
                continue
            if item.get("strength") == "strong" and item.get("stance") in {"supports", "partially_supports"}:
                return True
        return False

    def support_diversity_for_claims(claim_ids: Sequence[str]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, List[str]], List[Dict[str, Any]]]:
        from .support_quality import derive_support_quality, independence_group_id

        claim_set = {str(item) for item in claim_ids if str(item)}
        claim_by_id = {
            str(item.get("claim_id") or ""): item
            for item in state.get("claims", []) or []
            if isinstance(item, dict) and str(item.get("claim_id") or "")
        }
        support_items_by_claim: Dict[str, List[Dict[str, Any]]] = {claim_id: [] for claim_id in claim_set}
        for item in state.get("evidence_map", []) or []:
            if not isinstance(item, dict):
                continue
            claim_id = str(item.get("claim_id") or "")
            if claim_id not in claim_set:
                continue
            if str(item.get("stance") or "") not in {"supports", "partially_supports"}:
                continue
            if str(item.get("binding_status") or "") and str(item.get("binding_status") or "") != "bound_real_claim":
                continue
            if claim_id not in real_claim_ids:
                continue
            support_items_by_claim.setdefault(claim_id, []).append(item)

        summaries: List[Dict[str, Any]] = []
        needs: List[Dict[str, Any]] = []
        first_support_needs: List[Dict[str, Any]] = []
        avoid_by_claim: Dict[str, List[str]] = {}
        for claim_id in claim_ids:
            claim_id = str(claim_id or "")
            if not claim_id or claim_id not in real_claim_ids:
                continue
            groups: set[str] = set()
            quote_ids: set[str] = set()
            locators: set[str] = set()
            buckets: set[str] = set()
            depths: set[str] = set()
            for ev in support_items_by_claim.get(claim_id, []):
                groups.add(independence_group_id(ev))
                quote_id = str(ev.get("quote_id") or ev.get("source_quote_id") or "").strip()
                if quote_id:
                    quote_ids.add(quote_id)
                locator = str(ev.get("source_locator") or ev.get("source") or "").strip()
                if locator:
                    locators.add(locator)
                bucket = _decision_support_source_bucket(ev)
                if bucket:
                    buckets.add(bucket)
                quality = derive_support_quality(ev, claim_by_id.get(claim_id))
                depth = str(quality.get("support_depth") or "")
                if depth:
                    depths.add(depth)
            summary = {
                "claim_id": claim_id,
                "support_item_count": len(support_items_by_claim.get(claim_id, [])),
                "independent_support_group_count": len(groups),
                "used_quote_ids": sorted(quote_ids)[:6],
                "used_source_locators": sorted(locators)[:6],
                "used_source_buckets": sorted(buckets)[:6],
                "observed_support_depths": sorted(depths)[:4],
            }
            summaries.append(summary)
            if not support_items_by_claim.get(claim_id):
                claim = claim_by_id.get(claim_id) or {}
                first_support_needs.append({
                    "claim_id": claim_id,
                    "claim": claim.get("claim", ""),
                    "claim_type": claim.get("claim_type", ""),
                    "evidence_need": claim.get("evidence_need", ""),
                    "instruction": "Find the first quote-grounded evidence item for this real claim. If Evidence Quote Bank has a relevant copied quote, output an evidence_map item before adding unresolved_questions.",
                })
            elif len(groups) < 2:
                avoid_by_claim[claim_id] = sorted(quote_ids)[:8]
                needs.append({
                    "claim_id": claim_id,
                    "current_independent_support_group_count": len(groups),
                    "used_quote_ids": sorted(quote_ids)[:6],
                    "used_source_locators": sorted(locators)[:6],
                    "used_source_buckets": sorted(buckets)[:6],
                    "instruction": "Find a second independent source for this claim. Prefer a different quote_id and source_locator from a different section/source bucket; if no independent quote is visible, add an unresolved question instead of reusing the same quote.",
                })
        return summaries, needs[:4], avoid_by_claim, first_support_needs[:4]

    def claim_focus_score(item: Dict[str, Any], index: int) -> Tuple[int, int]:
        claim_id = str(item.get("claim_id") or "")
        text = " ".join(str(item.get(key) or "") for key in ("claim", "rationale", "evidence_need")).lower()
        score = 0
        if str(item.get("importance") or "").lower() in {"high", "critical"}:
            score += 4
        if _EVIDENCE_EMPIRICAL_PATTERN.search(text):
            score += 3
        if _EVIDENCE_METHOD_PATTERN.search(text):
            score += 1
        if not claim_has_strong_support(claim_id):
            score += 2
        if str(item.get("status") or "").lower() in {"new", "uncertain", "partially_supported", "unsupported"}:
            score += 1
        return score, -index

    evidence_focus_applied = False
    evidence_focus_reason = "not_needed"
    preferred_claims: List[Dict[str, Any]] = []
    if action_type in {"verify_evidence", "request_evidence_recheck"} and len(claims) > 2:
        ranked = sorted(enumerate(claims), key=lambda pair: claim_focus_score(pair[1], pair[0]), reverse=True)
        preferred_claims = [item for _, item in ranked[:2]]
        preferred_ids = {str(item.get("claim_id") or "") for item in preferred_claims}
        secondary_claims = [item for item in original_claims if str(item.get("claim_id") or "") not in preferred_ids]
        # Soft focus keeps secondary claims visible while biasing the Evidence Agent toward the two highest-value claims.
        claims = (preferred_claims + secondary_claims)[:4]
        if preferred_claims:
            evidence_focus_applied = True
            evidence_focus_reason = "soft_prefer_top2_high_importance_empirical_or_unsupported_claims"

    effective_target_claim_ids = [item.get("claim_id") for item in claims if item.get("claim_id")]
    if effective_target_claim_ids or target_evidence_ids:
        evidence = [item for item in evidence if item.get("claim_id") in effective_target_claim_ids or item.get("evidence_id") in (target_evidence_ids or [])] or evidence
    unresolved = state.get("unresolved_questions", [])[:4] if action_type in {"verify_evidence", "request_evidence_recheck", "challenge_previous_hypothesis"} else []
    allowed_claim_ids = [
        item.get("claim_id")
        for item in claims[:4]
        if item.get("claim_id") in real_claim_ids
    ]
    preferred_claim_ids = [
        item.get("claim_id")
        for item in preferred_claims[:2]
        if item.get("claim_id") in real_claim_ids
    ]
    original_allowed_claim_ids = [
        item.get("claim_id")
        for item in original_claims[:4]
        if item.get("claim_id") in real_claim_ids
    ]
    support_diversity_by_claim, independent_support_needs, quote_ids_to_avoid_by_claim, first_support_needs = support_diversity_for_claims(allowed_claim_ids)
    return {
        "active_focus": state.get("active_focus", state.get("last_focus", "")),
        "action_type": action_type,
        "allowed_claim_ids": allowed_claim_ids,
        "target_claims": claims[:4],
        "target_flaws": target_flaws,
        "negative_evidence_instruction": "When target_flaws are present, return negative/missing evidence only if a copied raw_quote directly grounds the weakness; otherwise return unresolved_questions.",
        "evidence_focus_mode": "soft_preferred_claims_v2",
        "evidence_focus_applied": evidence_focus_applied,
        "evidence_focus_reason": evidence_focus_reason,
        "evidence_focus_original_claim_ids": original_allowed_claim_ids,
        "evidence_focus_selected_claim_ids": allowed_claim_ids,
        "evidence_focus_preferred_claim_ids": preferred_claim_ids,
        "evidence_focus_original_claim_count": len(original_allowed_claim_ids),
        "evidence_focus_selected_claim_count": len(allowed_claim_ids),
        "evidence_focus_preferred_claim_count": len(preferred_claim_ids),
        "fallback_claim_targets_omitted": omitted_fallback_claim_ids[:4],
        "fallback_targets_replaced_with_real_candidates": fallback_targets_replaced_with_real_candidates,
        "target_evidence": evidence[:5],
        "support_diversity_by_claim": support_diversity_by_claim,
        "first_support_needs": first_support_needs,
        "independent_support_needs": independent_support_needs,
        "quote_ids_to_avoid_by_claim": quote_ids_to_avoid_by_claim,
        "evidence_gaps": _open_evidence_gaps(state)[:5],
        "unresolved_questions": unresolved,
        "conflict_summary": state.get("conflict_summary", [])[:3],
        "current_hypotheses": state.get("current_hypotheses", [])[:4] if action_type in {"request_evidence_recheck", "challenge_previous_hypothesis"} else [],
    }


def _render_critique_state_slice(state: Dict[str, Any], target_claim_ids: Optional[Sequence[str]] = None, target_flaw_ids: Optional[Sequence[str]] = None, target_evidence_ids: Optional[Sequence[str]] = None, action_type: str = "analyze_flaws") -> Dict[str, Any]:
    claims = _filter_items_by_ids(state.get("claims", []), "claim_id", target_claim_ids, 4)
    flaws = state.get("flaw_candidates", [])
    if target_claim_ids or target_flaw_ids:
        flaws = [item for item in flaws if item.get("flaw_id") in (target_flaw_ids or []) or any(claim_id in (target_claim_ids or []) for claim_id in item.get("related_claim_ids", []))] or flaws
    if action_type == "challenge_previous_hypothesis":
        claims = [item for item in claims if item.get("status") in {"supported", "uncertain", "partially_supported"}] or claims
    # Mainline-Final-Integrated P0-3: in ``challenge_previous_hypothesis`` mode
    # the critique worker must be able to see every paper-grounded negative
    # evidence record produced by the previous turn (typically by the
    # ``hard_negative_discovery_override`` recheck pass), even if that
    # evidence's claim_id is not listed in ``target_claim_ids``.  Otherwise
    # the worker correctly reports "No verified negative evidence found in
    # current state slice", which causes the recovery patch to be blocked
    # with BLOCKED_BY_POLICY despite the state actually containing a
    # ``verified_negative_flaw_count >= 1``.  To fix this we union all claim
    # ids that already host grounded paper-negative evidence into the
    # critique-visible claim set before evidence filtering happens.
    if action_type == "challenge_previous_hypothesis":
        negative_evidence_claim_ids: List[str] = []
        for item in state.get("evidence_map", []) or []:
            if not isinstance(item, dict):
                continue
            if _is_paper_negative_evidence_record(item):
                cid = str(item.get("claim_id") or "").strip()
                if cid and cid not in negative_evidence_claim_ids:
                    negative_evidence_claim_ids.append(cid)
        if negative_evidence_claim_ids:
            existing_claim_id_set = {str(item.get("claim_id") or "") for item in claims if item.get("claim_id")}
            extra_claim_ids = [cid for cid in negative_evidence_claim_ids if cid and cid not in existing_claim_id_set]
            if extra_claim_ids:
                extra_claim_records = [
                    item for item in state.get("claims", []) or []
                    if isinstance(item, dict) and str(item.get("claim_id") or "") in extra_claim_ids
                ]
                claims = list(claims) + extra_claim_records
    claim_ids = [str(item.get("claim_id") or "") for item in claims if item.get("claim_id")]
    target_evidence_id_set = {str(item) for item in (target_evidence_ids or []) if str(item)}
    evidence = [
        item for item in state.get("evidence_map", []) or []
        if not claim_ids or item.get("claim_id") in claim_ids or str(item.get("evidence_id") or "") in target_evidence_id_set
    ]
    negative_evidence = [item for item in evidence if _is_paper_negative_evidence_record(item)]
    negative_binding = _negative_evidence_binding_view(state)
    unlinked_negative_evidence_ids = {
        str(item.get("evidence_id") or "")
        for item in negative_binding["unlinked_negative_evidence_candidates"]
    }
    unlinked_negative_evidence = [
        item for item in negative_evidence
        if str(item.get("evidence_id") or "") in unlinked_negative_evidence_ids
    ]
    negative_evidence_by_claim: Dict[str, List[str]] = {}
    strong_support_by_claim: Dict[str, List[str]] = {}
    for item in evidence:
        claim_id = str(item.get("claim_id") or "")
        if _is_paper_negative_evidence_record(item):
            negative_evidence_by_claim.setdefault(claim_id, []).append(str(item.get("evidence_id") or ""))
        if item.get("strength") == "strong" and item.get("stance") in {"supports", "partially_supports"}:
            strong_support_by_claim.setdefault(claim_id, []).append(str(item.get("evidence_id") or ""))
    target_evidence = _prioritize_critique_evidence(evidence, target_evidence_id_set)
    recovery_hydration = _recovery_hydration_slice(state)
    return {
        "active_focus": state.get("active_focus", state.get("last_focus", "")),
        "action_type": action_type,
        "claims": claims[:4],
        "target_evidence": target_evidence[:6],
        "negative_evidence_candidates": negative_evidence[:4],
        "unlinked_negative_evidence_candidates": unlinked_negative_evidence[:4],
        "negative_evidence_by_claim": {claim_id: ids[:4] for claim_id, ids in negative_evidence_by_claim.items()},
        "strong_support_by_claim": {claim_id: ids[:4] for claim_id, ids in strong_support_by_claim.items()},
        "invalid_negative_grounding_conflicts": negative_binding["invalid_negative_grounding_conflicts"][:4],
        "recovery_hydration": recovery_hydration,
        "grounded_flaw_binding_rule": "If a flaw is based on negative_evidence_candidates, cite that id in both evidence_ids and negative_evidence_ids.",
        "flaw_candidates": flaws[:5],
        "evidence_gaps": _open_evidence_gaps(state)[:5],
        "conflict_summary": state.get("conflict_summary", [])[:4],
        "revision_summary": state.get("revision_summary", [])[:4],
    }


def _render_general_reviewer_state_slice(state: Dict[str, Any], action_type: str = "summarize_progress", target_claim_ids: Optional[Sequence[str]] = None, target_evidence_ids: Optional[Sequence[str]] = None, target_flaw_ids: Optional[Sequence[str]] = None) -> Dict[str, Any]:
    claims = _filter_items_by_ids(state.get("claims", []), "claim_id", target_claim_ids, 3)
    evidence = state.get("evidence_map", [])
    if target_claim_ids or target_evidence_ids:
        evidence = [item for item in evidence if item.get("claim_id") in (target_claim_ids or []) or item.get("evidence_id") in (target_evidence_ids or [])] or evidence
    flaws = state.get("flaw_candidates", [])
    if target_claim_ids or target_flaw_ids:
        flaws = [item for item in flaws if item.get("flaw_id") in (target_flaw_ids or []) or any(claim_id in (target_claim_ids or []) for claim_id in item.get("related_claim_ids", []))] or flaws
    return {
        "active_focus": state.get("active_focus", state.get("last_focus", "")),
        "action_type": action_type,
        "claims": claims[:3],
        "evidence_map": evidence[:3],
        "flaw_candidates": flaws[:3],
        "open_unresolved_questions": [item for item in state.get("unresolved_questions", [])[:4] if item.get("status") != "resolved"],
        "risk_profile": state.get("risk_profile", {}),
        "revision_summary": state.get("revision_summary", [])[:3],
    }


def render_review_observation(task: Dict[str, Any]) -> str:
    state = compact_review_state_for_prompt(task["review_state"])
    return (
        f"{_render_review_header(task)}\n"
        f"# Focus Context\n{_render_focus_context(state)}\n\n"
        f"# Paper Excerpt\n{_render_paper_excerpt(task)}\n\n"
        f"# Compact ReviewState\n{json.dumps(state, ensure_ascii=False, indent=2)}\n\n"
        f"# Recent Turn Log\n{_render_recent_turn_summary(task)}\n"
    )


def render_manager_observation(task: Dict[str, Any]) -> str:
    state = compact_review_state_for_prompt(task["review_state"])
    manager_slice = _render_manager_state_slice(state)
    return (
        f"{_render_review_header(task)}\n"
        f"# Manager Focus Context\n{_render_focus_context(state)}\n\n"
        f"# Paper Summary Excerpt\n{_render_paper_excerpt(task, max_length=700)}\n\n"
        f"# Manager Risk and Progress Slice\n{json.dumps(manager_slice, ensure_ascii=False, indent=2)}\n\n"
        f"# Recent Turn Log\n{_render_recent_turn_summary(task)}\n"
    )


def render_claim_observation(task: Dict[str, Any], manager_payload: Optional[Dict[str, Any]] = None) -> str:
    state = compact_review_state_for_prompt(task["review_state"])
    manager_payload = manager_payload or {}
    claim_slice = _render_claim_state_slice(state, action_type=manager_payload.get("action_type", "extract_claims"), target_claim_ids=manager_payload.get("target_claim_ids", []))
    focus = manager_payload.get("focus", "")
    return (
        f"{_render_review_header(task)}\n"
        f"# Claim Focus\n{_render_focus_context(state, fallback_focus=focus)}\n\n"
        f"# Claim-Relevant Paper Excerpt\n{_render_evidence_context(task, max_length=2200)}\n\n"
        f"# Claim State Slice\n{json.dumps(claim_slice, ensure_ascii=False, indent=2)}\n\n"
        f"# Recent Turn Log\n{_render_recent_turn_summary(task, max_items=1)}\n"
    )


def _prompt_quote_bank_entries(quote_bank: Sequence[Dict[str, Any]], max_items: int = 6) -> List[Dict[str, Any]]:
    entries: List[Dict[str, Any]] = []
    for item in quote_bank[:max_items]:
        if not isinstance(item, dict):
            continue
        entries.append(
            {
                "quote_id": str(item.get("quote_id") or ""),
                "source_bucket": str(item.get("source_bucket") or ""),
                "source_locator": str(item.get("source_locator") or ""),
                "raw_quote": str(item.get("raw_quote") or ""),
                "claim_overlap_score": _normalize_int(item.get("claim_overlap_score"), default=0, min_value=0),
                "support_role_hint": str(item.get("support_role_hint") or ""),
                "copy_rule": str(item.get("copy_rule") or "Copy raw_quote exactly; do not paraphrase."),
            }
        )
    return entries


def _prompt_negative_quote_bank_entries(quote_bank: Sequence[Dict[str, Any]], max_items: int = 5) -> List[Dict[str, Any]]:
    """Return negative quote-bank entries for Critique Agent grounding.

    The Critique Agent previously saw only the flattened paper evidence context,
    so actionable flaw formation depended on rediscovering negative anchors from
    prose.  This compact view exposes verified quote ids and negative types, but
    filters neutral control contexts so with/without ablation descriptions are
    not laundered into hard-negative flaws.
    """
    scored: List[Tuple[int, int, Dict[str, Any]]] = []
    for idx, item in enumerate(quote_bank or []):
        if not isinstance(item, dict):
            continue
        if str(item.get("source_bucket") or "") != "negative_or_gap":
            continue
        neg_type = _negative_evidence_type_for_record(item)
        if neg_type == "neutral_control_context":
            continue
        score = 0 if neg_type in ACTIONABLE_NEGATIVE_EVIDENCE_TYPES else 1
        scored.append((score, idx, item))
    def _prompt_safe_negative_quote_text(item: Dict[str, Any], neg_type: str) -> str:
        raw_quote = str(item.get("raw_quote") or "").strip()
        if not raw_quote:
            return ""
        sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+", raw_quote) if part.strip()]
        actionable_sentences: List[str] = []
        for sentence in sentences:
            if _NEG_TYPE_NEUTRAL_CONTEXT_RE.search(sentence):
                continue
            sentence_type = _classify_negative_evidence_type(sentence)
            if sentence_type in ACTIONABLE_NEGATIVE_EVIDENCE_TYPES:
                actionable_sentences.append(sentence)
        if actionable_sentences:
            return " ".join(actionable_sentences[:2])
        if _NEG_TYPE_NEUTRAL_CONTEXT_RE.search(raw_quote):
            return ""
        return raw_quote

    entries: List[Dict[str, Any]] = []
    for _, _, item in sorted(scored, key=lambda pair: (pair[0], pair[1]))[:max_items]:
        neg_type = _negative_evidence_type_for_record(item)
        prompt_quote = _prompt_safe_negative_quote_text(item, neg_type)
        if not prompt_quote or neg_type == "generic_gap":
            continue
        entries.append({
            "quote_id": str(item.get("quote_id") or ""),
            "source_locator": str(item.get("source_locator") or ""),
            "negative_evidence_type": neg_type,
            "negative_evidence_actionability": (
                "actionable" if neg_type in ACTIONABLE_NEGATIVE_EVIDENCE_TYPES else "limitation_or_gap"
            ),
            "raw_quote": prompt_quote,
            "copy_rule": "If used for a flaw, cite this quote_id in negative_evidence_ids and explain the paper-side weakness; do not treat neutral controls as flaws.",
        })
    return entries


def render_evidence_observation(task: Dict[str, Any], manager_payload: Optional[Dict[str, Any]] = None) -> str:
    state = compact_review_state_for_prompt(task["review_state"])
    manager_payload = manager_payload if manager_payload is not None else {}
    evidence_slice = _render_evidence_state_slice(
        state,
        target_claim_ids=manager_payload.get("target_claim_ids", []),
        target_evidence_ids=manager_payload.get("target_evidence_ids", []),
        target_flaw_ids=manager_payload.get("target_flaw_ids", []),
        action_type=manager_payload.get("action_type", "verify_evidence"),
    )
    evidence_context_target_claim_ids = (
        evidence_slice.get("evidence_focus_preferred_claim_ids")
        or evidence_slice.get("allowed_claim_ids")
        or manager_payload.get("target_claim_ids", [])
    )
    evidence_context, evidence_context_meta = _render_evidence_context_with_meta(
        task,
        max_length=2300,
        state=state,
        target_claim_ids=evidence_context_target_claim_ids,
    )
    evidence_quote_bank = list(evidence_context_meta.get("evidence_quote_bank", []) or [])
    evidence_context_meta_for_log = {k: v for k, v in evidence_context_meta.items() if k != "evidence_quote_bank"}
    manager_payload.update(evidence_context_meta_for_log)
    task["_latest_evidence_context_meta"] = dict(evidence_context_meta)
    omitted_fallback_claim_ids = evidence_slice.get("fallback_claim_targets_omitted", [])
    manager_payload["fallback_claim_targets_omitted"] = omitted_fallback_claim_ids
    manager_payload["fallback_claim_targets_omitted_count"] = len(omitted_fallback_claim_ids)
    manager_payload["fallback_targets_replaced_with_real_candidates"] = bool(
        evidence_slice.get("fallback_targets_replaced_with_real_candidates", False)
    )
    for key in (
        "evidence_focus_mode",
        "evidence_focus_applied",
        "evidence_focus_reason",
        "evidence_focus_original_claim_ids",
        "evidence_focus_selected_claim_ids",
        "evidence_focus_preferred_claim_ids",
        "evidence_focus_original_claim_count",
        "evidence_focus_selected_claim_count",
        "evidence_focus_preferred_claim_count",
    ):
        manager_payload[key] = evidence_slice.get(key)
    evidence_slice["evidence_context_meta"] = evidence_context_meta_for_log
    first_support_needs = evidence_slice.get("first_support_needs", []) or []
    independent_support_needs = evidence_slice.get("independent_support_needs", []) or []
    quote_ids_to_avoid_by_claim = evidence_slice.get("quote_ids_to_avoid_by_claim", {}) or {}
    used_quote_ids_for_needs = {
        str(quote_id)
        for quote_ids in quote_ids_to_avoid_by_claim.values()
        for quote_id in (quote_ids or [])
        if str(quote_id)
    }
    used_buckets_for_needs = {
        str(bucket)
        for need in independent_support_needs
        for bucket in (need.get("used_source_buckets") or [])
        if str(bucket)
    }
    if independent_support_needs and evidence_quote_bank:
        def _independent_quote_priority(item: Dict[str, Any]) -> Tuple[int, int, int]:
            quote_id = str(item.get("quote_id") or "")
            bucket = str(item.get("source_bucket") or "")
            locator = str(item.get("source_locator") or "")
            avoid_penalty = 1 if quote_id in used_quote_ids_for_needs else 0
            same_bucket_penalty = 1 if bucket in used_buckets_for_needs else 0
            specificity_bonus = -1 if _is_specific_locator(locator) else 0
            return (avoid_penalty, same_bucket_penalty, specificity_bonus)
        evidence_quote_bank = sorted(evidence_quote_bank, key=_independent_quote_priority)
    prompt_quote_bank = _prompt_quote_bank_entries(evidence_quote_bank)
    preferred_claim_ids = evidence_slice.get("evidence_focus_preferred_claim_ids", [])
    targeting_guidance = ""
    if evidence_slice.get("evidence_focus_applied") and preferred_claim_ids:
        targeting_guidance = (
            "# Evidence Targeting Guidance\n"
            "Prioritize new evidence for evidence_focus_preferred_claim_ids first, "
            "but keep other allowed_claim_ids available when they have concrete method/result/table support.\n\n"
        )
    focus = manager_payload.get("focus", "")
    quote_bank_block = ""
    if prompt_quote_bank:
        quote_bank_block = (
            "# Evidence Quote Bank\n"
            f"{json.dumps({'evidence_quote_bank': prompt_quote_bank}, ensure_ascii=False, indent=2)}\n\n"
        )
    first_support_block = ""
    if first_support_needs:
        first_support_payload = {
            "first_support_needs": first_support_needs[:4],
            "rule": (
                "First-support formation has priority over unresolved questions. "
                "For claims listed here, do not apply duplicate/independent-source avoidance yet: "
                "there is no existing support to duplicate. If Evidence Quote Bank or the visible paper excerpt "
                "contains a quote that grounds one listed claim, output at least one evidence_map item. "
                "Use unresolved_questions only when no copied quote can be bound to any listed claim."
            ),
        }
        first_support_block = (
            "# First Evidence Formation\n"
            f"{json.dumps(first_support_payload, ensure_ascii=False, indent=2)}\n\n"
        )
    independent_support_block = ""
    if independent_support_needs:
        independent_payload = {
            "independent_support_needs": independent_support_needs[:4],
            "quote_ids_to_avoid_by_claim": quote_ids_to_avoid_by_claim,
            "rule": "For listed claims, prefer a different quote_id/source_locator than the already used quote_ids. Reusing the same quote_id is duplicate support and should only be done when no independent source is visible; in that case emit an unresolved_question instead of another strong support item.",
        }
        independent_support_block = (
            "# Independent Evidence Diversification\n"
            f"{json.dumps(independent_payload, ensure_ascii=False, indent=2)}\n\n"
        )
    target_flaw_block = ""
    if evidence_slice.get("target_flaws"):
        target_flaw_payload = {
            "target_flaws": evidence_slice.get("target_flaws", [])[:4],
            "negative_evidence_instruction": evidence_slice.get("negative_evidence_instruction", ""),
        }
        target_flaw_block = (
            "# Evidence Target Flaws\n"
            f"{json.dumps(target_flaw_payload, ensure_ascii=False, indent=2)}\n\n"
        )
    open_check_payload = {
        key: evidence_slice.get(key, [])[:5]
        for key in ("evidence_gaps", "unresolved_questions", "current_hypotheses")
        if evidence_slice.get(key)
    }
    open_check_block = ""
    if open_check_payload:
        open_check_block = (
            "# Evidence Open Checks\n"
            f"{json.dumps(open_check_payload, ensure_ascii=False, indent=2)}\n\n"
        )
    action_payload = {
        "action_type": evidence_slice.get("action_type", "verify_evidence"),
        "allowed_claim_ids": evidence_slice.get("allowed_claim_ids", [])[:4],
        "target_evidence_ids": manager_payload.get("target_evidence_ids", [])[:4],
    }
    return (
        f"{_render_review_header(task)}\n"
        f"# Evidence Action Context\n{json.dumps(action_payload, ensure_ascii=False, indent=2)}\n\n"
        f"{first_support_block}"
        f"{target_flaw_block}"
        f"{quote_bank_block}"
        f"{independent_support_block}"
        f"{open_check_block}"
        f"# Evidence State Slice\n{json.dumps(evidence_slice, ensure_ascii=False, indent=2)}\n\n"
        f"# Recent Turn Log\n{_render_recent_turn_summary(task, max_items=1)}\n\n"
        f"# Evidence Focus\n{_render_focus_context(state, fallback_focus=focus)}\n\n"
        f"{targeting_guidance}"
        f"# Evidence-Relevant Paper Excerpt\n{evidence_context}\n"
    )


def render_critique_observation(task: Dict[str, Any], manager_payload: Optional[Dict[str, Any]] = None) -> str:
    state = compact_review_state_for_prompt(task["review_state"])
    manager_payload = manager_payload or {}
    critique_slice = _render_critique_state_slice(
        state,
        target_claim_ids=manager_payload.get("target_claim_ids", []),
        target_flaw_ids=manager_payload.get("target_flaw_ids", []),
        target_evidence_ids=manager_payload.get("target_evidence_ids", []),
        action_type=manager_payload.get("action_type", "analyze_flaws"),
    )
    focus = manager_payload.get("focus", "")
    critique_context, critique_context_meta = _render_evidence_context_with_meta(
        task,
        max_length=1800,
        state=state,
        target_claim_ids=manager_payload.get("target_claim_ids", []),
    )
    body, _ = _clean_paper_body(task.get("paper_text", ""))
    direct_negative_quote_bank = _build_critique_negative_quote_bank(body, max_quotes=6)
    negative_quote_bank = _prompt_negative_quote_bank_entries(
        list(direct_negative_quote_bank) + list(critique_context_meta.get("evidence_quote_bank", []) or [])
    )
    negative_quote_block = ""
    if negative_quote_bank:
        negative_quote_block = (
            "# Critique Negative Quote Bank\n"
            f"{json.dumps({'negative_quote_bank': negative_quote_bank}, ensure_ascii=False, indent=2)}\n\n"
        )
    negative_grounding_rules_block = ""
    if negative_quote_bank:
        negative_grounding_rules_block = (
            "# Critique Negative Grounding Rules\n"
            "Use a quote from negative_quote_bank only when it states a paper-side weakness. "
            "If you create a flaw from such a quote, copy the quote_id into both evidence_ids "
            "and negative_evidence_ids, preserve negative_evidence_type, and explain why the quote "
            "grounds the weakness. Actionable types are missing_ablation, missing_baseline, "
            "insufficient_evaluation, negative_result, and direct_contradiction. Scope/reproducibility "
            "quotes are assessment limitations unless the paper itself frames them as a concrete failure. "
            "Do not turn generic gaps, external-baseline unavailability, neutral with/without controls, "
            "or system/context limitations into grounded weaknesses.\n\n"
        )
    return (
        f"{_render_review_header(task)}\n"
        f"# Critique Focus\n{_render_focus_context(state, fallback_focus=focus)}\n\n"
        f"# Critique-Relevant Paper Evidence Context\n{critique_context}\n\n"
        f"{negative_quote_block}"
        f"{negative_grounding_rules_block}"
        f"# Critique State Slice\n{json.dumps(critique_slice, ensure_ascii=False, indent=2)}\n\n"
        f"# Recent Turn Log\n{_render_recent_turn_summary(task, max_items=1)}\n"
    )


def render_general_reviewer_observation(task: Dict[str, Any], manager_payload: Optional[Dict[str, Any]] = None) -> str:
    state = compact_review_state_for_prompt(task["review_state"])
    manager_payload = manager_payload or {}
    focus = manager_payload.get("focus", "")
    compact_slice = _render_general_reviewer_state_slice(
        state,
        action_type=manager_payload.get("action_type", "summarize_progress"),
        target_claim_ids=manager_payload.get("target_claim_ids", []),
        target_evidence_ids=manager_payload.get("target_evidence_ids", []),
        target_flaw_ids=manager_payload.get("target_flaw_ids", []),
    )
    return (
        f"{_render_review_header(task)}\n"
        f"# Review Focus\n{_render_focus_context(state, fallback_focus=focus)}\n\n"
        f"# Paper Summary Excerpt\n{_render_paper_excerpt(task, max_length=700)}\n\n"
        f"# General Review Slice\n{json.dumps(compact_slice, ensure_ascii=False, indent=2)}\n\n"
        f"# Recent Turn Log\n{_render_recent_turn_summary(task, max_items=1)}\n"
    )


def infer_final_decision(state: Dict[str, Any], manager_payload: Dict[str, Any]) -> str:
    # Binary accept/reject remains a health-check projection of the richer
    # recommendation view. Only strict accept_like maps to accept; borderline
    # and not-assessable cases stay conservative instead of becoming false
    # accepts.
    return infer_final_recommendation_view(state or {}, manager_payload or {}).get("binary_decision", "reject")


def _render_strengths(state: Dict[str, Any]) -> List[str]:
    strengths = []
    real_claim_ids = _decision_real_claim_ids(state)
    for claim in state.get("claims", []):
        if claim.get("status") in {"supported", "partially_supported"}:
            strengths.append(f"The paper advances the claim that {claim['claim']}.")
    for evidence in state.get("evidence_map", []):
        if _is_real_bound_support(evidence, real_claim_ids):
            strengths.append(f"Supporting evidence is reported in {evidence['source']}: {evidence['evidence']}.")
    return strengths[:4]


_NEGATIVE_EVIDENCE_STANCES = frozenset(
    {
        "contradicts",
        "contradict",
        "refutes",
        "refute",
        "weakens",
        "weaken",
        "undermines",
        "undermine",
        "partially_contradicts",
        "partially_refutes",
        "negative",
        "missing",
        "not_grounded",
        "unsupported",
        "opposes",
        "oppose",
    }
)


def _is_system_generated_evidence_record(item: Dict[str, Any]) -> bool:
    source = str(item.get("source") or "").strip().lower()
    evidence_id = str(item.get("evidence_id") or "").strip().lower()
    binding_status = str(item.get("binding_status") or "").strip().lower()
    return (
        source in {"system recovery salvage", "fallback-extraction", "system_meta", "system-meta"}
        or evidence_id.startswith("evidence-recovery-")
        or evidence_id.startswith("evidence-fallback-")
        or binding_status in {"fallback_unverified", "fallback_bound"}
    )


def _is_negative_evidence_record(item: Dict[str, Any]) -> bool:
    if not isinstance(item, dict):
        return False
    stance = str(item.get("stance") or "").strip().lower()
    strength = str(item.get("strength") or "").strip().lower()
    return stance in _NEGATIVE_EVIDENCE_STANCES or strength == "missing"


def _is_paper_negative_evidence_record(item: Dict[str, Any]) -> bool:
    return (
        _is_negative_evidence_record(item)
        and not _is_system_generated_evidence_record(item)
        and _is_real_paper_claim_id(item.get("claim_id"))
    )


def _state_requires_verified_grounding(state: Dict[str, Any]) -> bool:
    if state.get("evidence_quote_bank"):
        return True
    return any(
        isinstance(item, dict) and str(item.get("verified_grounding_label") or "") not in {"", "unjudged"}
        for item in state.get("evidence_map", []) or []
    )


def _is_grounded_paper_negative_evidence_record(item: Dict[str, Any], state: Dict[str, Any]) -> bool:
    if not _is_paper_negative_evidence_record(item):
        return False
    if not _state_requires_verified_grounding(state):
        return True
    if not _is_verified_paper_grounded_evidence(item):
        return False
    semantic_label = str(item.get("semantic_grounding_label") or "").strip()
    if semantic_label not in {"semantic_negative_verified", "semantic_support_verified"}:
        return False
    neg_type = _negative_evidence_type_for_record(item)
    if neg_type in {"neutral_control_context", "generic_gap", "bibliographic_or_title_noise", "neutral_instruction_noise"}:
        return False
    return True


def _compact_evidence_for_prompt(items: Sequence[Dict[str, Any]], max_items: int = 6) -> List[Dict[str, Any]]:
    indexed = [(idx, item) for idx, item in enumerate(items or []) if isinstance(item, dict)]
    if len(indexed) <= max_items:
        return [item for _, item in indexed]

    def score(pair: tuple[int, Dict[str, Any]]) -> tuple[int, int]:
        idx, item = pair
        if _is_paper_negative_evidence_record(item):
            return (0, idx)
        if item.get("strength") == "strong" and item.get("stance") in {"supports", "partially_supports"}:
            return (1, idx)
        return (2, idx)

    selected = {idx for idx, _ in sorted(indexed, key=score)[:max_items]}
    return [item for idx, item in indexed if idx in selected]


def _prioritize_critique_evidence(items: Sequence[Dict[str, Any]], target_evidence_ids: set[str]) -> List[Dict[str, Any]]:
    indexed = [(idx, item) for idx, item in enumerate(items or []) if isinstance(item, dict)]

    def score(pair: tuple[int, Dict[str, Any]]) -> tuple[int, int]:
        idx, item = pair
        evidence_id = str(item.get("evidence_id") or "")
        if evidence_id in target_evidence_ids:
            return (0, idx)
        if _is_paper_negative_evidence_record(item):
            return (1, idx)
        if item.get("strength") == "strong" and item.get("stance") in {"supports", "partially_supports"}:
            return (2, idx)
        return (3, idx)

    return [item for _, item in sorted(indexed, key=score)]


def _flaw_cited_evidence_records(flaw: Dict[str, Any], state: Dict[str, Any]) -> List[Dict[str, Any]]:
    if not isinstance(flaw, dict):
        return []
    evidence_map = state.get("evidence_map") or []
    by_id: Dict[str, Dict[str, Any]] = {}
    for ev in evidence_map:
        if isinstance(ev, dict):
            eid = str(ev.get("evidence_id") or "")
            if eid:
                by_id[eid] = ev
    cited: List[Dict[str, Any]] = []
    for eid in flaw.get("evidence_ids") or []:
        record = by_id.get(str(eid))
        if isinstance(record, dict):
            cited.append(record)
    return cited


def _flaw_explicit_negative_evidence_ids(flaw: Dict[str, Any]) -> List[str]:
    if not isinstance(flaw, dict):
        return []
    raw = (
        flaw.get("negative_evidence_ids")
        or flaw.get("hard_negative_evidence_ids")
        or flaw.get("contradicting_evidence_ids")
        or []
    )
    if isinstance(raw, str):
        raw = [raw]
    return [str(eid) for eid in raw if isinstance(eid, (str, int)) and str(eid).strip()]


def _evidence_records_by_id(state: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    by_id: Dict[str, Dict[str, Any]] = {}
    for ev in state.get("evidence_map") or []:
        if isinstance(ev, dict):
            eid = str(ev.get("evidence_id") or "")
            if eid:
                by_id[eid] = ev
    return by_id


def _flaw_valid_explicit_negative_evidence_ids(flaw: Dict[str, Any], state: Dict[str, Any]) -> List[str]:
    explicit_ids = _flaw_explicit_negative_evidence_ids(flaw)
    if not explicit_ids:
        return []
    by_id = _evidence_records_by_id(state)
    if not by_id:
        return explicit_ids
    valid: List[str] = []
    seen: set[str] = set()
    for eid in explicit_ids:
        if eid in seen:
            continue
        record = by_id.get(eid)
        if isinstance(record, dict) and _is_grounded_paper_negative_evidence_record(record, state):
            valid.append(eid)
            seen.add(eid)
    return valid


def _flaw_negative_grounding_conflicts(flaw: Dict[str, Any], state: Dict[str, Any]) -> List[Dict[str, Any]]:
    if str(flaw.get("status") or "") in {"downgraded", "retracted"}:
        return []
    explicit_ids = _flaw_explicit_negative_evidence_ids(flaw)
    if not explicit_ids:
        return []
    by_id = _evidence_records_by_id(state)
    if not by_id:
        return []
    conflicts: List[Dict[str, Any]] = []
    seen: set[str] = set()
    for eid in explicit_ids:
        if eid in seen:
            continue
        seen.add(eid)
        record = by_id.get(eid)
        if not isinstance(record, dict):
            conflicts.append({
                "flaw_id": str(flaw.get("flaw_id") or ""),
                "evidence_id": eid,
                "reason": "negative_evidence_id_unresolved",
            })
            continue
        if not _is_paper_negative_evidence_record(record):
            conflicts.append({
                "flaw_id": str(flaw.get("flaw_id") or ""),
                "evidence_id": eid,
                "reason": "negative_evidence_id_not_negative_stance",
                "stance": str(record.get("stance") or ""),
                "strength": str(record.get("strength") or ""),
                "source": str(record.get("source") or ""),
            })
        elif not _is_grounded_paper_negative_evidence_record(record, state):
            conflicts.append({
                "flaw_id": str(flaw.get("flaw_id") or ""),
                "evidence_id": eid,
                "reason": "negative_evidence_id_not_verified",
                "verified_grounding_label": str(record.get("verified_grounding_label") or ""),
            })
    return conflicts


def _flaw_valid_negative_evidence_ids(flaw: Dict[str, Any], state: Dict[str, Any]) -> List[str]:
    valid: List[str] = []
    seen: set[str] = set()
    # R4: drop NOISE_NEGATIVE_TYPES (bibliographic/title, neutral-instruction)
    # so they cannot anchor a verified negative concern (and thus cannot enter
    # contested-support or recovery). Noise records stay in evidence_map.
    noise_ids = {
        str(item.get("evidence_id") or "")
        for item in state.get("evidence_map", []) or []
        if isinstance(item, dict)
        and _negative_evidence_type_for_record(item) in NOISE_NEGATIVE_TYPES
    }
    for source_ids in (
        _flaw_valid_explicit_negative_evidence_ids(flaw, state),
        _stance_based_negative_evidence_ids(flaw, state),
        _related_claim_negative_evidence_ids(flaw, state),
    ):
        for eid in source_ids:
            if eid in noise_ids:
                continue
            if eid not in seen:
                valid.append(eid)
                seen.add(eid)
    return valid


def _negative_evidence_type_counts_for_flaw(flaw: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, int]:
    by_id = _evidence_records_by_id(state)
    counts: Counter[str] = Counter()
    for eid in _flaw_valid_negative_evidence_ids(flaw, state):
        record = by_id.get(eid)
        if isinstance(record, dict):
            counts[_negative_evidence_type_for_record(record)] += 1
    return dict(counts)


def _verified_actionable_negative_evidence_ids_for_flaw(flaw: Dict[str, Any], state: Dict[str, Any]) -> List[str]:
    by_id = _evidence_records_by_id(state)
    actionable: List[str] = []
    for eid in _flaw_valid_negative_evidence_ids(flaw, state):
        record = by_id.get(eid)
        if isinstance(record, dict) and _negative_evidence_type_for_record(record) in ACTIONABLE_NEGATIVE_EVIDENCE_TYPES:
            actionable.append(eid)
    return actionable


def _negative_evidence_binding_view(state: Dict[str, Any]) -> Dict[str, Any]:
    negative_evidence = [
        item for item in state.get("evidence_map", []) or []
        if isinstance(item, dict) and _is_grounded_paper_negative_evidence_record(item, state)
    ]
    negative_evidence_ids = {
        str(item.get("evidence_id") or "")
        for item in negative_evidence
        if str(item.get("evidence_id") or "")
    }
    linked_ids: set[str] = set()
    conflicts: List[Dict[str, Any]] = []
    for flaw in state.get("flaw_candidates", []) or []:
        if not isinstance(flaw, dict):
            continue
        conflicts.extend(_flaw_negative_grounding_conflicts(flaw, state))
        for eid in _flaw_valid_negative_evidence_ids(flaw, state):
            if eid in negative_evidence_ids:
                linked_ids.add(eid)
    unlinked = [
        item for item in negative_evidence
        if str(item.get("evidence_id") or "") not in linked_ids
    ]
    return {
        "negative_evidence_candidates": negative_evidence,
        "linked_negative_evidence_ids": sorted(linked_ids),
        "unlinked_negative_evidence_candidates": unlinked,
        "invalid_negative_grounding_conflicts": conflicts,
    }


_NEGATIVE_GROUNDING_DIMENSION_PATTERNS = {
    "empirical": re.compile(r"\b(experiment|evaluation|baseline|ablation|dataset|metric|table|figure|result|benchmark|empirical|performance)\b", re.I),
    "method": re.compile(r"\b(method|methodology|approach|model|algorithm|framework|assumption|objective|theory|technical)\b", re.I),
    "novelty": re.compile(r"\b(novel|novelty|original|contribution|related work|prior work|incremental)\b", re.I),
    "clarity": re.compile(r"\b(clarity|clear|presentation|readability|reproduc|implementation|detail|code|hyperparameter)\b", re.I),
    "limitation": re.compile(r"\b(limit|limitation|missing|lack|insufficient|absent|unclear|gap|fail|does not|(?:do|does|did)\s+not\s+(?:prove|provide|show|report|evaluate|compare|include|establish)|not\s+(?:proven|proved|provided|reported|evaluated|compared|included|established)|open question|no baseline|no comparison|no evaluation)\b", re.I),
}


def _negative_grounding_dimensions(text: str) -> set[str]:
    value = str(text or "")
    return {name for name, pattern in _NEGATIVE_GROUNDING_DIMENSION_PATTERNS.items() if pattern.search(value)}


def _related_claim_negative_evidence_ids(flaw: Dict[str, Any], state: Dict[str, Any]) -> List[str]:
    if not isinstance(flaw, dict):
        return []
    related_claim_ids = {str(item).strip() for item in flaw.get("related_claim_ids") or [] if str(item).strip()}
    if not related_claim_ids:
        return []
    flaw_text = " ".join(str(flaw.get(key) or "") for key in ("title", "description", "source"))
    flaw_dims = _negative_grounding_dimensions(flaw_text)
    if not flaw_dims:
        return []
    inferred: List[str] = []
    seen: set[str] = set()
    for record in state.get("evidence_map", []) or []:
        if not isinstance(record, dict):
            continue
        evidence_id = str(record.get("evidence_id") or "").strip()
        if not evidence_id or evidence_id in seen:
            continue
        if str(record.get("claim_id") or "").strip() not in related_claim_ids:
            continue
        if not _is_grounded_paper_negative_evidence_record(record, state):
            continue
        evidence_text = " ".join(
            str(record.get(key) or "")
            for key in ("evidence", "raw_quote", "source", "source_locator", "support_source_bucket", "verified_source_bucket")
        )
        evidence_dims = _negative_grounding_dimensions(evidence_text)
        if flaw_dims & evidence_dims:
            inferred.append(evidence_id)
            seen.add(evidence_id)
    return inferred


def _stance_based_negative_evidence_ids(
    flaw: Dict[str, Any], state: Dict[str, Any]
) -> List[str]:
    """Infer hard-negative evidence anchors for ``flaw`` from evidence stance.

    Scans the cited ``evidence_ids`` of ``flaw`` against ``state.evidence_map``
    and returns the subset whose ``stance`` is in :data:`_NEGATIVE_EVIDENCE_STANCES`
    (``contradicts`` / ``refutes`` / ``weakens`` / ``missing`` / ...). These
    ids are a **derivation** of information already present in the state, not
    a new agent claim — so it is safe to attach them in the view-only
    ``decision_hygiene`` layer and keep the live state unchanged.

    Returns an empty list when the evidence_map is empty (so tests that
    omit the map do not accidentally gain inferred grounding) or when no
    cited evidence carries a negative stance.
    """
    if not isinstance(flaw, dict):
        return []
    evidence_map = state.get("evidence_map") or []
    if not evidence_map:
        return []
    by_id: Dict[str, Dict[str, Any]] = {}
    for ev in evidence_map:
        if isinstance(ev, dict):
            eid = str(ev.get("evidence_id") or "")
            if eid:
                by_id[eid] = ev
    inferred: List[str] = []
    seen: set[str] = set()
    for eid in flaw.get("evidence_ids") or []:
        eid_str = str(eid)
        if not eid_str or eid_str in seen:
            continue
        record = by_id.get(eid_str)
        if not isinstance(record, dict):
            continue
        if _is_grounded_paper_negative_evidence_record(record, state):
            inferred.append(eid_str)
            seen.add(eid_str)
    return inferred


def _verified_negative_evidence_ids_for_flaw(flaw: Dict[str, Any], state: Dict[str, Any]) -> List[str]:
    return _flaw_valid_negative_evidence_ids(flaw, state)


def _classify_flaw_final_view_layer(flaw: Dict[str, Any], state: Dict[str, Any]) -> str:
    if not isinstance(flaw, dict):
        return "assessment_limitation"
    status = str(flaw.get("status") or "candidate")
    if status in {"downgraded", "retracted"}:
        return "assessment_limitation"
    verified_negative_ids = _verified_negative_evidence_ids_for_flaw(flaw, state)
    if verified_negative_ids:
        actionable_ids = _verified_actionable_negative_evidence_ids_for_flaw(flaw, state)
        if actionable_ids:
            if status == "confirmed":
                return "grounded_weakness"
            # A verified, actionable negative candidate should surface in the
            # final diagnostic chain as a potential concern.  The separate
            # ``verified_potential_concern_count`` metric tracks verification
            # status, so the final-view layer can stay report-oriented instead
            # of using an exclusive intermediate layer that never reaches
            # ``potential_concern_count``.
            return "potential_concern"
        return "assessment_limitation"
    if _is_fallback_or_meta_flaw(flaw):
        return "assessment_limitation"
    if _is_system_assessment_limitation_flaw(flaw, state):
        return "assessment_limitation"
    explicit_negative_ids = _flaw_explicit_negative_evidence_ids(flaw)
    if explicit_negative_ids:
        by_id = _evidence_records_by_id(state)
        for eid in explicit_negative_ids:
            record = by_id.get(str(eid))
            if not isinstance(record, dict):
                continue
            neg_type = _negative_evidence_type_for_record(record)
            if neg_type not in {"neutral_control_context", "generic_gap", "bibliographic_or_title_noise", "neutral_instruction_noise"}:
                return "potential_concern"
        return "assessment_limitation"
    if flaw.get("evidence_ids"):
        return "potential_concern"
    return "assessment_limitation"


def _flaw_has_negative_grounding(flaw: Dict[str, Any], state: Dict[str, Any]) -> bool:
    """Return True iff the flaw is anchored by negative grounding.

    Resolution order:

    1. Use the explicit ``negative_evidence_ids`` field (or the legacy
       ``hard_negative_evidence_ids`` / ``contradicting_evidence_ids``
       aliases) when present.  The listed ids must resolve to records in
       ``evidence_map``; unresolved ids are ignored so the schema cannot
       claim grounding for an evidence id that does not exist.
    2. Fall back to scanning the cited ``evidence_ids`` records for a
       non-supports stance (``contradicts`` / ``refutes`` / ``missing`` etc.).
       This preserves backward compatibility for older runs that only
       populate ``evidence_ids``.

    A flaw whose only cited evidence supports the related claim is *not* a
    grounded paper weakness; the supporting evidence anchors the *claim*, not
    the flaw.  Such flaws are demoted to ``Potential concerns requiring
    verification`` in the final report.
    """
    if not isinstance(flaw, dict):
        return False
    return bool(_flaw_valid_negative_evidence_ids(flaw, state))


def _flaw_only_cites_supports(flaw: Dict[str, Any], state: Dict[str, Any]) -> bool:
    cited = _flaw_cited_evidence_records(flaw, state)
    if not cited:
        return False
    for record in cited:
        stance = str(record.get("stance") or "").strip().lower()
        if stance not in {"supports", "partially_supports", "partial_support", "partial-support"}:
            return False
    return True


def _render_weaknesses(state: Dict[str, Any]) -> List[str]:
    """Return the *Grounded paper weaknesses* shortlist.

    A flaw qualifies only when it is ``confirmed`` and at least one of its
    cited evidence records stands as negative grounding (stance not in
    ``{supports, partially_supports}``).  Active candidates and confirmed
    flaws that only cite positive-support evidence are surfaced separately as
    *Potential concerns requiring verification* so the report does not present
    them as paper-grounded weaknesses.
    """
    weaknesses: List[str] = []
    for flaw in state.get("flaw_candidates", []) or []:
        if not isinstance(flaw, dict):
            continue
        if flaw.get("status") in {"downgraded", "retracted"}:
            continue
        if _is_fallback_or_meta_flaw(flaw) and not _verified_actionable_negative_evidence_ids_for_flaw(flaw, state):
            continue
        if flaw.get("status") != "confirmed":
            continue
        if not flaw.get("evidence_ids"):
            continue
        if not _flaw_has_negative_grounding(flaw, state):
            continue
        title = _normalize_text(flaw.get("title"), max_length=160)
        description = _normalize_text(
            flaw.get("description") or flaw.get("flaw") or flaw.get("weakness"),
            max_length=400,
        )
        if not title and not description:
            continue
        weaknesses.append(f"{title}: {description}".strip())
    return weaknesses[:4]


def _is_system_assessment_limitation_flaw(flaw: Dict[str, Any], state: Dict[str, Any]) -> bool:
    """Return True iff a flaw is really a *system assessment limitation* rather
    than a paper defect.

    Heuristic: the flaw uses generic ``lack of / missing / insufficient X``
    language and is anchored only by ``supports`` / ``partially_supports``
    evidence (or no evidence at all).  In that case the system has not
    actually observed a paper deficiency — it has merely failed to extract
    the requested artifact.  Such flaws should be reported under
    ``Unresolved assessment limitations`` so reviewers do not read them as
    confirmed paper weaknesses.
    """
    if not isinstance(flaw, dict):
        return False
    if flaw.get("status") in {"downgraded", "retracted"}:
        return False
    if _is_fallback_or_meta_flaw(flaw):
        return False
    if _flaw_has_negative_grounding(flaw, state):
        return False
    text = " ".join(str(flaw.get(key) or "") for key in ("title", "description")).lower()
    if not _GENERIC_LACK_SUPPORT_PATTERN.search(text):
        return False
    cited = _flaw_cited_evidence_records(flaw, state)
    if cited and not _flaw_only_cites_supports(flaw, state):
        return False
    return True


def _render_assessment_limitation_flaws(state: Dict[str, Any]) -> List[str]:
    """Return reviewer-visible assessment-limitation lines derived from flaws
    that the system tagged as paper defects but really reflect missing
    extraction (positive support only + ``lack of X`` language).
    """
    items: List[str] = []
    seen: set[str] = set()
    for flaw in state.get("flaw_candidates", []) or []:
        if not _is_system_assessment_limitation_flaw(flaw, state):
            continue
        title = _normalize_text(flaw.get("title"), max_length=160)
        description = _normalize_text(flaw.get("description"), max_length=320)
        if not title and not description:
            continue
        anchor = title or description[:120]
        line = f"Current extraction did not surface evidence to confirm or refute: {anchor}"
        key = line.lower()
        if key in seen:
            continue
        seen.add(key)
        items.append(line)
        if len(items) >= 4:
            break
    return items


def _claim_text_for_flaw(flaw: Dict[str, Any], state: Dict[str, Any]) -> str:
    related_ids = [str(item).strip() for item in (flaw or {}).get("related_claim_ids") or [] if str(item).strip()]
    if not related_ids:
        return ""
    for claim in state.get("claims", []) or []:
        if not isinstance(claim, dict):
            continue
        claim_id = str(claim.get("claim_id") or "").strip()
        if claim_id in related_ids:
            return _normalize_text(claim.get("claim") or claim.get("text"), max_length=180)
    return ""


def _readable_negative_evidence_type(negative_type: str) -> str:
    value = str(negative_type or "").strip()
    if not value:
        return "negative evidence"
    return value.replace("_", " ")


def _negative_evidence_weakened_dimension(negative_type: str, text: str) -> str:
    value = str(negative_type or "").strip()
    if value in {"missing_ablation", "missing_baseline", "insufficient_evaluation", "negative_result"}:
        return "the empirical support for the claim"
    if value == "direct_contradiction":
        return "the claim's stated conclusion"
    if value == "reproducibility_gap":
        return "the reproducibility or implementation support"
    if value == "scope_limitation":
        return "the scope of the claim"
    lowered = str(text or "").lower()
    if any(token in lowered for token in ("table", "figure", "baseline", "ablation", "benchmark", "evaluation", "result")):
        return "the empirical support for the claim"
    if any(token in lowered for token in ("method", "algorithm", "architecture", "framework")):
        return "the method claim"
    return "the strength or scope of the claim"


def _render_verified_negative_concern_line(
    flaw: Dict[str, Any],
    state: Dict[str, Any],
    *,
    flaw_status: str,
    fallback_title: str,
    fallback_description: str,
) -> str:
    by_id = _evidence_records_by_id(state)
    negative_ids = _verified_actionable_negative_evidence_ids_for_flaw(flaw, state)
    if not negative_ids:
        return ""
    record = next((by_id.get(eid) for eid in negative_ids if isinstance(by_id.get(eid), dict)), None)
    if not isinstance(record, dict):
        return ""
    claim_text = _claim_text_for_flaw(flaw, state)
    if not claim_text:
        claim_id = str(record.get("claim_id") or "").strip()
        for claim in state.get("claims", []) or []:
            if isinstance(claim, dict) and str(claim.get("claim_id") or "").strip() == claim_id:
                claim_text = _normalize_text(claim.get("claim") or claim.get("text"), max_length=180)
                break
    quote = _normalize_text(record.get("raw_quote") or record.get("evidence"), max_length=240)
    locator = _normalize_text(record.get("source_locator") or record.get("source"), max_length=100)
    negative_type = _negative_evidence_type_for_record(record)
    readable_type = _readable_negative_evidence_type(negative_type)
    dimension = _negative_evidence_weakened_dimension(
        negative_type,
        " ".join([quote, fallback_title, fallback_description]),
    )
    parts = [f"[{flaw_status}] Verified negative concern"]
    if claim_text:
        parts.append(f"targeting claim: {claim_text}")
    if quote:
        quote_prefix = f"{locator} reports" if locator else "paper quote reports"
        parts.append(f"{quote_prefix}: {quote}")
    parts.append(f"negative type: {readable_type}")
    parts.append(f"review implication: this weakens {dimension} without by itself invalidating the whole paper")
    return "; ".join(parts)


def _render_potential_concerns(state: Dict[str, Any]) -> List[str]:
    """Return active flaws that did not pass the grounded-weakness bar.

    These are surfaced under *Potential concerns requiring verification* so
    candidate concerns and confirmed-but-only-positive-grounded flaws remain
    visible to the reviewer without being framed as paper-grounded weaknesses.
    Generic ``lack of empirical support`` flaws against claims that already
    carry strong real support are filtered out as obviously inconsistent, and
    flaws classified as system assessment limitations are routed to the
    ``Unresolved assessment limitations`` layer instead.
    """
    concerns: List[str] = []
    seen: set[str] = set()
    support_counts = _real_strong_support_counts(state)
    for flaw in state.get("flaw_candidates", []) or []:
        if not isinstance(flaw, dict):
            continue
        flaw_status = flaw.get("status", "candidate")
        if flaw_status in {"downgraded", "retracted"}:
            continue
        verified_actionable_negative = bool(_verified_actionable_negative_evidence_ids_for_flaw(flaw, state))
        if _is_fallback_or_meta_flaw(flaw) and not verified_actionable_negative:
            continue
        if flaw_status == "confirmed" and _flaw_has_negative_grounding(flaw, state):
            continue
        if _generic_lack_support_flaw_conflicts_with_support(flaw, support_counts):
            continue
        if _is_system_assessment_limitation_flaw(flaw, state):
            continue
        title = _normalize_text(flaw.get("title"), max_length=160)
        description = _normalize_text(
            flaw.get("description") or flaw.get("flaw") or flaw.get("weakness"),
            max_length=400,
        )
        if not title and not description:
            continue
        line = _render_verified_negative_concern_line(
            flaw,
            state,
            flaw_status=str(flaw_status),
            fallback_title=title,
            fallback_description=description,
        ) if verified_actionable_negative else ""
        if not line:
            line = f"[{flaw_status}] {title}: {description}".strip()
        key = line.lower()
        if key in seen:
            continue
        seen.add(key)
        concerns.append(line)
        if len(concerns) >= 4:
            break
    return concerns


def _render_assessment_limitations(state: Dict[str, Any]) -> List[str]:
    limitations: List[str] = []
    for item in state.get("unresolved_questions", []) or []:
        if not isinstance(item, dict) or item.get("status") == "resolved":
            continue
        if item.get("final_diagnostic_visible") is False:
            continue
        reason = str(item.get("hygiene_status_reason") or "")
        question = _normalize_text(item.get("question"), max_length=300)
        if not question:
            continue
        is_limitation = question.lower().startswith("assessment limitation") or reason in {
            "decision_view_meta_uncertainty",
        }
        if not is_limitation:
            continue
        visible = _report_visible_text(question, max_length=260)
        if not visible:
            visible = "Some critique candidates were treated as assessment limitations rather than paper weaknesses."
        if visible not in limitations:
            limitations.append(visible)
        if len(limitations) >= 3:
            break
    return limitations



def _evidence_section_bucket(evidence: Dict[str, Any]) -> str:
    from .support_quality import evidence_section_bucket

    return evidence_section_bucket(evidence)


def _is_real_support_evidence(evidence: Dict[str, Any]) -> bool:
    claim_id = str(evidence.get("claim_id") or "")
    return (
        _has_final_support_strength(evidence)
        and evidence.get("stance") in {"supports", "partially_supports"}
        and evidence.get("binding_status") == "bound_real_claim"
        and _is_real_paper_claim_id(claim_id)
        and _is_usable_support_grounding(evidence)
        and evidence.get("source") != "fallback-extraction"
    )


_HUMAN_ANCHOR_MAX_ITEMS = 3


def _evidence_human_anchor(state: Dict[str, Any], evidence_ids: Sequence[str]) -> str:
    """Return a paper-side anchor text for the given evidence ids.

    The anchor prefers ``source_locator`` (e.g. "Section 4.2", "Table 4")
    and falls back to ``source`` so the human-readable report cites concrete
    paper artefacts rather than internal ``evidence-X-turn-Y`` ids. Internal
    ids are kept for the dedicated *Audit Trace* section.
    """
    if not evidence_ids:
        return ""
    by_id: Dict[str, Dict[str, Any]] = {}
    for ev in state.get("evidence_map", []) or []:
        if isinstance(ev, dict):
            eid = str(ev.get("evidence_id") or "")
            if eid:
                by_id[eid] = ev
    anchors: List[str] = []
    seen: set[str] = set()
    for raw in evidence_ids:
        eid = str(raw or "")
        if not eid:
            continue
        record = by_id.get(eid)
        source = ""
        if record:
            source = _normalize_text(record.get("source_locator") or record.get("source"), max_length=160)
        if not source:
            section = _evidence_section_bucket(record or {})
            section_label = section.replace("_", " ") if section and section != "unknown" else "paper"
            source = f"the paper's {section_label} section"
        if source not in seen:
            seen.add(source)
            anchors.append(source)
        if len(anchors) >= _HUMAN_ANCHOR_MAX_ITEMS:
            break
    if not anchors:
        return ""
    return " (Evidence: " + "; ".join(anchors) + ")"


def _fmt_audit_number(value: Any) -> str:
    """Format a number for the audit-trace hygiene line.

    Integers are rendered as-is, floats are rounded to 3 decimals (and trailing
    zeros stripped) so ratios like ``actionable_limitation_ratio=0.016`` render
    cleanly without explosion of digits.
    """
    if isinstance(value, bool):
        return str(int(value))
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        if value != value or value in (float("inf"), float("-inf")):  # NaN/inf guard
            return "0"
        rounded = round(value, 3)
        if rounded.is_integer():
            return str(int(rounded))
        return f"{rounded:.3f}".rstrip("0").rstrip(".")
    return str(value)


def _criterion_audit_signature(claim_ids: Sequence[str], evidence_ids: Sequence[str]) -> str:
    """Return an audit-trace signature for a criterion line.

    Used only by the *Audit Trace* section so internal ids never bleed into
    the human-readable criterion bullets.
    """
    claims = [str(item) for item in claim_ids if item][:3]
    evidence = [str(item) for item in evidence_ids if item][:3]
    parts = []
    if claims:
        parts.append("claims=[" + ", ".join(claims) + "]")
    if evidence:
        parts.append("evidence=[" + ", ".join(evidence) + "]")
    if not parts:
        return ""
    return "; ".join(parts)


# Backward-compatibility shim: a few external scripts and tests still import
# ``_criterion_citation`` directly.  Newer renderers should call the explicit
# human / audit helpers above; this shim keeps legacy callers working but is
# no longer used inside the human-readable report.
def _criterion_citation(claim_ids: Sequence[str], evidence_ids: Sequence[str]) -> str:
    sig = _criterion_audit_signature(claim_ids, evidence_ids)
    return f" [{sig}]" if sig else ""


def _active_flaws_for_criterion(state: Dict[str, Any], pattern: str) -> List[Dict[str, Any]]:
    rx = re.compile(pattern, re.I)
    flaws = []
    for flaw in state.get("flaw_candidates", []) or []:
        if not isinstance(flaw, dict):
            continue
        if flaw.get("status") in {"downgraded", "retracted"}:
            continue
        if _is_fallback_or_meta_flaw(flaw):
            continue
        text = f"{flaw.get('title', '')} {flaw.get('description', '')}"
        if rx.search(text):
            flaws.append(flaw)
    return flaws


def _format_criterion_line(
    state: Dict[str, Any],
    name: str,
    status: str,
    rationale: str,
    evidence_ids: Sequence[str] = (),
) -> str:
    """Build a human-readable criterion bullet.

    Internal ids are deliberately omitted so reviewers see only paper-side
    anchors (e.g. "Figure 2, Table 4").  Audit trace ids are emitted by a
    dedicated section instead.
    """
    anchor = _evidence_human_anchor(state, evidence_ids)
    return f"- {name}: {status} - {rationale}{anchor}"


def _render_criterion_assessments(state: Dict[str, Any]) -> Tuple[str, List[Dict[str, Any]]]:
    """Render audit-style review dimensions without changing final decisions.

    Returns a ``(text, audit_anchors)`` tuple.  ``text`` is the human-readable
    bullet list shown in the main report; ``audit_anchors`` is a list of
    ``{name, claim_ids, evidence_ids, flaw_ids}`` dicts consumed by the
    *Audit Trace* section.
    """
    claims = [claim for claim in state.get("claims", []) or [] if isinstance(claim, dict)]
    evidence_items = [ev for ev in state.get("evidence_map", []) or [] if isinstance(ev, dict)]
    support_items = [ev for ev in evidence_items if _is_real_support_evidence(ev)]
    sections = {str(ev.get("evidence_id") or ""): _evidence_section_bucket(ev) for ev in support_items}

    def support_by_sections(*wanted: str) -> List[Dict[str, Any]]:
        wanted_set = set(wanted)
        return [ev for ev in support_items if sections.get(str(ev.get("evidence_id") or "")) in wanted_set]

    method_support = support_by_sections("method")
    result_support = support_by_sections("result", "table_or_figure", "ablation")
    abstract_support = support_by_sections("abstract")
    high_claims = [claim for claim in claims if claim.get("importance") == "high"] or claims[:2]

    novelty_flaws = _active_flaws_for_criterion(state, r"novel|original|incremental|prior work|related work")
    significance_flaws = _active_flaws_for_criterion(state, r"significance|impact|contribution|importance|useful|meaningful")
    soundness_flaws = _active_flaws_for_criterion(state, r"sound|method|assumption|valid|technical|algorithm|objective|theory")
    empirical_flaws = _active_flaws_for_criterion(state, r"experiment|evaluation|baseline|ablation|dataset|metric|table|figure|empirical|result")
    clarity_flaws = _active_flaws_for_criterion(state, r"clarity|clear|reproduc|implementation|detail|code|hyperparameter|presentation")

    def flaw_evidence_ids(flaws: Sequence[Dict[str, Any]]) -> List[str]:
        ids: List[str] = []
        for flaw in flaws:
            for evidence_id in flaw.get("evidence_ids", []) or []:
                if evidence_id and evidence_id not in ids:
                    ids.append(str(evidence_id))
        return ids

    def flaw_ids(flaws: Sequence[Dict[str, Any]]) -> List[str]:
        return [str(flaw.get("flaw_id") or "") for flaw in flaws if flaw.get("flaw_id")]

    lines: List[str] = []
    audit_anchors: List[Dict[str, Any]] = []

    def emit(name: str, status: str, rationale: str, claim_ids: Sequence[str], evidence_ids: Sequence[str], related_flaws: Sequence[Dict[str, Any]] = ()) -> None:
        lines.append(_format_criterion_line(state, name, status, rationale, evidence_ids))
        audit_anchors.append({
            "name": name,
            "status": status,
            "claim_ids": [cid for cid in claim_ids if cid],
            "evidence_ids": [eid for eid in evidence_ids if eid],
            "flaw_ids": flaw_ids(related_flaws),
        })

    novelty_claims = [str(claim.get("claim_id")) for claim in high_claims if claim.get("claim_id")]
    novelty_evidence = [str(ev.get("evidence_id")) for ev in (method_support or abstract_support) if ev.get("evidence_id")]
    if novelty_flaws:
        status = "mixed" if novelty_evidence else "not_assessable"
        rationale = "Novelty concerns are present, but ungrounded concerns are treated as assessment limits unless tied to paper evidence."
        emit("Novelty / Originality", status, rationale, novelty_claims, novelty_evidence or flaw_evidence_ids(novelty_flaws), novelty_flaws)
    elif novelty_evidence:
        emit("Novelty / Originality", "positive", "The main contribution is identifiable from grounded claims/evidence, but this is not a global novelty proof.", novelty_claims, novelty_evidence)
    else:
        emit("Novelty / Originality", "not_assessable", "No grounded novelty-specific evidence was available in the structured state.", novelty_claims, ())

    significance_claims = [str(claim.get("claim_id")) for claim in high_claims if claim.get("claim_id")]
    significance_evidence = [str(ev.get("evidence_id")) for ev in support_items[:3] if ev.get("evidence_id")]
    if significance_flaws and not significance_evidence:
        emit("Significance / Contribution", "not_assessable", "Contribution concerns exist but lack grounded evidence links.", significance_claims, flaw_evidence_ids(significance_flaws), significance_flaws)
    elif significance_evidence:
        status = "mixed" if significance_flaws else "positive"
        emit("Significance / Contribution", status, "The contribution signal is based on verified real-claim support rather than unverified artifacts.", significance_claims, significance_evidence, significance_flaws)
    else:
        emit("Significance / Contribution", "not_assessable", "The state lacks enough bound support to judge contribution strength.", significance_claims, ())

    method_evidence = [str(ev.get("evidence_id")) for ev in method_support[:3] if ev.get("evidence_id")]
    method_claims = [str(ev.get("claim_id")) for ev in method_support[:3] if ev.get("claim_id")]
    if soundness_flaws:
        status = "negative" if flaw_evidence_ids(soundness_flaws) else "mixed"
        rationale = "Technical concerns remain active; ungrounded concerns should be read as provisional."
        emit("Technical Soundness", status, rationale, method_claims, method_evidence or flaw_evidence_ids(soundness_flaws), soundness_flaws)
    elif method_evidence:
        emit("Technical Soundness", "positive", "Method-level evidence supports the reviewed technical claims.", method_claims, method_evidence)
    else:
        emit("Technical Soundness", "not_assessable", "No method-grounded evidence was available for a confident soundness judgment.", method_claims, ())

    empirical_evidence = [str(ev.get("evidence_id")) for ev in result_support[:3] if ev.get("evidence_id")]
    empirical_claims = [str(ev.get("claim_id")) for ev in result_support[:3] if ev.get("claim_id")]
    if empirical_flaws:
        status = "negative" if flaw_evidence_ids(empirical_flaws) else "mixed"
        rationale = "Empirical concerns remain active; missing table/result grounding should be treated cautiously."
        emit("Empirical Adequacy", status, rationale, empirical_claims, empirical_evidence or flaw_evidence_ids(empirical_flaws), empirical_flaws)
    elif empirical_evidence:
        emit("Empirical Adequacy", "positive", "Result/table/ablation evidence is present for at least part of the empirical story.", empirical_claims, empirical_evidence)
    else:
        emit("Empirical Adequacy", "not_assessable", "No result-, table-, or ablation-grounded support was available in the final state.", empirical_claims, ())

    clarity_evidence = method_evidence[:2] or empirical_evidence[:2]
    if clarity_flaws:
        status = "negative" if flaw_evidence_ids(clarity_flaws) else "mixed"
        emit("Clarity / Reproducibility", status, "Clarity or reproducibility concerns were identified; ungrounded concerns remain provisional.", (), clarity_evidence or flaw_evidence_ids(clarity_flaws), clarity_flaws)
    elif clarity_evidence:
        emit("Clarity / Reproducibility", "mixed", "Some method or result details are grounded, but reproducibility-specific evidence is not fully established.", (), clarity_evidence)
    else:
        emit("Clarity / Reproducibility", "not_assessable", "The state does not contain enough grounded implementation or reproducibility detail.", (), ())

    return "\n".join(lines), audit_anchors


_LIMITATION_LABELS = {
    "actionable_limitation": "Actionable limitations (authors can address)",
    "context_limitation": "Assessment limitations (context unavailable or not grounded)",
    "unresolved_diagnostic": "Unresolved diagnostic questions (require manual confirmation)",
    "stale_limitation": "Stale items (already resolved by current support)",
}


def _classified_limitation_questions(state: Dict[str, Any]) -> Dict[str, List[str]]:
    """Group reviewer-visible limitation questions by their classification.

    The classification is computed in :func:`build_decision_hygiene_view`; here
    we just bucket the surfaced text so the renderer can emit a four-class
    breakdown instead of a single flat list.
    """
    grouped: Dict[str, List[str]] = {key: [] for key in _LIMITATION_LABELS}
    seen: set[str] = set()
    for question in state.get("unresolved_questions", []) or []:
        if not isinstance(question, dict):
            continue
        if question.get("final_diagnostic_visible") is False:
            continue
        text = _normalize_text(question.get("question"), max_length=260)
        if not text:
            continue
        visible = _report_visible_text(text, max_length=260)
        if not visible:
            continue
        key = visible.lower()
        if key in seen:
            continue
        seen.add(key)
        bucket = str(question.get("limitation_classification") or "")
        if bucket not in grouped:
            grouped["context_limitation"].append(visible)
        else:
            grouped[bucket].append(visible)
    return grouped


def _render_limitations_section(decision_state: Dict[str, Any]) -> str:
    """Render the *Unresolved assessment limitations* section, classified."""
    grouped = _classified_limitation_questions(decision_state)
    flaw_lines = _render_assessment_limitation_flaws(decision_state)
    lines: List[str] = []
    if flaw_lines:
        lines.append("  - System assessment limitations (flaws routed away from grounded weaknesses):")
        for item in flaw_lines[:3]:
            lines.append(f"    - {item}")
    for key, label in _LIMITATION_LABELS.items():
        items = grouped.get(key, [])
        if not items:
            continue
        lines.append(f"  - {label}:")
        for item in items[:3]:
            lines.append(f"    - {item}")
    return "\n".join(lines)


def _render_support_coverage_summary(decision_hygiene: Dict[str, Any]) -> str:
    """Return one human-readable bullet line summarising support coverage."""
    if not isinstance(decision_hygiene, dict):
        return ""
    total = int(decision_hygiene.get("real_strong_support_total") or 0)
    moderate_total = int(decision_hygiene.get("final_verified_moderate_support_total") or 0)
    diagnostic_total = total + moderate_total
    depth_counts = decision_hygiene.get("claim_support_depth_counts") or {}
    depth_total = sum(int(depth_counts.get(label, 0) or 0) for label in ("deep", "moderate", "shallow", "none")) if isinstance(depth_counts, dict) else 0
    depth_text = ""
    if isinstance(depth_counts, dict) and depth_total > 0:
        depth_text = (
            f" Claim-level support depth: {int(depth_counts.get('deep', 0) or 0)} deep, "
            f"{int(depth_counts.get('moderate', 0) or 0)} moderate, "
            f"{int(depth_counts.get('shallow', 0) or 0)} shallow, "
            f"{int(depth_counts.get('none', 0) or 0)} without real strong support."
        )
    if total <= 0:
        if moderate_total > 0:
            return (
                f"Support coverage: no final real strong support survived, but {moderate_total} verified moderate diagnostic support item(s) remain visible for human review."
                + (f" {depth_text.strip()}" if depth_text.strip() else "")
            ).strip()
        return depth_text.strip()
    claims_with = int(decision_hygiene.get("claims_with_real_strong_support") or 0)
    claims_2plus_indep = int(decision_hygiene.get("claims_with_2plus_independent_support") or 0)
    claims_with_empirical = int(decision_hygiene.get("claims_with_empirical_real_strong_support") or 0)
    empirical_total = int(decision_hygiene.get("empirical_real_strong_support_count") or 0)
    method_total = int(decision_hygiene.get("method_real_strong_support_count") or 0)
    abstract_total = int(decision_hygiene.get("abstract_real_strong_support_count") or 0)
    concentration = float(decision_hygiene.get("support_concentration_index") or 0.0)
    return (
        f"Support coverage: {total} real strong support items plus {moderate_total} verified moderate diagnostic items "
        f"({diagnostic_total} total reviewer-visible support signals) across {claims_with} strong-supported claim(s); "
        f"{claims_2plus_indep} claim(s) carry two or more independent supports; "
        f"{claims_with_empirical} claim(s) include empirical (result/table/ablation) grounding "
        f"({empirical_total} empirical, {method_total} method, {abstract_total} abstract). "
        f"Top-claim concentration={concentration:.2f}.{depth_text}"
    )


def _render_audit_trace_section(
    decision_hygiene: Dict[str, Any],
    criteria_audit: Sequence[Dict[str, Any]],
    recommendation: Dict[str, Any],
) -> str:
    """Render the dedicated *Audit Trace* section with internal ids.

    This block is intentionally separated from the human-readable report so
    paper-facing prose never carries internal claim/evidence ids while
    auditors can still recover full lineage.
    """
    lines: List[str] = []

    view_label = str(recommendation.get("recommendation_view") or "")
    binary = str(recommendation.get("binary_decision") or "")
    reason = str(recommendation.get("reason") or "")
    if view_label or binary:
        lines.append(
            f"- recommendation_view={view_label}; binary_decision={binary}; reason={reason}"
        )
    warnings = recommendation.get("accept_calibration_warnings") or []
    if warnings:
        lines.append("- accept_calibration_warnings=" + ",".join(str(item) for item in warnings))

    hygiene = decision_hygiene or {}
    hygiene_keys = (
        "real_strong_support_total",
        "non_abstract_real_strong_support_count",
        "empirical_real_strong_support_count",
        "method_real_strong_support_count",
        "abstract_real_strong_support_count",
        "claims_with_real_strong_support",
        "claims_with_2plus_independent_support",
        "claims_with_empirical_real_strong_support",
        "claims_with_deep_support",
        "claims_with_moderate_or_deep_support",
        "claims_with_only_shallow_support",
        "claims_without_real_strong_support",
        "primary_claim_total",
        "primary_claims_with_real_strong_support",
        "primary_claims_with_empirical_support",
        "primary_claims_with_deep_support",
        "primary_claims_with_moderate_or_deep_support",
        "primary_claim_support_coverage",
        "primary_claim_empirical_coverage",
        "support_concentration_index",
        "support_only_flaw_filtered_count",
        "candidate_to_potential_concern_downgrade_count",
        "grounded_weakness_count",
        "verified_potential_concern_count",
        "potential_concern_count",
        "assessment_limitation_flaw_count",
        "verified_negative_flaw_count",
        "negative_evidence_candidate_count",
        "negative_evidence_linked_to_flaw_count",
        "negative_evidence_unlinked_to_flaw_count",
        "negative_evidence_binding_retry_candidate_count",
        "negative_grounding_conflict_count",
        "invalid_negative_evidence_id_count",
        "stance_inferred_negative_grounding_count",
        "actionable_limitation_count",
        "context_limitation_count",
        "unresolved_diagnostic_count",
        "stale_limitation_count",
        "total_limitation_count",
        "actionable_limitation_ratio",
        "diagnostic_useful_limitation_ratio",
        "stale_evidence_gap_count",
    )
    summary_kv = ", ".join(
        f"{key}={_fmt_audit_number(hygiene.get(key))}"
        for key in hygiene_keys
        if hygiene.get(key) is not None
    )
    if summary_kv:
        lines.append(f"- hygiene: {summary_kv}")

    for entry in criteria_audit or []:
        sig = _criterion_audit_signature(entry.get("claim_ids", []), entry.get("evidence_ids", []))
        flaw_ids = [fid for fid in entry.get("flaw_ids", []) if fid]
        sig_parts = []
        if sig:
            sig_parts.append(sig)
        if flaw_ids:
            sig_parts.append("flaws=[" + ", ".join(flaw_ids[:3]) + "]")
        suffix = " (" + "; ".join(sig_parts) + ")" if sig_parts else ""
        lines.append(f"- {entry.get('name','')}: status={entry.get('status','')}{suffix}")

    if not lines:
        return "- (no audit anchors emitted)"
    return "\n".join(lines)


def _build_review_diagnostic_parts(
    state: Dict[str, Any],
    manager_payload: Dict[str, Any],
) -> Dict[str, Any]:
    """Compute the shared building blocks for the review diagnostic outputs.

    Returns a dict with the rendered text fragments for sections 1-6 of the
    user-facing report, the rendered Audit Trace text (section 7), and the
    structured pieces (``recommendation`` / ``decision_hygiene`` /
    ``criteria_audit``) that feed both the human report and the
    machine-readable ``state_audit`` artifact.

    The split exists so that ``render_user_report`` (paper-facing) can stay
    free of recommendation/decision tokens while ``build_state_audit``
    can preserve the full machine-readable trace.
    """

    model_report = _normalize_text(manager_payload.get("final_report"), max_length=4000)
    decision_state = build_decision_hygiene_view(state or {})
    # Use the live state for the canonical recommendation view so the renderer
    # and the runtime evaluator always agree on the label.  ``build_decision_hygiene_view``
    # is now idempotent, so this stays consistent regardless of which input is
    # passed in by callers.
    recommendation = infer_final_recommendation_view(state or {}, manager_payload or {})
    recommendation_view = str(recommendation.get("recommendation_view") or "reject_like")
    recommendation_reason = str(recommendation.get("reason") or "unspecified")
    # P2.9: Reviewer-facing labels are *signal* phrases — they describe what the
    # system observed in the ReviewState, NOT a recommendation to accept/reject.
    # The internal enum (accept_like / borderline_positive / borderline_insufficient
    # / not_assessable_uncertain / reject_like) is preserved verbatim in the
    # machine-readable Audit Trace section and in ``infer_final_recommendation_view``
    # (red line: thresholds and enum keys do not change).
    recommendation_labels = {
        "accept_like": "Support-rich positive signal",
        "borderline_positive": "Support-rich but coverage insufficient",
        "borderline_insufficient": "Evidence-limited (human review needed)",
        "not_assessable_uncertain": "Context-limited assessment",
        "reject_like": "Grounded concern signal",
    }
    recommendation_reason_labels = {
        "grounded_major_or_critical_flaw": "grounded major or critical concerns remain active",
        "high_confidence_real_empirical_support_without_grounded_blocker": "strong empirical support is present and no grounded blocker remains active",
        "real_nonabstract_empirical_support_without_grounded_blocker": "non-abstract empirical support is present and no grounded blocker remains active",
        "positive_support_present_but_uncertainty_or_unverified_negative_remains": "positive support is present, but uncertainty or unverified concerns remain",
        "some_real_support_but_not_enough_quality_or_coverage_for_accept_like": "some real support is present, but coverage is not strong enough for a support-rich positive signal",
        "insufficient_grounded_support_with_open_uncertainty": "grounded support is insufficient and important uncertainties remain",
        "no_usable_accept_support": "the current record lacks enough usable support to be reviewer-actionable",
    }
    recommendation_label = recommendation_labels.get(recommendation_view, recommendation_view.replace("_", " "))
    recommendation_reason_text = recommendation_reason_labels.get(recommendation_reason, recommendation_reason.replace("_", " "))

    decision_hygiene = decision_state.get("decision_hygiene", {}) if isinstance(decision_state, dict) else {}
    claims = decision_state.get("claims", [])
    strengths = _render_strengths(decision_state)
    weaknesses = _render_weaknesses(decision_state)
    unresolved = _open_unresolved_questions(decision_state)
    dialogue_summary = _report_visible_text(
        decision_state.get("dialogue_summary"),
        default="The dialogue tracked the paper's main claims, supporting evidence, and open risks.",
        max_length=800,
    )

    summary_bits = [claim["claim"] for claim in claims[:3]]
    summary_text = " ".join(summary_bits) if summary_bits else "The paper presents a set of claims that were reviewed through iterative claim, evidence, and flaw analysis."
    if model_report:
        import re as _re
        _stripped = _re.sub(r"^final\s*decision\s*[:：]\s*\S+\s*", "", model_report, flags=_re.IGNORECASE).strip()
        _visible_summary = _report_visible_text(_stripped, max_length=800)
        if _visible_summary:
            summary_text = _visible_summary
    strengths = _filter_report_visible_items(strengths)
    weaknesses = _filter_report_visible_items(weaknesses)
    potential_concerns = _filter_report_visible_items(_render_potential_concerns(decision_state), max_items=3)

    coverage_line = _render_support_coverage_summary(decision_hygiene)
    strength_items = list(strengths)
    if coverage_line:
        strength_items.insert(0, coverage_line)
    if not strength_items:
        strength_items = ["The paper raises potentially useful ideas, but the supporting record is mixed."]
    strengths_text = "\n".join(f"- {item}" for item in strength_items)

    weakness_lines: List[str] = []
    if weaknesses:
        weakness_lines.append("- Grounded paper weaknesses:")
        weakness_lines.extend(f"  - {item}" for item in weaknesses)
    else:
        weakness_lines.append("- Grounded paper weaknesses: none passed the paper-evidence grounding filter.")
    if potential_concerns:
        weakness_lines.append("- Potential concerns requiring verification:")
        weakness_lines.extend(f"  - {item}" for item in potential_concerns)
    limitations_block = _render_limitations_section(decision_state)
    if limitations_block.strip():
        weakness_lines.append("- Unresolved assessment limitations:")
        weakness_lines.append(limitations_block)
    weaknesses_text = "\n".join(weakness_lines)

    suggestion_items = _filter_report_visible_items(unresolved[:8]) or [
        "Clarify the strongest empirical support for each main claim.",
        "Address the highest-severity flaw before rebuttal or revision.",
    ]
    suggestions_text = "\n".join(f"- {item}" for item in suggestion_items)

    criteria_text_raw, criteria_audit = _render_criterion_assessments(decision_state)
    criteria_lines = _filter_report_visible_items(criteria_text_raw.splitlines(), max_items=8)
    criteria_lines.append("- Criterion assessments are diagnostic notes for human review; machine-readable lineage is stored separately.")
    criteria_text = "\n".join(criteria_lines)
    reason = (
        f"The diagnostic signal is {recommendation_label.lower()} because {recommendation_reason_text}. "
        "Evidence gaps and unresolved concerns should be treated as human-review questions."
    )

    audit_trace_text = _render_audit_trace_section(decision_hygiene, criteria_audit, recommendation)

    return {
        "decision_state": decision_state,
        "recommendation": recommendation,
        "recommendation_view": recommendation_view,
        "recommendation_label": recommendation_label,
        "recommendation_reason": recommendation_reason,
        "recommendation_reason_text": recommendation_reason_text,
        "decision_hygiene": decision_hygiene,
        "criteria_audit": criteria_audit,
        "dialogue_summary": dialogue_summary,
        "summary_text": summary_text,
        "strengths_text": strengths_text,
        "weaknesses_text": weaknesses_text,
        "criteria_text": criteria_text,
        "suggestions_text": suggestions_text,
        "diagnostic_reason_text": reason,
        "audit_trace_text": audit_trace_text,
    }


def _format_user_facing_sections(parts: Dict[str, Any]) -> str:
    """Render sections 1-6 of the Review Diagnostic Report.

    The user-facing report intentionally omits the machine-readable Audit
    Trace section so the artifact cannot be misread as an automated
    accept/reject decision.  Use ``build_state_audit`` to obtain the
    machine-readable trace (recommendation view, binary decision, hygiene
    counters, criterion lineage) for analysis tooling.
    """
    return (
        f"Review Diagnostic Report\n\n"
        f"1. Summary of Reviews\n"
        f"{parts['dialogue_summary']} {parts['summary_text']}\n\n"
        f"2. Key Strengths\n"
        f"{parts['strengths_text']}\n\n"
        f"3. Key Weaknesses\n"
        f"{parts['weaknesses_text']}\n\n"
        f"4. Criterion Assessment\n"
        f"{parts['criteria_text']}\n\n"
        f"5. Questions/Suggestions\n"
        f"{parts['suggestions_text']}\n\n"
        f"6. Diagnostic Summary\n"
        f"Diagnostic signal: {parts['recommendation_label']}. {parts['diagnostic_reason_text']}\n"
    )


def render_user_report(state: Dict[str, Any], manager_payload: Dict[str, Any]) -> str:
    """Render the paper-facing Review Diagnostic Report (sections 1-6 only).

    This artifact deliberately excludes ``binary_decision`` /
    ``recommendation_view`` / hygiene-counter exposure so that downstream
    consumers (papers, deployment UI, qualitative reviewers) cannot mistake
    it for an automated accept/reject judgement.  The machine-readable
    counterpart is produced by :func:`build_state_audit`.
    """
    parts = _build_review_diagnostic_parts(state or {}, manager_payload or {})
    return _format_user_facing_sections(parts)


def build_state_audit(state: Dict[str, Any], manager_payload: Dict[str, Any]) -> Dict[str, Any]:
    """Build the machine-readable companion to :func:`render_user_report`.

    The returned dict captures everything that previously lived in section 7
    of the combined report (``recommendation_view``, ``binary_decision``,
    hygiene counters, per-criterion audit anchors, accept calibration
    warnings, plus a rendered text snippet for log inspection).
    """
    parts = _build_review_diagnostic_parts(state or {}, manager_payload or {})
    recommendation = parts["recommendation"]
    return {
        "recommendation_view": str(recommendation.get("recommendation_view") or ""),
        "binary_decision": str(recommendation.get("binary_decision") or ""),
        "reason": str(recommendation.get("reason") or ""),
        "accept_calibration_warnings": list(recommendation.get("accept_calibration_warnings") or []),
        "decision_hygiene": copy.deepcopy(parts["decision_hygiene"]),
        "criteria_audit": copy.deepcopy(parts["criteria_audit"]),
        "audit_trace_text": parts["audit_trace_text"],
    }


def render_final_review(state: Dict[str, Any], manager_payload: Dict[str, Any]) -> str:
    """Backward-compatible combined renderer.

    Returns the full text including section 7 (Audit Trace).  Existing
    callers (env reward computation, archived analysis scripts) continue to
    receive identical output; new callers should prefer
    :func:`render_user_report` together with :func:`build_state_audit`.
    """
    parts = _build_review_diagnostic_parts(state or {}, manager_payload or {})
    user_text = _format_user_facing_sections(parts)
    return (
        f"{user_text}\n"
        f"7. Audit Trace (machine-readable)\n"
        f"{parts['audit_trace_text']}\n"
    )


def _classify_revision_events(revision_events: List[Dict[str, Any]], worker_payloads: Optional[List[Dict[str, Any]]] = None) -> Dict[str, List[str]]:
    new_items: List[str] = []
    downgraded_items: List[str] = []
    retracted_items: List[str] = []
    revision_reasons: List[str] = []

    # Substantive demotion transitions (general downgrades)
    DOWNGRADE_TRANSITIONS = {
        # Flaw demotions
        ("confirmed", "candidate"),
        ("confirmed", "downgraded"),
        ("candidate", "downgraded"),
        # Claim demotions
        ("supported", "unsupported"),
        ("supported", "uncertain"),
        ("partially_supported", "unsupported"),
    }

    # "Commits" are a subset of recovery actions that land in the final lifecycle statuses
    COMMIT_TRANSITIONS = {
        # Flaw commits
        ("candidate", "downgraded"),
        ("confirmed", "downgraded"),
        ("candidate", "retracted"),
        ("confirmed", "retracted"),
        # Claim commits.  ``partially_supported -> unsupported`` is a
        # substantive lifecycle demotion (the V17 hardneg8 audit surfaced a
        # turn that mutated state via this transition but was previously
        # mis-labelled ``commit_applied=False`` because only the
        # ``supported``/``uncertain`` source statuses were enumerated here).
        ("supported", "unsupported"),
        ("supported", "superseded"),
        ("uncertain", "unsupported"),
        ("partially_supported", "unsupported"),
        ("partially_supported", "superseded"),
        # State-hygiene commits. Recovery patches can validly repair stale
        # unresolved/gap burden without changing a claim/flaw status. These
        # transitions should count as effective repairs when they occur in a
        # committed recovery turn, otherwise recovery impact is undercounted.
        ("open", "resolved"),
        ("open", "converted"),
        ("open", "superseded"),
    }
    RETRACT_VALUES = {"retracted", "superseded"}

    commit_applied = False
    commit_details = []

    for item in revision_events or []:
        entity_type = item.get('entity_type', 'unknown')
        entity_id = item.get('entity_id', '')
        entity = f"{entity_type}:{entity_id}"
        old_value = str(item.get('old_value', item.get('before', '')) or '').strip().lower()
        new_value = str(item.get('new_value', item.get('after', '')) or '').strip().lower()
        field = str(item.get('field', '') or '').strip().lower()
        reason = str(item.get('reason', '') or '').strip()

        if old_value in {'', 'none'} and new_value not in {'', 'none'}:
            if entity not in new_items:
                new_items.append(entity)

        # Check for downgrades
        is_downgrade = False
        if field == 'status' and (old_value, new_value) in DOWNGRADE_TRANSITIONS:
            is_downgrade = True
        elif new_value == 'downgraded':
            is_downgrade = True

        if is_downgrade and entity not in downgraded_items:
            downgraded_items.append(entity)

        # Check for "Commits"
        if field == 'status' and (old_value, new_value) in COMMIT_TRANSITIONS:
            commit_applied = True
            commit_details.append({
                "target_id": entity,
                "old_status": old_value,
                "new_status": new_value,
                "reason": reason or "lifecycle_commit",
                "success": True
            })

        # Check for retractions
        if new_value in RETRACT_VALUES and entity not in retracted_items:
            retracted_items.append(entity)
            if field == 'status':
                commit_applied = True
                commit_details.append({
                    "target_id": entity,
                    "old_status": old_value,
                    "new_status": new_value,
                    "reason": reason or "lifecycle_retraction",
                    "success": True
                })

        if reason and reason not in revision_reasons:
            revision_reasons.append(reason)


    for worker in worker_payloads or []:
        payload = (worker or {}).get('payload', {}) or {}
        for claim in payload.get('claims', []) or []:
            entity = f"claim:{claim.get('claim_id', '')}"
            if claim.get('claim_id') and entity not in new_items:
                new_items.append(entity)
            status = str(claim.get('status', '') or '').strip().lower()
            if status in {'unsupported', 'superseded'} and entity not in downgraded_items:
                downgraded_items.append(entity)
        for evidence in payload.get('evidence_map', []) or []:
            entity = f"evidence:{evidence.get('evidence_id', '')}"
            if evidence.get('evidence_id') and entity not in new_items:
                new_items.append(entity)
        for flaw in payload.get('flaw_candidates', []) or []:
            entity = f"flaw:{flaw.get('flaw_id', '')}"
            if flaw.get('flaw_id') and entity not in new_items:
                new_items.append(entity)
            status = str(flaw.get('status', '') or '').strip().lower()
            if status == 'downgraded' and entity not in downgraded_items:
                downgraded_items.append(entity)
            if status in RETRACT_VALUES and entity not in retracted_items:
                retracted_items.append(entity)

    return {
        "new_items": sorted(set(new_items))[:8],
        "downgraded_items": sorted(set(downgraded_items))[:8],
        "retracted_items": sorted(set(retracted_items))[:8],
        "revision_reasons": sorted(set(revision_reasons))[:6],
        "commit_applied": commit_applied,
        "commit_details": commit_details[:6],
    }


def _summarize_conflict_events(conflict_events: List[Dict[str, Any]]) -> List[str]:
    summary: List[str] = []
    for item in conflict_events or []:
        note = str(item.get('note', '') or '').strip()
        if note and note not in summary:
            summary.append(note[:220])
    return summary[:6]


def _build_payload_support_survival_trace(
    turn_id: int,
    manager_payload: Dict[str, Any],
    worker_payloads: List[Dict[str, Any]],
    state: Dict[str, Any],
) -> List[Dict[str, Any]]:
    real_claim_ids = _decision_real_claim_ids(state)
    claims_by_id = _claim_lookup_by_id(state)
    state_evidence_by_id = {
        str(item.get("evidence_id") or ""): item
        for item in state.get("evidence_map", []) or []
        if isinstance(item, dict) and str(item.get("evidence_id") or "")
    }
    open_gap_claim_ids = {
        str(gap.get("claim_id") or "")
        for gap in _open_evidence_gaps(state)
        if str(gap.get("claim_id") or "")
    }
    # Mainline-Final-Integrated P1-2: contested-support arbitration set is
    # carried per turn so the trace can mark the positive support as
    # ``contested_support`` without dropping it from the final view.
    contested_claim_ids = _contested_support_claim_ids(state)
    raw_target_ids = list(manager_payload.get("raw_target_claim_ids") or manager_payload.get("target_claim_ids") or [])
    target_count = int(manager_payload.get("raw_target_count", len(raw_target_ids)) or 0)
    target_too_broad = bool(
        manager_payload.get("raw_target_is_broad", False)
        or manager_payload.get("broad_target_gate_blocked", False)
        or target_count > 2
    )
    trace: List[Dict[str, Any]] = []
    for worker in worker_payloads or []:
        if not isinstance(worker, dict):
            continue
        payload = worker.get("payload", {}) or {}
        if not isinstance(payload, dict):
            continue
        worker_id = str(worker.get("agent_id") or worker.get("worker_id") or "")
        for evidence in payload.get("evidence_map", []) or []:
            if not isinstance(evidence, dict):
                continue
            stance = str(evidence.get("stance") or evidence.get("initial_stance") or "").strip()
            if stance not in {"supports", "partially_supports"}:
                continue
            evidence_id = str(evidence.get("evidence_id") or "")
            claim_id = str(evidence.get("claim_id") or "")
            claim = claims_by_id.get(claim_id, {})
            claim_kind = _classify_claim_kind(claim_id, claim.get("claim_kind") if isinstance(claim, dict) else "")
            merged = bool(evidence_id and evidence_id in state_evidence_by_id)
            final_item = state_evidence_by_id.get(evidence_id, evidence)
            included = bool(merged and _is_real_bound_support(final_item, real_claim_ids))
            final_depth = _support_depth_label(final_item)
            trace.append(
                {
                    "support_id": str(evidence.get("support_id") or evidence_id),
                    "evidence_id": evidence_id,
                    "paper_id": str(state.get("paper_id") or ""),
                    "turn_id": turn_id,
                    "worker_id": worker_id,
                    "claim_id": claim_id,
                    "claim_kind": claim_kind,
                    "quote_id": str(final_item.get("quote_id") or evidence.get("quote_id") or ""),
                    "raw_quote": str(final_item.get("raw_quote") or evidence.get("raw_quote") or ""),
                    "source_locator": str(final_item.get("source_locator") or evidence.get("source_locator") or ""),
                    "source_locator_specific": _is_specific_locator(str(final_item.get("source_locator") or evidence.get("source_locator") or "")),
                    "initial_strength": str(evidence.get("initial_strength") or evidence.get("strength") or ""),
                    "initial_stance": stance,
                    "verified_grounding_label": str(final_item.get("verified_grounding_label") or evidence.get("verified_grounding_label") or ""),
                    "semantic_alignment_score": final_item.get("semantic_alignment_score", evidence.get("semantic_alignment_score", 0.0)),
                    "semantic_grounding_label": str(final_item.get("semantic_grounding_label") or evidence.get("semantic_grounding_label") or ""),
                    "support_depth": final_depth,
                    "target_claim_count": target_count,
                    "target_claim_ids": raw_target_ids[:8],
                    "target_too_broad": target_too_broad,
                    "merged_into_state": merged,
                    "merge_drop_reason": "" if merged else ("target_too_broad" if target_too_broad else "hygiene_filtered"),
                    "final_strength": str(final_item.get("strength") or ""),
                    "final_support_depth": final_depth,
                    # Bug C fix: surface medium→strong promotion telemetry on
                    # the per-turn trace so post-run analyses can attribute
                    # `final_strength=strong` to the direct or fallback path.
                    "verified_claim_overlap_score": _verified_claim_overlap_score(final_item),
                    "strength_promotion_from_medium_used": bool(final_item.get("strength_promotion_from_medium_used")),
                    "strength_promotion_reason": str(final_item.get("strength_promotion_reason") or ""),
                    "support_quality_adjustment": str(final_item.get("support_quality_adjustment") or ""),
                    "included_in_final_view": included,
                    "final_drop_reason": _support_survival_drop_reason(
                        final_item,
                        real_claim_ids=real_claim_ids,
                        claim_kind=claim_kind,
                        included_in_final_view=included,
                        merged_into_state=merged,
                        target_too_broad=target_too_broad and not merged,
                        open_gap_claim_ids=open_gap_claim_ids,
                    ),
                    "contested_support": bool(claim_id and claim_id in contested_claim_ids),
                }
            )
    return trace[:12]


_RECOVERY_ACTIONS = set(RECOVERY_ACTION_TYPES)
_RECOVERY_PATCH_ACTIONS = set(RECOVERY_PATCH_ACTION_TYPES)
_RECOVERY_POLICIES = {"conflict_block_override", "s4_conflict_recovery_override"}


def _is_recovery_action(action_type: str, effective_action_type: str, policy_source: str) -> bool:
    return (
        action_type in _RECOVERY_ACTIONS
        or effective_action_type in _RECOVERY_ACTIONS
        or policy_source in _RECOVERY_POLICIES
    )


def _recovery_type(action_type: str, effective_action_type: str) -> str:
    for act in (action_type, effective_action_type):
        if act == "challenge_previous_hypothesis":
            return "challenge"
        if act == "request_evidence_recheck":
            return "recheck"
    return "none"


def _resolve_turn_mode(manager_payload: Dict[str, Any], action_type: str, effective_action_type: str) -> str:
    requested = _normalize_choice(manager_payload.get("turn_mode"), TURN_MODES, "")
    if requested:
        return requested
    if action_type in _RECOVERY_PATCH_ACTIONS or effective_action_type in _RECOVERY_PATCH_ACTIONS:
        return "recovery_patch"
    return "normal_evidence"


def _has_recovery_payload(worker_payloads: Sequence[Dict[str, Any]]) -> bool:
    for worker in worker_payloads or []:
        payload = (worker or {}).get("payload", {}) or {}
        if looks_like_recovery_payload(payload):
            return True
    return False


def _has_recovery_patch_emission(worker_payloads: Sequence[Dict[str, Any]], latest_patch_log: Optional[Dict[str, Any]] = None) -> bool:
    for worker in worker_payloads or []:
        payload = (worker or {}).get("payload", {}) or {}
        if str(payload.get("action") or "") == "apply_recovery_patch":
            return True
    latest_patch_log = latest_patch_log or {}
    return bool(latest_patch_log.get("recovery_attempted") and latest_patch_log.get("recovery_target_id"))


def _first_worker_emission_failure(worker_payloads: Sequence[Dict[str, Any]]) -> tuple[str, str]:
    for worker in worker_payloads or []:
        payload = (worker or {}).get("payload", {}) or {}
        code = str(payload.get("_emission_failure_code") or "").strip()
        if code:
            return code, str(payload.get("_emission_failure_message") or "").strip()
    return "", ""


def _is_patch_recovery_attempt(
    action_type: str,
    effective_action_type: str,
    worker_payloads: Sequence[Dict[str, Any]],
    latest_patch_log: Optional[Dict[str, Any]] = None,
) -> bool:
    del latest_patch_log
    if _has_recovery_payload(worker_payloads):
        return True
    return action_type == "challenge_previous_hypothesis" or effective_action_type == "challenge_previous_hypothesis"


def _classify_emission_failure(
    manager_payload: Dict[str, Any],
    worker_payloads: Sequence[Dict[str, Any]],
    latest_patch_log: Dict[str, Any],
    turn_mode: str,
    recovery_emitted: bool,
    action_type: str,
    effective_action_type: str,
) -> tuple[str, str]:
    if turn_mode != "recovery_patch" or recovery_emitted:
        return "", ""

    code, message = _first_worker_emission_failure(worker_payloads)
    if code:
        return code, message

    if manager_payload.get("decision") == "finalize" or not manager_payload.get("selected_agents"):
        return (
            "TRIGGERED_BUT_ROUTED_TO_SUMMARY",
            "Recovery was triggered, but the turn did not route any worker into recovery patch generation.",
        )

    if action_type not in _RECOVERY_ACTIONS and effective_action_type not in _RECOVERY_ACTIONS:
        return (
            "ACTION_SEMANTICS_MISMATCH",
            f"Turn mode was recovery_patch, but action semantics resolved to {action_type or 'none'} / {effective_action_type or 'none'}.",
        )

    blocked_reason = str(latest_patch_log.get("recovery_failure_message") or "").strip()
    if str(latest_patch_log.get("recovery_failure_code") or "") == "BLOCKED_BY_POLICY":
        return (
            "EMISSION_NOT_REQUESTED",
            blocked_reason or "Recovery patch mode produced only blocked outputs, so no patch was emitted.",
        )

    return (
        "EMISSION_NOT_REQUESTED",
        "Recovery patch mode was entered, but no worker emitted apply_recovery_patch on this turn.",
    )


def _recovery_blocked_reason(
    recovery_attempted: bool,
    downgraded_items: List[str],
    retracted_items: List[str],
    conflict_summary: List[str],
) -> str:
    has_outcome = bool(downgraded_items or retracted_items)
    if not recovery_attempted:
        if conflict_summary:
            return "no_recovery_action_attempted"
        return ""
    if has_outcome:
        return ""
    return "recovery_attempted_no_state_change"


def _compute_recovery_layer_fields(
    turn_patch_log: Dict[str, Any],
    revision_meta: Dict[str, Any],
) -> Dict[str, Any]:
    """Stratify a recovery turn outcome into a 4-layer taxonomy.

    Historically two distinct booleans (``recovery_patch_committed`` and
    ``recovery_success`` / ``recovery_commit_applied``) were both used as
    "successful recovery" signals even though they measure different things.
    External audits flagged this ambiguity as a paper-level statistics risk,
    so this helper exposes an explicit stratified taxonomy:

    1. ``patch_validated``         — validator accepted the patch (no
       guarantee the patch was committed to the patch log).
    2. ``patch_committed``         — validator committed the patch to the
       per-turn recovery patch log (``turn_patch_log['recovery_committed']``).
    3. ``state_mutation_applied``  — committing the patch produced a real
       status-field transition in the ReviewState
       (``revision_meta['commit_applied']``).  This matches the legacy
       ``recovery_success`` / ``recovery_commit_applied`` semantics.
    4. ``hygiene_delta_improved``  — a state mutation that materially
       reduces ReviewState inconsistency according to the before/after
       recovery quality snapshot.  This deliberately does not count every
       status transition as an effective repair: a committed patch can be
       syntactically valid but still leave all tracked hygiene burdens
       unchanged.

    Returns a dict that callers can splat into the turn log so the new
    fields are emitted alongside (and not replacing) the legacy ones.  The
    paper-facing "successful recovery" counter should be
    ``recovery_effective_repair`` (alias of layer 4).
    """

    attempted = bool(turn_patch_log.get("recovery_attempted", False))
    validated = bool(turn_patch_log.get("recovery_validated", False))
    committed = bool(turn_patch_log.get("recovery_committed", False))
    commit_applied = bool(revision_meta.get("commit_applied", False))
    state_mutation_applied = bool(committed and commit_applied)

    commit_details = revision_meta.get("commit_details") or []
    has_status_transition = any(
        bool(str((entry or {}).get("new_status") or "").strip())
        for entry in commit_details
    )
    state_delta = turn_patch_log.get("recovery_state_delta") or {}
    consistency_improved = bool(state_delta.get("consistency_improved", False))
    negative_recovery_commit = bool(state_delta.get("negative_recovery_commit", False))
    hygiene_delta_improved = bool(state_mutation_applied and consistency_improved and not negative_recovery_commit)
    no_effect_commit = bool(state_mutation_applied and has_status_transition and not consistency_improved and not negative_recovery_commit)

    if hygiene_delta_improved:
        layer = "hygiene_delta_improved"
    elif state_mutation_applied:
        layer = "state_mutation_applied_no_hygiene_delta" if no_effect_commit else "state_mutation_applied"
    elif committed:
        layer = "patch_committed"
    elif validated:
        layer = "patch_validated"
    elif attempted:
        layer = "attempted"
    else:
        layer = ""

    return {
        "recovery_layer": layer,
        "recovery_layer_validated": validated,
        "recovery_layer_committed": committed,
        "recovery_layer_state_mutation_applied": state_mutation_applied,
        "recovery_layer_hygiene_delta_improved": hygiene_delta_improved,
        "recovery_effective_repair": hygiene_delta_improved,
        "recovery_no_effect_commit": no_effect_commit,
        "recovery_harmful_commit_risk": bool(state_mutation_applied and negative_recovery_commit),
    }


def _build_recovery_details(
    commit_details: List[Dict[str, Any]],
    recovery_attempted: bool,
    target_flaw_ids: List[str],
    target_claim_ids: List[str],
    downgraded_items: List[str],
    retracted_items: List[str],
) -> List[Dict[str, Any]]:
    details = copy.deepcopy(commit_details)

    if recovery_attempted:
        committed_ids = {d["target_id"] for d in details}
        outcome_ids = set(downgraded_items) | set(retracted_items)

        # Track targets that weren't committed
        for fid in target_flaw_ids:
            entity = f"flaw:{fid}"
            if entity not in committed_ids:
                details.append({
                    "target_id": entity,
                    "reason": "attempted_not_committed",
                    "success": False,
                    "failed_reason": "active_in_turn_but_not_downgraded" if entity not in outcome_ids else "demoted_to_candidate_only"
                })

        for cid in target_claim_ids:
            entity = f"claim:{cid}"
            if entity not in committed_ids:
                details.append({
                    "target_id": entity,
                    "reason": "attempt_not_committed",
                    "success": False,
                    "failed_reason": "not_transitioned_to_unsupported"
                })

    return details[:12]


def build_turn_log(
    turn_id: int,
    manager_payload: Dict[str, Any],
    worker_payloads: List[Dict[str, Any]],
    state: Dict[str, Any],
    final_report: str = "",
    revision_events: Optional[List[Dict[str, Any]]] = None,
    conflict_events: Optional[List[Dict[str, Any]]] = None,
    previous_action_type: str = "",
) -> Dict[str, Any]:
    action_type = manager_payload.get("action_type", "extract_claims")
    effective_action_type = manager_payload.get("effective_action_type") or action_type
    turn_mode = _resolve_turn_mode(manager_payload, action_type, effective_action_type)
    phase_before_action = _normalize_choice(manager_payload.get("phase_before_action"), REVIEW_PHASES, state.get("phase", "normal_review"))
    phase_after_action = _normalize_choice(state.get("phase"), REVIEW_PHASES, manager_payload.get("phase", "normal_review"))
    phase_turn_index = int(state.get("phase_turn_index", manager_payload.get("phase_turn_index", 0)) or 0)
    revision_meta = _classify_revision_events(revision_events or [], worker_payloads=worker_payloads)
    conflict_summary = _summarize_conflict_events(conflict_events or [])
    latest_patch_log = state.get("_latest_patch_log", {})
    recovery_attempted = _is_patch_recovery_attempt(
        action_type,
        effective_action_type,
        worker_payloads,
        latest_patch_log,
    )
    turn_patch_log = latest_patch_log if recovery_attempted or _has_recovery_payload(worker_payloads) else {}
    recovery_patch_mode_entered = turn_mode == "recovery_patch"
    recovery_emission_expected = recovery_patch_mode_entered
    recovery_emitted = _has_recovery_patch_emission(worker_payloads, turn_patch_log)
    emission_failure_code, emission_failure_message = _classify_emission_failure(
        manager_payload,
        worker_payloads,
        turn_patch_log,
        turn_mode,
        recovery_emitted,
        action_type,
        effective_action_type,
    )
    recovery_patch_source = turn_patch_log.get("recovery_patch_source", "none") or "none"
    worker_fallback_claim_ids: List[str] = []
    worker_fallback_evidence_ids: List[str] = []
    worker_fallback_contradiction = False
    for worker in worker_payloads or []:
        payload = worker.get("payload", {}) if isinstance(worker, dict) else {}
        for evidence in payload.get("evidence_map", []) or []:
            claim_id = str(evidence.get("claim_id") or "")
            evidence_id = str(evidence.get("evidence_id") or "")
            if claim_id.startswith("claim-fallback-") or claim_id.startswith("claim-general-"):
                worker_fallback_claim_ids.append(claim_id)
            if evidence_id.startswith("evidence-fallback-") or evidence_id.startswith("evidence-general-"):
                worker_fallback_evidence_ids.append(evidence_id)
        for note in payload.get("conflict_notes", []) or []:
            claim_id = str(note.get("claim_id") or "")
            evidence_id = str(note.get("evidence_id") or "")
            conflict_type = str(note.get("conflict_type") or "")
            if claim_id.startswith("claim-fallback-") or claim_id.startswith("claim-general-"):
                worker_fallback_claim_ids.append(claim_id)
            if evidence_id.startswith("evidence-fallback-") or evidence_id.startswith("evidence-general-"):
                worker_fallback_evidence_ids.append(evidence_id)
            if conflict_type.startswith("fallback_"):
                worker_fallback_contradiction = True
    fallback_claim_ids_used = list(dict.fromkeys((manager_payload.get("fallback_claim_ids_used") or []) + worker_fallback_claim_ids))[:8]
    fallback_evidence_ids_used = list(dict.fromkeys((manager_payload.get("fallback_evidence_ids_used") or []) + worker_fallback_evidence_ids))[:8]
    fallback_contradiction_emitted = bool(manager_payload.get("fallback_contradiction_emitted", False) or worker_fallback_contradiction)
    turn_claim_kind_counts = _claim_kind_counts(state.get("claims", []) or [])
    support_survival_trace = _build_payload_support_survival_trace(turn_id, manager_payload, worker_payloads, state)
    return {
        "turn_id": turn_id,
        "turn_index": turn_id,
        "decision": manager_payload.get("decision", "continue"),
        "action_type": action_type,
        "effective_action_type": effective_action_type,
        "turn_mode": turn_mode,
        "phase": phase_after_action,
        "phase_before_action": phase_before_action,
        "phase_after_action": phase_after_action,
        "phase_enter_reason": manager_payload.get("phase_enter_reason", state.get("phase_enter_reason", "")),
        "phase_exit_reason": manager_payload.get("phase_exit_reason", state.get("phase_exit_reason", "")),
        "phase_hold_reason": manager_payload.get("phase_hold_reason", state.get("phase_hold_reason", "")),
        "phase_turn_index": phase_turn_index,
        "recovery_patch_mode_entered": recovery_patch_mode_entered,
        "recovery_emission_expected": recovery_emission_expected,
        "recovery_emitted": recovery_emitted,
        "recovery_patch_emitted": recovery_emitted,
        "emission_failure_code": emission_failure_code,
        "emission_failure_message": emission_failure_message,
        "early_finalize_attempted": bool(manager_payload.get("early_finalize_attempted", False)),
        "finalize_blocked_by_phase": bool(manager_payload.get("finalize_blocked_by_phase", False)),
        "auto_finalized": bool(manager_payload.get("auto_finalized", False)),
        "strategy_changed": bool(previous_action_type and previous_action_type != effective_action_type),
        "selected_agents": manager_payload.get("selected_agents", []),
        "focus": manager_payload.get("focus", ""),
        "rationale": manager_payload.get("rationale", ""),
        "target_claim_ids": manager_payload.get("target_claim_ids", []),
        "target_flaw_ids": manager_payload.get("target_flaw_ids", []),
        "target_evidence_ids": manager_payload.get("target_evidence_ids", []),
        "target_hypotheses": manager_payload.get("target_hypotheses", []),
        "requires_clarification": manager_payload.get("requires_clarification", False),
        "clarification_question": manager_payload.get("clarification_question", ""),
        "summary_update": manager_payload.get("summary_update", ""),
        "policy_source": manager_payload.get("policy_source", "manager_model"),
        "policy_notes": manager_payload.get("policy_notes", []),
        "claim_coverage_expansion_required": bool(manager_payload.get("claim_coverage_expansion_required", False)),
        "claim_coverage_missing_tags": manager_payload.get("claim_coverage_missing_tags", []),
        "claim_coverage": manager_payload.get("claim_coverage", claim_coverage_summary(state)),
        "progression_gate_triggered": bool(manager_payload.get("progression_gate_triggered", False)),
        "progression_gate_reason": manager_payload.get("progression_gate_reason", ""),
        "progression_gate_raw_target_ids": manager_payload.get("progression_gate_raw_target_ids", []),
        "progression_gate_sanitized_target_ids": manager_payload.get("progression_gate_sanitized_target_ids", []),
        "support_formation_pass_triggered": bool(manager_payload.get("support_formation_pass_triggered", False)),
        "support_formation_pass_reason": manager_payload.get("support_formation_pass_reason", ""),
        "support_formation_pass_from_action": manager_payload.get("support_formation_pass_from_action", ""),
        "negative_evidence_formation_required": bool(
            manager_payload.get("negative_evidence_formation_required", False)
            or manager_payload.get("policy_source") == "negative_evidence_formation_override"
        ),
        "negative_evidence_binding_retry_required": bool(manager_payload.get("negative_evidence_binding_retry_required", False)),
        "blocked_aggressive_recovery_action": manager_payload.get("blocked_aggressive_recovery_action", ""),
        "fallback_target_gate_blocked": bool(manager_payload.get("fallback_target_gate_blocked", False)),
        "broad_target_gate_blocked": bool(manager_payload.get("broad_target_gate_blocked", False)),
        "weak_conflict_gate_blocked": bool(manager_payload.get("weak_conflict_gate_blocked", False)),
        "raw_target_claim_ids": manager_payload.get("raw_target_claim_ids", []),
        "raw_target_count": manager_payload.get("raw_target_count", 0),
        "raw_target_is_broad": bool(manager_payload.get("raw_target_is_broad", False)),
        "post_fallback_target_claim_ids": manager_payload.get("post_fallback_target_claim_ids", []),
        "post_fallback_target_count": manager_payload.get("post_fallback_target_count", 0),
        "fallback_target_present": bool(manager_payload.get("fallback_target_present", False) or fallback_claim_ids_used or fallback_evidence_ids_used),
        "fallback_claim_ids_used": fallback_claim_ids_used,
        "fallback_evidence_ids_used": fallback_evidence_ids_used,
        "fallback_contradiction_emitted": fallback_contradiction_emitted,
        "post_sanitize_target_claim_ids": manager_payload.get("post_sanitize_target_claim_ids", []),
        "post_sanitize_target_count": manager_payload.get("post_sanitize_target_count", 0),
        "sanitize_bloat_detected": bool(manager_payload.get("sanitize_bloat_detected", False)),
        "sanitize_bloat_delta": manager_payload.get("sanitize_bloat_delta", 0),
        "sanitize_expanded_from_raw": bool(manager_payload.get("sanitize_expanded_from_raw", False)),
        "sanitize_expanded_from_fallback": bool(manager_payload.get("sanitize_expanded_from_fallback", False)),
        "final_action_target_claim_ids": manager_payload.get("final_action_target_claim_ids", manager_payload.get("target_claim_ids", [])),
        "final_action_target_count": manager_payload.get("final_action_target_count", len(manager_payload.get("target_claim_ids", []) or [])),
        "final_action_type": manager_payload.get("final_action_type", action_type),
        "final_effective_action_type": manager_payload.get("final_effective_action_type", effective_action_type),
        "recovery_candidate_action": manager_payload.get("recovery_candidate_action", action_type),
        "recovery_push_triggered": bool(manager_payload.get("recovery_push_triggered", False)),
        "recovery_push_source": manager_payload.get("recovery_push_source", "none"),
        "recovery_push_reasons": manager_payload.get("recovery_push_reasons", []),
        "target_quality_label": manager_payload.get("target_quality_label", ""),
        "target_quality_reasons": manager_payload.get("target_quality_reasons", []),
        "tqc_target_source": manager_payload.get("tqc_target_source", "empty_or_unknown"),
        "tqc_target_width": manager_payload.get("tqc_target_width", "empty"),
        "tqc_evidence_grounding": manager_payload.get("tqc_evidence_grounding", "no_aligned_evidence"),
        "tqc_conflict_strength": manager_payload.get("tqc_conflict_strength", "weak_conflict"),
        "recovery_readiness_label": manager_payload.get("recovery_readiness_label", "not_ready_for_recovery"),
        "recovery_readiness_reasons": manager_payload.get("recovery_readiness_reasons", []),
        "recovery_entry_deferred": bool(manager_payload.get("recovery_entry_deferred", False)),
        "recovery_entry_defer_reason": manager_payload.get("recovery_entry_defer_reason", ""),
        "recovery_entry_deferred_from": manager_payload.get("recovery_entry_deferred_from", ""),
        "evidence_context_chars": manager_payload.get("evidence_context_chars", state.get("_latest_evidence_context_meta", {}).get("evidence_context_chars", 0)),
        "evidence_context_mode": manager_payload.get("evidence_context_mode", state.get("_latest_evidence_context_meta", {}).get("evidence_context_mode", "")),
        "evidence_context_cleaned_wrapper": bool(manager_payload.get("evidence_context_cleaned_wrapper", state.get("_latest_evidence_context_meta", {}).get("evidence_context_cleaned_wrapper", False))),
        "evidence_context_contains_method": bool(manager_payload.get("evidence_context_contains_method", state.get("_latest_evidence_context_meta", {}).get("evidence_context_contains_method", False))),
        "evidence_context_contains_results": bool(manager_payload.get("evidence_context_contains_results", state.get("_latest_evidence_context_meta", {}).get("evidence_context_contains_results", False))),
        "evidence_context_contains_conclusion": bool(manager_payload.get("evidence_context_contains_conclusion", state.get("_latest_evidence_context_meta", {}).get("evidence_context_contains_conclusion", False))),
        "evidence_context_contains_table_or_figure": bool(manager_payload.get("evidence_context_contains_table_or_figure", state.get("_latest_evidence_context_meta", {}).get("evidence_context_contains_table_or_figure", False))),
        "evidence_context_contains_claim_match": bool(manager_payload.get("evidence_context_contains_claim_match", state.get("_latest_evidence_context_meta", {}).get("evidence_context_contains_claim_match", False))),
        "evidence_context_contains_empirical_terms": bool(manager_payload.get("evidence_context_contains_empirical_terms", state.get("_latest_evidence_context_meta", {}).get("evidence_context_contains_empirical_terms", False))),
        "evidence_context_empirical_term_count": int(manager_payload.get("evidence_context_empirical_term_count", state.get("_latest_evidence_context_meta", {}).get("evidence_context_empirical_term_count", 0)) or 0),
        "evidence_context_table_or_figure_term_count": int(manager_payload.get("evidence_context_table_or_figure_term_count", state.get("_latest_evidence_context_meta", {}).get("evidence_context_table_or_figure_term_count", 0)) or 0),
        "evidence_context_method_term_count": int(manager_payload.get("evidence_context_method_term_count", state.get("_latest_evidence_context_meta", {}).get("evidence_context_method_term_count", 0)) or 0),
        "evidence_context_claim_query_term_count": int(manager_payload.get("evidence_context_claim_query_term_count", state.get("_latest_evidence_context_meta", {}).get("evidence_context_claim_query_term_count", 0)) or 0),
        "evidence_context_claim_query_terms": manager_payload.get("evidence_context_claim_query_terms", state.get("_latest_evidence_context_meta", {}).get("evidence_context_claim_query_terms", [])),
        "evidence_context_snippet_sources": manager_payload.get("evidence_context_snippet_sources", state.get("_latest_evidence_context_meta", {}).get("evidence_context_snippet_sources", [])),
        "evidence_quote_bank_count": int(manager_payload.get("evidence_quote_bank_count", state.get("_latest_evidence_context_meta", {}).get("evidence_quote_bank_count", 0)) or 0),
        "evidence_quote_bank_sources": manager_payload.get("evidence_quote_bank_sources", state.get("_latest_evidence_context_meta", {}).get("evidence_quote_bank_sources", [])),
        "evidence_quote_bank_claim_matched_count": int(manager_payload.get("evidence_quote_bank_claim_matched_count", state.get("_latest_evidence_context_meta", {}).get("evidence_quote_bank_claim_matched_count", 0)) or 0),
        "evidence_quote_bank_mode": manager_payload.get("evidence_quote_bank_mode", state.get("_latest_evidence_context_meta", {}).get("evidence_quote_bank_mode", "")),
        "evidence_empirical_observability_mode": manager_payload.get("evidence_empirical_observability_mode", ""),
        "evidence_raw_contains_empirical_terms": bool(manager_payload.get("evidence_raw_contains_empirical_terms", False)),
        "evidence_raw_contains_table_or_figure_terms": bool(manager_payload.get("evidence_raw_contains_table_or_figure_terms", False)),
        "evidence_raw_empirical_term_count": int(manager_payload.get("evidence_raw_empirical_term_count", 0) or 0),
        "evidence_raw_negative_empirical_term_count": int(manager_payload.get("evidence_raw_negative_empirical_term_count", 0) or 0),
        "evidence_payload_evidence_count": int(manager_payload.get("evidence_payload_evidence_count", 0) or 0),
        "evidence_payload_empirical_evidence_count": int(manager_payload.get("evidence_payload_empirical_evidence_count", 0) or 0),
        "evidence_payload_table_or_figure_count": int(manager_payload.get("evidence_payload_table_or_figure_count", 0) or 0),
        "evidence_payload_method_evidence_count": int(manager_payload.get("evidence_payload_method_evidence_count", 0) or 0),
        "evidence_payload_strong_empirical_count": int(manager_payload.get("evidence_payload_strong_empirical_count", 0) or 0),
        "evidence_payload_support_empirical_count": int(manager_payload.get("evidence_payload_support_empirical_count", 0) or 0),
        "evidence_payload_has_empirical_evidence": bool(manager_payload.get("evidence_payload_has_empirical_evidence", False)),
        "evidence_empirical_structuring_status": manager_payload.get("evidence_empirical_structuring_status", ""),
        "support_survival_trace": support_survival_trace,
        "payload_support_total": len(support_survival_trace),
        "payload_real_strong_support_total": sum(
            1
            for item in support_survival_trace
            if item.get("initial_strength") == "strong" and item.get("claim_kind") == "paper_extracted"
        ),
        "merged_payload_support_total": sum(1 for item in support_survival_trace if item.get("merged_into_state")),
        "semantic_verified_payload_support_total": sum(
            1 for item in support_survival_trace if item.get("semantic_grounding_label") == "semantic_support_verified"
        ),
        "final_view_payload_support_total": sum(1 for item in support_survival_trace if item.get("included_in_final_view")),
        "evidence_json_contract_mode": manager_payload.get("evidence_json_contract_mode", ""),
        "evidence_json_parse_status": manager_payload.get("evidence_json_parse_status", ""),
        "evidence_json_failure_type": manager_payload.get("evidence_json_failure_type", ""),
        "evidence_json_parse_error": manager_payload.get("evidence_json_parse_error", ""),
        "evidence_json_partial_recovery": bool(manager_payload.get("evidence_json_partial_recovery", False)),
        "evidence_json_fallback_payload_used": bool(manager_payload.get("evidence_json_fallback_payload_used", False)),
        "evidence_json_raw_chars": int(manager_payload.get("evidence_json_raw_chars", 0) or 0),
        "evidence_json_prompt_chars": int(manager_payload.get("evidence_json_prompt_chars", 0) or 0),
        "evidence_focus_mode": manager_payload.get("evidence_focus_mode", ""),
        "evidence_focus_applied": bool(manager_payload.get("evidence_focus_applied", False)),
        "evidence_focus_reason": manager_payload.get("evidence_focus_reason", ""),
        "evidence_focus_original_claim_ids": manager_payload.get("evidence_focus_original_claim_ids", []),
        "evidence_focus_selected_claim_ids": manager_payload.get("evidence_focus_selected_claim_ids", []),
        "evidence_focus_preferred_claim_ids": manager_payload.get("evidence_focus_preferred_claim_ids", []),
        "evidence_focus_original_claim_count": int(
            manager_payload.get(
                "evidence_focus_original_claim_count",
                len(manager_payload.get("evidence_focus_original_claim_ids", []) or []),
            )
            or 0
        ),
        "evidence_focus_selected_claim_count": int(
            manager_payload.get(
                "evidence_focus_selected_claim_count",
                len(manager_payload.get("evidence_focus_selected_claim_ids", []) or []),
            )
            or 0
        ),
        "evidence_focus_preferred_claim_count": int(
            manager_payload.get(
                "evidence_focus_preferred_claim_count",
                len(manager_payload.get("evidence_focus_preferred_claim_ids", []) or []),
            )
            or 0
        ),
        "fallback_claim_targets_omitted": manager_payload.get("fallback_claim_targets_omitted", []),
        "fallback_claim_targets_omitted_count": manager_payload.get(
            "fallback_claim_targets_omitted_count",
            len(manager_payload.get("fallback_claim_targets_omitted", []) or []),
        ),
        "fallback_targets_replaced_with_real_candidates": bool(manager_payload.get("fallback_targets_replaced_with_real_candidates", False)),
        "pending_user_question": state.get("pending_user_question", ""),
        "simulated_user_reply": state.get("simulated_user_reply", ""),
        "active_focus": state.get("active_focus", state.get("last_focus", "")),
        "revision_events": copy.deepcopy(revision_events or []),
        "revised_entities": [
            f"{item.get('entity_type', 'unknown')}:{item.get('entity_id', '')}:{item.get('field', '')}"
            for item in (revision_events or [])
        ],
        "new_items": revision_meta["new_items"],
        "downgraded_items": revision_meta["downgraded_items"],
        "retracted_items": revision_meta["retracted_items"],
        "reason_for_revision": revision_meta["revision_reasons"],
        "conflict_events": copy.deepcopy(conflict_events or []),
        "conflicts_detected": conflict_summary,
        "evidence_gaps": copy.deepcopy(_open_evidence_gaps(state)[:6]),
        "evidence_gap_lifecycle": copy.deepcopy(_normalize_evidence_gaps(state.get("evidence_gaps", []), max_items=10)),
        "revision_summary": copy.deepcopy(state.get("revision_summary", [])[:4]),
        "conflict_summary": copy.deepcopy(state.get("conflict_summary", [])[:4]),
        "risk_profile": copy.deepcopy(state.get("risk_profile", {})),
        "open_unresolved_questions": _open_unresolved_questions(state)[:6],
        "claim_kind_counts": turn_claim_kind_counts,
        "paper_extracted_claim_count": turn_claim_kind_counts.get("paper_extracted", 0),
        "non_paper_claim_count": sum(
            value
            for key, value in turn_claim_kind_counts.items()
            if key != "paper_extracted"
        ),
        "recovery_attempted": bool(turn_patch_log.get("recovery_attempted", False)),
        "recovery_validated": bool(turn_patch_log.get("recovery_validated", False)),
        "recovery_patch_validated": bool(turn_patch_log.get("recovery_validated", False)),
        "recovery_blocked": bool(turn_patch_log.get("recovery_blocked", False)),
        "recovery_committed": bool(turn_patch_log.get("recovery_committed", False)),
        "recovery_patch_committed": bool(turn_patch_log.get("recovery_committed", False)),
        "recovery_failure_code": turn_patch_log.get("recovery_failure_code", ""),
        "recovery_failure_message": turn_patch_log.get("recovery_failure_message", ""),
        "recovery_target_type": turn_patch_log.get("recovery_target_type", ""),
        "recovery_target_id": turn_patch_log.get("recovery_target_id", ""),
        "recovery_target_gate_label": turn_patch_log.get("recovery_target_gate_label", ""),
        "recovery_patch_operation": turn_patch_log.get("recovery_patch_operation", ""),
        "recovery_target_commit_allowed": bool(turn_patch_log.get("recovery_target_commit_allowed", False)),
        "old_status": turn_patch_log.get("old_status", ""),
        "new_status": turn_patch_log.get("new_status", ""),
        "recovery_state_delta": copy.deepcopy(turn_patch_log.get("recovery_state_delta", {})),
        "recovery_consistency_improved": bool(turn_patch_log.get("recovery_consistency_improved", False)),
        "negative_recovery_commit": bool(turn_patch_log.get("negative_recovery_commit", False)),
        "supporting_evidence_ids": _strip_synthetic_recovery_markers(
            turn_patch_log.get("supporting_evidence_ids", [])
        ),
        "resolved_conflict_count": turn_patch_log.get("resolved_conflict_count", 0),
        "recovery_patch_source": recovery_patch_source,
        "recovery_terminal": bool(turn_patch_log.get("recovery_terminal", False)),
        "recovery_terminal_reason": turn_patch_log.get("recovery_terminal_reason", ""),
        "recovery_repeat_allowed": bool(turn_patch_log.get("recovery_repeat_allowed", True)),
        "sticky_target_id": state.get("sticky_target_id", ""),
        "sticky_target_type": state.get("sticky_target_type", ""),
        "sticky_target_active": bool(state.get("sticky_target_active", False)),
        "sticky_target_turns_remaining": int(state.get("sticky_target_turns_remaining", 0) or 0),
        "sticky_release_reason": state.get("sticky_release_reason", ""),
        "sticky_target_applied": bool(manager_payload.get("sticky_target_applied", False)),
        "sticky_target_reused": bool(manager_payload.get("sticky_target_reused", False)),
        "sticky_target_released": bool(manager_payload.get("sticky_target_released", False)),
        "target_switch_blocked_by_sticky": bool(manager_payload.get("target_switch_blocked_by_sticky", False)),
        "recovery_type": _recovery_type(action_type, effective_action_type),
        "recovery_success": bool(turn_patch_log.get("recovery_committed", False) and revision_meta["commit_applied"]),
        "recovery_commit_applied": bool(turn_patch_log.get("recovery_committed", False) and revision_meta["commit_applied"]),
        # Stratified 4-layer recovery taxonomy.  Paper-level statistics should
        # prefer these explicit fields over the legacy ``recovery_patch_committed``
        # / ``recovery_success`` aliases above (which collapse different stages).
        **_compute_recovery_layer_fields(turn_patch_log, revision_meta),
        "recovery_details": _build_recovery_details(
            revision_meta["commit_details"],
            bool(turn_patch_log.get("recovery_attempted", False)),
            manager_payload.get("target_flaw_ids", []),
            manager_payload.get("target_claim_ids", []),
            revision_meta["downgraded_items"],
            revision_meta["retracted_items"],
        ) if turn_patch_log.get("recovery_attempted", False) else [],
        "recovery_blocked_by": (
            turn_patch_log.get("recovery_failure_message", "")
            or _recovery_blocked_reason(
                bool(turn_patch_log.get("recovery_attempted", False)),
                revision_meta["downgraded_items"],
                revision_meta["retracted_items"],
                conflict_summary,
            )
        ) if (turn_patch_log.get("recovery_attempted", False) and not turn_patch_log.get("recovery_committed", False)) else "",
        "manager_payload": copy.deepcopy(manager_payload),
        "worker_payloads": copy.deepcopy(worker_payloads),
        "state_snapshot": compact_review_state_for_prompt(state),
        "final_report": final_report,
    }

def maybe_write_turn_log(log_dir: Optional[str], task: Dict[str, Any], logs: List[Dict[str, Any]]) -> Optional[str]:
    if not log_dir:
        return None
    os.makedirs(log_dir, exist_ok=True)
    safe_paper_id = re.sub(r"[^a-zA-Z0-9._-]+", "_", task["paper_id"])[:80] or "paper"
    filename = f"{safe_paper_id}_{datetime.utcnow().strftime('%Y%m%dT%H%M%S%f')}.json"
    path = os.path.join(log_dir, filename)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(
            {
                "paper_id": task["paper_id"],
                "data_source": task["data_source"],
                "mode": task["mode"],
                "max_turns": task["max_turns"],
                "review_state": task["review_state"],
                "turn_logs": logs,
            },
            handle,
            ensure_ascii=False,
            indent=2,
        )
    return path
