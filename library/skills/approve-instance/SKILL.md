---
name: approve-instance
description: |
  汇金工作流 — 审批流程单技能（同意/拒绝/转办/前置加签/后置加签/参议）。执行前会主动查询流程单输入字段值和当前节点的能力配置，通过问答组件二次确认后才执行写操作。
  触发词：审批、同意、通过、批准、拒绝、驳回、我要审批、审这个单、处理待办、执行审批、转办、加签、前置加签、后置加签、参议、咨询审议
---

# approve-instance

## 这个技能做什么

对指定流程单（InstanceId，T 开头）的当前待办任务节点执行审批操作。这是**写操作**，提交后不可回退。

支持的 `JudgeRet` 取值：`Agree`（同意）/ `Reject`（拒绝）/ `Transfer`（转办）/ `PreAddApprover`（前置加签）/ `NextAddApprover`（后置加签）/ `Consultant`（参议）。

> ⚠️ 节点是否支持转办/加签/参议由流程图配置决定，必须先通过 `GetInstanceTaskDetail` 探测。

## 可用工具

| 阶段 | 工具 | 用途 |
|------|------|------|
| 读 | `DescribeWorkflowInstance` | 查流程单整体信息 |
| 读 | `GetInstanceTaskList` | 拿当前进行中的 TaskId 和处理人 |
| 读 | `DescribeWorkflow` | 获取 VariableKeys（字段定义） |
| 读 | `GetInstanceTaskDetail` | 探测节点能力（转办/加签/参议/审批后可撤回） |
| 读 | `ExportWorkflowInstanceList` | 获取用户填写的字段值 |
| 写 | `CompleteWorkflowInstance` | 执行审批（核心工具） |

## 约束

- **InstanceId 是必填参数**（T 开头）。如果用户没给，请求用户提供或从上下文推断。
- **必须先查后写**：写操作前必须先执行 Step 1~3 拿到 TaskId、字段值和节点能力。
- 🚨 **三件套铁律**：`ExportWorkflowInstanceList` 单独传 `InstanceIds` 会报错，必须同时传 `WorkflowId`（从 Step 1 获取）+ `InstanceIds` + `VariableKeys`（从 `DescribeWorkflow` 获取），缺一不可。
- **必须在问答组件二次确认后才调用 `CompleteWorkflowInstance`**。严禁跳过确认。
- **只调用 1 次 `CompleteWorkflowInstance`**。成功即完成，失败按错误告知。
- 只有当前用户是任务处理人才能审批；否则如实告知权限不足。
- 转办/加签/参议必须提供 `NewApprover`（RTX 列表）；节点不支持时明确阻止。
- 拒绝时鼓励用户填写 `Opinion`（审批意见）。

## 执行流程

1. **定位目标任务**（并行读）：
   - `DescribeWorkflowInstance` → 获取流程单标题、发起人、状态
   - `GetInstanceTaskList` → 拿到 `Status=Running` 的 `TaskId` 和 `Handler`
   - 判断：非 `Running` 终止 / 非处理人终止 / 多节点让用户选择

2. **获取字段值与节点能力**（并行读）：
   - `DescribeWorkflow`（`Id: WorkflowId, IsLatest: true`）→ 提取 `VariableKeys`（排除 `__user_instance_follower`）
   - `GetInstanceTaskDetail`（`InstanceId`+`TaskId`）→ 探测能力，参考 `@references/task-capability.md`
   - 能力展示：转办/前置加签/后置加签/参议/审批后可撤回（缺字段按"不支持"处理）
   - 然后调用 `ExportWorkflowInstanceList`（`WorkflowId`+`InstanceIds:[InstanceId]`+`VariableKeys`+`Limit:1`）→ 字段值
   - ⚠️ 三个参数缺一不可：WorkflowId（Step 1 获取）+ InstanceIds + VariableKeys

3. **呈现审批前简报** → 按 `@templates/pre-approval-brief.md` 输出：
   - 流程单信息 + 字段值表格 + 节点能力清单 + 可用操作提示

4. **收集操作意图**：解析 `JudgeRet`、`Opinion`、`NewApprover`。
   - 参数与节点能力冲突 → 告知并让用户重选

   | 用户说法 | JudgeRet |
   |---------|----------|
   | 同意 / 通过 / 批准 | `Agree` |
   | 拒绝 / 驳回 / 不通过 | `Reject` |
   | 转办 / 转给 | `Transfer` |
   | 前置加签 / 前面加签 | `PreAddApprover` |
   | 后置加签 / 后面加签 | `NextAddApprover` |
   | 参议 / 咨询 / 协助审议 | `Consultant` |

   > 各动作是否必须带 `NewApprover`、或签/会签（HandleMode）、以及节点/流程单状态的可审批性，详见 @references/status-enum.md。

5. **问答组件二次确认**（强制）→ 按 `@templates/confirm-approval.md` 生成确认摘要。
   - ✅ 确认执行 → 进入下一步
   - ❌ 取消 → 终止，输出"已取消，未做任何变更"

6. **调用 `CompleteWorkflowInstance`** 执行：
   ```json
   { "Id": "T...", "TaskId": "N...", "JudgeRet": "Agree", "Opinion": "...", "NewApprover": [] }
   ```
   转办/加签时必须带 `NewApprover`（如 `["justinke"]`）

7. **展示结果** → 按 `@templates/approval-result.md` 输出成功/失败信息

## 输出末尾

```markdown
> 以上操作均通过流程平台（https://huijin.woa.com/flow/apply/detail/{InstanceId}）
```
