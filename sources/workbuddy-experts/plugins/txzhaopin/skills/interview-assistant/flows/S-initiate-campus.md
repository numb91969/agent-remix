# 面试助手 · SC 校招发起面试子模块

> 子模块路径：`flows/S-initiate-campus.md`
> 触发：主 `SKILL.md` 的 Router-0 命中「发起校招面试 / 推进校招候选人到面试环节 / 发起 2026 青云实习」后，必须先读取本文件。
> 定位：为**校招 / 实习**候选人简历创建面试流程（写接口 `start_campus_interview`）；成功并回读最新状态后，再交给 `flows/S.md` 安排本轮面试。

在招聘系统（zhaopin.woa.com）中，对有权限的**校招 / 实习**候选人简历一键发起面试流程，覆盖从"发起面试"到成功创建面试待办的完整链路，并支持从自然语言指令中智能提取关键词自动填充、对多名候选人批量发起。

> ⚠️ 本子流程只处理**校招 / 实习**（写接口 `start_campus_interview`，用整数 `stepId` / `recruitProject`）。**社招发起走 `flows/S-initiate-social.md`**（写接口 `recruit.interview-flow.start_interview`，用 `FlowStepGroup.FlowSteps[]` + StepCode），两套字段完全不同、禁止互相套用。若无法判断校招/社招，先反问确认通道再选对应子流程。

---

## 一、触发词与使用时机

当用户表达以下**校招 / 实习**面试发起意图时进入本子流程：

- 「帮我发起 XX 的校招/实习面试」/「给这份校招简历发起面试」
- 「发起面试流程」「开始面试」「发起 2026 青云实习」「推进到面试环节」
- 对某位校招/实习候选人 / 某份 RID 简历需要进入面试环节
- 「对 A、B、C 批量发起校招面试」（批量模式）

**前置条件**：
- 已连接生产 `recruit-mcp` 连接器（同 SI 社招发起，见「二、生产连接器与调用规范」）
- 当前用户对该简历拥有「发起面试」权限（通常为招聘经理 / 面试官角色）
- 当前用户已完成**面试官视频课程学习**（否则会被前端引导拦截，属页面级提示，见 Phase 0.2）

---

## 二、生产连接器与调用规范（每次会话首次调用前确认一次）⚠️

校招简历搜索、控制校验、下拉选项、组织/职位反查、`start_campus_interview` 发起及后续核验，统一使用专家包注册的**生产连接器 `recruit-mcp`**。整条链路必须保持在同一生产连接器中，禁止混用测试连接器或复用其他环境返回的 RID、interview_id、staffId。

调用前必须：

1. 通过 `SearchAPI(query=..., domain="recruit")` 探测目标能力，再用 `SearchAPI(apiId=...)` 获取当前生产 schema。
2. `CallAPI` 只接受 SearchAPI 返回的原始完整三段式 apiId，禁止自行拼造，**禁止通过 `_extra` 等无业务字段绕过网关校验**——如出现 `TYPE_MISMATCH` 等参数类型错误，以 SearchAPI 返回的正确类型重试，仍失败则降级到简历详情页。
3. 若生产 SearchAPI 未返回 `recruit.campus-interview-service.start_campus_interview`，停止自动写入并降级到校招简历详情页，不得切换到测试连接器。
4. 所有读写均使用同一连接器；发起成功后必须在同一连接器回读状态，再进入面试安排。

> 📌 详细接口参考：`../references/interview-lifecycle/campus-initiation-api.md`。

### 性能与正确性四原则（每次发起都必须遵守）

1. **只读调用并行发、结果缓存复用**：无依赖的只读接口一次性并行发出（≤5/批）；半静态下拉项（项目/年份/线路/环节）与**会话级稳定参数（staffId / subDepartment / position）**缓存到会话级，不为每个候选人重拉慢接口。
2. **写接口软错先核实再决定**：返回"正在操作/状态不可发起"等软错时，**禁止立即重试**，先 `getResumeByRId` 核实是否已落库（见 Phase 3 协议）。
3. **连接中断只重发失败项**：偶发 `Connection closed` / `socket hang up` 等瞬时错误时，**仅重发失败的调用（不重跑整批）**，必要时先 `SearchAPI` 重载 schema 再重试。
4. **慢接口提前标注**：`get_campus_interview_todo_list`（取 staffId）、`org_lookup`（组织反查）偏慢，给足超时（≥120s），不要因慢就反复重发。

---

## 三、会话级稳定参数预解析（一次性，省去每候选人慢调用）⚡

以下参数**与候选人无关、整会话恒定**，应在会话首次发起时解析并缓存，后续候选人直接复用：

| 参数 | 来源 | 解析 / 缓存方式 |
|------|------|----------------|
| `staffId`（当前用户工号） | 个人信息接口（首选）/ 待办列表回退 | 会话首次调一次 `get_personal_api_web_personal_infoDetail` 取 `staffId` 缓存（见 Phase 2.5）|
| `subDepartment`（目标组织 ID） | `org_lookup` 反查（首选）；待办列表按组织路径匹配（回退）| 优先调 `org_lookup` 按组织名/路径反查 `orgId` 缓存；多命中/零命中时回退待办列表扫描 |
| `position`（职位 ID） | `position_lookup` 按职位名反查（首选）| 用户提供职位名 → 调 `position_lookup` 反查 `postId` 缓存（见 Phase 2.7）|
| `recruitYear`（招聘年份） | `get_interview_recruit_year` 按类型反查 | **必查**，不可从毕业年份推导（见 Phase 2.2.2）|

> ⚡ 这样每候选人路径收敛为：候选搜索 → 控制校验 → 写接口 → 成功核验，约 4 次调用。

### 🔥 Phase 1 预热批（强烈建议 · 省掉后续零散往返）

会话首次发起时，把**全部与候选人无关的只读项一次性并行发出**（≤5/批，两批打完），结果缓存整会话复用：

