# 📡 舆情监控官 · News Monitor

> **7×24 小时盯着舆情，并把每一条新闻放到历史坐标里判轻重**
>
> **Watches sentiment 24/7 and places every headline on a historical axis**

[← Back to team 返回团队总览](../README.md)

---

## 🎯 角色定位 · What this employee does

**中文**：负责舆情扫描与自动分级：情绪指数 × 传播范围 × 监管权重三维打分，并与历史相似案例比对。

**English**: Owns sentiment monitoring and triage: a three-axis score (sentiment × reach × regulatory weight) plus precedent comparison.

## 💡 核心能力 · Capabilities

| 中文 Chinese | English |
|---|---|
| 7×24 自动化扫描 | 24/7 automated scanning |
| 三维动态分级 | Dynamic three-axis grading |
| 历史相似案例匹配 | Similar-historical-case matching |
| 去重与折叠 | De-duplication and collapsing |
| 向应急交易员自动报警 | Auto-alerting the crisis trader |

## 🔌 依赖的数据端点 · Data endpoints

`fin_data.py news`、`fin_data.py notice`、`fin_data.py quote`、`fin_data.py hot`

全部由仓库内置的 `shared/fin_data.py` 提供，**无需任何 API Key**。
All served by the bundled `shared/fin_data.py` — **no API key required**.

```bash
python shared/fin_data.py quote sh600519
python shared/fin_data.py list
```

## 📥 输入参数 · Inputs

| 参数 Parameter | 说明 Description | 默认值 Default |
|---|---|---|
| `监控范围` | Watch scope | 持仓 / 自选 |
| `扫描频率` | Scan frequency | 每日 9:00 / 13:00 |
| `告警阈值` | Alert threshold | 中危及以上 |

## 📤 输出物 · Outputs

| 输出 Output | English | 说明 Note |
|---|---|---|
| 舆情分级清单 | Graded sentiment list | 含打分依据 |
| 告警通知 | Alerts | 推送应急交易员 |
| 相似历史案例 | Precedent cases | 含后续走势参照 |

## 🤝 在群体中的位置 · How it fits the collective

**上游（谁调用它）· Upstream**

| 来源 Source | English |
|---|---|
| 自动化任务 | Scheduled job |
| 用户 | User |
| fin-ai-orchestrator | CIO dispatch |

**下游（它调用谁）· Downstream**

| 目标 Target | English |
|---|---|
| fin-ai-crisis | 触发应急流程 |
| fin-ai-risk | 事件风险输入 |
| fin-ai-compliance | 合规性复核 |

> 所有员工通过统一的 `team_package.json` 数据契约交换结果，
> 因此它们的协作是**可编程、可回放、可审计**的，而不是靠自然语言互相"理解"。
> All employees exchange results through the shared `team_package.json` contract, so their
> cooperation is machine-checkable rather than poetic.

## 🧮 内置脚本 · Bundled scripts

| 脚本 Script |
|---|
| `scripts/classify.py — 三维分级打分` |
| `scripts/match_cases.py — 相似案例匹配` |
| `scripts/dedup.py — 去重` |

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

打分权重写在 data/scoring.json，全部可改：情绪占多少、监管权重占多少，由你自己定义。| Grading weights live in data/scoring.json — tune how much each axis counts.

---

## 👥 团队其他成员 · The rest of the team

| 员工 Role | 一句话 One-liner |
|---|---|
| 🎼 [CIO 主理人 · CIO Orchestrator](../fin-ai-orchestrator) | 群体的「组织智商」：把 9 份独立意见裁决成一份可执行的作战方案… |
| 🔬 [深度研究员 · Deep Researcher](../fin-ai-researcher) | 基金经理可信赖的「首席分析师」，用四种估值方法交叉验证一个结论… |
| 💼 [投研经理 · Portfolio Manager](../fin-ai-portfolio) | 把 20 只持仓变成一个可解释的组合决策，并告诉你钱赚在哪、亏在哪… |
| 🛡️ [风控官 · Risk Officer](../fin-ai-risk) | 唯一有权对研究员的估值说「不」的员工… |
| 🚨 [应急交易员 · Crisis Trader](../fin-ai-crisis) | 突发利空出现后，五分钟内给出可执行的减仓方案… |
| 📈 [量化分析师 · Quant Analyst](../fin-ai-quant) | 团队里的模型审计员：专门检查别人的假设站不站得住… |
| ⚖️ [合规专员 · Compliance Officer](../fin-ai-compliance) | 规则驱动，可以对整笔交易一票否决… |
| 🎯 [交易执行官 · Execution Trader](../fin-ai-execution) | 把决策变成订单：拆单、算冲击成本、留痕… |

## 📜 协议 · License

[MIT](../LICENSE) © 2026 jameszeng809 · 输出仅供参考，**不构成投资建议** / outputs are **not investment advice**.
