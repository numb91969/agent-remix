---
name: yarn-app-diagnose
description: 当用户直接提供以下**运行时任务 ID**并要求诊断失败原因时，使用此 skill：(1) YARN Application ID —— 形如 `application_xxx` 或 `job_xxx`；(2) 峰峦（K8s on Spark）Job ID —— 包括 `livy-sessionid-*`（SuperSQL 经 Livy 提交的 Spark 作业，platform=US-SUPERSQL），以及 `us-*` / `wedata-*` **严格四段式** `^(us|wedata)-\d+-\d+-\d+$`（前缀 + 恰好 3 段纯数字，如 `wedata-2026070103102338-1782848143426-3`）才是峰峦 job_id，**不是**上层调度任务 ID。**触发边界（重要）**：如果用户给出的是**上层调度平台的任务 ID**（如 US 平台任务 ID=纯数字 18 位、WeData 任务 ID=纯数字 17 位、TDW 例行任务 ID 等），**不要直接调用本 skill**——必须先调用对应的调度平台 skill（如 us-fail-task-diagnose、wedata-instance-ops 等）解析出底层的 YARN application id 或峰峦 job id 后，再回到本 skill 做失败诊断。**`livy-sessionid-*` 说明**：它是 SuperSQL 经 Livy 提交的 Spark 作业，归属峰峦运行时 job_id，**优先用本 skill 以 `livy-sessionid-*` 为入参诊断**（`engine=fengluan`）；仅当进一步需要 SuperSQL 全链路上下文（SQL、错误码、Failover）时才转 SuperSQL 子系统。**核心思路**：引擎层故障模式（Spark Stage 失败、Driver/Executor OOM、PySpark 异常等）在 YARN 和峰峦上完全一致，区别只在「平台层」——日志获取方式不同（YARN 走 NodeManager Container 日志，峰峦走 K8s Pod 日志）、app 元信息来源不同、以及峰峦独有 K8s 级诊断（ExitCode/Events/OOMKilled）。除运行时任务 ID 外，也接受 AM/Container 日志链接或峰峦 dashboard URL 作为诊断入口。在调用此 skill 前，必须再次加载一次 tencent-bigdata 这个 skill，进行热加载。
---

## 概述

诊断**运行时任务**（YARN application / 峰峦 K8s on Spark job）的失败原因。

> [WARN] **触发边界（重要）**：本 skill **只处理运行时任务 ID**，不处理"上层调度平台任务 ID"。
>
> **应触发（用户直接给出运行时 ID）**：
> - YARN Application ID：`application_1757659972062_13336918` / `job_1757659972062_13336918`
> - 峰峦 Job ID：`livy-sessionid-31118986-...`（SuperSQL 经 Livy 提交的 Spark 作业）；或 **严格四段式** `^(us|wedata)-\d+-\d+-\d+$` 的 `us-2026070103102338-1782848143426-3` / `wedata-2026070103102338-1782848143426-3`
> - 或直接给出 YARN AM 容器日志链接、峰峦 dashboard URL
>
> **不应触发（用户给的是调度任务 ID）**：
> - US 平台任务 ID（**纯数字 18 位**，不满足 `us-` 四段式）→ 应先调用 `us-fail-task-diagnose` 等 US 相关 skill 拿到底层 YARN application id 或峰峦 job id
> - WeData 任务 ID / 实例 ID（**纯数字 17 位**，不满足 `wedata-` 四段式）→ 应先调用 `wedata-instance-ops` 等 WeData 相关 skill
> - TDW 例行任务 / 其他调度平台 → 先走对应调度平台 skill
>
> **`livy-sessionid-*` 优先本 skill（峰峦）**：`livy-sessionid-31118986-...` 是 SuperSQL 经 Livy 提交的 Spark 作业（platform=`US-SUPERSQL`），本质是峰峦运行时 job_id，**优先用本 skill 以 `livy-sessionid-*` 为入参诊断**（`engine=fengluan`，拿 Pod 日志、Stage/Task/Executor、K8s 级 ExitCode/OOMKilled）；仅当进一步需要 **SuperSQL 全链路上下文**（SQL、错误码、Failover、引擎参数）时，才转 `SuperSQL/` 子系统。
>
> 只有从上层调度 skill 中提取到**底层运行时 ID**后，才回到本 skill 做失败诊断。

**两类运行平台**：

| 平台 | app_id 形态 | 日志来源 | 元信息来源 |
|---|---|---|---|
| **YARN** | `application_xxx` / `job_xxx` | NodeManager Container 日志 (`http://{nm_ip}:{port}/node/containerlogs/...`) | YARN ResourceManager + tdwbi |
| **峰峦（K8s on Spark）** | `livy-sessionid-*` / `us-*` / `wedata-*` | K8s 节点日志服务 (`http://{host}:8081/logs/{node_ip}/{pod_uid}/...`) | 峰峦 fengluan_app_instance + dashboard SSR HTML |

**核心诊断原则**：

> * **引擎层故障模式与平台无关。** Spark 应用无论跑在 YARN 还是峰峦，Driver/Executor/Stage 概念都一样，OOM、Shuffle Fetch Failed、PySpark SyntaxError、Driver Full GC 等故障表现也都一样。**本 skill 的结构按"平台层取数"与"引擎层诊断"分离**：第 2 节负责把日志/元信息拿到手（平台差异在此收口），第 3 节做引擎层诊断（YARN/峰峦共用，单一权威源）。

**适用引擎**：Spark（YARN + 峰峦均支持）、MapReduce / Flink 等（仅 YARN）。

**核心能力**：

1. **应用状态分析** — 解读 app 基础信息（state / diagnostics / 时间 / 日志入口）快速定位问题方向
2. **日志智能获取** — 自动识别关键日志文件（stderr、stdout、spark.log、gc.log、滚动归档等），按引擎与扫描清单全覆盖
3. **首轮聚合扫描** — 用 `log-scan` / `fengluan-log-scan --profile` 一次并行扫完扫描清单中**所有** size>1 文件的整套错误关键字，最大化错误信号捕获面、最小化调用轮次
4. **PySpark / Python 专项检查** — 涉及 Python 代码时追加 10 个 Python 异常关键字
5. **Spark Stage 失败深挖** — 命中 `Aborting job` / `Job aborted due to stage failure` 后逐层定位 FetchFailedException、Lost task 等
6. **Driver Full GC 联动诊断** — Executor 集中失败时强制检查 Driver gc.log
7. **Executor / 非 Driver Pod 深度分析** — 从 Driver 日志中提取失败 Executor 信息，按平台规则获取其日志
8. **K8s 级深度诊断**（仅峰峦） — 调用诊断 API 获取 ExitCodes / K8s Events / OOMKilled 等结构化信号
9. **失败模式匹配** — 基于异常模式库（`references/yarn_log_patterns.md`）匹配根因
10. **知识库语义检索** — Spark 类应用追加历史诊断案例（单次诊断最多 3 次）
11. **诊断报告输出** — 给出明确结论和分步修复建议

## 前置条件

- 已知待诊断的任务 ID（YARN：`application_xxx`；峰峦：`livy-sessionid-xxx` / `us-...` / `wedata-...`），或可提供：
  - YARN：AM 容器日志链接 `http://{nm_ip}:{port}/node/containerlogs/{container_id}/{user}`
  - 峰峦：dashboard URL `http://{host}:8081/platforms/{platform}/jobs/{job_id}`

> * **海外任务（overseas-sg 命名空间）**：诊断部署在海外新加坡环境的 YARN 任务时，**所有 `do-bigdata yarn` 命令须追加 `--skill-namespace overseas-sg`**（Agent 应按用户意图/任务归属自动传入）。该参数会同时驱动：①鉴权走海外 TAuth 安全中心；②后端按 namespace 选海外数据源（tdwbi / NGCP StarRocks `yarn_rm_application`·`spark_app`）。不传时默认走国内（`default`）数据源，向后兼容。
>
> [WARN] 说明：`overseas-sg` 命名空间下**无峰峦（fengluan）app**，海外一律走 **YARN 原生路径**（`app-info` / `log-list` / `log-content` / `log-scan` / `knowledge-search`），无需使用 `fengluan-*` 子命令。知识库为全局资源，`knowledge-search` 传 namespace 仅作审计。

## CLI 命令说明

本 Skill 的所有数据获取操作均通过 `do-bigdata yarn` CLI 命令完成，CLI 内部会自动调用 do-mcp API 服务，**严禁直接使用 `curl` 或 `web_fetch` 等工具请求 API 或 Container / Pod 日志链接**。

> * **全局强制要求（所有命令通用）：命令输出被截断时，必须用 `read_file` 读取落盘文件取全量内容。**
>
> 部分 agent 框架会在固定字节处（如 51200 bytes）硬截断命令行 stdout。因此对所有可能产生大输出的命令（`log-scan` / `fengluan-log-scan` / `log-content` / `fengluan-log-content` / `fengluan-diagnosis`），**一律加 `--out-file auto`**：完整 JSON 会落盘，且落盘文件的**绝对路径会前置打印在 stdout 开头**（即使后续渲染摘要被框架截断，也能先拿到路径）。
>
> **一旦发现命令输出被截断（stdout 末尾出现 `truncated` / 内容明显不完整 / JSON 无法解析），不要基于残缺输出下结论、也不要重复执行命令，而是立刻用 `read_file` 读取 stdout 开头给出的落盘文件绝对路径**（可配合 `offset` / `limit` 分页）拿到无截断的全量结果。详见下文《大输出落盘》小节。

