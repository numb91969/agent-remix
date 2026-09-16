---
name: aigc-comfyui-delivery
description: 将想法或镜头表转为生成提示词与工作流映射，只使用用户已有自有 ComfyUI 和免费本地剪辑环境完成生成、恢复与交付。
---

# 提示词与自有 ComfyUI 交付

此包无第三方生成 SDK、API key、付费服务或其他 skill 前置条件。文字工作使用当前会话；视频运行环境仅限用户已有的本地/自有云电脑 ComfyUI 和已安装模型。不能自动下载模型、节点、软件或购买云算力。

## 从实际环境开始

优先使用用户给出的 ComfyUI 页面或已有工作流 JSON。用已有浏览器/文件工具核对节点、模型、输入字段、帧数和分辨率要求；没看到的名称不能猜。可使用用户已指定、自主管理的 ComfyUI 本地接口，但不得转接第三方托管生成服务或代理。自有环境支持身份认证时使用现有正常登录，凭据不进产物。

审计实际 workflow：逐个核查自定义节点是否调用外部网络、付费推理、上传素材、自动下载权重。仅有节点名字不足以判定；读节点实现或已有离线审计记录，无法验证的节点不能投产。只有经过审计且已安装的模型/节点进入执行配置。

WorkBuddy 企业 Agent 可能在云端独立沙箱运行。沙箱的 localhost 不是用户电脑；不得宣称能够直接访问用户本机文件、浏览器或 GPU。只有已存在、已授权且从当前运行环境可达的自有 ComfyUI 才能直接执行。否则交付便携工程包供用户本地 WorkBuddy 助理执行；不新建公网隧道、不开放端口、不额外接入付费服务。

runtime-profile.json 记录 endpoint_owner="user"、workflow_file、workflow_sha256、model_files、node_classes、prompt_node_mapping、reference_node_mapping、duration/frame_constraints、audio_support、verification_status。未发现环境时 verification_status="missing"，仍交完整 prompts 和待映射任务，不编造可运行工作流。

## 提示词与模型适配

先写通用版：主体与参考资产 → 空间与初始状态 → 动作及结束状态 → 构图/运镜 → 光线与材质 → 保持条件。图像写一刻，视频写时间变化。具体名词优先，不堆机型、强制皮肤瑕疵或镜头呼吸。

prompts.json 顶层 schema_version="1.0"、project_id、revision、mode、shots[]；每镜 id、asset_revision、image_prompt、video_prompt、negative_prompt（不支持时 null）、reference_files、duration_seconds、workflow_mapping、adaptation_notes。普通语言和专用语法分开；只有模型支持才写多图序号、首尾帧、<d> 或多镜标签。没有音频功能就不给原生音效承诺。

单镜短片直接由 brief 生成；多镜只补需要的镜头表；连载严格沿用角色/空间母版。负面词针对实际失败原因，不能承诺完全防止缺陷。种子用于复现，不是身份锁。

## 生成、恢复与资源控制

载入用户已有工作流，将已验证的字段映射到实际节点；保留其他设置的来源。先做关键镜头短样，使用工作流支持的较低分辨率/帧数，不凭空降低到无效参数。记录样片结果后按用户授权范围继续。每镜最多 2 次纠错重试；连续同因失败就修改镜头方案或标 blocked。不得自动扩机器、购服务、下载模型或清空共享队列。

generation-manifest.json：schema_version、project_id、revision、mode、jobs[]；每项 shot_id、attempt、workflow_sha256、model_versions、seed、params、input_hashes、prompt_id、status、elapsed_seconds、output_files、failure_reason、review。

状态单向记录：planned → queued → rendered → reviewed → delivered，失败为 failed/blocked。提交超时后先查本任务历史与队列，不能盲目再提交；只处理自己的 prompt_id。文件确实存在、可读且类型正确才算 rendered，完成视觉审阅才算 reviewed。任何已生成状态都需工具证据。

## 音频和本地剪辑

仅使用用户自有录音/音乐、已有离线语音模型、或已验证支持音频的 ComfyUI 工作流。无音源时输出台词和字幕草案及静音版本说明，不悄悄请求云 TTS。静音视频不能标“音画同步已通过”。

timeline.json：project_id、revision、fps、width、height、clips[]（shot_id/file/in_seconds/out_seconds/start_seconds）、audio_tracks、subtitles、export_file。素材按工作流实际秒数修订时间线，生成帧率与播放帧率不同会影响片长，不能仅改元数据伪装。

使用已装 FFmpeg 或免费本地编辑器：先检查可执行文件/编码器和素材，统一尺寸/帧率/像素格式后拼接；字幕与品牌文字后期叠加。命令用参数数组或严格引用文件名，禁止拼接未经转义的用户文字。输出新文件，保留原始素材。没有编辑环境则交 clips 与 timeline，标待合成，不安装新依赖。

## 最终检查

实际播放全片检查黑帧/冻结/穿帮/角色与空间连续性，核对真实分辨率/帧率/片长/音轨和字幕时间。程序只能检查技术指标；未视觉查看就写 visual_review="pending"。对失败给到具体镜号与修复动作。

交付 final.mp4（真实存在才列）、prompts、workflow 副本与 hash、manifest、timeline、引用素材清单、失败记录、字幕。不得把静图幻灯片冒充动态视频，不承诺商业生成成功率或报价。生成不等于发布社交平台，未经请求只交文件。
