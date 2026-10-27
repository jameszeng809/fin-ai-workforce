---
name: fin-ai-quant
slug: fin-ai-quant
displayName: 普惠金融数字团队-量化分析师
version: "4.3.0"
description: >
  普惠金融数字员工团队的"量化分析师"角色。
  相关性矩阵、组合优化（Markowitz）、因子暴露分析、量化选股——
  用数学武装基金经理的眼睛。
author: jameszeng809
agent_created: true
tags:
  - finance
  - quantitative
  - markowitz
  - factor-model
  - digital-employee
  - fin-ai-team
  - open-finance-data
parent_skill: fin-ai-terminal
data_source:
  - shared/fin_data.py  # 统一金融数据层：公开数据源，零 API Key，全球可用
trigger_phrases:
  - 量化
  - 相关性
  - 组合优化
  - 因子模型
  - 量化选股
  - quantitative
  - markowitz
---
## 团队归属与运行模式

> **本项目是「普惠金融数字员工团队」的其中一员**，可独立作为数字员工「超级个体」运行，也可整个团队下载后作为整体「超级团队」运行。
>
> 如希望运行「超级团队」，请搜索 **「普惠金融数字团队-CIO 主理人」** 页面，按指引一键安装全部 9 名数字员工，由 CIO 主理人调度 3 轮圆桌会议即可获得「群体智能」决策。

### 团队成员清单（9 名数字员工）

| 中文花名 | Skill ID | 核心职能 |
|---------|---------|---------|
| **v4.3.0** | **2026-10-27** | **🔗 跨员工联动版：修复「量化→风控」链路断裂——公募双十口径下股票池常不满仓，风控官却硬要求权重和为 1，整条流水线直接报错；现为 VaR / 压力测试新增--cash 现金仓位，并要求「权重 + 现金 = 1」，现金按零波动计入，历史情景冲击按权益暴露折算（30% 仓位下 2015 股灾损失由 -42.75% 修正为 -13.5%）；端到端演练改为真实传递组合权重，不再用单资产绕过 |
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


# 普惠金融-量化分析师 (fin-ai-quant) v3.0

## 用途

「普惠金融数字员工团队」中的**量化分析师**角色，对标真实基金的"量化投资部"。
v3.0 升级：**接入公开数据源 60 日 K 线 + 因子排序 + 策略筛选**，让量化模型跑在真实数据上。

## v3.0 升级亮点

| 维度 | v1/v2 模拟版 | **v3.0 真实数据 + 算法库** |
|------|------|------|
| 数据源 | 模拟 K 线 | **data_kline 60/120/250 日真实 K 线** |
| 相关性 | 假数据 | **20×20 真实相关性矩阵** |
| 组合优化 | 单一 Markowitz | **+ Black-Litterman + 风险平价** |
| 因子模型 | CAPM 简化 | **Fama-French 五因子 + 动量** |
| 选股 | 通用筛选 | **fin_data.py sector + fin_data.py hot 真实工具** |

## 工作流程（9 步 · v3.2.0）

### Step 0 · **宏观配置**（v3.2.0 新增：先定股债比，再谈选股）
- 调 `fin_data.py macro` 拉取 GDP 增速 / CPI / 10 年期国债收益率 / 社融与 M2 增速差
- **美林时钟四象限判断**（"经济×通胀"二维）：
  - 复苏（增长↑通胀↓）→ 股 70 / 债 20 / 现金 10
  - 过热（增长↑通胀↑）→ 股 50 / 债 20 / 商品现金 30
  - 滞胀（增长↓通胀↑）→ 股 20 / 债 50 / 现金 30
  - 衰退（增长↓通胀↓）→ 股 30 / 债 60 / 现金 10
- 输出：宏观象限判断 + 依据（引用具体宏观数值）+ 股债现金基准比例
- 该比例作为 Step4 组合优化的总仓位约束（股票部分不得超过该比例）

### Step 0.5 · **行业轮动**（v3.2.0 新增）
- 调 `fin_data.py sector` 拿申万一级行业涨跌排名（近 20 日动量）
- 调 `fin_data.py fund_flow` + `fin_data.py north_holding` 看行业级资金流向
- 输出：**超配 3 行业 / 低配 3 行业**清单，每行业附理由（动量排名 + 资金净流入 + 宏观象限适配度）
- 该清单作为 Step6 选股漏斗的第一层过滤