> [WARN] **日志链接获取方式要求（重要）**
>
> 无论是 YARN Container 日志（含 AM/Executor 日志）、峰峦 Pod 日志、还是诊断 API，**必须始终通过对应的 CLI 命令**获取（YARN 侧：`do-bigdata yarn log-list` / `log-content` / `log-scan`；峰峦侧：`do-bigdata yarn fengluan-*` 系列），**严禁直接请求具体链接**（如 NodeManager 的 `http://{nm_ip}:{port}/node/containerlogs/...` 或峰峦的 `http://{host}:8081/logs/...` / `/diagnosis/api/...`）。
>
> 这些链接仅作为 **传入 CLI 命令的参数**使用，不能直接用 `curl` 或任何工具访问。
>
> **正确做法**（YARN）：
> ```bash
> # 通过 CLI 获取日志列表（AM 或 Executor Container 均可）
> do-bigdata yarn log-list --container-url "http://9.23.14.56:8080/node/containerlogs/container_xxx/user"
>
> # 【首选首轮】聚合扫描：一次并行扫完整个容器全部 size>1 文件的整套错误关键字（默认加 --out-file auto 避免 stdout 截断）
> do-bigdata yarn log-scan --container-url "http://9.23.14.56:8080/node/containerlogs/container_xxx/user" --profile spark --out-file auto
>
> # 单文件深挖：一次正则多关键字（放大 --start 到 40MB 覆盖全量，用 | 覆盖多关键字；默认加 --out-file auto 避免 stdout 截断）
> do-bigdata yarn log-content --log-url "http://..." --start 40960000 --grep "ERROR|Exception|FATAL" --context 3 --out-file auto
>
> # 读末尾快速预览（默认读末尾 8KB）
> do-bigdata yarn log-content --log-url "http://..." --start 8192
> ```
>
> **正确做法**（峰峦）：
> ```bash
> do-bigdata yarn fengluan-dashboard --dashboard-url "http://21.24.99.122:8081/platforms/US-SUPERSQL/jobs/livy-sessionid-xxx"
> do-bigdata yarn fengluan-log-list --log-url "<pod.log_url>"
>
> # 【首选首轮】聚合扫描：递归扫完整个 pod 日志目录的整套错误关键字（默认加 --out-file auto 避免 stdout 截断）
> do-bigdata yarn fengluan-log-scan --log-url "<pod.log_url>" --profile spark --tail-kb 40960 --out-file auto
>
> # 单文件深挖：一次正则多关键字（默认加 --out-file auto 避免 stdout 截断）
> do-bigdata yarn fengluan-log-content --log-url "<file.url>" --tail-kb 40960 --grep "ERROR|Exception|FATAL" --context 3 --out-file auto
>
> do-bigdata yarn fengluan-diagnosis --diagnosis-url "<pod.diagnosis_url>"
> ```
>
> **错误做法**：
> ```bash
> # [FAIL] 禁止直接请求 container / pod 日志链接
> curl -s "http://9.23.14.56:8080/node/containerlogs/container_xxx/user"
> curl -s "http://21.24.99.79:8081/logs/29.98.140.74/d6642750-.../spark-kubernetes-executor/stderr"
>> # [FAIL] 禁止直接调用 API
> curl -s "http://do-mcp.server.woa.com:8080/api/yarn/app_info?app_id=application_xxx"
> ```

### 大输出落盘：`--out-file` + read_file（应对 stdout 截断）

> [WARN] **为什么需要**：聚合扫描 / 大范围 grep 命中很多时，完整 JSON 数据体积很大，**部分 agent 框架会截断命令行 stdout**，导致返回的 JSON 残缺、甚至无法解析。而`read_file` 工具读取本地文件**没有截断**。因此对大输出命令，用 `--out-file` 把完整 JSON 落盘，并把**落盘文件路径前置打印到 stdout 开头**（即使后续渲染摘要被框架截断，也能先拿到路径），再用 `read_file` 无截断读取全量结果。

**适用命令**（输出体积可能较大者，建议默认加 `--out-file auto`）：
- `log-scan` / `fengluan-log-scan`（聚合扫描，命中多时 JSON 最大）
- `log-content` / `fengluan-log-content`（读取日志内容，尤其放大 `--start` / `--tail-kb` 或带 `--grep` 做全量深挖时，输出可能很大，建议默认加）
- `fengluan-diagnosis`（job 级含全部 pod 概览时）

**用法**：
```bash
# 传 auto：完整 JSON 自动落到规范目录，stdout 仅回显渲染摘要 + 文件绝对路径
do-bigdata yarn log-scan --container-url "{am_container_logs}" --profile spark --out-file auto

# stdout 开头会【前置】打印落盘路径（即使后续渲染摘要被 agent 框架截断，也能先拿到路径）：
#   === 完整 JSON 已写入文件（请优先用 read_file 读取该绝对路径，无截断；可配合 offset/limit 分页）===
#   /root/.do-bigdata/output/log-scan_20260701_153012_12345.json
#   ────────────────────────────────────────────────────────────
#   （以下为渲染摘要，仅供快速预览；被命令行工具截断属正常，以上面的落盘文件为准）
# 然后用 read_file 读取该绝对路径拿到全量 JSON（可配合 offset/limit 分页）
```

**输出目录规范**：
- `--out-file auto` 或纯文件名 → 统一落到 `~/.do-bigdata/output/`，文件名形如 `<命令名>_<时间戳>_<pid>.json`（跨命令/并发不冲突）
- `--out-file` 传**绝对路径** → 写到指定位置（尊重调用方指定的可写目录）
- 不传 `--out-file` → 维持原行为，完整 JSON 直接打印在 stdout（小输出命令如 `app-info` / `log-list` 无需落盘）

**自动清理（无需手动删）**：
- CLI 每次写入后会**自动回收**规范目录 `~/.do-bigdata/output/` 下的历史文件：仅保留最近约 30 个结果、并清理超过 24 小时的旧文件。
- 清理由 CLI 以纯 Python 方式（进程内 `unlink`）完成，**不调用外部 `rm`**——因此**不要**再用 `rm` / shell 删除这些文件（部分 agent 框架已将 `rm` 加入命令黑名单），交给 CLI 自清理即可。

> [TIP] **决策建议**：渲染摘要（命中文件 × 关键字计数 + 样例 + 上下文）通常已足够定位方向；仅当需要逐条核对全量命中、或 stdout 明显被截断时，才 `read_file` 打开落盘文件取全量 JSON。

## 工作流总览

本 skill 严格按"平台层 → 引擎层 → 报告"三段组织。LLM 执行时按以下顺序进行：

```
第 1 步  统一获取 app-info（自动按 app_id 形态分流，返回 engine 字段）
            │
第 2 步  ┌── engine = yarn      → 2A. YARN 平台层取数（拿到 Driver 日志列表 + 扫描清单）
          └── engine = fengluan  → 2B. 峰峦平台层取数（拿到所有 pod + Driver 日志列表 + 扫描清单）
            │
            ▼
第 3 步  引擎层诊断（YARN/峰峦共用 — 与平台无关）
          ├── 3.0  首轮错误全面扫描（强制 — 用 log-scan / fengluan-log-scan --profile 一次聚合扫完整个容器/Pod）
          ├── 3.1  Spark 应用专项（Stage 失败深挖 / PySpark 专项 / Driver Full GC / Executor 深挖）
          ├── 3.2  MapReduce 应用（仅 YARN）
          ├── 3.3  Flink 应用（仅 YARN）
          └── 3.4  通用策略（未知引擎）
            │
            ▼
第 4 步  K8s 级深度诊断（仅 engine=fengluan，按需）
            │
            ▼
第 5 步  知识库检索（Spark 类应用，辅助参考）
            │
            ▼
第 6 步  根因分析与诊断报告
```

> [TIP] **关键边界条件**：YARN 状态为 SUCCEEDED 不代表内部任务全部成功。Spark 应用（尤其通过 Livy 提交的交互式 Session）可能因 Stage 失败被 Livy 捕获异常继续运行，最终状态仍是 SUCCEEDED。**即使状态正常，对 Spark 类应用也必须完成第 3 步首轮扫描**（3.0 的 `spark` profile 含 `Aborting job` / `Job aborted due to stage failure` 用于检测此类隐藏失败）。

---

## 第 1 步：获取应用基础信息（统一入口）

```bash
do-bigdata yarn app-info --app-id {app_id} --query "<用户原始问题>"
```

CLI 会按 app_id 形态自动分流：
- `application_xxx` / `job_xxx` → YARN（job_ 前缀自动归一化为 application_）
- `livy-sessionid-xxx` / `us-xxx` / `wedata-xxx` / 其他非 application 前缀 → 峰峦

**关键字段**（返回的 `engine` 字段决定后续分支）：

