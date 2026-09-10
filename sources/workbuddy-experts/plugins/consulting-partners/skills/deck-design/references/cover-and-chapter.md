# 封面与章节页（骨架示例；口径已并入 mck-consulting）

> **权威定义已写入** `$TP/references/designs/design-principle.mck-consulting.md` 的 **① 封面** 与 **③ 章节扉页**。
> 本文件保留可复制骨架与 exemplars 指针；写页以 mck-consulting 为准。
>
> 通用 `design-principle.consulting.md` 的「满铺 Navy + 白字巨编号」在本包内**禁止命中**。

视觉锚点（用 Read 看一眼，别凭记忆）：

- `exemplars/07-quarterly-covers.png` — 季刊/特刊封面拼图（白底 + 右侧/下方概念图 + 青线波纹）
- `exemplars/08-cover-title-zoom.png` — 标题块特写（白底 + 深蓝楷体）

---

## 1. 封面（默认：白底 + 右侧出血生图）

季刊特刊封面不是「一行字 + 一条线」。默认做成：**左侧标题区纯白 + 右侧概念图出血（约 40% 宽）+ 细青线纹氛围**。
纯白无图只允许作生图失败时的降级，不是默认成品。

**图是出血的，不是浮在白底上的一张方图**（2026-08 改版）：图**顶到画布右、上、下三条边**，
主体被边缘裁断是**刻意效果**，不是事故——那正是特刊封面的做法。
这样整张图只剩**左边一条接缝**要处理，比四边都露白容易收得多。

🔴 **出血 ≠ 边角碎影**（2026-08 实测共病）：「靠右 + 允许裁断」写得太松时，
模型会把主体缩成右下角一小坨、或只露出轮毂/气流线——版面中间整片死白，
看起来像「贴边装饰」而不是特刊主视觉。裁断是**啃掉主体 15–25%**，
不是只留边角碎片；主体仍须一眼可辨。

### 必须

| 元素 | 规格 |
|---|---|
| 底 | `#FFFFFF` 满铺。**禁止**满铺 `#051C2C` / `#061F32` / `#062032` |
| **深蓝签名（必做）** | **左侧竖轨** **24px** × 全高 `#051C2C`（**不要顶条**）。这是白底上的麦肯锡深蓝辨识，不是满铺封面 |
| 主标 | 60–72px Bold `#051C2C`，`fontFamily: '楷体'`，**左对齐**，最多两行；**≤9 字/行** |
| 副标 | 22–26px `#7D7E81`，楷体，紧贴主标下；**≤24 字/行、最多两行** |
| 装饰线 | 主标下 **72 × 4px** `#051C2C`，再跟 **40 × 3px** `#00A9F4`（深蓝主、亮青辅） |
| **右侧概念图** | **默认必做**：`ImageGen` → `assets/cover-accent.png`；**出血**：`right:0 top:0 width:520 height:720`，`objectFit: 'cover'`；主体占竖条 **55–70%**，边缘只啃 **15–25%**，禁止碎影/右下角小摆件。属性名是 **`src`**，**禁止**写成 `source` |
| 署名 | 左下；署名上方再加一条 **32 × 3px** `#051C2C`；**底边 ≤640** |
| 日期 | 署名下一行，楷体（含「年/月」） |
| 安全边 | 左内容从 **100** 起（24 竖轨 + 边距）；主标约 y=200–240 |
| **文字与图的间距** | 所有文本块宽 **≤580**（右边界 680），与图左缘 760 之间留 **≥80** 的白 |

🔴 **主标、副标、署名都必须包在带显式 `width` 的 `<Box>` 里。**
2026-08 实测事故：副标写成 `<Text style={{position:'absolute', left:100, top:444}}>`——
**一个宽度都没给的绝对定位文本**，于是 33 个字一路排到 x≈890，右半句被封面图整段吃掉。
不给宽度就不会换行，这是比"宽度设大了"更常见的写法。

而且**门禁查不出来**：`gate_check.py` 的「文字被压住」显式排除图片
（`kind != "pic"`，理由见该函数注释——端点直标压在图上是麦式做法），
所以这类缺陷只能靠几何提前防住，别指望跑完门禁能发现。

### 生图流程（封面写页前完成）

