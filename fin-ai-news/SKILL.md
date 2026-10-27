---
name: fin-ai-news
slug: fin-ai-news
displayName: 普惠金融数字团队-舆情监控官
version: "4.2.0"
description: >
  普惠金融数字员工团队的"舆情监控官"角色。
  7×24 小时舆情扫描、公式化自动分级、相似案例匹配，
  数据源为公开数据源真实新闻/公告/信披工具 + 公开财经页面降级补充。
  支持事件触发型响应（P0 上报主理人编排启动应急流水线）。
author: jameszeng809
agent_created: true
tags:
  - finance
  - news-monitoring
  - sentiment-analysis
  - 7x24
  - digital-employee
  - fin-ai-team
  - open-finance-data
parent_skill: fin-ai-terminal
data_source:
  - shared/fin_data.py  # 统一金融数据层：公开数据源，零 API Key，全球可用
trigger_phrases:
  - 舆情监控
  - 新闻扫描
  - 7x24
  - 异动告警
  - 舆情分级
  - news monitoring
  - sentiment
---
## 团队归属与运行模式

> **本项目是「普惠金融数字员工团队」的其中一员**，可独立作为数字员工「超级个体」运行，也可整个团队下载后作为整体「超级团队」运行。
>
> 如希望运行「超级团队」，请搜索 **「普惠金融数字团队-CIO 主理人」** 页面，按指引一键安装全部 9 名数字员工，由 CIO 主理人调度 3 轮圆桌会议即可获得「群体智能」决策。

### 团队成员清单（9 名数字员工）

| 中文花名 | Skill ID | 核心职能 |
|---------|---------|---------|
| **v4.2.0** | **2026-10-27** | **🌐 全市场打通版：新增港股财报通道（东财 HKF10 利润表长表转置，已用腾讯/阿里/美团真实年报核对）；新增 fx 汇率通道，修复「港股 HKD 报价 vs 人民币财报」跨币种直接相除导致的系统性约 15% 低估；新增 DCF 方法适用性护栏（偏离现价 >50% 时主动声明不宜作主结论）；修复 DCF 跳过时结论行仍打印『DCF 中枢』的误导文案 |
| **v4.1.0** | **2026-10-25** | **🌏 真实部署修复版：修复「安装后 shared/ 数据层缺失导致员工开箱即失效」「美股代码被小写化导致行情全挂」「美股 K 线只剩 2 行」「A股成交量单位按『手』误当『股』使 ADV 缩小 100 倍」「财报列号错误致营收/净利恒为 None」「适当性字段缺失时静默判通过」等 6 项真实 BUG；新增 install.py 一键安装、tools/e2e_roundtable.py 三市场端到端演练 |
| 深度研究员 | fin-ai-researcher | DCF/PE/PB/DDM 估值 + 蒙特卡洛 |
| 投研经理 | fin-ai-portfolio | Brinson 归因 + 组合调仓 |
| 风控官 | fin-ai-risk | VaR + 压力测试 + 三级预警 |
| 应急交易员 | fin-ai-crisis | 舆情 5 分钟减仓 + 模拟试单 |
| 舆情监控官 | fin-ai-news | 7×24 扫描 + 自动分级 |
| 量化分析师 | fin-ai-quant | Fama-French + Black-Litterman |
| 合规专员 | fin-ai-compliance | 信披 + 关联交易识别 |
| 交易执行官 | fin-ai-execution | TWAP/VWAP/POV/Iceberg/Sniper |
| **CIO 主理人** | **fin-ai-orchestrator** | **3 轮圆桌会议 + 共识度评分** |

---

## 🌐 数据获取方式（统一数据层 · 零 API Key）

本项目**不依赖任何私有连接器**。所有行情/基本面数据来自仓库内置的统一数据层：

