#!/usr/bin/env python3
"""Evaluate a state-hygiene focused review run.

This script is intentionally lightweight and run-output-only: it does not
modify runtime behavior. It computes decision health, hygiene counts, and
final-decision blocker diagnostics for a JSONL result file.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List

import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.simulate_state_hygiene_decision import decision_blockers, hygiene_counts

DEFAULT_GOLD = Path("/reviewF/datasets/drmas_review/test.parquet")
DEFAULT_META = ROOT / "outputs/subsets/state_hygiene_4b_focus_meta.json"
DEFAULT_REPORT = ROOT / "docs/experiments/FOUR_B_STATE_HYGIENE_QUICK_RESULT.md"


def norm(value: Any) -> str:
    return str(value or "").strip().lower()


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_gold(path: Path) -> Dict[str, str]:
    return {row["id"]: row["decision"] for row in pq.read_table(path).to_pylist()}


def load_meta(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def groups_from_meta(meta: Dict[str, Any]) -> Dict[str, str]:
    groups = {}
    for group_name, ids in meta.get("groups", {}).items():
        for pid in ids:
            groups[pid] = group_name
    return groups


def selected_ids_from_meta(meta: Dict[str, Any]) -> set[str]:
    ids = meta.get("selected_ids") or []
    if not ids:
        for group_ids in meta.get("groups", {}).values():
            ids.extend(group_ids)
    return {str(pid) for pid in ids}


def infer_pred(row: Dict[str, Any]) -> str:
    value = row.get("final_decision") or row.get("predicted_decision") or row.get("decision")
    return norm(value) or "undecided"


def class_metrics(rows: List[Dict[str, Any]], gold: Dict[str, str]) -> Dict[str, Any]:
    tp = tn = fp = fn = missing = 0
    pred_ctr = Counter()
    gold_ctr = Counter()
    records = []
    for row in rows:
        pid = row.get("paper_id") or row.get("id")
        if pid not in gold:
            missing += 1
            continue
        g = norm(gold[pid])
        p = infer_pred(row)
        gold_ctr[g] += 1
        pred_ctr[p] += 1
        if g == "accept" and p == "accept":
            tp += 1
        elif g == "accept" and p != "accept":
            fn += 1
        elif g == "reject" and p == "accept":
            fp += 1
        elif g == "reject" and p != "accept":
            tn += 1
        records.append((pid, g, p))
    n = tp + tn + fp + fn
    accuracy = (tp + tn) / n if n else 0.0
    accept_precision = tp / (tp + fp) if (tp + fp) else 0.0
    accept_recall = tp / (tp + fn) if (tp + fn) else 0.0
    accept_f1 = 2 * accept_precision * accept_recall / (accept_precision + accept_recall) if (accept_precision + accept_recall) else 0.0
    reject_precision = tn / (tn + fn) if (tn + fn) else 0.0
    reject_recall = tn / (tn + fp) if (tn + fp) else 0.0
    reject_f1 = 2 * reject_precision * reject_recall / (reject_precision + reject_recall) if (reject_precision + reject_recall) else 0.0
    return {
        "n": n,
        "missing_gold": missing,
        "gold_dist": dict(gold_ctr),
        "predicted_dist": dict(pred_ctr),
        "accuracy": accuracy,
        "accept_precision": accept_precision,
        "accept_recall": accept_recall,
        "accept_f1": accept_f1,
        "reject_precision": reject_precision,
        "reject_recall": reject_recall,
        "reject_f1": reject_f1,
        "macro_f1": (accept_f1 + reject_f1) / 2,
        "confusion": {
            "gold_accept_pred_accept": tp,
            "gold_accept_pred_nonaccept": fn,
            "gold_reject_pred_accept": fp,
            "gold_reject_pred_nonaccept": tn,
        },
        "records": records,
    }


def aggregate_hygiene(rows: List[Dict[str, Any]]) -> Dict[str, int]:
    total = Counter()
    for row in rows:
        for key, value in hygiene_counts(row.get("review_state", {})).items():
            total[key] += int(value)
    return dict(total)


def aggregate_blockers(rows: List[Dict[str, Any]]) -> Dict[str, int]:
    total = Counter()
    per_sample = {}
    for row in rows:
        pid = row.get("paper_id") or row.get("id")
        diag = decision_blockers(row.get("review_state", {}))
        per_sample[pid] = diag
        for blocker in diag.get("blockers", []):
            total[blocker] += 1
    return {"totals": dict(total), "per_sample": per_sample}


def group_metrics(rows: List[Dict[str, Any]], gold: Dict[str, str], groups: Dict[str, str]) -> Dict[str, Any]:
    by_group = defaultdict(list)
    for row in rows:
        pid = row.get("paper_id") or row.get("id")
        by_group[groups.get(pid, "ungrouped")].append(row)
    return {name: class_metrics(items, gold) for name, items in sorted(by_group.items())}


def write_report(payload: Dict[str, Any], path: Path) -> None:
    m = payload["decision_metrics"]
    title = payload.get("report_title") or "State Hygiene Run Result"
    lines = [
        f"# {title}",
        "",
        f"**输入结果**：`{payload['result_path']}`",
        f"**样本数**：{m['n']}",
        "",
        "## 1. Decision Health",
        "",
        "| metric | value |",
        "|---|---:|",
        f"| accuracy | {m['accuracy']:.4f} |",
        f"| macro-F1 | {m['macro_f1']:.4f} |",
        f"| accept precision | {m['accept_precision']:.4f} |",
        f"| accept recall | {m['accept_recall']:.4f} |",
        f"| reject precision | {m['reject_precision']:.4f} |",
        f"| reject recall | {m['reject_recall']:.4f} |",
        f"| predicted accept | {m['predicted_dist'].get('accept', 0)} |",
        f"| predicted reject/nonaccept | {m['n'] - m['predicted_dist'].get('accept', 0)} |",
        "",
        "## 2. Confusion Matrix",
        "",
        "| item | count |",
        "|---|---:|",
    ]
    for key, value in m["confusion"].items():
        lines.append(f"| `{key}` | {value} |")
    lines += ["", "## 3. Blocker Distribution", "", "| blocker | samples |", "|---|---:|"]
    for key, value in sorted(payload["blockers"]["totals"].items(), key=lambda kv: -kv[1]):
        lines.append(f"| `{key}` | {value} |")
    lines += ["", "## 4. Hygiene Totals", "", "| metric | total |", "|---|---:|"]
    for key, value in sorted(payload["hygiene_totals"].items()):
        lines.append(f"| `{key}` | {value} |")
    lines += ["", "## 5. Group Metrics", ""]
    for group, gm in payload["group_metrics"].items():
        lines += [
            f"### {group}",
            "",
            f"- **n**: {gm['n']}",
            f"- **accept recall**: {gm['accept_recall']:.4f}",
            f"- **reject recall**: {gm['reject_recall']:.4f}",
            f"- **predicted_dist**: `{gm['predicted_dist']}`",
            "",
        ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate state hygiene focused run output.")
    parser.add_argument("--results-path", required=True)
    parser.add_argument("--gold-path", default=str(DEFAULT_GOLD))
    parser.add_argument("--meta-path", default=str(DEFAULT_META))
    parser.add_argument("--output-json", default="")
    parser.add_argument("--report-path", default=str(DEFAULT_REPORT))
    parser.add_argument("--selected-only", action="store_true", help="Filter results to selected_ids/groups from meta before scoring.")
    parser.add_argument("--report-title", default="State Hygiene Run Result")
    args = parser.parse_args()

    result_path = Path(args.results_path)
    rows = load_jsonl(result_path)
    meta = load_meta(Path(args.meta_path))
    if args.selected_only:
        selected = selected_ids_from_meta(meta)
        rows = [row for row in rows if str(row.get("paper_id") or row.get("id")) in selected]
    gold = load_gold(Path(args.gold_path))
    groups = groups_from_meta(meta)
    payload = {
        "result_path": str(result_path),
        "gold_path": str(Path(args.gold_path)),
        "meta_path": str(Path(args.meta_path)),
        "selected_only": bool(args.selected_only),
        "report_title": args.report_title,
        "decision_metrics": class_metrics(rows, gold),
        "group_metrics": group_metrics(rows, gold, groups),
        "hygiene_totals": aggregate_hygiene(rows),
        "blockers": aggregate_blockers(rows),
    }

    if args.output_json:
        Path(args.output_json).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    write_report(payload, Path(args.report_path))

    m = payload["decision_metrics"]
    print(json.dumps({
        "n": m["n"],
        "accuracy": m["accuracy"],
        "macro_f1": m["macro_f1"],
        "accept_recall": m["accept_recall"],
        "reject_recall": m["reject_recall"],
        "predicted_dist": m["predicted_dist"],
        "blockers": payload["blockers"]["totals"],
        "report_path": args.report_path,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
