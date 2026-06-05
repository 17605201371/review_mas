#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Sequence

CRITERIA = [
    ("novelty", "Novelty / Originality"),
    ("significance", "Significance / Contribution"),
    ("soundness", "Technical Soundness"),
    ("empirical", "Empirical Adequacy"),
    ("clarity", "Clarity / Reproducibility"),
]

LABELS = {
    "novelty": "novelty_originality",
    "significance": "significance_contribution",
    "soundness": "technical_soundness",
    "empirical": "empirical_adequacy",
    "clarity": "clarity_reproducibility",
}


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def md_table(headers: Sequence[str], rows: Sequence[Sequence[Any]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(x).replace("\n", " ") for x in row) + " |")
    return "\n".join(lines) + "\n"


def status_for_link(link: Dict[str, Any]) -> str:
    pos = bool(link.get("positive_evidence_ids"))
    neg = bool(link.get("negative_evidence_ids") or link.get("flaw_ids"))
    if pos and neg:
        return "mixed_grounded"
    if pos:
        return "positive_grounded"
    if neg:
        return "negative_grounded"
    return "not_assessable"


def render_criterion_line(key: str, title: str, row: Dict[str, Any]) -> str:
    links = (row.get("criterion_links") or {}).get(key, {})
    status = status_for_link(links)
    evidence_ids = [x for x in (links.get("positive_evidence_ids") or []) + (links.get("negative_evidence_ids") or []) if x]
    flaw_ids = [x for x in links.get("flaw_ids") or [] if x]
    sections = sorted(set(x for x in links.get("sections") or [] if x))
    if status == "positive_grounded":
        rationale = "positive assessment is grounded in linked evidence."
    elif status == "negative_grounded":
        rationale = "negative assessment is grounded in linked evidence or grounded flaw records."
    elif status == "mixed_grounded":
        rationale = "both positive and negative grounded signals are present; treat this dimension as mixed rather than decisive."
    else:
        rationale = "not assessable from the current grounded state; do not treat missing evidence as a paper weakness."
    evidence_text = ", ".join(evidence_ids) if evidence_ids else "none"
    flaw_text = ", ".join(flaw_ids) if flaw_ids else "none"
    section_text = ", ".join(sections) if sections else "none"
    return f"- **{title}**: `{status}`. Evidence: {evidence_text}. Flaws: {flaw_text}. Sections: {section_text}. Rationale: {rationale}"


def render_section(row: Dict[str, Any]) -> str:
    lines = ["4. Criterion Assessment (Grounded View)", ""]
    for key, title in CRITERIA:
        lines.append(render_criterion_line(key, title, row))
    lines.append("")
    lines.append("Note: This section is rendered from state-grounded criterion links. Not-assessable dimensions are not used as weaknesses or final-decision evidence.")
    return "\n".join(lines)


def strip_old_grounded_section(report: str) -> str:
    marker = "4. Criterion Assessment (Grounded View)"
    idx = report.find(marker)
    if idx >= 0:
        return report[:idx].rstrip()
    return report.rstrip()


