---
name: wedata-plugsql
description: >
  在 WeData 上**创建或修改 PlugSQL 离线任务**（task_type=3）的端到端编排技能。
  覆盖图示的完整流程：上传 SQL 文件 → 查询文件信息 → 创建任务（含平台运行账户）→
  配置目标表（子域 / 授权库 / 目标表草稿）→ 配置开放参数（git 同步）→
  发布前代码校验 → 代码转换并存储 → 发布上线。
  同时支持对已有 PlugSQL 任务的修改操作：修改任务配置（调度参数、负责人、脚本等）→
  更新 git 参数 → 校验 → 发布。
  **支持模板驱动创建**：业务方按标准 JSON 模板填好参数后交给 AI，AI 自动按
  step_order 顺序执行全流程，无需再逐步确认参数。
  **触发关键词**：wedata 创建 plugsql、plugsql 任务、PlugSQL、插件 SQL、
  wedata 插件 sql 任务、创建插件 sql、修改 plugsql、plugsql 修改、
  plugsql 模板、模板创建 plugsql、一键创建 plugsql、
  目标表草稿、配置目标表、saveEntityDraft、
  代码校验发布、execute_plugin、save_task_transfer_main_file、发布前校验、
  微信支付目标表、wedata plugsql 全流程、修改插件 sql 任务、更新 plugsql。
  **使用场景**：
  - 用户明确要在 WeData 上创建并发布一个 **PlugSQL（task_type=3）任务**；
  - 用户需要走"上传脚本 → 建任务 → 配目标表 → 配 git → 校验 → 发布"的完整链路；
  - 用户要**修改已有的 PlugSQL 任务**（修改 SQL 代码、调度参数、负责人、目标表、git 配置等）并重新发布；
  - 用户提供了一份**填好的 PlugSQL 参数模板（JSON）**，AI 自动按模板一键执行全流程。
  本 Skill **只做"创建 / 修改 PlugSQL 任务"这两件事**。其它离线任务（SuperSQL / PySpark
  / Shell 等）的通用增删改查请用 `wedata-task-dev`；任务实例运维请用
  `wedata-instance-ops`；即席 SQL 请用 `wedata-sql-explore`。
---

## 概述

`wedata-plugsql` 把 WeData PlugSQL 任务（task_type=3）的**创建与修改**流程封装为可复现的
编排链路。底层通过 `wedata-mcp-server` 的 MCP 工具直接调用（Streamable HTTP +
TAuth 鉴权），不依赖 do-mcp API。

**支持三种核心场景：**
- **场景 A — 从零创建**：完整走"上传 → 建任务 → 配目标表 → 配 git → 校验 → 发布"流程。
- **场景 A+ — 模板驱动一键创建**：业务方填好标准 JSON 参数模板后交给 AI，AI 自动按 `step_order` 顺序执行全流程，无需逐步确认参数。
- **场景 B — 修改已有任务**：对已有的 PlugSQL 任务做变更（SQL 代码 / 调度参数 / 负责人 / 目标表 / git 配置等）后重新发布。

**设计原则：plugsql 专属 + 完全自包含。** 本 Skill 的全部命令都在
`do-bigdata wedata plugsql` 分组下独立实现，上传文件、目录查询、计算资源、
创建 / 修改 / 发布任务均已独立重写进 plugsql：

- **不复用别人**：不依赖 `wedata-upload-utils` / `wedata-task-dev` 等任何其它子系统的命令。
- **不外供别人**：`plugsql` 下的命令与能力**仅服务于 PlugSQL 链路**，不对外提供给其它
  服务复用。其它任务类型（SuperSQL / PySpark / Shell 等）请各走自己的子系统，
  不要调用 `do-bigdata wedata plugsql ...`。

## 参考文档（按需加载）

本 Skill 的详细内容拆分为以下参考文档，**需要时**用 `do-bigdata docs show` 按需读取，
避免一次性加载过多内容：

```bash
# 列出 wedata-plugsql 的所有参考文档
do-bigdata docs list --skill wedata-plugsql

# 查看模板驱动一键创建（场景 A+）的完整说明、JSON 模板、映射表、执行流程
do-bigdata docs show --skill wedata-plugsql --file template-create.md

# 查看所有命令参数说明 + 创建/修改的端到端工作流示例
do-bigdata docs show --skill wedata-plugsql --file commands-reference.md
```

