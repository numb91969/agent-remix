# US（统一调度）子系统 Skill 明细

> [WARN] **使用本 catalog 内任何子 skill 前，必须先读取该子 skill 的 `SKILL.md`**
>
> 本文档仅用于 **路由发现**：根据触发场景 / 关键词定位到目标子 skill 后，**必须再加载** `sub-skills/<子系统>/<skill-name>/SKILL.md`，了解完整的执行步骤、参数约束、两阶段流程与边界条件，再调用 CLI 命令或脚本。
>
> [FAIL] 严禁仅凭本文档列出的命令清单直接执行；catalog 描述通常省略关键参数与前置依赖，跳读会导致执行路径不准确。

> **路径说明（CLI 化后）**：各子 Skill 的 `SKILL.md` + `version` 位于 `do_skills/sub-skills/US/<skill>/`；
> 而 `references/` 参考文档实物已迁移到 CLI 侧 `do_cli/sub-cli/US/<skill>/references/`，由 CLI 在运行时按需加载。
> 下文「包含资源」中列出的参考文档均指 `do_cli/sub-cli/US/<skill>/references/` 下的文件。

<!-- skill:us-fail-task-diagnose -->
### us-fail-task-diagnose

- **目录**: `US/us-fail-task-diagnose/`
- **触发场景**: US 任务失败/报错/诊断失败原因；出库入库失败/脏数据/权限错误；查询告警记录（延迟/失败告警）；US 平台使用咨询（权限、配置、调度等）；封闭域相关问题。
- **触发关键词**: US任务失败、出库失败、入库失败、脏数据、权限错误、SQL报错、连接失败、OOM、告警记录、封闭域、Permission denied、脚本错误、连接超时
- **核心能力**:
  - 通过 US API 采集任务配置、实例状态、执行日志、依赖关系
  - 识别任务类型（20+种）和错误阶段（调度阶段/运行阶段）
  - 匹配已知错误模式（出库/入库/权限/连接/资源/超时/SQL/脚本/HDFS/Shell/封闭域等 11 类）
  - 失败任务自动调用平台智能分析接口（fail_task_analyze）
  - **全量日志机器化取证**（v2 物化方案：一次 fetch + N 次本地 grep），强制执行
  - 级联深度诊断（US → SuperSQL → YARN 自动级联）：
    - 有 Application ID → 自动级联 YARN 诊断
    - 有 Session/Connection ID → 自动级联 SuperSQL 链路诊断
    - 支持 SuperSQL Implicit Bypass 机制感知
  - **封闭域文档自动加载触发机制**
  - 诊断报告输出（基础信息、执行记录、依赖链路、根因分析、解决方案、相关链接）
  - **R4 缓存清理收尾**（临时诊断文件自动清理）
- **包含资源**:
  - 共享 `us-log-analyzer` 的 CLI 命令能力和参考文档
  - 独立参考文档（`do_cli/sub-cli/US/us-fail-task-diagnose/references/`，7 个文件）：
    - `execution-rules.md` — 执行规则
    - `cascade-diagnosis.md` — 级联诊断流程
    - `error-patterns.md` — 11 类错误模式定义
    - `platform-and-log.md` — 平台与日志采集
    - `fail-task-analyze-api.md` — 智能分析接口
    - `reference-links.md` — 相关参考链接
    - `report-template.md` — 诊断报告模板

---
<!-- /skill:us-fail-task-diagnose -->

<!-- skill:us-slow-task-diagnose -->
### us-slow-task-diagnose

