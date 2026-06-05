#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Sequence


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def norm(value: Any) -> str:
    return str(value or "").strip().lower()


def table(headers: Sequence[str], rows: Sequence[Sequence[Any]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(v).replace("\n", " ") for v in row) + " |")
    return "\n".join(lines)


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def by_paper(rows: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    return {str(row.get("paper_id")): row for row in rows}


def safe_state(row: Dict[str, Any]) -> Dict[str, Any]:
    return row.get("review_state") or {}


def top_evidence(state: Dict[str, Any], limit: int = 3) -> List[str]:
    out: List[str] = []
    for ev in state.get("evidence_map", []) or []:
        if norm(ev.get("strength")) != "strong":
            continue
        if norm(ev.get("stance")) not in {"supports", "partially_supports"}:
            continue
        if "fallback" in norm(ev.get("claim_id")):
            continue
        text = str(ev.get("evidence") or "").strip().replace("\n", " ")
        bucket = ev.get("support_source_bucket") or ev.get("source") or ""
        claim_id = ev.get("claim_id") or ""
        out.append(f"{claim_id}/{bucket}: {text[:180]}")
    return out[:limit]


def top_flaws(state: Dict[str, Any], limit: int = 3) -> List[str]:
    out: List[str] = []
    for flaw in state.get("flaw_candidates", []) or []:
        if not isinstance(flaw, dict):
            continue
        title = str(flaw.get("title") or "").strip().replace("\n", " ")
        severity = flaw.get("severity") or ""
        status = flaw.get("status") or ""
        source = flaw.get("source") or ""
        out.append(f"{severity}/{status}/{source}: {title[:160]}")
    return out[:limit]


def top_unresolved(state: Dict[str, Any], limit: int = 3) -> List[str]:
    out: List[str] = []
    for q in state.get("unresolved_questions", []) or []:
        if not isinstance(q, dict) or norm(q.get("status")) not in {"", "open"}:
            continue
        text = str(q.get("question") or "").strip().replace("\n", " ")
        out.append(text[:180])
    return out[:limit]


def case_bucket(row: Dict[str, Any]) -> str:
    if row["gold"] == "accept":
        if row["targetless_unresolved"] >= 5:
            return "gold_accept_but_unresolved_heavy"
        return "gold_accept_borderline_positive"
    if row["ungrounded_candidate_flaws"] > 0:
        return "reject_false_accept_risk_with_ungrounded_flaw"
    if row["targetless_unresolved"] >= 5:
        return "reject_false_accept_risk_unresolved_heavy"
    return "reject_false_accept_risk_no_hard_negative"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runtime-jsonl", type=Path, required=True)
    ap.add_argument("--recommendation-json", type=Path, required=True)
    ap.add_argument("--lifecycle-json", type=Path, required=True)
    ap.add_argument("--outdir", type=Path, required=True)
    ap.add_argument("--output-json", type=Path, required=True)
    args = ap.parse_args()

    runtime = by_paper(load_jsonl(args.runtime_jsonl))
    rec = load_json(args.recommendation_json)
    lifecycle = load_json(args.lifecycle_json)
    life_by = by_paper(lifecycle.get("case_rows", []))
    rows: List[Dict[str, Any]] = []
    for item in rec.get("case_rows", []):
        if item.get("final_view_v2") != "borderline_positive":
            continue
        pid = str(item.get("paper_id"))
        runtime_row = runtime.get(pid, {})
        state = safe_state(runtime_row)
        life = life_by.get(pid, {})
        enriched = dict(item)
        enriched["bucket"] = case_bucket(enriched)
        enriched["top_evidence"] = top_evidence(state)
        enriched["top_flaws"] = top_flaws(state)
        enriched["top_unresolved"] = top_unresolved(state)
        enriched["lifecycle_label"] = life.get("derived_label", "")
        enriched["lifecycle_reason"] = life.get("derived_reason", "")
        enriched["meta_negative_burden_count"] = life.get("meta_negative_burden_count", 0)
        rows.append(enriched)

    counts = Counter(row["bucket"] for row in rows)
    gold_counts = Counter(row["gold"] for row in rows)
    payload = {"rows": rows, "bucket_counts": dict(counts), "gold_counts": dict(gold_counts)}
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    table_rows = []
    for r in rows:
        table_rows.append([
            r["paper_id"], r["gold"], r["bucket"], r["real_strong"], r["nonabstract_support"], r["empirical_support"], r["independent_groups"],
            r["targetless_unresolved"], r["ungrounded_candidate_flaws"], r["fallback_or_meta_flaws"], r["grounded_major_or_critical"], r["meta_negative_burden_count"],
        ])
    write(args.outdir / "BORDERLINE_POSITIVE_CASE_TABLE_V1.md", "# Borderline Positive Case Table v1\n\n" + table(
        ["paper_id", "gold", "bucket", "real", "nonabs", "empirical", "groups", "targetless_unres", "ungrounded_flaw", "fallback_meta_flaw", "grounded_major", "meta_burden"],
        table_rows,
    ))

    detail_parts = ["# Borderline Positive Case Review v1", "", "## 汇总", "", table(["bucket", "count"], counts.most_common()), "", table(["gold", "count"], gold_counts.most_common())]
    for r in rows:
        detail_parts.extend([
            "",
            f"## {r['paper_id']} ({r['gold']})",
            "",
            f"- bucket: `{r['bucket']}`",
            f"- support: real={r['real_strong']}, nonabstract={r['nonabstract_support']}, empirical={r['empirical_support']}, groups={r['independent_groups']}",
            f"- blockers: grounded_major={r['grounded_major_or_critical']}, ungrounded_flaw={r['ungrounded_candidate_flaws']}, targetless_unresolved={r['targetless_unresolved']}, meta_burden={r['meta_negative_burden_count']}",
            f"- lifecycle: `{r['lifecycle_label']}` / {r['lifecycle_reason']}",
            "- top evidence:",
            *(f"  - {x}" for x in (r['top_evidence'] or ['无'])),
            "- top flaws:",
            *(f"  - {x}" for x in (r['top_flaws'] or ['无'])),
            "- top unresolved:",
            *(f"  - {x}" for x in (r['top_unresolved'] or ['无'])),
        ])
    write(args.outdir / "BORDERLINE_POSITIVE_CASE_REVIEW_V1.md", "\n".join(detail_parts))

    decision = f"""# Borderline Positive Next Step Decision v1

## 结论

`borderline_positive` 不应升级为 `accept_like`。15 条中只有 {gold_counts.get('accept', 0)} 条 gold accept，{gold_counts.get('reject', 0)} 条是 gold reject；如果直接把它们映射为 accept，会制造明显 false accept。

## 分布

{table(['bucket', 'count'], counts.most_common())}

## 解释

当前 positive evidence 已经能形成 real/non-abstract/empirical support，但 paper-level recommendation 仍缺 hard-negative grounding。多数 reject 样本没有 grounded major/critical flaw，因此被 V2 标成 `borderline_positive`；这不是系统应该 accept，而是说明当前 final-view 还无法安全地区分“局部 claim 有支持”和“整篇论文值得接收”。

## 下一刀

下一步唯一建议：`Hard-Negative Grounding Audit v1`。目标是审计 reject 样本中的真实拒稿依据是否被系统抽出并 grounded 到 evidence/criterion/flaw。不要直接调 accept 阈值，也不要把 criterion positive 裸接入 decision。

## 不做

- 不回 sticky / throttle / progression gate。
- 不继续加 Evidence Context，除非 hard-negative audit 证明 reject 样本缺少可见负证据。
- 不把 `borderline_positive` 当作 accept。
"""
    write(args.outdir / "BORDERLINE_POSITIVE_NEXT_STEP_DECISION.md", decision)
    print(json.dumps({"rows": len(rows), "gold_counts": dict(gold_counts), "bucket_counts": dict(counts), "output_json": str(args.output_json)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
