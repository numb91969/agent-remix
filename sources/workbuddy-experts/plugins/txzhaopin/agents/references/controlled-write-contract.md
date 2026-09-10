# 招聘 Agent 受控写操作契约

> 版本：1.0（txzhaopin v1.11.3 MVP）
>
> 用途：把用户确认绑定到真正执行的 payload，防止重复外呼、重复通知和确认后参数漂移。本契约不授予新权限，也不替代各 Skill、MCP 或服务端安全门。

## 1. 当前启用范围

仅启用 `capability-registry.yaml` 中登记的动作：

- `social_interview_start`
- `campus_interview_start`
- `campus_evaluation_submit`
- `social_job_intention_outbound`
- `hrclaw_mail_send`
- `hrclaw_tips_send`

其中 `social_interview_start` 仅覆盖社招发起面试流程的 `start_interview`，`campus_interview_start` 仅覆盖校招/实习发起面试流程的 `start_campus_interview`（成功引用为 `interview_id`，支持一次为 ≤20 名候选人各创建独立流程的批量目标），`campus_evaluation_submit` 仅覆盖校招面评提交的 `submit_interview_flow_trace`（成功引用为 `traceId`，单目标；HR面试/通道面委环节不在覆盖范围）；后续约面下单、改面、取消、社招面评提交、自动化创建/删除等写操作继续遵守原 Skill Flow，在单独登记、补齐字段和回归测试前不得假装已经接入本契约。

使用 `recruit-mcp` 的写动作还必须在 `write_actions.<action>.backend_binding` 中登记完整能力 ID。
执行前必须通过 SearchAPI 按当前用户权限重新发现并读取详情；本轮返回的完整原始 ID 必须与
`backend_binding.capability_id` 逐字一致。未返回、不可见、名称近似但 ID 不同或 Schema 已漂移时一律
失败关闭，不得沿用历史接口信息；先更新注册表与回归用例，再恢复执行。该绑定只证明动作已经过治理，
不替代本契约的确认、权限和业务校验。

## 2. 五步握手

1. **冻结 payload**：按注册表的 `payload_fields` 生成最终请求体；缺省字段也要用明确的 `null`、`false` 或空数组表达。
2. **计算摘要**：对 UTF-8、键排序、无多余空白的规范 JSON 计算 SHA-256。需要脚本时，将 payload 通过标准输入交给：

   ```bash
   python3 scripts/validate_write_action.py --digest < payload.json
   ```

   只输出摘要，不输出 payload。若必须使用临时文件，权限设为仅当前用户可读，完成后立即删除，禁止进入埋点、日志和最终回复。
3. **展示并确认**：向用户展示业务可读的通道、对象、岗位/标题、时间和影响；确认有效期固定为 10 分钟。不要展示手机号、身份证、Cookie、Token 或完整内部请求。
4. **确认后校验**：把同一 `payload_digest` 写入写操作信封及 `confirmation.payload_digest`，执行：

   ```bash
   python3 scripts/validate_write_action.py --envelope <envelope.json> --phase preflight
   ```

   payload 任一字段变化、确认过期或目标变化，旧确认立即失效，必须重新计算摘要并确认。
5. **执行并审计**：只发送已确认摘要对应的 payload。成功记录服务端任务 ID / `msgId`；失败保留真实错误码；网络中断或返回不明确标记 `unknown`，禁止自动重试。

## 3. 幂等边界

- `idempotency.key` 是当前会话的请求身份，不等于服务端一定支持技术幂等。
- AI 外呼只有业务频控与去重，注册表标记为 `business_dedup_only`；仍须服从服务端 `errorCode`。
- HRClaw 当前没有幂等接口，注册表标记为 `none`。发送后结果未知时不得再次发送；先核实消息记录，无法核实时让用户重新确认。
- 任何重试都必须产生新的确认记录；不得因“刚才应该没成功”而自动重放。

## 4. 审计状态

写操作信封符合 `schemas/write-action-envelope.schema.json`：

- `prepared`：已确认、尚未调用；
- `submitted`：已经调用，结果尚未明确；
- `success`：必须记录动作注册表指定的成功引用：社招发起面试为 `FlowMainId`，校招发起面试为 `interview_id`，校招面评提交为 `traceId`，AI 外呼为 `aiCallTaskId`，HRClaw 为 `msgId`；
- `failed`：必须记录真实错误码；
- `unknown`：结果不明确，禁止自动重试。

结果确定后执行：

```bash
python3 scripts/validate_write_action.py --envelope <envelope.json> --phase outcome
```

## 5. 隐私与候选人体验

- 信封只保存目标数量与目标摘要，不保存手机号、邮箱、身份证或消息正文；
- 确认摘要只保留业务必要信息；
- 不允许把完整 payload 放入 tracking 事件；
- 外呼承诺、频控、拒绝联系、投诉和隐私诉求仍以 outbound Skill 与服务端规则为准；
- 本契约校验通过不代表业务动作一定允许执行，所有原安全门必须同时通过。
