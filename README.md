# 🌍 普惠金融数字员工团队 · FinAI Digital Workforce

> **9 个 AI 数字员工组成一支投研团队**——不是 9 个孤立工具，而是一支会**开会、互相质疑、投票、弃权、最后由 CIO 拍板**的智能体队伍。
>
> **Nine AI digital employees running as ONE investment committee** — they debate, cross-examine, vote, abstain, and escalate to a CIO arbiter.

<p align="center">
  <img alt="License" src="https://img.shields.io/badge/License-MIT-green.svg">
  <img alt="Python" src="https://img.shields.io/badge/Python-3.8+-blue.svg">
  <img alt="Digital Employees" src="https://img.shields.io/badge/Digital%20Employees-9-orange.svg">
  <img alt="API Key" src="https://img.shields.io/badge/API%20Key-None%20required-brightgreen.svg">
  <img alt="Award" src="https://img.shields.io/badge/2026%20Tencent%20Cloud%20Hackathon-Global%202nd%20Prize-red.svg">
</p>

<p align="center">
  <b>🏆 2026 腾讯云黑客松 AI 智能体争霸赛 · 全球二等奖</b><br>
  <b>🏆 2026 Tencent Cloud Hackathon — AI Agent Competition, Global 2nd Prize</b><br>
  <i>受邀于腾讯全球数字生态大会展示 · Showcased at Tencent Global Digital Ecosystem Summit</i>
</p>

[English README / 英文版 →](README_EN.md)

---

## 🧠 核心不是 9 个工具，是「群体智能」 Collective Intelligence

大多数 Agent 项目把多个角色平铺输出，各说各话，结果就是**一堆平行报告**。
我们解决的是**如何让 9 个 Agent 真正像一个投委会那样协作**。

Most agent projects simply aggregate parallel reports from several roles. We asked a harder question:
**how can nine agents genuinely behave like an investment committee?**

### 五个关键机制 / Five Mechanisms That Make It Work

| # | 机制 Mechanism | 中文说明 | What it does (EN) |
|:--:|---|---|---|
| 1 | 🪑 **圆桌讨论 Roundtable** | CIO 主理人召集 3 轮会议：独立陈述 → 交叉质疑 → 收敛定案 | Three rounds: independent briefs → cross-examination → convergence |
| 2 | ⚔️ **对抗式交叉质疑 Adversarial Review** | 风控官有权**否决**研究员估值；合规专员能否决整笔交易；量化分析师负责校准两者的模型假设 | Risk officer can veto the researcher's valuation; compliance can veto the trade; quant audits both models' assumptions |
| 3 | 🖐️ **弃权权 Right to Abstain** | 任一员工数据不足时可 `abstain: true` 弃权——**沉默的好过编造的**；弃权必须写明原因，且主理人要降级采信 | Any employee may abstain when data is insufficient. An honest abstention outranks a fabricated number |
| 4 | 📊 **共识度评分 Consensus Scoring** | 主理人对 9 份意见做加权汇总，输出 `consensus_score`；低共识时自动降级为"观察名单"而非强行给结论 | Weighted aggregation produces a consensus score; low consensus auto-downgrades to "watchlist" instead of forcing a call |
| 5 | 📦 **统一数据契约 Shared Data Contract** | 所有员工上报 `team_package.json`（同一 schema），让协作**可编程、可回放、可审计**，而不是靠自然语言互相理解 | Every employee emits the same JSON contract, making collaboration machine-checkable and replayable |

> **一句话总结**：单个员工负责"专业深度"，主理人负责"组织智商"。
> Individual employees own **depth**; the orchestrator owns **organizational IQ**.

### 群体智能运行流 / How a decision flows

