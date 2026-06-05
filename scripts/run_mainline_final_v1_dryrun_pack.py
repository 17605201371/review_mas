#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence


ROOT = Path('.')
DEFAULT_DOC_DIR = Path('docs/experiments/mainline_current')
DEFAULT_OUTPUT_JSON = Path('outputs/results_main/review_infer/mainline_final_v1_dry_run_pack_summary.json')
DEFAULT_REPRO_DOC = DEFAULT_DOC_DIR / 'MAINLINE_FINAL_V1_DRY_RUN_REPRODUCIBILITY.md'


class PackError(RuntimeError):
    pass


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
    lines = [
        '| ' + ' | '.join(headers) + ' |',
        '| ' + ' | '.join(['---'] * len(headers)) + ' |',
    ]
    for row in rows:
        lines.append('| ' + ' | '.join(str(value).replace('\n', ' ') for value in row) + ' |')
    return '\n'.join(lines)


def run_capture(args: Sequence[str], *, check: bool = True) -> Dict[str, Any]:
    start = time.time()
    env = os.environ.copy()
    current_path = str(ROOT.resolve())
    old_pythonpath = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = current_path if not old_pythonpath else f"{current_path}:{old_pythonpath}"
    proc = subprocess.run(args, cwd=ROOT, text=True, capture_output=True, env=env)
    duration = round(time.time() - start, 3)
    result = {
        'cmd': list(args),
        'returncode': proc.returncode,
        'duration_sec': duration,
        'stdout_tail': proc.stdout[-4000:],
        'stderr_tail': proc.stderr[-4000:],
    }
    if check and proc.returncode != 0:
        raise PackError(f"command failed: {' '.join(args)}\n{proc.stderr[-2000:]}")
    return result


def git_value(args: Sequence[str]) -> str:
    proc = subprocess.run(['git', *args], cwd=ROOT, text=True, capture_output=True)
    if proc.returncode != 0:
        return ''
    return proc.stdout.strip()


def artifact_row(path: Path, purpose: str) -> List[Any]:
    return [str(path), 'yes' if path.exists() else 'NO', path.stat().st_size if path.exists() else 0, purpose]


def summarize_metrics() -> Dict[str, Any]:
    readiness = read_json(Path('outputs/results_main/review_infer/main_experiment_readiness_audit_v1.json'))
    unified = read_json(Path('outputs/results_main/review_infer/mainline_final_v1_unified_results.json'))
    invalid = read_json(Path('outputs/results_main/review_infer/final_view_invalid_binding_filter_v1_id_scoped_fulltest39.json'))
    calibration = read_json(Path('outputs/results_main/review_infer/final_recommendation_calibration_v1.json'))
    empirical_audit = read_json(Path('outputs/results_main/review_infer/empirical_negative_grounding_audit_v1.json'))
    rec_counts = unified.get('final_recommendation_view_counts', {}) if isinstance(unified, dict) else {}
    runtime = unified.get('runtime_health', {}) if isinstance(unified, dict) else {}
    support = unified.get('support_state', {}) if isinstance(unified, dict) else {}
    return {
        'readiness_status': readiness.get('status'),
        'readiness_recommendation': readiness.get('recommendation'),
        'readiness_blockers': readiness.get('blockers', []),
        'readiness_warnings': readiness.get('warnings', []),
        'runtime_rows': runtime.get('rows'),
        'runtime_final_decision_counts': runtime.get('runtime_final_decision_counts', {}),
        'final_recommendation_view_counts': rec_counts,
        'real_strong_support_total': support.get('real_strong_support_total'),
        'non_abstract_support_total': support.get('non_abstract_support_total'),
        'empirical_support_total': support.get('empirical_support_total'),
        'strict_recovered_accept_ids': ((invalid.get('strict') or {}).get('recovered_accept_ids') or []),
        'strict_false_accept_ids': ((invalid.get('strict') or {}).get('false_accept_ids') or []),
        'calibration_9b_high_precision': (((calibration.get('datasets') or {}).get('9b_fulltest39_dryrun') or {}).get('binary_rules') or {}).get('calibrated_high_precision', {}),
        'calibration_9b_balanced': (((calibration.get('datasets') or {}).get('9b_fulltest39_dryrun') or {}).get('binary_rules') or {}).get('calibrated_balanced', {}),
        'empirical_negative_audit_label_counts': empirical_audit.get('audit_label_counts', {}),
        'empirical_negative_audit_next_cut': (empirical_audit.get('next_cut') or {}).get('recommendation'),
    }