### Step 1 · 获取真实 K 线
- 调 `fin_data.py kline` 拉 20 只股的 250 日 K 线（不复权）
- 调 `fin_data.py chip` 拉筹码分布
- 输出：真实的"价格 + 成交量 + 换手率"数据集（整理为 CSV 供脚本使用）

### Step 2 · 简化因子代理（v3.2.0 方法论修正，明示局限）
> **v3.2.0 修正说明**：v3.0 所写"Fama-French 五因子 + 60 个月回归"存在两处不严谨——①标准 Fama-French 因子（SMB/HML/RMW/CMA）需**全市场**股票按市值/账面市值比分组构建，仅 20 只成分股无法构建；②"60 个月回归"与实际只有 250 日 K 线矛盾。修正为**简化因子代理**：

因子代理计算（单股票横截面，用 250 日窗口）：
- **市场暴露**：个股 vs 沪深300 的 250 日 β（回归）
- **规模**：流通市值（data_quote）
- **价值**：PE_TTM / PB_TTM 反向得分（data_finance）
- **盈利质量**：ROE 及其稳定性（近 4 季）
- **动量**：过去 12 月-1 月收益率（250 日剔除最近 21 日）

输出：每只股 5 维因子得分 + 与组合均值的偏离。**报告中必须声明**："以上为简化因子代理，非标准 Fama-French 因子；样本仅 20 只股票，统计效力有限，结论供参考。"

### Step 3 · **相关性矩阵 + 协方差**（v3.2.0 脚本化）
- 把 Step1 的收益率整理为 CSV，**必须运行**（禁止手算）
  `python scripts/correlation.py --returns-file returns.csv --labels 茅台,腾讯,宁德,特斯拉 --top-k 5`
  v3.4.1：`--labels` 按 CSV 列序给出资产名，高相关对直接输出股票名而非列下标；不传则回落 ASSET_i 占位符。
- 输出：热力图 + 脚本自动给出的高相关对 Top5 与 >0.85 分散化警告

### Step 4 · **组合优化落地为具体权重**（v3.2.0：从理论曲线到可执行清单）
- **必须运行** `python scripts/optimizer.py --cov-file cov_annual.csv --mode risk_parity` 或 `--mode markowitz --mu-file mu.csv --target-return 0.12`

### Step 4.1 · **单票上限口径与现金解释**（v3.4.1 ★ 现场必答点）

单票上限由 `--policy` 决定，**不再是写死的 10%**：

| 口径 | 单票上限 | 适用 | 依据 |
|------|:---:|------|------|
| `public_fund`（默认） | 10% | 公募基金组合 | PL-01《运作管理办法》第三十二条，红线不可放宽 |
| `discretionary` | 25% | 专户/高端投顾 | 内部风控制度，**报告中必须注明口径** |
| `demo` | 35% | 演示教学 | 报告中必须注明口径 |

```bash
# 法规口径（默认），评估结果 + 现金成因解释 + 达标所需股票池数量
python scripts/optimizer.py --cov-file cov_annual.csv --mode risk_parity
# 专户口径，或自行指定上限并启用现金回填
python scripts/optimizer.py --cov-file cov_annual.csv --mode risk_parity --policy discretionary
python scripts/optimizer.py --cov-file cov_annual.csv --mode risk_parity --max-position 0.20 --cash-cap 0.10
```

> **⚠️ 「为什么六成是现金」——提前解释，不要等观众问**
> 公募口径下 **股票池 N 只 × 单票 10% = 可投上限**。4 只标的 → 上限 40% → 现金必然 60%。
> 这不是优化失败，而是 PL-01 的数学必然。脚本的 `cash_explanation` / `pool_hint` 会自动输出这段，
> 报告首段必须引用；需要低现金时只有两条路：扩大股票池到 ≥9 只，或切换口径。
> **演示技巧：同一组合跑 public_fund 与 discretionary 两遍并列展示**，把「约束」讲成「合规差异化能力」。
- 输出不再停留在"有效前沿曲线"，而是 **20 只股的具体目标权重**
- 约束（脚本内置）：单票 ≤10%（硬夹逼）、权重非负
- **v3.3.0 现金口径修正**：单票 10% 截断后**不再强制归一化回 100%**，被夹掉的份额输出为
  `cash_weight` 归现金（与 fin-ai-risk 硬夹逼"被夹份额归现金、不得回补其他股票"一致）

