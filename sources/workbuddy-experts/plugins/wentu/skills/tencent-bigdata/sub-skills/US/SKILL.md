---
name: us
description: >
  US（统一调度）平台相关技能集合，覆盖任务失败诊断、慢任务耗时分析、任务/实例操作、日志查询与脚本管理、模板化任务创建五大能力。
  包含子技能：us-fail-task-diagnose（任务失败/出库入库失败/脏数据/权限错误/SQL报错/告警查询等诊断）、
  us-slow-task-diagnose（任务慢/耗时异常/超时/等待下发/调度延迟/队列排队等慢任务诊断）、
  us-operate-diagnose（创建任务/上传脚本/创建依赖/冻结解冻/复制任务/补录/回溯/重跑/终止/强制成功等操作）、
  us-log-analyzer（下载脚本/批量下载/WeData开发态日志/US平台使用咨询/封闭域/任务类型配置等）、
  create-us-task-from-templates（基于模板/参考任务/git+打包指令一键创建 100/121/128/129/132 五类常见 US 任务）。
  触发关键词：US任务、统一调度、任务失败、任务慢、耗时长、创建US通用任务（LhotseTask，**不含 PlugSQL/插件SQL，task_type=3 的创建请走 WeData/wedata-plugsql**）、复制任务、补录、回溯、重跑、下载脚本、告警查询、US视图、视图ID、视图详情、查询视图、任务所属视图、任务列表查询、模板创建US任务、git打包创建US任务、参考任务创建US任务、taskType 100/121/128/129/132。
---

# US（统一调度）技能集

## 概述

US（Unified Scheduler / 统一调度）是腾讯内部的分布式任务调度平台（https://us.woa.com），每天管理数百万个任务实例。本目录包含与 US 平台相关的所有技能。

> [WARN] **边界：`us-<数字>-<数字>-<数字>` 严格四段式的 ID 不是 US 任务 ID，不要在本子系统处理。**
>
> US **统一调度任务 ID 是纯数字（18 位）**。如果用户给的 ID **严格命中四段式** `^us-\d+-\d+-\d+$`（`us-` 前缀 + 恰好 3 段纯数字，如 `us-2026070103102338-1782848143426-3`），那是**峰峦（K8s on Spark）运行时 job_id**，不是 US 调度任务——用它去 US 平台按任务 ID 查一定查不到。此时**必须改用 `Yarn/yarn-app-diagnose`**（app-info 会自动识别为 `engine=fengluan`）。同理 `wedata-` 四段式也是峰峦 job_id；`application_xxx` / `job_xxx` 亦走 `Yarn/yarn-app-diagnose`。
>
> 另：`livy-sessionid-*` 是 SuperSQL 经 Livy 提交的 Spark 作业，本质是**峰峦运行时 job_id**，**优先走 `Yarn/yarn-app-diagnose`**（`engine=fengluan`），仅当需要 SuperSQL 全链路上下文时才转 `SuperSQL/`。

## 可用技能

### 1. us-fail-task-diagnose — US 失败任务诊断

- **路径**: `us-fail-task-diagnose/`
- **用途**: 分析 US 任务实例日志，自动诊断任务失败原因，提取错误特征，提供针对性解决方案
- **触发场景**:
  - 用户提供 US 任务日志链接、日志内容或任务 ID，需要诊断任务失败原因
  - 用户遇到任务失败、出库失败、入库失败、脏数据、权限错误、SQL 报错、连接超时等问题
  - 用户咨询 US 平台使用问题：权限管理、任务配置、调度依赖、告警配置、时间变量、任务补录、系统冻结、封闭域等
- **核心能力**:
  - 通过 US API 自动采集任务配置、实例状态、执行日志、依赖关系
  - 查询告警记录（延迟告警、失败告警），支持按任务ID和时间范围筛选
  - 11 大类错误模式扫描（出库脏数据、入库分区、权限连接、资源超时、SQL 脚本、HDFS 文件、Shell、封闭域等）
  - 失败任务自动调用平台智能分析接口
  - 内置排障指南、错误码索引、平台使用手册、封闭域指南等参考资料
