#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

try:
    import pyarrow.parquet as pq
except Exception:
    pq = None

from agent_system.environments.env_package.review.state import (
    _open_unresolved_questions,
    build_decision_hygiene_view,
    infer_final_decision,
)


def norm(x: Any) -> str:
    return str(x or "").strip().lower()


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_gold_from_summary(summary_path: Path) -> Dict[str, str]:
    if not summary_path.exists():
        return {}
    data = json.loads(summary_path.read_text(encoding="utf-8"))
    out: Dict[str, str] = {}
    for row in data.get("case_rows", []) or []:
        pid = str(row.get("paper_id") or "")
        decision = norm(row.get("gold") or row.get("gold_decision"))
        if pid and decision in {"accept", "reject"}:
            out[pid] = decision
    return out


def load_gold(dataset: Path) -> Dict[str, str]:
    if not dataset.exists() or pq is None:
        return {}
    out: Dict[str, str] = {}
    for row in pq.read_table(dataset).to_pylist():
        env = row.get("env_kwargs") or {}
        pid = row.get("id") or env.get("paper_id")
        decision = norm(row.get("decision") or env.get("ground_truth_decision"))
        if pid and decision in {"accept", "reject"}:
            out[str(pid)] = decision
    return out


def gold_for(row: Dict[str, Any], gold_map: Dict[str, str]) -> str:
    pid = str(row.get("paper_id") or "")
    explicit = norm(row.get("gold_decision") or row.get("ground_truth_decision"))
    return gold_map.get(pid) or (explicit if explicit in {"accept", "reject"} else "unknown")


def original_pred(row: Dict[str, Any]) -> str:
    st = row.get("review_state") or {}
    pred = norm(row.get("final_decision") or st.get("final_decision"))
    return pred if pred in {"accept", "reject"} else "reject"


def metric(rows: List[Dict[str, Any]], key: str) -> Dict[str, Any]:
    tp = tn = fp = fn = 0
    false_accept: List[str] = []
    false_reject: List[str] = []
    recovered_accept: List[str] = []
    for row in rows:
        gold = row["gold"]
        pred = row[key]
        if gold == "accept" and pred == "accept":
            tp += 1
            recovered_accept.append(row["paper_id"])
        elif gold == "reject" and pred == "reject":
            tn += 1
        elif gold == "reject" and pred == "accept":
            fp += 1
            false_accept.append(row["paper_id"])
        elif gold == "accept" and pred == "reject":
            fn += 1
            false_reject.append(row["paper_id"])
    n = max(1, tp + tn + fp + fn)
    accept_recall = tp / max(1, tp + fn)
    reject_recall = tn / max(1, tn + fp)
    accept_precision = tp / max(1, tp + fp)
    reject_precision = tn / max(1, tn + fn)
    accept_f1 = 0.0 if accept_precision + accept_recall == 0 else 2 * accept_precision * accept_recall / (accept_precision + accept_recall)
    reject_f1 = 0.0 if reject_precision + reject_recall == 0 else 2 * reject_precision * reject_recall / (reject_precision + reject_recall)
    return {
        "accuracy": round((tp + tn) / n, 4),
        "macro_f1": round((accept_f1 + reject_f1) / 2, 4),
        "accept_recall": round(accept_recall, 4),
        "reject_recall": round(reject_recall, 4),
        "predicted_accept_count": tp + fp,
        "false_accept_ids": false_accept,
        "false_reject_ids": false_reject,
        "recovered_accept_ids": recovered_accept,
    }


def active_flaw_count(state: Dict[str, Any]) -> int:
    return sum(
        1
        for flaw in state.get("flaw_candidates", []) or []
        if isinstance(flaw, dict) and flaw.get("status", "candidate") not in {"downgraded", "retracted"}
    )


def table(headers: List[str], rows: List[List[Any]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(x).replace("\n", " ") for x in row) + " |")
    return "\n".join(lines)