- **目录**: `US/us-slow-task-diagnose/`
- **触发场景**: US 任务慢/耗时异常/超时；等待下发/调度延迟/队列排队；任务各阶段耗时分析/性能瓶颈定位。
- **触发关键词**: 任务慢、执行慢、耗时长、耗时异常、跑得慢、超时、等待下发、运行时间长、调度延迟、队列排队、资源等待、任务超时
- **核心能力**:
  - 6 阶段全生命周期耗时拆解（US 调度等待 → US 提交到执行引擎 → Runner 准备 → SuperSQL/计算引擎提交 → Application 运行 → 结果回写/收尾）
  - 自动获取上一运行周期日志进行**逐阶段耗时对比**分析
  - 自动标注占比 >30% 的瓶颈阶段
  - 耗时增幅判定（总耗时或关键阶段增幅 >50% 为异常）
  - **阶段耗时表精确性铁律**：严禁出现"待确认"/"约数分钟"等模糊措辞，必须精确到秒
  - 级联深度诊断（**无条件执行，非询问式**，反问禁止铁律）：
    - 底层引擎=Spark + 1个 App ID → 级联 `spark-slow-analyzer`（diagnose 模式）
    - 底层引擎=Spark + 2个 App ID（含上一周期）→ 级联 `spark-slow-analyzer`（compare 模式）
    - 底层引擎=MR/Flink + App ID → 级联 `yarn-app-diagnose`
    - 有 Session/Connection ID → 级联 SuperSQL 链路诊断
    - 无关键 ID 但耗时异常 → 级联 `yarn-queue-analysis`（队列资源分析）
  - 诊断报告输出（基础信息、阶段耗时分析、耗时对比表格、根因分析、优化建议）
  - 临时诊断文件自动清理
- **包含资源**:
  - 共享 `us-log-analyzer` 的 CLI 命令能力和参考文档
  - 独立参考文档（`do_cli/sub-cli/US/us-slow-task-diagnose/references/`，3 个文件）：
    - `execution-rules.md` — 执行规则
    - `cascade-diagnosis.md` — 级联诊断流程（慢任务专项）
    - `platform-and-log.md` — 平台与日志采集

---
<!-- /skill:us-slow-task-diagnose -->

<!-- skill:us-operate-diagnose -->
### us-operate-diagnose

- **目录**: `US/us-operate-diagnose/`
- **触发场景**: 用户需要对 US 任务或实例进行管理操作，包括创建、修改、复制、上传脚本、创建依赖、冻结解冻、补录、回溯、重跑、终止、强制成功等。
- **触发关键词**: 创建任务、上传脚本、创建依赖、冻结任务、解冻任务、修改任务、复制任务、任务补录、任务回溯、重跑实例、终止实例、kill实例、强制成功、查询告警配置、修改告警
- **核心能力**:
  - **任务级操作**：
    - 创建任务（两阶段：prepare 校验 + execute 执行，三道门禁确认流程 G1/G2/G3）
    - 批量创建任务
    - 修改任务（两阶段，支持告警配置自动补全，展示修改前后对比）
    - 复制任务（两阶段，支持批量复制、超过 10 个自动分批，支持 addlink 控制是否复制关联关系）
    - 上传脚本（四道门禁流程：G1 参数校验 → G2 脚本检查 → G3 确认上传 → G4 执行上传）
    - 创建依赖关系（在两个任务间建立父子依赖）
    - 冻结/解冻任务（两阶段，自动查询任务信息展示确认，超过 10 个自动分批）
    - 查询任务类型、查询告警配置、获取扩展参数列表
  - **实例级操作**：
    - 补录实例（自动按周期类型分批，生效日期约束自动处理）
    - 回溯任务（自动路由 WeData/US 接口，根据任务 ID 长度和 projectId 智能判断，支持 4 种回溯方式 11/12/21/22）
    - 重跑实例（自动分批 + 异步轮询结果，支持 5 种重跑方式 11/12/21/22/31）
    - 终止实例（两阶段 + 终止轮询策略）
    - 强制成功（两阶段 + 强制成功轮询策略）
  - **智能特性**：
    - `requires_user_confirmation` 程序级确认拦截（所有写操作必须用户确认）
    - 操作前自动查询任务信息，基于调度周期给出合理时间范围示例
    - 操作人自动从 CMK 凭证获取，无需用户提供
    - 小时/分钟任务时间格式自动补齐
    - 隐藏底层命令行和原始 JSON，只展示结构化结果
