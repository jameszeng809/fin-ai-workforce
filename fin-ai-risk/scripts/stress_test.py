#!/usr/bin/env python3
"""压力测试：按 data/scenarios.json 情景库计算组合冲击损失。

用途：fin-ai-risk Step5。v3.3.2 新增——Step5 此前无任何脚本支撑，
      只能靠 LLM 心算，与团队「禁止 LLM 心算」原则冲突。
依赖：无（纯标准库）
用法：python scripts/stress_test.py --weights 0.3,0.25,0.2,0.15,0.1 \
             [--industries 食品饮料,新能源,银行,非银金融,其他] [--beta 1.0] \
             [--illiquid-weight 0.10] [--scenario SC-2015]
输出：JSON（逐情景损失、最坏情景、与 VaR 的对比提示）

计算口径：
  历史回放类（historical=true）：组合损失 = index_shock × beta
  假设冲击类（historical=false，读 apply 字段）：
    industry_shock   = 最大单一行业权重 × per_day_shock × days
    position_shock   = 最大单一持仓权重 × shock
    liquidity_shock  = 低流动性持仓权重合计 × shock
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SCENARIOS = os.path.join(HERE, "..", "data", "scenarios.json")


def load_scenarios():
    try:
        with open(SCENARIOS, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError) as e:
        sys.exit(json.dumps({"error": f"无法读取情景库 {SCENARIOS}: {e}"}, ensure_ascii=False))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--weights", required=True, help="风险资产权重，逗号分隔")
    p.add_argument("--cash", type=float, default=0.0,
                   help="现金权重。权重之和 + 本值 须为 1；现金在情景中不受冲击")
    p.add_argument("--industries", default=None,
                   help="每只持仓所属行业，逗号分隔，长度与 weights 一致（用于 SC-SECTOR）")
    p.add_argument("--beta", type=float, default=1.0,
                   help="组合相对指数的 beta，默认 1.0（历史回放类情景）")
    p.add_argument("--illiquid-weight", type=float, default=None,
                   help="低流动性（日均成交额后 30%%）持仓权重合计；不给则用"
                        "「权重最小的 ceil(30%%) 只持仓之和」作代理并标注")
    p.add_argument("--scenario", default=None, help="只算指定情景 id，如 SC-2015")
    p.add_argument("--var-95", type=float, default=None,
                   help="可选：传入 VaR(95%%,1日) 损失比例，用于对比压力测试与 VaR")
    args = p.parse_args()

    try:
        w = [float(x) for x in args.weights.split(",")]
    except ValueError:
        sys.exit(json.dumps({"error": "weights 必须为逗号分隔数值"}, ensure_ascii=False))
    if not w or any(x < 0 for x in w):
        sys.exit(json.dumps({"error": "weights 不能为空或含负值"}, ensure_ascii=False))
    s = sum(w)
    # 与 var.py 同口径：风险资产 + 现金 = 1。公募"双十"下股票池不足 9 只时
    # 必然留有现金，硬性要求和为 1 会让 量化→风控 链路直接断掉。
    invested_w = s
    if not -1e-9 <= args.cash <= 1 + 1e-9:
        sys.exit(json.dumps({"error": f"--cash 必须在 0~1 之间，当前 {args.cash}"},
                            ensure_ascii=False))
    if abs(s + args.cash - 1.0) > 0.01:
        sys.exit(json.dumps(
            {"error": f"权重之和({s:.4f}) + 现金({args.cash:.4f}) 必须为 1。"
                      f"若组合留有现金，请用 --cash 显式声明"},
            ensure_ascii=False))

    if args.beta <= 0:
        sys.exit(json.dumps({"error": "beta 必须为正"}, ensure_ascii=False))

    inds = None
    if args.industries:
        inds = [x.strip() for x in args.industries.split(",")]
        if len(inds) != len(w):
            sys.exit(json.dumps({"error": "industries 长度必须与 weights 一致"},
                                ensure_ascii=False))

    # 低流动性权重
    illiquid_note = None
    if args.illiquid_weight is not None:
        if not (0 <= args.illiquid_weight <= 1):
            sys.exit(json.dumps({"error": "illiquid-weight 必须在 [0,1]"}, ensure_ascii=False))
        illiquid_w = args.illiquid_weight
    else:
        k = max(1, int(len(w) * 0.3 + 0.999))
        illiquid_w = sum(sorted(w)[:k])
        illiquid_note = (f"未提供 --illiquid-weight，用「权重最小的 {k} 只持仓之和 "
                         f"{round(illiquid_w, 4)}」作代理（真实口径应取日均成交额后 30%）")

    cfg = load_scenarios()
    scen = cfg.get("scenarios", [])
    if not scen:
        sys.exit(json.dumps({"error": "情景库为空"}, ensure_ascii=False))

    # 行业权重
    ind_w = {}
    if inds:
        for i, name in enumerate(inds):
            ind_w[name] = ind_w.get(name, 0.0) + w[i]
    top_ind = max(ind_w.values()) if ind_w else None
    max_pos = max(w)

    results = []
    for sc in scen:
        sid = sc.get("id")
        if args.scenario and sid != args.scenario:
            continue
        if sc.get("historical"):
            shock = sc.get("index_shock")
            if shock is None:
                results.append({"id": sid, "error": "历史情景缺少 index_shock 字段"})
                continue
            # 现金仓位在冲击中不受损，因此组合损失 = 权益暴露 × 指数冲击 × beta。
            # 少了这一步，30% 仓位的组合会被算成满仓挨跌。
            loss = shock * args.beta * invested_w
            detail = (f"权益暴露 {round(invested_w, 4)} × 指数冲击 {shock} "
                      f"× beta {args.beta}")
        else:
            ap = sc.get("apply")
            if not ap:
                results.append({"id": sid, "error": "假设情景缺少 apply 字段"})
                continue
            op = ap.get("op")
            if op == "industry_shock":
                if top_ind is None:
                    results.append({"id": sid, "skipped":
                                    "未提供 --industries，无法计算行业集中度冲击"})
                    continue
                loss = top_ind * ap.get("per_day_shock", -0.10) * ap.get("days", 2)
                detail = (f"最大行业权重 {round(top_ind, 4)} × {ap.get('per_day_shock')} "
                          f"× {ap.get('days')} 日")
            elif op == "position_shock":
                loss = max_pos * ap.get("shock", -0.80)
                detail = f"最大持仓权重 {round(max_pos, 4)} × {ap.get('shock')}"
            elif op == "liquidity_shock":
                loss = illiquid_w * ap.get("shock", -0.20)
                detail = f"低流动性权重 {round(illiquid_w, 4)} × {ap.get('shock')}"
            else:
                results.append({"id": sid, "error": f"未知 apply.op: {op}"})
                continue
        results.append({"id": sid, "name": sc.get("name"),
                        "portfolio_loss": round(loss, 4),
                        "portfolio_loss_pct": round(loss * 100, 2),
                        "calc": detail})

    done = [r for r in results if "portfolio_loss" in r]
    worst = min(done, key=lambda r: r["portfolio_loss"]) if done else None

    out = {
        "inputs": {"n_positions": len(w), "beta": args.beta,
                   "cash_weight": round(args.cash, 4),
                   "invested_weight": round(invested_w, 4),
                   "top_industry_weight": round(top_ind, 4) if top_ind is not None else None,
                   "max_position_weight": round(max_pos, 4),
                   "illiquid_weight": round(illiquid_w, 4)},
        "scenario_count": len(done),
        "scenarios": results,
        "worst_scenario": worst,
        "illiquid_note": illiquid_note,
        "source": os.path.relpath(SCENARIOS, HERE),
        "engine": "stdlib",
    }
    if args.var_95 is not None and worst:
        out["vs_var"] = {
            "var_95_1d": args.var_95,
            "worst_stress_loss": worst["portfolio_loss"],
            "stress_over_var_times": round(abs(worst["portfolio_loss"] / args.var_95), 1)
            if args.var_95 else None,
            "note": ("压力测试损失显著大于 VaR 属正常：VaR 基于正态假设的 95% 分位，"
                     "压力测试是尾部历史/假设情景，两者互补不可互相替代"),
        }
    print(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    main()
