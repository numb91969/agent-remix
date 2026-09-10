# 请求操作合同

所有请求均为 `schemaVersion=mibao.request.v1`、`operation`、`input` 三字段。未列出的字段或操作被拒绝。路径必须绝对；以下项目简称 project。

| operation | 必填 input | 可选 input |
|---|---|---|
| doctor | 无 | 无 |
| create | project | name |
| add_source | project, source | 无 |
| scan | project, sourceId | resume, maxFiles(1–1000000), maxSeconds(0–3600], fullHash(bool), allowEmpty(bool), exclude(字符串数组) |
| status | project | 无 |
| list | project | limit(1–2000), offset, sourceId, assetId |
| search | project, query | limit(1–100), offset, sourceId, kind, dateFrom, dateTo, minBytes, maxBytes, minDuration, maxDuration |
| duplicates | project | limit(1–1000) |
| annotate | project, assetId, field, value | supersedes |
| subtitles | project, assetId, path | encoding |
| collection | project, name, assets | collectionId |
| link | project, leftId, rightId, kind, evidence | 无 |
| source_policy | project, sourceId, enabled(bool) | 无 |
| relocate | project, sourceId, source, confirmed=true | 无 |
| cancel | project, jobId | 无 |
| export | project, output | 无 |
| restore | path, project | 无 |
| recover | project | 无 |
| report | project, output | limit(1–2000), query |
| legacy_view | path | 无 |
| legacy_search | path, query | limit(1–100) |
| accept_move | project, oldLocationId, newLocationId, confirmed=true | 无 |
| xmp_export | project, assetId, output | 无 |
| xmp_import | project, assetId, path | confirmed(bool，默认仅预览) |
| media_probe | project, assetId | 无 |
| convert | source, output, profile | 无 |
| migrate | path, project, confirmed=true | 无 |
| analysis_prepare | project, assetId, task, output, disclosureConfirmed=true | 无 |
| analysis_import | project, path | 无 |

annotation.field: tag/caption/rating/favorite/person/date/correction。value 是文本。人工修订保留历史；相同内容的不同副本共享内容标注，但各自的位置与来源政策独立。

关系 kind: raw-jpeg/live-photo/subtitle/derivative/version/near-candidate。同名只能作为候选线索，不自动判定同源或删除文件。evidence 写明用户确认或可核对的依据。

analysis.task: ocr/transcribe/describe。prepare 只生成等待实际执行的任务。import 需要 jobId、assetId、inputSha256、真实 model/producerVersion/observedAt、evidenceRefs 和 segments。每段含 text/startMs/endMs/confidence；不能确认的画面不编造，转写必须有合法时间码。模型结果仍标为 unreviewed。

示例 scan：

```json
{"schemaVersion":"mibao.request.v1","operation":"scan","input":{"project":"<project>","sourceId":"<add_source返回的ID>","maxFiles":1000,"maxSeconds":60}}
```

扫描受文件数/时间预算约束。paused 后传回同一 jobId；相同请求文件本身不可被编辑重用。completed 与 coverage 需同时读取，partial/needs_review 不等于完整枚举。

旧版转换入口仍为 `bin/mibao.py convert <source> <output> --profile video-access|audio|image|remux`；由宿主以参数向量调用，源文件只读，输出必须新建。缺失 FFmpeg 则仅阻断转换。

日期过滤为带时区的文件修改时间半开区间，不冒充拍摄时间；时长过滤只覆盖media_probe已测得的durationSeconds。未知时长不满足时长过滤。

restore/migrate发布中断时，用recover只完成已有、哈希绑定的新项目发布；缺少prepared回执时保留staging，不猜测或覆盖。搜索每项最多展示50个位置，副本组最多1000个位置；使用list的assetId和offset继续分页。
