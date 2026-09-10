---
name: quiz-deliverable-evaluator
description: >
  考试评估全能工具，围绕两条主干路线组织：
  【路线一 · 阅卷待办 → 辅助阅卷】拉阅卷待办（仅主观题：简答/代码/AI实战）→ 逐题读透题干、评分参考、考生答案 → 生成「阅读简报」+ AI 建议分数与理由，辅助阅卷官打分（只给建议，绝不提交系统，MCP 也无写回分数的接口）；
  【路线二 · 成绩单 → 整理归档 / 自定义重评】给场次链接或场次名即可定位 → exam_venue_detail2 列出该场次全部考生及状态（待测验/作答中/已交卷/阅卷中/已出分）→ 逐个取成绩单 → 两种交付：
  ① 整理归档：导出单工作表 Excel（题目/作答/结果/附件），支持用户自带模板，附件下载到本地并以相对链接关联，另打一体化 ZIP 包；
  ② 自定义重评：把作答内容全量落盘（简答全文、代码源码、AI 实战对话、附件解包）成评审套件 + 维度分数格留空的评分表，客观题只取对错，平台原分只作参照。
  注意：附件只出自简答题（studentAnswer.attachment[]）与 AI 实战题（deliverableUrl），客观题与代码题没有附件。
  也回答「这个场次有没有完成的试卷 / 谁出分了 / 有哪些考生」这类场次与考生状态查询。
  另保留 HTTP+Cookie 附录模式（A 取原始数据 / B 自定义维度报告 / C 交付物评分），供外部脚本使用。
tags:
  - quiz
  - evaluation
  - scoring
  - 考试
  - 打分
  - 评估
  - 待办
  - 成绩单
  - 阅卷
  - 重评
  - 导出
  - Excel
  - 场次
  - 答卷
  - 附件下载
  - 自定义报告
  - mcp
  - html-report
version: "8.0.0"
author: zpagent-team
support_contact: elioyao
---

# 考试评估全能工具

## 🚨 FIRST ACTION（进入 Skill 后第一件事 · MANDATORY · 静默执行）

> 🔴 **每次 agent 通过 `use_skill("quiz-deliverable-evaluator")` 进入本 skill 时**，第一件事是后台静默上报 `skill_invoked`。这是看板能区分"哪个 skill 被调用了多少次"的核心数据，**缺它将导致该 skill 调用量在看板上为 0**。

```bash
bash ../../scripts/track_skill_event.sh "0WEB06ZI7OVDOZQW" "quiz-deliverable-evaluator" "skill_invoked"
```

**执行约束**：
1. **每次进入都要执行** — agent 每次 use_skill 调用都跑一次，不要因为"刚跑过"就跳过。
2. **静默后台** — 命令输出不展示给用户，失败也不中断主流程。
3. **不要询问用户** — 不得就"是否上报""以什么方式记录"等问任何问题。
4. **上报完立即继续** — 不等待、不复述，直接进入下方业务流程。

> 隐私：中央脚本只上报 skill 名、事件名与安装级伪名，**不含任何用户输入、候选人信息或自由文本**；
> 用户可用 `DO_NOT_TRACK=1` / `SKILL_TRACKER_DISABLED=1` / `~/.skill-tracker/opt-out` 完全关闭。

---

本工具围绕**两条主干路线**组织，分水岭是「成绩单出没出分」：

- **路线一：阅卷待办 → 辅助阅卷**——考生**还没出分**，帮阅卷官把待批阅的主观题读透，给出建议分供人工在系统里提交。
- **路线二：成绩单 → 整理归档 / 自定义重评**——考生**已有作答**（已交卷 / 阅卷中 / 已出分都能查），把成绩单拉全，再按用户目标交付：整理成表存档，或落盘成可重评的评审套件。

> HTTP+Cookie 的老路径（A 取数 / B 维度报告 / C 交付物评分）作为**附录**保留，供外部脚本/批量场景使用。

---

## 触发场景

### 路线一：阅卷待办 → 辅助阅卷
- "帮我读一下我的阅卷待办"、"把这些待阅卷的题给我读了"
- "帮阅卷官把每道题读透，给我建议分，我来提交"
- "我有一批待阅卷的主观题，逐题梳理题目/评分参考/考生答案，并给建议分"
- 核心特征：**阅卷官视角**，待办里只有主观题（简答/代码/AI实战），要 AI **读题+读评分参考+读考生答案**，产出「阅读简报 + 建议分」，最终由阅卷官到系统提交

### 路线二 · 目标 A：整理归档（导出成表）
- "把这个人的作答下载下来做成 Excel"、"导出成绩单，题目、作答、结果都要"
- "整理一下这个场次的答题情况"、"做个表给我"、"我要本地存档"
- "附件下载到本地然后插入进来"、"按我这个模板导"
- "导出这个场次所有已出分考生的成绩单到 Excel"
- "只导出简答题的题目、提交答案、阅卷人、评分、评语"
- "把判断题/多选题单独导出，答案要显示正确或错误/实际选项文案"
- 核心特征：**要产出本地文件**，可读优先（长文本给摘要、附件给链接），不需要 AI 给结论

### 路线二 · 目标 B：自定义重评（下载全量作答后自己打分）
- "把所有作答内容下载下来，我按自己的维度重新打分"
- "考生已经出成绩了，我想用自己的维度重新评价"
- "平台评分我不认，我要自己评"、"我要逐题看完自己打分"
- "这个场次的考生，客观题看对错就行，主观题按我的标准重评"
- 核心特征：**成绩单已存在**，用户要**换维度重评**，完整优先（作答全文不截断、附件必须解包）

### 场次与考生状态查询（两个目标的前置）
- "这个场次有没有完成的试卷"、"有几个人交卷了"、"谁出分了"
- "这个场次里有哪些考生 / 考生状态如何"（→ `exam_venue_detail2`）
- "帮我看看待办列表"、"有哪些考试需要评估"
- "我还有什么场次的成绩单可以看到"、"查一下场次列表"
- "拉取这个候选人的成绩单"、"看一下这道题的答题情况"
- 直接给了场次链接：`https://quiz.woa.com/quiz-manage/session-manage/view?id=<数字>`

### HTTP 附录模式（A/B/C）
- 用户提供 quiz.woa.com 的待办/成绩单/交付物 URL
- 需要外部脚本/批量处理、且手头有 OA Cookie

---

## 🧭 两条主干路线（总纲）

| | **路线一：阅卷待办 → 辅助阅卷** | **路线二：成绩单 → 整理归档 / 自定义重评** |
|---|---|---|
| **入口** | `todo_mark_list`（我的阅卷待办） | 场次链接 / 场次名 / `todo_mark_list` 反查 → `exam_venue_detail2`（按场次列考生） |
| **数据状态** | **待批阅**（status=0，还没出分） | **成绩单已存在**（已出分 marked 为典型，阅卷中/已交卷也可查） |
| **核心接口链** | `todo_mark_list` → `todo_mark_detail` | `exam_venue_detail2` → `queryResult` →（附件/AI实战）COS 预签名 URL 落盘 |
| **题型范围** | 只有主观题（简答/代码/AI实战） | 全题型（客观+主观都在成绩单里） |
| **AI 角色** | **辅助阅读 + 给建议分**（不提交系统） | 目标 A 只做整理不给结论；目标 B 备料给用户自评（要建议分须显式标注） |
| **客观题** | 待办里没有客观题 | 只取对错、不重评 |
| **产出** | 逐题「阅读简报 + 建议分/理由」 | 目标 A：单表 Excel + 附件包；目标 B：评审套件 + 空白评分表 |
| **谁最终定分** | **阅卷官**到系统提交 | 目标 A 不定分；目标 B 由用户自己定（不写回系统） |

**分水岭一句话：还没出分走路线一，已经出分走路线二。**

> ⚠️ **重要事实**：MCP 的阅卷接口（`todo_mark_list` / `todo_mark_detail` / `queryResult` / `exam_venue_detail2`）**全部只读**，没有"把分数写回系统"的接口。因此路线一里 AI 给的分数**永远只是建议**，落库提交只能由阅卷官在平台手动完成。

### 🎯 路线二的两个交付目标（进路线二后必须先认目标）

取数链路完全一样，**交付物和内容取舍相反**：

