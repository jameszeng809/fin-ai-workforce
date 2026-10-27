---
name: fin-ai-researcher
slug: fin-ai-researcher
displayName: 普惠金融数字团队-深度研究员
version: "4.3.0"
description: >
  普惠金融数字员工团队的"深度研究员"角色。
  输入股票代码或公司名称，通过**统一金融数据层**实时获取 A股/港股/美股
  真实行情、财务数据、资金流向、机构评级、研报、产业链、风险事件，一键完成
  数据聚合、财务指标速算、可比公司筛选、DCF/PE/PB/DDM 多方法估值建模、
  蒙特卡洛敏感性分析、专业图表生成，最终输出含估值模型与买卖区间的
  深度投研报告（HTML）。本团队获 2026 腾讯云黑客松 AI 智能体争霸赛全球二等奖。
author: jameszeng809
agent_created: true
tags:
  - finance
  - stock-analysis
  - investment-research
  - digital-employee
  - fin-ai-team
  - bloomberg-alternative
  - open-finance-data
parent_skill: fin-ai-terminal
parent_skills:
  - fin-ai-terminal
data_source:
  - shared/fin_data.py  # 统一金融数据层：公开数据源，零 API Key，全球可用
  - wb-finance-skill  # WorkBuddy 金融总入口（可选，用于补充数据源）
trigger_phrases:
  - 研究员分析
  - 深度研究
  - 个股深挖
  - 估值建模
  - 研究这只股票
  - 深度研究员
  - 真实数据研究
  - analyze stock in depth
  - valuation model
  - 生成深度报告
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


# 普惠金融-深度研究员 (fin-ai-researcher) v3.0

## 用途

「普惠金融数字员工团队」中的**深度研究员**角色，定位为：**基金经理/CIO 可信赖的"首席分析师"**。
本版本相较于 v1.0.0 / v2.0.0，**核心差异**是接入了**统一金融数据层**（20+ 公开数据端点），
所有数据从"模拟估算"升级到"实时公开数据"，从"单股分析"升级到"产业链定位 + 同类替代"。

### v3.0 升级亮点

| 维度 | v1.0.0 模拟数据版 | **v3.0 公开数据版** |
|------|------|------|
| 数据源 | 手工估算/假设数据 | **统一金融数据层 实时获取** |
| 行情数据 | 静态价格快照 | **data_quote 批量实时价** |
| 财务数据 | 简化报表 | **data_finance 三大报表原始数据** |
| 资金流向 | 不支持 | **data_fund_flow + 北向资金** |
| 估值参考 | 单独 PE/PB | **data_consensus 机构一致预期** |
| 风险信号 | 无 | **data_risk 风险事件明细 + data_events** |
| 研报参考 | 无 | **data_report + data_dehydrated 脱水研报** |
| 行业定位 | 行业归类 | **data_industry_chain 产业链图谱** |
| 估值建模 | DCF/PE/PB/DDM | **+ 蒙特卡洛敏感性 + 同类替代** |
| 报告交付 | 投研报告 | **真实数据 + 可执行清单 + 团队作战包 JSON** |

### 适用场景

| 场景 | 触发方式 | 配合员工 |
|------|---------|---------|
| 基金经理看组合某只重点股 | "深度研究 600519" | 投研经理调度 |
| 研究员做新覆盖 | "首次覆盖 宁德时代" | 单兵作战 |
| 应急小组需要快速判断 | "5 分钟内对 301117 出结论" | 应急交易员调度 |
| 主理人圆桌讨论 | "对茅台估值不同意见" | 团队圆桌 |
| 真实场景路演演示 | "分析贵州茅台/中免/海大" | 路演主输出 |

## 使用方法

直接告诉数字员工以下信息（不提供则交互式引导）：

| 参数 | 说明 | 默认值 | 示例 |
|------|------|-------|------|
| `股票代码` | A股/港股/美股代码 | 必填 | sh600519 / hk00700 / usAAPL |
| `市场` | cn/hk/us | 自动识别 | cn |
| `估值方法` | dcf/comparable/ddm/monte_carlo/all | all | all |
| `分析深度` | quick/standard/deep | deep | deep |
| `可比公司数量` | 对标的同行数量 | 5 | 5 |
| `是否输出买卖区间` | true/false | true | true |
| `报告格式` | html/pdf/word/all | html | html |
| `是否需要团队包` | true/false | true（被主理人调用时强制 true） | true |

