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
    failure_code_counts = Counter()
    joint_counts = Counter()
    per_row = []

    for row in rows:
        row_metric = {
            "paper_id": row.get("paper_id"),
            "reward": float(row.get("reward") or 0.0),
            "decision_correct": bool(row.get("decision_correct")),
            "conflict_detected_count": 0,
            "recovery_relevant_count": 1,
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
            "has_conflict": False,
            "has_triggered": False,
            "has_patch_mode": False,
            "has_emitted": False,
            "has_validated": False,
            "has_committed": False,
            "type": "A",
        }
        row_stage_counts["recovery_relevant_rows"] += 1

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

            stage_counts["recovery_relevant"] += 1
            if conflict:
                stage_counts["conflict_detected"] += 1
                row_metric["conflict_detected_count"] += 1
                row_metric["has_conflict"] = True
            if triggered:
                stage_counts["recovery_triggered"] += 1
                row_metric["recovery_triggered_count"] += 1
                row_metric["has_triggered"] = True
            if patch_mode:
                stage_counts["recovery_patch_mode_entered"] += 1
                row_metric["recovery_patch_mode_entered_count"] += 1
                row_metric["has_patch_mode"] = True
            if emitted:
                stage_counts["patch_emitted"] += 1
                row_metric["patch_emitted_count"] += 1
                row_metric["has_emitted"] = True
            if validated:
                stage_counts["patch_validated"] += 1
                row_metric["patch_validated_count"] += 1
                row_metric["has_validated"] = True
            if committed:
                stage_counts["patch_committed"] += 1
                row_metric["patch_committed_count"] += 1
                row_metric["has_committed"] = True
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
                failure_code_counts[recovery_failure] += 1
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

        if row_metric["has_conflict"]:
            row_stage_counts["conflict_detected_rows"] += 1
        if row_metric["has_triggered"]:
            row_stage_counts["recovery_triggered_rows"] += 1
        if row_metric["has_patch_mode"]:
            row_stage_counts["recovery_patch_mode_entered_rows"] += 1
        if row_metric["has_emitted"]:
            row_stage_counts["patch_emitted_rows"] += 1
        if row_metric["has_validated"]:
            row_stage_counts["patch_validated_rows"] += 1
        if row_metric["has_committed"]:
            row_stage_counts["patch_committed_rows"] += 1
        if row_metric["has_emitted"] and row_metric["has_validated"]:
            row_stage_counts["emitted_and_validated_rows"] += 1
        if row_metric["has_validated"] and row_metric["has_committed"]:
            row_stage_counts["validated_and_committed_rows"] += 1
        row_stage_counts[f"type_{row_metric['type']}"] += 1
        row_metric["emission_failure_code_counts"] = dict(row_metric["emission_failure_code_counts"])
        row_metric["failure_code_counts"] = dict(row_metric["failure_code_counts"])
        row_metric["combo_counts"] = dict(row_metric["combo_counts"])
        per_row.append(row_metric)

    stage_counts_dict = dict(stage_counts)
    relevant_rows = row_stage_counts.get("recovery_relevant_rows", 0)
    triggered_rows = row_stage_counts.get("recovery_triggered_rows", 0)
    patch_mode_rows = row_stage_counts.get("recovery_patch_mode_entered_rows", 0)
    emitted_rows = row_stage_counts.get("patch_emitted_rows", 0)
    validated_rows = row_stage_counts.get("patch_validated_rows", 0)
    emitted_and_validated_rows = row_stage_counts.get("emitted_and_validated_rows", 0)
    validated_and_committed_rows = row_stage_counts.get("validated_and_committed_rows", 0)
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
            "failure_code_distribution": dict(failure_code_counts),
            "joint_semantics_counts": dict(joint_counts),
            "per_row": per_row,
            "model_generated_commit_count": sum(r["model_generated_commit_count"] for r in per_row),
            "salvaged_commit_count": sum(r["salvaged_commit_count"] for r in per_row),
            "recovery_relevant_to_trigger_rate": round(triggered_rows / max(relevant_rows, 1), 4),
            "trigger_to_patch_mode_rate": round(patch_mode_rows / max(triggered_rows, 1), 4),
            "patch_mode_to_emission_rate": round(emitted_rows / max(patch_mode_rows, 1), 4),
            "emission_to_validation_rate": round(emitted_and_validated_rows / max(emitted_rows, 1), 4),
            "validation_to_commit_rate": round(validated_and_committed_rows / max(validated_rows, 1), 4),
        }
    )
    return overall


def _bullet_list(records: List[Dict[str, Any]], mode: str) -> List[str]:
    lines: List[str] = []
    for record in records:
        lines.append(
            f"- `{record['paper_id']}`: activation={record.get('activation_type', record.get('bucket', 'unknown'))}, reasons={', '.join(record.get('reasons', [])) or 'none'}, conflicts={record.get('conflict_detected_count', 0)}, triggers={record.get('recovery_triggered_count', 0)}, patch_mode={record.get('recovery_patch_mode_entered_count', 0)}, emitted={record.get('patch_emitted_count', 0)}, committed={record.get('patch_committed_count', 0)}, sources={', '.join(record.get('sources', [])) if mode == 'meta' else 'run row' }"
        )
    return lines


