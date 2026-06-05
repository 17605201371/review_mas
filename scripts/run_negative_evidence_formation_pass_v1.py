#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agent_system.inference.review_runner import (
    VllmReviewGenerator,
    _row_to_env_kwargs,
    extract_tagged_json,
    load_review_rows,
)
from agent_system.environments.env_package.review.state import _clean_paper_body

CORE_CRITERIA = {"novelty", "significance", "soundness", "empirical"}
REAL_CLAIM_PREFIX_BLOCKLIST = ("claim-fallback", "claim-general")
META_RE = re.compile(
    r"\b(excerpt|truncat|provided text|full text|not provided|insufficient context|cannot verify|"
    r"unable to verify|fallback|parse|raw output|agent|system|review limitation|not assessable)\b",
    re.I,
)
PAPER_GROUNDING_RE = re.compile(
    r"\b(method|algorithm|experiment|evaluation|baseline|dataset|metric|result|table|figure|ablation|"
    r"architecture|assumption|proof|theorem|model|framework|comparison|benchmark|contribution)\b",
    re.I,
)
NEGATIVE_CONTEXT_PATTERNS = [
    ("results", re.compile(r"\b(results?|evaluation|experiments?|benchmark|performance|metric|accuracy|f1|auc|bleu|rouge)\b", re.I)),
    ("table_figure", re.compile(r"\b(table|figure|fig\.?|appendix table)\b", re.I)),
    ("ablation", re.compile(r"\bablation\b|ablat", re.I)),
    ("baseline", re.compile(r"\b(baseline|comparison|compare|state-of-the-art|sota|outperform)\b", re.I)),
    ("dataset", re.compile(r"\b(dataset|data set|benchmark suite|train/test|split)\b", re.I)),
    ("limitation", re.compile(r"\b(limitation|failure|fails|weakness|future work|threats to validity)\b", re.I)),
    ("method", re.compile(r"\b(method|approach|model|framework|algorithm|architecture|assumption|theorem|proof)\b", re.I)),
    ("conclusion", re.compile(r"\b(conclusion|discussion)\b", re.I)),
]


