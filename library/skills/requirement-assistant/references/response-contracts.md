# 常见返回结构与状态约束

本文件记录 `requirement-assistant` MCP Server 中最值得 Skill 识别的返回结构与关键字段。

## 产品上下文缺失 / 歧义

新建需求与补全需求在缺产品上下文时，可能返回：

- `stage: input_required`
- `available_products`
- `action_required: ask_user_to_select_product`
- `prompt_hint`

处理要求：

- 优先基于 `available_products` 让用户选择
- 不重复发散式追问
- 不要擅自猜默认产品

## 新建需求 preview 状态机

`start_new_requirement(action=status, preview_task_id=...)` 常见返回：

### 1. 运行中

关键字段：

- `task.status = running`
- `stage = task_running`
- `retry_after_seconds`
- `next_step.recommended_action = status`

处理要求：

- 只同步一句简短进度
- 继续保留 `preview_task_id`
- 继续查询，不要把人工草案冒充成 preview 结果

### 2. 已完成

关键字段：

- `task.status = completed`
- `stage = task_completed`
- `result`
- `next_step.recommended_action = create`

新建需求 preview 结果常见字段：

- `prd_title`
- `prd_content`
- `prd_length`
- `template_id`
- `workitem_type_id`
- `required_field_values`
- `required_fields`
- `missing_required_fields`
- `feature_preview`
- `used_context_sources`
- `warnings`
- `suggested_validate_payload`
- `suggested_create_payload`

处理要求：

- 优先基于 `prd_title` + `prd_content` 做摘要
- 若 `missing_required_fields` 非空，不要直接 create
- 若 `template_id` 为空，不要擅自宣称"已按模板生成"

### 3. 已过期

关键字段：

- `stage = preview_expired` 或 `task_completed_expired`

处理要求：

- 明确告知需要重新 preview
- 不继续 create

### 4. 已消费

关键字段：

- `task.status = consumed`
- `consumed_result`

处理要求：

- 说明该 preview 已用于创建
- 如需再次创建，必须重新 preview

## 新建需求 create 关键阻塞点

`start_new_requirement(action=create, ...)` 常见阻塞：

### 1. 缺少 preview_task_id

关键字段：

- `stage = preview_task_required`

处理要求：

- 先 preview，再 create

### 2. preview 仍在运行

关键字段：

- `stage = preview_task_running`

处理要求：

- 继续 status，不要误判失败

### 3. 模板必填字段不足

关键字段：

- `stage = need_required_fields`
- `missing_required_fields`
- `preview`

处理要求：

- 调用 `get_required_fields`
- 翻译字段含义、候选值、默认值
- 引导用户一次性补齐

## 补全 preview 结果

`enrich_existing_requirement(action=preview)` 或 `preview_enrichment` 成功后，常见字段：

- `story_id`
- `story_title`
- `tapd_url`
- `already_enriched`
- `preview_generated`
- `modules`
- `generated_modules`
- `enrichment`
- `enriched_html`
- `original_html`
- `used_context_sources`
- `knowledge_result_count`

处理要求：

- `preview_generated = true` 才表示拿到了新的补全预览
- `already_enriched = true` 表示需求可能已补充过，不要假装生成了全新内容
- `enriched_html` 是 apply 的直接输入，不要随意改写其结构含义

## 补全 revise 草稿改写

`enrich_existing_requirement(action=revise, preview_task_id=...)` 常见返回：

### 成功改写

关键字段：

- `stage = revised`
- `draft_state`：草稿状态（`original` / `current` / `previous` / `revision_count` / `last_change_summary`）
- `enriched_html`：改写后的补全 HTML
- `story_title`：改写后的标题（如有修改）

处理要求：

- 说明本次改写基于哪版基线（`current` / `original`）
- 改写后草稿仍可继续 revise 或执行 apply

### 需要 preview_task_id

关键字段：

- `stage = preview_task_required`

处理要求：

- 先 preview，再 revise

### preview 已消费

关键字段：

- `stage = already_consumed`

处理要求：

- 该 preview 已用于写回，无法再改写，需重新 preview

## 补全 apply 关键约束

`enrich_existing_requirement(action=apply, preview_task_id=...)` 常见约束：

- 若 `preview_task_id` 对应结果已过期，必须重新 preview
- 若该 preview 已被消费，再次 apply 会命中幂等保护
- 若没有 `enriched_html` 且没有可复用 preview，Server 会尝试重新 preview

处理要求：

- 用户未明确确认前，不自动 apply
- 成功时说明本次写回了哪些模块
- 失败时保留 preview 摘要，不只报异常字符串

