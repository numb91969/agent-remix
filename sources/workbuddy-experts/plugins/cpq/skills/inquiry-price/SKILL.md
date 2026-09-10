---
name: inquiry-price
description: >-
  腾讯云客户报价的统一询价适配器 · CPQ skill 的内部子能力 · 也可被独立调用。
  路由到内部 core skill（knot 默认 · 由环境变量 INQUIRY_PRICE_CORE 切换）·
  对外承诺统一的 summary.xlsx 强 schema（9 个内置列 + 源表头）。
  触发场景：multi-row 配置清单批量询价 · CPQ D 段委托询价 · 任何「帮我查这批
  产品的价格 / 整张表询价 / 批量报价」的请求。**不是 cpq 主流程的替代**——cpq
  仍然是客户报价业务的主入口；本 wrapper 仅负责询价这一具体子能力。
---

# inquiry-price · 询价适配器

> 设计依据：`docs/superpowers/specs/2026-06-26-inquiry-price-wrapper-design.md`

本 skill 是询价能力的**对外唯一入口**。LLM 加载本 skill 后看到的是统一的调用模板；
真正干活的内部 core skill 由环境变量 `INQUIRY_PRICE_CORE` 决定（默认 `knot`）。

## 🔒 调用契约

| 调用来源                                                                   | 合法性 | 备注                                                                                     |
| -------------------------------------------------------------------------- | ------ | ---------------------------------------------------------------------------------------- |
| 用户独立调用（"帮我查这批价格"）                                           | ✅     | 默认走 knot core                                                                         |
| CPQ 主流程 D 段委托                                                        | ✅     | 必须按 `references/core-contract.md §委托规约` 设 `CPQ_SESSION_DIR` + `CPQ_DELEGATION=1` |
| 兄弟 skill（如 tencent-cloud-pricing）反向引用                             | ✅     | 仅用于 precall gate 等检测 · 不绕过本 wrapper                                            |
| LLM 直接 use_skill core（`inquiry-price-parallel` / `inquiry-price-knot`） | ❌     | core SKILL.md 自我声明禁止 · 必须经本 wrapper                                            |

## 🎯 核心定位

加载本 skill 后 · 你（LLM）的角色：

- **机械搬运** 用户输入 → markdown 表格（步骤 2）
- **调 wrapper dispatcher**（步骤 3）· dispatcher 按 env 路由到内部 core
- **当 dispatcher exit 10 时**（knot / parallel 均会产）：读 `pending.json` → **提供建议但交用户拍板**（见步骤 5 §asking 阶段铁律）→ 收回答 → `--resume`
- **完成态**：读 `summary.xlsx` + `summary.md`（若存在）给用户展示

**永远不做**：推算价格 / 改写远端原文 / 替用户回答远端追问（**含拆批前的确认问题**）/ 自行判断该不该问 / **把自己的建议当成用户已确认的答复直接 `--resume`**。

## 六条铁律（继承自 parallel · 任一违反立刻回退）

1. 用户输入忠实搬运（字节级 · 不归一化 · 不翻译）
2. 服务端响应忠实展示（不抠数字 / 不汇总 / 不解释）
3. 客户端是双向管道（不替任何一方决策）
4. 产品归属交服务端（不本地推断产品名/规格语义）
5. 拆分 = 按行机械 fan-out · 不按语义重组（parallel core 现实现 · knot core 在远端等价做）
6. 价格值与单位只能原样搬运远端结构化返回 · 本地零数字运算

## 整体流程

```
用户输入 → [LLM] markdown 表格 → [LLM] 调 dispatcher
    ↓
dispatcher（按 INQUIRY_PRICE_CORE env 路由）
    ├─ knot（默认） → run_knot.py（JSON-over-SSE · 整表一次发 · 多轮 turn loop · max=20 轮）
    │   退出 0  → summary.xlsx（final 或终态 failed）
    │   退出 10 → pending.json + summary.xlsx（部分 · status=asking） · LLM 走步骤 5
    │
    └─ parallel（需 INQUIRY_PRICE_CORE=parallel）
        → build_proposal → split_tasks → parallel_orchestrator
        退出 0  → summary.xlsx + summary.md
        退出 10 → pending.json + summary.xlsx（部分） · LLM 走步骤 5
```

