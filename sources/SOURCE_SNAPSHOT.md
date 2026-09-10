# Source snapshot

本目录的两套 AGENCY-AGENTS 快照来自：

- [jnmetacode/AGENCY-AGENTS-ZH](https://github.com/jnmetacode/AGENCY-AGENTS-ZH)，归档 commit `b08f35c07c62d985d0c60a4faaa7304ad4aee686`；
- [msitarzewski/AGENCY-AGENTS](https://github.com/msitarzewski/AGENCY-AGENTS)，归档 commit `6d29a9b08785a0e49ffc9818bbdd381164c2df5f`。

`workbuddy-experts/` 是从本机 WorkBuddy marketplace 目录生成的可移植文本快照：保留专家 Markdown、`SKILL.md`、references、包 metadata、README/LICENSE；运行时脚本、第三方 vendor、数据集、数据库、媒体和本机凭据按根目录 `EXPORT_MANIFEST.md` 排除。WorkBuddy 的专家 prompt 全量快照和关系数据库位于 `../catalog/workbuddy_expert_catalog/`。

源文件做了路径脱敏和已知示例密钥替换，以便归档；这不是可直接安装的 WorkBuddy marketplace 镜像。
