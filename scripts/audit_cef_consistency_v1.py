#!/usr/bin/env python3
"""Claim-Evidence-Flaw Consistency checker v1 (offline, pure rule-based).

Implements **A3 / C0b** from `PAPER_GAP_REMEDIATION_PLAN.md` and addresses
`PAPER_C_DIRECTION_LIMITATION_AUDIT.md` 不足十二 + INTEGRATED #N2 / C0b.

This script is the cheapest quantifiable main metric for the *State Hygiene /
Auditability* paper section. It does **0 LLM calls** and reads only the
existing fulltest39 jsonl produced by the closure pipeline.

It checks 6 invariants over the ReviewState exports:

  R1. `flaw.related_claim_ids` must all exist in `claims[].claim_id`.
  R2. `flaw.evidence_ids` must all exist in `evidence_map[].evidence_id`.
  R3. `evidence.claim_id` must exist in `claims[].claim_id`
      (fallback / general claim ids excluded from the check).
  R4. `claim.supporting_evidence_ids` must all exist in
      `evidence_map[].evidence_id`.
  R5. If `claim.status == "supported"`, at least one supporting evidence must
      have `stance in {supports, partially_supports}`.
  R6. If `flaw.status == "resolved"` and `flaw.severity in {critical, major}`,
      a downgrade reason must be recorded (otherwise it is an inconsistency:
      a supposedly resolved critical flaw should not silently survive).

Per-paper score:
    consistency_score = 1 - (sum(violations) / sum(checks))
where `checks` is the number of rule applications (each ID, each claim, each
flaw, etc.) so the denominator scales with paper complexity.

Outputs:
  - <output>.json : structured per-paper + aggregate score.
  - <output>.md   : human-readable report with rule breakdown.

Both are safe to publish as evidence in a paper *State Hygiene* section,
since they are entirely deterministic and reproducible from the jsonl alone.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

SUPPORT_STANCES = {"supports", "partially_supports"}
RESOLVED_FLAW_STATUS = {"resolved", "addressed", "retracted", "downgraded"}
SEVERE_FLAW_LEVELS = {"critical", "major"}


def norm(value: Any) -> str:
    return str(value or "").strip().lower()


def is_fallback_claim_id(cid: Any) -> bool:
    s = norm(cid)
    return (not s) or "fallback" in s or "general" in s


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def check_paper(state: Dict[str, Any]) -> Tuple[Dict[str, Dict[str, int]], List[Dict[str, Any]]]:
    """Run all 6 rules against a single ReviewState; return per-rule counters
    and a list of concrete violation records (for case-level reporting)."""
    claims = state.get("claims") or []
    evidence = state.get("evidence_map") or []
    flaws = state.get("flaw_candidates") or []

    claim_ids = {norm(c.get("claim_id")) for c in claims if c.get("claim_id")}
    evidence_ids = {norm(e.get("evidence_id")) for e in evidence if e.get("evidence_id")}
    evidence_by_id = {norm(e.get("evidence_id")): e for e in evidence}

    rules: Dict[str, Dict[str, int]] = {
        "R1_flaw_claim_id_exists": {"checks": 0, "violations": 0},
        "R2_flaw_evidence_id_exists": {"checks": 0, "violations": 0},
        "R3_evidence_claim_id_exists": {"checks": 0, "violations": 0},
        "R4_claim_supporting_evidence_id_exists": {"checks": 0, "violations": 0},
        "R5_supported_claim_has_supporting_evidence": {"checks": 0, "violations": 0},
        "R6_resolved_severe_flaw_has_reason": {"checks": 0, "violations": 0},
    }
    violations: List[Dict[str, Any]] = []

    # R1: flaw.related_claim_ids ⊆ claim_ids
    for fl in flaws:
        for cid in fl.get("related_claim_ids") or []:
            rules["R1_flaw_claim_id_exists"]["checks"] += 1
            if norm(cid) and norm(cid) not in claim_ids:
                rules["R1_flaw_claim_id_exists"]["violations"] += 1
                violations.append({
                    "rule": "R1_flaw_claim_id_exists",
                    "flaw_id": fl.get("flaw_id"),
                    "missing_claim_id": cid,
                })

    # R2: flaw.evidence_ids ⊆ evidence_ids
    for fl in flaws:
        for eid in fl.get("evidence_ids") or []:
            rules["R2_flaw_evidence_id_exists"]["checks"] += 1
            if norm(eid) and norm(eid) not in evidence_ids:
                rules["R2_flaw_evidence_id_exists"]["violations"] += 1
                violations.append({
                    "rule": "R2_flaw_evidence_id_exists",
                    "flaw_id": fl.get("flaw_id"),
                    "missing_evidence_id": eid,
                })

    # R3: evidence.claim_id ∈ claim_ids (excluding fallback / general claim slots)
    for ev in evidence:
        cid = ev.get("claim_id")
        if not cid or is_fallback_claim_id(cid):
            continue
        rules["R3_evidence_claim_id_exists"]["checks"] += 1
        if norm(cid) not in claim_ids:
            rules["R3_evidence_claim_id_exists"]["violations"] += 1
            violations.append({
                "rule": "R3_evidence_claim_id_exists",
                "evidence_id": ev.get("evidence_id"),
                "missing_claim_id": cid,
            })

    # R4: claim.supporting_evidence_ids ⊆ evidence_ids
    for cl in claims:
        for eid in cl.get("supporting_evidence_ids") or []:
            rules["R4_claim_supporting_evidence_id_exists"]["checks"] += 1
            if norm(eid) and norm(eid) not in evidence_ids:
                rules["R4_claim_supporting_evidence_id_exists"]["violations"] += 1
                violations.append({
                    "rule": "R4_claim_supporting_evidence_id_exists",
                    "claim_id": cl.get("claim_id"),
                    "missing_evidence_id": eid,
                })

    # R5: claim.status == supported ⇒ at least one supporting evidence with
    #     supports / partially_supports stance.
    for cl in claims:
        if norm(cl.get("status")) != "supported":
            continue
        rules["R5_supported_claim_has_supporting_evidence"]["checks"] += 1
        ok = False
        for eid in cl.get("supporting_evidence_ids") or []:
            ev = evidence_by_id.get(norm(eid))
            if ev and norm(ev.get("stance")) in SUPPORT_STANCES:
                ok = True
                break
        if not ok:
            rules["R5_supported_claim_has_supporting_evidence"]["violations"] += 1
            violations.append({
                "rule": "R5_supported_claim_has_supporting_evidence",
                "claim_id": cl.get("claim_id"),
                "supporting_evidence_ids": cl.get("supporting_evidence_ids"),
            })

    # R6: resolved + severe flaw must record a downgrade / resolution reason.
    #     Otherwise a "resolved critical" silently survives -- inconsistency.
    for fl in flaws:
        if (
            norm(fl.get("status")) in RESOLVED_FLAW_STATUS
            and norm(fl.get("severity")) in SEVERE_FLAW_LEVELS
        ):
            rules["R6_resolved_severe_flaw_has_reason"]["checks"] += 1
            reason_fields = [
                fl.get("hygiene_status_reason"),
                fl.get("resolution_reason"),
                fl.get("downgrade_reason"),
                fl.get("grounding_status"),
            ]
            if not any(norm(r) for r in reason_fields):
                rules["R6_resolved_severe_flaw_has_reason"]["violations"] += 1
                violations.append({
                    "rule": "R6_resolved_severe_flaw_has_reason",
                    "flaw_id": fl.get("flaw_id"),
                    "severity": fl.get("severity"),
                    "status": fl.get("status"),
                })

    return rules, violations


def aggregate(per_paper: List[Dict[str, Any]]) -> Dict[str, Any]:
    rule_total: Dict[str, Dict[str, int]] = {}
    checks_total = 0
    violations_total = 0
    score_sum = 0.0
    score_n = 0
    for entry in per_paper:
        for name, c in entry["rules"].items():
            slot = rule_total.setdefault(name, {"checks": 0, "violations": 0})
            slot["checks"] += c["checks"]
            slot["violations"] += c["violations"]
        checks_total += entry["checks"]
        violations_total += entry["violations"]
        # paper-level score is well-defined only if at least one check fired
        if entry["checks"] > 0:
            score_sum += entry["consistency_score"]
            score_n += 1
    aggregate_score = (
        1.0 - (violations_total / checks_total)
        if checks_total > 0
        else 1.0
    )
    mean_consistency_score = score_sum / score_n if score_n > 0 else 1.0
    rule_breakdown = {
        name: {
            **stats,
            "violation_rate": (stats["violations"] / stats["checks"]) if stats["checks"] else 0.0,
        }
        for name, stats in rule_total.items()
    }
    return {
        "row_count": len(per_paper),
        "rows_with_at_least_one_check": score_n,
        "checks_total": checks_total,
        "violations_total": violations_total,
        "aggregate_consistency_score": aggregate_score,
        "mean_consistency_score": mean_consistency_score,
        "rule_breakdown": rule_breakdown,
    }


def write_markdown(out_path: Path, payload: Dict[str, Any], top_violations: List[Dict[str, Any]]) -> None:
    agg = payload["aggregate"]
    rb = agg["rule_breakdown"]
    lines: List[str] = [
        "# Claim-Evidence-Flaw Consistency Audit v1",
        "",
        f"- input: `{payload['input']}`",
        f"- row_count: **{agg['row_count']}**",
        f"- rows_with_at_least_one_check: **{agg['rows_with_at_least_one_check']}**",
        f"- checks_total: **{agg['checks_total']}**",
        f"- violations_total: **{agg['violations_total']}**",
        f"- **aggregate_consistency_score** = 1 - (violations / checks) = **{agg['aggregate_consistency_score']:.4f}**",
        f"- **mean_consistency_score** (per-paper averaged, papers with ≥1 check) = **{agg['mean_consistency_score']:.4f}**",
        "",
        "## Rule breakdown",
        "",
        "| rule | checks | violations | violation_rate |",
        "|---|---:|---:|---:|",
    ]
    for name in sorted(rb.keys()):
        s = rb[name]
        lines.append(f"| `{name}` | {s['checks']} | {s['violations']} | {s['violation_rate']:.4f} |")
    lines += [
        "",
        "## Per-paper consistency score (sorted by score asc, top 10 worst)",
        "",
        "| paper_id | checks | violations | consistency_score |",
        "|---|---:|---:|---:|",
    ]
    sorted_per = sorted(
        payload["per_paper"],
        key=lambda r: (r["consistency_score"], -r["violations"], r["paper_id"]),
    )
    for entry in sorted_per[:10]:
        lines.append(
            f"| {entry['paper_id']} | {entry['checks']} | {entry['violations']} | {entry['consistency_score']:.4f} |"
        )
    lines += [
        "",
        "## Sample violations (up to 20)",
        "",
        "| paper_id | rule | detail |",
        "|---|---|---|",
    ]
    for v in top_violations[:20]:
        detail_keys = [k for k in v if k not in {"paper_id", "rule"}]
        detail = ", ".join(f"{k}={v[k]}" for k in detail_keys)
        lines.append(f"| {v.get('paper_id', '')} | `{v.get('rule', '')}` | {detail} |")
    lines += [
        "",
        "## How to interpret",
        "",
        "- `aggregate_consistency_score` is the global ratio. Use this for the paper's main *State Hygiene* number.",
        "- `mean_consistency_score` averages per-paper scores; helpful if a paper has very different scale of state objects.",
        "- These metrics are **rule-based**, not LLM-judged. They quantify *intra-state ID/lifecycle hygiene*, not paper-grounded correctness.",
        "- Pair this with `analyze_mainline_final_v1.py` outputs (support quality, recovery funnel) and `audit_recovery_subfunnel_v1.py` (when available) to form the full hygiene picture.",
        "",
        "Generated by `scripts/audit_cef_consistency_v1.py`.",
    ]
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Claim-Evidence-Flaw Consistency Audit v1 (rule-based, 0 LLM calls).")
    parser.add_argument(
        "--jsonl",
        default="outputs/results_main/review_infer/mainline_final_v1_closure_9b_fulltest39_20260504_gold.jsonl",
        help="Input ReviewState jsonl (one paper per line).",
    )
    parser.add_argument(
        "--output-json",
        default="outputs/results_main/review_infer/cef_consistency_v1.json",
    )
    parser.add_argument(
        "--output-md",
        default="docs/experiments/mainline_current/MAIN_EXPERIMENT_CODE_CLOSURE_V1/CEF_CONSISTENCY_V1.md",
    )
    args = parser.parse_args()

    rows = load_jsonl(Path(args.jsonl))
    per_paper: List[Dict[str, Any]] = []
    top_violations: List[Dict[str, Any]] = []

    for row in rows:
        state = row.get("review_state") or {}
        rule_counts, violations = check_paper(state)
        checks = sum(c["checks"] for c in rule_counts.values())
        viols = sum(c["violations"] for c in rule_counts.values())
        score = 1.0 - (viols / checks) if checks > 0 else 1.0
        for v in violations:
            v["paper_id"] = row.get("paper_id")
            top_violations.append(v)
        per_paper.append({
            "paper_id": row.get("paper_id"),
            "checks": checks,
            "violations": viols,
            "consistency_score": score,
            "rules": rule_counts,
            "violation_records": violations,
        })

    payload = {
        "input": args.jsonl,
        "schema_version": "v1",
        "rule_set": "R1..R6 (see scripts/audit_cef_consistency_v1.py docstring)",
        "per_paper": per_paper,
        "aggregate": aggregate(per_paper),
    }

    out_json = Path(args.output_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    out_md = Path(args.output_md)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    write_markdown(out_md, payload, top_violations)

    summary = {
        "row_count": payload["aggregate"]["row_count"],
        "checks_total": payload["aggregate"]["checks_total"],
        "violations_total": payload["aggregate"]["violations_total"],
        "aggregate_consistency_score": payload["aggregate"]["aggregate_consistency_score"],
        "mean_consistency_score": payload["aggregate"]["mean_consistency_score"],
        "rule_breakdown": payload["aggregate"]["rule_breakdown"],
        "output_json": str(out_json),
        "output_md": str(out_md),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
