---
name: query-todo-instances
description: |
  汇金工作流 — 查询待我处理的流程单技能。获取当前用户待审批/待处理的流程单列表。
  触发词：待我处理、待我审批、我的待办、待办流程单、需要我审批的、等我处理的、我要处理的流程单
---

# query-todo-instances

## 这个技能做什么

查询当前用户待审批/待处理的流程单列表，支持按发起人、状态、关键字、排序等条件筛选。

## 唯一可用工具

`ListParticipateWorkflowInstance`

> 注意：通过传 `NeedDeal: "true"` 筛选出待当前用户处理的流程单。

## 筛选参数

命中筛选/排序意图时，按 @references/filters.md 的「触发词 ↔ MCP 参数」映射带上对应参数下推过滤（含 `NeedDeal`/`Apply`/`Keyword`/`Status`/排序）。⚠️ 本工具无时间范围参数，按时间筛需本地过滤。

## ⚠️ 降级策略（仅在遇到错误时使用）

正常传 Limit、NeedDeal 等参数调用。只有遇到 `must be integer` / `must be array` 错误时，才执行以下降级：

1. 去掉 Limit 等非 string 参数重试一次
2. 如果 Flows=null（只有 TotalCount）：告知用户"受平台工具链限制，暂无法获取待办列表详情，请到网页查看"，附带 TotalCount。网页链接：`https://huijin.woa.com/flow/apply/todo`

## 约束

- **不要人为截断展示条数。** 默认拉取首批 `Limit:50` 并**展示全部返回项**；若 `Total` 大于已取数量，末尾告知"共 N 条，已展示 M 条，需要更多/全量请告诉我"。
- 用户说"全部/全量/导出/统计"时，按 `Limit:200` + `Offset` 递增**分批拉全量**。
- 命中筛选触发词时，按上方映射表带对应参数下推过滤。
- 不要使用 `ListApplyWorkflowInstance`（那是查"我发起的"）或 `ListWorkflowInstance`（那是按流程查的）。
- 调用时必须传 `NeedDeal: "true"` 来筛选待处理的流程单。

## 场景判断

| 用户意图 | 取多少条 | 输出形式 |
|---------|---------|---------|
| 默认查看（"待我处理的"） | 首批 50，展示全部返回 | Markdown 表格 |
| 带筛选（"关键字 xxx"、"xxx 发起的"） | 带筛选参数拉取，展示全部返回 | Markdown 表格 |
| 导出 Excel | 全量（分批 200） | xlsx skill 生成文件 |
| 统计分析 | 全量（分批 200） | HTML 简报 |

## 输出格式

按 @templates/todo-instance-list.md 渲染 Markdown 表格（列：流程单名称 / 流程单ID / 发起人 / 处理节点 / 节点开始时间；状态展示映射见 @references/filters.md）。

展示完毕后追加：
```markdown
> 共 {Total} 条，已展示 {显示数} 条。需要按发起人/状态/关键字筛选或查看全量请告诉我。

---
💡 还可以帮你：
- 📋 更多/筛选：按发起人、状态、关键字筛选
- 📊 导出 Excel
- 📈 统计分析简报
- 🔍 发送流程单 ID（T 开头）可查看详情
```

## 统计分析输出

全量拉取后统计：总待办数 + 按发起人分布 + 平均等待时长 + 等待最久 Top。以 HTML 简报输出（参考 @templates/my-todo-briefing.html）。

## 输出末尾

```markdown
> 以上数据均来自流程平台（https://huijin.woa.com/flow/apply/todo）
```

流程单 ID（T 开头）可链接：`https://huijin.woa.com/flow/apply/detail/{InstanceId}`

## 空结果

提示：当前暂无待您处理的流程单，可尝试去掉筛选条件。
