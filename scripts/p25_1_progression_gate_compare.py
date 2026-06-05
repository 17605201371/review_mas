from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple

RECOVERY_ACTIONS = {"challenge_previous_hypothesis", "request_evidence_recheck"}
PATH_KEYS = {"subset_path", "subset_meta_path"}
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
    "seed",
    "tensor_parallel_size",
    "trust_remote_code",
    "enforce_eager",
    "limit",
    "split",
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


def normalize_config_value(key: str, value: Any) -> Any:
    if key in PATH_KEYS and value is not None:
        return str(Path(str(value)))
    if key == "sample_ids":
        return list(value or [])
    if isinstance(value, float):
        return round(value, 6)
    return value


def config_alignment_rows(baseline: Dict[str, Any], candidate: Dict[str, Any]) -> List[Tuple[str, Any, Any, str]]:
    rows: List[Tuple[str, Any, Any, str]] = []
    for key in ALIGNMENT_KEYS:
        left = normalize_config_value(key, baseline.get(key))
        right = normalize_config_value(key, candidate.get(key))
        rows.append((key, left, right, "OK" if left == right else "MISMATCH"))
    return rows


def require_config_alignment(baseline: Dict[str, Any], candidate: Dict[str, Any]) -> List[Tuple[str, Any, Any, str]]:
    rows = config_alignment_rows(baseline, candidate)
    mismatches = [row for row in rows if row[3] != "OK"]
    if mismatches:
        rendered = "\n".join(f"- {key}: baseline={left!r} candidate={right!r}" for key, left, right, _ in mismatches)
        raise SystemExit("Progression gate compare invalid due to config mismatch:\n" + rendered)
    return rows


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


def _is_fallback_target(target_ids: Sequence[str]) -> bool:
    return any(str(item).startswith("claim-fallback") for item in target_ids or [])


def _is_broad_target(target_ids: Sequence[str]) -> bool:
    real = [str(item) for item in target_ids or [] if not str(item).startswith("claim-fallback")]
    return len(real) > 2


def summarize_rows(rows: List[Dict[str, Any]], groups: Dict[str, str]) -> Dict[str, Any]:
    totals = Counter()
    policy_counts: Counter[str] = Counter()
    summaries: List[Dict[str, Any]] = []
    reward_sum = 0.0
    decision_sum = 0.0
    for row in rows:
        turns = list(row.get("turn_logs", []) or [])
        per = Counter()
        failures: Counter[str] = Counter()
        last_targets = None
        for idx, turn in enumerate(turns):
            action = str(turn.get("effective_action_type") or turn.get("action_type") or "")
            targets = list(turn.get("target_claim_ids") or [])
            policy_counts[str(turn.get("policy_source") or "none")] += 1
            if action in RECOVERY_ACTIONS:
                per["recovery_enter_count"] += 1
                if _is_broad_target(targets):
                    per["broad_target_recovery_count"] += 1
                if _is_fallback_target(targets):
                    per["fallback_target_recovery_count"] += 1
                if str(turn.get("progression_gate_reason") or "") == "weak_conflict" or bool(turn.get("weak_conflict_gate_blocked")):
                    per["weak_conflict_recovery_count"] += 1
            if bool(turn.get("progression_gate_triggered")):
                per["progression_gate_triggered_turns"] += 1
            if bool(turn.get("broad_target_gate_blocked")):
                per["broad_target_gate_blocked"] += 1
            if bool(turn.get("fallback_target_gate_blocked")):
                per["fallback_target_gate_blocked"] += 1
            if bool(turn.get("weak_conflict_gate_blocked")):
                per["weak_conflict_gate_blocked"] += 1
            if bool(turn.get("recovery_patch_emitted", turn.get("recovery_emitted", False))):
                per["patch_emitted_count"] += 1
            committed = bool(turn.get("recovery_patch_committed", turn.get("recovery_committed", False)))
            if committed:
                per["patch_committed_count"] += 1
                source = normalize_patch_source(turn.get("recovery_patch_source"))
                if source == "model_generated":
                    per["model_generated_commit_count"] += 1
                elif source == "system_salvaged":
                    per["system_salvaged_commit_count"] += 1
            code = str(turn.get("recovery_failure_code") or "").strip()
            if code:
                failures[code] += 1
            sig = (tuple(targets), tuple(turn.get("target_flaw_ids") or []), tuple(turn.get("target_evidence_ids") or []))
            if any(sig):
                if last_targets is not None and sig != last_targets:
                    per["target_switch_count"] += 1
                last_targets = sig
            if turn.get("action_type") == "finalize" and idx < len(turns) - 1:
                per["early_finalize_count"] += 1
        per["rows_with_any_commit"] = int(per["patch_committed_count"] > 0)
        per["NO_EFFECT_PATCH"] = failures.get("NO_EFFECT_PATCH", 0)
        per["BLOCKED_BY_POLICY"] = failures.get("BLOCKED_BY_POLICY", 0)
        summary = {
            "paper_id": row.get("paper_id", ""),
            "bucket": groups.get(row.get("paper_id", ""), "unknown"),
            "reward": float(row.get("reward", 0.0) or 0.0),
            "decision_correct": float(row.get("decision_correct", 0.0) or 0.0),
            **dict(per),
        }
        summaries.append(summary)
        for key, value in per.items():
            totals[key] += value
        reward_sum += summary["reward"]
        decision_sum += summary["decision_correct"]
    totals["rows"] = len(rows)
    totals["avg_reward"] = round(reward_sum / len(rows), 4) if rows else 0.0
    totals["decision_correct_rate"] = round(decision_sum / len(rows), 4) if rows else 0.0
    totals["policy_source_counts"] = dict(policy_counts)
    totals["summaries"] = summaries
    return dict(totals)


