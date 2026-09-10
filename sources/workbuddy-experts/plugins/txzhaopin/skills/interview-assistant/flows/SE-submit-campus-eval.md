# 面试助手 · SE 校招面评提交子模块（提交面试评价到系统）

> 子模块路径：`flows/SE-submit-campus-eval.md`
> 触发：主 SKILL.md 的 Router-0 命中「提交校招面评 / 录入系统 / 代提交面评」后，或 D 流程 D-3.5 识别到"提交面评"意图后，**第一件事是 Read 本文件**再执行。
> 定位：把面试评价**写入招聘系统**（写接口 `submit_interview_flow_trace`）。与 D 子流程分工——**D 只生成面评草稿文本，SE 负责真正提交入库**。

<!-- skill-tracker sub_flow: begin (auto-generated) -->

> 🚨 **FIRST ACTION（读到本文件第一件事 · MANDATORY · 静默执行）**：上报 `sub_flow_entered` 事件，标记本次进入了 **`SE` 子流程（校招面评提交）**。

```bash
bash ../../scripts/track_skill_event.sh "0WEB06ZI7OVDOZQW" "interview-assistant" "sub_flow_entered" '{"sub_flow":"SE"}'
```

**约束**：每次读到本文件就执行一次；静默后台，失败容忍，不询问用户。

<!-- skill-tracker sub_flow: end -->

---

## 概述与定位

本子流程在校招面试流程的各环节中**提交面试评价（面评）到招聘系统**。通过生产 `recruit-mcp` 的 `submit_interview_flow_trace` 写接口完成面评数据的收集、校验和提交。支持**面试官本人提交**和**招聘经理代提交**两种模式。

> ⚠️ **仅覆盖校招 4 类环节作为「当前待提交节点」**：集体面试(1)/初试(2)/复试(3)/用人决策者面试(200)。**HR面试(5)/通道面委(100)** 作为当前待提交节点时**本子流程不支持**（竞企信息/HR必问信息等属前端独立表单，MCP 提交接口无字段可填）——引导用户去招聘系统 Web 端提交（见「环节四」）。

### SE 与 D 的分工（必须理解）

| 子流程 | 干什么 | 产物 |
|---|---|---|
| **D**（`D-evaluation.md`） | 拉转写 → 按模型/模板**生成面评草稿文本**（系统版 + 微信版） | 草稿文本，**不入库** |
| **SE**（本文件） | 定位待办 → 收集必填字段 → 准入校验 → **R2 受控写 → 提交入库** | 面评落库，流程推进 |

- 用户说"帮我**写**面评" → D（写草稿）
- 用户说"帮我**提交**面评 / 录入系统 / 把面评填进去 / 代 XX 提交面评" → **SE（本文件）**
- 用户说"录面评 / 填面评"（模糊）→ 反问 1 句："是要我**写面评草稿**，还是**提交面评到系统**？"
- D 生成完草稿后用户接着说"提交吧" → 无缝进入 SE，D 的系统版文本作为 `comment` 候选（仍需 SE 走完待办定位 + 字段收集 + R2 确认）

---

## 一、生产连接器与调用规范（每次会话首次调用前确认一次）⚠️

校招面评的读写接口统一使用生产连接器 **`recruit-mcp`**（与 SC 校招发起、SI 社招发起同一连接器；**2026-08 已确认生产暴露 `campus-interview-service` 分组，含 `submit_interview_flow_trace` 写接口**）。

调用前必须：
1. `SearchAPI(query=..., domain="recruit")` 发现能力 → `SearchAPI(apiId=...)` 取参数 schema → `CallAPI` 执行。
2. `CallAPI` 只接受 SearchAPI 返回的原始完整三段式 apiId，禁止自行拼造。
3. 若生产 SearchAPI 未返回 `recruit.campus-interview-service.submit_interview_flow_trace`，停止自动提交并降级到简历详情页 Web 端，不得切换测试连接器。

### 核心接口清单（生产）

