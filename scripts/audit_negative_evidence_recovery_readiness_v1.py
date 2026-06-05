#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List

from agent_system.environments.env_package.review.state import (
    _flaw_valid_negative_evidence_ids,
    _is_grounded_paper_negative_evidence_record,
    _is_paper_negative_evidence_record,
)

ACTIVE_FLAW_STATUSES = {"candidate", "confirmed"}


def _rows(path: Path) -> Iterable[Dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                yield json.loads(line)


def _paper_id(row: Dict[str, Any]) -> str:
    return str(row.get("paper_id") or row.get("id") or "unknown")


def _evidence_lookup(state: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    return {
        str(item.get("evidence_id") or "").strip(): item
        for item in state.get("evidence_map", []) or []
        if isinstance(item, dict) and str(item.get("evidence_id") or "").strip()
    }


def _active_flaws(state: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [
        flaw for flaw in state.get("flaw_candidates", []) or []
        if isinstance(flaw, dict)
        and str(flaw.get("flaw_id") or "").strip()
        and str(flaw.get("status") or "candidate").strip().lower() in ACTIVE_FLAW_STATUSES
    ]


def analyze(path: Path) -> Dict[str, Any]:
    rows = list(_rows(path))
    metrics = Counter()
    semantic_counts = Counter()
    cases: List[Dict[str, Any]] = []
    for row in rows:
        state = row.get("review_state") or {}
        evidence_lookup = _evidence_lookup(state)
        active_flaws = _active_flaws(state)
        paper_id = _paper_id(row)
        negative_evidence_ids: List[str] = []
        grounded_negative_ids: List[str] = []
        for item in state.get("evidence_map", []) or []:
            if not isinstance(item, dict):
                continue
            if _is_paper_negative_evidence_record(item):
                evidence_id = str(item.get("evidence_id") or "").strip()
                if evidence_id:
                    negative_evidence_ids.append(evidence_id)
                semantic_counts[str(item.get("semantic_grounding_label") or "semantic_unjudged").strip() or "semantic_unjudged"] += 1
                if _is_grounded_paper_negative_evidence_record(item, state) and evidence_id:
                    grounded_negative_ids.append(evidence_id)
        metrics["papers"] += 1
        metrics["evidence_total"] += len(state.get("evidence_map", []) or [])
        metrics["negative_evidence_total"] += len(negative_evidence_ids)
        metrics["grounded_negative_evidence_total"] += len(grounded_negative_ids)
        metrics["active_flaw_total"] += len(active_flaws)
        unverified_flaws: List[str] = []
        formation_ready: List[str] = []
        no_target: List[str] = []
        for flaw in active_flaws:
            flaw_id = str(flaw.get("flaw_id") or "").strip()
            valid_negative_ids = _flaw_valid_negative_evidence_ids(flaw, state)
            if valid_negative_ids:
                metrics["active_flaw_with_grounded_negative"] += 1
                continue
            metrics["active_flaw_without_grounded_negative"] += 1
            unverified_flaws.append(flaw_id)
            related_claim_ids = [str(item).strip() for item in flaw.get("related_claim_ids") or [] if str(item).strip()]
            evidence_ids = [str(item).strip() for item in flaw.get("negative_evidence_ids") or flaw.get("evidence_ids") or [] if str(item).strip()]
            for evidence_id in evidence_ids:
                claim_id = str((evidence_lookup.get(evidence_id) or {}).get("claim_id") or "").strip()
                if claim_id and claim_id not in related_claim_ids:
                    related_claim_ids.append(claim_id)
            if related_claim_ids or evidence_ids:
                metrics["negative_evidence_formation_ready_flaw"] += 1
                formation_ready.append(flaw_id)
            else:
                metrics["negative_evidence_no_target_flaw"] += 1
                no_target.append(flaw_id)
        if unverified_flaws or negative_evidence_ids:
            cases.append({
                "paper_id": paper_id,
                "active_flaw_count": len(active_flaws),
                "unverified_flaw_ids": unverified_flaws,
                "formation_ready_flaw_ids": formation_ready,
                "no_target_flaw_ids": no_target,
                "negative_evidence_ids": negative_evidence_ids[:8],
                "grounded_negative_evidence_ids": grounded_negative_ids[:8],
            })
    result = {
        "input": str(path),
        "metrics": dict(metrics),
        "semantic_negative_evidence_distribution": dict(semantic_counts),
        "cases": cases,
    }
    return result


def write_markdown(result: Dict[str, Any], output: Path) -> None:
    m = result["metrics"]
    lines = [
        "# Negative Evidence + Recovery Readiness Audit v1",
        "",
        "本审计不跑模型，只检查现有 ReviewState 中 active flaw、负证据与 recovery target 是否已形成可安全修复的闭环。",
        "",
        "## Summary",
        "",
        f"- input: `{result['input']}`",
        f"- papers: {m.get('papers', 0)}",
        f"- active_flaw_total: {m.get('active_flaw_total', 0)}",
        f"- active_flaw_with_grounded_negative: {m.get('active_flaw_with_grounded_negative', 0)}",
        f"- active_flaw_without_grounded_negative: {m.get('active_flaw_without_grounded_negative', 0)}",
        f"- negative_evidence_total: {m.get('negative_evidence_total', 0)}",
        f"- grounded_negative_evidence_total: {m.get('grounded_negative_evidence_total', 0)}",
        f"- negative_evidence_formation_ready_flaw: {m.get('negative_evidence_formation_ready_flaw', 0)}",
        f"- negative_evidence_no_target_flaw: {m.get('negative_evidence_no_target_flaw', 0)}",
        "",
        "## Semantic Distribution For Negative Evidence",
        "",
    ]
    for key, value in sorted(result.get("semantic_negative_evidence_distribution", {}).items()):
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Cases", ""])
    for case in result.get("cases", [])[:60]:
        lines.append(
            f"- `{case['paper_id']}`: active={case['active_flaw_count']}, "
            f"unverified={case['unverified_flaw_ids']}, formation_ready={case['formation_ready_flaw_ids']}, "
            f"no_target={case['no_target_flaw_ids']}, grounded_negative={case['grounded_negative_evidence_ids']}"
        )
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--output-md", required=True)
    args = parser.parse_args()
    result = analyze(Path(args.input))
    Path(args.output_json).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(result, Path(args.output_md))


if __name__ == "__main__":
    main()
