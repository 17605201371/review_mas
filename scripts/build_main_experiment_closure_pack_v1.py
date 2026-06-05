#!/usr/bin/env python3
"""Build the Main Experiment Closure Pack v1 from existing audit outputs."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def md_table(headers: list[str], rows: list[list[Any]]) -> str:
    out = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(x).replace("|", "\\|").replace("\n", " ") for x in row) + " |")
    return "\n".join(out)


def pct(v: Any) -> str:
    try:
        return f"{float(v):.4f}"
    except Exception:
        return str(v)


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.strip() + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=Path("docs/experiments/mainline_current/MAIN_EXPERIMENT_CLOSURE_PACK_V1"))
    args = parser.parse_args()

    root = Path(".")
    summary = load_json(root / "docs/experiments/mainline_current/MAINLINE_FINAL_V1_9B_FULLTEST39/MAINLINE_FINAL_V1_9B_FULLTEST39_SUMMARY.json")
    final_view = load_json(root / "docs/experiments/mainline_current/FINAL_RECOMMENDATION_VIEW_RUNTIME_V1/final_recommendation_view_runtime_v1_9b_context_v2_2_eval.json")
    neg = load_json(root / "docs/experiments/mainline_current/NEGATIVE_LIFECYCLE_HARD_NEGATIVE_V1/negative_lifecycle_hard_negative_audit_v1_9b.json")
    gap = load_json(root / "docs/experiments/mainline_current/NEGATIVE_LIFECYCLE_HARD_NEGATIVE_V1/open_gap_resolution_audit_v1_9b.json")
    case = load_json(root / "docs/experiments/mainline_current/HARD_NEGATIVE_CASE_STUDY_V1/hard_negative_case_study_v1.json")

    d = summary["decision_health"]
    s = summary["support_quality"]
    r = summary["recovery"]
    criterion = summary["criterion_stats"]["counts"]
    negs = neg["summary"]
    gaps = gap["summary"]
    cases = case["summary"]
    out = args.output_dir

    closure_summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_summary": "docs/experiments/mainline_current/MAINLINE_FINAL_V1_9B_FULLTEST39/MAINLINE_FINAL_V1_9B_FULLTEST39_SUMMARY.json",
        "row_count": d["row_count"],
        "binary_decision_health": d,
        "final_recommendation_view_counts": final_view["recommendation_view_counts"],
        "support_quality": s,
        "recovery": r,
        "negative_lifecycle_summary": negs,
        "open_gap_summary": gaps,
        "hard_negative_case_summary": cases,
    }
    write(out / "main_experiment_closure_pack_v1_summary.json", json.dumps(closure_summary, ensure_ascii=False, indent=2))

    locked_spec = f"""
# MAINLINE_FINAL_V1_LOCKED_SPEC

## 封版结论

`Mainline-Final-v1` 的论文主线版本已经冻结为：`p25.1 + explicit recovery phase` 加上 evidence binding / JSON robustness / final-view recommendation / criterion-aware report / offline lifecycle audits。它不是一个继续叠加 controller 的实验分支。

## Runtime 主线包含

- `p25.1 + explicit recovery phase`：保留显式 recovery phase 作为结构化状态修复框架。
- Evidence Binding Robustness：强支持必须绑定到真实 claim，不允许 fallback/unbound support 进入 accept 信号。
- Evidence JSON Robustness：降低 evidence payload parse/fallback 污染。
- Evidence context / empirical structuring：支持 method / empirical / result-oriented support formation。
- Final Recommendation View Runtime v1：输出 `accept_like`、`borderline_positive`、`borderline_insufficient`、`not_assessable_uncertain`、`reject_like`。
- Conservative binary projection：只有严格 `accept_like` 映射为 binary `accept`；二元 accept/reject 只作为 health check。

## Final-view / offline 层包含

- Derived hygiene view：只在 final decision/report 前解释 stale gap、context/meta unresolved、fallback/meta flaw，不修改 live trajectory。
- Criterion-aware final report：覆盖 novelty、significance、technical soundness、empirical adequacy、clarity/reproducibility。
- Support quality audit：区分 real/non-abstract/empirical/method/table/ablation support。
- Hard-negative case study：解释 high-support reject 与 accept-protect 样本。

## 明确不进入主线

- Sticky 系列。
- Throttle / progression gate 系列。
- Support formation pass 作为独立 controller。
- Live state hygiene mutation。
- 全局 fallback suppression。
- Hard-negative prompt family runtime 化。
- 直接调 binary accept/reject 阈值。

## 论文主指标口径

