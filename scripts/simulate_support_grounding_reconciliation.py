#!/usr/bin/env python3
"""Offline support-grounding and claim-status reconciliation simulation.

Uses existing ReviewState outputs only. It tests whether non-fallback strong
support plus claim status reconciliation can recover accept decisions safely.
No runtime behavior is changed.
"""
from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List

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
    norm,
    open_unresolved_count,
)

DEFAULT_RESULTS = ROOT / 'outputs/results_main/review_infer/p25_1_state_hygiene_4b_focus.jsonl'
DEFAULT_GOLD = Path('/reviewF/datasets/drmas_review/test.parquet')
DEFAULT_META = ROOT / 'outputs/subsets/state_hygiene_4b_focus_meta.json'
DEFAULT_JSON = ROOT / 'outputs/results_main/review_infer/p25_1_support_grounding_reconciliation_sim.json'
DEFAULT_REPORT = ROOT / 'docs/experiments/SUPPORT_GROUNDING_RECONCILIATION_SIMULATION.md'

GENERIC_SOURCE_RE = re.compile(r'unknown|not specified|fallback|model|system', re.I)
META_RE = re.compile(r'provided excerpt|current evidence set|no grounded|invalid json|system uncertainty', re.I)


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


def valid_positive_evidence(ev: Dict[str, Any], *, allow_unsupported: bool = True) -> bool:
    cid = str(ev.get('claim_id') or '')
    if not cid or is_fallback_claim_id(cid):
        return False
    if norm(ev.get('strength')) != 'strong':
        return False
    if norm(ev.get('stance')) not in {'supports', 'partially_supports'}:
        return False
    source = str(ev.get('source') or '')
    text = f"{ev.get('evidence', '')} {source}"
    if not source.strip() or GENERIC_SOURCE_RE.search(source) or META_RE.search(text):
        return False
    return True


def strong_contradiction_claims(state: Dict[str, Any]) -> set[str]:
    claims = set()
    for ev in state.get('evidence_map', []) or []:
        cid = str(ev.get('claim_id') or '')
        if cid and norm(ev.get('strength')) == 'strong' and norm(ev.get('stance')) == 'contradicts':
            claims.add(cid)
    return claims


def reconcile_state(state: Dict[str, Any], *, min_support: int = 1) -> Dict[str, Any]:
    state = copy.deepcopy(state)
    claims = claim_index(state)
    contradictions = strong_contradiction_claims(state)
    support_counts = Counter()
    support_ids = {}
    for ev in state.get('evidence_map', []) or []:
        if valid_positive_evidence(ev):
            cid = str(ev.get('claim_id') or '')
            support_counts[cid] += 1
            support_ids.setdefault(cid, []).append(ev.get('evidence_id'))
    for cid, count in support_counts.items():
        claim = claims.get(cid)
        if not claim or cid in contradictions or count < min_support:
            continue
        if norm(claim.get('status')) == 'unsupported':
            claim['status'] = 'partially_supported' if count == 1 else 'supported'
            claim['support_grounding_reconciled'] = True
            claim['supporting_evidence_ids'] = sorted(set((claim.get('supporting_evidence_ids') or []) + [x for x in support_ids.get(cid, []) if x]))
    return state


def support_counts(state: Dict[str, Any], *, count_reconciled_status: bool = False) -> Dict[str, int]:
    claims = claim_index(state)
    total_valid = 0
    supported_valid = 0
    unsupported_valid = 0
    fallback_valid = 0
    for ev in state.get('evidence_map', []) or []:
        cid = str(ev.get('claim_id') or '')
        if is_fallback_claim_id(cid) and norm(ev.get('strength')) == 'strong' and norm(ev.get('stance')) in {'supports', 'partially_supports'}:
            fallback_valid += 1
        if valid_positive_evidence(ev):
            total_valid += 1
            status = norm((claims.get(cid) or {}).get('status'))
            if status in {'supported', 'partially_supported'}:
                supported_valid += 1
            elif status == 'unsupported':
                unsupported_valid += 1
    return {'valid': total_valid, 'supported_valid': supported_valid, 'unsupported_valid': unsupported_valid, 'fallback_strong': fallback_valid}


def flaw_counts(state: Dict[str, Any], *, grounded_only: bool = True, candidate_weight: float = 0.5) -> Dict[str, float]:
    ev_ids = evidence_ids(state)
    critical = 0.0
    major = 0.0
    for flaw in state.get('flaw_candidates', []) or []:
        status = norm(flaw.get('status')) or 'candidate'
        severity = norm(flaw.get('severity'))
        if status in {'downgraded', 'retracted'}:
            continue
        if grounded_only and not flaw_is_grounded(flaw, ev_ids):
            continue
        weight = 1.0 if status == 'confirmed' else candidate_weight
        if severity == 'critical':
            critical += weight
        if severity == 'major':
            major += weight
    return {'critical': critical, 'major': major}