- **触发关键词**: US任务、统一调度、任务日志、实例日志、任务失败、出库失败、入库失败、脏数据、权限错误、SQL报错、连接失败、脚本错误、OOM、Permission denied、告警配置、告警记录、告警查询、延迟告警、失败告警、权限申请、任务依赖、任务补录、时间变量、系统冻结、封闭域

### 2. us-slow-task-diagnose — US 慢任务诊断

- **路径**: `us-slow-task-diagnose/`
- **用途**: 分析 US 任务实例日志，自动诊断任务耗时异常原因，拆解全生命周期各阶段耗时，定位性能瓶颈
- **触发场景**:
  - 用户反映任务跑得慢、耗时变长、等待下发时间过长
  - 用户需要分析任务各阶段耗时、定位性能瓶颈
  - 任务超时、运行时间异常增长的排查
- **核心能力**:
  - 通过 US API 自动采集任务配置、实例状态、阶段日志
  - 6 阶段全生命周期耗时拆解（US 调度等待 → 提交引擎 → Runner 准备 → 引擎提交 → Application 运行 → 收尾）
  - 自动获取上一运行周期日志进行耗时对比分析
  - 自动标注占比 >30% 的瓶颈阶段
  - 耗时增幅 >50% 时联动失败诊断和队列资源分析
- **触发关键词**: 任务慢、执行慢、耗时长、耗时异常、跑得慢、超时、等待下发、运行时间长、调度延迟、队列排队、资源等待、任务超时

### 3. us-operate-diagnose — US 任务/实例操作工具

- **路径**: `us-operate-diagnose/`
- **用途**: 提供 US 平台的任务级别和实例级别操作能力，支持任务全生命周期管理和实例运维操作
- **触发场景**:
  - 用户需要创建任务、批量创建任务、修改任务配置
  - 用户需要上传脚本、创建任务依赖关系
  - 用户需要冻结/解冻任务、复制任务
  - 用户需要补录实例、重跑实例、终止实例、强制成功实例
- **核心能力**:
  - 任务管理：创建任务、批量创建任务、修改任务、复制任务（支持批量、自动分批）、上传脚本（四道门禁流程）、创建依赖、冻结/解冻任务
  - 实例运维：补录实例（自动分批）、重跑实例（自动分批+异步轮询结果）、终止实例、强制成功
  - 查询辅助：查询任务类型、查询扩展参数列表、校验上传参数、检查脚本是否存在
- **触发关键词**: 创建任务、上传脚本、创建依赖、冻结任务、解冻任务、修改任务、复制任务、任务补录、重跑实例、终止实例、kill实例、强制成功

### 4. create-us-task-from-templates — US 模板化任务创建（聚焦 100/121/128/129/132）

- **路径**: `create-us-task-from-templates/`
- **用途**: 把"创建一个常见 US 任务"压缩成"业务一次性给齐 / 给参考任务 / 给 git 仓库 + 打包指令"三种姿势，由本 Skill 编排 git clone、打包、上传脚本、创建任务的完整链路
- **适用范围**: 仅 taskType ∈ {100, 121, 128, 129, 132}；其它 taskType / 批量创建 / 修改复制 / 实例运维请走 `us-operate-diagnose`
- **核心能力**:
  - 三种业务输入姿势：A（git_url + build_cmd + artifact_path）/ B（完整 task_config + 已有脚本）/ C（参考任务 ID）
  - 自动按 taskType 选择"先建任务后上传脚本"（128/129）或"先上传脚本后建任务"（121/132/100）
  - 复用 `us-operate-diagnose` 的 create-task-flow 三道门禁 和 upload-script-flow 四道门禁，**不重复实现**
  - 打包前用户确认门禁（G0）— 任意 shell 命令必须先复述给用户确认
  - 复用 `do-bigdata us` 现有 CLI（`query-task` / `validate-upload` / `check-script-exist` / `upload-script` / `prepare-create-task` / `execute-create-task`），**不引入新 CLI 命令**
