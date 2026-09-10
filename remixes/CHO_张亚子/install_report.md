# CHO 张亚子｜安装与 Remix 报告

## 安装结果

- Agent 名称：CHO 张亚子
- 对话身份：我是 CHO 张亚子（文昌帝君）
- 定位：首席人力资源官（CHO）兼行政负责人，覆盖选、育、用、留与办公运营
- 发布状态：已发布并启用
- Agent ID：`agent_01M23YSFP8TPG17QCN48DMX07G`
- 发布时间：2026-09-10 10:23（WorkBuddy 页面显示）
- 创建方式：基于本地合并数据库 `merged_catalog.db` 的 1004 条 agent 记录、721 个 WorkBuddy skill 记录及对应本地提示词，多来源融合重写
- 浏览器页面：WorkBuddy 企业智能体 → 新建 Agent
- 可见范围：企业内全员可见
- 头像：已上传并随 v1 发布；写实摄影风格的文昌帝君/现代 CHO 形象，手机、平板与现代办公场景；本地压缩文件：`agent_avatars/CHO张亚子_avatar.jpg`（768×768，约 160KB）
- 页面技能计划：智能招聘大师、eRoad 智能岗位画像、新员工入职清单、WJ 的 Excel / WPS 表格自动化工具
- 未绑定外部连接器：轻流/QingFlow、腾讯招聘实时接口、HR 数仓、内部 HR 知识库、飞书人事、背景调查、海外 HR 数据服务；原因是需要额外连接、登录态、权限、密钥或特定司法辖区

## 参与 Remix 的 agent

### HR 运营与行政主干

1. WorkBuddy `HrOperationsTeam`（HR 运营团队）——招聘、薪酬、组织发展、人员分析、政策咨询、入职运营和统一交付结构；移除了必须创建 Team/Spawn 子团队的实现指令，改写为单 Agent 可执行流程。
2. WorkBuddy `SmbOperations`（毕运营）——岗位发布、结构化面试材料、Offer 模板、入职初始化、工具上下文、日常/周度/季度运营简报和行动项。
3. AGENCY-AGENTS-ZH `hr/hr-recruiter`（招聘专家）——中国招聘渠道、HC 审批、岗位画像、简历筛选、面试协调、Offer、背调、入职和候选人体验。
4. AGENCY-AGENTS-ZH `specialized/hr-onboarding`（HR 入职管理专家）——预入职、第一天、第一周、30-60-90 天、合规材料、福利登记、经理准备度和早期留存。

### 招聘、面试与人才获取

5. AGENCY-AGENTS-ZH `specialized/recruitment-specialist`（人才获取专家）——ATS、能力模型、STAR 结构化面试、渠道 ROI、雇主品牌、校招/社招、猎头管理和招聘漏斗。
6. WorkBuddy `RecruitmentExpert`（伯乐乐）——全流程招聘和人才获取方法。
7. WorkBuddy `Txzhaopin`（腾讯招聘专家）——招聘需求、JD、面试、评估、招聘数据、雇主品牌和路由/写操作边界；只吸收方法论，不默认启用腾讯实时接口。
8. WorkBuddy `IhrAiInterviewer` / `IhrConference`——岗位画像、面试维度、面试大纲、结构化纪要和待办；只吸收结构化面试与记录思路，不启用 iHR 外部服务。

### 绩效、组织、发展与员工体验

9. AGENCY-AGENTS-ZH `hr/hr-performance-reviewer`（绩效管理专家）——OKR/KPI 双轨、360 反馈、过程辅导、校准、晋升答辩、PIP、申诉和留痕。
10. WorkBuddy `PerfManagementExpert`（绩效管理专家）——目标制定、绩效辅导、反馈、角色扮演和能力测评闭环。
11. WorkBuddy `CorporateTrainingDesigner`（育才才）——需求诊断、能力差距、课程地图、混合学习、内部讲师、领导力发展和 Kirkpatrick 四层评估。
12. AGENCY-AGENTS-ZH `specialized/organizational-psychologist`（组织心理学家）——心理安全、团队动力、JD-R/burnout 风险、文化评估、敬业度、冲突与变革中的员工体验；改为 HR 场景下的非临床、聚合式建议。
13. WorkBuddy `CareerBroker`（鹅厂职业经纪人）——职业画像、发展路径、导师和人才成长建议，仅吸收方法论。

