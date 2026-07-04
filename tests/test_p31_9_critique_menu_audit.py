from scripts import dashboard_run_comparison_v1 as dashboard


def test_dashboard_surfaces_selected_menu_failure_and_existing_seed_attribution_details():
    row = {
        "paper_id": "paper-1",
        "review_state": {
            "state_audit": {
                "decision_hygiene": {
                    "critique_payload_verified_cluster_count": 1,
                    "critique_selected_verified_cluster_count": 1,
                    "critique_selected_verified_by_existing_cluster_count": 1,
                    "candidate_menu_item_failed_count": 1,
                    "candidate_menu_item_failed_by_reason": {
                        "selected_menu_item_not_in_current_menu_or_filtered": 1,
                    },
                    "candidate_menu_item_failed_by_stage": {
                        "menu_lookup_or_quality_filter": 1,
                    },
                    "failed_menu_candidate_items": [
                        {
                            "candidate_id": "review-issue-candidate-selected-menu-1",
                            "candidate_menu_id": "rim-c1-ma-example",
                            "claim_id": "claim-1",
                            "issue_type": "missing_ablation",
                            "review_issue_slot": "missing_ablation",
                            "selected_missing_items": ["example mechanism"],
                            "resolved_expected_entity": "example mechanism",
                            "stop_stage": "menu_lookup_or_quality_filter",
                            "rejection_reason": "selected_menu_item_not_in_current_menu_or_filtered",
                            "inventory_anchor_summary": {
                                "locator": "Table 1",
                                "quote": "Table 1 reports an ablation over a different mechanism.",
                                "observed_items": ["different mechanism"],
                            },
                        }
                    ],
                    "critique_selected_verified_clusters": [
                        {
                            "claim_id": "claim-2",
                            "issue_type": "missing_baseline",
                            "issue_cluster_key": "missing_baseline|equalal_baseline",
                            "issue_cluster_target": "equalal_baseline",
                            "candidate_menu_ids": ["rim-c2-mb-equalal"],
                            "candidate_ids": ["review-issue-candidate-selected-menu-2"],
                            "discovery_origin": "critique_payload_menu_selected",
                            "attribution_mode": "selected_menu_matches_existing_verified_cluster",
                        }
                    ],
                }
            }
        },
    }

    row[dashboard._DASHBOARD_HYGIENE_CACHE_KEY] = row["review_state"]["state_audit"]["decision_hygiene"]
    metrics = dashboard._aggregate([row])

    assert metrics["critique_direct_verified_cluster_count"] == 0
    assert metrics["critique_selected_existing_seed_cluster_count"] == 1
    assert metrics["candidate_menu_item_failed_detail_count"] == 1
    assert metrics["candidate_menu_item_failed_details"][0]["paper_id"] == "paper-1"
    assert metrics["candidate_menu_item_failed_details"][0]["rejection_reason"] == (
        "selected_menu_item_not_in_current_menu_or_filtered"
    )
    assert metrics["critique_selected_verified_cluster_detail_count"] == 1
    assert metrics["critique_selected_verified_cluster_details"][0]["candidate_menu_ids"] == [
        "rim-c2-mb-equalal"
    ]
