# HRClaw 邮件 / 企微 Tips 通知 SOP

用于保温场景下，招聘经理向导师或直接上级发送候选人保温信息。只处理**通知导师/上级**，不用于群机器人日报；群推送走 `references/reminder.md`。

## 1. 通知通道与认证方式

### 1.1 认证前提：使用者 OA SSO Cookie

HRClaw 接口依赖**当前使用者本人**在 OA / SSO 域下的登录态。发送邮件或企微 Tips 时，必须使用浏览器自动化方案在本机浏览器会话中读取并携带**使用者自己的 OA SSO Cookie**，不得使用开发者、机器人、共享账号或硬编码 Cookie。

**执行要求**：

1. 使用浏览器自动化打开 `https://ntsgw.woa.com` 或 HRClaw 接口同域页面，确认当前使用者已完成 OA/SSO 登录。
2. 从浏览器上下文读取该域下的 SSO Cookie，并仅用于本次 `fetch` / XHR 请求的同域认证。
3. Cookie 只允许在浏览器自动化会话内使用；不得在对话、日志、Excel、Markdown、代码文件中展示、复制、持久化或转发。
4. 若浏览器中没有使用者登录态，先提示使用者在浏览器完成 OA 登录；不得降级为后台直连、固定 Token、他人 Cookie 或伪造认证。
5. 调用完成后只展示接口业务结果（如 `msgId` / `message`），不得回显 Cookie、请求头或完整认证信息。

### 1.2 企微 Tips

`POST https://ntsgw.woa.com/api/sso/message-channel-service/hrclaw/v1/workchat-tips/send`

请求体：

```json
{
  "receivers": ["员工英文名"],
  "title": "标题，≤100字符",
  "content": "正文，≤2000字符"
}
```

### 1.3 邮件

`POST https://ntsgw.woa.com/api/sso/message-channel-service/hrclaw/v1/mail/send`

请求体：

```json
{
  "receivers": ["员工英文名"],
  "cc": [],
  "bcc": [],
  "subject": "主题，≤200字符",
  "content": "HTML正文，≤500KB"
}
```

## 2. 收件人规则

- 收件人只能是员工英文名 loginName，例如 `zhangsan`。
- 不接受邮箱，不接受中文名；出现 `@` 或不符合 `^[A-Za-z][A-Za-z0-9_\-]{1,30}$` 时，先让用户修正。
- 默认收件人：
  - 通知导师：使用 `tutor_name_en`
  - 通知上级：使用 `lead_name_en`
- 允许招聘经理在发送前修改发送对象。
- 企微 Tips 单次最多 100 人；邮件收件人 / 抄送 / 密送合计最多 200 人。

## 3. 保温通知模板（企微 Tips 与邮件保持一致）

### 3.1 单人通知模板

标题：

```text
[校招保温] {候选人姓名}同学保温信息同步
```

正文：

```text
你好，你已被指定为{候选人姓名}同学的{导师/直接上级}，请关注该同学签约后保温与入职前沟通。

一、同学基本信息
- 姓名：{候选人姓名}
- 员工子类型：{offer_staff_subtype_name，如"毕业生"/"应届实习生"/"日常实习生"；缺失时写"暂无"}
- 人选标签：{candidate_tag，如"⭐青云计划"/"⭐青云实习"/"⭐产品经理培训生"；普通人选写"普通"}
- 学校/学历：{最高学校}（{最高学历}）
- 专业：{专业}
- 岗位：{岗位}
- 工作地：{工作城市}
- 预计入职：{预计入职日期}（{入职倒计时/已入职/待定}）
- 当前保温阶段：{保温阶段}

二、真实简历链接
{真实 resume_link；若仍无法取得，写"暂无可用简历链接，请在招聘系统按姓名/简历ID检索"}

三、同学联系方式
请通过上方真实简历链接登录招聘系统查看联系方式。

四、招聘经理企微
{招聘经理中文名}（企微/英文名：{recruit_manager_en}）

五、你作为{导师/直接上级}的建议动作
{按"导师/上级"角色 + 当前保温阶段，从下方"角色标准动作"中挑选 2-3 条最贴合的动作列出，让对方清楚下一步要做什么}

{高潜人才（人选标签非"普通"）追加一句：该同学为高潜人选（{candidate_tag}），建议加强关注、在资源与发展规划上给予倾斜，必要时由更高级别管理者一同参与沟通}

建议你尽快完成首次沟通，了解同学近况、入职安排和潜在风险。如需更多信息，可通过上述企微联系招聘经理。
```

