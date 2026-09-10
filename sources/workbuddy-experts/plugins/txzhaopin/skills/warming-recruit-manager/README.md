# warming-recruit-manager - 腾讯校招签约后保温工作台

版本：v2.1 | 更新时间：2026-07-03 | 作者：acescwu

---

## 一句话简介

面向**招聘经理**的签约后候选人保温经营 Skill，融合导师/上级/入职岗位字段补充能力，让查数据、写话术、补字段、发通知、被提醒、定期推群、定时自动跑的保温闭环一键完成。

---

## 解决什么痛点？

签约后到正式入职之间是候选人最容易动摇的阶段，本 Skill 帮你：

- 灵活查询：支持**四种查询范围**（我名下 / 指定导师 / 指定上级 / 指定组织），可叠加**毕业届次 + 招聘类型**三维筛选
- 风险识别：自动识别**导师未填写、上级未确认、临近入职未建联**等风险，支持**高潜人选标签**（青云计划 / 青云实习 / 产培生）优先保温
- 深度分析：基于深度关注分析脚本输出**关注优先级、稳定签约等级、主关注维度**，帮助招聘经理聚焦重点
- 智能话术：一键生成个性化保温话术，支持 7 种保温阶段模板（欢迎词 / 入职倒计时 / 风险检测等）
- 自动播报：按三级提醒生成今日保温播报，督促关键动作
- 企微推送：通过企微机器人定期推送保温日报/周报到群
- 定时提醒：通过 CodeBuddy 自动化任务定时自动跑保温播报，无需手动唤起
- 通知协同：通过 HRClaw 邮件/企微 Tips 向导师或直接上级发送候选人保温信息
- 字段补充：发现导师、直接上级、入职岗位、直接上级岗位空字段，生成建议值和确认页，经用户确认后通过正式 `recruit-mcp` 回写

---

## 核心使用场景

### 场景 A - 保温数据查询

触发词：查一下我名下的 / 查 XXX 导师名下的同学 / 按组织看保温情况

- 按查询范围拉取待入职校招候选人
- 识别导师未填写、上级未确认、临近入职未建联等风险人选
- 可调用深度关注分析脚本，输出重点关注名单与稳定签约名单

### 场景 B - 保温话术生成

触发词：帮我写个欢迎话术 / 给 XXX 写保温脚本 / 候选人画像

- 基于简历特征 + 面评亮点生成个性化保温话术
- 可叠加深度关注建议，补充候选人关注优先级与稳定签约等级
- 支持 7 种保温阶段模板，内置合规红线检查

### 场景 C - 保温工作提醒

触发词：今日播报 / 给我提醒 / 我还有什么要跟进的

- 按三级提醒生成结构化播报（紧急 / 重要 / 常规）
- 督促跟进建联、责任链确认、临近入职等关键动作

### 场景 D - 企微机器人定期推送

触发词：设置企微机器人推送 / 每天发保温日报到群

- 将保温日报/周报转换为适合企微群的 Markdown 摘要
- 支持每日、每周或自定义频率的周期任务

### 场景 E - CodeBuddy 自动化任务定时提醒

触发词：让 CodeBuddy 自动提醒我 / 每天早上自动跑保温播报

- 通过 CodeBuddy 自动化在约定时间自动加载本 Skill 并生成保温播报
- 无需手动唤起，支持每日 / 每周 / 自定义频率

### 场景 F - HRClaw 通知导师/上级

触发词：发送邮件通知导师 / 企微提醒上级 / playwright-cli 发送邮件

- 支持 HRClaw 邮件和企微 Tips 两种通知方式
- 在本机可启动受支持浏览器、可完成 OA 登录时，通过 `playwright-cli` 浏览器自动化发送；macOS 优先 Chrome，Windows 可用 Edge/Chrome，不要求手动复制 Cookie

### 场景 G - 导师/上级/入职岗位字段补充

触发词：补充导师 / 补充直接上级 / 补充入职岗位 / 空字段 / 生成确认页 / 回写导师上级信息

- 拉取导师、直接上级、入职岗位、直接上级岗位缺失的录用单据
- 通过正式 `recruit-mcp` 复查招聘系统详情，不覆盖详情页已有值
- 用户确认策略后生成建议值和确认页 HTML
- 用户确认后才允许回写，且所有回写走当前用户鉴权

---

## 快速开始

1. 在 CodeBuddy / AI agent 平台安装本 Skill
2. 确保已连接 `hr-ai-data` MCP 插件（自动检测，未连接会提示）
3. 加载 Skill 后，按提示确认本次保温查询的**人群三要素**（查询范围 + 毕业届次 + 招聘类型）
4. 然后对我说：
   - `查一下我名下的待入职学生` → 立即看到保温清单
   - `查招聘活水部中待保温的` → 按组织筛选候选人
   - `帮我给张三写个欢迎话术` → 立即获得个性化脚本
   - `今日播报` → 立即看到今日需跟进事项
   - `给张三的导师发一封保温信息邮件` → 生成并发送通知
   - `帮我找出导师和直接上级为空的 offer，并生成确认页` → 进入字段补充流程
   - `让 CodeBuddy 每天早上自动跑一遍保温播报` → 引导创建自动化任务

