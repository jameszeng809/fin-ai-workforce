---
name: fin-ai-portfolio
slug: fin-ai-portfolio
displayName: 普惠金融数字团队-投研经理
version: "4.3.0"
description: >
  普惠金融数字员工团队的"投研经理"角色。
  输入 20 只持仓清单（**来自公开数据源 watchlist.json（本地持仓清单） 真实分组**），
  一键完成组合全局视图、资产配置分析、Brinson 业绩归因、
  行业因子暴露、相关性矩阵、调仓方案，
  最终输出含组合 Dashboard 的 HTML 报告。
author: jameszeng809
agent_created: true
tags:
  - finance
  - portfolio-management
  - brinson-attribution
  - digital-employee
  - fin-ai-team
  - open-finance-data
parent_skill: fin-ai-terminal
data_source:
  - shared/fin_data.py  # 统一金融数据层：公开数据源，零 API Key，全球可用
trigger_phrases:
  - 投研经理
  - 组合分析
  - 持仓管理
  - 调仓建议
  - 资产配置
  - 业绩归因
  - portfolio management
  - rebalance portfolio
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


# 普惠金融-投研经理 (fin-ai-portfolio) v3.0

## 用途

「普惠金融数字员工团队」中的**投研经理**角色，对标真实基金的"基金经理助手"。
v4.0 核心差异：**持仓来自用户自备的本地清单 `watchlist.json`，行情来自统一数据层**。
持仓数据 100% 由用户掌控、可离线编辑、可版本管理；告别 v1/v2 的"模拟持仓"，
也**不依赖任何私有自选股接口**——同一份清单在任何国家都跑得通。

### v4.0 升级亮点

| 维度 | v1.0.0 模拟组合版 | **v4.0 开源组合版** |
|------|------|------|
| 持仓数据 | 手工 JSON 模拟 | **`watchlist.json` 本地持仓清单（用户自备）** |
| 实时价 | 静态快照 | **`fin_data.py quote` 批量实时价** |
| 资金动向 | 不支持 | **`fin_data.py fund_flow`（L1）** |
| 业绩归因 | 模板输出 | **Brinson 三因子真实计算** |
| 调仓建议 | 通用建议 | **基于 `fin_data.py sector` 同类替代** |
| 模拟试单 | 不支持 | **本地 paper trading 一键验证** |

> 📄 持仓清单格式见仓库根目录 `templates/watchlist.example.json`，复制为 `watchlist.json` 后按需编辑。

## 使用方法

| 参数 | 说明 | 默认值 | 示例 |
|------|------|-------|------|
| `组合来源` | watchlist 分组名 / 持仓 JSON | watchlist 全部 | "景顺长城新兴成长" |
| `市场` | A/HK/US/全部 | 全部 | A |
| `业绩基准` | 沪深300 / 恒生 / SP500 / 中证500 | 沪深300 | 沪深300 |
| `分析周期` | 1m / 3m / 6m / 1y / ytd | 3m | 3m |
| `是否输出调仓清单` | true/false | true | true |

调用入口：
- `@fin-ai-portfolio 分析我的景顺长城组合`
- 被 `fin-ai-orchestrator` 调度
- 被自动化任务（每日 17:00）触发

## 工作流程（8 步流水线 · v3.0）

### Step 1 · **读取持仓清单 + 拉取真实行情**（v4.0）
- 读取本地 `watchlist.json` 的全部分组（用户自备，格式见 `templates/`）
- 选中目标分组（如"景顺长城组合"）；未提供则退化为交互式录入
- 调用 `fin_data.py quote` 批量拉取 20 只股的实时行情
- 输出：标准持仓 JSON（每只股：code/name/weight/cost/current_price/PnL）

