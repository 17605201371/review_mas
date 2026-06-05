#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List


CORE_WEAK_CRITERIA = {"technical_soundness", "empirical_adequacy"}


def read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_md(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def table_row(values: Iterable[Any]) -> str:
    return "| " + " | ".join(str(v).replace("\n", " ") for v in values) + " |"


def as_int(row: Dict[str, Any], key: str) -> int:
    try:
        return int(row.get(key) or 0)
    except (TypeError, ValueError):
        return 0


def positive_grounded_count(row: Dict[str, Any]) -> int:
    return len(row.get("positive_grounded_criteria") or [])


def grounded_empirical(row: Dict[str, Any]) -> bool:
    return bool(row.get("criterion_grounded_empirical")) and row.get("criterion_rating_empirical") in {
        "moderate_or_strong",
        "neutral_or_mentioned",
    }


def has_hard_negative(row: Dict[str, Any]) -> bool:
    return (
        as_int(row, "confirmed_critical_flaw_count") > 0
        or as_int(row, "grounded_major_flaw_count") > 0
        or bool(set(row.get("grounded_weak_core_criteria") or []) & CORE_WEAK_CRITERIA)
    )


def high_precision_accept(row: Dict[str, Any]) -> bool:
    return (
        row.get("sim4_label") == "accept_like"
        and not has_hard_negative(row)
        and as_int(row, "non_abstract_support_total") >= 2
        and as_int(row, "independent_support_group_total") >= 2
        and positive_grounded_count(row) >= 2
        and (as_int(row, "empirical_support_total") >= 1 or grounded_empirical(row))
    )


def support_positive_but_insufficient(row: Dict[str, Any]) -> bool:
    return (
        not has_hard_negative(row)
        and (
            row.get("sim4_label") == "accept_like"
            or (
                as_int(row, "real_strong_support_total") >= 2
                and as_int(row, "independent_support_group_total") >= 2
                and positive_grounded_count(row) >= 1
            )
        )
    )


def classify(row: Dict[str, Any]) -> str:
    if has_hard_negative(row):
        return "reject_like"
    if high_precision_accept(row):
        return "accept_like"
    if support_positive_but_insufficient(row):
        return "borderline_positive"
    if as_int(row, "real_strong_support_total") == 0 and positive_grounded_count(row) == 0:
        return "not_assessable"
    return "borderline_insufficient"


def render_schema() -> str:
    return """# Final Recommendation View v1 Schema

## 定位

本轮只做离线推荐视图，不改 runtime、不改 final decision、不写回 ReviewState。

## 为什么不继续二分类

当前 high-precision support filter 可以把 false accept 压到 0，但只能恢复 1 个 accept。继续用 accept/reject 二分类会把系统的不确定性伪装成确定判断。

## 推荐标签

- `accept_like`: 高质量非 abstract、独立、criterion-grounded 支持足够，且没有 hard negative。
- `borderline_positive`: 有正向支持，但证据质量或维度覆盖不足以安全 accept。
- `reject_like`: 存在 confirmed critical / grounded major / grounded weak core negative。
- `not_assessable`: 缺少真实正向支持与维度 grounding，不应硬判。
- `borderline_insufficient`: 有少量信号，但不足以归入上述类别。

## 论文定位

这比强制 accept/reject 更符合审稿辅助系统：系统应把不确定样本交给人类，而不是默认 reject 或过度 accept。
"""


def render_results(rows: List[Dict[str, Any]], classified: List[Dict[str, Any]]) -> str:
    counts = Counter(item["recommendation_view"] for item in classified)
    by_gold = Counter((item["gold_decision"], item["recommendation_view"]) for item in classified)
    lines = [
        "# Final Recommendation View v1 Simulation",
        "",
        "## Label Counts",
        "",
        table_row(["label", "count"]),
        table_row(["---", "---:"]),
    ]
    for key, value in counts.most_common():
        lines.append(table_row([key, value]))
    lines += [
        "",
        "## Gold x Recommendation",
        "",
        table_row(["gold", "recommendation", "count"]),
        table_row(["---", "---", "---:"]),
    ]
    for (gold, label), value in sorted(by_gold.items()):
        lines.append(table_row([gold, label, value]))
    return "\n".join(lines)


def render_case_table(classified: List[Dict[str, Any]]) -> str:
    lines = [
        "# Final Recommendation View v1 Case Table",
        "",
        table_row(["paper_id", "gold", "recommendation", "real_strong", "nonabs", "independent", "empirical", "positive_criteria", "hard_negative"]),
        table_row(["---", "---", "---", "---:", "---:", "---:", "---:", "---", "---"]),
    ]
    for row in classified:
        lines.append(
            table_row(
                [
                    row["paper_id"],
                    row["gold_decision"],
                    row["recommendation_view"],
                    row["real_strong_support_total"],
                    row["non_abstract_support_total"],
                    row["independent_support_group_total"],
                    row["empirical_support_total"],
                    ",".join(row.get("positive_grounded_criteria") or []),
                    row["has_hard_negative"],
                ]
            )
        )
    return "\n".join(lines)


def render_decision(classified: List[Dict[str, Any]]) -> str:
    counts = Counter(item["recommendation_view"] for item in classified)
    accept_like_gold = Counter(item["gold_decision"] for item in classified if item["recommendation_view"] == "accept_like")
    return f"""# Final Recommendation View v1 Decision

## 结论

建议把下一阶段的 final-view 输出从硬二分类改成四类/五类推荐视图，而不是继续调 accept/reject 阈值。

## 关键数字

- accept_like: `{counts.get('accept_like', 0)}`
- borderline_positive: `{counts.get('borderline_positive', 0)}`
- reject_like: `{counts.get('reject_like', 0)}`
- not_assessable: `{counts.get('not_assessable', 0)}`
- accept_like gold 分布: `{dict(accept_like_gold)}`

## 判断

当前证据链支持高精度 accept-like，但不支持高召回二分类 accept。负向 blocker formation 覆盖不足，因此不应为了压 false accept 继续硬造 blocker。

下一步应做 `Final Recommendation View v1` 的论文层整合：

1. runtime final decision 仍作为 health check。
2. final-view report 输出 `accept_like / borderline_positive / reject_like / not_assessable`。
3. `borderline_positive` 不映射为 accept，用于展示系统可诊断的不确定性。
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-json", default="outputs/results_main/review_infer/criterion_grounded_decision_sim_v1_9b_fulltest39_dryrun.json")
    parser.add_argument("--output-json", default="outputs/results_main/review_infer/final_recommendation_view_v1_simulation.json")
    parser.add_argument("--doc-dir", default="docs/experiments/mainline_current")
    args = parser.parse_args()

    data = read_json(Path(args.input_json))
    rows = data.get("case_rows", [])
    classified: List[Dict[str, Any]] = []
    for row in rows:
        classified.append(
            {
                "paper_id": row["paper_id"],
                "gold_decision": row.get("gold_decision"),
                "recommendation_view": classify(row),
                "real_strong_support_total": as_int(row, "real_strong_support_total"),
                "non_abstract_support_total": as_int(row, "non_abstract_support_total"),
                "independent_support_group_total": as_int(row, "independent_support_group_total"),
                "empirical_support_total": as_int(row, "empirical_support_total"),
                "positive_grounded_criteria": row.get("positive_grounded_criteria") or [],
                "has_hard_negative": has_hard_negative(row),
            }
        )

    output = {
        "input_json": args.input_json,
        "rows": len(classified),
        "label_counts": dict(Counter(item["recommendation_view"] for item in classified)),
        "gold_by_label": {
            f"{gold}:{label}": count
            for (gold, label), count in Counter((item["gold_decision"], item["recommendation_view"]) for item in classified).items()
        },
        "case_rows": classified,
    }
    write_json(Path(args.output_json), output)
    doc_dir = Path(args.doc_dir)
    write_md(doc_dir / "FINAL_RECOMMENDATION_VIEW_V1_SCHEMA.md", render_schema())
    write_md(doc_dir / "FINAL_RECOMMENDATION_VIEW_V1_SIMULATION.md", render_results(rows, classified))
    write_md(doc_dir / "FINAL_RECOMMENDATION_VIEW_V1_CASE_TABLE.md", render_case_table(classified))
    write_md(doc_dir / "FINAL_RECOMMENDATION_VIEW_V1_DECISION.md", render_decision(classified))
    print(json.dumps({"output_json": args.output_json, "rows": len(classified), "label_counts": output["label_counts"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
