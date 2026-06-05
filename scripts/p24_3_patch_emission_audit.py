from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List

RECOVERY_ACTION_TYPES = {"challenge_previous_hypothesis", "request_evidence_recheck"}


def _load_jsonl(path: Path) -> List[Dict[str, Any]]:
    return [json.loads(line) for line in path.read_text("utf-8").splitlines() if line.strip()]


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


def analyze_run(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    overall = {
        "rows": len(rows),
        "avg_reward": round(sum(float(r.get("reward") or 0.0) for r in rows) / max(len(rows), 1), 4),
        "decision_correct_rate": round(sum(1 for r in rows if r.get("decision_correct")) / max(len(rows), 1), 4),
    }
    stage_counts = Counter()
    row_stage_counts = Counter()
    action_counts = Counter()
    effective_counts = Counter()
    turn_mode_counts = Counter()
    policy_counts = Counter()
    patch_source_counts = Counter()
    emission_failure_code_counts = Counter()
    joint_counts = Counter()
    per_row = []

    for row in rows:
        row_metric = {
            "paper_id": row.get("paper_id"),
            "reward": float(row.get("reward") or 0.0),
            "decision_correct": bool(row.get("decision_correct")),
            "conflict_detected_count": 0,
            "recovery_triggered_count": 0,
            "recovery_patch_mode_entered_count": 0,
            "patch_emitted_count": 0,
            "patch_validated_count": 0,
            "patch_committed_count": 0,
            "model_generated_commit_count": 0,
            "salvaged_commit_count": 0,
            "emission_failure_code_counts": Counter(),
            "failure_code_counts": Counter(),
            "combo_counts": Counter(),
            "type": "A",
        }
        for turn in row.get("turn_logs", []) or []:
            action = str(turn.get("action_type") or "")
            effective = str(turn.get("effective_action_type") or "")
            turn_mode = str(turn.get("turn_mode") or "normal_evidence")
            policy = str(turn.get("policy_source") or "")
            patch_source = _normalized_source(turn.get("recovery_patch_source"))
            emission_failure = str(turn.get("emission_failure_code") or "").strip()
            recovery_failure = str(turn.get("recovery_failure_code") or "").strip()

            conflict = _turn_conflict_detected(turn)
            triggered = _turn_recovery_triggered(turn)
            patch_mode = _turn_patch_mode_entered(turn)
            emitted = _turn_patch_emitted(turn)
            validated = bool(turn.get("recovery_validated"))
            committed = bool(turn.get("recovery_committed"))

            if conflict:
                stage_counts["conflict_detected"] += 1
                row_metric["conflict_detected_count"] += 1
            if triggered:
                stage_counts["recovery_triggered"] += 1
                row_metric["recovery_triggered_count"] += 1
            if patch_mode:
                stage_counts["recovery_patch_mode_entered"] += 1
                row_metric["recovery_patch_mode_entered_count"] += 1
            if emitted:
                stage_counts["patch_emitted"] += 1
                row_metric["patch_emitted_count"] += 1
            if validated:
                stage_counts["patch_validated"] += 1
                row_metric["patch_validated_count"] += 1
            if committed:
                stage_counts["patch_committed"] += 1
                row_metric["patch_committed_count"] += 1
                if patch_source == "model_generated":
                    row_metric["model_generated_commit_count"] += 1
                elif patch_source == "salvaged":
                    row_metric["salvaged_commit_count"] += 1

            if action:
                action_counts[action] += 1
            if effective:
                effective_counts[effective] += 1
            if turn_mode:
                turn_mode_counts[turn_mode] += 1
            if policy:
                policy_counts[policy] += 1
            if patch_source != "none":
                patch_source_counts[patch_source] += 1
            if emission_failure:
                emission_failure_code_counts[emission_failure] += 1
                row_metric["emission_failure_code_counts"][emission_failure] += 1
            if recovery_failure:
                row_metric["failure_code_counts"][recovery_failure] += 1
            if triggered or patch_mode or emitted:
                combo = f"{action} -> {effective} | {turn_mode} | {policy} | {patch_source}"
                joint_counts[combo] += 1
                row_metric["combo_counts"][combo] += 1

        if row_metric["patch_committed_count"] > 0:
            row_metric["type"] = "D"
        elif row_metric["patch_emitted_count"] > 0:
            row_metric["type"] = "C"
        elif row_metric["recovery_triggered_count"] > 0:
            row_metric["type"] = "B"
        else:
            row_metric["type"] = "A"

        for stage in [
            "conflict_detected_count",
            "recovery_triggered_count",
            "recovery_patch_mode_entered_count",
            "patch_emitted_count",
            "patch_validated_count",
            "patch_committed_count",
        ]:
            if row_metric[stage] > 0:
                row_stage_counts[stage.replace("_count", "_rows")] += 1
        row_stage_counts[f"type_{row_metric['type']}"] += 1
        row_metric["emission_failure_code_counts"] = dict(row_metric["emission_failure_code_counts"])
        row_metric["failure_code_counts"] = dict(row_metric["failure_code_counts"])
        row_metric["combo_counts"] = dict(row_metric["combo_counts"])
        per_row.append(row_metric)

    stage_counts_dict = dict(stage_counts)
    trigger_to_patch_mode_rate = round(
        stage_counts_dict.get("recovery_patch_mode_entered", 0) / max(stage_counts_dict.get("recovery_triggered", 0), 1),
        4,
    )
    patch_mode_to_emission_rate = round(
        stage_counts_dict.get("patch_emitted", 0) / max(stage_counts_dict.get("recovery_patch_mode_entered", 0), 1),
        4,
    )
    overall.update(
        {
            "stage_counts": stage_counts_dict,
            "row_stage_counts": dict(row_stage_counts),
            "action_counts": dict(action_counts),
            "effective_action_counts": dict(effective_counts),
            "turn_mode_counts": dict(turn_mode_counts),
            "policy_source_counts": dict(policy_counts),
            "patch_source_counts": dict(patch_source_counts),
            "emission_failure_code_distribution": dict(emission_failure_code_counts),
            "joint_semantics_counts": dict(joint_counts),
            "trigger_to_patch_mode_rate": trigger_to_patch_mode_rate,
            "patch_mode_to_emission_rate": patch_mode_to_emission_rate,
            "per_row": per_row,
            "model_generated_commit_count": sum(r["model_generated_commit_count"] for r in per_row),
            "salvaged_commit_count": sum(r["salvaged_commit_count"] for r in per_row),
        }
    )
    return overall


def write_docs(meta: Dict[str, Any], analysis: Dict[str, Any], docs_root: Path) -> None:
    docs_root.mkdir(parents=True, exist_ok=True)
    emission_cases = meta.get("recovery_emission_cases", [])
    sentinel_cases = meta.get("historical_sentinel_cases", [])
    missing_sentinels = meta.get("missing_historical_sentinels", [])

    subset_doc = docs_root / "P24_3_RECOVERY_EMISSION_SUBSET_AUDIT.md"
    subset_lines = [
        "# P24.3 Recovery Emission Subset Audit",
        "",
        "## Subset Rule",
        "- The run subset only contains rows with non-zero recovery-triggered activity or direct patch/emission failure signals.",
        "- Prefer three buckets: triggered-but-no-patch, patch-emitted-but-not-committed, and committed rows.",
        "- Historical sentinel cases are tracked separately to avoid mixing no-trigger baselines into the emission benchmark.",
        "",
        "## Recovery-Emission Cases",
    ]
    for record in emission_cases:
        subset_lines.append(
            f"- `{record['paper_id']}`: bucket={record['bucket']}, reasons={', '.join(record['reasons'])}, triggers={record['recovery_triggered_count']}, patch_mode={record['recovery_patch_mode_entered_count']}, emitted={record['patch_emitted_count']}, committed={record['patch_committed_count']}"
        )
    subset_lines.extend(["", "## Historical Sentinel Cases"])
    for record in sentinel_cases:
        subset_lines.append(
            f"- `{record['paper_id']}`: reasons={', '.join(record['reasons'])}, triggers={record['recovery_triggered_count']}, patch_mode={record['recovery_patch_mode_entered_count']}, emitted={record['patch_emitted_count']}, committed={record['patch_committed_count']}"
        )
    subset_lines.append("")
    subset_lines.append(f"- missing_historical_sentinels: {', '.join(missing_sentinels) or 'none'}")
    subset_doc.write_text("\n".join(subset_lines) + "\n", encoding="utf-8")

    protocol_doc = docs_root / "P24_3_PATCH_MODE_PROTOCOL.md"
    protocol_lines = [
        "# P24.3 Patch Mode Protocol",
        "",
        "## Hard Patch Mode",
        "- A turn enters `turn_mode = recovery_patch` whenever the manager action or effective action is `challenge_previous_hypothesis` or `request_evidence_recheck`.",
        "- In recovery patch mode, worker prompts switch to the recovery patch prompt regardless of the worker role label.",
        "- Allowed worker outputs are only `apply_recovery_patch` or `blocked`.",
        "- Ordinary evidence/critique/state-update payloads are stripped and converted into emission-failure bookkeeping instead of being merged into ReviewState.",
        "",
        "## Emission Diagnostics",
        "- `recovery_patch_mode_entered` records whether the turn actually switched into hard patch mode.",
        "- `recovery_emission_expected` records whether the turn should have emitted a patch.",
        "- `recovery_emitted` records whether an `apply_recovery_patch` payload was actually emitted.",
        "- `emission_failure_code` and `emission_failure_message` explain why a triggered turn still did not emit a patch.",
    ]
    protocol_doc.write_text("\n".join(protocol_lines) + "\n", encoding="utf-8")

    stage = analysis["stage_counts"]
    funnel_doc = docs_root / "P24_3_EMISSION_FUNNEL.md"
    funnel_lines = [
        "# P24.3 Emission Funnel",
        "",
        "## Turn-Level Funnel",
        "| Stage | Count |",
        "| --- | ---: |",
        f"| conflict_detected | {stage.get('conflict_detected', 0)} |",
        f"| recovery_triggered | {stage.get('recovery_triggered', 0)} |",
        f"| recovery_patch_mode_entered | {stage.get('recovery_patch_mode_entered', 0)} |",
        f"| patch_emitted | {stage.get('patch_emitted', 0)} |",
        f"| patch_validated | {stage.get('patch_validated', 0)} |",
        f"| patch_committed | {stage.get('patch_committed', 0)} |",
        "",
        "## Derived Rates",
        f"- trigger_to_patch_mode_rate: {analysis['trigger_to_patch_mode_rate']}",
        f"- patch_mode_to_emission_rate: {analysis['patch_mode_to_emission_rate']}",
        "",
        "## Row-Level Coverage",
        f"- recovery_triggered_rows: {analysis['row_stage_counts'].get('recovery_triggered_rows', 0)} / {analysis['rows']}",
        f"- recovery_patch_mode_entered_rows: {analysis['row_stage_counts'].get('recovery_patch_mode_entered_rows', 0)} / {analysis['rows']}",
        f"- patch_emitted_rows: {analysis['row_stage_counts'].get('patch_emitted_rows', 0)} / {analysis['rows']}",
        f"- patch_validated_rows: {analysis['row_stage_counts'].get('patch_validated_rows', 0)} / {analysis['rows']}",
        f"- patch_committed_rows: {analysis['row_stage_counts'].get('patch_committed_rows', 0)} / {analysis['rows']}",
    ]
    funnel_doc.write_text("\n".join(funnel_lines) + "\n", encoding="utf-8")

    failure_doc = docs_root / "P24_3_EMISSION_FAILURE_REPORT.md"
    top_failures = sorted(analysis["emission_failure_code_distribution"].items(), key=lambda kv: (-kv[1], kv[0]))
    failure_lines = [
        "# P24.3 Emission Failure Report",
        "",
        "## Distribution",
    ]
    for code, count in top_failures:
        failure_lines.append(f"- `{code}`: {count}")
    failure_lines.extend(["", "## Representative Cases"])
    for row in sorted(analysis["per_row"], key=lambda item: (-sum(item["emission_failure_code_counts"].values()), -item["recovery_triggered_count"], item["paper_id"]))[:5]:
        if not row["emission_failure_code_counts"]:
            continue
        failure_lines.append(
            f"- `{row['paper_id']}`: type={row['type']}, failures={json.dumps(row['emission_failure_code_counts'], ensure_ascii=False)}, triggers={row['recovery_triggered_count']}, patch_mode={row['recovery_patch_mode_entered_count']}, emitted={row['patch_emitted_count']}"
        )
    failure_doc.write_text("\n".join(failure_lines) + "\n", encoding="utf-8")

    semantics_doc = docs_root / "P24_3_ACTION_SEMANTICS_CLEANUP.md"
    top_combos = sorted(analysis["joint_semantics_counts"].items(), key=lambda kv: (-kv[1], kv[0]))[:15]
    semantics_lines = [
        "# P24.3 Action Semantics Cleanup",
        "",
        "## Top Joint Semantics",
    ]
    for combo, count in top_combos:
        semantics_lines.append(f"- `{combo}`: {count}")
    semantics_lines.extend([
        "",
        "## Source Distributions",
        f"- action_counts: {json.dumps(analysis['action_counts'], ensure_ascii=False)}",
        f"- effective_action_counts: {json.dumps(analysis['effective_action_counts'], ensure_ascii=False)}",
        f"- turn_mode_counts: {json.dumps(analysis['turn_mode_counts'], ensure_ascii=False)}",
        f"- policy_source_counts: {json.dumps(analysis['policy_source_counts'], ensure_ascii=False)}",
        f"- patch_source_counts: {json.dumps(analysis['patch_source_counts'], ensure_ascii=False)}",
    ])
    semantics_doc.write_text("\n".join(semantics_lines) + "\n", encoding="utf-8")

    go_doc = docs_root / "P24_3_GO_NO_GO.md"
    stage = analysis["stage_counts"]
    triggered = stage.get("recovery_triggered", 0)
    patch_mode = stage.get("recovery_patch_mode_entered", 0)
    emitted = stage.get("patch_emitted", 0)
    validated = stage.get("patch_validated", 0)
    committed = stage.get("patch_committed", 0)
    if analysis["patch_mode_to_emission_rate"] < 0.6:
        decision = "No-Go for 9B frozen comparison; continue 4B emission tuning."
        diagnosis = "The primary bottleneck is still patch emission after hard patch mode entry."
    elif emitted > 0 and validated < emitted:
        decision = "No-Go for 9B frozen comparison; emission improved, but validation is now the next bottleneck."
        diagnosis = "The bottleneck has shifted from emission into validation/commit."
    elif emitted > 0 and committed == 0:
        decision = "No-Go for 9B frozen comparison; patch emission exists, but commit is still not stable enough."
        diagnosis = "Emission is no longer zero, but commit throughput is still too weak."
    else:
        decision = "Conditional Go: emission is no longer the main bottleneck; validate with a frozen 9B comparison only if model-generated patches are no longer isolated cases."
        diagnosis = "Patch mode entry and patch emission are now reasonably aligned."
    go_lines = [
        "# P24.3 Go / No-Go",
        "",
        f"## Decision\n- {decision}",
        "",
        f"## Main Diagnosis\n- {diagnosis}",
        f"- turn funnel: triggered={triggered}, patch_mode={patch_mode}, emitted={emitted}, validated={validated}, committed={committed}",
        f"- trigger_to_patch_mode_rate={analysis['trigger_to_patch_mode_rate']}",
        f"- patch_mode_to_emission_rate={analysis['patch_mode_to_emission_rate']}",
        f"- model_generated_commit_count={analysis['model_generated_commit_count']}, salvaged_commit_count={analysis['salvaged_commit_count']}",
        "",
        "## Next Step",
        "- If patch_mode_to_emission_rate remains low, keep tuning 4B prompt/dispatch semantics.",
        "- If emission is healthy but validated/committed stay low, switch the next bounded pass to validator/commit analysis rather than more emission work.",
    ]
    go_doc.write_text("\n".join(go_lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate p24.3 patch-emission audit markdown files.")
    parser.add_argument("--subset-meta", default="outputs/review_infer/p24_3_recovery_emission_subset_meta.json")
    parser.add_argument("--run-results", default="outputs/review_infer/p24_3_4b_regression.jsonl")
    parser.add_argument("--analysis-json", default="outputs/review_infer/p24_3_4b_analysis.json")
    parser.add_argument("--docs-root", default=".")
    args = parser.parse_args()

    meta = json.loads(Path(args.subset_meta).read_text("utf-8"))
    rows = _load_jsonl(Path(args.run_results))
    analysis = analyze_run(rows)
    Path(args.analysis_json).write_text(json.dumps(analysis, ensure_ascii=False, indent=2), "utf-8")
    write_docs(meta, analysis, Path(args.docs_root))
    print(json.dumps(analysis, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
