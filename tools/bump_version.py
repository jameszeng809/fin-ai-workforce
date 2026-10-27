#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Bump every employee to the target version and append a changelog row.

Run from the repository root. Edit NEW / DATE / ROW above, then:

    python tools/bump_version.py
"""
import json
import pathlib
import re

NEW = "4.3.0"
DATE = "2026-10-27"
ROW = (
    f"| **v{NEW}** | **{DATE}** | **🔗 跨员工联动版：修复「量化→风控」链路断裂——公募双十口径下"
    "股票池常不满仓，风控官却硬要求权重和为 1，整条流水线直接报错；现为 VaR / 压力测试新增"
    "--cash 现金仓位，并要求「权重 + 现金 = 1」，现金按零波动计入，历史情景冲击按权益暴露折算"
    "（30% 仓位下 2015 股灾损失由 -42.75% 修正为 -13.5%）；端到端演练改为真实传递组合权重，"
    "不再用单资产绕过 |"
)

root = pathlib.Path(".")
bumped = []

for meta in sorted(root.glob("fin-ai-*/_meta.json")):
    d = json.loads(meta.read_text(encoding="utf-8"))
    d["version"] = NEW
    meta.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8")
    bumped.append(meta.parent.name)

for skill in sorted(root.glob("fin-ai-*/SKILL.md")):
    s = skill.read_text(encoding="utf-8")
    # frontmatter version
    s2 = re.sub(r'^version:\s*"[^"]*"', f'version: "{NEW}"', s, count=1,
                flags=re.M)
    # append changelog row after the header line of the changelog table
    if ROW.split("|")[1].strip() not in s2:
        m = re.search(r"(\|\s*-{3,}\s*\|\s*-{3,}\s*\|\s*-{3,}\s*\|\s*\n)", s2)
        if m:
            s2 = s2[:m.end()] + ROW + "\n" + s2[m.end():]
        else:
            print(f"  ! no changelog table found in {skill}")
    skill.write_text(s2, encoding="utf-8")

print(f"bumped {len(bumped)} employees -> v{NEW}")
for b in bumped:
    print("  ", b)
