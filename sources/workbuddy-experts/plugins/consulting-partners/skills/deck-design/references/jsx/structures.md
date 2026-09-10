# 咨询结构图 JSX 片段库：六种核心框架图

`tencent-pptx` 的 `design-principle.mck-consulting.md` 描述了 12 个信息结构图子版式，但**只有文字规格、
没有任何代码**——agent 每次都要从零手画，方差极大。本文件把其中咨询交付最常用、最容易画错的六种
做成成品片段：Issue Tree、**战略房屋**、**分层价值链**、实施甘特、横向阶段条、**泳道架构**。

**最该先看 §2 战略房屋**：**「目标—路径」关系用 §2**，即结论呈「1 个总目标 + 3–5 条并列路径
+ 一层共同支撑」时；它是建议 / 举措章节的收口图，边界与反例见该节节首。
其次是**流程 / 价值链类，占语料 20%，是第二大图型**：
**层级堆叠关系用 §3，先后工序关系用 §5，多角色并行协作 / 触点×中台用 §6 泳道**。

共同规范（来自它的 ⑨ 节，必须遵守）：
- **文图分离**：形状层用 `<svg>` 或 `<Box>`，**所有文字必须是独立的可编辑文本元素**，
  禁止把字烤进 SVG path。烤进去的字无法编辑、不受字号体系管控、投影会糊。
- 线条只用直线或直角折线，禁曲线连接。主框架 1–2px，分支 0.5–1px。
- 结构图应占内容区 ≥70%，标题必须陈述结构图的**结论**，不是"XX 框架"。
- 节点标题 21–24px Bold，说明 15–18px，标签 14–15px。

**取用**：按 `../exemplars/README.md` 打开本文件对应节；**agent 默认不 Read PNG**。
默认只改数据与文案；**一页多图、层数/支柱数变化时可按比例改宽高与间距**，但须守坐标系铁律、
内容区 166–646、色板白名单，改完跑 `slidep-validate` + `jsx_lint.py`。房屋五层高度预算改一层要从别层扣回来。

## ⚠️ 坐标系铁律（手画结构图第一大坑，实测已致溢出）

`position: 'absolute'` 的 `left/top` **相对「直接父元素」，不是整页**。

⚠️ **这里和 CSS 不一样，实测四组用例确认**：引擎走 Yoga 语义，定位基准就是直接父元素，
**父元素有没有 `position` 完全无关**。实测：一个未定位的静态父级被 `marginTop:100` 推下去，
它里面 `top:0` 的绝对定位子节点也跟着落在 100px 处（若按 CSS 的"最近已定位祖先"应落在 0）。
这条差异会引出一个致命坑：**`bottom`/`right` 要求直接父元素在该轴上尺寸确定**，
不确定时该轴按 0 算、元素被静默锚到容器**起始边**并朝画布外生长。
最常见的两种"不确定"是 `.map` 里那层无样式 `<Box key={i}>` 和"只写了 width 没写 height"的容器。
**所以结构图一律用 `top`/`left` 正向定位，不要用 `bottom`/`right`。**
九组实测矩阵见 `../../SKILL.md` 已知坑 4。

所以：

- **外层定位容器只管把图放到页面哪里**（`position:'absolute', top:168, left:56, width:1168, height:472`）；
- **容器内所有子节点一律用局部坐标**，取值范围就是 `0…width` / `0…height`，
  **绝不能写整页坐标，更不能把容器的 top/left 再加一遍**。

写成 `top: 196 + p.y`（而容器 top 已经是 188）就是把偏移加了两遍，元素被推到页面外——
实测报 `❌ overflow [bottom] … Bottom+32px`。同理 `left: 110 + p.x` 配 `left:110` 的容器也是错的。

**为什么特别容易错**：结构图常在同一个容器里混用 `<svg>` 和 `<Box>`。
`<svg>` 的 `x1/y1/cx/cy` 由 `viewBox` 决定，**永远是局部坐标**；
如果 `<Box>` 子节点写成整页坐标，两套坐标系就整整错开一个容器偏移量——
连线端点和节点框对不上，而且底部节点会掉出画布。

**正确骨架**（本文件所有片段都是这个写法，照抄即可）：

```jsx
<Box style={{ position: 'absolute', top: 168, left: 56, width: 1168, height: 472 }}>
  <svg width='1168' height='472' viewBox='0 0 1168 472'>
    <line x1='584' y1='232' x2='584' y2='47' stroke='#B3B3B3' strokeWidth='1' />
  </svg>
  {/* 节点框：局部坐标，圆心/端点与上面 SVG 的 (584,47) 对齐 */}
  <Box style={{ position: 'absolute', left: 479, top: 5, width: 210, height: 84 }}>…</Box>
</Box>
```

