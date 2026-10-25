#!/usr/bin/env python3
"""圆桌共识度计算：按 data/scoring.json 公式量化团队一致性。

用途：fin-ai-orchestrator 第 3 轮圆桌综合（禁止 LLM 拍脑袋给共识度）。
依赖：无（纯标准库，开箱即用）
用法：python scripts/consensus.py --peer-scores 4,4,5,3 --disputes-total 5 --disputes-resolved 4 --data-consistency 0.9
      （--peer-scores 为第 2 轮员工互评 1-5 星；弃权员工的评分不传入即可实现"不稀释"）
输出：JSON（consensus_score 及三个分项数值、不确定性量级建议）

公式：consensus = 0.4×互评一致性 + 0.3×分歧解决率 + 0.3×数据一致性
      互评一致性 = 1 - (互评标准差 / 互评均值)，截断到 [0,1]
"""
import argparse
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SCORING = os.path.join(HERE, "..", "data", "scoring.json")
DEFAULT_WEIGHTS = {"peer_review": 0.4, "dispute_resolution": 0.3, "data_consistency": 0.3}


def load_weights():
    """v3.3.2：真正从 data/scoring.json 读取三组权重。

    旧版只读 components.peer_review_consistency.weight——而配置文件里该字段根本不存在
    （权重实际写在 _meta.weights 下），所以无论怎么改配置都恒返回硬编码默认值，
    配置形同虚设。现按 _meta.weights → 顶层 weights → 默认值 三级回退，
    并对缺失项逐项补齐、非数值项报错提示。
    """
    try:
        with open(SCORING, encoding="utf-8") as f:
            d = json.load(f)
    except (OSError, ValueError):
        return dict(DEFAULT_WEIGHTS), "配置读取失败，已回退默认权重"
    raw = None
    if isinstance(d.get("_meta"), dict) and isinstance(d["_meta"].get("weights"), dict):
        raw = d["_meta"]["weights"]
    elif isinstance(d.get("weights"), dict):
        raw = d["weights"]
    if raw is None:
        return dict(DEFAULT_WEIGHTS), "配置中未找到 weights，已回退默认权重"
    out, miss = {}, []
    for k, v in DEFAULT_WEIGHTS.items():
        val = raw.get(k)
        if isinstance(val, (int, float)) and not isinstance(val, bool):
            out[k] = float(val)
        else:
            out[k] = v
            miss.append(k)
    note = ("部分权重缺失或非法，已用默认值补齐：" + ",".join(miss)) if miss else None
    return out, note


def pstd(vals):
    m = sum(vals) / len(vals)
    return math.sqrt(sum((x - m) ** 2 for x in vals) / len(vals))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--peer-scores", required=True,
                   help="第 2 轮员工互评 1-5 星，逗号分隔（弃权评分不传入）")
    p.add_argument("--disputes-total", type=int, required=True, help="第 1 轮识别出的总分歧数")
    p.add_argument("--disputes-resolved", type=int, required=True, help="主理人已裁决解决的分歧数")
    p.add_argument("--data-consistency", type=float, required=True,
                   help="各员工引用同一指标偏差小于 1%% 的比例，0-1")
    p.add_argument("--json", action="store_true",
                   help="机器可读输出开关（本脚本始终输出 JSON；此参数仅为兼容 v3.3.0 文档承诺）")
    args = p.parse_args()

    try:
        scores = [float(x) for x in args.peer_scores.split(",")]
    except ValueError:
        sys.exit(json.dumps({"error": "peer-scores 必须为逗号分隔的数值"}, ensure_ascii=False))
    if not scores:
        sys.exit(json.dumps({"error": "peer-scores 不能为空（全部弃权时共识度无意义，"
                                      "请在纪要中标注『全员弃权』）"}, ensure_ascii=False))
    if any(not (1 <= s <= 5) for s in scores):
        sys.exit(json.dumps({"error": "互评分必须在 1-5 星之间"}, ensure_ascii=False))
    if args.disputes_total < 0 or args.disputes_resolved < 0:
        sys.exit(json.dumps({"error": "分歧数不能为负"}, ensure_ascii=False))
    if args.disputes_resolved > args.disputes_total:
        sys.exit(json.dumps({"error": "已解决分歧数不能大于总分歧数"}, ensure_ascii=False))
    if not (0 <= args.data_consistency <= 1):
        sys.exit(json.dumps({"error": "data-consistency 必须在 [0,1]"}, ensure_ascii=False))

    mean_s = sum(scores) / len(scores)
    sd = pstd(scores)
    peer_consistency = max(0.0, min(1.0, 1 - (sd / mean_s if mean_s > 0 else 1.0)))
    if args.disputes_total == 0:
        dispute_rate = 1.0  # 无分歧视为完全一致
    else:
        dispute_rate = args.disputes_resolved / args.disputes_total

    W, weights_note = load_weights()
    # v3.4.1：权重必须归一化。旧版直接用配置权重加权，若配置里三个权重之和不是 1
    #（例如被误改成 0.8/0.4/0.2，和=1.4），共识度会算出 1.1686 > 1 这种非法值，
    # 而共识度的语义是 0-1 的一致性比例，超出即失去意义。
    wsum = sum(W.values())
    weights_normalized = None
    if wsum <= 0:
        sys.exit(json.dumps({"error": "权重之和必须为正数", "weights": W}, ensure_ascii=False))
    if abs(wsum - 1.0) > 1e-6:
        W = {k: round(v / wsum, 6) for k, v in W.items()}
        weights_normalized = {
            "applied": True,
            "original_sum": round(wsum, 6),
            "note": "配置权重之和不为 1，已按比例归一化，避免共识度越界（>1）",
        }

    total = (W["peer_review"] * peer_consistency
             + W["dispute_resolution"] * dispute_rate
             + W["data_consistency"] * args.data_consistency)

    if total >= 0.75 and args.data_consistency >= 0.8:
        uncertainty = "low"
    elif total >= 0.5:
        uncertainty = "medium"
    else:
        uncertainty = "high"

    print(json.dumps({
        "inputs": {
            "peer_scores": scores,
            "disputes_total": args.disputes_total,
            "disputes_resolved": args.disputes_resolved,
            "data_consistency": args.data_consistency,
        },
        "components": {
            "peer_review_consistency": round(peer_consistency, 4),
            "dispute_resolution_rate": round(dispute_rate, 4),
            "data_consistency": round(args.data_consistency, 4),
            "peer_scores_mean": round(mean_s, 3),
            "peer_scores_std": round(sd, 3),
        },
        "weights": W,
        "weights_source": os.path.relpath(SCORING, HERE),
        "weights_note": weights_note,
        "weights_normalized": weights_normalized,
        "consensus_score": round(total, 4),
        "uncertainty": uncertainty,
        "unresolved_disputes": args.disputes_total - args.disputes_resolved,
        "note": ("弃权(abstain=true)员工的评分不传入本脚本，即自动实现『不稀释他人观点』；"
                 "共识度 <0.5 时主理人必须在纪要中显式列出未解决分歧"),
        "engine": "stdlib",
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
