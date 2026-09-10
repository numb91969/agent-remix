# 定时任务上下文推荐协议

> 本文件是 `agents/recruitment-expert.md` §9.1「定时化推荐」的完整协议（agent 只保留三条底线，细则在此）。
> **按需 Read**：仅当某个 skill 刚执行完、且命中下表推荐时机时才需读取本文件。
> 主 agent 不再内联此协议全文。


> **背景**：用户跑完高频能力（待办查询 / 流程跟踪 / 漏斗 / 保温等）后，**90% 的概率明天还会再跑一次**——这时候主动推一句"要不要自动跑"，是把"我想自动化"埋到用户脑子里的最佳时机。
> **本节目的**：在能力 flow 的输出末尾**追加一段标准化推荐**，命中条件时引导用户一句话开启对应预置定时模板；不命中条件时**绝不刷屏**。

### A · 适用清单（哪些能力跑完后推荐 + 推荐什么）

| 触发能力 | 推荐模板 ID | 推荐文案 |
|---|---|---|
| `interview-assistant · T` 待办查询 | `daily-interview-todo` | 工作日 9:00 自动给你过一遍今日面试 + 待填面评 + 推荐待办 |
| `recruitment-process-tracker` 流程跟踪 | `weekly-process-pipeline` | 每周一 9:00 自动给你「本周聚焦清单」+ 偏慢预警 |
| `warming-recruit-manager` 场景 C 三级播报 | `daily-recruit-warming-brief` | 工作日 9:00 自动跑保温播报 + 今日 3 件事 |
| `hr-data-router` 跑完招聘漏斗查询 | `monthly-recruit-funnel-report` | 每月 1 号 9:00 自动整理上月漏斗 + 渠道效果 + 同环比 |
| `recruit-data-dashboard` 跑完社招看板查询 | `monthly-recruit-funnel-report` | 每月 1 号 9:00 自动整理上月社招漏斗 + 转化率 + 同环比 |
| `hr-data-router` 跑完合同到期查询 | `monthly-contract-expiry` | 每月 1 号 9:00 自动发未来 N 月合同到期清单 |
| `zhaopin-operations` / `zhaopin-social-operations` 跑完简历搜推 | `daily-resume-search` | 工作日 9:00 按本次画像每天自动搜简历，**跨天去重只推近 30 天新增**（⚠️ 推荐时必须附隐私前置确认，见下） |

🔴 **简历搜推定时化的特殊门槛（推荐前必须做）**：`daily-resume-search` 已用「跨天去重只推新增 + 强制 webhook + 标题日期戳」解决了旧版顾虑（天天推重复、隐私敞口），因此**可以**在用户跑完搜简历后推荐。但推荐文案**必须**额外带一句隐私确认：「⚠️ 该任务每天会把对口候选人推到群里，请确认群成员都有查看权限」。用户没明确认可前，不替他建任务。

❌ **仍不推荐定时化**的能力：D 面评 / E 单场复盘 / C 出题 / **mapping 人才寻访**（事件驱动 / 一次性动作 / 外部公开信息研究，不宜每日跑）。
> 💡 mapping 虽**不主动推荐定时化**，但若用户**主动**说"每天帮我跑一遍某赛道 mapping"，仍按 agent §3.1「调度意图」正常建任务，不拦。

### B · 不打扰硬规则（必须**全部满足**才推）

```
推荐前自检：
  ① 当前 flow 是本文件 §A 适用清单内的能力吗？          ❌ 否 → 不推
  ② 本会话之前已经为同一能力推过 1 次吗？         ✅ 推过 → 不推
  ③ 【判重·关键词匹配】调 automation_update mode=list 拉全部任务，
     用下面 §B-1 的关键词表判断"是否已有同类任务"？      ✅ 已有 → 不推
  ④ 用户偏好文件已设置 disable_recommend=true？   ✅ 已禁 → 不推
  ⑤ 用户上轮明确拒绝过（"不用"/"不要"/"算了"）？  ✅ 拒过 → 不推

全部 ❌ → 推荐（按 C 输出）
```

#### B-1 · 判重关键词表（🔴 核心 · 解决"已配过还重复推"）

