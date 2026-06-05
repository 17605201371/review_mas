#!/usr/bin/env python3
"""Offline final-decision interface hygiene simulation.

This is a run-output-only diagnostic. It does not change runtime behavior and
uses existing JSONL ReviewState outputs to test whether final-decision rules are
collapsing to reject because of flaw/unresolved/support interfaces.
"""
from __future__ import annotations

import argparse
import copy
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List

import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.simulate_state_hygiene_decision import (  # noqa: E402
    apply_claim_reconciliation,
    claim_support_maps,
    apply_generic_unresolved_cleanup,
    apply_oracle_candidate_suppression,
    apply_oracle_question_cleanup,
    apply_stale_gap_cleanup,
    decision_blockers,
    evidence_ids,
    flaw_is_grounded,
    hygiene_counts,
    norm,
    open_unresolved_count,
    raw_decision,
)

DEFAULT_GOLD = Path('/reviewF/datasets/drmas_review/test.parquet')
DEFAULT_META = ROOT / 'outputs/subsets/state_hygiene_4b_focus_meta.json'
DEFAULT_RESULTS = ROOT / 'outputs/results_main/review_infer/p25_1_state_hygiene_4b_focus.jsonl'
DEFAULT_JSON = ROOT / 'outputs/results_main/review_infer/p25_1_decision_interface_hygiene_sim.json'
DEFAULT_REPORT = ROOT / 'docs/experiments/DECISION_INTERFACE_HYGIENE_SIMULATION.md'


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]


def load_gold(path: Path) -> Dict[str, str]:
    return {row['id']: row['decision'] for row in pq.read_table(path).to_pylist()}


def load_meta(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}


def selected_ids(meta: Dict[str, Any]) -> set[str]:
    ids = list(meta.get('selected_ids') or [])
    if not ids:
        for group_ids in meta.get('groups', {}).values():
            ids.extend(group_ids)
    return {str(pid) for pid in ids}


def strong_support_count(state: Dict[str, Any]) -> int:
    return sum(
        1 for ev in state.get('evidence_map', []) or []
        if norm(ev.get('strength')) == 'strong' and norm(ev.get('stance')) in {'supports', 'partially_supports'}
    )


def flaw_counts(state: Dict[str, Any], *, confirmed_only: bool = False, grounded_only: bool = False, candidate_weight: float = 1.0) -> Dict[str, float]:
    ev_ids = evidence_ids(state)
    critical = 0.0
    major = 0.0
    for flaw in state.get('flaw_candidates', []) or []:
        status = norm(flaw.get('status')) or 'candidate'
        severity = norm(flaw.get('severity'))
        if status in {'downgraded', 'retracted'}:
            continue
        grounded = flaw_is_grounded(flaw, ev_ids)
        if confirmed_only and status != 'confirmed':
            continue
        if grounded_only and not grounded:
            continue
        weight = 1.0 if status == 'confirmed' else candidate_weight
        if severity == 'critical':
            critical += weight
        if severity == 'major':
            major += weight
    return {'critical': critical, 'major': major}


def interface_decision(
    state: Dict[str, Any],
    *,
    confirmed_only: bool = False,
    grounded_only: bool = False,
    candidate_weight: float = 1.0,
    unresolved_reject_threshold: int = 6,
    unresolved_accept_threshold: int = 3,
    allow_accept_with_soft_major: bool = False,
    conflict_reject_threshold: int = 4,
) -> str:
    counts = flaw_counts(state, confirmed_only=confirmed_only, grounded_only=grounded_only, candidate_weight=candidate_weight)
    strong = strong_support_count(state)
    unresolved = open_unresolved_count(state)
    conflicts = len(state.get('conflict_notes', []) or [])
    if counts['critical'] >= 1 or counts['major'] >= 2 or unresolved >= unresolved_reject_threshold or conflicts >= conflict_reject_threshold:
        return 'reject'
    major_ok = counts['major'] == 0 or (allow_accept_with_soft_major and counts['major'] < 1)
    if strong >= 2 and major_ok and unresolved <= unresolved_accept_threshold:
        return 'accept'
    return 'reject'




def _is_system_or_weak_unresolved(item: Any, strong_supports: Dict[str, int]) -> bool:
    text = str(item.get('question') if isinstance(item, dict) else item or '')
    has_target = bool(item.get('claim_id') or item.get('target_claim_id') or item.get('target_claim_ids') or item.get('claim_ids')) if isinstance(item, dict) else bool(__import__('re').search(r'claim-(?:fallback-)?\d+', text, __import__('re').I))
    meta = bool(__import__('re').search(r'provided excerpt|excerpt limitation|current evidence set|no grounded|fallback|invalid json|blocked by policy|recovery failed|system uncertainty', text, __import__('re').I))
    generic = bool(__import__('re').search(r'verify whether|locate a concrete|check whether|needs more evidence|more context|full paper|methodology details|replace this fallback|paper text is incomplete', text, __import__('re').I))
    stale = any(str(cid) in text and count >= 1 for cid, count in strong_supports.items())
    return meta or generic or stale or not has_target


