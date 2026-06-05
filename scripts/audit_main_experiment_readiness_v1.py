#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding='utf-8'))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')


def write_md(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + '\n', encoding='utf-8')


def md_table(headers: Sequence[str], rows: Sequence[Sequence[Any]]) -> str:
    lines = ['| ' + ' | '.join(headers) + ' |', '| ' + ' | '.join(['---'] * len(headers)) + ' |']
    for row in rows:
        lines.append('| ' + ' | '.join(str(x).replace('\n', ' ') for x in row) + ' |')
    return '\n'.join(lines)


def exists_row(root: Path, rel: str, purpose: str, required: bool = True) -> Dict[str, Any]:
    path = root / rel
    return {
        'path': rel,
        'purpose': purpose,
        'required': required,
        'exists': path.exists(),
        'size': path.stat().st_size if path.exists() else 0,
    }


def metric(payload: Dict[str, Any], *keys: str, default: Any = None) -> Any:
    cur: Any = payload
    for key in keys:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(key)
    return default if cur is None else cur


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, default=Path('.'))
    parser.add_argument('--doc-dir', type=Path, default=Path('docs/experiments/mainline_current'))
    parser.add_argument('--output-json', type=Path, default=Path('outputs/results_main/review_infer/main_experiment_readiness_audit_v1.json'))
    args = parser.parse_args()
    root = args.root

    required = [
        exists_row(root, 'SERVER_CANONICAL_NOTE.md', '服务器权威工作区说明'),
        exists_row(root, 'docs/experiments/mainline_current/MAINLINE_FINAL_V1_SPEC.md', '主线边界和保留/不保留模块'),
        exists_row(root, 'docs/experiments/mainline_current/MAINLINE_FINAL_V1_ARTIFACT_INDEX.md', '论文/外部分析文件索引'),
        exists_row(root, 'docs/experiments/mainline_current/PAPER_MAIN_RESULTS_TABLE_V1.md', '论文主结果表草稿'),
        exists_row(root, 'docs/experiments/mainline_current/MAINLINE_FINAL_V1_FAILURE_TAXONOMY.md', 'failure taxonomy'),
        exists_row(root, 'docs/experiments/mainline_current/MAINLINE_FINAL_V1_CASE_STUDY_PACK.md', 'case study pack'),
        exists_row(root, 'docs/experiments/mainline_current/PAPER_NEGATIVE_FINDINGS_SUMMARY_V1.md', '负结果总结'),
        exists_row(root, 'outputs/results_main/review_infer/mainline_final_v1_unified_results.json', '统一主线结果 JSON'),
        exists_row(root, 'outputs/results_main/review_infer/final_view_invalid_binding_filter_v1_id_scoped_fulltest39.json', 'final-view invalid binding/support-quality simulation'),
        exists_row(root, 'outputs/results_main/review_infer/evidence_id_turn_scoping_v1_fulltest39_4b.jsonl', 'ID turn-scoping fulltest39 runtime output'),
        exists_row(root, 'outputs/results_main/review_infer/mainline_final_v1_9b_fulltest39_dryrun.jsonl', '9B fulltest39 dry-run output'),
    ]
    optional = [
        exists_row(root, 'docs/experiments/mainline_current/CRITERION_COVERAGE_GROUNDING_9B_FULLTEST39.md', '9B criterion coverage/grounding audit', required=False),
        exists_row(root, 'docs/experiments/mainline_current/FINAL_RECOMMENDATION_VIEW_V1_DECISION.md', 'final recommendation view decision', required=False),
        exists_row(root, 'docs/experiments/mainline_current/MAINLINE_FINAL_V1_9B_FULLTEST39_DECISION.md', '9B dry-run decision', required=False),
    ]

    unified = read_json(root / 'outputs/results_main/review_infer/mainline_final_v1_unified_results.json')
    invalid = read_json(root / 'outputs/results_main/review_infer/final_view_invalid_binding_filter_v1_id_scoped_fulltest39.json')

    blockers: List[str] = []
    warnings: List[str] = []
    for item in required:
        if not item['exists']:
            blockers.append(f"missing required artifact: {item['path']}")
    if metric(unified, 'runtime_health', 'rows') not in {39, '39'}:
        warnings.append('unified results row count is not 39 or missing')
    if metric(invalid, 'rows') not in {39, '39'}:
        warnings.append('invalid binding filter row count is not 39 or missing')
    if metric(invalid, 'strict', 'false_accept_count', default=999) > 0:
        warnings.append('strict support-quality view still has false accepts; do not use as runtime decision')
    if metric(unified, 'runtime_health', 'runtime_final_decision_counts', 'accept', default=0) == 0:
        warnings.append('runtime final decision still has zero accepts; report as health-check collapse, not primary failure')

    status = 'go_for_dry_run_or_paper_pack' if not blockers else 'no_go_missing_artifacts'
    if blockers:
        recommendation = '先补齐缺失文件，再考虑主试验。'
    else:
        recommendation = '可以进入主试验 dry-run / 论文结果包整理；正式主试验前仍需冻结 final recommendation policy，并明确 accept/reject 只是 health check。'

    audit = {
        'status': status,
        'recommendation': recommendation,
        'required_artifacts': required,
        'optional_artifacts': optional,
        'blockers': blockers,
        'warnings': warnings,
        'key_metrics': {
            'unified_rows': metric(unified, 'runtime_health', 'rows'),
            'runtime_final_decision_counts': metric(unified, 'runtime_health', 'runtime_final_decision_counts', default={}),
            'recommendation_view_counts': metric(unified, 'final_recommendation_view_counts', default={}),
            'invalid_filter_rows': invalid.get('rows'),
            'invalid_filter_strict': invalid.get('strict', {}),
            'failure_taxonomy_counts': {},
        },
    }
    write_json(args.output_json, audit)

    artifact_rows = [
        [item['path'], 'yes' if item['exists'] else 'NO', item['purpose'], item['size']]
        for item in required + optional
    ]
    metric_rows = [
        ['status', status],
        ['recommendation', recommendation],
        ['blockers', '; '.join(blockers) if blockers else 'none'],
        ['warnings', '; '.join(warnings) if warnings else 'none'],
        ['runtime_final_decision_counts', json.dumps(metric(unified, 'runtime_health', 'runtime_final_decision_counts', default={}), ensure_ascii=False)],
        ['final_recommendation_view_counts', json.dumps(metric(unified, 'final_recommendation_view_counts', default={}), ensure_ascii=False)],
        ['strict_false_accept_count', metric(invalid, 'strict', 'false_accept_count')],
        ['strict_recovered_accept_ids', ', '.join(metric(invalid, 'strict', 'recovered_accept_ids', default=[]))],
        ['strict_false_accept_ids', ', '.join(metric(invalid, 'strict', 'false_accept_ids', default=[]))],
    ]
    md = (
        '# Main Experiment Readiness Audit v1\n\n'
        '## 结论\n\n'
        f'- readiness_status: `{status}`\n'
        f'- recommendation: {recommendation}\n\n'
        '## 关键指标\n\n'
        + md_table(['metric', 'value'], metric_rows)
        + '\n\n## Artifact 检查\n\n'
        + md_table(['path', 'exists', 'purpose', 'size_bytes'], artifact_rows)
        + '\n\n## 执行边界\n\n'
        '- 可以继续做主试验 dry-run / 论文结果包整理。\n'
        '- 不建议继续新增 sticky/throttle/progression gate。\n'
        '- 不建议把 support-quality 或 criterion simulation 直接接成 runtime final decision。\n'
        '- 若要跑正式主试验，应先冻结 final recommendation policy，并明确二分类只是 health check。\n'
    )
    write_md(args.doc_dir / 'MAIN_EXPERIMENT_READINESS_AUDIT_V1.md', md)
    print(json.dumps({'status': status, 'blockers': blockers, 'warnings': warnings}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
