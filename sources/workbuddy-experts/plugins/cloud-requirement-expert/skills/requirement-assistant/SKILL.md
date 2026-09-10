---
name: requirement-assistant
description: "Use this skill when users need to generate, preview, revise, create, enrich, update, or split TAPD requirements through the requirement-assistant MCP Server."
---

# Requirement Assistant

## 背景

本技能面向 TAPD 需求生成、补全、写回、AI读层生成和需求拆分场景，将 `requirement-assistant` MCP Server 作为真实执行后端，Skill 本身只负责识别意图、选择工具、整理返回结果和控制高风险动作确认边界。

将本技能作为 `requirement-assistant` MCP Server 的**薄编排层**使用。

只做以下事情：

- 识别当前属于"新建需求"、"补全已有需求"、"生成 AI读层"、"更新已有需求"还是"拆分需求"
- 在真正缺信息时，优先利用 MCP 已返回的结构化提示补问
- 优先调用 `public` 总入口；仅在必要时调用 `expert` 工具
- 将 MCP 返回的 JSON 结果整理成可读摘要与下一步建议
- 避免把"PRD 正文结构""TAPD 模板字段""人工兜底草案"混成一件事

## 何时使用

在以下场景触发：

- 需要根据一句话想法、会议纪要、聊天记录、草稿生成正式需求
- 需要先预览需求草案，再决定是否创建 TAPD 需求
- 预览后不满意，需要改写 PRD 草稿后再创建
- 需要补全已有 TAPD 需求的背景、目标、范围、验收标准、风险、竞品等内容
- 补全预览后不满意，需要改写补全草稿后再写回
- 需要为已有 PRD 生成结构化的 AI读层（AI可读的需求摘要）
- 需要修改已创建需求的字段（标题、描述、状态、优先级等）
- 需要查看需求模板、模板字段、补全模块等专家级辅助信息
- 需要将复杂需求拆分为可独立交付的子需求（子Story）

## 前置条件

仅在 `requirement-assistant` MCP Server 已可用时使用本技能。

### MCP Server 未连接时的处理

若当前环境缺少该 MCP Server，不要假装已经查询到 TAPD、已经完成预览、已经成功建单或写回。同时，不要仅仅告知"MCP 不可用"就结束——**必须主动给出用户可执行的操作指引**：

**向用户输出以下内容：**

> ⚠️ `requirement-assistant` MCP Server 未连接，无法执行 TAPD 操作。
>
> 请重新召唤本专家，WorkBuddy 会弹出连接引导卡片，通过太湖完成授权。
>
> 如果你只是想先看一版需求草案，我也可以整理一份**人工草案**（明确标注非 MCP 生成），等 MCP 就绪后再走正式流程。

### MCP 已连接但返回 401/403 时的处理

向用户输出以下内容：

> ⚠️ 认证失败，太湖授权可能已过期。请重新连接 MCP Server 刷新授权。
>
> 如果提供过个人令牌，也请检查令牌是否仍然有效。

## 输入约束

- 用户请求应与 TAPD 需求生成、需求补全、需求更新、AI读层生成或需求拆分直接相关。
- 新建需求至少需要产品 / 项目、需求背景或一句话想法，并确认用户目标是预览草案还是最终建单。
- 补全、更新或拆分已有需求时，应尽量获取 `story_id`，并补充 `product` 或 `workspace_id`。
- 涉及 create、apply、update 或批量创建子需求时，必须先获得用户明确确认，不能自动写回 TAPD。
- 若 MCP 返回 `input_required`、`available_products` 或 `prompt_hint`，应优先使用返回的结构化提示向用户补问信息。

## 能力边界

先按 `references/capability-matrix.md` 理解 Server 的真实能力，再开始编排。

遵循以下硬规则：

1. 主流程优先只走三个 `public` 总入口：
   - `start_new_requirement`（支持 preview / status / revise / create）
   - `enrich_existing_requirement`（支持 preview / status / revise / apply）
   - `generate_ai_read_layer`
