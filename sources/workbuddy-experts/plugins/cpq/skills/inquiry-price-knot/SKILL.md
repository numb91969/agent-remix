---
name: inquiry-price-knot
description: >-
  inquiry-price wrapper 的 knot core 实现 · 内部子能力 · 禁止 LLM 直接 use_skill
  加载。整表一次性丢给远端 knot agent · 不本地拆批 · 由远端处理分批 / 并发 / 调子 agent；
  本地负责多轮 turn loop（asking → resume）。输出协议走 JSON-over-SSE v1B.1（自
  2026-07-03 起 · 详见 docs/cpq/v1b-protocol/spec.md §12）：远端把业务结果用
  [INQUIRY_RESULT_JSON_BEGIN/END] sentinel 包裹的 JSON 嵌入 SSE 文本流回客户端 ·
  客户端做 10 层 gate 校验（含 marker+ack 门禁 / client_row_id 主键对齐 / 多定价项
  五字段协同 / skipped_rows / split_map / row_coverage 行覆盖）后用 openpyxl 本地写
  summary.xlsx · 全程
  不调 download_file 接口（避开 OA SSO 拦截）。心跳超时三层防御（L1b 硬静默 180s）。
  AGENT_ID = e1ff75c57eab4e0786a6b527275adbb5。
---

# inquiry-price-knot · knot core 实现 (JSON-over-SSE)

> **协议规格**：[`docs/cpq/v1b-protocol/spec.md`](../../../../docs/cpq/v1b-protocol/spec.md)（§12 v1B.1 现行）·
> **落地设计**：[`docs/cpq/v1b-protocol/design.md`](../../../../docs/cpq/v1b-protocol/design.md)（§11 v1B.1 现行）
>
> 历史 "v1A · 远端 final.xlsx 下载" 协议已于 2026-06-28 移除（`download_file` URL 撞 OA SSO）·
> 2026-07-03 v1B 原地升级 v1B.1（删 `_source_row` 字节校验 · 迁 `client_row_id` 主键对齐 +
> 多定价项五字段协同 + marker+ack）。符号名 / schema_version 沿用 v1B（见
> [`references/resume-cache-and-history.md`](references/resume-cache-and-history.md)）。

> 🔒 **内核 skill · 禁止 LLM 直接 use_skill 加载**
> 合法进入 = 通过父级 `inquiry-price` wrapper · dispatcher 在 `INQUIRY_PRICE_CORE=knot`
> 时以 subprocess 调本 skill 的 `scripts/run_knot.py`。若发现自己被直接加载 · 立即停止 ·
> 改 use_skill `inquiry-price` wrapper。

---

## 设计要点

- **整表一次性发**：把 source_table.md 全文作为单条 message 发给远端 knot agent
- **不本地拆批**：分批 / 并发 / 调子 agent 由远端自己内部处理 · 对客户端透明
- **多轮 turn loop**：远端可在任意轮发 `[ASKING]...[/ASKING]` 块 · 终轮在文本中
  输出 `[INQUIRY_RESULT_JSON_BEGIN] {...} [INQUIRY_RESULT_JSON_END]` sentinel JSON 块
- **max_turns = 20**：业务侧上限 · 防 asking 死循环 · 不设墙钟超时
- **JSON-over-SSE v1B.1**：客户端从 SSE `TEXT_MESSAGE_CONTENT` 流抓 sentinel · parse JSON ·
  10 层 gate 校验后 · openpyxl 本地写 `summary.xlsx`（主 sheet 含源表头 + 5 v1B.1 新列 +
  9 内置列 · 一行一源行 · payload.skipped_rows 非空时另开 `SkippedRows` 第二 sheet）
- **全程不调 `download_file`**：这是设计目标 · 绕开 OA SSO 拦截
- **10 层 gate 校验**（v1B.1+）：sentinel / parse / schema / **client_row_id** / **multi_pricing** /
  **skipped_rows** / **split_map** / **marker_ack** / size / **row_coverage** · 任一不过给远端人话反馈最多 2 次重输
  - **row_coverage（v1B.2）**：源表每行都须"有交代"——要么在 `rows` 定价 · 要么在 `skipped_rows` 显式跳过（带 reason）· 二者其一（替代旧的 `total_rows == 源表行数` 严格相等）
