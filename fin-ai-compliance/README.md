# ⚖️ 合规专员 · Compliance Officer

> **规则驱动，可以对整笔交易一票否决**
>
> **Rule-driven, with veto power over an entire trade**

[← Back to team 返回团队总览](../README.md)

---

## 🎯 角色定位 · What this employee does

**中文**：负责信披合规、关联交易识别、投资者保护条款检查，每条结论都必须能溯源到具体条款号。

**English**: Owns disclosure compliance, related-party transaction detection and investor-protection checks; every finding traces back to a specific rule ID.

## 💡 核心能力 · Capabilities

| 中文 Chinese | English |
|---|---|
| 规则库驱动检查 | Rule-pack driven checking |
| 关联交易识别 | Related-party transaction detection |
| 信息披露合规检查 | Disclosure and listing-rule compliance |
| 投资者保护条款核查 | Investor-protection clause audit |
| 完整审计日志 | Full audit trail |

## 🔌 依赖的数据端点 · Data endpoints

`fin_data.py profile`、`fin_data.py shareholder`、`fin_data.py notice`、`fin_data.py news`

全部由仓库内置的 `shared/fin_data.py` 提供，**无需任何 API Key**。
All served by the bundled `shared/fin_data.py` — **no API key required**.

```bash
python shared/fin_data.py quote sh600519
python shared/fin_data.py list
```

## 📥 输入参数 · Inputs

| 参数 Parameter | 说明 Description | 默认值 Default |
|---|---|---|
| `标的清单` | Symbol list | 必填 |
| `适用规则集` | Rule set | data/rules.json |
| `是否穿透股东` | Look-through shareholder analysis | true |

## 📤 输出物 · Outputs

| 输出 Output | English | 说明 Note |
|---|---|---|
| 合规审查意见 | Compliance opinion | 通过 / 限制 / 否决 |
| 风险条款清单 | Triggered rule list | 含条款号与阈值 |
| 审计日志 | Audit log | 可回放 |

## 🤝 在群体中的位置 · How it fits the collective

**上游（谁调用它）· Upstream**

| 来源 Source | English |
|---|---|
| fin-ai-portfolio | 调仓前合规预检 |
| fin-ai-orchestrator | CIO dispatch |

**下游（它调用谁）· Downstream**

| 目标 Target | English |
|---|---|
| fin-ai-execution | 可否决下单 |
| fin-ai-risk | 合规风险叠加 |

> 所有员工通过统一的 `team_package.json` 数据契约交换结果，
> 因此它们的协作是**可编程、可回放、可审计**的，而不是靠自然语言互相"理解"。
> All employees exchange results through the shared `team_package.json` contract, so their
> cooperation is machine-checkable rather than poetic.

## 🧮 内置脚本 · Bundled scripts

| 脚本 Script |
|---|
| `scripts/check_rules.py — 规则引擎` |

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

规则库 data/rules.json 采用「阈值 + 法条号」的结构，判定不再靠 LLM 自由发挥——这让审计人员可以逐条复核。| data/rules.json pairs each threshold with a clause number, so a human auditor can re-check every verdict line by line.

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
| 🎯 [交易执行官 · Execution Trader](../fin-ai-execution) | 把决策变成订单：拆单、算冲击成本、留痕… |

## 📜 协议 · License

[MIT](../LICENSE) © 2026 jameszeng809 · 输出仅供参考，**不构成投资建议** / outputs are **not investment advice**.
