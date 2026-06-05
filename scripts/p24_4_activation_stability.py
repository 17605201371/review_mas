from __future__ import annotations

import argparse
import json
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Sequence

import pyarrow as pa
import pyarrow.parquet as pq

RECOVERY_ACTION_TYPES = {"challenge_previous_hypothesis", "request_evidence_recheck"}
DEFAULT_RESULT_PATHS = [
    "outputs/review_infer/p24_2_4b_regression.jsonl",
    "outputs/review_infer/p24_1_4b_regression.jsonl",
    "outputs/review_infer/p24_4b_regression.jsonl",
    "outputs/review_infer/p24_9b_regression.jsonl",
    "outputs/review_infer/p23_9b_verification.jsonl",
    "outputs/review_infer/p22_test_verification_qwen35_4b_v3.jsonl",
    "outputs/review_infer/p2_final_s4_batch100.jsonl",
    "outputs/review_infer/pilot_s4_batch39.jsonl",
]
DEFAULT_DATASET_PATHS = [
    "outputs/review_infer/pilot2_batch100.parquet",
    "outputs/review_infer/pilot_batch39.parquet",
]
DEFAULT_SENTINEL_IDS = ["X41c4uB4k0", "hj323oR3rw"]
DEFAULT_SUBSET_PATH = "outputs/review_infer/p24_4_recovery_emission_subset.parquet"
DEFAULT_META_PATH = "outputs/review_infer/p24_4_recovery_emission_subset_meta.json"
DEFAULT_ANALYSIS_PATH = "outputs/review_infer/p24_4_recovery_emission_selection.json"
DEFAULT_OUTPUT_PATH_4B = "outputs/review_infer/p24_4_4b_regression.jsonl"


def _load_jsonl(path: Path) -> List[Dict[str, Any]]:
    return [json.loads(line) for line in path.read_text("utf-8").splitlines() if line.strip()]


def _load_parquet_rows(path: Path) -> List[Dict[str, Any]]:
    return pq.read_table(path).to_pylist()


def _row_paper_id(row: Dict[str, Any]) -> str:
    env = row.get("env_kwargs")
    if isinstance(env, str):
        try:
            env = json.loads(env)
        except json.JSONDecodeError:
            env = {}
    if isinstance(env, dict) and env.get("paper_id"):
        return str(env.get("paper_id"))
    return str(row.get("paper_id") or row.get("id") or "")


def _normalized_source(value: Any) -> str:
    text = str(value or "none").strip().lower()
    return text or "none"


def _turn_conflict_detected(turn: Dict[str, Any]) -> bool:
    return bool(turn.get("conflicts_detected") or turn.get("conflict_summary") or turn.get("conflict_events"))


def _turn_recovery_triggered(turn: Dict[str, Any]) -> bool:
    return bool(
        turn.get("recovery_patch_mode_entered")
        or turn.get("recovery_emission_expected")
        or turn.get("recovery_attempted")
        or str(turn.get("action_type") or "") in RECOVERY_ACTION_TYPES
        or str(turn.get("effective_action_type") or "") in RECOVERY_ACTION_TYPES
        or str(turn.get("recovery_blocked_by") or "").strip()
        or str(turn.get("emission_failure_code") or "").strip()
    )


def _turn_patch_mode_entered(turn: Dict[str, Any]) -> bool:
    if "recovery_patch_mode_entered" in turn:
        return bool(turn.get("recovery_patch_mode_entered"))
    return str(turn.get("turn_mode") or "") == "recovery_patch"


def _turn_patch_emitted(turn: Dict[str, Any]) -> bool:
    if "recovery_emitted" in turn:
        return bool(turn.get("recovery_emitted"))
    if str(turn.get("recovery_patch_source") or "none").strip().lower() != "none":
        return True
    if turn.get("recovery_attempted") and turn.get("recovery_target_id"):
        return True
    for worker in turn.get("worker_payloads") or []:
        payload = worker.get("payload") or {}
        if payload.get("action") == "apply_recovery_patch":
            return True
    return False


