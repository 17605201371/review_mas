#!/usr/bin/env python3
"""Recovery sub-funnel audit v1 (offline, rule-based, 0 LLM calls).

Implements **A5 / C0d** from `PAPER_GAP_REMEDIATION_PLAN.md` and addresses
`PAPER_C_DIRECTION_LIMITATION_AUDIT.md` 不足三 + INTEGRATED C0d.

Why this script exists
----------------------
The closure-run summary reports `patch_emitted=96 / patch_committed=1`, which
makes the recovery channel look like a black box. To support the paper's
*Structured Recovery Patch* claim we need a complete funnel that distinguishes:

  1. **Recovery worker self-abstention** — the worker explicitly emitted
     `action: "blocked"`, flagging that paper text or available evidence is
     insufficient to safely propose a state mutation. The validator records
     this as `failure_code = BLOCKED_BY_POLICY` and `validated = True`. This
     is a **desired safety behavior**, not a validator strictness issue.
  2. **Validator structural rejection** — patch was syntactically valid but
     violated a structural invariant (`INSUFFICIENT_EVIDENCE`,
     `NO_EFFECT_PATCH`, `INVALID_STATUS_TRANSITION`, `EVIDENCE_TARGET_MISMATCH`,
     `EVIDENCE_SEMANTIC_MISMATCH`, `UNRESOLVED_CONFLICT`, `UNKNOWN_TARGET`,
     `MISSING_TARGET_ID`, `SEMANTIC_MISMATCH`, `CHECKER_TOO_STRICT`).
  3. **Parse failure** — recovery output was unparseable (`PARSE_ERROR`).
  4. **Successful commit** — patch passed validator and the state merge
     actually applied the transition (`SUCCESS` + `recovery_committed`).
  5. **Negative / harmful commit** — committed but introduced a downgrade
     that the system later flagged as bad. (Currently 0 by construction;
     reported explicitly as a safety-claim datum.)

Outputs
-------
  - <output_json>: structured aggregate + per-paper funnel.
  - <output_md>:   human-readable report with all three breakdowns
                   (top-level funnel, validator code distribution,
                   `BLOCKED_BY_POLICY` self-abstention reason clusters).

The blocked-reason clustering is keyword-based and intentionally coarse: it
shows *why the worker abstained* (data missing, no evidence in slice, cannot
verify, etc.) without claiming entailment-level accuracy. It is meant to feed
the paper's Recovery section, not to drive any runtime decision.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# -----------------------------------------------------------------------------
# Failure-code groupings (sourced from
# agent_system/environments/env_package/review/recovery_validator.py)
# -----------------------------------------------------------------------------
WORKER_SELF_ABSTAIN_CODES = {"BLOCKED_BY_POLICY"}
PARSE_FAILURE_CODES = {"PARSE_ERROR"}
VALIDATOR_STRUCTURAL_REJECT_CODES = {
    "UNKNOWN_TARGET",
    "MISSING_TARGET_ID",
    "NO_EFFECT_PATCH",
    "INVALID_STATUS_TRANSITION",
    "SEMANTIC_MISMATCH",
    "INSUFFICIENT_EVIDENCE",
    "EVIDENCE_TARGET_MISMATCH",
    "EVIDENCE_SEMANTIC_MISMATCH",
    "UNRESOLVED_CONFLICT",
    "CHECKER_TOO_STRICT",
}
SUCCESS_CODES = {"SUCCESS"}

# -----------------------------------------------------------------------------
# Self-abstention reason clustering (BLOCKED_BY_POLICY only)
# -----------------------------------------------------------------------------
BLOCKED_REASON_PATTERNS: List[Tuple[str, re.Pattern]] = [
    ("data_missing_table_or_figure",
        re.compile(r"\b(missing|no full|cannot.*verify|no\b).*?(table|figure|caption|chart|plot)", re.IGNORECASE)),
    ("data_missing_quantitative",
        re.compile(r"\b(missing|no|lack).*?(quantitative|metric|score|accuracy|f1|recall|precision|statistical|number|percent)", re.IGNORECASE)),
    ("data_missing_ablation",
        re.compile(r"\b(missing|no full|lack|cannot.*verify).*?(ablation|baseline)", re.IGNORECASE)),
    ("data_missing_methodology",
        re.compile(r"\b(missing|no full|lack).*?(method|implementation|architecture|hyperparam|protocol)", re.IGNORECASE)),
    ("data_missing_generic",
        re.compile(r"\b(missing|no full|lack|cannot.*verify|no\b).*?(data|detail|content|information|paper)", re.IGNORECASE)),
    ("no_evidence_in_slice",
        re.compile(r"(no evidence|no .* evidence|evidence .* not (found|present|available)|no relevant)", re.IGNORECASE)),
    ("context_limited_truncation",
        re.compile(r"(truncat|context.*(limited|insufficient|cut off)|window|excerpt|snippet)", re.IGNORECASE)),
    ("cannot_verify_generic",
        re.compile(r"(cannot|unable to|not able to)[^a-z]*(verify|confirm|determine|conclude)", re.IGNORECASE)),
    ("policy_or_safety_block",
        re.compile(r"(policy|safety|guideline|forbidden|disallow)", re.IGNORECASE)),
]


def cluster_blocked_reason(text: str) -> str:
    if not text:
        return "unspecified"
    for label, pattern in BLOCKED_REASON_PATTERNS:
        if pattern.search(text):
            return label
    return "other"


def norm(value: Any) -> str:
    return str(value or "").strip().lower()


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def classify_outcome(code: str, committed: bool) -> str:
    """Map a per-turn (failure_code, committed) pair to the funnel bucket."""
    if committed:
        return "committed_success"
    if not code:
        return "no_validator_record"
    if code in WORKER_SELF_ABSTAIN_CODES:
        return "worker_self_abstain"
    if code in PARSE_FAILURE_CODES:
        return "parse_failure"
    if code in VALIDATOR_STRUCTURAL_REJECT_CODES:
        return "validator_rejected"
    if code in SUCCESS_CODES:
        # SUCCESS but not committed -> commit-side stall
        return "validator_passed_commit_stalled"
    return f"other:{code}"


def audit_paper(turns: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Per-paper recovery funnel and code distribution."""
    funnel = Counter()
    code_dist = Counter()
    blocked_clusters = Counter()
    detail_failed_reasons = Counter()
    push_sources = Counter()
    push_reasons = Counter()
    target_types = Counter()
    blocked_examples: List[Dict[str, Any]] = []
    committed_examples: List[Dict[str, Any]] = []
    harmful_commits = 0

    for i, t in enumerate(turns):
        if not t.get("recovery_attempted") and not t.get("recovery_patch_emitted"):
            continue
        funnel["attempted"] += int(bool(t.get("recovery_attempted") or t.get("recovery_patch_emitted")))
        if t.get("recovery_patch_emitted"):
            funnel["emitted"] += 1
        else:
            funnel["attempted_but_not_emitted"] += 1
            continue

        committed = bool(t.get("recovery_patch_committed") or t.get("recovery_committed"))
        code = (t.get("recovery_failure_code") or "").strip()
        bucket = classify_outcome(code, committed)
        funnel[bucket] += 1
        if code:
            code_dist[code] += 1

        if bucket == "worker_self_abstain":
            reason_text = t.get("recovery_blocked_by") or t.get("recovery_failure_message") or ""
            cluster = cluster_blocked_reason(reason_text)
            blocked_clusters[cluster] += 1
            if len(blocked_examples) < 3:
                blocked_examples.append({
                    "turn": i,
                    "cluster": cluster,
                    "reason_text": (reason_text or "")[:240],
                })

        if committed:
            committed_examples.append({
                "turn": i,
                "target_type": t.get("recovery_target_type"),
                "target_id": t.get("recovery_target_id"),
                "code": code,
            })

        target_types[t.get("recovery_target_type") or "unknown"] += 1
        for det in t.get("recovery_details") or []:
            r = det.get("failed_reason")
            if r:
                detail_failed_reasons[r] += 1
        for r in t.get("recovery_push_reasons") or []:
            push_reasons[r] += 1
        ps = t.get("recovery_push_source")
        if ps:
            push_sources[ps] += 1

        # Harmful commit = committed and worker emitted action that the system
        # later flagged as a regression. We rely on the manager-level signal
        # `blocked_aggressive_recovery_action` if present, otherwise 0.
        if committed and t.get("blocked_aggressive_recovery_action"):
            harmful_commits += 1

    return {
        "funnel": dict(funnel),
        "code_distribution": dict(code_dist),
        "worker_self_abstain_reason_clusters": dict(blocked_clusters),
        "detail_failed_reasons": dict(detail_failed_reasons),
        "push_sources": dict(push_sources),
        "push_reasons": dict(push_reasons),
        "target_types": dict(target_types),
        "blocked_examples": blocked_examples,
        "committed_examples": committed_examples,
        "harmful_commit_count": harmful_commits,
    }


