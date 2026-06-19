# P26 负向证据相关开关说明（SWITCHES.md）

本文件说明 P26 阶段为"提升 hard-negative 负向证据"加入的三个环境变量开关。
最后更新：2026-06-14（commit 3342192 之上，hardneg20 实测后）。

## 共同设计原则

- **全部默认关闭**。不设任何开关 = 原版 guard3 行为，smoke8 基线逐字节不变。
- **彼此独立**，可单独开关，方便做干净的消融（ablation）。
- **会在 run_tag / 输出文件名加后缀**，避免不同配置互相覆盖：
  - `DRMAS_NEG_DISCOVERY_MODE=aggressive` → `_negaggr`
  - `DRMAS_NEG_RECLASSIFY=1` → `_reclass`
  - `DRMAS_NEG_QUOTE_HYGIENE=1` → `_qhyg`
- 沙盒单测（默认 + 各开关组合）均通过；smoke/hardneg/full39 的真实验证须在配好 conda + MiMo API 的机器上跑。

## 速查表

| 开关 | 对应 | 作用层 | 默认 | 实测结论 |
|---|---|---|---|---|
| `DRMAS_NEG_DISCOVERY_MODE=aggressive` | 7.3 | 运行时（改路由轨迹） | 关 | **净负**：多发现但全是噪声 + 啃轮数预算 → recovery 退化 |
| `DRMAS_NEG_RECLASSIFY=1` | 7.5 | 视图层（只改最终标签/指标） | 关 | **空转**：真实数据上触发 0 次 |
| `DRMAS_NEG_QUOTE_HYGIENE=1` | option B | 运行时（改喂给 Critique 的候选） | 关 | **唯一确定性正向**：噪声占比 54%→17%，不伤 recovery |

> 关键区分：**视图层**开关（7.5）安全但容易空转、不改实际行为；**运行时**开关（7.3 / option B）会真正改结果——7.3 改了更糟，option B 改了更干净。

---

## 1. `DRMAS_NEG_DISCOVERY_MODE`（7.3：hard-negative 持续发现）

**代码位置**：`agent_system/review_manager_policy.py`
**作用层**：运行时——影响 manager 把哪些回合路由去"找负向证据"。

**管什么**：控制 hard-negative 发现循环"什么时候算够了、停止继续找"。系统每篇会主动搜负向证据，攒够一定量就不再追加发现 pass。这个开关调的就是那组停止阈值：

| 参数 | `default`（或不设） | `aggressive` |
|---|---|---|
| `_HARD_NEGATIVE_DISCOVERY_GROUNDED_TARGET` | 3 | 5 |
| `_HARD_NEGATIVE_DISCOVERY_ACTIONABLE_TARGET` | 2 | 3 |
| `_HARD_NEGATIVE_DISCOVERY_VERIFIED_FLAW_TARGET` | 2 | 3 |
| `_HARD_NEGATIVE_DISCOVERY_MAX_ATTEMPTS` | 3 | 5 |
| `_HARD_NEGATIVE_DISCOVERY_MIN_REMAINING`（剩余轮数门槛） | 2 | 1 |

接受值：`aggressive` / `hardneg` / `enrich` 视为开启；其它（含不设）= default。

**实测结论（hardneg20, mt7）**：**净负**。候选数确实上升（12→17），但多出来的几乎全进 `scope_limitation`（14→19，actionable 类型仍全 0），而且多出的发现 pass 啃掉了 mt7 仅 7 轮的预算（evidence 轮 95→108，多的全是只产问题不产证据），导致 recovery 退化：`recovery_effective_repair` 7→5、`recovery_no_effect_commit` 0→1、`mark_contested_commit` 7→5。
**教训**：只放量发现、不修类型分类/质量，就是在制造噪声并挤占预算。

---

## 2. `DRMAS_NEG_RECLASSIFY`（7.5：claim-aware 负向重分类）

**代码位置**：`agent_system/environments/env_package/review/state.py`（`build_decision_hygiene_view` 内）
**作用层**：**视图层**——只在最终决策视图/报告里改类型标签，**不改运行轨迹**。

**管什么**：把被过度归入 `scope_limitation`（非 actionable）的负向证据，在同时满足三个条件时升级为 `scope_overclaim`（actionable）：
1. 原 base 类型是 `scope_limitation`；
2. 它绑定的 real claim 是"自夸/overclaim"表述（state-of-the-art / outperforms / generalizes / universal…）；
3. quote 含具体的范围限制线索（only applies / restricted to / assumes / does not generalize…）。

