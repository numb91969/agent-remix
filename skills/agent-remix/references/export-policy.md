# GitHub 导出策略

目标是让仓库保存可复现的专家知识资产和 Remix 证据，同时不把本机环境、凭据或不必要的大文件带出。

## 默认纳入

- `experts.db`、`merged_catalog.db` 及其 CSV/JSON/XLSX 导出；
- 原始专家 `agents/*.md`、`SKILL.md`、技能 references、包的 manifest/license/README；
- 两套 AGENCY-AGENTS 的源码快照和 commit 信息；
- WorkBuddy 专家 prompt 快照、技能索引、下载/验证结果；
- 自定义 agent 系统提示词、来源证据表、技能映射和安装报告；
- 重建/审计脚本和 `EXPORT_MANIFEST.md`。

## 默认排除

- SSH 私钥、API key、token、cookie、`.env`、master key、账号 session；
- `node_modules`、`.git`、缓存、日志、临时文件、构建产物；
- 用户目录绝对软链、未解析的挂载点和只在本机存在的 socket；
- 体积很大的数据库、CSV 数据集、音视频、字体、模型、截图和运行时二进制，除非用户明确要求并单独审计；
- 含个人信息、客户数据、企业内部秘密或无法确认分发许可的原始文件。

被排除但对复现有价值的文件，记录在 `EXPORT_MANIFEST.md`：相对路径、大小、SHA-256、排除原因和可选获取方式。不要把秘密的内容或密钥值写入 manifest。

## 提交前检查

```bash
python3 skills/agent-remix/scripts/audit_export.py .
git status --short
git diff --stat
```

发现 high severity 时先删除/替换再提交。对二进制和源仓库快照检查总大小；GitHub 仓库不应因为一个专家包的数据库或媒体附件失控膨胀。
