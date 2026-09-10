# 招聘 Agent 受控执行契约

> 版本：1.0（txzhaopin v1.11.2 MVP）
>
> 用途：在已注册的复杂只读任务中保证任务完整覆盖、招聘对象隔离、结构化交付和确定性归并。它是执行协议，不是新的业务 Skill，不授予任何额外权限。

## 1. 当前启用范围

本版本仅启用两个试点能力，能力定义以 `capability-registry.yaml` 为唯一依据：

1. `resume_evaluation_batch`：3-10 份简历的独立评估与确定性排序；
2. `question_audit_batch`：3-100 道题目的独立审核与覆盖统计；超过 100 道必须拆成多个 execution。

单份简历、单道题、普通单 Skill 流程以及所有写操作，不进入本 MVP 编排。未登记在能力注册表中的任务不得自行套用本协议。

## 2. 不可下放的控制权

以下事项始终由招聘主 Agent 控制：

- 用户意图、校招/社招判断与 Skill 路由；
- 数据权限、隐私边界、合规检查、用户确认和业务安全门；
- 是否执行写操作以及写操作的先后顺序；
- 任务覆盖检查、异常处置与最终对用户的解释；
- 确认对应 Skill 声明的能力模型、量表和 Flow 已正确加载且版本明确；
- 是否将一次运行经验提交为候选规则。

具体评分、模型匹配和业务判断仍由对应 Skill 按原 Flow 执行，主 Agent 不得重新发明评分标准或覆盖 Skill 原始结果。

禁止自由组队、自主选择其它 Skill、自动扩展任务范围、修改 Prompt / Skill / Flow，或把一个招聘对象的信息共享给其它对象任务。

## 3. 风险分级

| 等级 | 场景 | 允许方式 |
|---|---|---|
| `R0` | 不涉及可识别自然人的公开行业、公司、岗位或政策信息，只读 | 可使用确定性批处理 |
| `R1` | 腾讯内部数据、内部评估资产，或任何可识别员工/候选人的信息；公开履历也属于 R1 | 主进程执行；最小化取数；业务对象隔离；默认串行 |
| `R2` | 对外发送、业务回写、流程推进、约面、改面、取消、面评提交、消息或外呼等副作用操作 | 主进程串行；逐项走原 Skill 安全门；确认绑定具体 payload；必须幂等和可审计 |

风险级别必须同时存在于 execution 和每个 task：

- `task.risk_level` 表示该原子任务的实际风险；
- `execution_risk` 必须等于所有 task 中的最高风险；
- 当前两个 MVP 试点固定为 R1；R2 字段仅作为协议预留，不得据此开启批量写操作。

当前平台下，`Task(subagent_name=...)` 不属于任何等级的允许方式。所谓隔离执行，只能通过 Skill 已声明的批量接口、独立脚本输入或明确分段的主进程调用实现。

## 4. 何时加载本契约

仅满足以下任一条件时加载：

1. 命中能力注册表中的试点能力，且达到该能力的最小对象数；
2. 上游结构化结果将被下游机器消费，并且能力已登记；
3. 需要独立重试、缺口恢复或部分成功交付，并且能力已登记；
4. 用户明确要求对试点能力做批量覆盖检查。

“需要排序/去重”“包含两个步骤”本身不足以触发。单 Skill 已有成熟 Flow 时，继续遵守原 Flow，不额外套任务清单。

## 5. 执行前：任务清单

任务清单必须符合 `schemas/task-envelope.schema.json`，并通过：

```bash
python3 scripts/validate_execution.py --plan <plan.json>
```

原子任务边界是：

```text
一个业务对象 × 一个岗位 × 一个阶段 × 一个明确动作 × 一个量表版本
```

核心字段示例：

```json
{
  "schema_version": "1.0",
  "execution_id": "exec-<unique-id>",
  "objective": "脱敏后的用户目标，不擅自扩写",
  "execution_risk": "R1",
  "merge_strategy": "ranked",
  "context": {
    "key_dimensions": ["岗位核心维度"]
  },
  "tasks": [
    {
      "task_id": "t-001",
      "capability": "resume_evaluation_batch",
      "skill": "interview-assistant",
      "risk_level": "R1",
      "subject_scope": {
        "subject_type": "candidate",
        "subject_id": "candidate-001",
        "position_id": "position-001",
        "stage": "resume_evaluation",
        "rubric_version": "model-v1"
      },
      "action": "evaluate",
      "input_ref": ["resume://candidate-001"],
      "depends_on": [],
      "side_effect": false,
      "output_slot": "results.t-001",
      "status": "pending"
    }
  ]
}
```

