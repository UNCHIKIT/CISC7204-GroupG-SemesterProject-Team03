# 介绍视频讲稿 · 5 分钟
**CISC7204 Data Science and Data Visualization · Class G — Team 03**
**The Power-Hungry World: Comparing Global Electricity Consumption Across Sectors**
汇报人：HE YIFEI (Zephyr) · MC664916 · 2026/2027, Semester 1

---

## 怎么用这份稿子

- 12 页对 12 段，**每段就是一个镜头**：一页录一遍，剪的时候按页切。
- 台词是**逐字稿**，可以直接念；加粗的词落重音，`（停）`处停半拍。
- 全稿实测 **683 词**，按 145–150 词/分钟念完约 **4:40**，加上换页停顿正好在 5:00 以内。下表每段的时长是**上限**，不是配额，念完早了就早点切页。
- 视频上限 5 分钟是硬线，**目标录到 4:45**，留剪辑余量。

| 页 | 段落 | 时长 | 累计 | 中文一句话 |
|---|---|---|---|---|
| 1 | 开场 | 0:15 | 0:15 | 我是谁、讲什么 |
| 2 | 团队 | 0:20 | 0:35 | 六个人、一人一责 |
| 3 | 选题起点 | 0:30 | 1:05 | 一个数字说明不了问题 |
| 4 | 研究问题 | 0:30 | 1:35 | 一个问题拆成三块 |
| 5 | 数据 | 0:35 | 2:10 | 三个公开源互补 |
| 6 | 方法 | 0:30 | 2:40 | 六步管线 |
| 7 | 产出 | 0:20 | 3:00 | 四图 + 看板 + notebook |
| 8 | 要解决的问题 | 0:45 | 3:45 | 五个坑，五个对策 |
| 9 | 验收标准 | 0:20 | 4:05 | 九项检查 |
| 10 | 分工 | 0:20 | 4:25 | 每项检查都有主 |
| 11 | 时间线 | 0:25 | 4:50 | 四周到 12/3 |
| 12 | 收尾 | 0:10 | 5:00 | 仓库 + 致谢 |

---

## 1 · 封面 —— 0:15

> Hi, I'm Zephyr — He Yifei — from Class G, Team 03. In the next five minutes I'll introduce our semester project: **The Power-Hungry World** — comparing global electricity consumption across sectors.

*镜头：正视镜头，语速正常，微笑。*

---

## 2 · 团队 —— 0:20

> We're six, and every role has **exactly one owner**. Un Chi Kit coordinates the project and tracks the deadlines. Kelden Jamtsho leads the analysis and reviews every number. Gan Ruiyan builds the pipeline. Sheng Tian builds the visualisations. Tang Jing keeps the minutes. And I handle the report, this video, and contact with the instructor.

*镜头：手指从左到右扫过六个名字，念到谁停一下。*

---

## 3 · 选题起点 —— 0:30

> Start with one number. In 2022 the world consumed about **24,700 terawatt-hours** of electricity — 88,859 petajoules in the IEA's data, divided by 3.6. Electricity is the **fastest-moving** part of the world energy system, and yet public debate reduces it to that single figure. The figure is correct. It's also useless on its own. It can't tell you which regions grew, which countries hold the shares, or whether industry or households drove the demand. So we replace one number with a **decomposition**.

*镜头：念到 24,700 时手停在大数字上；最后一句放慢。*

---

## 4 · 研究问题 —— 0:30

> That gives us one question, with three measurable parts. **How has electricity consumption changed across the world's countries and regions between 1990 and 2022, and which countries and sectors account for the largest shares of that consumption?** （停）
> Change over time: growth rates, and an index set to a hundred in 1990. Country shares: who holds the world total, and how the ranking moved. Sector shares: industry, transport, residential, and services. All three come out of **one harmonised table**.

*镜头：念问题的时候看着屏幕，念三个子问题时依次点 01 / 02 / 03。*

---

## 5 · 数据 —— 0:35

> Three public sources, each covering the others' gaps. The **IEA World Energy Balances** give sector detail and regional totals — but the licence forbids redistributing the file. The **UN Energy Balance** dataflow gives all 218 countries and territories, without aggregates. **Our World in Data** adds the generation mix, and because it downloads in one request, it becomes our reproducibility anchor. Three units become one: terawatt-hours, where one TWh is 3.6 petajoules.

*镜头：三张卡片依次指一下；最后一句是重点，别赶。*

---

## 6 · 方法 —— 0:30

> Six steps. Freeze the three raw files with a dated manifest. Harmonise them — country spellings, unit conversion, four sector groups, and the estimate flag carried through. Then one analysis per sub-question. Then validate: nine checks, four figures, a dashboard, and a notebook that reproduces every number. Window, unit and sector groups are **fixed before the first figure is drawn**.

*镜头：沿 01→06 的横线扫一遍，节奏均匀，一句一步。*

---

## 7 · 产出 —— 0:20

> What comes out: a regional trend, a country-share shift, a sector-share comparison, and — kept deliberately separate, because generation is not consumption — the fuel mix. Plus an interactive dashboard, and the notebook behind it.

*镜头：说到"generation is not consumption"时指一下第 4 张卡。*

---

## 8 · 五个要解决的问题 —— 0:45

