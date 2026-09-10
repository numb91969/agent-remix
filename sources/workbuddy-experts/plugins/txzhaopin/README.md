# 腾讯招聘专家 · Tencent Recruitment Expert

> WorkBuddy 招聘 agent — 五层能力架构：① 招聘全流程（校招/社招）② HR 数据查询 ③ **招聘渠道（猎头 / 委外供应商决策）** ④ **雇主品牌（策划 / 文案 / 审核 / 舆情 / 调研）** ⑤ 定时任务调度。覆盖 招聘需求沟通 → 人才搜索 → 简历筛选 → 胜任力建模 / JD / 面试设计 → 面评审核 → 面试数据分析 → 待办查询 → 面试安排 → **招聘流程跟踪** → **校招签约后保温** → 招聘智能问询 → **HR 数仓查询（员工/组织/招聘漏斗等）** → **猎头渠道推荐** → **雇主品牌策划 / 文案 / 物料审核 / 舆情口碑 / 招聘调研** → **定时任务调度**。服务 **招聘经理 / 面试官 / HR / BP / 数据分析 / 品牌经理**。

- **包名**：`txzhaopin`
- **版本**：1.39.0
- **分类**：`09-OperationsHR`
- **运行环境**：WorkBuddy

---

## 目录结构

```
txzhaopin/
├── .codebuddy-plugin/
│   └── plugin.json                              # 插件清单
├── agents/
│   ├── recruitment-expert.md                    # 唯一注册 Agent：安全内核 + 薄路由
│   └── references/                              # 按需加载，不常驻主上下文
│       ├── capability-registry.yaml             # 30 张结构化能力卡（单一来源）
│       ├── route-ambiguities.yaml               # 跨能力消歧组
│       ├── routes/                              # 5 个领域路由参考（非 Agent）
│       ├── schemas/route-decision.schema.json   # 结构化路由决策契约
│       └── data-rules/                          # HR 数据规则单一来源
├── avatars/
│   └── expert.png                               # 头像 512×512
├── skills/                                      # 30 个 skills
│   # —— 招聘业务域（9 个 · 核心）——
│   ├── requirement-communication-assistant/     # 招聘需求沟通：需求识别 → 画像+胜任力 → JD 端到端
│   ├── assessment-quality-expert/               # 甄选方法论 + 质量裁判 + 面试设计中心
│   ├── zhaopin-operations/                      # 校招简历搜索 / 筛选 / 推荐
│   ├── zhaopin-social-operations/               # 社招简历搜索 / 粗读 / 精读
│   ├── interview-assistant/                     # 面试官日常：T 待办 / SI 社招发起 / S 安排 / A 拉简历 / B 评 / C 出题 / D 写面评
│   ├── interview-data-processor/                # 面评 Excel → 标准化 JSON
│   ├── interview-talent-modeler/                # 面评数据 → 岗位能力模型
│   ├── recruitment-inquiry-bot/                 # 招聘智能问询（知识库检索）
│   ├── recruitment-process-tracker/             # 招聘流程跟踪（社招专用 · 招聘经理 case-level 视角）
│   # —— 校招专属应用层 ——
│   ├── warming-recruit-manager/                 # 校招签约后保温工作台（招聘经理日常 SOP）
│   # —— HR 数据副链路（7 个）——
│   ├── hr-data-router/                          # HR 数仓查询统一入口（编排下面 6 个）
│   ├── hr-data-sql-builder/                     # NL2SQL（StarRocks）
│   ├── data-table-permission-checker/           # 表级/行列权限排查
│   ├── indicator-query/                         # 通用 HR 预置指标查询（内部工具）
│   ├── indicator-api-codegen/                   # 预置指标前端接口代码（内部工具）
│   ├── data-warehouse-api-codegen/              # 前端调数仓接口代码生成
│   ├── hr-vue-next/                             # HR 业务组件库（员工/组织/岗位选择器）
│   # —— 社招指标驾驶舱（独立）——
│   ├── recruit-data-dashboard/                  # 社招 44 个治理级指标精准口径查询
│   # —— 人才 Mapping（独立）——
│   ├── mapping/                                 # 竞对人才摸底 / 组织调研 / 候选人画像 / 寻访报告
│   # —— AI 外呼（独立）——
│   ├── recruiting-ai-outbound-call/             # AI 电话外呼候选人确认岗位意向（v1 仅社招）
│   # —— 测验平台（独立）——
│   ├── quiz-deliverable-evaluator/              # 测验平台：阅卷待办辅助阅卷 / 成绩单自定义重评 / 成绩单导出
│   # —— 横切能力 ——
│   ├── daily-routine-builder/                   # 把"每天/每周自动跑"翻译为 automation_update 调度
│   ├── hrclaw-messenger/                        # HRClaw 邮件 + 企微 Tips 通用发送通道（被其他 skill 调用）
│   └── mcp-capability-explorer/                 # 用户权限范围内的 recruit-mcp 动态能力发现（内部 fallback）
└── README.md                                    # 本文件
```

