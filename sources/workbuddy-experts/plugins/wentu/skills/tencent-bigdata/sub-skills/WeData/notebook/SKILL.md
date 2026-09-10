---
name: notebook
description: 当用户需要对 Notebook 进行代码编辑、执行运行、诊断排错时使用此技能。支持读取/保存/重命名（移动）notebook 文件、提交执行任务并查询状态、获取文件诊断信息（包括 kernel 状态、执行错误、环境信息等）、通过 Spark app_id 进行 AI 智能诊断、在 skill 和用户都无法解决问题时向对应板块 oncall 负责人告警或拉群、检索 Notebook 产品官方 iWiki 文档（使用手册 / FAQ / 实践案例 / 版本更新等 55 篇 reference）辅助回答产品用法类问题，并以 **agent diff 审阅 v2 模式**提交修改（save-notebook --with-diff，让用户在前端逐 cell accept / reject 后再执行）。可串联为"编辑→执行→诊断→修改→执行→诊断"的循环工作流。触发关键词包括：notebook、代码编辑、代码运行、代码执行、代码诊断、排错、调试、Spark诊断、app_id、oncall、告警、拉群、负责人、iwiki、官方文档、使用手册、FAQ、协作区、太极迁移、NotebookRunner、资源模板、AI Coding、Ray kernel、Iceberg、Lance、PySpark 包兼容、重命名、改名、改文件名、移动文件、移动目录、rename、move、diff、审阅、accept、reject、cell 级 diff、agent_diff、用户确认。
---

# Notebook 智能编辑运行诊断

## 概述

通过 WeData Notebook 平台对 notebook 文件进行代码编辑、执行运行和诊断排错。本技能封装了 Jupyter Server 的核心 API，提供以下子技能和一个串联工作流：