> 调用入口：
> - **直接调用**：`@fin-ai-researcher 研究 sh600519`
> - **被主理人调度**：`fin-ai-orchestrator` 自动调用
> - **被应急交易员调度**：`fin-ai-crisis` 紧急模式（5 分钟内输出）
> - **被投研经理批量调度**：`fin-ai-portfolio` 组合批量研究

## 工作流程（10 步流水线 · v3.0 升级版）

### Step 1 · 任务解析 + 标的识别
- 解析输入：`股票代码/名称` + 可选 `市场/估值方法/深度`
- 自动识别市场：
  - `sh`/`sz`/`6位数字` → A股（沪/深）
  - `hk`/`5位数字` → 港股
  - `us`/`字母代码` → 美股
- 调用 `fin_data.py search` 搜索模糊标的 → 获取准确 code

### Step 2 · **公开数据源获取真实行情**（v3.0 新增）
并行调用：
- `fin_data.py quote`（实时价 / 涨跌 / 成交额 / 换手率 / 流通市值 / 总市值）
- `fin_data.py kline`（最近 250 日 K 线）
- `fin_data.py minute`（最近 5 日分时）
- `fin_data.py technical`（KDJ / MACD / RSI / BOLL）
- `fin_data.py chip`（筹码分布 / 主力成本）
- `fin_data.py market_overview`（大盘技术指标）

输出：实时行情快照 JSON → 用于所有后续计算的"当前数据"

### Step 3 · **公开数据源拉取基本面**（v3.0 新增）
并行调用：
- `fin_data.py profile`（公司概况 / 主营业务 / 行业地位）
- `fin_data.py finance`（利润表 / 资产负债表 / 现金流量表）
- `fin_data.py shareholder`（股东信息 / 流通结构）
- `fin_data.py dividend`（分红历史）
- `fin_data.py buyback`（回购数据）
- `fin_data.py industry_chain`（产业链图谱 / 个股归属）

### Step 4 · **公开数据源拉取市场情绪 + 资金**（v3.0 新增）
并行调用：
- `fin_data.py fund_flow`（主力资金 / 大单 / 中单 / 小单资金流向）
- `fin_data.py north_holding`（北向资金持仓变化）
- `fin_data.py south_holding`（南下资金，港股专用）
- `fin_data.py fund_margin`（融资融券）
- `fin_data.py fund_short`（融券数据 / 卖空压力）
- `fin_data.py fund_block`（大宗交易）
- `fin_data.py hot`（资金热度榜）
- `fin_data.py score`（诊股评分，多维度）

### Step 5 · **机构一致预期 + 研报参考**（v3.0 新增）
并行调用：
- `fin_data.py consensus`（机构一致预期：目标价 / 评级分布）
- `fin_data.py rating`（机构评级历史）
- `fin_data.py report`（研究报告列表）
- `fin_data.py dehydrated`（脱水研报-核心要点）
- `fin_data.py disclosure`（信息披露预约）
- `fin_data.py news`（最新新闻）
- `fin_data.py notice`（公告）

输出：市场预期值 + 卖方分析师观点 → 与我们自己的估值对比

### Step 6 · **风险事件扫描**（v3.0 新增）
并行调用：
- `fin_data.py risk`（风险事件：质押 / 解禁 / 诉讼 / ST 等）
- `fin_data.py events`（公司事件标签）
- `fin_data.py suspension`（停牌状态）
- `fin_data.py lhb`（龙虎榜 - 游资动向）

输出：风险清单 + 估值折价因子
- **风险阈值统一读规则库（v3.2.0）**：质押率/解禁占比/ST 等判定阈值从 `../fin-ai-compliance/data/rules.json` 的 `risk_events` 节读取（与合规专员同源），不自行拍阈值