| | **目标 A · 整理归档** | **目标 B · 自定义重评取数** |
|---|---|---|
| 用户想干什么 | 整理成表，本地存档 / 传阅 / 自己加备注 | 作答全量落盘，按**自己的维度**重新打分 |
| 典型话术 | 「整理成 Excel」「导出成绩单」「做个表给我」「附件下载下来放表里」 | 「所有作答下载下来」「我按自己维度重新打分」「平台评分我不认」 |
| 内容取舍 | **可读优先**：长文本给摘要，附件给链接 | **完整优先**：长文本给全文，附件全部解包可读 |
| 交付物 | 单表 Excel（+ 附件 ZIP 包） | 评审套件（逐题全文 + 附件解包 + 空白评分表）+ Excel 索引 |
| 平台原分 | 如实呈现，是主要信息 | 只作**参照**单列，**不是**结论 |
| 谁给结论 | 不给结论 | 用户自己按维度评；AI 协助时必须标注「建议，仅供参考」 |

**判别问一句就够**：用户没明说时问「① 整理成表存档 ② 下载全部作答我自己重新打分」。
两个都要 → 都给：Excel 做索引，套件做正文，互相链接不重复两份。

🔴 **速判口诀**：**要不要产出本地文件** —— 要文件走路线二（再分 A/B）；只在对话里读题给建议分走路线一。

---

## 🔴 执行硬约束（不得违反）

> 这些约束原先写在一级 agent 里，现下沉到本 skill 就近约束——
> 无论 agent 是否复述，进入本 skill 后都必须遵守。

1. **主进程串行执行，禁子代理**：本 skill 的「取待办 → 取详情 → 解析 → 出简报/报告」**必须在主进程内 `use_skill` 后串行跑完**，**严禁** `Task(subagent_name=...)` 起子代理。
2. **阅卷接口全只读，AI 只给建议分**：`todo_mark_list` / `todo_mark_detail` / `queryResult` / `exam_venue_detail2` **均无写回分数接口**。路线一 AI 给的分**永远只是建议**，必须标注「仅供参考，请到系统提交」，落库由阅卷官手动完成——**绝不声称已提交 / 已打分入库**。
3. **绝不臆造考生答案**：考生答案取不到时（如 AI 实战题 `conversationsFetchStatus=EMPTY`）**如实说明缺失**，严禁凭题目正文脑补答案内容或硬凑分数。
4. **二进制不进对话**：AI 实战题交付物优先用 `queryResult` 返回的 `deliverableUrl`（COS 预签名 URL）`curl` 落盘，再离线解析；**禁止**让 `downloadAllFiles` 的 ZIP 二进制回传上下文。
5. **考试敏感数据**：成绩单 / 答卷 / 交付物属敏感数据，评估完成后建议清理本地临时文件。

## 🔴 与相邻 skill 的边界（防抢错）

「待办」「导出」「评估」这些词与面试待办、面评、简历评估高度相邻：

| 用户想要的 | 该走 | 不是 |
|---|---|---|
| **考试/测验的阅卷待办**（简答/代码/AI 实战题批阅） | 本 skill 路线一 | ❌ 不是 `interview-assistant · T`（那是面试待办） |
| **面试待办 / 推荐待办**（约面、面评待填） | `interview-assistant · T/T2` | ❌ 不是测验阅卷 |
| **测验成绩单导出 Excel / 整理答题情况** | 本 skill 路线二目标 A | ❌ 不是 `interview-assistant`、也不需要另一个导出 skill |
| **测验成绩单重评 / 按维度重打考卷** | 本 skill 路线二目标 B | ❌ 不是 `interview-assistant · B`（那是简历评估） |
| **场次有没有完成的试卷 / 有哪些考生** | 本 skill（`exam_venue_detail2`） | ❌ 不是 hr-data-router（那是数仓沉淀数据） |
| **简历评估 / 简历打分** | `interview-assistant · B` | ❌ 不是测验重评 |
| 只说"待办"，没说测验还是面试 | 反问一句确认 | — |

> 判据：**出现「阅卷 / 评卷 / 成绩单 / 场次 / 考生答卷 / 测验 / 考试」等考试语义时才进本 skill**。单纯"待办 / 评估 / 打分"默认归面试链路，除非明确带考试 / 测验语义。

🔴 **本 skill 是测验平台的唯一入口**：阅卷、成绩单查询、Excel 导出、附件下载、自定义重评**全部在这里**，不要去找 / 不要新建别的 `quiz-*` / `exam-*` skill 分担。若看到清单外的近名 skill（带 `quiz` / `exam` / `transcript` 的变体），一律视为外部体系不调用。

---

## MCP 调用规范（必读）

> recruit-mcp 的 SearchAPI / CallAPI 有严格的三步调用流程，**禁止跳步或凭猜测构造 apiId**。

### 三步流程

```
第①步：SearchAPI(query="关键词") → 获取能力清单，找到目标 apiId
第②步：SearchAPI(apiId="从①复制的完整ID") → 获取参数定义和调用示例
第③步：CallAPI(apiId, params) → 执行实际调用
```

### 关键规则

1. **apiId 必须完整复制**：格式为 `{domain}.{group}.{name}`（三段式），不可自行构造
2. **必须先看参数定义再调 CallAPI**：第②步返回的字段定义了 params 里该传什么
3. **相同业务连续操作锁定同一分组**：待办→场次→成绩单→阅卷详情都在 quizplatform 分组下

---

## 前置条件

### 1. MCP 环境（推荐，无需 Cookie）

如果在 CodeBuddy 中有 `recruit-mcp` 服务可用，则**无需 OA Cookie**，通过 MCP 直连 quizplatform API。

### 2. HTTP 模式（附录 A/B/C 备选）

脚本路径：`plugins/txzhaopin/skills/quiz-deliverable-evaluator/`

```bash
pip install -r plugins/txzhaopin/skills/quiz-deliverable-evaluator/requirements.txt
export QUIZ_OA_COOKIE="uin=o000xxx; p_uin=o000xxx; skey=@xxxx; p_skey=xxxx"
```

---

## API 速查表（MCP 模式）

### 测验平台 · quizplatform 分组

| 用途 | API ID | 方法 | 关键参数 | 返回核心字段 |
|------|--------|------|---------|-------------|
| 阅卷待办 | `recruit.quizplatform.post_api_mcp_todo_mark_list` | POST | `{}` | `records[].markPaperId` / `examReceiptId` / `name` / `paperName` / `examVenueName` / `examVenueId` / `status`(0待批阅) —— **固定只查待办，不查已办** |
| 阅卷详情 | `recruit.quizplatform.get_api_mcp_todo_mark_detail` | GET | `markPaperId`(必填) + `receiptId`(必填，来自待办的 examReceiptId) | `shortMarkQuestionVOS`/`codeMarkQuestionVOS`/`aiCodeMarkQuestionVOS`、评分参考、考生答案、`markCard`、`canJudgeFlag`。⚠️ **aiCoding 的 studentAnswer 实测为空，对话记录需走 queryResult** |
| **场次详情（含考生列表）** ★ | `recruit.quizplatform.post_api_mcp_exam_venue_detail2` | POST | `{"examVenueId": "..."}` | `venue`(名称/statusName/typeName/起止时间) + `totalCount` + `examinees[]`（**`examReceiptId` / `name` / `statusName`：待测验/作答中/已交卷/阅卷中/已出分/未参加/已取消**），不分页全量 |
| 场次发现 | 无独立场次列表 API | — | 从 `todo_mark_list` 的 `records[].examVenueId` + `examVenueName` 提取场次 | 生产环境无 `exam_venue_list`，需通过阅卷待办间接获取场次 ID |
| 成绩单 | `recruit.quizplatform.get_api_mcp_answer_result_queryResult` | GET | `receiptId`(必填) | `title` / `markStatus`(unmark/marking/marked) / `studentInfo` / `testContentVO[]`（逐题：题干/学生答案/得分/正确答案/`trueAnswer`）/ `scoreCard`。**AI实战题额外返回 `conversations[]`（CodeBuddy 对话记录）+ `conversationsFetchStatus`(SUCCESS/EMPTY/FAILED)** |
| 下载 AI 实战题文件 | `recruit.quizplatform.post_api_mcp_answer_result_downloadAllFiles` | POST | `{"examReceiptId": "...", "questionId": "..."}` | ZIP 二进制流（302 跳 COS）；仅 aiCoding 题、工作空间有文件时可下 |
| 通用待办（审题/审卷） | `recruit.quizplatform.post_api_mcp_todo_list` | POST | `{}` 或 `{"type":"questionReview"}` | 多种待办类型，各有独立结构 |
| 审题/审卷操作 | `recruit.quizplatform.post_api_mcp_todo_review` | POST | `action`(`approve`/`reject`), `remark` | 审核结果 |

