#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Tuple

POSITIVE_STANCES = {"supports", "support", "partially_supports", "partial_support"}
NEGATIVE_STANCES = {"contradicts", "contradict", "refutes", "missing"}
REAL_CLAIM_PREFIX_BLOCKLIST = ("claim-fallback", "claim-general")

SECTION_PATTERNS = [
    ("ablation", re.compile(r"\bablation\b|ablat", re.I)),
    ("table_or_figure", re.compile(r"\b(table|figure|fig\.?|appendix table)\b", re.I)),
    ("result", re.compile(r"\b(result|evaluation|experiment|benchmark|baseline|outperform|accuracy|f1|auc|bleu|rouge|performance|metric|dataset)\b", re.I)),
    ("method", re.compile(r"\b(method|approach|model|framework|algorithm|architecture|training objective|loss function|inference|design|variational|mechanism)\b", re.I)),
    ("abstract", re.compile(r"\babstract\b|\btitle\b", re.I)),
    ("conclusion", re.compile(r"\bconclusion\b|\bdiscussion\b", re.I)),
]

CRITERIA = {
    "novelty": {
        "label": "novelty_originality",
        "sections": {"abstract", "method", "result", "ablation", "table_or_figure"},
        "positive": re.compile(r"\b(novel|novelty|original|new contribution|propose|introduce|first to|distinct|advance)\b", re.I),
        "negative": re.compile(r"\b(lack(?:s|ing)? novelty|not novel|incremental|limited novelty|insufficient novelty)\b", re.I),
    },
    "significance": {
        "label": "significance_contribution",
        "sections": {"abstract", "result", "ablation", "table_or_figure"},
        "positive": re.compile(r"\b(significant|important|impact|useful|meaningful|contribution|improve|outperform)\b", re.I),
        "negative": re.compile(r"\b(limited significance|minor contribution|unclear impact|limited impact|weak contribution)\b", re.I),
    },
    "soundness": {
        "label": "technical_soundness",
        "sections": {"method", "result", "ablation", "table_or_figure"},
        "positive": re.compile(r"\b(sound|valid|well[- ]?motivated|method|algorithm|objective|inference|framework|design|mechanism)\b", re.I),
        "negative": re.compile(r"\b(unsound|invalid|flaw(?:ed)? method|methodological flaw|unsupported assumption|weak theory|incorrect|unverifiable)\b", re.I),
    },
    "empirical": {
        "label": "empirical_adequacy",
        "sections": {"result", "ablation", "table_or_figure"},
        "positive": re.compile(r"\b(strong result|outperform|improve|baseline|ablation|empirical evidence|evaluation|experiment|dataset|metric|performance)\b", re.I),
        "negative": re.compile(r"\b(insufficient experiment|weak evaluation|missing baseline|no ablation|limited empirical|inadequate experiment|no evidence)\b", re.I),
    },
    "clarity": {
        "label": "clarity_reproducibility",
        "sections": {"method", "result", "table_or_figure", "abstract"},
        "positive": re.compile(r"\b(clear|well[- ]?presented|readable|reproducible|detailed|implementation|description)\b", re.I),
        "negative": re.compile(r"\b(unclear|not clear|lacks detail|insufficient detail|hard to reproduce|not reproducible|poorly written)\b", re.I),
    },
}

COVERAGE_RE = {k: re.compile(v["positive"].pattern + "|" + v["negative"].pattern, re.I) for k, v in CRITERIA.items()}
META_RE = re.compile(r"\b(excerpt|truncated|not available|cannot verify|could not verify|fallback|recovery failure|system|agent|raw output|parse|complete text|insufficient context)\b", re.I)
NOT_ASSESSABLE_RE = re.compile(r"\b(not assessable|cannot assess|insufficient information|not enough information|needs more context|cannot determine|truncated)\b", re.I)
ACCEPT_REJECT = {"accept", "reject"}


def norm(value: Any) -> str:
    return str(value or "").strip().lower()


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def pred_decision(row: Dict[str, Any]) -> str:
    value = norm(row.get("final_decision") or (row.get("review_state") or {}).get("final_decision"))
    return value if value in ACCEPT_REJECT else "undecided"


