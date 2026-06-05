#!/usr/bin/env python3
"""Compile the Mainline-Final-v1 9B fulltest39 paper pack from existing artifacts."""

from __future__ import annotations

import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "docs" / "experiments" / "mainline_current" / "MAINLINE_FINAL_V1_9B_FULLTEST39"

RUNTIME_SUMMARY = ROOT / "outputs/results_main/review_infer/mainline_final_v1_9b_context_v2_2_fulltest39_merged_20260503_summary.json"
PREFLIGHT = ROOT / "outputs/results_main/review_infer/mainline_final_v1_9b_context_v2_2_fulltest39_merged_20260503_preflight.json"
SOFT_REC = ROOT / "outputs/results_main/review_infer/soft_evidence_recommendation_v1_9b_context_v2_2.json"
HARD_NEG = ROOT / "outputs/results_main/review_infer/hard_negative_grounding_v2_9b_context_v2_2.json"
FINAL_REPORT_SUMMARY = ROOT / "outputs/results_main/review_infer/mainline_final_v1_9b_context_v2_2_fulltest39_final_view_report_v2_summary.json"
SOFT_NEG_4B = ROOT / "outputs/results_main/review_infer/soft_negative_evidence_formation_pass_v1_4b_diagnostic9_soft_summary.json"
SOFT_NEG_9B = ROOT / "outputs/results_main/review_infer/soft_negative_evidence_formation_pass_v1_9b_diagnostic9_soft_summary.json"
SOFT_NEG_COMPACT = ROOT / "outputs/results_main/review_infer/soft_negative_extraction_compact_v1_9b_diagnostic9_soft_summary.json"

CRITERIA = [
    ("novelty_originality", "Novelty / Originality"),
    ("significance_contribution", "Significance / Contribution"),
    ("technical_soundness", "Technical Soundness"),
    ("empirical_adequacy", "Empirical Adequacy"),
    ("clarity_reproducibility", "Clarity / Reproducibility"),
]


def load_json(path: Path, required: bool = True) -> dict[str, Any]:
    if not path.exists():
        if required:
            raise FileNotFoundError(path)
        return {}
    return json.loads(path.read_text())


def pct(num: float, den: float) -> str:
    if not den:
        return "0.000"
    return f"{num / den:.3f}"


def md_table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(x) for x in row) + " |")
    return "\n".join(lines)


def criterion_stats(report_summary: dict[str, Any]) -> dict[str, Any]:
    rows = report_summary.get("rows", [])
    counts: dict[str, Counter[str]] = {key: Counter() for key, _ in CRITERIA}
    for row in rows:
        report = str(row.get("final_view_report", ""))
        for key, label in CRITERIA:
            pattern = re.compile(rf"^- {re.escape(label)}:(.*)$", re.MULTILINE)
            match = pattern.search(report)
            if not match:
                continue
            counts[key]["covered"] += 1
            line = match.group(1)
            if "[claims:" in line or "[evidence:" in line or "; evidence:" in line:
                counts[key]["grounded"] += 1
            if "not assessable" in line.lower() or "not_assessable" in line.lower():
                counts[key]["not_assessable"] += 1
            if any(token in line.lower() for token in ["excerpt", "missing input", "context is limited", "full text is unavailable"]):
                counts[key]["context_limited"] += 1
    return {"row_count": len(rows), "counts": {k: dict(v) for k, v in counts.items()}}


def recovery_metrics(summary: dict[str, Any]) -> dict[str, Any]:
    emitted = int(summary.get("patch_emitted_count", 0))
    committed = int(summary.get("patch_committed_count", 0))
    validated = int(summary.get("patch_validated_count", 0))
    return {
        "patch_emitted_count": emitted,
        "patch_validated_count": validated,
        "patch_committed_count": committed,
        "rows_with_any_commit": int(summary.get("rows_with_any_commit", 0)),
        "validation_to_commit_rate": round(committed / validated, 4) if validated else 0.0,
        "emission_to_commit_rate": round(committed / emitted, 4) if emitted else 0.0,
        "model_generated_commit_count": int(summary.get("model_generated_commit_count", 0)),
        "system_salvaged_commit_count": int(summary.get("system_salvaged_commit_count", 0)),
    }