def apply_lifecycle_cleanup(state: Dict[str, Any], *, keep_grounded_only: bool = True) -> Dict[str, Any]:
    state = copy.deepcopy(state)
    strong_supports, _ = claim_support_maps(state)
    cleaned_questions = []
    for item in state.get('unresolved_questions', []) or []:
        text = str(item.get('question') if isinstance(item, dict) else item or '')
        is_grounded = bool(__import__('re').search(r'claim-(?:fallback-)?\d+', text, __import__('re').I)) and not _is_system_or_weak_unresolved(item, strong_supports)
        if keep_grounded_only and not is_grounded:
            if isinstance(item, dict):
                new_item = copy.deepcopy(item)
                new_item['status'] = 'resolved'
                new_item['hygiene_lifecycle_closed'] = True
                cleaned_questions.append(new_item)
            continue
        cleaned_questions.append(item)
    state['unresolved_questions'] = cleaned_questions
    ev_ids = evidence_ids(state)
    for flaw in state.get('flaw_candidates', []) or []:
        status = norm(flaw.get('status')) or 'candidate'
        if status != 'candidate':
            continue
        if not flaw_is_grounded(flaw, ev_ids):
            flaw['status'] = 'downgraded'
            flaw['hygiene_lifecycle_downgraded_ungrounded'] = True
    return state

def apply_variant_state(state: Dict[str, Any], variant: str) -> Dict[str, Any]:
    state = copy.deepcopy(state)
    if variant in {'baseline', 'DI1_grounded_flaw_only', 'DI4_confirmed_only_flaw'}:
        return state
    if variant in {'DI2_grounded_flaw_stale_cleanup', 'DI3_balanced_hygiene'}:
        state = apply_claim_reconciliation(state, 'supported')
        state = apply_stale_gap_cleanup(state)
        state = apply_generic_unresolved_cleanup(state)
        return state
    if variant == 'DI5_lifecycle_cleanup':
        state = apply_claim_reconciliation(state, 'supported')
        state = apply_stale_gap_cleanup(state)
        state = apply_lifecycle_cleanup(state, keep_grounded_only=True)
        return state
    if variant == 'DI_ORACLE_no_candidates_no_unresolved':
        state = apply_claim_reconciliation(state, 'supported')
        state = apply_oracle_candidate_suppression(state)
        state = apply_oracle_question_cleanup(state)
        return state
    raise ValueError(f'unknown variant: {variant}')


def predict(state: Dict[str, Any], variant: str) -> str:
    if variant == 'baseline':
        return raw_decision(state)
    if variant == 'DI1_grounded_flaw_only':
        return interface_decision(state, grounded_only=True, candidate_weight=1.0)
    if variant == 'DI2_grounded_flaw_stale_cleanup':
        return interface_decision(state, grounded_only=True, candidate_weight=1.0)
    if variant == 'DI3_balanced_hygiene':
        return interface_decision(
            state,
            grounded_only=True,
            candidate_weight=0.5,
            unresolved_reject_threshold=8,
            unresolved_accept_threshold=5,
            allow_accept_with_soft_major=True,
        )
    if variant == 'DI4_confirmed_only_flaw':
        return interface_decision(state, confirmed_only=True, candidate_weight=0.0)
    if variant == 'DI5_lifecycle_cleanup':
        return interface_decision(state, grounded_only=True, candidate_weight=0.5, unresolved_reject_threshold=6, unresolved_accept_threshold=3)
    if variant == 'DI_ORACLE_no_candidates_no_unresolved':
        return raw_decision(state)
    raise ValueError(f'unknown variant: {variant}')


def metrics(preds: Dict[str, str], gold: Dict[str, str], ids: Iterable[str], baseline: Dict[str, str]) -> Dict[str, Any]:
    tp = tn = fp = fn = 0
    pred_ctr = Counter()
    gold_ctr = Counter()
    flips = []
    recovered_accept = []
    false_accept = []
    for pid in ids:
        g = norm(gold[pid])
        p = norm(preds[pid])
        b = norm(baseline[pid])
        pred_ctr[p] += 1
        gold_ctr[g] += 1
        if g == 'accept' and p == 'accept':
            tp += 1
        elif g == 'accept':
            fn += 1
        elif p == 'accept':
            fp += 1
        else:
            tn += 1
        if p != b:
            flips.append(pid)
            if g == 'accept' and p == 'accept':
                recovered_accept.append(pid)
            if g == 'reject' and p == 'accept':
                false_accept.append(pid)
    n = tp + tn + fp + fn
    acc = (tp + tn) / n if n else 0.0
    ap = tp / (tp + fp) if (tp + fp) else 0.0
    ar = tp / (tp + fn) if (tp + fn) else 0.0
    af1 = 2 * ap * ar / (ap + ar) if (ap + ar) else 0.0
    rp = tn / (tn + fn) if (tn + fn) else 0.0
    rr = tn / (tn + fp) if (tn + fp) else 0.0
    rf1 = 2 * rp * rr / (rp + rr) if (rp + rr) else 0.0
    return {
        'n': n,
        'gold_dist': dict(gold_ctr),
        'predicted_dist': dict(pred_ctr),
        'accuracy': acc,
        'macro_f1': (af1 + rf1) / 2,
        'accept_precision': ap,
        'accept_recall': ar,
        'reject_recall': rr,
        'confusion': {
            'gold_accept_pred_accept': tp,
            'gold_accept_pred_nonaccept': fn,
            'gold_reject_pred_accept': fp,
            'gold_reject_pred_nonaccept': tn,
        },
        'flips': flips,
        'recovered_accept_ids': recovered_accept,
        'false_accept_ids': false_accept,
    }