def _row_metrics(row: Dict[str, Any], source_name: str) -> Dict[str, Any]:
    turns = list(row.get("turn_logs", []) or [])
    action_counts: Counter[str] = Counter()
    effective_counts: Counter[str] = Counter()
    policy_counts: Counter[str] = Counter()
    turn_mode_counts: Counter[str] = Counter()
    patch_source_counts: Counter[str] = Counter()
    emission_failure_counts: Counter[str] = Counter()
    failure_code_counts: Counter[str] = Counter()
    joint_semantics: Counter[str] = Counter()

    conflict_detected = 0
    recovery_triggered = 0
    patch_mode_entered = 0
    patch_emitted = 0
    patch_validated = 0
    patch_committed = 0
    model_generated_commits = 0
    salvaged_commits = 0

    for turn in turns:
        action = str(turn.get("action_type") or "")
        effective = str(turn.get("effective_action_type") or "")
        policy = str(turn.get("policy_source") or "")
        turn_mode = str(turn.get("turn_mode") or "normal_evidence")
        patch_source = _normalized_source(turn.get("recovery_patch_source"))
        emission_failure = str(turn.get("emission_failure_code") or "").strip()
        recovery_failure = str(turn.get("recovery_failure_code") or "").strip()

        if action:
            action_counts[action] += 1
        if effective:
            effective_counts[effective] += 1
        if policy:
            policy_counts[policy] += 1
        if turn_mode:
            turn_mode_counts[turn_mode] += 1
        if patch_source != "none":
            patch_source_counts[patch_source] += 1
        if emission_failure:
            emission_failure_counts[emission_failure] += 1
        if recovery_failure:
            failure_code_counts[recovery_failure] += 1

        if _turn_conflict_detected(turn):
            conflict_detected += 1
        if _turn_recovery_triggered(turn):
            recovery_triggered += 1
        if _turn_patch_mode_entered(turn):
            patch_mode_entered += 1
        if _turn_patch_emitted(turn):
            patch_emitted += 1
        if turn.get("recovery_validated"):
            patch_validated += 1
        if turn.get("recovery_committed"):
            patch_committed += 1
            if patch_source == "model_generated":
                model_generated_commits += 1
            elif patch_source == "salvaged":
                salvaged_commits += 1
        if _turn_recovery_triggered(turn) or _turn_patch_mode_entered(turn):
            joint_semantics[f"{action} -> {effective} | {turn_mode} | {policy} | {patch_source}"] += 1

    return {
        "paper_id": str(row.get("paper_id") or ""),
        "source_name": source_name,
        "reward": float(row.get("reward") or 0.0),
        "decision_correct": bool(row.get("decision_correct")),
        "conflict_detected_count": conflict_detected,
        "recovery_triggered_count": recovery_triggered,
        "recovery_patch_mode_entered_count": patch_mode_entered,
        "patch_emitted_count": patch_emitted,
        "patch_validated_count": patch_validated,
        "patch_committed_count": patch_committed,
        "model_generated_commit_count": model_generated_commits,
        "salvaged_commit_count": salvaged_commits,
        "action_counts": dict(action_counts),
        "effective_action_counts": dict(effective_counts),
        "policy_source_counts": dict(policy_counts),
        "turn_mode_counts": dict(turn_mode_counts),
        "patch_source_counts": dict(patch_source_counts),
        "emission_failure_counts": dict(emission_failure_counts),
        "failure_code_counts": dict(failure_code_counts),
        "joint_semantics": dict(joint_semantics),
    }


def _merge_counter_dict(target: Counter[str], payload: Dict[str, int]) -> None:
    for key, value in payload.items():
        target[key] += int(value)


