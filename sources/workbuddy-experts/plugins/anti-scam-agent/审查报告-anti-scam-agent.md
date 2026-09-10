# 专家包审查报告 - anti-scam-agent

## 一、总体结论

**整体结论：需修复后方可上架**

- 来源类型：external（腾讯云天御团队通过 zip 提交）
- 阻断问题（BLOCKER）：1 个
- 建议改进项（SUGGESTION）：6 个
- 不在审查范围（仓库管理员职责）：3 项

## 二、基本信息

| 项目 | 值 |
|------|------|
| 包名 | `anti-scam-agent` |
| 版本 | `1.0.0` |
| 作者 | 腾讯云天御（csig_lkfz_deld@tencent.com） |
| 类型 | agent |
| categoryId | `13-TencentZone`（腾讯专区） |
| Agent 文件 | `agents/anti-scam-agent.md` |
| Skills | 5 个：fraud-laundering、dark-grey-intel、debt-runner、victim、knowledge |
| 头像 | `avatars/expert.png`（512×512px，377KB） |

## 三、阻断问题（BLOCKER）— 必修

### B01 ❌ Skill 文件中硬编码认证凭据（Sign / CredentialId / ResourceID / InstanceID）

- **现状**：全部 5 个 Skill 的 `SKILL_windows.md` 和 `SKILL_unix.md`（共 10 个文件）中均硬编码了 `AUTH_CONFIG` 环境变量值，包含预签名凭据：

  ```
  $env:AUTH_CONFIG='{"Sign":"DQsZXjYVSigaJjNXVQAPQRIEARQ2GwgQHRVDYQ9fIEEGFVc2PRw6XSw9BmksTw0LKnhTEkpCHElYLh1ENkdZBDg8WhZMK1VKEgMmEzhMSxQ6fQZ/IydYKww7ez0xMxY8FAYOQiY7WTRdGF5VGGg7VTlcOBo9R11YGiJRPEEpEQ==","CredentialId":"crd-HvjD1b3q","ResourceID":"mcp-280b0453","InstanceID":"ins-3b7b6eb8"}'
  ```

  每个 Skill 使用不同的 `ResourceID`（如 fraud-laundering=`mcp-280b0453`、victim=`mcp-667476b4`），但 `Sign` 和 `CredentialId` 相同。

- **规范依据**：WorkBuddy专家开发规范.md §6.6 / §6.4 明确规定"专家包内任何位置都不得硬编码真实 Token / 密钥"。CODEBUDDY.md 安全规则要求"Secrets: env-only"。虽然该 Sign 是 amcpcli 的预签名凭据而非用户个人 Token，且使用时仍需用户完成 OAuth 认证，但将其以明文形式硬编码在 10 个文件中，存在凭据泄露风险——任何人获取该专家包即可获得这些预签名凭据。

- **修复方案**：
  - 方案 A（推荐）：改用规范支持的 `.mcp.json` + `dependencies` 声明方式，将 MCP 连接信息通过 `x-workbuddy` 元信息声明，凭据部分走 `tokenSchema` 让用户填入或通过 OAuth 流程获取
  - 方案 B：如果 amcpcli 机制必须使用预签名凭据，建议将 Sign/CredentialId/ResourceID/InstanceID 提取为环境变量占位符（如 `${AMCP_SIGN}`），在 Skill 中引用，由用户在首次使用时通过引导填入或由部署端注入
  - 方案 C：如确认为可公开的公共服务凭据（不涉及敏感权限），请在报告中明确说明并经安全团队确认后放行

## 四、建议改进项（SUGGESTION）

### S01 ⚠️ SKILL.md description 存在双句号笔误

- **现状**：3 个 Skill 的 `SKILL.md` frontmatter `description` 字段末尾出现连续两个句号"。。"：
  - `skills/dark-grey-intel/SKILL.md`：`...黑灰产生态链分析。。通过 amcpcli 二进制对接`
  - `skills/debt-runner/SKILL.md`：`...专题情报。。通过 amcpcli`
  - `skills/knowledge/SKILL.md`：`...风控方案查询。。通过 amcpcli`
- **规范依据**：文案质量
- **修复方案**：将"。。"改为"。"

### S02 ⚠️ 残留文件未清理

- **现状**：
  - `avatars/.gitkeep` — git 占位文件，不应包含在交付的专家包中
  - 5 个 `_user_meta.json`（每个 skill 目录下一个）— WorkBuddy 客户端安装时生成的元数据文件，不应包含在源包中
- **修复方案**：删除 `avatars/.gitkeep` 和所有 `skills/*/\_user_meta.json`

### S03 ⚠️ Windows 安装脚本修改用户级 PATH 环境变量

- **现状**：所有 Skill 的 `SKILL_windows.md` 中 amcpcli 安装脚本包含：
  ```powershell
  $u=[Environment]::GetEnvironmentVariable("Path","User"); if ($u -notlike "*$d*") { [Environment]::SetEnvironmentVariable("Path","$u;$d","User") }
  ```
  这会永久修改用户级 PATH 环境变量。虽然 Skill 正文规则 #5 禁止对 `AUTH_CONFIG`/`MCP_CONFIG` 持久化，但安装脚本对 PATH 的持久化修改未在规则中覆盖，且未向用户明确提示。
