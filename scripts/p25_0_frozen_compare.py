from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from statistics import median
from typing import Any, Dict, Iterable, List, Tuple

RECOVERY_ACTION_TYPES = {"challenge_previous_hypothesis", "request_evidence_recheck"}


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    return [json.loads(line) for line in path.read_text("utf-8").splitlines() if line.strip()]


def normalized_source(value: Any) -> str:
    text = str(value or "none").strip().lower()
    return text or "none"


def turn_conflict_detected(turn: Dict[str, Any]) -> bool:
    return bool(turn.get("conflicts_detected") or turn.get("conflict_summary") or turn.get("conflict_events"))


def turn_recovery_triggered(turn: Dict[str, Any]) -> bool:
    return bool(
        turn.get("recovery_patch_mode_entered")
        or turn.get("recovery_emission_expected")
        or turn.get("recovery_attempted")
        or str(turn.get("action_type") or "") in RECOVERY_ACTION_TYPES
        or str(turn.get("effective_action_type") or "") in RECOVERY_ACTION_TYPES
        or str(turn.get("recovery_blocked_by") or "").strip()
        or str(turn.get("emission_failure_code") or "").strip()
    )


def turn_patch_mode_entered(turn: Dict[str, Any]) -> bool:
    if "recovery_patch_mode_entered" in turn:
        return bool(turn.get("recovery_patch_mode_entered"))
    return str(turn.get("turn_mode") or "") == "recovery_patch"


def turn_patch_emitted(turn: Dict[str, Any]) -> bool:
    if "recovery_emitted" in turn:
        return bool(turn.get("recovery_emitted"))
    if normalized_source(turn.get("recovery_patch_source")) != "none":
        return True
    if turn.get("recovery_attempted") and turn.get("recovery_target_id"):
        return True
    for worker in turn.get("worker_payloads") or []:
        payload = worker.get("payload") or {}
        if payload.get("action") == "apply_recovery_patch":
            return True
    return False


def turn_attempted(turn: Dict[str, Any]) -> bool:
    return bool(
        turn_patch_emitted(turn)
        or turn.get("recovery_attempted")
        or turn.get("recovery_validated")
        or turn.get("recovery_committed")
        or str(turn.get("recovery_failure_code") or "").strip()
        or turn_patch_mode_entered(turn)
    )


def summarize_row(row: Dict[str, Any]) -> Dict[str, Any]:
    turns = row.get("turn_logs", []) or []
    summary = {
        "paper_id": row.get("paper_id"),
        "reward": float(row.get("reward") or 0.0),
        "decision_correct": bool(row.get("decision_correct")),
        "recovery_triggered_count": 0,
        "recovery_patch_mode_entered_count": 0,
        "patch_emitted_count": 0,
        "patch_validated_count": 0,
        "patch_committed_count": 0,
        "model_generated_commit_count": 0,
        "salvaged_commit_count": 0,
        "failure_code_counts": Counter(),
        "failure_code_counts_emitted": Counter(),
        "state_change_counts": Counter(),
        "state_change_by_type": Counter(),
        "top_failure": "none",
        "has_conflict": False,
        "has_triggered": False,
        "has_patch_mode": False,
        "has_emitted": False,
        "has_validated": False,
        "has_committed": False,
        "has_model_generated_commit": False,
        "has_salvaged_commit": False,
    }

    for turn in turns:
        failure_code = str(turn.get("recovery_failure_code") or "").strip()
        patch_source = normalized_source(turn.get("recovery_patch_source"))
        triggered = turn_recovery_triggered(turn)
        patch_mode = turn_patch_mode_entered(turn)
        emitted = turn_patch_emitted(turn)
        validated = bool(turn.get("recovery_validated"))
        committed = bool(turn.get("recovery_committed"))

        if turn_conflict_detected(turn):
            summary["has_conflict"] = True
        if triggered:
            summary["has_triggered"] = True
            summary["recovery_triggered_count"] += 1
        if patch_mode:
            summary["has_patch_mode"] = True
            summary["recovery_patch_mode_entered_count"] += 1
        if emitted:
            summary["has_emitted"] = True
            summary["patch_emitted_count"] += 1
        if validated:
            summary["has_validated"] = True
            summary["patch_validated_count"] += 1
        if committed:
            summary["has_committed"] = True
            summary["patch_committed_count"] += 1
            if patch_source == "model_generated":
                summary["model_generated_commit_count"] += 1
                summary["has_model_generated_commit"] = True
            elif patch_source == "salvaged":
                summary["salvaged_commit_count"] += 1
                summary["has_salvaged_commit"] = True

        if turn_attempted(turn) and failure_code:
            summary["failure_code_counts"][failure_code] += 1
        if emitted and failure_code:
            summary["failure_code_counts_emitted"][failure_code] += 1

        if committed:
            target_type = str(turn.get("recovery_target_type") or "unknown")
            old_status = str(turn.get("old_status") or "")
            new_status = str(turn.get("new_status") or "")
            if old_status and new_status and old_status != new_status:
                transition = f"{old_status} -> {new_status}"
                summary["state_change_counts"][transition] += 1
                summary["state_change_by_type"][f"{target_type}: {transition}"] += 1

    non_success = {k: v for k, v in summary["failure_code_counts"].items() if k != "SUCCESS"}
    if non_success:
        summary["top_failure"] = max(non_success.items(), key=lambda item: (item[1], item[0]))[0]
    elif summary["failure_code_counts"]:
        summary["top_failure"] = max(summary["failure_code_counts"].items(), key=lambda item: (item[1], item[0]))[0]

    summary["failure_code_counts"] = dict(summary["failure_code_counts"])
    summary["failure_code_counts_emitted"] = dict(summary["failure_code_counts_emitted"])
    summary["state_change_counts"] = dict(summary["state_change_counts"])
    summary["state_change_by_type"] = dict(summary["state_change_by_type"])
    return summary