1. Read `exemplars/07-quarterly-covers.png`（看白底那几张：牛熊、赛车、机器人、青线波纹）。
2. 调 `ImageGen`，**`aspect_ratio` 取 `3:4` 竖图**（版面里是 520×720 的竖条，
   出方图会被 `cover` 裁掉两侧近 14%，主体容易被切坏）。prompt 固定骨架（**背景写在第一句，别放末尾**）：
   - **背景（第一位，必须写死）**：**纯白 `#FFFFFF` 无缝背景、均匀平光、背景与画布融为一体**；
     英文关键词一并给上：`pure white #FFFFFF seamless background, flat even lighting, no backdrop`
   - 主体：与议题相关的**概念 3D / 静物特写**（车、设备、抽象几何），**主体直接坐在纯白上**
   - 氛围：细亮青 `#00A9F4` 波纹线、冷色青蓝。
     **英文里把 `cyan` 这个词写出来**，只给 hex 容易出成宝蓝（实测过一次）
   - **构图（配合出血）——占比硬约束，不只写「靠右裁断」**：
     - 主体占竖条画面约 **55–70%**（宽与高都要撑住，不是只占右下角一角）
     - 机位用 **3/4 侧视或 3/4 侧前/侧后**，须保留**可辨轮廓的大半个主体**
       （车：至少车顶线 + 大半车身；设备：整机大半身；勿只剩轮毂/局部面板）
     - 右 / 上 / 下边缘**各啃掉主体约 15–25%**（刻意出血）；**禁止**裁到只剩碎片
     - **左侧约 25–35% 保持干净纯白**（接缝带）——与版面白无缝相接
     - 主体在竖条里**上下向要有存在感**（顶缘或底缘至少一侧被裁到，或主体高度占条高 ≥60%）；
       禁止整坨缩在右下、上方大片空
     - 英文一并写死量级，例如：
       `large hero object filling 55-70% of frame, three-quarter view,
        slightly cropped by right/top/bottom edges (15-25% only),
        left 30% clean white for seamless bleed, recognizable full silhouette,
        NOT a tiny corner ornament, NOT extreme close-up of a fragment`
     - 不要写"大量留白"，模型会理解成灰调氛围；也不要只写
       "subject on the right / cropped by edges"——缺占比时模型默认出碎影
   - **禁忌**：**灰底 / 渐变底 / 影棚背景纸 / 暗角 vignette / 画框描边**、
     文字、Logo、人脸大头、卡通、暖色、满铺深蓝底、
     **极近距局部特写（只露轮/角/气流线）**、**右下角小摆件构图**

   > ⚠️ 「3D 渲染 / 静物特写」在模型里默认配影棚布光，而影棚的默认背景就是**灰色无缝纸带渐变**，
   > 所以白底仍要显式写死并放首句。但**别指望提示词能把底洗成纯白**，那一步交给第 3 步的脚本。

   > ⚠️ 「靠右下 + 允许裁断」是必要但不足的：没有占比与裁切幅度时，
   > 实测会稳定出两类废图——**(A) 右下角小摆件、上下半出血**；
   > **(B) 极端侧面碎切、只剩局部**。两者都判失败，改 prompt 重出，不要用
   > 拉大 `<Image width>` 硬救（会挤字，且救不了碎影）。

3. 保存为 `assets/cover-accent.png`，**必跑白场归一化**：

   ```bash
   python3 scripts/whiten_bg.py assets/cover-accent.png --seam left
   ```

   看到 `✅ ... 留白带非白 0.0%` 才算过，再写 `01.slide`。脚本做两件事：
   把近白底拉成纯 `#FFFFFF`（这个它能修），以及检查**接缝侧 15% 留白带**里有没有主体
   （这个它只能报，得你改 prompt 重生成）。退出码 2 是图里压根没白底，3 是接缝不干净。

   > 留白带这条比"看四角白不白"严得多，是实测补的：方图那次左边缘**中位数是 255、四角也全白**，
   > 但卡片堆在中间高度伸了出来，`cover` 裁掉左右各 14% 之后正好把它竖直切断，
   > 在封面上留下一条露出图边界的直线。只看边缘一列查不到——那一列 76% 的行确实是白的。

   > 🔴 **这一步不能省，也不要试图用提示词替代。** 扩散模型几乎不输出精确的 255：
   > 2026-08 实测，提示词首句已写死 `pure white #FFFFFF`，出图四角仍是 **RGB(244,244,244)**；
   > 把提示词改狠之后重出一张，四角还是 243–245，**改前改后没有区别**。
   > 244 与版面的 255 差 11 级，在纯白封面上就是一个肉眼可见的浅灰方块。
   > 这是模型输出特性，不是提示词写得不够狠——脚本 0.6 秒解决，纯标准库无依赖。

4. 出图后 **Read 原图自检**（白场脚本管不了构图，只能靠眼看）：

   | 判据 | 过 | 不过 → 重出 |
   |---|---|---|
   | 主体占比 | 竖条里主体约 55–70%，一眼认出是什么 | 右下角小摆件；或只剩局部碎片 |
   | 裁切幅度 | 右/上/下啃掉一小截，轮廓仍完整可读 | 裁到无法辨认；或上下都不碰边（半出血） |
   | 接缝 | 左侧 25–35% 干净白，无主体伸出 | 主体伸进左留白带（`whiten_bg` 也会报） |
   | 视角 | 3/4 可辨大半身 | 极端贴边侧影、只露轮毂/边角 |

