# 探元 MCP Tool 参考（tanyuan-wb-mcp-server）

> 本文件是 `tanyuan-search` 技能内部的 MCP 工具参考，供 Agent 在执行时快速查阅工具入参、出参与语义。
> 原先的 HTTP 接口脚本（`search-relics.js`、`search-knowledge.js`）已删除，禁止调用。所有检索必须通过 MCP 工具完成。

## MCP 服务端点

MCP 协议：Streamable HTTP。

| 环境 | 端点地址 |
|---|---|
| 测试 | https://test-api.tanyuan.qq.com/wb/mcp |
| 正式 | https://api.tanyuan.qq.com/wb/mcp |

> 已在专家根目录 `.mcp.json` 中配置为 `tanyuan-wb-mcp-server`，`plugin.json` 通过 `dependencies.mcpServers` 引用。鉴权由平台级统一 API Key 托管注入请求头，无需手动配置。

## 通用约定

- 调用失败时统一返回 `success=false` + `errorMessage`，须先判断 `success` 再取结果。
- 工具通过 MCP 连接器系统调用，工具名前缀为 `mcp__tanyuan-wb-mcp-server__`。
- **`datasourceType`**（仅 `search_relics`）：
  - `0` = 文物数据库（默认）
  - `1` = 世界文化遗产数据库

---

## 1. `search_movable_relics`（知识库检索 · 原 search-knowledge.js）

根据自然语言问题，检索相关的可移动文物文献片段。对应原先的知识库检索能力。后端使用关键词 + 向量语义检索 + Rank，返回多段综合文本。

### 适用场景

开放 / 语义性问题（背景、原因、工艺、故事、鉴赏、对比论证、攻略、研学）。快，语义覆盖好，是多数问答首选。query 宜短（通常 2–4 个词），只保留核心实体 + 单一主要意图，不堆砌维度词；需要多维度时拆成多个精简子 query 分别检索。

### 入参

| 参数名 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `query` | string | 是 | 检索问题，如"蟠螭纹柱状足铜甗的纹饰特征" |
| `topK` | integer | 否 | 返回结果条数，默认 10 |

### 出参

```json
{
  "success": true,
  "errorMessage": null,
  "result": [
    {
      "id": "string",
      "content": "命中内容",
      "contentChunkIds": ["string"],
      "contextPrefix": "子标题",
      "documentId": "string",
      "documentName": "string",
      "chunkIndex": 0,
      "score": 0.0,
      "startIndex": 0,
      "endIndex": 0,
      "categoryId": "string",
      "confidence": 0.0
    }
  ],
  "total": 10,
  "mode": "hybrid"
}
```

| 字段 | 类型 | 说明 |
|---|---|---|
| `success` | boolean | 是否成功 |
| `errorMessage` | string | 失败原因，成功时为 `null` |
| `result` | array | 命中结果列表 |
| `total` | integer | 命中总数 |
| `mode` | string | 检索模式 |

`result` 元素字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | string | 结果 ID |
| `content` | string | 命中内容 |
| `contentChunkIds` | array\<string\> | 相邻内容片段 ID |
| `contextPrefix` | string | 子标题 |
| `documentId` | string | 文档 ID |
| `documentName` | string | 文档名称 |
| `chunkIndex` | integer | 片段序号 |
| `score` | number | 相关度得分 |
| `startIndex` | integer | 起始位置 |
| `endIndex` | integer | 结束位置 |
| `categoryId` | string | 分类 ID |
| `confidence` | number | 置信度 |

---

## 2. `search_oracle_bone_character`（甲骨文单字检索 · 新增）

根据包含具体汉字的问题，检索该字对应的甲骨文字形、读音、释义等信息。

### 入参

| 参数名 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `query` | string | 是 | 要查询的汉字或问题，如"山的甲骨文" |

### 出参

```json
{
  "success": true,
  "errorMessage": null,
  "result": [
    {
      "confidence": 0.63,
      "content": "命中内容",
      "docName": "字头表v5 (1).csv"
    }
  ],
  "references": []
}
```

| 字段 | 类型 | 说明 |
|---|---|---|
| `success` | boolean | 是否成功 |
| `errorMessage` | string | 失败原因，成功时为 `null` |
| `result` | array | 命中结果列表 |
| `references` | array | 引用来源，通常为空数组 |

`result` 元素字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `confidence` | number | 置信度 |
| `content` | string | 命中内容 |
| `docName` | string | 文档名称 |

---

## 3. `search_relics`（文物数据库检索 · 原 search-relics.js）

根据自然语言问题，在文物或世界文化遗产数据库中进行生成式检索。后端根据 `datasourceType` 使用对应 Text2SQL prompt，将完整自然语言问题转换为只读 SQL；调用方不写 SQL，也不应把问题压缩成关键词串。

### 适用场景

结构化事实的详情、列表、统计、分组和排行查询。`datasourceType=0` 查询数据库内文物；`datasourceType=1` 查询世界遗产及其关联数据。

