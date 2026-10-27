#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Bump every employee to the target version and append a changelog row.

Run from the repository root. Edit NEW / DATE / ROW above, then:

    python tools/bump_version.py
"""
import json
import pathlib
import re

NEW = "4.2.0"
DATE = "2026-10-27"
ROW = (
    f"| **v{NEW}** | **{DATE}** | **🌐 全市场打通版：新增港股财报通道（东财 HKF10 利润表长表转置，"
    "已用腾讯/阿里/美团真实年报核对）；新增 fx 汇率通道，修复「港股 HKD 报价 vs 人民币财报」"
    "跨币种直接相除导致的系统性约 15% 低估；新增 DCF 方法适用性护栏（偏离现价 >50% 时主动"
    "声明不宜作主结论）；修复 DCF 跳过时结论行仍打印『DCF 中枢』的误导文案 |"
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