def build_outputs(input_rows: List[Dict[str, Any]], linker_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    by_id = {row.get("paper_id"): row for row in linker_rows}
    out = []
    for original in input_rows:
        paper_id = original.get("paper_id")
        link = by_id.get(paper_id, {})
        section = render_section(link)
        original_report = str(original.get("final_report") or (original.get("review_state") or {}).get("final_report") or "")
        rendered = strip_old_grounded_section(original_report) + "\n\n" + section
        out.append({
            "paper_id": paper_id,
            "gold_decision": link.get("gold_decision"),
            "pred_decision": link.get("pred_decision"),
            "criterion_grounded_section_v2": section,
            "final_report_v2": rendered,
            "criterion_statuses": {key: status_for_link((link.get("criterion_links") or {}).get(key, {})) for key, _ in CRITERIA},
            "criterion_positive_grounded_count": link.get("criterion_positive_grounded_count", 0),
            "criterion_negative_grounded_count": link.get("criterion_negative_grounded_count", 0),
            "criterion_not_assessable_count": link.get("criterion_not_assessable_count", 0),
        })
    return out


def write_jsonl(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n", encoding="utf-8")


def write_docs(rows: List[Dict[str, Any]], outdir: Path, input_path: Path, linker_path: Path) -> None:
    outdir.mkdir(parents=True, exist_ok=True)
    status_counts: Dict[str, Dict[str, int]] = {key: {} for key, _ in CRITERIA}
    for row in rows:
        for key, _ in CRITERIA:
            status = row["criterion_statuses"].get(key, "not_assessable")
            status_counts[key][status] = status_counts[key].get(status, 0) + 1
    protocol = """# Criterion-Grounded Report Section v2 Protocol\n\n本轮是离线 report rendering，不改 runtime、不改 final decision、不重跑模型。\n\n## 目标\n\n使用 `Criterion Grounding Linker v1` 的 state-grounded evidence/flaw 绑定结果，重渲染 final report 中的 criterion section。\n\n## 规则\n\n- 有正向 linked evidence 的维度写为 `positive_grounded`。\n- 有 linked flaw / negative evidence 的维度写为 `negative_grounded`。\n- 正负都有时写为 `mixed_grounded`。\n- 没有 state grounding 的维度写为 `not_assessable`，并明确不能作为 paper weakness。\n\n## 边界\n\n本轮只改善报告可读性和 grounding 可诊断性，不改变 accept/reject。\n"""
    (outdir / "CRITERION_GROUNDED_REPORT_SECTION_V2_PROTOCOL.md").write_text(protocol, encoding="utf-8")
    summary_rows = []
    for key, title in CRITERIA:
        counts = status_counts[key]
        summary_rows.append([title, counts.get("positive_grounded", 0), counts.get("negative_grounded", 0), counts.get("mixed_grounded", 0), counts.get("not_assessable", 0)])
    audit = "# Criterion-Grounded Report Section v2 Audit\n\n" + f"Input: `{input_path}`\nLinker: `{linker_path}`\nRows: `{len(rows)}`\n\n" + md_table(["criterion", "positive_grounded", "negative_grounded", "mixed_grounded", "not_assessable"], summary_rows)
    (outdir / "CRITERION_GROUNDED_REPORT_SECTION_V2_AUDIT.md").write_text(audit, encoding="utf-8")
    preview_rows = []
    for row in rows[:8]:
        preview_rows.append([row["paper_id"], row["gold_decision"], row["pred_decision"], ", ".join(f"{k}:{v}" for k, v in row["criterion_statuses"].items())])
    (outdir / "CRITERION_GROUNDED_REPORT_SECTION_V2_PREVIEW.md").write_text(
        "# Criterion-Grounded Report Section v2 Preview\n\n" + md_table(["paper_id", "gold", "pred", "criterion_statuses"], preview_rows), encoding="utf-8")
    decision = """# Criterion-Grounded Report Section v2 Decision\n\n## 当前结论\n\n本轮可以保留为离线 report-layer 改进。它没有修改 final decision，但让 criterion section 从纯文本/关键词式维度描述，变成了 evidence/flaw-linked 的 grounded view。\n\n## 价值\n\n1. 论文中可以展示 novelty / significance / soundness / empirical / clarity 五个审稿维度。\n2. 每个维度明确区分 `positive_grounded`、`negative_grounded`、`mixed_grounded` 和 `not_assessable`。\n3. 无 grounding 的维度不会被写成论文 weakness，降低 meta/excerpt limitation 误写风险。\n\n## 限制\n\n1. 这仍是离线渲染，不代表模型推理本身更强。\n2. criterion grounding 仍依赖现有 evidence/flaw 质量；如果 evidence formation 不足，criterion section 会大量 not_assessable。\n3. 不允许把本轮输出接入 accept/reject。\n\n## 下一步建议\n\n如果继续推进主线，应回到 evidence/support quality：提升 non-abstract、empirical、independent support formation。criterion report v2 作为论文展示层保留，不再继续叠 decision rule。\n"""
    (outdir / "CRITERION_GROUNDED_REPORT_SECTION_V2_DECISION.md").write_text(decision, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=Path("outputs/results_main/review_infer/decision_hygiene_view_v1_fulltest39_4b.jsonl"))
    parser.add_argument("--linker", type=Path, default=Path("outputs/results_main/review_infer/criterion_grounding_linker_v1.json"))
    parser.add_argument("--jsonl-out", type=Path, default=Path("outputs/results_main/review_infer/criterion_grounded_report_section_v2_fulltest39.jsonl"))
    parser.add_argument("--outdir", type=Path, default=Path("docs/experiments/mainline_current"))
    args = parser.parse_args()
    input_rows = load_jsonl(args.input)
    linker_payload = json.loads(args.linker.read_text(encoding="utf-8"))
    linker_rows = linker_payload.get("rows", [])
    rows = build_outputs(input_rows, linker_rows)
    write_jsonl(args.jsonl_out, rows)
    write_docs(rows, args.outdir, args.input, args.linker)
    print(json.dumps({"rows": len(rows), "jsonl_out": str(args.jsonl_out)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
