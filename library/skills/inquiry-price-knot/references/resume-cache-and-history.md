# resume 缓存探测 + Phase 3 实验 + v1B 命名历史

> 本文件汇总 [`SKILL.md`](../SKILL.md) 里外部化的深入背景：resume 命中 conversation 缓存的
> 探测证据、Phase 3 实验（为什么 P1 暂不落地）、以及 "v1B" 命名的历史脚注。均为**按需**背景资料。

## 🚀 resume 命中 conversation 缓存（P2 · 探测实验证实）

> 数据来源：`~/.workbuddy/knot-probe/20260630-201159-A-baseline/` (首跑) +
> `~/.workbuddy/knot-probe/20260630-201612-B-resume/` (续跑)

进程被 SIGKILL / 网络中断后 · 用同一 `conversation_id` 续跑 · 远端 knot agent
会**命中 conversation 级缓存** · 不重新询价 · 仅 1 次 `task_planning` tool
就拿回完整结果。

### 实测对比（2 行表 · 国际站新加坡）

| 指标 | 首跑 (A) | resume (B · 同 cid) | 倍数 |
|---|---|---|---|
| 耗时 | 86s | **12s** | **7.2× 加速** |
| Tool 调用次数 | 9 | **1** (仅 task_planning) | 9× 减少 |
| Token 峰值 | ~46K | 43K | ≈ flat |
| Conversation ID | `0509e78e...` | **同一个** | ✅ 复用 |

### 实现链路

1. `call_knot_agent.py` 的 `RESUME_AFTER_DISCONNECT_MESSAGE` 自 2026-06-30 起改为
   **结构化协议指令** `[SYSTEM_RESUME_PROTOCOL v1]` · 替代旧版自然语言软求情 ·
   提高远端命中缓存的稳定性
2. `dispatch.py` 在 `_is_signal_kill(rc)` 且 state 非终态时 · **自动触发一次 resume**
   (D.9 升级)；auto-resume 成功（rc ∈ {0, 10} + schema 校验通过）→ 透传该 rc 给
   supervisor · 失败才升 11
3. supervisor (CodeBuddy / Claude) 看到 rc=0 即正常处理结果 · 看到 rc=11 才走兜底
   决策（不再像之前那样 137 → 拆批 · 因为 resume 已被 dispatch 自动尝试过）

### Caveat（必读）

- 远端 conversation 缓存的有效期 / 容量未知 · 探测实验仅覆盖 ~30 秒内的续跑
  生产场景可能命中率不同 · 异常时仍要兜底
- 缓存命中靠远端 LLM 自己识别 `[SYSTEM_RESUME_PROTOCOL v1]` · 远端模型升级 / prompt
  变更可能影响识别率 · 若发现 resume 后 tool 调用数 ≈ 首跑 → 远端缓存失效信号
- **resume 仅在 turn-level 边界生效** · 不解决"单轮内 partial 落盘"问题
  那部分由未来 P1 (client partial commit) 解决 · 当前未落地

### Phase 3 实验 D · 为什么 P1 暂不落地（探测证据）

> 数据来源：`~/.workbuddy/knot-probe/20260630-203408-D-contract/raw_responses/round_001.json`
> 该实验跑了一次完整 `run_knot.py` (带 OUTPUT_CONTRACT_V1B) · 2 行表 · 138s · 13 tools

生产 contract 模式下 · 远端 SSE 文本结构：

```
[0  ─────────────  57.5%  ────  99.1%  ─ 100%]
└── 自然语言思考链 ─┴ sentinel JSON ──┴ 收尾
   "现在开始执行查价        {"schema_version": "v1B",
    流程。先解析地域...       "rows": [...]}
    现在查 CBS 价格..."
```

| 指标 | 数值 |
|---|---|
| raw_text 总长 | 2,859 字符 |
| BEGIN sentinel 位置 | 1,643 字符 / **57.5%** |
| END sentinel 位置 | 2,834 字符 / 99.1% |
| sentinel 内 JSON 体 | 1,191 字符 (41%) |

**P1 (client partial 落盘) 在生产 contract 模式下作用有限**：

- 进程在 sentinel BEGIN 之前死（138s × 57.5% ≈ 79s 之前）→ partial 拿到的全是
  自然语言思考链 · 没有结构化数据可落盘 · partial 等于无效
- 进程在 sentinel BEGIN 之后死（79s 之后）→ partial 能拿到部分 JSON · 但远端
  通常此时已接近完成 · 多救几秒意义不大
- 即使把 sentinel 解析改成 "lenient JSON parser 容忍尾部截断"也只能在最后 ~57s
  窗口内救命 · 投入产出比低

→ 决策：**P1 暂不落地** · 优先靠 P2 (auto-resume) · 等远端协议升级到 v1C (增量
sentinel · 每行一个独立 sentinel) 后 · partial 落盘才有正面 ROI

## 历史脚注 · 为什么会有"v1B"这个名字

代码里仍能看到 `OUTPUT_CONTRACT_V1B` / `_output_contract_v1b.py` / `MAX_GATE_RETRIES_V1B`
这类带 v1B 后缀的符号。这是该协议刚落地时（2026-06-27）与 v1A（远端 final.xlsx
附件下载）并存阶段留下的命名。v1A 在 2026-06-28 完整移除后 · v1B 成为唯一协议 ·
2026-07-03 v1B 又原地升级到 v1B.1（破坏性变更 · 内容全面重写但符号名不变）。名字保留是为了：

- 不再产生大批量纯改名 commit 污染 history
- `docs/cpq/v1b-protocol/{spec,design}.md` 沿用原名 · 与 git log 一一对应
- `schema_version: "v1B"` 字段已是协议约定的一部分 · 客户端 / 远端都按此值校验
  （**v1B → v1B.1 沿用同一 schema_version 值** · 版本区分由 marker + ack 承担 · 见 spec §12）

后续设计协议迭代时 · 可在新版本里换名（如 `OUTPUT_CONTRACT_V2`）· 但当前 v1B
名字本身**不需要**更名 · v1B.1 也沿用。
