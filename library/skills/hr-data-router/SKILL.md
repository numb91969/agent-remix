---
name: hr-data-router
description: |
  HR 数仓数据分析查询统一入口——从**沉淀数据**视角做统计、分析、看板。能力覆盖：① 基础 HR 业务数据（员工信息 / 组织架构 / 合同 / 调动 / 入离职 / 派驻 / 编制 / 职级分布 / 司龄 / 学历分布 / 绩效梯队）② 招聘历史数据分析（招聘漏斗 / 各渠道转化率 / 伯乐推荐 ROI / 校招学校分布 / 录用结构 / 招聘周期 / 需求完成率 / HC 达成率 / 部门校招社招数据看板）③ 干部能下退出 / 学习培训 / 福利假期等其他 HR 数仓宽表。内部按口径分流招聘治理指标、通用 HR 预置指标和明细 SQL，并编排数据权限排查、前端取数代码生成等子能力。
  
  什么时候用我：**在 `recruit-data-dashboard` 已判定未命中 44 治理指标之后**，承接「XX 部门今年招了多少人（治理库无对应口径时）」「校招需求完成率」「在职人数/学历分布/司龄结构」「step_name 环节粒度」「活水专项」「搭个 XX 数据看板」等查询。
  
  不要用我：① 要做**实时业务动作**（约面、写面评、搜简历、推进流程）走对应招聘 skill ② 问**规则制度**（活水冷冻期、伯乐奖金怎么算、offer 审批流）走 recruitment-inquiry-bot。
  
  🔴 **前置门禁（用户约定 2026-08-26）**：本 Skill 是数据域的 **fallback 入口，不是默认第一站**。数据域请求应先经 `recruit-data-dashboard` 做 44 治理指标命中判断；只有在「已确认未命中 + 已向用户显式告知口径降级」之后才进入本 Skill。例外仅四类：精确斜杠命令 `/HR数据`、纯前端取数代码类（F-*）、权限排查症状（`*` / 异常 0 / 1970）、同主题连续追问。若发现本轮尚未过 dashboard 判断，应先补做该判断再继续。交付时须标注「口径来源：数仓自由查询（非 44 治理指标）」。
support_contact: ansleyyu
---

# hr-data-router · HR 数仓数据分析查询路由


## 🚨 FIRST ACTION（进入 Skill 后第一件事 · MANDATORY · 静默执行）

> 🔴 **每次 agent 通过 `use_skill("hr-data-router")` 进入本 skill 时**，第一件事是后台静默上报 `skill_invoked`。这是看板能区分"哪个 skill 被调用了多少次"的核心数据，**缺它将导致该 skill 调用量在看板上为 0**。

```bash
bash ../../scripts/track_skill_event.sh "0WEB06ZI7OVDOZQW" "hr-data-router" "skill_invoked"
```

**执行约束**：
1. **每次进入都要执行** — agent 每次通过 `use_skill("hr-data-router")` 调用本 skill 时都跑一次，不要因为"刚跑过"就跳过。
2. **静默后台** — 命令输出不展示给用户，失败也不中断主流程。
3. **不要询问用户** — 不得就"是否上报""以什么方式记录"等问任何问题。
4. **不生成会话标识** — 统一脚本只保留低敏白名单字段，不拼接时间戳。
5. **隐私最小化** — 只上报 Skill、事件和运行状态，不上传用户原话或候选人数据。
6. **执行完毕**才能进入正文 SOP。

> ⚠️ 与 hook 互补：WorkBuddy SessionStart hook 只在会话启动时触发 1 次（一次会话内 agent 调本 skill 100 次只触发 1 次 hook），所以**真实的"agent 调用次数"只能靠这条 FIRST ACTION 上报**。

---

## 按需装载数据规则

完成意图分流后再读取规则，避免三份长规则常驻上下文：

