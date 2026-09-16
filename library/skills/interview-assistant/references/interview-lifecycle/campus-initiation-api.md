# 校招发起面试 — API 参考

> 所有 apiId 为三段式 `{domain}.{group}.{name}`，**必须**先经 `SearchAPI(apiId=...)` 确认参数后再 `CallAPI`，禁止自行拼造。
> 所有接口统一通过专家包注册的**生产连接器 `recruit-mcp`** 调用（与社招发起同一连接器）。首次调用必须以生产 SearchAPI 返回的能力与 schema 为准。
> ⚠️ **禁止**通过 `_extra` 等无业务字段绕过网关校验——如遇 `TYPE_MISMATCH`，以 SearchAPI 返回的正确参数类型重试。
> 本文档只覆盖**校招 / 实习**发起接口（`campus-interview-service` 分组）。社招接口见 `social-initiation-api.md`。

---

## 一、校招发起面试（写操作）

### 1.1 发起校招面试（核心写操作）

- **apiId**: `recruit.campus-interview-service.start_campus_interview`
- **Method**: POST · **Path**: `/api/web/interview/start` · ⚠️ 写操作（走受控写契约 `campus_interview_start`）

**必填参数**：

| 参数 | 类型 | 说明 |
|------|------|------|
| `resumeIds` | integer[] | 候选人简历 ID 列表，**支持批量**：传多个 ID 即一次为多人各创建一条同参独立面试流程；不能为空 |
| `recruitYear` | integer | 招聘年份 = **招募周期年，不是候选人毕业年份** 🔴 必须由 1.5 `get_interview_recruit_year` 按 `recruitType` 反查取值，禁止从简历 `graduate_time` 推导 |
| `recruitType` | integer | 招聘类型：**发起接口语义 1=应届毕业生，2=实习生**（🔴 与搜索接口语义相反，禁止透传搜索返回值）|
| `recruitCity` | integer | 招聘线路 ID（对应 s_dictionary_recruit_line 主键）；未提供默认 48（远程面试）|
| `stepId` | integer | 流程步骤：1=集体面试，2=初试（仅这两个可作发起环节）|
| `recruitProject` | integer | 招聘项目 ID（见 1.5 项目下拉 + SKILL 2.2 白名单反查）|
| `subDepartment` | integer | 下级组织 ID（1.6 org_lookup 反查）|
| `positionOuterTitle` | string | 职位对外标题 |

**可选（但实测须显式传）参数**：

| 参数 | 类型 | 说明 |
|------|------|------|
| `staffId` | integer | ⚠️ **必须显式传当前用户工号，不能留 null**（否则报"面试官信息不存在"）；来源见 1.7 |
| `position` | integer | 职位 ID，**必须从 `position_lookup`（1.9）或待办列表已验证值获取**，禁止从简历 `station` 映射（否则报"职位无效或已禁用"）。特例：`recruitProject=12`（项目实习）后端跳过职位校验 |
| `jobFamily` | integer | 海外职位 ID |
| `unitOwnershipTypeId` | integer | 组织归属类型，3=海外（默认 0）|

**响应**：
```json
{ "status": 200, "data": { "success": true, "total": 1, "errorMsg": [], "successMsg": [] } }
```
**判断成功**：外层 `status=200` 且 `data.success=true` 且 **`errorMsg` 为空数组**。
> ⚠️ **"三空"成功**：实测存在 `success=true`、`errorMsg=[]` 且 `successMsg=[]`（既无错误也无成功文案）。**禁止**因 successMsg 空误判失败，也不得仅凭 success=true 报成功——**必须**紧接 `getResumeByRId`（1.8）核实新增同参 `status=0` 记录并取 `interview_id`，才判定成功。
> **注意**：此接口**不直接返回 traceId**，成功详情链接需重新拉待办列表（1.7）从 `pcUrl` 取。

> 📦 **批量发起**：`resumeIds` 传多个 ID → 一次写调用为每人各创建一条参数相同的独立面试流程（每人独立 `interview_id`，非集体面试）；单批建议 ≤20，超出分片。响应 `data.total` 为处理人数；`errorMsg` 非空或部分未落库时，逐人 `getResumeByRId` 核验生成结果表，不因个别失败否定整批。

### 1.2 前置校验：简历控制限制（只读）

