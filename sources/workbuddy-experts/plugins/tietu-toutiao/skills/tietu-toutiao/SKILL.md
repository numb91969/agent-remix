---
name: tietu-toutiao-layout
description: This skill should be used when one or many newspaper pages need a traceable edition plan, a validated content-state.v1/v2 render, deterministic mobile cover layouts, accurate Chinese text rendering, bounded revisions, or versioned rollback.
agent_created: true
---

# 贴图头条：确定性头图排版

## 目的

R3 主流程为“微信贴图作品”，同时保留以下旧单图排版。先读包根 `references/wechat-post-workflow.md`：post_materials 显式摄入、post_state 作品状态与局部修改、post_render 图组/配文/预览/ZIP、post_bridge 旧资产旁侧接续。原默认的单报纸三方案请求仍走旧单图，不强制创建图组。

完整作品入口（本节命令从当前 Skill 目录执行）：

```bash
python scripts/post_materials.py --project <project-root> --input <明确提供的PDF或图片> --batch-id issue1
python scripts/post_state.py --project <project-root> create --input post-plan.json
python scripts/post_state.py --project <project-root> show --post-id post1
python scripts/post_state.py --project <project-root> patch --post-id post1 --input post-patch.json
python scripts/post_state.py --project <project-root> render --post-id post1 --out deliverables/post1-draft
python scripts/post_state.py --project <project-root> render --post-id post1 --out deliverables/post1-final --final
python scripts/post_bridge.py --project <project-root> --post-id imported from-cover --state old-state.json --cover old-cover.png
```

新计划例见包根 `references/wechat-post-workflow.md`，平台硬限制未知字段保持 null。show 只读，不主动重扫原始目录；firstValue 不依赖连接器。final 要求作品和每一张卡片的有效确认，修改只失效相应确认。输出目录已存在时使用新 revision 目录，不覆盖成品。

将多模态模型输出的报纸内容状态转换为可审计的固定模板头图。多版任务先由 `edition-state.v1` 保存来源、候选、关系和编辑方向，再投影到旧版兼容的 `content-state`。多模态模型只负责理解和建议；本 Skill 负责校验、版式、中文文字、等比裁切、保存和回退。

## 触发条件

在以下情况加载本 Skill：

- 已上传 JPG、JPEG 或 PNG 报纸版面，需要生成三种头图方案；
- 已有 `content-state.v1`，需要渲染或修改当前版本；
- 用户要求保留原标题、只调整日期、突出某张图片、减少装饰或返回上一版。

## 固定流程

1. 多版综合先建立 `edition-state.v1`：每篇候选都有源文件/页/摘录，关联或冲突均有类型，三个编辑方向只在材料支持时出现。旧项目先用 `scripts/continuity.py` 只读检查，不能原地迁移。
2. 将已裁决的方向投影为 `content-state.v2`，保留原文、来源、坐标、置信度和确认状态。
3. 运行 `scripts/validate_content_state.py`；v1/v2 的关键字段确认、低置信和裁切边界检查在出图前统一执行；v2 另要求版面确认及自审全部通过。缺少来源或待确认时保留工作状态，不生成可交付 PNG。
4. 对 `authoritative`、`visual`、`digest`、`synthesis` 模板按需渲染。
5. `render_cover.py` 使用明确中文字体；先按 `primary_photo.path` 的原图像素执行 `primary_photo.crop`，再等比缩放及按 `focal_point` 取窗。焦点相对于 crop 区域；不能丢弃 crop 改用整版图。标题自动换行或缩小。
6. 在用户确认或生成修订后，用 `scripts/version_manager.py save` 保存 `state.json`、`layout.json` 和 `cover.png`。
7. 自然语言修改先转换为 `edition_state.py patch` 或 `apply_patch.py` 接受的结构化 patch；锁定字段不得被修改，错误补丁不写入。
8. 用户要求回退时，同时恢复内容状态、布局和图片，不只恢复图片文件。

## 四种模板

- `authoritative`：保留报头、原标题、日期和核心图片，突出正式媒体感。
- `visual`：放大核心图片和标题，减少次要信息，适合手机信息流。
- `digest`：以“今日关注”或同类标签组织一个主标题和少量辅助信息。
- `synthesis`：综合报道型，包含主标题、核心图片及精选条目，适合多版主题综合。

模板文件是唯一版式真相源，位于 `templates/`；版式引擎不得再复制一套坐标硬编码。

状态契约定义位于专家包根目录的 `../../references/content-state.v1.schema.json`、`content-state.v2.schema.json` 和 `edition-state.v1.schema.json`；运行时由 `scripts/validate_content_state.py` 与 `scripts/edition_state.py` 执行关键门禁。

## 命令

以下命令在 `skills/tietu-toutiao/` 目录执行。安装依赖：

```bash
python -m pip install -r ../../requirements.txt
```

校验状态：

```bash
python scripts/validate_content_state.py --input content-state.json
python scripts/edition_state.py validate --project <project-root> --input .tietu/editions/<edition>/state.json
```

生成版式并渲染：

```bash
python scripts/layout_engine.py --state content-state.json --type authoritative --output layout.json
python scripts/render_cover.py --input layout.json --output cover_authoritative.png
```

应用结构化修改：

```bash
python scripts/apply_patch.py --input content-state.json --patch revision.patch.json --output next-state.json
python scripts/edition_state.py patch --project <project-root> --input .tietu/editions/<edition>/state.json --patch plan.patch.json --output .tietu/editions/<edition>/state-r2.json
```


整期 patch 请求示例（plan.patch.json），每次一个操作，字段均位于顶层：

```json
{
  "base_revision_id": "e1",
  "plan_id": "roundup",
  "operation": "set_digest",
  "candidate_id": "story-3",
  "revision_id": "e2"
}
```

这里的版本、plan_id 和 candidate_id 必须替换为当前 state 里的真实值；set_digest 只能用于已 selected 的候选。`digest` 是 plan 的可选数组，缺省视为 `[]`；patch 只在目标 plan 的新版本内补齐，不改输入文件或其他 plan。不能将 `operation` 写为对象或放进 `operations` 数组。

请求 schema 为包根目录 `references/edition-patch.v1.schema.json`。来源字段使用 `sources[].relative_path`、`sha256`、`pages`；`candidates[].source_refs` 是含 `source_id`、`page`、`quote` 的对象数组。source SHA-256 必须来自实际文件；结构符合 schema 不等于源文件、路径与跨对象引用已经验证。

保存和回退命令：

```bash
python scripts/version_manager.py save --workspace session --name v1 --state content-state.json --layout layout.json --cover cover.png
python scripts/version_manager.py revert --workspace session --name v1 --output-state session/restored-state.json --output-layout session/restored-layout.json --output-cover session/restored-cover.png
```

对当前材料执行出图前检查（开发回归不随审核包分发）：

```bash
python scripts/validate_content_state.py --input content-state.json --check-image-bounds
python scripts/build_covers.py --state content-state.json --types synthesis --out-dir covers
```

## 失败原则

- 不允许静默使用不支持中文的默认字体。
- 不允许把关键中文交给图像模型直接绘制。
- 不允许拉伸新闻图片改变人物或现场比例。
- 不允许在缺少内容状态、字体、图片或模板字段时报告“已生成可发布成品”。
- 不允许让版本名、输出路径或输入图片路径越出当前会话工作目录。