### 校招/社招待办中心（与阅卷无关，数据隔离）

| 用途 | API ID |
|------|--------|
| 校招面试/录用/评估/考核待办 | `recruit.campus-center-front.get_campus_interview_todo_list` 等 |
| 社招待办数据列表 | `recruit.social-todo-center.get_api_trace_get_list` |

> ⚠️ 这些"已办/待办"接口属于流程审批，**不能**用来查"阅卷已办"。阅卷侧 `todo_mark_list` 固定只查待办、无已办列表接口。

---

## 两个待办接口的区别

| | `todo_mark_list`（阅卷待办） | `todo_list`（通用待办） |
|---|---|---|
| 用途 | 查看需要阅卷打分的考生 | 查看审题、审卷等通用待办 |
| type 参数 | 不支持，固定只查待阅卷 | 可选 `questionReview` / `paperReview` |
| 使用场景 | "帮我评测待办"、"有哪些待阅卷的" | "有哪些审题待办" |

> **默认规则**：用户说"待办"且未明确类型时，优先 `todo_mark_list`（阅卷待办是最常见场景）。

---

═══════════════════════════════════════════════════════════
# 路线一：阅卷待办 → 辅助阅卷（给建议分，不提交系统）
═══════════════════════════════════════════════════════════

> **何时使用**：阅卷官有一批**待阅卷的主观题**（阅卷待办里只会是简答 short / 代码 code / AI实战 aiCoding），希望 AI 把每道题**读透**——题目要点、评分参考、考生答案（含附件）都整理清楚，产出「阅读简报」并给出**建议分数与理由**，供阅卷官参考后自行到系统提交。
>
> **核心原则**：
> - AI **给建议分 + 理由**，但**绝不触碰系统提交**（MCP 也无写回分数的接口，天然做不到）。
> - 建议分永远标注"仅供参考"，最终分由阅卷官在平台提交。
> - 考生答案**取不到时如实说明缺失，严禁凭题目臆造**。

### 接口链（实测验证）

| 步骤 | 接口 | 作用 |
|------|------|------|
| 1 | `todo_mark_list` | 拉阅卷待办，拿每条的 `markPaperId` + `examReceiptId` + 考生名 + 场次 |
| 2 | `todo_mark_detail` | 用 `markPaperId`+`receiptId` 拿**题目详情+评分参考+考生答案**（辅助阅卷主数据源） |
| 2b（AI实战题） | `queryResult` | ⚠️ AI实战题的**对话记录不在 mark_detail**，需用 `queryResult` 取 `conversations`；文件走 `downloadAllFiles` |

### 🔒 考生提交答案的形态约束（硬约束，必须遵守）

> 三种题型的**考生答案形态是固定的**，简报里对"考生答案"的呈现必须符合下表；取不到时如实说明缺失，**绝不臆造答案内容**。

| 题型 | 考生答案一定包含 | 可能包含附件 |
|------|-----------------|---------|
| 简答题 `short` | **考生填写的文本** | ✅ 可能有（0~多个，`studentAnswer.attachment[]`） |
| 代码题 `code` | **考生提交的源码**（`studentAnswer.sourceCode`） | ❌ **没有附件** |
| AI实战题 `aiCoding` | **考生与模型的对话记录** | ✅ 可能有（工作空间 ZIP，`deliverableUrl`） |

🔒 **附件只出自简答题和 AI 实战题**——代码题的源码是文本字段不是附件，客观题（单选/多选/判断/填空）根本没有附件位。**不要在这两类题上找附件，也不要因为找不到就报"附件缺失"。**

**推论（决定简报怎么写）：**
- 简答题：文本必读；**有附件才**按附件规则下载解析，没有就不提。
- 代码题：**核心作答就是 `sourceCode` 文本**，必须读到代码内容；为空则说明未提交，如实提示。**不要去下载代码题附件**——它没有。
- AI实战题：**对话记录是主要评判对象**。`todo_mark_detail` 里 `studentAnswer` 为空 `{}`，对话记录需改用 `queryResult` 取 `conversations`（`conversationsFetchStatus=EMPTY` 表示考生确实没产生会话）；交付物走 `queryResult` 的 `deliverableUrl`，为 `null` 才用 `downloadAllFiles` 触发打包。

### 三种题型的字段结构（以实测真实返回为准）

| 题型 | 题干 | 评分参考（辅助阅卷的核心） | 考生答案（按硬约束） |
|------|------|--------------------------|--------------------|
| 简答 `short` | `titleRich` | `questionContent.scoreReference`（答案要点）+ 关键词 | **生产成绩单 `queryResult`：文本** `studentAnswer.answer`，附件 `studentAnswer.attachment[]`；兼容旧结构时再回退 `studentAnswer.text` / `attachments[]`。⚠️ 实测存在**文本为空、作答全在附件里**的情况，此时必须下载附件 |
| 代码 `code` | `titleRich` | `questionContent`：参考答案 + IO 样例 + 测试用例 + 语言/时限/内存 | **源码文本** `studentAnswer.sourceCode` + `submitTime`。**无附件字段** |
| AI实战 `aiCoding` | `titleRich` | `questionContent`：AI实战题描述 + 评分维度（D1/D2/D3/R1）+ 评分锚点 + 建议追问 | **对话记录**（mark_detail 为空 → 用 `queryResult.conversations`）+ 可选交付物 ZIP（`deliverableUrl`，为 null 才 `downloadAllFiles`） |

> **公共字段**：`questionScore`(满分) / `score`(未阅为 null) / `status`(0未阅/1已阅) / `canJudgeFlag`(是否有权阅这份卷) / `markCard`(答题卡汇总) / `studentInfo`(考生名，匿名为 `**`)。

### 执行流程

```
┌──────────────────────────────────────────────────────────┐
│ Step 1  拉阅卷待办  todo_mark_list {}                        │
│  → records[]：markPaperId / examReceiptId / name / 场次     │
└───────────────────────────┬──────────────────────────────┘
                            ▼
┌──────────────────────────────────────────────────────────┐
│ Step 2  展示待办，让阅卷官选（可全部、可指定某人某场次）          │
│  提示：待办里都是主观题，且只含 status=0 待批阅               │
└───────────────────────────┬──────────────────────────────┘
                            ▼
┌──────────────────────────────────────────────────────────┐
│ Step 3  逐份取阅卷详情  todo_mark_detail                      │
│    {markPaperId, receiptId=examReceiptId}                  │
│  先看 canJudgeFlag，false 则提示无阅卷权限、跳过              │
│  若含 AI实战题 → 另调 queryResult 取 conversations            │
└───────────────────────────┬──────────────────────────────┘
                            ▼
┌──────────────────────────────────────────────────────────┐
│ Step 4  按题型解析每道题（题干/评分参考/考生答案）              │
│  · titleRich 去 HTML 标签取纯文本要点                        │
│  · 评分参考按题型取对应字段                                   │
│  · 考生答案(按硬约束)：                                       │
│    - 简答：读文本 + 有附件则下载解析                          │
│    - 代码：读代码文件 + 语言/提交时间                          │
│    - AI实战：queryResult 取对话记录；仍为空则如实提示          │
└───────────────────────────┬──────────────────────────────┘
                            ▼
┌──────────────────────────────────────────────────────────┐
│ Step 5  逐题输出「阅读简报 + 建议分」                          │
│  给建议分数+理由，标注"仅供参考，请到系统提交"                 │
└──────────────────────────────────────────────────────────┘
```

### Step 4 · 附件处理（下载并解析）

> 🔒 **只有简答题和 AI 实战题需要走这一步**。代码题（源码在 `sourceCode` 文本里）和客观题**没有附件**，跳过即可，不要当成缺漏。

**简答题附件**（`studentAnswer.attachment[]` 的 `name`/`size`/`url`）：
- 有附件时**下载并解析内容**一起纳入阅读（复用附录 C 的 `downloader.py`；MCP 环境下 url 是 COS 预签名直链可直接 `curl`）。
- 常见附件：文档（docx/pdf/md）、代码文件、压缩包。解析后并入该题「考生答案摘要」。
- ⚠️ **文本为空但有附件是常见形态**——作答实体就在附件里，必须下载，不能只写"未提交答案"。
- 下载失败/无法解析时**降级为列出附件清单**（名称/大小/链接）提示阅卷官自查，不阻断简报。

