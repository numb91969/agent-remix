# 腾讯探元文博专家（Tanyuan Cultural Heritage Expert）

> WorkBuddy 专家市场 Agent 型专家。基于腾讯探元的文物数据库、世界遗产数据库与文博知识库（通过 MCP 接入），面向文博爱好者、亲子家庭及职场办公人群（策划、编辑、教师、设计师等），提供文物与世界遗产查询、知识问答、文物对比、攻略规划与研学方案五大能力。

- **专家类型**：Agent
- **分类**：`12-IndustryConsultant`（行业顾问）
- **作者**：腾讯 SSV 数字文化实验室
- **版本**：1.0.0

## 目录结构

```
tanyuan-cultural-heritage-expert/
├── .codebuddy-plugin/
│   └── plugin.json                       # 专家核心配置
├── .mcp.json                             # MCP 连接器配置（tanyuan-wb-mcp-server）
├── agents/
│   └── tanyuan-cultural-heritage-expert.md   # Agent 定义（系统提示词）
├── skills/
│   └── tanyuan-search/                   # 探元检索技能（MCP 版）
│       ├── SKILL.md
│       └── references/
│           └── api-spec.md               # MCP 工具参考
├── avatars/
│   └── expert.png                        # 头像（512×512 PNG，420KB，已就绪）
└── README.md
```

> ⚠️ 原 `skills/tanyuan-search/scripts/` 目录下的 `search-relics.js`、`search-knowledge.js` 已删除。所有检索统一走 MCP 工具，禁止再以任何方式调用脚本。

## 核心能力（5 项）

| 能力 | 典型问题 |
|------|---------|
| 文物与世界遗产查询 | 查询文物名称/年代/类别/等级/馆藏机构等信息，以及世界遗产国家/入选年份/类别/标准/濒危状态等结构化事实 |
| 知识问答 | 考古发现、文物保护、历史脉络、艺术鉴赏、工艺技术等专业问答 |
| 文物对比 | 两件及以上文物的产地/釉色/工艺/存世量/代表作等多维对比 |
| 攻略规划 | 博物馆参观建议、主题展览推荐、文博研学路线定制 |
| 研学方案 | 面向不同年龄段（尤其亲子）的主题研学教案设计 |

## MCP 接入

本专家通过 `tanyuan-wb-mcp-server` MCP 连接器接入探元检索能力，配置见根目录 `.mcp.json`，`plugin.json` 通过 `dependencies.mcpServers` 引用。

### MCP 工具与数据源映射

| MCP 工具 | 对应原脚本 | 数据源 | 适用问题 |
|---|---|---|---|
| `search_movable_relics` | ~~search-knowledge.js~~ | 可移动文物文献片段库 | 工艺、历史背景、艺术风格、故事、文化内涵、对比论证等开放语义问题 |
| `search_relics` | ~~search-relics.js~~ | 文物数据库／世界文化遗产数据库 | 名称、年代、材质、器型、馆藏机构、产地、出土地点等结构化约束 |
| `search_oracle_bone_character` | （新增） | 甲骨文字头库 | 根据具体汉字检索甲骨文字形、读音、释义等信息 |

- MCP 工具名前缀为 `mcp__tanyuan-wb-mcp-server__`。
- 鉴权由平台级统一 API Key 托管注入请求头，无需手动配置（`auth.type: "oauth"`）。
- MCP 服务端点：测试 `https://test-api.tanyuan.qq.com/wb/mcp`，正式 `https://api.tanyuan.qq.com/wb/mcp`（当前 `.mcp.json` 配置为预发环境 `https://pre-api.tanyuan.qq.com/wb/mcp`）。

## 工具选择与 Agentic RAG 策略（概览）

本专家**不把能力硬绑定到某个工具**，而是由 Agent 依据问题特征自主选择工具、重构检索 query、并按需多轮迭代（Agentic RAG）：

- `search_relics`（datasourceType=0，文物数据库 NL→SQL）：面向**精确事实查询**，按明确的馆藏机构/出土地/年代/类别/等级等条件查询数据库内文物。
- `search_relics`（datasourceType=1，世界遗产数据库 NL→SQL）：查询世界遗产国家/洲别、入选年份、类别、评定标准、濒危状态及关联知识层数据。
- `search_movable_relics`（关键词 + 向量）：擅长**单件文物或单主题**的背景、工艺、故事、鉴赏、对比论证、攻略、研学等细节说明。
- `search_oracle_bone_character`：甲骨文字形、读音、释义检索。
- **平台联网检索**：探元两个库覆盖有限、均非全集，**"代表作/著名/最重要/十大/排名"这类总结评价类问题以联网检索建立清单与知名度判断为主，再用探元库补单件细节**。