---

## 30 个技能（skills）

### 🎯 招聘业务域（9 个 · 核心）

| Skill | 作用 | 典型触发 |
|---|---|---|
| **requirement-communication-assistant** | 招聘需求沟通三段式链路：需求识别 → 人才画像 + 胜任力模型 → 可发布 JD | `/需求沟通` "我有一个招聘需求" "新开了一个 HC" |
| **assessment-quality-expert** | 甄选方法论 + 质量裁判 + 面试设计中心（建模 / 出题 / 审题 / 审面评 / 测评方案 / AI 防作弊；**JD 仅限「基于已有胜任力模型派生」**，从零写 JD 走 `requirement-communication-assistant`） | `/搭模型` `/出套题` `/审面评` |
| **zhaopin-operations** | 腾讯校招平台简历搜索 / 筛选 / 推荐（recruit-mcp 直连） | `/搜简历` "校招搜索" |
| **zhaopin-social-operations** | 腾讯社招平台简历搜索 / 粗读 / 精读 / 收藏 | `/社招搜索` "社招简历" |
| **interview-assistant** | 面试官日常工具入口（T 待办 / SI 社招发起面试 / S 面试安排 / A 拉简历 / B 评 / C 出题 / D 写面评） | `/待办` `发起社招面试` `/面试安排` `/评简历` `/面试计划` `/填面评` |
| **interview-data-processor** | 面评 Excel / CSV → 标准化 JSON | `/清洗面评` |
| **interview-talent-modeler** | 清洗后面评数据 → 按部门生成岗位能力模型 | `/建岗位模型` |
| **recruitment-inquiry-bot** | 招聘智能问询：知识库回答活水/伯乐/Offer/三方协议/HR 系统操作 | `/招聘问询` "活水规则" "伯乐奖金" |
| **recruitment-process-tracker** | 招聘流程跟踪（**社招专用** · 招聘经理 case-level 视角）：我负责的流程 / 跨人查别的 hr / 偏慢预警 | `/流程跟踪` `/招聘进度` "查我负责的岗位流程" |

### ⭐ 校招专属应用层

| Skill | 作用 | 典型触发 |
|---|---|---|
| **warming-recruit-manager** | 校招签约后**保温工作台**：识别毁约风险 / 重点关注名单 / 写保温话术 / 通知导师上级 / 按 BG/部门组织视角 / 每日保温播报 | "校招保温" "待入职名单" "通知导师" "重点关注" |

### 📊 HR 数据副链路

| Skill | 作用 | 典型触发 |
|---|---|---|
| **hr-data-router** | HR 数仓查询 **fallback 入口**（编排下面 6 个）：在 `recruit-data-dashboard` 判定未命中 44 治理指标后，承接员工 / 组织 / 入离职 / 招聘历史 / 环节粒度 / 活水专项等查询 | "查员工花名册" "看离职率" "组织架构" |
| **hr-data-sql-builder** | NL2SQL（StarRocks 数仓） — 自然语言 → SQL | 由 hr-data-router 编排 |
| **data-table-permission-checker** | 数据权限排查（脱敏值是否因权限不足） | "我有哪些表权限" "为什么这个字段是 0" |
| **indicator-query** | 通用 HR 预置指标查询（离职率 / 流入流出率 / 结构占比 / 均值 / 上级组织对比） | 由 hr-data-router 内部编排 |
| **indicator-api-codegen** | 预置指标浏览器端 API 代码生成 | 由 hr-data-router 内部编排 |
| **data-warehouse-api-codegen** | 前端调数仓接口代码生成（**仅前端**用，后端禁调） | "给前端项目生成调数仓的代码" |
| **hr-vue-next** | HR 业务组件库（员工 / 组织 / 岗位选择器，Vue 3 + TDesign） | 开发 HR 页面时 |