| 批次 | 并行发出 | 得到 |
|:---:|---|---|
| 第 1 批 | `get_personal_api_web_personal_infoDetail` · `get_interview_recruit_project(filterStart=true)` · `get_interview_recruit_line` · `get_interview_start_step` · `check_course_learn_status` | staffId / departmentId / 项目下拉 / 线路下拉 / 环节下拉 / 课程状态 |
| 第 2 批 | `get_interview_recruit_year(recruitType=1)` · `get_interview_recruit_year(recruitType=2)` · `org_lookup(<组织名>)` · `position_lookup(<职位名>)` | 两种类型各自可选年份 / subDepartment / position |

> 🔴 **反面教训**：把这些拆成十几轮零散调用（每次现用现取）会让单次发起从 ~5 次调用膨胀到 20+ 次，且中间任一超时都要重来。**年份两种类型都拉**，因为类型可能在确认环节被用户改动，预先拿到可避免二次往返。

---

## 四、完整工作流（Workflow）

严格按阶段顺序执行。**Phase 0 前置校验**、**Phase 2.3.5 已在流程预判断**、**Phase 2.5 R2 二次确认**、**全链路提示/报错展示（贯穿始终）** 为硬性节点，不可跳过。

> 🔴 **全链路报错透传总则（贯穿 Phase 0→4，必须遵守）**
> 从前置校验、候选反查、发起提交，到结果核验——**任何一步返回的提示（hint）、警告（warning）、报错（error）都必须原样、显式地展示给用户，不得吞掉或改写为泛化的"操作失败"**。

### Phase 0 — 前置校验（Pre-checks）

打开表单前完成三项校验，任一不通过则终止并提示用户：

#### 0.1 简历控制限制校验

```
CallAPI(apiId: "recruit.campus-interview-service.get_resume_control_info", params: {
  resumeIds: [简历ID],   // 批量时传全部有效 ID 数组，一次校验多人
  ctrlType: "StartInterview"
})
```

判断逻辑：
- `data.actionEnable === true` → 通过，继续
- `data.actionEnable === false` → 终止，展示 `data.hintList` 中每条原因话术

> ⚠️ **`actionEnable=true` 只是"必要非充分"门槛**：控制校验与写路径是两套独立判断（手机号、简历实时状态、测评状态等）。实测出现过 `actionEnable=true` 但写接口仍因"手机号不能为空"/"简历状态不可发起"/"综合测评未完成"被拒。最终以 `start_campus_interview` 实际响应为准。
> 📦 **批量模式**：把全部有效候选人 `resumeIds` 放进同一数组一次调用，逐人解析 `actionEnable`；`false` 者移出批次并记录 `hintList`。

#### 0.2 面试官课程学习状态校验（页面级提示，非后端强制）

```
CallAPI(apiId: "recruit.campus-interview-service.check_course_learn_status", params: {})
```

- `data.finishFlag === true` → 通过
- `data.finishFlag === false / null` → 提示用户前往 `data.learnUrl` 完成课程（页面级引导拦截；后端 `start` 接口不因课程未学而拒绝，本步仅为对齐网页端行为、提前提示）

#### 0.3 获取可发起的面试环节步骤

```
CallAPI(apiId: "recruit.campus-interview-service.get_interview_start_step", params: {})
```

返回可用步骤列表（`stepId=1 集体面试`、`stepId=2 初试`），供后续表单填写。
> 🔴 **发起环节仅 1（集体面试）/ 2（初试）两个可选**。"复试"及以后是流程流转产生的后续环节，**不能作为发起 stepId**；实测硬传 `stepId=3/5/999` 后端统一硬拦并返回"该环节不可直接发起面试，只能从集体面试或初试发起"。指令里出现"复试"等应在 skill 层就拦下并提示用户。

### Phase 1 — 获取下拉选项（首拉 + 会话级缓存）

| 表单字段 | API 接口 | 说明 |
|----------|---------|------|
| 招聘项目 | `get_interview_recruit_project` | 参数 `filterStart=true`；**会话级缓存** |
| 招聘年份 | `get_interview_recruit_year` | 仅当 `recruitType` 确定后调用（依赖类型）|
| 招聘线路 | `get_interview_recruit_line` | 返回启用的线路列表；**会话级缓存** |
| 面试环节 | `get_interview_start_step` | Phase 0.3 已拉，复用即可 |
| 面试组织 | `org_lookup` | 按组织名/路径反查 `orgId`（Phase 2.4）|
| 职位 | `position_lookup` | 按职位名反查内部通道职位 ID（Phase 2.7）|

**并行策略**：本次会话首次发起时，下拉三件套 + 课程 + 环节与候选搜索同批一次性并行发出并缓存；同会话后续候选人直接复用缓存（除非 `recruitType` 切换需重查 year）。候选搜索返回的 `resumeIds` 是控制校验（0.1）的依赖，控制校验需等搜索返回后再发。

### Phase 2 — 自然语言信息提取与表单组装

从用户自然语言指令提取关键词，自动映射到发起字段，减少逐项询问。

#### 2.1 关键词提取规则

| 用户原话关键词 | 提取字段 | 映射逻辑 |
|----------------|---------|----------|
| 「2026 届」「26 届」「2026 年」 | `recruitYear=2026` | 年份数字提取 |
| 「实习」「青云实习」「日常实习」 | `recruitType=2`（实习生）| 含"实习"→实习生；含"应届/校招"→应届毕业生 |
| 「青云实习」「青云计划」「项目实习」 | `recruitProject` | 见 2.2 反查（最长短语匹配）|
| 候选人名 / RID | `resumeIds` | 见 2.3 反查（同名多人强制确认）|
| 「集体面试」「初试」 | `stepId` | 集体面试=1，初试=2（仅这两个可选）|
| 地点/线路词（深圳/北京/远程/线上）| `recruitCity` | 从线路下拉匹配；**未提及任何线路词 → 默认远程面试(48)，不追问**（见 2.2.1）|
| 职位名（后台/前端/产品经理/视觉设计）| `position` / `positionOuterTitle` | 通过 `position_lookup` 反查内部通道职位 ID（Phase 2.7）|
| 「我作为面试官」「指派给张三」 | `staffId` | 不提则**必须显式传当前用户工号**（不能留 null）|

