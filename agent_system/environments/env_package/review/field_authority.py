from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Sequence, Set, Tuple


CLAIM_AGENT = "claim"
EVIDENCE_AGENT = "evidence"
CRITIQUE_AGENT = "critique"
MANAGER = "manager"
CLAIM_JUDGE = "claim_judge"
EVIDENCE_JUDGE = "evidence_judge"
ISSUE_JUDGE = "issue_judge"
DETERMINISTIC_VERIFIER = "deterministic_verifier"
ADMISSION = "admission"
RECOVERY = "recovery"
REPORT_RENDERER = "report_renderer"

_ALIASES = {
    "review manager agent": MANAGER,
    "manager": MANAGER,
    "claim agent": CLAIM_AGENT,
    "claim": CLAIM_AGENT,
    "evidence agent": EVIDENCE_AGENT,
    "evidence": EVIDENCE_AGENT,
    "critique agent": CRITIQUE_AGENT,
    "critique": CRITIQUE_AGENT,
    "claim judge": CLAIM_JUDGE,
    "evidence judge": EVIDENCE_JUDGE,
    "review issue judge": ISSUE_JUDGE,
    "issue judge": ISSUE_JUDGE,
    "deterministic verifier": DETERMINISTIC_VERIFIER,
    "admission": ADMISSION,
    "recovery": RECOVERY,
    "state renderer": REPORT_RENDERER,
    "report renderer": REPORT_RENDERER,
}

_TOP_LEVEL_OWNERS: Mapping[str, Set[str]] = {
    "claims": {CLAIM_AGENT, CLAIM_JUDGE, DETERMINISTIC_VERIFIER, RECOVERY},
    "evidence_map": {EVIDENCE_AGENT, EVIDENCE_JUDGE, DETERMINISTIC_VERIFIER, ADMISSION, RECOVERY},
    "flaw_candidates": {ISSUE_JUDGE, ADMISSION, RECOVERY},
    "reviewer_negative_candidates": {CRITIQUE_AGENT, ISSUE_JUDGE},
    "current_hypotheses": {CRITIQUE_AGENT},
    "conflict_notes": {ADMISSION, RECOVERY},
    "contested_relations": {ADMISSION, RECOVERY},
    "evidence_gaps": {CLAIM_AGENT, EVIDENCE_AGENT, CLAIM_JUDGE, EVIDENCE_JUDGE},
    "unresolved_questions": {CLAIM_AGENT, EVIDENCE_AGENT, CRITIQUE_AGENT, MANAGER, RECOVERY},
    "recommendation": {REPORT_RENDERER},
    "final_report": {REPORT_RENDERER},
    "user_report": {REPORT_RENDERER},
    "decision": {MANAGER},
    "selected_agents": {MANAGER},
    "action_type": {MANAGER},
    "focus": {MANAGER},
    "active_focus": {MANAGER},
    "summary_update": {MANAGER},
    "dialogue_summary": {MANAGER},
    "pending_user_question": {MANAGER},
    "clarification_question": {MANAGER},
    "clarification_needed": {MANAGER},
}

