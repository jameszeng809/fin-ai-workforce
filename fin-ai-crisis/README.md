# 🚨 应急交易员 · Crisis Trader

> **突发利空出现后，五分钟内给出可执行的减仓方案**
>
> **Five minutes after bad news breaks, an executable de-risking plan**

[← Back to team 返回团队总览](../README.md)

---

## 🎯 角色定位 · What this employee does

**中文**：对标真实基金的突发事件处置小组：舆情分级 → 历史案例匹配 → 影响评估 → 减仓方案 → 模拟试单 → 一键执行。

**English**: Mirrors a real fund's incident desk: severity grading → precedent matching → impact estimate → de-risking plan → paper trade → execution.

## 💡 核心能力 · Capabilities

| 中文 Chinese | English |
|---|---|
| 5 分钟应急响应流水线 | 5-minute incident pipeline |
| 突发事件自动分级 | Automatic severity grading |
| 历史事件案例库匹配 | Precedent case-library matching |
| 去重与噪声抑制 | De-duplication and noise suppression |
| 一键模拟试单 | One-click paper trade |

## 🔌 依赖的数据端点 · Data endpoints

`fin_data.py quote`、`fin_data.py kline`、`fin_data.py news`、`fin_data.py index`

全部由仓库内置的 `shared/fin_data.py` 提供，**无需任何 API Key**。
All served by the bundled `shared/fin_data.py` — **no API key required**.

```bash
python shared/fin_data.py quote sh600519
python shared/fin_data.py list
```

## 📥 输入参数 · Inputs

| 参数 Parameter | 说明 Description | 默认值 Default |
|---|---|---|
| `标的/事件` | Symbol or event | 必填 |
| `响应时限` | Time budget | 5 min |
| `最大可承受回撤` | Max tolerable drawdown | 10% |

## 📤 输出物 · Outputs

| 输出 Output | English | 说明 Note |
|---|---|---|
| 应急作战方案 HTML | Incident battle plan HTML | 分级 + 依据 + 动作 |
| 减仓指令 | De-risking orders | 可直送交易执行官 |

## 🤝 在群体中的位置 · How it fits the collective

**上游（谁调用它）· Upstream**

| 来源 Source | English |
|---|---|
| fin-ai-news | 舆情预警触发 |
| 用户 | User |
| fin-ai-orchestrator | CIO dispatch |

**下游（它调用谁）· Downstream**

| 目标 Target | English |
|---|---|
| fin-ai-researcher | 请求应急估值 |
| fin-ai-execution | 执行减仓 |
| fin-ai-risk | 复核组合冲击 |

> 所有员工通过统一的 `team_package.json` 数据契约交换结果，
> 因此它们的协作是**可编程、可回放、可审计**的，而不是靠自然语言互相"理解"。
> All employees exchange results through the shared `team_package.json` contract, so their
> cooperation is machine-checkable rather than poetic.

## 🧮 内置脚本 · Bundled scripts

| 脚本 Script |
|---|
| `scripts/classify.py — 事件分级` |
| `scripts/match_cases.py — 历史案例匹配` |
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

案例库 data/case_library.json 是它的「经验」来源——把你自己亲历的踩坑事件加进去，它就会越来越像你的老交易员。| Case library data/case_library.json is its memory: add your own past incidents and it starts behaving like a veteran trader.

---

## 👥 团队其他成员 · The rest of the team

| 员工 Role | 一句话 One-liner |
|---|---|
| 🎼 [CIO 主理人 · CIO Orchestrator](../fin-ai-orchestrator) | 群体的「组织智商」：把 9 份独立意见裁决成一份可执行的作战方案… |
| 🔬 [深度研究员 · Deep Researcher](../fin-ai-researcher) | 基金经理可信赖的「首席分析师」，用四种估值方法交叉验证一个结论… |
| 💼 [投研经理 · Portfolio Manager](../fin-ai-portfolio) | 把 20 只持仓变成一个可解释的组合决策，并告诉你钱赚在哪、亏在哪… |
| 🛡️ [风控官 · Risk Officer](../fin-ai-risk) | 唯一有权对研究员的估值说「不」的员工… |
| 📡 [舆情监控官 · News Monitor](../fin-ai-news) | 7×24 小时盯着舆情，并把每一条新闻放到历史坐标里判轻重… |
| 📈 [量化分析师 · Quant Analyst](../fin-ai-quant) | 团队里的模型审计员：专门检查别人的假设站不站得住… |
| ⚖️ [合规专员 · Compliance Officer](../fin-ai-compliance) | 规则驱动，可以对整笔交易一票否决… |
| 🎯 [交易执行官 · Execution Trader](../fin-ai-execution) | 把决策变成订单：拆单、算冲击成本、留痕… |

## 📜 协议 · License

[MIT](../LICENSE) © 2026 jameszeng809 · 输出仅供参考，**不构成投资建议** / outputs are **not investment advice**.