### 🛠️ 横切能力

| Skill | 作用 | 典型触发 |
|---|---|---|
| **daily-routine-builder** | 把"每天/每周自动跑"翻译成 `automation_update` 调度任务（已预置喝水提醒/晨报/招聘漏斗/校招保温模板） | `/定时任务` "每周一发我招聘漏斗" "每月 1 号给我组织变动月报" |
| **hrclaw-messenger** | HRClaw 邮件 + 企微 Tips 通用发送通道（playwright-cli + OA SSO Cookie），**被其他 skill 调用** | （内部工具，不直接对用户暴露） |
| **mcp-capability-explorer** | 动作、对象和平台需求明确后，现有 Skill 部分覆盖或无覆盖且缺口可探索时，按当前用户权限动态发现 recruit-mcp 能力；模糊输入先澄清，搜索使用全任务共享预算，动态写入仍须已登记 owner Skill | （内部 fallback，不直接对用户暴露，不展示全量能力目录） |

### 🚀 独立能力（社招看板 / 人才 Mapping / AI 外呼 / 测验平台）

| Skill | 作用 | 典型触发 |
|---|---|---|
| **recruit-data-dashboard** | 🥇 **数据域默认第一入口**（任何要数请求先进这里判命中）+ 社招指标驾驶舱：44 个治理级社招指标（漏斗/转化率/offer 接受率/入职/在招需求）精准口径，汇报/KPI 首选；未命中须显式告知后交接 hr-data-router | `/社招看板` "社招漏斗" "社招 offer 接受率" "在招需求进展" |
| **mapping** | 人才 Mapping / 人才行研：基于外部公开信息做竞对人才摸底 / 组织调研 / 候选人画像 / 寻访报告 | `/人才mapping` "挖字节大模型团队" "竞对人才摸底" "做个行研" |
| **recruiting-ai-outbound-call** | AI 电话外呼社招候选人确认岗位意向 + 查外呼结果（v1 仅 `SOCIAL_JOB_INTENTION`，绝不暴露手机号/承诺 offer） | "AI 外呼候选人确认岗位意向" "查那个岗位意向外呼结果" |
| **quiz-deliverable-evaluator** | 测验平台（quiz.woa.com · recruit-mcp quizplatform 分组）：路线一 阅卷待办→辅助阅卷给建议分（只读，供人工提交）/ 路线二 成绩单→自定义维度重评 / 成绩单 Excel 导出。后续可能扩展测验出题 | `/测验平台` `/阅卷` `/重评` "帮我读阅卷待办给建议分" "某场次按我的维度重评" "导出这个场次成绩单" |

完整的 slash 命令与关键词路由表见 [`agents/recruitment-expert.md`](./agents/recruitment-expert.md)。

### 🤝 招聘渠道域（1 个 · 按需读取 `references/routes/channel.md`）

| Skill | 作用 | 典型触发 |
|---|---|---|
| **headhunter-recommend** | 猎头供应商推荐（**仅社招**）：必须先拿到岗位 JD 或明确方向，再基于历史合作数据 / 能力标签 / 访谈记录推荐猎头。禁输出 BG 采购分布、禁原文回显、禁落盘 | `/猎头推荐` "这个岗位找哪家猎头" "帮我推荐猎头" "委外找人" |

> 与搜索域的分界：**渠道域产出「供应商清单」（找谁去找人），搜索域产出「候选人名单」（把人找出来）**。
> 校招问猎头 → 不支持（仅社招），引导转搜索域走校招库搜索或外部寻访。

### 🎨 雇主品牌域（5 个 · 按需读取 `references/routes/brand.md`）

一个统筹 + 三个执行 + 一个研究。人格名仅作**内部分工代号**，对外只有「腾讯招聘专家」一个身份。

