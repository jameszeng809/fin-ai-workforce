#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FinAI Digital Workforce · 开源自检脚本 Self-check for the open-source release.

用法 Usage:
    python tools/selfcheck.py            # 全量自检 everything
    python tools/selfcheck.py --quick    # 跳过联网冒烟 skip network smoke tests

检查项 Checks:
    1. 9 个员工目录与 SKILL.md 齐备 directory + SKILL.md completeness
    2. 无私有连接器残留 no proprietary connector residue
    3. 所有 scripts/*.py 语法可编译 all calculators compile
    4. 所有 data/*.json 合法 all JSON packs parse
    5. 数据层在线冒烟（可选）live data layer smoke test
"""
import argparse
import json
import pathlib
import py_compile
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
SKILLS = ["fin-ai-orchestrator", "fin-ai-researcher", "fin-ai-portfolio",
          "fin-ai-risk", "fin-ai-crisis", "fin-ai-news", "fin-ai-quant",
          "fin-ai-compliance", "fin-ai-execution"]
BANNED = ["westock-mcp", "mcp__westock", "portfolio_watchlist", "portfolio_paper_trade"]

ok, warn, fail = [], [], []


def record(bucket, msg):
    bucket.append(msg)
    print(f"  {'✅' if bucket is ok else ('⚠️ ' if bucket is warn else '❌')} {msg}")


def check_structure():
    print("\n[1/5] 目录结构 Directory structure")
    for s in SKILLS:
        d = ROOT / s
        if not d.is_dir():
            record(fail, f"{s}: 目录缺失 missing directory")
        elif not (d / "SKILL.md").is_file():
            record(fail, f"{s}: SKILL.md 缺失 missing")
        elif not (d / "README.md").is_file():
            record(warn, f"{s}: README.md 缺失 missing")
        else:
            lines = len((d / "SKILL.md").read_text(encoding="utf-8").splitlines())
            record(ok, f"{s}: OK ({lines} lines)")
    for extra in ["README.md", "README_EN.md", "LICENSE", "requirements.txt",
                  ".gitignore", "shared/fin_data.py", "templates/watchlist.example.json"]:
        if (ROOT / extra).exists():
            record(ok, f"root/{extra}")
        else:
            record(fail, f"root/{extra} 缺失 missing")


def check_residue():
    print("\n[2/5] 私有连接器残留 Proprietary connector residue")
    hits = []
    for sk in SKILLS:
        md = ROOT / sk / "SKILL.md"
        if not md.exists():
            continue
        text = md.read_text(encoding="utf-8")
        for line_no, line in enumerate(text.splitlines(), 1):
            if any(b in line for b in BANNED) and not line.strip().startswith("| **v"):
                hits.append(f"{sk}/SKILL.md:{line_no} -> {line.strip()[:70]}")
    if hits:
        for h in hits:
            record(fail, h)
    else:
        record(ok, "9 份 SKILL.md 均无私有连接器调用 no residue in any SKILL.md")


def check_scripts():
    print("\n[3/5] 脚本语法 Script compilation")
    total = 0
    for sk in SKILLS:
        for py in sorted((ROOT / sk / "scripts").glob("*.py")) if (ROOT / sk / "scripts").exists() else []:
            total += 1
            try:
                py_compile.compile(str(py), cfile=tempfile.mktemp(), doraise=True)
                record(ok, f"{py.relative_to(ROOT)}")
            except Exception as exc:
                record(fail, f"{py.relative_to(ROOT)}: {type(exc).__name__}: {exc}")
    for shared_py in [ROOT / "shared" / "fin_data.py"]:
        total += 1
        try:
            py_compile.compile(str(shared_py), cfile=tempfile.mktemp(), doraise=True)
            record(ok, f"{shared_py.relative_to(ROOT)}")
        except Exception as exc:
            record(fail, f"{shared_py.name}: {exc}")
    record(ok, f"共编译 {total} 个 Python 文件 compiled {total} files")


def check_json():
    print("\n[4/5] 数据文件 JSON packs")
    total = 0
    for jf in sorted(ROOT.rglob("*.json")):
        total += 1
        try:
            json.loads(jf.read_text(encoding="utf-8"))
            record(ok, f"{jf.relative_to(ROOT)}")
        except Exception as exc:
            record(fail, f"{jf.relative_to(ROOT)}: {exc}")
    record(ok, f"共校验 {total} 个 JSON validated {total} files")


def check_data_layer():
    print("\n[5/5] 数据层在线冒烟 Live data-layer smoke test")
    sys.path.insert(0, str(ROOT / "shared"))
    try:
        import fin_data
    except Exception as exc:
        record(fail, f"导入 fin_data 失败 import failed: {exc}")
        return
    probes = [("search", "600519"), ("quote", "sh600519"), ("kline", "sh600519"),
              ("finance", "sh600519"), ("index", "")]
    for ep, code in probes:
        try:
            r = fin_data.call(ep, code)
            if r["status"] == "ok":
                record(ok, f"{ep:<9} ok  ({r['source']}, {r['latency_ms']}ms)")
            elif r["status"] == "degraded":
                record(warn, f"{ep:<9} degraded ({r.get('note', '')[:50]})")
            else:
                record(warn, f"{ep:<9} unavailable ({r.get('note', '')[:50]})")
        except Exception as exc:
            record(fail, f"{ep:<9} crash {type(exc).__name__}: {exc}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true", help="skip network smoke test")
    args = ap.parse_args()

    print("=" * 66)
    print("  普惠金融数字员工团队 · 开源自检 self-check")
    print("  FinAI Digital Workforce · open-source self-check")
    print("=" * 66)

    check_structure()
    check_residue()
    check_scripts()
    check_json()
    if args.quick:
        print("\n[5/5] 跳过联网冒烟（--quick）skipped network smoke test")
    else:
        check_data_layer()

    print("\n" + "=" * 66)
    print(f"  ✅ 通过 passed : {len(ok)}")
    print(f"  ⚠️  降级 warn   : {len(warn)}")
    print(f"  ❌ 失败 failed : {len(fail)}")
    print("=" * 66)
    if fail:
        print("\n失败详情 failures:")
        for f in fail:
            print("  -", f)
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