- **触发关键词**: 模板创建US任务、create_us_task_from_templates、git打包创建US任务、参考任务创建US任务、一键创建US任务、spark/pyspark/pythonsql/supersql/微信计算 任务模板、taskType 100/121/128/129/132

### 5. us-log-analyzer — US 日志查询与脚本管理（共享资源库）

- **路径**: `us-log-analyzer/`
- **说明**: 作为 us-fail-task-diagnose 和 us-slow-task-diagnose 的**共享脚本和参考文档库**，提供底层 CLI 查询命令和平台参考资料
- **核心能力**:
  - **US API 查询命令**（`do-bigdata us`）：任务查询、实例状态查询、执行日志获取、阶段日志获取、依赖关系查询、变更记录查询、重跑明细查询、脚本版本查询
  - **脚本下载与管理**：单个脚本下载（`do-bigdata us download-script`）、批量下载应用组脚本（`do-bigdata us batch-download`，内置限流保护）、脚本元数据查询（`do-bigdata us script-view`）
  - **WeData API 查询命令**（`do-bigdata us`）：调度态日志查询（`do-bigdata us describe-log`）、开发态执行记录查询（`do-bigdata us describe-execution-records`）、开发态执行日志查询（`do-bigdata us describe-execution-log`）
  - **参考文档库**（`do-bigdata docs list --skill us-log-analyzer`）：排障指南、错误码索引、US 平台使用指南、任务类型配置指南、封闭域指南、Gaia 集群映射表、FAQ 等
- **触发场景**:
  - 用户需要下载 US 脚本、批量下载应用组脚本、查询脚本版本/元数据
  - 用户需要查询 WeData 开发态的执行记录或执行日志
  - 用户咨询 US 平台使用问题（权限、配置、封闭域、任务类型等）→ 通过参考文档回答
  - 失败/慢任务诊断场景由 us-fail-task-diagnose / us-slow-task-diagnose 调用其脚本工具
- **触发关键词**: 下载脚本、批量下载、脚本版本、脚本查询、应用组脚本、WeData日志、开发态日志、执行记录、US使用指南、封闭域、任务类型配置、Gaia集群、查询视图、视图ID、视图详情、任务所属视图、视图任务列表、任务列表查询

## 强制输出规则（铁律）

> **[WARN] 仅当本次响应确实由 US 子技能（本 `US/SKILL.md` 路由命中的子技能，如 us-fail-task-diagnose / us-slow-task-diagnose / us-operate-diagnose / us-log-analyzer 等）处理时**，回复的最末尾必须附加以下内容（加粗高亮，不可省略）：
>
> **[WARN] 如果US使用上有任何问题，可以直接联系 kimlinlin**
>
> **作用域边界（防止泛化到其他子系统）**：
> - [OK] 适用：诊断报告、操作结果、US 使用咨询回复等**由 US 子技能产出的任何形式回复**。
> - [NO] **禁止**：若本次任务被**跨模块路由到非 US 子系统**（如 WeData/wedata-plugsql、Authentication、Flink、Spark、OLAP 等），即使路由过程中读到了本规则，**也绝不能**在那些子系统的回复末尾附加此提示。此提示**只属于 US**，不得带入其他子系统。

## 多地域（Namespace）支持

US 平台支持多地域部署，当前已支持的地域：

| 环境 | namespace | US 前台访问地址 | WeData 前台访问地址 | US OpenAPI 域名 | WeData OpenAPI |
|------|-----------|----------------|-------------------|----------------|----------------|
| **国内（默认）** | `default` | `https://us.woa.com/` | `https://wedata.woa.com/` | `tdwopen.oa.com` | [OK] 支持 |
| **国内自研新加坡** | `sg` | `https://us-sg.woa.com/` | `https://wedata-sg.woa.com/` | `tdwopen-sg.woa.com` | [OK] 支持 |
| **海外公有云新加坡** | `overseas-sg` | `https://public-qcloud-sg-us.wedata.deltaverse-intl.com/` | 暂无 | 后台接口 `43.163.59.19:8888`（仅 CLI 底层使用，不对用户展示） | [FAIL] **不支持，仅用 US 原生 API** |

