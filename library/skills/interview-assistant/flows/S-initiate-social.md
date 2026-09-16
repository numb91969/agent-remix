# 面试助手 · SI 社招发起面试子模块

> 子模块路径：`flows/S-initiate-social.md`
> 触发：主 `SKILL.md` 的 Router-0 命中「发起社招面试 / 推进到面试环节」后，必须先读取本文件。
> 定位：创建社招招聘面试流程；成功并回读最新状态后，再交给 `flows/S.md` 安排本轮面试。

在招聘系统（zhaopin.woa.com）中，对**社招简历库**中的候选人简历一键发起面试流程。覆盖从简历搜索、可发起校验，到发起流程页面的五步交互（候选人信息确认 / 离职回流 / 部门岗位 / 面试流程 / 保密流程），最终锁定简历并可跳转面试安排的完整链路。

> ⚠️ 本子流程只处理**社招**。校招/实习发起面试走 `flows/S-initiate-campus.md`（SC）；社招与校招数据、状态和接口必须隔离，禁止跨域调用。

---

## 一、触发词与使用时机

当用户表达以下意图时触发本 Skill：

- 「对 XXX（候选人）的简历发起面试」「给这份社招简历发起面试」
- 「帮某候选人发起社招面试」「发起社招面试流程」
- 用户提供社招候选人姓名 / 手机号 / 简历 RID / 简历详情链接并要求进入面试环节

**前置条件**：
- 已连接招聘 MCP 连接器（连接器路由见「二、环境与连接器」）
- 当前用户对该简历拥有发起面试权限（招聘经理 / 有 ATS 权限的角色）

---

## 二、生产连接器与调用规范（每次会话首次调用前确认一次）⚠️

社招简历搜索、详情、岗位流程预拉取、回流校验、`start_interview` 发起流程及后续面试安排，统一使用专家包注册的生产连接器 **`recruit-mcp`**。整条链路必须保持在同一生产连接器中，禁止混用测试连接器或复用其他环境返回的 RID、FlowMainId、TraceId、InterviewId。

调用前必须：

1. 通过 `SearchAPI(query=..., domain="recruit")` 探测目标能力，再用 `SearchAPI(apiId=...)` 获取当前生产 schema。
2. `CallAPI` 只接受 SearchAPI 返回的原始完整三段式 apiId，禁止自行拼造、禁止通过额外无业务字段绕过网关校验。
3. 若生产 SearchAPI 未返回 `recruit.interview-flow.start_interview`，停止自动写入并降级到简历详情页，不得切换到测试连接器。
4. 所有读写均使用同一连接器；发起成功后必须在同一连接器回读状态，再进入面试安排。

> 📌 详细接口参考：`../references/interview-lifecycle/social-initiation-api.md`。

---

## 三、完整工作流（Workflow）

严格按阶段顺序执行。**Phase 1.5 可发起校验**、**Phase 6 发起前二次确认**、**全链路报错透传（贯穿始终）** 为硬性节点，不可跳过。

> 🔴 **全链路报错透传总则（贯穿 Phase 1.5→7，必须遵守）**
> 从简历搜索、可发起校验、离职回流校验、发起提交，到锁定后安排面试——**任何一步返回的提示 / 警告 / 报错（`msg` / `errorMsg` / 业务码等），都必须原样、显式地返回给用户，不得吞掉或改写为泛化的"操作失败"**。这是用户对本 Skill 的核心要求。

### Phase 1 — 搜索社招简历（定位 RID）

用户给出候选人后，调用社招简历搜索定位简历：

```
CallAPI(apiId: "recruit.social-resume.post_api_resume_query_query", params: {
  name: "张三",                              // 姓名精确匹配；mobile / email 精确匹配（含历史号码/邮箱）
  diggerSearchId: "mcp-recruit-{随机uuid}",  // 每次搜索必传，分页时保持不变
  from: 0, size: 20                          // ⚠️ 分页约束：from≥0 且 from+size<10000；size≤200
})
// 从 data.resumes[] 取目标：Rid（GUID，发起面试用的 CandidateId）、Name、Status、StatusText、atsRights、IsSecret
```

- **⚠️ 搜索接口的分页约束**：`from+size < 10000` 且 `size ≤ 200`；翻页时 `diggerSearchId` 保持不变。
  - 🧪 **2026-07-22 反向测试实测**：越界并**不报错，而是被后端静默钳制**——`from=9990,size=300`（同时越两界）时，ES query 里 `from` 被重置为 `0`、`size` 被钳到上限 `200`，正常返回首页 200 条内结果。→ **不能靠"后端报错"来发现分页越界**；若结果与预期页码不符，应自查是否越界并主动收窄 `size≤200`、控制 `from+size<10000`，勿误以为后端会拦。
