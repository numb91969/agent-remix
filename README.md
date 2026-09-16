# agent-remix

一个开箱即用的 Codex / WorkBuddy Skill：从随包提供的 1000+ 专家 prompt 和技能库中检索多个互补来源，审查依赖，生成可追溯、可移植的自定义 agent。

## 这个仓库现在提供什么

- 1004 个已物化的专家 prompt；
- 971 个随 Skill 提供的技能目录，其中包含 721 个合并目录技能和本地发现的未绑定技能；
- 929 条专家与技能绑定关系；
- JSON 运行时索引、来源路径、commit、哈希和排除文件记录；
- 标准库 Python 检索/阅读/提取工具；
- 一个读书知识库助手的最小多专家生成示例。

专家和技能都在 library/ 里面。下载仓库一次即可正常检索和提取，不需要再下载数据库、源仓库或第三方服务。运行时只需要 Python 3.9+ 标准库；实际执行某个技能仍需遵守该技能自己的本地运行前提。

## 安装

在 Codex 中，把仓库根目录复制到配置的技能目录，通常是 ~/.codex/skills/agent-remix/。在 WorkBuddy 中，把同一个根目录复制到它的本地 Skill 目录，并保持 library/ 与 SKILL.md 同级。

安装后调用 $agent-remix，或者直接运行：

~~~sh
cd agent-remix
python3 scripts/agent_remix.py stats
python3 scripts/agent_remix.py search "财务 现金流"
python3 scripts/agent_remix.py search "读书 知识库" --limit 20
python3 scripts/agent_remix.py show-agent workbuddy:LlmWiki
python3 scripts/agent_remix.py show-skill personal-knowledge-architect --files
python3 scripts/agent_remix.py extract-agent workbuddy:PersonalKnowledgeArchitect \
  --output ./exports/personal-knowledge-architect
~~~

检索工具离线运行，不联网、不改写索引。真正的 Remix 由模型依据 SKILL.md 完成：先选多个来源，再合并能力、保留证据、明确排除外部 API/付费服务/凭据和不可移植运行时。

## 目录

~~~text
agent-remix/
├── SKILL.md
├── agents/openai.yaml
├── library/
│   ├── index.json
│   ├── agents/
│   └── skills/
├── scripts/
│   ├── agent_remix.py
│   ├── audit_export.py
│   └── build_library.py
├── references/
└── examples/reader-knowledge-agent/
~~~

## 维护者刷新

发布包中的 library/ 是物化副本。只有在明确刷新来源时，才在包含合并 SQLite 目录和源快照的维护工作区运行：

~~~sh
python3 scripts/build_library.py \
  --catalog catalog/agency_agents_merged/merged_catalog.db \
  --source-root . \
  --output ./library \
  --force
~~~

构建脚本不会联网，跳过凭据、绝对软链、缓存、数据集、二进制和超过阈值的支持文件；所有跳过项写入 index.json。

## 来源与许可

本仓库包含用户本地研究后整理的公开发布包。来源包括本地 WorkBuddy 快照、jnmetacode/AGENCY-AGENTS-ZH 和 msitarzewski/AGENCY-AGENTS；具体 commit、文件路径和依赖裁决见 library/SOURCES.md 与 EXPORT_MANIFEST.md。各上游许可证和再分发范围仍需由使用者自行核对。本仓库不代表 WorkBuddy 官方发行包。
