"""Red-line regression tests: author self-limitations must never be counted as
reviewer-discovered verified negatives, genuine negatives must still pass, and
raw-salvaged claims that are not locatable in the paper must not host negatives.

Covers the 2026-06-19 fixes:
  * Fix#1  _assess_review_negative_relation author-limitation short-circuit
  * Fix#3  canonicalized raw-salvage claim must be paper-text locatable to host
           a counted negative (_salvage_negative_blocked_by_unlocatable_claim)
"""

from __future__ import annotations

from agent_system.environments.env_package.review import state as S

REAL_CLAIM_ID = "claim-baseline-coverage"
CLAIM_TEXT = "Our method outperforms all baselines across diverse benchmark datasets."


def _negative_evidence(
    raw_quote: str,
    negative_evidence_type: str,
    *,
    source: str = "Section 5 Experiments",
    claim_id: str = REAL_CLAIM_ID,
):
    return {
        "evidence_id": "evidence-neg-1",
        "claim_id": claim_id,
        "raw_quote": raw_quote,
        "agent_raw_quote": raw_quote,
        "evidence": raw_quote,
        "negative_evidence_type": negative_evidence_type,
        "stance": "missing",
        "strength": "missing",
        "verified_grounding_label": "paper_grounded_exact",
        "verified_quote_match_type": "quote_bank_raw_canonical",
        "verified_source_span_start": 10,
        "verified_source_span_end": 90,
        "semantic_grounding_label": "semantic_negative_verified",
        "source": source,
        "source_locator": source,
    }


def _state(evidence, *, claim=None, paper_text=""):
    claim = claim or {
        "claim_id": REAL_CLAIM_ID,
        "claim": CLAIM_TEXT,
        "status": "supported",
        "claim_kind": "paper_extracted",
    }
    return {
        "paper_id": "P1",
        "claims": [claim],
        "evidence_map": [evidence],
        "evidence_quote_bank": [{"quote_id": "q1", "raw_quote": evidence["raw_quote"]}],
        "paper_text": paper_text,
    }


# --- Fix#1: author self-limitations are not reviewer-discovered negatives ---

def test_author_self_limitation_not_verified_negative():
    ev = _negative_evidence(
        "Note that we do not evaluate the quality of the output in this work.",
        "insufficient_evaluation",
        source="Section 6 Limitations",
    )
    st = _state(ev)
    assert S._assess_review_negative_relation(st, ev)["review_negative_label"] == "author_limitation_only"
    assert S._is_grounded_paper_negative_evidence_record(ev, st) is False


def test_author_dps_limitation_not_verified_negative():
    ev = _negative_evidence(
        "A limitation of our method is the DPS approximation used during sampling.",
        "method_support_gap",
        source="Section 6 Limitations",
    )
    st = _state(ev)
    assert S._assess_review_negative_relation(st, ev)["review_negative_label"] == "author_limitation_only"
    assert S._is_grounded_paper_negative_evidence_record(ev, st) is False


def test_future_work_not_verified_negative():
    ev = _negative_evidence(
        "We leave evaluation on out-of-domain data to future work.",
        "insufficient_evaluation",
        source="Section 7 Conclusion",
    )
    st = _state(ev)
    assert S._assess_review_negative_relation(st, ev)["review_negative_label"] == "author_limitation_only"
    assert S._is_grounded_paper_negative_evidence_record(ev, st) is False


# --- Fix#1 must not over-correct: genuine reviewer negatives still pass ---

def test_genuine_missing_baseline_still_grounded():
    ev = _negative_evidence(
        "We compare only against method A; method B is not included in our experiments.",
        "missing_baseline",
    )
    st = _state(ev)
    assert S._assess_review_negative_relation(st, ev)["review_negative_label"] == "review_negative_verified"
    assert S._is_grounded_paper_negative_evidence_record(ev, st) is True


# --- Codex-audit fix: problem-motivation / addressed-by-our-method is NOT a
#     reviewer-discovered negative. A first-person difficulty observed under the
#     paper's OWN method/setting (which the paper then solves) must not auto-verify,
#     but the guard must not block genuine negative results. ---

