# 测验平台字段与调用参考（实测校验）

来源：`recruit-mcp` → `quizplatform` 分组，全部只读。以真实响应为准，接口文档描述与实测冲突时以实测为准。

## 一、调用三步（不可跳步）

```text
① SearchAPI(query="关键词")        → 拿能力清单，定位 apiId
② SearchAPI(apiId="<原样复制>")     → 拿参数定义与调用示例
③ CallAPI(apiId, params)          → 真正调用
```

apiId 为三段式 `{domain}.{group}.{name}`，禁止自行拼接或凭记忆填写。

## 二、核心接口

### 场次详情（含考生列表）

- apiId：`recruit.quizplatform.post_api_mcp_exam_venue_detail2`
- 方法：POST
- 参数：`{"examVenueId": "<字符串>"}`
- 权限：`Quiz_ExamVenue_ReadOnly`

返回：

```json
{
  "venue": {
    "examVenueId": "...",
    "name": "场次名",
    "statusName": "待开始|测验中|阅卷中|已完成|已取消|草稿",
    "typeName": "考试|作业",
    "examStartTime": "yyyy-MM-dd HH:mm:ss",
    "examEndTime": "yyyy-MM-dd HH:mm:ss"
  },
  "totalCount": 6,
  "examinees": [
    { "examReceiptId": "...", "name": "考生名", "statusName": "待测验|作答中|已交卷|阅卷中|已出分|未参加|已取消" }
  ]
}
```

要点：不分页、一次全量、按创建时间倒序；场次不存在或无权限会抛业务异常。

### 成绩单

- apiId：`recruit.quizplatform.get_api_mcp_answer_result_queryResult`
- 方法：GET
- 参数：`receiptId`（即 `examReceiptId`，字符串）
- 状态自动路由：`unmark`（已交卷）/ `marking`（阅卷中）/ `marked`（已出分）都能查

顶层字段：`title`、`receiptId`、`examVenueId`、`markStatus`、`scoreFlag`、`completedFlag`、`studentInfo`、`testContentVO[]`、`scoreCard`。

`studentInfo`：`name`、`startTime`、`endTime`、`totalScore`、`durationInfo.formattedDuration`、`anonymousMarkFlag`。

`testContentVO[]` 单题：`questionSequence`、`questionType`、`questionId`、`title`、`titleRich`、`questionContent`、`studentAnswer`、`questionTrueAnswer`、`blankQuestionTrueAnswer`、`score`、`questionScore`、`status`、`trueAnswer`、`remark`、`overallRating`、`dimensionScore[]`、`examReceiptQuestionId`、`markPaperId`、`markPaperStaffId`、`markPaperStaffName`、`markTime`、`conversations`、`conversationsFetchStatus`、`deliverableUrl`。

`scoreCard`：按题型汇总，未使用的题型为 `null`（`radioChoice` / `multipleChoice` / `blankChoice` / `judgmentChoice` / `shortChoice` / `codeChoice` / `aiCodeChoice`）。

### 阅卷待办 / 阅卷详情（用于反查场次或辅助阅卷）

- 待办列表：`recruit.quizplatform.post_api_mcp_todo_mark_list`，参数 `{}`，固定只查待办，最多 100 条。可从 `records[].examVenueId` + `examVenueName` 反查可见场次。
- 阅卷详情：`recruit.quizplatform.get_api_mcp_todo_mark_detail`，参数 `markPaperId` + `receiptId`。返回评分参考、`canJudgeFlag`。AI 实战题的 `studentAnswer` 实测为空，对话记录要走 `queryResult`。

### AI 实战题交付物打包

- apiId：`recruit.quizplatform.post_api_mcp_answer_result_downloadAllFiles`
- 参数：`{"examReceiptId": "...", "questionId": "..."}`
- 仅在 `deliverableUrl` 为 `null`（归档未生成）时调用以触发打包。返回二进制流，**不要让它进上下文**。

## 三、题型与作答结构

| `questionType` | 归类 | 作答结构 | 可能有附件 |
|---|---|---|---|
| `radio` | 客观 | `studentAnswer[]` 里的 `optionId`，用 `questionContent.radioOptionList[]` 映射 `describe` | ❌ |
| `multiple` | 客观 | 同上，用 `multipleOptionList[]` | ❌ |
| `judgment` | 客观 | 同上，用 `judgmentOptionList[]`，语义为正确 / 错误 | ❌ |
| `blank` | 客观 | `studentAnswer` 内每空 `blankAnswer`，其次 `text` | ❌ |
| `short` | 主观 | 生产返回 `studentAnswer.answer` + `studentAnswer.attachment[]`；旧结构为 `text` + `attachments[]` | ✅ `studentAnswer.attachment[]` |
| `code` | 主观 | `studentAnswer.sourceCode`（+ `submitTime`） | ❌ 源码是文本字段，不是附件 |
| `aiCoding` | 主观 | `studentAnswer.workspace` + `conversations[]` + `deliverableUrl` | ✅ `testContentVO[].deliverableUrl` |

🔒 **附件只有两个来源**：`short` 的 `studentAnswer.attachment[]`，和 `aiCoding` 的 `deliverableUrl`。
其余题型没有附件位——遍历 `testContentVO[]` 时**不要在客观题/代码题上找附件**，字段为 `null` 是正常的，不是缺漏。
附件数口径 = `Σ(short 的 attachment[] 长度) + Σ(aiCoding 的 deliverableUrl 非空数)`。

