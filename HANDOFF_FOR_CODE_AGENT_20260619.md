# 交接文档:给接手的 Code Agent(2026-06-19)

> 写这份文档是因为另一个 agent(权限更高的 code 模型)没有我的跨会话记忆。这里把**项目理解 + 硬约束/已证伪教训 + 本会话所有改动 + 已确认的测试语义 + 当前状态与下一步**一次性交接。结论用中文,代码/字段名用英文。**file:line 可能随改动漂移,认函数名/commit 为准,落手前核当前代码。**

---

## 0. 一句话现状

DrMAS 多轮论文评审研究项目。**当前论文叙事完全打不动的唯一根因:Evidence Agent 合法 JSON 产出率 ~10%(~90% fallback)→ verified negative 恒为 0。** 已定位真因并落地一个强制 JSON 的修复(commit `6ce54d6`),**待你带 mimo API 验证**。在 JSON 可靠率(`evidence_json_fallback_rate_pct`)降到 <20% 之前,**冻结一切下游负向/recovery 调参**——否则信号被噪声埋着,任何 A/B 都不可信。

---

## 1. 项目理解(来自长期记忆)

- **项目**:`Dr.MAS for Paper Review`(基于 verl/verl-agent fork)。以 `ReviewState` 为中心、证据驱动、可修订的多轮论文评审系统。主模式 **S4**(Manager + Claim/Evidence/Critique Agent 分工)。数据集 DeepReview-13K。
- **论文标题方向**:*Structured Review State Tracking and Verifiable Recovery for LLM-Assisted Peer Review*。**核心贡献不是 accept/reject**,而是:structured ReviewState + 正负证据生命周期 + contested relation + guarded recovery patch + final-view hygiene。
- **核心任务一句话**:在不破坏 hygiene/safety 前提下,提高 hard-negative 场景的**负向证据召回**,使每篇 reject-prone 论文产生多个 **verified negative concerns**,并让 recovery 不只 mark_contested,还支持 evidence enrichment 与安全的 stale gap resolution。
- **主线基线**:`p25.1`(论文唯一主线基线)。当前代码主线已转 **MiMo v2.5 API + small_model adapter**。
- **当前阶段**:P26 优化 + MiMo v2.5,围绕 negative recovery / hygiene filter / recovery cap / contested support 做小步迭代。纲领见仓库 `P26_OPTIMIZATION_PLAN.md`、`PAPER_GOAL_AND_ROADMAP.md`、`AGENT.md`。

## 2. 硬约束 + 绝对不要做(已被实验证伪并回滚——别重试)

**硬约束(见 `AGENT.md`)**:不改 verl / PPO trainer / rollout 内核;不改 validator 主逻辑;不做框架级 structured-state 重构;保持 S1/S2/S3/S4;**每次只改一个可解释因素并跑 smoke 验证**;日志暴露路径、覆盖写不续写。

**Do-Not-Retry(已证伪)**:
- progression_gate / throttle / gate 任何变体、sticky 新版本、fallback 全局 suppress、任何"用简单规则阻断 recovery"的方案。
- **把 negative discovery 交给 Critique 的 model-judgment('想')而不是 Evidence 的 quote-find+verify('找+核验') = 两次证伪的 net-negative**。具体:`DRMAS_HARDNEG_DIAGNOSIS=1` 干净 A/B 决定性 net-negative(avg_reward 0.498→0.454,real_strong 75→53,negative/verified/actionable/contested/recovery **全部→0**)。根因:它把 `hard_negative_discovery_override` 路由成 analyze_flaws/Critique 而非 request_evidence_recheck/Evidence,抢走 recheck 轮,Critique 出 `diagnosis_pending_verification` 候选但无 Evidence 核验→verified negative=0。**diagnosis 方向保持默认关、只作反例**。P-A compact 同型失败。
- **下一步真正方向 = P-B(尚未实现)**:不替换 evidence-recheck 轮,用 claim-centric 诊断**重排 verify_evidence 的 target 优先级**,让 Evidence Agent 仍负责形成+核验负向。(注:本批 Codex 已加 `DRMAS_TARGETED_NEGATIVE_SEARCH`,方向上接近 P-B——Evidence 收到 claim-obligation 搜索任务,只能返回 quote-grounded 负向或 not_assessable。)