1. **代码编辑子技能**：读取、保存、重命名/移动 notebook 文件（对应 ContentsHandler 的 GET/PUT/POST/PATCH 接口）
2. **代码运行子技能**：提交 notebook 执行任务并查询状态（对应 ExecuteHandler/ExecuteStatusHandler 接口）
3. **代码诊断子技能**：获取 notebook 文件的完整诊断信息（对应 /api/sessions/file-info 接口，无需鉴权，通过 user 参数指定用户）
4. **存储交互子技能**：在 notebook 中添加 Ceph 存储操作 cell（hadoop fs 命令），支持 ls/put/get/mkdir/cat/put-variable 操作（默认自动添加 `fs.ceph.impl` 配置，**禁止删除操作**）
5. **Spark 诊断子技能**：通过 Spark application_id 调用 LLMAPP AI 诊断服务，获取异常类型、根因定位和解决方案
6. **Compute 管理子技能**：查询、创建和更新计算资源（对应 ComputeHandler 的 GET/POST/PATCH 接口，**不支持删除**）
7. **Oncall 通知子技能**：当 skill 和用户都无法解决某个问题时，按问题症状最明显的板块把它路由给对应 oncall 负责人——发送告警或拉 oncall 群（对应 /api/notify/alert 和 /api/notify/group-chat，**拉群必须征得用户同意**）
8. **iWiki 文档查询子技能**：检索 Notebook 产品官方 iWiki 文档（55 篇 reference，覆盖产品功能 / 实践案例 / 版本更新 / FAQ），先在本地索引按关键词缩候选再通过 iWiki MCP 抓正文，用原文回答产品用法类问题（**严禁绕过 iWiki MCP 直接抓 iwiki.woa.com**）
9. **Agent Diff 审阅子技能（v2）**：让 agent 改 notebook 时不直接静默覆盖——`save-notebook --with-diff` 会先 GET 当前 nb 作为 base，**在客户端**按 `cell.id` 算 cell-level diff，给变化的 cell 注入 `metadata.agent_diff = {action, base_source}` 后再 PUT；用户可在前端**异步**逐 cell accept / reject，**不阻塞 agent 后续 execute / diagnose / 下一轮编辑**（文件物理上已是 target，execute 跑的就是新代码；参见 [iWiki 4020552703](https://iwiki.woa.com/p/4020552703)）
10. **Ray driver_log 诊断子技能**：通过智研 OpenAPI 抓取任一 Ray Job 的 driver 全量日志（智研侧已落盘 `job-driver-<sid>.log`）并扫描 ERROR/Traceback/OOM 等异常；submission 定位支持两种入口——直接传 `--submission-id`，或传 Ray Dashboard URL + `--job-id` 由 `/api/jobs/` 自动翻译
11. **Ray 资源指标子技能**：通过 Ray Dashboard 内嵌的 Grafana Proxy 查询 Ray 集群的 CPU/GPU/内存/显存利用率时序及资源配置快照（出图依赖 matplotlib）
12. **智研管道日志检索子技能**：通过腾讯智研 OpenAPI（`openapi.zhiyan.oa.com`）按关键词/字段/时间窗口检索管道日志，覆盖 ES / CK 两种存储（Ray 日志 `dataflowName=ray_log` 为典型场景）
13. **串联工作流**：编辑 → 执行 → 诊断 → 修改编辑 → 执行 → 诊断 ... 的循环

> **鉴权说明**：第 10/11/12 三个诊断子技能走 Ray Dashboard / 智研 OpenAPI，与 notebook 主流程的 CMK 鉴权**相互独立**——Ray Dashboard 的 `/redirect/<base64>/` 入口通常匿名可访问（仅 401/302 时才需补 `--cookie`），智研日志检索用 `--token` 透传。

**核心用途**：帮助用户自动化 notebook 的开发调试流程，实现代码编写、运行、错误诊断、修复的闭环。

## 执行规则

- **隐藏所有执行细节**：整个过程中，不要向用户暴露任何底层操作痕迹：
  - 回复文本中**不要提及或展示**任何命令行指令（如 `do-bigdata wedata ...`）
  - 调用 `execute_command` 工具时，`explanation` 字段使用简短的中文描述（如「读取文件」「保存文件」「提交执行」「查询状态」「获取诊断」），**不要包含具体命令内容**
  - **不要展示原始 JSON 输出**，只提取关键信息以结构化方式呈现
  - 配置凭证时：收到用户的用户名和 CMK 后，静默完成配置，只告知「凭证配置成功」
- **用户视角**：用户应只看到操作进度和最终结果，看不到任何中间的技术细节。
- **分步进度反馈**：操作过程中必须让用户感知到进展：
  1. 凭证检查阶段 → 回复「正在验证凭证...」，完成后 → 「凭证验证通过 ✓」
  2. 编辑阶段 → 回复「正在读取/保存文件...」，完成后 → 「文件读取/保存成功 ✓」
  3. 执行阶段 → 回复「正在执行 notebook，请稍候...」，完成后 → 「执行完成 ✓」或「执行出错 ✗」
  4. 诊断阶段 → 回复「正在获取诊断信息...」，完成后 → 展示诊断结果
  5. Spark 诊断阶段 → 回复「正在进行 Spark 任务诊断...」，完成后 → 展示诊断结果（异常类型、根因定位、解决方案）
- **错误处理**：当某个步骤失败时，展示友好的错误信息，并建议用户可能的修复方案
- **Cell Output 展示**（默认不输出到前端）：为避免上下文贯穿过多低价值输出干扰用户，默认情况下**不向用户输出 cell 的执行 output**，仅用简要汇总反馈执行结果（成功 / 失败 / 每个 cell 的状态概述）。仅下列场景**必须**输出完整 output：
  1. **有 cell 执行失败**：输出失败 cell 的 error traceback，供用户/AI 诊断修复
  2. **用户明确要求查看 output**（如「展示运行结果」「打印 output」「看下 cell N 的输出」等）：全量展示相关 cell 的 stream / execute_result / display_data
  3. **Phase 7 交付验收阶段**上层任务明确要求汇报交付产物时：展示关键产出的 output（如最终评估指标、样例表格、图表路径）

  展示时仍遵循之前的红线：按 cell 序号 / cell_id 分组、单 cell 最多 500 行、超出提示已截断。

  获取方式（仅在上述场景才调用）：`read-notebook` 或 `execute-status`（单 cell 任务）从远端读取最新 cell outputs。

  > 不在上述场景时，禁止主动输出 cell output。完整 output 仍会随本地同步写回 `.ipynb` 文件，用户可本地查看。
- **`save-notebook` 必须走 Agent Diff 审阅**（[WARN] 强制要求 / 最高优先级）：只要 agent 通过 `save-notebook` 写 notebook 内容，**无论是修改已有文件还是新建文件**（包括 `edit-run-diagnose` 自动修复每一轮的保存、`add-storage-cell` 追加 cell、新增 cell、修改 cell、首次落地一份新 notebook 等任何会写 cells 的操作），**必须加 `--with-diff`**，以便用户在前端逐 cell accept / reject。
  - [OK] 默认行为：`save-notebook ... --with-diff`
  - [PIN] 修改场景：远端已有该文件 → 与远端 base 做 cell-level diff，仅变化的 cell 注入 `metadata.agent_diff`，未变 cell 维持原状
  - [PIN] 新建场景：远端无该文件 → 视作 base 为空，**所有 cell 都会被标为 `added`**，每个 cell 都进入用户 review 视图（用户可逐 cell accept / reject 这次新建产物）
  - [FAIL] 禁止：不加 `--with-diff` 直接 PUT 写 notebook（这会让用户失去 review / reject 通道）
  - [WARN] 唯一例外：用户**明确**说"直接改、别走 diff"——此时必须在回复里明确告知"已跳过 diff review，本次直接覆盖/写入"
  - 注意：`create-notebook` 仅用于创建空 notebook 占位，不涉及业务 cell 写入；只要后续要往里写实际 cell，仍走 `save-notebook --with-diff`
  - 详细协议、cell-level 约束、review 流程见**子技能九：Agent Diff 审阅（v2）**
- **文件修改禁区**（最高优先级 / 不可绕过）：**notebook 顶层 `metadata.file-id` 字段是远端文件的唯一身份标识，agent 在任何编辑场景下都不得修改、删除或伪造该字段。**
  - **前提条件**：远端已存在该文件（即先前能通过 `read-notebook` 成功拿到 content）。
  - **强制要求**：构造 `save-notebook --content` 的 JSON 时，`metadata.file-id` **必须与远端读取时的值完全一致**，**上传前后保持不变**。
  - **正确流程**：编辑前先 `read-notebook` 拿到完整 notebook → 在内存里改 `cells` / 业务字段 → **原样回写 `metadata.file-id`**（连同其他 metadata 一起）→ `save-notebook --with-diff` 提交。
  - **典型反模式（禁止）**：
    - [FAIL] 自己生成一份新 notebook JSON 时漏掉 `metadata.file-id`（会导致远端被识别为新文件，元数据/版本/git 关联全部断链）
    - [FAIL] 把 `metadata.file-id` 改成新 UUID 或空串
    - [FAIL] 删除整个 `metadata` 字段，只保留 `cells`
    - [FAIL] 把 A 文件的 `file-id` 复制到 B 文件的 content 里再 save（会污染远端身份映射）
- **本地文件同步**（[WARN] 强制要求）：当用户指定了本地文件路径（如 `file_from_notebook/xxx.ipynb`）时，必须遵循以下规则：
  1. **修改后同步到本地**：每次对 notebook 内容进行自动修改（包括代码修复、新增 cell、删除 cell 等）并保存到远端后，必须同时将修改后的完整 notebook 内容写回本地文件路径，确保本地文件与远端保持一致
  2. **执行后同步到本地**：每次 notebook 执行完成后（无论成功或失败），必须从远端重新读取 notebook 文件（此时包含最新的 cell outputs 和执行结果），并将其保存到本地文件路径，确保用户可以在本地查看执行结果
  3. **同步时机**：本地同步操作应在每次「保存到远端」或「执行完成」之后立即执行，不要等到整个工作流结束才同步
  4. **同步方式**：
     - notebook 同步（含 outputs）：`read-notebook` 拿到 JSON → 写本地，或直接 `download-file --type notebook`
     - 任意产物文件（html / csv / 图片）同步：**优先用 `download-file`**（一步到位）；老写法 `read-notebook --type file` 也能用，但返回的是带元信息的 JSON 响应，调用方还得自己剥壳。
- **关键信息结构化输出**（[WARN] 强制要求）：每次操作完成的回复**末尾**，必须以固定格式输出当前持有的关键信息：

  ```
  ---
  **[KEY] 当前操作关键信息**
  - **file_path**: `<文件路径>`
  - **compute_id**: `<计算资源ID>`
  - **session_id**: `<会话ID>`（如有）
  - **task_id**: `<任务ID>`（如有）
  - **kernel_state**: `<内核状态>`（如有）
  ```

## 工作流程

### 前置步骤：检查 CMK 凭证配置

在执行任何操作前，**必须先检查凭证是否已配置且有效**。

**检查方式**：通过 CLI 的 `auth status` 命令检查凭证状态：

```bash
do-bigdata auth status
```

**凭证存在且有效时**：直接进入工作流程。

**如果凭证不存在或已失效**，**立即停止**，引导用户提供凭证：

> 需要先配置 CMK 凭证才能使用 Notebook 技能：
>
> **CMK 密钥获取方式：**
> 1. 访问 https://wedata.woa.com/security/user/keys 下载个人 CMK 文件
> 2. 打开下载的文件，找到 `"key"` 字段的值即为 CMK
>    文件格式示例: `{"id":...,"subject":"xxx","key":"这里就是CMK","type":"cmk",...}`
>
> 配置凭证：
> ```bash
> do-bigdata auth init --user <RTX> --cmk <CMK密钥> --cmk-id <CMK_ID>
> # 或从 CMK JSON 文件内容解析
> do-bigdata auth init --from-json '{"id":...,"subject":"xxx","key":"xxx","type":"cmk"}'
> ```
>
> 请直接在对话中回复您的 CMK 文件内容（或单独提供 RTX 和 CMK），我会自动帮您完成配置。

### 子技能一：代码编辑

用于读取和保存 notebook 文件内容。

**读取文件**：
```bash
do-bigdata wedata read-notebook --path "Untitled.ipynb"
```

> **注意**：`read-notebook` 的 stdout 是**纯 JSON**（调试 URL 打到 stderr），可直接 `| python3 -c 'import sys,json; ...'` 消费。响应里 `content` 字段：notebook→dict、text 文件→字符串、二进制→base64。

**保存文件**（[WARN] 任何 `save-notebook` 都必须加 `--with-diff`，无论修改已有文件还是新建文件，详见**子技能九**）：
```bash
# [OK] 默认形式：走 diff 审阅协议（强制）
#   修改已有文件：与远端 base 做 cell-level diff，仅变化 cell 进入 review
#   新建文件：远端无 base，所有 cell 全部标为 added，每个 cell 都进入 review
do-bigdata wedata save-notebook --path "Untitled.ipynb" --content '<JSON内容>' --with-diff

# [WARN] 仅当用户明确说"直接改、别走 diff"时才省略 --with-diff（需在回复中告知已跳过 review）
# do-bigdata wedata save-notebook --path "Untitled.ipynb" --content '<JSON内容>'
```

**上传本地文件到远端**：
```bash
do-bigdata wedata upload-file --local-path ./data.csv --remote-path data.csv
```

> [WARN] **file_id / cell id 保留（避免破坏例行化绑定）**：`save-notebook` 与 `upload-file` 写 `.ipynb` 时，**默认会先 GET 远端文件，自动继承其 `file_id`（注入 `content.metadata.file_id`）与 cell id（按位置复用）再 PUT**。这是因为 jupyter server 在 PUT 时若 body 不带原 `file_id` 会**重新分配新 file_id**，导致 WeData 例行化调度绑定失效（任务"找不到"该 notebook）。
> - 远端不存在（新建）时不注入，由 server 正常分配。
> - 需找回被改坏的绑定时，用 `--file-id <原file_id>` 显式指定。
> - 确需全新 cell id 时，加 `--no-preserve-cell-ids` 关闭继承。
> - 输出 JSON 会回显实际保留的 `file_id` 与 `reused_cell_ids`，便于核对。

**下载远端文件到本地**（`read-notebook` 的"纯下载"变种，推荐做产物同步用）：
```bash
# 自动按后缀判断 notebook / file
do-bigdata wedata download-file --remote-path report.html --local-path ./report.html
do-bigdata wedata download-file --remote-path my.ipynb    --local-path ./my.ipynb
# 差异：
#  - download-file 的 stdout 只打一行简短 JSON 元信息（path/size/local_path）
#  - 文件内容直接按原格式落盘到 --local-path
#    * notebook → 序列化 JSON
#    * text/html / text/plain → 文本
#    * 二进制（.png/.zip...）→ base64 自动解码
#  - 避免 AI 自己 parse read-notebook 的嵌套响应
```

**重命名 / 移动文件或目录**（PATCH 接口，只改路径不重传内容）：
```bash
# 文件改名
do-bigdata wedata rename-path --old-path "Untitled.ipynb" --new-path "demo.ipynb"
# 文件搬家（移动到另一目录）
do-bigdata wedata rename-path --old-path "a/foo.ipynb" --new-path "b/foo.ipynb"
# 目录改名
do-bigdata wedata rename-path --old-path "old_dir" --new-path "new_dir"
```
> - 只改路径、**不重新上传内容**（内容修改请用 `save-notebook --with-diff`）。
> - 命中以下路径会被服务端拒绝（403）：`/projectshared` 根或一级子目录、`/projectshared/*/WeData任务模板/*.ipynb`、任何 `/wedata_nb_tutorials` 开头的路径。

### 子技能二：代码运行

用于提交 notebook 执行任务并查询状态。支持执行所有 cell 或指定执行单个 cell。

**执行所有 cell（异步）**：
```bash
do-bigdata wedata execute --file-path "Untitled.ipynb" --compute-id "xxx"
```

**执行所有 cell（等待完成）**：
```bash
do-bigdata wedata execute --file-path "Untitled.ipynb" --compute-id "xxx" --wait
```

**逐 Cell 执行（推荐用于 Ray/GPU 等长耗时任务）**：
```bash
do-bigdata wedata execute --file-path "Untitled.ipynb" --compute-id "xxx" --sequential --cell-timeout 300 --stuck-threshold 60
```
> 逐 Cell 模式会依次提交每个 Cell，独立监控执行状态和输出，Cell 长时间无新输出时自动告警。避免全量执行时一个 Cell 卡住导致整个 notebook 丢失进度。
```

**执行单个 cell（通过 cell_id 指定）**：
```bash
do-bigdata wedata execute --file-path "Untitled.ipynb" --compute-id "xxx" --cell-id "abc123" --wait
```

> **单 Cell 执行输出展示**：执行单个 cell 时（传入 `--cell-id`），状态查询接口 `/api/sessions/execute/<task_id>` 会在响应中返回该 cell 的完整内容。工具会自动提取并格式化该 cell 的 outputs（包括 stream、execute_result、display_data、error 等），**最多展示 500 行**，超出部分会被截断并提示。展示内容包含 ANSI 颜色码剥离后的 traceback，便于排查错误。

**查询执行状态**：
```bash
do-bigdata wedata execute-status --task-id "xxx"
```

> 若该 task 是单 Cell 执行任务，`execute-status` 的输出会包含 `cell` 字段，内含 `execution_count`、`has_error`、`output_count`、`output_text`（最多 500 行）等信息。

**可选参数**：
- `--cell-id`：指定只执行某个 cell 的 ID。不传则执行所有 code cell。cell_id 可通过 `read-notebook` 读取文件内容获取。

### 子技能三：代码诊断

用于获取 notebook 文件的完整诊断信息，包括 kernel 状态、文件内容（含 cell 执行结果和错误）、dashboard 链接、环境信息、依赖包状态等。

> **注意**：该接口（`/api/sessions/file-info`）不需要鉴权，通过 `user` 查询参数指定用户。脚本会自动从凭证配置中提取用户名并传递。

> **自动 Spark 深入诊断**：当诊断结果中 `dashboard.type` 为 `spark` 且 `dashboard.application_id` 不为空时，会自动调用 Spark 诊断子技能进行深入分析（异常类型、根因定位、解决方案），结果会附加在输出的 `spark_diagnosis` 字段中。

**获取诊断信息**：
```bash
do-bigdata wedata diagnose --path "Untitled.ipynb"
```

### 子技能四：Spark 诊断

用于通过 Spark application_id 调用 LLMAPP 平台的 AI 诊断服务，对 Spark 任务进行智能分析，返回异常类型、根因定位和解决方案。

**基本诊断**（自动使用最近7天日期）：
```bash
do-bigdata wedata spark-diagnose --app-id "application_1763433692922_60220230"
```

**指定日期范围**：
```bash
do-bigdata wedata spark-diagnose --app-id "application_1763433692922_60220230" --current-date "20260312"
```

**跨天任务**（任务从8号启动到10号结束）：
```bash
do-bigdata wedata spark-diagnose --app-id "application_1763433692922_60220230" --current-date "20260308,20260309,20260310"
```

**指定环境**（默认 dev，可选 staging/prod）：
```bash
do-bigdata wedata spark-diagnose --app-id "application_1763433692922_60220230" --env prod
```

**可选参数**：
- `--app-id`（必填）：Spark application ID，格式如 `application_xxxx_xxxx`
- `--current-date`：日期范围（YYYYMMDD 格式，多天用逗号分隔）。用于缩小日志抓取范围：
  - 不跨天：传当天日期即可，如 `20260312`
  - 跨天：传起止日期范围，如 `20260308,20260309,20260310`
  - 不传：自动使用最近7天的日期
- `--env`：LLMAPP 环境（dev/staging/prod），默认 dev
- `--verbose`：输出详细的思考过程

**诊断结果包含**：
- `app_id`: Spark application ID
- `session_id`: LLMAPP 会话 ID
- `has_error`: 是否有错误
- `diagnosis`: 诊断结果文本（包含异常类型、根因定位、解决方案）
- `knowledges`: 引用的知识库内容（如有）
- `error_msg`: 错误信息（如有）

### 子技能五：Compute 管理

用于查询、创建和更新计算资源（Compute）。**不支持删除操作**。

**查询 compute 列表**：
```bash
do-bigdata wedata list-computes
```

**按 runtime 类型过滤**：
```bash
do-bigdata wedata list-computes --runtime yarn
```

**按状态过滤**：
```bash
do-bigdata wedata list-computes --status healthy
```

**按名称过滤**：
```bash
do-bigdata wedata list-computes --name "my-compute"
```

**查询单个 compute 详情**：
```bash
do-bigdata wedata get-compute --compute-id "xxx-xxx-xxx-xxx-xxx"
```

**创建 compute**：
```bash
do-bigdata wedata create-compute --body '{"name":"my-compute","runtime":"python"}'
```

**更新 compute**：
```bash
do-bigdata wedata update-compute --compute-id "xxx-xxx-xxx-xxx-xxx" --body '{"name":"new-name"}'
```

**可选参数（list-computes）**：
- `--runtime`：按 runtime 类型过滤（yarn/python/ray/spark-k8s/flink-k8s）
- `--name`：按名称过滤
- `--status`：按状态过滤（healthy/starting/restarting/stopped 等）

**必填参数（get-compute / update-compute）**：
- `--compute-id`：Compute 的 ID

**必填参数（create-compute / update-compute）**：
- `--body`：请求体（JSON 字符串），包含 name, runtime, resource 等字段

**支持的 runtime 类型**：

| runtime | 显示名称 |
|---------|----------|
| `yarn` | PySpark(Yarn) |
| `python` | Python |
| `ray` | Ray |
| `spark-k8s` | PySpark（K8s）- beta |
| `flink-k8s` | PyFlink |

**compute 状态说明**：

| status | 说明 |
|--------|------|
| `healthy` | 运行中，可正常使用 |
| `starting` | 启动中 |
| `restarting` | 重启中 |
| `stopped` | 已停止 |
| `terminated` | 已终止（包含 exit_code 如 RECYCLED/DEAD/LAUNCH_TIMEOUT 等） |
| `error` | 异常 |

**compute 结构字段说明**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | string | Compute 唯一标识（UUID） |
| `name` | string | Compute 名称 |
| `user` | string | 所属用户（RTX） |
| `description` | string | 描述信息 |
| `runtime` | string | 运行时类型（yarn/python/ray/spark-k8s/flink-k8s） |
| `runtime_spec` | object | 运行时配置（不同 runtime 字段不同，见下方示例） |
| `resource` | object | 资源配置（driver + executor_group） |
| `resource.driver_cpu` | int | Driver CPU 核数 |
| `resource.driver_mem` | int | Driver 内存（MB） |
| `resource.driver_gpu` | int | Driver GPU 数量 |
| `resource.executor_group` | array | Executor 组配置列表（每组含 replicas/num_cpu/num_mem/num_gpu） |
| `env` | object | 环境变量（如 Ray 的 `RAY_DEFAULT_OBJECT_STORE_MEMORY_PROPORTION` 等） |
| `context` | object | 运行上下文（application_id、dashboard_url、exit_code 等） |
| `packages` | object | 已安装的依赖包（每个包含 name/version/status/message） |
| `active_kernels` | array | 当前活跃的 kernel ID 列表 |
| `status` | string | 当前状态 |
| `provisioned` | bool | 是否已分配资源 |
| `created_time` | string | 创建时间（ISO 8601） |
| `last_activity` | string | 最后活动时间 |
| `launch_timeout` | int | 启动超时时间（秒） |
| `cull_idle_timeout` | int | 空闲回收超时时间（秒） |

**各 runtime 类型的典型创建示例**：

**1. 创建 Python compute**：
```bash
do-bigdata wedata create-compute --body '{
  "name": "my_python_cluster",
  "runtime": "python",
  "runtime_spec": {
    "python_version": "3.10"
  },
  "resource": {
    "driver_cpu": 1,
    "driver_mem": 4096,
    "driver_gpu": 0,
    "executor_group": [
      {"replicas": 1, "num_cpu": 1, "num_mem": 4096, "num_gpu": 0}
    ]
  }
}'
```

**2. 创建 PySpark(Yarn) compute**：
```bash
do-bigdata wedata create-compute --body '{
  "name": "my_yarn_cluster",
  "runtime": "yarn",
  "runtime_spec": {
    "gaia_id": "14866",
    "group_id": "g_teg_tdwtest_1506907589461508096",
    "gaia_name": "TDW深汕麒麟座集群",
    "spark_version": "3.3",
    "python_version": "3.10",
    "cluster_id": "tl",
    "gaia_version": "3.2",
    "enable_dynamic_allocation": true,
    "supersql_url": "supersql-hn0-teg-migrplc.woa.com:10000"
  },
  "resource": {
    "driver_cpu": 2,
    "driver_mem": 4096,
    "driver_gpu": 0,
    "executor_group": [
      {"replicas": 2, "num_cpu": 4, "num_mem": 8192, "num_gpu": 0}
    ]
  }
}'
```

**3. 创建 Ray compute（纯 CPU）**：

> **重要**：Ray compute 必须配置 `runtime_spec`（含 provider、image 等）和 `resource.extra`（含 cpu_provider、override_config），否则创建后会立即变为 dead 状态。Head 节点内存最低 12GB。Worker 预装依赖通过 `override_config.job_config` 配置。

```bash
do-bigdata wedata create-compute --body '{
  "name": "my_ray_cluster",
  "runtime": "ray",
  "runtime_spec": {
    "provider": "ModelService",
    "ray_version": "2.51.1+0f31ba",
    "python_version": "python 3.12",
    "image": "mirrors.tencent.com/rayproject/ray:2.51.1-py312-cpu-0f31bac9-all",
    "dynamic_scheduling_config": {"dynamicSchedulingResourceQueue": {"private": {"enable": true}}},
    "driver_placement_group": {"num_cpu": 0, "index": -1},
    "autoscaler": {"idleTimeoutSeconds": 60},
    "override_config": {
      "cluster_config": {},
      "job_config": {
        "servingRayConfig": {
          "runtimeEnv": {"pip": {"packages": ["torch", "scikit-learn", "pandas", "numpy"], "pip_check": false}}
        }
      }
    }
  },
  "env": {"RAY_DEFAULT_OBJECT_STORE_MEMORY_PROPORTION": "0.5", "RAY_DEFAULT_OBJECT_STORE_MAX_MEMORY_BYTES": "2000000000000"},
  "resource": {
    "driver_cpu": 6, "driver_mem": 12288, "driver_gpu": 0,
    "extra": {
      "cpu_provider": {"namespace": "ray-test", "gaia_id": "15654", "cpu_type": "tdw", "enable_pod_affinity": false},
      "override_config": {"nodeSelector": {"set": "ray-tdw"}, "priorityClassName": "low-priority"}
    },
    "executor_group": [
      {"replicas": 2, "num_cpu": 4, "num_mem": 8192, "num_gpu": 0,
       "extra": {
         "cpu_provider": {"namespace": "ray-test", "gaia_id": "15654", "cpu_type": "tdw", "enable_pod_affinity": false},
         "override_config": {"nodeSelector": {"set": "ray-tdw"}, "priorityClassName": "low-priority"}
       }
      }
    ]
  }
}'
```

**3b. 创建 Ray compute（CPU + GPU 混合节点）**：
```bash
do-bigdata wedata create-compute --body '{
  "name": "my_ray_gpu_cluster",
  "runtime": "ray",
  "runtime_spec": {
    "provider": "ModelService",
    "ray_version": "2.51.1+0f31ba",
    "python_version": "python 3.12",
    "image": "mirrors.tencent.com/rayproject/ray:2.51.1-py312-cpu-0f31bac9-all",
    "taiji_app_group": "<应用组ID>",
    "taiji_app_group_location": "<地区>",
    "dynamic_scheduling_config": {"dynamicSchedulingResourceQueue": {"private": {"enable": true}}},
    "driver_placement_group": {"num_cpu": 0, "index": -1},
    "autoscaler": {"idleTimeoutSeconds": 60},
    "override_config": {
      "cluster_config": {},
      "job_config": {
        "servingRayConfig": {
          "runtimeEnv": {"pip": {"packages": ["torch", "scikit-learn", "pandas", "numpy"], "pip_check": false}}
        }
      }
    }
  },
  "env": {"RAY_DEFAULT_OBJECT_STORE_MEMORY_PROPORTION": "0.5", "RAY_DEFAULT_OBJECT_STORE_MAX_MEMORY_BYTES": "2000000000000"},
  "resource": {
    "driver_cpu": 6, "driver_mem": 12288, "driver_gpu": 0,
    "extra": {
      "cpu_provider": {"namespace": "ray-test", "gaia_id": "15654", "cpu_type": "tdw", "enable_pod_affinity": false},
      "override_config": {"nodeSelector": {"set": "ray-tdw"}, "priorityClassName": "low-priority"}
    },
    "executor_group": [
      {"replicas": 2, "num_cpu": 4, "num_mem": 8192, "num_gpu": 0,
       "extra": {
         "cpu_provider": {"namespace": "ray-test", "gaia_id": "15654", "cpu_type": "tdw", "enable_pod_affinity": false},
         "override_config": {"nodeSelector": {"set": "ray-tdw"}, "priorityClassName": "low-priority"}
       }
      },
      {"replicas": 1, "num_cpu": 2, "num_mem": 8192, "num_gpu": 1,
       "extra": {
         "gpu_provider": {
           "taiji": {
             "app_group_name": "<应用组ID>", "cluster_type": 1, "gpu_type": "<GPU型号>",
             "owners": "null", "enable_node_cpu": false, "app_group_location": "<地区>",
             "dynamic_scheduling_config": {"dynamicSchedulingResourceQueue": {"private": {"enable": true}}}
           }
         }
       }
      }
    ]
  }
}'
```

**4. 创建 PySpark(K8s) compute**：
```bash
do-bigdata wedata create-compute --body '{
  "name": "my_k8s_spark_cluster",
  "runtime": "spark-k8s",
  "runtime_spec": {
    "gaia_id": "16613",
    "group_id": "g_teg_tdwtest_1506907589461508096",
    "gaia_name": "fengluan-sw0-teg-common-spark-1",
    "spark_version": "3.3",
    "python_version": "3.10",
    "cluster_id": "tl",
    "gaia_version": "2.8",
    "enable_dynamic_allocation": true,
    "namespace": "fengluan-34422-offline",
    "supersql_url": "supersql-hn0-teg-migrplc.woa.com:10000"
  },
  "resource": {
    "driver_cpu": 2,
    "driver_mem": 4096,
    "driver_gpu": 0,
    "executor_group": [
      {"replicas": 2, "num_cpu": 4, "num_mem": 8192, "num_gpu": 0}
    ]
  }
}'
```

**典型更新示例**：

**修改 compute 名称和资源配置**：
```bash
do-bigdata wedata update-compute --compute-id "69a5819f-7cad-4815-8346-b1fc07317b41" --body '{
  "name": "updated_compute_name",
  "resource": {
    "driver_cpu": 4,
    "driver_mem": 8192,
    "executor_group": [
      {"replicas": 4, "num_cpu": 8, "num_mem": 16384, "num_gpu": 0}
    ]
  }
}'
```

**修改 compute 环境变量**：
```bash
do-bigdata wedata update-compute --compute-id "a582c5c2-af22-482b-8f49-d19da4d6b034" --body '{
  "env": {
    "RAY_DEFAULT_OBJECT_STORE_MEMORY_PROPORTION": "0.7"
  }
}'
```

**各 runtime 的 runtime_spec 关键字段**：

| runtime | 关键字段 | 说明 |
|---------|----------|------|
| `yarn` | `gaia_id`, `group_id`, `gaia_name`, `spark_version`, `python_version`, `cluster_id`, `gaia_version`, `enable_dynamic_allocation`, `supersql_url` | TDW Gaia 集群配置 |
| `python` | `python_version` | Python 版本（如 "3.10"） |
| `ray` | `provider`, `ray_version`, `python_version`, `image`, `taiji_app_group` | Ray 集群配置（ModelService 模式含更多字段） |
| `spark-k8s` | 同 `yarn` + `namespace` | K8s 上的 Spark，额外需要 namespace |
| `flink-k8s` | 类似 `spark-k8s` | K8s 上的 Flink |

### 子技能六：存储交互

用于在 PySpark 引擎的 Notebook 中对 Ceph 进行读写操作。读取 notebook 文件，在文件中增加一个包含 hadoop fs 命令的 code cell，并保存文件。

**Ceph URI 格式**：
```
ceph://group_id@cluster_id/path
```
- `ceph` — 协议说明
- `group_id` — Ceph 多租户下的应用组 ID
- `cluster_id` — 集群信息
- 示例：`ceph://share_xxxxxxx@apdcephfs_xxxx/`

