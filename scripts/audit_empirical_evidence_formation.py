#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List

import pyarrow.parquet as pq

RESULT_RE = re.compile(r"\b(experiment|experiments|evaluation|evaluations|result|results|baseline|dataset|metric|performance|outperform|accuracy|f1|auc|benchmark)\b", re.I)
TABLE_RE = re.compile(r"\b(table|figure|fig\.?|tab\.?|ablation)\b", re.I)
METHOD_RE = re.compile(r"\b(method|approach|model|framework|algorithm|architecture|training|optimization|mechanism|objective)\b", re.I)
EMPIRICAL_RE = re.compile(r"\b(experiment|evaluation|result|baseline|dataset|metric|performance|outperform|accuracy|f1|auc|benchmark|table|figure|fig\.?|ablation)\b", re.I)
SUPPORT_STANCES = {"supports", "support", "supported", "partially_supports", "partially_support", "positive"}


def norm(value: Any) -> str:
    return str(value or "").strip().lower()


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_dataset(path: Path) -> Dict[str, Dict[str, Any]]:
    table = pq.read_table(path)
    return {str(row.get("id") or row.get("env_kwargs", {}).get("paper_id")): row for row in table.to_pylist()}


def clean_paper(prompt_messages: Any) -> str:
    text = ""
    if isinstance(prompt_messages, list):
        text = "\n".join(str(m.get("content", "")) for m in prompt_messages if isinstance(m, dict))
    else:
        text = str(prompt_messages or "")
    if "--- BEGIN PAPER ---" in text:
        text = text.split("--- BEGIN PAPER ---", 1)[1]
    if "--- END PAPER ---" in text:
        text = text.split("--- END PAPER ---", 1)[0]
    return text.strip()


def is_real_claim_id(cid: Any) -> bool:
    s = str(cid or "")
    return s.startswith("claim-") and not s.startswith("claim-fallback")


def evidence_text(ev: Dict[str, Any]) -> str:
    return " ".join(str(ev.get(k) or "") for k in ["evidence", "source", "section", "evidence_section", "rationale", "binding_rationale"])


def evidence_section(ev: Dict[str, Any]) -> str:
    text = evidence_text(ev)
    src = norm(ev.get("source"))
    if TABLE_RE.search(text) or TABLE_RE.search(src):
        return "table_or_figure_or_ablation"
    if RESULT_RE.search(text) or RESULT_RE.search(src):
        return "empirical_result"
    if METHOD_RE.search(text) or METHOD_RE.search(src):
        return "method"
    if "abstract" in src or "abstract" in norm(text):
        return "abstract"
    if "fallback" in src:
        return "fallback"
    return src or "unknown"


def is_strong_support(ev: Dict[str, Any]) -> bool:
    return norm(ev.get("strength")) == "strong" and norm(ev.get("stance")) in SUPPORT_STANCES


def gold_from_row(row: Dict[str, Any]) -> str:
    pred = norm(row.get("final_decision")) or "reject"
    correct = row.get("accept_reject_correct", row.get("decision_correct"))
    try:
        correct_f = float(correct)
    except (TypeError, ValueError):
        return "unknown"
    if pred in {"accept", "reject"}:
        return pred if correct_f >= 0.5 else ("accept" if pred == "reject" else "reject")
    return "unknown"


def classify_break(row: Dict[str, Any]) -> str:
    if not row["full_has_empirical"]:
        return "source_empirical_absent_or_keyword_missed"
    if not row["first_3072_has_empirical"]:
        return "context_visibility_loss"
    if row["evidence_fallback_count"] > 0 and row["final_empirical_strong"] == 0:
        return "json_or_fallback_structuring_loss"
    if row["final_empirical_any"] > 0 and row["final_empirical_strong"] == 0:
        return "strength_downgrade_or_policy_loss"
    if row["final_empirical_strong"] == 0:
        return "evidence_extraction_or_binding_loss"
    return "empirical_support_formed"


