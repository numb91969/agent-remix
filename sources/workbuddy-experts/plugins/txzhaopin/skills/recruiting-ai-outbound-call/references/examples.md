# Examples

Few-shot examples for the enabled scenario. Decisions show the four routing dimensions and the resulting action.

## Example 1: create call (happy path)

User: 帮我外呼候选人张三，确认他对后台开发岗位还有没有兴趣。

Decision:
- recruit_type = social
- target_role = candidate
- call_goal = job_intention
- action_type = create_call
- scenario_code = SOCIAL_JOB_INTENTION (enabled)

Action: confirm `employeeId` and `recruitPostId` from context. If both known, run safety gates (window 09:00-21:00, same-candidate+same-post 180-day check), then call `recruit.admin-test.post_api_ai_call_submit` with `contactItems=["JOB_INTENT"]`. On success, report `aiCallTaskId` and 沟通中, and note the result can be queried later.

## Example 2: missing slot

User: 帮我给这个候选人打个电话问下岗位意向。

Decision: action_type = create_call, scenario_code = SOCIAL_JOB_INTENTION, but `recruitPostId` (and maybe `employeeId`) unknown.

Action: ask one concise question — which post, and which candidate (by name/resume), so we can resolve `employeeId` and `recruitPostId`. Do not fabricate ids. Do not ask for a phone number.

## Example 3: query result

User: 查下刚刚那个岗位意向外呼结果。

Decision: action_type = query_result, scenario_code = SOCIAL_JOB_INTENTION.

Action: call `recruit.admin-test.post_api_ai_call_my_list` filtered by recent context (candidate `key` + today's `timeStart`/`timeEnd`, or `status`). Locate the record by `aiCallTaskId`, map `status`/`callStatus`/`hasIntent` to a business result, and give a concise summary + next action.

## Example 4: unsafe immediate retry

User: 他没接，马上再打一次。

Decision: action_type = create_call (retry).

Action: do not call immediately. Check the unreachable-retry rule (≥30 min interval, ≤3 retries). If too soon, explain the retry is blocked and offer to schedule a callback within 09:00-21:00.

## Example 5: out-of-window request

User: 现在晚上 11 点，帮我外呼候选人确认岗位意向。

Decision: action_type = create_call, but current time is outside 09:00-21:00.

Action: do not submit an immediate call. Offer to schedule a `startTime` within 09:00-21:00 (within 7 days).

## Example 6: same post within 180 days

User: 再给这个候选人按这个岗位打一次岗位意向。

Decision: same candidate + same post.

Action: warn that same candidate + same post is limited to once per 180 days and will be blocked (`DUPLICATE_SAME_POST`); do not submit. If the user means a different post, confirm the new post id first.

## Example 7: other-post soft block

Server returns `success=false`, `errorCode=DUPLICATE_OTHER_POST`, `allowForceSubmit=true`.

Action: explain that this candidate already had an AI call for another post recently. Ask whether to proceed anyway. Only if the user explicitly confirms, retry with `forceSubmit=true`.

## Example 8: unsupported scenario

User: 帮我外呼这个校招候选人提醒他来参加笔试。

Decision: recruit_type = campus, call_goal = exam_reminder, scenario_code = CAMPUS_EXAM_REMINDER (planned, not enabled).

Action: explain that AI outbound calling for campus exam reminders is not yet enabled; offer to create a manual follow-up reminder instead. Do not call any create API.

## Example 9: prohibited content / escalation

User: 外呼候选人，告诉他我们一定给他发 offer，薪资按他要求来。

Decision: prohibited promises (offer certainty, salary).

Action: decline to make such promises in an AI call. Offer a neutral job-intention call instead, and route salary/offer discussions to a human recruiter.
