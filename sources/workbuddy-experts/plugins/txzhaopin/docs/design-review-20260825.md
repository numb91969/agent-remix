# 腾讯招聘专家（txzhaopin）设计评审

- **评审对象**：`txzhaopin` v1.35.0（单 Agent 薄路由 + 29 Skills）
- **评审日期**：2026-08-25
- **评审范围**：路由架构、Skill 分解、安全模型、评测与校验工程
- **评审方式**：全量静态阅读 + 实跑 5 个校验脚本与路由回归

---

## 0. 总体判断

**架构选型是对的，工程水平明显高于一般 prompt 型 agent。**真正的问题不在架构本身，而在两处纪律断层：

1. **「薄路由」的约束只在第一层被强制执行**，到 Skill 层完全失效——一级省下的上下文在二级被吃回去；
2. **评测测的是「静态可达性」而非「路由准确率」**——文档自洽性 100%，模型实际选对的概率未被度量。

其余问题（CI 缺失、元数据碎片、少量陈旧内容）属于卫生级别，不影响架构成立。

---

## 1. 设计得好的部分

### 1.1 分层路由的上下文预算算得很清楚

| 层 | 体积 | 加载时机 |
|---|---|---|
| 一级 Agent `agents/recruitment-expert.md` | 234 行 / 13,023 B | 常驻 |
| 域视图 `agents/references/routes/*.md` | 5 个文件合计 306 行 | 命中域后读 1 个 |
| 能力注册表 `capability-registry.yaml` | 636 行 | 单一真源，按需 |
| 消歧组 `route-ambiguities.yaml` | 18 组 | 仅读命中的那一组 |

一次典型请求的路由开销约 15KB，而非把 29 个 skill 描述全量塞入上下文。这是该规模下唯一站得住的做法。

并且这个预算**被脚本强制**：

```python
# scripts/validate_routes.py:162-165
if len(agent_text.encode("utf-8")) > 25_000:
    fail("primary agent exceeds 25KB hot-context budget", errors)
if len(agent_text.splitlines()) > 350:
    fail("primary agent exceeds 350-line hot-context budget", errors)
```

### 1.2 消歧被当成一等公民设计，而不是靠模型自觉

这是本插件最有价值的部分。几个判据写得很准：

- **写 JD 的归属**（`agents/references/routes/interview.md:38-42`）：判据是**有没有可用的胜任力模型**，不是话术里有没有「JD」二字。这条把一个高频抢路由的场景钉死了。
- **规则 vs 动作**（`agents/recruitment-expert.md:89`）：「活水/伯乐/Offer/三方」只有主题词时**默认判为问规则**，出现「这条单据 + 改/提交/推进」才走业务 Skill，并明确「不要凭主题词直接调业务接口」。这直接堵死了最危险的失败模式。
- **发起流程 vs 安排面试**（`routes/interview.md:19`）：前者创建招聘流程，后者创建/变更日程；用户只说「安排一下」时先查状态，不凭字面猜接口。

### 1.3 安全模型是分级的，且看得出是踩过坑的

R0/R1/R2 三级风险 + 写操作握手顺序（`agents/recruitment-expert.md:183-190`）：

```
补齐参数 → 冻结最终 Payload → 计算摘要 → 展示影响并确认
→ 校验 Payload 未变化 → 串行执行一次 → 返回服务端任务 ID/审计 ID
```

其中「冻结后校验 Payload 未变化」和「网络中断或返回不明确时不得自动重试」是真实事故经验，不是模板话术。

`hrclaw-messenger` 标记 `routable: false` 并强制走业务上下文（`recruitment-expert.md:123`），避免「发个通知」退化成裸发消息，这个设计同样正确。

### 1.4 部分 Skill 的分解是范式级的

| Skill | SKILL.md | 总文件数 | 结构 |
|---|---|---|---|
| `mapping` | 308 行 | 71 | references/ + scripts/ + templates/ |
| `recruit-data-dashboard` | 255 行 | 64 | knowledge/metrics 四层（atomic/derived/composite/recipes） |
| `interview-assistant` | 647 行 | 53 | `flows/` 字母流程码 T/T2/SI/SC/A–H |

`recruit-data-dashboard` 的指标分层（原子/派生/复合/配方）和 `interview-assistant` 的 flow 码是可以推广到其他 Skill 的现成范式。