- 简历详情链接拼接：`https://zhaopin.woa.com/resume/resume_detail?rid={Rid}&fromplace=MCP`
- **同名多份**：`data.resumes` 命中多人时，展示候选清单（姓名 / 当前公司 / 学历 / 简历链接 / 手机尾号），请用户用「RID / 手机号 / 简历链接」任一方式确认，**禁止默认取第一条**。
- **搜不到**：先仅用 `name` 再搜一次确认；仍 0 条则告知"未在社招简历库找到该候选人"，请用户确认是否走校招 / 活水通道或提供 RID。
- **⚠️ 完善度字段来源差异（勿混用）**：搜索接口返回的是 `WorkExperienceList[]` / `EducationList[]`（可在搜索阶段粗判完善度）；详情接口（Phase 2）返回的是 `resumeWorkExp[]` / `resumeEdu[]`。两套字段**名字不同、来源不同**，判断完善度时务必按当前调用的接口取对应字段，不要跨接口套用字段名。

### Phase 1.5 — 可发起校验（是否允许发起面试）⚠️ 硬性

社招**没有**校招那样独立的 `get_resume_control_info` 控制校验接口。可发起性依据搜索 / 详情返回字段综合判断，**任一不满足即中断并返回具体原因**：

| 判断项 | 依据字段 | 不可发起时返回给用户的原因 |
|--------|----------|------------------------------|
| 无操作权限 | 搜索结果 `atsRights` 非空 | "您对该简历无操作权限，需联系有权限的同事：{atsRights[].fullName/engName 列表}" |
| 简历已锁定 / 已在流程 | `Status != 1`（1=待筛选=未锁定；其他状态均视为已锁定/在流程） | "该简历当前状态为「{StatusText}」，已被锁定或在面试流程中，不可重复发起" |
| 简历已删除 | `Enable=0` / `enableFlag=0` | "该简历已删除，无法发起面试" |
| **本 RID 存在在途流程** | 详情 `data.flowList[]` 中存在未终态流程（需结合 `stateId/stateName` 判断） | "该简历已存在面试流程：{postName}（状态：{stateName}），请勿重复发起" |

> 💡 **flowList 判定口径**：`flowList[]` 非空不等于不可发起。历史“面试放弃/淘汰/已结束”等终态流程不阻断重新发起；只有未终态、仍在途的流程才阻断。简历当前 `Status/status` 仍是主要判断依据。
> ⚠️ 这只能覆盖本 RID 的流程；同手机号另一份简历已在流程仍可能只能由服务端最终校验发现，需原样返回业务错误。

> ⚠️ 以上为**必要非充分**校验：即使通过，最终能否发起仍以 Phase 6 `start_interview` 实际响应为准（岗位停招、简历已在流程、面试官非法、缺薪资谈判环节等只有写接口才会报）。写接口报错时同样按报错透传总则原样返回。

校验通过 → 进入发起流程（Phase 2~7）。校验不通过 → 输出原因 + 简历详情链接，终止。

### Phase 2 — 第①步：确认候选人信息（简历完善度校验）

调用社招简历详情，展示候选人核心信息并校验简历完善度：

```
CallAPI(apiId: "recruit.social-resume.get_api_resume_detail_getresume_with_detail", params: {
  rid: "{Rid}", fromPlace: "MCP"
})
// data.resume：基本信息 + resumeWorkExp[]（工作经历）+ resumeEdu[]（教育经历）
// data.flowList[]：该简历已有的面试流程记录（可用于判断是否已在流程）
```

**简历完善度判断（对应发起面试页面的前端提示）**：
- 若 `data.resume.resumeWorkExp` 为空 / 缺失 **或** `data.resume.resumeEdu` 为空 / 缺失，**必须原样返回下列提示语给用户**（这是 MCP 无专门接口、需由本 Skill 依据详情数据拼装的前端文案）：

  > ⚠️ 该人选工作经历、教育经验未完善，为保障面试官和人选的面试体验，建议完善简历信息后再发起面试流程。

  同时**必须提供简历详情页跳转链接**：`https://zhaopin.woa.com/resume/resume_detail?rid={Rid}&fromplace=MCP`
- 提示后询问用户是"先去完善简历"还是"仍继续发起"，由用户决定（不强制阻断，仅提示）。

> 📌 展示候选人信息卡片：姓名 / 手机（脱敏）/ 邮箱 / 当前公司职位（extendLastWorkExp）/ 最高学历（extendLastResumeEdu）/ 工作年限（extendWorkYearValue）/ 简历状态。

### Phase 3 — 第②步：确认是否离职回流（Reborn）

询问用户"该候选人是否为离职回流（前腾讯员工）"：

