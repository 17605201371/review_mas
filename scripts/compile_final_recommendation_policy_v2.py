#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Sequence


def table(headers: Sequence[str], rows: Sequence[Sequence[Any]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(x).replace("\n", " ") for x in row) + " |")
    return "\n".join(lines)


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def load(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def by_paper(rows: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    return {str(row["paper_id"]): row for row in rows}


def final_view_for(pid: str, support: Dict[str, Dict[str, Any]], gaps: Dict[str, Dict[str, Any]], flaws: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    s = support[pid]
    g = gaps[pid]
    f = flaws[pid]
    hard_negative = int(f.get("grounded_major_or_critical", 0)) > 0
    nonabstract = int(s.get("real_strong", 0)) - int(s.get("abstract", 0))
    empirical = int(s.get("empirical_result", 0)) + int(s.get("table_or_figure", 0)) + int(s.get("ablation", 0))
    support_quality_signal = nonabstract >= 2 and int(s.get("independent_groups", 0)) >= 2 and empirical >= 1
    targetless_unresolved = int(g.get("targetless_unresolved", 0))
    paper_unresolved = int(g.get("paper_unresolved", 0))
    stale_burden = int(g.get("stale_gaps", 0)) + int(g.get("stale_unresolved", 0)) + int(g.get("meta_unresolved", 0))
    if hard_negative:
        view = "reject_like"
        rationale = "存在 grounded major/critical flaw，作为强 reject blocker。"
    elif support_quality_signal:
        view = "borderline_positive"
        rationale = "有 non-abstract / independent / empirical support，但 support-only simulation 已产生 false accept，因此不提升为 accept_like。"
    elif targetless_unresolved >= 5 or paper_unresolved > 0:
        view = "not_assessable"
        rationale = "targetless/paper unresolved 负担较高，当前证据不足以形成可靠推荐。"
    elif stale_burden > 0:
        view = "borderline_insufficient"
        rationale = "存在 stale/meta burden，需要 final-view hygiene 解释，不能直接作为论文弱点。"
    else:
        view = "not_assessable"
        rationale = "缺少足够的高质量正向支持或 grounded hard-negative，保持不可评估。"
    return {
        "paper_id": pid,
        "gold": s.get("gold"),
        "runtime_pred": s.get("pred"),
        "final_view_v2": view,
        "rationale": rationale,
        "real_strong": s.get("real_strong", 0),
        "nonabstract_support": nonabstract,
        "empirical_support": empirical,
        "independent_groups": s.get("independent_groups", 0),
        "grounded_major_or_critical": f.get("grounded_major_or_critical", 0),
        "fallback_or_meta_flaws": f.get("fallback_or_meta", 0),
        "ungrounded_candidate_flaws": f.get("ungrounded_candidate", 0),
        "targetless_unresolved": g.get("targetless_unresolved", 0),
        "paper_unresolved": g.get("paper_unresolved", 0),
        "stale_gaps": g.get("stale_gaps", 0),
    }


def render_plan() -> str:
    return """# Final Recommendation Policy v2 Execution Plan

## 目标

基于当前 fulltest39 离线审计结果，冻结一版更安全的 final-view 推荐口径。该口径不改变 runtime、不修改 live `ReviewState`，只用于论文结果层和 case 分析。

## 背景结论

- runtime binary decision 仍是 39/39 reject，只能作为 health check。
- Evidence Binding 已稳定：fallback/unbound strong support 为 0。
- 单纯 support-quality rule 可恢复部分 accept，但会引入 false accept。
- flaw 层主要是 fallback/meta 与 ungrounded candidate，只有少量 grounded major/critical flaw。
- unresolved/gap 主要是 targetless/stale/system burden，不能直接当作 confirmed paper weakness。

## 执行步骤

1. 使用已对齐 gold label 的 fulltest39 lifecycle/support summary 作为唯一输入。
2. 将 support-quality 正向信号从 `accept_like` 降为 `borderline_positive`，除非后续人工核查证明无 hard-negative 风险。
3. 只有 grounded major/critical flaw 允许输出 `reject_like`。
4. targetless unresolved 或证据不足输出 `not_assessable`。
5. stale/meta burden 输出 `borderline_insufficient` 或在 rationale 中解释，不写成 paper weakness。
6. 输出 V2 policy、逐样本 final-view table 和执行结论。

## 禁止事项

- 不改 runtime prompt。
- 不改 final decision 阈值。
- 不做 live state hygiene mutation。
- 不回 sticky / throttle / progression gate。
- 不把 novelty/soundness/empirical adequacy 裸接入 binary decision。
"""


def render_policy(summary: Dict[str, Any]) -> str:
    return f"""# Final Recommendation Policy v2 Final

## 定位

`Final Recommendation Policy v2` 是基于当前 fulltest39 离线审计后的推荐口径。它替代“strong support 数量 -> accept”的粗规则，但不替代 runtime final decision。runtime `accept/reject` 仍只作为 health check。

## 输出标签

| 标签 | 使用条件 | binary 映射 |
| --- | --- | --- |
| `accept_like` | 暂不自动产生；需要 support-quality + hard-negative 人工核查通过后才能使用。 | 不自动映射。 |
| `borderline_positive` | 有 non-abstract、independent、empirical/table/method support，但尚未排除 false-accept 风险。 | 不映射 accept。 |
| `borderline_insufficient` | 有部分 support 或 stale/meta burden，但不足以形成可靠推荐。 | 不映射 accept。 |
| `reject_like` | 有 grounded major/critical flaw。 | 可映射 reject。 |
| `not_assessable` | 缺少足够证据、targetless unresolved 较多、或无法可靠 grounding。 | 不写成论文 weakness。 |

## V2 与 V1 的关键差异

V1 允许高精度 accept-like 作为正向推荐；V2 在当前 fulltest39 证据下更保守：support-quality rule 虽然恢复 2 个 accept，但同时产生 5 个 false accept，因此自动 `accept_like` 暂停，先输出 `borderline_positive`。

## 当前输入执行分布

| view | count |
| --- | ---: |
| accept_like | {summary.get('accept_like', 0)} |
| borderline_positive | {summary.get('borderline_positive', 0)} |
| borderline_insufficient | {summary.get('borderline_insufficient', 0)} |
| reject_like | {summary.get('reject_like', 0)} |
| not_assessable | {summary.get('not_assessable', 0)} |

## 论文写法

论文中应明确：当前系统的二分类推荐尚未成熟，但 final-view 能把“有正向 evidence 但不足以安全 accept”的样本与“真正 grounded reject-like”样本区分开。这比 always-reject 更符合审稿辅助定位。

## 下一步

在正式主试验前，对 `borderline_positive` 样本做人工核查：确认 support 是否支撑核心贡献、是否存在未捕获的 hard-negative、是否应进入 paper case study。
"""


def render_case_table(rows: List[Dict[str, Any]]) -> str:
    table_rows = [
        [
            r["paper_id"], r["gold"], r["runtime_pred"], r["final_view_v2"],
            r["real_strong"], r["nonabstract_support"], r["empirical_support"], r["independent_groups"],
            r["grounded_major_or_critical"], r["fallback_or_meta_flaws"], r["targetless_unresolved"], r["paper_unresolved"], r["rationale"],
        ]
        for r in rows
    ]
    return "# Final Recommendation View v2 Case Table\n\n" + table(
        ["paper_id", "gold", "runtime", "view_v2", "real", "nonabstract", "empirical", "groups", "grounded_major", "fallback_meta_flaws", "targetless_unresolved", "paper_unresolved", "rationale"],
        table_rows,
    )


def render_result(summary: Dict[str, Any], support_metrics: Dict[str, Any], sim_metrics: Dict[str, Any]) -> str:
    sim_rows = []
    for name, data in sim_metrics.items():
        m = data.get("metrics", {})
        sim_rows.append([name, data.get("view_counts", {}), m.get("accuracy"), m.get("macro_f1"), m.get("accept_recall"), m.get("reject_recall"), m.get("predicted_accept_count"), ", ".join(m.get("false_accept_ids") or []) or "无", ", ".join(m.get("recovered_accept_ids") or []) or "无"])
    return "\n\n".join([
        "# Final Recommendation Policy v2 Execution Result",
        "## 结论",
        "已按当前 fulltest39 审计结果执行 V2 推荐口径：不自动输出 `accept_like`，将 support-quality 正向样本标为 `borderline_positive`；只有 grounded major/critical flaw 标为 `reject_like`；证据不足或 targetless unresolved 较高标为 `not_assessable`。",
        "## V2 View 分布",
        table(["view", "count"], [[k, summary.get(k, 0)] for k in ["accept_like", "borderline_positive", "borderline_insufficient", "reject_like", "not_assessable"]]),
        "## 关键依据",
        table(["metric", "value"], [
            ["real_strong_total", support_metrics.get("real_strong_total")],
            ["strong_method", support_metrics.get("strong_method")],
            ["strong_empirical_result", support_metrics.get("strong_empirical_result")],
            ["strong_table_or_figure", support_metrics.get("strong_table_or_figure")],
            ["fallback_or_unbound_strong", support_metrics.get("fallback_or_unbound_strong", 0)],
        ]),
        "## 对比 Simulation",
        table(["rule", "view_counts", "accuracy", "macro_f1", "accept_recall", "reject_recall", "pred_accept", "false_accept", "recovered_accept"], sim_rows),
        "## 下一步",
        "不要继续调 binary decision。下一步应人工核查 `borderline_positive` 与 false-accept-risk 样本，把它们写入论文 case study 或用于定义最终 9B confirmation subset。",
    ])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="MAINLINE_FINAL_V1_CLEAN_4B_LIFECYCLE_AUDIT_V1.json", type=Path)
    parser.add_argument("--outdir", default="docs/experiments/mainline_current", type=Path)
    parser.add_argument("--output-json", default="FINAL_RECOMMENDATION_VIEW_V2_CLEAN_4B.json", type=Path)
    args = parser.parse_args()
    data = load(args.input)
    support = by_paper(data["support"]["case_rows"])
    gaps = by_paper(data["unresolved_gap"]["case_rows"])
    flaws = by_paper(data["flaw"]["case_rows"])
    rows = [final_view_for(pid, support, gaps, flaws) for pid in support]
    counts = dict(Counter(row["final_view_v2"] for row in rows))
    payload = {"input": str(args.input), "view_counts": counts, "case_rows": rows}
    args.output_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    write(args.outdir / "FINAL_RECOMMENDATION_POLICY_V2_EXECUTION_PLAN.md", render_plan())
    write(args.outdir / "FINAL_RECOMMENDATION_POLICY_V2_FINAL.md", render_policy(counts))
    write(args.outdir / "FINAL_RECOMMENDATION_VIEW_V2_CASE_TABLE.md", render_case_table(rows))
    write(args.outdir / "FINAL_RECOMMENDATION_POLICY_V2_EXECUTION_RESULT.md", render_result(counts, data["support"]["summary"], data["recommendation_simulation"]))
    print(json.dumps({"view_counts": counts, "outputs": [str(args.output_json), str(args.outdir / "FINAL_RECOMMENDATION_POLICY_V2_FINAL.md")]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