def support_metrics(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "real_strong_support_total": summary.get("real_strong_support_total", 0),
        "nonabstract_strong_support_total": summary.get("nonabstract_strong_support_total", 0),
        "empirical_strong_support_total": summary.get("empirical_strong_support_total", 0),
        "method_strong_support_total": summary.get("method_strong_support_total", 0),
        "table_or_figure_strong_support_total": summary.get("table_or_figure_strong_support_total", 0),
        "ablation_strong_support_total": summary.get("ablation_strong_support_total", 0),
        "abstract_strong_support_total": summary.get("abstract_strong_support_total", 0),
        "fallback_strong_support_total": summary.get("fallback_strong_support_total", 0),
        "unbound_strong_support_total": summary.get("unbound_strong_support_total", 0),
        "strong_support_binding_precision": summary.get("strong_support_binding_precision", 0),
        "rows_with_2plus_real_strong_support": summary.get("rows_with_2plus_real_strong_support", 0),
        "accept_rows_with_2plus_real_strong_support": summary.get("accept_rows_with_2plus_real_strong_support", 0),
        "rows_with_empirical_support": summary.get("rows_with_empirical_support", 0),
        "accept_rows_with_empirical_support": summary.get("accept_rows_with_empirical_support", 0),
    }


def decision_metrics(summary: dict[str, Any]) -> dict[str, Any]:
    keys = [
        "row_count",
        "gold_accept",
        "gold_reject",
        "predicted_accept_count",
        "predicted_reject_count",
        "accuracy",
        "macro_f1",
        "accept_recall",
        "reject_recall",
        "true_accept_count",
        "false_accept_count",
        "false_reject_count",
        "false_accept_ids",
        "false_reject_ids",
    ]
    return {k: summary.get(k) for k in keys}


def case_lookup(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(row.get("paper_id")): row for row in rows}


def build_case_studies(soft: dict[str, Any], hard: dict[str, Any]) -> list[dict[str, Any]]:
    soft_rows = case_lookup(soft.get("case_rows", []))
    hard_rows = case_lookup(hard.get("case_rows", []))
    selected = ["jVEoydFOl9", "BXY6fe7q31", "uOrfve3prk", "ye3NrNrYOY", "hj323oR3rw"]
    studies = []
    for pid in selected:
        row = soft_rows.get(pid) or hard_rows.get(pid)
        if not row:
            continue
        hrow = hard_rows.get(pid, {})
        studies.append({
            "paper_id": pid,
            "gold": row.get("gold"),
            "runtime_pred": row.get("runtime_pred"),
            "soft_view": row.get("soft_view"),
            "final_view_v4": hrow.get("final_view_v4"),
            "real_strong": row.get("real_strong"),
            "nonabstract_support": row.get("nonabstract_support"),
            "empirical_support": row.get("empirical_support"),
            "independent_groups": row.get("independent_groups"),
            "negative_score": row.get("negative_score"),
            "uncertainty_score": row.get("uncertainty_score"),
            "v4_reason": hrow.get("v4_reason"),
        })
    return studies


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def write_spec(path: Path) -> None:
    path.write_text(
        """# MAINLINE_FINAL_V1_SPEC

## 定位

`Mainline-Final-v1` 是当前论文主线的冻结口径。它的目标不是继续追加 controller，而是把已经证明有效的 evidence / state / report 组件收束成可复现的主试验 pipeline。

## Runtime 主线组件

- `p25.1 + explicit recovery phase` 保留版。
- Evidence Context / Empirical Structuring：让 Evidence Agent 看到更有效的正文证据区域。
- Evidence Binding Robustness：强约束 evidence 绑定到真实 claim，fallback/unbound support 不进入 real support。
- Evidence JSON Robustness：减少 JSON parse failure 与 fallback payload 污染。
- Config alignment / observability：固定 `max_turns`、model、subset、sampling 等关键运行口径。

## Final-view / Offline 层

- Derived hygiene / recommendation view：只在最终解释层使用，不改 live `ReviewState`。
- Support quality audit：区分 real / non-abstract / empirical / independent support。
- Hard-negative grounding audit：区分 grounded paper weakness、context limitation、targetless unresolved、unverified negative。
- Criterion-aware final report rendering：生成 novelty、significance、soundness、empirical、clarity 五个维度的报告段落。

## 暂停且不进入主线的分支

- target sticky 系列。
- progression throttle / progression gate 系列。
- support formation pass 作为当前主线控制器。
- live state hygiene mutation。
- final decision 阈值硬调。
- 全局 fallback suppression。

## 决策口径

Runtime binary accept/reject 只作为 health check。论文主输出采用 final-view recommendation：

- `accept_like`
- `borderline_positive`
- `borderline_insufficient`
- `not_assessable_*`
- `reject_like`

其中 `borderline_positive` 不映射为 accept；它表示已有正向证据但仍需人工审查。
""",
        encoding="utf-8",
    )