def analyze_model(rows: List[Dict[str, Any]], subset_ids: Iterable[str]) -> Dict[str, Any]:
    subset_ids = list(subset_ids)
    subset = [row for row in rows if row.get("paper_id") in subset_ids]
    per_row = {row["paper_id"]: summarize_row(row) for row in subset}
    rewards = [summary["reward"] for summary in per_row.values()]
    decision_correct = sum(1 for summary in per_row.values() if summary["decision_correct"])

    row_counts = {
        "recovery_relevant_count": len(subset_ids),
        "recovery_triggered_count": sum(1 for summary in per_row.values() if summary["has_triggered"]),
        "recovery_patch_mode_entered_count": sum(1 for summary in per_row.values() if summary["has_patch_mode"]),
        "patch_emitted_count": sum(1 for summary in per_row.values() if summary["has_emitted"]),
        "patch_validated_count": sum(1 for summary in per_row.values() if summary["has_validated"]),
        "patch_committed_count": sum(1 for summary in per_row.values() if summary["has_committed"]),
    }

    failure_code_counts = Counter()
    failure_code_counts_emitted = Counter()
    state_change_by_type = Counter()
    state_change_by_target = Counter()
    emitted_turns = 0
    validated_turns = 0
    committed_turns = 0
    for summary in per_row.values():
        failure_code_counts.update(summary["failure_code_counts"])
        failure_code_counts_emitted.update(summary["failure_code_counts_emitted"])
        emitted_turns += summary["patch_emitted_count"]
        validated_turns += summary["patch_validated_count"]
        committed_turns += summary["patch_committed_count"]
        for transition, count in summary["state_change_by_type"].items():
            state_change_by_type[transition] += count
            target_type = transition.split(":", 1)[0]
            state_change_by_target[target_type] += count

    outcomes = {
        "rows_with_any_commit": row_counts["patch_committed_count"],
        "rows_with_model_generated_commit": sum(1 for summary in per_row.values() if summary["has_model_generated_commit"]),
        "rows_with_only_salvaged_commit": sum(1 for summary in per_row.values() if summary["has_salvaged_commit"] and not summary["has_model_generated_commit"]),
        "rows_with_no_commit": sum(1 for summary in per_row.values() if not summary["has_committed"]),
        "rows_with_successful_recovery_and_correct_decision": sum(1 for summary in per_row.values() if summary["has_committed"] and summary["decision_correct"]),
    }

    return {
        "rows": len(subset),
        "avg_reward": round(sum(rewards) / max(len(rewards), 1), 4),
        "median_reward": round(median(rewards) if rewards else 0.0, 4),
        "decision_correct_rate": round(decision_correct / max(len(subset), 1), 4),
        "row_counts": row_counts,
        "rates": {
            "recovery_relevant_to_trigger_rate": round(row_counts["recovery_triggered_count"] / max(row_counts["recovery_relevant_count"], 1), 4),
            "trigger_to_patch_mode_rate": round(row_counts["recovery_patch_mode_entered_count"] / max(row_counts["recovery_triggered_count"], 1), 4),
            "patch_mode_to_emission_rate": round(row_counts["patch_emitted_count"] / max(row_counts["recovery_patch_mode_entered_count"], 1), 4),
            "emission_to_validation_rate": round(row_counts["patch_validated_count"] / max(row_counts["patch_emitted_count"], 1), 4),
            "validation_to_commit_rate": round(row_counts["patch_committed_count"] / max(row_counts["patch_validated_count"], 1), 4),
        },
        "failure_code_counts": dict(failure_code_counts),
        "failure_code_counts_emitted": dict(failure_code_counts_emitted),
        "effectiveness": {
            "emitted_turns": emitted_turns,
            "validated_turns": validated_turns,
            "committed_turns": committed_turns,
            "success_rate_among_emitted": round(failure_code_counts_emitted.get("SUCCESS", 0) / max(emitted_turns, 1), 4),
            "no_effect_rate_among_emitted": round(failure_code_counts_emitted.get("NO_EFFECT_PATCH", 0) / max(emitted_turns, 1), 4),
            "blocked_rate_among_emitted": round(failure_code_counts_emitted.get("BLOCKED_BY_POLICY", 0) / max(emitted_turns, 1), 4),
        },
        "state_change_by_type": dict(state_change_by_type),
        "state_change_by_target": dict(state_change_by_target),
        "outcomes": outcomes,
        "per_row": per_row,
    }