#### 角色标准动作（按角色 + 阶段挑选，嵌入"五、建议动作"）

> 依据《学生人才吸引保温全景》三方标准动作，按收件人角色与当前保温阶段精选 2-3 条，避免一次罗列全部。

**导师**：
1. 接到通知后 1 周内首次沟通，做自我介绍、建立联系；
2. 分享团队技术氛围与个人成长经历，建立专业认同；
3. 解答岗位 / 技术 / 团队疑问，适度分享行业动态与学习资料；
4. 入职前帮助做好技术与心理准备，降低入职焦虑；
5. 关注情绪变化，发现异常及时反馈招聘经理。

**直接上级**：
1. 接到通知后 2 周内沟通，欢迎加入团队；
2. 介绍团队业务方向、文化与工作模式；
3. 描绘岗位发展路径与成长空间，必要时分享团队成果增强吸引力；
4. 关注合理诉求，在职责范围内提供支持；
5. 入职前做好团队接纳准备，让同学感受到被重视。

**阶段裁剪建议**：签约初期重"首次建联 + 欢迎"；保温中期重"持续互动 + 答疑 + 资料同步"；入职前期重"入职准备 + 接纳 + 缓解焦虑"。

### 3.2 多人合并通知模板

当一次通知涉及 **2 名及以上** 同学时，使用表格合并展示。**必须为每位同学注明员工子类型**，以便导师/上级区分毕业生和不同类型实习生的保温重点。

标题：

```text
[校招保温] 您名下 {N} 位同学保温信息同步
```

正文：

```text
你好，你已被指定为以下 {N} 位同学的{导师/直接上级}，请关注这些同学签约后保温与入职前沟通。

一、同学基本信息

| 姓名 | 人选标签 | 员工子类型 | 学校/学历 | 专业 | 岗位 | 组织 | 工作地 | 预计入职 |
|---|---|---|---|---|---|---|---|---|
| {姓名} | {candidate_tag，高潜显示⭐青云计划/⭐青云实习/⭐产品经理培训生，普通显示—} | {offer_staff_subtype_name} | {最高学校}（{最高学历}） | {专业} | {岗位} | {组织} | {工作地} | {预计入职日期} |

二、真实简历链接
{逐人列出真实 resume_link；若仍有无法取得的，写"暂无可用简历链接，请在招聘系统按姓名/简历ID检索"}

三、同学联系方式
请通过上方真实简历链接登录招聘系统查看联系方式。

四、招聘经理企微
{招聘经理中文名}（企微/英文名：{recruit_manager_en}）

五、你作为{导师/直接上级}的建议动作
{按"导师/上级"角色 + 各同学当前保温阶段，从"角色标准动作"中精选 2-3 条通用动作列出}
{若名单中含高潜人才（人选标签非"—"），追加一句：其中 {高潜同学姓名} 为高潜人选，建议优先关注、资源倾斜，必要时由更高级别管理者参与沟通}

建议你尽快与这些同学建立联系，了解近况及入职安排。如需更多信息，可通过上述企微联系招聘经理。
```

**多人模板关键规则**：
- `offer_staff_subtype_name`（员工子类型）为必填列，不能省略；数据来自 `Report_School_Recruiti_Info_List` 的 `offer_staff_subtype_name` 字段
- 「人选标签」列由派生 `candidate_tag` 生成（口径见 `sql-templates.md`）：高潜显示 ⭐青云计划 / ⭐青云实习 / ⭐产品经理培训生，普通显示"—"；含高潜同学时须在"五、建议动作"中点名提示重点关注
- 若某位同学的员工子类型缺失，写"暂无"而非留空，事后通过 zhaopin-mcp / recruit-mcp 补查
- 邮件版本将表格转为 HTML `<table>` + 内联样式（蓝色表头）；企微 Tips 保留 Markdown 表格
- 邮件版本中简历链接转可点击 `<a href="...">点击查看</a>`

### 3.3 隐私边界