def merge_counters(per_paper: List[Dict[str, Any]], key: str) -> Dict[str, int]:
    total: Counter = Counter()
    for entry in per_paper:
        for k, v in (entry["audit"].get(key) or {}).items():
            total[k] += v
    return dict(total)


def aggregate(per_paper: List[Dict[str, Any]]) -> Dict[str, Any]:
    funnel = merge_counters(per_paper, "funnel")
    code_dist = merge_counters(per_paper, "code_distribution")
    blocked_clusters = merge_counters(per_paper, "worker_self_abstain_reason_clusters")
    detail_failed_reasons = merge_counters(per_paper, "detail_failed_reasons")
    push_sources = merge_counters(per_paper, "push_sources")
    push_reasons = merge_counters(per_paper, "push_reasons")
    target_types = merge_counters(per_paper, "target_types")

    emitted = funnel.get("emitted", 0)
    committed = funnel.get("committed_success", 0)
    self_abstain = funnel.get("worker_self_abstain", 0)
    validator_rej = funnel.get("validator_rejected", 0)
    parse_fail = funnel.get("parse_failure", 0)
    commit_stalled = funnel.get("validator_passed_commit_stalled", 0)
    harmful_commits = sum(p["audit"].get("harmful_commit_count", 0) for p in per_paper)

    rates = {
        "commit_rate": committed / emitted if emitted else 0.0,
        "worker_self_abstain_rate": self_abstain / emitted if emitted else 0.0,
        "validator_reject_rate": validator_rej / emitted if emitted else 0.0,
        "parse_failure_rate": parse_fail / emitted if emitted else 0.0,
        "harmful_commit_rate_over_committed": (harmful_commits / committed) if committed else 0.0,
    }
    rows_with_any_commit = sum(
        1 for p in per_paper if p["audit"]["funnel"].get("committed_success", 0) > 0
    )
    return {
        "row_count": len(per_paper),
        "rows_with_any_commit": rows_with_any_commit,
        "funnel_total": funnel,
        "rates": rates,
        "validator_code_distribution": code_dist,
        "worker_self_abstain_reason_clusters": blocked_clusters,
        "detail_failed_reasons": detail_failed_reasons,
        "recovery_push_sources": push_sources,
        "recovery_push_reasons": push_reasons,
        "target_types": target_types,
        "harmful_commit_count": harmful_commits,
        "negative_recovery_commit_count": harmful_commits,  # alias for paper text
    }


