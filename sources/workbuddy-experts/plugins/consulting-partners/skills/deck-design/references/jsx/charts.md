# 咨询图表 JSX 片段库

**取用规则**：整段复制到 `slides/NN.slide`，**默认只改数据数组与文案**；几何数字是经实测配平的起点，不是死锁。

**几何怎么调（允许，但有边界）**：
- **默认**：照抄几何（760×376 绘图区、行高公式、房屋五层预算等），只换数据与标签。
- **可以改**：一页多图并排/上下叠、条目显著多于/少于片段默认、右栏结论变厚需让图——按比例缩绘图区宽高、行高、柱宽、`left/top` 步长。
- **改完必须**：① 内容区仍落在 **166–646**，墨水底边尽量 ≥560；② 相关量一起改（折线要同步 `points` / 圆点 / 线端 `top`；堆叠段 `left+w` 之和 = 轨宽；房屋五层高度和 ≤478）；③ 色值仍在 `mck-palette`；④ 跑 `slidep-validate` + `jsx_lint.py`。
- **禁止**：为塞字去缩字号（<14 FAIL）；把坐标基准从「直接父元素」改成整页乱加偏移；预测底纹改回外层 absolute `#EFEFF0` Box。

动笔前按 `../exemplars/README.md` **打开本文件对应 JSX 节**整段复制（折线 §1、多情景 §1.1、
灰 track §2、双向 §2.1、双栏 §2.2、堆叠横条 §2.4、哑铃 §2.5、热力 §3、2×2 §4、气泡 §5、
瀑布 §6、竖柱矩阵 §8、圆环 §9）。**agent 默认不 Read PNG**；PNG 仅人工校对可选。

## 排序依据：麦肯锡真实用什么图

本文件的章节顺序 = 麦肯锡的真实使用频率，**不是按"哪种图难画"排的**。
对《麦肯锡中国季刊》2020+ 语料 487 张图表的实测分布：

| 类型 | 实测占比 | 本文件 |
|---|---|---|
| 折线趋势 | **50%** | §1 / §1.1 多情景 |
| 流程 / 价值链 | **20%** | 见 `structures.md` §3；泳道 §6 |
| 热力矩阵 | **10%** | §3 |
| 横向条形 | 6% | §2 / §2.1 / §2.2 / §2.4 / §2.5 |
| 堆叠柱 | 5% | §2.6 原生；竖向矩阵 §8 |
| 散点气泡 | 3% | §5 |
| 二维矩阵 2×2 | 2% | §4 |
| 瀑布 | <1% | §6 |
| 圆环 | — | §9 手绘 |
| Mekko / 漏斗 | ≈0 | 附录，**非必要不用** |

**这个顺序很重要**：上一版片段库把精修片段全押在瀑布、Mekko、漏斗上，而占八成的折线、
流程、热力三类没有麦味实现——结果是"每页都有图，但每张图都不像麦肯锡"。
动笔前先查这张表，**别再为了炫技去画语料里根本不存在的图型**。

---

## ⚠️ 动笔前必读的三条硬规矩

> 🔴 **坐标系铁律**：`position:'absolute'` 的 `left/top` 相对**直接父元素**，不是整页
> （Yoga 语义，与 CSS 不同——父元素有没有 `position` 都一样，实测确认）。
> 绘图区容器内的柱子、气泡、色块、连线一律用**局部坐标**（`0…width` / `0…height`），
> **不许把容器的 top/left 再加一遍**。完整正误对照见 `structures.md` 开头。

> 🔴 **纵向撑满铁律**：内容区 166–646（可用 480px），墨水底边须到 **y≥560**（约 85%）。
> 行/条数少于片段默认时**加高行高或条高**，禁止照抄矮几何让矮图贴顶、下半空白过大。
> 热力/横条公式见 §2、§3；`gate_check`「下半留白」会 WARN。

> 🔴 **一律用 `top` 正向定位，禁用 `bottom` / `right`**。
> `bottom` 要求直接父元素在纵轴上尺寸确定，否则高度按 0 算、元素被锚到绘图区**顶部**
> 朝上长并翻出画布，且不报任何错（实测柱状图整体上翻 204px，`slidep-validate` 静默放过）。
> 柱子写 `top: 绘图区高 − 柱底距 − 柱高`。本文件所有片段都已按这条改写过，照抄即可。
> 九组实测矩阵见 `../../SKILL.md` 已知坑 4。

> 🔴 **横排文字一律加 `flexShrink: 0`**。`flexDirection:'row'` 的子元素默认可收缩，
> 排不下时渲染器会把它们一起压窄到刚好塞进容器——几何毫无异常，但行尾会被截掉（实测丢过 `[A]`）。

**页面 y 坐标基准**（与 `exhibit-anatomy.md` 一致，本文件所有片段的容器都从这里起）：

| 元素 | y |
|---|---|
| Action Title（36px，结论句 20–23 字≈一行） | 72 |
| 口径副行（18px 灰） | 121 |
| 1px 深蓝分割线 | 154 |
| **内容区（本文件片段的外层容器）** | **166 起，至 646，可用 480px** |
| 页脚 Footnote / Source / 页码 | 662–700 |

---

## 1. 麦式折线（占语料 50%，最该做对的一张图）

锚点 PNG（可选校对）：`../exemplars/09-line-trend.png`。多情景变体见 §1.1（`15`）。

**为什么必须手绘**：原生 `<Chart lineChart>` 关不掉横向网格线和 Y 轴，而麦肯锡折线是
**无轴、无网格、线端直标终值、预测段浅灰底纹**。这四条里原生一条都做不到，
所以占比最高的图型反而只能手绘。

**几何**：绘图区 760×376。基线在 `top: 340`，x 标签在 `top: 350`。
数值换算 `y = 340 − 数值 / 满刻度 × 300`，满刻度取比最大值略大的整数（本例 100）。
x 步长 110，起点 40：`x = 40 + i × 110`。

**斜线是本文件唯一允许用 `<svg>` 的地方**——务必让 svg 与绘图区**等尺寸、零偏移**，
否则线与标签会整体错开一个容器偏移量（`jsx_lint.py` 会报"连线脱节"）。

> 🔴 **预测段底纹铁律（OpenEvidence 8/11 页复盘）**：`#EFEFF0`「预测区间」**只许**写在
> `<svg>` 内最底层 `<rect fill='#EFEFF0'>`。**禁止**外层
> `<Box style={{ position:'absolute', background:'#EFEFF0', … }}>`——
> 即便源码把 Box 写在 `<svg>` 前面，slidep 仍会把 absolute 色块画到折线 `<p:pic>` **之后**，
> 盖住整段走势（`gate_check`「绘制顺序」FAIL）。「预测区间」四字标签放在基线上方空隙
> （约 `top: 318`），不要压在折线上。`jsx_lint.py` 会直接拦 absolute `#EFEFF0` 大色块。