## 调用模板

### 步骤 1：检查环境

参 `references/input-parsing.md`（鉴权 / 依赖 / OAuth ticket 管理 · 由内部 core 处理）

### 步骤 2：用户输入 → markdown 表格

`.xlsx / .xls / .xlsm / .csv` 直接调本 skill 的 `scripts/parse_input.py`：

```bash
SKILL_BASE_DIR="<加载 inquiry-price skill 时的 Base directory>"
python3 "$SKILL_BASE_DIR/scripts/parse_input.py" \
  --input "<用户给的 .xlsx 路径>" \
  --output "$RUN_DIR/source_table.md"
```

其它输入类型（PDF / DOCX / 图片 / 自由文本）按 `references/input-parsing.md` 走 sibling skill
（pdf-extraction / docx-manipulation / xlsx-manipulation / LLM 视觉）转 markdown 后再用。

### 步骤 2.5：识别用户自然语言中的公共信息（如有）

仅白名单字段（站点 / 地域 / 计费模式 / 时长 / 数量 / 币种）整合成一句话作为 `--common-context`。
完整白名单与禁止识别内容参 `references/input-parsing.md §公共信息白名单`。

### 步骤 3：调 dispatcher（路由 + delegate gate + schema 校验）

```bash
# 独立调用（用户自己 use_skill 进来）：用默认随机路径即可
RUN_DIR="<workspace>/.tmp/inquiry-price-runs/run_$(date +%Y%m%d_%H%M%S)_$(openssl rand -hex 2)"

# 被 cpq D 段委托时（必须 export 两个变量 · 缺一个 dispatcher 都会 exit 3）：
#   export CPQ_SESSION_DIR="<cpq A 段 resolve-session-dir.mjs 的输出绝对路径>"
#   export CPQ_DELEGATION=1
#   RUN_DIR="$CPQ_SESSION_DIR/inquiry-run"
# 只 export CPQ_DELEGATION=1 而漏 export CPQ_SESSION_DIR 会触发
# 「未能解析 CPQ_SESSION_DIR；委托检测信号不一致」错误 · 这是典型踩坑。
# 详见 references/core-contract.md §3 + cpq/references/how-to-query-pricing.md 委托规约段。

mkdir -p "$RUN_DIR"

# 仅当切到 parallel core（INQUIRY_PRICE_CORE=parallel）：在调 dispatcher 之前必须
# 先按 parallel 的 SKILL.md 步骤 3-4 生成 tasks.json（build_proposal → split_tasks）·
# 因为第一版 dispatcher 直接调 parallel_orchestrator · 需要 tasks.json 已就绪。
# 默认的 knot core 不需要 tasks.json · run_knot.py 直接吃 source_table.md。
# 详见 references/core-contract.md。

python3 "$SKILL_BASE_DIR/scripts/dispatch.py" \
  --source-table "$RUN_DIR/source_table.md" \
  --run-dir      "$RUN_DIR" \
  [--common-context "<步骤 2.5 整合的字符串>"]
EXIT_CODE=$?
```

