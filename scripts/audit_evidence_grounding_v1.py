#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List

SUPPORT_STANCES = {"supports", "partially_supports"}


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def norm(value: Any) -> str:
    return str(value or "").strip()


def is_real_claim(claim_id: Any) -> bool:
    cid = norm(claim_id).lower()
    return bool(cid) and "fallback" not in cid and "context" not in cid and "marker" not in cid


def bool_span(ev: Dict[str, Any]) -> bool:
    try:
        start = int(ev.get("source_span_start", -1))
        end = int(ev.get("source_span_end", -1))
    except Exception:
        return False
    return start >= 0 and end >= start


def pick_examples(rows: List[Dict[str, Any]], limit: int = 8) -> Dict[str, List[Dict[str, Any]]]:
    missing_quote: List[Dict[str, Any]] = []
    missing_locator: List[Dict[str, Any]] = []
    paper_grounded: List[Dict[str, Any]] = []
    self_claimed: List[Dict[str, Any]] = []
    for row in rows:
        pid = row.get("paper_id")
        for ev in (row.get("review_state") or {}).get("evidence_map", []) or []:
            stance = norm(ev.get("stance")).lower()
            strength = norm(ev.get("strength")).lower()
            if strength != "strong" or stance not in SUPPORT_STANCES:
                continue
            item = {
                "paper_id": pid,
                "evidence_id": norm(ev.get("evidence_id")),
                "claim_id": norm(ev.get("claim_id")),
                "source_locator": norm(ev.get("source_locator")),
                "raw_quote": norm(ev.get("raw_quote")),
                "grounded_judge_label": norm(ev.get("grounded_judge_label")),
                "evidence": norm(ev.get("evidence"))[:140],
            }
            if not item["raw_quote"] and len(missing_quote) < limit:
                missing_quote.append(item)
            if not item["source_locator"] and len(missing_locator) < limit:
                missing_locator.append(item)
            if item["grounded_judge_label"] == "paper_grounded" and len(paper_grounded) < limit:
                paper_grounded.append(item)
            if item["grounded_judge_label"] == "self_claimed_by_agent" and len(self_claimed) < limit:
                self_claimed.append(item)
    return {
        "missing_quote_examples": missing_quote,
        "missing_locator_examples": missing_locator,
        "paper_grounded_examples": paper_grounded,
        "self_claimed_examples": self_claimed,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="claim_coverage_full39_20260511_qwen35_merged.jsonl")
    parser.add_argument("--output-json", default="EVIDENCE_GROUNDING_AUDIT_V1_FULL39.json")
    parser.add_argument("--output-md", default="EVIDENCE_GROUNDING_AUDIT_V1_FULL39.md")
    args = parser.parse_args()

    rows = load_jsonl(Path(args.input))
    c = Counter()
    per_paper: List[Dict[str, Any]] = []
    judge_dist_all = Counter()
    judge_dist_strong = Counter()
    judge_dist_real_strong = Counter()

    for row in rows:
        state = row.get("review_state") or {}
        paper = {
            "paper_id": row.get("paper_id"),
            "evidence_total": 0,
            "strong_support_total": 0,
            "real_strong_support_total": 0,
            "with_source_locator": 0,
            "with_raw_quote": 0,
            "with_quote_and_locator": 0,
            "with_span": 0,
            "paper_grounded_strong": 0,
            "self_claimed_strong": 0,
            "unclear_or_unjudged_strong": 0,
        }
        for ev in state.get("evidence_map", []) or []:
            paper["evidence_total"] += 1
            c["evidence_total"] += 1
            label = norm(ev.get("grounded_judge_label")) or "missing_label"
            judge_dist_all[label] += 1
            stance = norm(ev.get("stance")).lower()
            strength = norm(ev.get("strength")).lower()
            if strength == "strong" and stance in SUPPORT_STANCES:
                paper["strong_support_total"] += 1
                c["strong_support_total"] += 1
                judge_dist_strong[label] += 1
                if is_real_claim(ev.get("claim_id")):
                    paper["real_strong_support_total"] += 1
                    c["real_strong_support_total"] += 1
                    judge_dist_real_strong[label] += 1
                locator = norm(ev.get("source_locator"))
                quote = norm(ev.get("raw_quote"))
                if locator:
                    paper["with_source_locator"] += 1
                    c["with_source_locator"] += 1
                if quote:
                    paper["with_raw_quote"] += 1
                    c["with_raw_quote"] += 1
                if locator and quote:
                    paper["with_quote_and_locator"] += 1
                    c["with_quote_and_locator"] += 1
                if bool_span(ev):
                    paper["with_span"] += 1
                    c["with_span"] += 1
                if label == "paper_grounded":
                    paper["paper_grounded_strong"] += 1
                    c["paper_grounded_strong"] += 1
                elif label == "self_claimed_by_agent":
                    paper["self_claimed_strong"] += 1
                    c["self_claimed_strong"] += 1
                else:
                    paper["unclear_or_unjudged_strong"] += 1
                    c["unclear_or_unjudged_strong"] += 1
        per_paper.append(paper)

    denom = max(c["strong_support_total"], 1)
    real_denom = max(c["real_strong_support_total"], 1)
    examples = pick_examples(rows)
    summary = {
        "input": args.input,
        "paper_count": len(rows),
        "evidence_total": c["evidence_total"],
        "strong_support_total": c["strong_support_total"],
        "real_strong_support_total": c["real_strong_support_total"],
        "strong_with_source_locator": c["with_source_locator"],
        "strong_with_raw_quote": c["with_raw_quote"],
        "strong_with_quote_and_locator": c["with_quote_and_locator"],
        "strong_with_span": c["with_span"],
        "strong_source_locator_rate": c["with_source_locator"] / denom,
        "strong_raw_quote_rate": c["with_raw_quote"] / denom,
        "strong_quote_and_locator_rate": c["with_quote_and_locator"] / denom,
        "strong_span_rate": c["with_span"] / denom,
        "paper_grounded_strong": c["paper_grounded_strong"],
        "self_claimed_strong": c["self_claimed_strong"],
        "unclear_or_unjudged_strong": c["unclear_or_unjudged_strong"],
        "paper_grounded_strong_rate": c["paper_grounded_strong"] / denom,
        "paper_grounded_real_strong_rate": judge_dist_real_strong.get("paper_grounded", 0) / real_denom,
        "judge_label_distribution_all": dict(judge_dist_all),
        "judge_label_distribution_strong": dict(judge_dist_strong),
        "judge_label_distribution_real_strong": dict(judge_dist_real_strong),
        "examples": examples,
        "per_paper": per_paper,
    }
    Path(args.output_json).write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    md = []
    md.append("# Evidence Grounding Audit v1 (Full39)\n")
    md.append(f"- 输入文件: `{args.input}`")
    md.append(f"- 论文数: {len(rows)}")
    md.append(f"- evidence 总数: {c['evidence_total']}")
    md.append(f"- strong support 总数: {c['strong_support_total']}")
    md.append(f"- real strong support 总数: {c['real_strong_support_total']}\n")
    md.append("## 核心闭环指标")
    md.append(f"- strong evidence 带 `source_locator`: {c['with_source_locator']} ({c['with_source_locator']/denom:.1%})")
    md.append(f"- strong evidence 带 `raw_quote`: {c['with_raw_quote']} ({c['with_raw_quote']/denom:.1%})")
    md.append(f"- strong evidence 同时带 quote+locator: {c['with_quote_and_locator']} ({c['with_quote_and_locator']/denom:.1%})")
    md.append(f"- strong evidence 带 span: {c['with_span']} ({c['with_span']/denom:.1%})")
    md.append(f"- strong evidence 标为 `paper_grounded`: {c['paper_grounded_strong']} ({c['paper_grounded_strong']/denom:.1%})")
    md.append(f"- strong evidence 标为 `self_claimed_by_agent`: {c['self_claimed_strong']} ({c['self_claimed_strong']/denom:.1%})")
    md.append(f"- real strong evidence 的 `paper_grounded` 比例: {judge_dist_real_strong.get('paper_grounded', 0) / real_denom:.1%}\n")
    md.append("## 判断")
    if c['with_quote_and_locator'] == 0:
        md.append("- 当前 full39 结果基本还没有完成真正的 quote/locator 闭环；这说明现有产物大概率早于本轮 grounding schema 改动，或者 Evidence Agent 还未稳定填写这些字段。")
    elif c['paper_grounded_strong'] == 0:
        md.append("- 字段开始出现，但 `paper_grounded` judgment 仍未真正进入 strong evidence 主路径；目前仍更接近 agent self-claimed grounding。")
    else:
        md.append("- strong evidence 已经开始进入 quote/locator/judge 闭环，但仍需要抽样核查质量，不能直接当成人工验证结果。")
    md.append("- 这份审计回答的是“字段是否闭环”，不是“judge 是否正确”；judge 质量还需要单独抽样复核。\n")
    md.append("## judge label 分布（strong support）")
    for k, v in judge_dist_strong.most_common():
        md.append(f"- `{k}`: {v}")
    md.append("\n## 缺失示例（strong support）")
    for key in ["missing_quote_examples", "missing_locator_examples"]:
        md.append(f"### {key}")
        items = examples[key]
        if not items:
            md.append("- 无")
        else:
            for item in items:
                md.append(f"- `{item['paper_id']}` / `{item['evidence_id']}` / claim=`{item['claim_id']}` / locator=`{item['source_locator']}` / quote=`{item['raw_quote']}` / label=`{item['grounded_judge_label']}`")
    Path(args.output_md).write_text("\n".join(md) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
