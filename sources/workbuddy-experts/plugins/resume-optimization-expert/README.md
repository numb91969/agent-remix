# 简历优化专家

融合猎头顾问、ATS 工程师与职业规划师视角的求职简历专家：百分制评分、40+ 项清单精修、JD 精准定制、多格式导出。

## 类型

Agent 型（单个 AI 专家）

## 核心能力

1. **百分制专业评分** — 内容质量 30 / 结构与排版 25 / 语言与语法 20 / ATS 优化 15 / 影响力与印象 10，输出总分、A+~F 等级、Top 3 优势、优先级改进项（含 Before→After 示例）与 5 步行动计划。
2. **40+ 项清单深度润色** — 覆盖联系方式、摘要、工作经历、教育背景、技能、语法、排版、ATS 兼容性 8 大类，逐项 ✅/❌/⚠️ 标注，输出强动词 + 量化成果精修稿，并按 🔴🟡🟢💡 分级说明。
3. **岗位精准定制** — 解析 JD（必备/加分技能、职责、关键词）→ 差距矩阵 → 关键词自然融入 → 匹配度提升对比，附求职信要点与面试准备。
4. **多格式专业导出** — Word / Markdown / HTML / LaTeX / PDF，内置 modern、professional、minimal、academic 四套模板。

## 目录结构

```
resume-optimization-expert/
├── .codebuddy-plugin/plugin.json
├── agents/resume-optimization-expert.md     # 专家主 Prompt
├── skills/resume-toolkit/
│   ├── SKILL.md
│   ├── references/
│   │   ├── scoring-model.md                 # 五维度评分模型与等级
│   │   ├── checklist-40.md                  # 40+ 检查项 + 强动词表 + 量化指南
│   │   ├── ats-guide.md                     # ATS 解析兼容与 JD 关键词策略
│   │   └── export-formats.md                # 五种格式导出规范
│   ├── scripts/resume_score.py              # 百分制评分计算器
│   └── templates/
│       ├── resume-modern.html               # 科技/创业风
│       ├── resume-professional.html         # 金融/法律/咨询风
│       ├── resume-academic.tex              # 学术/科研风（XeLaTeX）
│       └── score-report.md                  # 评分/润色/定制报告骨架
└── avatars/expert.png
```

## 使用示例

- "发我你的简历（或粘贴内容），我先做百分制评分诊断，给出优先改进项。"
- "这是目标岗位 JD 和我的简历，帮我做差距分析并按 JD 定制，给出匹配度提升对比。"
- "把这份简历按 modern 模板导出成可打印的 HTML/PDF，并确认 ATS 解析兼容。"

## 评分脚本

```bash
python3 skills/resume-toolkit/scripts/resume_score.py \
  --content 18 --structure 15 --language 12 --ats 7 --impact 5 \
  --after-content 28 --after-structure 23 --after-language 18 --after-ats 14 --after-impact 9
```

## 安装位置

```
<local-user-path>
```

重新注册（修改专家后必须执行）：

```bash
python3 scripts/register_expert.py <expert-dir>
```

## 头像

头像已自动生成在 `avatars/` 目录，可手动替换（PNG/JPG，512×512，≤500KB）。

## 版本

v1.0.0