> 🚨 **前台 supervisor 强制约束 · 不要丢进 IDE background pool**
>
> dispatch.py 必须以**前台进程**方式启动 · LLM 同步等其退出码。**禁止**：
>
> - ❌ 把它放进 IDE / CodeBuddy 的 background shell（实测会被宿主在 ~12 min 静默回收 ·
>   远早于 30 min HTTP 超时 · 见 `inquiry-price-knot/SKILL.md §心跳超时三层` 之上的事故记录）
> - ❌ 用 `nohup ... &` / `&` 后台化后立刻去做别的事 · 让进程脱离 LLM 视野
> - ❌ 在 dispatch.py 没退出前主动 `kill` / `TaskStop` · 即使看起来"没输出"
>
> 进程运行期间 · LLM 必须遵守 `inquiry-price-knot/SKILL.md §LLM Agent 行为契约`：
>
> - 只允许只读观察 state.json / heartbeat.txt / summary.xlsx / progress.log
> - >2 min 无新事件时**主动**给用户一行进度同步（不要等用户来问）
> - 唯一允许的退出条件：进程自然 exit / 用户明确说停 / wall-clock > 60 min 兜底
>
> 如需 detach（如想离开 IDE 跑长任务）· 用 run_knot.py 的 `--detach` 模式（B.5 落地后可用）·
> 它会把进程托管到 `setsid` 独立会话并把 PID 写到 `<run-dir>/pid.txt` ·
> 续跑通过读 state.json 重建上下文 · 不通过 LLM 持有进程句柄。

退出码：

- `0` → 步骤 4（完成态展示）
- `10` → 步骤 5（处理 pending）· knot core 远端发 `[ASKING]` 时产 · parallel core 也产
- `1` → 失败 · 看 stderr · 终止
- `3` → CPQ 委托校验失败（cpq A 段未完成）· 回 cpq 主流程
- `11` → 进程异常消失（B.4 + D.9 落地后才会产 · state.json 显示有 PID 但已死）· 看 state.json
  最后状态 · 与用户商量重试还是切兜底

### 步骤 4：完成态展示

```bash
cat "$RUN_DIR/summary.md" 2>/dev/null || echo "（core 未产 summary.md）"
# 列出 summary.xlsx 中各 concluded 任务的 download_links · 提示用户本地汇总表路径
```

### 步骤 5：处理 pending.json（仅当文件存在）

> 🚫 **asking 阶段铁律（拆批前的确认问题 · 最容易被违反 · 违反即回退）**
>
> 询价初级阶段（远端拆批前）· 远端 knot agent 常发确认类问题（如：站点 / 地域是否为 X ·
> 计费模式取哪种 · 某产品规格是否按 Y 理解 · 要不要按某方案拆分）。**这些问题的答复权
> 100% 属于用户 · 你（LLM）只是双向管道 · 不是决策者。** 实测 agent 倾向"自己想通了就
> 直接答" · 这是明确禁止的行为。
>
> - ❌ **禁止**：自己判断答案 → 直接写 `answers.json` → `--resume`（哪怕你自认"很确定"）
> - ❌ **禁止**：把自己的建议当成用户已确认的答复
> - ❌ **禁止**：合并 / 省略远端的问题 · 或只挑"简单的"问用户、"难的"自己答
> - ✅ **必须**：把远端 `asking.text` 的**每一个**问题**如实转给用户**（不改写、不裁剪语义）
> - ✅ **应当**：对每个问题**给出你的推荐答案 + 一句理由**（帮用户决策 · 但不替他决策）
> - ✅ **必须**：**优先用 `ask_followup_question` 工具**呈现（见下 UX 规约）· 拿到用户的
>   明确选择 / 回复后**才**写 `answers.json`
>
> **`ask_followup_question` UX 规约（更好的确认体验）**：
>
> 1. 把 `asking.text` 拆成一个或多个结构化问题（一个远端追问 → 一道题）
> 2. 每道题的 `options` 里：把**你的推荐答案放在首位并标注「（推荐）」** · 再给其它合理选项 ·
>    并始终附一个「我要自己输入 / 其它」兜底项 · 让用户既能一键采纳建议也能自由改写
> 3. 多个独立问题一次性作为多道题提交（减少来回）· 需要多选时设 `multiSelect`
> 4. 若问题确实开放到无法列选项（如"请描述预期架构"）· 才退化为让用户自由文本回复 ·
>    但仍要先给出你的建议草稿供参考
> 5. 只有用户**明确确认 / 选择后** · 才把最终答复合并成一段字符串写入 `answers.json`
>
> **唯一例外**（无需再问用户 · 由脚本自动处理 · 你不用管）：C7 worker 回退补救 ——
> 远端"失忆"退回**已经确认过**的问题时 · `run_knot.py` 会自动重放 `answers_archive/` 里
> 的历史答复（bounded）· 这是代码路径 · **不是**授权你自答。

