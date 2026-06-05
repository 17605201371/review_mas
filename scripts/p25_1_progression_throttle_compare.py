from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple


RECOVERY_ACTIONS = {"challenge_previous_hypothesis", "request_evidence_recheck"}
PATH_KEYS = {"subset_path", "subset_meta_path", "output_path", "log_path"}
ALIGNMENT_KEYS: Sequence[str] = (
    "mode",
    "subset_path",
    "sample_ids",
    "model_path",
    "max_turns",
    "max_workers_per_turn",
    "manager_batch_size",
    "max_model_len",
    "max_tokens",
    "temperature",
    "top_p",
    "max_num_seqs",
    "gpu_memory_utilization",
)


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text())


def normalize_patch_source(value: Any) -> str:
    raw = str(value or "").strip()
    if raw == "salvaged":
        return "system_salvaged"
    if raw in {"model_generated", "system_salvaged"}:
        return raw
    return "none"


def group_map(meta: Dict[str, Any]) -> Dict[str, str]:
    ids = list(meta.get("ids", []))
    mapping: Dict[str, str] = {}
    for idx, paper_id in enumerate(ids):
        if idx < 4:
            mapping[paper_id] = "canonical_success_sensitive"
        elif idx < 7:
            mapping[paper_id] = "hardest_drift_prone"
        else:
            mapping[paper_id] = "recovery_support"
    return mapping


def summarize_rows(rows: List[Dict[str, Any]], groups: Dict[str, str]) -> Dict[str, Any]:
    aggregates = {
        "rows": len(rows),
        "patch_emitted_count": 0,
        "patch_committed_count": 0,
        "rows_with_any_commit": 0,
        "NO_EFFECT_PATCH": 0,
        "BLOCKED_BY_POLICY": 0,
        "model_generated_commit_count": 0,
        "system_salvaged_commit_count": 0,
        "target_switch_count": 0,
        "recovery_action_turns": 0,
        "progression_throttle_turns": 0,
        "early_finalize_count": 0,
        "avg_reward": 0.0,
        "decision_correct_rate": 0.0,
    }
    policy_source_counts: Counter[str] = Counter()
    summaries: List[Dict[str, Any]] = []
    for row in rows:
        turns = list(row.get("turn_logs", []))
        target_switch_count = 0
        last_targets = None
        patch_emitted_count = 0
        patch_committed_count = 0
        model_generated_commit_count = 0
        system_salvaged_commit_count = 0
        failure_counts: Counter[str] = Counter()
        recovery_action_turns = 0
        progression_throttle_turns = 0
        early_finalize_count = 0
        for idx, turn in enumerate(turns):
            action_type = turn.get("effective_action_type") or turn.get("action_type") or ""
            if action_type in RECOVERY_ACTIONS:
                recovery_action_turns += 1
            if turn.get("policy_source") == "progression_throttle_override":
                progression_throttle_turns += 1
            policy_source_counts[str(turn.get("policy_source") or "") or "none"] += 1
            target_sig = (
                tuple(turn.get("target_claim_ids", []) or []),
                tuple(turn.get("target_flaw_ids", []) or []),
                tuple(turn.get("target_evidence_ids", []) or []),
                tuple(turn.get("target_hypotheses", []) or []),
            )
            if any(target_sig):
                if last_targets is not None and target_sig != last_targets:
                    target_switch_count += 1
                last_targets = target_sig
            if turn.get("action_type") == "finalize" and idx < len(turns) - 1:
                early_finalize_count += 1
            emitted = bool(turn.get("recovery_patch_emitted", turn.get("recovery_emitted", False)))
            committed = bool(turn.get("recovery_patch_committed", turn.get("recovery_committed", False)))
            if emitted:
                patch_emitted_count += 1
            if committed:
                patch_committed_count += 1
                source = normalize_patch_source(turn.get("recovery_patch_source"))
                if source == "model_generated":
                    model_generated_commit_count += 1
                elif source == "system_salvaged":
                    system_salvaged_commit_count += 1
            code = str(turn.get("recovery_failure_code") or "").strip()
            if code:
                failure_counts[code] += 1
        summary = {
            "paper_id": row.get("paper_id", ""),
            "bucket": groups.get(row.get("paper_id", ""), "unknown"),
            "reward": float(row.get("reward", 0.0) or 0.0),
            "decision_correct": float(row.get("decision_correct", 0.0) or 0.0),
            "target_switch_count": target_switch_count,
            "patch_emitted_count": patch_emitted_count,
            "patch_committed_count": patch_committed_count,
            "rows_with_any_commit": int(patch_committed_count > 0),
            "NO_EFFECT_PATCH": failure_counts.get("NO_EFFECT_PATCH", 0),
            "BLOCKED_BY_POLICY": failure_counts.get("BLOCKED_BY_POLICY", 0),
            "model_generated_commit_count": model_generated_commit_count,
            "system_salvaged_commit_count": system_salvaged_commit_count,
            "recovery_action_turns": recovery_action_turns,
            "progression_throttle_turns": progression_throttle_turns,
            "early_finalize_count": early_finalize_count,
            "top_failure": failure_counts.most_common(1)[0][0] if failure_counts else "none",
        }
        summaries.append(summary)
        for key in (
            "patch_emitted_count",
            "patch_committed_count",
            "rows_with_any_commit",
            "NO_EFFECT_PATCH",
            "BLOCKED_BY_POLICY",
            "model_generated_commit_count",
            "system_salvaged_commit_count",
            "target_switch_count",
            "recovery_action_turns",
            "progression_throttle_turns",
            "early_finalize_count",
        ):
            aggregates[key] += summary[key]
        aggregates["avg_reward"] += summary["reward"]
        aggregates["decision_correct_rate"] += summary["decision_correct"]
    if rows:
        aggregates["avg_reward"] = round(aggregates["avg_reward"] / len(rows), 4)
        aggregates["decision_correct_rate"] = round(aggregates["decision_correct_rate"] / len(rows), 4)
    aggregates["policy_source_counts"] = dict(policy_source_counts)
    aggregates["summaries"] = summaries
    return aggregates