- **用户选"否"** → `IsReborn=false`，跳过校验，进入 Phase 4。
- **用户选"是"** → `IsReborn=true`，此时：
  1. **必须校验用户是否同时提供了「之前的帐号 / 曾用英文名」**（`RebornEngName`）。未提供 → 提示"离职回流必须提供候选人之前的腾讯帐号/曾用英文名"，请用户补充后再继续。
  2. 提供了 → 进入离职回流校验：

  ```
  CallAPI(apiId: "recruit.interview-flow.reborn_validate", params: {
    dimissionName: "{曾用英文名}",   // 离职员工英文名
    rid: "{Rid}",
    flowMainId: 0                     // ⚠️ 时序说明见下方注意事项
  })
  // data.staffId：员工ID（0=查无此人，须先看此字段）
  // data.code：0=查无此人(配合 staffId=0) / 200=通过 / 3000006=需人工校验 / 3000007=找到但非集团离职回流(staffId≠0)
  // data.msg、data.suggestion（重新录用建议 / 离职面谈记录）；查无此人与非回流两分支 msg 均为空
  ```

  - `data.code=200` → 校验通过，展示 `msg`（符合要求）+ `suggestion`，继续。
  - `data.code=3000006` → **校验不通过，原样返回 `msg`**："需人工校验，请部门招聘经理发邮件至 IVC-service@tencent.com 申请查询"，由用户决定后续。
  - `data.code=3000007` → 非集团离职（找到了员工但非集团正式离职）；请用户确认曾用英文名是否正确。
  - `data.code=0` 且 `data.staffId=0` → **未找到该英文名对应的员工**（曾用英文名拼写错误/查无此人）；提示用户核对曾用英文名。
  - 接口本身报错（网络 / 权限）→ 按报错透传总则原样返回原因。

  > 🔬 **生产口径验证（2026-07-22）——两条 code 的真实分界（修正旧文档）**：
  > - 传**查无此人**的英文名（如 `nonexistentxyz999`）→ 返回 `staffId=0, code=0, msg=""`（**不是** 3000007）。即"查无此人"走 `code=0 + staffId=0`。
  > - 传**在职、从未离职**的真实员工（如 `rodickwu`，staffId=56251）→ 返回 `staffId=56251, code=3000007, msg=""`。即 3000007 表示"找到了这个人、但不是集团正式离职回流"，**此时 staffId 非 0**。
  > - 故判断口径应为：**先看 `staffId` 是否为 0**（0=查无此人，提示核对英文名）；**staffId≠0 再看 code**（3000007=非离职回流、3000006=需人工校验、200=通过）。切勿把 `staffId=0` 等同于 `code=3000007`——实测二者不同源。两个异常分支 `msg` 均为空，需由 Skill 自行拼装提示文案。

  **回流可选字段的续填（校验通过或用户坚持继续时）**：当 `code=200`，或 `code=3000006` 后用户明确坚持继续发起时，可把以下回流附加字段随 `start_interview` 一并提交（有则填、无则省略）：
  - `RebornSuggestion`（重新录用建议，可取 `data.suggestion`）、`RebornMemo` / `RebornMemoId`（离职面谈记录/ID）、`RebornRemark`（备注）、`DimissionReason`（离职原因）、`IsReBornContinue`（在需人工校验等情形下"坚持继续"的标记）。
  - 这些字段**由用户提供或从 reborn_validate 返回带出**，Skill 不臆造；缺失则省略，由后端决定是否拦截并透传报错。

> ⚠️ **时序边界（重要）**：`reborn_validate` 需要 `flowMainId`，但正常发起流程此时**流程尚未创建、还没有 flowMainId**。实测可先传 `flowMainId=0` 做前置回流校验；若接口因缺流程返回异常，则将回流信息（`IsReborn/RebornEngName/RebornMemo`）随 `start_interview` 一并提交、由发起接口内部完成回流校验，并把发起返回中的回流相关报错原样透传给用户。

### Phase 4 — 第③步：用户提供并确认面试岗位（系统不自动带出岗位）⚠️

**关键修正（来自真实产品行为）**：系统**不会自动带出**面试岗位。进入发起流程后，必须**主动向用户索取岗位信息**，用户须提供 **岗位名称 或 岗位 ID（二选一）**：

- **用户提供岗位 ID（RecruitPostId）** → 直接使用；部门（RecruitDeptId/RecruitDeptName）随之确定。
- **用户提供岗位名称** → 调用 `recruit.social-resume.get_api_post_GetPostByPostName` 模糊反查，拿回 `RecruitPostId` + 所属 `RecruitDeptId/RecruitDeptName`；同名多岗位时请用户用岗位 ID 确认。
- **用户未提供任何岗位线索** → **必须显式询问**、不得默认/臆造岗位。可提示用户提供岗位名或岗位 ID。

> 🔑 **岗位反查会带出面试官（实测 2026-07-22，重要能力补强）**：`get_api_post_GetPostByPostName` 的返回**每个岗位都含**：
> - `recruitPostID` / `recruitPostName` / `departmentId` / `departmentName` / `isDisabled`（是否停招）/ `isSecret`（是否保密岗位）；
> - **`hrView`**（岗位的**招聘经理**：staffId/engName/fullName）——对应 `HRSalaryView` 环节处理人；
> - **`firstView`**（岗位的**部门初试官**：staffId/engName/fullName）——对应 `DeptView` 环节处理人。
> → 这意味着 Phase 5 的面试官**不必靠"错误驱动盲试"**，可直接从岗位反查的 `hrView`/`firstView` 取到**真实 staffId + engName** 组装 FlowStepGroup（`HRSalaryView.StepUser=hrView`、`DeptView.StepUser=firstView`），既拿到精确 staffId、又规避了 employee_lookup 403 缺口（#14）。**这是本次实测新确认的推荐做法，优先于错误驱动法。**
> ⚠️ 注意 `isDisabled` 参数：反查时传 `isDisabled=false` 只查在招岗位；`isDisabled=true` 查停招岗位；不传查全部。发起前应确认岗位 `isDisabled=false`（停招岗位发起会被拦，见 Phase 7 实测）。

