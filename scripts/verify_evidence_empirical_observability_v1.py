#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from agent_system.environments.env_package.review.state import build_turn_log, render_evidence_observation
from agent_system.inference.review_runner import _record_evidence_empirical_observability

OUT_JSON = Path('outputs/results_main/review_infer/evidence_empirical_observability_v1_sanity.json')
DOC_DIR = Path('docs/experiments/mainline_current')


def write_md(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + '\n', encoding='utf-8')


def main() -> None:
    review_state = {
        'phase': 'normal_review',
        'claims': [
            {
                'claim_id': 'claim-1',
                'claim': 'The proposed method improves classification accuracy on benchmark datasets.',
                'status': 'uncertain',
                'supporting_evidence_ids': [],
            }
        ],
        'evidence_map': [],
        'flaw_candidates': [],
        'unresolved_questions': [],
        'evidence_gaps': [],
        'conflict_summary': [],
        'revision_summary': [],
        'risk_profile': {},
        'turn_id': 0,
    }
    task = {
        'paper_id': 'sanity-empirical-observability',
        'user_goal': 'Assess evidence grounding for review support.',
        'mode': 's4',
        'max_turns': 8,
        'paper_text': '''[Instruction]\nFormat requirements\n--- BEGIN PAPER ---\nTitle: A Benchmark Method\nAbstract: We propose a method for classification.\nMethod: The model uses a two-stage architecture with a contrastive objective.\nExperiments: We evaluate on three benchmark datasets. Table 1 reports accuracy and F1 improvements over strong baselines.\nConclusion: The method improves empirical performance while preserving reproducibility.\n--- END PAPER ---''',
        'review_state': review_state,
        'turn_logs': [],
    }
    manager_payload = {
        'action_type': 'verify_evidence',
        'effective_action_type': 'verify_evidence',
        'decision': 'continue',
        'selected_agents': ['Evidence Agent'],
        'target_claim_ids': ['claim-1'],
    }
    observation = render_evidence_observation(task, manager_payload)
    raw = '''<json>{"evidence_map":[{"evidence_id":"evidence-1","claim_id":"claim-1","stance":"supports","strength":"strong","source":"Table 1 experiments","evidence":"Table 1 reports accuracy and F1 gains over baseline datasets."}]}</json>'''
    payload = {
        'evidence_map': [
            {
                'evidence_id': 'evidence-1-turn-1',
                'claim_id': 'claim-1',
                'stance': 'supports',
                'strength': 'strong',
                'source': 'Table 1 experiments',
                'evidence': 'Table 1 reports accuracy and F1 gains over baseline datasets.',
            }
        ],
        'claims': [],
        'flaw_candidates': [],
        'unresolved_questions': [],
        'conflict_notes': [],
        'evidence_gaps': [],
    }
    trace_worker = {'agent_id': 'Evidence Agent', 'raw': raw}
    _record_evidence_empirical_observability('Evidence Agent', trace_worker, manager_payload, raw, worker_payload=payload)
    turn_log = build_turn_log(
        1,
        manager_payload,
        [{'agent_id': 'Evidence Agent', 'payload': payload}],
        review_state,
    )
    required = [
        'evidence_context_contains_empirical_terms',
        'evidence_context_empirical_term_count',
        'evidence_raw_contains_empirical_terms',
        'evidence_raw_empirical_term_count',
        'evidence_payload_empirical_evidence_count',
        'evidence_payload_strong_empirical_count',
        'evidence_empirical_structuring_status',
    ]
    missing = [key for key in required if key not in turn_log]
    failed = []
    if missing:
        failed.append('missing fields: ' + ', '.join(missing))
    if not turn_log.get('evidence_context_contains_empirical_terms'):
        failed.append('context empirical flag not set')
    if not turn_log.get('evidence_raw_contains_empirical_terms'):
        failed.append('raw empirical flag not set')
    if turn_log.get('evidence_payload_strong_empirical_count') != 1:
        failed.append('strong empirical payload count mismatch')
    if turn_log.get('evidence_empirical_structuring_status') != 'strong_empirical_payload_formed':
        failed.append('unexpected structuring status')
    result = {
        'status': 'fail' if failed else 'pass',
        'failed_checks': failed,
        'observation_chars': len(observation),
        'turn_log_subset': {key: turn_log.get(key) for key in required},
        'context_sources': turn_log.get('evidence_context_snippet_sources', []),
        'trace_worker_subset': {key: trace_worker.get(key) for key in required if key in trace_worker},
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    protocol = '''# Evidence Empirical Context & Raw Output Observability v1

## 目标

本轮只补观测字段，不改 Evidence Agent 输入、不改 prompt、不改 fallback、不改 binding、不改 final decision。目标是把 empirical/result/table support 的断点拆成四层：

1. Evidence context 是否包含 empirical/table/method 线索。
2. Evidence Agent raw output 是否提到 empirical/table 线索。
3. 解析后的 payload 是否形成 empirical evidence item。
4. payload 是否形成 supports + strong 的 empirical evidence。

## 新增字段

- `evidence_context_contains_empirical_terms`
- `evidence_context_empirical_term_count`
- `evidence_context_table_or_figure_term_count`
- `evidence_context_method_term_count`
- `evidence_empirical_observability_mode`
- `evidence_raw_contains_empirical_terms`
- `evidence_raw_contains_table_or_figure_terms`
- `evidence_raw_empirical_term_count`
- `evidence_raw_negative_empirical_term_count`
- `evidence_payload_evidence_count`
- `evidence_payload_empirical_evidence_count`
- `evidence_payload_table_or_figure_count`
- `evidence_payload_method_evidence_count`
- `evidence_payload_strong_empirical_count`
- `evidence_payload_support_empirical_count`
- `evidence_payload_has_empirical_evidence`
- `evidence_empirical_structuring_status`

## 边界

这些字段只用于 turn log / runner trace 诊断。它们不改变 worker payload，不改变 ReviewState merge，不改变 recommendation policy。
'''
    sanity = f'''# Evidence Empirical Observability v1 Sanity

## 结果

- status: `{result['status']}`
- failed_checks: `{failed}`
- observation_chars: `{result['observation_chars']}`
- context_sources: `{result['context_sources']}`

## Turn log subset

```json
{json.dumps(result['turn_log_subset'], ensure_ascii=False, indent=2)}
```

## 结论

该 sanity 只验证字段能落入 turn log，不代表模型效果提升。下一轮如果跑 4B/9B 样本，应先看 `evidence_empirical_structuring_status` 的分布，再决定是否做 empirical-targeted context/pass。
'''
    decision = '''# Evidence Empirical Observability v1 Decision

## 保留判断

保留。该补丁是纯观测层，不改变 runtime 行为，能直接回答 empirical support 断点发生在 context、raw output、payload structuring 还是 strong/support 标注阶段。

## 下一步

在下一次 4B/9B 小样本或 fulltest dry-run 后，统计：

- `no_raw_empirical_signal`
- `raw_empirical_no_payload_evidence`
- `raw_empirical_payload_no_empirical_evidence`
- `empirical_payload_without_strong_support`
- `strong_empirical_payload_formed`

如果主要是 `no_raw_empirical_signal`，下一刀才考虑 Evidence Context Selection v2；如果主要是 payload/strong structuring loss，下一刀应改 Evidence JSON/labeling robustness，而不是加长 context。
'''
    write_md(DOC_DIR / 'EVIDENCE_EMPIRICAL_OBSERVABILITY_V1_PROTOCOL.md', protocol)
    write_md(DOC_DIR / 'EVIDENCE_EMPIRICAL_OBSERVABILITY_V1_SANITY.md', sanity)
    write_md(DOC_DIR / 'EVIDENCE_EMPIRICAL_OBSERVABILITY_V1_DECISION.md', decision)
    print(json.dumps({'status': result['status'], 'output_json': str(OUT_JSON)}, ensure_ascii=False, indent=2))
    if failed:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
