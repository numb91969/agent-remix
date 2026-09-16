# 腾讯问卷 API 对接操作指南（tencent-survey skill）

> 当 Rita 设计完问卷并通过审核（流程E），选择"问卷直接创建"时，自动执行以下流程。

## ⭐ P0 核心原则：连接了就直接在线生成，绝不甩 DSL

> **高频用户反馈 bug**：用户已经连好腾讯问卷，Rita 却还是丢一段 DSL 让用户自己复制到腾讯问卷里生成。这是**必须杜绝**的失职行为。

**判定与分支（每次创建问卷前先做这一步）：**

1. 检查当前会话的**可用工具列表**中是否出现 `create_survey`（以及 `get_survey`/`update_logic` 等）。
2. **✅ 出现 = tencent-survey 已 MCP 原生连接 → 必须直接调用 `create_survey` 工具在线生成**，这是最简单、最可靠的路径，不需要 Token、不需要 curl。
3. 💡 **工具当前不在活动列表 → 先用 ToolSearch 按工具名（`create_survey`）加载 schema，再用 DeferExecuteTool 调用。不要因为"没看到工具"就断定未连接、更不要直接退回甩 DSL。**
4. **❌ 确认完全没有 tencent-survey MCP → 才允许**走 curl / mcporter 备选路径；若备选也不可用，最后才降级为"输出 DSL 纯文本 + 手动导入指引"。

> **⚠️ 根因提醒**：curl / setup.sh / mcporter 那套**只适用于开发者本机命令行环境**；招聘经理在 WorkBuddy 客户端用的是 **MCP 工具直连**，两者不要混。用户反馈的 bug 正是错误地去跑 curl/setup.sh、遇阻后退回甩 DSL。

**⛔ 严禁**：只要工具列表里有 `create_survey`（或能通过 ToolSearch 加载到），就不许输出"请把下面的 DSL 复制到腾讯问卷"这类甩锅话术。

---

## 第一步：确认调用方式（优先级从高到低）

| 优先级 | 方式 | 适用条件 | 调用 |
|:---:|------|---------|------|
| **1（首选）** | **MCP 原生工具直调** | 工具列表出现 `create_survey` | 直接调用 `create_survey` 工具，传 `{"text": "<DSL>", "scene": 1}` |
| 2（备选） | mcporter CLI | 无原生工具但装了 mcporter | `mcporter call tencent-survey.create_survey --args '{"text":"<DSL>","scene":1}'` |
| 3（兜底） | curl 直连 API | 上两者都不可用、且有 Token | 见下方 curl 示例 |
| 4（最后降级） | 输出 DSL 纯文本 | 以上全部不可用 | 附手动导入指引，⛔禁止拼接 URL |

> 只要能走到优先级 1 或 2，就**不要**往下降级。降级到第 4 档 = 用户要自己动手，仅在确实无连接时才允许。

## 第二步：鉴权检查（仅 curl/mcporter 备选路径需要；MCP 原生直调通常无需手动鉴权）

```bash
# 方式一：已有 Token（环境变量）
TENCENT_SURVEY_TOKEN=xxx bash "${SKILL_DIR}/setup.sh" wj_check_and_start_auth

# 方式二：OAuth 授权（无 Token 时自动进入）
bash "${SKILL_DIR}/setup.sh" wj_check_and_start_auth
# 输出 AUTH_REQUIRED:<url> 时，向用户展示授权链接
# 然后执行：bash "${SKILL_DIR}/setup.sh" wj_wait_auth
```

> `${SKILL_DIR}` = `~/.workbuddy/skills/腾讯问卷`
> 鉴权通过后同一会话内无需重复检查。

## 第三步：将问卷方案转换为 DSL text 格式

参见 `assets/dsl-format.md` 获取完整的 DSL 语法规范。

## 第四步：创建问卷

### 首选：MCP 原生工具直调（工具列表有 create_survey 时）

直接调用 `create_survey` 工具，参数：
```json
{"text": "<DSL内容>", "scene": 1}
```
> scene：调查(1, 默认) / 考试(3) / 测评(6) / 投票(8)。返回 `survey_id` 和 `hash`。
> 这是最优路径——无需 Token、无需 curl，不要因为"想用 curl"而放弃直调。

### 备选：curl 直连（仅当工具列表无 create_survey 且备选 mcporter 也不可用）

> **沙箱确认说明**：执行网络请求时，系统可能弹出"是否在沙区外进行"的确认提示。Rita 需要主动向用户解释：
> 
> 「系统提示需要确认"沙区"权限——这是 WorkBuddy 的安全隔离机制，类似于手机App首次联网时的权限请求。创建问卷需要访问腾讯问卷服务器，所以需要你点击"允许"。这是正常操作，不会影响任何数据安全。」

```bash
# 鉴权 Token（从腾讯问卷后台获取，或通过 OAuth 授权流程获得）
TOKEN="wjpt_xxxx..."

# 创建问卷
curl -s -X POST "https://wj.qq.com/api/v2/mcp" \
  -H "Content-Type: application/json" \
  -H "Cookie: token=${TOKEN}" \
  -d '{
    "method": "tools/call",
    "params": {
      "name": "create_survey",
      "arguments": {"text": "<DSL内容>", "scene": 1}
    }
  }'
```

