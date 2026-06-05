#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence

from audit_final_view_unresolved_candidate_classifier_v1 import (
    classify_flaw,
    classify_gap,
    classify_unresolved,
    item_text,
    load_json,
    load_jsonl,
    support_claim_sets,
)


META_TERMS = ("fallback", "json", "parse", "parser", "system", "agent", "the user wants me")


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_jsonl(path: Path, rows: Sequence[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n", encoding="utf-8")


def write_md(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def md_table(headers: Sequence[str], rows: Sequence[Sequence[Any]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(x).replace("\n", " ") for x in row) + " |")
    return "\n".join(lines)


def as_list(value: Any) -> List[Any]:
    if isinstance(value, list):
        return value
    if value is None:
        return []
    return [value]


def short_text(value: Any, max_len: int = 180) -> str:
    text = " ".join(str(value or "").split())
    if len(text) <= max_len:
        return text
    return text[: max_len - 3].rstrip() + "..."


def strip_existing_final_view_sections(report: str) -> str:
    markers = [
        "4. Criterion Assessment (Final-View)",
        "4. Criterion Assessment (Grounded View)",
        "5. Final Recommendation View (Diagnostic)",
        "5. Final-View Recommendation",
    ]
    end = len(report)
    for marker in markers:
        idx = report.find(marker)
        if idx >= 0:
            end = min(end, idx)
    return report[:end].rstrip()


def support_summary(view: Dict[str, Any]) -> str:
    return (
        f"real strong={view.get('real_strong_support_total', 0)}, "
        f"non-abstract={view.get('non_abstract_support_total', 0)}, "
        f"empirical={view.get('empirical_support_total', 0)}, "
        f"method={view.get('method_support_total', 0)}, "
        f"independent groups={view.get('independent_support_group_total', 0)}"
    )


def recommendation_label(view: Dict[str, Any]) -> str:
    return str(view.get("classifier_view") or "not_assessable")


def recommendation_note(label: str) -> str:
    notes = {
        "accept_like": "positive evidence is sufficiently grounded and final-view blockers are low.",
        "borderline_positive": "positive evidence exists, but blockers or support depth are not clean enough for accept-like use.",
        "borderline_insufficient": "state evidence is mixed or too shallow for a confident recommendation.",
        "reject_like": "trusted hard negatives or repeated candidate hard negatives dominate the final-view state.",
        "not_assessable": "open paper-grounded questions or review limitations prevent a reliable recommendation.",
    }
    return notes.get(label, notes["not_assessable"])


def flaw_bucket(flaw: Dict[str, Any]) -> str:
    cls = classify_flaw(flaw)
    if cls in {"confirmed_grounded_hard_flaw", "trusted_critical_flaw", "trusted_major_flaw"}:
        return "confirmed_weakness"
    if cls in {"candidate_empirical_hard_flaw", "candidate_method_hard_flaw", "candidate_generic_hard_flaw", "weak_candidate_hard_flaw"}:
        return "potential_concern"
    if cls in {"system_or_fallback_flaw", "review_context_limitation_flaw"}:
        return "review_limitation"
    return "minor_or_nonblocking"


def flaw_line(flaw: Dict[str, Any]) -> str:
    flaw_id = str(flaw.get("flaw_id") or flaw.get("id") or "flaw")
    severity = str(flaw.get("severity") or "unknown")
    status = str(flaw.get("status") or "candidate")
    evidence = ", ".join(str(x) for x in as_list(flaw.get("evidence_ids")) if str(x).strip()) or "none"
    text = short_text(flaw.get("description") or flaw.get("title") or flaw.get("note") or item_text(flaw))
    return f"- `{flaw_id}` ({severity}, {status}; evidence: {evidence}): {text}"


def unresolved_line(item: Any) -> str:
    text = short_text(item_text(item))
    if isinstance(item, dict):
        qid = str(item.get("question_id") or item.get("id") or "unresolved")
        return f"- `{qid}`: {text}"
    return f"- {text}"


def gap_line(gap: Any) -> str:
    return f"- {short_text(gap)}"


def criterion_line(key: str, label: str, view: Dict[str, Any]) -> str:
    covered = bool(view.get(f"criterion_covered_{key}"))
    grounded = bool(view.get(f"criterion_grounded_{key}"))
    unsupported = int(view.get(f"unsupported_{key}_critique_count", 0) or 0)
    not_assessable = bool(view.get(f"criterion_not_assessable_{key}"))
    meta = int(view.get(f"meta_leakage_{key}", 0) or 0)
    if grounded:
        status = "grounded"
    elif not_assessable:
        status = "not_assessable"
    elif covered:
        status = "covered_ungrounded"
    else:
        status = "not_covered"
    return f"- **{label}**: `{status}`; unsupported critiques={unsupported}; meta leakage={meta}."


def categorize_state_items(state: Dict[str, Any]) -> Dict[str, List[str]]:
    supported_claims, strong_claims = support_claim_sets(state)
    out: Dict[str, List[str]] = {
        "confirmed_weaknesses": [],
        "potential_concerns": [],
        "review_limitations": [],
        "unresolved_questions": [],
        "resolved_or_stale_items": [],
        "minor_or_nonblocking_flaws": [],
    }
    for flaw in state.get("flaw_candidates", []) or []:
        if not isinstance(flaw, dict):
            continue
        bucket = flaw_bucket(flaw)
        if bucket == "confirmed_weakness":
            out["confirmed_weaknesses"].append(flaw_line(flaw))
        elif bucket == "potential_concern":
            out["potential_concerns"].append(flaw_line(flaw))
        elif bucket == "review_limitation":
            out["review_limitations"].append(flaw_line(flaw))
        else:
            out["minor_or_nonblocking_flaws"].append(flaw_line(flaw))
    for item in state.get("unresolved_questions", []) or []:
        cls = classify_unresolved(item, supported_claims, strong_claims)
        line = unresolved_line(item)
        if cls in {"system_or_fallback", "review_context_limitation"}:
            out["review_limitations"].append(line)
        elif cls in {"resolved_by_support", "resolved_by_strong_support", "closed_or_resolved"}:
            out["resolved_or_stale_items"].append(line)
        else:
            out["unresolved_questions"].append(line)
    for gap in state.get("evidence_gaps", []) or []:
        cls = classify_gap(gap, supported_claims)
        line = gap_line(gap)
        if cls in {"system_or_fallback_gap", "review_context_gap"}:
            out["review_limitations"].append(line)
        elif cls == "stale_gap_resolved_by_support":
            out["resolved_or_stale_items"].append(line)
        elif cls == "active_claim_gap":
            out["unresolved_questions"].append(line)
    return out


def cap_lines(lines: Sequence[str], limit: int = 6) -> List[str]:
    if len(lines) <= limit:
        return list(lines) if lines else ["- none"]
    return list(lines[:limit]) + [f"- ... {len(lines) - limit} more omitted in preview"]


def render_section(title: str, lines: Sequence[str], limit: int = 6) -> str:
    return "\n".join([f"### {title}", "", *cap_lines(lines, limit), ""])


def render_final_view_report(original_report: str, state: Dict[str, Any], view: Dict[str, Any]) -> str:
    categories = categorize_state_items(state)
    label = recommendation_label(view)
    criteria = [
        ("novelty", "Novelty / Originality"),
        ("significance", "Significance / Contribution"),
        ("soundness", "Technical Soundness"),
        ("empirical", "Empirical Adequacy"),
        ("clarity", "Clarity / Reproducibility"),
    ]
    lines = [
        strip_existing_final_view_sections(original_report),
        "",
        "4. Criterion Assessment (Final-View)",
        "",
        *[criterion_line(key, label_text, view) for key, label_text in criteria],
        "",
        "5. Final-View Recommendation",
        "",
        f"- **Recommendation view**: `{label}`",
        f"- **Interpretation**: {recommendation_note(label)}",
        f"- **Support summary**: {support_summary(view)}.",
        "- **Decision boundary**: this section is diagnostic and does not alter the runtime accept/reject label.",
        "",
        "6. Final-View Weakness / Limitation Partition",
        "",
        render_section("Confirmed Weaknesses", categories["confirmed_weaknesses"]),
        render_section("Potential Concerns", categories["potential_concerns"]),
        render_section("Review Limitations", categories["review_limitations"]),
        render_section("Unresolved Questions", categories["unresolved_questions"]),
    ]
    return "\n".join(x for x in lines if x is not None).rstrip()


def confirmed_meta_leak_count(report: str) -> int:
    marker = "### Confirmed Weaknesses"
    idx = report.find(marker)
    if idx < 0:
        return 0
    next_idx = report.find("### Potential Concerns", idx)
    section = report[idx: next_idx if next_idx >= 0 else len(report)].lower()
    return sum(1 for term in META_TERMS if term in section)


def build_rows(source_rows: Sequence[Dict[str, Any]], view_rows: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    by_view = {row.get("paper_id"): row for row in view_rows}
    out: List[Dict[str, Any]] = []
    for raw in source_rows:
        pid = raw.get("paper_id")
        view = by_view.get(pid)
        if not view:
            continue
        state = raw.get("review_state") or {}
        original_report = str(raw.get("final_report") or state.get("final_report") or "")
        rendered = render_final_view_report(original_report, state, view)
        categories = categorize_state_items(state)
        out.append({
            "paper_id": pid,
            "gold_decision": view.get("gold_decision") or raw.get("gold_decision"),
            "runtime_final_decision": raw.get("final_decision") or state.get("final_decision"),
            "classifier_view": view.get("classifier_view"),
            "final_view_report": rendered,
            "section_counts": {key: len(value) for key, value in categories.items()},
            "support_summary": {
                "real_strong_support_total": view.get("real_strong_support_total", 0),
                "non_abstract_support_total": view.get("non_abstract_support_total", 0),
                "empirical_support_total": view.get("empirical_support_total", 0),
                "method_support_total": view.get("method_support_total", 0),
                "independent_support_group_total": view.get("independent_support_group_total", 0),
            },
            "confirmed_weakness_meta_leak_count": confirmed_meta_leak_count(rendered),
        })
    return out


def aggregate(rows: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    counts = Counter(row.get("classifier_view") for row in rows)
    section_totals: Counter[str] = Counter()
    for row in rows:
        section_totals.update(row.get("section_counts") or {})
    return {
        "rows": len(rows),
        "classifier_view_counts": dict(counts),
        "section_totals": dict(section_totals),
        "confirmed_weakness_meta_leak_rows": sum(1 for row in rows if row.get("confirmed_weakness_meta_leak_count", 0) > 0),
        "reports_with_confirmed_weakness": sum(1 for row in rows if (row.get("section_counts") or {}).get("confirmed_weaknesses", 0) > 0),
        "reports_with_potential_concerns": sum(1 for row in rows if (row.get("section_counts") or {}).get("potential_concerns", 0) > 0),
        "reports_with_review_limitations": sum(1 for row in rows if (row.get("section_counts") or {}).get("review_limitations", 0) > 0),
        "reports_with_unresolved_questions": sum(1 for row in rows if (row.get("section_counts") or {}).get("unresolved_questions", 0) > 0),
    }


def render_protocol() -> str:
    return """# Final-View Report Renderer v1 Protocol

## 定位

本轮是离线 final report 渲染，不改 runtime、不改 live `ReviewState`、不重跑模型、不改变已有 accept/reject。

## 输入

- fulltest39 运行后的 final `ReviewState` / final report。
- `Final-View Unresolved / Candidate-Flaw Classifier v1` 的分类结果。

## 渲染原则

- confirmed / trusted grounded hard flaw 才进入 `Confirmed Weaknesses`。
- candidate hard flaw 进入 `Potential Concerns`，不能等同 confirmed weakness。
- fallback / malformed JSON / system-meta / excerpt limitation 进入 `Review Limitations`。
- paper-grounded open items 进入 `Unresolved Questions`。
- criterion section 只报告 coverage / grounding / unsupported / meta-leakage 状态，不参与 runtime final decision。

## 边界

本轮目标是让 final report 更符合论文主线：证据对齐、状态卫生、维度可诊断。它不是新的决策阈值，也不是 controller 改动。
"""


def render_audit(rows: Sequence[Dict[str, Any]], agg: Dict[str, Any]) -> str:
    summary_rows = [[k, v] for k, v in agg.items() if k not in {"classifier_view_counts", "section_totals"}]
    view_rows = [[k, v] for k, v in sorted(agg["classifier_view_counts"].items())]
    section_rows = [[k, v] for k, v in sorted(agg["section_totals"].items())]
    return "\n\n".join([
        "# Final-View Report Renderer v1 Audit",
        "## 汇总",
        md_table(["metric", "value"], summary_rows),
        "## Recommendation view 分布",
        md_table(["view", "count"], view_rows),
        "## 分区总数",
        md_table(["section", "count"], section_rows),
    ])


def render_preview(rows: Sequence[Dict[str, Any]]) -> str:
    table = []
    for row in rows[:12]:
        sc = row.get("section_counts") or {}
        table.append([
            row["paper_id"], row.get("gold_decision"), row.get("runtime_final_decision"), row.get("classifier_view"),
            sc.get("confirmed_weaknesses", 0), sc.get("potential_concerns", 0), sc.get("review_limitations", 0), sc.get("unresolved_questions", 0),
        ])
    return "# Final-View Report Renderer v1 Preview\n\n" + md_table(["paper_id", "gold", "runtime", "view", "confirmed", "potential", "limitations", "unresolved"], table)


def render_decision(agg: Dict[str, Any]) -> str:
    return f"""# Final-View Report Renderer v1 Decision

## 结论

建议保留为论文层 report rendering / final-view 展示模块。

本轮把 final report 的负面内容拆成 `Confirmed Weaknesses`、`Potential Concerns`、`Review Limitations`、`Unresolved Questions` 四类，避免把 candidate flaw、fallback/malformed JSON、excerpt limitation 直接写成确认论文缺陷。

## 关键数字

- reports: `{agg['rows']}`
- reports_with_confirmed_weakness: `{agg['reports_with_confirmed_weakness']}`
- reports_with_potential_concerns: `{agg['reports_with_potential_concerns']}`
- reports_with_review_limitations: `{agg['reports_with_review_limitations']}`
- reports_with_unresolved_questions: `{agg['reports_with_unresolved_questions']}`
- confirmed_weakness_meta_leak_rows: `{agg['confirmed_weakness_meta_leak_rows']}`

## 对主试验的意义

当前最可信的系统输出不是单一 accept/reject，而是证据约束下的 final-view review。正式主试验可以继续报告 accept/reject health check，但论文主表应加入 report hygiene、criterion grounding、support quality 和 final-view recommendation。

## 下一步

下一步应整合 `Mainline-Final-v1` 主表：把 runtime evidence 指标、support quality、hard-negative lifecycle、criterion grounding、final-view report 分区放进同一份 fulltest39 分析，而不是继续新增 runtime controller。
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-jsonl", type=Path, default=Path("outputs/results_main/review_infer/fallback_flaw_guard_v1_4b_fulltest39.jsonl"))
    parser.add_argument("--classifier-json", type=Path, default=Path("outputs/results_main/review_infer/final_view_unresolved_candidate_classifier_v1.json"))
    parser.add_argument("--output-jsonl", type=Path, default=Path("outputs/results_main/review_infer/final_view_report_renderer_v1.jsonl"))
    parser.add_argument("--output-json", type=Path, default=Path("outputs/results_main/review_infer/final_view_report_renderer_v1_summary.json"))
    parser.add_argument("--doc-dir", type=Path, default=Path("docs/experiments/mainline_current"))
    args = parser.parse_args()

    source_rows = load_jsonl(args.source_jsonl)
    classifier = load_json(args.classifier_json)
    rows = build_rows(source_rows, classifier.get("rows", []))
    agg = aggregate(rows)
    write_jsonl(args.output_jsonl, rows)
    write_json(args.output_json, {
        "source_jsonl": str(args.source_jsonl),
        "classifier_json": str(args.classifier_json),
        "aggregate": agg,
        "rows": rows,
    })
    write_md(args.doc_dir / "FINAL_VIEW_REPORT_RENDERER_V1_PROTOCOL.md", render_protocol())
    write_md(args.doc_dir / "FINAL_VIEW_REPORT_RENDERER_V1_AUDIT.md", render_audit(rows, agg))
    write_md(args.doc_dir / "FINAL_VIEW_REPORT_RENDERER_V1_PREVIEW.md", render_preview(rows))
    write_md(args.doc_dir / "FINAL_VIEW_REPORT_RENDERER_V1_DECISION.md", render_decision(agg))
    print(json.dumps({"rows": len(rows), "aggregate": agg, "output_jsonl": str(args.output_jsonl)}, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()

