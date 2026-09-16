# 备考状态与迁移规则

## 一、计划周期

一次同时规划和滚动调整的一组考试属于一个计划周期。多门考试共享同一个 `plan_cycle_id` 和 `plan_version`，不同学期或新一轮备考不得混用。

```yaml
plan_cycle_id: ""
timezone: ""
plan_version: 1
exams:
  - id: ""
    database_record_id: ""
    name: ""
    date: ""
    goal: ""
    current_level: ""
    scope_source: ""
    minimum_daily_minutes: 0
    priority: high | medium | low | pending
    status: active | completed | abandoned
constraints:
  daily_minutes: 0
  capacity_type: gross | net | unknown
  buffer_rate: 0.15
  unavailable_times: []
  preferred_session_minutes: 30
mode: term | sprint | rescue
assumptions: []
last_review_date: ""
next_review_date: ""
change_log: []
```

字段原则：

- 首次写入备考总览后，从批量新增响应 `results[0].id` 取得第一条考试记录 ID，在内部规范化为 `record_id` 并作为 `plan_cycle_id`，再回写该周期的全部考试和任务；禁止读取不存在的 `results[0].record_id`，也禁止自行编造周期 ID。
- `plan_version` 是计划周期级整数。第一次成形为 1；只有任务顺序、容量、范围或优先级发生实质变化时加 1。
- 一次重排影响多门考试时，各考试行的版本同步更新；计划变更记录必须写同一 `plan_cycle_id`。
- 仅更新完成度、掌握证据、耗时、卡点或解释文字，不改变后续计划时，不递增版本。
- 日期和提醒按 `timezone` 处理。用户未说明且任务不跨时区时使用其当前环境时区；存在旅行或异地考试时先确认。
- 查询到考试日期已过但状态仍为 `active` 时，先从本轮容量中排除，再确认“已考完 / 延期 / 仍需收口”；不把过期记录继续当作进行中考试。

## 二、知识点状态

```yaml
- id: ""
  database_record_id: ""
  plan_cycle_id: ""
  exam_record_id: ""
  subject: ""
  chapter: ""
  topic: ""
  scope_source: ""
  exam_weight: high | medium | low | unknown
  mastery: proficient | uncertain | not_learned | unverified
  estimated_minutes: 0
  status: not_started | learning | due_for_review | verified
  evidence_type: answer | practice | recall | mock | correction | self_report | none
  evidence: ""
  next_action: ""
  review_stage: 0
  review_count: 0
  next_review_date: ""
```

### 掌握与复习迁移

- 新知识点默认 `unverified`；明确完全未学时记为 `not_learned`。两者只排学习或验证任务，不进入到期复习。
- 只看过、抄完、听懂或主观感觉良好，不得进入 `proficient`。
- 第一次与目标匹配的独立验证达到完成标准：`mastery=proficient`、`status=due_for_review`、`review_stage=0`，用 `scripts/review_schedule.py baseline_pass` 计算 1 天后的复习日期；已启用台账但覆盖清单尚未创建时，按需创建并写入该知识点的最小记录，不能只把日期留在对话里。
- 到期复习正确：保持 `proficient`，按阶段依次安排 3、7、15 天；完成 15 天阶段后转 `status=verified`，清空普通下一复习日期。
- 到期复习模糊、错误或遗忘：`mastery=uncertain`、`status=due_for_review`、`review_stage=0`，下一次回到 1 天。
- 高权重内容即使 `verified`，考前仍可安排 `recall` 回炉任务；回炉不改写已经完成的普通间隔阶段，除非新证据显示遗忘。
- 下一复习日期必须使用 `scripts/review_schedule.py` 计算；脚本失败时不写日期，改为待确认。

## 三、每日任务

```yaml
- id: ""
  database_record_id: ""
  plan_cycle_id: ""
  exam_record_id: ""
  knowledge_record_id: ""
  date: ""
  due_date: ""
  priority: A | B | C
  task_type: learning | review | mock | recall
  action: ""
  topic: ""
  estimated_minutes: 0
  completion_criteria: ""
  status: completed | partial | not_started | cancelled | replaced
  actual_minutes: 0
  mastery: proficient | uncertain | not_learned | unverified
  review_result: correct | fuzzy | wrong | unverified
  blocker: ""
  error_reason: cannot_do | too_large | schedule_conflict | estimate_error | fatigue | missing_material | ineffective_method | none
  insight_path: ""
  previous_task_id: ""
  change_reason: ""
```

### 任务标识与匹配

- 对用户展示的任务 ID 可使用 `A1`、`B2` 等短号，但只在同一计划周期、考试和日期内唯一。
- 更新记录必须用 `plan_cycle_id + exam_record_id + date + task_id` 联合匹配；仍不唯一时再用动作或知识点消歧，禁止只凭 `A1` 更新。
- `due_date` 只用于复习或回炉任务，记录该任务原本应复习的日期；学习和模考留空。
- `review_result` 只记录本次复习证据：正确、模糊、错误或未验证。看板的到期复习正确率以它为口径，不用任务完成度或掌握度代替。