### 1.5 校验工程有真东西

实跑结果（2026-08-25）：

| 校验 | 退出码 | 结果 |
|---|---|---|
| `scripts/validate_routes.py` | 0 | 29 skills / 8 domains / 18 ambiguity groups，agent 在预算内 |
| `scripts/validate_execution.py --self-test` | 0 | 通过（6 个内嵌用例） |
| `scripts/validate_write_action.py --self-test` | 0 | 通过（4 个内嵌用例） |
| `scripts/reduce_controlled_execution.py --self-test` | 0 | 通过 |
| `evals/route_regression.py --strict` | 0 | 103/103 可达，0 weak / 0 冲突 / 0 未声明依赖 |
| `scripts/validate_plugin_consistency.py` | **1** | **16 项失败**（见 §2.3） |

6 个 JSON Schema 中 5 个被脚本真实校验（`task-envelope`、`result-envelope`、`resume-evaluation-data`、`question-audit-data`、`write-action-envelope`），不是摆设。`validate_plugin_consistency.py` 的注释里还记录了真实事故背景（如 `use_skill("tai-oauth")` 死引用累积 13 处），这种「校验器即事故档案」的写法值得保留。

---

## 2. 主要问题

### 2.1 【P0】评测测的不是路由准确率

**现象**：`evals/route_regression.py` 是纯 Python 字符串匹配，不调用任何模型（脚本自身在 4-14 行诚实标注了这一点）。判定逻辑是 `signal in text` 级别的子串命中。

**含义**：「103/103 可达」= 每条 golden query 都存在一条**文档路径**通向目标 skill；它**不能说明模型真的会选对**。

**为什么这是 P0**：插件里写得最用心的那些边界判据——JD 归属、找人的三岔口（内部库 / `mapping` / 猎头）、规则 vs 动作、发起流程 vs 安排面试——**全部落在模型判断层，一条都没有被度量**。当前状态是：文档自洽性 100%，实际路由准确率未知。

**覆盖情况**（供改造时复用）：

- golden set 103 条，其中 96 条有 `expected_skill`，7 条为设计上的「不应命中」（clarify-only / decline / zero-tool / 内部通道守卫）
- 26 个 routable skill **全部**至少有 1 条用例覆盖
- 3 个 `routable: false` skill 通过 `forbidden_skills` 反向覆盖
- 来源分布：`registry:examples` 39 / `registry:commands` 35 / `manual:*` 29

### 2.2 【P0】薄路由的纪律没有传导到 Skill 层

**现象**：一级 Agent 有 25KB / 350 行的硬预算并被脚本强制；**SKILL.md 没有任何等价预算**。

结果是 29 个 SKILL.md 合计 **873,623 B**，其中：

| Skill | SKILL.md | 子文件数 | 可延迟内容估算 |
|---|---|---|---|
| `employer-brand-xiaoe` | 84,240 B / 1,238 行 | 5 | ~78%（BG 档案 L174-601 共 428 行 + 3 个 playbook） |
| `interview-assistant` | 73,670 B / 647 行 | 53 | 已分解，入口偏大 |
| `employer-brand-amy` | 73,468 B / 531 行 | 32 | 已分解 |
| `quiz-deliverable-evaluator` | 68,149 B / 953 行 | 13 | ~59%（路线一/二正文 L247-656 共 410 行） |
| `headhunter-recommend` | 40,171 B / 715 行 | **1** | ~64%（算法 L220-641 共 422 行） |
| `hr-data-router` | — / 497 行 | **1** | ~350 行 |

**最能说明问题的是同仓库内两种风格并存**：`mapping`（308 行入口 + 71 文件）与 `headhunter-recommend`（715 行、**仅 SKILL.md 一个文件**）出自同一套设计规范。

**更矛盾的一处**：`quiz-deliverable-evaluator` 已经有 `references/quiz-api-reference.md`（174 行），却又在 SKILL.md L209-244 把 API 速查表重新内联了一遍——分解做了一半，收益被抵消。

`assessment-quality-expert` 的 description 写了「模块独立可用，按需加载」，但文件结构并没有强制这件事（模块 A-3 占 L355-515 共 161 行仍在主文件）。