**绝对不要做**:不直接用 full39 替代 hardneg20;不放开 fallback/context claim status patch;不让 quote-bank evidence 直接 claim downgrade;不把 generic gap 包装成 negative;不为 grounded_weakness 数量牺牲 semantic grounding;不取消 recovery guard;不破坏 `state_contamination=0` / `recovery_harmful_commit_risk=0` / `recovery_no_effect_commit=0`。

**⚠️ 纠正一条过时记忆**:旧记忆写"推荐 `--max-tokens 768`(严格优于 2048)"——**这条已被本次诊断推翻**:768 在 API 后端导致 JSON 截断;应用 **2048** 且配合强制 JSON(见 §5)。

## 3. 双 agent 协作模式

用户用 **Codex + Claude 双 agent**,常让 Codex 审计 Claude 写的代码(反之亦然)。偏好中文、要点明确、**严禁"为绿而绿"**(改测试必须反映真实语义,改不对就留红并标记,不许用 `assert isinstance(...)` 之类空断言糊弄)。

## 4. 本会话改动(commits `ae178bb`、`6ce54d6`)

### 4.1 审计 Codex 的 verified-negative 硬化批次(已确认大体正确)
- 新建**三层负向门禁**(state.py):一条负向要计入 verified,必须同时:paper-grounded(`verified_grounding_label∈{paper_grounded_exact,normalized}` + 合法 span + `verified_quote_match_type` 属可信集)+ `semantic_grounding_label=="semantic_negative_verified"` + `review_negative_label=="review_negative_verified"`。作者自陈局限 / quote-bank-negative-grounding / fallback-context / semantic_mismatch 一律**不计入**。
- 审出并由 Codex 修掉的红线漏点:`_assess_review_negative_relation` 的 concrete_gap 通道曾短路绕过 author-limitation 排除(真实 run 里 QA/X41 两条作者自陈被误计 verified)。现已加 author-limitation gate。

### 4.2 我加的(commit ae178bb)
- **Fix#3 — canonicalized raw-salvage claim 必须 paper-text 可定位才能 host 负向**:`state.py` 新增 `_claim_text_locatable_in_paper` / `_salvage_negative_blocked_by_unlocatable_claim`,在 `_is_grounded_paper_negative_evidence_record` 内对 raw-salvage claim 要求 ≥60% 内容词在 `paper_text` 命中(仅 runtime 有 paper_text 时生效,离线重算回退,不动 baseline)。防 salvage 噪声 claim 冒充真实 claim 挂负向。
- **回归测试 + CI 守卫**:`tests/test_review_negative_author_limitation_guard.py`;`scripts/audit_verified_negative_author_limitation_guard_v1.py`(扫 run jsonl,任何计入 grounded 的负向若是作者自陈/quote-bank/非 verified 则 exit≠0)。
- **review_prompts.py baseline 漂移真 bug 修复**:`_critique_prompt_baseline()` 之前用"从 hardneg 变体删字符串"重建 OFF 提示,因副本漂移导致 `diagnosis_pending_verification`/hardneg 规则泄漏进默认线。已加 quote-bank 行替换 + 对齐 rule line,使 OFF 提示真正不含 hardneg 标记(`test_critique_prompt_baseline_excludes_hardneg_additions` 守住)。
- **焦点测试全绿(561 passed)**:把 36 红逐条改对(非凑绿),依据 §6 的已确认语义。新增可复用 helper `_verified_negative` / `_grounding_bank`(在 `tests/test_review_decision_hygiene.py`)。

### 4.3 我加的(commit 6ce54d6)——P0 JSON 修复
- `review_runner.py` 的 API client:加 `response_format={"type":"json_object"}`,由 env **`DRMAS_JSON_RESPONSE_FORMAT`(auto|on|off,默认 auto)** 控制。`auto`=首调尝试,被 provider 拒则**本会话降级**并不带该参数重试(瞬时错误仍走原重试循环)。下游 parser 本就吃裸 JSON,故 prompt 未改,便于干净 A/B。

## 5. P0 根因与修复细节(最重要)