def aggregate_blockers_for_rows(rows: List[Dict[str, Any]], variant: str) -> Dict[str, int]:
    total = Counter()
    for row in rows:
        state = apply_variant_state(row.get('review_state', {}), variant)
        if variant in {'DI1_grounded_flaw_only', 'DI2_grounded_flaw_stale_cleanup', 'DI3_balanced_hygiene', 'DI5_lifecycle_cleanup'}:
            diag = decision_blockers(state, candidate_weight=0.5 if variant in {'DI3_balanced_hygiene', 'DI5_lifecycle_cleanup'} else 1.0, grounded_only=True)
        elif variant == 'DI4_confirmed_only_flaw':
            diag = decision_blockers(state, candidate_weight=0.0, grounded_only=False)
        else:
            diag = decision_blockers(state)
        for blocker in diag['blockers']:
            total[blocker] += 1
    return dict(total)


def write_report(payload: Dict[str, Any], path: Path) -> None:
    variants = payload['variants']
    lines = [
        '# Decision Interface Hygiene Simulation v1',
        '',
        f"**Input**: `{payload['results_path']}`",
        f"**Samples**: {payload['sample_count']}",
        '**Runtime behavior changed**: no',
        '',
        '## 1. Summary',
        '',
        '| variant | acc | macro-F1 | accept R | reject R | pred A | pred R | flips | recovered A | false A |',
        '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|',
    ]
    for name, data in variants.items():
        m = data['metrics']
        pd = m['predicted_dist']
        lines.append(
            f"| `{name}` | {m['accuracy']:.4f} | {m['macro_f1']:.4f} | {m['accept_recall']:.4f} | {m['reject_recall']:.4f} | "
            f"{pd.get('accept', 0)} | {pd.get('reject', 0)} | {len(m['flips'])} | {len(m['recovered_accept_ids'])} | {len(m['false_accept_ids'])} |"
        )
    lines += ['', '## 2. Key Flips', '']
    for name, data in variants.items():
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
    lines += ['', '## 3. Blocker Distribution', '']
    for name, data in variants.items():
        lines += [f'### {name}', '', '| blocker | samples |', '|---|---:|']
        for key, value in sorted(data['blockers'].items(), key=lambda kv: -kv[1]):
            lines.append(f'| `{key}` | {value} |')
        lines.append('')
    lines += [
        '## 4. Decision',
        '',
        '- If all non-oracle variants still predict zero accepts, the immediate blocker is not a missing runtime controller. It is that final-decision inputs remain dominated by unresolved/strong-support/flaw blockers.',
        '- If a non-oracle variant restores accept recall without false accepts on stable reject controls, that variant becomes the candidate for a minimal runtime state-hygiene fix.',
        '- Oracle results are upper-bound diagnostics only and must not be treated as deployable policy.',
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def main() -> None:
    parser = argparse.ArgumentParser(description='Offline decision-interface hygiene simulation.')
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
    variants = [
        'baseline',
        'DI1_grounded_flaw_only',
        'DI2_grounded_flaw_stale_cleanup',
        'DI3_balanced_hygiene',
        'DI4_confirmed_only_flaw',
        'DI5_lifecycle_cleanup',
        'DI_ORACLE_no_candidates_no_unresolved',
    ]
    pred_by_variant: Dict[str, Dict[str, str]] = {}
    for variant in variants:
        pred_by_variant[variant] = {}
        for row in rows:
            pid = row.get('paper_id') or row.get('id')
            state = apply_variant_state(row.get('review_state', {}), variant)
            pred_by_variant[variant][pid] = predict(state, variant)
    baseline = pred_by_variant['baseline']
    payload = {
        'results_path': str(Path(args.results_path)),
        'gold_path': str(Path(args.gold_path)),
        'meta_path': str(Path(args.meta_path)),
        'selected_only': bool(args.selected_only),
        'sample_count': len(ids),
        'variants': {},
        'hygiene_totals': Counter(),
    }
    for variant in variants:
        payload['variants'][variant] = {
            'metrics': metrics(pred_by_variant[variant], gold, ids, baseline),
            'blockers': aggregate_blockers_for_rows(rows, variant),
        }
    total = Counter()
    for row in rows:
        total.update(hygiene_counts(row.get('review_state', {})))
    payload['hygiene_totals'] = dict(total)

    Path(args.output_json).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output_json).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
    write_report(payload, Path(args.report_path))
    print(json.dumps({
        'samples': len(ids),
        'report_path': args.report_path,
        'variants': {name: data['metrics'] for name, data in payload['variants'].items()},
    }, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
