"""Audit real-strong support smoke runs.

Reads a smoke jsonl produced by ``review_runner`` and emits a per-paper
table that answers:

1. ``missing_verified_quote`` 是否在新跑里下降。
2. quote-bank claim-overlap fallback 是否真的为 real strong 贡献。
3. semantic-weak claim-overlap promotion 是否被 hygiene 卡住。
4. medium → strong promotion 在新跑里是否产生 real strong。

The script is read-only; it never re-runs the model. Pair with
``scripts/export_hygiene_metrics_v1.py`` for the wider hygiene CSV/JSON.
"""
from __future__ import annotations

import argparse
import copy
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agent_system.environments.env_package.review.state import build_decision_hygiene_view


def _safe_int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _hygiene_for_record(record: Dict[str, Any]) -> Dict[str, Any]:
    state = copy.deepcopy(record.get("review_state") or {})
    state.pop("decision_hygiene", None)
    if isinstance(state.get("state_audit"), dict):
        state["state_audit"].pop("decision_hygiene", None)
    return build_decision_hygiene_view(state).get("decision_hygiene", {}) or {}


def _baseline_real_strong(baseline_path: Path) -> Dict[str, int]:
    if not baseline_path or not baseline_path.exists():
        return {}
    out: Dict[str, int] = {}
    with baseline_path.open("r", encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            record = json.loads(line)
            paper_id = str(record.get("paper_id") or "")
            if not paper_id:
                continue
            hygiene = _hygiene_for_record(record)
            out[paper_id] = _safe_int(hygiene.get("real_strong_support_total"))
    return out


def _row_for_record(record: Dict[str, Any], baseline: Dict[str, int]) -> Dict[str, Any]:
    hygiene = _hygiene_for_record(record)
    survival = hygiene.get("support_survival_summary", {}) or {}
    real_strong = _safe_int(hygiene.get("real_strong_support_total"))
    fb_used = _safe_int(hygiene.get("quote_bank_claim_overlap_fallback_used_count"))
    fb_real_strong = _safe_int(hygiene.get("quote_bank_claim_overlap_fallback_real_strong_count"))
    fb_mismatch = _safe_int(hygiene.get("quote_bank_claim_overlap_fallback_semantic_mismatch_count"))
    wp_used = _safe_int(hygiene.get("semantic_weak_promotion_used_count"))
    wp_real_strong = _safe_int(hygiene.get("semantic_weak_promotion_real_strong_count"))
    sp_used = _safe_int(hygiene.get("strength_promotion_from_medium_count"))
    sp_real_strong = _safe_int(hygiene.get("strength_promotion_from_medium_real_strong_count"))
    drops = survival.get("drop_by_final_reason", {}) or {}
    paper_id = str(record.get("paper_id") or "")
    return {
        "paper_id": paper_id,
        "old_real_strong": baseline.get(paper_id, -1),
        "new_real_strong": real_strong,
        "delta": real_strong - baseline.get(paper_id, real_strong),
        "fallback_used": fb_used,
        "fallback_real_strong": fb_real_strong,
        "fallback_semantic_mismatch": fb_mismatch,
        "weak_promotion_used": wp_used,
        "weak_promotion_real_strong": wp_real_strong,
        "medium_to_strong_used": sp_used,
        "medium_to_strong_real_strong": sp_real_strong,
        "missing_verified_quote_drops": _safe_int(drops.get("missing_verified_quote")),
        "semantic_mismatch_drops": _safe_int(drops.get("semantic_mismatch")),
        "weak_support_depth_drops": _safe_int(drops.get("weak_support_depth")),
        "duplicate_quote_drops": _safe_int(drops.get("duplicate_quote")),
        "fallback_case_sample": hygiene.get("quote_bank_claim_overlap_fallback_case_sample", []) or [],
        "weak_promotion_case_sample": hygiene.get("semantic_weak_promotion_case_sample", []) or [],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--jsonl", required=True, help="Smoke jsonl produced by review_runner.")
    parser.add_argument("--baseline-jsonl", default="", help="Optional baseline jsonl for delta computation.")
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--output-md", required=True)
    args = parser.parse_args()

    smoke_path = Path(args.jsonl)
    baseline = _baseline_real_strong(Path(args.baseline_jsonl)) if args.baseline_jsonl else {}

    rows: List[Dict[str, Any]] = []
    with smoke_path.open("r", encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            record = json.loads(line)
            rows.append(_row_for_record(record, baseline))

    aggregate = {
        "smoke_jsonl": str(smoke_path),
        "baseline_jsonl": str(args.baseline_jsonl or ""),
        "row_count": len(rows),
        "sum_real_strong": sum(r["new_real_strong"] for r in rows),
        "papers_with_real_strong": sum(1 for r in rows if r["new_real_strong"] > 0),
        "fallback_used_total": sum(r["fallback_used"] for r in rows),
        "fallback_real_strong_total": sum(r["fallback_real_strong"] for r in rows),
        "fallback_semantic_mismatch_total": sum(r["fallback_semantic_mismatch"] for r in rows),
        "weak_promotion_used_total": sum(r["weak_promotion_used"] for r in rows),
        "weak_promotion_real_strong_total": sum(r["weak_promotion_real_strong"] for r in rows),
        "medium_to_strong_used_total": sum(r["medium_to_strong_used"] for r in rows),
        "medium_to_strong_real_strong_total": sum(r["medium_to_strong_real_strong"] for r in rows),
        "missing_verified_quote_drops_total": sum(r["missing_verified_quote_drops"] for r in rows),
        "semantic_mismatch_drops_total": sum(r["semantic_mismatch_drops"] for r in rows),
        "weak_support_depth_drops_total": sum(r["weak_support_depth_drops"] for r in rows),
        "duplicate_quote_drops_total": sum(r["duplicate_quote_drops"] for r in rows),
        "rows": rows,
    }
    Path(args.output_json).write_text(json.dumps(aggregate, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    md_lines: List[str] = []
    md_lines.append("# Real-Strong Smoke Audit")
    md_lines.append("")
    md_lines.append(f"- smoke jsonl: `{smoke_path}`")
    if args.baseline_jsonl:
        md_lines.append(f"- baseline jsonl: `{args.baseline_jsonl}`")
    md_lines.append(f"- rows: {len(rows)}")
    md_lines.append(
        f"- sum real strong: {aggregate['sum_real_strong']} (papers with real strong: {aggregate['papers_with_real_strong']})"
    )
    md_lines.append(
        f"- fallback used / real strong / semantic mismatch: {aggregate['fallback_used_total']} / {aggregate['fallback_real_strong_total']} / {aggregate['fallback_semantic_mismatch_total']}"
    )
    md_lines.append(
        f"- weak promotion used / real strong: {aggregate['weak_promotion_used_total']} / {aggregate['weak_promotion_real_strong_total']}"
    )
    md_lines.append(
        f"- medium\u2192strong used / real strong: {aggregate['medium_to_strong_used_total']} / {aggregate['medium_to_strong_real_strong_total']}"
    )
    md_lines.append(
        f"- drops: missing_quote={aggregate['missing_verified_quote_drops_total']}, semantic_mismatch={aggregate['semantic_mismatch_drops_total']}, weak_depth={aggregate['weak_support_depth_drops_total']}, duplicate={aggregate['duplicate_quote_drops_total']}"
    )
    md_lines.append("")
    md_lines.append("## Per-paper table")
    md_lines.append("")
    md_lines.append(
        "| paper | old | new | Δ | fb_used | fb_real | fb_mismatch | wp_used | wp_real | m2s_used | m2s_real | miss_q | sem_mis | weak_depth | dup |"
    )
    md_lines.append(
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"
    )
    for r in rows:
        md_lines.append(
            "| {paper_id} | {old} | {new} | {delta} | {fb_used} | {fb_real} | {fb_mis} | {wp_used} | {wp_real} | {m2s_used} | {m2s_real} | {miss} | {sem} | {weak} | {dup} |".format(
                paper_id=r["paper_id"],
                old=("-" if r["old_real_strong"] < 0 else r["old_real_strong"]),
                new=r["new_real_strong"],
                delta=("-" if r["old_real_strong"] < 0 else r["delta"]),
                fb_used=r["fallback_used"],
                fb_real=r["fallback_real_strong"],
                fb_mis=r["fallback_semantic_mismatch"],
                wp_used=r["weak_promotion_used"],
                wp_real=r["weak_promotion_real_strong"],
                m2s_used=r["medium_to_strong_used"],
                m2s_real=r["medium_to_strong_real_strong"],
                miss=r["missing_verified_quote_drops"],
                sem=r["semantic_mismatch_drops"],
                weak=r["weak_support_depth_drops"],
                dup=r["duplicate_quote_drops"],
            )
        )
    md_lines.append("")
    md_lines.append("## Fallback case sample (first 10)")
    md_lines.append("")
    sample_count = 0
    for r in rows:
        for case in r["fallback_case_sample"]:
            if sample_count >= 10:
                break
            md_lines.append(
                f"- **{r['paper_id']}**: claim={case.get('claim_id')} bucket={case.get('quote_bank_claim_overlap_fallback_source_bucket')} score={case.get('quote_bank_claim_overlap_fallback_score')} sem={case.get('semantic_grounding_label')} drop={case.get('final_drop_reason')} included={case.get('included_in_final_view')}"
            )
            md_lines.append(
                f"    - quote: {(case.get('raw_quote') or '')[:160]!r}"
            )
            md_lines.append(
                f"    - agent_quote: {(case.get('agent_raw_quote') or '')[:160]!r}"
            )
            sample_count += 1
        if sample_count >= 10:
            break
    md_lines.append("")
    md_lines.append("## Weak-promotion case sample (first 10)")
    md_lines.append("")
    sample_count = 0
    for r in rows:
        for case in r["weak_promotion_case_sample"]:
            if sample_count >= 10:
                break
            md_lines.append(
                f"- **{r['paper_id']}**: claim={case.get('claim_id')} bucket={case.get('source_bucket')} overlap={case.get('verified_claim_overlap_score')} sem_score={case.get('semantic_alignment_score')} sem={case.get('semantic_grounding_label')} drop={case.get('final_drop_reason')} included={case.get('included_in_final_view')}"
            )
            sample_count += 1
        if sample_count >= 10:
            break
    Path(args.output_md).write_text("\n".join(md_lines) + "\n", encoding="utf-8")
    print(json.dumps({"row_count": len(rows), "output_json": args.output_json, "output_md": args.output_md}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
