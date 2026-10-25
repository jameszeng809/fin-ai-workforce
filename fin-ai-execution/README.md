# 🎯 交易执行官 · Execution Trader

> **把决策变成订单：拆单、算冲击成本、留痕**
>
> **Turns a decision into orders: slicing, impact estimation, and receipts**

[← Back to team 返回团队总览](../README.md)

---

## 🎯 角色定位 · What this employee does

**中文**：团队的最后一公里：算法拆单（TWAP/VWAP/POV/Iceberg/Sniper）、冲击成本测算、模拟撮合与成交留痕。

**English**: The last mile: algorithmic slicing (TWAP/VWAP/POV/Iceberg/Sniper), impact-cost estimation, paper trading and auditable fill records.

## 💡 核心能力 · Capabilities

| 中文 Chinese | English |
|---|---|
| 五种算法拆单 | Five slicing algorithms |
| 冲击成本测算 | Market impact cost estimation |
| 本地模拟撮合（paper trading） | Local paper trading |
| 成交明细留痕 | Auditable fill records |
| 受风控与合规双重约束 | Constrained by both risk limits and compliance |

## 🔌 依赖的数据端点 · Data endpoints

`fin_data.py quote`、`fin_data.py kline`、`fin_data.py minute`

全部由仓库内置的 `shared/fin_data.py` 提供，**无需任何 API Key**。
All served by the bundled `shared/fin_data.py` — **no API key required**.

```bash
python shared/fin_data.py quote sh600519
python shared/fin_data.py list
```

## 📥 输入参数 · Inputs

| 参数 Parameter | 说明 Description | 默认值 Default |
|---|---|---|
| `订单` | Order | 买/卖 + 数量 |
| `执行算法` | Algorithm | TWAP |
| `参与率上限` | Max participation rate | 10% |

## 📤 输出物 · Outputs

| 输出 Output | English | 说明 Note |
|---|---|---|
| 拆单计划 | Slicing schedule | 时间切片 + 数量 |
| 冲击成本估算 | Impact cost estimate | bp 计 |
| 成交回放 | Fill replay | 含滑点 |

## 🤝 在群体中的位置 · How it fits the collective

**上游（谁调用它）· Upstream**

| 来源 Source | English |
|---|---|
| fin-ai-portfolio | 调仓指令 |
| fin-ai-crisis | 应急减仓 |
| fin-ai-orchestrator | CIO dispatch |

**下游（它调用谁）· Downstream**

| 目标 Target | English |
|---|---|
| fin-ai-risk | 回传实际成交与偏离 |
| fin-ai-compliance | 提交合规留痕 |

> 所有员工通过统一的 `team_package.json` 数据契约交换结果，
> 因此它们的协作是**可编程、可回放、可审计**的，而不是靠自然语言互相"理解"。
> All employees exchange results through the shared `team_package.json` contract, so their
> cooperation is machine-checkable rather than poetic.

## 🧮 内置脚本 · Bundled scripts

| 脚本 Script |
|---|
| `scripts/impact_cost.py — 冲击成本测算` |

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

它永远不会自行决定「要不要买」，只负责「怎么买更划算」——决策权与执行权在架构上强制分离。| It never decides whether to buy, only how to buy efficiently — decision and execution authority are structurally separated.

---

## 👥 团队其他成员 · The rest of the team

| 员工 Role | 一句话 One-liner |
|---|---|
| 🎼 [CIO 主理人 · CIO Orchestrator](../fin-ai-orchestrator) | 群体的「组织智商」：把 9 份独立意见裁决成一份可执行的作战方案… |
| 🔬 [深度研究员 · Deep Researcher](../fin-ai-researcher) | 基金经理可信赖的「首席分析师」，用四种估值方法交叉验证一个结论… |
| 💼 [投研经理 · Portfolio Manager](../fin-ai-portfolio) | 把 20 只持仓变成一个可解释的组合决策，并告诉你钱赚在哪、亏在哪… |
| 🛡️ [风控官 · Risk Officer](../fin-ai-risk) | 唯一有权对研究员的估值说「不」的员工… |
| 🚨 [应急交易员 · Crisis Trader](../fin-ai-crisis) | 突发利空出现后，五分钟内给出可执行的减仓方案… |
| 📡 [舆情监控官 · News Monitor](../fin-ai-news) | 7×24 小时盯着舆情，并把每一条新闻放到历史坐标里判轻重… |
| 📈 [量化分析师 · Quant Analyst](../fin-ai-quant) | 团队里的模型审计员：专门检查别人的假设站不站得住… |
| ⚖️ [合规专员 · Compliance Officer](../fin-ai-compliance) | 规则驱动，可以对整笔交易一票否决… |

## 📜 协议 · License

[MIT](../LICENSE) © 2026 jameszeng809 · 输出仅供参考，**不构成投资建议** / outputs are **not investment advice**.