- **CLI 命令**（统一挂在 `do-bigdata us` 下）:
  - 任务操作：`prepare-create-task` / `execute-create-task` / `modify-task` / `copy-task` / `freeze` / `unfreeze`
  - 脚本操作：`validate-upload` / `check-script-exist` / `upload-script`
  - 依赖操作：`create-dependency`
  - 实例操作：`backfill` / `retrace` / `redo` / `kill` / `force-success`
  - 查询辅助：`query-task-types` / `query-alarm-config` / `get-task-ext-params`
- **包含资源**:
  - 独立参考文档（`do_cli/sub-cli/US/us-operate-diagnose/references/`，8 个文档 + 5 个任务模板）：
    - `create-task-flow.md` — 创建任务流程（三道门禁）
    - `create-task-params.md` — 创建任务参数说明
    - `create-task-type-rules.md` — 任务类型规则
    - `upload-script-flow.md` — 上传脚本流程（四道门禁）
    - `task-modify-freeze-flow.md` — 修改/冻结/解冻流程
    - `instance-operate-flow.md` — 实例操作流程（补录/回溯/重跑/终止/强制成功）
    - `operation-notes.md` — 操作注意事项
    - `cli-reference.md` — CLI 命令参考
    - `templates/` — 5 类任务模板 JSON（100/121/128/129/132）

---
<!-- /skill:us-operate-diagnose -->

<!-- skill:create-us-task-from-templates -->
### create-us-task-from-templates

- **目录**: `US/create-us-task-from-templates/`
- **触发场景**: 用户希望基于模板 / 参考任务 / git 仓库 + 打包指令一键创建一个 US 常见任务（taskType ∈ {100, 121, 128, 129, 132}）。
- **触发关键词**: 模板创建US任务、create_us_task_from_templates、git打包创建US任务、参考任务创建US任务、一键创建US任务、spark任务模板、pyspark任务模板、pythonsql任务模板、supersql任务模板、微信计算任务模板、taskType 100/121/128/129/132
- **适用范围**: 仅 taskType ∈ {100, 121, 128, 129, 132}；其它 taskType / 批量创建 / 修改 / 复制 / 实例运维请走 `us-operate-diagnose`；PlugSQL（task_type=3）请走 `WeData/wedata-plugsql`。
- **核心能力**:
  - **三种业务输入姿势**：
    - A — `git_url` + `git_branch` + `git_workdir` + `build_cmd` + `artifact_path` + 任务参数
    - B — 完整 `task_config` JSON + 已有脚本本地路径
    - C — 一个参考任务 ID（`do-bigdata us query-task` 拉配置作为基底，业务给覆盖字段）
  - **打包前 G0 用户确认门禁**：clone / build_cmd 必须先把完整命令链向用户确认
  - **复用 `us-operate-diagnose` 的硬卡点**：创建任务三道门禁（G1/G2/G3）+ 上传脚本四道门禁（G1/G2/G3/G4），不重复实现
  - **顺序自动选择**：121/132/100 走"先脚本后任务"；128/129 走"先任务后脚本"（jar 上传需要 taskId）
  - **fileType 选择铁律**：按 taskType 选 fileType（PySpark 129 的 .py 必须走 jar，不是 pysql）
  - **5 步硬卡点执行流程**：Step 0 前置自检 → Step 1 参数装配 → Step 2 G1 参数完整性 → Step 3 脚本准备 → Step 4 创建任务(G2+G3) → Step 5 收尾
  - **不引入新 CLI**：全程复用 `do-bigdata us query-task` / `validate-upload` / `check-script-exist` / `upload-script` / `prepare-create-task` / `execute-create-task` / `get-task-ext-params`
- **包含资源**:
  - `templates-quick-ref.md`（实物路径 `do_cli/sub-cli/US/create-us-task-from-templates/references/`）— 5 类 taskType 字段速查
  - 模板 JSON 直接引用 `do_cli/sub-cli/US/us-operate-diagnose/references/templates/`，**不重复维护一份**
  - 复用文档：`us-operate-diagnose` 的 `create-task-flow.md` / `create-task-params.md` / `upload-script-flow.md` / `create-task-type-rules.md`

---
<!-- /skill:create-us-task-from-templates -->