def write_report(path: Path, data: dict[str, Any]) -> None:
    summary = data["runtime_summary"]
    soft = data["soft_recommendation"]
    hard = data["hard_negative"]
    criterion = data["criterion_stats"]
    preflight = data["preflight"]
    soft_neg = data["soft_negative_series"]

    lines = [
        "# MAINLINE_FINAL_V1_9B_FULLTEST39_PAPER_PACK",
        "",
        "## 总结论",
        "",
        "这份结果包说明：当前系统已经从 controller 试错阶段收束到 `Mainline-Final-v1` 主线。Evidence binding、JSON robustness、empirical/non-abstract support formation 和 criterion-aware report 都已经具备论文结果层价值；runtime binary final decision 仍然是 health check，不作为论文主指标。",
        "",
        "最关键的解释是：系统已经能形成较干净的 real-claim support，但最终推荐必须通过 final-view recommendation、support quality、hard-negative grounding 和 criterion grounding 来解释，而不能继续用二元 accept/reject 或 strong support 数量单独下结论。",
        "",
        "## 1. Config / Controller Cleanliness",
        "",
        md_table(
            ["item", "value"],
            [
                ["preflight_status", preflight.get("status")],
                ["sticky_recovery_bias", preflight.get("runtime_controller_counts", {}).get("sticky_recovery_bias", 0)],
                ["progression_gate_triggered", preflight.get("runtime_controller_counts", {}).get("progression_gate_triggered", 0)],
                ["support_formation_pass_triggered", preflight.get("runtime_controller_counts", {}).get("support_formation_pass_triggered", 0)],
                ["legacy_controller_active_turns", summary.get("legacy_controller_active_turns", 0)],
            ],
        ),
        "",
        "## 2. Runtime Decision Health Check",
        "",
        md_table(
            ["metric", "value"],
            [[k, v] for k, v in decision_metrics(summary).items() if not isinstance(v, list)],
        ),
        "",
        "Runtime binary decision 仍然是 `reject=39/39`，因此不能作为主指标。它只说明原始 final decision 仍然保守，而不是 evidence / report 层没有进展。",
        "",
        "## 3. Evidence / Support Quality",
        "",
        md_table(["metric", "value"], [[k, v] for k, v in support_metrics(summary).items()]),
        "",
        "关键点：`fallback_strong_support_total=0` 且 `strong_support_binding_precision=1.0`，说明 binding 修复站稳；`nonabstract` 与 `empirical` support 已经成为主线可报告指标。",
        "",
        "## 4. State Burden / Recovery",
        "",
        md_table(
            ["metric", "value"],
            [
                ["unresolved_count", summary.get("unresolved_count")],
                ["evidence_gap_count", summary.get("evidence_gap_count")],
                ["flaw_count", summary.get("flaw_count")],
                ["conflict_note_count", summary.get("conflict_note_count")],
                *recovery_metrics(summary).items(),
            ],
        ),
        "",
        "Recovery 框架可作为结构化状态修复模块保留，但当前 commit throughput 很低，不应作为本阶段主贡献。",
        "",
        "## 5. Final-view Recommendation",
        "",
        md_table(["view", "count"], sorted(soft.get("soft_view_counts", {}).items())),
        "",
        "严格 `accept_like` 只恢复 1 个 accept，且保持 0 false accept；`borderline_positive` 不能映射为 accept，否则 false accept 风险过高。正式论文应把 `borderline_positive` 写成需要人工审查的正向边界样本。",
        "",
        "## 6. Hard-negative / Not-assessable Decomposition",
        "",
        md_table(["view_v4", "count"], sorted(hard.get("view_v4_counts", {}).items())),
        "",
        "Hard-negative v2/v4 的价值在于把 `reject_like`、context-limited、targetless unresolved、hard-negative unverified 分开。当前 soft negative extraction 还不稳定，不进入 runtime，只作为离线诊断/人工审查辅助。",
        "",
        "## 7. Criterion-aware Report",
        "",
        md_table(
            ["criterion", "covered", "grounded", "not_assessable", "context_limited"],
            [
                [
                    label,
                    criterion["counts"].get(key, {}).get("covered", 0),
                    criterion["counts"].get(key, {}).get("grounded", 0),
                    criterion["counts"].get(key, {}).get("not_assessable", 0),
                    criterion["counts"].get(key, {}).get("context_limited", 0),
                ]
                for key, label in CRITERIA
            ],
        ),
        "",
        "Criterion section 在 final-view report v2 中稳定生成。它用于论文报告质量审计，不直接进入 runtime decision。",
        "",
        "## 8. Soft Negative Extraction 系列结论",
        "",
        md_table(
            ["run", "rows", "trusted_blocker_rows", "parse_error_rows", "conclusion"],
            [
                [
                    "4B v1.4 diagnostic",
                    soft_neg.get("4b", {}).get("rows", "n/a"),
                    soft_neg.get("4b", {}).get("trusted_blocker_rows", "n/a"),
                    soft_neg.get("4b", {}).get("parse_error_rows", "n/a"),
                    "有潜力，但只适合作离线诊断",
                ],
                [
                    "9B v1.4 diagnostic",
                    soft_neg.get("9b", {}).get("rows", "n/a"),
                    soft_neg.get("9b", {}).get("trusted_blocker_rows", "n/a"),
                    soft_neg.get("9b", {}).get("parse_error_rows", "n/a"),
                    "9B 未稳定复现 blocker",
                ],
                [
                    "9B compact diagnostic",
                    soft_neg.get("compact", {}).get("rows", "n/a"),
                    soft_neg.get("compact", {}).get("trusted_blocker_rows", "n/a"),
                    soft_neg.get("compact", {}).get("parse_error_rows", "n/a"),
                    "compact prompt 不可靠",
                ],
            ],
        ),
        "",
        "## Go / No-Go",
        "",
        "- Go：进入论文结果整理、主试验预跑和 9B 结果包分析。",
        "- Go：使用 final-view recommendation + support quality + criterion grounding 作为论文主指标。",
        "- No-Go：继续做 sticky/throttle/progression gate/controller。",
        "- No-Go：把 soft negative extraction 接入 runtime 或 final decision。",
        "- No-Go：把 runtime binary accept/reject 准确率当主指标。",
    ]
    path.write_text("\n".join(str(x) for x in lines) + "\n", encoding="utf-8")