### Step 7 · 多方法估值建模（核心）
基于真实数据，**自动选择**估值方法：

#### 7.1 · DCF 现金流折现（v3.2.0：必须由脚本执行，禁止 LLM 心算）
```
WACC = (D/V) * Rd * (1-t) + (E/V) * Re
  Re = Rf + β * (Rm - Rf)  # CAPM 模型
  Rf = 10年期国债收益率（来自 data_macro）
FCFF 5 年预测 → 终值 → 折现 → 每股价值
```
**执行方式（v3.2.0 强制）**：整理好 FCFF/WACC/g/净负债/股本后，运行：

```
python scripts/dcf.py --fcff 120,130,140,150,158 --wacc 0.09 --g 0.03 --net-debt 50000 --shares 12.56
```

脚本自动校验 WACC>g；终值占比>75% 时输出敏感性警告。脚本输出 error 时修复输入重跑，禁止跳过脚本手算。

> **⚠️ v3.4.1：β 异常与 WACC 护栏的强制处置（实测高频）**
>
> 用真实数据回归沪深300 时，β 常出现异常值——实测贵州茅台（sh600519）近 119 个交易日
> 回归得 **β = -0.20、R² = 0.033**，叠加 Rf=1.75% 后 WACC≈0.55% < g=3%，
> 旧版 dcf.py 直接 `sys.exit` 报错（"WACC 必须大于永续增长率 g"），整条投研流水线第一步即断。
>
> v3.4.1 起 dcf.py 改为**护栏模式**：WACC ≤ g 时自动抬升到 `g + 3%`，并在输出中返回
> `guardrail: {applied, input_wacc, used_wacc, reason, action_required}`。
>
> **调用方必须遵守（硬性）**：
> 1. `guardrail.applied == true` 时，**禁止把 DCF 结果当作主结论**，只能作为"参考区间"；
> 2. 报告主结论改用**相对估值**（PE/PB 历史分位 + 可比公司），并注明"DCF 因 β 异常不适用"；
> 3. β 的取值必须披露：来源（回归窗口/基准指数）、R²、是否已回退到行业 β；
> 4. R² < 0.10 时，β 视为不可用，直接改用**行业可比 β**（取同业上市公司 β 中位数）。
>
> 这条规则的意义：宁可给出"该方法不适用"的专业结论，也不要用一个数学上成立、
> 经济上荒谬的 WACC 编出一个精确到小数点的目标价。

**蒙特卡洛（v3.2.0 改为脚本执行）**：`python scripts/monte_carlo.py --base <DCF每股价值> --wacc 0.09 --g 0.03 --n 10000`，固定种子 42 保证可复现，输出估值分布与 95% 置信区间。

#### 7.2 · 可比公司 PE/PB/EV-EBITDA
- 用 `fin_data.py search` + `fin_data.py sector` 找 5 家可比公司（同行业 + 同市值规模）
- 拉取 5 家的 PE_TTM/PB_TTM/ROE/营收增速
- 算中位数 → 套用到目标公司

#### 7.3 · DDM 股利贴现（仅高股息股，分级处理）
```
Payout Ratio（分红比例）→ 红利增长率 → 贴现
若 dividend_yield < 1.5% → 自动 N/A（v3.0 修复 v1.0.0 的 bug）
若 payout_ratio < 20% → 显示「分红率偏低，建议参考 DCF 为主」
```

#### 7.4 · 估值方法对比 + 加权综合
| 方法 | 权重 | 适用性 |
|------|:---:|------|
| DCF | 50% | 成熟期、有稳定现金流 |
| 可比 PE | 25% | 行业相似、市值相近 |
| 可比 PB | 15% | 金融/资源等重资产 |
| DDM | 10% | 高股息个股 |

综合基准价 = 加权平均 → 自动给出买卖区间（基准价 ±1σ/2σ）

### Step 8 · **同类替代 + 行业定位**（v3.0 新增）
- 用 `fin_data.py sector` + `fin_data.py sector` 在该股所属申万一级行业中找**估值更合理、走势更强**的同类
- 用 `fin_data.py industry_chain` 输出**产业链图谱**（上中下游各 3 家代表企业）
- 决策建议：是否要做"调仓到同类替代"

