# WorkBuddy + Agency Agents 合并索引

构建时间：`2026-09-09T16:58:01+00:00`

本索引保留 WorkBuddy 本地专家包、Agency Agents 中文仓库、Agency Agents 英文仓库三类来源。相同 `domain + role_stem` 的记录归入同一角色族，中文、英文和 WorkBuddy 包作为独立变体保留。

## 来源与规模

| 来源 | 记录数 | 版本/位置 |
|---|---:|---|
| Agency Agents 中文仓库 | 278 | `b08f35c07c62d985d0c60a4faaa7304ad4aee686` |
| Agency Agents 英文仓库 | 280 | `6d29a9b08785a0e49ffc9818bbdd381164c2df5f` |
| WorkBuddy 本地专家包 | 446 | `catalog/workbuddy_expert_catalog/experts.db` |

## 分类分组

| 分类 | 专家记录 | 角色族 | 入口 |
|---|---:|---:|---|
| 公司经营 / Company | 7 | 7 | [分组](groups/company/README.md) |
| 内容创作 / Content & Creative | 48 | 48 | [分组](groups/content-creative/README.md) |
| 数据智能 / Data & AI | 70 | 57 | [分组](groups/data-ai/README.md) |
| 教育学术 / Education & Academia | 24 | 19 | [分组](groups/education/README.md) |
| 技术工程 / Engineering | 153 | 119 | [分组](groups/engineering/README.md) |
| 金融投资 / Finance | 52 | 47 | [分组](groups/finance/README.md) |
| 游戏空间 / Game & Spatial | 78 | 34 | [分组](groups/game-spatial/README.md) |
| 全球发展 / Global Development | 21 | 21 | [分组](groups/global-development/README.md) |
| 医疗健康 / Healthcare | 3 | 3 | [分组](groups/healthcare/README.md) |
| 行业顾问 / Industry Consulting | 34 | 34 | [分组](groups/industry-consulting/README.md) |
| 法务安全 / Legal & Security | 51 | 41 | [分组](groups/legal-security/README.md) |
| 营销增长 / Marketing & Growth | 130 | 87 | [分组](groups/marketing-growth/README.md) |
| 运营人力 / Operations & HR | 19 | 19 | [分组](groups/operations-hr/README.md) |
| 产品设计 / Product & Design | 50 | 36 | [分组](groups/product-design/README.md) |
| 项目质量 / Project & Quality | 57 | 42 | [分组](groups/project-quality/README.md) |
| 销售商务 / Sales & Commerce | 35 | 24 | [分组](groups/sales-commerce/README.md) |
| 战略专项 / Strategy & Specialized | 117 | 69 | [分组](groups/strategy/README.md) |
| 供应链 / Supply Chain | 5 | 5 | [分组](groups/supply-chain/README.md) |
| 客户支持 / Customer Support | 13 | 7 | [分组](groups/support/README.md) |
| 腾讯专区 / Tencent | 37 | 37 | [分组](groups/tencent/README.md) |

## 文件

- `merged_catalog.db`：SQLite 合并数据库，含 agents、families、domains、skills、sources。
- `agents.csv` / `agents.json`：全部来源的专家记录。
- `families.csv` / `families.json`：按角色族去重后的变体索引。
- `domains.csv` / `domains.json`：重新分类后的大类统计。
- `skills.csv` / `skills.json`：WorkBuddy 包内 skill 去重清单；两个 GitHub 仓库当前没有 `SKILL.md` 目录。
- `agent_skills.csv` / `agent_skills.json`：WorkBuddy 专家与 skill 的完整关联。
- `agents/by-source/`、`agents/by-domain/`、`agents/by-family/`：指向原始 agent 文件的软链。
- `skills/by-agent/`、`skills/by-skill/`：按专家和按 skill 的软链入口。
- `groups/<domain>/README.md`：按新分类分组的可读索引。

## 原始来源

- [AGENCY-AGENTS-ZH](https://github.com/jnmetacode/AGENCY-AGENTS-ZH)
- [AGENCY-AGENTS](https://github.com/msitarzewski/AGENCY-AGENTS)
- WorkBuddy 本地包：`sources/workbuddy-experts/plugins`
