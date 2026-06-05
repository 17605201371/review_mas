from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

from p25_0_frozen_compare import analyze_model, load_jsonl


def state_change_summary(summary: Dict[str, Any]) -> str:
    payload = summary.get('state_change_by_type') or {}
    if not payload:
        return 'none'
    return '; '.join(f"{name} x{count}" for name, count in sorted(payload.items()))


def pairwise_table(rows_4b: Dict[str, Any], rows_9b: Dict[str, Any], bucket_map: Dict[str, str]) -> List[Dict[str, Any]]:
    paper_ids = sorted(set(rows_4b) | set(rows_9b))
    table: List[Dict[str, Any]] = []
    for paper_id in paper_ids:
        left = rows_4b.get(paper_id, {})
        right = rows_9b.get(paper_id, {})
        left_commit = left.get('patch_committed_count', 0)
        right_commit = right.get('patch_committed_count', 0)
        if left_commit == 0 and right_commit > 0:
            primary_group = 'A'
        elif left_commit > 0 and right_commit > 0:
            primary_group = 'B'
        elif left_commit == 0 and right_commit == 0:
            primary_group = 'C'
        else:
            primary_group = 'reverse_regression'

        notes: List[str] = []
        if primary_group == 'A':
            notes.append('9B unlocks commit')
        if left.get('top_failure') == 'NO_EFFECT_PATCH' and right.get('top_failure') != 'NO_EFFECT_PATCH':
            notes.append('9B reduces no-effect')
        if right.get('top_failure') == 'BLOCKED_BY_POLICY' and right_commit <= left_commit:
            notes.append('policy block may be bottleneck')
        reward_only = right.get('reward', 0.0) > left.get('reward', 0.0) and right_commit <= left_commit
        if reward_only:
            notes.append('reward up without better patch quality')
        if not notes:
            notes.append('stable')

        table.append(
            {
                'paper_id': paper_id,
                'bucket': bucket_map.get(paper_id, 'unknown'),
                'primary_group': primary_group,
                'reward_only_flag': reward_only,
                '4b_emitted': left.get('patch_emitted_count', 0),
                '9b_emitted': right.get('patch_emitted_count', 0),
                '4b_validated': left.get('patch_validated_count', 0),
                '9b_validated': right.get('patch_validated_count', 0),
                '4b_committed': left_commit,
                '9b_committed': right_commit,
                '4b_failure_top': left.get('top_failure', 'none'),
                '9b_failure_top': right.get('top_failure', 'none'),
                '4b_state_change': state_change_summary(left),
                '9b_state_change': state_change_summary(right),
                '4b_reward': round(float(left.get('reward', 0.0)), 4),
                '9b_reward': round(float(right.get('reward', 0.0)), 4),
                'notes': '; '.join(notes),
            }
        )
    return table


def total_state_changes(payload: Dict[str, Any]) -> int:
    return sum((payload.get('state_change_by_target') or {}).values())


def write_setup_doc(docs_root: Path, setup: Dict[str, Any]) -> None:
    lines = [
        '# P25.1 Setup',
        '',
        f"- frozen_commit: `{setup['frozen_commit']}`",
        f"- 9B main subset: `{setup['main_subset_path']}`",
        f"- 4B reference subset: `{setup['reference_subset_path']}`",
        f"- expanded recovery_relevant_count: {setup['recovery_relevant_count']}",
        f"- fixed 4B reference_count: {setup['reference_compare_count']}",
        f"- historical_sentinel_count: {setup['historical_sentinel_count']}",
        f"- 4B model: `{setup['models']['4b']}`",
        f"- 9B model: `{setup['models']['9b']}`",
        '',
        '## Selection Rule',
        f"- {setup['selection_rule']}",
        '',
        '## Frozen Parameters',
    ]
    for key, value in setup['fixed_params'].items():
        lines.append(f'- {key}: {value}')
    lines.extend([
        '',
        '## Runtime Note',
        f"- {setup['runtime_note']}",
        '',
        '## Fixed 4B Reference IDs',
        f"- {', '.join(setup['reference_ids'])}",
        '',
        '## Historical Sentinel IDs',
        f"- {', '.join(setup['historical_sentinel_ids'])}",
    ])
    (docs_root / 'P25_1_SETUP.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')


