# SPU (CPQ) 报价

当用户输入包含 CPQ `spuId`（标准产品单元 ID，例如 `14339`、`18795`）时，先用 `tcloud-price spu` 解析它再决定报价路径。`spu` 走的是 panshi OMP 内网链路，与下单页报价（`quote`）是不同的认证域和数据源。

## 三分支决策

```text
输入含 spuId?
├── 否 → 走下单页报价 tcloud-price quote（与今天一致）
└── 是 → tcloud-price spu resolve 解析四层
        ├── 四层完整（情况 1.1）→ tcloud-price spu quote 返回 CPQ 刊例价
        └── 仅二层（情况 1.2，如 CVM）→ 按返回的 mappedProduct 走 tcloud-price quote 下单页报价
```

判据：`getSpuInfo` 返回的 `productCode / subProductCode / billingItemCode / subBillingItemCode` 是否全部非空。全非空即情况 1.1，可直接四层报价；缺 `billingItemCode` 或 `subBillingItemCode` 即情况 1.2，计费项与 SKU 由后续业务规格决定，必须路由回下单页报价。`isNewLevel4` 不是判据。

## 命令

```bash
# 解析四层 + 路由判定（不报价），先跑这个判断走哪条路
tcloud-price spu resolve --site cn --spu-id 14339

# 情况 1.1：返回 CPQ 刊例价（刊例价/线性价单价）
tcloud-price spu quote --site cn --spu-id 14339
tcloud-price spu quote --site cn --spu-id 18795 --sale-mode prepay
tcloud-price spu quote --site intl --spu-id 30522
```

站点映射：`--site cn` → OMP `envId 4` / 网关 `site 1` / `CNY`；`--site intl` → OMP `envId 121` / 网关 `site 2` / `USD`。`--sale-mode` 可选（`postpay` / `prepay` / `ripay`），不填时使用 `getSpuInfo` 返回的计费模式。

## 认证（环境变量签名，无交互登录）

`spu` 子命令用 panshi OMP 的 API Token 签名鉴权，从环境变量读取，skill 内不做登录或刷新：

- `PANSHI_API_TOKEN_KEY`（默认 `cpq-mcp`）
- `PANSHI_API_TOKEN`
- `PANSHI_API_STAFFNAME`

运行环境（沙箱）已预置这些变量。本地测试时先 `source scripts/panshi-token-env.sh`（参考 `scripts/panshi-token-env.example.sh`）。变量缺失、鉴权失败（HTTP 401/302 跳登录页）或内网不可达（`omp-service.tencentyun.com`）时，命令会如实报错；此时停止报价、照实说明，不得编造金额。

## 输出契约（情况 1.1）

CPQ 刊例价是**单价 / 线性价**（如 `0.13 元/个/小时`），来自 `queryInsuredPriceDetails`，**不是按数量或购买周期算好的总价**。遵守主 `SKILL.md` 的"禁止派生报价 / 禁止手算"：

- 只展示命令返回的 `priceType / priceUnit / productUnit / unitPrice / prices[]`，以及（如有）`insuredPrice / insuredPlan`。
- 不得用单价 × 数量、单价 × 周期、小时价转月价等任何方式派生总价。用户要总价时，说明这是单价口径，需要按业务规格走下单页报价。
- `quotes[].status` 为 `no-price` 表示该 saleMode 未返回可匹配价格，列为待确认，不得补值，也不得据此改判为情况 1.2。

### 多地域线性价（必须全列）

同一 saleMode 的 `latestPrice` 可能含**多条按地域区分的单价**（例如大多数地域 `0.13`、少数特殊地域 `0.195`）。此时 `quotes[].regionPrices[]` 会列出每条地域档，`quotes[]` 顶层 `unitPrice / prices` 仅是默认选中地域档（数组第一条），**不代表全部地域**，且可能不是大多数地域适用的那档。

- 当 `regionPrices` 长度 > 1（或 `note` 提示多地域）时，必须把 `regionPrices[]` 的**每条地域单价**都展示给用户，并标注各自适用的 `regionInfo.regionIds`；不得只报顶层 `unitPrice` 一个数字。
- 各地域档的金额逐字来自对应 `regionPrices[].unitPrice / prices[]`，不得在地域之间做任何换算或外推。
- `regionInfo.regionIds` 是地域 ID（非地域名），如需地域中文名以命令返回为准，不得自行映射臆测。

返回结构关键字段：

- `routing`：`cpq-four-level`（1.1）或 `order-page`（1.2）。
- `fourLevel`：四层编码 + `complete`。
- `quotes[]`：每个 saleMode 一条，含 `saleMode / payMode / timeUnit / priceUnit / unitPrice / prices[]`，以及多地域时的 `regionPrices[]`（每条含 `pid / isCareRegion / regionInfo / priceUnit / productUnit / unitPrice / prices[]`）。
- `orderPageRouting`（仅 1.2）：`mappedProduct`（如 `p_cvm` → `cvm`）、`implemented`、`nextStep`。

## 情况 1.2 路由

`spu quote` 命中 1.2 时不出价，只返回路由判定。按 `orderPageRouting.mappedProduct` 与 `nextStep` 改走下单页报价：先 `tcloud-price help --site <cn|intl> --product <mappedProduct>` 确认业务规格（地域、机型族、CPU/内存、磁盘、带宽等），再 `tcloud-price quote ...`。若 `implemented=false` 或映射不到已接入产品，说明无法自动报价，请人工确认产品后再报。
