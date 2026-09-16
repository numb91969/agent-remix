---
name: recruiting-ai-outbound-call
description: |
  AI 电话外呼候选人 — 让 agent 发起对候选人的 AI 语音外呼、并查询解读外呼结果。能力：① 发起外呼（v1 仅支持**社招岗位意向**场景）② 查询/解读外呼结果（是否接通、有无意向、下一步建议）。
  
  什么时候用我：用户明确说要**打电话 / 外呼 / AI 电话 / AI 语音沟通**候选人，如「帮我外呼这个候选人确认还有没有意向」「给这个社招候选人打个 AI 电话问岗位意向」「查下刚才那个外呼结果」「今天完成的 AI 沟通哪些有意向」。
  
  范围限制（v1）：只有「社招 + 候选人 + 岗位意向」可真正发起；校招提醒、面试确认、催办材料、offer 跟进等其它外呼场景**只识别不发起**，需如实告知未开放并给安全替代（如手动跟进提醒）。
  
  不要用我：① 约面/ 改期 / 取消 / 走系统面试邀约 → interview-assistant ② 在简历库搜候选人 / 推进流程 → zhaopin-operations（校招）或 zhaopin-social-operations（社招）③ 用户只说「联系一下候选人」、没提打电话/外呼 → 先反问确认是要 AI 外呼还是系统邀约。
support_contact: fayellawang
---

# Recruiting AI Outbound Call Skill

## 🚨 FIRST ACTION (on entering this skill · MANDATORY · run silently)

> The first thing to do every time the agent enters this skill via `use_skill("recruiting-ai-outbound-call")` is a silent background `skill_invoked` report. This is the core data that lets the dashboard tell how many times each skill was invoked; without it this skill shows 0 calls on the dashboard.

```bash
bash ../../scripts/track_skill_event.sh "0WEB06ZI7OVDOZQW" "recruiting-ai-outbound-call" "skill_invoked"
```

Additionally, after a `create_call` succeeds (server returns `aiCallTaskId`), fire one more business event (do not block on it):

```bash
bash ../../scripts/track_skill_event.sh "0WEB06ZI7OVDOZQW" "recruiting-ai-outbound-call" "outbound_created" '{"scenario_code":"SOCIAL_JOB_INTENTION"}'
```

Constraints:
1. Run the `skill_invoked` report on every entry — do not skip it because it "just ran".
2. Never put candidate PII (name/phone/id) into the tracking payload; only non-sensitive routing/scenario fields.
3. Reporting must never block the main flow — the script always exits 0; ignore its output.

---

This skill tells the recruiting agent whether, when, and how to call the recruiting MCP AI outbound-call APIs, and how to explain results. The MCP executes the capability; this skill governs intent routing, safety gates, frequency control, and result interpretation.

Current date context: treat the user's local time (GMT+8) as authoritative for time-window checks.

## Scope of version 1

Only the social-recruitment job-intention scenario can actually be initiated:

- `recruit_type = social`
- `target_role = candidate`
- `call_goal = job_intention`
- `scenario_code = SOCIAL_JOB_INTENTION`
- enabled actions: `create_call`, `query_result`, `explain_result`

All other scenarios (campus, intern, urge, interview confirm, material collect, offer/onboarding follow-up, etc.) may be recognized and routed, but MUST NOT be initiated. For those, tell the user the capability is not yet enabled and offer a safe alternative such as a manual follow-up reminder. See `references/routing_matrix.md`.

---

## 🔴 执行硬约束（HARD CONSTRAINTS ·不得违反）

> 这些约束原先写在一级 agent 里，现下沉到本 skill 就近约束——
> 无论 agent 是否复述，进入本 skill 后都必须遵守。

1. **主进程串行执行，禁子代理**：本skill 的「分类 → 取号 → 安全门 → 调 MCP → 解读结果」**必须在主进程内 `use_skill` 后串行跑完**，**严禁** `Task(subagent_name=...)` 起子代理。
2. **绝不越scope 发起**：只有 `SOCIAL_JOB_INTENTION` 可以发起；其它场景一律「只识别不发起」，如实告知未开放并给安全替代（如手动跟进提醒）。**不得**为了"帮到用户"硬调 create API。
3. **敏感信息红线**：
   - 绝不向用户索要或回显候选人**手机号**；只传 `employeeId` + `recruitPostId`，由后端解析拨号。
   - 绝不主动设 `forceSubmit=true`（仅当服务端返回 `DUPLICATE_OTHER_POST` 且用户显式确认后才置真）。
   - 绝不承诺 offer /薪资 / 职级 / 面试结果。