### Step 9 · 专业图表生成（matplotlib · 6 张）
1. **K 线 + 成交量**（120 日）
2. **财务三柱图**（营收/净利/毛利趋势）
3. **6 维雷达图**（资金/估值/技术/行业/情绪/风险）
4. **DCF 敏感性热力图**（WACC × g 双轴）
5. **估值方法对比图**（4 种方法柱状对比）
6. **买卖区间可视化**（基准价 + 上下沿）
7. **（v3.0 新增）蒙特卡洛模拟分布**
8. **（v3.0 新增）产业链图谱**

### Step 10 · 团队作战包 JSON（标准化接口）
无论是否被主理人调用，都输出标准化 JSON：

```json
{
  "schema_version": "3.4.1",
  "skill_id": "fin-ai-researcher",
  "timestamp": "2026-10-23T15:30:00+08:00",
  "subject": {
    "type": "stock",
    "code": "sh600519",
    "name": "贵州茅台",
    "market": "cn"
  },
  "signal": {
    "value": -0.35,
    "confidence": 0.72,
    "reasoning": "DCF 脚本估值 1295.90 元，较现价 1335 元偏离 -2.93%；蒙特卡洛 95% 区间 [1074.7, 1520.3]；终值占比 0.801 偏高，故置信度下调至 0.72",
    "abstain": false,
    "abstain_reason": null,
    "recommendation": "hold",
    "key_risks": ["β 回归异常(R²=0.033)导致 WACC 护栏触发", "白酒行业动销同比下滑约 10%"]
  },
  "audit": {
    "input_snapshot_hash": "sha256:9f2c...（数据快照哈希，用于决策回放）",
    "data_as_of": "2026-10-23",
    "tokens_estimate": 18000,
    "downgraded_sources": []
  },
  "payload": {
    "real_data": {
      "current_price": 1335.00,
      "pe_ttm": 20.49,
      "pb_ttm": 6.64,
      "fund_flow_main": null,
      "consensus_target_price": null,
      "risk_events": []
    },
    "valuation": {
      "dcf": 1295.90,
      "comparable_pe": 1487,
      "comparable_pb": 787,
      "ddm": "N/A",
      "weighted": 1295.90,
      "monte_carlo": {"mean": 1296.1, "std": 113.6, "ci_95": [1074.7, 1520.3]}
    },
    "verdict": "合理偏低估",
    "upside": -2.93,
    "trading_range": {
      "buy_zone": [1074.7, 1295.9],
      "hold_zone": [1295.9, 1409.5],
      "sell_zone": [1409.5, 1520.3]
    },
    "industry_peers": [],
    "industry_chain": {},
    "team_package": {
      "ready_for_portfolio": true,
      "ready_for_crisis": true,
      "ready_for_orchestrator": true,
      "consume_by": ["fin-ai-portfolio", "fin-ai-crisis", "fin-ai-orchestrator"],
      "checksum": "sha256:xxx"
    }
  }
}
```

**Signal 卡规则（v3.2.0）**：
- `reasoning` 必填且须引用具体计算结果（脚本输出/数据字段），禁止纯观点
- 数据缺口 ≥3 项必需工具时必须 `abstain: true` 并写明 `abstain_reason`
- 输出前必须过校验器：`python scripts/validate_package.py <json文件>`，不过禁止上报主理人
> **✅ 跨 skill 依赖已内置转发壳（v3.4.0）**：`validate_package.py` 与 `team_package.schema.json` 属于 `fin-ai-orchestrator`（全团队共用同一份数据契约，故不复制副本）。若未同时安装 CIO 主理人，该命令会失败；此时须先安装 `fin-ai-orchestrator`，或人工对照 schema 自检并在报告中标注「未过脚本校验」。

## 工具依赖

### 数据接口依赖（v3.0 强制）

