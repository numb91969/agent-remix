# 数据域路由

> 只在一级 Agent 已判定为数据域后读取。任何真实数字必须来自数仓/MCP 返回；数据域规则位于 `../data-rules/`，由命中的 Skill 按需加载。

## 0. 🔴 数据域默认入口铁律（先读这条，再看能力表）

**用户约定（2026-08-26）：数据域的一切「要数」请求，默认第一站是 `recruit-data-dashboard`。**

除下面「§0.2 直接绕过」列举的情况外，任何数据请求都必须按以下顺序执行，**不得跳步、不得凭语感直接落到 `hr-data-router`**：

```text
Step A  use_skill("recruit-data-dashboard")
        └─ 在其 44 指标治理库内做一次真实命中判断
             （读倒排索引 knowledge/_audit/metrics-search-index.json，
               或跑 scripts/search_metric.py，不靠记忆猜）
Step B  命中 → 就地用治理口径查完、交付，流程结束
Step C  未命中 → 先向用户明确告知，再转 hr-data-router
```

### 0.1 未命中时的强制告知（不可省略）

未命中**不允许静默切换数据源**。必须先给用户一句显式说明，再进入 `hr-data-router`：

> 「这个口径不在社招治理指标库（44 指标）内，我改走 HR 数仓通用查询（`hr-data-router`），结果为现场口径、非治理级，引用到汇报前建议先跟我确认口径。」

告知后**直接继续执行，不要停下来等用户点头**——用户已授权自动 fallback。但交付时必须在口径块里标注 `口径来源：数仓自由查询（非 44 治理指标）`。

已知的高频未命中类型（出现这些直接判 Step C，无需在 dashboard 里反复试探）：

| 未命中类型 | 原因 | 落点 |
|---|---|---|
| **环节粒度**（`step_name` 级，如「HR初筛人数」「面委会安排人数」）| 治理库是汇总时点口径（评估中/面试中/offer中），**不含 `step_name` 拆解** | `hr-data-router · Q` |
| **活水专项**（只看 `flow_id = 5`，不含社招）| 治理库把活水作为「含活水」合并分支，无活水独立指标 | `hr-data-router · Q` |
| 校招指标 | 治理库仅覆盖社招 | `hr-data-router · Q` |
| 员工、组织、编制、合同、调动、职级、司龄、学历 | 非招聘过程指标 | `hr-data-router · Q` / `· I` |
| 离职率、流入/流出率、结构占比、平均年龄/工龄/司龄 | 属通用 HR 预置指标 | `hr-data-router · I` |
| offer 薪资金额/分位、拒因分布、渠道来源明细、候选人画像 | 治理库确实没有该维度 | 先说明缺口，再判断数仓有无 |

### 0.2 允许绕过 dashboard 直接进入的例外

只有以下四类**不需要**先过 dashboard：

1. **精确入口信号**——用户敲了 `/HR数据` `/HR SQL` `/数据权限` `/数仓前端代码` `/HR组件`，或显式点名某个 skill；
2. **纯前端/代码类**——只要取数代码、Vue 组件、看板页面，不要具体数字（`F-api` / `F-indicator-api` / `F-vue` / `F-page`）；
3. **权限排查**——数据是 `*`、异常 0、1970 日期这类明显的权限/脱敏症状（`· P`）；
4. **上一轮已确认走 hr-data-router 的同主题追问**——同一口径的连续追问不必每轮重新过 dashboard。

⚠️ 「用户没说社招」不是绕过理由。中性说法（「查一下这个部门招了多少人」）仍然先过 dashboard。

## 1. 能力表

> 阅读顺序即优先级。第一行是默认入口。

| 用户目标 | Skill / Flow |
|---|---|
| **🥇 默认第一站：任何「要数」请求，先在此判断是否命中 44 治理指标** | **`recruit-data-dashboard`** |
| 社招简历/面试/Offer/入职/需求/漏斗/归因的治理级口径 | `recruit-data-dashboard` |
| ↓ 以下均为 dashboard 未命中后的落点（须先完成 §0.1 告知）↓ | — |
| 明细、自由统计、趋势、环节粒度、活水专项、校招或指标库外查询 | `hr-data-router · Q` |
| 离职率、流入/流出率、人员结构占比、平均年龄/工龄/司龄、上级组织对比 | `hr-data-router · I` / 内部 `indicator-query` |
| 数据为 `*`、异常 0、1970 日期或查不到权限 | `hr-data-router · P` / `data-table-permission-checker` |
| 明确要 StarRocks SQL | `hr-data-sql-builder` |
| 前端调用数仓 HTTP 接口的代码 | `hr-data-router · F-api` / `data-warehouse-api-codegen` |
| 前端调用预置指标 HTTP 接口的代码 | `hr-data-router · F-indicator-api` / 内部 `indicator-api-codegen` |
| Vue HR 业务组件 | `hr-data-router · F-vue` / `hr-vue-next` |
| 完整前端 HR 数据页面 | `hr-data-router · F-page` |

### 🔴 上表右列出现两个选项时怎么选

`data-table-permission-checker` / `hr-data-sql-builder` / `data-warehouse-api-codegen` / `hr-vue-next` 在注册表里是 **`entry_type: command_only`** 的工具 skill；`indicator-query` / `indicator-api-codegen` 是 **`entry_type: internal_only`**：

