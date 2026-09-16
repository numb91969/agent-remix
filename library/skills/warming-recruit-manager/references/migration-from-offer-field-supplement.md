# 从 `offer-field-supplement` 融合到 `warming-recruit-manager`

## 1. 融合结论

`warming-recruit-manager` 保留为主 Skill。原 `offer-field-supplement` /「导师上级信息收集」能力并入主 Skill，作为场景 G「导师/上级/入职岗位字段补充」。

## 2. 资源迁移关系

| 原路径 | 新路径 | 说明 |
|---|---|---|
| `campus-mentor-supplementV16-0612/config/field_mappings.json` | `warming-recruit-manager-skill/config/supplement/field_mappings.json` | 字段映射配置 |
| `campus-mentor-supplementV16-0612/scripts/*.py` | `warming-recruit-manager-skill/scripts/supplement/` | 字段补充 Step 脚本 |
| `campus-mentor-supplementV16-0612/sql/*.sql` | `warming-recruit-manager-skill/sql/supplement/` | 字段补充 SQL 模板 |
| `campus-mentor-supplementV16-0612/templates/confirm_template.html` | `warming-recruit-manager-skill/templates/supplement/confirm_template.html` | 确认页模板 |
| `campus-mentor-supplementV16-0612/output/` | `warming-recruit-manager-skill/output/supplement/` | 运行产物目录 |
| `campus-mentor-supplementV16-0612/references/implementation_details.md` | `warming-recruit-manager-skill/references/supplement-flow.md` + `supplement-field-mapping.md` + `supplement-api-and-auth.md` + `supplement-output-and-notify.md` | 实现细节重组为四个分主题文件 |
| `campus-mentor-supplementV16-0612/references/notification_guide.md` | `warming-recruit-manager-skill/references/supplement-output-and-notify.md` | 通知配置指南 |
| `campus-mentor-supplementV16-0612/references/automation_guide.md` | `warming-recruit-manager-skill/references/supplement-output-and-notify.md` | Automation 配置指南 |
| `campus-mentor-supplementV16-0612/references/mcp_queries.md` | SQL 文件迁移到 `sql/supplement/`，查询逻辑说明见 `supplement-field-mapping.md` | MCP 查询说明 |

## 3. 命名变化

- 主 Skill 名称：保留 `warming-recruit-manager`。
- 原 Skill 名称：`offer-field-supplement` 不再作为并列主 Skill。
- 对外场景名：`导师/上级/入职岗位字段补充`。
- API 默认服务：统一为正式 `recruit-mcp`。

## 4. 行为变化

- 字段补充不再单独触发一个 Skill，而是通过场景 G 进入。
- 「通知导师/上级」默认走场景 F；只有补充、回写、空字段、确认页等意图才走场景 G。
- 字段补充支持正式聘用制，但保温经营默认不纳入正式聘用制。
- 生产回写前必须二次确认，且不覆盖详情页已有值。

## 5. 环境变量与配置路径变化

| 旧名称 | 新名称 |
|---|---|
| `OFFER_SUPPLEMENT_WEBHOOK` | `WARMING_SUPPLEMENT_WEBHOOK` |
| `OFFER_SUPPLEMENT_CONFIG` | `WARMING_SUPPLEMENT_CONFIG` |
| `OFFER_FIELD_SUPPLEMENT_CURRENT_USER` | `WARMING_RECRUIT_MANAGER_CURRENT_USER` |
| `~/.config/offer-field-supplement/config.local.json` | `~/.config/warming-recruit-manager/supplement.local.json` |

## 6. 兼容建议

如用户仍说 `offer-field-supplement` 或「导师上级信息收集」，应路由到场景 G，并说明该能力已合入 `warming-recruit-manager`。
