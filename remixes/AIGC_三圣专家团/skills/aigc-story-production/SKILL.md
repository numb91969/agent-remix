---
name: aigc-story-production
description: 为个人与企业自媒体编写连载或单集小剧场，管理简报、大纲、人物声线、剧本和跨集连续性；纯视觉短片只做最小事件单。
---

# 故事与制作统筹

这是自包含的纯文本制作技能。使用当前会话和项目文件；无外部账号、API、安装命令或其他 skill 前置条件。

## 模式与粒度

- 连载：先形成栏目承诺和试播季大纲，人物与场景资产贯穿各集。默认建议 6×60 秒、先完成首集，用户明确数量优先。
- 小剧场：单集目标—阻力—选择—结果，默认 30–60 秒、2 位主角、1 主场景；允许开放余味，不强加下一集悬念。
- 短片：无完整戏剧冲突时只记录主体、事件、情绪与结尾画面，直接交提示词阶段。可省 outline 和正式 script。

默认值写为 assumption 并直接做草案。已有信息不重问，重大未定方向集中问一次；用户已授权全流程时按约定范围推进，不把每个文件变成审批节点。

## 项目契约

写到用户项目中的 `aigc/<project_id>/`，用相对路径。所有 JSON 顶层有 schema_version="1.0"、project_id、revision（整数）、mode（serial/theater/clip）。这些是本技能独立格式，不宣称兼容原 novel-* 校验器。

brief.json：title、audience、purpose、platform、aspect_ratio、target_seconds、episode_count、tone、constraints、assumptions、available_assets、production_budget（镜头数/生成次数/可用时间；没有实际报价不写价格）。

outline.json（需要时）：premise、world_rules、characters（id/name/want/obstacle/choice/arc/voice）、locations（id/name/reuse_plan）、episodes（id/synopsis/hook/payoff/next_question/character_ids/location_ids）、foreshadowing（id/setup_episode/payoff_episode/status）。完结集 next_question 可空。

script.json：episodes 数组，每集 id、target_seconds、scenes 数组；每场 id、location_id、character_ids、lighting、prop_ids、beats 数组；每拍 id、kind（action/dialogue）、text、speaker（对白必填，可 VO）、delivery、seconds_estimate。动作与对白是独立条目，不写镜号或模型参数。

continuity.json：facts、relationships、wardrobe_states、prop_states、unresolved_promises、latest_episode、changes（revision/reason/affected_ids）。记录事实来自哪一集/哪个文件，修订不默默覆盖既有设定。

交接文件 handoff.json：project_id、revision、from_role、to_role、input_files、locked_decisions、open_questions、required_outputs、invalidated_ids。没有真实委派工具时交接文件就是协作依据。

## 写作方法

一句话先明确谁为了什么遇到何种阻力。每场至少改变信息、关系或行动方向之一；无变化的场删除或合并。角色台词先看戏剧功能，再看个人声线，最后压缩；避免借角色之口解释双方早已知道的事。用可观察行动代替抽象心理。

对改编材料记录实际引文/章节，没读到的内容标未读；原创则标原创设定。长材料分段读取，不能假装读完。人名、别名和资产 ID 建表去重。

先按台词约 4 字/秒做草估，再加不与对白并行的动作时间；节拍并行要写明，不双算。单句尽量一口气，必要时分句，不以机械字数破坏人物语气。拿到音频再按真实时长校准。

制作约束优先反馈到剧本：减少只出现一次的角色和场景；复杂动作可用结果镜头、反应镜头或声音桥讲清。增加镜头/场景意味着算力与连续性检查成本，不能说几乎免费。品牌功能服务人物目标，不制造无依据的商品功效。

## 检查与更新

交付前检查角色/场景引用有效、每场动作与对白可区分、每集时长估计与目标差异是否超过 15%、开头是否呈现事件、结尾是否完成约定回收、跨集时间/道具/关系是否冲突。15% 为工作阈值，可按明确需求调整，估时不冒充实际片长。

用户改单个角色时，列出受影响的集、场、镜头和生成任务；只更新关联数据。每次交付附 Markdown 剧本、变更摘要与下一步可执行输入。无文件工具则直接提供完整 JSON/正文，并注明未落盘。
