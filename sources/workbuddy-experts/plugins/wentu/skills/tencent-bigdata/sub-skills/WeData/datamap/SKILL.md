---
name: datamap
description: >
  腾讯 WeData 数据地图的 AI 库表检索 + 数据治理问答能力。
  当用户需要按业务关键词找物理表、看表结构、查血缘、查库表关联的调度任务、查表分区列表（创建时间/大小/行数）、
  查我有权限/我名下/我常用的表，
  或者用自然语言查询自己/组织的存储治理现状（低热度表、未配置生命周期、治理项分布、存储 Top N、治理方案）时使用此 skill。
  支持 6 种检索命令（search/schema/partitions/related/tasks/t2s）+ 3 个治理只读子命令（gov-health/suggestions/chat）。
  ⛔ 开放问答（ask / scope=ask）已禁用，"X 是什么/怎么做" 请走通用对话回答，不要进入本 skill。
  ⛔ 治理服务的 6 个旧接口（status/stop/detail/summary/history + 旧版非 sync chat）已于 2026-07 前下线（404），对应子命令已移除。
  可串联为"先检索找表 → 再做治理判断"或"治理查出候选表 → 再看血缘判可删性"的复合工作流。
  ⛔ 治理写操作（删表 / 改生命周期）不在 skill 范围内，检测到删除意图仅透传警告，不会自动 confirm。
  触发关键词：找表、库表检索、数据资产、字段反查、表 schema、查字段、表结构、上下游、血缘、关联表、
  库表关联任务、调度任务、生产任务、任务血缘、下游任务、上游任务、表由哪个任务产出、消费该表的任务、
  表分区、分区列表、分区创建时间、分区更新时间、分区大小、分区行数、partitions、DescribeAssetPartitions、
  我有权限、我名下、我常用、热度表、accessible、owned、hot、related、tasks、t2s、text2sql、找字段、写SQL找表、
  存储概览、低热度表、未配生命周期、治理项分布、存储 Top N、优化收益、治理方案、
  我占了多少存储、我有多少 TB 数据、按库名统计存储分布、应用组治理、
  governance、数据治理、ads_wedata_cost_table_gov_detail_df、datamap、数据地图。
---

# DataMap 数据地图 AI 库表检索 + 数据治理问答

## 概述

通过腾讯 WeData 数据地图的多源后端（Hippo 知识库 + wedata OpenAPI + 热度表 API）和数据治理问答助手（乐高服务），提供两条互补的能力链路 + 4 种串联工作姿势：

**子技能一：库表检索（search/schema/partitions/related/tasks/t2s）** — 业务关键词 → 物理表 / 关联任务 / 分区列表
1. **业务搜表（search --scope any/accessible/owned/hot）** — 按 scope 切换 4 种意图：业务搜 / 我有权限 / 我名下 / 我常用
2. **单表 schema（schema）** — 看一张表的字段说明书（含字段中文名 + 业务含义 + 字段级 provenance 来源）
3. **单表分区列表（partitions）** — 查一张表的分区清单（每分区含创建时间 / 大小 / 行数），走 wedata DescribeAssetPartitions 接口
4. **关联血缘（related）** — Hippo 语义图谱 + wedata 控制台血缘双源混合（返回**关联表**）
5. **关联调度任务（tasks）** — 查库表关联的调度任务（返回**产出该表 / 消费该表**的任务清单）
6. **Text-to-SQL 找表找字段（t2s）** — 多通道并行召回（Table/SemanticView/Measure/Dimension/Segment/Column）+ RRF 融合 + 字段精排 + 共查询补全 + JOIN 扩展（为写 SQL 找齐表和字段）
7. ~~**开放问答（ask）**~~ — ⛔ 已禁用，开放问答交由通用对话

**子技能二：数据治理问答（gov-* 系列，只读）** — 自然语言 → SQL → 治理底表
6. **核心对话（gov-chat）** — 同步直返（user_llm_chat_sync）；命中模板出 SQL，否则 LLM 生成
7. **首屏推荐 / 探活（gov-suggestions / gov-health）** — 辅助查询
   ⛔ 旧接口 status/stop/detail/summary/history 已下线，对应子命令已移除

**核心用途**：让用户用一句中文/英文搞定"找表 + 看字段 + 看治理现状 + 决定怎么治理"的端到端链路，无需在多个网页之间来回切换。

### ⭐ Owner（资产清单）vs Gov（治理诊断）路由判定

两条子技能链最容易被混淆的边界，**调工具前先按下面这张表把意图归类**，再决定走 `search --scope owned` 还是 `gov-chat`：

