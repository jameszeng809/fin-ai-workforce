#!/usr/bin/env python3
"""组合 VaR / CVaR 蒙特卡洛估算。

用途：fin-ai-risk Step4。历史波动率与权重由调用方（LLM）从 data_kline 整理后传入本脚本。
依赖：无（纯标准库，v3.3.0 去除 numpy 依赖，开箱即用）
用法：python scripts/var.py --weights 0.3,0.3,0.4 --vols 0.25,0.30,0.20 --corr "1,0.6,0.2;0.6,1,0.3;0.2,0.3,1" --n 10000
      （weights 组合权重；vols 各股年化波动率；corr 分号分隔的行、逗号分隔的列）
输出：JSON（VaR95/VaR99/CVaR99，1日与10日）
"""
import argparse
import json
import math
import random
import sys

SEED = 42


def parse_corr(text, n):
    rows = [r.strip() for r in text.split(";") if r.strip()]
    mat = [[float(x) for x in r.split(",")] for r in rows]
    if len(mat) != n or any(len(r) != n for r in mat):
        sys.exit(json.dumps({"error": f"corr 矩阵应为 {n}x{n}"}, ensure_ascii=False))
    # 对称性校验：相关性矩阵必须对称，否则 Cholesky 无意义
    for i in range(n):
        for j in range(n):
            if abs(mat[i][j] - mat[j][i]) > 1e-6:
                sys.exit(json.dumps({"error": f"corr 矩阵非对称：({i},{j}) != ({j},{i})"},
                                    ensure_ascii=False))
    return mat


def cholesky(mat, n):
    """Cholesky 分解；失败即说明矩阵非正定（含负特征值）。返回下三角矩阵 L。"""
    L = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1):
            s = sum(L[i][k] * L[j][k] for k in range(j))
            if i == j:
                val = mat[i][i] - s
                if val <= 1e-12:
                    return None
                L[i][j] = math.sqrt(val)
            else:
                L[i][j] = (mat[i][j] - s) / L[j][j]
    return L


def percentile(vals, q):
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
    p.add_argument("--weights", required=True, help="逗号分隔权重，和须为 1")
    p.add_argument("--vols", required=True, help="逗号分隔年化波动率")
    p.add_argument("--corr", required=True, help="分号分隔的相关性矩阵")
    p.add_argument("--n", type=int, default=10000)
    args = p.parse_args()

    w = [float(x) for x in args.weights.split(",")]
    vols = [float(x) for x in args.vols.split(",")]
    if len(w) != len(vols):
        sys.exit(json.dumps({"error": "weights 与 vols 长度不一致"}, ensure_ascii=False))
    if abs(sum(w) - 1.0) > 0.01:
        sys.exit(json.dumps({"error": "权重之和必须为 1"}, ensure_ascii=False))
    n = len(w)
    corr = parse_corr(args.corr, n)

    # 年化协方差 → 日化：cov_d[i][j] = vol_i * vol_j * corr_ij / 252
    cov = [[vols[i] * vols[j] * corr[i][j] / 252.0 for j in range(n)] for i in range(n)]
    L = cholesky(cov, n)
    if L is None:
        sys.exit(json.dumps({"error": "相关性/协方差矩阵非正定，请检查输入"}, ensure_ascii=False))

    rng = random.Random(SEED)
    losses = []
    for _ in range(args.n):
        z = [rng.gauss(0.0, 1.0) for _ in range(n)]
        # 多元正态样本 = L @ z
        daily = [sum(L[i][k] * z[k] for k in range(n)) for i in range(n)]
        port = sum(daily[i] * w[i] for i in range(n))
        losses.append(-port)
    losses.sort()

    var95 = percentile(losses, 95)
    var99 = percentile(losses, 99)
    tail = [x for x in losses if x >= var99]
    cvar99 = sum(tail) / len(tail) if tail else var99

    print(json.dumps({
        "n": args.n,
        "seed": SEED,
        "var_95_1d": round(var95, 4),
        "var_99_1d": round(var99, 4),
        "cvar_99_1d": round(cvar99, 4),
        "var_95_10d": round(var95 * math.sqrt(10), 4),
        "note": "输出为损失比例；正态假设低估尾部，极端情景请配合 scenarios.json 压力测试使用",
        "engine": "stdlib-cholesky(seed=42)",
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
