# MAINLINE_BASELINE_V2_METADATA

## Identity

- **baseline_name**: MAINLINE_BASELINE_V2
- **source_run**: `full39_20260602_head60ce62a_qwen35_t7.jsonl`
- **source_commit**: `30e9fd2`
- **previous_baseline**: P0_1A_BASELINE
- **replacement_reason**: Selected V2 baseline after full39 audit; audit-only closure commits add interpretability fields and case-audit exports without changing inference/runtime behavior.

## Key Metrics

| Metric | Value |
|--------|-------|
| paper_count | 39 |
| final_decision | reject 39/39 |
| avg_reward | 0.3390 |
| nonzero_reward | 39/39 |
| real_strong_total | 40 |
| empirical_strong_total | 23 |
| method_strong_total | 17 |
| avg_real_strong_per_paper | 1.0256 |
| zero_real_papers | 14 |
| papers_with_real_strong | 25 |

## Protection Lines (all must be 0)

| Line | Value |
|------|-------|
| final_nonreal_strong_support | 0 |
| low_score_promoted_strong | 0 |
| user_report_leakage_paper_count | 0 |
| final_report_leakage_paper_count | 0 |
| synthetic_marker_in_supporting_count | 0 |
| negative_evidence_unlinked_to_flaw | 0 |
| harmful_state_contamination_count | 0 |

## Audit Verdict

**STABLE_SAFE_QUALIFIED**

- All protection lines pass (all zeros)
- `EVIDENCE_TARGET_MISMATCH` cases are `safe_blocked_patch` (validator blocked, no state corruption)
- `invalid_negative_evidence_id` cases are `negative_semantic_anchor_conflict` (IDs exist but lack valid negative anchor)
- `state_contamination_count=34` decomposes to `harmful=0` + `repairable=0` + `conservative=34` (all validator-caught warnings; harmful is always 0 in current system)
- Audit-only closure commits add interpretability fields and case-audit exports without changing inference/runtime behavior

## Known Limitations

- `final_decision` always reject (`accept_recall=0` vs gold 8 accept)
- 14/39 papers have zero real strong support
- Support survival funnel: payload→merge→semantic→final has significant drop at semantic validation
- Negative evidence semantic rejection (16 cases) indicates room for improved negative anchor formation

## Schema Version

`mainline_baseline_v2_metadata_20260603`
