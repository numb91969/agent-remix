# Routing Matrix

Classify every outbound-call request along four dimensions, then map to a `scenario_code` and check `launch_status`. Only initiate calls when `launch_status = enabled`.

## Dimensions

- `recruit_type`: `social` (社招) / `campus` (校招) / `intern` (实习) / `unknown`
- `target_role`: `candidate` (候选人) / `interviewer` (面试官) / `recruiter` (HR) / `unknown` — v1 only `candidate`
- `call_goal`: `job_intention` (岗位意向) / `interview_confirm` (面试邀约确认) / `urge` (催办) / `material_collect` (材料补充) / `exam_reminder` (笔试提醒) / `offer_followup` (Offer 跟进) / `onboarding_followup` (入职前跟进)
- `action_type`: `create_call` (发起) / `query_result` (查结果) / `cancel_or_stop` (停止) / `explain_result` (解释结果)

## Launch status legend

- `enabled`: agent may initiate via MCP.
- `planned`: agent may recognize and route, but must not initiate; tell the user it is not yet available.
- `restricted`: high-sensitivity; never initiate automatically; always route to a human recruiter.

## Scenario table

| scenario_code | recruit_type | call_goal | target_role | launch_status |
|---|---|---|---|---|
| SOCIAL_JOB_INTENTION | social | job_intention | candidate | enabled |
| SOCIAL_INTERVIEW_CONFIRM | social | interview_confirm | candidate | planned |
| SOCIAL_CANDIDATE_URGE | social | urge | candidate | planned |
| SOCIAL_MATERIAL_COLLECT | social | material_collect | candidate | planned |
| SOCIAL_OFFER_FOLLOWUP | social | offer_followup | candidate | restricted |
| SOCIAL_ONBOARDING_FOLLOWUP | social | onboarding_followup | candidate | restricted |
| CAMPUS_JOB_INTENTION | campus | job_intention | candidate | planned |
| CAMPUS_EXAM_REMINDER | campus | exam_reminder | candidate | planned |
| CAMPUS_INTERVIEW_REMINDER | campus | interview_confirm | candidate | planned |
| CAMPUS_MATERIAL_COLLECT | campus | material_collect | candidate | planned |
| CAMPUS_OFFER_FOLLOWUP | campus | offer_followup | candidate | restricted |
| INTERN_GENERIC | intern | (any) | candidate | planned |

> 🔴 **Only `SOCIAL_JOB_INTENTION` is `enabled`. Everything else — including campus job-intention — is `planned`/`restricted`: recognize and explain, never initiate.** In particular, "AI-call a **campus** candidate about job intention" maps to `CAMPUS_JOB_INTENTION` (planned) — do NOT reuse the social create API for a campus candidate.

## Routing rules

If `action_type` is `query_result` or `explain_result`, routing is allowed for any social job-intention record regardless of create permissions, because querying does not initiate a call.

If `action_type = create_call` and the matched `scenario_code` is not `enabled`, respond that the outbound-call capability for that scenario is not yet enabled, and offer to create a manual follow-up reminder or to handle the job-intention scenario instead if applicable.

**Fail-closed default (no matching row):** if the four dimensions do not map to ANY row in the table, treat it as NOT enabled — do not initiate. Never fall back to the social create API just because it is the only enabled one. Example: a campus candidate + job_intention maps to `CAMPUS_JOB_INTENTION` (planned) → explain campus outbound is not yet open, offer a manual follow-up; **do NOT** call `post_api_ai_call_submit` (that API is social-only and would either fail or mis-target).

If `recruit_type` or `call_goal` cannot be determined, ask one concise clarifying question rather than guessing.

The matrix is designed to grow: new scenarios are added by inserting a row and flipping `launch_status` to `enabled` once the corresponding MCP capability and its risk config (see `risk_controls.md`) are ready. No agent-logic change should be required beyond this table and per-scenario config.
