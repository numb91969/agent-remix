# 贴图头条 · 26.9.6 R3

面向微信贴图号的图文编辑专家：优先服务报纸、报道和融媒体编辑，也帮助创作者将照片与原话整理为一篇作品。保留既有名称、默认单图入口与历史作品；不代表微信官方产品。

## R3 新能力

- 作品级图组：首图、有序图片、独立标题／配文／话题、用户品牌和来源。支持媒体与创作者两类呈现。
- 3:4（1080×1440）、方图（1080×1080）、旧9:16（1080×1920）为本地设计建议；未声称微信强制尺寸、数量或字数上限。
- 全部 PDF 页摄入、原图只读、完整文本提取、明确待语义复核。已登记的相同素材批次可复用。
- 逐卡修改、换图、增删、排序、品牌配置、锁定、确认与不可覆盖的版本恢复。未变卡片保留确认并复用渲染缓存。
- 实际输出有序 PNG、配文文本、离线整篇预览、来源清单及作品 ZIP。预览支持逐图查看、缩略检查、图片获取和文案复制。
- 旧 cover／edition 可旁侧派生成新作品。历史 PNG 可逐字节导出；旧状态与新旧作品都不被覆盖。
- 新头像采用蓝橙“标题图卡”B方向，提供512×512 PNG和可维护SVG；旧图标单独保留。专家logo不自动盖到用户作品上。
- 修复 DEF-3：缺省 digest 的合法整期 plan 在 patch 中按空数组处理；源状态与其他 plan 不变，错误请求返回明确错误。
- R2 的 crop、v1/v2 低置信和文档修复继续保留；真实宿主对 R2 的通过不自动证明 R3 的新能力。

## 使用

用户仍可以说“上传这张报纸版面，生成3个方案”“把这批报道或照片做成微信贴图作品”“修改上一版”。先交材料，看作品，再说修改。不要强迫单图用户选择新的流程。

执行环境：Python 3.10+、Pillow、pypdfium2。使用宿主提供的实际解释器，不能假定某个固定 venv。图片与状态流程不安装本地MCP或常驻服务。PDF模块按需加载。

从专家包根目录执行：

```bash
python -m pip install -r requirements.txt
python skills/tietu-toutiao/scripts/post_materials.py --project <项目目录> --input <明确提供的PDF或图片> --batch-id issue1
python skills/tietu-toutiao/scripts/post_state.py --project <项目目录> create --input post-plan.json
python skills/tietu-toutiao/scripts/post_state.py --project <项目目录> show --post-id post1
python skills/tietu-toutiao/scripts/post_state.py --project <项目目录> patch --post-id post1 --input post-patch.json
python skills/tietu-toutiao/scripts/post_state.py --project <项目目录> render --post-id post1 --out deliverables/draft1
python skills/tietu-toutiao/scripts/post_state.py --project <项目目录> render --post-id post1 --out deliverables/final1 --final
```

计划和修改请求见 references/wechat-post-workflow.md。draft 为待确认草案；final 需要作品与每张卡的当前摘要确认。不要为了通过检查而编造确认人或来源。图片识别和编辑语义仍由当前模型与用户核对，脚本不把元数据或文字提取冒充理解。

旧单图检查与制作命令保持可用：

```bash
python skills/tietu-toutiao/scripts/validate_content_state.py --input content-state.json --check-image-bounds
python skills/tietu-toutiao/scripts/build_covers.py --state content-state.json --out-dir covers
python skills/tietu-toutiao/scripts/continuity.py --input old-state.json
```

四模板 authoritative／visual／digest／synthesis 与 content-state.v1/v2 保留；图组是新增工作面，不自动迁移旧项目。

## 交付与外部边界

作品保存在用户项目 .tietu/posts 与显式指定的交付目录；项目名、卡片ID、版本ID有独立约束。原文件、旧图片和旧版本不删除。中断未完成的交付目录不会被标成成品；已有目录不覆盖。writer lock 冲突停止，不抢其他会话的写入。

本地作品ZIP、微信草稿写入、正式发布和推荐曝光分别报告。当前核心流程只交本地作品；publish-handoff.json 是人工上传衔接清单，不等于调用微信API或已经发布。连接器和企微外发仍是可选出口，push_wecom.py 保留显式外发确认。

## 安装复测

Agent 稳定标识 tietu-toutiao；Skill声明名 tietu-toutiao-layout 与目录 skills/tietu-toutiao 的映射保持不变。用官方 expert-manager 校验注册，显式使用真实宿主会话ID并回读marker；缺失时最多同命令幂等重试一次，不手写marker。隔离测试ID不得用于真实宿主。

本包为 26.9.6-retest-r3 复测候选，尚未正式提交或上架。新的图组、单页修改、确认、导出和头像需在目标宿主上复测。