| apiId | 用途 | 关键返回 |
|-------|------|---------|
| `recruit.campus-center-front.get_campus_interview_todo_list` | 查询**当前登录用户名下**的面试待办 | 含 `personList[].flowTraceId`（submit 必填项）|
| `recruit.campus-interview-service.submit_interview_flow_trace` | **提交面试评价（写入）** | 需 `traceId` |
| `recruit.campus-resume-search.get_v1_mcp_resume_getResumeByRId` | 简历详情（按 rid）| `interviewRecords.flows` 含各节点 result/rank/status |
| `recruit.campus-interview-service.get_campus_interview_report` | 面试进度跟踪（按 studentId）| ⚠️ 无 flowTraceId 字段，不能直接拿 traceId |
| `recruit.campus-interview-service.get_interview_evaluate_template` | 按 traceId 获取评语配置（只读探测）| 能返回配置即说明 traceId 有效 |
| `recruit.campus-interview-service.get_resume_control_info` | 准入控制校验（提交前必做）| `actionEnable` / `showHint` / `hintList` |
| `recruit.campus-interview-service.get_interview_dictionary_config` | 工作城市字典 | 解析 workCity 编码 |

---

## 二、完整工作流

严格按阶段顺序执行。**待办定位**、**准入校验**、**差异化提示语查询**、**R2 二次确认**、**报错透传** 为硬性节点，不可跳过。

### SE-1 待办定位与权限解析（提交前第一步）

用户请求提交面评时，**不要直接让用户回答「当前环节/角色」**，而是先通过系统查询定位正确的待办：

**Step A · 获取候选人面试待办列表**

调用 `get_campus_interview_todo_list`（返回的是**当前登录用户名下**的待办，同一候选人可能有多条环节待办）。

**Step B · 判断是否命中本人待办**

遍历待办列表，检查是否存在归属人为当前用户的待办：
- **命中**（多条中只要有 1 条在用户名下即算命中）：提交该条用户名下待办，操作角色 = **本人提交**。
- **未命中**：进入 Step C 代提交。

**Step C · 代提交场景 → 引导走标准 UI 路径获取 traceId**

若待办均不在当前用户名下（查无该候选人或 total=0），确认为**代提交场景**：
1. 先用 `get_campus_interview_report(studentId)` 确认候选人当前待办节点的**面试官姓名**（`staffName`）和**环节名称**（`stepName`）。
2. 向用户展示代提交标准 UI 操作路径（见 SE-2 第 2 条），引导用户拿 traceId。
3. 拿到 traceId 后，用 `get_interview_evaluate_template(traceId)` 只读探测确认有效性，再进入 R2 确认与提交。

**Step D · 多条待办的选择（仅代提交场景）**

- 用户已明确指定环节（如「提交 xxx 的复试环节」）→ 定位对应环节待办。
- 用户未明确 → **必须询问**用户要提交哪一条，列出环节名称、候选人、状态供选择。

> ⚠️ 代提交必须在 R2 确认与提交说明中标注「代提交」身份：**被代提交的面试官姓名**（实际处理人）+ **当前操作人**（代提交人）。

### SE-2 traceId 获取（核心痛点）

`submit_interview_flow_trace` 的必填项 **`traceId` 是 `flowTraceId`（StdFlowActionTrace 主键），绝对不等于 `flow_id` 或 `current_step`**。误用会报 `code 1005 / 面试流程信息不存在`。

**可靠获取路径（按优先级）**：

1. **🌟 本人待办列表（本人提交首选）**：`get_campus_interview_todo_list` 返回项含 `personList[].flowTraceId`，直接可用，无需用户额外操作。
2. **🌐 代提交标准 UI 路径（代提交首选）**：待办不在当前登录用户名下时，MCP 无法直接查他人 flowTraceId（接口无 staffId 筛选参数）。引导用户按固定步骤操作：
   ```
   Step 1: 打开「面试官进度跟踪」页面（校招招聘管理 / 面试官进度跟踪）
   Step 2: 搜索被代提交的面试官姓名（英文名或中文名均可）
   Step 3: 在该面试官行点「代为处理」按钮
   Step 4: 系统跳转「待办中心」→ 切「校园招聘待办」Tab（显示该面试官名下待办）
   Step 5: 找到目标候选人，点「评价」列按钮
   Step 6: 详情页 URL 形如 https://zhaopin.woa.com/zhaopin/campus/NewInterviewDetail?traceId=xxxxxxx
   Step 7: 把 URL 中的 traceId 值发给 AI
   ```
   > 平台官方代提交入口，比"随便贴链接"更规范。检测到代提交场景后主动给出上述步骤，而非被动等待。