5. 最多重试 2 次；仍失败 → 降级用下方「无图骨架」，并在交付说明里写一句「封面装饰图未生成」。

### 禁止

- 满铺深蓝 / 渐变 / 阴影 / 金色 / 居中海报排版
- 主标用白字；生图拉满整页再叠白字（又变深色封面）
- 标题、副标、署名被图挡住——**出血图不透明，文本块宽度超 580 必然出这个事故**
- 图只贴右边缘、上下仍留白（半出血），或图四边都浮在白底里（旧的 `contain` 做法）
- **主体过小或碎切**：右下角装饰摆件、极端侧面局部特写——用拉大 `width` 硬救无效，必须重出
- 写实人物大头、K 线截图、竞品 Logo 拼贴

### 默认骨架（右侧出血生图 + 深蓝签名）

`width:520` 的图从 x=760 出血到右边缘；文本块 `width:580` 排在 x=100–680，
两者之间留 80px 白。**这三个数字是配平过的，改一个要把另外两个一起算过。**

```jsx
<Slide style={{ width: 1280, height: 720, background: '#FFFFFF', position: 'relative' }}>
    <Box style={{ position: 'absolute', left: 0, top: 0, width: 24, height: 720, background: '#051C2C' }} />
    {/* 属性名是 src，不是 source —— 写成 source 图不显示 */}
    <Image
        src="assets/cover-accent.png"
        style={{ position: 'absolute', right: 0, top: 0, width: 520, height: 720, objectFit: 'cover' }}
    />
    <Box style={{ position: 'absolute', left: 100, top: 220, width: 580 }}>
        <Text style={{ fontFamily: '楷体', fontSize: 64, fontWeight: 'bold', color: '#051C2C', lineHeight: 1.2 }}>
            中国新能源汽车行业分析
        </Text>
        <Box style={{ width: 72, height: 4, background: '#051C2C', marginTop: 28 }} />
        <Box style={{ width: 40, height: 3, background: '#00A9F4', marginTop: 8 }} />
        <Text style={{ fontFamily: '楷体', fontSize: 24, color: '#7D7E81', lineHeight: 1.45, marginTop: 24 }}>
            从规模竞赛到效率竞赛：渗透率拐点后的格局、利润与出海
        </Text>
    </Box>
    <Box style={{ position: 'absolute', left: 100, top: 590, width: 480 }}>
        <Box style={{ width: 32, height: 3, background: '#051C2C', marginBottom: 16 }} />
        <Text style={{ fontFamily: '楷体', fontSize: 16, color: '#7D7E81' }}>
            丁笃行（Ding）· 战略咨询合伙人
        </Text>
        <Text style={{ fontFamily: '楷体', fontSize: 16, color: '#7D7E81', marginTop: 8 }}>
            2026年8月
        </Text>
    </Box>
</Slide>
```

### 降级：无图骨架（仅生图失败时；深蓝签名仍保留）

```jsx
<Slide style={{ width: 1280, height: 720, background: '#FFFFFF', position: 'relative' }}>
    <Box style={{ position: 'absolute', left: 0, top: 0, width: 24, height: 720, background: '#051C2C' }} />
    <Box style={{ position: 'absolute', left: 100, top: 220, width: 900 }}>
        <Text style={{ fontFamily: '楷体', fontSize: 64, fontWeight: 'bold', color: '#051C2C', lineHeight: 1.2 }}>
            中国新能源汽车行业分析
        </Text>
        <Box style={{ width: 72, height: 4, background: '#051C2C', marginTop: 28 }} />
        <Box style={{ width: 40, height: 3, background: '#00A9F4', marginTop: 8 }} />
        <Text style={{ fontFamily: '楷体', fontSize: 24, color: '#7D7E81', lineHeight: 1.45, marginTop: 24 }}>
            从规模竞赛到效率竞赛：渗透率拐点后的格局、利润与出海
        </Text>
    </Box>
    <Box style={{ position: 'absolute', left: 100, top: 590 }}>
        <Box style={{ width: 32, height: 3, background: '#051C2C', marginBottom: 16 }} />
        <Text style={{ fontFamily: '楷体', fontSize: 16, color: '#7D7E81' }}>丁笃行（Ding）· 战略咨询合伙人</Text>
        <Text style={{ fontFamily: '楷体', fontSize: 16, color: '#7D7E81', marginTop: 8 }}>2026年8月</Text>
    </Box>
</Slide>
```