| 路由 | 必读规则 |
|---|---|
| Q（通用查询） | [`hr-starrocks-query-conventions.md`](../../agents/references/data-rules/hr-starrocks-query-conventions.md)；展示结果时再读脱敏规则 |
| I（预置指标） | 展示结果时读取 [`hr-data-desensitization.md`](../../agents/references/data-rules/hr-data-desensitization.md) |
| P（权限排查） | [`hr-data-desensitization.md`](../../agents/references/data-rules/hr-data-desensitization.md) |
| F-api / F-indicator-api / F-page | [`hr-datawarehouse-api-constraint.md`](../../agents/references/data-rules/hr-datawarehouse-api-constraint.md) + 对应数据源规则 + 脱敏规则 |
| F-vue（纯组件） | 无需加载数仓规则；只有接入真实数据时再加载 |

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


> 你是 HR 数据分析查询的统一入口与编排中心。**所有沉淀数据的查询/统计/分析（含招聘历史数据）从这里进**，由本 Skill 决定调用哪个子 Skill / 哪个 MCP 工具，并把结果按统一规范呈现。
>
> **核心边界（v5.1）**：本 Skill 处理"分析数据"，**不**处理"做业务动作"。判别口诀：「今年/比例/分布/漏斗/趋势」= 数据分析（来）；「我现在/我要/我的待办」= 业务动作（不来）。

---

## 🚨 §0 边界硬规则（CRITICAL — 路由前必读 · v5.1 重写）

### 0.1 受理范围（白名单）

✅ **本 Skill 处理**：HR 数仓的**所有沉淀数据分析**，包括但不限于：

| 主题域 | 典型问题 | 主用宽表（参考） |
|---|---|---|
| 员工现状（最新 T-1） | "A 部门当前在职多少人 / 各职级分布 / 学历结构" | Report_Wide_Public_Staff_Info（最新版）|
| 员工历史快照（月末） | "B 部门去年 12 月在职人数对比今年 6 月" | Report_Wide_Public_Staff_Info（月末快照版）|
| 组织架构 | "今年新建 / 撤销了哪些组 / 组织异动" | Report_OD_Org_Info / Report_Org_Move_Record_New |
| 合同 | "未来 3 个月合同到期的员工 / 无固定期限合同分布" | Report_Wide_Public_Staff_Contract_Info |
| 调动 | "A 部门近 1 年流入流出 / 跨 BG 调动" | Report_Wide_Public_Staff_Transfer_Info |
| 入离职 | "今年入职/离职明细及结构 / 离职原因分布" | Report_Wide_Public_Staff_Register_Info / Dimission_Info |
| 派驻 | "当前派驻中的员工 / 派驻津贴" | Report_StaffStation |
| 编制 / HC | "各组织编制使用情况 / 剩余 HC" | Report_HC_Management |
| 绩效 / 梯队 | "近 4 个评估周期的结果分布" | 员工信息宽表 |
| **招聘历史数据分析** ⚠️ | "**今年校招漏斗 / 各渠道转化率 / 伯乐推荐效果 / 校招录用学校分布 / 社招公司来源**" | Report_Recruit_Flow_Detail / Report_Recruit_Resume_Assessment / Report_School_Recruit_* / Report_Bole_Recommendation_Record_Details |
| 干部能下退出 | "近一年干部能下 / 退出明细 / 管理者结构" | Report_OD_Manager_Demotion_Info / Report_OD_Manager_Quitting |
| 导师 / 讲师 | "导师辅导记录 / 讲师授课能力" | Report_Tutor_Counseling_Record / Lecturer 表 |
| 学习 | "课程学习行为 / 班级运营数据" | t_ads_dw_qlearning_lrs_behavioral_for_staff |
| 福利 / 假期 | "周末 / 节假日加班 / 休假申请 / 安居贷款" | Report_Benefits_* / Report_Housing_Plan_* |
| BP 关系 | "某部门当前 BP 是谁" | Report_BP_bp_mapping |
| 流程 | "权限中台流程实例 / 流程委托" | Hris_flow_* / Report_Liu_Cheng_* |

