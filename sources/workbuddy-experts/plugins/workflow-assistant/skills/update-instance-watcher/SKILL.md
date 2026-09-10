---
name: update-instance-watcher
description: |
  汇金工作流 — 更新流程单关注人技能。为流程单添加或移除关注人（关注人可收到流程单进度通知）。
  触发词：关注流程单、添加关注、取消关注、我要关注这个单子、加关注人、移除关注人、不再关注
---

# update-instance-watcher

## 这个技能做什么

为指定流程单添加或替换关注人。这是**写操作**。

## 唯一可用工具

`UpdateInstanceFollowers`

参数：
- `InstanceId`（string，必填）：流程单 ID（T 开头）
- `Users`（array，必填）：关注人 RTX 列表，如 `["justinke"]`
- `IsReplace`（boolean，必填）：`true` = 替换关注人，`false` = 追加关注人

## 约束

- **InstanceId 是必填参数**（T 开头）。如果用户没给，请求用户提供。
- 🚨 **必须用 `mcp_call_tool` 调用此工具，不能用 `mcp__` 前缀的内部调用方式**。此工具的两个参数（Users 是 array、IsReplace 是 boolean）都会被内部调用链的序列化 bug 损坏，只有 `mcp_call_tool` 能正确传递。
  正确格式：`mcp_call_tool(serverName="huijin-workflow", toolName="UpdateInstanceFollowers", arguments="{\"InstanceId\":\"T...\",\"Users\":[\"rtxname\"],\"IsReplace\":false}")`
- **只调用 1 次**。成功即完成，失败则提示错误原因（不要重试）。
- 如果用户只说"关注"，默认 `IsReplace: false`（追加模式），Users 填用户指定的 RTX。
- 如果用户说"取消关注"/"移除关注"，则把当前用户从 Users 中排除后 `IsReplace: true`（替换模式）。
- 如果遇到 "must be array" / "must be boolean" 错误，**不要重试**，直接告知用户到平台手动操作：https://huijin.woa.com/flow/apply/detail/{InstanceId}

## 执行流程

1. 确认 InstanceId（T 开头）
2. 确认意图：追加关注（IsReplace=false）还是替换关注人（IsReplace=true）
3. 确认 Users 列表（默认当前用户）
4. 用 `mcp_call_tool` 调用 UpdateInstanceFollowers
5. 展示结果

## 输出格式

成功：
```markdown
✅ 已更新流程单 {InstanceId} 的关注人：{Users}

后续状态变更将通知到以上关注人。
```

失败（不要重试，直接输出）：
```markdown
❌ 操作失败：{错误原因}

建议到平台手动操作：https://huijin.woa.com/flow/apply/detail/{InstanceId}
```

## 输出末尾

```markdown
> 以上操作均通过流程平台（https://huijin.woa.com/flow/apply/detail/{InstanceId}）
```
