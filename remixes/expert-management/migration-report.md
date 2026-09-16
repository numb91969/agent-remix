# 五位神仙专家迁移记录

2026-09-12：已重新提交至 WorkBuddy「AI 资源管理 → 专家管理」，企业自建列表显示 5 条；五位均为 v1.0、已发布、所有用户可见，使用“保存并启用”提交。

| 名称 | 专家标识 | 分类 |
| --- | --- | --- |
| CFO 赵公明 | cfo-zhao-gongming | 神仙专家团·企业经营 |
| CHO 张亚子 | cho-zhang-yazi | 神仙专家团·企业经营 |
| 剧本 关汉卿 | guan-hanqing | 神仙专家团·AIGC |
| 分镜 吴道子 | wu-daozi | 神仙专家团·AIGC |
| 提示词 李白 | li-bai | 神仙专家团·AIGC |

全部上传原有对应 JPG 头像，同时将头像写入 ZIP。每包包含 .codebuddy-plugin/plugin.json、agents/*.md、skills/*/SKILL.md、avatars/avatar.jpg。ZIP 完整性测试通过，SHA256 见 packages.json。平台回读李白包名、151.6KB、v1.0 与所有成员权限均正确；列表核验全部五位的名称、分类、版本、发布状态和可见范围。未进行客户端下载运行测试。

## 能力迁移差异

- 三位 AIGC 专家的完整系统提示词与三项技能文件直接携带，无外部依赖和软链。
- 财务、人事保留角色正文，统一职位＋名字格式，删除开头禁止承认 AI 的条款。
- CFO 随包 finance-ops-portable 与 office-tables-portable：原财务 skill 存在缺失脚本、遥测/版本检查入口，因此用纯文本财务简报和表格流程替代这些入口。
- CHO 随包 hr-admin-portable 与 office-tables-portable：保留岗位画像、招聘面试、入职、人事行政台账方法。原市场技能的程序实现没有冒称迁移；不依赖 eRoad、招聘服务或外部表格服务。
- skill-creator 用于整理便携技能规范；不自动安装运行时、模型或第三方服务。

原企业智能体没有删除或停用，已有会话未改动。新专家管理记录是重新提交，不是原云端 Session 的搬迁。后续如需清理重复入口，可单独停用原五个企业智能体。
