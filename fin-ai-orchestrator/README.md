# 🎼 CIO 主理人 · CIO Orchestrator

> **群体的「组织智商」：把 9 份独立意见裁决成一份可执行的作战方案**
>
> **Owns the team's organizational IQ — arbitrating nine opinions into one executable battle plan**

[← Back to team 返回团队总览](../README.md)

---

## 🎯 角色定位 · What this employee does

**中文**：投委会主席 / 调度中枢。负责召集「三轮圆桌会议」：独立陈述 → 交叉质疑 → 收敛裁决，并对分歧做加权汇总，输出共识度评分。

**English**: Committee chair and dispatcher. Runs the three-round roundtable (briefs → cross-examination → verdict), aggregates disagreements into a weighted consensus score.

## 💡 核心能力 · Capabilities

| 中文 Chinese | English |
|---|---|
| 三轮圆桌会议 | Three-round roundtable dialogue |
| 加权裁决 + 共识度评分 | Weighted arbitration with consensus scoring |
| 弃权感知（abstain） | Abstention-aware aggregation |
| 全队统一数据契约 owner | Sole owner of the shared team_package schema |
| 任务路由与并发调度 | Task routing and parallel dispatch |

## 🔌 依赖的数据端点 · Data endpoints

`fin_data.py quote`、`fin_data.py kline`、`fin_data.py index`、`fin_data.py sector`、`fin_data.py news`

全部由仓库内置的 `shared/fin_data.py` 提供，**无需任何 API Key**。
All served by the bundled `shared/fin_data.py` — **no API key required**.

```bash
python shared/fin_data.py quote sh600519
python shared/fin_data.py list
```

## 📥 输入参数 · Inputs

| 参数 Parameter | 说明 Description | 默认值 Default |
|---|---|---|
| `问题/任务` | Question or mandate | 必填 |
| `参与员工` | Which employees to summon | 全部 9 名 |
| `决策风格` | Style: 稳健 balanced / 激进 aggressive | 稳健 balanced |

## 📤 输出物 · Outputs

| 输出 Output | English | 说明 Note |
|---|---|---|
| 作战方案 HTML | Battle-plan HTML | 完整决策方案 |
| 圆桌会议纪要 | Roundtable minutes | 谁说了什么、谁否决了谁 |
| 共识度评分卡 | Consensus scorecard | 加权分值 + 分歧点清单 |

## 🤝 在群体中的位置 · How it fits the collective

**上游（谁调用它）· Upstream**

| 来源 Source | English |
|---|---|
| 用户 / 自动化任务 | User or scheduled job |

**下游（它调用谁）· Downstream**

| 目标 Target | English |
|---|---|
| 其余 8 名员工（全部） | All other 8 employees |

> 所有员工通过统一的 `team_package.json` 数据契约交换结果，
> 因此它们的协作是**可编程、可回放、可审计**的，而不是靠自然语言互相"理解"。
> All employees exchange results through the shared `team_package.json` contract, so their
> cooperation is machine-checkable rather than poetic.

## 🧮 内置脚本 · Bundled scripts

| 脚本 Script |
|---|
| `scripts/consensus.py — 加权共识计算` |
| `scripts/validate_package.py — 数据契约校验器` |

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

全队唯一的契约校验器在这里。其余 8 名员工的 scripts/validate_package.py 均为指向此处的内置转发壳，保证单独安装任何一名员工也能通过契约校验。| The only real contract validator lives here; the other eight ship a forwarding shell so any single employee still validates when installed alone.

---

## 👥 团队其他成员 · The rest of the team

| 员工 Role | 一句话 One-liner |
|---|---|
| 🔬 [深度研究员 · Deep Researcher](../fin-ai-researcher) | 基金经理可信赖的「首席分析师」，用四种估值方法交叉验证一个结论… |
| 💼 [投研经理 · Portfolio Manager](../fin-ai-portfolio) | 把 20 只持仓变成一个可解释的组合决策，并告诉你钱赚在哪、亏在哪… |
| 🛡️ [风控官 · Risk Officer](../fin-ai-risk) | 唯一有权对研究员的估值说「不」的员工… |
| 🚨 [应急交易员 · Crisis Trader](../fin-ai-crisis) | 突发利空出现后，五分钟内给出可执行的减仓方案… |
| 📡 [舆情监控官 · News Monitor](../fin-ai-news) | 7×24 小时盯着舆情，并把每一条新闻放到历史坐标里判轻重… |
| 📈 [量化分析师 · Quant Analyst](../fin-ai-quant) | 团队里的模型审计员：专门检查别人的假设站不站得住… |
| ⚖️ [合规专员 · Compliance Officer](../fin-ai-compliance) | 规则驱动，可以对整笔交易一票否决… |
| 🎯 [交易执行官 · Execution Trader](../fin-ai-execution) | 把决策变成订单：拆单、算冲击成本、留痕… |

## 📜 协议 · License

[MIT](../LICENSE) © 2026 jameszeng809 · 输出仅供参考，**不构成投资建议** / outputs are **not investment advice**.