> ⚠️ 注意：部门（RecruitDeptId）通常随岗位一起带出；若用户另指部门，以用户为准。
> ⚠️ **岗位↔部门一致性（埋雷点）**：`RecruitDeptId` 一般由岗位反查带出，且应属于该岗位。**若用户另行指定的部门与岗位反查带出的部门不一致**，先向用户明确二者冲突、请其确认以哪个为准，**不要静默用用户值覆盖岗位带出值**；不一致仍强行提交可能触发后端岗位/部门校验失败，届时按报错透传。

- **用户提供后允许调整**：用户给出新岗位名/ID 时，重新反查确认 `RecruitPostId` + `RecruitDeptId`（`RecruitPostId`、`RecruitDeptId` 均不能为 0）。
- **⚠️ 提交前硬断言**：进入 Phase 7 前必须确保 `RecruitPostId ≠ 0` 且 `RecruitDeptId ≠ 0`；若反查失败返回 0/空，**不得用 0 提交**，须回到本步请用户重新提供岗位。
- **调整后如出现报错**（岗位不存在 / 已停招 / 部门无效等，通常在 Phase 6 发起时暴露）→ **原样返回报错原因**，请用户重新提供岗位。

> ⚠️ 缺口提示：目前 MCP 无独立的"社招岗位详情校验/停招校验"只读接口，岗位是否停招等只有发起（`start_interview`）时才会校验并报错。因此岗位合法性以发起响应为准，报错须透传。

### Phase 5 — 第④步：岗位确定后展示系统自动带出的面试流程 ⚠️

**产品行为（zhaopin.woa.com 前端）**：一旦岗位（RecruitPostId）确定，系统会**自动带出该岗位已配置好的面试流程**，包括：

1. 各环节 `StepCode/StepName` 与对应面试官 `StepUser`（来自岗位流程配置）；
2. HR 薪资谈判（HRSalaryView）环节的招聘经理；
3. HR 资格面试环节的招聘经理；
4. 部门经理审批环节的处理人。

**MCP 行为（2026-07-30 更新）**：`start_interview` 是底层写接口，**不会自动从岗位模板装配 FlowStepGroup**。不传 → 报「缺少薪资谈判环节」。但通过 MCP 可以完整预拉取：
- 调 `get_recruit_post` 读取 `flowStepGroup.flowStepList[]`，获得**用户截图里看到的全部环节 + 面试官 + staffId**；
- 将 `stepUser` 中提取英文名（如 `"rodickwu(吴倚)"` → `"rodickwu"`），连同 `stepCode/stepName/stepUserID` 组装 FlowStepGroup 提交；
- 调用前必须以生产 `SearchAPI(apiId=...)` 返回的参数类型为准；如出现 `TYPE_MISMATCH`，使用 SearchAPI 返回的正确参数结构重试一次，仍失败则改用 `get_api_post_GetPostByPostName` 只读接口或降级页面。禁止添加 `_extra` 等无业务字段绕过校验。

组装到 `FlowStepGroup.FlowSteps[]`（**结构示意，实际值必须由岗位配置自动带出**）：

```json
"FlowStepGroup": { "FlowSteps": [
  { "StepCode": "DeptView",         "StepName": "第1轮部门内专业面试", "StepUserID": 56251, "StepUser": "rodickwu",   "IsSuperior": 0 },
  { "StepCode": "DeptManagerView",  "StepName": "第1轮用人决策者面试", "StepUserID": 752,   "StepUser": "wang",       "IsSuperior": 0 },
  { "StepCode": "HRView",           "StepName": "HR资格面试",         "StepUserID": 56251, "StepUser": "rodickwu",   "IsSuperior": 0 },
  { "StepCode": "HRSalaryView",     "StepName": "HR薪资谈判",         "StepUserID": 56251, "StepUser": "rodickwu",   "IsSuperior": 0 },
  { "StepCode": "GMView",           "StepName": "部门经理审批",       "StepUserID": 56251, "StepUser": "rodickwu",   "IsSuperior": 0 }
] }
```

> ⚠️ **已实测确认的合法 StepCode（2026-07-30 纠正 DeptManagerView + 新增 GMView）**：
> | StepCode | 环节名称 | 面试官来源 |
> |----------|---------|-----------|
> | `DeptView` | 部门内专业面试 | 预拉取接口 `flowStepList` 或岗位反查 `firstView` |
> | `DeptManagerView` | 用人决策者面试（部门负责人面试）| 预拉取接口 `flowStepList` |
> | `HRView` | HR资格面试 | 预拉取接口 `flowStepList` |
> | `HRSalaryView` | HR薪资谈判 | 预拉取接口 `flowStepList` 或岗位反查 `hrView` |
> | `GMView` | 部门经理审批 | 预拉取接口 `flowStepList` |
> | `CommitteeView` | 通道/面委会面试 | 预拉取接口 `flowStepList`（视岗位配置） |
>
> ⚠️ 注意：用人决策者的正确 StepCode 是 **`DeptManagerView`**（不是 `DeptManageView`）。`DeptManageView` 是早期猜测值（能偶尔通过但不准确）。
> **切勿臆造 StepCode**（如 `HRQualification`/`DeptManagerApprove`/`GMDecisionView` 等），臆造会导致后端泛化 500。
> 🔑 **`StepUser` 必须是面试官的英文登录名（engName），不是中文显示名**：写接口按英文名匹配面试官（报错形如 `{英文名}不是面试官`），中文名会匹配失败。预拉取接口返回的 `stepUser` 格式为 `"engName(中文名)"`（如 `"rodickwu(吴倚)"`），**只需提取括号前的部分作为 StepUser**。提取规则：取 `stepUser` 字符串第一个 `(` 之前的内容作为 engName，`stepUserID` 直接使用无需转换。

