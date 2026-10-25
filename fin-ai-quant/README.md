# 📈 量化分析师 · Quant Analyst

> **团队里的模型审计员：专门检查别人的假设站不站得住**
>
> **The team's model auditor — its job is to check whether everyone else's assumptions hold up**

[← Back to team 返回团队总览](../README.md)

---

## 🎯 角色定位 · What this employee does

**中文**：负责因子归因、相关性/协方差估计、组合优化，并对研究员与风控官的模型假设做独立校准。

**English**: Owns factor attribution, covariance estimation and portfolio optimization, and independently audits the assumptions made by the researcher and risk officer.

## 💡 核心能力 · Capabilities

| 中文 Chinese | English |
|---|---|
| Fama-French 因子归因 | Fama-French factor attribution |
| Black-Litterman 观点融合 | Black-Litterman view blending |
| Markowitz 组合优化 | Markowitz mean-variance optimization |
| 相关性 / 协方差矩阵 | Correlation and covariance matrices |
| 模型假设独立校准 | Independent calibration of model assumptions |

## 🔌 依赖的数据端点 · Data endpoints

`fin_data.py kline`、`fin_data.py quote`、`fin_data.py index`、`fin_data.py sector`

全部由仓库内置的 `shared/fin_data.py` 提供，**无需任何 API Key**。
All served by the bundled `shared/fin_data.py` — **no API key required**.

```bash
python shared/fin_data.py quote sh600519
python shared/fin_data.py list
```

## 📥 输入参数 · Inputs

| 参数 Parameter | 说明 Description | 默认值 Default |
|---|---|---|
| `股票池` | Universe | 必填 |
| `因子集合` | Factor set | 市场 / 规模 / 价值 / 动量 |
| `优化目标` | Objective | 最大夏普 |

## 📤 输出物 · Outputs

| 输出 Output | English | 说明 Note |
|---|---|---|
| 因子暴露报告 | Factor exposure report | 钱到底因子哪 |
| 优化后权重 | Optimized weights | 含有效前沿 |
| 假设审计意见 | Assumption audit opinion | 可否决他人模型 |

## 🤝 在群体中的位置 · How it fits the collective

**上游（谁调用它）· Upstream**

| 来源 Source | English |
|---|---|
| fin-ai-portfolio | 组合输入 |
| fin-ai-orchestrator | CIO dispatch |

**下游（它调用谁）· Downstream**

| 目标 Target | English |
|---|---|
| fin-ai-researcher | 校准估值假设 |
| fin-ai-risk | 协方差矩阵供给 |

> 所有员工通过统一的 `team_package.json` 数据契约交换结果，
> 因此它们的协作是**可编程、可回放、可审计**的，而不是靠自然语言互相"理解"。
> All employees exchange results through the shared `team_package.json` contract, so their
> cooperation is machine-checkable rather than poetic.

## 🧮 内置脚本 · Bundled scripts

| 脚本 Script |
|---|
| `scripts/optimizer.py — 组合优化` |
| `scripts/backtest.py — 策略回测` |
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

它是圆桌会议上唯一被授权「审计其他员工模型假设」的角色——这是群体智能里刻意设计的制衡。| It is deliberately the only role allowed to audit other employees' model assumptions — a built-in check inside the collective.

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
| ⚖️ [合规专员 · Compliance Officer](../fin-ai-compliance) | 规则驱动，可以对整笔交易一票否决… |
| 🎯 [交易执行官 · Execution Trader](../fin-ai-execution) | 把决策变成订单：拆单、算冲击成本、留痕… |

## 📜 协议 · License

[MIT](../LICENSE) © 2026 jameszeng809 · 输出仅供参考，**不构成投资建议** / outputs are **not investment advice**.