### 2.3 【P1】一致性门禁实际上没在跑

**现象**：`validate_plugin_consistency.py` 报 16 个错，**全部**来自 `check_release_hygiene`：14 个 `.DS_Store` + 1 个 `.pyc` + 1 个 `__pycache__` 目录。

**根因**：这两类文件在 `.gitignore` 里**已经被正确忽略**。校验器扫的是**工作目录**（`ROOT.rglob(pattern)`，`validate_plugin_consistency.py:136-144`），而它想保护的是**打包产物**：

```python
# scripts/validate_plugin_consistency.py:136-140
def check_release_hygiene(errors: list[str]) -> None:
    for pattern, reason in FORBIDDEN_FILE_GLOBS:
        for hit in ROOT.rglob(pattern):
            if hit.is_file():
                fail(f"forbidden file in package ({reason}): {hit.relative_to(ROOT)}", errors)
```

**后果**：这个门禁在任何一台正常的 Mac 上都必然红。于是没人会把它接进流程——这也解释了为什么至今没有 CI。**一个必然失败的门禁等于没有门禁**，而它恰恰是全仓库唯一的总集成校验（内部 subprocess 调用 `validate_routes.py` 和 `route_regression.py --strict`）。

**修法**：让 hygiene 检查读取 `.gitignore`，或改为扫描 `git ls-files` / 实际打包产物，而非工作目录。

### 2.4 【P1】没有任何自动化

搜索确认**不存在**：`.github/workflows`、`Makefile`、`package.json`、`.pre-commit-config.yaml`、`pyproject.toml`（本插件及上级 marketplace 均无）。

所有校验靠手跑。README 的评测章节（L354-388）只记录了三条 `evals/` 命令，**没有把 `validate_plugin_consistency.py` 列为发布前必跑项**。

**文档已开始漂移**：README L365-376 仍写 **90 条**用例、只列 3 类 manual 来源；实际已是 **103 条**，且新增了 `manual:paired_boundary`(7) 与 `manual:data_path`(4)。

### 2.5 【P2】元数据碎片化与陈旧内容

**Frontmatter 分成 6 种风格**（29 个 Skill）：

| 字段 | 覆盖 | 缺失方 |
|---|---|---|
| `name` / `description` | 29/29 | — （且 folder ↔ name 零错配） |
| `support_contact` | 23/29 | 5 个 `employer-brand-*` + `headhunter-recommend` |
| `agent_created` | 9/29 | — |
| `version` | 7/29 | — |
| `tags` | 5/29 | — |
| `allowed-tools` | 2/29 | 其中 `assessment-quality-expert:4` 为**空值** |

**实质性陈旧内容**：

| 问题 | 位置 | 说明 |
|---|---|---|
| 内容损坏 | `skills/zhaopin-operations/SKILL.md:850-883` | Known Issues 重复两遍，L865-867、L882-883 有乱码片段（`orter_call.py`、`olutions`） |
| 死引用 | `assessment-quality-expert/SKILL.md:3,479`、`scripts/export_model.py:29`、`README.md:31` | 指向不存在的 `recruiting-assistant`（实际为 `interview-assistant`） |
| 陈旧安装路径 | `employer-brand-xiaoe/SKILL.md:32` 及 `使用指南.md:18-28` | 引用 `tencent-employer-branding/`，实际目录为 `employer-brand-xiaoe/` |
| 边界自相矛盾 | `employer-brand-xiaoe/SKILL.md:4` vs `1027-1104` | description 声明「舆情交给 Amy」，正文却内嵌 78 行合规 playbook |
| 遥测缺口 | `recruitment-inquiry-bot/SKILL.md` | 唯一没有 `FIRST ACTION` 埋点的 Skill（其余 28/29 都有） |
| 人格残留 | `employer-brand-amy/references/舆情危机处理方法论.md:4-5,215` | 仍写「仅供 Bonnie 内部调用」，Amy 已从 Bonnie fork |

**样板重复**：5 个 `employer-brand-*` 的 FIRST ACTION 块 87.5% 相同（约 70 行重复）；`zhaopin-operations` 与 `zhaopin-social-operations` 头部 L17-48 近乎逐行相同（约 116 行），但正文实现确有差异（整体行级相似度仅 7.8%），**只需抽头部，不必合并正文**。

