# 展示模板：审批操作二次确认（confirm-approval）

## 用途
在调用 `CompleteWorkflowInstance` 前，通过问答组件让用户对操作参数进行最终确认。

---

## 确认摘要格式

按用户选择的操作动作，套用下面对应的摘要模板：

### 场景 1：同意（Agree）

````markdown
⚠️ 即将执行审批操作 — 请二次确认

| 项目 | 内容 |
|------|------|
| 流程单 | {Title}（`{InstanceId}`） |
| 当前节点 | {CurrentTaskName}（`{TaskId}`） |
| 操作 | ✅ **同意 (Agree)** |
| 审批意见 | {Opinion 或 "（无意见）"} |
| 审批后可撤回 | {✅ 是 / ❌ 否 — 一旦提交不可回退} |

> 提交后本任务将标记为「已同意」，流程将继续流转到下一节点。
````

### 场景 2：拒绝（Reject）

````markdown
⚠️ 即将执行审批操作 — 请二次确认

| 项目 | 内容 |
|------|------|
| 流程单 | {Title}（`{InstanceId}`） |
| 当前节点 | {CurrentTaskName}（`{TaskId}`） |
| 操作 | ❌ **拒绝 (Reject)** |
| 审批意见 | {Opinion 或 "（无意见）"} |
| 审批后可撤回 | {✅ 是 / ❌ 否 — 一旦提交不可回退} |

> 🚨 拒绝后流程将按配置终止或退回，请务必确认。建议填写清晰的拒绝理由。
````

### 场景 3：转办（Transfer）

````markdown
⚠️ 即将执行审批操作 — 请二次确认

| 项目 | 内容 |
|------|------|
| 流程单 | {Title}（`{InstanceId}`） |
| 当前节点 | {CurrentTaskName}（`{TaskId}`） |
| 操作 | 🔀 **转办 (Transfer)** |
| 新处理人 | {NewApprover，逗号分隔} |
| 审批意见 | {Opinion 或 "（无意见）"} |

> 转办后该任务的处理权将交给新处理人，你不再是此节点的审批人。
````

### 场景 4：前置加签（PreAddApprover）

````markdown
⚠️ 即将执行审批操作 — 请二次确认

| 项目 | 内容 |
|------|------|
| 流程单 | {Title}（`{InstanceId}`） |
| 当前节点 | {CurrentTaskName}（`{TaskId}`） |
| 操作 | ⬅️ **前置加签 (PreAddApprover)** |
| 新增审批人 | {NewApprover，逗号分隔} |
| 审批意见 | {Opinion 或 "（无意见）"} |

> 前置加签后，需先由新增审批人处理，通过后再回到你审批。
````

### 场景 5：后置加签（NextAddApprover）

````markdown
⚠️ 即将执行审批操作 — 请二次确认

| 项目 | 内容 |
|------|------|
| 流程单 | {Title}（`{InstanceId}`） |
| 当前节点 | {CurrentTaskName}（`{TaskId}`） |
| 操作 | ➡️ **后置加签 (NextAddApprover)** |
| 新增审批人 | {NewApprover，逗号分隔} |
| 审批意见 | {Opinion 或 "（无意见）"} |

> 后置加签后，你审批通过后，需再由新增审批人处理才会继续流转。
````

### 场景 6：参议（Consultant）

````markdown
⚠️ 即将执行审批操作 — 请二次确认

| 项目 | 内容 |
|------|------|
| 流程单 | {Title}（`{InstanceId}`） |
| 当前节点 | {CurrentTaskName}（`{TaskId}`） |
| 操作 | 💬 **参议 (Consultant)** |
| 参议人 | {NewApprover，逗号分隔} |
| 审批意见 | {Opinion 或 "（无意见）"} |

> 参议不会转移审批权：参议人处理完毕后，任务仍会回到你手上继续审批。
````

---

## 问答组件调用规范

按上面摘要拼好文案后，**必须**通过问答组件（`ask_followup_question` 或平台等价问答工具）弹出确认对话，提供两个选项：

- `确认执行` → 进入 Step 6 调用 `CompleteWorkflowInstance`
- `取消` → 输出「已取消，未做任何变更」并终止流程

用户选择「取消」时的回复模板：

```markdown
已取消 ✅ 本次未执行任何审批操作，流程单 `{InstanceId}` 状态保持不变。

如需重新审批，请再次告诉我。
```

---

## 铁律

🚨 严禁跳过问答组件二次确认直接调用 `CompleteWorkflowInstance`。这是**写操作**，一经提交不可回退。
