from __future__ import annotations

import hashlib
import re
from typing import Any, Dict, Iterable, List, Sequence


ABSTRACT_RE = re.compile(r"\b(abstract|title)\b", re.I)
METHOD_RE = re.compile(r"\b(method|approach|model|framework|algorithm|architecture|training objective|loss function|design)\b", re.I)
RESULT_RE = re.compile(r"\b(result|evaluation|experiment|benchmark|baseline|dataset|metric|performance|outperform|accuracy|f1|auc|bleu|rouge)\b", re.I)
TABLE_RE = re.compile(r"\b(table|tab\.?|figure|fig\.?)\b", re.I)
ABLATION_RE = re.compile(r"\bablation\b|ablat", re.I)
CONCLUSION_RE = re.compile(r"\b(conclusion|discussion)\b", re.I)
FRAMEWORK_FIGURE_RE = re.compile(r"\b(framework|overview|architecture|pipeline|workflow|diagram|schematic)\b", re.I)
THEORY_RE = re.compile(r"\b(theorem|lemma|proposition|corollary|proof|provably|convergence|generalization bound|sample complexity|regret bound)\b", re.I)
# R1 empirical-admission tightening regexes.
# Concrete empirical outcome wording: numbers, comparison verdicts, or metric deltas.
_EMPIRICAL_OUTCOME_RE = re.compile(
    r"(\b\d+(?:\.\d+)?\s*%|\b\d+\.\d+\b|"
    r"\b(outperform|outperforms|improv\w*|reduc\w*|increas\w*|decreas\w*|"
    r"higher|lower|better|worse|surpass\w*|exceed\w*|gain\w*|drop\w*|"
    r"performance|perform\w*|show\w*|demonstrat\w*|achiev\w*|result\w*|"
    r"state-of-the-art|sota|effective\w*|superior)\b|"
    r"\b(accuracy|f1|auc|bleu|rouge|precision|recall|mae|rmse|psnr|score)\b)",
    re.I,
)
# Pure dataset / experimental-setup wording (not effectiveness by itself).
_DATASET_SETUP_RE = re.compile(
    r"(\bexperimental setup\b|\bimplementation details?\b|"
    r"\bhyper-?parameters?\b|\btrain(?:ing)?/test split\b|"
    r"\b(train|test|validation)\s+split\b|"
    r"\bwe (use|adopt|employ)\s+the\b.*\b(dataset|datasets|benchmark|benchmarks)\b|"
    r"\b(datasets?|benchmarks?)\s+used\s+(for|in)\b|"
    r"\binstructions?\s+used\s+in\b)",
    re.I,
)
# Generic intent-to-evaluate wording with no reported outcome.
_GENERIC_EVAL_INTENT_RE = re.compile(
    r"\b(we (?:evaluate|test|assess|validate|conduct experiments?|run experiments?|"
    r"perform experiments?|carry out experiments?|report results?)|"
    r"experiments? (?:are|were) (?:conducted|performed|carried out)|"
    r"to (?:evaluate|assess|validate))\b",
    re.I,
)


def _text(*values: Any) -> str:
    return " ".join(str(value or "") for value in values).strip()


def evidence_section_bucket(evidence: Dict[str, Any]) -> str:
    """Classify the paper section/source behind an evidence item.

    The rule is intentionally conservative: a figure is not empirical by itself.
    Framework/architecture figures are method support unless paired with result,
    metric, benchmark, ablation, or table wording.
    """
    source = _text(
        evidence.get("source"),
        evidence.get("source_locator"),
        evidence.get("section"),
        evidence.get("snippet_source"),
        evidence.get("source_section"),
        evidence.get("verified_source_bucket"),
    )
    body = _text(evidence.get("evidence"), evidence.get("raw_quote"), evidence.get("support_quality_reason"), evidence.get("binding_rationale"))
    combined = f"{source} {body}"
    bucket = str(evidence.get("support_source_bucket") or "").strip().lower()

    if ABSTRACT_RE.search(source):
        return "abstract"
    if ABLATION_RE.search(combined):
        return "ablation"
    if TABLE_RE.search(source) or TABLE_RE.search(body):
        if FRAMEWORK_FIGURE_RE.search(combined) and not RESULT_RE.search(combined) and not ABLATION_RE.search(combined):
            return "method"
        return "table_or_figure"
    if METHOD_RE.search(source) or bucket in {"method_or_approach", "method_or_design", "method"}:
        return "method"
    if THEORY_RE.search(source) or bucket in {"theory_or_proof", "proof", "theory"}:
        return "theory_or_proof"
    if RESULT_RE.search(combined) or bucket in {"result_or_experiment", "result", "results", "experiment"}:
        return "result"
    if THEORY_RE.search(combined):
        return "theory_or_proof"
    if METHOD_RE.search(combined):
        return "method"
    if CONCLUSION_RE.search(source):
        return "conclusion"
    if bucket == "abstract":
        return "abstract"
    return "unknown"


