# 导出清单

- 目标仓库：`git@github.com:wuyinhust/agent-remix.git`
- 本地构建目录：`agent-remix/`
- 导出时间：2026-09-10（Asia/Shanghai）
- 目的：归档专家目录、原始提示词/技能文本、数据库和 Remix 方法，形成可复现的 Agent Remix 研究仓库。

## 来源快照

| 来源 | 记录/范围 | 版本证据 |
| --- | --- | --- |
| WorkBuddy 本地专家目录 | 446 条已获取专家，446 份 prompt | `catalog/workbuddy_expert_catalog/snapshots/expert_center.json`；SHA-256 `dc924682bf5bf700a8ea25acd34f4628c5780173a6ed76a4dc79d736f37f84ec` |
| AGENCY-AGENTS-ZH | 278 条 | commit `b08f35c07c62d985d0c60a4faaa7304ad4aee686` |
| AGENCY-AGENTS | 280 条 | commit `6d29a9b08785a0e49ffc9818bbdd381164c2df5f` |
| 合并目录 | 1004 条 agent、756 个角色族、20 个领域、721 个技能、929 条 agent-skill 关系 | `catalog/agency_agents_merged/merged_catalog.db` |

## 纳入

- `experts.db`、`merged_catalog.db`、CSV/JSON/XLSX 和构建/抓取/验证结果；
- WorkBuddy 的 446 份 prompt 快照、包元数据和分类/技能索引；
- 两套 AGENCY-AGENTS 源码快照；
- WorkBuddy 包的 `agents/*.md`、`SKILL.md`、references、包 manifest、README 和 LICENSE 等文本/配置；
- `CFO 赵公明`、`CHO 张亚子` 的 Remix prompt、安装报告和头像；
- `skills/agent-remix` Skill、参考文档和审计脚本。

## 排除与处理

- 排除 SSH 私钥、API key、token、cookie、master key、`.env`/`.env.example`、session 和本机配置；MCP 配置只在确认不含实际凭据时保留，带 PAT/密钥的文件删除或脱敏；
- 排除 `.git`、`node_modules`、缓存、构建目录、运行时二进制、模型、音视频、字体和图片型 WorkBuddy 包资产（Remix 头像除外）；
- 排除 WorkBuddy `Databases/`、`CSV_Datasets/`、大型 DuckDB/SQLite、`references/corpus/`、`Reference_Texts/`、`render-bundle/`、`vendor/` 和超过 2MiB 的单文件；
- 合并目录的 28MiB inspection NDJSON 临时产物未上传；同一 workbook 和较小的 inspection JSON 已保留；
- WorkBuddy 技能的脚本/第三方依赖不作为完整运行时发行包上传；技能正文和 references 仍保留，缺失运行时在目录与报告中按依赖处理；
- 合并目录和 WorkBuddy 的 agent 索引视图已从本机绝对软链物化为文本副本；`skills` 的重复软链视图未原样上传，数据库、CSV/JSON、prompt 快照和 `sources/workbuddy-experts/` 技能文本保留同样的关联信息。指向 `local qclaw workspace` 的 6 条不可移植软链已删除；
- 数据库和文本索引中的 `local user/...`、`local user/.workbuddy/...` 已改写为仓库相对路径。来源 URL、commit 和内容哈希保留。

## 审计要求

提交前运行：

```bash
python3 skills/agent-remix/scripts/audit_export.py .
```

high severity 结果必须为 0。出现外部软链、绝对路径或体积警告时，应确认是否属于来源元数据、删除或改写后再提交。该清单不记录任何秘密值。
