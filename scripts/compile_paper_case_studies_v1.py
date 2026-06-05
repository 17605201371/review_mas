#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List


def read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_md(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def table_row(values: Iterable[Any]) -> str:
    return "| " + " | ".join(str(v).replace("\n", " ") for v in values) + " |"


def get_rows(path: Path) -> List[Dict[str, Any]]:
    return read_json(path).get("case_rows", [])


def by_id(rows: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    return {row["paper_id"]: row for row in rows}


def support_summary(row: Dict[str, Any]) -> str:
    return (
        f"real={row.get('real_strong_support_total', 0)}, "
        f"nonabs={row.get('non_abstract_support_total', 0)}, "
        f"ind={row.get('independent_support_group_total', 0)}, "
        f"emp={row.get('empirical_support_total', 0)}"
    )


def render_case(pid: str, title: str, rec: Dict[str, Any], note: str) -> str:
    criteria = ", ".join(rec.get("positive_grounded_criteria") or []) or "none"
    return "\n".join(
        [
            f"## {title}: `{pid}`",
            "",
            f"- gold decision: `{rec.get('gold_decision')}`",
            f"- final recommendation view: `{rec.get('recommendation_view')}`",
            f"- support summary: `{support_summary(rec)}`",
            f"- positive grounded criteria: `{criteria}`",
            f"- hard negative: `{rec.get('has_hard_negative')}`",
            "",
            f"**解释**：{note}",
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--recommendation-json", type=Path, default=Path("outputs/results_main/review_infer/final_recommendation_view_v1_simulation.json"))
    parser.add_argument("--output-md", type=Path, default=Path("docs/experiments/mainline_current/PAPER_CASE_STUDIES_V1.md"))
    args = parser.parse_args()

    rec_rows = get_rows(args.recommendation_json)
    rec = by_id(rec_rows)
    selected = [
        (
            "KI9NqjLVDT",
            "High-precision accept-like",
            "这是当前系统最可信的正向样本：真实 claim strong support、non-abstract support 和独立 support 都达到最低安全条件，并且有 grounded empirical adequacy。它说明系统不是完全没有 accept-like 能力，而是只能在证据质量足够时输出高精度正向推荐。",
        ),
        (
            "BXY6fe7q31",
            "Borderline positive gold accept",
            "该样本是 gold accept，但系统只给 borderline_positive。原因是正向证据存在，但 empirical support 不够强，criterion grounding 也不完整。它说明为了避免 false accept，系统需要诚实保留不确定性，而不是把所有正向信号都映射成 accept。",
        ),
        (
            "WNxlJJIEVj",
            "Borderline positive gold reject",
            "该样本是 gold reject，但也有 real/non-abstract/empirical support 和 positive criteria。它说明 positive support 不是 accept 的充分条件；如果没有可靠 negative blocker，系统不能安全地区分这类 false accept 风险。",
        ),
        (
            "QAAsnSRwgu",
            "Not assessable gold accept",
            "该样本是 gold accept，但 final-view 中没有形成真实 strong support 或 positive grounded criteria。它代表当前证据形成失败类型：系统不是应该 reject，而是应该承认证据不足，输出 not_assessable。",
        ),
        (
            "a6SntIisgg",
            "Reject-like gold reject",
            "这是少数 reject_like 样本。系统同时看到正向支持和 hard negative，最终推荐层把 grounded hard negative 作为主导信号。它说明 reject_like 目前覆盖率低，但这种标签比默认 reject 更可解释。",
        ),
    ]

    lines = [
        "# Paper Case Studies v1",
        "",
        "## 目的",
        "",
        "本文件把 `Final Recommendation View v1` 的代表样本转成论文可写的 case study。核心论点是：多类 recommendation view 比硬二分类更适合当前 evidence-grounded review assistance。",
        "",
    ]
    for pid, title, note in selected:
        if pid in rec:
            lines.append(render_case(pid, title, rec[pid], note))
            lines.append("")
    lines += [
        "## Case-level 结论",
        "",
        "1. `accept_like` 是高精度但低召回的正向推荐。",
        "2. `borderline_positive` 混合 gold accept 与 gold reject，不能直接映射为 accept。",
        "3. `not_assessable` 是系统诚实表达证据不足的必要类别，不应默认等同 reject。",
        "4. `reject_like` 当前覆盖率低，说明 reliable negative blocker formation 仍是限制项。",
    ]
    write_md(args.output_md, "\n".join(lines))
    print(json.dumps({"output_md": str(args.output_md), "cases": [pid for pid, _, _ in selected if pid in rec]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
