# 面试域路由

> 只在一级 Agent 已判定为面试域后读取。本文件只定位 Skill/Flow，不复述各 Flow 的执行 SOP。

## 1. `interview-assistant`：面试执行侧

| 用户目标 | Flow |
|---|---|
| 我的面试待办 / 推荐待办 / 校招全环节待办与已办 | `T` / `T2` / `T4` |
| 给社招候选人发起面试流程 | `SI` |
| 发起校招/实习/青云面试流程 | `SC` |
| 首次约面、改期、取消、查日程 | `S` |
| 按 RID 拉单份简历详情 | `A` |
| 单份或同岗批量评简历 | `B` / `B2` |
| 针对候选人出题或生成面试计划 | `C` |
| 写面评、定位面评待办、校招面评提交 | `D` / `SE` |
| 面试官单场复盘、多场成长、招聘经理评估面试官 | `E` / `G` / `H` |

“发起面试流程”和“安排面试”必须区分：前者创建招聘流程，后者创建或变更面试日程。用户只说“安排一下”且对象还没有流程时，先按 Skill SOP 检查状态，不凭字面猜接口。

## 2. 其他 Skill

| 用户目标 | Skill |
|---|---|
| 甄选方法论、胜任力模型、面试设计、题目审核、面评审核、测评方案 | `assessment-quality-expert` |
| 面评 Excel/CSV 清洗成标准 JSON | `interview-data-processor` |
| 基于批量面评数据生成岗位能力模型 | `interview-talent-modeler` |
| 阅卷待办、建议分、成绩单、按自定义维度重评和导出 | `quiz-deliverable-evaluator` |

## 3. 必要消歧

### 建模

- 为一个新岗位定义人才标准/胜任力 → `assessment-quality-expert`；
- 已有大量面评数据，反推岗位模型 → `interview-talent-modeler`；
- 需求沟通后生成人才画像和 JD → 出域到 `requirement-communication-assistant`。

### 写 JD 的归属（易抢错）

- **从零写 JD**（只有岗位名或模糊需求，没有胜任力模型）→ 出域到 `requirement-communication-assistant`，这是默认归属；
- **基于已有模型派生 JD**（本域刚搭完模型，或已有活跃模型，用户说“按这个模型出份 JD”）→ 留在 `assessment-quality-expert`；
- 判据是**有没有可用的胜任力模型**，不是话术里有没有“JD”二字。没有模型就别留在本域。

### 出题

- 针对某位已知候选人的履历出个性化问题 → `interview-assistant · C`；
- 为岗位设计整套题本、评分锚点或审核题库 → `assessment-quality-expert`。

### 面评

- 写/提交某场面评 → `interview-assistant · D/SE`；
- 审核已有面评质量 → `assessment-quality-expert`；
- 批量清洗面评文件 → `interview-data-processor`；
- 批量面评反推岗位模型 → `interview-talent-modeler`；
- 复盘面试官表现 → `interview-assistant · E/G/H`。

### 评分

- 测验平台阅卷或成绩单重评 → `quiz-deliverable-evaluator`；
- 面试题质量审核/候选人面试评价 → 甄选或面试 Skill；
- 单份简历评估 → `interview-assistant · B`；批量搜索候选人 → 出域到搜索域。

## 4. 唯一约束

- 所有已知候选人的写操作必须先拿到正确 RID/traceId/FlowMainId 等对象标识；
- `B2` 和批量题目审核使用受控批处理契约；
- 发起流程、约面、改期、取消、提交面评均为 R2；
- 测验平台当前只读，AI 建议分不得写回；
- 具体模型、量表、模板和远程资产由命中的 Skill/Flow 加载，Router 不替代。

