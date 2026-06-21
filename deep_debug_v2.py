#!/usr/bin/env python3
"""深度调试：如果 v2 还是失败，找出具体哪一步出了问题"""

import json
import sys
import copy

sys.path.insert(0, '/Users/zss/Downloads/zssmas-codex-p26-optimization-20260524')

def deep_debug(result):
    """深度调试单篇论文"""
    paper_id = result.get('paper_id')
    print(f"\n{'='*80}")
    print(f"深度调试: {paper_id}")
    print('='*80)

    review_state = result.get('review_state', {})
    turn_logs = result.get('turn_logs', [])

    # 1. 启发式检测
    print(f"\n【步骤 1】启发式检测")
    from agent_system.review_manager_policy import _has_empirical_claim_without_baseline_evidence

    detected = _has_empirical_claim_without_baseline_evidence(review_state)
    print(f"  _has_empirical_claim_without_baseline_evidence: {detected}")

    if not detected:
        print(f"  ✗ 启发式没检测到，后续步骤不会触发")
        return

    # 2. Recovery 触发
    print(f"\n【步骤 2】Recovery 触发")
    recovery_turns = [(i+1, t) for i, t in enumerate(turn_logs) if 'recovery' in str(t.get('phase')).lower()]
    print(f"  Recovery turns: {len(recovery_turns)}")

    if not recovery_turns:
        print(f"  ✗ 没有 recovery turn")
        return

    for turn_num, turn in recovery_turns:
        action = turn.get('action_type')
        print(f"  Turn {turn_num}: action={action}")

    # 3. Patch mode
    print(f"\n【步骤 3】Patch Mode")
    patch_mode_turns = [(i+1, t) for i, t in enumerate(turn_logs) if t.get('recovery_patch_mode_entered')]
    print(f"  Patch mode turns: {len(patch_mode_turns)}")

    if not patch_mode_turns:
        print(f"  ✗ 没有进入 patch mode")
        return

    for turn_num, turn in patch_mode_turns:
        patch_op = turn.get('recovery_patch_operation')
        patch_source = turn.get('recovery_patch_source')
        print(f"  Turn {turn_num}:")
        print(f"    patch_operation: {patch_op}")
        print(f"    patch_source: {patch_source}")

        # 4. Patch 详情
        if patch_op == 'record_diagnosis_pending_concern':
            print(f"    ✓ patch_operation 正确！")

            # 检查是否 committed
            committed = turn.get('recovery_patch_committed')
            validated = turn.get('recovery_patch_validated')
            print(f"    patch_committed: {committed}")
            print(f"    patch_validated: {validated}")

            if not committed:
                blocked_by = turn.get('recovery_blocked_by')
                failure_code = turn.get('recovery_failure_code')
                print(f"    ✗ Patch 未 commit")
                print(f"    blocked_by: {blocked_by}")
                print(f"    failure_code: {failure_code}")

        elif patch_op == 'reject_patch':
            print(f"    ✗ Patch 被 reject")
            blocked_by = turn.get('recovery_blocked_by')
            failure_code = turn.get('recovery_failure_code')
            failure_msg = turn.get('recovery_failure_message')
            print(f"    blocked_by: {blocked_by}")
            print(f"    failure_code: {failure_code}")
            print(f"    failure_message: {failure_msg}")

        elif not patch_op:
            print(f"    ✗ patch_operation 为空")

    # 5. 最终结果
    print(f"\n【步骤 5】最终结果")
    concerns = result.get('diagnosis_pending_concerns', [])
    concern_count = result.get('diagnosis_pending_concern_count', 0)
    print(f"  diagnosis_pending_concern_count: {concern_count}")
    print(f"  diagnosis_pending_concerns 长度: {len(concerns)}")

    if concerns:
        print(f"  ✓✓✓ 成功！")
        for i, c in enumerate(concerns[:1]):
            print(f"  Concern {i+1}:")
            print(f"    claim_id: {c.get('claim_id')}")
            print(f"    missing_requirements: {c.get('missing_requirements')}")
    else:
        print(f"  ✗ 最终没有生成 concerns")

    # 6. Hygiene view 测试
    print(f"\n【步骤 6】Hygiene View 测试")
    try:
        from agent_system.environments.env_package.review.state import build_decision_hygiene_view

        view_state = copy.deepcopy(review_state)
        view_state.pop("decision_hygiene", None)
        view = build_decision_hygiene_view(view_state)

        requirement_audit = view.get("claim_requirement_audit") or {}
        verified_gaps = requirement_audit.get("verified_coverage_gap_items", [])
        print(f"  verified_coverage_gap_items: {len(verified_gaps)}")

        if verified_gaps:
            gap = verified_gaps[0]
            print(f"  第一个 gap:")
            print(f"    claim_id: {gap.get('claim_id')}")
            print(f"    gap_id: {gap.get('gap_id')}")
            print(f"    missing_requirements: {gap.get('missing_requirements')}")
            print(f"  ✓ Hygiene view 能生成 gaps")
    except Exception as e:
        print(f"  ✗ 错误: {e}")


if __name__ == '__main__':
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    else:
        import glob
        files = sorted(glob.glob('mimo_v25_refactor_final_v2_diagpending_smoke8*.jsonl'))
        if files:
            filename = files[-1]
        else:
            print("错误: 找不到结果文件")
            sys.exit(1)

    print(f"分析文件: {filename}\n")

    with open(filename, 'r') as f:
        results = [json.loads(line) for line in f if line.strip()]

    print(f"总论文数: {len(results)}")

    # 深度调试前 3 篇
    for r in results[:3]:
        deep_debug(r)
