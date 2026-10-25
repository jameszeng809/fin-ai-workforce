#!/usr/bin/env python3
"""冲击成本估算（平方根市场冲击模型）。

用途：fin-ai-execution Step2。基于订单规模与日均成交额估算价格冲击。
依赖：无（纯标准库，v3.3.0 去除 numpy 依赖，开箱即用）
用法：python scripts/impact_cost.py --order-value 5000 --adv 120000 --daily-vol 0.03
      （order-value 订单金额万元；adv 20日日均成交额万元；daily-vol 日波动率）
      python scripts/impact_cost.py --order-value 2000 --adv 1329400 --daily-vol 0.028 --horizon-hours 1
输出：JSON（一次性冲击成本bps、可执行判定、候选算法篮子与推荐、建议拆单参数）

v3.4.1 修正：旧版只输出**一个**算法（小单必然是 "1 笔 Sniper"），演示时观众看不到算法选择过程，
交易执行官的"为一笔单挑选最优执行路径"这一核心职责完全没被体现。现改为同时输出 5 个候选
算法的一次性估算对比（含拆分后的摊薄效应），并给出推荐与理由。

拆分摊薄模型（Almgren-Chriss 简化）：
  总冲击 = 永久冲击（不可摊薄）+ 临时冲击 / √N
  其中临时占比默认 40%（行业常用区间 30%~50%，可用 --temp-share 调整）。
  这是估算而非承诺，输出中必须连同假设一起披露。

v3.3.0 重要修正：修复量纲错误。旧版 `33 * vol * sqrt(participation) * 10000` 会把
0.2% 的合理冲击算成 2000+ bps（20%），属于百分点与基点换算错误（应为 ×100）。
"""
import argparse
import json
import math
import sys

MAX_PARTICIPATION = 0.10  # 单笔不超过日均成交额 10%，与 SKILL 正文一致
# 平方根冲击模型：Δp/p = Y · σ_日 · √(Q/ADV)
# Y 为标定系数。v3.3.1 由 33.0（百分比口径下的等效值）显式改写为 0.33（小数口径），
# 数值结果不变，但量纲与文献一致、可解释。典型区间 0.3~1.0：
#   0.33 ≈ 永久冲击口径（保守）；1.0 ≈ 含临时冲击的全口径。可用 --impact-coef 校准。
IMPACT_COEF = 0.33
VOL_SANITY_WARN = 0.10  # A股日波动率 >10% 极罕见（涨停板 10%），提示可能误传年化值
VOL_SANITY_MAX = 0.30   # 超过直接拒绝
TEMP_SHARE = 0.40       # 临时冲击占总冲击比例（可用 --temp-share 调整）
TEMP_SHARE_RANGE = (0.30, 0.50)

ALGO_SPECS = {
    "Sniper": {"interval_min": 0, "desc": "一次性下单，即时成交"},
    "TWAP": {"interval_min": 10, "desc": "时间加权，等分 N 笔匀速成交"},
    "VWAP": {"interval_min": 15, "desc": "跟随日内成交量分布，放量时段多下"},
    "POV_10pct": {"interval_min": 0, "desc": "按成交量比例跟随，参与率上限 10%"},
    "Iceberg": {"interval_min": 20, "desc": "冰山单，仅露出一小块挂单隐藏意图"},
}


