#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_md(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def md_table(headers: Iterable[Any], rows: Iterable[Iterable[Any]]) -> str:
    headers = [str(h) for h in headers]
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(v).replace("\n", " ") for v in row) + " |")
    return "\n".join(lines)


def as_int(row: Dict[str, Any], key: str) -> int:
    try:
        return int(row.get(key) or 0)
    except (TypeError, ValueError):
        return 0


def trusted_hard_negative_count(row: Dict[str, Any]) -> int:
    if "trusted_major_or_critical_flaws" in row:
        return as_int(row, "trusted_major_or_critical_flaws")
    return as_int(row, "major_or_critical_flaws")


def indexed(rows: List[Dict[str, Any]], key: str = "paper_id") -> Dict[str, Dict[str, Any]]:
    return {str(r.get(key) or ""): r for r in rows}


def missing_high_precision_reasons(row: Dict[str, Any]) -> List[str]:
    ratings = row.get("criterion_ratings") or {}
    reasons: List[str] = []
    if as_int(row, "real_strong_support_total") < 3:
        reasons.append("real_strong_lt3")
    if as_int(row, "non_abstract_support_total") < 3:
        reasons.append("nonabstract_lt3")
    if as_int(row, "empirical_support_total") < 1:
        reasons.append("no_empirical_support")
    if as_int(row, "method_support_total") < 1:
        reasons.append("no_method_support")
    if as_int(row, "independent_support_group_total") < 3:
        reasons.append("independent_lt3")
    if as_int(row, "unresolved_count") > 4:
        reasons.append("unresolved_gt4")
    if trusted_hard_negative_count(row) > 0:
        reasons.append("trusted_major_or_critical_flaw_present")
    if ratings.get("novelty") != "positive":
        reasons.append("novelty_not_positive")
    if ratings.get("soundness") != "positive":
        reasons.append("soundness_not_positive")
    if ratings.get("empirical") != "positive":
        reasons.append("empirical_not_positive")
    return reasons


def blocker_family(reasons: List[str]) -> str:
    if "trusted_major_or_critical_flaw_present" in reasons or "unresolved_gt4" in reasons:
        return "hard_negative_burden"
    if "no_method_support" in reasons or "soundness_not_positive" in reasons:
        return "method_soundness_gap"
    if "novelty_not_positive" in reasons:
        return "novelty_gap"
    if "real_strong_lt3" in reasons or "nonabstract_lt3" in reasons or "independent_lt3" in reasons:
        return "support_depth_gap"
    if "no_empirical_support" in reasons or "empirical_not_positive" in reasons:
        return "empirical_gap"
    return "passes_or_other"


