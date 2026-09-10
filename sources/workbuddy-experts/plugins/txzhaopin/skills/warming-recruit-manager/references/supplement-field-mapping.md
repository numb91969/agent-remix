# 场景 G：字段映射与冲突说明

字段补充配置入口：`config/supplement/field_mappings.json`。

## 1. 共享主表

保温经营和字段补充共用主表：

```text
catalog_dos_da_mcp.hrdw.Report_School_Recruiti_Info_List
```

共享候选人标识字段：

```text
offer_id
resume_id
name
recruit_manager_name
offer_staff_subtype_name
org_full_name_cn
expect_entry_date
offer_link
resume_link
```

## 2. 场景化口径

### 保温经营口径

- `sign_status IN ('已签','毁约')`
- `entry_status IN ('待入职')`
- 默认招聘类型：`毕业生` / `应届实习生` / `日常实习生`

### 字段补充口径

- `step_name = '待确认入职时间'`
- `state_name = '流程中'`
- `entry_status IN ('未发起','流程中')`
- 可处理招聘类型：`毕业生` / `应届实习生` / `日常实习生` / `正式聘用制`

两类口径不得互相替代。字段补充支持正式聘用制，不代表保温经营默认纳入正式聘用制。

## 3. 关键字段关系

| 语义 | HRData / 保温字段 | 招聘详情 API 字段 | 回写字段 | 回写规则 |
|---|---|---|---|---|
| 导师 | `tutor_name_en`, `tutor_staff_id8` | `tutor.name_en`, `tutor.staff_id8` | `fields.tutor` | `staff_id8 + name_en` 双因子必填 |
| 直接上级 | `lead_name_en`, `lead_staff_id8` | `leader.name_en`, `leader.staff_id8` | `fields.leader` | `staff_id8 + name_en` 双因子必填 |
| 直接上级岗位 | `leader_post_name` | `leader_post.post_name`, `leader_post.post_id8` | `fields.leader_post` | 只传 `post_id8` |
| 入职岗位 | `post_name_cn`, `position_name_cn` | `post_name_cn`, `post_id` | `fields.post_name_cn` | 写入岗位名称 |

## 4. 字段来源优先级

1. 招聘系统详情页当前值：用于判断是否已有值；已有值默认不覆盖。
2. HRData 空字段查询结果：用于定位空单据、展示原值、提供组织/面试官策略输入。
3. 用户确认策略：用于生成建议值。
4. 用户确认结果：用于回写 payload。

## 5. 字段别名兼容

脚本读取字段时应通过 `field_mappings.json` 处理别名，不在脚本中散落硬编码。已知别名包括：

- `lead_name_en` / `leader_name_en` / `leaderNameEn`
- `lead_staff_id8` / `leader_staff_id8` / `leaderId`
- `leader_post_name` / `leaderPostName` / `leaderOaPostName`
- `leader_post_id8` / `leaderOaPostId`
- `org_full_name_cn` / `orgFullName`

## 6. 冲突处理原则

- 字段展示可以使用中文名或组合名；写入必须使用接口要求的结构化字段。
- `lead_name_en` 只可视为直接上级英文名，不等价于员工 ID。
- `leader_post_name` 只用于展示或校验，不替代 `leader_post.post_id8` 回写。
- HRData 原值不作为建议值唯一来源；详情页当前值和用户确认优先。