- 不要在对话、企微 Tips 或邮件模板中直接抓取或展示候选人手机号、邮箱、微信号。
- 联系方式统一用兜底话术："请通过上方真实简历链接登录招聘系统查看联系方式"。
- 如果用户要求自动抓取联系方式，说明该能力暂不启用，并引导通过招聘系统详情页查看。

### 3.4 自定义模板

当默认模板（3.1 单人 / 3.2 多人）无法满足部门个性化需求时，招聘经理可以创建和维护自定义通知模板。自定义模板以 Markdown 文件形式存放，在场景 F 执行时由 AI 引导选择。

#### 3.4.1 存放路径与命名

```
config/custom-notify-templates/
  ├── {模板名}.md          # 如 pcg-tutor-notify.md
  └── {模板名}.md
```

- **目录**：`config/custom-notify-templates/`（skill 安装时自带，空目录有 `.gitkeep` 占位）
- **命名规范**：`{组织或用途}-{通知对象}.md`，全小写，连字符分隔，如 `pcg-tutor-notify.md`、`ieg-leader-multi.md`
- **一个文件 = 一个模板**，不允许多模板共存于同一文件

#### 3.4.2 模板格式规范

每个自定义模板文件必须包含两部分：**YAML front-matter（元信息）** + **Markdown 正文（模板内容）**。

**front-matter 必填字段**：

```yaml
---
name: "PCG 导师通知模板"           # 模板显示名称（中文可）
scene: tutor                        # tutor(导师) / leader(上级) / both
template_type: single               # single(单人) / multi(多人合并)
author: "acescwu"                   # 创建者 loginName
created_at: "2026-06-24"            # 创建日期
updated_at: "2026-06-24"            # 最后更新日期
description: "PCG 部门导师专用，增加了技术栈匹配提示" # 简短说明
---
```

**正文必填区块**（5 个，缺一不可，顺序可调整）：

| 区块 | 说明 | 必填占位变量 |
|---|---|---|
| ① 同学基本信息 | 姓名、员工子类型、学校/学历、岗位等 | `{候选人姓名}`、`{offer_staff_subtype_name}` |
| ② 真实简历链接 | 候选人简历 URL | `{resume_link}` |
| ③ 联系方式说明 | 隐私兜底话术 | 固定文案，不可省略 |
| ④ 招聘经理企微 | 招聘经理联系方式 | `{招聘经理中文名}`、`{recruit_manager_en}` |
| ⑤ 建议动作 | 导师/上级需要做的事 | `{角色标准动作}` 或自定义 |

**可选区块**：组织信息、技术栈匹配、团队介绍、入职准备清单、高潜提示等，由招聘经理自由扩展。

#### 3.4.3 占位变量表

自定义模板中使用 `{变量名}` 格式的占位符，AI 在生成通知时自动替换。变量名与默认模板保持一致：

| 变量名 | 含义 | 数据来源 |
|---|---|---|
| `{候选人姓名}` | 候选人中文名 | 查询结果 |
| `{offer_staff_subtype_name}` | 员工子类型（毕业生/应届实习生/日常实习生） | `Report_School_Recruiti_Info_List` |
| `{candidate_tag}` | 人选标签（⭐青云计划/⭐青云实习/⭐产品经理培训生/普通） | 派生字段 |
| `{最高学校}` | 最高学历毕业院校 | 查询结果 |
| `{最高学历}` | 最高学历层次 | 查询结果 |
| `{专业}` | 专业 | 查询结果 |
| `{岗位}` | 应聘岗位 | 查询结果 |
| `{工作城市}` | 工作地城市 | 查询结果 |
| `{预计入职日期}` | 预计入职时间 | 查询结果 |
| `{入职倒计时}` | 入职倒计时/已入职/待定 | 派生字段 |
| `{保温阶段}` | 当前保温阶段 | 派生字段 |
| `{resume_link}` | 真实简历链接 | `T_LINK` 查询 / zhaopin-mcp 补查 |
| `{招聘经理中文名}` | 招聘经理中文名 | `get_current_user` |
| `{recruit_manager_en}` | 招聘经理英文名 | `get_current_user` |
| `{角色标准动作}` | 按角色+阶段精选 2-3 条动作 | 本文 3.1 节角色标准动作池 |
| `{组织}` | 候选人所属组织 | 查询结果 |
| `{导师/直接上级}` | 收件人角色 | 用户选择 |