def analyze(input_path: Path, dataset_path: Path) -> Dict[str, Any]:
    rows = load_jsonl(input_path)
    dataset = load_dataset(dataset_path)
    out_rows = []
    agg = Counter()
    for row in rows:
        pid = row.get("paper_id")
        ds = dataset.get(str(pid), {})
        paper = clean_paper(ds.get("prompt"))
        first800, first2400, first3072 = paper[:800], paper[:2400], paper[:3072]
        rs = row.get("review_state") or {}
        evidence = [ev for ev in rs.get("evidence_map", []) or [] if isinstance(ev, dict)]
        strong = [ev for ev in evidence if is_strong_support(ev) and is_real_claim_id(ev.get("claim_id"))]
        emp_any = [ev for ev in evidence if evidence_section(ev) in {"empirical_result", "table_or_figure_or_ablation"}]
        emp_strong = [ev for ev in strong if evidence_section(ev) in {"empirical_result", "table_or_figure_or_ablation"}]
        table_strong = [ev for ev in strong if evidence_section(ev) == "table_or_figure_or_ablation"]
        method_strong = [ev for ev in strong if evidence_section(ev) == "method"]
        fallback_evidence = [ev for ev in evidence if "fallback" in norm(ev.get("source")) or str(ev.get("claim_id", "")).startswith("claim-fallback")]
        evidence_agent_turns = 0
        evidence_payload_nonempty = 0
        evidence_payload_empirical = 0
        evidence_payload_empty = 0
        for turn in row.get("turn_logs") or []:
            for wp in turn.get("worker_payloads") or []:
                if not isinstance(wp, dict) or wp.get("agent_id") != "Evidence Agent":
                    continue
                evidence_agent_turns += 1
                payload = wp.get("payload") or {}
                evs = payload.get("evidence_map") or []
                if evs:
                    evidence_payload_nonempty += 1
                    if any(EMPIRICAL_RE.search(evidence_text(ev)) for ev in evs if isinstance(ev, dict)):
                        evidence_payload_empirical += 1
                else:
                    evidence_payload_empty += 1
        item = {
            "paper_id": pid,
            "gold_decision": gold_from_row(row),
            "pred_decision": norm(row.get("final_decision")),
            "paper_chars": len(paper),
            "full_has_method": bool(METHOD_RE.search(paper)),
            "full_has_results": bool(RESULT_RE.search(paper)),
            "full_has_table_or_figure": bool(TABLE_RE.search(paper)),
            "full_has_empirical": bool(EMPIRICAL_RE.search(paper)),
            "first_800_has_empirical": bool(EMPIRICAL_RE.search(first800)),
            "first_2400_has_empirical": bool(EMPIRICAL_RE.search(first2400)),
            "first_3072_has_empirical": bool(EMPIRICAL_RE.search(first3072)),
            "first_3072_has_table_or_figure": bool(TABLE_RE.search(first3072)),
            "final_real_strong": len(strong),
            "final_method_strong": len(method_strong),
            "final_empirical_any": len(emp_any),
            "final_empirical_strong": len(emp_strong),
            "final_table_or_figure_strong": len(table_strong),
            "evidence_fallback_count": len(fallback_evidence),
            "evidence_agent_turns": evidence_agent_turns,
            "evidence_payload_nonempty_turns": evidence_payload_nonempty,
            "evidence_payload_empirical_turns": evidence_payload_empirical,
            "evidence_payload_empty_turns": evidence_payload_empty,
            "observation_context_logged": False,
        }
        item["breakpoint"] = classify_break(item)
        out_rows.append(item)
        for k, v in item.items():
            if isinstance(v, bool):
                agg[k] += int(v)
        agg["rows"] += 1
        agg["final_empirical_any"] += item["final_empirical_any"]
        agg["final_empirical_strong"] += item["final_empirical_strong"]
        agg["final_table_or_figure_strong"] += item["final_table_or_figure_strong"]
        agg["final_method_strong"] += item["final_method_strong"]
        agg["evidence_fallback_count"] += item["evidence_fallback_count"]
        agg["evidence_agent_turns"] += item["evidence_agent_turns"]
        agg["evidence_payload_empty_turns"] += item["evidence_payload_empty_turns"]
        agg["evidence_payload_empirical_turns"] += item["evidence_payload_empirical_turns"]
        agg["breakpoint_" + item["breakpoint"]] += 1
    return {"input": str(input_path), "dataset": str(dataset_path), "aggregate": dict(agg), "rows": out_rows}


def md_table(headers: List[str], rows: List[List[Any]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(x).replace("|", "/") for x in row) + " |")
    return "\n".join(lines) + "\n"


