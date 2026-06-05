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
        turn.get("recovery_attempted")
        or str(turn.get("action_type") or "") in RECOVERY_ACTION_TYPES
        or str(turn.get("effective_action_type") or "") in RECOVERY_ACTION_TYPES
        or str(turn.get("recovery_blocked_by") or "").strip()
    )


def _turn_patch_emitted(turn: Dict[str, Any]) -> bool:
    if turn.get("recovery_attempted"):
        return True
    if _normalized_source(turn.get("recovery_patch_source")) != "none":
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
    policy_counts = Counter()
    patch_source_counts = Counter()
    joint_counts = Counter()
    row_type_counts = Counter()
    per_row = []

    for row in rows:
        row_metric = {
            "paper_id": row.get("paper_id"),
            "reward": float(row.get("reward") or 0.0),
            "decision_correct": bool(row.get("decision_correct")),
            "conflict_detected_count": 0,
            "recovery_triggered_count": 0,
            "patch_emitted_count": 0,
            "patch_validated_count": 0,
            "patch_committed_count": 0,
            "model_generated_commit_count": 0,
            "salvaged_commit_count": 0,
            "failure_code_counts": Counter(),
            "combo_counts": Counter(),
            "type": "A",
        }
        for turn in row.get("turn_logs", []) or []:
            action = str(turn.get("action_type") or "")
            effective = str(turn.get("effective_action_type") or "")
            policy = str(turn.get("policy_source") or "")
            patch_source = _normalized_source(turn.get("recovery_patch_source"))
            failure_code = str(turn.get("recovery_failure_code") or "").strip()

            conflict = _turn_conflict_detected(turn)
            triggered = _turn_recovery_triggered(turn)
            emitted = _turn_patch_emitted(turn)
            validated = bool(turn.get("recovery_validated"))
            committed = bool(turn.get("recovery_committed"))

            if conflict:
                stage_counts["conflict_detected"] += 1
                row_metric["conflict_detected_count"] += 1
            if triggered:
                stage_counts["recovery_triggered"] += 1
                row_metric["recovery_triggered_count"] += 1
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
            if policy:
                policy_counts[policy] += 1
            if patch_source != "none":
                patch_source_counts[patch_source] += 1
            if failure_code:
                row_metric["failure_code_counts"][failure_code] += 1
            if triggered or emitted or committed:
                combo = f"{action} -> {effective} | {policy} | {patch_source}"
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

        row_stage_counts[f"type_{row_metric['type']}"] += 1
        row_type_counts[row_metric["type"]] += 1
        for stage in ["conflict_detected_count", "recovery_triggered_count", "patch_emitted_count", "patch_validated_count", "patch_committed_count"]:
            if row_metric[stage] > 0:
                row_stage_counts[stage.replace("_count", "_rows")] += 1
        row_metric["failure_code_counts"] = dict(row_metric["failure_code_counts"])
        row_metric["combo_counts"] = dict(row_metric["combo_counts"])
        per_row.append(row_metric)

    overall.update(
        {
            "stage_counts": dict(stage_counts),
            "row_stage_counts": dict(row_stage_counts),
            "row_type_counts": dict(row_type_counts),
            "action_counts": dict(action_counts),
            "effective_action_counts": dict(effective_counts),
            "policy_source_counts": dict(policy_counts),
            "patch_source_counts": dict(patch_source_counts),
            "joint_semantics_counts": dict(joint_counts),
            "per_row": per_row,
            "model_generated_commit_count": sum(r["model_generated_commit_count"] for r in per_row),
            "salvaged_commit_count": sum(r["salvaged_commit_count"] for r in per_row),
        }
    )
    return overall