### 2.6 【P2】能力注册表用 `.yaml` 后缀装 JSON

`agents/references/capability-registry.yaml` 首字符是 `{`，`json.load()` 可直接解析。YAML 是 JSON 超集所以不报错，但因此**失去了 YAML 唯一的好处：在路由规则旁边写注释**。

这个文件是整个路由的单一真源、636 行、内容全部是需要解释「为什么这样分域」的判断，却恰恰是最不能写注释的格式。此外它也会误导贡献者和任何 YAML 专用工具链。

**修法**：改名为 `.json`，或转成真 YAML 并把边界理由写进注释（推荐后者——这些理由现在散落在 route 视图和 agent 正文里）。

### 2.7 【P2】其他

- **`route-decision.schema.json` 是规范但未被实例校验**：`validate_routes.py:69` 只检查它能否被 JSON 解析；没有任何脚本校验实际的 route-decision 实例。它在 `recruitment-expert.md:127` 只作为 prose 契约存在。
- **受控执行校验只覆盖 2 个试点能力**（`resume_evaluation_batch`、`question_audit_batch`），其余 Skill 无同类运行时封套校验。

---

## 3. 建议的动作顺序

### 第一步：建立回归保护（P0，先做，否则后续改动无保护网）

1. **搭 shadow eval**：把现有 103 条 golden set 喂给模型跑**真实路由**，统计 top-1 准确率。重点看 7 条 `manual:paired_boundary` 和跨域用例——那才是判据是否有效的证据。产出应与现有 `evals/reports/` 同格式，可对比。
2. **修 `check_release_hygiene`**：改为读 `.gitignore` 或扫 `git ls-files`，让 `validate_plugin_consistency.py` 在干净 Mac 上能跑绿。
3. **接 CI**：`.github/workflows` 里跑 `validate_plugin_consistency.py`（它已 subprocess 串起 routes + reachability），并把它写进 README 的发布前 checklist。

### 第二步：把薄路由纪律传导到 Skill 层（P0）

4. **给 SKILL.md 加与 agent 同级的预算校验**（建议阈值先设宽，如 40KB / 600 行，只拦增量恶化）。
5. **用预算驱动三个大文件的拆分**：`employer-brand-xiaoe`（BG 档案 + playbook → `references/`）、`headhunter-recommend`（算法 → `references/algorithm.md`）、`quiz-deliverable-evaluator`（路线正文 → `references/`，并删掉与已有 reference 重复的内联速查表）。**照抄 `mapping` 和 `interview-assistant/flows/` 两个现成范式即可，不需要发明新结构。**

### 第三步：卫生清理（P2，可在上两步过程中顺手做，不单独排期）

6. 修 `zhaopin-operations/SKILL.md:850-883` 的损坏段落。
7. 全局替换 `recruiting-assistant` → `interview-assistant`；修 xiaoe 陈旧安装路径；清理 Amy 的 Bonnie 残留。
8. 补齐 6 个 Skill 的 `support_contact`；删除空的 `allowed-tools`；给 `recruitment-inquiry-bot` 补 FIRST ACTION 埋点。
9. 抽出共享样板（FIRST ACTION 模板、客服 footer、recruit-mcp 接入说明）到 `skills/_shared/`。
10. 同步 README 的评测章节（90 → 103 条及新来源分类）。
11. 决定 `capability-registry` 的格式：改 `.json` 或转真 YAML 并补注释。

---

## 4. 复核命令

```bash
cd <plugin-root>

# 单项校验
python3 scripts/validate_routes.py
python3 scripts/validate_execution.py --self-test
python3 scripts/validate_write_action.py --self-test
python3 scripts/reduce_controlled_execution.py --self-test

# 路由静态可达性（当前 103/103）
python3 evals/route_regression.py --strict

# 总集成（当前因 .DS_Store 必然失败，见 §2.3）
python3 scripts/validate_plugin_consistency.py

# 上下文预算实测
wc -lc agents/recruitment-expert.md
find skills -name SKILL.md -exec wc -c {} \; | sort -rn | head -10
```

> 注意：`evals/build_golden_set.py` 会**覆写** `router-golden.jsonl`，`route_regression.py --report` 会**写入** `evals/reports/`，只读复核时勿运行。