```bash
if [ -f "$RUN_DIR/pending.json" ]; then
  # 1) 读 pending.json 的 asking.text → 用 ask_followup_question 转给用户
  #    （每个问题附「推荐答案 +（推荐）标注 + 理由」· 但由用户拍板 · 禁止自答）
  # 2) 用户明确确认/选择后 → 把回复合并成一段字符串写到 answers.json（schema 见下）
  # 3) --resume 续跑
  python3 "$SKILL_BASE_DIR/scripts/dispatch.py" --resume --run-dir "$RUN_DIR"
fi
```

**`answers.json` schema（务必照抄 · 不要自己发挥）**：

```json
{
  "answer_text": "<用户对 asking.text 的原文回复 · 一段字符串 · 可含换行>"
}
```

> ⚠️ **常见笨格式（笨模型必踩 · run_knot.py 的 `read_answers` 已做兜底兼容 · 但请优先按标准 schema 写）**：
>
> - ❌ 写成数组：`[{"question": "...", "answer": "..."}, ...]`
> - ❌ 写成对象嵌套：`{"answer_text": {"q1": "..."}}`
> - ❌ 字段名笔误：`{"answer": "..."}` / `{"text": "..."}`
> - ✅ 唯一标准形态：`{"answer_text": "<字符串>"}`
>
> pending.json 的 `answers_schema` 字段也直接内嵌了 schema + example + common_mistakes ·
> LLM 可直接读 pending.json 取 schema · 无需回查本文档。

**knot core 支持 pending.json + exit 10**。当远端在某轮发
`[ASKING]...[/ASKING]` 块需要用户补信息时 · run_knot.py 写 pending.json + 部分
summary.xlsx（每行 status=asking）→ 退出 10 → LLM 走步骤 5 → `--resume` 续跑直到
final 或 max_turns 用尽。详细协议见 `inquiry-price-knot/SKILL.md`。

### 步骤 6（dispatch 自动挂载）：独立看门狗守护 —— 稳定进度 + 完成通知 + 自动续跑（agent 无关）

> **✅ knot core 首跑时 · dispatch 会自动拉起看门狗 · 你（LLM）无需手动起、也无需
> 手搓 `sleep + state.json` 轮询。** 这是**代码必经路径**（`dispatch._spawn_watcher_and_verify`）·
> 不依赖 agent 照文档自觉执行 —— 历史事故：步骤 6 曾是"推荐手动" · agent 直接跳过 ·
> 退回不可靠的手搓轮询 · 用户被迫追问"你在等什么"。现在改成 dispatch 强制挂载 · 根治。

> **⚠️ 仅 knot core（默认）自动挂载**：看门狗判据（终态词汇 / `pid.txt` / 顶层
> `last_turn_status`）照抄 knot 状态模型。parallel core 用**每 task 各自的 status** ·
> 无这些字段 · **不兼容** · dispatch 对 parallel **不**挂看门狗（parallel 用自己的
> `parallel_orchestrator.py --status`）。看门狗自身也有护栏：检测到 run_dir 非 knot
> 风格（state 无 `core=knot`）会自动关闭 auto-resume 退化为只读。

看门狗（`scripts/watch_inquiry.py`）每 30s 读 `state.json`（SSOT）· 追加进度到
`watch.log` · 命中终态发系统通知（macOS osascript）· core 被 SIGHUP 等信号端掉且
状态非终态时**自动 `dispatch.py --resume`**（补上"整棵进程树被端后没人续跑"的洞）·
支持 `cancel.txt` 取消。

**dispatch 自动完成（你无需执行）**：拉起 knot core 后立即 `Popen(watch_inquiry.py
--detach)` 并校验 `watch.pid` 存活（二道 gate · 起不来会打 ⚠️ 到 stderr）。