```jsx
<Box style={{ position: 'absolute', top: 166, left: 56, width: 1168, height: 480, flexDirection: 'row', gap: 40 }}>
    <Box style={{ width: 760 }}>
        {/* 图例：inline 微线段，不用 Office 图例 */}
        <Box style={{ flexDirection: 'row', gap: 24, height: 26, paddingLeft: 40 }}>
            {[
                { c: '#00A9F4', n: 'AI 总体采用率' },
                { c: '#051C2C', n: '其中：生成式 AI' },
            ].map((l, i) => (
                <Box key={i} style={{ flexDirection: 'row', alignItems: 'center', gap: 8, flexShrink: 0 }}>
                    <Box style={{ width: 24, height: 3, background: l.c, flexShrink: 0 }} />
                    <Text style={{ fontFamily: '楷体', fontSize: 16, color: '#191919' }}>{l.n}</Text>
                </Box>
            ))}
        </Box>

        <Box style={{ position: 'relative', width: 760, height: 376 }}>
            <svg width={760} height={376} viewBox='0 0 760 376'>
                {/* ✅ 预测底纹：svg 内最先画的 <rect> */}
                <rect x='424' y='0' width='336' height='340' fill='#EFEFF0' />
                <polyline points='40,274 150,247 260,223 370,190 480,154 590,118 700,88'
                          fill='none' stroke='#00A9F4' strokeWidth='3' />
                <polyline points='370,304 480,250 590,199 700,154'
                          fill='none' stroke='#051C2C' strokeWidth='3' />
                {[[40,274],[150,247],[260,223],[370,190],[480,154],[590,118],[700,88]].map((p, i) => (
                    <circle key={'a'+i} cx={p[0]} cy={p[1]} r='4' fill='#00A9F4' />
                ))}
                {[[370,304],[480,250],[590,199],[700,154]].map((p, i) => (
                    <circle key={'b'+i} cx={p[0]} cy={p[1]} r='4' fill='#051C2C' />
                ))}
            </svg>

            {/* 标注放在底纹下缘空隙，勿压折线；不要再画一层 EFEFF0 Box */}
            <Box style={{ position: 'absolute', left: 424, top: 318, width: 336, alignItems: 'center' }}>
                <Text style={{ fontFamily: '楷体', fontSize: 16, color: '#7D7E81' }}>预测区间</Text>
            </Box>

            {/* 线端直标终值——麦肯锡不让读者去对刻度 */}
            <Box style={{ position: 'absolute', left: 712, top: 76 }}>
                <Text style={{ fontFamily: 'Arial', fontSize: 20, fontWeight: 'bold', color: '#00A9F4' }}>84%</Text>
            </Box>
            <Box style={{ position: 'absolute', left: 712, top: 142 }}>
                <Text style={{ fontFamily: 'Arial', fontSize: 20, fontWeight: 'bold', color: '#051C2C' }}>62%</Text>
            </Box>

            {/* 基线：唯一保留的一条轴，1px 浅灰。没有 Y 轴、没有网格线 */}
            <Box style={{ position: 'absolute', left: 0, top: 340, width: 760, height: 1, background: '#B3B3B3' }} />

            {['2017', '2019', '2021', '2023', '2026E', '2028E', '2030E'].map((t, i) => (
                <Box key={i} style={{ position: 'absolute', left: 40 + i * 110 - 40, top: 350, width: 80, alignItems: 'center' }}>
                    <Text style={{ fontFamily: 'Arial', fontSize: 16, color: '#191919' }}>{t}</Text>
                </Box>
            ))}
        </Box>
    </Box>

    <Box style={{ width: 368, justifyContent: 'center', gap: 18 }}>
        <Box style={{ width: 48, height: 3, background: '#2251FF' }} />
        <Text style={{ fontFamily: '楷体', fontSize: 26, fontWeight: 'bold', color: '#051C2C', lineHeight: 1.35 }}>
            采用曲线尚未见顶
        </Text>
        <Text style={{ fontFamily: '楷体', fontSize: 22, color: '#191919', lineHeight: 1.45 }}>
            总体采用率七年从 22% 升至 84% [F]，且 2026 年后斜率未收敛。生成式 AI 起步晚三年但斜率更陡，
            2030 年前两条曲线的差距将收窄到 22pp [E]。
        </Text>
    </Box>
</Box>
```

**改数据时要同步改三处**：`polyline points`、圆点数组、线端标签的 `top`。
三处对不上就是"点和线错位"，`jsx_lint.py` 查不到（它只查 `<Box>`），只能靠自己核。
**线端两个标签的 `top` 至少差 30px**，否则中文数字会叠在一起。

### 1.1 多情景折线（实线 / 虚线）

锚点 PNG（可选校对）：`../exemplars/15-line-automation-page.png`。**默认照抄改数据**；多图/条目数异常时可按节首「几何怎么调」改尺寸。

**用途**：同一指标多情景（基准 / 乐观 / 悲观 / 政策），用 stroke 实虚区分，不用彩虹色。
高亮一条实线 `#051C2C`，其余 `#00A9F4` 实线 + `#AAE6F0`/`#027AB1` 虚线（`strokeDasharray='8 6'`）。

**几何**：与 §1 同（760×376，基线 340）。预测底纹仍用 svg 内最底层 `<rect fill='#EFEFF0'>`。

```jsx
<Box style={{ position: 'absolute', top: 166, left: 56, width: 1168, height: 480, flexDirection: 'row', gap: 40 }}>
    <Box style={{ width: 760 }}>
        <Box style={{ flexDirection: 'row', gap: 20, height: 26, paddingLeft: 40, flexWrap: 'wrap' }}>
            {[
                { c: '#051C2C', n: '基准', dash: false },
                { c: '#00A9F4', n: '加速', dash: false },
                { c: '#027AB1', n: '缓慢', dash: true },
                { c: '#AAE6F0', n: '停滞', dash: true },
            ].map((l, i) => (
                <Box key={i} style={{ flexDirection: 'row', alignItems: 'center', gap: 8, flexShrink: 0 }}>
                    <Box style={{ width: 28, height: 3, background: l.c, flexShrink: 0, opacity: l.dash ? 0.85 : 1 }} />
                    <Text style={{ fontFamily: '楷体', fontSize: 15, color: '#191919' }}>{l.n}{l.dash ? '（虚）' : ''}</Text>
                </Box>
            ))}
        </Box>
        <Box style={{ position: 'relative', width: 760, height: 376 }}>
            <svg width={760} height={376} viewBox='0 0 760 376'>
                <rect x='424' y='0' width='336' height='340' fill='#EFEFF0' />
                <polyline points='40,280 150,250 260,220 370,190 480,160 590,130 700,100'
                          fill='none' stroke='#051C2C' strokeWidth='3' />
                <polyline points='40,290 150,255 260,215 370,170 480,130 590,95 700,60'
                          fill='none' stroke='#00A9F4' strokeWidth='3' />
                <polyline points='40,275 150,255 260,240 370,225 480,210 590,200 700,190'
                          fill='none' stroke='#027AB1' strokeWidth='2.5' strokeDasharray='8 6' />
                <polyline points='40,300 150,285 260,275 370,270 480,265 590,262 700,260'
                          fill='none' stroke='#AAE6F0' strokeWidth='2.5' strokeDasharray='8 6' />
            </svg>
            <Box style={{ position: 'absolute', left: 424, top: 318, width: 336, alignItems: 'center' }}>
                <Text style={{ fontFamily: '楷体', fontSize: 15, color: '#7D7E81' }}>预测区间</Text>
            </Box>
            <Box style={{ position: 'absolute', left: 712, top: 88 }}>
                <Text style={{ fontFamily: 'Arial', fontSize: 18, fontWeight: 'bold', color: '#051C2C' }}>72%</Text>
            </Box>
            <Box style={{ position: 'absolute', left: 712, top: 48 }}>
                <Text style={{ fontFamily: 'Arial', fontSize: 18, color: '#00A9F4' }}>88%</Text>
            </Box>
            <Box style={{ position: 'absolute', left: 0, top: 340, width: 760, height: 1, background: '#B3B3B3' }} />
            {['2020', '2022', '2024', '2026E', '2028E', '2030E', '2032E'].map((t, i) => (
                <Box key={i} style={{ position: 'absolute', left: 40 + i * 110 - 40, top: 350, width: 80, alignItems: 'center' }}>
                    <Text style={{ fontFamily: 'Arial', fontSize: 15, color: '#191919' }}>{t}</Text>
                </Box>
            ))}
        </Box>
    </Box>
    <Box style={{ width: 368, justifyContent: 'center', gap: 16 }}>
        <Box style={{ width: 48, height: 3, background: '#2251FF' }} />
        <Text style={{ fontFamily: '楷体', fontSize: 26, fontWeight: 'bold', color: '#051C2C', lineHeight: 1.35 }}>
            情景差在执行速度
        </Text>
        <Text style={{ fontFamily: '楷体', fontSize: 22, color: '#191919', lineHeight: 1.45 }}>
            基准与加速在 2030 年差 16pp [E]；停滞情景几乎持平——关键变量是部署节奏而非技术上限。
        </Text>
    </Box>
</Box>
```

虚线系列**不要加圆点**（点会盖住虚线语义）。线端只直标高亮 + 次高亮两条，避免四条标签叠字。

---

## 2. 灰 track 横条（麦肯锡辨识度最高的单一特征）

锚点 PNG（可选校对）：`../exemplars/01-bar-grey-track.png`。双向 / 双栏 / 堆叠横 / 哑铃见 §2.1–§2.5。

**用途**：排名对比、受访者占比、并列比较。**凡是"排名 / 对比"型数据，一律用这个，
不许退回三栏卡片**——上一版最典型的翻车就是把竞争格局做成了卡片墙。

