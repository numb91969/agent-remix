# 问图 (WenTu) — 腾讯地图数据问数助手

一站式腾讯地图数据问数专家，覆盖**手图 App、出行服务（打车/顺风车/代驾/货运/跑腿/快递/海外打车）、乘车码、地图+** 四大业务域。

## 六类核心能力

1. 指标口径 / 表结构 / DDL 知识查询
2. 离线数据查询（Iceberg/Hive/TDW → WeData）
3. 实时数据查询（StarRocks/MySQL/灯塔 → dola）
4. 埋点查询（曝光/点击/PUV/PV）
5. 数据异常排查（对不上/波动归因）
6. SQL 自检与优化

## 依赖

- **tencent-bigdata**（已内置）：离线 SQL 执行
- **dola**（已内置，首次使用需 OAuth 授权）：实时数据查询
- **工蜂 MCP**（需授权）：读取 git.woa.com `mobile-map-data/data_knowledge` 知识库
