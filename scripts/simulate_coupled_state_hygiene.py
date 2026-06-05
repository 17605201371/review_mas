#!/usr/bin/env python3
"""Offline coupled state-hygiene simulation.

This tests whether negative lifecycle cleanup becomes safe when it is coupled
with non-fallback positive support accounting. No runtime behavior is changed.
"""
from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List

import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.simulate_decision_interface_hygiene import metrics, selected_ids  # noqa: E402
from scripts.simulate_state_hygiene_decision import (  # noqa: E402
    apply_oracle_candidate_suppression,
    apply_oracle_question_cleanup,
    decision_blockers,
    evidence_ids,
    flaw_is_grounded,
    flaw_is_meta_or_excerpt,
    infer_final_decision,
    norm,
    open_unresolved_count,
)

DEFAULT_RESULTS = ROOT / 'outputs/results_main/review_infer/p25_1_state_hygiene_4b_focus.jsonl'
DEFAULT_GOLD = Path('/reviewF/datasets/drmas_review/test.parquet')
DEFAULT_META = ROOT / 'outputs/subsets/state_hygiene_4b_focus_meta.json'
DEFAULT_JSON = ROOT / 'outputs/results_main/review_infer/p25_1_coupled_state_hygiene_sim.json'
DEFAULT_REPORT = ROOT / 'docs/experiments/COUPLED_STATE_HYGIENE_SIMULATION.md'
DEFAULT_CASEBOOK = ROOT / 'docs/experiments/COUPLED_STATE_HYGIENE_CASEBOOK.md'

META_RE = re.compile(r'provided excerpt|excerpt limitation|current evidence set|no grounded|invalid json|blocked by policy|recovery failed|system uncertainty', re.I)
GENERIC_RE = re.compile(r'verify whether|locate a concrete|check whether|needs more evidence|more context|full paper|methodology details|paper text is incomplete', re.I)
GENERIC_SOURCE_RE = re.compile(r'unknown|not specified|fallback|model|system', re.I)
CLAIM_RE = re.compile(r'claim-(?:fallback-)?\d+', re.I)


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]


def load_gold(path: Path) -> Dict[str, str]:
    return {row['id']: row['decision'] for row in pq.read_table(path).to_pylist()}


def load_meta(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}


def is_fallback_claim_id(cid: str) -> bool:
    return 'fallback' in str(cid or '').lower()


