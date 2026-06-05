#!/usr/bin/env python3
"""Case Study Pack v1 (offline, deterministic).

Implements **A4** from `PAPER_GAP_REMEDIATION_PLAN.md`.

Generates a single Markdown file containing 4 paper-level case studies that
together illustrate the C-direction framing:

  1. Recovered accept_like      — `jVEoydFOl9` (gold=accept, pred=accept,
                                  final-view=accept_like, real_strong=4).
  2. High-support gold reject   — `9zEBK3E9bX` (gold=reject, pred=reject,
                                  view=borderline_positive, real_strong=3).
  3. False-reject of gold accept— `gzqrANCF4g` (gold=accept, pred=reject,
                                  view=reject_like, real_strong=1, also the
                                  unique CEF consistency violation source).
  4. Blocked recovery           — `ye3NrNrYOY` (gold=reject, 5/5 recovery
                                  emissions ended in worker self-abstain).

Each case section contains:
  - Header (paper_id, gold, system binary, final-view bucket, why it matters).
  - Claims table (id, importance, status, supporting evidence ids).
  - Evidence table (id, source, bucket, stance, strength, bound claim id).
  - Flaws table (id, severity, status, grounding, title).
  - Recovery activity summary (drawn from `audit_recovery_subfunnel_v1.py`).
  - CEF consistency summary (drawn from `audit_cef_consistency_v1.py`).
  - A short narrative paragraph (auto-generated draft; the author should
    expand / edit before paper submission).

The script does NOT make any LLM calls; it is fully reproducible from the
fulltest39 jsonl and the two audit JSONs already produced.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple


CASES: List[Dict[str, str]] = [
    {
        "paper_id": "jVEoydFOl9",
        "type": "Recovered accept_like",
        "headline": "唯一同时满足 binary accept 与 final-view accept_like 的样本；展示系统在 evidence 充分时安全恢复 accept 的能力。",
    },
    {
        "paper_id": "9zEBK3E9bX",
        "type": "High-support gold reject (correct reject, borderline_positive view)",
        "headline": "系统正确拒绝 gold reject 论文，但 evidence 层形成 3 条 real strong support；hard-negative grounding 不足，因此 final-view 落入 borderline_positive 而非 reject_like。",
    },
    {
        "paper_id": "gzqrANCF4g",
        "type": "False-reject of gold accept (reject_like view)",
        "headline": "gold accept 但 system 误判为 reject_like。同时是 CEF Consistency 唯一违规来源（2 条 flaw 引用了已被替换的 evidence id），可串联 State Hygiene 章节。",
    },
    {
        "paper_id": "ye3NrNrYOY",
        "type": "Blocked recovery (worker self-abstain dominant)",
        "headline": "5 个 recovery turn 全部是 worker self-abstain（action='blocked'），体现 BLOCKED_BY_POLICY 的真实语义：worker 在证据不足时主动拒绝构造 state mutation。",
    },
]

SUPPORT_STANCES = {"supports", "partially_supports"}


def norm(s: Any) -> str:
    return str(s or "").strip().lower()


def is_real_claim(cid: Any) -> bool:
    s = norm(cid)
    return bool(s) and "fallback" not in s and "general" not in s


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


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


def find_final_view_label(final_report: str) -> str:
    if not final_report:
        return "(not in final_report)"
    for ln in final_report.splitlines():
        if "Final Recommendation View" in ln:
            return ln.split(":", 1)[-1].strip()
    return "(not in final_report)"


def find_recommendation_reason(final_report: str) -> str:
    if not final_report:
        return ""
    capture = False
    out = []
    for ln in final_report.splitlines():
        if ln.startswith("- Recommendation Reason"):
            capture = True
            out.append(ln.split(":", 1)[-1].strip())
        elif capture and ln.startswith("- "):
            break
        elif capture and ln.strip():
            out.append(ln.strip())
    return " ".join(out)[:400]


def support_summary(state: Dict[str, Any]) -> Dict[str, int]:
    real_strong = nonabstract = empirical = method = 0
    for ev in state.get("evidence_map") or []:
        if norm(ev.get("stance")) not in SUPPORT_STANCES:
            continue
        if norm(ev.get("strength")) != "strong":
            continue
        if not is_real_claim(ev.get("claim_id")):
            continue
        real_strong += 1
        bucket = norm(ev.get("support_source_bucket"))
        if bucket and bucket != "abstract":
            nonabstract += 1
        if bucket in {"empirical", "result_or_experiment", "table_or_figure"}:
            empirical += 1
        if bucket == "method_or_approach":
            method += 1
    return {
        "real_strong": real_strong,
        "nonabstract_strong": nonabstract,
        "empirical_strong": empirical,
        "method_strong": method,
    }


def recovery_summary(turn_logs: List[Dict[str, Any]]) -> Dict[str, Any]:
    emitted = self_abstain = validator_rejected = committed = 0
    blocked_reasons: List[str] = []
    for t in turn_logs or []:
        if not t.get("recovery_patch_emitted"):
            continue
        emitted += 1
        code = t.get("recovery_failure_code") or ""
        is_committed = bool(t.get("recovery_patch_committed") or t.get("recovery_committed"))
        if is_committed:
            committed += 1
        elif code == "BLOCKED_BY_POLICY":
            self_abstain += 1
            txt = t.get("recovery_blocked_by") or t.get("recovery_failure_message") or ""
            if txt:
                blocked_reasons.append(txt[:160])
        elif code:
            validator_rejected += 1
    return {
        "emitted": emitted,
        "worker_self_abstain": self_abstain,
        "validator_rejected": validator_rejected,
        "committed": committed,
        "sample_blocked_reasons": blocked_reasons[:3],
    }


def build_claims_table(state: Dict[str, Any]) -> List[str]:
    claims = state.get("claims") or []
    if not claims:
        return ["_(no claims)_"]
    lines = ["| claim_id | importance | status | supporting_evidence_ids |", "|---|---|---|---|"]
    for c in claims:
        sids = ", ".join(c.get("supporting_evidence_ids") or []) or "_∅_"
        lines.append(
            f"| `{c.get('claim_id', '')}` | {c.get('importance', '')} | "
            f"{c.get('status', '')} | {sids} |"
        )
    return lines


def build_evidence_table(state: Dict[str, Any]) -> List[str]:
    ev = state.get("evidence_map") or []
    if not ev:
        return ["_(no evidence)_"]
    lines = [
        "| evidence_id | source | bucket | stance | strength | claim_id |",
        "|---|---|---|---|---|---|",
    ]
    for e in ev:
        lines.append(
            f"| `{e.get('evidence_id', '')}` | "
            f"{(e.get('source') or '')[:40]} | "
            f"{e.get('support_source_bucket', '')} | "
            f"{e.get('stance', '')} | {e.get('strength', '')} | "
            f"`{e.get('claim_id', '')}` |"
        )
    return lines


def build_flaws_table(state: Dict[str, Any]) -> List[str]:
    fl = state.get("flaw_candidates") or []
    if not fl:
        return ["_(no flaws)_"]
    lines = [
        "| flaw_id | severity | status | grounding | related_claim_ids | title |",
        "|---|---|---|---|---|---|",
    ]
    for f in fl:
        title = (f.get("title") or "").replace("\n", " ").replace("|", "\\|")[:100]
        rcid = ", ".join(f.get("related_claim_ids") or []) or "_∅_"
        lines.append(
            f"| `{f.get('flaw_id', '')}` | {f.get('severity', '')} | "
            f"{f.get('status', '')} | {f.get('grounding_status', '')} | {rcid} | "
            f"{title} |"
        )
    return lines


def cef_for_paper(cef_payload: Dict[str, Any], paper_id: str) -> Tuple[float, int, int, List[Dict[str, Any]]]:
    for entry in cef_payload.get("per_paper") or []:
        if entry.get("paper_id") == paper_id:
            return (
                entry.get("consistency_score", 1.0),
                entry.get("checks", 0),
                entry.get("violations", 0),
                entry.get("violation_records") or [],
            )
    return 1.0, 0, 0, []


def auto_narrative(case_meta: Dict[str, str], gold: str, pred: str, view: str, support: Dict[str, int],
                   rec: Dict[str, Any], cef: Tuple[float, int, int, List[Dict[str, Any]]],
                   reason: str) -> List[str]:
    """Generate a draft narrative paragraph; author will refine before paper submission."""
    score, checks, vios, _ = cef
    case_type = case_meta["type"]
    pid = case_meta["paper_id"]
    paragraphs: List[str] = []

    paragraphs.append(
        f"**Why this case matters**: {case_meta['headline']}"
    )

    correctness = "correct" if pred == gold else ("false reject" if gold == "accept" else "false accept")
    paragraphs.append(
        f"**Binary decision**: gold = `{gold}`, system = `{pred}` → "
        f"**{correctness}**. Final-view bucket: **{view}**."
    )

    paragraphs.append(
        f"**Evidence formation**: real_strong = {support['real_strong']}, "
        f"non-abstract = {support['nonabstract_strong']}, "
        f"empirical = {support['empirical_strong']}, "
        f"method = {support['method_strong']}. "
        f"This is the support footprint the final-view recommendation acted on."
    )

    paragraphs.append(
        f"**Recovery activity**: emitted = {rec['emitted']}, "
        f"worker self-abstain = {rec['worker_self_abstain']}, "
        f"validator rejected = {rec['validator_rejected']}, "
        f"committed = {rec['committed']}. "
        + (
            "Sample worker abstain reasons: "
            + "; ".join(f"\"{r}\"" for r in rec["sample_blocked_reasons"])
            if rec["sample_blocked_reasons"] else
            "No worker self-abstain text captured."
        )
    )

    paragraphs.append(
        f"**State auditability**: CEF consistency score = {score:.4f} "
        f"(violations / checks = {vios}/{checks}). "
        + (
            f"This paper carries the only R2 violations in fulltest39 — flaw records "
            "reference an evidence id (`evidence-1-turn-3`) that has been replaced "
            "in the final ReviewState. The audit surfaces this lifecycle drift "
            "rather than hiding it; this is precisely the kind of intra-state "
            "inconsistency the C-direction *auditability* claim is intended to expose."
            if pid == "gzqrANCF4g" else
            "ID and lifecycle invariants hold for this paper."
        )
    )

    if reason:
        paragraphs.append(f"**System recommendation reason**: {reason}")

    paragraphs.append(
        "**Author note**: the above paragraphs are auto-generated drafts; "
        "expand with paper-specific contribution / weakness narrative before "
        "submission. The structured tables above are the authoritative data."
    )
    return paragraphs


def render_case(row: Dict[str, Any], case_meta: Dict[str, str], gold: str,
                cef_payload: Dict[str, Any], rec_payload: Dict[str, Any]) -> List[str]:
    pid = row["paper_id"]
    state = row.get("review_state") or {}
    final_report = row.get("final_report") or ""
    pred = norm(row.get("final_decision"))
    view = find_final_view_label(final_report)
    reason = find_recommendation_reason(final_report)
    support = support_summary(state)
    rec = recovery_summary(row.get("turn_logs") or [])
    cef = cef_for_paper(cef_payload, pid)

    lines: List[str] = [
        "",
        f"## Case — {case_meta['type']}",
        "",
        f"- **paper_id**: `{pid}`",
        f"- **gold**: `{gold}`",
        f"- **system binary**: `{pred}` ({'✓' if pred == gold else '✗ false-' + ('reject' if gold == 'accept' else 'accept')})",
        f"- **final-view recommendation**: `{view}`",
        f"- **headline**: {case_meta['headline']}",
        "",
        "### Claims",
        "",
        *build_claims_table(state),
        "",
        "### Evidence",
        "",
        *build_evidence_table(state),
        "",
        "### Flaws",
        "",
        *build_flaws_table(state),
        "",
        "### Recovery funnel (this paper)",
        "",
        f"- emitted: **{rec['emitted']}**",
        f"- worker self-abstain (BLOCKED_BY_POLICY): **{rec['worker_self_abstain']}**",
        f"- validator rejected: **{rec['validator_rejected']}**",
        f"- committed: **{rec['committed']}**",
    ]
    if rec["sample_blocked_reasons"]:
        lines.append("- sample worker self-abstain reasons:")
        for r in rec["sample_blocked_reasons"]:
            lines.append(f"  - _\"{r}\"_")
    score, checks, vios, vrs = cef
    lines += [
        "",
        "### State auditability (CEF consistency, this paper)",
        "",
        f"- consistency_score = **{score:.4f}**",
        f"- checks = {checks}, violations = {vios}",
    ]
    if vrs:
        lines.append("- violation records:")
        for v in vrs[:6]:
            payload = ", ".join(f"{k}={v[k]}" for k in v if k not in {"paper_id", "rule"})
            lines.append(f"  - `{v.get('rule')}`: {payload}")
    lines += ["", "### Narrative (draft; author to refine)", ""]
    for para in auto_narrative(case_meta, gold, pred, view, support, rec, cef, reason):
        lines.append(para)
        lines.append("")
    return lines


def main() -> None:
    parser = argparse.ArgumentParser(description="Case Study Pack v1 (4 typical cases for the C-direction paper).")
    parser.add_argument(
        "--jsonl",
        default="outputs/results_main/review_infer/mainline_final_v1_closure_9b_fulltest39_20260504_gold.jsonl",
    )
    parser.add_argument(
        "--gold-labels",
        default="docs/experiments/mainline_current/MAIN_EXPERIMENT_CODE_CLOSURE_V1/fulltest39_gold_labels_locked_20260504.json",
    )
    parser.add_argument(
        "--cef-json",
        default="outputs/results_main/review_infer/cef_consistency_v1.json",
    )
    parser.add_argument(
        "--recovery-json",
        default="outputs/results_main/review_infer/recovery_subfunnel_v1.json",
    )
    parser.add_argument(
        "--output-md",
        default="docs/experiments/mainline_current/MAIN_EXPERIMENT_CODE_CLOSURE_V1/CASE_STUDY_PACK_V1.md",
    )
    args = parser.parse_args()

    rows = {row["paper_id"]: row for row in load_jsonl(Path(args.jsonl))}
    gold_map = load_gold_map(Path(args.gold_labels))
    cef_payload = load_json(Path(args.cef_json))
    rec_payload = load_json(Path(args.recovery_json))  # currently used only for documentation

    out: List[str] = [
        "# Case Study Pack v1 (4 representative samples)",
        "",
        f"- input: `{args.jsonl}`",
        f"- gold labels: `{args.gold_labels}` (locked)",
        f"- CEF consistency: `{args.cef_json}`",
        f"- recovery sub-funnel: `{args.recovery_json}`",
        "",
        "Each case is intentionally one of four representative *types* required by the C-direction Limitation audit (`PAPER_C_DIRECTION_LIMITATION_AUDIT.md` 不足七 退路 + INTEGRATED #3). Together they show: a successful conservative accept, a correct reject with positive support, a false reject of a gold accept, and a recovery worker self-abstain. The auto-generated narrative paragraphs are drafts; the author refines them before submission.",
        "",
        "## Index",
        "",
        "| # | type | paper_id |",
        "|---|---|---|",
    ]
    for i, c in enumerate(CASES, 1):
        out.append(f"| {i} | {c['type']} | `{c['paper_id']}` |")

    for case_meta in CASES:
        pid = case_meta["paper_id"]
        row = rows.get(pid)
        if not row:
            out += [f"\n## (missing) `{pid}` not found in input jsonl"]
            continue
        gold = gold_map.get(pid, "?")
        out += render_case(row, case_meta, gold, cef_payload, rec_payload)

    out += [
        "",
        "---",
        "",
        f"Generated by `scripts/build_case_study_pack_v1.py`. Cases selected per the C-direction Limitation audit. Numbers reproducible from the inputs above.",
    ]
    out_path = Path(args.output_md)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(json.dumps({
        "cases": [{"paper_id": c["paper_id"], "type": c["type"]} for c in CASES],
        "output_md": str(out_path),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