🔴 **重要认知**：hr-ai-data 数仓**包含招聘历史数据**！招聘域的「漏斗 / 转化率 / 渠道效果 / 伯乐 ROI / 录用结构」等**历史分析**问题就该由本 Skill 处理，**不要**因为出现"招聘"二字就把控制权丢回 agent 让它路由到招聘 skill——招聘 skill 没有这种历史分析口径。

### 0.2 拒绝范围（黑名单）⚠️ 严格执行

❌ **本 Skill 严禁处理"实时业务动作"场景**，必须立即把控制权交还 agent，由 agent 路由到正确的业务 skill：

| 用户问题特征（业务动作） | 正确路由目标 |
|---|---|
| 我要搜简历 / 帮我招人 / 推进流程 / 锁定简历 | `zhaopin-operations`（校招）/ `zhaopin-social-operations`（社招） |
| 我的面试待办 / 推荐待办 / 待填面评 / 今天的面试 | `interview-assistant · T/T2/D` |
| 我要约面 / 改面 / 取消面试 / 查我的日程 | `interview-assistant · S` |
| 我要写面评 / 评这个候选人 / 出题 / 出面试题 | `interview-assistant · B/C/D` |
| 我要写 JD / 搭胜任力模型 / 做人才画像 / 招聘需求沟通 | `requirement-communication-assistant` / `assessment-quality-expert` |
| **我现在负责的招聘流程到哪一步**（实时业务态） | `recruitment-process-tracker` |
| 招聘业务知识问询（活水规则 / 伯乐奖金算法 / 三方协议条款 / 实习考核流程） | `recruitment-inquiry-bot` |

### 0.3 关键判别（招聘历史数据 vs 招聘实时业务）

> 这是最容易踩坑的场景。下面给出判别表：

| 用户问法 | 路由 | 原因 |
|---|---|---|
| "**今年我们 BG 校招漏斗的转化率**" | ✅ 本 Skill | 历史数据分析 |
| "**A 部门今年伯乐推荐了多少人，转化率多少**" | ✅ 本 Skill | 历史数据分析 |
| "**校招今年录用员工的学校分布**" | ✅ 本 Skill | 历史数据分析 |
| "**社招今年各渠道效果排名**" | ✅ 本 Skill | 历史数据分析 |
| "**招聘活水部的校招需求完成率**" | ✅ 本 Skill | 历史数据分析（需求完成率 = 录用人数 / 需求人数，是招聘漏斗的统计指标） |
| "**XX 部门 HC 达成率多少**" | ✅ 本 Skill | 历史数据分析（HC 达成率 = 入职 / HC 数） |
| "**看板：云架构平台部 26 年校招毕业生数据**" | ✅ 本 Skill | 数据看板 = 按部门+年份+人群做录用/招聘统计可视化，走数仓 → SQL → 数据；如需前端可视化再编排 data-warehouse-api-codegen |
| "**XX 部门校招/社招数据大盘**" | ✅ 本 Skill | 同上，dashboard/大盘/看板都是数据分析可视化 |
| "**我现在负责的岗位流程到哪一步**" | ❌ 转 `recruitment-process-tracker` | 实时业务态 |
| "**我的面试待办**" | ❌ 转 `interview-assistant · T` | 实时业务动作 |
| "**帮我搜个候选人**" | ❌ 转 `zhaopin-operations` | 业务动作 |

### 0.4 模糊场景（必须反问，禁止猜测）

如果用户问题不能明确区分"分析 vs 业务动作"，**立即把控制权交还 agent，由 agent 加载 `route-ambiguities.yaml` 对应歧义组反问消歧**。常见灰色场景：