```bash
# 你（LLM / 用户）只需"观察"，不需要"启动"：

# 随时查看进度（任何时候 · 不影响任务）
tail -f "$RUN_DIR/watch.log"          # 实时进度流
cat    "$RUN_DIR/WATCH_STATUS.txt"    # 最新一行状态快照
cat    "$RUN_DIR/state.json"          # 原始 SSOT
cat    "$RUN_DIR/WATCH_DONE.txt"      # 命中终态后才有 · 最终摘要

# 取消任务
touch  "$RUN_DIR/cancel.txt"          # 看门狗下一轮停 core 并退出

# 兜底手动补起（仅当 dispatch stderr 出现"看门狗进程未确认存活"⚠️ 时）：
python3 "$SKILL_BASE_DIR/scripts/watch_inquiry.py" --run-dir "$RUN_DIR" --interval 30 --detach
```

**看门狗行为速查**：

| 检测到 | 动作 |
| --- | --- |
| `last_turn_status` ∈ 终态（`final_ok` / `*_exhausted` / `remote_failed` 等） | 系统通知「询价完成」+ 写 `WATCH_DONE.txt` + 退出 0 |
| `last_turn_status == asking` | 系统通知「需要你确认」（去重 · 每个问题一次）· **不退出** · 用户回复 `--resume` 后继续守 |
| core 进程死 + 状态非终态非 asking | 自动 `dispatch.py --resume`（detached）· 连续失败超 `--max-resume`（默认 5）才通知需人工介入并退出 2 |
| `cancel.txt` 出现 | SIGTERM 停 core · 退出 0 |
| `running`（进行中） | 每轮写一行**阶段感知心跳安抚**到 `watch.log`（见下）· 不通知（避免打扰） |

**阶段感知心跳 + 行数 ETA（进行中的安抚 · 回答"能不能展示预计时间"）**：

> **为什么是"先验行数粗估"而非"实时进度条"**：knot core 把整表一次性交给远端 ·
> 结果全堆在最后的 sentinel JSON 里一次性吐回 · **运行中拿不到"已完成 X/N 行"**；
> 且拆批是远端内部做的 · 批次数对客户端是黑盒。所以 ETA 只能开跑时按**行数**先验
> 估算（不靠实时完成度）· 运行中补**粗粒度阶段感知**做安抚。**零改远端、零改 knot
> core** —— 全靠看门狗读现成的 `state.json`（`client_row_ids` 长度=行数 ·
> `session_started_at`=起点）+ `heartbeat.txt`（`tool_calls` / `sse_bytes_this_step`
> 增量=阶段信号）。

看门狗每 30s 在 `watch.log` 追加一行形如：

```
… | 阶段=查询定价中 · 33行 · 已跑3m20s · 预计总时长 6m36s~14m51s(典型9m54s) · 约还需 4m35s~12m50s · 正在查询各产品价格（已发起 8 次询价）…
```

**阶段判据**（从 heartbeat 增量识别）：

| 阶段 | 判据 | 安抚文案 |
| --- | --- | --- |
| 启动中 | 还没 heartbeat | 正在启动询价… |
| 查询定价中 | `tool_calls` 比上轮增加 | 正在查询各产品价格（已发起 N 次询价）… |
| 汇总生成结果中 | `tool_calls` 不变但 `sse_bytes_this_step` 增加 | 价格基本查完 · 正在汇总生成结果（通常要几分钟 · 属正常）… |
| 疑似停滞 | 两者都不动 + `silence` ≥ 180s | 远端暂时安静 · 看门狗仍在守候… |

> **ETA 系数是单点 seed**（`ETA_COEF_*`：12/18/27 s/行 · 标定自"33 行≈10min"这一次
> 干净 run）· 精度有限。看门狗命中终态时会把**实际耗时 vs 估算**写进 `WATCH_DONE.txt` ·
> 供后续累积精化系数。展示成**区间**而非单值 · 就是为了不给假精确。

