# WorkBuddy Expert Catalog

构建时间：`2026-09-09T14:36:37+00:00`

本目录以 WorkBuddy 本机缓存的 `manifest.json` 为主数据源：446 个专家、15 个分类。源文件快照位于 `snapshots/expert_center.json`，SHA-256 为 `dc924682bf5bf700a8ea25acd34f4628c5780173a6ed76a4dc79d736f37f84ec`。

## 已生成内容

- `experts.db`：SQLite 数据库，包含专家、分类、标签、快捷提示词、技能引用、包状态和验证记录。
- `experts.csv`：全部专家清单。
- `marketing_growth.csv` / `sales_commerce.csv`：严格按营销增长、销售商务两个分类筛选，共 54 个。
- `marketing_ecommerce.csv` / `marketing_ecommerce.json`：分类或名称、简介、标签中命中电商/营销词的扩大集合，共 142 个。
- `skills.csv` / `skills.json`：技能去重清单及其引用专家。
- `exact_marketing_sales_skills.csv` / `marketing_ecommerce_skills.csv`：两个筛选范围对应的技能清单。
- `download_plan.json`：全部专家的提示词直链、专家包现签接口和后续下载范围。
- `experts.csv` / `experts.db` 中的 `prompt_status` 是公开静态提示词抓取结果；`agent_source`、`agent_available` 是本机实际可用的 agent 状态。公开地址 404 不等于专家不可获取，优先看后两列和 `package_status`。
- `skills/by-expert/`、`skills/by-skill/`：指向已下载包中技能目录的软链；尚未下载的技能只记录在数据库和清单中。
- `agents/by-expert/`：指向本地专家提示词或已下载包中 agent 文件的软链。
- `verification.json`：本地缓存、WorkBuddy 界面搜索和实际召唤落包的验证记录。

## 当前状态

- 446 个专家，15 个分类；严格的 `05-MarketingGrowth` + `07-SalesCommerce` 共 54 个，关键词扩展筛选共 142 个。
- WorkBuddy 本地已有 445 个完整包；其中 446 个 agent 提示词可直接使用或通过软链访问。
- 公开静态提示词抓取结果为 248 成功、198 个 404；另有 721 个去重技能引用，当前 929 条技能软链已落地。

## WorkBuddy 包结构

典型包根目录为 `plugins/experts/<plugin>/`，包含：

```text
.codebuddy-plugin/plugin.json
agents/<agent-name>.md
skills/<skill-name>/SKILL.md
skills/<skill-name>/references/...
avatars/...
license/...
README.md
```

## 更新目录

```bash
python3 build_catalog.py \
  --live-manifest snapshots/live_expert_center.json \
  --overlay snapshots/internalExpert.json \
  --overlay snapshots/externalExpert.json
```

提示词的公开 COS 地址由 `prompt_url` 给出；完整包对有 `market_expert_id` 的条目需要调用 WorkBuddy 的短时签名下载接口：`https://copilot.tencent.com/portal/operation-platform/market/expert/download-url`。为避免泄露授权信息，本目录不保存签名 URL 查询串。

注意：缓存清单为 446 条；公开 COS 基础清单、内部/外部覆盖清单和 operation-platform 实时列表可能有不同数量，不能简单相加。
