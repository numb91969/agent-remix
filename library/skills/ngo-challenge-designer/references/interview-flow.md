# Interview flow

## Opening

Use Simplified Chinese for NGO-facing questions. Keep explanations short. Prefer a single clickable question per turn.

## Question map

| Stage | Goal | Default question | Selection |
|---|---|---|---|
| Track | Classify broadly | 这个工作问题主要属于哪些方向？ | Multi-select + primary |
| Organization | Establish issuer identity | 这道题目由哪个机构提出？（会显示在赛题上） | Single free-text answer, with「暂不公开」choice |
| Pain | Identify one problem | 你目前最想解决的工作痛点是甚么？ | Single-select |
| Current method | Understand today | 目前你们通常怎样处理这个问题？ | Single-select; multi-select only when several methods are genuinely used |
| Frequency / effort | Establish baseline | 这个情况大约多久发生一次？ | Single-select ranges |
| Outcome | Define desired change | 你希望日常工作变成甚么样？可多选。 | Multi-select; faithfully join selected phrases into `desired_outcome` |
| Success | Define evidence | 出现甚么可观察的改变，便算真的有帮助？可多选。 | Multi-select → `success_criteria[]` |
| Materials | Identify inputs | 完成这项工作通常会用到哪些资料？可多选。 | Multi-select → `materials[]` |
| Boundaries | Protect data | 哪些内容不能公开或必须由人确认？可多选。 | Multi-select → `boundaries[]` |
| Title | Name the brief | 以下哪个题目名称最合适？ | Single-select |
| Confirmation | Submit for review | 是否确认提交审批？ | Single-select |

## Dynamic choice patterns

### Track to organization

After the primary track is confirmed, ask once for the issuing organization. Keep it lightweight:

- 直接输入机构名称（一行即可）
- 暂不公开（赛题会显示「未公開機構」）

If the user chooses not to disclose, store `organization_name: "未公開機構"` and note it in `internal_metadata.fit_reasons` or scope notes is NOT required — anonymity is acceptable. Ask `organization_intro` only if the user volunteers context; do not push.

### Track to pain

Generate pains that describe work friction, not solutions.

Example for report/document + data tracks:
- 资料分散，整理和汇总很花时间
- 经常重复复制、贴上和调整格式
- 不同同事记录方式不一致
- 容易遗漏数据、服务重点或必填内容
- 其他（自己描述）

### Pain to current method

Example for fragmented data:
- 由同事逐份打开文件，再人工汇总
- 在 Excel、Word 或表格之间复制贴上
- 先各自整理，再由一位同事统一核对
- 暂时没有固定做法，每次临时处理
- 其他（自己描述）

### Current method to baseline

Prefer ranges when exact numbers are not known:
- 每天都会发生
- 每周 1–3 次
- 每月 1–3 次
- 只在特定活动或报告期发生
- 不确定／其他

### Pain to outcome

Example for fragmented, repetitive reporting:
- 把分散资料整理成统一结构
- 减少重复输入和复制贴上
- 在输出前提示缺失资料
- 保留人工检查后再输出的步骤
- 其他（自己描述）

### Outcome to success

- 完成时间明显缩短
- 遗漏或错误减少
- 不同同事的输出更一致
- 新同事也能按相同步骤完成
- 其他（自己描述）

## Choice rules

- All NGO-facing questions, choices, previews, and process reminders must use Simplified Chinese.
- Show 3–4 generated choices plus Other.
- Use multi-select where several answers can truthfully coexist: tracks, current methods (if genuinely multiple), outcomes, success criteria, materials, and boundaries.
- Use single-select for the primary pain, primary track, frequency/baseline, trial scenario, title, and approval confirmation.
- Keep labels concrete and mutually distinguishable.
- Do not select choices on the user's behalf.
- Do not generate organization-specific facts without evidence; organization identity must come from the user's own answer.
- If the user types a complete answer, extract it and skip redundant questions.
