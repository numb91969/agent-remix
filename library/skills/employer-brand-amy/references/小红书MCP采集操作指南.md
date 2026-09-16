# 小红书 MCP 采集操作指南（启动 / 登录 / 抓详情评论）

> Amy 读取小红书笔记详情、互动数据、**完整评论区**的权威方式。优于 WebFetch（取不到数据/评论）和 agent-browser 无头（被风控拦截 300012）。
> ⭐ 本机已装独立二进制服务，无需 npm。Amy 应优先用此 MCP 抓小红书。

---

## 一、服务本体与登录态（本机现状）

| 项 | 路径 |
|----|------|
| MCP 服务二进制 | `~/.local/bin/xiaohongshu-mcp` |
| 登录辅助二进制 | `~/.local/bin/xiaohongshu-login` |
| 工作目录（cookie/log/pid 都在这） | `~/.xiaohongshu/` |
| 登录态 cookie | `~/.xiaohongshu/cookies.json` |
| 服务端口 | `127.0.0.1:18060`，MCP 端点 `http://127.0.0.1:18060/mcp` |
| mcp.json 已配置 | `~/.workbuddy/mcp.json` → key `xiaohongshu` → `{"url":"http://127.0.0.1:18060/mcp"}` |

> ⚠️ **关键踩坑：必须 `cd ~/.xiaohongshu` 再启动**！服务用**相对路径**读写 `cookies.json`，从别处启动会读不到登录态、且扫码后存到错误位置导致"扫了还是未登录"。

---

## 二、启动服务（服务挂掉时）

```bash
# 1. 若端口被旧进程占用，先停掉
lsof -nP -iTCP:18060 -sTCP:LISTEN 2>/dev/null | awk 'NR==2{print $2}'   # 拿到PID
kill <PID>

# 2. 必须从 ~/.xiaohongshu 目录启动（相对路径读 cookie）
cd ~/.xiaohongshu && ~/.local/bin/xiaohongshu-mcp >> ~/.xiaohongshu/mcp.log 2>&1 &
echo $! > ~/.xiaohongshu/mcp.pid

# 3. 等 5 秒，确认监听
sleep 5; lsof -nP -iTCP:18060 -sTCP:LISTEN
```
> 用 Bash 工具 `run_in_background=true` 启动，避免阻塞。参数：`-headless`(默认true) / `-port`(默认:18060) / `-bin`(浏览器路径)。

---

## 三、MCP 调用协议（curl，三步握手）

服务是 **Streamable HTTP MCP**，每次会话要先握手拿 session-id：

```bash
BASE="http://127.0.0.1:18060/mcp"
HDR=(-H "Content-Type: application/json" -H "Accept: application/json, text/event-stream")

# ① initialize（响应头里取 mcp-session-id）
curl -s -D /tmp/h.txt "$BASE" "${HDR[@]}" -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"amy","version":"1.0"}}}' >/dev/null
SID=$(grep -i "mcp-session-id" /tmp/h.txt | awk '{print $2}' | tr -d '\r')

# ② initialized 通知
curl -s "$BASE" "${HDR[@]}" -H "mcp-session-id: $SID" -d '{"jsonrpc":"2.0","method":"notifications/initialized"}' >/dev/null

# ③ 调工具（tools/call）
curl -s "$BASE" "${HDR[@]}" -H "mcp-session-id: $SID" -d '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"check_login_status","arguments":{}}}' | tr -d '\r' | sed 's/^data: //'
```
> 响应是 SSE 格式，需 `tr -d '\r' | sed 's/^data: //'` 清洗成 JSON。
> 直接 `tools/list` 不握手会报 "invalid during session initialization"。

---

## 四、登录（cookie 失效时，约1个月一次）

```bash
# 取二维码（返回 base64 png）
curl -s "$BASE" "${HDR[@]}" -H "mcp-session-id: $SID" -d '{"jsonrpc":"2.0","id":4,"method":"tools/call","params":{"name":"get_login_qrcode","arguments":{}}}' | tr -d '\r' | sed 's/^data: //' > /tmp/xhs_qr.json
# 解码成图片 → 用 present_files 展示给用户扫码
python -c "import json,base64; d=json.load(open('/tmp/xhs_qr.json')); [open('/tmp/xhs_qr.png','wb').write(base64.b64decode(c['data'])) for c in d['result']['content'] if c.get('type')=='image']"
```
1. 解码出 `/tmp/xhs_qr.png` → `present_files` 给用户
2. 让用户：小红书App→我→右上菜单→扫一扫→扫码→**手机确认登录**
3. 用户回"好了" → 再次 `check_login_status` 确认 "✅ 已登录"
4. 二维码约 4 分钟过期，过期重新取

---

## 五、可用工具清单

| 工具 | 用途 | 关键参数 |
|------|------|---------|
| `check_login_status` | 查登录态 | — |
| `get_login_qrcode` | 取登录二维码 | — |
| `search_feeds` | 关键词搜笔记 | `keyword`；`filters.sort_by`(综合/最新/最多点赞/最多评论/最多收藏)、`publish_time`(一天内/一周内/半年内)、`note_type` |
| `get_feed_detail` | **抓单条详情+评论** | `feed_id`(必填)、`xsec_token`(必填,从链接或search取)、`load_all_comments`(true抓全部)、`limit`(一级评论数)、`click_more_replies`(展开子评论) |
| `user_profile` | 看用户主页 | — |
| `list_feeds` | 首页feed流 | — |
| `like_feed`/`favorite_feed`/`post_comment_to_feed`/`reply_comment_in_feed` | 点赞/收藏/评论/回复（⚠️ 写操作，舆情场景一般只读，慎用） | — |
| `publish_content`/`publish_with_video` | 发笔记（⚠️ 一般不用） | — |

### 抓详情+全部评论示例
```bash
curl -s --max-time 120 "$BASE" "${HDR[@]}" -H "mcp-session-id: $SID" \
  -d '{"jsonrpc":"2.0","id":5,"method":"tools/call","params":{"name":"get_feed_detail","arguments":{"feed_id":"<笔记ID>","xsec_token":"<token>","load_all_comments":true,"limit":60}}}' \
  | tr -d '\r' | sed 's/^data: //' > /tmp/xhs_detail.json
```
- 从分享链接取参数：`xiaohongshu.com/discovery/item/<feed_id>?...xsec_token=<token>`
- 返回 `result.content[0].text` 是 JSON 字符串，二次 `json.loads`：
  - `data.note.interactInfo` → likedCount/commentCount/collectedCount
  - `data.note.time`(13位毫秒戳)/`ipLocation`
  - `data.comments.list[]` → 每条含 `content`/`likeCount`/`ipLocation`/`userInfo.nickname`/子回复

---

## 六、Amy 使用决策（小红书取数优先级）

1. **用户已给截图** → 直接读图取互动数（最快，不必起服务）
2. **需评论区内容 / 需精确数据 / 做监测搜索** → 用本 MCP：
   - 先 `check_login_status`；服务没起→按第二节启动；未登录→第四节扫码
   - 再 `search_feeds`（监测/爆点）或 `get_feed_detail`（单条case深挖评论）
3. **MCP 不可用且无截图** → WebFetch 兜底（仅能取标题+部分正文，注明数据缺失）
4. ❌ 不要用 agent-browser 无头直开小红书链接（必被风控 300012 拦）

> 评论区分析价值：判断是否"系统性问题"（大量+1同款遭遇）、有无竞品截胡、有无@官号喊话、高赞评论的定性（如"刷KPI"）——这些直接影响处置力度升级。