**提取原则**：能明确映射的字段自动填充、不必再问；ID 型字段（`recruitProject`/`position`）必须经反查拿到真实 ID；未提取到且无默认值的必填字段，Phase 2.6 一次性列出询问。

#### 2.2 反查：项目名 → 项目 ID（含类型-项目白名单校验）⚠️

复用 Phase 1 已拉的 `get_interview_recruit_project`。匹配必须按顺序：

**0. 招聘项目白名单（按招聘类型，硬约束）**

| 招聘类型 `recruitType` | 允许招聘项目（title 白名单）|
|------------------------|------------------------------|
| `1`（应届毕业生）| `无/空`、`产品经理培训生`、`青云计划` |
| `2`（实习生）| `日常实习`、`应届实习`、`项目实习`、`青云实习` |

> 🔴 **后端不校验类型-项目白名单**（责任链无对应 Validator）——错配在简历状态允许时会真落库造成脏数据。**本白名单校验是 skill 唯一防线，绝不可跳过或指望后端兜底。**

**1. type 预筛 + 冲突校验**：先按 `recruitType` 过滤下拉项目；当用户同时明确了类型与项目、但项目不在该类型白名单中 → **判定"类型-项目不匹配"，立即中断并显式提示**（列出该类型允许的项目 + 冲突项目所属正确类型 + 让用户在"改类型/改项目"间二选一），**禁止静默剔除或自动代换**。

> 示例：用户说「实习生 + 青云计划」→ 实习生白名单不含"青云计划"（它属应届毕业生），触发冲突提示，请用户在「改类型为应届毕业生」或「改项目为青云实习」间二选一。

**2. title 模糊匹配**：在筛后列表中按关键词匹配 `title`，**优先最长短语**（"青云实习" > "青云"）。

**3. 判定**：唯一命中→取 `id` 作 `recruitProject`；多命中→展示候选让用户选；零命中→提示未找到，请用户提供更准确名称。

> 🔴 **为什么必须 type 预筛**：下拉中同时存在 `青云计划`(type=1,校招) 与 `青云实习`(type=2,实习)。只按"青云"模糊匹配两者都命中会误选；先按 `recruitType` 预筛可精准锁定。

#### 2.2.1 招聘线路默认值：未提供 → 默认远程面试(48)⭐

`recruitCity` 为必填，但**用户未提供任何线路/地点信息时，自动默认「远程面试」(`recruitCity=48`)，无需追问**。
- 出现城市/线路词 → 复用线路下拉按 `value` 匹配取 `key`（深圳=11、北京=8、上海=5、广州=3 等）
- 无任何线路信息 → 默认 48，不作为缺失必填字段追问
- "远程/线上" → 显式命中 48
- 二次确认卡片如实回显「招聘线路：远程面试(48)」，让用户有机会改成具体城市

#### 2.2.2 招聘年份：必须走下拉反查，禁止用毕业年份 🔴⭐

`recruitYear` 是**招募周期年（招聘活动所属年度）**，**不是候选人毕业年份**。两者经常不相等，尤其实习生。

```
CallAPI(apiId: "recruit.campus-interview-service.get_interview_recruit_year", params: { recruitType: <1 或 2> })
// 返回 integer 数组，如 [2026] / [2026, 2027]
```

**硬规则**：

1. **必查**：进入 Phase 2.5 前必须调一次本接口拿到该 `recruitType` 的**允许年份集合**，不允许跳过。
2. **禁止从毕业时间推导** `recruitYear`。简历里的 `graduate_time` / `graduateTimeTxt` 只用于判断候选人届别，**与本字段无关**。
3. **取值优先级**：
   - 用户明确说了年份且该年份 ∈ 允许集合 → 用用户的
   - 用户明确说了年份但 ∉ 允许集合 → **中断并显式提示**"您指定的 {年份} 不在当前【{类型}】可选年份 {集合} 内，请二选一：改年份 / 改招聘类型"，**禁止静默改成集合里的值**
   - 用户未提年份 → 集合仅 1 个值时直接取用；多个值时取最小（最近在招周期），并在 R2 卡片如实回显让用户有机会改
4. **年份集合按 `recruitType` 分岔**：实习生与应届毕业生的可选年份**不同**，切换类型必须重查（预热批已两种都拉时直接切缓存）。
5. **R2 卡片必须回显年份来源**：形如「招聘年份：{年份}（该类型可选：{集合}）」。若候选人毕业年与之不同，加一句"候选人 {毕业年} 届，招聘年份按系统在招周期填 {年份}"，避免用户误以为填错。

> 🔴 **反面教训**：曾按候选人毕业年份（远于当前周期）组装 payload，若不查本接口直接提交，将写入不存在的招聘周期或被后端拦截。**"毕业年 ≠ 招聘年"是本流程最高发的隐性字段语义坑。**

#### 2.3 反查：候选人名 → 简历 RID

```
CallAPI(apiId: "recruit.campus-resume-search.post_v1_resume_search", params: {
  name: "张三",
  startInterviewEnable: 1,             // 仅返回当前用户可发起面试的简历
  searchId: "mcp-campus-{随机uuid}",   // 每次搜索必传（随机 UUID），分页时保持不变
  page: 1, limit: 20
})
// 从 data.list 匹配姓名 → 取 id 作 resumeIds（注意：字段名是 "id" 不是 "resumeId"）
// rid 是 UUID 字符串（如 "4dd31196-..."），id 是整数（如 2482815），两者都是必取
// 单条简历链接：https://zhaopin.woa.com/resume/campus/ResumeDetail?rid={rid}
```

> ⚠️ **搜索返回字段名差异（实测 2026-08-03）**：`resumeId` 在搜索结果中字段名为 **`id`**（整数），不是 `resumeId`。`rid` 是 UUID 字符串。批量收集时应取 `{name, id, rid}`（`id` 即 `resumeIds` 数组元素）。

批量模式：对多个姓名并行搜索（≤5/批，各自独立 `searchId`），逐个收集 `{name, id, rid}`（`id` 即 resumeId）。

