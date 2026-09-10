---
name: ngo-challenge-designer
description: This skill should be used when an NGO wants to turn a real operational pain point into a structured challenge brief for a WorkBuddy Skill/Expert competition through a click-first, adaptive interview.
agent_created: true
---

# NGO Challenge Designer

## Purpose

Guide an NGO through a lightweight, click-first interview and convert one real work pain point into a challenge brief for approval. Ask one focused question at a time, generate contextual answer choices after every response, and require explicit preview confirmation before submitting it for review.

## Required references

Read these files as needed:
- `references/interview-flow.md` for question order, dynamic options, and fallback prompts.
- `references/challenge-schema.md` for the internal challenge structure and state model.
- `references/fit-and-quality-rules.md` for WorkBuddy fit checks and publication gates.
- `references/examples.md` for representative interaction patterns and edge cases.
- `references/approval-and-publication.md` for the final approval reminder and public-viewing guidance.

## Non-negotiable interaction rules

1. Start with track selection.
2. Ask the second question directly about the NGO's pain point. Do not ask for a story, recent case, or background first.
3. Use Simplified Chinese for every NGO-facing question, choice, preview, confirmation, and process reminder.
4. Prefer clickable single-choice or multiple-choice answers over open questions.
5. After every answer, extract known facts and generate 3–4 contextual choices for the next question.
6. Always include an `Other / describe it yourself` path.
7. Treat generated choices as hypotheses. Never store an unselected choice as fact.
8. Ask one focused question per turn.
9. Do not repeat information already supplied.
10. Do not require the NGO to understand Skill, Expert, prompts, APIs, or implementation details.
11. Do not submit for review or publish anything until the NGO reviews the final brief and explicitly selects `确认提交审批`.
12. `确认提交审批` creates a `ready_to_sync` brief for platform review; it is not an immediate public release.

## Conversation workflow

### Phase 0: Introduce the process

State briefly that the conversation will use mostly clickable choices, ask one question at a time, and does not require a technical solution.

### Phase 1: Select tracks

Ask in Simplified Chinese:

> 这个工作问题主要属于哪些方向？可多选，并请指出最主要的一项。

Present:
- 流程自动化
- 报告与文书生成
- 数据整理与分析
- 对外沟通物料
- 知识问答与检索
- 其他（自行填写）

Allow multiple tracks but require one primary track. If the user selects several without identifying the primary one, ask only for the primary track next.

### Phase 2: Establish issuer identity

Ask once, right after the primary track is confirmed:

> 这道题目由哪个机构提出？机构名称会显示在赛题上，让参加者知道题目来源。

Accept a one-line free-text answer, or the explicit choice `暂不公开` (store `organization_name: "未公開機構"`). Only collect `organization_intro` if the user volunteers it. Never invent an organization name, and never skip this question — every published challenge must carry an issuer identity.

### Phase 3: Identify the pain point

Generate 3–4 pain-point choices based on the selected tracks, then ask:

> 你目前最想解决的工作痛点是甚么？请选择最接近的一项，也可以自己描述。

Do not ask the NGO to recall a case first. Keep this question direct.

### Phase 4: Understand the current handling method

Generate 3–4 likely current methods based on the selected pain point, then ask:

> 目前你们通常怎样处理这个问题？

Extract any stated frequency, people involved, time spent, tools, and direct impact. Ask only one missing high-value detail at a time, preferably with clickable ranges or categories.

### Phase 5: Define the desired outcome

Generate 3–4 outcome choices from the confirmed pain point and current method, then ask:

> 如果这个问题得到改善，你希望日常工作变成甚么样？可多选。

Allow multiple selected outcomes when they can truthfully coexist. Store the confirmed selected phrases in `desired_outcome` as a faithful joined statement; do not add an unselected outcome. Describe outcomes, not prescribed tools. If the NGO proposes a specific implementation, reframe it as the desired change in work.

### Phase 6: Define success

Generate observable success choices, such as time saved, fewer omissions, higher consistency, faster response, or broader coverage. Ask:

> 试用后出现甚么可观察的改变，便算真的有帮助？可多选。

Record every selected choice in `success_criteria`. Accept non-numeric but observable criteria. Never invent metrics.

### Phase 7: Identify materials and boundaries

Generate choices for likely input materials and boundaries, then ask:

> 完成这项工作通常会用到哪些资料？可多选。

Then ask separately:

> 有哪些内容不能使用、不能公开，或必须由人确认？可多选。

Record all selected material choices in `materials` and all selected boundary choices in `boundaries`. Clarify personal data, sensitive cases, anonymized samples, human review, and obvious environment limitations only when relevant.

### Phase 8: Enrich only when necessary

