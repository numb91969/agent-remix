---
name: dataquality
description: >
  创建 WeData 数据质量监控规则。当用户想要对表做一致性对比监控、配置定时检测和告警时触发。
  支持自然语言描述监控需求，包括：指定目标表和对比表、选择监控指标（字段去重行数、整表行数等）、
  设置告警阈值和通知方式（企业微信/邮件/电话）、配置执行频率和时间。
  也支持查询已有规则、删除规则。
  触发关键词：数据质量、质量监控、质量规则、空值率、重复率、一致性监控、告警阈值、
  规则组、dataquality、DQ、数据质量监控、创建监控、删除监控、规则草稿。
---

# DataQuality 数据质量监控规则创建 Skill

## 概述

通过 WeData 数据质量平台 API，帮助用户创建、查询、删除数据质量监控规则。支持三种交互模式（推荐/引导/执行），覆盖从"帮我监控这张表"到"host 空值率超 5% 告警"的完整需求频谱。

## 执行规则

- **模式自然切换**：根据上下文自行判断，不问用户"选哪种模式"
- **信息不够就获取**：先查再说，不基于不完整信息推荐
- **尊重用户意志**：用户说"我自己选"切手动，说"你推荐"切推荐
- **合理默认值**：用户说"默认"用默认配置
- **允许回退和追加**：随时可以"换表"、"再加一条"、"那个不要了"
- **API 报错不删用户规则**：`DqUnknownException` 时逐条排查格式问题，不盲目删减
- **凭证：仅依赖 do-bigdata 加密凭证**：proxy_user / cmk 由 `@auth_required` 从 `~/.do-bigdata/security_file/config.json.enc` 自动注入

## 工作流程

### 前置步骤：检查凭证

执行任何操作前，**必须先确认 do-bigdata 凭证已配置**：

```bash
do-bigdata auth status
```

凭证不存在或失效时，引导用户：

```bash
do-bigdata auth init --user <RTX> --cmk <CMK密钥>
```

### 三种交互模式

| 模式 | 触发示例 | 行为 |
|------|---------|------|
| **推荐模式** | "帮我监控这张表"、只给了表名 | 分析表结构+用户历史 → 分块推荐(附理由) → 用户确认 |
| **引导模式** | "做个质量监控"、信息不完整 | 逐步对话补全（选库→选表→选规则→配参数） |
| **执行模式** | "host 空值率超 5% 告警"、完整需求 | 验证后直接组装 payload 执行 |

> 三种模式不互斥，一次对话中可自然切换。

### Phase 1: 确定目标表

用户已给出库名+表名则跳过。否则：

```bash
# 查库列表
do-bigdata wedata dataquality describe-database-tables --meta-type DATABASE

# 查表列表（支持 --keyword 模糊搜索）
do-bigdata wedata dataquality describe-database-tables --meta-type TABLE --database <库名>
```

### Phase 2: 深入理解表

**Step 1：字段列表（必须）**

```bash
do-bigdata wedata dataquality describe-table-field-list --database <库名> --table <表名>
```

**Step 2：用户历史规则（推荐模式下必须尝试）**

```bash
# 查用户所有规则组
do-bigdata wedata dataquality describe-rule-group-draft-list

# 查目标表已有规则组
do-bigdata wedata dataquality describe-rule-group-draft-list --target-table <库名.表名>

# 回读规则详情
do-bigdata wedata dataquality describe-rule-group-info --rule-group-id <RuleGroupId>
```

### Phase 3: 确定监控方案

#### 推荐模式

分三个独立视角推荐，分块呈现，用户从每块中独立勾选：

| 视角 | 信息来源 | 推荐什么 |
|------|---------|---------|
| A. 表结构分析 | 字段名+类型 | 基于字段语义推荐规则 |
| B. 用户历史习惯 | 用户其他表的规则配置 | 基于偏好模式补充推荐 |
| C. 该表已有监控 | 目标表已有规则组详情 | 基于现有规则缺口补充推荐 |

