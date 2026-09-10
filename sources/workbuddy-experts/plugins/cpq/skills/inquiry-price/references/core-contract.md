# core contract: summary.xlsx 强 schema + 退出码 + 委托规约

本文档定义所有 inquiry-price-\* core 必须遵守的对外契约。任何 core 违反本契约 ·
wrapper dispatcher 会在 schema 校验阶段拒绝（exit 1）。

## 1. summary.xlsx 强 schema

**必需的 9 个内置列**（参 spec §4.3）· 顺序不强制 · 名称必须一致：

| 列                          | 类型 | 含义                                                                                        |
| --------------------------- | ---- | ------------------------------------------------------------------------------------------- |
| `task_id`                   | str  | `task_001` / `task_002` ... · 序号即 source_table.md 数据行 1-based                         |
| `status`                    | enum | `pending` / `concluded` / `failed` / `asking` / `exception` / `timeout` / `aborted_by_user` |
| `rounds_taken`              | int  | 经历轮数（parallel 多轮；knot 固定 1）                                                      |
| `conversation_id`           | str  | knot 会话 id                                                                                |
| `download_links`            | str  | 远端报价单下载链接（多个用换行连接）                                                        |
| `remote_price`              | str  | 远端 `[价格]` 段原文逐字                                                                    |
| `four_layer`                | str  | 远端 `[四层]` 段原文逐字                                                                    |
| `last_round_answer_excerpt` | str  | 远端最后一轮回答原文前 200 字                                                               |
| `last_round_error`          | str  | 最后一轮错误信息                                                                            |

**源表头列在前**：source_table.md 第一行（表头）的所有原始列必须在 9 个内置列之前。
core 可以追加自己的扩展列在内置列之后 · 上游脚本忽略未知列。

## 2. 退出码语义

| code | 含义                                                                   |
| ---- | ---------------------------------------------------------------------- |
| 0    | 所有任务终态 · summary.xlsx 已就绪                                     |
| 10   | 存在 asking · 已写 pending.json · 等用户回答 · 仅 parallel core 可能产 |
| 1    | core 错误 / 输入校验失败                                               |
| 3    | CPQ 委托校验失败（gate 拒绝）· 由 wrapper dispatcher 抛出              |

## 3. CPQ 委托规约

cpq 主流程把 D 段委托给本 wrapper 时必须**同时 export 两个变量**（缺一个就 exit 3）：

```bash
# ⚠️ 必须 export · 不能只在 shell 局部变量里赋值 · 否则子进程 dispatch.py 读不到
export CPQ_SESSION_DIR="<cpq A 段 resolve-session-dir.mjs 的输出绝对路径>"
export CPQ_DELEGATION=1
RUN_DIR="$CPQ_SESSION_DIR/inquiry-run"
mkdir -p "$RUN_DIR"
```

`_cpq_delegate_gate.py`（wrapper dispatch.py 内集成）会校验：

- `CPQ_SESSION_DIR` 和 `CPQ_DELEGATION` 至少有一组完整信号（详见 `_cpq_delegate_gate.py` 三个信号定义）
- `<CPQ_SESSION_DIR>/phase1.md` 含 `<!-- phase1-done` 标记
- `<CPQ_SESSION_DIR>/context.md` 含 `<!-- context-done` 标记

校验失败 → wrapper exit 3 · cpq 主流程必须先回到 A 段补齐再重跑。

**典型踩坑**：只 export `CPQ_DELEGATION=1` 而忘了 export `CPQ_SESSION_DIR` → 信号 3
explicit 分支命中 → 但 `session_dir=None` → 错误信息「未能解析 CPQ_SESSION_DIR；
委托检测信号不一致」。修复 = 同时 export 两个变量。

## 4. core 不变量

每个 core 必须：

- 接受参数：`--source-table <path>` `--run-dir <path>` `[--common-context <str>]` `[--resume]`
- 产物：`<run-dir>/summary.xlsx`（必填 · 含上述 9 列） + `<run-dir>/summary.md`（可选 · 给用户看）
- core 进程崩溃时退出码 ≠ 0/10 · wrapper 透传给调用方

## 5. knot core 输出协议（JSON-over-SSE · 对 wrapper 透明）

`inquiry-price-knot` core 走 JSON-over-SSE sentinel 协议（**现行版本 v1B.1** · 自
2026-07-03 起）：远端把业务结果用 `[INQUIRY_RESULT_JSON_BEGIN] {...} [INQUIRY_RESULT_JSON_END]`
包裹的 JSON 嵌入 SSE `TEXT_MESSAGE_CONTENT` 文本流回客户端 · 客户端多层 gate 校验后 ·
openpyxl 本地写 `summary.xlsx` · 全程**不调** `download_file` 接口
（避开 OA SSO 拦截）。

