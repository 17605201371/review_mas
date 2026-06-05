#!/usr/bin/env python3
"""Audit negative-evidence formation and recovery policy routing from review jsonl logs."""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List


def _iter_jsonl(path: Path) -> Iterable[Dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line=line.strip()
            if line:
                yield json.loads(line)


def _turn_logs(row: Dict[str, Any]) -> List[Dict[str, Any]]:
    return list(row.get("turn_logs") or row.get("logs") or [])


def _review_state(row: Dict[str, Any]) -> Dict[str, Any]:
    return row.get("review_state") or row.get("final_state") or {}


def _is_active_flaw(item: Dict[str, Any]) -> bool:
    return str(item.get("status") or "candidate").strip().lower() in {"candidate", "confirmed"}


def _has_negative_ids(item: Dict[str, Any]) -> bool:
    return bool(item.get("negative_evidence_ids") or item.get("evidence_ids"))


def audit(path: Path) -> Dict[str, Any]:
    policy_source_counts=Counter()
    action_counts=Counter()
    flag_counts=Counter()
    recovery_counts=Counter()
    semantic_label_counts=Counter()
    negative_evidence_counts=Counter()
    rows=[]
    for row in _iter_jsonl(path):
        paper_id=str(row.get("paper_id") or row.get("id") or "")
        state=_review_state(row)
        active_flaws=[f for f in state.get("flaw_candidates",[]) or [] if isinstance(f,dict) and _is_active_flaw(f)]
        flaws_with_negative_ids=sum(1 for f in active_flaws if _has_negative_ids(f))
        for turn in _turn_logs(row):
            src=str(turn.get("policy_source") or "")
            if src:
                policy_source_counts[src]+=1
            action=str(turn.get("action_type") or turn.get("effective_action_type") or "")
            if action:
                action_counts[action]+=1
            for flag in [
                "negative_evidence_formation_required",
                "negative_evidence_binding_retry_required",
                "recovery_patch_mode_entered",
                "progression_gate_triggered",
            ]:
                if turn.get(flag):
                    flag_counts[flag]+=1
            if turn.get("phase_before_action")=="recovery" or turn.get("phase_after_action")=="recovery":
                recovery_counts["recovery_turn"]+=1
            if turn.get("recovery_patch_mode_entered") or turn.get("turn_mode")=="recovery_patch":
                recovery_counts["patch_mode_entered"]+=1
        for evidence in state.get("evidence_map",[]) or []:
            if not isinstance(evidence,dict):
                continue
            semantic=str(evidence.get("semantic_grounding_label") or "")
            if semantic:
                semantic_label_counts[semantic]+=1
            stance=str(evidence.get("stance") or "").lower()
            if stance in {"contradicts","missing","refutes","undermines"}:
                negative_evidence_counts["negative_or_missing_evidence"]+=1
                if str(evidence.get("verified_grounding_label") or "") in {"paper_grounded_exact","paper_grounded_normalized"}:
                    negative_evidence_counts["verified_quote_negative_or_missing"]+=1
                if semantic in {"semantic_negative_verified", "semantic_support_verified"}:
                    negative_evidence_counts["semantic_verified_negative_or_missing"]+=1
                if semantic == "semantic_negative_verified":
                    negative_evidence_counts["semantic_negative_verified"]+=1
        rows.append({
            "paper_id": paper_id,
            "active_flaws": len(active_flaws),
            "flaws_with_negative_ids": flaws_with_negative_ids,
        })
    return {
        "input": str(path),
        "paper_count": len(rows),
        "policy_source_counts": dict(policy_source_counts),
        "action_counts": dict(action_counts),
        "flag_counts": dict(flag_counts),
        "recovery_counts": dict(recovery_counts),
        "negative_evidence_counts": dict(negative_evidence_counts),
        "semantic_label_counts": dict(semantic_label_counts),
        "rows": rows,
    }


def write_markdown(summary: Dict[str, Any], path: Path) -> None:
    lines=["# Negative Recovery Policy Audit v1", "", f"- input: `{summary['input']}`", f"- papers: {summary['paper_count']}", ""]
    for title,key in [
        ("Policy Source Counts","policy_source_counts"),
        ("Action Counts","action_counts"),
        ("Flags","flag_counts"),
        ("Recovery Turns","recovery_counts"),
        ("Negative Evidence","negative_evidence_counts"),
        ("Semantic Labels","semantic_label_counts"),
    ]:
        lines += [f"## {title}", ""]
        items=summary.get(key,{})
        if not items:
            lines.append("- none")
        else:
            for k,v in sorted(items.items(), key=lambda kv: (-kv[1], kv[0])):
                lines.append(f"- {k}: {v}")
        lines.append("")
    lines += ["## Rows", ""]
    for row in summary.get("rows",[]):
        lines.append(f"- `{row['paper_id']}` active_flaws={row['active_flaws']} flaws_with_negative_ids={row['flaws_with_negative_ids']}")
    path.write_text("\n".join(lines)+"\n", encoding="utf-8")


def main() -> None:
    ap=argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output-json", required=True)
    ap.add_argument("--output-md", required=True)
    args=ap.parse_args()
    summary=audit(Path(args.input))
    Path(args.output_json).write_text(json.dumps(summary, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")
    write_markdown(summary, Path(args.output_md))


if __name__ == "__main__":
    main()