| 字段 | engine=yarn 含义 | engine=fengluan 含义 |
|---|---|---|
| `engine` | `"yarn"` | `"fengluan"` |
| `state` | YARN state（RUNNING/FINISHED/FAILED/KILLED） | 峰峦 state（FINISHED/FAILED/...） |
| `final_status` | YARN final_status | （无） |
| `diagnostics` | YARN AM 退出原因（最重要的一级线索） | （无 — 改用 F4 的 fengluan-diagnosis） |
| `app_type` | SPARK / MAPREDUCE / APACHE FLINK / TEZ 等 | （无 — 峰峦目前都是 Spark） |
| `am_container_logs` | Driver 容器日志链接 | Driver Pod 日志链接（同样字段名） |
| `dashboard_url` | （无） | 峰峦 dashboard URL（第 2B 步用） |
| `diagnosis_api` | （无） | 峰峦 job 级诊断 URL（第 4 步用） |
| `cluster_info` | YARN 集群信息（ch_name/en_name/alias_name/gaia_id） | 峰峦租户集群信息（同格式） |
| `data_source` | `tdwbi` / `spark_app`（兜底来源） | `fengluan_app_instance` / `+spark_app` |

**分析要点**：
- `state` / `final_status`：确认应用状态
- `elapsed_time`：执行耗时是否异常（过长可能是数据倾斜或资源等待）
- `diagnostics`（仅 YARN）：YARN 级别诊断信息，通常包含 AM 退出原因，是最重要的一级线索
- `app_type`（仅 YARN）：决定第 3 步进入哪个引擎分支；峰峦目前都按 Spark 处理

**[WARN] 边界限制：app-info 获取失败时的处理**

YARN 侧 `app_info` 内部实现了两级数据获取（tdwbi 主 + spark_app 兜底）；峰峦侧也有两级（fengluan_app_instance 主 + spark_app 兜底）。

- 若返回中含 `"data_source": "spark_app"`（或 `"+spark_app"`）：说明数据来自兜底查询，此时主要可用的是 `am_container_logs`，其他字段（state/diagnostics 等）可能不完整 → 直接跳到第 2 步用 AM 日志链接继续诊断
- 若返回 `error` 字段（两级策略均失败），**必须严格按以下规则处理**：

1. **立即停止自主探索**：禁止自行尝试其他方式获取信息（如直接拼接 ResourceManager URL、猜测日志路径、调用未在本 Skill 中定义的 API）。本 Skill 所有数据获取仅通过 `do-mcp.server.woa.com:8080` 的 `/api/yarn/` 与 `/api/fengluan_spark/` 系列接口完成
2. **向用户请求人工提供入口**：
   - YARN：请求 AM 容器日志链接 `http://{nm_ip}:{port}/node/containerlogs/{container_id}/{user}`
   - 峰峦：请求 dashboard URL `http://{host}:8081/platforms/{platform}/jobs/{job_id}`
3. **用户提供后继续流程**：拿到链接后跳到第 2A / 2B 步继续。YARN 路径此时 `app_type` 未知，按"通用策略"获取日志，后续根据日志内容（如出现 `spark.log` 则判定为 Spark 应用）动态识别

**此规则同样适用于后续步骤**：任何接口调用失败，不要自行绕过，应告知用户具体失败原因并请求必要信息。

---

## 第 2 步：平台层取数（按 engine 分流）

> * **本步骤的目标**：拿到 **Driver 日志的扫描清单**（含 size > 1 的关键日志文件），供第 3 步引擎层诊断使用。**平台差异在本步骤完全收口**，进入第 3 步后引擎诊断流程与平台无关。

### 第 2A 步：YARN 平台层取数（engine = yarn）

#### 2A.1 获取 AM 容器日志列表

**直接使用**第 1 步返回的 `am_container_logs` 字段，**原样传入** `--container-url`（CLI 内部会自动处理 TDW 代理前缀的剥离，无需手动预处理）：

```bash
do-bigdata yarn log-list --container-url "{am_container_logs}" --query "<用户原始问题>"
```

> [WARN] **Container 日志链接使用规则（重要）**
>
> **核心原则：`app_info` 返回的 `am_container_logs` 是最终可用地址，直接原样传给 `--container-url`，无需任何预处理/剥离/还原操作。**
>
> 以下是两种 URL 形态的说明：
>
> **① TDW 代理链接（国内环境，CLI 会自动剥离）**：
> ```
> http://tdw-application.tianqiong.woa.com:8080/{nm_ip}:{nm_port}/node/containerlogs/{container_id}/{user}
> ```
> CLI 内部会自动去除代理前缀，你无需手动处理。
>
> **② knox 网关链接（overseas-sg 海外环境，[NO] 禁止剥离/修改）**：
> ```
> https://public-qcloud-sg-knox.wedata.deltaverse-intl.com:8080/gateway/{cluster}/yarn/nodemanager/node/containerlogs/{container}/{user}?scheme=http&host={nm_ip}&port={nm_port}
> ```
> 这是海外环境访问容器日志的**唯一通路**，直接原样使用。**绝对不能**把它当作"代理前缀"去剥离或还原为 `http://{nm_ip}:{nm_port}/...`——内网地址不可达，剥离后请求必定超时。
>
> **判断方法**：链接以 `https://` 开头且包含 `/gateway/` 和 `?scheme=http&host=` → knox 网关，原样使用；链接含 `tdw-application.tianqiong.woa.com` 或 `application.tdw.oa.com` → TDW 代理，CLI 自动处理。

**返回示例**：
```json
{
  "logs": [
    {"name": "stderr", "url": "http://...", "size": "12345"},
    {"name": "stdout", "url": "http://...", "size": "234"},
    {"name": "spark.log", "url": "http://...", "size": "1"},
    {"name": "gc.log", "url": "http://...", "size": "5678"}
  ]
}
```

#### 2A.2 大日志清理识别（size=1）

> **重要诊断知识**：在调用 `log-content` 之前，**必须先检查 `log-list` 返回的每条日志的 `size` 字段**。

**触发特征**：
- `log-list` 返回的某条日志，`url` 字段正常存在，但 `size == 1`（或字符串 `"1"`）

**根本原因**：
- 当某个 Container 的日志文件**单文件超过 1.5GB** 时，为了避免写满 NodeManager 节点磁盘导致整台机器上的任务一起失败，**机器上的日志清理脚本会自动清空该日志文件内容**（保留文件名和链接，但内容被置空，文件大小变为 1 字节占位）
- 这是机器侧的**自我保护机制**，不是任务异常

**对任务的影响**：
- **完全不影响任务运行**：任务本身可能仍正常完成（YARN 状态可能为 SUCCEEDED）
- 只是无法再通过 NodeManager 容器日志查看该文件的具体内容

**正确响应方式**：
1. **不要对该日志文件调用 `log-content`**（调用结果会是空内容，浪费一次 API 调用）
2. **跳过该日志文件**，继续分析其他 `size > 1` 的日志（如 stderr / stdout / gc.log 等）
3. **明确告知用户**：该日志因超过 1.5GB 被机器侧清理脚本自动清空，**不代表任务失败**
4. **引导用户使用替代方案**：如果需要查看任务的运行情况和详细指标，建议通过 **Spark History Server** 查看（任务的 Spark UI / History Server 链接通常可在 `am_container_logs` 同级页面找到，或通过 Spark 平台入口访问）

**回复模板（参考）**：

> 您查看的应用中 `<日志文件名>` 这个日志文件，因为单个文件超过了 1.5GB，触发了机器上的大日志清理脚本（这是为了避免日志写满磁盘导致整机任务失败的保护机制），文件内容已被清空，**但这不影响任务运行**。
>
> 如果您需要查看任务的具体运行情况和指标，建议通过 **Spark History Server** 查看（包含 Stage、Task、Executor 等运行指标）。其他日志（如 stderr / stdout）我已经获取并分析。

#### 2A.3 输出扫描清单（强制 — 进入第 3 步前必须完成）

> [WARN] **此步骤是诊断流程中最容易踩坑的一步**：当应用日志被 log4j 滚动成多个文件、或用户改了 logger 名时，模型若只挑某一个"看起来最大/最像主日志"的文件去 grep，**极易漏掉真正包含失败信息的文件**。

**日志分组规则**：对 `log-list` 返回的所有 `size > 1` 的日志，按下表分类：

| 分组 | 识别规则 | 处理策略 |
|---|---|---|
| **标准容器日志** | 文件名 ∈ {`stderr`、`stdout`、`gc.log`（含轮转 `gc.log.0`、`gc.log.0.current` 等）、`syslog`、`hdfs.log`、`cpu_monitor.log`} | 每个文件独立纳入扫描清单 |
| **引擎应用日志组**（spark-group / driver-group / app-group / jobmanager-group / taskmanager-group） | 以 `spark`、`driver`、`app`、`jobmanager`、`taskmanager` 为前缀，且后缀只是 `.log` 或带日期/时间戳/序号（例如：`spark.log`、`spark-06-24-26-11-55-1.log`、`spark.log.2026-06-24-11`、`driver.log.1`、`jobmanager.log.0` 等） | **整组合并**为一个扫描组，**全部文件**纳入扫描清单 |
| **业务自定义日志** | 不属于上两类的其他 `size > 1` 文件 | ≤ 3 个：全部纳入扫描清单；> 3 个：列出名单告知用户，请用户指定关注哪些 |

**引擎应用日志组的扫描顺序（重要）**：组内的多个文件，按以下顺序扫描，**优先级从高到低**：

