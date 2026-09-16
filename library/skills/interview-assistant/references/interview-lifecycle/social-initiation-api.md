# 社招发起面试 — API 参考

> 所有 apiId 为三段式 `{domain}.{group}.{name}`，**必须**先经 `SearchAPI(apiId=...)` 确认参数后再 `CallAPI`，禁止自行拼造。
> 所有接口统一通过专家包注册的生产连接器 `recruit-mcp` 调用。首次调用必须以生产 SearchAPI 返回的能力与 schema 为准。

---

## 1. 社招简历搜索 — 定位 RID（只读）

`recruit.social-resume.post_api_resume_query_query` (POST /api/resume_query/query)

常用请求体字段：
- `name` string — 姓名精确匹配
- `mobile` / `email` string — 手机号 / 邮箱精确匹配（含历史）
- `searchKey` string — 全文关键字（多个空格分隔）
- `diggerSearchId` string — **每次搜索必传**，`mcp-recruit-{uuid}`，分页时保持不变
- `from` / `size` int — 分页（from>0 且 from+size<10000；size≤200）

关键返回（`data.resumes[]`）：
- `Rid` string(GUID) — **发起面试用的 CandidateId**；详情链接 `https://zhaopin.woa.com/resume/resume_detail?rid={Rid}&fromplace=MCP`
- `ExtId` string — 数字型 employeeId
- `Name` / `Gender` / `Email`（脱敏）/ `Mobile`（脱敏）
- `Status` int — **判断锁定用此字段，不要用 Locked**：1=待筛选(未锁定)；2=推荐中,3=面试中,4=录用中,5=入职中,6=已入职,7=其他 → **非 1 均视为已锁定/在流程**
- `StatusText` string — 状态文本
- `Enable` int — 1=正常，0=已删除
- `IsSecret` int — 是否保密简历（非 0=保密）
- `atsRights` array — **非空表示当前登录人无权限查看/操作该简历**，元素含 `staffId/engName/fullName/bgId/bgName`
- `WorkExperienceList[]` / `EducationList[]` — 工作/教育经历（可粗判完善度）

---

## 2. 社招简历详情（含面试流程记录）（只读）

`recruit.social-resume.get_api_resume_detail_getresume_with_detail` (GET /api/resume_detail/getresume_with_detail)

请求参数（query）：
- `rid` string ✅ — 简历 RID
- `fromPlace` string ✅ — MCP 过来传 `MCP`

关键返回：
- `data.resume` — 简历详情：
  - `resumeWorkExp[]` — **工作经历**（判断完善度：为空则提示未完善）
  - `resumeEdu[]` — **教育经历**（判断完善度：为空则提示未完善）
  - `extendLastWorkExp` — 最后一份工作经历（当前公司职位展示）
  - `extendLastResumeEdu` — 最后教育经历（最高学历展示）
  - `extendWorkYearValue` number — 动态工作年限（展示用，勿用 workYears）
  - `isSecret` int — 是否保密简历（0=非保密；非 0=保密）
  - `status` int / `statusText` — 简历状态
- `data.flowList[]` — 已有面试流程记录：`flowMainId / postId / postName / stateId / stateName / creater / traces[]`（各环节 stepId/stepName/owner）/ `secret`（是否保密流程）
- `data.contactRecords[]` — 沟通记录

---

## 3. 离职回流校验（只读）

`recruit.interview-flow.reborn_validate` (GET /api/HRSalary/rebornValidate)

请求参数（query）：
- `dimissionName` string ✅ — 离职员工英文名（曾用英文名/之前帐号）
- `flowMainId` int ✅ — 流程主 ID（**发起前流程未建，先试传 0**，见 SKILL 时序边界）
- `rid` string ✅ — 候选人简历 RID(GUID)

返回（注意两层 code）：
- 外层 `code` = 200（HTTP 成功）
- `data.staffId` int — 员工 ID（**0=查无此人**，曾用英文名有误/查无此人；**判断时先看此字段**）
- `data.code` int — **业务校验码**（实测 2026-07-22 纠偏）：`0`=查无此人（配合 `staffId=0`）/ `200`=通过 / `3000006`=不通过需人工校验 / `3000007`=找到但非集团离职回流（此时 `staffId≠0`，如在职员工 rodickwu→56251）。**切勿把 staffId=0 等同 code=3000007**；两异常分支 `msg` 均为空。
- `data.msg` string — 校验消息（"符合要求" / "需人工校验，请部门招聘经理发邮件至 IVC-service@tencent.com 申请查询" / 空）
- `data.suggestion` string — 重新录用建议 / 离职面谈记录（无记录时="无离职面谈记录"；可回填 start_interview.RebornSuggestion）

---

## 4. 发起社招面试流程（写操作！）

`recruit.interview-flow.start_interview` (POST /api/v2/interview/startInterview)

### 必填字段
- `CandidateId` string(GUID) ✅ — 候选人简历 RID，不能为空
- `RecruitPostId` int ✅ — 应聘岗位 ID，不能为 0
- `RecruitDeptId` int ✅ — 应聘部门 ID，不能为 0（应属于该岗位；与用户另指部门冲突时先确认，勿静默覆盖）

### 候选人信息（可选）
`Candidate`(姓名,**≤50 字符**) / `MobilePhone` / `Email` / `GenderId` / `MobileCountry`

### 岗位/部门（可选）
`RecruitPostName` / `RecruitDeptName` / `RecruitDegree` / `IsLowerDegree` / `PostProperty`

### 离职回流
- `IsReborn` bool — 是否离职回流（默认 false）
- `RebornEngName` string — 曾用英文名（**IsReborn=true 时条件必填**）
- `RebornSuggestion` / `RebornMemo` / `RebornMemoId` / `RebornRemark` / `DimissionReason` / `IsReBornContinue`