> **重要区分**：`sg` 和 `overseas-sg` 都对应"新加坡"，但**不是同一个环境**（账号、密钥、任务、数据完全不通）：
> - `sg`：**国内自研**新加坡环境（通过 `.woa.com` 域名访问，走 US OpenAPI 或 WeData OpenAPI）
> - `overseas-sg`：**海外公有云**新加坡环境（通过 `public-qcloud-sg-us.wedata.deltaverse-intl.com` 访问，**只能使用 US 原生 API，不能使用 WeData OpenAPI**；对应的 `43.163.59.19:8888` 是**后台接口地址**，只有 CLI 底层调用时使用，**禁止在对用户可见的提示中展示**）

### * Namespace 自动识别决策流（铁律）

**按 Step 1 → Step 2 → Step 3 → Step 4 从上到下优先级判定，命中即停。**

---

#### Step 1：URL 自动识别（最高优先级）

扫描用户消息里的**所有 URL**（宽松匹配规则见下）：
- **全部命中同一 namespace** → 直接采用该 namespace，**跳过二次确认**，直接输出环境声明进入下一步
- **命中多个不同 namespace**（如同时出现 `us.woa.com` 和 `wedata-sg.woa.com`）→ **停下来向用户澄清**，禁止擅自选（见【多 URL 环境冲突提示模板】）
- **未命中任何 URL** → 进入 Step 2

**URL 匹配规则（U1~U6）**：

| 编号 | 规则 |
|---|---|
| **U1** | **大小写不敏感** + 允许协议头（`http://` / `https://`）与端口 + 允许后面带任意 path / query（如 `?taskId=xxx`、`/task-manage/xxx`） |
| **U2** | **子串包含**匹配，不做精确等于（用户经常粘贴的是深链） |
| **U3** | **域名 → namespace 映射表**：<br>• `us-sg.woa.com` / `wedata-sg.woa.com` / `tdwopen-sg.woa.com` / `sg.security.tianqiong.woa.com` → `sg`<br>• `public-qcloud-sg-us.wedata.deltaverse-intl.com` / `qcloud-sg-us.wedata.deltaverse-intl.com` / `43.163.59.19` → `overseas-sg`<br>• `us.woa.com` / `wedata.woa.com` / `tdwopen.oa.com` → `default` |
| **U4** | **一条消息里出现多个链接指向不同 namespace 时** → 停下来问用户，禁止擅自选（提示模板见下方） |
| **U5** | **URL 与用户口头声明冲突时（如用户说"帮我在新加坡建任务"但粘贴的是 `us.woa.com` 链接）** → **以 URL 为准**，并在响应第一行提示（模板见下方） |
| **U6** | **URL auto-detect 命中后不再二次确认**（URL 是强证据，直接进入下一步，不再执行 Step 2/3） |

---

#### Step 2：关键词直判（用户明确说了限定词）

用户消息中未包含任何 URL，但**明确带限定词**时直接判定，**无需二次确认**：

| 用户说法（关键词） | 判定 |
|---|---|
| "公有云新加坡" / "公网新加坡" / "海外新加坡" / "overseas SG" | `overseas-sg` |
| "自研新加坡" / "内网新加坡" / "SG 内网" | `sg` |

---

#### Step 3：仅提到"新加坡 / SG / Singapore"（无限定词）

无 URL、也没有 Step 2 的限定词，**必须**走【标准提示语模板 · 新加坡环境二次确认】进行二次确认，禁止默认走 `sg` 或 `overseas-sg`。

---

#### Step 4：未提及新加坡相关词

→ namespace = `default`（国内）

---