def aggregate_metrics(result_paths: Sequence[Path]) -> Dict[str, Dict[str, Any]]:
    aggregated: Dict[str, Dict[str, Any]] = {}
    for path in result_paths:
        if not path.exists():
            continue
        rows = _load_jsonl(path)
        source_name = path.name
        for row in rows:
            paper_id = str(row.get("paper_id") or "")
            if not paper_id:
                continue
            row_metric = _row_metrics(row, source_name)
            bucket = aggregated.setdefault(
                paper_id,
                {
                    "paper_id": paper_id,
                    "sources": [],
                    "source_rows": [],
                    "conflict_detected_count": 0,
                    "recovery_triggered_count": 0,
                    "recovery_patch_mode_entered_count": 0,
                    "patch_emitted_count": 0,
                    "patch_validated_count": 0,
                    "patch_committed_count": 0,
                    "model_generated_commit_count": 0,
                    "salvaged_commit_count": 0,
                    "action_counts": Counter(),
                    "effective_action_counts": Counter(),
                    "policy_source_counts": Counter(),
                    "turn_mode_counts": Counter(),
                    "patch_source_counts": Counter(),
                    "emission_failure_counts": Counter(),
                    "failure_code_counts": Counter(),
                    "joint_semantics": Counter(),
                },
            )
            bucket["sources"].append(source_name)
            bucket["source_rows"].append(row_metric)
            bucket["conflict_detected_count"] += row_metric["conflict_detected_count"]
            bucket["recovery_triggered_count"] += row_metric["recovery_triggered_count"]
            bucket["recovery_patch_mode_entered_count"] += row_metric["recovery_patch_mode_entered_count"]
            bucket["patch_emitted_count"] += row_metric["patch_emitted_count"]
            bucket["patch_validated_count"] += row_metric["patch_validated_count"]
            bucket["patch_committed_count"] += row_metric["patch_committed_count"]
            bucket["model_generated_commit_count"] += row_metric["model_generated_commit_count"]
            bucket["salvaged_commit_count"] += row_metric["salvaged_commit_count"]
            _merge_counter_dict(bucket["action_counts"], row_metric["action_counts"])
            _merge_counter_dict(bucket["effective_action_counts"], row_metric["effective_action_counts"])
            _merge_counter_dict(bucket["policy_source_counts"], row_metric["policy_source_counts"])
            _merge_counter_dict(bucket["turn_mode_counts"], row_metric["turn_mode_counts"])
            _merge_counter_dict(bucket["patch_source_counts"], row_metric["patch_source_counts"])
            _merge_counter_dict(bucket["emission_failure_counts"], row_metric["emission_failure_counts"])
            _merge_counter_dict(bucket["failure_code_counts"], row_metric["failure_code_counts"])
            _merge_counter_dict(bucket["joint_semantics"], row_metric["joint_semantics"])
    for metric in aggregated.values():
        metric["sources"] = sorted(set(metric["sources"]))
        for key in [
            "action_counts",
            "effective_action_counts",
            "policy_source_counts",
            "turn_mode_counts",
            "patch_source_counts",
            "emission_failure_counts",
            "failure_code_counts",
            "joint_semantics",
        ]:
            metric[key] = dict(metric[key])
        if metric["patch_committed_count"] > 0:
            metric["activation_type"] = "committed"
        elif metric["patch_emitted_count"] > 0:
            metric["activation_type"] = "emitted_no_commit"
        elif metric["recovery_triggered_count"] > 0:
            metric["activation_type"] = "triggered_no_patch"
        else:
            metric["activation_type"] = "no_trigger"
    return aggregated


def _selection_reasons(metric: Dict[str, Any], forced: bool = False) -> List[str]:
    reasons: List[str] = []
    if forced:
        reasons.append("historical_sentinel")
    if metric["patch_committed_count"] > 0:
        reasons.append("model_or_salvaged_commit")
    elif metric["patch_emitted_count"] > 0:
        reasons.append("patch_emitted_no_commit")
    elif metric["recovery_triggered_count"] > 0:
        reasons.append("triggered_no_patch")
    if metric["emission_failure_counts"]:
        reasons.append("emission_failure_signal")
    if metric["failure_code_counts"]:
        reasons.append("validator_failure_signal")
    return reasons or ["no_trigger_baseline"]