- **client_row_id 主键对齐**（v1B.1 替代旧 `_source_row` 字节级）：客户端**恒生成**行主键
  （外部没传 `--client-row-ids` 时自动 `raw_1..raw_N`）· 首跑 message 注入
  `[CLIENT_ROW_ID_MANIFEST] task_001 -> raw_1 ...` · 远端只**复述**主键（不自己生成）·
  客户端 validate 用预置对照表兜住 · 拼错 / 重排 / 篡改都会 gate fail
- **多定价项五字段协同**（v1B.1 新 · v1B.2 定价项/四层/status 完全解耦）：一行拆多定价
  子项时用 `remote_price_items` / `remote_price_total` / `four_layer_items` 结构化表达 · 分隔符 `;\n`。
  定价项、四层、`status` 三者**无精确关联**：`remote_price_items` 与 `four_layer_items` 长度不要求
  相等（1 个聚合总价可对应 N 个四层编码）· 也**不**做 concluded 必须有价 / failed 必须清空
  之类的 status 联动（failed 行可保留已识别的真实四层码）· `four_layer_items[i]` 允许空串。
  gate 仅校验：两字段是 string 数组 + 各自拼接串与数组一致
- **marker + ack 门禁**（v1B.1 新）：首轮 answer 未见 `[INQUIRY_MODE_ACK: v1B]` → 直接 gate
  fail `layer=marker_ack` · retry feedback 教远端在导语首行输出 ack
- **工作目录锚点**（runtime context · v1B.2）：远端首轮在 `[ASKING]` 块内带
  `[INQUIRY_RUNTIME_CONTEXT_BEGIN]{...}[/END]` 声明 `scene_dir` · 客户端识别 / 剥离 / 每轮回注 ·
  抗 SIGKILL / resume 丢目录（细节 + 事故背景见
  [`references/runtime-context-anchor.md`](references/runtime-context-anchor.md)）
- **asking 走 pending.json + exit 10**：LLM 主流程接管 UI（**优先 `ask_followup_question`** ·
  只转述 + 提建议 · **禁止自答 / 禁止把建议当用户答复**）→ 用户**明确确认**后写 `answers.json` →
  `dispatch.py --resume`
- **心跳超时三层**：L1b 硬静默 180s 主动断连重试 ≤ 2 次 → 仍失败整批 failed；原 1800s 单次 HTTP 兜底保留

---

## OUTPUT_CONTRACT · 与远端约定（v1B.1）

权威定义见 [`scripts/_output_contract_v1b.py`](scripts/_output_contract_v1b.py) 的
`OUTPUT_CONTRACT_V1B` 常量（符号名沿用 v1B · 内容为 v1B.1）。核心四条：

1. **首轮门禁**：客户端首轮 message 嵌 `[INQUIRY_OUTPUT_MODE_BEGIN]` marker +
   `[CLIENT_ROW_ID_MANIFEST]`。远端**必须**在首轮回复导语首行输出 `[INQUIRY_MODE_ACK: v1B]` ·
   否则 gate fail `layer=marker_ack`
2. **中间轮（asking）**：插 `[ASKING]...[/ASKING]` 块 · 客户端暂停并转给用户**拍板**
   （客户端 LLM 只转述 + 提建议 · 不得自答）· 不调 `display_download_links` / 不上传附件