def write(path: Path, text: str) -> None:
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", type=Path, default=Path("MAINLINE_FINAL_V1_CLEAN_4B_FULLTEST39_20260502.jsonl"))
    ap.add_argument("--dataset", type=Path, default=Path("/reviewF/datasets/drmas_review/test.parquet"))
    ap.add_argument("--summary", type=Path, default=Path("MAINLINE_FINAL_V1_CLEAN_4B_FULLTEST39_20260502_SUMMARY.json"))
    ap.add_argument("--json", type=Path, default=Path("FINAL_VIEW_HYGIENE_FIX_V1_CLEAN_4B.json"))
    ap.add_argument("--outdir", type=Path, default=Path("docs/experiments/mainline_current"))
    args = ap.parse_args()

    rows = load_jsonl(args.input)
    gold = load_gold_from_summary(args.summary) or load_gold(args.dataset)
    case_rows: List[Dict[str, Any]] = []
    summary = Counter()
    for row in rows:
        st = row.get("review_state") or {}
        view = build_decision_hygiene_view(st)
        hygiene = view.get("decision_hygiene", {}) or {}
        raw_unresolved = len(_open_unresolved_questions(st))
        view_unresolved = len(_open_unresolved_questions(view))
        raw_flaws = active_flaw_count(st)
        view_flaws = active_flaw_count(view)
        raw_gaps = len(st.get("evidence_gaps", []) or [])
        view_gaps = len(view.get("evidence_gaps", []) or [])
        summary["raw_open_unresolved"] += raw_unresolved
        summary["view_open_unresolved"] += view_unresolved
        summary["raw_active_flaws"] += raw_flaws
        summary["view_active_flaws"] += view_flaws
        summary["raw_evidence_gaps"] += raw_gaps
        summary["view_evidence_gaps"] += view_gaps
        summary["deferred_unresolved_count"] += int(hygiene.get("deferred_unresolved_count", 0) or 0)
        summary["targetless_unresolved_deferred_count"] += int(hygiene.get("targetless_unresolved_deferred_count", 0) or 0)
        summary["downgraded_flaw_count"] += int(hygiene.get("downgraded_flaw_count", 0) or 0)
        summary["stale_evidence_gap_count"] += int(hygiene.get("stale_evidence_gap_count", 0) or 0)
        summary["stale_conflict_count"] += int(hygiene.get("stale_conflict_count", 0) or 0)
        case_rows.append({
            "paper_id": str(row.get("paper_id")),
            "gold": gold_for(row, gold),
            "original_pred": original_pred(row),
            "hygiene_pred": infer_final_decision(st, {}),
            "raw_unresolved": raw_unresolved,
            "view_unresolved": view_unresolved,
            "raw_gaps": raw_gaps,
            "view_gaps": view_gaps,
            "raw_active_flaws": raw_flaws,
            "view_active_flaws": view_flaws,
            "targetless_deferred": int(hygiene.get("targetless_unresolved_deferred_count", 0) or 0),
            "downgraded_flaws": int(hygiene.get("downgraded_flaw_count", 0) or 0),
            "real_strong": int(hygiene.get("real_strong_support_total", 0) or 0),
            "nonabstract_strong": int(hygiene.get("non_abstract_real_strong_support_count", 0) or 0),
        })

    metrics = {
        "original_runtime": metric(case_rows, "original_pred"),
        "hygiene_view_runtime_rule": metric(case_rows, "hygiene_pred"),
    }
    payload = {"input": str(args.input), "summary": dict(summary), "metrics": metrics, "cases": case_rows}
    args.json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    args.outdir.mkdir(parents=True, exist_ok=True)
    plan = """# Final-View Hygiene Fix v1 Plan\n\n## 目标\n\n本轮只修 2.1-2.5 中能安全落地的缺陷：final decision / final report 前的派生视图污染，而不是 live state 轨迹。\n\n## 修复范围\n\n1. targetless unresolved 不再作为 paper defect blocker，进入 final-view 时降级为 `decision_view_targetless_uncertainty`。\n2. fallback/meta flaw 的识别从 `flaw-fallback` 和 `source=fallback` 扩展到 `fallback-extraction`、`fallback_unverified`、system/meta 文本。\n3. final report strengths 只渲染 real-claim-bound strong support，避免 fallback/unbound support 被写成优势。\n4. criterion 与 weakness 渲染过滤 fallback/meta flaw，避免系统限制进入审稿维度 weakness。\n\n## 不修的范围\n\n本轮不调 accept 阈值、不改 manager、不改 recovery controller、不改 live `_refresh_state_consistency()`。原因是这些改动会改变推理轨迹，风险高于收益。\n"""
    write(args.outdir / "FINAL_VIEW_HYGIENE_FIX_V1_PLAN.md", plan)

    result_rows = [[k, v] for k, v in payload["summary"].items()]
    case_table = [[r["paper_id"], r["gold"], r["original_pred"], r["hygiene_pred"], r["raw_unresolved"], r["view_unresolved"], r["raw_gaps"], r["view_gaps"], r["raw_active_flaws"], r["view_active_flaws"], r["targetless_deferred"], r["downgraded_flaws"], r["real_strong"], r["nonabstract_strong"]] for r in case_rows]
    result = "\n\n".join([
        "# Final-View Hygiene Fix v1 Result",
        "## 结论",
        "本轮修复没有改变 live trajectory，也没有放松 binary accept/reject 阈值；它把 targetless unresolved 与 fallback/meta flaw 从 final-view 的强负面证据中剥离，减少 final report 和 criterion section 的系统性污染。runtime binary decision 仍然是保守 health check，不作为论文主指标。",
        "## 汇总",
        table(["metric", "value"], result_rows),
        "## Decision Health",
        "```json\n" + json.dumps(metrics, ensure_ascii=False, indent=2) + "\n```",
        "## 逐样本",
        table(["paper_id", "gold", "orig_pred", "hygiene_pred", "raw_unres", "view_unres", "raw_gaps", "view_gaps", "raw_flaws", "view_flaws", "targetless_def", "downgraded_flaws", "real_strong", "nonabs_strong"], case_table),
    ])
    write(args.outdir / "FINAL_VIEW_HYGIENE_FIX_V1_RESULT.md", result)
    write(args.outdir / "FINAL_VIEW_HYGIENE_FIX_V1_CASE_TABLE.md", table(["paper_id", "gold", "orig_pred", "hygiene_pred", "raw_unres", "view_unres", "raw_gaps", "view_gaps", "raw_flaws", "view_flaws", "targetless_def", "downgraded_flaws", "real_strong", "nonabs_strong"], case_table))

    print(json.dumps({"summary": dict(summary), "metrics": metrics}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