def write_patch_doc(docs_root: Path, main_9b: Dict[str, Any], ref_4b: Dict[str, Any], ref_9b: Dict[str, Any]) -> None:
    lines = [
        '# P25.1 Patch Effectiveness',
        '',
        '## 9B Expanded Recovery-Relevant Failure Codes (attempt-level)',
        '| Failure Code | 9B main |',
        '| --- | ---: |',
    ]
    for code in sorted(main_9b['failure_code_counts']):
        lines.append(f"| {code} | {main_9b['failure_code_counts'].get(code, 0)} |")
    lines.extend([
        '',
        '## 9B Expanded Rates Among Emitted Recovery Patches',
        '| Metric | 9B main |',
        '| --- | ---: |',
    ])
    for key in ['success_rate_among_emitted', 'no_effect_rate_among_emitted', 'blocked_rate_among_emitted']:
        lines.append(f"| {key} | {main_9b['effectiveness'][key]} |")
    lines.extend([
        '',
        '## Fixed Reference Compare (4B vs 9B)',
        '| Failure Code | 4B reference | 9B reference |',
        '| --- | ---: | ---: |',
    ])
    all_codes = sorted(set(ref_4b['failure_code_counts']) | set(ref_9b['failure_code_counts']))
    for code in all_codes:
        lines.append(f"| {code} | {ref_4b['failure_code_counts'].get(code, 0)} | {ref_9b['failure_code_counts'].get(code, 0)} |")
    lines.extend([
        '',
        '## Fixed Reference Rates Among Emitted Recovery Patches',
        '| Metric | 4B reference | 9B reference |',
        '| --- | ---: | ---: |',
    ])
    for key in ['success_rate_among_emitted', 'no_effect_rate_among_emitted', 'blocked_rate_among_emitted']:
        lines.append(f"| {key} | {ref_4b['effectiveness'][key]} | {ref_9b['effectiveness'][key]} |")
    (docs_root / 'P25_1_PATCH_EFFECTIVENESS.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')


def write_commit_doc(docs_root: Path, main_9b: Dict[str, Any], ref_4b: Dict[str, Any], ref_9b: Dict[str, Any]) -> None:
    lines = [
        '# P25.1 Commit Throughput',
        '',
        '## 9B Expanded Recovery-Relevant Rows',
        '| Metric | 9B main |',
        '| --- | ---: |',
    ]
    for key in [
        'recovery_relevant_count',
        'recovery_triggered_count',
        'recovery_patch_mode_entered_count',
        'patch_emitted_count',
        'patch_validated_count',
        'patch_committed_count',
    ]:
        lines.append(f"| {key} | {main_9b['row_counts'][key]} |")
    lines.extend([
        '',
        '## 9B Expanded Rates',
        '| Metric | 9B main |',
        '| --- | ---: |',
    ])
    for key in [
        'recovery_relevant_to_trigger_rate',
        'trigger_to_patch_mode_rate',
        'patch_mode_to_emission_rate',
        'emission_to_validation_rate',
        'validation_to_commit_rate',
    ]:
        lines.append(f"| {key} | {main_9b['rates'][key]} |")
    lines.extend([
        '',
        '## Fixed Reference Compare (4B vs 9B)',
        '| Metric | 4B reference | 9B reference |',
        '| --- | ---: | ---: |',
    ])
    for key in [
        'recovery_relevant_count',
        'recovery_triggered_count',
        'recovery_patch_mode_entered_count',
        'patch_emitted_count',
        'patch_validated_count',
        'patch_committed_count',
    ]:
        lines.append(f"| {key} | {ref_4b['row_counts'][key]} | {ref_9b['row_counts'][key]} |")
    lines.extend([
        '',
        '## Fixed Reference Rates',
        '| Metric | 4B reference | 9B reference |',
        '| --- | ---: | ---: |',
    ])
    for key in [
        'recovery_relevant_to_trigger_rate',
        'trigger_to_patch_mode_rate',
        'patch_mode_to_emission_rate',
        'emission_to_validation_rate',
        'validation_to_commit_rate',
    ]:
        lines.append(f"| {key} | {ref_4b['rates'][key]} | {ref_9b['rates'][key]} |")
    lines.extend([
        '',
        '- note: `patch_validated_count` still includes blocked-but-validated recovery turns, so the main quality read should stay anchored on `NO_EFFECT_PATCH`, `patch_committed_count`, and real state changes.',
    ])
    (docs_root / 'P25_1_COMMIT_THROUGHPUT.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')


