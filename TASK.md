# TASK.md

## 当前任务：P26 negative discovery 增强（交付书 2026-06-12）

**目标**：在不破坏 hygiene/safety（state_contamination=0、recovery_harmful_commit_risk=0、recovery_no_effect_commit=0、不碰 claim downgrade）的前提下，提高 hard-negative 场景的负向证据召回，让每篇 reject-prone paper 产生多个 verified negative concerns。

**当前主线代码版本**：commit `3342192`（recoverycap guard3）+ 本会话三个 mode-gated 开关（默认全关）。
**纲领以 `PAPER_GOAL_AND_ROADMAP.md` 为准**（论文目标 + 8 系统目标 + 9 不足 + P0–P4 路线图）。

### 三个开关的实测结论（详见 SWITCHES.md）
- `DRMAS_NEG_DISCOVERY_MODE=aggressive`（7.3）：**净负**——多发现全进 scope_limitation 噪声 + 啃 mt7 预算 → recovery 退化。
- `DRMAS_NEG_RECLASSIFY=1`（7.5）：**空转**——hardneg20 触发 0 次（claim 是描述性的，无 overclaim 信号）。
- `DRMAS_NEG_QUOTE_HYGIENE=1`（option B）：**唯一确定性正向**——grounded 负向噪声占比 54%→17%，不破红线。

### 已确定（不受 run 方差干扰）
1. 7.5 空转、7.3 伤 recovery、option B 减噪不伤红线。
2. 缺失类型（missing_ablation/insufficient_evaluation/reproducibility_gap/result_claim_mismatch=0）是 **discovery/retrieval 问题，不是分类问题**（已用全量负向证据扫描验证）。

### 进度（按路线图）
- ✅ **P0.1**：补 qhyg 两处残留噪声正则（裸引用标题 + future-plan），单测 289 passed，fresh run 可达噪声 7→0。
- ⏳ **P0.2（需 Mac）**：`default × 3` vs `qhyg × 3` 多次跑 + noise audit，确认减噪稳定且 recovery 不退化（noise_rate≤20%，effective_repair/mark_contested/actionable/potential ≥ default 均值−1）。
- **P1**：先做 context-coverage 诊断（缺失类型的论文段落到底有没有喂进 evidence context）→ 再决定改 prompt（type-targeted discovery）还是改 section selection。类型目标须"机会条件型"、严禁硬凑、verifier 当硬闸（历史上 Critique Context Selection 激进找负向已失败回滚）。
- **P2**：quality-aware aggressive（7.3 加预算/质量 guard，仅在 qhyg 稳定后）+ 打通 `resolve_stale_gap`（已存在，只差触发）。
- **P3**：repeated-run 稳健性贯穿（mean/std/worst-case，采用规则见路线图）。
- **P4**：以上稳定后才跑 full39 MT9。

### 开关速查（默认全关 = smoke8 基线不变）
- `DRMAS_NEG_DISCOVERY_MODE=aggressive`(7.3) / `DRMAS_NEG_RECLASSIFY=1`(7.5) / `DRMAS_NEG_QUOTE_HYGIENE=1`(option B)
- `DRMAS_NEGATIVE_PASS_MODE=compact`(P-A，已验证失败/反例) / `DRMAS_HARDNEG_DIAGNOSIS=1`(claim-centric 模型判断式诊断，默认关，待 Mac 多种子)
- 组合示例：`DRMAS_NEG_QUOTE_HYGIENE=1 bash run_hardneg20_guard3.sh`（run_tag 加 `_qhyg`）

### 2026-06-16 检查点（测试全绿 + qhyg 收口 + diagnosis 加开关）
- review 单测 514→520，OFF/ON 两种开关位置各 520 passed；recovery-replay 20 passed。详见 `CHECKPOINT_TESTS_GREEN_AND_HARDNEG_GATE_20260616.md`。
- 3 个 recovery-replay 老 fixture（9z/WL/XH）过时已修：同一根因（validator "verified positive support→BLOCKED_BY_POLICY" guard 早于旧失败码），committed HEAD 上同样 fail，确认历史遗留、非本次改动引入；commit_allowed 安全不变（XH 由 SUCCESS→BLOCKED 是 contested-relation 设计的更安全行为）。
- 新增 `DRMAS_HARDNEG_DIAGNOSIS`（默认关）：把常开未验证的 hard_negative_diagnosis_targets + prompt/schema + manager 分支(analyze_flaws/诊断 focus) + runner 诊断块 统一收到一个开关后；OFF 逐项核验=已验证基线（prompt 与 HEAD 字节相同、manager=request_evidence_recheck+formation+Evidence Agent）。claim_requirement live 解耦未动。
- audit 精度修复在 003753 离线重算确认：missing_total 14→12、仅 missing_baseline 8→6、其它类型不变。未 git commit（与 Codex 未提交解耦混在同文件，留待审计后提交）。
- **2026-06-16 后续（按 Codex 审计修点 1+3）**：点1 ON 诊断轮不再被记成 negative formation（build_turn_log 记 hard_negative_diagnosis_required + 3 个 manager 计数器跳过；OFF 安全）；点3 新增记录级 `_is_real_paper_negative_target` 让高质量 raw-salvaged 真实 paper claim 进 diagnosis，`_is_real_paper_claim_id_for_negative` 放宽为只排 context（回归 HEAD，修点2 的 OFF≠基线），status patch 仍由 `_is_fallback_recovery_claim` 阻断。脚本加 `_hardnegdiag` 后缀。单测 520→522，OFF/ON 各 522。干净 ON A/B：`DRMAS_NEG_QUOTE_HYGIENE=1 DRMAS_HARDNEG_DIAGNOSIS=1 bash run_hardneg20_guard3.sh`。点4(prompt strip 脆)暂未重构（有测试兜底）。详见 CHECKPOINT 文件后续节。

### 参考文档
- **`PAPER_GOAL_AND_ROADMAP.md` —— 纲领文件（论文目标 + 8 系统目标 + 9 不足 + P0–P4 路线图），下一步以它为准。**
- `SWITCHES.md` —— 三个开关(7.3/7.5/option B)的作用、实测结论、用法。
- `P26_NEGATIVE_DISCOVERY_CODE_LOCATIONS.md` —— 第 7 节各压制点的确切行号/改法/安全约束。
- `P26_OPTIMIZATION_PLAN.md` —— P26 总体方案 v3。

### 硬约束
不直接用 full39 替代 hardneg20；不放开 fallback/context claim status patch；不让 quote-bank evidence 直接 claim downgrade；不把 generic gap 包装成 negative；不取消 recovery guard。已知 Do-Not-Retry：progression_gate/throttle/sticky/support-formation pass/fallback 全局 suppress。
