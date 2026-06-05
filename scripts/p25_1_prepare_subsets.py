from __future__ import annotations

import json
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List

import pyarrow as pa
import pyarrow.parquet as pq

OUTPUT_DIR = Path('outputs/review_infer')
PILOT2_JSONL = OUTPUT_DIR / 'pilot2_s4_batch100.jsonl'
PILOT2_PARQUET = OUTPUT_DIR / 'pilot2_batch100.parquet'
PILOT39_PARQUET = OUTPUT_DIR / 'pilot_batch39.parquet'
MAIN_SUBSET_PATH = OUTPUT_DIR / 'p25_1_9b_expanded_subset.parquet'
REFERENCE_SUBSET_PATH = OUTPUT_DIR / 'p25_1_4b_reference_subset.parquet'
SETUP_META_PATH = OUTPUT_DIR / 'p25_1_setup_meta.json'
SELECTION_AUDIT_PATH = OUTPUT_DIR / 'p25_1_selection_audit.json'

RECOVERY_ACTIONS = {'challenge_previous_hypothesis', 'request_evidence_recheck'}
CARRYOVER_IDS = [
    '2Cg4YrsCMA',
    '7LZjuA4AB2',
    'IqaQZ1Jdky',
    'kdriw2a8sl',
    '9EBSEkFSje',
    'qgyF6JVmar',
    'NhLBhx5BVY',
    'GSckuQMzBG',
]
EXPANSION_IDS = [
    'Ze49bGd4ON',
    'RyWypcIMiE',
    'meY36sGyyv',
    'k03mB41vyM',
    'hAYHmV1gM8',
    'qrGjFJVl3m',
    'JdWpIe70FL',
    'EXGahWDp1E',
    'fO1xnmW8T6',
    'nrvoWOWcyg',
    'KlxK4ncqWZ',
    'IiRlImvLQI',
    'UpgRVWexaD',
    'FqWtMGw8tt',
    'ydlDRUuGm9',
    'nrRkAAAufl',
]
REFERENCE_IDS = [
    '2Cg4YrsCMA',
    'NhLBhx5BVY',
    '9EBSEkFSje',
    'GSckuQMzBG',
    'IqaQZ1Jdky',
    'kdriw2a8sl',
    'qgyF6JVmar',
    'Ze49bGd4ON',
]
SENTINEL_IDS = ['X41c4uB4k0', 'hj323oR3rw']
FIXED_PARAMS = {
    'mode': 's4',
    'max_turns': 8,
    'max_workers_per_turn': 3,
    'manager_batch_size': 2,
    'gpu_memory_utilization': 0.94,
    'max_num_seqs': 128,
    'max_model_len': 3072,
    'max_tokens': 640,
    'temperature': 0.2,
    'top_p': 0.95,
}
MODELS = {
    '4b': '/reviewF/datasets/Qwen3___5-4B',
    '9b': '/reviewF/datasets/Qwen3___5-9B',
}
RUNTIME_NOTE = (
    'Original strict-frozen startup at gpu_memory_utilization=0.6 could not boot 9B on RTX 4090 24GB; '
    'the p25.1 bounded runs keep all pipeline settings fixed and share gpu_memory_utilization=0.94.'
)
SELECTION_RULE = (
    'Expanded recovery-relevant set keeps the 8 carry-over p25.0 rows for continuity, then adds 16 pilot2 rows '
    'with the strongest pre-recovery signals from frozen S4 logs: recovery-oriented action turns, conflict turns, '
    'downgrade/retract evidence, and revision events. Historical sentinel rows remain separate and are not counted '
    'inside the 24-row expanded recovery-relevant total.'
)


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    return [json.loads(line) for line in path.read_text('utf-8').splitlines() if line.strip()]


def git_head() -> str:
    return subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()


def summarize_pilot2_signals() -> List[Dict[str, Any]]:
    rows = load_jsonl(PILOT2_JSONL)
    metrics: List[Dict[str, Any]] = []
    for row in rows:
        counts: Counter[str] = Counter()
        for turn in row.get('turn_logs') or []:
            action = str(turn.get('action_type') or '')
            effective = str(turn.get('effective_action_type') or '')
            if action in RECOVERY_ACTIONS:
                counts['recovery_action_turns'] += 1
            if effective in RECOVERY_ACTIONS:
                counts['recovery_effective_turns'] += 1
            if turn.get('conflicts_detected'):
                counts['conflict_turns'] += 1
            counts['revision_events'] += len(turn.get('revision_events') or [])
            counts['downgraded_items'] += len(turn.get('downgraded_items') or [])
            counts['retracted_items'] += len(turn.get('retracted_items') or [])
            counts['open_unresolved'] += len(turn.get('open_unresolved_questions') or [])
            counts['evidence_gaps'] += len(turn.get('evidence_gaps') or [])
        score = (
            counts['recovery_action_turns'] * 5
            + counts['recovery_effective_turns'] * 4
            + counts['conflict_turns'] * 4
            + counts['revision_events']
            + counts['downgraded_items'] * 3
            + counts['retracted_items'] * 3
            + counts['open_unresolved']
            + counts['evidence_gaps']
        )
        metrics.append(
            {
                'paper_id': row['paper_id'],
                'reward': row.get('reward'),
                'score': score,
                'recovery_action_turns': counts.get('recovery_action_turns', 0),
                'recovery_effective_turns': counts.get('recovery_effective_turns', 0),
                'conflict_turns': counts.get('conflict_turns', 0),
                'downgraded_items': counts.get('downgraded_items', 0),
                'retracted_items': counts.get('retracted_items', 0),
                'revision_events': counts.get('revision_events', 0),
                'open_unresolved': counts.get('open_unresolved', 0),
                'evidence_gaps': counts.get('evidence_gaps', 0),
            }
        )
    metrics.sort(key=lambda item: (-item['score'], -item['conflict_turns'], -item['recovery_action_turns'], item['paper_id']))
    return metrics


