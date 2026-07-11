import json

from scripts.p34_role_retrieval_audit import build_audit


def test_role_retrieval_audit_reports_nonidentical_roles(tmp_path):
    paper = r"""--- BEGIN PAPER ---
\section{Introduction} We propose a retrieval reranker.
\section{Method} The reranker uses a contrastive objective.
\section{Experiments} Table 2 reports 12.4% higher accuracy than BM25.
\section{Limitations} No multilingual benchmark is evaluated.
--- END PAPER ---"""
    row = {
        "paper_id": "paper-1",
        "review_state": {
            "paper_text": paper,
            "claims": [{"claim_id": "claim-1", "claim": "The reranker improves BM25 accuracy.", "evidence_need": "Table 2."}],
            "evidence_map": [],
            "flaw_candidates": [],
            "evidence_gaps": [],
        },
    }
    path = tmp_path / "input.jsonl"
    path.write_text(json.dumps(row) + "\n")

    report = build_audit(path)

    assert report["paper_count"] == 1
    assert all(report["role_summary"][role]["roundtrip_ok_count"] == 1 for role in ("claim", "evidence", "critique"))
    assert all(report["role_summary"][role]["nonempty_count"] == 1 for role in ("claim", "evidence", "critique"))