### [LIST] 标准提示语模板（子 skill 直接引用，禁止各自硬编码）

#### 【模板 T1 · 新加坡环境二次确认】（Step 3 触发时使用）

> 您提到的是"新加坡"环境。国内自研和海外公有云是**两套完全独立的环境**（账号、密钥、任务、数据都不通），请先确认是以下哪一个：
>
> | 环境名称 | US 前台访问地址 | WeData 前台地址 | 命名空间 |
> |---|---|---|---|
> | ** **国内自研新加坡** | https://us-sg.woa.com/ | https://wedata-sg.woa.com/ | `sg` |
> | * **海外公有云新加坡** | https://public-qcloud-sg-us.wedata.deltaverse-intl.com/ | 暂无 | `overseas-sg` |
>
> 请回复 **"国内自研新加坡"** 或 **"海外公有云新加坡"**，也可以直接把您访问的页面 URL 发给我，我会自动识别。
>
> [WARN] 未收到明确回复前**禁止**执行任何 `do-bigdata us` 命令。

#### 【模板 T2 · 多 URL 环境冲突】（U4 触发时使用）

> [WARN] 您在同一条消息里提供了**指向不同环境的链接**：
> - `<url_1>` → `<env_a>`（`<namespace_a>`）
> - `<url_2>` → `<env_b>`（`<namespace_b>`）
>
> 请确认本次操作针对哪个环境？回复环境名称或只保留对应链接即可。

#### 【模板 T3 · URL 与口头声明冲突】（U5 触发时使用，输出后**继续按 URL 判定的环境执行**）

> ℹ️ 检测到您的链接域名指向 **<从URL识别的环境名>**（`<namespace_from_url>`），与您口头声明的 **<声明的环境名>** 不一致。
> 已**按链接域名**走 `<namespace_from_url>` 环境；如需切换请重新提供对应环境的 URL 或明确说明。

---

### [LIST] 环境声明（统一措辞，每次执行诊断/查询/操作前必须输出）

| namespace | 环境声明 |
|---|---|
| `default` | `* 当前环境：国内（default）` |
| `sg` | `* 当前环境：国内自研新加坡（sg） · us-sg.woa.com / wedata-sg.woa.com` |
| `overseas-sg` | `* 当前环境：海外公有云新加坡（overseas-sg） · public-qcloud-sg-us.wedata.deltaverse-intl.com（仅用 US 原生 API）` |

**规则 4：namespace 参数传递**

当识别到非 default 的 namespace 时，所有 `do-bigdata us` 命令必须附加 `--skill-namespace <ns>` 参数：
```bash
# 国内（默认，无需额外参数）
do-bigdata us query-task --task-id 12345 --query "查询任务"

# 新加坡内网（必须附加 --skill-namespace sg）
do-bigdata us query-task --task-id 12345 --skill-namespace sg --query "查询任务"

# 新加坡公网（必须附加 --skill-namespace overseas-sg）
do-bigdata us query-task --task-id 12345 --skill-namespace overseas-sg --query "查询任务"
```

**[WARN] overseas-sg 环境特殊限制**：

`overseas-sg` **只能使用 US 原生 API，不能使用 WeData OpenAPI**。以下命令族在 `overseas-sg` 环境下**禁止调用**（当前底层不支持，调用会 fallback 到国内域名并失败）：

- [FAIL] `describe-log` / `describe-execution-records` / `describe-execution-log`
- [FAIL] `describe-tasks` / `describe-task-detail` / `download-file`

在 `overseas-sg` 环境下，遇到"看日志""查任务详情""下载脚本"等诉求：
- **日志类**：改用 US 原生日志接口（如 `log` / `stage-log` / `original-log`）
- **任务详情**：改用 US 原生 `query-task`
- **脚本下载**：改用 US 原生 `download-script`