_FIELD_OWNERS: Mapping[str, Mapping[str, Set[str]]] = {
    "claims": {
        "claim": {CLAIM_AGENT},
        "text": {CLAIM_AGENT},
        "importance": {CLAIM_AGENT, CLAIM_JUDGE},
        "claim_type": {CLAIM_AGENT, CLAIM_JUDGE},
        "claim_kind": {CLAIM_AGENT, CLAIM_JUDGE},
        "claim_source": {CLAIM_AGENT, DETERMINISTIC_VERIFIER},
        "claim_extraction_source": {CLAIM_AGENT, DETERMINISTIC_VERIFIER},
        "source": {CLAIM_AGENT, DETERMINISTIC_VERIFIER},
        "source_locator": {CLAIM_AGENT, DETERMINISTIC_VERIFIER},
        "source_span_start": {CLAIM_AGENT, DETERMINISTIC_VERIFIER},
        "source_span_end": {CLAIM_AGENT, DETERMINISTIC_VERIFIER},
        "span_start": {CLAIM_AGENT, DETERMINISTIC_VERIFIER},
        "span_end": {CLAIM_AGENT, DETERMINISTIC_VERIFIER},
        "claim_obligations": {CLAIM_AGENT, CLAIM_JUDGE},
        "required_evidence_types": {CLAIM_AGENT, CLAIM_JUDGE},
        "review_obligations": {CLAIM_AGENT, CLAIM_JUDGE},
        "evidence_need": {CLAIM_AGENT, CLAIM_JUDGE},
        "verification_need": {CLAIM_AGENT, CLAIM_JUDGE},
        "coverage_tags": {CLAIM_AGENT, CLAIM_JUDGE},
        "status": {CLAIM_JUDGE, RECOVERY},
        "supporting_evidence_ids": {EVIDENCE_JUDGE, ADMISSION, RECOVERY},
    },
    "evidence_map": {
        "evidence": {EVIDENCE_AGENT},
        "text": {EVIDENCE_AGENT},
        "raw_quote": {EVIDENCE_AGENT},
        "quote": {EVIDENCE_AGENT},
        "agent_raw_quote": {EVIDENCE_AGENT},
        "source": {EVIDENCE_AGENT},
        "source_locator": {EVIDENCE_AGENT},
        "source_span_start": {EVIDENCE_AGENT, DETERMINISTIC_VERIFIER},
        "source_span_end": {EVIDENCE_AGENT, DETERMINISTIC_VERIFIER},
        "span_start": {EVIDENCE_AGENT, DETERMINISTIC_VERIFIER},
        "span_end": {EVIDENCE_AGENT, DETERMINISTIC_VERIFIER},
        "claim_id": {EVIDENCE_AGENT},
        "quote_id": {EVIDENCE_AGENT},
        "source_quote_id": {EVIDENCE_AGENT},
        "required_evidence_type": {EVIDENCE_AGENT, EVIDENCE_JUDGE},
        "targeted_negative_search_task_id": {EVIDENCE_AGENT},
        "reviewer_negative_candidate_id": {EVIDENCE_AGENT},
        "stance": {EVIDENCE_JUDGE, ADMISSION},
        "strength": {EVIDENCE_JUDGE, ADMISSION},
        "binding_status": {EVIDENCE_JUDGE},
        "binding_confidence": {EVIDENCE_JUDGE},
        "verified_grounding_label": {DETERMINISTIC_VERIFIER},
        "verified_grounding_reason": {DETERMINISTIC_VERIFIER},
        "verified_source_span_start": {DETERMINISTIC_VERIFIER},
        "verified_source_span_end": {DETERMINISTIC_VERIFIER},
        "verified_quote_match_type": {DETERMINISTIC_VERIFIER},
        "semantic_grounding_label": {EVIDENCE_JUDGE},
        "review_negative_label": {ISSUE_JUDGE},
        "review_issue_verification_status": {ISSUE_JUDGE, ADMISSION},
    },
    "flaw_candidates": {
        "title": {ISSUE_JUDGE, ADMISSION, RECOVERY},
        "description": {ISSUE_JUDGE, ADMISSION, RECOVERY},
        "weakness_type": {ISSUE_JUDGE, ADMISSION, RECOVERY},
        "severity": {ISSUE_JUDGE, ADMISSION, RECOVERY},
        "related_claim_ids": {ISSUE_JUDGE, ADMISSION, RECOVERY},
        "required_evidence_type": {ISSUE_JUDGE, ADMISSION, RECOVERY},
        "criterion": {ISSUE_JUDGE, ADMISSION, RECOVERY},
        "confidence": {ISSUE_JUDGE, ADMISSION, RECOVERY},
        "paper_side_rationale": {ISSUE_JUDGE, ADMISSION, RECOVERY},
        "source_stage": {ISSUE_JUDGE, ADMISSION, RECOVERY},
        "source": {ISSUE_JUDGE, ADMISSION, RECOVERY},
        "status": {ISSUE_JUDGE, ADMISSION, RECOVERY},
        "evidence_ids": {ISSUE_JUDGE, ADMISSION, RECOVERY},
        "negative_evidence_ids": {ISSUE_JUDGE, ADMISSION, RECOVERY},
        "verified_negative_evidence_ids": {ISSUE_JUDGE, ADMISSION, RECOVERY},
        "grounding_status": {DETERMINISTIC_VERIFIER},
    },
    "reviewer_negative_candidates": {
        "claim_id": {CRITIQUE_AGENT, ISSUE_JUDGE},
        "obligation_id": {CRITIQUE_AGENT, ISSUE_JUDGE},
        "claim": {CRITIQUE_AGENT, ISSUE_JUDGE},
        "weakness": {CRITIQUE_AGENT, ISSUE_JUDGE},
        "hypothesis": {CRITIQUE_AGENT, ISSUE_JUDGE},
        "negative_type": {CRITIQUE_AGENT, ISSUE_JUDGE},
        "required_evidence_type": {CRITIQUE_AGENT, ISSUE_JUDGE},
        "quote_grounding_mode": {CRITIQUE_AGENT, ISSUE_JUDGE},
        "verification_question": {CRITIQUE_AGENT, ISSUE_JUDGE},
        "expected_quote_cues": {CRITIQUE_AGENT, ISSUE_JUDGE},
        "missing_or_weak_items": {CRITIQUE_AGENT, ISSUE_JUDGE},
        "candidate_raw_quote": {CRITIQUE_AGENT, ISSUE_JUDGE},
        "quote_id": {CRITIQUE_AGENT, ISSUE_JUDGE},
        "source_locator": {CRITIQUE_AGENT, ISSUE_JUDGE},
        "observed_inventory": {CRITIQUE_AGENT, ISSUE_JUDGE},
        "rationale": {CRITIQUE_AGENT, ISSUE_JUDGE},
        "confidence": {CRITIQUE_AGENT, ISSUE_JUDGE},
        "status": {CRITIQUE_AGENT, ISSUE_JUDGE},
        "source": {CRITIQUE_AGENT, ISSUE_JUDGE},
        "source_of_expectation": {CRITIQUE_AGENT, ISSUE_JUDGE},
        "target_locator_hint": {CRITIQUE_AGENT, ISSUE_JUDGE},
    },
}