def render_repro_doc(summary: Dict[str, Any]) -> str:
    metrics = summary['metrics']
    artifact_rows = [
        artifact_row(Path('docs/experiments/mainline_current/MAINLINE_FINAL_V1_UNIFIED_RESULTS_TABLE.md'), '统一主线结果表'),
        artifact_row(Path('docs/experiments/mainline_current/PAPER_MAIN_RESULTS_TABLE_V1.md'), '论文主结果表草稿'),
        artifact_row(Path('docs/experiments/mainline_current/FINAL_RECOMMENDATION_POLICY_V1_FINAL.md'), 'final recommendation policy 冻结口径'),
        artifact_row(Path('docs/experiments/mainline_current/FINAL_RECOMMENDATION_CALIBRATION_V1_RESULTS.md'), 'final recommendation calibration 结果'),
        artifact_row(Path('docs/experiments/mainline_current/FINAL_RECOMMENDATION_CALIBRATION_V1_DECISION.md'), 'final recommendation calibration 决策'),
        artifact_row(Path('docs/experiments/mainline_current/FINAL_RECOMMENDATION_CALIBRATION_CASE_REVIEW_V1.md'), 'final recommendation calibration 关键 case review'),
        artifact_row(Path('docs/experiments/mainline_current/EMPIRICAL_EVIDENCE_SUFFICIENCY_AUDIT_V1.md'), 'empirical evidence sufficiency audit'),
        artifact_row(Path('docs/experiments/mainline_current/HARD_NEGATIVE_GROUNDING_AUDIT_V1.md'), 'hard-negative grounding audit'),
        artifact_row(Path('docs/experiments/mainline_current/EMPIRICAL_NEGATIVE_CASE_TABLE_V1.md'), 'empirical/negative grounding case table'),
        artifact_row(Path('docs/experiments/mainline_current/NEXT_CUT_AFTER_CALIBRATION_DECISION.md'), 'calibration 后下一刀方向'),
        artifact_row(Path('docs/experiments/mainline_current/EVIDENCE_EMPIRICAL_OBSERVABILITY_V1_PROTOCOL.md'), 'Evidence empirical observability protocol'),
        artifact_row(Path('docs/experiments/mainline_current/EVIDENCE_EMPIRICAL_OBSERVABILITY_V1_SANITY.md'), 'Evidence empirical observability sanity'),
        artifact_row(Path('docs/experiments/mainline_current/EVIDENCE_EMPIRICAL_OBSERVABILITY_V1_DECISION.md'), 'Evidence empirical observability decision'),
        artifact_row(Path('docs/experiments/mainline_current/SERVER_IMPORT_PATH_GUARD.md'), 'server import path guard'),
        artifact_row(Path('docs/experiments/mainline_current/MAINLINE_FINAL_V1_ARTIFACT_INDEX.md'), '主线 artifact 索引'),
        artifact_row(Path('docs/experiments/mainline_current/FINAL_RECOMMENDATION_CASEBOOK_V1.md'), 'final recommendation casebook'),
        artifact_row(Path('docs/experiments/mainline_current/PAPER_NEGATIVE_FINDINGS_SUMMARY_V1.md'), '负结果总结'),
        artifact_row(Path('docs/experiments/mainline_current/MAINLINE_FINAL_V1_FAILURE_TAXONOMY.md'), 'failure taxonomy'),
        artifact_row(Path('docs/experiments/mainline_current/MAIN_EXPERIMENT_READINESS_AUDIT_V1.md'), '主试验 readiness audit'),
        artifact_row(Path('outputs/results_main/review_infer/mainline_final_v1_unified_results.json'), '统一结果 JSON'),
        artifact_row(Path('outputs/results_main/review_infer/main_experiment_readiness_audit_v1.json'), 'readiness audit JSON'),
        artifact_row(Path('outputs/results_main/review_infer/mainline_final_v1_dry_run_pack_summary.json'), 'dry-run pack summary JSON'),
        artifact_row(Path('outputs/results_main/review_infer/final_recommendation_calibration_v1.json'), 'final recommendation calibration JSON'),
        artifact_row(Path('outputs/results_main/review_infer/final_recommendation_calibration_case_review_v1.json'), 'final recommendation calibration case review JSON'),
        artifact_row(Path('outputs/results_main/review_infer/empirical_negative_grounding_audit_v1.json'), 'empirical/negative grounding audit JSON'),
        artifact_row(Path('outputs/results_main/review_infer/evidence_empirical_observability_v1_sanity.json'), 'Evidence empirical observability sanity JSON'),
    ]
    command_rows = [
        [' '.join(step['cmd']), step['returncode'], step['duration_sec']]
        for step in summary['steps']
    ]
    metric_rows = [
        ['readiness_status', metrics.get('readiness_status')],
        ['blockers', '; '.join(metrics.get('readiness_blockers') or []) or 'none'],
        ['warnings', '; '.join(metrics.get('readiness_warnings') or []) or 'none'],
        ['runtime_rows', metrics.get('runtime_rows')],
        ['runtime_final_decision_counts', json.dumps(metrics.get('runtime_final_decision_counts') or {}, ensure_ascii=False)],
        ['final_recommendation_view_counts', json.dumps(metrics.get('final_recommendation_view_counts') or {}, ensure_ascii=False)],
        ['real_strong_support_total', metrics.get('real_strong_support_total')],
        ['non_abstract_support_total', metrics.get('non_abstract_support_total')],
        ['empirical_support_total', metrics.get('empirical_support_total')],
        ['strict_recovered_accept_ids', ', '.join(metrics.get('strict_recovered_accept_ids') or [])],
        ['strict_false_accept_ids', ', '.join(metrics.get('strict_false_accept_ids') or [])],
        ['calibration_high_precision_recovered', ', '.join((metrics.get('calibration_9b_high_precision') or {}).get('recovered_accept_ids') or [])],
        ['calibration_high_precision_false_accept', ', '.join((metrics.get('calibration_9b_high_precision') or {}).get('false_accept_ids') or []) or 'none'],
        ['calibration_balanced_recovered', ', '.join((metrics.get('calibration_9b_balanced') or {}).get('recovered_accept_ids') or [])],
        ['calibration_balanced_false_accept', ', '.join((metrics.get('calibration_9b_balanced') or {}).get('false_accept_ids') or []) or 'none'],
        ['empirical_negative_audit_label_counts', json.dumps(metrics.get('empirical_negative_audit_label_counts') or {}, ensure_ascii=False)],
        ['empirical_negative_audit_next_cut', metrics.get('empirical_negative_audit_next_cut') or ''],
    ]
    return f"""# Mainline-Final-v1 Dry-Run Reproducibility Pack

## 结论

本文件记录 `Mainline-Final-v1` 论文结果包的一键离线复现流程。本轮不跑模型、不改 runtime，只重跑现有离线汇总、case study、paper pack 和 readiness audit。当前状态可作为主试验 dry-run / 论文结果包入口，但正式主试验前仍需明确 final recommendation policy；runtime accept/reject 只作为 health check。

## Git 状态

- branch: `{summary['git']['branch']}`
- head: `{summary['git']['head']}`
- dirty_before: `{summary['git']['dirty_before'] or 'clean'}`
- generated_at_utc: `{summary['generated_at_utc']}`

## 复现命令

{md_table(['command', 'returncode', 'duration_sec'], command_rows)}

## 关键指标快照

{md_table(['metric', 'value'], metric_rows)}

## 产物检查

{md_table(['path', 'exists', 'size_bytes', 'purpose'], artifact_rows)}

## 使用边界

- 这是离线结果包，不是新的模型推理实验。
- 不把 support-quality / criterion simulation 直接接成 runtime final decision。
- 不继续 sticky / throttle / progression gate。
- 论文中应将 binary accept/reject 作为 health check，将 final recommendation view、support quality、criterion grounding 和 failure taxonomy 作为主解释层。
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--doc-dir', type=Path, default=DEFAULT_DOC_DIR)
    parser.add_argument('--output-json', type=Path, default=DEFAULT_OUTPUT_JSON)
    parser.add_argument('--repro-doc', type=Path, default=DEFAULT_REPRO_DOC)
    args = parser.parse_args()

    required_inputs = [
        Path('scripts/compile_mainline_final_v1_unified_results.py'),
        Path('scripts/compile_paper_result_pack_v1.py'),
        Path('scripts/compile_mainline_case_study_pack_v1.py'),
        Path('scripts/audit_main_experiment_readiness_v1.py'),
        Path('scripts/simulate_final_recommendation_calibration_v1.py'),
        Path('scripts/compile_final_recommendation_calibration_case_review_v1.py'),
        Path('scripts/audit_empirical_negative_grounding_v1.py'),
        Path('scripts/verify_evidence_empirical_observability_v1.py'),
        Path('outputs/results_main/review_infer/final_view_invalid_binding_filter_v1_id_scoped_fulltest39.json'),
    ]
    missing = [str(path) for path in required_inputs if not path.exists()]
    if missing:
        raise PackError('missing required inputs: ' + ', '.join(missing))

    git = {
        'branch': git_value(['branch', '--show-current']),
        'head': git_value(['rev-parse', '--short', 'HEAD']),
        'dirty_before': git_value(['status', '--short']),
    }
    steps: List[Dict[str, Any]] = []
    commands = [
        [sys.executable, 'scripts/compile_mainline_final_v1_unified_results.py'],
        [sys.executable, 'scripts/compile_paper_result_pack_v1.py'],
        [sys.executable, 'scripts/simulate_final_recommendation_calibration_v1.py'],
        [sys.executable, 'scripts/compile_final_recommendation_calibration_case_review_v1.py'],
        [sys.executable, 'scripts/audit_empirical_negative_grounding_v1.py'],
        [sys.executable, 'scripts/verify_evidence_empirical_observability_v1.py'],
        [sys.executable, 'scripts/compile_mainline_case_study_pack_v1.py', '--input-json', 'outputs/results_main/review_infer/final_view_invalid_binding_filter_v1_id_scoped_fulltest39.json', '--doc-dir', str(args.doc_dir)],
        [sys.executable, 'scripts/audit_main_experiment_readiness_v1.py', '--doc-dir', str(args.doc_dir)],
    ]
    for command in commands:
        steps.append(run_capture(command))

    summary = {
        'generated_at_utc': datetime.now(timezone.utc).isoformat(),
        'git': git,
        'steps': steps,
        'metrics': summarize_metrics(),
        'outputs': {
            'summary_json': str(args.output_json),
            'repro_doc': str(args.repro_doc),
        },
    }
    write_json(args.output_json, summary)
    write_md(args.repro_doc, render_repro_doc(summary))
    print(json.dumps({'summary_json': str(args.output_json), 'repro_doc': str(args.repro_doc), 'status': summary['metrics'].get('readiness_status')}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
