from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List

NARRATIVE_LIST_FIELDS = (
    "new_items",
    "downgraded_items",
    "retracted_items",
    "conflicts_detected",
    "reason_for_revision",
)


def load_rows(path: Path) -> List[Dict[str, Any]]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def flatten_counts(rows: List[Dict[str, Any]], key: str) -> Counter:
    counter: Counter = Counter()
    for row in rows:
        for log in row.get("turn_logs", []) or []:
            value = log.get(key)
            if value:
                counter[str(value)] += 1
    return counter


def flatten_list_counts(rows: List[Dict[str, Any]], key: str) -> Counter:
    counter: Counter = Counter()
    for row in rows:
        for log in row.get("turn_logs", []) or []:
            for value in log.get(key, []) or []:
                if value:
                    counter[str(value)] += 1
    return counter


def summarize_mode(label: str, rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    def avg(values: List[float]) -> float:
        return round(sum(values) / len(values), 4) if values else 0.0

    claim_counts = [len((row.get("review_state") or {}).get("claims", [])) for row in rows]
    evidence_counts = [len((row.get("review_state") or {}).get("evidence_map", [])) for row in rows]
    flaw_counts = [len((row.get("review_state") or {}).get("flaw_candidates", [])) for row in rows]
    turn_counts = [len(row.get("turn_logs", [])) for row in rows]
    rewards = [float(row.get("reward", 0.0)) for row in rows]
    narrative_turns = {
        f"{field}_turns": sum(1 for row in rows for log in row.get("turn_logs", []) or [] if log.get(field))
        for field in NARRATIVE_LIST_FIELDS
    }
    return {
        "label": label,
        "rows": len(rows),
        "avg_reward": avg(rewards),
        "avg_turns": avg(turn_counts),
        "avg_claims": avg(claim_counts),
        "avg_evidence": avg(evidence_counts),
        "avg_flaws": avg(flaw_counts),
        "nonempty_claim_rows": sum(1 for x in claim_counts if x > 0),
        "nonempty_evidence_rows": sum(1 for x in evidence_counts if x > 0),
        "nonempty_flaw_rows": sum(1 for x in flaw_counts if x > 0),
        "effective_action_type_counts": dict(flatten_counts(rows, "effective_action_type")),
        "policy_source_counts": dict(flatten_counts(rows, "policy_source")),
        **narrative_turns,
        "narrative_value_counts": {
            field: dict(flatten_list_counts(rows, field)) for field in NARRATIVE_LIST_FIELDS
        },
    }


def build_table(summaries: List[Dict[str, Any]]) -> str:
    headers = [
        "mode", "rows", "avg_reward", "avg_turns", "avg_claims", "avg_evidence", "avg_flaws",
        "claim_rows", "evidence_rows", "flaw_rows", "new_turns", "conflict_turns", "revision_turns"
    ]
    lines = ["\t".join(headers)]
    for item in summaries:
        lines.append("\t".join([
            item["label"],
            str(item["rows"]),
            f"{item['avg_reward']:.4f}",
            f"{item['avg_turns']:.2f}",
            f"{item['avg_claims']:.2f}",
            f"{item['avg_evidence']:.2f}",
            f"{item['avg_flaws']:.2f}",
            str(item["nonempty_claim_rows"]),
            str(item["nonempty_evidence_rows"]),
            str(item["nonempty_flaw_rows"]),
            str(item["new_items_turns"]),
            str(item["conflicts_detected_turns"]),
            str(item["reason_for_revision_turns"]),
        ]))
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare review mode outputs.")
    parser.add_argument("--input", nargs=2, action="append", metavar=("LABEL", "PATH"), required=True)
    parser.add_argument("--output", default="", help="Optional JSON output path.")
    args = parser.parse_args()

    summaries = []
    for label, raw_path in args.input:
        path = Path(raw_path)
        rows = load_rows(path)
        summaries.append(summarize_mode(label, rows))

    payload = {
        "table": build_table(summaries),
        "modes": {item["label"]: item for item in summaries},
    }
    print(payload["table"])
    print(json.dumps(payload["modes"], indent=2, ensure_ascii=False))
    if args.output:
        Path(args.output).write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