_IDENTITY_FIELDS = {
    "claims": {"claim_id"},
    "evidence_map": {"evidence_id", "quote_id"},
    "flaw_candidates": {"flaw_id"},
    "reviewer_negative_candidates": {"candidate_id"},
}


@dataclass(frozen=True)
class AuthorityViolation:
    actor: str
    path: str
    reason: str


def normalize_actor(actor: str) -> str:
    value = str(actor or "").strip().lower()
    return _ALIASES.get(value, value.replace(" ", "_"))


def _field_allowed(actor: str, container: str, field: str) -> bool:
    if field in _IDENTITY_FIELDS.get(container, set()):
        return actor in _TOP_LEVEL_OWNERS.get(container, set())
    explicit = _FIELD_OWNERS.get(container, {}).get(field)
    if explicit is not None:
        return actor in explicit
    if container in _FIELD_OWNERS:
        return False
    return actor in _TOP_LEVEL_OWNERS.get(container, set())


def audit_update_authority(actor: str, payload: Mapping[str, Any]) -> List[AuthorityViolation]:
    normalized_actor = normalize_actor(actor)
    violations: List[AuthorityViolation] = []
    for key, value in payload.items():
        owners = _TOP_LEVEL_OWNERS.get(key)
        if owners is None:
            continue
        if normalized_actor not in owners:
            violations.append(AuthorityViolation(normalized_actor, key, "top_level_owner_mismatch"))
            continue
        if key not in _FIELD_OWNERS or not isinstance(value, list):
            continue
        for index, item in enumerate(value):
            if not isinstance(item, Mapping):
                continue
            for field in item:
                if not _field_allowed(normalized_actor, key, field):
                    violations.append(AuthorityViolation(normalized_actor, f"{key}[{index}].{field}", "field_owner_mismatch"))
    return violations


def filter_unauthorized_update(actor: str, payload: Mapping[str, Any]) -> Tuple[Dict[str, Any], List[AuthorityViolation]]:
    normalized_actor = normalize_actor(actor)
    filtered = copy.deepcopy(dict(payload))
    violations = audit_update_authority(normalized_actor, payload)
    for key in list(filtered):
        owners = _TOP_LEVEL_OWNERS.get(key)
        if owners is not None and normalized_actor not in owners:
            filtered.pop(key, None)
            continue
        if key not in _FIELD_OWNERS or not isinstance(filtered.get(key), list):
            continue
        cleaned_items: List[Any] = []
        for item in filtered[key]:
            if not isinstance(item, dict):
                cleaned_items.append(item)
                continue
            cleaned_items.append({field: value for field, value in item.items() if _field_allowed(normalized_actor, key, field)})
        filtered[key] = cleaned_items
    return filtered, violations


def authority_matrix() -> Dict[str, Dict[str, Sequence[str]]]:
    return {
        "top_level": {key: sorted(value) for key, value in _TOP_LEVEL_OWNERS.items()},
        "fields": {
            f"{container}.{field}": sorted(owners)
            for container, fields in _FIELD_OWNERS.items()
            for field, owners in fields.items()
        },
    }
