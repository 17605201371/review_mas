# Forensic Target Timeline Casebook V2

## Run

- Output: `outputs/results_main/review_infer/p25_1_target_observability_l2.jsonl`
- Root copy: `p25_1_target_observability_l2.jsonl`
- Log: `p25_1_target_observability_l2.log`
- Rows: 5
- Note: This is Layer 2, not the full 10-12 row Layer 3 forensic subset.

## Case Timeline

| paper_id | first_raw_target_turn | first_broad_raw_turn | first_fallback_target_turn | first_sanitize_bloat_turn | first_recovery_push_turn | first_patch_emission_turn | first_commit_turn | terminal_outcome | earliest_badpoint |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| 2Cg4YrsCMA | 2 | - | - | - | - | - | - | no_meaningful_recovery | no-badpoint-observed |
| NhLBhx5BVY | 2 | 2 | 2 | - | - | - | - | fallback_without_commit | fallback-first |
| IqaQZ1Jdky | 2 | - | 3 | - | 5 | 5 | 5 | commit | fallback-first |
| 9EBSEkFSje | 2 | 2 | - | - | - | - | - | no_meaningful_recovery | raw-broad-first |
| qgyF6JVmar | 2 | - | - | - | - | - | - | no_meaningful_recovery | no-badpoint-observed |

## Reading

The casebook separates two patterns: fallback can appear early and still lead to a commit (`IqaQZ1Jdky`), while raw broad targets can appear without recovery or commit (`9EBSEkFSje`). This means a blunt fallback suppression or broad-target gate is risky without a more selective condition.
