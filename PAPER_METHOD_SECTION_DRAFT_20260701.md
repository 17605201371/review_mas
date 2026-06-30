# Method Section Draft

Date: 2026-07-01

This draft describes the method that the current code actually implements. It avoids claiming broad autonomous flaw discovery. The method contribution is ReviewState maintenance, conservative issue verification, final-view hygiene, and non-destructive recovery.

## 3. Method

### 3.1 Overview

DrMAS treats LLM-assisted reviewing as a state maintenance problem. Instead of asking a model to directly produce a final review, the system incrementally builds a structured `ReviewState`, audits that state, and renders the final review from an audited view.

At a high level, the pipeline is:

```text
paper text
  -> claim extraction
  -> evidence grounding and claim binding
  -> reviewer issue candidate formation
  -> review issue bundle verification
  -> final-view hygiene
  -> contested relation / recovery
  -> final report
```

The central design decision is to keep direct quote-grounded negative evidence separate from obligation-grounded review issues. A direct quote-grounded negative must be a copied paper quote that itself supports a reviewer-negative relation. An obligation-grounded review issue may instead be verified from a claim anchor, observed paper inventory, a concrete missing or mismatched entity, and the absence of resolving counterevidence.

### 3.2 ReviewState

We define a ReviewState as a structured state object:

```text
S = (C, E, F, G, I, K, R, H)
```

where:

- `C` is the set of extracted paper claims;
- `E` is the evidence map;
- `F` is the set of flaw or concern candidates;
- `G` is the set of evidence gaps and unresolved questions;
- `I` is the set of verified review issue bundles;
- `K` is the set of conflict or contested relations;
- `R` is the recovery patch log;
- `H` is the final-view hygiene audit.

Each claim `c in C` carries an identifier, text, status, type, importance, coverage tags, and optional claim obligations. Each evidence record `e in E` carries an identifier, claim binding, quote or inventory text, source locator, stance, strength, grounding labels, semantic labels, and review-negative labels when applicable.

The implementation maintains this state through `merge_review_state`, which merges model updates while preserving IDs, recording revisions, validating evidence bindings, and retaining explicit conflict notes. The final report is not rendered from raw model output; it is rendered from an audited state view.

### 3.3 Evidence Grounding And Claim Binding

DrMAS first grounds evidence against the paper and binds it to real claims. The evidence map records:

- `claim_id`: the target claim;
- `raw_quote` or evidence text;
- source locator and source bucket;
- `verified_grounding_label`;
- `semantic_grounding_label`;
- stance and strength;
- binding status and binding rationale.

The system distinguishes support evidence from negative or missing evidence. Accept-like support requires real-claim binding and verified evidence quality. This prevents fallback claims, parser artifacts, or context-only snippets from becoming accept-level support.

This evidence layer also builds neutral paper inventory. Inventory is not treated as negative evidence. It is used later to verify whether a reviewer issue is a real claim-inventory-obligation mismatch.

### 3.4 Two Negative Lanes

DrMAS uses two separate lanes for review-critical information.

#### Direct Quote-Grounded Negative Lane

The direct lane is intentionally strict. A record can count as a quote-grounded reviewer negative only if it passes all of the following checks:

```text
paper-grounded quote
AND semantic negative relation
AND reviewer-negative relation
AND real claim binding
AND non-noise negative type
AND linked flaw or issue
```

This lane is counted by `review_negative_verified_count`.

The current experiments show that this lane remains hard: the P28.6 run has `review_negative_verified_count=0`. The paper should present this as an honest limitation, not hide it.

#### Obligation-Grounded Review Issue Lane

The second lane verifies reviewer issues that are not copied negative quotes. This is the current main mechanism.

An obligation-grounded issue is represented as a review issue bundle:

```json
{
  "issue_id": "...",
  "claim_id": "...",
  "issue_type": "missing_ablation | missing_baseline | reproducibility_gap | ...",
  "required_evidence_type": "...",
  "claim_anchor": {"quote": "...", "locator": "..."},
  "observed_inventory": [{"quote": "...", "locator": "...", "observed_items": [...]}],
  "missing_or_mismatch": {"entity": "...", "items": [...]},
  "source_of_expectation": "reviewer_candidate | claim_obligation",
  "verification_status": "verified_review_issue",
  "not_quote_negative": true
}
```

This lane is counted by `verified_review_issue_count` and deduplicated by `verified_review_issue_cluster_count`.

### 3.5 Review Issue Bundle Verification

The verifier checks whether a candidate review issue is auditable from the paper state. Conceptually, a candidate bundle `b` becomes a verified issue only if:

```text
real_claim(b.claim_id)
AND locatable_claim_anchor(b)
AND concrete_missing_or_mismatch_entity(b)
AND auditable_expectation(b)
AND verifiable_observed_inventory(b)
AND issue_type_relevant_inventory(b)
AND missing_entity_not_already_observed(b)
AND no_ablation_or_full_text_counterevidence(b)
AND review_worthiness_gate(b)
AND not_author_limitation_or_retrieval_gap(b)
```

The implementation corresponds to `_review_issue_bundle_verification_failure` and `_is_obligation_grounded_review_issue_evidence_record`.

Important verifier gates include:

- claim anchor locatability;
- source-of-expectation checks;
- concrete missing item checks;
- missing-baseline specificity;
- missing-ablation target quality;
- observed inventory availability and relevance;
- counterevidence from inventory and full text;
- review-worthiness checks;
- rejection of author self-limitations, generic gaps, and retrieval gaps.

