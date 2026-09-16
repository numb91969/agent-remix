# GitHub 导出策略

目标是让下载者只取得一个仓库，就能调用 agent-remix 的检索、阅读和提取能力。

## 发布包纳入

- SKILL.md、agents/openai.yaml 和标准库脚本；
- library/ 下的物化专家 prompt、技能正文、允许的文本/配置支持文件和 index.json；
- examples/ 中最多一个小型生成 agent 示例；
- 来源、依赖、分组和安全规则等短参考文档。

library/ 不使用运行时软链。维护阶段可以用相对软链表示关系，但生成发布包时必须复制文本并把关系写入索引。这样 Codex、WorkBuddy 或普通文件夹安装都不需要第二次下载。

## 依赖裁决

- 纯 prompt、Markdown、表格和本地常见文本处理：direct，直接随包带入；
- 需要保持本地关联的技能：维护时可标记 symlink-audit，发布时物化并保留来源关系；
- 外部 API、私有 MCP、账号/token、付费服务、内网、.NET、不可用的二进制、大型数据集：exclude，只保留能力说明和排除理由；
- 只要技能正文仍然要求调用供应商服务，就不能因为文件被打包而宣称它是离线能力。

## 永不纳入

- SSH 私钥、API key、token、cookie、.env、session、master key；
- .git、缓存、日志、用户目录绝对路径和绝对软链；
- 音视频、字体、模型、运行时二进制、数据集和超过构建阈值的支持文件。

## 提交前检查

~~~sh
python3 scripts/audit_export.py .
python3 scripts/agent_remix.py stats
git diff --check -- . ':(exclude)library'
~~~

audit_export.py 的 high severity 必须为 0；index.json 的 missing_records 必须为 0，除非发布说明明确记录了有意排除。
