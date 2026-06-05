#!/usr/bin/env python3
"""Compact hard-negative extraction pass for 9B confirmation.

This is an offline diagnostic pass. It does not write back to ReviewState and
does not change final decisions.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

SRC = PROJECT_ROOT / "scripts" / "run_negative_evidence_formation_pass_v1.py"
spec = importlib.util.spec_from_file_location("negative_pass_v1", SRC)
neg = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(neg)

from agent_system.inference.review_runner import VllmReviewGenerator, _row_to_env_kwargs, load_review_rows


def build_compact_prompt(row: Dict[str, Any], task: Dict[str, Any]) -> str:
    state = row.get("review_state") or {}
    claims = neg.compact_claims(state, limit=4)
    evidence = neg.compact_evidence(state, limit=5)
    flaws = neg.compact_flaws(state, limit=3)
    open_items = neg.compact_open_items(state, limit=4)
    context = neg.render_negative_evidence_context(task, max_length=2200)
    payload = {
        "paper_id": row.get("paper_id"),
        "claims": claims,
        "evidence": evidence,
        "flaws": flaws,
        "open_items": open_items,
        "paper_context": context,
    }
    return (
        "/no_think\n"
        "Extract paper-grounded hard negatives only. Return exactly one <json> object. "
        "Do not echo this prompt. Do not use markdown. Do not decide accept/reject. "
        "Do not treat missing full text, truncation, parser failure, fallback, or system uncertainty as paper flaws. "
        "Use only real claim_id values from claims. If no grounded hard negative is visible, use not_assessable_items.\n"
        "Schema: <json>{\"negative_evidence_items\":[{\"criterion\":\"empirical|soundness|novelty|significance\",\"claim_id\":\"claim-*\",\"polarity\":\"contradicts|missing_required_support|limits_claim\",\"paper_anchor\":\"short quote\",\"evidence_text\":\"short evidence\",\"grounding_strength\":\"strong|medium|weak\",\"confidence\":0.0,\"rationale\":\"short\"}],\"flaw_confirmation_items\":[{\"flaw_id\":\"id\",\"criterion\":\"empirical|soundness|novelty|significance\",\"status\":\"confirmed|downgraded|not_assessable\",\"severity\":\"critical|major|minor|none\",\"related_claim_ids\":[\"claim-*\"],\"evidence_refs\":[\"short quote\"],\"confidence\":0.0,\"rationale\":\"short\"}],\"not_assessable_items\":[{\"criterion\":\"empirical|soundness|novelty|significance\",\"reason\":\"short\",\"related_claim_ids\":[\"claim-*\"]}]}</json>\n"
        f"Input JSON:\n{json.dumps(payload, ensure_ascii=False, separators=(',', ':'))}\n"
        "/no_think\n"
    )


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_jsonl(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-path", default="/reviewF/datasets/Qwen3___5-9B")
    parser.add_argument("--dataset-path", default="/reviewF/datasets/drmas_review/test.parquet")
    parser.add_argument("--source-jsonl", required=True)
    parser.add_argument("--subset-json", required=True)
    parser.add_argument("--output-jsonl", required=True)
    parser.add_argument("--summary-json", required=True)
    parser.add_argument("--batch-size", type=int, default=2)
    parser.add_argument("--max-model-len", type=int, default=3072)
    parser.add_argument("--max-tokens", type=int, default=384)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--top-p", type=float, default=0.9)
    parser.add_argument("--gpu-memory-utilization", type=float, default=0.9)
    parser.add_argument("--max-num-seqs", type=int, default=32)
    parser.add_argument("--seed", type=int, default=20260429)
    args = parser.parse_args()

    subset = neg.load_json(Path(args.subset_json))
    subset_cases = {case["paper_id"]: case for case in subset["cases"]}
    source_rows = {row.get("paper_id"): row for row in neg.load_jsonl(Path(args.source_jsonl))}
    dataset_tasks = {}
    for raw in load_review_rows(args.dataset_path, split="test"):
        task = _row_to_env_kwargs(raw)
        pid = task.get("paper_id")
        if pid in subset_cases:
            dataset_tasks[pid] = task

    requests = []
    meta = []
    for pid in subset["paper_ids"]:
        if pid not in source_rows or pid not in dataset_tasks:
            continue
        requests.append(("Compact Hard Negative Agent", build_compact_prompt(source_rows[pid], dataset_tasks[pid])))
        meta.append((pid, source_rows[pid], subset_cases[pid]))

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
    for (pid, source_row, subset_case), raw in zip(meta, outputs):
        payload = neg.parse_payload(raw)
        real_claim_ids = [item.get("claim_id") for item in neg.compact_claims(source_row.get("review_state") or {}, limit=20)]
        classification = neg.classify_pass_payload(payload, real_claim_ids)
        result_rows.append(
            {
                "paper_id": pid,
                "gold_decision": subset_case.get("gold_decision"),
                "tag": subset_case.get("tag"),
                "soft_view_v1": subset_case.get("soft_view_v1"),
                "raw_output": raw,
                "parsed_payload": payload,
                "parse_error": bool(payload.get("_parse_error")),
                **classification,
            }
        )
    summary = {
        "model_path": args.model_path,
        "source_jsonl": args.source_jsonl,
        "subset_json": args.subset_json,
        "rows": len(result_rows),
        "case_rows": [
            {k: v for k, v in row.items() if k not in {"raw_output", "parsed_payload", "trusted_negative_items", "trusted_flaw_items"}}
            for row in result_rows
        ],
    }
    write_jsonl(Path(args.output_jsonl), result_rows)
    write_json(Path(args.summary_json), summary)
    print(json.dumps({"jsonl": args.output_jsonl, "summary": args.summary_json, "rows": len(result_rows)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