- **修复方案**：在安装脚本前增加提示说明，或改为仅修改当前会话 PATH（`$env:Path`），不持久化到用户级

### S04 ⚠️ MCP 服务地址暴露内网 CLB 域名

- **现状**：所有 Skill 中硬编码了腾讯云内网 CLB 地址：
  ```
  http://lb-hcl91l4w-9x3l6p5id8zfs7h1.clb.nj-tencentclb.cloud/_llmsgw_/mcp/aga-6588cc10/mcp-280b0453
  ```
- **风险评估**：该地址是腾讯云内网负载均衡域名，暴露在专家包中。虽然用户无法直接访问（需 amcpcli 鉴权），但内网拓扑信息泄露属于安全卫生问题。
- **修复方案**：建议将该地址通过环境变量或配置注入，不硬编码在 Skill 文件中；或确认该 CLB 地址是否为公网可达地址

### S05 ⚠️ amcpcli 下载使用固定 URL 而非版本锁定

- **现状**：amcpcli 二进制下载地址为 `https://agent-identity-1302490086.cos.ap-guangzhou.myqcloud.com/cli/new/amcpcli_windows_amd64.exe`，未指定版本号，每次安装都会拉取最新版本。
- **风险**：latest 模式可能导致不同用户安装到不同版本，引发行为不一致
- **修复方案**：建议锁定特定版本号，或在安装后检查版本并提示

### S06 ⚠️ SKILL.md 正文极简，实际执行逻辑在子文件中

- **现状**：5 个 Skill 的 `SKILL.md` 正文仅包含操作系统路由表（指向 `SKILL_windows.md` / `SKILL_unix.md`），实际的工具列表、参数说明、工作流等全部在子文件中。每个 Skill 的 `SKILL_windows.md` 和 `SKILL_unix.md` 内容高度重复（仅 shell 语法差异）。
- **影响**：维护成本高——每次修改需同步两个文件；Skill 可读性下降
- **修复方案**：考虑将公共逻辑合并到 `SKILL.md` 正文中，仅将 OS 相关的安装命令和语法差异放在子文件中

## 五、深度质量评审

| 维度 | 评级 | 判断 |
|------|------|------|
| AI 可执行性 | 优 | Agent MD 路由规则清晰，含完整意图→Skill→工具映射表和快速路由示例，AI 能准确判断该调哪个 Skill 和工具 |
| 路由/触发清晰度 | 优 | 复杂度分级（简单/中等/复杂）明确，触发词定义清晰，视角硬约束（黑灰产侧/受害者侧/双侧）防止误调用 |
| 上下文效率 | 优 | 最小调用原则——简单问题只加载 1 个 Skill，禁止"保险起见"扩展无关 Skill；零命中来源彻底不展示 |
| 容错降级 | 优 | 明确标注工具已知 bug（如 `evil_bankcard_stats_query` 的 dimensions/filters 失效）并提供绕开方案；`victim_aggregate` 降级场景定义清晰 |
| 角色边界 | 优 | 服务边界明确（支持/拒绝清单），拒答话术规范；视角隔离严格（4 套口径互不混写） |
| 团队编排 | N/A | Agent 型，不适用 |
| 用户体验 | 优 | 输出口径规范（渠道名映射表），输出前强制自检流程，零命中不展示避免噪音 |
| 受众适配 | 优 | 面向风控/反洗钱/信贷风控/催收/安全情报团队，场景覆盖精准 |
| 可移植性 | 良 | 支持 Windows 和 macOS/Linux 双平台，但依赖 amcpcli 二进制和腾讯云内网 MCP 服务，跨环境可移植性受限 |
| 领域准确性 | 优 | 金融黑灰产术语专业（卡U、跑分、水房、承兑、四件套等），维度标准值字典完整（34 省份、94 银行、10 诈骗类型、4 风险等级） |
| 可维护性 | 良 | 文档结构清晰但 SKILL_windows/unix.md 高度重复，维护需双文件同步；Agent MD 质量极高 |

## 六、形状层检查结果（脚本确定性检查）

### 目录结构 ✅

| 检查项 | 结果 |
|--------|------|
| `.codebuddy-plugin/plugin.json` 存在 | ✅ |
| `agents/anti-scam-agent.md` 存在 | ✅ |
| `avatars/expert.png` 存在 | ✅ |
| `agents/`、`skills/`、`avatars/` 在插件根目录 | ✅ |
| `.codebuddy-plugin/` 下只有 `plugin.json` | ✅ |
| 不包含 `hooks/`、`commands/`、`.lsp.json` | ✅ |
| 无 `settings.json`（Agent 型不需要） | ✅ |

### plugin.json 字段 ✅

