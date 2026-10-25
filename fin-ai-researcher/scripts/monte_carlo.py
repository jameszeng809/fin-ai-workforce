#!/usr/bin/env python3
"""估值蒙特卡洛模拟：输出估值分布而非点估计。

用途：fin-ai-researcher Step7.1 蒙特卡洛敏感性、fin-ai-risk Step4 VaR 的分布基础。
依赖：无（纯标准库，v3.3.0 去除 numpy 依赖，开箱即用）
用法：python scripts/monte_carlo.py --base 1087 --wacc 0.09 --wacc-sd 0.01 --g 0.03 --g-sd 0.005 --margin-sd 0.02 --n 10000
      （对 WACC/g/利润率施加正态扰动，输出估值分布统计量）
输出：JSON（均值/标准差/95%置信区间/各分位数）
"""
import argparse
import json
import math
import random
import sys

# WACC/g 弹性由 DCF 泰勒展开标定，改动需重跑基准并在此注明依据
WACC_ELASTICITY, G_ELASTICITY = -8.0, 6.0
SEED = 42  # 固定种子保证结果可复现


def mean(vals):
    return sum(vals) / len(vals)


def pstd(vals):
    """总体标准差（与 numpy 默认 ddof=0 一致）。"""
    m = mean(vals)
    return math.sqrt(sum((x - m) ** 2 for x in vals) / len(vals))


def percentile(vals, q):
    """线性插值分位数（与 numpy.percentile 默认 linear 一致）。vals 需已升序。"""
    if not vals:
        return 0.0
    if len(vals) == 1:
        return vals[0]
    pos = (len(vals) - 1) * (q / 100.0)
    lo = math.floor(pos)
    hi = math.ceil(pos)
    if lo == hi:
        return vals[int(pos)]
    return vals[lo] * (hi - pos) + vals[hi] * (pos - lo)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--base", type=float, required=True, help="基准估值（如 DCF 每股价值）")
    p.add_argument("--wacc", type=float, required=True)
    p.add_argument("--wacc-sd", type=float, default=0.01, help="WACC 扰动标准差，默认 0.01")
    p.add_argument("--g", type=float, required=True)
    p.add_argument("--g-sd", type=float, default=0.005, help="永续增长率扰动标准差")
    p.add_argument("--margin-sd", type=float, default=0.02, help="利润率扰动对估值的一阶弹性标准差")
    p.add_argument("--n", type=int, default=10000, help="模拟次数，默认 10000")
    args = p.parse_args()

    if args.base <= 0:
        sys.exit(json.dumps({"error": "基准估值必须为正"}, ensure_ascii=False))
    if args.n < 1000:
        sys.exit(json.dumps({"error": "模拟次数至少 1000，否则分布无统计意义"}, ensure_ascii=False))
    rng = random.Random(SEED)  # 固定种子保证结果可复现

    vals = []
    for _ in range(args.n):
        wacc = min(max(rng.gauss(args.wacc, args.wacc_sd), 0.03), 0.30)
        # v3.3.0 修正：g 上限随本次抽样的 wacc 走，杜绝出现 g >= wacc 的无效样本
        g = min(max(rng.gauss(args.g, args.g_sd), 0.0), wacc - 0.005)
        margin = rng.gauss(0, args.margin_sd)
        # 一阶近似：估值对 WACC 弹性约 -8（久期效应），对 g 弹性约 +6，对利润率弹性 +1
        vals.append(args.base * (1 + WACC_ELASTICITY * (wacc - args.wacc)
                                 + G_ELASTICITY * (g - args.g) + margin))

    vals.sort()
    print(json.dumps({
        "n": args.n,
        "seed": SEED,
        "mean": round(mean(vals), 1),
        "std": round(pstd(vals), 1),
        "p05": round(percentile(vals, 5), 1),
        "p25": round(percentile(vals, 25), 1),
        "median": round(percentile(vals, 50), 1),
        "p75": round(percentile(vals, 75), 1),
        "p95": round(percentile(vals, 95), 1),
        "ci95": [round(percentile(vals, 2.5), 1), round(percentile(vals, 97.5), 1)],
        "engine": "stdlib-random(seed=42)",
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