| 用户意图信号 | 应走 | 理由 |
|---|---|---|
| "我名下**有哪些表** / 我负责的表清单 / 我的表都有什么 / 我建过哪些表" | `search --scope owned` | 要的是**资产元数据**：表名 / 库 / 字段 / Owner / 权限 |
| "我名下表的**字段 / 业务用途 / 上下游**" | `search --scope owned` → `schema` / `related` | 元数据深挖，不涉及成本/热度指标 |
| "我名下的**低热度 / 长期未访问 / 冷数据**表" | `gov-chat` (personal) | 涉及"热度"指标 → 走治理底表 |
| "我名下表**占了多少存储 / 多少 TB / Top N 大表**" | `gov-chat` (personal) | 涉及"存储成本"指标 → 治理底表 |
| "我名下的**治理项 / 健康分 / 优化建议 / 待治理**" | `gov-chat` (personal) | 治理项分布只在底表 `ads_wedata_cost_table_gov_detail_df` |
| "我名下表的**生命周期 / 未配 TTL / 永久保留**" | `gov-chat` (personal) | 生命周期是治理维度 |
| "我们组 / 我们部门的资产清单（表名列表）" | `search --scope any --department <BG>` 或 `--organize` | 组织维度的元数据资产盘点 |
| "我们组 / 我们部门的**存储 / 治理 / 低热度**" | `gov-chat --scope-type org` | 组织维度的治理指标 |

**判定规则一句话**：意图里包含**「成本 / 热度 / 治理 / 生命周期 / 健康度」**等**治理指标语义** → 走 `gov-chat`；只想看**「我有什么表 / 表是干啥的 / 字段怎样 / 上下游」**等**资产元数据语义** → 走 `search` 系列。两者都要 → 链式串联（见下文「典型使用场景 C/D」）。

[WARN] 不要因为用户说了"我名下"就无脑路由到 owned；同样也不要因为说了"治理"就无脑路由到 gov-chat。**关键看后半句问的是元数据还是治理指标**。

## 执行规则

- **复合问题先规划**：用户一句话同时含"找表 + 治理"、"先 A 再 B"、"X 里的 Y" 等多步语义时，**先在 thinking 区域拆原子任务 T1..Tn，标依赖序，再开始调工具**；不要把整句塞给某一个入口。
- **query 必须剥词**：`search` 的 `--query` 参数**只能装业务关键词**（如"微信支付"、"视频号 GMV"）。礼貌词（帮我、想找）、scope 修饰词（我的、我常用的）、列表动词（列出、显示）必须剥光，否则会被语义召回当业务概念污染结果。详见 `references/parameter_mapping.md`。
- **能下推 Hippo 的维度拆出来**：部门（`--department WXG`）/ 数仓分层（`--warehouse-layer dws`）/ 业务分类（`--business-category '视频号直播'`）/ 库名（`--db-names`）/ 标签（`--tags`）等结构化维度识别到就拆成 CLI 参数，不要留在 `--query` 里。
- **翻页禁止重跑**：用户说"下一页 / 继续 / 后面 30 张"时，**必须** `read_file(上一次 result_file)` 然后切 `tool.candidates[N*30:(N+1)*30]`，**禁止**重新调 search（会因时间戳/召回抖动产生不一致结果）。
- **answer 原样转发**：gov-chat 返回的 `data.answer`（Markdown）**直接转发给用户**，不要 LLM 重写。后端已模板化（含 emoji + 表格 + [TIP] 建议），重写只会变差。
- **治理写操作红线（⛔）**：gov-chat 响应里如果带 `action_required != null`（识别到删表/改生命周期意图），**只把警告原样转告用户**，**绝不调用** `user_llm_query` / `user_llm_query/cancel` 写接口。要执行治理动作请引导用户到网页端 `http://11.151.217.90:8080/` 人工确认（confirm_token 60s 内有效）。
- **gov-detail 必带 scope**：~~拿 chat 的 `filter_sql` 调 gov-detail 时必须带 scope~~ — ⛔ `gov-detail` 已下线。如需调整过滤条件，直接在 `gov-chat --question` 里改问法重新查。
- **三级权限递进 + 未收录分支**：每张候选表带 `can_view_schema` + `has_select` 两个标记。
  - `scope=accessible` 时默认启用 group 间接授权校验（`ACCESSIBLE_INCLUDE_GROUP_GRANT=true`）：对 `has_select=None` 的候选按优先级（literal > semantic_hits > 其他）批量调 `metaDataPrivilege+select` 精校验，把通过用户组/appGroup 间接授权的表从 None 升级为 True，避免一刀切漏掉。容量上限 500（`ACCESSIBLE_GROUP_VERIFY_MAX`）。
  - `_not_indexed=true` → wedata 未收录该表（≠ 无权限）。工具会调 `security_center` 真实鉴权（含 appGroup 间接授权）判 select：有 select → 渲染 do-bigdata DESC 兜底命令模板；无 select → 渲染申请链接。`found=0`，**不要编字段**。
  - `can_view_schema=false`（已收录但无权限）→ 不要介绍字段，仅给表名 + Owner，列表行末尾打 * 标签
  - `can_view_schema=true, has_select=false` → 可介绍字段，列表行末尾打 * 标签
  - `has_select=true` → 正常介绍，**不打标签**（避免每张表都重复说一遍权限路径）
  - 注：通用召回输出按 `references/output_format.md` 的"凝练直观"骨架——盘点 + 列表突出 Top 表 + 直接的下一步建议；权限异常**汇总点出**即可，不要逐张展开成三段并列说明。
