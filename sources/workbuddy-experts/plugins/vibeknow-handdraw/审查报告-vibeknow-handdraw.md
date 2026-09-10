# 专家包审查报告 - vibeknow-handdraw

> 来源类型：external
> 专家类型：agent（Agent 型单专家）
> 版本：2.0.3
> 审查日期：2026-08-12

---

## 一、总体结论

**整体结论：可上架**

- 来源类型：external（vibeknow，dev@vibeknow.com，外部合作方提交）
- 阻断问题（BLOCKER）：0 个
- 建议改进项（SUGGESTION）：5 个
- 不在审查范围（仓库管理员职责）：3 项

---

## 二、阻断问题（BLOCKER）— 必修

无。

---

## 三、建议改进项（SUGGESTION）

### S01 ⚠️ SKILL.md 路径示例为 macOS 个人路径格式

- **现状**：`skills/handdraw/SKILL.md:13` 写道：
  ```
  SKILL_DIR="<local-user-path><你>/.workbuddy/plugins/marketplaces/my-experts/plugins/vibeknow-handdraw/skills/handdraw"
  ```
  虽然用了 `<你>` 占位符（非真实个人路径），但路径格式是 macOS 专用的（`<local-user-path> 用户（`C:\Users\...`）无法直接参考。
- **规范依据**：安全规则 — 通用性要求 / CODEBUDDY.md §十七
- **修复方案**：将路径示例改为更通用的描述，如 `SKILL_DIR="<SKILL.md 所在目录的绝对路径>"`，或同时给出 macOS/Windows 两种示例。agent MD 中已正确用了 `SKILL_DIR="<handdraw SKILL.md 所在目录>"` 的通用写法，SKILL.md 可对齐。

### S02 ⚠️ README 引用了包内不存在的脚本

- **现状**：`README.md` 的"本地安装"章节引用了 `bash install-local.sh` 和 `bash pack.sh`，但 zip 包内不包含这两个文件（它们是开发仓库中的辅助脚本，未打包进发布包）。
- **规范依据**：CODEBUDDY.md §五 / §十七 — 依赖引导完整性
- **修复方案**：在 README 中注明 `install-local.sh` / `pack.sh` 仅存在于开发仓库，发布包用户通过 `node "$SKILL_DIR/scripts/run.mjs" init` 安装依赖即可；或从 README 中移除对这两个脚本的引用。

### S03 ⚠️ 安装说明偏 macOS，缺少 Windows 平台指引

- **现状**：README 安装步骤写 `Cmd+Q` 退出 WorkBuddy（macOS 快捷键）、路径用 `<local-user-path> 格式、图片编码降级链首选项 `sips`（macOS 专有命令）。Windows 用户缺少对应指引。
- **规范依据**：可移植性 — CODEBUDDY.md §十七
- **修复方案**：补充 Windows 平台的快捷键说明（如 `Ctrl+Q` 或任务栏退出）、路径示例；编码器降级链已有 `magick`/`convert`/`ffmpeg` 兜底（跨平台），无需改代码，仅需在 README 中注明 Windows 用户需确保 `ffmpeg` 或 `ImageMagick` 可用。

### S04 ⚠️ displayDescription.zh 字数在下限边界

- **现状**：`displayDescription.zh` = "老师讲考点、医生讲术后护理、工程师讲原理，专业内容边画边讲成手绘科普视频，51种风格随选。"
  - 不含标点约 38 个中文字符 + "51" 2 个数字字符 = 40 字符，处于规范要求的 40-50 字下限边界。
- **规范依据**：CODEBUDDY.md §3.5 / WorkBuddy专家开发规范.md §3.3 — 中文字数须在 40-50 字之间
- **修复方案**：可适当补充 2-3 字使字数更稳定地落在 40-50 区间，如"...51 种手绘风格随选"或"...51种风格可选"。当前不阻断上架。

### S05 ⚠️ `mcp/` 目录命名可能引起混淆

- **现状**：包内有 `mcp/` 目录（含 `server.mjs`、`auth-login.mjs`、`token-path.mjs`），但 README 和 plugin.json 均明确声明"无 MCP、无连接器"。`mcp/` 实际是零外部依赖的客户端函数库，供 skill 脚本经 Bash 调用。
- **规范依据**：CODEBUDDY.md §二 / §五 — 目录命名应避免与规范概念混淆
- **修复方案**：考虑将 `mcp/` 重命名为 `lib/` 或 `client/`，消除"MCP 服务声明"的歧义。此为架构层面的命名建议，不阻断上架。

---

## 四、深度质量评审

