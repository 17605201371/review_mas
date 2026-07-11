#!/usr/bin/env python3
"""Build a deterministic, paper-balanced P34 secondary-label assignment."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Mapping, Sequence


def _load_labels(path: Path) -> List[Dict[str, Any]]:
    value = json.loads(path.read_text(encoding="utf-8"))
    rows = value.get("labels", []) if isinstance(value, dict) else []
    if not isinstance(rows, list):
        raise ValueError(f"{path} must contain a labels list")
    return [dict(item) for item in rows if isinstance(item, dict) and item.get("packet_id")]


def _hash_key(seed: str, task: str, value: str) -> str:
    return hashlib.sha256(f"{seed}|{task}|{value}".encode("utf-8")).hexdigest()


def select_paper_balanced(rows: Sequence[Mapping[str, Any]], target: int, seed: str, task: str) -> List[str]:
    by_paper: Dict[str, List[str]] = defaultdict(list)
    for item in rows:
        packet_id = str(item.get("packet_id") or "")
        paper_id = str(item.get("paper_id") or "unknown")
        if packet_id:
            by_paper[paper_id].append(packet_id)
    for paper_id in by_paper:
        by_paper[paper_id].sort(key=lambda packet_id: _hash_key(seed, task, packet_id))
    paper_order = sorted(by_paper, key=lambda paper_id: _hash_key(seed, task, paper_id))
    selected: List[str] = []
    depth = 0
    while len(selected) < min(target, sum(len(values) for values in by_paper.values())):
        added = False
        for paper_id in paper_order:
            values = by_paper[paper_id]
            if depth < len(values):
                selected.append(values[depth])
                added = True
                if len(selected) >= target:
                    break
        if not added:
            break
        depth += 1
    return selected


def build_assignment(templates: Mapping[str, Path], targets: Mapping[str, int], seed: str) -> Dict[str, Any]:
    tasks = {}
    blocking = []
    for task, path in templates.items():
        rows = _load_labels(path)
        ids = [str(item.get("packet_id") or "") for item in rows]
        duplicate_ids = sorted(packet_id for packet_id in set(ids) if ids.count(packet_id) > 1)
        target = int(targets[task])
        selected = select_paper_balanced(rows, target, seed, task)
        lookup = {str(item.get("packet_id") or ""): item for item in rows}
        paper_counts: Dict[str, int] = defaultdict(int)
        for packet_id in selected:
            paper_counts[str(lookup[packet_id].get("paper_id") or "unknown")] += 1
        task_blocking = []
        if duplicate_ids:
            task_blocking.append(f"duplicate_packet_ids:{len(duplicate_ids)}")
        if len(selected) < target:
            task_blocking.append(f"secondary_assignment_below_minimum:{len(selected)}/{target}")
        tasks[task] = {
            "template_path": str(path),
            "template_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "primary_packet_count": len(rows),
            "secondary_target_count": target,
            "secondary_packet_ids": selected,
            "secondary_packet_count": len(selected),
            "secondary_paper_count": len(paper_counts),
            "secondary_counts_by_paper": dict(sorted(paper_counts.items())),
            "duplicate_packet_ids": duplicate_ids,
            "blocking_issues": task_blocking,
        }
        blocking.extend(f"{task}:{item}" for item in task_blocking)
    payload = {"seed": seed, "tasks": tasks}
    assignment_sha256 = hashlib.sha256(
        (json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")
    ).hexdigest()
    return {
        "schema_version": "p34_annotation_assignment_v1",
        "status": "PASS" if not blocking else "BLOCKED",
        "boundary": "Deterministic paper-balanced secondary-label assignment; contains no labels",
        **payload,
        "assignment_sha256": assignment_sha256,
        "blocking_issues": blocking,
    }


def render_markdown(report: Mapping[str, Any]) -> str:
    lines = [
        "# P34 Annotation Assignment",
        "",
        f"- status: **{report['status']}**",
        f"- seed: `{report['seed']}`",
        f"- assignment_sha256: `{report['assignment_sha256']}`",
        "",
        "## Tasks",
        "",
    ]
    for task, value in report["tasks"].items():
        lines.append(
            f"- `{task}`: primary={value['primary_packet_count']}, secondary={value['secondary_packet_count']}/"
            f"{value['secondary_target_count']}, papers={value['secondary_paper_count']}"
        )
    lines.extend(["", "## Blocking Issues", ""])
    lines.extend(f"- `{item}`" for item in report["blocking_issues"]) if report["blocking_issues"] else lines.append("- none")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--positive-template", default="P34_2_JUDGE_DATASET_HARDNEG20_20260711_POSITIVE_HUMAN_AUDIT_TEMPLATE.json")
    parser.add_argument("--claim-template", default="P34_2_JUDGE_DATASET_HARDNEG20_20260711_CLAIM_HUMAN_AUDIT_TEMPLATE.json")
    parser.add_argument("--negative-template", default="P34_2_SYMMETRIC_DISCOVERY_ACTIVE_20260711_HUMAN_AUDIT_TEMPLATE.json")
    parser.add_argument("--positive-secondary", type=int, default=20)
    parser.add_argument("--claim-secondary", type=int, default=15)
    parser.add_argument("--negative-secondary", type=int, default=20)
    parser.add_argument("--seed", default="P34-20260711-frozen-secondary-v1")
    parser.add_argument("--output-json", default="P34_ANNOTATION_ASSIGNMENT_20260711.json")
    parser.add_argument("--output-md", default="P34_ANNOTATION_ASSIGNMENT_20260711.md")
    args = parser.parse_args()
    report = build_assignment(
        {
            "evidence_relation": Path(args.positive_template),
            "claim_faithfulness": Path(args.claim_template),
            "review_issue": Path(args.negative_template),
        },
        {
            "evidence_relation": args.positive_secondary,
            "claim_faithfulness": args.claim_secondary,
            "review_issue": args.negative_secondary,
        },
        args.seed,
    )
    Path(args.output_json).write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    Path(args.output_md).write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
