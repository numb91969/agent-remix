---
name: query-workflow-related-instances
description: |
  汇金工作流 — 查询流程相关单据技能。查看某个流程下所有相关的流程单列表，或批量查询该流程下所有流程单的输入字段实际值。
  触发词：流程的单据、流程相关的流程单、这个流程有哪些申请、流程下的流程单、P开头ID的流程单、某流程的申请记录、批量导出字段、批量提取字段、某流程下所有流程单的字段、查这个流程所有单据的字段、帮我查某个流程下所有单据的字段
---

# query-workflow-related-instances

## 这个技能做什么

查询指定流程（WorkflowId，P 开头）下的所有流程单列表，或批量导出这些流程单的输入字段实际值。

## 可用工具

| 工具 | 用途 |
|------|------|
| `ListWorkflowInstance` | 查询流程单列表（基础信息） |
| `ExportWorkflowInstanceList` | 批量提取流程单输入字段实际值（需传 VariableKeys） |
| `DescribeWorkflow` | 获取流程输入字段定义（提取 key/name/type/enum） |

## ⚠️ 降级策略（仅在遇到错误时使用）

正常传 WorkflowId、Limit、Status、VariableKeys 等参数调用。只有遇到 `must be integer` / `must be array` 错误时，才执行降级：

1. 去掉非 string 参数重试一次
2. 如果仍失败或 Flows=null：告知用户"受平台工具链限制，暂无法获取数据，请到网页查看"。网页链接：`https://huijin.woa.com/flow/detail/{WorkflowId}`

## 约束

- **WorkflowId 是必填参数**（P 开头）。如果用户没给，先通过 query-workflow-list 技能定位。
- **不要人为截断展示条数。** 默认拉取首批 `Limit:50` 并**展示全部返回项**；若 `Total` 大于已取数量，末尾告知"共 N 条，已展示 M 条，需要更多/全量请告诉我"。
- 用户说"全部/全量/导出/统计"时，按 `Limit:200` + `Offset` 递增**分批拉全量**。
- 命中筛选触发词时，按 @references/filters.md 的「触发词 ↔ MCP 参数」映射带对应参数下推过滤。
- 用户说「字段」「导出字段」→ 默认指**实际填写的值**（用 ExportWorkflowInstanceList），不是字段定义。
- 数组参数（VariableKeys / Status / InstanceIds）必须传 JSON 数组，不能传字符串。
- **ExportWorkflowInstanceList 必须传 VariableKeys**，否则返回 `Total>0, List=[]`（不是接口异常，是参数缺失）。
- 🚨 **ExportWorkflowInstanceList 必须用 `mcp_call_tool` 调用，不能用 `mcp__` 前缀的内部调用方式**。内部调用链存在 array 参数序列化 bug，会误报 "must be array"。正确格式：`mcp_call_tool(serverName="huijin-workflow", toolName="ExportWorkflowInstanceList", arguments="...")`
- **Excel 导出只能执行现成脚本** `skills/query-workflow-related-instances/scripts/export_instance_fields.py`，禁止自写 Python。
- 不要使用 `ListApplyWorkflowInstance`（那是查"我发起的"，属于另一个技能）。

## 筛选参数

命中筛选/排序意图时，按 @references/filters.md 带上对应参数下推过滤（含 `Status`/`Apply`/`NeedFollow`/`Keyword`/时间范围/`InstanceIds`/排序，`WorkflowId` 必带）。

## 场景判断

| 用户意图 | 取多少条 | 用什么工具 | 输出形式 |
|---------|---------|-----------|---------|
| 默认查看（"这个流程有哪些申请"） | 首批 50，展示全部返回 | ListWorkflowInstance | Markdown 表格 |
| 带筛选（"进行中的"、"xxx 发起的"） | 带筛选参数拉取，展示全部返回 | ListWorkflowInstance + 筛选参数 | Markdown 表格 |
| 导出基础 Excel | 全量（分批 200） | ListWorkflowInstance | xlsx skill 生成文件 |
| 导出字段实际值 | 全量（分批 100） | DescribeWorkflow → ExportWorkflowInstanceList | 现成脚本生成 Excel |
| 统计分析 | 全量（分批 200） | ListWorkflowInstance | HTML 简报 |

## 输出格式

按 @templates/related-instance-list.md 渲染（列表输出 + 批量字段导出预览两种格式；状态展示映射见 @references/filters.md）。

展示完毕后追加：
```markdown
> 共 {Total} 条，已展示 {显示数} 条。需要按状态/发起人/时间筛选或查看全量请告诉我。

---
💡 还可以帮你：
- 📋 更多/筛选：按状态/发起人/时间筛选
- 📊 导出基础 Excel
- 📑 导出字段值（实际填写内容）
- 📈 统计分析简报
```

## 导出字段实际值（核心场景）

当用户要求导出字段值时，需要 3 步数据获取 + 脚本执行：

1. 调 DescribeWorkflow 获取字段定义（key/name/type/enum），排除 `__user_instance_follower`。<br>⚠️ 必须保留 Key→Name 映射：Key 用于从 ParamsMap 取值，Name 用于 Excel 列标题
2. 调 ExportWorkflowInstanceList（传入 VariableKeys = 上一步的 key 列表），分批拉全
3. 执行现成脚本生成 Excel：
   - write_to_file 写 JSON 到 `/tmp/export_data_{WorkflowId}.json`，格式：`{ workflow_name, workflow_id, fields: [{key,name,type,enum}], instances: [{Id,Title,Creator,CreateTime,Status,ParamsMap}] }`<br>（⚠️ `fields[].name` 必须来自 DescribeWorkflow 返回的 `Name` 属性（中文名称），不能使用 `Key`）
   - execute_command: `python skills/query-workflow-related-instances/scripts/export_instance_fields.py --input /tmp/export_data_{WorkflowId}.json --output {WorkflowId}_流程单输入字段导出.xlsx`
   - delete_file 删除临时 JSON

注意：步骤 1→2 有依赖（VariableKeys 来自步骤 1），必须串行。

## 输出末尾

```markdown
> 以上数据均来自流程平台（https://huijin.woa.com/flow/detail/{WorkflowId}）
```

流程单 ID（T 开头）可链接：`https://huijin.woa.com/flow/apply/detail/{InstanceId}`

## 空结果

提示：确认 WorkflowId 正确 / 该流程暂无申请 / 调整筛选条件 / 确认权限。