**列出 Ceph 路径下的文件**：
```bash
do-bigdata wedata add-storage-cell --path "Untitled.ipynb" --operation ls --ceph-uri "ceph://share_xxxxx@apdcephfs_xxx/"
```

**上传文件到 Ceph**：
```bash
do-bigdata wedata add-storage-cell --path "Untitled.ipynb" --operation put --ceph-uri "ceph://share_xxxxx@apdcephfs_xxx/tmp" --local-file "text.txt"
```

**从 Ceph 下载文件**：
```bash
do-bigdata wedata add-storage-cell --path "Untitled.ipynb" --operation get --ceph-uri "ceph://share_xxxxx@apdcephfs_xxx/tmp/text.txt"
```

**创建 Ceph 目录**：
```bash
do-bigdata wedata add-storage-cell --path "Untitled.ipynb" --operation mkdir --ceph-uri "ceph://share_xxxxx@apdcephfs_xxx/new_dir"
```

**查看 Ceph 文件内容**：
```bash
do-bigdata wedata add-storage-cell --path "Untitled.ipynb" --operation cat --ceph-uri "ceph://share_xxxxx@apdcephfs_xxx/tmp/text.txt"
```

**上传变量到 Ceph（先保存到本地再上传）**：
```bash
do-bigdata wedata add-storage-cell --path "Untitled.ipynb" --operation put-variable --ceph-uri "ceph://share_xxxxx@apdcephfs_xxx/yuruiyang" --variable-name "data_df"
```