| 文档 | 内容 | 何时加载 |
|------|------|---------|
| `template-create.md` | 场景 A+ 完整内容：JSON 参数模板、字段→CLI 映射表、执行流程图、提供模板时机 | 用户提交 JSON 模板 / 问"plugsql 模板" / "一键创建" 时 |
| `commands-reference.md` | 所有子命令参数说明 + 创建（场景 A）和修改（场景 B）的端到端 bash 示例 | 执行具体命令遇到参数不确定时 / 需要完整工作流示例时 |

> [WARN] **按需加载原则**：主 SKILL.md 已包含流程规则与核心逻辑，足以指导大多数场景。
> 只在需要**模板 JSON 全文**或**具体命令参数细节**时才加载对应参考文档。

## 完整流程（与流程图一一对应）

> [ALERT] **[严禁跳步铁律 — 最高优先级]**
>
> 创建 PlugSQL 任务**必须严格按照下表 1 → 2 → 3 → 4a/4b/4c → 5 → 6a → 6b → 7 的顺序依次执行**，
> **禁止跳过任何步骤、禁止合并步骤、禁止调换顺序**。
>
> *** 任何一步失败 = 整个流程立即终止（Fail-Fast 铁律）**
>
> **每一步执行后必须检查返回结果，只有明确成功才能进入下一步。**
> 任何步骤返回错误、异常、校验不通过，都必须**立即停止整个流程**，
> 将错误信息完整反馈给用户，等用户修正后重新执行该步骤。
> **绝对禁止**：跳过失败步骤继续执行后续步骤、忽略错误强行推进、
> 将失败步骤标记为"可选"后继续。
>
> **严禁以下行为**：
> - [FAIL] 跳过 Step 1/2 直接创建任务（即使用户声称"文件已上传"，也必须验证 fileId 有效）
> - [FAIL] 跳过 Step 4（目标表配置）直接进入 Step 5（modify）或 Step 6（校验）
> - [FAIL] 跳过 Step 5（modify 配置 git 参数）直接发布
> - [FAIL] 跳过 Step 6a/6b（校验+转换）直接发布
> - [FAIL] 在一轮对话中连续执行多个步骤而不等待用户确认中间结果
> - [FAIL] 某步骤执行失败后跳过该步骤继续执行后续步骤
> - [FAIL] 某步骤返回错误/异常后不停止流程而是尝试"绕过"
> - [FAIL] 将失败步骤的结果视为"非关键"而继续推进
>
> **原因**：每一步的输出是下一步的必要输入（fileId → create → TaskId → save-target-table → modify → validate → publish），
> 跳步会导致参数缺失、接口报错或生产事故。**失败步骤若不修正就继续，
> 后续步骤必然因依赖缺失而连锁失败，甚至可能写入脏数据到生产环境。**
>
> **唯一正确做法**：按编号逐步执行，每步执行后**必须验证返回结果为成功**，
> 成功后将关键返回值告知用户，用户确认后再进入下一步。
> **任何步骤失败则立即停止，报告错误，等待用户指示。**

| # | 流程图节点 | CLI 命令 | 对应 MCP 工具 |
|---|-----------|----------|--------------|
| 1 | UploadFile | `do-bigdata wedata plugsql upload-file` | `upload_online_edit_file` |
| 2 | DescribeFile | `do-bigdata wedata plugsql describe-file` | `describe_file` |
| 3 | CreateTask | `do-bigdata wedata plugsql create` | `create_offline_task`（task-type 3） |
| 4a | getBoundaryList | `do-bigdata wedata plugsql boundary-list` | `get_boundary_list` |
| 4b | getAuthorizedDatabase | `do-bigdata wedata plugsql authorized-db` | `get_authorized_database` |
| 4c | saveEntityDraft（配置+提交目标表） | `do-bigdata wedata plugsql save-target-table` | `save_entity_draft` |
| 5 | ModifyTask（配置开放参数 / git） | `do-bigdata wedata plugsql modify` | `modify_offline_task` |
| 6a | /ExecutePlugin（代码校验） | `do-bigdata wedata plugsql validate` | `execute_plugin` |
| 6b | SaveTaskTransferMainFile（代码转换并存储） | `do-bigdata wedata plugsql transfer-main-file` | `save_task_transfer_main_file` |
| 7 | PublishOfflineTask | `do-bigdata wedata plugsql publish` | `publish_offline_task` |