**核心特征**：每根蓝条底下压一根满宽 `#E6E6E6` 灰条表示 100% 基准。
有了它就可以**完全去掉 X 轴与网格线**，读者仍能判断"这一项占整体多少"。

**几何**：标签列 160 + track 520 + 数值列 60 = 740。
片段默认行高 34、行距 8（按 8 条写）。**条数少于 6 时必须加高**：
`rowH = floor((420 − (N−1)×gap) / N)`，`gap` 8–14，条本身高 ≈ rowH−8，夹在 **26–48**。
例：N=4 → rowH≈96、条高 40+；N=3 → 再加大 gap 或条高到 48，并在底部加一句结论注，
别让三条细条飘在内容区上半。
条宽 `= 数值 / 满刻度 × 520`，**全组共用一个满刻度**（本例 60），否则条长之间不可比。

```jsx
<Box style={{ position: 'absolute', top: 166, left: 56, width: 1168, height: 480, flexDirection: 'row', gap: 48 }}>
    <Box style={{ width: 740 }}>
        {[
            { n: '不准确', v: 56, hl: true },
            { n: '网络安全', v: 53, hl: false },
            { n: '知识产权侵权', v: 46, hl: false },
            { n: '监管合规', v: 45, hl: false },
            { n: '可解释性', v: 39, hl: false },
            { n: '个人隐私', v: 39, hl: false },
            { n: '取代人工', v: 34, hl: false },
            { n: '公平公正', v: 31, hl: false },
        ].map((r, i) => (
            <Box key={i} style={{ flexDirection: 'row', alignItems: 'center', height: 34, marginBottom: 8 }}>
                <Box style={{ width: 160, flexShrink: 0 }}>
                    <Text style={{ fontFamily: '楷体', fontSize: 18, color: '#191919' }}>{r.n}</Text>
                </Box>
                <Box style={{ position: 'relative', width: 520, height: 26, flexShrink: 0 }}>
                    <Box style={{ position: 'absolute', left: 0, top: 0, width: 520, height: 26, background: '#E6E6E6' }} />
                    <Box style={{
                        position: 'absolute', left: 0, top: 0,
                        width: Math.round(r.v / 60 * 520), height: 26,
                        background: r.hl ? '#051C2C' : '#AAE6F0',
                    }} />
                </Box>
                <Box style={{ width: 60, flexShrink: 0, paddingLeft: 12 }}>
                    <Text style={{ fontFamily: 'Arial', fontSize: 18, fontWeight: r.hl ? 'bold' : 'normal', color: r.hl ? '#051C2C' : '#7D7E81' }}>
                        {r.v}
                    </Text>
                </Box>
            </Box>
        ))}
    </Box>

    <Box style={{ width: 380, justifyContent: 'center', gap: 18 }}>
        <Box style={{ width: 48, height: 3, background: '#2251FF' }} />
        <Text style={{ fontFamily: '楷体', fontSize: 26, fontWeight: 'bold', color: '#051C2C', lineHeight: 1.35 }}>
            准确性是第一道闸门
        </Text>
        <Text style={{ fontFamily: '楷体', fontSize: 22, color: '#191919', lineHeight: 1.45 }}>
            56% 的受访企业把"输出不准确"列为正在着手解决的风险 [F]，比第二位高 3pp。
            合规类风险虽被高频提及，但排在技术可靠性之后。
        </Text>
    </Box>
</Box>
```

**三条规矩**：①**降序排列**，不许按字母或原始顺序；②**只高亮一根**，其余一律 `#AAE6F0`；
③数值直接标在条端右侧，**不设图例、不画 X 轴**。

### 2.1 双向横条（中轴左右）

锚点 PNG（可选校对）：`../exemplars/13-diverging-bar.png`。**默认照抄改数据**；多图/条目数异常时可按节首「几何怎么调」改尺寸。

**用途**：风险/收益、正负贡献、两极评价。中轴竖直 1px，左为负（或「风险」）用 `#061F79`，
右为正（或「机会」）用 `#00A9F4`；**禁止橙色**。

**几何**：标签列 160 + 左轨 250 + 中缝 8 + 右轨 250 + 数值列各 50 ≈ 768。行高按 N 用 §2 公式加高。

```jsx
<Box style={{ position: 'absolute', top: 166, left: 56, width: 1168, height: 480, flexDirection: 'row', gap: 40 }}>
    <Box style={{ width: 800 }}>
        <Box style={{ flexDirection: 'row', height: 28, marginBottom: 8, paddingLeft: 160 }}>
            <Box style={{ width: 250, alignItems: 'center' }}>
                <Text style={{ fontFamily: '楷体', fontSize: 15, color: '#7D7E81' }}>下行风险</Text>
            </Box>
            <Box style={{ width: 8 }} />
            <Box style={{ width: 250, alignItems: 'center' }}>
                <Text style={{ fontFamily: '楷体', fontSize: 15, color: '#7D7E81' }}>上行机会</Text>
            </Box>
        </Box>
        {[
            { n: '需求波动', neg: 42, pos: 18, hl: true },
            { n: '政策变化', neg: 35, pos: 28, hl: false },
            { n: '成本通胀', neg: 30, pos: 12, hl: false },
            { n: '技术替代', neg: 22, pos: 40, hl: false },
            { n: '人才缺口', neg: 18, pos: 25, hl: false },
        ].map((r, i) => (
            <Box key={i} style={{ flexDirection: 'row', alignItems: 'center', height: 56, marginBottom: 10 }}>
                <Box style={{ width: 160, flexShrink: 0 }}>
                    <Text style={{ fontFamily: '楷体', fontSize: 18, color: '#191919', flexShrink: 0 }}>{r.n}</Text>
                </Box>
                <Box style={{ position: 'relative', width: 250, height: 28, flexShrink: 0 }}>
                    <Box style={{ position: 'absolute', left: 0, top: 0, width: 250, height: 28, background: '#E6E6E6' }} />
                    <Box style={{
                        position: 'absolute', right: 0, top: 0,
                        width: Math.round(r.neg / 50 * 250), height: 28,
                        background: r.hl ? '#061F79' : '#AAE6F0',
                    }} />
                </Box>
                <Box style={{ width: 8, height: 40, background: '#B3B3B3', flexShrink: 0 }} />
                <Box style={{ position: 'relative', width: 250, height: 28, flexShrink: 0 }}>
                    <Box style={{ position: 'absolute', left: 0, top: 0, width: 250, height: 28, background: '#E6E6E6' }} />
                    <Box style={{
                        position: 'absolute', left: 0, top: 0,
                        width: Math.round(r.pos / 50 * 250), height: 28,
                        background: r.hl ? '#00A9F4' : '#AAE6F0',
                    }} />
                </Box>
                <Box style={{ width: 70, flexShrink: 0, paddingLeft: 10 }}>
                    <Text style={{ fontFamily: 'Arial', fontSize: 16, color: '#7D7E81', flexShrink: 0 }}>
                        −{r.neg}/{r.pos}
                    </Text>
                </Box>
            </Box>
        ))}
    </Box>
    <Box style={{ width: 328, justifyContent: 'center', gap: 16 }}>
        <Box style={{ width: 48, height: 3, background: '#2251FF' }} />
        <Text style={{ fontFamily: '楷体', fontSize: 26, fontWeight: 'bold', color: '#051C2C', lineHeight: 1.35 }}>
            风险侧更陡
        </Text>
        <Text style={{ fontFamily: '楷体', fontSize: 22, color: '#191919', lineHeight: 1.45 }}>
            需求波动下行敞口 42 [I]，显著高于上行 18——对冲应优先做需求侧而非技术侧。
        </Text>
    </Box>
</Box>
```

满刻度两侧各自独立（本例 50）；改数据时两侧用同一满刻度，否则左右不可比。

### 2.2 双栏排名横条

锚点 PNG（可选校对）：`../exemplars/17-dual-panel-risk-page.png`、`18-ranked-dual-bar-page.png`。**默认照抄改数据**；多图时可按比例改尺寸。

**用途**：两组 TopN 对比（如「认为重要」vs「已着手」），或左右两议题共用行标签。
左栏 `#051C2C`、右栏 `#00A9F4`，各自灰 track，**共用同一满刻度**。顶部 16px 灰列头说明口径。