def row_map_from_table(table: pa.Table) -> Dict[str, Dict[str, Any]]:
    mapping: Dict[str, Dict[str, Any]] = {}
    for row in table.to_pylist():
        env_kwargs = row.get('env_kwargs') or {}
        paper_id = str(env_kwargs.get('paper_id') or row.get('id'))
        mapping[paper_id] = row
    return mapping


def select_rows(table: pa.Table, ids: List[str]) -> pa.Table:
    mapping = row_map_from_table(table)
    missing = [paper_id for paper_id in ids if paper_id not in mapping]
    if missing:
        raise KeyError(f'missing ids from source table: {missing}')
    ordered_rows = [mapping[paper_id] for paper_id in ids]
    return pa.Table.from_pylist(ordered_rows, schema=table.schema)


def main() -> None:
    recovery_relevant_ids = CARRYOVER_IDS + EXPANSION_IDS
    assert len(recovery_relevant_ids) == len(set(recovery_relevant_ids)) == 24
    assert set(REFERENCE_IDS).issubset(recovery_relevant_ids)

    pilot2_table = pq.read_table(PILOT2_PARQUET)
    pilot39_table = pq.read_table(PILOT39_PARQUET)

    main_recovery_table = select_rows(pilot2_table, recovery_relevant_ids)
    reference_table = select_rows(pilot2_table, REFERENCE_IDS)
    sentinel_table = select_rows(pilot39_table, SENTINEL_IDS).cast(main_recovery_table.schema, safe=False)

    pq.write_table(pa.concat_tables([main_recovery_table, sentinel_table]), MAIN_SUBSET_PATH)
    pq.write_table(pa.concat_tables([reference_table, sentinel_table]), REFERENCE_SUBSET_PATH)

    metrics = summarize_pilot2_signals()
    metric_map = {item['paper_id']: item for item in metrics}

    setup = {
        'frozen_commit': git_head(),
        'selection_rule': SELECTION_RULE,
        'runtime_note': RUNTIME_NOTE,
        'models': MODELS,
        'fixed_params': FIXED_PARAMS,
        'main_subset_path': str(MAIN_SUBSET_PATH),
        'reference_subset_path': str(REFERENCE_SUBSET_PATH),
        'recovery_relevant_ids': recovery_relevant_ids,
        'carryover_ids': CARRYOVER_IDS,
        'expansion_ids': EXPANSION_IDS,
        'reference_ids': REFERENCE_IDS,
        'historical_sentinel_ids': SENTINEL_IDS,
        'main_row_count': len(recovery_relevant_ids) + len(SENTINEL_IDS),
        'recovery_relevant_count': len(recovery_relevant_ids),
        'reference_row_count': len(REFERENCE_IDS) + len(SENTINEL_IDS),
        'reference_compare_count': len(REFERENCE_IDS),
        'historical_sentinel_count': len(SENTINEL_IDS),
        'sources': {
            'pilot2_jsonl': str(PILOT2_JSONL),
            'pilot2_parquet': str(PILOT2_PARQUET),
            'pilot39_parquet': str(PILOT39_PARQUET),
        },
    }
    SETUP_META_PATH.write_text(json.dumps(setup, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')

    selection_audit = {
        'selection_rule': SELECTION_RULE,
        'top_30_pilot2_candidates': metrics[:30],
        'recovery_relevant_candidates': [metric_map[paper_id] for paper_id in recovery_relevant_ids],
        'reference_candidates': [metric_map[paper_id] for paper_id in REFERENCE_IDS],
        'sentinels': SENTINEL_IDS,
    }
    SELECTION_AUDIT_PATH.write_text(json.dumps(selection_audit, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')

    print(json.dumps({
        'main_subset_path': str(MAIN_SUBSET_PATH),
        'reference_subset_path': str(REFERENCE_SUBSET_PATH),
        'setup_meta_path': str(SETUP_META_PATH),
        'selection_audit_path': str(SELECTION_AUDIT_PATH),
        'recovery_relevant_count': len(recovery_relevant_ids),
        'reference_compare_count': len(REFERENCE_IDS),
        'historical_sentinel_count': len(SENTINEL_IDS),
    }, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