def write_state_doc(docs_root: Path, main_9b: Dict[str, Any], ref_4b: Dict[str, Any], ref_9b: Dict[str, Any]) -> None:
    lines = [
        '# P25.1 State Repair',
        '',
        '## 9B Expanded State Change Counts By Target Type',
        '| Target Type | 9B main |',
        '| --- | ---: |',
    ]
    for target in sorted(main_9b['state_change_by_target']):
        lines.append(f"| {target} | {main_9b['state_change_by_target'].get(target, 0)} |")
    lines.extend([
        '',
        '## 9B Expanded Transition Detail',
        '| Transition | 9B main |',
        '| --- | ---: |',
    ])
    for transition in sorted(main_9b['state_change_by_type']):
        lines.append(f"| {transition} | {main_9b['state_change_by_type'].get(transition, 0)} |")
    lines.extend([
        '',
        '## Fixed Reference State Change Counts By Target Type',
        '| Target Type | 4B reference | 9B reference |',
        '| --- | ---: | ---: |',
    ])
    all_targets = sorted(set(ref_4b['state_change_by_target']) | set(ref_9b['state_change_by_target']))
    for target in all_targets:
        lines.append(f"| {target} | {ref_4b['state_change_by_target'].get(target, 0)} | {ref_9b['state_change_by_target'].get(target, 0)} |")
    lines.extend([
        '',
        '## Fixed Reference Transition Detail',
        '| Transition | 4B reference | 9B reference |',
        '| --- | ---: | ---: |',
    ])
    all_transitions = sorted(set(ref_4b['state_change_by_type']) | set(ref_9b['state_change_by_type']))
    for transition in all_transitions:
        lines.append(f"| {transition} | {ref_4b['state_change_by_type'].get(transition, 0)} | {ref_9b['state_change_by_type'].get(transition, 0)} |")
    (docs_root / 'P25_1_STATE_REPAIR.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')


def write_pairwise_doc(docs_root: Path, pairwise: List[Dict[str, Any]]) -> None:
    lines = [
        '# P25.1 Pairwise Table',
        '',
        '| paper_id | bucket | group | 4B emitted | 9B emitted | 4B validated | 9B validated | 4B committed | 9B committed | 4B failure top | 9B failure top | 4B state change | 9B state change | 4B reward | 9B reward | notes |',
        '| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | --- | --- | ---: | ---: | --- |',
    ]
    for row in pairwise:
        lines.append(
            f"| {row['paper_id']} | {row['bucket']} | {row['primary_group']} | {row['4b_emitted']} | {row['9b_emitted']} | {row['4b_validated']} | {row['9b_validated']} | {row['4b_committed']} | {row['9b_committed']} | {row['4b_failure_top']} | {row['9b_failure_top']} | {row['4b_state_change']} | {row['9b_state_change']} | {row['4b_reward']} | {row['9b_reward']} | {row['notes']} |"
        )
    (docs_root / 'P25_1_PAIRWISE_TABLE.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')


def first_case(rows: List[Dict[str, Any]], predicate) -> Dict[str, Any] | None:
    for row in rows:
        if predicate(row):
            return row
    return None


def add_case(lines: List[str], title: str, row: Dict[str, Any] | None) -> None:
    lines.append(f'## {title}')
    if row is None:
        lines.append('No clean instance under this bounded compare; read the pairwise table for the nearest row.')
        lines.append('')
        return
    lines.append(f"- paper_id: `{row['paper_id']}`")
    lines.append(f"- bucket: `{row['bucket']}`")
    lines.append(f"- group: `{row['primary_group']}`")
    lines.append(f"- 4B: emitted={row['4b_emitted']}, validated={row['4b_validated']}, committed={row['4b_committed']}, top_failure={row['4b_failure_top']}, state_change={row['4b_state_change']}, reward={row['4b_reward']}")
    lines.append(f"- 9B: emitted={row['9b_emitted']}, validated={row['9b_validated']}, committed={row['9b_committed']}, top_failure={row['9b_failure_top']}, state_change={row['9b_state_change']}, reward={row['9b_reward']}")
    lines.append(f"- reading: {row['notes']}")
    lines.append('')