3. **Web 链接备用方案**：用户已有详情页链接 → 直接提取 `traceId=xxx`。
4. **只读探测**：`get_interview_evaluate_template(traceId)` 传入候选 traceId，能返回评语配置即说明 traceId 有效。

**为什么代提交无法通过 API 直接拿 traceId**：
- `get_campus_interview_todo_list` 仅返回当前登录用户名下待办，无 staffId 参数查他人。
- 简历详情 `flows` 只展开已结束节点，进行中节点不展开，拿不到进行中节点 flowTraceId。
- 报告接口 `get_campus_interview_report` 无 flowTraceId 字段。
- ⇒ 代提交**必须走 UI 标准路径或请用户提供 Web 链接中的 traceId**，不要用错误 ID 试错。

### SE-3 staffId 解析（下一环节面试官 / 被代提交人）

`submit_interview_flow_trace` 的 `nextSteps[].staffId` 需要**数字型 staffId**，不是英文名。解析方法：
- 从「<英文名>(<中文名>)」这类信息，用 `get_v1_mcp_resume_getResumeByRId` 简历详情的 `staff_info`，或用 `get_campus_interview_todo_list` 返回项里的 `staffId` 反查。
- 也可用 `SearchAPI` 搜索面试官账号解析。
- 🔴 **禁止凭记忆填工号**：英文名与 staffId 的对应关系必须每次现查，不得使用文档里的历史示例值或凭印象拼。

### SE-4 差异化提示语（部门级配置）查询（提交前必做）

部分部门在面试评价页面配置了差异化的提示语（tips）与评价模板（evaluate）。提交面评前，若待提交节点命中配置部门，**必须把差异化提示语返回给用户**，由用户按提示语撰写内容——**AI 不得自行编造评价内容**。

**配置文件**：`references/campus-eval-tips/dept_evaluation_tips.json`（转换脚本 `references/campus-eval-tips/convert_xlsx_to_tips.py`；用户提供新 xlsx 时重跑覆盖）。当前配置部门：**PCG(org_id 29292) / SD 商业分析师(org_id 30) / FiT P族(org_id 18424)**。

**取数来源**（简历详情 `get_v1_mcp_resume_getResumeByRId`）：
- 部门 `org_id`：待提交节点所在 `interviewRecord.department`
- 环节 `step_id`：该节点 `flow.step_id`（完整编码：1=集体面试/2=初试/3=复试/5=HR面试/100=通道面委/200=用人决策者）
- 岗位 `position`：`interviewRecord.position`

**匹配逻辑**：在 `departments` 找 `org_id` 匹配项 → 在其 `steps` 找 `step_id` 匹配项（`enable_flag=1` 生效）→ 其他维度均为 `0` 通配，只看**部门 + 环节** → 命中取 `tips` + `evaluate`。

**命中后行为（关键）**：
- **必须完整返回 `tips` 与 `evaluate` 给用户**，告知按该部门差异化提示语撰写本节点评价内容。
- **暂停收集/提交**，等待用户提供符合提示语的评价内容（不 AI 代写、不用通用模板填 `comment`）。
- 用户给出内容后，**必须执行「评价内容拆分与二次确认」**（见 SE-5）。
- 用户坚持不按提示语填 → 按其内容提交，但提示"该部门有差异化提示语要求，建议按其撰写"。
- **未命中**：不执行拆分，按通用流程直接用用户提供的原文作为 `comment`。

### SE-5 评价内容拆分与二次确认（命中差异化提示语时必做）

用户提供的评语常为自由文本。为让提交到系统的 `comment` 与部门 `evaluate` 模板一致，AI **必须**：

1. **按 `evaluate` 模板小节标题拆分**，将用户评语归并映射到对应小节。各部门骨架：
   - **PCG(29292)**：`1、专业能力` / `2、综合素质` / `3、人选意愿度及其他` / `4、基于以上，综合结论`
   - **SD 商业分析师(30)**：`1、问题组织拆解` … `7、其他` + `面试case记录`（满分 4 分维度）
   - **FiT P族(18424)**：`底线要求(热爱/聪明/坚韧)` / `加分项(锐气/AI学习与应用)` / `其他评价`