1. **current 文件**（不含日期/时间戳/序号后缀，例如 `spark.log` / `driver.log`）—— log4j 通常将最新的活跃日志写入 current 文件，**任务失败的关键 ERROR 通常在这里**
2. **时间戳最新的归档文件**（例如同组中 `spark-...-13-55-1.log` 比 `spark-...-11-55-1.log` 更新）
3. **序号最大的滚动文件**（例如 `driver.log.1`、`driver.log.2`，序号大通常更新；具体语义取决于 log4j 配置，无法 100% 判断时按时间戳/lastModified 排序）
4. 最旧的归档文件

> [FAIL] **严禁仅凭文件大小选扫描目标。** 35MB 的 `spark-...-11-55-1.log` 不一定包含失败信息——它可能只是任务正常运行阶段的大量 INFO 日志；而 3MB 的 `spark.log`（current）才是失败发生时的关键日志。
>
> [FAIL] **严禁因为同组里有 N 个文件就只挑一个扫**——首轮扫描必须**覆盖组内每个文件**（聚合扫描 `log-scan` 已自动做到），因为 ERROR 可能写在任何一个文件里（取决于失败时间是否跨过滚动点）。

**输出扫描清单格式**（在进入第 3 步前必须**显式列出**）：

```
本次诊断扫描清单（共 N 个文件）：
  标准容器日志：
    - stderr (8 KB)
    - stdout (0 B, skip)         ← size=0 跳过
    - gc.log (10 KB)
  spark-group（按 current → 时间戳新→旧 排序）：
    - spark.log (3.1 MB)         ← current，最优先
    - spark-06-24-26-13-55-1.log (6.9 MB)
    - spark-06-24-26-12-55-1.log (5.7 MB)
    - spark-06-24-26-11-55-1.log (35 MB, 最旧)
  业务自定义日志：（无）
```

进入第 3 步后，**首轮聚合扫描（详见 3.0，`log-scan --container-url ... --profile`）会自动覆盖清单中每个 size>1 文件的整套关键字**。

### 第 2B 步：峰峦平台层取数（engine = fengluan）

> [PIN] **峰峦核心差异**：
> 1. **没有 NodeManager**：日志由峰峦节点上的 logs 服务暴露，目录结构为 `/logs/{node_ip}/{pod_uid}/{容器名}/{文件}`
> 2. **每个 pod 都有独立日志根目录**：需先通过 dashboard 解析得到所有 pod 的 `log_url`
> 3. **日志接口不支持 `start`**：峰峦日志服务永远返回全文，本 skill 通过 `--tail-kb` 在客户端裁剪
> 4. **日志列表无 `size` 字段**：峰峦目录页无法返回文件大小，"size=1 跳过大日志清理"规则**不适用于峰峦**；要看文件大小只能通过 `fengluan-log-content` 返回的 `total_bytes`

#### 2B.1 解析 dashboard 获取所有 Pod

```bash
# 默认：返回所有 master(Driver) + 前 20 个 executor + 总数统计
do-bigdata yarn fengluan-dashboard --dashboard-url "{dashboard_url}" --query "<用户原始问题>"

# 仅看 Driver（首次定位 Spark 作业失败时优先这么做，避免上千 executor 撑爆上下文）
do-bigdata yarn fengluan-dashboard --dashboard-url "{dashboard_url}" --role master

# 精确查询某个 executor（推荐用法，比如从 Driver 日志中提取出 exec-37 报错）
do-bigdata yarn fengluan-dashboard --dashboard-url "{dashboard_url}" --pod-name "exec-37"

# 调大 executor 返回上限（默认 20；几十到上百个 executor 时酌情放大）
do-bigdata yarn fengluan-dashboard --dashboard-url "{dashboard_url}" --executor-limit 100
```

> [WARN] **大型 Spark 作业（上千 executor）的处理策略**：
> 1. **首次调用永远传 `--role master`**（只看 Driver，~1 个 pod，绝不超量）
> 2. 从 Driver 日志（3.1 步 grep）中定位出报错的 executor id（如 `Lost executor 37`、`container_xxx_000037`）
> 3. 再用 `--pod-name exec-37` 精确查询该 executor，拿到它的 `log_url` / `diagnosis_url`
>
> 切勿无脑用 `--executor-limit 9999` 把全部 executor 序列化到上下文。

**返回示例**：
```json
{
  "job_id": "livy-sessionid-31118986-...",
  "platform": "US-SUPERSQL",
  "dashboard_url": "http://21.24.99.122:8081/platforms/US-SUPERSQL/jobs/livy-...",
  "web_ui": "http://k8s-spark-history-server.tianqiong.woa.com/history/livy-...",
  "diagnosis_url": "http://21.24.99.79:8081/diagnosis/api/v1/platforms/US-SUPERSQL/jobs/livy-.../diagnosis?Debug=true&EngineName=spark",
  "state": "FINISHED",
  "master_count": 1,
  "executor_count": 1247,
  "executor_truncated": true,
  "filter": { "role": "all", "pod_name": null, "executor_limit": 20 },
  "pods": [
    {
      "name": "livy-sessionid-...-driver",
      "role": "master",
      "uid": "c607a5ae-caf9-4707-b559-9221d08c7ac4",
      "node_name": "node-29.98.142.14",
      "node_ip": "29.98.142.14",
      "state": "Terminating",
      "pod_ip": "29.98.140.74",
      "cluster": "tc-w4vdrcgq",
      "namespace": "fengluan-29365-offline",
      "log_url": "http://21.24.99.79:8081/logs/29.98.142.14/c607a5ae.../?jobID=...&podName=...&tenantCluster=tc-w4vdrcgq",
      "diagnosis_url": "http://21.24.99.79:8081/diagnosis/api/v1/clusters/tc-w4vdrcgq/namespaces/fengluan-29365-offline/pods/livy-.../diagnosis?EngineName=spark"
    },
    { "role": "executor", "...": "..." }
  ]
}
```

**字段分析要点**：
- `state`：作业整体状态（如 `FINISHED`）。**注意：dashboard 解析不返回 job 级 Severity / Reason / Suggestion**，若需诊断结论，用第 4 步 `fengluan-diagnosis` 传 `diagnosis_url` 获取（同 YARN SUCCEEDED 不等于内部成功，状态正常仍需看 pod 与日志确认）
- `master_count` / `executor_count`：作业实际的总 pod 数，**不受 `--executor-limit` / `--role` 影响**，用于评估是否需要精确查询
- `executor_truncated == true`：说明 executor 被截断了，**继续看 executor 必须用 `--pod-name` 精确查询**
- `pods`：master pod（Driver）排在前面，其余为 Executor。每个 pod 的 `state` 是 K8s 原生状态：
  - `state` ∈ {Running, Terminating, Terminated, ContainerCreating, ...}
- `log_url`：直接作为 2B.2 步的 `--log-url` 参数
- `diagnosis_url`：pod 级诊断 API，作为第 4 步的 `--diagnosis-url` 参数

> [TIP] **诊断数据有 TTL，但 AM 日志是持久的**：峰峦 dashboard 和 diagnosis API 的数据只在任务结束后保留一段时间（典型为数小时～1 天），过期后 `fengluan-dashboard` 可能返回空 `pods` / `fengluan-diagnosis` 返回 `{Result:"failed", Reason:"... no longer exists or has been expired"}`。这种情况下：
>
> - 直接跳过 2B.1（dashboard）与第 4 步（K8s 诊断），**用第 1 步 `app-info` 返回的 `am_container_logs`（Driver Pod 日志 URL）直接调 `fengluan-log-list` 进入 2B.2**
> - 代价：拿不到 Driver Pod 的 `diagnosis_url`，即 K8s 层面的 Events / ExitCodes / OOMKilled 标记看不到了。只能从 Driver 应用日志推断根因

#### 2B.2 列出 Driver Pod 的日志文件

**首次定位时只对 master pod（Driver）调用**：

```bash
do-bigdata yarn fengluan-log-list --log-url "{driver_pod.log_url}" --query "<用户原始问题>"
```

**返回示例**：
```json
{
  "files": [
    {"name": "spark-kubernetes-driver/stderr",   "url": "http://21.24.99.79:8081/logs/.../spark-kubernetes-driver/stderr?..."},
    {"name": "spark-kubernetes-driver/stdout",   "url": "..."},
    {"name": "spark-kubernetes-driver/spark.log","url": "..."},
    {"name": "spark-kubernetes-driver/gc.log",   "url": "..."}
  ]
}
```

> [PIN] **目录层级**：峰峦的日志按容器名分子目录，driver pod 下通常是 `spark-kubernetes-driver/{stderr,stdout,spark.log,gc.log,...}`，executor pod 下是 `spark-kubernetes-executor/{stderr,stdout,spark.log,...}`。`fengluan-log-list` 已自动递归。
>
> [WARN] **与 YARN 的差异**：峰峦日志列表**没有 size 字段**——目前无法从目录页直接拿到文件大小，只能通过 `fengluan-log-content` 返回的 `total_bytes` 字段获取。因此 YARN 分支中"size=1 跳过大日志清理"的规则**不适用于峰峦**。

