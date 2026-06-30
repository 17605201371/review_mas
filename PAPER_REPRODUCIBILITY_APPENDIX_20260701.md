# Paper Reproducibility And Implementation Appendix Draft

Date: 2026-07-01

Status: appendix draft for the DrMAS paper narrative. This file maps paper concepts to current artifacts, scripts, and implementation anchors. It is not a new experiment and should not be cited as evidence for broader performance than the current hardneg20 diagnostic setting supports.

## Purpose

The main paper argues that DrMAS is a ReviewState maintenance framework rather than a direct review generator. This appendix supports that claim by mapping the paper-facing concepts to concrete implementation and audit artifacts.

This appendix can support claims about:

- where ReviewState fields are audited before rendering;
- how direct quote-grounded negatives are separated from obligation-grounded review issues;
- how issue rows are deduplicated into clusters;
- how verified issue bundles connect to non-destructive recovery;
- how dashboard, review-issue, and recovery case tables are regenerated.

This appendix cannot support claims about:

- broad peer-review quality improvement;
- solved direct quote-grounded negative discovery;
- a completed fresh full20 rerun;
- autonomous Critique issue discovery being mature;
- statistical generalization beyond the diagnostic hardneg20 setting.

## Current Authoritative Artifacts

| Artifact | Role In Paper |
| --- | --- |
| `P28_6_CONFLICTFIX_TARGETREFINE2_194911_HARDNEG20_DASHBOARD.md/json` | Main offline full20 diagnostic result |
| `P28_6_CONFLICTFIX_TARGETREFINE2_194911_REVIEW_ISSUE_CASE_TABLE.md/json` | Row-to-cluster review issue evidence table |
| `P28_6_CONFLICTFIX_TARGETREFINE2_194911_RECOVERY_CASE_TABLE.md/json` | Recovery and contested-relation case table |
| `P28_6_CONFLICTFIX_MIMO_PARTIAL16_224133_*` | Fresh live partial16 sanity check; not a full20 rerun |
| `P28_5_TARGETREFINE2_MANUAL_CLUSTER_AUDIT_20260630.md` | Manual A/B/C cluster audit used for conservative quality count |
| `PAPER_CONTINUOUS_DRAFT_20260701.md` | Current paper-facing manuscript draft |
| `PAPER_CLAIMS_EVIDENCE_MATRIX_20260701.md` | Claim-to-evidence guardrail |
| `PAPER_READINESS_AUDIT_20260701.md` | Skeptical readiness and reviewer-attack audit |

## Implementation Anchor Map

| Paper Concept | Implementation Anchor | What To Check |
| --- | --- | --- |
| ReviewState final-view audit | `agent_system/environments/env_package/review/state.py::build_decision_hygiene_view` | Builds the audited state view used by dashboards and case-table scripts |
| Claim-requirement audit | `state.py::_claim_requirement_audit` | Detects claim requirements not covered by verified support |
| Obligation-grounded issue materialization | `state.py::_add_reviewer_absence_audit_artifacts` | Converts verified absence/coverage gaps into review issue bundle evidence |
| Verified issue freshness/sync | `state.py::_sync_verified_review_issues` | Removes stale issue evidence that no longer passes current verification |
| Direct quote-negative lane | `state.py::_is_grounded_paper_negative_evidence_record` | Keeps strict quote-grounded reviewer negatives separate from obligation-grounded issues |
| Review issue clustering | `state.py::_review_issue_cluster_signature_for_record` and `state.py::_review_issue_cluster_id_for_record` | Deduplicates repeated issue rows by issue type and normalized target |
| Final report rendering | `state.py::_render_verified_review_issue_bundle_lines` and `state.py::_render_claim_requirement_gap_concerns` | Renders verified issues separately from diagnosis-pending concerns |
| Non-destructive recovery validation | `state.py::merge_review_state` and mark-contested validation helpers | Commits contested relations without downgrading supported claims |
| Recovery scheduling bridge | `agent_system/review_manager_policy.py::_verified_review_issue_contested_recovery_claim_ids` | Routes verified issue bundles with same-claim positive support toward `mark_contested` |
| Dashboard generation | `scripts/dashboard_run_comparison_v1.py` | Recomputes final-view metrics and protection status |
| Review issue case table | `scripts/audit_review_issue_case_table_v1.py` | Recomputes case rows, cluster ids, and duplicate row counts |
| Recovery case table | `scripts/audit_recovery_case_table_v1.py` | Recomputes recovery case classifications and verified-issue repair counts |
| Author-limitation guard | `scripts/audit_verified_negative_author_limitation_guard_v1.py` | Guards against author self-limitations being counted as reviewer-negative evidence |

## Reproduction Checklist

Use the current code commit and the authoritative hardneg20 artifacts. The main reproducibility goal is to regenerate the dashboard and case tables, not to claim a fresh run.

1. Regenerate the dashboard from the completed MiMo hardneg20 artifact with the current verifier and final-view hygiene.
2. Regenerate the review issue case table from the same artifact.
3. Regenerate the recovery case table from the same artifact.
4. Verify the main metric tuple:

```text
paper_count = 20
review_negative_verified_count = 0
verified_review_issue_count = 13
verified_review_issue_cluster_count = 9
duplicate_review_issue_row_count = 4
mark_contested_commit_count = 14
recovery_case_verified_review_issue_repair = 6
negative_grounding_conflict_count = 0
negative_semantic_anchor_conflict_count = 0
semantic_negative_without_review_relation_count = 0
negative_evidence_unlinked_to_flaw = 0
positive_or_neutral_negative_candidate_count = 0
```

5. Verify that the fresh live run remains described as partial16 unless a new full20 run completes:

```text
paper_count = 16
verified_review_issue_cluster_count = 8
review_negative_verified_count = 0
mark_contested_commit_count = 5
recovery_case_verified_review_issue_repair = 5
```

## Paper-Facing Interpretation

The implementation evidence supports the following statement:

> DrMAS represents review-critical content as auditable state. In the current diagnostic artifacts, the system separates direct quote-grounded negatives from obligation-grounded review issues, verifies 9 issue clusters after row deduplication, and routes verified issues to non-destructive contested recovery while keeping measured false-negative-evidence conflicts at zero.

The implementation evidence does not support the following stronger statement:

> DrMAS broadly discovers true review flaws or solves negative evidence discovery.

## Appendix Integration Notes

For the main paper, use this appendix only to support reproducibility and implementation transparency. Keep the main text focused on concepts and results:

- ReviewState lifecycle;
- two critical-content lanes;
- issue-bundle verifier;
- final-view hygiene;
- non-destructive recovery.

Move function names, script names, and artifact prefixes to the appendix unless they are needed to define the experimental setting.
