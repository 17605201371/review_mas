# Paper Result Consistency Audit

Date: 2026-07-01

Status: result-number consistency check for the current DrMAS paper narrative. This is not a new experiment. It verifies that the paper-facing result claims in the clean/continuous drafts match the authoritative P28.6 artifacts.

## Authoritative Artifacts Checked

Main full20 diagnostic result:

- `P28_6_CONFLICTFIX_TARGETREFINE2_194911_HARDNEG20_DASHBOARD.md/json`
- `P28_6_CONFLICTFIX_TARGETREFINE2_194911_REVIEW_ISSUE_CASE_TABLE.md/json`
- `P28_6_CONFLICTFIX_TARGETREFINE2_194911_RECOVERY_CASE_TABLE.md/json`
- `P28_5_TARGETREFINE2_MANUAL_CLUSTER_AUDIT_20260630.md`

Fresh live sanity check:

- `P28_6_CONFLICTFIX_MIMO_PARTIAL16_224133_HARDNEG20_DASHBOARD.md/json`
- `P28_6_CONFLICTFIX_MIMO_PARTIAL16_224133_REVIEW_ISSUE_CASE_TABLE.md/json`
- `P28_6_CONFLICTFIX_MIMO_PARTIAL16_224133_RECOVERY_CASE_TABLE.md/json`

## Metric Tuple Confirmed

The main full20 offline recompute supports the following paper-facing tuple:

```text
paper_count = 20
review_negative_verified_count = 0
verified_review_issue_count = 13
verified_review_issue_cluster_count = 9
duplicate_review_issue_row_count = 4
reviewer_candidate_review_issue_count = 13
reviewer_candidate_review_issue_critique_payload_count = 2
reviewer_candidate_review_issue_deterministic_seed_count = 11
claim_obligation_review_issue_count = 0
claim_obligation_review_issue_cluster_count = 0
verified_missing_ablation_cluster_count = 6
review_issue_cluster_type_missing_ablation = 6
review_issue_cluster_type_missing_baseline = 2
review_issue_cluster_type_reproducibility_gap = 1
mark_contested_commit_count = 14
recovery_case_verified_review_issue_repair = 6
negative_grounding_conflict_count = 0
negative_semantic_anchor_conflict_count = 0
semantic_negative_without_review_relation_count = 0
negative_evidence_unlinked_to_flaw = 0
positive_or_neutral_negative_candidate_count = 0
```

The fresh live partial16 sanity check supports the following limited tuple:

```text
paper_count = 16
review_negative_verified_count = 0
verified_review_issue_count = 12
verified_review_issue_cluster_count = 8
duplicate_review_issue_row_count = 4
reviewer_candidate_review_issue_count = 12
reviewer_candidate_review_issue_critique_payload_count = 0
reviewer_candidate_review_issue_deterministic_seed_count = 12
verified_missing_ablation_cluster_count = 6
mark_contested_commit_count = 5
recovery_case_verified_review_issue_repair = 5
negative_grounding_conflict_count = 0
negative_semantic_anchor_conflict_count = 0
semantic_negative_without_review_relation_count = 0
negative_evidence_unlinked_to_flaw = 0
positive_or_neutral_negative_candidate_count = 0
```

## Manuscript Consistency Findings

The current clean and continuous drafts are consistent with the main P28.6 tuple:

- abstract headline: 9 obligation-grounded issue clusters, 8 manually judged valid/defensible, direct quote-negative lane at 0;
- Table 1: 20 papers, 0 direct quote-grounded negatives, 13 rows, 9 clusters, 4 duplicate rows, 13 reviewer-candidate rows, 2 Critique-payload rows, 11 deterministic-seed rows, 0 claim-obligation fallback rows, 6 missing-ablation clusters, all measured protection lines at 0/PASS;
- Figure 3: 13 rows -> 9 clusters -> 8 A/B clusters, duplicate rows = 4, direct negatives = 0;
- Table 3: 3 A clusters, 5 B clusters, 1 C cluster, conservative count 8/9;
- Table 4: full20 offline mark-contested commits = 14, verified-review-issue repairs = 6; fresh partial16 mark-contested commits = 5, verified-review-issue repairs = 5;
- limitations: fresh live rerun is partial16, not a completed full20; deterministic seeds dominate; issue distribution is missing-ablation heavy.

The only drift found in this pass was outside the result table: `PAPER_BIBLIOGRAPHY_AUDIT_20260701.md` still described 13 bibliography keys across 14 citation occurrences. The current clean/continuous drafts use 13 unique bibliography keys across 16 citation-key uses, and that audit line has been corrected.

## Guardrail For Future Edits

Do not change the main paper result wording unless the corresponding authoritative artifact changes and this audit is updated. In particular:

- do not call the 13 rows independent defects;
- do not call the partial16 run a fresh full20 rerun;
- do not convert `review_negative_verified_count=0` into a hidden caveat;
- do not describe deterministic reviewer seeds as autonomous Critique discovery;
- do not report the 8/9 manual audit as population-level precision.

## Recheck Commands

```bash
python3 - <<'PY'
import json
from pathlib import Path
for f in [
    'P28_6_CONFLICTFIX_TARGETREFINE2_194911_HARDNEG20_DASHBOARD.json',
    'P28_6_CONFLICTFIX_MIMO_PARTIAL16_224133_HARDNEG20_DASHBOARD.json',
]:
    data = json.loads(Path(f).read_text())
    m = data['candidate']['metrics']
    print(f)
    for k in [
        'paper_count',
        'review_negative_verified_count',
        'verified_review_issue_count',
        'verified_review_issue_cluster_count',
        'duplicate_review_issue_row_count',
        'reviewer_candidate_review_issue_critique_payload_count',
        'reviewer_candidate_review_issue_deterministic_seed_count',
        'verified_missing_ablation_cluster_count',
        'mark_contested_commit_count',
        'recovery_case_verified_review_issue_repair',
        'negative_grounding_conflict_count',
        'negative_semantic_anchor_conflict_count',
        'semantic_negative_without_review_relation_count',
        'negative_evidence_unlinked_to_flaw',
        'positive_or_neutral_negative_candidate_count',
    ]:
        print(k, m.get(k))
PY
```

```bash
python3 - <<'PY'
import re
from pathlib import Path
bib = Path('PAPER_REFERENCES_DRAFT_20260701.bib').read_text()
bib_keys = set(re.findall(r'@\w+\{([^,]+),', bib))
for path in ['PAPER_CLEAN_BODY_DRAFT_20260701.md', 'PAPER_CONTINUOUS_DRAFT_20260701.md']:
    text = Path(path).read_text()
    cite_keys = []
    for m in re.finditer(r'\\citep\{([^}]+)\}', text):
        cite_keys.extend(k.strip() for k in m.group(1).split(','))
    refs = re.findall(r'!\[[^\]]+\]\((paper_figures/[^)]+\.svg)\)', text)
    print(path, 'unique_cite_keys', len(set(cite_keys)), 'citation_key_uses', len(cite_keys), 'figure_refs', len(refs))
    assert not [k for k in cite_keys if k not in bib_keys]
    assert len(refs) == 4
PY
```
