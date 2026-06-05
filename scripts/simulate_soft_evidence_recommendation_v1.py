#!/usr/bin/env python3
"""Offline soft evidence recommendation simulation.

This script does not change runtime decisions. It turns support quality,
criterion grounding, and hard-negative evidence into soft scores so that the
paper-level recommendation is not driven by a single hard support threshold.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def clamp(value: float, low: float = 0.0, high: float = 10.0) -> float:
    return max(low, min(high, value))


def safe_num(value: Any) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def soft_scores(hn_row: Dict[str, Any], criterion_row: Dict[str, Any]) -> Dict[str, Any]:
    real = safe_num(hn_row.get("real_strong"))
    nonabs = safe_num(hn_row.get("nonabstract_support"))
    empirical = safe_num(hn_row.get("empirical_support"))
    independent = safe_num(hn_row.get("independent_groups"))
    grounded_hn = safe_num(hn_row.get("grounded_hard_negative_v2_count"))
    context_limit = safe_num(hn_row.get("context_limitation_count"))
    ungrounded_neg = safe_num(hn_row.get("ungrounded_negative_count"))
    targetless = safe_num(hn_row.get("targetless_open_question_count"))
    positive_criteria = safe_num(criterion_row.get("criterion_positive_grounded_count"))
    negative_criteria = safe_num(criterion_row.get("criterion_negative_grounded_count"))
    not_assessable_criteria = safe_num(criterion_row.get("criterion_not_assessable_count"))
    meta_criteria = len(criterion_row.get("meta_leakage_criteria") or [])

    support_score = (
        min(real, 4) * 0.8
        + min(nonabs, 4) * 0.7
        + min(empirical, 4) * 0.9
        + min(independent, 4) * 0.8
        + min(positive_criteria, 5) * 1.0
    )
    negative_score = (
        min(grounded_hn, 4) * 2.4
        + min(negative_criteria, 5) * 1.4
        + min(ungrounded_neg, 5) * 0.45
    )
    uncertainty_score = (
        min(context_limit, 6) * 0.75
        + min(targetless, 8) * 0.22
        + min(not_assessable_criteria, 5) * 0.6
        + min(meta_criteria, 5) * 0.65
    )
    # Uncertainty is not a hard blocker, but it should materially reduce
    # accept-like confidence. Otherwise context-limited cases become false
    # accepts as soon as they have local positive support.
    net_support = support_score - negative_score - uncertainty_score * 0.70
    reject_pressure = negative_score + uncertainty_score * 0.18 - support_score * 0.15

    if reject_pressure >= 3.0 and negative_score >= 2.4:
        view = "reject_like"
        reason = "grounded_negative_pressure_dominates"
    elif uncertainty_score >= 4.0 and support_score >= 4.0:
        view = "not_assessable_evidence_conflict"
        reason = "positive_support_but_review_context_or_target_uncertain"
    elif uncertainty_score >= 4.0:
        view = "not_assessable_uncertain"
        reason = "high_uncertainty_without_enough_grounded_signal"
    elif net_support >= 7.0 and negative_score <= 1.2:
        view = "accept_like"
        reason = "high_grounded_support_low_negative_pressure"
    elif net_support >= 3.5:
        view = "borderline_positive"
        reason = "positive_signal_exceeds_negative_pressure_but_not_decisive"
    elif reject_pressure >= 1.8:
        view = "reject_like"
        reason = "negative_pressure_exceeds_positive_support"
    else:
        view = "borderline_insufficient"
        reason = "insufficient_grounded_positive_or_negative_signal"

    return {
        "support_score": round(clamp(support_score), 3),
        "negative_score": round(clamp(negative_score), 3),
        "uncertainty_score": round(clamp(uncertainty_score), 3),
        "net_support": round(net_support, 3),
        "reject_pressure": round(reject_pressure, 3),
        "soft_view_v1": view,
        "soft_reason": reason,
    }


def metrics(rows: Iterable[Dict[str, Any]], accept_views: set[str]) -> Dict[str, Any]:
    tp = tn = fp = fn = 0
    false_accept: List[str] = []
    recovered_accept: List[str] = []
    for row in rows:
        gold = row.get("gold")
        pred_accept = row.get("soft_view_v1") in accept_views
        if gold == "accept" and pred_accept:
            tp += 1
            recovered_accept.append(str(row["paper_id"]))
        elif gold == "accept":
            fn += 1
        elif gold == "reject" and pred_accept:
            fp += 1
            false_accept.append(str(row["paper_id"]))
        elif gold == "reject":
            tn += 1
    total = max(1, tp + tn + fp + fn)
    acc = (tp + tn) / total
    ar = tp / max(1, tp + fn)
    rr = tn / max(1, tn + fp)
    ap = tp / max(1, tp + fp)
    rp = tn / max(1, tn + fn)
    af1 = 0.0 if ap + ar == 0 else 2 * ap * ar / (ap + ar)
    rf1 = 0.0 if rp + rr == 0 else 2 * rp * rr / (rp + rr)
    return {
        "accuracy": round(acc, 4),
        "macro_f1": round((af1 + rf1) / 2, 4),
        "accept_recall": round(ar, 4),
        "reject_recall": round(rr, 4),
        "predicted_accept_count": tp + fp,
        "false_accept_ids": false_accept,
        "recovered_accept_ids": recovered_accept,
    }


def table(headers: Sequence[str], rows: Sequence[Sequence[Any]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(cell).replace("\n", " ") for cell in row) + " |")
    return "\n".join(lines)


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def render_docs(payload: Dict[str, Any], outdir: Path) -> None:
    rows = payload["case_rows"]
    write(
        outdir / "SOFT_EVIDENCE_RECOMMENDATION_V1_SCHEMA.md",
        """# Soft Evidence Recommendation v1 Schema