| Skill | 角色 | 作用 | 典型触发 |
|---|---|---|---|
| **employer-brand-xiaoe** | 小鹅 · 统筹 | 品牌/传播/活动策划 + 各 BG（WXG/IEG/CDG/PCG/CSIG/TEG/S线）业务认知与 Playbook | "校招 campaign" "传播方案" "KV 创意" "宣讲材料策划" |
| **employer-brand-xiaowanneng** | 小完能 · 撰稿 | 公众号推文 / 标题摘要 / 社媒短文案（小红书·B站·抖音·视频号）撰写与保留原意润色 | "写篇招聘推文" "润色这段文案" "优化标题" |
| **employer-brand-lulu** | lulu · 审核 | JD / 宣讲 PPT / 海报 / 招聘短信 / 青云课题合规审核，出分级清单（🔴必改 / 🟡建议 / 💡待确认） | "帮我审一下这份 JD" "审核海报" "检查合规" |
| **employer-brand-amy** | Amy · 舆情 | 舆情监测研判 / 负面处置话术 / 取消 offer 沟通 / 面试投诉 / 删帖维权 / 水军对冲 | "最近舆情怎么样" "这个负面怎么处理" "取消 offer 话术" |
| **employer-brand-rita** | Rita · 调研 | 招聘调研设计 / 问卷生成 / 竞品人才策略 / 拒 offer 分析 / 跨域交叉洞察 | "帮我做招聘调研" "设计候选人体验问卷" "竞品人才策略分析" |

> ⚠️ **Rita 的数据类能力需另行接入 `campus-mcp`（校招调研数据后端）**（本包未声明，无弹窗，按需自助接入 → 见「连接 MCP」章节）。
> **未接通时只做方法论**（调研设计/问卷框架），绝不编造满意度百分比、样本量、NPS。
> 其余 4 个品牌 skill **完全不依赖 MCP，开箱即用**。

> 与招聘主链路的分界：**品牌域产出方案/文案/审核清单/舆情建议/调研报告，不产出候选人、不推进招聘流程**。
> 🔴 **「写 JD」归 `requirement-communication-assistant`，「审 JD」归本域 lulu** —— 最易越界的一条。

---

## 安装

在 WorkBuddy 专家中心找到「腾讯招聘专家」一键安装（1 个 Agent + 5 个按需路由参考 + 30 个 Skills）。安装时会弹出 userConfig 表单，按下面 §配置招聘 MCP 填好 Token 即完成。

### 技能依赖概览（统一索引）

> 一张表看清本专家所有外部依赖、归属、安装方式与必选性。**绝大多数用户开箱即用**——核心运行只需 Python 标准库 + 一个 MCP；其余皆为可选/特定场景才用。

| 依赖 | 类型 | 谁用到 | 必选性 | 安装方式 |
|---|---|---|---|---|
| **Python ≥ 3.8**（建议 3.10+）| 运行时 | 所有带脚本的 skill | ✅ 必选 | 系统自带 / 官网 |
| **Python 标准库**（`json`/`subprocess`/`pathlib`/`urllib`…）| 运行时 | 所有运行时脚本 | ✅ 必选 | 无需安装，开箱即用 |
| **`recruit-mcp`**（招聘 MCP）| MCP 服务 | 招聘业务全域（待办/简历/面评/问询…）| ✅ 必选 | 见下方 §配置招聘 MCP（写 `~/.workbuddy/mcp.json` + 连接器连接）|
| **`hr_data_service_v1`**（HR 数仓 MCP）| MCP 服务 | hr-data-router / hr-data-sql-builder / recruit-data-dashboard | ⬜ 用到 HR 数据/社招看板时 | 写 `~/.workbuddy/mcp.json` 的 `hr_data_service_v1` 段 + 连接器连接（探活引导内置在 skill 里）|
| **`iWiki` 连接器** | MCP 服务 | mapping（仅"沉淀到知识库"环节）| ⬜ 用 mapping 且要沉淀时 | WorkBuddy 左侧「连接器」→「自定义连接器」→ iWiki → 连接（搜索/出报告不依赖它）|
| **mcporter** | CLI | recruit-mcp 命令行兼容路径 / zhaopin-* 老用户 | ⬜ 可选（WorkBuddy 直配则不需要）| `npm install -g mcporter` |
| **playwright-cli** | CLI | hrclaw-messenger（邮件 + 企微 Tips 发送通道）| ⬜ 用 HRClaw 发送时 | `npm install -g @playwright/cli@latest` |
| **pdfplumber** | Python 包 | 解析 PDF 类输入的 skill（如简历/转写 PDF）| ⬜ 可选 | `pip install pdfplumber` |
| **pandas + openpyxl** | Python 包 | `recruitment-inquiry-bot/scripts/build_term_dict.py`（**离线维护工具**，agent 运行时不调）| ⬜ 仅开发者维护术语词典时 | `pip install pandas openpyxl` |