### ❌ 别这样"修"：把容器挪到原点

发现节点掉出画布后，最容易想到的补救是把外层容器改成 `top:0, left:0, width:1280, height:720`，
让整页坐标重新生效。**这是错的，而且错得更隐蔽**：节点框确实落对了位置，
但**内嵌的 `<svg>` 也跟着回到了页面原点**，于是连线整体往左上移了一个原容器偏移量——
连线接不上任何节点，图明显歪掉。更糟的是 `slidep-validate` 此时返回 `success:true`
（没有任何东西超出画布），`gate_check` 的布局重叠项也管不到（连线没有文字）。

```jsx
// ❌ 容器移到原点：节点框对了，svg 里的连线整体偏移 (56,168)，全部接不上
<Box style={{ position: 'absolute', top: 0, left: 0, width: 1280, height: 720 }}>
  <svg width='1168' height='472' style={{ position: 'absolute', top: 0, left: 0 }}>
    <line x1='584' y1='232' x2='584' y2='47' />   {/* 端点在页面 (584,232) */}
  </svg>
  <Box style={{ position: 'absolute', left: 535, top: 173, width: 210, height: 84 }}>…</Box>
  {/* ↑ 框中心在页面 (640,215)，与端点差 (56,168) —— 正是原容器的 left/top */}
</Box>

// ✅ 保留容器，节点框改局部坐标：端点与框中心重合
<Box style={{ position: 'absolute', top: 168, left: 56, width: 1168, height: 472 }}>
  <svg width='1168' height='472' viewBox='0 0 1168 472'>
    <line x1='584' y1='232' x2='584' y2='47' />
  </svg>
  <Box style={{ position: 'absolute', left: 479, top: 5, width: 210, height: 84 }}>…</Box>
  {/* ↑ 框中心 (584,47) = 连线上端点，对齐 */}
</Box>
```

**最省事的做法是根本不用 `<svg>` 画连线**：本文件所有片段的连线都是 1–2px 的 `<Box>` 细条
（如 `<Box style={{position:'absolute', left:200, top:212, width:60, height:1}} />`），
它与节点框同处一个坐标空间，**不可能失步**。只有需要斜线时才用 `<svg>`，
此时务必让 svg 与容器**等尺寸、零偏移**。

**动笔即可自检，不用等渲图**：

- 容器内最大的 `top + height` 必须 ≤ 容器 `height`；换算到页面就是
  `容器top + 容器height ≤ 660`（页脚线）；
- 每条连线的端点必须落在某个节点框的矩形内——对不上就是坐标空间错了。

这两条都能机读，写完当页就跑：

```bash
${NODE_BIN_DIR}/slidep-validate slides/NN.slide --project .   # 查掉出画布
python3 ../../scripts/jsx_lint.py slides/NN.slide             # 查连线脱节
```

---

## 1. Issue Tree 问题树（MECE 拆解）

**用途**：把一个大问题拆成互斥穷尽的几支，并标出每支的量级贡献。**必须从左向右展开**——
从上向下展开的是组织架构图，不是问题树。

**几何**：核心问题框 200×84 居左；干线从核心框右缘伸出 60px，再竖向贯通所有分支；
每个分支横线 48px 接到节点框左缘。分支框 320×88，纵向间距 104（本例末支间距 92 以收紧）。
绘图区高度 436 = 末支 `top` 348 + 框高 88，**声明值必须等于内容实际到达的位置**——
写小了 `jsx_lint.py` 会报容器内溢出（这处原先写 420，差 16px 已修正）。
关键分支用 `2px solid #2251FF` 边框 + `#EFEFF0` 浅底，非关键用 `1px solid #B3B3B3` + 白底。