def support_role(evidence: Dict[str, Any]) -> str:
    section = evidence_section_bucket(evidence)
    text = _text(evidence.get("source"), evidence.get("evidence"), evidence.get("support_quality_reason"))
    if section == "ablation":
        return "ablation_support"
    if section in {"result", "table_or_figure"}:
        if re.search(r"\b(baseline|compare|comparison|outperform)\b", text, re.I):
            return "comparison_support"
        return "empirical_result"
    if section == "method":
        return "method_description"
    if section == "theory_or_proof":
        return "theory_or_proof_support"
    if section == "abstract":
        return "claim_articulation"
    if re.search(r"\b(limitation|failure|weakness)\b", text, re.I):
        return "limitation_discussion"
    return "unclear"


def support_depth(evidence: Dict[str, Any]) -> str:
    section = evidence_section_bucket(evidence)
    if section in {"result", "table_or_figure", "ablation", "theory_or_proof"}:
        return "deep"
    if section == "method":
        return "moderate"
    if section == "abstract":
        return "shallow"
    return "moderate" if str(evidence.get("strength") or "") == "strong" else "shallow"


def independence_group_id(evidence: Dict[str, Any]) -> str:
    """Return a conservative independent-support group id.

    Independence is claim-local and locator-aware. The previous grouping used
    only ``claim_id|section|source``; after quote-bank canonicalisation many
    rows carry generic ``source`` values such as ``Results`` or ``method``, so
    distinct Table/Figure/Section anchors were collapsed into one group. This
    function prefers a concrete locator, falls back to the canonical quote id,
    and finally uses a short raw-quote digest. Exact duplicate quotes for the
    same claim still collapse to one group.
    """
    claim_id = str(evidence.get("claim_id") or "unknown")
    section = evidence_section_bucket(evidence)
    locator = re.sub(
        r"\s+",
        " ",
        str(
            evidence.get("source_locator")
            or evidence.get("verified_source_locator")
            or evidence.get("source")
            or section
        ).strip().lower(),
    )[:120]
    quote_value = re.sub(
        r"\s+",
        " ",
        str(evidence.get("quote_id") or evidence.get("raw_quote") or "").strip().lower(),
    )
    quote_key = hashlib.sha1(quote_value[:320].encode("utf-8")).hexdigest()[:10] if quote_value else "noquote"
    normalized = f"{claim_id}|{section}|{locator}|{quote_key}"
    digest = hashlib.sha1(normalized.encode("utf-8")).hexdigest()[:10]
    return f"support-group-{digest}"


def _claim_is_effectiveness(claim: Dict[str, Any] | None) -> bool:
    """Effectiveness / empirical claim: needs demonstrated results, not just a method."""
    if not isinstance(claim, dict):
        return False
    ctype = str(claim.get("claim_type") or "").strip().lower()
    if ctype in {"empirical", "effectiveness", "result", "performance"}:
        return True
    tags = claim.get("coverage_tags") or []
    if isinstance(tags, (list, tuple, set)):
        tagset = {str(t or "").strip().lower() for t in tags}
        if tagset & {"empirical", "effectiveness", "result", "experiment"}:
            return True
    need = str(claim.get("evidence_need") or "").lower()
    return "result" in need or "empirical" in need or "effectiveness" in need


def _empirical_admission_block_reason(
    evidence: Dict[str, Any],
    section: str,
    claim: Dict[str, Any] | None,
) -> str:
    """Return a non-empty block reason iff this evidence must NOT count as empirical support.

    Pure tightening: only reduces misclassified empirical support. Never promotes.
    """
    body = _text(
        evidence.get("evidence"),
        evidence.get("raw_quote"),
        evidence.get("support_quality_reason"),
        evidence.get("binding_rationale"),
    )
    has_outcome = bool(_EMPIRICAL_OUTCOME_RE.search(body))
    # 1. method/theory quote offered as support for an effectiveness claim.
    if _claim_is_effectiveness(claim) and section in {"method", "theory_or_proof"}:
        return "method_quote_for_empirical_claim"
    # 2. pure dataset/setup wording with no concrete empirical outcome.
    if _DATASET_SETUP_RE.search(body) and not has_outcome:
        return "dataset_setup_not_effectiveness"
    # 3. generic intent-to-evaluate with no reported outcome.
    if _GENERIC_EVAL_INTENT_RE.search(body) and not has_outcome:
        return "generic_evaluate_intent"
    return ""


def derive_support_quality(evidence: Dict[str, Any], claim: Dict[str, Any] | None = None, paper_context: str | None = None) -> Dict[str, Any]:
    section = evidence_section_bucket(evidence)
    role = support_role(evidence)
    depth = support_depth(evidence)
    is_empirical_result = section in {"result", "table_or_figure", "ablation"}
    block_reason = _empirical_admission_block_reason(evidence, section, claim)
    is_empirical_admissible = is_empirical_result and not block_reason
    return {
        "evidence_section": section,
        "support_role": role,
        "support_depth": depth,
        "is_abstract_only": section == "abstract",
        "is_non_abstract": section != "abstract",
        "is_method_based": section in {"method", "theory_or_proof"},
        "is_empirical_result": is_empirical_result,
        "is_empirical_admissible": is_empirical_admissible,
        "empirical_admission_block_reason": block_reason,
        "is_table_or_figure_based": section == "table_or_figure",
        "is_ablation_based": section == "ablation",
        "independence_group_id": independence_group_id(evidence),
    }


