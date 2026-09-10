# 多格式导出规范

## 一、模板选择矩阵

| 模板 | 适用人群 | 视觉特征 |
|------|---------|---------|
| `resume-modern.html` | 科技 / 互联网 / 创业公司 / 工程师 | 单栏、无衬线字体、标题细线分割、强调色条 |
| `resume-professional.html` | 金融 / 法律 / 咨询 / 传统制造 | 衬线标题、居中姓名头、克制的深蓝主色 |
| `resume-minimal` | 10 年以上资深 / 工程专家 | 极致单栏、纯文本层级、无装饰色（在 modern 模板上去除强调色即为此风格） |
| `resume-academic.tex` | 学术 / 科研 / 高校 | 论文与项目列表、XeLaTeX + CJK 排版 |

## 二、HTML 模板使用规范

1. 复制 `templates/resume-*.html` 到输出目录后再修改（**不修改模板原件**）
2. 只替换内容占位区，保留 `<style>` 与 `@media print` 不变
3. 中英文混排：数字/英文与中文之间加空格
4. 打印设置：A4、边距 12-15 mm、勾选"背景图形"（保证色条打印）
5. 生成后用 `present_files` 打开预览，再由用户浏览器导出 PDF

## 三、各格式要点

### Markdown（工作主格式）
- 一级标题 = 姓名；二级标题 = 版块；三级或加粗 = 公司/职位
- 要点用 `-` 列表，每条一行
- 保留原始文本，便于后续任意格式转换

### Word (.docx)
- 由 Markdown + YAML front matter 转换：
  ```yaml
  ---
  title: 张三-整车控制器工程师
  author: 张三
  template: professional
  ---
  ```
- 使用内置"标题 1/2/3"样式，不使用手动字号放大
- 项目符号统一一种样式；不套表格

### LaTeX
- 使用 `templates/resume-academic.tex`，编译命令：
  ```bash
  xelatex -interaction=nonstopmode resume.tex
  xelatex -interaction=nonstopmode resume.tex   # 二次编译解决引用
  ```
- 中文字体通过 `xeCJK` 设置，macOS 推荐 `PingFang SC`，Windows 推荐 `SimSun`
- 编译必须先本地跑通，再交付

### PDF
- 由 HTML 或 LaTeX 导出，**禁止扫描件/图片型 PDF**
- 导出后必须验证：能复制文字、无分页断裂（每项经历不被拆到两页）

## 四、交付前校验

| 校验项 | 方法 |
|--------|------|
| 文本层可选中 | 打开 PDF 尝试选中复制 |
| 分页无断裂 | 预览每页，条目块不被拆分 |
| 版面一致 | 全文日期、标点、字体统一 |
| 链接可用 | 邮箱、主页链接点击测试 |
| 文件命名 | `姓名-目标岗位-年限.pdf` |
