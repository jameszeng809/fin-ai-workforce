#!/usr/bin/env python3
"""历史事件案例匹配：从案例库检索最相似案例并给出历史跌幅统计。

用途：fin-ai-crisis Step2（应急交易员）、fin-ai-news Step4（舆情监控官）共用。
依赖：无（纯标准库，开箱即用）
用法：python scripts/match_cases.py --event-type financial_fraud --market cn --top 3
      python scripts/match_cases.py --event-type debt_crisis --severity P0
      python scripts/match_cases.py --event-type earnings_shock --severity P1 --market cn
      python scripts/match_cases.py --list-types
输出：JSON（Top-K 相似案例 + 分级基准跌幅 + 样本量 + 结局分布 + 适用性警告）

v3.4.1 重要修正（旧版会系统性高估影响）：
  1. severity 改为相邻衰减打分（精确 20 / 相邻 10 / 跨档 0）。旧版只给「完全匹配 20 分、
     否则 0 分」，P1 事件查不到同类 P1 时，会把 P0 退市级案例按满分排上来。
  2. 统计口径改为「同 event_type + 同 severity」优先，样本 <5 才逐级降级，并显式标注
     benchmark_level。旧版一律按整个 event_type 统计，样本内混杂不同严重度。
  3. 新增 impact_class（terminal/severe/moderate/minor）分层与**跨等级类比拦截**：
     把「单季业绩环比小幅回落」套到「财务造假退市」案例（-88%）必须被拦下来。
  4. 案例库从 50 例扩到 56 例，重点补 earnings_shock 温和/可修复样本——旧库该类型仅
     4 例且全为 A 股价值陷阱，中位 -40%，套到龙头公司必然严重高估。
"""
import argparse
import json
import os
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.join(HERE, "..", "data", "case_library.json")

SEVERITY_ORDER = ["P2", "P1", "P0"]
MIN_SAMPLES_FOR_STAT = 5   # 低于此项不足以做分位数统计，须降级并披露


def load_library():
    try:
        with open(LIB, encoding="utf-8") as f:
            return json.load(f)
    except OSError as e:
        sys.exit(json.dumps({"error": f"无法读取案例库: {e}"}, ensure_ascii=False))