**上传变量到 Ceph（指定 CSV 格式）**：
```bash
do-bigdata wedata add-storage-cell --path "Untitled.ipynb" --operation put-variable --ceph-uri "ceph://share_xxxxx@apdcephfs_xxx/yuruiyang" --variable-name "data_df" --file-format csv
```

**上传变量到 Ceph（通过 HDFS 中转，适用于大数据量 Spark DataFrame）**：
```bash
do-bigdata wedata add-storage-cell --path "Untitled.ipynb" --operation put-variable --ceph-uri "ceph://share_xxxxx@apdcephfs_xxx/yuruiyang" --variable-name "data_df" --hdfs-uri "hdfs://mycluster/tmp/staging"
```

> 指定 `--hdfs-uri` 后，Spark DataFrame 会直接通过 `DataFrame.write` 写入 HDFS，然后通过 `hadoop fs -cp` 复制到 Ceph，避免 `toPandas()` 导致的 Driver 内存不足问题。完成后会自动清理 HDFS 中间文件。

**可选参数**：
- `--no-impl`：不添加 `fs.ceph.impl` 配置（默认会自动添加 `fs.ceph.impl=org.apache.hadoop.fs.ceph.CephFileSystem`，仅 Ceph 协议有效）
- `--recursive`：递归操作（ls 可用）
- `--comment`：自定义 cell 注释
- `--insert-index`：指定 cell 插入位置（默认追加到末尾）
- `--variable-name`：变量名（put-variable 操作时必填，将变量先保存到本地再上传到存储）
- `--file-format`：变量保存格式（parquet/csv/pickle，默认 parquet，put-variable 操作时有效）
- `--hdfs-uri`：HDFS 中间存储 URI（put-variable 操作时可选）。指定后变量将先写入 HDFS 再 cp 到 Ceph，适用于大数据量 Spark DataFrame 场景，避免 toPandas() 导致内存不足

**诊断信息包含**：
- `kernel`: 内核信息（id, name, execution_state, reason）
- `file`: 文件信息（cells 摘要，包含每个 cell 的执行状态和错误信息）
- `dashboard`: 监控面板（Spark/Ray dashboard URL）
- `environment`: 运行环境（runtime, python_version, resource 配置）
- `packages`: 依赖包状态（安装中/已安装/失败）

### 子技能七：Oncall 通知

当 skill 和用户都无法解决某个问题时，向对应板块的负责人升级。提供两个原子操作：

- `send-alert`：**向负责人单向推送告警**。满足下方「升级条件」时 AI 可直接调用。
- `create-group-chat`：**拉 oncall 群，把用户和负责人拉到一起**。[WARN] **必须先征得用户口头同意**，不得擅自调用。

> [WARN] **强制红线：写 `question` / `text` 临时文件时，必须直接用文件编辑工具写入**（如你的 edit_file / write 类工具），
> **禁止通过 shell 命令行** （如 `echo "..." > x.txt`、`cat <<EOF`、`printf`） 写入长文本。原因：
> question 内容经常超过 shell 的 `ARG_MAX` 或包含特殊字符（反引号、美元符、换行、中文、emoji 等），
> shell 可能静默截断或解析失败，**结果是文件看似写入但实际为空或内容损坏，后续命令静默失败**。用文件编辑工具直写可避开所有转义问题。

#### 重要定位

Notebook 的执行链路很长（用户代码 → Kernel → Compute → Yarn/K8s → Spark → 存储 → 网络 → ……），skill **无法精确判定问题根因**属于哪一层。因此：

- `field` **只用于把问题路由到对应板块的负责人**，不代表 skill 断定"就是这一层的锅"。
- 根因由负责人接手后去定位，skill 只需按"**症状最明显的板块**"选 field。
- 绝不因为"skill 猜不出是不是基础设施问题"而犹豫——判断标准只看下面三条升级条件。

#### 升级条件（三条同时满足才升级）

1. **skill 修不了**：skill 已经按常识尝试过，仍然无效（详见下表"skill 应先尝试"列）
2. **用户也搞不定**：常规操作（改代码、换参数、重启 kernel、换资源等）无效，或用户明确表达「搞不定 / 卡住 / 帮我叫负责人」
3. **影响用户体验**：不是可忽略的 warning，而是让用户跑不动、跑不顺的问题（即便是随手实验也算——用户跑得舒服是平台的底线）

> 三条都满足才升级。**任一不满足都不要升级**——宁可少报也不要打扰负责人。

#### field 选择表（按症状最明显的板块路由）

| field | 症状表现（观测信号） | skill 应先尝试 | 尝试无效后再考虑升级 |
|---|---|---|---|
| `kernel` | Kernel dead/unknown、reason 含 killed/oom | 重启 kernel、换个 compute 试试 | 连续 ≥2 次同样 dead |
| `compute` | Compute/Yarn/K8s status=error/terminated、创建失败 | 换资源规格、稍后重试 | 换规格后仍失败 |
| `spark` | Spark 作业失败 | 先跑 `spark-diagnose` 看有无修复建议 | 无建议或建议指向集群侧 |
| `storage` | Ceph/HDFS 读写异常、权限报错 | 核对 URI、换路径、检查配置 | 配置正确仍失败 |
| `platform` | Server/Gateway/鉴权/路由异常 | 刷新凭证、换端点重试 | 多次尝试仍异常 |
| `other` | 以上都不是、症状跨层或不清晰 | 按常识尝试常见修复 | 仍无头绪，交平台侧分流 |

> 上表"skill 应先尝试"仅为典型示例，不是穷举；LLM 应按当时的上下文灵活判断，但**必须先尝试**、**不要跳过这一步直接升级**。
>
> **多个板块都像时的消歧义规则**：优先选**更靠近报错源头**的那个板块。报错源头 = 触发异常的最底层组件。
> 例如 Spark 作业因拿不到 compute 资源而失败 → 报错源头是 compute 拉不起来，选 `compute`；
> Spark 正常拿到资源后 executor lost → 报错源头在 Spark 运行时，选 `spark`。
> 链路定位实在不清晰时，选 `other` 交由平台侧分流，**不要硬猜**。

#### skill 自己该修、不得升级的情况（红线）

以下情况属于 skill 正常工作范畴，**绝对不要**升级：

- [FAIL] 用户代码的语法错误、`NameError`、`KeyError`、`TypeError` 等逻辑错误
- [FAIL] `ImportError` / `ModuleNotFoundError`：**提示用户缺少哪个包、建议其安装**（skill 无权擅自 `pip install`，kernel 环境不一定匹配用户期望的环境）
- [FAIL] 用户传入的参数、文件路径、URI 笔误
- [FAIL] 依赖包版本不匹配、环境未激活等（应先引导用户修正）
- [FAIL] 未经用户同意拉群
- [FAIL] `field` 使用枚举外的值（脚本会直接报错）

#### 行动流程

1. 命中升级条件后，**立即调 `send-alert`**（无需征求同意，这是单向通知，脚本会自动按 1 小时去重）。调用前告知用户「已向 `<field>` 负责人上报」。
2. 若 5 分钟后仍无进展，或用户表达「搞不定 / 卡住 / 帮我联系负责人」，**用一句话征求同意后**再调 `create-group-chat`。用户未明确同意时不得拉群。

#### `text` 模板（alert 正文，服务端原文转发）

3 行，保持精简（企微告警消息越短越好读）：

```
【告警】<field> - <一句话症状，≤30字>
- 关键线索: <从下面「关键线索可选字段」挑具体有的值拼起来，逗号分隔>
- 根因推断: <skill 已得出的技术判断，不超过一行>
```

**关键线索字段（按当时诊断结果填入存在的字段，没有就略去，不要编造）**：

- 文件路径 / kernel_id / kernel_state / kernel_reason
- compute_id / runtime / compute_status / exit_code
- session_id / task_id
- Spark application_id / Spark dashboard_url / Spark spark_session_id (LLMAPP 会话)
- Ray dashboard_url
- 首错 cell idx / ename / evalue 前 100 字
- 任何其他 skill 认为对负责人定位有帮助的字段（如 trace_id / request_id / yarn_app_id / namespace 等，上面没列但确实出现在诊断输出里的都应当加上）

> AI 不要写「触发人」行，脚本会自动从 CMK 注入。

#### `question` 模板（group-chat 详情，群内首条消息）

**三段**（服务端已自动在头部拼接「问题类型 / 发起人 / 摘要」，AI 不要重复）：

```
【结论与根因推断】
<一句话故障画像>
<一句话 skill 为什么搞不定>

【关键技术线索】
<按以下可选字段按顺序填写；有就写上，没有就略去该行，不要编造>
- 文件: <file_path>
- 计算资源: <compute_id> (runtime=<runtime>, status=<status>, exit_code=<exit_code>)
- Session: <session_id>
- Task: <task_id>
- Kernel: <kernel_id> state=<state> reason=<reason>
- Spark AppID: <application_id>
- Spark Dashboard: <dashboard_url>
- Spark 诊断会话: <spark_session_id>   # LLMAPP 会话，可反查诊断过程
- Ray Dashboard: <ray_dashboard_url>
- 首错 Cell: [idx=<i>] <ename>: <evalue 前 200 字>
- 依赖包异常: <有哪些包状态是 failed / 安装中>
- 时间: <YYYY-MM-DD HH:MM:SS>
- 其他有价值的字段: <trace_id / request_id / yarn_app_id / namespace / …——
  模板未列但确实出现在本次诊断输出中的关键字段，也应当主动列上>

【已尝试的方案】
1. <skill 尝试过什么，结果如何，比如"重启 kernel 2 次均 dead"、"换 compute 也失败"——让负责人不走回头路>
2. ...
```

> **字段普遍原则**：模板列出的是目前可能出现的常见字段，不是穷举。**有就写上，没有就略去该行，不要编造字段值**。
> 如果诊断输出里出现了模板未列的关键字段（如以后新增的 trace_id），也应当写进「其他有价值的字段」一行。

#### 参数细节

- **`--abstract`**（仅 `create-group-chat`）：必填，≤ 30 字符，会被服务端拼进企微群名 `[nb oncall]<user>-<abstract>`。应用一句话概括问题（例：「PySpark kernel 连续 dead」），让负责人从群名就能一眼识别群。空或超长脚本直接报错。
- **`--question-file`** / **`--text-file`**：AI 应把模板 **直接用文件编辑工具写入** `security_file/.notify_<field>_<timestamp>.txt`，**不得用 shell 命令写入**（见上方红线）；再把文件路径传给脚本，并加 `--delete-question-file` / `--delete-text-file` 让脚本在发送后清理。
- **`--location-id`**：去重粒度键，优先填 `application_id` > `compute_id` > `file_path`；不填则退化为「user + field 级」去重
- **去重**：脚本按 `user + action + field + location_id` 自动在 **1 小时内**去重；命中返回 `status=skipped`，这不是失败，原操作继续
- **`--force`**（`send-alert` / `create-group-chat` 都支持）：跳过 1 小时去重。[WARN] **仅在用户明确表达「再发一次 / 再拉一次」时才能使用**，不得默认加上，也不得因为 skill 自身觉得「上一次没人理」就自主加上
- **失败不阻塞**：通知失败时脚本返回 `status=failed` 但 exit 0，**不会打断主诊断流程**，AI 应告知用户并继续其他尝试

#### 命令示例

> 前提：`security_file/.notify_<field>_<ts>.txt` 此时已通过文件编辑工具写入了模板内容（见上方红线）。

