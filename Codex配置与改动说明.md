## Codex 第三方 Provider 配置与聊天记录修复记录

本文档记录了 2026 年 6 月 10 日对 Codex 桌面端进行的完整配置调整过程，包括 CodexManager 修复、上游中转站切换、直连模式配置以及切换 Provider 后聊天记录丢失的修复方案。

---

### 一、系统架构概览

整个调用链路涉及三层：

```
Codex 桌面端  →  CodexManager（本地网关 :48760）  →  上游中转站（rawchat / sharedchat）
```

Codex 桌面端既可以经过 CodexManager 网关转发请求，也可以通过 setup 脚本配置为直连上游中转站。两种模式的配置方式、兼容性限制和已知问题各不相同，下面逐一说明。

---

### 二、CodexManager 配置（本地网关模式）

CodexManager 是运行在本地的 API 聚合代理，监听 `localhost:48760`，负责将 Codex 的请求路由到配置好的上游中转站。它的核心配置存储在 SQLite 数据库中。

**数据库路径：** `~/Library/Application Support/com.codexmanager.desktop/codexmanager.db`

**关键数据表：**

| 表名 | 用途 |
|------|------|
| `api_keys` | 网关 API Key 配置，包含轮转策略和绑定的聚合 API |
| `aggregate_apis` | 上游中转站配置（URL、状态等） |
| `aggregate_api_secrets` | 上游中转站的 API Key |
| `model_source_mappings` | 模型名到上游 API 的映射关系 |
| `gateway_error_logs` | 网关错误日志，调试用 |

**本次修改内容：**

**修改 1：绑定 API Key 到聚合 API**

原始状态中 `api_keys` 表的 `aggregate_api_id` 字段为空，导致网关找不到上游路由。

```sql
UPDATE api_keys 
SET aggregate_api_id = 'ag_6b605f329c21' 
WHERE id = 'gk_7b3be7f521aa';
```

**修改 2：切换轮转策略**

原始策略为 `account_rotation`（通过 ChatGPT 账号轮转），但账号 token 已失效。改为 `aggregate_api_rotation`（通过第三方 API 轮转）。

```sql
UPDATE api_keys 
SET rotation_strategy = 'aggregate_api_rotation' 
WHERE id = 'gk_7b3be7f521aa';
```

轮转策略说明：`account_rotation` 使用绑定的 ChatGPT 账号 token 轮转；`aggregate_api_rotation` 使用配置的第三方聚合 API 轮转；`hybrid_rotation` 两种方式混合使用。

**修改 3：更新上游 URL 和 Key**

切换到 sharedchat 时，更新了聚合 API 的地址和密钥：

```sql
UPDATE aggregate_apis 
SET url = 'https://new.sharedchat.cc/codex', updated_at = strftime('%s','now') 
WHERE id = 'ag_6b605f329c21';

UPDATE aggregate_api_secrets 
SET secret_value = 'sk-eb75cdfb310f416aa5792211acefae75', updated_at = strftime('%s','now') 
WHERE aggregate_api_id = 'ag_6b605f329c21';
```

**日志路径：** `~/Library/Application Support/com.codexmanager.desktop/gateway-trace.log`，每条记录包含 `account_id`、`upstream_url`、`elapsed_ms` 等字段，调试时重点关注 `elapsed_ms=0` 表示没有成功路由到上游。

---

### 三、上游中转站配置

#### 3.1 Rawchat（rawchat.cn/codex）

Rawchat 作为上游时没有客户端指纹校验，CodexManager 可以直接转发请求。本次调试中 Rawchat 已返回 200 OK，但后来发现额度超限（$10.09 / $10.00），无法继续使用。

额度重置时间：2026-06-11 20:30:35。

#### 3.2 Sharedchat（new.sharedchat.cc/codex）

切换到 Sharedchat 后遇到兼容性问题。Sharedchat 有客户端指纹校验机制，对请求参数有严格要求：

- 必须同时包含 `reasoning` 和 `tools` 参数，否则返回 403
- 错误信息：`"请使用最新版的codex客户端或codex cli调用"`（错误码 `codex_access_restricted`）
- CodexManager 转发请求时无法保证每次都同时携带这两个参数，导致间歇性 502

实测结果：

| 参数组合 | 结果 |
|----------|------|
| 仅 reasoning | 403 |
| 仅 tools | 403 |
| reasoning + tools | 200 |
| 都不带 | 200 |