def select_recovery_relevant_cases(
    aggregated: Dict[str, Dict[str, Any]],
    max_samples: int,
) -> List[Dict[str, Any]]:
    candidates = [
        metric for metric in aggregated.values()
        if (
            metric["recovery_triggered_count"] > 0
            or metric["patch_emitted_count"] > 0
            or metric["patch_committed_count"] > 0
            or metric["emission_failure_counts"]
            or metric["failure_code_counts"]
            or metric["action_counts"].get("challenge_previous_hypothesis", 0) > 0
            or metric["action_counts"].get("request_evidence_recheck", 0) > 0
        )
    ]

    def sort_key(metric: Dict[str, Any]):
        return (
            -metric["patch_committed_count"],
            -metric["patch_emitted_count"],
            -metric["recovery_patch_mode_entered_count"],
            -metric["recovery_triggered_count"],
            -metric["conflict_detected_count"],
            metric["paper_id"],
        )

    by_bucket = {
        "committed": [m for m in candidates if m["patch_committed_count"] > 0],
        "emitted_no_commit": [m for m in candidates if m["patch_emitted_count"] > 0 and m["patch_committed_count"] == 0],
        "triggered_no_patch": [m for m in candidates if m["recovery_triggered_count"] > 0 and m["patch_emitted_count"] == 0],
        "recovery_relevant_no_trigger": [m for m in candidates if m["recovery_triggered_count"] == 0],
    }
    selected: List[Dict[str, Any]] = []
    selected_ids = set()

    for bucket_name in ["committed", "emitted_no_commit", "triggered_no_patch", "recovery_relevant_no_trigger"]:
        items = sorted(by_bucket[bucket_name], key=sort_key)
        if items:
            metric = items[0]
            selected.append({
                "paper_id": metric["paper_id"],
                "bucket": bucket_name,
                "reasons": _selection_reasons(metric),
                **{k: metric[k] for k in [
                    "activation_type",
                    "conflict_detected_count",
                    "recovery_triggered_count",
                    "recovery_patch_mode_entered_count",
                    "patch_emitted_count",
                    "patch_validated_count",
                    "patch_committed_count",
                    "model_generated_commit_count",
                    "salvaged_commit_count",
                    "sources",
                    "emission_failure_counts",
                    "failure_code_counts",
                ]},
            })
            selected_ids.add(metric["paper_id"])

    remaining = sorted(candidates, key=sort_key)
    for metric in remaining:
        if len(selected) >= max_samples:
            break
        if metric["paper_id"] in selected_ids:
            continue
        selected.append({
            "paper_id": metric["paper_id"],
            "bucket": metric["activation_type"],
            "reasons": _selection_reasons(metric),
            **{k: metric[k] for k in [
                "activation_type",
                "conflict_detected_count",
                "recovery_triggered_count",
                "recovery_patch_mode_entered_count",
                "patch_emitted_count",
                "patch_validated_count",
                "patch_committed_count",
                "model_generated_commit_count",
                "salvaged_commit_count",
                "sources",
                "emission_failure_counts",
                "failure_code_counts",
            ]},
        })
        selected_ids.add(metric["paper_id"])

    return selected[:max_samples]


def collect_historical_sentinels(aggregated: Dict[str, Dict[str, Any]], sentinel_ids: Sequence[str]) -> Dict[str, List[Dict[str, Any]]]:
    found = []
    missing = []
    for paper_id in sentinel_ids:
        metric = aggregated.get(paper_id)
        if metric is None:
            missing.append(paper_id)
            continue
        found.append({
            "paper_id": paper_id,
            "reasons": _selection_reasons(metric, forced=True),
            "activation_type": metric["activation_type"],
            "conflict_detected_count": metric["conflict_detected_count"],
            "recovery_triggered_count": metric["recovery_triggered_count"],
            "recovery_patch_mode_entered_count": metric["recovery_patch_mode_entered_count"],
            "patch_emitted_count": metric["patch_emitted_count"],
            "patch_committed_count": metric["patch_committed_count"],
            "sources": metric["sources"],
        })
    return {"historical_sentinel_cases": found, "missing_historical_sentinels": missing}


def materialize_subset(dataset_paths: Sequence[Path], paper_ids: Sequence[str], subset_path: Path) -> Dict[str, Any]:
    wanted = list(dict.fromkeys([pid for pid in paper_ids if pid]))
    row_map: Dict[str, Dict[str, Any]] = {}
    dataset_coverage: Dict[str, str] = {}
    for path in dataset_paths:
        if not path.exists():
            continue
        rows = _load_parquet_rows(path)
        for row in rows:
            paper_id = _row_paper_id(row)
            if paper_id and paper_id not in row_map:
                row_map[paper_id] = row
                dataset_coverage[paper_id] = str(path)
    subset_rows = [row_map[pid] for pid in wanted if pid in row_map]
    missing = [pid for pid in wanted if pid not in row_map]
    subset_path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(pa.Table.from_pylist(subset_rows), subset_path)
    return {
        "materialized_count": len(subset_rows),
        "missing_from_dataset": missing,
        "dataset_coverage": dataset_coverage,
    }