```bash
# 告警
do-bigdata wedata send-alert --field kernel \
  --text-file security_file/.notify_kernel_<ts>.txt --delete-text-file \
  --location-id <compute_id>

# 拉群（先征得同意！）
do-bigdata wedata create-group-chat --field spark \
  --abstract "Spark作业因集群故障持续失败" \
  --question-file security_file/.notify_spark_<ts>.txt --delete-question-file \
  --location-id <application_id>

# 强制重发告警（仅在用户明确要求「再发一次」时使用）
do-bigdata wedata send-alert --field kernel \
  --text-file security_file/.notify_kernel_<ts>.txt --delete-text-file \
  --location-id <compute_id> --force

# 强制重拉新群（仅在用户明确表示「原群无人回 / 请再拉一次」时使用；需再次征得用户同意）
do-bigdata wedata create-group-chat --field spark \
  --abstract "Spark作业持续失败（重拉）" \
  --question-file security_file/.notify_spark_<ts2>.txt --delete-question-file \
  --location-id <application_id> --force
```


### 子技能八：iWiki 文档查询

用于回答 Notebook **产品用法 / FAQ / 实践案例 / 版本更新**类问题。本子技能**只做两件事**：

1. 把 Notebook 官方 iWiki 目录结构化成索引（`references/notebook_iwiki_index.json`，共 55 条）；
2. 提供一个 uv 脚本 `scripts/search_iwiki_ref.py`，按**关键词 / 分类 / 二级模块**在索引里快速缩出 3~10 条候选 URL。

> 正文抓取不在本子技能范围内——拿到候选 URL 后，**务必通过 iWiki MCP 读原文**，再结合原文回答用户问题，严禁凭记忆 / 猜测编造 Notebook 产品行为。

#### 何时触发

**[OK] 触发场景**：
- 用户咨询 Notebook **产品功能 / 使用手册**（协作区、VSCode 版、AI Coding、ADA 助手、SQL on Notebook、文件管理、Git）。
- 用户问 **资源 / 环境 / 依赖包**（Pyspark on k8s 自定义镜像、Yarn Python 包推荐、资源释放策略、资源模板分享、太极 Python 环境迁移）。
- 用户问 **模板 / Pipeline / NotebookRunner 调度**。
- 用户问 **实践案例 / Demo**（Iceberg、Lance、Ray kernel、AI Function、PySpark Dashboard、因果推断、AutoDS、公共数据集）。
- 用户问 **FAQ / 技术支持**（Ceph 读取、PySpark 第三方包兼容版本、数据管道知识、通用排障）。
- 用户问 **版本更新 / 太极 → WeData 迁移**。

**[NO] 不触发场景**（应走本 skill 的其他子技能）：
- 要**创建 / 执行 / 调试**具体 notebook 任务 → 走子技能一~六（代码编辑 / 运行 / 诊断 / 存储 / Spark 诊断 / Compute 管理）。
- 问题需要升级给 oncall 负责人 → 走子技能七。
- 用户明确要求"不查文档，就按你知道的讲" → 尊重用户，跳过本子技能。

#### 工作流（三步）

```
Step 1  本地缩候选
  └─ do-bigdata wedata search-iwiki --keywords "..."
                 │
                 ▼
Step 2  iWiki MCP 抓正文
  └─ 对 Top 1~3 条 url 调 iWiki MCP（read_page / 正文检索等）
                 │
                 ▼
Step 3  基于原文回答
  └─ 回答时在句尾附 iWiki 链接（Markdown [title](url) 形式）
```

**Step 1 · 本地缩候选**

脚本 **只读本地 JSON，不访问网络**，成本极低，每次回答前都应跑一次。

```bash
# 关键词召回（推荐从这里开始，空格分隔多关键词）
do-bigdata wedata search-iwiki --keywords "Ray GPU" --top-k 5

# 叠加一级分类过滤：产品功能 / 实践案例 / 版本更新 / NotebookFAQ
do-bigdata wedata search-iwiki --category NotebookFAQ --keywords "PySpark 包 兼容"

# 只过滤二级模块（子串匹配，方便写简称）
do-bigdata wedata search-iwiki --module "AI Coding" --top-k 10

# 兜底：列出当前过滤条件下的全部条目
do-bigdata wedata search-iwiki --list-all --category 实践案例
```

输出（JSON）：

```json
{
  "query":   {"keywords": ["Ray", "GPU"], "category": null, "module": null, "top_k": 5},
  "total":   2,
  "results": [
    {"id": 38, "category": "实践案例", "module": "快速入门Demo", "submodule": "Ray kernel",
     "title": "Ray分布式计算入门", "url": "https://iwiki.woa.com/p/4012242425", "score": 1}
  ],
  "hint": "请将 results[*].url 作为输入交给 iwiki MCP 抓取正文；..."
}
```

**关键词选词技巧**：
- 先用**用户原话里的核心名词**（如 "协作区"、"PySpark on yarn"、"Ray kernel"、"Iceberg"）。
- 命中为 0 时，换更宽泛 / 同义词（"资源" / "计算资源"；"迁移" / "太极"；"调度" / "Runner"）。
- 遇到 FAQ 类问题，先试 `--category NotebookFAQ` 叠加关键词。

**Step 2 · iWiki MCP 抓正文**

> [WARN] 本子技能**不提供抓取脚本**，严禁用 `curl` / `requests` 等方式直接抓 `iwiki.woa.com`（需鉴权且政策受限）。

正确做法：
- 拿到候选 URL（一般取 Top 1~3 条，信息不足再补）后，**调 iWiki MCP** 读原文。
- 抓回正文后，**用原文回答用户**，并在引用段落后以 Markdown 链接附上来源页。
- 如 iWiki MCP 不可用，如实告知用户："相关文档见 [xxx](url)，我暂时无法抓取正文，建议你直接打开链接。"严禁编造内容。

**Step 3 · 基于原文回答**

- **逐条核对**：用户的子问题必须能在原文里找到依据；找不到就说"该问题未在该文档覆盖，建议咨询 Notebook 产品支持"。
- **链接格式**：`[V2版本Git操作](https://iwiki.woa.com/p/4016256440)`——不要裸贴 URL。
- **多文档互补**：遇到"怎么把太极 Notebook 迁移到 WeData 并装自定义 Python 环境"这种跨文档问题，分别抓 id=7 与 id=19，综合回答。

#### iWiki 索引速览

> 回答前**无需**把下表完整读进上下文；先跑 `search_iwiki_ref.py` 缩候选，再按需要查此表。本表主要用于"没跑脚本时人工核对 id / URL"的场景。权威来源是 `references/notebook_iwiki_index.json`。

**1. 产品功能（id 1~32）**

| id | 二级模块 | 三级子模块 | 标题 | iwiki |
|----|----------|------------|------|-------|
| 1  | — | — | Notebook 核心功能文档总览 | https://iwiki.woa.com/p/4013087181 |
| 2  | 产品介绍&首次使用 | — | 产品入门引导 | https://iwiki.woa.com/p/4013084698 |
| 3  | 产品介绍&首次使用 | 新版本Notebook简介&功能比对 | 新旧版本功能对比说明 | https://iwiki.woa.com/p/4015376295 |
| 4  | 产品介绍&首次使用 | 概念说明 | Notebook 核心概念解释 | https://iwiki.woa.com/p/4015853968 |
| 5  | Notebook使用手册 | — | 日常使用操作指南 | https://iwiki.woa.com/p/4013095576 |
| 6  | Notebook使用手册 | 【协作区】使用说明 | 通过协作区进行项目协作 | https://iwiki.woa.com/p/4016112360 |
| 7  | Notebook使用手册 | 太极Notebook->WeData Notebook使用说明 | 从太极迁移到 WeData 的指南 | https://iwiki.woa.com/p/4016270316 |
| 8  | Notebook使用手册 | VSCode版本使用说明 | VSCode 集成使用方法 | https://iwiki.woa.com/p/4019618281 |
| 9  | Notebook AI Coding | — | AI 辅助编码功能 | https://iwiki.woa.com/p/4016248575 |
| 10 | Notebook AI Coding | 【AI Coding】代码生成 | AI 自动生成代码 | https://iwiki.woa.com/p/4015215899 |
| 11 | Notebook AI Coding | 【AI Coding】智能补全 | AI 代码智能补全 | https://iwiki.woa.com/p/4016236024 |
| 12 | Notebook AI Coding | NoteBook ADA代码助手 | ADA 代码助手使用说明 | https://iwiki.woa.com/p/4012242423 |
| 13 | 【Notebook资源】使用说明 | — | 计算资源配置与管理 | https://iwiki.woa.com/p/4011936011 |
| 14 | 【Notebook资源】使用说明 | 如何通过配置释放策略提升资源利用率 | 资源优化策略 | https://iwiki.woa.com/p/4017699266 |
| 15 | 【Notebook资源】使用说明 | 资源模板/分享给他人使用 | 资源模板共享 | https://iwiki.woa.com/p/4018263339 |
| 16 | 【基础环境/依赖包管理】使用说明 | — | Python 环境与包管理 | https://iwiki.woa.com/p/4013056353 |
| 17 | 【基础环境/依赖包管理】使用说明 | 【Pyspark on k8s自定义镜像】 | K8s 环境自定义镜像 | https://iwiki.woa.com/p/4018704249 |
| 18 | 【基础环境/依赖包管理】使用说明 | 【Pyspark on yarn Python包推荐】 | Yarn 环境推荐包列表 | https://iwiki.woa.com/p/4019505051 |
| 19 | 【基础环境/依赖包管理】使用说明 | 【Pyspark自定义Python环境/Taiji迁移】 | 自定义环境配置与迁移 | https://iwiki.woa.com/p/4017166563 |
| 20 | 【文件管理】使用说明 | — | 文件管理操作指南 | https://iwiki.woa.com/p/4013087179 |
| 21 | 【文件管理】使用说明 | 数据下载 | 文件/数据下载方法 | https://iwiki.woa.com/p/4013840660 |
| 22 | 【SQL on Notebook】使用说明 | — | 在 Notebook 中使用 SQL | https://iwiki.woa.com/p/4013071522 |
| 23 | 【通过模板快速构建任务】使用说明 | — | 模板化创建任务 | https://iwiki.woa.com/p/4016225525 |
| 24 | 【通过模板快速构建工作流Pipeline】使用说明 | — | 模板化构建工作流 | https://iwiki.woa.com/p/4016676483 |
| 25 | 【一键转NotebookRunner调度】使用说明 | — | Notebook 转定时调度任务 | https://iwiki.woa.com/p/4012177212 |
| 26 | 【Git】使用说明 | — | Git 版本控制 | https://iwiki.woa.com/p/4016259362 |
| 27 | 【Git】使用说明 | 【Git】On NotebookV2 | V2 版本 Git 操作 | https://iwiki.woa.com/p/4016256440 |
| 28 | 【Git】使用说明 | 【Git】On NotebookV1 | V1 版本 Git 操作 | https://iwiki.woa.com/p/4013936970 |
| 29 | 【Git】使用说明 | 【fs/git操作】通过命令执行操作 | 命令行 Git / 文件操作 | https://iwiki.woa.com/p/4018939460 |
| 30 | 附录 | — | 补充参考信息 | https://iwiki.woa.com/p/4013840659 |
| 31 | 附录 | NotebookSpark集群支持登记 | Spark 集群接入登记 | https://iwiki.woa.com/p/4015336823 |
| 32 | 附录 | 太极Notebook镜像依赖的包清单 | 镜像包依赖列表 | https://iwiki.woa.com/p/4016333918 |

**2. 实践案例（id 33~46）**

