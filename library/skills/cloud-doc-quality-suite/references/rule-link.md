# 规则 3：超链接异常检测

## 目的

检测目标文档中是否存在**异常、失效或不可访问**的超链接。

## 工作流程

### Step 1：提取所有超链接

扫描全文，提取以下类型链接：

| 链接类型 | 格式示例 |
|----------|----------|
| 显式超链接 | `[文本](URL)`、`<a href="URL">` |
| 内联 URL | 直接出现的 http/https 链接 |
| 锚点链接 | `#anchor` 内部章节链接 |
| 引用式链接 | `[文本][ref]` 及其定义 |

记录每个链接的：**链接文本、链接地址、所在位置**

### Step 2：分类

| 链接类型 | 说明 | 示例 |
|----------|------|------|
| 外部链接 | 指向外部网站 | `https://cloud.tencent.com/document/product/xxx` |
| 内部平台链接 | 企业内部知识平台 | 云知、乐享、iWiki、Confluence 等 |
| 锚点链接 | 文档内部章节跳转 | `#第三章-产品架构` |
| 邮件链接 | mailto 协议 | `mailto:support@tencent.com` |
| 文件下载链接 | 文件资源 | `https://xxx.com/download/file.pdf` |

### Step 3：执行检测规则

> **核心原则：必须从原文出发，不要联想和推理，不要夸大问题**

#### 一、请求异常检测

| 子类型 | 判定条件 |
|--------|----------|
| HTTP 4xx | 400/401(公开文档)/403/404/410 |
| HTTP 5xx | 500/502/503 |
| DNS 失败 | 域名无法解析(NXDOMAIN)、已过期、拼写错误（如 `clod.tencent.com`） |
| 请求超时 | 连接超时(>10s) 或 读取超时(>30s) |

#### 二、锚点异常检测

- 文档内部锚点目标章节已删除/重命名/拼写错误
- 外部页面锚点已不存在

#### 三、平台文档链接异常检测

| 平台 | 异常判定 | 常见格式 |
|------|----------|----------|
| 云知（腾讯云知识库） | 已删除/下架/空间归档 | `https://doc.weixin.qq.com/doc/xxx` |
| 乐享知识库 | 已删除/知识库关闭/404 | `https://*.lexiangla.com/pages/xxx` |
| iWiki / Confluence | 页面已删除/空间移除 | `https://iwiki.woa.com/pages/viewpage.action?pageId=xxx` |
| 腾讯云官网文档 | 已下线/迁移/ID失效/404 | `https://cloud.tencent.com/document/product/xxx` |
| 其他平台（GitHub/飞书/语雀/Notion） | 页面不可访问 | 各平台 URL 格式 |

#### 四、链接格式规范检测

| 子类型 | 规则要点 | 判定条件 | 反例 |
|--------|---------|---------|------|
| 外网链接必须绝对链接 | 指向外部站点的链接必须使用完整绝对 URL（含 `https://` 协议头及域名），禁止使用相对路径引用外网资源 | 链接目标为外部域名但写法为相对路径（如 `//cloud.tencent.com/xxx`、`/document/product/xxx` 却指向外网），或缺失协议头 | `[文档](//cloud.tencent.com/document/product/213)`、`[文档](document/product/213)` |
| 禁止内部预览链接 | 正式发布文档中禁止出现内部预览态 / 编辑态链接（含 `!preview`、`!editLang`、`!draft`、`?preview=` 等参数或路径片段） | URL 匹配 `!preview` / `!editLang` / `!draft` / `?preview=` / `edit.` / `-preview.` 等预览编辑态特征 | `https://cloud.tencent.com/document/product/213!preview`、`https://xxx.com/doc/123!editLang=zh` |

**处理原则**：
- 检测发现即输出，属于**写作规范硬性错误**，与链接可访问性并列。
- 若同一链接既命中格式规范又命中可访问性异常（如 404），分别输出两条问题，不合并。

#### 五、特殊链接处理（不直接判定为异常）

| 特殊类型 | 处理方式 |
|----------|----------|
| 需登录认证的内部平台链接 | 返回 401/403 标注 `"AUTH_REQUIRED"`（需认证访问），非"失效" |
| 占位/示例链接 | 不检测：`example.com`、`localhost`、`your-domain.com`、`<链接>` |
| mailto 链接 | 仅检查邮箱格式，不验证真实性 |
| 含临时参数链接 | 标注 `"TEMP_PARAM"`（含临时参数，可能失效） |

## 输出格式

```json
[{
  "链接文本": "文档中显示的链接文字",
  "链接地址": "完整的 URL 地址",
  "所在位置": "链接在文档中所处的章节或段落",
  "异常类型": "枚举值之一（见下表）",
  "异常详情": "异常的具体描述，不超过30个汉字",
  "修复建议": "针对该异常的具体修复建议"
}]
```

### 异常类型枚举

| 枚举值 | 说明 |
|--------|------|
| `HTTP_404` | 页面不存在（404 Not Found） |
| `HTTP_4XX` | 其他客户端错误（400/401/403/410 等） |
| `HTTP_5XX` | 服务端错误（500/502/503 等） |
| `DNS_FAILURE` | DNS 解析失败 |
| `TIMEOUT` | 请求超时 |
| `ANCHOR_INVALID` | 锚点失效 |
| `PLATFORM_REMOVED` | 平台文档已删除/下架 |
| `PLATFORM_ARCHIVED` | 平台文档/空间已归档 |
| `FORMAT_ERROR` | 链接格式错误 |
| `RELATIVE_EXTERNAL` | 外网链接使用了相对路径 / 缺失协议头 |
| `PREVIEW_LINK` | 内部预览 / 编辑态链接（含 `!preview`、`!editLang` 等） |
| `AUTH_REQUIRED` | 需认证访问（提醒类） |
| `TEMP_PARAM` | 含临时参数，可能失效 |

### 输出要求

1. 纯 JSON 格式，不含 Markdown 代码块符号
2. 无异常返回 `[]`
3. "异常类型" 使用上方枚举值之一
4. "异常详情" 不超过 30 个汉字
5. 多轮校验结果完全一致

### 检测优先级

| 优先级 | 异常类型 |
|--------|----------|
| P0 - 严重 | `HTTP_404`、`PLATFORM_REMOVED`、`DNS_FAILURE`、`PREVIEW_LINK` |
| P1 - 重要 | `ANCHOR_INVALID`、`FORMAT_ERROR`、`RELATIVE_EXTERNAL`、`HTTP_5XX` |
| P2 - 一般 | `TIMEOUT`、`PLATFORM_ARCHIVED`、`HTTP_4XX` |
| P3 - 提醒 | `AUTH_REQUIRED`、`TEMP_PARAM` |

## 注意事项

- **区分认证与失效**：401/403 不直接判定为"链接失效"
- **跳过占位链接**：example.com / localhost 等不检测
- **实际验证优先**：尽量通过实际请求验证，而非仅凭 URL 推断
- **记录验证方式**：报告中说明是实际请求还是推断
- **格式规范与可访问性并列输出**：`RELATIVE_EXTERNAL` / `PREVIEW_LINK` 属静态规则，无需发起网络请求即可判定，且与 HTTP 检测结果不互斥