2. `expert` 工具只用于"选模板、看模板、查必填字段、看需求详情、选补全模块、做补全预览实验、更新已有需求字段"
3. 不主动调用 `internal` 工具
4. 不把"调用过 TAPD 模板"直接等同于"PRD 正文一定按模板结构生成"
5. 不在 `preview` 仍为 `running` 时，擅自把人工整理草案说成 MCP 预览结果
6. 产品发现不再使用独立的 `list_products` 工具（已移除），而是利用 public 工具返回的 `input_required` / `available_products` / `prompt_hint` 结构化提示

## 关键认知：不要混淆两种模板

必须区分以下两件事：

### 1. PRD 正文结构

这是预览结果里的 `prd_content` 长什么样。

- 若在 `preview` 前显式传入 `template_id` 或 `template_content`，PRD 正文可能按模板结构生成
- 若没有显式传入模板信息，PRD 正文可能退回通用结构

### 2. TAPD 建单模板

这是创建需求时的字段与必填项约束。

- `template_id` 会影响 TAPD 需求模板、必填字段、字段校验
- 但**不能倒推出**预览正文一定已经按模板结构生成

因此：

- 只有在**明确选定模板并把 `template_id` / `template_content` 带入 preview** 后，才可说"本次预览按模板结构生成"
- 如果没有做过模板选择，只能说"生成了需求草案预览"，不能说"按模板生成"

## 关键认知：三种"更新"场景的区别

必须区分以下三种更新场景，不要混用：

| 场景 | 工具 | 适用阶段 |
|------|------|----------|
| 预览草稿改写（新建） | `start_new_requirement(action=revise)` | 尚未创建 TAPD 需求 |
| 补全草稿改写 | `enrich_existing_requirement(action=revise)` | 已有 TAPD 需求，补全预览后改写 |
| 补全写回 | `enrich_existing_requirement(action=apply)` | 已有 TAPD 需求，写回补全模块 |
| 通用字段编辑 | `update_tapd_story` | 已有 TAPD 需求，修改标题/状态/优先级等 |

## 使用示例

典型调用：用户提出新建、补全、更新、生成 AI读层或拆分 TAPD 需求时，先判断具体场景和必要上下文，再优先调用 `public` 总入口完成预览、状态查询、改写、创建或写回，最后按输出格式给出阶段、结果、风险和下一步建议。

### 示例 1：新建需求

用户输入：

```text
帮我基于这个内容生成一个 TSF 的 TAPD 需求
```

执行方式：调用 `start_new_requirement(action=preview)` 异步生成，完成后返回 `prd_title`、`prd_content`、缺失必填字段和下一步建议。

### 示例 2：补全已有需求

用户输入：

```text
帮我补全这个需求 1234567890 的背景、验收标准和风险
```

执行方式：确认 `story_id`、产品或 `workspace_id` 后调用 `enrich_existing_requirement(action=preview)`；只有用户明确确认写回时，才继续调用 `action=apply`。

## 工作流 1：新建需求

### 步骤 0：确认产品名称

⛔ **收到用户需求后的第一件事：检查用户是否已指定产品。此步不可跳过。**

- 已指定产品 → 进入步骤 1
- **未指定产品 → 立即用 `ask_followup_question` 弹窗让用户选择，等待回复后再进入步骤 1。不允许跳过此步直接调 MCP、或自行分析需求意图。**

**`available_products` 选项生成规则：**
- 只列**对外售卖的腾讯云产品**（如对象存储 COS、云服务器 CVM、微服务平台 TSF 等），基于 LLM 对云产品的知识生成
- ⛔ **禁止列入**：TAPD、DevOps 工具、需求管理系统、评测工具、评审任务、运营后台、文件服务、代码评审工具、部门/组织名称、`*_DevOps_Helper` 等任何非对外售卖的系统或工具
- 必须包含「其他云产品（请直接输入名称）」兜底选项

