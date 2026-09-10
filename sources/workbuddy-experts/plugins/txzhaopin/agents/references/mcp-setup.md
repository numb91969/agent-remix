# 腾讯招聘专家 MCP 自检 + 连接引导 · mcp-setup

> **统一架构（2026-08-04）**：专家包声明两个 MCP。大部分招聘功能依赖 `recruit-mcp`；数据查询依赖 `hr_data_service_v1`。两者均由 WorkBuddy 在首次进入对应能力时直接唤起连接并完成太湖授权，**都不需要招活 Token**。
>
> | MCP | 能力范围 | 地址 |
> |---|---|---|
> | `recruit-mcp` | 待办、简历搜索、面试安排、面评、招聘问询、外呼、测验等大部分招聘功能 | `https://zhaopin.mcp.it.woa.com` |
> | `hr_data_service_v1` | HR 基础数据、招聘历史分析、社招指标驾驶舱等数据查询功能 | `https://dos-dataview.mcp.it.woa.com/mcp` |
>
> **用途**：完成业务路由后的 MCP 探活、依赖矩阵、失败时的连接引导。
> **加载时机**：① 已命中的 Skill 需要 MCP ② `mcp-capability-explorer` 被触发 ③ MCP 调用失败需要引导用户连接时。**非常驻**——纯方法论请求不探活，当前会话已确认 MCP 接通后无需重复 Read。
> **白名单例外**：用户问的是 §依赖矩阵里标 🟢 的事（建模/JD/出题/审核/面评清洗/岗位建模），**跳过自检**直接进 skill，不用读本文件。

---

## §0 招聘链路 MCP 自检（CRITICAL — 路由到 MCP 依赖后再做）

招聘业务的所有数据请求（待办 / 面试安排 / 简历搜索 / 简历详情 / 知识库检索 / 面评提交等）都依赖 **`recruit-mcp`**。

用户进入任何 MCP 依赖场景前，**必须先做一次 MCP 探活**。失败时直接进入“安装引导”，**不要**进入正式 Skill 执行，也不要把连接失败误报成“知识库未收录”或“系统没有能力”。

### MCP 依赖矩阵

| Skill / 场景 | 是否依赖 MCP | 失败时行为 |
|---|---|---|
| `recruitment-inquiry-bot`（招聘智能问询） | 🔴 强依赖 | 必须 MCP 才能检索知识库 |
| `zhaopin-operations`（校招搜简历） | 🔴 强依赖 | 必须 MCP 调 `post_v1_resume_search` |
| `zhaopin-social-operations`（社招搜简历） | 🔴 强依赖 | 必须 MCP 调社招搜索 API |
| `interview-assistant · T/T2`（待办） | 🔴 强依赖 | 必须 MCP 拉本人待办（v4.5 起 T 默认同时查校招 + 社招两类待办） |
| `interview-assistant · S`（面试安排） | 🔴 强依赖 | 必须 MCP 调度 |
| `interview-assistant · A`（按 RID 拉简历详情） | 🔴 强依赖 | 必须 MCP |
| `interview-assistant · D`（面评填写/转写） | 🔴 强依赖 | 必须 MCP |
| `interview-assistant · B`（评简历） | 🟡 部分依赖 | 候选人主数据需 MCP；本地材料兜底可跑 |
| `interview-assistant · C`（出题/面试计划） | 🟡 部分依赖 | 候选人主数据需 MCP；本地材料兜底可跑 |
| `requirement-communication-assistant`（需求沟通链路） | 🟡 部分依赖 | 模型/词典走 MCP 文档接口；拉取失败静默降级走本地兜底，链路不中断 |
| `mcp-capability-explorer`（内部 fallback） | 🔴 强依赖 | 仅在 Skill 部分覆盖或无覆盖时，搜索当前用户可见能力；连接失败须返回连接问题，不得判定为不支持 |
| `assessment-quality-expert`（建模/JD/出题/审核） | 🟢 不依赖 | 纯方法论本地可跑 |
| `interview-data-processor`（面评清洗） | 🟢 不依赖 | 本地 Excel 处理 |
| `interview-talent-modeler`（岗位建模） | 🟢 不依赖 | 本地脚本 |

### 探活方法（任一可用即视为接通）

1. 检查当前会话是否暴露了 `mcp__recruit-mcp__*` 工具（最直观）
2. 或 Read `~/.workbuddy/mcp.json`，看 `mcpServers` 里是否有未 disabled 的 `recruit-mcp` 段（含 `url: https://zhaopin.mcp.it.woa.com`）

### 权限范围内的运行时发现

- 专家包不保存、不加载也不向用户展示 recruit-mcp 的全量能力目录。
- 现有业务 Skill 完整覆盖时，按该 Skill 的固定流程执行，不启动通用探索。
- Skill 部分覆盖或无覆盖时，只有内部 `mcp-capability-explorer` 可以调用 `SearchAPI` 做窄查询；服务端返回结果已经按当前用户权限过滤。
- 搜索结果只能作为候选，必须再通过 `SearchAPI(apiId=...)` 获取当前 Schema，之后才能进入读写策略门。
- MCP 权限代表“当前用户具备访问资格”，不代表“用户已确认本次副作用操作”；写操作仍按受控写契约处理。