- **裸表名兜底协议（related / schema）**：当用户只给**裸表名**（如 `dwm_wedata_user_activity_aggr_di`，缺 `db.` 前缀，或写成 `tl.<表名>` 这种 cluster.table 形式）就要求查血缘 / 字段时：
  1. ⛔ **绝对禁止** LLM 自行编造库名 / cluster 前缀（如 `tl.`、`public.`、`default.`、瞎猜的 `xxx_db.`）来拼 `db.table` —— 编造的 db 必然命中失败，且污染审计链路。
  2. [OK] **工具已内置确定性消歧**：直接把裸表名透传给 related/schema 即可，工具会按表名精确召回真实 `db.table`：
     - **唯一命中** → 工具**自动回填**继续查，`notice` 头部会标注"已自动定位到 db.X"，转告用户即可；
     - **多张同名（schema 路径有权限择优）** → 若用户对其中**恰好 1 张**有元数据查阅权限，自动收敛到那张，`notice` 会注明"其余 N-1 张同名表无权限已跳过，如目标是另一张请提供完整 db.table 重查"；用户**仍需**把这条提示原样转告，让用户有机会纠正；
     - **多张同名 + 0/≥2 张有权限**（observation 标题为"裸表名需要消歧"）→ 把工具返回的同名表清单（带 db/Owner）给用户选，**禁止替用户臆断**，用户选定后用完整 `db.table` 重调；
     - **零命中** → 工具返回干净 error，如实告知"全公司无此表"，**不要自己拼 db 硬试**。
- **不编造**：所有表名、字段名、SQL 必须来自工具实际返回，**禁止**编造工具结果之外的内容。
- **schema 模式必须有 user_rtx**：用于校验查阅权限；缺失时先让用户提供。
- **高敏识别**：`sensitive=true` 或 `security_level >= "4"` 标记为高敏表，输出时单独提示。
- **复合问题的扇出上限**：对候选列表逐个二次操作时**最多并行 ≤ 10**，超过先按存储/热度排序取 Top N 收敛。
- **凭证：仅依赖 do-bigdata 加密凭证，不需要 config.json**：proxy_user / cmk / cmk_id 由 `@auth_required` 从 `~/.do-bigdata/security_file/config.json.enc` 自动注入。**没有 rtx 字段**——用户意图含"我们组 / 我们部门 / 自身组织热门表"时，**先反问一次组织路径**（如 `TEG/数据计算平台部/智能算法组`）然后统一用 `--organize` 显式透传，不要让用户去碰 config.json。意图未涉及组织维度的 → 不必反问，直接走个人维度。
- **结果文件落盘约定**：每次调用都会落盘 `<workspace>/tmp/datamap_result_*.json` 或 `governance_<endpoint>_*.json`。**翻页/二次过滤/串联工作流靠 read_file 串数据，不要每步重跑**。可通过环境变量 `DATAMAP_RESULT_DIR` 改落盘目录。

## 工作流程

### 前置步骤：检查凭证

执行任何检索/治理操作前，**必须先确认 do-bigdata 凭证已配置**：

```bash
do-bigdata auth status
```

**凭证不存在或失效时**，引导用户：

```bash
# CMK 从 https://wedata.woa.com/security/user/keys 下载
do-bigdata auth init --user <RTX> --cmk <CMK密钥>
```

CMK 由 do-bigdata 加密存储到 `~/.do-bigdata/security_file/config.json.enc`，**永不明文落盘**。

### 凭证字段说明（无需任何 config.json）

datamap 完全复用 do-bigdata 加密凭证，**不需要用户提供 config.json**。三个字段由 `@auth_required` 自动注入到 subprocess 环境变量：

| 字段 | 来源 | 必填 | 说明 |
|---|---|---|---|
| `proxy_user` | `do-bigdata auth init --user` 加密保存 → `DATAMAP_USER` | [OK] | 用户 RTX |
| `cmk` | `do-bigdata auth init --cmk` 加密保存 → `DATAMAP_CMK` | [OK] | TAuth 主密钥 |
| `cmk_id` | 同上加密保存 → `DATAMAP_CMK_ID` | 可选 | CMK 版本号 |
| ~~`rtx`（组织架构路径）~~ | **不再需要** | — | 见下方"组织路径处理约定" |

#### 组织路径处理约定（替代旧 `rtx` 字段）

旧版 `config.json` 里的 `rtx`（如 `TEG技术工程事业群/数据计算平台部/智能算法组`）在 do-bigdata 加密凭证里**不保存**，因此 datamap 内部 `organize` 不再自动派生。这只影响下面两类查询：