**操作流程**（2026-07-29 推荐做法升级）：
- **第 1 步**：先调 `recruit.recruit-post-social.get_api_web_recruitPost_get_recruit_post?recruitPostId={id}` 读 `data.postData.flowStepGroup.flowStepList[]`（接口字段说明：与前端交互使用 `flowStepGroup` 对象，保存到数据库时转 XML；同步可读 `data.postData.hr` / `data.postData.firstView`）。
- **第 2 步**：把 `flowStepList[]` 逐项映射到 `FlowStepGroup.FlowSteps[]`。映射规则：
  - `stepCode` → `StepCode`（直接使用）
  - `stepName` → `StepName`（直接使用）
  - `stepUserID` → `StepUserID`（直接使用，即为正确 staffId）
  - `stepUser` → `StepUser`：提取 `(` 前的部分，如 `"rodickwu(吴倚)"` → `"rodickwu"`
  - `superior` → `IsSuperior`（`false`→0，`true`→1）
  - 注意字段名大小写：预拉取返回的是 camelCase（`stepCode`/`stepUserID`），提交到 start_interview 需用 PascalCase（`StepCode`/`StepUserID`）
- **第 3 步**：如果 `flowStepList` 为空或不完整，停止自动发起并降级到招聘页面；禁止用 `start_interview` 写接口试探 StepCode、面试官或必填字段。
- **第 4 步**：把组装好的完整流程展示给用户确认；允许用户在确认前调整。
- **硬性规则**：`FlowStepGroup` **必须包含 `StepCode=HRSalaryView`（HR 薪资谈判）环节**；各 `StepUser` 必须来自生产岗位流程配置、具备对应环节资格且不能为 GM。

> 🔑 **StepCode 必须精确**：`start_interview` 按 StepCode 匹配岗位流程。禁止臆造 StepCode；合法环节仍必须以当前岗位 `get_recruit_post` 的实际返回为准。

> ✅ **【2026-07-29 重大更新·周浩用例】岗位→流程预拉取接口已找到**：✅ 实际上 MCP 存在一个**预拉取岗位面试流程配置的只读接口**：`recruit.recruit-post-social.get_api_web_recruitPost_get_recruit_post`（获取 RecruitPost 已发布岗位详情 NEW）。该接口的 `data.postData.flowStepGroup.flowStepList[]` 字段返回**完整的面试流程配置**，包括所有环节的 `StepCode/StepName/StepUser/staffId/IsSuperior` 等，与产品 UI 自动带出的内容完全一致。还附带 `data.postData.hr`（招聘经理/HRSalaryView）、`data.postData.firstView`（初试官/DeptView）字段。→ **Phase 5 的推荐做法从"靠错误驱动 + 用户手填"升级为"先调此接口读 flowStepList，再按业务需要组装 FlowStepGroup"**。调用前用 `SearchAPI(apiId="recruit.recruit-post-social.get_api_web_recruitPost_get_recruit_post")` 取全参数。⚠️ 注意：当前 `recruitPostId` 参数在某些 MCP 网关下被强转为 string 类型会报 `TYPE_MISMATCH` 校验错误，可改用 `get_api_post_GetPostByPostName` 接口（更轻量、字段足够）作为备选。

### Phase 6 — 第⑤步：保密流程校验与保密信息收集 + 发起前二次确认

**6.1 判断岗位/简历是否涉及保密流程**：
- 依据：简历详情 `data.resume.isSecret != 0`（保密简历）/ 岗位为保密岗位（`SecretPost`）。
- **两条独立触发路径，勿混为一谈**：① **简历保密**——由简历 `isSecret != 0` 触发；② **岗位保密**——由岗位为保密岗位触发，对应顶层字段 `SecretPost=true` 与 `SecretType=1`（1=保密岗位导致流程保密）。任一路径成立即进入保密流程。
- 缺口提示：MCP 无独立"校验岗位是否开启保密流程"接口；以简历 `isSecret` 与用户告知为准（`SecretPost` 为非 DB 字段，无法只读预查）。

**6.2 若开启保密流程 → 收集保密信息**（⚠️ **不做本地必填拦截**：用户给什么就带什么提交，缺失字段由系统在 `start_interview` 提交时校验并把报错原样透传给用户，Skill 端不再因保密字段缺失而阻断发起）：

