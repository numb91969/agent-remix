# 单课文件与续接执行

此文供专家执行，不把脚本参数交给教师填写。当前工具负责确定性处理；教学内容仍由当前宿主模型按用户材料生成，并由教师复核。

## 入口与能力判断

使用当前宿主提供的 Python 3.10 或更新版本；不安装服务，不调用 BookWriter、连接器或邻接专家。通过宿主注入的本 Skill 位置定位 `scripts/beike.py`，不可假设脚本位于教师工作区。

```text
python "<skill-root>/scripts/beike.py" health
```

若宿主未暴露执行能力或 Skill 路径，继续交付聊天正文及完整替换段，明确文件动作未完成。不要扫描用户电脑寻找软件，不要求安装 MCP。所有命令路径作为独立参数传递，含空格的路径正确加引号。

## 工作方式

1. 先根据教师当前要求作语义路由。`route` 只提供辅助建议，不是权限或意图真源，允许通过请求JSON的 `intent` 明确语义。
2. 教师明确指定文件时，用 `inspect` 读取该文件。仅列文件名不等于读过正文。`--start/--end` 对文本是行号，对DOCX是正文段落号（含表格内段落），**不是打印页码**。教师指定打印页码时，改用宿主的PDF/页面读取工具；不能用段落号冒充页码。
3. 需要整课文件时，模型内部形成 `schemas/lesson.v2.schema.json` 的课时内容。不要从空模板直接生成空洞占位教案，不让教师写JSON。
4. 使用 `validate` 校验字段、来源绑定、目标覆盖和课时时间。校验通过不代表学科事实正确。来源冲突保留，不把模型假设变成教师已确认事实。
5. 明确请求文件后，沿既有授权生成新文件，执行回读，再使用当前宿主的文档预览检查版式。普通保存不反复索要同一授权。
6. 后续需要继续时保存最小项目记录；恢复先读取当前文件，教师手改优先于旧JSON。

## 常用命令

```text
python "<skill-root>/scripts/beike.py" route --workspace-root "<工作区>" --input request.json
python "<skill-root>/scripts/beike.py" inspect --workspace-root "<指定文件所在目录>" --input "旧教案.docx"
python "<skill-root>/scripts/beike.py" validate --workspace-root "<工作区>" --input lesson.json
python "<skill-root>/scripts/beike.py" render --workspace-root "<工作区>" --input lesson.json --format docx --output "教案_v02.docx" --authorized
python "<skill-root>/scripts/beike.py" render --workspace-root "<工作区>" --input lesson.json --format docx --audience student --output "任务单_v02.docx" --authorized
python "<skill-root>/scripts/beike.py" render --workspace-root "<工作区>" --input lesson.json --format md --output "教案_v02.md" --authorized
python "<skill-root>/scripts/beike.py" render --workspace-root "<工作区>" --input lesson.json --format html --output "课堂流程_v02.html" --authorized
```

`--authorized` 只记录宿主已从本次用户请求确认文件写入，不是凭一个开关增加权限。输出目录必须已存在；助手可在已有项目写入授权内创建明确目标目录，不让教师手工准备。默认Letter纸张；教师要求A4时传 `--paper A4`，提供学校模板时按模板尺寸。

本地材料的 `path/sha256/bytes` 来自实际读取结果；用户材料在工作区外时，用宿主读取指定范围并保留来源，不自动复制或移动材料。便携校验器验证本工作区内材料绑定；外部材料用 `kind=host_material` 记录真实读取范围与 `observationRef`，引用宿主当次读取证据，不伪装成已由本地脚本核验的材料。来源事实仍由教师复核。

## 一处修改

整课结构修改使用 `revise --input lesson.json --change change.json --output lesson_v02.json --authorized`。变更文件包含 `expectedDigest`（validate返回的内容摘要）、`activityId`、`changes` 和 `reason`。只允许改该活动的内容字段，目标/评价/作业保持。改动时长造成全课时间不匹配时需说明影响，不能暗改其他环节来凑总时长。

旧DOCX或MD使用 `replace --input old.docx --change change.json --output new.docx --authorized`。变更文件必须有 `expectedSha256`、`anchor`、`replacement` 和 `reason`。锚点必须唯一，旧DOCX当前仅支持一个普通文本段落内替换（可以跨多个文本run）。复杂域、修订标记、图片或公式位于目标段落时返回宿主编辑需求；不能为了成功删掉这些结构。其他ZIP成员保留原字节，范围外正文保留。输出DOCX仍须预览。

## 学校模板

`render ... --template "学校模板.docx"` 支持含一个独立正文段落 `{{lesson.content}}` 的DOCX模板，另支持正文/表格中的 `{{lesson.title}}`、`{{lesson.grade}}`、`{{lesson.subject}}`。保留模板的页眉、页脚、图片、纸张与已有样式。未知令牌或页眉页脚令牌显式拒绝。

教师给普通学校模板时，先用其副本作字段/位置映射，经宿主确认适配后使用；不要求教师给原件添加令牌。不支持的复杂任意模板需由宿主编辑，不宣称零损失自动适配。模板只是版式，不是教材事实来源。

## 续接与旧资产

```text
python "<skill-root>/scripts/beike.py" save-project --workspace-root "<工作区>" --project-id lesson-a --input checkpoint.json --expected-revision -1 --authorized
python "<skill-root>/scripts/beike.py" resume --workspace-root "<工作区>" --project-id lesson-a
python "<skill-root>/scripts/beike.py" status --workspace-root "<工作区>" --project-id lesson-a
python "<skill-root>/scripts/beike.py" legacy --workspace-root "<工作区>" --input old-card.json
```

checkpoint包含 `operationId`、完整 `lesson`、`artifacts`（每项只含相对路径path、bytes、sha256）和note。首次修订号为-1，后续使用status返回的revision。记录追加在 `.beike-yi/<project-id>/`；同操作ID同输入重放不增加版本，冲突输入拒绝。status/resume/legacy不创建目录或修复记录。

包根 `examples/runtime/lesson.json` 与 `material.md` 提供完整合成输入。开发者演练时先复制到独立测试工作区，再执行文件命令；不要把专家安装目录当成输出工作区。示例不是教师真实材料或教材认证。

恢复只核对记录中的指定文件，缺失文件是“当前未找到”，不当成删除。路径迁移后，在教师指定新工作区用相对路径恢复，不扫整盘。手改文件返回当前内容与变化，先对齐再写新版本。legacy保留所有字段，包括未知字段，不自动升级旧项目。

## 状态和错误

`saved_and_read_back` 只表示文件生成与结构回读完成。`presentationStatus=not_inspected` 时不能说版式已检查；通过实际预览后再说明当前文件的版式观察。教师审核、课堂实施和学习效果分开表达。

`output_exists` 保留原件并选择新版本名；`revision_stale/source_changed` 先读取当前文件；`revision_anchor_not_unique` 只定位该处；`project_revision_conflict` 保留双方版本；`atomic_commit_unavailable` 保留聊天成果，使用宿主受控新文件写入。禁止无界重试、覆盖清理、静默格式替代和外部发送。

质量评审最多两轮定向修正，范围与标准固定，退步时保留较好版本。正常教学未知进入复核项；机器不得编造教师批准或用自评分证明学生已学会。
