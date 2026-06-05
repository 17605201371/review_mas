# Target Quality Audit

## Layer 2 Target Quality Counts

| target_quality_label | turns | recovery_turns | patch_emitted | commit | salvage_commit | fallback_contradiction |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| empty_target | 6 | 1 | 0 | 0 | 0 | 0 |
| narrow_real_target | 20 | 4 | 3 | 2 | 2 | 1 |
| broad_target | 10 | 0 | 0 | 0 | 0 | 0 |

## Reading

The strongest positive recovery outcomes in this run happened under `narrow_real_target`, not broad or fallback target quality. Broad targets were common, but they mostly corresponded to repeated evidence verification rather than actual recovery push/commit.

## Risk

A gate that simply suppresses broad target turns can reduce activity without improving recovery because broad targets may be evidence-stage symptoms rather than the direct cause of failed recovery.