```jsx
<Box style={{ position: 'absolute', top: 166, left: 56, width: 1168, height: 480 }}>
    <Box style={{ flexDirection: 'row', height: 28, marginBottom: 12, paddingLeft: 200 }}>
        <Box style={{ width: 320, alignItems: 'center' }}>
            <Text style={{ fontFamily: '楷体', fontSize: 16, color: '#7D7E81' }}>认为重要 %</Text>
        </Box>
        <Box style={{ width: 24 }} />
        <Box style={{ width: 320, alignItems: 'center' }}>
            <Text style={{ fontFamily: '楷体', fontSize: 16, color: '#7D7E81' }}>已着手解决 %</Text>
        </Box>
    </Box>
    {[
        { n: '输出不准确', a: 56, b: 31, hl: true },
        { n: '网络安全', a: 53, b: 28, hl: false },
        { n: '知识产权', a: 46, b: 22, hl: false },
        { n: '监管合规', a: 45, b: 35, hl: false },
        { n: '可解释性', a: 39, b: 18, hl: false },
    ].map((r, i) => (
        <Box key={i} style={{ flexDirection: 'row', alignItems: 'center', height: 52, marginBottom: 12 }}>
            <Box style={{ width: 200, flexShrink: 0 }}>
                <Text style={{ fontFamily: '楷体', fontSize: 18, color: '#191919', flexShrink: 0 }}>{r.n}</Text>
            </Box>
            <Box style={{ position: 'relative', width: 280, height: 26, flexShrink: 0 }}>
                <Box style={{ position: 'absolute', left: 0, top: 0, width: 280, height: 26, background: '#E6E6E6' }} />
                <Box style={{
                    position: 'absolute', left: 0, top: 0,
                    width: Math.round(r.a / 60 * 280), height: 26,
                    background: r.hl ? '#051C2C' : '#AAE6F0',
                }} />
            </Box>
            <Box style={{ width: 44, flexShrink: 0, paddingLeft: 8 }}>
                <Text style={{ fontFamily: 'Arial', fontSize: 17, fontWeight: r.hl ? 'bold' : 'normal', color: r.hl ? '#051C2C' : '#7D7E81', flexShrink: 0 }}>{r.a}</Text>
            </Box>
            <Box style={{ width: 24, flexShrink: 0 }} />
            <Box style={{ position: 'relative', width: 280, height: 26, flexShrink: 0 }}>
                <Box style={{ position: 'absolute', left: 0, top: 0, width: 280, height: 26, background: '#E6E6E6' }} />
                <Box style={{
                    position: 'absolute', left: 0, top: 0,
                    width: Math.round(r.b / 60 * 280), height: 26,
                    background: r.hl ? '#00A9F4' : '#AAE6F0',
                }} />
            </Box>
            <Box style={{ width: 44, flexShrink: 0, paddingLeft: 8 }}>
                <Text style={{ fontFamily: 'Arial', fontSize: 17, color: r.hl ? '#00A9F4' : '#7D7E81', flexShrink: 0 }}>{r.b}</Text>
            </Box>
        </Box>
    ))}
    <Text style={{ fontFamily: '楷体', fontSize: 18, color: '#7D7E81', marginTop: 16, lineHeight: 1.4 }}>
        「重要」与「已着手」平均落差约 20pp [F]——认知领先于行动是当前主矛盾。
    </Text>
</Box>
```

两组 Top5 **各自降序**时若行标签不同，拆成左右两套标签列（各 160），不要硬共用。

### 2.3 什么时候可以退回原生 `<Chart>`

条形图数据超过 12 项、或客户明确要求在 PowerPoint 里改数时，用原生
`<Chart chartType='barChart' barDirection='bar'>`，代价是带一条 Y 轴和横向网格线，
交付前用 `$ED` 的 `slide_update_chart_gridlines(visible=false)` 关掉。
**灰 track 效果原生做不出来**，这是手绘唯一不可替代的地方。

### 2.4 堆叠横条

锚点 PNG（可选校对）：`../exemplars/02-bar-stacked.png`。**默认照抄改数据**；多图/条目数异常时可按节首「几何怎么调」改尺寸。

**用途**：构成对比（各段占比叠在同一横条）。色阶深→浅 `#051C2C` → `#027AB1` → `#00A9F4` → `#AAE6F0`，**≤4 段**。
段内直标百分比（浅段用深字）。条总宽 = 满轨 520；各段宽按占比切。

```jsx
<Box style={{ position: 'absolute', top: 166, left: 56, width: 1168, height: 480, flexDirection: 'row', gap: 40 }}>
    <Box style={{ width: 760 }}>
        <Box style={{ flexDirection: 'row', gap: 16, height: 26, marginBottom: 12, paddingLeft: 160 }}>
            {[
                { c: '#051C2C', n: '自有' },
                { c: '#027AB1', n: '合资' },
                { c: '#00A9F4', n: '外购' },
                { c: '#AAE6F0', n: '其他' },
            ].map((l, i) => (
                <Box key={i} style={{ flexDirection: 'row', alignItems: 'center', gap: 6, flexShrink: 0 }}>
                    <Box style={{ width: 14, height: 14, background: l.c, flexShrink: 0 }} />
                    <Text style={{ fontFamily: '楷体', fontSize: 15, color: '#191919' }}>{l.n}</Text>
                </Box>
            ))}
        </Box>
        {[
            { n: '动力总成', parts: [
                { v: 45, left: 0, w: 234, c: '#051C2C' },
                { v: 30, left: 234, w: 156, c: '#027AB1' },
                { v: 15, left: 390, w: 78, c: '#00A9F4' },
                { v: 10, left: 468, w: 52, c: '#AAE6F0' },
            ], hl: true },
            { n: '智驾域控', parts: [
                { v: 20, left: 0, w: 104, c: '#051C2C' },
                { v: 25, left: 104, w: 130, c: '#027AB1' },
                { v: 40, left: 234, w: 208, c: '#00A9F4' },
                { v: 15, left: 442, w: 78, c: '#AAE6F0' },
            ], hl: false },
            { n: '座舱电子', parts: [
                { v: 15, left: 0, w: 78, c: '#051C2C' },
                { v: 20, left: 78, w: 104, c: '#027AB1' },
                { v: 50, left: 182, w: 260, c: '#00A9F4' },
                { v: 15, left: 442, w: 78, c: '#AAE6F0' },
            ], hl: false },
            { n: '底盘', parts: [
                { v: 55, left: 0, w: 286, c: '#051C2C' },
                { v: 20, left: 286, w: 104, c: '#027AB1' },
                { v: 15, left: 390, w: 78, c: '#00A9F4' },
                { v: 10, left: 468, w: 52, c: '#AAE6F0' },
            ], hl: false },
            { n: '内外饰', parts: [
                { v: 10, left: 0, w: 52, c: '#051C2C' },
                { v: 15, left: 52, w: 78, c: '#027AB1' },
                { v: 55, left: 130, w: 286, c: '#00A9F4' },
                { v: 20, left: 416, w: 104, c: '#AAE6F0' },
            ], hl: false },
        ].map((r, i) => (
            <Box key={i} style={{ flexDirection: 'row', alignItems: 'center', height: 56, marginBottom: 12 }}>
                <Box style={{ width: 160, flexShrink: 0 }}>
                    <Text style={{ fontFamily: '楷体', fontSize: 18, fontWeight: r.hl ? 'bold' : 'normal', color: '#191919', flexShrink: 0 }}>{r.n}</Text>
                </Box>
                <Box style={{ position: 'relative', width: 520, height: 32, flexShrink: 0 }}>
                    {r.parts.map((p, si) => (
                        <Box key={si} style={{
                            position: 'absolute', left: p.left, top: 0, width: p.w, height: 32,
                            background: p.c, alignItems: 'center', justifyContent: 'center',
                        }}>
                            {p.v >= 12 ? (
                                <Text style={{
                                    fontFamily: 'Arial', fontSize: 14, flexShrink: 0,
                                    color: (p.c === '#00A9F4' || p.c === '#AAE6F0') ? '#191919' : '#FFFFFF',
                                }}>{p.v}</Text>
                            ) : null}
                        </Box>
                    ))}
                </Box>
            </Box>
        ))}
    </Box>
    <Box style={{ width: 368, justifyContent: 'center', gap: 16 }}>
        <Box style={{ width: 48, height: 3, background: '#2251FF' }} />
        <Text style={{ fontFamily: '楷体', fontSize: 26, fontWeight: 'bold', color: '#051C2C', lineHeight: 1.35 }}>
            智驾最依赖外购
        </Text>
        <Text style={{ fontFamily: '楷体', fontSize: 22, color: '#191919', lineHeight: 1.45 }}>
            智驾域控外购占 40% [F]，显著高于动力总成——供应链议价权在供应商侧。
        </Text>
    </Box>
</Box>
```

