import json

from agent_system.environments.env_package.review.paper_index import build_paper_index
from scripts.p34_paper_index_audit import _anchor_match, _boundary_match, _score_annotations, build_report, write_annotation_template


def test_human_boundary_and_anchor_scoring_uses_original_spans():
    paper = r"""\section{Method}
The reranker uses contrastive learning.
\section{Experiments}
Table 1 compares the reranker against BM25 on BenchX.
"""
    index = build_paper_index(paper)
    experiments = next(item for item in index.sections if item.section_type == "results")
    boundary = {"heading": "Experiments", "section_type": "results", "source_span_start": experiments.source_span_start}
    anchor = {"query": "reranker BM25 BenchX", "text": "Table 1 compares the reranker against BM25"}

    assert _boundary_match(index, boundary, tolerance=0) is True
    assert _anchor_match(index, anchor) is True


def test_annotation_score_does_not_treat_missing_labels_as_pass():
    index = build_paper_index("# Method\nBody")
    score = _score_annotations(index, {}, tolerance=8)

    assert score == {
        "expected_boundary_count": 0,
        "expected_boundary_hit_count": 0,
        "key_anchor_count": 0,
        "key_anchor_hit_count": 0,
        "labeled_false_boundary_count": 0,
        "labeled_false_boundary_hit_count": 0,
    }


def test_annotation_template_separates_machine_suggestions_from_human_labels(tmp_path):
    report = {
        "dataset_sha256": "abc",
        "cases": [
            {
                "paper_id": "paper-1",
                "sections": [
                    {
                        "heading": "Method",
                        "section_type": "method",
                        "source_span_start": 10,
                        "source_span_end": 100,
                        "parser_mode": "latex",
                        "confidence": 0.99,
                        "text_preview": "Method text",
                    }
                ],
                "artifacts": [
                    {
                        "artifact_type": "caption",
                        "locator": "Table 1",
                        "source_span_start": 60,
                        "source_span_end": 80,
                        "text_preview": "Table 1: Accuracy",
                    }
                ],
            }
        ],
    }
    path = tmp_path / "anchors.json"

    write_annotation_template(report, path)
    value = json.loads(path.read_text())

    assert value["machine_suggestions_are_not_labels"] is True
    assert value["cases"][0]["expected_boundaries"] == []
    assert value["cases"][0]["machine_boundary_suggestions"][0]["heading"] == "Method"
    assert value["cases"][0]["machine_anchor_suggestions"][0]["query"] == "Table 1"
    suggestion = value["cases"][0]["machine_anchor_suggestions"][0]
    assert suggestion["source_span_end"] == suggestion["source_span_start"] + len(suggestion["text"])


def test_template_rows_do_not_count_as_completed_human_annotations(tmp_path, monkeypatch):
    dataset = tmp_path / "papers.jsonl"
    dataset.write_text("placeholder\n")
    annotations = tmp_path / "anchors.json"
    annotations.write_text(json.dumps({
        "cases": [{
            "paper_id": "paper-1",
            "expected_boundaries": [],
            "key_anchors": [],
            "false_boundaries": [],
            "human_review_complete": False,
        }]
    }))
    monkeypatch.setattr(
        "scripts.p34_paper_index_audit.load_review_rows",
        lambda _path, limit=None: [{"id": "paper-1", "inputs": "# Method\nBody"}],
    )

    report = build_report(dataset, annotations, limit=None, tolerance=8)

    assert report["annotated_paper_count"] == 1
    assert report["completed_annotation_count"] == 0
    assert report["gates"]["all_papers_annotated"] is False
    assert report["status"] == "NEEDS_MANUAL_ANCHORS"
    assert report["false_boundary_rate"] is None


def test_completed_review_with_explicit_zero_false_boundaries_can_pass(tmp_path, monkeypatch):
    paper = "# Method\nThe reranker uses contrastive learning.\n# Experiments\nTable 1 compares BM25 accuracy."
    index = build_paper_index(paper)
    method = next(item for item in index.sections if item.section_type == "method")
    dataset = tmp_path / "papers.jsonl"
    dataset.write_text("placeholder\n")
    annotations = tmp_path / "anchors.json"
    annotations.write_text(json.dumps({"cases": [{
        "paper_id": "paper-1",
        "expected_boundaries": [{
            "heading": "Method", "section_type": "method", "source_span_start": method.source_span_start,
        }],
        "key_anchors": [{"query": "reranker contrastive learning", "text": "reranker uses contrastive learning"}],
        "false_boundaries": [],
        "human_review_complete": True,
    }]}))
    monkeypatch.setattr(
        "scripts.p34_paper_index_audit.load_review_rows",
        lambda _path, limit=None: [{"id": "paper-1", "inputs": paper}],
    )

    report = build_report(dataset, annotations, limit=None, tolerance=8)

    assert report["status"] == "PASS"
    assert report["false_boundary_rate"] == 0.0
    assert report["gates"]["false_section_boundary_rate_lte_0_10"] is True


def test_completed_review_still_fails_when_labeled_false_boundary_is_parsed(tmp_path, monkeypatch):
    paper = "# Method\nThe reranker uses contrastive learning.\n# References\nCitation list."
    index = build_paper_index(paper)
    method = next(item for item in index.sections if item.section_type == "method")
    references = next(item for item in index.sections if item.heading == "References")
    dataset = tmp_path / "papers.jsonl"
    dataset.write_text("placeholder\n")
    annotations = tmp_path / "anchors.json"
    annotations.write_text(json.dumps({"cases": [{
        "paper_id": "paper-1",
        "expected_boundaries": [{
            "heading": "Method", "section_type": "method", "source_span_start": method.source_span_start,
        }],
        "key_anchors": [{"query": "reranker contrastive learning", "text": "reranker uses contrastive learning"}],
        "false_boundaries": [{
            "heading": "References", "section_type": references.section_type,
            "source_span_start": references.source_span_start, "reason": "Human marked this as non-section noise.",
        }],
        "human_review_complete": True,
    }]}))
    monkeypatch.setattr(
        "scripts.p34_paper_index_audit.load_review_rows",
        lambda _path, limit=None: [{"id": "paper-1", "inputs": paper}],
    )

    report = build_report(dataset, annotations, limit=None, tolerance=8)

    assert report["status"] == "FAIL"
    assert report["false_boundary_rate"] == 1.0
    assert report["gates"]["false_section_boundary_rate_lte_0_10"] is False