def claim_index(state: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    return {str(c.get('claim_id')): c for c in state.get('claims', []) or [] if c.get('claim_id')}


def item_text(item: Any) -> str:
    if isinstance(item, dict):
        return str(item.get('question') or item.get('description') or item.get('text') or '')
    return str(item or '')


def item_has_claim_target(item: Any) -> bool:
    if isinstance(item, dict) and (item.get('claim_id') or item.get('target_claim_id') or item.get('target_claim_ids') or item.get('claim_ids')):
        return True
    return bool(CLAIM_RE.search(item_text(item)))


def unresolved_label(item: Any) -> str:
    text = item_text(item)
    if META_RE.search(text):
        return 'system_meta'
    if GENERIC_RE.search(text):
        return 'generic_system'
    if not item_has_claim_target(item):
        return 'unowned_weak'
    return 'paper_targeted'


def valid_positive_evidence(ev: Dict[str, Any]) -> bool:
    cid = str(ev.get('claim_id') or '')
    if not cid or is_fallback_claim_id(cid):
        return False
    if norm(ev.get('strength')) != 'strong' or norm(ev.get('stance')) not in {'supports', 'partially_supports'}:
        return False
    source = str(ev.get('source') or '')
    text = f"{ev.get('evidence', '')} {source}"
    if not source.strip() or GENERIC_SOURCE_RE.search(source) or META_RE.search(text):
        return False
    return True


def strong_contradiction_claims(state: Dict[str, Any]) -> set[str]:
    out = set()
    for ev in state.get('evidence_map', []) or []:
        cid = str(ev.get('claim_id') or '')
        if cid and norm(ev.get('strength')) == 'strong' and norm(ev.get('stance')) == 'contradicts':
            out.add(cid)
    return out


def reconcile_claims(state: Dict[str, Any], min_support: int = 1) -> Dict[str, Any]:
    state = copy.deepcopy(state)
    claims = claim_index(state)
    contradicted = strong_contradiction_claims(state)
    support_counts = Counter()
    support_ids = {}
    for ev in state.get('evidence_map', []) or []:
        if valid_positive_evidence(ev):
            cid = str(ev.get('claim_id') or '')
            support_counts[cid] += 1
            support_ids.setdefault(cid, []).append(ev.get('evidence_id'))
    for cid, count in support_counts.items():
        claim = claims.get(cid)
        if not claim or cid in contradicted or count < min_support:
            continue
        if norm(claim.get('status')) == 'unsupported':
            claim['status'] = 'partially_supported' if count == 1 else 'supported'
            claim['coupled_hygiene_reconciled'] = True
            claim['supporting_evidence_ids'] = sorted(set((claim.get('supporting_evidence_ids') or []) + [x for x in support_ids.get(cid, []) if x]))
    return state


def cleanup_unresolved(state: Dict[str, Any], mode: str) -> Dict[str, Any]:
    state = copy.deepcopy(state)
    cleaned = []
    for item in state.get('unresolved_questions', []) or []:
        label = unresolved_label(item)
        should_close = False
        if mode == 'system_only':
            should_close = label in {'system_meta', 'generic_system'}
        elif mode == 'system_and_unowned':
            should_close = label in {'system_meta', 'generic_system', 'unowned_weak'}
        if should_close:
            if isinstance(item, dict):
                new_item = copy.deepcopy(item)
                new_item['status'] = 'resolved'
                new_item['coupled_hygiene_closed_reason'] = label
                cleaned.append(new_item)
            continue
        cleaned.append(item)
    state['unresolved_questions'] = cleaned
    return state


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


def cleanup_candidates(state: Dict[str, Any], mode: str) -> Dict[str, Any]:
    state = copy.deepcopy(state)
    ev_ids = evidence_ids(state)
    for flaw in state.get('flaw_candidates', []) or []:
        if norm(flaw.get('status')) != 'candidate':
            continue
        label = flaw_label(flaw, ev_ids)
        should_downgrade = False
        if mode == 'meta_only':
            should_downgrade = label == 'system_meta'
        elif mode == 'ungrounded_major':
            should_downgrade = label == 'system_meta' or (label == 'ungrounded_candidate' and norm(flaw.get('severity')) in {'major', 'critical'})
        if should_downgrade:
            flaw['status'] = 'downgraded'
            flaw['coupled_hygiene_downgraded_reason'] = label
    return state


def support_count(state: Dict[str, Any], supported_only: bool = False) -> int:
    claims = claim_index(state)
    count = 0
    for ev in state.get('evidence_map', []) or []:
        if not valid_positive_evidence(ev):
            continue
        if supported_only and norm((claims.get(str(ev.get('claim_id') or '')) or {}).get('status')) not in {'supported', 'partially_supported'}:
            continue
        count += 1
    return count


def flaw_counts(state: Dict[str, Any]) -> Dict[str, float]:
    ev_ids = evidence_ids(state)
    critical = 0.0
    major = 0.0
    for flaw in state.get('flaw_candidates', []) or []:
        status = norm(flaw.get('status')) or 'candidate'
        severity = norm(flaw.get('severity'))
        if status in {'downgraded', 'retracted'}:
            continue
        if not flaw_is_grounded(flaw, ev_ids):
            continue
        weight = 1.0 if status == 'confirmed' else 0.5
        if severity == 'critical':
            critical += weight
        if severity == 'major':
            major += weight
    return {'critical': critical, 'major': major}


def apply_rule(state: Dict[str, Any], rule: str) -> Dict[str, Any]:
    state = copy.deepcopy(state)
    if rule == 'baseline':
        return state
    if rule in {'C1_system_unresolved_meta_candidate', 'C2_system_unresolved_ungrounded_candidate', 'C3_unowned_unresolved_ungrounded_candidate'}:
        state = reconcile_claims(state, min_support=1)
    if rule == 'C1_system_unresolved_meta_candidate':
        state = cleanup_unresolved(state, 'system_only')
        state = cleanup_candidates(state, 'meta_only')
    elif rule == 'C2_system_unresolved_ungrounded_candidate':
        state = cleanup_unresolved(state, 'system_only')
        state = cleanup_candidates(state, 'ungrounded_major')
    elif rule == 'C3_unowned_unresolved_ungrounded_candidate':
        state = cleanup_unresolved(state, 'system_and_unowned')
        state = cleanup_candidates(state, 'ungrounded_major')
    elif rule == 'C4_oracle_negative_plus_support_guard':
        state = reconcile_claims(state, min_support=1)
        from scripts.simulate_state_hygiene_decision import apply_oracle_candidate_suppression, apply_oracle_question_cleanup
        state = apply_oracle_candidate_suppression(state)
        state = apply_oracle_question_cleanup(state)
    return state


def decide(state: Dict[str, Any], rule: str) -> str:
    if rule == 'baseline':
        return infer_final_decision(state, {})
    strong = support_count(state, supported_only=False)
    flaws = flaw_counts(state)
    unresolved = open_unresolved_count(state)
    conflicts = len(state.get('conflict_notes', []) or [])
    unresolved_reject = 6 if rule in {'C1_system_unresolved_meta_candidate', 'C2_system_unresolved_ungrounded_candidate'} else 8
    unresolved_accept = 3 if rule in {'C1_system_unresolved_meta_candidate', 'C2_system_unresolved_ungrounded_candidate'} else 5
    if flaws['critical'] >= 1 or flaws['major'] >= 2 or unresolved >= unresolved_reject or conflicts >= 4:
        return 'reject'
    if strong >= 2 and flaws['major'] < 1 and unresolved <= unresolved_accept:
        return 'accept'
    return 'reject'


def blocker_counts(rows: List[Dict[str, Any]], rule: str) -> Dict[str, int]:
    total = Counter()
    for row in rows:
        state = apply_rule(row.get('review_state', {}), rule)
        diag = decision_blockers(state, candidate_weight=0.5, grounded_only=True)
        if support_count(state) >= 2:
            diag['blockers'] = [b for b in diag['blockers'] if b != 'strong<2']
        for blocker in diag['blockers']:
            total[blocker] += 1
    return dict(total)


def load_gold(path: Path) -> Dict[str, str]:
    return {row['id']: row['decision'] for row in pq.read_table(path).to_pylist()}


def write_report(payload: Dict[str, Any], report_path: Path, casebook_path: Path) -> None:
    lines = [
        '# Coupled State Hygiene Simulation v1',
        '',
        f"**Input**: `{payload['results_path']}`",
        f"**Samples**: {payload['sample_count']}",
        '**Runtime behavior changed**: no',
        '',
        '## 1. Summary',
        '',
        '| rule | acc | macro-F1 | accept R | reject R | pred A | pred R | recovered A | false A | decision |',
        '|---|---:|---:|---:|---:|---:|---:|---:|---:|---|',
    ]
    for rule, data in payload['rules'].items():
        m = data['metrics']
        pd = m['predicted_dist']
        decision = 'candidate' if m['recovered_accept_ids'] and not m['false_accept_ids'] else 'reject'
        if rule == 'baseline':
            decision = 'baseline'
        lines.append(
            f"| `{rule}` | {m['accuracy']:.4f} | {m['macro_f1']:.4f} | {m['accept_recall']:.4f} | {m['reject_recall']:.4f} | "
            f"{pd.get('accept', 0)} | {pd.get('reject', 0)} | {len(m['recovered_accept_ids'])} | {len(m['false_accept_ids'])} | {decision} |"
        )
    lines += ['', '## 2. Flips', '']
    for rule, data in payload['rules'].items():
        if rule == 'baseline':
            continue
        m = data['metrics']
        lines += [
            f'### {rule}',
            '',
            f"- recovered_accept_ids: `{m['recovered_accept_ids']}`",
            f"- false_accept_ids: `{m['false_accept_ids']}`",
            f"- all_flips: `{m['flips']}`",
            '',
        ]
    safe = [rule for rule, data in payload['rules'].items() if rule != 'baseline' and data['metrics']['recovered_accept_ids'] and not data['metrics']['false_accept_ids']]
    lines += ['', '## 3. Decision', '']
    if safe:
        lines += [f"Safe offline candidate(s): `{safe}`.", 'Review case details before runtime implementation.']
    else:
        lines += ['No coupled non-oracle rule safely recovered accept.', 'Runtime state hygiene should still be deferred.']
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text('\n'.join(lines) + '\n', encoding='utf-8')

    case_lines = [
        '# Coupled State Hygiene Casebook',
        '',
        '| paper_id | gold | baseline | C1 | C2 | C3 | C4 oracle | support_count_after_C3 | unresolved_after_C3 | blockers_C3 |',
        '|---|---|---|---|---|---|---|---:|---:|---|',
    ]
    for case in payload['cases']:
        case_lines.append(
            f"| {case['paper_id']} | {case['gold']} | {case['baseline']} | {case['C1_system_unresolved_meta_candidate']} | "
            f"{case['C2_system_unresolved_ungrounded_candidate']} | {case['C3_unowned_unresolved_ungrounded_candidate']} | "
            f"{case['C4_oracle_negative_plus_support_guard']} | {case['support_count_after_C3']} | {case['unresolved_after_C3']} | {', '.join(case['blockers_C3'])} |"
        )
    casebook_path.parent.mkdir(parents=True, exist_ok=True)
    casebook_path.write_text('\n'.join(case_lines) + '\n', encoding='utf-8')


def main() -> None:
    parser = argparse.ArgumentParser(description='Offline coupled state hygiene simulation.')
    parser.add_argument('--results-path', default=str(DEFAULT_RESULTS))
    parser.add_argument('--gold-path', default=str(DEFAULT_GOLD))
    parser.add_argument('--meta-path', default=str(DEFAULT_META))
    parser.add_argument('--selected-only', action='store_true')
    parser.add_argument('--output-json', default=str(DEFAULT_JSON))
    parser.add_argument('--report-path', default=str(DEFAULT_REPORT))
    parser.add_argument('--casebook-path', default=str(DEFAULT_CASEBOOK))
    args = parser.parse_args()

    rows = load_jsonl(Path(args.results_path))
    meta = load_meta(Path(args.meta_path))
    if args.selected_only:
        keep = selected_ids(meta)
        rows = [row for row in rows if str(row.get('paper_id') or row.get('id')) in keep]
    gold = load_gold(Path(args.gold_path))
    ids = [row.get('paper_id') or row.get('id') for row in rows]
    rules = ['baseline', 'C1_system_unresolved_meta_candidate', 'C2_system_unresolved_ungrounded_candidate', 'C3_unowned_unresolved_ungrounded_candidate', 'C4_oracle_negative_plus_support_guard']
    preds = {rule: {} for rule in rules}
    for row in rows:
        pid = row.get('paper_id') or row.get('id')
        for rule in rules:
            state = apply_rule(row.get('review_state', {}), rule)
            preds[rule][pid] = decide(state, rule)
    baseline = preds['baseline']
    payload = {'results_path': str(Path(args.results_path)), 'sample_count': len(rows), 'rules': {}, 'cases': []}
    for rule in rules:
        payload['rules'][rule] = {'metrics': metrics(preds[rule], gold, ids, baseline), 'blockers': blocker_counts(rows, rule)}
    for row in rows:
        pid = row.get('paper_id') or row.get('id')
        c3_state = apply_rule(row.get('review_state', {}), 'C3_unowned_unresolved_ungrounded_candidate')
        payload['cases'].append({
            'paper_id': pid,
            'gold': gold.get(pid, ''),
            **{rule: preds[rule][pid] for rule in rules},
            'support_count_after_C3': support_count(c3_state),
            'unresolved_after_C3': open_unresolved_count(c3_state),
            'blockers_C3': decision_blockers(c3_state, candidate_weight=0.5, grounded_only=True).get('blockers', []),
        })
    Path(args.output_json).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output_json).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
    write_report(payload, Path(args.report_path), Path(args.casebook_path))
    print(json.dumps({rule: payload['rules'][rule]['metrics'] for rule in rules}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