**AI 实战题交付物**（`testContentVO[].deliverableUrl` 工作空间 ZIP）：
- 有 URL 直接 `curl` 落盘；为 `null` 表示归档未生成，才调 `downloadAllFiles` 触发打包。
- 解包后区分「初始模板」与「考生真实产出」，只有后者作交付质量依据。

**通用**：附件属考试敏感数据，简报产出后建议清理本地临时文件。

### Step 5 ·「阅读简报 + 建议分」输出模板（每道题一段）

```
════════ 考生：{name} · {场次}-{试卷} · 用时 {duration} ════════
阅卷权限：{canJudgeFlag ? 可阅卷 : ⚠️无权限} · 待阅题数：{N}

── 第 {seq} 题【{题型}】满分 {questionScore} ──

▸ 题目要点
  （titleRich 去标签后提炼：背景 / 任务 / 要求，3-5 条）

▸ 评分参考解读
  · 简答：答案要点 + 应覆盖的关键词
  · 代码：参考答案思路 + IO样例 + 测试用例覆盖点
  · AI实战：各维度评分锚点(逐档) + 建议追问 + 埋设的AI陷阱

▸ 考生答案摘要（严格按题型形态，缺失即如实说明，不臆造）
  · 简答：文本要点提炼；有附件→已下载解析要点 / 未取到→附件清单+提示
  · 代码：语言、核心实现逻辑、是否覆盖题目要求；过长则摘要+关键片段
  · AI实战：对话记录要点（来自 queryResult.conversations）；
     若 conversationsFetchStatus=EMPTY→"考生未产生会话"；仍取不到→提示到平台查看

▸ 对照评分锚点的观察
  · 命中了评分参考的哪些点 / 疑似遗漏哪些点
  · 代码题：是否覆盖样例与边界；AI实战：是否踩中埋设陷阱
  · 需阅卷官重点核实的地方（1-3 条）

▸ 💡 AI 建议分数与理由（仅供参考）
  · 建议分：{X} / {questionScore}
  · 理由：命中/遗漏点 → 为何给这个分（对齐评分参考）
  · 若考生答案缺失无法评：说明"无有效作答，建议核实后再定分"

【AI 建议分 {X}/{questionScore}，仅供参考 —— 最终分请阅卷官到系统提交】
════════════════════════════════════════════════
```

> **底线**：AI 可给建议分+理由，但必须①标注"仅供参考"②不做任何系统提交动作（也没有提交接口）③考生答案缺失时不硬凑分数，改为提示核实。

### 落地示例

```
用户: 帮我把阅卷待办里的题都读一下，给建议分，我来提交

AI:
  Step1 SearchAPI(query="阅卷待办") → SearchAPI(apiId) → CallAPI(todo_mark_list, {})
        → 展示 records[]（都是主观题、status=0），按场次+考生列出

  用户: 先读投资分析岗·AI实战那份

  Step3 CallAPI(todo_mark_detail, {markPaperId, receiptId})
        → canJudgeFlag=true；aiCodeMarkQuestionVOS 有评分锚点，但 studentAnswer={} 为空
        → 补调 CallAPI(queryResult, {receiptId}) 取 conversations 对话记录

  Step4 解析题干 + 评分锚点 + 对话记录

  Step5 输出「阅读简报 + 建议分」：题目要点 / D1-D3+R1评分锚点 / 建议追问 /
        考生对话记录要点 / 需核实点 / 💡建议分X分及理由（仅供参考，请到系统提交）
```

---

═══════════════════════════════════════════════════════════
# 路线二：成绩单 → 整理归档 / 自定义重评
═══════════════════════════════════════════════════════════

> **何时使用**：考生**已有作答**（已交卷 / 阅卷中 / 已出分都能查，`marked` 为典型）。用户要么想把答题情况**整理成表存档**（目标 A），要么想**下载全部作答后按自己维度重评**（目标 B）。
>
> **与路线一的本质区别**：路线一从"待批阅"进入、给建议分供阅卷官提交；路线二从"已有成绩单"进入、产出本地文件。

### Step 0 · 需求识别（先判后动，五个变量）

| 变量 | 取值来源 | 缺失时 |
|---|---|---|
| **交付目标** | 「整理 / 存档 / 做表 / 导出」→ A；「下载全部作答 / 我自己打分 / 重新评」→ B | 反问二选一（A / B / 都要） |
| 场次 `examVenueId` | URL 的 `?id=` 参数；或用户给的数字 ID；或从 `todo_mark_list` 的 `records[].examVenueId` 反查 | 反问或先列可见场次 |
| 考生范围 | 点名姓名 / `examReceiptId`；或「已出分的那个」「全部」 | 先列场次考生 + 状态让用户挑；只有 1 个符合条件时可直接用并说明 |
| 状态筛选 | 「完成的 / 出分的 / 交卷的 / 全部」 | 默认取**已出分**；若无已出分，明确告知并列出实际状态 |
| 交付形态 | 用户给的模板 / 「Excel」/「表格」 | 无模板则用本 skill 默认单表模板 |

**状态词映射（不要自行发挥）**：

| 用户说 | 对应 `statusName` |
|---|---|
| 完成 / 做完了 / 交了 | 已交卷、阅卷中、已出分（三者都算做完，**需分开列出**） |
| 出分 / 有成绩 / 判完了 | 已出分 |
| 在做 / 进行中 | 作答中 |
| 没做 / 还没开始 | 待测验、未参加 |

⚠️「完成」是高频歧义词：`已交卷` / `阅卷中` / `已出分` 是三种不同状态。回答「有没有完成的试卷」时**必须按状态分别报数**，不要笼统说「有 N 份完成」。

目标 B 额外要确认（问不到就用默认并在交付时说明）：

| 追加变量 | 默认 |
|---|---|
| 评分维度 | 给预设模板让用户选或改（见下「预设维度模板」） |
| 客观题是否重评 | 默认**不重评**，只取平台对错 |
| AI 是否给建议分 | 默认**只备料不打分**；用户明确要才给，且必须标注「建议，仅供参考」 |

### ★ 关键：按场次拿考生单据已打通（exam_venue_detail2）

> 之前"没有按场次列已出分考生接口"的约束**已作废**。新增的 `exam_venue_detail2` 传 `examVenueId` 即可**一次性列出该场次全部考生**（`examReceiptId` + `name` + `statusName`，含"已出分"），不分页全量。断链补齐：
>
> ```
> 场次 URL（解析 ?id=）或场次名 → examVenueId
>    ↓  （只有场次名时才用 todo_mark_list 的 records[].examVenueId 反查）
> exam_venue_detail2(examVenueId)  →  全部考生 [{examReceiptId, name, statusName}]
>    ↓  （按 statusName 筛/让用户挑，重评典型选"已出分"）
> queryResult(receiptId)  →  逐个拿成绩单
>    ↓  （附件 / AI实战交付物）
> COS 预签名 URL curl 落盘（deliverableUrl 为 null 时才用 downloadAllFiles 触发打包）
> ```

🔴 **`examVenueId` ≠ `examReceiptId`**：前者是场次，后者是某考生的答卷单据。`queryResult` **只吃 `receiptId`**，传错必然查不到。用户点名某人时用姓名匹配 `examinees[].name` 拿 `examReceiptId`，不要凭猜。

### 交互开场必问（目标 B 才需要问全）

目标 A 只要拿到「场次 + 考生范围」就能开工，不必问维度。
目标 B **先一次性问清以下 4 点再动手**（除非已在需求中说明）：

```
好的，按场次重评。开始前先确认 4 件事：

1️⃣ 评哪个场次？（场次链接 / 场次名 / examVenueId 都行）
2️⃣ 评谁？—— 我会用 exam_venue_detail2 列出该场次全部考生及状态，
   你可以全部逐个评，或指定其中几个（重评典型是选「已出分」的）。
   （按你的设定：一个个评，每人单独出一份报告）
3️⃣ 用什么维度评？—— 有几套预设模板（见下），可直接选/在模板上改/完全自定义。
4️⃣ 确认评价范围：客观题（单选/多选/判断/填空）只取平台判定的对错、不重评；
   自定义维度只作用在主观题（问答 short / 代码 code / AI实战 aiCoding）上。是这样吗？
```

> **规则**：4 点没问清前不要调用评分逻辑；但"拉场次列表""拉场次详情""拉成绩单""下载附件"这类只读操作可以先做。
> 🔴 **附件签名只有 30 分钟**，所以**先下载再排版**，不要等问完维度才下载。

### 预设维度模板（供用户选择/微调）

