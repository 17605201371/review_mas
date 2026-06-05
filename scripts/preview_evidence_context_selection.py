#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pyarrow.parquet as pq

SECTION_PATTERNS: List[Tuple[str, re.Pattern[str]]] = [
    ('abstract', re.compile(r'\babstract\b', re.IGNORECASE)),
    ('method', re.compile(r'\b(method|methods|methodology|approach|model|framework)\b', re.IGNORECASE)),
    ('results', re.compile(r'\b(experiment|experiments|evaluation|results|analysis)\b', re.IGNORECASE)),
    ('table_or_figure', re.compile(r'\b(table|figure|ablation)\b', re.IGNORECASE)),
    ('conclusion', re.compile(r'\b(conclusion|conclusions|discussion)\b', re.IGNORECASE)),
]


def normalize(text: Any, max_length: int = 64000) -> str:
    return str(text or '').strip()[:max_length]


def clean_paper_body(text: str) -> Tuple[str, bool]:
    raw = normalize(text)
    cleaned = False
    begin = re.search(r'---\s*BEGIN\s+PAPER\s*---', raw, re.IGNORECASE)
    if begin:
        raw = raw[begin.end():]
        cleaned = True
    end = re.search(r'---\s*END\s+PAPER\s*---', raw, re.IGNORECASE)
    if end:
        raw = raw[:end.start()]
        cleaned = True
    lines = []
    skip_prefixes = ('[instruction]', 'format requirements', 'you are', 'return json', 'output json')
    for line in raw.splitlines():
        stripped = line.strip()
        low = stripped.lower()
        if not stripped:
            continue
        if any(low.startswith(prefix) for prefix in skip_prefixes):
            cleaned = True
            continue
        lines.append(stripped)
    return '\n'.join(lines).strip(), cleaned


def window_around(text: str, pos: int, window: int = 520) -> str:
    start = max(0, pos - window // 3)
    end = min(len(text), pos + window)
    return re.sub(r'\s+', ' ', text[start:end]).strip()


def evidence_context(text: str, max_length: int = 2400) -> Tuple[str, Dict[str, Any]]:
    body, cleaned = clean_paper_body(text)
    snippets: List[Tuple[str, str]] = []
    spans: List[Tuple[int, int]] = []

    def add(source: str, pos: int, window: int = 520) -> None:
        start = max(0, pos - window // 3)
        end = min(len(body), pos + window)
        for old_start, old_end in spans:
            if min(end, old_end) - max(start, old_start) > 160:
                return
        spans.append((start, end))
        snippet = window_around(body, pos, window)
        if snippet:
            snippets.append((source, snippet))

    if body:
        add('abstract', 0, 700)
    for source, pattern in SECTION_PATTERNS:
        m = pattern.search(body)
        if m:
            add(source, m.start(), 620 if source in {'results', 'table_or_figure'} else 540)
    if not snippets and body:
        snippets.append(('body_start', re.sub(r'\s+', ' ', body[:max_length]).strip()))
    sources: List[str] = []
    parts = []
    for source, snippet in snippets:
        if source not in sources:
            sources.append(source)
        parts.append(f'[{source}] {snippet}')
    ctx = '\n\n'.join(parts)[:max_length].strip()
    src = set(sources)
    return ctx or 'No paper text available.', {
        'evidence_context_chars': len(ctx),
        'evidence_context_cleaned_wrapper': cleaned,
        'evidence_context_contains_method': 'method' in src,
        'evidence_context_contains_results': 'results' in src,
        'evidence_context_contains_conclusion': 'conclusion' in src,
        'evidence_context_contains_table_or_figure': 'table_or_figure' in src,
        'evidence_context_snippet_sources': sources,
    }


def load_meta(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}


def selected_ids(meta: Dict[str, Any], limit: int) -> List[str]:
    ids: List[str] = []
    groups = meta.get('groups') or {}
    for group in ('fresh_accept', 'fresh_reject', 'accept', 'reject'):
        for pid in groups.get(group, []) or []:
            if pid not in ids:
                ids.append(pid)
            if len(ids) >= limit:
                return ids
    for pid in meta.get('selected_ids') or []:
        if pid not in ids:
            ids.append(pid)
        if len(ids) >= limit:
            return ids
    return ids[:limit]


def compact(text: str, limit: int = 700) -> str:
    text = ' '.join(str(text or '').split())
    return text[:limit] + ('...' if len(text) > limit else '')


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--dataset-path', default='outputs/subsets/state_hygiene_mixed_v2.parquet')
    parser.add_argument('--meta-path', default='outputs/subsets/state_hygiene_mixed_v2_meta.json')
    parser.add_argument('--limit', type=int, default=5)
    parser.add_argument('--report-path', default='docs/experiments/EVIDENCE_CONTEXT_SELECTION_V1_PREVIEW.md')
    args = parser.parse_args()
    rows = pq.read_table(args.dataset_path).to_pylist()
    meta = load_meta(Path(args.meta_path))
    ids = selected_ids(meta, args.limit)
    id_set = set(ids)
    rows = [row for row in rows if str(row.get('paper_id') or row.get('id')) in id_set]
    rows.sort(key=lambda row: ids.index(str(row.get('paper_id') or row.get('id'))))
    lines = ['# Evidence Context Selection v1 Preview', '', f'- Dataset: `{args.dataset_path}`', f'- Samples previewed: {len(rows)}', '- Runtime behavior changed: no model run; static context rendering only.', '']
    for row in rows:
        paper_text = normalize(row.get('paper_text') or row.get('question') or row.get('paper') or row.get('task_description'))
        if not paper_text:
            env_kwargs = row.get('env_kwargs') if isinstance(row.get('env_kwargs'), dict) else {}
            paper_text = normalize(env_kwargs.get('paper_text'))
        if not paper_text:
            inputs_val = row.get('inputs')
            msg_list = None
            if isinstance(row.get('prompt'), list):
                msg_list = row.get('prompt')
            elif isinstance(inputs_val, str) and inputs_val.strip().startswith('['):
                try:
                    msg_list = json.loads(inputs_val)
                except Exception:
                    msg_list = None
            if isinstance(msg_list, list):
                for item in msg_list:
                    if isinstance(item, dict) and item.get('role') == 'user':
                        content = normalize(item.get('content'))
                        if len(content) > len(paper_text):
                            paper_text = content
        old = paper_text[:800] or 'No paper text available.'
        new, meta_info = evidence_context(paper_text, 2400)
        pid = str(row.get('paper_id') or row.get('id'))
        gold = str(row.get('ground_truth_decision') or row.get('decision') or '').lower()
        lines += [
            f'## {pid}', '', f'- gold_decision: `{gold}`', f'- old_chars: {len(old)}', f'- new_chars: {len(new)}', f'- cleaned_wrapper: `{meta_info["evidence_context_cleaned_wrapper"]}`',
            f'- contains_method: `{meta_info["evidence_context_contains_method"]}`', f'- contains_results: `{meta_info["evidence_context_contains_results"]}`', f'- contains_conclusion: `{meta_info["evidence_context_contains_conclusion"]}`', f'- contains_table_or_figure: `{meta_info["evidence_context_contains_table_or_figure"]}`', f'- snippet_sources: `{meta_info["evidence_context_snippet_sources"]}`', '',
            '### old_first_800_preview', '', compact(old, 800), '', '### new_context_preview', '', compact(new, 1200), ''
        ]
    out = Path(args.report_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(json.dumps({'report_path': str(out), 'samples': len(rows)}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