def write_outputs(result: Dict[str, Any], out_prefix: str) -> None:
    rows = result["rows"]
    agg = Counter(result["aggregate"])
    n = agg["rows"] or 1
    Path(out_prefix + ".json").write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    audit = []
    audit.append("# EMPIRICAL_EVIDENCE_FORMATION_AUDIT_9B_FULLTEST39")
    audit.append("")
    audit.append("## 结论")
    audit.append("9B fulltest39 中 empirical/table support 低，主要不是因为原始论文没有实验/结果内容，而是 evidence formation 链路没有稳定把这些内容结构化成 real-claim strong support。当前 jsonl 也没有记录 Evidence Agent 的 observation/context/raw output，因此无法直接证明模型是否看到了具体片段；这本身是 observability 缺口。")
    audit.append("")
    audit.append("## Aggregate")
    audit.append("")
    audit.append(md_table(["metric", "value"], [
        ["rows", n],
        ["full_has_empirical", agg["full_has_empirical"]],
        ["full_has_table_or_figure", agg["full_has_table_or_figure"]],
        ["first_800_has_empirical", agg["first_800_has_empirical"]],
        ["first_2400_has_empirical", agg["first_2400_has_empirical"]],
        ["first_3072_has_empirical", agg["first_3072_has_empirical"]],
        ["first_3072_has_table_or_figure", agg["first_3072_has_table_or_figure"]],
        ["final_empirical_any", agg["final_empirical_any"]],
        ["final_empirical_strong", agg["final_empirical_strong"]],
        ["final_table_or_figure_strong", agg["final_table_or_figure_strong"]],
        ["final_method_strong", agg["final_method_strong"]],
        ["evidence_fallback_count", agg["evidence_fallback_count"]],
        ["evidence_agent_turns", agg["evidence_agent_turns"]],
        ["evidence_payload_empty_turns", agg["evidence_payload_empty_turns"]],
        ["evidence_payload_empirical_turns", agg["evidence_payload_empirical_turns"]],
    ]))
    audit.append("## Breakpoint Distribution")
    audit.append("")
    bp_rows = [[k.replace("breakpoint_", ""), v] for k, v in sorted(agg.items()) if k.startswith("breakpoint_")]
    audit.append(md_table(["breakpoint", "count"], bp_rows))
    audit.append("## Interpretation")
    audit.append("")
    audit.append("- 如果 full paper 有 empirical/table 关键词，但 first 3072 没有，则是 context visibility loss。")
    audit.append("- 如果 first 3072 已有 empirical 关键词，但最终没有 empirical strong support，则是 extraction / JSON / fallback / binding 链路问题。")
    audit.append("- 当前 turn logs 没有保存 Evidence Agent observation context 或 raw output，因此无法区分“模型没看到”和“模型看到了但没结构化”。下一步若要改 runtime，优先补 observability 或做小样本 Evidence Context v2，不应直接改 decision。")
    Path("EMPIRICAL_EVIDENCE_FORMATION_AUDIT_9B_FULLTEST39.md").write_text("\n".join(audit) + "\n", encoding="utf-8")
    case_lines = ["# EMPIRICAL_EVIDENCE_FORMATION_CASE_TABLE", "", md_table(
        ["paper_id", "gold", "full_emp", "full_table", "first3072_emp", "first3072_table", "final_emp_strong", "final_table_strong", "fallback_ev", "ev_turns", "empty_payload_turns", "breakpoint"],
        [[r["paper_id"], r["gold_decision"], r["full_has_empirical"], r["full_has_table_or_figure"], r["first_3072_has_empirical"], r["first_3072_has_table_or_figure"], r["final_empirical_strong"], r["final_table_or_figure_strong"], r["evidence_fallback_count"], r["evidence_agent_turns"], r["evidence_payload_empty_turns"], r["breakpoint"]] for r in rows]
    )]
    Path("EMPIRICAL_EVIDENCE_FORMATION_CASE_TABLE.md").write_text("\n".join(case_lines) + "\n", encoding="utf-8")
    decision = []
    decision.append("# EMPIRICAL_EVIDENCE_FORMATION_NEXT_STEP")
    decision.append("")
    decision.append("## 当前判断")
    decision.append("")
    decision.append("empirical/table support 的主要问题不是 final decision，也不是 criterion rendering，而是 Evidence Agent 到 ReviewState 的证据形成链路不透明且不稳定。原文中大多数样本存在 empirical/result/table 线索，但最终 `final_empirical_strong` 和 `final_table_or_figure_strong` 很低。")
    decision.append("")
    decision.append("## 下一步唯一建议")
    decision.append("")
    decision.append("建议做 **Evidence Empirical Context & Raw Output Observability v1**，先补日志，不改行为：记录 Evidence Agent 的 context source、contains_results/table flags、raw output parse status、partial recovery、evidence dropped/downgraded reason。")
    decision.append("")
    decision.append("如果必须做功能改动，应先小样本试 `Evidence Context Selection v2`，但要受 JSON robustness 保护；不要直接扩大 context 或改 decision。")
    decision.append("")
    decision.append("## 暂时不要做")
    decision.append("")
    decision.append("- 不要把 empirical 缺失直接变成 reject。")
    decision.append("- 不要回到 criterion decision rule。")
    decision.append("- 不要盲目加长 max_model_len 或 evidence context。")
    Path("EMPIRICAL_EVIDENCE_FORMATION_NEXT_STEP.md").write_text("\n".join(decision) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=Path("WEBGPT_9B_FULLTEST39_RERUN_20260429.jsonl"))
    parser.add_argument("--dataset", type=Path, default=Path("/reviewF/datasets/drmas_review/test.parquet"))
    parser.add_argument("--out-prefix", default="EMPIRICAL_EVIDENCE_FORMATION_AUDIT_9B_FULLTEST39")
    args = parser.parse_args()
    result = analyze(args.input, args.dataset)
    write_outputs(result, args.out_prefix)
    print(json.dumps({"rows": len(result["rows"]), "aggregate": result["aggregate"]}, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