**与 agent 的分层（回答"通知能不能用 agent 回复"）**：

- **可靠层 = 看门狗**（保证）：30s 进度 + 系统通知 · 纯读文件 · 与 agent 无关 · 你离开 / 换会话都照跑。
- **便利层 = agent 回复**（锦上添花）：看门狗把状态写成 `WATCH_STATUS.txt` / `WATCH_DONE.txt` ·
  你回到会话时 agent 读这些文件用聊天回复；也可挂一个小时级 IDE automation 让 agent 定时读状态并回复。
  但**不要**把保证押在 agent 上 —— 真正每 30s 的稳定播报只有守护进程能做。

**与步骤 3「前台 supervisor」的关系（§一.7 冲突暴露 · 不并用）**：

- knot core 现由 dispatch **自动挂看门狗** · 看门狗是**唯一 supervisor**（进度 + 通知 + resume）。
- 因此走 knot 时 · 步骤 3 里"agent 每 60–120s 手动观察 / 手动 resume"的契约**作废** ——
  agent **不要**再 `sleep + cat state.json` 轮询、**不要**自己 `--resume`（resume 归看门狗独占 ·
  dispatch 的 D.9 auto-resume 在看门狗激活时已让位）。agent 只需最后读 `summary.xlsx` /
  `WATCH_DONE.txt` 给用户。
- core 被信号杀死时 · dispatch 前台会 exit 11 并提示"已交看门狗接管" —— 这**不是失败** ·
  任务在后台由看门狗续跑 · agent 应 watch `WATCH_DONE.txt` 而非当场判定失败或重跑。
- parallel core 不挂看门狗 · 仍按步骤 3 的前台观察契约走。

## 可选 core 切换（运维 / 维护者向）

本 wrapper 默认走 `inquiry-price-knot` core（JSON-over-SSE · 整表一次交给远端 knot agent ·
不本地拆批 / 不本地并发 · 但支持多轮 asking → resume · 最多 20 轮）。
也可以通过环境变量切到其它 core：

```bash
export INQUIRY_PRICE_CORE=knot       # 默认 · 显式声明
export INQUIRY_PRICE_CORE=parallel   # 本地拆批 + 并发 · 行为已稳定 · 支持 pending.json 异步追问
```

切换由开发者拍板 · 每次切换跟随 plugin 版本号发版（不通过 LLM 运行时决策）。

> ⚠️ LLM 不要在响应里主动建议用户改 `INQUIRY_PRICE_CORE`——core 切换是运维决策 · 不是用户决策。
> 用户问"为什么这次询价变慢/变快了" 也不要解释 core 切换细节 · 只回答询价结果本身。

## 完成态展示规则

完全沿用 parallel 现有规则：读 summary.md → 列 download_links → 不本地解析价格汇总。

## ✋ 回应前自检清单（核心 7 条）

- [ ] 是否走的 wrapper 而非直接 use_skill 任何 core？
- [ ] step 2 是否把异构输入转成了 source_table.md（含合并单元格展开）？
- [ ] step 3 dispatcher 退出码是否正确处理（0/10/1/3 四态）？
- [ ] step 5 仅在 pending.json 存在时执行 · 不假设 core 一定支持？
- [ ] step 5 的 asking 问题是否**全部交用户拍板**（可附建议但不自答 · 优先 `ask_followup_question`）？
- [ ] 完成态是否只读 core 产物 · 不自己解析价格做汇总？
- [ ] core 切换需求 → 是否回答用户"改 env + 发新版" 而非临时改本 SKILL.md？

## 加新 core 怎么办？

参 `references/adding-new-core.md`。简言之：新建 `inquiry-price-<id>/` skill 目录 + 实现
`scripts/run.py`（产 summary.xlsx 9 列）+ dispatch.py 加一个 elif 分支 + plugin version bump。
**wrapper SKILL.md 无需修改**（除非新 core 引入用户感知的新能力）。