def write_docs(meta: Dict[str, Any], analysis: Dict[str, Any], docs_root: Path) -> None:
    recovery_cases = meta.get("recovery_relevant_cases", [])
    sentinel_cases = meta.get("historical_sentinel_cases", [])
    missing_sentinels = meta.get("missing_historical_sentinels", [])
    stage = analysis["stage_counts"]

    (docs_root / "P24_4_DIRECTION_NOTE.md").write_text(
        "# P24.4 Direction Note\n\nCurrent priority has shifted from recovery commit/checker debugging to activation and patch-emission stabilization. The bounded objective of p24.4 is to make recovery-relevant samples re-enter recovery more consistently, force triggered turns into explicit `recovery_patch` mode, and measure whether patch emission becomes a stable rather than incidental behavior.\n",
        encoding="utf-8",
    )

    hist_lines = [
        "# P24.4 Historical Sentinel Subset",
        "",
        "Historical sentinels are retained to detect drift on known hard cases. They are not required to trigger recovery on every rerun.",
        "",
        "## Cases",
        *_bullet_list(sentinel_cases, "meta"),
        "",
        f"- missing_historical_sentinels: {', '.join(missing_sentinels) or 'none'}",
    ]
    (docs_root / "P24_4_HISTORICAL_SENTINEL_SUBSET.md").write_text("\n".join(hist_lines) + "\n", encoding="utf-8")

    relevant_lines = [
        "# P24.4 Recovery Relevant Subset",
        "",
        "Recovery-relevant cases are used to test activation and emission only. No-trigger baseline rows should not dominate this set.",
        "",
        "## Selection Rule",
        "- historical recovery_attempted > 0, or",
        "- historical recovery_triggered > 0, or",
        "- recovery_patch_source != none, or",
        "- recovery_failure_code non-empty, or",
        "- challenge_previous_hypothesis / request_evidence_recheck appeared in recovery-related chains.",
        "",
        "## Cases",
        *_bullet_list(recovery_cases, "meta"),
    ]
    (docs_root / "P24_4_RECOVERY_RELEVANT_SUBSET.md").write_text("\n".join(relevant_lines) + "\n", encoding="utf-8")

    bias_lines = [
        "# P24.4 Manager Recovery Bias",
        "",
        "Sticky recovery bias keeps recovery-relevant rows from drifting back to plain evidence or summary mode too early.",
        "",
        "## Trigger Conditions",
        "- state.recovery_relevant is true",
        "- conflict_notes exists",
        "- recovery_blocked_by exists",
        "- latest patch log has recovery_failure_code",
        "- previous turn entered recovery_patch mode but emitted no patch",
        "",
        "## Bias Rule",
        "- prefer `challenge_previous_hypothesis` when unresolved conflicts remain or a prior recovery turn failed to emit",
        "- prefer `request_evidence_recheck` when evidence is weak/missing but the row remains recovery-relevant",
        "- avoid drifting to `summarize_progress` or plain continue while the row is still recovery-relevant",
    ]
    (docs_root / "P24_4_MANAGER_RECOVERY_BIAS.md").write_text("\n".join(bias_lines) + "\n", encoding="utf-8")

    turn_mode_lines = [
        "# P24.4 Turn Mode Protocol",
        "",
        "Two explicit internal turn modes are now used:",
        "- `normal_evidence`: ordinary evidence verification / critique work",
        "- `recovery_patch`: bounded recovery patch generation turn",
        "",
        "## Switch Rule",
        "- once recovery is triggered, the turn must enter `recovery_patch` mode rather than relying on verify_evidence as a side effect",
        "- in `recovery_patch` mode, worker prompts switch to the recovery patch prompt",
        "",
        "## Allowed Outputs In Recovery Patch Mode",
        "- `apply_recovery_patch` JSON",
        "- `blocked` JSON",
        "",
        "## Forbidden Outputs",
        "- ordinary evidence prose",
        "- critique paragraphs",
        "- review-style free text",
        "- mixed prose plus malformed JSON",
    ]
    (docs_root / "P24_4_TURN_MODE_PROTOCOL.md").write_text("\n".join(turn_mode_lines) + "\n", encoding="utf-8")

    funnel_lines = [
        "# P24.4 Emission Funnel",
        "",
        "## Turn-Level Funnel",
        "| Stage | Count |",
        "| --- | ---: |",
        f"| conflict_detected | {stage.get('conflict_detected', 0)} |",
        f"| recovery_relevant | {stage.get('recovery_relevant', 0)} |",
        f"| recovery_triggered | {stage.get('recovery_triggered', 0)} |",
        f"| recovery_patch_mode_entered | {stage.get('recovery_patch_mode_entered', 0)} |",
        f"| patch_emitted | {stage.get('patch_emitted', 0)} |",
        f"| patch_validated | {stage.get('patch_validated', 0)} |",
        f"| patch_committed | {stage.get('patch_committed', 0)} |",
        "",
        "## Row-Level Rates",
        f"- recovery_relevant_to_trigger_rate: {analysis['recovery_relevant_to_trigger_rate']}",
        f"- trigger_to_patch_mode_rate: {analysis['trigger_to_patch_mode_rate']}",
        f"- patch_mode_to_emission_rate: {analysis['patch_mode_to_emission_rate']}",
        f"- emission_to_validation_rate: {analysis['emission_to_validation_rate']}",
        f"- validation_to_commit_rate: {analysis['validation_to_commit_rate']}",
        "",
        "## Row Coverage",
    ]
    for key, value in sorted(analysis["row_stage_counts"].items()):
        funnel_lines.append(f"- {key}: {value}")
    (docs_root / "P24_4_EMISSION_FUNNEL.md").write_text("\n".join(funnel_lines) + "\n", encoding="utf-8")

    failure_lines = [
        "# P24.4 Emission Failure Report",
        "",
        "## Emission Failure Codes",
    ]
    emission_failures = analysis["emission_failure_code_distribution"]
    if emission_failures:
        for key, value in sorted(emission_failures.items(), key=lambda item: (-item[1], item[0])):
            failure_lines.append(f"- {key}: {value}")
    else:
        failure_lines.append("- none")
    failure_lines.extend(["", "## Recovery Failure Codes"])
    recovery_failures = analysis["failure_code_distribution"]
    if recovery_failures:
        for key, value in sorted(recovery_failures.items(), key=lambda item: (-item[1], item[0])):
            failure_lines.append(f"- {key}: {value}")
    else:
        failure_lines.append("- none")
    failure_lines.extend(["", "## Representative Rows"])
    for row in sorted(analysis["per_row"], key=lambda r: (r["type"], -r["recovery_triggered_count"], r["paper_id"])):
        if row["type"] in {"B", "C", "D"}:
            failure_lines.append(
                f"- `{row['paper_id']}`: type={row['type']}, triggers={row['recovery_triggered_count']}, patch_mode={row['recovery_patch_mode_entered_count']}, emitted={row['patch_emitted_count']}, committed={row['patch_committed_count']}, emission_failures={row['emission_failure_code_counts'] or 'none'}, recovery_failures={row['failure_code_counts'] or 'none'}"
            )
    (docs_root / "P24_4_EMISSION_FAILURE_REPORT.md").write_text("\n".join(failure_lines) + "\n", encoding="utf-8")

    go_lines = [
        "# P24.4 Go / No-Go",
        "",
        f"- rows: {analysis['rows']}",
        f"- avg_reward: {analysis['avg_reward']}",
        f"- decision_correct_rate: {analysis['decision_correct_rate']}",
        f"- recovery_relevant_to_trigger_rate: {analysis['recovery_relevant_to_trigger_rate']}",
        f"- trigger_to_patch_mode_rate: {analysis['trigger_to_patch_mode_rate']}",
        f"- patch_mode_to_emission_rate: {analysis['patch_mode_to_emission_rate']}",
        f"- emission_to_validation_rate: {analysis['emission_to_validation_rate']}",
        f"- validation_to_commit_rate: {analysis['validation_to_commit_rate']}",
        "",
    ]
    if analysis["patch_mode_to_emission_rate"] >= 0.6 and analysis["trigger_to_patch_mode_rate"] >= 0.8:
        go_lines.append("Current judgment: GO for frozen 9B comparison preparation. Activation and emission are no longer the dominant blocker.")
    else:
        go_lines.append("Current judgment: NO-GO for 9B. Continue bounded 4B activation/emission stabilization; patch emission is still the bottleneck.")
    go_lines.extend(
        [
            "",
            "## Main Reading",
            "- If recovery_relevant rows still fail to trigger, manager activation bias remains too weak.",
            "- If triggered rows enter patch mode but emission remains low, worker prompt adherence remains the primary blocker.",
            "- Validation and commit matter only after emission stops being sparse.",
        ]
    )
    (docs_root / "P24_4_GO_NO_GO.md").write_text("\n".join(go_lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--result-path", required=True)
    parser.add_argument("--meta-path", required=True)
    parser.add_argument("--docs-root", default=".")
    parser.add_argument("--analysis-path", default="outputs/review_infer/p24_4_analysis.json")
    args = parser.parse_args()

    rows = _load_jsonl(Path(args.result_path))
    meta = json.loads(Path(args.meta_path).read_text("utf-8"))
    analysis = analyze_run(rows)
    Path(args.analysis_path).write_text(json.dumps(analysis, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_docs(meta, analysis, Path(args.docs_root))


if __name__ == "__main__":
    main()
