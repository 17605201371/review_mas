# P31.6 Fresh Full20 Runbook

## Purpose

P31.6 is the checkpoint before P32.  Do not enter P32 until a fresh MiMo full20
run proves Critique-origin recovery quality:

```text
critique_payload_verified_cluster_count >= 3
machine protection = PASS
manual A/B Critique-origin clusters >= 3
manual D clusters = 0
unfilled manual audit clusters = 0
no external-baseline / retrieval-context / author-limitation false positives
```

Current old-raw status:

```text
machine_gate = FAIL
manual_gate = FAIL
critique_payload_verified_cluster_count = 2
manual_A_B_clusters = 2
api_preflight = 402 insufficient_balance
```

## 1. Check Readiness

```bash
scripts/p31_6_status_report.py \
  --api-preflight \
  --output-json P31_6_READINESS_STATUS_20260703.json \
  --output-md P31_6_READINESS_STATUS_20260703.md
```

If the report says `402 insufficient_balance`, stop.  Do not create a fresh
full20 result from a failed/empty run.

## 2. Launch Fresh Full20

After MiMo balance/key is usable:

```bash
scripts/p31_6_full20_pipeline.sh --launch --wait --update-latest
```

This wrapper launches with:

```text
DRMAS_NEG_QUOTE_HYGIENE=1
DRMAS_TARGETED_NEGATIVE_SEARCH=1
DRMAS_FREEFORM_REVIEWER_NEGATIVE=1
DRMAS_REVIEW_ISSUE_BUNDLE=1
API_MAX_WORKERS=4
API_MAX_RETRIES=8
API_TIMEOUT=600
MAX_TOKENS=1536
```

It waits for 20 rows, then generates:

```text
*_HARDNEG20_DASHBOARD.md/json/audit.json
*_REVIEW_ISSUE_CASE_TABLE.md/json
*_RECOVERY_CASE_TABLE.md/json
*_ENTRY_GATE_AUDIT.md/json
*_MANUAL_AUDIT_TEMPLATE.md/json
*_READINESS_STATUS.md/json
```

## 3. Fill Manual Audit

Copy the generated `*_MANUAL_AUDIT_TEMPLATE.json` to:

```text
<LABEL>_MANUAL_AUDIT.json
```

Fill every Critique-origin cluster:

```text
label = A | B | C | D | MERGE
manual_decision = keep | keep_with_wording_caution | downgrade | reject | merge
reason = concrete justification
false_positive_categories = required for D
```

Use the rubric:

```text
A = clear review-worthy issue with strong claim/inventory/missing relation
B = defensible review concern; usable with careful wording
C = weak or over-specific concern; keep only as diagnosis/pending
D = false positive / contradicted by paper text
MERGE = duplicate; do not count separately
```

## 4. Validate Manual Audit

```bash
scripts/p31_6_manual_audit.py validate \
  --audit-json <LABEL>_MANUAL_AUDIT.json \
  --output-json <LABEL>_MANUAL_AUDIT_VALIDATION.json \
  --output-md <LABEL>_MANUAL_AUDIT_VALIDATION.md
```

Validation must pass:

```text
manual_A_B_clusters >= 3
manual_D_clusters = 0
unfilled_clusters = 0
```

## 5. Re-run Entry Gate With Manual Audit

```bash
scripts/p31_6_entry_gate_audit.py \
  --dashboard-json <LABEL>_HARDNEG20_DASHBOARD.json \
  --case-json <LABEL>_REVIEW_ISSUE_CASE_TABLE.json \
  --recovery-json <LABEL>_RECOVERY_CASE_TABLE.json \
  --manual-audit-validation-json <LABEL>_MANUAL_AUDIT_VALIDATION.json \
  --require-manual-audit \
  --output-json <LABEL>_ENTRY_GATE_WITH_MANUAL_AUDIT.json \
  --output-md <LABEL>_ENTRY_GATE_WITH_MANUAL_AUDIT.md
```

P32 entry requires both:

```text
machine_gate = PASS
manual_gate = PASS
```

## 6. Do Not Enter P32 If

```text
critique_payload_verified_cluster_count < 3
manual_A_B_clusters < 3
manual_D_clusters > 0
unfilled_clusters > 0
negative_evidence_unlinked_to_flaw > 0
positive_or_neutral_negative_candidate_count > 0
negative_grounding_conflict_count > 0
API run has fewer than 20 rows
```

## 7. Current Next Action

```text
Restore MiMo balance/key, then run:
scripts/p31_6_full20_pipeline.sh --launch --wait --update-latest
```