> 💡 **一句话**：普通用户装好专家 + 一键连上 `recruit-mcp`（弹窗点「连接」，太湖 SSO 授权，无需手填 Token）即可用；HR 数据/看板再连 `hr_data_service_v1`；mapping 沉淀再连 iWiki；mcporter/playwright/pdfplumber/pandas 都是特定场景才需要的可选项。
>
> ⚠️ 30+ 运行时脚本的环境要求按所属 skill 分散在各自 `SKILL.md` 中，本表是**统一索引**，细节仍以各 skill 文档为准。

---

## 连接 MCP（按能力分两条链路）

腾讯招聘专家在专家包层声明两个 MCP，首次进入对应能力时均由 WorkBuddy 直接唤起连接，并通过太湖 SSO 授权；**都不需要招活 Token**。

| MCP | 覆盖能力 | 地址 | 授权 |
|---|---|---|---|
| `recruit-mcp` | 大部分招聘业务：待办、简历搜索、面试安排、面评、招聘问询、外呼、测验平台等 | `https://zhaopin.mcp.it.woa.com` | 太湖 SSO / `Authorization` 单 header |
| `hr_data_service_v1` | 数据查询：员工/组织/合同/编制、招聘漏斗、社招指标驾驶舱等 | `https://dos-dataview.mcp.it.woa.com/mcp` | WorkBuddy 连接时唤起太湖授权 |

### 第三个 MCP：`campus-mcp` 校招调研数据后端（可选 · 按需自行接入）

Rita（`employer-brand-rita`，雇主品牌调研）的**数据类**能力还依赖一个校招调研后端。

> 📌 **命名说明**：官方页面生成的配置里 server 名默认叫 `rita`，与 skill `employer-brand-rita` 同名容易混淆
> （一个是数据后端、一个是执行 skill）。**建议粘贴时把 key 改成 `campus-mcp`**，本文档统一用这个名字；
> 保留 `rita` 原名也完全能用 —— Rita 调工具用裸工具名，不依赖 server 名前缀。
它**有意不写进本包声明** —— 因为它只服务 1 个 skill 的一半能力，若声明会导致全部 30 个 skill 的用户
在每次会话开场都被提示连接一个与自己无关的连接器。

> ⚠️ **申请资格：仅限「招聘团队」**。该后端存的是校招调研原始数据与竞品情报，只对招聘团队开放申请。
> 非招聘团队的同学不必申请 —— Rita 的方法论能力（调研设计 / 问卷框架 / 维度拆解）不接入也能用。

因此它**没有弹窗**，招聘团队同学需要用到时自行接入（两步）：

1. 打开 `https://campus123.woa.com/fofo` → 点「**已生成配置**」（OA 登录态直接完成注册，秒级免审批）
2. 页面会输出一段含 API Key 的完整 MCP 配置 → 粘进 WorkBuddy 的 MCP 配置（可顺手把 server 名改成 `campus-mcp`）

> ⚠️ 该配置含明文 API Key，属个人凭据：别贴到对话里、别截图外发、别提交 Git。
> ⚠️ 该后端地址是内网明文 HTTP（`http://21.91.205.237:8080/mcp`），官方暂未提供 HTTPS 端点。
>
> **不接入也能用 Rita 的方法论能力**（调研方案设计、问卷框架、维度拆解）；
> 其余 4 个雇主品牌 skill（小鹅 / 小完能 / lulu / Amy）完全不依赖它。
> 未接通时 Rita 会明确降级告知，**不会编造满意度百分比 / NPS / 样本量**。

工具清单（13 个）与 5 级角色权限见 `skills/employer-brand-rita/references/MCP接入指南.md`。

### 连接 MCP

招聘业务的所有数据（待办 / 面试安排 / 简历 / 知识库问询 / 面评 / 转写等）都通过 **`recruit-mcp`** 拉取，地址 `https://zhaopin.mcp.it.woa.com`。

### 一键弹窗连接（推荐 · 只需太湖授权）

🆕 recruit-mcp 已支持在 WorkBuddy 直接弹窗连接，**不再需要单独申请「招活 Token」**：

1. 首次触发招聘专家时，WorkBuddy 会弹出「**是否连接 recruit-mcp（https://zhaopin.mcp.it.woa.com）**」窗口 → 点「**连接**」。
2. 按提示用**太湖 SSO 授权**即可（无需手填任何 Token）。
3. 没弹窗时：WorkBuddy 左侧「连接器」→ 右上角「自定义连接器」→ 找到 recruit-mcp → 点「连接」/「Trust」。

