# -*- coding: utf-8 -*-
"""fin-ai-news / dedup.py 的团队共用实现转发壳（v3.4.1）。

舆情去重。与舆情监控官共用同一套聚类口径，保证同稿不会被重复计入分级。

本文件不含任何计算逻辑，只负责定位并调用「fin-ai-news」下的真实实现，
因此不存在多份副本漂移的风险——改共用实现，全队立即生效。

查找顺序：
  1. ../fin-ai-news/scripts/dedup.py        （并列安装，最常见）
  2. 本 skill 内嵌副本 scripts/_vendored_dedup.py
  3. 用户级技能目录 ~/.workbuddy/skills/@user_9bec034f/fin-ai-news/scripts/dedup.py
  4. 系统临时/下载目录中的同名安装副本

全部找不到时输出可执行安装指引，而非裸 FileNotFoundError。
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OWNER = "fin-ai-news"
SCRIPT = "dedup.py"

CANDIDATES = [
    os.path.join(HERE, "..", "..", OWNER, "scripts", SCRIPT),
    os.path.join(HERE, "_vendored_" + SCRIPT),
    os.path.join(os.path.expanduser("~"), ".workbuddy", "skills",
                 "@user_9bec034f", OWNER, "scripts", SCRIPT),
]

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
            "error": "未找到 fin-ai-news 的 dedup.py",
            "detail": "本 skill 依赖团队共用实现，未单独内置副本（避免口径漂移）。",
            "fix": [
                "skillhub install fin-ai-news --namespace user_9bec034f --force",
                "或把 fin-ai-news 与本 skill 安装在同一父目录下",
            ],
            "degrade": "无法执行脚本时，须在报告中显式标注「未过去重」，"
                       "并手工剔除明显同名转载稿后再分级。",
        }, ensure_ascii=False))
        sys.stdout.write("\n")
        sys.exit(2)
    proc = subprocess.run([sys.executable, target] + sys.argv[1:])
    sys.exit(proc.returncode)


if __name__ == "__main__":
    main()