| 检查项 | 结果 |
|--------|------|
| `name` = `anti-scam-agent`（小写+连字符） | ✅ |
| `version` = `1.0.0`（语义化版本） | ✅ |
| `description`（英文一句话描述） | ✅ |
| `author` = {name, email} | ✅ |
| `expertType` = `agent` | ✅ |
| `agentName` = `anti-scam-agent` | ✅ |
| `agents` = `["./agents/anti-scam-agent.md"]` 路径存在 | ✅ |
| `skills` 5 个路径均存在对应 `SKILL.md` | ✅ |
| `displayName` = {en, zh} | ✅ |
| `profession` = {en, zh} | ✅ |
| `displayDescription` = {en, zh}，中文 41 字（40-50 字范围内） | ✅ |
| `avatar` = `avatars/expert.png`（文件存在） | ✅ |
| `categoryId` = `13-TencentZone`（合法分类） | ✅ |
| `defaultInitPrompt` = {en, zh} | ✅ |
| `defaultInitPrompt` 与 `quickPrompts[0]` 一致 | ✅ |
| `tags` = 3 个，每个 {en, zh} | ✅ |
| `quickPrompts` = 3 个，每个 {en, zh} | ✅ |
| `plugin` = `anti-scam-agent`（与 `name` 一致） | ✅ |
| 无已废弃字段（如 `expertCount`） | ✅ |

### Agent MD frontmatter ✅

| 检查项 | 结果 |
|--------|------|
| `name` = `anti-scam-agent`（与文件名、agentName 一致） | ✅ |
| `description`（英文描述） | ✅ |
| `displayName` = {en, zh} | ✅ |
| `profession` = {en, zh} | ✅ |
| `maxTurns` = 50 | ✅ |
| **无 `tools` 字段** | ✅ |

### 头像 ✅

| 检查项 | 结果 |
|--------|------|
| 格式 PNG | ✅ |
| 尺寸 512×512px | ✅ |
| 大小 377KB < 500KB | ✅ |

### 一致性约束 ✅

| 检查项 | 结果 |
|--------|------|
| `agentName` = Agent MD `name` = 文件名 | ✅ |
| `avatar` 路径指向实际存在的文件 | ✅ |
| `skills[]` 路径下存在对应 `SKILL.md` | ✅ |
| Agent frontmatter 无 `tools` 字段 | ✅ |
| 目录结构规范 | ✅ |

## 七、安全审查

### 安全亮点 ✅

- Agent MD 包含完善的安全边界设计：脱敏强制（手机号/银行卡/身份证/钱包地址等）、渠道名映射表（TG→加密群组等）、输出前强制自检流程
- 明确禁止输出内部实现细节（endpoint、SQL、ES DSL、索引名、表名、内部字段、脚本路径）
- 拒绝违法犯罪操作指导、规避风控、逃避监管
- amcpcli 鉴权流程设计合理：零自研鉴权、禁止复用旧态、鉴权失败不绕过
- 环境变量仅当前会话生效，调用后主动清理（Windows）/禁止 export（Unix）

### 安全风险

| 风险 | 级别 | 说明 |
|------|------|------|
| 硬编码 AUTH_CONFIG 凭据 | BLOCKER | 见 B01 |
| 内网 CLB 地址暴露 | SUGGESTION | 见 S04 |
| amcpcli 下载未锁版本 | SUGGESTION | 见 S05 |

## 八、不在审查范围（仓库管理员入库时处理）

- 目录重命名 `.workbuddy-plugin/` → `.codebuddy-plugin/`（本包已使用 `.codebuddy-plugin/`，无需处理）
- `expert_center.json` 条目追加 / 刷新 `updatedAt`
- `.codebuddy-plugin/marketplace.json` 条目追加 / 更新
- `avatars/` 根目录头像复制（`AntiScamAgent.png`）

## 九、修复优先级表

| 优先级 | 编号 | 问题 | 工作量 |
|--------|------|------|--------|
| P0 | B01 | 硬编码 AUTH_CONFIG 凭据（10 个文件） | 大（需重构凭据注入方式） |
| P1 | S02 | 残留文件清理（.gitkeep + _user_meta.json） | 小 |
| P1 | S01 | SKILL.md description 双句号笔误 | 小 |
| P2 | S03 | Windows 安装脚本 PATH 持久化提示 | 小 |
| P2 | S04 | 内网 CLB 地址暴露 | 中 |
| P2 | S05 | amcpcli 版本锁定 | 小 |
| P3 | S06 | SKILL.md 正文极简 / 子文件重复 | 中 |

## 十、亮点

1. **Agent MD 质量极高**：路由规则、复杂度分级、视角硬约束、输出前自检流程等设计专业且完善，是高质量 Agent prompt 的典范
2. **安全边界设计全面**：脱敏强制、渠道名映射、零命中不展示、静默后置上报等安全措施覆盖到位
3. **跨平台支持**：每个 Skill 提供 Windows（PowerShell）和 macOS/Linux（bash/zsh）双平台执行文件，覆盖主流环境
4. **容错降级经验沉淀**：SKILL 文件中详细标注了工具已知 bug 和绕开方案（如 dimensions 失效、filters 静默忽略等），体现了充分的实测验证
5. **维度标准值字典完整**：34 省份、94 银行、10 诈骗类型、4 风险等级的完整枚举，防止参数传错
6. **数据时效口径标注**：涉诈银行卡统计标注"半月延迟"，避免用户误读为实时数据