> **[ALERT] 规则 4 全命令覆盖铁律（最高优先级，违反即报错）**
>
> `--skill-namespace <ns>` 必须传给 **`do-bigdata us` 子树下的全部命令**，**没有例外**。包括但不限于：
>
> | 命令族 | 示例 | 非 default 环境必传 | overseas-sg 支持性 |
> |---|---|---|---|
> | US 原生 API | `query-task` / `query-run` / `log` / `stage-log` / `original-log` / `relation` / `change-log` / `redo-list` / `task-list` / `list-view` / `view-detail` / `download-script` / `script-versions` 等 | [OK] | [OK] 支持 |
> | **WeData 复用 API**（do-bigdata us 子树下封装的 WeData OpenAPI 命令） | **`describe-log` / `describe-execution-records` / `describe-execution-log` / `describe-tasks` / `describe-task-detail` / `download-file`** | [OK] **同样必传** | [FAIL] **禁止使用** |
> | 操作类命令 | `create-task` / `modify-task` / `copy-task` / `freeze` / `unfreeze` / `redo` / `kill` / `force-success` / `backfill` 等 | [OK] | [OK] 支持 |
>
> **常见误判（必须避免）**：
>
> - [FAIL] **误判 A**："`describe-task-detail` 是 WeData 接口，不需要 namespace" → 错。它在 `do-bigdata us` 子树下被 CLI 重新封装，**底层域名根据 `--skill-namespace` 路由到 `wedata.woa.com` 或 `wedata-sg.woa.com`，不传就默认走国内域名，SG 环境下会查不到任务**（典型表现：返回"任务不存在"或字段不全）。
> - [FAIL] **误判 B**："只读查询不需要切环境" → 错。**只读查询同样必须带 namespace**，否则跨环境查询会得到错误的"不存在"结论，进而误导后续创建/操作动作。
> - [FAIL] **误判 C**："参考国内任务创建 SG 任务，所以查国内、建 SG" → 错。如果用户在 SG 环境且参考任务也在 SG 环境，**查询和创建必须都用 `--skill-namespace sg`**；如果参考任务是国内任务（用户明确说"参考国内的 X 任务建 SG 任务"），需要**先用 default 查参考任务、再用 sg 创建**，并在响应中明确两步分别用了哪个 namespace。
>
> *** 自检清单（每次执行海外环境命令前必走）**：
>
> 1. **URL 优先**：用户消息里是否有 URL？→ 有 → 按 Step 1 (U1~U6) 决策流判定 namespace，多 URL 冲突走【模板 T2】、URL 与声明冲突走【模板 T3】+ 以 URL 为准继续执行
> 2. **关键词直判**：无 URL 但用户明确说"公有云/公网/海外新加坡" → `overseas-sg`；说"自研/内网新加坡" → `sg`（无需二次确认）
> 3. **仅笼统提"新加坡"**（无 URL 且无限定词）→ **必须走【模板 T1】二次确认**，禁止默认
> 4. 即将执行的命令是否在 `do-bigdata us` 子树？→ 是 → **必须带 `--skill-namespace <ns>`**
> 5. 命令名是否以 `describe-` 开头？→ **不能因为它"看起来像 WeData 接口"就漏传 namespace**；且若 namespace=overseas-sg → **禁止使用 `describe-*` 类命令**，改用 US 原生接口
> 6. 命令拼接好后，肉眼检查 `--skill-namespace <ns>` 是否真的出现在命令字符串里
>
> **[SHIELD] 兜底**：如果一条海外环境命令执行后返回"任务不存在 / 数据为空 / 字段不全"，**第一反应必须是检查是否漏了 `--skill-namespace <ns>`**，或（overseas-sg 环境）是否误用了 `describe-*` 类命令；不要告诉用户"任务可能在其他区域"。

## 执行流程

收到用户请求后，按以下步骤执行：

1. **环境识别**：从用户提供的链接中识别 namespace（参见上方「Namespace 自动识别规则」）
2. **意图识别**：分析用户请求，确定属于哪类场景（失败诊断 / 慢任务 / 操作 / 日志查询）
3. **路由分发**：根据下方路由规则表选择合适的子技能
4. **执行子技能**：跳转到对应子技能的 SKILL.md，按其定义的流程执行（传递 namespace 上下文）
5. **结果输出**：将子技能执行结果整理后返回给用户