def norm(value: Any) -> str:
    return str(value or "").strip().lower()


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_jsonl(path: Path, rows: Sequence[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_md(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def is_real_claim_id(claim_id: Any) -> bool:
    cid = norm(claim_id)
    return bool(cid) and not cid.startswith(REAL_CLAIM_PREFIX_BLOCKLIST)


def clip(text: Any, limit: int = 900) -> str:
    value = str(text or "").strip()
    if len(value) <= limit:
        return value
    return value[: max(0, limit - 18)].rstrip() + "\n...[truncated]"


def render_negative_evidence_context(task: Dict[str, Any], max_length: int = 5000) -> str:
    body, _ = _clean_paper_body(str(task.get("paper_text") or task.get("question") or ""))
    body = body.strip()
    if not body:
        return ""
    snippets: List[tuple[str, int, int, str]] = []
    intro_end = min(len(body), 700)
    snippets.append(("front_matter", 0, intro_end, body[:intro_end]))
    for label, pattern in NEGATIVE_CONTEXT_PATTERNS:
        for match in pattern.finditer(body):
            start = max(0, match.start() - 450)
            end = min(len(body), match.end() + 850)
            snippets.append((label, start, end, body[start:end]))
            break
    snippets.sort(key=lambda item: item[1])
    merged: List[tuple[str, int, int, str]] = []
    for label, start, end, text in snippets:
        if merged and start <= merged[-1][2] + 120:
            prev_label, prev_start, prev_end, _ = merged[-1]
            merged[-1] = (prev_label + "+" + label, prev_start, max(prev_end, end), body[prev_start:max(prev_end, end)])
        else:
            merged.append((label, start, end, text))
    parts = []
    used = 0
    for label, _start, _end, text in merged:
        cleaned = " ".join(text.split())
        if not cleaned:
            continue
        segment = f"[{label}] {cleaned}"
        if used + len(segment) + 2 > max_length:
            remaining = max_length - used - 2
            if remaining > 200:
                parts.append(segment[:remaining].rstrip())
            break
        parts.append(segment)
        used += len(segment) + 2
    return "\n\n".join(parts)


def compact_claims(state: Dict[str, Any], limit: int = 5) -> List[Dict[str, Any]]:
    claims = []
    for item in state.get("claims", []) or []:
        if not isinstance(item, dict):
            continue
        cid = item.get("claim_id", "")
        if not is_real_claim_id(cid):
            continue
        claims.append(
            {
                "claim_id": cid,
                "claim": clip(item.get("claim"), 260),
                "importance": item.get("importance", ""),
                "status": item.get("status", ""),
                "supporting_evidence_ids": item.get("supporting_evidence_ids", []) or [],
            }
        )
    return claims[:limit]


def compact_evidence(state: Dict[str, Any], limit: int = 8) -> List[Dict[str, Any]]:
    rows = []
    for item in state.get("evidence_map", []) or []:
        if not isinstance(item, dict):
            continue
        rows.append(
            {
                "evidence_id": item.get("evidence_id", ""),
                "claim_id": item.get("claim_id", ""),
                "stance": item.get("stance", ""),
                "strength": item.get("strength", ""),
                "source": item.get("source", ""),
                "evidence": clip(item.get("evidence"), 240),
            }
        )
    # Prefer real non-fallback evidence and existing negative/missing entries.
    rows.sort(
        key=lambda ev: (
            0 if is_real_claim_id(ev.get("claim_id")) and ev.get("source") != "fallback-extraction" else 1,
            0 if norm(ev.get("stance")) in {"contradicts", "missing", "refutes"} else 1,
        )
    )
    return rows[:limit]


def compact_flaws(state: Dict[str, Any], limit: int = 6) -> List[Dict[str, Any]]:
    rows = []
    for item in state.get("flaw_candidates", []) or []:
        if not isinstance(item, dict):
            continue
        rows.append(
            {
                "flaw_id": item.get("flaw_id") or item.get("id") or "",
                "title": clip(item.get("title"), 160),
                "description": clip(item.get("description") or item.get("flaw"), 280),
                "severity": item.get("severity", ""),
                "status": item.get("status", ""),
                "related_claim_ids": item.get("related_claim_ids") or item.get("claim_ids") or [],
                "evidence_ids": item.get("evidence_ids") or item.get("supporting_evidence_ids") or [],
            }
        )
    return rows[:limit]


def compact_open_items(state: Dict[str, Any], limit: int = 8) -> List[str]:
    texts: List[str] = []
    for bucket in ("unresolved_questions", "evidence_gaps", "conflict_notes"):
        for item in state.get(bucket, []) or []:
            if isinstance(item, dict):
                text = item.get("question") or item.get("note") or item.get("description") or json.dumps(item, ensure_ascii=False)
            else:
                text = str(item)
            if text:
                texts.append(f"{bucket}: {clip(text, 220)}")
    return texts[:limit]


def build_prompt(row: Dict[str, Any], dataset_task: Dict[str, Any], subset_case: Dict[str, Any]) -> str:
    state = row.get("review_state") or {}
    paper_context = render_negative_evidence_context(dataset_task, max_length=5000)
    payload = {
        "paper_id": row.get("paper_id"),
        "focus_criteria": ["empirical", "soundness", "novelty", "significance"],
        "real_claims": compact_claims(state),
        "current_evidence": compact_evidence(state),
        "current_flaws": compact_flaws(state),
        "open_questions_or_gaps": compact_open_items(state),
        "paper_context": paper_context,
    }
    return (
        "/no_think\n"
        "You are a negative-evidence and flaw-confirmation auditor for a paper-review state.\n"
        "Do not output analysis, chain-of-thought, markdown, or prose. Start directly with <json>.\n"
        "Use ONLY the provided paper context and current ReviewState summary. Do not use reviewer comments or gold labels as evidence.\n"
        "Your job is not to make a final accept/reject decision. Your job is to find paper-grounded negative evidence or confirm/downgrade existing flaw candidates.\n\n"
        "Rules:\n"
        "- Focus only on empirical, soundness, novelty, and significance.\n"
        "- A trusted blocker must be tied to a real claim_id from real_claims, not a fallback/general claim.\n"
        "- Do not treat excerpt limits, missing full text, parse failures, fallback failures, or system uncertainty as paper flaws.\n"
        "- If the paper context is insufficient, emit not_assessable_items instead of inventing weaknesses.\n"
        "- If you cannot ground a negative claim in the paper context, set grounding_strength='weak' and do not mark it confirmed.\n\n"
        "Return compact JSON only. Keep every string under 18 words. Use at most one item in each list.\n"
        "Return only JSON inside <json>...</json> with this schema:\n"
        "{\n"
        "  \"negative_evidence_items\": [\n"
        "    {\"criterion\":\"empirical|soundness|novelty|significance\", \"claim_id\":\"claim-*\", \"polarity\":\"contradicts|missing_required_support|limits_claim\", \"paper_anchor\":\"short section/quote\", \"evidence_text\":\"short negative evidence\", \"grounding_strength\":\"strong|medium|weak\", \"confidence\":0.0, \"rationale\":\"short reason\"}\n"
        "  ],\n"
        "  \"flaw_confirmation_items\": [\n"
        "    {\"flaw_id\":\"existing id or new\", \"criterion\":\"empirical|soundness|novelty|significance\", \"status\":\"confirmed|downgraded|not_assessable\", \"severity\":\"critical|major|minor|none\", \"related_claim_ids\":[\"claim-*\"], \"evidence_refs\":[\"short anchor\"], \"confidence\":0.0, \"rationale\":\"short reason\"}\n"
        "  ],\n"
        "  \"not_assessable_items\": [\n"
        "    {\"criterion\":\"empirical|soundness|novelty|significance\", \"reason\":\"short missing evidence\", \"related_claim_ids\":[\"claim-*\"]}\n"
        "  ]\n"
        "}\n\n"
        f"Input:\n{json.dumps(payload, ensure_ascii=False, indent=2)}\n"
        "/no_think\n"
    )


def parse_payload(raw: str) -> Dict[str, Any]:
    try:
        data = extract_tagged_json(raw)
        if isinstance(data, dict):
            return data
    except Exception:
        pass
    try:
        return json.loads(raw)
    except Exception:
        return {
            "negative_evidence_items": [],
            "flaw_confirmation_items": [],
            "not_assessable_items": [{"criterion": "unknown", "reason": "parse_failed", "related_claim_ids": []}],
            "_parse_error": True,
        }


def confidence(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def classify_pass_payload(payload: Dict[str, Any], real_claim_ids: Iterable[str]) -> Dict[str, Any]:
    real_claims = set(str(x) for x in real_claim_ids)
    trusted_negative_items = []
    weak_negative_items = []
    trusted_flaw_items = []
    weak_flaw_items = []
    not_assessable = payload.get("not_assessable_items", []) if isinstance(payload.get("not_assessable_items"), list) else []

    for item in payload.get("negative_evidence_items", []) or []:
        if not isinstance(item, dict):
            continue
        criterion = norm(item.get("criterion"))
        claim_id = str(item.get("claim_id") or "")
        text = " ".join(str(item.get(k) or "") for k in ("paper_anchor", "evidence_text", "rationale"))
        conf = confidence(item.get("confidence"))
        strong_enough = norm(item.get("grounding_strength")) in {"strong", "medium"} and conf >= 0.55
        trusted = (
            criterion in CORE_CRITERIA
            and claim_id in real_claims
            and strong_enough
            and PAPER_GROUNDING_RE.search(text)
            and not META_RE.search(text)
        )
        (trusted_negative_items if trusted else weak_negative_items).append(item)

    for item in payload.get("flaw_confirmation_items", []) or []:
        if not isinstance(item, dict):
            continue
        criterion = norm(item.get("criterion"))
        claims = [str(x) for x in (item.get("related_claim_ids") or [])]
        text = " ".join(str(item.get(k) or "") for k in ("rationale", "evidence_refs"))
        conf = confidence(item.get("confidence"))
        trusted = (
            criterion in CORE_CRITERIA
            and norm(item.get("status")) == "confirmed"
            and norm(item.get("severity")) in {"major", "critical"}
            and any(cid in real_claims for cid in claims)
            and conf >= 0.55
            and not META_RE.search(text)
        )
        (trusted_flaw_items if trusted else weak_flaw_items).append(item)

    return {
        "trusted_negative_evidence_count": len(trusted_negative_items),
        "weak_negative_evidence_count": len(weak_negative_items),
        "trusted_flaw_confirmation_count": len(trusted_flaw_items),
        "weak_flaw_confirmation_count": len(weak_flaw_items),
        "not_assessable_count": len(not_assessable),
        "trusted_blocker_count": len(trusted_negative_items) + len(trusted_flaw_items),
        "trusted_negative_items": trusted_negative_items,
        "trusted_flaw_items": trusted_flaw_items,
    }


def group_summary(rows: List[Dict[str, Any]], tag: str) -> Dict[str, Any]:
    subset = [r for r in rows if r["tag"] == tag]
    return {
        "rows": len(subset),
        "trusted_blocker_rows": sum(1 for r in subset if r["trusted_blocker_count"] > 0),
        "avg_trusted_blockers": round(sum(r["trusted_blocker_count"] for r in subset) / len(subset), 3) if subset else 0,
        "not_assessable_rows": sum(1 for r in subset if r["not_assessable_count"] > 0),
        "parse_error_rows": sum(1 for r in subset if r["parse_error"]),
    }


def table_row(values: Iterable[Any]) -> str:
    return "| " + " | ".join(str(v).replace("\n", " ") for v in values) + " |"


def render_protocol() -> str:
    return """# Negative Evidence Formation / Flaw Confirmation Pass v1 Protocol

## 定位

本轮是小样本诊断 pass，不改变 final decision，不写回 live ReviewState，不使用 reviewer comments。目标是验证系统能否从 paper text + 当前 ReviewState 中形成可信负向证据和 confirmed flaw。

## 输入

- 7 条 criterion Sim4 false accept。
- 3 条 criterion Sim4 recovered accept。
- 当前 final ReviewState。
- section-aware paper context。

## 输出

- `negative_evidence_items`
- `flaw_confirmation_items`
- `not_assessable_items`

## Trusted blocker 条件

- 绑定真实 claim_id。
- 非 fallback / system / excerpt limitation。
- 关联 empirical / soundness / novelty / significance。
- grounding strength 为 medium/strong。
- confidence >= 0.55。

## 约束

本 pass 只评估 formation 能力，不进入最终推荐聚合。
"""


def render_compare(summary: Dict[str, Any]) -> str:
    lines = [
        "# Negative Evidence Formation Pass v1 Compare",
        "",
        "## Summary",
        "",
        table_row(["group", "rows", "trusted_blocker_rows", "avg_trusted_blockers", "not_assessable_rows", "parse_error_rows"]),
        table_row(["---", "---:", "---:", "---:", "---:", "---:"]),
    ]
    for group, data in summary["group_summaries"].items():
        lines.append(table_row([group, data["rows"], data["trusted_blocker_rows"], data["avg_trusted_blockers"], data["not_assessable_rows"], data["parse_error_rows"]]))
    lines += [
        "",
        "## Interpretation",
        "",
        "- false accept 中形成 trusted blocker，说明负证据 formation pass 有潜在价值。",
        "- recovered accept 中形成 trusted blocker，则说明规则还不够区分，不能直接进入 final decision。",
        "- parse_error_rows 应保持低，否则该 pass 还需要 JSON robustness。"
    ]
    return "\n".join(lines)


def render_case_table(rows: List[Dict[str, Any]]) -> str:
    lines = [
        "# Negative Evidence Formation Pass v1 Case Table",
        "",
        table_row(["paper_id", "gold", "tag", "trusted_blockers", "trusted_neg", "trusted_flaw", "weak_neg", "weak_flaw", "not_assessable", "parse_error"]),
        table_row(["---", "---", "---", "---:", "---:", "---:", "---:", "---:", "---:", "---"]),
    ]
    for row in rows:
        lines.append(table_row([
            row["paper_id"],
            row["gold_decision"],
            row["tag"],
            row["trusted_blocker_count"],
            row["trusted_negative_evidence_count"],
            row["trusted_flaw_confirmation_count"],
            row["weak_negative_evidence_count"],
            row["weak_flaw_confirmation_count"],
            row["not_assessable_count"],
            int(row["parse_error"]),
        ]))
    return "\n".join(lines)


def render_decision(summary: Dict[str, Any]) -> str:
    false_accept = summary["group_summaries"].get("false_accept", {})
    recovered = summary["group_summaries"].get("recovered_accept", {})
    keep = (
        false_accept.get("trusted_blocker_rows", 0) > 0
        and false_accept.get("trusted_blocker_rows", 0) > recovered.get("trusted_blocker_rows", 0)
        and false_accept.get("parse_error_rows", 0) == 0
    )
    decision = "继续迭代，但暂不进入 final decision" if keep else "不直接保留为决策模块，先分析误伤/漏检"
    return f"""# Negative Evidence Formation Pass v1 Decision

## 结论

{decision}。

## 关键数字

- false accept trusted_blocker_rows: `{false_accept.get('trusted_blocker_rows', 0)} / {false_accept.get('rows', 0)}`
- recovered accept trusted_blocker_rows: `{recovered.get('trusted_blocker_rows', 0)} / {recovered.get('rows', 0)}`
- false accept parse_error_rows: `{false_accept.get('parse_error_rows', 0)}`

## 判断

如果 false accept 与 recovered accept 都大量形成 trusted blocker，则说明当前 pass 能找负面线索，但缺少 discriminative confirmation，不能直接用于 reject。

下一步只允许做两类小修：

1. 收紧 trusted blocker 条件，要求 paper anchor 更具体。
2. 对 recovered accept 的 blocker 做 precision audit，找出误伤来源。

暂时仍不改 final decision 阈值。
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-path", default="/reviewF/datasets/Qwen3___5-4B")
    parser.add_argument("--dataset-path", default="/reviewF/datasets/drmas_review/test.parquet")
    parser.add_argument("--source-jsonl", default="outputs/results_main/review_infer/mainline_final_v1_9b_fulltest39_dryrun.jsonl")
    parser.add_argument("--subset-json", default="outputs/results_main/review_infer/negative_evidence_formation_v1_diagnostic_subset.json")
    parser.add_argument("--output-jsonl", default="outputs/results_main/review_infer/negative_evidence_formation_pass_v1_4_4b_diagnostic10.jsonl")
    parser.add_argument("--summary-json", default="outputs/results_main/review_infer/negative_evidence_formation_pass_v1_4_4b_diagnostic10_summary.json")
    parser.add_argument("--doc-dir", default="docs/experiments/mainline_current")
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--max-model-len", type=int, default=6144)
    parser.add_argument("--max-tokens", type=int, default=512)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--top-p", type=float, default=0.9)
    parser.add_argument("--gpu-memory-utilization", type=float, default=0.9)
    parser.add_argument("--max-num-seqs", type=int, default=64)
    parser.add_argument("--seed", type=int, default=20260429)
    args = parser.parse_args()

    subset = load_json(Path(args.subset_json))
    subset_cases = {case["paper_id"]: case for case in subset["cases"]}
    source_rows = {row.get("paper_id"): row for row in load_jsonl(Path(args.source_jsonl))}

    dataset_rows = load_review_rows(args.dataset_path, split="test")
    dataset_tasks = {}
    for row in dataset_rows:
        task = _row_to_env_kwargs(row)
        pid = task.get("paper_id")
        if pid in subset_cases:
            dataset_tasks[pid] = task

    requests = []
    row_meta = []
    for pid in subset["paper_ids"]:
        if pid not in source_rows or pid not in dataset_tasks:
            continue
        prompt = build_prompt(source_rows[pid], dataset_tasks[pid], subset_cases[pid])
        requests.append(("Negative Evidence Formation Agent", prompt))
        row_meta.append((pid, source_rows[pid], subset_cases[pid]))

    generator = VllmReviewGenerator(
        model_path=args.model_path,
        gpu_memory_utilization=args.gpu_memory_utilization,
        max_model_len=args.max_model_len,
        temperature=args.temperature,
        top_p=args.top_p,
        max_tokens=args.max_tokens,
        max_num_seqs=args.max_num_seqs,
        seed=args.seed,
    )

    outputs: List[str] = []
    for start in range(0, len(requests), max(1, args.batch_size)):
        outputs.extend(generator.generate_many(requests[start : start + args.batch_size]))

    result_rows = []
    for (pid, source_row, subset_case), raw in zip(row_meta, outputs):
        payload = parse_payload(raw)
        real_claim_ids = [item.get("claim_id") for item in compact_claims(source_row.get("review_state") or {}, limit=20)]
        classification = classify_pass_payload(payload, real_claim_ids)
        parse_error = bool(payload.get("_parse_error"))
        row = {
            "paper_id": pid,
            "gold_decision": subset_case.get("gold_decision"),
            "tag": subset_case.get("tag"),
            "sim4_label": subset_case.get("sim4_label"),
            "raw_output": raw,
            "parsed_payload": payload,
            "parse_error": parse_error,
            **classification,
        }
        result_rows.append(row)

    summary = {
        "model_path": args.model_path,
        "source_jsonl": args.source_jsonl,
        "subset_json": args.subset_json,
        "rows": len(result_rows),
        "group_summaries": {
            "false_accept": group_summary(result_rows, "false_accept"),
            "recovered_accept": group_summary(result_rows, "recovered_accept"),
        },
        "case_rows": [
            {k: v for k, v in row.items() if k not in {"raw_output", "parsed_payload", "trusted_negative_items", "trusted_flaw_items"}}
            for row in result_rows
        ],
    }

    write_jsonl(Path(args.output_jsonl), result_rows)
    write_json(Path(args.summary_json), summary)
    doc_dir = Path(args.doc_dir)
    write_md(doc_dir / "NEGATIVE_EVIDENCE_FORMATION_PASS_V1_4_PROTOCOL.md", render_protocol())
    write_md(doc_dir / "NEGATIVE_EVIDENCE_FORMATION_PASS_V1_4_COMPARE.md", render_compare(summary))
    write_md(doc_dir / "NEGATIVE_EVIDENCE_FORMATION_PASS_V1_4_CASE_TABLE.md", render_case_table(result_rows))
    write_md(doc_dir / "NEGATIVE_EVIDENCE_FORMATION_PASS_V1_4_DECISION.md", render_decision(summary))

    print(json.dumps({
        "jsonl": args.output_jsonl,
        "summary": args.summary_json,
        "docs": [
            "NEGATIVE_EVIDENCE_FORMATION_PASS_V1_4_PROTOCOL.md",
            "NEGATIVE_EVIDENCE_FORMATION_PASS_V1_4_COMPARE.md",
            "NEGATIVE_EVIDENCE_FORMATION_PASS_V1_4_CASE_TABLE.md",
            "NEGATIVE_EVIDENCE_FORMATION_PASS_V1_4_DECISION.md",
        ],
        "group_summaries": summary["group_summaries"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