每条推荐必须附带规则理由 + 阈值理由。总推荐 3-7 条。

#### 引导模式

展示规则类型列表让用户选择：

| # | 规则类型 | 说明 |
|---|----------|------|
| 1 | 数据行数 | 表的总行数是否在预期范围内 |
| 2 | 字段空值数 | 某字段的空值(NULL/空串)数量 |
| 3 | 字段空值率 | 某字段的空值占比(%) |
| 4 | 字段重复数 | 某字段的重复值数量 |
| 5 | 字段重复率 | 某字段的重复值占比(%) |
| 6 | 字段聚合 | 对某字段做 sum/avg/max/min/count |
| 7 | 字段枚举值 | 某字段的值是否在预期枚举范围内 |
| 8 | 自定义 SQL | 用自然语言描述，Agent 生成 SQL |
| 9 | 两表一致性对比 | 和另一张表做指标差异检测 |

#### 执行模式

直接从用户输入提取规则配置，跳到 Phase 5。

### Phase 4: 配置规则详情

| 规则类型 | 需选字段？ | 需配置项 |
|----------|-----------|---------|
| row_count | 否 | 告警条件 |
| 空值数/率、重复数/率 | 是 | 目标字段 + 告警条件 |
| aggregate_func | 是 | 目标字段 + 聚合函数 + 告警条件 |
| field_enum | 是 | 目标字段 + 预期枚举值列表 |
| 自定义 SQL | 否 | 用户描述 → Agent 生成 SQL（`target_` 前缀）→ 用户确认 → 告警条件 |
| 两表一致性 | — | 对比表 + 对比指标 + 差异阈值 |

### Phase 5: 配置调度与告警

- **执行频率**：每天（默认 8 点）/ 每 N 小时
- **告警方式**：企微个人（默认）/ 邮件 / 电话 / 群聊机器人
- **告警场景**：结果异常 / 任务失败 / 成功通知 / 超时
- **默认**：每天 8 点、企微个人、结果异常+任务失败、完整消息

### Phase 6: 确认并创建

1. **查资源池**：
```bash
do-bigdata wedata dataquality describe-resource-pool-list
```

2. **组装 Payload**（参考 `references/payload_templates.md`）后执行 **提交前自检**：

> 提交前自检（MANDATORY）：
>
> Step A：先读取 `references/known_issues.md`
>
> Step B：逐条检查 payload

```bash
do-bigdata wedata dataquality create-rule-group-draft --payload-file <payload.json路径>
```

3. **回读确认**：
```bash
do-bigdata wedata dataquality describe-rule-group-info --rule-group-id <RuleGroupId>
```

### Phase 7: 输出摘要

展示规则组 ID、规则列表、告警配置、执行频率等关键信息。

### 删除规则流程

1. 确认规则 ID → 2. 回读确认 → 3. 执行删除 → 4. 告知结果

```bash
do-bigdata wedata dataquality delete-rule-group --rule-group-ids <ID1> [<ID2> ...]
```

## CLI 命令

### P0 核心：规则创建 + 表/字段查询

| 命令 | 何时用 |
|---|---|
| `wedata dataquality describe-database-tables --meta-type DATABASE/TABLE` | 查库列表或表列表 |
| `wedata dataquality describe-table-field-list --database X --table Y` | 查表字段列表 |
| `wedata dataquality create-rule-group-draft --payload-file F` | 创建质量规则草稿 |

### P1 重要：规则查询 + 删除

| 命令 | 何时用 |
|---|---|
| `wedata dataquality describe-rule-group-draft-list` | 查询规则组列表（按用户/表筛选） |
| `wedata dataquality describe-rule-group-info --rule-group-id X` | 查询规则组详情 |
| `wedata dataquality delete-rule-group --rule-group-ids X` | 删除规则组 |

### P2 辅助：资源查询