def find_summary(items: List[Dict[str, Any]], paper_id: str) -> Dict[str, Any]:
    for item in items:
        if item.get("paper_id") == paper_id:
            return item
    return {"paper_id": paper_id}


def get(summary: Dict[str, Any], key: str) -> Any:
    return summary.get(key, 0)


def write_config_alignment(root: Path, alignment_rows: List[Tuple[str, Any, Any, str]], baseline_config_path: Path, candidate_config_path: Path) -> None:
    lines = [
        "# P25.1 Config Alignment",
        "",
        "## Result",
        "- status: PASS",
        f"- baseline config: `{baseline_config_path}`",
        f"- candidate config: `{candidate_config_path}`",
        "",
        "## Alignment Table",
        "| Key | Baseline | Candidate | Status |",
        "| --- | --- | --- | --- |",
    ]
    for key, left, right, status in alignment_rows:
        lines.append(f"| {key} | `{left}` | `{right}` | {status} |")
    lines.extend([
        "",
        "## Guard Rule",
        "The compare script aborts before producing conclusions if any critical field above mismatches.",
        "Output/log paths and run names are intentionally excluded from strict equality because they differ by run identity.",
    ])
    root.joinpath("P25_1_CONFIG_ALIGNMENT.md").write_text("\n".join(lines) + "\n")


def write_protocol(root: Path) -> None:
    lines = [
        "# Progression Gate V1 Protocol",
        "",
        "## Scope",
        "- First add config alignment protection.",
        "- Then add one pre-sanitize progression gate before aggressive recovery becomes final routing.",
        "- Do not change sticky, sanitize, fallback generation, validator/lifecycle, reward, or dataset scope.",
        "",
        "## Gate Placement",
        "The gate runs in `review_manager_policy.apply_manager_policy_fallback()` after S4 recovery-oriented overrides and sticky recovery bias have selected a candidate action, but before `_sanitize_targets_for_action()` and before `review_runner._apply_recovery_phase_protocol()`.",
        "",
        "## Gate Input",
        "The main input is raw/pre-sanitize `target_claim_ids` from the manager payload or `infer_action_from_state(...)`, not post-sanitize targets.",
        "The final sanitized target ids are logged separately for diagnosis.",
        "",
        "## Blocked Aggressive Actions",
        "- `request_evidence_recheck`",
        "- `challenge_previous_hypothesis`",
        "",
        "## Reasons",
        "- `fallback_target`: raw target contains `claim-fallback-*`.",
        "- `broad_target`: raw real target set is too broad, or challenge has multiple real targets.",
        "- `weak_conflict`: recovery action lacks enough conflict/evidence signal.",
        "- `multiple_reasons`: more than one reason applies.",
        "",
        "## Safe Downgrade Order",
        "1. keep current non-aggressive action if it is evidence/flaw/claim work",
        "2. `verify_evidence`",
        "3. `analyze_flaws`",
        "4. current action only as a last fallback",
    ]
    root.joinpath("PROGRESSION_GATE_V1_PROTOCOL.md").write_text("\n".join(lines) + "\n")