检查规则：

1. `capability` 和 `skill` 必须与能力注册表一致；
2. 每个任务只有一个可验收目标和一个唯一输出槽位；
3. 所有依赖使用 `task_id`，禁止“上面那个结果”等模糊指代；
4. `subject_scope` 不得放姓名、电话、邮箱、身份证等直接标识，只使用任务内脱敏 ID；
5. 不同候选人、题目或其它业务对象不得共用同一个任务；
6. 任务清单之和覆盖用户目标，但不得扩展到未授权动作；
7. 任何 R2 任务都必须有确认摘要哈希、确认有效期、幂等键和审计引用；payload 变化后旧确认立即失效。

## 6. 执行后：结果信封

每个子任务必须输出符合 `schemas/result-envelope.schema.json` 的结果信封；试点业务数据还需分别符合：

- `schemas/resume-evaluation-data.schema.json`
- `schemas/question-audit-data.schema.json`

结果信封核心字段：

```json
{
  "schema_version": "1.0",
  "execution_id": "exec-001",
  "task_id": "t-001",
  "subject_ref": {},
  "status": "success",
  "data": {},
  "evidence": [],
  "missing_evidence": [],
  "risk_flags": [],
  "warnings": [],
  "validation": {
    "schema_valid": true,
    "business_rules": []
  },
  "error": null,
  "next_actions": []
}
```

约束：

- `subject_ref` 必须与任务的 `subject_scope` 完全一致；
- `data` 只放本任务事实或业务对象，不混入其它任务推断；
- 每个已评分维度必须回指本结果信封内的 `evidence_id`；
- 信息不足必须进入 `missing_evidence`，不能强行评分；
- 失败、缺失和权限不足必须显式保留；
- 手机号、邮箱、身份证等敏感字段禁止进入跨任务信封；
- 下游只消费声明字段，不从自然语言摘要猜入参；
- `next_actions` 只是建议，必须重新经过主 Agent 路由、分级和必要确认，不能自动执行。

最终执行包校验：

```bash
python3 scripts/validate_execution.py \
  --plan <plan.json> \
  --results <results.json> \
  --final
```

## 7. 确定性归并

当前两个试点使用：

```bash
python3 scripts/reduce_controlled_execution.py \
  --plan <plan.json> \
  --results <results.json> \
  --output <summary.json>
```

程序负责：

- 按 task ID 收集并检查缺失、重复和多余结果；
- 检查业务对象作用域、状态、证据引用和敏感字段；
- 简历评估按原始维度分数与权重计算加权分，不修改原始评分；
- 题目审核统计维度覆盖、遗漏、过度覆盖和检查项分布；
- 失败与阻断任务原样保留；
- 在汇总产物中保留完整 `source_results`，防止二次改写造成信息损耗。

模型只负责解释确定性汇总结果，不得修改原始评分、证据、失败状态和计算结果。

## 8. 运行经验只能成为候选规则

运行中发现的新方法、接口参数或失败规避方式，只能记录为 `experience_candidate`：

```json
{
  "trigger": "适用条件",
  "observation": "实际现象",
  "proposed_rule": "候选改进",
  "evidence": [],
  "privacy_review": "passed | required",
  "fairness_review": "passed | required | rejected",
  "replay_test": "passed | failed | pending",
  "approval": "pending",
  "target_version": null,
  "rollback_plan": null
}
```

允许沉淀通用方法、正确参数组合、错误恢复方式和经过验证的数据口径。禁止沉淀候选人个人信息、个人偏好和薪资、未验证的淘汰规律，以及可能形成性别、年龄、学校等歧视的经验。

候选经验只有经过脱敏、多案例回放、公平性检查、招聘专家审核、版本发布并具备回滚方案后，才能进入正式规则。运行时不得自行修改长期规则。

## 9. 结束检查与指标

交付前确认：

- 原始目标没有扩展；
- 每个业务对象都有唯一 task、状态和输出；
- 不存在跨候选人或跨题目污染；
- 所有失败和缺失均被保留；
- 汇总数字与任务明细闭合；
- 敏感信息未进入跨任务结果；
- 原始评分和证据未被模型改写；
- 一次运行经验未被自动升级为长期规则。

试点指标：

- 任务覆盖率；
- 证据保留率；
- 静默丢失率；
- 跨业务对象污染率；
- Schema 合格率；
- 人工推翻率；
- 同量表评分一致性；
- 未确认写操作数与敏感信息泄漏数，目标均为 0。