def test_problem_motivation_under_own_method_not_verified_negative():
    ev = _negative_evidence(
        "Worse yet, we found increased data heterogeneity among clients when "
        "federatively training with our distilled local virtual data.",
        "negative_result",
        source="Section 3 Method",
    )
    st = _state(ev)
    assessment = S._assess_review_negative_relation(st, ev)
    assert assessment["review_negative_label"] == "author_limitation_only"
    assert assessment["review_negative_reason"] == "negative_result_is_problem_motivation_addressed_by_method"
    assert S._is_grounded_paper_negative_evidence_record(ev, st) is False


def test_problem_motivation_guard_does_not_block_genuine_negative_result():
    ev = _negative_evidence(
        "Relying solely on detection as a pre-training task yields minimal performance gains.",
        "negative_result",
    )
    st = _state(ev)
    assert S._assess_review_negative_relation(st, ev)["review_negative_label"] == "review_negative_verified"
    assert S._is_grounded_paper_negative_evidence_record(ev, st) is True


# --- Codex-audit fix (2): related-work criticism of a CITED prior work
#     (\cite{x2024} ... does not compare ...) is a prior_work_limitation, not a
#     verified negative against THIS paper; a real own-paper gap must still verify. ---

def test_prior_work_cite_criticism_not_verified_negative():
    ev = _negative_evidence(
        r"\cite{templeton2024scaling} on the other hand only provides a qualitative "
        r"evaluation and does not compare to other interpretability methods.",
        "missing_baseline",
        source="Section 2 Related Work",
    )
    st = _state(ev)
    assessment = S._assess_review_negative_relation(st, ev)
    assert assessment["review_negative_label"] == "prior_work_limitation"
    assert assessment["review_negative_reason"] == "quote_describes_prior_or_external_work"
    assert S._is_grounded_paper_negative_evidence_record(ev, st) is False


# --- Fix#3: raw-salvaged claim must be locatable in the paper to host a negative ---

def _salvage_claim(claim_text):
    return {
        "claim_id": REAL_CLAIM_ID,
        "claim": claim_text,
        "status": "supported",
        "claim_kind": "paper_extracted",
        "claim_origin_kind": "raw_salvaged_claim_agent_output",
        "paper_claim_canonicalized_from_raw_salvage": True,
    }


def test_salvage_claim_negative_blocked_when_not_locatable():
    claim_text = "The proposed contrastive diffuser plans toward high-return states."
    ev = _negative_evidence(
        "We compare only against method A; method B is not included in our experiments.",
        "missing_baseline",
    )
    st = _state(
        ev,
        claim=_salvage_claim(claim_text),
        paper_text="This paper studies offline reinforcement learning with uncertainty estimation only.",
    )
    # claim content words are absent from paper_text -> salvage claim cannot host a counted negative
    assert S._is_grounded_paper_negative_evidence_record(ev, st) is False


def test_salvage_claim_negative_allowed_when_locatable():
    claim_text = "The proposed contrastive diffuser plans toward high-return states."
    ev = _negative_evidence(
        "We compare only against method A; method B is not included in our experiments.",
        "missing_baseline",
    )
    paper = (
        "We propose a contrastive diffuser that plans toward high-return states "
        "using contrastive learning over offline trajectories."
    )
    st = _state(ev, claim=_salvage_claim(claim_text), paper_text=paper)
    assert S._is_grounded_paper_negative_evidence_record(ev, st) is True


def test_salvage_gate_inert_offline_without_paper_text():
    # Offline recompute (paper_text stripped) keeps prior behaviour: gate does not fire.
    claim_text = "Totally unrelated hallucinated salvage claim about quantum widgets."
    ev = _negative_evidence(
        "We compare only against method A; method B is not included in our experiments.",
        "missing_baseline",
    )
    st = _state(ev, claim=_salvage_claim(claim_text), paper_text="")
    assert S._is_grounded_paper_negative_evidence_record(ev, st) is True
