import argparse
import importlib.util
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def _load_script_module(name, relative_path):
    spec = importlib.util.spec_from_file_location(name, REPO_ROOT / relative_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


p31_gate = _load_script_module("p31_6_entry_gate_audit", "scripts/p31_6_entry_gate_audit.py")
p31_manual = _load_script_module("p31_6_manual_audit", "scripts/p31_6_manual_audit.py")
p31_status = _load_script_module("p31_6_status_report", "scripts/p31_6_status_report.py")
p32_stability = _load_script_module("p32_stability_report", "scripts/p32_stability_report.py")


def _write_json(path, data):
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return path


def _dashboard(path, critique_clusters=3, protection_passed=True):
    return _write_json(
        path,
        {
            "candidate": {
                "metrics": {
                    "verified_review_issue_count": critique_clusters,
                    "verified_review_issue_cluster_count": critique_clusters,
                    "duplicate_review_issue_row_count": 0,
                    "verified_review_issue_cluster_recomputed_count": critique_clusters,
                    "quote_duplicate_merged_verified_review_issue_cluster_count": critique_clusters,
                    "critique_payload_verified_cluster_count": critique_clusters,
                    "critique_direct_verified_cluster_count": critique_clusters,
                    "critique_selected_existing_seed_cluster_count": 0,
                    "candidate_menu_item_verified_count": critique_clusters,
                    "verified_review_issue_cluster_origin_critique_payload_count": critique_clusters,
                    "verified_review_issue_cluster_origin_deterministic_seed_count": 0,
                    "verified_review_issue_cluster_origin_claim_obligation_fallback_count": 0,
                    "verified_review_issue_cluster_origin_direct_quote_count": 0,
                    "verified_review_issue_cluster_origin_other_candidate_count": 0,
                    "verified_review_issue_cluster_origin_other_count": 0,
                    "negative_evidence_unlinked_to_flaw": 0,
                    "positive_or_neutral_negative_candidate_count": 0,
                    "negative_grounding_conflict_count": 0,
                    "mark_contested_commit_count": 1,
                    "verified_issue_cluster_without_recovery_count": 0,
                }
            },
            "protection_passed": protection_passed,
        },
    )


def _case_table(path, cluster_count=3):
    cases = []
    for idx in range(cluster_count):
        paper_id = f"paper-{idx}"
        target = f"target-{idx}"
        cases.append(
            {
                "paper_id": paper_id,
                "issue_type": "reproducibility_gap",
                "claim_id": "claim-1",
                "reviewer_candidate_kind": "critique_payload_candidate",
                "discovery_origin": "freeform_reviewer_negative",
                "reviewer_candidate_id": f"review-issue-candidate-{idx}",
                "missing_or_mismatch": target,
                "claim_anchor": f"claim anchor {idx}",
                "inventory_or_quote_locator": "Section 4",
                "inventory_or_quote": f"inventory quote {idx}",
                "issue_cluster_key": f"{paper_id}|obligation_grounded_review_issue|reproducibility_gap|{target}",
                "issue_cluster_target": target,
            }
        )
    return _write_json(
        path,
        {
            "summary": {
                "verified_review_issue_cases": len(cases),
                "verified_review_issue_cluster_count": cluster_count,
                "duplicate_review_issue_row_count": 0,
            },
            "cases": cases,
        },
    )


def _recovery_table(path):
    return _write_json(path, {"summary": {}, "cases": []})


def _manual_validation(path, *, label="TEST", labels=None, origins=None):
    labels = labels or ["A", "B", "B"]
    origins = origins or ["critique_payload", "critique_payload", "quote_grounded"]
    clusters = []
    for idx, manual_label in enumerate(labels):
        origin = origins[idx] if idx < len(origins) else "critique_payload"
        clusters.append(
            {
                "label": manual_label,
                "paper_id": f"paper-{idx}",
                "issue_type": "reproducibility_gap",
                "target_entity": f"target-{idx}",
                "cluster_target": f"target-{idx}",
                "issue_cluster_key": f"paper-{idx}|obligation_grounded_review_issue|reproducibility_gap|target-{idx}",
                "origin": origin,
                "claim_ids": ["claim-1"],
                "manual_decision": "keep",
                "raw_paper_evidence_checked": "yes",
                "counterevidence_checked": "yes",
                "paper_facing_usable": "yes",
                "reason": "Defensible claim/inventory/missing relation.",
            }
        )
    ab_count = sum(1 for item in clusters if item["label"] in {"A", "B"})
    d_count = sum(1 for item in clusters if item["label"] == "D")
    critique_ab = sum(1 for item in clusters if item["label"] in {"A", "B"} and item["origin"] == "critique_payload")
    return _write_json(
        path,
        {
            "run_label": label,
            "summary": {
                "system_clusters": len(clusters),
                "critique_origin_clusters": sum(1 for item in clusters if item["origin"] == "critique_payload"),
                "manual_A_clusters": sum(1 for item in clusters if item["label"] == "A"),
                "manual_B_clusters": sum(1 for item in clusters if item["label"] == "B"),
                "manual_A_B_clusters": ab_count,
                "manual_C_clusters": sum(1 for item in clusters if item["label"] == "C"),
                "manual_D_clusters": d_count,
                "unfilled_clusters": 0,
                "critique_origin_manual_A_B_clusters": critique_ab,
                "deterministic_seed_manual_A_B_clusters": 0,
                "status": "PASS" if d_count == 0 else "FAIL",
            },
            "clusters": clusters,
        },
    )


def _entry_gate(path, *, critique_clusters=3, manual_status="PASS"):
    return _write_json(
        path,
        {
            "machine_gate_status": "PASS",
            "manual_gate_status": "PASS" if manual_status == "PASS" else "FAIL",
            "blocking_issues": [],
            "headline_metrics": {
                "critique_direct_verified_cluster_count": critique_clusters,
                "candidate_menu_item_verified_count": critique_clusters,
                "mark_contested_commit_count": 2,
                "verified_issue_cluster_without_recovery_count": 0,
            },
            "manual_audit_summary": {
                "status": manual_status,
                "manual_A_B_clusters": critique_clusters,
                "manual_D_clusters": 0,
                "unfilled_clusters": 0,
                "critique_origin_manual_A_B_clusters": critique_clusters,
            },
        },
    )


def _dashboard_for_stability(path, raw_path, *, critique_clusters=3, protection_passed=True):
    payload = json.loads(_dashboard(path, critique_clusters=critique_clusters, protection_passed=protection_passed).read_text(encoding="utf-8"))
    payload["candidate"]["path"] = str(raw_path)
    payload["candidate"]["metrics"]["paper_count"] = 20
    payload["candidate"]["metrics"]["evidence_json_fallback_rate_pct"] = 0
    payload["candidate"]["metrics"]["state_contamination_count"] = 0
    payload["candidate"]["metrics"]["semantic_negative_without_review_relation_count"] = 0
    payload["candidate"]["metrics"]["recovery_harmful_commit_committed"] = 0
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _write_stability_artifacts(tmp_path, label, *, rows=20, labels=None):
    raw = tmp_path / f"{label}.jsonl"
    raw.write_text("\n".join("{}" for _ in range(rows)) + ("\n" if rows else ""), encoding="utf-8")
    _entry_gate(tmp_path / f"{label}_ENTRY_GATE_AUDIT.json", critique_clusters=3)
    _case_table(tmp_path / f"{label}_REVIEW_ISSUE_CASE_TABLE.json", cluster_count=3)
    _recovery_table(tmp_path / f"{label}_RECOVERY_CASE_TABLE.json")
    _dashboard_for_stability(tmp_path / f"{label}_HARDNEG20_DASHBOARD.json", raw, critique_clusters=3)
    _manual_validation(tmp_path / f"{label}_MANUAL_AUDIT_VALIDATION.json", label=label, labels=labels)
    return raw


def test_entry_gate_fails_when_critique_origin_cluster_count_below_threshold(tmp_path):
    dashboard = _dashboard(tmp_path / "dashboard.json", critique_clusters=2)
    case_table = _case_table(tmp_path / "cases.json", cluster_count=2)
    recovery = _recovery_table(tmp_path / "recovery.json")

    report, exit_code = p31_gate.build_report(
        argparse.Namespace(
            dashboard_json=str(dashboard),
            case_json=str(case_table),
            recovery_json=str(recovery),
            manual_audit_validation_json="",
            output_json="",
            output_md="",
            min_critique_clusters=3,
            min_candidate_menu_verified=2,
            fail_on_red_flags=False,
            require_manual_audit=False,
        )
    )

    assert exit_code == 1
    assert report["machine_gate_status"] == "FAIL"
    assert report["manual_gate_status"] == "REQUIRED"
    assert len(report["critique_origin_clusters"]) == 2
    assert any("critique_direct_verified_cluster_count" in issue for issue in report["blocking_issues"])


def test_manual_audit_template_and_validation_pass_for_three_ab_clusters(tmp_path):
    entry_gate = _write_json(
        tmp_path / "entry_gate.json",
        {
            "critique_origin_clusters": [
                {
                    "paper_id": f"paper-{idx}",
                    "issue_type": "reproducibility_gap",
                    "issue_cluster_target": f"target-{idx}",
                    "issue_cluster_key": f"cluster-{idx}",
                    "claim_ids": ["claim-1"],
                    "missing_or_mismatch": f"target-{idx}",
                    "claim_anchor": f"claim anchor {idx}",
                    "inventory_or_quote_locator": "Section 4",
                    "inventory_or_quote": f"inventory quote {idx}",
                    "discovery_origin": "freeform_reviewer_negative",
                }
                for idx in range(3)
            ]
        },
    )
    template = p31_manual._build_template(
        argparse.Namespace(
            entry_gate_json=str(entry_gate),
            run_label="TEST",
            audit_date="2026-07-03",
            min_critique_ab_clusters=3,
        )
    )
    assert len(template["clusters"]) == 3
    assert template["summary"]["status"] == "TODO"

    for idx, cluster in enumerate(template["clusters"]):
        cluster["label"] = "A" if idx == 0 else "B"
        cluster["manual_decision"] = "keep"
        cluster["raw_paper_evidence_checked"] = "yes"
        cluster["counterevidence_checked"] = "yes"
        cluster["paper_facing_usable"] = "yes"
        cluster["reason"] = "Defensible claim/inventory/missing relation."

    audit_path = _write_json(tmp_path / "manual_audit.json", template)
    report, exit_code = p31_manual._validate_audit(
        argparse.Namespace(
            audit_json=str(audit_path),
            output_json="",
            output_md="",
            min_critique_ab_clusters=3,
            min_all_ab_clusters=0,
            allow_d=False,
        )
    )

    assert exit_code == 0
    assert report["summary"]["status"] == "PASS"
    assert report["summary"]["manual_A_B_clusters"] == 3
    assert report["summary"]["manual_D_clusters"] == 0
    assert report["summary"]["unfilled_clusters"] == 0


def test_manual_audit_template_from_case_table_includes_all_system_clusters(tmp_path):
    case_table = _case_table(tmp_path / "cases.json", cluster_count=3)
    payload = json.loads(case_table.read_text(encoding="utf-8"))
    payload["cases"].append(
        {
            **payload["cases"][0],
            "paper_id": "paper-seed",
            "reviewer_candidate_kind": "deterministic_reviewer_seed",
            "discovery_origin": "deterministic_component_ablation_seed",
            "issue_cluster_key": "paper-seed|obligation_grounded_review_issue|missing_ablation|seed-target",
            "issue_cluster_target": "seed-target",
            "missing_or_mismatch": "seed-target",
        }
    )
    case_table.write_text(json.dumps(payload), encoding="utf-8")

    template = p31_manual._build_template(
        argparse.Namespace(
            entry_gate_json="",
            case_json=str(case_table),
            critique_origin_only=False,
            run_label="TEST",
            audit_date="2026-07-03",
            min_critique_ab_clusters=3,
            min_all_ab_clusters=0,
        )
    )

    assert len(template["clusters"]) == 4
    origins = {cluster["origin"] for cluster in template["clusters"]}
    assert {"critique_payload", "deterministic_seed"} <= origins
    assert template["summary"]["system_clusters"] == 4
    assert template["summary"]["critique_origin_clusters"] == 3


def test_entry_gate_consumes_manual_validation_report(tmp_path):
    dashboard = _dashboard(tmp_path / "dashboard.json", critique_clusters=3)
    case_table = _case_table(tmp_path / "cases.json", cluster_count=3)
    recovery = _recovery_table(tmp_path / "recovery.json")
    manual_validation = _write_json(
        tmp_path / "manual_validation.json",
        {
            "summary": {
                "status": "PASS",
                "manual_A_B_clusters": 3,
                "manual_D_clusters": 0,
                "unfilled_clusters": 0,
            }
        },
    )

    report, exit_code = p31_gate.build_report(
        argparse.Namespace(
            dashboard_json=str(dashboard),
            case_json=str(case_table),
            recovery_json=str(recovery),
            manual_audit_validation_json=str(manual_validation),
            output_json="",
            output_md="",
            min_critique_clusters=3,
            min_candidate_menu_verified=2,
            fail_on_red_flags=False,
            require_manual_audit=True,
        )
    )

    assert exit_code == 0
    assert report["machine_gate_status"] == "PASS"
    assert report["manual_gate_status"] == "PASS"
    assert report["manual_audit_summary"]["manual_A_B_clusters"] == 3


def test_status_report_summarizes_ready_gate_without_api_preflight(tmp_path):
    run_base = tmp_path / "run"
    (tmp_path / "run.jsonl").write_text("\n".join("{}" for _ in range(20)) + "\n", encoding="utf-8")
    entry_gate = _write_json(
        tmp_path / "entry_gate.json",
        {
            "machine_gate_status": "PASS",
            "manual_gate_status": "PASS",
            "blocking_issues": [],
            "headline_metrics": {
                "verified_review_issue_count": 3,
                "verified_review_issue_cluster_recomputed_count": 3,
                "quote_duplicate_merged_verified_review_issue_cluster_count": 3,
                "critique_payload_verified_cluster_count": 3,
                "verified_review_issue_cluster_origin_critique_payload_count": 3,
                "mark_contested_commit_count": 1,
            },
            "manual_audit_summary": {
                "status": "PASS",
                "manual_A_B_clusters": 3,
                "manual_D_clusters": 0,
                "unfilled_clusters": 0,
            },
        },
    )
    manual_validation = _write_json(
        tmp_path / "manual_validation.json",
        {
            "summary": {
                "status": "PASS",
                "manual_A_B_clusters": 3,
                "manual_D_clusters": 0,
                "unfilled_clusters": 0,
            }
        },
    )

    report = p31_status.build_report(
        argparse.Namespace(
            run_base=str(run_base),
            entry_gate_json=str(entry_gate),
            manual_validation_json=str(manual_validation),
            api_preflight=False,
            output_json="",
            output_md="",
        )
    )

    assert report["p32_entry_ready"] is True
    assert report["latest_run"]["jsonl_lines"] == 20
    assert report["api_preflight"]["status"] == "not_run"
    assert "P32 review" in report["next_action"]


def test_status_report_explicit_entry_gate_does_not_use_default_manual_validation(tmp_path, monkeypatch):
    run_base = tmp_path / "run"
    (tmp_path / "run.jsonl").write_text("\n".join("{}" for _ in range(20)) + "\n", encoding="utf-8")
    entry_gate = _write_json(
        tmp_path / "entry_gate.json",
        {
            "machine_gate_status": "PASS",
            "manual_gate_status": "REQUIRED",
            "blocking_issues": [],
            "headline_metrics": {"critique_payload_verified_cluster_count": 3},
        },
    )
    _write_json(
        tmp_path / p31_status.DEFAULT_MANUAL_VALIDATION,
        {"summary": {"status": "PASS", "manual_A_B_clusters": 99}},
    )
    monkeypatch.chdir(tmp_path)

    report = p31_status.build_report(
        argparse.Namespace(
            run_base=str(run_base),
            entry_gate_json=str(entry_gate),
            manual_validation_json="",
            api_preflight=False,
            output_json="",
            output_md="",
        )
    )

    assert report["manual_validation"]["exists"] is False
    assert report["manual_validation"]["summary"] == {}
    assert report["entry_gate"]["manual_gate_status"] == "REQUIRED"


def test_p32_stability_report_excludes_partial_runs(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    raw = _write_stability_artifacts(tmp_path, "P32_PARTIAL", rows=16)

    report = p32_stability.build_report(
        argparse.Namespace(
            run=[f"P32_PARTIAL={raw.with_suffix('')}"],
            min_runs=3,
            min_rows=20,
            max_d_rate=0.25,
        )
    )

    assert report["status"] == "BLOCKED"
    assert report["runs_included"] == 0
    assert report["runs_excluded"] == 1
    assert report["runs"][0]["jsonl_rows"] == 16
    assert any("jsonl rows 16 < required 20" in issue for issue in report["runs"][0]["blocking_issues"])


def test_p32_stability_report_counts_recurrent_ab_clusters(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    raw1 = _write_stability_artifacts(tmp_path, "P32_R1", rows=20)
    raw2 = _write_stability_artifacts(tmp_path, "P32_R2", rows=20)

    report = p32_stability.build_report(
        argparse.Namespace(
            run=[f"P32_R1={raw1.with_suffix('')}", f"P32_R2={raw2.with_suffix('')}"],
            min_runs=2,
            min_rows=20,
            max_d_rate=0.25,
        )
    )

    assert report["status"] == "PASS"
    assert report["runs_included"] == 2
    assert report["manual_A_B_cluster_count_stats"]["mean"] == 3
    assert report["accepted_cluster_jaccard_stats"]["mean"] == 1.0
    assert report["critique_origin_cluster_jaccard_stats"]["mean"] == 1.0
    recurrent = report["recurrence"]["accepted_clusters"]
    assert recurrent["paper-0|reproducibility_gap|target-0"] == 2
    critique_recurrent = report["recurrence"]["critique_origin_accepted_clusters"]
    assert critique_recurrent["paper-1|reproducibility_gap|target-1"] == 2
