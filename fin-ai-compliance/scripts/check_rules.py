# -*- coding: utf-8 -*-
"""合规规则库驱动检查（v3.4.0 新增）。

合规专员此前是 9 名数字员工中**唯一没有脚本**的：data/rules.json 只被 LLM 阅读，
判定结果不可复现、无法回归。本脚本让规则库变成可执行契约——改 rules.json 立即
影响检查结果（已通过配置绑定审计）。

用法：
  python scripts/check_rules.py --holdings-file holdings.json [--orders-file orders.json]
                                [--investor-file investor.json]
                                [--nav-ratio 1.0] [--equity-ratio 1.0]

holdings.json 数组，每项：
  {
    "code": "sh600519", "name": "贵州茅台", "weight": 0.30, "industry": "食品饮料",
    "pledge_ratio": 0.00,        # 大股东质押率        → RE-01
    "unlock_ratio": 0.00,        # 限售解禁占流通股比  → RE-02
    "is_st": false,              # ST/*ST             → RE-03
    "daily_return": -0.012,      # 当日涨跌幅          → RE-04
    "reduction_ratio": 0.0,      # 大股东90日减持占比  → RE-05
    "float_holding_ratio": 0.02, # 本组合持股/该股流通股 → PL-02
    "suspension": false,         # 停牌                → EX-01
    "limit_down": false,         # 跌停封板            → EX-02
    # ↓ v3.4.1 新增：信息披露 ID 系列，逐只持仓判定
    "report_overdue_days": 0,          # 定期报告逾期天数     → ID-01
    "preforecast_deviation_pct": 0.0,  # 业绩预告偏离幅度     → ID-02
    "material_event_delay_days": 0,    # 重大事件公告延迟天数 → ID-03
    "pledge_undisclosed": false,       # 质押/冻结未披露      → ID-04
    "reduction_without_predisclosure": false  # 减持未预披露   → ID-05
  }

investor.json（可选，v3.4.1 新增）对象，驱动投资者适当性 SU 系列：
  {
    "investor_type": "retail",        # retail | professional
    "investor_risk_level": "C3",      # C1-C5
    "product_risk_level": "R4",       # R1-R5
    "risk_assessment_age_years": 1.2, # 风险测评距今年限      → SU-03
    "active_recommendation": true     # 是否主动推介         → SU-02
  }
  SU-01/suitability_mismatch 与 SU-02/high_risk_push_to_retail 由 script 依据
  上述字段推导（C1<R1…C5<R5 映射为 1..5 可比），无需调用方自己判断。

orders.json（可选）数组，每项：
  {"code": "sh600519", "side": "sell", "value_wan": 8000, "adv_wan": 120000}
  participation = value_wan / adv_wan  → EX-03

输出：JSON（逐条规则判定 + verdict + 法规出处）。
verdict：block（存在 red_alert/block_trade）/ partial（存在 orange/yellow）/ ok

v3.4.1：规则库补齐 investor_suitability(SU×3) 与 disclosure(ID×5)。这两类是 SKILL.md
Step1/Step2 早就承诺、但规则库里一直没有的检查项——旧版是"说了没做"。新增段一律走
check_struct 通用求值，不新增 if 分支链。
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RULES = os.path.join(HERE, "..", "data", "rules.json")

SEV_ORDER = {"red_alert": 3, "block_trade": 3,
             "orange_alert": 2, "defer_to_next_session": 2,
             "yellow_alert": 1, "split_order": 1,
             "pass": 0}
BLOCKING = {"red_alert", "block_trade"}


def load_rules():
    with open(RULES, encoding="utf-8") as f:
        return json.load(f)


def num(v, default=0.0):
    try:
        if v is None:
            return default
        return float(v)
    except (TypeError, ValueError):
        return default


def load_json_arg(path_or_literal):
    if os.path.isfile(path_or_literal):
        with open(path_or_literal, encoding="utf-8") as f:
            return json.load(f)
    return json.loads(path_or_literal)


def risk_rank(level):
    """把 C1-C5 / R1-R5 归一到 1-5，用于适当性匹配（SU-01/SU-02）。"""
    try:
        s = str(level).strip().upper()
        return int(s[1:]) if s[:1] in ("C", "R") and s[1:].isdigit() else None
    except (TypeError, ValueError, IndexError):
        return None


def build_suitability_ctx(inv):
    """由投资者画像推导适性规则的判定上下文（v3.4.1）。

    适当性结论必须在脚本里推出，不能让调用方自己算——否则同一份画像在不同员工手里
    会得出不同结论，圆桌共识就无从谈起。
    """
    ctx = dict(inv or {})
    # 字段别名容错：上游员工常把画像字段写成 risk_level / product_level /
    # tolerance 等近似名。读不到就静默跳过 SU 段，等于对适当性违规"查无此事"，
    # 是最危险的假阴性，因此这里先做一次归一化再求值。
    aliases = {
        "investor_risk_level": ("investor_risk_level", "risk_level",
                                "investor_level", "risk_tolerance", "risk_appetite"),
        "product_risk_level": ("product_risk_level", "risk_level_of_product",
                               "product_level", "product_risk"),
        "investor_type": ("investor_type", "is_professional", "investor_category"),
    }
    norm = dict(inv or {})
    for target, sources in aliases.items():
        if target not in norm:
            for s in sources:
                if inv.get(s) is not None:
                    norm[target] = inv[s]
                    break
    if isinstance(norm.get("investor_type"), bool):
        norm["investor_type"] = "professional" if norm["investor_type"] else "retail"
    ctx.update(norm)

    c, r = risk_rank(norm.get("investor_risk_level")), risk_rank(norm.get("product_risk_level"))
    ctx["su_evaluable"] = c is not None and r is not None
    if not ctx["su_evaluable"]:
        # 无法判定必须显式暴露，禁止伪装成"无适当性问题"
        ctx["su_skip_reason"] = (
            "投资者画像缺少可识别的 investor_risk_level / product_risk_level"
            "（已尝试别名 %s），SU-01/SU-02/SU-03 未执行；报告中不得表述为"
            "『适当性合规』，须标注『适当性未校验』"
            % ", ".join(sum(aliases.values(), ())))
    if c is not None and r is not None:
        ctx["suitability_mismatch"] = r > c
    elif inv:
        ctx["suitability_mismatch"] = None
    is_prof = str(norm.get("investor_type", "")).lower() == "professional"
    if (not is_prof) and r is not None and isinstance(inv.get("active_recommendation"), bool):
        ctx["high_risk_push_to_retail"] = bool(r >= 4 and inv.get("active_recommendation"))
    elif inv:
        ctx["high_risk_push_to_retail"] = False
    return ctx


def eval_section(section, items, subject_key="code"):
    """通用段落求值：对带 check_struct 的规则逐项检查（v3.4.1 新增 SU/ID 两段即走此路）。

    旧版每加一类规则就要在 main 里加一条 if 分支；现在只要规则自带 check_struct，
    新增段落无需改代码。
    """
    out = []
    for r in section:
        if not r.get("check_struct"):
            continue
        for it in items:
            hit, actual = eval_struct(r, it)
            if not hit:
                continue
            out.append({"rule_id": r["rule_id"], "name": r["name"],
                        "severity": r["action"],
                        "subject": str(it.get(subject_key, "PORTFOLIO")),
                        "actual": actual if isinstance(actual, bool) else round(num(actual), 4),
                        "threshold": r.get("threshold"), "unit": r.get("unit"),
                        "legal_basis": r.get("legal_basis"),
                        "desc": r.get("check_struct", {}).get("desc")})
    return out


def eval_struct(rule, ctx):
    """按 check_struct 通用求值。返回 (命中, 实际值)"""
    cs = rule.get("check_struct")
    if not cs:
        return None, None
    val = ctx.get(cs["field"])
    if cs["op"] == "eq":
        return bool(val) == bool(cs["value"]), val
    if cs["op"] == "gt":
        return num(val) > num(cs["value"]), num(val)
    if cs["op"] == "lt":
        return num(val) < num(cs["value"]), num(val)
    return None, val


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--holdings-file", required=True,
                   help="持仓 JSON 文件路径或 JSON 字符串")
    p.add_argument("--orders-file", default=None, help="交易指令 JSON（可选）")
    p.add_argument("--nav-ratio", type=float, default=1.0,
                   help="本组合占基金净值比例，用于 PL-01 换算（默认 1.0）")
    p.add_argument("--equity-ratio", type=float, default=1.0,
                   help="股票资产占净值比例，用于 PL-03（默认 1.0）")
    p.add_argument("--investor-file", default=None,
                   help="投资者画像 JSON（路径或字符串），驱动 SU 系列适当性检查")
    args = p.parse_args()

    try:
        holdings = load_json_arg(args.holdings_file)
    except Exception as e:
        sys.exit(json.dumps({"error": f"持仓解析失败: {e}"}, ensure_ascii=False))
    if not isinstance(holdings, list) or not holdings:
        sys.exit(json.dumps({"error": "持仓必须为非空数组"}, ensure_ascii=False))

    orders = []
    if args.orders_file:
        try:
            orders = load_json_arg(args.orders_file)
        except Exception as e:
            sys.exit(json.dumps({"error": f"指令解析失败: {e}"}, ensure_ascii=False))

    R = load_rules()
    checks = []

    total_w = sum(num(h.get("weight")) for h in holdings)

    # ---------- 持仓集中度 PL ----------
    for r in R.get("position_limits", []):
        thr = num(r.get("threshold"))
        unit = r.get("unit")
        if r["rule_id"] == "PL-01":
            for h in holdings:
                eff = num(h.get("weight")) * args.nav_ratio
                if eff > thr:
                    checks.append({"rule_id": r["rule_id"], "name": r["name"],
                                   "severity": r["action"], "subject": h.get("code"),
                                   "actual": round(eff, 4), "threshold": thr,
                                   "unit": unit,
                                   "legal_basis": r.get("legal_basis")})
        elif r["rule_id"] == "PL-02":
            for h in holdings:
                v = num(h.get("float_holding_ratio"))
                if v > thr:
                    checks.append({"rule_id": r["rule_id"], "name": r["name"],
                                   "severity": r["action"], "subject": h.get("code"),
                                   "actual": round(v, 4), "threshold": thr,
                                   "unit": unit,
                                   "legal_basis": r.get("legal_basis")})
        elif r["rule_id"] == "PL-03":
            if args.equity_ratio < thr:
                checks.append({"rule_id": r["rule_id"], "name": r["name"],
                               "severity": r["action"], "subject": "PORTFOLIO",
                               "actual": round(args.equity_ratio, 4),
                               "threshold": thr, "unit": unit,
                               "legal_basis": r.get("legal_basis")})

    # ---------- 行业集中度 IL ----------
    ind = {}
    for h in holdings:
        ind[h.get("industry", "未知")] = ind.get(h.get("industry", "未知"), 0.0) \
            + num(h.get("weight"))
    for r in R.get("industry_limits", []):
        thr = num(r.get("threshold"))
        if r["rule_id"] == "IL-01":
            for k, v in ind.items():
                if v > thr:
                    checks.append({"rule_id": r["rule_id"], "name": r["name"],
                                   "severity": r["action"], "subject": k,
                                   "actual": round(v, 4), "threshold": thr,
                                   "unit": r.get("unit"),
                                   "legal_basis": r.get("legal_basis")})
        elif r["rule_id"] == "IL-02":
            hhi = sum(v * v for v in ind.values())
            if hhi > thr:
                checks.append({"rule_id": r["rule_id"], "name": r["name"],
                               "severity": r["action"], "subject": "PORTFOLIO",
                               "actual": round(hhi, 4), "threshold": thr,
                               "unit": r.get("unit"),
                               "legal_basis": r.get("legal_basis")})

    # ---------- 风险事件 RE ----------
    for r in R.get("risk_events", []):
        field = {"RE-01": "pledge_ratio", "RE-02": "unlock_ratio",
                 "RE-03": "is_st", "RE-04": "daily_return",
                 "RE-05": "reduction_ratio"}.get(r["rule_id"])
        if not field:
            continue
        for h in holdings:
            if r.get("check_struct"):
                hit, actual = eval_struct(r, h)
                if not hit:
                    continue
                checks.append({"rule_id": r["rule_id"], "name": r["name"],
                               "severity": r["action"], "subject": h.get("code"),
                               "actual": actual, "threshold": r.get("threshold"),
                               "unit": r.get("unit"),
                               "legal_basis": r.get("legal_basis")})
                continue
            v = num(h.get(field))
            thr = num(r.get("threshold"))
            if r["rule_id"] == "RE-04":
                if v < -thr:
                    checks.append({"rule_id": r["rule_id"], "name": r["name"],
                                   "severity": r["action"], "subject": h.get("code"),
                                   "actual": round(v, 4), "threshold": -thr,
                                   "unit": r.get("unit"),
                                   "legal_basis": r.get("legal_basis")})
            elif v > thr:
                checks.append({"rule_id": r["rule_id"], "name": r["name"],
                               "severity": r["action"], "subject": h.get("code"),
                               "actual": round(v, 4), "threshold": thr,
                               "unit": r.get("unit"),
                               "legal_basis": r.get("legal_basis")})

    # ---------- 信息披露 ID（v3.4.1 新增）----------
    checks += eval_section(R.get("disclosure", []), holdings)

    # ---------- 投资者适当性 SU（v3.4.1 新增）----------
    investor_ctx, su_checks = None, []
    if args.investor_file:
        try:
            inv = load_json_arg(args.investor_file)
        except Exception as e:
            sys.exit(json.dumps({"error": f"投资者画像解析失败: {e}"}, ensure_ascii=False))
        investor_ctx = build_suitability_ctx(inv)
        su_checks = eval_section(R.get("investor_suitability", []),
                                 [investor_ctx], subject_key="investor_risk_level")
        checks += su_checks

    # ---------- 可执行性 EX ----------
    hmap = {h.get("code"): h for h in holdings}
    verdict_ex = "ok"
    for o in orders:
        code = o.get("code")
        h = hmap.get(code, {})
        for r in R.get("executability", []):
            ctx = dict(h)
            if r["rule_id"] == "EX-03":
                adv = num(o.get("adv_wan"))
                val = num(o.get("value_wan"))
                if adv <= 0:
                    continue
                ctx["participation"] = val / adv
            hit, actual = eval_struct(r, ctx)
            if hit:
                checks.append({"rule_id": r["rule_id"], "name": r["name"],
                               "severity": r["action"], "subject": code,
                               "actual": (actual if isinstance(actual, bool)
                                          else round(num(actual), 4)),
                               "threshold": r.get("threshold"),
                               "unit": r.get("unit"),
                               "legal_basis": r.get("legal_basis"),
                               "note": r.get("note")})

    # ---------- 汇总 ----------
    if any(c["severity"] in BLOCKING for c in checks):
        verdict = "block"
    elif checks:
        verdict = "partial"
    else:
        verdict = "ok"

    by_sev = {}
    for c in checks:
        by_sev[c["severity"]] = by_sev.get(c["severity"], 0) + 1

    rule_count = {k: len(v) for k, v in R.items()
                  if isinstance(v, list) and v and isinstance(v[0], dict)
                  and "rule_id" in v[0]}
    print(json.dumps({
        "version": R.get("_meta", {}).get("version"),
        "rules_loaded": rule_count,
        "rules_total": sum(rule_count.values()),
        "inputs": {
            "n_holdings": len(holdings),
            "n_orders": len(orders),
            "total_weight": round(total_w, 4),
            "nav_ratio": args.nav_ratio,
            "equity_ratio": args.equity_ratio,
            "industry_weights": {k: round(v, 4) for k, v in ind.items()},
            "investor_profile": investor_ctx,
        },
        "verdict": verdict,
        "verdict_cn": {"block": "阻断", "partial": "有条件通过", "ok": "通过"}[verdict],
        "n_violations": len(checks),
        "by_severity": by_sev,
        "by_section": {"investor_suitability": len(su_checks)},
        "checks": checks,
        "note": ("规则全部读自 data/rules.json（活配置）。"
                 "verdict=block 时禁止下单；partial 须在报告中列明告警项。"
                 "SU（适当性）/ID（信息披露）为 v3.4.1 补齐的两类——"
                 "SKILL.md 早有承诺而规则库长期缺失，现已逐条可执行"),
        "engine": "stdlib",
    }, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
