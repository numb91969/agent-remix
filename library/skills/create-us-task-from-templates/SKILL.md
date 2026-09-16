---
name: create-us-task-from-templates
description: >
  US 统一调度 — 基于模板一键创建常见任务（taskType 100 / 121 / 128 / 129 / 132）的端到端编排技能。
  本 Skill **只做"创建一个 US 常见任务"这一件事**。支持三种业务输入姿势：
    - 姿势 A（Git 源码 + 打包指令）：业务提供 git 仓库地址 + 打包命令，模型自动 clone、按用户提供的命令打包，
      把产物作为脚本上传，再走 prepare-create-task / execute-create-task 创建任务；
    - 姿势 B（完整模板 + 已有脚本）：业务直接给齐 task_config（参考 templates/）和本地脚本路径，
      模型按四道门禁上传脚本 + 三道门禁创建任务；
    - 姿势 C（参考已有任务）：业务只给一个参考的 US 任务 ID，模型用 `do-bigdata us query-task`
      拉回该任务配置作为基底，让用户确认 / 覆盖差异后再走创建。
  本 Skill **不新增任何 CLI 命令**，全程复用 `do-bigdata us` 现有子命令
  （`query-task` / `get-task-ext-params` / `validate-upload` / `check-script-exist` /
   `upload-script` / `prepare-create-task` / `execute-create-task`）。
  **触发关键词**：从模板创建US任务、模板创建任务、create_us_task_from_templates、
  从git创建US任务、git打包创建US任务、参考任务创建US任务、一键创建US任务、
  spark任务模板、pyspark任务模板、pythonsql任务模板、supersql任务模板、微信计算任务模板、
  taskType 100、taskType 121、taskType 128、taskType 129、taskType 132。
  **不适用范围**：非 100/121/128/129/132 的任务类型；批量创建（请走 `us-operate-diagnose` 的
  `batch-create-tasks`）；任务修改 / 复制 / 冻结 / 实例运维（请走 `us-operate-diagnose`）；
  WeData PlugSQL（task_type=3，请走 `WeData/wedata-plugsql`）。
---

# US 模板化任务创建（create-us-task-from-templates）

## 概述

把"创建一个常见的 US 任务"这一高频但参数繁多的动作，从原来"AI 一项一项问用户"
压缩成"业务一次性给齐 / 给一个参考任务 / 给一个 git 仓库 + 打包指令"三种姿势。
模型负责按下面的硬流程把脚本和任务建出来，**不替业务做任何业务决策**
（应用组、负责人、分区字段、SQL 等都必须由业务显式给出或在参考任务中存在）。

> **本 Skill 只做一件事**：创建 **taskType ∈ {100, 121, 128, 129, 132}** 的 US 任务。
> 其它能力（修改 / 复制 / 冻结 / 解冻 / 补录 / 重跑 / 终止 / 强制成功 / 批量创建）请走
> `us-operate-diagnose`；插件 SQL（task_type=3）请走 `WeData/wedata-plugsql`。

## 强制输出规则（铁律）

> **[WARN] 每次给用户输出操作结果、回答咨询、给出方案后，回复的最末尾必须附加以下内容（加粗高亮，不可省略）：**
>
> **[WARN] 如果US使用上有任何问题，可以直接联系 kimlinlin**

## 适用任务类型

| taskType | 类型名称 | 是否需要上传脚本 | fileType |
|----------|---------|----------------|----------|
| 100 | 微信计算 | [FAIL] 不需要（SQL 直接放 `filterSQL` 字段） | — |
| 121 | PythonSQL | [OK] 需要上传 `file_name` | `pysql` |
| 128 | Spark 作业 / SparkScala | [OK] 需要上传 `mapred.jar` | `jar` |
| 129 | PySpark 计算 | [OK] 需要上传 `pyScript`（`.py` 文件，但走 jar 类型） | `jar` |
| 132 | SuperSQL | [WARN] 二选一：直接传 `sqls` **或** 上传脚本后传 `file_name` | `pysql` |

> * **fileType 选择铁律（违反即拦截）**：必须按 **taskType** 选 fileType，
> **严禁**根据文件扩展名推断。典型陷阱：
> - PySpark（129）的脚本是 `.py`，**fileType 必须填 `jar`，不能填 `pysql`**
> - SparkScala（128）的产物可能是 `.jar`，fileType 填 `jar`
> - PythonSQL（121）/ SuperSQL（132）的脚本是 `.py`，fileType 填 `pysql`