```jsx
<Box style={{ position: 'absolute', top: 172, left: 56, width: 1168, height: 478 }}>
    <Box style={{ position: 'relative', width: 1168, height: 436 }}>
        <Box style={{ position: 'absolute', left: 0, top: 170, width: 200, height: 84, background: '#051C2C', padding: 12, justifyContent: 'center' }}>
            <Text style={{ fontFamily: '楷体', fontSize: 22, fontWeight: 'bold', color: '#FFFFFF', lineHeight: 1.3 }}>
                毛利率两年<br />下滑 6.4pp
            </Text>
        </Box>

        <Box style={{ position: 'absolute', left: 200, top: 212, width: 60, height: 1, background: '#051C2C' }} />
        <Box style={{ position: 'absolute', left: 260, top: 48, width: 1, height: 328, background: '#051C2C' }} />

        {[
            { top: 48, name: '售价下行', val: '-3.1pp', desc: '入门级跟随行业降价，均价两年降 11%', key: true },
            { top: 152, name: '料本上升', val: '-2.2pp', desc: '关键芯片与稀土涨价，单机料本升 8%', key: true },
            { top: 256, name: '产能利用率', val: '-0.7pp', desc: '新厂爬坡期折旧未被产量摊薄', key: false },
            { top: 348, name: '结构变化', val: '-0.4pp', desc: '高毛利定制占比由 7% 降至 5%', key: false },
        ].map((b, i) => (
            <Box key={i}>
                <Box style={{ position: 'absolute', left: 260, top: b.top + 32, width: 48, height: 1, background: '#051C2C' }} />
                <Box style={{
                    position: 'absolute', left: 308, top: b.top, width: 320, height: 88,
                    border: b.key ? '2px solid #2251FF' : '1px solid #B3B3B3',
                    background: b.key ? '#EFEFF0' : '#FFFFFF',
                    paddingLeft: 14, paddingRight: 14, justifyContent: 'center',
                }}>
                    <Box style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
                        <Text style={{ fontFamily: '楷体', fontSize: 22, fontWeight: 'bold', color: '#051C2C' }}>{b.name}</Text>
                        <Text style={{ fontFamily: 'Arial', fontSize: 22, fontWeight: 'bold', color: b.key ? '#061F79' : '#7D7E81' }}>{b.val}</Text>
                    </Box>
                    <Text style={{ fontFamily: '楷体', fontSize: 16, color: '#191919', lineHeight: 1.35, marginTop: 4 }}>{b.desc}</Text>
                </Box>
            </Box>
        ))}

        <Box style={{ position: 'absolute', left: 680, top: 48, width: 380, height: 212, background: '#E6E6E6', padding: 22, justifyContent: 'center' }}>
            <Text style={{ fontFamily: '楷体', fontSize: 24, fontWeight: 'bold', color: '#051C2C', lineHeight: 1.3 }}>
                两支合计 -5.3pp
            </Text>
            <Text style={{ fontFamily: '楷体', fontSize: 22, color: '#191919', lineHeight: 1.45, marginTop: 10 }}>
                占总降幅 82%。改善动作应全部投向售价与料本，产能与结构两支可暂不干预。
            </Text>
        </Box>

        <Box style={{ position: 'absolute', left: 680, top: 288, width: 380 }}>
            <Text style={{ fontFamily: '楷体', fontSize: 16, color: '#7D7E81', lineHeight: 1.5 }}>
                MECE 校验 ✓ 四支互斥且穷尽，加总 -6.4pp 与财报口径一致
            </Text>
        </Box>
    </Box>
</Box>
```

**字数预算**：分支说明在 320px 框内、16px 字号下约 18 字/行，两行共 ≤34 字，超了会溢出框底。
右侧结论卡 380px 宽、22px 字号约 15 字/行，212px 高约容 4 行正文。

---

## 2. 战略房屋（五层框架）

**用途**：把一整套战略压进一页，回答三件事——**要去哪、靠哪几条路径去、底下要有什么托着**。
它是建议章节的收口图，通常放在正式提出方案的那一页，让人一眼看到全貌与主次。

**五层各装什么**（自上而下，Navy 由深到浅）：

| 层 | 装什么 | 写法 |
|---|---|---|
| ① 屋顶（三角） | **使命 / 愿景**：最终要成为什么 | 1–2 行，通常不带数字 |
| ② 第一横梁 | **战略目标**：可量化的终点 | 1 行，**必须带数字与时点** |
| ③ 支柱（3–5 根） | **战略支柱**：达成目标的几条并列路径 | 标题 ≤8 字 + 说明 ≤40 字 |
| ④ 第二横梁 | **战略举措**：支柱落下来的具体动作 | 横铺列编号，每条 ≤10 字 |
| ⑤ 地基 | **赋能因素**：几根支柱共用的底座 | 4–6 项平铺 |

**什么时候用**：结论呈「**1 个总目标 + 3–5 条并列路径 + 一层共同支撑**」这个形状时。
判据是**支柱之间平级无先后、且共用同一套底座**——有底座才是房子。

**什么时候不用**：

| 情形 | 该用什么 |
|---|---|
| 几条事项平级、彼此无关、也没有共同底座 | 三 / 四栏卡片 |
| 有明确先后工序 | §5 横向阶段条 |
| 是技术栈 / 能力的堆叠关系，不是「目标—路径」 | §3 分层价值链 |
| 是在拆解问题原因，不是在给方案 | §1 Issue Tree |

**举例**（下方代码即这一例，某工业仿真软件公司、下游为储能行业）：

| 层 | 本例内容 |
|---|---|
| 屋顶 | 成为中国储能系统的效率标准 |
| 目标 | 2028 年营收翻倍至 240 亿，EBITDA 率提升 4pp |
| 三支柱 | 中端场景优先 / 验证资产积累 / 交付能力前置 |
| 举措 | ① 中端产品线重构 ② 头部客户联合验证 ③ 交付标准化 ④ 渠道伙伴体系 |
| 地基 | 算例数据资产平台、行业工程师培养、与高校联合标准、客户成功体系 |