### 步骤 1：调 MCP 启动预览（必须）

收集产品名 + 用户需求描述后，**强制调 `start_new_requirement(action=preview)`**。

⛔ **即使用户说"创建"或"建单"，也必须先走 `action=preview` 生成预览。** `action=create` 只在步骤 8 用户看完预览并明确确认后才使用。

不需要先问目标（预览/创建）和模板。

MCP 会返回以下几种情况：

**情况 A：产品已在数据库且有 workspace_id 映射** → MCP 启动 preview（增强模式：含知识库检索、功能点提取、竞品分析），返回 task_id → 正常走后续步骤。

**情况 B：产品不在数据库，需要 workspace_id** → MCP 返回 `input_required` 带 `action_required: "provide_workspace_id"`。告知用户："产品名未在系统中找到，请提供该产品的项目 ID（在项目地址栏里能看到的一串数字）。提供后即可正常生成需求。"

**情况 C：MCP 确认失败** → 告知用户并终止本次操作。

### 步骤 2：产品上下文就绪后，再问目标和模板

MCP 返回 product_key 和 workspace_id 都已就绪后，再确认：

1. 用户目标是"先看草案"还是"最终建单"（默认先看草案）
2. 用户是否明确要求"按某个模板"

### 步骤 3：处理模板决策

按以下规则决策：

- 若用户**明确要求模板**、强调字段对齐、强调按项目既有结构输出：
  - 先调用 `get_story_template_list`
  - 必要时调用 `get_story_template_detail`
  - 确认选中的 `template_id` 后，再启动 preview
- 若用户没有要求模板，只想先看一版需求草案：
  - 可直接 preview
  - 但不要暗示"这版一定按 TAPD 模板结构输出"

当模板不明确时，不要自行臆测默认模板。

### 步骤 4：启动 preview（如尚未启动）

如果步骤 1 中 MCP 已成功启动 preview 并返回了 task_id（说明产品在数据库中有映射），直接跳到步骤 5。

如果步骤 1 中被 workspace_id 阻塞了，用户补齐后在此启动：

调用：

- `start_new_requirement(action=preview)`

若已选模板，则在 preview 阶段一并传入：

- `template_id`
- 必要时 `template_content`
- 可选 `workitem_type_id`

记录返回的 `task_id` / `preview_task_id`。

### 步骤 5：查询 preview 状态

调用：

- `start_new_requirement(action=status, preview_task_id=...)`

当 `status` 仍为 `running` 时：

- 只做一句简短进度同步
- 保留 `preview_task_id`
- 继续查询闭环
- 不输出人工草案冒充 MCP 结果

只有在以下情况之一，才允许改为输出人工草案：

- MCP 明确失败
- MCP 当前不可用
- 用户明确表示"不等了，先给我一版人工草案"

且必须明确标注：**该草案不是 MCP 预览结果。**

### 步骤 6：处理 preview 完成结果

新建需求预览完成后，重点读取这些字段：

- `prd_title`
- `prd_content`
- `template_id`
- `required_fields`
- `missing_required_fields`
- `suggested_create_payload`
- `draft_state`（如果存在，说明已有改写历史）
- `warnings`

对外返回时：

1. **将完整 PRD 内容保存为 Markdown 文件**并展示给用户：
   - 文件名格式：`prd_{标题简写}.md`（用中文或英文均可）
   - 文件内容：以 `# {prd_title}` 为标题，正文使用 MCP 返回的 `prd_content` 原文
   - 保存后告知用户文件路径
2. 附带一段**简短摘要**（3-5 行即可），说明核心功能点数量、必填字段状态
3. 给出下一步建议（改写 / 创建）

**不要自行总结或压缩 PRD 正文内容**，用户需要看到完整的预览结果。

### 步骤 7：可选 — 改写预览草稿

