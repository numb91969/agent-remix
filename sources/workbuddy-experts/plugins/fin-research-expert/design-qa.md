# Design QA: Industry Viewpoint MCP App

## Reference

- Same Boat H5 timeline: `https://same-boat-test.textmind-gz.com/#/pages/industryPerspective/industryPerspectiveTimeLine?sector=1026009`
- Same Boat H5 detail: `https://same-boat-test.textmind-gz.com/#/pages/industryPerspective/industryPerspectiveDetails?id=7484774133331398658`
- Product intent: reuse the H5 information hierarchy and visual language without copying its account shell, bottom navigation, or full-page feed.

## Reviewed States

- Desktop viewpoint timeline with sentiment distribution and filters.
- Desktop viewpoint detail with interpretation, calibrated radar, and source tabs.
- Narrow layout at 375 CSS pixels with no horizontal overflow.
- Dark host theme through the standalone preview theme hook.
- Empty, unavailable, busy, and uncalibrated-radar fallback states in source review.

## Findings

- P0: none.
- P1: none.
- P2: none.
- P3: the official WorkBuddy host still needs acceptance testing after it advertises and renders the third-party `ui://` capability.

## Result

The App uses a compact timeline instead of a generic dashboard, keeps mainland-market red/green semantics, exposes one primary task view, and preserves deterministic source and follow-up actions. Radar geometry is rendered only when the service provides an explicit scale; otherwise the UI shows raw dimensions without implying calibration.

Final result: passed