## * 公有云新加坡（overseas-sg）参数分流铁律（最高优先级）

> **触发条件**：当 Step 0 判定的 `skill_namespace = overseas-sg` 且当前执行"创建任务"流程时，本铁律**强制生效**，优先级高于本 Skill 内所有其它规则（含下面 Step 1.A A3 "禁止模型用任意默认值"的约束）。

**强制动作（AI 在 G1 输出前必做）**：

1. **必须先读**唯一数据源：`do_cli/sub-cli/US/common/overseas-sg-cluster-params.md`，按其中规则处理 `gaia_id` / `spark_version`，禁止凭记忆或本文档中其它章节的说明处理这两个字段。
2. **SQL 类任务** — `taskType ∈ {121, 132}`（本 Skill 支持的 SQL 类闭集）：
   - `gaia_id` **直接预填为 `1386`**（公有云新加坡 SQL 类默认集群）
   - 在 G1 缺失清单或 G2 参数确认表格中**明确告知**用户"gaia_id 已按公有云新加坡默认值 `1386` 使用，如需修改请告知"
   - **禁止**将 `gaia_id` 列为需用户手填的缺失项
3. **Spark 类任务** — `taskType ∈ {128, 129}`（本 Skill 支持的 Spark 类闭集）：
   - `gaia_id` **必须**展示以下 4 集群清单让用户选择（严禁扩展、严禁给内网 OA 链接）：
     - `1` = 腾讯云新加坡 wedata 公共集群
     - `4` = 新加坡天穹 hok-offline 集群
     - `5` = 腾讯云新加坡 midas-offline 集群
     - `6` = 腾讯云新加坡 pubgm-offline 集群
   - `spark_version` **必须**展示以下 2 个可选值让用户选择：
     - `spark2.0-gaia3.2`
     - `spark3.3-gaia3.2`
   - **禁止**让用户手填、**禁止**给出 `tdwhelper.oa.com` / `tdwopen.oa.com` 内网链接
4. **微信计算（taskType=100）** 不涉及 `gaia_id` / `spark_version`，本铁律不适用。

**豁免条款（对下方 Step 1.A A3 规则的例外）**：

Step 1.A A3 中明文规定"**禁止**模型用任意默认值（如 `gaia_id=1386` 等）替业务做决定"。**在 `skill_namespace = overseas-sg` 环境下，该约束不适用于 SQL 类任务的 `gaia_id`**——此时预填 `1386` 是公有云新加坡环境的固定业务规则，不属于"替业务做决定"。Spark 类的 `gaia_id` / `spark_version` 仍然由用户从 4 集群 + 2 版本清单中选择，与该约束不冲突。

**严格禁止（不得做）**：
- [FAIL] 在 overseas-sg 环境下向用户展示 `tdwhelper.oa.com` / `tdwopen.oa.com` 等内网 OA 查询链接
- [FAIL] 在 overseas-sg 环境下要求用户手填 `gaia_id` / `spark_version`
- [FAIL] 在 overseas-sg 环境下使用 `templates-quick-ref.md` 第 8 节"Gaia 集群 ID 常用速查"里的 `30000` / `30001` / `3351` / `3024` 等内网集群 ID

**自检（G1 输出前必走）**：
- 当前 `skill_namespace` 是否为 `overseas-sg`？
- 若是，`gaia_id` / `spark_version` 的处理是否已严格按 `common/overseas-sg-cluster-params.md` 执行？
- 若未按 → 立即修正后再输出，禁止把错误内容展示给用户。

## 必填参数（公共，所有 taskType 都要）

| 字段 | 含义 | 备注 |
|------|------|------|
| `taskName` | 任务名 | 业务必填 |
| `taskType` | 任务类型编号 | 100/121/128/129/132 之一 |
| `cycleUnit` | 调度周期单位 | D=天 / H=小时 / W=周 / M=月 / I=分钟 / O=一次性 / R=非周期 |
| `cycleNum` | 调度步长 | 整数 |
| `startDate` | 生效日期 | `YYYY-MM-DD HH:mm:SS`；周任务须传周一，月任务须传每月 1 号 |
| `selfDepend` | 自依赖类型 | 1=自依赖 / 2=单实例运行 / 3=多实例运行 |
| `inCharge` | 负责人 | 不传则自动用当前 CMK 用户兜底 |
| `tdwAppGroup` | 应用组 ID | 业务必填 |