> 未列出的自定义变量，AI 会尝试从查询结果中匹配同名字段；匹配不到时保留原占位符并提示用户。

#### 3.4.4 校验规则

AI 在保存自定义模板前执行以下校验：

| 检查项 | 规则 | 处理方式 |
|---|---|---|
| front-matter 完整性 | `name`/`scene`/`template_type`/`author` 必填 | 缺失则提示补充，不保存 |
| 必填区块齐全 | 5 个必填区块全部出现 | 缺失则警告并列出缺失区块，允许用户确认后强制保存 |
| 占位变量有效 | 所有 `{xxx}` 变量在变量表或查询字段中可匹配 | 未知变量警告，不阻断 |
| 隐私收口 | 正文不得包含手机号/邮箱/微信号占位 | 发现则拒绝保存，提示使用固定兜底话术 |
| 高潜提示 | 建议包含 `{candidate_tag}` 相关占位 | 缺失则提醒，不阻断 |

#### 3.4.5 示例模板骨架

```markdown
---
name: "PCG 导师通知模板（含技术栈匹配）"
scene: tutor
template_type: single
author: "acescwu"
created_at: "2026-06-24"
updated_at: "2026-06-24"
description: "PCG 部门导师专用，在默认模板基础上增加技术栈匹配和团队项目介绍"
---

标题：[校招保温] {候选人姓名}同学保温信息同步

正文：

你好，你已被指定为{候选人姓名}同学的导师，请关注该同学签约后保温与入职前沟通。

一、同学基本信息
- 姓名：{候选人姓名}
- 员工子类型：{offer_staff_subtype_name}
- 人选标签：{candidate_tag}
- 学校/学历：{最高学校}（{最高学历}）
- 专业：{专业}
- 岗位：{岗位}
- 工作地：{工作城市}
- 预计入职：{预计入职日期}（{入职倒计时}）
- 当前保温阶段：{保温阶段}

二、真实简历链接
{resume_link}

三、同学联系方式
请通过上方真实简历链接登录招聘系统查看联系方式。

四、招聘经理企微
{招聘经理中文名}（企微/英文名：{recruit_manager_en}）

五、你作为导师的建议动作
{角色标准动作}

六、团队技术栈匹配（PCG 专用）
请根据同学简历中的技术背景，提前了解其技术栈与团队项目的匹配度，入职第一周安排一次技术交流。
```

#### 3.4.6 自定义模板生命周期

| 操作 | 触发方式 | 处理逻辑 |
|---|---|---|
| **新建** | 用户说"新建模板"/"上传模板" | 引导用户提供模板内容（粘贴 Markdown 或口述结构），校验后保存为 `.md` 文件 |
| **查看** | 用户说"看看我有哪些模板"/"列出模板" | 扫描 `config/custom-notify-templates/` 目录，列出 front-matter 中的 `name` 和 `description` |
| **更新** | 用户说"修改 xxx 模板" | 读取原模板，引导用户修改，校验后覆盖保存 |
| **删除** | 用户说"删除 xxx 模板" | 二次确认后删除文件 |
| **使用** | 场景 F 执行时引导选择 | 读取模板正文，替换占位变量后作为通知正文 |

### 3.5 模板选择引导话术

在场景 F 执行流程中，AI 读取通知规范后、生成模板前，使用以下话术引导用户选择模板：

#### 3.5.1 标准引导（有自定义模板时）

```text
📬 通知模板选择

本次通知可以使用以下模板：

🟦 默认模板（推荐）
   标准保温通知，含基本信息+简历链接+建议动作，适用于大多数场景

🟩 自定义模板（你已保存 N 个）
   1. {模板1 name} — {模板1 description}
   2. {模板2 name} — {模板2 description}
   ...

请回复：
- "默认" 或序号选择已有模板
- "新建" 创建新的自定义模板
- "管理" 查看/修改/删除已有模板
```

#### 3.5.2 标准引导（无自定义模板时）

```text
📬 通知模板选择

当前使用默认模板（标准保温通知）。

如果你部门有特殊要求，可以创建自定义模板（Markdown 格式），后续使用时可直接选择。

请回复：
- "默认" 继续使用默认模板（直接回车也是默认）
- "新建" 开始创建自定义模板
```

