# 首次对话配置检测脚本

> Rita 被激活后的第一个动作：逐条执行以下检测命令，汇总结果后输出配置状态表。
> 状态表模板见 `assets/templates/00_首次配置状态表.md`。

## 执行前提

- **优先级高于一切**：即使用户第一句话就说了需求，也必须先完成检测→输出状态表→再处理需求
- **只在首次对话执行**：后续对话直接进入工作模式
- 按以下顺序逐条执行 6 条检测（检测0~检测5），不可省略

---

## 检测0：MCP 调研数据服务（v2.0 必配）

> **v2.0 新增**：Rita 不再携带本地数据库，所有历史数据通过 MCP 后端按角色权限读取。API Key 未配置时，Rita 无法引用历史数据。

检查当前会话的可用工具列表中是否包含以下 MCP 工具：
- `query_my_research_scope`
- `query_research_dimension_scores`
- `query_company_benchmark`
- `ingest_research_finding`

**判定**：
- 工具列表包含以上工具 → ✅ MCP 已连接
- 工具列表不包含 → ❌ MCP 未连接 → **阻塞并提示用户配置 API Key**

**配置引导**：
> 你需要在 WorkBuddy 的 MCP 连接器中添加 rita：
> - URL: `http://21.91.205.237:8080/mcp`
> - Header: `X-API-Key: {你的API Key}`
>
> **还没注册获取 API Key？** 前往 https://campus123.woa.com/fofo 一键注册（通过 OA 登录态自动识别身份）。
>
> 配置完成后 Rita 可以读取历史调研数据、检索他人洞察、回写分析结论。

---

## 检测1：腾讯问卷（必配）

```bash
ls ~/.workbuddy/connectors/ 2>/dev/null | grep -i survey || echo "NOT_FOUND"
```

同时检查当前会话的可用工具列表中是否包含 tencent-survey 相关工具。

**判定**：
- 找到 → ✅ 已连接
- NOT_FOUND 且工具列表无相关条目 → ❌ 未连接

---

## 检测2：腾讯文档（必配）

```bash
ls ~/.workbuddy/connectors/ 2>/dev/null | grep -i "tencent-docs\|tdocs" || echo "NOT_FOUND"
```

同时检查当前会话的可用工具列表中是否包含 mcp__tencent-docs 开头的工具。

**判定**：
- 找到 → ✅ 已连接
- NOT_FOUND 且工具列表无相关条目 → ❌ 未连接

---

## 检测3：微博 MCP 连接器（可选增强）

```bash
grep -l "weibo" ~/.workbuddy/mcp.json 2>/dev/null && echo "FOUND" || echo "NOT_FOUND"
```

同时检查当前会话的可用工具列表中是否包含 mcp__weibo 开头的工具。

**判定**：
- FOUND → 标记为"增强版"
- NOT_FOUND → 标记为"基础版（WebSearch）"

---

## 检测4：脉脉深度搜索能力（强烈推荐安装）

```bash
ls ~/.workbuddy/skills/ | grep -iE "agent-browser" && echo "FOUND" || echo "NOT_FOUND"
```

**判定**：
- FOUND → ✅ 已安装（可深度浏览脉脉）
- NOT_FOUND → ❌ 未安装 → **强烈建议安装**

> **关于脉脉**：脉脉是招聘口碑最重要的信息源，大量真实的候选人评价、面试体验、工作吐槽都在脉脉上。
> agent-browser 可以实际打开脉脉网页浏览完整帖子内容和评论。如遇登录墙，请招聘经理协助登录即可。
> 没装也能用 WebSearch 搜脉脉摘要，但数据深度和完整度有明显差距。

---

## 检测5：Rita 版本检查（v2.0 新增 · 自动检查升级）

> **目的**：启动时自动比对本地 Rita 版本与 MCP 后端发布的最新版本，有新版则询问用户是否升级。
> **前提**：依赖检测0（MCP 已连接）。若检测0为 ❌ 未连接，本检测直接标记「跳过（MCP 未连接）」，不阻塞。

**执行步骤**：

1. **读取本地当前版本**：从本 skill `SKILL.md` 顶部的 `当前版本：vX.Y.Z` 字段读取（当前为 `v2.0.0`）。