若用户对预览结果不满意，可在不重新生成的前提下改写草稿：

调用：

- `start_new_requirement(action=revise, preview_task_id=...)`

改写方式：

- 传 `edit_instruction`：自然语言改写指令（如"增加安全设计章节"）
- 传 `edited_prd_content`：直接覆盖正文
- 可选 `edited_title` 修改标题

改写基线：

- `base=current`（默认）：基于当前草稿
- `base=original`：基于初始预览草稿（丢弃中间改写）

改写后草稿仍可继续 revise 或执行 create。注意 `draft_state` 中的 `revision_count`。

### 步骤 8：创建 TAPD 需求

仅当用户明确要求建单时，才继续。

**创建需求必须具有 workspace_id**。create 是对项目的真实写入操作，没有 workspace_id 无法确定创建到哪个项目。

如果创建工作流到达此步骤时仍没有 workspace_id：
1. 明确告知用户：
   > "创建需求需要知道目标项目，请提供 xx 产品的项目 ID。"
2. 用户补齐后，确认项目名称再创建。

**创建前确认目标项目**：

- 如果 workspace_id 是**用户最初显式提供**的 → 无需额外确认，直接创建
- 如果 workspace_id 是**通过产品名自动解析**的（用户只说了产品名） → **先展示给用户**：
  > 将创建到项目 **XXX**（workspace_id: xxx），确认吗？
  
  用户确认后再调用 create。

调用：

- `start_new_requirement(action=create, preview_task_id=...)` —
  若需创建到**与 preview 时不同的项目**，额外传入新的 `workspace_id` 即可覆盖预览时的绑定，**无需重新 preview**。

**若返回 `stage: "need_tapd_token"`**：

> **这是什么意思？** 操作需要提供个人访问令牌（Token），配置到连接器中。只需配置一次，以后永久生效。

📎 **详细处理流程见独立文档：[`references/token-setup-guide.md`](references/token-setup-guide.md)**

核心决策逻辑摘要如下（完整步骤、配置指引、检查清单均在外部文档）：

1. 使用 `ask_followup_question` 弹出三个选项：
   - 「我已有令牌，直接粘贴给你」→ 接收用户的 Token，协助写入连接器配置后重试
   - 「我还不知道怎么获取令牌」→ 提供令牌页面链接 + 获取步骤
   - 「跳过，暂不配置」→ 终止当前操作

2. **处理原则**：
   - 用户主动发送 Token 时，引导用户在连接器编辑器中添加 headers 配置：
     ```json
     "headers": {
       "X-Tapd-Access-Token": "用户提供的令牌"
     }
     ```
   - 写入完成后立即重试原来的工具调用
   - 写入后建议用户后续通过设置界面重新配一个新令牌（可选，非强制）

若存在 `missing_required_fields`：

- 先调用 `get_required_fields`
- 将字段含义、候选值翻译成人话
- 引导用户一次性补齐 `required_field_values` / `fields` / `custom_fields`
- 再执行 create

若用户希望同时插入本地截图/图片：

1. 确认 `workspace_id`（从用户提供的 TAPD 链接中提取，或引导用户从项目地址栏 URL 获取）
2. 确认图片文件的本地路径
3. 通过 `execute_command` 调用上传脚本（Token 优先通过 `--tapd-access-token` 传入，即用户在 need_tapd_token 流程中提供的令牌）：

   ```bash
   python skills/requirement-assistant/scripts/upload_local_images.py --workspace_id {workspace_id} --file /path/to/screenshot.png --tapd-access-token {token}
   ```
   > 脚本也支持 `TAPD_ACCESS_TOKEN` 环境变量作为后备方案。

4. 解析命令输出的 JSON，提取 `image_html_codes`
5. 在 `action=create` 时传入 `image_html_codes` 参数

## 工作流 2：补全已有需求

### 步骤 1：确认基础信息

至少确认：

