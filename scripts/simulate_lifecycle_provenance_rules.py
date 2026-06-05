#!/usr/bin/env python3
"""Offline provenance-aware lifecycle rule simulation.

This script uses existing ReviewState JSONL output only. It tries narrow rules
for unresolved/candidate flaw lifecycle cleanup and checks whether any rule can
recover accept decisions without flipping reject controls.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.simulate_decision_interface_hygiene import interface_decision, metrics, selected_ids  # noqa: E402
from scripts.simulate_state_hygiene_decision import (  # noqa: E402
    apply_claim_reconciliation,
    apply_stale_gap_cleanup,
    evidence_ids,
    flaw_is_grounded,
    flaw_is_meta_or_excerpt,
    hygiene_counts,
    norm,
)

DEFAULT_RESULTS = ROOT / 'outputs/results_main/review_infer/p25_1_state_hygiene_4b_focus.jsonl'
DEFAULT_GOLD = Path('/reviewF/datasets/drmas_review/test.parquet')
DEFAULT_META = ROOT / 'outputs/subsets/state_hygiene_4b_focus_meta.json'
DEFAULT_JSON = ROOT / 'outputs/results_main/review_infer/p25_1_lifecycle_provenance_sim.json'
DEFAULT_REPORT = ROOT / 'docs/experiments/LIFECYCLE_PROVENANCE_RULE_SIMULATION.md'

META_RE = re.compile(r'provided excerpt|excerpt limitation|current evidence set|no grounded|invalid json|blocked by policy|recovery failed|system uncertainty', re.I)
GENERIC_RE = re.compile(r'verify whether|locate a concrete|check whether|needs more evidence|more context|full paper|methodology details|paper text is incomplete', re.I)
CLAIM_RE = re.compile(r'claim-(?:fallback-)?\d+', re.I)


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]


def load_gold(path: Path) -> Dict[str, str]:
    return {row['id']: row['decision'] for row in pq.read_table(path).to_pylist()}


def load_meta(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}


def item_text(item: Any) -> str:
    if isinstance(item, dict):
        return str(item.get('question') or item.get('description') or item.get('text') or '')
    return str(item or '')


def has_claim_target(item: Any) -> bool:
    if isinstance(item, dict):
        if item.get('claim_id') or item.get('target_claim_id') or item.get('target_claim_ids') or item.get('claim_ids'):
            return True
    return bool(CLAIM_RE.search(item_text(item)))


def unresolved_label(item: Any) -> str:
    text = item_text(item)
    if META_RE.search(text):
        return 'system_meta'
    if GENERIC_RE.search(text):
        return 'generic_system'
    if not has_claim_target(item):
        return 'unowned_weak'
    return 'paper_targeted'


def flaw_label(flaw: Dict[str, Any], ev_ids: set) -> str:
    text = f"{flaw.get('title', '')} {flaw.get('description', '')}"
    status = norm(flaw.get('status')) or 'candidate'
    if status == 'confirmed' and flaw_is_grounded(flaw, ev_ids):
        return 'confirmed_grounded'
    if flaw_is_meta_or_excerpt(flaw) or META_RE.search(text):
        return 'system_meta'
    if status == 'candidate' and flaw_is_grounded(flaw, ev_ids):
        return 'grounded_candidate'
    if status == 'candidate':
        return 'ungrounded_candidate'
    return status or 'unknown'


def apply_rule(state: Dict[str, Any], rule: str) -> Dict[str, Any]:
    import copy
    state = copy.deepcopy(state)
    ev_ids = evidence_ids(state)

    if rule in {'baseline', 'decision_grounded_only'}:
        return state

    if rule in {'R1_close_system_unresolved', 'R3_close_system_and_meta_candidates', 'R4_targeted_lifecycle', 'R5_targeted_plus_reconcile'}:
        cleaned = []
        for item in state.get('unresolved_questions', []) or []:
            label = unresolved_label(item)
            should_close = label in {'system_meta', 'generic_system'}
            if rule in {'R4_targeted_lifecycle', 'R5_targeted_plus_reconcile'}:
                # More conservative: leave unowned weak questions open; close only system/generic.
                should_close = label in {'system_meta', 'generic_system'}
            if should_close:
                if isinstance(item, dict):
                    new_item = copy.deepcopy(item)
                    new_item['status'] = 'resolved'
                    new_item['lifecycle_sim_closed_reason'] = label
                    cleaned.append(new_item)
                continue
            cleaned.append(item)
        state['unresolved_questions'] = cleaned

    if rule in {'R2_downgrade_meta_ungrounded_candidates', 'R3_close_system_and_meta_candidates', 'R4_targeted_lifecycle', 'R5_targeted_plus_reconcile'}:
        for flaw in state.get('flaw_candidates', []) or []:
            if norm(flaw.get('status')) != 'candidate':
                continue
            label = flaw_label(flaw, ev_ids)
            should_downgrade = False
            if rule == 'R2_downgrade_meta_ungrounded_candidates':
                should_downgrade = label in {'system_meta', 'ungrounded_candidate'}
            elif rule == 'R3_close_system_and_meta_candidates':
                should_downgrade = label == 'system_meta'
            elif rule in {'R4_targeted_lifecycle', 'R5_targeted_plus_reconcile'}:
                # Keep grounded candidates as concerns; downgrade only system/meta and ungrounded critical/major candidates.
                should_downgrade = label == 'system_meta' or (label == 'ungrounded_candidate' and norm(flaw.get('severity')) in {'major', 'critical'})
            if should_downgrade:
                flaw['status'] = 'downgraded'
                flaw['lifecycle_sim_downgraded_reason'] = label

    if rule == 'R5_targeted_plus_reconcile':
        state = apply_claim_reconciliation(state, 'supported')
        state = apply_stale_gap_cleanup(state)
    return state


def predict(state: Dict[str, Any], rule: str) -> str:
    if rule == 'baseline':
        return interface_decision(state)
    if rule == 'decision_grounded_only':
        return interface_decision(state, grounded_only=True, candidate_weight=0.5)
    if rule in {'R1_close_system_unresolved', 'R2_downgrade_meta_ungrounded_candidates', 'R3_close_system_and_meta_candidates'}:
        return interface_decision(state, grounded_only=True, candidate_weight=0.5, unresolved_reject_threshold=6, unresolved_accept_threshold=3)
    if rule in {'R4_targeted_lifecycle', 'R5_targeted_plus_reconcile'}:
        return interface_decision(state, grounded_only=True, candidate_weight=0.5, unresolved_reject_threshold=8, unresolved_accept_threshold=4)
    raise ValueError(rule)


def blocker_counts(rows: List[Dict[str, Any]], rule: str) -> Dict[str, int]:
    total = Counter()
    for row in rows:
        state = apply_rule(row.get('review_state', {}), rule)
        # mirror prediction policy enough for diagnostic blocker counts
        from scripts.simulate_state_hygiene_decision import decision_blockers
        diag = decision_blockers(state, candidate_weight=0.5, grounded_only=True)
        for blocker in diag['blockers']:
            total[blocker] += 1
    return dict(total)


def write_report(payload: Dict[str, Any], path: Path) -> None:
    lines = [
        '# Lifecycle Provenance Rule Simulation v1',
        '',
        f"**Input**: `{payload['results_path']}`",
        f"**Samples**: {payload['sample_count']}",
        '**Runtime behavior changed**: no',
        '',
        '## 1. Rule Summary',
        '',
        '| rule | acc | macro-F1 | accept R | reject R | pred A | pred R | recovered A | false A | decision |',
        '|---|---:|---:|---:|---:|---:|---:|---:|---:|---|',
    ]
    for name, data in payload['rules'].items():
        m = data['metrics']
        pd = m['predicted_dist']
        decision = 'candidate' if m['recovered_accept_ids'] and not m['false_accept_ids'] else 'reject'
        if name == 'baseline':
            decision = 'baseline'
        lines.append(
            f"| `{name}` | {m['accuracy']:.4f} | {m['macro_f1']:.4f} | {m['accept_recall']:.4f} | {m['reject_recall']:.4f} | "
            f"{pd.get('accept', 0)} | {pd.get('reject', 0)} | {len(m['recovered_accept_ids'])} | {len(m['false_accept_ids'])} | {decision} |"
        )
    lines += ['', '## 2. Flips', '']
    for name, data in payload['rules'].items():
        if name == 'baseline':
            continue
        m = data['metrics']
        lines += [
            f'### {name}',
            '',
            f"- recovered_accept_ids: `{m['recovered_accept_ids']}`",
            f"- false_accept_ids: `{m['false_accept_ids']}`",
            f"- all_flips: `{m['flips']}`",
            '',
        ]
    lines += ['', '## 3. Decision', '']
    candidates = [name for name, data in payload['rules'].items() if name != 'baseline' and data['metrics']['recovered_accept_ids'] and not data['metrics']['false_accept_ids']]
    if candidates:
        lines += [
            f"Safe offline candidates: `{candidates}`.",
            '',
            'These rules should be inspected per case before any runtime implementation.',
        ]
    else:
        lines += [
            'No non-oracle provenance rule recovered accept without false accepts.',
            '',
            'Do not implement runtime lifecycle cleanup yet. The current state lacks enough positive evidence/support separation; cleanup-only rules remain unsafe or ineffective.',
        ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def main() -> None:
    parser = argparse.ArgumentParser(description='Offline lifecycle provenance rule simulation.')
    parser.add_argument('--results-path', default=str(DEFAULT_RESULTS))
    parser.add_argument('--gold-path', default=str(DEFAULT_GOLD))
    parser.add_argument('--meta-path', default=str(DEFAULT_META))
    parser.add_argument('--selected-only', action='store_true')
    parser.add_argument('--output-json', default=str(DEFAULT_JSON))
    parser.add_argument('--report-path', default=str(DEFAULT_REPORT))
    args = parser.parse_args()

    rows = load_jsonl(Path(args.results_path))
    meta = load_meta(Path(args.meta_path))
    if args.selected_only:
        keep = selected_ids(meta)
        rows = [row for row in rows if str(row.get('paper_id') or row.get('id')) in keep]
    gold = load_gold(Path(args.gold_path))
    ids = [row.get('paper_id') or row.get('id') for row in rows]
    rules = [
        'baseline',
        'decision_grounded_only',
        'R1_close_system_unresolved',
        'R2_downgrade_meta_ungrounded_candidates',
        'R3_close_system_and_meta_candidates',
        'R4_targeted_lifecycle',
        'R5_targeted_plus_reconcile',
    ]
    preds = {}
    for rule in rules:
        preds[rule] = {}
        for row in rows:
            pid = row.get('paper_id') or row.get('id')
            state = apply_rule(row.get('review_state', {}), rule)
            preds[rule][pid] = predict(state, rule)
    baseline = preds['baseline']
    payload = {
        'results_path': str(Path(args.results_path)),
        'selected_only': bool(args.selected_only),
        'sample_count': len(rows),
        'rules': {},
    }
    for rule in rules:
        payload['rules'][rule] = {
            'metrics': metrics(preds[rule], gold, ids, baseline),
            'blockers': blocker_counts(rows, rule),
        }
    Path(args.output_json).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output_json).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
    write_report(payload, Path(args.report_path))
    print(json.dumps({rule: payload['rules'][rule]['metrics'] for rule in rules}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
