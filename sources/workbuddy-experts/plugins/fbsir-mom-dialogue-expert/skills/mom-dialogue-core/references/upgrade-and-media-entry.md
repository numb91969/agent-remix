# 26.9.6 旧项目与媒体入口

妈妈问答仍然从妈妈出发，整理一个家的故事。旧项目不需要换专家或重建。

## 先续接，再增强

识别到 `.mom-dialogue-project.json` 时，先执行：

```text
python scripts/mom.py inspect <project>
python scripts/mom.py resume <project>
```

两者只读，不扫描来源、不迁移、不初始化。根据返回的实际原作品、状态与下一步继续。只有用户要加入或处理新媒体时才执行 `enable-media`。核心格式继续为 2.0，新增记录放在 `14_媒体处理/`。

未知格式、旧事务未完成、字段差异必须保留原文件。不能用 `migrate_schema.py` 或 `--fix` 作为升级后首次打开的通用步骤。不能重新询问项目中已有的人物、目标与授权。

## 已接入的技术处理

```text
python scripts/mom.py enable-media <project>
python scripts/mom.py capabilities
python scripts/mom.py plan-media <project>
python scripts/mom.py inspect-media <project> --plan <returned-plan-path> --max-jobs 10 --deadline-seconds 60
python scripts/mom.py media-status <project> --plan <returned-plan-path>
```

先确保所需来源已经经过原版登记/扫描/差异复核与提交链。媒体计划不会替代来源提交。返回的计划路径必须使用实际输出，不手编 ID。

`inspect-media` 只读取真实技术属性，不代表图片观察、音频转写或完整视频理解。FFprobe 不可用时保留待处理；禁止安装外部 Skill 或下载工具。`--max-input-bytes` 约束本轮来源字节总量，默认 1 GiB；已成功解析的来源在文件和处理器未变化时复用。失败重试需要 `--retry-failed`，同任务最多三次。

任何“抽样关键帧”只能形成采样画面证据；音频与视频画面覆盖分别计算，重叠区间只计一次。未形成媒体行的来源也属于待处理分母。

## 访问副本

```text
python scripts/mom.py prepare-media <project> --source-id <existing-source-id> --profile audio_clip --start-seconds 0 --end-seconds 60
python scripts/mom.py prepare-media <project> --source-id <existing-source-id> --profile thumbnail
python scripts/mom.py prepare-media <project> --source-id <existing-source-id> --profile video_frame --start-seconds 30
```

时间范围必须取自已解析的真实时长。每段音频或视频访问副本最长五分钟，输出默认不超过 64 MiB；可使用 `video_clip` 生成可播放视频片段。源文件、已生成访问副本和人工修改都不覆盖；内容变化后重新扫描并形成新任务。失败临时文件未验收，不展示为成功作品。

访问副本通过格式、时长、字节和哈希检查，只证明技术处理。仍需宿主实际观察/转写与用户核对，才能生成有依据的故事；不能把转码成功写成“已经理解妈妈讲的内容”。

## 家人确认与交付

候选故事默认是私密、待确认且不可入稿。家人可在项目的 `14_媒体处理/inbox/` 放入明确确认文件，再运行：

```text
python scripts/mom.py confirm-story <project> --story-id <candidate-story-id> --file 14_媒体处理/inbox/<confirmation>.json
```

确认文件必须绑定候选故事当前 SHA-256，包含确认者标签、确认时间和所确认的字段。它只能将故事标为私密已确认，保留候选前像并追加版本记录；不会自动开放给家人、入稿或公开。入稿和公开仍须使用现有 `create_delivery_selection.py`、`validate_permissions.py` 和 `export_delivery_manifest.py`，并让每一适用来源/故事的权限记录通过。

家人明确授权入稿时，先把每项来源和故事的许可 JSON 放入 `14_媒体处理/inbox/`，用 `record-consent` 记录；然后执行：

```text
python scripts/mom.py authorize-story-manuscript <project> --story-id <confirmed-story-id>
```

它会检查故事和每个来源都有明确入稿许可，保存已确认故事前像，并把故事标为“可入稿但仍私密”。公开权限不由该命令授予。

## 停用与资产保全

```text
python scripts/mom.py disable-media <project>
```

停用只暂停新媒体能力，不删除扩展结果，不恢复旧快照覆盖新增稿件，不改写来源或家人确认。旧版继续修改的核心文件由下次只读检查重新读取。

面向家庭的回答只显示可读成果、实际处理范围、待确认问题和下一步；不要把命令、哈希、内部 ID 或长机器报告倾倒给用户。