def decide(state: Dict[str, Any], rule: str) -> str:
    sc = support_counts(state)
    strong = sc['valid'] if rule in {'SG1_nonfallback_support', 'SG2_reconcile_status'} else sc['supported_valid']
    if rule == 'baseline':
        from agent_system.environments.env_package.review.state import infer_final_decision
        return infer_final_decision(state, {})
    fc = flaw_counts(state, grounded_only=True, candidate_weight=0.5)
    unresolved = open_unresolved_count(state)
    conflicts = len(state.get('conflict_notes', []) or [])
    unresolved_reject = 6
    unresolved_accept = 3
    if rule in {'SG3_reconcile_plus_soft_unresolved', 'SG4_oracle_negatives_with_support_guard'}:
        unresolved_reject = 8
        unresolved_accept = 5
    if fc['critical'] >= 1 or fc['major'] >= 2 or unresolved >= unresolved_reject or conflicts >= 4:
        return 'reject'
    if strong >= 2 and fc['major'] < 1 and unresolved <= unresolved_accept:
        return 'accept'
    return 'reject'


def apply_rule(state: Dict[str, Any], rule: str) -> Dict[str, Any]:
    state = copy.deepcopy(state)
    if rule in {'SG2_reconcile_status', 'SG3_reconcile_plus_soft_unresolved'}:
        state = reconcile_state(state, min_support=1)
    if rule == 'SG4_oracle_negatives_with_support_guard':
        state = reconcile_state(state, min_support=1)
        state = apply_oracle_candidate_suppression(state)
        state = apply_oracle_question_cleanup(state)
    return state


def blocker_counts(rows: List[Dict[str, Any]], rule: str) -> Dict[str, int]:
    total = Counter()
    for row in rows:
        state = apply_rule(row.get('review_state', {}), rule)
        diag = decision_blockers(state, candidate_weight=0.5, grounded_only=True)
        if support_counts(state)['valid'] >= 2 and 'strong<2' in diag['blockers']:
            diag['blockers'] = [b for b in diag['blockers'] if b != 'strong<2']
        for blocker in diag['blockers']:
            total[blocker] += 1
    return dict(total)


def write_report(payload: Dict[str, Any], path: Path) -> None:
    lines = [
        '# Support Grounding + Claim-Status Reconciliation Simulation v1',
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
    lines += ['', '## 3. Rule Decision', '']
    safe = [name for name, data in payload['rules'].items() if name != 'baseline' and data['metrics']['recovered_accept_ids'] and not data['metrics']['false_accept_ids']]
    if safe:
        lines.append(f"Safe offline candidates: `{safe}`.")
        lines.append('Inspect case-level support before runtime implementation.')
    else:
        lines.append('No support-grounding rule safely recovered accept without false accepts.')
        lines.append('Do not implement runtime reconciliation yet; positive evidence extraction/mapping remains insufficient or ambiguous.')
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def main() -> None:
    parser = argparse.ArgumentParser(description='Offline support grounding reconciliation simulation.')
    parser.add_argument('--results-path', default=str(DEFAULT_RESULTS))
    parser.add_argument('--gold-path', default=str(DEFAULT_GOLD))
    parser.add_argument('--meta-path', default=str(DEFAULT_META))
    parser.add_argument('--selected-only', action='store_true')
    parser.add_argument('--output-json', default=str(DEFAULT_JSON))
    parser.add_argument('--report-path', default=str(DEFAULT_REPORT))
    args = parser.parse_args()

    rows = load_jsonl(Path(args.results_path))
    meta = json.loads(Path(args.meta_path).read_text(encoding='utf-8')) if Path(args.meta_path).exists() else {}
    if args.selected_only:
        keep = selected_ids(meta)
        rows = [row for row in rows if str(row.get('paper_id') or row.get('id')) in keep]
    gold = load_gold(Path(args.gold_path))
    ids = [row.get('paper_id') or row.get('id') for row in rows]
    rules = ['baseline', 'SG1_nonfallback_support', 'SG2_reconcile_status', 'SG3_reconcile_plus_soft_unresolved', 'SG4_oracle_negatives_with_support_guard']
    preds = {}
    for rule in rules:
        preds[rule] = {}
        for row in rows:
            pid = row.get('paper_id') or row.get('id')
            state = apply_rule(row.get('review_state', {}), rule)
            preds[rule][pid] = decide(state, rule)
    baseline = preds['baseline']
    payload = {'results_path': str(Path(args.results_path)), 'sample_count': len(rows), 'rules': {}}
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