def build_rows(support_rows: List[Dict[str, Any]], rec_case_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    support_by_id = indexed(support_rows)
    rows: List[Dict[str, Any]] = []
    for rec in rec_case_rows:
        pid = str(rec.get("paper_id") or "")
        s = support_by_id.get(pid, {})
        merged = dict(s)
        merged.update(rec)
        reasons = missing_high_precision_reasons(merged)
        merged["missing_high_precision_reasons"] = reasons
        merged["blocker_family"] = blocker_family(reasons)
        rows.append(merged)
    return rows


def aggregate(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    gold_accept = [r for r in rows if r.get("gold_decision") == "accept"]
    gold_reject = [r for r in rows if r.get("gold_decision") == "reject"]
    borderline = [r for r in rows if r.get("three_way") == "borderline_positive"]
    accept_like = [r for r in rows if r.get("three_way") == "accept_like"]
    runtime_false_accept = [r for r in rows if r.get("gold_decision") == "reject" and r.get("runtime_pred") == "accept"]
    false_reject = [r for r in rows if r.get("gold_decision") == "accept" and r.get("runtime_pred") != "accept"]
    return {
        "total_rows": len(rows),
        "gold_accept_count": len(gold_accept),
        "gold_reject_count": len(gold_reject),
        "accept_like_count": len(accept_like),
        "borderline_positive_count": len(borderline),
        "runtime_false_accept_ids": [r["paper_id"] for r in runtime_false_accept],
        "runtime_false_reject_ids": [r["paper_id"] for r in false_reject],
        "gold_accept_gap_counts": dict(Counter(reason for r in gold_accept for reason in r["missing_high_precision_reasons"])),
        "borderline_gap_counts": dict(Counter(reason for r in borderline for reason in r["missing_high_precision_reasons"])),
        "gold_accept_blocker_families": dict(Counter(r["blocker_family"] for r in gold_accept)),
        "borderline_blocker_families": dict(Counter(r["blocker_family"] for r in borderline)),
        "gold_accept_with_method_support": sum(1 for r in gold_accept if as_int(r, "method_support_total") > 0),
        "gold_accept_with_soundness_positive": sum(1 for r in gold_accept if (r.get("criterion_ratings") or {}).get("soundness") == "positive"),
        "gold_accept_with_novelty_positive": sum(1 for r in gold_accept if (r.get("criterion_ratings") or {}).get("novelty") == "positive"),
        "borderline_with_method_support": sum(1 for r in borderline if as_int(r, "method_support_total") > 0),
        "borderline_with_soundness_positive": sum(1 for r in borderline if (r.get("criterion_ratings") or {}).get("soundness") == "positive"),
    }


def render_method_soundness_audit(rows: List[Dict[str, Any]], summary: Dict[str, Any]) -> str:
    gold_accept = [r for r in rows if r.get("gold_decision") == "accept"]
    rows_table = []
    for r in gold_accept:
        ratings = r.get("criterion_ratings") or {}
        rows_table.append([
            r["paper_id"], r.get("three_way"), as_int(r, "real_strong_support_total"), as_int(r, "non_abstract_support_total"),
            as_int(r, "empirical_support_total"), as_int(r, "method_support_total"), as_int(r, "independent_support_group_total"),
            as_int(r, "unresolved_count"), trusted_hard_negative_count(r), ratings.get("novelty"), ratings.get("soundness"), ratings.get("empirical"),
            ",".join(r["missing_high_precision_reasons"]),
        ])
    text = "# Method / Soundness Evidence Formation Audit v1\n\n"
    text += "## 结论\n\n"
    text += "Soft Focus v2 已经能形成大量 real/non-abstract/empirical support，但 high-precision accept-like 只能恢复 1 条，主因不是 fallback binding，而是 method support、soundness/novelty criterion 与 hard-negative burden 没有同时满足。\n\n"
    text += "## 汇总\n\n"
    text += md_table(["metric", "value"], [[k, v] for k, v in summary.items() if not isinstance(v, dict) and not isinstance(v, list)])
    text += "\n\n## Gold accept case audit\n\n"
    text += md_table(["paper_id", "view", "real", "nonabs", "empirical", "method", "independent", "unresolved", "major", "novelty", "soundness", "empirical_rating", "missing"], rows_table)
    text += "\n"
    return text


def render_borderline_casebook(rows: List[Dict[str, Any]]) -> str:
    selected = [r for r in rows if r.get("three_way") in {"borderline_positive", "accept_like"} or r.get("gold_decision") == "accept"]
    table = []
    for r in selected:
        ratings = r.get("criterion_ratings") or {}
        table.append([
            r["paper_id"], r.get("gold_decision"), r.get("runtime_pred"), r.get("three_way"),
            as_int(r, "real_strong_support_total"), as_int(r, "empirical_support_total"), as_int(r, "method_support_total"), as_int(r, "independent_support_group_total"),
            ratings.get("novelty"), ratings.get("soundness"), ratings.get("empirical"), r.get("blocker_family"), ",".join(r["missing_high_precision_reasons"]),
        ])
    text = "# Soft Focus v2 Borderline / False-Reject Casebook\n\n"
    text += "本表覆盖全部 gold accept、accept_like 与 borderline_positive。用途是判断哪些样本只差 method/soundness evidence，哪些样本仍被 hard-negative burden 阻断。\n\n"
    text += md_table(["paper_id", "gold", "runtime", "view", "real", "empirical", "method", "independent", "novelty", "soundness", "empirical_rating", "family", "missing"], table)
    return text


def render_hard_negative_audit(rows: List[Dict[str, Any]]) -> str:
    risky = [r for r in rows if r.get("gold_decision") == "reject" and (r.get("support_quality_basic") == "accept" or r.get("criterion_positive") == "accept" or r.get("runtime_pred") == "accept")]
    table = []
    for r in risky:
        ratings = r.get("criterion_ratings") or {}
        table.append([
            r["paper_id"], r.get("runtime_pred"), r.get("support_quality_basic"), r.get("criterion_positive"), r.get("high_precision_criterion_quality"),
            as_int(r, "real_strong_support_total"), as_int(r, "empirical_support_total"), as_int(r, "method_support_total"), as_int(r, "unresolved_count"), trusted_hard_negative_count(r),
            ratings.get("novelty"), ratings.get("soundness"), ratings.get("empirical"), ",".join(r["missing_high_precision_reasons"]),
        ])
    text = "# Hard-Negative Blocker Audit v2\n\n"
    text += "宽松 support-quality / criterion-positive 规则的主要风险是把 gold reject 中的 result support 误当成 accept-like。high-precision 规则通过 method support、soundness/novelty positive 与 hard-negative blocker 同时约束，把这些风险样本挡回 reject。\n\n"
    text += md_table(["paper_id", "runtime", "support_quality", "criterion_positive", "high_precision", "real", "empirical", "method", "unresolved", "major", "novelty", "soundness", "empirical_rating", "blockers"], table)
    return text


def render_next_cut(summary: Dict[str, Any]) -> str:
    return f"""# Method / Soundness Next-Cut Decision

## 当前判断

修正 trusted hard-negative 口径后，Soft Focus v2 的剩余瓶颈分成两层：

1. `flaw-fallback-*` / malformed critique 不能算真实 paper flaw，这类问题必须在 runtime fallback flaw lifecycle 中降级。
2. 对仍未进入 `accept_like` 的样本，主要缺口是 method support、soundness/novelty positive、empirical support depth 和 open unresolved burden。

因此，下一刀不应继续放宽 final recommendation，也不应恢复 sticky / throttle / progression gate。

## 关键证据

- gold accept 数：{summary['gold_accept_count']}
- accept_like 数：{summary['accept_like_count']}
- borderline_positive 数：{summary['borderline_positive_count']}
- gold accept 中具备 method support 的样本数：{summary['gold_accept_with_method_support']}
- gold accept 中 soundness positive 的样本数：{summary['gold_accept_with_soundness_positive']}
- runtime false accept：{', '.join(summary['runtime_false_accept_ids']) or 'none'}
- gold accept blocker family：{summary['gold_accept_blocker_families']}
- borderline blocker family：{summary['borderline_blocker_families']}

## 本轮已执行的最小修复

实现 `Fallback Flaw Lifecycle Guard v1`：Critique / General Reviewer fallback 解析失败不再生成 `major candidate flaw`，而是写成 `severity=minor`、`status=downgraded`、`source=fallback-extraction`、`grounding_status=fallback_unverified`，并且 recommendation 保持 `undecided`。这属于 bug fix，不是新 controller。

## 下一轮唯一建议

先用 4B 小确认或 fulltest39 重跑验证 `Fallback Flaw Lifecycle Guard v1`：

1. `trusted_major_or_critical_flaws` 是否下降。
2. `fallback_or_meta_flaws` 是否仍可观测但不再阻断 accept-like。
3. `LebzzClHYw` 这类 accept_like 是否不再被 fallback flaw 污染。
4. false accept `NnExMNiTHw` 是否仍被 method/soundness/novelty blocker 挡住。

如果确认稳定，再进入 `Method / Soundness Evidence Formation v1`，优先补 method/mechanism/assumption 与 result/table 的配对证据。

## 暂时不做

- 不放宽 `high_precision_criterion_quality`。
- 不把 `borderline_positive` 映射 accept。
- 不恢复 sticky / throttle / progression gate。
- 不做大规模 9B 正式主试验，先做 4B 确认。
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--support-summary", required=True, type=Path)
    parser.add_argument("--recommendation-json", required=True, type=Path)
    parser.add_argument("--output-json", required=True, type=Path)
    parser.add_argument("--doc-dir", required=True, type=Path)
    parser.add_argument("--doc-prefix", default="", help="Optional prefix for generated markdown files")
    args = parser.parse_args()

    support = load_json(args.support_summary)
    rec = load_json(args.recommendation_json)
    rows = build_rows(support["rows"], rec["case_rows"])
    summary = aggregate(rows)
    output = {"summary": summary, "rows": rows}
    write_json(args.output_json, output)
    prefix = f"{args.doc_prefix}_" if args.doc_prefix else ""
    write_md(args.doc_dir / f"{prefix}METHOD_SOUNDNESS_EVIDENCE_FORMATION_AUDIT_V1.md", render_method_soundness_audit(rows, summary))
    write_md(args.doc_dir / f"{prefix}BORDERLINE_FALSE_REJECT_CASEBOOK.md", render_borderline_casebook(rows))
    write_md(args.doc_dir / f"{prefix}HARD_NEGATIVE_BLOCKER_AUDIT_V2.md", render_hard_negative_audit(rows))
    write_md(args.doc_dir / f"{prefix}METHOD_SOUNDNESS_NEXT_CUT_DECISION.md", render_next_cut(summary))
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
