# 专家目录与常用查询

## 运行时目录是唯一入口

安装后的 Skill 不依赖 SQLite。'library/index.json' 是运行时目录，记录：

- 'agents'：每个专家的名称、描述、领域、来源、相对路径、哈希和绑定技能；
- 'skills'：每个已物化的 'SKILL.md'、安全支持文件、排除文件和来源；
- 'bindings'：专家与技能的原始关系；
- 'missing'：构建时发现但没有纳入的记录。

先使用标准库脚本检索，再阅读完整 prompt 和技能正文：

~~~sh
python3 scripts/agent_remix.py stats
python3 scripts/agent_remix.py search "财务 现金流"
python3 scripts/agent_remix.py search "读书 知识库" --kind all --limit 20
python3 scripts/agent_remix.py show-agent workbuddy:LlmWiki
python3 scripts/agent_remix.py show-skill personal-knowledge-architect --files
~~~

脚本不会联网，也不会修改索引。'extract-agent' 会复制 prompt、绑定技能和 'provenance.json'，用于生成 WorkBuddy/Codex 的下一步成品。

## 维护时的 SQLite 输入

只有在刷新发布包时才读取维护者输入的 'merged_catalog.db'：

- 'agents'：来源、名称、路径、角色摘要和状态；
- 'skills'：技能目录和本地源目录；
- 'agent_skills'：agent 与技能关系；
- 'families'、'domains'、'sources'、'meta'：分组、来源和构建证据。

~~~sh
python3 scripts/build_library.py \
  --catalog /path/to/merged_catalog.db \
  --source-root /path/to/source/repository \
  --output ./library \
  --force
~~~

## 来源记录

至少保存：来源库、仓库 URL、commit/ref、文件相对路径、文件 SHA-256、构建时间。发布包只保存相对路径和物化文本；绝对路径、本机软链、账号信息和凭据不得进入 'library/'。