- "看看 XX 部门的招聘情况" → 实时进度还是历史分析？
- "查一下我们组的数据" → HR 数据还是招聘数据？
- "招聘漏斗" → 实时业务漏斗还是年度统计漏斗？

🔴 **分不清就交还 agent 反问，不要在本 Skill 内强行二选一**。

### 0.5 跨域协作场景

如果用户需求**真的跨两条链路**（例：「我组织里离职率高，要从外部招新人补」），由 agent 拆成两步分别在两个链路里跑，**不要试图在本 Skill 里搞定**。

---

## 🚨 §1 MCP 探活（首次进入必做）

> 腾讯招聘专家已在专家包 `.mcp.json` 与 `plugin.json` 中声明 `hr_data_service_v1`。进入数据查询能力时，WorkBuddy 应直接唤起连接并完成太湖授权；**不需要招活 Token，也不应把手写配置作为首选步骤**。

### 1.1 探活方法

按以下顺序检查（任一可用即视为接通）：
1. 当前会话能否访问 HR 数据 MCP，工具如 `starrocks_query` / `slang_query` / `get_current_user_data_permission`（最直观）
2. 连接器状态是否显示 `hr_data_service_v1` 已连接
3. 仅兼容旧客户端：Read `~/.workbuddy/mcp.json`，确认 `mcpServers` 里存在未 disabled 的 `hr_data_service_v1` 段

### 1.2 失败时的连接引导（v5.5 · 专家包声明优先）

#### 首选：直接唤起专家包声明的 MCP

```
⚠️ 本次数据查询需要 HR 数据 MCP（hr_data_service_v1）。

WorkBuddy 应会弹出连接窗口，请点「连接」并按提示完成太湖授权（无需招活 Token，也无需手填 Token）。
若没有弹窗：WorkBuddy 左侧「连接器」→ 右上角「自定义连接器」→ hr_data_service_v1 →「连接」/「Trust」。

完成后告诉我「继续」，我接着帮你查。
```

#### 旧客户端兜底：连接器列表没有 hr_data_service_v1 时才手动配置

```json
{
  "mcpServers": {
    "hr_data_service_v1": {
      "url": "https://dos-dataview.mcp.it.woa.com/mcp",
      "protocol": "streamable-http",
      "disabled": false
    }
  }
}
```

保存后再到连接器完成太湖授权。已有 `mcpServers` 时只合并 `hr_data_service_v1`，不要覆盖其他 MCP。

### 1.3 配置完成后的承接规则

用户回复「继续」/「好了」时：
1. 内部回顾用户原始查询意图
2. 重新走本 Skill 流程，**不要**绕过路由直接调 `starrocks_query`

---

## 🚨 §2 数据安全口径（CRITICAL）

### 2.1 PII 默认脱敏

以下字段在结果展示时**默认脱敏**，除非用户明确要求并明确风险：
- 手机号、邮箱、身份证号、银行卡号、护照号
- 详细家庭住址、紧急联系人电话
- 银行卡详细信息

### 2.2 敏感字段提示

以下字段查询前必须**主动提示用户**该字段需对应权限，可能因权限不足返回脱敏值：
- 薪酬相关
- 近期绩效结果（如用户非当事人/非授权管理者）
- 9 宫格 / 梯队评估结果
- 银行卡 / 身份证 / 户籍

### 2.3 脱敏值识别（保守判别 · v5.1 修正）

> ⚠️ 不要看到 `0` / `null` 就判脱敏——`司龄=0` 表示新入职、`下属人数=0` 表示非管理者，都是真值。错误判别会把用户引向无意义的权限排查。

仅在以下**强信号**同时满足时，才提示用户「可能因权限不足被脱敏」：

**强信号 A · 字段语义不应为该值**：
- 字符串字段（如部门名、员工姓名、组织全路径）恒为 `*` / `***` / `脱敏` / 单个 `-` / 空字符串
- 日期字段（如入职日期、合同开始日期）恒为 `1970-01-01` / `1900-01-01` / `0000-00-00`
- 身份证 / 手机 / 邮箱字段格式异常（如全为 `0` 或单字符填充）

