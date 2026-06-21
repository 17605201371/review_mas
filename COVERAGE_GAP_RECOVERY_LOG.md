# Coverage Gap Recovery 实现日志

## 目标
实现 coverage gap 驱动的 recovery，生成 diagnosis_pending_concern

## 实现过程

### Commit 1: c0ec19b - 初始实现
**时间**: 2026-06-21

**内容**:
- Policy: 添加 `_state_is_recovery_relevant`、`_has_blocking_recovery_signal`、`_choose_blocking_recovery_action` 对 verified_coverage_gap 的支持
- Runner: 添加 `_claim_requirement_gap_recovery_patch_payload` 生成 recovery patch
- 测试: 添加 `test_coverage_gap_recovery.py`

**问题**: 字段名错误，使用了 `requirement_audit` 而非 `claim_requirement_audit`

**测试结果**: 558/561 passed

---

### Commit 2: 98e91c0 - 修正字段名
**时间**: 2026-06-21

**修复**: `requirement_audit` → `claim_requirement_audit`

**问题**: 仍然读不到数据，因为 `claim_requirement_audit` 不在 runtime state 里

**测试结果**: 557/561 passed

---

### Commit 3: 56acad1 - 架构重构
**时间**: 2026-06-22

**根因**: `claim_requirement_audit` 只存在于 `build_decision_hygiene_view` 的临时 view，不在 runtime state

**修复**: 两层架构
1. **Policy 层（高频调用）**: 轻量启发式 `_has_empirical_claim_without_baseline_evidence`
   - 检查 empirical claim 是否缺 baseline/comparison/ablation evidence
   - 直接读取 state 的 claims 和 evidence_map，无需调用 hygiene view
2. **Runner 层（低频调用）**: `_claim_requirement_gap_recovery_patch_payload` 自己调用 `build_decision_hygiene_view`
   - 获取精确的 `verified_coverage_gap_items`

**测试结果**: 全部通过

**smoke8 运行**: 
- Recovery 触发: ✓ (4/7 turns 进入 recovery phase)
- Patch mode: ✓ (Turn 6 进入 patch mode)
- diagnosis_pending_concern: ✗ (仍然是 0)

---

### 问题 4: 环境变量未传递
**时间**: 2026-06-22

**根因**: 启动命令用 `export DRMAS_DIAGPENDING_RECOVERY=1 && python ...` 方式，环境变量可能没传递到后台进程

**修复**: 改用 `DRMAS_DIAGPENDING_RECOVERY=1 python ...` 直接传递

**envfix 运行**:
- Recovery 触发: ✓
- Patch mode: ✓ (Turn 6)
- Patch operation: ✗ (`reject_patch`)
- diagnosis_pending_concern: ✗ (仍然是 0)

**错误信息**:
```
recovery_blocked_by: Target id 'claim-requirement-gap-claim-1-robustness-or-generaliza' 
                     was not found in the current ReviewState.
recovery_failure_code: UNKNOWN_TARGET
```

---

### Commit 4: b5d25b6 - 修复 target_id
**时间**: 2026-06-22

**根因**: 
- `gap_id` 格式: `"claim-requirement-gap-{claim_id}-{missing_requirements}"`
- 太长被截断成: `"claim-requirement-gap-claim-1-robustness-or-generaliza"`
- Recovery 系统找不到这个 target，报 `UNKNOWN_TARGET`，patch 被 reject

**修复**: `target_id` 直接用 `claim_id`（短且稳定），不用 `gap_id`

**代码**:
```python
# Before
"target_id": str(gap.get("gap_id") or claim_id),

# After
"target_id": claim_id,  # Use claim_id directly, not gap_id (gap_id is too long)
```

**测试结果**: 全部通过

**final_v2 运行**: 🔄 运行中...

---

## 技术要点

### 1. 两层检测架构
- **Policy 层**: 轻量启发式，快速检测（每 turn 调用）
- **Runner 层**: 完整 hygiene view，精确数据（低频触发）

### 2. 启发式条件
```python
empirical claim 
  AND claim_type == "empirical"
  AND importance in {"high", ""}
  AND claim_kind == "paper_extracted"
  AND status == "supported"
  AND NOT has_baseline_evidence (baseline_or_comparison / ablation_study / empirical_result)
```

### 3. Recovery 流程
1. Policy: `_has_empirical_claim_without_baseline_evidence` → True
2. Policy: `_has_blocking_recovery_signal` → True (≥3 turns)
3. Policy: `_choose_blocking_recovery_action` → `challenge_previous_hypothesis`
4. Runner: 进入 recovery phase, patch_mode=True
5. Runner: `_claim_requirement_gap_recovery_patch_payload` 调用 `build_decision_hygiene_view`
6. Runner: 生成 patch with `recovery_patch_operation: "record_diagnosis_pending_concern"`
7. State: 添加 `diagnosis_pending_concerns` 列表项

### 4. Hygiene 保证
- `state_contamination = 0`
- `recovery_harmful_commit_risk = 0`
- `recovery_no_effect_commit = 0`

---

## 待验证

**final_v2 运行**: 包含所有 4 个修复
- ✓ 字段名正确
- ✓ 两层架构
- ✓ 环境变量正确传递
- ✓ target_id 使用 claim_id

**预期结果**: `diagnosis_pending_concern_count > 0`

**运行状态**: 🔄 运行中，预计 2026-06-22 00:35 完成
