#!/usr/bin/env python3
"""Build the fixed 4B state-hygiene focus subset.

The subset is designed for fast 4B iteration after the offline hygiene simulation:
  - all 9 gold-accept samples from full test
  - 5 oracle false-accept reject controls
  - 2 stable reject controls

It writes a parquet subset plus a JSON meta file under outputs/subsets/.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

import pyarrow as pa
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[1]
DATASET_PATH = Path("/reviewF/datasets/drmas_review/test.parquet")
SIM_RESULT_PATH = ROOT / "FULLTEST_HYGIENE_SIMULATION_RESULTS.json"
OUTPUT_SUBSET_PATH = ROOT / "outputs/subsets/state_hygiene_4b_focus.parquet"
OUTPUT_META_PATH = ROOT / "outputs/subsets/state_hygiene_4b_focus_meta.json"

GOLD_ACCEPT_IDS = [
    "hj323oR3rw",
    "QAAsnSRwgu",
    "X41c4uB4k0",
    "gzqrANCF4g",
    "KI9NqjLVDT",
    "1HCN4pjTb4",
    "LebzzClHYw",
    "BXY6fe7q31",
    "jVEoydFOl9",
]

ORACLE_FALSE_ACCEPT_REJECT_IDS = [
    "NnExMNiTHw",
    "fGXyvmWpw6",
    "TPAj63ax4Y",
    "aTBE70xiFw",
    "kam84eEmub",
]

STABLE_REJECT_CONTROL_IDS = [
    "GE6iywJtsV",
    "KOUAayk5Kx",
]

SELECTED_IDS = GOLD_ACCEPT_IDS + ORACLE_FALSE_ACCEPT_REJECT_IDS + STABLE_REJECT_CONTROL_IDS


def load_sim_case_map() -> Dict[str, Dict]:
    if not SIM_RESULT_PATH.exists():
        return {}
    payload = json.loads(SIM_RESULT_PATH.read_text(encoding="utf-8"))
    return {row["paper_id"]: row for row in payload.get("case_rows", [])}


def main() -> None:
    rows = pq.read_table(DATASET_PATH).to_pylist()
    by_id = {row["id"]: row for row in rows}
    missing = [pid for pid in SELECTED_IDS if pid not in by_id]
    if missing:
        raise SystemExit(f"Missing ids in dataset: {missing}")

    selected_rows: List[Dict] = []
    case_map = load_sim_case_map()
    for order, pid in enumerate(SELECTED_IDS):
        row = dict(by_id[pid])
        row["state_hygiene_4b_group"] = (
            "gold_accept" if pid in GOLD_ACCEPT_IDS
            else "oracle_false_accept_reject" if pid in ORACLE_FALSE_ACCEPT_REJECT_IDS
            else "stable_reject_control"
        )
        row["state_hygiene_4b_order"] = order
        selected_rows.append(row)

    OUTPUT_SUBSET_PATH.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(pa.Table.from_pylist(selected_rows), OUTPUT_SUBSET_PATH)

    meta = {
        "dataset_path": str(DATASET_PATH),
        "simulation_result_path": str(SIM_RESULT_PATH),
        "output_subset_path": str(OUTPUT_SUBSET_PATH),
        "selected_count": len(selected_rows),
        "selected_ids": SELECTED_IDS,
        "groups": {
            "gold_accept": GOLD_ACCEPT_IDS,
            "oracle_false_accept_reject": ORACLE_FALSE_ACCEPT_REJECT_IDS,
            "stable_reject_control": STABLE_REJECT_CONTROL_IDS,
        },
        "case_table": {pid: case_map.get(pid, {}) for pid in SELECTED_IDS},
        "recommended_4b_command": [
            "conda", "run", "-n", "DrMAS-qwen35", "python", "-u", "-m", "agent_system.inference.review_runner",
            "--dataset-path", str(OUTPUT_SUBSET_PATH),
            "--model-path", "/reviewF/datasets/Qwen3___5-4B",
            "--temperature", "0.2",
            "--top-p", "0.95",
            "--mode", "s4",
            "--max-turns", "8",
            "--max-workers-per-turn", "2",
            "--manager-batch-size", "1",
            "--gpu-memory-utilization", "0.60",
            "--max-num-seqs", "64",
            "--max-model-len", "3072",
            "--max-tokens", "640",
            "--output-path", "outputs/results_main/review_infer/p25_1_state_hygiene_4b_focus.jsonl",
        ],
    }
    OUTPUT_META_PATH.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps({
        "output_subset_path": str(OUTPUT_SUBSET_PATH),
        "output_meta_path": str(OUTPUT_META_PATH),
        "selected_count": len(selected_rows),
        "selected_ids": SELECTED_IDS,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
