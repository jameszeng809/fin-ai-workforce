# 💼 投研经理 · Portfolio Manager

> **把 20 只持仓变成一个可解释的组合决策，并告诉你钱赚在哪、亏在哪**
>
> **Turns twenty holdings into one explainable portfolio decision — and tells you where the money was made**

[← Back to team 返回团队总览](../README.md)

---

## 🎯 角色定位 · What this employee does

**中文**：负责组合层视图：资产配置分析、Brinson 业绩归因、相关性分析、调仓建议与组合回测。

**English**: Owns the portfolio layer: asset allocation, Brinson attribution, correlation analysis, rebalancing proposals and backtesting.

## 💡 核心能力 · Capabilities

| 中文 Chinese | English |
|---|---|
| Brinson 三因子业绩归因 | Brinson three-factor attribution |
| 组合相关性矩阵 | Portfolio correlation matrix |
| 调仓建议与同类替代 | Rebalancing proposals and substitutes |
| 组合回测（防前视偏差） | Walk-forward backtest with look-ahead protection |
| 空持仓清单三重降级路径 | Three-step fallback when no watchlist exists |

## 🔌 依赖的数据端点 · Data endpoints

`fin_data.py quote`、`fin_data.py sector`、`fin_data.py index`、`fin_data.py fund_flow`

全部由仓库内置的 `shared/fin_data.py` 提供，**无需任何 API Key**。
All served by the bundled `shared/fin_data.py` — **no API key required**.

```bash
python shared/fin_data.py quote sh600519
python shared/fin_data.py list
```

## 📥 输入参数 · Inputs

| 参数 Parameter | 说明 Description | 默认值 Default |
|---|---|---|
| `组合来源` | Holdings source | 本地 watchlist.json |
| `业绩基准` | Benchmark | 沪深300 |
| `分析周期` | Period | 3m |

## 📤 输出物 · Outputs

| 输出 Output | English | 说明 Note |
|---|---|---|
| 组合 Dashboard HTML | Portfolio dashboard HTML | 全局视图 + 归因 |
| 调仓清单 | Rebalancing list | 可直接交给交易执行官 |
| 归因报告 | Attribution report | 配置收益 / 选股收益 / 交互项 |

## 🤝 在群体中的位置 · How it fits the collective

**上游（谁调用它）· Upstream**

| 来源 Source | English |
|---|---|
| 用户 | User |
| fin-ai-orchestrator | CIO dispatch |

**下游（它调用谁）· Downstream**

| 目标 Target | English |
|---|---|
| fin-ai-researcher | 请求个股深度研究 |
| fin-ai-risk | 组合风险输入 |
| fin-ai-execution | 触发调仓下单 |

> 所有员工通过统一的 `team_package.json` 数据契约交换结果，
> 因此它们的协作是**可编程、可回放、可审计**的，而不是靠自然语言互相"理解"。
> All employees exchange results through the shared `team_package.json` contract, so their
> cooperation is machine-checkable rather than poetic.

## 🧮 内置脚本 · Bundled scripts

| 脚本 Script |
|---|
| `scripts/brinson.py — Brinson 归因` |
| `scripts/backtest.py — 组合回测` |
| `scripts/correlation.py — 相关性矩阵` |

## 🗂️ 目录内容 · Directory contents

| 路径 Path | 说明 Description |
|---|---|
| `SKILL.md` | 完整角色定义与流水线 Full role definition and pipeline |
| `scripts/` | 纯标准库计算脚本 Stdlib-only calculators |
| `data/` | 本地规则库 / 案例库 Local rule & case packs |

## 🛡️ 数据诚实原则 · Honesty contract

每次数据调用返回 `status`（`ok` / `degraded` / `unavailable`）；凡非 `ok` 的字段
**必须在报告中显式披露**，禁止用估算值静默填充。
Every call carries a `status`; anything not `ok` **must be surfaced** — never silently backfilled.

## 🧩 设计说明 · Design note

持仓来自用户自备的本地 watchlist.json（模板见 templates/），不依赖任何私有自选股接口；同一份清单在任何国家都跑得通。| Holdings come from your local watchlist.json (template in templates/) — no proprietary watchlist connector needed, so the same file runs anywhere.

---

## 👥 团队其他成员 · The rest of the team

| 员工 Role | 一句话 One-liner |
|---|---|
| 🎼 [CIO 主理人 · CIO Orchestrator](../fin-ai-orchestrator) | 群体的「组织智商」：把 9 份独立意见裁决成一份可执行的作战方案… |
| 🔬 [深度研究员 · Deep Researcher](../fin-ai-researcher) | 基金经理可信赖的「首席分析师」，用四种估值方法交叉验证一个结论… |
| 🛡️ [风控官 · Risk Officer](../fin-ai-risk) | 唯一有权对研究员的估值说「不」的员工… |
| 🚨 [应急交易员 · Crisis Trader](../fin-ai-crisis) | 突发利空出现后，五分钟内给出可执行的减仓方案… |
| 📡 [舆情监控官 · News Monitor](../fin-ai-news) | 7×24 小时盯着舆情，并把每一条新闻放到历史坐标里判轻重… |
| 📈 [量化分析师 · Quant Analyst](../fin-ai-quant) | 团队里的模型审计员：专门检查别人的假设站不站得住… |
| ⚖️ [合规专员 · Compliance Officer](../fin-ai-compliance) | 规则驱动，可以对整笔交易一票否决… |
| 🎯 [交易执行官 · Execution Trader](../fin-ai-execution) | 把决策变成订单：拆单、算冲击成本、留痕… |

## 📜 协议 · License

[MIT](../LICENSE) © 2026 jameszeng809 · 输出仅供参考，**不构成投资建议** / outputs are **not investment advice**.