2. **保留用户原意、不增删事实**：只做"结构归集"，不编造不篡改；某小节未提供则留空标注"（未提供）"。
3. **返回结构化拆分结果请用户二次确认**：
   ```
   ── 评价内容拆分（请确认是否准确对应模板）──
   【1、专业能力】……（用户原话归集）
   【2、综合素质】……
   ...
   如有不准或遗漏，请告诉我修正；确认无误回复"确认"。
   ```
4. **确认后**：该结构化拆分结果（保留小节标题）即作为最终 `comment` 提交内容。
5. **未命中差异化提示语的部门**：不拆分，直接用用户原文作 `comment`。

> 📌 拆分示例（PCG/SD/FiT 三部门自由文本→结构化）见文末附录。

### SE-6 各环节字段逻辑

**通用校验链路（所有环节共通，提交前逐条过）**：

| 步骤 | 校验点 | 关键规则 |
|---|---|---|
| ① 定位待办拿 traceId | `flowTraceId` | 必须 `flowTraceId`(>0)，**≠** flow_id/current_step；为空/≤0 报错，用错报 `1005` |
| ② 准入控制校验 | `get_resume_control_info` | `actionEnable=false`→拦截；`=true & showHint=true`→展示 `hintList` 待用户知悉；4 环节提交通过准入码用 `CommitPassInterviewFlow` |
| ③ 字段必填校验 | 按 `result` 分支 | 放弃(3)=只选填「等级+评价」；通过(2)=按环节定必填集合 |
| ④ 下一环节面试官权限 | `nextSteps[].staffId` | 仅「通过且非末环节」时校验；姓名/账号须解析为数字 staffId |
| ⑤ R2 提交 | `submit_interview_flow_trace` | 走受控写握手（SE-7）；`comment≤5000字` |

> 🔑 **放弃(result=3) 是所有环节通用简化分支**：只需 `rankId` + `comment`，`workCity`/`nextSteps` 放宽。

**通用字段**：

| 字段 | 类型 | 可选值 |
|------|------|--------|
| 面试结果 | 单选（必填）| 通过(2) / 放弃(3) |
| 工作城市 | 文本（通过时必填）| 用字典编码 |
| 下一环节 | 单选 | 见各环节 |
| 下一环节面试官 | 账号/姓名→解析 staffId | — |
| 面试等级 | 单选 | S(1)/A+(2)/A(3)/A-(4)/B(5)（**前端只渲染这 5 档**；后端保留 6=C 但不展示，勿臆造 C）|
| 面试评价 | 多行文本 | ≤5000 字 |

**环节一：集体面试(1) / 初试(2)**
```
放弃：面试等级(选填) + 面试评价(选填)
通过：工作城市(必填) + 下一环节(必填,可选[集体面试1/初试2/复试3]) + 下一环节面试官(必填) + 面试等级(必填) + 面试评价(必填)
```

**环节二：复试(3)**
```
放弃：面试等级(选填) + 面试评价(选填)
通过：工作城市(必填) + 下一环节(必填,可选[复试3/通道面委100/用人决策者200/HR面试5]) + 面试等级(必填) + 面试评价(必填)
```
下一环节面试官逻辑（仅通过时）：

| 下一环节 | 面试官字段 | 特殊逻辑 |
|---|---|---|
| 复试(3) | 下一环节面试官 | 普通必填 |
| HR面试(5) | HR面试官 | 普通必填 |
| 通道面委(100) | ①通道面委处理人(默认带出可改) ②HR面试官(必填) | 系统默认带出面委处理人；并行增加 HR 面试环节 |
| 用人决策者(200) | ①用人决策者面试官(必填) ②HR面试官(必填) | 两字段分别填充 |

> ✅ **复试推进实测结论**：
> - **复试→用人决策者(200) 是并行环节**：`nextSteps` 必须放 **2 个元素** `[{stepId:200,staffId},{stepId:5,staffId}]`（用人决策者 + HR面试官），提交成功后同时开出两条并行待办。
> - **复试→HR面试(5) 是单环节**：`nextSteps` 放 1 个元素 `[{stepId:5,staffId}]`。
> - ⚠️ **复试待办的 `flowTraceId` 在每次流程写操作后会动态刷新**（旧 traceId 立即失效）。用稍早拉取的 traceId 提交可能返回 `1005`，但后端**可能已成功写入**。规则：提交复试前**务必紧邻提交那一刻重新拉一次 `get_campus_interview_todo_list` 取最新 traceId**；若返回 1005，**不要盲目重试**，先用 `getResumeByRId` 查简历环节历史确认是否已写入。