- `search --scope hot`（"我常用的表"）：缺 organize 时只查**个人热度**，不会自动合并"自身组织热度"
- 用户说"我们部门 / 我们组 / 团队 ..."类查询：缺 organize 时退化为按 owner 维度查

**LLM 处理规则**：

1. 用户意图含**自身组织语义**（"我们组 / 我们部门 / 自己团队"）或想看"自身组织热门表"时，**先反问一次**：
   > "需要带上你的组织架构路径才能合并组织热度，例如 `TEG/数据计算平台部/智能算法组`，请提供一下，我会通过 `--organize` 透传。"
2. 用户给出后，**统一通过 `--organize <路径>` 显式传**，不要让用户去碰 config.json
3. 用户**明确指定他人组织**（"WXG 微信支付组"）时直接用 `--organize` 即可（工具会自动开启 `hot_org_only`）
4. 用户不在意 / 没提到组织 → 直接走，不必反问；个人热度也是合理结果

### 子技能一：业务搜表（search）

```bash
# 业务关键词搜（不限权限的全公司召回）
do-bigdata wedata datamap search --scope any --query '微信支付'

# 我有权限的所有表（统计型）
do-bigdata wedata datamap search --scope accessible --query ''

# 我有权限的微信支付相关表
do-bigdata wedata datamap search --scope accessible --query '微信支付'

# 我名下的表（owner=当前用户）
do-bigdata wedata datamap search --scope owned --query ''

# 我常用的 wedata 表（默认仅个人热度；要合并组织热度需显式传 --organize）
do-bigdata wedata datamap search --scope hot --query 'wedata'
do-bigdata wedata datamap search --scope hot --query 'wedata' \
    --organize 'TEG技术工程事业群/数据计算平台部/智能算法组'

# 加结构化下推：WXG 部门 dws 层用户分层
do-bigdata wedata datamap search --scope any --query '用户分层' \
    --department WXG --warehouse-layer dws

# 限定库 + 标签
do-bigdata wedata datamap search --scope any --query '代理人' \
    --db-names ams_agency_db --tags 核心表

# 看他人组织的热门表（自动开启 hot_org_only）
do-bigdata wedata datamap search --scope hot --query '' \
    --organize 'WXG微信事业群/微信支付应用部/支付平台组'
```

> `scope=hot` 带业务 query 时启用**关键词主召回 + Hippo 语义混合排序**：先在表名/库名/description/字段名/字段中文名上扫关键词，再用 Hippo 语义命中做交叉验证加分。详见 `references/parameter_mapping.md`。

### 子技能二：单表 schema（schema）

```bash
# 看某张表的完整字段说明书
do-bigdata wedata datamap schema --query 'wxg_finder_dws.dws_app_finder_vip'
```

返回 `tool.candidates[0]` 含 `columns`（字段名 + 类型 + 中文名）+ `hippo_props` + `cube_def`。无权限时 `notice` 提示申请。**wedata 未收录时**（`found=0` + `_not_indexed=true`）：工具会调 `security_center` 真实鉴权判 select 权限，渲染段给出 do-bigdata DESC 兜底命令模板（含天穹大数据 skill 安装指引）或申请链接。

### 子技能三：单表分区列表（partitions）

查一张表的分区清单，走 wedata `DescribeAssetPartitions` 接口（Type=HIVE/STARROCKS + Attribute={ClusterName, DatabaseName, TableName}）。
每分区返回 4 个字段：**创建时间**（`CreateTime`，毫秒时间戳转可读字符串）/ **分区名**（`Name`）/ **大小**（`Size`，字节转 GB/B）/ **行数**（`RowCount`）。

```bash
# 查某张表的分区列表（默认 size=20，即展示前 20 个分区）
do-bigdata wedata datamap partitions --query 'public_thive.dim_task_type'

# 展示前 50 个分区
do-bigdata wedata datamap partitions --query 'public_thive.dim_task_type' --size 50
```

**result_file 结构**：
- `tool.candidates[]` — 每个分区一个 candidate，字段：
  - `partition_name` — 分区名（如 `p_20260714`）
  - `partition_create_time` — 创建时间（如 `2026-07-15 00:07:44`）
  - `partition_size` — 字节数（渲染段已转 GB/B 可读字符串）
  - `partition_row_count` — 分区行数
  - `qualified_name` — 表的全限定名（`cluster.db.table`）
- `tool.found` — 分区总数（如 561）
- `output` — 渲染好的 Markdown（含召回摘要 JSON + 分区列表 JSON）

**适用场景**：
- "这张表的分区什么时候创建的 / 最近一次更新分区是哪天"
- "这张表有多少个分区 / 分区大小分布"
- "最近 7 天新增了哪些分区"（拿 `partition_create_time` 排序后筛）