- `story_id`
- `product` 或 `workspace_id`
- 用户是只看建议，还是希望最终写回 TAPD

### 步骤 2：必要时先看需求详情

当需要理解当前需求现状、判断是否已经补全过、查看描述中图片、或先做人工审阅时，优先调用：

- `get_story_detail`

尤其适用于：

- 用户只给了 `story_id`
- 需要先看原始描述再决定补哪些模块
- 需要分析描述中的截图内容

### 步骤 3：处理补全模块

- 若用户想指定补全范围，调用 `get_enrichment_modules`
- 若用户没有指定模块，可走默认模块

### 步骤 4：预览补全结果

默认优先走 `public` 总入口：

- `enrich_existing_requirement(action=preview)`

仅在需要直接拿到补全实验结果、明确比较模块输出、或调试补全内容时，才调用：

- `preview_enrichment`

### 步骤 5：处理补全结果

重点关注：

- `story_title`
- `already_enriched`
- `preview_generated`
- `modules`
- `generated_modules`
- `enrichment`
- `enriched_html`

当 `already_enriched=true` 或 `preview_generated=false` 时，不要假装拿到了新的补全内容。

### 步骤 6：可选 — 改写补全草稿

若用户对补全预览结果不满意，可在不重新生成的前提下改写草稿：

调用：

- `enrich_existing_requirement(action=revise, preview_task_id=...)`

改写方式：

- 传 `edit_instruction`：自然语言改写指令（如"补充更多竞品细节"）
- 传 `edited_enriched_html`：直接覆盖补全 HTML

改写基线：

- `base=current`（默认）：基于当前补全草稿
- `base=original`：基于初始补全预览草稿（丢弃中间改写）

改写后草稿仍可继续 revise 或执行 apply。注意 `draft_state` 中的 `revision_count`。

### 步骤 7：写回 TAPD

仅在用户明确要求写回时，才继续。写回前展示目标需求信息：

> 将写回到需求 **{{story_title}}**（ID: {{story_id}}），所属项目 workspace_id: {{workspace_id}}，确认吗？

用户确认后调用：

- `enrich_existing_requirement(action=apply, preview_task_id=...)`

**若返回 `stage: "need_tapd_token"`**：

> **这是什么意思？** 操作需要提供个人访问令牌（Token），配置到连接器中。只需配置一次，以后永久生效。

📎 **详细处理流程见独立文档：[`references/token-setup-guide.md`](references/token-setup-guide.md)**

核心决策逻辑摘要如下（完整步骤、配置指引、检查清单均在外部文档）：

1. 使用 `ask_followup_question` 弹出三个选项：
   - 「我已有令牌，直接粘贴给你」→ 接收用户的 Token，协助写入连接器配置后重试
   - 「我还不知道怎么获取令牌」→ 提供令牌页面链接 + 获取步骤
   - 「跳过，暂不配置」→ 终止当前操作

2. **处理原则**：
   - 用户主动发送 Token 时，引导用户在连接器编辑器中添加 headers 配置：
     ```json
     "headers": {
       "X-Tapd-Access-Token": "用户提供的令牌"
     }
     ```
   - 写入完成后立即重试原来的工具调用
   - 写入后建议用户后续通过设置界面重新配一个新令牌（可选，非强制）

不要在未确认的情况下默认写回。

## 工作流 3：生成 AI读层

### 步骤 1：确认 PRD 正文来源

- 来自新建需求预览结果（`prd_content`）
- 来自已有需求详情（`get_story_detail` 返回的 `description_markdown`）
- 用户直接粘贴

### 步骤 2：调用生成

- `generate_ai_read_layer(prd_content=..., product=..., title=..., source=...)`

`source` 取值：`new_requirement_preview` / `tapd_story` / `pasted_prd`

### 步骤 3：处理结果

- 成功时读取 `ai_read_layer_markdown`
- AI读层只生成预览，不写回 TAPD
- 若需写回，拼接内容后调用 `update_tapd_story(story_id=..., description=...)`