---

## 依赖说明

- `hr-ai-data` MCP 插件（主数据源，**必须**）
- `wework-bot` MCP（企微群推送，可选）
- `recruit-mcp`（简历/面评/流程详情补充、字段补充详情复查与回写；字段补充场景必须使用正式 `recruit-mcp`）
- Python 3.10+（深度分析脚本运行环境；Windows 可用 `py -3` / `python`，macOS/Linux 通常用 `python3`）
- Node.js / npm + `playwright-cli`（HRClaw 邮件/企微 Tips 浏览器自动化发送）
- 本机可交互浏览器：macOS 推荐 Chrome，Windows 推荐 Edge/Chrome，Linux 需可视化桌面和可用 `DISPLAY` / Wayland
- 插件级低敏埋点入口 `../../scripts/track_skill_event.sh`（可选，不影响业务流程）

---

## 文件结构

```
warming-recruit-manager/
  SKILL.md                             # Skill 核心提示词与 SOP
  SKILL-MARKET.md                      # Skill 市场展示说明
  README.md                            # 本文件
  requirements.txt                     # Python 依赖
  references/
    data-query.md                      # 场景 A：数据查询 SOP 与字段说明
    warming-scripts.md                 # 场景 B：话术生成 SOP + 深度分析章节
    reminder.md                        # 场景 C/D/E：提醒、企微推送、自动化 SOP
    hrclaw-message.md                  # 场景 F：HRClaw 邮件/企微 Tips SOP
    supplement-flow.md                 # 场景 G：字段补充流程
    supplement-field-mapping.md        # 场景 G：字段映射与冲突说明
    supplement-api-and-auth.md         # 场景 G：API 与鉴权说明
    supplement-output-and-notify.md   # 场景 G：输出列、推送与定时配置、错误码
    migration-from-offer-field-supplement.md # 旧 Skill 融合说明
    sql-templates.md                   # 保温经营 SQL 模板（T1-T9、T_LINK）
  scripts/
    analyze_warming_status.py          # 基础保温状态风险分析
    analyze_candidate_attention_v4.py  # 深度关注建议 + 稳定签约识别
    supplement/                        # 字段补充 Step 化脚本
    shared/                            # 共享字段/API/路径工具
  sql/
    supplement/                        # 字段补充 SQL 模板
  config/
    supplement/field_mappings.json     # 字段补充融合映射
  templates/
    supplement/confirm_template.html   # 字段补充确认页模板
  output/
    supplement/                        # 字段补充运行产物
```

---

## 适用对象

- 腾讯校招**招聘经理**：本 Skill 的核心使用者
- 经营名下签约后人选 / 检视责任链 / 协调导师与直接上级的招聘负责人

> 本 Skill 当前不开放给导师/直接上级独立使用；如需查阅自己名下的人选，请联系对应招聘经理代查。

---

## 注意事项

- 本 Skill 依赖 `hr-ai-data` MCP 插件作为主数据源，请先安装并连接
- 企微群推送依赖 `wework-bot` MCP；机器人未连接或发送失败时，不会声称已推送成功
- 本 Skill 只查询「已签 + 毁约」的签约后候选人，不含面试中/offer 审批中阶段
- 已毁约候选人不生成保温话术，只支持毁约复盘建议
- HRClaw 邮件/企微 Tips 发送优先通过浏览器自动化完成；环境问题先按跨平台 SOP 修复并重试，手动 Console / Bookmarklet 仅作为最后兜底；Cookie 不展示、不记录、不持久化
- 高潜人选（青云计划/青云实习/产培生）所有场景均优先保温，必要时上级管理者参与
- 查询范围支持四选一并可叠加（如"我名下 + 在 PCG"），组织视角默认叠加招聘经理过滤防越权
- 字段补充场景默认只补空字段，不覆盖详情页已有值；生成建议值前必须确认策略，生产回写前必须二次确认
- 字段补充允许处理正式聘用制，但保温经营默认仍只纳入毕业生 / 应届实习生 / 日常实习生

---

## 相关文档

- [SKILL.md](./SKILL.md) - Skill 核心提示词与完整 SOP
- [SKILL-MARKET.md](./SKILL-MARKET.md) - Skill 市场展示说明
- [references/](./references/) - 详细业务规则与 SQL 模板
- 插件级 `scripts/track_skill_event.sh` - 统一的隐私最小化埋点入口