**改数据**：先算各段 `w = round(占比/100×520)`，再累加 `left`；各段 `w` 之和必须 = 520。

### 2.5 哑铃差距

锚点 PNG（可选校对）：`../exemplars/06-dumbbell-gap.png`。**默认照抄改数据**；多图/条目数异常时可按节首「几何怎么调」改尺寸。

**用途**：同一主体两个时点 / 两个口径的差距（空心起点 → 实心终点）。可加极浅竖虚线刻度（唯一允许的竖向网格例外，色不得深于 `#CED0D1`）。

```jsx
<Box style={{ position: 'absolute', top: 166, left: 56, width: 1168, height: 480, flexDirection: 'row', gap: 40 }}>
    <Box style={{ width: 760 }}>
        <Box style={{ flexDirection: 'row', gap: 24, height: 26, marginBottom: 8, paddingLeft: 180 }}>
            <Box style={{ flexDirection: 'row', alignItems: 'center', gap: 8, flexShrink: 0 }}>
                <Box style={{ width: 12, height: 12, borderRadius: 6, border: '2px solid #00A9F4', flexShrink: 0 }} />
                <Text style={{ fontFamily: '楷体', fontSize: 15, color: '#191919' }}>2022</Text>
            </Box>
            <Box style={{ flexDirection: 'row', alignItems: 'center', gap: 8, flexShrink: 0 }}>
                <Box style={{ width: 12, height: 12, borderRadius: 6, background: '#051C2C', flexShrink: 0 }} />
                <Text style={{ fontFamily: '楷体', fontSize: 15, color: '#191919' }}>2025</Text>
            </Box>
        </Box>
        <Box style={{ position: 'relative', width: 760, height: 400 }}>
            {[20, 40, 60, 80].map((v, i) => (
                <Box key={i} style={{
                    position: 'absolute', left: 180 + v / 100 * 480, top: 0, width: 1, height: 360,
                    background: '#CED0D1', opacity: 0.5,
                }} />
            ))}
            {[
                { n: '一线城市', y: 20, x0: 314, x1: 478, hl: true, b: 62 },
                { n: '新一线', y: 88, x0: 266, x1: 410, hl: false, b: 48 },
                { n: '二线', y: 156, x0: 238, x1: 348, hl: false, b: 35 },
                { n: '三线及以下', y: 224, x0: 209, x1: 286, hl: false, b: 22 },
                { n: '县域', y: 292, x0: 194, x1: 247, hl: false, b: 14 },
            ].map((r, i) => (
                <Box key={i}>
                    <Box style={{ position: 'absolute', left: 0, top: r.y, width: 170 }}>
                        <Text style={{ fontFamily: '楷体', fontSize: 18, color: '#191919', flexShrink: 0 }}>{r.n}</Text>
                    </Box>
                    <Box style={{
                        position: 'absolute', left: r.x0, top: r.y + 10,
                        width: Math.max(r.x1 - r.x0, 2), height: 3,
                        background: r.hl ? '#051C2C' : '#AAE6F0',
                    }} />
                    <Box style={{
                        position: 'absolute', left: r.x0 - 6, top: r.y + 4,
                        width: 14, height: 14, borderRadius: 7,
                        border: '2px solid #00A9F4', background: '#FFFFFF',
                    }} />
                    <Box style={{
                        position: 'absolute', left: r.x1 - 6, top: r.y + 4,
                        width: 14, height: 14, borderRadius: 7,
                        background: r.hl ? '#051C2C' : '#027AB1',
                    }} />
                    <Box style={{ position: 'absolute', left: r.x1 + 12, top: r.y + 2, width: 60 }}>
                        <Text style={{ fontFamily: 'Arial', fontSize: 17, fontWeight: r.hl ? 'bold' : 'normal', color: r.hl ? '#051C2C' : '#7D7E81', flexShrink: 0 }}>
                            {r.b}%
                        </Text>
                    </Box>
                </Box>
            ))}
            <Box style={{ position: 'absolute', left: 180, top: 370, width: 480, height: 1, background: '#B3B3B3' }} />
        </Box>
    </Box>
    <Box style={{ width: 368, justifyContent: 'center', gap: 16 }}>
        <Box style={{ width: 48, height: 3, background: '#2251FF' }} />
        <Text style={{ fontFamily: '楷体', fontSize: 26, fontWeight: 'bold', color: '#051C2C', lineHeight: 1.35 }}>
            渗透差在扩大
        </Text>
        <Text style={{ fontFamily: '楷体', fontSize: 22, color: '#191919', lineHeight: 1.45 }}>
            一线从 28% 升至 62% [F]，县域仅到 14%——渠道下沉仍是最大增量池。
        </Text>
    </Box>
</Box>
```

`x = 180 + 占比/100×480`。改数据时重算 `x0`/`x1`/`y`（行距 68）。

### 2.6 堆叠柱（原生）

原生 `<Chart grouping='stacked'>` 可用（占语料 5%，简单构成用这个；**矩阵形多组竖柱**用手绘 §8）。
必传 `colors={['#051C2C', '#027AB1', '#00A9F4', '#AAE6F0']}`（深→浅，**≤4 段**），
`showDataLabels={true}`，柱顶另加一个 `<Box>` 文本标总量。

---

## 3. 热力矩阵（占语料 10%，上一版完全没有）

锚点 PNG（可选校对）：`../exemplars/03-heatmap.png`。**默认照抄改数据**；多图/条目数异常时可按节首「几何怎么调」改尺寸。

**用途**：多维评估、用例打分、影响强度。行列清晰命名，单色阶浅→深表强度，
左侧可外挂一列总量——这是麦肯锡最爱用的"一屏给总量 + 结构 + 细节"版式。

**几何**：行标签 150 + 外挂总量列 100 + 矩阵 790（6 列 × 130，列缝 2）= 1040。
列头 52。**行高不要死抄 42**：片段默认按 8 行写，行少时必须加高，否则图贴顶、下半空白过大
（`gate_check`「下半留白」WARN）。

> 🔴 **纵向撑满公式**（热力 / 横条通用）：内容区可用 ≈480px；扣掉图例行(~34) + 列头(52) +
> 底注(~36) 后，矩阵体可用 `bodyH ≈ 350`。
> `rowH = floor((bodyH − (N−1)×gap) / N)`，`gap` 取 2–4，`rowH` 夹在 **42–72**。
> 例：N=6、gap=4 → rowH=55；N=4、gap=4 → rowH=84→封顶 72 并加大 gap / 加底注卡。
> **禁止** N=4 仍用 rowH=42 让矩阵只占半屏。

**色阶固定五档**（`mck-palette.md` §2.1 的强弱色阶，全篇方向必须一致：深 = 影响大）：
`#99E6FF` → `#AAE6F0` → `#00A9F4` → `#027AB1` → `#051C2C`

**格内文字颜色**：`lvl >= 3` 用白字，否则用 `#191919`。这条不能凭感觉——
`#00A9F4` 配白字对比度不足 4.5:1，必须用深色字。