**环节三：用人决策者面试(200)**
```
放弃：面试等级(选填) + 面试评价(选填)
通过：工作城市(必填) + 面试等级(必填) + 面试评价(必填)  （末环节，无"下一环节"，nextSteps 可空）
```

**环节四：HR面试(5) / 通道面委(100) —— 本子流程不支持提交，引导至系统**

> ⚠️ 一旦识别用户意图是提交这两类环节的评价，**明确告知并引导用户前往招聘系统 Web 端完成填写与提交**，不凭 stepId 硬套其他环节字段逻辑去 MCP 提交。

识别信号：待办当前节点 `step_id=5`（HR面试）或 `=100`（通道面委）；或用户说"提交 HR 面试/HR 面评""提交通道面委/面委评价"。

引导话术（保持简洁，**不暴露技术原因**）：
> 「HR 面试环节和通道面委面试环节暂不支持提交，请前往招聘系统进行填写和提交。」

> ✅ **区分：仅"推进"到这两类环节是被支持的**。复试(3)通过时，可在 `nextSteps` 把候选人推进到 HR面试(5)/通道面委(100) 并指定面试官——这是开出下一环节待办，不是"提交 HR/面委环节面评"。本环节规则只约束"作为当前待提交节点、由本子流程提交其面评"的场景。

### SE-7 提交（Step-by-Step，含 R2 受控写）

**Step 1 · 收集字段值**

基于已定位待办环节，按「各环节字段逻辑」逐步引导用户填写必填字段（无需再问候选人/环节/角色）。
> 🔎 **提交前必做**：先执行 SE-4 差异化提示语查询——命中则返回 tips/evaluate 并暂停；用户给内容后先做 SE-5 拆分二次确认，再继续收集其余字段。
1. 先问「面试结果」（通过/放弃）——关键分支点。
2. 通过 → 按必填顺序：工作城市 → 下一环节（若有）→ 相关面试官 → 面试等级 → 面试评价。
3. 放弃 → 选填面试等级和评价（不强求）。
> 收集到面试官姓名/账号后按 SE-3 解析为数字 staffId。

**Step 2 · 面试官权限校验（如涉及）**

用户提供下一环节面试官后，校验该账号是否具备对应环节面试官权限。失败则原样展示错误、要求更换。

**Step 2.5 · 简历准入控制校验（提交前必做）**

调 `get_resume_control_info` 查候选人是否允许在当前环节提交面评：
- **入参 `ctrlType`**：本子流程 4 环节（集体面试/初试/复试/用人决策者，提交通过）→ **`CommitPassInterviewFlow`**（实测有效码；传假码后端返 `1015 参数不合法`，反证此码有效）。
- **入参 `resumeIds`**：候选人简历 ID 列表（不能为空）。
- **判定**（`actionEnable` 与 `showHint` 两个独立维度）：
  - `actionEnable=false` → **禁止提交**，把 `hintList`（`{简历名称}：hintText`）原样展示后停止。
  - `actionEnable=true & showHint=true` → **允许但有提醒**：先展示 `hintList` 话术，**待用户知悉后再继续**。
  - `actionEnable=true & showHint=false` → 无限制，直接继续。
  - ⚠️ 二者都是多简历全局汇总值；批量时结合 `hintList` 的 `{简历名称}` 前缀逐人核对。
- 命中黑名单/限制名单应在提交前拦截，**不要跳过此步直接撞错误**。

**Step 3 · R2 二次确认（受控写契约 · 强制节点）**

**在调用 `submit_interview_flow_trace` 之前，必须完成受控写握手。本动作使用 `capability-registry.yaml` 中的 `campus_evaluation_submit` 受控写定义。**

