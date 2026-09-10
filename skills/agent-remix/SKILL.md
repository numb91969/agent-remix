---
name: agent-remix
description: "Remix multiple expert prompts and skills into a traceable custom agent, with dependency review, browser publication, and export-safe provenance. Use when creating or revising an agent from a local expert catalog, WorkBuddy package, or AGENCY-AGENTS source."
---

# Agent Remix

将多个已有专家的角色、方法论和技能组合成一个可发布的企业智能体，并保留来源、取舍和依赖记录。先查证再融合，先生成可审阅的产物，再执行外部发布。

## 工作流

### 1. 盘点来源

- 优先读取本地合并目录中的 `merged_catalog.db`、`experts.db`、CSV/JSON 索引和每个专家的原始 Markdown。
- 同时查找 WorkBuddy 专家包的 `agents/*.md` 与 `skills/*/SKILL.md`，以及 AGENCY-AGENTS 的中英文源文件。
- 用角色名称、职位同义词、职责、领域标签和技能标签做多维检索；不要只选一个“看起来最像”的专家。通常选 3–8 个互补来源，并保留每个来源的路径和哈希。
- 数据库字段和常用查询见 `references/catalog-schema.md`。

### 2. 构建融合证据表

在写提示词前先建立一张 provenance 表，至少包含：

| 字段 | 内容 |
| --- | --- |
| source_agent | 专家名称、来源库、文件路径 |
| retained | 保留的身份/职责/方法 |
| discarded | 删除的冲突或系统专属指令 |
| skill | 技能名称、路径、调用条件 |
| dependency | 外部连接器、运行时、密钥或数据要求 |
| decision | direct / symlink-audit / exclude 及理由 |

优先保留经过多个来源重复验证的职责、流程、检查清单和输出格式。对冲突内容以目标企业的职责边界、用户明确要求和安全约束为准。

### 3. Remix 系统提示词

按以下顺序写成一个可以独立运行的提示词：

1. 身份和称谓：如果用户指定“只能自称专家名、不得说自己是 AI/Agent/底层模型”，将这段约束放在最开头；除非用户另有要求，不要凭空加入神秘化或模型披露条款。
2. 使命和边界：明确服务对象、决策权限、不能代替的人类审批和需要升级的风险。
3. 核心能力：把来源专家的能力去重、分组、按优先级排列；避免把“团队编排器”的内部命令直接带进单体 agent。
4. 工作协议：输入澄清、分析步骤、证据/假设区分、输出模板、复盘和追踪。
5. 风险控制：财务、人事、法律、隐私、付款、税务等高风险场景必须标注假设、依据、审批人和下一步，不能伪造已执行动作。
6. 技能使用规则：只在满足触发条件时调用技能；调用失败时给出降级路径，不泄露密钥或本地绝对路径。
7. 语言和身份一致性：遵循用户指定名称格式；例如 `职位+名字`，若需保留神话身份，使用“我是 CHO 张亚子（文昌帝君）”这类明确身份而不改变职责边界。

详细的融合方法、冲突处理和交付清单见 `references/remix-method.md`。

### 4. 裁决技能依赖

- **direct**：技能内容自洽、只依赖通用文件/命令/已存在连接器，且目标平台支持；可直接复制或绑定。
- **symlink-audit**：本地需要保留技能与专家包的关联、但运行环境可能变化；在本地索引中用相对软链或 link map 表示，发布包中不要依赖指向用户机器的绝对软链。
- **exclude**：需要 `.NET`、私有 MCP、企业内网、付费数据库、特定凭据、绝对路径、不可复现二进制或法律上不能再分发的资源；保留能力说明和安装前置条件，不把秘密或不可移植文件复制进 agent。

对每个技能检查：触发条件、输入输出、运行时、网络权限、凭据、数据敏感性、许可证。若技能只是“读文件/写 Markdown/常规表格”，优先 direct；若要求外部账号或系统，就在 prompt 中写清“需要用户授权/连接器可用”，并在报告里单列缺失依赖。

### 5. 发布到企业智能体页面

使用用户已经打开的浏览器页面或明确指定的浏览器。填入：名称、简介、欢迎语、系统提示词和可用技能。发布前检查名称格式、身份约束、提示词完整性和技能映射；若页面出现最终发布确认，向用户请求确认后再点击。发布后回读智能体名称/ID/状态，保存截图或页面证据（若工具支持）。

不要把“能写出提示词”当成“已发布成功”；必须验证列表中出现目标 agent，或明确报告停在何处。

### 6. 生成安装报告

每次 remix 产出：

- 最终系统提示词 Markdown；
- `source_agents`、保留内容、删除内容和冲突处理；
- 技能清单、依赖裁决和缺失依赖；
- 发布字段、目标页面、发布时间、验证结果；
- 已知风险、人工审批点和回滚/修订建议。

涉及企业财务、人事、税务、薪酬或法律时，明确“建议/草案/待审批”，不得声称已经记账、付款、报税、录用或修改人事记录。

### 7. 导出到 GitHub

导出“可复现的知识资产”，而不是整机缓存：数据库、CSV/JSON/XLSX、原始提示词、技能文本、来源仓库快照、remix 提示词、安装报告和 `EXPORT_MANIFEST.md`。遵循 `references/export-policy.md`：排除密钥、token、session、缓存、`node_modules`、系统临时文件、不可移植的绝对软链和体积过大的二进制数据。提交前运行 `scripts/audit_export.py <repo>`，处理所有 high severity 结果。

## 默认交付目录

```text
skills/agent-remix/       # 本 Skill
catalog/                  # 专家数据库、索引和本地 prompt
sources/                  # AGENCY-AGENTS 与筛选后的 WorkBuddy 包
remixes/                  # 自定义 agent 的提示词、技能映射、安装报告
scripts/                  # 可重复的盘点、审计和导出脚本
EXPORT_MANIFEST.md        # 纳入/排除规则和文件统计
```

当用户只要求写提示词时，不必自动发布或上传；当用户明确要求发布/上传时，沿用上述验证和安全检查。
