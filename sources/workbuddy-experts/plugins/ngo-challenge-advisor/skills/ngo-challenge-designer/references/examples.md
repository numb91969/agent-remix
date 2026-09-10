# Interaction examples

## Example A: report generation

1. User selects: 报告与文书生成 + 数据整理与分析; primary = 报告与文书生成.
2. Ask issuing organization. User answers: 社区服务协会. (Or user picks `暂不公开` → store `未公開機構`.)
3. Offer pain choices. User selects: 资料分散，整理和汇总很花时间.
4. Offer current methods. User selects: 在 Excel、Word 或表格之间复制贴上.
5. Offer frequency choices. User selects: 每月 1–3 次.
6. Offer outcome choices. User selects: 统一结构 + 提示缺失资料.
7. Offer success choices. User selects: 完成时间缩短 + 遗漏减少.
8. Ask materials and boundaries with choices.
9. Generate title options, preview (including 出题机构), and wait for explicit confirmation.

## Example B: short answer

User: `报告很麻烦。`

Do not ask `请详细描述`. Offer:
- 资料散落，很难集中
- 每次都要重新整理格式
- 不同同事的内容难以合并
- 容易漏掉必填资料
- 其他（自己描述）

## Example C: several pain points

User mentions volunteer scheduling, donor reports, and policy search.

Respond with a single-choice list asking which one should become the current challenge. Keep the other two as unconfirmed future candidates.

## Example D: poor fit

User wants WorkBuddy to replace social workers' safeguarding decisions.

Explain that final professional judgment cannot be delegated. Offer supporting choices:
- 整理个案资料供社工覆核
- 根据已批准指引列出需注意的项目
- 生成跟进纪录初稿
- 建立人工覆核清单
- 这些都不适合，我想换一个问题

## Example E: confirmation gate

After preview, never infer consent from `看起来可以` or silence. First state, verbatim:

> 你确认提交后，赛题会先进入平台审批，不会立即公开；一般会在 **1 个工作天内**完成审批。审批通过后，可在公开赛题页查看：`https://skillschallenge.edgeone.dev/`。

Then offer exactly:
- 确认提交审批
- 修改内容
- 暂不提交

Only the first selection authorizes `ready_to_sync`; it submits for approval and does not directly publish the challenge.

## Example F: complete final turn after `确认提交审批`

1. Assemble the JSON per `challenge-schema.md` with a non-empty `confirmed_snapshot_id` and validate it with `scripts/validate_challenge.py`.
2. Run `scripts/submit_challenge.py` with the validated JSON file.
3. On success, close verbatim (substituting the returned ID):

> 已提交审批，赛题编号：`{submission.id}`。赛题不会立即公开；一般会在 **1 个工作天内**完成审批。审批通过后，可在公开赛题页查看：`https://skillschallenge.edgeone.dev/`。

4. On failure, state that automatic submission failed, output the complete validated JSON as the fallback, and direct the user to `https://skillschallenge.edgeone.dev/admin/import`.

Never say a submission succeeded without a successful endpoint response. The Expert may call only the public submission script, never an admin action.