主指标不是 binary accuracy，而是 evidence alignment、support quality、state hygiene、criterion grounding、final-view recommendation distribution 与 recovery process quality。Binary accept/reject 仅作为健康检查和 collapse 诊断。
"""
    write(out / "MAINLINE_FINAL_V1_LOCKED_SPEC.md", locked_spec)

    main_table = "\n".join([
        "# MAIN_RESULTS_TABLE_9B_FULLTEST39",
        "",
        "## 9B Fulltest39 主结果表",
        "",
        md_table(
            ["group", "metric", "value", "interpretation"],
            [
                ["Decision Health", "row_count", d["row_count"], "39 条 fulltest"],
                ["Decision Health", "gold_accept/gold_reject", f"{d['gold_accept']} / {d['gold_reject']}", "gold 分布"],
                ["Decision Health", "runtime predicted accept/reject", f"{d['predicted_accept_count']} / {d['predicted_reject_count']}", "runtime binary 仍 collapse，只作 health check"],
                ["Decision Health", "accuracy", pct(d["accuracy"]), "受 reject skew 影响，不是主指标"],
                ["Decision Health", "macro_f1", pct(d["macro_f1"]), "binary health check"],
                ["Final-view Recommendation", "view_counts", final_view["recommendation_view_counts"], "论文主推荐层"],
                ["Final-view Recommendation", "accept_like / false_accept", f"{len(final_view['accept_like_ids'])} / {len(final_view['false_accept_ids'])}", "保守恢复 1 个 accept-like，0 false accept"],
                ["Support Quality", "real_strong_support_total", s["real_strong_support_total"], "强支持已绑定真实 claim"],
                ["Support Quality", "nonabstract_strong_support_total", s["nonabstract_strong_support_total"], "非摘要支持形成稳定"],
                ["Support Quality", "empirical_strong_support_total", s["empirical_strong_support_total"], "经验/结果支持形成稳定"],
                ["Support Quality", "fallback_strong_support_total", s["fallback_strong_support_total"], "fallback strong 污染为 0"],
                ["Criterion", "coverage", "39/39 all five criteria", "criterion-aware report 稳定生成"],
                ["Criterion", "grounded novelty/significance/soundness/empirical/clarity", f"{criterion['novelty_originality']['grounded']} / {criterion['significance_contribution']['grounded']} / {criterion['technical_soundness']['grounded']} / {criterion['empirical_adequacy']['grounded']} / {criterion['clarity_reproducibility']['grounded']}", "grounding 质量仍是报告层指标"],
                ["Negative Lifecycle", "raw unresolved/gap/flaw/conflict", f"{negs['raw_unresolved_total']} / {negs['raw_gap_total']} / {negs['raw_flaw_total']} / {negs['raw_conflict_total']}", "raw negative burden 高，但不能直接当 paper defect"],
                ["Negative Lifecycle", "hygiene open unresolved / gap", f"{negs['hygiene_open_unresolved_total']} / {negs['hygiene_gap_total']}", "final-view 已过滤 context/meta/stale burden"],
                ["Open Gap", "open_gap_total", gaps["open_gap_total"], "仍需作为 limitation / future work"],
                ["Recovery", "patch emitted/validated/committed", f"{r['patch_emitted_count']} / {r['patch_validated_count']} / {r['patch_committed_count']}", "recovery 框架可运行，但非主增益"],
                ["Hard Negative", "status_counts", cases["hard_negative_status_counts"], "稳定 hard-negative blocker 仍弱"],
                ["Hard Negative", "false_accept_risk / accept_protect", f"{cases['bucket_counts'].get('false_accept_risk_reject_cases', 0)} / {cases['bucket_counts'].get('accept_protect_cases', 0)}", "解释为什么不能硬接 support count"],
            ],
        ),
        "",
        "## 解释",
        "",
        "这张表支持当前论文主线：系统已经改善 evidence binding、support formation、criterion report 和 final-view hygiene；但 binary final decision 仍不能作为主指标。正式论文应强调 evidence-aligned recommendation view，而不是二分类准确率。",
    ])
    write(out / "MAIN_RESULTS_TABLE_9B_FULLTEST39.md", main_table)

    readiness = f"""
# MAIN_EXPERIMENT_FINAL_READINESS_AUDIT

## 总判断

当前可以进入论文主试验收口 / dry-run 结果整理；不建议继续 runtime 机制研发。若要做正式 9B 主实验，应该使用封版 pipeline 复跑，而不是继续添加 sticky/throttle/gate/hard-negative controller。

## 已解决项

- Evidence Binding：`fallback_strong_support_total={s['fallback_strong_support_total']}`，support 绑定污染已基本压住。
- Evidence Support：`real_strong={s['real_strong_support_total']}`、`nonabstract={s['nonabstract_strong_support_total']}`、`empirical={s['empirical_strong_support_total']}`。
- Final-view recommendation：`accept_like=1`，`false_accept=0`，binary projection 保守。
- Criterion report：五个审稿维度 39/39 均覆盖。
- 旧 controller：不再作为主线贡献，已从论文主线排除。

## 未解决但已收束的风险