> ⚠️ **手机号脱敏 ≠ 资料完整**：搜索/网页返回的手机号是脱敏掩码（`150****3559`），只供辨识同名候选人，**不代表主库手机号真实非空**。真正的手机号非空以写接口响应为准。掩码只用于同名确认，不作发起前置资料完整性依据。

**0 结果回退（两步判定，结论必须显式告知用户）**：
1. 带 `startInterviewEnable=1` 返回 0 条 → 去掉过滤、仅用 `name` 重试一次。
2. **重试有结果（简历存在）** → 说明**用户对该简历无发起权限**。明确告知：`⚠️ 无法发起：您对该简历没有发起面试的权限。简历 RID：{rid}，链接：{ResumeDetail}`，**终止流程、不进入确认**；建议确认候选人是否走活水/社招通道、换有权限账号、或联系 HR 开通权限。
3. **重试仍 0 条** → 判定"不在校招库"（可能在活水/社招通道），提示用户确认候选人类型。

##### ⚠️ 同名歧义：强制确认规则（硬性节点）

搜索结果匹配到多名同名且均可发起的候选人时，**必须暂停自动填充，强制用户确认**，不得默认取第一个：

1. 展示候选清单（每项列 姓名/rid/手机号(脱敏)/简历链接/学校或意向）
2. 请用户用「① 简历ID ② 手机号(用 `mobile` 重新精确匹配) ③ 简历链接(提取其中 rid)」任一方式确认；**邮箱不支持**（接口不返回也不支持按邮箱查询）
3. 命中唯一一份 → 取 rid 继续；命中零/多份 → 重新展示清单请用户换标识；用户放弃 → 终止

> 🚫 未完成同名确认前，绝不允许带模糊 resumeIds 进入 Phase 2.5 / Phase 3。

#### 2.3.5 候选是否已处于面试流程中预判断（防重复发起）⚠️ 必做

在 Phase 2.3 解析出 `rid` 后、进入 Phase 2.5 之前，**必须**先判断候选人是否已在面试流程中：

```
CallAPI(apiId: "recruit.campus-resume-search.get_v1_mcp_resume_getResumeByRId", params: { rid: "r-abc123" })
// 遍历 data.interviewRecords，看 status
```

> 🔴 **API ID 完整性提醒（实测 2026-08-03）**：短名 `recruit.campus-resume.getResumeByRId` 不存在（报 TARGET_NOT_FOUND）。**必须使用完整三段式** `recruit.campus-resume-search.get_v1_mcp_resume_getResumeByRId`。若不确定 API ID 是否有效，先 `SearchAPI(query="getResumeByRId campus")` 验证。

判定：
- 存在任一 `status=0`（进行中/已发起未结束）→ 判定"已在面试流程中"，进入提示分支
- `interviewRecords` 为空或均非 `status=0` → "未在流程中"，正常继续

> 📝 **读不到时勿阻断**：`getResumeByRId` 需面试官权限或为该简历伯乐；无权限读不到时不阻断，交由 Phase 0.1 / Phase 3 兜底。

**提示分支（已在流程中）**：展示现有进行中面试（环节/项目/年份/状态 + 去处理链接），请用户决策"仍要发起"或"跳过"。用户未明确"仍要发起"前不得进入 Phase 2.5。批量模式对每人执行，命中者按此处理，不阻塞其他人。

#### 2.4 反查：组织名 → subDepartment ID（org_lookup）

```
CallAPI(apiId: "recruit.recruit-standard-resource.post_api_mcp_org_lookup", params: {
  orgNameCn: "BP组"   // 组织末级名或完整路径
})
// 取 data.orgId 作 subDepartment；data.orgFullNameCn 全路径用于回显确认
```

判定：唯一命中→取 `orgId` 并回显全路径；多命中(`data=null`+提示)→请用户补上级组织路径；零命中→请用户提供组织 ID 或完整路径。
> 回退：`org_lookup` 无法唯一确定时，扫描 `get_campus_interview_todo_list` 按 `subDepartmentTxt`/`fullOrgName` 匹配取 `subDepartment`，或请用户从发起面试页「面试组织」下拉取数字 ID。拿到后仍以二次确认节点回显。

#### 2.5 获取当前用户工号（staffId 来源）⚠️

`staffId` **必填且必须显式传入**（留 null 报"面试官信息不存在"）。

获取优先级链（逐级尝试，命中即停）：

**方法 ① 个人信息接口**（首选，直接从登录身份获取）⭐ 实测 2026-08-03：
```
CallAPI(apiId: "recruit.huoshui-server.get_personal_api_web_personal_infoDetail", params: {})
// 返回当前登录用户完整信息，直接取 data.staffId
// 额外可得：fullName、departmentId（可复用作 subDepartment）、bgId、positionName 等
```
> ✅ **推荐**：无依赖、不需待办、不需简历，直接从认证 token 解析当前用户。一次调用同时拿到 staffId + departmentId + bgId，可与 Phase 2.4 org_lookup 交叉验证。

**方法 ② 待办列表**（方法 ① 失败时）：
```
CallAPI(apiId: "recruit.campus-center-front.get_campus_interview_todo_list", params: { pageIndex: 1, pageSize: 20 })
// 取 personList[].staffId（同一登录用户的待办 staffId 一致）
```

**方法 ③ 请用户提供**（最终兜底）：
> 明确告知："无法自动获取您的工号。请直接告诉我您的工号数字。"

- 用户明确"指派给 XX"时，`staffId` 可改为其他面试官工号
- 🔴 **禁止**：留 null/0 提交（后端报"面试官信息不存在"）；编造工号

> 📝 **实测结论**：方法 ① `get_personal_api_web_personal_infoDetail` 一次调用即返回 `staffId` + `departmentId` + `bgId`，无需待办或简历。此前"误用待办列表（可能为空）→ 从简历 flows 刨 staffId"的方案已废弃，改为方法 ① 优先。
> ⚠️ 待办列表为空时取不到 staffId，因此方法 ② 只作回退，不可作首选。