```jsx
<Box style={{ position: 'absolute', top: 166, left: 56, width: 1168, height: 480 }}>
    {/* 右上角 inline 图例：五个色块 + 低/高，不用 Office 图例 */}
    <Box style={{ position: 'absolute', left: 900, top: 0, flexDirection: 'row', alignItems: 'center', gap: 6 }}>
        <Text style={{ fontFamily: '楷体', fontSize: 15, color: '#7D7E81', flexShrink: 0 }}>影响　低</Text>
        {['#99E6FF', '#AAE6F0', '#00A9F4', '#027AB1', '#051C2C'].map((c, i) => (
            <Box key={i} style={{ width: 22, height: 14, background: c, flexShrink: 0 }} />
        ))}
        <Text style={{ fontFamily: '楷体', fontSize: 15, color: '#7D7E81', flexShrink: 0 }}>高</Text>
    </Box>

    <Box style={{ position: 'absolute', left: 0, top: 34, width: 1040, height: 402 }}>
        {/* 列头 */}
        <Box style={{ flexDirection: 'row', height: 52, alignItems: 'flex-end' }}>
            <Box style={{ width: 150, flexShrink: 0 }} />
            <Box style={{ width: 100, flexShrink: 0, paddingBottom: 6 }}>
                <Text style={{ fontFamily: '楷体', fontSize: 15, fontWeight: 'bold', color: '#7D7E81' }}>总体价值<br />（万亿美元）</Text>
            </Box>
            {['营销与销售', '客户运营', '产品研发', '软件工程', '供应链', '风险与法律'].map((h, i) => (
                <Box key={i} style={{ width: 130, marginLeft: i === 0 ? 0 : 2, flexShrink: 0, paddingBottom: 6, paddingRight: 6 }}>
                    <Text style={{ fontFamily: '楷体', fontSize: 15, fontWeight: 'bold', color: '#191919', lineHeight: 1.25 }}>{h}</Text>
                </Box>
            ))}
        </Box>

        {[
            { n: '银行与保险', tot: '2.0–3.4', lv: [4, 4, 2, 3, 1, 3] },
            { n: '零售消费品', tot: '1.2–1.9', lv: [4, 3, 2, 1, 3, 0] },
            { n: '软件技术',   tot: '1.4–2.6', lv: [3, 2, 4, 4, 1, 1] },
            { n: '医疗健康',   tot: '1.0–1.6', lv: [2, 3, 4, 2, 1, 2] },
            { n: '先进制造',   tot: '0.6–1.0', lv: [1, 2, 3, 2, 4, 1] },
            { n: '能源与材料', tot: '0.4–0.8', lv: [1, 1, 2, 1, 3, 2] },
            { n: '电信媒体',   tot: '0.4–0.7', lv: [3, 4, 2, 3, 0, 1] },
            { n: '公共部门',   tot: '0.2–0.4', lv: [1, 2, 1, 1, 1, 3] },
        ].map((r, ri) => (
            <Box key={ri} style={{ flexDirection: 'row', height: 42, marginTop: ri === 0 ? 0 : 2, alignItems: 'center' }}>
                <Box style={{ width: 150, flexShrink: 0 }}>
                    <Text style={{ fontFamily: '楷体', fontSize: 17, color: '#191919' }}>{r.n}</Text>
                </Box>
                <Box style={{ width: 100, flexShrink: 0 }}>
                    <Text style={{ fontFamily: 'Arial', fontSize: 17, fontWeight: 'bold', color: '#051C2C' }}>{r.tot}</Text>
                </Box>
                {r.lv.map((v, ci) => (
                    <Box key={ci} style={{
                        width: 130, height: 42, marginLeft: ci === 0 ? 0 : 2, flexShrink: 0,
                        background: ['#99E6FF', '#AAE6F0', '#00A9F4', '#027AB1', '#051C2C'][v],
                        alignItems: 'center', justifyContent: 'center',
                    }}>
                        <Text style={{ fontFamily: '楷体', fontSize: 15, color: v >= 3 ? '#FFFFFF' : '#191919' }}>
                            {['很低', '低', '中', '高', '很高'][v]}
                        </Text>
                    </Box>
                ))}
            </Box>
        ))}
    </Box>
</Box>
```

**格内文字可以留空**（原刊很多热力图只有色块没有字），但**行列标签绝不能省**。
若格内要放长文字（如具体用例名），把行高从 42 提到 56 并把字号降到 15px——
再长就该拆成两页，不许缩到 14px 以下。

---

## 4. 2×2 矩阵 / BCG（战略优先级）

锚点 PNG（可选校对）：`../exemplars/16-matrix-competition-page.png`。**默认照抄改数据**；多图时可按比例改尺寸。

**用途**：两维定位 + 第三维量级。右上象限浅青底表"优先"，高亮项深蓝实心白字，其余浅青空心。

**几何**：绘图区 620×380，中线在 `left: 310` / `top: 190`。气泡 `left/top` 是**左上角**坐标，
不是圆心——圆心 = `(left + r, top + r)`。半径 r 代表第三维大小，建议 17–44。

**标签规则**：`r ≥ 34` 的高亮气泡文字放圆内白字；`r < 34` 的一律把标签放在圆**外侧下方**，
否则中文必然溢出圆外（实测踩过的坑，也是麦肯锡季刊原图的做法）。

```jsx
<Box style={{ position: 'absolute', top: 166, left: 56, width: 1168, height: 480, flexDirection: 'row', gap: 44 }}>
    <Box style={{ width: 700 }}>
        <Box style={{ flexDirection: 'row', height: 420 }}>
            <Box style={{ width: 36, justifyContent: 'center', alignItems: 'center', flexShrink: 0 }}>
                <Text style={{ fontFamily: '楷体', fontSize: 16, color: '#191919' }}>市<br />场<br />吸<br />引<br />力</Text>
            </Box>
            <Box style={{ flex: 1 }}>
                <Box style={{ position: 'relative', width: 620, height: 380, border: '1px solid #B3B3B3' }}>
                    <Box style={{ position: 'absolute', left: 310, top: 0, width: 310, height: 190, background: '#AAE6F0' }} />
                    <Box style={{ position: 'absolute', left: 310, top: 0, width: 1, height: 380, background: '#7D7E81' }} />
                    <Box style={{ position: 'absolute', left: 0, top: 190, width: 620, height: 1, background: '#7D7E81' }} />

                    <Box style={{ position: 'absolute', left: 322, top: 10 }}>
                        <Text style={{ fontFamily: '楷体', fontSize: 18, fontWeight: 'bold', color: '#051C2C' }}>优先下注</Text>
                    </Box>

                    {[
                        { x: 470, y: 60, r: 44, n: '储能', hl: true },
                        { x: 372, y: 130, r: 34, n: '充电网络', hl: true },
                        { x: 156, y: 84, r: 26, n: '换电', hl: false },
                        { x: 220, y: 244, r: 22, n: '电池回收', hl: false },
                        { x: 456, y: 268, r: 20, n: '车载软件', hl: false },
                        { x: 96, y: 292, r: 17, n: '燃料电池', hl: false },
                    ].map((p, i) => (
                        <Box key={i}>
                            <Box style={{
                                position: 'absolute', left: p.x, top: p.y,
                                width: p.r * 2, height: p.r * 2, borderRadius: p.r,
                                background: p.hl ? '#051C2C' : '#FFFFFF',
                                border: p.hl ? '2px solid #FFFFFF' : '2px solid #00A9F4',
                                alignItems: 'center', justifyContent: 'center',
                            }}>
                                {p.hl ? (
                                    <Text style={{ fontFamily: '楷体', fontSize: 16, fontWeight: 'bold', color: '#FFFFFF', textAlign: 'center' }}>
                                        {p.n}
                                    </Text>
                                ) : null}
                            </Box>
                            {p.hl ? null : (
                                <Box style={{ position: 'absolute', left: p.x + p.r - 50, top: p.y + p.r * 2 + 4, width: 100, alignItems: 'center' }}>
                                    <Text style={{ fontFamily: '楷体', fontSize: 16, color: '#191919', textAlign: 'center' }}>{p.n}</Text>
                                </Box>
                            )}
                        </Box>
                    ))}
                </Box>
                <Box style={{ flexDirection: 'row', justifyContent: 'space-between', width: 620, marginTop: 8 }}>
                    <Text style={{ fontFamily: '楷体', fontSize: 15, color: '#7D7E81', flexShrink: 0 }}>低</Text>
                    <Text style={{ fontFamily: '楷体', fontSize: 16, color: '#191919', flexShrink: 0 }}>我方相对胜率 →</Text>
                    <Text style={{ fontFamily: '楷体', fontSize: 15, color: '#7D7E81', flexShrink: 0 }}>高</Text>
                </Box>
            </Box>
        </Box>
    </Box>

    <Box style={{ width: 380, justifyContent: 'center', gap: 18 }}>
        <Box style={{ width: 48, height: 3, background: '#2251FF' }} />
        <Text style={{ fontFamily: '楷体', fontSize: 26, fontWeight: 'bold', color: '#051C2C', lineHeight: 1.35 }}>
            右上象限只容得下两个
        </Text>
        <Text style={{ fontFamily: '楷体', fontSize: 22, color: '#191919', lineHeight: 1.45 }}>
            两者现有能力复用率均超 60%，是唯一不需要新建团队即可进入的赛道。
        </Text>
        <Text style={{ fontFamily: '楷体', fontSize: 16, color: '#7D7E81', lineHeight: 1.4 }}>
            气泡大小 = 2028E 市场规模
        </Text>
    </Box>
</Box>
```