本层是离线 recommendation simulation，不改 runtime。目标是减少单条硬约束对 final recommendation 的支配。

核心字段：

- `support_score`: real / non-abstract / empirical / independent support 与 positive grounded criterion 的软分。
- `negative_score`: grounded hard-negative、negative grounded criterion、ungrounded negative unresolved 的软分。
- `uncertainty_score`: context limitation、targetless unresolved、not-assessable criterion、meta leakage 的不确定性分。
- `net_support`: support_score 减去 negative 与 uncertainty 折扣后的净正向信号。
- `reject_pressure`: negative 与 uncertainty 对 reject-like 的压力。

原则：模型或 report 负责产生 criterion / evidence 信号；规则只负责 provenance 约束和软聚合，不把 novelty / soundness 裸规则化。
""",
    )
    view_rows = [[k, v] for k, v in sorted(payload["soft_view_counts"].items())]
    write(
        outdir / "SOFT_EVIDENCE_RECOMMENDATION_V1_AUDIT.md",
        "# Soft Evidence Recommendation v1 Audit\n\n"
        + table(["soft_view_v1", "count"], view_rows)
        + "\n\n## Score averages\n\n"
        + table(["score", "avg"], [[k, v] for k, v in payload["score_averages"].items()]),
    )
    sim_rows = [
        [
            name,
            data["accuracy"],
            data["macro_f1"],
            data["accept_recall"],
            data["reject_recall"],
            data["predicted_accept_count"],
            ", ".join(data["false_accept_ids"]) or "无",
            ", ".join(data["recovered_accept_ids"]) or "无",
        ]
        for name, data in payload["simulations"].items()
    ]
    write(
        outdir / "SOFT_EVIDENCE_RECOMMENDATION_V1_SIMULATION.md",
        "# Soft Evidence Recommendation v1 Simulation\n\n"
        + table(
            ["mapping", "accuracy", "macro_f1", "accept_recall", "reject_recall", "pred_accept", "false_accept", "recovered_accept"],
            sim_rows,
        ),
    )
    case_rows = [
        [
            row["paper_id"],
            row["gold"],
            row["old_view_v4"],
            row["soft_view_v1"],
            row["soft_reason"],
            row["support_score"],
            row["negative_score"],
            row["uncertainty_score"],
            row["real_strong"],
            row["empirical_support"],
            row["grounded_hard_negative_v2_count"],
        ]
        for row in rows
    ]
    write(
        outdir / "SOFT_EVIDENCE_RECOMMENDATION_V1_CASE_TABLE.md",
        "# Soft Evidence Recommendation v1 Case Table\n\n"
        + table(
            [
                "paper_id",
                "gold",
                "v4",
                "soft_v1",
                "reason",
                "support_score",
                "negative_score",
                "uncertainty_score",
                "real",
                "empirical",
                "grounded_hn",
            ],
            case_rows,
        ),
    )
    write(
        outdir / "SOFT_EVIDENCE_RECOMMENDATION_V1_DECISION.md",
        f"""# Soft Evidence Recommendation v1 Decision

