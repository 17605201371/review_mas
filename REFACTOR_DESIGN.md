# 负向证据流程重构设计

## 问题诊断

当前三条路径都是"找 quote"思路：
1. `HARDNEG_DIAGNOSIS`: Critique 自由诊断 → 假阳性多（已证伪两次）
2. `TARGETED_NEGATIVE_SEARCH`: Evidence targeted search → 缺失类找不到 quote
3. 默认: Evidence recheck → 还是找 quote

**根本问题**：把"审稿判断"（需要模型能力）变成了"找原文句子"（文本检索任务）。

网页端为什么能找到问题：
- 模型先理解论文主张
- 用审稿常识判断缺什么（baseline/ablation/实验不足/overclaim）
- 再引用论文材料支撑判断

## 新架构设计

### Phase 1: 确定性诊断层（不用模型判断，避免假阳性）

**输入**：ReviewState（claims + evidence + paper_text）
**输出**：`diagnosis_pending_concerns`（确定性缺陷列表）

**诊断维度**：
1. **Coverage gap（已有，需增强）**：
   - 当前：claim-centric，依赖 evidence binding（56% over-flag）
   - 改进：paper-level + full-text scan（commit 2717c16 已修）
   - 类型：missing_baseline/ablation/evaluation/robustness/efficiency

2. **Overclaim（新增）**：
   - 检测：claim 强度 > verified evidence 强度
   - 判据：claim 说"SOTA/best/significantly better" 但 evidence 只有"comparable/marginal improvement"
   - 实现：规则 + 简单模型判断（但有对抗验证）

3. **Method-result mismatch（新增）**：
   - 检测：claim 描述的方法 vs evidence 引用的表格/实验不一致
   - 判据：确定性（方法名/实验 ID 不匹配）

### Phase 2: 取证层（Evidence Agent 降级为工具）

**输入**：`diagnosis_pending_concern`
**任务**：回论文找支持或反驳材料（不判断，只提取）

**Evidence Agent 的新职责**：
- 对于 `missing_baseline` concern：找 baseline 章节/表格，提取比较方法列表
- 对于 `overclaim` concern：找 claim 对应的表格/结果，提取具体数值
- 对于 `method_gap` concern：找方法描述章节，提取关键组件

**返回**：
- `supporting_material`（支持诊断的材料，quote + locator）
- `refuting_material`（反驳诊断的材料，比如找到了 baseline）
- `not_assessable`（论文里找不到相关章节）

### Phase 3: 验证层（分流两条轨道）

**轨道 1：Quote-grounded verified negative**（极严格，0 假阳性）
- 要求：有 verbatim quote 直接反驳 claim
- 类型：own_method_underperforms, direct_contradiction
- 门禁：Route A verifier（不放松）

**轨道 2：Verified coverage concern**（确定性审计，独立计数）
- 要求：确定性缺陷 + Evidence 确认找不到（not_assessable）OR 找到的材料确认缺陷
- 类型：verified_missing_baseline, verified_insufficient_evaluation, verified_overclaim
- 门禁：对抗验证（避免假阳性）

### Phase 4: Recovery 层（支持两类 target）

**当前问题**：recovery 只认 `verified_negative_flaw`，coverage concern 进不了 recovery 轨道

**改进**：
- `challenge_previous_hypothesis` 支持 `verified_coverage_concern` target
- `mark_contested` 支持 coverage concern
- `downgrade_final_to_candidate` 识别两类缺陷

## 实现策略

### 最小可验证路径（MVP）

**Step 1**：增强 coverage gap 诊断（已完成 commit 2717c16）
- Paper-level 判断消除 56% over-flag ✓
- Full-text scan 避免 evidence binding 假阴性 ✓

**Step 2**：让 coverage gap 进入 recovery 轨道（本次重构核心）
- 修改 `_state_is_recovery_relevant` 识别 `verified_coverage_gap_items`
- 修改 `_sanitize_targets_for_action` 保留 coverage concern target
- 修改 `review_runner.py` 让 recovery patch 支持 coverage concern

**Step 3**：添加对抗验证（防止 coverage gap 假阳性）
- 用 Critique Agent 尝试反驳 coverage gap
- 如果 Critique 能找到论文里确实有该证据，降级 concern
- 保持 0 假阳性原则

**Step 4**（后续）：新增 overclaim 诊断
- 比较 claim 强度 vs evidence 强度
- 规则 + 模型判断 + 对抗验证

### 不踩的坑（Do-Not-Retry）

1. **不放松 Route A verifier**：quote-grounded 门禁保持极严格
2. **不让 Critique 做自由诊断**（HARDNEG_DIAGNOSIS 已证伪）
3. **不把 coverage concern 伪装成 verified negative quote**
4. **不破坏现有 hygiene/safety 指标**：`state_contamination=0`, `recovery_harmful_commit_risk=0`

## 验证指标

**成功标准**：
- `verified_coverage_gap_count` > 0（当前 ≈ 0）
- 命中真审稿缺陷（baseline 9→13/19）
- 假阳性 = 0（coverage gap over-flag < 20%）
- 不破坏现有 hygiene 指标

**smoke8 + hardneg20 回归**：
- smoke8 基线不变（默认不启用新路径）
- hardneg20 启用新路径（env flag 控制）
