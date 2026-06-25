"""测试 verified_coverage_gap 能触发 recovery

验证 2026-06-21 重构 + 2026-06-22 修复：
1. _has_blocking_recovery_signal 识别 verified_coverage_gap (需要 turn ≥ 3)
2. _choose_blocking_recovery_action 返回 challenge_previous_hypothesis
3. _claim_requirement_gap_recovery_patch_payload 使用 verified_coverage_gap_items

注意：coverage gap 检查只在 _has_blocking_recovery_signal (需要 turn ≥ 3)，
不在 _state_is_recovery_relevant，以避免过早触发 recovery（evidence 还未收集完）。
"""
import os
import sys
from typing import Any, Dict

# 导入需要测试的函数
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agent_system.review_manager_policy import (
    _state_is_recovery_relevant,
    _has_blocking_recovery_signal,
    _choose_blocking_recovery_action,
)
from agent_system.inference.review_runner import (
    _claim_requirement_gap_recovery_patch_payload,
)


def test_has_blocking_recovery_signal_with_coverage_gap():
    """测试 _has_blocking_recovery_signal 识别 coverage gap (需要 turn ≥ 3)"""
    state = {
        "claims": [
            {
                "claim_id": "claim-primary-1",
                "claim_type": "empirical",
                "importance": "high",
                "claim_kind": "paper_extracted",
                "status": "supported",
            }
        ],
        "evidence_map": [
            {
                "evidence_id": "ev-1",
                "claim_id": "claim-primary-1",
                "support_source_bucket": "method_or_approach",
                "verified_grounding_label": "paper_grounded_exact",
                "semantic_grounding_label": "semantic_support_verified",
            }
        ],
        "flaw_candidates": [],
    }
    # 需要至少 3 个 turn logs
    recent_turn_logs = [
        {"action_type": "extract_claims"},
        {"action_type": "verify_evidence"},
        {"action_type": "analyze_flaws"},
    ]

    result = _has_blocking_recovery_signal(state, recent_turn_logs)
    assert result is True, "应该识别 empirical claim 缺 baseline 为 blocking signal (turn ≥ 3)"
    print("✓ _has_blocking_recovery_signal 识别 coverage gap")


def test_has_blocking_recovery_signal_not_triggered_before_turn_3():
    """测试 turn < 3 时不触发 coverage gap recovery"""
    state = {
        "claims": [
            {
                "claim_id": "claim-primary-1",
                "claim_type": "empirical",
                "importance": "high",
                "claim_kind": "paper_extracted",
                "status": "supported",
            }
        ],
        "evidence_map": [
            {
                "evidence_id": "ev-1",
                "claim_id": "claim-primary-1",
                "support_source_bucket": "method_or_approach",
                "verified_grounding_label": "paper_grounded_exact",
                "semantic_grounding_label": "semantic_support_verified",
            }
        ],
        "flaw_candidates": [],
    }
    # 只有 2 个 turn logs
    recent_turn_logs = [
        {"action_type": "extract_claims"},
        {"action_type": "verify_evidence"},
    ]

    result = _has_blocking_recovery_signal(state, recent_turn_logs)
    assert result is False, "turn < 3 时不应该触发 coverage gap recovery"
    print("✓ turn < 3 时不触发 coverage gap recovery")


def test_choose_blocking_recovery_action_with_coverage_gap():
    """测试 _choose_blocking_recovery_action 返回正确的 action"""
    state = {
        "claims": [
            {
                "claim_id": "claim-primary-1",
                "claim_type": "empirical",
                "importance": "high",
                "claim_kind": "paper_extracted",
                "status": "supported",
            }
        ],
        "evidence_map": [
            {
                "evidence_id": "ev-1",
                "claim_id": "claim-primary-1",
                "support_source_bucket": "method_or_approach",
                "verified_grounding_label": "paper_grounded_exact",
                "semantic_grounding_label": "semantic_support_verified",
            }
        ],
        "risk_profile": {},
        "flaw_candidates": [],
    }

    result = _choose_blocking_recovery_action(state)
    assert result == "challenge_previous_hypothesis", \
        f"应该返回 challenge_previous_hypothesis，实际返回 {result}"
    print("✓ _choose_blocking_recovery_action 返回 challenge_previous_hypothesis")