> 辅助命令：
> - `do-bigdata wedata plugsql parse-template`（纯本地）**模板解析**——
>   输入模板 JSON 文件路径，程序自动校验参数、映射为 CLI 命令、生成执行计划。
>   **场景 A+ 一键创建时，AI 必须先调此命令解析模板，不要自行从 JSON 提取参数。**
> - `do-bigdata wedata plugsql platform-accounts`（`describe_platform_accounts`）查"平台运行账户"，
>   供第 3 步 `--execute-incharge` 和第 4b 步 `--account` 使用。
> - `do-bigdata wedata plugsql upload-folder-list`（`describe_file_folders`）查文件目录
>   （仅在排查 / 浏览文件目录时使用；`upload-file` 已切到
>   `upload_online_edit_file`，文件名与所属目录均由后端自动生成，**不再需要 `--folder-id`**）。
> - `do-bigdata wedata plugsql folder-list`（`describe_task_folders`）查任务目录，供 `create --dir-id` 使用。
> - `do-bigdata wedata plugsql resources`（`describe_task_compute_resource`）查计算资源，供 `create --resource-id` 使用。
>   **必须带 `--execute-in-charge <平台运行账号>`**，否则返回的资源列表可能不准确（不同账号可见资源不同）。

## 前置条件

1. **已通过 `do-bigdata auth init` 配置 CMK 凭证**。
2. **已知 project_id**：可先跑 `do-bigdata wedata projects` 查询。
3. **准备好 SQL 内容**：
   - **形态 A — 业务直接提供 `.sql` 本地文件**：直接把文件路径作为 `upload-file --path` 入参。
   - **形态 B — 业务只提供 SQL 文本/代码片段**（贴在对话里、来自其他工具的产出等）：
     **AI 必须先把这段 SQL 文本写入一个本地 `.sql` 临时文件，再用该文件路径调用 `upload-file`**。
     `upload-file` 只接受 `--path 本地文件路径`，**不**接受裸 SQL 字符串。
     落盘建议：放到 `/tmp/plugsql_<时间戳>.sql` 或工作目录下任意位置；
     文件名不影响最终展示（`upload_online_edit_file` 由后端自动生成展示名）。
   - 形态 A / B 走完后 CLI 都会以 UTF-8 纯文本读取并透传到 MCP，**不要做 base64 编码**。

   > * **SQL 内容约束（查询语句检查）**：PlugSQL 是**查询/SELECT 模式**，
   > **仅支持 `SELECT` 或 `WITH ... SELECT` 开头的查询语句**。
   > 结果写入目标表的动作由平台根据目标表配置自动完成（INSERT OVERWRITE 由后端拼装）。
   > **严禁上传 `INSERT OVERWRITE` / `INSERT INTO` / `CREATE TABLE` 等写操作语句**，
   > 否则发布前校验（validate）会报 `"仅支持查询语句(SELECT/WITH)"`。
   > 如果业务提供的 SQL 包含 `INSERT OVERWRITE ... SELECT ...`，AI 必须**只保留 SELECT 部分**再上传。

## 必填参数与用户确认规则（强制，最高优先级）

> 继承 WeData 目录的全局强制规则。本 Skill 涉及大量写操作与生产变更，AI 必须严格遵守。

### * 强制铁律

- **必填参数缺失时，必须先向用户确认，绝不自行决定**（项目、任务名、目标表库/表、
  子域、告警接收人等）。
- **凡是有查询接口能拿到候选项的，先查询再让用户挑选**（项目 / 目录 / 资源 /
  子域 / 授权库），**绝不替用户做选择**。
  向用户展示候选项时，**必须使用自然语言列表**（如 `1. xxx  2. yyy  请选择：`），
  **严禁**用 XML/JSON 伪指令（如 `<ask_followup_question> [...]`）直接输出原始工具调用格式，
  那会导致用户看到乱码般的 JSON 文本而非正常的交互界面。
