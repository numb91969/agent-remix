# 专家包审查报告 - malaysia-finance-tax（修复版）

> 专家类型：agent
> 来源类型：external（外部提交，作者 Patrick）
> 审查日期：2026-07-14
> ⚠️ 金融类启发式已触发（categoryId=08-FinanceInvestment），已校验 §十八 合规要求
> 📌 本轮为修复版复审，重点验证上一轮 3 个 BLOCKER 的修复情况

---

## 一、总体结论

**整体结论：可上架** ✅

- 结构层 BLOCKER：0 个
- 规范层 BLOCKER：0 个（上一轮 3 个 BLOCKER 已全部修复）
- 建议改进项（SUGGESTION）：5 个
- 上一轮 BLOCKER 修复验证：3/3 已通过

---

## 二、上一轮 BLOCKER 修复验证

### ✅ B01 已修复 — 三个 Python 脚本语法错误

- **上一轮问题**：`duckdb_query.py`、`data_verifier.py`、`build_duckdb.py` 开头 `try/import duckdb` 自动安装块缩进错乱（IndentationError），无法运行
- **修复验证**：三个脚本均已修正为标准 `try/except` 结构：
  ```python
  try:
      import duckdb
  except ImportError:
      import subprocess, sys
      print("duckdb not found, auto-installing...", file=sys.stderr)
      subprocess.check_call([sys.executable, "-m", "pip", "install", "duckdb", "--quiet"])
      import duckdb
  ```
- **语法验证**：三个文件均通过 `python3 -c "import ast; ast.parse(...)"` 检查，输出 `OK`

### ✅ B02 已修复 — build_duckdb.py 硬编码 Windows 个人路径

- **上一轮问题**：`DB_PATH = r"C:\Users\lenovo\.workbuddy\..."` 硬编码个人路径
- **修复验证**：已改为基于 `__file__` 的相对路径：
  ```python
  SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
  PLUGIN_ROOT = os.path.normpath(os.path.join(SCRIPT_DIR, '..', '..'))
  DB_PATH = os.path.join(PLUGIN_ROOT, 'Databases', 'malaysia_finance_tax.duckdb')
  SKILL_DB_PATH = os.path.join(PLUGIN_ROOT, 'skills', 'malaysia-finance-tax', 'datasets', 'malaysia_finance_tax.duckdb')
  ```

### ✅ B03 已修复 — 金融类专家缺少统一免责声明

- **上一轮问题**：Agent prompt 三种输出模式均未包含 §十八 强制要求的免责声明
- **修复验证**：`agents/malaysia-finance-tax.md` 末尾新增章节：
  ```markdown
  ## ⚠️ 免责声明（必须附加到每次输出末尾）

  > 以上内容由 AI 基于公开信息整理生成，仅供参考，不构成任何投资建议或个股推荐。投资有风险，决策需谨慎。
  ```
  涵盖四要素：AI 生成 ✅ + 公开信息 ✅ + 不构成投资建议 ✅ + 不构成个股推荐 ✅

---

## 三、阻断问题（BLOCKER）

无。

---

## 四、建议改进项（SUGGESTION）

### S01 ⚠️ displayName.zh 与 profession.zh 完全重复

- **现状**：plugin.json 中 `displayName.zh = "马来西亚财税金融专家"`，`profession.zh = "马来西亚财税金融专家"`，两者完全相同。
- **规范依据**：CODEBUDDY.md §九 9.1「不与 profession 重复 — displayName 是'谁'，profession 是'做什么'，两者互补」
- **说明**：§十六规定外部提交包尊重作者命名风格，不强制花名。但 displayName 与 profession 完全重复会导致市场卡片展示信息冗余（"谁"和"做什么"一样），影响用户体验。
- **建议**：将 `profession.zh` 调整为体现职能的表述，如「马来西亚财税金融分析师」或「大马财税金融顾问」，与 displayName 形成互补。

### S02 ⚠️ 包内残留 .review-cache 目录

- **现状**：包内存在 `.review-cache/review.json`，是上一轮审查脚本生成的缓存文件，不应打包进提交包。
- **建议**：删除 `.review-cache/` 目录后再提交。

### S03 ⚠️ fetch_with_fallback.py 已移除代理池，但 CORS 网关仍存在数据外传风险

- **现状**：相比上一轮，已移除 Layer 4（硬编码免费代理池 + 动态代理抓取），改为三层降级（直连 → Google 缓存 → CORS 网关）。改进显著。
- **残留风险**：Layer 3 仍使用三个公共 CORS 网关（`api.allorigins.win`、`corsproxy.io`、`api.codetabs.com`），通过第三方网关传输 URL 参数可能泄露用户查询意图。不过风险等级较低（仅传递公开网页 URL，不涉及凭据）。
- **建议**：可在 SKILL.md 或 README 中注明 CORS 网关的使用场景和风险，让用户知情。当前不阻断。

