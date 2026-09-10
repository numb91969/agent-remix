# 远程 MCP 接入方式

本文件说明如何在 WorkBuddy 中接入远程 `requirement-assistant` MCP Server。

## 必要前提

远程模式通过太湖网关接入，请求需携带以下 Header：

- `Authorization: Bearer <token>`（若服务端开启了统一认证）
- `X-Tapd-Access-Token: <tapd_personal_token>`

其中：

- `Authorization` 用于访问 MCP Server 本身
- `X-Tapd-Access-Token` 用于在服务端解析真实 TAPD 用户身份

## 在 WorkBuddy 中添加 MCP

在 WorkBuddy 中执行：

1. 打开 `Settings -> MCP`
2. 点击 `Add MCP`
3. 选择远程 MCP Server
4. 填入服务名：`requirement-assistant`
5. 填入远程地址
6. 配置请求头

## 配置示例

可参考如下结构：

```json
{
  "mcpServers": {
    "requirement-assistant": {
      "transportType": "streamable-http",
      "url": "https://your-mcp-host.example.com",
      "headers": {
        "Authorization": "Bearer <mcp_server_auth_token>",
        "X-Tapd-Access-Token": "<tapd_personal_access_token>"
      }
    }
  }
}
```

若服务端未开启 Bearer 认证，可只保留：

```json
{
  "mcpServers": {
    "requirement-assistant": {
      "transportType": "streamable-http",
      "url": "https://your-mcp-host.example.com",
      "headers": {
        "X-Tapd-Access-Token": "<tapd_personal_access_token>"
      }
    }
  }
}
```

## 本地文件位置

也可直接修改：

- `~/.workbuddy/mcp.json`

修改后重新加载 MCP 配置。

## 联调检查

接入完成后，优先检查：

1. 能否在 MCP 工具列表中看到 `start_new_requirement`
2. 能否看到 `enrich_existing_requirement`
3. 若服务端开启 expert 暴露，能否看到：
   - `get_story_template_list`
   - `get_story_template_detail`
   - `get_required_fields`
   - `get_enrichment_modules`
   - `get_story_detail`
   - `preview_enrichment`

## 常见问题

### 工具列表为空

优先检查：

- MCP 地址是否正确
- 服务端是否已启动
- Bearer Token 是否正确

### 返回缺少 `X-Tapd-Access-Token`

说明客户端没有把 TAPD Token 带到请求头。

补充该 Header 后重试。

### 401 / 403

优先检查：

- `Authorization` 是否正确
- `X-Tapd-Access-Token` 是否有效
- Token 是否能解析出真实 TAPD 用户
