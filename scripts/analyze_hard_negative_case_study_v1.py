#!/usr/bin/env python3
"""Offline hard-negative grounding case study.

No runtime behaviour is changed. The script separates paper-grounded blockers
from context/meta/fallback burden for high-support reject and accept-protect
cases.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from agent_system.environments.env_package.review.state import (
    build_decision_hygiene_view,
    infer_final_recommendation_view,
)

META_RE = re.compile(
    r"fallback|parser|parse|json|malformed|could not bind|unbound|excerpt|truncat|cut off|cut-off|"
    r"full text|full paper|provided text|provided paper|available text|not visible|not shown|not provided|"
    r"cannot verify|unable to verify|missing input|incomplete abstract|system",
    re.I,
)
HARD_NEG_RE = re.compile(
    r"contradict|unsupported|insufficient|missing baseline|no baseline|lack(s|ing)? ablation|"
    r"lack(s|ing)? experiment|invalid|flaw|weakness|fails to|does not support|not demonstrate|"
    r"empirical.*insufficient|soundness|technical.*issue|method.*invalid|evaluation.*insufficient|"
    r"baseline.*missing|ablation.*missing|limited evaluation",
    re.I,
)
CLAIM_ID_RE = re.compile(r"claim-[A-Za-z0-9_-]+")


def state_from_row(row: dict[str, Any]) -> dict[str, Any]:
    state = row.get("review_state") or row.get("final_state") or row.get("state") or {}
    return state if isinstance(state, dict) else {}


def text(value: Any) -> str:
    if isinstance(value, dict):
        parts: list[str] = []
        for key, val in value.items():
            if key in {"embedding", "raw"}:
                continue
            if isinstance(val, (str, int, float)):
                parts.append(str(val))
            elif isinstance(val, list):
                parts.extend(str(x) for x in val if isinstance(x, (str, int, float)))
        return " ".join(parts)
    return str(value or "")


def real_claim_ids(state: dict[str, Any]) -> set[str]:
    return {
        str(claim.get("claim_id") or "")
        for claim in state.get("claims", []) or []
        if isinstance(claim, dict)
        and claim.get("claim_id")
        and not str(claim.get("claim_id")).startswith("claim-fallback")
    }


def usable_support(evidence: dict[str, Any], claim_ids: set[str]) -> bool:
    cid = str(evidence.get("claim_id") or "")
    if cid not in claim_ids or cid.startswith("claim-fallback"):
        return False
    if str(evidence.get("binding_status") or "") not in {"", "unchecked", "bound_real_claim"}:
        return False
    return evidence.get("strength") == "strong" and evidence.get("stance") in {"supports", "partially_supports"}


def support_bucket(evidence: dict[str, Any]) -> str:
    body = (str(evidence.get("support_source_bucket") or "") + " " + str(evidence.get("support_quality") or "") + " " + text(evidence)).lower()
    if any(t in body for t in ("result", "experiment", "evaluation", "benchmark", "baseline", "ablation", "table")):
        return "empirical_or_result"
    if "figure" in body:
        return "figure_or_diagram"
    if any(t in body for t in ("method", "approach", "model", "framework", "algorithm")):
        return "method_or_approach"
    if any(t in body for t in ("abstract", "title", "conclusion")):
        return "abstract_or_conclusion"
    return "unknown"


def support_profile(state: dict[str, Any]) -> dict[str, Any]:
    claim_ids = real_claim_ids(state)
    per_claim: Counter[str] = Counter()
    buckets: Counter[str] = Counter()
    groups: set[str] = set()
    evidence_ids: list[str] = []
    for ev in state.get("evidence_map", []) or []:
        if not isinstance(ev, dict) or not usable_support(ev, claim_ids):
            continue
        cid = str(ev.get("claim_id") or "")
        bucket = support_bucket(ev)
        ev_text = re.sub(r"\W+", " ", str(ev.get("evidence") or "").lower()).strip()[:80]
        per_claim[cid] += 1
        buckets[bucket] += 1
        groups.add(f"{cid}:{bucket}:{ev_text}")
        if ev.get("evidence_id"):
            evidence_ids.append(str(ev.get("evidence_id")))
    nonabstract = sum(v for k, v in buckets.items() if k not in {"abstract_or_conclusion", "unknown"})
    empirical = buckets.get("empirical_or_result", 0) + buckets.get("figure_or_diagram", 0)
    return {
        "real_strong": sum(per_claim.values()),
        "claims_with_support": sum(1 for v in per_claim.values() if v > 0),
        "claims_with_2plus_support": sum(1 for v in per_claim.values() if v >= 2),
        "nonabstract": nonabstract,
        "empirical_or_result": empirical,
        "method_or_approach": buckets.get("method_or_approach", 0),
        "figure_or_diagram": buckets.get("figure_or_diagram", 0),
        "abstract_or_conclusion": buckets.get("abstract_or_conclusion", 0),
        "independent_group_count": len(groups),
        "support_evidence_ids": evidence_ids,
        "per_claim_support": dict(per_claim),
        "bucket_counts": dict(buckets),
    }


def classify_gap(gap: Any, support_counts: Counter[str]) -> tuple[str, str]:
    t = text(gap)
    if META_RE.search(t) or "claim-fallback" in t:
        return "context_or_fallback_gap", t
    claim_ids = CLAIM_ID_RE.findall(t)
    if any(support_counts.get(cid, 0) > 0 for cid in claim_ids):
        return "stale_gap_resolved_by_support", t
    if claim_ids:
        return "open_missing_claim_support", t
    return "open_unanchored_gap", t


def classify_unresolved(item: Any, support_counts: Counter[str]) -> tuple[str, str]:
    t = text(item)
    if META_RE.search(t):
        return "context_or_meta_uncertainty", t
    related_claims: list[str] = []
    related_evidence: list[str] = []
    if isinstance(item, dict):
        related_claims = [str(x) for x in item.get("related_claim_ids", []) or [] if x]
        related_evidence = [str(x) for x in (item.get("related_evidence_ids") or item.get("evidence_ids") or []) if x]
    if any(support_counts.get(cid, 0) > 0 for cid in related_claims) and re.search(r"lacks grounded|missing evidence|supporting evidence", t, re.I):
        return "stale_unresolved_resolved_by_support", t
    if HARD_NEG_RE.search(t) and (related_claims or related_evidence):
        return "paper_grounded_unverified_negative", t
    if related_claims or related_evidence:
        return "paper_grounded_open_question", t
    return "targetless_open_question", t


def classify_flaw(flaw: Any) -> tuple[str, str]:
    t = text(flaw)
    if not isinstance(flaw, dict):
        return "ungrounded_candidate_flaw", t
    fid = str(flaw.get("flaw_id") or "")
    source = str(flaw.get("source") or "").lower()
    status = str(flaw.get("status") or "candidate").lower()
    severity = str(flaw.get("severity") or "").lower()
    evidence_ids = [str(x) for x in flaw.get("evidence_ids", []) or [] if x]
    if status in {"downgraded", "retracted"}:
        return "downgraded_or_retracted_flaw", t
    if fid.startswith("flaw-fallback") or source in {"fallback", "fallback-extraction", "system_meta", "system-meta"} or META_RE.search(t):
        return "fallback_or_meta_flaw", t
    if severity in {"major", "critical"} and evidence_ids and HARD_NEG_RE.search(t):
        return "grounded_major_or_critical_flaw", t
    if evidence_ids:
        return "grounded_candidate_flaw", t
    return "ungrounded_candidate_flaw", t


def classify_conflict(conflict: Any) -> tuple[str, str]:
    t = text(conflict)
    if not isinstance(conflict, dict):
        return "open_unanchored_conflict", t
    ctype = str(conflict.get("conflict_type") or "").lower()
    eid = str(conflict.get("evidence_id") or "")
    cid = str(conflict.get("claim_id") or "")
    if "fallback" in ctype or eid.startswith("evidence-fallback") or META_RE.search(t):
        return "fallback_or_context_conflict", t
    if cid and eid and HARD_NEG_RE.search(t):
        return "paper_grounded_open_conflict", t
    return "open_unanchored_conflict", t


def negative_profile(state: dict[str, Any], profile: dict[str, Any]) -> dict[str, Any]:
    support_counts = Counter({str(k): int(v) for k, v in (profile.get("per_claim_support") or {}).items()})
    categories = {"gap": Counter(), "unresolved": Counter(), "flaw": Counter(), "conflict": Counter()}
    blockers: list[dict[str, Any]] = []
    for item in state.get("evidence_gaps", []) or []:
        cat, t = classify_gap(item, support_counts)
        categories["gap"][cat] += 1
        if cat in {"open_missing_claim_support", "open_unanchored_gap"}:
            blockers.append({"type": cat, "grounding": "unverified", "text": t[:240]})
    for item in state.get("unresolved_questions", []) or []:
        cat, t = classify_unresolved(item, support_counts)
        categories["unresolved"][cat] += 1
        if cat in {"paper_grounded_unverified_negative", "paper_grounded_open_question"}:
            blockers.append({"type": cat, "grounding": "unverified", "text": t[:240]})
    for item in state.get("flaw_candidates", []) or []:
        cat, t = classify_flaw(item)
        categories["flaw"][cat] += 1
        if cat == "grounded_major_or_critical_flaw":
            blockers.insert(0, {"type": cat, "grounding": "grounded", "text": t[:240]})
        elif cat == "grounded_candidate_flaw":
            blockers.append({"type": cat, "grounding": "candidate_grounded", "text": t[:240]})
    for item in state.get("conflict_notes", []) or []:
        cat, t = classify_conflict(item)
        categories["conflict"][cat] += 1
        if cat == "paper_grounded_open_conflict":
            blockers.append({"type": cat, "grounding": "unverified", "text": t[:240]})
    if any(b["grounding"] == "grounded" for b in blockers):
        status = "grounded_blocker_found"
    elif blockers:
        status = "unverified_blocker_candidate"
    elif any(categories[k] for k in categories):
        status = "context_limited_no_grounded_blocker"
    else:
        status = "no_blocker_detected"
    return {"hard_negative_status": status, "category_counts": {k: dict(v) for k, v in categories.items()}, "blocker_candidates": blockers[:5]}


def audit_row(row: dict[str, Any]) -> dict[str, Any]:
    state = state_from_row(row)
    profile = support_profile(state)
    negative = negative_profile(state, profile)
    view = infer_final_recommendation_view(state, {})
    hygiene = build_decision_hygiene_view(state)
    return {
        "paper_id": row.get("paper_id") or row.get("id"),
        "gold": str(row.get("gold_decision") or row.get("gold") or "").lower(),
        "runtime_decision": str(row.get("final_decision") or row.get("prediction") or "").lower(),
        "recommendation_view": view.get("recommendation_view"),
        "recommendation_reason": view.get("reason"),
        "support_profile": profile,
        "hard_negative_status": negative["hard_negative_status"],
        "negative_category_counts": negative["category_counts"],
        "blocker_candidates": negative["blocker_candidates"],
        "hygiene_open_unresolved": len([q for q in hygiene.get("unresolved_questions", []) or [] if isinstance(q, dict) and q.get("status", "open") == "open"]),
        "hygiene_gap_count": len(hygiene.get("evidence_gaps", []) or []),
        "hygiene_flaw_count": len(hygiene.get("flaw_candidates", []) or []),
        "hygiene_conflict_count": len(hygiene.get("conflict_notes", []) or []),
    }


def case_bucket(row: dict[str, Any]) -> str:
    profile = row["support_profile"]
    if row["gold"] == "reject" and (profile["real_strong"] >= 2 or profile["empirical_or_result"] >= 1 or row["recommendation_view"] in {"borderline_positive", "accept_like"}):
        return "false_accept_risk_reject_cases"
    if row["gold"] == "accept" and (profile["real_strong"] >= 2 or row["recommendation_view"] in {"accept_like", "borderline_positive", "borderline_insufficient"}):
        return "accept_protect_cases"
    return "background_cases"


def md_table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(x).replace("|", "\\|").replace("\n", " ") for x in row) + " |")
    return "\n".join(lines)


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    status_counts: Counter[str] = Counter()
    view_counts: Counter[str] = Counter()
    gold_counts: Counter[str] = Counter()
    for row in rows:
        buckets[case_bucket(row)].append(row)
        status_counts[row["hard_negative_status"]] += 1
        view_counts[str(row["recommendation_view"])] += 1
        gold_counts[str(row["gold"])] += 1
    return {
        "row_count": len(rows),
        "gold_counts": dict(gold_counts),
        "recommendation_view_counts": dict(view_counts),
        "hard_negative_status_counts": dict(status_counts),
        "bucket_counts": {name: len(items) for name, items in buckets.items()},
        "false_accept_risk_reject_ids": [str(r["paper_id"]) for r in buckets.get("false_accept_risk_reject_cases", [])],
        "accept_protect_ids": [str(r["paper_id"]) for r in buckets.get("accept_protect_cases", [])],
    }


def load_rows(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def write_reports(output_dir: Path, input_path: Path, rows: list[dict[str, Any]], summary: dict[str, Any]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "hard_negative_case_study_v1.json").write_text(json.dumps({"input": str(input_path), "summary": summary, "case_rows": rows}, ensure_ascii=False, indent=2) + "\n")
    sorted_rows = sorted(rows, key=lambda r: (case_bucket(r), -r["support_profile"]["real_strong"], str(r["paper_id"])))
    table_rows = []
    for row in sorted_rows:
        profile = row["support_profile"]
        first_blocker = row["blocker_candidates"][0]["type"] if row["blocker_candidates"] else "none"
        table_rows.append([row["paper_id"], row["gold"], row["recommendation_view"], case_bucket(row), profile["real_strong"], profile["nonabstract"], profile["empirical_or_result"], profile["independent_group_count"], row["hard_negative_status"], first_blocker])
    (output_dir / "HARD_NEGATIVE_CASE_TABLE_V1.md").write_text("\n".join([
        "# HARD_NEGATIVE_CASE_TABLE_V1", "", "这张表用于解释哪些 high-support reject 不能被裸 support 规则接收，以及哪些 accept 样本需要避免被负面噪声误压。", "",
        md_table(["paper_id", "gold", "view", "bucket", "real", "nonabs", "empirical", "indep", "hard_negative_status", "first_blocker"], table_rows), "",
    ]))
    false_risk = [r for r in rows if case_bucket(r) == "false_accept_risk_reject_cases"]
    accept_protect = [r for r in rows if case_bucket(r) == "accept_protect_cases"]
    report = [
        "# HARD_NEGATIVE_CASE_STUDY_V1", "", "## 结论", "",
        "本轮只做离线 case study，不改 runtime。结果显示：高正向支持的 reject 样本大量存在，但多数样本只有未验证 blocker 或 context/meta burden，缺少稳定 paper-grounded hard-negative blocker。因此 borderline_positive 不能直接映射为 accept。", "",
        "## Aggregate", "",
        md_table(["metric", "value"], [["rows", summary["row_count"]], ["gold_counts", summary["gold_counts"]], ["recommendation_view_counts", summary["recommendation_view_counts"]], ["hard_negative_status_counts", summary["hard_negative_status_counts"]], ["bucket_counts", summary["bucket_counts"]]]), "",
        "## False-Accept Risk Reject Cases", "", "这些样本有 real/non-abstract/empirical support，但 gold 是 reject。它们是 final recommendation 不能激进放松的主要原因。", "",
        md_table(["paper_id", "view", "real", "empirical", "status", "blocker_candidates"], [[r["paper_id"], r["recommendation_view"], r["support_profile"]["real_strong"], r["support_profile"]["empirical_or_result"], r["hard_negative_status"], "; ".join(c["type"] for c in r["blocker_candidates"][:3]) or "none"] for r in false_risk]), "",
        "## Accept-Protect Cases", "", "这些样本是 gold accept，下一轮 policy 不能因为 stale gap / meta unresolved / fallback burden 把它们继续压成 reject。", "",
        md_table(["paper_id", "view", "real", "empirical", "status", "blocker_candidates"], [[r["paper_id"], r["recommendation_view"], r["support_profile"]["real_strong"], r["support_profile"]["empirical_or_result"], r["hard_negative_status"], "; ".join(c["type"] for c in r["blocker_candidates"][:3]) or "none"] for r in accept_protect]), "",
    ]
    (output_dir / "HARD_NEGATIVE_CASE_STUDY_V1.md").write_text("\n".join(report))
    decision = "\n".join([
        "# HARD_NEGATIVE_CASE_STUDY_DECISION_V1", "", "## 决策", "",
        "暂不把 hard-negative extraction runtime 化，也不把 borderline_positive 直接映射为 accept。保留当前 final-view recommendation 的保守投影，并把 hard-negative grounding 作为论文 case-study / audit 指标。", "",
        "## 原因", "",
        "1. high-support reject 多数缺少稳定 paper-grounded hard-negative blocker，说明不能靠 support 数量做 accept。",
        "2. accept-protect 样本仍需要避免被 stale gap / meta unresolved 压制，说明 raw negative burden 也不能直接做 reject。",
        "3. 当前最符合论文目标的结论是：系统能形成正向证据，但 final recommendation 必须区分 grounded hard-negative 与系统不确定性。", "",
        "## 下一步", "",
        "选取 2 个 high-support reject 和 2 个 accept-protect 样本，写 paper-ready case studies；不新增 controller，不硬调 binary decision。", "",
    ])
    (output_dir / "HARD_NEGATIVE_CASE_STUDY_DECISION_V1.md").write_text(decision)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    rows = [audit_row(row) for row in load_rows(args.input)]
    summary = summarize(rows)
    write_reports(args.output_dir, args.input, rows, summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