### 任务状态迁移

- `completed`：达到任务完成标准；是否掌握仍由证据单独判断。
- `partial`：只完成部分标准；下一轮保留已完成部分，不默认整项重做。
- `not_started`：先判断原因，不自动判定为懒惰或执行力差。
- `cancelled`：任务已无价值、容量不足或条件不成立。
- `replaced`：用更小前置任务、替代练习或更合适任务替换，并填写 `previous_task_id` 和原因。
- `insight_path` 只记录用户实际形成的想通路径；用户尚未想通时留空。

## 四、每次打卡后的状态迁移

1. **锁定周期**：先定位唯一的进行中计划周期；多个周期无法唯一判断时请用户选择。
2. **匹配原任务**：使用计划周期、考试记录、日期和任务 ID 联合匹配。
3. **更新执行结果**：记录完成状态、实际耗时、卡点与错误原因。
4. **更新掌握证据**：只根据答题、实操、复述、真题、自测或错题复做改变掌握状态；“不会”按是否尝试过归为 `uncertain` 或 `not_learned`。
5. **计算复习状态**：复习任务记录 `due_date` 和 `review_result`；需要下一日期时调用确定性脚本。
6. **校正估时**：同类任务有至少两条历史时，参考最近三次实际耗时中位数；条件变化时说明不直接套用。
7. **检查重排触发器**：连续未完成、耗时偏差、新高权重弱项、范围或日程变化、容量溢出、疲劳、受挫或断档积压。
8. **处理断档积压**：保高权重和临考内容，低权重复习顺延，不要求一次清零。
9. **提交版本变化**：仅实质重排时生成差异；所有受影响记录写入并回读成功后，再追加计划变更记录并确认新版本。部分失败不得宣称新版本已完整生效。
10. **给出下一入口**：明确用户完成什么后反馈哪些字段。

## 五、变更日志

每次实质重排追加一条周期级记录：

```yaml
- plan_cycle_id: ""
  version: 2
  reason: "A1 实际耗时 80 分钟，超过原估时且卡在前置知识"
  kept: ["task-a2"]
  moved: ["task-b1"]
  removed: ["task-c1"]
  added: ["task-a1-foundation"]
  replaced:
    - from: "task-a1"
      to: "task-a1-foundation"
  unresolved: ["考试范围仍待确认"]
```

理由必须对应用户反馈、练习证据或现实约束，不能只写“优化计划”。

## 六、多考试分配

1. 更新同一计划周期内每门考试的日期、目标、范围依据、当前基础和最低保障。
2. 使用 `decision-guide.md` 的稳定排序规则确定主攻科目。
3. 先分配最低保障，再分配剩余净容量。
4. 某门考试结束、目标完成或日程变化后，释放容量；只有后续任务发生变化时才生成新版本。
5. 范围和基础不足时将优先级标为 `pending`，同时给出最低风险诊断任务。

## 七、跨会话续接与摘要兜底

- 用户说“继续”等续接语时，先按 `library-integration.md` 查找约定标题的总览表，再定位唯一的进行中计划周期；不要求用户先说明是否启用。
- 用户已启用台账：读取当前周期的考试、今日与逾期任务、到期复习和最近版本；结束时简短说明本轮写入结果。
- 用户未启用、拒绝记录或资料库不可用：当前对话维护简化状态，每次形成或实质重排计划后附可复制摘要：

```markdown
【下轮状态摘要｜计划 vN】
- 考试：名称｜日期｜优先级｜最低保障
- 时区与每日净容量：
- 当前主攻与主要约束：
- 未完成任务：日期｜任务 ID｜考试｜动作｜预计时长｜完成标准
- 到期复习：日期｜知识点｜当前阶段
- 已验证掌握与证据：
- 待确认：
- 下次反馈：任务 ID｜完成度｜掌握度｜实际耗时｜卡点
```

没有可用台账、可复制摘要或用户提供的历史记录时，不假装记得原计划。

## 八、记录与授权

- 用户明确要求开启台账、保存计划、记录打卡或继续已有台账时，加载平台内置「资料库」能力，按当前空间分类和写入规则处理，不另造重复确认。
- 只增量更新已匹配记录，不覆盖无关内容；删除、字段类型转换等有数据损失风险的动作必须另行明确。
- 资料库记录 ID 只从创建或最新查询结果取得；禁止猜测、截断或跨表复用。
- 旧台账缺少 `计划周期ID`、`应复习日期`、`复习结果` 等当前字段时，可只读恢复单一明确周期；写入前说明需要升级字段或新建当前结构，不静默改表，也不把多个旧周期合并推断。
- 只记录规划需要的信息，不保存无关敏感字段。
