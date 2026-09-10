# Phase 1 列名同义词字典（column-aliases）

> **定位**：本文是 Phase 1 算法（A.1 列级语义识别 / A.4 行结构展开 / 4 段名称组装）依赖的**单一权威源**。新增列别名只在本文添加，下游脚本与 reference 文档统一引用本文。
>
> **不要**在 `how-to-parse-product-list.md` / `how-to-classify-tokens.md` 等正文里复述本文表格——只在使用处用 `参见 [column-aliases.md](data/phase1-token-dict/column-aliases.md) §X` 形式引用。

## 规范化匹配函数

```text
normalize(name) = lower(strip(name, [spaces | dashes | underscores]))
```

判断列名是否命中某语义：先 `normalize(候选列名)`，再与对应表格的「规范化形态」列做集合判断。

示例：

- `Sub Product Name` → `subproductname`
- `four-level-code` → `fourlevelcode`
- `产品名称` → `产品名称`（中文不归一化）

## 表 1：SPUID

| 原始列名形态 | 规范化形态 |
|---|---|
| `SPUID` / `SpuId` / `SpuID` / `spuid` / `SPU ID` / `Spu Id` | `spuid` |
| `spu_id` / `spu-id` | `spuid` |

## 表 2：四层编码

| 原始列名形态 | 规范化形态 |
|---|---|
| `四层编码` / `四层Code` / `四层 Code` | `四层编码` / `四层code` |
| `四层` | `四层` |
| `four level code` / `four_level_code` / `four-level-code` / `FourLevelCode` | `fourlevelcode` |
| `four level` / `FourLevel` / `fourLevel` | `fourlevel` |

任一规范化形态命中即视为四层编码列。

## 表 3：四层定义名称 · 一级（产品）

| 原始列名形态 | 规范化形态 |
|---|---|
| `产品名称` | `产品名称` |
| `Product Name` / `product name` / `productName` / `product_name` | `productname` |
| `产品名` | `产品名` |

## 表 4：四层定义名称 · 二级（子产品）

| 原始列名形态 | 规范化形态 |
|---|---|
| `子产品名称` | `子产品名称` |
| `SubProduct Name` / `subProductName` / `sub_product_name` / `sub-product-name` | `subproductname` |
| `子产品名` | `子产品名` |

## 表 5：四层定义名称 · 三级（组件类型 / 计费项）

| 原始列名形态 | 规范化形态 |
|---|---|
| `组件类型` | `组件类型` |
| `Component Type` / `component type` / `componentType` / `component_type` | `componenttype` |
| `计费项` | `计费项` |
| `billingItem` / `billing_item` / `billing-item` / `BillingItem` | `billingitem` |
| `ValueItemName` / `valueItemName` / `value_item_name` | `valueitemname` |

## 表 6：四层定义名称 · 四级（组件名称 / 计费细项）

| 原始列名形态 | 规范化形态 |
|---|---|
| `组件名称` | `组件名称` |
| `Component Name` / `component name` / `componentName` / `component_name` | `componentname` |
| `计费细项` | `计费细项` |
| `subBillingItem` / `sub_billing_item` / `sub-billing-item` / `SubBillingItem` | `subbillingitem` |
| `ValueSubItemName` / `valueSubItemName` / `value_sub_item_name` | `valuesubitemname` |

## 表 7：四层定义名称 · 单列兜底

当输入材料没有 4 段拆列、但有单一列承载完整路径时识别。

| 原始列名形态 | 规范化形态 |
|---|---|
| `四层定义名称` | `四层定义名称` |
| `四层路径` | `四层路径` |
| `Four Level Name` / `four_level_name` / `four-level-name` / `FourLevelName` | `fourlevelname` |

## 维护原则

1. **只增不删**：新发现的列名变体只在表格末尾追加，禁止删除已有形态（向后兼容）
2. **数据驱动**：新增列名同义词不需要改脚本逻辑，只改本表
3. **中英文均保留**：中文列名（如 `产品名称`）和英文列名（如 `Product Name`）必须各自列出·不能省
4. **大小写不敏感 + 空格/连字符/下划线归一化**：通过 `normalize()` 函数实现·这是与 gate 脚本 / A.1 算法约定的契约

## 与 abc-refactor 的关系

abc-refactor A5/A6 步骤的「识别已有 SPUID / 四层编码」在本文落地为**列名维度**的识别清单；token 维度（cell 值的格式校验）由 [`how-to-classify-tokens.md`](../../how-to-classify-tokens.md) 和 [`check-phase1.mjs`](../../../scripts/check-phase1.mjs) 承担。