**v1B.1 关键机制**（详见 [`docs/cpq/v1b-protocol/spec.md §12`](../../../../../docs/cpq/v1b-protocol/spec.md#12-v1b1-迁移2026-07-03--现行协议)）：

- **主键对齐**：客户端首轮 message 注入 `[CLIENT_ROW_ID_MANIFEST]` 声明每个 task_id 对应的
  `client_row_id` · 远端只需复述主键 · 不再要求字节级 echo 整行源数据
- **多定价项协同**：一行拆多定价子项时用 `remote_price_items` / `remote_price_total` /
  `four_layer_items` 三字段结构化表达 · 分隔符 `;\n`
- **skipped_rows**：合计行 / 说明行等非询价行显式声明 · 落到 xlsx 第二 sheet `SkippedRows`
- **client_row_id_split_map**：拆单场景 · 一源行拆多子行的双向一致声明
- **marker + ack 门禁**：首轮 answer 未见 `[INQUIRY_MODE_ACK: v1B]` → gate fail
- **9 层 gate**：sentinel / parse / schema / client_row_id / multi_pricing /
  skipped_rows / split_map / marker_ack / size · 任一 fail 触发 `MAX_GATE_RETRIES_V1B=2` 重输

**对 wrapper / 下游消费者透明**：

- `wrapper dispatch.py` 校验只看 §1 定义的 9 列内置契约 · knot core 满足即可 · 无需感知协议细节
- v1B.1 主 sheet 在 9 列内置之外**追加了 5 列扩展**（`client_row_id` / `source_row_id` /
  `billing_split_index` / `currency` / `remote_price_total`）· 属于 §1 允许的
  "core 追加扩展列" · 上游脚本忽略未知列即可
- `fill-phase4-1.mjs` 打开 summary.xlsx 按列名读 cell value · 与其它 core 等价 · 对 5 新列
  与 SkippedRows 第二 sheet **零感知** · 保持向后兼容

**协议规格 / 落地设计**：

- [`docs/cpq/v1b-protocol/spec.md`](../../../../../docs/cpq/v1b-protocol/spec.md)（§1-§11 为 v1B 历史设计 · §12 为 v1B.1 现行协议）
- [`docs/cpq/v1b-protocol/design.md`](../../../../../docs/cpq/v1b-protocol/design.md)（§1-§10 v1B · §11 v1B.1 落地）

**v1B.1 客户端参数扩展**：

wrapper `dispatch.py` 与 knot core `run_knot.py` 支持 `--client-row-ids <path>` CLI 参数（
JSON array of strings · 与 source_table 数据行数等长）· 用于预置 manifest。**resume 场景
不透传**（首跑已 dump 到 state.json · resume 从 state 读回）。

> **2026-07-07 修正**：`client_row_id` 行主键必须由**客户端生成**、远端仅原样透传复述
> —— 这是主键对齐校验成立的前提。故**外部不透传 `--client-row-ids` 时 · `run_knot.py`
> 会自动生成 `raw_1..raw_N` 并恒注入 `[CLIENT_ROW_ID_MANIFEST]`**（见
> `run_knot._generate_client_row_ids`）· validate 恒走严格对齐校验。不再有"未透传 →
> 放宽 → 远端自己起 client_row_id"这条路径（那会让 client_row_id 失去对齐意义 · 且远端
> 无 manifest 可复述会填空串直接 gate fail）。CPQ D 段委托场景亦然（D 段另有
> `source_row_index` 机制 · 与 v1B.1 主键正交 · 两者并存不冲突）。

**历史脚注**：2026-06-28 之前曾经存在过"v1A · 远端 final.xlsx 附件下载"协议 ·
因 `download_file` URL 撞 OA SSO 偶发返回登录页 HTML 而被完整移除。2026-07-03 v1B 升级到
v1B.1（删除 `_source_row` 字节级校验 · 迁到 `client_row_id` 主键对齐）· 一刀切迁移 ·
无过渡兼容层。当前协议的设计文档与代码符号仍沿用 v1B 名字（`OUTPUT_CONTRACT_V1B` /
`_output_contract_v1b.py` / `schema_version: "v1B"`）· 演化轨迹见
[`plugins/cpq/skills/inquiry-price-knot/SKILL.md`](../../inquiry-price-knot/SKILL.md)
末尾"历史脚注"段与 spec.md §12。