> **🐛 v3.3.0 修复：股票池 < 10 只时优化器必然失败**
> 旧版 `clip_normalize` 先截断到 10% 再归一化回 100%，当股票池不足 10 只时，
> 归一化后单票必然再次 > 10%，循环 100 次仍不收敛 → 直接报错退出
> （"资产数过少…建议 ≥10 只"），使小股票池场景完全不可用。
> 现改为截断后保留现金：5 只股票也能正常出权重（每只 10%，现金 50%）。
>
> **🐛 v3.3.0 修复：numpy 依赖导致三个脚本全崩** —— correlation.py / optimizer.py / backtest.py
> 均已改为纯标准库实现（自写 Cholesky 无关的高斯消元、样本协方差、分位数），开箱即用。
>
> **✨ v3.3.0 新增**：Markowitz 输出 `target_return_infeasible` 与 `infeasible_note`，
> 当目标收益在数学上不可达时显式告警，禁止把不可达目标当可实现收益展示。
- 总仓位约束：股票部分不得超过 Step0 宏观配置给出的股比
- Black-Litterman：融合 Step0.5 行业轮动观点 + 主理人圆桌观点 → 后验收益 → 重跑 optimizer
- 报告要求：Markowitz 结果必须附 risk_parity 对照（Markowitz 对输入敏感）
- Black-Litterman：
  - 融合历史数据 + 主观观点（主理人圆桌输出）
  - 输出：先验 + 观点 → 后验收益率 → 最优权重

### Step 5 · 风险平价组合
- 算法：每个资产对组合方差的边际贡献相等
- 优点：不需要预测收益率，对输入不敏感
- 适用：稳健型组合

### Step 6 · **量化选股清单**（v3.2.0：三级漏斗 + 三种输入）

**输入三种模式（v3.2.0 新增）**：
1. 用户直接给 20 只股票清单（A股/港股）→ 跳过漏斗第 1 层
2. 用户只给行业名（如"半导体"）→ 漏斗第 1 层自动配出 20 只候选
3. 混合输入 → 缺口部分由漏斗补齐

**三级漏斗**：
- 第 1 层 · 行业过滤：Step 0.5 超配行业内，用 `fin_data.py sector`/`fin_data.py label` 拉全行业候选池
- 第 2 层 · 因子打分：对候选池逐股计算因子得分（估值/质量/动量，权重可配），取 Top 30
- 第 3 层 · 事件过滤：`fin_data.py event` 剔除未来 30 日有解禁>5%、大股东减持中、立案调查等负面事件的标的 → 输出 **20 只候选池 + 每只因子得分明细**

综合调用：`fin_data.py sector` + `fin_data.py sector` + `fin_data.py hot` + `fin_data.py label` + `fin_data.py event`

输出：20 只候选池清单 + 因子得分 + 信心度（不再是 5-10 只）

### Step 7 · **策略回测**（v3.2.0 新增：回答"这条选股规则历史上灵不灵"）

**必须运行 `scripts/backtest.py`（禁止 LLM 心算/编造回测结果）**：

```bash
# 推荐：基准单独给文件（沪深300 单列 CSV，行数与 prices 一致）
python scripts/backtest.py --prices-file prices.csv --signals-file signals.csv \
       --benchmark-file hs300.csv [--cost 0.0015]
# 也可把基准作为 prices 的某一列，用 --benchmark-col 指定（该列会被剔除出持仓）
python scripts/backtest.py --prices-file prices.csv --signals-file signals.csv --benchmark-col 5
```

- `prices.csv`：无表头，行=交易日，列=股票，收盘价（前复权，来自 `fin_data.py kline` 整理）
- `signals.csv`：与 prices 同形状；**第 j 行 = 第 j 日收盘可确定的目标权重**（用于 j→j+1 日收益，收盘调仓惯例，天然防前视）；非调仓行填 `nan`
- **基准必须显式指定**（`--benchmark-file` 推荐，或 `--benchmark-col`）。未指定时 `excess_return` / `benchmark_annual_return` 输出 `null` 并在 `benchmark_note` 告警，**禁止把总收益当作 alpha 上报**
- 交易成本按**实际平均调仓间隔**摊销（`actual_avg_rebalance_interval_days` 字段回显），不再写死月度
- 输出 JSON：累计/年化收益、夏普、最大回撤、超额收益、分年度收益、平均换手率、成本假设
- 回测报告 HTML：净值曲线 vs 沪深300 + 分年度收益表
- **声明**：SimBroker 全额成交无滑点，结果用于策略横向比较，不代表可实现收益
- 回测结果输出到当前会话工作目录，供主理人场景模板 D 汇总引用