#### 3.5.3 新建模板引导

```text
📝 创建自定义模板

你可以通过以下方式提供模板内容：

方式一：直接粘贴 Markdown
  把你写好的模板内容粘贴到对话中，我会校验格式后保存。
  格式要求：开头是 YAML front-matter（--- 包裹），后面是模板正文。
  可以参考默认模板的结构。

方式二：口述结构，我来帮你写
  告诉我你想包含哪些区块、有什么特殊要求，我帮你生成模板草稿。

请选择方式，或直接粘贴模板内容。
```

#### 3.5.4 模板保存后确认

```text
✅ 模板已保存

- 文件：config/custom-notify-templates/{filename}.md
- 名称：{name}
- 适用场景：{scene}
- 模板类型：{template_type}
- 创建者：{author}

本次通知将使用该模板。如需修改，回复"管理"。
```

## 4. 发送前检查

### 4.1 真实简历链接检查

发送前必须确认模板中已带入同学的**真实 `resume_link`**：

- 优先使用 `T_LINK` 查询中 `lastest_flow_flag_name = '是'` 的 `resume_link`
- 若 `resume_link` 为空但 `offer_link` 可用，仍需优先补查简历链接；不能只放录用链接替代"真实简历链接"
- 若 hr-ai-data 链接为空或脱敏，使用 zhaopin-mcp / `recruit-mcp` 补查当前最新简历详情或流程详情中的简历 URL
- 若最终仍无真实简历链接，正文必须明确写"暂无可用简历链接，请在招聘系统按姓名/简历ID检索"

### 4.2 发送二次确认

发送前必须二次确认：

```text
请二次确认是否发送通知：

通知方式：企微 Tips / 邮件
通知类型：导师 / 直接上级
发送对象：{receivers}
消息标题：{title}

确认后将立即发送。
```

用户确认前不得调用接口。

## 5. 结果反馈

若浏览器自动化无法取得使用者本人 OA SSO Cookie，必须先提示使用者完成 OA/SSO 登录，不能继续发送，也不能要求用户复制 Cookie。

接口返回：

```json
{ "code": 0, "message": "success", "data": "msgId" }
```

- `code === 0`：必须展示 `msgId`，如 `邮件发送成功，消息 ID：...`。
- `code !== 0`：必须展示后端返回的 `message`，不要自造泛化错误。

常见错误建议：

| code | 建议 |
|---|---|
| 40001 | 检查收件人英文名、标题/正文长度、附件限制 |
| 40301 | 当前发送人被黑名单限制，联系管理员 |
| 40302 | 当前页面域名被黑名单限制，联系管理员 |
| 40901 | 触发频率限制，60 秒后重试 |
| 50000 | 服务端异常，稍后重试 |

## 6. 浏览器自动化发送 SOP（playwright-cli）

HRClaw 接口需要**使用者本人**的 OA/SSO 登录态 Cookie，全程由浏览器自动化控制在同一会话内完成，**不要求用户手动复制 Cookie**。macOS、Windows、Linux 均应优先走自动化链路；登录扫码属于自动化流程中的身份认证动作，不等同于手动发送。

### 6.1 工具准备（按系统选择）

**Windows PowerShell**：

```powershell
Get-Command playwright-cli -ErrorAction SilentlyContinue
# 或
where.exe playwright-cli
# 如未安装
npm install -g @playwright/cli@latest
```

**macOS / Linux Bash 或 Zsh**：

```bash
command -v playwright-cli || (npm bin -g 2>/dev/null | xargs -I{} test -x "{}/playwright-cli" && echo "$(npm bin -g)/playwright-cli")
# 如未安装
npm install -g @playwright/cli@latest
```

> 不要硬编码 `/opt/homebrew/bin/playwright-cli` 等本机路径。若全局 npm bin 不在 `PATH`，先把 `npm bin -g` 输出目录加入 `PATH`，再重试自动化。

### 6.2 浏览器选择

按本机可用浏览器选择 `--browser`，不要固定 Edge：

| 系统 | 推荐顺序 |
|---|---|
| Windows | `msedge` → `chrome` → `chromium` |
| macOS | `chrome` → `msedge` → `chromium` |
| Linux | `chromium` → `chrome` → `firefox` |

