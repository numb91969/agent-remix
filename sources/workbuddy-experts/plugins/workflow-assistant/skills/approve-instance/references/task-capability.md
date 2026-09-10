# 任务节点能力字段参考（task-capability）

用于在 `GetInstanceTaskDetail` 返回结果中解析当前节点是否支持转办、前置加签、后置加签、参议、审批后撤回等能力。

由于平台字段命名可能演进，本文列出**已知常见字段名**，代码/模型在解析时应按下述优先级依次尝试，取到第一个存在的作为准。

---

## 字段解析优先级

### 1. 是否支持转办（Transfer）

| 优先级 | 字段名 | 类型 | 期望值 |
|-------|-------|------|-------|
| 1 | `AllowTransfer` | bool | true → 支持 |
| 2 | `CanTransfer` | bool | true → 支持 |
| 3 | `TransferConfig.Enable` | bool | true → 支持 |
| 4 | 无字段 | — | **视为不支持** |

### 2. 是否支持前置加签（PreAddApprover）

| 优先级 | 字段名 | 类型 | 期望值 |
|-------|-------|------|-------|
| 1 | `AllowPreAddApprover` | bool | true → 支持 |
| 2 | `CanPreAddApprover` | bool | true → 支持 |
| 3 | `AddApproverConfig.Pre` | bool | true → 支持 |
| 4 | 无字段 | — | **视为不支持** |

### 3. 是否支持后置加签（NextAddApprover）

| 优先级 | 字段名 | 类型 | 期望值 |
|-------|-------|------|-------|
| 1 | `AllowNextAddApprover` | bool | true → 支持 |
| 2 | `CanNextAddApprover` | bool | true → 支持 |
| 3 | `AddApproverConfig.Next` | bool | true → 支持 |
| 4 | 无字段 | — | **视为不支持** |

### 4. 是否支持参议（Consultant）

| 优先级 | 字段名 | 类型 | 期望值 |
|-------|-------|------|-------|
| 1 | `AllowConsultant` | bool | true → 支持 |
| 2 | `CanConsultant` | bool | true → 支持 |
| 3 | `ConsultantConfig.Enable` | bool | true → 支持 |
| 4 | 无字段 | — | **视为不支持** |

### 5. 审批后是否可撤回（RevokeAfterApprove）

| 优先级 | 字段名 | 类型 | 期望值 |
|-------|-------|------|-------|
| 1 | `AllowRevokeAfterApprove` | bool | true → 可撤回 |
| 2 | `CanRevoke` | bool | true → 可撤回 |
| 3 | `RevokeConfig.AfterApprove` | bool | true → 可撤回 |
| 4 | 无字段 | — | **视为不可撤回** |

---

## 展示原则

- 展示给用户时**必须如实**：字段缺失时按「不支持/不可撤回」处理，并在页脚加提示「（该能力字段未返回，按不支持处理）」
- 严禁猜测/伪造节点能力
- 若用户选择的操作与节点能力冲突（如节点不支持后置加签但用户选了 NextAddApprover），必须拦截并让用户重新选择，不得直接调用 `CompleteWorkflowInstance`

---

## 审批方式（Handler List Mode）

`GetInstanceTaskDetail` 中通常有 `HandleMode` 或 `Mode` 字段：

| 枚举值 | 展示 | 说明 |
|--------|------|------|
| `or` | 或签（任一人审批即可） | 任一处理人审批即可推进 |
| `and` | 会签（全部审批才通过） | 所有处理人都审批后才推进 |

---

## JudgeRet 与操作能力的对应关系

| JudgeRet | 对应平台 Go 常量 | 需要检查的能力 | NewApprover 是否必填 |
|----------|---------------|--------------|-------------------|
| `Agree` | `JudgeRetPass` | 无 | 否 |
| `Reject` | `JudgeRetRefuse` | 无 | 否 |
| `Transfer` | `JudgeRetTransfer` | 转办 | ✅ 是 |
| `PreAddApprover` | `JudgeRetPreAddApprover` | 前置加签 | ✅ 是 |
| `NextAddApprover` | `JudgeRetNextAddApprover` | 后置加签 | ✅ 是 |
| `Consultant` | `JudgeRetConsultant` | 参议 | ✅ 是 |