## 输出
- 因子暴露报告 HTML
- 相关性矩阵热力图 HTML
- 组合优化建议（Black-Litterman 最优权重）
- 量化选股清单 CSV

## 数据接口
| 工具 | 用途 |
|------|------|
| `fin_data.py kline` | K 线（核心） |
| `fin_data.py chip` | 筹码分布 |
| `fin_data.py quote` | 实时价 |
| `fin_data.py finance` | 财报因子 |
| `fin_data.py score` | 多维评分 |
| `fin_data.py sector` | 因子排序 |
| `fin_data.py sector` | 条件选股 |
| `fin_data.py hot` | 策略筛选 |
| `fin_data.py label` | 标签 |
| `fin_data.py event` | 事件 |

## 版本
| 版本 | 日期 | 更新 |
|------|------|------|
| v1.0.0 | 2026-09-04 | 初版（模拟数据） |
| v3.0.0 | 2026-09-05 | 真实 K 线 + Black-Litterman + fin_data.py sector 真实对接 |
| **v3.2.0** | **2026-09-09** | **宏观配置（美林时钟）+ 行业轮动 + 三级漏斗选股（3 种输入，20 只候选池）+ 优化落地具体权重 + 相关性/优化脚本化 + Fama-French 修正为简化因子代理（明示局限）+ 策略回测（scripts/backtest.py，防前视偏差）** |
| **v3.2.1** | **2026-09-09** | **修复 backtest.py 前视偏差（信号偏移一行导致回测结果全 0）+ Step 6 三级漏斗/三种输入落地 + 新增 Step 7 策略回测章节（输入格式/防前视约定）** |
| **v3.3.0** | **2026-10-21** | **🐛 修复 correlation/optimizer/backtest 三个脚本依赖 numpy 导致崩溃（全部改纯标准库）+ 🐛 修复 optimizer 在股票池 <10 只时死循环报错（改现金口径，输出 cash_weight）+ 🐛 修复 backtest 收益率越界 IndexError + 全 nan 信号从崩溃改为明确报错 + ✨ Markowitz 新增目标收益不可达告警 + 真实 A 股 300 日数据回归测试通过** |
| **v3.3.1** | **2026-10-22** | **🐛 修复回测基准默认取「最后一列」的致命缺陷：旧版会把最后一只持仓股当基准并踢出组合，导致组合少一只股票、超额收益对标单只个股（实测把 -10.4% 的真实超额报成 +26.7%）。改为基准必须显式指定（--benchmark-file 推荐），未指定时 excess_return 输出 null 并告警 + 🐛 修复交易成本摊销写死 /21 天（日频调仓成本低估约 21 倍），改用实际平均调仓间隔** |
| **v3.3.2** | **2026-10-23** | **与团队 v3.3.2 契约对齐；本轮修复主理人 / 风控 / 舆情三处配置装饰化问题，本 skill 脚本回归全部通过** |
| **v3.4.0** | **2026-10-25** | **📝 修正展示层版本冲突；真实数据复测（9 只标的 300 日，风险平价 + 沪深300 显式基准回测）回归通过** |
| **v3.4.1** | **2026-10-25** | **✨ `optimizer.py` 单票上限改为策略口径驱动：新增 `--policy`（public_fund 10% 红线 / discretionary 25% / demo）、`--max-position`、`--cash-cap`（瀑布回填），并输出 `cash_explanation` 与 `pool_hint`——旧版 4 只股票池必然产出「每只 10% + 现金 60%」且无法解释，现场必被追问。Markowitz 新增 `mu_diagnostics`：先算约束下理论可达上界再判定目标是否可达（修正了「可达 7.40% 却宣称上限 2.96%」的口径不自洽），负 μ 导致的 target_return_infeasible 现直接给出可改的目标值** |
| **v4.0.0** | **2026-10-25** | **🌍 开源版：移除私有连接器 westock-mcp 依赖，改用内置统一数据层 shared/fin_data.py（L1 公开源 / L2 AKShare / L3 yfinance，零 API Key）+ 中英双语文档** |
