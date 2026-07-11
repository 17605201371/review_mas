import json

from scripts.p34_field_authority_audit import build_audit


def test_authority_audit_uses_raw_payload_and_ignores_empty_schema_fields(tmp_path):
    row = {
        "paper_id": "paper-1",
        "runner_trace": [
            {
                "turn_id": 1,
                "manager_raw": json.dumps({
                    "decision": "continue",
                    "selected_agents": ["Claim Agent"],
                    "claims": [],
                    "flaw_candidates": [{"flaw_id": "f1", "description": "Injected flaw"}],
                }),
                "worker_calls": [
                    {
                        "agent_id": "Claim Agent",
                        "raw": json.dumps({
                            "claims": [{"claim_id": "c1", "claim": "Claim", "status": "supported"}],
                            "evidence_map": [],
                        }),
                    }
                ],
            }
        ],
    }
    path = tmp_path / "runner.jsonl"
    path.write_text(json.dumps(row) + "\n")

    report = build_audit(path)

    assert report["parse_error_count"] == 0
    assert report["effective_violation_payload_count"] == 2
    assert report["effective_violation_counts"]["manager:flaw_candidates"] == 1
    assert report["effective_violation_counts"]["claim:claims[0].status"] == 1
    assert "manager:claims" in report["declared_violation_counts"]
    assert "manager:claims" not in report["effective_violation_counts"]
    assert report["effective_violation_category_counts"]["entity_owner_violation"] == 1
