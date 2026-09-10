# Agent Remix

这是本地 WorkBuddy 专家目录、两套 AGENCY-AGENTS 源码和企业智能体 Remix 产物的可复现归档，并包含把多专家能力融合成单个企业 agent 的 `agent-remix` Skill。

## 已归档资产

- WorkBuddy 专家目录：446 条已获取记录，含专家数据库、分类、标签、技能关系、验证结果和 446 份 prompt 快照；
- 合并目录：WorkBuddy + AGENCY-AGENTS 中英文共 1004 条 agent 记录、角色族/领域/技能/agent-skill 关系和 `agent_list_merged.xlsx`；
- 来源快照：`jnmetacode/AGENCY-AGENTS-ZH` 与 `msitarzewski/AGENCY-AGENTS`；
- WorkBuddy 技能快照：包元数据、专家 Markdown、`SKILL.md` 和可分发的 references；
- Remix 成品：`CFO 赵公明`、`CHO 张亚子` 的系统提示词、安装报告和头像；
- 方法 Skill：`skills/agent-remix/`，包含检索、融合、技能依赖裁决、发布验证、报告和 GitHub 脱敏导出规范。

## 目录

```text
skills/agent-remix/       # 可复用 Skill
catalog/workbuddy_expert_catalog/
                           # WorkBuddy 446 专家数据库、prompt、技能索引
catalog/agency_agents_merged/
                           # 1004 条合并目录、数据库、Excel、分组和 Remix 原始产物
sources/AGENCY-AGENTS-ZH/ # AGENCY 中文源码快照
sources/AGENCY-AGENTS/   # AGENCY 英文源码快照
sources/workbuddy-experts/
                           # WorkBuddy 包的可移植文本快照
remixes/                  # 按职位+名字整理的自定义 agent 成品
EXPORT_MANIFEST.md        # 纳入/排除、路径脱敏、体积和来源说明
```

## 使用 Skill

在 Codex 中调用 `$agent-remix`，提供目标职位、称谓/身份、边界、需要绑定的工具和发布渠道。Skill 会要求先建立来源证据表，再合并多个专家，而不是把一个来源直接改名；对外部运行时、私有连接器、`.NET`、密钥和本机软链会单独做依赖裁决。

每个 Remix 目录都应同时保存最终 prompt、来源/技能说明和安装报告。发布到企业智能体页面后，报告必须记录列表验证结果；未发布成功不能标记为已安装。

## 运行审计

```bash
python3 skills/agent-remix/scripts/audit_export.py .
```

仓库内的目录和数据库已将本机绝对路径改成相对路径；原始快照中的来源 URL、commit 和内容哈希仍保留。WorkBuddy 运行时、缓存、数据集、媒体和不可移植软链按 `EXPORT_MANIFEST.md` 规则排除。

## 来源与许可

本仓库是用户本地研究和 Remix 归档。各来源仓库/专家包的许可证、作者和再分发范围以对应目录中的 LICENSE/README 和上游仓库为准；使用者应在公开分发前逐项核对。不要把本仓库当作 WorkBuddy 官方发行包，也不要将未授权的企业数据或凭据加入其中。
