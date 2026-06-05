#!/usr/bin/env python3
"""Build a fresh mixed accept/reject subset for state-hygiene validation.

This subset intentionally uses a larger dataset source than the original 39-row
test set and excludes the original 16 focus ids to reduce overfitting.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

import pyarrow as pa
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[1]
DATASET_PATH = Path('/reviewF/datasets/drmas_review_eval100/test.parquet')
OLD_META_PATH = ROOT / 'outputs/subsets/state_hygiene_4b_focus_meta.json'
OUTPUT_SUBSET_PATH = ROOT / 'outputs/subsets/state_hygiene_mixed_v2.parquet'
OUTPUT_META_PATH = ROOT / 'outputs/subsets/state_hygiene_mixed_v2_meta.json'

SELECT_ACCEPT = 8
SELECT_REJECT = 8


def load_old_ids() -> set[str]:
    if not OLD_META_PATH.exists():
        return set()
    meta = json.loads(OLD_META_PATH.read_text(encoding='utf-8'))
    ids = set(meta.get('selected_ids') or [])
    for group_ids in meta.get('groups', {}).values():
        ids.update(group_ids)
    return ids


def compact_row_summary(row: Dict) -> Dict:
    text = str(row.get('inputs') or row.get('prompt') or '')
    return {
        'id': row.get('id'),
        'decision': row.get('decision'),
        'rating': row.get('rating'),
        'year': row.get('year'),
        'input_chars': len(text),
    }


def main() -> None:
    rows = pq.read_table(DATASET_PATH).to_pylist()
    old_ids = load_old_ids()
    pool = [dict(row) for row in rows if row.get('id') not in old_ids]
    accepts = [row for row in pool if str(row.get('decision')).strip().lower() == 'accept']
    rejects = [row for row in pool if str(row.get('decision')).strip().lower() == 'reject']
    if len(accepts) < SELECT_ACCEPT or len(rejects) < SELECT_REJECT:
        raise SystemExit(f'Not enough rows after excluding old ids: accepts={len(accepts)}, rejects={len(rejects)}')
    # Deterministic spread: first rows by source order, but interleaved to avoid grouped runs.
    selected_accepts = accepts[:SELECT_ACCEPT]
    selected_rejects = rejects[:SELECT_REJECT]
    selected = []
    for idx in range(max(len(selected_accepts), len(selected_rejects))):
        if idx < len(selected_accepts):
            row = dict(selected_accepts[idx])
            row['state_hygiene_mixed_v2_group'] = 'fresh_accept'
            selected.append(row)
        if idx < len(selected_rejects):
            row = dict(selected_rejects[idx])
            row['state_hygiene_mixed_v2_group'] = 'fresh_reject'
            selected.append(row)
    for order, row in enumerate(selected):
        row['state_hygiene_mixed_v2_order'] = order

    OUTPUT_SUBSET_PATH.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(pa.Table.from_pylist(selected), OUTPUT_SUBSET_PATH)
    meta = {
        'dataset_path': str(DATASET_PATH),
        'old_focus_meta_path': str(OLD_META_PATH),
        'old_excluded_count': len(old_ids),
        'output_subset_path': str(OUTPUT_SUBSET_PATH),
        'selected_count': len(selected),
        'selected_ids': [row['id'] for row in selected],
        'groups': {
            'fresh_accept': [row['id'] for row in selected_accepts],
            'fresh_reject': [row['id'] for row in selected_rejects],
        },
        'case_table': {row['id']: compact_row_summary(row) for row in selected},
        'recommended_4b_command': [
            'conda', 'run', '-n', 'DrMAS-qwen35', 'python', '-u', '-m', 'agent_system.inference.review_runner',
            '--dataset-path', str(OUTPUT_SUBSET_PATH),
            '--model-path', '/reviewF/datasets/Qwen3___5-4B',
            '--temperature', '0.2',
            '--top-p', '0.95',
            '--mode', 's4',
            '--max-turns', '8',
            '--max-workers-per-turn', '2',
            '--manager-batch-size', '1',
            '--gpu-memory-utilization', '0.60',
            '--max-num-seqs', '64',
            '--max-model-len', '3072',
            '--max-tokens', '640',
            '--output-path', 'outputs/results_main/review_infer/p25_1_state_hygiene_mixed_v2.jsonl',
        ],
    }
    OUTPUT_META_PATH.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({
        'dataset_path': str(DATASET_PATH),
        'output_subset_path': str(OUTPUT_SUBSET_PATH),
        'output_meta_path': str(OUTPUT_META_PATH),
        'selected_count': len(selected),
        'groups': meta['groups'],
    }, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