**强信号 B · 整体异常**：
- 同一查询返回的多条记录，多个本应不同的字段都呈现相同的占位值
- 查询条件命中明确的人/组织，但返回结果远少于预期（如「查 1000 人部门员工」只返回 5 条）

**仅出现以下"弱信号"时，不要主动判脱敏，结果照常展示**：
- 单个数值字段为 0（可能就是真值）
- 个别字段 NULL（可能就是没填）

发现强信号 → **不要直接切到 §3.3**，而是在结果末尾**提示用户**：

> ℹ️ 我注意到结果里 XX 字段呈现脱敏特征（举例值: `***`）。可能是数据权限限制。需要我帮你排查权限范围吗？回复「是」即走权限排查流程。

由用户决定是否排查，**不替用户做决定**。

### 2.4 跨人查询提醒

用户查"非自己"或"非自己直接管理范围"的员工信息时，结果可能因数据权限受限。结果展示前提醒：
> ℹ️ 注：HR 数仓查询受行权限控制，你只能看到自己有授权范围的员工。如果结果与预期不符，可以让我帮你查一下你对该表的权限范围。

---

## §3 子流程路由（按 args 调用）

| args | 场景 | 调用链 |
|---|---|---|
| `Q`（默认） | 明细、自由统计或无预置指标命中的查询 | hr-data-sql-builder → MCP `starrocks_query` → 渲染 |
| `I` | 通用 HR 预置指标、上级组织对比 | indicator-query → MCP `indicator_query` → 渲染；无匹配/无权限时降级 Q |
| `P` | 数据看不到 / 字段被脱敏 / 权限排查 | data-table-permission-checker → MCP `get_current_user_data_permission` |
| `F-api` | 给前端项目生成调数仓 HTTP 接口的代码 | data-warehouse-api-codegen |
| `F-indicator-api` | 给前端项目生成调预置指标 HTTP 接口的代码 | indicator-query → indicator-api-codegen |
| `F-vue` | 给前端 Vue 项目接入 HR 业务组件（员工/组织/岗位选择器等） | hr-vue-next |
| `F-page` | 指标/SQL 取数能力与 F-vue 联动，做一个完整页面 | 对应 API codegen + hr-vue-next |

> 用户没指定 args 时，按用户问题判别：
> - 通用离职率、流入/流出率、结构占比、平均年龄/工龄/司龄、上级组织对比 → I
> - 明细、列表、自由统计或无指标命中 → Q
> - 含"看不到 / 被脱敏 / 没数据 / 为什么 0 / 权限" → P
> - 含"前端 / 接口 / 调用 / 代码 / 页面 / Vue / 组件" → 按数据源进入 F-api / F-indicator-api / F-vue / F-page
> - 仍不明 → 反问

---

## §3.1 流程 Q · 直接查数据（核心流程）

### 步骤

#### Q-0 · 意图理解
- 解析用户问题：核心查询对象（员工 / 组织 / 合同 / 调动…）+ 限定条件（部门、时间、状态…）+ 期望输出（数量 / 列表 / 分布 / 趋势）
- 如果关键限定缺失（例：用户说"查员工信息"但没说哪个部门），**反问 1 句最关键的问题**，不要硬猜
- 在生成 SQL 前执行一次口径分流：
  1. 社招简历、面试、Offer、入职、需求等招聘过程 KPI → 返回一级 Agent，改走 `recruit-data-dashboard`；
  2. 通用 HR 预置指标或上级组织对比 → 转流程 I；
  3. 明细、自由统计、趋势、预置指标未命中，或用户明确要求 SQL → 继续 Q。

