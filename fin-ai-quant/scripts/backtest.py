#!/usr/bin/env python3
"""策略回测引擎（月度调仓，防前视偏差）。

用途：fin-ai-quant Step7 策略级回测、fin-ai-portfolio Step10 组合调仓建议回测、
      fin-ai-orchestrator 场景模板 D 的计算核心。
依赖：无（纯标准库，v3.3.0 去除 numpy 依赖，开箱即用）
用法：python scripts/backtest.py --prices-file prices.csv --signals-file signals.csv
             [--benchmark-file hs300.csv] [--benchmark-col N] [--cost 0.0015]
      prices.csv：无表头，行=交易日，列=股票，收盘价（前复权）
      signals.csv：与 prices 同形状，行=调仓日，值=目标权重（0-1），列对应股票
      信号约定（防前视）：signals 第 j 行 = 第 j 日收盘时点可确定的目标权重，
      用于第 j→j+1 日的收益（收盘调仓惯例）；非调仓行填 nan/空
      --benchmark-file：单列 CSV（如沪深300），行数与 prices 一致【推荐】
输出：JSON（累计收益/年化/夏普/最大回撤/分年度收益/换手率）

v3.3.1 重要修正：
  1. 基准默认由「最后一列」改为「不指定」。旧版 --benchmark-col 默认 -1，会把最后一只
     持仓股当基准、并从组合里剔除，导致组合少一只股票且超额收益对标单只个股，结论失真。
     未指定基准时 excess_return / benchmark_annual_return 输出 null，禁止拿总收益当 alpha。
  2. 成本摊销由写死 /21（月度）改为「实际平均调仓间隔」，修复日频/季频调仓的交易成本低估。
"""
import argparse
import csv
import json
import math
import sys

TRADING_DAYS = 244  # A股年均交易日，非 252，改用其他市场需显式指定


def load_csv(path):
    rows = []
    with open(path, encoding="utf-8-sig", newline="") as f:
        for line in csv.reader(f):
            if not line or all(c.strip() == "" for c in line):
                continue
            rows.append([float(c) if c.strip() and c.strip().lower() != "nan" else float("nan")
                         for c in line])
    if not rows:
        sys.exit(json.dumps({"error": f"{path} 为空"}, ensure_ascii=False))
    width = len(rows[0])
    if any(len(r) != width for r in rows):
        sys.exit(json.dumps({"error": f"{path} 各行列数不一致"}, ensure_ascii=False))
    return rows


def is_nan(x):
    return x != x


def mean(vals):
    return sum(vals) / len(vals) if vals else 0.0