### 面试流程步骤 `FlowStepGroup.FlowSteps[]`（非 DB 字段）
每个环节：
- `StepCode` string — 步骤代码，如 `DeptView`(部门面) / `HRSalaryView`(HR薪资谈判) / `CommitteeView`
- `StepName` string — 步骤名称
- `StepUser` string — 面试官英文名；`StepUserID` int — 面试官员工 ID
- `IsSuperior` int — 是否上级：0=否 1=是
- `StepCodeEx` / `StepIgnoreValue` / `HasTodo` / `ArrangeNext`
- **⚠️ 必须包含 `StepCode=HRSalaryView` 的薪资谈判环节，面试官须来自面试官定义表且不能为 GM**

> 📌 **岗位与流程的获取方式**：
> - 进入发起流程后必须由用户提供岗位名称或岗位 ID；岗位名称使用 `get_api_post_GetPostByPostName` 反查岗位和部门。
> - 岗位确定后调用 `recruit.recruit-post-social.get_api_web_recruitPost_get_recruit_post`，从 `data.postData.flowStepGroup.flowStepList[]` 读取完整流程模板。
> - 映射规则：`stepCode→StepCode`、`stepName→StepName`、`stepUserID→StepUserID`、`stepUser` 取第一个 `(` 前的英文名作为 `StepUser`、`superior→IsSuperior`。
> - 预拉取失败或流程不完整时停止自动写入并降级页面；禁止用 `start_interview` 试探字段或面试官。

### 保密流程
- `IsSecret` bool — 是否保密单据
- `SecretType` int — 1=保密岗位导致流程保密
- `SecretPost` bool — 是否保密岗位（非 DB 字段）
- `SecretFlow` object：
  - `SecretReason` string — 保密原因（必填）
  - `SecretTypes[]` — `[{TypeId, TypeName}]` 保密类型（多选：竞业/敏感机构人选/高职级人选/其它）
  - `Viewers[]` — `[{StaffId, StaffName}]` 流程白名单/可见人员（选填）
  - `Attachments[]` — `[{FileId, FileName}]` 附件
  - `SecretFlows[]` — `[{FormId, FlowMainId}]`
- ⚠️ **保护策略（一星/二星/三星）在 schema 中未见独立字段**，需向用户收集并在确认卡片展示，提交方式以接口实际接收为准。

### 其他常用（可选）
`InputFrom`(1=PC,2=移动端) / `IsDelayBackground` / `Viewers[]` / `IFCFlowMainId`(推荐流程) / `TraceId` / `HasOfferPreCommunicationStep`

### 校验规则（后端）
1. CandidateId 不能空 2. RecruitPostId 不能为 0 3. RecruitDeptId 不能为 0
4. IsReborn=true 时 RebornEngName 必填 5. 岗位不能已停招 6. 简历不能已在面试流程中
7. 面试官须来自面试官定义表且不能 GM 8. FlowStepGroup 必须含 HRSalaryView

### 返回（外层 code=200 即 HTTP 成功）
`data`: `InterviewId`(面试安排ID) / `TraceId`(流程追踪ID,后续关键) / `FormId` / `FlowMainId`(主流程ID) / `RequestId` / `StepId` / `StepName`(当前环节) / `Owner`(处理人英文名) / `OwnerId`

> 失败时 `msg` / 报错原文必须原样返回给用户。

---

## 5. 保密类型字典（只读）

`recruit.recruit-post-social.get_api_web_base_data_secret_type_dic` (GET /api/web/base_data/secret_type_dic)
- 返回 `data` 保密类型字典（用于取 SecretTypes 的 TypeId/TypeName）。

---

## 6. 面试安排（发起成功后，用户选择"是"时）

- `recruit.interview-arrange.post_order_add` (POST) — 创建社招面试安排（下单）。支持单面/多对一/多轮一对一，现场/电话/面呗/腾讯会议等。
- `recruit.interview-arrange.get_order_detail` / `get_order_invite_detail` — 查安排/邀约详情。
- `recruit.interview-arrange.get_auth_checkInterviewer` (GET) — 校验面试官权限（Phase 5 校验面试官可用）。
- `recruit.social-resume.get_api_post_GetPostByPostName` (GET) — 按岗位名模糊查岗位 ID（Phase 4 岗位反查）。

关键枚举（面试安排）：
- `interviewForm`：1=现场 2=电话 3=面呗 4=腾讯会议 5=腾讯会议(面呗) 6=牛客网
- `interviewType`：1=单面 2=多对一 3=多轮一对一 4=集体面试
- `stateId`：1 首次邀约待候选人确认 … 8 邀约完成 10 面试已完成 11 已关单

> ⚠️ `post_order_add` 具体必填项以 `SearchAPI(apiId="recruit.interview-arrange.post_order_add")` 返回 schema 为准，通常需 `InterviewId`/`TraceId`、面试官、时间、地点/会议方式，勿臆造。

---

## 7. 生产调用边界

- 面试环节的 staffId 与英文名优先从岗位 `flowStepList` 获取；白名单人员无法解析时请用户补充，禁止猜测。
- 所有参数以生产 SearchAPI schema 为准；出现类型不匹配时修正参数结构，不得追加无业务字段绕过校验。
- `start_interview` 属于 R2 写操作，必须经过 payload 冻结、摘要绑定、10 分钟确认、preflight 校验和结果审计。
- 超时、空响应或泛化错误一律标记 unknown，先回读简历状态和 flowList，禁止自动重试。
- 发起成功后必须重新读取生产待办并取得 fresh trace，再交给 S-A 安排本轮面试。