#### Q-1 · 调 hr-data-sql-builder
通过 `use_skill("hr-data-sql-builder")` 加载子 skill，由它：
1. 从 `starrocks://tables` resource 拉表清单 → 选最合适的宽表
2. 从 `starrocks://tables/{table_code}` resource 拉字段列表
3. 必要时从 `starrocks://slangs` 校准业务术语
4. 生成符合 StarRocks 语法的 SELECT 语句（带 LIMIT，禁权限类 WHERE）

⚠️ 子 skill 返回 SQL 后，**先把 SQL 给用户看**（折叠/简短描述均可），让用户对查询逻辑有感知。

#### Q-2 · 执行查询
调 MCP 工具 `starrocks_query`，参数：
- `sql`（必填）：上一步生成的 SELECT
- `userQuestion`（必填）：原始自然语言问题，用于审计

#### Q-3 · 结果处理与脱敏判别（保守原则）
- 应用 §2.1 的 PII 脱敏（手机/邮箱/身份证默认 `***`）
- 按 §2.3 的**强信号**判别脱敏；只有强信号成立时，在结果末尾**提示用户**是否要走权限排查（**禁止**自动切到流程 P）
- 弱信号（单个 0、个别 NULL）不要提示，避免误导
- 如果查询返回 0 条结果但条件看上去合理，提示用户："该条件下无数据，可能是 ① 真无数据 ② 行权限限制看不到，需要排查权限请回复「排查权限」"

#### Q-4 · 结果呈现
**统一格式：先结论，后明细。**

```
✅ 查询结果

📊 结论：A 部门当前在职 1234 人，其中专家级（T11+）占 12%。

📋 明细（前 20 条）：
| 员工ID | 中文名 | 组织 | 专业职级 | 司龄 |
|---|---|---|---|---|
| ... | ... | ... | ... | ... |

🔧 SQL（参考）：
SELECT staff_id, staff_name_cn, ...
FROM Report_Wide_Public_Staff_Info
WHERE ...
LIMIT 1000;

💡 下一步建议：
- /数据查询 进一步看「按司龄分布」
- /权限排查 如果发现字段异常
```

---

## §3.2 流程 I · 通用 HR 预置指标

### 触发条件
- 离职率、流入率、流出率、人员各维度占比、平均年龄、平均工龄、平均司龄等已封装口径；
- 用户明确要求与上级线/BG 对比，table/SQL 行权限可能不足；
- 不包含社招简历、面试、Offer、入职、需求等招聘过程 KPI，后者必须走 `recruit-data-dashboard`。

### 步骤
1. 通过 `use_skill("indicator-query")` 加载子 skill；
2. 从 `data-view://indicators` 实时匹配指标并读取参数定义，从 `data-view://dimensions` 解析组织和维度值；
3. 调 MCP `indicator_query`，按子 skill 的权限字段校验结果；
4. 成功则按脱敏规则展示指标口径、数值和对比；
5. 无指标匹配、指标簇均无权限或重试失败时，自动降级到 Q，并明确标注“以下为 SQL 现场统计口径”。

> 不要因为用户只说了“率/占比”就强行命中指标；以 `data-view://indicators` 实时返回为准。

---

## §3.3 流程 P · 权限排查

### 触发条件（用户显式触发，禁止 agent 自作主张切入）
- 用户在 Q 流程结果后**回复「是」/「排查权限」/「为什么看不到」**等明确指令
- 用户主动询问"我能看哪些表 / 我对 XX 表有什么权限 / 为什么这个字段查不到 / 我应该看到的数据为啥少"

### 步骤
1. 通过 `use_skill("data-table-permission-checker")` 加载子 skill
2. 由子 skill 调 MCP 工具 `get_current_user_data_permission`，参数 `tableCode`
3. 解读返回的权限 JSON：行权限范围（哪些组织 / 员工类型）、列权限明细（哪些字段被脱敏）
4. 用人话告诉用户："你对 XX 表的行权限是 XX 范围，列 XX/YY 已被脱敏（原因：XX）"
5. 给出建议：是申请扩权、改用其他表、还是接受脱敏继续

