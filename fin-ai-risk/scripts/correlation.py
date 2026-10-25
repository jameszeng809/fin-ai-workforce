#!/usr/bin/env python3
"""相关性矩阵与协方差矩阵计算。

用途：fin-ai-quant Step3、fin-ai-portfolio Step5。输入各资产收益率序列（或由 LLM 从 data_kline 整理为 CSV 后传入）。
依赖：无（纯标准库，v3.3.0 去除 numpy 依赖，开箱即用）
用法：python scripts/correlation.py --returns-file returns.csv
      python scripts/correlation.py --returns-file returns.csv --labels 茅台,腾讯,宁德,特斯拉
      returns.csv 格式：无表头，每行一个交易日，每列一只股票，列为日收益率（小数）
输出：JSON（相关性矩阵、协方差矩阵日化/年化、高相关对 Top5）

v3.4.1 修正：high_corr_pairs 此前只返回列下标（如 {"pair":[2,3]}），调用方必须自行维护
"第几列对应哪只股票"的映射表，跨脚本传递时极易错位（风控官把第2列当腾讯，量化当宁德）。
新增 --labels：按 CSV 列序给出资产名，输出 pair_names 与 labels，让结论自解释。
"""
import argparse
import csv
import json
import math
import sys

MIN_DAYS_HARD = 40        # 低于此值拒绝计算（样本太少，协方差矩阵不可信）
MIN_DAYS_RECOMMEND = 60   # 低于此值出 warn：v3.4.1 起改为告警而非中止


def load_csv(path):
    rows = []
    with open(path, encoding="utf-8-sig", newline="") as f:
        for line in csv.reader(f):
            if not line or all(c.strip() == "" for c in line):
                continue
            rows.append([float(c) for c in line])
    if not rows:
        sys.exit(json.dumps({"error": "CSV 为空"}, ensure_ascii=False))
    width = len(rows[0])
    if any(len(r) != width for r in rows):
        sys.exit(json.dumps({"error": "CSV 各行列数不一致，请检查缺失值"}, ensure_ascii=False))
    return rows


def mean(vals):
    return sum(vals) / len(vals)


def cov_matrix(cols):
    n = len(cols)
    mu = [mean(c) for c in cols]
    m = len(cols[0])
    denom = m - 1 if m > 1 else 1  # 样本协方差（与 numpy.cov 默认 ddof=1 一致）
    out = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i, n):
            s = sum((cols[i][t] - mu[i]) * (cols[j][t] - mu[j]) for t in range(m)) / denom
            out[i][j] = s
            out[j][i] = s
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--returns-file", required=True, help="日收益率 CSV，无表头，行=交易日，列=股票")
    p.add_argument("--labels", default="",
                   help="资产名称，逗号分隔，按 CSV 列序（如 茅台,腾讯,宁德）；"
                        "不传则回落为 ASSET_0/ASSET_1 占位符")
    p.add_argument("--top-k", type=int, default=5, help="输出高相关对数量，默认 5")
    args = p.parse_args()

    try:
        rows = load_csv(args.returns_file)
    except ValueError as e:
        sys.exit(json.dumps({"error": f"解析失败，CSV 只能含数值: {e}"}, ensure_ascii=False))
    except OSError as e:
        sys.exit(json.dumps({"error": f"读取失败: {e}"}, ensure_ascii=False))

    n_days, n_assets = len(rows), len(rows[0])
    # v3.4.1：跨市场（A/港/美）组合按 SKILL 默认取 60 日 K 线时，交易日交集常只剩
    # 50-55 天，旧版一律 exit 1，导致风控/量化第一步就断链。现改为两级门槛：
    # 低于 HARD 才拒绝，低于 RECOMMEND 仅告警并继续（结果须披露样本天数）。
    if n_days < MIN_DAYS_HARD:
        sys.exit(json.dumps({
            "error": f"样本仅 {n_days} 个交易日，低于最低要求 {MIN_DAYS_HARD} 日",
            "n_days": n_days,
            "min_required": MIN_DAYS_HARD,
            "fix": "跨市场组合请把 K 线取数区间扩到 120 个交易日以上（A/港/美交集后仍可≥40）",
        }, ensure_ascii=False))
    if n_days < MIN_DAYS_RECOMMEND:
        print(f"[warn] 样本 {n_days} 个交易日 < 建议 {MIN_DAYS_RECOMMEND} 日，"
              f"相关性估计误差偏大，报告中须披露实际样本天数", file=sys.stderr)
    if n_assets < 2:
        sys.exit(json.dumps({"error": "至少需要 2 个资产才能计算相关性"}, ensure_ascii=False))

    cols = [[rows[t][i] for t in range(n_days)] for i in range(n_assets)]
    cov_d = cov_matrix(cols)
    sd = [math.sqrt(max(cov_d[i][i], 0.0)) for i in range(n_assets)]
    corr = [[0.0] * n_assets for _ in range(n_assets)]
    for i in range(n_assets):
        for j in range(n_assets):
            if sd[i] > 0 and sd[j] > 0:
                corr[i][j] = max(-1.0, min(1.0, cov_d[i][j] / (sd[i] * sd[j])))
            else:
                corr[i][j] = 1.0 if i == j else 0.0
    cov_y = [[cov_d[i][j] * 252 for j in range(n_assets)] for i in range(n_assets)]

    labels = [x.strip() for x in args.labels.split(",") if x.strip()] if args.labels else []
    if labels and len(labels) != n_assets:
        sys.exit(json.dumps({"error": f"--labels 给出 {len(labels)} 个名称，"
                                      f"但 CSV 有 {n_assets} 列，必须一一对应"},
                            ensure_ascii=False))
    display = labels if labels else [f"ASSET_{i}" for i in range(n_assets)]

    pairs = []
    for i in range(n_assets):
        for j in range(i + 1, n_assets):
            pairs.append({"pair": [i, j],
                          "pair_names": [display[i], display[j]],
                          "corr": round(corr[i][j], 3)})
    pairs.sort(key=lambda x: -x["corr"])

    print(json.dumps({
        "n_assets": n_assets,
        "n_days": n_days,
        "labels": display,
        "labels_source": "cli:--labels" if labels else "auto:ASSET_i占位符（建议传 --labels）",
        "corr_matrix": [[round(x, 3) for x in row] for row in corr],
        "cov_annualized": [[round(x, 5) for x in row] for row in cov_y],
        "high_corr_pairs": pairs[: args.top_k],
        "warning": ("存在相关性>0.85 的资产对，分散化效果存疑，报告必须提示"
                    if any(x["corr"] > 0.85 for x in pairs) else None),
        "engine": "stdlib",
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
