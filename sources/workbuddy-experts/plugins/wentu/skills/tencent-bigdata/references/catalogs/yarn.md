# Yarn 子系统 Skill 明细

> [WARN] **使用本 catalog 内任何子 skill 前，必须先读取该子 skill 的 `SKILL.md`**
>
> 本文档仅用于 **路由发现**：根据触发场景 / 关键词定位到目标子 skill 后，**必须再加载** `sub-skills/<子系统>/<skill-name>/SKILL.md`，了解完整的执行步骤、参数约束、两阶段流程与边界条件，再调用 CLI 命令或脚本。
>
> [FAIL] 严禁仅凭本文档列出的命令清单直接执行；catalog 描述通常省略关键参数与前置依赖，跳读会导致执行路径不准确。

### yarn-app-diagnose

- **目录**: `Yarn/yarn-app-diagnose/`
- **触发场景**: 当用户直接给出**运行时任务 ID**并要求诊断失败原因时使用。运行时任务 ID 分两类：(1) **YARN Application ID**（形如 `application_xxx` 或 `job_xxx`，运行在 YARN 上，可承载 Spark / MapReduce / Flink / Tez 等引擎）；(2) **峰峦 K8s on Spark Job ID**——包括 `livy-sessionid-*`（SuperSQL 经 Livy 提交的 Spark 作业，platform=`US-SUPERSQL`），以及 `us-*` / `wedata-*` **严格四段式** `^(us|wedata)-\d+-\d+-\d+$`（前缀 + 恰好 3 段纯数字，如 `wedata-2026070103102338-1782848143426-3`）才是峰峦 job_id，不是上层调度任务 ID。统一从 `app-info` 入口按 app_id 形态自动分流，返回 `engine` 字段（`yarn` 或 `fengluan`）后进入对应分支。Spark 类型应用在日志分析后会自动调用知识库检索，获取历史诊断案例作为辅助参考。
- **不触发场景**: 用户给出的是**上层调度平台任务 ID**时**不要直接调用本 skill**——先走对应调度平台 skill 拿到底层运行时 ID：
  - US 平台任务 ID（**纯数字 18 位**，不满足 `us-` 四段式）→ 先调用 `us-fail-task-diagnose`
  - WeData 任务 ID / 实例 ID（**纯数字 17 位**，不满足 `wedata-` 四段式）→ 先调用 `wedata-instance-ops`
  - TDW 例行任务 / 其他调度平台 → 先走对应调度平台 skill
  - 从这些调度 skill 中提取出 YARN application id 或峰峦 job id 后，再回到本 skill 做失败诊断
  - 注：`livy-sessionid-*` 属**峰峦运行时 job_id**（SuperSQL 经 Livy 提交），**直接走本 skill**（`engine=fengluan`）即可；仅当进一步需要 SuperSQL 全链路上下文（SQL、错误码、Failover）时才转 `SuperSQL/`
- **触发关键词**: YARN Application、application_xxx、job_xxx、AM 日志、Driver 日志、AM 容器日志链接、Container killed、Executor lost、Executor 累计失败、峰峦、Fengluan、K8s on Spark、livy-sessionid、Pod 失败、Pod 日志、OOMKilled、K8s 诊断、dashboard URL 诊断、fengluan_diagnosis
- **核心能力**:
  - 应用状态分析（YARN：state / final_status / diagnostics / am_container_logs；峰峦：platform / cluster / namespace / state / dashboard_url / diagnosis_api）
  - YARN：AM/Executor 容器日志列表获取与精准定位（从 AM 日志提取失败 Container 构造 Executor 日志链接）
  - 峰峦：解析 dashboard 获取全部 pod 列表（master + executor）、递归列出 pod 日志目录、调用 K8s 级诊断 API（ExitCodes / K8s Events / OOMKilled 判定）
  - 日志内容分段读取 + grep 关键字过滤（YARN 用 `--start` 字节偏移；峰峦用 `--tail-kb` 客户端裁剪）
  - 多 AM attempt 信息聚合（含每个 attempt 的 log_urls）
  - 失败模式匹配（基于 `yarn_log_patterns.md` 异常模式库）
  - 知识库语义检索（Spark 场景，单次诊断最多 3 次）