Linux 必须有可视化桌面与可用的 `DISPLAY` / Wayland 会话，否则无法完成 OA 登录交互。浏览器 channel 不存在时，切换下一个可用浏览器重试，不要直接回退手动 Console。

### 6.3 完整发送流程

#### Step 1：打开自动化浏览器并完成 OA 登录

```bash
# macOS 推荐
playwright-cli open https://ntsgw.woa.com --browser=chrome --persistent

# Windows 常用
playwright-cli open https://ntsgw.woa.com --browser=msedge --persistent

# Linux 常用
playwright-cli open https://ntsgw.woa.com --browser=chromium --persistent
```

#### Step 2：检查登录状态

```bash
playwright-cli snapshot --filename=hrclaw-login.yaml
```

`snapshot` 默认写入 `.playwright-cli/` 文件。读取方式：

```bash
cat .playwright-cli/hrclaw-login.yaml
```

判断规则：

- URL 仍为 `std.passport.woa.com/...signin.ashx`：进入 Step 3 登录
- URL 已为 `https://ntsgw.woa.com/...`：登录成功，进入 Step 4
- URL 不是 `ntsgw.woa.com`：先 `playwright-cli goto https://ntsgw.woa.com`，确保后续同源请求成立

#### Step 3：通过 OA 快速登录或扫码登录

快照中常见两种场景：

**场景 A**：检测到已登录账号（快照中有 `检测到当前已登录账号` + 英文名）：

```bash
# 点击“快速登录”按钮，ref 号按快照实际值替换
playwright-cli click e33
```

**场景 B**：未检测到已登录账号：

- 提示用户在**自动化打开的浏览器窗口**完成 OA 扫码 / 快速登录；
- 用户完成登录后，重新执行 Step 2 确认 URL 已回到 `ntsgw.woa.com`；
- 不要求用户打开 F12、粘贴 Console 代码或执行 Bookmarklet。

#### Step 4：在浏览器上下文中发送 HRClaw 请求

将 JS 写入系统临时目录，避免 skill 安装目录只读、路径含空格/中文或多会话覆盖。

**JS 示例（邮件发送）**：

```js
async page => {
  const mailBody = {
    receivers: ['acescwu'],
    cc: [],
    bcc: [],
    subject: '[校招保温] 您名下 4 位同学保温信息同步',
    content: '<p>你好，你已被指定为以下 4 位同学的导师：</p>...'
  };

  const response = await page.evaluate(async (body) => {
    if (location.origin !== 'https://ntsgw.woa.com') {
      return { code: -1, message: `当前页面不是 ntsgw.woa.com：${location.href}`, data: null };
    }
    const res = await fetch('/api/sso/message-channel-service/hrclaw/v1/mail/send', {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });
    return await res.json();
  }, mailBody);

  return JSON.stringify(response);
}
```

**Windows PowerShell 执行**：

```powershell
$tmp = Join-Path $env:TEMP ("hrclaw_send_{0}.js" -f ([DateTimeOffset]::Now.ToUnixTimeMilliseconds()))
Set-Content -Path $tmp -Encoding UTF8 -Value @'
async page => {
  // 将上方 JS 内容粘贴到这里
}
'@
$code = [System.IO.File]::ReadAllText($tmp, [System.Text.Encoding]::UTF8)
playwright-cli run-code $code
Remove-Item $tmp -Force
```

**macOS / Linux Bash 或 Zsh 执行**：

```bash
tmp_js="$(mktemp /tmp/hrclaw_send.XXXXXX.js)"
cat > "$tmp_js" <<'JS'
async page => {
  // 将上方 JS 内容粘贴到这里
}
JS
playwright-cli run-code "$(cat "$tmp_js")"
rm -f "$tmp_js"
```

**关键约束**：

- JS 代码中使用 `credentials: 'include'`，浏览器自动携带当前域下的 Cookie，**代码中不读取、不传递、不打印 Cookie**；
- 请求 URL 使用绝对路径 `/api/sso/...`，必须先确认页面 origin 为 `https://ntsgw.woa.com`；
- 成功后返回 `{ code: 0, message: "success", data: "msgId" }`，只展示业务结果。

#### Step 5：清理

```bash
playwright-cli close
```