**诊断**(基于最新 `nothink_compactprompt_json2048` run 的原始模型输出):
- 2048 token 下截断基本消失;主导失败是 `invalid_json` + `no_json_object`。
- 原始输出 head/tail **全是推理 prose**(如 `"First, the task is to output... My role is the Evidence Agent... To be precise..."`)——**mimo 小模型把链式推理当输出、常整段 2048 token 都在推理、根本不吐 JSON**,解析从 char 1 即崩。
- `enable_thinking:False`(review_runner `_completion_kwargs` mimo 分支)**没压住**。
- ∴ 这不是长度/prompt 措辞问题,再调那些没用;真杠杆是**强制 JSON 输出格式**。

**修复**:`response_format=json_object`(guided 解码从首 token 起约束成合法 JSON,堵死推理 prose)。已实现见 §4.3。

**验收门**:`evidence_json_fallback_rate_pct`(dashboard 已有)。**降到 <20% 前冻结一切下游负向/recovery 调参。**

**回退**:若日志出现 `response_format=json_object rejected; disabling for session` → mimo 不认该参数,回退方案是 **assistant 预填 `<json>{`**(在 `_messages` 末尾加 assistant 消息 + 在 `_call_api_once` 把前缀拼回再解析)或换 provider 的 guided 解码。若 JSON 通过率上去但 mimo 的 json 模式是 hint-only 且 `<json>` 标签冲突 → 去掉 evidence/critique prompt 的 `<json>` 标签要求(parser 已兼容纯 JSON)。

## 6. 已确认的测试/验证器语义(改这些代码或测试前必读,防回退)

- **trusted-grounding 契约**:`_has_trusted_existing_grounding` 接受的 `verified_quote_match_type` ∈ {exact, exact_match, normalized, normalized_match, quote_bank_id_canonical, quote_bank_raw_canonical, quote_bank_claim_overlap_canonical}——**`quote_bank_exact_substring/normalized_substring` 不被接受**;且需 raw_quote + 有效 span(start≥0,end>start);source 不能是 `_UNTRUSTED_VERIFIER_SOURCE_LABELS`(fallback/model/salvage/quote-bank-negative-grounding 等)。
- **`merge_review_state` 剥离模型自报 grounding**(置 `model_claimed_verification_stripped`/`runtime_evidence_verification_required`),只有能对 `evidence_quote_bank`/`paper_text` **真实核验**的引文才计为 support/negative。→ 经 merge 的测试 fixture 必须带 paper_text + quote_bank(用测试里的 `_grounding_bank` helper)。
- **review-relation 判定**(`_assess_review_negative_relation`):quote 含 positive 词("achieve/improve/outperform/...")→ positive_or_neutral_support(不计);含 author-limitation 词("limitation/future work/...")→ author_limitation_only(不计);TRUE_PAPER_NEGATIVE 类型经 concrete_gap 或 {direct_contradiction,negative_result,result_claim_mismatch,evaluation_protocol_risk} 通过。**写测试 quote 要避开 positive 词**。
- **recovery flaw 状态机**:`candidate→downgraded/retracted`(挂 verified actionable 负向)→ reject `ACTIONABLE_CONCERN_PRESERVED`;`confirmed→downgraded/retracted`→ 规范化 `confirmed→candidate` 提交(op `downgrade_final_to_candidate`);`route_to_assessment_limitation` 仅在负向**未 verified** 时提交。`RECOVERY_STATUS_TRANSITIONS["claim"]["supported"]={"unsupported","superseded"}`(supported→partially_supported 在 recovery 里**非法**→ INVALID_STATUS_TRANSITION)。
- **final-view 分类**(`_classify_flaw_final_view_layer`):verified actionable + confirmed → `grounded_weakness`;verified actionable + candidate → `potential_concern`;verified 非 actionable / scope_overclaim / scope_limitation → `assessment_limitation`;fallback/meta → `assessment_limitation`。actionable 类型集见 `TRUE_PAPER_NEGATIVE_EVIDENCE_TYPES`(注意:`scope_overclaim` 在 final-view **非 actionable**)。reason 串:negative_result/direct_contradiction→`not_confirmed_stays_potential_concern`;missing_baseline/missing_ablation→`limitation_type_stays_potential_concern`;result_claim_mismatch→`verified_candidate_stays_potential_concern`。
- **`verified_negative_evidence_ids`** 只在 active flaw 且有 verified 负向 ids 时写键 → 测试用 `.get(...)`。
- 焦点测试套件(`tests/test_recovery_patch.py` + `test_review_inference_runner.py` + `test_recovery_replay_harness.py` + `test_review_decision_hygiene.py` + `test_review_negative_author_limitation_guard.py`)当前 **561 passed**;跑法 `PYTHONPATH=$(pwd) python3 -m pytest <files> -q`(沙盒无 torch/ray,只能跑这些不依赖重包的)。