- **每一步写操作前，必须用自然语言向用户复述影响面**，用户确认后再执行；
  严禁未经确认加 `--yes`。
- **`create` 与 `publish` 完全解耦**：`create` 返回的 TaskId 仅供参考，AI 不得自动
  拿它衔接后续写操作；后续步骤（save-target-table / modify / validate /
  transfer-main-file / publish）所需的 `--task-id` 必须由用户显式确认提供。
- **负责人/维护人/平台运行账户自动补全规则**：
  - **负责人（`--data-charger`）**：未指定时 CLI 自动使用提交人（当前登录用户），无需确认。
  - **维护人（`--in-charger`）**：CLI 自动把提交人放到维护人列表第一位，并确保
    负责人+维护人合计至少两个不同的人。用户无需再手动指定维护人，除非需要额外添加。
  - **平台运行账户（`--execute-incharge`）**：CLI 自动查询项目绑定的平台运行账户，
    如果项目只绑定了一个则直接使用（无需确认）；有多个时 CLI 会自动识别
    "项目共享"账户（通过 `OwnerProjectId`/`IsProjectAccount` 字段或 `pr_` 名称前缀），
    若能唯一确定则自动选择（无需确认），否则才需要用户选择。
    **AI 不应在 CLI 自动选择之前抢先让用户选账户**——直接不传 `--execute-incharge`
    让 CLI 自行决定即可。
- **调试输出（`--debug`）**：当用户要求"打印请求参数和响应"、"显示调用详情"、
  "debug 模式"等时，AI 应在命令中加上 `--debug` 标志（放在 `plugsql` 子命令组之后、
  具体子命令之前），例如：
  `do-bigdata wedata plugsql --debug folder-list -p <project_id>`。
  加了 `--debug` 后 CLI 会打印每次 MCP 请求的完整参数和响应内容。

### 关键参数清单

| 步骤 | 必须先与用户确认 | 自动补全（无需确认） | 理由 |
|------|----------------|-----------------|------|
| create | `--project-id` / `--task-name` / `--dir-id` / `--resource-id` | `--data-charger`（默认提交人）/ `--in-charger`（提交人+负责人自动补齐≥2人）/ `--execute-incharge`（项目唯一账户自动选择） | 项目隔离、责任归属、计费 |
| save-target-table | `--db` / `--table-name` / `--boundary-id` / `--life-cycle` / `--owner` | 分区字段自动从 fields 中过滤 | 库必须是用户有权限的库；目标表元数据涉及资产治理 |
| modify | `--task-id` 及 OpenPluginParam **7 项全必填**：`--tapd` / `--git-project-id` / `--git-project-name` / `--git-branch-name` / `--git-file-name`（不传则按 `{任务名}_{任务ID}.sql` 自动生成）/ `--git-file-path` / `--git-commit-message` | - | 代码同步到 git 仓库，改错影响生产 |
| publish | `--task-id` | - | 影响生产环境调度；发布前会校验 OpenPluginParam 完整性 |

### * Cron 表达式格式（WeData 6 位格式，含秒）

当使用 crontab 调度（`--schedule-type 2` + `--crontab`）时，**WeData 的 Cron 表达式必须是 6 位格式（含秒位）**，
格式为：`秒 分 时 日 月 周`。

**正确示例**：
| 含义 | 表达式 |
|------|--------|
| 每天凌晨 2 点执行 | `0 0 2 * * ?` |
| 每天凌晨 0 点执行 | `0 0 0 * * ?` |
| 每小时整点执行 | `0 0 * * * ?` |
| 每天 8:30 执行 | `0 30 8 * * ?` |
| 每周一凌晨 3 点执行 | `0 0 3 ? * MON` |

**[FAIL] 错误示例**（5 位标准 Linux cron 格式，缺少秒位）：
- `0 2 * * *` — 缺少秒位，WeData 不识别
- `30 8 * * *` — 同样缺少秒位

> [WARN] **AI 必须确保传给 `--crontab` 的表达式是 6 位格式**。
> 如果用户提供了 5 位的标准 cron 表达式，AI 应自动在最前面补 `0`（秒位）并告知用户。
> 同时注意：日和周不能同时指定具体值，其中一个必须用 `?` 表示。

