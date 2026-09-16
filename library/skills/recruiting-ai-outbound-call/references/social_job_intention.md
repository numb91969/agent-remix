# Social Recruitment Job-Intention Scenario (SOCIAL_JOB_INTENTION)

The only scenario enabled for initiating calls in version 1.

## Purpose

A recruiter (HR) asks the agent to AI-call a candidate to confirm whether the candidate is interested in a specific social-recruitment post.

## Trigger examples (create_call)

- 帮我外呼候选人确认他对这个岗位还有没有意向
- 问一下候选人还看不看这个社招岗位
- 给这个候选人打个电话确认岗位意向
- 对张三发起一次 AI 岗位意向沟通

## Trigger examples (query_result / explain_result)

- 查一下刚才那个岗位意向外呼的结果
- 这个候选人的 AI 沟通有没有完成
- 外呼接通了吗，候选人有没有意向
- 今天完成的 AI 沟通有哪些有意向的

## Required slots (create_call)

- `employeeId` (integer, required): candidate resume id = extId. Obtain from resume detail (`resume.extId`) or resume search results. Not `rid`.
- `recruitPostId` (integer, required): post id. Obtain from post lookup (`recruitPostID`) or post link `/postdetails/{id}`.
- `contactItems` (string array, required): must include `JOB_INTENT`. Optional additions: `JOB_STATUS` (求职状态), `INTERVIEW_TIME` (面试时间). For v1, default to `["JOB_INTENT"]` unless the user explicitly asks to also confirm job status or interview time.
- `startTime` (string, optional): GMT+8 `yyyy-MM-dd HH:mm:ss`. Omit/null = call immediately. Must be inside the call window (09:00-21:00) and within 7 days.
- `forceSubmit` (boolean, optional): only set true after explicit user confirmation to override the other-post soft block. Never default to true.

If `employeeId` or `recruitPostId` is unknown, resolve from context or ask one concise question. Never invent ids. Never request or echo a phone number.

## Result handling summary

- 有意向 (interested): suggest recruiter follow-up / advancing the screening or interview process.
- 无意向 (not_interested): suggest recording the reason and stopping automatic calls for this post.
- 未接通 (unreachable): suggest a retry only if frequency rules allow (≥30 min interval, ≤3 retries).
- 系统异常/失败 (failed): suggest retry later; do not loop.
- 简历被忽略 (ignored): explain the candidate/resume was skipped; suggest checking resume status.
- 沟通中 (in_progress): tell the user it is still running and offer to query again later.

Full mapping is in `result_taxonomy.md`. Frequency and window rules are in `risk_controls.md`. API contracts are in `tool_contracts.md`.