保守单路径：绝不碰 noise/neutral/generic、绝不降级；升级后仍走既有 semantic 校验。升级的记录会带 `negative_type_reclassified_from` 标记便于审计。

接受值：`1` / `true` / `on` / `yes` / `aggressive`。

**实测结论（hardneg20）**：**空转**——在真实数据上触发 0 次（`negative_type_reclassified_from` 标记数 = 0；同一 jsonl 开/关该开关的 dashboard 完全相同）。原因：系统抽出的 claim 是**描述性**的（"the method uses temporal causal mechanisms"），不带自夸语言，条件 2 永不满足。
**注意**：dashboard 里出现的 `scope_overclaim>0` 是 base 分类器 + run 方差，**不是**这个开关的作用。要让 7.5 有用，得改成不依赖 claim 措辞的信号。

---

## 3. `DRMAS_NEG_QUOTE_HYGIENE`（option B：负向 quote 选择卫生）

**代码位置**：`agent_system/environments/env_package/review/state.py`
（`_build_critique_negative_quote_bank` 的两个 skip 点 + 正向 quote bank 的 `negative_or_gap` 路径；核心判定函数 `_is_low_quality_negative_quote`）
**作用层**：运行时——改的是喂给 Critique Agent 的负向候选池，因此**会改结果**。

**管什么**：在负向 quote 进候选池前，丢掉那些"匹配了 limitation/future-work 关键词、其实是噪声"的句子：
- LaTeX / 编号章节头：`\section{...FUTURE WORK}`、`9 LIMITATIONS ...`
- 参考文献 / 作者列表行（含全名作者列表，即使标题里有 "limitations" 也丢）
- "future work … can be explored" 这类前瞻方向句
- 只有自夸、无真负向线索的句子

**保守原则**：任何含真负向线索的句子（worse / fails / cannot / lacks / missing / insufficient / limited to / without a…）一律保留——包括 "\section{Limitations} 方法 does not scale" 这种标题后接真内容的。

接受值：`1` / `true` / `on` / `yes` / `aggressive`。

**实测结论（hardneg20）**：**目前唯一确定性正向**。grounded 负向里的噪声占比从 **54%（7/13）降到 ~17%（2/12）**，且 recovery 红线全部保住（effective_repair / no_effect_commit / harmful_risk / mark_contested / contested_effective / contamination 全部与基线持平）。
**残留噪声已修复（2026-06-14, P0.1）**：补了两条正则——① 裸引用标题（`_NEG_QUOTE_CITATION_TITLE_RE`，无作者列表、colon-title+limitation 关键词、无第一人称）；② future-plan 句（`_NEG_QUOTE_FUTURE_PLAN_RE`，"we will/plan to/intend to … focus/investigate/explore …"）。复验：对 qhyg run 那 12 条 grounded 负向，新 filter 正确标出原先漏网的 2 条且不误杀真负向 → **fresh run 可达 7→0**。单测 289 passed。

---

## 用法

启动脚本：`run_hardneg20_guard3.sh`（在配好 conda + `MIMO_API_KEY` 的机器上跑）。

```bash
# 默认基线（三开关全关 = guard3 原版）
bash run_hardneg20_guard3.sh

# 仅某一个
DRMAS_NEG_DISCOVERY_MODE=aggressive bash run_hardneg20_guard3.sh   # 7.3
DRMAS_NEG_RECLASSIFY=1              bash run_hardneg20_guard3.sh   # 7.5
DRMAS_NEG_QUOTE_HYGIENE=1          bash run_hardneg20_guard3.sh   # option B

# 组合（run_tag 后缀会叠加，如 _negaggr_reclass_qhyg）
DRMAS_NEG_DISCOVERY_MODE=aggressive DRMAS_NEG_RECLASSIFY=1 DRMAS_NEG_QUOTE_HYGIENE=1 bash run_hardneg20_guard3.sh
```

跑完用 `scripts/dashboard_run_comparison_v1.py` 出 dashboard 对比。

## 现状结论与方法论提醒

- 三个确定性事实：**7.5 空转、7.3 伤 recovery、option B 减噪不伤红线**。
- 其余差异（候选数 ±2、scope_overclaim 计数、decision accept/reject 比例）在单次 temp=1.0 run 的**方差范围内**，不应作为"留作主线"的依据。要可信，需**每配置多种子（3–5）取平均**。
- **真正未解决的问题**：负向**数量与类型覆盖**（candidate≥18、actionable≥12、missing_ablation / insufficient_evaluation / reproducibility_gap / result_claim_mismatch 至少各出现 1 类）。这三个开关都没碰到它——它在更上游：让 Critique/quote-bank 主动 surfacing 出这些类型的**真**证据。
