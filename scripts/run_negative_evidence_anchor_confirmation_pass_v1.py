#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agent_system.inference.review_runner import VllmReviewGenerator, extract_tagged_json

CORE_CRITERIA = {"empirical", "soundness", "novelty", "significance"}
REAL_CLAIM_PREFIX_BLOCKLIST = ("claim-fallback", "claim-general")
META_RE = re.compile(
    r"\b(excerpt|truncat|not provided|insufficient context|cannot verify|unable to verify|"
    r"fallback|parse|agent|system|review limitation|not assessable|no anchor)\b",
    re.I,
)
PAPER_ANCHOR_TYPES = {"table", "figure", "results", "baseline", "ablation", "dataset_metric"}
PAPER_ANCHOR_RE = re.compile(
    r"\b(table|figure|fig\.?|result|experiment|evaluation|baseline|ablation|dataset|metric|"
    r"accuracy|f1|auc|bleu|rouge|performance|comparison|outperform)\b",
    re.I,
)


def norm(value: Any) -> str:
    return str(value or "").strip().lower()


def read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> List[Dict[str, Any]]:
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


def table_row(values: Iterable[Any]) -> str:
    return "| " + " | ".join(str(v).replace("\n", " ") for v in values) + " |"


def clip(value: Any, limit: int = 500) -> str:
    text = " ".join(str(value or "").split())
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 18)].rstrip() + " ...[truncated]"


def is_real_claim_id(claim_id: Any) -> bool:
    cid = norm(claim_id)
    return bool(cid) and not cid.startswith(REAL_CLAIM_PREFIX_BLOCKLIST)


def compact_claims(state: Dict[str, Any], limit: int = 6) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for item in state.get("claims", []) or []:
        if not isinstance(item, dict):
            continue
        cid = item.get("claim_id", "")
        if not is_real_claim_id(cid):
            continue
        rows.append(
            {
                "claim_id": cid,
                "claim": clip(item.get("claim"), 220),
                "status": item.get("status", ""),
                "importance": item.get("importance", ""),
            }
        )
    return rows[:limit]


def compact_anchors(anchors: List[Dict[str, Any]], limit: int = 6) -> List[Dict[str, Any]]:
    rows = []
    for item in anchors[:limit]:
        rows.append(
            {
                "anchor_id": item.get("anchor_id", ""),
                "anchor_type": item.get("anchor_type", ""),
                "has_quantitative_signal": bool(item.get("has_quantitative_signal")),
                "text": clip(item.get("text"), 700),
            }
        )
    return rows


