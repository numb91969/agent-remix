# 筛选参数：export-instance-fields（`ExportWorkflowInstanceList`）

批量导出时，`ExportWorkflowInstanceList` 除 `WorkflowId`/`InstanceIds`/`VariableKeys` 三件套外，还支持以下筛选参数。用户要求"只导出某类单子"时按此下推：

| 用户中文说法 / 触发词 | MCP 参数 | 取值 | 说明 |
|---------------------|---------|------|------|
| 已完成的 / 已结束的 / 只要通过的 | `Status` | `["Succeed"]` | 状态数组，可多选 |
| 进行中的 | `Status` | `["Running"]` | |
| 被驳回的 / 失败的 | `Status` | `["Failed"]` | |
| 已撤回的 / 已撤单的 | `Status` | `["Revoked"]` | |
| 待处理的 | `Status` | `["Pending"]` | |
| xxx 发起的 / xxx 提交的 | `Apply` | `"rtxname"` | 申请人 RTX |
| 关键字 xx / 标题带 xx | `Keyword` | `"xx"` | 名称模糊匹配 |
| 最近一周 / 从 X 号起 | `StartCreateTime` | `"2026-07-22 00:00:00"` | 起始创建时间 |
| 截止到 X / X 号之前 | `EndCreateTime` | `"2026-07-29 23:59:59"` | 结束创建时间 |
| 最新在前 / 时间倒序 | `SortBy`+`SortOrder` | `"CreateTime"` + `"desc"` | |

## 类型与约束

- `Status`/`InstanceIds`/`VariableKeys` 恒为**数组**；`Apply`/`Keyword`/时间为**字符串**。
- 不带这些筛选参数时默认导出该流程下全部流程单。
