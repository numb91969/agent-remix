---
name: westock
description: |
  股票数据查询与条件选股工具集。包含两个子工具：
  westock-data：查询已知股票/指数的详细数据（行情、K线、财报、资金流向、技术指标、机构评级、宏观、板块成份、风险事件、ETF 等）
  westock-tool：按条件/策略/标签筛选股票（PE、市值、ROE、涨跌幅、40+ 预置策略、70+ 分类标签等）
  触发词：查行情、看K线、查财报、资金流向、技术指标、选股、筛选、策略选股、帮我找股票、宏观数据、板块成份
---

# WeStock — 股票数据查询与条件选股

本 skill 包含两个子工具，覆盖"查数据"和"选股票"两大场景。

## 分工

| 工具 | 用途 | 真实调用方式 |
|------|------|---------|
| **westock-data** | 查已知股票/指数的详细数据（行情、K线、财报、资金、技术指标、宏观、板块成份等） | `node <skill-path>/scripts/data-index.js <命令> <参数>` |
| **westock-tool** | 按条件/策略/标签从市场里筛选股票 | `node <skill-path>/scripts/tool-index.js <命令> <参数>` |

两个子工具**合并在同一个 skill 包里**，所以入口脚本按前缀区分：`data-index.js` / `tool-index.js`
（各自为单文件打包，无需再加载 vendor）。

**配合流程**：westock-tool 筛选候选池 → westock-data 查详细数据 → 基于数据做分析。

## 快速示例

```bash
WS=<skill-path>/scripts        # 下面所有命令都基于这个路径

node $WS/data-index.js search 腾讯                    # 搜索股票代码
node $WS/data-index.js quote hk00700                  # 查实时行情
node $WS/data-index.js kline sh600519 --period day --limit 60 --fq qfq
node $WS/data-index.js finance sh600519 --num 4       # 查财报
node $WS/data-index.js consensus sh600519             # 卖方一致预期
node $WS/tool-index.js filter "intersect([PE_TTM > 0, PE_TTM < 20, ROETTM > 15])"
node $WS/tool-index.js strategy macd_golden           # 策略选股
node $WS/tool-index.js label shareholder_central_state # 标签选股（央企）
```

## ⚠️ 短命令是简写，不是可执行文件

**本包及下属文档里写的 `westock-data <命令>` / `westock-tool <命令>` 一律是简写**，
等价于 `node <skill-path>/scripts/data-index.js <命令>` / `tool-index.js <命令>`。

**它们没有随包安装到 PATH**——包里没有 `bin/` 目录，照抄短命令会报 command not found。
即便机器上恰好存在同名可执行文件，那也可能是一份与本包无关的旧版独立拷贝
（实测某台机器上的 `westock-tool` 就是这种情况），**结果可能与包内版本不一致，一律走完整路径**。

## 代码格式

| 市场 | 格式 | 示例 |
|------|------|------|
| 沪市 | `sh` + 代码 | `sh600519`（茅台） |
| 深市 | `sz` + 代码 | `sz000001`（平安银行） |
| 港股 | `hk` + 代码 | `hk00700`（腾讯） |
| 美股 | `us` + 代码 | `usAAPL`（苹果） |

## 详细文档

- **westock-data 完整命令手册**：`SKILL-westock-data.md`
- **westock-tool 完整命令手册**：`SKILL-westock-tool.md`
- **westock-data AI 使用指南**：`references/data-ai-guide.md`
- **westock-data 场景指南**：`references/data-scenarios-guide.md`
- **westock-data 宏观字段**：`references/data-macro-fields.md`
- **westock-tool AI 使用指南**：`references/tool-ai-guide.md`
- **westock-tool 字段参考**：`references/tool-fields-guide.md`
- **westock-tool 场景指南**：`references/tool-scenarios-guide.md`

## 环境要求

Node.js >= v18（脚本为单文件打包，无需 npm install）

## 降级策略

如果脚本不可用，使用 WebSearch 搜索相关信息作为替代：
- 行情数据：搜索"XX股票 实时行情""XX股票 PE PB"
- 财务数据：搜索"XX公司 最新财报"
- 资金流向：搜索"XX股票 资金流向"
- 条件选股：搜索"低估值高分红股票""PE低于15的银行股"

联网搜索的数据同样**必须标注来源**，禁止编造。