def build_algo_plan(order_value, adv, daily_vol, coef, participation, horizon_minutes, temp_share):
    """生成候选算法篮子：估算各算法的冲击成本、笔数、时长与取舍。"""
    single_bps = coef * daily_vol * math.sqrt(participation) * 10000.0
    perm = single_bps * (1.0 - temp_share)      # 永久冲击：与总成交量相关，拆单无法摊薄
    temp = single_bps * temp_share              # 临时冲击：按 1/√N 摊薄

    def slices_for(name):
        if name == "Sniper":
            return 1
        if name == "POV_10pct":
            return max(1, math.ceil(participation / MAX_PARTICIPATION))
        return max(2, math.ceil(horizon_minutes / ALGO_SPECS[name]["interval_min"]))

    plan = []
    for name, spec in ALGO_SPECS.items():
        n = slices_for(name)
        est = perm + temp / math.sqrt(n)
        vol_seconds = daily_vol / math.sqrt(240 * 60 * 60) if daily_vol > 0 else 0  # 粗略秒波动
        horizon = 0.0 if spec["interval_min"] == 0 else round(n * spec["interval_min"], 1)
        plan.append({
            "algo": name,
            "desc": spec["desc"],
            "slices": n,
            "per_slice_value_wan": round(order_value / n, 2),
            "est_impact_bps": round(est, 2),
            "saved_bps_vs_sniper": round(single_bps - est, 2),
            "est_duration_minutes": horizon,
            "timing_risk": "高" if spec["interval_min"] == 0 else
                           ("中" if horizon <= 60 else "低"),
            "trade_off": {
                "Sniper": "成交最快、无择时风险，但一次性冲击最大，且暴露全部意图",
                "TWAP": "节奏均匀、可预测，不随量能自适应，放量时段会错失流动性",
                "VWAP": "贴合真实成交量分布，隐蔽性好，但依赖日内量能预测",
                "POV_10pct": "自动跟随市场活跃度，量缩则减；执行时长不可控",
                "Iceberg": "挂单暴露最小，适合大额隐蔽建仓，但成交确定性最低",
            }[name],
        })
    # 推荐：估算成本最低者；并列时优先执行更快的（时长短 = 择时风险小）
    best = sorted(plan, key=lambda x: (x["est_impact_bps"], x["est_duration_minutes"]))[0]
    return single_bps, plan, best


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--order-value", type=float, required=True, help="订单金额（万元）")
    p.add_argument("--adv", type=float, required=True, help="20日日均成交额（万元）")
    p.add_argument("--daily-vol", type=float, required=True,
                   help="【日】波动率小数，如 0.02。切勿传年化波动率（年化请 /sqrt(244)≈15.6）")
    p.add_argument("--impact-coef", type=float, default=IMPACT_COEF,
                   help="冲击系数 Y，默认 0.33（永久冲击口径），典型区间 0.3~1.0")
    p.add_argument("--horizon-hours", type=float, default=1.0,
                   help="期望执行窗口（小时），影响 TWAP/VWAP/Iceberg 的可拆笔数，默认 1.0")
    p.add_argument("--temp-share", type=float, default=TEMP_SHARE,
                   help=f"临时冲击占比，默认 {TEMP_SHARE}（区间 {TEMP_SHARE_RANGE[0]}~{TEMP_SHARE_RANGE[1]}）")
    args = p.parse_args()

    if args.adv <= 0 or args.order_value <= 0:
        sys.exit(json.dumps({"error": "订单金额与日均成交额必须为正"}, ensure_ascii=False))
    if args.daily_vol <= 0:
        sys.exit(json.dumps({"error": "日波动率必须为正"}, ensure_ascii=False))
    if args.daily_vol > VOL_SANITY_MAX:
        sys.exit(json.dumps({
            "error": f"日波动率 {args.daily_vol} 不合理（A股单日涨跌幅上限 10%，"
                     f"日波动率一般 <5%）。若你传入的是年化波动率，请先除以 sqrt(244)≈15.62",
            "hint": f"年化 {args.daily_vol} → 日波动率约 {round(args.daily_vol / 15.62, 5)}"},
            ensure_ascii=False))
    if args.impact_coef <= 0 or args.impact_coef > 2:
        sys.exit(json.dumps({"error": "冲击系数 Y 必须在 (0, 2]（典型 0.3~1.0）"},
                            ensure_ascii=False))
    participation = args.order_value / args.adv
    if participation > 1.0:
        sys.exit(json.dumps({"error": "订单超过单日成交额，禁止执行，必须分日拆单"},
                            ensure_ascii=False))

    # 平方根冲击模型：Δp/p = Y · σ_日 · √(Q/ADV)，结果转 bps（×10000）
    impact_frac = args.impact_coef * args.daily_vol * math.sqrt(participation)
    impact_pct = impact_frac * 100.0
    impact_bps = impact_frac * 10000.0
    vol_warn = None
    if args.daily_vol > VOL_SANITY_WARN:
        vol_warn = (f"日波动率 {args.daily_vol} 偏高：A股日波动率通常 <5%。"
                    f"若传的是年化值，请改用约 {round(args.daily_vol / 15.62, 5)}")

    feasible = participation <= MAX_PARTICIPATION
    slices = 1 if feasible else math.ceil(participation / MAX_PARTICIPATION)

    if not TEMP_SHARE_RANGE[0] <= args.temp_share <= TEMP_SHARE_RANGE[1]:
        sys.exit(json.dumps({
            "error": f"临时冲击占比 {args.temp_share} 超出合理区间 "
                     f"{TEMP_SHARE_RANGE[0]}~{TEMP_SHARE_RANGE[1]}",
            "hint": "该比例用于把总冲击拆为『可摊薄的临时部分』与『不可摊薄的永久部分』，"
                    "超出区间会让摊薄估算失真"}, ensure_ascii=False))
    if args.horizon_hours <= 0 or args.horizon_hours > 24:
        sys.exit(json.dumps({"error": "执行窗口必须在 (0, 24] 小时"}, ensure_ascii=False))
    horizon_minutes = args.horizon_hours * 60.0
    single_bps, plan, best = build_algo_plan(
        args.order_value, args.adv, args.daily_vol, args.impact_coef,
        participation, horizon_minutes, args.temp_share)

    print(json.dumps({
        "participation": round(participation, 4),
        "impact_cost_bps": round(impact_bps, 1),
        "impact_cost_pct": round(impact_pct, 4),
        "feasible_single_shot": feasible,
        "suggested_slices": slices,
        "suggested_algo": "TWAP" if slices > 3 else ("VWAP" if participation > 0.03 else "Sniper"),
        "impact_coef_used": args.impact_coef,
        "vol_warning": vol_warn,
        "order_value_wan": args.order_value,
        "adv_wan": args.adv,
        "horizon_hours": args.horizon_hours,
        "assumptions": {
            "model": "总冲击 = 永久冲击 + 临时冲击/√N（Almgren-Chriss 简化）",
            "temp_share_used": args.temp_share,
            "temp_share_range": list(TEMP_SHARE_RANGE),
            "note": "估算值而非成交承诺；永久部分不随拆单次数摊薄，这是拆单收益递减的根因",
        },
        "algo_plan": plan,
        "recommended_algo": best["algo"],
        "recommended_reason": (
            f"{best['algo']}：估算冲击 {best['est_impact_bps']} bps，"
            f"较一次性下单节省 {best['saved_bps_vs_sniper']} bps，"
            f"拆 {best['slices']} 笔、约 {best['est_duration_minutes']} 分钟完成，"
            f"择时风险{best['timing_risk']}。{best['trade_off']}"),
        "ranked_by_cost": sorted([{"algo": x["algo"], "est_impact_bps": x["est_impact_bps"]}
                                  for x in plan], key=lambda x: x["est_impact_bps"]),
        "note": ("冲击成本为统计近似；跌停封板/停牌状态必须先过合规专员 EX 规则检查。"
                 "algo_plan 为同条件下的横向对比，用于选算法，不代表最终成交价"),
        "engine": "stdlib",
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