- **apiId**: `recruit.campus-interview-service.get_resume_control_info` · POST

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| `resumeIds` | integer[] | ✅ | 简历 ID 列表，支持批量（一次数组传全部候选人，逐人解析 `actionEnable`）|
| `ctrlType` | string | ✅ | 操作类型：`StartInterview`（发起面试）等 |

**响应关键字段**：`actionEnable`(boolean 是否可执行)、`showHint`(boolean)、`hintList`(string[] 提醒话术)。
> `actionEnable=true` 是必要非充分门槛；最终以 1.1 写接口响应为准。

### 1.3 前置校验：面试官课程学习状态（只读）

- **apiId**: `recruit.campus-interview-service.check_course_learn_status` · GET · 无参数

**响应**：`finishFlag`(boolean|null，null=未开始/true=完成/false=未完成)、`learnUrl`(未完成时的学习页 URL)。
> 页面级提示门禁，非后端 `start` 强制校验；本步仅为对齐网页端行为、提前提示用户。

### 1.4 获取允许发起面试的环节步骤（只读）

- **apiId**: `recruit.campus-interview-service.get_interview_start_step` · GET · 无参数

**响应**：`[{ "stepId": 1, "StepName": "集体面试" }, { "stepId": 2, "StepName": "初试" }]`
> 🔴 发起环节仅 1/2；硬传 3/5/999 后端统一硬拦"该环节不可直接发起面试，只能从集体面试或初试发起"。

### 1.5 下拉选项接口（半静态，会话级缓存）

| 用途 | apiId | 参数 | 响应字段 |
|------|-------|------|---------|
| 招聘项目列表 | `recruit.campus-interview-service.get_interview_recruit_project` | `filterStart`(boolean, 默认 true) | `id` / `title` / `type` / `description` |
| 招聘年份列表 | `recruit.campus-interview-service.get_interview_recruit_year` | `recruitType`(1=毕业生,2=实习生) | integer 数组（如 `[2025,2026,2027]`）|
| 招聘线路列表 | `recruit.campus-interview-service.get_interview_recruit_line` | 无 | `key`(ID) / `value`(名称) / `defaultFlag`；远程面试恒为 `key=48` |

> 🔴 **招聘年份接口的两个必知事实**：
> ① **年份集合按 `recruitType` 分岔**——实习生与应届毕业生返回的可选年份**不同**（实测出现过实习生仅 1 个值、应届 2 个值的情况），切换类型必须重查。
> ② **返回的是"当前在招周期"，与候选人毕业年份无关**。候选人毕业年可能远晚于返回集合里的任何值，这是正常的——**不要**因为"候选人是 N 年毕业"就把 `recruitYear` 填成 N。取值规则见 `S-initiate-campus.md` 2.2.2。

### 1.5.1 当前用户信息（staffId 首选来源，只读）⭐

- **apiId**: `recruit.huoshui-server.get_personal_api_web_personal_infoDetail` · GET · 无参数

**响应关键字段**：`data.staffId`（发起接口 `staffId` 必填值）、`data.fullName`、`data.departmentId`（可与 1.6 org_lookup 交叉验证）、`data.bgId`。

> ✅ **优先用本接口取 staffId**：无依赖、不需待办、不需简历，直接从认证身份解析，一次调用同时拿到 staffId + departmentId + bgId。
> ⚠️ 1.7 待办列表也能取 staffId，但**慢且待办为空时取不到**，仅作回退方案。

### 1.6 组织 ID 查询（面试组织反查，只读）

- **apiId**: `recruit.recruit-standard-resource.post_api_mcp_org_lookup` · POST · `/api/mcp/org/lookup`

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| `orgNameCn` | string | ✅ | 组织末级名（如"BP组"）或完整路径（"/"分隔），非空 |

**响应**：`data.orgId`(即 `subDepartment` 取值)、`data.orgFullNameCn`(全路径，回显确认用)、`data.orgNameCn`(末级名)。
**判定**：唯一命中→取 `orgId`；末级名多命中→`data=null`+提示补上级路径；零命中→请用户提供 ID/完整路径。
> 生产 `recruit-mcp` 可用，**优先主动调用反查 `subDepartment`**；仅多命中/零命中无法唯一确定时回退 1.7 待办列表扫描或请用户提供数字 ID。

### 1.7 校招面试待办列表（subDepartment 反查 + 当前用户 staffId 来源，只读）

- **apiId**: `recruit.campus-center-front.get_campus_interview_todo_list` · POST · `/v1/interview/todoListV2`