4. **安全门以服务端为准**：呼叫时段（09:00–21:00）、频控（同候选人 + 同岗位 180 天 1 次）、重试（30 分钟间隔、≤3 次）等，skill 侧只做预判和解释，真正拦截在服务端 `errorCode`；**绝不帮用户绕过任何门**。

## 🔴 与相邻 skill 的边界（防抢错）

外呼的动作词（"联系候选人 / 确认 / 催"）与面试安排、搜简历高度相邻：

| 用户想要的 | 该走 | 不是 |
|---|---|---|
| **用 AI 电话去问**候选人（岗位意向） | 本 skill | ❌ 不是 interview-assistant |
| **约面 / 改期 / 取消 / 系统面试邀约** | `interview-assistant` | ❌ 不是外呼 |
| **在简历库搜候选人 / 推进流程** | `zhaopin-*` | ❌ 不是外呼 |
| 只说"联系一下候选人"，没说打电话 / 外呼 | 反问一句确认 | — |

> 判据：**只有出现明确的「打电话 / 外呼 / AI 电话 / AI 沟通」语义时才进本 skill**。单纯"确认 / 邀约 / 催办"默认归 `interview-assistant`，除非用户明说"用 AI 电话 / 外呼"。

## Step 0: decide if this is an outbound-call request

If the user is not asking to initiate a candidate call or to query/explain outbound-call results, do not use this skill; route to other recruiting capabilities.

## Step 0.5: weak-signal confirmation gate (MANDATORY before any create_call)

Chinese trigger words like 「帮我沟通/意向沟通/帮我联系候选人/沟通一下意向」 are **weak signals**: they may mean an AI phone call, but may equally mean a manual contact, a system interview invitation, or just advancing the pipeline. Never assume they mean "place an AI call".

- If the user's wording clearly and explicitly says AI phone call (e.g. 「AI 外呼 / AI 打电话 / AI 电话沟通 / 打个电话问意向」), you may proceed to Step 1 directly.
- If the wording is a weak signal (「帮我沟通 / 意向沟通 / 帮我联系一下候选人 / 沟通一下他还看不看这岗位」), **ask one concise confirming question before doing anything else**, e.g.:
  > "你是想让我发起一次 **AI 电话外呼**（自动打电话跟候选人确认岗位意向）吗？还是只是想我帮你走系统面试邀约 / 其它方式联系？"
  - User confirms AI call → continue to Step 1.
  - User means something else → hand back to the right capability (interview invitation → interview-assistant; just contact info / pipeline → the relevant skill). Do not initiate a call.
- This gate applies to `create_call` only. Pure result queries (「查外呼结果」) are unambiguous and skip this gate.

## Step 1: classify intent

Determine four dimensions before doing anything:

- `recruit_type`: `social` / `campus` / `intern` / `unknown`
- `target_role`: `candidate` / `interviewer` / `recruiter` / `unknown`
- `call_goal`: `job_intention` / `interview_confirm` / `urge` / `material_collect` / `exam_reminder` / `offer_followup` / `onboarding_followup`
- `action_type`: `create_call` / `query_result` / `cancel_or_stop` / `explain_result`

Map to a `scenario_code` using `references/routing_matrix.md`. If the matched scenario is not `enabled`, stop and explain it is not yet available; do not call any create API.

## Step 2: collect minimal slots (create_call only)

For `SOCIAL_JOB_INTENTION` create_call, you must have:

- candidate resume id (`employeeId`, i.e. extId — NOT rid)
- job/post id (`recruitPostId`)
- communication items (`contactItems`), must include `JOB_INTENT`
- optional scheduled time (`startTime`), GMT+8, within the call window and not more than 7 days out

**Resolving `employeeId` and `recruitPostId` from a resume link/rid** (verified 2026-07-08): call `recruit.social-resume.get_api_resume_detail_getresume_with_detail` with `{"rid":"<rid>","fromPlace":"MCP"}` (fromPlace is REQUIRED). The response gives `extId` (= employeeId) and, under `flowList`, the candidate's associated posts as `postId`+`postName`. If the candidate has several posts, **list them and let the user pick the target `recruitPostId` — never guess**.

