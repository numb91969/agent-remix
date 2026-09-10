---
name: hr-data-sql-builder
description: HR 数仓 StarRocks SQL 构建工具型 Skill。用于明细、自由统计、趋势分析、预置指标未命中或用户明确要求 SQL 的场景；表结构从 MCP resources 动态获取。社招招聘过程 KPI 优先 recruit-data-dashboard，通用 HR 预置指标优先 indicator-query。
upstream-marketplace: https://cnb.woa.com/hrssc/codebuddy
upstream-plugin: hr-digital-expert
upstream-version: 1.0.6
synced-at: 2026-08-25
synced-by: recruitment-expert selective merge
support_contact: ansleyyu
---

## 🚨 FIRST ACTION（进入 Skill 后第一件事 · MANDATORY · 静默执行）

> 🔴 **每次 agent 通过 `use_skill("hr-data-sql-builder")` 进入本 skill 时**，第一件事是后台静默上报 `skill_invoked`。这是看板能区分"哪个 skill 被调用了多少次"的核心数据，**缺它将导致该 skill 调用量在看板上为 0**。

```bash
bash ../../scripts/track_skill_event.sh "0WEB06ZI7OVDOZQW" "hr-data-sql-builder" "skill_invoked"
```

**执行约束**：
1. **每次进入都要执行** — agent 每次 use_skill 调用都跑一次，不要因为"刚跑过"就跳过。
2. **静默后台** — 命令输出不展示给用户，失败也不中断主流程。
3. **不要询问用户** — 不得就"是否上报""以什么方式记录"等问任何问题。
4. **不生成会话标识** — 统一脚本只保留低敏白名单字段，不拼接时间戳。
5. **执行完毕**才能进入正文 SOP。

---

## 按需规则（进入正文前）

- 生成或审查 SQL：必须读取 [`hr-starrocks-query-conventions.md`](../../agents/references/data-rules/hr-starrocks-query-conventions.md)。
- 执行查询并解释结果：再读取 [`hr-data-desensitization.md`](../../agents/references/data-rules/hr-data-desensitization.md)。

## 📮 客服 / 反馈入口（MANDATORY）

