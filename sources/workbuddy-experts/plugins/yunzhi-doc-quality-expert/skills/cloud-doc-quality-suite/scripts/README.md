# scripts/ 说明

## 设计原则

本目录脚本**不承担检测逻辑**，所有具体检测规则由 AI 按 `references/` 下的 8 个规则文件 + `rule-scoring.md`（评分）执行。
脚本仅在「AI 已经输出 JSON 检测结果 + 评分」之后，负责：

1. **持久化**：把 JSON 检测结果写入磁盘
2. **可视化**：渲染为 HTML 报告（含综合评分区块，便于业务方查看与归档）

## 文件说明

| 文件 | 作用 |
|------|------|
| `check.py` | 报告生成入口（CLI） |

## 使用方式

### 1. 渲染单份 JSON 检测结果

```bash
python scripts/check.py \
    --result ./ai_output.json \
    --output ./reports/
```

### 2. 覆盖文档名（用于命名报告文件）

```bash
python scripts/check.py \
    --result ./ai_output.json \
    --output ./reports/ \
    --doc-name "腾讯乐享产品白皮书"
```

### 3. 批量渲染目录下所有 *.json 检测结果

```bash
python scripts/check.py \
    --result ./batch_results/ \
    --output ./reports/ \
    --batch
```

## 输入 JSON Schema

检测结果 JSON 必须符合 SKILL.md 中定义的格式，关键字段：

```json
{
  "文档名称": "...",
  "检测时间": "ISO 8601 时间戳",
  "文档类型": "白皮书 / 案例集 / 解决方案 / 产品介绍 / 其他",
  "检测结果": {
    "structure":   { "检测状态": "已完成", "综合建议": "...", "建议详情": [...] },
    "timeliness":  { "检测状态": "已完成", "异常数量": 0, "问题列表": [...] },
    "link":        { "检测状态": "已完成", "异常数量": 0, "问题列表": [...] },
    "layout":       { "检测状态": "已完成", "异常数量": 0, "问题分布": {...}, "问题列表": [...] },
    "typo_writing": { "检测状态": "已完成", "异常数量": 0, "问题分布": {...}, "类别统计": {...}, "问题列表": [...] },
    "currency":     { "检测状态": "已完成", "异常数量": 0, "问题列表": [...] },
    "compliance":   { "检测状态": "已完成", "异常数量": 0, "类别统计": {...}, "问题列表": [...] }
  },
  "统计摘要": {
    "总问题数": 0,
    "各维度分布": { "structure": 0, "timeliness": 0, "link": 0, "layout": 0, "typo_writing": 0, "currency": 0, "compliance": 0 },
    "严重级别分布": { "P0_严重": 0, "P1_重要": 0, "P2_一般": 0, "P3_提醒": 0 }
  },
  "scoring": {
    "dimensions": [
      { "name": "内容时效性", "type": "main", "max": 45, "score": 0, "reason": "..." },
      { "name": "结构规范性", "type": "main", "max": 45, "score": 0, "reason": "..." },
      { "name": "内容准确性", "type": "main", "max": 10, "score": 0, "reason": "..." }
    ],
    "value_bonus": {
      "name": "内容价值性",
      "type": "bonus",
      "max": 10,
      "score": 0,
      "sub_scores": {
        "产品定位清晰度": "",
        "案例实证": "",
        "技术深度支撑": "",
        "一线销售可复用性": ""
      },
      "reason": "..."
    },
    "final_score": 0,
    "grade": "优秀 / 良好 / 合格 / 待改进",
    "summary": "一句话总评"
  },
  "总体评价": "..."
}
```

## 输出

| 文件 | 说明 |
|------|------|
| `<prefix>_quality_report.html` | 可视化 HTML 报告（便于业务方查看） |

## 依赖

- Python ≥ 3.8（仅使用标准库，无第三方依赖）

## 安全说明

- 仅读取本地 JSON 文件，不发起任何网络请求
- 不执行 shell 命令，无 RCE 风险
- 所有写入 HTML 的数据均经过 HTML 实体转义，防 XSS
- JSON 文件大小限制 50MB，防 DoS