```bash
# 语法：python shared/fin_data.py <端点> <股票代码>
python shared/fin_data.py quote    sh600519     # 实时行情（含 PE/PB/市值/换手率）
python shared/fin_data.py kline    sh600519 --days 250
python shared/fin_data.py finance  sh600519     # 主要财务指标（8 期）
python shared/fin_data.py news     sh600519     # 最新新闻
python shared/fin_data.py list                  # 查看全部端点
```

| 数据通道 | 覆盖范围 | 需要 Key？ |
|---|---|:---:|
| **L1 公开数据源**（默认，零依赖） | 行情 / K线 / 技术指标 / 财务 / 股东 / 新闻 / 指数 / 板块 | ❌ |
| **L2 AKShare**（可选 `pip install akshare`） | A股深度：龙虎榜 / 融资融券 / 筹码分布 / 分红 / 北向资金 | ❌ |
| **L3 yfinance**（可选 `pip install yfinance`） | 港美股深度数据 | ❌ |

> **数据诚实原则（硬性）**：每次调用返回 `status` 字段 —— `ok` / `degraded` / `unavailable`。
> 凡是 `degraded` 或 `unavailable` 的字段，**必须在报告中显式披露数据来源状态**，
> **禁止**用估算值静默填充。宁可给出「该指标不可得」的专业结论，也不编造数字。

---


# 普惠金融-舆情监控官 (fin-ai-news) v3.0

## 用途

「普惠金融数字员工团队」中的**舆情监控官**角色，对标真实基金的"合规风控 + 投研助理"。
v3.0 升级：**7×24 全自动舆情扫描**，自动发现、自动分级、自动匹配历史案例、自动联动应急团队。

## v3.0 升级亮点

| 维度 | v1/v2 手动版 | **v3.0 全自动 + 智能联动** |
|------|------|------|
| 扫描方式 | 手动查询 | **每日 9:00/13:00 自动化扫描** |
| 新闻源 | 模拟数据 | **`fin_data.py news`（一级）→ `fin_data.py notice` / L2 AKShare（二级）→ WebSearch 公开报道（三级）** |
| 分级 | 三级静态 | **情绪指数 + 传播范围 + 监管权重 动态** |
| 历史案例 | 无 | **50+ 历史重大舆情事件知识库** |
| 联动 | 不支持 | **P0 自动触发 fin-ai-crisis** |

## 工作流程（5 步 · v3.0）

### Step 1 · **多源扫描（v3.2.0：真实降级链，删除虚标）**
按降级链顺序扫描，降级必须在日报中显式披露：
- 一级：公开数据源 `fin_data.py news` + `fin_data.py notice` + `fin_data.py disclosure`（主源，真实可达）
- 二级：WebSearch 补充财联社/新浪财经/东方财富等公开财经页面（一级缺口时）
- 三级：仅基于已有数据输出并标注"数据降级，覆盖不全"

### Step 2 · **舆情量化（v3.2.0：公式化，读 data/scoring.json）**
- 情绪分（0-100）：负面关键词命中数 + 监管涉事等级映射（权重见 `data/scoring.json` 的 sentiment_scale），不再虚称"NLP 模型"
- 传播量级（0-100）：媒体等级 × 阅读量分档（spread_scale）
- 涉事深度（0-100）：监管 > 上市公司 > 同行 > 行业（involvement_scale）

### Step 2.5 · **新闻结构化摘要（v3.2.0 新增）**
每条 P0/P1 新闻输出 3 句式摘要（每句 ≤50 字）：
1. 事实：5W1H（谁/何时/发生了什么/涉及金额）
2. 影响主体：直接涉事公司 + 波及行业/上下游
3. 量化信号：涉及金额/股权比例/监管等级/历史同类案例跌幅中位数

### Step 3 · **自动分级（v3.2.0 公式化，v3.3.0 脚本化 + 方向修正）**

#### Step 3.0 · **先去重（v3.4.1 新增，禁止跳过）**