> ✅ 连接只认**太湖授权**一项。旧版要求的第二个「招活 Token / recruit-Authorization」已下线，不用再申请。

### 手动配置（仅当客户端不支持弹窗连接时）

打开 `~/.workbuddy/mcp.json`，在 `mcpServers` 里加：

```json
{
  "mcpServers": {
    "recruit-mcp": {
      "url": "https://zhaopin.mcp.it.woa.com",
      "headers": { "Authorization": "Bearer <太湖PAT>" },
      "disabled": false
    }
  }
}
```

- 太湖 PAT 申请：<https://tai.it.woa.com/user/pat>（`Authorization` 要带 `Bearer ` 前缀）
- 另：`TRAG_TOKEN`（可选）仅 `requirement-communication-assistant` 用（参照人法 / 内部盘活），不用可留空，申请见 tRAG 控制台 → 个人中心 → PAT 管理（http://api.trag.woa.com）。

### 验证

- 当前会话工具列表能看到 `mcp__recruit-mcp__*` 系列工具 ✅
- 或检查 `~/.workbuddy/mcp.json` 出现 `recruit-mcp` 段（含 `Authorization` 一个 header 即可）

授权过期 → 重新点一次「连接」走太湖 SSO 即可。

---

## 故障排查

### ❌ 现象：agent "假装"完成了任务，但输出明显不准确

**典型表现**：
- 声称已调用 `assessment-quality-expert · A` 搭模型，但维度组合不对、缺少素质词典锚点
- 声称已调用 `zhaopin-operations` 搜简历，但没有真实候选人 RID
- 声称面试已下单，但拿不到 orderId

**根本原因**：通过 `task` 工具（subagent 方式）调用 `recruitment-expert`。

`task` 启动的是**轻量级子代理**，工具集被裁剪——子进程**没有 `use_skill` 工具**，无法加载 30 个子 skill 的完整上下文（SOP 文档、素质词典、模型库、招聘知识库等），只能基于训练记忆"编"答案。

### ✅ 正确触发方式

| 方式 | 示例 |
|---|---|
| **@ 提及 agent** | `@腾讯招聘专家 帮我搭一个产品经理的胜任力模型` |
| **直接说招聘关键词** | "帮我搭模型 / 写 JD / 出整套题 / 搜简历 / 填面评 / 看面试待办 ..." |
| **直接喊 agent 名** | "腾讯招聘专家"、"招聘专家"、"招聘助手" |

### ❌ 严禁的调用方式

```
task(subagent_name="recruitment-expert", prompt="...")  ← 严禁！
```

详细约束见 [`agents/recruitment-expert.md`](./agents/recruitment-expert.md) 顶部的「调用方式硬约束」章节。

---

## 客服反馈入口（Support Contacts）

> 用户在使用任意 skill 过程中遇到问题、反馈、建议时，agent 应在交付内容/报错信息末尾**附上对应 skill 的产品负责人**联系入口（企微/RTX 同名搜索可达）。

### 路由表（30 个 skill · 分域路由）

| 分组 | Skill | 产品负责人 |
|---|---|---|
| **数据查询副链路** | hr-data-router | `ansleyyu` |
| | hr-data-sql-builder | `ansleyyu` |
| | data-table-permission-checker | `ansleyyu` |
| | indicator-query | `ansleyyu` |
| | indicator-api-codegen | `ansleyyu` |
| | data-warehouse-api-codegen | `ansleyyu` |
| | hr-vue-next | `ansleyyu` |
| **社招指标驾驶舱** | recruit-data-dashboard | `ansleyyu` |
| **校招专属应用层** | warming-recruit-manager | `ansleyyu` |
| **业务问询** | recruitment-inquiry-bot | `ansleyyu` |
| **招聘需求 / 找人** | requirement-communication-assistant | `fayellawang` |
| | zhaopin-operations | `fayellawang` |
| | zhaopin-social-operations | `fayellawang` |
| **面试官日常 / 面试设计 / 面评** | interview-assistant | `elioyao` |
| | assessment-quality-expert | `elioyao` |
| | interview-data-processor | `elioyao` |
| | interview-talent-modeler | `elioyao` |
| | recruitment-process-tracker | `elioyao` |
| **人才 Mapping** | mapping | `elioyao` |
| **AI 外呼** | recruiting-ai-outbound-call | `elioyao` |
| **测验平台** | quiz-deliverable-evaluator | `elioyao` |
| **横切能力** | daily-routine-builder | `elioyao` |
| | hrclaw-messenger | `elioyao` |
| | mcp-capability-explorer | `elioyao` |