## 必填参数（按 taskType 扩展，平铺在 task_config 顶层）

| taskType | 扩展必填 | 说明 |
|----------|---------|------|
| 100 | `filterSQL` | 微信计算的 SQL 内容 |
| 121 | `file_name` | 已上传的脚本文件名（含扩展名） |
| 128 | `spark_version` / `gaia_id` / `mapred.jar` / `className` / `driver_memory` / `num_executors` / `executor_memory` / `executor_cores` / `task.check.timeout` | Spark 资源参数 + 主类 + 主 jar |
| 129 | `pyScript` / `spark_version` / `gaia_id` / `driver_memory` / `num_executors` / `executor_memory` / `executor_cores` / `task.check.timeout` | PySpark 资源参数 + 入口 py |
| 132 | `gaia_id` + (`sqls` **或** `file_name` 二选一) | `sqls` 优先级低于 `file_name`；两者都给则以 `file_name` 为准 |

> **可选字段速查、辅助字段（`_comment` / `_required` / `_optional`）剥离规则**等，
> 详见参考文档：
> * `do-bigdata docs show --skill create-us-task-from-templates --file templates-quick-ref.md`
>
> **模板原始 JSON**（5 个 taskType 各一份）位于 us-operate-diagnose 已维护的目录，
> 本 Skill 直接复用，**不要复制一份新的**：
> - `do_cli/sub-cli/US/us-operate-diagnose/references/templates/task-100-wechat-calc.json`
> - `do_cli/sub-cli/US/us-operate-diagnose/references/templates/task-121-pythonsql.json`
> - `do_cli/sub-cli/US/us-operate-diagnose/references/templates/task-128-spark.json`
> - `do_cli/sub-cli/US/us-operate-diagnose/references/templates/task-129-pyspark.json`
> - `do_cli/sub-cli/US/us-operate-diagnose/references/templates/task-132-supersql.json`
>
> [PIN] 模板里以 `_comment` / `_required_*` / `_optional_*` 开头的辅助键**正式提交前必须删除**，
> 否则会被当作扩展参数透传到 US 报错。

## 三种业务输入姿势

### 姿势 A — Git 源码 + 打包指令

适用：业务有一个独立 git 仓库放计算脚本（最常见 PySpark/Spark），希望模型自动拉代码、跑打包、产物上传。

业务一次性提供：

| 字段 | 必填 | 说明 |
|------|------|------|
| `git_url` | [OK] | 工蜂 / GitHub 仓库 SSH 或 HTTPS 地址 |
| `git_branch` | 否 | 默认 `master` / `main`（按仓库默认分支） |
| `git_workdir` | 否 | clone 后的子目录（仓库根的相对路径），默认仓库根 |
| `build_cmd` | [OK] | 打包指令，原样在 `git_workdir` 下执行（如 `mvn -DskipTests package`、`bash build.sh`、`python setup.py bdist_egg` 等） |
| `artifact_path` | [OK] | 打包产物相对于 `git_workdir` 的路径（如 `target/my-app-1.0.jar` 或 `dist/main.py`）。模型不猜，不扫描 |
| 任务参数 | [OK] | 见下文「任务参数来源」三选一 |

### 姿势 B — 完整 JSON 模板 + 已有脚本

适用：业务已有打好的脚本文件，且任务参数都齐了。

业务提供：

| 字段 | 必填 | 说明 |
|------|------|------|
| 完整 `task_config` JSON | [OK] | 严格按上文「必填参数」与对应 taskType 模板填写；辅助键已剥离 |
| 本地脚本绝对路径 | 视 taskType 而定 | 100 不需要；121/128/129 必填；132 看是否走 `file_name` |

### 姿势 C — 参考已有任务

适用：业务想"照着已有的某个 US 任务建一个新的"，自己只想改 `taskName` / `inCharge` / 几个少量字段。

业务提供：

