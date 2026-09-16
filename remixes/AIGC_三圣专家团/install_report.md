# AIGC 三圣专家团｜安装与 Remix 报告

安装日期：2026-09-12。三位均已通过 Chrome 的 WorkBuddy 企业 Agent 页面发布 v1，企业全员可见。发布后逐一重新打开配置，核验头像、提示词字符数与全员可见设置。

| 专家 | 职责 | Agent ID | 提示词字符数 |
| --- | --- | --- | --- |
| 剧本 关汉卿（曲圣） | 故事、连载、小剧场、制作统筹与团队总入口 | agent_01M2AD04TQD74RPDS5C209VHCK | 7788 |
| 分镜 吴道子（画圣） | 人物/场景/道具资产、镜头叙事与连续性 | agent_01M2ADVNAXFNBYBHKY5YQS0760 | 2936 |
| 提示词 李白（诗仙·谪仙人） | 图像/视频提示词、自有 ComfyUI 适配与交付 | agent_01M2AE4B6XDKS29R9XH7VXBDMZ | 4051 |

## 三种产品模式

- 连载：默认建议 6×60 秒试播季，先首集；维护人物、场景、道具和跨集伏笔。用户明确规模优先。
- 小剧场：默认 30–60 秒、2 主角、1 主场景；保留单集冲突与回收，不强加季大纲。
- 短片：想法→最小镜头单→提示词→生成/剪辑；没有戏剧冲突时不强迫写完整故事。

采用三位互补专家而非按产品复制三套工作流。关汉卿内嵌完整流程，在平台没有真实委派工具时能继续分阶段工作，不谎称已调用其他专家。

## 参与 Remix 的 6 个数据库 Agent

检索基线为本地合并库 1004 条记录：WorkBuddy 446、AGENCY-AGENTS 英文 280、中文 278。最终阅读并吸收：

1. WorkBuddy AiVideoScript：剧本、镜头描述、画面提示词与配音字幕分层；用于三位专家。
2. WorkBuddy NarrativeDesigner：人物声线、世界规则、叙事承诺与回收；用于关汉卿。
3. WorkBuddy PromptEngineer：具体约束、格式、单变量迭代与版本管理；用于李白。
4. AGENCY-AGENTS academic-narratologist：欲望/需要、伏笔、叙事时间与节奏；用于关汉卿。
5. AGENCY-AGENTS design-visual-storyteller：视觉情绪弧线、一致性、镜头节奏；用于吴道子。
6. AGENCY-AGENTS project-management-studio-producer：范围控制、资源预算、优先级与风险；用于关汉卿。

来源路径、commit、SHA256、保留/删除项见 provenance.json。未把中文对应版本重复计为额外来源。

## 技能来源与实际安装方式

7 项技能方法被改写为 3 项自包含纯文本技能：

- aigc-story-production：来自 novel-outline、novel-script、novel-writing，包含大纲、人物声线、节拍剧本、估时、跨集状态与制作预算。
- aigc-visual-storyboard：来自 novel-characters、novel-art、novel-storyboard，包含角色母版、空间锚点、道具状态、节拍覆盖与镜头连续性。
- aigc-comfyui-delivery：来自 prompt-engineer 的提示词迭代方法，并新写自有 ComfyUI 环境核验、任务清单、失败恢复和本地交付规范。

线上采用“直接内嵌系统提示词”，不是平台注册的独立 skill 绑定；本地另有 agents/、skills/ 和每位的 ZIP。关汉卿内嵌全部 3 项，吴道子内嵌视觉分镜，李白内嵌提示词与交付。没有运行时软链、原始脚本前置依赖，也没有绑定第三方连接器/MCP。

排除：LibTV/Liblib、ListenHub、ChatCut、付费生成/素材服务、私有 MCP、.NET、原 Remotion/HyperFrames 运行包、供应商强绑定提示词包。anti-distill 实际为知识脱敏而非父 Agent 所称的“去 AI 味”，因此没有采用。删除禁止承认 AI/Agent 的角色伪装条款，保留专业对话身份。

## 头像

三张写实摄影头像均已上传并随 v1 发布；与 CFO 赵公明保持传统人物＋现代工作室风格。

- 关汉卿：绛红文士袍、马甲、墨镜、剧本与手机；JPG 152689 字节。
- 吴道子：水墨长袍、现代西装、数位板与手写笔；JPG 160916 字节。
- 李白：白衣儒巾、浅色西装、手机与酒葫芦；JPG 146656 字节。

上传版均为 768×768，小于页面 512KB 限制；PNG 原图及生成提示词保存在 avatars/。头像由本次内置图像工具生成，图像生成服务并未成为三位专家的运行依赖。

## 验证和边界

已验证：网页发布返回列表、三位均有 v1 与 Agent ID；重新打开后头像正确、全员可见、提示词字符数与本地文件一致。没有执行真实 GPU 视频试跑，不将规范检查冒充生成验收。

企业 Agent 使用独立云端沙箱，localhost 不等于用户电脑。只有当前环境可达、已授权的自有 ComfyUI 才能直接运行；否则提供便携工程包交本地助理执行。不会新开公网隧道、下载模型/节点、购置云算力或调用第三方付费 API。WorkBuddy 本身模型用量和用户自有算力仍有成本，并非“所有运行免费”。

入口：WorkBuddy 客户端“助理→企业智能体”。从故事开始找关汉卿；已有剧本找吴道子；已有镜头/视觉想法找李白。