def _claim_id(claim: Dict[str, Any]) -> str:
    return str(claim.get("claim_id") or "")


def _is_real_claim_for_support_summary(claim_id: str, claim_kind: str = "") -> bool:
    kind = str(claim_kind or "").strip().lower()
    if kind:
        return kind == "paper_extracted"
    value = str(claim_id or "").strip().lower()
    if not value:
        return False
    if value.startswith(("claim-fallback", "fallback", "claim-context", "context", "claim-recovery", "recovery")):
        return False
    return value.startswith("claim-")


def _is_real_strong_support(evidence: Dict[str, Any], claim_id: str, claim_kind: str = "") -> bool:
    binding_status = str(evidence.get("binding_status") or "").strip()
    return (
        _is_real_claim_for_support_summary(claim_id, claim_kind)
        and
        str(evidence.get("claim_id") or "") == claim_id
        and binding_status in {"", "unchecked", "bound_real_claim"}
        and evidence.get("strength") == "strong"
        and evidence.get("stance") in {"supports", "partially_supports"}
    )


def derive_claim_support_summary(claim: Dict[str, Any], evidence_map: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    claim_id = _claim_id(claim)
    claim_kind = str(claim.get("claim_kind") or "")
    qualities = [derive_support_quality(ev, claim) for ev in evidence_map if _is_real_strong_support(ev, claim_id, claim_kind)]
    groups = {q["independence_group_id"] for q in qualities}
    empirical = sum(1 for q in qualities if q.get("is_empirical_admissible"))
    empirical_blocked = sum(
        1 for q in qualities
        if q["is_empirical_result"] and not q.get("is_empirical_admissible")
    )
    method = sum(1 for q in qualities if q["is_method_based"])
    non_abstract = sum(1 for q in qualities if q["is_non_abstract"])
    table_or_figure = sum(1 for q in qualities if q["is_table_or_figure_based"])
    ablation = sum(1 for q in qualities if q["is_ablation_based"])
    has_deep_evidence = any(q["support_depth"] == "deep" for q in qualities)
    # Claim-level depth describes the deepest verified support available for a
    # claim; it is not an accept decision. A single verified result/table/
    # ablation/proof support is already deep evidence, while 2+ independent
    # non-abstract supports also count as deep even when both are method-side.
    if has_deep_evidence or (non_abstract >= 2 and len(groups) >= 2):
        depth = "deep"
    elif non_abstract > 0:
        depth = "moderate"
    elif qualities:
        depth = "shallow"
    else:
        depth = "none"
    return {
        "claim_id": claim_id,
        "claim_real_strong_support_count": len(qualities),
        "claim_non_abstract_support_count": non_abstract,
        "claim_empirical_support_count": empirical,
        "claim_empirical_blocked_count": empirical_blocked,
        "claim_method_support_count": method,
        "claim_table_or_figure_support_count": table_or_figure,
        "claim_ablation_support_count": ablation,
        "claim_independent_support_group_count": len(groups),
        "claim_has_deep_evidence": has_deep_evidence,
        "claim_has_only_abstract_support": bool(qualities) and non_abstract == 0,
        "claim_has_empirical_support": empirical > 0,
        "claim_has_method_plus_result_support": method > 0 and empirical > 0,
        "claim_support_depth_label": depth,
    }


def derive_sample_support_summary(review_state: Dict[str, Any]) -> Dict[str, Any]:
    claims = [c for c in review_state.get("claims", []) or [] if isinstance(c, dict)]
    evidence_map = [e for e in review_state.get("evidence_map", []) or [] if isinstance(e, dict)]
    claim_summaries = [derive_claim_support_summary(claim, evidence_map) for claim in claims]
    return {
        "real_strong_support_total": sum(c["claim_real_strong_support_count"] for c in claim_summaries),
        "nonabstract_support_total": sum(c["claim_non_abstract_support_count"] for c in claim_summaries),
        "empirical_support_total": sum(c["claim_empirical_support_count"] for c in claim_summaries),
        "empirical_blocked_total": sum(c.get("claim_empirical_blocked_count", 0) for c in claim_summaries),
        "method_support_total": sum(c["claim_method_support_count"] for c in claim_summaries),
        "table_or_figure_support_total": sum(c["claim_table_or_figure_support_count"] for c in claim_summaries),
        "ablation_support_total": sum(c["claim_ablation_support_count"] for c in claim_summaries),
        "independent_support_group_total": sum(c["claim_independent_support_group_count"] for c in claim_summaries),
        "claims_with_2plus_independent_support": sum(1 for c in claim_summaries if c["claim_independent_support_group_count"] >= 2),
        "claims_with_only_abstract_support": sum(1 for c in claim_summaries if c["claim_has_only_abstract_support"]),
        "claims_with_empirical_support": sum(1 for c in claim_summaries if c["claim_has_empirical_support"]),
        "claims_with_method_plus_result_support": sum(1 for c in claim_summaries if c["claim_has_method_plus_result_support"]),
        "claim_support_summaries": claim_summaries,
    }