<!-- skill:us-log-analyzer -->
### us-log-analyzer

- **目录**: `US/us-log-analyzer/`
- **触发场景**: **不直接对用户触发**（失败/慢任务诊断由对应 Skill 调用）；但以下场景直接路由到此 Skill：下载脚本、批量下载应用组脚本、查询脚本版本、查询视图/视图详情、查询任务列表、查询 WeData 开发态日志、WeData 任务详情/脚本下载、US 平台使用咨询。
- **触发关键词**: 下载脚本、批量下载、脚本版本、脚本查询、应用组脚本、WeData日志、开发态日志、执行记录、US使用指南、封闭域、任务类型配置、Gaia集群、查询视图、视图ID、视图详情、任务所属视图、视图任务列表、任务列表查询、WeData任务列表、WeData任务详情、下载WeData脚本
- **核心能力**:
  - **US API 查询命令**（`do-bigdata us`）：
    - 任务查询（`check`、`query-task`）
    - 实例状态查询（`query-run`）
    - 执行日志获取（`log`、`stage-log`、`original-log`，支持精确定位参数）
    - 集群 Job ID 查询（`job-info`）
    - 依赖关系查询（`relation`，支持依赖检测模式）
    - 变更记录查询（`change-log`）
    - 重跑明细查询（`redo-list`）
    - 任务列表查询（`task-list`，按负责人/应用组/视图ID等条件筛选）
    - 任务类型信息查询（`task-type-info`）
    - 视图查询（`list-view` 查询任务所属视图、`view-detail` 查询视图详情含任务列表和依赖关系）
  - **US 脚本管理命令**：
    - 单个脚本下载（`download-script`）
    - 批量下载应用组脚本（`batch-download`，内置限流保护 192次/min）
    - 脚本版本查询（`script-versions`）
    - 脚本元数据查询（`script-view`）
    - 脚本存在检查（`script-exist`）
  - **WeData API 查询命令**（`do-bigdata us`）：
    - 调度态日志查询（`describe-log`）
    - 开发态执行记录查询（`describe-execution-records`）
    - 开发态执行日志查询（`describe-execution-log`）
    - WeData 项目任务列表查询（`describe-tasks`）
    - WeData 任务详情查询（`describe-task-detail`）
    - WeData 任务脚本下载（`download-file`）
  - **脚本下载降级策略**：US API 下载失败时自动降级到 WeData API 重试
  - **通用功能**：本地缓存、自动重试（3次指数退避）、限流保护（100ms间隔）、错误处理
- **包含资源**:
  - `references/`（实物路径 `do_cli/sub-cli/US/us-log-analyzer/references/`）— 16 个参考文档：
    - `troubleshooting-guide.md` — 排障流程（含任务责任人管理流程）
    - `common-errors.md` — 错误码索引及解决方案（含 US 工具箱分类列表）
    - `us-user-guide.md` — US 平台使用指南（权限/依赖/补录/告警/冻结/重跑/视图等）
    - `us-task-types.md` — 任务类型配置指南（出库/入库/计算/同步/Shell等）
    - `shell-task-guide.md` — US Shell 脚本任务使用指南
    - `closed-domain-guide.md` — 封闭域使用指南
    - `us-api-identification.md` — US API 前缀识别规则
    - `us-task-list-api.md` — US 任务列表查询接口（task-list）参数与用户字段意图识别规则
    - `gaia-clusters.md` — Gaia 集群 ID 与名称映射表（300+集群）
    - `notebook-runner-guide.md` — WeData Notebook 一键转调度指南
    - `us-faq.md` — US 常见问题（FAQ）
    - `wedata-faq.md` — WeData 高频问题 FAQ
    - `wedata-offline-task-config.md` — WeData 离线任务配置说明
    - `tdw-sql-common-issues.md` — TDW SQL 常见问题汇总
    - `mysql-sync-ip-whitelist.md` — MySQL 同步 IP 白名单授权指南
    - `error-fingerprints.json` — 错误指纹库（机器化错误模式匹配）

---
<!-- /skill:us-log-analyzer -->