## OpenPluginParam（开放参数 / Git MR 配置，PlugSQL 专用）

PlugSQL（task_type=3）任务发布时，需要通过请求体**外层独立字段** `OpenPluginParam`
（与 `TaskId` / `TaskName` / `TaskExtList` 同级，**不是** TaskExt 扩展属性）配置一组
Git 参数，发布时自动把代码提交到工蜂仓库。该字段值是 JSON 数组字符串，每个元素形如
`{"name":"gitProjectId","value":"1103601"}`。

`plugsql create` / `plugsql modify` 已内置扁平化选项，CLI 内部组装回 JSON 数组字符串
并以 `open_plugin_param` 下发：

| CLI 选项 | name 字段 | modify 必填 | create 触发后必填¹ | 说明 |
|---------|-----------|:----:|:----:|------|
| `--git-project-id` | gitProjectId | [OK] | [OK] | Git 仓库 ID（工蜂项目ID），如 `1103601` |
| `--git-project-name` | gitProjectName | [OK] | [OK] | Git 仓库路径 `group/project`，如 `scheduler/data-platform` |
| `--git-branch-name` | gitBranchName | [OK] | [OK] | Git 分支名 |
| `--git-file-name` | gitFileName | [OK] ⚙️ 自动 | [OK] | 提交文件名（含扩展名）。**modify 场景不传时自动按 `{任务名}_{任务ID}.sql` 生成**（如 `czq_test_plugsql_02_2026060815080721.sql`）。create 阶段因尚无 task_id，无法自动拼装，需显式传（仅在已触发 OpenPluginParam 提交时） |
| `--git-file-path` | gitFilePath | [OK] | 否 | 仓库内目录路径（不含文件名）；create 不传默认仓库根 |
| `--git-commit-message` | gitCommitMessage | [OK] | 否 | Git 提交描述，形如 `"XXXX任务变更"`；create 不传时系统自动生成 |
| `--tapd` | tapd | [OK] | 否 | 关联的 TAPD 单链接 |
| `--open-plugin-param-json` | - | 否 | 否 | 逃生出口：直接透传完整 JSON 数组字符串 |

> ¹ **"create 触发后必填"语义说明**：`create` 阶段 OpenPluginParam **整体可省略**——
> 7 项 git-* / tapd 选项**一个都不传**时 CLI 直接跳过 OpenPluginParam，照常建任务。
> **一旦传了任意一项**（哪怕只填了 `--tapd`），CLI 会要求 4 个核心字段
> （`--git-project-id` / `--git-project-name` / `--git-branch-name` / `--git-file-name`）必须齐全；
> 但 `--git-file-path` / `--git-commit-message` / `--tapd` 仍然可选。
> 也就是说：**`create` 不会强制让你"7 项全填"，只在你"主动开启 OpenPluginParam"后做 4 项一致性校验**。

> * **gitFileName 自动生成**：调用 `plugsql modify` 时**无需显式传 `--git-file-name`**，
> CLI 会按 `{任务名}_{任务ID}.sql` 自动拼装（任务名取本次修改值或现有配置，任务 ID 取 `-t`）。
> 仅当需要自定义文件名时才显式传入。

> * **modify 阶段（任务代码变更同步 git）—— 7 项全必填铁律**
>
> 截图中 `ModifyTask（配置开放参数）`节点明确标注：
> **tapd 链接、git 仓库、分支、文件名称（任务名+文件名.sql）、目录、提交描述（XXXX任务变更）** 全部为必填参数。
>
> CLI 层已在 `plugsql modify` 调用 `_build_open_plugin_param` 时传 `enforce_required=True`，
> **缺任意一项都会被本地拦截并报错**（避免提交到服务端后才失败）。错误示例：
>
> ```
> [FAIL] OpenPluginParam（PlugSQL 开放参数）缺少必填字段：gitFilePath、gitCommitMessage、tapd。
>    对应 CLI 选项：--git-file-path / --git-commit-message / --tapd
>    PlugSQL modify 阶段（任务代码变更同步 git）必须同时提供这 7 项 ……
> ```
>
> 若想绕过扁平化选项直接透传整段 JSON，可用 `--open-plugin-param-json`（自带逃生属性，
> 不走 7 项必填校验）。
>
> * **publish 前的服务端校验**：`/V2/PublishOffLineTask` 仍会校验
> `gitProjectId` / `gitProjectName` / `gitBranchName` / `gitFileName` 非空，
> 缺失会报 `InvalidParameter.DpeParameterCheckError`。modify 阶段已强制 7 项必填，
> publish 时这部分不会出问题。create 阶段如未配置，可在 modify 阶段补齐。