| 保密字段 | 本地拦截 | 取值 | 说明 |
|----------|:----:|------|------|
| 保密类型 `SecretTypes[]` | ❌ 不拦截 | **多选**：竞业 / 敏感机构人选 / 高职级人选 / 其它 | 可选：通过 `recruit.recruit-post-social.get_api_web_base_data_secret_type_dic` 取 `TypeId/TypeName` 组装为 `[{TypeId, TypeName}, ...]`；**字典接口不可用或用户未提供 TypeId 时，带 `TypeName` 或直接留空提交均可，由后端校验** |
| 保护策略 | ❌ 不拦截 | **单选**：一星 / 二星 / 三星 / 其它 | 接口无独立字段（见下），并入保密原因/备注一起提交；用户未提供也不阻断 |
| 保密原因 `SecretReason` | ❌ 不拦截 | 文本 | 用户提供则带上；未提供留空提交，由后端决定是否报"保密原因必填" |
| 流程白名单 `Viewers[]` | ❌ 不拦截 | 员工列表 `[{StaffId, StaffName}]` | 可见人员，留空即空数组 |

> 🔑 **核心策略（用户明确要求）**：保密相关的一切字段（保密类型 / 保护策略 / 保密原因 / 白名单），**Skill 端一律不做"必填/缺失"校验与阻断**。把用户已提供的内容如实组装进 `SecretFlow` 直接提交，**让系统在流程提交时自行校验**；若系统返回某保密字段缺失/非法的报错，**原样透传给用户**，再请用户补齐后重试。

组装到 `start_interview` 的 `IsSecret=true` + `SecretFlow`（字段按用户实际提供填充，未提供的可省略或留空）：
```json
"IsSecret": true,
"SecretType": 1,        // 岗位保密路径时=1（保密岗位导致流程保密）；纯简历保密可省略
"SecretPost": true,     // 岗位为保密岗位时=true；非岗位保密可省略
"SecretFlow": {
  "SecretReason": "……",
  "SecretTypes": [{ "TypeId": 1, "TypeName": "竞业" }],
  "Viewers": [{ "StaffId": 123, "StaffName": "zhangsan" }]
}
```
> 📌 **顶层保密字段说明**：`IsSecret`(是否保密单据) 是总开关；`SecretType`/`SecretPost` 用于标识"岗位保密"这条触发路径。三者与 `SecretFlow` 一起提交，但同样**不做本地必填拦截**——用户/岗位信息给到什么就带什么，缺失由后端校验并透传。
> ⚠️ 【实锤·仅作说明，不作拦截依据】`start_interview` 的 `SecretFlow` 结构仅含 `SecretReason/SecretTypes/Viewers/Attachments/SecretFlows`，**"保护策略（一星/二星/三星）"在接口 schema 全字段中无独立字段，也无独立字典接口**。收集到的保护策略并入保密原因/备注一起提交；接口是否接收、缺失是否报错，均以系统提交校验结果为准并透传，Skill 不据此阻断。

**6.3 发起前二次确认（R2 硬性节点）**：本动作使用 `capability-registry.yaml` 中的 `social_interview_start` 受控写定义。

1. 冻结最终 payload，至少包含 CandidateId、RecruitPostId、RecruitDeptId、Candidate、回流字段、FlowStepGroup、保密字段及实际发送的所有可选字段。
2. 向用户回显业务卡片：候选人、部门、岗位、各流程环节与面试官、回流结论、保密设置和本次影响；手机号、邮箱、Token、Cookie、完整内部 payload 不展示。
3. **等待用户明确确认后**，一条命令完成「算摘要 + 生成信封 + preflight」：
   ```bash
   python3 scripts/build_write_envelope.py prepare \
       --action-key social_interview_start \
       --payload "$TMP_DIR/payload.json" \
       --target-ids <候选人+岗位复合标识> \
       --summary "社招发起面试：{部门} / {岗位} / {环节数} 个环节" \
       --out "$TMP_DIR/envelope.json"
   ```
   脚本自动从注册表带出 skill / target_type / TTL，并校验 payload 字段白名单与敏感信息（详见 `scripts/README.md`）。
   > 回退手工路径见 `controlled-write-contract.md`：`validate_write_action.py --digest` → 手工拼信封 → `--phase preflight`。
4. 确认有效期 10 分钟。用户修改任何字段后，原摘要立即失效，必须重新冻结、重新确认、重新 `prepare`。
5. 保密字段中用户未提供的项如实标注“未提供，交由系统校验”，但不得省略对整体 payload 的重新确认。
6. **结果确定后回填审计**（成功引用为 `FlowMainId`）：
   ```bash
   python3 scripts/build_write_envelope.py outcome \
       --envelope "$TMP_DIR/envelope.json" --status success --ref <FlowMainId>
   ```
   失败用 `--status failed --error-code "<真实错误码>"`；超时/结果不明用 `--status unknown`（**禁止自动重试**）。审计完成后删除临时文件。

### Phase 7 — 提交发起 + 结果处理

二次确认通过后调用发起接口：

```
CallAPI(apiId: "recruit.interview-flow.start_interview", params: {
  CandidateId: "{Rid GUID}",         // 必填
  RecruitPostId: 12345,              // 必填，不能为 0
  RecruitDeptId: 67890,              // 必填，不能为 0
  Candidate: "张三",                  // 可选：姓名 ≤50 字符
  IsReborn: false, RebornEngName: "",// 回流：IsReborn=true 时 RebornEngName 必填
  FlowStepGroup: { FlowSteps: [ /* 必含 HRSalaryView */ ] },
  IsSecret: false, SecretFlow: { /* 保密流程时填 */ }
  // 其他可选：InputFrom(1=PC,2=移动端) / IsDelayBackground / Viewers[] / IFCFlowMainId(推荐流程) / TraceId
})
```

