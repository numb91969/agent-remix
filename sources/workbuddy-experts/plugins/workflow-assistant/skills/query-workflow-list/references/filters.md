# 筛选参数：query-workflow-list（`ListWorkflow`）

## 关键参数

| 参数 | 说明 | 本技能用法 |
|------|------|-----------|
| `ListType` | 列表类型（枚举：`FlowListTypeDefault`/`Admin`/`Edit`/`Focus`） | `Admin`=我是管理员的流程；`Focus`=我收藏的；不传=默认可见范围 |
| `IsPublic` | 是否公开（字符串） | `"true"`=仅公开流程 |
| `Category` | 流程分类（字符串） | 传**英文分类 code**（见下方分类映射） |
| `Status` | 流程**模板**状态（字符串，非数组） | 用户可见 3 态（见下方状态映射，⚠️ 不是流程单状态） |
| `Keyword` | 搜索关键词 | 名称/描述模糊匹配 |
| `SortBy` | 排序字段 | `InstanceCount`=按发起量；`CreateTime`/`UpdateTime`=按时间 |
| `SortOrder` | 排序顺序 | `desc`/`asc` |
| `Limit` / `Offset` | 分页 | 全量时每批 200，Offset 递增 |
| `AllowSubWorkflow` | 是否子流程 | 一般忽略 |

## 分类中文名 → 英文 code 映射（关键）

`Category` 必须传**英文分类 code**，但用户常说中文。平台当前共 4 个分类，映射如下（已通过实际数据核实）：

| 用户说的中文 | 传的 `Category` 值 | 代表流程 |
|------------|------------------|---------|
| 产商品库 | `ProductsHouse` | 商品上架、产品树新建、私有云产品出海 |
| 计费平台 | `QcbuyPlatform` | 计费接入审批、计量差错、公有云下单、折扣异常 |
| 官网平台 | `QcloudPlatform` | 平台子用户权限收敛、事件中心、配额中心、待办 |
| 其他 | `OtherFlow` | 演示分组、批量通过审批单据、通用审批流 |

> 口语引导：产商品库/商品/产品→`ProductsHouse`；计费/交易/下单/折扣→`QcbuyPlatform`；官网/平台/事件中心/配额→`QcloudPlatform`；其他/杂项→`OtherFlow`。
> **严禁瞎猜英文 code**：若用户提到的分类无法对应上述 4 类，先不带 `Category` 拉一次公开流程，从返回结果的 `Category` 字段核对后再精确筛选。

## 状态映射（`Status`，⚠️ 流程模板状态，非流程单状态）

`ListWorkflow.Status` 是**流程模板/图纸本身的上线状态**，与流程单（实例）的 Running/Succeed 完全不同。用户可见状态只有 **3 种**；「未启用」= 后端 `Ready`（就绪）+ `Draft`（草稿）合并，用户不区分：

| 用户说的（只会问这 3 种） | `Status` 值 | 展示 |
|------------------------|------------|------|
| 已启用 / 已上线 / 生效中 / 在用的 / 能用的 | `Enable` | ✅ 已启用 |
| 已停用 / 已下线 / 停用的 / 禁用 | `Disable` | ⛔ 已停用 |
| 未启用 / 还没启用 / 没上线的 / 草稿 / 就绪 | `Ready` 或 `Draft` | ⚪ 未启用 |

> `Status` 传**字符串单值**（如 `"Enable"`），不是数组。
> **「未启用」对应两个原始值**（`Ready`/`Draft`），单值 `Status` 无法一次覆盖——用户要筛「未启用」时，**先不带 `Status` 拉全量，再在本地保留 `Status ∈ {Ready, Draft}`**，展示统一渲染为「⚪ 未启用」。
> **严禁把流程单状态（Running/Succeed/Failed/Revoked/Pending）传给 `ListWorkflow.Status`**——那是 `ListWorkflowInstance` 等流程单查询工具的取值。

## 发起量排序

- 最多发起量在前：`SortBy:"InstanceCount", SortOrder:"desc"`
- 最少在前：`SortBy:"InstanceCount", SortOrder:"asc"`
- 若工具不支持该 `SortBy`，则全量拉取后在本地按 `InstanceCount` 字段排序后输出。