def build_prompt(source_row: Dict[str, Any], anchor_row: Dict[str, Any]) -> str:
    state = source_row.get("review_state") or {}
    payload = {
        "paper_id": anchor_row.get("paper_id"),
        "real_claims": compact_claims(state),
        "paper_anchors": compact_anchors(anchor_row.get("anchors") or []),
        "task": (
            "Confirm whether the anchors show a paper-grounded blocker. "
            "Use only the supplied anchors, not missing context."
        ),
    }
    return (
        "/no_think\n"
        "You are a strict negative-evidence anchor confirmation auditor.\n"
        "Return compact JSON only. Start directly with <json>. No prose.\n\n"
        "Rules:\n"
        "- Use ONLY paper_anchors. Do not cite abstract-only context unless the anchor itself contains table/result/baseline evidence.\n"
        "- A blocker must cite one anchor_id and one real claim_id from real_claims.\n"
        "- Do not treat missing context, excerpt limits, or absent table visibility as a paper flaw.\n"
        "- If anchors do not prove a blocker, return no_blocker_items or not_assessable_items.\n"
        "- Keep strings under 18 words. At most one item in each list.\n\n"
        "Schema:\n"
        "{\n"
        "  \"blocker_items\": [\n"
        "    {\"criterion\":\"empirical|soundness|novelty|significance\", \"claim_id\":\"claim-*\", \"anchor_id\":\"anchor-*\", \"blocker_type\":\"missing_baseline|weak_result|contradicted_claim|limited_evaluation|novelty_gap|soundness_gap\", \"anchor_quote\":\"short quote\", \"confidence\":0.0, \"rationale\":\"short reason\"}\n"
        "  ],\n"
        "  \"no_blocker_items\": [\n"
        "    {\"reason\":\"short reason\", \"anchor_ids\":[\"anchor-*\"]}\n"
        "  ],\n"
        "  \"not_assessable_items\": [\n"
        "    {\"reason\":\"short reason\", \"anchor_ids\":[\"anchor-*\"]}\n"
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
        data = json.loads(raw)
        if isinstance(data, dict):
            return data
    except Exception:
        pass
    return {"blocker_items": [], "no_blocker_items": [], "not_assessable_items": [{"reason": "parse_failed", "anchor_ids": []}], "_parse_error": True}


def confidence(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def classify_payload(payload: Dict[str, Any], source_row: Dict[str, Any], anchor_row: Dict[str, Any]) -> Dict[str, Any]:
    real_claims = {item["claim_id"] for item in compact_claims(source_row.get("review_state") or {}, limit=50)}
    anchors = {item.get("anchor_id"): item for item in anchor_row.get("anchors") or []}
    trusted = []
    weak = []
    for item in payload.get("blocker_items", []) or []:
        if not isinstance(item, dict):
            continue
        anchor = anchors.get(item.get("anchor_id"))
        text = " ".join(str(item.get(key) or "") for key in ("anchor_quote", "rationale", "blocker_type"))
        ok_anchor = bool(anchor) and anchor.get("anchor_type") in PAPER_ANCHOR_TYPES and bool(anchor.get("has_quantitative_signal"))
        ok = (
            norm(item.get("criterion")) in CORE_CRITERIA
            and item.get("claim_id") in real_claims
            and ok_anchor
            and confidence(item.get("confidence")) >= 0.6
            and PAPER_ANCHOR_RE.search(text)
            and not META_RE.search(text)
        )
        (trusted if ok else weak).append(item)
    return {
        "trusted_anchor_blocker_count": len(trusted),
        "weak_anchor_blocker_count": len(weak),
        "no_blocker_count": len(payload.get("no_blocker_items", []) or []),
        "not_assessable_count": len(payload.get("not_assessable_items", []) or []),
        "trusted_anchor_blockers": trusted,
        "weak_anchor_blockers": weak,
    }


def group_summary(rows: List[Dict[str, Any]], tag: str) -> Dict[str, Any]:
    subset = [row for row in rows if row.get("tag") == tag]
    return {
        "rows": len(subset),
        "trusted_blocker_rows": sum(1 for row in subset if row["trusted_anchor_blocker_count"] > 0),
        "avg_trusted_blockers": round(sum(row["trusted_anchor_blocker_count"] for row in subset) / len(subset), 3) if subset else 0,
        "weak_blocker_rows": sum(1 for row in subset if row["weak_anchor_blocker_count"] > 0),
        "not_assessable_rows": sum(1 for row in subset if row["not_assessable_count"] > 0),
        "parse_error_rows": sum(1 for row in subset if row["parse_error"]),
    }


def render_protocol() -> str:
    return """# Negative Evidence Anchor Confirmation Pass v1 Protocol

## 定位

本轮只在 10 条 diagnostic subset 上做 4B 小跑，不改 runtime、不写回 ReviewState、不接 final decision。

## 目标

验证 `Negative Evidence Anchor Extraction v1` 抽出的 table/result/baseline/ablation anchors 是否能支撑更高精度的 negative blocker confirmation。

## 约束

- 模型只能使用 `paper_anchors`。
- blocker 必须引用真实 `claim_id` 和一个 `anchor_id`。
- 不允许把 missing context / excerpt limitation / absent table visibility 当 paper flaw。
- trusted blocker 还要通过后处理：real claim、core criterion、quant anchor、confidence >= 0.6、非 meta。
"""


def render_compare(summary: Dict[str, Any]) -> str:
    lines = [
        "# Negative Evidence Anchor Confirmation Pass v1 Compare",
        "",
        table_row(["group", "rows", "trusted_blocker_rows", "avg_trusted", "weak_blocker_rows", "not_assessable_rows", "parse_error_rows"]),
        table_row(["---", "---:", "---:", "---:", "---:", "---:", "---:"]),
    ]
    for group, data in summary["group_summaries"].items():
        lines.append(table_row([group, data["rows"], data["trusted_blocker_rows"], data["avg_trusted_blockers"], data["weak_blocker_rows"], data["not_assessable_rows"], data["parse_error_rows"]]))
    return "\n".join(lines)


def render_case_table(rows: List[Dict[str, Any]]) -> str:
    lines = [
        "# Negative Evidence Anchor Confirmation Pass v1 Case Table",
        "",
        table_row(["paper_id", "tag", "trusted", "weak", "not_assessable", "parse_error", "trusted_items"]),
        table_row(["---", "---", "---:", "---:", "---:", "---:", "---"]),
    ]
    for row in rows:
        trusted_preview = "; ".join(
            f"{item.get('criterion')}:{item.get('anchor_id')}:{item.get('blocker_type')}"
            for item in row.get("trusted_anchor_blockers", [])
        )
        lines.append(table_row([row["paper_id"], row["tag"], row["trusted_anchor_blocker_count"], row["weak_anchor_blocker_count"], row["not_assessable_count"], int(row["parse_error"]), trusted_preview]))
    return "\n".join(lines)


def render_decision(summary: Dict[str, Any]) -> str:
    false_accept = summary["group_summaries"].get("false_accept", {})
    recovered = summary["group_summaries"].get("recovered_accept", {})
    return f"""# Negative Evidence Anchor Confirmation Pass v1 Decision

## 结论

本轮仍是诊断 pass，不能直接进入 final decision。是否继续取决于 false accept 覆盖与 recovered accept 误伤之间的差距。

## 关键数字

- false_accept trusted_blocker_rows: `{false_accept.get('trusted_blocker_rows', 0)} / {false_accept.get('rows', 0)}`
- recovered_accept trusted_blocker_rows: `{recovered.get('trusted_blocker_rows', 0)} / {recovered.get('rows', 0)}`
- parse_error_rows: `{false_accept.get('parse_error_rows', 0) + recovered.get('parse_error_rows', 0)}`

## 下一步判定

如果 recovered_accept 仍被 trusted blocker 命中，说明 anchor 约束还不够，需要做人工 case review 或 criterion-specific confirmation；不要接入推荐聚合。
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-path", default="/reviewF/datasets/Qwen3___5-4B")
    parser.add_argument("--source-jsonl", default="outputs/results_main/review_infer/mainline_final_v1_9b_fulltest39_dryrun.jsonl")
    parser.add_argument("--anchor-json", default="outputs/results_main/review_infer/negative_evidence_anchor_extraction_v1.json")
    parser.add_argument("--output-jsonl", default="outputs/results_main/review_infer/negative_evidence_anchor_confirmation_pass_v1_4b_diagnostic10.jsonl")
    parser.add_argument("--summary-json", default="outputs/results_main/review_infer/negative_evidence_anchor_confirmation_pass_v1_4b_diagnostic10_summary.json")
    parser.add_argument("--doc-dir", default="docs/experiments/mainline_current")
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--max-model-len", type=int, default=4096)
    parser.add_argument("--max-tokens", type=int, default=384)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--top-p", type=float, default=0.9)
    parser.add_argument("--gpu-memory-utilization", type=float, default=0.9)
    parser.add_argument("--max-num-seqs", type=int, default=64)
    parser.add_argument("--seed", type=int, default=20260429)
    args = parser.parse_args()

    source_rows = {row.get("paper_id"): row for row in read_jsonl(Path(args.source_jsonl))}
    anchor_data = read_json(Path(args.anchor_json))
    anchor_rows = [row for row in anchor_data.get("case_rows", []) if row.get("paper_id") in source_rows]

    prompts = []
    meta = []
    for anchor_row in anchor_rows:
        source_row = source_rows[anchor_row["paper_id"]]
        prompts.append(("Negative Evidence Anchor Confirmation Agent", build_prompt(source_row, anchor_row)))
        meta.append((source_row, anchor_row))

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
    for start in range(0, len(prompts), max(1, args.batch_size)):
        outputs.extend(generator.generate_many(prompts[start : start + args.batch_size]))

    rows = []
    for (source_row, anchor_row), raw in zip(meta, outputs):
        payload = parse_payload(raw)
        parsed = classify_payload(payload, source_row, anchor_row)
        row = {
            "paper_id": anchor_row["paper_id"],
            "tag": anchor_row.get("tag", ""),
            "gold_decision": anchor_row.get("gold_decision", ""),
            "raw_output": raw,
            "payload": payload,
            "parse_error": bool(payload.get("_parse_error")),
            **parsed,
        }
        rows.append(row)

    summary = {
        "source_jsonl": args.source_jsonl,
        "anchor_json": args.anchor_json,
        "rows": len(rows),
        "group_summaries": {
            "false_accept": group_summary(rows, "false_accept"),
            "recovered_accept": group_summary(rows, "recovered_accept"),
        },
        "trusted_blocker_rows_total": sum(1 for row in rows if row["trusted_anchor_blocker_count"] > 0),
        "parse_error_rows_total": sum(1 for row in rows if row["parse_error"]),
    }

    write_jsonl(Path(args.output_jsonl), rows)
    write_json(Path(args.summary_json), summary)
    doc_dir = Path(args.doc_dir)
    write_md(doc_dir / "NEGATIVE_EVIDENCE_ANCHOR_CONFIRMATION_PASS_V1_PROTOCOL.md", render_protocol())
    write_md(doc_dir / "NEGATIVE_EVIDENCE_ANCHOR_CONFIRMATION_PASS_V1_COMPARE.md", render_compare(summary))
    write_md(doc_dir / "NEGATIVE_EVIDENCE_ANCHOR_CONFIRMATION_PASS_V1_CASE_TABLE.md", render_case_table(rows))
    write_md(doc_dir / "NEGATIVE_EVIDENCE_ANCHOR_CONFIRMATION_PASS_V1_DECISION.md", render_decision(summary))
    print(json.dumps({"summary_json": args.summary_json, "rows": len(rows), "trusted_blocker_rows_total": summary["trusted_blocker_rows_total"], "parse_error_rows_total": summary["parse_error_rows_total"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