## 工作流 4：更新已有需求

### 步骤 1：确认更新内容

用户需要修改已创建需求的字段（标题、描述、状态、优先级、负责人、自定义字段等）。

### 步骤 2：调用更新

- `update_tapd_story(story_id=..., ...)`

可传入字段：`title`、`description`（支持 Markdown）、`priority`、`owner`、`developer`、`status` / `v_status`、`fields`、`custom_fields`、`image_html_codes`

### 插入图片

若用户希望在需求描述中插入本地图片：

1. 确认 `workspace_id`（从用户提供的 TAPD 链接中提取）
2. 确认图片文件的本地路径
3. 通过 `execute_command` 调用上传脚本（Token 优先通过 `--tapd-access-token` 传入）：

   ```bash
   python skills/requirement-assistant/scripts/upload_local_images.py --workspace_id {workspace_id} --file /path/to/screenshot.png --tapd-access-token {token}
   ```
4. 解析 JSON 输出，提取 `image_html_codes`
5. 传给 `update_tapd_story`，若同时传了 `description`，图片追加到 description 后面；若没传 description，会先获取需求当前描述再追加

### 步骤 3：处理结果

- 成功时确认 `submitted_fields`
- 失败时查看 `error`

注意：这是通用字段编辑，与补全写回（`enrich_existing_requirement(action=apply)`）不同。

## 工作流 5：需求拆分

将复杂需求拆分为可独立交付的子需求（子 Story）。

**拆分框架详见 `references/requirement-split-framework.md`**，本节只编排步骤。

### 步骤 1：获取需求内容

调用：

- `get_story_detail(story_id=..., workspace_id=...)`

获取需求标题、描述、优先级等完整信息。

### 步骤 2：判断是否需要拆分

按 `references/requirement-split-framework.md` 第一节判断，不需要拆分则输出不拆分结论，需要则继续。

### 步骤 3：执行拆分分析

按框架执行：

1. **选主切维度**（三选一）：业务流程 / 功能模块 / 架构技术栈
2. **辅助维度调整**（按需叠加）：风险等级 / 交付优先级 / 工作量规模
3. **领域维度**（如触发）：数据流 / 合规域 / 模型生命周期
4. **INVEST 质量门禁检验**：逐条检验，不通过则回溯调整

### 步骤 4：生成拆分报告

按 `references/requirement-split-framework.md` 中的输出模板生成报告，包含：

- 拆分概览（主切维度、辅助维度、子需求数量）
- 子需求列表（名称、描述、验收标准、依赖、复杂度、建议优先级）
- INVEST 检验结果

### 步骤 5：用户确认与创建

用户确认拆分方案后，逐个创建子需求：

- `create_tapd_story(title=..., description=..., workspace_id=..., fields={"parent_id": "父需求ID"}, ...)`

通过 `fields` 透传 `parent_id` 建立父子关联。父需求 ID 为 19 位长 ID，若只有短 ID 需先转换。

所有子需求创建**必须经用户确认后执行，禁止自动创建**。

## 输出格式

统一采用以下输出顺序：

1. 当前阶段发生了什么
2. 结果摘要
3. 还缺什么 / 有什么风险
4. 下一步建议

同时遵循以下约束：

- 不原样粘贴整段 MCP JSON 给用户
- 不在模板未锁定时说"已按模板生成"
- 不在人工整理草案时说"这是预览结果"
- 若结果来自人工兜底，明确写"人工草案"
- 若结果来自 MCP，明确写"预览结果"或"写回结果"
- 改写预览草稿时，说明改写基于哪版基线（current / original）

## 已知限制