> ⚠️ **字段约束补充**：`Candidate`（姓名）≤50 字符;`CandidateId` 非空、`RecruitPostId`/`RecruitDeptId` 均 ≠0（提交前已在 Phase 4 断言）。可选写字段 `InputFrom`/`IsDelayBackground`/`Viewers`/`IFCFlowMainId`/`TraceId` 按需带,不提供不影响主流程。

**结果判断与审计**：调用前将信封状态置为 `submitted`。外层 `code === 200` 且返回真实 `FlowMainId` 视为成功，审计状态写为 `success`，`audit.ref` 使用 `FlowMainId`；明确业务失败写为 `failed` 并记录真实错误码。

- **成功** → 说明简历已锁定并创建面试流程。展示成功卡片（当前环节 `StepName` + 处理人 `Owner`），随后执行同连接器状态回读。
- **返回不明确、超时或泛化错误** → 审计状态标记 `unknown`，立即读取简历详情，检查 `status` 是否变为面试中、`flowList` 是否出现本次新流程。禁止自动重试；任何重试都必须重新确认。
- **后续返回“已在面试流程中”** → 不直接判成功，先回读详情；只有确认出现新在途流程后才按成功处理。
- **失败 / 报错** → 返回业务可读的原始 `msg/errorCode` 并给出修正建议；不得暴露 Token、Cookie、请求头、完整 payload 或内部调用栈。

**成功后：询问是否安排面试（硬性交互）**：
> ✅ 已成功发起面试并锁定简历。是否现在安排面试？

- 用户选"**否**" → 结束本次任务（告知稍后可在待办中安排）。
- 用户选"**是**" → 不直接复用 `start_interview` 返回的 TraceId 拼接下单请求。必须：
  1. 在同一生产 `recruit-mcp` 回读简历详情，确认状态已变为“面试中”且存在新在途 FlowMain；
  2. 重新查询社招待办，取得当前环节最新的 `nextTraceId/id`、orderId 和联系人字段；
  3. 重新进入 `flows/S.md`，按 S-Pre → S-0 → S-A 的既有安排流程执行；
  4. 若状态或待办尚未同步，停止自动下单并提示稍后重试，禁止拿发起返回 ID 冒充待办 traceId。

---

## 四、错误处理速查