---

## 2. 章节扉页（白底轻量，不要反白巨字）

### 必须

| 元素 | 规格 |
|---|---|
| 底 | `#FFFFFF`。**禁止**满铺深蓝 |
| **深蓝签名（必做）** | 与封面同款：**左侧竖轨 24px** `#051C2C`（**不要顶条**） |
| 编号 | **深蓝底块** 约 **120×88**，内白字 **48px** Arial Bold（`01`/`02`）。**不是** 160–320px 半透明白字，也不是纯字号飘在白底上 |
| 章节名 | 40–48px Bold `#051C2C`，楷体，编号块下方 |
| 装饰线 | **72 × 4px** `#051C2C` + **40 × 3px** `#00A9F4` |
| 英文副标 | 可选，20px `#7D7E81`，Arial |
| 页码 | 右下 14px 灰，可保留 |

### 禁止

- 满铺 `#051C2C` / `#062032` + 白字
- 160–320px 低透明白色巨字编号（旧预设）
- 插画撑满、渐变、金色、Cyan 大色块
- 章节扉页**不要**加生图（封面实验满意后再说）
- 只有细青线、没有任何 `#051C2C` 块面（会显得不像麦肯锡）

### 骨架

```jsx
<Slide style={{ width: 1280, height: 720, background: '#FFFFFF', position: 'relative' }}>
    <Box style={{ position: 'absolute', left: 0, top: 0, width: 24, height: 720, background: '#051C2C' }} />
    <Box style={{ position: 'absolute', left: 100, top: 240, width: 120, height: 88, background: '#051C2C', alignItems: 'center', justifyContent: 'center' }}>
        <Text style={{ fontFamily: 'Arial', fontSize: 48, fontWeight: 'bold', color: '#FFFFFF' }}>01</Text>
    </Box>
    <Box style={{ position: 'absolute', left: 100, top: 360, width: 900 }}>
        <Text style={{ fontFamily: '楷体', fontSize: 44, fontWeight: 'bold', color: '#051C2C', lineHeight: 1.25 }}>
            市场全景
        </Text>
        <Box style={{ width: 72, height: 4, background: '#051C2C', marginTop: 20 }} />
        <Box style={{ width: 40, height: 3, background: '#00A9F4', marginTop: 8 }} />
        <Text style={{ fontFamily: 'Arial', fontSize: 20, color: '#7D7E81', marginTop: 20 }}>
            Market Overview
        </Text>
    </Box>
    <Box style={{ position: 'absolute', right: 56, bottom: 40 }}>
        <Text style={{ fontFamily: 'Arial', fontSize: 14, color: '#7D7E81' }}>03</Text>
    </Box>
</Slide>
```

**若章节短、页数紧**：可以**取消独立扉页**，只保留目录大编号 + 正文右上角章节进度
（`02 竞争格局`，14–16px `#7D7E81`）。

---

## 3. 防「字被挡 / 字被裁」清单（封面与内页共用）

实测常见不是「形状越界」，而是下面几类——`slidep-validate` 常放过：

| 现象 | 正解 |
|---|---|
| 目录/卡片最后一行掉进 y>646 页脚区 | 先算：`top + 行高×行数 + gap ≤ 640`。5 卡两列 = **三行**，卡高 ×3 + gap×2 必须进得去 |
| 行动标题折成两行，压扁图形区 | 标题 **≤34 字 / 一行**；多说的放口径副行 |
| `Arial` 的 `<Text>` 里夹了「万/月/年」 | **拆开**：数字 `Arial`，中文单位另起 `楷体`；或整段含中文一律楷体 |
| 横条 `flexDirection:'row'` 行尾丢字 | 文字加 `flexShrink: 0`，或加宽容器 |
| 色块高度按最短文案定，长文案被裁 | 卡高按**最长**那条算；不够就加高或删字，**不缩字号** |

---

## 4. 与通用 consulting 预设冲突时怎么选

| 议题 | 通用 `design-principle.consulting.md`（禁命中） | **`mck-consulting` / 本文件** |
|---|---|---|
| 封面底 | 满 Navy 或左半 Navy | **白底 + 左侧宽竖轨深蓝签名 + 右侧特刊生图** |
| 章节底 | 满铺 `#062032` | **白底 + 同款深蓝签名 + 深蓝编号底块** |
| 章节编号 | 160–320px 白字 | **120×88 深蓝底块内白字** |
| 居中 | 封面/扉页可居中 | **一律左对齐** |

写页前读 `design-principle.mck-consulting.md`；门禁不单独查「是否深色封面」，靠预览与自检清单把关。