- 本技能依赖 `requirement-assistant` MCP Server，MCP 不可用时不能宣称已经完成 TAPD 查询、预览、建单或写回。
- 预览、补全和 AI读层生成可能存在异步等待，不能把 `running` 状态当成失败，也不能用人工草案冒充 MCP 预览结果。
- TAPD 字段、模板和产品配置受项目权限影响；缺失必填字段时必须先补齐再创建或写回。
- 插入本地图片依赖上传脚本和 Access Token，缺少凭据时只能提示用户补齐。
- 所有 create、apply、update 和拆分后建单动作都需要用户明确确认。

## Troubleshooting

### MCP Server 不可用

不要仅输出"MCP 不可用"就结束——**主动引导用户去配置**：

> ⚠️ `requirement-assistant` MCP Server 当前未连接。
> 请前往 WorkBuddy 左上角 **⚙️ 设置 → 连接器** 检查 requirement-assistant 的连接状态。
> 配置模板见 `references/remote-mcp-setup.md`。配置完成后重试。

可选：若用户只是要文档草案，明确标注"人工草案"后可提供一版备用内容。

### MCP 返回 401 / 403

> ⚠️ 认证失败，请检查 WorkBuddy 左上角 **⚙️ 设置 → 连接器 → requirement-assistant** 下的 MCP 配置：
> - 太湖授权是否已过期（重新召唤专家可自动弹出授权卡片）
> - `X-Tapd-Access-Token` 是否有效（如已配置）

### Preview 长时间 running
- 正常现象，PRD 生成通常需要 1-5 分钟
- 按 `retry_after_seconds` 间隔轮询
- 超过 10 分钟仍 running → 可能服务端异常

### Create 返回 need_required_fields
- 先调用 `get_required_fields` 查看缺失字段
- 引导用户补齐后再重试

### 返回 need_tapd_token（首次配置引导）

📎 **完整指引见：[`references/token-setup-guide.md`](references/token-setup-guide.md)**

简要版：
1. 用户前往 TAPD 生成个人访问令牌（约 1 分钟）
2. 打开 WorkBuddy 左上角 **⚙️ 设置 → 连接器 → 编辑对应连接器 → headers 添加 `X-Tapd-Access-Token`**
3. 保存后重试

## 常见错误避免

避免以下错误：

- 把 `preview` 的 `running` 当成失败
- 把人工草案当成 MCP 预览结果
- 没选模板却宣称"按模板生成"
- 没补齐 `missing_required_fields` 就直接 create
- 未经确认就 apply / create
- 忽略 MCP 已返回的 `available_products`、`input_required`、`prompt_hint`
- 在预览草稿阶段用 `update_tapd_story`（应用 `action=revise`）
- 调用不存在的 `list_products`
- 把 `stage = insufficient_permissions` / `tapd_api_param_error` 说成"服务端内部错误"或"MCP 配置问题"（应按 `references/response-contracts.md` 中的说明精确归因）
- **默认**不应代用户操作 `~/.workbuddy/mcp.json`，优先引导用户手动配置；仅在用户明确要求时协助写入

### fallback 链路：requirement-assistant 建单失败时的降级方案

若 `requirement-assistant` 的 `create` / `apply` 无法完成建单（如 `need_tapd_token` 未解决、服务端不可用等）：

1. **检查 `tapd-woa`（TAPD 司内版本）是否可用**（通过 OAuth 鉴权，用户工作台一般已配置）
   - 可用 → 告知用户后，通过 `tapd-woa` 的 `stories_create` 尝试降级建单（仅基础字段，不执行补全增强）
   - 注意：`tapd-woa` 通常**只读权限**，create 可能返回 403
2. 降级不是默认路径，优先解决 `requirement-assistant` 自身的认证问题

## 参考资料

按需读取以下文件：

- `references/capability-matrix.md`：工具能力矩阵与使用边界
- `references/response-contracts.md`：常见返回结构、状态机与关键字段
- `references/remote-mcp-setup.md`：远程 MCP 接入方式
- `references/requirement-split-framework.md`：需求拆分框架（维度、INVEST门禁、输出模板）