**结论：Sharedchat 与 CodexManager 不兼容，必须使用直连模式。**

---

### 四、直连模式配置（当前生效方案）

通过 `setup-codex.sh` 脚本将 Codex 配置为直连 Sharedchat，绕过 CodexManager。

**脚本来源：** `curl -s https://vibe.aiok.me/setup-codex.sh | bash -s -- --url URL --key KEY`

**脚本做了以下修改：**

#### 4.1 config.toml（`~/.codex/config.toml`）

核心变更是 `model_provider` 从 `"cm"` 改为 `"codex"`，并新增了 `[model_providers.codex]` 配置段：

```toml
# 当前生效的 provider 名称，必须是下面定义的某个 model_providers 子段
model_provider = "codex"

# 直连 sharedchat 的 provider 配置
[model_providers.codex]
name = "codex"
base_url = "https://new.sharedchat.cc/codex"
wire_api = "responses"
supports_websockets = false
env_key = "CODEX_API_KEY"

# CodexManager 的 provider 配置（保留，切换时改 model_provider 即可）
[model_providers.cm]
name = "OpenAI"
base_url = "http://localhost:48760/v1"
wire_api = "responses"
approval_policy = "on-request"
sandbox_mode = "workspace-write"
web_search = "live"
```

脚本还额外设置了 `disable_response_storage = true`（阻止聊天记录存储）以及若干 experimental/features 标志。`disable_response_storage` 已被手动移除，否则会导致历史对话不保存。

#### 4.2 环境变量（`~/.zshrc`）

```bash
export OPENAI_BASE_URL="https://new.sharedchat.cc/codex"
export OPENAI_API_KEY="sk-eb75cdfb310f416aa5792211acefae75"
export CODEX_API_KEY="sk-eb75cdfb310f416aa5792211acefae75"
```

#### 4.3 auth.json（`~/.codex/auth.json`）

未修改，保持原始状态。该文件存储的是 OpenAI 官方 API Key 的哈希值，与第三方中转无关。

#### 4.4 切换 Provider 的快捷方式

如需在 CodexManager 模式和直连模式之间切换，只需修改 `config.toml` 中的 `model_provider` 字段：

- `"codex"` → 直连 Sharedchat（当前）
- `"cm"` → 走 CodexManager 网关（适用于 Rawchat 等兼容的中转站）

修改后重启 Codex 即可生效。

---

### 五、聊天记录丢失的修复

切换 `model_provider` 后，Codex 桌面端的历史对话列表会清空。聊天记录实际并未丢失，只是因为 Codex 按照 `model_provider` 字段过滤显示，旧对话的 provider 标识与当前不一致所以被隐藏。

#### 5.1 数据存储结构

Codex 的对话数据存储在两个位置，都需要 provider 标识一致：

**`~/.codex/state_5.sqlite`**（线程索引数据库）

`threads` 表的关键字段：`id`、`title`、`model_provider`、`rollout_path`、`archived`、`created_at`、`updated_at`。Codex 使用 `model_provider` 列（有索引 `idx_threads_provider`）过滤当前 provider 下的对话列表。

**`~/.codex/sessions/` 和 `~/.codex/archived_sessions/`**（对话内容 JSONL 文件）

每个 JSONL 文件的第一行是 `session_meta` 类型，其 `payload.model_provider` 字段记录了创建该对话时使用的 provider。Codex 在重新索引时会读取此值。

#### 5.2 修复方案

修复需要同步更新数据库和 JSONL 文件两边的 `model_provider` 值，步骤如下：

1. **关闭 Codex**（`osascript -e 'tell application "Codex" to quit'`），防止运行中的 Codex 覆盖修改
2. **更新 state_5.sqlite**：将所有 threads 的 `model_provider` 改为当前 provider
3. **更新所有 JSONL 文件**：将 `session_meta.payload.model_provider` 改为当前 provider
4. **强制 WAL 检查点**：`PRAGMA wal_checkpoint(TRUNCATE)` 确保修改写入主数据库文件
5. **重启 Codex**

自动化脚本已保存在：`~/.qoderworkcn/workspace/mpzgpefm0urjwkma/fix_codex_history.py`

使用方式：

```bash
# 1. 先关闭 Codex
osascript -e 'tell application "Codex" to quit'

# 2. 运行修复脚本
python3 ~/.qoderworkcn/workspace/mpzgpefm0urjwkma/fix_codex_history.py

# 3. 重启 Codex
open -a "Codex"
```