- Runtime binary decision 仍偏 reject：`predicted_accept={d['predicted_accept_count']}`，所以 binary decision 只作为 health check。
- Hard-negative grounding 弱：`grounded_blocker_found=1`，多数 blocker 仍是 unverified candidate。
- Open gaps 仍存在：`open_gap_total={gaps['open_gap_total']}`，需要作为 limitation / future work。
- Recovery commit 率低：`patch_committed={r['patch_committed_count']}`，recovery 是结构化过程指标，不是当前主增益。

## 是否阻止主试验

不阻止主试验收口，但阻止把 binary accept/reject accuracy 当论文主结果。主试验应汇报：support quality、binding precision、criterion grounding、final-view recommendation、negative lifecycle 和 recovery funnel。
"""
    write(out / "MAIN_EXPERIMENT_FINAL_READINESS_AUDIT.md", readiness)

    policy = """
# FINAL_RECOMMENDATION_POLICY_FOR_PAPER

## 决策口径

论文中不把 runtime binary accept/reject 作为主推荐输出。Binary decision 只用于健康检查，判断系统是否出现 always-reject 或 false-accept collapse。

正式推荐采用 final-view recommendation：

- `accept_like`：正向 support 充足、支持质量较高、没有 grounded hard-negative blocker。
- `borderline_positive`：正向 support 明显，但仍有未验证 gap / blocker；应交给 human review，不自动 accept。
- `borderline_insufficient`：部分 support 存在，但不足以形成 accept-like，且缺少稳定 hard-negative。
- `not_assessable_uncertain`：上下文、target 或 evidence 不足，不能可靠判断。
- `reject_like`：存在 grounded major/critical flaw 或明确 paper-grounded blocker。

## 聚合原则

- Strong support 数量不能直接映射 accept。
- Positive criterion 不能裸接 decision。
- Raw unresolved / gap / candidate flaw 不能直接映射 reject。
- Fallback/meta/context limitation 不能写成 paper weakness。
- `borderline_positive` 与 `borderline_insufficient` 应作为审稿辅助中的 human-review routing。

## 论文表述

可以写为：We do not treat final recommendation as a free-form binary model judgment. We derive an evidence-grounded recommendation view over the final ReviewState and use binary accept/reject only as a diagnostic health check.
"""
    write(out / "FINAL_RECOMMENDATION_POLICY_FOR_PAPER.md", policy)

    limitation = f"""
# HARD_NEGATIVE_LIMITATION_CASEBOOK

## 核心限制

当前系统能形成正向 evidence support，但还不能稳定形成 paper-grounded hard-negative blocker。这是 final recommendation 不能进一步激进映射为 accept 的主要原因。

## 量化信号

- high-support gold reject：`{cases['bucket_counts'].get('false_accept_risk_reject_cases', 0)}` 条。
- accept-protect：`{cases['bucket_counts'].get('accept_protect_cases', 0)}` 条。
- hard-negative status：`{cases['hard_negative_status_counts']}`。

## 关键案例

- `9zEBK3E9bX`：gold reject，但有 3 条 empirical real support；说明 support-count rule 会产生 false accept 风险。
- `mHv6wcBb0z`：有正向 support 与 unverified conflict，说明 context-limited blocker 不能直接当稳定 hard negative。
- `jVEoydFOl9`：gold accept 且 `accept_like`，说明 final-view hygiene 可以保护强支持样本。
- `KI9NqjLVDT`：gold accept 且 borderline_positive，说明 borderline routing 比 binary reject 更合理。

## 论文使用方式

这部分应写入 limitation / discussion：hard-negative grounding 是剩余研究瓶颈，不是当前 runtime controller 已解决的问题。下一阶段可研究 criterion-specific negative evidence extraction，但不应在本论文主线里硬接 runtime decision。
"""
    write(out / "HARD_NEGATIVE_LIMITATION_CASEBOOK.md", limitation)

    gng = """
# GO_NO_GO_MAIN_EXPERIMENT

## 结论

Go for main-experiment closure / paper writing. No-Go for adding new runtime controllers.

## Go 条件满足情况

- 9B fulltest39 已有完整结果包。
- Evidence binding 与 JSON robustness 已稳定。
- Criterion-aware report 可以稳定生成。
- Final-view recommendation 已安全恢复 1 个 accept_like，未引入 false accept。
- Hard-negative limitation 已有 casebook 支撑。

## No-Go 条件

- 不应把 binary accept/reject accuracy 当主结果。
- 不应把 hard-negative extraction runtime 化。
- 不应继续 sticky / throttle / progression gate。
- 不应为提升 accept recall 直接放宽 binary threshold。

## 下一步

如果需要新增实验，只做封版 pipeline 的正式 9B rerun 或复现性确认；如果不跑新实验，则直接进入论文写作：方法、主结果表、case study、limitation / discussion。
"""
    write(out / "GO_NO_GO_MAIN_EXPERIMENT.md", gng)

    print(json.dumps({"output_dir": str(out), "files": [p.name for p in sorted(out.iterdir())]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
