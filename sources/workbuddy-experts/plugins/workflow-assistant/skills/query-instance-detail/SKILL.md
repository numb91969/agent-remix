---
name: query-instance-detail
description: |
  汇金工作流 — 查询流程单详情技能。查看某个流程单的完整信息，包括审批进度、审批历史。
  触发词：流程单详情、T开头ID的详情、查看审批进度、这个流程单、审批到哪了、这个单子的详情、流程单状态
---

# query-instance-detail

## 这个技能做什么

查看某个流程单（InstanceId，T 开头）的基本信息、审批进度和审批历史。

## 唯一可用工具

`DescribeWorkflowInstance`

## 约束

- **InstanceId 是必填参数**（T 开头）。如果用户没给，请求用户提供或从上下文推断。
- **只调用 1 次**，不需重复。
- 不使用 ExportWorkflowInstanceList / DescribeWorkflow / ListWorkflowInstance / ListApplyWorkflowInstance 等其他工具。

## 输出内容

从 DescribeWorkflowInstance 返回中提取：

**基本信息**：流程单标题 / ID / 所属流程名称 / 发起人 / 发起时间 / 状态 / 流程耗时

**审批进度**（流程图节点）：按节点顺序展示每个节点的名称、状态、处理人、处理时间

**审批历史**（DealHistory）：按时间倒序展示操作人、操作（同意/拒绝/转审）、意见、时间

## 输出格式

参考 @templates/instance-detail.md 模板渲染。

状态映射：Running→🔄进行中 / Succeed→✅已完成 / Revoked→↩️已撤回 / Failed→❌已失败 / Pending→⏳待处理

审批结果映射：Agree→✅同意 / Reject→❌拒绝 / Revoke→↩️撤回 / Transfer→🔀转审

> 流程单状态、任务节点状态、审批结果（DealHistory.JudgeRet）、节点类型的完整枚举见 @references/status-enum.md。

## 输出末尾

```markdown
> 以上数据均来自流程平台（https://huijin.woa.com/flow/apply/detail/{InstanceId}）
```

流程单的实际字段填写值，请在流程平台详情页查看。

## 空结果 / 错误

提示：确认流程单 ID（T 开头）是否正确 / 确认是否有查看权限。