> ⚠️ 该接口慢，且 `staffId`/`subDepartment`/`position` 是会话级稳定参数——会话首次拉取后缓存复用，不要每候选人重调。

**请求参数**：`pageIndex`(≥1)、`pageSize`(1-200)、`keyword`(姓名/手机号)、`recruitType`、`recruitYear`、`currentStep` 等（详见 SearchAPI）。

**响应关键字段**（personList[] 元素）：

| 字段 | 类型 | 说明 |
|------|------|------|
| `subDepartment` | integer | 下级组织数字 ID（即发起接口的 `subDepartment` 取值）|
| `subDepartmentTxt` / `fullOrgName` / `fullOrgLocation` | string | 组织名/全路径，用于匹配用户指定路径 |
| `staffId` | integer | **当前登录用户工号**（同一用户所有待办一致），即发起接口 `staffId` 必填值 |
| `flowTraceId` | integer | 面试流程跟踪 ID |
| `pcUrl` | string | 面试待办详情页链接（生产格式 `https://zhaopin.woa.com/zhaopin/campus/NewInterviewDetail?traceId={flowTraceId}`）|

**反查用法**：组织 ID 按 `subDepartmentTxt`/`fullOrgName` 匹配取 `subDepartment`；当前用户工号直接取任一记录 `staffId`；成功后"去处理"链接重新拉此列表按名/rid 匹配新记录取 `pcUrl`（超时不推翻成功结论，先用 `getResumeByRId` 的 `interview_id` 报成功）。

### 1.8 简历详情聚合（面试流程预判断 / 落库核实，只读）⚠️

- **apiId**: `recruit.campus-resume-search.get_v1_mcp_resume_getResumeByRId` · GET · `/v1/mcp/resume/getResumeByRId`

**请求参数**：`rid`(string, 必填)

**响应关键字段**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `data.interviewRecords` | object | 面试流程记录**容器对象**（⚠️ 不是数组）；实际记录在 `.list[]`，另有 `.allnum` 总数 / `.showFlag` |
| `data.interviewRecords.list[]` | array | 面试流程记录数组；判断"是否已在面试流程中"要遍历它 |
| `data.interviewRecords.list[].status` | string | **`"0"`=进行中/已发起未结束**（命中即"已在流程中"）；非 0 视为已结束/放弃。⚠️ 实测为**字符串**，比较时勿用严格 `=== 0` |
| `data.interviewRecords.list[].interview_id` | integer | 面试流程 ID（受控写 `audit.ref` / 落库核实用）|
| `data.interviewRecords.list[].start_step_txt` | string | 发起环节名（如"初试"）；同级另有 `start_step` |
| `data.interviewRecords.list[].recruit_year` / `recruit_type` / `recruit_project` / `recruit_city` / `position` / `sub_department` | mixed | 落库后的实际参数，用于与提交 payload **逐字段比对**确认是否同参 |
| `data.resumeInfo.flow_status` / `flow_txt` | string | 简历当前流程状态；发起成功后会从"待筛选"推进到发起环节名 |

> 🔴 **字段命名风格差异（实测）**：`interviewRecords.list[]` 内部用**下划线风格**（`interview_id` / `recruit_year` / `start_step_txt` / `sub_department`），而待办列表 `personList[]` 用**小驼峰**（`interviewId` / `recruitYear` / `stepId` / `subDepartment`）。跨接口取值时勿混用命名。
> 🔴 **落库核实的正确做法**：不能只看"有没有 `status=0` 记录"，要把 `recruit_year` / `recruit_type` / `recruit_project` / `recruit_city` / `position` / `sub_department` 与提交 payload **逐字段比对**，确认是本次提交产生的记录、而非历史遗留流程。

**判定与权限**：遍历 `interviewRecords` 存在任一 `status=0` → 已在流程中（Phase 2.3.5 触发提示）；调用方需面试官权限或为该简历伯乐，读不到时**不阻断**，交由 Phase 0.1 / Phase 3 兜底。

### 1.9 职位反查（内部通道职位 ID，只读）

- **apiId**: `recruit.recruit-standard-resource.post_api_mcp_position_lookup` · POST

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| `postNameCn` | string | ✅ | 职位名（如"视觉设计""产品策划"）|