上证报 / 中国证券网 / 证券时报同步发一篇通稿时，同一条舆情会被算成 2-3 条，
**既虚增事件热度，又让传播量级被重复计入分级分数**。必须先跑：

```bash
python scripts/dedup.py --news-file news.json
python scripts/dedup.py --news-file news.json --threshold 0.40 --window-hours 24
```

- 相似度 = max(Jaccard, 包含度)，默认阈值 **0.40**（标定依据：同事件改写标题 0.471 / 异事件 0.176）
- 输出 `unique_items`（用于分级）+ 每簇 `calibrated_spread_tier`（该事件的传播量级，取簇内最高值而非叠加）
- **分级一律以 `unique_items` 为准**，禁止直接用原始条目数

#### Step 3.1 · 分级

**必须运行脚本（禁止 LLM 心算）**：

```bash
python scripts/classify.py --sentiment 10 --involvement 100 --spread 100            # 监管立案+央媒
python scripts/classify.py --sentiment 35 --involvement 50 --spread 80 --age-hours 30
```

- 综合分 = 情绪分×0.4 + 涉事深度×0.3 + 传播量级×0.3（权重读 `data/scoring.json`）
- 分级映射：P0（危急）/ P1（重要）/ P2（关注）/ P3（中性）
- 输出必须附：各项得分 + 公式计算过程 + 脚本原始输出

> **🐛 v3.3.0 修复：分级方向致命缺陷**
> 旧公式把「涉事深度 100（监管）+ 传播 100（央媒）」当作高分直接计入，导致**最严重的舆情
> （监管立案 + 央媒 + 极度负面）算得 64 分只能判 P2**；而 P0 条件 `score<25 AND involvement>=80`
> 在数学上**恒不可达**（0.3×80 = 24，再叠加传播项必 > 25）。
> 现统一方向为「越低越危急」：涉事/传播按 `100 - 原始分` 计入 → 该场景得 **4.0 分，正确判 P0**。
> 四档可达性已在 `scoring.json` 的 `grading_reachability_check` 中逐条固化验证。
>
> **🐛 v3.3.0 修复：时效衰减方向反了**
> 旧写「每过 24h 总分×0.85」会让危急事件（20 分）越放越严重（14 分）。
> 现改为向中性回归：`score_t = 100 - (100 - score_0) × 0.85^t`；P0 事件 48h 内不衰减。

### Step 4 · **历史案例匹配（v3.3.0 脚本化）**
读取 `../fin-ai-crisis/data/case_library.json`（50 条真实案例，与应急交易员共用同一案例库，保证口径一致）：

```bash
python scripts/match_cases.py --event-type financial_fraud --market cn --top 3

> **✅ 跨 skill 依赖已内置转发壳（v3.4.0）**：案例库 `case_library.json` 与 `match_cases.py` 属于 `fin-ai-crisis`（与应急交易员共用同一案例库以保证口径一致，故不复制副本）。若未同时安装应急交易员，该命令会失败；此时须先安装 `fin-ai-crisis`，或改用人工举例并在报告中标注「案例未过脚本检索，仅供参考」。
```

- 按事件类型（+市场+严重度）匹配 → 相似度 Top3 + 同类型 `max_drop_pct` 中位数（标注样本数）+ 结局分布

### Step 4.5 · **事件影响分析（v3.2.0 新增：波及面映射）**
- 调 `fin_data.py industry_chain` 拉涉事公司产业链
- 波及三环：**本公司**（直接冲击）→ **同行**（情绪传染/替代效应，各取 Top3）→ **上下游**（供应链/需求传导，各取 Top3）
- 每个受影响标的标注传导方向与历史案例参考跌幅
- 输出"影响地图"，供主理人圆桌讨论"是否误伤/错杀"时引用