**限制**：
- 仅支持 HIVE / STARROCKS 引擎；非分区表返回 `found=0` + notice 提示"没有分区或未收录"
- `--size` 上限 100（受 wedata 接口 PageSize 限制）；分区总数大时只能翻页
- 没有"分区更新时间"字段——接口只返回 `CreateTime`，不含 `LastModifiedTime`
- 裸表名协议同 schema/related：支持自动消歧，但建议直接传 `db.table` 全限定名

### 子技能四：关联血缘（related）

双源混合：**Hippo 语义图谱**（derivedFrom / joinedWith / columnLineage）+ **wedata 控制台血缘**（DescribeMapTableLineage，覆盖率高，兜 Hippo 5% 盲区）。同一张表双源命中标 `lineage_cross_validated`（强证据）。

⭐ **一次调用同时返回"关联表 + 关联调度任务"**：wedata 血缘调用默认开启 `DisplayNextTask=True`，
一次 HTTP 同时把「表↔表」和「表↔任务」两类边解析出来。结果分成两部分：
- `tool.candidates` —— 关联表清单（含 Hippo + wedata 双源合并 / 权限反查 / cross_validated 标记）
- `tool.related_tasks` —— 顺带查到的关联调度任务清单（结构同 `tasks` 子技能，见 `references/tasks_api.md`）

```bash
# 跟某张表相关/上下游的表 + 关联调度任务（默认）
do-bigdata wedata datamap related --query 'public_thive.dim_task_type'

# 只要关联表、不要任务（关联表已够多、任务节点过大时可关闭省 token）
do-bigdata wedata datamap related --query 'db.tbl' --no-include-tasks

# 强制关闭 wedata 兜底（仅用 Hippo 单源；此时也不会有任务）
do-bigdata wedata datamap related --query 'wechat_pay_data_mining.t_dm_db_tableinfo' \
    --lineage-fallback off
```

**输出建议**（LLM 侧）：
- final answer 里主表格给"关联表"，然后**用一段小结**给"关联任务"数量 + Top N（按 direction 分组）
- 若用户明确只问"表血缘"，任务信息可折叠到附注；若用户还问"这些表怎么产出的 / 有哪些任务"，
  就把 `related_tasks` 展开
- 用户想深挖某个任务详情（重跑 / 看实例日志 / 诊断失败），把 `related_tasks[i].task_id`
  作为入参跳转到 US skill（`us-log-analyzer` / `us-fail-task-diagnose`）

> [WARN] **裸表名自动消歧**：用户只给 `dwm_wedata_user_activity_aggr_di`（无 db. 前缀，或写成 `tl.<表名>`）时，**直接透传**给 `related --query` 即可，工具会按表名精确召回：
> - 唯一命中 → 自动回填 `db.table` 继续查血缘（`notice` 会标注定位到哪张表）；
> - 多张同名 → 返回"裸表名需要消歧"清单，把同名表给用户选后用完整 `db.table` 重调；
> - 零命中 → 返回 error，如实告知不存在。
> ⛔ **禁止**自行补 `tl.` / `public.` / 任何瞎猜的库名硬拼。

### 子技能五：关联调度任务（tasks）

查一张表关联的**调度任务清单**（不返回关联表）。走 wedata `DescribeMapTableLineage(DisplayNextTask=True)`，
从血缘图里把「表↔任务」的边解出来，返回：

- **上游任务（direction=upstream）**：产出这张表的任务，即"这张表由哪个/哪些任务写入"
- **下游任务（direction=downstream）**：消费这张表的任务，即"哪些任务把这张表作为输入读取"

> [TIP] **与 `related` 的重叠**：`related` 已经默认返回 `tool.related_tasks`，
> 大多数场景直接用 `related` 一次拿全"关联表+关联任务"即可。**只在用户明确只关心任务、
> 不关心关联表**（例如"这张表由哪个任务产出"、"用这张表的下游任务有几个"）时，
> 才用 `tasks` 命令——它省掉了 Hippo 表血缘检索这一路的开销，返回更聚焦。

```bash
# 默认返回上游 + 下游两类任务
do-bigdata wedata datamap tasks --query 'public_thive.dim_task_type'

# 只查上游（这张表是哪个任务产出的）
do-bigdata wedata datamap tasks --query 'wxg_finder_dws.dws_app_finder_vip' \
    --direction upstream

# 只查下游（这张表被哪些任务消费）
do-bigdata wedata datamap tasks --query 'db.tbl' --direction downstream
```

**返回字段**（每个 candidate 的 `task` 字段）：`task_id / task_name / task_type / direction / owner / workflow_id / project_id / cycle_type / cluster / qualified_name / guid / peer_tables`。详见 `references/tasks_api.md`。

**与 related 的边界**：
- 用户问"这张表的**上下游是什么**、**关联表**、**血缘表**" → `related`
- 用户问"这张表**由哪个任务产出**、**由什么任务写入**、**被哪些任务用了**、**关联的调度任务**、**生产任务**" → `tasks`
- 用户问"这张表在**哪个 US 视图/工作流下**" → `tasks`（`workflow_id` 字段），仍拿不到具体视图详情时引导到 US skill