#### 2.6 组装完整参数

将提取结果与用户补充信息合并成完整参数对象。未提取到且无默认值的必填字段，此阶段一次性列出询问用户。

#### 校招表单字段映射（API 参数）

> 🔴 **跨接口警示：`recruitType` 在搜索接口与发起接口语义相反，禁止直接透传！**
> - 搜索 `post_v1_resume_search` 返回：`recruitType` **1=实习生，2=校园招聘(正式)，3=社会招聘**
> - 发起 `start_campus_interview` 入参：`recruitType` **1=应届毕业生，2=实习生**
> 两者 1/2 含义颠倒。`recruitType` 一律**从用户自然语言意图判定**（"实习"→2；"应届/校招"→1）或按 2.2 项目白名单反推，**绝不可**把搜索返回的 recruitType 原样填进发起入参。

| API 参数 | 类型 | 必填 | 说明 |
|-----------|------|:----:|------|
| `staffId` | integer | ✅ | 必须显式传当前用户工号，不能留 null；获取见 Phase 2.5 |
| `recruitType` | integer | ✅ | 发起接口语义：1=应届毕业生，2=实习生 |
| `recruitProject` | integer | ✅ | 从下拉反查 ID（2.2）|
| `recruitYear` | integer | ✅ | 如 2026、2027 |
| `recruitCity` | integer | ✅ | 线路 ID；未提供默认 48（远程面试）|
| `subDepartment` | integer | ✅ | 下级组织 ID（2.4 反查）|
| `position` | integer | ✅ | 职位 ID，**必须从 `position_lookup` 反查**，禁止从简历 `station` 直接映射（否则报"职位无效或已禁用"）。特例：`recruitProject=12`（项目实习）后端跳过职位校验 |
| `stepId` | integer | ✅ | 1=集体面试，2=初试 |
| `resumeIds` | integer[] | ✅ | 目标候选人简历 ID 数组 |
| `positionOuterTitle` | string | ✅ | 职位对外显示名称 |

**完整调用示例**（ID 均为占位，实际值一律来自反查）：

```
CallAPI(apiId: "recruit.campus-interview-service.start_campus_interview", params: {
  resumeIds: [<简历ID>],             // 搜索结果 data.list[].id（整数，非 rid）
  recruitType: 2,                    // 从用户意图判定：含"实习"→2，含"应届/校招"→1
  recruitYear: <年份>,               // 🔴 get_interview_recruit_year 反查所得，禁用毕业年
  recruitProject: <项目ID>,          // 2.2 白名单 + title 反查得到
  recruitCity: 48,                   // 未指定线路默认远程面试
  stepId: 2,                         // 1=集体面试 / 2=初试（仅此两个可发起）
  subDepartment: <组织ID>,           // 2.4 org_lookup 反查
  position: <职位ID>,                // 2.7 position_lookup 反查，禁从 station 映射
  positionOuterTitle: "<职位对外名>",
  staffId: <当前用户工号>            // 必须显式传，禁 null/0（见 2.5）
})
```

#### 2.7 反查：职位名 → 内部通道职位 ID（position_lookup）

```
CallAPI(apiId: "recruit.recruit-standard-resource.post_api_mcp_position_lookup", params: { postNameCn: "视觉设计" })
// data.postId 作 position；data.postFullNameCn 回显确认；data.matchCount 判多命中
```

判定：唯一命中→取 `postId`；多命中→展示 `postFullNameCn` 列表让用户确认；零命中→请用户提供更准确职位名。
> ⚠️ **多匹配只返首个（实测 2026-08-03）**：`matchCount > 1` 时 API 只返回 `postId`（升序第一个），**不返回全部匹配列表**。因此"展示列表让用户确认"实际无法执行。当前处理：直接取返回的 `postId` + `postFullNameCn` 回显，并在 R2 确认卡中标注"职位有 N 个匹配，已取首个，如需更换请提供更精确名称"。
> 🚫 **禁止使用门户职位树** `positionJoinQueryTree`/`getPositionByParentIds` 的 id——它们是门户投递岗位分类树，与发起接口所需的内部通道职位主键是两套体系，硬套必被后端拦（实测 position=140→"职位无效或已禁用"）。

---

### 批量发起模式（Batch Mode）⚡

一条指令含多个候选人、且发起参数完全相同（仅 `resumeIds` 不同）时启用批量：**一次写调用为每人各创建一条参数相同的独立面试流程**（每人独立 `interview_id`，非集体面试）。

关键：`start_campus_interview` 的 `resumeIds` 原生支持 `integer[]`；`get_resume_control_info` 也支持数组一次校验全部。

批量协议：
1. 候选收集（扩展 2.3）：多姓名并行搜索，逐人收集 `{name, resumeId, rid}`
2. 逐人权限/存在性预筛（0 结果回退规则）+ 一次批量控制校验（全部有效 `resumeIds` 一次 `get_resume_control_info`，`false` 移出并记 `hintList`）
3. 逐人 2.3.5 预判断（已在流程者按提示分支处理）
4. R2 批量二次确认（Phase 2.5）：回显批次卡片（顶部共享参数 + 候选列表 + 移出批次名单及原因）
5. 一次批量写：`resumeIds` 传全部有效 ID 数组
6. 逐人结果核验（Phase 4）：写后对每人并行 `getResumeByRId`（≤5/批）核对新增同参 `status=0` 记录 → 逐人结果表
7. 单批次建议 ≤20 人；超过按 20/片拆多次写（每片独立确认/核验）

> ⚠️ **批量 ≠ 集体面试**：批量指"参数相同、每人各创建独立流程"。候选人需不同岗位/线路/环节时不是批量，应拆成多次单发起。

---

### Phase 2.5 — R2 二次确认（受控写契约 · 强制节点）⚠️

**在调用 `start_campus_interview` 之前，必须完成受控写握手。本动作使用 `capability-registry.yaml` 中的 `campus_interview_start` 受控写定义。**