> [ALERT] **Pod 未启动成功的处理（重要）**：如果 `fengluan-dashboard` 返回的 Driver pod 状态为 `Pending` / `ContainerCreating` 而非 `Running` / `Terminating` / `Terminated`，或 `fengluan-log-list` 返回的 `files` 数组为空 —— 说明 **Driver Pod 从未启动成功**，此时**没有 pod 日志可读**。
>
> 遇到这种情况：
> 1. **跳过 3.0 首轮扫描与 3.1.x 引擎层诊断**（无日志可扫）
> 2. **直接跳到第 4 步 `fengluan-diagnosis`**，用 pod 级 `diagnosis_url` 获取 K8s 层面的启动失败原因（`FailedMount` / `FailedScheduling` / `ImagePullBackOff` / `FailedToCreatePodRelatedObjects` 等）
> 3. 常见根因：跨地域 ceph 挂载失败（详见 `yarn_log_patterns.md` 第 14 章）、镜像拉取失败、资源不足调度失败、依赖 secret 缺失

#### 2B.3 输出扫描清单（强制 — 进入第 3 步前必须完成）

与 2A.3 同样的强制要求：**进入第 3 步前必须显式列出扫描清单**。峰峦的清单规则**与 YARN 一致**（参见 2A.3 的分组规则），唯一差异：

- **无 size 字段**：清单只列文件名，无法标注大小；扫描时对所有文件一律纳入，不做 size=0/size=1 过滤
- **滚动归档处理与 YARN 完全一致**：spark-group 内多个文件全部纳入，按 current → 时间戳新→旧 排序

**输出扫描清单格式**：

```
本次诊断扫描清单（共 N 个文件，Driver Pod）：
  标准日志：
    - spark-kubernetes-driver/stderr
    - spark-kubernetes-driver/stdout
    - spark-kubernetes-driver/gc.log
  spark-group（按 current → 时间戳新→旧 排序）：
    - spark-kubernetes-driver/spark.log              ← current，最优先
    - spark-kubernetes-driver/spark.log.2026-06-24-13
    - spark-kubernetes-driver/spark.log.2026-06-24-12
  业务自定义日志：（无）
```

进入第 3 步后，**首轮聚合扫描（详见 3.0，`fengluan-log-scan --log-url ... --profile`）会自动递归覆盖 pod 下每个日志文件的整套关键字**。

---

## 第 3 步：引擎层诊断（与平台无关）

> * **本步骤的核心原则**：到本步骤为止，已经拿到了 **Driver 的日志扫描清单**（YARN 走 container-log-*，峰峦走 fengluan-log-*）。**Spark 引擎层的故障模式与平台无关**——Driver/Executor 概念一致、Stage 重试机制一致、OOM/FetchFailed 表现一致。下面的诊断流程同时适用于 YARN 与峰峦，只在 CLI 命令上稍有差异（YARN 用 `log-content`，峰峦用 `fengluan-log-content --grep`），关键字与判定规则完全相同。

### 3.0 首轮错误全面扫描（强制执行）

> [WARN] 在第 2A.3 / 2B.3 输出扫描清单后、深入分析前，**必须先对清单中所有 size>1（或峰峦的全部）文件执行一轮系统化的错误扫描**。这是诊断流程中最关键的一步，目的是快速全面地捕获所有错误信息，避免遗漏关键异常。

#### 3.0.1 首轮聚合扫描命令（按平台，一次调用完成）

> [ROCKET] **首选做法：用聚合扫描命令 `log-scan` / `fengluan-log-scan` 一次完成整个容器 / Pod 的全量扫描**，无需再对每个文件、每个关键字分别发起 grep。聚合扫描会：自动列出容器下全部 size>1 文件（峰峦递归列出 pod 全部日志文件）→ 对每个文件并行执行整套 `--profile` 关键字正则扫描 → 返回按 **文件 × 关键字** 聚合的紧凑命中摘要（计数 + Top-N 样例行 + 上下文）。

> [WARN] **必须带 `--out-file auto`（重要）**：聚合扫描命中多时完整 JSON 体积很大，部分 agent 框架会截断命令行 stdout（如 `stdout truncated to 51200 bytes`），导致返回 JSON 残缺无法解析。因此 `log-scan` / `fengluan-log-scan` **默认一律加 `--out-file auto`**：stdout 只保留渲染摘要 + 落盘文件绝对路径，再按需用 `read_file` 无截断读取全量结果（详见前文「大输出落盘」小节）。

**YARN 平台**（一条命令扫完整个容器）：

```bash
# Spark 应用：用 spark profile（含 ERROR/Exception/FATAL/Error/Traceback/FAILED + Aborting job / Job aborted due to stage failure）
do-bigdata yarn log-scan --container-url "{am_container_logs}" --profile spark --out-file auto --query "<用户原始问题>"

# 非 Spark（MapReduce/Flink/未知）：用 generic profile（6 个通用错误关键字）
do-bigdata yarn log-scan --container-url "{am_container_logs}" --profile generic --out-file auto
```

**峰峦平台**（一条命令递归扫完整个 Driver Pod）：

```bash
do-bigdata yarn fengluan-log-scan --log-url "{driver_pod.log_url}" --profile spark --tail-kb 40960 --out-file auto --query "<用户原始问题>"
```

> [TIP] 也可显式指定文件子集：YARN 用可重复的 `--log-url`，峰峦用可重复的 `--file-url`（不传 `--container-url`/`--log-url` 时生效）。

**profile → 关键字集**（YARN/峰峦相同）：

| profile | 关键字 | 适用 |
|---|---|---|
| `generic` | `ERROR` / `Exception` / `FATAL` / `Error` / `Traceback` / `FAILED` | MapReduce / Flink / 未知引擎 |
| `spark` | generic 全部 + `Aborting job` / `Job aborted due to stage failure` | Spark 应用（YARN app_type=SPARK 或峰峦全部） |
| `python` | `Traceback` / `SyntaxError` / `ImportError` / `ModuleNotFoundError` / `NameError` / `TypeError` / `IndentationError` / `FileNotFoundError` / `AttributeError` / `ValueError` | PySpark / Python 专项（见 3.1.2） |

- `Aborting job` / `Job aborted due to stage failure`（spark profile 独有）用于捕获 **即便 YARN/峰峦 SUCCEEDED 也可能存在的隐藏 Stage 失败**，命中后进入 3.1.1 做 Stage 级深挖。

#### 3.0.2 覆盖原则与结果解读（YARN 与峰峦通用）

> [PIN] **覆盖原则**：聚合扫描已自动覆盖清单中**每一个 size>1 文件 × 整套关键字**，无需手动逐文件逐关键字发起请求。若因故只能用 `log-content` / `fengluan-log-content` 单文件扫描，则仍须对清单中**每个文件**都执行、且用正则 `ERROR|Exception|FATAL|Error|Traceback|FAILED`（Spark 再加 `|Aborting job|Job aborted due to stage failure`）**一次覆盖整套关键字**，严禁一个关键字发一次请求。
>
> [FAIL] **严禁只挑某一个"最像主日志"或"最大"的文件扫描**——35MB 的 `spark-...-11-55-1.log`（最旧的归档）可能全是 INFO，而 3MB 的 `spark.log`（current）才是失败时刻的 ERROR。聚合扫描已保证全覆盖，不要再手动缩小到单文件。
>
> [FAIL] **严禁因为某个文件命中就忽略其他文件**——可能 stderr 看到 `ExecutorLostFailure`，spark.log 看到真正的 `Job aborted due to stage failure: ... FetchFailedException`。聚合结果里要**通读每个文件的 hits**，拼出完整因果链。

**聚合结果解读要点**：
1. **优先看 `Traceback` / `Exception` 组的样例**：Python Traceback 与 Java Exception 通常含最直接的根因。
2. **关注因果链**：样例中出现 `Caused by:` 时，进入 3.1.1 深挖追到最内层。
3. **关注时间顺序**：`line_no` 最小（最早）的命中通常是根因，后续多为连锁反应；每个关键字的样例默认已保留"最早若干条 + 最后一条"。
4. **命中截断（truncated）处理**：某关键字 `truncated=true` 说明命中数超过样例上限、只回了 Top-N 样例——这本身就是"该类错误大量出现"的强信号；如需看全部命中，再对**该文件**用 `log-content --grep "<该关键字>" --max-matches 500 --context 3` 精确追查（见 3.0.3）。

> [WARN] **不要跳过首轮扫描直接去读日志尾部。** 很多关键错误（如 Python 的 SyntaxError、ImportError）可能出现在日志中间而非末尾，仅读尾部很容易遗漏。聚合扫描 / 正则全量 grep 覆盖全量日志，确保不遗漏。**只有在首轮扫描完全无命中时**，才回退到 `log-content` / `fengluan-log-content --tail-kb` 直接读尾部。

#### 3.0.3 第二批：按线索追加搜索（正则多关键字单次调用）

根据首轮聚合扫描发现的线索，针对性地对**命中的文件**追加搜索。**每类线索用一次正则多关键字调用完成**（`--grep "A|B|C"`），并用 `--context` 带回上下文、`--max-matches` 控制返回体积：

| 如果首轮发现... | 则对命中文件执行（一次正则调用） |
|---|---|
| Java OOM 相关异常 | `--grep "OutOfMemoryError|heap space|killed by YARN"` |
| Python 异常（Traceback/Error） | 进入 3.1.2 「PySpark / Python 专项」（用 `--profile python` 或 python 关键字正则） |
| Executor 失败信息 | `--grep "ExecutorLostFailure|Container exited|Lost executor|Max number of executor"` |
| Spark Stage 失败（Aborting job / Job aborted due to stage failure 任一命中） | 进入 3.1.1 「Spark Stage 失败深挖」 |
| 连接/网络问题 | `--grep "Connection refused|SocketTimeoutException|RpcEndpointNotFoundException"` |
| 权限问题 | `--grep "AccessControlException|Permission denied"` |
| 文件/路径问题 | `--grep "FileNotFoundException|Path does not exist|No such file"` |
| `submitSql has error` 或类似 | `--grep "submitSql|PythonRunner|HiveContextManager"` |

