# 微信贴图作品 · R3 实际工作流

## 用户路径

交材料 → 看作品 → 说修改。媒体优先，也支持创作者。单图可以独立交付；图组由首图、后续页及独立标题/配文组成。现有四模板仍可用。

图组有 portrait（1080×1440）、square（1080×1080）和 legacy（1080×1920）三种本地版式建议；不当作微信强制比例。账号是否可发贴图、平台图数/字数/API 权限仍需当前入口核验，不预填硬限制。

## 1. 摄入与来源

仅处理用户明确给出的文件；post_materials 支持 PDF、PNG/JPG、文本。一个 PDF 的所有页都会处理；输出图片并保留完整可提取文本，扫描页没有文本时保持为空，不伪造 OCR。来源摘要、物理页号和 rendered_unreviewed 状态保存在 ingest.json。相同 batch/来源/参数且材料摘要未变时复用；改变输入要新 batch。原文件只读。

项目内 sources 使用真实文件及 SHA-256。身份和路径来自当前项目；不把模型猜测写成来源。图片坐标针对实际生成位图，不跨 DPI 沿用 crop。

需要保留已选照片完整构图时设置 photo.fit=contain，按整张 crop 区域等比放入画框，空余区域使用纸色；默认 cover 按焦点取窗。QA 的临时图片序号不等于印刷版号，以源文件摘要、原页和图片内容对应为准。

## 2. 新作品计划

以下为字段示例，需要替换为当前实际来源摘要与有效 crop。示例不代表自动分析已完成。post_state.create 默认不继承任何传入确认。

```json
{
  "post_id": "post1",
  "audience": "media",
  "profile": "portrait",
  "title": "当前作品标题",
  "caption": "独立的发布配文",
  "tags": [],
  "brand": {"name": "用户自己的媒体名", "ink": "#163755", "accent": "#db5d30", "paper": "#ffffff"},
  "sources": [{"id": "s1", "path": "materials/issue1/source-1-p001.png", "sha256": "使用实际文件的SHA-256", "label": "原报第一页"}],
  "cards": [{"id": "cover", "kind": "photo", "title": "首图标题", "text": "图片说明", "credit": "来源与日期", "source_refs": ["s1"], "photo": {"source_id": "s1", "crop": {"x": 0,"y": 0,"width": 800,"height": 600}, "focal_point": {"x": 0.5,"y": 0.5}}}],
  "order": ["cover"]
}
```

audience 为 media/creator；kind 为 photo/text/legacy。text 卡片也必须引用材料，个人观点可引用用户提供的笔记。不强制使用媒体报头，creator 可使用空或个人 brand.name。order 必须逐一列出全部 card ID，首个为封面；本地资源预算 50 张不是平台上传上限，超过时拒绝不截断。

## 3. 有界改稿

所有 patch 绑定 base_revision_id 和新的 revision_id：

```json
{"base_revision_id":"r1","revision_id":"r2","operation":"edit_card","card_id":"cover","set":{"text":"仅调整这一张的说明"}}
```

可用操作：edit_post（title/caption/tags/profile/brand）、edit_card（kind/title/text/credit/source_refs/photo）、reorder（完整 order）、add_card、remove_card、add_source、lock、unlock、confirm。修改不覆盖输入/历史；错误或父版本冲突不提交新状态。移除卡片后 order 同步变动；移除最后一张拒绝。顺序变化使整篇确认失效，但未变卡片可复用。锁定状态需要明确 unlock 后才能修改。

## 4. 确认与交付

show 返回各 scope 的当前摘要。用户核对并确认具体内容后，才将其决定记录为 confirm：

```json
{"base_revision_id":"r2","revision_id":"r3","operation":"confirm","card_id":"cover","expected_digest":"使用show返回的该卡当前digest","actor":"真实确认者或用户角色","note":"记录实际核对的来源和决定"}
```

card_id=post 确认作品标题、配文、顺序和品牌；每个 card 还需自己的确认。摘要不一致拒绝；源文件变更会阻止交付，不能复用旧来源确认。actor/note 是本地审阅记录，不代表服务端验签或外部发布授权。

draft 有明显草案标记，final 需全部有效确认。每个输出目录是不可覆盖的交付快照，包含有序 PNG、独立标题/配文/话题、来源说明、内嵌图片的离线 review.html、manifest.json、wechat-post.zip 与 publish-handoff.json。预览支持翻页、160px 缩略检查、单图获取、配文复制和版本绑定的改稿意见。浏览器禁止剪贴板时提供手动选择复制。未变卡片由摘要和字体/渲染器版本绑定的缓存复用，更新一页不全量重画。

publish-handoff 是人工上传衔接清单，不执行微信 API。uploaded/published 固定 false；草稿箱接口是独立可选连接，当前未验证账号授权时不得宣称已上传。也不承诺流量、推荐或收益。

## 5. 旧项目与恢复

post_bridge.from-cover 只读旧 state 与已生成图片，新建旁侧 post。kind=legacy 的 final 导出保留旧图片原始字节；要换比例请显式转为 photo 卡重新排版，不能静默改旧图。

from-edition 将已选报道全部映射到新的待确认文字卡，并保留版次/来源绑定；需要照片时再按实际素材替换。桥接不代表自动确认，也不原地改写 edition-state。原 content-state、锁定项和拒绝风格绑定保留。

post_state.restore 用 from-revision、expected-revision 和 new-revision 新建恢复版本，不删除新旧版本。show 只读当前指针；即使来源暂时离线仍可查看已保存工作状态和交付目录。需要新生成时才要求来源存在。单写者锁占用或中断残留时停止，先核对是否仍有写者与完整历史，不自动删锁抢写。
