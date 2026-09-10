# WorkBuddy Inspiration Audit

Date: 2026-06-29

## Observed Patterns

- Popular cards sell a finished artifact, not an internal capability. Titles usually read as `object + output`, such as `今日 AI 日报一键生成`, `个人投资组合再平衡仪表盘`, `基金组合健康诊断`, `我的自选股盯盘看板`.
- Card copy uses plain benefit language: `一眼看清`, `一份看懂`, `体检`, `路线图`, `盯盘`, `可交互 HTML 看板`.
- Screenshots matter. Top cards show a complete first screen with visible charts, KPI cards, sections, and a clear artifact shape.
- Financial inspirations that feel closer to consumer use are framed around concrete anxieties: `一周涨 25% 还能追吗`, `深套 30% 怎么办`, `朋友推荐靠谱吗`, `手把手教新手分析一只股票`.
- Information/news inspirations are packaged by time window and output: `今日 AI 日报`, `最近 7 天动态追踪`, `最近一周论文盘点`.
- Current official financial examples often still lack strong source click-through inside the artifact, so Tongzhou can stand out by making `源头复核` a first-class visible section.

## Gap In Current Expert Inspirations

- `研报共识与分歧雷达` and `个股批判性分析报告` are accurate but too professional for WorkBuddy inspiration browsing.
- Several prompts lead with internal research process words such as `批判性`, `共识`, `分歧`, `证据台账`; these should move below the fold or into prompt internals.
- The strongest existing entry is `大白话投研解释卡`; it already matches the target audience and should become the tone anchor.
- Source traceability is present, but the artifact should make clickable source buttons visible near the top, not only in later tables.

## Recommended Rewrite Direction

- Rename user-facing inspiration titles:
  - `个股批判性分析报告` -> `手把手看懂一只股票`
  - `行业/板块异动归因仪表盘` -> `今天这个板块为什么涨`
  - `研报共识与分歧雷达` -> `券商最近都在说什么`
  - keep `大白话投研解释卡`, or promote it as `小白也能看懂的投研解释卡`
- Add one news-style inspiration:
  - `今日 A 股发生了什么`
  - Output: HTML daily card with 3 top events, affected industries, plain-language translation, and source links including Tongzhou mini-program links when returned by MCP.
- Each artifact first screen should include:
  - one-sentence plain conclusion
  - 3-4 evidence cards with source tags
  - `查看源头` buttons
  - a small `不是投资建议` risk note
  - mobile-friendly layout
- Prompt style should ask for C-end wording first, then evidence rigor:
  - `先讲人话，再放证据`
  - `每个事实必须带来源标签`
  - `有 URL 就做可点击链接；没有 URL 就明确写未返回可跳转源头`

## Candidate Inspiration Set

1. `今日 A 股发生了什么` - daily news/dashboard entry using same-boat news/report links.
2. `手把手看懂一只股票` - stock health card for one listed company.
3. `今天这个板块为什么涨` - industry/event impact explanation.
4. `券商最近都在说什么` - research digest rewritten for ordinary users.
5. `朋友推荐的股票靠谱吗` - evidence check / red-team style, framed as source review rather than investment advice.