### 何时展示

每个 skill 在以下场景**必须**在消息末尾原样附上「💬 有问题或建议可联系产品负责人 **<contact>**（企微/RTX 同名）」：
1. 查询结果交付时
2. 调用接口报错时
3. 用户表达疑问 / 不满 / 反馈意图时

### 写法约定

- 各 SKILL.md frontmatter 中 `support_contact: <对应英文名>` 字段固化产品负责人
- SKILL.md 顶部「📮 客服 / 反馈入口（MANDATORY）」段使用对应路由表中的英文名
- 严禁把别的 skill 的 contact 当成本 skill 的 contact 输出（每个 SKILL.md 段内已加反向警示）

---

## 使用统计与隐私（Telemetry）

本包使用唯一入口 `scripts/track_skill_event.sh` 统计 Skill 调用和低敏运行状态，避免每个 Skill 复制一份脚本。上报地址为公司内部 Beacon（`otheve.beacon.qq.com`）；未在 Skill 中调用该入口的能力不会上报。

**上报什么**

| 字段 | 内容 | 是否可还原到个人 |
|---|---|---|
| 安装标识 | 首次运行随机生成 UUID，再做 SHA-256 单向散列 | 否 |
| `skill_name` / 事件名 | 哪个 Skill、什么低敏运营事件 | 否 |
| 白名单参数 | `status`、`scene`、`sub_flow`、`action` 等有限枚举 | 否 |

**不上报**：对话内容、候选人信息、简历数据、查询参数、MCP 返回的任何业务数据。

**如何完全关闭**（任一方式即可，脚本会在采集任何东西之前直接退出）

```bash
export SKILL_TRACKER_DISABLED=1        # 或使用通用约定 DO_NOT_TRACK=1
mkdir -p ~/.skill-tracker && touch ~/.skill-tracker/opt-out   # 持久化关闭
```

> 上报失败不会影响任何功能：统一脚本始终返回 0，网络异常时静默跳过。

---

## 路由评测（evals）

瘦身后架构从「靠信息冗余兜底」改成「靠精准路由」——一级 Agent 只判域、进域后只读一个路由视图。
好处是上下文大幅下降，代价是**压缩误删规则不再会被冗余掩盖**。因此配了一套评测集做门禁。

```bash
python3 evals/build_golden_set.py       # 从注册表重新生成样本集
python3 evals/route_regression.py       # 跑可达性检查
python3 evals/route_regression.py --report   # 额外写入 evals/reports/
```

**样本来源**（共 90 条，`evals/router-golden.jsonl`）：

| 来源 | 数量 | 说明 |
|---|---:|---|
| `registry:examples` | 37 | 注册表里每条能力的 examples，标签最可信 |
| `registry:commands` | 35 | slash 命令必须精确命中 |
| `manual:*` | 18 | 人工沉淀：跨域边界、历史事故、调度意图、已知不覆盖、内部通道 |

> `excludes` **不作为独立负样本**——它存的是能力短语而非用户话术，实测只有 7/80 能反查到
> 正确归属，直接用会造出标签错误的脏数据。它只用来生成 `forbidden_skills` 约束。

**当前基线**：90/90 可达（70 条经域内路由视图，13 条由一级 Agent 直接承接，0 条弱可达）。

**指标含义**：

- `via route view` —— 域内路由视图里有明确落点，最健康；
- `agent direct` —— `recruitment_core` / `automation` / `internal` 这三个域按设计没有路由视图，落在一级 Agent 正文属正常；
- `agent-only (weak)` —— **本该有视图的域却只在一级 Agent 找到落点**，是路由质量下降的早期信号，`--strict` 会拦。

⚠️ **这套评测只衡量「静态可达性」**（样本能否在文档里找到明确去处），
**不等于模型实际路由准确率**。真实准确率需要把样本喂给 Agent 跑一遍再比对，属于在线 Shadow Eval，尚未建立。
静态可达性是准确率的上界：文档里连线索都没有，模型不可能稳定路由对。

`validate_plugin_consistency.py` 已接入该回归，样本不可达时校验直接失败。

---

## 许可与作者

见 `.codebuddy-plugin/plugin.json` 的 `author` / `license` 字段。
