# Approval and publication reminder

Use this wording in the final confirmation turn, after presenting the full brief:

> 你确认提交后，赛题会先进入平台审批，不会立即公开；一般会在 **1 个工作天内**完成审批。审批通过后，可在公开赛题页查看：`https://skillschallenge.edgeone.dev/`。

Offer exactly these actions:

- 确认提交审批
- 修改内容
- 暂不提交

Rules:

- Only `确认提交审批` sets `conversation_state.status` to `ready_to_sync`.
- This action is a submission to platform review, never direct publication.
- The admin process performs the later publish action (`ready_to_sync` → `synced`).
- Only `synced` challenges appear on the public site.

## Validate and submit (immediately after `确认提交审批`)

1. Assemble the JSON per `challenge-schema.md` (`schema_version: "1.2"`, `id: null`, status `ready_to_sync`, `explicit_confirmation: true`). Map the primary track to `publishable.theme` (one of: 文書撰寫, 數據整理, 知識查找, 流程管理, 其他). Generate 2–4 descriptive `auto_tags`. Generate a non-empty `confirmed_snapshot_id`.
2. Validate with `scripts/validate_challenge.py`; fix all errors first.
3. Run `scripts/submit_challenge.py` with the validated JSON file.
4. On success, report the returned challenge ID and remind the NGO that approval normally takes 1 working day; do not output the full JSON unless requested.
5. On failure, never claim submission. Output the validated JSON as a fallback and point to `https://skillschallenge.edgeone.dev/admin/import`.

The Expert calls only the public review-submission endpoint and never uses or embeds admin credentials. Publication remains an admin action.
