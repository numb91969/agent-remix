# 发布包清单

- 目标仓库：https://github.com/numb91969/agent-remix
- 发布形态：单仓库、单 Skill、物化资源；
- 生成时间：2026-09-16（Asia/Shanghai）；
- 运行入口：SKILL.md；
- 运行索引：library/index.json；
- 构建方式：Python 3.9+ 标准库，正常使用不联网。

## 发布包统计

| 内容 | 数量 | 位置 |
| --- | ---: | --- |
| 专家 prompt | 1004 | library/agents/ |
| 合并目录技能 | 721 | library/index.json |
| 随包技能目录 | 971 | library/skills/ |
| agent-skill 绑定 | 929 | library/index.json |
| 缺失记录 | 0 | library/index.json |

971 个随包技能包括合并目录中登记的技能，以及从本地 WorkBuddy 插件树发现但没有出现在绑定表中的技能。每个技能保留自己的 SKILL.md；通过绑定关系能定位专家和技能的来源。

## 来源

| 来源 | 证据 |
| --- | --- |
| WorkBuddy 本地专家快照 | local:sources/workbuddy-experts；快照时间记录在 library/index.json |
| jnmetacode/AGENCY-AGENTS-ZH | 上游 URL 和 commit 保存在每个 agent 条目 |
| msitarzewski/AGENCY-AGENTS | 上游 URL 和 commit 保存在每个 agent 条目 |

## 随包纳入

- Skill 主说明、Codex 元数据和标准库脚本；
- 1004 份物化 prompt；
- 971 个技能目录的 SKILL.md 及经审计的文本/配置支持文件；
- agent 与 skill 的绑定、来源相对路径、哈希、构建策略和排除记录；
- 一个读书知识库助手的最小生成示例。

## 明确排除

- SSH 私钥、API key、token、cookie、session、master key、.env 和本机账号配置；
- 绝对路径、绝对软链、缓存、node_modules、数据库数据集、语料库、音视频、字体、模型和运行时二进制；
- 需要外部 API、私有 MCP、付费服务、内网、.NET 或专用账号才能工作的支持文件；
- 原维护目录中的 SQLite/CSV/XLSX 归档、源仓库快照、头像、过程性 Remix 产物和发布过程文件。它们已经从当前发布树移除；当前 Skill 不依赖它们。

“物化”只表示文本和安全支持文件已经随包提供，不表示某个技能所描述的供应商服务或本地软件已经安装。依赖判断以 library/index.json 的 excluded_files 和 Skill 正文为准。

## 复现与检查

维护者在有源快照的工作区中运行：

~~~sh
python3 scripts/build_library.py \
  --catalog catalog/agency_agents_merged/merged_catalog.db \
  --source-root . \
  --output ./library \
  --force
python3 scripts/agent_remix.py stats
python3 scripts/audit_export.py .
git diff --check -- . ':(exclude)library'
~~~

提交前要求 missing_records 为 0，审计 high severity 为 0。上游内容的许可证仍需逐项核对。