---

## §3.4 流程 F-api · 前端调数仓接口代码

### 触发条件
- 用户要求"在前端页面调数仓 / 给我生成一段调用代码 / 我要写个查员工的页面"
- 用户的项目是 Web 前端（Vue / React 等），**不是后端服务**

### 关键约束
⚠️ **数仓接口（`https://dos-dataview-mcp.woa.com/api/query`）只能在浏览器端调用**，因为依赖用户 SSO Cookie。任何后端环境（Node.js / Python / Go / Java 服务）调用都会因缺失身份信息而失败/被脱敏。

如果用户场景是后端服务调用 → **拒绝并解释**，建议用户走"用户 → 浏览器 → 数仓"链路，或申请其他服务端 API。

### 步骤
1. 通过 `use_skill("data-warehouse-api-codegen")` 加载子 skill
2. 让子 skill 按用户技术栈（fetch / axios / Vue Composition API 等）生成代码
3. 关键检查点：
   - `credentials: 'include'` 必须存在
   - SQL 走 SELECT 且带 LIMIT
   - 错误处理覆盖 401（未登录）/ 403（权限不足）/ 500（SQL 语法）

---

## §3.5 流程 F-indicator-api · 前端调预置指标接口代码

### 触发条件
- 用户明确要在浏览器前端调用离职率、结构占比、平均年龄等预置指标接口；
- 不是普通指标查询，也不是 Node.js / Python / Go / Java 等后端服务调用。

### 步骤
1. 先通过 `indicator-query` 从 MCP 实时确定 `apiCode`、参数定义和请求参数；
2. 再通过 `use_skill("indicator-api-codegen")` 生成对应技术栈代码；
3. 检查 `credentials: 'include'` / `withCredentials: true`、禁止传 `staffId`、覆盖 401/403/500；
4. 后端调用直接拒绝，并解释 SSO Cookie 只存在于浏览器链路。

---

## §3.6 流程 F-vue · HR 业务组件库

### 触发条件
- 用户要在 Vue 项目里"快速接入员工选择器 / 组织选择器 / 岗位选择器"等 HR 标准组件
- 用户问"hr-vue-next 怎么用"

### 步骤
1. 通过 `use_skill("hr-vue-next")` 加载子 skill
2. 子 skill 提供 UMD / npm 两种引入方式 + 典型组件用法
3. 关键提醒：组件依赖 TDesign + Vue 3.x，需确认用户技术栈匹配

---

## §3.7 流程 F-page · 完整页面方案

当用户想做"一个能查员工的完整页面"时，串行调用：
1. F-vue 引入员工/组织选择器组件做查询表单
2. 按数据源选择 F-api（SQL）或 F-indicator-api（预置指标），生成结果展示区的数据请求代码
3. 提供完整的页面骨架代码，把两者拼起来

---

## §4 错误兜底

| 异常 | 处理 |
|---|---|
| MCP 不可用 | 走 §1.2 引导 |
| `starrocks_query` 返回 SQL 语法错 | 把错误回喂给 hr-data-sql-builder 让它修正，最多 2 轮 |
| `indicator_query` 无匹配/无权限/重试失败 | 降级流程 Q，并标明使用 SQL 现场统计口径 |
| 行权限完全为空（用户连自己都查不到） | 引导用户走流程 P 排查 |
| 用户问的字段在所有表里都找不到 | 明确说"该字段不在 HR 数仓覆盖范围"，**不要编造表名/字段名** |
| 用户问的是招聘实时业务动作或制度 | 立即返回 agent，由 agent 路由到对应招聘 skill；招聘历史数据分析仍由本 Skill 处理 |

---

## §5 输出风格

