# Industry Fund Flow Reference

Use for:
- 最新一个可用交易日的申万一级行业主力资金净流入/净流出榜
- 单个或少量申万一级行业的日频资金流趋势
- 1、5、20 个交易日累计资金流比较

Also read `references/limitations.md`.

## rank_industry_fund_flows

- Use directly when the user asks broad questions such as “板块资金流”“一级行业净流入排名”.
- Default scope is `taxonomy="sw"` and `industry_level="industry01"`. State this default in the answer.
- `direction`: `all` | `inflow` | `outflow`.
- `rank_window`: `1` | `5` | `20`; all three windows are returned in `window_metrics`.
- `trade_date` is an as-of boundary. Always report the returned `trade_date`; it may be earlier than the calendar date.
- Read `coverage` before interpreting ranks. If it is partial, show missing industries and do not call the list complete.
- Keep the original sign. Positive main net inflow is not interchangeable with price gains, and negative flow must not be converted to an absolute value.

## get_industry_fund_flow_series

- Use after a standard SW level-1 code is known, or reuse codes returned by `rank_industry_fund_flows`.
- `industry_codes` accepts 1-10 codes, such as `["801080.SL", "801730.SL"]`.
- Use one batch call for comparisons. Do not call once per industry.
- 最近 N 个交易日 -> set `limit=N`; calendar periods -> provide explicit `start_date`/`end_date`.
- Inspect each series `quality`, `missing_dates`, and the top-level `unresolved_codes`.
- Points are ascending by trading date and are chart-ready. Do not silently fill missing flow values with zero.

## Cross-MCP Identity Routing

- Exact standard SW level-1 codes can go directly to Fin Data.
- Free text, lycode, themes, concepts, or names that may cross taxonomies must first use Fin Graph `resolve_research_identity`.
- Pass only the returned SW market/industry code into the series tool. Do not substitute a same-named concept, industry-chain node, or basket id.
- Fin Graph provides identity, graph, crowding, viewpoints, and anomalies. Fin Data remains the numerical source for the fund-flow ranking and series.

## Interpretation Rules

- “主力净流入” follows the licensed data supplier's statistical definition. Do not call it institutional, northbound, or account-level net buying.
- Current coverage is daily review data, not intraday realtime flow.
- Do not derive minute fund flow or order-size buckets from minute prices, volume, turnover, or K lines.
- For charts in Chinese securities contexts, use red for positive/inflow and green for negative/outflow; keep a visible zero line.