> 本节仅为面向读者的概览。**工具选择信号、query 重构规则、组合与迭代等完整策略以运行时文档为单一事实源**：技能侧见 `skills/tanyuan-search/SKILL.md`，Agent 决策逻辑见 `agents/tanyuan-cultural-heritage-expert.md`。

## 运行依赖

- 已在专家根目录 `.mcp.json` 中配置 `tanyuan-wb-mcp-server` 连接器，`plugin.json` 通过 `dependencies.mcpServers: "./.mcp.json"` 引用。
- 无需 Node.js 运行时，无需本地脚本依赖——检索全部走 MCP 远程调用。
- 鉴权由平台级统一 API Key 托管注入请求头，无需手动配置。
- 探元 MCP 返回的 `cover` / `thumbUrl` 等图片资源视为已授权可用，直接嵌入回答，无需追加授权限制说明。

## 头像

`avatars/expert.png` **已就绪**：512×512 px PNG，约 420KB（≤500KB），符合规范。如需替换，保持同样的尺寸与格式约束即可。

## 打包提交

打包前先清理仓库产生的临时/评审文件（这些**不应**进入专家包）：

```bash
# 1. 清理临时与评审产物
find tanyuan-cultural-heritage-expert -name '.DS_Store' -delete
rm -rf tanyuan-cultural-heritage-expert/.review-cache

# 2. 打包上架（排除评审报告与临时文件）
zip -r tanyuan-cultural-heritage-expert.zip tanyuan-cultural-heritage-expert/ \
  -x "*.DS_Store" -x "*/__pycache__/*" \
  -x "*/.review-cache/*" -x "*/审查报告-*.md"
```

> 说明：`审查报告-*.md`、`.review-cache/` 仅用于开发期自检，不属于专家包内容，打包时排除。

## 提交前自检清单

### 文件结构
- [x] `.codebuddy-plugin/plugin.json` 存在且 JSON 有效
- [x] `.mcp.json` 存在且 JSON 有效（含 `x-workbuddy` 元数据 + `auth.type`）
- [x] `agents/tanyuan-cultural-heritage-expert.md` 存在
- [x] `skills/tanyuan-search/SKILL.md` 与 `references/api-spec.md` 存在
- [x] `avatars/expert.png` 已放入（512×512 PNG，420KB ≤500KB）
- [x] 不含 `hooks/` / `commands/` / `.lsp.json` / `settings.json`
- [x] `agents/` 和 `skills/` 在根目录（不在 `.codebuddy-plugin/` 里）
- [x] **不含 `scripts/` 目录**（原脚本已删除，检索统一走 MCP）
- [ ] 打包前已删除 `.DS_Store`、`.review-cache/`，并排除 `审查报告-*.md`

### plugin.json
- [x] `name = plugin = tanyuan-cultural-heritage-expert`
- [x] `expertType = "agent"`，`agentName = tanyuan-cultural-heritage-expert`
- [x] `displayName / profession / displayDescription / defaultInitPrompt / tags / quickPrompts` 全部中英双语
- [x] `displayDescription.zh` 字数在 40-50 之间（当前 49 字）
- [x] `tags` 固定 3 个
- [x] `quickPrompts` 固定 3 条，第 1 条 = `defaultInitPrompt`
- [x] `categoryId = "12-IndustryConsultant"`
- [x] `skills = ["./skills/tanyuan-search"]`
- [x] `dependencies.mcpServers = "./.mcp.json"`

### Agent MD
- [x] frontmatter `name` 与文件名一致（`tanyuan-cultural-heritage-expert`）
- [x] frontmatter 含 `description / displayName / profession / maxTurns`
- [x] **frontmatter 中不含 `tools` 字段**
- [x] 正文清晰定义了五大能力、Agentic RAG 工具选择策略、MCP 工具调用方式、输出模板与边界
- [x] 明确约束**不向用户暴露内部运行信息**（工具/检索/query 改写/失败等）
- [x] 明确**禁止再调用 `scripts/` 目录下的脚本**

### MCP 配置
- [x] `.mcp.json` 配置 `tanyuan-wb-mcp-server`（type: streamableHttp）
- [x] 含 `x-workbuddy.displayName` / `x-workbuddy.description`（双语）
- [x] `x-workbuddy.auth.type = "oauth"`

### 头像
- [x] PNG 格式，512×512 px，≤500KB（420KB）
- [x] 内容合规、风格专业
