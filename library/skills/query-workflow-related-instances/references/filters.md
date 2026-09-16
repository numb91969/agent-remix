# 筛选参数：query-workflow-related-instances

`ListWorkflowInstance`（及 `ExportWorkflowInstanceList` 同名筛选参数）的入参与用户口语的对应关系（`WorkflowId` 必带）。

| 用户中文说法 / 触发词 | MCP 参数 | 取值 | 说明 |
|---------------------|---------|------|------|
| 进行中 / 审批中 | `Status` | `["Running"]` | 状态数组，可多选 |
| 已完成 / 已结束 / 已通过 | `Status` | `["Succeed"]` | |
| 已驳回 / 被拒 / 没通过 | `Status` | `["Failed"]` | |
| 已撤回 / 已撤单 | `Status` | `["Revoked"]` | |
| 待处理 / 还没开始 | `Status` | `["Pending"]` | |
| xxx 发起的 / xxx 提交的 / 谁申请的 | `Apply` | `"rtxname"` | 申请人 RTX |
| 我关注的 / 关注的单子 | `NeedFollow` | `true` | **布尔值**，非字符串 |
| 关键字 xx / 标题带 xx / 搜 xx | `Keyword` | `"xx"` | 名称模糊匹配 |
| 最近一周 / 近一个月 / 从 X 号起 | `StartCreateTime` | `"2026-07-22 00:00:00"` | 起始创建时间 `YYYY-MM-DD HH:mm:ss` |
| 截止到 X / X 号之前 | `EndCreateTime` | `"2026-07-29 23:59:59"` | 结束创建时间 |
| 最新 / 时间倒序 | `SortBy`+`SortOrder` | `"CreateTime"` + `"desc"` | |
| 最早 / 正序 | `SortBy`+`SortOrder` | `"CreateTime"` + `"asc"` | |
| 指定单号 / 这几个流程单 | `InstanceIds` | `["T...","T..."]` | 流程单 ID 数组 |
| 全部 / 全量 / 导出 / 统计 | `Limit`+`Offset` | `200` + 递增 | 分批拉全量 |

## 类型与约束

- `Status`/`InstanceIds`/`VariableKeys` 恒为**数组**；`NeedFollow` 恒为**布尔**；`Apply`/`Keyword`/时间为**字符串**。多条件可叠加。
- 流程单状态展示映射：`Running`→🔄进行中 / `Succeed`→✅已结束 / `Revoked`→↩️已撤单 / `Failed`→❌已驳回 / 其他→⚠️异常。