1. **冻结 payload**：按注册表 `payload_fields` 生成最终请求体（缺省字段用明确 `null`/`false`/空数组），写入临时文件。
2. **展示业务卡片并确认**（确认有效期 10 分钟）：
   ```
   ── 面评提交确认 ──
   候选人：[姓名] (ID: [xxx])
   当前环节：[环节名称]
   操作角色：[本人提交 / 代[被代提交人xxx]提交，操作人[当前用户yyy]]

   面试结果：[通过/放弃]
   工作城市：[xxx]
   下一环节：[xxx]
   下一环节面试官：[xxx] (staffId: [nnn])
   面试等级：[S/A+/A/A-/B]
   面试评价：[摘要或全文]

   请确认以上信息无误？确认后将提交。
   ```
   展示业务可读信息，**不展示** Token/Cookie/完整内部 payload。
3. **用户明确确认后**，一条命令完成「算摘要 + 生成信封 + preflight」：
   ```bash
   python3 scripts/build_write_envelope.py prepare \
       --action-key campus_evaluation_submit \
       --payload "$TMP_DIR/payload.json" \
       --target-ids <traceId> \
       --summary "校招面评提交：trace {traceId} / {结果} / {等级} / 下一环节 {环节名}" \
       --out "$TMP_DIR/envelope.json"
   ```
   脚本自动带出注册表配置并校验 payload 字段白名单与敏感信息（详见 `scripts/README.md`）。
   ⚠️ `--summary` 禁含手机号/邮箱；面评正文不要塞进 summary（正文在 payload 里，摘要只写结论）。
   > 回退手工路径：`validate_write_action.py --digest < payload.json` → 手工拼信封 → `--phase preflight`。
4. payload 任一字段变化、确认过期或目标变化 → 旧确认失效，必须重新冻结、重新确认、重新 `prepare`。
5. 用户要改 → 回对应步骤修正后**重新确认**；用户取消 → 终止。

> 🚫 未经 R2 确认、或用户未明确说"确认"，禁止调用提交接口。

**Step 4 · 调用提交接口（组装参数）**

R2 确认通过后，调用前将信封状态置 `submitted`，再调 `submit_interview_flow_trace`。参数骨架示例（"通过 → 推进到复试"，ID 均为占位）：
```json
{
  "traceId": "<面评待办 traceId>", "result": 2, "rankId": 1,
  "comment": "……（SE-5 拆分后的结构化文本或用户原文）",
  "workCity": 1, "workCityName": "深圳总部",
  "rankName": "S", "resultName": "通过",
  "nextSteps": [ { "stepId": 3, "staffId": "<下一环节面试官工号>", "staffFullName": "<面试官中文名>" } ]
}
```
**字段映射要点**（编码以写接口 schema 为准）：
- `result`：**通过=2，放弃=3**；`resultName` 同步填文本。
- `rankId`：**S=1/A+=2/A=3/A-=4/B=5**；`rankName` 同步。后端保留 6=C 但前端不展示，除非系统回传否则不用。
- `workCity`+`workCityName`：编码+文本，用 `get_interview_dictionary_config` 对齐。
- `nextSteps[].staffId` = 被代提交面试官（实际处理人）的 staffId；`nextSteps[].stepId` 下一环节编码（1/2/3/5/100/200）。
- **代提交语义**：`nextSteps[].staffId`=实际处理人；`update_by` 系统自动记为当前 MCP 登录用户（代提交人）。两者不同勿混。
- `comment`：≤5000 字，超限提示用户精简。
- `draftFlag`：布尔，默认不传=正式提交。**用户说"先存草稿/暂存"时显式传 `draftFlag:true`**；草稿模式 result/nextSteps 约束放宽。
- `nextSteps` 通过时必填，但**用人决策者(200)是末环节可空**；其余环节通过时至少 1 元素（并行 2 元素）。
- `aiCodingEvaluateItems`（可选）：仅 AICoding/编程岗环节有——模板返回编程维度时按维度收集评分填入，普通岗位留空。

**Step 5 · 提交后审计**

- **成功**（`status/code == 200`）→ 审计状态 `success`，`audit.ref` 用 `traceId`：
  ```bash
  python3 scripts/build_write_envelope.py outcome \
      --envelope "$TMP_DIR/envelope.json" --status success --ref <traceId>
  ```