1. **冻结 payload**：按注册表 `payload_fields` 生成最终请求体（缺省字段用明确的 `null`/`false`/空数组表达），写入临时文件。
2. **展示业务卡片并确认**（确认有效期 10 分钟）：

   > 📋 **即将发起面试，请确认以下信息：**
   > - 候选人：{姓名}（简历ID: {resumeId}）
   > - 招聘类型：{类型名}（{recruitType}）
   > - 招聘项目：{项目名}（{recruitProject}）
   > - 招聘年份：{recruitYear}（该类型可选：{年份集合}）
   > - 招聘线路：{线路名}（{recruitCity}，未指定线路时默认远程面试 48）
   > - 面试组织：{组织全路径}（{subDepartment}）
   > - 职位：{职位对外名}（{position}）{多匹配时附"该职位名有 N 个匹配，已取首个，如需更换请提供更精确名称"}
   > - 面试环节：{环节名}（{stepId}）
   > - 面试官：{当前用户或指派人}（staffId {staffId}）
   >
   > ⚠️ 确认无误后将正式创建面试流程，此操作不可撤销。是否继续？

   > 📦 **批量模式变体**：回显批次卡片——顶部【共享面试参数】+【候选列表】（#/姓名/简历ID/状态）+【移出批次】（含原因），确认后一次调用为 N 人创建流程。

   展示的是业务可读信息，**不展示**手机号、邮箱、Token、Cookie、完整内部 payload。
   🔴 **年份必须带上"该类型可选集合"**（见 2.2.2）；候选人毕业年与招聘年不同时补一句说明，否则用户会以为填错。

3. **用户明确确认后**，一条命令完成「算摘要 + 生成信封 + preflight 校验」：

   ```bash
   python3 scripts/build_write_envelope.py prepare \
       --action-key campus_interview_start \
       --payload "$TMP_DIR/payload.json" \
       --target-ids <逗号分隔的 resumeId 列表> \
       --summary "校招发起面试：{N} 名候选人 / {项目} / {年份} / {线路} / {组织} / {环节}" \
       --out "$TMP_DIR/envelope.json"
   ```

   脚本自动从注册表带出 skill / risk_level / target_type / backend_deduplication / TTL，
   校验 payload 字段白名单、目标数上限、敏感信息，并输出 `payload_digest`。
   **只输出摘要，不回显 payload**；临时文件用完即删（脚本已设 0600 权限）。
   ⚠️ `--summary` 禁含手机号/邮箱/证件号，命中敏感扫描会直接校验失败。

   > 若脚本不可用（环境异常），回退手工路径：`python3 ../../scripts/validate_write_action.py --digest < payload.json` 算摘要 → 按 `schemas/write-action-envelope.schema.json` 手工拼信封 → `validate_write_action.py --envelope <file> --phase preflight`。

4. payload 任一字段变化、确认过期或目标变化 → 旧确认立即失效，必须**重新冻结、重新确认、重新 prepare**（摘要会随之改变）。
5. 用户提出修改 → 回 Phase 2 修正后**重新执行本节点**；用户取消 → 终止。

> 🚫 **绝对禁止**：未经 R2 确认、或用户未明确说"确认"就调用写接口。

---

### Phase 3 — 提交发起（Submit）

R2 确认通过后：调用前将信封状态置为 `submitted`，再调 `start_campus_interview`。

> 📦 批量：`resumeIds` 传全部有效 ID 数组，其余参数共用；>20 人按 20/片拆多次调用。

> ⚠️ **写接口软错处理协议（防误判/防重复发起，硬性规则）**
> 返回软错（`当前有面试官正在操作`、`此简历状态目前不可发起面试`）时，**绝对禁止立即重试**——这类软错常见"响应报错、写入却已成功"的并发竞态。必须先调 `getResumeByRId` 查 `interviewRecords`：
> - 已有同参面试（year/type/project/city/position/department 一致）且 `status=0` → **视为已成功**，不重试，直接走 Phase 4 成功输出
> - 无同参面试 → 再按错误类型处理（确为并发锁可隔数秒重试**一次**）
> 📦 批量软错整批返回时**不整批重发**——逐人 `getResumeByRId` 核验，仅对未落库子集隔数秒重试一次。

### Phase 3.5 — 全链路提示/报错展示（Mandatory）⚠️

从 Phase 0 → Phase 4 任何步骤返回的 hint/warning/error **必须原样、显式展示给用户**，不得吞掉或静默跳过：

- ❌ 禁止仅返回"操作失败"而不展示接口 `errorMsg` 原文
- ❌ 禁止 Phase 0 校验不通过仍继续后续流程
- ✅ 任何非 200 / `status != 0` / `actionEnable=false` 都必须中断并展示原因；提示类（非阻塞）信息也附带展示

### Phase 4 — 成功处理 + 审计（Success Handling）

**判断成功**：外层 `status === 200` 且 `data.success === true` 且 **`data.errorMsg` 为空数组**。

> ⚠️ **成功时 `successMsg` 也可能为空数组（"三空"成功，硬性核实规则）**：实测存在 `success=true`、`total=1`、`errorMsg=[]` 且 `successMsg=[]` 的响应。此时**禁止**因 successMsg 空而误判失败，也**不得**仅凭 success=true 就报成功——**必须**紧接着调 `getResumeByRId` 查 `interviewRecords`，确认新增了同参 `status=0` 记录并取得 `interview_id`，方可判定成功。
> 判定优先级：`errorMsg` 非空→失败（按错误表）；`errorMsg` 空 + 查到新增 `status=0` 记录→成功；`errorMsg` 空但复查无新增→疑似未落库，按软错协议处理，勿盲目重试。