def pairwise_table(rows_4b: Dict[str, Any], rows_9b: Dict[str, Any], bucket_map: Dict[str, str]) -> List[Dict[str, Any]]:
    paper_ids = sorted(set(rows_4b) | set(rows_9b))
    table = []
    for paper_id in paper_ids:
        left = rows_4b.get(paper_id, {})
        right = rows_9b.get(paper_id, {})
        note = []
        if left.get("patch_committed_count", 0) == 0 and right.get("patch_committed_count", 0) > 0:
            note.append("9B unlocks commit")
        if left.get("top_failure") == "NO_EFFECT_PATCH" and right.get("patch_committed_count", 0) > left.get("patch_committed_count", 0):
            note.append("9B reduces no-effect")
        if left.get("top_failure") == "BLOCKED_BY_POLICY" and right.get("patch_committed_count", 0) > left.get("patch_committed_count", 0):
            note.append("9B escapes policy block")
        if right.get("reward", 0) > left.get("reward", 0) and right.get("patch_committed_count", 0) <= left.get("patch_committed_count", 0):
            note.append("reward up without better patch quality")
        if not note:
            note.append("stable")
        table.append(
            {
                "paper_id": paper_id,
                "bucket": bucket_map.get(paper_id, "unknown"),
                "4b_emitted": left.get("patch_emitted_count", 0),
                "9b_emitted": right.get("patch_emitted_count", 0),
                "4b_committed": left.get("patch_committed_count", 0),
                "9b_committed": right.get("patch_committed_count", 0),
                "4b_failure_top": left.get("top_failure", "none"),
                "9b_failure_top": right.get("top_failure", "none"),
                "4b_reward": round(float(left.get("reward", 0.0)), 4),
                "9b_reward": round(float(right.get("reward", 0.0)), 4),
                "notes": "; ".join(note),
            }
        )
    return table


def format_compare_table(title: str, left: Dict[str, Any], right: Dict[str, Any], keys: List[Tuple[str, str]]) -> str:
    lines = [f"# {title}", "", "| Metric | 4B | 9B |", "| --- | ---: | ---: |"]
    for label, key in keys:
        lines.append(f"| {label} | {left[key]} | {right[key]} |")
    return "\n".join(lines) + "\n"