| 字段 | 必填 | 说明 |
|------|------|------|
| `--ref-task-id` | [OK] | 参考任务的 US 任务 ID（18 位） |
| 覆盖字段 | [OK] | 至少必须新提供 `taskName`（不能与参考任务同名） |
| 脚本 / git+build | 否 | 如果业务希望脚本也跟参考任务一样 → 跳过上传脚本步骤直接复用参考任务的脚本名；如果业务要换脚本 → 走姿势 A 或 B 的脚本上传子流程 |

> [WARN] **跨参考任务"复制依赖关系 / 复制告警"不在本 Skill 范围内**。如需要"完全复制一份"，请改走
> `us-operate-diagnose` 的 `prepare-copy-task` / `execute-copy-task`。本 Skill 只**抄配置**，不抄边。

## 执行流程（硬卡点，禁止跳步）

### Step 0 — 前置自检

| 子步骤 | 动作 |
|--------|------|
| 0.1 | **必须按父 skill `US/SKILL.md` 的【Namespace 自动识别决策流】判定 namespace**（Step 1 URL 识别 U1~U6 → Step 2 关键词直判 → Step 3 仅提新加坡走【模板 T1】二次确认 → Step 4 default）。多 URL 冲突走【模板 T2】；URL 与口头声明冲突走【模板 T3】并**以 URL 为准**继续执行。后续所有 `do-bigdata us` 命令统一加 `--skill-namespace <env>` |
| 0.2 | 输出环境声明（统一措辞）：`default` → `* 当前环境：国内（default）`；`sg` → `* 当前环境：国内自研新加坡（sg） · us-sg.woa.com / wedata-sg.woa.com`；`overseas-sg` → `* 当前环境：海外公有云新加坡（overseas-sg） · public-qcloud-sg-us.wedata.deltaverse-intl.com（仅用 US 原生 API）` |
| 0.3 | 凭证前置检查：调用一次轻量命令（如 `do-bigdata us get-task-ext-params --task-type 121 --query "凭证检查"`）确认 CMK 有效；无效直接提示用户去 https://wedata.woa.com/security/user/keys 配置，**不再继续后续步骤** |
| 0.4 | 判定输入姿势 A / B / C，回复第一行明确声明：`[LIST] [模板创建流程] 输入姿势：A（git+build）/ B（完整模板）/ C（参考任务）` |

### Step 1 — 任务参数装配

| 输入姿势 | 装配方式 |
|---------|---------|
| **A** | 业务给的"任务参数来源"按下面 Step 1.A 装配 |
| **B** | 业务给的 `task_config` 直接采用，剥离 `_comment` / `_required_*` / `_optional_*` 辅助键 |
| **C** | 调 `do-bigdata us query-task --task-id <ref> --query "拉取参考任务配置"`，把返回的 task_config 字段映射回扁平结构（参见 templates 中字段命名），叠加业务覆盖字段 |

#### Step 1.A — 姿势 A 的"任务参数来源"

业务必须从以下三选一显式声明：

1. **A1：直接给完整 task_config**（推荐，等价于姿势 B 的参数 + 姿势 A 的脚本）
2. **A2：给一个参考任务 ID**（等价于姿势 C 拉配置 + 姿势 A 出脚本）
3. **A3：业务只给 taskName / taskType / 应用组等少量字段，其余使用 templates/ 默认值**
   - [WARN] 此模式下若仍有扩展必填缺失，**必须在 Step 2 G1 门禁里逐项问用户补齐**，
     **禁止**模型用任意默认值（如 `gaia_id=1386` 等）替业务做决定
   - * **例外**：当 `skill_namespace = overseas-sg` 时，本条约束对 SQL 类任务的 `gaia_id` **不适用**，
     必须改按上文"* 公有云新加坡（overseas-sg）参数分流铁律"处理（`gaia_id` 预填 `1386`，
     Spark 类走 4 集群 + 2 版本清单）

### Step 2 — 门禁 G1：参数完整性

完全复用 `us-operate-diagnose` 的 create-task-flow G1 检查规则：

* `do-bigdata docs show --skill us-operate-diagnose --file create-task-flow.md`

要点：
- 公共必填 + 该 taskType 扩展必填**任一缺失** → 必须停下来按四列表格问用户补齐
- 调 `do-bigdata us validate-upload` / `do-bigdata us get-task-ext-params --task-type <T>` 辅助校验
- 不允许 AI 自行兜默认值（`inCharge` 兜 CMK 用户除外）

