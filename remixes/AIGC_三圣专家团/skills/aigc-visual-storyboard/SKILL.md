---
name: aigc-visual-storyboard
description: 把剧本节拍或视觉事件拆成低成本可生成分镜，维护角色、场景、道具与关键帧一致性；输出模型无关镜头表。
---

# 视觉资产与分镜

使用当前会话与项目文件。此技能自身不调用图像服务、外部 API 或其他技能，生成任务交给用户已有 ComfyUI。

## 输入与资产

读取 brief、已有 script、角色/场景资产、continuity 与用户已锁定参考。纯视觉短片可只用 brief 和最小事件单；不要强求完整小说或季大纲。任何新增故事含义都回写为建议，不私改原台词。

JSON 共用 schema_version="1.0"、project_id、revision、mode，与其他三圣技能格式一致。

cast.json：characters[]，每项 id/name、appearance_anchors、body_proportions、wardrobe_variants、voice_notes、reference_files、reference_revision、status。分开永久身份与当前姿态；角色母图未产出写 planned，参考图路径必须真实。

art.json：locations[]（id/name/spatial_anchors/layout/lighting_variants/reference_files/status）；props[]（id/name/scale/material/owner/state_variants/reference_files/status）。空间锚点 3–5 个，要能逐项核对；日夜变体保留门窗、家具位置与比例。叙事道具才建独立卡。

## 镜头结构

storyboard.json：episodes[]，每集 id/target_seconds/segments[]；每段 id/scene_id/shots[]；每镜 id、beat_ids、seconds、purpose、character_ids、location_id、prop_ids、asset_revision、shot_size、camera_position、axis、camera_motion、start_state、action、end_state、frame_brief、sound、transition、reference_files、generation_risk。

一个 beat 只能被一个镜头完整认领，镜头按剧情顺序，不跨场；若长对白必须切分，先把原台词保留原文拆成带 parent_beat_id 的连续子拍，再分配镜头，不能重复算整句或漏字。无剧本短片也给事件拍稳定 ID。

生成段与剪辑镜头分开。默认一段一个镜头，多个镜头只有已验证工作流支持才合成一段；单段时长和帧数使用实际模型限制，未探明时标待适配，不能把 15 秒当通用上限。输出时长合计与目标差异，对白时长装不下先延长或拆拍。

## 画面方法

先建立空间，再按信息/情绪变化切镜。每镜只承担一个主要可观察动作，交代动作前后状态。轴线、左右站位、视线、移动方向和道具持有保持连续；换轴用中性镜头或可理解的过渡。

多人交互优先拆为双人关系镜头、单人反应或物件插入；手指细活、复杂碰撞、快速变形给低成本替代方案。关键情绪可静镜，不强加移动。转场服务时间/空间变化，少用无目的花哨效果。

参考图分角色母版、场景母版、该镜关键帧。关键帧一张一镜，审阅拼版不能直接当视频起始帧；保持实际画幅和目标构图。画面文字需要单独排字区域与准确文本，避免把乱码带进后续镜头。

## 输出和验收

交付 cast.json/art.json/storyboard.json 与 Markdown 镜头表，表含镜号、秒数、景别、动作、声音、关键帧说明、引用资产与生成风险。未出图不计为资产完成。

检查节拍覆盖恰好一次且顺序正确、资产引用存在、版本相符、同场轴线一致、对白与镜头时长匹配、总时长合理、关键剧情动作可见。生成后核验脸部/服装/手/家具空间/道具状态；只重做失败镜头。上游变更时标失效镜号和原因。

交给提示词专家的是镜头与锁定条件，不是泛泛美学形容词。无委派工具时保存 handoff.json，由当前会话继续执行或交给用户选择下一位。