def write_json(payload: Dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), "utf-8")


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
    parser = argparse.ArgumentParser(description="Construct and optionally run the p24.4 recovery-relevant subset.")
    parser.add_argument("--results-path", action="append", default=[])
    parser.add_argument("--dataset-path", action="append", default=[])
    parser.add_argument("--subset-path", default=DEFAULT_SUBSET_PATH)
    parser.add_argument("--meta-path", default=DEFAULT_META_PATH)
    parser.add_argument("--analysis-path", default=DEFAULT_ANALYSIS_PATH)
    parser.add_argument("--max-emission-samples", type=int, default=8)
    parser.add_argument("--sentinel-id", action="append", default=[])
    parser.add_argument("--extract-only", action="store_true")
    parser.add_argument("--skip-run", action="store_true")
    parser.add_argument("--manager-batch-size", type=int, default=2)
    parser.add_argument("--max-turns", type=int, default=15)
    parser.add_argument("--max-workers-per-turn", type=int, default=3)
    parser.add_argument("--gpu-memory-utilization", type=float, default=0.6)
    parser.add_argument("--max-num-seqs", type=int, default=128)
    parser.add_argument("--max-model-len", type=int, default=3072)
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--top-p", type=float, default=0.95)
    parser.add_argument("--max-tokens", type=int, default=640)
    parser.add_argument("--output-path-4b", default=DEFAULT_OUTPUT_PATH_4B)
    args = parser.parse_args()

    result_paths = [Path(p) for p in (args.results_path or DEFAULT_RESULT_PATHS)]
    dataset_paths = [Path(p) for p in (args.dataset_path or DEFAULT_DATASET_PATHS)]
    sentinel_ids = list(dict.fromkeys(DEFAULT_SENTINEL_IDS + list(args.sentinel_id or [])))

    aggregated = aggregate_metrics(result_paths)
    recovery_relevant_cases = select_recovery_relevant_cases(aggregated, max_samples=args.max_emission_samples)
    sentinel_info = collect_historical_sentinels(aggregated, sentinel_ids)
    materialized = materialize_subset(dataset_paths, [item["paper_id"] for item in recovery_relevant_cases], Path(args.subset_path))
    subset_path = Path(args.subset_path)
    if subset_path.exists() and materialized.get("materialized_count", 0) > 0:
        rows = _load_parquet_rows(subset_path)
        relevant_ids = {item["paper_id"] for item in recovery_relevant_cases}
        sentinel_ids_set = {item["paper_id"] for item in sentinel_info.get("historical_sentinel_cases", [])}
        for row in rows:
            pid = _row_paper_id(row)
            row["recovery_relevant"] = pid in relevant_ids
            row["historical_sentinel"] = pid in sentinel_ids_set
        pq.write_table(pa.Table.from_pylist(rows), subset_path)

    meta = {
        "result_paths": [str(p) for p in result_paths if p.exists()],
        "dataset_paths": [str(p) for p in dataset_paths if p.exists()],
        "subset_path": str(Path(args.subset_path).resolve()),
        "recovery_relevant_cases": recovery_relevant_cases,
        **sentinel_info,
        **materialized,
    }
    analysis = {
        "aggregated_by_paper": aggregated,
        "recovery_relevant_cases": recovery_relevant_cases,
        **sentinel_info,
    }
    write_json(meta, Path(args.meta_path))
    write_json(analysis, Path(args.analysis_path))
    print(json.dumps(meta, ensure_ascii=False, indent=2))

    if args.extract_only or args.skip_run:
        return 0
    if materialized["materialized_count"] == 0:
        print("No rows materialized for recovery-relevant subset; aborting run.")
        return 1

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
    print("Running 4B recovery-relevant regression:")
    print(" ".join(cmd_4b))
    subprocess.run(cmd_4b, check=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