如需修改目标 provider（比如切回 `"cm"`），编辑脚本中的 `TARGET_PROVIDER` 变量即可。

#### 5.3 注意事项

- 修复必须在 Codex 停止状态下进行，否则 Codex 会在退出时把内存中的旧状态写回数据库，覆盖修改
- 只改数据库不改 JSONL 文件是不够的，Codex 重新索引时会从 JSONL 读取 provider 值再次覆盖
- `disable_response_storage = true` 会阻止新对话被记录，如果 setup 脚本添加了此行，需要手动删除

---

### 六、备份文件清单

本次操作过程中创建的备份文件：

| 备份文件 | 内容 |
|----------|------|
| `config.toml.bak.before_sharedchat` | 切换到 sharedchat 前的 config.toml |
| `.zshrc.bak.before_sharedchat` | 切换到 sharedchat 前的 .zshrc |
| `auth.json.bak.before_sharedchat` | auth.json 的备份 |
| `state_5.sqlite.bak.before_fix` | 修复聊天记录前的数据库 |
| `sessions.bak/` | 修复前的 sessions 目录完整备份 |
| `archived_sessions.bak/` | 修复前的归档会话备份 |
| `setup-codex.sh` | setup 脚本的本地副本 |

所有备份位于：`~/.qoderworkcn/workspace/mpzgpefm0urjwkma/`

**Anyrouter 直连配置备份（当前生效）：**

| 备份文件 | 说明 |
|----------|------|
| `codex_config_anyrouter/config.toml` | 当前生效的 config.toml（anyrouter 直连） |
| `codex_config_anyrouter/auth.json` | 当前生效的 auth.json |
| `codex_config_anyrouter/zshrc_anyrouter.env` | 当前生效的 .zshrc 环境变量片段 |

位于：`~/.qoderworkcn/workspace/mpzgpefm0urjwkma/codex_config_anyrouter/`

---

### 七、关键路径速查

| 路径 | 说明 |
|------|------|
| `~/.codex/config.toml` | Codex 主配置文件 |
| `~/.codex/auth.json` | Codex 认证信息 |
| `~/.codex/state_5.sqlite` | 对话线程索引数据库 |
| `~/.codex/sessions/` | 对话内容 JSONL 文件（按年月日组织） |
| `~/.codex/archived_sessions/` | 归档的对话内容 |
| `~/.codex/session_index.jsonl` | 会话索引（不含 provider 字段） |
| `~/.codex/history.jsonl` | 历史记录摘要（不含 provider 字段） |
| `~/.zshrc` | Shell 环境变量（API Key 等） |
| `~/Library/Application Support/com.codexmanager.desktop/codexmanager.db` | CodexManager 数据库 |
| `~/Library/Application Support/com.codexmanager.desktop/gateway-trace.log` | CodexManager 网关日志 |

---

### 八、配置模式速查手册

以下是所有可用配置模式的完整参数汇总。切换模式时，按照对应模式修改所有标注"需要修改"的文件即可。

#### 模式 1：CodexManager + 账号轮转（account_rotation）

通过 CodexManager 本地网关转发，使用绑定的 OpenAI 账号 token 轮转。

| 配置项 | 值 | 是否需修改 |
|--------|-----|-----------|
| **config.toml** `model_provider` | `"cm"` | ✅ |
| **config.toml** `[model_providers.cm]` `base_url` | `http://localhost:48760/v1` | ✅ |
| **.zshrc** `OPENAI_BASE_URL` | `http://localhost:48760/v1` | ✅ |
| **.zshrc** `OPENAI_API_KEY` | `a371e91565d4f0dc05f3b1e33b427473e7cf65d4750f10344da4950f5a02becf` | ✅ |
| **.zshrc** `CODEX_API_KEY` | `a371e91565d4f0dc05f3b1e33b427473e7cf65d4750f10344da4950f5a02becf` | ✅ |
| **auth.json** `OPENAI_API_KEY` | `a371e91565d4f0dc05f3b1e33b427473e7cf65d4750f10344da4950f5a02becf` | ✅ |
| **fix_codex_history.py** `TARGET_PROVIDER` | `"cm"` | ✅ |
| **CodexManager DB** `api_keys.rotation_strategy` | `account_rotation` | ✅ |
| **CodexManager DB** `api_keys.aggregate_api_id` | `NULL`（留空） | ✅ |

