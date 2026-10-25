#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
为 9 个数字员工生成中英双语 README.md（幂等，可重复执行）。
python tools/gen_sub_readmes.py
"""
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent

E = [
    dict(
        d="fin-ai-orchestrator", emoji="🎼", cn="CIO 主理人", en="CIO Orchestrator",
        cn_tag="群体的「组织智商」：把 9 份独立意见裁决成一份可执行的作战方案",
        en_tag="Owns the team's organizational IQ — arbitrating nine opinions into one executable battle plan",
        cn_role="投委会主席 / 调度中枢。负责召集「三轮圆桌会议」：独立陈述 → 交叉质疑 → 收敛裁决，并对分歧做加权汇总，输出共识度评分。",
        en_role="Committee chair and dispatcher. Runs the three-round roundtable (briefs → cross-examination → verdict), aggregates disagreements into a weighted consensus score.",
        caps=[("三轮圆桌会议", "Three-round roundtable dialogue"),
              ("加权裁决 + 共识度评分", "Weighted arbitration with consensus scoring"),
              ("弃权感知（abstain）", "Abstention-aware aggregation"),
              ("全队统一数据契约 owner", "Sole owner of the shared team_package schema"),
              ("任务路由与并发调度", "Task routing and parallel dispatch")],
        eps=["quote", "kline", "index", "sector", "news"],
        io_in=[("问题/任务", "Question or mandate", "必填"),
               ("参与员工", "Which employees to summon", "全部 9 名"),
               ("决策风格", "Style: 稳健 balanced / 激进 aggressive", "稳健 balanced")],
        io_out=[("作战方案 HTML", "Battle-plan HTML", "完整决策方案"),
                ("圆桌会议纪要", "Roundtable minutes", "谁说了什么、谁否决了谁"),
                ("共识度评分卡", "Consensus scorecard", "加权分值 + 分歧点清单")],
        up=[("用户 / 自动化任务", "User or scheduled job")],
        down=[("其余 8 名员工（全部）", "All other 8 employees")],
        scripts=["scripts/consensus.py — 加权共识计算", "scripts/validate_package.py — 数据契约校验器"],
        note="全队唯一的契约校验器在这里。其余 8 名员工的 scripts/validate_package.py 均为指向此处的内置转发壳，保证单独安装任何一名员工也能通过契约校验。| The only real contract validator lives here; the other eight ship a forwarding shell so any single employee still validates when installed alone.",
    ),
    dict(
        d="fin-ai-researcher", emoji="🔬", cn="深度研究员", en="Deep Researcher",
        cn_tag="基金经理可信赖的「首席分析师」，用四种估值方法交叉验证一个结论",
        en_tag="The portfolio manager's trusted chief analyst — four valuation methods cross-checking one conclusion",
        cn_role="负责单只股票的深度研究：估值建模、可比公司筛选、敏感性分析，最终给出含买卖区间的投研报告。",
        en_role="Owns single-name depth: valuation modelling, comparable screening and sensitivity analysis, ending in a research report with trading ranges.",
        caps=[("DCF / PE / PB / DDM 四法估值", "Four-method valuation: DCF / PE / PB / DDM"),
              ("蒙特卡洛敏感性（10k 次，种子 42 可复现）", "Monte Carlo sensitivity — 10k draws, seed 42, reproducible"),
              ("可比公司与同类替代清单", "Comparable screening and substitute candidates"),
              ("产业链定位", "Industry-chain positioning"),
              ("5 秒应急模式", "5-second emergency mode")],
        eps=["quote", "kline", "finance", "profile", "news", "shareholder", "sector"],
        io_in=[("股票代码", "Symbol", "必填，如 sh600519 / hk00700 / usAAPL"),
               ("估值方法", "Valuation method", "all"),
               ("分析深度", "Depth", "deep")],
        io_out=[("投研报告 HTML", "Research report HTML", "含 6-8 张图表"),
                ("团队作战包 JSON", "team_package.json", "供其他员工消费"),
                ("路演摘要卡", "Showcase card", "适合投屏")],
        up=[("fin-ai-orchestrator", "CIO dispatch"), ("fin-ai-portfolio", "Batch study of 20 names"),
            ("fin-ai-crisis", "5-minute emergency mode")],
        down=[("fin-ai-portfolio", "写入组合 Dashboard"), ("fin-ai-risk", "作为风险输入"),
              ("fin-ai-crisis", "快速估值结论"), ("fin-ai-quant", "校准估值假设")],
        scripts=["scripts/dcf.py — 现金流折现（含 WACC 护栏）", "scripts/monte_carlo.py — 蒙特卡洛模拟"],
        note="真实案例：贵州茅台回归 β = -0.20、R² = 0.033，导致 WACC(0.55%) < 永续增长率 g(3%)。脚本不会粉饰输入——它触发护栏并在报告中声明「DCF 不适用，主结论改用相对估值」。| Real case: regressing 600519 gave β = -0.20, R² = 0.033 → WACC 0.55% < g 3%. The script refuses to massage inputs: it triggers a guardrail and tells the report to switch to relative valuation.",
    ),
    dict(
        d="fin-ai-portfolio", emoji="💼", cn="投研经理", en="Portfolio Manager",
        cn_tag="把 20 只持仓变成一个可解释的组合决策，并告诉你钱赚在哪、亏在哪",
        en_tag="Turns twenty holdings into one explainable portfolio decision — and tells you where the money was made",
        cn_role="负责组合层视图：资产配置分析、Brinson 业绩归因、相关性分析、调仓建议与组合回测。",
        en_role="Owns the portfolio layer: asset allocation, Brinson attribution, correlation analysis, rebalancing proposals and backtesting.",
        caps=[("Brinson 三因子业绩归因", "Brinson three-factor attribution"),
              ("组合相关性矩阵", "Portfolio correlation matrix"),
              ("调仓建议与同类替代", "Rebalancing proposals and substitutes"),
              ("组合回测（防前视偏差）", "Walk-forward backtest with look-ahead protection"),
              ("空持仓清单三重降级路径", "Three-step fallback when no watchlist exists")],
        eps=["quote", "sector", "index", "fund_flow"],
        io_in=[("组合来源", "Holdings source", "本地 watchlist.json"),
               ("业绩基准", "Benchmark", "沪深300"),
               ("分析周期", "Period", "3m")],
        io_out=[("组合 Dashboard HTML", "Portfolio dashboard HTML", "全局视图 + 归因"),
                ("调仓清单", "Rebalancing list", "可直接交给交易执行官"),
                ("归因报告", "Attribution report", "配置收益 / 选股收益 / 交互项")],
        up=[("用户", "User"), ("fin-ai-orchestrator", "CIO dispatch")],
        down=[("fin-ai-researcher", "请求个股深度研究"), ("fin-ai-risk", "组合风险输入"),
              ("fin-ai-execution", "触发调仓下单")],
        scripts=["scripts/brinson.py — Brinson 归因", "scripts/backtest.py — 组合回测",
                 "scripts/correlation.py — 相关性矩阵"],
        note="持仓来自用户自备的本地 watchlist.json（模板见 templates/），不依赖任何私有自选股接口；同一份清单在任何国家都跑得通。| Holdings come from your local watchlist.json (template in templates/) — no proprietary watchlist connector needed, so the same file runs anywhere.",
    ),
    dict(
        d="fin-ai-risk", emoji="🛡️", cn="风控官", en="Risk Officer",
        cn_tag="唯一有权对研究员的估值说「不」的员工",
        en_tag="The one employee empowered to say NO to the researcher's valuation",
        cn_role="负责事件驱动型风控： VaR 测算、压力测试、相关性矩阵、三级预警，以及把风险压在硬约束之内的「夹逼」处理。",
        en_role="Owns event-driven risk control: VaR, stress testing, correlation matrix, three-tier alerting, and hard clipping positions back inside limits.",
        caps=[("VaR（历史法 + 参数法）", "VaR — historical and parametric"),
              ("多情景压力测试", "Multi-scenario stress testing"),
              ("组合相关性矩阵", "Correlation matrix"),
              ("三级预警（黄/橙/红）", "Three-tier alerts: yellow / orange / red"),
              ("硬夹逼 hard clip", "Hard position clipping to mandate limits")],
        eps=["quote", "kline", "index", "news", "fund_flow"],
        io_in=[("持仓清单", "Holdings", "本地 watchlist.json"),
               ("置信度", "Confidence level", "95%"),
               ("情景集", "Scenario set", "data/scenarios.json")],
        io_out=[("风险评估报告", "Risk report", "VaR + 压力 + 预警清单"),
                ("夹逼后的建议仓位", "Clipped position proposals", "可直接可执行")],
        up=[("用户", "User"), ("fin-ai-orchestrator", "CIO dispatch"), ("fin-ai-portfolio", "组合输入")],
        down=[("fin-ai-execution", "仓位上限约束"), ("fin-ai-compliance", "风险事件复核")],
        scripts=["scripts/var.py — VaR 测算", "scripts/stress_test.py — 压力测试",
                 "scripts/correlation.py — 相关性矩阵", "scripts/hard_clip.py — 硬夹逼"],
        note="风险情景库在 data/scenarios.json，可自由增删：把 2008、2015、2020 换成你关心的任何历史窗口。| Scenario library lives in data/scenarios.json — swap in any historical window you care about.",
    ),
    dict(
        d="fin-ai-crisis", emoji="🚨", cn="应急交易员", en="Crisis Trader",
        cn_tag="突发利空出现后，五分钟内给出可执行的减仓方案",
        en_tag="Five minutes after bad news breaks, an executable de-risking plan",
        cn_role="对标真实基金的突发事件处置小组：舆情分级 → 历史案例匹配 → 影响评估 → 减仓方案 → 模拟试单 → 一键执行。",
        en_role="Mirrors a real fund's incident desk: severity grading → precedent matching → impact estimate → de-risking plan → paper trade → execution.",
        caps=[("5 分钟应急响应流水线", "5-minute incident pipeline"),
              ("突发事件自动分级", "Automatic severity grading"),
              ("历史事件案例库匹配", "Precedent case-library matching"),
              ("去重与噪声抑制", "De-duplication and noise suppression"),
              ("一键模拟试单", "One-click paper trade")],
        eps=["quote", "kline", "news", "index"],
        io_in=[("标的/事件", "Symbol or event", "必填"),
               ("响应时限", "Time budget", "5 min"),
               ("最大可承受回撤", "Max tolerable drawdown", "10%")],
        io_out=[("应急作战方案 HTML", "Incident battle plan HTML", "分级 + 依据 + 动作"),
                ("减仓指令", "De-risking orders", "可直送交易执行官")],
        up=[("fin-ai-news", "舆情预警触发"), ("用户", "User"), ("fin-ai-orchestrator", "CIO dispatch")],
        down=[("fin-ai-researcher", "请求应急估值"), ("fin-ai-execution", "执行减仓"),
              ("fin-ai-risk", "复核组合冲击")],
        scripts=["scripts/classify.py — 事件分级", "scripts/match_cases.py — 历史案例匹配",
                 "scripts/dedup.py — 去重"],
        note="案例库 data/case_library.json 是它的「经验」来源——把你自己亲历的踩坑事件加进去，它就会越来越像你的老交易员。| Case library data/case_library.json is its memory: add your own past incidents and it starts behaving like a veteran trader.",
    ),
    dict(
        d="fin-ai-news", emoji="📡", cn="舆情监控官", en="News Monitor",
        cn_tag="7×24 小时盯着舆情，并把每一条新闻放到历史坐标里判轻重",
        en_tag="Watches sentiment 24/7 and places every headline on a historical axis",
        cn_role="负责舆情扫描与自动分级：情绪指数 × 传播范围 × 监管权重三维打分，并与历史相似案例比对。",
        en_role="Owns sentiment monitoring and triage: a three-axis score (sentiment × reach × regulatory weight) plus precedent comparison.",
        caps=[("7×24 自动化扫描", "24/7 automated scanning"),
              ("三维动态分级", "Dynamic three-axis grading"),
              ("历史相似案例匹配", "Similar-historical-case matching"),
              ("去重与折叠", "De-duplication and collapsing"),
              ("向应急交易员自动报警", "Auto-alerting the crisis trader")],
        eps=["news", "notice", "quote", "hot"],
        io_in=[("监控范围", "Watch scope", "持仓 / 自选"),
               ("扫描频率", "Scan frequency", "每日 9:00 / 13:00"),
               ("告警阈值", "Alert threshold", "中危及以上")],
        io_out=[("舆情分级清单", "Graded sentiment list", "含打分依据"),
                ("告警通知", "Alerts", "推送应急交易员"),
                ("相似历史案例", "Precedent cases", "含后续走势参照")],
        up=[("自动化任务", "Scheduled job"), ("用户", "User"), ("fin-ai-orchestrator", "CIO dispatch")],
        down=[("fin-ai-crisis", "触发应急流程"), ("fin-ai-risk", "事件风险输入"),
              ("fin-ai-compliance", "合规性复核")],
        scripts=["scripts/classify.py — 三维分级打分", "scripts/match_cases.py — 相似案例匹配",
                 "scripts/dedup.py — 去重"],
        note="打分权重写在 data/scoring.json，全部可改：情绪占多少、监管权重占多少，由你自己定义。| Grading weights live in data/scoring.json — tune how much each axis counts.",
    ),
    dict(
        d="fin-ai-quant", emoji="📈", cn="量化分析师", en="Quant Analyst",
        cn_tag="团队里的模型审计员：专门检查别人的假设站不站得住",
        en_tag="The team's model auditor — its job is to check whether everyone else's assumptions hold up",
        cn_role="负责因子归因、相关性/协方差估计、组合优化，并对研究员与风控官的模型假设做独立校准。",
        en_role="Owns factor attribution, covariance estimation and portfolio optimization, and independently audits the assumptions made by the researcher and risk officer.",
        caps=[("Fama-French 因子归因", "Fama-French factor attribution"),
              ("Black-Litterman 观点融合", "Black-Litterman view blending"),
              ("Markowitz 组合优化", "Markowitz mean-variance optimization"),
              ("相关性 / 协方差矩阵", "Correlation and covariance matrices"),
              ("模型假设独立校准", "Independent calibration of model assumptions")],
        eps=["kline", "quote", "index", "sector"],
        io_in=[("股票池", "Universe", "必填"),
               ("因子集合", "Factor set", "市场 / 规模 / 价值 / 动量"),
               ("优化目标", "Objective", "最大夏普")],
        io_out=[("因子暴露报告", "Factor exposure report", "钱到底因子哪"),
                ("优化后权重", "Optimized weights", "含有效前沿"),
                ("假设审计意见", "Assumption audit opinion", "可否决他人模型")],
        up=[("fin-ai-portfolio", "组合输入"), ("fin-ai-orchestrator", "CIO dispatch")],
        down=[("fin-ai-researcher", "校准估值假设"), ("fin-ai-risk", "协方差矩阵供给")],
        scripts=["scripts/optimizer.py — 组合优化", "scripts/backtest.py — 策略回测",
                 "scripts/correlation.py — 相关性矩阵"],
        note="它是圆桌会议上唯一被授权「审计其他员工模型假设」的角色——这是群体智能里刻意设计的制衡。| It is deliberately the only role allowed to audit other employees' model assumptions — a built-in check inside the collective.",
    ),
    dict(
        d="fin-ai-compliance", emoji="⚖️", cn="合规专员", en="Compliance Officer",
        cn_tag="规则驱动，可以对整笔交易一票否决",
        en_tag="Rule-driven, with veto power over an entire trade",
        cn_role="负责信披合规、关联交易识别、投资者保护条款检查，每条结论都必须能溯源到具体条款号。",
        en_role="Owns disclosure compliance, related-party transaction detection and investor-protection checks; every finding traces back to a specific rule ID.",
        caps=[("规则库驱动检查", "Rule-pack driven checking"),
              ("关联交易识别", "Related-party transaction detection"),
              ("信息披露合规检查", "Disclosure and listing-rule compliance"),
              ("投资者保护条款核查", "Investor-protection clause audit"),
              ("完整审计日志", "Full audit trail")],
        eps=["profile", "shareholder", "notice", "news"],
        io_in=[("标的清单", "Symbol list", "必填"),
               ("适用规则集", "Rule set", "data/rules.json"),
               ("是否穿透股东", "Look-through shareholder analysis", "true")],
        io_out=[("合规审查意见", "Compliance opinion", "通过 / 限制 / 否决"),
                ("风险条款清单", "Triggered rule list", "含条款号与阈值"),
                ("审计日志", "Audit log", "可回放")],
        up=[("fin-ai-portfolio", "调仓前合规预检"), ("fin-ai-orchestrator", "CIO dispatch")],
        down=[("fin-ai-execution", "可否决下单"), ("fin-ai-risk", "合规风险叠加")],
        scripts=["scripts/check_rules.py — 规则引擎"],
        note="规则库 data/rules.json 采用「阈值 + 法条号」的结构，判定不再靠 LLM 自由发挥——这让审计人员可以逐条复核。| data/rules.json pairs each threshold with a clause number, so a human auditor can re-check every verdict line by line.",
    ),
    dict(
        d="fin-ai-execution", emoji="🎯", cn="交易执行官", en="Execution Trader",
        cn_tag="把决策变成订单：拆单、算冲击成本、留痕",
        en_tag="Turns a decision into orders: slicing, impact estimation, and receipts",
        cn_role="团队的最后一公里：算法拆单（TWAP/VWAP/POV/Iceberg/Sniper）、冲击成本测算、模拟撮合与成交留痕。",
        en_role="The last mile: algorithmic slicing (TWAP/VWAP/POV/Iceberg/Sniper), impact-cost estimation, paper trading and auditable fill records.",
        caps=[("五种算法拆单", "Five slicing algorithms"),
              ("冲击成本测算", "Market impact cost estimation"),
              ("本地模拟撮合（paper trading）", "Local paper trading"),
              ("成交明细留痕", "Auditable fill records"),
              ("受风控与合规双重约束", "Constrained by both risk limits and compliance")],
        eps=["quote", "kline", "minute"],
        io_in=[("订单", "Order", "买/卖 + 数量"),
               ("执行算法", "Algorithm", "TWAP"),
               ("参与率上限", "Max participation rate", "10%")],
        io_out=[("拆单计划", "Slicing schedule", "时间切片 + 数量"),
                ("冲击成本估算", "Impact cost estimate", "bp 计"),
                ("成交回放", "Fill replay", "含滑点")],
        up=[("fin-ai-portfolio", "调仓指令"), ("fin-ai-crisis", "应急减仓"),
            ("fin-ai-orchestrator", "CIO dispatch")],
        down=[("fin-ai-risk", "回传实际成交与偏离"), ("fin-ai-compliance", "提交合规留痕")],
        scripts=["scripts/impact_cost.py — 冲击成本测算"],
        note="它永远不会自行决定「要不要买」，只负责「怎么买更划算」——决策权与执行权在架构上强制分离。| It never decides whether to buy, only how to buy efficiently — decision and execution authority are structurally separated.",
    ),
]


def build(emp: dict, siblings: list) -> str:
    others = "\n".join(
        f"| {s['emoji']} [{s['cn']} · {s['en']}](../{s['d']}) | {s['cn_tag'][:38]}… |"
        for s in siblings if s["d"] != emp["d"]
    )
    caps = "\n".join(f"| {c} | {e} |" for c, e in emp["caps"])
    ins = "\n".join(f"| `{a}` | {b} | {c} |" for a, b, c in emp["io_in"])
    outs = "\n".join(f"| {a} | {b} | {c} |" for a, b, c in emp["io_out"])
    ups = "\n".join(f"| {a} | {b} |" for a, b in emp["up"])
    downs = "\n".join(f"| {a} | {b} |" for a, b in emp["down"])
    sc = "\n".join(f"| `{s}` |" for s in emp["scripts"])
    eps = "、".join(f"`fin_data.py {e}`" for e in emp["eps"])

    return f"""# {emp['emoji']} {emp['cn']} · {emp['en']}