**这一例为什么立得住**：三根支柱是可以同时推进的三条独立路径（不是三个阶段），
而地基那四项**每根支柱都要用**——「算例数据资产平台」既支撑"验证资产积累"、也支撑"交付能力前置"。
**反过来，如果地基里的某项只服务于一根支柱，那它就不是地基，这页也不该画成房子。**

Navy 阶由屋顶最深到地基最浅。必须保持房屋轮廓，不能画成"五层蛋糕"（即屋顶必须是三角）。

**高度预算（这是最容易翻车的地方）**：内容区从 168 起、须在 646 前结束，可用 478px。
五层加间距必须精确配平：`56(屋顶) + 4 + 52(目标梁) + 12 + 234(支柱) + 12 + 42(举措梁) + 4 + 62(地基) = 478`。
改任何一层的高度都要从别层扣回来。

**支柱文案硬预算**：支柱框宽 `(912 − 24) / 3 = 296`，减 padding 36 后内宽 260px，22px 字号约 11 字/行；
可用文本高 143px ÷ 32px 行高 = 4 行 → **说明 ≤40 字**。超过就会被框底切掉，
正解是精简文案（它的规范也要求"精简文案而非缩小字号"）。

```jsx
<Box style={{ position: 'absolute', top: 168, left: 184, width: 912 }}>
    <Box style={{ position: 'relative', width: 912, height: 56 }}>
        <svg width={912} height={56} viewBox='0 0 912 56'>
            <path d='M456 0 L912 56 L0 56 Z' fill='#051C2C' />
        </svg>
        <Box style={{ position: 'absolute', left: 206, top: 20, width: 500, alignItems: 'center' }}>
            <Text style={{ fontFamily: '楷体', fontSize: 20, fontWeight: 'bold', color: '#FFFFFF' }}>
                使命：成为中国储能系统的效率标准
            </Text>
        </Box>
    </Box>

    <Box style={{ width: 912, height: 52, background: '#034B6F', alignItems: 'center', justifyContent: 'center', marginTop: 4 }}>
        <Text style={{ fontFamily: '楷体', fontSize: 24, fontWeight: 'bold', color: '#FFFFFF' }}>
            战略目标：2028 年营收翻倍至 240 亿，EBITDA 率提升 4pp
        </Text>
    </Box>

    <Box style={{ flexDirection: 'row', gap: 12, marginTop: 12 }}>
        {[
            { t: '中端场景优先', d: '放弃高端对标，预算集中投向占市场 73% 的中端场景。' },
            { t: '验证资产积累', d: '以免费迁移验证换取算例授权，积累 200 套可复用算例。' },
            { t: '交付能力前置', d: '沉淀标准实施包，单项目人月从 4.5 压到 2.0。' },
        ].map((p, i) => (
            <Box key={i} style={{ flex: 1, background: '#027AB1', padding: 18, height: 234 }}>
                <Text style={{ fontFamily: '楷体', fontSize: 24, fontWeight: 'bold', color: '#FFFFFF', lineHeight: 1.3 }}>{p.t}</Text>
                <Box style={{ width: 36, height: 2, background: '#FFFFFF', marginTop: 10, marginBottom: 12 }} />
                <Text style={{ fontFamily: '楷体', fontWeight: 'bold', fontSize: 22, color: '#FFFFFF', lineHeight: 1.45 }}>{p.d}</Text>
            </Box>
        ))}
    </Box>

    <Box style={{ width: 912, height: 42, background: '#3C96B4', flexDirection: 'row', alignItems: 'center', justifyContent: 'space-around', marginTop: 12 }}>
        {['① 中端产品线重构', '② 头部客户联合验证', '③ 交付标准化', '④ 渠道伙伴体系'].map((t, i) => (
            <Text key={i} style={{ fontFamily: '楷体', fontSize: 20, fontWeight: 'bold', color: '#051C2C' }}>{t}</Text>
        ))}
    </Box>

    <Box style={{ width: 912, height: 62, background: '#AAE6F0', paddingLeft: 14, paddingRight: 14, paddingTop: 10, paddingBottom: 10, marginTop: 4 }}>
        <Text style={{ fontFamily: '楷体', fontSize: 18, fontWeight: 'bold', color: '#051C2C' }}>赋能因素</Text>
        <Box style={{ flexDirection: 'row', justifyContent: 'space-between', marginTop: 8 }}>
            {['算例数据资产平台', '行业工程师培养', '与高校联合标准', '客户成功体系'].map((t, i) => (
                <Text key={i} style={{ fontFamily: '楷体', fontSize: 18, color: '#191919' }}>{t}</Text>
            ))}
        </Box>
    </Box>
</Box>
```

