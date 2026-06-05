#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence


LABEL_EXPLANATIONS = {
    "accept_like": "High-precision positive recommendation: support quality and grounded criterion signals are strong enough for an accept-like view.",
    "borderline_positive": "Positive signals exist, but support depth, criterion coverage, or blocker uncertainty is insufficient for a safe accept-like view.",
    "borderline_insufficient": "Some review signals exist, but neither positive support nor grounded blockers are strong enough for a confident recommendation.",
    "reject_like": "Grounded negative criteria or hard blockers dominate the derived final-view state.",
    "not_assessable": "The grounded final-view state lacks enough reliable support or blocker evidence for a confident recommendation.",
}


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path: Path, rows: Sequence[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n", encoding="utf-8")


def write_md(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def table_row(values: Iterable[Any]) -> str:
    return "| " + " | ".join(str(v).replace("\n", " ") for v in values) + " |"


def strip_existing_section(report: str) -> str:
    marker = "Final Recommendation View (Diagnostic)"
    idx = report.find(marker)
    if idx >= 0:
        return report[:idx].rstrip()
    return report.rstrip()


def render_recommendation_section(view: Dict[str, Any]) -> str:
    label = view.get("recommendation_view", "not_assessable")
    explanation = LABEL_EXPLANATIONS.get(label, LABEL_EXPLANATIONS["not_assessable"])
    positive = ", ".join(view.get("positive_grounded_criteria") or []) or "none"
    hard_negative = "yes" if view.get("has_hard_negative") else "no"
    return "\n".join(
        [
            "5. Final Recommendation View (Diagnostic)",
            "",
            f"- **Recommendation view**: `{label}`",
            f"- **Interpretation**: {explanation}",
            f"- **Real strong support**: `{view.get('real_strong_support_total', 0)}`",
            f"- **Non-abstract support**: `{view.get('non_abstract_support_total', 0)}`",
            f"- **Independent support groups**: `{view.get('independent_support_group_total', 0)}`",
            f"- **Empirical support**: `{view.get('empirical_support_total', 0)}`",
            f"- **Positive grounded criteria**: {positive}",
            f"- **Hard negative present**: `{hard_negative}`",
            "",
            "Note: This is a final-view diagnostic recommendation, not the runtime accept/reject decision.",
        ]
    )


def build_outputs(source_rows: List[Dict[str, Any]], view_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    by_id = {row["paper_id"]: row for row in view_rows}
    outputs: List[Dict[str, Any]] = []
    for row in source_rows:
        paper_id = row.get("paper_id")
        view = by_id.get(paper_id)
        if not view:
            continue
        original_report = str(row.get("final_report") or (row.get("review_state") or {}).get("final_report") or "")
        section = render_recommendation_section(view)
        rendered = strip_existing_section(original_report) + "\n\n" + section
        outputs.append(
            {
                "paper_id": paper_id,
                "gold_decision": row.get("gold_decision") or view.get("gold_decision"),
                "runtime_final_decision": row.get("final_decision") or (row.get("review_state") or {}).get("final_decision"),
                "recommendation_view": view.get("recommendation_view"),
                "recommendation_section": section,
                "final_report_with_recommendation_view": rendered,
                "recommendation_features": {
                    "real_strong_support_total": view.get("real_strong_support_total", 0),
                    "non_abstract_support_total": view.get("non_abstract_support_total", 0),
                    "independent_support_group_total": view.get("independent_support_group_total", 0),
                    "empirical_support_total": view.get("empirical_support_total", 0),
                    "positive_grounded_criteria": view.get("positive_grounded_criteria") or [],
                    "has_hard_negative": bool(view.get("has_hard_negative")),
                },
            }
        )
    return outputs


def render_protocol() -> str:
    return """# Final Recommendation Report v1 Protocol

## 定位

本轮是离线 report rendering，不改 runtime、不改 ReviewState、不改变已有 accept/reject。它只把 `Final Recommendation View v1` 的多类推荐结果写入派生 final report。

## 输出标签

- `accept_like`
- `borderline_positive`
- `borderline_insufficient`
- `reject_like`
- `not_assessable`

## 规则边界

- runtime final decision 仍只作为 health check。
- `borderline_positive` 不映射为 accept。
- `not_assessable` 不映射为 reject。
- 本节用于论文层可诊断展示，不是新的决策阈值。
"""


def render_audit(rows: List[Dict[str, Any]]) -> str:
    counts = Counter(row["recommendation_view"] for row in rows)
    by_gold = Counter((row["gold_decision"], row["recommendation_view"]) for row in rows)
    lines = [
        "# Final Recommendation Report v1 Audit",
        "",
        "## Label Counts",
        "",
        table_row(["label", "count"]),
        table_row(["---", "---:"]),
    ]
    for label, count in counts.most_common():
        lines.append(table_row([label, count]))
    lines += [
        "",
        "## Gold x Recommendation View",
        "",
        table_row(["gold", "recommendation_view", "count"]),
        table_row(["---", "---", "---:"]),
    ]
    for (gold, label), count in sorted(by_gold.items()):
        lines.append(table_row([gold, label, count]))
    return "\n".join(lines)


def render_preview(rows: List[Dict[str, Any]]) -> str:
    lines = [
        "# Final Recommendation Report v1 Preview",
        "",
        table_row(["paper_id", "gold", "runtime_decision", "recommendation_view", "features"]),
        table_row(["---", "---", "---", "---", "---"]),
    ]
    for row in rows[:12]:
        features = row["recommendation_features"]
        summary = (
            f"real={features['real_strong_support_total']}, "
            f"nonabs={features['non_abstract_support_total']}, "
            f"ind={features['independent_support_group_total']}, "
            f"emp={features['empirical_support_total']}"
        )
        lines.append(table_row([row["paper_id"], row["gold_decision"], row["runtime_final_decision"], row["recommendation_view"], summary]))
    return "\n".join(lines)


def render_decision(rows: List[Dict[str, Any]]) -> str:
    counts = Counter(row["recommendation_view"] for row in rows)
    return f"""# Final Recommendation Report v1 Decision

## 结论

建议保留为论文层 final-view report rendering。它解决的是“最终报告如何诚实表达系统证据状态”的问题，不解决也不试图替代 runtime accept/reject。

## 关键数字

- accept_like: `{counts.get('accept_like', 0)}`
- borderline_positive: `{counts.get('borderline_positive', 0)}`
- borderline_insufficient: `{counts.get('borderline_insufficient', 0)}`
- reject_like: `{counts.get('reject_like', 0)}`
- not_assessable: `{counts.get('not_assessable', 0)}`

## 判断

本轮说明当前系统最可信的输出不是硬二分类，而是证据约束下的多类推荐视图。论文主试验可以继续报告 accept/reject health check，但主叙事应转向 recommendation calibration、support quality 和 criterion grounding。

## 下一步

如果继续推进，应做 `Mainline-Final-v1` 结果表整合：把 runtime evidence/state 指标、criterion grounding、final recommendation view 放进同一张主表，而不是继续新增 controller。
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-jsonl", type=Path, default=Path("outputs/results_main/review_infer/mainline_final_v1_9b_fulltest39_dryrun.jsonl"))
    parser.add_argument("--view-json", type=Path, default=Path("outputs/results_main/review_infer/final_recommendation_view_v1_simulation.json"))
    parser.add_argument("--output-jsonl", type=Path, default=Path("outputs/results_main/review_infer/final_recommendation_report_v1_fulltest39.jsonl"))
    parser.add_argument("--doc-dir", type=Path, default=Path("docs/experiments/mainline_current"))
    args = parser.parse_args()

    source_rows = load_jsonl(args.source_jsonl)
    view_data = load_json(args.view_json)
    output_rows = build_outputs(source_rows, view_data.get("case_rows", []))
    write_jsonl(args.output_jsonl, output_rows)
    write_md(args.doc_dir / "FINAL_RECOMMENDATION_REPORT_V1_PROTOCOL.md", render_protocol())
    write_md(args.doc_dir / "FINAL_RECOMMENDATION_REPORT_V1_AUDIT.md", render_audit(output_rows))
    write_md(args.doc_dir / "FINAL_RECOMMENDATION_REPORT_V1_PREVIEW.md", render_preview(output_rows))
    write_md(args.doc_dir / "FINAL_RECOMMENDATION_REPORT_V1_DECISION.md", render_decision(output_rows))
    print(json.dumps({"rows": len(output_rows), "output_jsonl": str(args.output_jsonl)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