> **背景**：用户名下定时任务大多 `expert_id` 为空、`skills_json=[]`，**不能靠 expert_id / skills_json / 模板ID 判重**。
> 唯一可靠信号是任务 `name`（和必要时 `prompt`）里的业务关键词。判重时把 list 返回的每条任务 name 跟下表比对：

| 当前能力 / 推荐模板 | 命中即视为"已有同类任务"的 name 关键词（任一） |
|---|---|
| 待办查询 → `daily-interview-todo` | 待办、面试待办、今日面试、面试播报、招聘早班、招聘班次 |
| 流程跟踪 → `weekly-process-pipeline` | 流程、流程跟踪、流程周报、process-pipeline、pipeline、聚焦清单 |
| 保温播报 → `daily-recruit-warming-brief` | 保温、待入职、签约后、warming、欢迎话术 |
| 招聘漏斗 → `monthly-recruit-funnel-report` | 漏斗、转化率、招聘漏斗、funnel、渠道效果、招聘月报 |
| 合同到期 → `monthly-contract-expiry` | 合同到期、合同、续签、contract-expiry |
| 简历搜推 → `daily-resume-search` | 简历搜推、每日简历、搜简历、简历推送、找简历、resume-search、找校招、找社招 |

**判重执行要点**：
1. 关键词匹配**忽略大小写、忽略中英文混排**；name 含任一关键词即判"已有"。
2. **不区分 expert_id / status**：哪怕是 `expert_id` 为空的历史任务、或 PAUSED 状态，只要 name 命中关键词就算"已配过"→ 不重复推荐（避免打扰）。
3. list 调用失败 / 拿不到任务时：**保守不推**（宁可漏推一次，不可误扰）。

> ⚠️ **session 状态记录方式**：在 agent 内部维护一个内存 `recommended_in_session: Set[capability_id]`，每次推荐后写入；新会话清空。
> ⚠️ **用户偏好持久化路径**：`~/.workbuddy/skills/daily-routine-builder/user-prefs.json`（schema 见 daily-routine-builder/SKILL.md §六）

### C · 标准化推荐输出（统一模板 · 不要自由发挥）

业务能力的正常输出**完整给完**之后，**追加**这段：

```markdown
─────────────────────
⏰ **想每天/每周自动跑这个吗？**

  · 推荐模板：`<模板ID>`（<频率>）
  · 一键开启：直接说「<示例触发语>」即可
  · 想自定义频率/时间？说「我要自定义」
  · 不需要：说「不用了」（本会话不再问）
```

每个适用能力的具体填充见上 §A 表格。**示例触发语必须是大白话**，比如"设个面试待办定时" / "开启每周流程周报"。

### D · 老用户 / 已有任务用户的精简版

如果用户名下已经存在 ≥1 个定时任务（automation_update view 列表非空）但没匹配模板任务 → 用**单行小灰字**版本：

```markdown
> ⏰ 提示：可设为定时任务（推荐 `<模板ID>`，<频率>）—— 说「设个 XX 定时」即可。
```

不另起 5 行段落。

### E · 用户回复处理

| 用户回复 | 处理 |
|---|---|
| "开" / "好" / "1" / "一键" / "示例触发语" | 进 `daily-routine-builder` 直接走 §三 模板入口（携带模板 ID） |
| "自定义" / "2" / "改个时间" | 进 `daily-routine-builder` 走 §四 七问 SOP |
| "不用" / "不要" / "算了" / "3" | 当前会话**记入** disabled_in_session；如用户说"以后别问 X" → 写入 user-prefs.json 的 disable_recommend_for_capabilities 黑名单；如用户说"以后别再推荐定时任务"/"全局禁推" → 写入 user-prefs.json 的 disable_recommend_global=true |
| "为什么推荐这个" | 简单解释 1 句（如"因为你刚才查了今日面试，每天早上看一次很高频"），再问要不要 |

### F · 跟「调度意图」路由的关系

- **调度意图路由**（agent §3.1）是用户**主动**说定时相关诉求时的横切识别（用户 push agent）
- **定时化推荐**（agent §9.1 + 本文件）是 agent 在用户跑完高频能力后**主动**建议（agent push 用户）
- 两者**不冲突**：前者在**入口阶段**最先识别意图（用户主动提调度时先识别、确认后分流）；后者在**输出阶段**做"末尾贴片"（业务结果给完后才追加推荐）。一前一后，互不抢占。

---