---

## 3. 分层价值链（原刊形态，占语料 20%，是最常用的结构图）

**2026-08 改版：chevron 箭头链已下架。** 实测《麦肯锡中国季刊》2020+ 语料里
流程 / 价值链类占 20%，是仅次于折线的第二大图型，但它的真实形态**不是首尾相连的箭头**，
而是**分层标签块 + 每层一行说明**：左对齐、深→浅青色阶自上而下、无箭头、无边框、无外框。
原刊范例见 `../exemplars/04-flow-layered.png`（GenAI 特刊图2「支持生成式AI系统的价值链」）。

**为什么换**：chevron 的箭头暗示"必须按顺序流过"，适合工序流程；
而咨询里 80% 的"价值链"其实是**技术栈 / 生态分层 / 能力层级**——它们是堆叠关系不是流转关系，
画成箭头链是语义错误。真要表达工序流转，用 §5 的横向阶段条。

**几何**：容器 `top:166 left:56 width:1168`，五层每层 91px
（标签块 37 + 细线 4 + 说明 28 + 间隙 6 + 层距 16），合计 455px，落在内容区 480px 内。
**层数超过 5 就要把说明压到一行或减层**，六层必然顶破内容区。
说明写成两行时每层再涨 28px，此时最多只能放 4 层。
**不要在容器里再加一行小标题**——那个位置的信息属于 y=121 的口径副行，重复一次就会挤爆预算。

**色阶固定深→浅**，方向代表"由上层应用到底层基础设施"：
`#051C2C` → `#034B6F` → `#027AB1` → `#00A9F4` → `#AAE6F0`。
后两档（`#00A9F4` 及更浅）的标签文字必须换成 `#051C2C`，白字对比度不足。

```jsx
<Box style={{ position: 'absolute', top: 166, left: 56, width: 1168 }}>
    {[
        { n: '服务', c: '#051C2C', t: '#FFFFFF', k: false,
          d: '围绕如何用好求解器提供的实施、培训与调优服务，按人月计价。' },
        { n: '行业验证算例', c: '#034B6F', t: '#FFFFFF', k: true,
          d: '核心卡点：国际厂商单行业超 3,000 套认证算例，国产不足 200 套 [F]。' },
        { n: '前后处理', c: '#027AB1', t: '#FFFFFF', k: false,
          d: '建模与结果可视化工具链，效率约为国际产品的 70%，可通过版本迭代追赶 [I]。' },
        { n: '求解器内核', c: '#00A9F4', t: '#051C2C', k: false,
          d: '主流工况精度差距已收窄至 3% 以内，不再是决策阻碍 [F]。' },
        { n: '基础算力与并行框架', c: '#AAE6F0', t: '#051C2C', k: false,
          d: '依赖通用 HPC 生态，非差异化环节，不建议自建 [A]。' },
    ].map((l, i) => (
        <Box key={i} style={{ marginBottom: 16 }}>
            <Box style={{ flexDirection: 'row', alignItems: 'center', gap: 12 }}>
                <Box style={{
                    background: l.c, flexShrink: 0,
                    paddingLeft: 16, paddingRight: 16, paddingTop: 4, paddingBottom: 4,
                }}>
                    <Text style={{ fontFamily: '楷体', fontSize: 21, fontWeight: 'bold', color: l.t }}>{l.n}</Text>
                </Box>
                {l.k ? (
                    <Box style={{ flexDirection: 'row', alignItems: 'center', gap: 8, flexShrink: 0 }}>
                        <Box style={{ width: 28, height: 2, background: '#2251FF', flexShrink: 0 }} />
                        <Text style={{ fontFamily: '楷体', fontSize: 17, fontWeight: 'bold', color: '#2251FF', flexShrink: 0 }}>核心卡点</Text>
                    </Box>
                ) : null}
            </Box>
            {/* 标签块下压一条同色细线横贯全宽——原刊每层都有，是这个版式的识别特征 */}
            <Box style={{ width: 1168, height: 2, background: l.c, marginTop: 2 }} />
            <Text style={{ fontFamily: '楷体', fontSize: 20, color: '#191919', lineHeight: 1.4, marginTop: 6 }}>{l.d}</Text>
        </Box>
    ))}
</Box>
```

**四条硬规矩**：

1. **标签块宽度由文字撑开，不要写死 `width`**。原刊每层标签宽窄不一，那正是它不像 PPT 模板的原因；
   写死等宽会立刻变回"五层色块蛋糕"。
2. **说明文字必须是完整句子**，不是关键词。每层 25–40 字，超了压缩措辞不要缩字号。
3. **卡点用主蓝短线 + 标注标出**，不要靠改标签块颜色——色阶已经被"层级深浅"占用了，
   再叠一个语义会让读者分不清深色到底表示"底层"还是"有问题"。
