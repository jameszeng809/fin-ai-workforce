#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Install the 9 digital employees into a WorkBuddy / CodeBuddy skills directory.

Why this exists
---------------
Every SKILL.md tells the agent to run::

    python shared/fin_data.py quote sh600519

but `shared/` lives at the **repository root**, not inside each skill folder.
Copying a single `fin-ai-*` folder into `~/.workbuddy/skills/` therefore
produces a skill whose documented data path does not exist - the employee boots
up and dies on its first tool call. This installer fixes that by planting the
shared data layer into every installed skill.

Usage
-----
    python install.py                      # auto-detect skills dir, install all
    python install.py --target <dir>       # explicit destination
    python install.py --namespace my-team  # sub-folder under the skills dir
    python install.py --dry-run            # show what would happen
    python install.py --uninstall          # remove previously installed copies
    python install.py --only fin-ai-risk,fin-ai-quant

Zero mandatory dependencies: standard library only, same rule as the data layer.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SHARED = os.path.join(HERE, "shared")
SKILL_PREFIX = "fin-ai-"

DEFAULT_NAMESPACES = ["@fin-ai-workforce"]
SKILL_ROOT_CANDIDATES = [
    os.path.expanduser("~/.workbuddy/skills"),
    os.path.expanduser("~/.codebuddy/skills"),
    os.path.expanduser("~/.claude/skills"),
]


# --------------------------------------------------------------------------- #
# discovery
# --------------------------------------------------------------------------- #
def discover_employees() -> list[str]:
    return sorted(d for d in os.listdir(HERE)
                  if d.startswith(SKILL_PREFIX)
                  and os.path.isfile(os.path.join(HERE, d, "SKILL.md")))


def detect_target(cli_target: str | None) -> str | None:
    if cli_target:
        return os.path.abspath(os.path.expanduser(cli_target))
    for root in SKILL_ROOT_CANDIDATES:
        if os.path.isdir(root):
            return root
    return None


# --------------------------------------------------------------------------- #
# installation
# --------------------------------------------------------------------------- #
def install_one(employee: str, dest_root: str, dry_run: bool) -> dict:
    src = os.path.join(HERE, employee)
    dst = os.path.join(dest_root, employee)
    actions = []

    if os.path.isdir(dst):
        actions.append("replace existing install")
    if dry_run:
        return {"employee": employee, "dest": dst, "actions": actions,
                "status": "dry-run"}

    if os.path.isdir(dst):
        for name in os.listdir(dst):
            p = os.path.join(dst, name)
            shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)
    os.makedirs(dst, exist_ok=True)

    # skill payload
    for name in os.listdir(src):
        s, d = os.path.join(src, name), os.path.join(dst, name)
        if os.path.isdir(s):
            shutil.copytree(s, d, dirs_exist_ok=True)
        else:
            shutil.copy2(s, d)

    # THE fix: plant the shared data layer inside the skill itself.
    if os.path.isdir(SHARED):
        shutil.copytree(SHARED, os.path.join(dst, "shared"), dirs_exist_ok=True)
        actions.append("planted shared/fin_data.py")

    return {"employee": employee, "dest": dst, "actions": actions,
            "status": "installed"}


def verify_install(dest_root: str, employees: list[str]) -> list[dict]:
    """Prove each installed employee can actually resolve its data layer."""
    report = []
    for emp in employees:
        base = os.path.join(dest_root, emp)
        trader = os.path.join(base, "shared", "fin_data.py")
        report.append({
            "employee": emp,
            "skill_md": os.path.isfile(os.path.join(base, "SKILL.md")),
            "data_layer": os.path.isfile(trader),
            "scripts": len([f for f in os.listdir(os.path.join(base, "scripts"))
                            if f.endswith(".py")]) if os.path.isdir(
                os.path.join(base, "scripts")) else 0,
        })
    return report


def uninstall(dest_root: str, employees: list[str]) -> list[str]:
    removed = []
    for emp in employees:
        dst = os.path.join(dest_root, emp)
        if os.path.isdir(dst):
            shutil.rmtree(dst)
            removed.append(emp)
    return removed


# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #
def main() -> int:
    ap = argparse.ArgumentParser(
        description="Install the FinAI digital workforce into your skills dir.")
    ap.add_argument("--target", help="destination skills directory")
    ap.add_argument("--namespace", default=DEFAULT_NAMESPACES[0],
                    help=f"sub-folder under the skills dir (default "
                         f"{DEFAULT_NAMESPACES[0]})")
    ap.add_argument("--no-namespace", action="store_true",
                    help="install directly into the skills dir, no sub-folder")
    ap.add_argument("--only", help="comma separated employee list")
    ap.add_argument("--uninstall", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--json", action="store_true", help="machine readable output")
    args = ap.parse_args()

    employees = discover_employees()
    if args.only:
        wanted = {x.strip() for x in args.only.split(",") if x.strip()}
        missing = wanted - set(employees)
        if missing:
            print(json.dumps({"ok": False,
                              "error": f"unknown employee(s): {sorted(missing)}",
                              "available": employees}, ensure_ascii=False))
            return 2
        employees = [e for e in employees if e in wanted]

    target = detect_target(args.target)
    if not target:
        print(json.dumps({
            "ok": False,
            "error": "no skills directory found",
            "checked": SKILL_ROOT_CANDIDATES,
            "fix": "pass --target <skills dir> explicitly"}, ensure_ascii=False))
        return 2

    dest_root = target if args.no_namespace else os.path.join(target, args.namespace)

    if args.uninstall:
        removed = uninstall(dest_root, employees)
        out = {"ok": True, "removed": removed, "dest": dest_root}
        print(json.dumps(out, ensure_ascii=False) if args.json else
              "removed: " + (", ".join(removed) or "(nothing)"))
        return 0

    if args.dry_run:
        out = {"ok": True, "dest": dest_root, "employees": employees,
               "note": "dry run, nothing written"}
        print(json.dumps(out, ensure_ascii=False, indent=1) if args.json else
              f"[dry-run] would install {len(employees)} employees into "
              f"{dest_root}")
        return 0

    os.makedirs(dest_root, exist_ok=True)
    results = [install_one(e, dest_root, args.dry_run) for e in employees]
    report = verify_install(dest_root, employees)

    # cross-skill delegation needs the whole team under one parent
    delegated = [r for r in report
                 if not r["skill_md"] or not r["data_layer"]]
    payload = {
        "ok": not delegated,
        "dest": dest_root,
        "installed": employees,
        "count": len(employees),
        "verification": report,
        "broken": [r["employee"] for r in delegated],
        "next": "run: python " + os.path.join(
            dest_root, employees[0], "shared", "fin_data.py").replace("\\", "/")
                + " quote sh600519",
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=1))
    else:
        print(f"installed {len(employees)} employees -> {dest_root}\n")
        print(f"{'employee':<22}{'SKILL.md':<11}{'data layer':<12}scripts")
        print("-" * 56)
        for r in report:
            print(f"{r['employee']:<22}{str(r['skill_md']):<11}"
                  f"{str(r['data_layer']):<12}{r['scripts']}")
        print()
        if delegated:
            print("BROKEN:", ", ".join(payload["broken"]))
            return 1
        print(payload["next"])
    return 0 if not delegated else 1


if __name__ == "__main__":
    sys.exit(main())