### S04 ⚠️ 两份 DuckDB 数据库文件仍存在冗余

- **现状**：
  - `Databases/malaysia_finance_tax.duckdb`（12 MB）
  - `skills/malaysia-finance-tax/datasets/malaysia_finance_tax.duckdb`（5.4 MB）
- **说明**：`duckdb_query.py` 的 `get_db_path()` 会优先查找 skill 内的版本，找不到才回退到 `Databases/`。`build_duckdb.py` 同时写入两份。两份内容可能不完全一致（大小不同）。
- **建议**：确认两份数据库的用途差异。如无特殊需要，可考虑只保留 skill 内的版本以减小包体积（节省 12 MB）。

### S05 ⚠️ requirements.txt 已补充 pandas，依赖引导已完善

- **现状**：相比上一轮，`requirements.txt` 已从只有 `duckdb>=0.9.0` 补充为：
  ```
  duckdb>=0.9.0
  pandas>=1.5.0
  ```
  README.md 新增「安装与依赖」章节，包含 `pip install -r requirements.txt` 和可选依赖说明。
- **结论**：✅ 上一轮 S05 已修复。

---

## 五、深度质量评审

| 维度 | 评级 | 判断 |
|------|------|------|
| AI 可执行性 | 优 | 脚本语法已修复，三个核心工具可正常调用；Agent prompt 结构清晰（角色→能力→工作流→输出规范→免责声明） |
| 路由/触发清晰度 | 优 | SKILL.md「触发主题—强制读取表」覆盖 40+ 主题，「数据源定向触发矩阵」覆盖 18 类查询，路由精准 |
| 上下文效率 | 优 | 语料库优先级 6 层分明（Reference_Texts → DuckDB → CSV → API → site 搜索 → WebSearch），强制本地优先降低 token 消耗 |
| 容错降级 | 优 | fetch_with_fallback 三层降级（直连→Google缓存→CORS网关），data_verifier.py 提供反幻觉验证 |
| 角色边界 | 优 | Agent 型单专家，6 大核心能力清晰（税务/银行/外汇/审计/补贴/保险），无越界 |
| 团队编排 | N/A | Agent 型，无团队编排需求 |
| 用户体验 | 优 | 三种工作模式（查询/分析/合规审查）+ 三种输出模式（详细/简洁/语料库测试），输出模板含 emoji 和结构化引用 |
| 受众适配 | 优 | 面向在马来西亚经营或计划进入马来西亚市场的企业，问题示例贴合实际场景 |
| 可移植性 | 优 | 硬编码个人路径已修复为相对路径；无 __pycache__ 残留；脚本跨平台可用 |
| 领域准确性 | 优 | 56 份 Reference_Texts（含 20+ 份马来西亚法律全文）、33 张 DuckDB 表（28,295 行）、12 个 CSV 数据集，覆盖全链路 |
| 可维护性 | 优 | Corpus_Index.md 提供完整语料索引；脚本有 docstring；README 含安装引导和脚本说明表 |

---

## 六、修复优先级表

| 优先级 | 编号 | 问题 | 工作量 |
|--------|------|------|--------|
| P2 建议 | S01 | displayName.zh 与 profession.zh 完全重复 | 极小（改一处文案） |
| P2 建议 | S02 | 包内残留 .review-cache 目录 | 极小（删除目录） |
| P3 可选 | S03 | CORS 网关数据外传风险说明 | 小（补文档说明） |
| P3 可选 | S04 | 两份 DuckDB 冗余 | 小（确认后删除副本） |

---

## 七、亮点

1. **修复响应迅速且彻底**：上一轮 3 个 BLOCKER（脚本语法错误、硬编码路径、金融免责声明）全部精准修复，无遗漏
2. **额外改进**：同时修复了上一轮的 SUGGESTION 项——移除了 `__pycache__`、移除了代理池安全风险、补充了 `pandas` 依赖、增加了 README 安装引导章节
3. **语料库极其扎实**：56 份 Reference_Texts（~17 MB），含 Income Tax Act 1967、Companies Act 2016、FSA 2013、IFSA 2013、CMSA 2007、AMLATFPUAA 2001 等 20+ 份马来西亚法律全文
4. **结构化数据丰富**：33 张 DuckDB 表（28,295 行）+ 12 个 CSV 数据集，涵盖税率、SST、OPR、汇率、GDP、CPI、贸易、货币政策等维度
5. **反幻觉设计完善**：data_verifier.py 反幻觉防火墙 + Agent prompt 强制标注来源占比和不确定性
6. **触发矩阵覆盖全面**：40+ 主题绑定必须读取的文件和库表，AI 路由精准
7. **金融合规达标**：免责声明四要素齐全，defaultInitPrompt 无决策类措辞，数据来源披露规范