| 错误现象 | 可能原因 | 处理方式（均须原样透传原文） |
|----------|---------|------------------------------|
| 搜索 `atsRights` 非空 | 当前用户对简历无 ATS 权限 | 返回有权限人列表，建议联系或换账号 |
| `Status != 1` | 简历已锁定 / 已在流程 | 返回 `StatusText`，说明不可重复发起 |
| 同名多份简历 | 姓名匹配多人 | 展示候选清单，请用 RID/手机号/链接确认，禁止默认取第一条 |
| 回流 `data.code=3000006` | 回流校验不通过 | 原样返回"需人工校验，发邮件至 IVC-service@tencent.com" |
| 回流 `data.code=3000007`（且 `staffId≠0`） | 找到了在职/该员工，但**非集团正式离职回流**（实测 2026-07-22：在职员工 rodickwu→staffId=56251/code=3000007） | 提示确认曾用英文名 / 说明非回流场景 |
| 回流 `data.code=0` 且 `data.staffId=0` | **未找到该员工**（姓名/英文名不存在或拼写错误，实测：不存在姓名→staffId=0/code=0/msg="") | 请用户核对姓名拼写；**先看 staffId==0 再看 code** |
| `IsReborn=true` 但无 `RebornEngName` | 缺曾用英文名 | 阻断并请用户补充 |
| 发起报"岗位已停招 / 岗位无效" | RecruitPostId 非法或停招 | 请用户重新提供岗位，重查 ID |
| 发起报"简历已在面试流程中" | ① 简历此前已被发起过（正常去重拦截）；② **前一次 `start_interview` 调用已成功（即便是泛化 500），当前是重复提交被拦**（耗时通常 2-3s，明显短于泛化 500 的 5s+）。⚠️ **这是"发起已成功"的重要信号，不是失败** | ① **先查简历详情确认**：若 `status=3`(面试中)、`flowList` 有新记录，说明发起成功，直接进入 Phase 7 成功处理流程；② 若详情确认无流程，才是真正的旧流程去重 |
| 发起报"该简历不存在" | `CandidateId` 非法/不存在（如假 GUID、已删除简历） | 🧪 实测 2026-07-22：假 GUID（全 0）→ `code 500 该简历不存在`。核对 `CandidateId` 是否为搜索返回的真实 RID，勿用占位/臆造 GUID |
| 发起返回 `status 500` 但 **body 为空、无报错文案** | `RecruitPostId=0`（🧪 实测 2026-07-22 稳定复现两次，非瞬时中断）——后端对 PostId=0 的兜底不返回文案 | 这类空 body 无法透传原文；**务必在 Phase 4 提交前硬断言 `RecruitPostId≠0`**，从源头避免（不要靠后端报错发现）|
| 发起报"该简历手机号存在另一份简历，已在面试流程中" | 同一手机号的另一份简历已在流程中（**跨简历手机号去重**，非本 RID 自身状态） | 搜索/详情只回本 RID 的 Status，**Phase 1.5 无法预判**；返回该原文，请用户处理冲突简历或换候选人 |
| 发起报"缺少薪资谈判环节" | FlowStepGroup 未含 HRSalaryView 环节 | 补齐 HR 薪资谈判环节 |
| 发起报"请勿重复操作"（**极短耗时 ~100ms 秒回**） | **短时防重复提交锁**（同一 RID/参数在极短时间内被连续发起，被后端幂等/防抖拦截，非业务校验失败） | **不要立即重试**；稍候数秒后再发起；确认上一次发起是否已成功（查详情 flowList），避免重复创建 |
| **发起报泛化 `操作失败，请联系小T(连线HR)或8008`** | 参数、岗位流程配置或前一次提交结果不明确 | 标记 unknown，立即回读详情与 flowList；已产生新在途流程则按成功处理，未产生则停止自动提交并给出页面/客服路径，禁止写接口试探或盲重试 |
| 发起报"{英文名}不是面试官" | 面试官不在当前生产岗位流程配置中 | 重新读取岗位 `flowStepList`，使用接口返回的 engName 与 staffId；不得手填猜测 |
| 发起报"{环节}面试官数据异常" | 面试官虽是注册面试官，但**未被配置为该环节类型的面试官**（如用 HR 去当"部门内专业面试官"） | 该环节需换成**具备对应资格**的面试官（部门专业面试官/用人决策者/HR 官等按环节匹配） |
| 发起报面试官非法/为 GM | 面试官不在定义表或为 GM | 更换合法面试官 |
| 发起报保密字段缺失/非法（如"保密原因必填"） | 用户未提供该保密字段，系统提交时校验拦截 | **不在本地预先阻断**；原样透传后端报错，请用户补齐对应保密字段后重试 |
| 能力不存在（发起接口） | 当前生产连接器未暴露该能力或权限不足 | 停止自动写入，给出简历详情页；禁止切换测试连接器 |
| 发起报姓名超长 / 参数长度非法 | `Candidate` 姓名 >50 字符 | 截断或请用户确认规范姓名后重试 |
| 发起报部门/岗位不匹配 | 用户另指部门与岗位反查带出的 `RecruitDeptId` 冲突 | 回 Phase 4 确认以岗位带出部门为准，勿静默覆盖 |
| 分页越界（`from+size≥10000` 或 `size>200`） | 🧪 实测 2026-07-22：**后端不报错、静默钳制**（`from→0`、`size→200`），返回结果页码可能与预期不符 | 主动收窄 `size≤200`、控制 `from+size<10000`；**勿依赖后端报错发现越界**，结果异常时自查分页 |
| 面试官/白名单无法解析 staffId | 独立员工查询不可用 | 面试环节 staffId 从 `flowStepGroup.flowStepList[].stepUserID` 获取；白名单拿不到则请用户补充，不得猜测 |
| 预拉取 `get_recruit_post` 报 `TYPE_MISMATCH` | 参数类型与当前生产 schema 不一致 | 重新读取 SearchAPI schema 并按正确类型调用；仍失败则用岗位名反查接口或降级页面，禁止附加无业务字段绕过 |

---

## 五、生产边界与已验证规则

1. **无独立可发起校验接口**：社招主要依据 `atsRights`、`Status/status`、`Enable/enableFlag` 和在途 `flowList` 判断；最终仍以服务端写入校验为准。
2. **完善度字段有两套**：搜索接口使用 `WorkExperienceList/EducationList`，详情接口使用 `resumeWorkExp/resumeEdu`，禁止混用。
3. **岗位流程必须只读预拉取**：使用 `get_recruit_post` 获取 `flowStepList`，从中提取 StepCode、engName 和 staffId。读取失败时降级页面，禁止用写接口试探。
4. **必填字段本地硬断言**：CandidateId 非空，RecruitPostId 与 RecruitDeptId 均不得为 0，岗位与部门必须匹配。
5. **flowList 非空不等于阻断**：历史终态流程可以重新发起；只有仍在途流程才阻断。跨手机号的另一份简历可能只能由服务端发现。
6. **回流判断先看 staffId**：staffId=0 表示查无此人；staffId 非 0 后再解释业务 code。回流附加字段只使用接口返回或用户提供的值。
7. **保密触发路径分离**：简历保密与岗位保密分别判断；保护策略没有独立字段时只在确认摘要中说明，不擅自改变字段语义。
8. **start_interview 不自动装配流程**：必须提交由生产岗位配置生成的完整 FlowStepGroup，且包含 HRSalaryView。
9. **未知结果禁止重试**：超时、空响应、泛化错误先回读状态并标记 unknown；任何重试都需要新的确认记录。
10. **安排必须 fresh handoff**：发起成功后重新拉取生产待办，使用最新 nextTraceId/id 进入 S-A，不直接复用发起接口返回的 TraceId。

> 详细接口参考：`../references/interview-lifecycle/social-initiation-api.md`。
