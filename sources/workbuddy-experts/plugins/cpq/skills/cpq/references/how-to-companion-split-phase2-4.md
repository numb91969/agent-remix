# C 段 Phase 2.4 · 伴生拆分（C 段前置阶段）

> **定位**：C 段的最前置阶段，在 Phase 2.5 规范化之前执行。由独立子 agent `cpq-companion-split` 完成（见 [`.agent/agents/cpq-companion-split.md`](../../../../.agent/agents/cpq-companion-split.md)）。
>
> **迁移背景**：2026-07 从 A 段 Phase 1 B.2 迁移到此位置，详见 [`docs/cpq/companion-split-migration/design.md`](../../../../docs/cpq/companion-split-migration/design.md)。

## 输入契约

| 项   | 内容                                                                                                    |
| ---- | ------------------------------------------------------------------------------------------------------- |
| 必需 | `<CPQ_SESSION_DIR>/phase1.md`（含 `phase1-done` marker · v3 格式）                                      |
| 可选 | `<CPQ_SESSION_DIR>/phase4_1.md`（路径 2：先询价后选品场景，由 D 段回填的四层编码在 phase1.md 中已生效） |
| 参数 | `site`（cn / intl，由 phase1.md 首行 marker 传递）                                                      |

**注意**：phase4_1.md 存在时，其反哺的四层编码 / 四层定义名称 / SPUID 应已由 D 段写回 phase1.md（v3 铁律仍成立：D 不改 phase1，但通过 phase4_1 反哺的字段在 C 消费前会由主 agent 复制到工作副本，具体机制见 [`how-to-query-pricing.md`](./how-to-query-pricing.md) §v3 反哺）。Phase 2.4 只读 phase1.md 的当前状态。

## 准入判据（决策 D3 简化版）

**对每一行**：仅当**同时满足**以下三条时才触发伴生拆分：

1. `四层编码` 列为空（`-` 或空字符串）
2. `四层定义名称` 列为空
3. `SPUID` 列为空

**任一非空** → 跳过拆分（原行原样写入 phase2_4.md，`source_row_id = row_id`）。

**理由**：已有四层码 / SPUID 的行意味着该行已经过 D 段询价或用户显式指定，服务端 bundle 已识别 / 用户已精准定位，客户端不再需要拆分。

## 拆分规则

完全复用 [`how-to-identify-companion-products.md`](./how-to-identify-companion-products.md) 中的字典 + 规则，**不修改语义**。核心动作：

```
对每个通过准入判据的主产品行 R:
  1. 加载 data/phase1-token-dict/companion-trigger.md（按 site 过滤）
  2. 扫描 R.规格/子类型 + R.约束条件 中的所有 token
  3. 命中【强制清单】触发词 → 拆出独立行 R':
     - R'.row_id = <R.row_id>.<N>（N 从 1 起递增）
     - R'.source_row_id = R.row_id
     - R'.产品名 = 字典 "拆出的腾讯云产品名" 列
     - R'.规格/子类型 = 类型 + 容量（如 "SSD 系统盘 40GB"）
     - R'.站点 / 地域 / 售卖模式 / 优惠策略 / 来源判断 = 继承 R
     - R'.status = stable
     - R'.SPUID / 四层编码 / 四层定义名称 = 空（后续由 Phase 2.5+ 或 D 反哺填充）
  4. 命中【可选清单】触发词 → 拆出独立行 + 在 推断标记 列写 companion_inferred=yes
  5. 主产品行 R 移除已拆出的 token（搜索关键词重新构造 · 见 how-to-identify-companion-products.md）
  6. 累计 companion_expanded 计数
```

## 输出契约：phase2_4.md

**列结构**（v3 phase1 列 + 1 列 `source_row_id`）：

```
| # | row_id | status | 产品名 | 规格/子类型 | 搜索关键词 | 站点 | 地域 | 来源判断 | 售卖模式 | 优惠策略 | 返佣（%） | 约束条件 | 推断标记 | SPUID | 四层编码 | 四层定义名称 | source_row_id |
```

**首行 marker**：

```
<!-- site: cn|intl version=3 -->
```

**末行 marker**：

```
<!-- phase2_4-done:
  total=<N> source_rows=<M> companion_expanded=<C>
  skipped_by_four_layer=<S> step_split_executed=<yes|no>
  site=<cn|intl>
-->
```

字段语义：

- `total` = phase2_4.md 中所有活跃行数（不含 status=removed）
- `source_rows` = 输入 phase1.md 的活跃行数
- `companion_expanded` = 拆出的新伴生行数
- `skipped_by_four_layer` = 因准入判据未通过跳过拆分的行数
- `step_split_executed` = `yes` 当且仅当 `companion_expanded > 0`；否则 `no`
- `site` 从 phase1.md 继承

**恒等式**：`total = source_rows + companion_expanded`

## 输出示例

输入 `phase1.md`：

```
| # | row_id | status | 产品名 | 规格/子类型 | 搜索关键词 | ... | SPUID | 四层编码 | 四层定义名称 |
|---|--------|--------|--------|------------|-----------|-----|-------|----------|--------------|
| 1 | r001 | stable | CVM | 标准型 S5 / 4核8G / 系统盘 SSD 40G / 5Mbps | 云服务器 CVM 标准型 S5 4核8G | ... | - | - | - |
```

输出 `phase2_4.md`（假设该行三判据均空 → 触发拆分）：

```
| # | row_id | status | 产品名 | 规格/子类型 | 搜索关键词 | ... | SPUID | 四层编码 | 四层定义名称 | source_row_id |
|---|--------|--------|--------|------------|-----------|-----|-------|----------|--------------|---------------|
| 1 | r001 | stable | CVM | 标准型 S5 / 4核8G | 云服务器 CVM 标准型 S5 4核8G | ... | - | - | - | r001 |
| 2 | r001.1 | stable | 云硬盘 CBS | SSD 系统盘 40GB | 云硬盘 CBS SSD 系统盘 | ... | - | - | - | r001 |
| 3 | r001.2 | stable | 弹性公网 IP | 5Mbps 按量 | 弹性公网 IP 5Mbps | ... | - | - | - | r001 |
```

Marker：

```
<!-- phase2_4-done: total=3 source_rows=1 companion_expanded=2 skipped_by_four_layer=0 step_split_executed=yes site=cn -->
```

## 机器门控

产物必须通过 `scripts/check-phase2-4.mjs`（见 [gate 脚本](../scripts/check-phase2-4.mjs)）：

```bash
node scripts/check-phase2-4.mjs --session-dir <CPQ_SESSION_DIR>
```

- exit 0 = 通过
- exit 2 = 校验失败（stderr 输出具体 finding）

## 与 v3 铁律的关系

- `phase1.md` 是 A 段唯一权威产物，Phase 2.4 只读不写
- phase2_4.md 是独立文件，不回写 phase1.md
- `phase2_4.row_id ⊇ phase1.row_id`（只增不删）
- 每个 phase2_4 中的伴生行都能通过 `source_row_id` 回溯到 phase1 主行

## 下游消费方

C 段 Phase 2.5 起的所有阶段（规范化 / 意图识别 / 搜索匹配 / Phase 4 确认 / Phase 5 row add）**只读 `phase2_4.md`**，不再回读 phase1.md 的产品行数据（只允许读 phase1 的元数据如 site）。
