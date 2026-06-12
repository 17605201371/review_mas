# -*- coding: utf-8 -*-
"""R7 case audit generator tests (spec task 11.1)."""
import importlib.util
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# load the script module by path (scripts/ is not a package)
_spec = importlib.util.spec_from_file_location(
    "build_case_audit_v1", str(REPO_ROOT / "scripts" / "build_case_audit_v1.py")
)
cav = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cav)

_post_spec = importlib.util.spec_from_file_location(
    "audit_post4tasks_case_anomalies_v1",
    str(REPO_ROOT / "scripts" / "audit_post4tasks_case_anomalies_v1.py"),
)
post_audit = importlib.util.module_from_spec(_post_spec)
_post_spec.loader.exec_module(post_audit)

BUNDLE_FIELDS = {
    "case_type", "paper_id", "claim", "quote", "locator",
    "positive_evidence", "negative_evidence", "state_transition",
    "final_report_snippet", "audit_flags", "manual_label",
}


def _strong_row():
    return {
        "paper_id": "p-strong",
        "review_state": {
            "paper_id": "p-strong",
            "final_report": "Final report text.",
            "claims": [{"claim_id": "claim-1", "claim_kind": "paper_extracted",
                        "claim": "The method is effective.", "status": "supported"}],
            "evidence_map": [
                {"evidence_id": "evidence-pos-1", "claim_id": "claim-1",
                 "stance": "supports", "strength": "strong",
                 "raw_quote": "Table 2 shows 91% accuracy, outperforming the baseline.",
                 "source": "Results", "source_locator": "Table 2",
                 "verified_grounding_label": "paper_grounded_exact",
                 "semantic_grounding_label": "semantic_support_verified",
                 "binding_status": "bound_real_claim"},
            ],
        },
    }


def test_r7_generate_produces_all_case_types_as_lists():
    result = cav.generate([_strong_row()])
    assert set(result["bundles"].keys()) == set(cav.CASE_TYPES)
    for ct in cav.CASE_TYPES:
        assert isinstance(result["bundles"][ct], list)
    assert result["paper_count"] == 1
    assert result["errors"] == []


def test_r7_bundle_has_all_required_fields_and_empty_label():
    result = cav.generate([_strong_row()])
    assert result["case_counts"]["positive_strong"] >= 1
    b = result["bundles"]["positive_strong"][0]
    assert BUNDLE_FIELDS.issubset(set(b.keys()))
    assert b["manual_label"] == ""  # empty slot for human annotation


def test_r7_no_matching_cases_yields_empty_list_not_error():
    # a row with no real-strong support: dropped/empty types must be [] not missing
    empty_row = {"paper_id": "p-empty", "review_state": {"paper_id": "p-empty", "claims": [], "evidence_map": []}}
    result = cav.generate([empty_row])
    assert result["errors"] == []
    for ct in cav.CASE_TYPES:
        assert result["bundles"][ct] == []


def test_r7_bad_record_is_flagged_and_skipped():
    # review_state is not a dict in a way that breaks downstream -> recorded as error, run continues
    bad_row = {"paper_id": "p-bad", "review_state": {"claims": "not-a-list", "evidence_map": 12345}}
    good_row = _strong_row()
    result = cav.generate([bad_row, good_row])
    # the good row still produced cases; the run did not abort
    assert result["case_counts"]["positive_strong"] >= 1
    # bad row either errored (flagged) or yielded nothing; never aborts
    assert isinstance(result["errors"], list)


def test_r7_is_offline_zero_gpu_pure_function():
    # generate() must not import torch/vllm or call any model; it only reads dicts.
    import sys as _sys
    before = set(_sys.modules.keys())
    cav.generate([_strong_row()])
    after = set(_sys.modules.keys())
    newly = after - before
    assert not any(m.split(".")[0] in {"torch", "vllm"} for m in newly)