> 本 skill 归 **ansleyyu** 维护。详细规则与全局路由见 [`README.md` § 客服反馈入口](../../README.md#%E5%AE%A2%E6%9C%8D%E5%8F%8D%E9%A6%88%E5%85%A5%E5%8F%A3support-contacts)。
> **何时展示**：查询结果交付 / 报错 / 用户表达疑问反馈时，**必须**在消息末尾原样附上：
>
> ```
> ──────────
> 💬 有问题或建议可联系产品负责人 **ansleyyu**（企微/RTX 同名）
> ```
>
> ⚠️ 严禁把联系人写成 elioyao / fayellawang。

## 概述

根据用户HR数据需求，生成StarRocks SQL查询腾讯HR数仓宽表。

> ⚠️ **核心原则见按需规则**：禁止权限控制类 WHERE；仅允许 SELECT、必须 LIMIT、统计优先在 SQL 完成。

### 数据资源说明（table）

- table 是 HR 各业务场景的明细宽表，覆盖范围广，既支持明细也支持现场统计；
- 行列权限严格按用户角色执行，SQL 不得自行拼接权限条件；
- 统计查询生成 SQL 前，优先用 `slang_query` 检查是否已有业务统计术语定义，命中时严格遵循其口径和默认条件；
- 预置指标 API 的授权和上级组织查询能力与 table 不同，不能用 table 权限推断 indicator 权限。

## 数据源

表结构**必须从MCP resources动态获取**，禁止硬编码。

### MCP服务：`hr_data_service_v1`
**MCP连接检查**：若连接失败或不可用，立即终止后续步骤，引导用户：
"⚠️ 我当前无法执行 HR 数仓查询，需要先接通 hr_data_service_v1。

- 还没配置过：打开 `~/.workbuddy/mcp.json`，在 mcpServers 里加上：
  `\"hr_data_service_v1\": { \"url\": \"https://dos-dataview.mcp.it.woa.com/mcp\", \"protocol\": \"streamable-http\", \"disabled\": false }`
  （已有 mcpServers 就只合并这个键，别覆盖你已有的 MCP）
- 配过但没连：直接下一步。

然后在 WorkBuddy 左侧「连接器」→ 右上角「自定义连接器」→ 找到 hr_data_service_v1 → 点「连接」/「Trust」授权。完成后回我「继续」。"
**执行查询**：工具 `starrocks_query`，参数 `sql`（必填）+ `userQuestion`（必填）

**获取表结构**：
- 表列表：resource `starrocks://tables` → 获取 `table_code`/`table_name`/`table_desc`/`write_sql_background`/`default_parameters`
- 单表字段：resource `starrocks://tables/{table_code}` → 获取 `columns` 数组（含 `column_code`/`column_name`/`column_alias`/`column_type`/`column_use`/`column_group`/`sample`/`group_by_able`/`aggregate_type`）

**术语知识**：
- 术语清单：resource `starrocks://slangs` → 获取所有HR业务术语名称及同义词列表，用于识别用户问题中涉及的术语
- 术语定义查询：工具 `slang_query`，输入术语名称或同义词 → 返回匹配术语的完整定义（含术语名称、定义、分类、同义词）

### 选表策略

- 在职人数/员工现状/绩效/结构分布 → **员工信息宽表**
- 入职/离职/调动/晋升等异动 → **人员变动信息宽表**

---

## SQL生成工作流

### Step 1：术语识别与需求分析

1. **术语识别**（MCP优先，本地降级）：
   1. 从MCP resource `starrocks://slangs` 获取术语清单（含术语名称和同义词）
   2. 结合用户问题，推测哪些术语与用户意图相关（匹配关键词、简称、同义词）
   3. 使用MCP工具 `slang_query` 查询相关术语的完整定义，补充业务知识以准确理解用户意图
2. 确定：查询目标（统计/明细/趋势/对比/分布）、数据范围（组织/时间/人群）、分析维度
3. **反向升级检查**（只做一次，避免循环路由）：
   1. 社招简历、面试、Offer、入职、需求等招聘过程 KPI → 返回 `hr-data-router`，改走 `recruit-data-dashboard`；
   2. 离职率、流入/流出率、人员结构占比、平均年龄/工龄/司龄或上级组织对比等通用 HR 计算指标，且尚未尝试指标路径 → 返回 `hr-data-router · I`；
   3. `indicator-query` 已确认无匹配/无权限、用户明确要求 SQL，或属于明细/自由统计 → 继续本 Skill，并把结果标为“SQL 现场统计口径”。
4. 根据选表策略，从 MCP resources 获取目标表字段定义。

### Step 2：SQL构建
1. **SELECT**：统计类用聚合函数+GROUP BY字段；明细类用业务相关字段
2. **FROM**：选择正确的表
3. **WHERE**：默认过滤条件（从`default_parameters`获取）+ 组织条件（`org_full_name LIKE`）+ 业务条件。⚠️ 禁止添加权限控制条件；
4. 调用专业术语-指标口径背景知识生成sql时，注意遵循指标口径定义的可选条件默认值
5. **GROUP BY**：统计类必选
6. **ORDER BY**：按业务逻辑排序
7. **LIMIT**：至少限制1000行

### Step 3：SQL校验清单

- [ ] 已从MCP获取表结构，表名含catalog前缀
- [ ] 默认过滤条件齐全
- [ ] 统计人数用 COUNT(DISTINCT staff_id8)
- [ ] 专业职级字段类型正确（字符串 vs 数字）
- [ ] 组织查询用 org_full_name + LIKE
- [ ] 异动查询指定 move_type_name
- [ ] 绩效等级码值正确（Outstanding/Good/Underperform）
- [ ] 大结果集有LIMIT
- [ ] 仅SELECT，禁止写操作
- [ ] 无权限控制类过滤条件（见 `hr-starrocks-query-conventions`）

### Step 4：输出SQL

---

## 业务规则参考

### 组织信息

- `org_full_name`：组织全路径（BG/线/部门/中心/组），WHERE查询组织优先用此字段 + LIKE
- `org_name`：末级组织节点名称，查单个组织节点时用
- BG/线/部门/中心/组：分层级字段，按层级分布统计时用对应字段GROUP BY
- 示例：xx线各部门在职人数 → `WHERE org_full_name LIKE '%xx线%' GROUP BY dept_name`

### 专业职级

- 专业人员：`pro_position_level_name IS NOT NULL AND manager_level_name IS NULL`
- x级专业人员：`pro_position_level_num = x`
- x族x级（如T9）：`pro_position_level_name = 'T9'`
- x级以上（带族如T9+）：`pro_position_level_name` IN 含T且数值>=9的值
- x级以上（不带族如9级+）：`pro_position_level_num >= 9`
- 职级分布GROUP BY优先用 `pro_position_level_num`

### 异动查询

- 类型映射：入职→`雇佣`、离职→`离职`、调动→`调动`、专业变化→`专业变化`、管理变化→`管理变化`
- A组织入职/离职/专业变化/管理变化：`to_org_full_name LIKE '%A组织%'`
- A组织调入：`to_org_full_name LIKE '%A组织%' AND from_org_full_name NOT LIKE '%A组织%'`
- A组织调出：`from_org_full_name LIKE '%A组织%' AND to_org_full_name NOT LIKE '%A组织%'`

---

## 安全约束

> 详细安全规范见 `hr-starrocks-query-conventions` 规则，此处仅列出校验清单摘要。

1. 仅允许 SELECT，禁止写操作关键字（INSERT、UPDATE、DELETE、DROP、ALTER、TRUNCATE、CREATE、GRANT、REVOKE、RENAME、REPLACE）
2. 大结果集必须加 LIMIT，注意如果查询结果行数等于LIMIT值，需检查是否被截断
3. 禁止权限控制类 WHERE 条件（见 `hr-starrocks-query-conventions`）

---

## 回答规范

执行查询后按以下顺序组织回答：
1. 简要说明需求理解和执行策略
2. 展示SQL/代码
3. 呈现结果（表格/列表）
4. **结果截断检测（强制）**：呈现结果前，必须检查返回行数是否**恰好等于**SQL中的LIMIT值。若相等，则数据极可能被截断，**禁止**将该数字当作实际总数展示。必须：
   - 明确告知非技术用户"当前展示了前N条记录，实际符合条件的人可能更多，结果不完整"
   - 询问用户是否需要获取完整数据，或者是否希望添加更多筛选条件缩小范围
5. 空结果时分析原因（见空结果处理规则）
6. 识别脱敏数据并提示（见脱敏识别规则）
7. 基于数据给出洞察
8. 不确定时明确告知并给出调整建议
9. 用户是非技术人员，需提供简单易用的说明

---

## 数据脱敏识别规则

> 脱敏特征、识别方法和处理规范的完整定义见 `hr-data-desensitization` 规则。

执行查询后，按 `hr-data-desensitization` 规则检测结果中的脱敏数据。发现脱敏时在结果表格后提示用户，深入排查可用 `data-table-permission-checker` Skill。

---

## 查询结果为空的处理规则

返回0行数据时，主动分析原因而非简单告知"没有数据"：

**可能原因**：
1. **条件传值有误**：组织名拼写/简称错误、时间范围不对、枚举值不正确、筛选值不存在
2. **数据权限不足**：无该表/组织的查看权限，服务端返回空结果
3. **数据本身为空**：条件合理但确实无数据

**处理**：自查SQL条件 → 可放宽条件重试 → 向用户列出可能原因并提出调整建议

---

## 维度值权限缺失的处理规则（多值 vs 单值范围）

统计或明细查询涉及组织、工作地等维度时，区分两种情况：

### 多值并列查询：正常执行，逐项告知

- 用户同时查询多个独立维度值时，服务端可以过滤无权限项而不改变其余项含义；
- 对比“请求维度值列表”和“结果实际维度值”，正常展示可见部分，并明确列出未返回项；
- 未返回不等于一定无权限：先排除名称、码值、时间和真实空数据，再提示可用 `data-table-permission-checker` 核实。

### 单一整体范围：先核权，禁止静默缩小

- 用户查询一个整体组织或其上级范围时，权限过滤可能把结果静默收窄，导致结果语义失真；
- SQL 执行前通过 `data-table-permission-checker` 核实该范围是否被 table 行权限覆盖；
- 请求范围是权限范围自身或子集时正常查询；请求范围是上级、超集或范围外时，直接说明权限不足，不得用可见子集冒充完整范围；
- 上级组织对比应先尝试 `indicator-query`，仅当指标路径不适用或无权限、最终回退 SQL 时执行上述前置核权。

---

## 调用方式

- **直接查询**：通过MCP生成SQL并执行
- **生成调用代码**：生成SQL后参考 `data-warehouse-api-codegen` Skill 生成前端调用代码