def test_claim_requirement_gap_recovery_patch_uses_verified_items(monkeypatch):
    """测试 _claim_requirement_gap_recovery_patch_payload 使用 verified_coverage_gap_items"""
    monkeypatch.setenv("DRMAS_DIAGPENDING_RECOVERY", "1")
    # 使用完整的 state，让 build_decision_hygiene_view 能生成 verified_coverage_gap
    state = {
        "claims": [
            {
                "claim_id": "claim-primary-1",
                "claim": "Our method achieves SOTA results",
                "claim_type": "empirical",
                "importance": "high",
                "claim_kind": "paper_extracted",
                "status": "supported",
            }
        ],
        "evidence_map": [
            {
                "evidence_id": "e-method-1",
                "claim_id": "claim-primary-1",
                "evidence": "The method uses a reranking module.",
                "source_locator": "Section 3",
                "raw_quote": "The method uses a reranking module.",
                "stance": "supports",
                "strength": "medium",
                "binding_status": "bound_real_claim",
                "verified_grounding_label": "paper_grounded_exact",
                "semantic_grounding_label": "semantic_support_verified",
                "support_source_bucket": "method_or_approach",
            }
        ],
        "flaw_candidates": [],
        "unresolved_questions": [],
        "evidence_gaps": [],
        "conflict_notes": [],
    }
    manager_payload = {
        "target_claim_ids": ["claim-primary-1"],
    }

    result = _claim_requirement_gap_recovery_patch_payload(state, manager_payload)

    assert result is not None, "应该生成 recovery patch"
    assert result.get("action") == "apply_recovery_patch", \
        f"action 应该是 apply_recovery_patch，实际是 {result.get('action')}"
    assert result.get("target_type") == "claim_requirement_gap", \
        f"target_type 应该是 claim_requirement_gap，实际是 {result.get('target_type')}"
    assert result.get("recovery_patch_operation") == "record_diagnosis_pending_concern", \
        f"operation 应该是 record_diagnosis_pending_concern，实际是 {result.get('recovery_patch_operation')}"

    # 验证生成的 concern 内容
    concern = result.get("diagnosis_pending_concern", {})
    assert concern.get("claim_id") == "claim-primary-1", \
        f"应该使用 claim_id=claim-primary-1，实际是 {concern.get('claim_id')}"
    assert len(concern.get("missing_requirements", [])) > 0, \
        "应该有 missing_requirements"

    print("✓ _claim_requirement_gap_recovery_patch_payload 使用 verified_coverage_gap_items")


def test_recovery_patch_not_generated_when_flag_disabled():
    """测试 DRMAS_DIAGPENDING_RECOVERY=0 时不生成 patch"""
    # 临时关闭 flag
    old_value = os.environ.get("DRMAS_DIAGPENDING_RECOVERY")
    os.environ["DRMAS_DIAGPENDING_RECOVERY"] = "0"

    # 重新导入以获取新的 flag 值
    import importlib
    import agent_system.inference.review_runner as runner_module
    importlib.reload(runner_module)

    state = {
        "requirement_audit": {
            "verified_coverage_gap_items": [
                {
                    "claim_id": "claim-primary-1",
                    "missing_requirements": ["baseline_comparison"],
                }
            ]
        }
    }
    manager_payload = {}

    result = runner_module._claim_requirement_gap_recovery_patch_payload(state, manager_payload)
    assert result is None, "flag 关闭时不应该生成 patch"

    # 恢复 flag
    if old_value is not None:
        os.environ["DRMAS_DIAGPENDING_RECOVERY"] = old_value
    else:
        os.environ.pop("DRMAS_DIAGPENDING_RECOVERY", None)
    importlib.reload(runner_module)

    print("✓ flag 关闭时不生成 patch")


if __name__ == "__main__":
    print("运行 coverage gap recovery 测试...\n")

    try:
        test_has_blocking_recovery_signal_with_coverage_gap()
        test_has_blocking_recovery_signal_not_triggered_before_turn_3()
        test_choose_blocking_recovery_action_with_coverage_gap()
        test_claim_requirement_gap_recovery_patch_uses_verified_items()
        test_recovery_patch_not_generated_when_flag_disabled()

        print("\n✅ 所有测试通过")
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 测试错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