```mermaid
flowchart TB
    U([👤 用户提问<br/>User prompt]) --> CIO

    subgraph CIO[" 🎼 CIO 主理人 fin-ai-orchestrator · Conductor "]
      R1["第 1 轮 · 独立陈述<br/>Round 1: independent briefs"]
      R2["第 2 轮 · 交叉质疑<br/>Round 2: cross-examination"]
      R3["第 3 轮 · 收敛裁决<br/>Round 3: convergence & verdict"]
      R1 --> R2 --> R3
    end

    CIO -->|调度令 Dispatch| E1[🔬 深度研究员<br/>Researcher]
    CIO -->|调度令 Dispatch| E2[💼 投研经理<br/>Portfolio Manager]
    CIO -->|调度令 Dispatch| E3[🛡️ 风控官<br/>Risk Officer]
    CIO -->|调度令 Dispatch| E4[🚨 应急交易员<br/>Crisis Trader]
    CIO -->|调度令 Dispatch| E5[📡 舆情监控官<br/>News Monitor]
    CIO -->|调度令 Dispatch| E6[📈 量化分析师<br/>Quant Analyst]
    CIO -->|调度令 Dispatch| E7[⚖️ 合规专员<br/>Compliance Officer]
    CIO -->|调度令 Dispatch| E8[🎯 交易执行官<br/>Execution Trader]

    E1 -.->|team_package.json| R2
    E2 -.->|team_package.json| R2
    E3 -.->|❌ 可否决 veto| R2
    E4 -.->|team_package.json| R2
    E5 -.->|team_package.json| R2
    E6 -.->|❌ 可否决 veto| R2
    E7 -.->|❌ 可否决 veto| R2
    E8 -.->|team_package.json| R2

    R3 --> OUT([📋 作战方案 + 圆桌纪要 + 共识度评分<br/>Battle plan + Roundtable minutes + Consensus score])
```

---

## 👥 9 名数字员工 / Meet the Team

| 花名 · Role | 目录 · Directory | 核心能力 · Superpower | 关键算法/规则 · Core Method |
|---|---|---|---|
| 🎼 **CIO 主理人**<br/>CIO Orchestrator | `fin-ai-orchestrator/` | 3 轮圆桌会议、任务路由、加权裁决、共识度评分 | Consensus engine + veto arbitration |
| 🔬 **深度研究员**<br/>Deep Researcher | `fin-ai-researcher/` | 单股深度研究、多方法估值、敏感性分析 | DCF / PE / PB / DDM + 蒙特卡洛 (10k, seed 42) |
| 💼 **投研经理**<br/>Portfolio Manager | `fin-ai-portfolio/` | 组合全局视图、业绩归因、调仓建议 | Brinson 三因子归因 + 资产配置分析 |
| 🛡️ **风控官**<br/>Risk Officer | `fin-ai-risk/` | 组合风险扫描、极端情景推演、三级预警 | VaR (历史/参数) + 压力测试 + 相关性矩阵 |
| 🚨 **应急交易员**<br/>Crisis Trader | `fin-ai-crisis/` | **5 分钟**突发事件处置：分级→匹配案例→减仓 | 舆情分级 + 历史案例库匹配 + 一键模拟试单 |
| 📡 **舆情监控官**<br/>News Monitor | `fin-ai-news/` | 7×24 扫描、自动分级、相似历史案情比对 | 情绪×传播×监管 三维打分 + 案例库检索 |
| 📈 **量化分析师**<br/>Quant Analyst | `fin-ai-quant/` | 因子归因、组合优化、模型假设校准 | Fama-French + Black-Litterman + Markowitz |
| ⚖️ **合规专员**<br/>Compliance Officer | `fin-ai-compliance/` | 信披合规、关联交易识别、投资者保护 | 规则驱动 `rules.json`（含法条号）+ 审计日志 |
| 🎯 **交易执行官**<br/>Execution Trader | `fin-ai-execution/` | 算法下单、冲击成本测算、模拟撮合 | TWAP / VWAP / POV / Iceberg / Sniper |

> 每名员工既可**单兵作战**（单独安装），也可加入团队接受主理人调度。
> Each employee works **standalone** or joins the team under the orchestrator.

---

## ⚡ 快速开始 / Quick Start

