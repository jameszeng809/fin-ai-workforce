#!/usr/bin/env python3
"""DCF 两阶段自由现金流折现估值。

用途：fin-ai-researcher Step7.1。所有估值计算必须由本脚本执行，禁止 LLM 心算。
依赖：无（纯标准库，开箱即用）
用法：python scripts/dcf.py --fcff 120,130,140,150,158 --wacc 0.09 --g 0.03 --net-debt 50000 --shares 12.56
      （--fcff 为未来5年自由现金流预测，单位亿元；--net-debt 净负债亿元；--shares 股本亿股）
输出：JSON（企业价值/股权价值/每股价值/终值占比校验）

v3.4.1 修正（WACC 护栏）：CAPM 在真实数据上可能算出 β<0（例如茅台对沪深300
      回归得 β=-0.20、R²=0.033），进而 WACC≈0.55% < 永续增长率 g=3%，旧版直接
      sys.exit 报错，导致整条投研流水线在第一步就断链。现在不再裸退出，而是
      应用最小风险溢价护栏（WACC = g + MIN_WACC_G_SPREAD），并在输出中
      显式标注 guardrail 字段，提示调用方回退到行业 β 或目标资本结构重算。
"""
import argparse
import json
import sys

MIN_WACC_G_SPREAD = 0.03   # WACC 相对永续增长率的最小风险溢价


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--fcff", required=True, help="逗号分隔的5年FCFF预测（亿元）")
    p.add_argument("--wacc", type=float, required=True, help="加权平均资本成本，如 0.09")
    p.add_argument("--g", type=float, default=0.03, help="永续增长率，默认 0.03（不得超过长期名义GDP）")
    p.add_argument("--net-debt", type=float, default=0.0, help="净负债（亿元）")
    p.add_argument("--shares", type=float, required=True, help="总股本（亿股）")
    args = p.parse_args()

    fcff = [float(x) for x in args.fcff.split(",")]
    if len(fcff) != 5:
        sys.exit(json.dumps({"error": "fcff 必须为 5 期预测"}, ensure_ascii=False))
    if args.shares <= 0:
        sys.exit(json.dumps({"error": "总股本必须为正"}, ensure_ascii=False))

    wacc = args.wacc
    guardrail = None
    if wacc <= args.g:
        floor = round(args.g + MIN_WACC_G_SPREAD, 4)
        guardrail = {
            "applied": True,
            "input_wacc": args.wacc,
            "used_wacc": floor,
            "reason": (f"输入的 WACC({args.wacc:.4f}) 不大于永续增长率 g({args.g:.4f})，"
                       f"通常源于 CAPM β 异常（如 β<0 或回归 R² 过低）。"
                       f"已按最小风险溢价 {MIN_WACC_G_SPREAD:.0%} 抬升至 {floor:.4f}，"
                       "估值结果仅供参考，报告中必须披露该护栏并说明 β 来源。"),
            "action_required": "改用行业可比 β 或目标资本结构重算 WACC 后复核估值",
        }
        wacc = floor

    if wacc > 0.20 or args.g > 0.05:
        print("[warn] WACC>20% 或 g>5% 属激进假设，报告中须显式披露", file=sys.stderr)

    pv_explicit = sum(f / (1 + wacc) ** (i + 1) for i, f in enumerate(fcff))
    terminal = fcff[-1] * (1 + args.g) / (wacc - args.g)
    pv_terminal = terminal / (1 + wacc) ** 5
    ev = pv_explicit + pv_terminal
    equity = ev - args.net_debt
    per_share = equity / args.shares
    tv_ratio = pv_terminal / ev

    print(json.dumps({
        "pv_explicit": round(pv_explicit, 1),
        "pv_terminal": round(pv_terminal, 1),
        "enterprise_value": round(ev, 1),
        "equity_value": round(equity, 1),
        "value_per_share": round(per_share, 2),
        "terminal_value_ratio": round(tv_ratio, 3),
        "wacc_used": round(wacc, 4),
        "guardrail": guardrail,
        "tv_ratio_warning": tv_ratio > 0.75 and "终值占比>75%，估值对 g/WACC 极敏感，必须输出敏感性区间" or None,
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