### 入参

| 参数名 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `query` | string | 是 | 保留全部有效条件、问题形态和返回意图的自然语言问题（后端 NL→SQL） |
| `datasourceType` | integer | 否 | 数据源类型：`0`=文物（默认），`1`=世界文化遗产 |

### datasourceType=0：文物数据库

后端基于 MySQL 查询文物及已上架商品资产。调用方构造 query 时应保留：

- 结构化过滤：年代、类型、类别、等级、馆藏机构、创作者、出土地
- 明确文物实体名：完整专名保持完整；简称需明确其不完整性
- 普通文本概念：器类、题材、工艺、文化主题、颜色等保持完整组合词
- 问题形态与返回意图：详情/列表/统计/排行，以及希望返回的业务字段

出参示例：

```json
{
  "success": true,
  "errorMessage": null,
  "result": [
    {
      "name": "青花瓷刻花斗笠碗",
      "alias": "",
      "years": "宋",
      "category": "瓷器",
      "type": "可移动文物",
      "level": "二级文物",
      "museumName": "武汉市江夏区博物馆",
      "size": "口径：12.2、底径：4.4、高：5厘米",
      "cover": "https://...",
      "basicIntroduce": "敞口，圆唇……"
    }
  ],
  "total": 10,
  "datasourceType": 0
}
```

`result` 元素字段 — 文物（datasourceType=0）：

| 字段 | 类型 | 说明 |
|---|---|---|
| `name` | string | 名称 |
| `alias` | string | 别名 |
| `years` | string | 年代，如"宋""明""清" |
| `category` | string | 类别，如"瓷器" |
| `type` | string | 类型，仅指"可移动文物/不可移动文物"；青铜器、瓷器、古建筑等属于 `category` |
| `level` | string | 文物级别（一级/二级/三级/一般文物） |
| `museumName` | string | 藏馆名称（馆藏机构），与 `place`（出土地）不得混用 |
| `creator` | string | 创作者 |
| `place` | string | 出处/出土地，不是馆藏机构 |
| `size` | string | 尺寸 |
| `cover` | string | 封面图 URL（已授权，可直接嵌入回答） |
| `basicIntroduce` | string | 基本介绍 |
| `featureIntroduce` | string | 特征介绍 |

> 注意：`type` 仅指可移动文物/不可移动文物，青铜器、瓷器、古建筑等属于 `category`。`museumName` 是馆藏机构，`place` 是出土地，二者不得混用。颜色只能作为普通文本概念，不可直接按自然语言颜色过滤。

### datasourceType=1：世界遗产数据库

后端基于 PostgreSQL 查询 UNESCO 世界遗产主表及关联数据。主表可查询：名称、国家、洲别、入选年份、类别、评定标准、濒危状态、坐标、缩略图、封面与简介；关联层包括 OUV 声明、保护状态、历史事件、引用、知识卡片、叙事、媒体、每日推荐及用户贡献等。

- 洲别：亚洲、欧洲、非洲、美洲、大洋洲
- 类别：文化、自然、混合、预备名单
- 可按 UNESCO 标准编号（如 `(i)`、`(iv)`）、濒危状态、年份等筛选
- 非遗和传统技艺不属于此结构化数据库；开放问题应使用 `search_movable_relics`

出参示例：

```json
{
  "success": true,
  "errorMessage": null,
  "result": [
    {
      "id": "forbidden-city",
      "name": "故宫",
      "country": "中国",
      "continent": "asia",
      "inscribedYear": 1987,
      "category": "cultural",
      "criteria": ["i", "ii", "iii", "iv"],
      "inDanger": false,
      "thumbUrl": "https://...",
      "intro": "北京故宫于1987年被列入《世界遗产名录》……"
    }
  ],
  "total": 1,
  "datasourceType": 1
}
```

`result` 元素字段 — 世界遗产（datasourceType=1）：

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | string | 遗产标识 |
| `name` | string | 名称 |
| `country` | string | 所属国家 |
| `continent` | string | 所在大洲 |
| `inscribedYear` | integer | 列入名录年份 |
| `category` | string | 类别，如"cultural" |
| `criteria` | array | 入选标准，如 `["i","ii"]` |
| `inDanger` | boolean | 是否濒危 |
| `thumbUrl` | string | 缩略图 URL（已授权，可直接嵌入回答） |
| `intro` | string | 简介 |

> null 字段不返回。调用失败时返回 `success=false` + `errorMessage`，须先判断 `success` 再取结果。

---

## ⚠️ 返回条数 ≠ 总数

`search_relics` 的 `total` 是本次返回的行数，受后端检索条数上限约束（常见约 10 条），**并非库中符合条件的匹配总数**；当它达到上限时通常意味着还有更多记录未返回。Agent 不得将其当作总数或全集，也不得据返回的若干条臆造统计结论。组织回答时用"其中几件""可能还有更多"等自然表述，仅当为明确的统计（COUNT）查询并返回统计值时才给出数量。
