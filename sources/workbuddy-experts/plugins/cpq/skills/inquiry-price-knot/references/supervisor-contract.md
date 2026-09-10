# LLM Agent 行为契约（前台 supervisor 视角 · 必读）

> 本文件是 [`SKILL.md`](../SKILL.md) 「LLM Agent 行为契约」段的完整版。
> 对调用 `run_knot.py` 的上层 Agent（CodeBuddy / Claude / Cursor 等 LLM）强制生效。

> **历史教训**：曾出现 Agent 在 run_knot.py 仅跑 ~6 分钟（没收到新事件）就主动 `TaskStop` / `kill`
> 的事故 · 把"远端 LLM 编译慢"误判为"卡死" · 把还在合法 L1b 心跳窗口内的进程提前杀掉。

## 一、禁止越权 kill

启动 `run_knot.py`（首跑 / `--resume` / dispatch.py 间接拉起）之后 · 在以下三种事件**之一**
发生前 · **禁止**主动 `TaskStop` / `kill` / 关 shell / 中断进程：

1. 进程**自然 exit**（return code 0 / 10 / 1）
2. **用户明确**要求中止（用户原话出现"停掉 / 别等了 / 杀掉 / abort / cancel"等明确意图）
3. wall-clock 已经**超过 60 分钟**仍未自然退出（极端兜底 · 正常远端单轮最多十几分钟）

> **"卡住没输出"不是 kill 理由**——心跳静默 / max-turns / 单次 HTTP 都由 `run_knot.py` /
> `call_knot_agent.py` 自己兜底（详见 SKILL.md「心跳 / 超时三层防御」段）· **LLM 不要替代它**。

## 二、只允许观察 · 不允许干预

进程运行期间 · LLM 仅可做以下**只读**动作：

| 频率 | 动作 | 说明 |
|---|---|---|
| 每 60–120s 一次 | `cat <run-dir>/state.json` | 看 `rounds_taken` / `last_turn_status` / `last_turn_at` / `gate_retry_count` 是否在推进 |
| 每 60–120s 一次 | `cat <run-dir>/heartbeat.txt` | 看远端最近 SSE 事件时间戳（B.4 落地后才有） |
| 任意 | `cat <run-dir>/summary.xlsx` 头几行 | 看 status 列是否已转 final / asking / failed |
| 任意 | `tail -n 50 <run-dir>/progress.log` | 看本地心跳和 SSE 进度行 |
| 任意 | `ls -lt <run-dir>/raw_responses/ \| head -5` | 只看最新 `round_NNN.json` mtime · 若明显新于 `summary.xlsx` mtime · 说明远端已交答复但被 gate 拒 · 是"heartbeat 在跳但任务其实在原地打转"的独立信号（见 §三 触发 c）|

❌ **禁止**：`kill -9 <pid>` / `pkill -f run_knot` / `TaskStop` / 关 shell / 改 state.json /
**读 `raw_responses/round_NNN.json` 内容自己 parse 出 summary**（只允许 `ls` 看
mtime · 不允许 `cat` 内容做自主兜底 · 兜底路径由 run_knot.py 的 rescue 分支负责）。

## 三、主动进度报告

以下任一触发条件命中 · **必须**主动给用户一行进度同步（不必等用户来问）：

- **(a) 时间静默**：**两次连续观察**之间 `state.json` 的 `rounds_taken` / `last_turn_at`
  都没动 · 或 `heartbeat.txt` 时间戳超过 120s 没刷新
- **(b) L1b 重连**：`state.json` 的 `retry_count > 0` 或 `last_silence_seconds_max`
  接近 180（B.6 落地后）· 说明远端已经触发过 L1b 静默重连
- **(c) Gate 已在原地打转**（**heartbeat 仍在跳也算命中** · 独立于 (a)）：
  同时满足以下两条 —
    1. `state.gate_retry_count >= 1`（远端至少交过一轮被 gate 拒的答复）
    2. `ls -lt <run-dir>/raw_responses/` 显示最新 `round_NNN.json` mtime
       明显新于 `summary.xlsx` mtime（差 > 60s）
  这是"任务本身进入循环 · 不是编译慢"的信号 · 与 §一"禁止越权 kill"不冲突 ·
  仍**不 kill**（run_knot.py rescue 分支会兜底）· 只做一次进度同步

同步内容包含：

- 已运行 wall-clock 时长（分钟）
- 当前 round / max_turns
- 最近一条 progress.log 的尾巴（如 `[knot-agent] [380s] 智能体正在思考...`）
- `state.json` 的 `retry_count` / `last_silence_seconds_max`（B.6 落地后）
  + `gate_retry_count` · 让用户知道远端是否在 L1b 静默重连 · 或 gate 是否已在拉锯
- 一句话兜底说明 · 按触发条件分：
    - 触发 (a) / (b) 时：「远端 agent 在编译 LLM · 不是卡死 · 按契约继续等到自然退出 / 60 min 兜底」
    - 触发 (c) 时：「远端已交答复但客户端 schema gate 拒了 · 正在等 rescue 分支自动兜底
      （`gate_retry_count` 达到 `MAX_GATE_RETRIES_V1B=2` 后自动降级写 summary） · 通常几十秒内出结果」

形式上：**只用普通文本输出**（一行 / 简短段落即可）· **不要**调 `ask_followup_question` ·
**不要**让用户做选择题。这是单向进度同步 · 不是征求决策。

❌ **禁止**：默默等 · 直到用户主动来问"完成了吗"才回报。
❌ **禁止**：把进度同步包装成"我要不要继续等？"的问题——按契约**必须**继续等 · 不问。

> 例外：若 wall-clock 已超 60 min · 才允许 ask_followup_question 让用户选「再等 / 切兜底 / 放弃」

## 四、自然退出后的下一步

| run_knot.py exit code | LLM 该做什么 |
|---|---|
| 0 | 读 `summary.xlsx` 给用户展示结果（含 status=failed 的兜底行也照展） |
| 10 | 走 wrapper SKILL.md 步骤 5（处理 pending.json · 收用户回复 → `--resume`） |
| 1 | 看 stderr 找 fatal 原因 · 如实告诉用户 · 不擅自重跑 |
| 11 | （B.4 + D.9 落地后）进程异常消失 · 看 state.json 最后状态 · 与用户商量重试还是切兜底 |

## 五、与 cpq 主流程错误恢复表的关系

cpq `SKILL.md §错误恢复` 里的"CLI 命令超时或网络错误 → 重试一次"是**通用 CLI** 规则 ·
**不**适用于 `dispatch.py` / `run_knot.py` 这条链路。本节为该链路的**专用契约**。
冲突时 · **本节优先**（§一.7 冲突暴露而非求平均原则）。