| 模板 | 适用场景 | 维度（名称 / 权重） |
|------|---------|--------------------------|
| **技术能力** | 技术岗主观题/代码题 | 技术方案合理性 0.30；代码/实现质量 0.25；问题分析深度 0.20；表达逻辑性 0.15；工程素养 0.10 |
| **产品思维** | 产品/运营岗主观题 | 需求理解 0.30；方案完整度 0.25；用户视角 0.20；逻辑结构 0.15；创新性 0.10 |
| **AI 协作能力** | AI 实战题（aiCoding） | 意图澄清 0.25；任务拆解 0.25；审辩决策 0.25；交付质量 0.25 |
| **通用表达** | 开放主观题 | 内容准确性 0.30；逻辑清晰度 0.25；论证深度 0.25；表达规范 0.20 |

> 展示模板时让用户**确认或修改**：可改维度名、权重、说明，也可整套替换。权重总和建议为 1.0。
> 完整维度说明（每个维度"看什么"）+ 评分表生成规则 + 评分档位见 @references/scoring-templates.md
> 接口字段结构、题型作答结构、签名 URL 与 403 排障、实测回归样例见 @references/quiz-api-reference.md

### 执行流程

```
┌─────────────────────────────────────────────────────────┐
│ Step 0  认目标（A 归档 / B 重评）+ 问清场次 / 评谁              │
│  目标 B 再问：维度 / 客观题是否重评 / 要不要 AI 建议分          │
└───────────────────────────┬─────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────┐
│ Step 1  定位场次 → 拿 examVenueId                            │
│  优先解析场次 URL 的 ?id=；只有场次名时才用                │
│  todo_mark_list {} 从 records[].examVenueId 反查              │
└───────────────────────────┬─────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────┐
│ Step 2  ★ CallAPI: exam_venue_detail2 {"examVenueId":"..."}  │
│  → examinees[]：{examReceiptId, name, statusName}           │
│  展示考生清单+状态（已交卷/阅卷中/已出分要分开报数）            │
└───────────────────────────┬─────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────┐
│ Step 3  用户挑人（默认逐个，每人一份交付）                       │
└───────────────────────────┬─────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────┐
│ Step 4  逐个取成绩单 queryResult {"receiptId": ...}          │
│  → 立刻用 COS 预签名 URL 下载附件 / 交付物（签名仅 30 分钟）    │
└───────────────────────────┬─────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────┐
│ Step 5  拆分题型                                             │
│  · 客观题(radio/multiple/judgment/blank)：只取 trueAnswer/   │
│    score，如实呈现对错，不套用户维度                           │
│  · 主观题(short/code/aiCoding)：取 studentAnswer/titleRich/  │
│    conversations；目标 A 摘要、目标 B 全文落盘                 │
└───────────────────────────┬─────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────┐
│ Step 6  按目标交付                                           │
│  A：单表 Excel + attachments/ + 一体化 ZIP                   │
│  B：评审套件（全文 + 解包 + 空白评分表）+ ZIP                  │
│  （用户要 HTML 报告时才用 report_generator.py / json-report） │
└─────────────────────────────────────────────────────────┘
```

### Step 5 · 题型拆分规则（客观题只取对错、只重评主观题）

成绩单 `testContentVO[]` 每题按 `questionType` 分流：

| questionType | 归类 | 重评处理 |
|--------------|------|---------|
| `radio` 单选 / `multiple` 多选 / `judgment` 判断 / `blank` 填空 | **客观题** | 只读 `trueAnswer`(0错/1对/2部分)、`score`、`questionScore`；报告如实呈现对错，**不套用户维度** |
| `short` 问答 / `code` 代码 / `aiCoding` AI实战 | **主观题** | 取 `studentAnswer`（问答=生产 `answer` + `attachment`，兼容旧 `text` + `attachments`；代码=`sourceCode`；AI实战=`conversations` 对话记录 + `downloadAllFiles` 文件）、`titleRich`；**按用户自定义维度重新打分** |

> AI 实战题的 `conversations`（CodeBuddy 对话记录）现在**直接在成绩单 queryResult 返回**，是重评的重要依据；代码/交付物用 `downloadAllFiles`。
> 重评时**不要把平台原有的主观题 score/remark 当作你的结论**——那是被替换的对象；可作为对比参考单独标注。

### ★ 成绩单 Excel 导出规范（生产环境实测）

> **适用场景**：目标 A 整理归档，或目标 B 的 Excel 索引。数据源固定为 `exam_venue_detail2` + `queryResult`，不从页面截图、题目正文或题型名称猜测答案。

#### 0. 默认只建一个工作表（重要）

用户拿到 Excel 是要**本地继续整理**的，所以：

- **默认单工作表**，不拆「概览 / 明细 / 附件清单 / 附件内容」多表。
- 默认列（未指定时用这套精简版）：`题号`、`题型`、`题目`、`作答`、`结果`、`附件`。
  - 表格上方放一小块紧凑元信息：考生、场次 / 试卷、答卷状态、答题时长、导出说明。
  - `结果` 做信息收敛，一格写清 `正确` / `错误` / `部分正确` / `已阅，本题不参与人工阅卷`，有分数评语就带上 `得分：8/10`、`评语：…`。
  - `附件` **只有简答题和 AI 实战题可能有值**，写原始文件名 + `attachments/xxx.zip` 相对超链接，**不展开压缩包内部清单**；客观题与代码题该格写「无」或留空，**不要写"缺失/异常"**。
- **多考生**：同一张表往下追加行，最左边加 `考生` 列，仍然只有一个 Sheet。
- **长文本**（简答正文、代码、AI 对话）放摘要 + 关键片段；要完整原文时另存 `.md`/`.txt` 并在单元格里链接，**不要为此新增 Sheet**。
- **用户提供模板时模板优先**：用其主工作表，保留表头、列顺序、字体、列宽、冻结行等既有样式，把字段映射进模板列。模板没有的字段默认不加，**不新增 Sheet、不擅自加列**。
- 用户明确要求更全的字段时才扩展为：`考生姓名`、`总分`、`题号`、`题目`、`题型`、`提交答案`、`满分`、`得分`、`阅卷人`、`评语`、`阅卷时间`。

#### 1. 执行链路与筛选顺序

```text
exam_venue_detail2(examVenueId)
  → 按 examinees[].statusName 筛选（未指定时默认“已出分”）
  → 逐个 queryResult(receiptId)，以 testContentVO[] 为唯一逐题来源
  → 若指定题型：按 questionType 过滤导出行
  → 规范化题目、提交答案、阅卷人、评分、评语
  → 下载附件到工作簿旁的 attachments/（仅 short / aiCoding 两类题型有）
  → Excel：单工作表（默认）
  → 有附件时另打一体化 ZIP（工作簿 + attachments/）
```

- 用户指定考生时，先按姓名或 `examReceiptId` 过滤；未指定时保留该场次全部“已出分”考生。
- 用户指定题型时，**只筛选 Excel 明细行**，不修改原始分数、评语或评分状态；结果中明确写出筛选条件和导出人数。

#### 2. 题型筛选映射

| 用户表述 | `questionType` 筛选值 |
|---|---|
| 单选题 | `radio` |
| 多选题 | `multiple` |
| 判断题 | `judgment` |
| 填空题 | `blank` |
| 简答题 / 问答题 | `short` |
| 代码题 | `code` |
| AI 实战题 | `aiCoding` |
| 主观题 | `short`、`code`、`aiCoding` |
| 客观题 | `radio`、`multiple`、`judgment`、`blank` |

#### 3. “提交答案”字段映射（硬规则）

| 题型 | 原始答案字段 | 可读导出规则 |
|---|---|---|
| 单选 `radio` | `studentAnswer[]` 的 `optionId` | 通过 `questionContent.radioOptionList[]` 按 `optionId` 映射到 `describe`；可加选项序号。**禁止导出裸 optionId**。 |
| 多选 `multiple` | `studentAnswer[]` 的 `optionId` | 通过 `questionContent.multipleOptionList[]` 映射到每个 `describe`，多项用分号连接。**禁止导出裸 optionId**。 |
| 判断 `judgment` | `studentAnswer[]` 的 `optionId` | 通过 `questionContent.judgmentOptionList[]` 映射为“正确”或“错误”。若无法映射，标注“选项映射缺失”，不得写原始 ID 充数。 |
| 填空 `blank` | `studentAnswer` | 优先读取每空的 `blankAnswer`，其次 `text`；保留空序号。字段结构不符时如实标注“答案结构待核验”。 |
| 简答 `short` | `studentAnswer` | 生产 `queryResult` 优先读取 `studentAnswer.answer`；兼容旧返回才读取 `studentAnswer.text`。附件优先读取 `attachment[]`，兼容 `attachments[]`；文本为空且有附件时标注“未提交文本，含 N 个附件”，两者都空则标注“未提交答案”。 |
| 代码 `code` | `studentAnswer.sourceCode` | 导出源码；长度过大可截取并标注字符数，不能误报为“无答案”。**代码题没有平台附件**，要独立文件是我们自己另存，不是下载来的。 |
| AI 实战 `aiCoding` | `studentAnswer.workspace` + `conversations[]` + `deliverableUrl` | 目标 A：导出工作空间标识与会话摘要，完整对话另存文件并链接；目标 B：**完整对话逐条落盘**（role + content + 时间）。交付物 ZIP 走 `deliverableUrl`。**都不要**为此新增 Sheet。 |