> **⚠️ v4.0 持仓清单降级路径（禁止断链）**
>
> 本地 `watchlist.json` 可能不存在或为空（首次使用、换机器、未同步均会如此）。
> 旧版流程只有"读单一数据源"一条路，遇到空列表**整条流水线当场中断**，无任何提示。
> 现按下列顺序降级，**每种降级都必须在报告顶部标注数据来源**：
>
> | 优先级 | 数据来源 | 触发条件 | 报告标注 |
> |-------|---------|---------|---------|
> | 1 | `watchlist.json` 分组 | 有数据 | 「组合来源：本地持仓清单〈组名〉」 |
> | 2 | 用户口头/粘贴的持仓清单 | watchlist 为空且用户已提供 | 「组合来源：用户提供的持仓清单」 |
> | 3 | 演示组合（见下表） | watchlist 为空且用户未提供 | 「组合来源：内置演示组合（非真实持仓）」 |
> | 3 | 演示组合（见下表） | watchlist 为空且用户未提供 | 「组合来源：内置演示组合（非真实持仓）」 |
>
> **内置演示组合**（跨市场 5 只，覆盖 A/港/美，可直接用于展示）：
>
> | 代码 | 名称 | 权重 | 行业 |
> |------|------|------|------|
> | sh600519 | 贵州茅台 | 30% | 食品饮料 |
> | hk00700 | 腾讯控股 | 25% | 传媒互联网 |
> | sz300750 | 宁德时代 | 20% | 电力设备 |
> | usTSLA | 特斯拉 | 15% | 汽车 |
> | sz000858 | 五粮液 | 10% | 食品饮料 |
>
> 降级时**不得**静默继续：必须输出 `degrade: {applied: true, reason, source}` 字段，
> 并在结论首段用一句话说明"以下分析基于演示组合，非用户真实持仓"。

### Step 2 · **行业归类与权重统计**
- 调用 `fin_data.py profile` 给每只股打行业标签
- 调用 `fin_data.py sector`（mode=list, scope=industry_list_sw1）拿申万一级行业全表
- 算每个行业的总权重
- 与基准（沪深300 行业权重）对比 → 算出**超配/低配**清单

### Step 3 · **Brinson 业绩归因**（v3.0 真实计算，v3.2.0 脚本化）
核心公式：

```
配置贡献 = Σ (组合权重 - 基准权重) × 行业基准收益
选股贡献 = Σ 组合权重 × (个股收益 - 行业基准收益)
交互贡献 = Σ (组合权重 - 基准权重) × (个股收益 - 行业基准收益)
```

**v3.2.0 强制**：禁止 LLM 心算，必须运行（团队未装 quant 时用本 skill 自带备份路径，权重和收益由 data_kline/data_sector 整理后传入）：

```
python scripts/brinson.py --pw 0.5,0.5 --bw 0.4,0.6 --pr 0.10,0.05 --br 0.08,0.03 --sectors 消费,科技
```

脚本自动做守恒校验（excess = 配置+选股+交互），校验不过禁止出报告。brinson.py 随本 skill 自带（scripts/brinson.py）。

> **v3.3.0**：brinson.py 改为纯标准库实现（不再依赖 numpy，开箱即用）；输出新增
> `portfolio_return` / `benchmark_return` / `conservation_passed` 三个字段，
> 权重和不为 1 时错误信息直接回显当前实际和值，便于定位输入错误。
>
> **v3.3.1 字段位置澄清**：上述三个字段位于输出 JSON 的 **`summary` 节内**
> （`summary.portfolio_return` / `summary.benchmark_return` / `summary.conservation_passed`），
> 并非顶层字段；顶层为 `sectors` / `allocation` / `selection` / `interaction` / `summary`。
> **禁止在 `conservation_passed` 为 false 时出报告**（守恒式：超额 = 配置 + 选股 + 交互）。

数据来源：
- 组合权重：来自 Step 1
- 基准权重：来自 data_index（沪深300） + data_sector
- 个股收益：data_kline 计算周期收益

### Step 4 · **风格因子暴露**
- 调 `fin_data.py sector` 算 5 个因子：
  - **规模**：组合加权市值因子得分
  - **价值**：组合加权 PE 反向
  - **成长**：组合加权营收增速
  - **动量**：组合加权 3m 动量
  - **质量**：组合加权 ROE
- 与基准（沪深300）因子分布对比
- 输出：因子偏离度雷达图

### Step 5 · **相关性矩阵 + 集中度**（v3.2.0 脚本化）
- 拉 20 只股的 60 日 K 线（data_kline），整理为日收益率 CSV
- **必须运行**（相关性/协方差由脚本计算，禁止手算）：

```bash
python scripts/correlation.py --returns-file returns.csv --labels 茅台,腾讯,宁德,特斯拉
# 注：scripts/correlation.py 为本 skill 自带副本；若同时安装了 fin-ai-quant，
#     亦可改用团队共用版 python ../fin-ai-quant/scripts/correlation.py（两者实现一致）
```

