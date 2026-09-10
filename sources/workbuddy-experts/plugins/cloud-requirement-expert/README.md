# 云产品需求专家（Requirement Assistant）

基于 `requirement-assistant` MCP Server 的云产品需求专家，支持从一句话想法到正式建单的完整需求管理流程。

## 类型

Agent 型（单个 AI 专家）

> ⚠️ 本工具仅适用于腾讯内网环境（依赖 TAPD + 太湖 OAuth）

## 功能

1. **新建需求**：根据一句话想法、会议纪要、聊天记录或草稿生成正式 TAPD 需求，先预览再建单
2. **补全已有需求**：对已有 TAPD 需求结构化补全（背景、目标、范围、验收标准、风险、竞品等），先预览再写回
3. **生成 AI 读层**：为已有 PRD 生成结构化摘要，供下游 AI 系统消费
4. **更新已有需求**：修改已创建需求的标题、描述、状态、优先级等字段，支持插入本地图片
5. **需求拆分**：按业务流程/功能模块/架构维度拆分子需求，INVEST 质量门禁检验

## 前置条件

使用前需在 WorkBuddy 中配置 `requirement-assistant` MCP Server：

1. 打开 WorkBuddy 左上角 **⚙️ 设置 → 连接器**
2. 添加 `requirement-assistant` MCP Server（远程 `streamable-http` 类型）
3. 配置请求头：
   - `Authorization: Bearer <mcp_server_auth_token>`
   - `X-Tapd-Access-Token: <tapd_personal_access_token>`

详细配置模板见 `skills/requirement-assistant/references/remote-mcp-setup.md`。

## 运行时依赖

- Python 3.8+
- `pip install requests`（本地图片上传功能需要）
- **TAPD Token**：详见 [Token 配置指南](skills/requirement-assistant/references/token-setup-guide.md)（支持环境变量 `TAPD_ACCESS_TOKEN` 或连接器 Header `X-Tapd-Access-Token`）

## 使用示例

- "帮我基于这个内容生成一个 TSF 的 TAPD 需求"
- "补全需求 1234567890 的背景、验收标准和竞品分析"
- "把这个需求的 PRD 生成一个 AI 读层"
- "把需求 1234567890 的优先级改为高，负责人改成张三"
- "这个需求太大了，帮我按功能模块拆分成子需求"

## 头像

头像已自动生成在 `avatars/` 目录下。如需替换为自定义头像，要求：
- 格式：PNG（推荐）或 JPG
- 尺寸：512×512 px
- 大小：单张不超过 500KB