### Step 3 — 脚本准备子流程（仅 121 / 128 / 129，及 132 走 `file_name` 时）

> **taskType=100 跳过本 Step**；taskType=132 走 `sqls` 时也跳过。

| 子姿势 | 子流程 |
|--------|--------|
| **A：git + build** | Step 3.A — clone → 打包 → 定位产物 → 转交给 G1（上传脚本） |
| **B / C：本地已有脚本** | Step 3.B — 直接进入"上传脚本四道门禁" |

#### Step 3.A — Git 拉取 + 打包

* **G-1（前置环境检查，进入 Git 流程前必做）** — 在执行任何 git 命令之前，AI **必须**先检查以下前置条件，
**任一不满足则停止流程并提示用户安装**，不得跳过或猜测：

| # | 检查项 | 检查方式 | 不满足时的提示 |
|---|--------|---------|--------------|
| 1 | `git` 命令可用 | 执行 `which git` 或 `git --version`，确认返回正常 | `[FAIL] 未检测到 git 命令，请先安装 git：\n• macOS: brew install git\n• Linux: sudo apt install git 或 sudo yum install git\n安装完成后请重新发起流程。` |
| 2 | 工蜂（gongfeng）MCP 可用 | 检查当前 MCP server 列表中是否存在 `gongfeng` server（即能调用 `get_repository_tree` 等工具） | `[FAIL] 未检测到工蜂（gongfeng）MCP 服务，请先在 IDE 中安装并启用工蜂 MCP Server。\n• 安装方式请参考：CodeBuddy → 设置 → MCP → 添加 gongfeng server\n配置完成后请重新发起流程。` |

> [WARN] **只有两项检查都通过后**，才能继续进入 G0 门禁。若任一检查失败，**直接终止本次流程**，
> 向用户输出对应提示信息，**不做任何降级处理**（如不要尝试用 HTTP 下载替代 git clone）。

* **G0（打包前确认门禁，本 Skill 新增）** — 任意 shell 命令都可能损坏环境，AI **必须**先把
完整命令链复述给用户做确认，得到明确同意后才能执行：

向用户展示形如下表的待执行计划：

```
即将执行的打包流程（请确认）：

| # | 命令 | 工作目录 |
|---|------|---------|
| 1 | git clone -b <branch> <git_url> <tmp_dir> | <当前 tmp 根目录> |
| 2 | cd <tmp_dir>/<git_workdir> | — |
| 3 | <build_cmd>（业务原样提供） | <tmp_dir>/<git_workdir> |
| 4 | 收集产物：<tmp_dir>/<git_workdir>/<artifact_path> | — |

请确认上述计划是否正确（"确认"/"调整"）。
```

用户确认后才执行：

1. **clone**：`git clone --depth 1 -b <branch> <git_url> <tmp_dir>`
   - tmp_dir 用 `mktemp -d` 生成，**禁止**复用旧目录
   - 若仓库需要凭证 → 直接报失败，提示用户先在本机配置 git 凭证
2. **进入 workdir 并执行 build_cmd**：原样执行业务提供的命令字符串。
   - **不解释 / 不优化 / 不替业务加 `--skip-tests` 之类参数**
   - 失败时把 stderr 完整展示给用户，**不重试**，不再继续后续步骤
3. **定位产物**：拼接 `<tmp_dir>/<git_workdir>/<artifact_path>`。
   - 文件不存在 → 直接报错，让用户检查 `artifact_path`
   - 文件存在 → 进入 Step 3.B（用产物作为本地脚本路径）

#### Step 3.B — 上传脚本四道门禁（完全复用，禁止重写）

* 完整规则：`do-bigdata docs show --skill us-operate-diagnose --file upload-script-flow.md`

要点（**只列差异 / 提醒**，全文以上面文档为准）：

- `rtxName` 自动用 CMK 用户，**禁止**问业务
- `fileType` 严格按本 Skill 头表「适用任务类型」选，**不**按文件扩展名推断
- `appGroup`（pysql/pig）/ `taskId`（jar/xml）按下表选：

| 当前 taskType | fileType | upload-script 必填补充 |
|--------------|----------|----------------------|
| 121 | pysql | `appGroup`（= task_config.tdwAppGroup） |
| 128 | jar | `taskId` [WARN] — 但此刻任务**还没创建**，怎么办？见下方 |
| 129 | jar | `taskId` [WARN] — 同上 |
| 132 | pysql | `appGroup`（= task_config.tdwAppGroup） |