| 维度 | 评级 | 判断 |
|------|------|------|
| AI 可执行性 | 优 | SOP 极其详尽：6 步流程（理解输入→写讲稿拆页→选风格→逐页出图→逐页绘制→串成成片），每步都有具体脚本命令、参数、输出格式。关键防错约束（同号配对铁律、串行出图、尺寸三处一致）硬编码在 prompt 和脚本中。 |
| 路由/触发清晰度 | 良 | Agent 型单专家无需多角色路由。SKILL.md description 和 agent frontmatter description 均清晰描述了触发场景与能力边界。 |
| 上下文效率 | 良 | Agent prompt ~6900 字符，信息密度高但无冗余。references 文件（styles.md、visual-rules.md）按需加载，避免上下文膨胀。关键约束重复强调属于必要的防错设计。 |
| 容错降级 | 优 | 亮点：积分不足 SOP（禁止自由发挥，结构化报错→引导充值→可选降级）；渲染超时处理（不重跑，轮询等文件出现）；空绘制数据防御（hasDrawing 校验，不写空 vec.json）；图片编码降级链（sips→magick→convert→ffmpeg，全不可用回退原字节）；出图尺寸预检（check-images.mjs 掏钱前拦截）。 |
| 角色边界 | 优 | 明确区分本地能力（讲稿/分镜/出图/渲染）与远端服务（手绘绘制/TTS），标注哪些需登录/积分。Agent 不自行排查或替代远端能力。 |
| 团队编排 | N/A | Agent 型单专家，无团队编排。 |
| 用户体验 | 良 | defaultInitPrompt 和 quickPrompts 有具体使用场景（公众号文章→手绘科普、术后护理→手绘讲解、水墨风短片）。交付时明确告知成片路径和 job 目录。首次使用需 `run.mjs init` 安装依赖（可能耗时数分钟）+ 登录授权。 |
| 受众适配 | 良 | 面向教师、医生、工程师等需要将专业内容科普化的群体。51 种手绘风格覆盖中国传统/插画绘本/现代设计/卡通动漫/艺术流派/版画手工 6 大类，适配面广。 |
| 可移植性 | 待改进 | 安装说明偏 macOS（Cmd+Q、<local-user-path> 路径、sips 编码器）。render 依赖 Node.js + chrome-headless-shell，跨平台可行但 Windows 用户需自行确保 ffmpeg/ImageMagick 可用。 |
| 领域准确性 | 优 | 手绘动画制作流程专业完整：分镜→出图→矢量化→渲染。visual-rules.md 对画面描述的约束极其专业（禁抽象句、禁文字概念、画风适配转译、人物锁进画风、跨页角色一致禁指代），直接决定出图质量。 |
| 可维护性 | 良 | 脚本模块化清晰（run.mjs 统一 CLI，server.mjs 客户端库，各功能独立脚本）。代码注释充分，解释"为什么"而非仅"做什么"。有"踩坑经验"章节。package-lock.json 含在包内（98.7KB），确保依赖版本一致但增加包体积。 |

---

## 五、不在审查范围（仓库管理员入库时处理）

- `expert_center.json` 中已有条目 `id=VibeknowHanddraw`（updatedAt=2026-07-22T09:39:10Z），上架时由 expert-publisher 自动刷新 updatedAt
- `.codebuddy-plugin/marketplace.json` 条目追加/更新（由 expert-publisher 自动处理）
- `avatars/` 根目录头像复制为 `VibeknowHanddraw.png`（由 expert-publisher 自动处理）

---

## 六、修复优先级表

| 优先级 | 编号 | 问题 | 工作量 |
|--------|------|------|--------|
| 低 | S01 | SKILL.md macOS 路径示例通用化 | 小（改 1 行） |
| 低 | S02 | README 移除/注明不存在的脚本引用 | 小（改 2-3 行） |
| 低 | S03 | README 补充 Windows 平台说明 | 小（加 1 段） |
| 低 | S04 | displayDescription.zh 字数微调 | 小（改 1 字段） |
| 低 | S05 | `mcp/` 目录重命名（可选） | 中（改 import 路径） |

> 所有 SUGGESTION 均不阻断上架，可由作者在后续版本迭代中优化。

---

## 七、亮点

1. **工程化程度极高**：从分镜到成片的全流程脚本化，每个环节都有对应的 CLI 工具（`build-gen-prompt.mjs`、`check-images.mjs`、`handdraw-page.mjs`、`build-manifest.mjs`、`render-reel.mjs`），LLM 只需按 SOP 调用脚本，不参与数据拼装。
2. **防错设计出色**：同号配对铁律（NN.png/NN.vec.json/NN.mp3）、串行出图防覆盖、出图尺寸预检（掏钱前拦截）、空绘制数据防御（不写空 vec.json）、渲染原子改名（成片.mp4 出现即完整）——每一层都有结构性的防错保障。
3. **积分/降级 SOP 严谨**：积分不足时结构化报错（`{"error":"insufficient_credits","service":"handdraw"}`），Agent prompt 明确禁止自由发挥（不重试、不静默换方式、不编造产物），降级需二次确认。
4. **零外部依赖设计**：`mcp/` 客户端库仅用 Node 内置 `fetch`/`FormData`/`fs`，无需 `npm install`；渲染依赖通过 `run.mjs init` 按需拉取（chrome 走国内镜像 npmmirror + 官方兜底）。
5. **visual-rules.md 专业性强**：画面描述铁律（禁抽象句、禁文字概念、画风适配转译、人物锁进画风、跨页角色一致禁指代）直接决定手绘出图质量，体现了深厚的领域经验。