def test_post4tasks_case_audit_exports_conflict_semantic_and_mapping_cases():
    row = {
        "paper_id": "p-audit",
        "review_state": {
            "paper_id": "p-audit",
            "state_audit": {
                "decision_hygiene": {
                    "open_conflict_count": 1,
                    "state_contamination_count": 1,
                    "state_contamination_type_counts": {"evidence_misbinding": 1},
                    "state_contamination_targets": [
                        {
                            "target_type": "flaw",
                            "target_id": "flaw-semantic",
                            "error_type": "evidence_misbinding",
                            "evidence_context": "negative_evidence_id_not_verified",
                            "repairability": "conservative",
                        }
                    ],
                    "negative_semantic_anchor_conflict_count": 1,
                    "invalid_negative_evidence_id_count_legacy": 1,
                    "negative_evidence_semantic_rejected_count": 1,
                    "negative_evidence_candidate_count": 1,
                    "verified_negative_flaw_count": 2,
                    "verified_actionable_negative_flaw_count": 2,
                    "potential_concern_count": 2,
                }
            },
            "claims": [
                {
                    "claim_id": "claim-1",
                    "claim": "The method is evaluated with ablations.",
                    "status": "supported",
                    "supporting_evidence_ids": ["e-support"],
                }
            ],
            "evidence_map": [
                {
                    "evidence_id": "e-support",
                    "claim_id": "claim-1",
                    "raw_quote": "The method is evaluated on benchmark X.",
                    "source_locator": "Table 1",
                    "strength": "strong",
                    "stance": "supports",
                    "verified_grounding_label": "paper_grounded_exact",
                    "semantic_grounding_label": "semantic_support_verified",
                },
                {
                    "evidence_id": "e-semantic",
                    "claim_id": "claim-1",
                    "raw_quote": "Table 3 lists ablation experiments.",
                    "source_locator": "Table 3",
                    "strength": "missing",
                    "stance": "missing",
                    "verified_grounding_label": "paper_grounded_exact",
                    "semantic_grounding_label": "semantic_mismatch",
                    "negative_evidence_type": "scope_limitation",
                },
                {
                    "evidence_id": "e-neg",
                    "claim_id": "claim-1",
                    "raw_quote": "The method performs worse than the strongest baseline.",
                    "source_locator": "Table 2",
                    "strength": "strong",
                    "stance": "contradicts",
                    "verified_grounding_label": "paper_grounded_exact",
                    "semantic_grounding_label": "semantic_negative_verified",
                    "negative_evidence_type": "negative_result",
                },
            ],
            "flaw_candidates": [
                {
                    "flaw_id": "flaw-semantic",
                    "status": "candidate",
                    "related_claim_ids": ["claim-1"],
                    "evidence_ids": ["e-semantic"],
                    "negative_evidence_ids": ["e-semantic"],
                },
                {
                    "flaw_id": "flaw-active",
                    "status": "candidate",
                    "related_claim_ids": ["claim-1"],
                    "negative_evidence_ids": ["e-neg"],
                },
                {
                    "flaw_id": "flaw-inactive",
                    "status": "downgraded",
                    "related_claim_ids": ["claim-1"],
                    "negative_evidence_ids": ["e-neg"],
                },
            ],
            "conflict_notes": [
                {
                    "conflict_id": "conflict-support-only",
                    "claim_id": "claim-1",
                    "evidence_id": "e-support",
                    "flaw_id": "flaw-inactive",
                    "conflict_type": "support_only_flaw_without_negative_grounding",
                    "note": "Support-only flaw was downgraded.",
                }
            ],
        },
        "turn_logs": [],
    }

    audit = post_audit.generate([row])

    assert audit["stored_metric_totals"]["open_conflict_count"] == 1
    assert audit["recomputed_metric_totals"]["open_conflict_count"] == 0
    assert audit["stored_metric_totals"]["contamination_evidence_misbinding"] == 1
    assert audit["recomputed_metric_totals"]["contamination_evidence_misbinding"] == 0
    assert audit["p0_1_open_conflict_cases"] == []
    assert audit["p0_3_negative_semantic_anchor_cases"][0]["semantic_label"] == "semantic_mismatch"
    mapping = audit["p0_4_verified_negative_flaw_mapping"]
    assert mapping["current_negative_evidence_candidate_count"] == 1
    assert mapping["current_verified_negative_flaw_count"] == 1


def test_post4tasks_case_audit_does_not_list_historical_conflict_notes_when_clean():
    row = {
        "paper_id": "p-clean-conflict-notes",
        "review_state": {
            "paper_id": "p-clean-conflict-notes",
            "state_audit": {"decision_hygiene": {"open_conflict_count": 0}},
            "claims": [
                {
                    "claim_id": "claim-1",
                    "claim": "The method is effective.",
                    "status": "supported",
                    "supporting_evidence_ids": ["e-support"],
                }
            ],
            "evidence_map": [
                {
                    "evidence_id": "e-support",
                    "claim_id": "claim-1",
                    "raw_quote": "Table 1 reports strong results.",
                    "source_locator": "Table 1",
                    "stance": "supports",
                    "strength": "strong",
                    "verified_grounding_label": "paper_grounded_exact",
                    "semantic_grounding_label": "semantic_support_verified",
                }
            ],
            "flaw_candidates": [],
            "conflict_notes": [
                {
                    "conflict_id": "conflict-historical",
                    "claim_id": "claim-1",
                    "evidence_id": "e-support",
                    "conflict_type": "support_only_flaw_without_negative_grounding",
                    "note": "Historical support-only conflict note retained for traceability.",
                }
            ],
        },
        "turn_logs": [],
    }

    audit = post_audit.generate([row])

    assert audit["stored_metric_totals"]["open_conflict_count"] == 0
    assert audit["recomputed_metric_totals"]["open_conflict_count"] == 0
    assert audit["p0_1_open_conflict_cases"] == []
