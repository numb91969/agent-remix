# 可编辑 Word 交付

当用户需要 Word 成果且当前项目文件已实际读取，可用统一 `exportDocument` 入口，在原输入中增加 `formats:["markdown","html","docx"]`。返回的 `openPath` 指向可编辑预览副本；规范交付留在 deliveries 内，并由 manifest 逐文件记录字节和摘要。默认不传 formats 时仍生成原有 Markdown、HTML、resume.json 三件套。

当前新建支持普通段落、一级和二级标题、显式粗体与斜体。Markdown软换行按段内空格处理，一级二级标题会识别相邻正文；复杂表格、代码围栏、图片导入以及三级以上标题不在此转换范围，返回具体未支持原因。不能静默转成不满足用户要求的格式后宣称交付完成。不同格式选择和生成器依赖字节均进入交付身份。

已有DOCX的局部修改用 `expert-tools.mjs docxEdit`，或使用包内 Python 标准库工具 `docx-edit.py`。`--example docxEdit` 给出只读检查输入。检查可用后，编辑输入为：

```json
{
  "operation": "edit",
  "root": "/replace-with-authorized-project",
  "source": "input.docx",
  "expectedSourceSha256": "replace-with-the-actual-64-character-sha256",
  "output": "revised.docx",
  "edits": [{"textAnchor": "原文字串", "replacement": "替换文字", "paragraphAnchor": "包含原文字串的完整段落"}]
}
```

output必须是新的项目内路径。原件不覆盖，目标锚点必须唯一；带字段、公式、修订、图形或其他复杂结构的目标被拒绝。非目标页眉、页脚、图片及其他受支持被动部件保留其解压后字节。工具对可执行、外部关系或未知类型会失败关闭，不承诺处理所有Word文档。Python缺失时说明该可选能力不可用，继续提供可编辑正文，不要求安装连接器或常驻服务。

该工具的源保护及字节回读不判断文字是否真实、是否属于作者声音，也不证明当前文件已在宿主或Word界面打开。每次实际交付仍需检查打开结果和页面；若当前任务没有渲染证据，应保留版式待验证。新版本开发样例在隔离LibreOffice中完成过读取、修改、保存、重开和逐页检查，这不替代用户当前文件的验收，也不宣称Microsoft Word或WorkBuddy当前会话已实测。

预览修改不改变规范交付；要将修改后的文件作为新成果，明确采用新版本并重新生成回执。`verifyDelivery` 做两次物理读取核验交付组，之后发生的新改动仍需重新核验。旧v2交付清单可以继续读取，新Word集合使用v3清单，不要求迁移旧项目。