**响应**：`data.postId`(即 `position` 取值)、`data.postFullNameCn`(族/类/职位完整路径，回显用)、`data.matchCount`(命中数)。
**判定**：唯一命中→取 `postId`；多命中→展示 `postFullNameCn` 列表让用户确认；零命中→请用户提供更准确职位名。
> 🚫 **禁止使用门户职位树** `positionJoinQueryTree`/`getPositionByParentIds` 的 id——它们与发起接口所需的内部通道职位主键是两套体系，硬套必被后端拦（实测 position=140→"职位无效或已禁用"）。

### 1.10 候选人搜索（定位 RID，只读）

- **apiId**: `recruit.campus-resume-search.post_v1_resume_search` · POST

| 参数 | 类型 | 说明 |
|------|------|------|
| `name` | string | 姓名精确匹配 |
| `mobile` | string | 手机号精确匹配（同名歧义确认用）|
| `startInterviewEnable` | int | 1=仅返回当前用户可发起面试的简历 |
| `searchId` | string | **每次搜索必传**（随机 UUID `mcp-campus-{uuid}`），分页时保持不变 |
| `page` / `limit` | int | 分页 |

**关键返回**（`data.list[]`）：`rid`(作 resumeIds)、`name`、`mobile`(脱敏，仅辨识同名用)、`recruitType`(🔴 搜索语义 1=实习/2=校招/3=社招，禁止透传给发起接口)。
简历链接：`https://zhaopin.woa.com/resume/campus/ResumeDetail?rid={rid}`。

---

## 二、调用约定

1. 所有 apiId 必须通过 SearchAPI 两步法获取后使用（发现能力 → 获取详情），不可自行构造。
2. CallAPI 统一使用 `params` 对象传参。
3. 写操作前必须走受控写握手（R2 二次确认 + payload 摘要，见 `S-initiate-campus.md` Phase 2.5）。
4. 本文档仅覆盖校招 `campus-interview-service` 分组接口；社招接口见 `social-initiation-api.md`。

### 2.1 连接器路由（生产化）

- 全链路统一用**生产连接器 `recruit-mcp`**（与社招发起同一连接器）。
- 首次发起前先 `SearchAPI` 探测 `start_campus_interview` 能力可用后再走完整流程；若生产 SearchAPI 未返回该能力，停止自动写入、降级到校招简历详情页，**不得切换测试连接器**。

### 2.2 超时与重试

- `get_campus_interview_todo_list`、`org_lookup` 偏慢、偶发超时；MCP 连接偶发瞬时中断（`Connection closed`/`socket hang up`/`ECONNRESET`）。
- **需重试类失败**：超时/无响应、连接层错误、泛化"网络错误"。给足超时（≥120s），仅对失败的那几项重试一次（隔 2-3s），不重跑整批；连接中断伴随 schema 丢失先 `SearchAPI` 重载再重试。
- **不算超时、按正常错误处理**：明确 `errorMsg` / `403` / 空数据。
- 并发建议 ≤5/批，频繁中断时降到 3-4/批。

### 2.3 会话级缓存

- 项目/年份/线路/环节下拉是半静态选项，首拉后缓存到会话级，不为每候选人重复拉取（仅 `recruitType` 切换等需重查对应接口）。
- `org_lookup` 生产可用，优先调用；仅多命中/零命中时回退待办列表扫描。
- **年份两种类型都预拉**（`recruitType=1` 与 `=2` 各一次），避免用户在确认环节改类型时二次往返。

### 2.3.1 调用预算参考（用于自查是否在空转）

| 阶段 | 预期调用数 | 说明 |
|---|:---:|---|
| 预热批（会话仅一次） | 8~9 | 个人信息 + 项目/线路/环节/课程 + 年份×2 + org_lookup + position_lookup，分 2 批并行 |
| 每候选人 | 3~4 | 控制校验 → （2.3.5 在途预判断）→ 写接口 → 回读核实 |
| 成功后取链接 | 1 | 待办列表取 `pcUrl`（慢接口，仅 1 次） |
| **单人首次发起合计** | **~13** | 含预热；同会话第二人起降到 3~4 |

> 🔴 **超出预算 2 倍以上（>30 次）说明在空转**：常见原因是没做预热批缓存、每个字段现用现取、或对同一超时接口连环重试。此时停手回查参数，勿继续硬试（参见 agent §1-A 单轮 50 次硬上限）。

### 2.4 写接口软错处理

- `start_campus_interview` 返回"当前有面试官正在操作""此简历状态目前不可发起面试"等软错时，**勿立即重试**；先 `getResumeByRId` 查 `interviewRecords`，确认是否已落库（同参 + status=0 即成功），避免重复发起。