| id | 二级模块 | 三级子模块 | 标题 | iwiki |
|----|----------|------------|------|-------|
| 33 | — | — | 实际使用 Demo 与解决方案 | https://iwiki.woa.com/p/4015827909 |
| 34 | 快速入门 Demo | — | 快速上手演示 | https://iwiki.woa.com/p/4012242421 |
| 35 | 快速入门 Demo | PySpark on Yarn | Yarn 模式 PySpark 入门 | https://iwiki.woa.com/p/4012242424 |
| 36 | 快速入门 Demo | Pyspark 访问 Iceberg 表 | Iceberg 表读写操作 | https://iwiki.woa.com/p/4016227684 |
| 37 | 快速入门 Demo | Pyspark 访问 Lance 表 | Lance 表读写操作 | https://iwiki.woa.com/p/4016232826 |
| 38 | 快速入门 Demo | Ray kernel | Ray 分布式计算入门 | https://iwiki.woa.com/p/4012242425 |
| 39 | 快速入门 Demo | AI Function | AI 函数使用示例 | https://iwiki.woa.com/p/4014541045 |
| 40 | 快速入门 Demo | PySpark Dashboard 使用说明 | PySpark 可视化面板 | https://iwiki.woa.com/p/4016685365 |
| 41 | 场景解决方案 DEMO | — | 典型业务场景方案 | https://iwiki.woa.com/p/4013090385 |
| 42 | 场景解决方案 DEMO | Pyspark 的分布式机器学习 | 分布式 ML 训练方案 | https://iwiki.woa.com/p/4012842047 |
| 43 | 场景解决方案 DEMO | Notebook 因果推断 | 因果推断分析案例 | https://iwiki.woa.com/p/4012973385 |
| 44 | 场景解决方案 DEMO | SiriusAutoDS 模型参数调优 | AutoML 调参方案 | https://iwiki.woa.com/p/4013124752 |
| 45 | 场景解决方案 DEMO | 公共数据集 | 可用公共数据集一览 | https://iwiki.woa.com/p/4013104449 |
| 46 | 场景解决方案 DEMO | 不同特性数据的最佳处理实践 | 数据处理最佳实践 | https://iwiki.woa.com/p/4015842665 |

**3. 版本更新（id 47）**

| id | 标题 | iwiki |
|----|------|-------|
| 47 | Notebook 功能迭代与更新记录 | https://iwiki.woa.com/p/4013356257 |

**4. NotebookFAQ（id 48~55）**

| id | 二级模块 | 标题 | iwiki |
|----|----------|------|-------|
| 48 | — | 常见问题与技术支持 | https://iwiki.woa.com/p/4015827915 |
| 49 | Notebook 常见问题 | 高频问题汇总 | https://iwiki.woa.com/p/4012308928 |
| 50 | Notebook 技术支持文档 | 技术支持与排障指南 | https://iwiki.woa.com/p/4014929872 |
| 51 | Notebook 中通过 PySpark（Yarn）读取 ceph | Ceph 存储读取方法 | https://iwiki.woa.com/p/4016144734 |
| 52 | 数据管道知识 | 数据管道相关知识 | https://iwiki.woa.com/p/4017177234 |
| 53 | 实践案例 | FAQ 相关实践案例 | https://iwiki.woa.com/p/4017181682 |
| 54 | 产品功能 | FAQ 相关产品功能文档 | https://iwiki.woa.com/p/4017181733 |
| 55 | Notebook Pyspark 第三方包兼容版本一览表 | PySpark 包版本兼容清单 | https://iwiki.woa.com/p/4018101843 |

#### 反模式（禁止）

- [FAIL] 拿到候选 URL 后**不调 iWiki MCP**，凭印象 / 训练数据直接回答 Notebook 产品行为——随时可能过时或错位。
- [FAIL] 用 `requests` / `urllib` / `curl` 等方式绕过 iWiki MCP 直接抓 `iwiki.woa.com`。
- [FAIL] 一次性把 55 条全读给用户；应先缩候选，再按需抓 1~3 条。

#### 索引维护

- 权威来源：`references/notebook_iwiki_index.json`；本 SKILL.md 的速览表是镜像。
- 产品组新增 iWiki 文档时：往 JSON `docs` 数组里追加一条（保持 id 单调递增、url 唯一），然后同步更新上面对应分类的速览表。



### 子技能九：Agent Diff 审阅（v2 / cell metadata 内嵌方案）

让 agent 修改 notebook 时给用户一份"可审阅、可回滚"的修改建议——`save-notebook --with-diff` 会先 GET 当前 nb 作为 base，**在客户端**算 cell-level diff、给变化的 cell 注入 `metadata.agent_diff = {action, base_source}`，再 PUT 到远端；前端识别这个字段后会进入 review 视图，让用户**逐 cell** accept / reject。