- 中文为主；用户用英文则切英文
- **先结论后明细**：永远先给用户最关心的那个数字 / 那句话
- Q 流程总是给出 SQL（折叠或代码块）供审计；I 流程给出指标名称、口径和参数摘要，不伪造 SQL
- 表格数据 ≤ 20 行直接展示，> 20 行只展示前 20 + 提供"查看全部"建议
- PII 字段统一用 `***` 脱敏
- 每次回复末尾给"下一步"建议（继续查 / 排查权限 / 生成前端代码）
- 严格反编造：不知道的字段或表名直接说"数仓未覆盖"，不要瞎写

---

## §5.5 末尾推荐贴片（v5.8 新增 · 由 agent §9.1 定时化推荐协议驱动 · 仅适用招聘漏斗 / 合同到期）

> **触发条件**：用户跑完**招聘漏斗类**或**合同到期类**查询，且输出已完整给到用户后；满足 `automation-recommend-protocol.md` §B 全部不打扰条件。
> **不适用**：员工花名册 / 组织架构 / 单点员工 / 临时性查询（这类是事件驱动，不该定时化）

### 适用判定（按查询主题路由）

| 查询主题（用户输入关键词识别） | 推荐模板 | 频率 |
|---|---|---|
| "招聘漏斗 / 转化率 / 渠道效果 / 渠道 ROI / 学校分布 / 录用结构" | `monthly-recruit-funnel-report` | 每月 1 号 9:00 |
| "合同到期 / 续签 / 即将到期 / 过期合同" | `monthly-contract-expiry` | 每月 1 号 9:00 |

### 标准贴片文案（按命中模板）

#### 漏斗类查询完毕

```markdown
─────────────────────
⏰ **想每月自动看上月招聘漏斗？**

  · 推荐模板：`monthly-recruit-funnel-report`（每月 1 号 9:00 自动跑）
  · 一键开启：直接说「设个漏斗月报定时」
  · 想自定义频率/时间：说「我要自定义」
  · 不需要：说「不用了」（本会话不再问）
```

#### 合同到期查询完毕

```markdown
─────────────────────
⏰ **想每月自动收合同续签预警？**

  · 推荐模板：`monthly-contract-expiry`（每月 1 号 9:00 自动跑）
  · 一键开启：直接说「设个合同到期定时」
  · 想自定义频率/时间：说「我要自定义」
  · 不需要：说「不用了」（本会话不再问）
```

### 老用户精简版

```markdown
> ⏰ 提示：可设为定时任务（推荐 `<对应模板ID>`，每月 1 号 9:00）—— 说「设个 XX 定时」即可。
```

### 不追加情况

- 用户本会话已被推过 1 次本能力推荐
- `automation_update view` 已存在对应模板任务
- user-prefs 里 `disable_recommend_global=true` 或包含 `hr-data-router.funnel` / `hr-data-router.contract`
- 查询结果含错误 / 0 行（不要在失败时还推荐定时化）

详见 `agents/recruitment-expert.md` §9.1 与 `agents/references/automation-recommend-protocol.md`。

---

## §6 与上游同步

被本 router 编排的数据子 skill 采用 `hr-digital-expert@1.0.6` 的最新命名与指标能力，并保留招聘专家已有的按需安全约束：
- `hr-data-sql-builder` ← `hr-digital-expert` 选择性同步
- `data-table-permission-checker` ← `hr-digital-expert` 选择性同步
- `indicator-query` ← `hr-digital-expert` 选择性同步并修正动态组织解析
- `indicator-api-codegen` ← `hr-digital-expert` 选择性同步并收紧为内部工具
- `data-warehouse-api-codegen` ← 复用招聘专家已加固版本，MCP 名称同步为 `hr_data_service_v1`
- `hr-vue-next` ← `page-design` 插件

每个子 skill 的 SKILL.md 顶部 frontmatter 标了 `synced-at` 字段。如果上游有重要更新，参考 `references/sync-guide.md`（按需补齐）。