### 6.4 企微 Tips 发送

与邮件发送流程相同，仅替换 JS 中的 fetch URL 和请求体：

```js
const tipsBody = {
  receivers: ['acescwu'],
  title: '[校招保温] 您名下 4 位同学保温信息同步',
  content: '你好，你已被指定为以下 4 位同学的导师：\n...'
};

const response = await page.evaluate(async (body) => {
  if (location.origin !== 'https://ntsgw.woa.com') {
    return { code: -1, message: `当前页面不是 ntsgw.woa.com：${location.href}`, data: null };
  }
  const res = await fetch('/api/sso/message-channel-service/hrclaw/v1/workchat-tips/send', {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  });
  return await res.json();
}, tipsBody);
```

### 6.5 异常处理与重试优先级

| 异常 | 处理方式 |
|---|---|
| `playwright-cli` 未安装 | 指导安装 `npm install -g @playwright/cli@latest`，安装后重试自动化 |
| `playwright-cli` 不在 `PATH` | macOS/Linux 用 `command -v` + `npm bin -g` 定位；Windows 用 `Get-Command` / `where.exe`，修复 `PATH` 后重试 |
| 浏览器 channel 不存在 | 按 6.2 推荐顺序切换 `--browser` 后重试 |
| Linux 无可视化桌面 | 提示需要可交互桌面环境；若当前机器无法启动浏览器，换到可启动浏览器的本机执行 |
| OA 登录页无法快速登录 | 提示用户在自动化浏览器窗口扫码 / 快速登录，完成后继续自动化 |
| Shell 转义或命令不兼容 | 切换到对应系统的 PowerShell 或 Bash/Zsh 命令片段，不要直接回退 Console |
| 当前页面不是 `ntsgw.woa.com` | `playwright-cli goto https://ntsgw.woa.com` 后重新检查登录态 |
| OA 登录成功但接口返回 `code !== 0` | 展示后端 `message`，按第 5 节常见错误建议处理 |
| fetch 报网络错误 / CORS | 确认当前页面 origin 为 `https://ntsgw.woa.com`，同源请求不应触发 CORS |
| 用户拒绝浏览器自动化，或本机修复后仍无法启动任何自动化浏览器 | 才进入第 7 节最后兜底；不得把 macOS 命令差异、Edge 不存在、扫码登录视为手动发送理由 |

### 6.6 安全红线

1. **Cookie 不出浏览器**：Cookie 仅在 `page.evaluate` 内的 `fetch({ credentials: 'include' })` 中由浏览器自动携带，不通过 `document.cookie` 或其他方式读取。
2. **临时文件即用即删**：JS 临时文件放在系统临时目录，文件名唯一，请求完成后立即删除。
3. **不展示认证信息**：对话输出只展示 `code` / `msgId` / `message`，不展示 Cookie、Token、请求头。
4. **不做持久化**：不将 Cookie 写入 localStorage、文件系统、环境变量或任何持久化存储。

---

## 7. 页面 / 手动备用方案

手动方案只作为**最后兜底**：用户明确拒绝浏览器自动化，或本机经过安装、PATH 修复、浏览器切换后仍无法启动任何自动化浏览器时，才提供可复制的浏览器 Console 代码。macOS 命令差异、Edge 不存在、需要在自动化浏览器窗口扫码登录，都不能作为直接回退手动方案的理由。

如必须进入手动兜底，要求用户在已登录 OA 的可视化浏览器页面执行，且仍禁止复制 Cookie / Token / 请求头：

- macOS Chrome：`Option + Command + I` 打开开发者工具；
- Windows / Linux Chrome：`F12` 或 `Ctrl + Shift + I` 打开开发者工具；
- 若开发者工具被禁用，可考虑 Bookmarklet 兜底，但必须明确这是应急路径，不作为标准流程。

手动方案中邮件 HTML 的 `<a href="...">` 链接和企微 Tips 文本保持与自动化方案一致。

页面集成建议：

- 在候选人卡片或详情页拆成两个入口：`对导师`、`对上级`
- 弹窗内提供通道选择：`企微 Tips` / `邮件`
- 发送对象输入框默认带入对应责任人英文名，允许招聘经理修改
- 发送前展示真实简历链接、员工子类型、认证方式和隐私边界，等待招聘经理确认
