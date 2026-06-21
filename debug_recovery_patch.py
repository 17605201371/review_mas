#!/usr/bin/env python3
"""调试为什么 recovery patch 没有生成 diagnosis_pending_concern"""

import json
import sys
import copy

# 添加路径
sys.path.insert(0, '/Users/zss/Downloads/zssmas-codex-p26-optimization-20260524')

def debug_paper(result):
    """调试单篇论文为什么没有生成 concern"""
    paper_id = result.get('paper_id')
    print(f"\n{'=' * 70}")
    print(f"调试论文: {paper_id}")
    print('=' * 70)

    review_state = result.get('review_state', {})

    # 1. 检查启发式函数
    print(f"\n1. 检查启发式函数:")
    claims = [c for c in review_state.get("claims", []) or [] if isinstance(c, dict)]
    evidence_map = [e for e in review_state.get("evidence_map", []) or [] if isinstance(e, dict)]

    empirical_claims = [
        c for c in claims
        if str(c.get("claim_type") or "").strip() == "empirical"
        and str(c.get("importance") or "").strip() in {"high", ""}
        and str(c.get("claim_kind") or "").strip() == "paper_extracted"
        and str(c.get("status") or "").strip() == "supported"
    ]

    print(f"   Empirical claims: {len(empirical_claims)}")

    if empirical_claims:
        claim = empirical_claims[0]
        claim_id = str(claim.get("claim_id") or "")
        has_baseline = any(
            str(e.get("claim_id") or "") == claim_id
            and str(e.get("support_source_bucket") or "").strip() in {
                "baseline_or_comparison",
                "ablation_study",
                "empirical_result",
            }
            and str(e.get("verified_grounding_label") or "").startswith("paper_grounded")
            and str(e.get("semantic_grounding_label") or "") == "semantic_support_verified"
            for e in evidence_map
        )
        print(f"   第一个 empirical claim: {claim_id}")
        print(f"   有 baseline evidence: {has_baseline}")

        if not has_baseline:
            print(f"   ✓ 启发式函数应该返回 True")
        else:
            print(f"   ✗ 启发式函数会返回 False")

    # 2. 检查 recovery 是否触发
    print(f"\n2. 检查 recovery 触发:")
    turn_logs = result.get('turn_logs', [])
    recovery_turns = [t for t in turn_logs if 'recovery' in str(t.get('phase')).lower()]
    print(f"   Recovery turns: {len(recovery_turns)}")

    if recovery_turns:
        for i, turn in enumerate(recovery_turns):
            turn_idx = turn_logs.index(turn) + 1
            patch_mode = turn.get('recovery_patch_mode_entered')
            patch_op = turn.get('recovery_patch_operation')
            print(f"   Turn {turn_idx}: patch_mode={patch_mode}, patch_op={patch_op or '(empty)'}")

    # 3. 测试 build_decision_hygiene_view
    print(f"\n3. 测试 build_decision_hygiene_view:")
    try:
        from agent_system.environments.env_package.review.state import build_decision_hygiene_view

        view_state = copy.deepcopy(review_state)
        view_state.pop("decision_hygiene", None)
        view = build_decision_hygiene_view(view_state)

        requirement_audit = view.get("claim_requirement_audit") or {}
        if isinstance(requirement_audit, dict):
            verified_gaps = requirement_audit.get("verified_coverage_gap_items", [])
            print(f"   verified_coverage_gap_items: {len(verified_gaps)}")

            if verified_gaps:
                gap = verified_gaps[0]
                print(f"   第一个 gap:")
                print(f"     claim_id: {gap.get('claim_id')}")
                print(f"     missing_requirements: {gap.get('missing_requirements')}")
                print(f"   ✓ hygiene view 能生成 verified gaps")
            else:
                print(f"   ✗ 没有 verified_coverage_gap_items")
        else:
            print(f"   ✗ claim_requirement_audit 不是 dict")

    except Exception as e:
        print(f"   ✗ 错误: {e}")

    # 4. 检查最终的 diagnosis_pending_concerns
    print(f"\n4. 检查最终结果:")
    concerns = result.get('diagnosis_pending_concerns', [])
    concern_count = result.get('diagnosis_pending_concern_count', 0)
    print(f"   diagnosis_pending_concern_count: {concern_count}")
    print(f"   diagnosis_pending_concerns 数量: {len(concerns)}")

    if concerns:
        print(f"   ✓ 成功生成 concerns")
        for i, c in enumerate(concerns[:1]):
            print(f"   Concern {i+1}:")
            print(f"     claim_id: {c.get('claim_id')}")
            print(f"     missing: {c.get('missing_requirements')}")
    else:
        print(f"   ✗ 没有生成 concerns")


if __name__ == '__main__':
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    else:
        import glob
        files = sorted(glob.glob('mimo_v25_refactor_envfix_diagpending_smoke8*.jsonl'))
        if files:
            filename = files[-1]
        else:
            print("错误: 找不到结果文件")
            sys.exit(1)

    print(f"分析文件: {filename}\n")

    with open(filename, 'r') as f:
        results = [json.loads(line) for line in f if line.strip()]

    print(f"总论文数: {len(results)}")

    # 调试前 3 篇
    for r in results[:3]:
        debug_paper(r)
