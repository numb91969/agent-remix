# 能力矩阵

本文件描述 `requirement-assistant` MCP Server 当前对外暴露的能力边界，供 Skill 编排时按真实工具能力做路由。

## 可见性规则

Server 默认对外暴露：

- `public`
- `expert`

`internal` 工具默认不应由 Skill 直接调用。

## Public 工具

### `start_new_requirement`

用途：面向普通用户的新建需求总入口。

支持动作：

- `action=preview`：启动异步 PRD 预览，立即返回 `task_id`
- `action=status`：查询预览任务进度与结果
- `action=revise`：在预览完成后改写草稿（支持自然语言改写指令或直接覆盖正文）
- `action=create`：复用已完成的预览结果创建 TAPD 需求

适合处理：

- 从一句话想法到需求草案
- 先预览，再决定是否建单
- 预览后不满意，要求改写后再创建
- 复用 preview 结果做最终创建

### `enrich_existing_requirement`

用途：面向普通用户的已有需求补全总入口。

支持动作：

- `action=preview`：启动异步补全预览
- `action=status`：查询补全预览任务进度与结果
- `action=revise`：在补全预览完成后改写草稿（支持自然语言改写指令或直接覆盖补全 HTML）
- `action=apply`：复用预览结果写回 TAPD

适合处理：

- 对已有需求做结构化补全
- 先看补全结果，再决定是否回写
- 补全预览后不满意，要求改写后再写回

### `generate_ai_read_layer`

用途：基于已有 PRD Markdown，生成固定 Markdown 结构的 AI读层需求信息。

适合处理：

- 为已有 PRD 生成结构化的 AI 可读层
- 在补全或新建预览后，进一步生成 AI读层以便下游消费
- 用户需要精简、结构化的需求摘要

注意：

- 只生成预览，不写回 TAPD
- 不负责读取 TAPD 需求或生成代码方案
- 调用方需先取得 PRD 正文再传入
- 如需写回 TAPD，由编排层调用 `update_tapd_story` 完成

参数要点：

- `prd_content`（必填）：已有的人读层 PRD Markdown
- `product`（可选）：产品名称
- `title`（可选）：需求标题
- `source`（可选）：正文来源标识（tapd_story / new_requirement_preview / pasted_prd）
- `known_context`（可选）：已知需求上下文（需求ID、TAPD链接、模板ID等）

## Expert 工具

### `get_story_template_list`

用途：查询某个项目下可用的需求模板列表。

使用时机：

- 用户明确要求按模板生成
- 需要展示模板候选项
- 需要在 preview 前锁定 `template_id`

### `get_story_template_detail`

用途：查看模板正文结构与字段结构。

使用时机：

- 需要阅读模板正文结构
- 需要理解模板字段布局
- 需要帮助用户在多个模板间做选择

### `get_required_fields`

用途：查询模板中仍需补充的必填字段与候选值。

使用时机：

- create 前被 `missing_required_fields` 阻塞
- 需要把字段与候选值翻译成人话
- 需要一次性补齐必填字段

### `get_story_detail`

用途：查询已有需求详情；可选解析描述中的截图。

使用时机：

- 用户只给了 `story_id`
- 补全前需要先了解当前需求内容
- 需要分析需求描述里的截图
- 需要判断需求是否已补全过

### `get_enrichment_modules`

用途：查询可补全模块与默认模块。

使用时机：

- 用户想指定补全范围
- 需要解释补全模块含义
- 需要决定是否使用默认模块

### `preview_enrichment`

用途：直接生成补全预览，但不回写 TAPD。

使用时机：

- 需要直接查看补全实验结果
- 需要比较不同模块组合的补全结果
- 需要在不走总入口的情况下单独做 expert 级补全预览

注意：常规业务流程仍优先走 `enrich_existing_requirement(action=preview)`。

### `update_tapd_story`

用途：通用更新已有 TAPD 需求，支持修改标题、描述、优先级、负责人、状态及自定义扩展字段。

使用时机：

- 已创建需求需要二次编辑（如修改标题、描述）
- 需要更新需求状态、优先级、负责人
- 需要修改自定义字段值
- 不限于补全模块场景的通用更新

注意：

- 描述字段支持 Markdown（自动转 HTML）或直接传 HTML
- 与 `enrich_existing_requirement(action=apply)` 不同：apply 是补全写回，update 是通用字段修改
- 适用于已创建需求的后续编辑，不适用于预览阶段的草稿改写（预览草稿改写用 `revise` action）
- 若要插入本地图片，优先传 `image_html_codes`；Server 只负责把 HTML 追加到描述，不负责读取用户本地文件

## Internal 工具

以下工具属于底层实现层，不作为 Skill 的常规调用入口：

- `preview_prd`
- `create_tapd_story`
- `apply_enrichment`
- `resume_requirement`
- `search_knowledge`
- 旧任务状态查询 / 停止任务类工具

除非调试 Server 本身，否则不要在 Skill 中主动使用这些工具。

## 关于产品发现

`list_products` 不再作为独立工具暴露。产品上下文的发现已内化到 `start_new_requirement` 和 `enrich_existing_requirement` 的流程中：

- 若产品不明确，这两个 public 工具会返回 `input_required` + `available_products` / `prompt_hint`
- Skill 应直接利用返回的结构化提示引导用户选择，无需单独调用产品查询工具
- 传入 `workspace_id` 后，产品可被自动推断

## 能力边界总结

按如下顺序理解：

1. `public` 负责主流程闭环（新建 / 补全 / AI读层）
2. `expert` 负责选项发现、结构理解、字段补齐、详情读取、通用更新
3. `internal` 负责底层执行，不暴露给最终 Skill 路由

Skill 的职责不是复写后端逻辑，而是：

- 让 Agent 在正确时机调用正确层级的工具
- 避免误判模板、误判状态、误判写回时机
- 将返回结果翻译成用户可理解的结果摘要与下一步

## fallback 链路：降级建单方案

当 `requirement-assistant` 的 `create` / `apply` 无法完成时：

1. 检查 `tapd-woa`（TAPD 司内版本，通过 OAuth 鉴权）是否可用
2. 可用 → 告知用户后尝试降级建单（仅基础字段，不执行补全增强）；注意 `tapd-woa` 通常只读权限
3. 无 → 回到 Token 配置主线，优先解决认证问题

降级前应告知用户当前方案无法完成，征得同意后再切换。
具体判断逻辑详见 `SKILL.md` 中 Troubleshooting 的 fallback 链路章节。