4. **说明行 20px 属结构图豁免区间**（`mck-palette.md` §4 允许结构图说明 15–18px，
   这里放宽到 20px 以贴近正文下限）。`gate_check.py` 对 <22px 只报 WARN，不 FAIL。

---

## 4. 实施甘特 / 路线图

**用途**：举措 × 时间的实施计划。左 1/3 举措信息卡，右 2/3 甘特条，里程碑用橙色菱形。

**几何**：左栏 400px（举措 210 / 负责人 96 / KPI 94），右栏 748px 分 4 个时间格各 187px。
行高 96，行间 1px 浅灰分隔。甘特条高 30，`left`/`width` 按时间格换算：`1 个半年 = 187px`。
里程碑菱形 18×18，`left` 减 9 使其居中于时间点。

**易错点**：举措名必须包在固定宽度的 `<Box>` 里才会换行，直接给 `<Text>` 设 `width`
在 row 布局下会溢出压到下一列。

```jsx
<Box style={{ position: 'absolute', top: 172, left: 56, width: 1168, height: 478, flexDirection: 'row' }}>
    <Box style={{ width: 400 }}>
        <Box style={{ height: 44, flexDirection: 'row', borderBottom: '1px solid #B3B3B3', alignItems: 'flex-end', paddingBottom: 6 }}>
            <Text style={{ fontFamily: '楷体', fontSize: 16, fontWeight: 'bold', color: '#7D7E81', width: 210 }}>举措</Text>
            <Text style={{ fontFamily: '楷体', fontSize: 16, fontWeight: 'bold', color: '#7D7E81', width: 96 }}>负责人</Text>
            <Text style={{ fontFamily: '楷体', fontSize: 16, fontWeight: 'bold', color: '#7D7E81', width: 94 }}>关键 KPI</Text>
        </Box>
        {[
            { id: 'A', name: '中端产品线重构', owner: '产品 · 陈', kpi: '功能覆盖 85%' },
            { id: 'B', name: '头部客户联合验证', owner: '行业 · 李', kpi: '算例 200 套' },
            { id: 'C', name: '交付标准化', owner: '交付 · 王', kpi: '人月 ≤2.0' },
            { id: 'D', name: '渠道伙伴体系', owner: '销售 · 赵', kpi: '签约 30 家' },
        ].map((r, i) => (
            <Box key={i} style={{ height: 96, flexDirection: 'row', alignItems: 'center', borderBottom: '1px solid #E6E6E6' }}>
                <Box style={{ flexDirection: 'row', alignItems: 'center', gap: 10, width: 210 }}>
                    <Box style={{ width: 30, height: 30, borderRadius: 15, background: '#051C2C', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                        <Text style={{ fontFamily: 'Arial', fontSize: 17, fontWeight: 'bold', color: '#FFFFFF' }}>{r.id}</Text>
                    </Box>
                    <Box style={{ width: 150 }}>
                        <Text style={{ fontFamily: '楷体', fontSize: 21, fontWeight: 'bold', color: '#051C2C', lineHeight: 1.3 }}>{r.name}</Text>
                    </Box>
                </Box>
                <Box style={{ width: 96 }}>
                    <Text style={{ fontFamily: '楷体', fontSize: 17, color: '#191919', lineHeight: 1.35 }}>{r.owner}</Text>
                </Box>
                <Box style={{ width: 94 }}>
                    <Text style={{ fontFamily: '楷体', fontSize: 17, color: '#191919', lineHeight: 1.35 }}>{r.kpi}</Text>
                </Box>
            </Box>
        ))}
    </Box>

    <Box style={{ flex: 1, paddingLeft: 20 }}>
        <Box style={{ height: 44, flexDirection: 'row', borderBottom: '1px solid #B3B3B3', alignItems: 'flex-end', paddingBottom: 6 }}>
            {['2026 H2', '2027 H1', '2027 H2', '2028 H1'].map((t, i) => (
                <Text key={i} style={{ fontFamily: 'Arial', fontSize: 16, fontWeight: 'bold', color: '#7D7E81', width: 187 }}>{t}</Text>
            ))}
        </Box>
        <Box style={{ position: 'relative', width: 748, height: 384 }}>
            {[187, 374, 561].map((x, i) => (
                <Box key={i} style={{ position: 'absolute', left: x, top: 0, width: 1, height: 384, background: '#E6E6E6' }} />
            ))}
            {[
                { top: 33, left: 0, w: 300, label: '重构 + 灰度发布' },
                { top: 129, left: 150, w: 411, label: '迁移验证 100 → 200 套' },
                { top: 225, left: 280, w: 280, label: '实施包沉淀' },
                { top: 321, left: 430, w: 318, label: '伙伴招募与认证' },
            ].map((b, i) => (
                <Box key={i} style={{ position: 'absolute', left: b.left, top: b.top, width: b.w, height: 30, background: '#2251FF', justifyContent: 'center', paddingLeft: 10 }}>
                    <Text style={{ fontFamily: '楷体', fontWeight: 'bold', fontSize: 17, color: '#FFFFFF' }}>{b.label}</Text>
                </Box>
            ))}
            {[{ top: 129, left: 374 }, { top: 129, left: 561 }].map((m, i) => (
                <Box key={i} style={{ position: 'absolute', left: m.left - 9, top: m.top + 6 }}>
                    <svg width={18} height={18} viewBox='0 0 18 18'>
                        <path d='M9 0 L18 9 L9 18 L0 9 Z' fill='#051C2C' />
                    </svg>
                </Box>
            ))}
            <Box style={{ position: 'absolute', left: 374, top: 100, width: 220 }}>
                <Text style={{ fontFamily: '楷体', fontSize: 16, fontWeight: 'bold', color: '#051C2C' }}>里程碑：100 套 / 200 套</Text>
            </Box>
        </Box>
    </Box>
</Box>
```

