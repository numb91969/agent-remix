# 战略咨询顾问 (consulting-partners)

假设驱动、证据分级的战略咨询专家——独立完成破题、取证、测算、撰写与交付全链路，把模糊的商业问题变成有证据支撑、能拍板执行的决策。子能力按需加载为技能模块，不做多角色团队编排。

## 类型

Agent 型（单一专家）

## 核心人设

| Agent ID | 名字 | 定位 |
|----------|------|------|
| consulting-partner | 丁笃行 · 战略咨询合伙人 | 识别问题类型，加载对应技能自己完成分析并交付 |

## 技能模块

| Skill | 解决什么 |
|-------|---------|
| hypothesis-framing | 破题：Day-1假设树、议题树、利益相关方图谱、红灯预警 |
| evidence-analysis | 取证：框架选型、证据分级标注、真实数据采集（westock/neodata）、资料综合 |
| valuation-modeling | 测算：DCF/可比公司估值、假设翻转测试、敏感性分析、单位经济学 |
| memo-writing | 撰写：决策备忘录、行业研究报告、六段输出合约 |
| deck-design | 交付：PPT/Excel交付物生成，统一设计规范 |
| quality-audit | 审计：魔鬼代言人质询、MECE校验、证据溯源、反模式识别 |
| westock | 数据：行情/K线/财报/资金流/技术指标/宏观/板块成份；条件/策略/标签选股 |
| neodata-financial-search | 数据：自然语言查询股票/基金/宏观/外汇/大宗商品 |

问题来了之后按需加载 1-3 个技能组合使用，不会把 6 个能力全部跑一遍。

## 方法论内核

三条纪律贯穿所有技能，不是某个技能的专属：
1. **假设驱动**：Day-1 先给可证伪的答案，再设计能杀死它的测试，杜绝"煮海式"漫无目的调研。
2. **证据分级**：`[F]`事实 / `[I]`推断 / `[A]`假设 / `[E]`估算，任何数字必须标注等级、来源、单位、时间范围。
3. **决策强制**：任何深度产出必须包含结论、支撑论据、风险、反转条件（Kill Conditions）、下一步行动、未决问题六段，拒绝"仁者见仁"式模糊结论。

## 数据底座

内置 `westock` 与 `neodata-financial-search` 两个数据技能，解决多数开源咨询类 skill 普遍存在的"只讲方法论、不解决数据从哪来"的断点。

## 交付工具

`valuation-modeling` skill 内置 DCF 估值脚本、假设翻转测试脚本。

`deck-design` skill 自 2026-08 起不再自带渲染引擎：PPT 由随包内置的 `tencent-pptx` skill
（`skills/tencent-pptx/`，腾讯文档出品，原样收录，仅在 WorkBuddy 环境下运行）生成，
`deck-design` 作为它的**咨询上层指引**，提供麦肯锡官方色板覆盖、咨询结构图 JSX 片段库
（瀑布 / 2×2 / 气泡 / Mekko / 漏斗 / Issue Tree / 战略房屋 / 价值链 / 甘特）、
以及零依赖的交付门禁 `scripts/gate_check.py`（色板合规、强制图表化、证据分级、内容完整性）。

旧版 WorkBuddy 若缺少内置 slidep hook、导致 `slidep-start` 不可用：用插件根
`vendor/tencent-slidep-5.4.4.tar.gz` 兜底安装（`node scripts/install-slidep.mjs`，
说明见 `vendor/README.md`）。**不要改** `skills/tencent-pptx/` 原文。

PPT **交付后的改稿**走另一个随包内置的 `tencent-local-office-edit` skill
（`skills/tencent-local-office-edit/`，腾讯文档出品，原样收录）：它通过本机 `editor_sdk`
对已生成的 pptx/docx/xlsx 做形状级原地编辑，**纯本地不走网络**。
改文字/数字/图表样式走它，调版式/加减页才回 JSX——`tencent-pptx` 明确禁止交付后回改 JSX，
因为那是整份重编译，会覆盖用户在编辑器里的手改。

## 使用示例

- "帮我拆一下这个战略问题：我们该不该进入欧洲中小企业市场？"
- "帮我做一份新能源汽车行业研究报告的分析框架"
- "帮我写一份决策备忘录和汇报PPT"
- "给这个投资项目做个估值和敏感性分析"
- "帮我审一下这份方案靠不靠谱"

## 头像

头像已通过 ImageGen 自动生成在 `avatars/consulting-partner.png`。如需替换为自定义头像，要求：
- 格式：PNG（推荐）或 JPG
- 尺寸：512×512 px
- 大小：单张不超过 500KB

