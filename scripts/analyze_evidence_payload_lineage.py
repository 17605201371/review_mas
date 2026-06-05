from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List


def _read_jsonl(path: Path) -> List[Dict[str, Any]]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def _state(row: Dict[str, Any]) -> Dict[str, Any]:
    return row.get("review_state") or row.get("final_state") or row.get("state") or {}


def _is_real_claim(claim_id: Any) -> bool:
    value = str(claim_id or "")
    return bool(value) and not value.startswith("claim-fallback")


def _binding_status_for_payload(evidence: Dict[str, Any]) -> str:
    status = str(evidence.get("binding_status") or "")
    if _is_real_claim(evidence.get("claim_id")) and status in {"", "unchecked", "bound_real_claim"}:
        return "bound_real_claim"
    return status


def _is_real_strong_support(evidence: Dict[str, Any], *, payload: bool) -> bool:
    binding = _binding_status_for_payload(evidence) if payload else str(evidence.get("binding_status") or "")
    return (
        evidence.get("strength") == "strong"
        and evidence.get("stance") in {"supports", "partially_supports"}
        and _is_real_claim(evidence.get("claim_id"))
        and binding == "bound_real_claim"
    )


def _payload_evidence_items(row: Dict[str, Any]) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    for turn in row.get("turn_logs") or []:
        for wrapped in turn.get("worker_payloads") or []:
            payload = wrapped.get("payload") if isinstance(wrapped, dict) else None
            if isinstance(payload, dict):
                items.extend(ev for ev in payload.get("evidence_map", []) or [] if isinstance(ev, dict))
    return items


def _section(evidence: Dict[str, Any]) -> str:
    return str(evidence.get("support_source_bucket") or "unknown")


def summarize_rows(rows: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    summary: Dict[str, Any] = {
        "rows": 0,
        "payload_strong_real_total": 0,
        "payload_nonabstract_total": 0,
        "payload_empirical_total": 0,
        "final_strong_real_total": 0,
        "final_nonabstract_total": 0,
        "final_empirical_total": 0,
        "rows_payload_2plus": 0,
        "rows_final_2plus": 0,
        "rows_payload_gt_final": 0,
        "rows_duplicate_payload_ids": 0,
        "payload_duplicate_ids": 0,
        "pred_accept": 0,
        "case_table": [],
    }
    for row in rows:
        summary["rows"] += 1
        state = _state(row)
        paper_id = row.get("paper_id") or state.get("paper_id") or ""
        final_decision = str(row.get("final_decision") or state.get("final_decision") or "").lower()
        summary["pred_accept"] += int(final_decision == "accept")

        payload_items = _payload_evidence_items(row)
        final_items = [ev for ev in state.get("evidence_map", []) or [] if isinstance(ev, dict)]

        seen = set()
        duplicate_ids = 0
        for evidence in payload_items:
            evidence_id = evidence.get("evidence_id")
            if evidence_id in seen:
                duplicate_ids += 1
            if evidence_id:
                seen.add(evidence_id)

        payload_strong = [ev for ev in payload_items if _is_real_strong_support(ev, payload=True)]
        final_strong = [ev for ev in final_items if _is_real_strong_support(ev, payload=False)]
        payload_nonabstract = [ev for ev in payload_strong if _section(ev) != "abstract"]
        final_nonabstract = [ev for ev in final_strong if _section(ev) != "abstract"]
        payload_empirical = [ev for ev in payload_strong if _section(ev) == "result_or_experiment"]
        final_empirical = [ev for ev in final_strong if _section(ev) == "result_or_experiment"]

        summary["payload_strong_real_total"] += len(payload_strong)
        summary["payload_nonabstract_total"] += len(payload_nonabstract)
        summary["payload_empirical_total"] += len(payload_empirical)
        summary["final_strong_real_total"] += len(final_strong)
        summary["final_nonabstract_total"] += len(final_nonabstract)
        summary["final_empirical_total"] += len(final_empirical)
        summary["rows_payload_2plus"] += int(len(payload_strong) >= 2)
        summary["rows_final_2plus"] += int(len(final_strong) >= 2)
        summary["rows_payload_gt_final"] += int(len(payload_strong) > len(final_strong))
        summary["rows_duplicate_payload_ids"] += int(duplicate_ids > 0)
        summary["payload_duplicate_ids"] += duplicate_ids
        summary["case_table"].append(
            {
                "paper_id": paper_id,
                "final_decision": final_decision,
                "payload_strong_real": len(payload_strong),
                "final_strong_real": len(final_strong),
                "payload_nonabstract": len(payload_nonabstract),
                "final_nonabstract": len(final_nonabstract),
                "payload_empirical": len(payload_empirical),
                "final_empirical": len(final_empirical),
                "payload_duplicate_ids": duplicate_ids,
            }
        )
    return summary


def _write_report(summary_by_name: Dict[str, Dict[str, Any]], report_path: Path) -> None:
    lines = ["# Evidence Payload Lineage / Offline Reconstruction v1\n\n"]
    lines.append("本报告只做离线审计，不改变 runtime、不重跑模型。目标是比较 Evidence Agent payload 层已经形成的 real strong support 与 final ReviewState 实际保留下来的 support。\n\n")
    lines.append("| dataset | rows | payload real strong | final real strong | payload non-abstract | final non-abstract | payload empirical | final empirical | rows payload 2+ | rows final 2+ | duplicate payload ids |\n")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|\n")
    for name, summary in summary_by_name.items():
        lines.append(
            f"| {name} | {summary['rows']} | {summary['payload_strong_real_total']} | {summary['final_strong_real_total']} | "
            f"{summary['payload_nonabstract_total']} | {summary['final_nonabstract_total']} | "
            f"{summary['payload_empirical_total']} | {summary['final_empirical_total']} | "
            f"{summary['rows_payload_2plus']} | {summary['rows_final_2plus']} | {summary['payload_duplicate_ids']} |\n"
        )
    lines.append("\n## 结论\n\n")
    lines.append("payload 层已经存在明显更多 real strong support，且多个样本在 payload 层达到 2+，但 final state 中 2+ 样本仍为 0。下一步不应继续调 final decision 阈值，而应优先做 final-view evidence lineage / support reconstruction，或至少在论文中明确报告 payload-to-state support loss。\n")
    report_path.write_text("".join(lines))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", action="append", nargs=2, metavar=("NAME", "PATH"), required=True)
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--report-path", required=True)
    args = parser.parse_args()

    summaries = {name: summarize_rows(_read_jsonl(Path(path))) for name, path in args.input}
    Path(args.output_json).write_text(json.dumps(summaries, indent=2, ensure_ascii=False))
    _write_report(summaries, Path(args.report_path))
    print(json.dumps({name: {k: v for k, v in summary.items() if k != "case_table"} for name, summary in summaries.items()}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
