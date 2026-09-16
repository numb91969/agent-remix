# Tool Contracts

The recruiting outbound-call capability is exposed through the recruiting MCP. Per MCP protocol, confirm an API with SearchAPI (discovery then detail) before calling it with CallAPI.

> 🔴 **apiId prefix is `recruit.admin-test.` (verified 2026-07-08), NOT `recruit.social-resume.`**. Both AI-call APIs live in the recruiting MCP group "招活 / 管理员专用分组". Calling the wrong `social-resume.*` prefix returns `AUTH_PERMISSION_DENIED / 能力不存在或已被禁用`. Always confirm via SearchAPI before CallAPI.

## Create call

- api id: `recruit.admin-test.post_api_ai_call_submit`
- name: AI 沟通下单 (POST /api/ai-call/submit)
- purpose: HR initiates a one-click AI outbound call to a candidate. Server pipeline: gray check, input validation, checks (org / resume state / post / blacklist / high-level / dedup), scheduled-time validation, JD rewrite, place order with outbound system, persist.

Request params:

| param | type | required | notes |
|---|---|---|---|
| `employeeId` | integer | yes | candidate resume id = extId (not rid). From resume detail `resume.extId` or resume search. |
| `recruitPostId` | integer | yes | post id. From post lookup `recruitPostID` or `/postdetails/{id}`. |
| `contactItems` | string[] | yes | must include `JOB_INTENT`; optional `JOB_STATUS`, `INTERVIEW_TIME`. |
| `forceSubmit` | boolean | no | default false. Set true only to override the other-post soft block after user confirmation. |
| `startTime` | string | no | GMT+8 `yyyy-MM-dd HH:mm:ss`. null = call now. Must be inside call window and ≤ 7 days out. |

Success response: `success=true`, `data.aiCallTaskId="ai_call_xxxx"`, `data.status="沟通中"`.

Failure response: `success=false`, `data.errorCode`, `data.message`, `data.allowForceSubmit`.

### errorCode handling

| errorCode | meaning | agent response |
|---|---|---|
| AI_CALL_NOT_IN_GRAY | not in gray allowlist | feature not yet open for this user/org |
| INVALID_CONTACT_ITEMS | missing job intention | ensure `contactItems` includes `JOB_INTENT` |
| AI_CALL_ORG_RESTRICTED | org not supported | this org cannot place AI calls |
| IN_PROGRESS_LIMIT_REACHED | too many in-progress tasks | wait for current calls to finish, then retry |
| AI_CALL_RESUME_NOT_FOUND | resume not found | confirm the candidate id (message includes the id) |
| AI_CALL_RESUME_EMPLOYED | resume already employed | candidate is employed; cannot call |
| AI_CALL_RESUME_BLOCKED | resume under evaluation | resume is under evaluation; cannot call now |
| AI_CALL_POST_NOT_FOUND | post not found | confirm the post id (message includes the id) |
| AI_CALL_POST_SECRET | confidential post | secret post; cannot call |
| AI_CALL_HRCORE_BLACK | candidate in core-HR restricted list | candidate is restricted |
| AI_CALL_HIGH_LEVEL_BLOCKED | candidate level too high | candidate's historical interview level is high |
| DUPLICATE_SAME_POST | same post called within ~3 months (hard block) | someone already called this candidate for this post; cannot repeat |
| DUPLICATE_OTHER_POST | other post called recently (soft block) | if `allowForceSubmit=true`, explain and ask the user; retry with `forceSubmit=true` only on confirmation |
| NO_CANDIDATE_PHONE | candidate has no phone | cannot call; suggest checking contact info (do not display the number) |
| AI_CALL_START_TIME_EXPIRED | scheduled time already passed | choose a future time |
| AI_CALL_START_TIME_OUT_OF_RANGE | scheduled time > 7 days | choose a time within 7 days |
| AI_CALL_START_TIME_NOT_IN_SLOT | time not in call window | choose a time within 09:00-21:00 |
| AI_CALL_JD_REWRITE_FAILED | JD processing failed | retry later |
| AI_CALL_EXTERNAL_DUPLICATE | platform 180-day dedup block | platform dedup limit reached |
| AI_CALL_SUBMIT_FAILED | system busy | retry later |

Note: the server documents same-post hard block as "近3月" and a platform "180天" dedup. The product policy for v1 is to treat same candidate + same post as at most 1 per 180 days; the server's combined dedup enforces this. Always defer to the actual `errorCode` returned.

## Query results

- api id: `recruit.admin-test.post_api_ai_call_my_list`
- name: AI 沟通记录列表查询 (POST /api/ai-call/my-list)
- purpose: query the current HR's AI outbound-call records, with filters and pagination.

Request params (all optional): `key` (name/phone fuzzy, ES), `status` (`IN_PROGRESS`/`COMPLETED`/`CANCELLED`), `hasIntent` (`有意向`/`无意向`, only when COMPLETED), `lastCrop`, `lastPosition`, `locked` (1/0), `updateTimeStart`/`updateTimeEnd` (`yyyy-MM-dd HH:mm:ss`, ES), `timeStart`/`timeEnd` (`yyyy-MM-dd`, DB create_time), `todayPush` (bool), `pageNo` (default 1), `pageSize` (default 20).

