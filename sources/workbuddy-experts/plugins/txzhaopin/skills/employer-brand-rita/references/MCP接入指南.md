# MCP 接入指南（Rita v2.0）

> 本文档替代原 `数据库文档.md`。Rita v2.0 不再连接本地 SQLite，所有数据通过 MCP 后端按角色权限读取。

## MCP 服务地址

- **服务地址**：`21.91.205.237:8080`（直连 IP，不使用域名）
- **MCP 端点**：`21.91.205.237:8080/mcp`
- **API Key 认证**：请求头 `X-API-Key: {你的API Key}`

## API Key 配置

1. **注册获取 API Key**：前往 https://campus123.woa.com/fofo 一键注册（通过 OA 登录态自动识别身份，秒级获取 Key）
2. 在 WorkBuddy 的 MCP 连接器配置中填入：
   - URL: `http://21.91.205.237:8080/mcp`
   - Header: `X-API-Key: {你的Key}`
3. 首次配置时 Rita 会自动检测 API Key 是否有效

## Rita 角色与权限

API Key 绑定的用户角色决定了可读取的数据范围：

| Rita 角色 | 可读数据 | 写入范围 |
|---|---|---|
| rita_system_admin | 全部数据 + 使用统计 | 全部 |
| rita_hr_group | 公共数据 + 跨 BG 对比 | 集团池（public） |
| rita_bg_manager | 公共数据 + 本 BG 同侪调研 | 本 BG |
| rita_bg_other_hr | 公共数据（不可见同侪调研） | 本 BG |
| rita_public_viewer | 仅 benchmark + 方法论 | 无 |

调用 `query_my_research_scope` 可查看当前角色与可读范围。

## MCP 工具列表（13 个）

### 读取工具（10 个）

| 工具名 | 用途 | 关键参数 |
|---|---|---|
| `query_my_research_scope` | 查看当前角色/权限范围 | 无 |
| `query_research_projects` | 查询调研项目列表 | bg, survey_type, year, limit |
| `query_research_dimension_scores` | 查询维度评分（标准化对比） | bg, dimension, project_id, limit |
| `query_company_benchmark` | 公司级 benchmark（7 公司 × 13 维度 + 整体好感度） | company, dimension |
| `query_research_interviews` | 访谈摘要（脱敏后） | bg, project_id, sentiment, limit |
| `query_research_findings` | 检索他人沉淀的洞察 | bg, dimension, keyword, limit |
| `query_intern_surveys` | 实习生/秋招宣讲会调研项目列表 | year, limit |
| `query_bg_intern_presentation` | BG 宣讲会前后就职意向变化（2024-2026 三年） | bg, year |
| `query_bg_fall_recruitment` | BG 秋招候选人调研（知晓度/吸引力/子维度） | bg, year |
| `query_intern_responses` | 实习生回答明细（脱敏，可钻取） | survey_id, school, city, limit |

### 写入工具（2 个）

| 工具名 | 用途 | 关键参数 |
|---|---|---|
| `ingest_research_finding` | 提交结构化结论 | dimension, question_text, avg_score, sample_size, insight_text, visibility |
| `update_research_finding` | 编辑已沉淀的 finding | finding_id, 可选修改字段, edit_reason |

### 统计工具（1 个，仅管理员）

| 工具名 | 用途 | 关键参数 |
|---|---|---|
| `query_research_usage_stats` | 使用统计（按 BG/工具/角色/用户/天聚合） | period, group_by, only_denied |

## 降级策略

若 MCP 服务不可用：
- Rita 提示"调研数据库暂时不可用，本次按方法论模板出方案，不引用历史数据"
- 不阻塞工作流，仅影响历史数据引用能力

## 检索成功率操作细则（配合 SKILL.md「检索成功率 SOP」）

### 分层重试模板

```
第1层 专用工具（最精准，优先）：
  - 找洞察结论 → query_research_findings(keyword=..., bg=..., dimension=...)
  - 公司级技术影响力 → query_company_benchmark(company=..., dimension=...)
  - BG宣讲意向 → query_bg_intern_presentation(bg=..., year=...)
  - 维度评分 → query_research_dimension_scores(bg=..., dimension=...)
      ↓ 命中 0 条
第2层 联邦检索（最广，跨域兜底）：
  - search_campus_data(query=..., scope=["research","employer_brand","intel","materials"])
  - 命中多但杂 → 用 scope 收窄 + start_date/end_date 过滤，再 include_payload=true 取详情
      ↓ 仍 0 条
第3层 放宽关键词：
  - 换同义词/上位词/去修饰（去掉"最新/2026/腾讯"等限定），或拆成多个短词分别搜
      ↓ 2 轮仍 0 条
才可结论"暂无该数据"，并建议补充网络口碑或定制调研
```

### dimension 取值（必须命中白名单，否则返回 0 条）

- A组技术影响力13维：`tech_influence` / `brand_awareness` / `rd_resources` / `tech_value` / `tech_challenge` / `tech_accumulation` / `infrastructure` / `tech_patience` / `research_freedom` / `tech_innovation` / `tech_output` / `talent_quality` / `tech_atmosphere`
- 综合好感度：`overall_favorability`
- 完整中文名↔snake_case 映射见 `data/standard_schema.json` 的 `dimension_name_map`
- ⛔ 禁止：带序号后缀（`tech_influence_01`）、残留 markdown 加粗符（`**技术影响力**`）、中文直传当 dimension

### 关键词去噪清单

| 场景 | 推荐词 | 避免 |
|------|--------|------|
| 青云计划 | `青云计划` / `腾讯青云` | 只搜"青云"（混入苏宁易采云青云计划） |
| 专项招聘计划 | `专项招聘计划` + 公司名 | 泛词"计划" |
| 任何查询 | 去除 `**` 加粗符 | 直接把带格式的题干当关键词 |

> **核心心法：命中 0 条 = 换个姿势再试，不是没有数据。** 至少 2 轮不同尝试后才下"无数据"结论。
