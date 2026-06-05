import argparse
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

import pyarrow as pa
import pyarrow.parquet as pq

DEFAULT_SUBSET_PATH = "outputs/review_infer/p24_1_hardest_subset.parquet"
DEFAULT_META_PATH = "outputs/review_infer/p24_1_hardest_subset_meta.json"
DEFAULT_OUTPUT_PATH_4B = "outputs/review_infer/p24_1_4b_regression.jsonl"
DEFAULT_OUTPUT_PATH_9B = "outputs/review_infer/p24_1_9b_regression.jsonl"
DEFAULT_THRESHOLD = 5
DEFAULT_TARGET_IDS = ["X41c4uB4k0", "hj323oR3rw"]


def _load_jsonl(path: Path) -> List[Dict]:
    if not path.exists():
        raise FileNotFoundError(f"Results file not found: {path}")
    return [json.loads(line) for line in path.read_text("utf-8").splitlines() if line.strip()]


def _load_parquet_rows(path: Path) -> List[Dict]:
    if not path.exists():
        raise FileNotFoundError(f"Dataset file not found: {path}")
    return pq.read_table(path).to_pylist()


def _row_paper_id(row: Dict) -> str:
    env = row.get("env_kwargs")
    if isinstance(env, str):
        try:
            env = json.loads(env)
        except json.JSONDecodeError:
            env = {}
    if isinstance(env, dict) and env.get("paper_id"):
        return str(env.get("paper_id"))
    return str(row.get("paper_id") or row.get("id") or "")


def _sample_recovery_stats(row: Dict) -> Dict[str, int]:
    turns = list(row.get("turn_logs", []) or [])
    attempted = sum(1 for t in turns if t.get("recovery_attempted"))
    validated = sum(1 for t in turns if t.get("recovery_validated"))
    committed = sum(1 for t in turns if t.get("recovery_committed"))
    return {"attempted": attempted, "validated": validated, "committed": committed}


def select_high_conflict_ids(
    result_rows: Sequence[Dict],
    threshold: int,
    forced_ids: Sequence[str],
    extra_hard_cases: int = 4,
) -> Tuple[List[str], Dict[str, int], Dict[str, Dict[str, int]], List[str], List[str], List[str]]:
    selected: List[str] = []
    selected_from_threshold: List[str] = []
    forced_and_selected: List[str] = []
    forced_but_missing: List[str] = []
    conflict_map: Dict[str, int] = {}
    recovery_stats: Dict[str, Dict[str, int]] = {}
    seen_ids = set()

    for row in result_rows:
        paper_id = str(row.get("paper_id") or "")
        if not paper_id:
            continue
        seen_ids.add(paper_id)
        conflict_count = len((row.get("review_state") or {}).get("conflict_notes", []))
        conflict_map[paper_id] = conflict_count
        recovery_stats[paper_id] = _sample_recovery_stats(row)
        if conflict_count >= threshold and paper_id not in selected:
            selected.append(paper_id)
            selected_from_threshold.append(paper_id)

    low_commit_candidates = sorted(
        [
            paper_id for paper_id, stats in recovery_stats.items()
            if stats.get("attempted", 0) > 0 and stats.get("committed", 0) < stats.get("attempted", 0)
        ],
        key=lambda pid: (
            -(recovery_stats[pid].get("attempted", 0) - recovery_stats[pid].get("committed", 0)),
            -recovery_stats[pid].get("attempted", 0),
            -conflict_map.get(pid, 0),
            pid,
        ),
    )
    for paper_id in low_commit_candidates[:extra_hard_cases]:
        if paper_id not in selected:
            selected.append(paper_id)

    for paper_id in forced_ids:
        if paper_id in seen_ids:
            if paper_id not in selected:
                selected.append(paper_id)
            forced_and_selected.append(paper_id)
        else:
            forced_but_missing.append(paper_id)

    return selected, conflict_map, recovery_stats, selected_from_threshold, forced_and_selected, forced_but_missing


def build_subset_rows(dataset_rows: Sequence[Dict], paper_ids: Sequence[str]) -> Tuple[List[Dict], List[str]]:
    wanted = list(dict.fromkeys([paper_id for paper_id in paper_ids if paper_id]))
    id_to_row = {}
    for row in dataset_rows:
        paper_id = _row_paper_id(row)
        if paper_id and paper_id not in id_to_row:
            id_to_row[paper_id] = row
    subset_rows = [id_to_row[paper_id] for paper_id in wanted if paper_id in id_to_row]
    missing = [paper_id for paper_id in wanted if paper_id not in id_to_row]
    return subset_rows, missing


def write_subset(rows: Sequence[Dict], subset_path: Path) -> None:
    subset_path.parent.mkdir(parents=True, exist_ok=True)
    table = pa.Table.from_pylist(list(rows))
    pq.write_table(table, subset_path)


def write_meta(meta: Dict, meta_path: Path) -> None:
    meta_path.parent.mkdir(parents=True, exist_ok=True)
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), "utf-8")