### 失败时的接入引导（WorkBuddy 口径 · 一键弹窗连接优先）

> 🆕 **recruit-mcp 已支持一键弹窗连接**：地址 `https://zhaopin.mcp.it.woa.com`，连接时**只需太湖 SSO 授权**，**不再需要单独申请「招活 Token」**。绝大多数情况引导用户走「方式 A 弹窗连接」即可。

当探活失败时，**不要进入任何 MCP 依赖 skill**。专家包已经声明该 MCP，先直接触发连接并按下面顺序引导；不要先要求用户安装、申请 Token 或手写配置。

**方式 A · 专家包一键唤起连接（首选，最简单）**

```
⚠️ 招聘 MCP（recruit-mcp）还没连上，本次请求需要它（场景：xxx）。

连接很简单，只要一步：
① WorkBuddy 会弹出「是否连接 recruit-mcp（https://zhaopin.mcp.it.woa.com）」窗口 → 点「连接」
② 按提示用太湖 SSO 授权即可（无需手填任何 Token）

如果没弹窗，去 WorkBuddy 左侧「连接器」→ 右上角「自定义连接器」→ 找到 recruit-mcp → 点「连接」/「Trust」。

连好后告诉我「继续」。
```

**方式 B · 手动写配置（仅当客户端不支持弹窗连接时）**

```
打开 ~/.workbuddy/mcp.json，把以下段加进 mcpServers 字段：

{
    "mcpServers": {
        "recruit-mcp": {
            "url": "https://zhaopin.mcp.it.woa.com",
            "headers": {
                "Authorization": "Bearer <太湖PAT>"
            },
            "disabled": false
        }
    }
}

- 太湖 PAT 申请：https://tai.it.woa.com/user/pat（Authorization 必须带 "Bearer " 前缀）
- ⚠️ 已有 mcpServers 字段时只合并 "recruit-mcp" 这个键，不要覆盖你已有的 MCP（如 hr_data_service_v1）
- 保存后到「连接器」→「自定义连接器」→ recruit-mcp → 点「连接」/「Trust」

完成后告诉我「继续」。
```

**安全提醒**：太湖 PAT 不要贴在对话里 / 提交 Git / 截图外发；mcp.json 仅存本地（权限建议 0o600）；泄漏立刻到 https://tai.it.woa.com/user/pat 吊销重申。

> 💡 **不再需要「招活 Token / recruit-Authorization」**：旧版要求的第二个 token 已下线，连接只认太湖授权。若在旧文档/旧配置里看到 `recruit-Authorization` / `ZHAOPIN_TOKEN`，可忽略或删除。

**你可以先做的（不依赖 MCP，立刻可用）**：列出 §依赖矩阵中标 🟢 的 skill，让用户在等接入时也能继续工作。

---

## campus-mcp（校招调研数据后端）按需接入引导 · 官方一键生成配置

> 📌 **命名说明**：本文档统一把这个后端称为 **`campus-mcp`**，以便与 skill `employer-brand-rita`（Rita 本人）区分——
> 一个是数据后端，一个是执行 skill，同名会看错。
> **官方页面默认生成的 server 名是 `rita`**；用户粘贴时可以保留原名，也可以改成 `campus-mcp`，**两者都能正常工作**
> （Rita 调工具用裸工具名，不依赖 server 名前缀）。判断是否接通**一律看会话工具列表**，不要按 server 名判断。

> 🔴 **本 MCP 不在本包声明中（有意为之）**：它只服务 1 个 skill 的一半能力，
> 若写进 `.mcp.json` 会让**全部 30 个 skill 的用户**在每次会话开场都被提示连接一个与自己无关的东西。
> 因此改为**按需引导**：只有当用户真的提出 Rita 数据类请求时，才给下面的话术。
>
> ⚠️ **与 recruit-mcp / hr_data_service_v1 的区别**：那两个已在包内声明、走 **SSO 授权**（弹窗点一下即可）；
> `campus-mcp` **没有弹窗可点**，需用户到官方页面点按钮生成含 API Key 的整段 MCP 配置，自行粘贴到 WorkBuddy 的 MCP 配置里。
> **不要引导用户去找某个输入框手填 Key** —— 本包没有声明该 server，不会出现对应字段。

**谁需要它**：只有 `employer-brand-rita`（雇主品牌调研）的**数据类**请求依赖。
其余 4 个雇主品牌 skill（小鹅 / 小完能 / lulu / Amy）+ Rita 的**方法论类**请求（调研设计 / 问卷框架）**均不依赖 MCP，始终可用**。

> ⚠️ **申请资格：仅限招聘团队**。该后端存的是校招调研原始数据与竞品情报，
> **只对招聘团队开放申请**。引导时**必须前置告知这一点** —— 否则非招聘团队的用户跑一趟才发现申请不通过。
> 非招聘团队用户：直接转方法论降级方案，不必让他去申请。