⚠️ `short` 的 `answer` 为空字符串 **不等于未作答**：实测存在文本空、作答全在附件里的情况（`allowUpLoadFile=true` 时考生直接上传 ZIP）。此时必须下载附件才拿到真实作答。

`trueAnswer`：0 错、1 对、2 部分正确（客观题主用）。
`status`：0 未阅、1 已阅。
`dimensionScore[].dimension`：`D1` 意图澄清 / `D2` 任务拆解 / `D3` 审辩决策 / `R1` 交付质量，`score` 为 1-5。
`conversationsFetchStatus`：`SUCCESS` / `EMPTY`（考生确实无会话）/ `FAILED`（接口异常）。

## 四、附件下载与 403 排障

> **前提：先确认这道题会有附件**——只有 `short`（`studentAnswer.attachment[]`）和 `aiCoding`（`deliverableUrl`）两个来源，客观题与 `code` 代码题没有附件。

签名 URL 形如：

```text
https://tmpattachment-1252291750.cos.ap-guangzhou.myqcloud.com/out-s_quiz/<id>.zip
  ?q-sign-algorithm=sha1
  &q-ak=<AK>
  &q-sign-time=<start>;<end>
  &q-key-time=<start>;<end>
  &q-header-list=host
  &q-url-param-list=
  &q-signature=<40 位 hex>
```

参数含义与实测值：

| 参数 | 说明 | 实测 |
|---|---|---|
| `q-sign-time` | 签名有效期，`<起始>;<结束>`，Unix 秒 | 窗口 1800 秒（30 分钟） |
| `q-key-time` | 密钥有效期，通常与 `q-sign-time` 相同 | 同上 |
| `q-signature` | HMAC 签名 | **固定 40 位小写 hex** |
| `q-ak` | 临时 AK | 每次重取都可能变 |

落盘命令：

```bash
curl -L --fail --silent --show-error "<整段原始 URL>" -o "<dir>/<name>.zip"
file "<dir>/<name>.zip"   # 期望：Zip archive data
```

### 403 分因处置（关键：两种 403 处理方式不同）

```bash
# ① 先看签名长度是否 40 位 hex
python3 -c "import sys;s=sys.argv[1];print(len(s), all(c in '0123456789abcdef' for c in s))" "<q-signature 值>"

# ② 再看时间窗是否过期
date +%s                  # 当前时间
# 与 q-sign-time 的 <结束> 比较
```

| 判定 | 病因 | 正确处理 |
|---|---|---|
| 签名长度 ≠ 40 或含非 hex 字符 | 复制时截断 / 漏字符 | 用响应里的**原串**重发 curl；**不要**重取接口 |
| 签名格式正确，`q-sign-time` 结束时间 < 当前时间 | 签名真过期 | 重新调 `queryResult` 拿新 URL |
| 签名格式正确、未过期，但 URL 其他参数与响应有差异 | URL 被改写 / 转义丢失 | 用原串重发 |
| 重取接口后仍 403 | 权限不足 / COS 对象不存在 | 停止重试，如实告知用户 |

硬规则：

1. 换签名的唯一正确方式是**重新调 `queryResult`**；AI 实战题归档未生成（`deliverableUrl=null`）时才用 `downloadAllFiles` 触发打包。
2. **禁止**手改 `q-sign-time` / `q-key-time` / `q-signature` 试图续期——签名与这些参数强绑定。
3. **禁止**对同一 URL 无脑重试：403 是确定性拒绝，不是网络抖动。
4. 批量下载逐条记录成败，失败只重取失败那条，不整批重来。
5. **先下载、后排版**：签名只有 30 分钟，先把附件全部落盘再做表格。

### 实测踩坑记录（2026-08-06）

第一次下 `harbor.zip` 返回 403，当时误判为"签名过期"，实际是**签名串少复制了 1 个字符**（用了 39 位，真实为 40 位 `53ca305e...`）。当次 `q-sign-time` 窗口尚未过期。

教训：403 后**先验签名长度，再验时间窗**。若一批 URL 里其他几条能正常下载，几乎可以断定失败那条是复制问题，而不是过期。

## 五、实测样例（用于回归对照）

场次 `2084849732934610946`：

- 名称：TEG - AI Data 部 - 大模型数据研发实习生（Agent 方向）笔试
- `statusName=测验中`，`typeName=作业`
- `totalCount=6`：待测验 2、作答中 3、已出分 1

已出分考生程玮琦 `examReceiptId=2084892647195062273`：

- `markStatus=marked`、`completedFlag=true`、`scoreFlag=false`、`totalScore=null`
- 5 题：3 道 `multiple`（均 `trueAnswer=0`）+ 2 道 `short`（`remark=本题不参与人工阅卷`，`markPaperStaffName=system`）
- **附件 4 个，全部出自那 2 道简答题**：第 4 题 1 个（`harbor.zip`），第 5 题 3 个（`go-config-hotreload-override-fix.zip`、`bpe-tokenizer.zip`、`persistentKV (1).zip`）；3 道多选题**没有也不该有附件**
- 两道简答题 `studentAnswer.answer` 均为空字符串，**作答实体全在附件里**——这正是"文本空≠未作答"的实证

该样例可用于验证：状态分类是否正确、题目数是否为 5、附件数是否为 4（且只从简答题统计）、客观题是否被误判为"附件缺失"、空值是否被如实保留。