> 协议参考：[iWiki 4020552703](https://iwiki.woa.com/p/4020552703)。

#### 核心设计：审阅与执行解耦（v2 原意）

类似 Cursor / Windsurf 等 AI coding 工具的体感——agent 改完即可继续工作流，**用户的 review 是异步的、不阻塞 agent**：

```
agent save-notebook --with-diff
   ↓
文件物理上已是 target（PUT 已落盘）
   ↓
agent 可以立刻继续 → execute / diagnose / 下一轮编辑 ...（不需要等用户）
                            │
                            ▼
        （并行）用户随时去前端 review，逐 cell accept / reject
                            │
                            ▼
        前端调 5 个后端接口清理 metadata.agent_diff
```

**为什么这样设计**：
- 文件保存后**物理上已经是 agent 改后的 target**，execute 跑的就是新代码——天然合理
- accept 只是"删掉 metadata.agent_diff 字段"；reject 才是"把 source 回滚到 base_source"
- 即使用户最后 reject，agent 在中间跑过的执行结果也是基于"agent 想要的新代码"，结果有价值
- 不打断 agent 的多轮自动修复循环（edit-run-diagnose 场景关键）

#### v2 协议核心

cell.metadata.agent_diff 字段语义：

| `action` | cell 的 `source` 字段 | `base_source` |
|----------|----------------------|---------------|
| `modified` | 改动后的新代码 | 改动前的原代码（必填）|
| `added` | 新增的代码 | 可省略 |
| `removed` | **保持原代码不变**（agent **不删** cell，只标记） | 与 source 同（脚本会自动填）|

#### 何时触发本子技能

**默认触发**：所有"agent 通过 `save-notebook` 写 notebook 内容"的场景，无论修改还是新建，一律加 `--with-diff`：

- [OK] `save-notebook` 修改已有 notebook（与远端 base 做 cell-level diff，仅变化 cell 标记 `modified` / `added` / `removed`）
- [OK] `save-notebook` 新建 notebook（远端无 base，全部 cell 标为 `added`，每个 cell 都进入 review）
- [OK] `edit-run-diagnose` 自动修复循环里每一轮的"保存修改"
- [OK] `add-storage-cell` 追加 hadoop fs 命令 cell

**不触发本子技能**：

- [FAIL] `read-notebook` / `download-file`（只读，不改）
- [FAIL] `create-notebook`（仅创建空文件占位，不写业务 cell；后续往里写 cell 时改用 `save-notebook --with-diff`）
- [FAIL] `upload-file`（上传新数据文件，不是写 notebook 内容）
- [FAIL] `rename-path`（仅改路径不改 content）
- [FAIL] 用户**明确**说"直接改、别走 diff"——尊重用户意愿，但要在回复里告知"已跳过 diff review，本次直接覆盖/写入"

#### 两步工作流（agent 视角）

```
Step 1  改完一气呵成 PUT
  └─ do-bigdata wedata save-notebook \
        --path "demo.ipynb" \
        --content '<完整目标 nb JSON>' \
        --with-diff
                  │
                  ▼
Step 2  告知用户：修改已生效，可继续；review 可异步进行
  └─ stdout 末尾会含 review_hint 字段，照原文转告即可，例如：
       "已为 demo.ipynb 提交 N 处 cell-level 修改并保存。
        你可以随时去 notebook 前端逐 cell accept / reject 这次修改。
        我会继续后续工作（不会等待 review 完成）。"
                  │
                  ▼
（并行）agent 可立刻继续：execute / diagnose / 下一轮编辑
（并行）用户随时去前端 review，accept / reject 完全是 agent 之外的事
```

#### 客户端 diff 算法约束（重要！agent 必须遵守）

`save-notebook --with-diff` 只对 agent 提交的 target notebook 做**安全注入**——它对 agent 提供的 target 内容有以下要求，违反会**直接报错** `agent_truly_deleted_cells`：

1. **`modified` cell**：保留原 cell.id，把 source 改成新代码即可，脚本会自动算出 base_source 并注入 metadata
2. **`added` cell**：新增 cell 时**必须有 cell.id**（建议 uuid4）
3. **`removed` cell**（关键约束）：
   - [WARN] **agent 不能从 cells 数组里物理删除该 cell**
   - 必须**保留** cell（id / source / cell_type 都和 base 完全一样）
   - 在 cell 的 metadata 中加上 `{"agent_diff": {"action": "removed"}}`
   - 这是 v2 文档原文要求："物理删除会导致 base 信息丢失，前端无法 reject 恢复"
   - 如果 agent 真删了 cell，脚本会拒绝 PUT 并返回 `error: agent_truly_deleted_cells`，要求 agent 重新生成 target

#### base_source 累积语义（重要！连续修改不丢原文）

当同一 cell 被 agent 连续修改两次且中间用户还没 review 时，**`base_source` 永远锁定到最初的原文**，不会被中间态覆盖。

**场景**（原文 2222 → agent 改 3333 → 用户未 review → agent 又改 4444）：

| 阶段 | 远端 cell.source | metadata.agent_diff |
|---|---|---|
| T0 初始 | `2222` | （无）|
| T1 agent 首次 PUT 为 3333 | `3333` | `{action:"modified", base_source:"2222"}` |
| T2 agent 再次 PUT 为 4444（用户未 review）| `4444` | `{action:"modified", base_source:"2222"}` [OK] |

该语义是脚本**自动保证的**，agent 只需保证两点：
- 二次 PUT 前先 `read-notebook` 拿到最新远端 nb（里面已带 T1 注入的 `agent_diff.base_source="2222"`）
- target 里**保留**该 cell 的 `metadata.agent_diff` 字段原貌（不要手动清掉）

实现原理：脚本检测到 target cell 的 `metadata.agent_diff` 已带 `base_source` 时会沿用旧值，而不用"当前远端 base 的 source"（即中间态 3333）覆盖。这保证用户 reject 时能回到真正的原文。

#### 精准修改模式：`--target-cell-ids`（重要）

**用户明确指定“只改某几个 cell”时**（如「把 cell `4cdeb6af` 改为 5555」「修一下第 3 个 cell」），必须加 `--target-cell-ids "<id1>,<id2>"` 进入精准模式，防止 agent 误动其他 cell。

**语义**：
- 白名单内的 cell：正常参与 diff 计算与 metadata 注入
- 白名单外的 cell：**必须与 base 完全一致**（id / source / cell_type 都不变）且**metadata 原样不动**——保护仅期望被修改那些 cell 的上下文（包括上一轮未 review 的 agent_diff 也不会被误清）
- 若某个白名单外的 cell 与 base 不一致，脚本拒绝 PUT 并报 `error: out_of_scope_cells_modified`，要求 agent 要么把那些 cell 也加入 `--target-cell-ids`，要么重新生成 target
- 允许 agent 在 target 中**只传要改的 cell**（白名单外的 cell 可以不拷入 target），脚本会从 base 自动补齐为完整 nb 后再 PUT——这让极简调用成为可能

**何时该加**：
- [OK] 用户明确说「修改 cell X」「把第 N 个代码块改成…」「只改这个 cell」
- [OK] 只需追加一个新 cell（把新 cell 的 id 列进白名单）
- [FAIL] 用户说「重构整个 notebook」「重写这个文件」（走全本扫描更合适，不要加）
- [FAIL] agent 自动修复 / 全量重生成（这种场景 agent 意图就是动多 cell）

#### 与既有子技能的协同

| 既有动作 | 该不该走 diff | 备注 |
|---|---|---|
| `save-notebook` 修改已有 notebook | [OK] 默认加 `--with-diff` | 与远端 base 做 cell-level diff；用户说不要才不加 |
| `save-notebook` 新建 notebook（远端无该文件）| [OK] 默认加 `--with-diff` | 视 base 为空，所有 cell 全部标为 `added`，每个 cell 都进入 review |
| `add-storage-cell` 追加 hadoop fs 命令 | [OK] 走 diff | 让用户能 reject 不想要的存储行为 |
| `edit-run-diagnose` 自动修复循环 | [OK] 每轮 save 都加 `--with-diff` | execute 不阻塞，用户最后一并 review 多轮改动 |
| `run-and-diagnose` / `execute` | [OK] 正常调用，**不需要**先检查 diff 状态 | 文件物理上已是 target，跑的就是 agent 想要的新代码 |

#### 反模式（禁止）

- [FAIL] 调用 `save-notebook` 不加 `--with-diff` 直接覆盖用户 notebook（除非用户**明确**要求"直接改、别走 diff"）
- [FAIL] 删 cell 时直接从 cells 数组里物理删除（会触发 `agent_truly_deleted_cells` 错误）
- [FAIL] 自创 `metadata.agent_diff` 内容塞到 target 里（应该让脚本算）
- [FAIL] 试图调用 `open-diff` / `list-diffs` / `accept` / `reject`（v2 协议中 agent 端**不参与**这些操作，它们要么不存在、要么属于前端）
- [FAIL] 在告知用户时说"我会等你 review 完再继续"——这与 v2 解耦设计相反；正确说法是"修改已保存，你可以随时去前端 review，我会继续后续工作"

#### 命令参考

**最常见的"改完即继续"一条龙**（全本扫描模式）：
```bash
do-bigdata wedata save-notebook \
  --path "demo.ipynb" \
  --content '<目标完整 notebook JSON>' \
  --with-diff
```

**精准修改模式**（用户明确要改某几个 cell）：
```bash
do-bigdata wedata save-notebook \
  --path "demo.ipynb" \
  --content '<只带要改的 cell、或完整 nb 都可以>' \
  --with-diff \
  --target-cell-ids "4cdeb6af,9a1b2c3d"   # 逗号分隔的 cell.id
```
> 脚本会保证：只对 `4cdeb6af` / `9a1b2c3d` 走 diff 注入；其余 cell 与远端 base 不一致会报 `out_of_scope_cells_modified`；其余 cell 原有的 `metadata.agent_diff`（未 review 的上轮修改）不会被误清。

stdout 末尾会含 `diff_summary`（modified/added/removed/unchanged/out_of_scope_unchanged 计数）和 `review_hint`，AI 应把这块信息展示给用户。

执行紧随其后（无需任何额外标志）：
```bash
do-bigdata wedata execute \
  --file-path "demo.ipynb" --compute-id <xxx> --wait
```

#### 故障排查

| 现象 | 含义 | 怎么处理 |
|---|---|---|
| `error: agent_truly_deleted_cells` | agent 真删了 cell，违反 v2 协议 | 重新生成 target：把删掉的 cell 加回来（id/source 不变），并在 metadata 里标 `agent_diff: {action: "removed"}` |
| stdout 含 `diff_summary` 但所有计数都是 0 | 用户的 target 与 base 完全相同 | 没必要 PUT；脚本仍会 PUT 一份"内容相同"的文件，对前端无影响 |
| `Warning: 远端 base notebook 拉取失败` | base GET 失败（如 path 不存在） | 检查 path；脚本会降级为普通 PUT（不带 agent_diff） |



### 串联工作流：编辑 → 执行 → 诊断 循环

这是本技能的核心工作流，实现自动化的代码开发调试循环。

**单轮执行+诊断**：
```bash
do-bigdata wedata run-and-diagnose --file-path "Untitled.ipynb" --compute-id "xxx"
```

**完整循环（编辑+执行+诊断）**：
```bash
do-bigdata wedata edit-run-diagnose --file-path "Untitled.ipynb" --compute-id "xxx" --content '<JSON内容>'
```

**多轮循环**（最多 10 轮）：
```bash
do-bigdata wedata edit-run-diagnose --file-path "Untitled.ipynb" --compute-id "xxx" --content '<JSON内容>' --max-rounds 3
```

**循环逻辑**：
1. **编辑**：如果提供了 content，保存到文件；否则跳过
2. **执行**：提交执行任务并等待完成
3. **诊断**：获取诊断信息，检查是否有 cell 执行错误
4. **判断**：
   - 如果所有 cell 执行成功 → 循环结束
   - 如果有 cell 执行错误且未达到最大轮次 → 继续下一轮（需要外部提供修复后的 content）
   - 如果达到最大轮次 → 停止循环

### 典型使用场景

**场景一：用户要求运行 notebook 并查看结果**
1. 先调用 `diagnose` 获取 compute_id 和文件状态
2. 调用 `execute --wait` 执行 notebook
3. 调用 `diagnose` 查看执行结果和错误
4. 如果用户指定了本地文件，从远端读取执行后的 notebook 并保存到本地

**场景二：用户要求修改代码并运行**
1. 调用 `read-notebook` 读取当前文件内容
2. 根据用户需求修改 cells 内容
3. 调用 `save-notebook` 保存修改
4. 如果用户指定了本地文件，将修改后的内容同步写入本地文件
5. 调用 `execute --wait` 执行
6. 调用 `diagnose` 诊断结果
7. 如果用户指定了本地文件，从远端读取执行后的 notebook（含 outputs）并保存到本地

**场景三：用户要求自动修复错误**
1. 调用 `diagnose` 获取错误信息
2. 分析错误原因，修改对应 cell 的代码
3. 调用 `edit-run-diagnose` 执行完整循环
4. 如果用户指定了本地文件，每轮修改和执行后都需将最新 notebook 内容同步到本地
5. 如果仍有错误，重复步骤 2-4

**场景四：用户提供 Spark app_id 要求诊断**
1. 调用 `spark-diagnose --app-id "application_xxxx_xxxx"` 进行 AI 诊断
2. 如果用户提供了日期信息，加上 `--current-date` 参数
3. 展示诊断结果（异常类型、根因定位、解决方案）
4. 如果诊断结果中包含代码修复建议，可结合代码编辑子技能进行自动修复

**场景五：Notebook 执行失败后自动进行 Spark 诊断**
1. 调用 `diagnose` 获取 notebook 诊断信息
2. 如果 `dashboard.type` 为 `spark` 且 `application_id` 不为空，诊断脚本会**自动**调用 Spark 诊断进行深度 AI 分析，结果附加在 `spark_diagnosis` 字段中
3. 无需手动调用 `spark-diagnose`，综合诊断结果会一次性返回

## CLI 命令

通过 `do-bigdata wedata` 命令组访问 Notebook 技能的所有功能。CLI 的 `@auth_required` 装饰器自动处理凭证加载（三级 fallback：环境变量 → 加密文件 → 明文文件）。

**依赖安装**: `pip3 install requests pyDes matplotlib`（`matplotlib` 仅 `ray-metrics` 出图需要）

**支持的命令**:

| 命令 | 子技能 | 功能 | 示例 |
|------|--------|------|------|
| `read-notebook` | 代码编辑 | 读取 notebook 文件（stdout 纯 JSON） | `do-bigdata wedata read-notebook --path "Untitled.ipynb"` |
| `save-notebook` | 代码编辑 | 保存 notebook 文件 | `do-bigdata wedata save-notebook --path "Untitled.ipynb" --content '{...}'` |
| `create-notebook` | 代码编辑 | 远端创建新文件 | `do-bigdata wedata create-notebook --path my.ipynb` |
| `upload-file` | 代码编辑 | 本地 → 远端 | `do-bigdata wedata upload-file --local-path ./a.csv --remote-path a.csv` |
| `download-file` | 代码编辑 | 远端 → 本地（自动处理 notebook / 文本 / 二进制）| `do-bigdata wedata download-file --remote-path report.html --local-path ./report.html` |
| `execute` | 代码运行 | 提交执行任务（支持 `--cell-id` 执行单个 cell） | `do-bigdata wedata execute --file-path "Untitled.ipynb" --compute-id xxx --cell-id <可选>` |
| `execute-status` | 代码运行 | 查询执行状态 | `do-bigdata wedata execute-status --task-id xxx` |
| `diagnose` | 代码诊断 | 获取诊断信息 | `do-bigdata wedata diagnose --path "Untitled.ipynb"` |
| `run-and-diagnose` | 串联 | 执行+诊断 | `do-bigdata wedata run-and-diagnose --file-path "Untitled.ipynb" --compute-id xxx` |
| `edit-run-diagnose` | 串联 | 编辑+执行+诊断循环 | `do-bigdata wedata edit-run-diagnose --file-path "Untitled.ipynb" --compute-id xxx --content '{...}'` |
| `spark-diagnose` | Spark 诊断 | 通过 Spark app_id 进行 AI 诊断 | `do-bigdata wedata spark-diagnose --app-id "application_xxxx_xxxx"` |
| `list-computes` | Compute 管理 | 查询 compute 列表 | `do-bigdata wedata list-computes --runtime yarn --status healthy` |
| `get-compute` | Compute 管理 | 查询单个 compute 详情 | `do-bigdata wedata get-compute --compute-id xxx` |
| `create-compute` | Compute 管理 | 创建 compute | `do-bigdata wedata create-compute --body '{"name":"my-compute","runtime":"python"}'` |
| `update-compute` | Compute 管理 | 更新 compute | `do-bigdata wedata update-compute --compute-id xxx --body '{"name":"new-name"}'` |
| `add-storage-cell` | 存储交互 | 增加 Ceph 存储操作 cell（默认自动添加 fs.ceph.impl） | `do-bigdata wedata add-storage-cell --path "Untitled.ipynb" --operation ls --ceph-uri "ceph://share_xxx@apdcephfs_xxx/"` |
| `send-alert` | Oncall 通知 | 向 oncall 负责人发告警（自主触发） | `do-bigdata wedata send-alert --field kernel --text-file /path/to/text.txt --delete-text-file` |
| `create-group-chat` | Oncall 通知 | 拉 oncall 群（必须用户同意后调用） | `do-bigdata wedata create-group-chat --field spark --abstract "xxx" --question-file /path/to/q.txt --delete-question-file` |
| `ray-driver-log` | Ray 诊断 | 抓取 Ray Job driver_log 并扫描异常 | `do-bigdata wedata ray-driver-log --token <TOKEN> --submission-id <sid> --errors-only` |
| `ray-metrics` | Ray 诊断 | 查询 Ray 集群 CPU/GPU/内存/显存利用率 | `do-bigdata wedata ray-metrics --dashboard '<URL>' --duration 1h --metric all` |
| `pipeline-log-search` | 管道日志 | 智研 OpenAPI 检索管道日志（含 Ray 日志） | `do-bigdata wedata pipeline-log-search --token <TOKEN> --project <PROJ> --dataflow ray_log --keyword ERROR` |

> **put-variable HDFS 中转模式**：当 `put-variable` 操作指定了 `--hdfs-uri` 参数时，变量会先写入 HDFS，再通过 `hadoop fs -cp` 复制到 Ceph。这种模式适用于大数据量的 Spark DataFrame，避免 `toPandas()` 导致 Driver 内存不足。完成后会自动清理 HDFS 中间文件。

### Compute 管理命令

封装 ComputeHandler 的查询（GET）、创建（POST）和更新（PATCH）逻辑。不支持删除操作。

| 命令 | 功能 |
|------|------|
| `do-bigdata wedata list-computes` | 查询 compute 列表（支持按 runtime/name/status 过滤） |
| `do-bigdata wedata get-compute` | 查询单个 compute 详情 |
| `do-bigdata wedata create-compute` | 创建 compute |
| `do-bigdata wedata update-compute` | 更新 compute |

### Oncall 通知命令

封装 /api/notify/alert 和 /api/notify/group-chat 接口，用于在 skill 和用户都无法解决的问题上按板块路由给对应 oncall 负责人。见「子技能七：Oncall 通知」章节。

| 命令 | 功能 |
|------|------|
| `do-bigdata wedata send-alert` | 向对应 field 的负责人发送告警（服务端原文转发） |
| `do-bigdata wedata create-group-chat` | 拉 oncall 群（user + 负责人）并发送 question 作为首条消息 |

**关键差异**：HTTP 失败时本模块**不 exit 1**，而是返回 `status=failed`——通知失败不应打断主诊断流程。按 1 小时 `user+action+field+location_id` 为粒度自动去重。

### Ray / 管道日志诊断命令

这三条命令用于 Ray 任务与管道日志的诊断，鉴权独立于 notebook 主流程的 CMK：Ray Dashboard 的 `/redirect/<base64>/` 入口通常匿名可访问（仅 401/302 时补 `--cookie`），智研日志检索用 `--token`。

| 命令 | 功能 |
|------|------|
| `do-bigdata wedata ray-driver-log` | 通过智研 OpenAPI 抓取某 Ray Job 的 driver 全量日志（需 `--token`，未传则读 security_file/config.json 的 token）；submission 定位支持 `--submission-id` 直传或 `--dashboard` + `--job-id` 翻译；支持 `--list` 列举、`--errors-only`/`--summary` 错误扫描、`--tail`/`--head`/`--save` 输出控制、`--start-time`/`--end-time`/`--duration` 时间窗 |
| `do-bigdata wedata ray-metrics` | 通过 Grafana Proxy 查询 Ray 集群 CPU/GPU/内存/显存利用率与资源配置快照；`--metric` 选 cpu/gpu/mem/gram/config/all，`--duration` 或 `--start/--end` 指定时间窗，结果（PNG/CSV）输出到 `--output-dir` |
| `do-bigdata wedata pipeline-log-search` | 通过智研 OpenAPI 按关键词检索管道日志，覆盖 ES/CK；必填 `--token/--project/--dataflow`，可选 `--keyword/--field/--wildcard/--raw-query/--start-time/--end-time/--page/--limit` |

> **区分**：`ray-driver-log` 和 `pipeline-log-search` 都走**智研 OpenAPI**（都需 `--token`）：前者专抓单个 Ray Job 的 driver_log（按 submission_id 精确过滤），后者是通用的管道日志关键词检索。`ray-metrics` 走 **Ray Dashboard Grafana Proxy** 查资源利用率，数据源不同。

### 存储交互命令

封装 Ceph 存储操作的 hadoop fs 命令生成和 cell 注入逻辑。默认自动添加 `fs.ceph.impl=org.apache.hadoop.fs.ceph.CephFileSystem` 配置。支持 `put-variable` 操作，可将变量（Spark/Pandas DataFrame 等）先保存到本地再上传到 Ceph。

| 命令 | 功能 |
|------|------|
| `do-bigdata wedata add-storage-cell` | 读取 notebook，增加包含 hadoop fs 命令的 code cell 并保存 |

**支持的操作类型**：

| 操作 | 说明 | 生成的命令示例 |
|------|------|---------------|
| `ls` | 列出路径下的文件 | `!hadoop fs -Dfs.ceph.impl=org.apache.hadoop.fs.ceph.CephFileSystem -ls ceph://share_xxx@apdcephfs_xxx/` |
| `put` | 上传本地文件到 Ceph | `!hadoop fs -Dfs.ceph.impl=org.apache.hadoop.fs.ceph.CephFileSystem -put text.txt ceph://share_xxx@apdcephfs_xxx/tmp` |
| `get` | 从 Ceph 下载文件 | `!hadoop fs -Dfs.ceph.impl=org.apache.hadoop.fs.ceph.CephFileSystem -get ceph://share_xxx@apdcephfs_xxx/tmp/text.txt` |
| `mkdir` | 创建目录 | `!hadoop fs -Dfs.ceph.impl=org.apache.hadoop.fs.ceph.CephFileSystem -mkdir -p ceph://share_xxx@apdcephfs_xxx/new_dir` |
| `rm` | 删除文件 | [WARN] **已禁止**。如确需删除请手动执行 `!hadoop fs -rm` 命令 |
| `cat` | 查看文件内容 | `!hadoop fs -Dfs.ceph.impl=org.apache.hadoop.fs.ceph.CephFileSystem -cat ceph://share_xxx@apdcephfs_xxx/tmp/text.txt` |
| `put-variable` | 将变量先保存到本地再上传到 Ceph | 自动判断变量类型（Spark/Pandas DataFrame、其他类型），先保存到当前目录再用 hadoop fs -put 上传。指定 `--hdfs-uri` 时走 HDFS 中转模式：Spark DataFrame 直接 write 到 HDFS 再 cp 到 Ceph |

### 代码编辑命令

封装 ContentsHandler 的读取（GET）、保存（PUT）、创建（POST）、上传（PUT）、下载（GET）、重命名/移动（PATCH）逻辑。

| 命令 | 功能 |
|------|------|
| `do-bigdata wedata read-notebook` | 读取 notebook 文件内容（stdout 纯 JSON，调试信息打 stderr）|
| `do-bigdata wedata save-notebook` | 保存 notebook 文件内容（[WARN] 默认加 `--with-diff` 走 cell-level 审阅；支持 `--target-cell-ids` 精准修改）|
| `do-bigdata wedata create-notebook` | 远端创建新文件（支持 notebook / file / directory）|
| `do-bigdata wedata upload-file` | 本地 → 远端（按后缀自动 text / base64）|
| `do-bigdata wedata rename-path` | 重命名 / 移动远端文件或目录（PATCH，`--old-path`/`--new-path`，不重传内容）|
| `do-bigdata wedata download-file` | 远端 → 本地（自动处理 notebook / 文本 / 二进制；专为产物同步设计）|

### 代码运行命令

封装 ExecuteHandler 和 ExecuteStatusHandler 的执行和状态查询逻辑。

| 命令 | 功能 |
|------|------|
| `do-bigdata wedata execute` | 提交 notebook 执行任务（支持 `--wait` 等待完成，`--cell-id` 执行单个 cell，单 cell 完成时自动展示 output 最多 500 行） |
| `do-bigdata wedata execute-status` | 查询执行任务状态（单 cell 任务会返回该 cell 的 output，最多 500 行） |

### 代码诊断命令

封装 /api/sessions/file-info 接口的诊断逻辑。

| 命令 | 功能 |
|------|------|
| `do-bigdata wedata diagnose` | 获取 notebook 文件的完整诊断信息 |

### Spark 诊断命令

封装 LLMAPP 平台的 Spark AI 诊断服务，通过 Spark application_id 获取日志并进行智能分析。

| 命令 | 功能 |
|------|------|
| `do-bigdata wedata spark-diagnose` | 通过 Spark app_id 进行 AI 智能诊断 |

### iWiki 文档查询命令

在本地 iWiki 索引（`references/notebook_iwiki_index.json`，55 篇 reference）中按关键词/分类缩候选，返回候选 URL；正文抓取交给 iWiki MCP。

| 命令 | 功能 |
|------|------|
| `do-bigdata wedata search-iwiki` | 检索官方 iWiki 文档索引（`--keywords`/`--category`/`--module`/`--top-k`/`--list-all`），输出候选 URL 列表 |

**LLMAPP 环境配置**：

| 环境 | 状态 | 说明 |
|------|------|------|
| `dev` | [OK] 可用 | 开发环境（默认） |
| `staging` | ⏳ 暂不可用 | 预发布环境 |
| `prod` | ⏳ 暂不可用 | 正式环境 |

**诊断结果字段说明**：

| 字段 | 说明 |
|------|------|
| `app_id` | Spark application ID |
| `session_id` | LLMAPP 会话 ID |
| `env` | 使用的 LLMAPP 环境 |
| `has_error` | 诊断过程是否出错 |
| `diagnosis` | 诊断结果文本（包含异常类型、根因定位、解决方案） |
| `knowledges` | 引用的知识库内容 |
| `tool_results` | 工具调用的中间结果 |
| `error_msg` | 错误信息（仅在 has_error=true 时） |

**诊断信息字段说明**：

| 字段 | 说明 |
|------|------|
| `file_path` | 文件路径 |
| `user_id` | 用户 ID |
| `session_id` | 会话 ID |
| `compute_id` | 计算资源 ID |
| `kernel` | 内核信息（id, name, execution_state, reason 等） |
| `file` | 文件信息（cells 摘要，含错误信息） |
| `dashboard` | 监控面板（Spark/Ray dashboard URL） |
| `environment` | 运行环境（runtime, python_version, resource） |
| `packages` | 依赖包状态 |

**全局可选参数**（所有命令通用，由 CLI 的 `@skill_command` 装饰器自动注入）:

| 参数 | 说明 |
|------|------|
| `--query` | 用户原始问题（AI 自动传入） |
| `--output` | 输出格式（text / json / markdown） |

### 凭证配置

凭证由 CLI 的 `@auth_required` 装饰器自动加载，采用三级 fallback 策略（优先级从高到低）：

| 优先级 | 来源 | 适用场景 |
|--------|------|----------|
| 1 | 环境变量 `DO_BIGDATA_USER` / `DO_BIGDATA_CMK` / `DO_BIGDATA_CMK_ID` | CI/CD、临时使用 |
| 2 | 加密文件 `security_file/config.json.enc` | 日常使用（推荐） |
| 3 | 明文文件 `security_file/config.json` | 向后兼容 |

## 参考文档

```bash
# 列出 notebook 技能的所有参考文档
do-bigdata docs list --skill notebook

# 查看指定参考文档全文
do-bigdata docs show --skill notebook --file USER_GUIDE.md
```


```bash
do-bigdata docs list --skill notebook
do-bigdata docs show --skill notebook --file <文件名>.md
```

## 关键参考链接

| 资源 | URL |
|------|-----|
| WeData 平台 | https://wedata.woa.com |
| CMK 密钥下载 | https://wedata.woa.com/security/user/keys |

<!-- BIGDATA_QUERY_GUARD -->

## [WARN] --query 参数（强制要求）

每次调用 `do-bigdata` 命令时，**必须**带上 `--query "<用户原始问题>"` 参数，将用户的原始自然语言问题传递给 CLI。

**正确示例**：
```bash
do-bigdata olap metric-data --cluster starrocks-prod --metric cpu_util --query "帮我看看 starrocks-prod 最近一小时的 CPU 使用率"
```

**错误示例**（缺少 --query）：
```bash
do-bigdata olap metric-data --cluster starrocks-prod --metric cpu_util
```

> `--query` 参数用于使用回传记录用户的真实问题，缺少此参数会导致回传数据中 `user_query` 字段记录为 CLI 命令而非用户原始问题。

**严禁省略 `--query` 参数。**

<!-- /BIGDATA_QUERY_GUARD -->

<!-- BIGDATA_CLI_GUARD -->

## [WARN] CLI 可用性检查（强制前置）

在执行任何 `do-bigdata` 命令之前，**必须**先检查 CLI 是否已安装：

```bash
which do-bigdata
```

### 如果 CLI 不可用，按以下步骤修复：

**第一步**：执行本地热加载脚本安装 CLI：

```bash
python3 tencent-bigdata/hot_reload.py
```

执行后再次检查 `which do-bigdata`。如果 CLI 已可用，跳到「安装后检查」。

**第二步（仅当第一步后 CLI 仍不可用时）**：本地 `hot_reload.py` 可能是远古版本，不包含 CLI 安装逻辑。需要从远程下载最新版本并重新执行：

```bash
# 从 Skills Manager 下载最新的 hot_reload.py，覆盖本地远古版本
curl -fsSL "http://bigdata-do-skills-manager.woa.com/api/root-skill/hot_reload.py/download" -o tencent-bigdata/hot_reload.py

# 同时更新根 SKILL.md
curl -fsSL "http://bigdata-do-skills-manager.woa.com/api/root-skill/SKILL.md/download" -o tencent-bigdata/SKILL.md

# 执行最新的热加载脚本（会自动安装 CLI + 更新所有 Skills）
python3 tencent-bigdata/hot_reload.py
```

### 安装后检查

检查 hot_reload 输出：
- 如果输出包含 `[WARN] 注意: do-bigdata 不在默认 PATH 中`，需要根据输出的 `bin_dir` 执行 `export PATH` 后再调用 `do-bigdata`
- 如果输出 `CLI 可用: <路径>`，则可直接使用 `do-bigdata` 命令

**如果 CLI 不可用，必须先按照上述步骤完成安装，严禁跳过安装步骤直接放弃调用。** 如果安装出现问题，请联系 shimerhe 处理。

<!-- /BIGDATA_CLI_GUARD -->