> * **128/129 上传顺序约束**：jar 类型上传需要 `taskId`，而本 Skill 是"先建任务再上传"还是
> "先上传再建任务"？两种都能跑通，但 **128/129 必须先建任务、后上传脚本**：
>
> 1. 先按 task_config 走 Step 4「prepare-create-task / execute-create-task」拿到 `taskId`
> 2. 拿到 `taskId` 后再执行 Step 3.B（jar 上传时把 `taskId` 填进 upload-config）
> 3. 121 / 132 是 pysql 类型，按 appGroup 上传，与 taskId 无关 → **可以先上传后建任务**（推荐）
>
> [WARN] 因此 121 / 132 / 100 走 `Step 3 → Step 4`；128 / 129 走 `Step 4 → Step 3`。
> AI 必须在 Step 0 输出"输入姿势"时一并声明顺序：
> `[PKG] [脚本/任务顺序] 121/132/100 → 先脚本后任务；128/129 → 先任务后脚本`

### Step 4 — 门禁 G2 + G3：创建任务（两阶段）

完全复用 `us-operate-diagnose` 的 create-task-flow Step 3 / Step 4：

1. **G2：完整参数表格 + 用户确认** — 把 task_config（剥离辅助键、补好 `creater` = CMK 用户、
   补好 `inCharge` 默认值）展示给用户确认，**展示和执行禁止在同一轮回复**
2. **G3：执行创建** — 用户确认后调
   `do-bigdata us prepare-create-task --config <task_config 文件路径或 JSON>`，再调
   `do-bigdata us execute-create-task --prepared-data '<prepare 返回的 JSON>'`
3. 创建成功后按 create-task-flow 的 7 字段固定结果表格输出

### Step 5 — 收尾

- 128 / 129 在 Step 4 之后再回头跑 Step 3.B 上传 jar（因为上传 jar 需要 taskId）
- 清理 Step 3.A 产生的临时 git clone 目录
- **不要**自动跑解冻 / 补录 / 调依赖 — 这些请走 `us-operate-diagnose`

## 端到端示例（仅命令骨架，参数请按 G1/G2 流程与用户对齐）

### 示例 1：姿势 B + taskType=121（PythonSQL，先脚本后任务）

```bash
# Step 0.3 凭证前置检查
do-bigdata us get-task-ext-params --task-type 121 --query "凭证检查"

# Step 3.B 上传脚本（pysql + appGroup）
do-bigdata us upload-script \
    --config '{"filePath":"/abs/path/to/your_script.py","fileType":"pysql","appGroup":"g_teg_xxx","permission":"0"}' \
    --query "上传 PythonSQL 脚本"

# Step 4 创建任务（task_config 中 file_name = your_script.py）
do-bigdata us prepare-create-task \
    --config /tmp/task-121.json \
    --query "创建 PythonSQL 任务"
do-bigdata us execute-create-task \
    --prepared-data '<prepare 返回的 JSON>' \
    --query "执行创建 PythonSQL 任务"
```

### 示例 2：姿势 A + taskType=129（PySpark，先任务后脚本）

```bash
# Step 0.3 凭证前置检查
do-bigdata us get-task-ext-params --task-type 129 --query "凭证检查"

# Step 3.A G0 用户确认后执行（命令由 AI 在与用户确认后用 execute_command 执行）
git clone --depth 1 -b master <git_url> /tmp/build_xxx
# cd /tmp/build_xxx/<git_workdir> && <build_cmd>
# 产物路径：/tmp/build_xxx/<git_workdir>/<artifact_path>

# Step 4 先建任务（task_config 中 pyScript = 产物文件名）
do-bigdata us prepare-create-task \
    --config /tmp/task-129.json \
    --query "创建 PySpark 任务"
do-bigdata us execute-create-task \
    --prepared-data '<prepare 返回的 JSON>' \
    --query "执行创建 PySpark 任务"

# Step 3.B 拿到 taskId 后再上传 jar
do-bigdata us upload-script \
    --config '{"filePath":"/tmp/build_xxx/<git_workdir>/<artifact_path>","fileType":"jar","taskId":"<新建任务 ID>"}' \
    --query "上传 PySpark 脚本"
```