### HR 数字化与知识治理

14. WorkBuddy `QingflowHrExpert`（小Q）——招聘、培训、绩效、入职和人力分析的闭环设计；保留表单/流程/看板/权限的方案方法，不默认连接轻流。
15. WorkBuddy `HrDigitalExpert`（HR 数智专家）——HR 数据指标、权限最小化、数据表访问、知识检索和看板治理；不直接移植腾讯内部数仓、鉴权和应用部署指令。
16. WorkBuddy `Xiaot`（小T HR 智能助手）——仅作为能力覆盖参考，未采用其必须把所有输入原样转发至外部 HR Agent 的纯代理实现。

## 采用的 skill 方法

### 已绑定并可直接使用

- 智能招聘大师：覆盖 JD 定制、人才画像、简历筛选、笔面试方案、成绩统计和流程可视化；仍要求公司自定义和审批法律/薪酬条款。
- eRoad 智能岗位画像：把零散岗位需求转成可评审的岗位画像与招聘评估标准。
- 新员工入职清单：生成新员工或新用户的入职/上手检查清单。
- WJ 的 Excel / WPS 表格自动化工具：以零依赖表格处理支持考勤、人力台账、招聘漏斗、绩效/培训汇总与行政清单。

### 已吸收方法论但未默认挂载

- 招聘与面试：`ai-recruiting-engine`、`interview-assistant`、`interview-data-processor`、`interview-talent-modeler`、`recruitment-process-tracker`、`recruit-data-dashboard`、`assessment-quality-expert`、`headhunter-recommend`、`recruitment-inquiry-bot`。
- 入职与发展：`onboarding-flow-builder`、`onboarding-reflection`、`hr-performance-assistant`、`hr-analytics-dashboard`、`career-development-consultant`、`mentor-recommender`。
- HR 数字化与权限：`hr-ai-knowledge`、`hr-data-router`、`hr-data-sql-builder`、`data-table-permission-checker`、`hr-right`、`control-hr-claw-app`、`page-deliver`。
- 面谈与协作：`ihr-base`、`ihr-bootstrap`、`ihr-conference`、`ihr-shared`。

## 软链与直接带入的决定

- 本地技能仍以 `workbuddy_expert_catalog/skills/by-skill` 软链保存，用于来源追踪、版本审计和后续维护，不复制文件造成漂移。
- WorkBuddy 企业智能体页面不能把本机软链直接当线上运行时能力，因此只通过页面绑定 `hiring`、`onboarding` 和 Excel 技能。
- 依赖轻流、腾讯招聘/HR 数仓、iHR、内部知识库、外部背调或海外 HR 服务的技能未直接带入；没有授权或连接状态时，Agent 输出材料、方案、手工核验路径和降级方案，不假装已查询或已写入系统。
- 未默认依赖 .NET；行政工作以清单、台账、表格、制度草案和审批流设计为主，需要特定办公系统时再按权限逐项接入。

## 关键合规处理

- 避免把他国劳动法或过时的中国法律数字直接写成普适结论；涉及劳动合同、社保公积金、假期、竞业、解除、背调和个人信息时要求确认主体、工作地与当前官方口径。
- 绩效、晋升和招聘强调结构化、证据、校准、回避与申诉，不复制僵化强制分布。
- 保留 HR/行政执行边界：Agent 可以起草和分析，未经明确授权不录用/淘汰、不发 Offer、不改档案/薪酬/权限、不发布政策、不采购、不删除数据。
