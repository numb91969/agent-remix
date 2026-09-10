# 搜索域路由

> 只在一级 Agent 已判定为搜索域后读取。本文件只做 Skill/Flow 选择；通用安全、调用预算、调度和写操作规则以一级 Agent 为准。

## 1. 能力表

| 用户目标 | Skill | 关键信号 |
|---|---|---|
| 在公司校招简历库找应届生/实习生 | `zhaopin-operations` | 校招、应届、实习、届别、学校、专业 |
| 在公司社招简历库找有经验候选人 | `zhaopin-social-operations` | 社招、工作年限、在职、目标公司、跳槽 |
| 基于外部公开信息做人才/组织研究 | `mapping` | 人才 Mapping、竞对团队、关键人才、人才地图、行研 |
| AI 电话确认社招岗位意向或查结果 | `recruiting-ai-outbound-call` | AI 外呼、打电话、岗位意向、外呼结果 |
| 查社招实时招聘流程 | `recruitment-process-tracker` | 社招流程、卡在哪、招聘经理名下流程、偏慢预警 |

命中后在主进程精确调用一个 Skill。批量搜简历只能由两个 `zhaopin-*-operations` 承担；`interview-assistant` 只处理已知候选人的详情和后续动作。

## 2. 必要消歧

### 校招或社招

请求进入内部简历库搜索但没有任何招聘类型信号时，加载 `recruit_type` 歧义组。上下文或 JD 已明确应届/年限时不再问。

### 内部库、外部寻访或猎头

用户只说“找某方向的人、这个岗位招不到”而没有说明渠道时，加载 `sourcing_channel`：

- 内部库 → 校招/社招搜索；
- 外部公开信息 → `mapping`；
- 委外 → 出域到渠道。

### 联系候选人

- 明确 AI 电话/语音/外呼 → `recruiting-ai-outbound-call`；
- 明确约面/面试通知 → 出域到 `interview-assistant`；
- 只说“联系一下” → 加载 `contact_channel`。

### 流程或进度

- 社招逐候选人实时流程 → `recruitment-process-tracker`；
- 校招待办/已办事项 → 出域到 `interview-assistant · T4`；
- 漏斗、完成率、趋势 → 出域到数据域；
- 未说明实时还是历史 → 加载 `progress_source`。

## 3. 唯一约束

- 搜不到候选人时如实说明，不生成虚构姓名、公司或经历；
- `mapping` 的外部事实必须可溯源；
- 外呼仅在用户确认后执行，不回显手机号，不承诺 Offer/薪资，不主动 `forceSubmit`；
- 社招搜索锁定候选人后可以轻量推荐一次外呼，但不得自动发起；
- 评简历、出题、写面评、约面、改期和取消都属于面试域。

## 4. 依赖

| Skill | 依赖 |
|---|---|
| `zhaopin-operations` | `recruit-mcp` |
| `zhaopin-social-operations` | `recruit-mcp` |
| `recruiting-ai-outbound-call` | `recruit-mcp` |
| `recruitment-process-tracker` | `recruit-mcp` |
| `mapping` | 外部信息工具；iWiki 仅沉淀阶段可选 |