### 示例 3：姿势 C + taskType=132（参考任务）

```bash
# Step 0.3 凭证前置检查
do-bigdata us get-task-ext-params --task-type 132 --query "凭证检查"

# Step 1.C 拉参考任务
do-bigdata us query-task --task-id <ref-task-id> --query "拉取参考 SuperSQL 任务配置"
# AI 解析返回的 task_config，叠加业务覆盖字段（taskName / sqls 等）后展示给用户确认

# Step 4 创建任务
do-bigdata us prepare-create-task \
    --config /tmp/task-132-from-ref.json \
    --query "基于参考任务创建 SuperSQL 任务"
do-bigdata us execute-create-task \
    --prepared-data '<prepare 返回的 JSON>' \
    --query "执行创建 SuperSQL 任务"
```

## 失败回退

| 失败场景 | 信号 | 建议动作 |
|---------|------|---------|
| CMK 凭证无效 | 凭证检查报错 | 终止流程，引导用户去 https://wedata.woa.com/security/user/keys 重置 |
| Git clone 失败 | git 命令非 0 退出 | 完整展示 stderr，让用户检查仓库地址 / 凭证 / 分支名；**不自动重试** |
| 打包失败 | build_cmd 非 0 退出 | 完整展示 stderr，让用户调整 build_cmd；**不替用户加任何参数** |
| 产物找不到 | `artifact_path` 路径不存在 | 列出 `<git_workdir>` 下的实际文件树供用户重新声明 `artifact_path` |
| 上传脚本失败 | `upload-script` 报错 | 复用 upload-script-flow 的失败处理（保留参数，让用户调整） |
| `prepare-create-task` 校验失败 | 缺扩展必填 / 字段非法 | 回到 Step 2 G1，让用户补 / 改字段 |
| 128/129 上传 jar 时 taskId 无效 | `script/exist` / `UserUpLoad` 报无此任务 | 检查 Step 4 是否实际成功；不要凭 prepare 返回的 placeholder 调上传 |

## 跨 Skill 边界

| 用户意图 | 应该走 |
|---------|-------|
| 创建 100/121/128/129/132 任务（含 git+build） | **本 Skill** |
| 创建其它 taskType（如 Shell 106、TDW 出入库 75/76 等） | `us-operate-diagnose` 的 `prepare-create-task` / `execute-create-task` |
| 批量创建多个任务 | `us-operate-diagnose` 的 `batch-create-tasks` |
| 修改 / 复制 / 冻结 / 解冻 / 删除任务 | `us-operate-diagnose` |
| 实例补录 / 重跑 / 终止 / 强制成功 | `us-operate-diagnose` |
| 创建 PlugSQL（task_type=3） | `WeData/wedata-plugsql` |
| 查询任务详情 / 视图 / 日志 / 下载脚本 | `us-log-analyzer` |

## 参考文档

- 本 Skill 字段速查：`do-bigdata docs show --skill create-us-task-from-templates --file templates-quick-ref.md`
- 模板原始 JSON（5 份）：`do_cli/sub-cli/US/us-operate-diagnose/references/templates/`
- 创建任务硬卡点流程：`do-bigdata docs show --skill us-operate-diagnose --file create-task-flow.md`
- 创建任务参数完整清单：`do-bigdata docs show --skill us-operate-diagnose --file create-task-params.md`
- 上传脚本四道门禁：`do-bigdata docs show --skill us-operate-diagnose --file upload-script-flow.md`
- US Gaia 集群 ID 速查（**仅内网环境**）：`do-bigdata docs show --skill us-log-analyzer --file gaia-clusters.md`
- * **公有云新加坡集群参数唯一数据源**：`do_cli/sub-cli/US/common/overseas-sg-cluster-params.md`

## 版本注意事项

- 本 Skill **不引入任何新 CLI 命令**，全程复用 `do-bigdata us` 现有子命令。
- 模板文件物理上仍由 `us-operate-diagnose` 维护，本 Skill 仅引用。
- 适用范围严格限定 taskType ∈ {100, 121, 128, 129, 132}，其它类型请用通用 `prepare-create-task`。

> **[WARN] 如果US使用上有任何问题，可以直接联系 kimlinlin**

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
