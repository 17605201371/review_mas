#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Sequence

NEGATIVE_TERMS = re.compile(
    r"\b(lack|lacks|missing|insufficient|weak|limited|unclear|not demonstrate|does not demonstrate|no evidence|without|"
    r"unsupported|inadequate|fails? to|cannot|could not|not enough|absence|poor|flaw|limitation|concern|"
    r"baseline|ablation|dataset|metric|evaluation|experiment|comparison|novelty|soundness|validity|reproducib)\b",
    re.I,
)
EMPIRICAL_NEG_RE = re.compile(r"\b(baseline|ablation|dataset|metric|evaluation|experiment|result|table|figure|benchmark|comparison|empirical)\b", re.I)
SOUNDNESS_NEG_RE = re.compile(r"\b(method|algorithm|assumption|validity|soundness|proof|theory|mechanism|architecture|objective)\b", re.I)
NOVELTY_NEG_RE = re.compile(r"\b(novelty|novel|original|incremental|prior work|related work|contribution)\b", re.I)
META_RE = re.compile(r"\b(excerpt|truncated|provided text|complete text|not assessable|cannot assess|insufficient context|system|fallback|raw output|parse|agent)\b", re.I)


def norm(value: Any) -> str:
    return str(value or "").strip().lower()


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def by_paper(rows: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    return {str(row.get("paper_id")): row for row in rows}


def table(headers: Sequence[str], rows: Sequence[Sequence[Any]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(v).replace("\n", " ") for v in row) + " |")
    return "\n".join(lines)


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def issue_text(item: Dict[str, Any]) -> str:
    return " ".join(str(item.get(k) or "") for k in ("title", "description", "question", "note", "reason", "source", "status"))


def is_meta_text(text: str) -> bool:
    return bool(META_RE.search(text))


def is_negative_text(text: str) -> bool:
    return bool(NEGATIVE_TERMS.search(text)) and not is_meta_text(text)


def classify_negative_text(text: str) -> str:
    if EMPIRICAL_NEG_RE.search(text):
        return "empirical_negative"
    if SOUNDNESS_NEG_RE.search(text):
        return "soundness_negative"
    if NOVELTY_NEG_RE.search(text):
        return "novelty_or_significance_negative"
    return "general_negative"


def strong_support_count(state: Dict[str, Any]) -> int:
    count = 0
    for ev in state.get("evidence_map", []) or []:
        if norm(ev.get("strength")) == "strong" and norm(ev.get("stance")) in {"supports", "partially_supports"} and "fallback" not in norm(ev.get("claim_id")):
            count += 1
    return count


def hard_negative_from_state(state: Dict[str, Any]) -> Dict[str, Any]:
    counters = Counter()
    examples: List[Dict[str, Any]] = []
    for flaw in state.get("flaw_candidates", []) or []:
        if not isinstance(flaw, dict):
            continue
        text = issue_text(flaw)
        severity = norm(flaw.get("severity"))
        status = norm(flaw.get("status")) or "candidate"
        has_evidence = bool(flaw.get("evidence_ids"))
        if is_meta_text(text):
            counters["meta_or_fallback_flaw"] += 1
            continue
        if not is_negative_text(text):
            continue
        label = classify_negative_text(text)
        counters[f"flaw_{label}"] += 1
        if has_evidence:
            counters[f"grounded_flaw_{label}"] += 1
        if status == "confirmed":
            counters[f"confirmed_flaw_{label}"] += 1
        if severity in {"major", "critical"}:
            counters[f"major_flaw_{label}"] += 1
        examples.append({
            "kind": "flaw",
            "label": label,
            "grounded": has_evidence,
            "severity": severity,
            "status": status,
            "text": text[:260],
        })
    for q in state.get("unresolved_questions", []) or []:
        if not isinstance(q, dict) or norm(q.get("status")) not in {"", "open"}:
            continue
        text = issue_text(q)
        if is_meta_text(text):
            counters["meta_or_excerpt_unresolved"] += 1
            continue
        if not is_negative_text(text):
            counters["targetless_unresolved"] += 1
            continue
        label = classify_negative_text(text)
        counters[f"unresolved_{label}"] += 1
        examples.append({"kind": "unresolved", "label": label, "grounded": bool(q.get("evidence_ids") or q.get("related_claim_ids")), "severity": "", "status": norm(q.get("status")), "text": text[:260]})
    return {"counts": dict(counters), "examples": examples[:5]}


def dominant_gap(row: Dict[str, Any]) -> str:
    if row["grounded_major_or_critical"] > 0:
        return "has_grounded_major_or_critical"
    if row["grounded_negative_count"] > 0:
        return "has_grounded_negative_but_not_major"
    if row["negative_unresolved_count"] > 0:
        return "negative_unresolved_not_promoted"
    if row["meta_negative_burden"] > 0 and row["real_strong"] >= 2:
        return "meta_burden_masks_missing_hard_negative"
    if row["real_strong"] >= 2:
        return "positive_support_without_hard_negative"
    return "insufficient_positive_and_negative_grounding"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runtime-jsonl", type=Path, required=True)
    ap.add_argument("--recommendation-json", type=Path, required=True)
    ap.add_argument("--lifecycle-json", type=Path, required=True)
    ap.add_argument("--outdir", type=Path, required=True)
    ap.add_argument("--output-json", type=Path, required=True)
    args = ap.parse_args()

    runtime = by_paper(load_jsonl(args.runtime_jsonl))
    recommendation = load_json(args.recommendation_json)
    lifecycle = by_paper(load_json(args.lifecycle_json).get("case_rows", []))
    rows: List[Dict[str, Any]] = []
    for rec in recommendation.get("case_rows", []):
        pid = str(rec.get("paper_id"))
        gold = norm(rec.get("gold"))
        if gold != "reject":
            continue
        state = (runtime.get(pid) or {}).get("review_state") or {}
        hn = hard_negative_from_state(state)
        counts = Counter(hn["counts"])
        life = lifecycle.get(pid, {})
        grounded_negative = sum(v for k, v in counts.items() if k.startswith("grounded_flaw_"))
        negative_unresolved = sum(v for k, v in counts.items() if k.startswith("unresolved_") and "negative" in k)
        row = {
            "paper_id": pid,
            "final_view_v2": rec.get("final_view_v2"),
            "real_strong": int(rec.get("real_strong") or strong_support_count(state)),
            "empirical_support": int(rec.get("empirical_support") or 0),
            "independent_groups": int(rec.get("independent_groups") or 0),
            "grounded_major_or_critical": int(rec.get("grounded_major_or_critical") or 0),
            "grounded_negative_count": grounded_negative,
            "negative_unresolved_count": negative_unresolved,
            "meta_negative_burden": int(life.get("meta_negative_burden_count") or 0),
            "fallback_or_meta_flaws": int(rec.get("fallback_or_meta_flaws") or 0),
            "targetless_unresolved": int(rec.get("targetless_unresolved") or 0),
            "hard_negative_counts": dict(counts),
            "hard_negative_examples": hn["examples"],
        }
        row["dominant_gap"] = dominant_gap(row)
        rows.append(row)

    view_counts = Counter(row["final_view_v2"] for row in rows)
    gap_counts = Counter(row["dominant_gap"] for row in rows)
    borderline = [row for row in rows if row["final_view_v2"] == "borderline_positive"]
    payload = {"rows": rows, "view_counts": dict(view_counts), "dominant_gap_counts": dict(gap_counts), "borderline_reject_count": len(borderline)}
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    summary_rows = [[k, v] for k, v in gap_counts.most_common()]
    write(args.outdir / "HARD_NEGATIVE_GROUNDING_AUDIT_V1.md", "# Hard-Negative Grounding Audit v1\n\n" + table(["dominant_gap", "count"], summary_rows) + "\n\n## View Distribution\n\n" + table(["view", "count"], view_counts.most_common()))

    case_rows = []
    for row in rows:
        case_rows.append([
            row["paper_id"], row["final_view_v2"], row["dominant_gap"], row["real_strong"], row["empirical_support"], row["grounded_major_or_critical"], row["grounded_negative_count"], row["negative_unresolved_count"], row["meta_negative_burden"], row["targetless_unresolved"],
        ])
    write(args.outdir / "HARD_NEGATIVE_CASE_TABLE_V1.md", "# Hard-Negative Case Table v1\n\n" + table(["paper_id", "view", "dominant_gap", "real", "empirical", "grounded_major", "grounded_negative", "negative_unresolved", "meta_burden", "targetless_unresolved"], case_rows))

    detail = ["# Hard-Negative Evidence Examples v1", ""]
    for row in rows:
        if row["final_view_v2"] != "borderline_positive":
            continue
        detail.extend(["", f"## {row['paper_id']}", "", f"- dominant_gap: `{row['dominant_gap']}`", f"- hard_negative_counts: `{row['hard_negative_counts']}`", "- examples:"])
        for ex in row["hard_negative_examples"] or [{"text": "无"}]:
            detail.append(f"  - {ex.get('kind','')}/{ex.get('label','')}/grounded={ex.get('grounded','')}: {ex.get('text','')}")
    write(args.outdir / "HARD_NEGATIVE_EVIDENCE_EXAMPLES_V1.md", "\n".join(detail))

    decision = f"""# Hard-Negative Next Step Decision v1

## 结论

当前 reject 样本的主要缺口不是 positive support，而是 hard-negative grounding。30 条 gold reject 中，final-view 分布为：{dict(view_counts)}。

## 主导问题

{table(['dominant_gap', 'count'], summary_rows)}

## 对 recommendation 的含义

`borderline_positive` 不能升级为 `accept_like`，因为大量 gold reject 同时具有 real/non-abstract/empirical support。要想恢复安全的 accept-like，必须先证明 reject 样本的真实 hard-negative 能被抽取并 grounded；否则任何 support-only accept 规则都会制造 false accept。

## 下一步唯一建议

`Hard-Negative Extraction v1`，但只应先在离线/prompt 层小样本验证：让 critique / criterion report 明确抽取 empirical weakness、soundness weakness、novelty/significance weakness，并要求 evidence/claim grounding。不要改 runtime final decision，不要回 controller。
"""
    write(args.outdir / "HARD_NEGATIVE_NEXT_STEP_DECISION.md", decision)
    print(json.dumps({"rows": len(rows), "view_counts": dict(view_counts), "dominant_gap_counts": dict(gap_counts), "output_json": str(args.output_json)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