```bash
git clone https://github.com/jameszeng809/fin-ai-workforce.git
cd fin-ai-workforce

# 无需 pip install 即可使用数据层（零依赖）
python shared/fin_data.py quote sh600519        # 实时行情 realtime quote
python shared/fin_data.py kline sh600519 --days 250
python shared/fin_data.py finance sh600519      # 财务指标 financials
python shared/fin_data.py list                  # 全部端点 all endpoints
```

### 安装到你的 Agent（关键：必须用安装脚本）

**不要直接把单个员工目录复制进 skills 目录。** 每个 `SKILL.md` 都要求执行
`python shared/fin_data.py …`，而 `shared/` 位于仓库根目录——单独复制一个员工过去，
它的文档路径并不存在，员工会在第一次取数时直接挂掉（v4.0.0 的实际缺陷，v4.1.0 已修）。

```bash
python install.py                 # 自动识别 ~/.workbuddy/skills、~/.codebuddy/skills 等
python install.py --target <dir>  # 指定目录
python install.py --json          # 机器可读输出
python install.py --uninstall     # 卸载
```

安装器会把 9 名员工装到同一父目录，并为**每一名员工植入 `shared/` 数据层**，
安装后自动逐项校验（SKILL.md / 数据层 / 脚本数），任何一项缺失会直接报 BROKEN。

```text
employee              SKILL.md   data layer  scripts
--------------------------------------------------------
fin-ai-compliance     True       True        1
fin-ai-crisis         True       True        3
…                                            …
run: python <skills>/fin-ai-compliance/shared/fin_data.py quote sh600519
```

Need more control? `python install.py --only fin-ai-risk,fin-ai-quant` installs a
subset; the whole team still lands under one parent so cross-skill delegation
(`portfolio/backtest` → `quant/backtest`, `crisis/classify` → `news/classify`)
keeps working.

English: **do not copy a single employee folder into your skills directory** —
each `SKILL.md` calls `shared/fin_data.py`, which lives at the repo root.
`install.py` plants the shared data layer into every employee it installs.

### 端到端演练 / End-to-end roundtable

一次性把 9 名员工跑通同一个真实标的（A股/港股/美股均可），全部取数真实、全部指标由脚本计算：

```bash
python tools/e2e_roundtable.py --symbol sh600519
python tools/e2e_roundtable.py --symbol usTSLA --json
python tools/selfcheck.py                     # 全仓自检 self-check
```

```text
[PASS] researcher · DCF 估值     每股 1287.86 CNY（基数：2025-12-31 归母净利 823.2亿CNY…）
[PASS] quant · 马科维茨(自动最小方差)  mode=markowitz_min_variance infeasible=False
[PASS] risk · VaR / CVaR         VaR95(1d)=0.0227 CVaR99=0.0361
[PASS] execution · 冲击成本/拆单   参与率=0.0069 冲击=3.8bps 建议=Sniper
[PASS] consensus · 共识度        0.863 / 不确定性=low / 未决分歧=1
演练结论：17/17 项通过
```

**可选增强（均无需 API Key）：**

```bash
pip install -r requirements.txt      # akshare (A股深度) + yfinance (港美股) + matplotlib (图表)
```

---

## 🔌 数据源：为什么这里没有 API Key / Data Layer

本团队**不依赖任何私有数据连接器**。`shared/fin_data.py` 是一个统一数据层，内置三级通道：

| 通道 Tier | 覆盖范围 Coverage | 依赖 Requirement | 需要 Key？ |
|---|---|---|:--:|
| **L1 公开数据源** | 行情 / K线 / 技术指标 / 财务 / 股东 / 新闻 / 指数 / 板块 | 无（Python 标准库） | ❌ |
| **L2 AKShare** | A股深度：龙虎榜 / 融资融券 / 筹码分布 / 分红 / 北向资金 | `pip install akshare` | ❌ |
| **L3 yfinance** | 港美股深度数据 | `pip install yfinance` | ❌ |

```python
from shared import fin_data
r = fin_data.call("quote", "hk00700")
# {'status': 'ok', 'source': 'L1:eastmoney', 'data': {...}, ...}
```

### 🛡️ 数据诚实原则 — 本项目的底线 / Honesty Contract