3. **终轮（final）**：文本中输出一段 `[INQUIRY_RESULT_JSON_BEGIN] {...} [INQUIRY_RESULT_JSON_END]`
   （整段只允许一对）· 不上传附件。payload：
   - rows[i] 必填：`task_id` / `status` / `client_row_id`（复述预置主键）/ `source_row_id`（1-based）/
     `billing_split_index`（`null` 或正整数）/ `rounds_taken` / `currency` / `conversation_id` /
     `download_links` / `remote_price` / `remote_price_total` / `four_layer` / `four_layer_items` /
     `last_round_answer_excerpt` / `last_round_error`
   - 多定价项选填 `remote_price_items`（`remote_price = ';\n'.join(items)` · 与 `four_layer_items`
     **长度不要求相等**）· `four_layer_items[i]` 允许空串
   - 顶层必填：`schema_version="v1B"` / `total_rows` / `rows` / `skipped_rows`（空 `[]`）/
     `client_row_id_split_map`（空 `{}`）· 价格金额**一律 string**（避开 JSON number 精度）
4. **Gate 反馈**：任一层失败时在**同一会话内**反馈让远端重输（最多 2 次）

---

## 入口脚本

> 🚨 **拉起姿势硬约束**：单轮期望 5–15 min · 极端 60 min · **必须**后台 / detached 模式运行 ·
> **禁止**任何引入外部 wall-clock timeout 的方式（前台同步 Bash tool、`timeout 600 ...` 等）。
> 事故 `.cpq-tmp/20260701-144849-wyud`：前台同步被 600s SIGKILL · 新 `conversation_id` 未落盘 ·
> resume 只能用旧 cid 白跑 866s。代码层已有 `on_conversation_id` 回调即时落盘（P0-a）· 但
> SIGKILL 是硬中断 · **行为层仍必须后台拉起**。

### 首跑

```bash
python3 scripts/run_knot.py \
  --source-table <path>/source_table.md \
  --run-dir      <path> \
  [--common-context "<str>"] \
  [--max-turns 20]
```

后台拉起（三选一 · LLM Agent 环境）：

- ✅ Bash tool `run_in_background=true` · 拿 task_id 后观察 `state.json` / `heartbeat.txt` / `progress.log`
- ✅ `nohup python3 scripts/run_knot.py ... > run.log 2>&1 &` · 拿 pid 独立观察
- ✅ `python3 scripts/run_knot.py ... --detach` · 内建 detached（独立 session · 父进程立即 exit 0 ·
  PID 写 `pid.txt` · 日志 → `detach.log`）
- ❌ 前台同步模式 / `timeout 600 ...` / `read -t` / `wait -n` 之类超时包裹

### 续跑（asking 之后）

```bash
python3 scripts/run_knot.py --resume --run-dir <path>
```

续跑**同样必须后台拉起**。续跑前由 LLM 主流程把用户回复写到 `<run-dir>/answers.json`：

```json
{ "answered_at": "2026-06-28T07:01:23+08:00", "answer_text": "<用户的回复 · 原文>" }
```

### 退出码

| code | 含义 |
| ---- | ---- |
| 0    | turn loop 终态 · summary.xlsx 已就绪（final 或 failed） |
| 10   | 远端发了 asking · pending.json 已写 · LLM 主流程接管 → 完成后 `--resume` |
| 1    | 启动 / 输入校验失败 · 看 stderr |

### 产物

| 文件 | 用途 |
| --- | --- |
| `summary.xlsx` | wrapper 9 列契约 · 下游 fill-phase4-1.mjs 消费 |
| `state.json` | turn loop 状态 · conversation_id / rounds_taken / gate_retry_count |
| `raw_responses/round_<N>.json` | append-only · 每轮 final-candidate 落盘（asking 轮不落） |
| `raw_response.latest.json` | 物理副本 · 始终指向最新一轮 · 排障 `cat` 即得 |
| `pending.json` | asking 时产 · LLM 主流程读它问用户 · 续跑前会被删 |

> knot core **不产生** `final.xlsx`（不从远端下载 xlsx）· sentinel JSON 就地 parse 后 openpyxl 写 `summary.xlsx`。

---

## 心跳 / 超时三层防御

