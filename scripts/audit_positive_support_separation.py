#!/usr/bin/env python3
"""Audit positive evidence/support separation in ReviewState outputs.

Run-output-only diagnostic. It checks whether positive evidence is real,
fallback-bound, attached to unsupported claims, or too weak to enter final
decision. No runtime behavior is changed.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List

import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.simulate_state_hygiene_decision import claim_support_maps, decision_blockers, norm  # noqa: E402

DEFAULT_RESULTS = ROOT / 'outputs/results_main/review_infer/p25_1_state_hygiene_4b_focus.jsonl'
DEFAULT_GOLD = Path('/reviewF/datasets/drmas_review/test.parquet')
DEFAULT_META = ROOT / 'outputs/subsets/state_hygiene_4b_focus_meta.json'
DEFAULT_JSON = ROOT / 'outputs/results_main/review_infer/p25_1_positive_support_audit.json'
DEFAULT_REPORT = ROOT / 'docs/experiments/POSITIVE_SUPPORT_SEPARATION_AUDIT.md'
DEFAULT_CASEBOOK = ROOT / 'docs/experiments/POSITIVE_SUPPORT_SEPARATION_CASEBOOK.md'

META_RE = re.compile(r'provided excerpt|current evidence set|no grounded|fallback|invalid json|could not verify|system uncertainty', re.I)
GENERIC_SOURCE_RE = re.compile(r'unknown|not specified|fallback|model|system', re.I)

ORACLE_RECOVERED = {'QAAsnSRwgu', 'KI9NqjLVDT'}
FALSE_FLIP = {'aTBE70xiFw'}


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


def claim_index(state: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    return {str(c.get('claim_id')): c for c in state.get('claims', []) or [] if c.get('claim_id')}


def is_fallback_claim_id(cid: str) -> bool:
    return 'fallback' in str(cid or '').lower()


def is_meta_evidence(ev: Dict[str, Any]) -> bool:
    text = f"{ev.get('evidence', '')} {ev.get('source', '')}"
    return bool(META_RE.search(text))


def is_generic_source(ev: Dict[str, Any]) -> bool:
    source = str(ev.get('source') or '')
    return not source.strip() or bool(GENERIC_SOURCE_RE.search(source))


def evidence_bucket(ev: Dict[str, Any], claims: Dict[str, Dict[str, Any]]) -> str:
    cid = str(ev.get('claim_id') or '')
    stance = norm(ev.get('stance'))
    strength = norm(ev.get('strength'))
    claim = claims.get(cid, {})
    if strength != 'strong' or stance not in {'supports', 'partially_supports'}:
        return 'not_strong_positive'
    if is_meta_evidence(ev) or is_generic_source(ev):
        return 'strong_positive_meta_or_generic'
    if is_fallback_claim_id(cid):
        return 'strong_positive_fallback_claim'
    if norm(claim.get('status')) == 'unsupported':
        return 'strong_positive_on_unsupported_claim'
    if norm(claim.get('status')) in {'supported', 'partially_supported'}:
        return 'strong_positive_on_supported_claim'
    return 'strong_positive_on_uncertain_claim'


def audit_row(row: Dict[str, Any], gold: Dict[str, str]) -> Dict[str, Any]:
    pid = row.get('paper_id') or row.get('id')
    state = row.get('review_state', {})
    claims = claim_index(state)
    evs = state.get('evidence_map', []) or []
    bucket_counts = Counter(evidence_bucket(ev, claims) for ev in evs)
    strong_supports, strong_contras = claim_support_maps(state)
    blockers = decision_blockers(state).get('blockers', [])
    claim_status_counts = Counter(norm(c.get('status')) or 'unknown' for c in claims.values())
    strong_claim_ids = {cid for cid, count in strong_supports.items() if count > 0}
    strong_2plus_claim_ids = {cid for cid, count in strong_supports.items() if count >= 2}
    fallback_strong_claim_ids = {cid for cid in strong_claim_ids if is_fallback_claim_id(cid)}
    unsupported_strong_claim_ids = {
        cid for cid in strong_claim_ids
        if norm((claims.get(cid) or {}).get('status')) == 'unsupported'
    }
    support_quality_label = 'no_strong_support'
    if bucket_counts['strong_positive_on_supported_claim'] >= 2:
        support_quality_label = 'sufficient_supported_positive'
    elif bucket_counts['strong_positive_on_supported_claim'] >= 1:
        support_quality_label = 'partial_supported_positive'
    elif bucket_counts['strong_positive_on_unsupported_claim'] >= 1:
        support_quality_label = 'positive_but_status_conflicted'
    elif bucket_counts['strong_positive_fallback_claim'] >= 1:
        support_quality_label = 'fallback_positive_only'
    elif bucket_counts['strong_positive_meta_or_generic'] >= 1:
        support_quality_label = 'meta_or_generic_positive_only'
    return {
        'paper_id': pid,
        'gold': gold.get(pid, ''),
        'pred': row.get('final_decision') or state.get('final_decision'),
        'analysis_group': 'oracle_recovered_accept' if pid in ORACLE_RECOVERED else ('false_flip_reject' if pid in FALSE_FLIP else 'other'),
        'claim_count': len(claims),
        'claim_status_counts': dict(claim_status_counts),
        'evidence_count': len(evs),
        'strong_positive_total': sum(v for k, v in bucket_counts.items() if k.startswith('strong_positive')),
        'strong_positive_on_supported_claim': bucket_counts['strong_positive_on_supported_claim'],
        'strong_positive_on_unsupported_claim': bucket_counts['strong_positive_on_unsupported_claim'],
        'strong_positive_on_uncertain_claim': bucket_counts['strong_positive_on_uncertain_claim'],
        'strong_positive_fallback_claim': bucket_counts['strong_positive_fallback_claim'],
        'strong_positive_meta_or_generic': bucket_counts['strong_positive_meta_or_generic'],
        'strong_support_claim_count': len(strong_claim_ids),
        'strong_2plus_claim_count': len(strong_2plus_claim_ids),
        'fallback_strong_claim_count': len(fallback_strong_claim_ids),
        'unsupported_strong_claim_count': len(unsupported_strong_claim_ids),
        'strong_contradiction_claim_count': len([cid for cid, count in strong_contras.items() if count > 0]),
        'support_quality_label': support_quality_label,
        'strong_lt_2_blocker': 'strong<2' in blockers,
        'blockers': blockers,
    }


def aggregate(cases: List[Dict[str, Any]]) -> Dict[str, Any]:
    total = Counter()
    labels = Counter()
    groups = defaultdict(Counter)
    for case in cases:
        labels[case['support_quality_label']] += 1
        groups[case['analysis_group']][case['support_quality_label']] += 1
        for key, value in case.items():
            if key.endswith('_count') or key in {
                'strong_positive_total', 'strong_positive_on_supported_claim', 'strong_positive_on_unsupported_claim',
                'strong_positive_on_uncertain_claim', 'strong_positive_fallback_claim', 'strong_positive_meta_or_generic'
            }:
                total[key] += int(value)
        total['strong_lt_2_blocker_samples'] += int(case['strong_lt_2_blocker'])
    return {'totals': dict(total), 'support_quality_labels': dict(labels), 'group_labels': {k: dict(v) for k, v in groups.items()}}


def write_report(payload: Dict[str, Any], report_path: Path, casebook_path: Path) -> None:
    agg = payload['aggregate']
    lines = [
        '# Positive Evidence / Support Separation Audit v1',
        '',
        f"**Input**: `{payload['results_path']}`",
        f"**Samples**: {payload['sample_count']}",
        '**Runtime behavior changed**: no',
        '',
        '## 1. Aggregate Support Counts',
        '',
        '| metric | count |',
        '|---|---:|',
    ]
    for key, value in sorted(agg['totals'].items()):
        lines.append(f'| `{key}` | {value} |')
    lines += ['', '## 2. Support Quality Labels', '', '| label | samples |', '|---|---:|']
    for key, value in sorted(agg['support_quality_labels'].items(), key=lambda kv: -kv[1]):
        lines.append(f'| `{key}` | {value} |')
    lines += ['', '## 3. Key Group Comparison', '']
    for group, counts in sorted(agg['group_labels'].items()):
        lines += [f'### {group}', '', '| label | samples |', '|---|---:|']
        for key, value in sorted(counts.items(), key=lambda kv: -kv[1]):
            lines.append(f'| `{key}` | {value} |')
        lines.append('')
    lines += [
        '## 4. Interpretation',
        '',
        '- If oracle-recovered accept cases have real strong support but final decision still blocks them, the next fix is support accounting / claim-status reconciliation.',
        '- If false-flip reject cases also look positive under the same support accounting, runtime accept relaxation is unsafe.',
        '- If most strong support is fallback/meta/unsupported-bound, the next fix is evidence-to-claim grounding rather than final decision thresholds.',
    ]
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text('\n'.join(lines) + '\n', encoding='utf-8')

    case_lines = [
        '# Positive Support Separation Casebook',
        '',
        '| paper_id | group | gold | pred | support label | strong+ total | strong+ supported | strong+ unsupported | strong+ fallback | strong+ meta/generic | strong<2 blocker | blockers |',
        '|---|---|---|---|---|---:|---:|---:|---:|---:|---|---|',
    ]
    for c in payload['cases']:
        case_lines.append(
            f"| {c['paper_id']} | {c['analysis_group']} | {c['gold']} | {c['pred']} | {c['support_quality_label']} | "
            f"{c['strong_positive_total']} | {c['strong_positive_on_supported_claim']} | {c['strong_positive_on_unsupported_claim']} | "
            f"{c['strong_positive_fallback_claim']} | {c['strong_positive_meta_or_generic']} | {c['strong_lt_2_blocker']} | {', '.join(c['blockers'])} |"
        )
    casebook_path.parent.mkdir(parents=True, exist_ok=True)
    casebook_path.write_text('\n'.join(case_lines) + '\n', encoding='utf-8')


def main() -> None:
    parser = argparse.ArgumentParser(description='Audit positive evidence/support separation.')
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
    cases = [audit_row(row, gold) for row in rows]
    payload = {
        'results_path': str(Path(args.results_path)),
        'selected_only': bool(args.selected_only),
        'sample_count': len(cases),
        'cases': cases,
        'aggregate': aggregate(cases),
    }
    Path(args.output_json).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output_json).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
    write_report(payload, Path(args.report_path), Path(args.casebook_path))
    print(json.dumps({'sample_count': len(cases), 'aggregate': payload['aggregate'], 'report_path': args.report_path}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
