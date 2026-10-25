#!/usr/bin/env python3
"""舆情自动分级：按 scoring.json 公式计算综合分并映射 P0/P1/P2/P3。

用途：fin-ai-news Step3（舆情监控官）、fin-ai-crisis Step1（应急交易员分级采用同源公式）。
依赖：无（纯标准库，开箱即用）
用法：python scripts/classify.py --sentiment 20 --involvement 100 --spread 80
      python scripts/classify.py --sentiment 35 --involvement 50 --spread 60 --age-hours 30
输出：JSON（各分项得分、加权计算过程、分级、时效衰减前后对比、人工可读依据）

说明：三项分项统一为「0-100，越低越危急」后再加权：
      - 情绪分：直接采用（anchors: severe_negative=0 / negative=35 / neutral=60 / positive=85）
      - 涉事深度/传播量级：scoring.json 中原始 scale 为「越高越重大」（监管=100、央媒=100），
        与本公式的「越低越危急」方向相反，故内部统一取 (100 - 原始分) 后再加权。

v3.3.0 修正 1（分级方向致命缺陷）：旧公式直接把「涉事深度 100（监管）+ 传播 100（央媒）」
      当作高分计入，导致最严重的舆情（监管立案+央媒+极度负面）算得 64 分只能判 P2，
      而 P0 条件 score<25 在 involvement>=80 时数学上恒不可达（0.3×80=24，再叠加传播项必 >25）。
      现统一方向后，该场景得 4 分正确判为 P0。
v3.3.0 修正 2（时效衰减方向）：旧文档写「每过 24h 总分×0.85」，会让危急事件（20 分）
      越放越严重（14 分），与「衰减」语义相反；现改为向中性（100）回归。
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SCORING = os.path.join(HERE, "..", "data", "scoring.json")
DEFAULT_WEIGHTS = {"sentiment": 0.4, "involvement": 0.3, "spread": 0.3}
DECAY_PER_DAY = 0.85   # 每日保留的"偏离中性"比例
P0_GRACE_HOURS = 48    # P0 事件 48h 内不衰减
ANCHORS = {"severe_negative": 0, "negative": 35, "neutral": 60, "positive": 85}


def load_weights():
    try:
        with open(SCORING, encoding="utf-8") as f:
            d = json.load(f)
        return d.get("weights", DEFAULT_WEIGHTS)
    except (OSError, ValueError):
        return DEFAULT_WEIGHTS


DEFAULT_GRADING = [
    {"level": "P0", "label": "危急", "logic": "AND",
     "thresholds": {"max_score": 25, "min_involvement": 80, "max_sentiment": 25}},
    {"level": "P1", "label": "重要", "logic": "AND",
     "thresholds": {"max_score": 45, "min_involvement": 60}},
    {"level": "P2", "label": "关注", "logic": "OR",
     "thresholds": {"max_score": 60, "min_involvement": 50}},
    {"level": "P3", "label": "中性", "logic": "AND",
     "thresholds": {"max_score": None, "min_involvement": None}},
]


def load_grading():
    """v3.3.2：从 data/scoring.json 的 grading 节读取分级阈值。

    旧版把 25/45/60/80/60/50 六个数字硬编码在本函数里，改配置完全不起作用。
    """
    try:
        with open(SCORING, encoding="utf-8") as f:
            d = json.load(f)
        g = d.get("grading")
        if isinstance(g, list) and g and all(
                isinstance(x, dict) and x.get("level") and x.get("thresholds") for x in g):
            return g, None
        return DEFAULT_GRADING, "grading 节缺少 thresholds 结构，已回退内置阈值"
    except (OSError, ValueError):
        return DEFAULT_GRADING, "配置读取失败，已回退内置阈值"


def grade(score, involvement, table=None, sentiment=None):
    """按分级表判定等级。

    v3.4.1：P0 档新增 max_sentiment 必要条件（情绪必须足够负面）。
    旧版 P0 只要求 score<25 且 involvement>=80，而 involvement 是 LLM 给的
    "涉事深度"主观分——一篇普通的机构观点汇总稿也会被给到 80（"上市公司重大"），
    再叠加传播分即可把 score 压到 25 以下，导致常规分析稿被误判 P0 并自动
    触发应急交易流水线。危急事件必须以"情绪极负面"为准入门槛。
    """
    table = table or DEFAULT_GRADING
    for g in table:
        t = g.get("thresholds", {}) or {}
        ms, mi = t.get("max_score"), t.get("min_involvement")
        mse = t.get("max_sentiment")
        if g.get("logic") == "OR":
            hit = ((ms is not None and score < ms) or (mi is not None and involvement >= mi))
        else:
            hit = True
            if ms is not None:
                hit = hit and score < ms
            if mi is not None:
                hit = hit and involvement >= mi
            if ms is None and mi is None:
                hit = True          # 兜底档（P3）
        # 情绪准入门槛：缺 sentiment 输入时视为不满足（宁可降级，不可误报危急）
        if hit and mse is not None:
            hit = sentiment is not None and sentiment <= mse
        if hit:
            return g["level"], g.get("label", "")
    return table[-1]["level"], table[-1].get("label", "")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--sentiment", type=float, required=True,
                   help=f"情绪分 0-100，越低越负面（锚点 {ANCHORS}）")
    p.add_argument("--involvement", type=float, required=True,
                   help="涉事深度 0-100：监管/司法=100，上市公司重大=80，同行=50，行业泛化=30")
    p.add_argument("--spread", type=float, required=True,
                   help="传播量级 0-100：央媒=100，财经一级=80，门户=60，仅自媒体=30")
    p.add_argument("--age-hours", type=float, default=0.0, help="事件发生至今小时数，默认 0")
    args = p.parse_args()

    for name, v in [("sentiment", args.sentiment), ("involvement", args.involvement),
                    ("spread", args.spread)]:
        if not (0 <= v <= 100):
            sys.exit(json.dumps({"error": f"{name} 必须在 0-100 之间（当前 {v}）"},
                                ensure_ascii=False))
    if args.age_hours < 0:
        sys.exit(json.dumps({"error": "age-hours 不能为负"}, ensure_ascii=False))

    w = load_weights()
    grading, grading_note = load_grading()
    # 方向统一：涉事深度/传播量级原始 scale「越高越重大」→ 转为「越低越危急」
    inv_danger = 100.0 - args.involvement
    spread_danger = 100.0 - args.spread
    score = (args.sentiment * w["sentiment"] + inv_danger * w["involvement"]
             + spread_danger * w["spread"])
    level, label = grade(score, args.involvement, grading, args.sentiment)

    decayed = round(score, 1)
    decay_note = "未应用时效衰减（age-hours=0）"
    if args.age_hours > 0:
        if level == "P0" and args.age_hours <= P0_GRACE_HOURS:
            decay_note = f"P0 事件 {P0_GRACE_HOURS}h 内不衰减"
        else:
            days = args.age_hours / 24.0
            # 向中性（100）回归：保留 (100-score) * 0.85^days 的负面偏离
            decayed = 100 - (100 - score) * (DECAY_PER_DAY ** days)
            decayed = round(decayed, 1)
            decay_note = (f"已应用时效衰减（{days:.2f} 天，每日保留 {DECAY_PER_DAY} 偏离）："
                          f"{score:.1f} → {decayed}")
            level_after, label_after = grade(decayed, args.involvement, grading, args.sentiment)
            if level_after != level:
                decay_note += f"；衰减后等级降为 {level_after}（{label_after}）"

    print(json.dumps({
        "inputs": {"sentiment": args.sentiment, "involvement": args.involvement,
                   "spread": args.spread, "age_hours": args.age_hours},
        "weights": w,
        "components": {
            "sentiment_part": round(args.sentiment * w["sentiment"], 2),
            "involvement_part": round(inv_danger * w["involvement"], 2),
            "spread_part": round(spread_danger * w["spread"], 2),
        },
        "direction_note": ("分项已统一为『越低越危急』：涉事深度/传播量级按 100-原始分 计入"
                           f"（涉事 {args.involvement}→{inv_danger:.0f}，传播 {args.spread}→{spread_danger:.0f}）"),
        "score_direction": "越低越危急（0=最危急，100=中性）",
        "score": round(score, 1),
        "level": level,
        "label": label,
        "score_after_decay": decayed,
        "decay_note": decay_note,
        # v3.3.2：升级动作改为读配置 grading[].action，不再硬编码
        "escalation": next((g.get("action") for g in grading if g["level"] == level), None),
        "grading_source": os.path.relpath(SCORING, HERE),
        "grading_note": grading_note,
        "engine": "stdlib",
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
