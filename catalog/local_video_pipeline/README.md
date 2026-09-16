# 本地 / ComfyUI 视频生产候选集

这是从完整专家归档中筛出的本地优先候选集，面向“自有云电脑 + 本地 ComfyUI + 本地渲染”的短剧、剧本、分镜和视频生产流程。

## 筛选规则

- 排除必须调用 LibTV、ListenHub、ChatCut、WorkBuddy 内置生成模型或其他第三方生成/分析 API 的完整 agent/skill。
- 排除必须配置第三方 API key、付费连接器、私有 MCP 或固定云端账号的完整 agent/skill。
- 保留纯提示词、剧本结构、分镜规划、Remotion/HyperFrames/FFmpeg 本地编排，以及可以把生成环节替换为 ComfyUI 的流程。
- `qiaomu-cut` 和 `qiankun-video-shift` 只允许使用本地素材/本地生成结果的受限模式；不启用 ListenHub、外部素材搜索或远程生成器。
- 原始 446/1004 全量目录不删除，只是不进入本地优先候选集，便于追溯来源。

## 目录

- `agents.csv`：保留的 agent 和可独立复用的成员 prompt。
- `skills.csv`：保留的技能以及本地替代方式。
- `excluded.csv`：从本地候选集中剔除的外部依赖项和原因。

## 推荐链路

`novel-outline → novel-characters + novel-art → novel-script → novel-storyboard → ComfyUI → Remotion/HyperFrames/FFmpeg`

H3 prompt 只作为提示词格式参考，不要求调用 MiniMax 云端 API。