Response: `CommonList<AiCallListItem>` with `num` (total) and `list`. Each item:

| field | meaning |
|---|---|
| `employeeId` | candidate resume id |
| `aiCallTaskId` | task id, e.g. `ai_call_xxxx` |
| `staffId` / `staffName` | who placed the order |
| `recruitPostId` / `recruitPostName` | post |
| `candidateName` | candidate name |
| `status` | `IN_PROGRESS` 沟通中 / `COMPLETED` 已完成 / `CANCELLED` 已取消 |
| `callStatus` | `COMPLETED` / `UNREACHABLE` / `ERROR` / `IGNORED_RESUME` (valid only when COMPLETED) |
| `statusText` | 沟通中 / 已完成 / 已取消 |
| `hasIntent` | 有意向 / 无意向 / null (only when COMPLETED) |
| `createTime` | order time `yyyy-MM-dd HH:mm:ss` |
| `callTime` | actual call time (empty if not dialed yet) |
| `resultTags` | Map<String,String> structured tags (only when COMPLETED) |
| `resumeData` | resume ES detail |

To find a specific recent call, prefer filtering by `key` (candidate name) plus `timeStart`/`timeEnd`, or by `status`/`hasIntent`. There is no single-task-by-id query in v1; locate the record in the list by `aiCallTaskId`.

## Standard-field mapping

To keep agent logic stable as more scenarios are added, map real fields to standard names:

| standard | source |
|---|---|
| call_task_id | `aiCallTaskId` |
| scenario_code | fixed `SOCIAL_JOB_INTENTION` for these APIs |
| task_status | `status` |
| call_status | `callStatus` |
| has_intent | `hasIntent` |
| created_at | `createTime` |
| called_at | `callTime` |
| result_tags | `resultTags` |

Business-result derivation from these fields is defined in `result_taxonomy.md`.

## Live-test notes (2026-07-08, first real run)

First real end-to-end attempt on a social candidate (rid `51b70b76-...`, job "招聘信息化系统产品经理"). Findings:

1. **apiId prefix corrected**: create/query APIs are under `recruit.admin-test.*`, NOT `recruit.social-resume.*` (the old value returned `AUTH_PERMISSION_DENIED / 能力不存在或已被禁用`). Fixed across SKILL.md + this file + examples.md.
2. **Resolving `employeeId` (extId) from an rid**: use `recruit.social-resume.get_api_resume_detail_getresume_with_detail` with **both** `rid` AND `fromPlace="MCP"` (fromPlace is required; missing it → `VALIDATION_FAILED`). The resume detail returns `extId` (= employeeId) and, under `flowList`, the candidate's associated posts as `postId` + `postName` — use these to let the user pick the target `recruitPostId` (do not guess when there are several).
3. **Gray release**: submit returned `success=false, errorCode=AI_CALL_NOT_IN_GRAY, msg="功能暂未开放"` — the current user/org is **not yet in the gray allowlist**, so no call is actually placed. This is the expected fail-safe; surface "功能暂未开放" to the user and stop. The full create pipeline (params accepted, gray gate reached) is otherwise confirmed working; re-test the happy path once the account is grayed in.
4. **`contactItems` type — CONFIRMED array**: pass `["JOB_INTENT"]` (JSON array). Verified working end-to-end on 2026-07-09 (below). The schema doc's bare-string example is just illustrative; the array form is accepted.

## Live-test notes (2026-07-09, happy path CONFIRMED after gray release)

Account was grayed in; re-ran the same candidate (employeeId=<员工ID>, recruitPostId=<岗位ID>) with `contactItems:["JOB_INTENT"]`, immediate call (no startTime), inside the 09:00–21:00 window.

- **create** `recruit.admin-test.post_api_ai_call_submit` → `code:1, success:true, data.aiCallTaskId="ai_call_00fa3392...", data.status="沟通中"` (6.7s). Call actually placed. ✅ Full create path confirmed.
- **query** `recruit.admin-test.post_api_ai_call_my_list` with `{timeStart:"2026-07-09", timeEnd:"2026-07-09", pageNo:1, pageSize:20}` → located the task; right after submit it showed `status=沟通中, callStatus=null, hasIntent=null, callTime=null` (call not yet finished). ✅ Query path confirmed.
- ⚠️ **my_list response is large** — pipe to a file / parse fully; do NOT `head -c` truncate (breaks JSON). `data.data.list[]` holds the records, `data.data.num` is the total.
- Reminder: while `status=沟通中`, never claim the candidate answered or has intent. Re-query after the call finishes to read `callStatus` / `hasIntent`, then map via `result_taxonomy.md`.
- **Completed result confirmed (~6 min later)**: same task re-queried returned `status=COMPLETED, callStatus=COMPLETED, hasIntent=有意向, callTime=2026-07-09 19:50:21, resultTags={"has_intent":"有意向","is_employed":"在职"}`. Maps to business_result **interested** → suggest advancing to screening / interview. `resultTags` is a real dict (here: intent + employment status) — surface it briefly but don't over-interpret. **Full lifecycle create→沟通中→COMPLETED(有意向) is now end-to-end verified.**
