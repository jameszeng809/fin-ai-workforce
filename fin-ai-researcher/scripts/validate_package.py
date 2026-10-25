# -*- coding: utf-8 -*-
"""fin-ai-orchestrator / validate_package.py 的团队共用实现转发壳（v3.4.0）。

作战包契约校验。全队共用同一份 team_package.schema.json 数据契约。

本文件不含任何计算逻辑，只负责定位并调用「fin-ai-orchestrator」下的真实实现，
因此不存在多份副本漂移的风险——改共用实现，全队立即生效。

查找顺序：
  1. ../fin-ai-orchestrator/scripts/validate_package.py        （并列安装，最常见）
  2. 本 skill 内嵌副本 scripts/_vendored_validate_package.py
  3. 用户级技能目录 ~/.workbuddy/skills/@user_9bec034f/fin-ai-orchestrator/scripts/validate_package.py
  4. 系统临时/下载目录中的同名安装副本

全部找不到时输出可执行安装指引，而非裸 FileNotFoundError。
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OWNER = "fin-ai-orchestrator"
SCRIPT = "validate_package.py"

CANDIDATES = [
    os.path.join(HERE, "..", "..", OWNER, "scripts", SCRIPT),
    os.path.join(HERE, "_vendored_" + SCRIPT),
    os.path.join(os.path.expanduser("~"), ".workbuddy", "skills",
                 "@user_9bec034f", OWNER, "scripts", SCRIPT),
]

# 兜底：在常见安装根下搜索（限制深度，避免全盘扫描）
EXTRA_ROOTS = [
    os.path.join(os.path.expanduser("~"), ".workbuddy", "skills"),
    os.path.join(os.path.expanduser("~"), "AppData", "Local", "Temp"),
]


def find():
    for p in CANDIDATES:
        if os.path.isfile(p):
            return os.path.normpath(p)
    for root in EXTRA_ROOTS:
        if not os.path.isdir(root):
            continue
        for dirpath, _dirnames, filenames in os.walk(root):
            if SCRIPT in filenames and OWNER in dirpath:
                return os.path.join(dirpath, SCRIPT)
    return None


def main():
    target = find()
    if target is None:
        sys.stdout.write(json.dumps({
            "ok": False,
            "error": "未找到 fin-ai-orchestrator 的 validate_package.py",
            "detail": "本 skill 依赖团队共用实现，未单独内置副本（避免口径漂移）。",
            "fix": [
                "skillhub install fin-ai-orchestrator --namespace user_9bec034f --force",
                "或把 fin-ai-orchestrator 与本 skill 安装在同一父目录下",
            ],
            "degrade": "无法执行脚本时，须在报告中显式标注「未过脚本校验」，"
                       "不得凭 LLM 心算替代。",
        }, ensure_ascii=False))
        sys.stdout.write("\n")
        sys.exit(2)
    proc = subprocess.run([sys.executable, target] + sys.argv[1:])
    sys.exit(proc.returncode)


if __name__ == "__main__":
    main()
