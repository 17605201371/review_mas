from __future__ import annotations

import json
from pathlib import Path
from collections import Counter

BASE = Path('/root/zssmas/outputs/review_infer')
MODES = ['s1', 's2', 's3', 's4']
RESULTS = {m: BASE / f'pilot_{m}_batch39.jsonl' for m in MODES}


def load_jsonl(path: Path):
    rows = []
    if not path.exists():
        return rows
    with path.open('r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def summarize_rows(rows):
    summary = {
        'rows': len(rows),
        'avg_turns': 0.0,
        'avg_claims': 0.0,
        'avg_evidence': 0.0,
        'avg_flaws': 0.0,
        'nonempty_claim_rows': 0,
        'nonempty_evidence_rows': 0,
        'nonempty_flaw_rows': 0,
        'finalize_with_empty_state_rows': 0,
        'conflicts_detected_turns': 0,
        'downgraded_items_turns': 0,
        'retracted_items_turns': 0,
        'action_counts': Counter(),
        'effective_action_counts': Counter(),
        'policy_source_counts': Counter(),
    }
    if not rows:
        return summary
    for row in rows:
        state = row.get('review_state', {}) or {}
        turn_logs = row.get('turn_logs', []) or []
        summary['avg_turns'] += len(turn_logs)
        claims = len(state.get('claims', []) or [])
        evidence = len(state.get('evidence_map', []) or [])
        flaws = len(state.get('flaw_candidates', []) or [])
        summary['avg_claims'] += claims
        summary['avg_evidence'] += evidence
        summary['avg_flaws'] += flaws
        summary['nonempty_claim_rows'] += int(claims > 0)
        summary['nonempty_evidence_rows'] += int(evidence > 0)
        summary['nonempty_flaw_rows'] += int(flaws > 0)
        summary['finalize_with_empty_state_rows'] += int((claims + evidence + flaws) == 0 and bool(turn_logs))
        for turn in turn_logs:
            summary['action_counts'][turn.get('action_type', 'unknown')] += 1
            summary['effective_action_counts'][turn.get('effective_action_type', 'unknown')] += 1
            summary['policy_source_counts'][turn.get('policy_source', 'unknown')] += 1
            summary['conflicts_detected_turns'] += int(bool(turn.get('conflicts_detected')))
            summary['downgraded_items_turns'] += int(bool(turn.get('downgraded_items')))
            summary['retracted_items_turns'] += int(bool(turn.get('retracted_items')))
    n = len(rows)
    summary['avg_turns'] /= n
    summary['avg_claims'] /= n
    summary['avg_evidence'] /= n
    summary['avg_flaws'] /= n
    summary['action_counts'] = dict(summary['action_counts'])
    summary['effective_action_counts'] = dict(summary['effective_action_counts'])
    summary['policy_source_counts'] = dict(summary['policy_source_counts'])
    return summary


def pick_cases(data):
    by_id = {mode: {row.get('paper_id'): row for row in rows} for mode, rows in data.items()}
    paper_ids = sorted(set().union(*[set(v.keys()) for v in by_id.values()]))
    better_s4 = []
    conflict_no_recovery = []
    override_heavy = []
    for pid in paper_ids:
        s3 = by_id.get('s3', {}).get(pid)
        s4 = by_id.get('s4', {}).get(pid)
        if s3 and s4:
            s3_state = s3.get('review_state', {}) or {}
            s4_state = s4.get('review_state', {}) or {}
            if len(s3_state.get('flaw_candidates', []) or []) == 0 and len(s4_state.get('flaw_candidates', []) or []) > 0:
                better_s4.append(pid)
            s4_logs = s4.get('turn_logs', []) or []
            if any(t.get('conflicts_detected') for t in s4_logs) and not any(t.get('downgraded_items') or t.get('retracted_items') for t in s4_logs):
                conflict_no_recovery.append(pid)
            override_count = sum(1 for t in s4_logs if t.get('policy_source') not in {'manager_model', 'unknown'})
            if override_count >= 2:
                override_heavy.append(pid)
    return {
        's4_better_than_s3': better_s4[:6],
        'conflict_without_recovery': conflict_no_recovery[:6],
        'override_heavy': override_heavy[:6],
    }


def main():
    data = {mode: load_jsonl(path) for mode, path in RESULTS.items()}
    if not all(data.values()):
        missing = [mode for mode, rows in data.items() if not rows]
        print(json.dumps({'status': 'incomplete', 'missing_modes': missing}, ensure_ascii=False, indent=2))
        return 0

    summaries = {mode: summarize_rows(rows) for mode, rows in data.items()}
    cases = pick_cases(data)

    summary_lines = [
        '# PILOT_SUMMARY',
        '',
        'This file summarizes the 39-sample S1/S2/S3/S4 pilot run.',
        '',
        '| Mode | Rows | Avg Turns | Avg Claims | Avg Evidence | Avg Flaws | Claim Rows | Evidence Rows | Flaw Rows | Conflict Turns | Downgrade Turns |',
        '| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |',
    ]
    for mode in MODES:
        s = summaries[mode]
        summary_lines.append(
            f'| {mode.upper()} | {s["rows"]} | {s["avg_turns"]:.2f} | {s["avg_claims"]:.2f} | {s["avg_evidence"]:.2f} | {s["avg_flaws"]:.2f} | {s["nonempty_claim_rows"]} | {s["nonempty_evidence_rows"]} | {s["nonempty_flaw_rows"]} | {s["conflicts_detected_turns"]} | {s["downgraded_items_turns"]} |'
        )
        summary_lines.append('')
        summary_lines.append(f'`{mode}` action_counts: `{json.dumps(s["action_counts"], ensure_ascii=False)}`')
        summary_lines.append(f'`{mode}` effective_action_counts: `{json.dumps(s["effective_action_counts"], ensure_ascii=False)}`')
        summary_lines.append(f'`{mode}` policy_source_counts: `{json.dumps(s["policy_source_counts"], ensure_ascii=False)}`')
        summary_lines.append('')

    cases_lines = [
        '# PILOT_CASES',
        '',
        'Representative paper ids for manual case analysis.',
        '',
        '## Case A: S4 clearly better than S3',
    ]
    for pid in cases['s4_better_than_s3']:
        cases_lines.append(f'- `{pid}`')
    cases_lines += ['', '## Case B: conflict detected but recovery did not complete']
    for pid in cases['conflict_without_recovery']:
        cases_lines.append(f'- `{pid}`')
    cases_lines += ['', '## Case C: override-heavy samples']
    for pid in cases['override_heavy']:
        cases_lines.append(f'- `{pid}`')

    s3 = summaries['s3']
    s4 = summaries['s4']
    go = (
        s4['nonempty_flaw_rows'] > s3['nonempty_flaw_rows']
        and s4['finalize_with_empty_state_rows'] <= s3['finalize_with_empty_state_rows']
        and s4['conflicts_detected_turns'] > 0
    )
    go_lines = [
        '# PILOT_GO_NO_GO',
        '',
        f'Go decision: `{ "GO" if go else "NO-GO" }`',
        '',
        '## Rationale',
        f'- S4 nonempty flaw rows: {s4["nonempty_flaw_rows"]} vs S3 {s3["nonempty_flaw_rows"]}',
        f'- S4 conflict turns: {s4["conflicts_detected_turns"]}',
        f'- S4 downgrade turns: {s4["downgraded_items_turns"]}',
        f'- S4 finalize_with_empty_state_rows: {s4["finalize_with_empty_state_rows"]}',
        '',
        '## Immediate next step',
        '- If GO: proceed to larger main experiment planning with the current framework.',
        '- If NO-GO: prioritize conflict-to-recovery conversion and override interpretability before scaling.',
    ]

    (Path('/root/zssmas/PILOT_SUMMARY.md')).write_text('\n'.join(summary_lines) + '\n')
    (Path('/root/zssmas/PILOT_CASES.md')).write_text('\n'.join(cases_lines) + '\n')
    (Path('/root/zssmas/PILOT_GO_NO_GO.md')).write_text('\n'.join(go_lines) + '\n')
    print(json.dumps({'status': 'ok', 'cases': cases}, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