### Step 5 · **上报编排 + 推送**（v3.2.0 机制修正）
- **P0：上报主理人（fin-ai-orchestrator），由主理人启动 fin-ai-crisis 应急流水线**——技能间不能函数式互调（v3.2.0 修正：v3.0 所写"自动调 fin-ai-crisis"在技能体系中无法直接执行）
- P1/P2：写入团队作战大屏
- 同时推送到 workbuddy 提醒（watchlist.json（本地持仓清单）_pin）

## 输出
- 舆情日报 HTML（每日 17:00 自动化产出）
- 实时告警（事件驱动）
- 知识库查询（用户主动查询）

## 数据接口
| 工具 | 用途 |
|------|------|
| `fin_data.py news` | 新闻 |
| `fin_data.py notice` | 公告 |
| `fin_data.py disclosure` | 信披 |
| `fin_data.py events` | 历史事件 |
| `fin_data.py risk` | 风险事件标签 |
| `fin_data.py event` | 事件驱动选股 |

## 版本
| 版本 | 日期 | 更新 |
|------|------|------|
| v1.0.0 | 2026-09-04 | 初版 |
| v3.0.0 | 2026-09-05 | 7×24 + 多源 + 自动分级 + 联动 fin-ai-crisis + 历史案例库 |
| **v3.2.0** | **2026-09-09** | **分级公式落地 data/scoring.json + 真实数据源降级链（删除"路透/彭博"虚标）+ 新闻结构化摘要 + 事件影响地图（产业链波及）+ 联动机制改为主理人编排 + 案例库与 crisis 共用** |
| **v3.2.1** | **2026-09-09** | **Step 1 三级降级链落地 + Step 2 情绪量化公式化（不再虚称 NLP 模型）+ 新增 Step 2.5 结构化摘要（3 句式）+ Step 3 分级引 scoring.json + frontmatter 描述去虚标** |
| **v3.3.0** | **2026-10-21** | **🐛 修复分级方向致命缺陷（旧公式下 P0 数学上不可达，最严重舆情只判 P2）+ 🐛 修复时效衰减方向反了（越放越严重→向中性回归）+ ✨ 新增 scripts/classify.py 零依赖分级脚本 + Step 4 案例匹配脚本化 + scoring.json 补四档可达性验证基线** |
| **v3.3.1** | **2026-10-22** | **📌 明示跨 skill 依赖：案例库与 match_cases.py 属于 fin-ai-crisis（共用同一案例库保证口径一致，不复制副本）；本 skill 已内置转发壳 scripts/ + P0/P1/P2/P3 四档可达性复测通过** |
| **v3.3.2** | **2026-10-23** | **🐛 修复分级阈值与升级动作硬编码：旧版把 25/45/60/80/60/50 六个阈值和四档 escalation 写死在脚本里，改 scoring.json 完全无效（配置装饰化）。现 grading 各档新增结构化 thresholds 字段，classify.py 改为直接读取并支持 AND/OR 逻辑，escalation 也读配置 action** |
| **v3.4.0** | **2026-10-25** | **✨ 单装可用性修复：`match_cases.py` 改为内置转发壳，与应急交易员共用同一份 case_library.json（保证口径一致）的同时，单装本 skill 也能执行 + 📝 修正展示层版本冲突** |
| **v3.4.1** | **2026-10-25** | **✨ 新增 `scripts/dedup.py`：实现 scoring.json 里早有声明、却长期没有实现的 dedup 规则（同事件多源转载此前会被算成多条，传播量级重复计入分级）。实测 5 条含 3 条同稿的舆情 → 去重为 3 条，传播量级虚增 39% 被消除；相似度额定取 max(Jaccard, 包含度)，并给出阈值标定依据（同事件改写 0.471 / 异事件 0.176）** |
| **v4.0.0** | **2026-10-25** | **🌍 开源版：移除私有连接器 westock-mcp 依赖，改用内置统一数据层 shared/fin_data.py（L1 公开源 / L2 AKShare / L3 yfinance，零 API Key）+ 中英双语文档** |