**别把 2×2 做成四格文字框**。四个格子里各写一段话那是 SWOT 表格，不是矩阵——
矩阵的价值在于**把对象定位到连续的二维空间里**，让读者看出"谁离右上角更近"。
若手上只有定性判断没有坐标，那就不该用矩阵，改用 `structures.md` 的框架图。

---

## 5. 气泡 / 散点（两维 + 量级，带真实坐标轴）

锚点 PNG（可选校对）：`../exemplars/11-bubble.png`。**默认照抄改数据**；多图时可按比例改尺寸。

§4 片段的变体：**去掉两条中线与右上象限底色**，把 `border` 改为只留左下两条轴线
（左轴 `<Box>` 宽 1 高 380、底轴宽 620 高 1，色 `#7D7E81`），并在轴旁加 15px 灰刻度标签。
气泡与标签逻辑完全照用 §4。象限版用于"该投哪个"，坐标轴版用于"分布长什么样"。

---

## 6. 瀑布 / 桥图（增量归因）

锚点 PNG（可选校对）：`../exemplars/10-waterfall.png`。**默认照抄改数据**；多图时可按比例改尺寸。

**语料占比 <1%**，不是麦肯锡的常用图，**只在"必须解释从 A 到 B 差在哪"时才用**。

**没有暖色了**：现代刊是纯蓝青单色体系。首末柱深蓝 `#051C2C`，
增项亮青 `#00A9F4`，减项深靛 `#061F79`——靠色阶深浅 + 正负号 + 浮空位置三重表意。

**几何**：绘图区 760×376，基线 `top: 340`，`scale = 300 / 满刻度`（本例 `300/150 = 2` px/单位）。
柱宽 80、柱距 48、第 i 柱 `left = i × 128`。
**柱子一律用 `top` 定位**：`top = 340 − 柱底累计 × scale − 柱高`。

本例：100 →(+28)→ 128 →(+12)→ 140 →(−18)→ 122 →(−6)→ 116。

```jsx
<Box style={{ position: 'absolute', top: 166, left: 56, width: 1168, height: 480, flexDirection: 'row', gap: 40 }}>
    <Box style={{ width: 760 }}>
        <Box style={{ position: 'relative', width: 760, height: 376 }}>
            {/* 虚线累计水位：left = 前一柱右缘，top = 340 − 累计×scale − 1 */}
            {[
                { l: 80, t: 139 }, { l: 208, t: 83 }, { l: 336, t: 59 },
                { l: 464, t: 95 }, { l: 592, t: 107 },
            ].map((c, i) => (
                <Box key={i} style={{ position: 'absolute', left: c.l, top: c.t, width: 48, height: 1, borderTop: '1px dashed #B3B3B3' }} />
            ))}

            {[
                { l: 0,   t: 140, h: 200, c: '#051C2C' },
                { l: 128, t: 84,  h: 56,  c: '#00A9F4' },
                { l: 256, t: 60,  h: 24,  c: '#00A9F4' },
                { l: 384, t: 60,  h: 36,  c: '#061F79' },
                { l: 512, t: 96,  h: 12,  c: '#061F79' },
                { l: 640, t: 108, h: 232, c: '#051C2C' },
            ].map((b, i) => (
                <Box key={i} style={{ position: 'absolute', left: b.l, top: b.t, width: 80, height: b.h, background: b.c }} />
            ))}

            {/* 数值标签：top = 柱 top − 30 */}
            {[
                { l: 0,   t: 110, v: '100', c: '#051C2C', bold: true },
                { l: 128, t: 54,  v: '+28', c: '#00A9F4', bold: false },
                { l: 256, t: 30,  v: '+12', c: '#00A9F4', bold: false },
                { l: 384, t: 30,  v: '−18', c: '#061F79', bold: false },
                { l: 512, t: 66,  v: '−6',  c: '#061F79', bold: false },
                { l: 640, t: 78,  v: '116', c: '#051C2C', bold: true },
            ].map((t, i) => (
                <Box key={i} style={{ position: 'absolute', left: t.l, top: t.t, width: 80, alignItems: 'center' }}>
                    <Text style={{ fontFamily: 'Arial', fontSize: 20, fontWeight: t.bold ? 'bold' : 'normal', color: t.c }}>{t.v}</Text>
                </Box>
            ))}

            <Box style={{ position: 'absolute', left: 0, top: 340, width: 760, height: 1, background: '#B3B3B3' }} />

            {['2024 实际', '新客获取', '提价', '客户流失', '汇率', '2026E'].map((t, i) => (
                <Box key={i} style={{ position: 'absolute', left: i * 128, top: 350, width: 80, alignItems: 'center' }}>
                    <Text style={{ fontFamily: '楷体', fontSize: 16, color: '#191919', textAlign: 'center' }}>{t}</Text>
                </Box>
            ))}
        </Box>
    </Box>

    <Box style={{ width: 368, justifyContent: 'center', gap: 18 }}>
        <Box style={{ width: 48, height: 3, background: '#2251FF' }} />
        <Text style={{ fontFamily: '楷体', fontSize: 26, fontWeight: 'bold', color: '#051C2C', lineHeight: 1.35 }}>
            增长质量差于总量
        </Text>
        <Text style={{ fontFamily: '楷体', fontSize: 22, color: '#191919', lineHeight: 1.45 }}>
            两年净增 16 亿，但毛增量 40 亿里有 24 亿被流失与汇率抵消。这说明当前投入应从获客转向留存。
        </Text>
    </Box>
</Box>
```

**改数据时逐柱重算 `top`**，不能沿用同一个值——这是本片段最容易错的地方。
校验方法：任何一柱的 `top + height` 都必须 ≤ 340（基线），等于 340 的只有首末两根落地柱。

---

## 7. 什么时候用原生 `<Chart>`

只有**简单堆叠柱**还值得走原生（§2.6；好处是可编辑 OOXML）。
**圆环优先用手绘 §9**（原生环图关不了部分装饰，且与麦式中心 KPI 不一致）。
必须显式传参，否则会掉回 Office 默认蓝橙配色：

```jsx
<Chart
    style={{ height: 400 }}
    chartType='barChart'
    grouping='stacked'
    colors={['#051C2C', '#027AB1', '#00A9F4', '#AAE6F0']}   // 深→浅，永远不要省略
    showLegend={true}
    showDataLabels={true}              // 麦肯锡习惯直标数值
    legendColor='#7D7E81'
    axisColor='#7D7E81'
    dataLabelColor='#051C2C'
    background='#FFFFFF'
    data={[['细分', '高端', '中端'], ['2024', 31, 42], ['2025', 34, 51]]}
/>
```

**折线与横条不要走原生**（§1、§2 已给手绘片段）：原生关不掉网格线和 Y 轴，
而这两类恰恰是麦肯锡用得最多、也最讲究"无轴直标"的图型。
非要用原生时，交付前必须用 `$ED` 的 `slide_update_chart_gridlines(visible=false)` 关掉网格线，
`slide_update_chart_axis` 调坐标轴——**饼图和环图不支持这两个接口**。

---

## 8. 竖向堆叠柱矩阵

锚点 PNG（可选校对）：`../exemplars/14-column-vertical-page.png`。**默认照抄改数据**；多图/条目数异常时可按节首「几何怎么调」改尺寸。

**用途**：多类别 × 多系列的构成对比（如城市×车型渗透：基期深蓝 + 增量青）。
无 Y 轴、无横向网格；柱顶直标总量。

**几何**：绘图区宽 1000、高 400；基线 `top: 360`；每组宽 160、组内柱宽 28、柱缝 4。
`scale = 300 / 满刻度`。柱 `top = 360 − 累计高`。

