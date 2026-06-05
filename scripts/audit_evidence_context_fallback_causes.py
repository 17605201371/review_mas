#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

FALLBACK_PREFIXES = ("evidence-fallback-", "evidence-general-")


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def is_evidence_turn(turn: Dict[str, Any]) -> bool:
    selected = turn.get("selected_agents") or []
    return "Evidence Agent" in selected or bool(turn.get("evidence_context_mode"))


def evidence_payloads(turn: Dict[str, Any]) -> List[Dict[str, Any]]:
    payloads = []
    for item in turn.get("worker_payloads", []) or []:
        if item.get("agent_id") == "Evidence Agent":
            payloads.append(item.get("payload") or {})
    return payloads


def fallback_evidence_items(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    out = []
    for ev in payload.get("evidence_map", []) or []:
        if str(ev.get("evidence_id") or "").startswith(FALLBACK_PREFIXES):
            out.append(ev)
    return out


def payload_has_real_support(payload: Dict[str, Any]) -> bool:
    for ev in payload.get("evidence_map", []) or []:
        cid = str(ev.get("claim_id") or "")
        if "fallback" in cid.lower() or not cid:
            continue
        if str(ev.get("stance") or "").lower() in {"supports", "partially_supports"}:
            return True
    return False


def turn_reason(turn: Dict[str, Any], payload: Dict[str, Any]) -> str:
    if fallback_evidence_items(payload):
        return "fallback_evidence_id"
    rationale = str((turn.get("manager_payload") or {}).get("rationale") or "").lower()
    if "invalid json" in rationale or "json payload" in rationale or "parse" in rationale:
        return "manager_json_fallback"
    if not payload:
        return "missing_payload"
    return "other"


def summarize_run(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    totals = Counter()
    context_chars = []
    source_counts = Counter()
    mode_counts = Counter()
    per_row = []
    fallback_examples = []

    for row in rows:
        pid = row.get("paper_id")
        row_counts = Counter()
        for idx, turn in enumerate(row.get("turn_logs", []) or []):
            if not is_evidence_turn(turn):
                continue
            totals["evidence_turns"] += 1
            row_counts["evidence_turns"] += 1
            mode = str(turn.get("evidence_context_mode") or "missing")
            mode_counts[mode] += 1
            if turn.get("evidence_context_chars") is not None:
                try:
                    context_chars.append(int(turn.get("evidence_context_chars") or 0))
                except (TypeError, ValueError):
                    pass
            for source in turn.get("evidence_context_snippet_sources") or []:
                source_counts[str(source)] += 1
            for key in ["method", "results", "conclusion", "table_or_figure"]:
                if turn.get(f"evidence_context_contains_{key}"):
                    totals[f"contains_{key}"] += 1
                    row_counts[f"contains_{key}"] += 1
            target_count = len(turn.get("final_action_target_claim_ids") or [])
            if target_count > 1:
                totals["broad_target_turns"] += 1
                row_counts["broad_target_turns"] += 1
            payloads = evidence_payloads(turn)
            if not payloads:
                totals["missing_payload_turns"] += 1
                row_counts["missing_payload_turns"] += 1
            for payload in payloads:
                totals["evidence_payloads"] += 1
                row_counts["evidence_payloads"] += 1
                if payload_has_real_support(payload):
                    totals["payloads_with_real_support"] += 1
                    row_counts["payloads_with_real_support"] += 1
                fb_items = fallback_evidence_items(payload)
                if fb_items:
                    totals["fallback_payloads"] += 1
                    row_counts["fallback_payloads"] += 1
                    reason = turn_reason(turn, payload)
                    totals[f"fallback_reason_{reason}"] += 1
                    row_counts[f"fallback_reason_{reason}"] += 1
                    if len(fallback_examples) < 12:
                        fallback_examples.append({
                            "paper_id": pid,
                            "turn_index": idx,
                            "context_mode": turn.get("evidence_context_mode"),
                            "context_chars": turn.get("evidence_context_chars"),
                            "snippet_sources": turn.get("evidence_context_snippet_sources") or [],
                            "contains_method": bool(turn.get("evidence_context_contains_method")),
                            "contains_results": bool(turn.get("evidence_context_contains_results")),
                            "contains_table_or_figure": bool(turn.get("evidence_context_contains_table_or_figure")),
                            "target_count": target_count,
                            "reason": reason,
                            "fallback_evidence_ids": [ev.get("evidence_id") for ev in fb_items],
                            "fallback_claim_ids": [ev.get("claim_id") for ev in fb_items],
                        })
        per_row.append({"paper_id": pid, **dict(row_counts)})

    evidence_turns = totals["evidence_turns"] or 1
    return {
        "summary": {
            **dict(totals),
            "avg_context_chars": sum(context_chars) / len(context_chars) if context_chars else 0,
            "visible_method_rate": totals["contains_method"] / evidence_turns,
            "visible_results_rate": totals["contains_results"] / evidence_turns,
            "visible_conclusion_rate": totals["contains_conclusion"] / evidence_turns,
            "visible_table_or_figure_rate": totals["contains_table_or_figure"] / evidence_turns,
            "broad_target_turn_rate": totals["broad_target_turns"] / evidence_turns,
            "fallback_payload_rate": totals["fallback_payloads"] / evidence_turns,
            "payload_real_support_rate": totals["payloads_with_real_support"] / (totals["evidence_payloads"] or 1),
            "context_mode_counts": dict(mode_counts),
            "snippet_source_counts": dict(source_counts),
        },
        "per_row": per_row,
        "fallback_examples": fallback_examples,
    }


def by_paper(per_row: Iterable[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    return {str(row.get("paper_id")): row for row in per_row}


def compare(base: Dict[str, Any], cand: Dict[str, Any]) -> List[Dict[str, Any]]:
    b = by_paper(base["per_row"])
    c = by_paper(cand["per_row"])
    rows = []
    for pid in sorted(set(b) | set(c)):
        br = b.get(pid, {})
        cr = c.get(pid, {})
        rows.append({
            "paper_id": pid,
            "baseline_fallback_payloads": br.get("fallback_payloads", 0),
            "candidate_fallback_payloads": cr.get("fallback_payloads", 0),
            "fallback_delta": cr.get("fallback_payloads", 0) - br.get("fallback_payloads", 0),
            "baseline_broad_target_turns": br.get("broad_target_turns", 0),
            "candidate_broad_target_turns": cr.get("broad_target_turns", 0),
            "broad_target_delta": cr.get("broad_target_turns", 0) - br.get("broad_target_turns", 0),
            "baseline_payloads_with_real_support": br.get("payloads_with_real_support", 0),
            "candidate_payloads_with_real_support": cr.get("payloads_with_real_support", 0),
            "real_support_payload_delta": cr.get("payloads_with_real_support", 0) - br.get("payloads_with_real_support", 0),
        })
    rows.sort(key=lambda r: (r["fallback_delta"], -r["real_support_payload_delta"]), reverse=True)
    return rows


def write_markdown(payload: Dict[str, Any], path: Path) -> None:
    base = payload["baseline"]["summary"]
    cand = payload["candidate"]["summary"]
    lines = [
        "# Evidence Context v2 Fallback Cause Audit",
        "",
        "## 结论",
        "",
        "v2 的 fallback 激增主要不是由 fallback claim binding 造成，而是更复杂/更长的 Evidence observation 使 fallback evidence payload 更频繁出现。它同时没有提高 real-support payload rate，因此不应继续直接加长 context 或堆 prompt。",
        "",
        "## Aggregate Compare",
        "",
        "| metric | baseline | context v2 | delta |",
        "|---|---:|---:|---:|",
    ]
    keys = [
        "evidence_turns", "evidence_payloads", "fallback_payloads", "fallback_payload_rate",
        "payloads_with_real_support", "payload_real_support_rate", "avg_context_chars",
        "visible_method_rate", "visible_results_rate", "visible_table_or_figure_rate", "broad_target_turn_rate",
    ]
    for k in keys:
        bv = base.get(k, 0)
        cv = cand.get(k, 0)
        if isinstance(bv, float) or isinstance(cv, float):
            lines.append(f"| `{k}` | {float(bv):.4f} | {float(cv):.4f} | {float(cv)-float(bv):+.4f} |")
        else:
            lines.append(f"| `{k}` | {bv} | {cv} | {cv-bv:+d} |")

    lines += [
        "",
        "## Fallback Reason Breakdown",
        "",
        "| reason | baseline | context v2 |",
        "|---|---:|---:|",
    ]
    reasons = sorted({k for k in base if k.startswith("fallback_reason_")} | {k for k in cand if k.startswith("fallback_reason_")})
    for k in reasons:
        lines.append(f"| `{k.replace('fallback_reason_', '')}` | {base.get(k, 0)} | {cand.get(k, 0)} |")

    lines += [
        "",
        "## Per-Case Deltas",
        "",
        "| paper_id | fallback delta | broad target delta | real-support payload delta |",
        "|---|---:|---:|---:|",
    ]
    for row in payload["case_deltas"]:
        if row["fallback_delta"] or row["broad_target_delta"] or row["real_support_payload_delta"]:
            lines.append(f"| {row['paper_id']} | {row['fallback_delta']} | {row['broad_target_delta']} | {row['real_support_payload_delta']} |")

    lines += [
        "",
        "## Context v2 Fallback Examples",
        "",
        "| paper_id | turn | reason | context chars | sources | target count | fallback ids |",
        "|---|---:|---|---:|---|---:|---|",
    ]
    for ex in payload["candidate"]["fallback_examples"]:
        sources = ",".join(ex.get("snippet_sources") or [])
        ids = ",".join(str(x) for x in ex.get("fallback_evidence_ids") or [])
        lines.append(f"| {ex['paper_id']} | {ex['turn_index']} | {ex['reason']} | {ex.get('context_chars') or 0} | {sources} | {ex['target_count']} | {ids} |")

    lines += [
        "",
        "## 下一步",
        "",
        "不要直接进入 Evidence Context v3。更合理的下一刀是继续保持 v1 context，围绕 Evidence Agent 输出结构做小修：降低 fallback payload 的触发概率、保留现有 binding 约束，并优先在 2-5 条 accept-side case 上做快速验证。",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", required=True)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--output-md", required=True)
    args = parser.parse_args()
    baseline = summarize_run(load_jsonl(Path(args.baseline)))
    candidate = summarize_run(load_jsonl(Path(args.candidate)))
    payload = {
        "baseline_input": args.baseline,
        "candidate_input": args.candidate,
        "baseline": baseline,
        "candidate": candidate,
        "case_deltas": compare(baseline, candidate),
    }
    Path(args.output_json).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output_json).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(payload, Path(args.output_md))
    print(json.dumps({"baseline": baseline["summary"], "candidate": candidate["summary"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