def infer_gold(row: Dict[str, Any]) -> str:
    explicit = norm(row.get("gold_decision") or row.get("ground_truth_decision") or row.get("label"))
    if explicit in ACCEPT_REJECT:
        return explicit
    pred = pred_decision(row)
    try:
        correct = float(row.get("accept_reject_correct", row.get("decision_correct")))
    except (TypeError, ValueError):
        return "unknown"
    if pred not in ACCEPT_REJECT:
        return "unknown"
    return pred if correct >= 0.5 else ("reject" if pred == "accept" else "accept")


def is_real_claim_id(claim_id: Any) -> bool:
    cid = norm(claim_id)
    return bool(cid) and not cid.startswith(REAL_CLAIM_PREFIX_BLOCKLIST)


def evidence_text(ev: Dict[str, Any]) -> str:
    return " ".join(str(ev.get(k) or "") for k in ("source", "evidence", "support_quality_reason", "binding_rationale", "rationale"))


def evidence_section(ev: Dict[str, Any]) -> str:
    bucket = norm(ev.get("support_source_bucket"))
    mapping = {
        "result_or_experiment": "result",
        "method_or_approach": "method",
        "method_or_design": "method",
        "conclusion_or_discussion": "conclusion",
        "abstract": "abstract",
    }
    if bucket in mapping:
        return mapping[bucket]
    text = evidence_text(ev)
    for section, pattern in SECTION_PATTERNS:
        if pattern.search(text):
            return section
    source = norm(ev.get("source"))
    if source in {"abstract", "method", "result", "ablation", "table_or_figure", "conclusion"}:
        return source
    return "unknown"


def evidence_is_positive(ev: Dict[str, Any]) -> bool:
    return norm(ev.get("stance")) in POSITIVE_STANCES and norm(ev.get("strength")) in {"strong", "moderate"}


def evidence_is_strong_positive(ev: Dict[str, Any]) -> bool:
    return norm(ev.get("stance")) in POSITIVE_STANCES and norm(ev.get("strength")) == "strong"


def evidence_is_negative(ev: Dict[str, Any]) -> bool:
    return norm(ev.get("stance")) in NEGATIVE_STANCES or norm(ev.get("strength")) == "missing"


def link_evidence_to_criteria(ev: Dict[str, Any]) -> List[Tuple[str, str]]:
    section = evidence_section(ev)
    text = evidence_text(ev)
    links: List[Tuple[str, str]] = []
    for key, cfg in CRITERIA.items():
        if section not in cfg["sections"] and not cfg["positive"].search(text) and not cfg["negative"].search(text):
            continue
        if evidence_is_positive(ev) and (section in cfg["sections"] or cfg["positive"].search(text)):
            links.append((key, "positive"))
        elif evidence_is_negative(ev) and cfg["negative"].search(text):
            links.append((key, "negative"))
    return links


def link_flaw_to_criteria(flaw: Dict[str, Any]) -> List[str]:
    text = " ".join(str(flaw.get(k) or "") for k in ("title", "description", "source", "reason", "status", "severity"))
    out = []
    for key, cfg in CRITERIA.items():
        if cfg["negative"].search(text) or COVERAGE_RE[key].search(text):
            out.append(key)
    if not out:
        # Coarse fallback for common flaw wording.
        if re.search(r"experiment|baseline|ablation|dataset|metric|evaluation|result", text, re.I):
            out.append("empirical")
        if re.search(r"method|algorithm|assumption|theory|objective|valid|mechanism", text, re.I):
            out.append("soundness")
        if re.search(r"detail|clear|reproduc|implementation", text, re.I):
            out.append("clarity")
        if re.search(r"novel|contribution|incremental", text, re.I):
            out.append("novelty")
        if re.search(r"impact|significance|importance|meaningful", text, re.I):
            out.append("significance")
    return sorted(set(out))


def report_text(row: Dict[str, Any]) -> str:
    state = row.get("review_state") or {}
    return str(row.get("final_report") or state.get("final_report") or "")


def criterion_sentences(report: str, key: str) -> List[str]:
    pattern = COVERAGE_RE[key]
    parts = re.split(r"(?<=[.!?])\s+|\n+", report)
    return [part.strip() for part in parts if part.strip() and pattern.search(part)]


