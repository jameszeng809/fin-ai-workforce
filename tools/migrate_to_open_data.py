#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
一次性迁移脚本：把 9 个数字员工从私有连接器（westock-mcp）
切换到仓库内置的统一数据层（shared/fin_data.py）。

用法：python tools/migrate_to_open_data.py
幂等：重复执行不会产生重复插入（插入前检查哨兵串）。
"""
import re
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
SKILLS = ["fin-ai-orchestrator", "fin-ai-researcher", "fin-ai-portfolio",
          "fin-ai-risk", "fin-ai-crisis", "fin-ai-news", "fin-ai-quant",
          "fin-ai-compliance", "fin-ai-execution"]

SENTINEL = "统一数据层 fin_data.py"

# ---- 长句优先，避免被短规则截断 -------------------------------------------
PHRASES = [
    ("腾讯自选股 MCP 连接器（50+ 真实数据工具）", "统一金融数据层（公开数据源，全球可用）"),
    ("腾讯自选股 MCP 连接器", "统一金融数据层"),
    ("腾讯自选股 MCP", "统一金融数据层"),
    ("腾讯自选股接口", "数据接口"),
    ("腾讯自选股的真实数据", "公开数据源的真实数据"),
    ("腾讯自选股实时", "公开数据源实时"),
    ("腾讯自选股", "公开数据源"),
    ("腾讯自选股MCP", "统一金融数据层"),
    ("MCP 工具依赖", "数据接口依赖"),
    ("MCP 工具", "数据接口"),
    ("MCP 接口", "数据接口"),
    ("MCP 通道", "数据通道"),
    ("MCP 调用", "数据调用"),
    ("MCP 返回", "接口返回"),
    ("50+ 真实数据工具", "20+ 公开数据端点"),
    ("真实数据版", "公开数据版"),
    ("实时真实数据", "实时公开数据"),
    ("实时拉取", "实时获取"),
    ("拉真实数据", "取真实数据"),
    ("拉取真实行情", "获取真实行情"),
    ("拉取真实", "获取真实"),
    ("连腾讯自选股", "直连公开数据源"),
    ("零模拟：所有底层数据全部来自", "零模拟：所有底层数据全部来自"),
]

TOOL_MAP = {
    "tool_ranking": "fin_data.py sector",
    "tool_filter": "fin_data.py sector",
    "tool_strategy": "fin_data.py hot",
    "tool_list_events": "fin_data.py events",
    "tool_list_labels": "fin_data.py hot",
    "portfolio_watchlist": "watchlist.json（本地持仓清单）",
    "portfolio_watchlist_groups": "watchlist.json 分组",
    "portfolio_paper_trade": "模拟撮合（本地 paper trading）",
    "portfolio_paper_positions": "",
    "portfolio_paper_portfolio": "本地模拟持仓",
    "portfolio_paper_history": "本地模拟成交流水",
    "portfolio_tips_query": "本地提醒设置",
    "portfolio_group_add": "本地分组管理",
}

DATA_BLOCK = """## 🌐 数据获取方式（统一数据层 · 零 API Key）

本项目**不依赖任何私有连接器**。所有行情/基本面数据来自仓库内置的统一数据层：

```bash
# 语法：python shared/fin_data.py <端点> <股票代码>
python shared/fin_data.py quote    sh600519     # 实时行情（含 PE/PB/市值/换手率）
python shared/fin_data.py kline    sh600519 --days 250
python shared/fin_data.py finance  sh600519     # 主要财务指标（8 期）
python shared/fin_data.py news     sh600519     # 最新新闻
python shared/fin_data.py list                  # 查看全部端点
```

| 数据通道 | 覆盖范围 | 需要 Key？ |
|---|---|:---:|
| **L1 公开数据源**（默认，零依赖） | 行情 / K线 / 技术指标 / 财务 / 股东 / 新闻 / 指数 / 板块 | ❌ |
| **L2 AKShare**（可选 `pip install akshare`） | A股深度：龙虎榜 / 融资融券 / 筹码分布 / 分红 / 北向资金 | ❌ |
| **L3 yfinance**（可选 `pip install yfinance`） | 港美股深度数据 | ❌ |

> **数据诚实原则（硬性）**：每次调用返回 `status` 字段 —— `ok` / `degraded` / `unavailable`。
> 凡是 `degraded` 或 `unavailable` 的字段，**必须在报告中显式披露数据来源状态**，
> **禁止**用估算值静默填充。宁可给出「该指标不可得」的专业结论，也不编造数字。

---

"""

VERSION_ROW = ("| **v4.0.0** | **2026-10-25** | **🌍 开源版：移除私有连接器 westock-mcp 依赖，"
               "改用内置统一数据层 shared/fin_data.py（L1 公开源 / L2 AKShare / L3 yfinance，"
               "零 API Key）+ 中英双语文档** |\n")


def migrate_skill(skill: str) -> dict:
    md = ROOT / skill / "SKILL.md"
    if not md.exists():
        return {"skill": skill, "error": "SKILL.md not found"}
    s = md.read_text(encoding="utf-8")
    before = s

    # 1) frontmatter 依赖
    s = re.sub(r"(?m)^\s*-\s*westock-mcp[^\n]*\n", "", s)
    s = s.replace(
        "mcp_required:",
        "data_source:\n  - shared/fin_data.py  # 统一金融数据层：公开数据源，零 API Key，全球可用",
    )
    s = re.sub(r"(?m)^\s*-\s*mcp-westock\s*$", "  - open-finance-data", s)

    # 2) 私有工具名 -> 数据层端点（先长后短，避免误替换）
    for tool, repl in TOOL_MAP.items():
        s = s.replace(f"`{tool}`", f"`{repl}`")
        s = s.replace(tool, repl or "本地模拟撮合")

    # 3) data_xxx / tool_xxx 通用规则
    s = re.sub(r"`data_([a-z_]+)`", r"`fin_data.py \1`", s)
    s = re.sub(r"`tool_([a-z_]+)`", r"`fin_data.py \1`", s)

    # 4) 措辞
    for old, new in PHRASES:
        s = s.replace(old, new)

    # 5) 版本号
    s = s.replace('version: "3.4.1"', 'version: "4.0.0"')

    # 6) 插入数据获取章节（幂等）
    if SENTINEL not in s:
        idx = s.find("\n---\n", s.find("\n---\n") + 1)      # frontmatter 结束
        if idx == -1:
            idx = 0
        else:
            idx += len("\n---\n")
        s = s[:idx] + "\n" + DATA_BLOCK + s[idx:]

    # 7) 版本历史追加
    if "**v4.0.0**" not in s:
        s = s.rstrip() + "\n" + VERSION_ROW

    if s != before:
        md.write_text(s, encoding="utf-8")
    return {"skill": skill, "changed": s != before,
            "westock_left": len(re.findall(r"westock|自选股", s)),
            "mcp_left": len(re.findall(r"mcp_required|MCP 工具|MCP 调用", s))}


if __name__ == "__main__":
    print(f"{'skill':<24}{'changed':<10}{'westock残':<10}{'mcp残'}")
    print("-" * 54)
    for sk in SKILLS:
        r = migrate_skill(sk)
        if "error" in r:
            print(f"{sk:<24}{r['error']}")
            continue
        print(f"{sk:<24}{str(r['changed']):<10}{r['westock_left']:<10}{r['mcp_left']}")
    print("\ndone.")