> **v3.3.0 修复**：旧版只引用 `../fin-ai-quant/scripts/correlation.py`，单独安装本 skill
> （未装量化分析师）时该路径不存在，Step 5 相关性计算直接断链。现本 skill 自带一份
> 纯标准库实现，口径与 quant 版完全一致。
- 脚本自动输出高相关对 Top5 与 >0.85 警告
- HHI 集中度阈值读 `../fin-ai-compliance/data/rules.json`（IL-01 行业 30% / IL-02 HHI 0.25）
- 单股集中度（前 5 大占比）

### Step 6 · **风险贡献分解**
- 调 `fin-ai-risk` 团队的算法（可独立实现）
- 每只股对组合 VaR 的边际贡献
- 调用 `fin_data.py fund_flow` + `fin_data.py north_holding` 看资金动向

### Step 7 · **调仓方案 + 同类替代**（v3.2.0：Signal 卡 + 风控硬夹逼）
- 算法：
  - 找出超配最多的 3 个行业（> 阈值）
  - 找出低配最多的 3 个行业
  - 对每个超配行业，用 `fin_data.py sector` 找该行业内**估值更低**的替代股
  - 对每个低配行业，用 `fin_data.py sector` 找**值得配置**的代表股
- **v3.2.0 硬约束**：目标权重必须通过风控官硬夹逼——单票 ≤10%、单行业 ≤30%（读 `../fin-ai-compliance/data/rules.json`）；"Conviction requests, risk disposes"，本 skill 无权覆盖
- 输出调仓清单（Signal 卡格式，含每笔 value/confidence/reasoning/abstain），须过 `../fin-ai-orchestrator/scripts/validate_package.py` 校验
  - 减仓股（具体股票 + 减仓权重 + 减仓金额）
  - 加仓股（具体股票 + 加仓权重 + 加仓金额）
  - 每笔调仓的理由 + 信心度

### Step 8 · **CIO Dashboard HTML 输出**
报告章节：
1. **组合摘要卡**（合计 20 只，总市值，今日盈亏）
2. **行业配置超低配**
3. **Brinson 业绩归因**（配置/选股/交互三柱图）
4. **风格因子雷达**
5. **相关性矩阵热力图**
6. **集中度 + 风险贡献**
7. **资金面动向**
8. **调仓清单 + 同类替代**

### Step 9 · **事后绩效复盘**（v3.2.0 新增：复盘+回测双引擎之"复盘"）
- 读取上期输出（`reviews/` 下最近一份 review 或用户提供的上期调仓清单）
- 逐项核对：上期"减仓/加仓/持有"建议 vs 截至当日的实际走势
- 量化指标：建议方向准确率、夏普、最大回撤、信息比率、胜率
- 结果写入 `reviews/review_{date}.json`，字段：{date, suggestions:[{stock, action, then_price, now_price, realized_pct, hit}], accuracy, sharpe, max_drawdown, win_rate}
- 复盘结论自动供主理人"复盘记忆闭环"读取（上期错在哪，本轮假设如何修正）

### Step 10 · **组合回测**（v3.2.0 新增：复盘+回测双引擎之"回测"）
- 把历次调仓建议序列整理为 signals.csv（第 j 行 = 第 j 日收盘确定的目标权重，非调仓行填 nan）
- 价格矩阵来自 `fin_data.py kline`（前复权收盘价），基准列 = 沪深300/恒生（`fin_data.py index`）
- **必须运行 quant 携带的共享脚本**（禁止 LLM 心算）：

```bash
python scripts/backtest.py --prices-file prices.csv --signals-file signals.csv \
       --benchmark-file hs300.csv
```

- **基准必须显式指定**（v3.3.1）：`--benchmark-file` 传沪深300 单列 CSV（推荐）；
  未指定时 `excess_return` 为 `null`，**禁止把总收益当作 alpha**
- 输出：净值曲线 vs 基准、年化收益、夏普、最大回撤、超额收益、平均换手率
> **✅ 跨 skill 依赖已内置转发壳（v3.4.0）**：`backtest.py` 属于 `fin-ai-quant`。若未同时安装量化分析师，该命令会失败；此时须先安装 `fin-ai-quant`，或跳过 Step 10 回测并在报告中标注「未做脚本回测，结论未经历史验证」。
- SimBroker 声明：全额成交无滑点，用于建议序列横向比较，不代表可实现收益

## 输出文件（v3.2.0：一律写到当前会话工作目录）

| 文件 | 路径 |
|------|------|
| HTML Dashboard | `fin-ai-portfolio/dashboard_{date}.html` |
| 团队作战包 JSON | `fin-ai-portfolio/team_package_{date}.json`（Signal 卡，须过校验器） |
| 调仓清单 CSV | `fin-ai-portfolio/rebalance_{date}.csv` |
| 绩效复盘 | `fin-ai-portfolio/reviews/review_{date}.json`（v3.2.0 新增） |