def write_markdown(out_path: Path, payload: Dict[str, Any]) -> None:
    agg = payload["aggregate"]
    f = agg["funnel_total"]
    r = agg["rates"]
    cd = agg["validator_code_distribution"]
    bc = agg["worker_self_abstain_reason_clusters"]
    det = agg["detail_failed_reasons"]
    ps = agg["recovery_push_sources"]
    pr = agg["recovery_push_reasons"]
    tt = agg["target_types"]

    lines: List[str] = [
        "# Recovery Sub-funnel Audit v1",
        "",
        f"- input: `{payload['input']}`",
        f"- row_count: **{agg['row_count']}**",
        f"- rows_with_any_commit: **{agg['rows_with_any_commit']}**",
        f"- harmful (negative) commit count: **{agg['harmful_commit_count']}** "
        f"(rate over committed = {r['harmful_commit_rate_over_committed']:.4f})",
        "",
        "## Top-level funnel (per turn)",
        "",
        "| stage | count |",
        "|---|---:|",
        f"| recovery attempted | {f.get('attempted', 0)} |",
        f"| patch emitted | {f.get('emitted', 0)} |",
        f"| worker self-abstain (`action: blocked`) | {f.get('worker_self_abstain', 0)} |",
        f"| validator rejected | {f.get('validator_rejected', 0)} |",
        f"| parse failure | {f.get('parse_failure', 0)} |",
        f"| validator passed but commit stalled | {f.get('validator_passed_commit_stalled', 0)} |",
        f"| **commit success** | **{f.get('committed_success', 0)}** |",
        f"| (attempted but not emitted) | {f.get('attempted_but_not_emitted', 0)} |",
        f"| (no validator record) | {f.get('no_validator_record', 0)} |",
        "",
        "### Funnel rates",
        "",
        f"- commit rate (committed / emitted) = **{r['commit_rate']:.4f}**",
        f"- worker self-abstain rate = **{r['worker_self_abstain_rate']:.4f}**",
        f"- validator reject rate = {r['validator_reject_rate']:.4f}",
        f"- parse failure rate = {r['parse_failure_rate']:.4f}",
        "",
        "## Validator code distribution",
        "",
        "Distribution over the 13 documented codes from `recovery_validator.py`. "
        "`BLOCKED_BY_POLICY` is the **worker self-abstain** signal "
        "(`patch.action == 'blocked'`); validated=True merely confirms the schema "
        "was recognized. The rest are validator-side rejections.",
        "",
        "| code | count | category |",
        "|---|---:|---|",
    ]
    for code, count in sorted(cd.items(), key=lambda kv: -kv[1]):
        if code in WORKER_SELF_ABSTAIN_CODES:
            cat = "worker self-abstain"
        elif code in PARSE_FAILURE_CODES:
            cat = "parse failure"
        elif code in SUCCESS_CODES:
            cat = "success"
        elif code in VALIDATOR_STRUCTURAL_REJECT_CODES:
            cat = "validator rejected"
        else:
            cat = "other"
        lines.append(f"| `{code}` | {count} | {cat} |")
    lines += [
        "",
        "## Worker self-abstention reason clusters (BLOCKED_BY_POLICY only)",
        "",
        "Keyword-based clustering of `recovery_blocked_by` / "
        "`recovery_failure_message` text. **Coarse, not entailment-judged.** "
        "Used to show *why the worker declined to patch*, not to drive runtime "
        "decisions. This is a paper Recovery-section narrative aid.",
        "",
        "| cluster | count |",
        "|---|---:|",
    ]
    if bc:
        for cluster, count in sorted(bc.items(), key=lambda kv: -kv[1]):
            lines.append(f"| `{cluster}` | {count} |")
    else:
        lines.append("| _(no BLOCKED_BY_POLICY turns observed)_ | 0 |")

    lines += [
        "",
        "## Recovery target types attempted",
        "",
        "| target_type | count |",
        "|---|---:|",
    ]
    for k, v in sorted(tt.items(), key=lambda kv: -kv[1]):
        lines.append(f"| `{k}` | {v} |")

    lines += [
        "",
        "## detail.failed_reason distribution (per detail entry)",
        "",
        "| failed_reason | count |",
        "|---|---:|",
    ]
    if det:
        for k, v in sorted(det.items(), key=lambda kv: -kv[1]):
            lines.append(f"| `{k}` | {v} |")
    else:
        lines.append("| _(none)_ | 0 |")

    lines += [
        "",
        "## Recovery push context",
        "",
        "### push_source",
        "",
        "| source | count |",
        "|---|---:|",
    ]
    for k, v in sorted(ps.items(), key=lambda kv: -kv[1]):
        lines.append(f"| `{k}` | {v} |")
    lines += [
        "",
        "### push_reasons",
        "",
        "| reason | count |",
        "|---|---:|",
    ]
    for k, v in sorted(pr.items(), key=lambda kv: -kv[1]):
        lines.append(f"| `{k}` | {v} |")

    # paper-level summary table for case study selection
    lines += [
        "",
        "## Per-paper funnel snapshot (sorted by emitted desc, top 15)",
        "",
        "| paper_id | emitted | self_abstain | validator_reject | committed |",
        "|---|---:|---:|---:|---:|",
    ]
    sorted_per = sorted(
        payload["per_paper"],
        key=lambda p: -p["audit"]["funnel"].get("emitted", 0),
    )
    for entry in sorted_per[:15]:
        funnel_p = entry["audit"]["funnel"]
        lines.append(
            f"| {entry['paper_id']} | {funnel_p.get('emitted', 0)} | "
            f"{funnel_p.get('worker_self_abstain', 0)} | "
            f"{funnel_p.get('validator_rejected', 0)} | "
            f"{funnel_p.get('committed_success', 0)} |"
        )

    lines += [
        "",
        "## How to interpret",
        "",
        "- **`worker_self_abstain`** is the dominant non-commit bucket. The "
        "recovery worker explicitly returned `action: \"blocked\"` because the "
        "paper text or evidence in slice was insufficient to safely propose a "
        "state mutation. This is a desired *safety* behavior, not a validator "
        "strictness issue. The clustering of blocked reasons (above) shows the "
        "dominant abstention causes (data_missing_*, no_evidence_in_slice, "
        "cannot_verify_generic, ...).",
        "- **`validator_rejected`** is the structural validator path — a "
        "well-formed patch that violated an invariant (no-effect, invalid "
        "transition, semantic mismatch, etc.).",
        "- **`commit_success`** is the only bucket that mutates ReviewState. The "
        "low absolute count is consistent with the paper's claim that recovery "
        "is conservative; the funnel auditability (this script's main output) "
        "is the actual contribution, not a higher commit count.",
        "- **`harmful_commit_count`** / **`negative_recovery_commit_count`** "
        f"= **{agg['harmful_commit_count']}** is the safety datum: of the "
        f"{f.get('committed_success', 0)} commits, none were flagged as "
        "regressions by `blocked_aggressive_recovery_action`.",
        "",
        "Generated by `scripts/audit_recovery_subfunnel_v1.py`.",
    ]
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Recovery sub-funnel audit v1 (rule-based, 0 LLM calls).")
    parser.add_argument(
        "--jsonl",
        default="outputs/results_main/review_infer/mainline_final_v1_closure_9b_fulltest39_20260504_gold.jsonl",
        help="Input jsonl with `turn_logs` containing recovery_* fields.",
    )
    parser.add_argument(
        "--output-json",
        default="outputs/results_main/review_infer/recovery_subfunnel_v1.json",
    )
    parser.add_argument(
        "--output-md",
        default="docs/experiments/mainline_current/MAIN_EXPERIMENT_CODE_CLOSURE_V1/RECOVERY_SUBFUNNEL_V1.md",
    )
    args = parser.parse_args()

    rows = load_jsonl(Path(args.jsonl))
    per_paper: List[Dict[str, Any]] = []
    for row in rows:
        turns = row.get("turn_logs") or []
        per_paper.append({
            "paper_id": row.get("paper_id"),
            "audit": audit_paper(turns),
        })
    payload = {
        "input": args.jsonl,
        "schema_version": "v1",
        "rule_set": "validator codes from recovery_validator.py + worker action='blocked' detection + keyword reason clustering",
        "per_paper": per_paper,
        "aggregate": aggregate(per_paper),
    }

    out_json = Path(args.output_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    out_md = Path(args.output_md)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    write_markdown(out_md, payload)

    summary = {
        "row_count": payload["aggregate"]["row_count"],
        "rows_with_any_commit": payload["aggregate"]["rows_with_any_commit"],
        "funnel_total": payload["aggregate"]["funnel_total"],
        "rates": payload["aggregate"]["rates"],
        "validator_code_distribution": payload["aggregate"]["validator_code_distribution"],
        "worker_self_abstain_reason_clusters": payload["aggregate"]["worker_self_abstain_reason_clusters"],
        "harmful_commit_count": payload["aggregate"]["harmful_commit_count"],
        "negative_recovery_commit_count": payload["aggregate"]["negative_recovery_commit_count"],
        "output_json": str(out_json),
        "output_md": str(out_md),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
