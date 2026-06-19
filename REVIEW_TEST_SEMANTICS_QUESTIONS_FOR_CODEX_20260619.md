# 给 Codex 的询问:新门禁下的 recovery 路由 / flaw 分类语义意图

背景:你这批门禁收紧(trusted-grounding 要求 span+match_type、author-limitation 门、review_negative_verified 门、assessment_limitation 路由)让 16 个焦点测试变红。Claude 已确认其中相当一部分**不是 stale fixture,而是你改动带来的真语义变更**——旧测试编码的是旧语义。为了把测试改"对"(而不是为了变绿乱翻断言、掩盖真 bug),需要你确认下面几点**新语义是否符合你的设计意图**。已附实测产出。

## 已实测的当前行为(新代码)

flaw `f1` 有一条 verified negative(grounded:span+match_type+semantic_negative_verified+review_negative_verified),对它做 `candidate -> downgraded` 的 recovery patch:

| negative_evidence_type | committed | recovery_patch_operation | failure_code | terminal_reason |
|---|---|---|---|---|
| negative_result | False | reject_patch | ACTIONABLE_CONCERN_PRESERVED | verified_actionable_negative_concern_preserved |
| missing_baseline | False | reject_patch | ACTIONABLE_CONCERN_PRESERVED | verified_actionable_negative_concern_preserved |
| insufficient_evaluation | False | reject_patch | ACTIONABLE_CONCERN_PRESERVED | verified_actionable_negative_concern_preserved |
| scope_limitation | False | reject_patch | BLOCKED_BY_POLICY | assessment_limitation_no_effect_preserved |

delta(scope_limitation 且 source=`quote-bank-negative-grounding` 的 flaw,candidate→downgraded):
`assessment_limitation_flaw_count = 0`(旧断言 1)、`negative_grounding_conflict_count = -1`(一致)、`consistency_improved = True`(一致)、`tolerated_worsened_keys = []`(旧断言 `["assessment_limitation_flaw_count"]`)。

## 需要你确认的语义意图

**Q1 — flaw downgrade 是否一律被保留挡住?**
新代码下,只要 flaw 挂着 verified negative,无论 actionable 还是 limitation 类,downgrade **都返回 reject_patch 不 commit**。这是你的预期吗?
- 若"是":旧测试 `test_valid_patch_flaw_downgrade_commits`、`test_recovery_patch_revision_log_supports_flaw_downgrade` 的前提(downgrade 会 commit)已过时,我会把它们改成断言"保留/拒绝"(committed=False、op=reject_patch、对应 terminal_reason)。
- 若"否":请说明**什么配置下 flaw downgrade 仍应 commit**。

**Q2 — `route_to_assessment_limitation` 这个 commit 操作还存在吗?触发条件?**
`test_recovery_patch_revision_log_supports_flaw_downgrade` 断言 `recovery_patch_operation == "route_to_assessment_limitation"` 且 commit、并发 revision 事件。但现在所有 neg_type 都得到 `reject_patch`。请确认:这个"路由到 assessment_limitation 并 commit"的路径在新模型里**是否还存在**;若存在,需要怎样的 flaw/negative/claim 配置才会触发;若已废弃,我就按 reject 改断言。

**Q3 — 降级后的 quote-bank scope_limitation flaw 是否还应计 assessment_limitation?**
`test_recovery_delta_counts_negative_grounding_cleanup_as_effective_route_to_limitation` 期望 downgrade 后 `assessment_limitation_flaw_count=1` 且进 `tolerated_worsened_keys`。现在是 0、且 tolerated 为空(应该是因为 `source=quote-bank-negative-grounding` 现被判不可信)。**0 是你想要的新值吗?** 若是,我把断言改成 0 / tolerated=[]。

**Q4 — flaw 分类的迁移是否是设计预期?**
hygiene 多条断言具体分类标签,现在变了,例如:
- 期望 `grounded_weakness`,实得 `assessment_limitation`(decision_hygiene 约 :3263)。
- 期望 `potential_concern`,实得 `assessment_limitation`(约 :5301)。
即 scope/limitation 类负向被**整体重路由进 assessment_limitation**。这是你的意图吗?(影响我把这些断言改成 `assessment_limitation` 还是判定为代码过严。)

**Q5 — `verified_negative_evidence_ids` 现在是"非空才写键"吗?**
flaw 上的 `verified_negative_evidence_ids` 似乎只在非空时设置(测试无脑取键报 KeyError,约 :1970)。确认后我把测试改成 `.get(...)`(若这是有意的"无 verified negative 就不写键")。

**Q6 — 其余 hygiene 测试:stale fixture 还是有意改断言?**
大部分 hygiene 失败,根因是 fixture 缺新契约字段(`verified_source_span` + `verified_quote_match_type`,有时还要显式 `review_negative_label=review_negative_verified`)。我倾向当作 **stale fixture 补字段**。请确认这个方向 OK;若某些断言其实是你**有意改了行为**(而非 fixture 不全),请点名,我按新行为改断言而不是补字段。

(回答 Q1–Q3 即可解掉 recovery 那 3 条;Q4–Q6 给方向后,hygiene 13 条我能一次性改对并验证全绿。)