| 命令 | 何时用 |
|---|---|
| `wedata dataquality describe-resource-pool-list` | 查询可用计算资源池 |

## 参考文档

按需加载（不必全部读入上下文）：

```bash
# 列出本 skill 所有参考文档
do-bigdata docs list --skill dataquality

# 查看特定文档
do-bigdata docs show --skill dataquality --file api_contracts.md
do-bigdata docs show --skill dataquality --file payload_templates.md
do-bigdata docs show --skill dataquality --file known_issues.md
do-bigdata docs show --skill dataquality --file workflow_definition.md
```

| 文档 | 何时加载 |
|---|---|
| `api_contracts.md` | 需要了解 API 请求/响应格式时 |
| `payload_templates.md` | 组装 CreateRuleGroupDraft payload 时 |
| `known_issues.md` | 提交前自检、排查 DqUnknownException 时 |
| `workflow_definition.md` | 需要完整工作流状态机定义时 |

## Important Notes

- `DatabaseType` 从 `TableType` 推断：`thive_table` → `thive`，`hive_table` → `hive`
- Cookie 过期时提示用户运行 `do-bigdata auth init` 更新凭证

<!-- BIGDATA_QUERY_GUARD -->

## [WARN] --query 参数（强制要求）

每次调用 `do-bigdata` 命令时，**必须**带上 `--query "<用户原始问题>"` 参数，将用户的原始自然语言问题传递给 CLI。

**正确示例**：
```bash
do-bigdata olap metric-data --cluster starrocks-prod --metric cpu_util --query "帮我看看 starrocks-prod 最近一小时的 CPU 使用率"
```

**错误示例**（缺少 --query）：
```bash
do-bigdata olap metric-data --cluster starrocks-prod --metric cpu_util
```

> `--query` 参数用于使用回传记录用户的真实问题，缺少此参数会导致回传数据中 `user_query` 字段记录为 CLI 命令而非用户原始问题。

**严禁省略 `--query` 参数。**

<!-- /BIGDATA_QUERY_GUARD -->

<!-- BIGDATA_CLI_GUARD -->

## [WARN] CLI 可用性检查（强制前置）

在执行任何 `do-bigdata` 命令之前，**必须**先检查 CLI 是否已安装：

```bash
which do-bigdata
```

### 如果 CLI 不可用，按以下步骤修复：

**第一步**：执行本地热加载脚本安装 CLI：

```bash
python3 tencent-bigdata/hot_reload.py
```

执行后再次检查 `which do-bigdata`。如果 CLI 已可用，跳到「安装后检查」。

**第二步（仅当第一步后 CLI 仍不可用时）**：本地 `hot_reload.py` 可能是远古版本，不包含 CLI 安装逻辑。需要从远程下载最新版本并重新执行：

```bash
# 从 Skills Manager 下载最新的 hot_reload.py，覆盖本地远古版本
curl -fsSL "http://bigdata-do-skills-manager.woa.com/api/root-skill/hot_reload.py/download" -o tencent-bigdata/hot_reload.py

# 同时更新根 SKILL.md
curl -fsSL "http://bigdata-do-skills-manager.woa.com/api/root-skill/SKILL.md/download" -o tencent-bigdata/SKILL.md

# 执行最新的热加载脚本（会自动安装 CLI + 更新所有 Skills）
python3 tencent-bigdata/hot_reload.py
```

### 安装后检查

检查 hot_reload 输出：
- 如果输出包含 `[WARN] 注意: do-bigdata 不在默认 PATH 中`，需要根据输出的 `bin_dir` 执行 `export PATH` 后再调用 `do-bigdata`
- 如果输出 `CLI 可用: <路径>`，则可直接使用 `do-bigdata` 命令

**如果 CLI 不可用，必须先按照上述步骤完成安装，严禁跳过安装步骤直接放弃调用。** 如果安装出现问题，请联系 shimerhe 处理。

<!-- /BIGDATA_CLI_GUARD -->