> **{emp['cn_tag']}**
>
> **{emp['en_tag']}**

[← Back to team 返回团队总览](../README.md)

---

## 🎯 角色定位 · What this employee does

**中文**：{emp['cn_role']}

**English**: {emp['en_role']}

## 💡 核心能力 · Capabilities

| 中文 Chinese | English |
|---|---|
{caps}

## 🔌 依赖的数据端点 · Data endpoints

{eps}

全部由仓库内置的 `shared/fin_data.py` 提供，**无需任何 API Key**。
All served by the bundled `shared/fin_data.py` — **no API key required**.

```bash
python shared/fin_data.py quote sh600519
python shared/fin_data.py list
```

## 📥 输入参数 · Inputs

| 参数 Parameter | 说明 Description | 默认值 Default |
|---|---|---|
{ins}

## 📤 输出物 · Outputs

| 输出 Output | English | 说明 Note |
|---|---|---|
{outs}

## 🤝 在群体中的位置 · How it fits the collective

**上游（谁调用它）· Upstream**

| 来源 Source | English |
|---|---|
{ups}

**下游（它调用谁）· Downstream**

| 目标 Target | English |
|---|---|
{downs}

> 所有员工通过统一的 `team_package.json` 数据契约交换结果，
> 因此它们的协作是**可编程、可回放、可审计**的，而不是靠自然语言互相"理解"。
> All employees exchange results through the shared `team_package.json` contract, so their
> cooperation is machine-checkable rather than poetic.

## 🧮 内置脚本 · Bundled scripts

| 脚本 Script |
|---|
{sc}

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

{emp['note']}

---

## 👥 团队其他成员 · The rest of the team

| 员工 Role | 一句话 One-liner |
|---|---|
{others}

## 📜 协议 · License

[MIT](../LICENSE) © 2026 jameszeng809 · 输出仅供参考，**不构成投资建议** / outputs are **not investment advice**.
"""


def main():
    for emp in E:
        target = ROOT / emp["d"] / "README.md"
        target.write_text(build(emp, E), encoding="utf-8")
        print(f"  written {target.relative_to(ROOT)}")
    print(f"\n{len(E)} sub READMEs generated.")


if __name__ == "__main__":
    main()