def write_main_table(path: Path, data: dict[str, Any]) -> None:
    s = data["runtime_summary"]
    soft = data["soft_recommendation"]
    hard = data["hard_negative"]
    rows = [
        ["Runtime binary predicted accept", s.get("predicted_accept_count"), "health check only"],
        ["Runtime binary accept recall", s.get("accept_recall"), "still collapsed"],
        ["Real strong support", s.get("real_strong_support_total"), "evidence formation"],
        ["Non-abstract strong support", s.get("nonabstract_strong_support_total"), "support quality"],
        ["Empirical strong support", s.get("empirical_strong_support_total"), "support quality"],
        ["Fallback strong support", s.get("fallback_strong_support_total"), "binding safety"],
        ["Binding precision", s.get("strong_support_binding_precision"), "binding safety"],
        ["Evidence fallback payload turns", s.get("evidence_json_fallback_payload_turns"), "JSON robustness"],
        ["Patch committed", s.get("patch_committed_count"), "recovery auxiliary"],
        ["Rows with any commit", s.get("rows_with_any_commit"), "recovery auxiliary"],
        ["Soft accept_like", soft.get("soft_view_counts", {}).get("accept_like", 0), "strict final-view accept"],
        ["Soft borderline_positive", soft.get("soft_view_counts", {}).get("borderline_positive", 0), "human-review positive borderline"],
        ["Hard-negative reject_like", hard.get("view_v4_counts", {}).get("reject_like", 0), "grounded/safety reject"],
        ["Hard-negative context-limited", hard.get("view_v4_counts", {}).get("not_assessable_context_limited", 0), "not assessable"],
    ]
    path.write_text(
        "# MAINLINE_FINAL_V1_9B_MAIN_TABLE\n\n"
        + md_table(["指标", "值", "解释"], rows)
        + "\n",
        encoding="utf-8",
    )


def write_case_studies(path: Path, studies: list[dict[str, Any]]) -> None:
    rows = []
    for row in studies:
        rows.append([
            row.get("paper_id"),
            row.get("gold"),
            row.get("runtime_pred"),
            row.get("soft_view"),
            row.get("final_view_v4"),
            row.get("real_strong"),
            row.get("nonabstract_support"),
            row.get("empirical_support"),
            row.get("independent_groups"),
            row.get("v4_reason") or "",
        ])
    path.write_text(
        "# MAINLINE_FINAL_V1_9B_CASE_STUDIES\n\n"
        "这些样本用于解释论文中的关键现象：runtime decision 保守、final-view 能恢复少量 accept、borderline_positive 不能直接映射为 accept、context limitation 应进入 not-assessable。\n\n"
        + md_table(
            [
                "paper_id",
                "gold",
                "runtime_pred",
                "soft_view",
                "hard_negative_view",
                "real_strong",
                "nonabstract",
                "empirical",
                "independent_groups",
                "reason",
            ],
            rows,
        )
        + "\n",
        encoding="utf-8",
    )


