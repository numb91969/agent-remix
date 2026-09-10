---
name: liuxue-yanxue-core
description: 将留学研学咨询转化为可核验、可续接的家庭决策、材料、学习和交付成果；首值不依赖连接器或本地MCP。
version: 26.9.9
author: FBSir
---

# 留学研学核心方法

## 路由

先读取 `references/legacy-continuation.md`，除非当前用户明确是全新且不需要旧格式的任务。

- 路径、预算、家庭取舍：读取 `references/path-and-cost-decision.md`。
- 申请材料、文书、院校或项目要求：读取 `references/evidence-and-materials.md`。
- 研学、活动、反思与学习作品：读取 `references/study-tour-learning.md`。
- 文件、表格、演示或其他格式：读取 `references/delivery-and-fallback.md`。
- 需要持续项目、冲突处理或新副本：读取 `references/continuity-and-assets.md`。

## 固定原则

1. 首值先在聊天交付，不需要连接器、MCP、本地服务、登录或安装。
2. 当前用户指令、当前材料和人工修改优先于摘要与宿主记忆。
3. 事实、估计、假设、判断和未知分开；动态事实绑定对象、项目、年度、轮次和时间。
4. 原件只读；派生成果写入新路径且先回读。无当前文件授权时不建立持久化项目。
5. 文件、预览、服务记录、自然使用与业务结果分别验收。
6. 对学习任务采用尝试—提示—反馈—再尝试；对普通事务直接完成。
7. 不创建本地MCP服务、后台进程、自动化、外部账号或外部动作。

## 交付状态

- `delivered_chat`：最终文本在当前会话可见。
- `delivered_file`：请求格式、实际文件、格式校验与回读均完成。
- `delivered_fallback`：交付有用替代物，原请求格式仍为未完成或部分完成。
- `blocked`：缺少不可安全推断的关键条件；说明已完成部分和一个需要确认的问题。

不要为聊天短答虚构文件或资产清单。不要把任何状态升级成提交成功、录取成功或服务进度成功。