**限制**：数据源同 related（wedata 血缘图）。若表尚未被 wedata 血缘图收录、或 wedata 无 TableGuid，会返回 `status=no_guid` 的空结果——**不要编造任务**，如实告知用户。

[WARN] **裸表名自动消歧**：与 `related` 完全一致——直接透传 `dwm_wedata_xxx_di` 即可，工具会精确召回真实 `db.table`，多张同名时返回消歧清单；⛔ 禁止 LLM 自行补 `tl.` / `public.` 等库前缀硬拼。

### 子技能六：开放问答（ask） — ⛔ 已禁用

`do-bigdata wedata datamap ask` 命令已下线，调用会直接返回错误。
"X 是什么 / 怎么做 / 怎么选" 类开放问答请走通用对话回答，不要进入本 skill。

### 子技能七：治理对话（gov-chat）

自然语言查询治理底表 `ads_wedata_cost_table_gov_detail_df`。同步直返接口（`user_llm_chat_sync`），不再有异步轮询。

```bash
# 探活（先打一发，确认 llm_available=true）
do-bigdata wedata datamap gov-health

# 首屏推荐问题
do-bigdata wedata datamap gov-suggestions --scope-type personal

# ⭐ 核心对话（personal 视角）
do-bigdata wedata datamap gov-chat --question '我名下的低热度表有哪些？' --scope-type personal

# 组织视角
do-bigdata wedata datamap gov-chat --question '我们组的存储 Top 20 表' \
    --scope-type org --scope-org-code '0|958|54756|87803'

# 应用组视角（OBS 产品）
do-bigdata wedata datamap gov-chat --question '应用组治理现状' \
    --scope-type obs_product --scope-org-code '...' --scope-app-groups 'g_app_a,g_app_b'
```

#### Scope 三选一

| scope.type | 必填 | 可选 | 含义 |
|---|---|---|---|
| `personal`（默认）| `--scope-owner`（不传时自动用当前用户）| — | 个人账户视角 |
| `org` | `--scope-org-code` | `--scope-filter-owner` | HR 组织层级 |
| `obs_product` | `--scope-org-code` | `--scope-app-groups`、`--scope-filter-owner` | OBS 产品 / 规划产品 |

#### chat 响应字段处理

stdout 是元信息，**真内容在 `result_file`**。`read_file → data` 后：

| 字段 | 处理 |
|---|---|
| `answer` (Markdown) | **原样转发**，不要 LLM 重写 |
| `sql_info.sql` | 可折叠展示让用户审计 |
| `sql_info.is_llm_generated=true` | 提示用户"SQL 由 AI 生成，建议核对" |
| `sql_info.query_executed=true` | 标注 SQL 已执行，answer 里的数据是真实结果 |
| `meta` | 意图路由诊断（intent/result_type/confidence/route_suggestion/llm_used），可选展示 |
| `action_required != null` | ⛔ 只警告 + 给网页端链接，永不调写接口 |
| `suggestions` | 末尾附追问 chip |
| `session_id` | 缓存好供后续追问（自动上下文）|

### 子技能八：已下线接口说明

以下治理接口已于 2026-07 前下线（服务端返回 404），对应子命令已移除：
- ~~`gov-status`~~ — 异步轮询状态（sync 接口直返后不再需要）
- ~~`gov-stop`~~ — 中止任务（sync 接口无 call_id）
- ~~`gov-detail`~~ — SQL 下推/二次过滤（`query_table_detail_sql`）
- ~~`gov-summary`~~ — 治理概览刷新（`refresh_gov_summary`）
- ~~`gov-history`~~ — 对话历史（`user_llm_history`）

如需二次过滤明细，可在 `gov-chat` 返回的 `sql_info.sql` 基础上手动调整 SQL 后重新调 `gov-chat`。

### 串联工作流：4 种嵌套姿势

#### 链式（A → B → C）：上一步产物作下一步输入

例："我名下低热度表里存储 > 100GB 的，看其中 wxg_finder_dws.xxx 字段"
1. `gov-chat --question '我名下存储 > 100GB 的低热度表' --scope-type personal` → 拿到 N 张表
2. 对其中 wxg_finder_dws.xxx：`schema --query 'wxg_finder_dws.xxx'` → 看字段

> [WARN] 旧版 `gov-detail` 二次过滤已下线。如需调整过滤条件，直接在 `gov-chat --question` 里改问法重新查。

#### 扇出（A → {B1..Bn} 并行，≤10 收敛）：候选列表逐个二次操作