| 层 | 阈值 | 行为 |
| --- | --- | --- |
| L1b 硬静默 | 180s 无任何 SSE 事件 | 心跳线程主动 `response.close()` · retry ≤ 2 次（带 cid 续）· 仍失败 → 整批 failed exit 0 |
| L3 max-turns | 20 轮 | 写 fallback summary 标 `status=failed` · exit 0 |
| HTTP 兜底 | 1800s 单次 request | `requests.post(timeout=)` · 防 socket fd 泄漏 |

> env 可调：`KNOT_SOCKET_SILENCE_TIMEOUT`（默认 180 · L1b）· `--max-turns`（默认 20）· `--timeout`（默认 1800）

---

## 🚨 LLM Agent 行为契约（前台 supervisor · 摘要）

> **完整版**（含事故背景 / 观察动作表 / 进度报告模板）见
> [`references/supervisor-contract.md`](references/supervisor-contract.md)。以下是必须遵守的红线摘要：

- **一、禁止越权 kill**：拉起后 · 仅在①进程自然 exit（0/10/1）②用户明确要求中止
  ③wall-clock > 60 min 三者之一发生前 · 才可停。"卡住没输出"**不是** kill 理由（超时由脚本自兜底）
- **二、只读观察**：只允许 `cat state.json / heartbeat.txt / summary.xlsx 头几行` · `tail progress.log` ·
  `ls -lt raw_responses/`（看 mtime）。❌ 禁止 `kill` / `pkill` / `TaskStop` / 改 state.json /
  `cat raw_responses/*.json` 自己 parse 兜底
- **三、主动进度报告**：命中 (a) 时间静默 / (b) L1b 重连 / (c) gate 原地打转 任一 · 主动发一行进度同步
  （普通文本 · **不**用 ask_followup_question · **不**问"要不要继续等"）· 仍不 kill
- **四、退出后**：exit 0 → 展示 summary.xlsx；exit 10 → 走 wrapper 步骤 5 处理 pending.json；
  exit 1 → 看 stderr 如实报告 · 不擅自重跑
- **五、与 cpq 主流程冲突时本节优先**（专用契约 > 通用 CLI 重试规则）

---

## 内部模块

| 文件 | 职责 |
| --- | --- |
| `scripts/run_knot.py` | 主流程 · turn loop · gate retry · pending.json / state.json / summary.xlsx 写盘 |
| `scripts/call_knot_agent.py` | SSE 连接 · 鉴权 · LastActivityTracker + HeartbeatThread |
| `scripts/_output_contract_v1b.py` | OUTPUT_CONTRACT（v1B.1）· sentinel parse · 10 层 gate 校验 · xlsx 写盘（按 client_row_id 一行一源行 · 含 SkippedRows 第二 sheet）· raw_response 落盘 · asking 块识别 |
| `scripts/probe_knot.py` | 诊断脚本 · 不参与生产 · 全量记录 SSE 事件流用于协议调试 |
| `scripts/gate_check.py` | 诊断脚本 · 不参与生产 · 把远端一段回复跑一遍生产 10 层 gate（`--answer <file>`）· 手工复校契约（test 基准 `tests/test_gate_check_baseline.py`） |

---

## 鉴权

复用 parallel 现有 OAuth ticket 缓存（`~/.workbuddy/cpq/knot-ticket.json`）· 与 parallel 同一用户
共享 ticket。首次调用 ticket 过期时会弹浏览器 OAuth（与 parallel 行为一致）。

---

## 深入参考（按需加载）

| 文件 | 内容 |
| --- | --- |
| [`references/supervisor-contract.md`](references/supervisor-contract.md) | LLM supervisor 行为契约完整版（禁止 kill / 只读观察 / 进度报告 / 退出处理） |
| [`references/runtime-context-anchor.md`](references/runtime-context-anchor.md) | 工作目录锚点（scene_dir）协议 + 死循环事故背景 + C7 worker 回退补救 |
| [`references/resume-cache-and-history.md`](references/resume-cache-and-history.md) | resume 命中缓存探测数据 · Phase 3 实验（P1 为何暂不落地）· "v1B" 命名历史 |