## 模板驱动一键创建（场景 A+）

> [FILE] **完整模板内容已拆分到参考文档**，使用前请先加载：
> ```bash
> do-bigdata docs show --skill wedata-plugsql --file template-create.md
> ```

**核心机制**：模板参数的解析和校验**由程序自动完成**，AI 不需要自行解析模板 JSON。

**两阶段执行流程**：

1. **prepare 阶段** — 用 `parse-template` 命令解析模板：
   ```bash
   do-bigdata wedata plugsql parse-template \
       --config <模板JSON文件路径> \
       --query "按模板创建 plugsql 任务"
   ```
   程序自动：剥离辅助键 → 校验必填字段 → 映射为 CLI 参数 → 生成执行计划表。
   **不执行任何写操作**，仅输出参数确认表给用户核对。

2. **execute 阶段** — AI 按执行计划中的命令**逐步执行**：
   - `parse-template` 输出的 `steps` JSON 包含完整的命令和参数
   - 每步含占位符（`{{file_id}}`/`{{task_id}}`/`{{verification_code}}`），
     AI 执行上一步后把实际返回值替换进去
   - 每步执行前向用户复述影响面，用户确认后再执行

**何时使用**：
- 用户提交了含 `_meta.step_order` 的 JSON 模板
- 用户说"按模板创建"、"一键创建 plugsql"、"用这个模板跑"
- 用户提供了模板 JSON 文件路径

**向用户提供模板的时机**：当用户想创建 plugsql 但参数不全时，主动询问是否需要模板。
如用户确认使用模板，调用 `export-template` 命令导出空白模板文件给业务方填写：

```bash
# 导出空白模板到指定路径
do-bigdata wedata plugsql export-template -o /path/to/plugsql_template.json

# 或导出到当前目录（默认 ./plugsql_template.json）
do-bigdata wedata plugsql export-template
```

业务方填好后把文件路径告诉 AI，AI 再用 `parse-template` 解析并执行。
模板 JSON 的字段说明见参考文档 `template-create.md`。

**核心规则**：
- **Fail-Fast**：模板驱动执行同样遵守"任何一步失败 = 立即终止"铁律，不得跳过失败步骤
- validate 的 FinalResult 必须为 true 才能进入 transfer-main-file 和 publish
- publish 返回浏览器确认链接，需用户点确认
- 分区字段只配置在 `partition_field`，不要放进 `fields` 列表
  （即使误放了，CLI 也会自动过滤掉分区字段并提示）
- 负责人/维护人/平台运行账户未指定时，CLI 自动补全（无需用户确认）；
  **AI 不要抢先查询账户列表让用户选择**，直接不传让 CLI 自动决定

## 修改已有 PlugSQL 任务（场景 B）

当用户需要修改一个**已存在的 PlugSQL 任务**时，走以下流程。

### 修改场景分类

| 修改类型 | 涉及步骤 | 说明 |
|---------|---------|------|
| 仅改 SQL 代码 | 上传新文件 → modify（更新 main_file） → validate → transfer-main-file → publish | SQL 变更必须重新上传文件、校验、发布 |
| 仅改任务配置（调度/负责人/资源等） | modify → validate → transfer-main-file → publish | 不涉及 SQL 变更时无需重新上传文件 |
| 仅改目标表 | save-target-table → validate → transfer-main-file → publish | 变更目标表后需要重新校验发布 |
| 仅改 git 参数 | modify（更新 OpenPluginParam）→ validate → transfer-main-file → publish | git 配置变更后需要重新校验发布 |
| 组合修改 | 按需组合上述步骤 | 如：改 SQL + 改调度参数 + 改 git 配置 |

### 修改流程步骤