## 结论

v1 证明 recommendation 可以从硬约束转成软聚合，但当前 9B fulltest39 仍不支持把 recommendation 直接映射成二元 accept/reject。

## 分布

{table(['soft_view_v1', 'count'], view_rows)}

## 关键模拟

{table(['mapping', 'accuracy', 'macro_f1', 'accept_recall', 'reject_recall', 'pred_accept', 'false_accept', 'recovered_accept'], sim_rows)}

## 解释

- `support_score` 已经能表达正向 evidence 强度，不再只看 support 数量。
- `negative_score` 和 `uncertainty_score` 作为软分进入推荐，不再由单条硬规则直接拦截。
- 但当把 `borderline_positive` 或 `accept_like` 映射为 accept 时，仍需重点看 false accept 风险。

## 下一步

不要继续硬调 final decision。若要进一步提高 accept recovery，应做 `Hard-Negative Extraction v1` 或 criterion assessment 的模型化标注，让系统产生更准确的 grounded negative/positive criterion，而不是继续改聚合阈值。
""",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--hard-negative-json", type=Path, required=True)
    parser.add_argument("--criterion-json", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--doc-dir", type=Path, required=True)
    args = parser.parse_args()

    hn = load_json(args.hard_negative_json)
    criterion = {str(row.get("paper_id")): row for row in load_json(args.criterion_json).get("rows", [])}
    rows: List[Dict[str, Any]] = []
    for row in hn.get("case_rows", []):
        pid = str(row.get("paper_id"))
        c = criterion.get(pid, {})
        scored = {**row, **soft_scores(row, c)}
        scored["old_view_v4"] = row.get("final_view_v4")
        rows.append(scored)

    score_keys = ["support_score", "negative_score", "uncertainty_score", "net_support", "reject_pressure"]
    score_avgs = {k: round(sum(float(row.get(k, 0)) for row in rows) / max(1, len(rows)), 3) for k in score_keys}
    payload = {
        "inputs": {"hard_negative_json": str(args.hard_negative_json), "criterion_json": str(args.criterion_json)},
        "soft_view_counts": dict(Counter(row["soft_view_v1"] for row in rows)),
        "score_averages": score_avgs,
        "case_rows": rows,
        "simulations": {
            "strict_accept_like_only": metrics(rows, {"accept_like"}),
            "accept_or_borderline_positive_as_accept": metrics(rows, {"accept_like", "borderline_positive"}),
            "all_non_reject_as_accept_upper_bound": metrics(rows, {row["soft_view_v1"] for row in rows if row["soft_view_v1"] != "reject_like"}),
        },
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    render_docs(payload, args.doc_dir)
    print(json.dumps({k: payload[k] for k in ["soft_view_counts", "score_averages", "simulations"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
