#!/usr/bin/env python3
"""Audit whether hard-negative opportunity contexts are visible to the system.

This is an offline P1.0 diagnostic. It does not call any model and does not
change runtime state. The goal is to distinguish two failure modes:

1. The paper/reviewer context contains type-specific hard-negative cues, but
   quote-bank / state context does not surface them.
2. The context is surfaced, but the final ReviewState does not convert it into
   verified negative evidence / concerns.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

import pandas as pd

from agent_system.environments.env_package.review.state import (
    _build_evidence_quote_bank,
    _classify_negative_evidence_type,
    _clean_paper_body,
)


TARGET_TYPES: Dict[str, re.Pattern[str]] = {
    "missing_ablation": re.compile(
        r"\b(no ablation|missing ablation|lacks? (?:an? )?ablation|without (?:an? )?ablation|"
        r"ablation (?:is|was|are|were)?\s*(?:missing|absent|not provided)|"
        r"(?:component|module|mechanism|contribution) (?:analysis|ablation))\b",
        re.I,
    ),
    "missing_baseline": re.compile(
        r"\b(no baseline|missing baseline|without (?:a |the )?(?:strong |recent |sota |state-of-the-art )?baseline|"
        r"not compare(?:d)? (?:to|with|against)|lacks? (?:a |the )?(?:strong |recent |sota |state-of-the-art )?baseline)\b",
        re.I,
    ),
    "unfair_or_weak_baseline": re.compile(
        r"\b(unfair (?:comparison|baseline|evaluation)|weak baselines?|outdated baselines?|"
        r"non[- ]competitive baselines?|baseline(?:s)? (?:is|are|was|were)?\s*(?:weak|outdated|untuned|not tuned|inadequate)|"
        r"different (?:backbone|architecture|training budget|data split|protocol|setting) (?:for|between) (?:the )?(?:baseline|baselines|methods))\b",
        re.I,
    ),
    "insufficient_evaluation": re.compile(
        r"\b(insufficient evaluation|limited evaluation|not evaluated|small-scale evaluation|"
        r"limited (?:datasets?|benchmarks?|tasks?|domains?)|single dataset|only evaluated on|"
        r"insufficient experiments?|no evaluation|does not evaluate|not tested on)\b",
        re.I,
    ),
    "missing_robustness_or_generalization": re.compile(
        r"\b(no (?:robustness|generalization|generalisation|out-of-domain|ood|cross-domain|stress) (?:test|evaluation|experiment)|"
        r"missing (?:robustness|generalization|generalisation|out-of-domain|ood|cross-domain|stress) (?:test|evaluation|experiment)|"
        r"not (?:tested|evaluated|validated) (?:on|under|against) (?:unseen|out-of-domain|ood|cross-domain|external|corrupted|noisy)|"
        r"limited (?:robustness|generalization|generalisation|transferability) evaluation)\b",
        re.I,
    ),
    "evaluation_protocol_risk": re.compile(
        r"\b(train[- ]test leakage|data leakage|test[- ]set leakage|label leakage|"
        r"oracle (?:information|access|features?|labels?)|"
        r"(?:tune|tuned|select|selected) (?:hyperparameters?|models?|checkpoints?) on (?:the )?test set|"
        r"(?:validation|test) split (?:is|was)?\s*(?:not specified|unclear|missing)|"
        r"unfair evaluation protocol|protocol (?:bias|risk|leakage|mismatch)|"
        r"metric (?:mismatch|does not match|is inappropriate|not appropriate)|"
        r"best(?:-| )case (?:selection|reporting)|cherry[- ]pick(?:ed|ing))\b",
        re.I,
    ),
    "efficiency_cost_gap": re.compile(
        r"\b(no (?:runtime|latency|memory|parameter|parameters|flops|compute|computational cost|efficiency) (?:analysis|evaluation|report|measurement|comparison)|"
        r"missing (?:runtime|latency|memory|parameter|parameters|flops|compute|computational cost|efficiency) (?:analysis|evaluation|report|measurement|comparison)|"
        r"(?:runtime|latency|memory|parameters?|flops|compute|computational cost|efficiency)[^.!?]{0,120}(?:not (?:reported|measured|provided|evaluated|compared)|missing|omitted)|"
        r"computationally expensive|requires? substantial compute|requires? large memory)\b",
        re.I,
    ),
    "reproducibility_gap": re.compile(
        r"\b(reproducibility|reproduce|reproducible|implementation detail|hyperparameter|training detail|"
        r"code (?:unavailable|not (?:available|released))|not release(?:d)? code|data split|compute setup)\b",
        re.I,
    ),
    "result_claim_mismatch": re.compile(
        r"\b(results? (?:do|does|did) not support|claim(?:s)? (?:do|does|did) not match|"
        r"mismatch(?:es)? between (?:the )?(?:claim|conclusion) and (?:the )?result|"
        r"reported results? (?:are|is) weaker|mixed results?|inconsistent results?|does not always improve)\b",
        re.I,
    ),
    "negative_result": re.compile(
        r"\b(worse|underperform(?:s|ed)?|lower (?:accuracy|performance|score|f1|auc)|"
        r"no improvement|degrad(?:e|es|ed|ation)|poor performance|no significant|not significant)\b",
        re.I,
    ),
    "scope_overclaim": re.compile(
        r"\b(overclaim|over-claim|overstate(?:s|d)?|too broad|generaliz(?:e|es|ed|ation)|"
        r"only applies|limited to|restricted to|does not generalize|fails? to generalize)\b",
        re.I,
    ),
}


PAPER_SECTION_CUES: Dict[str, re.Pattern[str]] = {
    "ablation_section": re.compile(r"\b(ablation|component analysis|module analysis)\b", re.I),
    "evaluation_section": re.compile(r"\b(experiment|evaluation|benchmark|baseline|dataset|metric|results?)\b", re.I),
    "robustness_section": re.compile(r"\b(robustness|generalization|generalisation|ood|out-of-domain|stress test|cross-domain)\b", re.I),
    "protocol_section": re.compile(r"\b(protocol|data split|train[- ]test|validation|test set|metric)\b", re.I),
    "efficiency_section": re.compile(r"\b(runtime|latency|memory|flops|compute|computational cost|efficiency)\b", re.I),
    "repro_section": re.compile(r"\b(implementation|hyperparameter|training detail|code|reproducib|data split|compute)\b", re.I),
    "limitation_section": re.compile(r"\b(limitation|limitations|threats to validity|future work)\b", re.I),
}


def _load_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def _paper_id(row: Dict[str, Any]) -> str:
    return str(row.get("paper_id") or row.get("id") or "")


def _dataset_paper_text(row: Dict[str, Any]) -> str:
    return str(row.get("inputs") or "")


def _reviewer_text(row: Dict[str, Any]) -> str:
    return str(row.get("reviewer_comments") or row.get("outputs") or "")


def _snippets(text: str, pattern: re.Pattern[str], limit: int = 2, width: int = 180) -> List[str]:
    snippets: List[str] = []
    for match in pattern.finditer(text or ""):
        start = max(0, match.start() - width // 2)
        end = min(len(text), match.end() + width // 2)
        snippet = re.sub(r"\s+", " ", text[start:end]).strip()
        if snippet and snippet not in snippets:
            snippets.append(snippet)
        if len(snippets) >= limit:
            break
    return snippets


def _quote_bank_for_paper(raw_inputs: str, max_quotes: int = 24) -> List[Dict[str, Any]]:
    body, _ = _clean_paper_body(raw_inputs)
    return _build_evidence_quote_bank(body, max_quotes=max_quotes)


def _run_state_for_paper(rows: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    for row in rows:
        pid = _paper_id(row)
        if pid and pid not in out:
            out[pid] = row.get("review_state") or {}
    return out


def _state_negative_type_counts(state: Dict[str, Any]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for ev in state.get("evidence_map", []) or []:
        if not isinstance(ev, dict):
            continue
        typ = str(ev.get("negative_evidence_type") or "").strip()
        if not typ:
            text = " ".join(str(ev.get(key) or "") for key in ("raw_quote", "evidence"))
            typ = _classify_negative_evidence_type(text)
        if typ:
            stance = str(ev.get("stance") or "").lower()
            if stance in {"contradicts", "missing"} or typ not in {"generic_gap", "neutral_control_context"}:
                counts[typ] += 1
    return counts


def _quote_bank_type_counts(quote_bank: Iterable[Dict[str, Any]]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for item in quote_bank:
        if not isinstance(item, dict):
            continue
        quote = str(item.get("raw_quote") or "")
        typ = str(item.get("negative_evidence_type") or "") or _classify_negative_evidence_type(quote)
        if typ:
            counts[typ] += 1
    return counts


def audit(dataset_path: Path, run_path: Path) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    frame = pd.read_parquet(dataset_path)
    dataset_rows = frame.to_dict(orient="records")
    run_rows = _load_jsonl(run_path)
    state_by_id = _run_state_for_paper(run_rows)

    case_rows: List[Dict[str, Any]] = []
    summary: Dict[str, Any] = {
        "dataset": str(dataset_path),
        "run": str(run_path),
        "papers": 0,
        "oracle_mentions": Counter(),
        "paper_raw_mentions": Counter(),
        "quote_bank_mentions": Counter(),
        "state_negative_mentions": Counter(),
        "oracle_but_no_quote_bank": Counter(),
        "oracle_and_quote_bank_but_no_state": Counter(),
        "section_cues": Counter(),
    }

    for ds_row in dataset_rows:
        pid = str(ds_row.get("id") or "")
        if pid not in state_by_id:
            continue
        summary["papers"] += 1
        raw_inputs = _dataset_paper_text(ds_row)
        reviewer = _reviewer_text(ds_row)
        quote_bank = _quote_bank_for_paper(raw_inputs, max_quotes=24)
        qb_counts = _quote_bank_type_counts(quote_bank)
        state_counts = _state_negative_type_counts(state_by_id[pid])
        body, _ = _clean_paper_body(raw_inputs)

        section_hits = {
            name: bool(pattern.search(body))
            for name, pattern in PAPER_SECTION_CUES.items()
        }
        for name, hit in section_hits.items():
            if hit:
                summary["section_cues"][name] += 1

        type_row: Dict[str, Any] = {
            "paper_id": pid,
            "section_hits": section_hits,
            "types": {},
        }
        for typ, pattern in TARGET_TYPES.items():
            oracle_hit = bool(pattern.search(reviewer))
            paper_hit = bool(pattern.search(body))
            qb_hit = qb_counts.get(typ, 0) > 0
            state_hit = state_counts.get(typ, 0) > 0
            if oracle_hit:
                summary["oracle_mentions"][typ] += 1
            if paper_hit:
                summary["paper_raw_mentions"][typ] += 1
            if qb_hit:
                summary["quote_bank_mentions"][typ] += 1
            if state_hit:
                summary["state_negative_mentions"][typ] += 1
            if oracle_hit and not qb_hit:
                summary["oracle_but_no_quote_bank"][typ] += 1
            if oracle_hit and qb_hit and not state_hit:
                summary["oracle_and_quote_bank_but_no_state"][typ] += 1

            type_row["types"][typ] = {
                "oracle_mention": oracle_hit,
                "paper_raw_mention": paper_hit,
                "quote_bank_count": int(qb_counts.get(typ, 0)),
                "state_negative_count": int(state_counts.get(typ, 0)),
                "reviewer_snippets": _snippets(reviewer, pattern, limit=1),
                "paper_snippets": _snippets(body, pattern, limit=1),
            }
        case_rows.append(type_row)

    for key, value in list(summary.items()):
        if isinstance(value, Counter):
            summary[key] = dict(value)
    return case_rows, summary


def _md_table(headers: List[str], rows: List[List[Any]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(x) for x in row) + " |")
    return "\n".join(lines)


def write_outputs(case_rows: List[Dict[str, Any]], summary: Dict[str, Any], output_md: Path, output_json: Path) -> None:
    output_json.write_text(json.dumps({"summary": summary, "cases": case_rows}, ensure_ascii=False, indent=2), encoding="utf-8")
    types = list(TARGET_TYPES.keys())
    rows = []
    for typ in types:
        rows.append([
            typ,
            summary.get("oracle_mentions", {}).get(typ, 0),
            summary.get("paper_raw_mentions", {}).get(typ, 0),
            summary.get("quote_bank_mentions", {}).get(typ, 0),
            summary.get("state_negative_mentions", {}).get(typ, 0),
            summary.get("oracle_but_no_quote_bank", {}).get(typ, 0),
            summary.get("oracle_and_quote_bank_but_no_state", {}).get(typ, 0),
        ])

    md: List[str] = []
    md.append("# Negative Type Context Coverage Audit v1\n")
    md.append("本审计只读已有 parquet/jsonl，不调用模型，不修改 runtime。目标是判断缺失类 hard-negative 类型为 0 的原因：是相关上下文没有进入 quote/context，还是进入后没有转化为 verified negative evidence。\n")
    md.append(f"- dataset: `{summary.get('dataset')}`")
    md.append(f"- run: `{summary.get('run')}`")
    md.append(f"- papers: `{summary.get('papers')}`\n")
    md.append("## Aggregate Coverage\n")
    md.append(_md_table(
        [
            "type",
            "oracle reviewer mentions",
            "paper raw mentions",
            "quote-bank mentions",
            "state negative mentions",
            "oracle but no quote-bank",
            "oracle+quote-bank but no state",
        ],
        rows,
    ))
    md.append("\n## Section Cue Coverage\n")
    md.append(_md_table(["section cue", "papers"], sorted(summary.get("section_cues", {}).items())))
    md.append("\n## Case Notes\n")
    interesting = []
    for case in case_rows:
        for typ, item in case["types"].items():
            if item["oracle_mention"] and (not item["quote_bank_count"] or not item["state_negative_count"]):
                interesting.append([
                    case["paper_id"],
                    typ,
                    "Y" if item["paper_raw_mention"] else "N",
                    item["quote_bank_count"],
                    item["state_negative_count"],
                    (item["reviewer_snippets"] or [""])[0][:180],
                    (item["paper_snippets"] or [""])[0][:180],
                ])
    md.append(_md_table(
        ["paper_id", "type", "paper raw?", "quote-bank", "state", "reviewer snippet", "paper snippet"],
        interesting[:80],
    ))
    md.append("\n## Interpretation\n")
    md.append("- `oracle but no quote-bank` 高：优先改 section/quote selection。")
    md.append("- `oracle+quote-bank but no state` 高：优先改 type-targeted discovery prompt / adapter。")
    md.append("- `paper raw mentions` 低但 oracle 高：该类型多为 absence judgment，不能只靠 quote keyword，需要以 evaluation/method section coverage 和 reviewer oracle 做 opportunity-conditioned 评估。\n")
    output_md.write_text("\n".join(md), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--run", required=True)
    parser.add_argument("--output-md", required=True)
    parser.add_argument("--output-json", required=True)
    args = parser.parse_args()
    cases, summary = audit(Path(args.dataset), Path(args.run))
    write_outputs(cases, summary, Path(args.output_md), Path(args.output_json))
    print(f"wrote {args.output_md} and {args.output_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