---

## 5. 横向阶段条（真有先后工序时用，替代 chevron）

**用途**：确实存在时间/工序先后的流程——审批链、交易流程、实施阶段。
**没有先后关系就别用这个，用 §3**。

**为什么不是箭头**：麦肯锡表达"往前走"靠的是**从左到右的位置本身 + 阶段间一条细连接线**，
不是画一堆箭头。箭头一多，形状密度上去了，信息密度反而下降。

**几何**：四阶段，每段 268px、段距 32px（`268 × 4 + 32 × 3 = 1168`）。
顶部序号行 36、阶段条 56、说明区拉高填满下半（墨水底边 ≥560）。

> 🔴 **连接线铁律**：slidep 会把 absolute 细条画到色块/文字之上。**禁止**画一条贯通全宽的
> `width:1120` 横线——会横切阶段条标题。只在**段与段的 32px 缝里**画短线（宽 ≤32）。

```jsx
<Box style={{ position: 'absolute', top: 166, left: 56, width: 1168, height: 480 }}>
    {/* 只在段缝画连接线：段宽 268 + 起点，线长 = gap 32；top = 序号行 36 + 条高一半 28 = 64 */}
    {[0, 1, 2].map((i) => (
        <Box key={'c'+i} style={{
            position: 'absolute', left: 268 + i * 300, top: 64, width: 32, height: 2, background: '#B3B3B3',
        }} />
    ))}

    <Box style={{ flexDirection: 'row', gap: 32 }}>
        {[
            { i: '01', n: '线索识别', d: '按 ARR 与行业匹配度打分，每季筛出 40 家目标账户。', k: false },
            { i: '02', n: '技术验证', d: '两周 POC，客户自带真实工况，通过率是全流程最低的一环。', k: true },
            { i: '03', n: '商务谈判', d: '标准折扣带 + 三年期条款，平均周期 6 周。', k: false },
            { i: '04', n: '交付与续费', d: '实施包上线后转客户成功团队，续费率 61%。', k: false },
        ].map((s, idx) => (
            <Box key={idx} style={{ width: 268, flexShrink: 0 }}>
                <Box style={{ height: 36, flexDirection: 'row', alignItems: 'center' }}>
                    <Text style={{ fontFamily: 'Arial', fontSize: 18, fontWeight: 'bold', color: '#7D7E81' }}>{s.i}</Text>
                </Box>
                <Box style={{
                    height: 56, background: s.k ? '#051C2C' : '#AAE6F0',
                    alignItems: 'center', justifyContent: 'center',
                }}>
                    <Text style={{ fontFamily: '楷体', fontSize: 22, fontWeight: 'bold', color: s.k ? '#FFFFFF' : '#051C2C' }}>{s.n}</Text>
                </Box>
                <Text style={{ fontFamily: '楷体', fontSize: 20, color: '#191919', lineHeight: 1.45, marginTop: 20 }}>{s.d}</Text>
            </Box>
        ))}
    </Box>
</Box>
```

**只深色高亮一段**（那个卡点/最该看的阶段），其余一律 `#AAE6F0`。
阶段数 3–5 段为宜；6 段以上说明拆得太细，合并或改用甘特（§4）。

---

## 6. 泳道 / 触点架构

锚点 PNG（可选校对）：`../exemplars/05-flow-swimlane.png`。**默认照抄改数据**；层数变化时可按比例改行高。

**用途**：多角色/多系统沿**时间轴**协作（客户旅程 × 触点/模型/后端/数据）。看原刊 `05`：
节点按**从左到右铺满**主区，上下层同一列对齐；**不是**把白芯片全挤在泳道左侧。