```jsx
<Box style={{ position: 'absolute', top: 166, left: 56, width: 1168, height: 480 }}>
    <Box style={{ flexDirection: 'row', gap: 20, height: 26, marginBottom: 10 }}>
        {[
            { c: '#051C2C', n: '2020 基期' },
            { c: '#00A9F4', n: '2020–2025 增量' },
        ].map((l, i) => (
            <Box key={i} style={{ flexDirection: 'row', alignItems: 'center', gap: 8, flexShrink: 0 }}>
                <Box style={{ width: 16, height: 16, background: l.c, flexShrink: 0 }} />
                <Text style={{ fontFamily: '楷体', fontSize: 15, color: '#191919' }}>{l.n}</Text>
            </Box>
        ))}
    </Box>
    <Box style={{ position: 'relative', width: 1100, height: 400 }}>
        <Box style={{ position: 'absolute', left: 0, top: 360, width: 1100, height: 1, background: '#B3B3B3' }} />
        {[
            /* 预计算：scale=6（满刻度50→300px）；每柱 left = groupL+ti*32；bh/ah 为像素高 */
            { city: '上海', cols: [
                { left: 40, bh: 72, ah: 108 }, { left: 72, bh: 48, ah: 84 }, { left: 104, bh: 30, ah: 54 },
            ]},
            { city: '北京', cols: [
                { left: 215, bh: 60, ah: 90 }, { left: 247, bh: 42, ah: 72 }, { left: 279, bh: 24, ah: 48 },
            ]},
            { city: '深圳', cols: [
                { left: 390, bh: 84, ah: 120 }, { left: 422, bh: 54, ah: 66 }, { left: 454, bh: 36, ah: 42 },
            ]},
            { city: '广州', cols: [
                { left: 565, bh: 48, ah: 72 }, { left: 597, bh: 36, ah: 60 }, { left: 629, bh: 18, ah: 36 },
            ]},
            { city: '杭州', cols: [
                { left: 740, bh: 42, ah: 84 }, { left: 772, bh: 30, ah: 54 }, { left: 804, bh: 12, ah: 30 },
            ]},
            { city: '成都', cols: [
                { left: 915, bh: 36, ah: 66 }, { left: 947, bh: 24, ah: 48 }, { left: 979, bh: 12, ah: 24 },
            ]},
        ].map((g, gi) => (
            <Box key={gi}>
                {g.cols.map((c, ti) => (
                    <Box key={ti}>
                        <Box style={{ position: 'absolute', left: c.left, top: 360 - c.bh - c.ah, width: 28, height: c.ah, background: '#00A9F4' }} />
                        <Box style={{ position: 'absolute', left: c.left, top: 360 - c.bh, width: 28, height: c.bh, background: '#051C2C' }} />
                    </Box>
                ))}
                <Box style={{ position: 'absolute', left: g.cols[0].left, top: 370, width: 96, alignItems: 'center' }}>
                    <Text style={{ fontFamily: '楷体', fontSize: 16, color: '#191919' }}>{g.city}</Text>
                </Box>
            </Box>
        ))}
        <Box style={{ position: 'absolute', left: 40, top: 0, flexDirection: 'row', gap: 12 }}>
            {['轿车', 'SUV', 'MPV'].map((t, i) => (
                <Text key={i} style={{ fontFamily: '楷体', fontSize: 14, color: '#7D7E81', width: 32, textAlign: 'center' }}>{t}</Text>
            ))}
        </Box>
    </Box>
</Box>
```

改数据：`bh = round(基期×scale)`，`ah = round(增量×scale)`，`top` 由基线 360 回推；组内三柱 `left` 步长 32。

---

## 9. 圆环（手绘，中心 KPI）

锚点 PNG（可选校对）：`../exemplars/12-donut.png`。**默认照抄改数据**；多图/条目数异常时可按节首「几何怎么调」改尺寸。

**用途**：3–5 块构成 + 中心一个主 KPI。优先手绘 svg（一致、无 Office 装饰）；
**不要默认走原生 doughnutChart**。

**几何**：环外径 280、内径 160（中心空给 KPI）；右侧图例列。弧用多段 `<path>` 近似或等分 `<circle>` stroke-dasharray。

```jsx
<Box style={{ position: 'absolute', top: 166, left: 56, width: 1168, height: 480, flexDirection: 'row', gap: 48 }}>
    <Box style={{ width: 420, height: 420, position: 'relative' }}>
        <svg width={420} height={420} viewBox='0 0 420 420'>
            {/* 圆周长 ≈ 2*π*110 = 691；按占比切 strokeDasharray */}
            <circle cx='210' cy='210' r='110' fill='none' stroke='#E6E6E6' strokeWidth='44' />
            <circle cx='210' cy='210' r='110' fill='none' stroke='#051C2C' strokeWidth='44'
                    strokeDasharray='276 691' strokeDashoffset='0'
                    transform='rotate(-90 210 210)' />
            <circle cx='210' cy='210' r='110' fill='none' stroke='#00A9F4' strokeWidth='44'
                    strokeDasharray='173 691' strokeDashoffset='-276'
                    transform='rotate(-90 210 210)' />
            <circle cx='210' cy='210' r='110' fill='none' stroke='#027AB1' strokeWidth='44'
                    strokeDasharray='138 691' strokeDashoffset='-449'
                    transform='rotate(-90 210 210)' />
            <circle cx='210' cy='210' r='110' fill='none' stroke='#AAE6F0' strokeWidth='44'
                    strokeDasharray='104 691' strokeDashoffset='-587'
                    transform='rotate(-90 210 210)' />
        </svg>
        <Box style={{ position: 'absolute', left: 110, top: 160, width: 200, alignItems: 'center' }}>
            <Text style={{ fontFamily: 'Arial', fontSize: 48, fontWeight: 'bold', color: '#051C2C' }}>40%</Text>
            <Text style={{ fontFamily: '楷体', fontSize: 18, color: '#7D7E81', marginTop: 6 }}>最大块占比</Text>
        </Box>
    </Box>
    <Box style={{ width: 600, justifyContent: 'center', gap: 18 }}>
        {[
            { c: '#051C2C', n: '乘用车', v: '40%', d: '仍是基本盘' },
            { c: '#00A9F4', n: '商用车', v: '25%', d: '增速最快' },
            { c: '#027AB1', n: '两轮', v: '20%', d: '下沉市场' },
            { c: '#AAE6F0', n: '其他', v: '15%', d: '含出口改装' },
        ].map((r, i) => (
            <Box key={i} style={{ flexDirection: 'row', alignItems: 'center', gap: 14, flexShrink: 0 }}>
                <Box style={{ width: 18, height: 18, background: r.c, flexShrink: 0 }} />
                <Box style={{ width: 100, flexShrink: 0 }}>
                    <Text style={{ fontFamily: '楷体', fontSize: 20, fontWeight: 'bold', color: '#191919' }}>{r.n}</Text>
                </Box>
                <Box style={{ width: 70, flexShrink: 0 }}>
                    <Text style={{ fontFamily: 'Arial', fontSize: 22, fontWeight: 'bold', color: '#051C2C' }}>{r.v}</Text>
                </Box>
                <Text style={{ fontFamily: '楷体', fontSize: 18, color: '#7D7E81' }}>{r.d}</Text>
            </Box>
        ))}
    </Box>
</Box>
```

改占比时：`strokeDasharray='弧长 691'`，下一段 `strokeDashoffset` = 前段累计弧长取负。弧长 = 占比/100 × 691。
块数 3–5；只高亮中心 KPI 对应的那一块（用 `#051C2C`）。

---

## 附录：语料里不存在的两种图

以下两种在 2020+ 全语料里出现 **0 次**。保留片段只为兼容既有需求，
**主决策表里已移除，不要主动选用**。若确实需要，色值须按新色板改写。

### A. Mekko 市场份额块图

列宽 = 细分占比，块高 = 该厂份额。**各列的块高之和必须相等**，否则底边不齐立刻露馅。
块间用 2px 白色 `borderRight` / `borderBottom` 做缝。同一家公司在所有列中必须同色。
配色用 `#051C2C` / `#027AB1` / `#00A9F4` / `#AAE6F0` 四档，浅底块（`#00A9F4` 及更浅）里的
百分比必须用 `#191919` 深色字，否则对比度不足 4.5:1。

### B. 漏斗 Funnel

梯形上宽下窄，每层高 96、层间留 4px 缝，第 n 层的上边宽 = 第 n−1 层的下边宽。
色阶 `#051C2C` → `#034B6F` → `#027AB1` → `#00A9F4` → `#AAE6F0`，
最浅两层（`#00A9F4` 及更浅）的文字必须换成 `#051C2C`，否则白字看不见。
右侧配各环节转化率，卡点那条用 `#051C2C` 左边框与深色数字（**没有暖色可用了**）。
