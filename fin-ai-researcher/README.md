# 🔬 深度研究员 · Deep Researcher

> **基金经理可信赖的「首席分析师」，用四种估值方法交叉验证一个结论**
>
> **The portfolio manager's trusted chief analyst — four valuation methods cross-checking one conclusion**

[← Back to team 返回团队总览](../README.md)

---

## 🎯 角色定位 · What this employee does

**中文**：负责单只股票的深度研究：估值建模、可比公司筛选、敏感性分析，最终给出含买卖区间的投研报告。

**English**: Owns single-name depth: valuation modelling, comparable screening and sensitivity analysis, ending in a research report with trading ranges.

## 💡 核心能力 · Capabilities

| 中文 Chinese | English |
|---|---|
| DCF / PE / PB / DDM 四法估值 | Four-method valuation: DCF / PE / PB / DDM |
| 蒙特卡洛敏感性（10k 次，种子 42 可复现） | Monte Carlo sensitivity — 10k draws, seed 42, reproducible |
| 可比公司与同类替代清单 | Comparable screening and substitute candidates |
| 产业链定位 | Industry-chain positioning |
| 5 秒应急模式 | 5-second emergency mode |

## 🔌 依赖的数据端点 · Data endpoints

`fin_data.py quote`、`fin_data.py kline`、`fin_data.py finance`、`fin_data.py profile`、`fin_data.py news`、`fin_data.py shareholder`、`fin_data.py sector`

全部由仓库内置的 `shared/fin_data.py` 提供，**无需任何 API Key**。
All served by the bundled `shared/fin_data.py` — **no API key required**.

```bash
python shared/fin_data.py quote sh600519
python shared/fin_data.py list
```

## 📥 输入参数 · Inputs

| 参数 Parameter | 说明 Description | 默认值 Default |
|---|---|---|
| `股票代码` | Symbol | 必填，如 sh600519 / hk00700 / usAAPL |
| `估值方法` | Valuation method | all |
| `分析深度` | Depth | deep |

## 📤 输出物 · Outputs

| 输出 Output | English | 说明 Note |
|---|---|---|
| 投研报告 HTML | Research report HTML | 含 6-8 张图表 |
| 团队作战包 JSON | team_package.json | 供其他员工消费 |
| 路演摘要卡 | Showcase card | 适合投屏 |

## 🤝 在群体中的位置 · How it fits the collective

**上游（谁调用它）· Upstream**

| 来源 Source | English |
|---|---|
| fin-ai-orchestrator | CIO dispatch |
| fin-ai-portfolio | Batch study of 20 names |
| fin-ai-crisis | 5-minute emergency mode |

**下游（它调用谁）· Downstream**

| 目标 Target | English |
|---|---|
| fin-ai-portfolio | 写入组合 Dashboard |
| fin-ai-risk | 作为风险输入 |
| fin-ai-crisis | 快速估值结论 |
| fin-ai-quant | 校准估值假设 |

> 所有员工通过统一的 `team_package.json` 数据契约交换结果，
> 因此它们的协作是**可编程、可回放、可审计**的，而不是靠自然语言互相"理解"。
> All employees exchange results through the shared `team_package.json` contract, so their
> cooperation is machine-checkable rather than poetic.

## 🧮 内置脚本 · Bundled scripts

| 脚本 Script |
|---|
| `scripts/dcf.py — 现金流折现（含 WACC 护栏）` |
| `scripts/monte_carlo.py — 蒙特卡洛模拟` |

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

真实案例：贵州茅台回归 β = -0.20、R² = 0.033，导致 WACC(0.55%) < 永续增长率 g(3%)。脚本不会粉饰输入——它触发护栏并在报告中声明「DCF 不适用，主结论改用相对估值」。| Real case: regressing 600519 gave β = -0.20, R² = 0.033 → WACC 0.55% < g 3%. The script refuses to massage inputs: it triggers a guardrail and tells the report to switch to relative valuation.

---

## 👥 团队其他成员 · The rest of the team

| 员工 Role | 一句话 One-liner |
|---|---|
| 🎼 [CIO 主理人 · CIO Orchestrator](../fin-ai-orchestrator) | 群体的「组织智商」：把 9 份独立意见裁决成一份可执行的作战方案… |
| 💼 [投研经理 · Portfolio Manager](../fin-ai-portfolio) | 把 20 只持仓变成一个可解释的组合决策，并告诉你钱赚在哪、亏在哪… |
| 🛡️ [风控官 · Risk Officer](../fin-ai-risk) | 唯一有权对研究员的估值说「不」的员工… |
| 🚨 [应急交易员 · Crisis Trader](../fin-ai-crisis) | 突发利空出现后，五分钟内给出可执行的减仓方案… |
| 📡 [舆情监控官 · News Monitor](../fin-ai-news) | 7×24 小时盯着舆情，并把每一条新闻放到历史坐标里判轻重… |
| 📈 [量化分析师 · Quant Analyst](../fin-ai-quant) | 团队里的模型审计员：专门检查别人的假设站不站得住… |
| ⚖️ [合规专员 · Compliance Officer](../fin-ai-compliance) | 规则驱动，可以对整笔交易一票否决… |
| 🎯 [交易执行官 · Execution Trader](../fin-ai-execution) | 把决策变成订单：拆单、算冲击成本、留痕… |

## 📜 协议 · License

[MIT](../LICENSE) © 2026 jameszeng809 · 输出仅供参考，**不构成投资建议** / outputs are **not investment advice**.