例："我名下低热度表里哪些有下游依赖（不能直接删）"
1. `gov-chat --question '我名下的低热度表有哪些？'` → 拿到 18 张
2. 对前 10 张并行调 `related --query 'db.tbl_i'`（一个 message 多个 tool call 同发）
3. 汇总："18 张里 12 张无下游可直接删，6 张有下游需评估，剩余 8 张同理处理"

#### 扇入（{A1, A2} → 内存合并）：多份独立查询求交集

例："视频号 GMV 相关表里我有权限的"
1. 并行：`search --scope any --query '视频号 GMV'` + `search --scope accessible --query ''`
2. 内存按 `qualified_name` 求交集 → 输出

#### 循环（for each: B）：用户语义"逐个" → 实际仍用扇出实现

### 典型使用场景

**场景 A：纯治理统计概览（最常见）**
1. 用户："我名下表占了多少存储"
2. 调 `gov-chat --question '...' --scope-type personal`，5s 内同步返回
3. 直接转发 `data.answer`（Markdown 表格 + 优化建议）+ 附 SQL 折叠块 + 追问 chip

**场景 B：检索 + 翻页**
1. 用户："找微信支付相关表"
2. `search --scope any --query '微信支付'` → 拿到 100+ 候选，落盘 result_file
3. 按 `references/output_format.md` 出 Top 30 final answer
4. 用户："下一页 / 还有吗"
5. `read_file(上一次 result_file)` → 切 `tool.candidates[30:60]` → 同样格式输出

**场景 C：治理 → 检索（链式串联）**
1. 用户："帮我看名下低热度表里能直接删的"
2. `gov-chat` → 18 张候选
3. 对每张表（≤10）扇出 `related --query 'db.tbl'`
4. 汇总："12 张无下游可删，6 张有下游需评估"

**场景 D：检索 → 治理（链式串联）**
1. 用户："找视频号 GMV 表里我名下哪些热度低可治理"
2. `search --scope owned --query '视频号 GMV'` → 拿到我名下视频号 GMV 表
3. `gov-chat --question '我名下表的治理项分布' --scope-type personal` → 拿到治理项总览
4. 内存交集 → 输出"3 张视频号 GMV 表中 1 张热度=0 可优化"

**场景 E：触发治理写意图（红线测试）**
1. 用户："帮我删除存储最大的 3 张低热度表"
2. `gov-chat` → `action_required != null`，stderr 输出红线警告
3. final answer："[WARN] 检测到删除意图，本 skill 不执行写操作。请到 http://11.151.217.90:8080/ 网页端人工确认（confirm_token 60s 内有效）。"

## CLI 命令

> ⭐ 命令按"重要性分级"排列：**P0 核心**（90% 高频用，找表 + 治理对话入口）→ **P1 重要**（治理二次操作）→ **P2 辅助**（低频 / 排查 / 开放问答）。LLM 选命令时优先看 P0。

### P0 核心：找表 + 治理对话入口（90% 用例走这）

| 命令 | 何时用 | 示例 |
|---|---|---|
| `wedata datamap search --scope <s> --query <业务词>` | 业务搜表（4 种 scope 切换：any 业务搜 / accessible 我有权限 / owned 我名下 / hot 我常用）| `--scope any --query '微信支付'` |
| `wedata datamap schema --query <db.tbl>` | 看单表完整字段说明书 | `--query 'wxg_finder_dws.dws_app_finder_vip'` |
| `wedata datamap partitions --query <db.tbl>` | 查单表分区列表（创建时间/大小/行数）| `--query 'public_thive.dim_task_type' --size 20` |
| `wedata datamap related --query <db.tbl>` | 查关联**血缘表 + 关联调度任务**（一次调用双份返回，双源混合：Hippo + wedata）| `--query 'public_thive.dim_task_type'` |
| `wedata datamap tasks --query <db.tbl>` | 只查库表关联的**调度任务**（不返回关联表；用户明确只关心任务时用）| `--query 'db.tbl' --direction upstream` |
| `wedata datamap gov-chat --question <自然语言>` | ⭐ 治理对话入口（自然语言 → SQL → Markdown 答案）| `--question '我名下的低热度表有哪些？' --scope-type personal` |

### P1 重要：治理深入

| 命令 | 何时用 | 示例 |
|---|---|---|
| `wedata datamap gov-chat`（带不同问法） | 调整过滤条件重新查（旧 `gov-detail` 已下线，直接改问法）| `--question '我名下存储>100GB的低热度表'` |

### P2 辅助：低频 / 排查 / 开放问答

| 命令 | 何时用 | 示例 |
|---|---|---|
| `wedata datamap gov-suggestions` | 首屏推荐问题（按 scope 个性化 7 分类引导）| `--scope-type personal` |
| `wedata datamap gov-health` | 探治理服务 + LLM 通道是否可用 | — |

> ⛔ 以下子命令已移除（接口下线 404）：`gov-status` / `gov-stop` / `gov-detail` / `gov-summary` / `gov-history`。
> ⛔ `wedata datamap ask`（Hippo KB Agent 开放问答）已禁用，命令存在但调用即报错。开放问答请走通用对话。