def write_go_no_go(path: Path) -> None:
    path.write_text(
        """# MAINLINE_FINAL_V1_GO_NO_GO

## 结论

当前版本可以进入论文结果整理和主试验预跑，不建议继续研发新 controller。

## Go

- 使用 `Mainline-Final-v1` 作为论文主线 pipeline。
- 报告 evidence binding、JSON robustness、support quality、hard-negative grounding、criterion grounding、final-view recommendation。
- 把 runtime binary accept/reject 作为 health check，而不是主指标。
- 把 `borderline_positive` 解释为 human-review / borderline，不映射为 accept。
- 把 soft negative extraction 作为离线诊断材料，不接入 runtime。

## No-Go

- 不继续 sticky / throttle / progression gate。
- 不再靠硬阈值调 accept/reject。
- 不把 novelty / soundness / empirical adequacy 裸接入 final decision。
- 不把 context limitation、targetless unresolved 或 unverified hard-negative 当作 paper weakness。

## 下一步

1. 用本结果包写论文主结果与 failure analysis。
2. 如需正式主试验，保持同一 pipeline，只跑冻结配置，不再叠加新机制。
3. 若导师要求更饱满的审稿维度，使用 criterion-aware report 与 grounding audit，而不是 criterion-based decision rule。
""",
        encoding="utf-8",
    )


def summarize_soft_negative(data: dict[str, Any]) -> dict[str, Any]:
    if not data:
        return {}
    totals = Counter()
    for group in data.get("group_summaries", {}).values():
        totals["rows"] += int(group.get("rows", 0))
        totals["trusted_blocker_rows"] += int(group.get("trusted_blocker_rows", 0))
        totals["parse_error_rows"] += int(group.get("parse_error_rows", 0))
    return dict(totals)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    runtime = load_json(RUNTIME_SUMMARY)
    preflight = load_json(PREFLIGHT)
    soft = load_json(SOFT_REC)
    hard = load_json(HARD_NEG)
    report_summary = load_json(FINAL_REPORT_SUMMARY)
    soft_neg_4b = load_json(SOFT_NEG_4B, required=False)
    soft_neg_9b = load_json(SOFT_NEG_9B, required=False)
    soft_neg_compact = load_json(SOFT_NEG_COMPACT, required=False)

    runtime_summary = runtime.get("summary", runtime)
    data = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "runtime_summary": str(RUNTIME_SUMMARY.relative_to(ROOT)),
            "preflight": str(PREFLIGHT.relative_to(ROOT)),
            "soft_recommendation": str(SOFT_REC.relative_to(ROOT)),
            "hard_negative": str(HARD_NEG.relative_to(ROOT)),
            "final_view_report_summary": str(FINAL_REPORT_SUMMARY.relative_to(ROOT)),
        },
        "runtime_summary": runtime_summary,
        "preflight": preflight,
        "soft_recommendation": soft,
        "hard_negative": hard,
        "criterion_stats": criterion_stats(report_summary),
        "case_studies": build_case_studies(soft, hard),
        "soft_negative_series": {
            "4b": summarize_soft_negative(soft_neg_4b),
            "9b": summarize_soft_negative(soft_neg_9b),
            "compact": summarize_soft_negative(soft_neg_compact),
        },
    }

    write_spec(OUT_DIR / "MAINLINE_FINAL_V1_SPEC.md")
    write_report(OUT_DIR / "MAINLINE_FINAL_V1_9B_FULLTEST39_PAPER_PACK.md", data)
    write_main_table(OUT_DIR / "MAINLINE_FINAL_V1_9B_MAIN_TABLE.md", data)
    write_case_studies(OUT_DIR / "MAINLINE_FINAL_V1_9B_CASE_STUDIES.md", data["case_studies"])
    write_go_no_go(OUT_DIR / "MAINLINE_FINAL_V1_GO_NO_GO.md")
    write_json(OUT_DIR / "MAINLINE_FINAL_V1_9B_FULLTEST39_SUMMARY.json", {
        "generated_at_utc": data["generated_at_utc"],
        "inputs": data["inputs"],
        "decision_health": decision_metrics(runtime_summary),
        "support_quality": support_metrics(runtime_summary),
        "recovery": recovery_metrics(runtime_summary),
        "soft_view_counts": soft.get("soft_view_counts", {}),
        "hard_negative_view_counts": hard.get("view_v4_counts", {}),
        "criterion_stats": data["criterion_stats"],
        "case_studies": data["case_studies"],
        "soft_negative_series": data["soft_negative_series"],
    })

    print(f"Wrote {OUT_DIR}")


if __name__ == "__main__":
    main()
