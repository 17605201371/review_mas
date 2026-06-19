# Checkpoint: 测试全绿 + qhyg 主线收口 + hard-negative diagnosis 加默认关开关 (2026-06-16)

本次工作目标（用户指定）：(1) 把测试套件弄绿；(3) 收口 qhyg 主线；并对"常开且未验证"的 claim-centric
hard-negative diagnosis 方向**加一个默认关的开关**，使默认行为回到已验证基线、新方向变成可选（待 Mac 多种子验证）。

> **更正（回应 Codex 审计 2026-06-16）**：上面"默认行为回到已验证基线"说得过满。准确表述是：**OFF 对"diagnosis 四个触点"（prompt/critique slice/manager override 分支/runner 诊断块）逐项核验 = HEAD(3b97956)**。但工作区仍有**不受 `DRMAS_HARDNEG_DIAGNOSIS` 控制、常驻**的负向/recovery 实验改动，OFF 也带着它们，因此 OFF ≠ 完全等于旧基线。已知常驻项：① `_is_real_paper_claim_id_for_negative`（state.py:1730）现在只排除 context id，并允许 `paper_extracted` 的 `claim-paper-fallback-*` / raw-salvaged 真实论文 claim 承载负向证据，这会影响默认负向/contested 门；② audit 精度修复正则（纯诊断层，不进 reward/轨迹）；③ `_normalize_flaw_item` 对 weakness_type 的透传（OFF 时 agent 不产出该字段→空操作）。另外 Codex 指出 **ON 路径**一个计数语义 bug：turn log（state.py:11425）按 `policy_source==hard_negative_discovery_override` 把诊断轮记成 negative formation，但 ON 时该分支 `negative_evidence_formation_required=False`——会污染 ON 的"负向形成尝试次数"。下文已记录对应修复。

沙盒限制：本环境无 conda / 无 API，**不能跑推理**。以下全部是离线单测 + 离线重算 + 代码核验；GPU/API 多种子
smoke 必须在 Mac 上做。

---

## A. 测试弄绿：3 个过时的 recovery-replay fixture

`tests/test_recovery_replay_harness.py::test_all_fixtures_match` 失败。根因是**同一条**：
`recovery_validator.validate_recovery_patch` 里"claim 仍持有 verified positive support 时，禁止把它直接降级到
unsupported（应改记 contested_relation）"这条 guard，现在比 fixture 录制时的旧失败码**更早触发**。三个 fixture
都是 2026-06-04 录的快照，早于该 guard。

**关键判断：这不是本次工作区改动引入的。** `recovery_validator.py` / `recovery_replay.py` / `recovery_patch.py`
对 HEAD(3b97956) 零改动；在干净 HEAD（无任何未提交改动）上单独跑，三者同样 fail。即历史遗留的 stale fixture。

| fixture | 旧 expected | 新 expected | commit_allowed | 说明 |
|---|---|---|---|---|
| `9zEBK3E9bX_turn4` | INSUFFICIENT_EVIDENCE | BLOCKED_BY_POLICY | False→False（不变） | 无证据降级，被正面支持 guard 先拦 |
| `WLgbjzKJkk_turn4` | EVIDENCE_SEMANTIC_MISMATCH | BLOCKED_BY_POLICY | False→False（不变） | 同 guard 早于语义校验触发 |
| `XH3OiIhtvf_turn4` | SUCCESS | BLOCKED_BY_POLICY | **True→False** | 见下 |

`XH3OiIhtvf` 是唯一 commit_allowed 翻转的：patch 想把 claim-1 从 supported 降到 partially_supported 并引用一条
verified negative evidence；validator 先保守 normalize 到 unsupported，再因 claim-1 仍持有 strong verified
positive support（evidence-1-turn-2）而拦下，引导走 mark_contested。这**正是 contested-relation 设计要的更安全行为**，
旧的 SUCCESS 是加 guard 之前的快照。三者都在 fixture 里加了 `_audit_note` 字段写明理由（`meta.runner_failure_code`
保留原始录制码作为历史）。

> 安全红线未破：三者 commit_allowed 最终都是 False。

---

## B. qhyg 主线收口（离线核验）

1. **四个实验开关默认全关**：`DRMAS_NEG_DISCOVERY_MODE`(7.3)=default、`DRMAS_NEGATIVE_PASS_MODE`(P-A compact)=default、
   `DRMAS_NEG_RECLASSIFY`(7.5)=空、`DRMAS_NEG_QUOTE_HYGIENE`(qhyg/option B)=空。默认行为不变。
2. **claim_requirement 止血解耦在位**：`claim_requirement_gaps` / `claim_requirement_instruction` 不出现在任何
   live observation（evidence/critique/manager slice 与 render 都没有）；`claim_requirement_*` 只在
   `_claim_requirement_audit` + 最终 hygiene view / dashboard。
