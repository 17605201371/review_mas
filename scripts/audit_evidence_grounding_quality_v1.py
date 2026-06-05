#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Tuple

from agent_system.environments.env_package.review.state import _assess_quote_semantic_grounding


SUPPORT_STANCES = {"supports", "partially_supports"}
GENERIC_SECTION_TERMS = {
    "abstract", "introduction", "method", "methodology", "results", "evaluation", "discussion", "conclusion",
    "section evaluation", "results section", "methodology section", "section methodology", "section results",
}
VERIFIED_GROUNDED_LABELS = {"paper_grounded_exact", "paper_grounded_normalized"}


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def norm_text(value: Any) -> str:
    return str(value or "").strip()


def normalize_for_match(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", text.lower())).strip()


def normalize_with_offsets(text: str) -> Tuple[str, List[int]]:
    chars: List[str] = []
    offsets: List[int] = []
    previous_space = True
    for idx, char in enumerate(text.lower()):
        if char.isalnum():
            chars.append(char)
            offsets.append(idx)
            previous_space = False
        elif not previous_space:
            chars.append(" ")
            offsets.append(idx)
            previous_space = True
    while chars and chars[0] == " ":
        chars.pop(0)
        offsets.pop(0)
    while chars and chars[-1] == " ":
        chars.pop()
        offsets.pop()
    return "".join(chars), offsets


def load_paper_text_map(parquet_path: Path) -> Dict[str, str]:
    import pyarrow.parquet as pq

    table = pq.read_table(parquet_path, columns=["id", "inputs"])
    out: Dict[str, str] = {}
    ids = table.column("id").to_pylist()
    inputs = table.column("inputs").to_pylist()
    for pid, payload in zip(ids, inputs):
        text = ""
        try:
            messages = json.loads(payload)
        except Exception:
            messages = []
        for msg in messages or []:
            if isinstance(msg, dict) and msg.get("role") == "user":
                text = str(msg.get("content") or "")
                break
        if text:
            out[str(pid)] = text
    return out


def verify_quote_grounding(raw_quote: str, paper_text: str) -> Dict[str, Any]:
    quote = norm_text(raw_quote)
    if not quote:
        return {
            "verified_grounding_label": "missing_quote",
            "verified_quote_match_type": "missing_quote",
            "verified_source_span_start": -1,
            "verified_source_span_end": -1,
            "verified_grounding_reason": "raw_quote is empty; no paper-text verification possible",
        }

    exact_start = paper_text.find(quote)
    if exact_start >= 0:
        exact_end = exact_start + len(quote) - 1
        return {
            "verified_grounding_label": "paper_grounded_exact",
            "verified_quote_match_type": "exact_substring",
            "verified_source_span_start": exact_start,
            "verified_source_span_end": exact_end,
            "verified_grounding_reason": "raw_quote exactly matches the paper text",
        }

    normalized_quote, _ = normalize_with_offsets(quote)
    normalized_paper, paper_offsets = normalize_with_offsets(paper_text)
    normalized_start = normalized_paper.find(normalized_quote) if normalized_quote else -1
    if normalized_start >= 0 and paper_offsets:
        normalized_end = normalized_start + len(normalized_quote) - 1
        source_start = paper_offsets[normalized_start]
        source_end = paper_offsets[min(normalized_end, len(paper_offsets) - 1)]
        return {
            "verified_grounding_label": "paper_grounded_normalized",
            "verified_quote_match_type": "normalized_substring",
            "verified_source_span_start": source_start,
            "verified_source_span_end": source_end,
            "verified_grounding_reason": "raw_quote matches the paper text after normalization",
        }

    return {
        "verified_grounding_label": "not_verified_paraphrase_only",
        "verified_quote_match_type": "not_found_in_paper",
        "verified_source_span_start": -1,
        "verified_source_span_end": -1,
        "verified_grounding_reason": "raw_quote was not found in the paper text",
    }


def quote_match_type(raw_quote: str, paper_text: str) -> str:
    return str(verify_quote_grounding(raw_quote, paper_text)["verified_quote_match_type"])


def locator_quality(locator: str) -> str:
    loc = norm_text(locator)
    if not loc:
        return "missing_locator"
    if re.search(r"\b(table|figure|fig\.)\s*\d+", loc, re.I):
        return "specific_table_or_figure"
    if re.search(r"\bsection\s*\d+(?:\.\d+)?", loc, re.I):
        return "specific_section_number"
    if "/" in loc and re.search(r"(section|table|figure|fig\.)", loc, re.I):
        return "multi_anchor_locator"
    if loc.lower() in GENERIC_SECTION_TERMS or re.fullmatch(r"section\s+[a-z]+", loc.lower()):
        return "generic_section_locator"
    if re.search(r"\b(section|results|method|evaluation|discussion|conclusion|appendix)\b", loc, re.I):
        return "generic_section_locator"
    return "weak_or_custom_locator"


def agent_span_quality(ev: Dict[str, Any], paper_text: str, raw_quote: str) -> str:
    try:
        start = int(ev.get("source_span_start", -1))
        end = int(ev.get("source_span_end", -1))
    except Exception:
        return "missing_span"
    if start < 0 or end < start:
        return "missing_span"
    if end >= len(paper_text):
        return "invalid_out_of_bounds"
    span_text = paper_text[start:end + 1]
    if raw_quote and raw_quote in span_text:
        return "quote_inside_span"
    nq = normalize_for_match(raw_quote)
    ns = normalize_for_match(span_text)
    if nq and nq in ns:
        return "normalized_quote_inside_span"
    return "span_present_but_quote_mismatch"


def collect_examples(records: List[Dict[str, Any]], key: str, value: str, limit: int = 6) -> List[Dict[str, Any]]:
    picked = []
    for r in records:
        if r.get(key) == value:
            picked.append({
                "paper_id": r["paper_id"],
                "evidence_id": r["evidence_id"],
                "claim_id": r["claim_id"],
                "source_locator": r["source_locator"],
                "raw_quote": r["raw_quote"],
                "quote_id": r.get("quote_id", ""),
                "evidence": r["evidence"][:180],
                "verified_grounding_label": r["verified_grounding_label"],
                "verified_source_span_start": r["verified_source_span_start"],
                "verified_source_span_end": r["verified_source_span_end"],
            })
            if len(picked) >= limit:
                break
    return picked


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="evidence_grounding_full39_20260512_qwen35.jsonl")
    parser.add_argument("--dataset", default="/reviewF/datasets/drmas_review/test.parquet")
    parser.add_argument("--output-json", default="EVIDENCE_GROUNDING_QUALITY_AUDIT_V1_20260512_FULL39.json")
    parser.add_argument("--output-md", default="EVIDENCE_GROUNDING_QUALITY_AUDIT_V1_20260512_FULL39.md")
    args = parser.parse_args()

    rows = load_jsonl(Path(args.input))
    paper_text_map = load_paper_text_map(Path(args.dataset))
    records: List[Dict[str, Any]] = []
    counters = Counter()

    for row in rows:
        pid = str(row.get("paper_id") or "")
        paper_text = paper_text_map.get(pid, "")
        for ev in (row.get("review_state") or {}).get("evidence_map", []) or []:
            stance = norm_text(ev.get("stance")).lower()
            strength = norm_text(ev.get("strength")).lower()
            if strength != "strong" or stance not in SUPPORT_STANCES:
                continue
            raw_quote = norm_text(ev.get("raw_quote"))
            locator = norm_text(ev.get("source_locator"))
            verification = verify_quote_grounding(raw_quote, paper_text)
            locator_label = locator_quality(locator)
            agent_span_label = agent_span_quality(ev, paper_text, raw_quote)
            agent_label = norm_text(ev.get("grounded_judge_label")) or "missing_label"
            verified_label = verification["verified_grounding_label"]
            rec = {
                "paper_id": pid,
                "evidence_id": norm_text(ev.get("evidence_id")),
                "claim_id": norm_text(ev.get("claim_id")),
                "evidence": norm_text(ev.get("evidence")),
                "raw_quote": raw_quote,
                "quote_id": norm_text(ev.get("quote_id")),
                "source_locator": locator,
                "quote_match_type": verification["verified_quote_match_type"],
                "locator_quality": locator_label,
                "agent_span_quality": agent_span_label,
                "grounded_judge_label": agent_label,
                "verified_grounding_label": verified_label,
                "verified_grounding_reason": verification["verified_grounding_reason"],
                "verified_quote_match_type": verification["verified_quote_match_type"],
                "verified_source_span_start": verification["verified_source_span_start"],
                "verified_source_span_end": verification["verified_source_span_end"],
                "verified_locator_quality": locator_label,
            }
            semantic = _assess_quote_semantic_grounding(row.get("review_state") or {}, {**ev, **verification})
            rec.update(semantic)
            records.append(rec)
            counters["strong_support_total"] += 1
            counters[f"quote::{rec['quote_match_type']}"] += 1
            counters[f"locator::{locator_label}"] += 1
            counters[f"agent_span::{agent_span_label}"] += 1
            counters[f"agent_judge::{agent_label}"] += 1
            counters[f"verified::{verified_label}"] += 1
            if rec["quote_id"]:
                counters["quote_id_usage_count"] += 1
            if rec.get("semantic_grounding_label"):
                counters[f"semantic::{rec['semantic_grounding_label']}"] += 1
            if rec.get("semantic_grounding_label") == "semantic_support_verified":
                counters["semantic_support_verified_total"] += 1
            if rec.get("semantic_grounding_label") == "semantic_mismatch":
                counters["semantic_mismatch_total"] += 1
            if rec.get("semantic_grounding_label") == "semantic_support_weak":
                counters["semantic_support_weak_total"] += 1
            pair = f"{rec['paper_id']}::{rec['claim_id']}::{rec.get('quote_id') or rec['raw_quote'][:80]}"
            counters[f"independent_pair::{pair}"] += 1
            if agent_label == "paper_grounded" and verified_label not in VERIFIED_GROUNDED_LABELS:
                counters["agent_paper_grounded_but_unverified"] += 1
            if verified_label in VERIFIED_GROUNDED_LABELS:
                counters["verified_paper_grounded_total"] += 1
            else:
                counters["verified_not_grounded_total"] += 1

    total = max(counters["strong_support_total"], 1)
    exact = counters["verified::paper_grounded_exact"]
    normalized = counters["verified::paper_grounded_normalized"]
    verified_total = counters["verified_paper_grounded_total"]
    unverified_total = counters["verified_not_grounded_total"]
    not_found = counters["verified::not_verified_paraphrase_only"]
    missing_quote = counters["verified::missing_quote"]
    specific_locator = counters["locator::specific_table_or_figure"] + counters["locator::specific_section_number"] + counters["locator::multi_anchor_locator"]
    generic_locator = counters["locator::generic_section_locator"]
    trusted_span_total = counters["verified_paper_grounded_total"]
    independent_quote_pairs = len([k for k in counters if k.startswith("independent_pair::")])

    summary = {
        "input": args.input,
        "paper_count": len(rows),
        "strong_support_total": counters["strong_support_total"],
        "verified_paper_grounded_total": verified_total,
        "verified_paper_grounded_rate": verified_total / total,
        "verified_not_grounded_total": unverified_total,
        "verified_not_grounded_rate": unverified_total / total,
        "exact_quote_match_rate": exact / total,
        "normalized_quote_match_rate": normalized / total,
        "quote_not_found_rate": not_found / total,
        "missing_quote_rate": missing_quote / total,
        "specific_locator_rate": specific_locator / total,
        "generic_locator_rate": generic_locator / total,
        "trusted_span_generated_total": trusted_span_total,
        "trusted_span_generated_rate": trusted_span_total / total,
        "quote_id_usage_count": counters["quote_id_usage_count"],
        "quote_id_usage_rate": counters["quote_id_usage_count"] / total,
        "agent_paper_grounded_but_unverified": counters["agent_paper_grounded_but_unverified"],
        "semantic_support_verified_total": counters["semantic_support_verified_total"],
        "semantic_support_verified_rate": counters["semantic_support_verified_total"] / total,
        "semantic_mismatch_total": counters["semantic_mismatch_total"],
        "semantic_mismatch_rate": counters["semantic_mismatch_total"] / total,
        "semantic_support_weak_total": counters["semantic_support_weak_total"],
        "semantic_support_weak_rate": counters["semantic_support_weak_total"] / total,
        "independent_claim_quote_pair_total": independent_quote_pairs,
        "independent_claim_quote_pair_rate": independent_quote_pairs / total,
        "semantic_grounding_distribution": {k.split("semantic::", 1)[1]: v for k, v in counters.items() if k.startswith("semantic::")},
        "verified_grounding_distribution": {k.split("verified::", 1)[1]: v for k, v in counters.items() if k.startswith("verified::")},
        "quote_match_distribution": {k.split("quote::", 1)[1]: v for k, v in counters.items() if k.startswith("quote::")},
        "locator_quality_distribution": {k.split("locator::", 1)[1]: v for k, v in counters.items() if k.startswith("locator::")},
        "agent_span_quality_distribution": {k.split("agent_span::", 1)[1]: v for k, v in counters.items() if k.startswith("agent_span::")},
        "agent_judge_distribution": {k.split("agent_judge::", 1)[1]: v for k, v in counters.items() if k.startswith("agent_judge::")},
        "examples": {
            "paper_grounded_exact": collect_examples(records, "verified_grounding_label", "paper_grounded_exact"),
            "paper_grounded_normalized": collect_examples(records, "verified_grounding_label", "paper_grounded_normalized"),
            "not_verified_paraphrase_only": collect_examples(records, "verified_grounding_label", "not_verified_paraphrase_only"),
            "missing_quote": collect_examples(records, "verified_grounding_label", "missing_quote"),
            "specific_locator": [r for r in records if r["locator_quality"] in {"specific_table_or_figure", "specific_section_number", "multi_anchor_locator"}][:6],
            "generic_locator": collect_examples(records, "locator_quality", "generic_section_locator"),
            "agent_span_mismatch": collect_examples(records, "agent_span_quality", "span_present_but_quote_mismatch"),
            "semantic_mismatch": collect_examples(records, "semantic_grounding_label", "semantic_mismatch"),
            "semantic_support_weak": collect_examples(records, "semantic_grounding_label", "semantic_support_weak"),
        },
        "records": records,
    }
    Path(args.output_json).write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    md: List[str] = []
    md.append("# Evidence Grounding Quality Audit v1 (Full39)\n")
    md.append(f"- 输入结果: `{args.input}`")
    md.append(f"- strong support 总数: {counters['strong_support_total']}\n")
    md.append("## 核心质量指标")
    md.append(f"- verified paper-grounded strong evidence: {verified_total} ({verified_total/total:.1%})")
    md.append(f"- verified not-grounded / paraphrase-only strong evidence: {unverified_total} ({unverified_total/total:.1%})")
    md.append(f"- raw_quote 精确命中原文: {exact} ({exact/total:.1%})")
    md.append(f"- raw_quote 归一化后命中原文: {normalized} ({normalized/total:.1%})")
    md.append(f"- raw_quote 在原文中找不到: {not_found} ({not_found/total:.1%})")
    md.append(f"- raw_quote 缺失: {missing_quote} ({missing_quote/total:.1%})")
    md.append(f"- 由 verifier 自动生成可信 span: {trusted_span_total} ({trusted_span_total/total:.1%})")
    md.append(f"- quote_id 使用: {counters['quote_id_usage_count']} ({counters['quote_id_usage_count']/total:.1%})")
    md.append(f"- 具体 locator（表/图/编号 section/多锚点）: {specific_locator} ({specific_locator/total:.1%})")
    md.append(f"- 泛化 locator（Results section / Methodology section 等）: {generic_locator} ({generic_locator/total:.1%})")
    md.append(f"- agent 自称 paper_grounded 但 verifier 未通过: {counters['agent_paper_grounded_but_unverified']}")
    md.append(f"- quote-evidence-claim 语义支撑通过: {counters['semantic_support_verified_total']} ({counters['semantic_support_verified_total']/total:.1%})")
    md.append(f"- quote-evidence-claim 语义弱支撑: {counters['semantic_support_weak_total']} ({counters['semantic_support_weak_total']/total:.1%})")
    md.append(f"- quote-evidence-claim 语义不匹配: {counters['semantic_mismatch_total']} ({counters['semantic_mismatch_total']/total:.1%})")
    md.append(f"- 独立 claim-quote pair: {independent_quote_pairs} ({independent_quote_pairs/total:.1%})\n")
    md.append("## 质量判断")
    md.append("- 本审计不再信任 Evidence Agent 自己写的 `grounded_judge_label` 作为最终真实性标签；最终标签来自 `raw_quote -> paper_text` 的后处理匹配。")
    if unverified_total > 0:
        md.append("- 当前仍有 strong evidence 的 `raw_quote` 无法在论文原文中找到，因此这些证据只能算 `not_verified_paraphrase_only`，不能作为最强 paper-grounded evidence。")
    if verified_total > 0:
        md.append("- exact / normalized 命中的 evidence 已由 verifier 自动生成 `verified_source_span_start/end`，比模型自报 offset 更可信。")
    if generic_locator > specific_locator:
        md.append("- `source_locator` 仍以泛化 section 标签为主，定位精度还不够，离“可审稿复核的证据锚点”还有差距。")
    else:
        md.append("- `source_locator` 已经开始以具体锚点为主，但仍需统一 table/figure locator 与 support bucket 的统计口径。")
    if counters["semantic_mismatch_total"] > 0:
        md.append("- 现在额外检查 quote、evidence statement 与 target claim 的语义一致性；`semantic_mismatch` 说明 quote 存在于论文中，但不足以支撑该 evidence/claim 的具体表述。")
    md.append("\n## 分布")
    md.append("### verified grounding")
    for k, v in summary["verified_grounding_distribution"].items():
        md.append(f"- `{k}`: {v}")
    md.append("### quote match")
    for k, v in summary["quote_match_distribution"].items():
        md.append(f"- `{k}`: {v}")
    md.append("### locator quality")
    for k, v in summary["locator_quality_distribution"].items():
        md.append(f"- `{k}`: {v}")
    md.append("### agent span quality")
    for k, v in summary["agent_span_quality_distribution"].items():
        md.append(f"- `{k}`: {v}")
    md.append("### agent self judge")
    for k, v in summary["agent_judge_distribution"].items():
        md.append(f"- `{k}`: {v}")
    md.append("### semantic grounding")
    for k, v in summary["semantic_grounding_distribution"].items():
        md.append(f"- `{k}`: {v}")
    md.append("\n## 示例")
    for title, items in summary["examples"].items():
        md.append(f"### {title}")
        if not items:
            md.append("- 无")
            continue
        for item in items:
            span = f"{item['verified_source_span_start']}..{item['verified_source_span_end']}"
            quote_id = item.get("quote_id", "")
            quote_id_part = f" / quote_id=`{quote_id}`" if quote_id else ""
            md.append(f"- `{item['paper_id']}` / `{item['evidence_id']}`{quote_id_part} / label=`{item['verified_grounding_label']}` / span=`{span}` / locator=`{item['source_locator']}` / quote=`{item['raw_quote']}`")

    Path(args.output_md).write_text("\n".join(md) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