- **默认走 `hr-data-router` 的对应 Flow**（`· P` / `· F-api` / `· F-vue`），由它内部调用工具 skill；
- **仅当请求带精确入口信号**——用户敲了 `/数据权限` `/HR SQL` `/数仓前端代码` `/HR组件`，或明确点名该 skill——才直达工具 skill。
- 两个 indicator 工具没有一级语义直达入口，始终由 `hr-data-router` 判断数据源后调用。

判据是**有没有精确入口信号**，不是话术里出现了 SQL/权限/组件这些词。「帮我看下部门招聘数据为啥是 0」是模糊请求，走 `hr-data-router · P`，不要直接跳 `data-table-permission-checker`。

## 2. 数据路径优先级

严格按以下顺序，**不因为只出现「率/占比/明细」就抢路由**：

### 第 1 优先：`recruit-data-dashboard`（默认，无条件先过）

触发条件不是「用户明确说了社招看板」，而是**只要属于数据域的要数请求**就先过一遍。判断在 skill 内部用倒排索引做，不在路由阶段凭语感预判。

典型必走：社招看板、社招漏斗、Offer 接受率、入职、在招需求、面试中/评估中/offer中人数、需求完成率、各环节通过率，以及任何**中性说法**的招聘数量问题（「这个部门招了多少人」「今年进展怎么样」）。

### 第 2 优先：`hr-data-router · I`（dashboard 未命中 + 属通用 HR 预置指标）

- 离职率、流入/流出率、人员各维度占比、平均年龄/工龄/司龄；
- 需要上级线/BG 对比，且 indicator 资源实时存在匹配指标；
- 指标无匹配或无权限时自动降级 Q，不循环回指标路径。

### 第 3 优先：`hr-data-router · Q`（dashboard 未命中 + 指标库也没有）

- 环节粒度（`step_name`）、活水专项（`flow_id = 5`）等治理库不拆的切法；
- 员工、组织、合同、调动、编制、职级、司龄、学历等基础 HR 数据；
- 校招或跨招聘类型历史统计；
- 探索式、多表或指标库未覆盖的查询。

### 反问策略

- **已命中 44 指标** → 直接查，不额外追问口径路径；
- **dashboard 未命中** → 按 §0.1 告知后直接转 `hr-data-router`，**不停下来问**（用户已授权自动 fallback）；
- **只有用户目标确实不清楚**（例如「看看招聘情况」无法判断实时进度还是历史分析）才用 `progress_source` 歧义组反问一次。

## 3. 归因请求

用户问“为什么下降/哪个渠道拖累/哪类人群导致”时：

1. 先查询真实总量和可用分组；
2. 只使用指标库或数仓真实存在的维度；
3. 区分相关性、结构贡献和因果，不把相关性写成原因；
4. 数据不支持归因时明确说只能描述现象；
5. 不编造百分比，不用训练记忆补口径。

## 4. 实时态不是数据域

- 某候选人卡在哪一步 → 搜索域 `recruitment-process-tracker`；
- 我的面试待办/校招事项 → 面试域 `interview-assistant`；
- 测验场次当前状态 → 面试域 `quiz-deliverable-evaluator`；
- 竞对团队人数/人才分布 → 搜索域 `mapping`；
- 伯乐奖金、活水条件等制度算法 → `recruitment-inquiry-bot`。

判据不是用户是否问“多少”，而是数据来自实时业务接口、数仓沉淀还是外部公开信息。

## 5. 必要规则与依赖

| 场景 | 必须加载 |
|---|---|
| SQL 生成/审查 | `../data-rules/hr-starrocks-query-conventions.md` |
| 查询结果分析 | `../data-rules/hr-data-desensitization.md` |
| 前端 SQL / 指标接口代码 | `../data-rules/hr-datawarehouse-api-constraint.md` |

真实查询依赖 `hr_data_service_v1`。探活失败时按 Skill 接入引导处理，不编数、不回退为训练记忆。

## 6. 🔴 禁止绕过 Skill 直接调 MCP

**读 SKILL.md 当参考资料 ≠ 进入了该 Skill。** 数据域最容易犯的错是「读了几个 SKILL.md / 指标卡 → 自己拼 SQL → 直接调 `mcp__hr_data_service_v1__starrocks_query`」，跳过整个 Skill 层。这条**明确禁止**。

| ❌ 禁止 | ✅ 正确 |
|---|---|
| 直接调 `starrocks_query`，没先 `use_skill` | 先 `use_skill("recruit-data-dashboard")`，未命中再 `use_skill("hr-data-router")`，由 Skill 内部发起查询 |
| 只 `Read` 了 SKILL.md 就自认为「已经走了这个 skill」 | `use_skill` 是唯一的进入方式（也是 skill 调用量上报的触发点）|
| 因为「这个查询很简单」而抄近路 | 查询简单不是理由；口径一致性、治理口径校验、`FIRST ACTION` 埋点都在 Skill 内 |

**自检**（每次要动 `starrocks_query` 前问自己一句）：

> 我这一轮有没有真的 `use_skill` 过 `recruit-data-dashboard`？如果未命中，有没有按 §0.1 告知用户后再 `use_skill("hr-data-router")`？

两个都答不上 → 停下来，回到 Step A 重走。

> 副作用提醒：绕过 Skill 会让两个 skill 的 `FIRST ACTION` 埋点全部丢失，看板上调用量记 0，等于这次查询在统计上从未发生。
