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
