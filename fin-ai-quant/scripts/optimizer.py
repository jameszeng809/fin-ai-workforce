#!/usr/bin/env python3
"""组合优化：Markowitz 最小方差 + 风险平价，输出可执行目标权重。

用途：fin-ai-quant Step4/Step5。输入年化协方差矩阵 CSV（可选预期收益 CSV 做 Markowitz 目标收益约束）。
依赖：无（纯标准库，v3.3.0 去除 numpy 依赖，开箱即用）
用法：python scripts/optimizer.py --cov-file cov_annual.csv --mode risk_parity
      python scripts/optimizer.py --cov-file cov_annual.csv --mode markowitz --mu-file mu.csv --target-return 0.12
      python scripts/optimizer.py --cov-file cov_annual.csv --mode risk_parity --policy discretionary
      python scripts/optimizer.py --cov-file cov_annual.csv --mode risk_parity --max-position 0.20 --cash-cap 0.10
输出：JSON（各 mode 最优权重、组合波动率、现金权重、夹逼解释）

v3.3.0 重要修正：单票 10% 上限截断后**不再强制归一化回 100%**——被夹掉的份额归现金，
与 fin-ai-risk 硬夹逼"Conviction requests, risk disposes"口径一致；旧版强制归一化会在
股票池 < 10 只时死循环并直接报错退出。

v3.4.1 重要修正（配置装饰化 + 约束可解释）：
  1. MAX_POSITION 不再是写死的单一常量。旧版在 4 只股票池上必然产出「每只 10% + 现金
     60%」，观众会问「为什么六成是现金」——这不是优化失败，而是 PL-01 法规约束的必然
     结果，必须显式算给用户看。现改为策略口径驱动（--policy），并输出 cash_explanation
     与 pool_hint（达到目标现金比例所需的股票池数量）。
  2. 新增 --cash-cap：指定现金上限后启用瀑布式回填（waterfall），把超限现金按未触限
     资产权重回填，最多迭代 50 轮；默认关闭以保持与 fin-ai-risk 硬夹逼口径一致。
  3. 新增 Markowitz 可达性诊断：先算约束下理论最高收益 max_feasible_return，再判目标
     是否可达；旧版只在算完之后才发现 infeasible，且没有告诉用户可改成什么目标。
"""
import argparse
import csv
import json
import math
import sys

# 单票上限按「策略口径」区分——同是 10%，公募是法规红线，专户只是内部风控，
# 混为一谈会让演示结果无法解释。
POLICY_MAX_POSITION = {
    "public_fund": 0.10,    # 公开募集：《运作管理办法》第三十二条，红线，不可覆盖
    "discretionary": 0.25,  # 专户/高端投顾：内部风控制度，可用 --max-position 覆盖
    "demo": 0.35,           # 演示/教学：便于展示满仓效果，报告中须注明口径
}
DEFAULT_POLICY = "public_fund"   # 默认取最严口径，安全优先
MAX_ITER = 10000
WATERFALL_MAX_ROUNDS = 50


