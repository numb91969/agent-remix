# 筛选参数：query-my-instances

`ListApplyWorkflowInstance` 的入参与用户口语的对应关系。命中触发词就带上对应参数下推过滤。

| 用户中文说法 / 触发词 | MCP 参数 | 取值 | 说明 |
|---------------------|---------|------|------|
| 进行中 / 审批中 / 流转中 | `Status` | `["Running"]` | 状态数组，可多选 |
| 已完成 / 已结束 / 已通过 | `Status` | `["Succeed"]` | |
| 已驳回 / 被拒 / 没通过 | `Status` | `["Failed"]` | |
| 已撤回 / 已撤单 / 撤掉的 | `Status` | `["Revoked"]` | |
| 待处理 / 还没开始 | `Status` | `["Pending"]` | |
| 关键字 xx / 标题带 xx / 名字含 xx / 搜 xx | `Keyword` | `"xx"` | 名称模糊匹配 |
| 最近一周 / 近一个月 / X 月以后 / 从 X 号起 | `StartCreateTime` | `"2026-07-22 00:00:00"` | 起始创建时间 `YYYY-MM-DD HH:mm:ss` |
| 截止到 X / X 号之前 / 到某月 | `EndCreateTime` | `"2026-07-29 23:59:59"` | 结束创建时间 |
| 最新 / 最近的在前 / 按时间倒序 | `SortBy`+`SortOrder` | `"CreateTime"` + `"desc"` | 默认即最新在前 |
| 最早的在前 / 正序 | `SortBy`+`SortOrder` | `"CreateTime"` + `"asc"` | |
| 全部 / 全量 / 导出 / 统计 | `Limit`+`Offset` | `200` + 递增 | 分批拉全量 |

## 类型与约束

- 多个条件可叠加。`Status` 恒为**数组**；时间为**字符串**。
- "我发起的"身份由该工具隐含（当前用户即创建人），无需额外传参。
- 流程单状态展示映射：`Running`→🔄进行中 / `Succeed`→✅已结束 / `Revoked`→↩️已撤单 / `Failed`→❌已驳回 / `Pending`→⏳待处理 / 其他→⚠️异常。