**示例**（YARN，一次调用覆盖一整类线索并带 3 行上下文）：
```bash
do-bigdata yarn log-content --log-url "{spark.log_url}" --start 40960000 \
  --grep "ExecutorLostFailure|Container exited|Lost executor|Max number of executor" --context 3
```

**结果分析原则**：
1. **优先关注 Traceback 和 Exception**：同时命中多种错误时，Python Traceback 和 Java Exception 通常含最直接根因。
2. **关注因果链**：发现 `Caused by:` 链，追踪到最内层 `Caused by` 通常就是根因。
3. **关注时间顺序**：最早出现的错误通常是根因。
4. **命中过多（truncated）时收敛**：先用更具体的正则缩小范围，或用 `--max-matches` + `--context` 拿关键片段；必要时缩小 `--start` / `--tail-kb` 到更靠近失败时刻的区间。

### 3.1 Spark 应用专项（YARN + 峰峦共用）

> [WARN] **Spark 内部失败检测（必须执行，即使 YARN/峰峦状态为 SUCCEEDED）**：Spark SQL 应用（尤其通过 Livy 提交的交互式 Session）可能内部某条 SQL 的 Stage 失败后，Livy 层捕获异常继续运行，最终任务状态置为 SUCCEEDED。仅依赖任务状态、或仅扫单个日志文件，**都无法发现这类隐藏失败**。3.0 首轮扫描的 `Aborting job` / `Job aborted due to stage failure` 关键字就是为捕获此类隐藏失败设计的。

#### 3.1.1 Stage 失败深挖

当 3.0 首轮扫描中 `Aborting job` 或 `Job aborted due to stage failure` 在任一文件中命中，继续对**命中的 spark-group 文件 + stderr** 追加一次正则多关键字调用获取详细失败信息（关键字 YARN/峰峦相同，CLI 命令按平台）：

**YARN 平台**（对每个命中文件更换 `--log-url`，一次正则覆盖整组关键字）：
```bash
do-bigdata yarn log-content --log-url "{spark.log_url}" --start 40960000 --context 5 \
  --grep "ERROR|Lost task|Caused by|FetchFailedException|ResultStage.*failed|has failed the maximum allowable number of times|TypeError|PythonException"
```

**峰峦平台**（对每个命中文件更换 `--log-url`）：
```bash
do-bigdata yarn fengluan-log-content --log-url "{driver_pod}/spark-kubernetes-driver/spark.log" --tail-kb 40960 --context 5 \
  --grep "ERROR|Lost task|Caused by|FetchFailedException|ResultStage|has failed the maximum allowable number of times|TypeError|PythonException"
```

> [TIP] `--context 5` 让每个命中带回前后 5 行上下文，便于一次看清异常栈与因果链，避免"命中后再读一轮上下文"的额外往返。

关键字说明：
- `ERROR` — 错误级别日志
- `Lost task` — Task 失败详情（节点、Executor、TID）
- `Caused by` — 异常因果链
- `FetchFailedException` — Shuffle 拉取失败（最常见 Stage 失败根因，见 `yarn_log_patterns.md` 4.3）
- `ResultStage.*failed` — ResultStage 失败详情
- `has failed the maximum allowable number of times` — 4 次重试全失败的确认信号
- `TypeError` / `PythonException` — 涉及 Python UDF 时的 Python 异常

**典型 case**：

```
日志列表（Driver 扫描清单）：
  spark.log                    : 3.1 MB   ← current（活跃文件）
  spark-06-24-26-13-55-1.log   : 6.9 MB   ← 13 点滚动
  spark-06-24-26-12-55-1.log   : 5.7 MB   ← 12 点滚动
  spark-06-24-26-11-55-1.log   : 35 MB    ← 11 点滚动（最大但最旧）
  stderr                       : 8 KB
  stdout                       : 0

[FAIL] 错误做法：只挑 35MB 的 spark-...-11-55-1.log 扫 ERROR → 0 命中 → 结论"无失败"
[OK] 正确做法：对上述 spark-group 全部 4 个文件 + stderr 共 5 个文件并行扫
   → spark.log 命中：
     [14:26:39] ERROR FileFormatWriter: Aborting job 0f268200-...
     org.apache.spark.SparkException: Job aborted due to stage failure:
       ResultStage 10 (sql at SqlJob.java:135) has failed the maximum allowable number of times: 4.
       Most recent failure reason: org.apache.spark.shuffle.FetchFailedException
   → 实际是 Stage 因 Shuffle Fetch 失败被中止，详见 yarn_log_patterns.md 9.1 / 4.3
```

#### 3.1.2 PySpark / Python 应用专项检查

当识别到应用涉及 Python 代码时（日志中出现 `PythonRunner`、`submitPythonSql`、`pyspark`、`.py` 文件名等线索），**必须额外执行 Python 专项搜索**。有两种等效做法，任选其一：

**做法一（推荐）：用 `--profile python` 聚合扫描一次覆盖整套 Python 异常关键字**
```bash
# YARN：对 stderr / stdout 所在容器聚合扫描
do-bigdata yarn log-scan --container-url "{am_container_logs}" --profile python --out-file auto
# 峰峦：递归扫 driver pod
do-bigdata yarn fengluan-log-scan --log-url "{driver_pod.log_url}" --profile python --tail-kb 40960 --out-file auto
```

**做法二：对 stderr / stdout 用一次正则多关键字 `log-content` / `fengluan-log-content`**

**Python 关键字清单（YARN/峰峦相同）**：`Traceback` / `SyntaxError` / `ImportError` / `ModuleNotFoundError` / `NameError` / `TypeError` / `IndentationError` / `FileNotFoundError` / `AttributeError` / `ValueError`（另可加 `from.*import` 定位 import 行、`File.*line` 定位异常出处）。

**YARN 平台**（对 stderr、stdout 各一次调用）：
```bash
do-bigdata yarn log-content --log-url "{stderr_url}" --start 40960000 --context 5 \
  --grep "Traceback|SyntaxError|ImportError|ModuleNotFoundError|NameError|TypeError|IndentationError|FileNotFoundError|AttributeError|ValueError"
```

**峰峦平台**（对 driver 的 stderr、stdout 各一次调用）：
```bash
do-bigdata yarn fengluan-log-content --log-url "{driver_pod}/spark-kubernetes-driver/stderr" --tail-kb 40960 --context 5 \
  --grep "Traceback|SyntaxError|ImportError|ModuleNotFoundError|NameError|TypeError|IndentationError|FileNotFoundError|AttributeError|ValueError"
```

**PySpark 应用快速失败的典型模式**：
- 应用启动后秒级失败（< 30 秒），且无 Executor 被分配 → 大概率是 Driver 端 Python 代码加载阶段就失败了（如 SyntaxError、ImportError）
- 这类错误的关键信息通常在 stderr 或 stdout 中，且可能出现在日志中间位置而非末尾
- **必须通过 grep 全量扫描定位**，不能仅靠尾部读取

#### 3.1.3 Driver Full GC 联动诊断

> [WARN] **Executor 失败达上限时，必须同时检查 Driver 的 GC 日志**
>
> 当诊断结果指向 `Max number of executor failures (N) reached` / 大量 `ExecutorLostFailure` 时，**除了获取失败 Executor 日志外，必须检查 Driver 容器/Pod 的 GC 日志**，确认 Driver 端是否存在严重的 Full GC 问题。
>
> **原因**：Driver 端严重的 Full GC 会导致以下连锁问题：
> 1. Driver 长时间 STW（Stop-The-World），无法及时处理 Executor 的心跳和 RPC 请求
> 2. Executor 因无法与 Driver 通信而被判定为丢失（`ExecutorLostFailure`）
> 3. 大量 Executor 集中失败，快速触发 `max.executor.failures` 上限
> 4. 此时 Executor 本身可能并无问题，**根因在 Driver 端的 GC 压力**

**检查方法**：

1. 在 2A.3 / 2B.3 扫描清单中查找 `gc.log`（或 `gc.log.0`、`gc.log.0.current` 等 GC 日志文件）
2. 获取 GC 日志内容并搜索 Full GC 记录：

**YARN 平台**：
```bash
do-bigdata yarn log-content --log-url "{gc.log_url}" --start 40960000 --grep "Full GC"
```

**峰峦平台**：
```bash
do-bigdata yarn fengluan-log-content --log-url "{driver_pod}/spark-kubernetes-driver/gc.log" --tail-kb 40960 --grep "Full GC"
```

3. **判定标准**：
   - 单次 Full GC 暂停时间 > 10 秒 → 严重
   - Full GC 累计次数 ≥ 5 次 → 频繁
   - 连续多次 Full GC 且回收后堆使用率仍 > 80% → 内存严重不足

4. 如确认存在严重 Full GC，在诊断报告中应标注 **Driver 端 GC 压力是导致 Executor 集中失败的根因或重要因素**，并给出 Driver 端的内存和 GC 调优建议（参见 `references/yarn_log_patterns.md` 中 "9.4 Executor 累计失败次数达上限" 的 Driver GC 诊断部分）