**几何**：内容区 1168×480；左标签列 110；主区 1058。5 泳道行高 78、层缝 4，底栏 54。
主区内 **4 列**时间步：每格宽 232，`justifyContent:'space-between'` 拉开（勿用 `gap:12` 左堆）。
空槽用同宽透明占位，保证列对齐。节点块是**实心蓝底 + 白字**（原刊形态），不是白底灰框芯片。

> 🔴 **禁止左堆**：`flex` + 小 `gap`、不定宽芯片 = 全挤左侧。必须固定列宽 + `space-between` / 显式 `left`。
> 🔴 **跨层线**：禁止 absolute 长竖线横切节点（slidep 会盖住字）。列对齐本身表达调用关系；
> 需要 API 示意时只在**层缝空隙**画短竖线。禁止粗 chevron。

```jsx
<Box style={{ position: 'absolute', top: 166, left: 56, width: 1168, height: 480 }}>
    {[
        {
            lane: '客户', tone: '#AAE6F0', box: '#00A9F4',
            slots: ['登录并提出改签', '查看方案', '请求人工坐席', '完成并退出'],
        },
        {
            lane: '互动', tone: '#99E6FF', box: '#027AB1',
            slots: ['激活机器人', '传达方案', '转接坐席', '坐席反馈'],
        },
        {
            lane: '生成式AI', tone: '#00A9F4', box: '#027AB1',
            slots: ['提取诉求', '核政策/约束', '给替代方案', '指派坐席'],
        },
        {
            lane: '后端app', tone: '#027AB1', box: '#034B6F',
            slots: ['登录鉴权', '政策管理', '流程管理', '坐席分配'],
        },
        {
            lane: '数据源', tone: '#034B6F', box: '#051C2C',
            slots: ['客户ID', '历史数据', '政策数据', '坐席数据'],
        },
    ].map((row, ri) => (
        <Box key={ri} style={{ flexDirection: 'row', height: 78, marginBottom: 4, alignItems: 'center' }}>
            <Box style={{ width: 110, flexShrink: 0, paddingRight: 8 }}>
                <Text style={{ fontFamily: '楷体', fontSize: 17, fontWeight: 'bold', color: '#051C2C', flexShrink: 0 }}>{row.lane}</Text>
            </Box>
            <Box style={{
                width: 1058, height: 78, background: row.tone, flexDirection: 'row',
                alignItems: 'center', justifyContent: 'space-between', paddingLeft: 14, paddingRight: 14, flexShrink: 0,
            }}>
                {row.slots.map((it, ii) => (
                    it ? (
                        <Box key={ii} style={{
                            width: 232, height: 52, background: row.box, flexShrink: 0,
                            alignItems: 'center', justifyContent: 'center', paddingLeft: 8, paddingRight: 8,
                        }}>
                            <Text style={{ fontFamily: '楷体', fontSize: 16, fontWeight: 'bold', color: '#FFFFFF', flexShrink: 0 }}>{it}</Text>
                        </Box>
                    ) : (
                        <Box key={ii} style={{ width: 232, height: 52, flexShrink: 0 }} />
                    )
                ))}
            </Box>
        </Box>
    ))}
    {/* 底栏：满宽一条，与原刊「基础设施和计算」一致 */}
    <Box style={{ flexDirection: 'row', height: 54, alignItems: 'center' }}>
        <Box style={{ width: 110, flexShrink: 0, paddingRight: 8 }}>
            <Text style={{ fontFamily: '楷体', fontSize: 17, fontWeight: 'bold', color: '#051C2C', flexShrink: 0 }}>基础设施</Text>
        </Box>
        <Box style={{
            width: 1058, height: 54, background: '#051C2C', flexShrink: 0,
            alignItems: 'center', justifyContent: 'center',
        }}>
            <Text style={{ fontFamily: '楷体', fontSize: 18, fontWeight: 'bold', color: '#AAE6F0', flexShrink: 0 }}>
                云 / 本地基础设施与计算
            </Text>
        </Box>
    </Box>
</Box>
```

改数据时：`slots` 保持 **4 列**（缺步写 `null` 占位）；节点文案 ≤8 字以免溢出 232 宽。
列数改成 3/5 时同步改 `width` 与 `space-between` 视觉密度。层数 4–6。

---

## 其余八个子版式

`design-principle.mck-consulting.md` 的 ⑨ 节还描述了流程图、多支柱网格、组织/利益相关方地图等。
这些用本文件的同一套原语（`<Box>` 矩形 + `<svg>` 连线/箭头 + 独立文本层）直接照它的规格画即可，
没有额外技巧。**唯一必须守住的是文图分离**：任何时候都不要把中文烤进 SVG。
