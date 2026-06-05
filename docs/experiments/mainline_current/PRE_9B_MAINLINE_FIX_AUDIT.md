# 9B 前 Mainline Fix Audit

## 结论

2.1-2.5 里仍有可以修的点，但不能全部用 runtime 硬规则修。当前已完成的是 9B 前安全收口：修 final-view/report 污染、support quality 分类口径、fallback/meta flaw 隔离；不在 9B 前放松二元 accept 阈值，也不恢复 sticky/throttle/progression gate。

## 2.1 final decision always-reject

状态：不直接用阈值硬改。

原因：clean 4B fulltest39 已证明 support-quality-only 会产生 false accept。二元 accept/reject 目前应作为 health check，而不是论文主指标。当前可安全做的是确保 final-view hygiene 不把 stale/system burden 当 paper weakness；accept-like 仍交给 derived recommendation view。

已做：

- targetless unresolved 在 final-view 中降级为 uncertainty。
- 但 targetless uncertainty 仍阻止二元 health-check accept，避免 `ZHr0JajZfH` 这类 false accept。

## 2.2 unresolved / evidence gap burden 高

状态：已做 final-view cleanup，不改 live state。

已做：

- `raw_open_unresolved=190 -> view_open_unresolved=1`。
- `raw_evidence_gaps=147 -> view_evidence_gaps=112`。
- `targetless_unresolved_deferred_count=120`。
- `stale_evidence_gap_count=35`。

解释：这些字段用于 final report / decision view，不进入 turn-by-turn manager routing，避免重演 live state hygiene 破坏 evidence formation 的问题。

## 2.3 recovery effectiveness 不是当前主增益

状态：不继续改 recovery controller。

原因：clean run 中 recovery 能运行但 commit 率仍低，且前期 sticky/throttle/gate 已证明 controller 叠加会污染解释性。本轮不恢复旧 controller，只保留 recovery phase 与 instrumentation。

## 2.4 final decision 规则和论文主线冲突

状态：已降低二元决策的论文地位，保留为保守 health check。

已做：

- final report / criterion 使用 `build_decision_hygiene_view`。
- fallback/meta flaw 不再进入 Key Weaknesses 或 criterion weakness。
- fallback/unbound strong support 不进入 final strengths。

不做：

- 不把 `real strong support >= N` 直接改成 accept。
- 不让 novelty / empirical / soundness 裸规则直接决定 reject。

## 2.5 support quality 仍需更细

状态：已修 runtime criterion/report 的 section classifier。

已做：

- `_evidence_section_bucket` 现在优先读 explicit source label，再读宽泛 bucket。
- 避免 `support_source_bucket=result_or_experiment` 把 `Table/Figure/Ablation/Method` 证据吞成普通 result。
- 新增测试覆盖：Table 证据应为 `table_or_figure`，Ablation 证据应为 `ablation`，Method 证据应为 `method`。

## 验证

- `python -m py_compile agent_system/environments/env_package/review/state.py`
- `python -m pytest tests/test_review_decision_hygiene.py -q`：15 passed。
- `scripts/analyze_final_view_hygiene_fix_v1.py` 已验证 final-view cleanup 不引入 false accept。

## 9B 测试前判断

可以进入 9B confirmation。当前 9B 前不应再新增 runtime controller，也不应继续硬调 binary final decision。9B 需要重点看：

- evidence binding 是否仍为 1.0 附近；
- fallback/unbound strong support 是否保持 0；
- support quality 的 table/method/result/ablation 分类是否更可信；
- final-view report 是否无 fallback/meta weakness；
- recommendation view 是否保持高精度，不追求二元 accept recall。
