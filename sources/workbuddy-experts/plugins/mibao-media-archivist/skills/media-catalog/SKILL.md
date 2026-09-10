---
name: media-catalog
description: 秘宝26.9.6的持久媒体库执行入口：增量盘点、多位置、中文与字幕检索、标注、恢复、兼容迁移和可回读交付。
---

# 秘宝媒体库

## 运行

使用宿主已提供的 Python 3.11+ 与 SQLite FTS5。核心没有 pip 安装步骤、MCP、连接器、模型权重或 daemon。入口相对本 Skill 目录是 `../../bin/mibao-catalog.py`。

用宿主文件工具将 UTF-8 JSON 请求写入当前工作区的独立请求目录，随后以一次参数向量调用：

```text
python "${CODEBUDDY_SKILL_DIR}/../../bin/mibao-catalog.py" --request "<当前工作区>/mibao-requests/<唯一请求名>.json"
```

Skill 目录由宿主加载时解析；保持绝对工作区/请求路径。路径和搜索词等数据仅放 JSON，不拼接进 shell，不使用 `-c`、管道、重定向或动态命令。首次需要运行环境诊断时可调用同一入口 `--doctor`；无可用 Python 时报告条件缺失，不自行安装。

请求格式：

```json
{"schemaVersion":"mibao.request.v1","operation":"status","input":{"project":"<项目绝对路径>"}}
```

每次新动作使用新请求文件名。写动作有独立 claim/receipt；相同请求重放返回已有回执，改变旧请求内容会拒绝。如果前次可能已执行却没有回执，使用新请求读 status，并按 jobId 恢复，不盲目重放。请求和回执不能位于专家安装目录。

## 最小执行流程

1. 源目录和独立项目目录由用户给定或从当前明确上下文解析，两者互不包含。不把磁盘/主目录自动扩大为来源。
2. 新库 create；已有 `library.json` 则 status。旧 DB/manifest/task 走 legacy_view，禁止自动迁移。
3. add_source 登记当前授权源。scan 返回 jobId、discovered/hashed/reused/processed/failures/coverage。
4. state=paused 时，以新请求传 resume=jobId；取消任务保留已提交工作，不从取消态静默恢复。
5. 完成基本盘点后 report 生成有界 HTML/CSV/JSON 与哈希 manifest；按结果路径回读后由宿主展示。
6. 查找已有库使用 search。SRT/VTT 提供时以 subtitles 入库，再检索台词与时间码。外部字幕时间码不能当作媒体对齐已独立验证。

操作字段、示例和边界见 `references/operations.md`。只有相关动作才加载对应部分。

## 真实能力分层

- 核心已实现：目录、哈希、增量、中文文本/字幕、标注、集合、关系、兼容读取与显式迁移、完整交换、报告。
- 条件能力：FFmpeg 格式处理；当前宿主模型 OCR/ASR/视觉；已准备完整本地模型的离线分析。
- 模型结果默认候选；不能伪造向量、置信度、图片/视频读取、时间码或“已理解全部内容”。
- 具体云盘仅保留分页/快照合同；没有当前 provider 回执不能称已连通。资料库、自动化、分享只在用户具体要求后使用宿主能力。

无变化增量可复用旧哈希；fullHash=true 才做本轮完整校验。离线、部分枚举、排除规则变动和空结果异常不自动推断原件删除。原件修改/批量改名/删重不是默认功能。

## 结果与继续

核心返回 local-private 数据。完整交换包含数据库字段与关系，不包含原媒体备份。报告分页展示，不能把首1000行说成整个库。旧版信息已丢失时保持未知。错误、失败、中断与能力不可用必须保留，让下一轮从当前状态继续。