## 限制声明（v3.2.0 写全，不再引用其他文件）

- 本 skill 输出结果**仅供参考**，不构成任何投资建议；任何投资决策由人类投资者自行判断
- 历史业绩不代表未来表现；Brinson 归因基于公开数据简化计算，与卖方口径可能存在差异
- 回测为 SimBroker 全额成交、无滑点假设，不代表可实现收益
- 数据源降级时（一级→二级→三级）必须在报告中显式披露，写入 `audit.downgraded_sources`

## 与统一金融数据层 接口

| 工具 | 用途 |
|------|------|
| `watchlist.json（本地持仓清单）` | 读取真实持仓 |
| `watchlist.json（本地持仓清单）_groups` | 获取所有分组 |
| `watchlist.json（本地持仓清单）_batch_add` | 批量添加自选 |
| `fin_data.py quote` | 批量实时行情 |
| `fin_data.py kline` | 历史 K 线 |
| `fin_data.py profile` | 公司基本信息（用于行业归类） |
| `fin_data.py sector` | 申万一级行业 |
| `fin_data.py index` | 沪深300 基准 |
| `fin_data.py fund_flow` | 资金流向 |
| `fin_data.py north_holding` | 北向资金 |
| `fin_data.py consensus` | 一致预期 |
| `fin_data.py sector` | 同类替代排序 |

## 版本历史

| 版本 | 日期 | 关键更新 |
|------|------|---------|
| v1.0.0 | 2026-09-04 | 初版（模拟组合） |
| v2.0.0 | 2026-09-04 | Brinson 归因 |
| v3.0.0 | 2026-09-05 | 接入公开数据源组合 + 实时行情 + 真实 Brinson + 模拟试单 |
| **v3.2.0** | **2026-09-09** | **Brinson/相关性脚本化（禁 LLM 心算）+ Step9 绩效复盘 + Step10 组合回测（防前视偏差）+ 三种输入（20只A股/港股/行业自动配）+ Signal 卡 + 风控硬夹逼 + 限制声明写全** |
| **v3.2.1** | **2026-09-09** | **Step 9 绩效复盘/Step 10 组合回测章节落地 + 三种输入写入使用方法 + 修复 brinson.py 路径错误（改回本 skill 自带）+ 删除重复的限制声明章节** |
| **v3.3.0** | **2026-10-21** | **🐛 修复 brinson.py 依赖 numpy 导致崩溃（改纯标准库）+ 输出新增 portfolio_return/benchmark_return/conservation_passed + 真实 A 股数据（2025-07~2026-10，5 行业）回归测试通过，守恒校验 0.0** |

## 路演亮点
- **现场拉真实组合**：演示时调 watchlist.json（本地持仓清单），显示真实持仓
- **真实 Brinson 计算**：数据驱动而非模板
- **调仓清单可执行**：附带模拟试单验证
- **同类替代可视化**：一键看到该减仓什么、加仓什么
| **v3.3.1** | **2026-10-22** | **🐛 澄清字段位置：portfolio_return / benchmark_return / conservation_passed 位于 summary 节内而非顶层（文档曾误写为顶层）+ 📌 明示 backtest.py 属 fin-ai-quant 的跨 skill 依赖 + Step 10 回测命令补齐 --benchmark-file（未指定基准时超额收益为 null，禁止当 alpha）** |
| **v3.3.2** | **2026-10-23** | **与团队 v3.3.2 契约对齐；Brinson 真实数据复测守恒校验 0.0** |
| **v3.4.0** | **2026-10-25** | **✨ 单装可用性修复：`backtest.py` 改为内置转发壳，单装本 skill 也能回测（旧版必装 fin-ai-quant）；correlation.py 保留自带副本 + 📝 修正展示层版本冲突** |
| **v3.4.1** | **2026-10-25** | **✨ `correlation.py` 新增 `--labels`：高相关对从「只给列下标」改为同时输出资产名。旧版调用方必须自行维护「第几列是哪只股票」的映射表，跨 skill 传递时极易错位（风控官把第 2 列当腾讯、量化当成宁德）** |
| **v4.0.0** | **2026-10-25** | **🌍 开源版：移除私有连接器 westock-mcp 依赖，改用内置统一数据层 shared/fin_data.py（L1 公开源 / L2 AKShare / L3 yfinance，零 API Key）+ 中英双语文档** |