> [ALERT] **修改流程同样严禁跳步，且同样遵守 Fail-Fast 铁律** — 必须按以下顺序执行，
> 禁止跳过校验/转换直接发布。**任何一步执行失败必须立即终止整个修改流程，
> 不得跳过失败步骤继续执行后续步骤。**

#### M-Step 0 — 确认现有任务

1. 用户提供 **task_id** 和 **project_id**
2. AI 调用 `do-bigdata wedata plugsql info -p <project_id> -t <task_id>` 查看当前任务配置
3. 将当前配置中的关键信息（任务名、负责人、调度周期、SQL 文件、目标表、git 配置等）展示给用户
4. 与用户确认要修改的具体内容

#### M-Step 1 — 上传新 SQL 文件（仅 SQL 变更时）

若用户需要修改 SQL 代码：
- 按创建流程的 Step 1（upload-file 两阶段）上传新文件，得到新的 `fileId`
- 新 SQL 同样必须遵守"仅 SELECT/WITH 查询语句"约束

若不涉及 SQL 变更则跳过此步。

#### M-Step 2 — 执行修改（modify）

**关键说明**：
- `modify` 已内置"先 describe 再合并"逻辑：用户/AI 只需传"想改的字段"，未传的字段自动继承现有值
- **OpenPluginParam 7 项在 modify 阶段全部必填**（即便只改其中一项，也需要 7 项都传齐）
- `--git-file-name` 不传时 CLI 自动按 `{任务名}_{任务ID}.sql` 生成

> [FILE] 完整命令示例请参考：`do-bigdata docs show --skill wedata-plugsql --file commands-reference.md --section "端到端工作流（修改场景 B）"`

#### M-Step 3 — 更新目标表（仅目标表变更时）

若需要修改目标表配置，调用 `save-target-table`（同创建流程 Step 4c）。
若不涉及目标表变更则跳过此步。

#### M-Step 4 — 校验 + 转换 + 发布

与创建流程的 Step 6a → 6b → 7 **完全一致**，禁止跳过：

```bash
# 4a 代码校验
do-bigdata wedata plugsql validate -p <project_id> -t <task_id> \
    --slot DP_TASK_PRE_VALIDATE --query "<用户原始问题>"

# 4b 代码转换并存储
do-bigdata wedata plugsql transfer-main-file -p <project_id> -t <task_id> \
    --query "<用户原始问题>"

# 4c 发布
do-bigdata wedata plugsql publish -p <project_id> -t <task_id> \
    --query "<用户原始问题>"
```

### 修改场景的用户确认规则

- **修改前**：必须先展示当前配置，明确告知用户"将要修改哪些字段、从什么值改为什么值"
- **modify 执行前**：CLI 内置 `_confirm_or_abort`，会打印完整 payload 供核对，用户确认后才下发
- **发布前**：校验必须通过；校验不通过时停止流程，让用户修正后重新来
- **`--git-commit-message`**：建议以变更描述为内容（如 "修改调度周期从天改为小时"），不要用泛化描述

## 输出解读

所有子命令默认输出 **text 格式**（`=== 标题 === + 原始 JSON`），可用
`--output json / markdown` 切换。关键返回字段：

| 命令 | 关注字段 |
|------|---------|
| `upload-file` | `fileId`（拼装 create / modify 的 `--main-file`） |

> [WARN] **`--main-file` 格式要求**：值必须是一个 **JSON 对象字符串**，包含 4 个字段：
> ```
> '{"fileId":"<upload返回的fileId>","fileType":"sql","filePath":"DB","fileFolderPath":"项目内共享"}'
> ```
> - `fileId`：upload-file 返回的文件 ID（**必须是字符串类型**，如 `"21761"`）
> - `fileType`：固定 `"sql"`
> - `filePath`：固定 `"DB"`
> - `fileFolderPath`：固定 `"项目内共享"`
>
> CLI 会将此字符串作为 `task_ext_list` 中 `{"PropName": "mainFile", "PropValue": "<此字符串>"}` 发给 API。
> **AI 只需传这 4 字段的 JSON 字符串，不要传外层的 PropName/PropValue 结构。**