**CodexManager DB 切换 SQL：**

```sql
UPDATE api_keys SET rotation_strategy = 'account_rotation', aggregate_api_id = NULL WHERE id = 'gk_7b3be7f521aa';
```

**特点：** 使用 OpenAI 官方账号 token，无需第三方 API Key。需要账号 token 有效（通过 CodexManager 管理 token 刷新）。

---

#### 模式 2：CodexManager + 聚合 API 轮转（rawchat）

通过 CodexManager 本地网关转发，上游走 rawchat.cn。

| 配置项 | 值 | 是否需修改 |
|--------|-----|-----------|
| **config.toml** `model_provider` | `"cm"` | ✅ |
| **config.toml** `[model_providers.cm]` `base_url` | `http://localhost:48760/v1` | ✅ |
| **.zshrc** `OPENAI_BASE_URL` | `http://localhost:48760/v1` | ✅ |
| **.zshrc** `OPENAI_API_KEY` | `a371e91565d4f0dc05f3b1e33b427473e7cf65d4750f10344da4950f5a02becf` | ✅ |
| **.zshrc** `CODEX_API_KEY` | `a371e91565d4f0dc05f3b1e33b427473e7cf65d4750f10344da4950f5a02becf` | ✅ |
| **auth.json** `OPENAI_API_KEY` | `a371e91565d4f0dc05f3b1e33b427473e7cf65d4750f10344da4950f5a02becf` | ✅ |
| **fix_codex_history.py** `TARGET_PROVIDER` | `"cm"` | ✅ |
| **CodexManager DB** `api_keys.rotation_strategy` | `aggregate_api_rotation` | ✅ |
| **CodexManager DB** `api_keys.aggregate_api_id` | `ag_6b605f329c21` | ✅ |
| **CodexManager DB** `aggregate_apis` (id=`ag_6b605f329c21`) | URL: `https://rawchat.cn/codex`, status: `active` | ✅ |
| **CodexManager DB** `aggregate_api_secrets` | Key: `sk-wj9EEsrcNb0TRU6obXKWP0Q6eU10qotb` | ✅ |
| **CodexManager DB** `model_source_mappings` | 需有 source_kind=`aggregate_api`, source_id=`ag_6b605f329c21` 的所有模型映射 | ✅ |

**CodexManager DB 切换 SQL：**

```sql
-- 1. 切换轮转策略并绑定聚合 API
UPDATE api_keys SET rotation_strategy = 'aggregate_api_rotation', aggregate_api_id = 'ag_6b605f329c21' WHERE id = 'gk_7b3be7f521aa';

-- 2. 确保聚合 API 状态为 active
UPDATE aggregate_apis SET status = 'active', updated_at = strftime('%s','now') WHERE id = 'ag_6b605f329c21';

-- 3. 更新上游 URL（如需切换地址）
UPDATE aggregate_apis SET url = 'https://rawchat.cn/codex', updated_at = strftime('%s','now') WHERE id = 'ag_6b605f329c21';

-- 4. 更新 API Key（如需切换密钥）
UPDATE aggregate_api_secrets SET secret_value = 'sk-wj9EEsrcNb0TRU6obXKWP0Q6eU10qotb', updated_at = strftime('%s','now') WHERE aggregate_api_id = 'ag_6b605f329c21';

-- 5. 确保 model_source_mappings 存在（如缺失则插入）
-- 对每个模型执行：
INSERT OR IGNORE INTO model_source_mappings (id, platform_model_slug, source_kind, source_id, upstream_model, enabled, priority, weight, created_at, updated_at)
VALUES
  (lower(hex(randomblob(16))), 'gpt-5.5', 'aggregate_api', 'ag_6b605f329c21', 'gpt-5.5', 1, 0, 1, strftime('%s','now'), strftime('%s','now')),
  (lower(hex(randomblob(16))), 'gpt-5.4', 'aggregate_api', 'ag_6b605f329c21', 'gpt-5.4', 1, 0, 1, strftime('%s','now'), strftime('%s','now')),
  (lower(hex(randomblob(16))), 'gpt-5.4-mini', 'aggregate_api', 'ag_6b605f329c21', 'gpt-5.4-mini', 1, 0, 1, strftime('%s','now'), strftime('%s','now')),
  (lower(hex(randomblob(16))), 'gpt-5.5-openai-compact', 'aggregate_api', 'ag_6b605f329c21', 'gpt-5.5-openai-compact', 1, 0, 1, strftime('%s','now'), strftime('%s','now')),
  (lower(hex(randomblob(16))), 'gpt-5.4-openai-compact', 'aggregate_api', 'ag_6b605f329c21', 'gpt-5.4-openai-compact', 1, 0, 1, strftime('%s','now'), strftime('%s','now')),
  (lower(hex(randomblob(16))), 'codex-auto-review', 'aggregate_api', 'ag_6b605f329c21', 'codex-auto-review', 1, 0, 1, strftime('%s','now'), strftime('%s','now'));
```

