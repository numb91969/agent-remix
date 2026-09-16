# 考试作文批改 HTML 报告数据契约

HTML 仅用于 CET 与考研作文批改。一般写作修改和范文精读默认在对话中交付。

## 输入 JSON

```json
{
  "schema_version": "1.1",
  "report_type": "exam_review",
  "title": "CET-4 作文批改报告",
  "meta": {
    "task": "CET-4",
    "source": "CET-2016",
    "generated_at": "2026-08-30 20:50",
    "total_word_count": 145,
    "excluded_word_count": 3,
    "effective_word_count": 142
  },
  "score": {
    "raw": 11,
    "deduction": 1,
    "final": 10,
    "maximum": 15,
    "band": "11档"
  },
  "summary": "整体判断",
  "evidence": [
    {
      "claim": "支持当前档",
      "quote": "作文原句",
      "reason": "判断说明"
    }
  ],
  "issues": [
    {
      "priority": "P1",
      "location": "P2",
      "original": "原句",
      "suggestion": "建议改法",
      "reason": "原因"
    }
  ],
  "actions": ["下一步动作一", "下一步动作二"]
}
```

## 必填规则

- `schema_version` 固定为 `1.1`。
- `report_type` 固定为 `exam_review`。
- `title`、`summary` 为非空字符串。
- `meta.task` 只能是 `CET-4`、`CET-6`、`PG1A`、`PG1B`、`PG2A`、`PG2B`。
- `meta.source` 必填；填写实际使用的依据 ID。
- `meta.generated_at` 使用 `YYYY-MM-DD` 或 `YYYY-MM-DD HH:MM`。
- `score.raw`、`score.deduction`、`score.final`、`score.maximum` 使用非负整数。
- 满分：CET-4/CET-6 为 15；PG1A/PG2A 为 10；PG1B 为 20；PG2B 为 15。
- `score.final = max(0, score.raw - score.deduction)`。
- `score.band` 必须与 `score.raw` 对应的基准档一致。
- `evidence` 至少一项，每项的 `claim`、`quote`、`reason` 均为非空字符串。
- `issues` 可为空；有项目时 `priority`、`location`、`original`、`suggestion`、`reason` 均必填。
- `actions` 至少一项，每项为非空字符串。

## 词数规则

- 只有脚本可靠返回时才填写 `total_word_count`、`excluded_word_count`、`effective_word_count`。
- 三项同时存在时必须满足：`effective_word_count = total_word_count - excluded_word_count`。
- 三项均为非负整数，且排除词数不得大于总词数。
- 脚本返回 warning 或无法可靠分离时，只保留总词数，并在 `summary` 中说明限制。

## 分档规则

- CET 原始分 13—15 / 10—12 / 7—9 / 4—6 / 1—3 / 0 对应 14 / 11 / 8 / 5 / 2 / 0 档。
- 考研按 `exam-writing-review.md` 中当前题型的五档区间映射。
- CET 和考研当前均使用整数；不输出无依据的 0.5 分。
- 只有档次区间、无法给稳定整数时，不生成数字型 HTML 报告；先在对话中交付定性结果。

## 文件规则

- 所有用户内容在渲染时进行 HTML 转义。
- 分数、扣分、档次、证据和建议与对话输出一致。
- 报告不加载外部脚本、字体、图片或远程资源。
- 报告使用新文件名，不覆盖用户材料。
- 数据校验失败时停止生成并报告具体字段。
