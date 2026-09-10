---
name: query-my-instances
description: |
  汇金工作流 — 查询我发起的流程单技能。获取当前用户创建的流程单列表。
  触发词：我发起的、我创建的流程单、我提交的、我的申请、我申请的流程、我的审批单、我发起的审批单
---

# query-my-instances

## 这个技能做什么

展示当前用户发起的流程单列表，支持按状态、关键字、创建时间、排序等条件筛选。

## 唯一可用工具

`ListApplyWorkflowInstance`

## 筛选参数

命中筛选/排序意图时，按 @references/filters.md 的「触发词 ↔ MCP 参数」映射带上对应参数下推过滤（含 `Status`/`Keyword`/`StartCreateTime`/`EndCreateTime`/排序）。

## ⚠️ 降级策略（仅在遇到错误时使用）

正常传 Limit、Status 等参数调用。只有遇到 `must be integer` / `must be array` 错误时，才执行以下降级：

1. 去掉 Limit/Status 等非 string 参数重试一次
2. 如果 Flows=null（只有 TotalCount）：告知用户"受平台工具链限制，暂无法获取列表详情，请到网页查看"，附带 TotalCount。网页链接：`https://huijin.woa.com/flow/apply/mine`

## 约束

- **不要人为截断展示条数。** 默认拉取首批 `Limit:50` 并**展示全部返回项**；若 `Total` 大于已取数量，末尾告知"共 N 条，已展示 M 条，需要更多/全量请告诉我"。
- 用户说"全部/全量/导出/统计"时，按 `Limit:200` + `Offset` 递增**分批拉全量**。
- 命中筛选触发词时，务必按上方映射表带上对应参数，让平台端过滤，不要拉全量再手工筛。
- 不要使用 `ListWorkflowInstance`（那是按流程 ID 查的，属于另一个技能）。

## 场景判断

| 用户意图 | 取多少条 | 输出形式 |
|---------|---------|---------|
| 默认查看（"我发起的流程单"） | 首批 50，展示全部返回 | Markdown 表格 |
| 带筛选（"进行中的"、"关键字 xxx"） | 带筛选参数拉取，展示全部返回 | Markdown 表格 |
| 导出 Excel | 全量（分批，每次 200） | xlsx skill 生成文件 |
| 统计分析 | 全量（分批，每次 200） | HTML 简报 |

## 输出格式

按 @templates/my-instance-list.md 渲染 Markdown 表格（列：流程单名称 / 流程单ID / 发起时间 / 流程耗时 / 状态 / 当前节点 / 当前处理人；状态展示映射与耗时格式化见该模板）。

展示完毕后追加：
```markdown
> 共 {Total} 条，已展示 {显示数} 条。需要按状态/关键字/时间筛选或查看全量请告诉我。

---
💡 还可以帮你：
- 📋 更多/筛选：按状态、关键字、时间筛选
- 📊 导出 Excel
- 📈 统计分析简报
```

## 统计分析输出

全量拉取后统计：总数 + 状态分布 + 平均耗时 + 耗时 Top + 时间趋势。以 HTML 简报输出（参考 @templates/my-apply-flow-briefing.html）。

## 输出末尾

```markdown
> 以上数据均来自流程平台（https://huijin.woa.com/flow/apply/mine）
```

流程单 ID（T 开头）可链接：`https://huijin.woa.com/flow/apply/detail/{InstanceId}`

## 空结果

提示：当前暂无您发起的流程单，可尝试去掉筛选条件。