> Now the honest part: five problems we have to solve before December.
> **One** — the sources disagree on the same country. China by nine per cent, Indonesia by twenty-three. We report both, and never merge them silently.
> **Two** — sector reporting is uneven: UN transport is reported for 98 of 218 areas in 2022, so a rising trend may simply mean more countries reported.
> **Three** — later years carry more estimates, 17.3 per cent in 2022, so key results are re-run without them.
> **Four** — the IEA licence blocks replication, so we ship a derived extract, and anchor reproduction on Our World in Data.
> **Five** — country names don't join cleanly, and a missing row is **not a zero**. Both get explicit rules.

*镜头：这是全场最值钱的一段，语速放慢，"One… Two… Three…"要有节奏感。*

---

## 9 · 验收标准 —— 0:20

> Nine checks decide whether the work is good enough: data quality, reproducibility, the arithmetic, figure clarity, citations and licences, the brief itself, reporting bias, estimate sensitivity, and traceability — every sentence tied back to a number. All nine run **before** submission, not after.

*镜头：九项一口气念完，最后一句加重。*

---

## 10 · 分工 —— 0:20

> And every check has an owner. Kelden signs off the numbers. Gan owns the pipeline and the dashboard. Sheng owns the figures. Tang keeps the minutes. Un Chi Kit coordinates, and ticks off each individual submission by name. I own the narrative and this video.

*镜头：快、干脆，不逐字解释。*

---

## 11 · 时间线 —— 0:25

> Week one: data frozen and harmonised. Week two: the time series and the country shares. Week three: sector shares and the generation mix. Week four: the report, the dashboard, the rehearsal, and a final validation pass. The project is submitted on 3 December; the collaboration record follows on the 5th.

*镜头：跟着橙色的条从左往右走。*

---

## 12 · 收尾 —— 0:10

> Everything is in one repository: the code, the instructions and a derived extract of the data, so anyone can re-run our analysis and check every number. Thank you. Happy to take questions.

*镜头：回到正视镜头，笑一下再结束录制（留 2 秒尾巴给剪辑）。*

---

## 备用：30 秒版（万一被砍时长，或用在海报/晚宴介绍）

> Our project is **The Power-Hungry World**. We take one headline number — the world used about 24,700 terawatt-hours of electricity in 2022 — and break it down by region, by country and by sector, from 1990 to 2022. Three public sources, one harmonised table, four figures. The interesting part isn't the total. It's what the decomposition shows: where the growth happened, and how much of it is measured rather than estimated.

---

## 超时了删哪几句（按顺序删，删到 4:45 就停）

1. 第 3 段删「Electricity is the fastest-moving part of the world energy system, and yet public debate…」整句（−20 词）
2. 第 6 段删「Window, unit and sector groups are fixed before the first figure is drawn.」（−14 词）
3. 第 9 段把九项并成五组：*data quality, reproducibility, the arithmetic, the figures and citations, and traceability*（−8 词）
4. 第 10 段删「Tang keeps the minutes.」（−4 词）
5. 第 5 段最后一句改成「Everything is converted to terawatt-hours.」（−8 词）

> 反过来，如果念完还不到 4:30（说明你偏快），就在第 2 段加一句「That's all six of us — names and student IDs are on screen.」，第 3 段念完停一拍再说「So we replace one number with a decomposition.」

## 发音小抄

| 词 | 读法 |
|---|---|
| petajoules / terajoules | **PET**-uh-joolz / **TEH**-ruh-joolz（不是"焦耳"） |
| terawatt-hours | **TEH**-ruh-wot **OW**-erz |
| IEA | eye-ee-**AY**（三个字母分开念） |
| Our World in Data | 全称念，不要念成"OWID" |
| Czechia | **CHEK**-ee-uh |
| UN Statistics Division | 连读成 "you-en statistics division" |
| 24,700 | twenty-four thousand seven hundred（不要念成"二四七零零"） |
| 1.09 / 0.77 | one point oh nine / zero point seven seven |

## 录制小建议

- **一页一镜**：每页单独录，念错只重录那一段，不重录整条。
- **眼神**：第 2、10、12 页看镜头；第 3–9 页看屏幕（观众会觉得你在讲图）。
- **节奏**：每段之间停 0.5 秒再切页，剪辑时好下刀。
- **音量**：手机离嘴 20–30 cm，房间里挂条毛巾降混响。
- **剪辑**：页与页之间用硬切，不要花哨转场；结尾留 2 秒黑场。
- 导出 **MP4 / H.264 / 1080p**，时长务必 ≤ 5:00。

## 可能被问到的 5 个问题（30 秒版）

**Q1 为什么是 1990–2022？**
UN 序列从 1990 年才有；2023 年的估算值比例跳到 20.9%，放在结论里会误导，所以截止到 2022。

**Q2 为什么不用 IEA 一个源就够了？**
IEA 只覆盖 54 个国家 + 10 个聚合体，撑不起"全球"；UN 有 218 个国家地区但没有区域聚合。两个源互补，OWID 负责可复现。

**Q3 两个源数字不一样，你们信谁？**
都不"信"，同时报。差异量化成比值（中国 1.09、印尼 0.77），在图上并列呈现，并在限制里写明——不做静默合并。

**Q4 这是因果分析吗？**
不是。数据是观测性的，没有价格、政策、天气变量。我们只描述格局与变化，最多说"与人口/GDP 增长一致"，不说"导致"。

**Q5 为什么不研究数据中心 / 加密货币挖矿？**
这一组数据源里没有任何一个单独报告它们，硬做就只能猜。已明确写在 out of scope。