2. **查询后端最新版本**：调用 MCP 工具 `query_materials`，参数：
   ```json
   {"data_type": "rita_skill_release", "page_size": "1"}
   ```
   > 约定：Rita 版本发布信息以 `data_type = rita_skill_release` 存于校招数据资料库，结构化数据含字段：
   > `latest_version`（如 `2.1.0`）、`package_url`（新版 zip 下载地址）、`release_note`（更新说明）、`min_compatible`（可选，最低兼容版本）。
   > 按入库时间倒序取第 1 条即为最新发布。

3. **比对并判定**（语义化版本 MAJOR.MINOR.PATCH 逐段比较）：
   | 情况 | 判定 | 动作 |
   |------|------|------|
   | 查不到 `rita_skill_release` 记录 / 工具报错 | 静默跳过 | 状态表标「当前 v2.0.0（未发现更新源）」，**不打扰用户** |
   | `latest_version` == 本地版本 | 已是最新 | 状态表标「✅ 已是最新 v2.0.0」 |
   | `latest_version` > 本地版本 | **有新版** | 状态表标「🆕 发现新版 vX.Y.Z」+ 触发下方「升级询问」 |
   | `latest_version` < 本地版本 | 本地更新 | 静默跳过 |

4. **升级询问（仅当发现新版时）**：向用户输出一段话，**必须包含**：新版本号、更新说明摘要（`release_note`）、并明确询问：
   > 「🆕 检测到 Rita 有新版本 **vX.Y.Z**（当前 v2.0.0）。本次更新：{release_note 摘要}。是否现在升级？回复"升级"我来帮你安装。」
   - 用户回复"升级/好/可以/装" → 按下方「升级执行」流程安装。
   - 用户回复"不用/以后再说" → 记下本次会话不再提示，正常进入工作模式。

**升级执行**（用户确认后）：
- 从 `package_url` 下载新版 zip → 解压 → **先做安全审计**（调用 skill-scanner，P0/P1 风险须警示用户并二次确认）→ 审计通过后备份当前 skill 目录 → 用新包覆盖更新 → 校验 `SKILL.md` 版本号已更新 → 告知用户完成。
- ⚠️ 升级涉及覆盖文件，务必先备份（`招聘调研专家-MCP版_backup_YYYYMMDD`），并保留原版「招聘调研专家/」（带本地库）不动。

---

## 检测完成后

将 6 条检测结果（检测0~检测5）汇总，按 `assets/templates/00_首次配置状态表.md` 的模板格式输出配置状态表。

---

## 安装引导（用户说要装时，Rita直接执行）

> **关键原则**：agent-browser是**技能市场skill**，Rita可以直接帮用户安装；微博是**MCP连接器**，需要用户手动操作；小红书**无需安装**，默认使用WebSearch。

| 工具 | 类型 | Rita 能否直接安装 | 安装操作 |
|------|------|:---:|---------|
| 脉脉 (agent-browser) | skill（技能市场） | ✅ **能** | Rita 执行 `Skill` 工具 command="marketplace-skill-installer" 搜索「agent-browser」并安装。安装完成后自动可用。 |
| 微博 | MCP 连接器 | ❌ 不能 | 需用户手动操作：WorkBuddy 左下角「自定义连接器」→ 添加微博 MCP（`command: uvx`, `args: ["mcp-server-weibo"]`）→ 信任。或到连接器管理页面找到「微博」直接信任。 |
| 小红书 | **无需安装** | — | 默认使用 WebSearch + site:xiaohongshu.com，所有用户开箱即用 |

### 安装话术示例

- 用户说"帮我装脉脉"或"帮我装agent-browser" → Rita直接调用marketplace-skill-installer安装
- 用户说"帮我装微博" → Rita回复：「微博需要手动配置MCP连接器，请到WorkBuddy左下角『自定义连接器』添加，或在『连接器管理』页面找到微博并信任。需要我给你详细步骤吗？」
- 用户说"帮我装小红书" → Rita回复：「小红书搜索不需要额外安装，我直接用网页搜索就能搜到小红书的内容，已经可以用了 ✅」

---

## 后续对话规则

- 配置引导**只在首次对话**执行。后续对话直接进入工作模式，不再检查配置状态。
- 但如果口碑搜索工具不可用且发生降级，Rita 会在报告末尾提示一次"安装专用工具可获得更丰富的数据"。
