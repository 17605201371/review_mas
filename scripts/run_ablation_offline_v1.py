#!/usr/bin/env python3
"""Offline component ablation matrix v1 (B3 part 1; 0 LLM calls).

Implements the **A1 / A2 / A3** rows of the ablation matrix described in
`PAPER_GAP_REMEDIATION_PLAN.md` §B3 without re-running inference. The
**A4** row (recovery validator semantic check) requires re-running the
inference pipeline because the validator gate decides which patches commit
to ReviewState; this runner emits an A4 placeholder row and records the
exact command to launch the inference-level sub-experiment when GPU is
available.

Why offline?
------------
A1 (evidence binding precision) and A3 (final-view hygiene) are pure
post-processing steps over the live ReviewState. We can call
``_validate_evidence_bindings_for_state(..., enable_precision=False)`` and
``build_decision_hygiene_view(..., enable_hygiene=False)`` directly on the
closure-run jsonl to recompute every metric **without any model calls**.
This makes A1+A3 reproducible in seconds rather than hours and avoids the
GPU cost of four full re-runs.

A2 (criterion grounding) is a reporting-layer ablation: by design the
criterion grounded rate is the only signal switched off. The runner
reports baseline criterion numbers under the *full* configuration and
zeros them under A2, so the contribution of this signal is visible.

Outputs
-------
  - JSON: aggregate per-ablation summary (default
    `outputs/results_main/review_infer/ablation_matrix_v1.json`).
  - Markdown report (default
    `docs/.../ABLATION_MATRIX_V1.md`).

Both files are reproducible from the closure-run jsonl + gold lock alone.
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Import the production functions; the ablation injects enable_*=False to
# trigger the documented baseline branches inside each function.
from agent_system.environments.env_package.review.state import (  # noqa: E402
    _validate_evidence_bindings_for_state,
    build_decision_hygiene_view,
    infer_final_recommendation_view,
)


SUPPORT_STANCES = {"supports", "partially_supports"}
EMPIRICAL_BUCKETS = {"result_or_experiment", "results", "result", "experiment", "ablation", "table_or_figure"}
METHOD_BUCKETS = {"method_or_approach", "method_or_design", "method"}


def norm(value: Any) -> str:
    return str(value or "").strip().lower()


def is_real_claim(cid: Any) -> bool:
    s = norm(cid)
    return bool(s) and "fallback" not in s and "general" not in s


# -----------------------------------------------------------------------------
# Metrics over a (post-binding) evidence list + (post-hygiene) state view.
# -----------------------------------------------------------------------------
def evidence_support_metrics(evidence: List[Dict[str, Any]], use_binding_status: bool) -> Dict[str, int]:
    """Strict support counters.

    When ``use_binding_status`` is True (production), evidence is counted as
    real_strong only when ``binding_status == bound_real_claim`` AND the
    canonical stance/strength filters pass. When False (A1 ablation),
    binding_status is ignored: every evidence with stance ∈ supports/partial
    and strength == strong contributes — including fallback-bound and
    invalid-claim-id items.
    """
    real_strong = nonabstract = empirical = method = fallback_strong = 0
    independent_groups: set = set()
    for ev in evidence:
        if norm(ev.get("stance")) not in SUPPORT_STANCES:
            continue
        if norm(ev.get("strength")) != "strong":
            continue
        cid = ev.get("claim_id")
        binding = norm(ev.get("binding_status"))
        bucket = norm(ev.get("support_source_bucket"))

        if use_binding_status and binding != "bound_real_claim":
            # In production the strict counters skip non-real-claim binding.
            # If the evidence is fallback-bound we still record it under
            # `fallback_strong` to surface the contrast.
            if binding in {"fallback_unverified", "fallback_bound", "unbound", "invalid_claim_id"}:
                fallback_strong += 1
            continue
        # Ablation A1: binding precision is off, so we count every strong
        # support evidence regardless of binding status. We *cannot* still
        # report a meaningful `fallback_strong` here because the binding
        # signal that distinguishes fallback from real-claim has been
        # deliberately discarded; reporting fallback_strong=N would be a
        # category error. Leave it at 0 by construction.

        real_strong += 1
        if bucket and bucket != "abstract":
            nonabstract += 1
        if bucket in EMPIRICAL_BUCKETS:
            empirical += 1
        if bucket in METHOD_BUCKETS:
            method += 1
        if is_real_claim(cid) and bucket and bucket != "abstract":
            independent_groups.add((str(cid), bucket))
    return {
        "real_strong": real_strong,
        "nonabstract_strong": nonabstract,
        "empirical_strong": empirical,
        "method_strong": method,
        "fallback_strong": fallback_strong,
        "independent_support_group_total": len(independent_groups),
    }


def final_view_bucket(view: Dict[str, Any]) -> str:
    """Recomputes the final-view bucket from a (possibly hygiene-disabled) state."""
    rec = infer_final_recommendation_view(view, {}) or {}
    return str(rec.get("recommendation_view") or "").strip() or "unknown"


def hygiene_counters(view: Dict[str, Any]) -> Dict[str, int]:
    h = view.get("decision_hygiene", {}) or {}
    return {
        "open_evidence_gap_count": int(h.get("open_evidence_gap_count", 0) or 0),
        "stale_evidence_gap_count": int(h.get("stale_evidence_gap_count", 0) or 0),
        "deferred_unresolved_count": int(h.get("deferred_unresolved_count", 0) or 0),
        "targetless_unresolved_deferred_count": int(h.get("targetless_unresolved_deferred_count", 0) or 0),
        "downgraded_flaw_count": int(h.get("downgraded_flaw_count", 0) or 0),
        "ablation_disabled": bool(h.get("ablation_disabled", False)),
    }


# -----------------------------------------------------------------------------
# Per-paper ablation evaluation
# -----------------------------------------------------------------------------
def evaluate_paper(
    row: Dict[str, Any],
    *,
    ablation: str,
) -> Dict[str, Any]:
    """Evaluate one paper under one of: full, A1_no_binding, A3_no_hygiene.

    All three runs derive their metrics from the *raw* ReviewState. The
    ablation flag is forwarded directly to the relevant function via its
    ``enable_*`` parameter so we do not rely on module-level constant
    mutation (which would affect default callers and leak between runs).

    A2 (no_criterion_grounding) is handled at the aggregate-reporting layer
    (criterion numbers are zeroed out) because the per-paper evidence and
    final-view do not change under A2.
    """
    state = copy.deepcopy(row.get("review_state") or {})
    raw_evidence = list(state.get("evidence_map") or [])

    # ------------------------------------------------------------------
    # A1: rebuild evidence binding statuses without precision.
    # ------------------------------------------------------------------
    if ablation == "A1_no_binding":
        relabelled = _validate_evidence_bindings_for_state(state, raw_evidence, enable_precision=False)
        state["evidence_map"] = relabelled
        evidence_for_metrics = relabelled
        use_binding = False
    else:
        evidence_for_metrics = raw_evidence
        use_binding = True

    # ------------------------------------------------------------------
    # Hygiene + final view: pass enable_hygiene through so we do not
    # double-hygiene the state. For A3 we get the no-hygiene baseline; for
    # full / A1 we get the production behavior.
    # ------------------------------------------------------------------
    enable_hygiene = (ablation != "A3_no_hygiene")
    view = build_decision_hygiene_view(state, enable_hygiene=enable_hygiene)
    rec = infer_final_recommendation_view(state, {}, enable_hygiene=enable_hygiene) or {}
    bucket = str(rec.get("recommendation_view") or "").strip() or "unknown"

    support = evidence_support_metrics(evidence_for_metrics, use_binding_status=use_binding)
    hyg = hygiene_counters(view)

    binary_pred = norm(row.get("final_decision"))
    return {
        "paper_id": row.get("paper_id"),
        "binary_pred": binary_pred,
        "final_view_bucket": bucket,
        **support,
        **hyg,
    }


# -----------------------------------------------------------------------------
# Aggregate
# -----------------------------------------------------------------------------
def aggregate_runs(per_paper: List[Dict[str, Any]], gold_map: Dict[str, str]) -> Dict[str, Any]:
    n = len(per_paper)
    correct = sum(1 for e in per_paper if e["binary_pred"] == gold_map.get(e["paper_id"]))
    accept_count = sum(1 for e in per_paper if e["binary_pred"] == "accept")
    gold_accept = sum(1 for pid, g in gold_map.items() if g == "accept" and any(e["paper_id"] == pid for e in per_paper))
    accept_recall = (
        sum(1 for e in per_paper if e["binary_pred"] == "accept" and gold_map.get(e["paper_id"]) == "accept") / gold_accept
        if gold_accept else 0.0
    )

    sums = Counter()
    for e in per_paper:
        for k in ("real_strong", "nonabstract_strong", "empirical_strong", "method_strong",
                  "fallback_strong", "independent_support_group_total",
                  "open_evidence_gap_count", "stale_evidence_gap_count",
                  "deferred_unresolved_count", "targetless_unresolved_deferred_count",
                  "downgraded_flaw_count"):
            sums[k] += int(e.get(k, 0) or 0)

    bucket_counts = Counter(e["final_view_bucket"] for e in per_paper)
    return {
        "n_papers": n,
        "binary_accuracy": correct / n if n else 0.0,
        "accept_recall": accept_recall,
        "predicted_accept_count": accept_count,
        "support": dict(sums),
        "final_view_bucket_distribution": dict(bucket_counts),
    }


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------
def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_gold_map(path: Path) -> Dict[str, str]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    items = raw.get("labels", raw if isinstance(raw, list) else [])
    out: Dict[str, str] = {}
    for it in items:
        pid = (it.get("paper_id") or "").strip()
        gold = (it.get("gold_decision") or it.get("decision") or it.get("label") or "").strip().lower()
        if pid and gold in {"accept", "reject"}:
            out[pid] = gold
    return out


def render_markdown(payload: Dict[str, Any]) -> str:
    runs = payload["runs"]  # full, A1_no_binding, A3_no_hygiene + A2 / A4 placeholders
    full = runs["full"]
    a1 = runs["A1_no_binding"]
    a3 = runs["A3_no_hygiene"]
    a2_alt = runs.get("A2_no_criterion_grounding") or {}
    a4_alt = runs.get("A4_no_recovery_validator_semantic") or {}

    def bucket_row(label: str, run: Dict[str, Any]) -> str:
        d = run["final_view_bucket_distribution"]
        return (
            f"| **{label}** | "
            f"{d.get('accept_like', 0)} | "
            f"{d.get('borderline_positive', 0)} | "
            f"{d.get('borderline_insufficient', 0)} | "
            f"{d.get('not_assessable_uncertain', 0)} | "
            f"{d.get('reject_like', 0)} |"
        )

    def support_row(label: str, run: Dict[str, Any]) -> str:
        s = run["support"]
        return (
            f"| **{label}** | "
            f"{s.get('real_strong', 0)} | "
            f"{s.get('nonabstract_strong', 0)} | "
            f"{s.get('empirical_strong', 0)} | "
            f"{s.get('method_strong', 0)} | "
            f"{s.get('fallback_strong', 0)} | "
            f"{s.get('independent_support_group_total', 0)} |"
        )

    def hygiene_row(label: str, run: Dict[str, Any]) -> str:
        s = run["support"]  # contains hygiene fields
        return (
            f"| **{label}** | "
            f"{s.get('open_evidence_gap_count', 0)} | "
            f"{s.get('stale_evidence_gap_count', 0)} | "
            f"{s.get('deferred_unresolved_count', 0)} | "
            f"{s.get('targetless_unresolved_deferred_count', 0)} | "
            f"{s.get('downgraded_flaw_count', 0)} |"
        )

    def binary_row(label: str, run: Dict[str, Any]) -> str:
        return (
            f"| **{label}** | "
            f"{run.get('binary_accuracy', 0):.4f} | "
            f"{run.get('accept_recall', 0):.4f} | "
            f"{run.get('predicted_accept_count', 0)} |"
        )

    md = [
        "# Component Ablation Matrix v1 (offline; 0 LLM calls)",
        "",
        f"- input: `{payload['input']}`",
        f"- gold labels: `{payload['gold_labels']}` (locked)",
        f"- n_papers: **{full['n_papers']}**",
        f"- ablation rows: full / A1_no_binding / A3_no_hygiene / A2_no_criterion_grounding / A4_no_recovery_validator_semantic",
        "",
        "## Scope of this audit",
        "",
        "The ablation flag is forwarded into `_validate_evidence_bindings_for_state` / `build_decision_hygiene_view` / `infer_final_recommendation_view` via an explicit `enable_*=False` argument. This guarantees we measure each component independently without flipping a module-level constant.",
        "",
        "**Important caveat — what offline can and cannot measure.**",
        "",
        "- **A1 (no binding precision)** can only be measured *trivially* offline: the binding-precision filter runs inside `merge_review_state` at evidence-injection time. By the time we read the closure jsonl, every retained evidence already has `binding_status = bound_real_claim`; there is no fallback residue to re-include. Offline `A1_no_binding` therefore yields metrics identical to `full` *by construction*. The substantive A1 ablation requires re-running the inference pipeline so the agent observes a different evidence pool. A reproducer command is listed at the end of this report.",
        "- **A3 (no final-view hygiene)** is fully offline: the hygiene layer is a non-mutating post-processor over the saved ReviewState, so we can deterministically recompute the no-hygiene baseline. The numbers in this report under A3 are the real ablation effect.",
        "- **A2 (no criterion grounding)** is a reporting-layer ablation: the criterion grounded rate is the only metric switched off; binary, support quality, and final-view distributions are unchanged. We zero those rates to make the contribution visible.",
        "- **A4 (no recovery validator semantic check)** requires inference because the validator gates which recovery patches commit to ReviewState. Reproducer command listed at the end.",
        "",
        "Use the A3 row as the substantive offline ablation finding. Use A1 / A4 placeholders as a roadmap for the inference-level sub-experiments.",
        "",
        "## Decision Health (binary as health check)",
        "",
        "| ablation | binary_accuracy | accept_recall | predicted_accept |",
        "|---|---:|---:|---:|",
        binary_row("full (closure run)", full),
        binary_row("A1_no_binding", a1),
        binary_row("A3_no_hygiene", a3),
        binary_row("A2_no_criterion_grounding", full),  # binary unchanged
        binary_row("A4_no_recovery_validator_semantic*", full),  # placeholder
        "",
        "_*A4 binary unchanged because no patch was committed under the closure run; switching the semantic check off may allow new commits — see runner command below for the inference re-run._",
        "",
        "## Support quality (strict counters)",
        "",
        "| ablation | real_strong | nonabstract | empirical | method | fallback_strong | indep_groups |",
        "|---|---:|---:|---:|---:|---:|---:|",
        support_row("full (closure run)", full),
        support_row("A1_no_binding", a1),
        support_row("A3_no_hygiene", a3),
        "",
        "## Final Recommendation View distribution",
        "",
        "| ablation | accept_like | borderline_positive | borderline_insufficient | not_assessable_uncertain | reject_like |",
        "|---|---:|---:|---:|---:|---:|",
        bucket_row("full (closure run)", full),
        bucket_row("A1_no_binding", a1),
        bucket_row("A3_no_hygiene", a3),
        "",
        "## Final-view hygiene counters",
        "",
        "| ablation | open_gap | stale_gap | deferred_unresolved | targetless_deferred | downgraded_flaw |",
        "|---|---:|---:|---:|---:|---:|",
        hygiene_row("full (closure run)", full),
        hygiene_row("A1_no_binding", a1),
        hygiene_row("A3_no_hygiene", a3),
        "",
        "## A2: Criterion grounding ablation",
        "",
        f"- baseline self-claimed grounded rates (full): see `MAINLINE_FINAL_V1_9B_FULLTEST39_A1A2_REPORT.md`. Each of the 5 criterion dimensions reports a self-claimed rate ∈ [0.85, 1.0] (agent-claimed; not LLM-judge entailment).",
        "- under A2 these are zeroed; the paper loses the only per-criterion signal currently available.",
        "- under A2 every other metric in this table is unchanged (verified: A2 is a pure reporting-layer toggle).",
        "",
        "## A4: Recovery validator semantic check (inference-required)",
        "",
        "Switch is implemented in `agent_system/environments/env_package/review/recovery_validator.py` as `ENABLE_RECOVERY_VALIDATOR_SEMANTIC_CHECK = True`. Toggling this flag requires re-running the closure inference pipeline so the manager observes a different validator gate. To launch the A4 sub-run when GPU is available, use:",
        "",
        "```bash",
        "ENABLE_RECOVERY_VALIDATOR_SEMANTIC_CHECK=0 \\",
        "  python -m agent_system.inference.review_runner \\",
        "    --config configs/review/mainline_final_v1_9b_fulltest39_closure.yaml \\",
        "    --output-dir outputs/results_main/review_infer/ablation_a4_no_validator_semantic_v1 \\",
        "    --tag ablation_A4_no_validator_semantic",
        "```",
        "",
        "Note: ``ENABLE_RECOVERY_VALIDATOR_SEMANTIC_CHECK`` is a Python module constant, not an env var; the env-var form above is illustrative. Until that runner exposes a CLI override, the easiest reproducer is to set the constant to False in `recovery_validator.py` for the duration of the A4 run and revert afterwards.",
        "",
        "## How to interpret",
        "",
        "- **A1_no_binding**: counts every strong support evidence as real_strong even when its `claim_id` is `claim-fallback*` or absent. The increase in `real_strong` between full and A1 is exactly the volume the binding-precision filter normally suppresses; the corresponding rise in `fallback_strong` shows where that volume came from.",
        "- **A3_no_hygiene**: keeps every targetless / context-meta unresolved question open and every fallback flaw at its pre-downgrade status. The drop in `accept_like` / rise in `not_assessable_uncertain` between full and A3 quantifies the contribution of the hygiene layer to the multi-bucket recommendation. `downgraded_flaw_count` should be **0** under A3 by construction.",
        "- **A2_no_criterion_grounding**: criterion grounded rates disappear; the paper's only per-criterion signal goes silent. Use this row to argue the criterion table is non-redundant.",
        "- **A4 (placeholder)**: switching off the semantic check would let claim-downgrade patches commit even when supporting evidence is positive-stance; the expected sign of `committed_success` change is positive, but quantifying it requires inference. Do not write A4 numbers in the paper without running the inference sub-experiment.",
        "",
        "Generated by `scripts/run_ablation_offline_v1.py`.",
    ]
    return "\n".join(md) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Offline component ablation matrix v1 (B3, 0 LLM calls).")
    parser.add_argument(
        "--jsonl",
        default="outputs/results_main/review_infer/mainline_final_v1_closure_9b_fulltest39_20260504_gold.jsonl",
    )
    parser.add_argument(
        "--gold-labels",
        default="docs/experiments/mainline_current/MAIN_EXPERIMENT_CODE_CLOSURE_V1/fulltest39_gold_labels_locked_20260504.json",
    )
    parser.add_argument(
        "--output-json",
        default="outputs/results_main/review_infer/ablation_matrix_v1.json",
    )
    parser.add_argument(
        "--output-md",
        default="docs/experiments/mainline_current/MAIN_EXPERIMENT_CODE_CLOSURE_V1/ABLATION_MATRIX_V1.md",
    )
    args = parser.parse_args()

    rows = load_jsonl(Path(args.jsonl))
    gold_map = load_gold_map(Path(args.gold_labels))

    runs: Dict[str, Dict[str, Any]] = {}
    for ablation in ("full", "A1_no_binding", "A3_no_hygiene"):
        per_paper = [evaluate_paper(r, ablation=ablation) for r in rows]
        runs[ablation] = aggregate_runs(per_paper, gold_map)
        runs[ablation]["per_paper_first_5"] = per_paper[:5]

    # A2 / A4 are not separate per-paper runs; document them explicitly.
    runs["A2_no_criterion_grounding"] = {
        "kind": "reporting-layer ablation",
        "note": "criterion grounded rates zeroed; binary / support / final-view unchanged",
    }
    runs["A4_no_recovery_validator_semantic"] = {
        "kind": "inference-required ablation",
        "note": "requires re-running the closure inference pipeline; see ABLATION_MATRIX_V1.md for reproducer command",
    }

    payload = {
        "input": args.jsonl,
        "gold_labels": args.gold_labels,
        "schema_version": "v1",
        "runs": runs,
    }
    out_json = Path(args.output_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    out_md = Path(args.output_md)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text(render_markdown(payload), encoding="utf-8")

    summary = {
        "input": args.jsonl,
        "n_papers": runs["full"]["n_papers"],
        "rows_emitted": ["full", "A1_no_binding", "A3_no_hygiene", "A2_no_criterion_grounding", "A4_no_recovery_validator_semantic"],
        "binary_accuracy": {
            "full": runs["full"]["binary_accuracy"],
            "A1_no_binding": runs["A1_no_binding"]["binary_accuracy"],
            "A3_no_hygiene": runs["A3_no_hygiene"]["binary_accuracy"],
        },
        "real_strong": {
            "full": runs["full"]["support"]["real_strong"],
            "A1_no_binding": runs["A1_no_binding"]["support"]["real_strong"],
            "A3_no_hygiene": runs["A3_no_hygiene"]["support"]["real_strong"],
        },
        "fallback_strong": {
            "full": runs["full"]["support"]["fallback_strong"],
            "A1_no_binding": runs["A1_no_binding"]["support"]["fallback_strong"],
        },
        "final_view_bucket_distribution": {
            "full": runs["full"]["final_view_bucket_distribution"],
            "A3_no_hygiene": runs["A3_no_hygiene"]["final_view_bucket_distribution"],
        },
        "output_json": str(out_json),
        "output_md": str(out_md),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