def load_matrix(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        rows = [[float(c) for c in r] for r in csv.reader(f) if r and any(x.strip() for x in r)]
    if not rows:
        sys.exit(json.dumps({"error": "协方差矩阵 CSV 为空"}, ensure_ascii=False))
    n = len(rows)
    if any(len(r) != n for r in rows):
        sys.exit(json.dumps({"error": "协方差矩阵必须为方阵"}, ensure_ascii=False))
    return rows


def load_vector(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        vals = []
        for r in csv.reader(f):
            vals.extend(float(c) for c in r if c.strip())
    if not vals:
        sys.exit(json.dumps({"error": "预期收益 CSV 为空"}, ensure_ascii=False))
    return vals


def mat_vec(m, v):
    return [sum(m[i][j] * v[j] for j in range(len(v))) for i in range(len(m))]


def quad_form(w, m):
    return sum(w[i] * m[i][j] * w[j] for i in range(len(w)) for j in range(len(w)))


def solve(m, b):
    """高斯-约当消元解线性方程组 m @ x = b；奇异返回 None。"""
    n = len(m)
    a = [row[:] + [b[i]] for i, row in enumerate(m)]
    for col in range(n):
        piv = max(range(col, n), key=lambda r: abs(a[r][col]))
        if abs(a[piv][col]) < 1e-14:
            return None
        a[col], a[piv] = a[piv], a[col]
        pv = a[col][col]
        for r in range(n):
            if r == col:
                continue
            factor = a[r][col] / pv
            if factor:
                for c in range(col, n + 1):
                    a[r][c] -= factor * a[col][c]
    return [a[i][n] / a[i][i] for i in range(n)]


def invert(m):
    n = len(m)
    cols = []
    for k in range(n):
        e = [1.0 if i == k else 0.0 for i in range(n)]
        col = solve(m, e)
        if col is None:
            return None
        cols.append(col)
    return [[cols[j][i] for j in range(n)] for i in range(n)]


def clip_to_limit(w, max_position):
    """截断到 [0, max_position]，超出部分归现金（不重新分配）；返回 (权重, 现金权重)。"""
    w = [min(max(x, 0.0), max_position) for x in w]
    total = sum(w)
    if total > 1.0 + 1e-12:  # 理论上不会发生（单票已上限），保险起见等比压缩
        w = [x / total for x in w]
        total = 1.0
    return w, round(1.0 - total, 6)


def waterfall(w, max_position, cash_cap):
    """瀑布式回填：把超出 cash_cap 的现金按未触限资产权重回填，使现金 ≤ cash_cap。

    v3.4.1 新增。触发条件是 cash_cap 显式给出；若不触发则以 (w, cash, 0, None) 原样返回。
    回填后仍低于目标（所有资产都触到单票上限）则停止，并返回原因——否则用户会误以为
    回填功能坏了，实际是「数学上无处可填」。
    """
    if cash_cap is None:
        return w, round(1.0 - sum(w), 6), 0, None
    rounds, reason = 0, None
    for _ in range(WATERFALL_MAX_ROUNDS):
        cash = 1.0 - sum(w)
        if cash <= cash_cap + 1e-9:
            reason = None if rounds else "no_change_needed"
            break
        free = [i for i in range(len(w)) if w[i] < max_position - 1e-12]
        if not free:
            reason = ("all_assets_at_cap:全部标的均已触及单票上限，现金无处可填。"
                      f"要降低现金必须扩大股票池或提高单票上限（当前 {max_position:.0%}）")
            break
        room = {i: max_position - w[i] for i in free}
        give = cash - cash_cap
        base = sum(w[i] for i in free)
        for i in free:
            share = (w[i] / base) if base > 1e-12 else 1.0 / len(free)
            add = min(share * give, room[i])
            w[i] += add
        rounds += 1
    else:
        reason = "max_rounds_reached"
    w = [min(max(x, 0.0), max_position) for x in w]
    return w, round(1.0 - sum(w), 6), rounds, reason


def explain_cash(cash, n, max_position, policy):
    """把『为什么这么多现金』翻译成人话 + 可行动建议（v3.4.1）。"""
    capacity = round(n * max_position, 4)
    water = None
    if cash > 1e-6:
        water = (f"当前股票池 {n} 只 × 单票上限 {max_position:.0%} = 可投上限 {capacity:.0%}，"
                 f"剩余 {cash:.0%} 只能是现金。这不是优化失败，而是"
                 f"{'《公开募集证券投资基金运作管理办法》第三十二条的强制结果' if policy == 'public_fund' else '当前口径下单票上限的直接结果'}。")
    hint = None
    if cash > 0.20:
        need = math.ceil((1.0 - 0.10) / max_position)
        hint = (f"若不希望出现高现金，请二选一：① 把股票池扩大到 ≥{need} 只（法规口径下）；"
                f"② 切换口径 --policy discretionary 或 --max-position 自行设定。"
                f"‘六成现金’是常用演示吐槽点，报告中必须提前解释，不要等观众问。")
    return {
        "weight_capacity_under_policy": capacity,
        "cash_explanation": water,
        "pool_hint": hint,
    }


def max_feasible_return(mu, max_position, cash_cap):
    """约束下理论最高收益：把权重优先分配给 μ 最高者。用于判定目标收益是否数学可达。

    口径与 achievable_return_on_invested 一致 —— 均为「投入资本的加权平均收益」，
    即 Σ(w_i·μ_i)/Σw_i。v3.4.1 修正：旧原型漏除以实际投入，导致上界被系统性低估
    （出现过「可达 7.40% 但宣称上限 2.96%」的自相矛盾输出）。
    """
    budget = 1.0 if cash_cap is None else 1.0 - cash_cap
    order = sorted(range(len(mu)), key=lambda i: -mu[i])
    left, ret, used = budget, 0.0, 0.0
    for i in order:
        take = min(max_position, left)
        if take <= 1e-12:
            break
        ret += take * mu[i]
        used += take
        left -= take
    return ret / used if used > 1e-12 else 0.0


def diagnose_mu(mu, target, max_position, cash_cap):
    """μ 诊断：样本均值直接年化是 Markowitz 最脆弱的输入，必须显式披露。"""
    n_neg = sum(1 for x in mu if x < 0)
    upper = max_feasible_return(mu, max_position, cash_cap)
    return {
        "n_assets": len(mu),
        "mu_min": round(min(mu), 4), "mu_max": round(max(mu), 4),
        "mu_mean": round(sum(mu) / len(mu), 4),
        "n_negative_mu": n_neg,
        "source_warning": (
            "μ 若为历史收益样本均值直接年化，信噪比极低（尤其 n<60 或含强趋势样本），"
            "Markowitz 结果对 μ 极敏感；报告必须同时给出 risk_parity 对照"
            if len(mu) > 0 else None),
        "max_feasible_return_under_constraints": round(upper, 4),
        "target_vs_upper": ("可达" if target <= upper + 1e-9
                            else f"不可达（理论上限 {upper:.2%} < 目标 {target:.2%}）"),
        "suggested_target_return": round(upper, 4) if target > upper + 1e-9 else target,
    }


def risk_parity(cov):
    n = len(cov)
    w = [1.0 / n] * n
    for _ in range(MAX_ITER):
        mrc = mat_vec(cov, w)          # 边际风险贡献
        total = quad_form(w, cov)
        if total <= 0:
            sys.exit(json.dumps({"error": "协方差矩阵非正定"}, ensure_ascii=False))
        rc = [w[i] * mrc[i] for i in range(n)]
        grad = [rc[i] / total - 1.0 / n for i in range(n)]
        w_new = [min(max(w[i] * math.exp(-0.5 * grad[i]), 1e-6), 1.0) for i in range(n)]
        s = sum(w_new)
        w_new = [x / s for x in w_new]
        if max(abs(w_new[i] - w[i]) for i in range(n)) < 1e-8:
            w = w_new
            break
        w = w_new
    return w


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--cov-file", required=True, help="年化协方差矩阵 CSV")
    p.add_argument("--mode", choices=["markowitz", "risk_parity"], required=True)
    p.add_argument("--mu-file", help="年化预期收益 CSV（markowitz 模式必填）")
    p.add_argument("--target-return", type=float, help="目标年化收益（markowitz 模式）")
    p.add_argument("--policy", choices=sorted(POLICY_MAX_POSITION), default=DEFAULT_POLICY,
                   help=f"策略口径，决定单票上限；默认 {DEFAULT_POLICY}（公募法规口径）")
    p.add_argument("--max-position", type=float, default=None,
                   help="直接指定单票上限，优先级高于 --policy（public_fund 口径下不得放宽）")
    p.add_argument("--cash-cap", type=float, default=None,
                   help="现金上限 0-1；给出后启用瀑布式回填，超出的现金回填到未触限股票")
    args = p.parse_args()

    max_position = POLICY_MAX_POSITION[args.policy]
    source = "policy:" + args.policy
    if args.max_position is not None:
        if not 0 < args.max_position <= 1.0:
            sys.exit(json.dumps({"error": "单票上限必须在 (0, 1]"}, ensure_ascii=False))
        if args.policy == "public_fund" and args.max_position > POLICY_MAX_POSITION["public_fund"]:
            sys.exit(json.dumps({
                "error": f"public_fund 口径下 PL-01 硬红线为 "
                         f"{POLICY_MAX_POSITION['public_fund']:.0%}，不得放宽。"
                         f"确需更高集中度请改用 --policy discretionary 并在报告中披露口径"},
                ensure_ascii=False))
        max_position = args.max_position
        source = "cli:--max-position"
    if args.cash_cap is not None and not 0 <= args.cash_cap < 1.0:
        sys.exit(json.dumps({"error": "现金上限必须在 [0, 1)"}, ensure_ascii=False))

    try:
        cov = load_matrix(args.cov_file)
    except ValueError as e:
        sys.exit(json.dumps({"error": f"解析协方差失败，只能含数值: {e}"}, ensure_ascii=False))
    except OSError as e:
        sys.exit(json.dumps({"error": f"读取协方差失败: {e}"}, ensure_ascii=False))
    n = len(cov)

    if args.mode == "risk_parity":
        w = risk_parity(cov)
        w, cash0 = clip_to_limit(w, max_position)
        w, cash, rounds, wf_reason = waterfall(w, max_position, args.cash_cap)
        if sum(w) <= 0:
            sys.exit(json.dumps({"error": "优化结果全零，请检查协方差矩阵"}, ensure_ascii=False))
        vol = math.sqrt(max(quad_form(w, cov), 0.0))
        out = {
            "mode": "risk_parity",
            "weights": [round(x, 4) for x in w],
            "cash_weight": cash,
            "cash_weight_before_waterfall": cash0,
            "volatility": round(vol, 4),
            "policy": args.policy,
            "max_position_applied": max_position,
            "max_position_source": source,
            "waterfall_rounds": rounds,
            "waterfall_reason": wf_reason,
            "cash_cap_applied": args.cash_cap,
            "engine": "stdlib",
        }
        out.update(explain_cash(cash, n, max_position, args.policy))
        out["note"] = ("风险平价不依赖收益预测，适合稳健型组合；"
                       f"单票上限 {max_position:.0%}（{source}）截断后剩余 {cash:.2%} 归现金"
                       + ("，本次已启用瀑布回填" if rounds else "，不回补其他股票"))
        print(json.dumps(out, ensure_ascii=False))
        return

    if not args.mu_file:
        sys.exit(json.dumps({"error": "markowitz 模式必须提供 --mu-file"}, ensure_ascii=False))
    # 未指定 --target-return 时不再直接报错：退化为全局最小方差组合求解。
    # 数学上等价于把目标收益设为 b/a（见下方闭包），此时拉格朗日乘子 lam=0。
    auto_target = args.target_return is None
    mu = load_vector(args.mu_file)
    if len(mu) != n:
        sys.exit(json.dumps({"error": f"预期收益长度({len(mu)}) 与协方差维度({n}) 不一致"},
                            ensure_ascii=False))

    inv = invert(cov)
    if inv is None:  # 协方差近奇异：加极小对角扰动后重试（ridge），并在输出中披露
        cov = [[cov[i][j] + (1e-8 if i == j else 0.0) for j in range(n)] for i in range(n)]
        inv = invert(cov)
        ridge = True
    else:
        ridge = False
    if inv is None:
        sys.exit(json.dumps({"error": "协方差矩阵奇异且扰动后仍不可逆，请检查数据（可能含重复资产）"},
                            ensure_ascii=False))

    ones = [1.0] * n
    # 单资产池在数学上不存在 Markowitz 前沿（ac-b²恒为 0）：此处不做无意义报错，
    # 直接给"满仓该资产、受单票上限夹逼"的解析解，并用 mode 标注口径。
    if n == 1:
        w1, cash1 = clip_to_limit([1.0], max_position)
        w1, cash_a, rounds1, wf1 = waterfall(w1, max_position, args.cash_cap)
        vol1 = math.sqrt(max(quad_form(w1, cov), 0.0))
        out = {
            "mode": "single_asset_degenerate",
            "target_return": args.target_return,
            "target_return_source": ("auto:single_asset" if auto_target else "user"),
            "achievable_return_on_invested": round(mu[0], 4),
            "target_return_infeasible": False,
            "mu_diagnostics": None,
            "infeasible_note": None,
            "weights": [round(x, 4) for x in w1],
            "cash_weight": cash_a,
            "cash_weight_before_waterfall": cash1,
            "volatility": round(vol1, 4),
            "ridge_applied": False,
            "policy": args.policy,
            "max_position_applied": max_position,
            "max_position_source": source,
            "waterfall_rounds": rounds1,
            "waterfall_reason": wf1,
            "cash_cap_applied": args.cash_cap,
            "warning": ("股票池只有 1 只资产，Markowitz 前沿退化（ac-b²=0）；"
                        "已直接给出受单票上限夹逼的解析解，请勿解读为模型优化结果"),
            "engine": "stdlib",
        }
        out.update(explain_cash(cash_a, n, max_position, args.policy))
        out["note"] = ("单资产组合无分散效应，权重仅由法规上限决定；"
                       "如需真正的均值-方差优化请提供 ≥2 只资产")
        print(json.dumps(out, ensure_ascii=False))
        return
    iv_o, iv_m = mat_vec(inv, ones), mat_vec(inv, mu)
    a = sum(iv_o)
    b = sum(iv_m)
    c = sum(mu[i] * iv_m[i] for i in range(n))
    denom = a * c - b * b
    if abs(denom) < 1e-14:
        sys.exit(json.dumps({"error": "目标收益约束退化，请调整 --target-return"}, ensure_ascii=False))
    if auto_target:
        # lam = 0, gam = 1/a —— 闭式解退化为全局最小方差组合
        if abs(a) < 1e-14:
            sys.exit(json.dumps({"error": "协方差退化，无法求解最小方差组合"}, ensure_ascii=False))
        args.target_return = b / a
    lam = (a * args.target_return - b) / denom
    gam = (c - b * args.target_return) / denom
    diag = diagnose_mu(mu, args.target_return, max_position, args.cash_cap)
    w = mat_vec(inv, [lam * mu[i] + gam * ones[i] for i in range(n)])
    w, cash0 = clip_to_limit(w, max_position)
    w, cash, rounds, wf_reason = waterfall(w, max_position, args.cash_cap)
    if sum(w) <= 0:
        sys.exit(json.dumps({"error": "优化结果全零，请放宽目标收益或扩大股票池"}, ensure_ascii=False))
    vol = math.sqrt(max(quad_form(w, cov), 0.0))
    invested = sum(w)
    achieved = sum(w[i] * mu[i] for i in range(n)) / invested if invested > 0 else 0.0
    # v3.3.0 新增：目标收益在数学上无法达成时显式告警，禁止静默输出误导性权重。
    # v3.4.1：先算约束下理论上限再判定，并直接给出可改成什么目标（免 priming 失败重试）。
    # 目标为自动推导（最小方差）时不判"不可达"：目标本身就是该解的性质，
    # 此时的偏差只来自单票上限夹逼，属于制度约束而非数学无解。
    infeasible = (not auto_target) and achieved < args.target_return - 1e-6
    out = {
        "mode": "markowitz_min_variance" if auto_target else "markowitz",
        "target_return": args.target_return,
        "target_return_source": ("auto:global_min_variance" if auto_target else "user"),
        "achievable_return_on_invested": round(achieved, 4),
        "target_return_infeasible": infeasible,
        "mu_diagnostics": diag,
        "infeasible_note": (
            f"按给定 mu/cov，本组合可达年化约 {achieved:.2%}，低于目标 {args.target_return:.2%}；"
            f"约束下理论上限为 {diag['max_feasible_return_under_constraints']:.2%}"
            f"（建议改用 --target-return {diag['suggested_target_return']}）。"
            "根因多为 μ 用历史样本均值直接年化：弱市样本会给出负 μ，导致数学上无解。"
            "报告中必须披露该缺口，禁止把不可达目标当作可实现收益展示" if infeasible else None),
        "weights": [round(x, 4) for x in w],
        "cash_weight": cash,
        "cash_weight_before_waterfall": cash0,
        "volatility": round(vol, 4),
        "ridge_applied": ridge,
        "policy": args.policy,
        "max_position_applied": max_position,
        "max_position_source": source,
        "waterfall_rounds": rounds,
        "waterfall_reason": wf_reason,
        "cash_cap_applied": args.cash_cap,
        "warning": "Markowitz 对输入敏感，报告中必须同时给出 risk_parity 对照",
        "engine": "stdlib",
    }
    out.update(explain_cash(cash, n, max_position, args.policy))
    out["note"] = (f"权重已截断至单票≤{max_position:.0%}（{source}，硬夹逼），"
                   f"被截断份额归现金（本次现金 {cash:.2%}），由风控官复核")
    print(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    main()