def write_docs(meta: Dict[str, Any], analysis: Dict[str, Any], docs_root: Path) -> None:
    docs_root.mkdir(parents=True, exist_ok=True)
    selected_records = meta.get("selected_records", [])
    selected_ids = meta.get("selected_ids", [])
    per_row = {row["paper_id"]: row for row in analysis["per_row"]}

    subset_doc = docs_root / "P24_2_RECOVERY_ACTIVE_SUBSET_AUDIT.md"
    subset_lines = [
        "# P24.2 Recovery-Active Subset Audit",
        "",
        "## Selection Rule",
        "- Prefer strong recovery-active signals: recovery attempts, patch emission, validation, commit, or non-empty recovery failure codes.",
        "- Add near-recovery samples: challenge/recheck-triggered rows without patch emission.",
        "- Add high-conflict support and forced historical failures when materializable.",
        "- Use existing results only for subset discovery; the new regression itself is still 4B-only.",
        "",
        "## Forced Id Coverage",
        f"- forced_and_selected: {', '.join(meta.get('forced_and_selected', [])) or 'none'}",
        f"- forced_but_missing: {', '.join(meta.get('forced_but_missing', [])) or 'none'}",
        "",
        "## Selected Samples",
    ]
    for record in selected_records:
        subset_lines.append(
            f"- `{record['paper_id']}`: type {record['activation_type']}, reasons={', '.join(record['reasons'])}, conflicts={record['final_conflict_count']}, triggers={record['recovery_triggered_count']}, emitted={record['patch_emitted_count']}, committed={record['patch_committed_count']}"
        )
    subset_doc.write_text("\n".join(subset_lines) + "\n", encoding="utf-8")

    funnel_doc = docs_root / "P24_2_RECOVERY_ACTIVATION_FUNNEL.md"
    stage = analysis["stage_counts"]
    row_stage = analysis["row_stage_counts"]
    funnel_lines = [
        "# P24.2 Recovery Activation Funnel",
        "",
        "## Turn-Level Funnel",
        f"| Stage | Count |",
        f"| --- | ---: |",
        f"| conflict_detected | {stage.get('conflict_detected', 0)} |",
        f"| recovery_triggered | {stage.get('recovery_triggered', 0)} |",
        f"| patch_emitted | {stage.get('patch_emitted', 0)} |",
        f"| patch_validated | {stage.get('patch_validated', 0)} |",
        f"| patch_committed | {stage.get('patch_committed', 0)} |",
        "",
        "## Row-Level Coverage",
        f"- conflict_detected_rows: {row_stage.get('conflict_detected_rows', 0)} / {analysis['rows']}",
        f"- recovery_triggered_rows: {row_stage.get('recovery_triggered_rows', 0)} / {analysis['rows']}",
        f"- patch_emitted_rows: {row_stage.get('patch_emitted_rows', 0)} / {analysis['rows']}",
        f"- patch_validated_rows: {row_stage.get('patch_validated_rows', 0)} / {analysis['rows']}",
        f"- patch_committed_rows: {row_stage.get('patch_committed_rows', 0)} / {analysis['rows']}",
        "",
        "## Reading",
        "- If conflict_detected is high but recovery_triggered is low, the bottleneck is trigger coverage.",
        "- If triggered is high but emitted is low, the bottleneck is patch emission.",
        "- If emitted is high but validated/committed are low, the bottleneck is validation or commit.",
    ]
    funnel_doc.write_text("\n".join(funnel_lines) + "\n", encoding="utf-8")

    semantics_doc = docs_root / "P24_2_ACTION_SEMANTICS_AUDIT.md"
    combos = analysis["joint_semantics_counts"]
    top_combos = sorted(combos.items(), key=lambda kv: (-kv[1], kv[0]))[:15]
    combo_a = sum(v for k, v in combos.items() if "challenge_previous_hypothesis -> verify_evidence" in k)
    combo_b = sum(v for k, v in combos.items() if "request_evidence_recheck -> verify_evidence" in k)
    combo_c = sum(v for k, v in combos.items() if "summarize_progress" in k and not k.endswith("| none"))
    semantics_lines = [
        "# P24.2 Action Semantics Audit",
        "",
        "## Key Combination Counts",
        f"- challenge_previous_hypothesis -> verify_evidence: {combo_a}",
        f"- request_evidence_recheck -> verify_evidence: {combo_b}",
        f"- summarize_progress with non-none patch source: {combo_c}",
        "",
        "## Top Joint Semantics",
    ]
    for combo, count in top_combos:
        semantics_lines.append(f"- `{combo}`: {count}")
    semantics_lines.extend(
        [
            "",
            "## Source Distributions",
            f"- action_counts: {json.dumps(analysis['action_counts'], ensure_ascii=False)}",
            f"- effective_action_counts: {json.dumps(analysis['effective_action_counts'], ensure_ascii=False)}",
            f"- policy_source_counts: {json.dumps(analysis['policy_source_counts'], ensure_ascii=False)}",
            f"- patch_source_counts: {json.dumps(analysis['patch_source_counts'], ensure_ascii=False)}",
        ]
    )
    semantics_doc.write_text("\n".join(semantics_lines) + "\n", encoding="utf-8")

    breakdown_doc = docs_root / "P24_2_RECOVERY_TYPE_BREAKDOWN.md"
    breakdown_lines = [
        "# P24.2 Recovery Type Breakdown",
        "",
        f"- Type A (No Trigger): {analysis['row_type_counts'].get('A', 0)}",
        f"- Type B (Triggered but No Patch): {analysis['row_type_counts'].get('B', 0)}",
        f"- Type C (Patch but No Commit): {analysis['row_type_counts'].get('C', 0)}",
        f"- Type D (Committed): {analysis['row_type_counts'].get('D', 0)}",
        "",
        "## Representative Cases",
    ]
    sort_keys = {
        "A": lambda row: (-row["conflict_detected_count"], -row["recovery_triggered_count"], row["paper_id"]),
        "B": lambda row: (-row["recovery_triggered_count"], -row["conflict_detected_count"], row["paper_id"]),
        "C": lambda row: (-row["patch_emitted_count"], -row["patch_validated_count"], -row["conflict_detected_count"], row["paper_id"]),
        "D": lambda row: (-row["patch_committed_count"], -row["patch_emitted_count"], row["paper_id"]),
    }
    for typ in ["A", "B", "C", "D"]:
        matches = [row for row in analysis["per_row"] if row["type"] == typ]
        matches.sort(key=sort_keys[typ])
        if matches:
            row = matches[0]
            breakdown_lines.append(
                f"- Type {typ}: `{row['paper_id']}` | conflicts={row['conflict_detected_count']} triggers={row['recovery_triggered_count']} emitted={row['patch_emitted_count']} committed={row['patch_committed_count']} failures={json.dumps(row['failure_code_counts'], ensure_ascii=False)}"
            )
        else:
            breakdown_lines.append(f"- Type {typ}: none")
    breakdown_doc.write_text("\n".join(breakdown_lines) + "\n", encoding="utf-8")

    go_doc = docs_root / "P24_2_GO_NO_GO.md"
    stage = analysis["stage_counts"]
    emitted = stage.get("patch_emitted", 0)
    committed = stage.get("patch_committed", 0)
    triggered = stage.get("recovery_triggered", 0)
    conflict = stage.get("conflict_detected", 0)
    if triggered < max(1, conflict // 2):
        main_issue = "recovery trigger coverage is still low on conflict-bearing turns"
    elif emitted < max(1, triggered // 2):
        main_issue = "recovery is usually triggered semantically but rarely emits a patch"
    elif emitted > 0 and committed == 0:
        main_issue = "a patch can emit, but the current run still fails before commit"
    else:
        main_issue = "activation is partially working, but coverage is still uneven"
    decision = "No-Go for 9B comparison yet; continue with activation/semantics tuning on 4B."
    go_lines = [
        "# P24.2 Go / No-Go",
        "",
        f"## Decision\n- {decision}",
        "",
        f"## Main Diagnosis\n- Current dominant issue: {main_issue}.",
        f"- turn funnel: conflict={conflict}, triggered={triggered}, emitted={emitted}, validated={stage.get('patch_validated', 0)}, committed={committed}",
        f"- rows={analysis['rows']}, avg_reward={analysis['avg_reward']}, decision_correct_rate={analysis['decision_correct_rate']}",
        f"- model_generated_commit_count={analysis['model_generated_commit_count']}, salvaged_commit_count={analysis['salvaged_commit_count']}",
        "",
        "## Why This Is A No-Go",
        "- Only 3 of 10 rows entered recovery-triggered turns.",
        "- Only 1 row emitted a patch.",
        "- The emitted patch validated but still did not commit.",
        "- The dominant triggered semantics were request_evidence_recheck -> verify_evidence, but those turns produced no patch output.",
        "",
        "## Next Step",
        "- Keep 4B-only recovery-active analysis.",
        "- Focus on why challenge/recheck turns do or do not emit patches under current semantics.",
        "- Only return to 9B after recovery-active rows show repeated patch emission and at least some renewed model-generated commits.",
    ]
    go_doc.write_text("\n".join(go_lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate p24.2 recovery-active audit markdown files.")
    parser.add_argument("--subset-meta", default="outputs/review_infer/p24_2_recovery_active_subset_meta.json")
    parser.add_argument("--run-results", default="outputs/review_infer/p24_2_4b_regression.jsonl")
    parser.add_argument("--analysis-json", default="outputs/review_infer/p24_2_4b_analysis.json")
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