每一次数据调用都返回 `status`：`ok` / `degraded` / `unavailable`。
凡 `degraded` 或 `unavailable` 的字段，**必须在报告中显式披露**，禁止用估算值静默填充。

Every call returns `status`. Anything that is not `ok` **must be surfaced in the report** — never silently backfilled.

> *宁可给出"该方法不适用"的专业结论，也不用一个数学上成立、经济上荒谬的假设编出精确到小数点的目标价。*
> *We would rather publish "this method does not apply" than produce a precise-looking target price built on absurd assumptions.*

这条原则在研究员身上真实发生过：贵州茅台回归 β = **-0.20**、R² = **0.033**，导致 WACC ≈ 0.55% < 永续增长率 g = 3%。我们没有修数字，而是让 `dcf.py` 触发**护栏模式**并在报告中声明"DCF 因 β 异常不适用，主结论改用相对估值"。
Real case: Kweichow Moutai regressed to β = **-0.20**, R² = **0.033** → WACC ≈ 0.55% < g = 3%. The DCF script raised a guardrail and the report switched to relative valuation instead of faking a number.

---

## 📁 目录结构 / Repository Layout

```
fin-ai-workforce/
├── fin-ai-orchestrator/     🎼 CIO 主理人（含全队共用的数据契约 schema）
├── fin-ai-researcher/       🔬 深度研究员
├── fin-ai-portfolio/        💼 投研经理
├── fin-ai-risk/             🛡️ 风控官
├── fin-ai-crisis/           🚨 应急交易员
├── fin-ai-news/             📡 舆情监控官
├── fin-ai-quant/            📈 量化分析师
├── fin-ai-compliance/       ⚖️ 合规专员
├── fin-ai-execution/        🎯 交易执行官
├── shared/                  🌐 统一数据层 fin_data.py（零依赖核心）
├── install.py               📦 一键安装器（为每名员工植入 shared/ 数据层）
├── templates/               📄 持仓清单等模板
├── tools/                   🛠️ 自检 & 迁移脚本
│   ├── selfcheck.py             全仓自检（81 项：结构/脚本/JSON/数据层冒烟）
│   ├── migrate_to_open_data.py  去掉私有连接器的一键改造脚本
│   ├── e2e_roundtable.py        9 员工端到端圆桌演练（支持 A股/港股/美股）
│   └── bump_version.py          版本号与变更日志统一维护
└── docs/                    📚 群体智能设计说明
```

每个员工目录内含：`SKILL.md`（角色定义与流水线）· `scripts/`（纯标准库计算脚本）· `data/`（本地规则库）· `README.md`（中英介绍）。

> **为什么所有计算脚本只用标准库？**
> 旧版脚本依赖 numpy，在未安装的开箱环境直接 `ModuleNotFoundError`，导致"禁止 LLM 心算、必须跑脚本"的流水线整体断裂。现在全部改为**纯 Python 标准库**，任何 Python 3.8+ 环境开箱即用。

---

## 🧪 实战修复记录 / Bugs found by actually installing and running it

v4.1.0 不是文档更新，是把 9 名员工**真的装进 Agent、真的跑真实数据**之后修出来的。下面每一条都在生产链路里复现过：