For `missing_ablation`, the target-quality gate is particularly important. Generic targets such as bare "encoder", "decoder", "network", "component", action fragments, or ordinary training actions are rejected or downgraded. Named contribution mechanisms or paper-specific performance-driving components may pass as high or medium confidence.

The verifier is deliberately precision-oriented. A rejected candidate may still be useful as a diagnosis-pending concern, but it is not counted as a verified review issue.

### 3.6 From Verified Bundle To ReviewState Objects

When a bundle is verified, DrMAS materializes it as structured state rather than as an unstructured text criticism.

The implementation uses:

- `source = reviewer_absence_audit`;
- `review_issue_source = obligation_grounded_review_issue`;
- `review_issue_verification_status = verified_review_issue`;
- `verified_grounding_label = paper_absence_audit_verified`;
- `review_negative_label = review_negative_absence_audit_verified`.

This naming is intentionally explicit. It says that the issue is verified by absence or coverage audit, not by a direct negative quote. The final view can then render it as a potential concern or contested issue without mixing it into `review_negative_verified_count`.

### 3.7 Final-View Hygiene

The final-view hygiene pass constructs an audited decision/report view through `build_decision_hygiene_view`. This view is used for final accounting and rendering.

The hygiene pass:

- verifies evidence records against the current state;
- builds evaluation and method inventory;
- performs claim-requirement audit;
- materializes verified review issue bundles;
- filters stale evidence gaps and stale conflicts;
- reconciles unsupported claim statuses only in the audited view when verified support exists;
- downgrades fallback, meta, support-only, and semantically rejected flaws;
- tracks active negative grounding conflicts;
- deduplicates review issue rows into clusters.

This step is what prevents false negative-evidence artifacts from leaking into the final review. In P28.6, stale `reviewer_absence_audit` anchors and quote-bank negative candidates that no longer pass the verifier are treated as safe rejections, not active conflicts.

### 3.8 Recovery As Non-Destructive Repair

Recovery is not a mechanism for forcing accept/reject decisions. It is a mechanism for repairing ReviewState inconsistencies.

The preferred recovery action is `mark_contested`:

```json
{
  "operation": "mark_contested",
  "claim_id": "...",
  "support_evidence_ids": ["..."],
  "negative_evidence_ids": ["..."],
  "review_issue_bundle_ids": ["..."],
  "relation_type": "supported_but_contested_by_review_issue"
}
```

This preserves a supported claim while exposing that a verified issue contests its sufficiency or scope. Unsafe downgrade attempts are tracked separately and should not be described as the main recovery path.

The paper should describe recovery as state repair:

```text
supported claim + verified issue -> supported-but-contested relation
```

not as:

```text
verified issue -> downgrade claim status
```

### 3.9 Rendering The Final Review

The final report is rendered from the audited view. This lets the report distinguish:

- strengths supported by real, grounded evidence;
- direct quote-grounded reviewer negatives, if any;
- obligation-grounded verified review issues;
- diagnosis-pending concerns;
- assessment limitations;
- contested claims;
- unresolved or deferred questions.

This design is essential to the paper narrative. The final review should not collapse all weak signals into a single "flaw" list. It should preserve the lifecycle state of each concern.

### 3.10 Implementation Anchors

The current implementation maps to the following functions and constants:

| Concept | Implementation anchor |
| --- | --- |
| state merge | `merge_review_state` |
| final audited view | `build_decision_hygiene_view` |
| review issue bundle verifier | `_review_issue_bundle_verification_failure` |
| obligation-grounded issue predicate | `_is_obligation_grounded_review_issue_evidence_record` |
| absence-audit materialization | `_add_reviewer_absence_audit_artifacts` |
| verified issue sync | `_sync_verified_review_issues` |
| missing-ablation target quality | `_missing_ablation_target_quality` |
| review-worthiness gate | `_review_issue_bundle_review_worthiness_failure` |
| stale/semantic negative rejection | `_negative_grounding_conflict_is_semantic_rejection` |
| issue source constant | `REVIEW_ISSUE_BUNDLE_SOURCE = obligation_grounded_review_issue` |
| issue status constant | `REVIEW_ISSUE_BUNDLE_STATUS = verified_review_issue` |
| absence audit source | `ABSENCE_AUDIT_SOURCE = reviewer_absence_audit` |

These anchors are for internal traceability. The paper text should explain the concepts rather than cite implementation names.

### 3.11 What The Method Does Not Claim

The method does not claim that every reviewer issue can be verified from paper text alone. Direct quote-grounded negative discovery remains an open limitation. Autonomous discovery of diverse, high-value reviewer issues remains future work. Final accept/reject is treated as a health check rather than the paper's target objective.

The method claim is narrower and stronger:

> A structured ReviewState lets the system separate support, direct negatives, obligation-grounded reviewer issues, diagnosis-pending concerns, and recovery actions, so final reviews can be grounded in auditable state rather than unstructured model prose.

## Drop-In Method Summary

DrMAS maintains a persistent ReviewState containing claims, evidence, reviewer issues, conflicts, and recovery actions. Evidence records are grounded and bound to real claims before they can support conclusions. Reviewer-critical information is split into two lanes: direct quote-grounded negatives and obligation-grounded review issue bundles. A review issue bundle is verified only when a real claim anchor, observed inventory anchor, concrete missing or mismatched entity, auditable expectation, and counterevidence checks all succeed. The final-view hygiene pass filters stale or unsafe artifacts and deduplicates issue rows into clusters. Recovery is non-destructive: verified issues mark supported claims as contested instead of downgrading claim status. This design turns LLM review generation into auditable ReviewState maintenance.