def find_row(summaries: List[Dict[str, Any]], paper_id: str) -> Dict[str, Any]:
    for item in summaries:
        if item["paper_id"] == paper_id:
            return item
    return {
        "paper_id": paper_id,
        "target_switch_count": 0,
        "patch_emitted_count": 0,
        "patch_committed_count": 0,
        "rows_with_any_commit": 0,
        "NO_EFFECT_PATCH": 0,
        "BLOCKED_BY_POLICY": 0,
        "model_generated_commit_count": 0,
        "system_salvaged_commit_count": 0,
        "recovery_action_turns": 0,
        "progression_throttle_turns": 0,
        "top_failure": "missing",
        "reward": 0.0,
    }


def _normalize_config_value(key: str, value: Any) -> Any:
    if key in PATH_KEYS and value is not None:
        return str(Path(str(value)))
    if key == "sample_ids":
        if value is None:
            return []
        return list(value)
    if isinstance(value, float):
        return round(value, 6)
    return value


def config_alignment_rows(baseline: Dict[str, Any], candidate: Dict[str, Any]) -> List[Tuple[str, Any, Any, str]]:
    rows: List[Tuple[str, Any, Any, str]] = []
    for key in ALIGNMENT_KEYS:
        left = _normalize_config_value(key, baseline.get(key))
        right = _normalize_config_value(key, candidate.get(key))
        status = "OK" if left == right else "MISMATCH"
        rows.append((key, left, right, status))
    return rows


def require_config_alignment(baseline: Dict[str, Any], candidate: Dict[str, Any]) -> List[Tuple[str, Any, Any, str]]:
    rows = config_alignment_rows(baseline, candidate)
    mismatches = [row for row in rows if row[3] != "OK"]
    if mismatches:
        rendered = "\n".join(
            f"- {key}: baseline={left!r} candidate={right!r}" for key, left, right, _ in mismatches
        )
        raise SystemExit(
            "Progression throttle compare aborted due to config mismatch:\n" + rendered
        )
    return rows