> `题目`优先用 `title`，为空则用 `titleRich` 去 HTML 后的纯文本；`阅卷人`=`markPaperStaffName`，`评分`=`score`，`评语`=`remark`，`满分`=`questionScore`。这些字段空值必须保留为空，不得凭阅卷状态推断。

> 🔴 **空值即事实**：`score=null` / `totalScore=null` / `scoreFlag=false` 一律原样保留或用一句话说明，**绝不补 0、不倒推、不臆造**。实测存在 `scoreFlag=false` 且 `totalScore=null` 的作业型场次，此时不要编造总分。

#### 4. 交付前校验（必做）

1. 校验每位考生的 `queryResult` 返回 `status=200`，且 `markStatus` 与场次里该考生的 `statusName` 一致；失败考生单列清单，不可静默遗漏。
2. 对每个**被导出题型**至少抽查一行：判断题已显示“正确/错误”，选择题已显示选项文案，简答题已显示 `answer` 正文或明确的缺失说明，代码题有源码，AI 实战题有对话内容或 EMPTY/FAILED 标注。
3. 校验明细行数 = 成功获取成绩单的考生数 × 命中筛选的题数之和；单人单场次时行数应等于 `testContentVO` 长度。
4. 若某题的答案结构无法识别，保留原题、得分、评语，并把“提交答案”写为“答案结构待核验”；不得输出内部 optionId、空字符串或猜测的答案。
5. 用 `openpyxl` 重开工作簿确认可读、超链接 target 正确、**默认情况下只有 1 个工作表**。
6. 附件全部落盘且 `file` 判定为有效 ZIP；一体化 ZIP 内含工作簿 + 全部附件，保持相同相对目录。
7. **附件数口径核对**：应等于 `Σ(简答题 attachment[] 长度) + Σ(AI 实战题 deliverableUrl 非空数)`。客观题与代码题**不计入**；卷子没有这两类题时附件数为 0 属正常，不要报异常。

### ★ 目标 B 专属：评审套件交付规范

目标 B 的用户要**坐下来逐题看完、然后自己打分**，所以核心是「作答全文可读 + 打分位留好」。目录结构：

```text
<考生>_评审套件/
├── 00_评分表.xlsx            ← 主交付：按用户维度留空待填
├── 01_答卷全文.md            ← 逐题：题干 / 作答全文 / 参考答案 / 平台原评
├── answers/                  ← 需要独立打开的作答正文（我们自己另存，非平台下载）
│   ├── Q4_简答.md            ← 简答正文
│   ├── Q5_代码.py            ← 代码题源码（来自 sourceCode，不是附件）
│   └── Q6_AI实战_对话记录.md  ← 来自 conversations[]
├── attachments/              ← 平台原始附件，**只会来自简答题 + AI 实战题**
└── extracted/                ← 附件解包后的可读内容
    └── <附件名>/
        ├── _文件清单.md
        └── <解出的源码 / 文档>
```

> 🔒 `attachments/` 与 `extracted/` **只装简答题附件和 AI 实战交付物**。客观题不会有；代码题的源码走 `answers/`，别塞进 attachments。若这份卷子两类题都没有附件，**这两个目录可以不存在**，不是缺漏。

`00_评分表.xlsx` **单表**，列固定为：

| 题号 | 题型 | 题目 | 考生作答（摘要 + 全文链接） | 平台原评（参照） | 维度 1 | 维度 2 | … | 本题得分 | 评语 |
|---|---|---|---|---|---|---|---|---|---|

- **维度列按用户确认的维度动态生成**，表头带权重，如 `技术方案合理性(0.30)`。
- 维度格、本题得分、评语**全部留空**等用户填；可加数据校验限定 1-5 或 0-满分。
- `平台原评` 列名明确写「平台原评分（仅参照）」，**绝不当成结论**。
- 表尾留加权汇总**公式**（改分自动重算），不要写死数值。

`01_答卷全文.md` 每题一段，固定结构：

```markdown
## 第 N 题【题型】满分 <questionScore>

### 题目
<题干全文>

### 评分参考（平台提供）
<scoreReference / 参考答案；没有就写「平台未提供」>

### 考生作答
<全文，不截断；简答/AI 实战有附件时写「作答在附件：xxx.zip，已解包至 extracted/xxx/」；代码题写源码本体或指向 answers/ 里的文件>

### 平台原评（仅参照）
得分：<score>/<questionScore>｜阅卷人：<markPaperStaffName>｜评语：<remark>
```

附件解包规则（只针对简答题附件与 AI 实战交付物）：

- ZIP 一律解到 `extracted/<附件名去后缀>/`，生成 `_文件清单.md`（路径 + 大小 + 类型）。
- **区分脚手架与真实产出**：`examples/`、模板 HelloWorld、`.gitignore` 等标注「疑似初始模板，通常不计分」；考生新增的源码 / 文档 / 产物标注「考生产出」——**这才是重评该看的部分**。
- 二进制（图片 / 可执行 / 权重文件）只记类型和大小，**不打印字节**。
- 解包失败或加密时保留原 ZIP 并明确说明，不阻断交付。

最后打一个 `<考生>_评审套件.zip` 作为主交付。

**两个目标都要时**：Excel 做索引、套件做正文，Excel 里的 `附件` / `全文` 列直接链到套件对应文件，避免内容重复两份。

### ⚠️ 附件与 AI 实战交付物下载规范（以真实阅卷记录为准）

**核心原则：下载与处理分家，二进制绝不进对话。**

#### 🔒 附件只有两个来源（硬约束 · 先记住这条）

**成绩单里只有简答题和 AI 实战题可能有附件，其余题型一律没有。**

| 题型 | 附件字段 | 有无附件 |
|---|---|---|
| `short` 简答 | `studentAnswer.attachment[]`（旧结构 `attachments[]`） | **可能有**（0~多个），取决于 `questionContent.allowUpLoadFile` |
| `aiCoding` AI 实战 | `testContentVO[].deliverableUrl`（工作空间 ZIP） | **可能有**，归档未生成时为 `null` |
| `radio` / `multiple` / `judgment` / `blank` 客观题 | —— | **绝对没有** |
| `code` 代码题 | —— | **没有独立附件**，作答就是 `studentAnswer.sourceCode` 文本 |

推论（决定怎么写代码和怎么说话）：

1. **只在这两种题型上找附件**。遍历 `testContentVO[]` 时，客观题和代码题**不要去读 `attachment` / `deliverableUrl`**，也不要因为字段为 `null` 就报"附件缺失"——它们本来就没有。
2. **两个来源字段名不同、不能混用**：简答走 `studentAnswer.attachment[]`，AI 实战走 `testContentVO[].deliverableUrl`。别拿简答的字段去找 AI 实战的交付物，反之亦然。
3. **代码题不要去下载文件**：源码直接在 `studentAnswer.sourceCode` 里，要独立文件是**我们自己另存**（如 `Q5_代码.py`），不是从平台下载来的。
4. **"这份卷子没有附件"是正常结论**：全客观题的卷子、简答题没上传文件的卷子，附件数就是 0。Excel 的 `附件` 列写"无"，不要提示异常。
5. **附件数怎么算**：`Σ(简答题 attachment[] 长度) + Σ(AI 实战题 deliverableUrl 非空数)`。报数时按这个口径，别把代码题算进去。
6. 简答题**文本为空但有附件**是常见形态（实测存在），此时作答实体就在附件里——**必须下载**，不能只写"未提交答案"。

#### 下载链路

两个来源都是 COS 预签名 URL，落盘方式一致：

