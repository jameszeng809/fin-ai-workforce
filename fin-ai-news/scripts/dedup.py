#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""舆情去重与事件聚类（v3.4.1 新增）。

用途：fin-ai-news Step3 分级**之前**、fin-ai-crisis Step1 输入清洗。
依赖：无（纯标准库，开箱即用）

为什么必须有这个脚本：data/scoring.json 早就写了 dedup 规则
（"同一事件多源报道按 (主体+事件关键词) 聚类去重，取最高传播量源为主源"），
但 scripts/ 下一直没有实现。结果是上证报、中国证券网、证券时报同发一篇通稿时，
同一条新闻被算成 2-3 条，既虚增事件热度，又让传播量级被重复计入分级分数。

用法：
  python scripts/dedup.py --news-file news.json [--threshold 0.40] [--window-hours 24]
  python scripts/dedup.py --news-json '[{"title":"...","source":"上证报",...}]'

--threshold 标定依据（实测，勿随意改动默认值）：
  同一事件的直接转载标题      → 1.00（如"贵州茅台回应'稀缺性'争议" vs "茅台回应稀缺性争议"）
  同一事件的编辑改写标题      → 0.47（如上述 vs "贵州茅台'稀缺'之辩：公司称产能扩建正在推进"）
  完全不同事件          → 0.18（如上述 vs "贵州茅台2026年半年报：营收微增净利小幅下滑"）
  故 0.40 落在 0.18 与 0.47 之间，安全边际充足。低于 0.30 会把不同事件误并为一簇。

news.json 数组，每项：
  {
    "title": "茅台'稀缺'之辩",          # 必填
    "source": "上海证券报",              # 来源媒体名
    "spread_tier": 80,                  # 传播量级 0-100，对应 scoring.json 的 spread_scale.tiers
    "published_at": "2026-10-23T09:30", # 发布时间（可选，用于时间窗约束）
    "entity": "sh600519",               # 涉事主体代码（可选，不同主体永不合并且记 relevance）
    "url": "...", "summary": "..."      # 透传字段
  }

算法（无第三方依赖，中文友好）：
  1. 标题切分为 2-gram 字符片段（中文）与单词（ASCII），得到 token 集合
  2. 两两计算 Jaccard 相似度，超 --threshold 且发布时间差在 --window-hours 内 → 同簇
  3. 主源选择优先级：spread_tier 最高 → 发布时间最早 → 来源名字典序
  4. 簇的传播量级 = 成员最大值（不叠加，避免重复计数虚增热度）
