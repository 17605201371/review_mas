#!/usr/bin/env python3
"""Audit unresolved-question and candidate-flaw lifecycle hygiene.

Run-output-only diagnostic. It does not change runtime behavior. The goal is to
separate genuine paper-blocking defects from stale/system/fallback unresolved
items and ungrounded candidate flaws.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.simulate_state_hygiene_decision import (  # noqa: E402
    claim_support_maps,
    evidence_ids,
    flaw_is_grounded,
    flaw_is_meta_or_excerpt,
    hygiene_counts,
    is_stale_gap,
    norm,
)

DEFAULT_RESULTS = ROOT / 'outputs/results_main/review_infer/p25_1_state_hygiene_4b_focus.jsonl'
DEFAULT_GOLD = Path('/reviewF/datasets/drmas_review/test.parquet')
DEFAULT_META = ROOT / 'outputs/subsets/state_hygiene_4b_focus_meta.json'
DEFAULT_JSON = ROOT / 'outputs/results_main/review_infer/p25_1_lifecycle_hygiene_audit.json'
DEFAULT_REPORT = ROOT / 'docs/experiments/UNRESOLVED_CANDIDATE_LIFECYCLE_AUDIT.md'
DEFAULT_CASEBOOK = ROOT / 'docs/experiments/UNRESOLVED_CANDIDATE_LIFECYCLE_CASEBOOK.md'

META_RE = re.compile(
    r'provided excerpt|excerpt limitation|insufficient excerpt|current evidence set|no grounded|fallback|invalid json|blocked by policy|recovery failed|could not be verified|system uncertainty',
    re.I,
)
FALLBACK_RE = re.compile(r'claim-fallback|fallback', re.I)
RECOVERY_RE = re.compile(r'recovery|patch|blocked by policy|no effect|validator', re.I)
GENERIC_UNRESOLVED_RE = re.compile(
    r'verify whether|locate a concrete|check whether|needs more evidence|more context|full paper|methodology details|replace this fallback|paper text is incomplete',
    re.I,
)


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


def item_text(item: Any) -> str:
    if isinstance(item, dict):
        return str(item.get('question') or item.get('description') or item.get('text') or '')
    return str(item or '')


def item_target_claim(item: Any) -> str:
    if isinstance(item, dict):
        for key in ('claim_id', 'target_claim_id'):
            if item.get(key):
                return str(item[key])
        ids = item.get('target_claim_ids') or item.get('claim_ids') or []
        if ids:
            return str(ids[0])
    m = re.search(r'claim-(?:fallback-)?\d+', item_text(item), re.I)
    return m.group(0) if m else ''


def item_evidence_ids(item: Any) -> List[str]:
    if not isinstance(item, dict):
        return []
    ids = item.get('evidence_ids') or item.get('supporting_evidence_ids') or []
    return [str(x) for x in ids if x]


def classify_unresolved(item: Any, strong_supports: Dict[str, int]) -> Dict[str, Any]:
    text = item_text(item)
    target = item_target_claim(item)
    evs = item_evidence_ids(item)
    status = norm(item.get('status')) if isinstance(item, dict) else 'open'
    is_open = status in {'', 'open'}
    meta = bool(META_RE.search(text))
    fallback = bool(FALLBACK_RE.search(text) or FALLBACK_RE.search(target))
    recovery = bool(RECOVERY_RE.search(text))
    generic = bool(GENERIC_UNRESOLVED_RE.search(text))
    resolvable = bool(target and strong_supports.get(target, 0) >= 1) or is_stale_gap(text, strong_supports)
    grounded = bool(target or evs) and not (meta or fallback or generic)
    if meta:
        label = 'system_meta_or_excerpt'
    elif fallback:
        label = 'fallback_uncertainty'
    elif recovery:
        label = 'recovery_failure_uncertainty'
    elif resolvable:
        label = 'resolvable_by_existing_support'
    elif generic:
        label = 'generic_system_question'
    elif grounded:
        label = 'grounded_paper_unresolved'
    else:
        label = 'weak_or_unowned_unresolved'
    return {
        'label': label,
        'open': is_open,
        'target_claim_id': target,
        'has_target_claim': bool(target),
        'has_evidence': bool(evs),
        'meta': meta,
        'fallback': fallback,
        'recovery': recovery,
        'generic': generic,
        'resolvable_by_existing_support': resolvable,
        'grounded': grounded,
    }


def classify_flaw(flaw: Dict[str, Any], ev_ids: set) -> Dict[str, Any]:
    text = f"{flaw.get('title', '')} {flaw.get('description', '')}"
    status = norm(flaw.get('status')) or 'candidate'
    severity = norm(flaw.get('severity'))
    grounded = flaw_is_grounded(flaw, ev_ids)
    meta = flaw_is_meta_or_excerpt(flaw) or bool(META_RE.search(text))
    fallback = bool(FALLBACK_RE.search(text))
    recovery = bool(RECOVERY_RE.search(text))
    if status == 'confirmed' and grounded:
        label = 'confirmed_grounded_flaw'
    elif meta:
        label = 'system_meta_candidate'
    elif fallback:
        label = 'fallback_candidate'
    elif recovery:
        label = 'recovery_failure_candidate'
    elif status == 'candidate' and grounded:
        label = 'grounded_candidate'
    elif status == 'candidate':
        label = 'ungrounded_candidate'
    else:
        label = f'{status}_flaw'
    return {
        'label': label,
        'status': status,
        'severity': severity,
        'grounded': grounded,
        'meta': meta,
        'fallback': fallback,
        'recovery': recovery,
        'used_for_reject': status not in {'downgraded', 'retracted'} and severity in {'major', 'critical'},
    }


def audit_row(row: Dict[str, Any], gold: Dict[str, str]) -> Dict[str, Any]:
    pid = row.get('paper_id') or row.get('id')
    state = row.get('review_state', {})
    strong_supports, _ = claim_support_maps(state)
    ev_ids = evidence_ids(state)
    unresolved = [classify_unresolved(item, strong_supports) for item in state.get('unresolved_questions', []) or []]
    flaws = [classify_flaw(flaw, ev_ids) for flaw in state.get('flaw_candidates', []) or []]
    u_ctr = Counter(u['label'] for u in unresolved if u['open'])
    f_ctr = Counter(f['label'] for f in flaws)
    return {
        'paper_id': pid,
        'gold': gold.get(pid, ''),
        'pred': row.get('final_decision') or state.get('final_decision'),
        'unresolved_count': len(unresolved),
        'open_unresolved_count': sum(1 for u in unresolved if u['open']),
        'unresolved_with_target_claim_count': sum(1 for u in unresolved if u['has_target_claim']),
        'unresolved_with_evidence_count': sum(1 for u in unresolved if u['has_evidence']),
        'unresolved_from_recovery_failure_count': sum(1 for u in unresolved if u['recovery']),
        'unresolved_from_fallback_count': sum(1 for u in unresolved if u['fallback']),
        'unresolved_from_system_meta_count': sum(1 for u in unresolved if u['meta']),
        'unresolved_resolvable_by_existing_support_count': sum(1 for u in unresolved if u['resolvable_by_existing_support']),
        'grounded_paper_unresolved_count': u_ctr.get('grounded_paper_unresolved', 0),
        'weak_or_system_unresolved_count': sum(v for k, v in u_ctr.items() if k != 'grounded_paper_unresolved'),
        'unresolved_label_counts': dict(u_ctr),
        'candidate_flaw_count': sum(1 for f in flaws if f['status'] == 'candidate'),
        'candidate_with_grounded_evidence_count': sum(1 for f in flaws if f['status'] == 'candidate' and f['grounded']),
        'candidate_without_evidence_count': sum(1 for f in flaws if f['status'] == 'candidate' and not f['grounded']),
        'candidate_from_fallback_count': sum(1 for f in flaws if f['fallback']),
        'candidate_from_recovery_failure_count': sum(1 for f in flaws if f['recovery']),
        'candidate_from_excerpt_limitation_count': sum(1 for f in flaws if f['meta']),
        'candidate_used_for_reject_count': sum(1 for f in flaws if f['status'] == 'candidate' and f['used_for_reject']),
        'candidate_label_counts': dict(f_ctr),
        'confirmed_flaw_count': sum(1 for f in flaws if f['status'] == 'confirmed'),
        'downgraded_flaw_count': sum(1 for f in flaws if f['status'] == 'downgraded'),
        'retracted_flaw_count': sum(1 for f in flaws if f['status'] == 'retracted'),
        'hygiene_counts': hygiene_counts(state),
    }


def aggregate(cases: List[Dict[str, Any]]) -> Dict[str, Any]:
    total = Counter()
    unresolved_labels = Counter()
    candidate_labels = Counter()
    for case in cases:
        for key, value in case.items():
            if key.endswith('_count'):
                total[key] += int(value)
        unresolved_labels.update(case.get('unresolved_label_counts', {}))
        candidate_labels.update(case.get('candidate_label_counts', {}))
    return {'totals': dict(total), 'unresolved_labels': dict(unresolved_labels), 'candidate_labels': dict(candidate_labels)}


def write_report(payload: Dict[str, Any], report_path: Path, casebook_path: Path) -> None:
    agg = payload['aggregate']
    lines = [
        '# Unresolved + Candidate Flaw Lifecycle Audit',
        '',
        f"**Input**: `{payload['results_path']}`",
        f"**Samples**: {payload['sample_count']}",
        '**Runtime behavior changed**: no',
        '',
        '## 1. Aggregate Counts',
        '',
        '| metric | count |',
        '|---|---:|',
    ]
    for key, value in sorted(agg['totals'].items()):
        lines.append(f'| `{key}` | {value} |')
    lines += ['', '## 2. Open Unresolved Labels', '', '| label | count |', '|---|---:|']
    for key, value in sorted(agg['unresolved_labels'].items(), key=lambda kv: -kv[1]):
        lines.append(f'| `{key}` | {value} |')
    lines += ['', '## 3. Flaw Labels', '', '| label | count |', '|---|---:|']
    for key, value in sorted(agg['candidate_labels'].items(), key=lambda kv: -kv[1]):
        lines.append(f'| `{key}` | {value} |')
    lines += [
        '',
        '## 4. Direction',
        '',
        '- If weak/system unresolved dominates, the next simulation should close or downgrade those items before final decision.',
        '- If grounded candidates dominate, candidate cleanup alone is unsafe; promotion/confirmation rules are needed.',
        '- If ungrounded/meta candidates dominate reject use, candidate grounding filter is the next runtime candidate after offline validation.',
    ]
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text('\n'.join(lines) + '\n', encoding='utf-8')

    case_lines = [
        '# Unresolved + Candidate Lifecycle Casebook',
        '',
        '| paper_id | gold | pred | open unresolved | weak/system unresolved | grounded unresolved | candidates | grounded candidates | ungrounded candidates | candidate used reject | top unresolved labels | top flaw labels |',
        '|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|',
    ]
    for case in payload['cases']:
        u_labels = ', '.join(f'{k}:{v}' for k, v in sorted(case['unresolved_label_counts'].items(), key=lambda kv: -kv[1])[:3])
        f_labels = ', '.join(f'{k}:{v}' for k, v in sorted(case['candidate_label_counts'].items(), key=lambda kv: -kv[1])[:3])
        case_lines.append(
            f"| {case['paper_id']} | {case['gold']} | {case['pred']} | {case['open_unresolved_count']} | "
            f"{case['weak_or_system_unresolved_count']} | {case['grounded_paper_unresolved_count']} | {case['candidate_flaw_count']} | "
            f"{case['candidate_with_grounded_evidence_count']} | {case['candidate_without_evidence_count']} | {case['candidate_used_for_reject_count']} | {u_labels} | {f_labels} |"
        )
    casebook_path.parent.mkdir(parents=True, exist_ok=True)
    casebook_path.write_text('\n'.join(case_lines) + '\n', encoding='utf-8')


def main() -> None:
    parser = argparse.ArgumentParser(description='Audit unresolved/candidate flaw lifecycle hygiene.')
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
        'gold_path': str(Path(args.gold_path)),
        'meta_path': str(Path(args.meta_path)),
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