#### 3.1.4 Executor / 非 Driver Pod 深度分析

在以下场景需要查看 Executor / TaskManager / 其他 Container 的日志：

- Driver 日志显示 `Max number of executor failures (N) reached`，但未包含具体 Executor 失败原因
- Driver 日志显示 `ExecutorLostFailure` 但未给出详细 exit code 或异常栈
- Driver 日志显示 Container/Pod 退出但原因不明
- 需要分析特定 Task 在某个 Executor 上的失败详情

**统一流程**（与平台无关 — 一旦拿到 Executor 日志 URL，后续操作与 Driver 完全一致）：

**Step A（共性）：从 Driver 日志中定位失败 Executor 信息**

在 Driver 的关键日志（stderr、spark.log、stdout）中搜索以下关键字，找到失败 Executor 对应的标识：

| 平台 | grep 命令（一次正则多关键字） |
|---|---|
| YARN | `do-bigdata yarn log-content --log-url "{stderr_url}" --start 40960000 --context 3 --grep "ExecutorLostFailure|Container exited|container_e|Lost executor"` |
| 峰峦 | `do-bigdata yarn fengluan-log-content --log-url "{driver_pod}/spark-kubernetes-driver/stderr" --tail-kb 40960 --context 3 --grep "ExecutorLostFailure|Lost executor|-exec-"` |

**需要从日志中提取的关键信息**：

| 平台 | 提取目标 |
|---|---|
| YARN | ① 失败 Executor 的 **Container ID**（格式 `container_e{epoch}_{cluster_timestamp}_{app_number}_{attempt}_{container_number}`，例如 `container_e704_1757659972062_13336918_01_000025`，AM 容器为 `000001`，Executor 从 `000002` 开始递增）<br>② **NodeManager 节点 IP/hostname**（日志中 `host: x.x.x.x` 或 `on host x.x.x.x` 形式） |
| 峰峦 | **Executor 编号**（如 `Lost executor 37`、`...-exec-37`） |

**示例**：

YARN Driver 日志中：
```
Container exited with a non-zero exit code 137. Container id: container_e704_1757659972062_13336918_01_000025 on host: 9.134.56.78
Lost executor 24 (already removed): Container container_e704_1757659972062_13336918_01_000025 ... was preempted.
```
→ Container ID = `container_e704_..._000025`，NodeManager IP = `9.134.56.78`

峰峦 Driver 日志中：
```
Lost executor 37 (already removed): Container marked as failed: ...-exec-37
```
→ Executor 编号 = `37`，对应 pod 名后缀 `-exec-37`

**Step B（平台特定）：拿到 Executor 日志的 URL/入口**

| 平台 | 获取 Executor 日志入口 |
|---|---|
| **YARN** | 自行构造 URL：取 AM 日志链接作为模板 `http://{nm_ip}:{port}/node/containerlogs/{container_id}/{user}`，把 `{nm_ip}` 替换为 Executor 节点 IP，把 `{container_id}` 替换为 Executor Container ID，`{port}` 和 `{user}` 与 AM 链接一致 |
| **峰峦** | 回到 2B.1 步用 `--pod-name`：`do-bigdata yarn fengluan-dashboard --dashboard-url "{dashboard_url}" --pod-name "exec-37"` → 拿到 executor pod 的 `log_url` 与 `diagnosis_url` |

> * **关键认知**：YARN 的 Executor 日志 URL 不会被任何接口直接返回，必须从 AM 日志中提取信息后自行构造；而峰峦的 Executor pod 信息存在 dashboard 中，通过 `--pod-name` 反查即可。**这是两个平台在 Executor 深挖上的唯一差异**，一旦拿到入口，后续 Step C 完全一致。

**Step C（共性）：获取并分析 Executor 日志**

拿到 Executor 日志入口后，**流程与 Driver 完全一致**：

| 操作 | YARN | 峰峦 |
|---|---|---|
| 列日志文件 | `log-list --container-url "{executor_url}"` | `fengluan-log-list --log-url "{executor_pod.log_url}"` |
| 输出扫描清单 | 同 2A.3（含 size=1 识别） | 同 2B.3 |
| 首轮聚合扫描 | `log-scan --container-url "{executor_url}" --profile spark --out-file auto`（一次扫完该 Executor 容器全部文件） | `fengluan-log-scan --log-url "{executor_pod.log_url}" --profile spark --out-file auto` |
| 看尾部 | `log-content --log-url URL --start 8192` | `fengluan-log-content --tail-kb 8` |
| 读上下文 | `log-content --log-url URL --start 65536` | `fengluan-log-content --tail-kb 64` |

**Executor 日志关键字判定**（YARN/峰峦相同）：
- `java.lang.OutOfMemoryError` — Executor 内存不足
- `Container killed by YARN for exceeding memory limits` — YARN 物理内存超限
- `exit code 137` — 被 OOM-killer 或 YARN 抢占杀死（峰峦上同样意义）
- `exit code 143` — 收到 SIGTERM（正常终止或超时）
- `FetchFailedException` — Shuffle 数据拉取失败
- `Executor heartbeat timed out` — GC 暂停导致心跳超时

**注意事项**：
- 优先选择最近一次失败的 Executor（YARN container_number 较大的；峰峦 exec 编号较大的）进行分析
- 如果多个 Executor 失败原因可能不同，可选取 2-3 个不同的 Executor 做对比分析
- 如果从 Driver 日志中无法提取到 Executor 标识，应告知用户并请求提供相关信息
- Executor 的日志可能因 Container/Pod 已被清理而无法获取（YARN 日志过期 / 峰峦 pod 已 GC）：
  - **YARN**：告知用户日志不可用即可
  - **峰峦**：如果 executor pod 的 `log_url` 为空，或 `fengluan-log-list` 返回空 `files`，或 `fengluan-log-content` 内容为空 —— **不要就此止步**，改用第 4 步 `fengluan-diagnosis` 传该 executor pod 的 `diagnosis_url`，通过 K8s 层面的 `ExitCodes` / `Events` / `Messages` 拿到失败原因（如 `OOMKilled` / `Evicted` / `FailedMount` 等）

### 3.2 MapReduce 应用（仅 YARN）

1. **stderr** — AM 异常信息
2. **stdout** — 任务输出
3. **syslog** — 系统日志，包含详细的 Task 执行信息

首轮扫描用 `log-scan --profile generic` 一次覆盖整组文件。

### 3.3 Flink 应用（仅 YARN）

1. **jobmanager-group**（`jobmanager.log` 及其滚动归档 `jobmanager.log.0`、`jobmanager.log.1` 等）— JobManager 日志，包含作业提交和调度异常；聚合扫描会自动覆盖整组
2. **stderr** — JVM 级别错误
3. **gc.log** — GC 分析

首轮扫描用 `log-scan --profile generic` 一次覆盖整组文件（无需 Spark 专项关键字）。

### 3.4 通用策略（未知引擎）

对于未知引擎类型或自定义日志名，先获取 `stderr` 和 `stdout`，再根据日志列表中的文件名逐步排查。首轮扫描用 `log-scan --profile generic` 执行。

---

## 第 4 步：K8s 级深度诊断（仅峰峦，按需）

> * **使用时机（三种触发场景）**：`fengluan-diagnosis` **不是每次都要调**，只在以下三种场景之一才调用：
>
> **场景 A：Pod 未启动成功 → 调 pod 级 diagnosis**
> - 触发：第 2B 步 `fengluan-dashboard` 显示 Driver pod 状态为 `Pending` / `ContainerCreating`，或 `fengluan-log-list` 返回 `files` 为空
> - 无 pod 日志可读，此时**必须**通过 pod 级 `diagnosis_url` 拿 K8s Events（`FailedMount` / `FailedScheduling` / `ImagePullBackOff` 等）
> - 典型故障：**跨地域 ceph 挂载失败**（详见 `yarn_log_patterns.md` 第 14 章）、镜像拉取失败、资源不足调度失败
>
> **场景 B：Executor Pod 日志缺失 → 调该 executor 的 pod 级 diagnosis**
> - 触发：3.1.4 Executor 深挖时，某个 executor pod 的 `log_url` 为空 / `fengluan-log-list` 返回空 / `fengluan-log-content` 内容为空
> - Pod 已被 K8s GC 或从未产生日志，此时用该 executor 的 `diagnosis_url` 拿 K8s 层信号（`OOMKilled` + `ExitCode: 137` / `Evicted` 等）
>
> **场景 C：Driver + Executor 日志分析都无法定位根因 → 调 job 级 diagnosis**
> - 触发：3.0/3.1 首轮扫描 + Driver 日志 + Executor 日志都完成了，但**依然无法定位根因**（如日志中只有资源耗尽的 warning 但无明确失败点）
> - 调 job 级 `diagnosis_url` 让峰峦平台判断"是不是集群侧问题"（Severity/Suggestion/Reason 由峰峦运维方沉淀）

**调用命令**：

```bash
# Pod 级诊断（含 ExitCodes、K8s Events、状态时间线）— 场景 A / B
do-bigdata yarn fengluan-diagnosis --diagnosis-url "{pod.diagnosis_url}" --query "<用户原始问题>"

# Job 级诊断（含全部 pod 概览）— 场景 C
do-bigdata yarn fengluan-diagnosis --diagnosis-url "{job_diagnosis_url}" --query "<用户原始问题>"
```