def pstd(vals):
    if len(vals) < 2:
        return 0.0
    m = mean(vals)
    return math.sqrt(sum((x - m) ** 2 for x in vals) / len(vals))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--prices-file", required=True)
    p.add_argument("--signals-file", required=True)
    p.add_argument("--benchmark-col", type=int, default=None,
                   help="基准列索引（该列会被剔除出持仓）。v3.3.1 起默认为 None："
                        "不再默认拿最后一只持仓股当基准")
    p.add_argument("--benchmark-file", default=None,
                   help="基准价格文件（单列 CSV，行数与 prices 一致，如沪深300）。"
                        "推荐用此参数而非 --benchmark-col")
    p.add_argument("--cost", type=float, default=0.0015,
                   help="单边交易成本，默认 0.0015（佣金+冲击近似）")
    args = p.parse_args()

    try:
        prices = load_csv(args.prices_file)
        signals = load_csv(args.signals_file)
    except ValueError as e:
        sys.exit(json.dumps({"error": f"解析失败，CSV 只能含数值或 nan: {e}"}, ensure_ascii=False))
    except OSError as e:
        sys.exit(json.dumps({"error": f"读取失败: {e}"}, ensure_ascii=False))

    if len(prices) != len(signals) or len(prices[0]) != len(signals[0]):
        sys.exit(json.dumps({"error": "prices 与 signals 形状必须一致"}, ensure_ascii=False))
    if any(x <= 0 for row in prices for x in row):
        sys.exit(json.dumps({"error": "价格含非正值，请检查复权处理"}, ensure_ascii=False))
    for row in signals:
        for x in row:
            if not is_nan(x) and (x > 1.0 or x < 0):
                sys.exit(json.dumps({"error": "信号权重必须在 [0,1]"}, ensure_ascii=False))

    # v3.3.1：基准必须显式指定。旧版默认 -1（最后一列）会把最后一只持仓股当基准并踢出组合，
    # 导致组合少一只股票、超额收益对标单只个股，结论完全失真。
    bench_prices = None
    if args.benchmark_file:
        b = load_csv(args.benchmark_file)
        if len(b) != len(prices):
            sys.exit(json.dumps({"error": "benchmark-file 行数必须与 prices 一致"},
                                ensure_ascii=False))
        if len(b[0]) != 1:
            sys.exit(json.dumps({"error": "benchmark-file 必须为单列"}, ensure_ascii=False))
        bench_prices = [row[0] for row in b]
        keep = list(range(len(prices[0])))
    elif args.benchmark_col is not None:
        bench_col = (args.benchmark_col if args.benchmark_col >= 0
                     else len(prices[0]) + args.benchmark_col)
        if not (0 <= bench_col < len(prices[0])):
            sys.exit(json.dumps({"error": "benchmark-col 越界"}, ensure_ascii=False))
        bench_prices = [row[bench_col] for row in prices]
        keep = [i for i in range(len(prices[0])) if i != bench_col]
    else:
        keep = list(range(len(prices[0])))
    if not keep:
        sys.exit(json.dumps({"error": "剔除基准列后无资产可回测"}, ensure_ascii=False))

    rets = [[prices[t + 1][i] / prices[t][i] - 1.0 for i in range(len(prices[0]))]
            for t in range(len(prices) - 1)]
    n_days = len(rets)
    if n_days < 2:
        sys.exit(json.dumps({"error": "样本不足 2 个交易日，无法回测"}, ensure_ascii=False))
    bench = None
    if bench_prices is not None:
        bench = [bench_prices[t + 1] / bench_prices[t] - 1.0 for t in range(len(bench_prices) - 1)]
    # signals[j] 用于 j→j+1 收益：天然防前视（第 j 日收盘才可确定）
    asset_signals = [[signals[t][i] for i in keep] for t in range(n_days)]
    asset_rets = [[r[i] for i in keep] for r in rets]

    weights = [0.0] * len(keep)
    port_rets, turnovers = [], []
    for t in range(n_days):
        row = asset_signals[t]
        if not all(is_nan(x) for x in row):        # 该行为调仓日
            new_w = [0.0 if is_nan(x) else x for x in row]
            s = sum(new_w)
            if s > 0:
                new_w = [x / s for x in new_w]
            turnovers.append(sum(abs(new_w[i] - weights[i]) for i in range(len(keep))))
            weights = new_w
        port_rets.append(sum(weights[i] * asset_rets[t][i] for i in range(len(keep))))

    if not turnovers:
        sys.exit(json.dumps({"error": ("signals 中无任何有效调仓行（全为 nan），"
                                       "请至少给出一个调仓日的目标权重")}, ensure_ascii=False))

    # v3.3.1：成本摊销改用「实际平均调仓间隔」。旧版写死 /21（月度），
    # 日频调仓时会把成本低估约 21 倍、季频则高估，直接污染净收益与夏普。
    rebal_interval = n_days / len(turnovers)
    cost_drag = mean(turnovers) * args.cost / rebal_interval
    port_rets_net = [x - cost_drag for x in port_rets]

    nav, nav_b, peak, max_dd = 1.0, 1.0, 1.0, 0.0
    for t in range(n_days):
        nav *= (1 + port_rets_net[t])
        if bench is not None:
            nav_b *= (1 + bench[t])
        peak = max(peak, nav)
        max_dd = min(max_dd, nav / peak - 1.0)

    ann_ret = nav ** (TRADING_DAYS / n_days) - 1.0
    ann_vol = pstd(port_rets_net) * math.sqrt(TRADING_DAYS)
    sharpe = ann_ret / ann_vol if ann_vol > 0 else 0.0
    bench_ret = (nav_b ** (TRADING_DAYS / n_days) - 1.0) if bench is not None else None

    yearly = {}
    for y in range(n_days // TRADING_DAYS + 1):
        seg = port_rets_net[y * TRADING_DAYS:(y + 1) * TRADING_DAYS]
        if len(seg) > 10:
            acc = 1.0
            for x in seg:
                acc *= (1 + x)
            yearly[f"year_{y + 1}"] = round(acc - 1, 4)

    print(json.dumps({
        "days": n_days,
        "rebalances": len(turnovers),
        "total_return": round(nav - 1, 4),
        "annual_return": round(ann_ret, 4),
        "benchmark_annual_return": round(bench_ret, 4) if bench_ret is not None else None,
        "excess_return": (round(ann_ret - bench_ret, 4) if bench_ret is not None else None),
        "benchmark_note": ("未指定基准（--benchmark-file 或 --benchmark-col），"
                           "超额收益不可计算，已置 null；请勿把总收益当作 alpha"
                           if bench_ret is None else "基准已显式指定"),
        "annual_volatility": round(ann_vol, 4),
        "sharpe": round(sharpe, 3),
        "max_drawdown": round(max_dd, 4),
        "avg_turnover_per_rebalance": round(mean(turnovers), 4),
        "yearly_returns": yearly,
        "assumptions": {"cost_one_side": args.cost,
                        "actual_avg_rebalance_interval_days": round(rebal_interval, 1),
                        "trading_days": TRADING_DAYS},
        "note": ("SimBroker 全额成交无滑点，结果用于策略间横向比较，"
                 "不代表可实现收益（对标 ai-hedge-fund SimBroker 声明）"),
        "engine": "stdlib",
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
