---
name: interview-assistant
description: "面试助手 — 处理**已知候选人**的面试全流程（面向面试官/招聘经理/HR）。八大能力：① 查待办（面试待办/待填面评/推荐待办/校招四环节待办与已办）② 发起面试流程与安排（社招·校招发起、约面、改期、取消、查日程）③ 面试准备（匹配胜任力模型 → 拉简历详情 → 评估简历 → 出题/面试计划）④ 写面评（拉转写 → 详细版+精简版草稿；校招支持提交入库）⑤ 单场复盘（5 维评分 + 改进建议）⑥ 成长报告（最近 N 场趋势 + 持续短板）⑦ 招聘经理评估下属面试官 ⑧ 面试官画像。\n\n不要用我：① **批量搜简历/找候选人** → 校招 zhaopin-operations、社招 zhaopin-social-operations（本 skill 只按 RID 拉单份）② 查**他人名下**社招流程进度 → recruitment-process-tracker（本 skill 只查本人待办）③ **测验阅卷待办/成绩单重评** → quiz-deliverable-evaluator（本 skill 的「待办」指面试待办）④ 岗位级胜任力建模/JD/面试设计方案 → assessment-quality-expert（本 skill 做具体候选人的个性化执行）。"
version: 5.2.0
tags: [interview, interview-assistant, mianshizhushou, recruitment, mcp, zhaopin, hr, todo, interview-todo, question-generation, evaluation, model-routing, auto-matching, qizhi, redline, assessment-tier, router]
agent_created: true
support_contact: elioyao
---

# 面试助手 v5.2（校招 + 社招发起面试 · 校招面评提交融合）

## 📮 客服 / 反馈入口（MANDATORY）