3. **audit 精度修复是纯诊断层**（放宽 `_SUPPORT_BASELINE_RE` 认 benchmark/versus/prior·previous·existing work）。
   在 `mimo_v25_..._qhyg_..._003753.jsonl`（20 篇）上用 旧(HEAD)/新 正则离线重算：

   | 指标 | 旧(HEAD) | 新(工作区) |
   |---|---:|---:|
   | claim_requirement_missing_total | 14 | 12 |
   | missing_baseline | 8 | 6 |
   | insufficient_evaluation / method_support_gap / missing_ablation / scope_overclaim | 各不变 | 各不变 |

   只削 missing_baseline 的假缺口，其它类型无变化、无任何上升。该修复不进 live prompt、不影响 reward 路径。

---

## C. 给 hard-negative diagnosis 方向加默认关开关 `DRMAS_HARDNEG_DIAGNOSIS`

该方向（不靠负面词搜索，而是让 Critique 对每个真实 claim 做"模型判断式"弱点诊断）此前是**常开**的，会改变默认
Critique 行为，且未做多种子验证。本次把它收到一个默认关的 env 开关后面。**同一个 env 变量**在四个模块各自 import 时
读取，确保一处开关同时翻转全部触点：

| 模块 | OFF（默认 = 已验证基线） | ON（`DRMAS_HARDNEG_DIAGNOSIS=1`） |
|---|---|---|
| `review_prompts.py` `CRITIQUE_PROMPT` | 与 HEAD **字节相同** 的基线 prompt | 叠加 5 条 model-judgment 规则 + 扩展 schema(weakness_type/required_evidence_type/grounding_status/扩展 neg_type 枚举) |
| `state.py` `_render_critique_state_slice` | 不注入 `hard_negative_diagnosis_targets`/`_rule`（也不回灌 claim_requirement_gaps） | 注入这两个键 |
| `review_manager_policy.py` `hard_negative_discovery_override` else 分支 | `request_evidence_recheck` + `negative_evidence_formation_required=True`（HEAD 行为，Evidence Agent） | `analyze_flaws` + `hard_negative_diagnosis_required=True` + 诊断 focus（Critique Agent） |
| `review_runner.py` "Hard-Negative Diagnosis Mode" 观察块 | 不出现（只看 manager flag，OFF 时 flag 不置） | 出现 |

**OFF=基线的逐项核验**：
- prompt：子进程 import（未设 env）得到的 `CRITIQUE_PROMPT` 与 `git show HEAD:review_prompts.py` 的 `CRITIQUE_PROMPT`
  **逐字节相同**；ON 时等于增强版字面量。
- slice：OFF 无 `hard_negative_diagnosis_targets`/`_rule`、无 `claim_requirement_gaps`；ON 多且只多这两个键。
- manager：OFF 实跑 `apply_manager_policy_fallback` 得到 `policy_source=hard_negative_discovery_override`、
  `action_type=request_evidence_recheck`、`negative_evidence_formation_required=True`、无 `hard_negative_diagnosis_required`、
  `selected_agents=['Evidence Agent']`（与 HEAD 一致）；ON 得到 analyze_flaws + 诊断 flag + `['Critique Agent']`。
- runner：`build_worker_observation` OFF 无 "Hard-Negative Diagnosis Mode" 块、ON 有。

**实现说明 / 与 Codex 解耦的关系**：我没有动 claim_requirement 的 live 解耦本身（它继续保留为"不进 live observation"），
只是给**另外新增的** diagnosis 触点加了 gate。runner 处把 `or policy_source=="hard_negative_discovery_override"` 这一项去掉、
改为只看 `manager_payload["hard_negative_diagnosis_required"]`，因为 policy_source 在 OFF/ON 都为该值、不能用来区分。

---

## 单测

- review 套件：**514 → 520 passed**。新增 6 个测试（5 个 slice/prompt gate + 1 个 manager baseline）；6 个原 diagnosis 测试
  改为显式 `monkeypatch` 打开开关（它们验证的是 ON 路由）；修 1 个 observation 测试同理。
- **OFF（默认）与 ON（`DRMAS_HARDNEG_DIAGNOSIS=1`）两种位置各 520 passed**，且 baseline 测试用 monkeypatch 强制关、
  不依赖 ambient env。
- `tests/test_recovery_replay_harness.py` 20 passed。

## 没做 / 待办（须在 Mac，沙盒跑不了推理）

- ON 路径（claim-centric diagnosis）对 support/recovery/noise 的真实影响**未验证**——这正是把它默认关的原因。
  建议：`default×N` vs `DRMAS_HARDNEG_DIAGNOSIS=1 ×N` 多种子 A/B，看 real_strong / actionable / effective_repair /
  state_contamination 是否不退化再决定是否转正。
- 我**没有 git commit**：Codex 的未提交解耦改动与这些 gate 混在同几个文件里，提交交给你和 Codex 审计后再做。

## 改动文件清单