Rules: never ask the user to provide or confirm a raw phone number; the backend resolves and dials. If `employeeId` or `recruitPostId` is missing, ask a concise clarifying question or resolve it as above. Never fabricate ids. Do not auto-set `forceSubmit=true`; only set it after the user explicitly confirms overriding the other-post soft block.

## Step 3: safety and frequency-control gates

Before calling the create API, check the gates in `references/risk_controls.md`. Key points for `SOCIAL_JOB_INTENTION`:

- Call window: every day 09:00-21:00 (GMT+8), no holiday/weekday distinction. For an immediate call outside this window, do not submit; offer to schedule within the window. For a scheduled `startTime`, it must fall inside 09:00-21:00 and within 7 days.
- Frequency: same candidate + same post is limited to at most 1 call per 180 days. Same candidate + different post has no hard limit in v1 but triggers a soft block that needs explicit user confirmation (`forceSubmit`).
- Unreachable retry: only after a 30-minute interval, at most 3 retries.
- Permission, candidate stage, opt-out/blacklist, secret post, employed/under-evaluation, high-level, and no-phone checks are enforced server-side and surfaced as `errorCode`; reflect them honestly to the user.

The server is the source of truth for these gates. This skill sets expectations so the agent does not initiate calls that will obviously be rejected, and explains rejections clearly. Never instruct or help the user bypass any gate.

## Step 4: call the MCP tool

Use the recruiting MCP. Per MCP protocol, discover/confirm the API via SearchAPI before CallAPI. api ids (🔴 prefix is `recruit.admin-test.`, verified 2026-07-08 — NOT `social-resume.`, which returns `能力不存在或已被禁用`):

- create: `recruit.admin-test.post_api_ai_call_submit`
- query: `recruit.admin-test.post_api_ai_call_my_list`

Full request/response contracts and field mappings are in `references/tool_contracts.md`.

For `create_call`:

1. Summarize the scenario and the candidate/post you are about to call.
2. Run the Step 3 gates.
3. Call the create API with `employeeId`, `recruitPostId`, `contactItems` (include `JOB_INTENT`), and optional `startTime`.
4. On success, report `aiCallTaskId` and status (沟通中), and tell the user they can ask you to query the result later. Do not claim the candidate has been reached or has any intention until a query confirms it.
5. On failure, read `data.errorCode` and explain it using the errorCode table in `references/tool_contracts.md`. If `errorCode = DUPLICATE_OTHER_POST` and `allowForceSubmit = true`, explain the soft block and ask whether to force-submit; only then retry with `forceSubmit=true`.

For `query_result` / `explain_result`:

1. Locate records by recent context, candidate name (`key`), status, intent, or time range via the query API.
2. Map technical fields (`status`, `callStatus`, `hasIntent`, `resultTags`) into a business result label.
3. Give a concise summary and one recommended next action. See `references/result_taxonomy.md`.

## Step 5: result labels and next actions

Map results into: `in_progress`, `interested`, `not_interested`, `unreachable`, `failed`, `ignored`, `cancelled`, `need_human`, `unknown`. For `unreachable`, suggest a retry only if the 30-minute interval and 3-retry cap allow it. For `need_human`, `failed`, or `unknown`, do not auto-initiate another call. Details and phrasing in `references/result_taxonomy.md`.

## Human escalation

Escalate to a human recruiter when the candidate asks about salary, offer certainty, level, headcount, or contract details; expresses complaint, privacy concern, or refusal; gives an answer that cannot be reliably classified; or when the user asks to bypass frequency control, call outside the window, or repeatedly call the candidate.

## Tone and candidate-experience rules

Keep responses factual and operational. Never promise an offer, interview result, compensation, level, headcount, or hiring outcome. Never expose a candidate's raw phone number, email, ID number, or other unnecessary personal data. Prefer "我可以帮你发起一次岗位意向沟通外呼" over "我会直接联系候选人并推进入职".

## References

- `references/routing_matrix.md`: full scenario routing table and launch status.
- `references/social_job_intention.md`: the only enabled scenario, trigger examples, required slots, handling.
- `references/risk_controls.md`: per-scenario time windows, frequency control, and prohibited actions.
- `references/tool_contracts.md`: real MCP api ids, request/response fields, errorCode handling, standard-field mapping.
- `references/result_taxonomy.md`: status-to-business-result mapping and next-action guidance.
- `references/examples.md`: few-shot examples for create, query, and unsafe-repeat cases.
