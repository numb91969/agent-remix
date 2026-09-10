# WorkBuddy Windows Connector 连接异常证据包

## 事件范围

- 客户 ID：`WB-373A-D176-7FF9-73AC`
- 时间窗口：2026-07-29 18:08-18:25（Asia/Shanghai）
- 影响：WorkBuddy 界面显示 Connector 已连接，但授权后工具未加载；重复授权不能恢复。

## 已验证事实

1. 18:08:51，Device Flow 获得用户批准。
2. 18:08:52，`tongzhou_fin_research_cli` 成功换取可续期 Token。
3. 18:09:27 和 18:10:44，同一客户的 OAuth 会话调用 `/mcp/tongzhou-research` `tools/list`，Gateway 均返回 HTTP 200。
4. 18:25:16 和 18:25:44，WorkBuddy 原生 Connector 再次创建并批准 Authorization Code 请求，但没有观察到后续 `/oauth/token` 交换。
5. 客户最新有效 API Key 的 `last_used_at` 为空；未观察到该 Key 对 MCP 的有效调用。

以上记录不包含 API Key、Access Token、Refresh Token、短信验证码或手机号明文。

## 故障边界

- Gateway、账号状态、OAuth Device Flow、Token 签发和统一 MCP `tools/list` 均正常。
- npm stdio proxy 链路已实际返回工具。
- 异常集中在 WorkBuddy Windows 客户端的 Connector 选择、原生 OAuth 回调/Token 交换或本地 Connector 缓存。
- “浏览器授权已批准”不能作为“客户端已连接”的完成条件。

## 请 WorkBuddy 客户端团队检查

1. `workbuddy://workbuddy/mcp/<connector-id>/oauth/callback` 返回客户端后，是否继续执行 Authorization Code + PKCE Token 交换。
2. UI 显示的 Connector ID 是否与实际发起 MCP 请求的 Connector ID 一致。
3. 本地 Connector marketplace 更新后，`mcp.json` 是否被旧缓存覆盖。
4. 自定义 Connector 的 `Authorization` Header 或 stdio `command/args` 是否被保存并实际加载。
5. Windows 下解绑、重新绑定和客户端重启后，是否仍复用已失效的动态 client。

## 我方缓解措施

- npm 安装器新增 `repair --target workbuddy`。
- 修复仅覆盖并备份本机 Connector 的 `mcp.json`，使用已验证的 stdio Device Flow，不在配置中保存 Token。
- 修复成功条件包括远端 `tools/list` 返回至少一个工具。
- Portal 将 Token 换取和真实 MCP 调用分开显示，避免“假连接成功”。