- **CLI 命令**:
  - `do-bigdata yarn app-info` — 获取任务基础信息（YARN / 峰峦统一入口，返回 `engine` 字段用于分流）
  - `do-bigdata yarn log-list` — 获取 YARN 容器日志文件列表
  - `do-bigdata yarn log-content` — 获取 YARN 日志内容（支持 `--start` 字节偏移和 `--grep` 关键字过滤）
  - `do-bigdata yarn knowledge-search` — 根据错误关键词检索知识库历史诊断案例（仅 Spark 类型，最多 3 次）
  - `do-bigdata yarn fengluan-dashboard` — 【峰峦】解析 dashboard URL，列出 job 信息与精选 pod（默认 master + 前 20 个 executor，支持 `--role` / `--pod-name` / `--executor-limit`）
  - `do-bigdata yarn fengluan-log-list` — 【峰峦】递归列出指定 pod 日志目录下所有日志文件
  - `do-bigdata yarn fengluan-log-content` — 【峰峦】获取 pod 日志内容（客户端 `--tail-kb` 裁剪 + `--grep` 过滤）
  - `do-bigdata yarn fengluan-diagnosis` — 【峰峦】获取 K8s 级诊断结果（支持 job 级 / pod 级 URL）
- **参考文档**: `do-bigdata docs show --skill yarn-app-diagnose --file yarn_log_patterns.md`

---

### yarn-queue-analysis

- **目录**: `Yarn/yarn-queue-analysis/`
- **触发场景**:
  1. **队列资源分析**：分析 YARN 队列或应用组的资源使用情况，识别队列拥堵、资源大户、空跑/低效任务、临时任务、批量补录。需提供应用组名称（appgroup_name）和集群名称（cluster_name），也可通过 app_id 反查应用组信息。
  2. **应用组可用计算集群查询**：根据应用组名返回可选的计算集群列表（含 `cluster_name`/`cluster_alias`/`cluster_display_name`/`cluster_en_name`/`gaia_id`），用于查询、选择目标集群或为业务侧获取 `gaia_id`。
- **触发关键词**: 队列资源、队列分析、队列拥堵、应用组资源、资源使用率、pending任务、排队任务、资源大户、空跑任务、批量补录、queue分析、YARN资源、应用组可用集群、应用组在哪些集群、应用组集群列表、gaia_id 查询、appgroup 集群
- **核心能力**:
  - 应用组可用计算集群查询（含 gaia_id，独立轻量场景）
  - 队列健康度评估（资源使用率 / pending 任务数 / 拥堵判断）
  - 资源消耗 Top-N 应用识别（资源占用大户）
  - 空跑 / 低效任务识别（长时间运行但资源增量极低）
  - 临时任务、新增任务、批量补录任务发现
  - 用户维度资源聚合（识别资源占比最高的用户）
  - 队列使用率时序趋势分析
- **CLI 命令**:
  - `do-bigdata yarn appgroup-info` — 通过 app_id 反查应用组和集群信息
  - `do-bigdata yarn queue-clusters` — 查询应用组在哪些集群有资源（返回 cluster_name/alias/中文名/英文名/gaia_id）
  - `do-bigdata yarn queue-status` — 获取应用组当前资源使用状态快照
  - `do-bigdata yarn queue-analysis` — 综合应用分析（一次返回 6 维度：Top-N/持续占用/临时任务/新增任务/批量补录/用户聚合，1 分钟最多 2 次）
  - `do-bigdata yarn queue-trend` — 队列使用率时序趋势 + 统计摘要
- **参考文档**: `do-bigdata docs show --skill yarn-queue-analysis --file queue_analysis_guide.md`