**返回值**：
```json
{"survey_id": 716128, "hash": "859f"}
```

## 第四步：配置跳转逻辑

如问卷包含逻辑跳转，需要：

1. 先获取问卷结构和真实 ID：
```bash
curl -s -X POST "https://wj.qq.com/api/v2/mcp" \
  -H "Content-Type: application/json" \
  -H "Cookie: token=${TOKEN}" \
  -d '{"method": "tools/call", "params": {"name": "get_survey", "arguments": {"survey_id": <返回的survey_id>}}}'
```

2. 从返回的 `pages → questions → options` 中获取真实的题目 ID（格式 `q-1-xxxx`）和选项 ID（格式 `o-100-XXXX`）

3. 根据逻辑跳转说明表编写 DSL 逻辑代码：
```bash
curl -s -X POST "https://wj.qq.com/api/v2/mcp" \
  -H "Content-Type: application/json" \
  -H "Cookie: token=${TOKEN}" \
  -d '{"method": "tools/call", "params": {"name": "update_logic", "arguments": {"survey_id": <id>, "dsl": "<逻辑代码>"}}}'
```

### 常用逻辑 DSL 语法

| Rita 逻辑设计 | DSL 写法 |
|--------------|---------|
| Q1=选项A → 显示Q3 | `if \`q-1-xx::o-100-XX\` then show \`q-1-yy\`` |
| Q1=选项A → 隐藏Q3 | `if \`q-1-xx::o-100-XX\` then hide \`q-1-yy\`` |
| Q1=选项A → 跳到Q5 | `if \`q-1-xx::o-100-XX\` then branch from \`q-1-xx\` to \`q-1-zz\`` |
| Q1=其他 → 结束问卷 | `if \`q-1-xx::o-100-XX\` then branch from \`q-1-xx\` to END` |
| 选项随机排序 | `shuffle \`q-1-xx::o-100-A\`~\`q-1-xx::o-100-D\`` |

> ID 必须从 `get_survey` 返回值中获取，**禁止自行构造**。

## 第五步：交付用户

创建成功后，向用户输出：
```
✅ 问卷已创建成功！
📋 问卷标题：[标题]
🔗 投放链接：[从 get_survey 返回值中获取的投放URL]
✏️ 编辑链接：[从 get_survey 返回值中获取的编辑URL（如响应包含 edit_url/manage_url 字段则直接输出）]
⚙️ 跳转逻辑：已配置 / 无需配置
📝 建议：发布前请在腾讯问卷后台预览确认
```

### P0：链接来源规则

- 投放链接：**必须**从 API 返回值 (`get_survey` 响应) 中提取，**禁止**自行拼接
- 编辑链接：**优先**从 API 返回值中提取（如 `edit_url`、`manage_url`、`editor_url` 等字段）；如果 API 响应中确实不包含编辑URL字段，则引导用户「打开 wj.qq.com → 我的问卷 → 找到对应问卷 → 点击编辑」
- **禁止**自行猜测/拼接任何URL格式（如 `wj.qq.com/edit/{id}` 等）——这些可能404
- **总原则**：API返回什么就输出什么，API没返回的就用文字引导路径，**绝不自己造链接**

## 第六步：后续修改（如用户要求迭代）

```bash
# 修改单题（curl方式）
curl -s -X POST "https://wj.qq.com/api/v2/mcp" \
  -H "Content-Type: application/json" \
  -H "Cookie: token=${TOKEN}" \
  -d '{"method": "tools/call", "params": {"name": "update_question", "arguments": {"survey_id": <id>, "question_id": "<q-id>", "text": "<新题目DSL>"}}}'

# 修改逻辑（整体覆盖）
curl -s -X POST "https://wj.qq.com/api/v2/mcp" \
  -H "Content-Type: application/json" \
  -H "Cookie: token=${TOKEN}" \
  -d '{"method": "tools/call", "params": {"name": "update_logic", "arguments": {"survey_id": <id>, "dsl": "<完整逻辑代码>"}}}'
```

## 错误处理

| 错误 | 原因 | 处理 |
|------|------|------|
| `missing_token` | 未鉴权 | 重新执行第一步 |
| `invalid_text_format` | DSL 语法错误 | 检查格式，修正后重试 |
| `survey_not_editable` | 问卷回收中 | 提示用户先暂停回收 |
| `paid_function_trial_no_permission` | 跳转逻辑需付费 | 告知用户需升级腾讯问卷版本 |

## 完整工作流示意

```
Rita 设计问卷 → 流程E审核通过
    ↓
转换为 DSL text 格式
    ↓
调用 create_survey → 获取 survey_id + hash
    ↓
调用 get_survey → 获取真实题目/选项 ID
    ↓
调用 update_logic → 配置跳转逻辑
    ↓
输出投放链接给用户
    ↓
用户确认 → 如需修改 → update_question / update_logic
```
