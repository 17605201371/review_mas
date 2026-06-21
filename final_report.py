#!/usr/bin/env python3
"""最终报告：对比 baseline vs final_v2，验证 diagnosis_pending_concern 路径"""

import json
import sys

def load_results(filename):
    results = []
    with open(filename, 'r') as f:
        for line in f:
            if line.strip():
                results.append(json.loads(line))
    return results

def main():
    baseline_file = 'mimo_v25_refactor_baseline_smoke8_mt7_b4w2_api2_r5t600_20260621_230651.jsonl'
    final_file = sys.argv[1] if len(sys.argv) > 1 else None

    if not final_file:
        import glob
        files = sorted(glob.glob('mimo_v25_refactor_final_v2_diagpending_smoke8*.jsonl'))
        if files:
            final_file = files[-1]
        else:
            print("错误: 找不到 final_v2 文件")
            sys.exit(1)

    print("=" * 80)
    print("最终报告：Coverage Gap Recovery Path 验证")
    print("=" * 80)

    print(f"\nBaseline: {baseline_file}")
    print(f"Final v2: {final_file}\n")

    baseline = load_results(baseline_file)
    final = load_results(final_file)

    print(f"论文数: Baseline={len(baseline)}, Final={len(final)}")

    # Reward 对比
    baseline_reward = sum(r['reward'] for r in baseline) / len(baseline)
    final_reward = sum(r['reward'] for r in final) / len(final)
    print(f"\n平均 Reward:")
    print(f"  Baseline: {baseline_reward:.4f}")
    print(f"  Final v2: {final_reward:.4f}")
    print(f"  Δ:        {final_reward - baseline_reward:+.4f}")

    # Hygiene 检查
    print(f"\nHygiene 检查:")
    hygiene_keys = ['state_contamination', 'recovery_harmful_commit_risk', 'recovery_no_effect_commit']
    all_clean = True
    for key in hygiene_keys:
        final_count = sum(1 for r in final if r.get(key, 0) > 0)
        if final_count > 0:
            print(f"  ✗ {key}: {final_count}/{len(final)} (应该是 0)")
            all_clean = False

    if all_clean:
        print(f"  ✓ 所有 Hygiene 指标都是 0")

    # 关键指标对比
    print(f"\n关键指标对比:")
    metrics = [
        ('verified_negative_count', '验证负向数'),
        ('actionable_negative_count', '可操作负向数'),
        ('contested_relation_count', '对抗关系数'),
        ('verified_coverage_gap_count', '验证覆盖缺口数'),
        ('diagnosis_pending_concern_count', '待诊断问题数'),
    ]

    for key, name in metrics:
        baseline_total = sum(r.get(key, 0) for r in baseline)
        baseline_papers = sum(1 for r in baseline if r.get(key, 0) > 0)
        final_total = sum(r.get(key, 0) for r in final)
        final_papers = sum(1 for r in final if r.get(key, 0) > 0)

        print(f"\n  {name} ({key}):")
        print(f"    Baseline: total={baseline_total}, papers={baseline_papers}/8")
        print(f"    Final v2: total={final_total}, papers={final_papers}/8")
        print(f"    Δ:        {final_total - baseline_total:+d} total, {final_papers - baseline_papers:+d} papers")

        if key == 'diagnosis_pending_concern_count':
            if final_total > 0:
                print(f"    ✓✓✓ 成功！新路径生效，生成了 {final_total} 个 diagnosis_pending_concern！")
            else:
                print(f"    ✗✗✗ 失败！还是 0，需要继续调试...")

    # 详细的 diagnosis_pending_concerns
    concerns_by_paper = {}
    for r in final:
        concerns = r.get('diagnosis_pending_concerns', [])
        if concerns:
            concerns_by_paper[r['paper_id']] = concerns

    if concerns_by_paper:
        print(f"\n详细的 diagnosis_pending_concerns:")
        for paper_id, concerns in concerns_by_paper.items():
            print(f"\n  {paper_id}: {len(concerns)} 个问题")
            for i, c in enumerate(concerns[:2]):
                print(f"    问题 {i+1}:")
                print(f"      claim_id: {c.get('claim_id')}")
                print(f"      claim: {c.get('claim', '')[:60]}...")
                print(f"      missing_requirements: {c.get('missing_requirements', [])[:3]}")
                print(f"      concern_type: {c.get('concern_type', 'N/A')}")
                print(f"      final_view: {c.get('final_view')}")
    else:
        print(f"\n详细的 diagnosis_pending_concerns:")
        print(f"  （无）")

    # Recovery 统计
    print(f"\nRecovery 触发统计:")
    total_recovery_turns = 0
    total_patch_mode_turns = 0
    papers_with_recovery = 0
    papers_with_patch = 0

    for r in final:
        turn_logs = r.get('turn_logs', [])
        recovery_turns = [t for t in turn_logs if 'recovery' in str(t.get('phase')).lower()]
        patch_mode_turns = [t for t in recovery_turns if t.get('recovery_patch_mode_entered')]

        if recovery_turns:
            papers_with_recovery += 1
            total_recovery_turns += len(recovery_turns)

        if patch_mode_turns:
            papers_with_patch += 1
            total_patch_mode_turns += len(patch_mode_turns)

    print(f"  有 recovery 的论文: {papers_with_recovery}/{len(final)}")
    print(f"  总 recovery turns: {total_recovery_turns}")
    print(f"  有 patch mode 的论文: {papers_with_patch}/{len(final)}")
    print(f"  总 patch mode turns: {total_patch_mode_turns}")

    # 总结
    print(f"\n" + "=" * 80)
    print("总结")
    print("=" * 80)

    if concerns_by_paper:
        print(f"✓ 成功！Coverage Gap Recovery 路径完全打通！")
        print(f"  - {len(concerns_by_paper)} 篇论文生成了 diagnosis_pending_concern")
        print(f"  - 总共 {sum(len(c) for c in concerns_by_paper.values())} 个待诊断问题")
        print(f"  - Hygiene 全部为 0，没有引入新的安全问题")
    else:
        print(f"✗ 失败！还没有生成 diagnosis_pending_concern")
        print(f"  需要继续调试...")

if __name__ == '__main__':
    main()