```text
queryResult({receiptId})
  → 遍历 testContentVO[]，只对 short / aiCoding 两类取附件：
      · short    → studentAnswer.attachment[].url
      · aiCoding → testContentVO[].deliverableUrl（为 null 才调 downloadAllFiles 触发打包）
  → curl -L --fail --silent --show-error "<整段原始 URL>" -o "<dir>/<name>.zip"
  → file "<dir>/<name>.zip"     # 期望 Zip archive data，防 HTML 登录页/错误页
  → deliverable_processor.py --zip ... （需要离线解析时）
```

🔴 **URL 必须整段原样使用**：`q-signature` 是 **40 位小写 hex**，`q-ak` / `q-sign-time` / `q-key-time` 一个字符都不能错。不要手敲、不要截断、不要"看起来一样"就复用。

#### 403 分因处置（实测踩坑，两种 403 处理方式不同）

```text
curl 返回 403
   ↓
① 签名格式：q-signature 长度 == 40 且全为 hex？
   ├─ 否 → 【抄错/截断】用响应里的原串重发 curl，不必重取接口
   └─ 是 ↓
② 时间窗：q-sign-time 的结束时间戳 vs 当前时间（date +%s）
   ├─ 已过期 → 【真过期】重新调 queryResult 拿新 URL 再下
   └─ 未过期 ↓
③ URL 完整性：q-ak / q-key-time / q-url-param-list 与响应一致？
   ├─ 有差异 → 【URL 被改写】用原串重发
   └─ 全一致 → 【权限或对象不存在】如实告知用户，不要盲目重试
```

| 现象 | 病因 | 处理 |
|---|---|---|
| `q-signature` 不是 40 位 hex | 复制时截断 / 漏字符 | 用原串重发 curl，**不用**重取接口 |
| 签名格式对，但 `q-sign-time` 结束时间已过 | 真过期 | 重调 `queryResult` 换新签名 |
| 同一批 URL 里有的能下、有的 403 | 大概率是那条抄错了 | 逐条比对该条 URL |
| 重取接口后仍 403 | 权限 / 对象不存在 | 停止重试，告知用户 |

硬规则：

1. **`q-sign-time` 时间窗实测 1800 秒（30 分钟）**，格式 `<起始>;<结束>`，两端 Unix 秒。判过期用 `date +%s` 比对，不要靠感觉估。
2. 换签名的**唯一正确方式**是重新调 `queryResult`。
3. **禁止**手改 `q-sign-time` / `q-signature` / `q-key-time` 试图"续期"——签名与这些参数强绑定。
4. **禁止**对同一 URL 无脑重试：403 是确定性拒绝，不是网络抖动。
5. 批量下载逐条记录成败，某条失败**只重取该条**，不整批重来。
6. **先下载、后排版**：签名只有 30 分钟，不要先慢慢排 Excel 最后才下载。
7. 文件名含空格或括号（如 `persistentKV (1).zip`）时落盘名做安全化处理，但表格里显示原始名。

> ⚠️ 标准 `.xlsx` 无法把 ZIP 二进制真正嵌进单元格。用「相对超链接 + 同目录 `attachments/` + 一体化 ZIP」，**不要宣称附件已嵌入 Excel**。

#### 历史链路参考（阅卷视角）

```text
todo_mark_list
  → 选中一条记录，拿 markPaperId + examReceiptId
  → todo_mark_detail(markPaperId, receiptId)，拿阅卷详情/评分参考
  → queryResult({receiptId})，拿 conversations + testContentVO[].deliverableUrl
  → curl -L -o workspace.zip "{deliverableUrl}"
  → deliverable_processor.py --zip workspace.zip ...
```

> 如果某版本的 `todo_mark_detail` 真实响应也直接带交付物 URL，可以直接复用；以实际响应字段为准。当前已验证的稳定字段是 `queryResult` 中 AI 实战题的 `deliverableUrl`。

**第一步·下载到本地（二进制不进对话）**：
- **首选：**使用详情/成绩单返回的 COS 预签名 URL，直接 `curl -L -o` 落盘；URL 自带时效签名，通常不需要额外 OA Cookie。
- **备用：**客户端/平台侧走 MCP，把二进制响应直接写文件；不能让响应正文回传模型。
- **再备用：**带 OA Cookie 的子进程走业务直链：`python downloader.py --receipt-id <id> --question-id <id> --output ./deliverables/<receiptId>_<name> --overwrite`。

> ⚠️ `mcp_call_tool` 本身无落盘参数，直接 `CallAPI(downloadAllFiles)` 会把 ZIP 回传到上下文；裸 `curl` 业务直链若没有 OA 登录身份会得到 HTML 登录页而不是 ZIP。**但有 COS 预签名 URL 后可绕开这两个问题。**

**第二步·离线解析（只读、不打印二进制）**——用 `deliverable_processor.py`：

```bash
# 解析本地 ZIP：解压 + 区分模板/产出 + 抽取可读内容 + 生成评分材料
python deliverable_processor.py --zip ./elio.zip --output ./deliverables/elio \
  --scoring-prompt --scoring-output ./deliverables/elio/_scoring.md --question "<题目>"
# 或直接解析已解压目录
python deliverable_processor.py --dir ./deliverables/elio
```

脚本会**自动区分**：`examples/` 下 HelloWorld 等 = 工作空间初始模板（不计分）；`gen_ppt.py`/`投资分析报告.pptx` 等 = 考生真实产出（**仅此计入 R1 交付质量**）；根目录 `README.md`/`.gitignore` 标注"疑似脚手架、人工复核"。图片等二进制文件只记录类型和大小，绝不打印字节。

**接口改进建议（治本）**：让 `downloadAllFiles`/`queryResult` 直接返回 302 里的 **COS 预签名 URL**（而非跟随重定向回传二进制）。COS 预签名 URL 自带时效签名、无需任何身份，子进程 `curl` 即可落盘——一举解决"污染上下文"与"子进程无太湖身份"两个问题。

### 报告结构建议（每人一份）

```
考生：{name} · 场次：{venueName} · 答卷ID：{receiptId} · 作答状态：{statusName}
──────────────────────────────────────────
一、客观题结果（只呈现对错，不重评）
    第N题 [题型] 对/错/部分 · 得分 x/y
    客观题正确率：X/Y
二、主观题重评（按自定义维度）
    维度表：{维度名 · 权重 · 得分 · 评语}
    逐题：题干摘要 / 考生答案要点(含AI实战对话记录) / 亮点 / 不足 / 该题得分
三、综合结论
    主观题加权总分、等级(A+/A/B/C/D)、整体亮点/不足/建议
    （可选）与平台原评分的差异对比
```

### 落地示例（真实实测数据）

```
用户: 把「投资分析岗·AI实战」这个场次的考生，用「AI协作能力」维度重评

AI:
  [确认 4 件事：场次 / 评谁 / 维度=AI协作能力(可微调) / 只重评主观题 ✅]

  Step1 CallAPI(todo_mark_list, {})
        → examVenueId=2077231970580037634

  Step2 CallAPI(exam_venue_detail2, {"examVenueId":"2077231970580037634"})
        → totalCount=3, examinees:
          · leilei  (2077232229267931138)  已出分  ← 重评典型
          · elio    (2077262954825441282)  阅卷中
          · sihang  (2077232092651061250)  阅卷中
        展示清单，让用户挑（默认从"已出分"里选）

  Step4 对选中的 receiptId:
        CallAPI(queryResult, {"receiptId":"2077232229267931138"})
        → 拿 testContentVO[]（含 aiCoding 的 conversations 对话记录）
        （需代码文件时）CallAPI(downloadAllFiles, {examReceiptId, questionId})

  Step5 拆题型：客观题取 trueAnswer/score；AI实战题按 AI协作能力4维度重打

  Step6 python main.py json-report --input 评估.json \
          --output ./report_{receiptId}_{name}.html --title "{name}·AI协作能力重评"
```

---

## 附录：HTTP+Cookie 模式（A / B / C）

> 供外部脚本/批量处理，需手动提供 OA Cookie。CodeBuddy 内优先走上面两条 MCP 路线。

### 模式 A：HTTP 数据获取

```bash
# A1 待办列表
python plugins/txzhaopin/skills/quiz-deliverable-evaluator/main.py quiz \
  --url "https://quiz.woa.com/api/.../todoList" --cookie "$QUIZ_OA_COOKIE" --pretty

# A2 成绩单
python plugins/txzhaopin/skills/quiz-deliverable-evaluator/main.py quiz \
  --url "https://quiz.woa.com/api/.../transcript/123" --cookie "$QUIZ_OA_COOKIE" \
  --pretty --output ./transcript.json
```