def extract_high_conflict_subset(results_path: Path, dataset_path: Path, subset_path: Path, meta_path: Path, threshold: int, forced_ids: Sequence[str], extra_hard_cases: int = 4) -> Dict:
    result_rows = _load_jsonl(results_path)
    dataset_rows = _load_parquet_rows(dataset_path)
    selected_ids, conflict_map, recovery_stats, selected_from_threshold, forced_and_selected, forced_but_missing = select_high_conflict_ids(
        result_rows,
        threshold=threshold,
        forced_ids=forced_ids,
        extra_hard_cases=extra_hard_cases,
    )
    subset_rows, missing_ids = build_subset_rows(dataset_rows, selected_ids)

    write_subset(subset_rows, subset_path)
    meta = {
        "results_path": str(results_path.resolve()),
        "dataset_path": str(dataset_path.resolve()),
        "subset_path": str(subset_path.resolve()),
        "threshold": threshold,
        "forced_ids": list(forced_ids),
        "selected_ids": selected_ids,
        "selected_from_threshold": selected_from_threshold,
        "forced_and_selected": forced_and_selected,
        "forced_but_missing": forced_but_missing,
        "selected_conflict_counts": {paper_id: conflict_map.get(paper_id, 0) for paper_id in selected_ids},
        "selected_recovery_stats": {paper_id: recovery_stats.get(paper_id, {}) for paper_id in selected_ids},
        "selected_count": len(selected_ids),
        "materialized_count": len(subset_rows),
        "missing_from_dataset": missing_ids,
    }
    write_meta(meta, meta_path)
    print(json.dumps(meta, ensure_ascii=False, indent=2))
    return meta


def build_runner_cmd(model_path: str, dataset_path: Path, output_path: str, manager_batch_size: int, max_turns: int, max_workers_per_turn: int, gpu_memory_utilization: float, max_num_seqs: int, max_model_len: int, temperature: float, top_p: float, max_tokens: int) -> List[str]:
    return [
        "/opt/conda/envs/DrMAS-qwen35/bin/python",
        "-u",
        "-m",
        "agent_system.inference.review_runner",
        "--dataset-path",
        str(dataset_path),
        "--model-path",
        model_path,
        "--temperature",
        str(temperature),
        "--top-p",
        str(top_p),
        "--mode",
        "s4",
        "--max-turns",
        str(max_turns),
        "--max-workers-per-turn",
        str(max_workers_per_turn),
        "--manager-batch-size",
        str(manager_batch_size),
        "--gpu-memory-utilization",
        str(gpu_memory_utilization),
        "--max-num-seqs",
        str(max_num_seqs),
        "--max-model-len",
        str(max_model_len),
        "--max-tokens",
        str(max_tokens),
        "--output-path",
        output_path,
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description="Run high-conflict recovery regression with the bounded recovery patch pipeline.")
    parser.add_argument("--results-path", required=True)
    parser.add_argument("--dataset-path", required=True)
    parser.add_argument("--subset-path", default=DEFAULT_SUBSET_PATH)
    parser.add_argument("--meta-path", default=DEFAULT_META_PATH)
    parser.add_argument("--threshold", type=int, default=DEFAULT_THRESHOLD)
    parser.add_argument("--target-id", action="append", default=[])
    parser.add_argument("--extract-only", action="store_true")
    parser.add_argument("--run-9b", action="store_true", help="Also run the frozen 9B comparison after the 4B run. Off by default.")
    parser.add_argument("--skip-run", action="store_true")
    parser.add_argument("--manager-batch-size", type=int, default=1)
    parser.add_argument("--max-turns", type=int, default=15)
    parser.add_argument("--max-workers-per-turn", type=int, default=3)
    parser.add_argument("--gpu-memory-utilization", type=float, default=0.55)
    parser.add_argument("--max-num-seqs", type=int, default=64)
    parser.add_argument("--max-model-len", type=int, default=3072)
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--top-p", type=float, default=0.95)
    parser.add_argument("--max-tokens", type=int, default=640)
    parser.add_argument("--output-path-4b", default=DEFAULT_OUTPUT_PATH_4B)
    parser.add_argument("--output-path-9b", default=DEFAULT_OUTPUT_PATH_9B)
    parser.add_argument("--extra-hard-cases", type=int, default=4)
    args = parser.parse_args()

    forced_ids = list(dict.fromkeys(DEFAULT_TARGET_IDS + list(args.target_id or [])))
    meta = extract_high_conflict_subset(
        results_path=Path(args.results_path),
        dataset_path=Path(args.dataset_path),
        subset_path=Path(args.subset_path),
        meta_path=Path(args.meta_path),
        threshold=args.threshold,
        forced_ids=forced_ids,
        extra_hard_cases=args.extra_hard_cases,
    )

    if args.extract_only:
        return 0

    if meta["materialized_count"] == 0:
        print("No rows were materialized into the recovery subset; aborting run.")
        return 1

    if args.skip_run:
        return 0

    cmd_4b = build_runner_cmd(
        model_path="/reviewF/datasets/Qwen3___5-4B",
        dataset_path=Path(args.subset_path),
        output_path=args.output_path_4b,
        manager_batch_size=args.manager_batch_size,
        max_turns=args.max_turns,
        max_workers_per_turn=args.max_workers_per_turn,
        gpu_memory_utilization=args.gpu_memory_utilization,
        max_num_seqs=args.max_num_seqs,
        max_model_len=args.max_model_len,
        temperature=args.temperature,
        top_p=args.top_p,
        max_tokens=args.max_tokens,
    )
    print("Running 4B recovery regression:")
    print(" ".join(cmd_4b))
    subprocess.run(cmd_4b, check=True)

    if args.run_9b:
        cmd_9b = build_runner_cmd(
            model_path="/reviewF/datasets/Qwen3___5-9B",
            dataset_path=Path(args.subset_path),
            output_path=args.output_path_9b,
            manager_batch_size=args.manager_batch_size,
            max_turns=args.max_turns,
            max_workers_per_turn=args.max_workers_per_turn,
            gpu_memory_utilization=0.90,
            max_num_seqs=64,
            max_model_len=args.max_model_len,
            temperature=args.temperature,
            top_p=args.top_p,
            max_tokens=args.max_tokens,
        )
        print("Running 9B recovery regression:")
        print(" ".join(cmd_9b))
        subprocess.run(cmd_9b, check=True)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
