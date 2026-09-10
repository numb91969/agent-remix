---
name: query-workflow-list
description: |
  汇金工作流 — 查询流程列表技能。获取用户有权限查看的流程列表（流程模板），支持按管理员、公开范围、分类、状态、关键字筛选，并支持按发起量排序。
  触发词：我的流程、我的全部流程、查询公开流程、公开流程、有哪些流程、流程列表、流程模板、可用流程、搜索流程、找个流程、按分类查流程、发起量最多的流程
---

# query-workflow-list

## 这个技能做什么

查询用户有权限查看的流程列表（即流程模板/流程定义列表）。覆盖两类核心场景：

1. **我的流程**（用户是流程管理员）：拉取用户为管理员的**全部**流程，形成简报。
2. **公开流程**：拉取**全部**公开流程，支持按分类、状态、发起量筛选与排序。

## 唯一可用工具

`ListWorkflow`

## 筛选参数

完整的关键参数、分类中文→英文 code 映射、流程模板状态映射（3 态）、发起量排序规则见 @references/filters.md。命中筛选/排序意图时按其映射带参数下推。

## ⚠️ 降级策略（仅在遇到错误时使用）

1. 遇到 `must be integer` 错误：去掉 `Limit` 重试一次。
2. 若 `Flows=null`（只有 `TotalCount`）：告知"受平台工具链限制，暂无法获取流程列表详情，请到网页查看"：https://huijin.woa.com/flow

## 约束

- **「我的流程 / 我的全部流程」** → 必须传 `ListType: "Admin"`，并**拉取全量**（不再只取若干条），输出简报。
- **「公开流程」** → 必须传 `IsPublic: "true"`，并**默认拉取全量**；支持 Category / Status / 发起量 筛选。
- **普通浏览**（"有哪些流程""流程列表"等未明确要求范围）：默认拉取首批 `Limit:50` 并**展示全部返回项**，不做人为 10 条截断；末尾告知总数，用户说"全部/全量"则分批拉全量。
- **全量拉取**：每批 `Limit:200`，`Offset` 从 0 递增，直到取回数量 < 200 或达到 `TotalCount`。
- **全量分批**场景允许多次分页调用直至取完。
- 不要使用 `ListWorkflowInstance`（按流程查流程单）或 `ListApplyWorkflowInstance`（查我发起的）。

## 场景判断

| 用户意图 | 范围参数 | 取多少 | 输出形式 |
|---------|---------|--------|---------|
| 我的流程 / 我的全部流程 | `ListType:"Admin"` | 全量 | HTML 简报（参考 my-flows-briefing.html） |
| 公开流程（默认） | `IsPublic:"true"` | 全量 | Markdown 表格 + 筛选提示 |
| 公开流程 + 分类/状态/发起量 | `IsPublic:"true"` + 筛选参数 | 全量 | 已筛选/排序的 Markdown 表格 |
| 搜索（"找个 xx 流程"） | `Keyword:"xxx"` | 展示全部返回 | Markdown 表格 |
| 普通浏览（未指定范围） | 无 | 首批 50，展示全部返回 | Markdown 表格 |

## 场景 A：我的流程（管理员流程简报）

当用户说"我的流程""我名下的流程""我的全部流程"时：

1. 调用 `ListWorkflow({ ListType: "Admin", Limit: 200, Offset: 0 })`，分页拉全量。
2. 汇总成**简报**：总流程数、按分类分布、按创建人分布、按时间趋势、发起量 Top 榜。
3. 以 HTML 简报输出（参考 @templates/my-flows-briefing.html）。

> 默认**不再只展示 10 条**，而是把用户作为管理员的流程全部纳入简报。

## 场景 B：公开流程（带筛选）

当用户说"公开流程""查公开流程"时：

1. 默认调用 `ListWorkflow({ IsPublic: "true", Limit: 200 })` 拉全量。
2. 根据用户附加条件追加参数（映射见 @references/filters.md），全量拉取后再在结果上筛选/排序，或直接用参数下推：
   - **分类**：`Category` 传英文 code。
   - **状态**：`Status` 传流程模板状态（3 态）。
   - **发起量**：`SortBy:"InstanceCount", SortOrder:"desc"`（最多在前）；也可先拉全量后按 `InstanceCount` 排序。
3. 输出 Markdown 表格，列：流程名称 / 流程ID / 分类 / 状态 / 更新时间 / 发起量。

> 分类映射、状态映射（3 态）、发起量排序的完整取值见 @references/filters.md。

## 输出格式

按 @templates/workflow-list.md 渲染 Markdown 表格（列：流程名称 / 流程ID / 分类 / 状态 / 更新时间 / 发起量；状态 Emoji 与场景标题规则见该模板）。

展示完毕后追加：
```markdown
> 当前显示 {n} 条公开流程（已全量拉取）。需要按其他分类/状态/发起量筛选请告诉我。

---
💡 还可以帮你：
- 🔍 发送流程 ID（P 开头）可查看流程详情
- 📋 查看某个流程下的流程单列表
```

## 统计分析输出（全量简报）

全量拉取后统计：总流程数 + 按分类分布 + 按创建人分布 + 按时间维度创建趋势 + 发起量 Top 榜。以 HTML 简报输出（参考 @templates/my-flows-briefing.html）。

## 输出末尾

```markdown
> 以上数据均来自流程平台（https://huijin.woa.com/flow）
```

流程 ID（P 开头）可链接：`https://huijin.woa.com/flow/detail/{WorkflowId}`

## 空结果

提示：当前暂无可查看的流程 / 可尝试不同关键字或分类搜索。