> 📌 **不要主动推销接入**。用户没提数据类需求时，不要提这个后端的存在 —— 那等于把开场提示换个形式又加回来了。

### 完整引导话术（Rita 数据类请求且 MCP 未接通时，逐字给用户）

```
你要的调研数据在 Rita 调研后端里，这个后端还没接通。

⚠️ 先说明：这个后端仅限「招聘团队」申请使用。
   如果你不在招聘团队，申请可能不会通过 —— 那我就按方法论帮你出方案，
   不引用历史调研数据（下面列了不需要接通也能做的部分）。

招聘团队的同学接通很快，两步：

第 1 步 · 生成配置
打开 https://campus123.woa.com/fofo → 点「已生成配置」按钮
（用你的 OA 登录态直接完成注册与信息获取，不用开新页面、不用审批）
页面下方会直接显示一段拼好的 MCP 配置，里面已经含好你的 API Key。

第 2 步 · 复制粘贴给 WorkBuddy
把那整段配置复制下来，粘进 WorkBuddy 的 MCP 配置里即可。

⚠️ 那段配置里含你的 API Key（明文），属于个人凭据：
   直接粘进配置，别贴到对话里、别截图外发、别提交 Git。

弄好告诉我「好了」，我重新读数据。

等的期间我可以先做（不需要这个后端）：
· 调研方案设计、问卷框架、维度拆解（方法论部分）
· 雇主品牌策划 / 招聘文案 / 物料合规审核 / 舆情研判（这四块本来就不依赖 MCP）
```

### 🔴 引导时必须守的六条

| 约束 | 说明 |
|---|---|
| **先告知「仅限招聘团队申请」** | 放在引导最前面。非招聘团队用户直接转方法论降级，**别让他白跑一趟**才发现申请不通过。 |
| **引导「点按钮生成配置」，别让用户自己拼** | 官方页面会输出完整 JSON（含 url + X-API-Key）。让用户复制整段，**不要**引导他去某个输入框手填 Key —— 那是更麻烦且容易错的路径。 |
| **不要向用户索取 Key / 配置** | 用户自己粘进 WorkBuddy。**绝不能说"把 Key 发给我"或"把配置贴给我看看"**。 |
| **用户若已把 Key 贴进对话 → 立即提示轮换** | 这是**已泄漏**状态。明确告知：回 campus123.woa.com/fofo 重新生成一次（秒级、免审批），旧 Key 作废。**不要把已泄漏的 Key 写进任何文件。** |
| **两步都要给** | 只说"去 campus123 注册"是不完整的 —— 用户会不知道下一步干什么。 |
| **同时给降级选项** | 告知等待期间能做什么，不要让用户干等。 |

### server 名说明（可以随便叫，不影响功能）

官方页面生成的配置里 server 名默认是 **`rita`**。本包**不声明该 server**，
所以用户粘贴什么名字都不会与本包冲突。

**推荐改成 `campus-mcp`**（本文档统一用这个名字）：官方默认的 `rita` 与 skill
`employer-brand-rita` 同名，一个是数据后端、一个是执行 skill，混在一起容易看错。
改名只需把粘贴的配置里那个 key 换掉，**保留 `rita` 也完全能用**。

之所以随便叫都行：Rita 调用工具时用**裸工具名**（`query_research_findings` /
`query_company_benchmark` / `query_bg_intern_presentation` 等），**不依赖 server 名前缀**。

**判断是否已接通**：看当前会话工具列表里有没有 `query_my_research_scope` 之类的 Rita 工具，
**不要按 server 名判断、也不要去查配置文件**（用户可能已经改名）。没有就走下面的引导；有就直接调用。

> 📌 该 Key **仅用于 MCP 认证**，无需手动调用任何 REST API（官方页面明确说明）。

### 权限说明（用户可能追问"我能看到哪些数据"）

Key 绑定的角色决定可读范围（由后端判定，本包无法调整）：
`rita_system_admin` 全部 > `rita_hr_group` 公共+跨 BG 对比 > `rita_bg_manager` 公共+本 BG 同侪调研 > `rita_bg_other_hr` 仅公共 > `rita_public_viewer` 仅 benchmark+方法论。

用户可让 Rita 调 `query_my_research_scope` 查自己的实际范围。
若反馈"查不到某些数据"，先确认是**权限范围**问题而非 Key 失效 —— 详见 `skills/employer-brand-rita/references/MCP接入指南.md`。

### 🔴 接通失败或 Key 无效时

**绝不编造调研数据兜底**（禁满意度百分比 / 竞品对标数字 / 样本量 / NPS）。如实说明状态 + 给方法论降级方案。

### 自检例外（白名单）

如果用户问的就是 §依赖矩阵里 🟢 标识的事（建模 / JD / 出题 / 审核 / 面评清洗 / 岗位建模），**跳过 MCP 自检**，直接进入对应 skill。

雇主品牌域的白名单：小鹅（策划）/ 小完能（文案）/ lulu（审核）/ Amy（舆情）**均 🟢 不依赖 MCP**；只有 Rita 的**数据类**请求需要 `campus-mcp`（Rita 的纯方法论请求也可 🟢 降级执行）。
