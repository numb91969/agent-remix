---
name: export-instance-fields
description: |
  汇金工作流 — 批量提取流程单字段技能。支持查询流程单的输入字段值，并以管理员视角批量提取某个流程下所有流程单的全部输入字段和流程字段，导出表格做数据分析。
  触发词：批量导出、批量提取、导出流程单字段、提取字段值、导出所有流程单、流程单字段分析、输入字段、字段值、导出表格做分析、批量字段、某流程下所有流程单的字段
---

# export-instance-fields

## 这个技能做什么

两种粒度的流程单字段提取：

1. **单个流程单字段查询**：查看某个流程单填写的输入字段值
2. **批量字段导出**：管理员批量提取某流程下所有流程单的输入字段值，导出 Excel 做分析

## 可用工具

| 工具 | 用途 |
|------|------|
| `ExportWorkflowInstanceList` | **核心工具**，批量导出流程单 + 字段实际值 |
| `DescribeWorkflow` | 获取字段定义（key/name/type/enum），确定 VariableKeys |
| `DescribeWorkflowInstance` | 单个流程单字段查询场景的辅助工具 |

## ⚠️ 降级策略（仅在遇到错误时使用）

正常传所有参数（含 VariableKeys、Limit）调用 ExportWorkflowInstanceList。只有遇到 `must be array` / `must be integer` 错误时，才告知用户"受平台工具链限制，暂无法获取字段值，请到网页查看"，提供链接。

## 约束

- 🚨 **ExportWorkflowInstanceList 必须用 `mcp_call_tool` 调用**，不能用 `mcp__` 前缀的内部调用方式。内部调用链存在 array 参数序列化 bug，会误报 `must be array`。
  正确格式：`mcp_call_tool(serverName="huijin-workflow", toolName="ExportWorkflowInstanceList", arguments="…")`
- 🚨 **三件套铁律**：`ExportWorkflowInstanceList` 单独传 `InstanceIds` 会报错，必须同时传 `WorkflowId` + `InstanceIds` + `VariableKeys` 三个参数，缺一不可。
- **ExportWorkflowInstanceList 必须传 VariableKeys**，否则返回 `Total>0, List=[]`（不是接口异常，是参数缺失）。
- 批量导出场景：`VariableKeys` 必须先通过 `DescribeWorkflow` 拿到准确字段 key，避免传错导致值为空。
- **默认不翻页**。单个查询传 `Limit: 1`（配合 InstanceIds），批量导出每次传 `Limit: 100`，仅当用户明确要求全量且 Total > 当前已取数量时才翻页。
- **每个工具每个会话最多调 1 次**。如果报错不重试。
- 字段值中的枚举类型展示 Label，空值展示 `—`，数组值用逗号分隔。
- **字段列标题必须使用 `DescribeWorkflow` 返回的 `Name` 属性（中文名称），不能使用 `Key`（机器标识符）。`Key` 仅用于从 `ParamsMap` 中查找值，`Name` 用于展示给用户。**

## 筛选参数（批量导出时可按需筛选子集）

批量导出可在三件套之外追加 `Status`/`Apply`/`Keyword`/时间范围/排序等筛选参数，只导出某类单子。完整触发词映射见 @references/filters.md。

## 场景判断

| 用户意图 | 取多少条 | 用什么工具 | 输出形式 |
|---------|---------|-----------|---------|
| 单流程单字段查询（"Txxx 的字段值"） | 1 条 | ExportWorkflowInstanceList + InstanceIds | Markdown 表格 |
| 批量导出（"把 Pxxx 下所有流程单字段导出"） | 全量（分批 100） | DescribeWorkflow → ExportWorkflowInstanceList | Excel（用 query-workflow-related-instances 的脚本） |

## 场景 A — 单个流程单字段查询

```
0. 先调用 DescribeWorkflowInstance(Id="{T...}") → 拿到 WorkflowId
   → 若用户已提供 WorkflowId（P 开头），可跳过此步
1. mcp_call_tool(serverName="huijin-workflow", toolName="DescribeWorkflow",
     arguments={"Id":"P...","IsLatest":true})
   → 提取所有 InputParams 的 key，排除 __user_instance_follower
2. mcp_call_tool(serverName="huijin-workflow", toolName="ExportWorkflowInstanceList",
     arguments={"WorkflowId":"P...","InstanceIds":["T..."],"VariableKeys":["key1",...],"Limit":1})
   → ⚠️ 三个参数缺一不可：WorkflowId + InstanceIds + VariableKeys
3. 用 Key 查找值，用 Name 做表头：从 ParamsMap 中用 Key 提取字段值，用字段定义的 Name（中文名）做表头，Markdown 表格展示
```

输出格式：
```markdown
### 输入字段值：{Title}（{Id}）

| 字段名 | 值 |
|-------|----|
| {字段中文名} | {值} |
```

## 场景 B — 批量字段导出（管理员场景）

```
1. 确认 WorkflowId（用户给 P 开头 ID，或通过 query-workflow-list 定位）
2. mcp_call_tool DescribeWorkflow → { Id: WorkflowId, IsLatest: true }
   → 提取所有 InputParams 的 key，排除 __user_instance_follower
3. mcp_call_tool ExportWorkflowInstanceList → { WorkflowId, VariableKeys, Limit: 100, Offset: 0 }
   → 若 Total > 100，循环 Offset += 100 拉全
4. 建立 Key→Name 映射表：Key 用于从 ParamsMap 取值，Name 用于 Excel 列标题。组装数据 → 用 xlsx skill 或现成脚本生成 Excel
```

Excel 列：流程单ID / 标题 / 状态 / 发起人 / 发起时间（固定列）+ 每个输入字段列

## 输出末尾

- 批量导出：`> 以上数据均来自流程平台（https://huijin.woa.com/flow/detail/{WorkflowId}）`
- 单个查询：`> 以上数据均来自流程平台（https://huijin.woa.com/flow/apply/detail/{InstanceId}）`