> [WARN] **同一个命令支持两种 URL，但返回结构差异显著，按需选用**：
>
> | URL 类型 | 顶层结构 | 典型用途 |
> |---|---|---|
> | **job 级** | `Diagnosis.Pods{}` + 高层 `Severity/Reason` | 看作业整体状况 + 各 pod 概要 |
> | **pod 级** | `Diagnosis.Events.{ExitCodes,Events,Messages}` | 深挖单个 pod 的 K8s 级失败（OOMKilled / 调度失败 / 镜像拉取） |
> | **pod 已过期** | `{Result:"failed", Reason:"pod ... no longer exists or has been expired"}` | pod 已被 K8s GC，需降级查 job 级 |
>
> Job 级**无 `Events` 字段**——要看 ExitCodes / K8s Events，必须用具体 pod 的 `diagnosis_url`。

**返回结构化字段（已自动反序列化）**：
- `Diagnosis.Severity` / `Suggestion` / `Reason`：峰峦平台给出的高层诊断结论
- `Diagnosis.Pods.{pod_name}`（**仅 job 级**）：每个 pod 的概要 `Severity/Suggestion/IsMaster/Reason`
- `Diagnosis.Events.ExitCodes.Containers.{container_name}`（**仅 pod 级**）：容器退出码、终止原因（如 `Reason: OOMKilled`、`ExitCode: 137`）
- `Diagnosis.Events.Events.{Image,Kubelet,Scheduling,Sync}`（**仅 pod 级**）：K8s 事件流，含镜像拉取/容器启动/调度/同步 4 类
- `Diagnosis.Events.Messages`（**仅 pod 级**）：峰峦给出的"看哪里"提示

**关键判定（pod 级专属）**：
- `ExitCodes.Containers.{x}.ExitCode == 137` + `Reason == "OOMKilled"` → **容器被 K8s OOM-killer 杀掉**（典型内存超限）
- `ExitCodes.Containers.{x}.ExitCode == 143` → 收到 SIGTERM（正常终止或超时）
- `Events.Scheduling` 中包含 `FailedScheduling` → 资源/亲和性导致无法调度
- `Events.Sync` 中包含 `FailedToCreatePodRelatedObjects` → 平台层依赖资源（如 secret、token）创建失败
- `Events.Image` 中包含 `Failed` / `ErrImagePull` → 镜像拉取失败

**过期识别（pod 级专属）**：
- 返回 `{Result:"failed", Reason:"pod item (... ) no longer exists or has been expired"}` 时：
  - CLI 会自动识别并给出 [WARN] 提示
  - **兜底链（按顺序尝试，不要一过期就向用户报失败）**：
    1. **优先降级查 job 级 `diagnosis_url`**（`app-info` 返回的 `diagnosis_api` 字段；或 2B.1 `fengluan-dashboard` 返回的顶层 `diagnosis_url`）—— job 级数据保留时间通常比 pod 级长，能拿到作业整体 Severity/Reason 和各 pod 概要
    2. job 级也过期或无该 pod 时，回到 `app-info` 取 `am_container_logs`（即 Driver Pod 日志 URL），**直接走第 3 步分析 Driver 应用日志**；注意此路径拿不到 K8s 层面的 ExitCodes / OOMKilled 标记，只能从应用日志推断
    3. 全部为空时（无 dashboard、无 `am_container_logs`），才告知用户数据已全部过期并请求其他线索

**常见 K8s 级失败模式速查**：

| 关键信号 | 根因 | 深度参考 |
|---|---|---|
| `FailedMount` + `Unable to attach or mount volumes` + `timed out waiting for the condition` | **跨地域 ceph 挂载**（Pod 卡 Pending） | `yarn_log_patterns.md` **第 14 章**（含地域推导规则、修复模板） |
| `FailedMount` + `secret ... not found` / `configmap ... not found` | 平台层 secret / configmap 缺失 | 联系平台方检查 secret 下发 |
| `FailedScheduling` + `Insufficient cpu/memory` | 集群资源不足 | 建议缩小 pod resource request 或换集群 |
| `ImagePullBackOff` / `ErrImagePull` | 镜像拉取失败 | 检查镜像是否存在、镜像仓库鉴权 |
| `OOMKilled` + `ExitCode: 137` | 容器内存超 K8s limit | 提高 spark.executor.memory / driver.memory |
| `Evicted` | 节点资源压力驱逐（主要是磁盘/内存） | 优化 shuffle/临时数据、降低单 pod 压力 |
| `FailedToCreatePodRelatedObjects` | 平台层依赖资源（如 token / cert）创建失败 | 联系平台方 |

> [TIP] **判定 FailedMount 是否为跨地域 ceph 时**：读第 1 步 `app-info` 返回的 `cluster_info.allowed_ceph_locations` 字段（形如 `["qy", "gz"]`），询问用户实际使用的 ceph 卷地域，两者不匹配即可确认。修复模板见 `yarn_log_patterns.md` 14.4。

---

## 第 5 步：知识库检索（辅助诊断）

当任务类型是 Spark 时（YARN 上 `app_type == "SPARK"` 或峰峦全部），或者日志中有 Spark 相关的内容时，使用知识库检索命令获取历史诊断案例作为辅助参考。

**触发条件**：根据第 3 步首轮扫描结果中出现的错误特征判断，是否是 Spark 任务。

**调用方式**：
```bash
do-bigdata yarn knowledge-search --query "<核心错误特征>"
```

**查询构造**：从首轮扫描结果中提取最核心的错误特征作为 query 参数。例如：
- `java.lang.OutOfMemoryError: Java heap space`
- `ExecutorLostFailure: Executor heartbeat timed out`
- `FetchFailedException: Failed to connect`
- `OOMKilled` + `ExitCode: 137`（峰峦 K8s 级失败）

**约束**：
- 单次诊断中 `knowledge-search` **最多调用 3 次**，超过后不再调用，直接基于已有信息进行分析
- 每次检索应使用不同的核心错误特征，避免重复查询
- 检索结果作为**辅助参考**纳入第 6 步根因分析，不替代基于 `yarn_log_patterns.md` 的模式匹配分析
- 如果检索服务不可用（返回错误），跳过此步骤继续诊断，不阻塞流程

---

## 第 6 步：根因分析与诊断报告

基于获取到的日志内容，对照 `references/yarn_log_patterns.md` 中的异常模式进行匹配分析。**异常模式库 YARN/峰峦共用**——库中关于 Spark 引擎的失败模式（OOM/Stage 失败/Executor Lost/Driver GC/PySpark 异常 等）同时适用于 YARN 与峰峦上的 Spark 应用；峰峦独有的 K8s 级判定（OOMKilled/Evicted/FailedScheduling）由第 4 步的 `fengluan-diagnosis` 提供。

**诊断报告格式**：

### 6.1 YARN 应用报告模板（engine=yarn）

```
## YARN Application 诊断报告

### 基础信息
- Application ID: {app_id}
- 应用名称: {name}
- 提交用户: {user}
- 应用类型: {app_type}
- 状态: {state} / {final_status}
- 执行耗时: {elapsed_time}

### 诊断结论
{一句话概述失败根因}

### 详细分析
{分步骤的分析过程，引用关键日志片段}

### 修复建议
{从用户（app 维护者）角度给出的具体修复步骤和参数调整建议。所有建议必须是用户在提交任务时可自主操作的，如调整 Spark/MR/Flink 配置参数、修改代码逻辑、优化 SQL 等。不要给出需要集群运维权限的建议（如修改 YARN/NodeManager 集群配置、登录集群机器操作、调整队列配额等），如遇此类集群侧问题，建议用户联系集群运维方协助处理。}
```

### 6.2 峰峦应用报告模板（engine=fengluan）

```
## 峰峦（K8s on Spark）任务诊断报告

### 基础信息
- 任务 ID    : {job_id}
- 平台       : {platform}
- K8s 集群   : {cluster}
- Namespace  : {namespace}
- Master Pod : {master_pod_name}
- 状态       : {state}
- 开始时间   : {started_time}
- 结束时间   : {finished_time}
- 执行耗时   : {elapsed_time}

### 诊断结论
{一句话概述失败根因。若涉及 K8s 级别信号（如 OOMKilled），明确标注；若 fengluan-diagnosis 提供了 Severity/Suggestion，可一并引用}

### 详细分析
{分步骤的分析过程，引用关键日志片段；如有 K8s 级证据（ExitCode/Events/Messages），单独段落引用 fengluan-diagnosis 输出}

### 修复建议
{从用户角度给出的具体修复步骤和参数调整建议。Spark 引擎层的建议（配置/代码/SQL）与 YARN 一致；峰峦特有建议（如 K8s 资源 request/limit、镜像选择）可补充。不要给出需要平台/集群运维权限的建议。}
```

---

## 参考文档

```bash
do-bigdata docs list --skill yarn-app-diagnose
do-bigdata docs show --skill yarn-app-diagnose --file yarn_log_patterns.md
```

- `yarn_log_patterns.md` — 应用失败常见日志模式和分析用例参考文档。**YARN 与峰峦共用**：包含 OOM、GC 问题、资源不足、权限错误、数据倾斜、网络超时、PySpark 异常、Spark Stage 失败等故障模式的日志特征和诊断思路。当需要分析具体日志内容时，通过上述 CLI 命令读取此文件获取匹配模式和诊断建议。

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