def write_sanity(root: Path, candidate: Dict[str, Any]) -> None:
    lines = [
        "# P25.1 Progression Gate V1 Sanity",
        "",
        "## Run Status",
        f"- rows: {candidate.get('rows', 0)}",
        f"- progression_gate_triggered_turns: {candidate.get('progression_gate_triggered_turns', 0)}",
        f"- broad_target_gate_blocked: {candidate.get('broad_target_gate_blocked', 0)}",
        f"- fallback_target_gate_blocked: {candidate.get('fallback_target_gate_blocked', 0)}",
        f"- weak_conflict_gate_blocked: {candidate.get('weak_conflict_gate_blocked', 0)}",
        f"- patch_emitted_count: {candidate.get('patch_emitted_count', 0)}",
        f"- patch_committed_count: {candidate.get('patch_committed_count', 0)}",
        f"- rows_with_any_commit: {candidate.get('rows_with_any_commit', 0)}",
        "",
        "## Field Check",
        "- gate fields are read from turn logs: `progression_gate_triggered`, `progression_gate_reason`, raw/sanitized target ids, and reason booleans.",
        "- config alignment passed before this file was written.",
    ]
    root.joinpath("P25_1_PROGRESSION_GATE_V1_SANITY.md").write_text("\n".join(lines) + "\n")