## 7. 当前状态与下一步(P0→P1)

**P0(现在)**:验证 §5 的 JSON 修复。
- 跑 smoke8 A/B:`DRMAS_JSON_RESPONSE_FORMAT=on` vs `off`,同 prompt、同 flag(见 §8),看 `evidence_json_fallback_rate_pct` 是否从 ~85% 大幅下降、`review_negative_verified_count` 是否 >0。
- fallback 降到 <20% 前**冻结下游**。
- mimo 拒绝该参数 → 上预填回退(§5)。

**P1(JSON 可靠后)**:
- 负向**质量**(verified negative 是否真实 reviewer 缺陷,跑 `scripts/audit_verified_negative_author_limitation_guard_v1.py` 守红线)。
- reward 口径:`reward.py` 的 `grounded_active_flaw_count` 字段曾不存在导致 grounded-flaw 分量恒 0(Codex 已改读 `verified_actionable_negative_flaw_count`);decision 权重仍=0,另议;改 reward 口径后需重新 baseline。
- 实现 **P-B**(claim-centric 重排 verify_evidence target,不抢 recheck 轮)。
- recovery 侧 `_flaw_verified_actionable_negative_recovery_ids` 不 gate real-claim-id、hygiene 侧 gate——口径不一致(LOW,安全方向),建议对齐。
- prompt golden-baseline 重构(别再用"删字符串"重建 OFF 提示)。

**详尽审计报告(仓库内,建议读)**:`REALNEG_ROOTCAUSE_AUDIT_20260619.md`、`REVIEW_PIPELINE_FULL_AUDIT_20260619.md`、`REVIEW_TEST_SEMANTICS_QUESTIONS_FOR_CODEX_20260619.md`、`AGENT.md`。

## 8. 启动命令(A/B,需在能连 mimo 的机器上)

```bash
export MIMO_API_KEY=...; export MIMO_BASE_URL=https://token-plan-sgp.xiaomimimo.com/v1
# A. 开 JSON 修复
TAG="mimo_v25_realneg_jsonfmt_on_smoke8_mt7_b4w2_api2_r8t600_$(date +%Y%m%d_%H%M%S)"
DRMAS_JSON_RESPONSE_FORMAT=on DRMAS_TARGETED_NEGATIVE_SEARCH=1 DRMAS_NEG_QUOTE_HYGIENE=1 \
NO_PROXY="*" HTTPS_PROXY="" HTTP_PROXY="" PYTHONPATH=".:${PYTHONPATH}" \
/opt/miniconda3/envs/DrMAS/bin/python -u agent_system/inference/review_runner.py \
  --backend api --api-provider mimo --api-model mimo-v2.5 \
  --api-max-workers 2 --api-max-retries 8 --api-timeout 600 --model-adapter-mode small_model \
  --dataset-path smoke8_sameids_20260604.parquet \
  --mode s4 --max-turns 7 --max-workers-per-turn 2 --manager-batch-size 4 \
  --temperature 1.0 --top-p 0.95 --max-tokens 2048 \
  --output-path "${TAG}.jsonl" --log-dir "${TAG}_logs" 2>&1 | tee "${TAG}.log"
# B. 对照基线:把上面的 DRMAS_JSON_RESPONSE_FORMAT=on 换成 =off,TAG 改 _off
```
跑完看:`evidence_json_fallback_rate_pct`(降了没)、`review_negative_verified_count`(>0 没),再决定质量调优 vs 预填回退。
