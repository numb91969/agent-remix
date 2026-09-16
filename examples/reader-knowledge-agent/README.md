# 读书知识库助手：最小生成示例

这是一个可以直接复制到 Codex 或 WorkBuddy 的最小示例，用来展示多专家 Remix 的结果形态。

来源组合：

- workbuddy:LlmWiki：文件型知识库的 ingest、query、lint、交叉引用和冲突标注；
- workbuddy:PersonalKnowledgeArchitect：Zettelkasten、PARA、LYT、原子笔记和 MOC；
- personal-knowledge-architect：将上述方法落成可检索、可复用的笔记流程，按 direct 方式随包提供。

本示例只处理用户提供的本地文件或对话内容，不调用外部 API，不要求 Notion/Obsidian 账号，也不依赖 init_wiki.sh。工具配置只作为可选建议，不能假设已经安装。

文件：

- system_prompt.md：最终系统提示词；
- provenance.json：来源、保留内容和依赖裁决。
