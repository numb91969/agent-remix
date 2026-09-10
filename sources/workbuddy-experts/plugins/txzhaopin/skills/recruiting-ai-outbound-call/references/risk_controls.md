# Risk Controls

Time windows and frequency control are configured per scenario. Version 1 ships concrete values only for `SOCIAL_JOB_INTENTION`. The agent applies these as pre-call expectations; the recruiting MCP server is the source of truth and enforces them, returning an `errorCode` when a gate fails (see `tool_contracts.md`). The agent must never help a user bypass any gate.

## Per-scenario config (SOCIAL_JOB_INTENTION)

| Item | Rule |
|---|---|
| Call window | Every day 09:00-21:00 (GMT+8). No holiday/weekday distinction. |
| Scheduled time (`startTime`) | Must fall inside 09:00-21:00 and be no more than 7 days in the future. |
| Same candidate + same post | At most 1 call per 180 days (hard limit). |
| Same candidate + different post | No hard limit in v1; triggers a soft block requiring explicit user confirmation (`forceSubmit=true`). To be made configurable later. |
| Unreachable retry | Allowed only after a 30-minute interval; at most 3 retries. |
| In-progress concurrency | Bounded server-side; a too-many-in-progress rejection means wait for current calls to finish. |

These values are intentionally isolated per scenario so future scenarios (urge, interview confirm, campus reminders) can define their own windows and limits without changing agent logic. When a new scenario is enabled, add its own block here.

## Universal hard gates (all scenarios)

Before any `create_call`, the following must hold; all are enforced server-side and surfaced as `errorCode`:

- Permission: the user must be allowed to operate this candidate/post.
- Candidate state: not employed, not under evaluation/blocked, not high-level-blocked.
- Opt-out / blacklist: candidate not in the core-HR restricted list; has a valid phone.
- Post state: not a secret/confidential post.
- Gray release: the user/org must be in the gray allowlist; otherwise the feature is not yet open.
- Time window and dedup as above.

## Agent-side pre-call behavior

- If the user asks for an immediate call outside 09:00-21:00, do not submit an immediate call. Offer to schedule a `startTime` within the window.
- If the user asks to call again right after an unreachable result, check the 30-minute interval and the 3-retry cap. If too soon or exhausted, decline and explain; suggest a later callback or a scheduled time.
- If the user asks to re-call the same candidate for the same post within 180 days, warn that it will be blocked and do not submit unless the user is clearly addressing a different post.
- Never request, display, or confirm a raw phone number. Pass only `employeeId` and `recruitPostId`.
- Never set `forceSubmit=true` proactively. Only after the server returns `DUPLICATE_OTHER_POST` with `allowForceSubmit=true` and the user explicitly confirms overriding.

## Prohibited content during/around the call

- Do not promise an offer, salary, level, headcount guarantee, interview pass probability, or any hiring outcome.
- Do not collect or discuss sensitive personal matters (marriage/childbearing, age-based screening, health/privacy).
- For complaints, disputes, privacy concerns, salary/offer questions, or any ambiguous high-risk request, escalate to a human recruiter.

## Defense in depth

Frequency control exists at four layers: this skill (pre-call prompting and explanation), MCP server (hard validation and dedup, including 180-day platform dedup), the outbound platform (rate limiting), and the operations backend (configurable thresholds and kill switch). The skill layer reduces obviously-bad calls and explains rejections; it is not the enforcement boundary.