代码：`agent_system/review_prompts.py`、`agent_system/environments/env_package/review/state.py`、
`agent_system/review_manager_policy.py`、`agent_system/inference/review_runner.py`。
测试：`tests/test_review_inference_runner.py`、`tests/recovery_replay/cases/{9zEBK3E9bX,WLgbjzKJkk,XH3OiIhtvf}_turn4_*.json`。

---

## 2026-06-16 后续：按 Codex 审计修点 1 + 点 3（为干净 ON A/B 做准备）

Codex 审计认可"默认关 diagnosis"的方向，但指出 ON 路径有计数污染、且 fallback/salvage 真实 claim 被前缀误杀。已修：

- **点 1（ON 计数污染）**：`hard_negative_discovery_override` 在 ON 时设 `negative_evidence_formation_required=False`，
  但旧逻辑按 `policy_source` 把它记成 negative formation。修法（OFF 安全，诊断 flag 在 OFF 不存在）：
  `state.build_turn_log` 记录 `hard_negative_diagnosis_required` 并据此把诊断轮的 `negative_evidence_formation_required`
  置否；`state._manager_requires_negative_evidence_formation` 与 `review_manager_policy` 的 3 个计数器
  （`_recent_negative_evidence_formation_flaw_counts` / `_has_recent_negative_evidence_formation_turn` /
  `_negative_evidence_formation_attempt_count`）跳过诊断轮。+1 单测。
- **点 3 / 点 2（真实 salvage claim 被误杀）**：新增 **`_is_real_paper_negative_target(claim, real_claim_ids)`**（记录级）
  作 diagnosis 目标门，**放行高质量 raw-salvaged 真实 paper claim**（`claim_kind=paper_extracted`，可能带
  `claim-paper-fallback-*` id），仍排除 context/recovery 脚手架；`_hard_negative_diagnosis_targets` 改用它。
  同时把 **`_is_real_paper_claim_id_for_negative`** 从"按前缀排除 fallback+context"放宽为"只排 context"——这是
  **回归 HEAD 行为**（HEAD 的 `_is_paper_negative_evidence_record` 用 `_is_real_paper_claim_id`，本就允许 fallback-paper），
  修正了 Codex 点 2 指出的"OFF 也不完全等于旧基线"。**安全不变**：对 fallback/salvage 目标的 claim *status patch* 仍由
  `recovery_validator._is_fallback_recovery_claim` 阻断（已核验）。+1 单测。
  - 注意：点 3 的负向门放宽**会改变默认（OFF）路径**（让 salvage 真实 claim 能 host 负向）——这是朝 HEAD 收敛的修正。
    你正在跑的那条默认 qhyg 用的是修复前的码；若要对比应以修复后的新默认 run 为准。
- **run 脚本**：`run_hardneg20_guard3.sh` 加 `DRMAS_HARDNEG_DIAGNOSIS` 的 `_hardnegdiag` run-tag 后缀 + meta 记录。
- **点 4（prompt strip 维护性脆）**：Codex 认为短期可接受（有测试兜底），暂未重构为"显式 baseline + 拼接 hardneg 扩展"，记为后续可选。
- **单测**：520 → **522**（+点1计数 +点3 salvage 各 1）；**OFF 与 `DRMAS_HARDNEG_DIAGNOSIS=1` 两位置各 522 passed**。

**干净 ON A/B 命令（修后）**：`DRMAS_NEG_QUOTE_HYGIENE=1 DRMAS_HARDNEG_DIAGNOSIS=1 bash run_hardneg20_guard3.sh`
（run_tag 会带 `_qhyg_hardnegdiag`）。仍未 git commit。

### 2026-06-16 再收紧：按 Codex 第二轮审计收窄 diagnosis 门（gate 过宽）

Codex 认可点 1/点 3 方向，但指出 `_is_real_paper_negative_target` 比说明更宽，会放进 (a) 没有 `claim_origin_kind` 的
`claim-paper-fallback-*`、(b) 文本是"二次转述壳/prompt 泄漏"（claim 文本里 echo 了 `claim-paper-context-1` 这类内部 id）。已收紧
（只动 diagnosis 这层；`_is_real_paper_claim_id_for_negative` 仍保持 id-based / 向 HEAD 收敛，按 Codex 建议不动）：
- fallback id（`claim-paper-fallback*` / `claim-fallback*`）只有在 `claim_origin_kind == "raw_salvaged_claim_agent_output"` 时才放行；
- 新增 `_CLAIM_NEGATIVE_TARGET_LEAKAGE_RE`，claim 文本含 `claim-paper-context|claim-context|claim-paper-fallback|claim-fallback|claim-recovery|context_derived|context_synthesized|raw_salvaged` 时排除。
- 离线核验：salvage(带 origin) 与正常 claim 仍放行；fallback(无 origin)、leakage 壳、context 都被拒。+1 单测。单测 522→**523**，OFF/ON 各 523。
- **结论**：可以重新跑干净的 `default×N vs hardnegdiag×N` 了。Codex 提醒：已跑的 `diag_on seed101` 是修复前代码，不能作转正依据；点 4(prompt strip)仍待后续可选重构。