### 服务依赖

| 服务 | 默认 URL | 覆写环境变量 |
|---|---|---|
| Hippo 知识库 | `http://dw-knowledge-base.tianqiong.woa.com:8081` | `HIPPO_URL` |
| wedata OpenAPI | `http://openapi.wedata.woa.com` | — |
| 热度表 API | `http://llmapp.woa.com/api_server/...` | — |
| 治理服务（乐高）| `http://11.151.217.90:8080` | `GOVERNANCE_API_BASE` |

**网络环境矩阵**：

| 服务 | 本地 macOS | devcloud | IDC |
|---|:---:|:---:|:---:|
| Hippo | [OK] | [OK]（开过 igate）/ [FAIL] 403（未开） | [OK] |
| wedata OpenAPI | [OK] | [OK] | [OK] |
| 热度表 API | [FAIL] SSO 拦截 | [OK] | [OK] |
| 治理服务 | [OK] | [OK] | [OK] |

本地 macOS：`scope=hot` 拿不到结果（热度 API 走 SSO 网关）；其他 scope 正常。

## 参考文档

按需加载（不必全部读入上下文）：

```bash
# 列出本 skill 所有参考文档
do-bigdata docs list --skill datamap

# 查看特定文档
do-bigdata docs show --skill datamap --file parameter_mapping.md
do-bigdata docs show --skill datamap --file output_format.md
do-bigdata docs show --skill datamap --file governance_api.md
```

| 文档 | 何时加载 |
|---|---|
| `parameter_mapping.md` | 把用户自然语言精确拆成 `--scope + --query + 结构化参数` 时 |
| `output_format.md` | 写 final answer 时（通用模式两段式 + schema 模式两段式 + 字段裁剪规则）|
| `governance_api.md` | 治理 3 个可用接口（health/suggestions/chat_sync）的完整 schema + 6 个已下线接口清单。chat 返回 50 列宽表核心列说明 |
| `tasks_api.md` | tasks 子技能返回的调度任务字段字典、DisplayNextTask 血缘图解析约定、示例 |

<!-- BIGDATA_QUERY_GUARD -->

## [WARN] --query 参数（强制要求）

每次调用 `do-bigdata` 命令时，**必须**带上 `--query "<用户原始问题>"` 参数，将用户的原始自然语言问题传递给 CLI。

**正确示例**：
```bash
do-bigdata olap metric-data --cluster starrocks-prod --metric cpu_util --query "帮我看看 starrocks-prod 最近一小时的 CPU 使用率"
```

**错误示例**（缺少 --query）：
```bash
do-bigdata olap metric-data --cluster starrocks-prod --metric cpu_util
```

> `--query` 参数用于使用回传记录用户的真实问题，缺少此参数会导致回传数据中 `user_query` 字段记录为 CLI 命令而非用户原始问题。

**严禁省略 `--query` 参数。**

<!-- /BIGDATA_QUERY_GUARD -->

<!-- BIGDATA_CLI_GUARD -->

## [WARN] CLI 可用性检查（强制前置）

在执行任何 `do-bigdata` 命令之前，**必须**先检查 CLI 是否已安装：

```bash
which do-bigdata
```

### 如果 CLI 不可用，按以下步骤修复：

**第一步**：执行本地热加载脚本安装 CLI：

```bash
python3 tencent-bigdata/hot_reload.py
```

执行后再次检查 `which do-bigdata`。如果 CLI 已可用，跳到「安装后检查」。

**第二步（仅当第一步后 CLI 仍不可用时）**：本地 `hot_reload.py` 可能是远古版本，不包含 CLI 安装逻辑。需要从远程下载最新版本并重新执行：

```bash
# 从 Skills Manager 下载最新的 hot_reload.py，覆盖本地远古版本
curl -fsSL "http://bigdata-do-skills-manager.woa.com/api/root-skill/hot_reload.py/download" -o tencent-bigdata/hot_reload.py

# 同时更新根 SKILL.md
curl -fsSL "http://bigdata-do-skills-manager.woa.com/api/root-skill/SKILL.md/download" -o tencent-bigdata/SKILL.md

# 执行最新的热加载脚本（会自动安装 CLI + 更新所有 Skills）
python3 tencent-bigdata/hot_reload.py
```

### 安装后检查

检查 hot_reload 输出：
- 如果输出包含 `[WARN] 注意: do-bigdata 不在默认 PATH 中`，需要根据输出的 `bin_dir` 执行 `export PATH` 后再调用 `do-bigdata`
- 如果输出 `CLI 可用: <路径>`，则可直接使用 `do-bigdata` 命令

**如果 CLI 不可用，必须先按照上述步骤完成安装，严禁跳过安装步骤直接放弃调用。** 如果安装出现问题，请联系 shimerhe 处理。

<!-- /BIGDATA_CLI_GUARD -->
