#!/usr/bin/env python3
"""分析 diagpending 版本的结果，验证 diagnosis_pending_concern 是否生成"""

import json
import sys

def analyze_result(filename):
    print("=" * 70)
    print(f"分析文件: {filename}")
    print("=" * 70)

    # 读取结果
    results = []
    with open(filename, 'r') as f:
        for line in f:
            if line.strip():
                results.append(json.loads(line))

    print(f"\n论文数: {len(results)}")

    # 平均 reward
    avg_reward = sum(r['reward'] for r in results) / len(results)
    print(f"平均 reward: {avg_reward:.4f}")

    # Hygiene 指标
    print(f"\nHygiene 指标:")
    hygiene_keys = ['state_contamination', 'recovery_harmful_commit_risk', 'recovery_no_effect_commit']
    all_clean = True
    for key in hygiene_keys:
        count = sum(1 for r in results if r.get(key, 0) > 0)
        print(f"  {key}: {count}/{len(results)}")
        if count > 0:
            all_clean = False

    if all_clean:
        print("  ✓ 所有 Hygiene 指标都是 0")
    else:
        print("  ✗ 有 Hygiene 问题！")

    # 关键指标
    print(f"\n关键指标:")
    key_metrics = [
        'verified_negative_count',
        'actionable_negative_count',
        'contested_relation_count',
        'verified_coverage_gap_count',
        'diagnosis_pending_concern_count',
    ]

    for metric in key_metrics:
        total = sum(r.get(metric, 0) for r in results)
        papers_with = sum(1 for r in results if r.get(metric, 0) > 0)
        print(f"  {metric}:")
        print(f"    total={total}, papers={papers_with}/{len(results)}")

        if metric == 'diagnosis_pending_concern_count' and total > 0:
            print(f"    ✓✓✓ 成功！生成了 {total} 个 diagnosis_pending_concern！")

    # 检查 diagnosis_pending_concerns 详情
    concerns_found = False
    print(f"\ndiagnosis_pending_concerns 详情:")
    for r in results:
        concerns = r.get('diagnosis_pending_concerns', [])
        if concerns:
            concerns_found = True
            print(f"\n  {r['paper_id']}: {len(concerns)} 个问题")
            for i, c in enumerate(concerns[:2]):
                print(f"    问题 {i+1}:")
                print(f"      claim_id: {c.get('claim_id')}")
                print(f"      missing_requirements: {c.get('missing_requirements', [])[:3]}")
                print(f"      concern_type: {c.get('concern_type')}")

    if not concerns_found:
        print("  （无）")
        print("\n  ⚠️  没有生成 diagnosis_pending_concerns！")
        print("  需要进一步调试...")

    # 检查 recovery 触发情况
    print(f"\nRecovery 触发统计:")
    for r in results:
        paper_id = r.get('paper_id')
        turn_logs = r.get('turn_logs', [])
        recovery_turns = [t for t in turn_logs if 'recovery' in str(t.get('phase')).lower()]

        if recovery_turns:
            print(f"  {paper_id}: {len(recovery_turns)} 个 recovery turns")

            # 检查是否有 patch
            patch_turns = [t for t in recovery_turns if t.get('recovery_patch_mode_entered')]
            if patch_turns:
                print(f"    - {len(patch_turns)} 个 turn 进入了 patch mode")

                # 检查 patch operation
                for t in patch_turns:
                    op = t.get('recovery_patch_operation')
                    if op:
                        print(f"      ✓ recovery_patch_operation: {op}")
                    else:
                        print(f"      ✗ recovery_patch_operation 为空")

if __name__ == '__main__':
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    else:
        # 查找最新的 envfix 文件
        import glob
        files = sorted(glob.glob('mimo_v25_refactor_envfix_diagpending_smoke8*.jsonl'))
        if files:
            filename = files[-1]
        else:
            print("错误: 找不到结果文件")
            sys.exit(1)

    analyze_result(filename)
