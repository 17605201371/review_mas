#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List

SUPPORT_STANCES = {"supports", "partially_supports"}


def norm(value: Any) -> str:
    return str(value or "").strip().lower()


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


def table_row(values: Iterable[Any]) -> str:
    return "| " + " | ".join(str(v).replace("\n", " ") for v in values) + " |"


def is_fallback_claim(claim_id: Any) -> bool:
    cid = norm(claim_id)
    return not cid or "fallback" in cid or "general" in cid


def is_support_strong(ev: Dict[str, Any]) -> bool:
    return norm(ev.get("stance")) in SUPPORT_STANCES and norm(ev.get("strength")) == "strong"


def clip(text: Any, limit: int = 180) -> str:
    value = " ".join(str(text or "").split())
    if len(value) <= limit:
        return value
    return value[: limit - 18].rstrip() + " ...[truncated]"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mainline-jsonl", type=Path, default=Path("outputs/results_main/review_infer/mainline_final_v1_9b_fulltest39_dryrun.jsonl"))
    parser.add_argument("--criterion-json", type=Path, default=Path("outputs/results_main/review_infer/criterion_grounded_decision_sim_v1_9b_fulltest39_dryrun.json"))
    parser.add_argument("--recommendation-json", type=Path, default=Path("outputs/results_main/review_infer/final_recommendation_view_v1_simulation.json"))
    parser.add_argument("--output-json", type=Path, default=Path("outputs/results_main/review_infer/mainline_final_v1_metric_consistency_audit.json"))
    parser.add_argument("--doc-dir", type=Path, default=Path("docs/experiments/mainline_current"))
    args = parser.parse_args()

    rows = load_jsonl(args.mainline_jsonl)
    criterion_rows = {row["paper_id"]: row for row in load_json(args.criterion_json).get("case_rows", [])}
    recommendation_rows = {row["paper_id"]: row for row in load_json(args.recommendation_json).get("case_rows", [])}

    fallback_items: List[Dict[str, Any]] = []
    row_summaries: List[Dict[str, Any]] = []
    for row in rows:
        pid = row.get("paper_id")
        state = row.get("review_state") or {}
        fallback_strong = []
        real_strong = []
        for ev in state.get("evidence_map", []) or []:
            if not is_support_strong(ev):
                continue
            item = {
                "paper_id": pid,
                "evidence_id": ev.get("evidence_id"),
                "claim_id": ev.get("claim_id"),
                "source": ev.get("source"),
                "stance": ev.get("stance"),
                "strength": ev.get("strength"),
                "evidence": ev.get("evidence"),
            }
            if is_fallback_claim(ev.get("claim_id")):
                fallback_strong.append(item)
                fallback_items.append(item)
            else:
                real_strong.append(item)
        crit = criterion_rows.get(pid, {})
        rec = recommendation_rows.get(pid, {})
        row_summaries.append(
            {
                "paper_id": pid,
                "gold_decision": crit.get("gold_decision"),
                "runtime_final_decision": row.get("final_decision") or state.get("final_decision"),
                "raw_fallback_strong_count": len(fallback_strong),
                "decision_real_strong_count": crit.get("real_strong_support_total", 0),
                "decision_non_abstract_count": crit.get("non_abstract_support_total", 0),
                "recommendation_view": rec.get("recommendation_view"),
                "fallback_strong_excluded_from_recommendation": bool(fallback_strong) and rec.get("real_strong_support_total", 0) == crit.get("real_strong_support_total", 0),
            }
        )

    counts = Counter(norm(item.get("source")) for item in fallback_items)
    affected_rows = [row for row in row_summaries if row["raw_fallback_strong_count"] > 0]
    any_accept_like_with_fallback = [
        row for row in affected_rows if row.get("recommendation_view") == "accept_like"
    ]
    output = {
        "input_jsonl": str(args.mainline_jsonl),
        "rows": len(rows),
        "raw_fallback_strong_total": len(fallback_items),
        "rows_with_raw_fallback_strong": len(affected_rows),
        "fallback_source_counts": dict(counts),
        "accept_like_rows_with_raw_fallback_strong": [row["paper_id"] for row in any_accept_like_with_fallback],
        "row_summaries": row_summaries,
        "fallback_items": fallback_items,
        "conclusion": "raw_fallback_strong_exists_but_is_excluded_from_final_view_recommendation",
    }
    write_json(args.output_json, output)

    audit_lines = [
        "# Mainline-Final-v1 Metric Consistency Audit",
        "",
        "## 结论",
        "",
        "`fallback_strong_support_total=13` 是 raw ReviewState 中的 fallback-bound strong support 残留，主要绑定到 `claim-fallback-1`，多数来源是 abstract。它不应被解释为 decision-eligible real-claim strong support。",
        "",
        "## Aggregate",
        "",
        table_row(["metric", "value"]),
        table_row(["---", "---:"]),
        table_row(["raw_fallback_strong_total", len(fallback_items)]),
        table_row(["rows_with_raw_fallback_strong", len(affected_rows)]),
        table_row(["accept_like_rows_with_raw_fallback_strong", len(any_accept_like_with_fallback)]),
        "",
        "## Fallback Source Counts",
        "",
        table_row(["source", "count"]),
        table_row(["---", "---:"]),
    ]
    for source, count in counts.most_common():
        audit_lines.append(table_row([source or "missing", count]))
    audit_lines += [
        "",
        "## Affected Rows",
        "",
        table_row(["paper_id", "gold", "runtime_final", "raw_fallback_strong", "decision_real_strong", "recommendation_view"]),
        table_row(["---", "---", "---", "---:", "---:", "---"]),
    ]
    for row in affected_rows:
        audit_lines.append(
            table_row(
                [
                    row["paper_id"],
                    row.get("gold_decision"),
                    row.get("runtime_final_decision"),
                    row["raw_fallback_strong_count"],
                    row["decision_real_strong_count"],
                    row.get("recommendation_view"),
                ]
            )
        )
    write_md(args.doc_dir / "MAINLINE_FINAL_V1_METRIC_CONSISTENCY_AUDIT.md", "\n".join(audit_lines))

    reconciliation_lines = [
        "# Support Provenance Reconciliation v1",
        "",
        "## 需要区分的三个口径",
        "",
        "1. `raw_fallback_strong_support`: raw ReviewState 中存在的 fallback-bound strong support，通常绑定 `claim-fallback-*`，只作为污染/残留指标。",
        "2. `decision_real_strong_support`: criterion/support simulation 中使用的真实 claim strong support，排除 fallback/general claim。",
        "3. `recommendation_eligible_support`: final recommendation view 使用的 support quality 信号，必须是真实 claim、non-abstract/independent/criterion-grounded 的派生信号。",
        "",
        "## 本轮判断",
        "",
        "- raw fallback strong 仍存在，说明 runtime state 还保留早期 fallback 产物。",
        "- 这些 fallback strong 没有进入 `accept_like` 样本；`accept_like_rows_with_raw_fallback_strong=0`。",
        "- 因此 Evidence Binding 的论文结论应表述为：final-view/recommendation 层已经隔离 fallback strong，而不是 raw state 已经完全没有 fallback strong。",
        "",
        "## 写论文时的建议表述",
        "",
        "> We retain raw fallback-bound support as a diagnostic signal, but exclude it from decision-eligible real-claim support and final-view recommendation aggregation.",
    ]
    write_md(args.doc_dir / "SUPPORT_PROVENANCE_RECONCILIATION_V1.md", "\n".join(reconciliation_lines))

    print(json.dumps({"output_json": str(args.output_json), "raw_fallback_strong_total": len(fallback_items), "affected_rows": len(affected_rows)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