def write_compare(root: Path, baseline: Dict[str, Any], candidate: Dict[str, Any], groups: Dict[str, str]) -> None:
    metrics = [
        "progression_gate_triggered_turns",
        "broad_target_gate_blocked",
        "fallback_target_gate_blocked",
        "weak_conflict_gate_blocked",
        "recovery_enter_count",
        "broad_target_recovery_count",
        "fallback_target_recovery_count",
        "weak_conflict_recovery_count",
        "patch_emitted_count",
        "patch_committed_count",
        "rows_with_any_commit",
        "model_generated_commit_count",
        "system_salvaged_commit_count",
        "NO_EFFECT_PATCH",
        "BLOCKED_BY_POLICY",
        "target_switch_count",
        "early_finalize_count",
        "avg_reward",
        "decision_correct_rate",
    ]
    lines = [
        "# P25.1 Progression Gate V1 Compare",
        "",
        "## Aggregate Metrics",
        "| Metric | Baseline | Progression Gate V1 |",
        "| --- | ---: | ---: |",
    ]
    for metric in metrics:
        lines.append(f"| {metric} | {baseline.get(metric, 0)} | {candidate.get(metric, 0)} |")
    lines.extend([
        "",
        "## Per-Case Snapshot",
        "| paper_id | bucket | baseline commits | gate commits | baseline emitted | gate emitted | baseline fallback recovery | gate fallback recovery | gate triggered | baseline reward | gate reward |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ])
    for paper_id, bucket in groups.items():
        b = find_summary(baseline["summaries"], paper_id)
        c = find_summary(candidate["summaries"], paper_id)
        lines.append(
            f"| {paper_id} | {bucket} | {get(b, 'patch_committed_count')} | {get(c, 'patch_committed_count')} | {get(b, 'patch_emitted_count')} | {get(c, 'patch_emitted_count')} | {get(b, 'fallback_target_recovery_count')} | {get(c, 'fallback_target_recovery_count')} | {get(c, 'progression_gate_triggered_turns')} | {float(get(b, 'reward')):.4f} | {float(get(c, 'reward')):.4f} |"
        )
    root.joinpath("P25_1_PROGRESSION_GATE_V1_COMPARE.md").write_text("\n".join(lines) + "\n")


def write_decision(root: Path, baseline: Dict[str, Any], candidate: Dict[str, Any], groups: Dict[str, str]) -> None:
    canonical = [pid for pid, bucket in groups.items() if bucket == "canonical_success_sensitive"]
    regressions = []
    for pid in canonical:
        b = find_summary(baseline["summaries"], pid)
        c = find_summary(candidate["summaries"], pid)
        if get(c, "patch_committed_count") < get(b, "patch_committed_count") or get(c, "rows_with_any_commit") < get(b, "rows_with_any_commit"):
            regressions.append(pid)
    keep = (
        candidate.get("progression_gate_triggered_turns", 0) > 0
        and candidate.get("broad_target_recovery_count", 0) <= baseline.get("broad_target_recovery_count", 0)
        and candidate.get("fallback_target_recovery_count", 0) <= baseline.get("fallback_target_recovery_count", 0)
        and candidate.get("patch_committed_count", 0) >= baseline.get("patch_committed_count", 0)
        and candidate.get("rows_with_any_commit", 0) >= baseline.get("rows_with_any_commit", 0)
        and candidate.get("system_salvaged_commit_count", 0) >= baseline.get("system_salvaged_commit_count", 0)
        and not regressions
    )
    decision = "KEEP" if keep else "ROLLBACK"
    lines = [
        "# P25.1 Progression Gate V1 Decision",
        "",
        f"- decision: **{decision}**",
        f"- progression_gate_triggered_turns: {candidate.get('progression_gate_triggered_turns', 0)}",
        f"- broad_target_recovery_count: {baseline.get('broad_target_recovery_count', 0)} -> {candidate.get('broad_target_recovery_count', 0)}",
        f"- fallback_target_recovery_count: {baseline.get('fallback_target_recovery_count', 0)} -> {candidate.get('fallback_target_recovery_count', 0)}",
        f"- patch_emitted_count: {baseline.get('patch_emitted_count', 0)} -> {candidate.get('patch_emitted_count', 0)}",
        f"- patch_committed_count: {baseline.get('patch_committed_count', 0)} -> {candidate.get('patch_committed_count', 0)}",
        f"- rows_with_any_commit: {baseline.get('rows_with_any_commit', 0)} -> {candidate.get('rows_with_any_commit', 0)}",
        f"- model_generated_commit_count: {baseline.get('model_generated_commit_count', 0)} -> {candidate.get('model_generated_commit_count', 0)}",
        f"- system_salvaged_commit_count: {baseline.get('system_salvaged_commit_count', 0)} -> {candidate.get('system_salvaged_commit_count', 0)}",
        f"- NO_EFFECT_PATCH: {baseline.get('NO_EFFECT_PATCH', 0)} -> {candidate.get('NO_EFFECT_PATCH', 0)}",
        f"- BLOCKED_BY_POLICY: {baseline.get('BLOCKED_BY_POLICY', 0)} -> {candidate.get('BLOCKED_BY_POLICY', 0)}",
        f"- canonical_regressions: {', '.join(regressions) if regressions else 'none'}",
        "",
        "## Interpretation",
    ]
    if keep:
        lines.append("- Progression Gate V1 satisfies the retention criteria on the fixed forensic subset.")
    else:
        lines.append("- Progression Gate V1 does not satisfy the retention criteria; do not stack further changes on it without a root-cause review.")
    lines.extend([
        "- The decision is based on gate actuation plus preservation of commits, rows with commits, salvage commits, and canonical stability.",
        "- Config alignment passed before this compare was generated.",
    ])
    root.joinpath("P25_1_PROGRESSION_GATE_V1_DECISION.md").write_text("\n".join(lines) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--baseline', default='outputs/results_main/review_infer/p25_1_iter_recovery_phase_v1.jsonl')
    parser.add_argument('--candidate', default='outputs/results_main/review_infer/p25_1_iter_progression_gate_v1.jsonl')
    parser.add_argument('--baseline-config', default='P25_1_RUN_CONFIG_BASELINE.json')
    parser.add_argument('--candidate-config', default='P25_1_RUN_CONFIG_CANDIDATE.json')
    parser.add_argument('--subset-meta', default='outputs/results_main/review_infer/p25_1_iteration_subset_meta.json')
    parser.add_argument('--root', default='.')
    args = parser.parse_args()
    root = Path(args.root)
    baseline_config = load_json(Path(args.baseline_config))
    candidate_config = load_json(Path(args.candidate_config))
    alignment = require_config_alignment(baseline_config, candidate_config)
    meta = load_json(Path(args.subset_meta))
    groups = group_map(meta)
    baseline = summarize_rows(load_jsonl(Path(args.baseline)), groups)
    candidate = summarize_rows(load_jsonl(Path(args.candidate)), groups)
    write_config_alignment(root, alignment, Path(args.baseline_config), Path(args.candidate_config))
    write_protocol(root)
    write_sanity(root, candidate)
    write_compare(root, baseline, candidate, groups)
    write_decision(root, baseline, candidate, groups)
    print(json.dumps({'baseline': {k:v for k,v in baseline.items() if k != 'summaries'}, 'candidate': {k:v for k,v in candidate.items() if k != 'summaries'}}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