| 数据接口 | 用途 | 必填？ |
|---------|------|:---:|
| `fin_data.py quote` | 实时行情 | ✅ 必需 |
| `fin_data.py kline` | K 线 | ✅ 必需 |
| `fin_data.py profile` | 公司概况 | ✅ 必需 |
| `fin_data.py finance` | 三大报表 | ✅ 必需 |
| `fin_data.py consensus` | 机构一致预期 | 🟡 增强 |
| `fin_data.py rating` | 机构评级 | 🟡 增强 |
| `fin_data.py fund_flow` | 资金流向 | 🟡 增强 |
| `fin_data.py north_holding` | 北向资金 | 🟡 增强（A股） |
| `fin_data.py south_holding` | 南下资金 | 🟡 增强（港股） |
| `fin_data.py risk` | 风险事件 | 🟡 增强 |
| `fin_data.py events` | 公司事件 | 🟡 增强 |
| `fin_data.py news` | 新闻 | 🟡 增强 |
| `fin_data.py notice` | 公告 | 🟡 增强 |
| `fin_data.py industry_chain` | 产业链 | 🟢 锦上添花 |
| `fin_data.py hot` | 资金热度 | 🟢 锦上添花 |
| `fin_data.py score` | 诊股评分 | 🟢 锦上添花 |
| `fin_data.py report` | 研报列表 | 🟢 锦上添花 |
| `fin_data.py dehydrated` | 脱水研报 | 🟢 锦上添花 |
| `fin_data.py sector` | 同类排序 | 🟢 锦上添花 |
| `fin_data.py hot` | 策略筛选 | 🟢 锦上添花 |

降级策略：**如果某个 数据调用失败**，自动回退到本地缓存 / 简化估算，并在报告中标注「数据降级提示」。

### Python 依赖（v3.3.0：脚本零第三方依赖）

| 包 | 用途 | 必需？ |
|---|------|:---:|
| 无（标准库） | `scripts/dcf.py`、`scripts/monte_carlo.py` 已改为纯标准库实现 | ✅ 必需计算零依赖 |

> **v3.3.0 重要修复**：旧版 `monte_carlo.py` 依赖 `numpy`，在未安装 numpy 的环境（含大部分开箱环境）
> 会直接 `ModuleNotFoundError` 崩溃，导致"禁止 LLM 心算、必须跑脚本"的流水线整体断裂。
> 现已改为标准库实现（`random.Random(42)`，固定种子可复现），**任何 Python 3.8+ 环境开箱即用**。
> 蒙特卡洛分位数采用与 numpy 一致的线性插值算法，数值口径不变。

可选增强（非必需，失败不影响主流程）：

| 包 | 用途 |
|---|------|
| `matplotlib` | 图表渲染（无则跳过图表，报告改用表格） |
| `requests` | HTTP 调用 MCP（数据通道可用时无需） |
| `pandas` / `mplfinance` | 数据处理 / K 线图（可选） |

### wb-finance-skill（可选）

作为补充数据源，在公开数据源未覆盖的领域（如宏观经济指标）调用。

## 输出格式

### 1. HTML 投研报告（默认）

报告分 9 个章节：
1. **核心结论**（一页纸阅读：估值/评级/买卖区间/信心度）
2. **实时行情快照**（公开数据源拉取的最新 5 个行情指标）
3. **公司基本面**（营收/净利/行业地位）
4. **行业与产业链定位**
5. **资金面 + 机构态度**
6. **历史估值区间**
7. **多方法估值建模 + 敏感性**
8. **风险事件 + 监管动态**
9. **买卖建议 + 同类替代**

### 2. 团队作战包 JSON（必输出，无论是否被调用）

### 3. 路演摘要卡（v3.0 新增）
- 自动生成 1 张"研究员名片卡"适合贴在团队作战大屏
- 含：头像 / 评级 / 信心度 / 关键数字

## 路演亮点设计（v3.0）

### 亮点 1 · **现场连公开数据源取真实数据**
- 演示时输入"分析 sh600519"
- 现场调 `fin_data.py quote` + `fin_data.py finance` 等工具
- 现场看到真实茅台价格、最新净利、北向资金动向
- **评委看点**："你的数据和真实行情源完全打通，不是模拟"