### 模式 B：自定义维度 AI 报告

```bash
python plugins/txzhaopin/skills/quiz-deliverable-evaluator/main.py quiz \
  --url "https://quiz.woa.com/api/.../transcript/123" --cookie "$QUIZ_OA_COOKIE" \
  --report --dimensions '[{"name":"技术方案合理性","weight":0.30,"description":"..."}]' \
  --report-title "候选人技术能力评估" --report-output ./evaluation_prompt.md
```

常见场景维度参考：

| 场景 | 推荐维度 |
|------|---------|
| 技术笔试 | 技术准确性、解题思路、代码质量、边界覆盖、时间效率 |
| 设计题 | 方案合理性、技术选型、扩展性、文档质量、创新性 |
| 行为面试 | 逻辑清晰度、案例匹配度、反思深度、沟通表达、价值观契合 |
| 算法题 | 正确性、时间复杂度、空间复杂度、可读性、测试覆盖 |

### 模式 C：交付物评分

```bash
python plugins/txzhaopin/skills/quiz-deliverable-evaluator/main.py deliverable \
  --url "https://quiz.woa.com/api/questionCodeBuddy/downloadAllFiles/{id1}/{id2}" \
  --cookie "$QUIZ_OA_COOKIE" --output ./evaluations/candidate_q1 --overwrite

python plugins/txzhaopin/skills/quiz-deliverable-evaluator/main.py deliverable \
  --dir ./evaluations/candidate_q1 --analyze-only --scoring-prompt \
  > ./evaluations/candidate_q1/_scoring_prompt.md
```

评分维度：代码质量 25% / 功能完整度 30% / 可运行性 20% / 文档产物 15% / 工程素养 10%。
评分等级：A+ ≥ 95 | A 85-94 | B 75-84 | C 60-74 | D < 60。

---

## 路线一 vs 路线二（都走 MCP，别混）

| | 路线一（辅助阅卷） | 路线二（归档 / 重评） |
|---|-------------------|---------------------|
| 入口 | `todo_mark_list` | 场次 URL / 场次名 → `exam_venue_detail2` |
| 成绩状态 | 待批阅 status=0 | 已有作答（已交卷 / 阅卷中 / 已出分） |
| 主要接口 | mark_list + mark_detail(+queryResult 取 AI 对话) | venue_detail2 + queryResult(+ COS 预签名 URL 落盘) |
| AI 给分 | ✅ 给**建议分+理由**，不提交系统 | A 不给分；B 默认只备料，要建议分须标注 |
| 客观题 | 待办里无客观题 | 只取对错、不重评 |
| 产出 | 逐题「阅读简报 + 建议分」 | A：单表 Excel + 附件包；B：评审套件 + 空白评分表 |
| 触发词 | "帮我读待阅卷的题、给建议分我来提交" | "导出成绩单做成 Excel" / "下载全部作答我自己重评" |

🔴 **速判**：要不要产出本地文件 —— 要文件走路线二；只在对话里读题给建议分走路线一。

---

## 常见问题

### 1. MCP 调用失败 / apiId 找不到
自行构造了 apiId 或跳过 SearchAPI 第①步 → 严格走三步流程，apiId 从 SearchAPI 结果原样复制。

### 2. 成绩单接口返回空
receiptId 不正确 / 答卷未提交 / 无权限 → 先用 `exam_venue_detail2` 或 `todo_mark_list` 确认 receiptId。**最常见的错是把 `examVenueId`（场次）当成 `receiptId`（答卷）传进去。**

### 3. 阅卷详情返回权限错误 / canJudgeFlag=false
该阅卷单未分配给当前用户或已完成 → 提示无权限、跳过，或回退到成绩单查看。

### 4. AI 实战题对话记录取不到
`todo_mark_detail` 的 studentAnswer 本就为空 → 改用 `queryResult` 取 `conversations`；若 `conversationsFetchStatus=EMPTY` 表示考生确实未产生会话，如实说明。

### 5. 想查"阅卷已办"
`todo_mark_list` 固定只查待办（status=0），**无已办列表接口**。已批阅的卷子只能凭 `receiptId` 用 `queryResult` 单查（对 marked 状态可正常返回）。

### 6. 附件下载报 403
**先分因再处理**：`q-signature` 不是 40 位 hex → 抄错/截断，用原串重发；格式对但 `q-sign-time` 结束时间已过 → 真过期，重调 `queryResult` 换新 URL。详见「403 分因处置」。**同一批里有的能下有的挂，几乎必是那条抄错了。**

### 7. 用户问"这个场次有没有完成的试卷"
用 `exam_venue_detail2` 拉全部考生，按 `statusName` **分开报数**：已交卷 / 阅卷中 / 已出分是三种不同状态，不要笼统说"有 N 份完成"。

### 8. 某道题找不到附件字段
先看题型：**只有 `short` 简答和 `aiCoding` AI 实战会有附件**。客观题（`radio`/`multiple`/`judgment`/`blank`）没有附件位；`code` 代码题的作答是 `studentAnswer.sourceCode` 文本，也没有附件。这些题型读不到 `attachment` / `deliverableUrl` 是**正常的**，不要报错、不要重试、不要提示"附件缺失"。

### 9. 简答题 `answer` 是空字符串
不等于没作答。实测存在**文本为空、作答实体全在附件里**的情况（考生把内容打包成 ZIP 上传）。此时必须下载 `attachment[]` 才拿到真实作答；Excel 里标注「未提交文本，含 N 个附件」，不要写成"未提交答案"。

---

## 注意事项

- 本 skill 涉及考试敏感信息，评估/阅卷/导出完成后建议清理本地临时文件；OA Cookie 通过环境变量 `QUIZ_OA_COOKIE` 传入。
- MCP 调用必须严格遵守三步流程：SearchAPI → SearchAPI(apiId) → CallAPI。
- **MCP 阅卷接口全只读**：`todo_mark_list`/`todo_mark_detail`/`queryResult`/`exam_venue_detail2` 均无写回分数的能力，AI 永远只给建议，落库由阅卷官手动完成。
- **本 skill 是测验平台唯一入口**：阅卷、场次/考生查询、Excel 导出、附件下载、自定义重评全在这里，不要新建或调用别的 `quiz-*` / `exam-*` / `transcript-*` skill。
- **路线一（辅助阅卷）**：产出「阅读简报 + 建议分」；建议分必须标注"仅供参考、请到系统提交"；考生答案取不到时如实说明缺失，**严禁凭题目臆造**。
- **路线一考生答案硬约束**：简答=文本(必)+附件(可选)；代码=源码文本 `sourceCode`(必)、**无附件**；AI实战=对话记录(必，`todo_mark_detail` 为空需 `queryResult` 取 `conversations`)+交付物 ZIP(可选)。
- 🔒 **附件只出自简答题和 AI 实战题**：客观题（单选/多选/判断/填空）没有附件位，代码题的源码是文本字段不是附件。**不要在这些题型上找附件、也不要报"附件缺失"**；附件数口径 = Σ(简答 `attachment[]`) + Σ(AI 实战 `deliverableUrl` 非空)。全客观题的卷子附件数为 0 属正常。
- **路线二先认目标**：目标 A 整理归档（可读优先、单表 Excel、附件给链接）vs 目标 B 自定义重评（完整优先、全文落盘、附件解包、分数格留空）。没明说时反问一句，别猜。
- **路线二共性**：考生列表走 `exam_venue_detail2`；客观题只取对错、不重评；自定义维度只作用于主观题；**不要把平台原有主观题得分当作结论**；默认一个个来、每人单独一份，文件名带 receiptId+姓名。
- **Excel 默认单工作表**：不拆多 Sheet；用户给模板则模板优先，不擅自加列加表。
- **附件与交付物下载**：**只有简答题（`studentAnswer.attachment[].url`）和 AI 实战题（`testContentVO[].deliverableUrl`）两个来源**，首选 COS 预签名 URL `curl` 落盘；签名仅 30 分钟，**先下载后排版**；403 先验签名长度再验时间窗；禁止让 ZIP 二进制回传对话；自动区分「初始模板」与「考生真实产出」。
- **空值即事实**：`score=null` / `totalScore=null` / `scoreFlag=false` 原样保留或说明，绝不补 0。
- 自定义维度权重总和建议为 1.0，避免评分比例失真。
- 最终判定应由面试官/考官/阅卷官确认。