def write_docs(docs_root: Path, setup: Dict[str, Any], main_4b: Dict[str, Any], main_9b: Dict[str, Any], sentinel_4b: Dict[str, Any], sentinel_9b: Dict[str, Any], pairwise: List[Dict[str, Any]]) -> None:
    docs_root.mkdir(parents=True, exist_ok=True)

    setup_lines = [
        "# P25.0 Frozen Compare Setup",
        "",
        f"- frozen_commit: `{setup['frozen_commit']}`",
        f"- compare_subset: `{setup['subset_path']}`",
        f"- recovery_relevant_count: {setup['recovery_relevant_count']}",
        f"- historical_sentinel_count: {setup['historical_sentinel_count']}",
        f"- 4B model: `{setup['models']['4b']}`",
        f"- 9B model: `{setup['models']['9b']}`",
        "",
        "## Frozen Parameters",
    ]
    for key, value in setup["fixed_params"].items():
        setup_lines.append(f"- {key}: {value}")
    setup_lines.extend([
        "",
        "## Freeze Rule",
        "- manager policy, prompt, turn mode, validator, lifecycle and logging are held fixed.",
        "- the only intended experimental variable is the model path: 4B vs 9B.",
    ])
    (docs_root / 'P25_0_FROZEN_COMPARE_SETUP.md').write_text("\n".join(setup_lines) + "\n", encoding='utf-8')

    funnel_lines = [
        "# P25.0 Funnel Compare",
        "",
        "## Recovery-Relevant Rows",
        "| Metric | 4B | 9B |",
        "| --- | ---: | ---: |",
    ]
    for key in [
        'recovery_relevant_count','recovery_triggered_count','recovery_patch_mode_entered_count','patch_emitted_count','patch_validated_count','patch_committed_count'
    ]:
        funnel_lines.append(f"| {key} | {main_4b['row_counts'][key]} | {main_9b['row_counts'][key]} |")
    funnel_lines.extend(["", "## Recovery-Relevant Rates", "| Metric | 4B | 9B |", "| --- | ---: | ---: |"])
    for key, label in [
        ('recovery_relevant_to_trigger_rate','recovery_relevant_to_trigger_rate'),
        ('trigger_to_patch_mode_rate','trigger_to_patch_mode_rate'),
        ('patch_mode_to_emission_rate','patch_mode_to_emission_rate'),
        ('emission_to_validation_rate','emission_to_validation_rate'),
        ('validation_to_commit_rate','validation_to_commit_rate'),
    ]:
        funnel_lines.append(f"| {label} | {main_4b['rates'][key]} | {main_9b['rates'][key]} |")
    funnel_lines.extend(["", "## Historical Sentinel Rows", "| Metric | 4B | 9B |", "| --- | ---: | ---: |"])
    for key in [
        'recovery_relevant_count','recovery_triggered_count','recovery_patch_mode_entered_count','patch_emitted_count','patch_validated_count','patch_committed_count'
    ]:
        funnel_lines.append(f"| {key} | {sentinel_4b['row_counts'][key]} | {sentinel_9b['row_counts'][key]} |")
    (docs_root / 'P25_0_FUNNEL_COMPARE.md').write_text("\n".join(funnel_lines) + "\n", encoding='utf-8')

    pe_lines = [
        "# P25.0 Patch Effectiveness Compare",
        "",
        "## Recovery-Relevant Failure Codes (attempt-level)",
        "| Failure Code | 4B | 9B |",
        "| --- | ---: | ---: |",
    ]
    all_failure_codes = sorted(set(main_4b['failure_code_counts']) | set(main_9b['failure_code_counts']))
    for code in all_failure_codes:
        pe_lines.append(f"| {code} | {main_4b['failure_code_counts'].get(code, 0)} | {main_9b['failure_code_counts'].get(code, 0)} |")
    pe_lines.extend(["", "## Rates Among Emitted Recovery Patches", "| Metric | 4B | 9B |", "| --- | ---: | ---: |"])
    for key in ['success_rate_among_emitted','no_effect_rate_among_emitted','blocked_rate_among_emitted']:
        pe_lines.append(f"| {key} | {main_4b['effectiveness'][key]} | {main_9b['effectiveness'][key]} |")
    pe_lines.extend(["", "## Emitted / Validated / Committed Turns", "| Metric | 4B | 9B |", "| --- | ---: | ---: |"])
    for key in ['emitted_turns','validated_turns','committed_turns']:
        pe_lines.append(f"| {key} | {main_4b['effectiveness'][key]} | {main_9b['effectiveness'][key]} |")
    (docs_root / 'P25_0_PATCH_EFFECTIVENESS_COMPARE.md').write_text("\n".join(pe_lines) + "\n", encoding='utf-8')

    sc_lines = [
        "# P25.0 State Change Compare",
        "",
        "## State Change Counts By Target Type (recovery-relevant rows)",
        "| Target Type | 4B | 9B |",
        "| --- | ---: | ---: |",
    ]
    target_types = sorted(set(main_4b['state_change_by_target']) | set(main_9b['state_change_by_target']))
    for target in target_types:
        sc_lines.append(f"| {target} | {main_4b['state_change_by_target'].get(target, 0)} | {main_9b['state_change_by_target'].get(target, 0)} |")
    sc_lines.extend(["", "## Transition Detail", "| Transition | 4B | 9B |", "| --- | ---: | ---: |"])
    transitions = sorted(set(main_4b['state_change_by_type']) | set(main_9b['state_change_by_type']))
    for transition in transitions:
        sc_lines.append(f"| {transition} | {main_4b['state_change_by_type'].get(transition, 0)} | {main_9b['state_change_by_type'].get(transition, 0)} |")
    (docs_root / 'P25_0_STATE_CHANGE_COMPARE.md').write_text("\n".join(sc_lines) + "\n", encoding='utf-8')

    pair_lines = [
        "# P25.0 Pairwise Case Table",
        "",
        "| paper_id | bucket | 4B emitted | 9B emitted | 4B committed | 9B committed | 4B failure top | 9B failure top | 4B reward | 9B reward | notes |",
        "| --- | --- | ---: | ---: | ---: | ---: | --- | --- | ---: | ---: | --- |",
    ]
    for row in pairwise:
        pair_lines.append(
            f"| {row['paper_id']} | {row['bucket']} | {row['4b_emitted']} | {row['9b_emitted']} | {row['4b_committed']} | {row['9b_committed']} | {row['4b_failure_top']} | {row['9b_failure_top']} | {row['4b_reward']} | {row['9b_reward']} | {row['notes']} |"
        )
    (docs_root / 'P25_0_PAIRWISE_CASE_TABLE.md').write_text("\n".join(pair_lines) + "\n", encoding='utf-8')

    def find_case(predicate):
        for row in pairwise:
            if predicate(row):
                return row
        return None

    cases = {
        'Case 1: 4B NO_EFFECT_PATCH, 9B success': find_case(lambda row: row['4b_failure_top'] == 'NO_EFFECT_PATCH' and row['9b_committed'] > row['4b_committed']),
        'Case 2: 4B BLOCKED_BY_POLICY, 9B success': find_case(lambda row: row['4b_failure_top'] == 'BLOCKED_BY_POLICY' and row['9b_committed'] > row['4b_committed']),
        'Case 3: both commit successfully': find_case(lambda row: row['4b_committed'] > 0 and row['9b_committed'] > 0),
        'Case 4: both emit but both fail': find_case(lambda row: row['4b_emitted'] > 0 and row['9b_emitted'] > 0 and row['4b_committed'] == 0 and row['9b_committed'] == 0),
        'Case 5: 9B reward higher but patch quality not better': find_case(lambda row: row['9b_reward'] > row['4b_reward'] and row['9b_committed'] <= row['4b_committed']),
        'Case 6: historical sentinel improvement': find_case(lambda row: row['bucket'] == 'historical_sentinel' and row['9b_committed'] > row['4b_committed']),
    }

    cb_lines = ["# P25.0 Casebook", ""]
    for title, row in cases.items():
        cb_lines.append(f"## {title}")
        if row is None:
            cb_lines.append("No clean instance in this bounded compare; nearest cases should be read from the pairwise table.")
            cb_lines.append("")
            continue
        cb_lines.append(f"- paper_id: `{row['paper_id']}`")
        cb_lines.append(f"- bucket: `{row['bucket']}`")
        cb_lines.append(f"- 4B: emitted={row['4b_emitted']}, committed={row['4b_committed']}, top_failure={row['4b_failure_top']}, reward={row['4b_reward']}")
        cb_lines.append(f"- 9B: emitted={row['9b_emitted']}, committed={row['9b_committed']}, top_failure={row['9b_failure_top']}, reward={row['9b_reward']}")
        cb_lines.append(f"- reading: {row['notes']}")
        cb_lines.append("")
    (docs_root / 'P25_0_CASEBOOK.md').write_text("\n".join(cb_lines) + "\n", encoding='utf-8')

    md_lines = [
        "# P25.0 Model Decision",
        "",
        "## Recovery-Relevant Outcome",
        f"- 4B avg_reward / median_reward / decision_correct_rate: {main_4b['avg_reward']} / {main_4b['median_reward']} / {main_4b['decision_correct_rate']}",
        f"- 9B avg_reward / median_reward / decision_correct_rate: {main_9b['avg_reward']} / {main_9b['median_reward']} / {main_9b['decision_correct_rate']}",
        f"- 4B validation_to_commit_rate: {main_4b['rates']['validation_to_commit_rate']}",
        f"- 9B validation_to_commit_rate: {main_9b['rates']['validation_to_commit_rate']}",
        f"- 4B NO_EFFECT_PATCH count: {main_4b['failure_code_counts'].get('NO_EFFECT_PATCH', 0)}",
        f"- 9B NO_EFFECT_PATCH count: {main_9b['failure_code_counts'].get('NO_EFFECT_PATCH', 0)}",
        "",
    ]
    no_effect_delta = main_9b['failure_code_counts'].get('NO_EFFECT_PATCH', 0) - main_4b['failure_code_counts'].get('NO_EFFECT_PATCH', 0)
    commit_delta = main_9b['row_counts']['patch_committed_count'] - main_4b['row_counts']['patch_committed_count']
    if no_effect_delta < 0 and commit_delta > 0:
        decision = "9B is materially better on recovery quality; next step can move to 9B expansion."
    else:
        decision = "9B does not yet show a decisive recovery-quality win; next step should stay focused on patch effectiveness / policy gate rather than scaling blindly."
    md_lines.append(f"Current decision: {decision}")
    md_lines.extend([
        "",
        "## Interpretation",
        "- this compare is frozen at the p24.4 pipeline; changes in outcome are attributable to model capacity unless hardware forces otherwise.",
        "- reward differences are secondary; the main read should come from failure-code shifts and real state-change commits.",
    ])
    (docs_root / 'P25_0_MODEL_DECISION.md').write_text("\n".join(md_lines) + "\n", encoding='utf-8')


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--result-4b', required=True)
    parser.add_argument('--result-9b', required=True)
    parser.add_argument('--setup-meta', required=True)
    parser.add_argument('--docs-root', default='.')
    parser.add_argument('--analysis-path', default='outputs/review_infer/p25_0_compare_analysis.json')
    args = parser.parse_args()

    setup = json.loads(Path(args.setup_meta).read_text('utf-8'))
    rows_4b = load_jsonl(Path(args.result_4b))
    rows_9b = load_jsonl(Path(args.result_9b))
    recovery_ids = setup['recovery_relevant_ids']
    sentinel_ids = setup['historical_sentinel_ids']
    bucket_map = {paper_id: 'recovery_relevant' for paper_id in recovery_ids}
    bucket_map.update({paper_id: 'historical_sentinel' for paper_id in sentinel_ids})

    main_4b = analyze_model(rows_4b, recovery_ids)
    main_9b = analyze_model(rows_9b, recovery_ids)
    sentinel_4b = analyze_model(rows_4b, sentinel_ids)
    sentinel_9b = analyze_model(rows_9b, sentinel_ids)
    pairwise = pairwise_table(main_4b['per_row'] | sentinel_4b['per_row'], main_9b['per_row'] | sentinel_9b['per_row'], bucket_map)

    payload = {
        'setup': setup,
        'recovery_relevant': {'4b': main_4b, '9b': main_9b},
        'historical_sentinel': {'4b': sentinel_4b, '9b': sentinel_9b},
        'pairwise': pairwise,
    }
    Path(args.analysis_path).write_text(json.dumps(payload, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    write_docs(Path(args.docs_root), setup, main_4b, main_9b, sentinel_4b, sentinel_9b, pairwise)


if __name__ == '__main__':
    main()