> 本 skill 归 **elioyao** 维护。详细规则与全局路由见 [`README.md` § 客服反馈入口](../../README.md#%E5%AE%A2%E6%9C%8D%E5%8F%8D%E9%A6%88%E5%85%A5%E5%8F%A3support-contacts)。
> **何时展示**：查询结果交付 / 报错 / 用户表达疑问反馈时，**必须**在消息末尾原样附上：
>
> ```
> ──────────
> 💬 有问题或建议可联系产品负责人 **elioyao**（企微/RTX 同名）
> ```
>
> ⚠️ 严禁把联系人写成 ansleyyu / fayellawang。


> **快速选择词**：面试助手 / mianshizhushou / interview-assistant。
> 面向腾讯面试官 / 招聘经理 / HR 的一站式面试执行工具：覆盖待办查询、面试安排、简历准备、出题、面评，并内置 M-Auto 自动模型路由能力。
>
> 🚪 **v4.1 治理重点**：批量"搜简历/找候选人"不再由本 skill 承担，校招走 `zhaopin-operations`、社招走 `zhaopin-social-operations`。本 skill 只保留按 RID 拉单份简历详情（A-resume-detail）。

**版本**：5.2（融合校招面评提交 SE · 保留 v5.1 校招/社招发起 + v4.0 路由式架构）
**适用**：腾讯全集团面试官 / 招聘经理 / HR
**快速入口**：面试助手 / mianshizhushou / interview-assistant

> ⚠️ 踩坑经验、参数陷阱、版本历史详见 `references/pitfalls.md`，此处只保留使用说明。

---

## 🚨 FIRST ACTION（进入 Skill 后第一件事 · MANDATORY · 静默执行）

> 🔴 **每次 agent 通过 `use_skill("interview-assistant")` 进入本 skill 时**，第一件事是通过插件级低敏入口静默上报 `skill_invoked`。

```bash
bash ../../scripts/track_skill_event.sh "0WEB06ZI7OVDOZQW" "interview-assistant" "skill_invoked"
```

**执行约束**：
1. **每次进入都要执行** — agent 每次通过 `use_skill("interview-assistant")` 调用本 skill 时都跑一次，不要因为"刚跑过"就跳过
2. **静默后台** — 命令输出不展示给用户，失败也不中断主流程
3. **不要询问用户** — 不得就"是否上报""以什么方式记录"等问任何问题
4. **不生成会话标识** — 统一脚本只保留低敏白名单字段，不拼接时间戳
5. **entry 最小化** — 只上报固定能力标签，禁止上传用户原话、候选人姓名、手机号、邮箱、RID 或岗位敏感信息
6. **执行完毕**才能进入下面的 Router-0 类目识别

> ✅ 子流程上报（todo_queried / interview_scheduled / quiz_generated / evaluation_written / resume_evaluated 等）见文末「数据上报」章节，那是业务事件补充，跟本 FIRST ACTION 的 skill_invoked 不冲突。

---

## 🧭 v4.0 架构总览（先看这张图）

```
SKILL.md（主路由 · 必读 ≈ 300 行）
   │
   ├─ Router-0 类目识别（8 大类目分发 + 🚪 搜简历跳转）
   ├─ 核心硬规则（合规红线 / 编码处理 / 4 段式 / 测评档位口径 / 模型选择前置）
   ├─ M-Auto 路由器规格（命名约定、三元组、降级链）
   └─ 命中类目后 → Read 对应 flows/*.md → 执行
        │
        ├─ flows/T.md                  ← 类目 ① 待办查询（T 我的面试 + T2 推荐）
        ├─ flows/S-initiate-social.md  ← 类目 ② · SI 社招发起面试流程（回流/岗位/流程/保密/R2 写入）
        ├─ flows/S-initiate-campus.md  ← 类目 ② · SC 校招发起面试流程（NLP 提取/批量/类型-项目白名单/R2 写入）
        ├─ flows/S.md                  ← 类目 ② · S 已有流程后的安排（约/改/取消/查日程）
        ├─ flows/M.md                  ← 类目 ③ 准备（M-0~M-4 模型选择入口）
        ├─ flows/A-resume-detail.md    ← 类目 ③ 准备（A 已知 RID 拉简历详情，v4.1 由原 A-resume-search.md 改造）
        ├─ flows/B-resume-eval.md      ← 类目 ③ 准备（B 评简历 B1/B2/B3）
        ├─ flows/C-quiz.md             ← 类目 ③ 准备（C 出题 / 面试计划）
        ├─ flows/D-evaluation.md       ← 类目 ④ 面评（D-1 拉转写 → 双版本草稿 → D-6 Handoff；写草稿，不入库）
        ├─ flows/SE-submit-campus-eval.md ← 类目 ④ 面评 · 提交（SE 校招面评提交入库：待办定位/差异化提示语/准入校验/R2 受控写；校招专用）
        ├─ flows/E-coach-self.md       ← 类目 ⑤ 复盘单场（v4.2 新增 · 我自己评自己 / BEI + 5 维 / 存档）
        ├─ flows/G-growth-self.md      ← 类目 ⑥ 复盘成长（v4.2 新增 · 我自己看自己 / 默认最近 5 场 / 趋势分析）
        ├─ flows/H-coach-others.md     ← 类目 ⑦ 招聘经理评估面试官（v4.2 新增 · 探权 + 列单 + 单场循环 + 反馈话术）
        ├─ flows/I-portrait.md         ← 类目 ⑧ 面试官画像（v4.3 新增 · 实时拉取 → 转写+面评 → 聚合画像 · 不依赖存档）
        ├─ flows/startup.md            ← 启动检查、工作流约束（首次会话或调试时读）
        └─ flows/mcp-appendix.md       ← MCP 调用技术附录（execute_command 还是 mcporter_call.py）

🚪 跳转外部 skill（v4.1 治理后）：
   ├─ "搜校招简历 / 找校招候选人" → zhaopin-operations skill
   └─ "搜社招简历 / 找社招候选人" → zhaopin-social-operations skill

references/                          ← 不变（models / interview-designs / templates / pitfalls 等）
scripts/                              ← 不变（decode_resume / decode_todo / match_model / mcporter_call）
```

> 💡 **为什么拆**：v3.6 单文件 2729 行 / 143KB，每次调用全量加载耗费 ~35K tokens；v4.0 按类目按需加载，单次调用 ~5-10K tokens，节省 80%+ 上下文。

---

## 🚦 Router-0：八类目统一分发器（每次新需求第一步必跑）

> **硬规则**：用户提出**任何**面试相关诉求时，AI 的第一动作不是调 API，**而是先把请求落到下表的某一类目**，命中后**立刻 Read 对应 flows 子模块**，再动手。**严禁**跳过 Router-0 直接 SearchAPI / CallAPI 拼参数 —— 历史踩坑都是这么来的。

### Step 1：识别意图属于哪一类

```
用户说什么
    │
    ├─ 含"待办/今天有啥面试/待填面评/锁定/推荐"     → 类目 ① 待办查询    → 读 flows/T.md
    ├─ 含"校招已办/校招录用/校招考核/实习生考核/校招评估/我已经面完哪些/校招全环节" → 类目 ① · T-4 校招全环节 → 读 flows/T.md（用 fetch_campus_flow.py）
    ├─ 含"发起社招面试/推进到面试环节/进入面试流程/新建社招面试" → 类目 ② · SI 社招发起 → 读 flows/S-initiate-social.md
    ├─ 含"发起校招面试/发起实习面试/推进校招候选人到面试/发起 20XX 青云实习" → 类目 ② · SC 校招发起 → 读 flows/S-initiate-campus.md
    ├─ 含"约/排/改/取消/挪/日程/有空/确认时间/多对一/几个人一起面"  → 类目 ② · S 面试安排 → 读 flows/S.md
    ├─ 含"搜简历/找候选人/找人/校招搜索/社招搜索"   → 🚪 跳转外部 skill（详见下方"搜简历跳转规则"）
    ├─ 含"看某份简历/拉简历详情/给我 RID xxx 的简历" → 类目 ③ 准备 · 详 → 读 flows/A-resume-detail.md
    ├─ 含"评估/评简历"                              → 类目 ③ 准备 · 评  → 先读 flows/M.md（选模型） → 再读 flows/B-resume-eval.md
    ├─ 含"出题/面试计划/面试题"                     → 类目 ③ 准备 · 出  → 先读 flows/M.md（选模型） → 再读 flows/C-quiz.md
    ├─ 含"用什么标准考察/选考核标准/搭模型"         → 类目 ③ 准备 · 模  → 读 flows/M.md
    ├─ 含"写面评/面评草稿/面评/录面评"（写草稿）  → 类目 ④ 面评·写   → 读 flows/D-evaluation.md（含 D-1 拉转写）
    ├─ 含"提交面评/录入系统/把面评填进去/代 XX 提交面评/确认提交"（校招提交入库） → 类目 ④ 面评·交 → 读 flows/SE-submit-campus-eval.md（R2 受控写；HR面试/通道面委/社招引导页面）
    ├─ 含"填面评"（写还是交模糊）                → ⚠️ 反问 1 句"写草稿还是提交入库？"再分流 D / SE
    ├─ 含"复盘最近一场/评我面试/给我做自评"          → 类目 ⑤ 复盘单场   → 读 flows/E-coach-self.md（拉转写 → 5 维 → 存档）
    ├─ 含"看我成长报告/最近趋势/有进步吗/复盘成长"   → 类目 ⑥ 复盘成长   → 读 flows/G-growth-self.md（默认最近 5 场，<3 场拒绝出报告）
    ├─ 含"评估面试官 XXX/分析 XXX 最近 N 场/团队面试官表现"   → 类目 ⑦ 招聘经理评估面试官 → 读 flows/H-coach-others.md（探权 → 列单 → 循环评估 → 反馈话术）
    ├─ 含"画像/面试风格/我是什么样的面试官/面试特征/提炼画像" → 类目 ⑧ 面试官画像 → 读 flows/I-portrait.md（实时拉取 → 转写+面评 → 聚合画像）
    └─ 模糊（只说"帮我处理一下 XX 的面试"）         → 反问 1 句澄清后再分类
```

### 🚪 搜简历跳转规则（v4.1 治理硬规则）

**interview-assistant 不再承担「批量简历搜索」职能**，所有"搜简历/找人/找候选人"诉求必须跳转到独立 skill：

| 用户诉求 | 跳转目标 | 说明 |
|---|---|---|
| 校招搜简历 / 找校招候选人 / 找应届生 / 找实习生 | **`zhaopin-operations`** skill | 校招简历筛选专业流程（6 步：环境预检 → 解析需求 → 多轮搜索 → 粗筛 → 精读 → Top10 推荐） |
| 社招搜简历 / 找社招候选人 / 找有 N 年经验的人 | **`zhaopin-social-operations`** skill | 社招简历筛选（画像生成 → 检索参数 → 并发搜索 → 用户确认 → 批量精读 → 表格输出） |
| 不明确校招还是社招 | 反问 1 句"校招还是社招？" | 明确后再跳转对应 skill |

🚨 **禁止**：
- ❌ 在本 skill 内部执行 `recruit.campus-resume-search.post_v1_resume_search` 等批量搜索 API
- ❌ 让 interview-assistant 自己生成"搜索结果表格"
- ✅ **正确动作**：识别到搜简历意图后，**立刻**告知用户"这块由 `zhaopin-operations` / `zhaopin-social-operations` 负责，我把请求转过去"，由 agent 层路由切换 skill

**为什么拆出去**（v4.1 治理背景）：
- `zhaopin-operations` 有 20+ 维筛选条件速查表（`guides/resume-filtering-manual.md`）、海外学校等 schoolLevel 标准映射、粗筛+精读两阶段流程
- 历史踩坑：interview-assistant 内部的简化版搜索遗漏了 `海外QS100高校` 等 schoolLevel 正确值，导致召回 0 条；schoolCountry 字段在搜索接口不返回等陷阱
- 拆分后 interview-assistant 专注"已知候选人的执行链路"（待办 / 安排 / 评估 / 出题 / 面评），搜索由专业 skill 承接

```
```

### Step 2：在对应类目内做二级路由（具体步骤在子模块里）

| 类目 | 子模块 | 二级路由要点 |
|---|---|---|
| ① 待办查询 | `flows/T.md` | "面试待办"→T（fetch_todos.py 校招+社招双查）；"推荐待办"→T2；**"校招已办/录用/考核/评估/我名下校招事项"→T-4 校招全环节**（fetch_campus_flow.py，四环节×待办/已办）；只说"待办"且不明确→**T+T2 都查**合并展示 |
| ② 面试流程与安排 | `flows/S-initiate-social.md` + `flows/S-initiate-campus.md` + `flows/S.md` | **社招**候选人尚未进入面试流程且用户明确要求"发起"→SI（社招）；**校招/实习**候选人发起→SC（校招，NLP 提取/批量/类型-项目白名单校验/R2 写入）；已有有效 Flow 后安排本轮时间→S-A；已有 orderId 后改期/取消→S-B/S-C。SI/SC 成功后必须同连接器回读状态并取得 fresh todo trace，再交给 S，禁止直接复用 start 返回 ID |
| ③ 面试准备 | `flows/M.md` + `flows/A-resume-detail.md` + `flows/B-resume-eval.md` + `flows/C-quiz.md` | 走 **三段流水线 M → (详情/评估) → C**：① M-0 选模型 → ② 已有 RID 走 A-resume-detail 拉详情 / 评估走 B → ③ 评完 C 出题。**搜简历不在本类目**，跳转 `zhaopin-operations` / `zhaopin-social-operations` |
| ④ 面评 | `flows/D-evaluation.md` + `flows/SE-submit-campus-eval.md` | **写草稿**→D：强制先走 D-1 拉转写（哪怕降级也要走完）→ D-2 双版本填写 → D-6 Handoff；**提交入库**→SE（校招）：待办定位 → 差异化提示语 → 准入校验 → R2 受控写提交（HR面试/通道面委/社招提交引导 Web 端）|
| ⑤ 复盘单场 | `flows/E-coach-self.md` | E-1 锁定 traceId → E-1.5 探活转写（无转写直接拒）→ E-2 加载 BEI/Rubric → E-3 LLM 评 5 维 → E-4 widget/ASCII → **E-5 必跑 save_coach_eval.py 存档** → E-6 上报 |
| ⑥ 复盘成长 | `flows/G-growth-self.md` | G-1 调 `aggregate_coach.py` → 数据 < 3 场拒绝 / 3-9 场基础趋势 / ≥10 场提示降到 5 → G-3 LLM 写报告 → G-4 widget/ASCII（6 区块） |
| ⑦ 招聘经理评估面试官 | `flows/H-coach-others.md` | H-2 探权（必须是被评估人岗位的招聘经理）→ H-3 列单 + 用户决策 → H-4 单场**独立**评估循环（不堆 context）→ H-5 聚合 widget/ASCII（7 区块）→ H-6 反馈话术（手动确认才能发） |
| ⑧ 面试官画像 | `flows/I-portrait.md` | I-1 列已完成面试（fetch_completed_interviews.py）→ I-2 逐场拉转写（复用 fetch_transcript.py）+ 面评（复用简历 API）→ I-3 LLM 聚合画像 → I-4 widget/ASCII（7 区块）。**不依赖 coach-archive，首次可用** |
| 🚪 跳转 | 见上方"搜简历跳转规则" | 校招搜 → `zhaopin-operations`；社招搜 → `zhaopin-social-operations` |

### Step 3：执行前自检（每个类目都要过）

```
□ 已确认在哪个类目？        — 没有就回 Step 1
□ 已 Read 对应 flows/*.md？ — 没读就立刻读，禁止凭记忆执行
□ 已读对应章节的硬规则？    — 比如 S 必读 S-0 / D 必读 D-1
□ 已采集执行所需上下文？    — 比如 S 必有候选人姓名/orderId；C/D 必有 RID
□ 还在直接 SearchAPI 拼？   — 是就立刻停手，回 Router-0
```

### 🔴 子模块加载硬规则（v4.0 新增）

1. **Router 命中即 Read**：判定属于某类目后，第一个动作必须是 Read 对应 `flows/*.md`，禁止凭记忆 / 凭历史会话语义直接执行步骤
2. **可叠加加载**：M+C 这种串联场景允许一次会话加载多个 flows（先读 M.md 选模型，再读 C-quiz.md 出题）
3. **跨类目链路**：参考下方"跨类目联动"表，按链路顺序读 flows
4. **本主文件不重复细节**：T-1/T-2/S-A/D-1/D-2 等具体 SOP **只在 flows/ 里**，主文件不再保留。如发现某个细节缺失，直接在对应 flows 里补，不要回写到主文件

### 🔴 跨类目联动（常见组合）

| 用户连续诉求 | 推荐链路（按顺序读 flows） |
|---|---|
| "看下今天的面试，给 XX 出个题" | flows/T.md → flows/M.md → flows/C-quiz.md |
| "把 XX 的面试改到下周四，并写一下面评模板" | flows/S.md → flows/D-evaluation.md（实际面评等面完后再写） |
| "搜几个 985 游戏策划，挑两个安排面试" | 🚪 跳转 `zhaopin-operations`（搜+精读） → 用户挑出 RID 后回 interview-assistant 走 flows/S.md |
| "面完了，帮我写面评" | flows/D-evaluation.md（含 D-1 拉转写） → 完成后回 flows/T.md 刷新待办 |
| "有 XX 的 RID，给 ta 出个题" | flows/A-resume-detail.md（拉详情） → flows/M.md → flows/C-quiz.md |

---

## 🔴 合规红线（使用前必读）

本 skill 会处理腾讯校招/社招候选人的敏感数据，使用时**必须**遵守：

1. **不得外传**：候选人姓名可在腾讯内部 WorkBuddy 招聘会话中正常展示，用于识别候选人与承接后续操作；所有候选人信息（姓名 / RID / 简历 / 测评 / 面评）不得复制到外部 LLM、公网聊天工具、第三方笔记
2. **不得截图分享**：包含候选人个人信息的对话截图，**禁止**发送到非腾讯即时通讯、社交媒体、微信群/朋友圈；如需外发/截图/跨系统转述，使用候选人 ID 或序号替代姓名，并脱敏手机号、邮箱、身份证号、详细联系方式等敏感字段
3. **前轮面评保密**（硬规则）：从简历接口返回的前轮面评（`assessList` / `interviewRecords[].flows[].result_txt`/`comments`）及用户粘贴的上一轮面评，**只进面试官内部参考区，不进面向候选人的任何产出**（面试题正文、微信转发版、面评串联段）。详见 `flows/C-quiz.md` C-3 第 6 条
4. **测评数据只用于出题**：不得把测评红点直接告诉候选人（候选人已授权"测过"，但未授权获知具体分数）
5. **临时文件清理**：`$TMP_DIR` 下的 `resume_raw.json` 等文件用完主动删除
6. **集团权限使用**：如你拥有集团管理员权限（如总办数据查询），请仅用于招聘职责范围内的操作，不得越权

违反上述任一条款，可能触发腾讯个人信息保护合规流程。

---

## 🔒 远程资产加载规约（评分体系 / 红线 / 模型 / 风险核查 / BG 背景）

人才标准、评分锚点、BG 红线、风险核查清单、岗位胜任力模型等敏感原文**不在本 skill 仓库**，由后端知识库统一维护。skill 内 `references/` 下若仍有同名文件，是 **stub 占位**，不含正文。

### 索引位置

`references/_remote-assets.yaml` —— 含语义键 → documentId 映射、加载守则、缓存策略。

### 调用方式

```
apiId  : recruit.recruit-ai-service.get_document
params : { "documentId": "<由 _remote-assets.yaml 查得>" }
```

### 加载流程（agent 在 flows 中执行）

1. 根据当前 flow + 候选人元数据（BG / 岗位族 / 环节 / 招聘类型）选**语义键**
2. Read `references/_remote-assets.yaml` 取对应 `documentId`
3. 调 `get_document` 拉正文，命中**会话级缓存**（TTL 60 分钟）
4. 把正文作为 system context 内化使用，输出时**只产出整合结果**（题目 / 面评 / 评估）

### ⚠️ 5 条硬约束

1. **禁止原文回显** — 不向用户展示资产正文表格、行为锚点、评分细则、红线列表等
2. **禁止落盘** — 不把拉到的正文写入任何本地文件（含 stub 文件、temp、cache 目录）
3. **禁止暴露元信息** — 不在用户可见输出 / 思考链中提及 `documentId` 数值或具体内部文件名；只用语义键（如 `loaded asset/redline_s3`）
4. **禁止退化到 stub** — 远程拉取失败时，**不得**读取本地 stub 充数；用户侧只给"内部资产暂不可用，请稍后重试或联系 HR 业务运维"
5. **远程为权威** — 本地 stub 与远程内容如有差异，以远程为准；如发现 stub 残留旧正文，立即上报维护者

> 详细索引与守则请直接 Read `references/_remote-assets.yaml` 顶部注释。

---

## 核心硬规则（背下来 — 跨子模块通用）

- 🔴 **Router-0 优先**— 任何面试相关请求，第一步是 Router-0 四分类 + Read 对应 flows，不是 SearchAPI / CallAPI
- 🔴 **搜简历必跳转**（v4.1 新增）— 用户提到任何**批量搜简历 / 找候选人**诉求（"搜简历"/"找几个 XX"/"找做过 YY 的人"/"校招搜索"/"社招搜索"），**严禁**在本 skill 里调用 `recruit.campus-resume-search.post_v1_resume_search` 或 `recruit.social-resume-search.*` 等批量搜索 API。**第一动作**是告知用户跳转到对应 skill：校招 → `zhaopin-operations`、社招 → `zhaopin-social-operations`、不明确 → 反问"校招还是社招"。本 skill 只保留按 RID 拉单份简历详情（`flows/A-resume-detail.md`），用于 T/S/B/C/D 等已知候选人的执行链路
- 🔴 **前轮面评保密**— 前轮面评只进 🔒 内部参考区，不进面试正文（详见 flows/C-quiz.md）
- 🔴 **编码处理**— mcporter 终端中文是乱码（`���`），**必须**写文件 → decode → Read。**三条不可违反的子规则**：
  1. **"先写文件"**：所有 `mcporter call` 都用 `> $TMP_DIR/xxx.json 2>&1`，**禁止**直接读终端 stdout 做业务判断
  2. **"后 decode"**：解析前必须走 `scripts/decode_*.py`（已有 `decode_resume.py` / `decode_todo.py`）或等价 Python 片段，**禁止**用 grep / awk / sed 在终端里读中文字段
  3. **"再 Read"**：继续下一步前必须用 Read 工具打开 decoded 文件，**亲眼确认**里面是正确中文（如"北京大学"而非`���`）。看到乱码 → **立即停止**、不允许基于英文碎片/猜测继续出题、写面评、做判断
  - 🚨 **违规兜底**：任何时刻若输出里出现"我看到简历里写的是 XX（其实是猜的）"，视为严重违规，必须先回到本规则重跑 decode
- 🔴 **岗位/部门/BG 双口径硬规则**（v5.3 · 2026-08-20 实战事故整改）— 简历里有**两套**岗位/BG 字段，混用即编造：
  1. **候选人投递意向** = `resumeInfo.bg_txt` / `stationWithSubDirection`（候选人自己投的方向）
  2. 🔴 **本次面试实际挂载** = `interviewRecords.list[0].department_txt` / `bg_txt` / `bg_short` / `position_txt`（这场面试真正挂在哪个部门/BG/岗位）
  - **报告的「BG / 部门 / 本轮岗位」必须用第 2 套**；第 1 套只能另起一行标注「候选人投递意向」，**禁止合并成一行**
  - **事故案例**：曾把投递意向 `IEG互动娱乐事业群` 写进面试计划「BG / 部门」栏，而该面试实际挂载在 `S3 / 招聘活水部` → BG 完全写错，且岗位一栏被投递意向岗位冒充
  - **岗位名缺失兜底链**：`interviewRecords.position_txt` 实测**常为 null**（只有 `position` 数字 ID）→ ① 取**待办接口** `personList[].positionOuterTitle`（实测有值，如 `position=51 → '产品策划'`；`fetch_todos.py` 已做 6 字段变体探测）→ ② 仍拿不到就写「名称缺失(position=ID)」+ 用**面试部门 + BG** 描述归属
  - 🚨 **禁止**：用投递意向岗位冒充本次面试岗位；静默省略岗位行让用户以为报告漏写；岗位和部门一起空着（`department_txt`/`bgName`/`departmentFullName` 几乎总有值，**部门必须给出**）
  - `decode_resume.py` 已用 `[投递意向]` / `[面试挂载]` 前缀区分两套口径，且两者 BG 不一致时打印 **🔴 口径冲突告警** —— 看到该告警必须按面试挂载值写报告
- 🔴 **4 段式编排**— Part 0 开场破冰 / Part 1 经历深挖 / Part 2 岗位情景题 / Part 3 测评红点与数字抽查 / Part 4 价值观与反问（详见 flows/C-quiz.md）
- 🔴 **测评档位口径硬规则**（2026-05-12 事故整改）— `qualityAssessmentResults[].result` 是**档位**（1=低/2=中/3=高），不是分数：
  1. **输出必须写"档位"不是"分"**，并附 1-3 映射说明
  2. **只有档位 1 才算预警** → 可生成"测评红点验证"题；档位 2/3 都是正常，**禁止**标红点、**禁止**生成"反驳测评"式追问、**禁止**把 2/3 档写进"倾向不推"判据
  3. MCP 接口里 `totalscore=0, scoreLevel=null` 是**占位默认值**，不是真实数据，不要引用
  4. 原始分（1-10 尺度）在 MCP 拿不到，用户追问原始分必须诚实说明"只在招活前端 PDF 报告里"，**严禁**编造
  5. 若所有维度 ≥2 档 → 输出区写"测评档位全部 ≥2，无预警，本轮不作为判断依据"，Part 3 不必强行做"测评红点题"
- 🔴 **写面评必先拉转写**— 场景 D 接到"写面评"触发词，**第一步永远是 D-1 拉转写**，不是 D-2。即便转写没拿到，也必须走完 D-1 降级流程才进 D-2。严禁凭推演写面评（详见 flows/D-evaluation.md）
- 🔴 **面试计划全文直贴**— 计划 3000+ 字必须完整贴进对话，不得用"已保存到文件"替代
- 🔴 **简历数字抽查**— 简历中的百分比/用户量/营收等数字，至少抽 1 条作为 C-3 追问
- 🔴 **模型选择前置**— 场景 B/C/D 进入前必须走 M-0 询问路由（详见 flows/M.md），不得静默默认加载 fallback 模型
- 🔴 **本轮环节优先从数据读** — 场景 C 的"本轮面试环节"**不要上来就问用户**。判断链：
  1. **优先**从 T 待办联动数据读 `step_txt`（如"HR 面"/"复试"/"初试"）→ 命中则自动带入，输出时显式标注 `📌 环节来源：T 待办数据`
  2. 未命中则从简历 `PAYLOAD.interviewRecords.list[0].flows[]` 取**最后一条** `step_txt`（即"当前所处环节"）→ 命中则自动带入，输出时标注 `📌 环节来源：简历 interviewRecords.flows 最新节点`
  3. 还不到，从简历 `PAYLOAD.resumeInfo.currentStep`（整数映射：1-初试/2-复试/3-终面/5-HR 面）→ 命中按映射转义，输出时标注 `📌 环节来源：resumeInfo.currentStep`
  4. 以上都拿不到 **才**回落到 C-1 的 6 选 1 询问用户
  - 🚨 **禁止**：在 T 待办/简历里明明能读到环节却还问用户
  - 🚨 **禁止**：读到了但和用户口头说的不一致却不核对（必须当面确认以用户口述为准，并记录数据滞后）
- 🔴 **面试安排统一入口**— 用户提到任何**面试安排**相关需求（"安排面试"/"下单"/"改时间"/"调整时间"/"改期"/"取消面试"/"我什么时候有空"/"查日程"/"约时间"），**第一步永远是 Read flows/S.md 对照 S-0 路由表**，按 `orderId` 和 `stateId` 决定走 S-A/S-B/S-C，再调具体 API。**严禁**跳过 S 模块直接 SearchAPI 拼接接口调用
  - 🔵 **澄清"SearchAPI 到底能不能用"**：被禁的是"**跳过路由表、直接拿 SearchAPI 结果拼参数下单**"（绕流程瞎试）。**允许**的是：流程已按路由走到位、但 flows 文档没覆盖某场景/字段、或文档与实际接口对不上时，**用 SearchAPI 查权威接口目录来佐证**（接口存不存在/归哪个子域/参数线索/枚举）。详见 `flows/S.md` 的 **S-Ref 接口层兜底字典**。SearchAPI 只给接口目录+描述+部分枚举，不给完整 schema；专节已有的实测参数/类型陷阱仍以专节为准。

---

## 🎯 M-Auto · 模型自动路由器（核心特性 · 规格保留在主文件）

> **触发条件**：场景 B（简历评估）/ C（面试计划）/ D（面评填写）进入前，**自动**从已拉到的简历数据中提取 `stationTxt` + `bg_txt` + `recruitProject` 三元组，路由到最匹配的模型 + 面试方案，**不再询问用户**。
>
> **为什么放在主文件**：M-Auto 跨 B/C/D 三个 flows 共用，规格集中在主文件可避免 3 处重复维护。具体的"M-0 用户选模型入口"流程在 `flows/M.md`。

### M-Auto-1. 模型文件命名约定（强制）

**目录约定**：模型放 `references/models/`，面试方案放 `references/interview-designs/`。

**命名模板**：

```
{bg}-{station}-{recruitType}[-{round}].md
```

| 字段 | 取值范围 | 说明 |
|---|---|---|
| `bg` | `wxg` / `ieg` / `pcg` / `csig` / `teg` / `cdg` / `s3` / `group`（集团级） | 必填，全小写 |
| `station` | 岗位英文名缩写或拼音（如 `backend` / `gameplan` / `userresearch` / `productmgr`） | 模型必填；面试方案可省略 |
| `recruitType` | `campus`（校招）/ `social`（社招）/ `intern`（实习）/ `all`（通用） | 必填 |
| `round` | `hr` / `tech1` / `tech2` / `final`（仅面试方案需要，模型不分轮） | 仅面试方案文件需要 |

**资产清单**：

模型 / 面试设计 / 红线 / 气质叠加 等所有人才标准类资产，均不在本仓库以原文形式存在。
索引位置：`references/_remote-assets.yaml`（语义键 → documentId + 触发条件）。

```
references/_remote-assets.yaml          # 远程资产索引（语义键 + match 字段）
references/models/_station_alias.json   # 中文岗位名 → 标准 code（HR 可自定义）
```

> 💡 **迁移说明**：旧版本散落在 `references/models/*.md` 与 `references/interview-designs/*.md` 的本地原文已**全部移除**。所有引用统一走 `_remote-assets.yaml` 语义键 + MCP `get_document(documentId)`，agent 内部缓存（TTL 60 分钟）后内化使用，禁止原文回显与本地落盘。

### M-Auto-2. 三元组提取（拉到简历后立刻执行）

C-0 / B-0 拉到简历后（详见 flows/C-quiz.md C-0 Step 2.5），用 Python 提取：

```python
import json, re
raw = open(f'{TMP_DIR}/resume_raw.json').read()
m = re.search(r'\{.*\}', raw, re.S)
payload = json.loads(m.group(0))['data']['data']['data']

info    = payload.get('resumeInfo', {})
records = (payload.get('interviewRecords') or {}).get('list', [])

# 三元组
station_txt   = info.get('stationTxt', '')                          # 如 "后台开发"
bg_txt        = (records[0].get('bg_txt') if records else '') \
                or info.get('intentBgTxt', '')                       # 如 "WXG"
recruit_project = info.get('recruitProject', 1)                      # 1=校招, 2=实习, 3=社招

# 当前面试官 + 本轮环节
current_interviewer = records[0].get('current_staff_txt') if records else None
current_step = None
if records:
    for f in records[0].get('flows', []):
        if current_interviewer and f.get('staff_txt') == current_interviewer:
            current_step = f.get('step_txt')   # 如 "HR面试" / "初试" / "复试"
            break
```

或一行调脚本（推荐）：

```bash
python3 scripts/match_model.py $TMP_DIR/resume_raw.json
```

### M-Auto-3. 路由匹配规则（按 yaml 中 `match` 字段评分）

```
输入：(bg_txt, station_txt, recruit_project, current_step)
                    │
                    ▼
读取 references/_remote-assets.yaml，对所有 model_*/design_*/overlay 资产
按 match 字段（bg/position_family/recruit_type/step）做评分匹配：
  ├─ 全字段命中 → source=auto-matched, score=100
  ├─ 部分命中    → source=bg-fallback / round-fallback, score=60-90
  └─ 全不命中    → 退回 model_default_campus / flow_matrix_campus_fallback

叠加资产（overlays）独立判定：
  ├─ bg=WXG          → 自动追加 qizhi_wxg
  ├─ bg=S3 / 命中红线条线 → 自动追加 redline_s3
```

**station 模糊匹配规则**：见 `references/models/_station_alias.json`，未命中时 AI 跑一次模糊匹配 + 让用户确认。

### M-Auto-4. 命中后输出格式（每次场景 B/C/D 顶部强制显示）

```markdown
🎯 自动匹配模型：model_wxg_backend
   │ 来源：auto-matched
   │ 匹配：BG=WXG · 岗位=后台开发(backend) · 招聘=校招(campus)
   │ 匹配度：100/100
   │ 内容已通过 MCP get_document(id=18) 拉取并内化（不向用户回显原文）

📐 自动匹配面试设计：design_wxg_backend_tech1（本轮：初试）
   │ 来源：auto-matched
   │ 匹配度：90/100
   │ 内容已通过 MCP get_document(id=12) 拉取并内化

🎭 叠加资产：qizhi_wxg（BG=WXG 自动追加）
```

**降级时**：

```markdown
⚠️ 模型降级加载：model_default_campus（集团校招通用兜底）
   │ 来源：global-fallback
   │ 原因：未找到 BG=WXG · 岗位=AI研究员(ai-researcher) · 招聘=校招(campus) 的专属模型
   │ 建议：让 HR 在「甄选质量专家」搭建模型后由后端登记到 _remote-assets.yaml
   │ 匹配度：20/100
```

### M-Auto-5. 用户覆盖路由

如果用户**明确**说"用 XX 模型 / 用通用模型 / 我上传一份"，路由器**让位**给手动选择，跳到 flows/M.md 的 M-0 询问流程。

触发条件（关键词）：
- "用 {模型名}" / "换模型" / "不要这个模型"
- "我上传 / 我贴个 JD"
- "用通用模型 / 用兜底"
- "看看其他可选模型"

### M-Auto-6. 资产索引维护

资产清单维护在 `references/_remote-assets.yaml`：

```yaml
assets:
  model_<bg>_<position>:
    id: <documentId>
    summary: <一句话描述，避免暴露具体维度名/锚点>
    when_to_load: <触发条件描述>
    used_by: [flows/...]
    match: { bg: WXG, position_family: backend }   # 匹配字段
```

新建/修改流程：
1. 后端把新版正文录入知识库 → 拿到 `documentId`
2. 在 `_remote-assets.yaml` 的 `assets:` 节追加/修改条目（注意 summary 要脱敏）
3. agent 端 `scripts/match_model.py` 自动按 `match` 字段路由，无需重启

---

## 📋 工作流速览

| 步骤 | 当前流程 | 涉及子模块 |
|---|---|---|
| 用户进入场景 B/C/D | **直接拉简历 → 提取三元组 → M-Auto 自动加载** | flows/M.md（用户覆盖时） |
| 拉到简历后 | **M-Auto 跑一遍 → C-0.5 自动检测环节 → C-2 直接用匹配到的方案** | flows/C-quiz.md |
| 模型不存在 | **降级到 BG 级 / 招聘类型级 / 集团兜底，并在输出顶部 ⚠️ 标注** | 主文件 M-Auto-3 |
| 输出文档 | **每份评估/计划/面评顶部必出"已自动加载：XXX"标识** | 各 flows |

---

## 能力一览（4 大类目 / 9 个场景）

| 类目 | 涵盖场景 | 子模块 | 典型用户话术 |
|:---:|---|---|---|
| **① 待办查询** | T、T2 | `flows/T.md` | "我的面试待办"、"今天有啥面试"、"推荐待办"、"待填面评" |
| **② 面试安排** | S（含 S-0 路由 / S-0.5 查日程 / S-A 下单 / S-MultiPanel 多对一 / S-B 改期 / S-C 取消 / S-D 时差；下单参数走结构化弹窗一次问齐） | `flows/S.md` | "约面试"、"改时间"、"取消面试"、"多对一"、"我哪天有空"、"查日程" |
| **③ 面试准备** | M（选模型）、A（**按 RID 拉简历详情**）、B（评简历）、C（出题/面试计划） | `flows/M.md` + `flows/A-resume-detail.md` + `flows/B-resume-eval.md` + `flows/C-quiz.md` | "看一下 XX 的简历"、"评估一下简历"、"出题"、"面试计划"、"用什么标准考察" |
| **④ 面评** | D（拉转写 + 双版本面评草稿 + Handoff）、SE（校招面评提交入库） | `flows/D-evaluation.md`（写草稿）+ `flows/SE-submit-campus-eval.md`（提交入库，R2 受控写；详见 D-3.5「写→D / 交→SE」路由） | "写面评"、"面评草稿"、"录面评"（→D）；"提交面评"、"录入系统"、"代 XX 提交面评"（→SE，校招）|
| **⑤ 复盘单场** | E（自己评自己 · 拉转写 → BEI + 5 维 + 改进建议 → 存档） | `flows/E-coach-self.md` + `references/coach/{bei-framework,scoring-rubric,widget-spec}.md` + `scripts/save_coach_eval.py` | "复盘最近一场"、"复盘我刚刚那场"、"评一下我面试得怎样"、"给我做面试自评"、"复盘 traceId=xxx" |
| **⑥ 复盘成长** | G（自己看自己 · 默认最近 5 场 · 进步项 / 持续短板 / 改进建议） | `flows/G-growth-self.md` + `scripts/aggregate_coach.py` | "看我面试成长报告"、"我最近面试趋势"、"我面试有进步吗"、"复盘成长"、"看我最近 5 场表现" |
| **⑦ 招聘经理评估面试官** | H（管理者视角 · 3-5 场 · 探权 + 隐私收口 + 反馈话术） | `flows/H-coach-others.md` + 复用 E/G 的脚本 | "分析下 XXX 最近 5 场面试"、"看团队某面试官表现"、"评估面试官 XXX"、"我团队面试官谁面得最好" |
| **⑧ 面试官画像（v4.3）** | I（实时拉取 · 默认 10 场 · 转写+面评聚合 → 风格/偏好/覆盖度/倾向侧写 · 不依赖存档） | `flows/I-portrait.md` + `scripts/fetch_completed_interviews.py` + 复用 `fetch_transcript.py` + 简历 API | "我的面试画像"、"我是什么样的面试官"、"我的面试风格"、"分析我最近 10 场面试"、"提炼画像"、"面试官画像" |
| **🚪 跳转** | 批量搜简历不在本 skill 内 | → `zhaopin-operations`（校招） / `zhaopin-social-operations`（社招） | "搜简历"、"找候选人"、"找几个 985 的人"、"社招找 5 年经验" |

### 各场景明细

| 场景 | 触发词 | 功能 |
|:---:|---|---|
| **T** | "我的面试待办"、"今天有什么面试" | 查本人校招面试待办 |
| **T2** | "推荐待办"、"锁定简历" | 查锁定简历 / 他人推荐给我的简历 |
| **S** | "安排面试"、"改期"、"取消面试"、"查日程" | 调整时间 / 取消 / 下单 / 查面试官忙闲 |
| **M** | "搭模型"、"用什么标准考察"、"选考核标准" | 岗位考核标准选择 → 与 assessment-quality-expert 联动 |
| **A** | "看 XX 的简历"、"拉一下 RID xxx 的简历详情" | **按 RID 拉单份简历详情**（v4.1：批量搜简历已剥离至 zhaopin-operations） |
| **B** | "帮他评估一下简历" | 简历评估 **进入前走 M-0** |
| **C** | "出题"、"面试题"、"面试计划" | 个性化出题 **进入前走 M-0** |
| **D** | "写面评"、"面评草稿"、"录面评"（不含"提交面评"）| 双版本面评草稿 **进入前走 D-1 拉转写 + M-0 模型**；提交入库走 SE（D-3.5）|
| **SE** | "提交面评"、"录入系统"、"把面评填进去"、"代 XX 提交面评"、"确认提交" | 校招面评提交入库（待办定位 + 差异化提示语 + 准入校验 + **R2 受控写** `submit_interview_flow_trace`）；HR面试/通道面委/社招提交引导 Web 端（v5.2 新增）|
| **🚪→zhaopin-operations** | "搜简历"、"校招搜索"、"找几个 985 候选人" | 校招简历批量筛选（专业 6 步流程） |
| **🚪→zhaopin-social-operations** | "社招简历"、"社招搜索"、"找有 5 年经验的人" | 社招简历批量筛选 |
| **I** | "我的面试画像"、"面试风格"、"我是什么样的面试官"、"提炼画像" | 面试官画像（实时拉取 · 默认 10 场 · 不依赖存档 · v4.3 新增） |

---

## 📦 联动 skill 安装地址（内网 Knot）

> 本文档下文多处提到 `assessment-quality-expert`（甄选质量专家），它是腾讯内部 HR 团队搭的胜任力建模工具，**不是必装项**，但装了能让"搭新岗位模型"流程更顺。
>
> 🔗 **下载地址**：<https://knot.woa.com/skills/detail/33552>（点"安装"一键导入到 `~/.workbuddy/skills/assessment-quality-expert/`）
>
> 没装也能用：M-Auto 路由器只读 `references/models/` 目录的文件，与模型来自哪里无关。Skill 已自带集团兜底 + 2 个示例岗位模型可直接起步。

---

## 📦 首次使用（3 步，约 10 分钟）

### Step 1. 安装 mcporter 与 recruit-mcp（必装）

```bash
# 🆕 首选：WorkBuddy 弹窗「是否连接 recruit-mcp」→ 点「连接」→ 太湖 SSO 授权即可（无需手填 Token）

# 仅当客户端不支持弹窗、需手动 CLI 时：
# 1. 安装 mcporter（如已装可跳过）— 参考 https://mcporter.woa.com
# 2. 太湖 PAT：https://tai.it.woa.com/user/pat（🆕 不再需要「招活 Token」，只认太湖授权）
# 3. 添加 recruit-mcp 配置（只配太湖一个 header）
mcporter config add recruit-mcp \
  --url "https://zhaopin.mcp.it.woa.com" \
  --header "Authorization=Bearer <太湖PAT>"

# 4. 验证
mcporter list | grep recruit-mcp
```

### Step 2. 声明"我是谁"（首次会话时）

由于本 skill 不再硬编码个人账号，首次使用请在会话里告诉我：

> "我是 `<英文名>（<中文名>）`，例如：`zhangsan（张三）`"

我会在需要调用 `staffName` 的场景（S 下单 / S 改期等）直接复用。

> 💡 不知道自己英文名？调用 recruit-mcp 的 `recruit.huoshui-server.get_personal_api_web_personal_infoDetail`（无参），返回当前登录用户的 `staffId` / `fullName` / `departmentId` 等。⚠️ 旧文档里的 `recruit.campus-center-front.get_user_info` 已实测不存在（TARGET_NOT_FOUND），不要再用。

### Step 3. （可选）安装联动 skill

- **`assessment-quality-expert`**（可选，C/D 强烈推荐）— 提供胜任力模型、JD、评分标准。未安装时使用本 skill 内置 fallback 流程
- **`tencent-meeting-mcp`**（可选，D 场景拉会议转写用；未配置时走手工粘贴转写兜底）

---

## 跨平台路径约定

本 skill 所有临时文件统一使用 `$TMP_DIR`，**避免 Windows 伙伴炸路径**：

```bash
# macOS / Linux（默认）
export TMP_DIR="${TMPDIR:-/tmp}"

# Windows Git Bash / WSL
export TMP_DIR="$HOME/.workbuddy/tmp" && mkdir -p "$TMP_DIR"

# 首次使用在会话开头执行一次即可
```

文档中后续出现的 `$TMP_DIR/xxx.json` 都会被 Bash 展开为实际路径。

---

## 🧪 调试 / 排错入口

- 启动检查（每次会话开头）：详见 `flows/startup.md`
- MCP 调用技术细节（execute_command vs mcporter_call.py / 鉴权异常）：详见 `flows/mcp-appendix.md`
- 历史踩坑与版本差异：详见 `references/pitfalls.md`
- 风险检查清单：远程资产语义键 `risk_screening`（详见 `references/_remote-assets.yaml`）

---

## 📜 版本历史（简）

- **v5.3**（2026-08-20，用户实战反馈 · 岗位/部门/BG 双口径事故整改）：**面试计划把「候选人投递意向 BG」当成了「本次面试实际挂载 BG」，导致 BG 全错、岗位一栏被投递意向岗位冒充**。实战 case：给某校招候选人出题，报告「BG / 部门」栏写成 `IEG互动娱乐事业群`（来自 `resumeInfo.bg_txt`，那是候选人投递意向），而该面试**实际挂载**在 `interviewRecords.list[0]` 的 `bg_txt='S3'` / `department_txt='招聘活水部'`；用户追问"为什么报告没有本次面试岗位"才暴露。**三处根因 + 修复**：① **`decode_resume.py` 字段标签本身就是错的** —— 面试记录里的 `department_txt` 被标成"投递部门"、两处 `bg_txt` 都只标"BG"，agent 读 decoded 文件时天然会混淆。已改为 `[投递意向]` / `[面试挂载]` 前缀强区分，新增招聘类型/项目/招聘年/本轮环节/面试城市输出，并在两套 BG 不一致时打印 **🔴 口径冲突告警**。② **`fetch_todos.py` 岗位名探测字段不全** —— 只试了 `positionTxt` / `positionFullTitle`（该流程下都是 null），漏了**实际有值的 `positionOuterTitle`**（实测 `position=51 → positionOuterTitle='产品策划'`），导致岗位列渲染成 "—"，agent 误判"系统没有岗位"。已改为 6 字段并集顺序探测（`positionTxt`/`positionFullTitle`/`positionOuterTitle`/`positionClass`/`jobFamilyTxt`/`positionGroup`），全空时渲染 `⚠️ 名称缺失(position=<ID>)` 并在表下追加告警，**不静默吞成 "—"**。③ **校招待办表缺「部门」列**（社招表早有、校招表没有）—— 岗位名可能缺失，但 `departmentTxt`/`bgName`/`departmentFullName` 几乎总有值，是面试归属的唯一可靠锚点。已给校招表补上「面试部门」+「BG」两列，并在 `normalize_campus` 增补 `dept_full`/`bg`/`trace_id` 字段。**新增硬规则**：主 SKILL.md 核心硬规则区新增「岗位/部门/BG 双口径硬规则」（两套字段对照表 + 岗位名缺失兜底链 + 4 条禁止项）；`flows/C-quiz.md` C-0 Step 4 后新增同名硬规则块并把面试计划模板「基本信息表」的 `投递岗位`/`BG / 部门` 两行改为 `🔴 本次面试挂载` + `候选人投递意向` 两行强制分列；`flows/T.md` 补岗位/部门字段硬规则 4 条。**一句话教训**：简历里凡是"岗位/BG/部门"都存在**投递意向 vs 面试挂载**两套口径，报告口径必须取面试挂载（`interviewRecords`），投递意向只能另起一行标注。

- **v4.9.25**（2026-08-19，发起面试链路优化 · 隐性字段语义坑 + R2 握手工具化）：**四项沉淀**。①🔴**`recruitYear` 是招募周期年、不是候选人毕业年份**——新增 SC `2.2.2` 硬规则：必须调 `get_interview_recruit_year` 按 `recruitType` 反查可选集合（两种类型返回的年份**不同**），禁止从简历 `graduate_time` 推导；用户指定年份不在集合内时中断请其二选一、**禁止静默代换**；R2 卡片必须回显"该类型可选集合"，毕业年与招聘年不同时补一句说明。此坑不会在前置校验报错，只在写接口被拦或静默落成错误周期。②**新增 `scripts/build_write_envelope.py`**：把 R2 五步握手的「算摘要 + 手搓 12 字段信封 + 两次校验」收敛成 `prepare` / `outcome` 两条命令，从 `capability-registry.yaml` 自动带出 skill/risk_level/target_type/backend_deduplication/TTL，复用官方 `validate_write_action.py` 保证口径不漂移；内置五道防护（action_key 未登记 / payload 字段不在白名单 / 超 maximum_targets / summary 含手机号邮箱证件号 / success 缺 ref）；信封自动 0600、只打印摘要不回显 payload。**SC、SI、SE 三条写流程已统一接入**（各自保留手工回退路径）。③**新增 SC Phase 1「预热批」+ 调用预算表**：会话首次发起把 9 个与候选人无关的只读项分 2 批并行拉齐缓存（个人信息/项目/线路/环节/课程/年份×2/org_lookup/position_lookup），使单人首次发起 ≈13 次调用、同会话第二人起降到 3~4 次；预算表标注">30 次即在空转"的自查线。④**新增 SC 第七章「发起前自检清单」8 条**（类型来源/项目白名单/年份来源/职位反查/组织反查/环节∈{1,2}/staffId 非空/在途预判断），并修正 API 参考中 `interviewRecords` 的实际结构（是**容器对象**含 `.list[]`，`status` 是**字符串** `"0"`，内部字段为**下划线风格**与待办的小驼峰不同）+ 落库核实要求逐字段比对同参而非只看有无 `status=0`。附带：清理 flows/SKILL 中残留的真实工号/英文名/组织 ID，统一改占位符。
- **v4.9.24**（2026-07-30，性能优化 · 面评前期"很慢"根因）：**多条 traceId 串行试拉是"帮我写XX面评"前期慢的头号根因**。实测：接口本身不慢（查列表 1.4-2.2s、拉单条转写 1.9s），但面得多的候选人已办列表有**十几条 traceId**（实测某候选人 12 条），agent 逐个 `--trace-id` 串行试拉找哪条有转写 = 1.5-2s×N ≈ 20+ 秒白等。**优化**：①`fetch_transcript.py` 新增 `--trace-ids "id1,id2,..."`（逗号分隔）**并发试拉、自动选中转写行数最多的那条**（ThreadPoolExecutor，实测 6 条串行≈9-12s→并发 3.8s）。②D-1.1 加「多条 traceId 提速铁律」：先按"目标轮次+最近时间倒序"筛到最近 2-4 条，再 `--trace-ids` 并发一把过，别串行遍历全部历史。注：LLM 读转写生成面评本身的耗时（模型思考）不在此优化范围。
- **v4.9.23**（2026-07-30，实战修复 · rid 入口误判"HR 面无 traceId"）：**简历详情接口 `getResumeByRId` 的 `flows[]` 不含"当前进行中/HR 面"轮次，只列已归档的业务面（初试/复试）——不能据此断定该轮没 traceId/没转写**。实战：用户甩某候选人简历详情链接(rid=<示例RID>...)要写 HR 面评，agent 只调 getResumeByRId、见 flows 只有初试(<初试场次ID>)/复试(<复试场次ID>)无 HR 面 → 误判"HR 面没生成面试记录、拉不到转写"。但 HR 面实际 7-28 16:30 已面完、腾讯会议 <会议号>、系统有转写——HR 面 flowTraceId 在**待办列表**里不在简历详情 flows 里（简历详情 current_step=<环节ID>/current_staff=<面试官账号> 表明 HR 面存在，只是 flows 不吐当前环节）。已在 D-1.1 顶部加**头号铁律**：入口是 rid/简历详情且写当前环节/HR 面时，必须转查 `get_campus_interview_todo_list`(keyword=姓名) 取 personList[].flowTraceId，"简历详情 flows 没该轮 ≠ 该轮没 traceId"；并提醒待办是查登录人名下、跨账号查不到属正常应由该轮面试官本人会话查。
- **v4.9.22**（2026-07-20，实战修复 · D-1 转写拉取双坑）：**①已办/待办列表交叉排查废弃流程**：候选人的已办列表可能包含"发错类型"标记的废弃面试（traceId 返回 1018）。此时不应直接下结论"拉不到转写"——应转而调用待办列表（`get_campus_interview_todo_list`，keyword=候选人姓名），取 `personList[].flowTraceId` 重拉。实战：某候选人已办列表 flowMainId=<废弃场次ID>（废弃）返回 1018，待办列表 flowMainId=<活跃场次ID> 返回 code:200 的 413 行转写。D-1.1 新增「已办列表 1018 → 查待办列表找活跃场次」子条，并在第 2 条增量说明。②**`fetch_todos.py --format json` 输出格式说明**：该选项输出处理后摘要 JSON（显示字段），不含原始 `personList[]`（无 `flowTraceId`），传给 `fetch_transcript.py --todo-file` 会失败。D-1 方式 A 后新增格式陷阱说明，明确转写拉取应用原始 MCP 返回或已知 traceId 方式 B。
- **v4.9.21**（2026-07-14，社招下单兜底 500 误判实战坑）：**兜底「操作失败」500 = 参数问题（尤其漏 rid 反查），禁止脑补成"测试数据/业务拦截"**。实战：给社招候选人「某测试候选人」(employeeId=<员工ID>) 下单，`post_order_add` 连续 6 次返 `code:500「操作失败，请联系HR业务运维」`，agent 归因为"候选人是测试数据被系统拦截"、让用户去页面手动操作。**真因几乎可断定=漏了 rid 反查**：agent 全程只用 employeeId 数字，未跑 `resolve_social_rid.py --email` 反查 GUID rid（§S-Pre L75-87 早已明令"严禁 employeeId 当 rid、会报 500 操作失败"），直接拿 employeeId 当 candidates 标识 → 必兜底 500；且 6 次都带同一错误参数重复提交。已在社招下单 500 处理段加**【兜底 500 强制自查门】**（按概率排序自查 rid 反查/contacts 三件套/checklist）+ **禁止错误归因红线**（名字带"测试勿用"不构成被拦截证据，测试候选人参数对一样能下单）+ **止损行为规范**（兜底就停手回查参数、别盲目重试，修参数>换通道>重试）。
- **v4.9.20**（2026-07-14，用户实战反馈）：**查空档工作时间窗口 09:00-19:00 → 10:00-20:00（腾讯标准作息）**。S-0.5 单人查空档、S-MultiPanel 多对一共同空档算法此前都写死 `09:00-19:00`，与腾讯实际作息不符（腾讯 10 点上班、到晚 20 点）。已改 S.md 3 处：S-0.5 空档计算建议、S-MultiPanel 共同空档算法、S-0.5 实战示例时段，统一为 `10:00-20:00`。
- **v4.9.19**（2026-07-08，对照实验坐实，**推翻 v4.9.16 的 interviewers 规则**）：**修「面试官通知卡片重复」bug**。实战：下单把操作人本人塞进 `interviewers:[{<本人工号>,<本人英文名>}]`，通知卡片「面试官」把同一人显示了两次。查官方 schema：`interviewers` = **"辅助面试官（无则传空集合 `[]`）"**——即**主面试官=当前操作人系统自动带**，interviewers 只放"额外的辅助面试官"。之前把操作人本人塞进 interviewers → 系统带的主 + 自己传的辅（同一人）= 重复。对照实验（同单删了重下、interviewers 传 `[]`）：`code:200` 成功且 `interviewerName` 只剩 1 个。**连带纠正 v4.9.16 的两处误判**：① interviewers 空 `[]` **不会 500**（v4.9.16 那次 500 真因是漏订会议室前置链路拿不到会议室 id，与 interviewers 空不空无关，当时两变量混改扣错锅）；② 正确规则=本人面试传 `[]`、有额外面试官只放额外的人（都不含操作人本人）。改 S-A.2 关键参数说明 + v4.9.18 成功样例（interviewers 改 `[]`）+ S-Ref 参数表 L1193。
- **v4.9.18**（2026-07-08，校招「远程+订会议室」端到端实测一把过）：**沉淀成功样例 + 约面开头主动问会议室**。给校招候选人排"次日晚 19:00 腾讯会议 + 订线下会议室"全链路跑通（待办取 flowTraceId → 会议室 4 接口:城市→大厦→楼层→可用房 roomId → checkInterviewer 校验本人权限 data:true → post_order_add code:200，6.2s → 回读验证 orderId/时段/place/邀约完成）。**两处改动**：① S-A「订线下会议室」硬规则末尾加**端到端成功样例**（参数骨架+验证步骤+四个观察：a.待办渲染脚本只给rid必须回原始接口取flowTraceId别用rid冒充；b.下单传interviewForm=4+placeType=1时回读form归一化成5(web版面呗)属正常，系统在订会议室场景把线上形式转面呗；c.staffId=工号；d.timeConfirmed="true"才能订指定会议室）。② **S-A.1 弹窗新增 Q5「是否预订会议室」**（默认不订；选订则一次问清城市+大厦+楼层偏好再走4接口）+ 默认值表补"会议室=不订" + 加「主动问会议室」原则（约面开头就问，别等下单后补问逐层扫）。
- **v4.9.17**（2026-07-08，实战 case + 真实下单页面截图坐实）：**纠偏「面试方式 vs 会议室预订互斥」幻觉**。实战 case：用户说"是远程面试，只需要帮我预订会议室"，agent 却脑补出一张"远程(placeType=3) vs 现场(placeType=1) 二选一、远程不支持订会议室"的幻觉互斥表，据此反问用户"面试形式二选一"。**这是错的**——用户提供的真实下单页面截图证明：「面试方式」(腾讯会议/现场/面呗/电话) 和「会议室预订」(独立开关) 是**并排两栏、可同时开**，"腾讯会议(远程)+打开会议室预订"完全合法（面试官在会议室里用腾讯会议面候选人，即 v4.9.16 已确认的合理混合场景）。根因=S.md 缺少"这俩是独立维度"的正面权威陈述，agent 误把 placeType 当成"面试形式开关"脑补互斥。**已修**：S-A 弹窗 Q1 后新增「纠偏铁律：面试方式和会议室预订是两个独立维度、绝不互斥」块——给出双维度模型表（interviewForm 管形式 / placeType+会议室4id 或社招 needMeetingRoom 管会议室）、四种合法组合、"禁止再输出任何互斥说法"的红线。**并进一步单列「真正的互斥点」块**：页面上唯一那条互斥是「**候选人时间未确认（timeConfirmed/isConfirmTime=false）↔ 选指定会议室**」，**跟远程/现场无关**——因订房要按具体时段查空闲房（get_meetingRoom_rooms 必带 startTime/endTime），时间没定就查不了。执行含义：要订会议室先确认时间是否已定；未定则给两条路（先定时间再订 / 先建面试时间待定不订会议室），别带会议室 id 硬提交 timeConfirmed=false。一句话：卡订会议室的是"时间没定"，不是"选了远程"。
- **v4.9.16**（2026-07-01，实战 case + 4 接口实测坐实）：**同一 case 两个叠加坑：interviewers 禁止传空 + 订线下会议室前置链路。坑A（interviewers 空）**：agent 拼 `post_order_add` 时 `interviewers` 传了空 `[]`（没放面试官）→ 后端 500。根因是 change 参数表 L1134 抄了官方 schema 字面"辅助面试官，本人主面试官传 []"、误导下单也传空；但 add 的 interviewers 是 required、实测空数组必 500。**已修：interviewers 绝不能空，没指定面试官就默认放当前操作人(staffId+英文名)**，S-A 关键参数说明加硬规则、L1134 改为"必放主面试官、禁传[]"。**坑B（会议室）**：用户要"腾讯会议面呗 + 订会议室云海2栋14楼"，agent 没走订会议室前置接口、拿不到会议室 id 就硬提交 placeType=1，穷举 8 次 contacts/timeConfirmed 全 `code:500「操作失败」`，误判成"MCP 接口异常"走页面兜底。**真因不是接口坏，是漏了订会议室前置链路。** 实测坐实链路：`get_meetingRoom_cities → buildings(cityId) → floors(buildingId) → rooms(buildingId+floorId+startTime+endTime)`，逐级拿 cityId/buildingId/floorId/roomId。**关键坑：这 4 接口的 id 参数一律传字符串（传数字静默返 null）。** 实测：深圳"1"→云海2栋"470"→14楼"1170"→5 间可用会议室。混合场景说明：线上面(面呗/腾讯会议)也可同时订会议室(面试官在会议室用腾讯会议面)，interviewForm 保持线上、同时 placeType=1。新增 S-A「订线下会议室」硬规则 + S-Ref 会议室接口串联说明。
- **v4.9.15**（2026-06-30，用户从系统逻辑纠正 + 对照实验坐实，**推翻 v4.9.13/14**）：**校招 change 真因 = `interviewType` 隐性必传，漏了才返 500**。用户指出"候选人确认与否都能调整面试时间"，据此重测：同一单 <单号> 带 `interviewType:1` 改 15:00/14:00 → 均 `code:200` 且**待办即时变新时间**；故意漏 interviewType 改 13:00 → `code:500「操作失败」`。**坐实：change 完全可用且即时改时间，之前所有"change 改不动/返500/要候选人确认/stateId限制"的结论全是漏传 interviewType 的误判，已废弃。** 校招 change 强制带 `interviewType`(同社招 needMeetingRoom/contacts 一类隐性必传坑)；遇兜底500第一嫌疑=漏interviewType。改单前先 get_order_detail 读原单 interviewType/interviewForm/placeType 照抄。同步纠正 L165「stateId=1严禁change」旧规则为"可用,带全参数即可"、S-B兜底改为备选。isConfirmTime: false=改完发邀约让候选人确认/true=直接定,两者都即时改时间。
- **v4.9.13 / v4.9.14**（2026-06-30，⚠️**结论已被 v4.9.15 全部推翻，勿采用**）：这两版曾把校招 change 改不动误判为"stateId=1 严禁 change""change 本质是发邀约待候选人确认/不即时改""假失败"等——**全错**，真因只是漏传 `interviewType`（见 v4.9.15）。保留此条仅为记录排查轨迹：当时连续基于"漏参数导致的失败现象"反推业务语义，越推越偏；教训=遇接口 500 先穷举隐性必传参数，别急着推断业务语义。

- **v4.9.12**（2026-06-30）：**社招 `get_order_cancel` 端到端实测成功**。承接 v4.9.11 改期后的单 <单号>（某候选人·社招·stateId=4），实测取消成功（参数仅 id/reason/isSilence/staffName 四个，`code:200/data:true`，改后 `get_order_detail` 确认 `stateId=6「内部取消邀约」`）。与 change 不同，**社招 cancel 不需要 contacts/needMeetingRoom**，四参即可，staffName 放 body 有效。S-C 社招段补实测成功样例。**至此社招写接口三件套 add/change/cancel 全部端到端真实验证通过（同一候选人 某候选人 走完下单→改期→取消完整生命周期）。**
- **v4.9.11**（2026-06-30）：**社招 `post_order_change` 端到端实测成功 + `needMeetingRoom` 隐性必传坑**。实测改单 <单号>（某候选人·社招·stateId=1）19:00→20:00 成功（code:200/data:true，改后 stateId=4「内部调整邀约待候选人确认」，时段已更新）。关键发现：**社招 change 线上面试必须显式传 `needMeetingRoom:false`，否则失败且报错误导**——漏传报兜底「操作失败，请联系HR业务运维」(误导去补 contacts)，补了 contacts 仍漏则报「修改面试单据信息失败」，补 `needMeetingRoom:false` 才成功。已在 S-B 社招 change 段补实测成功样例 + 这两个 500 文案的排查指引（先查 needMeetingRoom 别只盯 contacts）+ 修正骨架 staffName 放 body 即可（不必 --header）。另确认 stateId=1 待候选人确认的社招单可直接 change 无需先确认时间。**至此社招写接口三件套(add/change/cancel)全部端到端或连通实测验证完毕。**

- **v4.9.9**（2026-06-30）：**取消面试接口实测 + 社招拿 orderId 正路确认**。校招 cancel 接口实测奏效(用已关单 orderId=<单号> 测，正确返回 code:500「已关单无需操作」，证明接口通+参数对)。社招拿 orderId 正路 = `get_order_toInterviewList_mine`(page/pageSize 字符串)，records[] 含 orderId。⚠️ **关键时间窗口**：该接口只返回"尚未到达面试时间"的单，面试时间一过该单即从列表掉出(records空)→ 社招改/取消必须在面试时间前操作；过期单经 MCP 无法反查 orderId(add只返data:true/待办只有traceId/detail要orderId)。拿不到时如实告知用户去页面，禁用 traceId 冒充 orderId。校招无此问题(待办含已安排单)。S-C 更新。

- **v4.9.8**（2026-06-30）：**社招拉转写实测确认 + D-1.1 补社招取 traceId 来源**。实测社招转写接口 `interview-arrange.get_interview_trace_record` 正常(<操作人> traceId=<traceId>→114行真实转写；脚本 --recruit-type social 实跑通过)；社招同样"转写挂某一场次"(6个历史场次仅1个有转写,其余1018/空)。修复 D-1.1 一处社招盲区：原只写"从 get_campus_interview_done_list(校招已办)取traceId"，补全社招应从 `social-todo-center.get_api_trace_get_list`(flowId=3+extType=interview+done=true) 取 `rows[].id`。校招社招转写路径现均已实测验证。

- **v4.9.7**（2026-06-30）：**D-1.1 转写多场定位改"先反问确认"（避免盲目遍历）**。v4.9.6 让"列出全部轮次逐个试拉"，但候选人面过很多次/多场时盲目遍历既慢又可能拉到无关旧场次。改为：仅1~2条且最近→直接试拉；**多场(≥3)/跨多流程/结束已久→先用 AskUserQuestion 让用户确认目标场次(列轮次+面试时间)再针对性拉**。原则"机器定位有歧义时让用户拍板，别硬猜也别全捞"。D-evaluation.md D-1.1 分情况表 + fetch_transcript.py 提示同步。

- **v4.9.6**（2026-06-30）：**D-1 拉转写"明明有转写却拉不到"修复（实测坐实根因）**。实战 case：某候选人报"招活转写拿不到(未开启转写)"+脑补"面试还没开始"算反时间。**用一名真实有转写的候选人实测复现**：已办列表查到 ta 有 4 条不同轮次 flowTraceId(分属2个flowMainId)，逐个拉转写——3 个返回 `code:1018「面试待办不存在或已失效」`(流程作废)，仅其中 1 个 traceId 返回 code:200+百余条真实转写。**根因坐实=traceId 取错轮次**(转写只挂某一具体轮次，待办flowTraceId常指当前轮次而非有转写的那轮)。修复：① fetch_transcript.py 识别内层 `code:1018` 并引导换轮次重拉(不再笼统判"未开启转写")；② `--todo-file` 兼容已办结构(候选人在 list[] 顶层无 personList)；③ D-evaluation.md 新增 D-1.1(目标场次定位+1018处理+已办结构说明)、D-1.2(面试是否已结束用date正确比较防脑补)。已实测验证：正确 traceId→百余行成功、失效 traceId→1018正确引导。

- **v4.9.5**（2026-06-30）：**社招约面全链路实测打通**。实测发现并修：① S.md 社招待办接口 `interview-arrange.get_my_interview_list` **已失效**，正确接口是 `social-todo-center.get_api_trace_get_list`(flowId=3+extType=interview+done=false)，API 分发表/S-E2 已更正；② employeeId→rid 反查正解 = `resolve_social_rid.py --email <邮箱>`（脚本实测一把过；手动直调 post_api_resume_query_query 必须用 `email` 字段+locked，否则返默认列表）；③ 社招 `post_order_add` 实测成功(code:200)：rid(email反查)+contacts三件套+noticeType四字段+traceId(待办nextTraceId)，已补成功样例。S-Pre 社招RID硬规则、社招接口表均更新。

- **v4.9.4**（2026-06-30）：**社招 change/cancel 接口上线，恢复社招 MCP 写路径**。MCP 目录普查发现社招 `interview-arrange` 子域已新增 `post_order_change`(改时间) + `get_order_cancel`(取消)，旧版 v4.5"社招无 change/cancel、只能去页面"全部作废。据用户提供的官方 schema 更新 S.md 7 处：API 分发表、S-B/S-C 社招分支改为调接口、S-E2 社招接口表(10→12个)、S-Index 二元表、误判案例。社招 change 关键差异（vs 校招）：required=id/interviewForm/interviewTimeList/period；用 timeConfirmed(bool,opt) 非 isConfirmTime；无 placeType 用 needMeetingRoom+interviewPlace；noticeType=outlook/weworkRobot/emailToCandidate/miniRobotToCandidate；staffName 必填；独有 changeTraceOwner/outlookReceiver/mailMessageForInterviewer。社招 cancel 参数同校招(id/reason/isSilence/staffName)。⚠️ 社招 change/cancel 未实测，骨架按 schema 拼，首跑后补样例。

- **v4.9.3**（2026-06-30）：**新增"接口层兜底字典"机制**。当 flows 文档没覆盖某场景/字段、或文档与实际接口对不上时，允许用 `SearchAPI`（接口名或自然语言）查招聘 MCP 的权威接口目录来佐证（接口存否/子域归属/参数线索/枚举）。在 S-Ref 加该机制说明 + 校招 S 模块权威 apiId 清单；并明确边界：① SearchAPI 只给目录+描述+部分枚举，不给完整 schema；② 与"禁止直接 SearchAPI 拼参数下单"不冲突（禁的是绕路由瞎试，允许的是流程到位后查证接口能力）；③ 专节已有的实测参数/类型陷阱仍以专节为准。主 SKILL.md「面试安排统一入口」硬规则旁加澄清指针。

- **v4.9.2**（2026-06-30）：**校招 5 接口经 MCP SearchAPI 核对 + 新增集体面试(S-GroupPanel)**。get_order_cancel(id/reason/isSilence)、get_order_detail(OrderMain)、get_order_invite_detail(InviteOrder)、get_interview_trace_record(ASR转写,属D流程) 均与 S.md 一致。**interviewType 区分校正（用户权威澄清）**：2=多对一(多面试官对1候选人，校社都有)；**4=集体面试(一/多面试官对多个候选人，🔴仅校招、社招不支持)**。据此：① 校招 change 参数表确认支持 4（去掉"待实测"）；② 社招 S-E2 参数表标明不支持 4；③ S-A.1 弹窗 Q3 增加"集体面试"选项 + 概念区分块；④ 新增 **S-GroupPanel 小节**（多候选人 candidates 数组 + interviewType=4 下单，集体面试下单结构待首次实跑确认）；⑤ S-Index 路由表加群面/集体面试行。contactType 校招标"已弃"/社招有效是两接口各自正确、非冲突。
- **v4.9.1**（2026-06-30）：**S-A.1 弹窗文案修正**。① `interviewForm=5` 显示名「腾讯会议面呗」→「web版面呗」；② `timeConfirmed=false` 显示名「让候选人确认时间」→「未确定时间，候选人可反馈调整」。同步改 S-A.1 弹窗定义 + 参数表 + 默认行为说明 + 3 个脚本(decode_todo/fetch_todos/fetch_campus_flow)的 form 映射，并在 S-A.1 加"弹窗选项文案口径"约束防回退。
- **v4.9**（2026-06-30）：**S 模块 500 诊断校招/社招分流 + `post_order_change` 对齐官方 schema**。
  - (a) 原 S-A.2（校招章节）的"操作失败兜底 500"硬规则错误照搬了社招的"优先核对 contacts 三件套"诊断——但 contacts 三件套是**社招专属** de-facto 必传字段，**校招根本没有**。导致校招批量下单遇兜底 500 时，模型反复增删 contacts、换 timeConfirmed 类型做无效穷举（实战 case：5 个校招候选人连续 3 次兜底）。已按校招/社招拆开诊断：校招明确"不需要 contacts、别抄社招坑"，给校招专属兜底（早止损 + 批量第 2 单兜底即整批走页面）；S-A 入口加"校招≠社招参数"红线。
  - (b) 按官方 `/order/change` schema 重写 S-Ref `post_order_change` 参数表：明确 required 5 字段（id/isConfirmTime/interviewTimeList/interviewForm/placeType）；`staffName` 标注"schema 可选但实测必传"（消除与官方 schema 的矛盾，保留实测经验）；补全遗漏字段 `againstCheatingTypeId`(反作弊) / `groupMax` / `contactsNumber` / `cityText 等文本字段` / `contacts 三件套`(校招 change 非必传)。详见 `flows/S.md`。

- **v4.3**（2026-06-12）：**面试官画像（I-portrait）**。新增类目 ⑧，实时拉取最近 N 场（默认 10 场）已完成面试的转写+面评，LLM 聚合面试风格/提问偏好/维度覆盖/面评倾向等静态侧写。不依赖 coach-archive 存档，首次可用。与 G（成长报告）互补：G 看趋势变化，I 看静态特征。新增 `scripts/fetch_completed_interviews.py` 一键拉取校招+社招已完成面试列表。社招转写接口 `recruit.interview-arrange.get_interview_trace_record` 同版本补充（v4.2 标注但实际与 v4.3 同期交付）。
- **v4.2**（2026-06-12）：**社招转写支持**。D-1 拉转写新增社招接口 `recruit.interview-arrange.get_interview_trace_record`（与校招 `recruit.interview-arrange-campus.get_interview_trace_record` 并列）；`fetch_transcript.py` v1.1 新增 `--recruit-type social` 参数；`references/transcripts/recruit-trace-api.md` 补充社招接口文档。
- **v4.1**（2026-05-18）：**搜简历跳转治理**。批量"搜简历/找候选人"职责从本 skill 剥离 — 校招跳 `zhaopin-operations`、社招跳 `zhaopin-social-operations`。原 `flows/A-resume-search.md` 改造为 `flows/A-resume-detail.md`（仅保留按 RID 拉单份简历详情，服务于 T/S/B/C/D 联动）。新增"搜简历必跳转"硬规则。
- **v3.7**（2026-05-14）：D-1 拉转写改用招活内嵌接口 `recruit.interview-arrange-campus.get_interview_trace_record`（取代 tencent-meeting-mcp 三跳路径）；新增 `scripts/fetch_transcript.py` 一键脚本与 `references/transcripts/recruit-trace-api.md` 字段说明。详见 `flows/D-evaluation.md` D-1 与参考文档。
- **v4.0**（2026-05-14）：路由式拆分。主 SKILL.md 仅保留路由规格 + 核心硬规则 + M-Auto 路由器，T/S/M/A/B/C/D 等流程详情下沉到 `flows/`。原 v3.6 单文件备份在 `SKILL.md.v3.6.bak`。
- **v3.6**（2026-05-12）：测评档位口径硬规则、4 段式编排、本轮环节优先从数据读
- **v3.0+**（更早）：M-Auto 自动路由器、Router-0 四类目分发器、编码处理硬规则

> ⚠️ 完整版本历史 → `references/pitfalls.md`

---

## 📊 数据上报（AUTO-TRACK · 跨平台通用）

> 以下上报统一走插件级低敏入口。只记录流程枚举和状态，不传会话 ID、岗位/BG、面试内容、候选人信息或自由文本错误。

**在以下时机执行上报（`requires_approval: false`）：**

### 1. 查待办完成后

```bash
bash ../../scripts/track_skill_event.sh "0WEB06ZI7OVDOZQW" "interview-assistant" "todo_queried" '{"sub_flow":"<T|T2>","status":"<success|fail>"}'
```

### 2. 面试安排操作完成后

```bash
bash ../../scripts/track_skill_event.sh "0WEB06ZI7OVDOZQW" "interview-assistant" "interview_scheduled" '{"action":"<create|reschedule|cancel|check>","status":"<success|fail>"}'
```

### 3. 出题/面试计划完成后

```bash
bash ../../scripts/track_skill_event.sh "0WEB06ZI7OVDOZQW" "interview-assistant" "quiz_generated" '{"sub_flow":"C","status":"<success|fail>"}'
```

### 4. 写面评草稿完成后（写完两版草稿，不含提交动作）

```bash
bash ../../scripts/track_skill_event.sh "0WEB06ZI7OVDOZQW" "interview-assistant" "evaluation_written" '{"sub_flow":"D","status":"<success|fail>"}'
```

> ⚠️ 该 event 只统计"草稿生成"，**不代表已提交到系统**。提交动作在简历详情页由用户人工完成（详见 flows/D-evaluation.md D-3.5），不要把"提交"也算进 evaluation_written。

### 5. 评简历完成后

```bash
bash ../../scripts/track_skill_event.sh "0WEB06ZI7OVDOZQW" "interview-assistant" "resume_evaluated" '{"sub_flow":"B","status":"<success|fail>"}'
```

### 6. 捕获到异常时

```bash
bash ../../scripts/track_skill_event.sh "0WEB06ZI7OVDOZQW" "interview-assistant" "error_occurred" '{"error_code":"<mcp_error|decode_error|api_timeout|script_error>","status":"fail"}'
```

### 7. 任务失败时上报失败归因（填入 `fail_reason`）

当任务未能成功完成时：
```bash
bash ../../scripts/track_skill_event.sh "0WEB06ZI7OVDOZQW" "interview-assistant" "task_completed" '{"result":"<skill_bug|llm_limitation|user_cancel|dependency_error|timeout>","status":"fail"}'
```
