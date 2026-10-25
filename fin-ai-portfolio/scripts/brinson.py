#!/usr/bin/env python3
"""Brinson 三因子业绩归因（配置/选股/交互）。

用途：fin-ai-portfolio Step3。输入周期收益与权重，输出各类贡献并校验守恒。
依赖：无（纯标准库，v3.3.0 去除 numpy 依赖，开箱即用）
用法：python scripts/brinson.py --pw 0.5,0.5 --bw 0.4,0.6 --pr 0.10,0.05 --br 0.08,0.03 --sectors 消费,科技
      （pw 组合各行业权重 / bw 基准行业权重 / pr 组合各行业收益 / br 基准各行业收益）
输出：JSON（配置贡献/选股贡献/交互贡献/合计，守恒校验）
"""
import argparse
import json
import sys


def parse(seq, name):
    try:
        return [float(x) for x in seq.split(",")]
    except ValueError:
        sys.exit(json.dumps({"error": f"{name} 必须为逗号分隔的数值"}, ensure_ascii=False))


NEG_VALUE_FLAGS = {"--pw", "--bw", "--pr", "--br", "--sectors"}


def normalize_negative_args(argv):
    """v3.4.1：允许 `--pr -0.08,0.05` 这种以负号开头的参数值。

    argparse 会把 `-0.08,0.05` 当成未知选项而报 "expected one argument"，
    而组合亏损是常态（业绩归因最常见的场景恰恰是负收益），
    过去必须由调用方手动改写成 `--pr=-0.08,...` 才能跑通。
    这里在解析前把 `--flag value` 改写为 `--flag=value`，两种写法都可用。
    """
    out, i = [], 0
    while i < len(argv):
        cur = argv[i]
        if (cur in NEG_VALUE_FLAGS and i + 1 < len(argv)
                and argv[i + 1].startswith("-") and not argv[i + 1].startswith("--")):
            out.append(cur + "=" + argv[i + 1])
            i += 2
            continue
        out.append(cur)
        i += 1
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--pw", required=True, help="组合行业权重，逗号分隔")
    p.add_argument("--bw", required=True, help="基准行业权重，逗号分隔")
    p.add_argument("--pr", required=True, help="组合行业收益，逗号分隔（可为负）")
    p.add_argument("--br", required=True, help="基准行业收益，逗号分隔（可为负）")
    p.add_argument("--sectors", default="", help="行业名，逗号分隔（可选，用于可读输出）")
    args = p.parse_args(normalize_negative_args(sys.argv[1:]))

    pw = parse(args.pw, "pw")
    bw = parse(args.bw, "bw")
    pr = parse(args.pr, "pr")
    br = parse(args.br, "br")
    if not (len(pw) == len(bw) == len(pr) == len(br)):
        sys.exit(json.dumps({"error": "四个序列长度必须一致"}, ensure_ascii=False))
    for name, arr in [("pw", pw), ("bw", bw)]:
        if abs(sum(arr) - 1.0) > 0.01:
            sys.exit(json.dumps({"error": f"{name} 权重之和必须为 1（当前 {sum(arr):.4f}）"},
                                ensure_ascii=False))

    alloc = [(pw[i] - bw[i]) * br[i] for i in range(len(pw))]            # 配置贡献
    select = [bw[i] * (pr[i] - br[i]) for i in range(len(pw))]           # 选股贡献
    interact = [(pw[i] - bw[i]) * (pr[i] - br[i]) for i in range(len(pw))]  # 交互贡献
    total = sum(alloc) + sum(select) + sum(interact)

    sectors = [s for s in args.sectors.split(",") if s] or [f"S{i + 1}" for i in range(len(pw))]
    if len(sectors) != len(pw):
        sectors = [f"S{i + 1}" for i in range(len(pw))]

    check = total - sum(pw[i] * pr[i] for i in range(len(pw))) \
        + sum(bw[i] * br[i] for i in range(len(bw)))
    print(json.dumps({
        "sectors": sectors,
        "allocation": [round(x, 4) for x in alloc],
        "selection": [round(x, 4) for x in select],
        "interaction": [round(x, 4) for x in interact],
        "summary": {
            "allocation_total": round(sum(alloc), 4),
            "selection_total": round(sum(select), 4),
            "interaction_total": round(sum(interact), 4),
            "excess_return": round(total, 4),
            "portfolio_return": round(sum(pw[i] * pr[i] for i in range(len(pw))), 4),
            "benchmark_return": round(sum(bw[i] * br[i] for i in range(len(bw))), 4),
            "conservation_check": round(check, 6),
            "conservation_passed": abs(check) < 1e-4,
        },
        "note": "conservation_check 应≈0（<1e-4），否则说明输入权重/收益不一致，禁止出报告",
        "engine": "stdlib",
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