- **明确业务失败** → `--status failed --error-code "<真实错误码/errorMsg 原文>"`。
- **超时/空响应/泛化错误** → `--status unknown`，**禁止自动重试**（见 SE-8 软错协议）；任何重试都需新确认记录。
- 审计完成后删除 `$TMP_DIR` 下的 payload / envelope 临时文件。
  > 回退手工路径：`python3 ../../scripts/validate_write_action.py --envelope <envelope.json> --phase outcome`（需先手改 `audit` 字段）。

> ⚠️ **提交后权限弹窗**：MCP 写接口首次调用会触发平台权限审批弹窗，用户需点「跳过」两次才能完成。**这不是失败，是平台正常权限确认**。提交成功标志是接口返回成功结果，而非弹窗消失。

---

## 三、失败诊断（code 1005 / 面试流程信息不存在）

| 成因 | 现象 | 判定方法 | 处理 |
|------|------|---------|------|
| ⓪a traceId=null/未传 | 传 null 或不传 | 实测返回 `code 500 面试流程TraceID不能为空` | 拿有效 `flowTraceId`(>0) 再提交 |
| ⓪b traceId=0/负数 | 传 0 或负数 | 实测返回 `code 1005 面试流程信息不存在` | 拿有效 `flowTraceId`(>0)，别用占位/空值试探 |
| ① traceId 用错 | 误用 flow_id/current_step | `get_interview_evaluate_template(错误ID)` 返回"节点不存在" | 用正确 `flowTraceId` 重试 |
| ② 节点已被提交关闭 | 用户/他人/Web 端已先提交，status=1 | `get_interview_evaluate_template(正确traceId)` 能返回配置，但简历详情 `flows` 该节点 `status=1` | **无需再提交**，用简历详情复核确认已写入 |

> 🔑 **判重核心技巧**：提交报错后先拉 `getResumeByRId` 看该节点 `status`：若已是 `status=1` 且 result/rank/comment 符合预期，说明**目标早已达成**（多半 Web 端已提交），MCP 报错只因节点已关闭。**不要反复重试**，向用户说明即可。

### SE-8 其他失败码速查（区分「软错/可重试」与「硬错/参数问题」）

| code | message | 触发条件 | 性质 | 处理 |
|------|---------|---------|------|------|
| **1008** | `当前有面试官正在操作，请稍后再试` | 同一 traceId 并发提交 | 🟡 软错/并发锁 | **稍后串行重试**（间隔 1~2s），**不可判硬失败、不可换参数**；重试前用简历详情复核是否已写入 |
| **500** | `重复执行！` | 对已落库(status=1) traceId 再提交 | 🟡 幂等拦截 | 等价"已提交过"，简历详情确认即可，**不要再试** |
| **500** | `面试流程TraceID不能为空` | traceId 传 null/未传 | 🔴 参数缺失 | 拿有效 flowTraceId(>0) 再提交 |
| **1015** | `参数不合法，工作城市: null` | 通过(2)缺 workCity | 🔴 必填缺失 | 补 workCity（通过必填）|
| **1015** | `参数不合法，面试评级值: 99` | rankId 非法枚举（合法 1~6）| 🔴 枚举非法 | 用合法 rankId（1=S/2=A+/3=A/4=A-/5=B）；rankId 校验优先级高于 nextSteps 必填 |
| **1015** | `参数不合法，不支持的面试结果: 99` | result 非 2/3 | 🔴 枚举非法 | result 只能 2/3 |
| **1015** | `参数不合法，操作类型=xxx` | get_resume_control_info 传假 ctrlType | 🔴 码值非法 | 用真实准入码 `CommitPassInterviewFlow` |
| **1002** | `下一环节列表不能为空` | 通过(2)非末环节缺 nextSteps | 🔴 必填缺失 | 补 nextSteps（末环节用人决策者200可空）|

> 📌 **统一响应结构**：所有失败均 `status=200 + data.code≠200 + success=false + message 明确带原因`，无笼统"操作失败"。判成败以 `code==200` 为准，`message` 已足够定位，无需盲试。

---

## 四、复核方法（提交后/报错后必做）

用 `get_v1_mcp_resume_getResumeByRId`(rid) 拉简历详情，在 `interviewRecords.flows` 找对应节点核对：
- `flowTraceId` 是否匹配
- `result` / `rank_id` / `comment` / `workCity` 是否符合预期
- `status` 是否为 1（已提交）
- `staff_id`（处理人）与 `update_by`（代提交人）是否正确