**特点：** Rawchat 无客户端指纹校验，与 CodexManager 完全兼容。受 rawchat 额度限制（$10/周期）。

---

#### 模式 3：Sharedchat 直连（绕过 CodexManager）

Codex 客户端直连 sharedchat，不经过 CodexManager 网关。

| 配置项 | 值 | 是否需修改 |
|--------|-----|-----------|
| **config.toml** `model_provider` | `"codex"` | ✅ |
| **config.toml** `[model_providers.codex]` `base_url` | `https://new.sharedchat.cc/codex` | ✅ |
| **.zshrc** `OPENAI_BASE_URL` | `https://new.sharedchat.cc/codex` | ✅ |
| **.zshrc** `OPENAI_API_KEY` | `sk-eb75cdfb310f416aa5792211acefae75` | ✅ |
| **.zshrc** `CODEX_API_KEY` | `sk-eb75cdfb310f416aa5792211acefae75` | ✅ |
| **auth.json** | 无需修改（Codex 直连模式使用 env_key） | ❌ |
| **fix_codex_history.py** `TARGET_PROVIDER` | `"codex"` | ✅ |

**注意事项：**

- Sharedchat 有客户端指纹校验，**必须**由 Codex 客户端直接发起请求，CodexManager 转发会被拦截（403 `codex_access_restricted`）
- Sharedchat 有全站额度限制，额度耗尽时返回 502 `usage_limit_reached`
- 2026-06-12 测试时 sharedchat 已启用更严格的指纹校验，非 Codex 客户端请求一律返回 403

---

#### 模式 4：Anyrouter 直连（绕过 CodexManager）— 已验证可用 ✅

Codex 客户端直连 anyrouter.top，不经过 CodexManager 网关。provider 名称保留为 `"sharedchat"`（避免切换 provider 导致会话丢失），仅修改 `base_url` 和 key。

| 配置项 | 值 | 是否需修改 |
|--------|-----|-----------|
| **config.toml** `model` | `"gpt-5.5"` | ✅ |
| **config.toml** `model_provider` | `"sharedchat"`（保留原名，避免会话丢失） | ❌ |
| **config.toml** `[model_providers.sharedchat]` `base_url` | `https://anyrouter.top/v1` | ✅ |
| **.zshrc** `OPENAI_BASE_URL` | `https://anyrouter.top/v1` | ✅ |
| **.zshrc** `OPENAI_API_KEY` | `sk-w5B2Jv0qvK8Ynn7e01mTixtqNCI0ptAxhxr004I0nodHmtBj` | ✅ |
| **.zshrc** `CODEX_API_KEY` | `sk-w5B2Jv0qvK8Ynn7e01mTixtqNCI0ptAxhxr004I0nodHmtBj` | ✅ |
| **auth.json** `OPENAI_API_KEY` | `sk-w5B2Jv0qvK8Ynn7e01mTixtqNCI0ptAxhxr004I0nodHmtBj` | ✅ |
| **fix_codex_history.py** `TARGET_PROVIDER` | `"sharedchat"` | ❌（无需改动） |

**完整的 config.toml anyrouter 段示例：**

```toml
model = "gpt-5.5"
model_provider = "sharedchat"
preferred_auth_method = "apikey"

[model_providers.sharedchat]
name = "Shared Chat"
base_url = "https://anyrouter.top/v1"
wire_api = "responses"
```

**auth.json 示例：**

```json
{
  "OPENAI_API_KEY": "sk-w5B2Jv0qvK8Ynn7e01mTixtqNCI0ptAxhxr004I0nodHmtBj"
}
```