> **默认路径**：当用户意图不明确时，优先推荐 `us-fail-task-diagnose`（覆盖面最广，兼具诊断和咨询能力）。

### [WARN] 批量任务 ID 限流（铁律）

当用户一次性提供的**任务 ID 数量超过 5 个**时（无论诊断、查询还是操作场景），**不要直接全部处理**，应先**明确告知用户分批提供**，原因：单个任务需要采集任务配置、实例状态、多类日志等大量信息，一次处理过多任务会**耗时过久**、容易超时或输出过长。

处理方式：
- 明确回复用户：「一次提供的任务 ID 较多（共 N 个，已超过 5 个），为保证处理速度和结果质量，请**分批提供（建议每批 ≤ 5 个）**，我会逐批为你处理。」
- 等待用户按批次重新提供后，再逐批执行。
- 不要为了"省事"而一次性串行处理全部任务。

## 路由规则

收到用户请求后，根据以下规则选择合适的技能：

| 用户意图 | 推荐技能 |
|---------|---------|
| **【失败诊断类】** | |
| 任务失败 / 报错 / 诊断失败原因 | us-fail-task-diagnose |
| 出库入库失败 / 脏数据 / 权限错误 | us-fail-task-diagnose |
| SQL报错 / 脚本错误 / OOM / 连接超时 / HDFS权限 | us-fail-task-diagnose |
| 封闭域导致的任务失败 | us-fail-task-diagnose |
| 查询告警记录（延迟/失败告警） | us-fail-task-diagnose |
| **【慢任务诊断类】** | |
| 任务慢 / 耗时异常 / 超时 / 跑得慢 | us-slow-task-diagnose |
| 等待下发 / 调度延迟 / 队列排队 / 资源等待 | us-slow-task-diagnose |
| 任务各阶段耗时分析 / 性能瓶颈定位 / 耗时对比 | us-slow-task-diagnose |
| **【操作类（写操作，需确认）】** | |
| 模板化创建 US 任务（taskType ∈ {100, 121, 128, 129, 132}，三种姿势：完整模板 / 参考任务 / git+打包指令） | **create-us-task-from-templates** |
| 创建其它 taskType 的 US 任务（如 Shell 106、出入库 75/76 等）/ 批量创建（>1 个）/ 修改任务 / 复制任务 | us-operate-diagnose |
| 上传脚本 / 创建依赖 | us-operate-diagnose |
| 冻结 / 解冻任务 | us-operate-diagnose |
| 任务补录（补历史数据） | us-operate-diagnose |
| 任务回溯（含下游回溯、4 种回溯方式） | us-operate-diagnose |
| 重跑 / 终止（kill） / 强制成功实例 | us-operate-diagnose |
| **【查询/日志/脚本类（只读）】** | |
| 下载脚本 / 批量下载应用组脚本 / 查询脚本版本 / 检查脚本是否存在 | us-log-analyzer（`download-script` / `batch-download` / `script-versions` / `script-exist`） |
| 查询任务配置 / 检查任务是否存在 / 查询任务类型 | us-log-analyzer（`query-task` / `check` / `task-type-info`） |
| 查询实例状态 / 实例执行日志 / 阶段日志 / 原始日志 / 集群 Job ID | us-log-analyzer（`query-run` / `log` / `stage-log` / `original-log` / `job-info`） |
| 查询任务依赖关系 / 变更记录 / 重跑明细 | us-log-analyzer（`relation` / `change-log` / `redo-list`） |
| 查询任务所属视图 / 视图ID / 视图详情 / 视图中的任务列表 | us-log-analyzer（`list-view` / `view-detail`） |
| 查询任务列表（按负责人/应用组/视图ID等条件筛选） | us-log-analyzer（`task-list`） |
| 查询 WeData 开发态执行记录 / 开发态日志 | us-log-analyzer（`describe-execution-records` / `describe-execution-log`） |
| 查询 WeData 调度态实例日志 | us-log-analyzer（`describe-log`） |
| 查询 WeData 项目任务列表 / 任务详情 / 下载 WeData 脚本 | us-log-analyzer（`describe-tasks` / `describe-task-detail` / `download-file`） |
| US 平台使用咨询（权限、配置、调度、任务类型等） | us-log-analyzer（参考文档） |
| 封闭域相关问题 / Gaia 集群查询 | us-log-analyzer（参考文档） |
| **【跨模块路由】** | |
| **创建 / 发布 WeData PlugSQL 任务**（插件 SQL，task_type=3） | **→ 跨模块路由到 [`WeData/wedata-plugsql`](../WeData/wedata-plugsql/SKILL.md)** |
| **库表权限查询** / 检查表权限 / 数据表访问权限 | **→ 跨模块路由到 [`Authentication`](../Authentication/SKILL.md)**（`table-permission-check`） |