## 新建需求 revise 草稿改写

`start_new_requirement(action=revise, preview_task_id=...)` 常见返回：

### 成功改写

关键字段：

- `stage = revised`
- `draft_state`：草稿状态（`original` / `current` / `revision_count` / `last_change_summary`）
- `prd_content`：改写后的 PRD 正文
- `prd_title`：改写后的标题（如有修改）

处理要求：

- 说明本次改写基于哪版基线（`current` / `original`）
- 改写后草稿仍可继续 revise 或执行 create

### 需要 preview_task_id

关键字段：

- `stage = preview_task_required`

处理要求：

- 先 preview，再 revise

### preview 已消费

关键字段：

- `stage = already_consumed`

处理要求：

- 该 preview 已用于创建，无法再改写，需重新 preview

## generate_ai_read_layer 返回

`generate_ai_read_layer(prd_content=..., ...)` 常见返回：

### 成功

关键字段：

- `success = true`
- `ai_read_layer_markdown`：生成的 AI读层 Markdown

### 失败

关键字段：

- `success = false`
- `error`：失败原因

注意：AI读层只生成预览，不写回 TAPD。如需写回，由编排层调用 `update_tapd_story` 完成。

## update_tapd_story 返回

`update_tapd_story(story_id=..., ...)` 常见返回：

### 成功

关键字段：

- `success = true`
- `submitted_fields`：实际提交的字段列表

### 失败

关键字段：

- `success = false`
- `error`：失败原因

与 `enrich_existing_requirement(action=apply)` 的区别：

- `update_tapd_story`：通用字段编辑（标题、状态、优先级等），直接传值
- `enrich_existing_requirement(action=apply)`：补全内容写回（背景、目标、竞品等模块），基于 preview 结果

## TAPD HTTP 结构化错误（新增）

任何 `public`/`expert` 工具调用 TAPD API 出错时，可能返回以下结构化 `stage`（而非笼统的 `INTERNAL_ERROR`）：

### 1. Token 已失效

关键字段：

- `stage = invalid_tapd_token`
- `error_code = TAPD_AUTH_401`
- `http_status = 401`

处理要求：

- 提示用户 Token 可能已过期，需要重新生成并更新连接器配置中的 Token
- 不要说成"MCP 配置问题"，这是 Token 本身失效

### 2. 权限不足

关键字段：

- `stage = insufficient_permissions`
- `error_code = TAPD_FORBIDDEN_403`
- `http_status = 403`
- `workspace_id`

处理要求：

- 明确告知用户："当前 TAPD Token 无权访问项目 `{workspace_id}`"
- 引导用户确认是否已加入该项目，或切换到有权限的项目
- 不要归因为"服务端内部错误"或引导用户重新配置 MCP

### 3. 参数错误（可能同时是权限问题）

关键字段：

- `stage = tapd_api_param_error`
- `error_code = TAPD_PARAM_ERROR_422`
- `http_status = 422`
- `workspace_id`（如有）

处理要求：

- TAPD 对"参数无效"和"权限不足"部分场景统一返回 422，无法仅凭状态码精确区分
- 必须把两种可能原因都告知用户：① 请求参数（如 `workspace_id`）不符合项目配置；② 当前 Token 对该项目/资源操作权限不足
- 引导用户先确认 `workspace_id` 是否正确，若正确则考虑权限问题
- 不要笼统说"服务端内部错误"，也不要单一断定为某一种原因

### 通用要求

- 这三类错误都带 `message` 字段（已经是可直接展示给用户的文案），优先直接使用或轻度改写，不要压缩掉关键信息（如 `workspace_id`）
- 不要把这类结构化错误误判为"MCP 配置问题"或"需要重新配置 Token"——只有 `need_tapd_token`（无 Token）才需要引导用户配置 Token
- 若线上返回的仍是 `error_code: INTERNAL_ERROR` 且无 `stage` 字段，说明服务端还未部署到含该分类逻辑的版本，此时才按通用错误处理，不要臆测具体原因

## 模板与结构的边界提醒

必须始终记住：

- `template_id` 主要影响模板选择、字段结构、必填字段、创建时的模板映射
- `prd_content` 是预览阶段生成的正文
- 若未在 preview 前显式传入模板信息，不应假设 `prd_content` 已按模板结构生成

Skill 对外表述时应保持精确：

- 可以说"本次预览返回了 template_id"
- 可以说"本次建单会使用该 TAPD 模板"
- 只有在 preview 阶段明确选中模板并传入后，才可以说"正文按模板结构生成"
