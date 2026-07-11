import json

from scripts.p34_annotation_assignment import build_assignment, select_paper_balanced


def _write_template(path, task, papers, per_paper):
    labels = []
    for paper in papers:
        for index in range(per_paper):
            labels.append({
                "packet_id": f"{task}-{paper}-{index}",
                "paper_id": paper,
                "task_type": task,
                "allowed_labels": ["yes", "no"],
            })
    path.write_text(json.dumps({"labels": labels}))
    return labels


def test_selection_is_deterministic_and_maximizes_paper_coverage():
    rows = [
        {"packet_id": f"p{paper}-{index}", "paper_id": f"p{paper}"}
        for paper in range(5)
        for index in range(4)
    ]

    first = select_paper_balanced(rows, 7, "seed", "task")
    second = select_paper_balanced(list(reversed(rows)), 7, "seed", "task")

    assert first == second
    assert len(first) == 7
    assert len({packet_id.split("-")[0] for packet_id in first}) == 5


def test_assignment_freezes_exact_secondary_ids_and_template_hashes(tmp_path):
    positive, claim, negative = tmp_path / "positive.json", tmp_path / "claim.json", tmp_path / "negative.json"
    _write_template(positive, "evidence_relation", ["p1", "p2", "p3"], 3)
    _write_template(claim, "claim_faithfulness", ["p1", "p2"], 3)
    _write_template(negative, "review_issue", ["p1", "p2", "p3", "p4"], 2)

    report = build_assignment(
        {"evidence_relation": positive, "claim_faithfulness": claim, "review_issue": negative},
        {"evidence_relation": 5, "claim_faithfulness": 4, "review_issue": 6},
        "frozen-seed",
    )

    assert report["status"] == "PASS"
    assert report["tasks"]["evidence_relation"]["secondary_packet_count"] == 5
    assert report["tasks"]["evidence_relation"]["secondary_paper_count"] == 3
    assert len(report["assignment_sha256"]) == 64
    assert all(len(value["template_sha256"]) == 64 for value in report["tasks"].values())


def test_assignment_blocks_when_a_task_cannot_meet_minimum(tmp_path):
    paths = {task: tmp_path / f"{task}.json" for task in ("evidence_relation", "claim_faithfulness", "review_issue")}
    for task, path in paths.items():
        _write_template(path, task, ["p1"], 1 if task == "review_issue" else 3)

    report = build_assignment(paths, {"evidence_relation": 2, "claim_faithfulness": 2, "review_issue": 2}, "seed")

    assert report["status"] == "BLOCKED"
    assert "review_issue:secondary_assignment_below_minimum:1/2" in report["blocking_issues"]