def derive_row(row: Dict[str, Any]) -> Dict[str, Any]:
    state = row.get("review_state") or {}
    report = report_text(row)
    evidence = [ev for ev in state.get("evidence_map", []) or [] if isinstance(ev, dict)]
    flaws = [flaw for flaw in state.get("flaw_candidates", []) or [] if isinstance(flaw, dict)]
    result: Dict[str, Any] = {
        "paper_id": row.get("paper_id"),
        "gold_decision": infer_gold(row),
        "pred_decision": pred_decision(row),
        "criterion_links": {},
        "covered_criteria": [],
        "state_grounded_criteria": [],
        "positive_grounded_criteria": [],
        "negative_grounded_criteria": [],
        "not_assessable_criteria": [],
        "report_only_criteria": [],
        "meta_leakage_criteria": [],
    }
    real_strong = 0
    real_nonabs = 0
    for ev in evidence:
        if evidence_is_strong_positive(ev) and is_real_claim_id(ev.get("claim_id")):
            real_strong += 1
            if evidence_section(ev) != "abstract":
                real_nonabs += 1
        if not is_real_claim_id(ev.get("claim_id")):
            continue
        for criterion, polarity in link_evidence_to_criteria(ev):
            entry = result["criterion_links"].setdefault(criterion, {"positive_evidence_ids": [], "negative_evidence_ids": [], "flaw_ids": [], "sections": []})
            if polarity == "positive":
                entry["positive_evidence_ids"].append(ev.get("evidence_id") or "")
            else:
                entry["negative_evidence_ids"].append(ev.get("evidence_id") or "")
            entry["sections"].append(evidence_section(ev))
    for flaw in flaws:
        grounded = bool(flaw.get("evidence_ids") or flaw.get("supporting_evidence_ids") or flaw.get("evidence_id"))
        severity = norm(flaw.get("severity"))
        status = norm(flaw.get("status")) or "candidate"
        if not grounded and not (severity in {"major", "critical"} and status == "confirmed"):
            continue
        for criterion in link_flaw_to_criteria(flaw):
            entry = result["criterion_links"].setdefault(criterion, {"positive_evidence_ids": [], "negative_evidence_ids": [], "flaw_ids": [], "sections": []})
            entry["flaw_ids"].append(flaw.get("flaw_id") or "")
    for key, cfg in CRITERIA.items():
        label = cfg["label"]
        local_sentences = criterion_sentences(report, key)
        covered = bool(local_sentences)
        local_text = " ".join(local_sentences)
        links = result["criterion_links"].get(key, {})
        has_pos = bool(links.get("positive_evidence_ids"))
        has_neg = bool(links.get("negative_evidence_ids") or links.get("flaw_ids"))
        grounded = has_pos or has_neg
        not_assessable = covered and bool(NOT_ASSESSABLE_RE.search(local_text))
        meta = covered and bool(META_RE.search(local_text))
        result[f"criterion_covered_{key}"] = covered
        result[f"criterion_state_grounded_{key}"] = grounded
        result[f"criterion_positive_grounded_{key}"] = has_pos
        result[f"criterion_negative_grounded_{key}"] = has_neg
        result[f"criterion_not_assessable_{key}"] = not_assessable
        result[f"criterion_report_only_{key}"] = covered and not grounded and not not_assessable
        result[f"criterion_meta_leakage_{key}"] = meta
        if covered:
            result["covered_criteria"].append(label)
        if grounded:
            result["state_grounded_criteria"].append(label)
        if has_pos:
            result["positive_grounded_criteria"].append(label)
        if has_neg:
            result["negative_grounded_criteria"].append(label)
        if not_assessable:
            result["not_assessable_criteria"].append(label)
        if covered and not grounded and not not_assessable:
            result["report_only_criteria"].append(label)
        if meta:
            result["meta_leakage_criteria"].append(label)
    result["real_strong_support_total"] = real_strong
    result["non_abstract_strong_support_total"] = real_nonabs
    result["criterion_state_grounded_count"] = len(result["state_grounded_criteria"])
    result["criterion_positive_grounded_count"] = len(result["positive_grounded_criteria"])
    result["criterion_negative_grounded_count"] = len(result["negative_grounded_criteria"])
    result["criterion_report_only_count"] = len(result["report_only_criteria"])
    result["criterion_not_assessable_count"] = len(result["not_assessable_criteria"])
    return result