**可用模型（2026-06-12 查询）：** gpt-5.5、gpt-5-codex、gpt-5.4、claude-3-5-haiku-20241022、claude-3-5-sonnet-20241022、claude-3-7-sonnet-20250219、claude-fable-5、claude-haiku-4-5-20251001、claude-opus-4-1-20250805、claude-opus-4-20250514、claude-opus-4-5-20251101、claude-opus-4-6、claude-opus-4-7、claude-opus-4-8、claude-sonnet-4-20250514、claude-sonnet-4-5-20250929、gemini-2.5-pro

**测试结果（2026-06-12）：**

- Codex 桌面端直连（model=gpt-5.5）：✅ 已连通，可正常对话
- 此前使用 `model = "gpt-5-codex"` 时服务端过载返回 500，改用 `gpt-5.5` 后正常
- 此前使用旧 key 时报 "invalid codex request"，更换新 key 后问题解决

**注意事项：**

- provider 名称保留 `"sharedchat"` 是为了避免切换 provider 导致历史会话消失，实际上 `base_url` 已指向 anyrouter.top
- 从 sharedchat 切到 anyrouter 时，只需改 `base_url` 和 key，不需要运行 fix_codex_history.py
- Claude 系列模型在 responses API 下不可用（返回 404 "API 不支持此模型"）

**配置备份位置：**

| 文件 | 路径 |
|------|------|
| config.toml | `~/.qoderworkcn/workspace/mpzgpefm0urjwkma/codex_config_anyrouter/config.toml` |
| auth.json | `~/.qoderworkcn/workspace/mpzgpefm0urjwkma/codex_config_anyrouter/auth.json` |
| zshrc 环境变量 | `~/.qoderworkcn/workspace/mpzgpefm0urjwkma/codex_config_anyrouter/zshrc_anyrouter.env` |

---

### 九、模式间切换操作清单

切换配置模式时，按以下顺序操作：

1. **关闭 Codex**：`osascript -e 'tell application "Codex" to quit'`（如关不掉则 `pkill -9 -x Codex`）
2. **修改 config.toml**：按目标模式修改 `model_provider` 和相关 `[model_providers.*]` 段
3. **修改 .zshrc**：按目标模式修改 `OPENAI_BASE_URL`、`OPENAI_API_KEY`、`CODEX_API_KEY`
4. **修改 auth.json**（如需要）：按目标模式修改 `OPENAI_API_KEY`
5. **修改 fix_codex_history.py**：将 `TARGET_PROVIDER` 改为目标模式的 provider 名称
6. **修改 CodexManager DB**（仅模式 1/2 需要）：执行对应 SQL
7. **运行 fix_codex_history.py**：`python3 ~/.qoderworkcn/workspace/mpzgpefm0urjwkma/fix_codex_history.py`
8. **重启 Codex**：`open -a "Codex"`
9. **验证**：发送一条测试消息确认正常响应

---

### 十、所有密钥与标识符速查

| 名称 | 值 | 用途 |
|------|-----|------|
| CodexManager 网关 Key | `a371e91565d4f0dc05f3b1e33b427473e7cf65d4750f10344da4950f5a02becf` | Codex 连接本地 CodexManager 网关 |
| CodexManager Key ID | `gk_7b3be7f521aa` | api_keys 表主键 |
| Rawchat API Key | `sk-wj9EEsrcNb0TRU6obXKWP0Q6eU10qotb` | rawchat.cn 上游密钥 |
| Rawchat Aggregate API ID | `ag_6b605f329c21` | aggregate_apis 表主键 |
| Sharedchat API Key | `sk-eb75cdfb310f416aa5792211acefae75` | new.sharedchat.cc 密钥 |
| Sharedchat Aggregate API ID | `ag_3899d1c97458` | aggregate_apis 表主键（已禁用） |
| Anyrouter API Key（旧） | `sk-YTjqZ68Armv71bRhR6Wg5MV54nTznNnnXEGs9uSU47d49vuw` | anyrouter.top 密钥（已弃用） |
| Anyrouter API Key（新） | `sk-w5B2Jv0qvK8Ynn7e01mTixtqNCI0ptAxhxr004I0nodHmtBj` | anyrouter.top 密钥（当前生效） |
| OpenAI 账号 ID | `apple\|001639.e29c58ffe09646efb350ffc64cbd5e4d.1126::cgpt=f4c3ffb2-e232-4e96-95f8-67719988ea55\|ws=org-gWVwdzlRrkWUJBEeebXupl1b\|zs2312259317@163.com` | accounts 表主键 |

---

*最后更新：2026-06-12*
