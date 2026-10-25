# 🛡️ 风控官 · Risk Officer

> **唯一有权对研究员的估值说「不」的员工**
>
> **The one employee empowered to say NO to the researcher's valuation**

[← Back to team 返回团队总览](../README.md)

---

## 🎯 角色定位 · What this employee does

**中文**：负责事件驱动型风控： VaR 测算、压力测试、相关性矩阵、三级预警，以及把风险压在硬约束之内的「夹逼」处理。

**English**: Owns event-driven risk control: VaR, stress testing, correlation matrix, three-tier alerting, and hard clipping positions back inside limits.

## 💡 核心能力 · Capabilities

| 中文 Chinese | English |
|---|---|
| VaR（历史法 + 参数法） | VaR — historical and parametric |
| 多情景压力测试 | Multi-scenario stress testing |
| 组合相关性矩阵 | Correlation matrix |
| 三级预警（黄/橙/红） | Three-tier alerts: yellow / orange / red |
| 硬夹逼 hard clip | Hard position clipping to mandate limits |

## 🔌 依赖的数据端点 · Data endpoints

`fin_data.py quote`、`fin_data.py kline`、`fin_data.py index`、`fin_data.py news`、`fin_data.py fund_flow`

全部由仓库内置的 `shared/fin_data.py` 提供，**无需任何 API Key**。
All served by the bundled `shared/fin_data.py` — **no API key required**.

```bash
python shared/fin_data.py quote sh600519
python shared/fin_data.py list
```

## 📥 输入参数 · Inputs

| 参数 Parameter | 说明 Description | 默认值 Default |
|---|---|---|
| `持仓清单` | Holdings | 本地 watchlist.json |
| `置信度` | Confidence level | 95% |
| `情景集` | Scenario set | data/scenarios.json |

## 📤 输出物 · Outputs

| 输出 Output | English | 说明 Note |
|---|---|---|
| 风险评估报告 | Risk report | VaR + 压力 + 预警清单 |
| 夹逼后的建议仓位 | Clipped position proposals | 可直接可执行 |

## 🤝 在群体中的位置 · How it fits the collective

**上游（谁调用它）· Upstream**

| 来源 Source | English |
|---|---|
| 用户 | User |
| fin-ai-orchestrator | CIO dispatch |
| fin-ai-portfolio | 组合输入 |

**下游（它调用谁）· Downstream**

| 目标 Target | English |
|---|---|
| fin-ai-execution | 仓位上限约束 |
| fin-ai-compliance | 风险事件复核 |

> 所有员工通过统一的 `team_package.json` 数据契约交换结果，
> 因此它们的协作是**可编程、可回放、可审计**的，而不是靠自然语言互相"理解"。
> All employees exchange results through the shared `team_package.json` contract, so their
> cooperation is machine-checkable rather than poetic.

## 🧮 内置脚本 · Bundled scripts

| 脚本 Script |
|---|
| `scripts/var.py — VaR 测算` |
| `scripts/stress_test.py — 压力测试` |
| `scripts/correlation.py — 相关性矩阵` |
| `scripts/hard_clip.py — 硬夹逼` |

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

风险情景库在 data/scenarios.json，可自由增删：把 2008、2015、2020 换成你关心的任何历史窗口。| Scenario library lives in data/scenarios.json — swap in any historical window you care about.

---

## 👥 团队其他成员 · The rest of the team

| 员工 Role | 一句话 One-liner |
|---|---|
| 🎼 [CIO 主理人 · CIO Orchestrator](../fin-ai-orchestrator) | 群体的「组织智商」：把 9 份独立意见裁决成一份可执行的作战方案… |
| 🔬 [深度研究员 · Deep Researcher](../fin-ai-researcher) | 基金经理可信赖的「首席分析师」，用四种估值方法交叉验证一个结论… |
| 💼 [投研经理 · Portfolio Manager](../fin-ai-portfolio) | 把 20 只持仓变成一个可解释的组合决策，并告诉你钱赚在哪、亏在哪… |
| 🚨 [应急交易员 · Crisis Trader](../fin-ai-crisis) | 突发利空出现后，五分钟内给出可执行的减仓方案… |
| 📡 [舆情监控官 · News Monitor](../fin-ai-news) | 7×24 小时盯着舆情，并把每一条新闻放到历史坐标里判轻重… |
| 📈 [量化分析师 · Quant Analyst](../fin-ai-quant) | 团队里的模型审计员：专门检查别人的假设站不站得住… |
| ⚖️ [合规专员 · Compliance Officer](../fin-ai-compliance) | 规则驱动，可以对整笔交易一票否决… |
| 🎯 [交易执行官 · Execution Trader](../fin-ai-execution) | 把决策变成订单：拆单、算冲击成本、留痕… |

## 📜 协议 · License

[MIT](../LICENSE) © 2026 jameszeng809 · 输出仅供参考，**不构成投资建议** / outputs are **not investment advice**.
