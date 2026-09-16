# 状态枚举说明（approve-instance 使用）

---

## 审批动作（JudgeRet，`CompleteWorkflowInstance` 入参）

| 枚举值 | 展示 | 说明 | NewApprover |
|--------|------|------|-------------|
| `Agree` | ✅ 同意 | 审批通过，流程流转到下一节点 | 无需 |
| `Reject` | ❌ 拒绝 | 审批拒绝，按配置终止或退回 | 无需 |
| `Transfer` | 🔀 转办 | 将本节点任务交给他人处理 | ✅ 必填 |
| `PreAddApprover` | ⬅️ 前置加签 | 在当前节点前追加一个审批人 | ✅ 必填 |
| `NextAddApprover` | ➡️ 后置加签 | 在当前节点后追加一个审批人 | ✅ 必填 |
| `Consultant` | 💬 参议 | 邀请他人协助审议，审议后回到原审批人 | ✅ 必填 |

> ⚠️ 平台内部 Go 常量对照：`JudgeRetPass=Agree`、`JudgeRetRefuse=Reject`、`JudgeRetTransfer=Transfer`、`JudgeRetPreAddApprover=PreAddApprover`、`JudgeRetNextAddApprover=NextAddApprover`、`JudgeRetConsultant=Consultant`。

---

## 任务节点状态（GetInstanceTaskList.List[].Status）

| 枚举值 | 展示 | 说明 |
|--------|------|------|
| `Running` | 🔄 进行中 | **可审批**：正在等待处理人操作 |
| `Succeed` | ✅ 已完成 | 节点已通过，不可再审批 |
| `Failed` | ❌ 已失败 | 节点被拒绝，不可再审批 |
| `Pending` | ⏳ 待激活 | 前置节点未完成，尚未激活 |
| `Skipped` | ⏭️ 已跳过 | 条件分支未命中，节点被跳过 |

> 只有 `Running` 状态的节点才能审批。

---

## 流程单整体状态（DescribeWorkflowInstance.Status）

| 枚举值 | 展示 | 是否可审批 |
|--------|------|-----------|
| `Running` | 🔄 进行中 | ✅ 可审批（若你是当前处理人） |
| `Succeed` | ✅ 已完成 | ❌ 不可审批 |
| `Failed` | ❌ 已失败 | ❌ 不可审批 |
| `Revoked` | ↩️ 已撤回 | ❌ 不可审批 |
| `Pending` | ⏳ 待处理 | ⚠️ 通常不需要审批 |

---

## 审批方式（HandleMode / Mode）

| 枚举值 | 展示 | 说明 |
|--------|------|------|
| `or` | 或签 | 任一处理人审批即可推进 |
| `and` | 会签 | 所有处理人都审批才推进 |

---

## ID 格式规范

| ID 类型 | 前缀 | 示例 |
|---------|------|------|
| 流程 ID (WorkflowId) | `P` | `P2026051400000274` |
| 流程单 ID (InstanceId) | `T` | `T2026051400014945` |
| 任务节点 ID (TaskId) | `N` | `N2026051400073742` |
| 处理记录 ID (HandleId) | 数字 | `123456` |
