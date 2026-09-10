# Result Taxonomy

Map the technical fields (`status`, `callStatus`, `hasIntent`, `resultTags`) returned by the query API into a single business-result label, then give one recommended next action. Never present a raw phone number or raw personal data.

## Derivation rules

Evaluate in this order:

| business_result | condition | candidate-facing meaning |
|---|---|---|
| in_progress | `status = IN_PROGRESS` | 沟通中，尚未完成 |
| cancelled | `status = CANCELLED` | 任务已取消 |
| interested | `status = COMPLETED` and `callStatus = COMPLETED` and `hasIntent = 有意向` | 已接通，候选人有意向 |
| not_interested | `status = COMPLETED` and `callStatus = COMPLETED` and `hasIntent = 无意向` | 已接通，候选人无意向 |
| unreachable | `status = COMPLETED` and `callStatus = UNREACHABLE` | 未接通（关机/无人接/拒接等） |
| failed | `status = COMPLETED` and `callStatus = ERROR` | 系统异常，外呼失败 |
| ignored | `status = COMPLETED` and `callStatus = IGNORED_RESUME` | 简历被忽略，未实际沟通 |
| need_human | result tags or candidate statements indicate salary/offer/complaint/privacy/dispute, or intent cannot be classified | 需人工跟进 |
| unknown | none of the above can be determined | 状态未知 |

When `callStatus = COMPLETED`, also read `resultTags` for structured detail (e.g. callback requests, specific concerns) and include a brief summary, but do not over-interpret.

## Recommended next actions

| business_result | next action |
|---|---|
| in_progress | tell the user it is still running; offer to query again shortly. Do not initiate a new call. |
| interested | suggest recruiter follow-up / advancing screening or interview; offer to surface candidate basics (no phone). |
| not_interested | suggest recording the reason and stopping automatic calls for this post. |
| unreachable | suggest a retry only if ≥30 min has passed since the last call and fewer than 3 retries have been used; otherwise suggest a scheduled callback. |
| failed | suggest retrying later; do not loop automatically. |
| ignored | explain the resume was skipped; suggest checking resume state/eligibility. |
| cancelled | confirm cancellation; ask if the user wants to re-initiate (subject to frequency gates). |
| need_human | route to a human recruiter; do not initiate another call. |
| unknown | ask for the task id or narrow the query (candidate name + time range); do not initiate another call. |

## Response style

State the business result plainly, give one concrete next step, and stop. Example: "这次外呼已完成，候选人对该岗位有意向。建议你推进到下一步筛选或安排面试，需要我帮你看候选人基本信息吗？" Do not claim outcomes that the data does not support, and never promise interview results or offers.