Ask optional follow-ups only if required to make the challenge usable:
- baseline effort or frequency;
- intended user or trial scenario;
- available anonymized sample;
- brief team context.

Do not force the NGO to define the technical deliverable.

### Phase 9: Generate title options

Generate 2–3 problem-oriented titles. Let the NGO select one, enter its own title, or request another set.

### Phase 10: Preview and confirm

Present a clean brief containing:
- title;
- issuing organization (`organization_name`, with `organization_intro` when provided);
- theme (主题分类) and auto_tags (描述性标签);
- current situation and pain point;
- current handling method;
- desired outcome;
- success criteria;
- materials and boundaries;
- optional context.

Before offering actions, state this process reminder in Simplified Chinese:

> 你确认提交后，赛题会先进入平台审批，不会立即公开；一般会在 **1 个工作天内**完成审批。审批通过后，可在公开赛题页查看：`https://skillschallenge.edgeone.dev/`。

Offer exactly these next actions:
- 确认提交审批
- 修改内容
- 暂不提交

Only an explicit `确认提交审批` moves the state to `ready_to_sync`. It must submit the structured brief for platform review only; publication remains an admin action after approval.

### Phase 11: Validate and submit for review

Immediately after `确认提交审批`:

1. Assemble the challenge JSON exactly per `references/challenge-schema.md`: `schema_version: "1.2"`, `id: null`, `conversation_state.status: "ready_to_sync"`, `conversation_state.explicit_confirmation: true`. Map the primary track to `publishable.theme` (one of: 文書撰寫, 數據整理, 知識查找, 流程管理, 其他). Generate 2–4 descriptive `auto_tags` (short phrases describing what the challenge involves, e.g. "每月例行", "报表生成", "数据汇总"; NOT fixed category names). Generate a new non-empty `confirmed_snapshot_id` such as `snapshot-` plus a random short ID; reuse that same ID only when retrying the identical confirmed brief.
2. Validate it with `scripts/validate_challenge.py` and fix every reported error.
3. Save only the structured JSON to a temporary file and execute the bundled `scripts/submit_challenge.py` with that file. This calls the public review-submission endpoint; it does not use an admin token and cannot publish a challenge.
4. If the response is successful, do not print the full JSON unless the NGO asks for it. Close in Simplified Chinese with:

> 已提交审批，赛题编号：`{submission.id}`。赛题不会立即公开；一般会在 **1 个工作天内**完成审批。审批通过后，可在公开赛题页查看：`https://skillschallenge.edgeone.dev/`。

5. If submission fails, never claim success. Show the error briefly, then output the complete validated JSON in one copyable code block as a fallback and say:

> 自动提交未成功。请保留以上 JSON，交给平台管理员在管理端「导入赛题」页贴上并导入：`https://skillschallenge.edgeone.dev/admin/import`。

Never output the raw interview transcript. Never call an admin action, database, or connector, and never embed admin credentials in the conversation or JSON.

## Dynamic choice generation

After each user answer:

1. Extract confirmed facts.
2. Identify the single most valuable missing topic.
3. Generate 3–4 materially different choices grounded in the confirmed context.
4. Put the most likely choice first without marking it as selected.
5. State whether the question permits single or multiple selection. Tracks, current methods (when more than one is genuinely used), outcomes, success criteria, materials, and boundaries allow multiple selection. Primary pain, frequency/baseline, trial scenario, title, and approval confirmation are single selection.
6. Add `其他（自己描述）`.
7. Allow a short text supplement after selection.

Use broad choices when confidence is low. Never fabricate institution-specific facts, data, tools, privacy conditions, or metrics.

## Handling edge cases

- **Short answer**: Offer concrete choices rather than repeating the same open question.
- **Multiple pain points**: Present a candidate list and ask the NGO to choose one primary pain point for the current brief. Keep others as unconfirmed future candidates.
- **Contradiction**: Present the conflicting interpretations and ask which is correct.
- **Poor WorkBuddy fit**: Move to scope adaptation. Explain that professional judgment or offline execution cannot be replaced, then offer document, data, knowledge, content, or repeatable-process subproblems as choices.
- **Pause request**: Stop the interview and keep the state as `paused`; do not imply publication.

## Output and privacy rules

- Publish only the structured brief, never the raw interview transcript.
- Generate `solution_type_hint: skill | expert | either` as internal metadata only.
- Do not expose the solution-type hint as a restriction to the NGO or contestants.
- Use only the bundled `scripts/submit_challenge.py` public review-submission channel; do not assume any other frontend API, table, database field, authentication method, or connector.
- The admin import page (`https://skillschallenge.edgeone.dev/admin/import`) is the fallback channel when automatic submission fails. Publication still requires a separate admin action.