| `describe-file` | 文件基础信息（用于补齐 create 参数） |
| `info` | 任务完整配置（修改场景 M-Step 0 查看现有配置） |
| `platform-accounts` | 可用平台账号（供 `--execute-incharge` / `--account`） |
| `boundary-list` | `UCBusinessBoundaryCode`（供 `--boundary-id`） |
| `authorized-db` | 有权限的 db 列表（供 `--db`） |
| `create` | `TaskId`（仅供参考，发布需用户显式确认） |
| `modify` | 修改结果（确认配置已更新） |
| `save-target-table` | 草稿保存结果 |
| `validate` | 校验结论（有错误需修正后再发布） |
| `transfer-main-file` | 转换并存储结果 |
| `publish` | 发布结果 |

## 回退 / 降级策略

| 失败场景 | 失败信号 | 建议动作 |
|---------|---------|---------|
| CMK 凭证缺失 | `请先执行 do-bigdata auth init 配置凭证` | 执行 `do-bigdata auth init` |
| `describe-file` 命中两阶段确认 | `[AI_ACTION_REQUIRED]` | 转交 confirm_url 给用户，确认后加 `--verification-code` 重跑 |
| `create` 报 `--execute-incharge` 非法 | schema/账号错误 | 用 `plugsql platform-accounts` 重新挑选可用账户 |
| `save-target-table` 报库无权限 | XUC 权限错误 | 库必须在 `authorized-db --account <账户>` 返回列表内 |
| `save-target-table` 报 field_type 非法 | 字段类型错误 | `--field` 的 field_type 仅允许 string/bigint/double |
| 分区表缺分区字段 | 校验失败 | 非 `noncyclic` 的 data-cycle 必须传 `--partition-field` |
| `validate` 报代码错误 | 校验结论含 error | 修正 SQL 后重新上传 / modify，再校验，**校验通过前不要发布** |
| `validate` 报"仅支持查询语句(SELECT/WITH)" | 查询语句检查 FAILED | SQL 中包含 INSERT OVERWRITE 等写操作；必须去掉 INSERT 部分，只保留 SELECT/WITH 查询语句后重新上传 |
| `validate` 报"负责人及维护人至少两个" | 负责人及运行账号检查 FAILED | 用 `plugsql modify --in-charger <另一个人>` 再加一个维护人（需与 `--data-charger` 不同） |
| `modify` 报 OpenPluginParam 缺失 | `缺少必填字段：gitXxx` | modify 阶段 7 项 git/tapd 全部必填，补齐缺失项后重试 |
| `modify` 报"读取现有任务配置失败" | task_id / project_id 有误 | 确认 task_id 和 project_id 正确，且该任务确实存在 |
| `info` 查询任务不存在 | 任务 ID 无效 | 确认用户提供的 task_id 正确；可能是任务已被删除或 project_id 不匹配 |
| `publish` 报任务状态非法 | - | 确认前置步骤（目标表 / git / 校验 / 转换）均已完成 |

## 版本注意事项

- PlugSQL 任务类型编码：**task_type=3**。
- `describe_file` 是两阶段（apply → commit）SENSITIVE_QUERY 工具；其余新增工具
  （`get_boundary_list` / `get_authorized_database` / `save_entity_draft` /
  `execute_plugin` / `save_task_transfer_main_file` / `describe_platform_accounts`）
  均为单阶段直出。
- MCP 协议版本：`2025-03-26`。
- 写操作（save-target-table / transfer-main-file / create / modify / publish）
  执行前都会先打印 payload 供核对，未经用户确认不得加 `--yes`。

## 参考文档

```bash
# 查看完整命令参数与工作流示例
do-bigdata docs show --skill wedata-plugsql --file commands-reference.md

# 查看模板驱动一键创建的完整说明
do-bigdata docs show --skill wedata-plugsql --file template-create.md

# CLI 帮助
do-bigdata wedata plugsql --help
do-bigdata wedata plugsql upload-file --help
do-bigdata wedata plugsql create --help
do-bigdata wedata plugsql modify --help
do-bigdata wedata plugsql publish --help
do-bigdata wedata plugsql save-target-table --help
do-bigdata wedata plugsql describe-file --help
```

## 联系信息

问题反馈：do-bigdata 团队

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
