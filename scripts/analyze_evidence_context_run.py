#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List

POS_RE = re.compile(r'\b(support|supports|supported|outperform|improve|improvement|effective|achieve|state-of-the-art|validate|demonstrate)\b', re.I)
INSUFF_RE = re.compile(r'insufficient excerpt|cannot verify|no grounded|lacks? evidence|not enough evidence', re.I)


def norm(v: Any) -> str:
    return str(v or '').strip().lower()


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]


def evidence_calls(row: Dict[str, Any]) -> List[Dict[str, Any]]:
    out = []
    for turn in row.get('turn_logs', []) or []:
        selected = turn.get('selected_agents') or []
        if 'Evidence Agent' in selected or turn.get('evidence_context_mode'):
            payloads = []
            for item in turn.get('worker_payloads', []) or []:
                if item.get('agent_id') == 'Evidence Agent':
                    payloads.append(item.get('payload') or {})
            out.append({'turn': turn, 'payloads': payloads})
    return out


def evidence_items(row: Dict[str, Any]) -> List[Dict[str, Any]]:
    return row.get('review_state', {}).get('evidence_map', []) or []


def is_real_claim(cid: str) -> bool:
    cid = str(cid or '')
    return bool(cid) and 'fallback' not in cid.lower() and 'general' not in cid.lower()


def summarize(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    total_calls = 0
    rows_with_context = 0
    context = Counter()
    parse = Counter()
    raw_pos = 0
    raw_insuff = 0
    final_strong = 0
    strong_real = 0
    strong_fallback = 0
    unbound_strong = 0
    fallback_extraction_strong = 0
    binding_error_count = 0
    binding_status_counts = Counter()
    accept_2plus = 0
    rows_2plus_real = 0
    per_row = []
    for row in rows:
        calls = evidence_calls(row)
        total_calls += len(calls)
        row_strong_real = 0
        row_context_seen = False
        for item in calls:
            turn = item['turn']
            if turn.get('evidence_context_mode'):
                row_context_seen = True
            if turn.get('evidence_context_cleaned_wrapper'):
                context['cleaned_wrapper'] += 1
            for key in ['method', 'results', 'conclusion', 'table_or_figure']:
                if turn.get(f'evidence_context_contains_{key}'):
                    context[f'contains_{key}'] += 1
            if turn.get('evidence_context_chars'):
                context['chars_total'] += int(turn.get('evidence_context_chars') or 0)
            payloads = item.get('payloads') or []
            if payloads:
                parse['payload_count'] += 1
            for payload in payloads:
                payload_text = json.dumps(payload, ensure_ascii=False)
                if POS_RE.search(payload_text):
                    raw_pos += 1
                if INSUFF_RE.search(payload_text):
                    raw_insuff += 1
                if any(str(ev.get('evidence_id') or '').startswith(('evidence-fallback-', 'evidence-general-')) for ev in payload.get('evidence_map', []) or []):
                    parse['fallback_payload'] += 1
        if row_context_seen:
            rows_with_context += 1
        for ev in evidence_items(row):
            if norm(ev.get('strength')) == 'strong' and norm(ev.get('stance')) in {'supports', 'partially_supports'}:
                final_strong += 1
                cid = str(ev.get('claim_id') or '')
                binding_status = norm(ev.get('binding_status')) or 'missing'
                binding_status_counts[binding_status] += 1
                if binding_status in {'unbound', 'fallback_bound', 'invalid_claim_id', 'fallback_unverified'}:
                    binding_error_count += 1
                    unbound_strong += 1
                if norm(ev.get('source')) == 'fallback-extraction':
                    fallback_extraction_strong += 1
                if is_real_claim(cid) and binding_status in {'bound_real_claim', 'unchecked', 'missing'}:
                    strong_real += 1
                    row_strong_real += 1
                else:
                    strong_fallback += 1
        if row_strong_real >= 2:
            rows_2plus_real += 1
        if norm(row.get('ground_truth_decision')) == 'accept' and row_strong_real >= 2:
            accept_2plus += 1
        per_row.append({
            'paper_id': row.get('paper_id'),
            'gold': row.get('ground_truth_decision'),
            'final_decision': row.get('final_decision') or row.get('review_state', {}).get('final_decision'),
            'evidence_calls': len(calls),
            'strong_support_real': row_strong_real,
            'strong_support_total': sum(1 for ev in evidence_items(row) if norm(ev.get('strength')) == 'strong' and norm(ev.get('stance')) in {'supports', 'partially_supports'}),
        })
    avg_chars = context['chars_total'] / total_calls if total_calls else 0
    return {
        'rows': len(rows),
        'evidence_calls': total_calls,
        'rows_with_context': rows_with_context,
        'visible_method_rate': context['contains_method'] / total_calls if total_calls else 0,
        'visible_results_rate': context['contains_results'] / total_calls if total_calls else 0,
        'visible_conclusion_rate': context['contains_conclusion'] / total_calls if total_calls else 0,
        'visible_table_or_figure_rate': context['contains_table_or_figure'] / total_calls if total_calls else 0,
        'avg_evidence_context_chars': avg_chars,
        'evidence_valid_payload_rate': parse['payload_count'] / total_calls if total_calls else 0,
        'evidence_fallback_payload_count': parse['fallback_payload'],
        'evidence_parse_error_count': parse['parse_error'],
        'raw_positive_evidence_mentions': raw_pos,
        'raw_insufficient_excerpt_mentions': raw_insuff,
        'final_strong_support_total': final_strong,
        'strong_support_on_real_claim': strong_real,
        'strong_support_on_fallback_claim': strong_fallback,
        'unbound_strong_support': unbound_strong,
        'fallback_extraction_strong_support': fallback_extraction_strong,
        'evidence_binding_error_count': binding_error_count,
        'strong_support_binding_precision': (strong_real / final_strong) if final_strong else 0,
        'binding_status_counts': dict(binding_status_counts),
        'rows_with_2plus_real_strong_support': rows_2plus_real,
        'accept_samples_with_2plus_real_strong_support': accept_2plus,
        'per_row': per_row,
    }


def write_report(payload: Dict[str, Any], path: Path, title: str) -> None:
    lines = [f'# {title}', '', f"Input: `{payload['input']}`", '', '## Summary', '', '| metric | value |', '|---|---:|']
    for key, value in payload['summary'].items():
        if key == 'per_row':
            continue
        if isinstance(value, float):
            lines.append(f'| `{key}` | {value:.4f} |')
        else:
            lines.append(f'| `{key}` | {value} |')
    lines += ['', '## Per Row', '', '| paper_id | gold | final | evidence calls | strong real | strong total |', '|---|---|---|---:|---:|---:|']
    for row in payload['summary']['per_row']:
        lines.append(f"| {row['paper_id']} | {row['gold']} | {row['final_decision']} | {row['evidence_calls']} | {row['strong_support_real']} | {row['strong_support_total']} |")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--results-path', required=True)
    parser.add_argument('--output-json', default='')
    parser.add_argument('--report-path', required=True)
    parser.add_argument('--title', default='Evidence Context Run Analysis')
    args = parser.parse_args()
    rows = load_jsonl(Path(args.results_path))
    payload = {'input': args.results_path, 'summary': summarize(rows)}
    if args.output_json:
        Path(args.output_json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output_json).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
    write_report(payload, Path(args.report_path), args.title)
    print(json.dumps(payload['summary'], ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