def write_casebook(docs_root: Path, pairwise: List[Dict[str, Any]]) -> None:
    lines = ['# P25.1 Casebook', '']
    add_case(lines, 'Case 1: 9B truly improves over 4B', first_case(pairwise, lambda row: row['primary_group'] == 'A'))
    add_case(lines, 'Case 2: both models succeed', first_case(pairwise, lambda row: row['primary_group'] == 'B'))
    add_case(lines, 'Case 3: both models fail', first_case(pairwise, lambda row: row['primary_group'] == 'C'))
    add_case(lines, 'Case 4: 9B reward rises without patch-quality gain', first_case(pairwise, lambda row: row['reward_only_flag']))
    add_case(lines, 'Case 5: hardest recovery case', max(pairwise, key=lambda row: (row['9b_emitted'] + row['4b_emitted'], row['9b_validated'] + row['4b_validated']), default=None))
    add_case(lines, 'Case 6: historical sentinel case', first_case(pairwise, lambda row: row['bucket'] == 'historical_sentinel'))
    (docs_root / 'P25_1_CASEBOOK.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')


def write_direction_doc(docs_root: Path, setup: Dict[str, Any], main_9b: Dict[str, Any], ref_4b: Dict[str, Any], ref_9b: Dict[str, Any], pairwise: List[Dict[str, Any]]) -> None:
    no_effect_4b = ref_4b['failure_code_counts'].get('NO_EFFECT_PATCH', 0)
    no_effect_9b = ref_9b['failure_code_counts'].get('NO_EFFECT_PATCH', 0)
    blocked_4b = ref_4b['failure_code_counts'].get('BLOCKED_BY_POLICY', 0)
    blocked_9b = ref_9b['failure_code_counts'].get('BLOCKED_BY_POLICY', 0)
    ref_state_4b = total_state_changes(ref_4b)
    ref_state_9b = total_state_changes(ref_9b)
    group_counts = {
        'A': sum(1 for row in pairwise if row['primary_group'] == 'A'),
        'B': sum(1 for row in pairwise if row['primary_group'] == 'B'),
        'C': sum(1 for row in pairwise if row['primary_group'] == 'C'),
        'reverse_regression': sum(1 for row in pairwise if row['primary_group'] == 'reverse_regression'),
        'reward_only': sum(1 for row in pairwise if row['reward_only_flag']),
    }

    q1 = 'yes' if no_effect_9b < no_effect_4b and ref_9b['rates']['validation_to_commit_rate'] >= ref_4b['rates']['validation_to_commit_rate'] else 'not yet'
    if no_effect_9b < no_effect_4b and ref_9b['rates']['validation_to_commit_rate'] > ref_4b['rates']['validation_to_commit_rate']:
        q2 = 'both fewer NO_EFFECT_PATCH and higher commit throughput'
    elif no_effect_9b < no_effect_4b:
        q2 = 'mainly fewer NO_EFFECT_PATCH'
    else:
        q2 = 'not clearly better on the current fixed reference subset'
    if blocked_9b > blocked_4b and ref_9b['row_counts']['patch_committed_count'] > ref_4b['row_counts']['patch_committed_count']:
        q3 = 'blocked cases likely reflect a stricter but still more productive 9B recovery policy; the gate is a visible secondary bottleneck, not the primary reason to stop scaling'
    elif blocked_9b > blocked_4b:
        q3 = 'policy gate is likely the next bottleneck because 9B hits more blocked turns without a matching commit gain'
    else:
        q3 = 'policy block does not dominate the new comparison'

    if no_effect_9b < no_effect_4b and ref_9b['rates']['validation_to_commit_rate'] >= ref_4b['rates']['validation_to_commit_rate'] and ref_state_9b >= ref_state_4b:
        next_step = '9B is stable enough to become the main working model; next step can move to a larger 9B recovery benchmark instead of an immediate policy-block calibration.'
    else:
        next_step = 'The 9B advantage is not yet stable enough; next step should be p25.2 policy-block calibration before any larger benchmark.'

    lines = [
        '# P25.1 Direction Decision',
        '',
        '## Main Read',
        f"- 9B main expanded rows: {main_9b['rows']} recovery-relevant + {setup['historical_sentinel_count']} sentinel rows in the actual run.",
        f"- Fixed reference compare rows: {setup['reference_compare_count']} recovery rows + {setup['historical_sentinel_count']} sentinel rows.",
        f"- 4B reference avg_reward / median_reward / decision_correct_rate: {ref_4b['avg_reward']} / {ref_4b['median_reward']} / {ref_4b['decision_correct_rate']}",
        f"- 9B reference avg_reward / median_reward / decision_correct_rate: {ref_9b['avg_reward']} / {ref_9b['median_reward']} / {ref_9b['decision_correct_rate']}",
        f"- 4B reference validation_to_commit_rate: {ref_4b['rates']['validation_to_commit_rate']}",
        f"- 9B reference validation_to_commit_rate: {ref_9b['rates']['validation_to_commit_rate']}",
        f"- 4B reference NO_EFFECT_PATCH: {no_effect_4b}",
        f"- 9B reference NO_EFFECT_PATCH: {no_effect_9b}",
        f"- 4B reference state changes: {ref_state_4b}",
        f"- 9B reference state changes: {ref_state_9b}",
        f"- Pairwise groups: A={group_counts['A']}, B={group_counts['B']}, C={group_counts['C']}, reverse_regression={group_counts['reverse_regression']}, reward_only={group_counts['reward_only']}",
        '',
        '## Research Questions',
        f"1. Does the 9B advantage remain stable on a larger recovery-relevant pool? {q1}.",
        f"2. Where does 9B gain come from? {q2}.",
        f"3. What does the larger BLOCKED_BY_POLICY footprint mean? {q3}.",
        f"4. What should happen next? {next_step}",
    ]
    (docs_root / 'P25_1_DIRECTION_DECISION.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--result-9b', required=True)
    parser.add_argument('--result-4b', required=True)
    parser.add_argument('--setup-meta', required=True)
    parser.add_argument('--docs-root', default='.')
    parser.add_argument('--analysis-path', default='outputs/review_infer/p25_1_analysis.json')
    args = parser.parse_args()

    setup = json.loads(Path(args.setup_meta).read_text('utf-8'))
    rows_9b = load_jsonl(Path(args.result_9b))
    rows_4b = load_jsonl(Path(args.result_4b))

    recovery_ids = setup['recovery_relevant_ids']
    reference_ids = setup['reference_ids']
    sentinel_ids = setup['historical_sentinel_ids']
    bucket_map = {paper_id: 'reference_recovery' for paper_id in reference_ids}
    bucket_map.update({paper_id: 'historical_sentinel' for paper_id in sentinel_ids})

    main_9b = analyze_model(rows_9b, recovery_ids)
    sentinel_9b = analyze_model(rows_9b, sentinel_ids)
    reference_9b = analyze_model(rows_9b, reference_ids)
    reference_4b = analyze_model(rows_4b, reference_ids)
    sentinel_4b = analyze_model(rows_4b, sentinel_ids)
    pairwise = pairwise_table(reference_4b['per_row'] | sentinel_4b['per_row'], reference_9b['per_row'] | sentinel_9b['per_row'], bucket_map)

    docs_root = Path(args.docs_root)
    docs_root.mkdir(parents=True, exist_ok=True)
    write_setup_doc(docs_root, setup)
    write_patch_doc(docs_root, main_9b, reference_4b, reference_9b)
    write_commit_doc(docs_root, main_9b, reference_4b, reference_9b)
    write_state_doc(docs_root, main_9b, reference_4b, reference_9b)
    write_pairwise_doc(docs_root, pairwise)
    write_casebook(docs_root, pairwise)
    write_direction_doc(docs_root, setup, main_9b, reference_4b, reference_9b, pairwise)

    payload = {
        'setup': setup,
        'expanded_9b': main_9b,
        'expanded_9b_sentinel': sentinel_9b,
        'reference_compare': {
            '4b': reference_4b,
            '9b': reference_9b,
            'sentinel_4b': sentinel_4b,
            'sentinel_9b': sentinel_9b,
        },
        'pairwise': pairwise,
    }
    Path(args.analysis_path).write_text(json.dumps(payload, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