def write_protocol(root: Path) -> None:
    lines = [
        "# Progression Throttle Protocol V1",
        "",
        "## Scope",
        "- This round only adds a pre-recovery throttle inside `review_manager_policy.apply_manager_policy_fallback()`.",
        "- Manager architecture, recovery phase, sticky, validator/lifecycle, reward, salvage, and dataset scope stay frozen.",
        "",
        "## Intent",
        "- Delay recovery-oriented routing when the target set is still broad or explicitly fallback-anchored.",
        "- Prefer `verify_evidence` over early `request_evidence_recheck` / `challenge_previous_hypothesis` until target grounding narrows.",
        "",
        "## Guard Conditions",
        "- only in `mode == s4`",
        "- only outside explicit `phase = recovery`",
        "- only for recovery actions after manager fallback has already chosen an action",
        "- only when sanitized target claims remain broad (`len > 1`) or fallback-anchored (`claim-fallback-*`)",
        "",
        "## Compare Discipline",
        "- baseline and candidate runs must provide explicit config snapshots",
        "- compare aborts on any mismatch across critical runtime fields (mode, subset, sample ids, model, max_turns, worker/runtime envelope)",
    ]
    root.joinpath("PROGRESSION_THROTTLE_PROTOCOL_V1.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_sanity(
    root: Path,
    baseline: Dict[str, Any],
    candidate: Dict[str, Any],
    output_path: Path,
    log_path: Path,
    baseline_config_path: Path,
    candidate_config_path: Path,
) -> None:
    lines = [
        "# P25.1 Progression Throttle V1 Sanity",
        "",
        "## Runtime Artifacts",
        "- retained baseline jsonl: `outputs/results_main/review_infer/p25_1_iter_recovery_phase_v1.jsonl`",
        f"- progression throttle v1 jsonl: `{output_path}`",
        f"- progression throttle v1 log: `{log_path}`",
        f"- baseline config snapshot: `{baseline_config_path}`",
        f"- candidate config snapshot: `{candidate_config_path}`",
        "",
        "## Sanity Checks",
        f"- rows: {candidate['rows']}",
        f"- progression_throttle_turns: {candidate['progression_throttle_turns']}",
        f"- recovery_action_turns: {candidate['recovery_action_turns']}",
        f"- early_finalize_count: {candidate['early_finalize_count']}",
        f"- decision_correct_rate: {candidate['decision_correct_rate']}",
        "",
        "## Observation",
        "- This run only counts a turn as throttled when `policy_source == progression_throttle_override` appears in the emitted turn log.",
        "- Compare output is only valid when the two config snapshots pass strict alignment checks.",
    ]
    root.joinpath("P25_1_PROGRESSION_THROTTLE_SANITY.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_compare(root: Path, baseline: Dict[str, Any], candidate: Dict[str, Any], groups: Dict[str, str], alignment_rows: List[Tuple[str, Any, Any, str]]) -> None:
    metrics = [
        "target_switch_count",
        "recovery_action_turns",
        "progression_throttle_turns",
        "patch_emitted_count",
        "patch_committed_count",
        "rows_with_any_commit",
        "NO_EFFECT_PATCH",
        "BLOCKED_BY_POLICY",
        "model_generated_commit_count",
        "system_salvaged_commit_count",
        "avg_reward",
        "decision_correct_rate",
    ]
    lines = [
        "# P25.1 Progression Throttle V1 Compare",
        "",
        "## Config Alignment",
        "| Key | Baseline | Candidate | Status |",
        "| --- | --- | --- | --- |",
    ]
    for key, left, right, status in alignment_rows:
        lines.append(f"| {key} | `{left}` | `{right}` | {status} |")
    lines.extend([
        "",
        "## Aggregate Compare",
        "| Metric | Retained baseline | Progression throttle v1 |",
        "| --- | ---: | ---: |",
    ])
    for metric in metrics:
        lines.append(f"| {metric} | {baseline.get(metric, 0)} | {candidate.get(metric, 0)} |")
    lines.extend([
        "",
        "## Per-Case Snapshot",
        "| paper_id | bucket | baseline recovery turns | v1 recovery turns | baseline committed | v1 committed | baseline blocked | v1 blocked | baseline reward | v1 reward |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ])
    for paper_id in groups:
        left = find_row(baseline["summaries"], paper_id)
        right = find_row(candidate["summaries"], paper_id)
        lines.append(
            f"| {paper_id} | {groups[paper_id]} | {left['recovery_action_turns']} | {right['recovery_action_turns']} | {left['patch_committed_count']} | {right['patch_committed_count']} | {left['BLOCKED_BY_POLICY']} | {right['BLOCKED_BY_POLICY']} | {left['reward']:.4f} | {right['reward']:.4f} |"
        )
    root.joinpath("P25_1_PROGRESSION_THROTTLE_COMPARE.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_decision(root: Path, baseline: Dict[str, Any], candidate: Dict[str, Any], groups: Dict[str, str], alignment_rows: List[Tuple[str, Any, Any, str]]) -> None:
    canonical_ids = [paper_id for paper_id, bucket in groups.items() if bucket == "canonical_success_sensitive"]
    canonical_regressions = []
    for paper_id in canonical_ids:
        left = find_row(baseline["summaries"], paper_id)
        right = find_row(candidate["summaries"], paper_id)
        if right["patch_committed_count"] < left["patch_committed_count"] or right["rows_with_any_commit"] < left["rows_with_any_commit"]:
            canonical_regressions.append(paper_id)
    keep = (
        candidate["progression_throttle_turns"] > 0
        and candidate["patch_committed_count"] >= baseline["patch_committed_count"]
        and candidate["rows_with_any_commit"] >= baseline["rows_with_any_commit"]
        and not canonical_regressions
    )
    decision = "KEEP" if keep else "ROLLBACK"
    lines = [
        "# P25.1 Progression Throttle V1 Decision",
        "",
        f"- decision: **{decision}**",
        f"- progression_throttle_turns: {candidate['progression_throttle_turns']} (baseline: {baseline['progression_throttle_turns']})",
        f"- patch_committed_count: {baseline['patch_committed_count']} -> {candidate['patch_committed_count']}",
        f"- rows_with_any_commit: {baseline['rows_with_any_commit']} -> {candidate['rows_with_any_commit']}",
        f"- NO_EFFECT_PATCH: {baseline['NO_EFFECT_PATCH']} -> {candidate['NO_EFFECT_PATCH']}",
        f"- BLOCKED_BY_POLICY: {baseline['BLOCKED_BY_POLICY']} -> {candidate['BLOCKED_BY_POLICY']}",
        f"- recovery_action_turns: {baseline['recovery_action_turns']} -> {candidate['recovery_action_turns']}",
        f"- canonical_regressions: {', '.join(canonical_regressions) if canonical_regressions else 'none'}",
        f"- config_alignment: {'ok' if all(status == 'OK' for _, _, _, status in alignment_rows) else 'mismatch'}",
        "",
        "## Interpretation",
        "- This round does not show an attributable positive signal from the intended mechanism unless `progression_throttle_override` actually appears in the turn logs.",
        "- Any throughput judgment is only valid after config alignment passes.",
        "- The safer reading is that upstream target/fallback drift still dominates unless throttle actuation becomes both visible and beneficial under aligned runtime settings.",
    ]
    root.joinpath("P25_1_PROGRESSION_THROTTLE_DECISION.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--baseline', default='outputs/results_main/review_infer/p25_1_iter_recovery_phase_v1.jsonl')
    parser.add_argument('--candidate', default='outputs/results_main/review_infer/p25_1_iter_progression_throttle_v1.jsonl')
    parser.add_argument('--baseline-config', default='outputs/results_main/review_infer/p25_1_iter_recovery_phase_v1.config.json')
    parser.add_argument('--candidate-config', default='outputs/results_main/review_infer/p25_1_iter_progression_throttle_v1.config.json')
    parser.add_argument('--subset-meta', default='outputs/results_main/review_infer/p25_1_iteration_subset_meta.json')
    parser.add_argument('--root', default='.')
    parser.add_argument('--log', default='p25_1_iter_progression_throttle_v1.log')
    args = parser.parse_args()

    root = Path(args.root)
    baseline_rows = load_jsonl(Path(args.baseline))
    candidate_rows = load_jsonl(Path(args.candidate))
    baseline_config = load_json(Path(args.baseline_config))
    candidate_config = load_json(Path(args.candidate_config))
    alignment_rows = require_config_alignment(baseline_config, candidate_config)
    meta = json.loads(Path(args.subset_meta).read_text())
    groups = group_map(meta)
    baseline = summarize_rows(baseline_rows, groups)
    candidate = summarize_rows(candidate_rows, groups)
    write_protocol(root)
    write_sanity(
        root,
        baseline,
        candidate,
        Path(args.candidate),
        Path(args.log),
        Path(args.baseline_config),
        Path(args.candidate_config),
    )
    write_compare(root, baseline, candidate, groups, alignment_rows)
    write_decision(root, baseline, candidate, groups, alignment_rows)
    print(json.dumps({
        'config_alignment': alignment_rows,
        'baseline': {k: v for k, v in baseline.items() if k != 'summaries'},
        'candidate': {k: v for k, v in candidate.items() if k != 'summaries'},
    }, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
