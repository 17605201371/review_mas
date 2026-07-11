import hashlib

from scripts.p34_annotation_server import AnnotationStore
from scripts.p34_translate_audit_paper import _batches, collect_display_strings


def test_collect_display_strings_deduplicates_visible_content():
    packet = {
        "claim": {"claim_text": "A claim"},
        "candidate_evidence": {"quote": "Evidence quote"},
        "counterevidence_candidates": [{"quote": "Evidence quote"}, {"quote": "Counter quote"}],
    }
    values = collect_display_strings(
        "p1",
        {"positive-p1-1": packet},
        {
            "evidence_relation": {"labels": [{"paper_id": "p1", "packet_id": "positive-p1-1"}]},
            "claim_faithfulness": {"labels": []},
            "review_issue": {"labels": []},
        },
        {"cases": [{
            "paper_id": "p1",
            "machine_boundary_suggestions": [{"heading": "Introduction", "text_preview": "Preview"}],
            "machine_anchor_suggestions": [],
            "machine_false_boundary_suggestions": [],
        }]},
    )

    assert values == ["A claim", "Evidence quote", "Counter quote", "Introduction", "Preview"]


def test_translation_batches_preserve_order_and_limits():
    values = ["a" * 4, "b" * 4, "c" * 4]
    batches = _batches(values, max_chars=8, max_items=2)

    assert batches == [[("t0001", "a" * 4), ("t0002", "b" * 4)], [("t0003", "c" * 4)]]


def test_display_translation_is_hash_addressed_and_does_not_mutate_source():
    store = AnnotationStore.__new__(AnnotationStore)
    source = "The original English claim."
    store._translations_by_hash = {hashlib.sha256(source.encode()).hexdigest(): "原始英文主张。"}
    packet = {"claim": {"claim_text": source}, "packet_id": "unchanged-id"}

    translated = store._display_translate(packet)

    assert translated["claim"]["claim_text"] == "原始英文主张。"
    assert translated["packet_id"] == "unchanged-id"
    assert packet["claim"]["claim_text"] == source


def test_pilot_lookup_returns_copy_and_never_creates_formal_label():
    store = AnnotationStore.__new__(AnnotationStore)
    store._pilot_tasks = {"review_issue": {"packet-1": {"suggested_label": "B", "reason_zh": "理由"}}}

    pilot = store._pilot_for("review_issue", "packet-1")
    pilot["suggested_label"] = "D"

    assert store._pilot_tasks["review_issue"]["packet-1"]["suggested_label"] == "B"
    assert "human_label" not in store._pilot_tasks["review_issue"]["packet-1"]
