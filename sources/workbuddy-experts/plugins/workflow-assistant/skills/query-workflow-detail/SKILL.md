---
name: query-workflow-detail
description: |
  汇金工作流 — 查询流程详情技能。查看某个流程的配置信息，包括流程图、输入字段定义、节点配置等。
  触发词：流程详情、P开头ID的详情、流程图、流程配置、这个流程的信息、流程定义、流程的节点、流程的字段定义
---

# query-workflow-detail

## 这个技能做什么

查看某个流程（WorkflowId，P 开头）的配置详情，包括流程基本信息、流程图节点结构、输入字段定义。

## 唯一可用工具

`DescribeWorkflow`

## 约束

- **WorkflowId 是必填参数**（P 开头）。如果用户没给，先通过 query-workflow-list 技能定位。
- **只调用 1 次** DescribeWorkflow 即可获取全部信息，不需要重复调用。
- 不要使用 ListWorkflowInstance（那是查流程单列表的，属于另一个技能）。
- 传 `IsLatest: true` 获取最新版本。

## 输出内容

从 DescribeWorkflow 返回中提取并展示：

**基本信息**：流程名称 / ID / 创建人 / 创建时间 / 更新时间 / 版本号 / 描述

**流程图节点**：按顺序展示每个节点的名称、类型（审批/自动/条件等）、处理人配置

**输入字段定义**：展示 InputParams 中每个字段的 name / key / type / 是否必填 / 枚举选项（如有）

## 输出格式

参考 @templates/workflow-detail.md 模板渲染。

## 输出末尾

```markdown
> 以上数据均来自流程平台（https://huijin.woa.com/flow/detail/{WorkflowId}）
```

## 空结果 / 错误

提示：确认流程 ID（P 开头）是否正确 / 确认是否有查看权限。
