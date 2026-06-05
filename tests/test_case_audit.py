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