**审计**：`start_campus_interview` 成功且核验到新增 `interview_id` → 审计状态 `success`，`audit.ref` 使用 `interview_id`；明确业务失败 → `failed` + 真实错误码；超时/空响应/泛化错误 → `unknown`，**禁止自动重试**。结果确定后执行：
```bash
# 成功
python3 scripts/build_write_envelope.py outcome \
    --envelope "$TMP_DIR/envelope.json" --status success --ref <interview_id>

# 失败（必须带真实错误码/errorMsg 原文）
python3 scripts/build_write_envelope.py outcome \
    --envelope "$TMP_DIR/envelope.json" --status failed --error-code "<errorMsg 原文>"

# 结果不明（超时/空响应）——禁止自动重试
python3 scripts/build_write_envelope.py outcome \
    --envelope "$TMP_DIR/envelope.json" --status unknown
```
> 回退手工路径：`python3 ../../scripts/validate_write_action.py --envelope <envelope.json> --phase outcome`（需先手工改 `audit` 字段）。
> ✅ 审计完成后删除 `$TMP_DIR` 下的 payload / envelope 临时文件。

**成功后标准输出语**：

> ✅ **已成功对该简历发起面试，请及时安排面试。**
>
> 📋 **去处理** → [查看面试待办详情]({从待办列表取到的 pcUrl；校招格式 https://zhaopin.woa.com/zhaopin/campus/NewInterviewDetail?traceId={flowTraceId}})

> 📦 **批量逐人结果表**（写后逐人 `getResumeByRId` 核验生成）：
>
> | 姓名 | 简历ID | 结果 | 面试ID / 说明 |
> |------|--------|------|---------------|
> | 杨大大 | 1931005 | ✅ 成功 | 391335 |
> | 史害毛 | 1932885 | ✅ 成功 | 391336 |
> | 贾牛命 | 1932888 | ❌ 失败 | 手机号不能为空（主库缺失，需网页端补存）|
>
> 成功项给 `interview_id`（+"去处理"链接）；失败项给具体原因 + 简历详情链接 + 建议。整体以"成功 N / 失败 M"呈现，不因个别失败否定整批。

**链接拼接规则**：
- `start_campus_interview` **不直接返回 traceId**。成功详情链接：
  - 优先用 `getResumeByRId` 即时确认（写后本就要调它核实），直接向用户报告"已创建 interview_id=xxx"
  - 链接（pcUrl/flowTraceId）用 `get_campus_interview_todo_list` 取（慢，仅此 1 次），按 rid/姓名匹配新记录取 `pcUrl`；该次超时**不推翻成功结论**，先报 interview_id、链接重试一次，仍失败则附简历详情链接 + interview_id，请用户到面试待办打开

**成功后：衔接面试安排（fresh handoff）**：
- 发起成功后**重新拉取生产待办**取最新 `flowTraceId`，再进入 `flows/S.md` 按 S-Pre → S-0 → S-A 安排本轮面试
- **禁止**直接复用发起返回/旧数据冒充待办 traceId；若状态或待办尚未同步，停止自动下单并提示稍后重试

---

## 五、错误处理速查

| 错误现象 | 可能原因 | 处理方式（均须原样透传原文）|
|----------|---------|------------------------------|
| `actionEnable=false` | 简历在限制名单（冷冻期/黑名单等）| 展示 hintList 原因，建议联系 HR |
| `finishFlag != true` | 面试官课程未完成 | 引导前往 learnUrl（页面级提示）|
| `status != 0` 且 `errorMsg` 非空 | 发起失败（岗位停招/已在流程等）| 展示 errorMsg 具体错误 |
| 401 | Token 过期/未认证 | 引导重新连接 MCP |
| 403 | 权限不足（非招聘经理/面试官）| 引导确认身份角色 |
| 必填字段缺失 | 用户未提供完整信息 | 逐项询问，不得猜测填充 |
| 同名歧义 | 姓名匹配多人 | 展示候选清单，请用 rid/手机号/链接确认；邮箱不支持 |
| 反查无结果（项目/候选人）| 关键词错误或无权查看 | 展示"未找到"，请用户提供更准确名称或 RID |
| 类型与项目不匹配（实习生+青云计划 等）| 类型与项目分属不同类型（见 2.2 白名单）| 显式提示"类型-项目不匹配"，列白名单，请用户改类型/改项目二选一；**禁止静默剔除或自动代换**。后端不校验此项，skill 是唯一防线 |
| `startInterviewEnable=1` 搜 0 条、去过滤仍 0 | 简历不在校招池（可能活水/社招）| 提示确认候选人类型；社招改走 SI 社招发起 |
| 简历存在但 `startInterviewEnable=1` 搜 0 条（去过滤能搜到）| **用户对该简历无发起权限** | 明确告知"⚠️ 无该简历发起权限"，展示 RID/链接并**终止**，勿依赖 Phase 0.1 兜底 |
| 调用超时/无响应 | 慢接口（todo_list/org_lookup）或瞬时抖动 | 超时**重试同接口一次**（隔 2-3s），勿连环重发 |
| `面试官信息不存在` | `staffId` 为 null/未显式传 | 必须显式传当前用户工号（从待办 `staffId` 取）|
| `职位无效或已禁用` | `position` 非法（从简历 station 映射，或误用门户职位树 id）| 用 `position_lookup` 反查内部通道职位 ID；禁用 positionJoinQueryTree 的 id |
| `当前有面试官正在操作，请稍后再试` | 并发竞态（可能已落库）| ⚠️ 切勿盲目重试；先 `getResumeByRId` 查，已有同参 `status=0` 即已成功 |
| `此简历状态目前不可发起面试` | 已有进行中同参面试 | 通常是"上次发起已成功"信号；`getResumeByRId` 核实即可 |
| `手机号不能为空` | 主库 mobile 为空（搜索索引/网页另有脱敏来源）| 接口无手机号入参，需网页端重存 mobile 到主库，或报平台修数据 |
| 批量部分成功 | 个别候选人数据/状态问题 | 逐人 `getResumeByRId` 核验生成结果表，不因个别失败否定整批 |
| 已在面试流程中（2.3.5 命中）| 已有进行中面试 | 预判断即提示：现有面试环节/状态 + 去处理链接，请用户"仍要发起/跳过" |
| `recruitYear` 不在可选集合 / 疑似填了毕业年 | 把候选人毕业年份当成招聘年份 | 调 `get_interview_recruit_year` 取该类型可选集合，按 2.2.2 规则取值；不在集合内时中断请用户二选一，**禁止静默代换** |
| 信封 schema 校验报错（`action_key is not registered` / 格式不符）| 手工拼信封字段缺失或格式错 | 改用 `scripts/build_write_envelope.py prepare` 自动生成，勿手搓 |
| `confirmation.summary: phone-like value is not allowed` | 确认摘要里写了手机号等敏感信息 | summary 只写业务可读信息（人数/项目/年份/线路/组织/环节），去掉联系方式 |
| `payload 含未登记字段` | payload 键拼写错误（如 `recruitTyp`）| 按 `capability-registry.yaml` 的 `payload_fields` 校正字段名 |

### 5.1 后端责任链 Validator 拦截话术对照

后端 `start` 接口在批量公共校验后，对每简历按 Order 跑 Validator，任一失败仅拦截该简历。返回以下 `errorMsg` 时按此表向用户解释，不要笼统报"发起失败"：

| Validator | 触发 `errorMsg` | 含义 & 建议 |
|----|----|----|
| StartResumeCheckValidator | `简历信息参数缺失`/`手机号参数缺失` | 主库简历/手机号为空，须网页端补存主库字段 |
| StartResumeCheckValidator | `当前简历状态不允许发起面试` | 状态不在白名单；常是"已有进行中面试"，先 `getResumeByRId` 核实 |
| StartResumeCheckValidator | `简历锁定在他人名下`/`锁定在 COE 简历库`/`锁定在项目中` | 简历被锁定；需对应解锁/强制发起权限，否则换有权限账号或联系 HR |
| StartBlacklistValidator | 命中限制性名单 | 作弊名单不可强制发起；其他名单需 `INTERVIEW_FLOW_BLACKLIST` 权限，建议联系 HR 核实 |
| StartQualityAssessmentValidator | 综合测评未完成 | 测评须完成态（红3/黄4/绿5）；青云岗位/海外学生/有跳过权限者可豁免 |
| StartInternAssessValidator | `该生有待考核记录，仅可发起面试`/`暂不允许发起面试` | 实习生考核状态限制，核实候选人考核/在职状态 |
| StartSocialRecruitLockValidator | `候选人已被社招锁定` | 姓名+手机号命中社招锁定；确认是否在社招通道或联系社招方解锁 |
| StartPendingFlowValidator | `存在未完成的待办流程，请先处理` | 有进行中 offer/面试待办；先处理或撤销原流程再发起 |
| StartLeaveRefluxValidator | 离职回流限制提示 | 受离职回流时间/次数限制，按提示等待或联系 HR |

> 📌 **职位校验特例**：`recruitProject=12`（项目实习）后端跳过职位校验。故"职位无效"仅对非项目实习普通组织生效。

---

## 六、生产边界与已验证规则

1. **控制校验必要非充分**：`get_resume_control_info` 的 `actionEnable=true` 不保证发起必成功；手机号/简历状态/测评在写接口才校验。
2. **类型-项目白名单是 skill 唯一防线**：后端责任链不校验类型-项目匹配，错配会真落库；进入 R2 前必须严格执行 2.2 白名单校验。
3. **recruitType 跨接口语义相反**：搜索 1=实习/2=校招，发起 1=应届/2=实习，禁止直接透传，一律从用户意图或项目白名单判定。
4. **recruitYear 是招募周期年、不是毕业年**：必须调 `get_interview_recruit_year` 按类型反查可选集合，禁止从 `graduate_time` 推导（见 2.2.2）。
5. **position 必须走 position_lookup**：禁止从简历 station 或门户职位树 id 映射。
6. **发起环节仅 1/2**：集体面试(1)/初试(2)；复试及以后不能作为发起 stepId，skill 层拦截。
7. **staffId 必填显式传**：留 null 报"面试官信息不存在"。
8. **线路默认 48**：未提供线路默认远程面试(48)，不追问。
9. **未知结果禁止重试**：超时/空响应/泛化错误先回读 `getResumeByRId`/待办并标记 `unknown`，任何重试都需新的确认记录。
10. **三空成功需核实**：`success=true`+`errorMsg=[]`+`successMsg=[]` 时必须 `getResumeByRId` 核实新增 `status=0` 记录才判成功。
11. **安排必须 fresh handoff**：发起成功后重新拉取生产待办取最新 flowTraceId 进入 S-A，不复用旧 ID。
12. **信封用脚本生成**：R2 信封走 `scripts/build_write_envelope.py`，禁止手搓 12 字段（手搓极易触发 schema 校验错并浪费往返）。

---

## 七、发起前自检清单（Phase 2.5 前逐条过一遍）✅

进入 R2 确认卡之前，把下面 8 条在心里过一遍；任一条为"否"就先补齐，不要带着不确定进写接口。

| # | 自检项 | 依据 |
|:-:|---|---|
| 1 | `recruitType` 是从**用户意图/项目白名单**判定的，不是从搜索结果透传的？ | 2.6 跨接口警示 |
| 2 | `recruitProject` 在该 `recruitType` 的白名单内？ | 2.2 白名单 |
| 3 | `recruitYear` 来自 `get_interview_recruit_year` 可选集合，**不是**毕业年份？ | 2.2.2 🔴 |
| 4 | `position` 来自 `position_lookup` 反查？多匹配已在卡片标注？ | 2.7 |
| 5 | `subDepartment` 来自 `org_lookup` 唯一命中并已拿到全路径回显？ | 2.4 |
| 6 | `stepId` ∈ {1, 2}？（复试及以后不可作发起环节） | 0.3 |
| 7 | `staffId` 已显式赋值（非 null/0）？ | 2.5 |
| 8 | 已做 2.3.5 在途流程预判断（`interviewRecords` 无 `status=0`，或用户已明确"仍要发起"）？ | 2.3.5 |

> 🔴 第 3 条是最高发漏项——它不会在前置校验里报错，只会在写接口被拦或静默落成错误周期。

> 详细接口入参/返回/校验规则见 `../references/interview-lifecycle/campus-initiation-api.md`。