def md_table(headers: Sequence[str], rows: Sequence[Sequence[Any]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(x).replace("\n", " ") for x in row) + " |")
    return "\n".join(lines) + "\n"


def rate(num: int, den: int) -> float:
    return round(num / den, 4) if den else 0.0


def write_outputs(rows: List[Dict[str, Any]], outdir: Path, json_out: Path, input_path: Path) -> None:
    outdir.mkdir(parents=True, exist_ok=True)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps({"input": str(input_path), "rows": rows}, ensure_ascii=False, indent=2), encoding="utf-8")
    n = len(rows)
    agg_rows = []
    for key, cfg in CRITERIA.items():
        label = cfg["label"]
        covered = sum(int(r[f"criterion_covered_{key}"]) for r in rows)
        grounded = sum(int(r[f"criterion_state_grounded_{key}"]) for r in rows)
        pos = sum(int(r[f"criterion_positive_grounded_{key}"]) for r in rows)
        neg = sum(int(r[f"criterion_negative_grounded_{key}"]) for r in rows)
        na = sum(int(r[f"criterion_not_assessable_{key}"]) for r in rows)
        report_only = sum(int(r[f"criterion_report_only_{key}"]) for r in rows)
        meta = sum(int(r[f"criterion_meta_leakage_{key}"]) for r in rows)
        agg_rows.append([label, covered, rate(covered, n), grounded, rate(grounded, n), pos, neg, na, report_only, meta])
    schema = """# Criterion Grounding Linker v1 Schema\n\n本轮是离线 grounding linker，不改 runtime、不改 final decision、不重跑模型。\n\n## 目的\n\n上一轮 criterion-grounded decision simulation 说明：criterion 信号现在不能安全接入 accept/reject。v1 linker 的目标不是决策，而是把 criterion 维度和已有 `ReviewState` 中的 evidence / flaw 建立可追踪关系，区分：\n\n- report text 提到了某维度；\n- 该维度是否能从 state evidence / grounded flaw 得到支撑；\n- 该维度是 positive grounding、negative grounding、not-assessable，还是 report-only；\n- 是否存在 meta leakage。\n\n## 五个维度\n\n- novelty_originality\n- significance_contribution\n- technical_soundness\n- empirical_adequacy\n- clarity_reproducibility\n\n## 关键字段\n\n- `criterion_state_grounded_*`: 该维度至少有真实 claim evidence 或 grounded flaw 绑定。\n- `criterion_positive_grounded_*`: 该维度有正向 evidence 绑定。\n- `criterion_negative_grounded_*`: 该维度有负向 evidence 或 grounded flaw 绑定。\n- `criterion_report_only_*`: final report 提到该维度，但 state 中没有找到 grounding。\n- `criterion_not_assessable_*`: 该维度缺少 grounding，应当报告为无法评估，而不是论文缺陷。\n\n## 约束\n\n该 linker 只用于审计和后续 report section 改进，不允许直接驱动 final decision。\n"""
    (outdir / "CRITERION_GROUNDING_LINKER_V1_SCHEMA.md").write_text(schema, encoding="utf-8")
    audit = "# Criterion Grounding Linker v1 Audit\n\n" + f"Input: `{input_path}`\nRows: `{n}`\n\n" + md_table([
        "criterion", "covered", "coverage_rate", "state_grounded", "grounded_rate", "positive_grounded", "negative_grounded", "not_assessable", "report_only", "meta_leakage"
    ], agg_rows)
    total_covered = sum(len(r["covered_criteria"]) for r in rows)
    total_grounded = sum(len(r["state_grounded_criteria"]) for r in rows)
    total_report_only = sum(len(r["report_only_criteria"]) for r in rows)
    audit += f"\n## 汇总\n\n- avg covered criteria/report: `{round(total_covered / n, 3) if n else 0}`\n- avg state-grounded criteria/report: `{round(total_grounded / n, 3) if n else 0}`\n- report-only criterion mentions: `{total_report_only}`\n"
    (outdir / "CRITERION_GROUNDING_LINKER_V1_AUDIT.md").write_text(audit, encoding="utf-8")
    case_rows = []
    for r in rows:
        case_rows.append([
            r["paper_id"], r["gold_decision"], r["pred_decision"], r["real_strong_support_total"], r["non_abstract_strong_support_total"],
            ",".join(r["covered_criteria"]), ",".join(r["state_grounded_criteria"]), ",".join(r["positive_grounded_criteria"]),
            ",".join(r["negative_grounded_criteria"]), ",".join(r["not_assessable_criteria"]), ",".join(r["report_only_criteria"]), ",".join(r["meta_leakage_criteria"]),
        ])
    (outdir / "CRITERION_GROUNDING_LINKER_V1_CASE_TABLE.md").write_text(
        "# Criterion Grounding Linker v1 Case Table\n\n" + md_table([
            "paper_id", "gold", "pred", "real_strong", "non_abs_strong", "covered", "state_grounded", "positive_grounded", "negative_grounded", "not_assessable", "report_only", "meta_leakage"
        ], case_rows), encoding="utf-8")
    # Decision text in Chinese.
    positives = sum(r["criterion_positive_grounded_count"] for r in rows)
    negatives = sum(r["criterion_negative_grounded_count"] for r in rows)
    report_only = sum(r["criterion_report_only_count"] for r in rows)
    not_assess = sum(r["criterion_not_assessable_count"] for r in rows)
    decision = f"""# Criterion Grounding Linker v1 Decision\n\n## 当前结论\n\n本轮 linker 支持继续把 criterion 放在报告与审计层，而不是接入 final decision。它能把 final report 的维度提及和 `ReviewState` 中的 evidence / flaw grounding 对齐，但也显示当前 criterion grounding 仍不够稳定，尤其不能把 positive criterion 作为 accept-like 信号。\n\n## 核心统计\n\n- rows: `{n}`\n- positive grounded criterion links: `{positives}`\n- negative grounded criterion links: `{negatives}`\n- report-only criterion mentions: `{report_only}`\n- not-assessable criterion labels: `{not_assess}`\n\n## 解释\n\n1. criterion 维度可以提升论文报告的“审稿维度饱满度”，也能帮助识别 novelty / significance / soundness / empirical / clarity 是否有证据支撑。\n2. 但是当前 grounding 多数仍依赖已有 evidence/flaw 的粗粒度匹配，不能证明 paper-level accept。\n3. 因此不要把 criterion linker 输出接入 accept/reject，也不要写 `positive criterion -> accept` 规则。\n4. 下一步如果继续推进 report 层，应做 `Criterion-Grounded Report Section v2`：用 linker 结果渲染 criterion section，确保无 grounding 的维度写成 not_assessable，而不是 weakness。\n\n## 下一步唯一建议\n\n建议下一步做 **Criterion-Grounded Report Section v2**，仍保持 report-only：\n\n- 用 linker 结果替代纯关键词式 criterion section。\n- 每个 criterion 明确列出 linked evidence / linked flaw / not_assessable reason。\n- 不改 final decision。\n\n## 暂时不要做\n\n- 不要 runtime 化 criterion-grounded decision。\n- 不要继续调 accept/reject 阈值。\n- 不要回到 sticky/throttle/progression gate。\n"""
    (outdir / "CRITERION_GROUNDING_LINKER_V1_DECISION.md").write_text(decision, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=Path("outputs/results_main/review_infer/decision_hygiene_view_v1_fulltest39_4b.jsonl"))
    parser.add_argument("--outdir", type=Path, default=Path("docs/experiments/mainline_current"))
    parser.add_argument("--json-out", type=Path, default=Path("outputs/results_main/review_infer/criterion_grounding_linker_v1.json"))
    args = parser.parse_args()
    rows = [derive_row(row) for row in load_jsonl(args.input)]
    write_outputs(rows, args.outdir, args.json_out, args.input)
    print(json.dumps({"rows": len(rows), "json_out": str(args.json_out)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