### [WARN] 视图查询属于 US 平台（不要误路由到 WeData）

**US 视图（View）** 是 US 统一调度平台的概念，用于将一组有依赖关系的任务组织到一起管理。以下场景**必须路由到 `us-log-analyzer`**，而不是 WeData 相关技能：

- 用户提到"视图ID"、"视图详情"、"任务所属视图"、"查询视图"等
- 用户想查某个任务属于哪个视图 → `do-bigdata us list-view --task-id <ID>`
- 用户想查某个视图包含哪些任务、依赖关系 → `do-bigdata us view-detail --view-id <ViewID>`
- 用户想按视图ID筛选任务列表 → `do-bigdata us task-list --view-id <ViewID>`

### [WARN] PlugSQL 任务创建属于 WeData（不要误路由到 US）

**PlugSQL（插件 SQL，task_type=3）** 是 WeData 平台的任务类型，其"创建 / 发布"是一条 WeData 专属的端到端编排链路（上传脚本 → 建任务 → 配目标表 → 配 git → 校验 → 发布），由 `WeData/wedata-plugsql` 独立、自包含实现。以下场景**必须跨模块路由到 [`WeData/wedata-plugsql`](../WeData/wedata-plugsql/SKILL.md)**，而**不要**因命中"创建任务"关键词就交给 `us-operate-diagnose`：

- 用户提到"创建 plugsql 任务"、"PlugSQL"、"插件 SQL"、"task_type=3"、"配置目标表 / 目标表草稿 / saveEntityDraft"、"发布前校验"等
- 用户要走"上传脚本 → 建任务 → 配目标表 → 配 git → 发布前校验 → 发布"的 WeData PlugSQL 完整链路

> `us-operate-diagnose` 的"创建任务"仅指 **US 统一调度的通用任务（LhotseTask）**；WeData PlugSQL 任务不在其范围内。

### [WARN] 库表权限问题跨模块引导

在 US 任务诊断过程中，如果发现失败原因涉及 **库表权限问题**（如 `Permission denied`、`Access denied`、无权限访问某个数据库/表、select/update/alter/create 权限不足等），**不要仅在 US 侧给出建议，应主动引导用户使用 [`Authentication/table-permission-check`](../Authentication/SKILL.md) 技能进行精确的权限检查**。

典型场景包括但不限于：
- 任务日志中出现 `Permission denied`、`Access denied`、`No privilege`、`Authorization failed` 等权限相关错误
- 用户主动询问"某个库表是否有权限"、"为什么没有权限"
- 诊断结论为权限不足导致任务失败

引导方式：告知用户可以通过 `Authentication/table-permission-check` 技能直接检查具体库表的权限状态（支持 select/update/alter/create 四种权限类型），并提供权限申请链接。

> 如果用户的问题不属于以上任何场景，可尝试基于通用知识回答，或建议用户查阅 [US 使用指南](https://iwiki.woa.com/p/188168765)。

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
