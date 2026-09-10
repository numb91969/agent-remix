# 筛选参数：query-todo-instances

`ListParticipateWorkflowInstance` 的入参与用户口语的对应关系。命中触发词就带上对应参数下推过滤。

| 用户中文说法 / 触发词 | MCP 参数 | 取值 | 说明 |
|---------------------|---------|------|------|
| 待我处理 / 待办 / 需要我审的（本技能核心） | `NeedDeal` | `"true"` | 字符串，**每次必传**，筛出待处理 |
| xxx 发起的 / xxx 提交的 / 谁申请的 | `Apply` | `"rtxname"` | 申请人 RTX，按发起人筛待办 |
| 关键字 xx / 标题带 xx / 搜 xx | `Keyword` | `"xx"` | 名称模糊匹配 |
| 进行中 / 审批中 | `Status` | `["Running"]` | 状态数组，可多选 |
| 已完成 / 已结束 / 已通过 | `Status` | `["Succeed"]` | |
| 已驳回 / 被拒 / 没通过 | `Status` | `["Failed"]` | |
| 已撤回 / 已撤单 | `Status` | `["Revoked"]` | |
| 待处理 / 还没开始 | `Status` | `["Pending"]` | |
| 最新 / 最近在前 / 时间倒序 | `SortBy`+`SortOrder` | `"CreateTime"` + `"desc"` | |
| 最早在前 / 正序 | `SortBy`+`SortOrder` | `"CreateTime"` + `"asc"` | |
| 全部 / 全量 / 导出 / 统计 | `Limit`+`Offset` | `200` + 递增 | 分批拉全量 |

## 类型与约束

- `Status` 恒为**数组**；`NeedDeal`/`Apply`/`Keyword` 为**字符串**。
- ⚠️ 本工具**没有 `StartCreateTime`/`EndCreateTime` 参数**，无法按创建时间范围下推筛选；若用户要按时间筛，拉取后在本地按 `CreateTime` 过滤。
- 流程单状态展示映射：`Running`→🔄进行中 / `Succeed`→✅已结束 / `Revoked`→↩️已撤单 / `Failed`→❌已驳回 / `Pending`→⏳待处理 / 其他→⚠️异常。
