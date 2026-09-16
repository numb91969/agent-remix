---
name: dola
description: >
  Dola 数据分析技能 —— 支持知识库数据分析和 Agent 模式。
  此技能用于通过 Dola（大数据平台部的 AI 数据分析助手）执行数据分析和知识库查询任务。
  当用户的问题涉及以下场景时，必须使用此技能：
  1. 数据分析：查数据、分析数据、数据查询、跑数、取数、数据统计、数据报表、看板数据、指标查询、数据趋势、同比环比
  2. 知识库：查知识库、知识库问答、查知识、搜索知识库、知识库列表、我的知识库、有哪些知识库
  3. Agent：dola agent、agent列表、使用agent分析、agent市场
  4. Dola 相关：dola、Dola、DOLA、用dola查、dola分析、dola帮我查
  5. 业务数据问询：日活、月活、DAU、MAU、留存率、转化率、GMV、收入、营收、用户量、PV、UV、渗透率、漏斗分析
  6. 数据洞察：数据洞察、趋势分析、归因分析、异常检测、数据对比、数据下钻
  触发短语包括：数据分析, dola, Dola, 查数据, 分析数据, 数据查询, 知识库分析, 大数据分析, 数据洞察,
  跑数, 取数, 查知识库, 知识库问答, 数据报表, 指标查询, DAU, MAU, 留存, 转化率, 日活, 月活,
  看数据, 帮我查, 数据统计, 业务数据, 用户数据, 收入数据, 漏斗, 趋势, 归因, agent, Agent
agent_created: true
---

# Dola 数据分析 Skills（支持 Agent）

## Overview

Dola 是大数据平台部开发的 Agentic AI 数据分析助手。通过本 skill，WorkBuddy 可以调用 Dola 的 OpenAPI，帮助用户进行数据分析。

支持两种分析模式：
- **知识库模式**：指定知识库和知识项进行数据查询
- **Agent 模式**：使用预配置的 Agent（含知识库+工具+提示词）
- Agent 和知识库（repo_info）二选一

## Prerequisites — 鉴权

API 调用时使用标准的 `Authorization: Bearer <token>` 头进行身份验证。

### Token 获取方式（三选一）

Token 统一落盘在 `<skill_root>/.env/token`，所有实际 API 调用都只从这个文件读 token。

#### 方式一：OAuth2 自动授权（推荐）

运行鉴权脚本，会自动打开浏览器完成授权：

```bash
python3 scripts/taihu-auth.py
```

- 如果 `.env/token` 已存在，脚本秒退不做任何请求
- 如果不存在，脚本会打印授权 URL、尝试打开浏览器、等授权完成后自动写入 `.env/token`

#### 方式二：太湖个人令牌（PAT）

前往 **https://tai.it.woa.com/user/pat** 申请个人访问令牌（Personal Access Token），然后将获取到的 token 提供给 WorkBuddy，WorkBuddy 会自动写入 `<skill_root>/.env/token`。

适用场景：环境无法打开浏览器、OAuth2 流程受限等。

#### 方式三：Dola Skills Token 页面

前往 **https://dola.woa.com/skills-token** 获取 Token，然后提供给 WorkBuddy 写入 `<skill_root>/.env/token`。

### Token 写入规则

- 如果用户自行提供 token（无论通过哪种方式获取），将其写入 `<skill_root>/.env/token`
- 所有实际 API 调用都只从 `.env/token` 读取，不读环境变量

### 使用方式

```bash
# Step 1：确保 token 就绪（三种方式任选其一）
python3 scripts/taihu-auth.py   # 方式一：自动 OAuth2
# 或用户提供 PAT/Skills Token → 写入 .env/token

# Step 2：后续所有调用直接用 dola-cli.py
python3 scripts/dola-cli.py list --output /tmp/dola_repos.json
python3 scripts/dola-cli.py agent-list --output /tmp/dola_agents.json
python3 scripts/dola-cli.py ask --question "..." --agent-id <id>
python3 scripts/dola-cli.py poll --conversation-id <id>
```

## Workflow — 数据分析流程

### 模式选择

Dola 支持两种分析模式（**二选一**）：

| 模式 | 适用场景 | ask 参数 |
|------|---------|----------|
| **知识库模式** | 用户明确知道要查哪个知识库/知识项 | `--repo-ids` + `--item-ids` |
| **Agent 模式** | 使用预配置的 Agent（含知识库+工具+提示词） | `--agent-id` |

### Step 1: 获取可用资源

#### 获取知识库列表

```bash
python3 scripts/dola-cli.py list --output /tmp/dola_repos.json
```

**⚠️ 重要：数据量可能很大，必须写入文件再读取。**

#### 获取 Agent 列表（新增）