def percentile(vals, q):
    if not vals:
        return None
    s = sorted(vals)
    if len(s) == 1:
        return s[0]
    pos = (len(s) - 1) * (q / 100.0)
    lo = int(pos)
    hi = min(lo + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (pos - lo)


def sev_distance(a, b):
    """严重度档位距离；不在同一量表的取值返回 None（视为不可比）。"""
    try:
        return abs(SEVERITY_ORDER.index(a) - SEVERITY_ORDER.index(b))
    except ValueError:
        return None


def score(case, event_type, market, severity, impact_class=None):
    """相似度打分（满分 100）：event_type 50 + market 30 + severity ≤20 分档。

    v3.4.1：severity 由「全有或全无」改为相邻衰减——P1 事件若无同类 P1 样本，
    同类 P0/P2 案例应拿到中间分而不是满分，避免退市级案例被当成常规业绩波动的先例。
    """
    s = 0.0
    if case.get("event_type") == event_type:
        s += 50
    code = str(case.get("code", ""))
    if market:
        hit = code.startswith("hk") if market == "hk" else (
            code.startswith("us") if market == "us" else (
                code.startswith(("sh", "sz", "bj"))))
        if hit:
            s += 30
    if severity:
        d = sev_distance(case.get("severity"), severity)
        if d == 0:
            s += 20
        elif d == 1:
            s += 10
        # d>=2 或不可比：0 分
    # 伤害等级与严重度的对应关系：用于拦截「一般业绩事件类比退市级案例」。
    # 旧版没有这层，P1 的业绩不及预期常被套到 -88% 的财务造假案例上。
    EXPECT_CLASS = {"P0": ("terminal", "severe"),
                    "P1": ("moderate", "severe"),
                    "P2": ("minor", "moderate")}
    if impact_class:
        if case.get("impact_class") == impact_class:
            s += 5
    elif severity in EXPECT_CLASS and case.get("impact_class") not in EXPECT_CLASS[severity]:
        s -= 20   # 跨伤害等级：降权，不禁止（可能确有价值），但绝不让它排在榜首
    return s


def stats_of(subset, label):
    """对给定子集算跌幅统计 + 结局分布 + 杀伤等级分布。"""
    drops = [c["max_drop_pct"] for c in subset if isinstance(c.get("max_drop_pct"), (int, float))]
    outcomes = {}
    for c in subset:
        outcomes[c.get("outcome", "未知")] = outcomes.get(c.get("outcome", "未知"), 0) + 1
    classes = {}
    for c in subset:
        classes[c.get("impact_class", "未知")] = classes.get(c.get("impact_class", "未知"), 0) + 1
    return {
        "benchmark_level": label,
        "sample_size": len(drops),
        "median_max_drop_pct": round(statistics.median(drops), 1) if drops else None,
        "p25_max_drop_pct": round(percentile(drops, 25), 1) if drops else None,
        "p75_max_drop_pct": round(percentile(drops, 75), 1) if drops else None,
        "mean_max_drop_pct": round(statistics.mean(drops), 1) if drops else None,
        "worst_max_drop_pct": min(drops) if drops else None,
        "best_max_drop_pct": max(drops) if drops else None,
        "outcome_distribution": outcomes,
        "impact_class_distribution": classes,
    }


def applicability(query_sev, stat, pool_n):
    """适用性检查：防止跨杀伤等级类比（v3.4.1）。"""
    n = stat["sample_size"]
    adequacy = ("adequate" if n >= MIN_SAMPLES_FOR_STAT
                else "limited" if n >= 2 else "insufficient")
    warnings = []
    if n < MIN_SAMPLES_FOR_STAT:
        warnings.append(
            f"同层样本仅 {n} 例（建议 ≥{MIN_SAMPLES_FOR_STAT}），统计结果仅作参考，"
            f"报告中必须标注样本数与 benchmark_level={stat['benchmark_level']}")
    cls = stat.get("impact_class_distribution", {})
    heavy = sum(v for k, v in cls.items() if k in ("terminal", "severe"))
    if n and query_sev != "P0" and heavy / n >= 0.5:
        warnings.append(
            f"适配警告：查询为 {query_sev}，但基准子集中 {(heavy/n):.0%} 属 terminal/severe 级"
            f"（退市/清盘/跌幅≤-60%）。把一般业绩事件类比到不可逆案例会严重高估影响，"
            f"请改用 impact_class=moderate/minor 的案例做基准，或换不带 mortality 的类型")
    if n and query_sev == "P0" and sum(v for k, v in cls.items() if k in ("minor",)) / n >= 0.5:
        warnings.append("适配警告：查询为 P0，但基准子集偏 minor，可能低估影响")
    return {
        "sample_adequacy": adequacy,
        "benchmark_level": stat["benchmark_level"],
        "pool_total": pool_n,
        "cross_class_warnings": warnings,
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--event-type", help="事件类型，如 financial_fraud")
    p.add_argument("--market", choices=["cn", "hk", "us"], help="市场，用于相似度加权")
    p.add_argument("--severity", choices=["P0", "P1", "P2"], help="事件严重度")
    p.add_argument("--top", type=int, default=3, help="返回相似案例数量，默认 3")
    p.add_argument("--impact-class", choices=["terminal", "severe", "moderate", "minor"],
                   help="期望杀伤等级，用于微调排序与跨等级拦截")
    p.add_argument("--list-types", action="store_true", help="列出全部事件类型与案例数")
    p.add_argument("--list-classes", action="store_true", help="列出杀伤等级说明与分布")
    args = p.parse_args()

    lib = load_library()
    cases = lib.get("cases", [])

    if args.list_classes:
        dist = {}
        for c in cases:
            dist[c.get("impact_class", "未知")] = dist.get(c.get("impact_class", "未知"), 0) + 1
        print(json.dumps({"impact_classes": lib.get("impact_classes", []),
                          "desc": lib.get("impact_class_desc", {}),
                          "distribution": dist, "total": len(cases)}, ensure_ascii=False))
        return

    if args.list_types:
        counts = {}
        for c in cases:
            counts[c.get("event_type")] = counts.get(c.get("event_type"), 0) + 1
        print(json.dumps({"event_types": lib.get("event_types", []),
                          "counts": counts, "total": len(cases)}, ensure_ascii=False))
        return

    if not args.event_type:
        sys.exit(json.dumps({"error": "必须提供 --event-type（或用 --list-types 查看可选值）"},
                            ensure_ascii=False))
    types = lib.get("event_types", [])
    if args.event_type not in types:
        sys.exit(json.dumps({"error": f"未知事件类型 {args.event_type!r}，可选: {types}"},
                            ensure_ascii=False))

    sc = lambda c: score(c, args.event_type, args.market, args.severity, args.impact_class)
    ranked = sorted(cases, key=lambda c: -sc(c))
    top = [c for c in ranked[: max(args.top * 3, args.top)] if sc(c) > 0][: args.top]
    if not top:
        sys.exit(json.dumps({"error": "案例库中没有可匹配案例，请放宽 market/severity 条件"},
                            ensure_ascii=False))

    same_type = [c for c in cases if c.get("event_type") == args.event_type]

    # ---- 分级基准：优先同类型同严重度，样本不足才逐级降级（v3.4.1）----
    if args.severity:
        tight = [c for c in same_type if c.get("severity") == args.severity]
        if len(tight) >= MIN_SAMPLES_FOR_STAT:
            benchmark, level = tight, f"same_type+same_severity({args.severity})"
        else:
            near = [c for c in same_type
                    if (sev_distance(c.get("severity"), args.severity) or 9) == 1]
            merged = tight + near
            if len(merged) >= MIN_SAMPLES_FOR_STAT:
                benchmark, level = merged, f"same_type+adjacent_severity(±1 of {args.severity})"
            else:
                benchmark, level = same_type, "same_type_only(样本不足，降级)"
    else:
        benchmark, level = same_type, "same_type_only(未指定 severity)"

    stat = stats_of(benchmark, level)
    # 同类型下按杀伤等级分组的对照表，便于人工核对该不该跨等级类比
    by_class = {}
    for c in same_type:
        by_class.setdefault(c.get("impact_class", "未知"), []).append(c["max_drop_pct"])
    class_breakdown = {
        k: {"sample_size": len(v), "median_max_drop_pct": round(statistics.median(v), 1)}
        for k, v in sorted(by_class.items())
    }

    # ---- 建议参考档：告诉调用方"该用哪个数字"，而不是甩一堆分布让他自己挑 ----
    PREFERRED_CLASS = {"P0": ("terminal", "severe"),
                       "P1": ("moderate", "severe"),
                       "P2": ("minor", "moderate")}
    suggested = None
    for cls in PREFERRED_CLASS.get(args.severity or "", ()):
        pool = [c for c in same_type if c.get("impact_class") == cls
                and isinstance(c.get("max_drop_pct"), (int, float))]
        if len(pool) >= 1:
            v = [c["max_drop_pct"] for c in pool]
            suggested = {
                "impact_class": cls,
                "sample_size": len(pool),
                "median_max_drop_pct": round(statistics.median(v), 1),
                "p25_max_drop_pct": round(percentile(v, 25), 1),
                "p75_max_drop_pct": round(percentile(v, 75), 1),
                "rationale": f"查询 severity={args.severity} 时优先参考 {cls} 级样本",
            }
            break

    print(json.dumps({
        "query": {"event_type": args.event_type, "market": args.market,
                  "severity": args.severity, "impact_class": args.impact_class},
        "suggested_reference": suggested,
        "estimation_guard": {
            "rule": "历史案例的 max_drop_pct 严禁直接当作本次事件的跌幅预测",
            "why": ("案例库记录的是事件的**尾部极端结果**，多数同类事件实际跌幅远小于该值；"
                    "且事件间的**绝对量级**往往差一个数量级"),
            "how_to_use": [
                "① 先按 impact_class 分层取中位（见 impact_class_breakdown 与 suggested_reference）",
                "② 把本次事件的定量落差与候选案例的定量特征做量级比较，量级不匹配则不可类比",
                "③ 结论必须给出区间 + 触发条件，禁止输出单一跌幅数字",
                "④ 报告中必须写明引用的 impact_class、样本数与 benchmark_level",
            ],
            "example_bias": ("宁德时代 2026Q3 归母净利 212.46 亿、环比 -5.8%、毛利率 -2.5pct——"
                             "若直接套用 earnings_shock 全类型中位 -35% 会高估约 6 倍；"
                             "合理做法是取 moderate/minor 档并与历史上真正的业绩爆雷案例区分"),
        },
        "top_matches": [{
            "id": c.get("id"), "name": c.get("name"), "code": c.get("code"),
            "year": c.get("year"), "severity": c.get("severity"),
            "impact_class": c.get("impact_class"),
            "max_drop_pct": c.get("max_drop_pct"), "outcome": c.get("outcome"),
            "summary": c.get("summary"),
            "similarity": round(sc(c), 1),
            "analogy_caution": (
                None if not args.severity or c.get("impact_class") in
                {"P0": ("terminal", "severe"), "P1": ("moderate", "severe"),
                 "P2": ("minor", "moderate")}.get(args.severity, ())
                else f"跨伤害等级类比：本例为 {c.get('impact_class')} 级"
                     f"（{c.get('max_drop_pct')}%），与查询 {args.severity} 的典型情形不符，"
                     f"引用时须说明为何可比"),
        } for c in top],
        "recommended_benchmark": stat,
        "impact_class_breakdown": class_breakdown,
        "applicability": applicability(args.severity or "P0", stat, len(same_type)),
        "type_statistics": {
            "sample_size": len(same_type),
            "median_max_drop_pct": round(statistics.median(
                [c["max_drop_pct"] for c in same_type
                 if isinstance(c.get("max_drop_pct"), (int, float))]), 1) if same_type else None,
            "note": "全类型口径（含各严重度混合），仅作背景参考；决策请用 recommended_benchmark",
        },
        "note": ("历史跌幅为公开行情近似整理，用于类比参考而非预测承诺；"
                 f"本报告基准为 {level}，样本 {stat['sample_size']} 例，"
                 "引用时必须连同样本数与杀伤等级一起披露"),
        "engine": "stdlib",
    }, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