### 亮点 2 · **机构一致预期 vs 我们估值的对比**
- 报告中的"估值结论"模块
- 显示：他们（机构）目标价 ¥1850 vs 我们 ¥1087
- 解释为什么我们认为应该更保守
- **评委看点**："你们有独立估值能力，不盲从大行"

### 亮点 3 · **同类替代清单**
- "如果你对茅台估值偏高的判断成立，那么可以加仓 海大/古井贡酒 等同类替代"
- 报告末尾自动列出 5 个替代标的
- **评委看点**："研究员的输出**直接给基金经理可执行清单**"

### 亮点 4 · **蒙特卡洛模拟分布**
- 用 10000 次模拟给出估值 95% 置信区间 [810-1402]
- 让评委看到"估值不是一个数字，是一个分布"
- **评委看点**："有量化思维，符合 MCM/MFE 模型"

## 应急模式（被 fin-ai-crisis 5min 内调度）

当被 `fin-ai-crisis` 紧急调用时：

| 步骤 | 正常模式 | 应急模式（5 分钟） |
|------|---------|-----------------|
| Step 2 行情 | 全 K 线 + 技术指标 | 仅实时价 + 涨跌 |
| Step 3 财务 | 全 3 大报表 | 仅关键财务指标（PE/PB/ROE） |
| Step 4 资金 | 全资金流向 | 仅主力净流入 |
| Step 5 预期 | 全部研报 | 仅一致预期 |
| Step 6 风险 | 全风险扫描 | 仅质押 + 解禁 + 诉讼 |
| Step 7 估值 | 全 4 方法 + 蒙特卡洛 | 仅 PE 可比 + DCF 简化版 |
| Step 9 图表 | 6-8 张 | 仅 K 线 + 雷达 |
| **总耗时** | 30 秒 | **5 秒** |

## 输出文件

| 文件 | 路径 | 说明 |
|------|------|------|
| HTML 报告 | `~/.workbuddy/workspace/fin-ai-researcher/{code}_report.html` | 完整投研报告 |
| 团队作战包 | `~/.workbuddy/workspace/fin-ai-researcher/{code}_team_package.json` | JSON 接口 |
| 路演摘要卡 | `~/.workbuddy/workspace/fin-ai-researcher/{code}_showcase_card.html` | 名片卡 |
| 日志 | `~/.workbuddy/workspace/fin-ai-researcher/logs/{date}.log` | 决策日志 |

## 版本历史

| 版本 | 日期 | 关键更新 |
|------|------|---------|
| v1.0.0 | 2026-09-04 | 初版（基于 fin-ai-terminal v1.0.2） |
| v2.0.0 | 2026-09-04 | 增加估值建模方法对比 |
| v3.0.0 | 2026-09-05 | 接入统一金融数据层（20+ 公开数据端点）+ 蒙特卡洛敏感性 + 产业链 + 同类替代 + 5 秒应急模式 |
| **v3.2.0** | **2026-09-09** | **DCF/蒙特卡洛脚本化（scripts/dcf.py、monte_carlo.py，禁 LLM 心算）+ Signal 统一卡（abstain 弃权机制）+ 风险阈值统一读 rules.json + 一页纸人话版 + 输出路径改会话相对路径 + 修复错别字** |
| **v3.2.1** | **2026-09-09** | **Step 10 Signal 统一卡字段落地（value/confidence/reasoning/abstain，必过校验器）+ Step 6 阈值读 rules.json 落地 + 第 4 处错别字修复 + frontmatter 版本号补齐** |
| **v3.3.0** | **2026-10-21** | **🐛 修复 monte_carlo.py 依赖 numpy 导致崩溃（改纯标准库，种子 42 可复现，分位数线性插值口径不变）+ 修复 g 抽样可能 ≥ wacc 的无效样本（g 上限改为随当次 wacc 浮动）+ 脚本全量真实数据回归测试通过 + Python 依赖段改写为零依赖声明** |

## 数据真实性声明（v3.2.0 统一降级模板）