| # | 症状 Symptom | 根因 Root cause | 修复 Fix |
|---|---|---|---|
| 1 | 员工安装后第一次取数就报 `can't open file '…/shared/fin_data.py'` | `shared/` 在仓库根，单独复制员工目录时不会被带过去 | 新增 `install.py`，安装时把数据层植入每一名员工并逐项校验 |
| 2 | 美股（特斯拉/苹果）行情全部返回空 | `tx_symbol()` 把整个代码小写成 `ustsla`，而腾讯 GBK 返回的键是 `v_usTSLA` | 只把市场前缀小写，ticker 保留原大小写 |
| 3 | 美股 K 线只返回 2 行（2011 年一条 + 最新一条） | 腾讯对无交易所后缀的美股只给残缺数据 | 自动尝试 `usTSLA.OQ` 等后缀，并列 Nasdaq 做兜底通道 |
| 4 | 交易执行官把**每一笔**茅台订单判为"超过单日成交额" | 腾讯/东财 A 股成交量单位是「手」（100 股），被当成「股」用，ADV 缩小 100 倍 | 数据层统一归一并输出 `shares` / `amount` / `volume_unit` |
| 5 | 财报接口 `营收`/`归母净利` 恒为 `null` | 代码用了美式列名 `TOTAL_OPERATE_INCOME`，东财真实列名是 `TOTALOPERATEREVE` | 按东财真实列名重取，并新增美股 Nasdaq 财报通道 |
| 6 | C1 保守型投资者买 R4 产品，合规报告显示"0 项适当性违规" | 画像字段名不匹配时 SU 规则段被静默跳过，变成假阴性 | 字段别名容错 + `su_skip_reason` 强制显式标注"适当性未校验" |

v4.2.0 继续把三个市场全部跑通，又挖出四条：

| # | 症状 Symptom | 根因 Root cause | 修复 Fix |
|---|---|---|---|
| 7 | 港股 DCF 做不出来，`finance` 返回 `no financial record for 00700.HK` | 港股财报走的是另一张接口（`RPT_HKF10_FN_INCOME`）且是**长表**（一科目一行），与 A 股宽表完全不同 | 新增港股通道：按报告期转置成长表→宽表，优先取年报（`DATE_TYPE_CODE=001`） |
| 8 | 腾讯 DCF 每股价值比现价低约 15%，且**不报任何错** | 港股**以 HKD 报价、却以人民币披露财报**，直接相除等于跨币种比较 | 新增 `fx` 汇率端点（ECB 参考汇率），DCF 显式换算并把汇率写进结论；汇率取不到则拒绝出数 |
| 9 | 特斯拉 DCF 给出每股 \$18.83，而现价 \$391.62，看着像坏了 | 用净利润替代自由现金流的简化 DCF，本就不适用于高成长标的 | 新增**方法适用性护栏**：偏离现价 >50% 时主动声明"本方法不宜作主结论，宜改用相对/分部估值" |
| 10 | 财报不可得时，报告末尾仍打印"DCF 中枢 ¥385.2" | 跳过分支把 `base` 回退成了现价，但结论文案没跟着变 | 跳过时改打印"DCF 已跳过（原因）"，绝不把现价包装成估值 |

> 第 4、6、8 条属于**静默错误**——不报错、给个错得离谱的结果。这也是本项目
> "宁可 unavailable，不用估算值静默填充"原则的反面教材。
> Items 4, 6 and 8 were *silent* failures: no exception, just a confidently wrong number.

---

## 🎤 路演亮点 / Demo Highlights

| 亮点 | 看点 |
|---|---|
| 🎼 **现场跑圆桌会议** | 输入一个问题，看 9 个员工现场开会、互相否决、CIO 加权裁决 |
| 🖐️ **看 AI 主动弃权** | 数据不足时明确说"我不发表意见"，而不是硬凑结论 |
| 💰 **β 异常触发护栏** | 展示"宁可承认模型不适用，也不编目标价"的专业克制 |
| 🎯 **从研究到下单闭环** | 研究员给估值 → 风控官给仓位上限 → 交易执行官拆单，全程数据契约贯通 |
| 🌐 **零 Key 全球可跑** | 任何人 clone 下来就能拉到真实行情，不需要注册任何账号 |

---

## 📜 开源协议 / License

[MIT License](LICENSE) © 2026 jameszeng809

## ⚠️ 免责声明 / Disclaimer

本项目输出**仅供参考，不构成任何投资建议**。所有计算结果基于公开数据，含合理假设；
历史业绩不代表未来表现；任何投资决策均由使用者自行判断。
This project is for research and education only. It is **not investment advice**. Use at your own discretion.

---

<p align="center">
  <i>如果这个项目对你有启发，点个 ⭐ Star 让更多人看到群体智能的可能。</i><br>
  <i>If this sparks something, drop a ⭐ — it helps others discover what collective agents can do.</i>
</p>