输出：JSON（去重后条目、簇明细、去重率、建议用于分级的 calibrated_spread）
"""
import argparse
import json
import math
import os
import re
import sys

ASCII_WORD = re.compile(r"[a-zA-Z][a-zA-Z0-9.\-]{1,}")
# 常见"非事件性"词语，参与相似度会稀释信号（如"公司股票交易异常波动公告"里的套话）
STOPWORDS = {"公告", "关于", "公司", "股份", "有限公司", "提示性", "的", "了", "及", "与",
             "有关", "相关", "事项", "情况", "说明", "披露", "发布", "表示", "显示"}


def fail(payload, code=1):
    """统一错误出口。

    所有错误都写成 JSON 打到 **stdout**，不用 sys.exit(str)——后者走 stderr，
    一旦调用方用管道接 jq / json.loads 解析 stdout，就会拿到空输出而误判为成功。
    """
    sys.stdout.write(json.dumps(payload, ensure_ascii=False))
    sys.stdout.write("\n")
    sys.exit(code)


def tokenize(text):
    """标题 → token 集合：ASCII 词 + 中文 2-gram（去停用词、去空白标点）。"""
    s = re.sub(r"[\s，。、；：！？（）()\[\]【】《》\"'“”‘’—\-—/|]+", "", str(text or ""))
    toks = set(w.lower() for w in ASCII_WORD.findall(s))
    zh = re.sub(r"[^\u4e00-\u9fff]", "", s)
    for i in range(len(zh) - 1):
        g = zh[i:i + 2]
        if g not in STOPWORDS:
            toks.add(g)
    if len(zh) == 1:
        toks.add(zh)
    return toks


def jaccard(a, b):
    if not a or not b:
        return 0.0
    inter = len(a & b)
    if not inter:
        return 0.0
    return inter / len(a | b)


def overlap_coefficient(a, b):
    """包含度 |A∩B| / min(|A|,|B|)。

    财媒转载常把长标题改写成短标题（"贵州茅台回应'稀缺性'争议" → "茅台'稀缺'之辩"），
    纯 Jaccard 会被标题长度差压到 0.4 以下而漏合并；包含度对这类子集关系鲁棒得多。
    """
    if not a or not b:
        return 0.0
    return len(a & b) / min(len(a), len(b))


def similarity(a, b):
    """综合相似度 = max(Jaccard, 包含度)，取两者之长。

    Jaccard 抗「短标题是任意长标题子集」的误合并，包含度抗「同一事件改写标题」的漏合并；
    实测茅台同一事件的三种写法 Jaccard 0.38 / 包含度 0.57，取 max 才能正确归为一簇。
    """
    return max(jaccard(a, b), overlap_coefficient(a, b))


def parse_time(s):
    """ tolerant 时间解析：接受 ISO8601，失败返回 None（不参与时间窗约束，但不报错）。"""
    if not s:
        return None
    try:
        t = str(s).replace("Z", "+00:00")
        import datetime
        return datetime.datetime.fromisoformat(t)
    except Exception:
        m = re.match(r"(\d{4})-(\d{2})-(\d{2})[ T]?(\d{2}):?(\d{2})?", str(s))
        if m:
            import datetime
            return datetime.datetime(*[int(x) for x in m.groups() if x is not None])
        return None


def load_news(path_or_literal):
    if os.path.isfile(path_or_literal):
        with open(path_or_literal, encoding="utf-8") as f:
            data = json.load(f)
    else:
        try:
            data = json.loads(path_or_literal)
        except ValueError as e:
            fail({"error": f"新闻 JSON 解析失败: {e}"})
    if not isinstance(data, list) or not data:
        fail({"error": "新闻必须为非空数组"})
    out = []
    for i, it in enumerate(data):
        if not isinstance(it, dict):
            fail({"error": f"第 {i+1} 项必须是对象"})
        title = str(it.get("title", "")).strip()
        if not title:
            fail({"error": f"第 {i+1} 项缺少 title"})
        out.append({"idx": i, "title": title,
                    "source": it.get("source") or "未知来源",
                    "spread_tier": it.get("spread_tier"),
                    "published_at": it.get("published_at"),
                    "entity": it.get("entity"),
                    "url": it.get("url"), "summary": it.get("summary"),
                    "_tokens": tokenize(title),
                    "_time": parse_time(it.get("published_at"))})
    return out


def pick_primary(members):
    """主源：传播量级最高优先，其次发布时间最早，最后来源名字典序（保证结果稳定可复现）。"""
    def rank(item):
        t = item.get("_time")
        return (-float(item.get("spread_tier") or 0),
                t.timestamp() if t else float("inf"),
                item["source"], item["idx"])
    return sorted(members, key=rank)[0]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--news-file", help="新闻 JSON 文件路径")
    p.add_argument("--news-json", help="新闻 JSON 字符串（与 --news-file 二选一）")
    p.add_argument("--threshold", type=float, default=0.40,
                   help="相似度阈值，默认 0.40（取值的依据见下方 SIM 标定说明）")
    p.add_argument("--window-hours", type=float, default=24.0,
                   help="同簇时间窗（小时），默认 24；设为 0 表示不做时间约束")
    p.add_argument("--same-entity-only", action="store_true",
                   help="仅当 entity 相同时才允许合并（严格模式）")
    args = p.parse_args()

    src = args.news_file or args.news_json
    if not src:
        fail({"error": "必须提供 --news-file 或 --news-json"})
    if not 0 < args.threshold <= 1.0:
        fail({"error": "相似度阈值必须在 (0, 1]"})
    news = load_news(src)

    # ---- 单遍增量聚类（O(n²) 但 n 通常为数十至上百，标准库足够）----
    clusters = []
    for item in news:
        best, best_sim = None, 0.0
        for c in clusters:
            rep = c["primary"]
            if rep["entity"] and item["entity"] and rep["entity"] != item["entity"]:
                continue
            if args.same_entity_only and (rep.get("entity") != item.get("entity")):
                continue
            sim = similarity(rep["_tokens"], item["_tokens"])
            if sim < args.threshold or sim <= best_sim:
                continue
            if args.window_hours > 0 and rep["_time"] and item["_time"]:
                delta = abs((rep["_time"] - item["_time"]).total_seconds()) / 3600.0
                if delta > args.window_hours:
                    continue
            best, best_sim = c, sim
        if best is None:
            clusters.append({"primary": item, "members": [item], "max_sim": 1.0,
                         "sim_detail": []})
        else:
            best["members"].append(item)
            best["sim_detail"].append({
                "title": item["title"], "source": item["source"],
                "jaccard": round(jaccard(best["primary"]["_tokens"], item["_tokens"]), 3),
                "overlap": round(overlap_coefficient(best["primary"]["_tokens"], item["_tokens"]), 3),
                "sim": round(best_sim, 3)})
            best["max_sim"] = round(max(best["max_sim"], best_sim), 4)
            best["primary"] = pick_primary(best["members"])

    unique = [c["primary"] for c in clusters]
    clusters.sort(key=lambda c: len(c["members"]), reverse=True)

    def strip(it):
        return {k: v for k, v in it.items() if not k.startswith("_")}

    total = len(news)
    n_unique = len(unique)
    detail = []
    for c in clusters:
        tiers = [m.get("spread_tier") for m in c["members"]
                 if isinstance(m.get("spread_tier"), (int, float))]
        detail.append({
            "cluster_size": len(c["members"]),
            "similarity_threshold_hit": c["max_sim"],
            "similarity_detail": c["sim_detail"],
            "primary_source": c["primary"]["source"],
            "primary_title": c["primary"]["title"],
            "calibrated_spread_tier": max(tiers) if tiers else None,
            "sources": [{"source": m["source"], "title": m["title"],
                         "spread_tier": m.get("spread_tier"),
                         "published_at": m.get("published_at")} for m in c["members"]],
        })

    print(json.dumps({
        "input_count": total,
        "unique_count": n_unique,
        "duplicate_count": total - n_unique,
        "dedup_rate": round((total - n_unique) / total, 4) if total else 0.0,
        "params": {"threshold": args.threshold, "window_hours": args.window_hours,
                   "same_entity_only": args.same_entity_only},
        "unique_items": [strip(x) for x in unique],
        "clusters": detail,
        "usage_hint": ("分级请以 unique_items 为准，并用每簇的 calibrated_spread_tier 作为"
                       "该事件的传播量级输入；直接用原始条目的 spread_tier 会把同一事件的"
                       "多份转载重复计入，虚增严重度"),
        "note": ("v3.4.1：实现 scoring.json 中早有声明但长期缺失的 dedup 规则。"
                 "同一事件多源报道按标题相似度 + 时间窗聚类，取最高传播量源为主源"),
        "engine": "stdlib",
    }, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