v3.2.0 统一降级模板（9 名员工共用同一格式，任何数据不可得必须显式披露，禁止沉默降级）：
- ✅ 一级数据源：公开数据源 `fin_data.py finance` / `fin_data.py quote` / `fin_data.py consensus` 等（实时真实）
- 🟡 二级数据源：wb-finance-skill 补充（如宏观指标）
- 🟠 三级数据源：WebSearch 公开资料（须标注"公开报道，未经交易所核实"）
- 🔴 降级披露：任一一级数据源失败时，报告显著位置输出「数据降级提示：本次 XX 指标来自 XX，可靠性降低」，并写入团队作战包 `audit.downgraded_sources`
- ⚠️ 估值建模（DCF/PE/PB/DDM）为本团队计算，含合理假设；蒙特卡洛为随机模拟（固定种子 42 可复现），结果有统计意义但非预测

## 与数字员工团队其他成员的接口

| 上游被谁调用 | 输入 | 输出 |
|------------|------|------|
| fin-ai-orchestrator | 调度令 + 任务上下文 | 团队作战包 JSON |
| fin-ai-portfolio | 批量研究 20 只股 | 20 份团队作战包 |
| fin-ai-crisis | 5min 应急模式 | 简版估值结论 |
| fin-ai-news | 历史案例匹配 | 比对评分 |
| fin-ai-quant | 估值模型校准 | 蒙特卡洛分布 |
| fin-ai-risk | 风险事件补充 | 风险折价因子 |

| 下游调用谁 | 场景 |
|----------|------|
| fin-ai-orchestrator | 接收团队作战包汇总 |
| fin-ai-portfolio | 写入组合 Dashboard |
| fin-ai-risk | 作为风险输入 |
| fin-ai-execution | 触发模拟/真实交易 |

## 技术亮点（v3.0）

1. **零模拟**：所有底层数据全部来自统一金融数据层，告别 v1/v2 的"虚拟数据"
2. **多方法估值**：DCF + 可比 PE/PB + DDM + 蒙特卡洛，提供分布而非点估计
3. **应急模式**：5 分钟应急 vs 30 秒标准模式，按场景自适应
4. **团队作战包**：标准 JSON 接口，让 9 个员工之间能程序化协作
5. **产业链定位**：用 `fin_data.py industry_chain` 自动生成产业链图谱
6. **同类替代**：自动给出可替换标的清单，配合主理人调仓

## 限制与免责声明

- 本员工输出结果**仅供参考**，不构成任何投资建议
- 任何投资决策均由人类基金经理/用户自行判断
- 历史业绩不代表未来表现
- 估值模型基于公开数据简化计算，可能与卖方研报存在显著差异
- 使用即视为同意本声明
| **v3.3.1** | **2026-10-22** | **📌 明示跨 skill 依赖：validate_package.py 与 team_package.schema.json 属于 fin-ai-orchestrator；本 skill 已内置转发壳 scripts/ + 真实数据实测（茅台 DCF 每股内在价值 1220.18 元 vs 现价 1318.49 元，终值占比 77.8% 触发告警）** |
| **v3.3.2** | **2026-10-23** | **与团队 v3.3.2 契约对齐；真实数据复测（茅台现价 1335.00，DCF 每股内在价值 vs 市价对比 + 蒙特卡洛区间）** |
| **v3.4.0** | **2026-10-25** | **✨ 单装可用性修复：`validate_package.py` 改为内置转发壳，单装本 skill 也能过契约校验 + 📝 修正展示层版本冲突（「决赛首版」「基于初赛作品二次升级」等过时文案已更新为获奖背书）** |
| **v3.4.1** | **2026-10-25** | **📝 文档自洽复核：Step 10 作战包示例已实跑契约校验器 PASS（此前示例缺 5 个必填字段，照抄必被自己的校验器 FAIL）；契约版本随全队同步至 3.4.1（本轮无脚本变更，仅契约版本同步）** |
| **v4.0.0** | **2026-10-25** | **🌍 开源版：移除私有连接器 westock-mcp 依赖，改用内置统一数据层 shared/fin_data.py（L1 公开源 / L2 AKShare / L3 yfinance，零 API Key）+ 中英双语文档** |
