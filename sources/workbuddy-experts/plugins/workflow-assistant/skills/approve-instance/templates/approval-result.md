# 展示模板：审批执行结果（approval-result）

## 用途
在 `CompleteWorkflowInstance` 调用完成后，向用户呈现操作结果与后续可用操作。

---

## 成功场景

### 通用成功模板

````markdown
✅ 审批操作已成功提交

| 项目 | 内容 |
|------|------|
| 流程单 | {Title}（`{InstanceId}`） |
| 节点 | {CurrentTaskName} |
| 操作 | {✅ 同意 / ❌ 拒绝 / 🔀 转办 / ⬅️ 前置加签 / ➡️ 后置加签 / 💬 参议} |
| 审批意见 | {Opinion 或 "（无意见）"} |
| 新处理人 | {NewApprover，逗号分隔；无则省略此行} |
| 提交时间 | {当前时间} |

{根据 JudgeRet 追加对应的流转说明}
````

### 按操作追加的流转说明

| 操作 | 追加说明 |
|------|---------|
| Agree | 流程已流转到下一节点，可查看详情跟踪进度。 |
| Reject | 流程已按配置终止或退回上一节点。 |
| Transfer | 当前任务已转交给 `{NewApprover}` 处理，你不再是本节点审批人。 |
| PreAddApprover | 已在当前节点前追加 `{NewApprover}`，将由其先处理。 |
| NextAddApprover | 已在当前节点后追加 `{NewApprover}`，将由其后续处理。 |
| Consultant | 已邀请 `{NewApprover}` 参议；参议完成后任务仍会回到你手上。 |

### 撤回提示（根据 Step 2 探测结果追加）

- 若「审批后可撤回」：
  ```markdown
  💡 你还可以在流程单详情页对本次审批进行撤回。
  ```
- 若「审批后不可撤回」：
  ```markdown
  🚨 该节点审批一经提交不可撤回，如需变更请联系流程发起人。
  ```

---

## 失败场景

````markdown
❌ 审批操作失败：{错误原因}

可能原因：
- 你不是当前节点的处理人（无权限）
- 任务已被其他处理人处理（或签场景下已被他人抢先审批）
- 当前节点不支持该操作（如节点不支持转办 / 加签）
- 参数不合法（TaskId / NewApprover 错误）

建议：
- 到平台确认最新状态：https://huijin.woa.com/flow/apply/detail/{InstanceId}
- 若确认状态无异，可稍后重试
````

> 遇到失败**不要自动重试**，先向用户说明并让用户判断。

---

## 后续引导（成功后可追加）

```markdown
---

💡 **接下来可以帮你**：
- 🔍 查看流程单最新详情：`查询 {InstanceId} 的详情`
- 📬 继续处理下一条待办：`查询我的待办`
- ↩️ 撤回该审批（若节点支持）：`撤回 {InstanceId}`
```

---

## 输出末尾（固定）

```markdown
> 以上操作均通过流程平台（https://huijin.woa.com/flow/apply/detail/{InstanceId}）
```