示例（贾牛命，流程 391336，复试节点）：
```
flow_id=<流程ID>, flowTraceId=<面评 traceId>
staff_id=<实际处理人工号>(<实际处理人姓名>), step_id=3(复试)
result=2(通过), rank_id=1(S), comment="……"
status=1(已提交), update_by=<代提交人工号>(代提交场景下为当前登录用户)
→ 全部符合，代提交成功、数据无误。
```

---

## 五、注意事项

1. **评价内容规范**：提醒面试官用文明用语，勿用"拉黑"等负面/歧视性表达。
2. **保存草稿 vs 提交**：用户想暂存 → 显式传 `draftFlag:true`。
3. **批量场景**：多名候选人逐个走完流程，不合并提交。
4. **错误恢复**：提交失败保留已收集字段，方便重试/复核。
5. **代提交标注**：任何代提交，R2 确认与最终说明必须明示「代[被代提交人]提交，操作人[当前用户]」。
6. **合规**：候选人姓名可内部展示，手机号/邮箱等敏感字段脱敏；面评内容不外传。

---

## 六、已知未覆盖 / 边界

| # | 场景 | 现状 | 建议处理 |
|---|------|------|---------|
| 1 | HR面试(5)/通道面委(100) 作为当前待提交节点 | 不支持提交（竞企/HR必问属前端独立表单，MCP 无字段）| 引导 Web 端提交，不硬套其他环节规则 |
| 2 | 草稿(draftFlag=true)字段校验放宽程度 | 未列具体可空项 | 草稿模式少校验，直接透传已填字段，正式提交再补齐 |
| 3 | AICoding/编程岗 aiCodingEvaluateItems 逐维度收集 | 字段存在但未给收集流程 | 模板返回编程维度时参照 SE-5"拆分+确认"逐维度收集 |
| 4 | 准入 showHint=true 后用户拒绝知悉/不回复 | 未定义兜底 | 未明确知悉前不得提交；明确放弃则终止 |
| 5 | 并行环节(100/200)其中一个面试官权限校验失败 | 未定义部分失败处理 | 任一 nextSteps 元素校验失败→整体阻断，要求更换后重试，不提交半个 |
| 6 | 同一候选人同环节多个 flowTraceId | 未覆盖 | 提交前用简历详情 flows 核对目标节点唯一性，多条请用户确认 |
| 7 | result 除通过/放弃外的其他态 | 只处理 2/3 | 模板出现其他 result 枚举先 SearchAPI 复核，勿臆造映射 |
| 8 | workCity 字典未命中/多地点 | 单值示例 | 用 get_interview_dictionary_config 全量匹配，查无编码请用户确认 |
| 9 | rankId=6(C) 后端保留位 | 前端不展示 | 除非系统回传 C，否则不主动使用/展示 |

> 📌 通用兜底：凡 stepId/字段必填/枚举无法从本子流程明确确认的，一律以生产接口实测返回（`SearchAPI` schema + `get_interview_evaluate_template` 模板）为准，不猜测、不硬套。

---

## 附录：评价内容拆分示例（SE-5 参考）

**PCG 初试**（用户自由文本→结构化）：
> 用户原话："专业能力还行，综合素质一般，在面试中感觉该候选人对本次面试准备了很充分，对于该岗位有较为强烈的意愿。综合考虑下来，给予通过的建议，让候选人进入到下一轮面试。"
> → 拆分：【1、专业能力】专业能力还行。【2、综合素质】综合素质一般。【3、人选意愿度及其他】对本次面试准备充分，对该岗位有较强意愿。【4、基于以上，综合结论】综合考虑给予通过建议，进入下一轮。

**SD 商业分析师**：按 `1、问题组织拆解 / 2、分析推导 / 3、总结提炼 / 4、行业理解 / 5、沟通表达 / 6、软性素质 / 7、其他 / 面试case记录` 归集（各维度含分数）。

**FiT P族**：按 `底线要求-热爱/聪明/坚韧 / 加分项-锐气/AI学习与应用 / 其他评价` 归集（各项含 A/A+ 等级）。

> 拆分只做结构归集，不编造不篡改；用户确认（或修正后确认）才作为 `comment` 提交。
