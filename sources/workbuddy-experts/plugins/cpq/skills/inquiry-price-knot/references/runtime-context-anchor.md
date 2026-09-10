# 工作目录锚点（runtime context · v1B.2 · 2026-07-09）

> 本文件是 [`SKILL.md`](../SKILL.md) 「工作目录锚点」段的完整版。
> 服务端 SoT：询价仓库 `.claude/skills/inquiry-price-dispatch/steps/merge_output.md §6.6`

**解决的问题**：远端把大表切多 batch 分发 worker 并发跑 · 判活脚本 `scan_completed_batches.py`
需要本次报价的**场景工作目录 `scene_dir`**。会话被 SIGKILL / resume 后远端会丢 `scene_dir`
→ 猜不到扫哪个目录 → 误判"未开始 / 无结果" → 问"要不要重来" → **死循环**
（run_20260708_161728 事故根因）。

**协议**：远端**首轮确认回复**（在 `[ASKING]` 块内）带且仅带一对独占块：

```
[INQUIRY_RUNTIME_CONTEXT_BEGIN]
{"project_root":"...","scene_dir":"tmp/{日期}_{场景}","scene_dir_abs":"..."}
[INQUIRY_RUNTIME_CONTEXT_END]
```

**客户端三件事**（`_output_contract_v1b` 出纯函数 · `run_knot` turn loop 调）：

| 职责 | 落点 | 说明 |
| --- | --- | --- |
| 识别并保存 | `extract_runtime_context` · 每轮从**原始 answer** 抽 → 存 `state.runtime_context` | 覆盖式 · resume 从 state 恢复；解析失败沿用旧值 |
| 从展示剥离 | `strip_runtime_context` · asking_text 写 pending.json 前剥 | 内部信息不给用户；不动其它 marker |
| 每一轮回注 | `build_runtime_context_block` · 发远端前拼在消息尾 | 规则=**state 有锚点就注入**（首轮 fresh 无 → 不注入；之后每轮 + resume 都带） |

**内部重连也带**（步骤3）：`call_knot_agent` 收 `runtime_context_block` 参数 · 单次调用内
SSE 断线重连发的 `RESUME_AFTER_DISCONNECT_MESSAGE` 也拼上锚点 · 避免重连丢目录。

**verdict 驱动的 resume（原 Phase 2）· 经实测论证：不做**（详见
`docs/investigations/PLAN-20260709-verdict-scenarios.md`）：8 次真实 run 表明 · 远端 4 种
verdict（`not_started`/`working`/`started_no_heartbeat`/`all_completed`）在**客户端只表现为
2 类响应**——① 退回确认求决策（覆盖前三种）② 复用/透传（all_completed）· 两类均安全。
verdict 是**服务端自己判活并自主行动**的内部概念 · 客户端观察不到 4 种独立形态 · 故**无需**
在客户端做 verdict 状态机 · 只需回注 scene_dir 锚点（已做）。

**C7 · worker 回退补救（2026-07-09 · 已落地）**：interrupt-resume 后远端可能"失忆"退回
已答过的确认问题（worker 已在远端派发/完成 · 但远端 conversation 回滚到确认阶段 · 实测
Run H）。此时若本 run 已有归档答复（`answers_archive/`）· 客户端**自动重放**已确认答复继续 ·
不打扰用户 · bounded（`KNOT_MAX_AUTO_REPLAY` 默认 2 次 · 超限落回 exit 10 交人工 · fail-loud）。
判据"有归档答复"天然区分「首轮确认」（无归档→交用户）vs「失忆退回」（有归档→重放）。
实测再确认后远端即"直接复用已有结果" · 故安全（无重复派发 · 无数据损失）。
