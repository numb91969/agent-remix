# 专家目录与常用查询

本 Skill 面向三类本地来源：WorkBuddy 专家目录、合并后的 AGENCY-AGENTS 目录，以及两者的原始 Markdown。实际路径以当前工作区为准，不要把下面的示例绝对路径写入最终提示词。

## SQLite 表

`workbuddy_expert_catalog/experts.db` 常见表：

- `experts`：专家名称、slug、类别、提示词路径、包路径、状态；
- `categories`：类别树和计数；
- `expert_tags`：专家与标签；
- `skills` / `expert_skills`：技能元数据和专家绑定关系；
- `verification`：抓取/下载/完整性校验结果；
- `catalog_meta`：快照时间、来源和统计。

`agency_agents_merged/merged_catalog.db` 常见表：

- `agents`：来源、名称、路径、角色摘要和状态；
- `families`：角色族；
- `domains`：领域分组；
- `skills`：技能目录；
- `agent_skills`：agent 与技能关系；
- `sources` / `meta`：仓库、提交号、构建信息。

## 查询示例

```bash
sqlite3 workbuddy_expert_catalog/experts.db \
  "select name, category, prompt_path from experts
   where lower(name || ' ' || coalesce(category,''))
   like '%finance%' limit 50;"

sqlite3 agency_agents_merged/merged_catalog.db \
  "select a.name, d.name, a.path
   from agents a left join domains d on d.id=a.domain_id
   where lower(a.name || ' ' || coalesce(a.summary,''))
   regexp 'finance|account|hr|human|payroll|tax';"
```

如果 SQLite 版本没有 `regexp`，使用多个 `like` 或先导出 CSV 再用 `rg`。检索结果要回到原始 Markdown 阅读，不要只依据摘要或文件名。

## 来源记录

至少保存：来源库、仓库 URL、commit/ref、文件相对路径、文件 SHA-256、抓取时间。生成产物时使用相对路径和相对软链；绝对路径只能留在本地审计报告，不能写进可发布 agent 或 GitHub 产物。
