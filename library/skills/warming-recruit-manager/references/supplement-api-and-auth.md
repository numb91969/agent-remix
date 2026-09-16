# 场景 G：API 与鉴权说明

## 1. 统一 API 口径

字段补充场景统一使用正式 `recruit-mcp`。默认能力名称：

```text
recruit-mcp.SearchAPI
recruit-mcp.CallAPI
recruit-mcp.CallDB
```

历史 `recruit-mcp-test` 只视为旧文档/旧脚本残留，不作为默认调用方式。

## 2. SearchAPI 关键词

| 用途 | query |
|---|---|
| 详情查询 | `录用详情` |
| 字段写入 | `录用更新` |
| 写入失败后校验 | `录用校验` |

必须先通过 `SearchAPI` 发现能力和参数详情，再用返回的原始完整 `apiId` / `queryId` 调用 `CallAPI` 或 `CallDB`。禁止凭猜测构造 API ID。

## 3. 鉴权原则

1. Step 1 HRData 查询使用当前登录用户的数据权限。
2. Step 2 招聘系统详情复查使用当前用户招聘系统鉴权。
3. Step 6 字段回写使用当前用户招聘系统鉴权。
4. 不允许脚本、文档或配置中内置 token、cookie、账号密码、私钥或服务账号密钥。
5. 组织视角查询必须遵循 `SKILL.md` 中的防越权规则。

## 4. 回写 payload

```json
{
  "offer_id": "string",
  "operator_rtx": "当前确认人 RTX",
  "request_id": "UUID",
  "version": "二次详情查询返回的版本号",
  "fields": {
    "post_name_cn": "入职岗位拟写入值",
    "tutor": { "staff_id8": "...", "name_en": "..." },
    "leader": { "staff_id8": "...", "name_en": "..." },
    "leader_post": { "post_id8": "..." }
  },
  "audit": {
    "source": "warming-recruit-manager.scene_g_supplement",
    "confirmed_at": "ISO-8601 datetime",
    "before_values": {},
    "after_values": {},
    "skipped_existing_fields": {},
    "overwrite_confirmed": false
  }
}
```

## 5. 写入约束

- `tutor` / `leader` 必须同时带 `staff_id8 + name_en`。
- `leader_post` 只传 `post_id8`。
- 字段级判断，不按整单覆盖。
- Step 6 当前详情页字段有值则跳过。
- 任一字段校验失败，只跳过该字段或该单据，并在结果中记录原因。

## 6. 私有配置

本地私有配置示例见：

```text
config/supplement/private_config.example.json
```

真实 webhook 或本地敏感配置应放在用户本机私有路径或环境变量中，不得提交到 Skill 仓库。
