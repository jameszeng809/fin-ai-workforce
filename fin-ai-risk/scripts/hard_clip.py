#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""风控硬夹逼（v3.4.1 新增）：把 Step 6.5 从「文档规则」变成「可复现脚本」。

背景：Step 6.5 此前只有文字规则，LLM 手工执行，无法回归、口径也容易漂移。典型后果是
演示时 5 只标的组合被夹成「股票 50% / 现金 50%」，观众当场问「为什么压着一半现金」，
现场只能靠嘴解释。本脚本把一步夹逼固化，并把解释写进输出。

用法：
  python scripts/hard_clip.py --weights-file target.json
  python scripts/hard_clip.py --weights-file target.json --policy discretionary
  python scripts/hard_clip.py --weights-file target.json --max-position 0.15 --cash-cap 0.10
  python scripts/hard_clip.py --weights-json '[{"code":"sh600519","weight":0.4}]'

input JSON（数组，或直接传 JSON 字符串）：
  [{"code":"sh600519","name":"贵州茅台","industry":"食品饮料","weight":0.30}, ...]
  权重口径：占组合净值比，可正可负（负=做空多头敞口抵消）

输出：JSON（夹逼前后对比、逐条夹逼明细、现金构成、口径解释、现场讲解要点）
"""
import argparse
import json
import math
import os
import sys

# 单票上限按策略口径区分（与 fin-ai-quant/scripts/optimizer.py 保持同源）
POLICY = {
    "public_fund": {"max_position": 0.10, "industry_cap": 0.30,
                    "basis": "《公开募集证券投资基金运作管理办法》第三十二条 / IL-01"},
    "discretionary": {"max_position": 0.25, "industry_cap": 0.40,
                      "basis": "专户/高端投顾内部风控制度（非法规强制）"},
    "demo": {"max_position": 0.35, "industry_cap": 0.50,
             "basis": "演示口径，报告中必须注明"},
}
DEFAULT_POLICY = "public_fund"


def load_weights(path_or_literal):
    if os.path.isfile(path_or_literal):
        with open(path_or_literal, encoding="utf-8") as f:
            data = json.load(f)
    else:
        try:
            data = json.loads(path_or_literal)
        except ValueError as e:
            sys.exit(json.dumps({"error": f"权重解析失败: {e}；请传 JSON 文件路径或 JSON 字符串"},
                                ensure_ascii=False))
    # 兼容多智能体协作的下游输出：`{"贵州茅台": 0.45, ...}` 映射形式。
    # 上游员工（如投研经理）常直接产出 名称->权重 字典，硬性要求数组会让流水线断在这里。
    if isinstance(data, dict):
        data = [{"name": k, "code": k, "weight": v} for k, v in data.items()]
    if not isinstance(data, list) or not data:
        sys.exit(json.dumps(
            {"error": "weight 必须为非空数组，形如 "
                      "[{\"code\":\"sh600519\",\"name\":\"贵州茅台\",\"industry\":\"食品饮料\","
                      "\"weight\":0.30}]；也接受 {\"贵州茅台\":0.30} 映射形式"},
            ensure_ascii=False))
    norm = []
    for i, it in enumerate(data):
        if not isinstance(it, dict):
            sys.exit(json.dumps({"error": f"第 {i+1} 项必须是对象"}, ensure_ascii=False))
        try:
            w = float(it.get("weight", 0.0))
        except (TypeError, ValueError):
            sys.exit(json.dumps({"error": f"第 {i+1} 项 weight 必须为数值"}, ensure_ascii=False))
        if abs(w) > 1.0:
            sys.exit(json.dumps({"error": f"第 {i+1} 项 weight={w} 绝对值超过 1（100%）"},
                                ensure_ascii=False))
        norm.append({"code": it.get("code") or it.get("name") or f"ASSET_{i+1}",
                     "name": it.get("name") or it.get("code") or f"资产{i+1}",
                     "industry": it.get("industry") or "未分类",
                     "weight": w})
    return norm


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--weights-file", help="目标权重 JSON 文件路径")
    p.add_argument("--weights-json", help="目标权重 JSON 字符串（与 --weights-file 二选一）")
    p.add_argument("--policy", choices=sorted(POLICY), default=DEFAULT_POLICY,
                   help=f"策略口径，默认 {DEFAULT_POLICY}")
    p.add_argument("--max-position", type=float, default=None, help="覆盖单票上限")
    p.add_argument("--industry-cap", type=float, default=None, help="覆盖单行业上限")
    p.add_argument("--cash-cap", type=float, default=None,
                   help="现金上限；给出后启用瀑布式回填（最多 50 轮）")
    args = p.parse_args()

    src = args.weights_file or args.weights_json
    if not src:
        sys.exit(json.dumps({"error": "必须提供 --weights-file 或 --weights-json"},
                            ensure_ascii=False))
    items = load_weights(src)

    cfg = POLICY[args.policy]
    max_pos = args.max_position if args.max_position is not None else cfg["max_position"]
    ind_cap = args.industry_cap if args.industry_cap is not None else cfg["industry_cap"]
    source = ("cli" if (args.max_position is not None or args.industry_cap is not None)
              else f"policy:{args.policy}")
    if not 0 < max_pos <= 1.0 or not 0 < ind_cap <= 1.0:
        sys.exit(json.dumps({"error": "单票/行业上限必须在 (0, 1]"}, ensure_ascii=False))
    if args.policy == "public_fund" and (
            (args.max_position or 0) > cfg["max_position"] or
            (args.industry_cap or 0) > cfg["industry_cap"]):
        sys.exit(json.dumps({
            "error": f"public_fund 口径下 PL-01/IL-01 为法规或内控红线"
                     f"（单票 {cfg['max_position']:.0%} / 行业 {cfg['industry_cap']:.0%}），不得放宽；"
                     f"确需更高集中度请改用 --policy discretionary 并披露口径"}, ensure_ascii=False))

    before = [dict(x) for x in items]
    steps = []

    # ---- 第 1 步：总敞口 > 100% 等比缩放 ----
    gross = sum(abs(x["weight"]) for x in items)
    if gross > 1.0 + 1e-9:
        k = 1.0 / gross
        for x in items:
            x["weight"] = round(x["weight"] * k, 6)
        steps.append({"step": "gross_scale", "action": f"总敞口 {gross:.2%} > 100%，等比缩放至 100%",
                      "scale_factor": round(k, 6)})

    # ---- 第 2 步：单票上限 ----
    for x in items:
        if abs(x["weight"]) > max_pos + 1e-12:
            old = x["weight"]
            x["weight"] = math.copysign(max_pos, old)
            steps.append({"step": "single_position", "code": x["code"], "name": x["name"],
                          "action": f"{x['name']} {old:.2%} → {x['weight']:.2%}（单票上限 {max_pos:.0%}）",
                          "released": round(abs(old) - max_pos, 6)})

    # ---- 第 3 步：行业上限（行业内等比压缩，压出的份额同样归现金）----
    ind_tot = {}
    for x in items:
        ind_tot[x["industry"]] = ind_tot.get(x["industry"], 0.0) + abs(x["weight"])
    ind_after = {}
    for sec, tot in ind_tot.items():
        if tot > ind_cap + 1e-9:
            k = ind_cap / tot
            released = 0.0
            for x in items:
                if x["industry"] == sec:
                    old = x["weight"]
                    x["weight"] = round(old * k, 6)
                    released += abs(old) - abs(x["weight"])
            steps.append({"step": "industry_cap", "industry": sec,
                          "action": f"{sec} 合计 {tot:.2%} → {ind_cap:.2%}（行业上限 {ind_cap:.0%}）",
                          "scale_factor": round(k, 6), "released": round(released, 6)})
        ind_after[sec] = round(
            sum(abs(x["weight"]) for x in items if x["industry"] == sec), 6)

    invested = sum(x["weight"] for x in items if x["weight"] > 0)
    cash_before = round(1.0 - sum(x["weight"] for x in before), 6)
    cash = round(1.0 - sum(x["weight"] for x in items), 6)

    # ---- 第 4 步（可选）：瀑布式回填 ----
    wf_rounds, wf_reason = 0, None
    if args.cash_cap is not None:
        if not 0 <= args.cash_cap < 1.0:
            sys.exit(json.dumps({"error": "现金上限必须在 [0, 1)"}, ensure_ascii=False))
        for _ in range(50):
            cur = 1.0 - sum(x["weight"] for x in items)
            if cur <= args.cash_cap + 1e-9:
                wf_reason = None if wf_rounds else "no_change_needed"
                break
            free = [x for x in items if 0 <= x["weight"] < max_pos - 1e-12]
            if not free:
                wf_reason = ("all_assets_at_cap:全部标的均已触及单票上限，现金无处可填；"
                             "要降低现金必须扩大股票池或放宽单票上限")
                break
            base = sum(x["weight"] for x in free)
            give = cur - args.cash_cap
            for x in free:
                share = (x["weight"] / base) if base > 1e-12 else 1.0 / len(free)
                x["weight"] = round(min(x["weight"] + share * give, max_pos), 6)
            wf_rounds += 1
        else:
            wf_reason = "max_rounds_reached"
        # 回填后重算
        ind_after = {s: round(sum(abs(x["weight"]) for x in items if x["industry"] == s), 6)
                     for s in ind_tot}
        invested = sum(x["weight"] for x in items if x["weight"] > 0)
        cash = round(1.0 - sum(x["weight"] for x in items), 6)

    # 行业上限回填后可能被再次突破，做最终守卫
    violations = [s for s, v in ind_after.items() if v > ind_cap + 1e-6]

    n = len(items)
    capacity = round(n * max_pos, 4)
    explanation = None
    if cash > 1e-6:
        explanation = (f"股票池 {n} 只 × 单票上限 {max_pos:.0%} = 可投上限 {capacity:.0%}，"
                       f"剩余 {cash:.0%} 只能是现金。")
    talking_points = []
    if cash >= 0.30:
        need = math.ceil(0.9 / max_pos)
        talking_points += [
            f"【必答】为什么现金 {cash:.0%}？——不是模型没钱可投，而是当前口径下 {n} 只标的"
            f"最多只能放 {capacity:.0%}，这是{'《运作管理办法》第三十二条的强制结果' if args.policy=='public_fund' else '内控上限的直接结果'}。",
            f"【给方案】把它放大到 {need} 只以上即可自然降低现金；或切 --policy discretionary 看同一组合在专户口径下的样子。",
            "【点价值】这一步正是风控官与投研经理的分工：投研经理负责收益想法，风控官负责在法规边界内决定能放多少。",
        ]
    if violations:
        talking_points.append(f"【须披露】回填后行业 {violations} 重新超过上限 {ind_cap:.0%}，"
                              f"说明 cash-cap 与行业上限在该股票池下不可同时满足，应放弃回填或扩大股票池。")

    print(json.dumps({
        "policy": args.policy,
        "policy_basis": cfg["basis"],
        "max_position_applied": max_pos,
        "industry_cap_applied": ind_cap,
        "limits_source": source,
        "before": {"weights": before,
                   "cash_weight": cash_before,
                   "gross_exposure": round(sum(abs(x["weight"]) for x in before), 6)},
        "after": {"weights": [{"code": x["code"], "name": x["name"], "industry": x["industry"],
                               "weight": round(x["weight"], 6)} for x in items],
                  "cash_weight": cash,
                  "invested_weight": round(invested, 6)},
        "comparison": [{"code": b["code"], "name": b["name"],
                        "before": round(b["weight"], 6),
                        "after": round(a["weight"], 6),
                        "delta": round(a["weight"] - b["weight"], 6)}
                       for b, a in zip(before, items)],
        "industry_weights_after": ind_after,
        "industry_cap_violations": violations,
        "clip_steps": steps,
        "n_clipped": len([s for s in steps if s["step"] != "gross_scale"]),
        "total_released_to_cash": round(
            sum(s.get("released", 0.0) for s in steps) + max(cash - cash_before, 0.0), 6),
        "cash_explanation": explanation,
        "waterfall": {"applied": args.cash_cap is not None, "cap": args.cash_cap,
                      "rounds": wf_rounds, "reason": wf_reason},
        "talking_points": talking_points,
        "note": ("夹逼结果可直接生效，分析师无权覆盖；异议写入圆桌纪要交 CIO 裁决。"
                 "被夹掉的份额归现金，不得重新分配给其他股票"),
        "engine": "stdlib",
    }, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