```bash
# 获取市场公共 Agent
python3 scripts/dola-cli.py agent-list --query-type market --output /tmp/dola_agents.json

# 获取用户自建 Agent
python3 scripts/dola-cli.py agent-list --query-type user --output /tmp/dola_agents.json
```

返回结果为 Agent 列表，每个 Agent 包含 `agentId`、`name`、`description`、`ownerId`、`canManage`、`useScope` 等信息。

**注意**：API 返回字段名是 `agentId`（驼峰），在 `ask` 命令中用 `--agent-id` 传入即可。

### Step 2: 智能推荐

根据用户需求，推荐合适的知识库 **或** Agent：

**知识库推荐格式：**
```
根据你的问题，我推荐使用以下知识库：
📚 知识库：<name>（<description>）
   - 知识项：<item_name>

确认使用这个知识库，还是要换一个？
```

**Agent 推荐格式：**
```
根据你的问题，我推荐使用以下 Agent：
🤖 Agent：<name>（<description>）

确认使用这个 Agent，还是要换一个？
```

### Step 3: 创建会话并发起分析

#### 知识库模式

```bash
python3 scripts/dola-cli.py ask --question "用户问题" --repo-ids <repo_id> --item-ids <item_id>
```

#### Agent 模式（新增）

```bash
python3 scripts/dola-cli.py ask --question "用户问题" --agent-id <agent_id>
```

脚本返回 `conversation_id`，保存供后续使用。

获取到 `conversation_id` 后，向用户提示可以在 Dola 平台直接查看输出：

```
💡 你也可以在 Dola 平台直接查看分析过程和结果：
https://dola.woa.com/ai-chat?conversation=<conversation_id>
```

### Step 4: 轮询获取结果

```bash
python3 scripts/dola-cli.py poll --conversation-id <id>
```

- 每 **5 秒**轮询一次
- `status == 0` 表示回复完成，取其 `content` 作为最终回答
- `status != 0` 表示仍在处理，继续轮询
- 建议最多轮询 120 次（10 分钟超时）

### Step 5: 展示结果

Dola 返回的 `content` 是 **Markdown 格式**，直接展示给用户即可。

### Step 6: 多轮追问（可选）

复用已有的 `conversation_id`，回到 Step 3 传入新问题即可。

## Error Handling

- **鉴权失败 / Token 过期 / HTTP 401 / HTTP 403**:
  exit code 2。引导用户删除 `.env/token` 并重跑 `taihu-auth.py`。
- **SSL / 证书错误**:
  exit code 3。提示修改脚本解决 SSL 问题。
- **知识库列表为空**: 引导用户前往 **https://dola.woa.com/knowledge** 创建知识库
- **轮询超时**: 提示用户稍后重试
- **其他 API 返回 code != 0**: 展示 `message` 字段的错误信息

### Exit code 约定

| exit code | 含义 | 动作 |
|-----------|------|------|
| `0` | 成功 | 正常处理结果 |
| `1` | 一般错误 | 展示 `error` / `detail` |
| `2` | **鉴权失败** | 引导用户重新走鉴权流程 |
| `3` | **SSL 错误** | 提示修改脚本解决 |

## API 端点速查

| 用途 | URL | Method |
|------|-----|--------|
| OAuth2 授权 | `https://dola.woa.com/abi_shakespeare/openapi/taihu/auth` | POST |
| 轮询授权状态 | `https://dola.woa.com/abi_shakespeare/openapi/taihu/session` | POST |
| 业务 API | `https://dola.mcp.it.woa.com` | POST |

### 支持的 action 列表

| action | 说明 | params |
|--------|------|--------|
| `repo_list` | 获取知识库列表 | `{}` |
| `agent_list` | 获取 Agent 列表 | `{"queryType": "market"\|"user"}` |
| `new` | 创建会话/追问 | `{"content": "问题", "repo_info": [...]}` 或 `{"content": "问题", "agent_id": "xxx"}` |
| `list` | 轮询获取消息 | `{"conversation_id": "xxx", "only_summary": true}` |

## Resources

### scripts/

- `taihu-auth.py` — 鉴权脚本
- `dola-cli.py` — Dola OpenAPI 调用脚本（增强版，支持 agent-list 和 --agent-id）

## 踩坑经验

- **Token 统一从 `.env/token` 读**: 所有 API 调用只从文件读 token。
- **Agent 和 repo_info 二选一**: `ask` 命令中 `--agent-id` 和 `--repo-ids`/`--item-ids` 不可混用。传了 `agent-id` 就不传 `repo_info`，反之亦然。
- **Agent 列表数据量**: Agent 数量也可能很多，建议用 `--output` 写文件再读。
- **通用 / 大量知识库**: 知识库列表可能非常大（50+ 个），一定要用 `--output` 写文件再读取。
